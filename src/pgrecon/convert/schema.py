"""Emit PostgreSQL schema DDL from the inventory's structured facts.

The converter reads the same fact tables the rules do and writes
plain DDL: tables with typed columns, then primary keys, unique
constraints, checks, and foreign keys in dependency-safe order.
Anything it cannot convert faithfully becomes a residue item naming
the object and the reason - wrong DDL is never emitted silently.

Identifiers are folded to PostgreSQL's lowercase convention and
quoted only when they need it, which is what migrated applications
almost always want.
"""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import sqlglot
from sqlglot import Expr, exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.transforms import eliminate_join_marks

from pgrecon.convert.typemap import map_type
from pgrecon.inventory.loader import PARSE_NORMALIZATIONS

_PLAIN_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")

_RESERVED = {
    "all",
    "analyse",
    "analyze",
    "and",
    "any",
    "array",
    "as",
    "asc",
    "asymmetric",
    "both",
    "case",
    "cast",
    "check",
    "collate",
    "column",
    "constraint",
    "create",
    "current_date",
    "current_role",
    "current_time",
    "current_timestamp",
    "current_user",
    "default",
    "deferrable",
    "desc",
    "distinct",
    "do",
    "else",
    "end",
    "except",
    "false",
    "fetch",
    "for",
    "foreign",
    "from",
    "grant",
    "group",
    "having",
    "in",
    "initially",
    "intersect",
    "into",
    "lateral",
    "leading",
    "limit",
    "localtime",
    "localtimestamp",
    "not",
    "null",
    "offset",
    "on",
    "only",
    "or",
    "order",
    "placing",
    "primary",
    "references",
    "returning",
    "select",
    "session_user",
    "some",
    "symmetric",
    "table",
    "then",
    "to",
    "trailing",
    "true",
    "union",
    "unique",
    "user",
    "using",
    "variadic",
    "when",
    "where",
    "window",
    "with",
}

_NOT_NULL_CONDITION = re.compile(
    r'^"?[A-Za-z0-9_$#]+"?\s+IS\s+NOT\s+NULL$', re.IGNORECASE
)


@dataclass(frozen=True)
class Residue:
    """One thing the converter declined to convert, and why."""

    owner: str
    object_name: str
    kind: str
    reason: str


@dataclass(frozen=True)
class Conversion:
    sql: str
    residue: tuple[Residue, ...]
    tables: int
    constraints: int
    indexes: int
    views: int
    partitions: int


def ident(name: str) -> str:
    """Fold to lowercase; quote only when the result needs it."""
    lowered = name.lower()
    if _PLAIN_IDENT.match(lowered) and lowered not in _RESERVED:
        return lowered
    return '"' + name.replace('"', '""') + '"'


def _columns(conn: sqlite3.Connection, owner: str, table: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT column_name, data_type, data_length, data_precision,"
        " data_scale, nullable FROM columns"
        " WHERE owner = ? AND table_name = ? ORDER BY position",
        (owner, table),
    ).fetchall()


@dataclass(frozen=True)
class _PartMeta:
    clause: str
    ptype: str
    subtype: str
    interval: str | None
    subkeys: str


_BOUND_DATE = re.compile(
    r"TO_(?:DATE|TIMESTAMP)\(\s*'([^']*)'\s*,\s*'[^']*'(?:\s*,\s*'[^']*')?\s*\)",
    re.IGNORECASE,
)


def _bound_to_pg(value: str | None) -> str | None:
    """One partition bound as a PostgreSQL literal, or None to decline."""
    v = (value or "").strip()
    if not v:
        return None
    if v.upper() == "MAXVALUE":
        return "MAXVALUE"
    v = _BOUND_DATE.sub(lambda m: "'" + m.group(1).strip() + "'", v)
    if "TO_DATE" in v.upper() or "TO_TIMESTAMP" in v.upper():
        return None
    return v


def _part_keys(
    conn: sqlite3.Connection, owner: str, table: str, fact_table: str
) -> str:
    return ", ".join(
        ident(r["column_name"])
        for r in conn.execute(
            f"SELECT column_name FROM {fact_table}"
            " WHERE owner = ? AND table_name = ? ORDER BY position",
            (owner, table),
        )
    )


def _partition_meta(
    conn: sqlite3.Connection, owner: str, table: str
) -> tuple[_PartMeta | None, str | None]:
    """Partitioning facts for one table, or a residue reason."""
    part = conn.execute(
        "SELECT partitioning_type, subpartitioning_type, interval"
        " FROM part_tables WHERE owner = ? AND table_name = ?",
        (owner, table),
    ).fetchone()
    if part is None:
        return None, None
    ptype = (part["partitioning_type"] or "").upper()
    subtype = (part["subpartitioning_type"] or "NONE").upper()
    keys = _part_keys(conn, owner, table, "part_key_columns")
    if ptype not in ("RANGE", "LIST", "HASH") or not keys:
        return None, f"{ptype or 'unknown'} partitioning needs a hand-designed layout"
    subkeys = ""
    if subtype in ("RANGE", "LIST", "HASH"):
        subkeys = _part_keys(conn, owner, table, "part_subkey_columns")
        if not subkeys:
            subtype = "NONE"
    return (
        _PartMeta(
            clause=f" PARTITION BY {ptype} ({keys})",
            ptype=ptype,
            subtype=subtype,
            interval=part["interval"],
            subkeys=subkeys,
        ),
        None,
    )


def _child_spec(
    ptype: str,
    high_value: str | None,
    truncated: int | None,
    position: int,
    total: int,
    prev: str,
) -> tuple[str | None, str]:
    """One child's FOR VALUES spec and the next range floor."""
    if ptype == "HASH":
        return f"FOR VALUES WITH (MODULUS {total}, REMAINDER {position - 1})", prev
    if truncated:
        return None, prev
    if ptype == "LIST":
        hv = (high_value or "").strip()
        if hv.upper() == "DEFAULT":
            return "DEFAULT", prev
        bound = _bound_to_pg(hv)
        return (f"FOR VALUES IN ({bound})" if bound else None), prev
    bound = _bound_to_pg(high_value)
    if bound is None:
        return None, prev
    return f"FOR VALUES FROM ({prev}) TO ({bound})", bound


def _emit_partition_children(
    conn: sqlite3.Connection,
    owner: str,
    table: str,
    meta: _PartMeta,
    out: list[str],
    residue: list[Residue],
) -> int:
    parts = conn.execute(
        "SELECT partition_name, position, high_value, truncated"
        " FROM part_partitions WHERE owner = ? AND table_name = ?"
        " ORDER BY position",
        (owner, table),
    ).fetchall()
    if not parts:
        residue.append(
            Residue(
                owner,
                table,
                "partitioning",
                "partition bounds are not in this dump (older extraction"
                " script); child partitions must be defined by hand",
            )
        )
        return 0

    statements: list[str] = []
    prev = "MINVALUE"
    for p in parts:
        child = f"{table}_{p['partition_name']}"
        if len(child) > 63:
            residue.append(
                Residue(
                    owner,
                    table,
                    "partitioning",
                    f"child name {child} exceeds PostgreSQL's 63-character"
                    " limit; children omitted, name them by hand",
                )
            )
            return 0
        spec, prev = _child_spec(
            meta.ptype,
            p["high_value"],
            p["truncated"],
            p["position"] or 1,
            len(parts),
            prev,
        )
        if spec is None:
            residue.append(
                Residue(
                    owner,
                    table,
                    "partitioning",
                    f"bound of partition {p['partition_name']} could not be"
                    " converted faithfully; children omitted",
                )
            )
            return 0
        stmt = f"CREATE TABLE {ident(child)} PARTITION OF {ident(table)} {spec}"
        if meta.subtype != "NONE":
            stmt += f" PARTITION BY {meta.subtype} ({meta.subkeys})"
        statements.append(stmt + ";")
        if meta.subtype != "NONE":
            subs = conn.execute(
                "SELECT subpartition_name, position, high_value, truncated"
                " FROM part_subpartitions"
                " WHERE owner = ? AND table_name = ? AND partition_name = ?"
                " ORDER BY position",
                (owner, table, p["partition_name"]),
            ).fetchall()
            if not subs:
                residue.append(
                    Residue(
                        owner,
                        table,
                        "partitioning",
                        f"subpartitions of {p['partition_name']} are not in"
                        " the dump; children omitted",
                    )
                )
                return 0
            sub_prev = "MINVALUE"
            for s in subs:
                sub_child = f"{table}_{p['partition_name']}_{s['subpartition_name']}"
                if len(sub_child) > 63:
                    residue.append(
                        Residue(
                            owner,
                            table,
                            "partitioning",
                            f"child name {sub_child} exceeds PostgreSQL's"
                            " 63-character limit; children omitted",
                        )
                    )
                    return 0
                sub_spec, sub_prev = _child_spec(
                    meta.subtype,
                    s["high_value"],
                    s["truncated"],
                    s["position"] or 1,
                    len(subs),
                    sub_prev,
                )
                if sub_spec is None:
                    residue.append(
                        Residue(
                            owner,
                            table,
                            "partitioning",
                            f"bound of subpartition {s['subpartition_name']}"
                            " could not be converted; children omitted",
                        )
                    )
                    return 0
                statements.append(
                    f"CREATE TABLE {ident(sub_child)} PARTITION OF"
                    f" {ident(child)} {sub_spec};"
                )

    out.extend(statements)
    out.append("")
    if meta.interval:
        residue.append(
            Residue(
                owner,
                table,
                "note",
                "existing partitions are emitted; Oracle was creating new"
                " ones automatically by interval, which needs scheduled"
                " creation on PostgreSQL (for example pg_partman)",
            )
        )
    return len(statements)


def convert_schema(db: Path) -> Conversion:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        return _convert(conn)
    finally:
        conn.close()


def _convert(conn: sqlite3.Connection) -> Conversion:
    out: list[str] = []
    residue: list[Residue] = []
    table_count = 0
    constraint_count = 0
    partition_count = 0

    out.append("-- Generated by pgrecon convert: schema structure from the")
    out.append("-- inventory's dictionary facts. Review the residue report")
    out.append("-- for everything that needs a human decision.")
    out.append("")

    tables = conn.execute(
        "SELECT owner, table_name, temporary FROM tables" " ORDER BY owner, table_name"
    ).fetchall()

    for t in tables:
        owner, table = t["owner"], t["table_name"]
        cols = _columns(conn, owner, table)
        if not cols:
            residue.append(
                Residue(owner, table, "table", "no column facts in the inventory")
            )
            continue
        lines: list[str] = []
        for c in cols:
            mapped = map_type(
                c["data_type"], c["data_length"], c["data_precision"], c["data_scale"]
            )
            if mapped.pg_type is None:
                residue.append(
                    Residue(
                        owner,
                        f"{table}.{c['column_name']}",
                        "column",
                        mapped.note or "unmappable type",
                    )
                )
                continue
            if mapped.note is not None:
                residue.append(
                    Residue(owner, f"{table}.{c['column_name']}", "note", mapped.note)
                )
            null = "" if (c["nullable"] or "Y") == "Y" else " NOT NULL"
            lines.append(f"    {ident(c['column_name'])} {mapped.pg_type}{null}")
        if not lines:
            residue.append(
                Residue(owner, table, "table", "every column was unconvertible")
            )
            continue
        meta, part_reason = _partition_meta(conn, owner, table)
        if part_reason is not None:
            residue.append(Residue(owner, table, "partitioning", part_reason))
        if (t["temporary"] or "N") == "Y":
            residue.append(
                Residue(
                    owner,
                    table,
                    "table",
                    "global temporary table emitted as a plain table;"
                    " per-session semantics need pgtt or a redesign",
                )
            )
        out.append(f"CREATE TABLE {ident(table)} (")
        out.append(",\n".join(lines))
        out.append(f"){meta.clause if meta else ''};")
        out.append("")
        table_count += 1
        if meta is not None:
            partition_count += _emit_partition_children(
                conn, owner, table, meta, out, residue
            )

    constraint_count += _emit_keys(conn, out, residue)
    constraint_count += _emit_checks(conn, out, residue)
    constraint_count += _emit_foreign_keys(conn, out, residue)
    index_count = _emit_indexes(conn, out, residue)
    view_count = _emit_views(conn, out, residue)

    return Conversion(
        "\n".join(out),
        tuple(residue),
        table_count,
        constraint_count,
        index_count,
        view_count,
        partition_count,
    )


def _constraint_columns(conn: sqlite3.Connection, owner: str, name: str) -> list[str]:
    return [
        ident(r["column_name"])
        for r in conn.execute(
            "SELECT column_name FROM constraint_columns"
            " WHERE owner = ? AND constraint_name = ? ORDER BY position",
            (owner, name),
        )
    ]


def _emit_keys(conn: sqlite3.Connection, out: list[str], residue: list[Residue]) -> int:
    count = 0
    rows = conn.execute(
        "SELECT owner, constraint_name, table_name, type FROM constraints"
        " WHERE type IN ('P', 'U') ORDER BY type, owner, table_name, constraint_name"
    ).fetchall()
    for r in rows:
        cols = _constraint_columns(conn, r["owner"], r["constraint_name"])
        if not cols:
            residue.append(
                Residue(
                    r["owner"], r["constraint_name"], "constraint", "no column facts"
                )
            )
            continue
        kind = "PRIMARY KEY" if r["type"] == "P" else "UNIQUE"
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} {kind} ({', '.join(cols)});"
        )
        count += 1
    if rows:
        out.append("")
    return count


def _emit_checks(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT c.owner, c.constraint_name, c.table_name, k.condition, k.truncated"
        " FROM constraints c JOIN check_conditions k"
        " ON k.owner = c.owner AND k.constraint_name = c.constraint_name"
        " WHERE c.type = 'C' ORDER BY c.owner, c.table_name, c.constraint_name"
    ).fetchall()
    emitted = False
    for r in rows:
        condition = (r["condition"] or "").strip()
        if not condition or _NOT_NULL_CONDITION.match(condition):
            # Column-level NOT NULL already lives on the column.
            continue
        if r["truncated"]:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "condition was truncated during extraction; recover it"
                    " from the source before porting",
                )
            )
            continue
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} CHECK ({condition});"
        )
        emitted = True
        count += 1
    if emitted:
        out.append("")
    return count


def _emit_foreign_keys(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT owner, constraint_name, table_name, ref_owner, ref_constraint,"
        " delete_rule FROM constraints WHERE type = 'R'"
        " ORDER BY owner, table_name, constraint_name"
    ).fetchall()
    for r in rows:
        cols = _constraint_columns(conn, r["owner"], r["constraint_name"])
        ref = conn.execute(
            "SELECT table_name FROM constraints"
            " WHERE owner = ? AND constraint_name = ?",
            (r["ref_owner"], r["ref_constraint"]),
        ).fetchone()
        ref_cols = (
            _constraint_columns(conn, r["ref_owner"], r["ref_constraint"])
            if ref
            else []
        )
        if not cols or ref is None or not ref_cols:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "foreign key",
                    "referenced key is outside the extracted schema",
                )
            )
            continue
        action = ""
        if (r["delete_rule"] or "").upper() == "CASCADE":
            action = " ON DELETE CASCADE"
        elif (r["delete_rule"] or "").upper() == "SET NULL":
            action = " ON DELETE SET NULL"
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} FOREIGN KEY ({', '.join(cols)})"
            f" REFERENCES {ident(ref['table_name'])} ({', '.join(ref_cols)}){action};"
        )
        count += 1
    if rows:
        out.append("")
    return count


def _emit_indexes(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    """Secondary indexes; constraint-backed and generated ones are the
    constraints' business and never emitted twice."""
    count = 0
    rows = conn.execute(
        "SELECT i.owner, i.index_name, i.table_name, i.index_type, i.uniqueness"
        " FROM indexes i"
        " WHERE COALESCE(i.generated, 'N') <> 'Y'"
        " AND NOT EXISTS (SELECT 1 FROM constraints c"
        "   WHERE c.owner = i.owner AND c.constraint_name = i.index_name)"
        " ORDER BY i.owner, i.table_name, i.index_name",
    ).fetchall()
    emitted = False
    for r in rows:
        itype = (r["index_type"] or "NORMAL").upper()
        if itype not in ("NORMAL", "FUNCTION-BASED NORMAL", "BITMAP"):
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "index",
                    f"{itype} indexes have no direct counterpart",
                )
            )
            continue
        cols = conn.execute(
            "SELECT column_name, position FROM index_columns"
            " WHERE owner = ? AND index_name = ? ORDER BY position",
            (r["owner"], r["index_name"]),
        ).fetchall()
        exprs = {
            e["position"]: (e["expression"], e["truncated"])
            for e in conn.execute(
                "SELECT position, expression, truncated FROM index_expressions"
                " WHERE owner = ? AND index_name = ?",
                (r["owner"], r["index_name"]),
            )
        }
        parts: list[str] = []
        skip_reason: str | None = None
        for c in cols:
            expression, truncated = exprs.get(c["position"], (None, 0))
            if expression:
                if truncated:
                    skip_reason = (
                        "index expression was truncated during extraction;"
                        " recreate it from the source"
                    )
                    break
                parts.append(f"({expression})")
            elif (c["column_name"] or "").upper().startswith("SYS_NC"):
                skip_reason = (
                    "hidden function-based column without its expression;"
                    " recreate the index from the source"
                )
                break
            else:
                parts.append(ident(c["column_name"]))
        if skip_reason is not None or not parts:
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "index",
                    skip_reason or "no column facts",
                )
            )
            continue
        if itype == "BITMAP":
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "note",
                    "bitmap index emitted as btree; evaluate btree_gin for"
                    " low-cardinality columns",
                )
            )
        locality = conn.execute(
            "SELECT locality FROM part_indexes WHERE owner = ? AND index_name = ?",
            (r["owner"], r["index_name"]),
        ).fetchone()
        if locality is not None and (locality["locality"] or "").upper() == "GLOBAL":
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "note",
                    "GLOBAL partitioned index becomes per-partition on"
                    " PostgreSQL; uniqueness across partitions needs the"
                    " partition key in the index",
                )
            )
        unique = "UNIQUE " if (r["uniqueness"] or "").upper() == "UNIQUE" else ""
        out.append(
            f"CREATE {unique}INDEX {ident(r['index_name'])}"
            f" ON {ident(r['table_name'])} ({', '.join(parts)});"
        )
        emitted = True
        count += 1
    if emitted:
        out.append("")
    return count


_VIEW_HEADER_NOISE = re.compile(
    r"\b(FORCE|EDITIONABLE|NONEDITIONABLE)\s+", re.IGNORECASE
)


def _fold_identifiers(tree: Expr) -> Expr:
    """Lowercase and unquote identifiers; drop schema qualifiers.

    DBMS_METADATA quotes every identifier in uppercase; carried as-is
    the view would reference "EMP" while the converted table is emp.
    Single-schema conversion also drops the owner prefix.
    """
    for node in tree.walk():
        if isinstance(node, exp.Identifier):
            node.set("this", node.name.lower())
            node.set("quoted", not _PLAIN_IDENT.match(node.name.lower()))
        if isinstance(node, exp.Table | exp.Column) and node.args.get("db"):
            node.set("db", None)
    return tree


def _emit_views(
    conn: sqlite3.Connection, out: list[str], residue: list[Residue]
) -> int:
    """Views via transpile of the stored DDL, in dependency order."""
    rows = conn.execute(
        "SELECT owner, name, ddl FROM ddl WHERE type = 'VIEW' ORDER BY name"
    ).fetchall()
    if not rows:
        return 0
    names = {r["name"] for r in rows}
    edges: dict[str, set[str]] = {r["name"]: set() for r in rows}
    for d in conn.execute(
        "SELECT name, ref_name FROM dependencies"
        " WHERE type = 'VIEW' AND ref_type = 'VIEW'"
    ):
        if d["name"] in names and d["ref_name"] in names:
            edges[d["name"]].add(d["ref_name"])
    ordered: list[str] = []
    while edges:
        ready = sorted(n for n, deps in edges.items() if not deps - set(ordered))
        if not ready:
            ordered.extend(sorted(edges))
            break
        ordered.extend(ready)
        for n in ready:
            edges.pop(n)
    by_name = {r["name"]: r for r in rows}

    count = 0
    emitted = False
    for name in ordered:
        r = by_name[name]
        text = _VIEW_HEADER_NOISE.sub("", r["ddl"] or "")
        for pattern, replacement in PARSE_NORMALIZATIONS:
            text = pattern.sub(replacement, text)
        try:
            parsed = sqlglot.parse(text, dialect="oracle")
            tree = parsed[0] if parsed else None
            if tree is None:
                raise SqlglotError("statement did not parse")
            # The generator passes some Oracle-only constructs through
            # verbatim instead of flagging them; wrong DDL must become
            # residue, never output, so the tree is checked explicitly.
            if tree.find(exp.Connect) is not None:
                residue.append(
                    Residue(
                        r["owner"],
                        name,
                        "view",
                        "needs a manual rewrite: CONNECT BY becomes a"
                        " WITH RECURSIVE query",
                    )
                )
                continue
            # Oracle (+) outer joins become ANSI joins; the rule is a
            # no-op on queries without join marks.
            tree = eliminate_join_marks(tree)
            statement = _fold_identifiers(tree).sql(
                dialect="postgres", unsupported_level=ErrorLevel.RAISE, pretty=True
            )
        except SqlglotError as exc:
            reason = str(exc).splitlines()[0][:140]
            residue.append(
                Residue(
                    r["owner"],
                    name,
                    "view",
                    f"needs a manual rewrite: {reason}",
                )
            )
            continue
        out.append(statement + ";")
        out.append("")
        emitted = True
        count += 1
    if emitted and out and out[-1] != "":
        out.append("")
    return count


def residue_report(residue: tuple[Residue, ...]) -> str:
    """The residue as a reviewable text report."""
    if not residue:
        return "Nothing was left behind: every fact converted cleanly.\n"
    lines = [
        "Residue: what the converter declined to convert, and why.",
        "Each line needs a human decision before the schema is complete.",
        "",
    ]
    for r in residue:
        lines.append(f"{r.kind:12} {r.owner}.{r.object_name}: {r.reason}")
    lines.append("")
    return "\n".join(lines)

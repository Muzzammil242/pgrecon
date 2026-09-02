"""Table emission: typed columns, defaults, and partition children."""

import re
import sqlite3

from pgrecon.convert.identifiers import (
    _date_function_guard,
    _default_column_guard,
    _default_guard,
    _fold_expression,
    _referenced_columns,
    _type_mismatch_guard,
    ident,
    over_limit,
    truncation_clash,
)
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.partitions import _emit_partition_children, _partition_meta
from pgrecon.convert.residue import Residue
from pgrecon.convert.typemap import expression_family, map_type

# Oracle identity columns store their backing sequence as the column
# default; the name is always ISEQ$$_<object id>.
_IDENTITY_DEFAULT = re.compile(r"ISEQ\$\$_\d+.{0,4}NEXTVAL", re.IGNORECASE | re.DOTALL)

# A default drawing from a sequence, as the catalog spells it:
# "OWNER"."SEQ"."NEXTVAL", SEQ.NEXTVAL, quoted or bare in any mix.
_SEQUENCE_DEFAULT = re.compile(
    r'^\s*(?:("[^"]+"|[\w$#]+)\s*\.\s*)?("[^"]+"|[\w$#]+)\s*\.\s*"?NEXTVAL"?\s*$',
    re.IGNORECASE,
)
# LOB initializers: an empty, non-null value of the target type.
_EMPTY_LOBS = {"EMPTY_CLOB()": "''", "EMPTY_BLOB()": "''::bytea"}


_STRING_LITERAL = re.compile(r"^'((?:[^']|'')*)'$")


def _literal_length_guard(folded: str, column: sqlite3.Row) -> str | None:
    """A string default longer than its column: Oracle accepts the
    table and rejects the row; PostgreSQL rejects the table."""
    m = _STRING_LITERAL.match(folded.strip())
    if m is None:
        return None
    dtype = (column["data_type"] or "").upper()
    length = column["data_length"]
    if dtype not in ("VARCHAR2", "NVARCHAR2", "CHAR", "NCHAR") or not length:
        return None
    chars = len(m.group(1).replace("''", "'"))
    if dtype.startswith("N"):
        length = length // 2
    if chars > length:
        return (
            f"default literal is {chars} characters, longer than the column;"
            " Oracle would reject the row, PostgreSQL rejects the table"
        )
    return None


def _column_families(
    conn: sqlite3.Connection, owner: str, table: str
) -> dict[str, str]:
    """Upper-cased column name to expression family, for the type-aware
    expression guards."""
    families: dict[str, str] = {}
    for r in conn.execute(
        "SELECT column_name, data_type, data_length, data_precision, data_scale,"
        " char_length FROM columns WHERE owner = ? AND table_name = ?",
        (owner, table),
    ):
        mapped = map_type(
            r["data_type"],
            r["data_length"],
            r["data_precision"],
            r["data_scale"],
            r["char_length"],
        ).pg_type
        if mapped is not None:
            families[(r["column_name"] or "").upper()] = expression_family(mapped)
    return families


_MULTIBYTE_PREFIXES = ("AL32", "AL16", "UTF", "ZHS16", "ZHT16", "JA16", "KO16")


def _multibyte_database(conn: sqlite3.Connection) -> bool:
    """Whether the source character set spends more than one byte on
    some characters, which is when BYTE-semantics widths bite."""
    row = conn.execute(
        "SELECT value FROM nls_params WHERE key = 'NLS_CHARACTERSET'"
    ).fetchone()
    charset = (row[0] or "").upper() if row else ""
    return charset.startswith(_MULTIBYTE_PREFIXES)


def _date_columns(conn: sqlite3.Connection, owner: str, table: str) -> set[str]:
    """Upper-cased names of the table's DATE and TIMESTAMP columns."""
    return {
        (r["column_name"] or "").upper()
        for r in conn.execute(
            "SELECT column_name FROM columns WHERE owner = ? AND table_name = ?"
            " AND (UPPER(data_type) = 'DATE' OR UPPER(data_type) LIKE 'TIMESTAMP%')",
            (owner, table),
        )
    }


def _columns(conn: sqlite3.Connection, owner: str, table: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT column_name, data_type, data_length, data_precision,"
        " data_scale, nullable, char_length, char_used FROM columns"
        " WHERE owner = ? AND table_name = ? ORDER BY position",
        (owner, table),
    ).fetchall()


def emit_tables(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    names: NameRegistry,
    skip_mviews: set[str] | None = None,
    sequence_names: set[str] | None = None,
) -> tuple[int, int]:
    """Emit every table; returns (table_count, partition_count).

    Tables named in skip_mviews are materialized-view containers whose
    defining query was captured; the mview emitter owns them.
    """
    table_count = 0
    partition_count = 0

    # Identity columns become integer identity columns; a foreign key
    # cannot span numeric and bigint, so every column referencing an
    # identity key widens to bigint with it.
    identity_cols = {
        ((r["table_name"] or "").upper(), (r["column_name"] or "").upper())
        for r in conn.execute(
            "SELECT table_name, column_name, default_text FROM column_defaults"
        )
        if _IDENTITY_DEFAULT.search(r["default_text"] or "")
    }
    promoted = {
        ((fk["tab"] or "").upper(), (fk["col"] or "").upper())
        for fk in conn.execute(
            "SELECT c.table_name AS tab, cc.column_name AS col,"
            " rc.table_name AS rtab, rcc.column_name AS rcol"
            " FROM constraints c"
            " JOIN constraint_columns cc ON cc.owner = c.owner"
            "  AND cc.constraint_name = c.constraint_name"
            " JOIN constraints rc ON rc.owner = c.ref_owner"
            "  AND rc.constraint_name = c.ref_constraint"
            " JOIN constraint_columns rcc ON rcc.owner = rc.owner"
            "  AND rcc.constraint_name = rc.constraint_name"
            "  AND rcc.position = cc.position"
            " WHERE c.type = 'R'"
        )
        if ((fk["rtab"] or "").upper(), (fk["rcol"] or "").upper()) in identity_cols
    }

    # DBMS_METADATA hands a materialized view over as its container
    # table, so the defining query never reaches the inventory; the
    # table converts, and the residue names what was lost.
    mviews = {
        ((r["owner"] or "").upper(), (r["mview_name"] or "").upper()): r
        for r in conn.execute(
            "SELECT owner, mview_name, rewrite_enabled, refresh_method FROM mviews"
        )
    }

    tables = conn.execute(
        "SELECT owner, table_name, temporary FROM tables ORDER BY owner, table_name"
    ).fetchall()
    multibyte = _multibyte_database(conn)

    for t in tables:
        owner, table = t["owner"], t["table_name"]
        if skip_mviews and (table or "").upper() in skip_mviews:
            continue
        if not names.claim(table or "", "table", owner, residue):
            continue
        cols = _columns(conn, owner, table)
        if not cols:
            residue.append(
                Residue(owner, table, "table", "no column facts in the inventory")
            )
            continue
        clash = truncation_clash((c["column_name"] or "") for c in cols)
        if clash is not None:
            residue.append(
                Residue(
                    owner,
                    table,
                    "table",
                    f"columns {clash[0]} and {clash[1]} collide within"
                    " PostgreSQL's 63-byte identifier limit; rename"
                    " before migration",
                )
            )
            continue
        extras = {
            (r["column_name"] or "").upper(): r
            for r in conn.execute(
                "SELECT column_name, default_text, virtual, truncated"
                " FROM column_defaults WHERE owner = ? AND table_name = ?",
                (owner, table),
            )
        }
        lines: list[str] = []
        kept_columns: set[str] = set()
        virtual_columns: set[str] = set()
        all_virtual = {
            name for name, r in extras.items() if (r["virtual"] or "NO") == "YES"
        }
        date_cols = _date_columns(conn, owner, table)
        families = _column_families(conn, owner, table)
        for c in cols:
            mapped = map_type(
                c["data_type"],
                c["data_length"],
                c["data_precision"],
                c["data_scale"],
                c["char_length"],
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
                dropped.setdefault((owner, table), set()).add(
                    (c["column_name"] or "").upper()
                )
                continue
            if mapped.note is not None:
                residue.append(
                    Residue(owner, f"{table}.{c['column_name']}", "note", mapped.note)
                )
            cname = (c["column_name"] or "").upper()
            null = "" if (c["nullable"] or "Y") == "Y" else " NOT NULL"
            suffix = ""
            col_type = mapped.pg_type
            if (table.upper(), cname) in promoted:
                col_type = "bigint"
                residue.append(
                    Residue(
                        owner,
                        f"{table}.{c['column_name']}",
                        "note",
                        "widened to bigint to match the identity column"
                        " its foreign key references",
                    )
                )
            extra = extras.get(cname)
            if extra is not None and (extra["virtual"] or "NO") == "YES":
                virtual_columns.add(cname)
                expr = (
                    None
                    if extra["truncated"]
                    else _fold_expression(extra["default_text"] or "")
                )
                guard = (
                    None
                    if expr is None
                    else _default_guard(expr)
                    or _date_function_guard(expr, date_cols)
                    or _type_mismatch_guard(expr, families)
                )
                if expr is not None and guard is None:
                    # PostgreSQL generated columns cannot read one another.
                    chained = sorted(
                        (_referenced_columns(expr) or set()) & (all_virtual - {cname})
                    )
                    if chained:
                        guard = (
                            f"expression reads virtual column {chained[0]};"
                            " PostgreSQL generated columns cannot reference one"
                            " another - inline the expression by hand"
                        )
                if expr is None or guard is not None:
                    residue.append(
                        Residue(
                            owner,
                            f"{table}.{c['column_name']}",
                            "column",
                            guard
                            or "virtual column expression could not be"
                            " translated; recreate it by hand",
                        )
                    )
                    dropped.setdefault((owner, table), set()).add(cname)
                    continue
                suffix = f" GENERATED ALWAYS AS ({expr}) STORED"
            elif extra is not None and (extra["default_text"] or "").strip():
                if _IDENTITY_DEFAULT.search(extra["default_text"] or ""):
                    # Oracle identity columns carry their backing
                    # ISEQ$$ sequence as the stored default; the
                    # PostgreSQL shape is an identity column, which
                    # must sit on an integer type.
                    col_type = "bigint"
                    suffix = " GENERATED BY DEFAULT AS IDENTITY"
                    residue.append(
                        Residue(
                            owner,
                            f"{table}.{c['column_name']}",
                            "note",
                            "identity column; after data load, restart"
                            " the identity past the loaded maximum",
                        )
                    )
                elif extra["truncated"]:
                    residue.append(
                        Residue(
                            owner,
                            f"{table}.{c['column_name']}",
                            "note",
                            "default was truncated during extraction;"
                            " column emitted without it",
                        )
                    )
                elif (
                    seq := _SEQUENCE_DEFAULT.match(extra["default_text"])
                ) is not None:
                    # A default drawn from a sequence; PostgreSQL wants
                    # nextval over the converted sequence, by its
                    # catalog spelling, and only if it exists.
                    wanted = seq.group(2).strip('"').upper()
                    raw_seq = conn.execute(
                        "SELECT sequence_name FROM sequences"
                        " WHERE UPPER(sequence_name) = ? LIMIT 1",
                        (wanted,),
                    ).fetchone()
                    if raw_seq is not None and wanted in (sequence_names or set()):
                        suffix = (
                            f" DEFAULT nextval('{ident(raw_seq['sequence_name'])}')"
                        )
                    else:
                        residue.append(
                            Residue(
                                owner,
                                f"{table}.{c['column_name']}",
                                "note",
                                f"default draws from sequence {wanted}, which is"
                                " not in the converted set; column emitted"
                                " without it",
                            )
                        )
                elif extra["default_text"].replace(" ", "").upper() in _EMPTY_LOBS:
                    suffix = (
                        " DEFAULT "
                        + _EMPTY_LOBS[extra["default_text"].replace(" ", "").upper()]
                    )
                else:
                    folded = _fold_expression(extra["default_text"])
                    guard = (
                        None
                        if folded is None
                        else _default_guard(folded)
                        or _date_function_guard(folded, date_cols)
                        or _type_mismatch_guard(folded, families)
                        or _default_column_guard(folded)
                        or _literal_length_guard(folded, c)
                    )
                    if folded is None or guard is not None:
                        residue.append(
                            Residue(
                                owner,
                                f"{table}.{c['column_name']}",
                                "note",
                                (guard or "default could not be translated")
                                + "; column emitted without it",
                            )
                        )
                    else:
                        suffix = f" DEFAULT {folded}"
            if over_limit(c["column_name"] or ""):
                residue.append(
                    Residue(
                        owner,
                        f"{table}.{c['column_name']}",
                        "note",
                        "name exceeds PostgreSQL's 63-byte identifier"
                        " limit and will be truncated on apply",
                    )
                )
            lines.append(f"    {ident(c['column_name'])} {col_type}{suffix}{null}")
            kept_columns.add(cname)
        if not lines:
            residue.append(
                Residue(owner, table, "table", "every column was unconvertible")
            )
            continue
        byte_sized = [
            c["column_name"]
            for c in cols
            if (c["char_used"] or "").upper() == "B"
            and (c["data_type"] or "").upper() in ("VARCHAR2", "CHAR", "VARCHAR")
            and (c["column_name"] or "").upper() in kept_columns
        ]
        if byte_sized and multibyte:
            residue.append(
                Residue(
                    owner,
                    table,
                    "note",
                    f"{len(byte_sized)} string column(s) were declared in BYTE"
                    " semantics; PostgreSQL counts characters, so they accept"
                    " more text than Oracle did - add CHECK"
                    " (octet_length(col) <= n) where the byte limit carried"
                    " meaning",
                )
            )
        meta, part_reason = _partition_meta(conn, owner, table)
        if meta is not None:
            # PostgreSQL cannot partition by a generated column, nor by
            # a column that did not convert.
            gone = dropped.get((owner, table), set())
            for k in conn.execute(
                "SELECT column_name FROM part_key_columns"
                " WHERE owner = ? AND table_name = ? ORDER BY position",
                (owner, table),
            ):
                key = (k["column_name"] or "").upper()
                if key in virtual_columns:
                    part_reason = (
                        f"partition key {key} is a virtual column; PostgreSQL"
                        " cannot partition by a generated column - partition by"
                        " the expression itself by hand"
                    )
                elif key in gone or key not in kept_columns:
                    part_reason = f"partition key {key} was not converted"
                if part_reason is not None:
                    meta = None
                    break
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
        mv = mviews.get(((owner or "").upper(), (table or "").upper()))
        if mv is not None:
            refresh = (mv["refresh_method"] or "unknown").upper()
            reason = (
                "materialized view emitted as a plain table; the defining"
                " query is not in the inventory - recreate it as CREATE"
                " MATERIALIZED VIEW and schedule REFRESH by hand"
                f" (Oracle refresh method: {refresh})"
            )
            if (mv["rewrite_enabled"] or "N") == "Y":
                reason += (
                    "; query rewrite does not exist in PostgreSQL - point"
                    " queries at the materialized view directly"
                )
            residue.append(Residue(owner, table, "materialized view", reason))
        out.append(f"CREATE TABLE {ident(table)} (")
        out.append(",\n".join(lines))
        out.append(f"){meta.clause if meta else ''};")
        out.append("")
        table_count += 1
        emitted[(owner, table)] = kept_columns
        if meta is not None:
            partition_count += _emit_partition_children(
                conn, owner, table, meta, out, residue, names
            )

    return table_count, partition_count

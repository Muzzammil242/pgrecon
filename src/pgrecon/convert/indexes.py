"""Secondary index emission."""

import sqlite3

from pgrecon.convert.identifiers import (
    _date_function_guard,
    _default_guard,
    _fold_expression,
    _referenced_columns,
    _type_mismatch_guard,
    ident,
    over_limit,
)
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.residue import Residue
from pgrecon.convert.tables import _column_families, _date_columns
from pgrecon.convert.typemap import UNINDEXABLE


def _emit_indexes(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    names: NameRegistry,
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
    wrote = False
    for r in rows:
        if (r["index_name"] or "").upper().startswith("I_SNAP$"):
            # Oracle maintains these itself to support fast-refresh
            # materialized views; PostgreSQL needs no counterpart.
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "note",
                    "Oracle-internal materialized view support index;"
                    " nothing to create on PostgreSQL",
                )
            )
            continue
        if (r["owner"], r["table_name"]) not in emitted:
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "index",
                    "its table is outside the converted set",
                )
            )
            continue
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
        plain: list[str] = []
        skip_reason: str | None = None
        families = _column_families(conn, r["owner"], r["table_name"])
        for c in cols:
            expression, truncated = exprs.get(c["position"], (None, 0))
            if expression:
                if truncated:
                    skip_reason = (
                        "index expression was truncated during extraction;"
                        " recreate it from the source"
                    )
                    break
                folded = _fold_expression(expression)
                guard = (
                    None
                    if folded is None
                    else _default_guard(folded)
                    or _date_function_guard(
                        folded, _date_columns(conn, r["owner"], r["table_name"])
                    )
                    or _type_mismatch_guard(folded, families)
                )
                if folded is None or guard is not None:
                    skip_reason = guard or (
                        "index expression could not be translated;"
                        " recreate it from the source"
                    )
                    break
                present = {k.upper() for k in emitted[(r["owner"], r["table_name"])]}
                unknown = sorted((_referenced_columns(folded) or set()) - present)
                if unknown:
                    skip_reason = (
                        f"index expression references {unknown[0]}, which is not"
                        " a column of the converted table"
                    )
                    break
                parts.append(f"({folded})")
            elif (c["column_name"] or "").upper().startswith("SYS_NC"):
                skip_reason = (
                    "hidden function-based column without its expression;"
                    " recreate the index from the source"
                )
                break
            elif (c["column_name"] or "").upper() not in {
                k.upper() for k in emitted[(r["owner"], r["table_name"])]
            }:
                skip_reason = f"column {c['column_name']} was not converted"
                break
            elif families.get((c["column_name"] or "").upper()) in UNINDEXABLE:
                skip_reason = (
                    f"column {c['column_name']} lands as"
                    f" {families[(c['column_name'] or '').upper()]}, which has no"
                    " btree operator class; index an expression over it by hand"
                )
                break
            else:
                parts.append(ident(c["column_name"]))
                plain.append((c["column_name"] or "").upper())
        if skip_reason is None and (r["uniqueness"] or "").upper() == "UNIQUE":
            # A unique index on a partitioned table must carry every
            # partition key column, as a plain column.
            part_keys = [
                (k["column_name"] or "").upper()
                for k in conn.execute(
                    "SELECT column_name FROM part_key_columns"
                    " WHERE owner = ? AND table_name = ?",
                    (r["owner"], r["table_name"]),
                )
            ]
            uncovered = [k for k in part_keys if k not in plain]
            if uncovered:
                skip_reason = (
                    "PostgreSQL requires a unique index on a partitioned table"
                    f" to include every partition key; {uncovered[0]} is"
                    " missing - widen the index or enforce uniqueness another way"
                )
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
        raw_name = r["index_name"] or ""
        # Oracle indexes live in their own namespace; PostgreSQL puts
        # them beside tables, views, and sequences, so a colliding
        # index takes a suffixed name - nothing references an index by
        # name, which makes the rename safe. A collision caused by
        # 63-byte truncation cannot be suffixed away and refuses.
        holder = names.peek(raw_name)
        if holder is None:
            names.claim(raw_name, "index", r["owner"], residue)
            name = ident(raw_name)
        elif over_limit(raw_name):
            names.claim(raw_name, "index", r["owner"], residue)
            continue
        else:
            renamed = raw_name + "_IX"
            if not names.claim(renamed, "index", r["owner"], residue):
                continue
            name = ident(renamed)
            residue.append(
                Residue(
                    r["owner"],
                    raw_name,
                    "note",
                    f"shares its name with {holder[1]} {holder[0]};"
                    f" created as {name} because PostgreSQL keeps indexes"
                    " in the relation namespace",
                )
            )
        out.append(
            f"CREATE {unique}INDEX {name}"
            f" ON {ident(r['table_name'])} ({', '.join(parts)});"
        )
        wrote = True
        count += 1
    if wrote:
        out.append("")
    return count

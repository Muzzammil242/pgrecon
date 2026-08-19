"""Secondary index emission."""

import sqlite3

from pgrecon.convert.identifiers import _default_guard, _fold_expression, ident
from pgrecon.convert.residue import Residue


def _emit_indexes(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
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
                folded = _fold_expression(expression)
                guard = None if folded is None else _default_guard(folded)
                if folded is None or guard is not None:
                    skip_reason = guard or (
                        "index expression could not be translated;"
                        " recreate it from the source"
                    )
                    break
                parts.append(f"({folded})")
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
        name = ident(r["index_name"])
        # Oracle indexes live in their own namespace; PostgreSQL puts
        # them beside tables, so an index named after a table needs a
        # different name.
        if (r["index_name"] or "").upper() in {t for (_, t) in emitted}:
            name = ident(r["index_name"] + "_IX")
            residue.append(
                Residue(
                    r["owner"],
                    r["index_name"],
                    "note",
                    f"shares its name with a table; created as {name}"
                    " because PostgreSQL keeps indexes in the relation"
                    " namespace",
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

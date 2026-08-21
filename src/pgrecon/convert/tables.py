"""Table emission: typed columns, defaults, and partition children."""

import re
import sqlite3

from pgrecon.convert.identifiers import _default_guard, _fold_expression, ident
from pgrecon.convert.partitions import _emit_partition_children, _partition_meta
from pgrecon.convert.residue import Residue
from pgrecon.convert.typemap import map_type

# Oracle identity columns store their backing sequence as the column
# default; the name is always ISEQ$$_<object id>.
_IDENTITY_DEFAULT = re.compile(r"ISEQ\$\$_\d+.{0,4}NEXTVAL", re.IGNORECASE | re.DOTALL)


def _columns(conn: sqlite3.Connection, owner: str, table: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT column_name, data_type, data_length, data_precision,"
        " data_scale, nullable FROM columns"
        " WHERE owner = ? AND table_name = ? ORDER BY position",
        (owner, table),
    ).fetchall()


def emit_tables(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    skip_mviews: set[str] | None = None,
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

    for t in tables:
        owner, table = t["owner"], t["table_name"]
        if skip_mviews and (table or "").upper() in skip_mviews:
            continue
        cols = _columns(conn, owner, table)
        if not cols:
            residue.append(
                Residue(owner, table, "table", "no column facts in the inventory")
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
                expr = (
                    None
                    if extra["truncated"]
                    else _fold_expression(extra["default_text"] or "")
                )
                guard = None if expr is None else _default_guard(expr)
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
                else:
                    folded = _fold_expression(extra["default_text"])
                    guard = None if folded is None else _default_guard(folded)
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
            lines.append(f"    {ident(c['column_name'])} {col_type}{suffix}{null}")
            kept_columns.add(cname)
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
                conn, owner, table, meta, out, residue
            )

    return table_count, partition_count

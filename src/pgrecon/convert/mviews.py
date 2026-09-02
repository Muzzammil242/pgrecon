"""Materialized views rebuilt from their captured defining queries.

The extraction carries ALL_MVIEWS.QUERY since 0.5; with it, the
container table DBMS_METADATA hands over stops masquerading as a
plain table and becomes CREATE MATERIALIZED VIEW again. Without the
query - an older dump, or a pre-0.5 inventory - the container keeps
converting as a table with the residue note that names the loss.
"""

import sqlite3

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.transforms import eliminate_join_marks

from pgrecon.convert.identifiers import _fold_identifiers, ident
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.residue import Residue
from pgrecon.convert.views import _view_guard
from pgrecon.inventory.loader import PARSE_NORMALIZATIONS


def mview_queries(conn: sqlite3.Connection) -> dict[tuple[str, str], sqlite3.Row]:
    """Materialized views whose defining query made it into the dump,
    keyed by (owner, NAME). Tolerates inventories older than the
    query column."""
    try:
        rows = conn.execute(
            "SELECT owner, mview_name, rewrite_enabled, refresh_method, query"
            " FROM mviews WHERE query IS NOT NULL AND TRIM(query) != ''"
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {
        ((r["owner"] or "").upper(), (r["mview_name"] or "").upper()): r for r in rows
    }


def _emit_mviews(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    created_views: set[str],
    names: NameRegistry,
) -> int:
    """CREATE MATERIALIZED VIEW for every captured query that proves
    convertible; a named residue line for every one that does not."""
    queries = mview_queries(conn)
    if not queries:
        return 0

    count = 0
    for (owner, name), r in sorted(queries.items()):
        # Lookups and output use the catalog spelling; the uppercased
        # key only orders and cross-references.
        raw = r["mview_name"] or name
        raw_columns = [
            c["column_name"] or ""
            for c in conn.execute(
                "SELECT column_name FROM columns"
                " WHERE owner = ? AND table_name = ? ORDER BY position",
                (r["owner"] or owner, raw),
            )
        ]
        columns = [c.upper() for c in raw_columns]
        if not columns:
            residue.append(
                Residue(
                    owner, raw, "materialized view", "no column facts in the inventory"
                )
            )
            continue
        text = r["query"]
        for pattern, replacement in PARSE_NORMALIZATIONS:
            text = pattern.sub(replacement, text)
        try:
            parsed = sqlglot.parse(text, dialect="oracle")
            tree = parsed[0] if parsed else None
            if tree is None:
                raise SqlglotError("query did not parse")
            tree = eliminate_join_marks(tree)
            tree = _fold_identifiers(tree)
            statement = tree.sql(
                dialect="postgres", unsupported_level=ErrorLevel.RAISE, pretty=True
            )
        except SqlglotError as exc:
            reason = str(exc).splitlines()[0][:140]
            residue.append(
                Residue(
                    owner,
                    raw,
                    "materialized view",
                    f"defining query needs a manual rewrite: {reason}",
                )
            )
            continue
        if not isinstance(tree, exp.Select):
            residue.append(
                Residue(
                    owner,
                    raw,
                    "materialized view",
                    "defining query is not a plain SELECT; rewrite by hand",
                )
            )
            continue
        # The container's column list names the query's outputs one for
        # one; a query that yields a different number, or names two
        # outputs alike, cannot be mounted under that list.
        outputs = list(tree.expressions)
        if not any(isinstance(e, exp.Star) for e in outputs):
            if len(outputs) != len(columns):
                residue.append(
                    Residue(
                        owner,
                        raw,
                        "materialized view",
                        f"the defining query yields {len(outputs)} columns but"
                        f" the container has {len(columns)}; recreate the view"
                        " by hand",
                    )
                )
                continue
            aliases = [(e.alias_or_name or "").upper() for e in outputs]
            if len(set(aliases)) != len(aliases):
                residue.append(
                    Residue(
                        owner,
                        raw,
                        "materialized view",
                        "the defining query names two output columns alike;"
                        " recreate the view with distinct aliases",
                    )
                )
                continue
        guard = _view_guard(tree, name, emitted, dropped, created_views)
        if guard is not None:
            residue.append(Residue(owner, raw, "materialized view", guard))
            continue
        if not names.claim(raw, "materialized view", owner, residue):
            continue
        # The container's column names come first: Oracle derived them
        # from the query once, and indexes converted from the container
        # reference them by exactly these names.
        header = ", ".join(ident(c) for c in raw_columns)
        out.append(f"CREATE MATERIALIZED VIEW {ident(raw)} ({header}) AS\n{statement};")
        out.append("")
        emitted[(owner, name)] = set(columns)
        created_views.add(name)
        count += 1
        refresh = (r["refresh_method"] or "unknown").upper()
        residue.append(
            Residue(
                owner,
                raw,
                "note",
                f"Oracle refreshed this materialized view ({refresh});"
                " PostgreSQL refreshes on command - schedule REFRESH"
                " MATERIALIZED VIEW",
            )
        )
        if (r["rewrite_enabled"] or "N") == "Y":
            residue.append(
                Residue(
                    owner,
                    raw,
                    "note",
                    "query rewrite does not exist in PostgreSQL - point"
                    " queries at the materialized view directly",
                )
            )
    return count

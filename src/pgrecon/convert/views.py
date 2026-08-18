"""View emission via transpile of the stored DDL."""

import re
import sqlite3

import sqlglot
from sqlglot import Expr, exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.transforms import eliminate_join_marks

from pgrecon.convert.identifiers import _fold_identifiers
from pgrecon.convert.residue import Residue
from pgrecon.inventory.loader import PARSE_NORMALIZATIONS

_VIEW_HEADER_NOISE = re.compile(
    r"\b(FORCE|EDITIONABLE|NONEDITIONABLE)\s+", re.IGNORECASE
)

_PARTITION_SCOPED = re.compile(r"\bPARTITION\s*\(", re.IGNORECASE)
_OBJECT_METHOD = re.compile(r"\b\w+\.\w+\.\w+\s*\(")


def _view_guard(
    tree: Expr,
    view_name: str,
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    created_views: set[str],
    folded_sql: str,
) -> str | None:
    """Why a view cannot be emitted faithfully, or None."""
    referenced: list[str] = []
    for node in tree.walk():
        if isinstance(node, exp.Table):
            tname = node.name.upper()
            if "@" in node.name:
                return "reads through a database link"
            referenced.append(tname)
    known = {t for (_, t) in emitted} | created_views | {view_name.upper()}
    for tname in referenced:
        if tname not in known:
            return f"references {tname}, which is not in the converted set"
    if _OBJECT_METHOD.search(folded_sql):
        return "uses object-relational methods that have no counterpart"
    sources = [t for t in referenced if t != view_name.upper()]
    if len(set(sources)) == 1:
        gone = set()
        for (_owner, t), cols in dropped.items():
            if t == sources[0]:
                gone |= cols
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_$#]*", folded_sql)
        lost = sorted({t.upper() for t in tokens} & gone)
        if lost:
            return f"references {lost[0]}, a column that was not converted"
    return None


def _emit_views(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
) -> tuple[int, set[str]]:
    """Views via transpile of the stored DDL, in dependency order."""
    rows = conn.execute(
        "SELECT owner, name, ddl FROM ddl WHERE type = 'VIEW' ORDER BY name"
    ).fetchall()
    if not rows:
        return 0, set()
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
    wrote = False
    created_views: set[str] = set()
    for name in ordered:
        r = by_name[name]
        text = _VIEW_HEADER_NOISE.sub("", r["ddl"] or "")
        if _PARTITION_SCOPED.search(text):
            # sqlglot silently mangles FROM t PARTITION (p) into an
            # alias, so the shape is refused before parsing.
            residue.append(
                Residue(
                    r["owner"],
                    name,
                    "view",
                    "uses a partition-scoped query; PostgreSQL reads the"
                    " child table directly - rewrite by hand",
                )
            )
            continue
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
            tree = _fold_identifiers(tree)
            statement = tree.sql(
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
        guard = _view_guard(tree, name, emitted, dropped, created_views, statement)
        if guard is not None:
            residue.append(Residue(r["owner"], name, "view", guard))
            continue
        out.append(statement + ";")
        out.append("")
        created_views.add(name.upper())
        wrote = True
        count += 1
    if wrote and out and out[-1] != "":
        out.append("")
    return count, created_views

"""View emission via transpile of the stored DDL."""

import re
import sqlite3

import sqlglot
from sqlglot import Expr, exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.transforms import eliminate_join_marks

from pgrecon.convert.identifiers import _fold_identifiers, ident
from pgrecon.convert.residue import Residue
from pgrecon.inventory.loader import PARSE_NORMALIZATIONS

_VIEW_HEADER_NOISE = re.compile(
    r"\b(FORCE|EDITIONABLE|NONEDITIONABLE)\s+", re.IGNORECASE
)

_PARTITION_SCOPED = re.compile(r"\bPARTITION\s*\(", re.IGNORECASE)

_OBJECT_VIEW = re.compile(r"\bVIEW\s+\"?[^\s(]+\s+OF\s", re.IGNORECASE)

_JSON_TABLE = re.compile(r"\bJSON_TABLE\s*\(", re.IGNORECASE)


def _view_guard(
    tree: Expr,
    view_name: str,
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    created_views: set[str],
) -> str | None:
    """Why a view cannot be emitted faithfully, or None."""
    referenced: list[str] = []
    for node in tree.walk():
        if isinstance(node, exp.Table):
            tname = node.name.upper()
            if "@" in node.name:
                return "reads through a database link"
            referenced.append(tname)
        # A dotted chain ending in a call is an object-type method
        # invocation; the tree shows it directly.
        if isinstance(node, exp.Dot) and isinstance(
            node.expression, exp.Func | exp.Anonymous | exp.Dot
        ):
            return "uses object-relational methods that have no counterpart"
    known = {t for (_, t) in emitted} | created_views | {view_name.upper()}
    for tname in referenced:
        if tname not in known:
            return f"references {tname}, which is not in the converted set"
    sources = [t for t in referenced if t != view_name.upper()]
    if len(set(sources)) == 1:
        gone = set()
        for (_owner, t), cols in dropped.items():
            if t == sources[0]:
                gone |= cols
        lost = sorted({c.name.upper() for c in tree.find_all(exp.Column)} & gone)
        if lost:
            return f"references {lost[0]}, a column that was not converted"
    return None


def _connect_by_view(tree: Expr, declared: list[str]) -> tuple[str | None, str | None]:
    """A hierarchical query as WITH RECURSIVE, or a named refusal.

    The provable subset: one table, one PRIOR equality, projections of
    plain columns, LEVEL, and SYS_CONNECT_BY_PATH over a column with a
    literal separator. START WITH filters the base branch; a WHERE
    applies after the hierarchy, which is Oracle's evaluation order. A
    hidden key column carries the parent side of the join so the
    projection list does not have to.
    """
    select = tree.find(exp.Select)
    connect = tree.find(exp.Connect)
    if select is None or connect is None:
        return None, "the hierarchical query shape did not dissect"
    if connect.args.get("nocycle"):
        return None, (
            "CONNECT BY NOCYCLE breaks cycles at runtime; add a CYCLE"
            " clause to the recursive query by hand"
        )
    if select.args.get("joins"):
        return None, (
            "CONNECT BY combined with joins has no mechanical"
            " translation; rewrite the query by hand"
        )
    order = select.args.get("order")
    if order is not None and "SIBLINGS" in order.sql(dialect="oracle").upper():
        return None, (
            "ORDER SIBLINGS BY orders within each parent; order the"
            " recursive result by hand"
        )
    cond = connect.args.get("connect")
    if not isinstance(cond, exp.EQ):
        return None, (
            "only a single PRIOR equality converts mechanically;"
            " rewrite the CONNECT BY condition by hand"
        )
    sides = [cond.this, cond.expression]
    priors = [s for s in sides if isinstance(s, exp.Prior)]
    plains = [s for s in sides if isinstance(s, exp.Column)]
    if len(priors) != 1 or len(plains) != 1:
        return None, (
            "only a single PRIOR equality converts mechanically;"
            " rewrite the CONNECT BY condition by hand"
        )
    prior_inner = priors[0].this
    if not isinstance(prior_inner, exp.Column):
        return None, (
            "PRIOR over an expression has no mechanical translation;"
            " rewrite the condition by hand"
        )
    parent_col = ident(prior_inner.name)
    child_col = ident(plains[0].name)
    start = connect.args.get("start")
    if start is not None and (
        any(True for _ in start.find_all(exp.Prior))
        or any(c.name.lower() == "level" for c in start.find_all(exp.Column))
    ):
        return None, (
            "START WITH over PRIOR or LEVEL has no mechanical"
            " translation; rewrite the condition by hand"
        )

    names: list[str] = []
    base_items: list[str] = []
    rec_items: list[str] = []
    for proj in select.expressions:
        alias = None
        inner = proj
        if isinstance(proj, exp.Alias):
            alias = proj.alias
            inner = proj.this
        if isinstance(inner, exp.Column) and inner.name.lower() == "level":
            name = alias or "level"
            base_items.append("1")
            rec_items.append(f"h.{ident(name)} + 1")
        elif isinstance(inner, exp.Column):
            name = alias or inner.name
            column = ident(inner.name)
            base_items.append(column)
            rec_items.append(f"c.{column}")
        elif (
            isinstance(inner, exp.Anonymous)
            and str(inner.this).upper() == "SYS_CONNECT_BY_PATH"
            and len(inner.expressions) == 2
            and isinstance(inner.expressions[0], exp.Column)
            and isinstance(inner.expressions[1], exp.Literal)
            and inner.expressions[1].is_string
        ):
            name = alias or "path"
            column = ident(inner.expressions[0].name)
            separator = str(inner.expressions[1].this).replace("'", "''")
            base_items.append(f"concat('{separator}', {column})")
            rec_items.append(f"concat(h.{ident(name)}, '{separator}', c.{column})")
        else:
            return None, (
                f"projection {proj.sql(dialect='oracle')} is beyond plain"
                " columns, LEVEL, and SYS_CONNECT_BY_PATH; rewrite the"
                " view by hand"
            )
        names.append(name)
    if declared and len(declared) == len(names):
        names = list(declared)
    names = [ident(n) for n in names]

    tables = list(select.find_all(exp.Table))
    if len(tables) != 1:
        return None, (
            "CONNECT BY over more than one table has no mechanical"
            " translation; rewrite the query by hand"
        )
    source = ident(tables[0].name)

    key = "pgr_key"
    while key in names:
        key = key + "_"
    base_items.append(parent_col)
    rec_items.append(f"c.{parent_col}")

    base_where = ""
    if start is not None:
        base_where = f"\n  WHERE {start.sql(dialect='postgres')}"
    where = select.args.get("where")
    outer_where = ""
    if where is not None:
        outer_where = f"\nWHERE {where.this.sql(dialect='postgres')}"
    outer_order = ""
    if order is not None:
        outer_order = f"\n{order.sql(dialect='postgres')}"

    columns = ", ".join(names)
    statement = (
        f"WITH RECURSIVE hierarchy ({columns}, {key}) AS (\n"
        f"  SELECT {', '.join(base_items)}\n"
        f"  FROM {source}{base_where}\n"
        f"  UNION ALL\n"
        f"  SELECT {', '.join(rec_items)}\n"
        f"  FROM {source} AS c\n"
        f"  JOIN hierarchy AS h ON c.{child_col} = h.{key}\n"
        f")\n"
        f"SELECT {columns}\n"
        f"FROM hierarchy{outer_where}{outer_order}"
    )
    return statement, None


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
        if _OBJECT_VIEW.search(text) or "WITH OBJECT IDENTIFIER" in text.upper():
            residue.append(
                Residue(
                    r["owner"],
                    name,
                    "view",
                    "object views are built on object types, which have"
                    " no counterpart; port the type and view by hand",
                )
            )
            continue
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
        if _JSON_TABLE.search(text):
            residue.append(
                Residue(
                    r["owner"],
                    name,
                    "view",
                    "uses JSON_TABLE, which PostgreSQL adds in version 17"
                    " with different clause syntax; rewrite the view by"
                    " hand",
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
                folded = _fold_identifiers(tree)
                declared = (
                    [e.name for e in folded.this.expressions]
                    if isinstance(folded.this, exp.Schema)
                    else []
                )
                built, why = _connect_by_view(folded, declared)
                if built is None:
                    residue.append(
                        Residue(
                            r["owner"],
                            name,
                            "view",
                            why or "the hierarchical query did not dissect",
                        )
                    )
                    continue
                guard = _view_guard(folded, name, emitted, dropped, created_views)
                if guard is not None:
                    residue.append(Residue(r["owner"], name, "view", guard))
                    continue
                out.append(f"CREATE VIEW {ident(name.lower())} AS\n{built};")
                out.append("")
                created_views.add(name.upper())
                wrote = True
                count += 1
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
        guard = _view_guard(tree, name, emitted, dropped, created_views)
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

"""View emission via transpile of the stored DDL."""

import re
import sqlite3
from collections.abc import Callable

import sqlglot
from sqlglot import Expr, exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.transforms import eliminate_join_marks

from pgrecon.convert.identifiers import _fold_identifiers, _trunc_unit_guard, ident
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.residue import Residue
from pgrecon.inventory.loader import PARSE_NORMALIZATIONS

_VIEW_HEADER_NOISE = re.compile(
    r"\b(FORCE|EDITIONABLE|NONEDITIONABLE)\s+", re.IGNORECASE
)

_PARTITION_SCOPED = re.compile(r"\bPARTITION\s*\(", re.IGNORECASE)

_OBJECT_VIEW = re.compile(r"\bVIEW\s+\"?[^\s(]+\s+OF\s", re.IGNORECASE)

_JSON_TABLE = re.compile(r"\bJSON_TABLE\s*\(", re.IGNORECASE)


def _fold_rownum(tree: Expr) -> str | None:
    """Turn the top-N idiom into LIMIT, or say why the query cannot be.

    Oracle numbers rows before ORDER BY, so the faithful shape is a
    ROWNUM predicate over a sorted subquery; that predicate, as a
    conjunct of its query's WHERE with a literal bound, becomes LIMIT
    on that query. ROWNUM anywhere else - projected, compared with a
    column, under OR, or beside an ORDER BY in the same query - has
    no mechanical equal and declines by name.
    """
    rownums = [c for c in list(tree.find_all(exp.Column)) if c.name.upper() == "ROWNUM"]
    for column in rownums:
        comparison = column.parent
        if not isinstance(comparison, exp.LTE | exp.LT | exp.EQ):
            return "uses ROWNUM outside a top-N bound; rewrite by hand"
        other = comparison.expression if comparison.this is column else comparison.this
        if not (isinstance(other, exp.Literal) and not other.is_string):
            return "compares ROWNUM with something other than a number; rewrite by hand"
        bound = int(float(other.this))
        if isinstance(comparison, exp.LT):
            bound -= 1
        elif isinstance(comparison, exp.EQ) and bound != 1:
            return "ROWNUM = n with n above 1 never matches; rewrite by hand"
        node: Expr = comparison
        while isinstance(node.parent, exp.And):
            node = node.parent
        where = node.parent
        if not isinstance(where, exp.Where) or not isinstance(where.parent, exp.Select):
            return "uses ROWNUM outside a plain WHERE conjunction; rewrite by hand"
        select = where.parent
        if select.args.get("order") is not None:
            return (
                "ROWNUM beside ORDER BY in the same query is not top-N on"
                " Oracle either; sort in a subquery, then bound, by hand"
            )
        if select.args.get("limit") is not None:
            return "uses ROWNUM twice; rewrite by hand"
        parent = comparison.parent
        if isinstance(parent, exp.And):
            sibling = parent.expression if parent.this is comparison else parent.this
            parent.replace(sibling)
        else:
            select.set("where", None)
        select.limit(bound, copy=False)
    return None


def _view_guard(
    tree: Expr,
    view_name: str,
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    created_views: set[str],
) -> str | None:
    """Why a view cannot be emitted faithfully, or None."""
    unit_guard = _trunc_unit_guard(tree)
    if unit_guard is not None:
        return unit_guard
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
    known = {t.upper() for (_, t) in emitted} | created_views | {view_name.upper()}
    for tname in referenced:
        if tname not in known:
            return f"references {tname}, which is not in the converted set"
    sources = [t for t in referenced if t != view_name.upper()]
    if len(set(sources)) == 1:
        gone = set()
        for (_owner, t), cols in dropped.items():
            if t.upper() == sources[0]:
                gone |= {c.upper() for c in cols}
        lost = sorted({c.name.upper() for c in tree.find_all(exp.Column)} & gone)
        if lost:
            return f"references {lost[0]}, a column that was not converted"
        # Over one table, every column named must be one the converted
        # table has, or an alias the query itself defines; a spool cut
        # short can leave a view naming a column that is not there.
        present: set[str] | None = None
        for (_owner, t), cols in emitted.items():
            if t.upper() == sources[0]:
                present = {c.upper() for c in cols}
        aliases = {(e.alias or "").upper() for e in tree.find_all(exp.Alias) if e.alias}
        if present is not None and tree.find(exp.Connect) is None:
            unknown = sorted(
                {c.name.upper() for c in tree.find_all(exp.Column)}
                - present
                - aliases
                - {"ROWNUM", "LEVEL", "ROWID", "USER", "SYSDATE"}
            )
            if unknown:
                return f"references {unknown[0]}, which is not a column of {sources[0]}"
    return None


def _connect_by_view(
    tree: Expr,
    declared: list[str],
    families: Callable[[str], dict[str, str]] | None = None,
) -> tuple[str | None, str | None]:
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
    source_tables = list(select.find_all(exp.Table))
    if families is not None and len(source_tables) == 1:
        # Oracle compares NUMBER with VARCHAR2 by converting one side;
        # PostgreSQL has no such operator, so the join would not parse.
        known = families(source_tables[0].name)
        parent_family = known.get(prior_inner.name.upper())
        child_family = known.get(plains[0].name.upper())
        if parent_family and child_family and parent_family != child_family:
            return None, (
                f"PRIOR {parent_col} = {child_col} compares {parent_family} with"
                f" {child_family}; Oracle converts implicitly, PostgreSQL does"
                " not - cast one side by hand"
            )
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
    registry: NameRegistry,
) -> tuple[int, set[str]]:
    """Views via transpile of the stored DDL, in dependency order."""
    rows = conn.execute(
        "SELECT owner, name, ddl FROM ddl WHERE type = 'VIEW' ORDER BY name"
    ).fetchall()
    names = {r["name"] for r in rows}
    # A view the catalog lists but whose DDL never reached the dump -
    # DBMS_METADATA failed on it, or the spool was cut - is declined
    # by name rather than forgotten.
    for o in conn.execute(
        "SELECT owner, name FROM objects WHERE type = 'VIEW' ORDER BY owner, name"
    ):
        if o["name"] not in names:
            residue.append(
                Residue(
                    o["owner"],
                    o["name"],
                    "view",
                    "no DDL for this view reached the dump; extract it by hand",
                )
            )
    if not rows:
        return 0, set()
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
    # Column families of the converted tables, for the hierarchy guard.
    by_upper = {t.upper(): (o, t) for (o, t) in emitted}

    def families(table: str) -> dict[str, str]:
        from pgrecon.convert.tables import _column_families

        found = by_upper.get(table.upper())
        return _column_families(conn, *found) if found else {}

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
            rownum_reason = _fold_rownum(tree)
            if rownum_reason is not None:
                residue.append(Residue(r["owner"], name, "view", rownum_reason))
                continue
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
                built, why = _connect_by_view(folded, declared, families)
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
                if not registry.claim(name, "view", r["owner"], residue):
                    continue
                out.append(f"CREATE VIEW {ident(name)} AS\n{built};")
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
        if not registry.claim(name, "view", r["owner"], residue):
            continue
        out.append(statement + ";")
        out.append("")
        created_views.add(name.upper())
        wrote = True
        count += 1
    if wrote and out and out[-1] != "":
        out.append("")
    return count, created_views

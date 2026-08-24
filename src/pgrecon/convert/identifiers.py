"""Identifier folding and expression translation helpers."""

import re
from collections.abc import Iterable

import sqlglot
from sqlglot import Expr, exp
from sqlglot.errors import SqlglotError

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


def ident(name: str) -> str:
    """Fold to lowercase; quote only when the result needs it."""
    lowered = name.lower()
    if _PLAIN_IDENT.match(lowered) and lowered not in _RESERVED:
        return lowered
    return '"' + name.replace('"', '""') + '"'


# PostgreSQL truncates identifiers to 63 bytes at parse time, quoted
# or not, keeping multibyte characters whole. Oracle allows 128 bytes
# from 12.2, so catalog names can arrive past the limit; two of them
# agreeing on their first 63 bytes would fold to the same name and
# make the DDL fail.
_NAMEDATALEN = 63


def over_limit(name: str) -> bool:
    return len(name.encode("utf-8")) > _NAMEDATALEN


def pg_truncate(name: str) -> str:
    """The name PostgreSQL will actually store."""
    cut = name.encode("utf-8")[:_NAMEDATALEN]
    while cut:
        try:
            return cut.decode("utf-8")
        except UnicodeDecodeError:
            cut = cut[:-1]
    return ""


def truncation_clash(names: Iterable[str]) -> tuple[str, str] | None:
    """The first pair of names PostgreSQL would fold together, if any."""
    seen: dict[str, str] = {}
    for name in names:
        key = pg_truncate(name.lower())
        prior = seen.get(key)
        if prior is not None and prior != name:
            return prior, name
        seen[key] = name
    return None


def _concat_parts(node: Expr) -> list[Expr]:
    """The operands of a concatenation, flattened across its links."""
    if isinstance(node, exp.DPipe):
        return _concat_parts(node.this) + _concat_parts(node.expression)
    if isinstance(node, exp.Concat):
        parts: list[Expr] = []
        for operand in node.expressions:
            parts.extend(_concat_parts(operand))
        return parts
    return [node]


def _fold_identifiers(tree: Expr) -> Expr:
    """Lowercase and unquote identifiers; drop schema qualifiers.

    DBMS_METADATA quotes every identifier in uppercase; carried as-is
    the view would reference "EMP" while the converted table is emp.
    Single-schema conversion also drops the owner prefix.

    Concatenation chains become NULLIF(concat(...), ''): Oracle ||
    treats NULL as the empty string where PostgreSQL || yields NULL,
    concat() ignores NULLs, and NULLIF restores the one case Oracle
    does return NULL - every part empty, since in Oracle '' IS NULL.
    The concat call is emitted anonymously because sqlglot renders its
    own Concat node back to || on the postgres dialect.
    """
    for node in tree.walk():
        if isinstance(node, exp.Identifier):
            node.set("this", node.name.lower())
            node.set("quoted", not _PLAIN_IDENT.match(node.name.lower()))
        if isinstance(node, exp.Table | exp.Column) and node.args.get("db"):
            node.set("db", None)
    chains = [
        node
        for node in tree.walk()
        if isinstance(node, exp.DPipe | exp.Concat)
        and not isinstance(node.parent, exp.DPipe | exp.Concat)
    ]
    for chain in chains:
        chain.replace(
            exp.Nullif(
                this=exp.Anonymous(this="concat", expressions=_concat_parts(chain)),
                expression=exp.Literal.string(""),
            )
        )
    stamps = [node for node in tree.walk() if _func_name(node) == "SYSTIMESTAMP"]
    for node in stamps:
        node.replace(exp.CurrentTimestamp())
    # Oracle GROUPING_ID(a, b) and PostgreSQL GROUPING(a, b) return
    # the same bit vector; only the name differs.
    grouping = [n for n in tree.walk() if isinstance(n, exp.GroupingId)]
    for node in grouping:
        node.replace(exp.Anonymous(this="GROUPING", expressions=node.expressions))
    # The postgres generator casts every division's numerator to
    # double precision to avoid integer division; Oracle NUMBER
    # arithmetic is exact decimal, and PostgreSQL's two-argument
    # round() exists only for numeric, so cast to decimal instead -
    # a numerator already cast by the source stays as written.
    for node in tree.walk():
        if isinstance(node, exp.Div) and not isinstance(node.this, exp.Cast):
            node.set("this", exp.Cast(this=node.this, to=exp.DataType.build("DECIMAL")))
    # Oracle folds '' to NULL, so a DECODE argument written as '' is a
    # NULL search, result, or default; compared as a real empty string
    # it would never match. The rest of the translation is sqlglot's
    # CASE, which renders NULL searches as IS NULL and column searches
    # with a both-NULL match - DECODE's null-equals-null rule.
    for node in tree.walk():
        if isinstance(node, exp.DecodeCase):
            for item in list(node.expressions):
                if isinstance(item, exp.Literal) and item.is_string and not item.this:
                    item.replace(exp.Null())
    return tree


def _fold_expression(expression: str) -> str | None:
    """An index expression folded to converted identifiers, or None."""
    try:
        parsed = sqlglot.parse(f"SELECT {expression}", dialect="oracle")
        tree = parsed[0] if parsed else None
        if tree is None:
            return None
        select = _fold_identifiers(tree).find(exp.Select)
        if select is None or not select.expressions:
            return None
        return str(select.expressions[0].sql(dialect="postgres"))
    except SqlglotError:
        return None


def _fold_condition(condition: str) -> str | None:
    """A check condition with identifiers folded, or None to decline.

    Oracle stores conditions with quoted uppercase identifiers that
    would miss the lowercase columns this converter creates; the same
    folding the views get fixes them, through a throwaway SELECT.
    """
    try:
        parsed = sqlglot.parse(f"SELECT 1 WHERE {condition}", dialect="oracle")
        tree = parsed[0] if parsed else None
        if tree is None:
            return None
        where = _fold_identifiers(tree).find(exp.Where)
        if where is None:
            return None
        return str(where.this.sql(dialect="postgres"))
    except SqlglotError:
        return None


_UNSUPPORTED_EXPR_FUNCS = {"SYS_GUID", "SYS_CONTEXT", "USERENV"}


def _func_name(node: Expr) -> str:
    """The call name of a function node, uppercased; '' otherwise."""
    if isinstance(node, exp.Anonymous):
        return str(node.this).upper()
    if isinstance(node, exp.Func):
        return node.sql_name().upper()
    return ""


def _reparse(folded: str) -> Expr | None:
    try:
        parsed = sqlglot.parse(f"SELECT {folded}", dialect="postgres")
        return parsed[0] if parsed else None
    except SqlglotError:
        return None


def _default_guard(folded: str) -> str | None:
    """Why a folded expression cannot ship, or None.

    The fold makes syntax valid; this walks the tree for calls
    PostgreSQL does not have. SYS_GUID and the context readers have
    no counterpart, and TO_DATE over a non-literal folds into a
    signature that does not exist. Walking nodes rather than text
    means a string literal that merely mentions SYS_GUID stays
    innocent.
    """
    tree = _reparse(folded)
    if tree is None:
        return "expression could not be re-checked; rewrite it by hand"
    for node in tree.walk():
        name = _func_name(node)
        if name in _UNSUPPORTED_EXPR_FUNCS or name.startswith("SYS_OP_"):
            return (
                f"{name} has no PostgreSQL counterpart here; choose a"
                " replacement by hand"
            )
        if name in ("TO_DATE", "STR_TO_DATE"):
            if isinstance(node, exp.Anonymous):
                first = node.expressions[0] if node.expressions else None
            else:
                first = node.args.get("this")
            if not (isinstance(first, exp.Literal) and first.is_string):
                return (
                    "TO_DATE over a non-literal has no matching"
                    " PostgreSQL signature; rewrite it by hand"
                )
    return None


def _referenced_columns(folded: str) -> set[str] | None:
    """Column names a folded condition references, or None on reparse
    failure so the caller can fall back to a token scan."""
    tree = _reparse(f"1 WHERE {folded}")
    if tree is None:
        return None
    return {c.name.upper() for c in tree.find_all(exp.Column)}

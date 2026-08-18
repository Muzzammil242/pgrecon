"""Identifier folding and expression translation helpers."""

import re

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


_NO_PG_DEFAULT_FUNCS = re.compile(
    r"\b(SYS_GUID|SYS_CONTEXT|USERENV)\s*\(", re.IGNORECASE
)
_TO_DATE_NONLITERAL = re.compile(r"\bTO_DATE\s*\(\s*[^')]", re.IGNORECASE)


def _default_guard(folded: str) -> str | None:
    """Why a folded default expression cannot ship, or None.

    The fold makes syntax valid; this catches functions PostgreSQL
    does not have. SYS_GUID and the context readers have no
    counterpart, and TO_DATE over a non-literal folds into a
    signature that does not exist.
    """
    m = _NO_PG_DEFAULT_FUNCS.search(folded)
    if m:
        return (
            f"{m.group(1).upper()} has no PostgreSQL counterpart in a"
            " default; choose a replacement by hand"
        )
    if _TO_DATE_NONLITERAL.search(folded):
        return (
            "TO_DATE over a non-literal has no matching PostgreSQL"
            " signature; rewrite the default by hand"
        )
    return None

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


def fold_case(name: str) -> str:
    """The spelling PostgreSQL will know the name by.

    Oracle stores a name created without quotes in uppercase and
    matches it case-insensitively; PostgreSQL does the same in
    lowercase, so those fold. A name carrying lowercase letters was
    created quoted and case-sensitive on Oracle and keeps its
    spelling exactly. Every emitter goes through this one rule, so a
    table, its comments, its grants, its checks, and the views over
    it all spell the name the same way.
    """
    return name.lower() if name == name.upper() else name


def ident(name: str) -> str:
    """Fold to PostgreSQL's case; quote only when the result needs it."""
    folded = fold_case(name)
    if _PLAIN_IDENT.match(folded) and folded not in _RESERVED:
        return folded
    return '"' + folded.replace('"', '""') + '"'


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
        key = pg_truncate(fold_case(name))
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


# Oracle TRUNC(date, format) formats that name a date_trunc field.
# Week formats other than ISO, day-of-week formats, and ISO years have
# no field and decline.
_TRUNC_UNITS = {
    "CC": "century",
    "SCC": "century",
    "SYYYY": "year",
    "YYYY": "year",
    "YEAR": "year",
    "SYEAR": "year",
    "YYY": "year",
    "YY": "year",
    "Y": "year",
    "Q": "quarter",
    "MONTH": "month",
    "MON": "month",
    "MM": "month",
    "RM": "month",
    "IW": "week",
    "DDD": "day",
    "DD": "day",
    "J": "day",
    "HH": "hour",
    "HH12": "hour",
    "HH24": "hour",
    "MI": "minute",
}
_PG_TRUNC_FIELDS = {
    "microseconds",
    "milliseconds",
    "second",
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "quarter",
    "year",
    "decade",
    "century",
    "millennium",
}


def _trunc_unit_guard(tree: Expr) -> str | None:
    """Why a date truncation cannot ship, or None.

    sqlglot turns Oracle TRUNC over a date into date_trunc but keeps
    the Oracle format string; the fold maps the formats that have a
    field, and whatever is left has none.
    """
    for node in tree.walk():
        if isinstance(node, exp.DateTrunc | exp.TimestampTrunc):
            unit = node.args.get("unit")
        elif _func_name(node) == "DATE_TRUNC" and isinstance(node, exp.Anonymous):
            # The postgres dialect re-reads an unknown field as a plain
            # call; the first argument is the field.
            unit = node.expressions[0] if node.expressions else None
        else:
            continue
        # A literal on the Oracle side, a bare field name once the
        # postgres dialect has re-read its own output.
        text = unit.name if unit is not None else ""
        if text.lower() not in _PG_TRUNC_FIELDS:
            return (
                f"TRUNC format '{text}' has no date_trunc field in"
                " PostgreSQL; rewrite it by hand"
            )
    return None


def _fold_identifiers(tree: Expr) -> Expr:
    """Fold identifiers to the converter's spelling; drop schema qualifiers.

    DBMS_METADATA quotes every identifier in uppercase; carried as-is
    the view would reference "EMP" while the converted table is emp.
    The fold is the same one ident() applies to DDL, so case-sensitive
    and reserved names come out spelled exactly as their objects were
    created. Single-schema conversion also drops the owner prefix.

    Concatenation chains become NULLIF(concat(...), ''): Oracle ||
    treats NULL as the empty string where PostgreSQL || yields NULL,
    concat() ignores NULLs, and NULLIF restores the one case Oracle
    does return NULL - every part empty, since in Oracle '' IS NULL.
    The concat call is emitted anonymously because sqlglot renders its
    own Concat node back to || on the postgres dialect.
    """
    # Oracle's raw conversions have PostgreSQL spellings.
    for node in list(tree.walk()):
        if not isinstance(node, exp.Anonymous) or not node.expressions:
            continue
        name = str(node.this).upper()
        if name == "HEXTORAW":
            node.replace(
                exp.Anonymous(
                    this="decode",
                    expressions=[node.expressions[0], exp.Literal.string("hex")],
                )
            )
        elif name == "RAWTOHEX":
            node.replace(
                exp.Anonymous(
                    this="encode",
                    expressions=[node.expressions[0], exp.Literal.string("hex")],
                )
            )
    # Oracle's USER is a function spelled like a column; a column that
    # is really named USER arrives quoted from the catalog and stays.
    # It runs before the fold, which would quote the reserved word.
    for node in list(tree.walk()):
        if (
            isinstance(node, exp.Column)
            and node.name.upper() == "USER"
            and not node.args.get("table")
            and isinstance(node.this, exp.Identifier)
            and not node.this.quoted
        ):
            node.replace(exp.CurrentUser())
    for node in tree.walk():
        if isinstance(node, exp.Identifier):
            folded = fold_case(node.name)
            node.set("this", folded)
            node.set("quoted", not _PLAIN_IDENT.match(folded) or folded in _RESERVED)
        if isinstance(node, exp.Table | exp.Column) and node.args.get("db"):
            node.set("db", None)
        if isinstance(node, exp.DateTrunc | exp.TimestampTrunc):
            unit = node.args.get("unit")
            if isinstance(unit, exp.Literal) and unit.is_string:
                mapped = _TRUNC_UNITS.get(str(unit.this).upper())
                if mapped is not None:
                    unit.set("this", mapped)
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
        folded = _fold_identifiers(tree)
        if _trunc_unit_guard(folded) is not None:
            # The postgres dialect normalizes unknown fields when it
            # re-reads its own output, so the check runs here, on the
            # Oracle-side tree, or not at all.
            return None
        select = folded.find(exp.Select)
        if select is None or not select.expressions:
            return None
        head = select.expressions[0]
        if isinstance(head, exp.Alias) or len(select.expressions) != 1:
            # An index expression is one expression; a trailing DESC or
            # a stray comma parses as an alias or a second column and
            # would ship as nonsense.
            return None
        return str(head.sql(dialect="postgres"))
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
        folded = _fold_identifiers(tree)
        if _trunc_unit_guard(folded) is not None:
            return None
        where = folded.find(exp.Where)
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
    unit_guard = _trunc_unit_guard(tree)
    if unit_guard is not None:
        return unit_guard
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


_DATE_SOURCES = {
    "CURRENT_TIMESTAMP",
    "CURRENT_DATE",
    "NOW",
    "TO_DATE",
    "TO_TIMESTAMP",
    "STR_TO_DATE",
    "LOCALTIMESTAMP",
}


def _date_function_guard(folded: str, date_columns: set[str]) -> str | None:
    """Why a folded expression misuses a date, or None.

    Oracle TRUNC and ROUND accept dates; PostgreSQL's do not, and the
    fold cannot know a column's type. Callers pass the table's date
    and timestamp columns so TRUNC(created) declines by name instead
    of shipping DDL the server rejects; a date function as the
    argument declines the same way.
    """
    tree = _reparse(folded)
    if tree is None:
        return None
    for node in tree.walk():
        name = _func_name(node)
        if name not in ("TRUNC", "ROUND"):
            continue
        if isinstance(node, exp.Anonymous):
            first = node.expressions[0] if node.expressions else None
        else:
            first = node.args.get("this")
        if isinstance(first, exp.Column) and first.name.upper() in date_columns:
            return (
                f"{name} over date column {first.name.upper()} has no PostgreSQL"
                " counterpart; use date_trunc by hand"
            )
        if first is not None and (
            _func_name(first) in _DATE_SOURCES
            or isinstance(first, exp.CurrentTimestamp | exp.CurrentDate)
        ):
            return (
                f"{name} over a date expression has no PostgreSQL counterpart;"
                " use date_trunc by hand"
            )
    return None


_TEXT_FUNCS = {
    "UPPER",
    "LOWER",
    "INITCAP",
    "TRIM",
    "LTRIM",
    "RTRIM",
    "LENGTH",
    "SUBSTR",
    "SUBSTRING",
    "INSTR",
    "STRPOS",
    "REPLACE",
    "LPAD",
    "RPAD",
    "TRANSLATE",
    "REGEXP_LIKE",
    "REGEXP_REPLACE",
    "REGEXP_SUBSTR",
}
_NUMBER_FUNCS = {"ABS", "FLOOR", "CEIL", "CEILING", "MOD", "POWER", "SQRT", "SIGN"}


def _first_argument(node: Expr) -> Expr | None:
    if isinstance(node, exp.Anonymous):
        return node.expressions[0] if node.expressions else None
    return node.args.get("this")


def _family_of(node: Expr, families: dict[str, str]) -> str | None:
    if isinstance(node, exp.Column):
        return families.get(node.name.upper())
    if isinstance(node, exp.Literal):
        return "text" if node.is_string else "number"
    return None


def _type_mismatch_guard(folded: str, families: dict[str, str]) -> str | None:
    """Why an expression leans on Oracle's implicit conversions, or None.

    Oracle upper-cases a NUMBER and coalesces a VARCHAR2 with 0 by
    converting silently; PostgreSQL refuses both. The callers pass the
    table's column families so the expression is checked where the
    types are known, and declines by name instead of shipping.
    """
    tree = _reparse(folded)
    if tree is None:
        return None
    for node in tree.walk():
        name = _func_name(node)
        if name in _TEXT_FUNCS or name in _NUMBER_FUNCS or name in ("TRUNC", "ROUND"):
            first = _first_argument(node)
            family = _family_of(first, families) if first is not None else None
            wanted = "text" if name in _TEXT_FUNCS else "number"
            if name in ("TRUNC", "ROUND") and family == "datetime":
                continue  # the date guard owns that case
            if (
                isinstance(first, exp.Column)
                and family is not None
                and family != wanted
            ):
                return (
                    f"{name} over {family} column {first.name.upper()} relies on"
                    " Oracle's implicit conversion; cast it explicitly by hand"
                )
        if isinstance(node, exp.Coalesce):
            seen = {
                f
                for f in (
                    _family_of(arg, families) for arg in [node.this, *node.expressions]
                )
                if f is not None
            }
            if len(seen) > 1:
                return (
                    "COALESCE mixes " + " and ".join(sorted(seen)) + "; Oracle"
                    " converted implicitly, PostgreSQL will not - cast by hand"
                )
    return None


def _default_column_guard(folded: str) -> str | None:
    """Why a column default cannot ship, or None.

    A default cannot read other columns on PostgreSQL, and every Oracle
    pseudo-column the fold did not translate - UID, ROWNUM, LEVEL -
    reaches here looking like one.
    """
    tree = _reparse(folded)
    if tree is None:
        return None
    for node in tree.walk():
        if isinstance(node, exp.Column):
            return (
                f"default refers to {node.name.upper()}, a column or Oracle"
                " pseudo-column; PostgreSQL defaults cannot - choose a"
                " replacement by hand"
            )
    return None


def _referenced_columns(folded: str) -> set[str] | None:
    """Column names a folded condition references, or None on reparse
    failure so the caller can fall back to a token scan."""
    tree = _reparse(f"1 WHERE {folded}")
    if tree is None:
        return None
    return {c.name.upper() for c in tree.find_all(exp.Column)}

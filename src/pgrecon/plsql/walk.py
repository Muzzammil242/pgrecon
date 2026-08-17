"""Feature extraction from parsed PL/SQL units.

One analysis pass produces the deep facts the rule engine queries:
a listener walk over the parse tree for statement-level constructs,
and a scan of the default token channel for function-level ones.
Comments and string literals reach neither, which is the point of the
exercise: a SYSDATE in a comment is not a finding.
"""

import re
from dataclasses import dataclass
from typing import Any

from antlr4 import ParseTreeWalker

from pgrecon.plsql import parse_source
from pgrecon.plsql._generated.PlSqlLexer import PlSqlLexer
from pgrecon.plsql._generated.PlSqlParserListener import PlSqlParserListener


@dataclass(frozen=True)
class Feature:
    feature: str
    line: int
    detail: str | None


@dataclass(frozen=True)
class Call:
    callee: str
    line: int


@dataclass(frozen=True)
class UnitAnalysis:
    mode: str
    errors: tuple[str, ...]
    features: tuple[Feature, ...]
    calls: tuple[Call, ...]


class _FeatureListener(PlSqlParserListener):  # type: ignore[misc]
    def __init__(self) -> None:
        self.features: list[Feature] = []
        self.calls: list[Call] = []

    def _add(self, ctx: Any, feature: str, detail: str | None = None) -> None:
        self.features.append(Feature(feature, ctx.start.line, detail))

    def enterCommit_statement(self, ctx: Any) -> None:
        self._add(ctx, "commit")

    def enterRollback_statement(self, ctx: Any) -> None:
        self._add(ctx, "rollback")

    def enterExecute_immediate(self, ctx: Any) -> None:
        self._add(ctx, "execute_immediate")

    def enterGoto_statement(self, ctx: Any) -> None:
        self._add(ctx, "goto")

    def enterForall_statement(self, ctx: Any) -> None:
        self._add(ctx, "forall")

    def enterHierarchical_query_clause(self, ctx: Any) -> None:
        self._add(ctx, "connect_by")

    def enterOuter_join_sign(self, ctx: Any) -> None:
        self._add(ctx, "outer_join_plus")

    def enterVarray_type_def(self, ctx: Any) -> None:
        self._add(ctx, "collection_type", "varray")

    def enterTable_type_def(self, ctx: Any) -> None:
        # TABLE OF ... INDEX BY is an associative array; without the
        # INDEX BY part it is a nested table. Both need rework, but
        # the remedies differ, so the detail says which one it is.
        kind = "associative array" if ctx.table_indexed_by_part() else "nested table"
        self._add(ctx, "collection_type", kind)

    def enterNested_table_type_def(self, ctx: Any) -> None:
        # The CREATE TYPE ... AS TABLE OF form, outside PL/SQL blocks.
        self._add(ctx, "collection_type", "nested table")

    def enterPragma_declaration(self, ctx: Any) -> None:
        if "AUTONOMOUS_TRANSACTION" in ctx.getText().upper():
            self._add(ctx, "autonomous_transaction")

    def enterException_handler(self, ctx: Any) -> None:
        names = [n.getText().upper() for n in ctx.exception_name()]
        if "OTHERS" not in names:
            return
        seq = ctx.seq_of_statements()
        if seq is None:
            return
        if [s.getText().upper() for s in seq.statement()] == ["NULL"]:
            self._add(ctx, "when_others_null")

    def enterMerge_statement(self, ctx: Any) -> None:
        self._add(ctx, "merge")

    def enterRef_cursor_type_def(self, ctx: Any) -> None:
        self._add(ctx, "ref_cursor")

    def enterCall_statement(self, ctx: Any) -> None:
        names = [r.getText().upper() for r in ctx.routine_name()]
        self.calls.append(Call(".".join(names), ctx.start.line))

    def enterGeneral_element(self, ctx: Any) -> None:
        # Record only the outermost element of a dotted chain, and only
        # when it carries an argument list: a call site, not a variable
        # or record-field reference. Callees that name no known object
        # (local variables with methods, unhandled builtins) resolve to
        # nothing when queried, which is harmless.
        if type(ctx.parentCtx).__name__ == "General_elementContext":
            return
        text = ctx.getText()
        if "(" not in text:
            return
        callee = text.upper().split("(", 1)[0].rstrip(".")
        if callee:
            self.calls.append(Call(callee, ctx.start.line))


_CURSOR_ATTRIBUTES = {
    PlSqlLexer.PERCENT_ROWCOUNT,
    PlSqlLexer.PERCENT_FOUND,
    PlSqlLexer.PERCENT_NOTFOUND,
    PlSqlLexer.PERCENT_ISOPEN,
}

_PLAIN_TOKENS = {
    PlSqlLexer.SYSDATE: "sysdate",
    PlSqlLexer.ROWNUM: "rownum",
    PlSqlLexer.PIPELINED: "pipelined",
    PlSqlLexer.ROWID: "rowid",
    PlSqlLexer.UROWID: "rowid",
}


def _scan_tokens(stream: Any) -> list[Feature]:
    """Collect function-level features from the default token channel.

    The lexer routes comments and string literals to other channels,
    so a keyword token here is a keyword in live code. Lookahead and
    lookbehind separate DECODE the function from DECODE the identifier
    and SQL%ROWCOUNT from a named cursor's c%ROWCOUNT.
    """
    tokens = [t for t in stream.tokens if t.channel == 0]
    features = []
    for i, token in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        prev = tokens[i - 1] if i > 0 else None
        if token.type in _PLAIN_TOKENS:
            features.append(Feature(_PLAIN_TOKENS[token.type], token.line, None))
        elif token.type == PlSqlLexer.DECODE:
            if nxt is not None and nxt.type == PlSqlLexer.LEFT_PAREN:
                features.append(Feature("decode_call", token.line, None))
        elif token.type == PlSqlLexer.BULK:
            if nxt is not None and nxt.type == PlSqlLexer.COLLECT:
                features.append(Feature("bulk_collect", token.line, None))
        elif (
            token.type == PlSqlLexer.REGULAR_ID
            and token.text.upper() == "SYS_REFCURSOR"
        ):
            # SYS_REFCURSOR is not a keyword to the lexer, just a
            # predefined type name; Ref_cursor_type_def catches the
            # TYPE ... IS REF CURSOR declarations.
            features.append(Feature("ref_cursor", token.line, None))
        elif token.type == PlSqlLexer.CHAR_STRING and token.text == "''":
            # A standalone empty-string literal, which Oracle treats as
            # NULL and PostgreSQL does not. An escaped quote inside a
            # string ('don''t') is one CHAR_STRING token and never
            # matches here, which is what text matching gets wrong.
            features.append(Feature("empty_string_literal", token.line, None))
        elif (
            token.type in _CURSOR_ATTRIBUTES
            and prev is not None
            and prev.type == PlSqlLexer.SQL
        ):
            features.append(Feature("sql_cursor_attribute", token.line, token.text))
    return features


_ALTER_TYPE = re.compile(r"^\s*ALTER\s+TYPE\b", re.IGNORECASE | re.MULTILINE)

# The lookbehind keeps directive matching away from identifiers:
# EVENT$END is a legal Oracle name whose tail must not read as $END.
# A true directive is never preceded by an identifier character.
_CC_DIRECTIVE = re.compile(r"(?<![\w$#])\$(?:if|elsif|else|end|error)\b", re.IGNORECASE)
_CC_ERROR_BLOCK = re.compile(
    r"(?<![\w$#])\$error\b.*?(?<![\w$#])\$end\b", re.IGNORECASE | re.DOTALL
)
_CC_CONDITION = re.compile(
    r"(?<![\w$#])\$(?:if|elsif)\b.*?(?<![\w$#])\$then\b",
    re.IGNORECASE | re.DOTALL,
)
_CC_TOKEN = re.compile(r"(?<![\w$#])\$(?:else|end)\b", re.IGNORECASE)
_CC_INQUIRY = re.compile(r"(?<![\w$#])\$\$\w+")


def _blank(match: re.Match[str]) -> str:
    return "".join(ch if ch == "\n" else " " for ch in match.group(0))


def _strip_conditional_compilation(text: str) -> tuple[str, int | None]:
    """Blank $IF directives in place, keeping every branch's code.

    Selection directives pick code at compile time by version or flag.
    For assessment every branch matters, so the directives and their
    conditions become whitespace - line numbers survive - and all
    branch bodies stay visible to the walk. Inquiry references such as
    $$plsql_unit become NULL, which parses as an expression wherever
    they legally appear. Returns the line of the first directive, or
    None when the unit uses no conditional compilation.
    """
    directive = _CC_DIRECTIVE.search(text)
    inquiry = _CC_INQUIRY.search(text)
    if directive is None and inquiry is None:
        return text, None
    first = min(m.start() for m in (directive, inquiry) if m is not None)
    line = text.count("\n", 0, first) + 1
    text = _CC_ERROR_BLOCK.sub(_blank, text)
    text = _CC_CONDITION.sub(_blank, text)
    text = _CC_TOKEN.sub(_blank, text)
    text = _CC_INQUIRY.sub("NULL", text)
    return text, line


_TYPE_KINDS = {"TYPE", "TYPE BODY"}
_DEFAULT_KW = re.compile(r"\bdefault\b", re.IGNORECASE)
_OID_CLAUSE = re.compile(r"\bOID\s+'[0-9A-Fa-f]+'", re.IGNORECASE)


def _blank_parameter_defaults(text: str) -> str:
    """Blank DEFAULT clauses in object-type method parameter lists.

    The vendored grammar predates DEFAULT values on type method
    parameters, which are legal Oracle. Each DEFAULT expression is
    blanked from the keyword to the comma or closing parenthesis that
    ends it, quote- and depth-aware, so the parameter list itself
    survives and line numbers do not move.
    """
    out = list(text)
    for kw in _DEFAULT_KW.finditer(text):
        i = kw.end()
        depth = 0
        in_string = False
        while i < len(text):
            ch = text[i]
            if in_string:
                if ch == "'":
                    in_string = False
            elif ch == "'":
                in_string = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    break
                depth -= 1
            elif ch == "," and depth == 0:
                break
            i += 1
        for j in range(kw.start(), i):
            if out[j] != "\n":
                out[j] = " "
    return "".join(out)


def analyze_source(text: str, unit_type: str | None = None) -> UnitAnalysis:
    """Parse one stored unit and extract its migration-relevant facts.

    A unit that fails to parse yields no features at all rather than
    features from a half-built tree; the rule engine falls back to
    token greps for those units.

    An evolved object type is the one known case where DBA_SOURCE
    holds more than one statement: the original CREATE followed by
    the ALTER TYPE statements that changed it. When a TYPE fails to
    parse whole, the text is split at the first ALTER TYPE line and
    the original definition parsed alone; the evolution itself is
    recorded as a feature, because it is a migration fact.

    Conditional compilation directives are blanked before parsing so
    every branch's code stays visible, and their presence is recorded
    as a feature - the port has to pick a branch. Object-type method
    parameters with DEFAULT values, legal Oracle the grammar predates,
    get a retry with the defaults blanked when the first parse fails.
    """
    text, cc_line = _strip_conditional_compilation(text)
    parse = parse_source(text)
    evolution_line: int | None = None
    if parse.errors and unit_type == "TYPE":
        match = _ALTER_TYPE.search(text)
        if match:
            retry = parse_source(text[: match.start()])
            if not retry.errors:
                parse = retry
                evolution_line = text.count("\n", 0, match.start()) + 1
                text = text[: match.start()]
    if parse.errors and unit_type in _TYPE_KINDS:
        # Two clauses the grammar predates, blanked together: DEFAULT
        # values on method parameters, and the OID identity clause the
        # sample schemas and replication-aware exports carry.
        cleaned = _OID_CLAUSE.sub(_blank, _blank_parameter_defaults(text))
        if cleaned != text:
            retry = parse_source(cleaned)
            if not retry.errors:
                parse = retry
    features: list[Feature] = []
    calls: list[Call] = []
    if parse.tree is not None and not parse.errors:
        listener = _FeatureListener()
        ParseTreeWalker.DEFAULT.walk(listener, parse.tree)
        features = listener.features + _scan_tokens(parse.tokens)
        if evolution_line is not None:
            features.append(Feature("type_evolution", evolution_line, None))
        if cc_line is not None:
            features.append(Feature("conditional_compilation", cc_line, None))
        features.sort(key=lambda f: (f.line, f.feature))
        calls = sorted(set(listener.calls), key=lambda c: (c.line, c.callee))
    return UnitAnalysis(parse.mode, parse.errors, tuple(features), tuple(calls))

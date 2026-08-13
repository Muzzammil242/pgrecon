"""Feature extraction from parsed PL/SQL units.

One analysis pass produces the deep facts the rule engine queries:
a listener walk over the parse tree for statement-level constructs,
and a scan of the default token channel for function-level ones.
Comments and string literals reach neither, which is the point of the
exercise: a SYSDATE in a comment is not a finding.
"""

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
class UnitAnalysis:
    mode: str
    errors: tuple[str, ...]
    features: tuple[Feature, ...]


class _FeatureListener(PlSqlParserListener):  # type: ignore[misc]
    def __init__(self) -> None:
        self.features: list[Feature] = []

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
            token.type in _CURSOR_ATTRIBUTES
            and prev is not None
            and prev.type == PlSqlLexer.SQL
        ):
            features.append(Feature("sql_cursor_attribute", token.line, token.text))
    return features


def analyze_source(text: str) -> UnitAnalysis:
    """Parse one stored unit and extract its migration-relevant facts.

    A unit that fails to parse yields no features at all rather than
    features from a half-built tree; the rule engine falls back to
    token greps for those units.
    """
    parse = parse_source(text)
    features: list[Feature] = []
    if parse.tree is not None and not parse.errors:
        listener = _FeatureListener()
        ParseTreeWalker.DEFAULT.walk(listener, parse.tree)
        features = listener.features + _scan_tokens(parse.tokens)
        features.sort(key=lambda f: (f.line, f.feature))
    return UnitAnalysis(parse.mode, parse.errors, tuple(features))

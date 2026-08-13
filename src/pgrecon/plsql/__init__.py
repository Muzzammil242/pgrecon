"""Deep PL/SQL parsing on top of the vendored grammars-v4 parser.

Parsing runs SLL prediction with a bail-out strategy first, which is
fast, and repeats in full LL mode only when SLL bails, which is rare
and correct. Errors from the LL pass are recorded, never raised: an
unparseable unit is assessment data. The first parse in a process pays
ANTLR's prediction-cache warmup (seconds); warm parses of typical
units take milliseconds.
"""

from dataclasses import dataclass
from typing import Any

from antlr4 import CommonTokenStream, InputStream
from antlr4.atn.PredictionMode import PredictionMode
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.Errors import ParseCancellationException
from antlr4.error.ErrorStrategy import BailErrorStrategy

from pgrecon.plsql._generated.PlSqlLexer import PlSqlLexer
from pgrecon.plsql._generated.PlSqlParser import PlSqlParser


@dataclass(frozen=True)
class PlSqlParse:
    tree: Any | None
    mode: str
    errors: tuple[str, ...]
    tokens: Any | None = None


class _Collector(ErrorListener):  # type: ignore[misc]
    def __init__(self) -> None:
        self.errors: list[str] = []

    def syntaxError(
        self, recognizer: Any, sym: Any, line: int, col: int, msg: str, e: Any
    ) -> None:
        self.errors.append(f"line {line}:{col} {msg}")


def _parser_for(text: str) -> tuple[PlSqlParser, CommonTokenStream]:
    lexer = PlSqlLexer(InputStream(text))
    lexer.removeErrorListeners()
    stream = CommonTokenStream(lexer)
    return PlSqlParser(stream), stream


def parse_unit(text: str) -> PlSqlParse:
    """Parse one complete SQL or PL/SQL statement."""
    parser, stream = _parser_for(text)
    parser.removeErrorListeners()
    parser._interp.predictionMode = PredictionMode.SLL
    parser._errHandler = BailErrorStrategy()
    try:
        return PlSqlParse(parser.sql_script(), "sll", (), stream)
    except ParseCancellationException:
        pass

    parser, stream = _parser_for(text)
    parser.removeErrorListeners()
    collector = _Collector()
    parser.addErrorListener(collector)
    tree = parser.sql_script()
    return PlSqlParse(tree, "ll", tuple(collector.errors), stream)


def parse_source(text: str) -> PlSqlParse:
    """Parse a stored unit as extracted from the source table.

    DBA_SOURCE holds the unit without its CREATE preamble, starting at
    the object type keyword, exactly what SQL*Plus spooled.
    """
    return parse_unit("CREATE OR REPLACE " + text)

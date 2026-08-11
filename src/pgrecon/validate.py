"""Syntax checking against PostgreSQL's own grammar.

pglast wraps libpg_query, the real PostgreSQL parser, so acceptance here
means acceptance by the server. Anything the tool presents as PostgreSQL
SQL must pass through this check before it reaches a report.
"""

from pglast import parse_sql
from pglast.parser import ParseError


def pg_syntax_error(sql: str) -> str | None:
    """Return the parser's error message, or None if PostgreSQL accepts sql."""
    try:
        parse_sql(sql)
    except ParseError as exc:
        return str(exc)
    return None

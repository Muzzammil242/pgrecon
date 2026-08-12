"""Rules over PL/SQL source and trigger structure.

Source detectors are token level: honest for an assessment and exactly
what the spec allows until the ANTLR deep-parse pass lands. Matching is
done per line against all_source text, deduplicated per object.
"""

from pgrecon.rules import Rule, Severity, sql_detector


def _source_grep(pattern: str, label: str) -> str:
    # One finding per object that matches anywhere in its source, with
    # the first matching line number as the detail.
    return (
        "SELECT owner, name, type,"
        f" '{label} (first at line ' || MIN(line) || ')' AS detail"
        " FROM source WHERE UPPER(text) LIKE UPPER('%" + pattern + "%')"
        " GROUP BY owner, name, type"
    )


RULES = [
    Rule(
        id="R-TRG-01",
        title="Compound trigger",
        category="triggers",
        severity=Severity.HIGH,
        effort=4.0,
        remedy=(
            "PostgreSQL has no compound triggers. Split the timing sections"
            " into separate trigger functions and move statement-level"
            " state into a transition table or a session variable."
        ),
        detector=sql_detector(
            "SELECT owner, trigger_name, 'TRIGGER', 'on ' || table_name"
            " FROM triggers WHERE trigger_type = 'COMPOUND'"
        ),
    ),
    Rule(
        id="R-TRG-02",
        title="Autonomous transaction",
        category="plsql",
        severity=Severity.HIGH,
        effort=4.0,
        remedy=(
            "PostgreSQL functions cannot commit independently of their"
            " caller. Rework audit-style autonomous transactions with a"
            " dblink loopback, a message table drained by a worker, or"
            " pg_background."
        ),
        detector=sql_detector(
            _source_grep("AUTONOMOUS_TRANSACTION", "PRAGMA AUTONOMOUS_TRANSACTION")
        ),
    ),
    Rule(
        id="R-SRC-01",
        title="Dynamic SQL",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "EXECUTE IMMEDIATE maps to PL/pgSQL EXECUTE, but bind syntax"
            " and error handling differ. Each dynamic statement needs a"
            " manual port and a test."
        ),
        detector=sql_detector(_source_grep("EXECUTE IMMEDIATE", "EXECUTE IMMEDIATE")),
    ),
    Rule(
        id="R-SRC-02",
        title="GOTO statement",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "PL/pgSQL has no GOTO. The control flow must be restructured"
            " with loops, exceptions, or early returns."
        ),
        detector=sql_detector(_source_grep("GOTO ", "GOTO")),
    ),
    Rule(
        id="R-SRC-03",
        title="BULK COLLECT",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "PL/pgSQL has no BULK COLLECT; array_agg into an array or a"
            " plain set-based statement usually replaces the whole loop."
        ),
        detector=sql_detector(_source_grep("BULK COLLECT", "BULK COLLECT")),
    ),
    Rule(
        id="R-SRC-04",
        title="CONNECT BY hierarchical query",
        category="sql",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "Rewrite as a recursive CTE (WITH RECURSIVE). LEVEL,"
            " SYS_CONNECT_BY_PATH, and ORDER SIBLINGS BY all need manual"
            " equivalents."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + _source_grep("CONNECT BY", "CONNECT BY")
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'CONNECT BY in view definition' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND UPPER(ddl) LIKE '%CONNECT BY%')"
        ),
    ),
    Rule(
        id="R-SRC-05",
        title="Old-style outer join (+)",
        category="sql",
        severity=Severity.LOW,
        effort=0.5,
        remedy=(
            "The (+) operator does not exist in PostgreSQL. Rewrite as"
            " ANSI LEFT or RIGHT JOIN; semantics match except for a few"
            " multi-condition corner cases worth testing."
        ),
        detector=sql_detector(
            "SELECT owner, name, 'VIEW DDL', 'uses (+) outer join'"
            " FROM ddl WHERE type = 'VIEW' AND ddl LIKE '%(+)%'"
        ),
    ),
]

"""Rules over Oracle SQL constructs found in code and view definitions.

Constructs in stored code come from the deep-parse facts with a grep
fallback; view bodies are text in the ddl table and stay grep-based
until views get their own parse.
"""

from pgrecon.rules import Rule, Severity, feature_grep, sql_detector

RULES = [
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
            + feature_grep(
                ("connect_by",), "UPPER(s.text) LIKE '%CONNECT BY%'", "CONNECT BY"
            )
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
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(
                ("outer_join_plus",), "s.text LIKE '%(+)%'", "(+) outer join"
            )
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'uses (+) outer join' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND ddl LIKE '%(+)%')"
        ),
    ),
    Rule(
        id="R-SRC-08",
        title="ROWNUM",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "Replace with LIMIT and OFFSET or row_number() over an"
            " explicit ORDER BY. ROWNUM is assigned before sorting, so"
            " every ROWNUM-with-ORDER-BY query deserves a correctness"
            " check, not just a rewrite."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(("rownum",), "UPPER(s.text) LIKE '%ROWNUM%'", "ROWNUM")
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL', 'ROWNUM in view definition'"
            " AS detail FROM ddl"
            " WHERE type = 'VIEW' AND UPPER(ddl) LIKE '%ROWNUM%')"
        ),
    ),
    Rule(
        id="R-SRC-09",
        title="MERGE statement",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "PostgreSQL 15 added MERGE, but without Oracle's DELETE"
            " clause inside WHEN MATCHED conditions and with different"
            " concurrency behavior; on older targets use INSERT ON"
            " CONFLICT. Each MERGE needs a per-statement decision."
        ),
        detector=sql_detector(
            feature_grep(
                ("merge",),
                "UPPER(s.text) LIKE '%MERGE INTO%'",
                "MERGE INTO",
            )
        ),
    ),
    Rule(
        id="R-SRC-10",
        title="DECODE",
        category="sql",
        severity=Severity.LOW,
        effort=0.3,
        remedy=(
            "Rewrite as CASE. One trap: DECODE treats two NULLs as equal,"
            " CASE does not, so any DECODE branching on NULL changes"
            " behavior silently."
        ),
        detector=sql_detector(
            feature_grep(("decode_call",), "UPPER(s.text) LIKE '%DECODE(%'", "DECODE")
        ),
    ),
    Rule(
        id="R-SRC-11",
        title="SYSDATE",
        category="sql",
        severity=Severity.LOW,
        effort=0.3,
        remedy=(
            "SYSDATE is evaluated at call time; now() is fixed at"
            " transaction start. Map to statement_timestamp() or"
            " clock_timestamp() where the difference matters, for example"
            " inside long transactions and loops."
        ),
        detector=sql_detector(
            feature_grep(("sysdate",), "UPPER(s.text) LIKE '%SYSDATE%'", "SYSDATE")
        ),
    ),
]

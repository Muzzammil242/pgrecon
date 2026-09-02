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
        extension="orafce",
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
    Rule(
        id="R-SRC-22",
        title="MODEL clause",
        category="sql",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "The MODEL clause is a spreadsheet engine inside SELECT;"
            " PostgreSQL has nothing comparable. Rewrite as recursive"
            " CTEs, window functions, or application logic - each MODEL"
            " query is a redesign, not a translation."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(
                ("model_clause",),
                "UPPER(s.text) LIKE '%DIMENSION BY%'",
                "MODEL clause",
            )
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'MODEL clause in view definition' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND UPPER(ddl) LIKE '%DIMENSION BY%')"
        ),
    ),
    Rule(
        id="R-SRC-23",
        title="PIVOT or UNPIVOT",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "PostgreSQL has no PIVOT clause. Rewrite as conditional"
            " aggregation with FILTER, or crosstab() from the tablefunc"
            " extension; UNPIVOT becomes a LATERAL VALUES join. Column"
            " lists that Oracle derived automatically must be spelled"
            " out."
        ),
        extension="tablefunc",
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(
                ("pivot_clause",),
                "UPPER(s.text) LIKE '%PIVOT (%' OR UPPER(s.text) LIKE '%PIVOT(%'",
                "PIVOT",
            )
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'PIVOT in view definition' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND (UPPER(ddl) LIKE '%PIVOT (%'"
            " OR UPPER(ddl) LIKE '%PIVOT(%'))"
        ),
    ),
    Rule(
        id="R-SRC-24",
        title="Flashback query",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "AS OF TIMESTAMP and AS OF SCN read the past from undo;"
            " PostgreSQL keeps no such history. Move the requirement to"
            " audit tables, temporal tables maintained by triggers, or"
            " point-in-time recovery clones for investigations."
        ),
        detector=sql_detector(
            feature_grep(
                ("flashback_query",),
                "UPPER(s.text) LIKE '%AS OF TIMESTAMP%'"
                " OR UPPER(s.text) LIKE '%AS OF SCN%'",
                "flashback query",
            )
        ),
    ),
    Rule(
        id="R-SRC-25",
        title="Multi-table INSERT",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "INSERT ALL and INSERT FIRST fan one row source into"
            " several tables; PostgreSQL takes one target per INSERT."
            " Rewrite as a data-modifying CTE (WITH src AS (...)"
            " INSERT ... SELECT per target) - INSERT FIRST needs its"
            " conditions made mutually exclusive by hand."
        ),
        detector=sql_detector(
            feature_grep(
                ("insert_multi",),
                "UPPER(s.text) LIKE '%INSERT ALL%'"
                " OR UPPER(s.text) LIKE '%INSERT FIRST%'",
                "multi-table INSERT",
            )
        ),
    ),
    Rule(
        id="R-SRC-26",
        title="WITH FUNCTION in a query",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "PL/SQL declared inline in a WITH clause has no PostgreSQL"
            " form. Hoist the function into a schema-level CREATE"
            " FUNCTION and reference it normally; the inline form often"
            " exists to dodge a grant, so check who may execute it."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(
                ("with_function",),
                "UPPER(s.text) LIKE '%WITH FUNCTION%'"
                " OR UPPER(s.text) LIKE '%WITH PROCEDURE%'",
                "WITH FUNCTION",
            )
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'WITH FUNCTION in view definition' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND (UPPER(ddl) LIKE '%WITH FUNCTION%'"
            " OR UPPER(ddl) LIKE '%WITH PROCEDURE%'))"
        ),
    ),
    Rule(
        id="R-SRC-27",
        title="SQL macro",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "SQL_MACRO functions splice text into the calling query at"
            " parse time; PostgreSQL has no macro expansion. Table"
            " macros usually become views or set-returning functions,"
            " scalar macros become plain functions - performance"
            " characteristics change either way."
        ),
        detector=sql_detector(
            feature_grep(
                ("sql_macro",),
                "UPPER(s.text) LIKE '%SQL_MACRO%'",
                "SQL macro",
            )
        ),
    ),
    Rule(
        id="R-SRC-28",
        title="Session context read",
        category="sql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "SYS_CONTEXT and USERENV read Oracle's session context."
            " current_user, inet_client_addr(), and current_setting()"
            " over custom parameters cover the common attributes;"
            " SESSIONID, CLIENT_IDENTIFIER, and application contexts set"
            " by DBMS_SESSION need each attribute mapped by hand."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            + feature_grep(
                ("sys_context",),
                "UPPER(s.text) LIKE '%SYS_CONTEXT(%'"
                " OR UPPER(s.text) LIKE '%USERENV(%'",
                "SYS_CONTEXT",
            )
            + " UNION ALL"
            " SELECT owner, name, 'VIEW DDL', 'SYS_CONTEXT in view definition'"
            " AS detail FROM ddl WHERE type = 'VIEW'"
            " AND (UPPER(ddl) LIKE '%SYS_CONTEXT(%' OR UPPER(ddl) LIKE '%USERENV(%'))"
        ),
    ),
]

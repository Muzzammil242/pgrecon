"""Rules over constructs that exist to steer the Oracle optimizer.

A schema tuned by hand for Oracle's planner does not carry that tuning
across: PostgreSQL plans the same statements from scratch. These rules
mark where the tuning lives so the plan work is scoped, not discovered
in production.
"""

from pgrecon.rules import Rule, Severity, sql_detector

RULES = [
    Rule(
        id="R-PERF-01",
        title="Optimizer hint",
        category="performance",
        severity=Severity.LOW,
        effort=0.5,
        extension="pg_hint_plan",
        remedy=(
            "PostgreSQL ignores optimizer hints; pg_hint_plan can pin"
            " plans but is a last resort. A hinted statement was tuned by"
            " hand against Oracle's planner, so budget a fresh look at its"
            " plan and indexes on PostgreSQL instead of a plain rewrite."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, detail FROM ("
            "SELECT owner, name, type,"
            " 'optimizer hint (first at line ' || MIN(line) || ')' AS detail"
            " FROM source WHERE text LIKE '%/*+%' OR text LIKE '%--+%'"
            " GROUP BY owner, name, type"
            " UNION ALL"
            " SELECT owner, name, 'VIEW DDL',"
            " 'optimizer hint in view definition' AS detail FROM ddl"
            " WHERE type = 'VIEW' AND ddl LIKE '%/*+%')"
        ),
    ),
]

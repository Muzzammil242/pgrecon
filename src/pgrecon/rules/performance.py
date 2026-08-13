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
    Rule(
        id="R-PERF-02",
        title="Global index on a partitioned table",
        category="performance",
        severity=Severity.HIGH,
        effort=2.0,
        remedy=(
            "PostgreSQL indexes on partitioned tables are always local:"
            " there is no global index, and a unique key must contain the"
            " partition key. Global-index lookups become per-partition"
            " probes, and unique constraints that cannot include the key"
            " force a design decision, not a translation."
        ),
        detector=sql_detector(
            "SELECT owner, index_name, 'INDEX',"
            " 'GLOBAL partitioned index on ' || table_name"
            " FROM part_indexes WHERE locality = 'GLOBAL'"
            " UNION ALL"
            " SELECT i.owner, i.index_name, 'INDEX',"
            " 'non-partitioned index on partitioned ' || i.table_name"
            " FROM indexes i"
            " JOIN part_tables p"
            " ON p.owner = i.owner AND p.table_name = i.table_name"
            " WHERE i.generated <> 'Y'"
            " AND i.index_name NOT LIKE 'I_SNAP$%'"
            " AND NOT EXISTS (SELECT 1 FROM part_indexes pi"
            " WHERE pi.owner = i.owner AND pi.index_name = i.index_name)"
        ),
    ),
    Rule(
        id="R-PERF-03",
        title="Parallel degree set on object",
        category="performance",
        severity=Severity.LOW,
        effort=0.5,
        remedy=(
            "PostgreSQL has no per-object parallel degree; the planner"
            " decides within max_parallel_workers_per_gather. Workloads"
            " that relied on forced parallel scans need a plan review and"
            " possibly session-level parallel settings."
        ),
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE', 'DEGREE ' || TRIM(degree)"
            " FROM tables WHERE TRIM(degree) NOT IN ('0', '1')"
            " AND degree IS NOT NULL"
            " UNION ALL"
            " SELECT owner, index_name, 'INDEX', 'DEGREE ' || TRIM(degree)"
            " FROM indexes WHERE TRIM(degree) NOT IN ('0', '1')"
            " AND degree IS NOT NULL"
        ),
    ),
    Rule(
        id="R-PERF-04",
        title="SQL plan management in use",
        category="performance",
        severity=Severity.MEDIUM,
        effort=2.0,
        extension="pg_hint_plan",
        remedy=(
            "Plan baselines and stored outlines pin execution plans;"
            " PostgreSQL has no plan-stability feature. The workflow that"
            " guaranteed plans never regress disappears: replace it with"
            " monitoring via pg_stat_statements, and pg_hint_plan only"
            " where a plan must be forced."
        ),
        detector=sql_detector(
            "SELECT '', kind, 'PLAN MANAGEMENT',"
            " COUNT(*) || ' pinned plan(s), e.g. ' || MIN(name)"
            " FROM plan_management GROUP BY kind"
        ),
    ),
    Rule(
        id="R-PERF-05",
        title="Query-rewrite materialized view",
        category="performance",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "Oracle rewrites matching queries to hit the materialized"
            " view transparently; PostgreSQL never does. Queries that"
            " benefited must reference the view explicitly, which means"
            " finding them in the application first."
        ),
        detector=sql_detector(
            "SELECT owner, mview_name, 'MATERIALIZED VIEW',"
            " 'REWRITE enabled, refresh ' || COALESCE(refresh_method, '?')"
            " FROM mviews WHERE rewrite_enabled = 'Y'"
        ),
    ),
]

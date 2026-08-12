"""Rules over tables, partitioning, indexes, and statistics."""

from pgrecon.rules import Rule, Severity, sql_detector

RULES = [
    Rule(
        id="R-PART-01",
        title="Interval partitioning",
        category="partitioning",
        severity=Severity.HIGH,
        effort=6.0,
        remedy=(
            "PostgreSQL has no partitioning scheme that creates partitions"
            " on data arrival. Plan pg_partman or scheduled partition"
            " creation, and decide the retention window explicitly."
        ),
        extension="pg_partman",
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE', 'INTERVAL ' || interval"
            " FROM part_tables WHERE interval IS NOT NULL"
        ),
    ),
    Rule(
        id="R-PART-02",
        title="Partitioned table",
        category="partitioning",
        severity=Severity.LOW,
        effort=1.0,
        remedy=(
            "Declarative partitioning covers RANGE, LIST, and HASH, but"
            " global indexes and reference partitioning do not exist."
            " Each partitioned table needs its scheme mapped explicitly."
        ),
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE', partitioning_type"
            " || CASE WHEN subpartitioning_type IS NOT NULL"
            "         AND subpartitioning_type <> 'NONE'"
            "    THEN '/' || subpartitioning_type ELSE '' END"
            " FROM part_tables WHERE interval IS NULL"
        ),
    ),
    Rule(
        id="R-TAB-01",
        title="Global temporary table",
        category="tables",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "PostgreSQL temporary tables are per session and vanish with"
            " it; there is no shared definition with private rows. Rework"
            " to on-the-fly temp tables or use the pgtt extension."
        ),
        extension="pgtt",
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE', 'GLOBAL TEMPORARY'"
            " FROM tables WHERE temporary = 'Y'"
        ),
    ),
    Rule(
        id="R-TAB-02",
        title="Index-organized table",
        category="tables",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "PostgreSQL stores all tables as heaps. A plain table with a"
            " primary key covers correctness; if the access pattern relied"
            " on IOT clustering, consider CLUSTER or a covering index."
        ),
        detector=sql_detector(
            "SELECT feature, detail, 'FEATURE', count || ' index-organized'"
            " || ' table(s)' FROM features"
            " WHERE feature = 'iot_tables' AND count > 0"
        ),
    ),
    Rule(
        id="R-TAB-03",
        title="External table",
        category="tables",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "Map to file_fdw for flat files, or move the load into the"
            " application or COPY jobs. Driver options and error handling"
            " do not carry over."
        ),
        extension="file_fdw",
        detector=sql_detector(
            "SELECT feature, detail, 'FEATURE', count || ' external table(s)'"
            " FROM features WHERE feature = 'external_tables' AND count > 0"
        ),
    ),
    Rule(
        id="R-IDX-01",
        title="Bitmap index",
        category="indexes",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "PostgreSQL has no persistent bitmap indexes; the planner"
            " builds bitmaps at run time from b-tree indexes. Usually a"
            " plain b-tree suffices; re-test the queries that relied on it."
        ),
        detector=sql_detector(
            "SELECT owner, index_name, 'INDEX', 'BITMAP on ' || table_name"
            " FROM indexes WHERE index_type LIKE 'BITMAP%'"
        ),
    ),
    Rule(
        id="R-IDX-02",
        title="Function-based index",
        category="indexes",
        severity=Severity.INFO,
        effort=0.3,
        remedy=(
            "PostgreSQL supports expression indexes directly. Port the"
            " expression and confirm the function is immutable on the"
            " PostgreSQL side."
        ),
        detector=sql_detector(
            "SELECT i.owner, i.index_name, 'INDEX',"
            " COALESCE(e.expression, 'expression not extracted')"
            " FROM indexes i LEFT JOIN index_expressions e"
            " ON e.owner = i.owner AND e.index_name = i.index_name"
            " WHERE i.index_type LIKE 'FUNCTION-BASED%'"
            " AND i.generated <> 'Y'"
            " AND i.index_name NOT LIKE 'I_SNAP$%'"
        ),
    ),
    Rule(
        id="R-IDX-03",
        title="Domain index",
        category="indexes",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "Domain indexes are usually Oracle Text. Full-text search maps"
            " to tsvector with a GIN index, or pg_trgm for fuzzy matching;"
            " query syntax and ranking both change."
        ),
        extension="pg_trgm",
        detector=sql_detector(
            "SELECT owner, index_name, 'INDEX', 'DOMAIN on ' || table_name"
            " FROM indexes WHERE index_type = 'DOMAIN'"
        ),
    ),
    Rule(
        id="R-STAT-01",
        title="Table without optimizer statistics",
        category="statistics",
        severity=Severity.INFO,
        effort=0.0,
        remedy=(
            "num_rows is null, so data-volume estimates for this table are"
            " unreliable. Gather statistics before trusting sizing numbers."
        ),
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE', 'no statistics gathered'"
            " FROM tables WHERE num_rows IS NULL"
        ),
    ),
]

"""Rules over schema-level objects and extraction quality."""

from pgrecon.rules import Rule, Severity, feature_grep, sql_detector

RULES = [
    Rule(
        id="R-OBJ-01",
        title="Database link",
        category="objects",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "Cross-database access needs postgres_fdw or oracle_fdw on the"
            " PostgreSQL side, plus credential management. Every statement"
            " using the link must be found and repointed."
        ),
        extension="postgres_fdw",
        detector=sql_detector(
            "SELECT owner, db_link, 'DATABASE LINK',"
            " 'to ' || COALESCE(host, '?') || ' as ' || COALESCE(username, '?')"
            " FROM db_links"
            " UNION ALL"
            " SELECT owner, synonym_name, 'SYNONYM', 'points over ' || db_link"
            " FROM synonyms WHERE db_link IS NOT NULL AND db_link <> ''"
        ),
    ),
    Rule(
        id="R-OBJ-02",
        title="Scheduler or legacy job",
        category="objects",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "DBMS_SCHEDULER and DBMS_JOB have no engine equivalent in"
            " PostgreSQL. Recreate schedules in pg_cron and port each job"
            " action; calendar syntax must be translated by hand."
        ),
        extension="pg_cron",
        detector=sql_detector(
            "SELECT owner, name, type, 'scheduler job' FROM objects"
            " WHERE type = 'JOB'"
            " UNION ALL"
            " SELECT feature, detail, 'FEATURE', count || ' dbms_job(s)'"
            " FROM features WHERE feature = 'legacy_jobs' AND count > 0"
        ),
    ),
    Rule(
        id="R-OBJ-03",
        title="Materialized view",
        category="objects",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "PostgreSQL materialized views refresh only in full and have"
            " no refresh-on-commit. Fast-refresh views need a trigger-based"
            " design or a scheduled REFRESH with the staleness accepted."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'materialized view' FROM objects"
            " WHERE type = 'MATERIALIZED VIEW'"
        ),
    ),
    Rule(
        id="R-OBJ-04",
        title="Advanced Queuing",
        category="objects",
        severity=Severity.HIGH,
        effort=6.0,
        remedy=(
            "AQ has no PostgreSQL counterpart. Depending on usage, replace"
            " with LISTEN/NOTIFY, a queue table with SKIP LOCKED consumers,"
            " or an external broker; every enqueue and dequeue call site"
            " changes."
        ),
        detector=sql_detector(
            "SELECT feature, detail, 'FEATURE', count || ' queue(s)'"
            " FROM features WHERE feature = 'queues' AND count > 0"
        ),
    ),
    Rule(
        id="R-OBJ-05",
        title="User-defined object type",
        category="objects",
        severity=Severity.MEDIUM,
        effort=2.5,
        remedy=(
            "Composite types carry the attributes, but member functions"
            " do not exist in PostgreSQL: each method becomes a standalone"
            " function taking the composite as its first argument, and"
            " every call site changes."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'object type' FROM objects WHERE type = 'TYPE'"
        ),
    ),
    Rule(
        id="R-OBJ-06",
        title="Synonym",
        category="objects",
        severity=Severity.LOW,
        effort=0.3,
        remedy=(
            "PostgreSQL has no synonyms. Same-database synonyms usually"
            " dissolve into search_path; cross-schema renames become views"
            " or schema qualification at the call sites."
        ),
        detector=sql_detector(
            "SELECT owner, synonym_name, 'SYNONYM',"
            " 'for ' || COALESCE(table_owner || '.', '') || table_name"
            " FROM synonyms WHERE db_link IS NULL OR db_link = ''"
        ),
    ),
    Rule(
        id="R-OBJ-07",
        title="Virtual Private Database policy",
        category="objects",
        severity=Severity.HIGH,
        effort=4.0,
        remedy=(
            "VPD policies rewrite queries through a policy function."
            " PostgreSQL row-level security expresses most of them as"
            " declarative policies, but each policy function must be"
            " translated by hand and its session context re-plumbed."
        ),
        detector=sql_detector(
            "SELECT feature, detail, 'FEATURE', count || ' VPD policy(ies)'"
            " FROM features WHERE feature = 'vpd_policies' AND count > 0"
        ),
    ),
    Rule(
        id="R-OBJ-08",
        title="Invalid object",
        category="objects",
        severity=Severity.INFO,
        effort=0.0,
        remedy=(
            "Already broken before any migration. Decide per object:"
            " fix it, or exclude it from scope in writing so the estimate"
            " does not pay for dead code."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'status ' || status FROM objects"
            " WHERE status IS NOT NULL AND status <> 'VALID'"
        ),
    ),
    Rule(
        id="R-OBJ-09",
        title="Evolved object type",
        category="objects",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "This type was changed in place with ALTER TYPE, which"
            " PostgreSQL composite types cannot do once data depends on"
            " them. Migrate the final shape, then decide how future"
            " attribute additions will land: added columns, a jsonb"
            " escape hatch, or a rebuild procedure."
        ),
        detector=sql_detector(
            feature_grep(
                ("type_evolution",),
                "s.type = 'TYPE' AND UPPER(s.text) LIKE 'ALTER TYPE%'",
                "evolved with ALTER TYPE",
            )
        ),
    ),
    Rule(
        id="R-VIEW-01",
        title="FORCE view",
        category="objects",
        severity=Severity.LOW,
        effort=0.3,
        remedy=(
            "PostgreSQL cannot create a view whose dependencies are"
            " missing. FORCE views usually signal broken dependencies or"
            " circular creation order; both need resolving before the"
            " schema replays."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'created with FORCE' FROM ddl"
            " WHERE type = 'VIEW' AND UPPER(ddl) LIKE '%FORCE%VIEW%'"
        ),
    ),
    Rule(
        id="R-DDL-01",
        title="DDL the parser could not read",
        category="extraction",
        severity=Severity.INFO,
        effort=0.5,
        remedy=(
            "The statement is preserved verbatim in the inventory but did"
            " not parse with the Oracle grammar, which usually means exotic"
            " syntax worth a manual look."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, COALESCE(SUBSTR(parse_error, 1, 80),"
            " 'parse failed') FROM ddl WHERE parse_ok = 0"
        ),
    ),
    Rule(
        id="R-OBJ-10",
        title="Materialized view log",
        category="objects",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "MLOG$ tables are the change capture behind FAST refresh;"
            " PostgreSQL refreshes materialized views only in full"
            " (CONCURRENTLY at best). Drop the logs, schedule REFRESH,"
            " and if true incremental maintenance is required, plan"
            " trigger-maintained summary tables instead."
        ),
        detector=sql_detector(
            "SELECT owner, table_name, 'TABLE',"
            " 'materialized view log container' FROM tables"
            " WHERE table_name LIKE 'MLOG$%' OR table_name LIKE 'RUPD$%'"
        ),
    ),
    Rule(
        id="R-DDL-02",
        title="DDL parsed only as an opaque command",
        category="extraction",
        severity=Severity.INFO,
        effort=0.3,
        remedy=(
            "The Oracle grammar accepted the statement without building a"
            " real syntax tree, which usually marks exotic constructs the"
            " deep-parse pass should revisit."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'opaque parse' FROM ddl"
            " WHERE parse_quality = 'fallback'"
        ),
    ),
    Rule(
        id="R-OBJ-11",
        title="Remote call over a database link",
        category="objects",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "A call through @link runs code on another database, which"
            " postgres_fdw cannot do - it reaches remote tables, not"
            " remote procedures. Move the logic to the caller's side, to"
            " the application, or to a queue between the databases."
        ),
        extension="postgres_fdw",
        detector=sql_detector(
            "SELECT owner, name, type,"
            " callee || ' (line ' || line || ')' FROM plsql_calls"
            " WHERE callee LIKE '%@%'"
        ),
    ),
]

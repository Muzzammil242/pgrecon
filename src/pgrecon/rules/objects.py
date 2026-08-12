"""Rules over schema-level objects and extraction quality."""

from pgrecon.rules import Rule, Severity, sql_detector

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
            "SELECT feature, detail, 'FEATURE', count || ' database link(s)'"
            " FROM features WHERE feature = 'db_links' AND count > 0"
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
]

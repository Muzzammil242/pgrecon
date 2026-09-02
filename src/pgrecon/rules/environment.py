"""Rules over the database environment: character set and grants."""

from pgrecon.rules import Rule, Severity, sql_detector

RULES = [
    Rule(
        id="R-ENV-01",
        title="Database character set needs an encoding decision",
        category="environment",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "Map the Oracle character set to a PostgreSQL encoding before"
            " creating the target database: AL32UTF8 and UTF8 become UTF8,"
            " WE8MSWIN1252 becomes WIN1252, WE8ISO8859P1 becomes LATIN1."
            " Anything else needs a conversion test on real data, and"
            " NCHAR columns collapse into the single database encoding."
        ),
        detector=sql_detector(
            "SELECT 'DATABASE', value, 'CHARACTERSET', 'NLS_CHARACTERSET '"
            " || value FROM nls_params WHERE key = 'NLS_CHARACTERSET'"
            " AND value NOT IN ('AL32UTF8', 'UTF8')"
        ),
    ),
    Rule(
        id="R-ENV-02",
        title="Object grants to migrate",
        category="environment",
        severity=Severity.LOW,
        effort=0.5,
        remedy=(
            "The converter emits role bootstraps and GRANT statements for"
            " privileges with a direct counterpart; EXECUTE grants and"
            " Oracle-only privileges are residue lines. Review the role"
            " list against the real user model before applying."
        ),
        detector=sql_detector(
            "SELECT owner, grantee, 'GRANTEE', COUNT(*) || ' object grants'"
            " FROM grants GROUP BY owner, grantee"
        ),
    ),
]

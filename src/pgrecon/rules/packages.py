"""Rules over package structure: the state that PostgreSQL cannot hold.

These detectors are line-level and deliberately conservative: they look
at declarations between the package header and the first subprogram,
which is where package state lives. Precision improves when the ANTLR
pass lands; until then findings name the evidence they saw.
"""

from pgrecon.rules import Rule, Severity, sql_detector

_STATE_QUERY = """
WITH members AS (
    SELECT DISTINCT owner, name, type FROM source
     WHERE type IN ('PACKAGE', 'PACKAGE BODY')
),
first_sub AS (
    SELECT owner, name, type, MIN(line) AS first_line FROM source
     WHERE type IN ('PACKAGE', 'PACKAGE BODY')
       AND (UPPER(text) LIKE '%FUNCTION %' OR UPPER(text) LIKE '%PROCEDURE %')
     GROUP BY owner, name, type
)
SELECT s.owner, s.name, s.type,
       COUNT(*) || ' package-level declaration(s), first at line '
       || MIN(s.line) AS detail
  FROM source s
  JOIN members m
    ON m.owner = s.owner AND m.name = s.name AND m.type = s.type
  LEFT JOIN first_sub f
    ON f.owner = s.owner AND f.name = s.name AND f.type = s.type
 WHERE s.line > 1
   AND s.line < COALESCE(f.first_line, 1000000000)
   AND s.text LIKE '%;%'
   AND LTRIM(s.text) NOT LIKE '--%'
   AND (UPPER(s.text) LIKE '%NUMBER%'
        OR UPPER(s.text) LIKE '%VARCHAR2%'
        OR UPPER(s.text) LIKE '%PLS_INTEGER%'
        OR UPPER(s.text) LIKE '%BOOLEAN%'
        OR UPPER(s.text) LIKE '%CONSTANT%'
        OR UPPER(s.text) LIKE '% DATE%')
 GROUP BY s.owner, s.name, s.type
"""

_INIT_QUERY = """
WITH counts AS (
    SELECT owner, name,
           COUNT(CASE WHEN UPPER(LTRIM(text)) LIKE 'BEGIN%' THEN 1 END)
               AS begins,
           COUNT(CASE WHEN UPPER(text) LIKE '%FUNCTION %'
                        OR UPPER(text) LIKE '%PROCEDURE %' THEN 1 END)
               AS subs
      FROM source
     WHERE type = 'PACKAGE BODY' AND LTRIM(text) NOT LIKE '--%'
     GROUP BY owner, name
)
SELECT owner, name, 'PACKAGE BODY',
       'BEGIN blocks exceed subprograms by ' || (begins - subs)
       || ' (possible initialization block)' AS detail
  FROM counts WHERE subs > 0 AND begins > subs
"""

RULES = [
    Rule(
        id="R-PKG-01",
        title="Package-level state",
        category="packages",
        severity=Severity.HIGH,
        effort=5.0,
        remedy=(
            "PostgreSQL has no package variables. Scalars map to session"
            " settings via set_config and current_setting (text only);"
            " composites and collections need per-session temporary"
            " tables. Every reader and writer of the state changes."
        ),
        detector=sql_detector(_STATE_QUERY),
    ),
    Rule(
        id="R-PKG-02",
        title="Package initialization block",
        category="packages",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "Oracle runs the block once per session on first reference,"
            " which PostgreSQL cannot replicate. Extract it into an init"
            " function guarded by a session flag and call it lazily from"
            " each entry point. Detection is heuristic; confirm by eye."
        ),
        detector=sql_detector(_INIT_QUERY),
    ),
]

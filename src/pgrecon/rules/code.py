"""Rules over PL/SQL source and trigger structure.

Source detectors read the deep-parse facts first and fall back to
token-level greps for units the parser rejected, so precision comes
from the tree and coverage never drops below what greps gave.
"""

from pgrecon.rules import Rule, Severity, feature_grep, sql_detector

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
            feature_grep(
                ("autonomous_transaction",),
                "UPPER(s.text) LIKE '%AUTONOMOUS_TRANSACTION%'",
                "PRAGMA AUTONOMOUS_TRANSACTION",
            )
        ),
    ),
    Rule(
        id="R-TRG-03",
        title="Sequence-assigned key via trigger",
        category="triggers",
        severity=Severity.MEDIUM,
        effort=0.5,
        remedy=(
            "The pre-12c idiom of filling a key from a sequence in a"
            " BEFORE INSERT trigger becomes a plain identity column or a"
            " DEFAULT nextval() in PostgreSQL; the trigger disappears."
        ),
        detector=sql_detector(
            "SELECT owner, name, type,"
            " 'NEXTVAL in trigger (first at line ' || MIN(line) || ')'"
            " AS detail FROM source"
            " WHERE type = 'TRIGGER' AND UPPER(text) LIKE '%NEXTVAL%'"
            " GROUP BY owner, name, type"
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
        detector=sql_detector(
            feature_grep(
                ("execute_immediate",),
                "UPPER(s.text) LIKE '%EXECUTE IMMEDIATE%'",
                "EXECUTE IMMEDIATE",
            )
        ),
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
        detector=sql_detector(
            feature_grep(("goto",), "UPPER(s.text) LIKE '%GOTO %'", "GOTO")
        ),
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
        detector=sql_detector(
            feature_grep(
                ("bulk_collect",),
                "UPPER(s.text) LIKE '%BULK COLLECT%'",
                "BULK COLLECT",
            )
        ),
    ),
    Rule(
        id="R-SRC-06",
        title="REF CURSOR",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "PostgreSQL refcursor exists but behaves differently: it is"
            " bound to the transaction and callers fetch with FETCH, not"
            " a client result set. Interfaces returning SYS_REFCURSOR to"
            " applications usually become set-returning functions."
        ),
        detector=sql_detector(
            feature_grep(
                ("ref_cursor",),
                "UPPER(s.text) LIKE '%REF CURSOR%'"
                " OR UPPER(s.text) LIKE '%SYS_REFCURSOR%'",
                "REF CURSOR",
            )
        ),
    ),
    Rule(
        id="R-SRC-07",
        title="Swallowed exception",
        category="plsql",
        severity=Severity.INFO,
        effort=0.2,
        remedy=(
            "WHEN OTHERS THEN NULL hides every failure including the ones"
            " a migration introduces. Worth removing before the port so"
            " the test phase can actually see errors."
        ),
        detector=sql_detector(
            feature_grep(
                ("when_others_null",),
                "REPLACE(UPPER(s.text), ' ', '') LIKE '%WHENOTHERSTHENNULL%'",
                "WHEN OTHERS THEN NULL",
            )
        ),
    ),
    Rule(
        id="R-SRC-12",
        title="Implicit cursor attributes",
        category="plsql",
        severity=Severity.LOW,
        effort=0.5,
        remedy=(
            "SQL%ROWCOUNT and friends become GET DIAGNOSTICS or the FOUND"
            " variable in PL/pgSQL; %ISOPEN has no direct equivalent for"
            " implicit cursors."
        ),
        detector=sql_detector(
            feature_grep(
                ("sql_cursor_attribute",),
                "UPPER(s.text) LIKE '%SQL\\%%' ESCAPE '\\'",
                "SQL% attribute",
            )
        ),
    ),
    Rule(
        id="R-SRC-13",
        title="RAISE_APPLICATION_ERROR",
        category="plsql",
        severity=Severity.LOW,
        effort=0.5,
        remedy=(
            "Map to RAISE EXCEPTION with USING ERRCODE. The -20000 range"
            " of custom error numbers disappears; applications that parse"
            " those numbers need a translation table."
        ),
        detector=sql_detector(
            "SELECT owner, name, type,"
            " 'RAISE_APPLICATION_ERROR (first at line ' || MIN(line) || ')'"
            " AS detail FROM plsql_calls"
            " WHERE callee = 'RAISE_APPLICATION_ERROR'"
            " GROUP BY owner, name, type"
            " UNION ALL"
            " SELECT s.owner, s.name, s.type,"
            " 'RAISE_APPLICATION_ERROR (first at line ' || MIN(s.line) || ')'"
            " AS detail FROM source s"
            " WHERE UPPER(s.text) LIKE '%RAISE_APPLICATION_ERROR%'"
            " AND NOT EXISTS (SELECT 1 FROM plsql_units u"
            " WHERE u.owner = s.owner AND u.name = s.name AND u.type = s.type"
            " AND u.error_count = 0)"
            " GROUP BY s.owner, s.name, s.type"
        ),
    ),
    Rule(
        id="R-SRC-14",
        title="Transaction control inside PL/SQL",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "PostgreSQL functions cannot COMMIT or ROLLBACK; only"
            " procedures called outside a transaction block can. Each"
            " routine that controls transactions must become a procedure"
            " or hand that control back to the caller."
        ),
        detector=sql_detector(
            feature_grep(
                ("commit", "rollback"),
                "UPPER(s.text) LIKE '%COMMIT;%' OR UPPER(s.text) LIKE '%ROLLBACK;%'",
                "COMMIT or ROLLBACK",
            )
        ),
    ),
    Rule(
        id="R-SRC-15",
        title="FORALL bulk binding",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "PL/pgSQL has no FORALL. The loop usually collapses into one"
            " set-based statement over unnest() of the collection, which"
            " is also the faster shape; SAVE EXCEPTIONS handling needs a"
            " separate error-logging design."
        ),
        detector=sql_detector(
            feature_grep(("forall",), "UPPER(s.text) LIKE '%FORALL %'", "FORALL")
        ),
    ),
    Rule(
        id="R-SRC-16",
        title="PL/SQL collection type",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=2.0,
        remedy=(
            "Nested tables, varrays, and associative arrays map to"
            " PostgreSQL arrays, jsonb, or temporary tables depending on"
            " use; collection methods such as EXTEND, COUNT, and FIRST"
            " have no direct equivalents and every reader changes."
        ),
        detector=sql_detector(
            feature_grep(
                ("collection_type",),
                "UPPER(s.text) LIKE '%TABLE OF %'"
                " OR UPPER(s.text) LIKE '%VARRAY(%'"
                " OR UPPER(s.text) LIKE '%VARRAY (%'",
                "collection type declaration",
            )
        ),
    ),
    Rule(
        id="R-SRC-20",
        title="Wrapped PL/SQL",
        category="plsql",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "The stored source is wrapped: obfuscated bytecode with"
            " nothing readable to assess or port. Find the original in"
            " version control or request it from the vendor; a unit"
            " with neither must be reverse-engineered from behavior,"
            " which belongs in the estimate as its own line."
        ),
        detector=sql_detector(
            "SELECT owner, name, type, 'wrapped source' FROM plsql_units"
            " WHERE parse_mode = 'wrapped'"
        ),
    ),
    Rule(
        id="R-SRC-19",
        title="ROWID in code",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "ctid is not a ROWID: it moves on update and vacuum and must"
            " not be stored or compared. Fetch-by-rowid loops rewrite to"
            " primary-key access or WHERE CURRENT OF; ROWID-typed"
            " variables and parameters change type with them."
        ),
        detector=sql_detector(
            feature_grep(("rowid",), "UPPER(s.text) LIKE '%ROWID%'", "ROWID")
        ),
    ),
    Rule(
        id="R-SRC-18",
        title="Empty string treated as NULL",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.0,
        remedy=(
            "Oracle treats '' as NULL; PostgreSQL treats it as a real"
            " value. v := '' assigns NULL in Oracle but an empty string"
            " in PostgreSQL, NVL(x, '') stops collapsing, and col = ''"
            " can start matching rows. Nothing errors: behavior changes"
            " silently. Decide per site whether NULL or empty was meant,"
            " and put the data path under test."
        ),
        detector=sql_detector(
            feature_grep(
                ("empty_string_literal",),
                "s.text LIKE '%''''%'",
                "empty-string literal",
            )
        ),
    ),
    Rule(
        id="R-SRC-17",
        title="Pipelined table function",
        category="plsql",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "Becomes a set-returning function with RETURN NEXT or RETURN"
            " QUERY. PostgreSQL materializes the result set before the"
            " caller sees rows, so pipelines relied on for streaming or"
            " early-abort behavior need a design check, not just a port."
        ),
        detector=sql_detector(
            feature_grep(
                ("pipelined",),
                "UPPER(s.text) LIKE '%PIPELINED%'",
                "PIPELINED function",
            )
        ),
    ),
]

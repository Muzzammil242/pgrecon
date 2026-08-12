"""Rules over PL/SQL source and trigger structure.

Source detectors are token level: honest for an assessment and exactly
what the spec allows until the ANTLR deep-parse pass lands. Matching is
done per line against all_source text, deduplicated per object.
"""

from pgrecon.rules import Rule, Severity, source_grep, sql_detector

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
            source_grep("AUTONOMOUS_TRANSACTION", "PRAGMA AUTONOMOUS_TRANSACTION")
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
        detector=sql_detector(source_grep("EXECUTE IMMEDIATE", "EXECUTE IMMEDIATE")),
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
        detector=sql_detector(source_grep("GOTO ", "GOTO")),
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
        detector=sql_detector(source_grep("BULK COLLECT", "BULK COLLECT")),
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
        detector=sql_detector(source_grep("REF CURSOR", "REF CURSOR")),
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
            "SELECT owner, name, type,"
            " 'WHEN OTHERS THEN NULL (first at line ' || MIN(line) || ')'"
            " AS detail FROM source"
            " WHERE REPLACE(UPPER(text), ' ', '')"
            " LIKE '%WHENOTHERSTHENNULL%'"
            " GROUP BY owner, name, type"
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
            "SELECT owner, name, type,"
            " 'SQL% attribute (first at line ' || MIN(line) || ')'"
            " AS detail FROM source"
            " WHERE UPPER(text) LIKE '%SQL\\%%' ESCAPE '\\'"
            " GROUP BY owner, name, type"
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
            source_grep("RAISE_APPLICATION_ERROR", "RAISE_APPLICATION_ERROR")
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
            "SELECT owner, name, type,"
            " 'COMMIT or ROLLBACK (first at line ' || MIN(line) || ')'"
            " AS detail FROM source"
            " WHERE UPPER(text) LIKE '%COMMIT;%'"
            " OR UPPER(text) LIKE '%ROLLBACK;%'"
            " GROUP BY owner, name, type"
        ),
    ),
]

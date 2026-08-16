"""Rules over Oracle supplied-package usage in PL/SQL source.

Usage is read from the call graph the deep parse stored, so a package
named in a comment or a string literal is not usage; units the parser
rejected fall back to token greps.
"""

from pgrecon.rules import Rule, Severity, calls_grep, sql_detector

RULES = [
    Rule(
        id="R-SYS-01",
        title="UTL_FILE usage",
        category="supplied packages",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "PostgreSQL functions have no supported server-side file API."
            " Move file handling to the application, or accept the"
            " operational cost of an untrusted language such as plpython."
        ),
        extension="orafce",
        detector=sql_detector(calls_grep(("UTL_FILE",), "UTL_FILE")),
    ),
    Rule(
        id="R-SYS-02",
        title="Network calls from the database",
        category="supplied packages",
        severity=Severity.HIGH,
        effort=4.0,
        remedy=(
            "UTL_HTTP, UTL_SMTP, and UTL_TCP have no equivalent inside"
            " PostgreSQL. Move outbound calls to the application or a"
            " worker that polls a queue table; calling out of the database"
            " from a trigger is a design smell worth fixing during the"
            " migration anyway."
        ),
        detector=sql_detector(
            calls_grep(("UTL_HTTP", "UTL_SMTP", "UTL_TCP"), "network package")
        ),
    ),
    Rule(
        id="R-SYS-03",
        title="DBMS_SQL usage",
        category="supplied packages",
        severity=Severity.HIGH,
        effort=3.0,
        remedy=(
            "The DBMS_SQL cursor API has no counterpart. Most call sites"
            " rewrite to PL/pgSQL EXECUTE with USING binds; describe-style"
            " introspection needs a redesign."
        ),
        detector=sql_detector(calls_grep(("DBMS_SQL",), "DBMS_SQL")),
    ),
    Rule(
        id="R-SYS-04",
        title="DBMS_LOB usage",
        category="supplied packages",
        severity=Severity.MEDIUM,
        effort=1.5,
        remedy=(
            "Piecewise LOB calls mostly disappear: text and bytea are"
            " handled whole, with substring and length built in. Streaming"
            " access beyond 1 GB needs large objects and the lo_ API."
        ),
        detector=sql_detector(calls_grep(("DBMS_LOB",), "DBMS_LOB")),
    ),
    Rule(
        id="R-SYS-05",
        title="DBMS_OUTPUT usage",
        category="supplied packages",
        severity=Severity.LOW,
        effort=0.3,
        remedy=(
            "Map PUT_LINE to RAISE NOTICE for diagnostics. If callers"
            " consume the output programmatically, that pattern needs a"
            " real interface instead."
        ),
        extension="orafce",
        detector=sql_detector(calls_grep(("DBMS_OUTPUT",), "DBMS_OUTPUT")),
    ),
]

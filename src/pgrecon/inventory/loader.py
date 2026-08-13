"""Load an offline extraction dump into the SQLite inventory.

The dump folder is produced by the SQL*Plus script that ships with
pgrecon (see pgrecon.extract). CSV files carry catalog metadata; the
ddl_*.sql files carry DDL, one object per marker line of the form:

    -- PGRECON_OBJECT <TYPE> <OWNER>.<NAME>

Every DDL statement is parsed with sqlglot's Oracle dialect and the
outcome is stored alongside the text. A statement the parser rejects is
recorded, never dropped: unparseable DDL is itself an assessment signal.
"""

import csv
import io
import logging
import re
import sqlite3
from collections.abc import Iterator
from importlib import resources
from pathlib import Path
from typing import TextIO

import sqlglot
from sqlglot.errors import SqlglotError

logger = logging.getLogger("pgrecon.inventory")

# CSV file name -> (inventory table, dump header -> column mapping).
# Files missing from the dump are skipped; a partial dump still loads.
CSV_TABLES: dict[str, tuple[str, dict[str, str]]] = {
    "meta.csv": ("meta", {"KEY": "key", "VALUE": "value"}),
    "objects.csv": (
        "objects",
        {
            "OWNER": "owner",
            "OBJECT_NAME": "name",
            "OBJECT_TYPE": "type",
            "STATUS": "status",
            "CREATED": "created",
            "LAST_DDL_TIME": "last_ddl",
        },
    ),
    "tables.csv": (
        "tables",
        {
            "OWNER": "owner",
            "TABLE_NAME": "table_name",
            "NUM_ROWS": "num_rows",
            "AVG_ROW_LEN": "avg_row_len",
            "PARTITIONED": "partitioned",
            "TEMPORARY": "temporary",
            "DEGREE": "degree",
        },
    ),
    "columns.csv": (
        "columns",
        {
            "OWNER": "owner",
            "TABLE_NAME": "table_name",
            "COLUMN_NAME": "column_name",
            "COLUMN_ID": "position",
            "DATA_TYPE": "data_type",
            "DATA_LENGTH": "data_length",
            "DATA_PRECISION": "data_precision",
            "DATA_SCALE": "data_scale",
            "NULLABLE": "nullable",
        },
    ),
    "source.csv": (
        "source",
        {
            "OWNER": "owner",
            "NAME": "name",
            "TYPE": "type",
            "LINE": "line",
            "TEXT": "text",
        },
    ),
    "features.csv": (
        "features",
        {"FEATURE": "feature", "DETAIL": "detail", "CNT": "count"},
    ),
    "dependencies.csv": (
        "dependencies",
        {
            "OWNER": "owner",
            "NAME": "name",
            "TYPE": "type",
            "REFERENCED_OWNER": "ref_owner",
            "REFERENCED_NAME": "ref_name",
            "REFERENCED_TYPE": "ref_type",
        },
    ),
    "constraints.csv": (
        "constraints",
        {
            "OWNER": "owner",
            "CONSTRAINT_NAME": "constraint_name",
            "TABLE_NAME": "table_name",
            "CONSTRAINT_TYPE": "type",
            "STATUS": "status",
            "R_OWNER": "ref_owner",
            "R_CONSTRAINT_NAME": "ref_constraint",
            "DELETE_RULE": "delete_rule",
        },
    ),
    "constraint_columns.csv": (
        "constraint_columns",
        {
            "OWNER": "owner",
            "CONSTRAINT_NAME": "constraint_name",
            "COLUMN_NAME": "column_name",
            "POSITION": "position",
        },
    ),
    "check_conditions.csv": (
        "check_conditions",
        {
            "OWNER": "owner",
            "CONSTRAINT_NAME": "constraint_name",
            "CONDITION": "condition",
            "TRUNCATED": "truncated",
        },
    ),
    "indexes.csv": (
        "indexes",
        {
            "OWNER": "owner",
            "INDEX_NAME": "index_name",
            "TABLE_NAME": "table_name",
            "INDEX_TYPE": "index_type",
            "UNIQUENESS": "uniqueness",
            "STATUS": "status",
            "GENERATED": "generated",
            "DEGREE": "degree",
        },
    ),
    "index_columns.csv": (
        "index_columns",
        {
            "OWNER": "owner",
            "INDEX_NAME": "index_name",
            "COLUMN_NAME": "column_name",
            "COLUMN_POSITION": "position",
        },
    ),
    "index_expressions.csv": (
        "index_expressions",
        {
            "OWNER": "owner",
            "INDEX_NAME": "index_name",
            "COLUMN_POSITION": "position",
            "COLUMN_EXPRESSION": "expression",
            "TRUNCATED": "truncated",
        },
    ),
    "part_tables.csv": (
        "part_tables",
        {
            "OWNER": "owner",
            "TABLE_NAME": "table_name",
            "PARTITIONING_TYPE": "partitioning_type",
            "SUBPARTITIONING_TYPE": "subpartitioning_type",
            "PARTITION_COUNT": "partition_count",
            "INTERVAL": "interval",
        },
    ),
    "part_key_columns.csv": (
        "part_key_columns",
        {
            "OWNER": "owner",
            "NAME": "table_name",
            "COLUMN_NAME": "column_name",
            "COLUMN_POSITION": "position",
        },
    ),
    "synonyms.csv": (
        "synonyms",
        {
            "OWNER": "owner",
            "SYNONYM_NAME": "synonym_name",
            "TABLE_OWNER": "table_owner",
            "TABLE_NAME": "table_name",
            "DB_LINK": "db_link",
        },
    ),
    "triggers.csv": (
        "triggers",
        {
            "OWNER": "owner",
            "TRIGGER_NAME": "trigger_name",
            "TRIGGER_TYPE": "trigger_type",
            "TRIGGERING_EVENT": "triggering_event",
            "TABLE_NAME": "table_name",
            "STATUS": "status",
        },
    ),
    "db_links.csv": (
        "db_links",
        {
            "OWNER": "owner",
            "DB_LINK": "db_link",
            "USERNAME": "username",
            "HOST": "host",
        },
    ),
    "part_indexes.csv": (
        "part_indexes",
        {
            "OWNER": "owner",
            "INDEX_NAME": "index_name",
            "TABLE_NAME": "table_name",
            "LOCALITY": "locality",
        },
    ),
    "mviews.csv": (
        "mviews",
        {
            "OWNER": "owner",
            "MVIEW_NAME": "mview_name",
            "REWRITE_ENABLED": "rewrite_enabled",
            "REFRESH_METHOD": "refresh_method",
        },
    ),
    "plan_management.csv": (
        "plan_management",
        {"KIND": "kind", "NAME": "name", "ENABLED": "enabled"},
    ),
}

INT_COLUMNS = {
    "num_rows",
    "avg_row_len",
    "position",
    "data_length",
    "data_precision",
    "data_scale",
    "line",
    "count",
    "partition_count",
    "truncated",
}

DDL_MARKER = re.compile(r"^-- PGRECON_OBJECT (\S+) ([^\s.]+)\.(\S+)\s*$", re.MULTILINE)

# DBMS_METADATA output carries physical and state keywords that
# sqlglot's Oracle grammar rejects but that mean nothing for an
# assessment: constraint states (ENABLE and friends), the spelled-out
# backing-sequence options of identity columns, and the VIRTUAL marker
# on generated columns. The syntax check runs on a normalized copy;
# the stored DDL is always the verbatim text from the dump.
PARSE_NORMALIZATIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(GENERATED\s+(?:ALWAYS|BY\s+DEFAULT(?:\s+ON\s+NULL)?)\s+AS\s+IDENTITY)"
            r"(?:\s+(?:MINVALUE\s+\d+|MAXVALUE\s+\d+|INCREMENT\s+BY\s+\d+"
            r"|START\s+WITH\s+\d+|CACHE\s+\d+|NOCACHE|ORDER|NOORDER|CYCLE|NOCYCLE"
            r"|KEEP|NOKEEP|SCALE|NOSCALE|EXTEND|NOEXTEND|SESSION|GLOBAL))*",
            re.IGNORECASE,
        ),
        r"\1",
    ),
    (
        re.compile(
            r"\s+(?:ENABLE|DISABLE)(?:\s+(?:NOVALIDATE|VALIDATE))?\b"
            r"|\s+(?:NOVALIDATE|VALIDATE)\b"
        ),
        "",
    ),
    (re.compile(r"\s+VIRTUAL\b", re.IGNORECASE), ""),
)


def open_db(db_path: Path) -> sqlite3.Connection:
    """Create the inventory database, replacing any existing file."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    schema = resources.files("pgrecon.inventory").joinpath("schema.sql")
    conn.executescript(schema.read_text(encoding="ascii"))
    return conn


def load_dump(
    dump_dir: Path, db_path: Path, encoding: str = "utf-8-sig"
) -> dict[str, int]:
    """Load a dump folder into db_path and return row counts per table.

    Files that do not decode with the given encoding are decoded again
    with replacement characters instead of failing the load; each such
    file is recorded as an encoding_warning row in the meta table. The
    extraction scripts ask for NLS_LANG=.AL32UTF8, but dumps arrive in
    whatever the client environment produced.
    """
    if not dump_dir.is_dir():
        raise FileNotFoundError(f"dump directory not found: {dump_dir}")

    conn = open_db(db_path)
    lossy: list[str] = []
    try:
        counts: dict[str, int] = {}
        for file_name, (table, mapping) in CSV_TABLES.items():
            path = dump_dir / file_name
            if path.exists():
                text = _read_text(path, encoding, lossy)
                counts[table] = _load_csv(conn, text, table, mapping)
        counts["ddl"] = 0
        for path in sorted(dump_dir.glob("ddl_*.sql")):
            text = _read_text(path, encoding, lossy)
            counts["ddl"] += _load_ddl(conn, text)
        (
            counts["plsql_units"],
            counts["plsql_features"],
            counts["plsql_calls"],
        ) = _analyze_plsql(conn)
        conn.executemany(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            [
                (
                    f"encoding_warning:{name}",
                    f"not valid {encoding}; decoded with replacement"
                    " characters, pass --encoding with the real one",
                )
                for name in lossy
            ],
        )
        conn.commit()
        return counts
    finally:
        conn.close()


def _read_text(path: Path, encoding: str, lossy: list[str]) -> str:
    data = path.read_bytes()
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        lossy.append(path.name)
        return data.decode(encoding, errors="replace")


def _load_csv(
    conn: sqlite3.Connection,
    text: str,
    table: str,
    mapping: dict[str, str],
) -> int:
    columns = list(mapping.values())
    placeholders = ", ".join("?" for _ in columns)
    sql = (
        f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    )

    rows = []
    for record in csv.DictReader(_data_lines(io.StringIO(text))):
        rows.append(
            tuple(
                _coerce(column, record.get(header))
                for header, column in mapping.items()
            )
        )
    conn.executemany(sql, rows)
    return len(rows)


def _data_lines(fh: TextIO) -> Iterator[str]:
    # SQL*Plus opens every spool with a blank line before the CSV header;
    # skip leading blanks so DictReader reads the real header first.
    for line in fh:
        if line.strip():
            yield line
            break
    yield from fh


def _coerce(column: str, value: str | None) -> str | int | None:
    if value is None or value == "":
        return None
    if column in INT_COLUMNS:
        return int(float(value))
    return value


def _load_ddl(conn: sqlite3.Connection, text: str) -> int:
    markers = list(DDL_MARKER.finditer(text))
    rows = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        obj_type, owner, name = marker.groups()
        statement = text[marker.end() : end].strip()
        error, quality = _oracle_parse(statement)
        rows.append((owner, name, obj_type, statement, error is None, error, quality))
    conn.executemany(
        "INSERT OR REPLACE INTO ddl"
        " (owner, name, type, ddl, parse_ok, parse_error, parse_quality)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def _analyze_plsql(conn: sqlite3.Connection) -> tuple[int, int, int]:
    """Deep-parse every stored unit and persist facts for the rules.

    Features come only from units that parse clean; a unit that does
    not is recorded with its first error and keeps token-level rule
    coverage. The import is deferred because the generated parser
    costs real time to load and only this step needs it.
    """
    from pgrecon.plsql.walk import analyze_source

    groups: dict[tuple[str, str, str], list[str]] = {}
    for owner, name, otype, text in conn.execute(
        "SELECT owner, name, type, text FROM source ORDER BY owner, name, type, line"
    ):
        # Real dumps carry the newline inside each source line; the
        # parser and its line numbers need it either way.
        line = text or "\n"
        if not line.endswith("\n"):
            line += "\n"
        groups.setdefault((owner, name, otype), []).append(line)

    if groups:
        logger.info("deep parse: %d stored units", len(groups))
    feature_count = 0
    call_count = 0
    for i, ((owner, name, otype), lines) in enumerate(groups.items(), start=1):
        analysis = analyze_source("".join(lines))
        if analysis.errors:
            logger.warning(
                "%s.%s (%s): %d syntax errors, token-level coverage only",
                owner,
                name,
                otype,
                len(analysis.errors),
            )
        conn.execute(
            "INSERT OR REPLACE INTO plsql_units"
            " (owner, name, type, parse_mode, error_count, first_error)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                owner,
                name,
                otype,
                analysis.mode,
                len(analysis.errors),
                analysis.errors[0] if analysis.errors else None,
            ),
        )
        conn.executemany(
            "INSERT INTO plsql_features"
            " (owner, name, type, feature, line, detail)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [
                (owner, name, otype, f.feature, f.line, f.detail)
                for f in analysis.features
            ],
        )
        feature_count += len(analysis.features)
        conn.executemany(
            "INSERT INTO plsql_calls (owner, name, type, callee, line)"
            " VALUES (?, ?, ?, ?, ?)",
            [(owner, name, otype, call.callee, call.line) for call in analysis.calls],
        )
        call_count += len(analysis.calls)
        if i % 200 == 0:
            logger.info("deep parse: %d/%d units", i, len(groups))
    return len(groups), feature_count, call_count


def _oracle_parse(statement: str) -> tuple[str | None, str | None]:
    """Parse a statement and report (error, quality).

    quality is 'full' for a real syntax tree, 'fallback' when sqlglot
    accepted the text only as an opaque Command node, and None when the
    parse failed outright.
    """
    normalized = statement
    for pattern, replacement in PARSE_NORMALIZATIONS:
        normalized = pattern.sub(replacement, normalized)
    try:
        statements = sqlglot.parse(normalized, dialect="oracle")
    except SqlglotError as exc:
        return str(exc), None
    if any(
        expression is None or isinstance(expression, sqlglot.exp.Command)
        for expression in statements
    ):
        return None, "fallback"
    return None, "full"

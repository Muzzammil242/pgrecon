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
import re
import sqlite3
from collections.abc import Iterator
from importlib import resources
from pathlib import Path
from typing import TextIO

import sqlglot
from sqlglot.errors import SqlglotError

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


def load_dump(dump_dir: Path, db_path: Path) -> dict[str, int]:
    """Load a dump folder into db_path and return row counts per table."""
    if not dump_dir.is_dir():
        raise FileNotFoundError(f"dump directory not found: {dump_dir}")

    conn = open_db(db_path)
    try:
        counts: dict[str, int] = {}
        for file_name, (table, mapping) in CSV_TABLES.items():
            path = dump_dir / file_name
            if path.exists():
                counts[table] = _load_csv(conn, path, table, mapping)
        counts["ddl"] = sum(
            _load_ddl(conn, path) for path in sorted(dump_dir.glob("ddl_*.sql"))
        )
        conn.commit()
        return counts
    finally:
        conn.close()


def _load_csv(
    conn: sqlite3.Connection,
    path: Path,
    table: str,
    mapping: dict[str, str],
) -> int:
    columns = list(mapping.values())
    placeholders = ", ".join("?" for _ in columns)
    sql = (
        f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    )

    rows = []
    # SQL*Plus spools may lead with a BOM depending on client configuration.
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for record in csv.DictReader(_data_lines(fh)):
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


def _load_ddl(conn: sqlite3.Connection, path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    markers = list(DDL_MARKER.finditer(text))
    rows = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        obj_type, owner, name = marker.groups()
        statement = text[marker.end() : end].strip()
        error = _oracle_parse_error(statement)
        rows.append((owner, name, obj_type, statement, error is None, error))
    conn.executemany(
        "INSERT OR REPLACE INTO ddl"
        " (owner, name, type, ddl, parse_ok, parse_error)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def _oracle_parse_error(statement: str) -> str | None:
    normalized = statement
    for pattern, replacement in PARSE_NORMALIZATIONS:
        normalized = pattern.sub(replacement, normalized)
    try:
        sqlglot.parse(normalized, dialect="oracle")
    except SqlglotError as exc:
        return str(exc)
    return None

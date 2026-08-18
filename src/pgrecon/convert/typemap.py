"""Oracle column types to PostgreSQL, deterministically.

Every mapping is a documented decision, not a guess: where PostgreSQL
has an exact counterpart the mapping is silent, where semantics shift
the mapping carries a note that surfaces in the residue report, and
where no counterpart exists the type maps to None and the column
becomes a residue item instead of wrong DDL.
"""

import re
from dataclasses import dataclass

_TIMESTAMP = re.compile(r"^TIMESTAMP\((\d+)\)$")
_TIMESTAMP_TZ = re.compile(r"^TIMESTAMP\((\d+)\) WITH TIME ZONE$")
_TIMESTAMP_LTZ = re.compile(r"^TIMESTAMP\((\d+)\) WITH LOCAL TIME ZONE$")
_INTERVAL_YM = re.compile(r"^INTERVAL YEAR\(\d+\) TO MONTH$")
_INTERVAL_DS = re.compile(r"^INTERVAL DAY\(\d+\) TO SECOND\(\d+\)$")


@dataclass(frozen=True)
class Mapped:
    """One column's mapping: the target type, or None plus the reason."""

    pg_type: str | None
    note: str | None = None


def map_type(
    data_type: str | None,
    length: int | None,
    precision: int | None,
    scale: int | None,
) -> Mapped:
    dtype = (data_type or "").strip().upper()

    if dtype == "NUMBER":
        if precision is None:
            return Mapped("numeric")
        if scale in (0, None):
            if precision <= 4:
                return Mapped("smallint")
            if precision <= 9:
                return Mapped("integer")
            if precision <= 18:
                return Mapped("bigint")
            return Mapped(f"numeric({precision})")
        return Mapped(f"numeric({precision},{scale})")
    if dtype == "FLOAT":
        return Mapped("double precision")
    if dtype == "BINARY_FLOAT":
        return Mapped("real")
    if dtype == "BINARY_DOUBLE":
        return Mapped("double precision")

    if dtype in ("VARCHAR2", "NVARCHAR2", "VARCHAR"):
        return Mapped(f"varchar({length})" if length else "varchar")
    if dtype in ("CHAR", "NCHAR"):
        return Mapped(f"char({length})" if length else "char")
    if dtype in ("CLOB", "NCLOB"):
        return Mapped("text")
    if dtype == "LONG":
        return Mapped(
            "text", "LONG survives as text; ordering and OCI semantics do not"
        )
    if dtype == "BLOB":
        return Mapped("bytea")
    if dtype in ("RAW", "LONG RAW"):
        return Mapped("bytea")

    if dtype == "DATE":
        return Mapped(
            "timestamp(0)",
            "Oracle DATE carries a time of day; date alone would lose it",
        )
    m = _TIMESTAMP.match(dtype)
    if m:
        return Mapped(f"timestamp({m.group(1)})")
    m = _TIMESTAMP_TZ.match(dtype)
    if m:
        return Mapped(f"timestamptz({m.group(1)})")
    m = _TIMESTAMP_LTZ.match(dtype)
    if m:
        return Mapped(
            f"timestamptz({m.group(1)})",
            "LOCAL TIME ZONE display semantics move to the client timezone setting",
        )
    if _INTERVAL_YM.match(dtype) or _INTERVAL_DS.match(dtype):
        return Mapped("interval", "interval precision constraints are not carried over")

    if dtype == "XMLTYPE":
        return Mapped(
            "xml", "XMLType methods and schemas have no counterpart; storage only"
        )

    if dtype in ("ROWID", "UROWID"):
        return Mapped(None, "no stable row-address type exists; rework the access path")
    if dtype == "BFILE":
        return Mapped(None, "external file locators have no counterpart")
    if dtype == "SDO_GEOMETRY":
        return Mapped(None, "spatial columns need PostGIS and a dedicated migration")

    return Mapped(None, f"user-defined or unsupported type {dtype or '(unknown)'}")


_SIZED = re.compile(
    r"^([A-Z_ ]+?)\s*\(\s*(\d+)\s*(?:(CHAR|BYTE)\s*)?(?:,\s*(-?\d+)\s*)?\)$"
)

# PL/SQL-only scalar types on top of the column map. SIMPLE_INTEGER
# wraps on overflow and NATURAL/POSITIVE carry range constraints, so
# they are absent: losing those semantics silently is not a mapping.
_CODE_TYPES = {
    "PLS_INTEGER": "integer",
    "BINARY_INTEGER": "integer",
    "BOOLEAN": "boolean",
    "STRING": "varchar",
    "REAL": "double precision",
    "DOUBLE PRECISION": "double precision",
    "TIMESTAMP": "timestamp",
}


def map_code_type(text: str) -> Mapped:
    """A type as written in PL/SQL source to PostgreSQL.

    Source text carries forms the dictionary never shows - bare
    NUMBER, PLS_INTEGER, VARCHAR2(30 CHAR) - so this normalizes the
    spelling and reuses the column rules for everything they cover.
    """
    dtype = " ".join(text.strip().upper().split())
    if dtype in _CODE_TYPES:
        return Mapped(_CODE_TYPES[dtype])
    if dtype.startswith("INTERVAL"):
        return Mapped("interval", "interval precision constraints are not carried over")
    base, length, precision, scale = dtype, None, None, None
    m = _SIZED.match(dtype)
    if m:
        base = m.group(1).strip()
        if base in ("NUMBER", "DECIMAL", "NUMERIC", "FLOAT"):
            precision = int(m.group(2))
            scale = int(m.group(4)) if m.group(4) else None
        else:
            length = int(m.group(2))
    if base in ("DECIMAL", "NUMERIC"):
        base = "NUMBER"
    if base in ("INT", "INTEGER", "SMALLINT"):
        # ANSI aliases are unconstrained NUMBER(*,0) underneath; the
        # honest mapping is numeric, not a range-limited integer.
        return Mapped("numeric")
    return map_type(base, length, precision, scale)

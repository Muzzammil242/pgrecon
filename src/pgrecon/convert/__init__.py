"""Schema conversion: inventory facts in, PostgreSQL DDL out.

Offline like everything else - the converter consumes the SQLite
inventory and emits DDL plus a residue report; it never connects to
either database.
"""

from pgrecon.convert.schema import (
    Conversion,
    Residue,
    convert_schema,
    residue_report,
)

__all__ = ["Conversion", "Residue", "convert_schema", "residue_report"]

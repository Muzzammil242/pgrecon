"""Offline extraction: the reviewable SQL*Plus scripts and their helpers."""

from importlib import resources


def script_text(legacy: bool = False) -> str:
    """Return the offline extraction script shipped with the package.

    The standard script needs a SQL*Plus 12.2+ client and targets Oracle
    11.2 or newer. The legacy variant runs on any old on-box SQL*Plus
    against Oracle 9.2 through 11.1: hand-built CSV, no DBMS_METADATA.
    """
    name = "pgrecon_extract_legacy.sql" if legacy else "pgrecon_extract.sql"
    path = resources.files("pgrecon.extract").joinpath(name)
    return path.read_text(encoding="ascii")

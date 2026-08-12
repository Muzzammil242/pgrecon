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


def needs_legacy(source_version: str) -> bool:
    """Decide the script variant from an Oracle version like 9.2 or 19.

    Anything below 11.2 takes the legacy variant. Raises ValueError for
    input that does not look like an Oracle version.
    """
    parts = source_version.strip().split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError) as exc:
        raise ValueError(f"not an Oracle version: {source_version!r}") from exc
    if not 8 <= major <= 30:
        raise ValueError(f"not a supported Oracle version: {source_version!r}")
    return (major, minor) < (11, 2)

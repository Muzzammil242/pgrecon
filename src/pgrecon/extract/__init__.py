"""Offline extraction: the reviewable SQL*Plus script and its helpers."""

from importlib import resources


def script_text() -> str:
    """Return the offline extraction script shipped with the package."""
    path = resources.files("pgrecon.extract").joinpath("pgrecon_extract.sql")
    return path.read_text(encoding="ascii")

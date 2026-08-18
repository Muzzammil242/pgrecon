"""The residue record shared by every emitter module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Residue:
    """One thing the converter declined to convert, and why."""

    owner: str
    object_name: str
    kind: str
    reason: str

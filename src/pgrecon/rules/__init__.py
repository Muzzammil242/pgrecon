"""The rule engine: deterministic findings over the inventory.

A rule is a declarative record: an id, a severity, a remedy, and a
detector that runs against the SQLite inventory and yields findings.
Most detectors are a single SQL query built with sql_detector(); the
query must select four columns: owner, name, type, detail.

Rules must stay deterministic. This package never imports the AI
layer, and tools/check_boundaries.py fails the build if it ever does.
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    owner: str
    name: str
    type: str
    detail: str


Detector = Callable[[sqlite3.Connection, "Rule"], list[Finding]]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    category: str
    severity: Severity
    effort: float
    remedy: str
    detector: Detector
    extension: str | None = None


def sql_detector(query: str) -> Detector:
    """Build a detector from a query selecting owner, name, type, detail."""

    def run(conn: sqlite3.Connection, rule: Rule) -> list[Finding]:
        return [
            Finding(rule.id, rule.severity, row[0], row[1], row[2], row[3])
            for row in conn.execute(query)
        ]

    return run


def all_rules() -> list[Rule]:
    from pgrecon.rules import code, columns, objects, packages, storage, syspackages

    rules = [
        *columns.RULES,
        *storage.RULES,
        *code.RULES,
        *packages.RULES,
        *syspackages.RULES,
        *objects.RULES,
    ]
    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rule id in registry")
    return rules

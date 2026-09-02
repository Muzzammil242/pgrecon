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


def feature_grep(features: tuple[str, ...], fallback_where: str, label: str) -> str:
    """Query deep parse facts, with a token grep for unparsed units.

    plsql_features covers every unit the deep parse accepted, so a
    match there is a construct in live code, never in a comment or a
    string literal. The grep half keeps coverage for units that failed
    to parse and for inventories loaded before the deep parse existed;
    fallback_where is a condition over the source table aliased as s.
    """
    quoted = ", ".join(f"'{feature}'" for feature in features)
    return (
        "SELECT owner, name, type,"
        f" '{label} (first at line ' || MIN(line) || ')' AS detail"
        f" FROM plsql_features WHERE feature IN ({quoted})"
        " GROUP BY owner, name, type"
        " UNION ALL"
        " SELECT s.owner, s.name, s.type,"
        f" '{label} (first at line ' || MIN(s.line) || ')' AS detail"
        f" FROM source s WHERE ({fallback_where})"
        " AND NOT EXISTS (SELECT 1 FROM plsql_units u"
        " WHERE u.owner = s.owner AND u.name = s.name AND u.type = s.type"
        " AND u.error_count = 0)"
        " GROUP BY s.owner, s.name, s.type"
    )


def calls_grep(packages: tuple[str, ...], label: str) -> str:
    """Query call sites into the named packages, greps for unparsed units.

    A callee in plsql_calls is an invocation in live code; the grep
    half mirrors feature_grep and covers only units without a clean
    parse. Both bare and schema-qualified callees match.
    """
    likes = " OR ".join(
        f"callee LIKE '{package}.%' OR callee LIKE '%.{package}.%'"
        for package in packages
    )
    greps = " OR ".join(f"UPPER(s.text) LIKE '%{package}.%'" for package in packages)
    return (
        "SELECT owner, name, type,"
        f" '{label} (first at line ' || MIN(line) || ')' AS detail"
        f" FROM plsql_calls WHERE {likes}"
        " GROUP BY owner, name, type"
        " UNION ALL"
        " SELECT s.owner, s.name, s.type,"
        f" '{label} (first at line ' || MIN(s.line) || ')' AS detail"
        f" FROM source s WHERE ({greps})"
        " AND NOT EXISTS (SELECT 1 FROM plsql_units u"
        " WHERE u.owner = s.owner AND u.name = s.name AND u.type = s.type"
        " AND u.error_count = 0)"
        " GROUP BY s.owner, s.name, s.type"
    )


def all_rules() -> list[Rule]:
    from pgrecon.rules import (
        code,
        columns,
        environment,
        objects,
        packages,
        performance,
        sqlconstructs,
        storage,
        syspackages,
    )

    rules = [
        *environment.RULES,
        *columns.RULES,
        *storage.RULES,
        *code.RULES,
        *sqlconstructs.RULES,
        *packages.RULES,
        *syspackages.RULES,
        *objects.RULES,
        *performance.RULES,
    ]
    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rule id in registry")
    return rules

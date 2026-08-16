"""Turn findings and inventory scale into a person-day estimate.

The estimate is built from named components so it can be argued with
line by line, which is the point: an opaque total invites either blind
trust or blind dismissal. Development effort is the sum of a baseline,
mechanical schema conversion, per-finding remediation, PL/SQL porting
by volume, and data movement; testing and stabilization is applied as
a factor range on top, because in field reports it rivals development
and nobody budgets it.

Every rate here is a default the author set from migration field
experience. None of it is a citation; all of it is visible, and real
engagements calibrate it against the client's team and workload.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from pgrecon.rules import Finding, Rule, Severity, all_rules

# Person-days. The baseline covers environments, tooling, data-movement
# setup, and cutover rehearsal scaffolding that exist even for a clean
# schema; none of that scales with table count, so it is flat.
BASELINE_PD = 5.0

# Mechanical conversion rates for objects that mostly translate.
CONVERT_TABLE_PD = 0.05
CONVERT_COLUMN_PD = 0.02
CONVERT_VIEW_PD = 0.1
CONVERT_SEQUENCE_PD = 0.02

# Porting rate for stored code, including its unit tests. Findings
# price the hotspots; this prices the bulk that merely needs careful
# transcription.
PLSQL_LINES_PER_DAY = 200.0

# Data movement is mostly machine time; the human share scales weakly
# with volume.
BYTES_PER_PD = 50e9

# A rule firing n times does not cost n times the first fix: the
# pattern is learned once. The marginal share of each further finding
# depends on how mechanical the fix is, which severity approximates.
MARGINAL = {
    Severity.INFO: 0.05,
    Severity.LOW: 0.2,
    Severity.MEDIUM: 0.5,
    Severity.HIGH: 0.7,
    Severity.BLOCKER: 1.0,
}

# Testing and stabilization as a share of development. Field reports
# put it between a third and everything-again-and-more.
TESTING_LOW = 1.3
TESTING_EXPECTED = 1.6
TESTING_HIGH = 2.2

WORKDAYS_PER_MONTH = 21.0


@dataclass(frozen=True)
class Component:
    label: str
    person_days: float


@dataclass(frozen=True)
class Estimate:
    components: tuple[Component, ...]
    development: float
    low: float
    expected: float
    high: float
    assumptions: tuple[str, ...]


def _scalar(conn: sqlite3.Connection, query: str) -> float:
    value = conn.execute(query).fetchone()[0]
    return float(value or 0)


def _remediation(findings: list[Finding], rules: list[Rule]) -> float:
    by_id = {rule.id: rule for rule in rules}
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
    total = 0.0
    for rule_id, n in counts.items():
        rule = by_id.get(rule_id)
        if rule is None:
            continue
        marginal = MARGINAL[rule.severity]
        total += rule.effort * (1 + marginal * (n - 1))
    return total


def estimate(
    db_path: Path, findings: list[Finding], rules: list[Rule] | None = None
) -> Estimate:
    if rules is None:
        rules = all_rules()
    conn = sqlite3.connect(db_path)
    try:
        tables = _scalar(conn, "SELECT COUNT(*) FROM tables")
        columns = _scalar(conn, "SELECT COUNT(*) FROM columns")
        views = _scalar(conn, "SELECT COUNT(*) FROM objects WHERE type = 'VIEW'")
        sequences = _scalar(
            conn, "SELECT COUNT(*) FROM objects WHERE type = 'SEQUENCE'"
        )
        source_lines = _scalar(conn, "SELECT COUNT(*) FROM source")
        data_bytes = _scalar(
            conn,
            "SELECT COALESCE(SUM(num_rows * avg_row_len), 0) FROM tables",
        )
    finally:
        conn.close()

    components = (
        Component("baseline and environment", BASELINE_PD),
        Component(
            "schema conversion",
            CONVERT_TABLE_PD * tables
            + CONVERT_COLUMN_PD * columns
            + CONVERT_VIEW_PD * views
            + CONVERT_SEQUENCE_PD * sequences,
        ),
        Component("finding remediation", _remediation(findings, rules)),
        Component("PL/SQL porting by volume", source_lines / PLSQL_LINES_PER_DAY),
        Component("data movement", data_bytes / BYTES_PER_PD),
    )
    development = sum(c.person_days for c in components)
    assumptions = (
        f"stored code ports at {PLSQL_LINES_PER_DAY:.0f} lines per person-day"
        " including unit tests",
        "repeated findings of one rule cost a severity-dependent fraction"
        " of the first fix",
        f"testing and stabilization runs {TESTING_LOW:.1f}x to"
        f" {TESTING_HIGH:.1f}x development, {TESTING_EXPECTED:.1f}x expected",
        "static estimate from schema facts alone: workload, data quality,"
        " and application coupling are not visible here",
    )
    return Estimate(
        components=components,
        development=round(development, 1),
        low=round(development * TESTING_LOW, 1),
        expected=round(development * TESTING_EXPECTED, 1),
        high=round(development * TESTING_HIGH, 1),
        assumptions=assumptions,
    )


def person_months(person_days: float) -> float:
    return round(person_days / WORKDAYS_PER_MONTH, 1)

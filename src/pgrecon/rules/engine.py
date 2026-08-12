"""Run rules over an inventory and summarize what they found."""

import sqlite3
from collections import Counter
from pathlib import Path
from typing import TypedDict

from pgrecon.rules import Finding, Rule, Severity, all_rules


class Summary(TypedDict):
    findings: int
    by_severity: dict[str, int]
    effort_points: float


SEVERITY_ORDER = [
    Severity.BLOCKER,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
]


def run_rules(db_path: Path, rules: list[Rule] | None = None) -> list[Finding]:
    if rules is None:
        rules = all_rules()
    conn = sqlite3.connect(db_path)
    try:
        findings = []
        for rule in rules:
            findings.extend(rule.detector(conn, rule))
        findings.sort(
            key=lambda f: (SEVERITY_ORDER.index(f.severity), f.rule_id, f.name)
        )
        return findings
    finally:
        conn.close()


def summarize(findings: list[Finding], rules: list[Rule] | None = None) -> Summary:
    if rules is None:
        rules = all_rules()
    effort_by_rule = {rule.id: rule.effort for rule in rules}
    by_severity = Counter(f.severity.value for f in findings)
    effort = sum(effort_by_rule.get(f.rule_id, 0.0) for f in findings)
    return {
        "findings": len(findings),
        "by_severity": {
            s.value: by_severity.get(s.value, 0)
            for s in SEVERITY_ORDER
            if by_severity.get(s.value)
        },
        # Raw weight sum, a sorting signal only. The effort model that
        # turns findings into person-day ranges is a later milestone.
        "effort_points": round(effort, 1),
    }

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pgrecon.cli import app
from pgrecon.effort import estimate, person_months
from pgrecon.inventory import open_db
from pgrecon.rules.engine import run_rules

runner = CliRunner()


@pytest.fixture()
def scaled_db(tmp_path: Path) -> Path:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.execute(
        "INSERT INTO tables (owner, table_name, num_rows, avg_row_len)"
        " VALUES ('HR', 'BIG', 1000000, 100)"
    )
    for i in range(4):
        conn.execute(
            "INSERT INTO columns (owner, table_name, column_name, data_type)"
            " VALUES ('HR', 'BIG', ?, 'LONG')",
            (f"C{i}",),
        )
    for line in range(1, 401):
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'P', 'PROCEDURE', ?, 'NULL;')",
            (line,),
        )
    conn.commit()
    conn.close()
    return db


def test_repetition_discount_prices_later_findings_lower(scaled_db: Path) -> None:
    findings = run_rules(scaled_db)
    long_findings = [f for f in findings if f.rule_id == "R-TYPE-01"]
    assert len(long_findings) == 4
    result = estimate(scaled_db, findings)
    remediation = next(c for c in result.components if c.label == "finding remediation")
    # R-TYPE-01 is high severity, effort 4.0, marginal 0.7:
    # 4.0 * (1 + 0.7 * 3) = 12.4, not the naive 16.0.
    assert remediation.person_days == pytest.approx(12.4)


def test_components_scale_with_inventory(scaled_db: Path) -> None:
    result = estimate(scaled_db, [])
    by_label = {c.label: c.person_days for c in result.components}
    assert by_label["PL/SQL porting by volume"] == pytest.approx(2.0)
    assert by_label["data movement"] == pytest.approx(0.002)
    assert result.development > 0
    assert result.low < result.expected < result.high


def test_person_months_conversion() -> None:
    assert person_months(210.0) == 10.0


def test_estimate_cli_text_and_json(scaled_db: Path) -> None:
    result = runner.invoke(app, ["estimate", "--db", str(scaled_db)])
    assert result.exit_code == 0
    assert "development subtotal" in result.output
    assert "person-months" in result.output
    assert "Assumptions:" in result.output

    result = runner.invoke(
        app, ["estimate", "--db", str(scaled_db), "--format", "json"]
    )
    payload = json.loads(result.output)
    assert payload["person_days"]["low"] < payload["person_days"]["high"]
    assert "finding remediation" in payload["components"]


def test_empty_inventory_still_estimates(tmp_path: Path) -> None:
    db = tmp_path / "empty.db"
    open_db(db).close()
    result = estimate(db, [])
    assert result.development == pytest.approx(5.0)

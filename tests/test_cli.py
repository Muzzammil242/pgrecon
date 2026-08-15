import json
from pathlib import Path

from typer.testing import CliRunner

from pgrecon.cli import app
from pgrecon.inventory import open_db

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.startswith("pgrecon ")


def test_script_writes_reviewable_sql(tmp_path: Path) -> None:
    out = tmp_path / "extract.sql"
    result = runner.invoke(app, ["script", "--out", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="ascii")
    assert "DBMS_METADATA.GET_DDL" in text
    assert "SET MARKUP CSV ON" in text


def test_legacy_script_avoids_modern_client_features(tmp_path: Path) -> None:
    out = tmp_path / "extract_legacy.sql"
    result = runner.invoke(app, ["script", "--legacy", "--out", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="ascii")
    # The legacy variant must run on a 9.2 server with its own client:
    # no CSV markup, no DBMS_METADATA calls, no 10g-only dictionary
    # views. Header comments may mention them; commands may not.
    assert "SET MARKUP CSV ON" not in text
    assert "DBMS_METADATA.GET_DDL" not in text
    assert "all_scheduler_jobs" not in text
    assert "PGRECON_OBJECT VIEW" in text


def test_source_version_picks_variant(tmp_path: Path) -> None:
    out = tmp_path / "for_10g.sql"
    result = runner.invoke(
        app, ["script", "--source-version", "10.2", "--out", str(out)]
    )
    assert result.exit_code == 0
    assert "legacy variant" in result.output
    assert "DBMS_METADATA.GET_DDL" not in out.read_text(encoding="ascii")

    out = tmp_path / "for_19c.sql"
    result = runner.invoke(app, ["script", "--source-version", "19", "--out", str(out)])
    assert result.exit_code == 0
    assert "DBMS_METADATA.GET_DDL" in out.read_text(encoding="ascii")


def test_source_version_rejects_garbage() -> None:
    result = runner.invoke(app, ["script", "--source-version", "banana"])
    assert result.exit_code != 0


def test_load_and_info(dump_basic: Path, tmp_path: Path) -> None:
    db = tmp_path / "inventory.db"
    result = runner.invoke(app, ["load", str(dump_basic), "--db", str(db)])
    assert result.exit_code == 0
    assert "objects" in result.output

    result = runner.invoke(app, ["info", "--db", str(db)])
    assert result.exit_code == 0
    assert "schema: HR" in result.output
    assert "ddl parsed: 3/4" in result.output


def test_report_remedies_appendix(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_BLANKS', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_features (owner, name, type, feature, line, detail)"
        " VALUES ('HR', 'P_BLANKS', 'PROCEDURE', 'empty_string_literal', 6, NULL)"
    )
    conn.commit()
    conn.close()
    result = runner.invoke(app, ["report", "--db", str(db), "--remedies"])
    assert result.exit_code == 0
    assert "Remedies:" in result.output
    assert "R-SRC-18  Empty string treated as NULL  [medium, 1 finding]" in (
        result.output
    )
    assert "Oracle treats '' as NULL" in result.output


def test_report_json_carries_rule_metadata(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.execute(
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('HR', 'NOTES', 'BODY', 'LONG')"
    )
    conn.commit()
    conn.close()
    result = runner.invoke(app, ["report", "--db", str(db), "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    rule = payload["rules"]["R-TYPE-01"]
    assert rule["severity"] == "high"
    assert rule["remedy"]
    assert set(payload["rules"]) == {f["rule_id"] for f in payload["findings"]}


def test_explain_one_rule() -> None:
    result = runner.invoke(app, ["explain", "r-src-18"])
    assert result.exit_code == 0
    assert "R-SRC-18: Empty string treated as NULL" in result.output
    assert "severity: medium" in result.output


def test_explain_lists_catalog() -> None:
    result = runner.invoke(app, ["explain"])
    assert result.exit_code == 0
    assert "R-TYPE-01" in result.output
    assert "63 rules" in result.output


def test_explain_rejects_unknown_id() -> None:
    result = runner.invoke(app, ["explain", "R-NOPE-99"])
    assert result.exit_code != 0

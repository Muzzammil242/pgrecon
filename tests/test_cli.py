from pathlib import Path

from typer.testing import CliRunner

from pgrecon.cli import app

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


def test_load_and_info(dump_basic: Path, tmp_path: Path) -> None:
    db = tmp_path / "inventory.db"
    result = runner.invoke(app, ["load", str(dump_basic), "--db", str(db)])
    assert result.exit_code == 0
    assert "objects" in result.output

    result = runner.invoke(app, ["info", "--db", str(db)])
    assert result.exit_code == 0
    assert "schema: HR" in result.output
    assert "ddl parsed: 3/4" in result.output

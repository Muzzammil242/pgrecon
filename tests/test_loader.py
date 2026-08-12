import sqlite3
from pathlib import Path

import pytest

from pgrecon.inventory import load_dump


@pytest.fixture()
def loaded(dump_basic: Path, tmp_path: Path) -> tuple[dict[str, int], Path]:
    db = tmp_path / "inventory.db"
    counts = load_dump(dump_basic, db)
    return counts, db


def test_counts_match_fixture(loaded: tuple[dict[str, int], Path]) -> None:
    counts, _ = loaded
    assert counts["objects"] == 5
    assert counts["tables"] == 1
    assert counts["columns"] == 3
    assert counts["source"] == 11
    assert counts["features"] == 4
    assert counts["dependencies"] == 2
    assert counts["ddl"] == 4


def test_columns_are_typed(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT position, data_precision, data_scale FROM columns"
        " WHERE table_name = 'EMP' AND column_name = 'ID'"
    ).fetchone()
    assert row == (1, 10, 0)
    # Empty CSV fields must load as NULL, not as empty strings.
    precision = conn.execute(
        "SELECT data_precision FROM columns WHERE column_name = 'NAME'"
    ).fetchone()[0]
    assert precision is None


def test_ddl_parse_outcome_is_recorded(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    ok = dict(
        conn.execute("SELECT name, parse_ok FROM ddl WHERE type = 'TABLE'").fetchall()
    )
    # INVOICES carries the identity-options tail DBMS_METADATA emits;
    # it must parse after normalization.
    assert ok == {"EMP": 1, "INVOICES": 1, "BROKEN": 0}
    error = conn.execute(
        "SELECT parse_error FROM ddl WHERE name = 'BROKEN'"
    ).fetchone()[0]
    assert error
    # The unparseable statement is kept verbatim for manual review.
    text = conn.execute("SELECT ddl FROM ddl WHERE name = 'BROKEN'").fetchone()[0]
    assert "not valid sql" in text


def test_ddl_is_stored_verbatim(loaded: tuple[dict[str, int], Path]) -> None:
    # The parse runs on a normalized copy; the stored text keeps the
    # DBMS_METADATA output exactly as extracted, ENABLE keywords and all.
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT ddl, parse_ok FROM ddl WHERE name = 'EMP'").fetchone()
    assert "NOT NULL ENABLE" in row[0]
    assert row[1] == 1


def test_view_ddl_parses(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT parse_ok FROM ddl WHERE name = 'EMP_V'").fetchone()
    assert row == (1,)


def test_missing_dump_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_dump(tmp_path / "nope", tmp_path / "inventory.db")


def test_reload_replaces_database(dump_basic: Path, tmp_path: Path) -> None:
    db = tmp_path / "inventory.db"
    load_dump(dump_basic, db)
    counts = load_dump(dump_basic, db)
    assert counts["objects"] == 5

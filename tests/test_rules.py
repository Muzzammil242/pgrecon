import sqlite3
from pathlib import Path

import pytest

from pgrecon.inventory import load_dump, open_db
from pgrecon.rules import all_rules
from pgrecon.rules.engine import run_rules, summarize


@pytest.fixture()
def inventory(tmp_path: Path) -> tuple[sqlite3.Connection, Path]:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    yield conn, db
    conn.close()


def fired(db: Path, rule_id: str) -> list[str]:
    return [f.name for f in run_rules(db) if f.rule_id == rule_id]


def test_registry_has_unique_ids_and_real_remedies() -> None:
    rules = all_rules()
    assert len(rules) >= 15
    assert len({r.id for r in rules}) == len(rules)
    for rule in rules:
        assert rule.remedy and len(rule.remedy) > 40, rule.id


def test_long_column_fires(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('HR', 'NOTES', 'BODY', 'LONG')"
    )
    conn.execute(
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('HR', 'NOTES', 'TITLE', 'VARCHAR2')"
    )
    conn.commit()
    assert fired(db, "R-TYPE-01") == ["NOTES.BODY"]


def test_compound_trigger_fires(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO triggers (owner, trigger_name, trigger_type, table_name)"
        " VALUES ('HR', 'TRG_X', 'COMPOUND', 'EMP')"
    )
    conn.execute(
        "INSERT INTO triggers (owner, trigger_name, trigger_type, table_name)"
        " VALUES ('HR', 'TRG_Y', 'AFTER EACH ROW', 'EMP')"
    )
    conn.commit()
    assert fired(db, "R-TRG-01") == ["TRG_X"]


def test_source_grep_dedupes_per_object(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    for line, text in [
        (1, "PROCEDURE audit_it IS"),
        (2, "  PRAGMA AUTONOMOUS_TRANSACTION;"),
        (5, "  -- pragma autonomous_transaction mentioned again"),
    ]:
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'AUDIT_IT', 'PROCEDURE', ?, ?)",
            (line, text),
        )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-TRG-02"]
    assert len(findings) == 1
    assert "line 2" in findings[0].detail


def test_db_link_feature_fires_only_when_present(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO features (feature, detail, count)"
        " VALUES ('db_links', 'owned or public', 0)"
    )
    conn.commit()
    assert fired(db, "R-OBJ-01") == []
    conn.execute("UPDATE features SET count = 2 WHERE feature = 'db_links'")
    conn.commit()
    assert len(fired(db, "R-OBJ-01")) == 1


def test_connect_by_found_in_source_and_view_ddl(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'ORG_PROC', 'PROCEDURE', 4, 'CONNECT BY PRIOR id = mgr')"
    )
    conn.execute(
        "INSERT INTO ddl (owner, name, type, ddl, parse_ok) VALUES"
        " ('HR', 'V_TREE', 'VIEW', 'CREATE VIEW v AS SELECT 1 CONNECT BY x', 1)"
    )
    conn.commit()
    assert sorted(fired(db, "R-SRC-04")) == ["ORG_PROC", "V_TREE"]


def test_summary_counts_and_effort(tmp_path: Path, dump_basic: Path) -> None:
    db = tmp_path / "inv.db"
    load_dump(dump_basic, db)
    findings = run_rules(db)
    summary = summarize(findings)
    assert summary["findings"] == len(findings)
    assert summary["effort_points"] > 0


def test_findings_on_fixture_dump(tmp_path: Path, dump_basic: Path) -> None:
    db = tmp_path / "inv.db"
    load_dump(dump_basic, db)
    ids = {f.rule_id for f in run_rules(db)}
    # Interval partitioning, the unparseable DDL statement, the
    # function-based index, and the db-link probe are in the fixture.
    assert {"R-PART-01", "R-DDL-01", "R-IDX-02", "R-OBJ-01"} <= ids
    # No compound trigger and no LONG column in the fixture.
    assert "R-TRG-01" not in ids
    assert "R-TYPE-01" not in ids

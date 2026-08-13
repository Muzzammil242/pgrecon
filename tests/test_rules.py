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
    assert len(rules) >= 40
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


def test_db_link_fires_per_link_with_target(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    assert fired(db, "R-OBJ-01") == []
    conn.execute(
        "INSERT INTO db_links (owner, db_link, username, host) VALUES"
        " ('HR', 'ERP_LINK', 'ERP_RO', '//erp-db:1521/PROD')"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-OBJ-01"]
    assert [f.name for f in findings] == ["ERP_LINK"]
    assert "erp-db" in findings[0].detail


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


def test_package_state_fires_on_body_not_spec(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    spec = [
        (1, "PACKAGE clean_pkg AS"),
        (2, "  FUNCTION f RETURN NUMBER;"),
        (3, "END clean_pkg;"),
    ]
    body = [
        (1, "PACKAGE BODY stateful_pkg AS"),
        (2, "  g_total NUMBER := 0;"),
        (3, "  g_name  VARCHAR2(30);"),
        (4, "  FUNCTION f RETURN NUMBER IS"),
        (5, "  BEGIN RETURN g_total; END;"),
        (6, "END stateful_pkg;"),
    ]
    for line, text in spec:
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'CLEAN_PKG', 'PACKAGE', ?, ?)",
            (line, text),
        )
    for line, text in body:
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'STATEFUL_PKG', 'PACKAGE BODY', ?, ?)",
            (line, text),
        )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-PKG-01"]
    assert [f.name for f in findings] == ["STATEFUL_PKG (body)"]
    assert "2 package-level declaration(s)" in findings[0].detail


def test_package_init_block_heuristic(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    body = [
        (1, "PACKAGE BODY init_pkg AS"),
        (2, "  PROCEDURE p IS"),
        (3, "  BEGIN NULL; END;"),
        (4, "BEGIN"),
        (5, "  init_something();"),
        (6, "END init_pkg;"),
    ]
    for line, text in body:
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'INIT_PKG', 'PACKAGE BODY', ?, ?)",
            (line, text),
        )
    conn.commit()
    assert fired(db, "R-PKG-02") == ["INIT_PKG"]


def test_supplied_package_usage(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'LOADER', 'PROCEDURE', 9,"
        " '  l_file := UTL_FILE.FOPEN(dir, name, mode);')"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-SYS-01"]
    assert len(findings) == 1
    assert "line 9" in findings[0].detail


def test_reserved_word_column(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('HR', 'ACCOUNTS', 'USER', 'VARCHAR2')"
    )
    conn.execute(
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('HR', 'ACCOUNTS', 'USERNAME', 'VARCHAR2')"
    )
    conn.commit()
    assert fired(db, "R-TYPE-05") == ["ACCOUNTS.USER"]


def test_transaction_control_fires_precisely(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'POSTER', 'PROCEDURE', 8, '    COMMIT;')"
    )
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'HARMLESS', 'PROCEDURE', 3,"
        " '  -- transaction COMMITTED elsewhere')"
    )
    conn.commit()
    assert fired(db, "R-SRC-14") == ["POSTER"]


def test_sequence_key_trigger_fires_only_for_triggers(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'TRG_ID', 'TRIGGER', 3,"
        " '  SELECT s.NEXTVAL INTO :NEW.id FROM dual;')"
    )
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'LOADER', 'PROCEDURE', 5, '  v := s.NEXTVAL;')"
    )
    conn.commit()
    assert fired(db, "R-TRG-03") == ["TRG_ID"]


def test_invalid_object_and_opaque_parse(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO objects (owner, name, type, status) VALUES"
        " ('HR', 'DEAD_PKG', 'PACKAGE', 'INVALID')"
    )
    conn.execute(
        "INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality)"
        " VALUES ('HR', 'ODD_TABLE', 'TABLE', 'CREATE ...', 1, 'fallback')"
    )
    conn.commit()
    assert fired(db, "R-OBJ-08") == ["DEAD_PKG"]
    assert fired(db, "R-DDL-02") == ["ODD_TABLE"]


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
    # function-based index, the db-link probe, and the package body
    # with a module-level variable are all in the fixture.
    assert {"R-PART-01", "R-DDL-01", "R-IDX-02", "R-OBJ-01", "R-PKG-01"} <= ids
    # No compound trigger and no LONG column in the fixture.
    assert "R-TRG-01" not in ids
    assert "R-TYPE-01" not in ids


def test_deep_facts_suppress_comment_matches(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    # The unit parsed clean and produced no sysdate fact, so the
    # SYSDATE sitting in a comment must not become a finding.
    conn, db = inventory
    for line, text in enumerate(
        ["PROCEDURE p IS", "  -- runs at SYSDATE", "BEGIN", "  NULL;", "END;"],
        start=1,
    ):
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'P_CLEAN', 'PROCEDURE', ?, ?)",
            (line, text),
        )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_CLEAN', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.commit()
    assert fired(db, "R-SRC-11") == []


def test_grep_fallback_covers_unparsed_units(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    # One unit failed the deep parse, one predates it entirely; both
    # keep token-level coverage.
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'P_BROKEN', 'PROCEDURE', 3, '  v := SYSDATE;')"
    )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_BROKEN', 'PROCEDURE', 'll', 2, 'line 1:0 boom')"
    )
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'P_LEGACY', 'PROCEDURE', 7, '  v := SYSDATE;')"
    )
    conn.commit()
    assert fired(db, "R-SRC-11") == ["P_BROKEN", "P_LEGACY"]


def test_deep_fact_becomes_finding(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'PKG_JOBS', 'PACKAGE BODY', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_features (owner, name, type, feature, line, detail)"
        " VALUES ('HR', 'PKG_JOBS', 'PACKAGE BODY', 'forall', 41, NULL)"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-SRC-15"]
    assert [f.name for f in findings] == ["PKG_JOBS"]
    assert "line 41" in findings[0].detail


def test_optimizer_hint_fires(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'P_TUNED', 'PROCEDURE', 12,"
        " '  SELECT /*+ INDEX(e emp_ix) */ id INTO v FROM emp e;')"
    )
    conn.commit()
    assert fired(db, "R-PERF-01") == ["P_TUNED"]


def test_pre_deep_parse_inventory_still_reports(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    # An inventory loaded before the deep parse existed has no fact
    # tables at all; the engine shims them and the greps carry on.
    conn, db = inventory
    conn.execute("DROP TABLE plsql_units")
    conn.execute("DROP TABLE plsql_features")
    conn.execute("DROP TABLE plsql_calls")
    conn.execute("DROP TABLE part_indexes")
    conn.execute("DROP TABLE mviews")
    conn.execute("DROP TABLE plan_management")
    conn.execute("ALTER TABLE tables DROP COLUMN degree")
    conn.execute("ALTER TABLE indexes DROP COLUMN degree")
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'OLD_PROC', 'PROCEDURE', 2, '  v := SYSDATE;')"
    )
    conn.commit()
    assert fired(db, "R-SRC-11") == ["OLD_PROC"]


def test_sys_package_in_comment_suppressed_by_call_graph(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'P_TIDY', 'PROCEDURE', 4, '  -- UTL_FILE.FOPEN retired')"
    )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_TIDY', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.commit()
    assert fired(db, "R-SYS-01") == []


def test_sys_package_call_fact_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_FILES', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_calls (owner, name, type, callee, line) VALUES"
        " ('HR', 'P_FILES', 'PROCEDURE', 'UTL_FILE.FOPEN', 11)"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-SYS-01"]
    assert [f.name for f in findings] == ["P_FILES"]
    assert "line 11" in findings[0].detail


def test_empty_string_fact_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
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
    findings = [f for f in run_rules(db) if f.rule_id == "R-SRC-18"]
    assert [f.name for f in findings] == ["P_BLANKS"]
    assert "line 6" in findings[0].detail


def test_rowid_and_bfile_columns_fire(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    for column, data_type in [
        ("REF_ADDR", "ROWID"),
        ("U_ADDR", "UROWID"),
        ("SCAN_DOC", "BFILE"),
        ("NAME", "VARCHAR2"),
    ]:
        conn.execute(
            "INSERT INTO columns (owner, table_name, column_name, data_type)"
            " VALUES ('HR', 'LEGACY_REFS', ?, ?)",
            (column, data_type),
        )
    conn.commit()
    assert fired(db, "R-TYPE-06") == ["LEGACY_REFS.REF_ADDR", "LEGACY_REFS.U_ADDR"]
    assert fired(db, "R-TYPE-07") == ["LEGACY_REFS.SCAN_DOC"]


def test_rowid_code_fact_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_BYRID', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_features (owner, name, type, feature, line, detail)"
        " VALUES ('HR', 'P_BYRID', 'PROCEDURE', 'rowid', 14, NULL)"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-SRC-19"]
    assert [f.name for f in findings] == ["P_BYRID"]
    assert "line 14" in findings[0].detail


def test_global_partitioned_index_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO part_tables (owner, table_name, partitioning_type)"
        " VALUES ('HR', 'SALES', 'RANGE')"
    )
    conn.execute(
        "INSERT INTO part_indexes (owner, index_name, table_name, locality)"
        " VALUES ('HR', 'SALES_GPI', 'SALES', 'GLOBAL')"
    )
    conn.execute(
        "INSERT INTO part_indexes (owner, index_name, table_name, locality)"
        " VALUES ('HR', 'SALES_LIX', 'SALES', 'LOCAL')"
    )
    conn.execute(
        "INSERT INTO indexes (owner, index_name, table_name, generated)"
        " VALUES ('HR', 'PK_SALES', 'SALES', 'N')"
    )
    conn.execute(
        "INSERT INTO indexes (owner, index_name, table_name, generated)"
        " VALUES ('HR', 'SALES_LIX', 'SALES', 'N')"
    )
    conn.commit()
    assert fired(db, "R-PERF-02") == ["PK_SALES", "SALES_GPI"]


def test_parallel_degree_fires_on_real_settings_only(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    for name, degree in [("T_PAR", "4"), ("T_DEF", "DEFAULT"), ("T_SER", "1")]:
        conn.execute(
            "INSERT INTO tables (owner, table_name, degree) VALUES ('HR', ?, ?)",
            (name, degree),
        )
    conn.execute(
        "INSERT INTO indexes (owner, index_name, degree) VALUES"
        " ('HR', 'IX_PAR', '   8')"
    )
    conn.commit()
    assert fired(db, "R-PERF-03") == ["IX_PAR", "T_DEF", "T_PAR"]


def test_plan_management_aggregates_per_kind(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    for kind, name in [
        ("BASELINE", "SQL_PLAN_1"),
        ("BASELINE", "SQL_PLAN_2"),
        ("OUTLINE", "OL_ORDERS"),
    ]:
        conn.execute(
            "INSERT INTO plan_management (kind, name, enabled) VALUES (?, ?, 'YES')",
            (kind, name),
        )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-PERF-04"]
    assert [f.name for f in findings] == ["BASELINE", "OUTLINE"]
    assert "2 pinned plan(s)" in findings[0].detail


def test_query_rewrite_mview_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO mviews (owner, mview_name, rewrite_enabled, refresh_method)"
        " VALUES ('HR', 'MV_HOT', 'Y', 'FORCE')"
    )
    conn.execute(
        "INSERT INTO mviews (owner, mview_name, rewrite_enabled, refresh_method)"
        " VALUES ('HR', 'MV_PLAIN', 'N', 'COMPLETE')"
    )
    conn.commit()
    assert fired(db, "R-PERF-05") == ["MV_HOT"]

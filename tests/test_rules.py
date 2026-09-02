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


def test_conditional_compilation_fires_from_feature_and_fallback(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'PKG_CC', 'PACKAGE BODY', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_features (owner, name, type, feature, line, detail)"
        " VALUES ('HR', 'PKG_CC', 'PACKAGE BODY', 'conditional_compilation',"
        " 12, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'PKG_CC_BROKEN', 'PACKAGE BODY', 'll', 3, 'boom')"
    )
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'PKG_CC_BROKEN', 'PACKAGE BODY', 4,"
        " '$IF dbms_db_version.ver_le_11 $THEN')"
    )
    conn.commit()
    assert fired(db, "R-SRC-21") == ["PKG_CC", "PKG_CC_BROKEN"]


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


def test_raise_application_error_reads_call_graph(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'P_CALM', 'PROCEDURE', 3, '  -- RAISE_APPLICATION_ERROR docs')"
    )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_CALM', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'P_LOUD', 'PROCEDURE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_calls (owner, name, type, callee, line) VALUES"
        " ('HR', 'P_LOUD', 'PROCEDURE', 'RAISE_APPLICATION_ERROR', 9)"
    )
    conn.commit()
    assert fired(db, "R-SRC-13") == ["P_LOUD"]


def test_evolved_type_fires_from_feature(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('OE', 'CATEGORY_T', 'TYPE', 'sll', 0, NULL)"
    )
    conn.execute(
        "INSERT INTO plsql_features (owner, name, type, feature, line, detail)"
        " VALUES ('OE', 'CATEGORY_T', 'TYPE', 'type_evolution', 5, NULL)"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-OBJ-09"]
    assert [f.name for f in findings] == ["CATEGORY_T"]
    assert "line 5" in findings[0].detail


def test_wrapped_unit_fires_its_own_rule(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO plsql_units"
        " (owner, name, type, parse_mode, error_count, first_error)"
        " VALUES ('HR', 'SECRET_PKG', 'PACKAGE BODY', 'wrapped', 0, NULL)"
    )
    conn.commit()
    findings = [f for f in run_rules(db) if f.rule_id == "R-SRC-20"]
    assert [f.name for f in findings] == ["SECRET_PKG"]


def test_null_generated_index_still_fires(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    # ALL_INDEXES.GENERATED can arrive NULL from a partial dump;
    # generated <> 'Y' evaluates to NULL and silently dropped the
    # finding until COALESCE fixed it.
    conn, db = inventory
    for name, generated in [("FBI_A", "N"), ("FBI_B", None)]:
        conn.execute(
            "INSERT INTO indexes (owner, index_name, table_name, index_type,"
            " generated) VALUES ('HR', ?, 'EMP', 'FUNCTION-BASED NORMAL', ?)",
            (name, generated),
        )
        conn.execute(
            "INSERT INTO index_expressions (owner, index_name, position,"
            " expression) VALUES ('HR', ?, 1, 'UPPER(name)')",
            (name,),
        )
    conn.commit()
    assert sorted(fired(db, "R-IDX-02")) == ["FBI_A", "FBI_B"]


def test_gap_pack_rules_fire(inventory: tuple[sqlite3.Connection, Path]) -> None:
    conn, db = inventory
    # Unparsed source exercises every grep fallback half.
    for line, text in enumerate(
        [
            "PROCEDURE gap_zoo IS BEGIN",
            "  SELECT 1 FROM t MODEL DIMENSION BY (x) MEASURES (y) RULES ();",
            "  SELECT * FROM sales PIVOT (SUM(amt) FOR y IN (1));",
            "  SELECT * FROM emp AS OF TIMESTAMP SYSTIMESTAMP - 1;",
            "  INSERT ALL INTO a VALUES (1) SELECT 1 FROM dual;",
            "  WITH FUNCTION f RETURN NUMBER IS BEGIN RETURN 1; END;",
            "  SELECT sql_macro_thing FROM dual; -- SQL_MACRO annotation",
            "END;",
        ],
        start=1,
    ):
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text)"
            " VALUES ('HR', 'GAP_ZOO', 'PROCEDURE', ?, ?)",
            (line, text),
        )
    conn.executemany(
        "INSERT INTO ddl (owner, name, type, ddl, parse_ok) VALUES (?, ?, ?, ?, 1)",
        [
            (
                "HR",
                "T_HIDDEN",
                "TABLE",
                'CREATE TABLE "HR"."T_HIDDEN" ("ID" NUMBER,'
                ' "SECRET" VARCHAR2(10) INVISIBLE)',
            ),
            (
                "HR",
                "T_FROZEN",
                "TABLE",
                'CREATE TABLE "HR"."T_FROZEN" ("ID" NUMBER) READ ONLY',
            ),
            (
                "HR",
                "T_DEFN",
                "TABLE",
                'CREATE TABLE "HR"."T_DEFN" ("ID" NUMBER,'
                " \"KIND\" VARCHAR2(4) DEFAULT ON NULL 'STD')",
            ),
        ],
    )
    conn.execute("INSERT INTO tables (owner, table_name) VALUES ('HR', 'MLOG$_ORDERS')")
    conn.commit()
    assert fired(db, "R-SRC-22") == ["GAP_ZOO"]
    assert fired(db, "R-SRC-23") == ["GAP_ZOO"]
    assert fired(db, "R-SRC-24") == ["GAP_ZOO"]
    assert fired(db, "R-SRC-25") == ["GAP_ZOO"]
    assert fired(db, "R-SRC-26") == ["GAP_ZOO"]
    assert fired(db, "R-SRC-27") == ["GAP_ZOO"]
    assert fired(db, "R-TAB-04") == ["T_HIDDEN"]
    assert fired(db, "R-TAB-05") == ["T_FROZEN"]
    assert fired(db, "R-TAB-06") == ["T_DEFN"]
    assert fired(db, "R-OBJ-10") == ["MLOG$_ORDERS"]


def test_charset_rule_fires_off_utf8_only(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.execute(
        "INSERT INTO nls_params (key, value) VALUES"
        " ('NLS_CHARACTERSET', 'WE8MSWIN1252')"
    )
    conn.commit()
    assert fired(db, "R-ENV-01") == ["WE8MSWIN1252"]
    conn.execute(
        "UPDATE nls_params SET value = 'AL32UTF8' WHERE key = 'NLS_CHARACTERSET'"
    )
    conn.commit()
    assert fired(db, "R-ENV-01") == []


def test_grants_rule_counts_per_grantee(
    inventory: tuple[sqlite3.Connection, Path],
) -> None:
    conn, db = inventory
    conn.executemany(
        "INSERT INTO grants (grantee, owner, table_name, privilege, grantable)"
        " VALUES (?, 'HR', ?, ?, 'NO')",
        [
            ("APP_RO", "EMP", "SELECT"),
            ("APP_RO", "DEPT", "SELECT"),
            ("APP_RW", "EMP", "UPDATE"),
        ],
    )
    conn.commit()
    assert sorted(fired(db, "R-ENV-02")) == ["APP_RO", "APP_RW"]


# Every rule ships with a fixture test; these fifteen were exercised
# nowhere - not referenced in the suite and silent on the bundled
# dump - so a detector regression in any of them would have shipped
# unnoticed. Minimal inventories, one per rule.
_RULE_FIXTURES = {
    "R-IDX-01": (
        "INSERT INTO indexes (owner, index_name, table_name, index_type)"
        " VALUES ('HR', 'BM_IX', 'SALES', 'BITMAP')"
    ),
    "R-IDX-03": (
        "INSERT INTO indexes (owner, index_name, table_name, index_type)"
        " VALUES ('HR', 'TXT_IX', 'DOCS', 'DOMAIN')"
    ),
    "R-OBJ-04": (
        "INSERT INTO features (feature, detail, count) VALUES ('queues', 'AQ', 2)"
    ),
    "R-OBJ-07": (
        "INSERT INTO features (feature, detail, count)"
        " VALUES ('vpd_policies', 'ALL_POLICIES', 1)"
    ),
    "R-PART-02": (
        "INSERT INTO part_tables (owner, table_name, partitioning_type,"
        " subpartitioning_type, partition_count, interval)"
        " VALUES ('HR', 'SALES', 'RANGE', 'NONE', 4, NULL)"
    ),
    "R-SRC-06": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'OPEN_IT', 'PROCEDURE', 1, 'l_cur SYS_REFCURSOR;')"
    ),
    "R-SRC-08": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'TOP_N', 'PROCEDURE', 1,"
        " 'SELECT id INTO l_id FROM emp WHERE ROWNUM < 10;')"
    ),
    "R-SRC-09": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'UPSERT', 'PROCEDURE', 1,"
        " 'MERGE INTO t USING s ON (t.id = s.id)')"
    ),
    "R-SRC-10": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'FLAGS', 'FUNCTION', 1, 'RETURN DECODE(p, 1, ''Y'', ''N'');')"
    ),
    "R-SRC-12": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'COUNTS', 'PROCEDURE', 1,"
        " 'IF SQL%ROWCOUNT > 0 THEN NULL; END IF;')"
    ),
    "R-SRC-17": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'STREAM_IT', 'FUNCTION', 1,"
        " 'FUNCTION stream_it RETURN t_tab PIPELINED IS')"
    ),
    "R-SYS-02": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'CALL_OUT', 'PROCEDURE', 1,"
        " 'l_resp := UTL_HTTP.REQUEST(''http://example.com'');')"
    ),
    "R-SYS-03": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'DYN_RUN', 'PROCEDURE', 1,"
        " 'DBMS_SQL.PARSE(l_cur, l_sql, DBMS_SQL.NATIVE);')"
    ),
    "R-TAB-02": (
        "INSERT INTO features (feature, detail, count) VALUES ('iot_tables', 'IOT', 1)"
    ),
    "R-TAB-03": (
        "INSERT INTO features (feature, detail, count)"
        " VALUES ('external_tables', 'EXT', 1)"
    ),
    "R-TYPE-08": (
        "INSERT INTO columns (owner, table_name, column_name, data_type)"
        " VALUES ('GIS', 'PARCELS', 'SHAPE', 'SDO_GEOMETRY')"
    ),
    "R-SRC-28": (
        "INSERT INTO source (owner, name, type, line, text) VALUES"
        " ('HR', 'WHO_AM_I', 'FUNCTION', 1,"
        " 'RETURN SYS_CONTEXT(''USERENV'', ''SESSION_USER'');')"
    ),
    "R-OBJ-11": (
        "INSERT INTO plsql_calls (owner, name, type, callee, line) VALUES"
        " ('HR', 'SYNC_IT', 'PROCEDURE', 'REMOTE_PKG.LOG_IT@SALES_LINK', 7)"
    ),
    "R-TYPE-09": (
        "INSERT INTO columns (owner, table_name, column_name, data_type, data_length,"
        " char_length, char_used) VALUES ('HR', 'T', 'NAME', 'VARCHAR2', 30, 30, 'B');"
        " INSERT INTO nls_params (key, value) VALUES ('NLS_CHARACTERSET', 'AL32UTF8')"
    ),
}


@pytest.mark.parametrize("rule_id", sorted(_RULE_FIXTURES))
def test_rule_fires_on_minimal_inventory(
    inventory: tuple[sqlite3.Connection, Path], rule_id: str
) -> None:
    conn, db = inventory
    conn.executescript(_RULE_FIXTURES[rule_id])
    conn.commit()
    assert fired(db, rule_id), rule_id


def test_bundled_dump_headline_numbers(tmp_path: Path) -> None:
    # The README quotes these exact numbers; nothing else asserted
    # them, so they could drift silently between releases. The dump
    # is regenerated by the Oracle-loop CI job; re-pin when it changes.
    db = tmp_path / "sample.db"
    load_dump(Path("examples/dump_oracle21c"), db)
    summary = summarize(run_rules(db))
    assert summary["findings"] == 58
    assert round(summary["effort_points"], 1) == 77.7
    assert summary["by_severity"]["high"] == 10

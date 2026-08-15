from pgrecon.plsql.walk import analyze_source


def test_comments_and_strings_produce_no_features() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  -- scheduled at SYSDATE, uses DECODE( and COMMIT;\n"
        "  v VARCHAR2(60) := 'SYSDATE DECODE( COMMIT; ROWNUM';\n"
        "BEGIN\n"
        "  v := TO_CHAR(SYSDATE);\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    assert [(f.feature, f.line) for f in analysis.features] == [("sysdate", 5)]


def test_statement_features_are_collected() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  PRAGMA AUTONOMOUS_TRANSACTION;\n"
        "  TYPE t_ids IS TABLE OF NUMBER;\n"
        "BEGIN\n"
        "  EXECUTE IMMEDIATE 'TRUNCATE TABLE stage';\n"
        "  FORALL i IN 1 .. 10\n"
        "    INSERT INTO t VALUES (i);\n"
        "  IF SQL%ROWCOUNT > 0 THEN\n"
        "    COMMIT;\n"
        "  END IF;\n"
        "EXCEPTION\n"
        "  WHEN OTHERS THEN NULL;\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    found = {f.feature for f in analysis.features}
    assert {
        "autonomous_transaction",
        "collection_type",
        "execute_immediate",
        "forall",
        "sql_cursor_attribute",
        "commit",
        "when_others_null",
    } <= found


def test_collection_kinds_are_distinguished() -> None:
    unit = (
        "PACKAGE p IS\n"
        "  TYPE t_tab IS TABLE OF NUMBER;\n"
        "  TYPE t_map IS TABLE OF NUMBER INDEX BY VARCHAR2(30);\n"
        "  TYPE t_arr IS VARRAY(10) OF NUMBER;\n"
        "END p;"
    )
    analysis = analyze_source(unit)
    kinds = sorted(
        f.detail for f in analysis.features if f.feature == "collection_type"
    )
    assert kinds == ["associative array", "nested table", "varray"]


def test_named_cursor_attribute_is_not_flagged() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  CURSOR c IS SELECT 1 FROM dual;\n"
        "BEGIN\n"
        "  OPEN c;\n"
        "  IF c%ISOPEN THEN\n"
        "    CLOSE c;\n"
        "  END IF;\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    assert all(f.feature != "sql_cursor_attribute" for f in analysis.features)


def test_when_others_with_real_handler_is_not_flagged() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "BEGIN\n"
        "  NULL;\n"
        "EXCEPTION\n"
        "  WHEN OTHERS THEN\n"
        "    RAISE;\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert all(f.feature != "when_others_null" for f in analysis.features)


def test_unparseable_unit_yields_no_features() -> None:
    analysis = analyze_source("PACKAGE broken AS PROCEDURE ((( END")
    assert analysis.errors
    assert analysis.features == ()


def test_call_sites_are_collected() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  l_out UTL_FILE.FILE_TYPE;\n"
        "  v NUMBER;\n"
        "BEGIN\n"
        "  l_out := UTL_FILE.FOPEN('DIR', 'x.log', 'w');\n"
        "  v := pay_pkg.net_amount(pay_pkg.gross(101));\n"
        "  DBMS_OUTPUT.NEW_LINE;\n"
        "  log_it('done');\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    callees = {c.callee for c in analysis.calls}
    assert {
        "UTL_FILE.FOPEN",
        "PAY_PKG.NET_AMOUNT",
        "PAY_PKG.GROSS",
        "DBMS_OUTPUT.NEW_LINE",
        "LOG_IT",
    } <= callees


def test_variable_references_are_not_calls() -> None:
    unit = (
        "PROCEDURE p IS\n  g_total NUMBER := 0;\nBEGIN\n  g_total := g_total + 1;\nEND;"
    )
    analysis = analyze_source(unit)
    assert all(c.callee != "G_TOTAL" for c in analysis.calls)


def test_package_named_in_comment_is_not_a_call() -> None:
    unit = (
        "PROCEDURE p IS\nBEGIN\n  -- UTL_FILE.FOPEN would be wrong here\n  NULL;\nEND;"
    )
    analysis = analyze_source(unit)
    assert analysis.calls == ()


def test_empty_string_literal_is_flagged() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  v VARCHAR2(10);\n"
        "BEGIN\n"
        "  v := '';\n"
        "  IF v = '' THEN\n"
        "    NULL;\n"
        "  END IF;\n"
        "END;"
    )
    analysis = analyze_source(unit)
    lines = [f.line for f in analysis.features if f.feature == "empty_string_literal"]
    assert lines == [4, 5]


def test_escaped_quote_inside_string_is_not_empty() -> None:
    # 'don''t' carries two consecutive quote characters, which is an
    # escaped quote, not an empty-string literal; text matching cannot
    # tell these apart, the lexer can.
    unit = "PROCEDURE p IS\n  v VARCHAR2(10) := 'don''t';\nBEGIN\n  NULL;\nEND;"
    analysis = analyze_source(unit)
    assert all(f.feature != "empty_string_literal" for f in analysis.features)


def test_rowid_usage_is_flagged() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "  l_rid ROWID;\n"
        "BEGIN\n"
        "  SELECT rowid INTO l_rid FROM emp WHERE id = 1;\n"
        "  DELETE FROM emp WHERE rowid = l_rid;\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    lines = [f.line for f in analysis.features if f.feature == "rowid"]
    assert lines == [2, 4, 5]


def test_merge_statement_is_flagged() -> None:
    unit = (
        "PROCEDURE p IS\n"
        "BEGIN\n"
        "  MERGE INTO tgt t USING src s ON (t.id = s.id)\n"
        "  WHEN MATCHED THEN UPDATE SET t.v = s.v\n"
        "  WHEN NOT MATCHED THEN INSERT (id, v) VALUES (s.id, s.v);\n"
        "END;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    assert [f.line for f in analysis.features if f.feature == "merge"] == [3]


def test_ref_cursor_declarations_are_flagged() -> None:
    unit = (
        "PACKAGE p AS\n"
        "  -- REF CURSOR mentioned in prose only\n"
        "  TYPE t_cur IS REF CURSOR;\n"
        "  FUNCTION open_it RETURN SYS_REFCURSOR;\n"
        "END p;"
    )
    analysis = analyze_source(unit)
    assert analysis.errors == ()
    assert [f.line for f in analysis.features if f.feature == "ref_cursor"] == [3, 4]


def test_evolved_type_parses_past_its_alter_tail() -> None:
    # DBA_SOURCE for an evolved type carries the CREATE followed by
    # the ALTER TYPE statements that changed it, in one listing.
    unit = (
        "TYPE category_t AS OBJECT\n"
        "  (category_id NUMBER(2),\n"
        "   category_name VARCHAR2(50))\n"
        "  NOT INSTANTIABLE NOT FINAL\n"
        "ALTER TYPE category_t\n"
        " ADD ATTRIBUTE (parent_id NUMBER(2)) CASCADE\n"
    )
    analysis = analyze_source(unit, "TYPE")
    assert analysis.errors == ()
    evolution = [f for f in analysis.features if f.feature == "type_evolution"]
    assert [f.line for f in evolution] == [5]


def test_unevolved_type_gains_no_evolution_feature() -> None:
    unit = "TYPE money_t AS OBJECT (amount NUMBER, currency VARCHAR2(3))"
    analysis = analyze_source(unit, "TYPE")
    assert analysis.errors == ()
    assert all(f.feature != "type_evolution" for f in analysis.features)

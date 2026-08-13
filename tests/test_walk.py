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

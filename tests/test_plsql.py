from pgrecon.plsql import parse_source, parse_unit


def test_package_spec_parses_in_sll_mode() -> None:
    result = parse_source(
        "PACKAGE pkg_ledger AS\n"
        "  g_rate NUMBER := 0.19;\n"
        "  PROCEDURE post(p_amount IN NUMBER);\n"
        "END pkg_ledger;"
    )
    assert result.errors == ()
    assert result.mode == "sll"
    assert result.tree is not None


def test_trigger_with_autonomous_transaction_parses() -> None:
    result = parse_source(
        "TRIGGER trg_audit AFTER UPDATE ON emp FOR EACH ROW\n"
        "DECLARE\n"
        "  PRAGMA AUTONOMOUS_TRANSACTION;\n"
        "BEGIN\n"
        "  INSERT INTO audit_log VALUES (:new.id, SYSDATE);\n"
        "  COMMIT;\n"
        "END;"
    )
    assert result.errors == ()
    assert result.tree is not None


def test_broken_source_reports_errors_without_raising() -> None:
    # SLL bails on the unroutable token, the LL retry records the
    # error, and nothing raises: an unparseable unit is data.
    result = parse_source("PACKAGE broken AS PROCEDURE ((( END")
    assert result.errors
    assert result.mode == "ll"
    assert result.errors[0].startswith("line ")


def test_plain_ddl_statement_parses() -> None:
    result = parse_unit("CREATE TABLE t (id NUMBER PRIMARY KEY, name VARCHAR2(40))")
    assert result.errors == ()

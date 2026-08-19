"""Trigger conversion: paired trigger functions and honest refusals."""

from pathlib import Path

import pytest

from pgrecon.convert import convert_schema
from pgrecon.inventory import open_db
from pgrecon.inventory.loader import _analyze_plsql

TRG_STAMP = """TRIGGER trg_stamp
BEFORE INSERT OR UPDATE ON t_fees
FOR EACH ROW
WHEN (new.fee > 0)
DECLARE
  v_tag VARCHAR2(10);
BEGIN
  IF INSERTING THEN
    :NEW.tag := 'ins';
  END IF;
  IF UPDATING THEN
    RETURN;
  END IF;
  :NEW.fee := NVL(:NEW.fee, 0);
END;"""

TRG_SEQ = """TRIGGER trg_seq
BEFORE INSERT ON t_fees
FOR EACH ROW
BEGIN
  :NEW.fee := ref_seq.NEXTVAL;
END;"""

TRG_STMT = """TRIGGER trg_stmt
AFTER INSERT ON t_fees
BEGIN
  INSERT INTO audit_log (audit_id) VALUES (1);
END;"""

TRG_UPDOF = """TRIGGER trg_updof
BEFORE UPDATE OF fee ON t_fees
FOR EACH ROW
BEGIN
  :NEW.tag := 'u';
END;"""

TRG_BAD = """TRIGGER trg_bad
BEFORE UPDATE ON t_fees
FOR EACH ROW
BEGIN
  IF UPDATING('fee') THEN
    :NEW.tag := 'x';
  END IF;
END;"""

TRG_DIS = """TRIGGER trg_dis
BEFORE INSERT ON t_fees
FOR EACH ROW
BEGIN
  :NEW.tag := 'd';
END;"""

TRG_WHENDEL = """TRIGGER trg_whendel
AFTER INSERT OR UPDATE OR DELETE ON t_fees
FOR EACH ROW
WHEN (new.fee > 0)
BEGIN
  DBMS_OUTPUT.PUT_LINE('fee: ' || :NEW.fee);
END;"""

_TRIGGERS = [
    ("TRG_STAMP", "BEFORE EACH ROW", "INSERT OR UPDATE", "ENABLED", TRG_STAMP),
    ("TRG_SEQ", "BEFORE EACH ROW", "INSERT", "ENABLED", TRG_SEQ),
    ("TRG_STMT", "AFTER STATEMENT", "INSERT", "ENABLED", TRG_STMT),
    ("TRG_UPDOF", "BEFORE EACH ROW", "UPDATE", "ENABLED", TRG_UPDOF),
    ("TRG_BAD", "BEFORE EACH ROW", "UPDATE", "ENABLED", TRG_BAD),
    ("TRG_DIS", "BEFORE EACH ROW", "INSERT", "DISABLED", TRG_DIS),
    (
        "TRG_WHENDEL",
        "AFTER EACH ROW",
        "INSERT OR UPDATE OR DELETE",
        "ENABLED",
        TRG_WHENDEL,
    ),
]


@pytest.fixture
def trigger_db(tmp_path: Path) -> Path:
    db = tmp_path / "triggers.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO objects VALUES ('AX', 'T_FEES', 'TABLE', 'VALID', NULL, NULL);
        INSERT INTO objects VALUES ('AX', 'AUDIT_LOG', 'TABLE', 'VALID', NULL, NULL);
        INSERT INTO tables (owner, table_name) VALUES ('AX', 'T_FEES');
        INSERT INTO tables (owner, table_name) VALUES ('AX', 'AUDIT_LOG');
        INSERT INTO columns VALUES
            ('AX', 'T_FEES', 'FEE', 1, 'NUMBER', 22, 10, 2, 'Y'),
            ('AX', 'T_FEES', 'TAG', 2, 'VARCHAR2', 30, NULL, NULL, 'Y'),
            ('AX', 'AUDIT_LOG', 'AUDIT_ID', 1, 'NUMBER', 22, 10, 0, 'Y');
        INSERT INTO sequences VALUES
            ('AX', 'REF_SEQ', '1', '9999999', '1', 'N', '20', '41');
        INSERT INTO triggers VALUES
            ('AX', 'TRG_COMP', 'COMPOUND', 'INSERT', 'T_FEES', 'ENABLED');
        """
    )
    for name, ttype, event, status, text in _TRIGGERS:
        conn.execute(
            "INSERT INTO triggers VALUES ('AX', ?, ?, ?, 'T_FEES', ?)",
            (name, ttype, event, status),
        )
        conn.execute(
            "INSERT INTO objects (owner, name, type, status)"
            " VALUES ('AX', ?, 'TRIGGER', 'VALID')",
            (name,),
        )
        for i, line in enumerate(text.splitlines(keepends=True), start=1):
            conn.execute(
                "INSERT INTO source (owner, name, type, line, text)"
                " VALUES ('AX', ?, 'TRIGGER', ?, ?)",
                (name, i, line),
            )
    _analyze_plsql(conn)
    conn.commit()
    conn.close()
    return db


def _reason(result, name: str) -> str:
    matches = [
        r.reason
        for r in result.residue
        if r.object_name == name and r.kind == "trigger"
    ]
    assert matches, f"no trigger residue for {name}"
    return matches[0]


def test_row_trigger_pairs_function_and_trigger(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    sql = result.sql
    assert "CREATE OR REPLACE FUNCTION trg_stamp_fn() RETURNS trigger" in sql
    assert "(TG_OP = 'INSERT')" in sql
    assert "NEW.tag := 'ins';" in sql
    assert "COALESCE(NEW.fee, 0)" in sql
    assert ":NEW" not in sql
    assert "RETURN COALESCE(NEW, OLD);" in sql
    assert "CREATE TRIGGER trg_stamp BEFORE insert OR update ON t_fees" in sql
    assert "FOR EACH ROW WHEN (new.fee > 0)" in sql
    assert "EXECUTE FUNCTION trg_stamp_fn();" in sql


def test_bare_return_gains_trigger_result(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    body = result.sql.split("trg_stamp_fn", 2)[1]
    assert body.count("RETURN COALESCE(NEW, OLD);") == 2


def test_sequence_trigger_converts_with_identity_note(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "NEW.fee := nextval('ref_seq');" in result.sql
    notes = [
        r.reason
        for r in result.residue
        if r.object_name == "TRG_SEQ" and r.kind == "note"
    ]
    assert any("identity column" in n for n in notes)


def test_statement_trigger_returns_null(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "CREATE TRIGGER trg_stmt AFTER insert ON t_fees" in result.sql
    assert "FOR EACH STATEMENT" in result.sql
    body = result.sql.split("trg_stmt_fn", 2)[1]
    assert "RETURN NULL;" in body


def test_update_of_column_list_survives(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "CREATE TRIGGER trg_updof BEFORE update of fee ON t_fees" in result.sql


def test_updating_column_predicate_refuses(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "UPDATING('column')" in _reason(result, "TRG_BAD")


def test_compound_trigger_refuses(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "compound" in _reason(result, "TRG_COMP")


def test_disabled_trigger_stays_disabled(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert "ALTER TABLE t_fees DISABLE TRIGGER trg_dis;" in result.sql


def test_new_reference_with_delete_moves_when_into_body(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    section = result.sql.split("trg_whendel_fn", 2)[1]
    assert "IF (new.fee > 0) IS NOT TRUE THEN" in section
    assert "CREATE TRIGGER trg_whendel AFTER insert OR update OR delete" in result.sql
    header = result.sql.split("CREATE TRIGGER trg_whendel", 1)[1].split(";", 1)[0]
    assert "WHEN" not in header


def test_trigger_body_concatenation_null_safe(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    section = result.sql.split("trg_whendel_fn", 2)[1]
    assert "NULLIF(concat('fee: ' , NEW.fee), '')" in section


def test_trigger_count(trigger_db: Path) -> None:
    result = convert_schema(trigger_db)
    assert result.triggers == 6
    assert result.sql.count("RETURNS trigger") == 6

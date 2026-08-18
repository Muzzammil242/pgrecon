"""The code lane: mechanical function/procedure conversion and its refusals."""

import sqlite3
from pathlib import Path

import pytest

from pgrecon.convert import convert_schema
from pgrecon.inventory import open_db
from pgrecon.inventory.loader import _analyze_plsql

FEE_FOR = """FUNCTION fee_for(p_kind IN VARCHAR2, p_rate IN NUMBER := 1.5)
RETURN NUMBER
DETERMINISTIC
IS
  v_fee NUMBER(10,2) := 0;
  v_day DATE;
  v_tag t_fees.tag%TYPE;
  CURSOR c_fees IS SELECT fee FROM t_fees WHERE kind = p_kind;
BEGIN
  SELECT ref_seq.NEXTVAL INTO v_fee FROM DUAL;
  v_tag := NVL(p_kind, q'[it's flat]') || TO_CHAR(SYSDATE, 'YYYY');
  IF INSTR(v_tag, 'x') > 0 THEN
    v_day := SYSDATE;
  END IF;
  DBMS_OUTPUT.PUT_LINE('fee at ' || SYSDATE);
  FOR r IN (SELECT fee FROM t_fees) LOOP
    v_fee := v_fee + r.fee;
  END LOOP;
  RETURN v_fee * p_rate;
EXCEPTION
  WHEN DUP_VAL_ON_INDEX THEN
    RETURN 0;
END fee_for;"""

AUTON_P = """PROCEDURE auton_p IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO t_fees (kind) VALUES ('a');
  COMMIT;
END auton_p;"""

FN_COMMIT = """FUNCTION fn_commit(p NUMBER) RETURN NUMBER IS
BEGIN
  COMMIT;
  RETURN p;
END fn_commit;"""

P_COMMIT = """PROCEDURE p_commit IS
BEGIN
  UPDATE t_fees SET fee = 0 WHERE fee IS NULL;
  COMMIT;
END p_commit;"""

LOB_P = """PROCEDURE lob_p(p CLOB) IS
  v NUMBER;
BEGIN
  v := DBMS_LOB.GETLENGTH(p);
END lob_p;"""

SEQ_MISS = """PROCEDURE seq_miss IS
  v NUMBER;
BEGIN
  SELECT other_seq.NEXTVAL INTO v FROM DUAL;
END seq_miss;"""

EXC_P = """PROCEDURE exc_p IS
  e_bad EXCEPTION;
BEGIN
  RAISE e_bad;
END exc_p;"""

CALLER_P = """PROCEDURE caller_p IS
  v NUMBER;
BEGIN
  v := fn_commit(1);
END caller_p;"""

INSTR3_P = """PROCEDURE instr3_p(p VARCHAR2) IS
  v NUMBER;
BEGIN
  v := INSTR(p, 'x', 2);
END instr3_p;"""

TDATE_P = """PROCEDURE tdate_p(p VARCHAR2) IS
  v DATE;
BEGIN
  v := TO_DATE(p);
END tdate_p;"""

OUT_FN = """FUNCTION out_fn(p OUT NUMBER) RETURN NUMBER IS
BEGIN
  p := 1;
  RETURN p;
END out_fn;"""

INOUT_P = """PROCEDURE inout_p(p IN OUT NUMBER) IS
BEGIN
  p := p + 1;
END inout_p;"""

ROWTYPE_P = """PROCEDURE rowtype_p IS
  CURSOR c1 IS SELECT kind, fee FROM t_fees;
  r c1%ROWTYPE;
BEGIN
  OPEN c1;
  FETCH c1 INTO r;
  CLOSE c1;
END rowtype_p;"""

ROWBAD_P = """PROCEDURE rowbad_p IS
  bad other_tab%ROWTYPE;
BEGIN
  NULL;
END rowbad_p;"""

FETCH_LOOP_P = """PROCEDURE fetch_loop_p IS
  CURSOR c IS SELECT fee FROM t_fees;
  v NUMBER;
BEGIN
  OPEN c;
  LOOP
    FETCH c INTO v;
    EXIT WHEN c%NOTFOUND;
  END LOOP;
  CLOSE c;
END fetch_loop_p;"""

FETCH_GAP_P = """PROCEDURE fetch_gap_p IS
  CURSOR c IS SELECT fee FROM t_fees;
  v NUMBER;
  n NUMBER := 0;
BEGIN
  OPEN c;
  LOOP
    FETCH c INTO v;
    n := n + 1;
    EXIT WHEN c%NOTFOUND;
  END LOOP;
  CLOSE c;
END fetch_gap_p;"""

BINDS_P = """PROCEDURE binds_p(p NUMBER) IS
BEGIN
  EXECUTE IMMEDIATE 'update t_fees set fee = :a where fee < :b'
    USING p, p;
END binds_p;"""

BINDS_LOOSE_P = """PROCEDURE binds_loose_p(p VARCHAR2) IS
  v VARCHAR2(200) := 'delete from t_fees where kind = :k';
BEGIN
  EXECUTE IMMEDIATE v USING p;
END binds_loose_p;"""

BINDS_OUT_P = """PROCEDURE binds_out_p(p IN OUT NUMBER) IS
BEGIN
  EXECUTE IMMEDIATE 'begin :x := 1; end;' USING OUT p;
END binds_out_p;"""

_UNITS = [
    ("FEE_FOR", "FUNCTION", FEE_FOR),
    ("AUTON_P", "PROCEDURE", AUTON_P),
    ("FN_COMMIT", "FUNCTION", FN_COMMIT),
    ("P_COMMIT", "PROCEDURE", P_COMMIT),
    ("LOB_P", "PROCEDURE", LOB_P),
    ("SEQ_MISS", "PROCEDURE", SEQ_MISS),
    ("EXC_P", "PROCEDURE", EXC_P),
    ("CALLER_P", "PROCEDURE", CALLER_P),
    ("INSTR3_P", "PROCEDURE", INSTR3_P),
    ("TDATE_P", "PROCEDURE", TDATE_P),
    ("OUT_FN", "FUNCTION", OUT_FN),
    ("INOUT_P", "PROCEDURE", INOUT_P),
    ("ROWTYPE_P", "PROCEDURE", ROWTYPE_P),
    ("ROWBAD_P", "PROCEDURE", ROWBAD_P),
    ("FETCH_LOOP_P", "PROCEDURE", FETCH_LOOP_P),
    ("FETCH_GAP_P", "PROCEDURE", FETCH_GAP_P),
    ("BINDS_P", "PROCEDURE", BINDS_P),
    ("BINDS_LOOSE_P", "PROCEDURE", BINDS_LOOSE_P),
    ("BINDS_OUT_P", "PROCEDURE", BINDS_OUT_P),
]


def _add_unit(
    conn: sqlite3.Connection, owner: str, name: str, otype: str, text: str
) -> None:
    conn.execute(
        "INSERT INTO objects (owner, name, type, status) VALUES (?, ?, ?, 'VALID')",
        (owner, name, otype),
    )
    for i, line in enumerate(text.splitlines(keepends=True), start=1):
        conn.execute(
            "INSERT INTO source (owner, name, type, line, text) VALUES (?, ?, ?, ?, ?)",
            (owner, name, otype, i, line),
        )


@pytest.fixture
def code_db(tmp_path: Path) -> Path:
    db = tmp_path / "code.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO objects VALUES ('AX', 'T_FEES', 'TABLE', 'VALID', NULL, NULL);
        INSERT INTO objects VALUES ('AX', 'PKG_X', 'PACKAGE', 'VALID', NULL, NULL);
        INSERT INTO objects VALUES ('AX', 'TY_Y', 'TYPE', 'VALID', NULL, NULL);
        INSERT INTO tables (owner, table_name) VALUES ('AX', 'T_FEES');
        INSERT INTO columns VALUES
            ('AX', 'T_FEES', 'KIND', 1, 'VARCHAR2', 30, NULL, NULL, 'Y'),
            ('AX', 'T_FEES', 'FEE', 2, 'NUMBER', 22, 10, 2, 'Y'),
            ('AX', 'T_FEES', 'TAG', 3, 'VARCHAR2', 60, NULL, NULL, 'Y');
        INSERT INTO sequences VALUES
            ('AX', 'REF_SEQ', '1', '9999999', '1', 'N', '20', '41');
        INSERT INTO triggers VALUES
            ('AX', 'TRG_Z', 'BEFORE EACH ROW', 'INSERT', 'T_FEES', 'ENABLED');
        INSERT INTO dependencies VALUES
            ('AX', 'FEE_FOR', 'FUNCTION', 'AX', 'T_FEES', 'TABLE'),
            ('AX', 'FEE_FOR', 'FUNCTION', 'AX', 'REF_SEQ', 'SEQUENCE');
        """
    )
    for name, otype, text in _UNITS:
        _add_unit(conn, "AX", name, otype, text)
    _analyze_plsql(conn)
    conn.commit()
    conn.close()
    return db


def _residue_reason(result, name: str) -> str:
    matches = [r.reason for r in result.residue if r.object_name == name]
    assert matches, f"no residue for {name}"
    return matches[0]


def test_happy_function_converts_mechanically(code_db: Path) -> None:
    result = convert_schema(code_db)
    sql = result.sql
    assert "CREATE OR REPLACE FUNCTION fee_for" in sql
    assert "RETURNS numeric" in sql
    assert "LANGUAGE plpgsql" in sql
    assert "IMMUTABLE" in sql
    assert "COALESCE(p_kind" in sql
    assert "'it''s flat'" in sql
    assert "nextval('ref_seq') INTO STRICT v_fee" in sql
    assert "CURRENT_TIMESTAMP" in sql
    assert "SYSDATE" not in sql
    assert "DUAL" not in sql
    assert "strpos(v_tag" in sql
    assert "RAISE NOTICE '%'," in sql
    assert "c_fees CURSOR" in sql and "CURSOR c_fees" not in sql
    assert "FOR SELECT fee" in sql
    assert "unique_violation" in sql
    assert "DUP_VAL_ON_INDEX" not in sql
    assert "t_fees.tag%TYPE" in sql
    assert "v_day timestamp(0)" in sql
    assert "DEFAULT 1.5" in sql
    assert "END fee_for" not in sql


def test_parameter_modes_translate(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "CREATE OR REPLACE PROCEDURE inout_p(p INOUT  numeric)" in result.sql
    reason = _residue_reason(result, "OUT_FN")
    assert "OUT parameters" in reason


def test_semantic_features_refuse_with_lines(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "auton_p" not in result.sql
    assert "autonomous transaction" in _residue_reason(result, "AUTON_P")
    assert "(line" in _residue_reason(result, "AUTON_P")


def test_commit_splits_by_unit_kind(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "transaction control inside a function" in _residue_reason(
        result, "FN_COMMIT"
    )
    assert "CREATE OR REPLACE PROCEDURE p_commit" in result.sql
    notes = [
        r.reason
        for r in result.residue
        if r.object_name == "P_COMMIT" and r.kind == "note"
    ]
    assert notes and "top-level CALL" in notes[0]


def test_unproven_calls_refuse_by_name(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "DBMS_LOB" in _residue_reason(result, "LOB_P")
    assert "INSTR with position" in _residue_reason(result, "INSTR3_P")
    assert "TO_DATE over a single argument" in _residue_reason(result, "TDATE_P")


def test_unknown_sequence_reference_refuses(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "OTHER_SEQ" in _residue_reason(result, "SEQ_MISS")


def test_user_exception_refuses(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "user-defined exceptions" in _residue_reason(result, "EXC_P")


def test_refusal_cascades_to_callers(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "calls FN_COMMIT, which was not converted" in _residue_reason(
        result, "CALLER_P"
    )


def test_routine_count_matches_emitted(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert result.routines == 7
    assert result.sql.count("LANGUAGE plpgsql") == 7


def test_adjacent_fetch_notfound_translates(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "EXIT WHEN NOT FOUND;" in result.sql
    assert "%NOTFOUND" not in result.sql
    assert "cursor attributes" in _residue_reason(result, "FETCH_GAP_P")


def test_dynamic_binds_fold_only_when_arity_matches(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "fee = $1 where fee < $2" in result.sql
    assert ":a" not in result.sql
    assert ":k" in result.sql
    assert "v varchar(200)" in result.sql
    assert "OUT bind" in _residue_reason(result, "BINDS_OUT_P")


def test_cursor_rowtype_becomes_record(code_db: Path) -> None:
    result = convert_schema(code_db)
    assert "r record;" in result.sql
    reason = _residue_reason(result, "ROWBAD_P")
    assert "OTHER_TAB" in reason and "%ROWTYPE" in reason


def test_packages_triggers_types_land_in_residue(code_db: Path) -> None:
    result = convert_schema(code_db)
    kinds = {r.object_name: r.kind for r in result.residue}
    assert kinds.get("PKG_X") == "package"
    assert kinds.get("TRG_Z") == "trigger"
    assert kinds.get("TY_Y") == "type"
    assert "flattening" in _residue_reason(result, "PKG_X")


def test_format_model_note_surfaces(code_db: Path) -> None:
    result = convert_schema(code_db)
    notes = [
        r.reason
        for r in result.residue
        if r.object_name == "FEE_FOR" and r.kind == "note"
    ]
    assert any("format models" in n for n in notes)

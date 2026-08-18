from pathlib import Path

import pytest

from pgrecon.convert import convert_schema, residue_report
from pgrecon.convert.schema import ident
from pgrecon.convert.typemap import map_type
from pgrecon.inventory import open_db


@pytest.mark.parametrize(
    ("oracle", "args", "expected"),
    [
        ("NUMBER", (None, None, None), "numeric"),
        ("NUMBER", (None, 3, 0), "smallint"),
        ("NUMBER", (None, 9, 0), "integer"),
        ("NUMBER", (None, 15, None), "bigint"),
        ("NUMBER", (None, 25, 0), "numeric(25)"),
        ("NUMBER", (None, 10, 2), "numeric(10,2)"),
        ("VARCHAR2", (100, None, None), "varchar(100)"),
        ("CHAR", (3, None, None), "char(3)"),
        ("CLOB", (None, None, None), "text"),
        ("BLOB", (None, None, None), "bytea"),
        ("RAW", (16, None, None), "bytea"),
        ("DATE", (None, None, None), "timestamp(0)"),
        ("TIMESTAMP(6)", (None, None, None), "timestamp(6)"),
        ("TIMESTAMP(6) WITH TIME ZONE", (None, None, None), "timestamptz(6)"),
        ("TIMESTAMP(3) WITH LOCAL TIME ZONE", (None, None, None), "timestamptz(3)"),
        ("INTERVAL DAY(2) TO SECOND(6)", (None, None, None), "interval"),
        ("XMLTYPE", (None, None, None), "xml"),
        ("BINARY_DOUBLE", (None, None, None), "double precision"),
        ("FLOAT", (None, 126, None), "double precision"),
        ("LONG", (None, None, None), "text"),
    ],
)
def test_type_mapping(
    oracle: str, args: tuple[int | None, int | None, int | None], expected: str
) -> None:
    assert map_type(oracle, *args).pg_type == expected


@pytest.mark.parametrize(
    "oracle", ["ROWID", "UROWID", "BFILE", "SDO_GEOMETRY", "T_MONEY"]
)
def test_unmappable_types_return_none_with_reason(oracle: str) -> None:
    mapped = map_type(oracle, None, None, None)
    assert mapped.pg_type is None
    assert mapped.note


def test_identifiers_fold_or_quote() -> None:
    assert ident("EMPLOYEES") == "employees"
    assert ident("ORDER") == '"ORDER"'
    assert ident("Weird Name") == '"Weird Name"'
    assert ident("T_1") == "t_1"


@pytest.fixture()
def facts_db(tmp_path: Path) -> Path:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'DEPT', 'N'), ('HR', 'EMP', 'N'), ('HR', 'SCANS', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'DEPT', 'DEPT_ID',  1, 'NUMBER',   22, 4,  0, 'N'),
          ('HR', 'DEPT', 'NAME',     2, 'VARCHAR2', 50, NULL, NULL, 'N'),
          ('HR', 'EMP',  'EMP_ID',   1, 'NUMBER',   22, 10, 0, 'N'),
          ('HR', 'EMP',  'DEPT_ID',  2, 'NUMBER',   22, 4,  0, 'Y'),
          ('HR', 'EMP',  'HIRED',    3, 'DATE',     7,  NULL, NULL, 'Y'),
          ('HR', 'EMP',  'SALARY',   4, 'NUMBER',   22, 8,  2, 'Y'),
          ('HR', 'SCANS', 'SCAN_ID', 1, 'NUMBER',   22, 10, 0, 'N'),
          ('HR', 'SCANS', 'DOC',     2, 'BFILE',    530, NULL, NULL, 'Y');
        INSERT INTO constraints
          (owner, constraint_name, table_name, type, ref_owner,
           ref_constraint, delete_rule) VALUES
          ('HR', 'DEPT_PK', 'DEPT', 'P', NULL, NULL, NULL),
          ('HR', 'EMP_PK',  'EMP',  'P', NULL, NULL, NULL),
          ('HR', 'EMP_DEPT_FK', 'EMP', 'R', 'HR', 'DEPT_PK', 'SET NULL'),
          ('HR', 'EMP_SAL_CK', 'EMP', 'C', NULL, NULL, NULL),
          ('HR', 'EMP_ID_NN', 'EMP', 'C', NULL, NULL, NULL);
        INSERT INTO constraint_columns
          (owner, constraint_name, column_name, position) VALUES
          ('HR', 'DEPT_PK', 'DEPT_ID', 1),
          ('HR', 'EMP_PK', 'EMP_ID', 1),
          ('HR', 'EMP_DEPT_FK', 'DEPT_ID', 1);
        INSERT INTO check_conditions (owner, constraint_name, condition, truncated)
          VALUES ('HR', 'EMP_SAL_CK', 'SALARY > 0', 0),
                 ('HR', 'EMP_ID_NN', '"EMP_ID" IS NOT NULL', 0);
        """
    )
    conn.commit()
    conn.close()
    return db


def test_schema_conversion_emits_tables_and_constraints(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE TABLE dept (" in sql
    assert "dept_id smallint NOT NULL" in sql
    assert "hired timestamp(0)" in sql
    assert "salary numeric(8,2)" in sql
    assert "ALTER TABLE dept ADD CONSTRAINT dept_pk PRIMARY KEY (dept_id);" in sql
    assert (
        "ALTER TABLE emp ADD CONSTRAINT emp_dept_fk FOREIGN KEY (dept_id)"
        " REFERENCES dept (dept_id) ON DELETE SET NULL;" in sql
    )
    assert "CHECK (SALARY > 0);" in sql
    assert result.tables == 3
    assert result.constraints == 4


def test_bfile_column_becomes_residue_not_ddl(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    assert "DOC" not in result.sql
    assert "bfile" not in result.sql.lower()
    kinds = {(r.kind, r.object_name) for r in result.residue}
    assert ("column", "SCANS.DOC") in kinds


def test_not_null_check_is_not_duplicated(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    assert "emp_id_nn" not in result.sql.lower()


def test_date_mapping_is_noted(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    notes = [r for r in result.residue if r.kind == "note"]
    assert any(r.object_name == "EMP.HIRED" for r in notes)


def test_residue_report_readable(facts_db: Path) -> None:
    text = residue_report(convert_schema(facts_db).residue)
    assert "SCANS.DOC" in text
    assert "human decision" in text

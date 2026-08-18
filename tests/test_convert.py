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
        INSERT INTO indexes
          (owner, index_name, table_name, index_type, uniqueness, generated) VALUES
          ('HR', 'EMP_NAME_IX', 'EMP', 'NORMAL', 'NONUNIQUE', 'N'),
          ('HR', 'EMP_UPPER_IX', 'EMP', 'FUNCTION-BASED NORMAL', 'NONUNIQUE', 'N'),
          ('HR', 'DEPT_PK', 'DEPT', 'NORMAL', 'UNIQUE', 'Y'),
          ('HR', 'SCANS_LOB_IX', 'SCANS', 'LOB', 'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position) VALUES
          ('HR', 'EMP_NAME_IX', 'ENAME', 1),
          ('HR', 'EMP_UPPER_IX', 'SYS_NC00009$', 1),
          ('HR', 'DEPT_PK', 'DEPT_ID', 1);
        INSERT INTO index_expressions
          (owner, index_name, position, expression, truncated)
          VALUES ('HR', 'EMP_UPPER_IX', 1, 'UPPER(ename)', 0);
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('HR', 'V_STAFF', 'VIEW',
           'CREATE OR REPLACE FORCE EDITIONABLE VIEW "HR"."V_STAFF"'
           || ' ("EMP_ID", "NAME") AS SELECT "EMP_ID", "ENAME"'
           || ' FROM "HR"."EMP" WHERE "SALARY" > 0', 1, 'full'),
          ('HR', 'V_TREE', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_TREE" AS SELECT "EMP_ID"'
           || ' FROM "HR"."EMP" CONNECT BY PRIOR "EMP_ID" = "DEPT_ID"',
           1, 'full'),
          ('HR', 'V_OLDJOIN', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_OLDJOIN" AS'
           || ' SELECT e."ENAME", d."NAME" FROM "HR"."EMP" e, "HR"."DEPT" d'
           || ' WHERE e."DEPT_ID" = d."DEPT_ID" (+)', 1, 'full');
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


def test_indexes_emit_and_skip_correctly(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE INDEX emp_name_ix ON emp (ename);" in sql
    assert "CREATE INDEX emp_upper_ix ON emp ((UPPER(ename)));" in sql
    # The constraint-backed index and the LOB index never appear.
    assert "CREATE UNIQUE INDEX dept_pk" not in sql
    assert "scans_lob_ix" not in sql.lower()
    kinds = {(r.kind, r.object_name) for r in result.residue}
    assert ("index", "SCANS_LOB_IX") in kinds
    assert result.indexes == 2


def test_plain_view_transpiles_with_folded_identifiers(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE OR REPLACE VIEW v_staff" in sql
    assert '"HR"' not in sql
    assert "FROM emp" in sql


def test_connect_by_view_becomes_residue(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    tree = [r for r in result.residue if r.object_name == "V_TREE"]
    assert len(tree) == 1
    assert tree[0].kind == "view"
    assert "rewrite" in tree[0].reason


def test_plus_join_view_becomes_ansi_join(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    assert "v_oldjoin" in result.sql
    assert "(+)" not in result.sql
    assert "LEFT" in result.sql
    assert result.views == 2


@pytest.fixture()
def parts_db(tmp_path: Path) -> Path:
    db = tmp_path / "parts.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'SALES', 'N'), ('HR', 'REGIONS', 'N'),
          ('HR', 'EVENTS', 'N'), ('HR', 'LH', 'N'), ('HR', 'BROKEN', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'SALES', 'SOLD_AT', 1, 'DATE', 7, NULL, NULL, 'N'),
          ('HR', 'REGIONS', 'CODE', 1, 'VARCHAR2', 4, NULL, NULL, 'N'),
          ('HR', 'EVENTS', 'EVT_ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'LH', 'CODE', 1, 'VARCHAR2', 4, NULL, NULL, 'N'),
          ('HR', 'LH', 'ID', 2, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'BROKEN', 'X', 1, 'NUMBER', 22, 10, 0, 'N');
        INSERT INTO part_tables
          (owner, table_name, partitioning_type, subpartitioning_type,
           partition_count, interval) VALUES
          ('HR', 'SALES', 'RANGE', 'NONE', 2, NULL),
          ('HR', 'REGIONS', 'LIST', 'NONE', 2, NULL),
          ('HR', 'EVENTS', 'HASH', 'NONE', 2, NULL),
          ('HR', 'LH', 'LIST', 'HASH', 2, NULL),
          ('HR', 'BROKEN', 'RANGE', 'NONE', 1, NULL);
        INSERT INTO part_key_columns (owner, table_name, column_name, position)
          VALUES ('HR', 'SALES', 'SOLD_AT', 1), ('HR', 'REGIONS', 'CODE', 1),
                 ('HR', 'EVENTS', 'EVT_ID', 1), ('HR', 'LH', 'CODE', 1),
                 ('HR', 'BROKEN', 'X', 1);
        INSERT INTO part_subkey_columns (owner, table_name, column_name, position)
          VALUES ('HR', 'LH', 'ID', 1);
        INSERT INTO part_partitions
          (owner, table_name, partition_name, position, high_value, truncated)
          VALUES
          ('HR', 'SALES', 'P2021', 1,
           'TO_DATE('' 2021-01-01 00:00:00'', ''SYYYY-MM-DD HH24:MI:SS'','
           || ' ''NLS_CALENDAR=GREGORIAN'')', 0),
          ('HR', 'SALES', 'PMAX', 2, 'MAXVALUE', 0),
          ('HR', 'REGIONS', 'P_EU', 1, '''DE'', ''FR''', 0),
          ('HR', 'REGIONS', 'P_REST', 2, 'DEFAULT', 0),
          ('HR', 'EVENTS', 'H1', 1, NULL, 0),
          ('HR', 'EVENTS', 'H2', 2, NULL, 0),
          ('HR', 'LH', 'PART_AA', 1, '''AA''', 0),
          ('HR', 'LH', 'PART_BB', 2, '''BB''', 0),
          ('HR', 'BROKEN', 'P1', 1, 'TO_DATE(SYSDATE)', 0);
        INSERT INTO part_subpartitions
          (owner, table_name, partition_name, subpartition_name, position,
           high_value, truncated) VALUES
          ('HR', 'LH', 'PART_AA', 'SP1', 1, NULL, 0),
          ('HR', 'LH', 'PART_AA', 'SP2', 2, NULL, 0),
          ('HR', 'LH', 'PART_BB', 'SP1', 1, NULL, 0),
          ('HR', 'LH', 'PART_BB', 'SP2', 2, NULL, 0);
        """
    )
    conn.commit()
    conn.close()
    return db


def test_range_children_with_maxvalue(parts_db: Path) -> None:
    result = convert_schema(parts_db)
    sql = result.sql
    assert (
        "CREATE TABLE sales_p2021 PARTITION OF sales"
        " FOR VALUES FROM (MINVALUE) TO ('2021-01-01 00:00:00');" in sql
    )
    assert (
        "CREATE TABLE sales_pmax PARTITION OF sales"
        " FOR VALUES FROM ('2021-01-01 00:00:00') TO (MAXVALUE);" in sql
    )


def test_list_children_with_default_partition(parts_db: Path) -> None:
    sql = convert_schema(parts_db).sql
    assert (
        "CREATE TABLE regions_p_eu PARTITION OF regions"
        " FOR VALUES IN ('DE', 'FR');" in sql
    )
    assert "CREATE TABLE regions_p_rest PARTITION OF regions DEFAULT;" in sql


def test_hash_children_use_modulus(parts_db: Path) -> None:
    sql = convert_schema(parts_db).sql
    assert (
        "CREATE TABLE events_h1 PARTITION OF events"
        " FOR VALUES WITH (MODULUS 2, REMAINDER 0);" in sql
    )
    assert (
        "CREATE TABLE events_h2 PARTITION OF events"
        " FOR VALUES WITH (MODULUS 2, REMAINDER 1);" in sql
    )


def test_composite_list_hash_children(parts_db: Path) -> None:
    sql = convert_schema(parts_db).sql
    assert (
        "CREATE TABLE lh_part_aa PARTITION OF lh"
        " FOR VALUES IN ('AA') PARTITION BY HASH (id);" in sql
    )
    assert (
        "CREATE TABLE lh_part_aa_sp1 PARTITION OF lh_part_aa"
        " FOR VALUES WITH (MODULUS 2, REMAINDER 0);" in sql
    )


def test_unconvertible_bound_omits_all_children(parts_db: Path) -> None:
    result = convert_schema(parts_db)
    assert "broken_p1" not in result.sql
    reasons = [
        r.reason
        for r in result.residue
        if r.object_name == "BROKEN" and r.kind == "partitioning"
    ]
    assert reasons and "children omitted" in reasons[0]

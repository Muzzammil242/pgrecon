from pathlib import Path

import pytest

from pgrecon.convert import convert_schema, residue_report
from pgrecon.convert.identifiers import _fold_condition
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
    assert "CHECK (salary > 0);" in sql
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


def test_identity_default_becomes_identity_column(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO column_defaults VALUES"
        " ('HR', 'EMP', 'EMP_ID', '\"HR\".\"ISEQ$$_75929\".nextval', 'NO', 0)"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "emp_id bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL" in result.sql
    assert "iseq" not in result.sql.lower()
    notes = [r.reason for r in result.residue if r.object_name == "EMP.EMP_ID"]
    assert any("identity" in n for n in notes)


def test_identity_reference_widens_with_it(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO column_defaults VALUES"
        " ('HR', 'DEPT', 'DEPT_ID', '\"HR\".\"ISEQ$$_11\".nextval', 'NO', 0)"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "dept_id bigint GENERATED BY DEFAULT AS IDENTITY NOT NULL" in result.sql
    assert "    dept_id bigint,\n" in result.sql
    notes = [r.reason for r in result.residue if r.object_name == "EMP.DEPT_ID"]
    assert any("widened to bigint" in n for n in notes)


def test_relation_namespace_collisions_rename_with_note(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO constraints (owner, constraint_name, table_name, type,
          ref_owner, ref_constraint, delete_rule)
          VALUES ('HR', 'EMP', 'DEPT', 'U', NULL, NULL, NULL);
        INSERT INTO constraint_columns (owner, constraint_name, column_name,
          position) VALUES ('HR', 'EMP', 'NAME', 1);
        INSERT INTO indexes (owner, index_name, table_name, index_type,
          uniqueness, generated)
          VALUES ('HR', 'DEPT', 'EMP', 'NORMAL', 'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position)
          VALUES ('HR', 'DEPT', 'ENAME', 1);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "ADD CONSTRAINT emp_uk UNIQUE (name);" in result.sql
    assert "CREATE INDEX dept_ix ON emp (ename);" in result.sql
    shared = [r for r in result.residue if "shares its name with a table" in r.reason]
    assert len(shared) == 2


def test_snapshot_index_is_skipped_with_note(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO indexes (owner, index_name, table_name, index_type,"
        " uniqueness, generated) VALUES"
        " ('HR', 'I_SNAP$_MV_X', 'EMP', 'FUNCTION-BASED NORMAL', 'UNIQUE', 'N')"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "I_SNAP" not in result.sql
    notes = [r.reason for r in result.residue if r.object_name == "I_SNAP$_MV_X"]
    assert any("materialized view support index" in n for n in notes)


def test_object_view_refuses(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES"
        " ('HR', 'OC_EMP', 'VIEW',"
        ' \'CREATE OR REPLACE VIEW "HR"."OC_EMP" OF "HR"."EMP_TYP"'
        ' WITH OBJECT IDENTIFIER (emp_id) AS SELECT * FROM "HR"."EMP"\','
        " 1, 'full')"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "OC_EMP" not in result.sql
    reasons = [r.reason for r in result.residue if r.object_name == "OC_EMP"]
    assert any("object views" in n for n in reasons)


def test_expression_guards_sysop_and_systimestamp() -> None:
    from pgrecon.convert.identifiers import _default_guard, _fold_expression

    guard = _default_guard("SYS_OP_MAP_NONNULL(dname)")
    assert guard is not None and "SYS_OP_MAP_NONNULL" in guard
    assert _fold_expression("SYSTIMESTAMP") == "CURRENT_TIMESTAMP"
    folded = _fold_expression("ROUND(net_amount * (1 + vat_rate/100), 2)")
    assert folded == "ROUND(net_amount * (1 + CAST(vat_rate AS DECIMAL) / 100), 2)"


def test_condition_concatenation_null_safe() -> None:
    # The sqlglot lane (checks, defaults, trigger WHEN, views) gets
    # the same Oracle NULL-as-empty concatenation semantics as the
    # PL/SQL lane, for both || and Oracle's CONCAT().
    folded = _fold_condition('"KIND" || "TAG" <> \'xy\'')
    assert folded == "NULLIF(CONCAT(kind, tag), '') <> 'xy'"
    folded = _fold_condition('CONCAT("KIND", "TAG") <> \'xy\'')
    assert folded == "NULLIF(CONCAT(kind, tag), '') <> 'xy'"


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


def test_quoted_uppercase_check_folds_to_converted_columns(facts_db: Path) -> None:
    # Oracle stores conditions with quoted uppercase identifiers; the
    # emitted check must reference the lowercase columns we created.
    sql = convert_schema(facts_db).sql
    assert '"SALARY"' not in sql
    assert '"EMP_ID"' not in sql


def test_check_on_dropped_column_declines(tmp_path: Path) -> None:
    db = tmp_path / "ck.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'SCANS', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'SCANS', 'ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'SCANS', 'DOC', 2, 'BFILE', 530, NULL, NULL, 'Y');
        INSERT INTO constraints
          (owner, constraint_name, table_name, type)
          VALUES ('HR', 'SCANS_DOC_CK', 'SCANS', 'C');
        INSERT INTO check_conditions (owner, constraint_name, condition, truncated)
          VALUES ('HR', 'SCANS_DOC_CK', '"DOC" IS NOT NULL OR "ID" > 0', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "scans_doc_ck" not in result.sql.lower()
    reasons = [r.reason for r in result.residue if r.object_name == "SCANS_DOC_CK"]
    assert reasons and "DOC" in reasons[0]


def test_partitioned_pk_missing_partition_key_declines(parts_db: Path) -> None:
    import sqlite3 as s3

    conn = s3.connect(parts_db)
    conn.executescript(
        """
        INSERT INTO constraints (owner, constraint_name, table_name, type)
          VALUES ('HR', 'LH_PK', 'LH', 'P');
        INSERT INTO constraint_columns
          (owner, constraint_name, column_name, position)
          VALUES ('HR', 'LH_PK', 'ID', 1);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(parts_db)
    assert "lh_pk" not in result.sql.lower()
    reasons = [r.reason for r in result.residue if r.object_name == "LH_PK"]
    assert reasons and "partition key" in reasons[0]


def test_constraint_on_hidden_system_column_declines(parts_db: Path) -> None:
    import sqlite3 as s3

    conn = s3.connect(parts_db)
    conn.executescript(
        """
        INSERT INTO constraints (owner, constraint_name, table_name, type)
          VALUES ('HR', 'EVENTS_UK', 'EVENTS', 'U');
        INSERT INTO constraint_columns
          (owner, constraint_name, column_name, position)
          VALUES ('HR', 'EVENTS_UK', 'SYS_NC00003$', 1);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(parts_db)
    assert "events_uk" not in result.sql.lower()
    reasons = [r.reason for r in result.residue if r.object_name == "EVENTS_UK"]
    assert reasons and "hidden system column" in reasons[0]


@pytest.fixture()
def closers_db(tmp_path: Path) -> Path:
    db = tmp_path / "cl.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'ORDERS', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'ORDERS', 'ORDER_ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'ORDERS', 'PLACED_AT', 2, 'DATE', 7, NULL, NULL, 'N'),
          ('HR', 'ORDERS', 'STATE', 3, 'VARCHAR2', 10, NULL, NULL, 'Y'),
          ('HR', 'ORDERS', 'TOTAL_TX', 4, 'NUMBER', 22, 10, 2, 'Y');
        INSERT INTO column_defaults
          (owner, table_name, column_name, default_text, virtual, truncated)
          VALUES
          ('HR', 'ORDERS', 'PLACED_AT', 'SYSDATE', 'NO', 0),
          ('HR', 'ORDERS', 'STATE', '''NEW''', 'NO', 0),
          ('HR', 'ORDERS', 'TOTAL_TX', '"ORDER_ID" * 2', 'YES', 0);
        INSERT INTO sequences
          (owner, sequence_name, min_value, max_value, increment_by,
           cycle_flag, cache_size, last_number) VALUES
          ('HR', 'ORDER_SEQ', '1', '9999999999999999999999999999', '1',
           'N', '20', '4242'),
          ('HR', 'BAD_SEQ', 'x', 'y', '1', 'N', '0', '1');
        INSERT INTO synonyms
          (owner, synonym_name, table_owner, table_name, db_link) VALUES
          ('HR', 'ORD', 'HR', 'ORDERS', NULL),
          ('HR', 'FAR', 'HR', 'EMPLOYEES', 'HR_REMOTE'),
          ('PUBLIC', 'ORDERS_PUB', 'HR', 'ORDERS', NULL);
        INSERT INTO db_links (owner, db_link, username, host)
          VALUES ('HR', 'HR_REMOTE', 'HR', 'orcl');
        """
    )
    conn.commit()
    conn.close()
    return db


def test_defaults_without_pg_counterparts_decline(tmp_path: Path) -> None:
    db = tmp_path / "dg.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'GUIDS', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'GUIDS', 'ID', 1, 'RAW', 16, NULL, NULL, 'N'),
          ('HR', 'GUIDS', 'MADE', 2, 'DATE', 7, NULL, NULL, 'Y');
        INSERT INTO column_defaults
          (owner, table_name, column_name, default_text, virtual, truncated)
          VALUES
          ('HR', 'GUIDS', 'ID', 'SYS_GUID()', 'NO', 0),
          ('HR', 'GUIDS', 'MADE', 'TO_DATE(SYSDATE)', 'NO', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "sys_guid" not in result.sql.lower()
    assert "to_date" not in result.sql.lower()
    assert "id bytea NOT NULL" in result.sql
    reasons = " ".join(r.reason for r in result.residue)
    assert "SYS_GUID" in reasons
    assert "TO_DATE" in reasons


def test_string_literal_mentioning_sys_guid_is_innocent(tmp_path: Path) -> None:
    # The guard walks the tree, so a default whose STRING mentions
    # SYS_GUID( must not decline - only a real call does.
    db = tmp_path / "lit.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'NOTES', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'NOTES', 'ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'NOTES', 'HINT', 2, 'VARCHAR2', 60, NULL, NULL, 'Y');
        INSERT INTO column_defaults
          (owner, table_name, column_name, default_text, virtual, truncated)
          VALUES ('HR', 'NOTES', 'HINT', '''use SYS_GUID() here''', 'NO', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "DEFAULT 'use SYS_GUID() here'" in result.sql
    assert not any("SYS_GUID" in r.reason for r in result.residue)


def test_object_method_view_declines(facts_db: Path) -> None:
    import sqlite3 as s3

    conn = s3.connect(facts_db)
    conn.execute(
        "INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality)"
        " VALUES ('HR', 'V_AGES', 'VIEW',"
        ' \'CREATE OR REPLACE VIEW "HR"."V_AGES" AS SELECT'
        ' p.person.getAge() AS age FROM "HR"."EMP" p\', 1, \'full\')'
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    ages = [r for r in result.residue if r.object_name == "V_AGES"]
    assert ages and "object-relational" in ages[0].reason
    assert "getage" not in result.sql.lower()


def test_defaults_and_generated_columns(closers_db: Path) -> None:
    sql = convert_schema(closers_db).sql
    assert "placed_at timestamp(0) DEFAULT CURRENT_TIMESTAMP NOT NULL" in sql
    assert "state varchar(10) DEFAULT 'NEW'" in sql
    assert "total_tx numeric(10,2) GENERATED ALWAYS AS (order_id * 2) STORED" in sql


def test_sequences_emit_with_bigint_safe_bounds(closers_db: Path) -> None:
    result = convert_schema(closers_db)
    sql = result.sql
    assert (
        "CREATE SEQUENCE order_seq INCREMENT BY 1 MINVALUE 1"
        " START WITH 4242 CACHE 20;" in sql
    )
    assert "MAXVALUE" not in sql
    reasons = [r for r in result.residue if r.object_name == "BAD_SEQ"]
    assert reasons and "recreate by hand" in reasons[0].reason
    assert result.sequences == 1


def test_synonyms_become_views_or_residue(closers_db: Path) -> None:
    result = convert_schema(closers_db)
    assert "CREATE OR REPLACE VIEW ord AS SELECT * FROM orders;" in result.sql
    kinds = {(r.kind, r.object_name) for r in result.residue}
    assert ("synonym", "FAR") in kinds
    assert ("synonym", "ORDERS_PUB") in kinds
    assert result.synonyms == 1


def test_db_links_scaffold_commented(closers_db: Path) -> None:
    # The scaffold needs oracle_fdw, credentials, and foreign tables;
    # it ships commented so the output applies on a vanilla server.
    result = convert_schema(closers_db)
    sql = result.sql
    assert "-- CREATE EXTENSION IF NOT EXISTS oracle_fdw;" in sql
    assert (
        "-- CREATE SERVER hr_remote FOREIGN DATA WRAPPER oracle_fdw"
        " OPTIONS (dbserver 'orcl');" in sql
    )
    assert "-- CREATE USER MAPPING FOR CURRENT_USER SERVER hr_remote" in sql
    assert "\nCREATE SERVER" not in sql
    assert result.db_links == 1


def test_unconvertible_bound_omits_all_children(parts_db: Path) -> None:
    result = convert_schema(parts_db)
    assert "broken_p1" not in result.sql
    reasons = [
        r.reason
        for r in result.residue
        if r.object_name == "BROKEN" and r.kind == "partitioning"
    ]
    assert reasons and "children omitted" in reasons[0]

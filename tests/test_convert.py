import re
import sqlite3
from pathlib import Path

import pytest

from pgrecon.convert import convert_schema, residue_report
from pgrecon.convert.identifiers import (
    _default_guard,
    _fold_condition,
    _fold_expression,
)
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
    assert ident("T_1") == "t_1"
    # Reserved words fold like any other case-insensitive name and
    # then need quotes.
    assert ident("ORDER") == '"order"'
    assert ident("LIMIT") == '"limit"'
    # A name with lowercase letters was created quoted on Oracle and
    # keeps its spelling; spaces need quotes either way.
    assert ident("Weird Name") == '"Weird Name"'
    assert ident("MixedCase") == '"MixedCase"'
    assert ident("WITH SPACE") == '"with space"'


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
          ('HR', 'EMP',  'ENAME',    5, 'VARCHAR2', 50, NULL, NULL, 'Y'),
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
    shared = [r for r in result.residue if "shares its name with table" in r.reason]
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
    from pgrecon.convert.identifiers import _fold_expression

    guard = _default_guard("SYS_OP_MAP_NONNULL(dname)")
    assert guard is not None and "SYS_OP_MAP_NONNULL" in guard
    assert _fold_expression("SYSTIMESTAMP") == "CURRENT_TIMESTAMP"
    folded = _fold_expression("ROUND(net_amount * (1 + vat_rate/100), 2)")
    assert folded == "ROUND(net_amount * (1 + CAST(vat_rate AS DECIMAL) / 100), 2)"
    assert _fold_expression("GROUPING_ID(a, b)") == "GROUPING(a, b)"


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


def test_connect_by_view_becomes_with_recursive(facts_db: Path) -> None:
    # No START WITH: Oracle roots the hierarchy at every row, so the
    # base branch carries no filter.
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE VIEW v_tree AS" in sql
    assert "WITH RECURSIVE hierarchy (emp_id, pgr_key) AS (" in sql
    assert "SELECT emp_id, emp_id\n  FROM emp\n  UNION ALL" in sql
    assert "JOIN hierarchy AS h ON c.dept_id = h.pgr_key" in sql
    assert not [r for r in result.residue if r.object_name == "V_TREE"]


def test_connect_by_full_shape_and_refusals(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('HR', 'V_CHART', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_CHART" ("EMP_ID", "DEPTH", "CHAIN")'
           || ' AS SELECT emp_id, LEVEL AS depth,'
           || ' SYS_CONNECT_BY_PATH(ename, ''/'') AS chain FROM emp'
           || ' START WITH dept_id IS NULL CONNECT BY PRIOR emp_id = dept_id',
           1, 'full'),
          ('HR', 'V_NOCYC', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_NOCYC" AS SELECT emp_id FROM emp'
           || ' CONNECT BY NOCYCLE PRIOR emp_id = dept_id', 1, 'full'),
          ('HR', 'V_SIBS', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_SIBS" AS SELECT emp_id FROM emp'
           || ' CONNECT BY PRIOR emp_id = dept_id ORDER SIBLINGS BY emp_id',
           1, 'full');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE VIEW v_chart AS" in sql
    assert "WITH RECURSIVE hierarchy (emp_id, depth, chain, pgr_key) AS (" in sql
    assert "SELECT emp_id, 1, concat('/', ename), emp_id" in sql
    assert "WHERE dept_id IS NULL" in sql
    assert "h.depth + 1, concat(h.chain, '/', c.ename), c.emp_id" in sql
    reasons = {r.object_name: r.reason for r in result.residue if r.kind == "view"}
    assert "CYCLE clause" in reasons["V_NOCYC"]
    assert "ORDER SIBLINGS BY" in reasons["V_SIBS"]


def test_decode_views_keep_oracle_null_semantics(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('HR', 'V_DEC', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_DEC" AS SELECT'
           || ' DECODE(ename, ''a'', 1, ''b'', 2, 0) AS lit_code,'
           || ' DECODE(ename, '''', ''missing'', ename) AS empty_search,'
           || ' DECODE(dept_id, emp_id, ''self'', ''other'') AS col_search,'
           || ' DECODE(ename, ''gone'', '''', ename) AS empty_result'
           || ' FROM emp', 1, 'full');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    # Literal searches keep plain equality: a NULL operand matches no
    # branch and falls to the default, in Oracle and PostgreSQL alike.
    assert "CASE WHEN ename = 'a' THEN 1 WHEN ename = 'b' THEN 2 ELSE 0 END" in sql
    # Oracle folds '' to NULL, as a search and as a result.
    assert "CASE WHEN ename IS NULL THEN 'missing' ELSE ename END" in sql
    assert "CASE WHEN ename = 'gone' THEN NULL ELSE ename END" in sql
    # A column search can be NULL at runtime, and DECODE matches two
    # NULLs; plain equality would fall through to the default.
    assert "WHEN dept_id = emp_id OR (" in sql
    assert "dept_id IS NULL AND emp_id IS NULL" in sql
    assert "= ''" not in sql
    assert not [r for r in result.residue if r.object_name == "V_DEC"]


def test_json_table_view_refuses_by_name(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('HR', 'V_JSON', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_JSON" AS SELECT jt.item'
           || ' FROM emp, JSON_TABLE(ename, ''$.items[*]'''
           || ' COLUMNS (item VARCHAR2(100) PATH ''$.name'')) jt',
           1, 'full');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    reasons = {r.object_name: r.reason for r in result.residue if r.kind == "view"}
    assert "JSON_TABLE" in reasons["V_JSON"]
    assert "version 17" in reasons["V_JSON"]
    assert "V_JSON" not in result.sql


def test_materialized_view_container_notes_the_loss(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'MV_DEPT_SUM', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'MV_DEPT_SUM', 'DNAME', 1, 'VARCHAR2', 14, NULL, NULL, 'N'),
          ('HR', 'MV_DEPT_SUM', 'TOTAL', 2, 'NUMBER', 22, NULL, NULL, 'Y');
        INSERT INTO mviews (owner, mview_name, rewrite_enabled, refresh_method)
          VALUES ('HR', 'MV_DEPT_SUM', 'Y', 'COMPLETE');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "CREATE TABLE mv_dept_sum (" in result.sql
    mv = [r for r in result.residue if r.kind == "materialized view"]
    assert len(mv) == 1 and mv[0].object_name == "MV_DEPT_SUM"
    assert "refresh method: COMPLETE" in mv[0].reason
    assert "query rewrite does not exist" in mv[0].reason


def test_mview_with_query_becomes_materialized_view(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'MV_SAL', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'MV_SAL', 'DEPT_ID', 1, 'NUMBER', 22, 4, 0, 'Y'),
          ('HR', 'MV_SAL', 'TOTAL', 2, 'NUMBER', 22, NULL, NULL, 'Y');
        INSERT INTO mviews
          (owner, mview_name, rewrite_enabled, refresh_method, query) VALUES
          ('HR', 'MV_SAL', 'Y', 'COMPLETE',
           'SELECT dept_id, SUM(salary) AS total FROM emp GROUP BY dept_id');
        INSERT INTO constraints
          (owner, constraint_name, table_name, type, ref_owner,
           ref_constraint, delete_rule) VALUES
          ('HR', 'MV_SAL_PK', 'MV_SAL', 'P', NULL, NULL, NULL);
        INSERT INTO constraint_columns
          (owner, constraint_name, column_name, position) VALUES
          ('HR', 'MV_SAL_PK', 'DEPT_ID', 1);
        INSERT INTO triggers
          (owner, trigger_name, trigger_type, triggering_event,
           table_name, status) VALUES
          ('HR', 'TRG_MV', 'AFTER EACH ROW', 'INSERT', 'MV_SAL', 'ENABLED');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "CREATE MATERIALIZED VIEW mv_sal (dept_id, total) AS" in sql
    assert "CREATE TABLE mv_sal" not in sql
    assert result.mviews == 1
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "cannot carry" in reasons["MV_SAL_PK"]
    assert "triggers on materialized" in reasons["TRG_MV"]
    notes = [r.reason for r in result.residue if r.object_name == "MV_SAL"]
    assert any("REFRESH MATERIALIZED VIEW" in n for n in notes)
    assert any("query rewrite" in n for n in notes)


def test_mview_query_over_unknown_table_refuses(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'MV_GONE', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'MV_GONE', 'X', 1, 'NUMBER', 22, NULL, NULL, 'Y');
        INSERT INTO mviews
          (owner, mview_name, rewrite_enabled, refresh_method, query) VALUES
          ('HR', 'MV_GONE', 'N', 'FORCE',
           'SELECT x FROM remote_thing');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "MV_GONE" not in result.sql
    mv = [r for r in result.residue if r.kind == "materialized view"]
    assert len(mv) == 1
    assert "REMOTE_THING" in mv[0].reason


def test_plus_join_view_becomes_ansi_join(facts_db: Path) -> None:
    result = convert_schema(facts_db)
    assert "v_oldjoin" in result.sql
    assert "(+)" not in result.sql
    assert "LEFT" in result.sql
    assert result.views == 3


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


def test_comments_and_grants_travel_with_the_schema(facts_db: Path) -> None:
    import sqlite3

    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO table_comments (owner, table_name, comments) VALUES
          ('HR', 'EMP', 'People on payroll'),
          ('HR', 'GHOST', 'comment on an unconverted table');
        INSERT INTO column_comments
          (owner, table_name, column_name, comments) VALUES
          ('HR', 'EMP', 'SALARY', 'Gross, it''s monthly'),
          ('HR', 'SCANS', 'DOC', 'comment on a dropped column');
        INSERT INTO grants
          (grantee, owner, table_name, privilege, grantable) VALUES
          ('APP_RO', 'HR', 'EMP', 'SELECT', 'NO'),
          ('APP_RO', 'HR', 'EMP', 'READ', 'NO'),
          ('APP_RW', 'HR', 'EMP', 'UPDATE', 'YES'),
          ('PUBLIC', 'HR', 'DEPT', 'SELECT', 'NO'),
          ('APP_RW', 'HR', 'EMP', 'FLASHBACK', 'NO'),
          ('APP_RO', 'HR', 'GHOST', 'SELECT', 'NO');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "COMMENT ON TABLE emp IS 'People on payroll';" in sql
    assert "COMMENT ON COLUMN emp.salary IS 'Gross, it''s monthly';" in sql
    # A comment follows its object: gone object, gone comment.
    assert "GHOST" not in sql and "unconverted table" not in sql
    assert "dropped column" not in sql
    # Roles bootstrap idempotently, grants map, grantable carries.
    assert "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_ro')" in sql
    assert "GRANT SELECT ON emp TO app_ro;" in sql
    assert "GRANT UPDATE ON emp TO app_rw WITH GRANT OPTION;" in sql
    assert "GRANT SELECT ON dept TO PUBLIC;" in sql
    # Oracle READ maps to SELECT; FLASHBACK declines by name.
    assert sql.count("GRANT SELECT ON emp TO app_ro;") == 2
    reasons = [r.reason for r in result.residue if r.kind == "grant"]
    assert reasons and "FLASHBACK" in reasons[0]


def test_names_past_the_identifier_limit(tmp_path: Path) -> None:
    prefix = "customer_account_reconciliation_adjustment_reference_number"
    alpha = (prefix + "_col_alpha").upper()  # 69 chars, same first 63
    beta = (prefix + "_col_beta").upper()
    lone = (prefix + "_settled_flag").upper()  # long but unique
    tab_a = (prefix + "_history_alpha").upper()
    tab_b = (prefix + "_history_beta").upper()
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        f"""
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('APP', 'COLLIDING', 'N'), ('APP', 'SURVIVOR', 'N'),
          ('APP', '{tab_a}', 'N'), ('APP', '{tab_b}', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('APP', 'COLLIDING', '{alpha}', 1, 'VARCHAR2', 30, NULL, NULL, 'Y'),
          ('APP', 'COLLIDING', '{beta}',  2, 'VARCHAR2', 30, NULL, NULL, 'Y'),
          ('APP', 'SURVIVOR',  '{lone}',  1, 'VARCHAR2', 30, NULL, NULL, 'Y'),
          ('APP', '{tab_a}', 'ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('APP', '{tab_b}', 'ID', 1, 'NUMBER', 22, 10, 0, 'N');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    sql = result.sql
    # Two columns folding to one name would fail the CREATE outright;
    # the table refuses with both names in the reason.
    assert "CREATE TABLE colliding" not in sql
    table_reasons = [r.reason for r in result.residue if r.object_name == "COLLIDING"]
    assert table_reasons and alpha in table_reasons[0] and beta in table_reasons[0]
    # A long name that stays unique after truncation emits verbatim
    # with a note; PostgreSQL truncates it consistently everywhere.
    assert f"CREATE TABLE {tab_a.lower()}" in sql
    assert lone.lower() in sql
    notes = [r for r in result.residue if r.kind == "note" and "63-byte" in r.reason]
    assert {r.object_name for r in notes} >= {tab_a, f"SURVIVOR.{lone}"}
    # The second table folding onto the first refuses; only one of the
    # pair may exist on the target.
    assert f"CREATE TABLE {tab_b.lower()}" not in sql
    clash = [r for r in result.residue if r.object_name == tab_b and r.kind == "table"]
    assert clash and tab_a in clash[0].reason
    assert result.tables == 2


def test_shared_relation_namespace_across_kinds(tmp_path: Path) -> None:
    prefix = "customer_account_reconciliation_adjustment_reference_number"
    ix_a = (prefix + "_ix_alpha").upper()
    ix_b = (prefix + "_ix_beta").upper()
    vw = (prefix + "_history_view").upper()
    tb = (prefix + "_history_table").upper()
    seq = (prefix + "_journal_seq").upper()
    tb2 = (prefix + "_journal_tab").upper()
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        f"""
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('APP', 'PLAIN', 'N'), ('APP', '{tb}', 'N'), ('APP', '{tb2}', 'N');
        INSERT INTO columns (owner, table_name, column_name, position,
          data_type, data_length, data_precision, data_scale, nullable) VALUES
          ('APP', 'PLAIN', 'ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('APP', 'PLAIN', 'NAME', 2, 'VARCHAR2', 50, NULL, NULL, 'Y'),
          ('APP', '{tb}', 'ID', 1, 'NUMBER', 22, 10, 0, 'N'),
          ('APP', '{tb2}', 'ID', 1, 'NUMBER', 22, 10, 0, 'N');
        INSERT INTO sequences (owner, sequence_name, min_value, max_value,
          increment_by, cycle_flag, cache_size, last_number) VALUES
          ('APP', '{seq}', '1', '', '1', 'N', '20', '55');
        INSERT INTO indexes (owner, index_name, table_name, index_type,
          uniqueness, generated) VALUES
          ('APP', '{ix_a}', 'PLAIN', 'NORMAL', 'NONUNIQUE', 'N'),
          ('APP', '{ix_b}', 'PLAIN', 'NORMAL', 'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position)
          VALUES ('APP', '{ix_a}', 'ID', 1), ('APP', '{ix_b}', 'NAME', 1);
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('APP', '{vw}', 'VIEW',
           'CREATE OR REPLACE VIEW "APP"."{vw}" ("ID") AS'
           || ' SELECT "ID" FROM "APP"."PLAIN"', 1, 'full');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    sql = result.sql
    # Two indexes folding to one name: the first emits, the second is
    # residue naming the first - never a false all-clear.
    assert sql.count("CREATE INDEX customer_account") == 1
    ix_refusals = [r for r in result.residue if r.object_name == ix_b]
    assert ix_refusals and ix_a in ix_refusals[0].reason
    # A view folding onto an emitted table refuses cross-kind: both
    # live in pg_class, whatever Oracle kept apart.
    assert "CREATE OR REPLACE VIEW" not in sql
    vw_refusals = [r for r in result.residue if r.object_name == vw]
    assert vw_refusals and tb in vw_refusals[0].reason
    assert vw_refusals[0].kind == "view"
    # Sequences emit before tables, so the sequence wins its name and
    # the folding table refuses naming the sequence.
    assert f"CREATE SEQUENCE {seq.lower()}"[:60] in sql
    tb2_refusals = [
        r for r in result.residue if r.object_name == tb2 and r.kind == "table"
    ]
    assert tb2_refusals and seq in tb2_refusals[0].reason
    assert "sequence" in tb2_refusals[0].reason


def test_registry_scopes_are_independent() -> None:
    from pgrecon.convert.namespace import RELATIONS, ROUTINES, NameRegistry
    from pgrecon.convert.residue import Residue

    residue: list[Residue] = []
    registry = NameRegistry()
    assert registry.claim("LEDGER", "table", "APP", residue)
    # The same name in the routine namespace is a different object on
    # PostgreSQL and claims cleanly.
    assert registry.claim("LEDGER", "function", "APP", residue, scope=ROUTINES)
    # Same-name collision in one scope names both namespaces' owner.
    assert not registry.claim("LEDGER", "index", "APP", residue)
    assert residue and "separate namespaces" in residue[-1].reason
    assert registry.peek("LEDGER", RELATIONS) == ("LEDGER", "table")
    # Per-table scopes see only their own table.
    assert registry.claim("CK", "check", "APP", residue, scope="constraint:T1")
    assert registry.claim("CK", "check", "APP", residue, scope="constraint:T2")
    assert not registry.claim("CK", "check", "APP", residue, scope="constraint:T1")


def test_check_without_condition_is_declined_by_name(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO constraints (owner, constraint_name, table_name, type)"
        " VALUES ('HR', 'EMP_QTY_CK', 'EMP', 'C')"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    reasons = {r.object_name: r.reason for r in result.residue if r.kind == "check"}
    assert "not captured" in reasons["EMP_QTY_CK"]
    assert "EMP_QTY_CK" not in result.sql.upper()


def test_view_without_ddl_is_declined_by_name(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.execute(
        "INSERT INTO objects (owner, name, type) VALUES ('HR', 'V_GHOST', 'VIEW')"
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    reasons = {r.object_name: r.reason for r in result.residue if r.kind == "view"}
    assert "no DDL" in reasons["V_GHOST"]


def test_case_sensitive_and_reserved_names_spell_consistently(tmp_path: Path) -> None:
    """A quoted mixed-case table with a reserved-word column: the
    table, its check, its comments, its grants, and a view over it
    must all spell both names one way, or the DDL does not apply."""
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO objects (owner, name, type) VALUES
          ('HR', 'MixedDept', 'TABLE'), ('HR', 'V_MIXED', 'VIEW');
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'MixedDept', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'MixedDept', 'ID',    1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'MixedDept', 'LIMIT', 2, 'NUMBER', 22, 5,  0, 'Y');
        INSERT INTO constraints (owner, constraint_name, table_name, type) VALUES
          ('HR', 'MIXED_PK', 'MixedDept', 'P'),
          ('HR', 'MIXED_CK', 'MixedDept', 'C');
        INSERT INTO constraint_columns (owner, constraint_name, column_name, position)
          VALUES ('HR', 'MIXED_PK', 'ID', 1);
        INSERT INTO check_conditions (owner, constraint_name, condition, truncated)
          VALUES ('HR', 'MIXED_CK', '"LIMIT" > 0', 0);
        INSERT INTO indexes (owner, index_name, table_name, index_type, uniqueness,
                             generated)
          VALUES ('HR', 'MIXED_LIMIT_IX', 'MixedDept', 'NORMAL', 'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position)
          VALUES ('HR', 'MIXED_LIMIT_IX', 'LIMIT', 1);
        INSERT INTO table_comments (owner, table_name, comments)
          VALUES ('HR', 'MixedDept', 'Case matters');
        INSERT INTO column_comments (owner, table_name, column_name, comments)
          VALUES ('HR', 'MixedDept', 'LIMIT', 'Reserved word');
        INSERT INTO grants (grantee, owner, table_name, privilege, grantable)
          VALUES ('APP_RO', 'HR', 'MixedDept', 'SELECT', 'NO');
        INSERT INTO ddl (owner, name, type, ddl, parse_ok, parse_quality) VALUES
          ('HR', 'V_MIXED', 'VIEW',
           'CREATE OR REPLACE VIEW "HR"."V_MIXED" AS'
           || ' SELECT "LIMIT" FROM "HR"."MixedDept" WHERE "LIMIT" > 1', 1, 'full');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    sql = result.sql
    assert 'CREATE TABLE "MixedDept" (' in sql
    assert re.search(r'^\s+"limit" (integer|smallint|numeric)', sql, re.MULTILINE)
    assert 'ALTER TABLE "MixedDept" ADD CONSTRAINT mixed_ck CHECK ("limit" > 0);' in sql
    assert 'CREATE INDEX mixed_limit_ix ON "MixedDept" ("limit");' in sql
    assert "COMMENT ON TABLE \"MixedDept\" IS 'Case matters';" in sql
    assert 'COMMENT ON COLUMN "MixedDept"."limit" IS \'Reserved word\';' in sql
    assert 'GRANT SELECT ON "MixedDept" TO app_ro;' in sql
    assert 'FROM "MixedDept"' in sql and '"limit" > 1' in sql
    for wrong in ('"LIMIT"', "mixeddept", '"MIXEDDEPT"'):
        assert wrong not in sql
    assert not [r for r in result.residue if r.kind not in ("note",)]


def test_sequence_default_becomes_nextval(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO sequences (owner, sequence_name, min_value, max_value,
                               increment_by, cycle_flag, cache_size, last_number)
          VALUES ('HR', 'EMP_SEQ', '1', '9999999999999999999999999999', '1', 'N',
                  '20', '1000'),
                 ('HR', 'DEAD_SEQ', '1', '100', '1', 'N', '20', '500');
        INSERT INTO column_defaults (owner, table_name, column_name, default_text,
                                     virtual, truncated)
          VALUES ('HR', 'EMP', 'EMP_ID', '"HR"."EMP_SEQ"."NEXTVAL"', 'NO', 0),
                 ('HR', 'EMP', 'DEPT_ID', 'DEAD_SEQ.NEXTVAL', 'NO', 0),
                 ('HR', 'DEPT', 'NAME', 'EMPTY_CLOB()', 'NO', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "emp_id bigint DEFAULT nextval('emp_seq') NOT NULL" in sql
    assert "CREATE SEQUENCE emp_seq INCREMENT BY 1 MINVALUE 1 START WITH 1000" in sql
    assert "DEAD_SEQ" not in sql.upper().replace("DEAD_SEQ,", "")
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "outside its bounds" in reasons["DEAD_SEQ"]
    assert "not in the converted set" in reasons["EMP.DEPT_ID"]
    assert "name varchar(50) DEFAULT '' NOT NULL" in sql


def test_partition_by_virtual_or_dropped_column_is_declined(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'BY_VIRTUAL', 'N'), ('HR', 'BY_GONE', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'BY_VIRTUAL', 'ID',    1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'BY_VIRTUAL', 'PRICE', 2, 'NUMBER', 22, 10, 2, 'Y'),
          ('HR', 'BY_VIRTUAL', 'BAND',  3, 'NUMBER', 22, 10, 0, 'Y'),
          ('HR', 'BY_GONE', 'ID',  1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'BY_GONE', 'DOC', 2, 'BFILE', 530, NULL, NULL, 'Y');
        INSERT INTO column_defaults (owner, table_name, column_name, default_text,
                                     virtual, truncated)
          VALUES ('HR', 'BY_VIRTUAL', 'BAND', '"PRICE" * 2', 'YES', 0);
        INSERT INTO part_tables (owner, table_name, partitioning_type,
                                 subpartitioning_type, partition_count, interval)
          VALUES ('HR', 'BY_VIRTUAL', 'LIST', 'NONE', 1, NULL),
                 ('HR', 'BY_GONE', 'HASH', 'NONE', 2, NULL);
        INSERT INTO part_key_columns (owner, table_name, column_name, position)
          VALUES ('HR', 'BY_VIRTUAL', 'BAND', 1), ('HR', 'BY_GONE', 'DOC', 1);
        INSERT INTO part_partitions (owner, table_name, partition_name, position,
                                     high_value, truncated)
          VALUES ('HR', 'BY_VIRTUAL', 'P1', 1, '1, 2', 0),
                 ('HR', 'BY_GONE', 'P1', 1, NULL, 0),
                 ('HR', 'BY_GONE', 'P2', 2, NULL, 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "PARTITION BY" not in result.sql
    assert "GENERATED ALWAYS AS (price * 2) STORED" in result.sql
    reasons = {
        r.object_name: r.reason for r in result.residue if r.kind == "partitioning"
    }
    assert "virtual column" in reasons["BY_VIRTUAL"]
    assert "was not converted" in reasons["BY_GONE"]


def test_trunc_over_dates_declines_where_types_are_known(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO constraints (owner, constraint_name, table_name, type)
          VALUES ('HR', 'EMP_HIRED_CK', 'EMP', 'C'),
                 ('HR', 'EMP_SAL_RND_CK', 'EMP', 'C');
        INSERT INTO check_conditions (owner, constraint_name, condition, truncated)
          VALUES ('HR', 'EMP_HIRED_CK', 'TRUNC("HIRED") = "HIRED"', 0),
                 ('HR', 'EMP_SAL_RND_CK', 'ROUND("SALARY") > 0', 0);
        INSERT INTO indexes (owner, index_name, table_name, index_type, uniqueness,
                             generated)
          VALUES ('HR', 'EMP_HIRED_DAY_IX', 'EMP', 'FUNCTION-BASED NORMAL',
                  'NONUNIQUE', 'N'),
                 ('HR', 'EMP_HIRED_DESC_IX', 'EMP', 'FUNCTION-BASED NORMAL',
                  'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position)
          VALUES ('HR', 'EMP_HIRED_DAY_IX', 'SYS_NC00010$', 1),
                 ('HR', 'EMP_HIRED_DESC_IX', 'SYS_NC00011$', 1);
        INSERT INTO index_expressions (owner, index_name, position, expression,
                                       truncated)
          VALUES ('HR', 'EMP_HIRED_DAY_IX', 1, 'TRUNC("HIRED")', 0),
                 ('HR', 'EMP_HIRED_DESC_IX', 1, '"HIRED" DESC', 0);
        INSERT INTO column_defaults (owner, table_name, column_name, default_text,
                                     virtual, truncated)
          VALUES ('HR', 'EMP', 'HIRED', 'TRUNC(SYSDATE)', 'NO', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "ADD CONSTRAINT emp_sal_rnd_ck CHECK (ROUND(salary) > 0)" in sql
    assert "emp_hired_ck" not in sql
    assert "emp_hired_day_ix" not in sql and "emp_hired_desc_ix" not in sql
    assert "DEFAULT TRUNC" not in sql
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "date column HIRED" in reasons["EMP_HIRED_CK"]
    assert "date column HIRED" in reasons["EMP_HIRED_DAY_IX"]
    assert "recreate it from the source" in reasons["EMP_HIRED_DESC_IX"]
    assert "hired timestamp(0) DEFAULT DATE_TRUNC('day', CURRENT_TIMESTAMP)" in sql
    assert _fold_expression("TRUNC(SYSDATE, 'IW')") == (
        "DATE_TRUNC('week', CURRENT_TIMESTAMP)"
    )
    assert _fold_expression("TRUNC(SYSDATE, 'W')") is None


def test_foreign_keys_over_incompatible_types_decline(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'PARENT', 'N'), ('HR', 'CHILD', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'PARENT', 'ID',   1, 'NUMBER',   22, 10, 0, 'N'),
          ('HR', 'PARENT', 'CODE', 2, 'CHAR',     3,  NULL, NULL, 'N'),
          ('HR', 'CHILD',  'ID',   1, 'NUMBER',   22, 10, 0, 'N'),
          ('HR', 'CHILD',  'P_ID', 2, 'NUMBER',   22, NULL, NULL, 'Y'),
          ('HR', 'CHILD',  'Q_ID', 3, 'NUMBER',   22, 5, 0, 'Y'),
          ('HR', 'CHILD',  'CODE', 4, 'VARCHAR2', 3,  NULL, NULL, 'Y'),
          ('HR', 'CHILD',  'X_ID', 5, 'NUMBER',   22, 10, 0, 'Y');
        INSERT INTO constraints (owner, constraint_name, table_name, type, ref_owner,
                                 ref_constraint, delete_rule) VALUES
          ('HR', 'PARENT_PK', 'PARENT', 'P', NULL, NULL, NULL),
          ('HR', 'PARENT_CODE_UK', 'PARENT', 'U', NULL, NULL, NULL),
          ('HR', 'CHILD_PK', 'CHILD', 'P', NULL, NULL, NULL),
          ('HR', 'FK_NUMERIC', 'CHILD', 'R', 'HR', 'PARENT_PK', 'NO ACTION'),
          ('HR', 'FK_NARROW', 'CHILD', 'R', 'HR', 'PARENT_PK', 'NO ACTION'),
          ('HR', 'FK_CHARS', 'CHILD', 'R', 'HR', 'PARENT_CODE_UK', 'NO ACTION'),
          ('HR', 'FK_COUNT', 'CHILD', 'R', 'HR', 'PARENT_PK', 'NO ACTION');
        INSERT INTO constraint_columns (owner, constraint_name, column_name, position)
          VALUES ('HR', 'PARENT_PK', 'ID', 1), ('HR', 'PARENT_CODE_UK', 'CODE', 1),
                 ('HR', 'CHILD_PK', 'ID', 1),
                 ('HR', 'FK_NUMERIC', 'P_ID', 1), ('HR', 'FK_NARROW', 'Q_ID', 1),
                 ('HR', 'FK_CHARS', 'CODE', 1),
                 ('HR', 'FK_COUNT', 'X_ID', 1), ('HR', 'FK_COUNT', 'Q_ID', 2);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    sql = result.sql
    # integer referencing bigint compares through the key; the rest cannot
    assert "ADD CONSTRAINT fk_narrow FOREIGN KEY (q_id) REFERENCES parent (id)" in sql
    reasons = {
        r.object_name: r.reason for r in result.residue if r.kind == "foreign key"
    }
    assert "numeric while the referenced ID maps to bigint" in reasons["FK_NUMERIC"]
    assert "varchar(3) while the referenced CODE maps to char(3)" in reasons["FK_CHARS"]
    assert "2 columns reference a key of 1" in reasons["FK_COUNT"]
    for name in ("fk_numeric", "fk_chars", "fk_count"):
        assert name not in sql


def test_defaults_that_postgres_cannot_evaluate_decline(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'DEPT', 'FLAG', 3, 'CHAR', 1, NULL, NULL, 'Y'),
          ('HR', 'DEPT', 'OWNER_UID', 4, 'NUMBER', 22, 10, 0, 'Y'),
          ('HR', 'DEPT', 'WHO', 5, 'VARCHAR2', 128, NULL, NULL, 'Y');
        INSERT INTO column_defaults (owner, table_name, column_name, default_text,
                                     virtual, truncated) VALUES
          ('HR', 'DEPT', 'FLAG', char(39) || 'LONGER' || char(39), 'NO', 0),
          ('HR', 'DEPT', 'OWNER_UID', 'UID', 'NO', 0),
          ('HR', 'DEPT', 'WHO', 'USER', 'NO', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    sql = result.sql
    assert "who varchar(128) DEFAULT CURRENT_USER" in sql
    assert "flag char(1)," in sql and "LONGER" not in sql
    assert "owner_uid bigint," in sql
    notes = {r.object_name: r.reason for r in result.residue if r.kind == "note"}
    assert "longer than the column" in notes["DEPT.FLAG"]
    assert "UID, a column or Oracle pseudo-column" in notes["DEPT.OWNER_UID"]


def test_foreign_key_to_a_key_that_did_not_convert_declines(tmp_path: Path) -> None:
    """The parent's key is refused (a partitioned table whose key misses
    the partition column), so the foreign key has nothing to point at."""
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES
          ('HR', 'PARENT', 'N'), ('HR', 'CHILD', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'PARENT', 'ID',     1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'PARENT', 'REGION', 2, 'NUMBER', 22, 3, 0, 'N'),
          ('HR', 'CHILD',  'ID',     1, 'NUMBER', 22, 10, 0, 'N'),
          ('HR', 'CHILD',  'P_ID',   2, 'NUMBER', 22, 10, 0, 'Y');
        INSERT INTO constraints (owner, constraint_name, table_name, type, ref_owner,
                                 ref_constraint, delete_rule) VALUES
          ('HR', 'PARENT_PK', 'PARENT', 'P', NULL, NULL, NULL),
          ('HR', 'CHILD_PK', 'CHILD', 'P', NULL, NULL, NULL),
          ('HR', 'CHILD_FK', 'CHILD', 'R', 'HR', 'PARENT_PK', 'NO ACTION');
        INSERT INTO constraint_columns (owner, constraint_name, column_name, position)
          VALUES ('HR', 'PARENT_PK', 'ID', 1), ('HR', 'CHILD_PK', 'ID', 1),
                 ('HR', 'CHILD_FK', 'P_ID', 1);
        INSERT INTO part_tables (owner, table_name, partitioning_type,
                                 subpartitioning_type, partition_count, interval)
          VALUES ('HR', 'PARENT', 'HASH', 'NONE', 2, NULL);
        INSERT INTO part_key_columns (owner, table_name, column_name, position)
          VALUES ('HR', 'PARENT', 'REGION', 1);
        INSERT INTO part_partitions (owner, table_name, partition_name, position,
                                     high_value, truncated)
          VALUES ('HR', 'PARENT', 'P1', 1, NULL, 0), ('HR', 'PARENT', 'P2', 2, NULL, 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "parent_pk" not in result.sql and "child_fk" not in result.sql
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "every partition key" in reasons["PARENT_PK"]
    assert "referenced key PARENT_PK was not converted" in reasons["CHILD_FK"]


def test_index_and_check_over_missing_columns_decline(facts_db: Path) -> None:
    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO indexes (owner, index_name, table_name, index_type, uniqueness,
                             generated)
          VALUES ('HR', 'EMP_GHOST_IX', 'EMP', 'NORMAL', 'NONUNIQUE', 'N');
        INSERT INTO index_columns (owner, index_name, column_name, position)
          VALUES ('HR', 'EMP_GHOST_IX', 'EMP_ID', 1),
                 ('HR', 'EMP_GHOST_IX', 'GHOST', 2);
        INSERT INTO constraints (owner, constraint_name, table_name, type)
          VALUES ('HR', 'EMP_GHOST_CK', 'EMP', 'C');
        INSERT INTO check_conditions (owner, constraint_name, condition, truncated)
          VALUES ('HR', 'EMP_GHOST_CK', '"GHOST" > 0', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "emp_ghost_ix" not in result.sql and "emp_ghost_ck" not in result.sql
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "column GHOST was not converted" in reasons["EMP_GHOST_IX"]
    assert "GHOST, which is not a column" in reasons["EMP_GHOST_CK"]


def test_multi_column_range_partitions_bound_every_column(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES ('HR', 'SALES', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'SALES', 'YEAR', 1, 'NUMBER', 22, 4, 0, 'N'),
          ('HR', 'SALES', 'REGION', 2, 'VARCHAR2', 10, NULL, NULL, 'N');
        INSERT INTO part_tables (owner, table_name, partitioning_type,
                                 subpartitioning_type, partition_count, interval)
          VALUES ('HR', 'SALES', 'RANGE', 'NONE', 2, NULL);
        INSERT INTO part_key_columns (owner, table_name, column_name, position)
          VALUES ('HR', 'SALES', 'YEAR', 1), ('HR', 'SALES', 'REGION', 2);
        INSERT INTO part_partitions (owner, table_name, partition_name, position,
                                     high_value, truncated)
          VALUES ('HR', 'SALES', 'P_EARLY', 1,
                  '2020, ' || char(39) || 'M' || char(39), 0),
                 ('HR', 'SALES', 'P_REST', 2, 'MAXVALUE', 0);
        """
    )
    conn.commit()
    conn.close()
    sql = convert_schema(db).sql
    assert "PARTITION BY RANGE (year, region)" in sql
    assert "FOR VALUES FROM (MINVALUE, MINVALUE) TO (2020, 'M')" in sql
    assert "FOR VALUES FROM (2020, 'M') TO (MAXVALUE, MAXVALUE)" in sql


def test_virtual_column_over_virtual_column_declines(tmp_path: Path) -> None:
    db = tmp_path / "inv.db"
    conn = open_db(db)
    conn.executescript(
        """
        INSERT INTO tables (owner, table_name, temporary) VALUES ('HR', 'PRICES', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'PRICES', 'NET',   1, 'NUMBER', 22, 12, 2, 'N'),
          ('HR', 'PRICES', 'GROSS', 2, 'NUMBER', 22, 12, 2, 'Y'),
          ('HR', 'PRICES', 'TWICE', 3, 'NUMBER', 22, 12, 2, 'Y');
        INSERT INTO column_defaults (owner, table_name, column_name, default_text,
                                     virtual, truncated) VALUES
          ('HR', 'PRICES', 'GROSS', '"NET" * 1.2', 'YES', 0),
          ('HR', 'PRICES', 'TWICE', '"GROSS" * 2', 'YES', 0);
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(db)
    assert "gross numeric(12,2) GENERATED ALWAYS AS (net * 1.2) STORED" in result.sql
    assert "twice" not in result.sql
    reasons = {r.object_name: r.reason for r in result.residue}
    assert "reads virtual column GROSS" in reasons["PRICES.TWICE"]


def test_mview_whose_query_does_not_fit_its_container_declines(
    facts_db: Path,
) -> None:
    conn = sqlite3.connect(facts_db)
    conn.executescript(
        """
        INSERT INTO mviews (owner, mview_name, rewrite_enabled, refresh_method, query)
          VALUES ('HR', 'MV_WIDE', 'N', 'COMPLETE',
                  'SELECT "DEPT_ID", COUNT(*) AS N, SUM("SALARY") AS TOTAL'
                  || ' FROM "HR"."EMP" GROUP BY "DEPT_ID"'),
                 ('HR', 'MV_TWICE', 'N', 'COMPLETE',
                  'SELECT "DEPT_ID", SUM("SALARY") AS DEPT_ID FROM "HR"."EMP"'
                  || ' GROUP BY "DEPT_ID"');
        INSERT INTO tables (owner, table_name, temporary)
          VALUES ('HR', 'MV_WIDE', 'N'), ('HR', 'MV_TWICE', 'N');
        INSERT INTO columns
          (owner, table_name, column_name, position, data_type,
           data_length, data_precision, data_scale, nullable) VALUES
          ('HR', 'MV_WIDE', 'DEPT_ID', 1, 'NUMBER', 22, 4, 0, 'Y'),
          ('HR', 'MV_WIDE', 'TOTAL',   2, 'NUMBER', 22, 8, 2, 'Y'),
          ('HR', 'MV_TWICE', 'DEPT_ID', 1, 'NUMBER', 22, 4, 0, 'Y'),
          ('HR', 'MV_TWICE', 'DEPT_ID_1', 2, 'NUMBER', 22, 8, 2, 'Y');
        """
    )
    conn.commit()
    conn.close()
    result = convert_schema(facts_db)
    assert "mv_wide" not in result.sql and "mv_twice" not in result.sql
    reasons = {
        r.object_name: r.reason for r in result.residue if r.kind == "materialized view"
    }
    assert "yields 3 columns but the container has 2" in reasons["MV_WIDE"]
    assert "two output columns alike" in reasons["MV_TWICE"]

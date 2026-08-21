import sqlite3
from pathlib import Path

import pytest

from pgrecon.inventory import load_dump


@pytest.fixture()
def loaded(dump_basic: Path, tmp_path: Path) -> tuple[dict[str, int], Path]:
    db = tmp_path / "inventory.db"
    counts = load_dump(dump_basic, db)
    return counts, db


def test_counts_match_fixture(loaded: tuple[dict[str, int], Path]) -> None:
    counts, _ = loaded
    assert counts["objects"] == 5
    assert counts["tables"] == 1
    assert counts["columns"] == 3
    assert counts["source"] == 11
    assert counts["features"] == 4
    assert counts["dependencies"] == 2
    assert counts["ddl"] == 4
    assert counts["constraints"] == 3
    assert counts["constraint_columns"] == 3
    assert counts["check_conditions"] == 1
    assert counts["indexes"] == 2
    assert counts["index_columns"] == 2
    assert counts["index_expressions"] == 1
    assert counts["part_tables"] == 1
    assert counts["part_key_columns"] == 1
    assert counts["synonyms"] == 1
    assert counts["triggers"] == 1
    assert counts["db_links"] == 1


def test_structured_facts_are_queryable(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    # The foreign key names its referenced constraint: the FK graph works.
    row = conn.execute(
        "SELECT ref_owner, ref_constraint, delete_rule FROM constraints"
        " WHERE constraint_name = 'FK_EMP_DEPT'"
    ).fetchone()
    assert row == ("HR", "PK_DEPT", "NO ACTION")
    # Function-based index expression carries its text unescaped.
    expr = conn.execute(
        "SELECT expression FROM index_expressions WHERE index_name = 'EMP_UPPER_IX'"
    ).fetchone()[0]
    assert expr == 'UPPER("NAME")'
    # Interval partitioning is visible as a structured fact.
    row = conn.execute(
        "SELECT partitioning_type, interval FROM part_tables WHERE table_name = 'SALES'"
    ).fetchone()
    assert row[0] == "RANGE"
    assert "NUMTOYMINTERVAL" in row[1]


def test_columns_are_typed(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT position, data_precision, data_scale FROM columns"
        " WHERE table_name = 'EMP' AND column_name = 'ID'"
    ).fetchone()
    assert row == (1, 10, 0)
    # Empty CSV fields must load as NULL, not as empty strings.
    precision = conn.execute(
        "SELECT data_precision FROM columns WHERE column_name = 'NAME'"
    ).fetchone()[0]
    assert precision is None


def test_ddl_parse_outcome_is_recorded(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    ok = dict(
        conn.execute("SELECT name, parse_ok FROM ddl WHERE type = 'TABLE'").fetchall()
    )
    # INVOICES carries the identity-options tail DBMS_METADATA emits;
    # it must parse after normalization.
    assert ok == {"EMP": 1, "INVOICES": 1, "BROKEN": 0}
    error = conn.execute(
        "SELECT parse_error FROM ddl WHERE name = 'BROKEN'"
    ).fetchone()[0]
    assert error
    # The unparseable statement is kept verbatim for manual review.
    text = conn.execute("SELECT ddl FROM ddl WHERE name = 'BROKEN'").fetchone()[0]
    assert "not valid sql" in text


def test_ddl_is_stored_verbatim(loaded: tuple[dict[str, int], Path]) -> None:
    # The parse runs on a normalized copy; the stored text keeps the
    # DBMS_METADATA output exactly as extracted, ENABLE keywords and all.
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT ddl, parse_ok FROM ddl WHERE name = 'EMP'").fetchone()
    assert "NOT NULL ENABLE" in row[0]
    assert row[1] == 1


def test_view_ddl_parses(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT parse_ok FROM ddl WHERE name = 'EMP_V'").fetchone()
    assert row == (1,)


def test_parse_quality_is_recorded(loaded: tuple[dict[str, int], Path]) -> None:
    _, db = loaded
    conn = sqlite3.connect(db)
    quality = conn.execute(
        "SELECT parse_quality FROM ddl WHERE name = 'EMP'"
    ).fetchone()[0]
    assert quality == "full"
    # A failed parse carries no quality at all.
    quality = conn.execute(
        "SELECT parse_quality FROM ddl WHERE name = 'BROKEN'"
    ).fetchone()[0]
    assert quality is None


def test_non_utf8_dump_degrades_and_warns(tmp_path: Path) -> None:
    # The dump_korean fixture is deliberately CP949-encoded, the way a
    # Korean Windows client without NLS_LANG set would spool it.
    fixture = Path(__file__).parent / "fixtures" / "dump_korean"
    db = tmp_path / "inv.db"
    counts = load_dump(fixture, db)
    assert counts["objects"] == 1
    conn = sqlite3.connect(db)
    warnings = conn.execute(
        "SELECT key FROM meta WHERE key LIKE 'encoding_warning:%'"
    ).fetchall()
    assert {w[0] for w in warnings} == {
        "encoding_warning:meta.csv",
        "encoding_warning:objects.csv",
    }
    # The name survives as replacement characters, never as a crash.
    name = conn.execute("SELECT name FROM objects").fetchone()[0]
    assert "\N{REPLACEMENT CHARACTER}" in name


def test_multilingual_utf8_roundtrips_exactly(tmp_path: Path) -> None:
    # Chinese, Hebrew, Arabic, Cyrillic, Japanese, and German names in
    # a properly UTF-8 dump must survive byte for byte, including the
    # right-to-left scripts.
    fixture = Path(__file__).parent / "fixtures" / "dump_multilingual"
    db = tmp_path / "inv.db"
    counts = load_dump(fixture, db)
    assert counts["objects"] == 6
    conn = sqlite3.connect(db)
    names = {row[0] for row in conn.execute("SELECT name FROM objects")}
    expected = {
        "客户",
        "לקוח",
        "عميل",
        "клиент",
        "顧客",
        "KüNDE",
    }
    assert names == expected
    warnings = conn.execute(
        "SELECT COUNT(*) FROM meta WHERE key LIKE 'encoding_warning:%'"
    ).fetchone()[0]
    assert warnings == 0


@pytest.mark.parametrize(
    ("encoding", "name"),
    [
        ("cp949", "고객"),
        ("gb18030", "客户"),
        ("shift_jis", "顧客"),
    ],
)
def test_wrong_encoding_recovers_with_flag(
    tmp_path: Path, encoding: str, name: str
) -> None:
    # Simulate a client whose spool came out in a local code page, then
    # prove the explicit --encoding override restores full fidelity.
    dump = tmp_path / "dump"
    dump.mkdir()
    header = '"OWNER","OBJECT_NAME","OBJECT_TYPE","STATUS","CREATED","LAST_DDL_TIME"'
    row = f'"HR","{name}","TABLE","VALID","2024-01-01 10:00:00","2024-01-01 10:00:00"'
    (dump / "objects.csv").write_bytes(f"\n{header}\n{row}\n".encode(encoding))

    db = tmp_path / "lossy.db"
    load_dump(dump, db)
    conn = sqlite3.connect(db)
    warnings = conn.execute(
        "SELECT COUNT(*) FROM meta WHERE key LIKE 'encoding_warning:%'"
    ).fetchone()[0]
    assert warnings == 1

    db = tmp_path / "exact.db"
    load_dump(dump, db, encoding=encoding)
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT name FROM objects").fetchone()[0] == name


def test_explicit_encoding_preserves_korean(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "dump_korean"
    db = tmp_path / "inv.db"
    load_dump(fixture, db, encoding="cp949")
    conn = sqlite3.connect(db)
    name = conn.execute("SELECT name FROM objects").fetchone()[0]
    korean_customer = "\uace0\uac1d"
    assert name == korean_customer
    warnings = conn.execute(
        "SELECT COUNT(*) FROM meta WHERE key LIKE 'encoding_warning:%'"
    ).fetchone()[0]
    assert warnings == 0


def test_missing_dump_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_dump(tmp_path / "nope", tmp_path / "inventory.db")


def test_reload_replaces_database(dump_basic: Path, tmp_path: Path) -> None:
    db = tmp_path / "inventory.db"
    load_dump(dump_basic, db)
    counts = load_dump(dump_basic, db)
    assert counts["objects"] == 5


def test_deep_parse_records_units(loaded: tuple[dict[str, int], Path]) -> None:
    counts, db = loaded
    assert counts["plsql_units"] == 2
    conn = sqlite3.connect(db)
    rows = dict(
        conn.execute("SELECT type, error_count FROM plsql_units WHERE name = 'EMP_PKG'")
    )
    # Both halves of the package parse clean even though the fixture
    # stores source lines without trailing newlines; the loader joins
    # them back into a real unit before parsing.
    assert rows == {"PACKAGE": 0, "PACKAGE BODY": 0}


@pytest.mark.parametrize(
    "ddl",
    [
        'CREATE TABLE "S"."SHIFTS" ("SPAN" INTERVAL DAY (2) TO SECOND (6))',
        'CREATE TABLE "S"."TERMS" ("AGE" INTERVAL YEAR (2) TO MONTH)',
        'CREATE TABLE "S"."BLOBS" ("PAYLOAD" LONG RAW)',
        'CREATE TABLE "S"."T" (X NUMBER,'
        ' CONSTRAINT "C" CHECK (X > 0) DEFERRABLE ENABLE)',
        'CREATE TABLE "S"."T" (X NUMBER,'
        " PRIMARY KEY (X) DEFERRABLE INITIALLY DEFERRED ENABLE)",
        'CREATE TABLE "S"."V" (P NUMBER, Q NUMBER'
        ' GENERATED ALWAYS AS (ROUND("P"*1.2,2)) VIRTUAL VISIBLE)',
        'CREATE TABLE "S"."R" (D DATE) PARTITION BY RANGE ("D")'
        " (PARTITION \"P1\" VALUES LESS THAN (TO_DATE(' 2021-01-01'"
        ", 'SYYYY-MM-DD')), PARTITION \"P2\" VALUES LESS THAN (MAXVALUE))",
        'CREATE TABLE "S"."L" (ST VARCHAR2(2)) PARTITION BY LIST ("ST")'
        " (PARTITION \"EAST\" VALUES ('NY', 'MA'),"
        " PARTITION \"WEST\" VALUES ('CA'))",
        'CREATE TABLE "S"."H" (ID NUMBER) PARTITION BY HASH ("ID")'
        ' (PARTITION "P1", PARTITION "P2")',
    ],
)
def test_field_ddl_shapes_parse(ddl: str) -> None:
    # Shapes DBMS_METADATA emits in the field: spelled-out partition
    # specification lists, deferrable constraint states, spaced
    # INTERVAL precision, LONG RAW, and virtual column visibility.
    from pgrecon.inventory.loader import _oracle_parse

    error, quality = _oracle_parse(ddl)
    assert error is None, error


def test_generated_xdb_trigger_is_skipped(tmp_path: Path) -> None:
    dump = tmp_path / "dump"
    dump.mkdir()
    header = '"OWNER","NAME","TYPE","LINE","TEXT"'
    rows = [
        '"OE","PURCHASEORDER$xd","TRIGGER",1,"trigger PURCHASEORDER$xd"',
        '"OE","PURCHASEORDER$xd","TRIGGER",2,"  call xdb.machinery(:new.x)"',
    ]
    (dump / "source.csv").write_text(
        "\n" + header + "\n" + "\n".join(rows) + "\n", encoding="utf-8"
    )
    db = tmp_path / "inv.db"
    load_dump(dump, db)
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT parse_mode, error_count FROM plsql_units"
        " WHERE name = 'PURCHASEORDER$xd'"
    ).fetchone()
    assert row == ("generated", 0)


def test_wrapped_unit_is_marked_not_parsed(tmp_path: Path) -> None:
    dump = tmp_path / "dump"
    dump.mkdir()
    header = '"OWNER","NAME","TYPE","LINE","TEXT"'
    rows = [
        '"HR","SECRET_PKG","PACKAGE BODY",1,"PACKAGE BODY secret_pkg wrapped "',
        '"HR","SECRET_PKG","PACKAGE BODY",2,"a000000"',
        '"HR","SECRET_PKG","PACKAGE BODY",3,"1"',
        '"HR","SECRET_PKG","PACKAGE BODY",4,"abcd GOTO commit SYSDATE xyz"',
    ]
    (dump / "source.csv").write_text(
        "\n" + header + "\n" + "\n".join(rows) + "\n", encoding="utf-8"
    )
    db = tmp_path / "inv.db"
    load_dump(dump, db)
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT parse_mode, error_count FROM plsql_units WHERE name = 'SECRET_PKG'"
    ).fetchone()
    assert row == ("wrapped", 0)
    # The base64 payload must produce no token-grep findings either.
    features = conn.execute("SELECT COUNT(*) FROM plsql_features").fetchone()[0]
    assert features == 0


def test_license_mview_and_partition_facts_load(tmp_path: Path) -> None:
    dump = tmp_path / "dump"
    dump.mkdir()
    (dump / "license.csv").write_text(
        '\n"KEY","VALUE"\n'
        '"banner","Oracle Database 21c Express Edition Release 21.0.0.0.0"\n'
        '"cpu_count","8"\n',
        encoding="utf-8",
    )
    (dump / "feature_usage.csv").write_text(
        '\n"NAME","VERSION","DETECTED_USAGES","CURRENTLY_USED","LAST_USAGE"\n'
        '"Partitioning (user)","21.0.0.0.0",4,"TRUE","2026-08-01"\n',
        encoding="utf-8",
    )
    # The legacy script opens the QUERY field on its own line, so the
    # value begins with a newline; the loader must keep it verbatim.
    (dump / "mviews.csv").write_text(
        '\n"OWNER","MVIEW_NAME","REWRITE_ENABLED","REFRESH_METHOD","QUERY"\n'
        '"HR","MV_SUM","Y","COMPLETE","\n'
        "SELECT dept, SUM(sal) AS total\n"
        "FROM emp\n"
        'GROUP BY dept"\n',
        encoding="utf-8",
        newline="\n",
    )
    (dump / "part_partitions.csv").write_text(
        '\n"OWNER","TABLE_NAME","PARTITION_NAME","POSITION","TRUNCATED",'
        '"HIGH_VALUE"\n'
        '"HR","SALES","P2021",1,0,"TO_DATE(\'\' 2021-01-01\'\','
        " ''YYYY-MM-DD'')\"\n".replace("''", "'"),
        encoding="utf-8",
    )
    db = tmp_path / "inv.db"
    load_dump(dump, db)
    conn = sqlite3.connect(db)
    assert (
        conn.execute("SELECT value FROM license_facts WHERE key = 'banner'")
        .fetchone()[0]
        .startswith("Oracle Database 21c Express")
    )
    usage = conn.execute(
        "SELECT detected_usages, currently_used FROM feature_usage"
        " WHERE name = 'Partitioning (user)'"
    ).fetchone()
    assert usage == (4, "TRUE")
    query = conn.execute(
        "SELECT query FROM mviews WHERE mview_name = 'MV_SUM'"
    ).fetchone()[0]
    assert query.startswith("\nSELECT dept")
    assert "GROUP BY dept" in query
    high = conn.execute(
        "SELECT high_value, truncated FROM part_partitions"
        " WHERE partition_name = 'P2021'"
    ).fetchone()
    assert high == ("TO_DATE(' 2021-01-01', 'YYYY-MM-DD')", 0)

from pgrecon.validate import pg_syntax_error


def test_valid_sql_passes() -> None:
    assert pg_syntax_error("SELECT id, name FROM emp WHERE id > 10") is None


def test_valid_ddl_passes() -> None:
    sql = "CREATE TABLE emp (id integer PRIMARY KEY, name text)"
    assert pg_syntax_error(sql) is None


def test_oracle_only_syntax_is_rejected() -> None:
    # Outer-join operator: legal in Oracle, not in PostgreSQL.
    error = pg_syntax_error("SELECT * FROM a, b WHERE a.id = b.id(+)")
    assert error is not None


def test_garbage_is_rejected_with_message() -> None:
    error = pg_syntax_error("CREATE ??? nonsense")
    assert error

-- Inventory schema. One SQLite file per assessed schema dump.
-- Loaded verbatim by pgrecon.inventory.open_db().

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE objects (
    owner    TEXT NOT NULL,
    name     TEXT NOT NULL,
    type     TEXT NOT NULL,
    status   TEXT,
    created  TEXT,
    last_ddl TEXT,
    PRIMARY KEY (owner, name, type)
);

CREATE TABLE tables (
    owner       TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    num_rows    INTEGER,
    avg_row_len INTEGER,
    partitioned TEXT,
    temporary   TEXT,
    PRIMARY KEY (owner, table_name)
);

CREATE TABLE columns (
    owner          TEXT NOT NULL,
    table_name     TEXT NOT NULL,
    column_name    TEXT NOT NULL,
    position       INTEGER,
    data_type      TEXT,
    data_length    INTEGER,
    data_precision INTEGER,
    data_scale     INTEGER,
    nullable       TEXT,
    PRIMARY KEY (owner, table_name, column_name)
);

-- PL/SQL source, one row per line, exactly as ALL_SOURCE returns it.
CREATE TABLE source (
    owner TEXT NOT NULL,
    name  TEXT NOT NULL,
    type  TEXT NOT NULL,
    line  INTEGER NOT NULL,
    text  TEXT,
    PRIMARY KEY (owner, name, type, line)
);

CREATE TABLE features (
    feature TEXT NOT NULL,
    detail  TEXT,
    count   INTEGER
);

CREATE TABLE dependencies (
    owner    TEXT NOT NULL,
    name     TEXT NOT NULL,
    type     TEXT NOT NULL,
    ref_owner TEXT,
    ref_name  TEXT,
    ref_type  TEXT
);

-- Extracted DDL plus the result of a syntax parse with sqlglot's Oracle
-- dialect. A failed parse is data for the assessment, not an error.
CREATE TABLE ddl (
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    ddl         TEXT,
    parse_ok    INTEGER NOT NULL,
    parse_error TEXT,
    PRIMARY KEY (owner, name, type)
);

-- Constraint facts. Type is Oracle's single letter: P primary key,
-- R referential, U unique, C check. Check conditions live in a
-- separate table because they arrive through a different channel
-- (the source column is a LONG).
CREATE TABLE constraints (
    owner           TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    type            TEXT,
    status          TEXT,
    ref_owner       TEXT,
    ref_constraint  TEXT,
    delete_rule     TEXT,
    PRIMARY KEY (owner, constraint_name)
);

CREATE TABLE constraint_columns (
    owner           TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    column_name     TEXT NOT NULL,
    position        INTEGER,
    PRIMARY KEY (owner, constraint_name, column_name)
);

CREATE TABLE check_conditions (
    owner           TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    condition       TEXT,
    truncated       INTEGER,
    PRIMARY KEY (owner, constraint_name)
);

CREATE TABLE indexes (
    owner      TEXT NOT NULL,
    index_name TEXT NOT NULL,
    table_name TEXT,
    index_type TEXT,
    uniqueness TEXT,
    status     TEXT,
    generated  TEXT,
    PRIMARY KEY (owner, index_name)
);

CREATE TABLE index_columns (
    owner       TEXT NOT NULL,
    index_name  TEXT NOT NULL,
    column_name TEXT,
    position    INTEGER,
    PRIMARY KEY (owner, index_name, position)
);

-- Function-based index expressions, read from a LONG and truncated to
-- what old DBMS_OUTPUT allows; presence matters more than fidelity.
CREATE TABLE index_expressions (
    owner      TEXT NOT NULL,
    index_name TEXT NOT NULL,
    position   INTEGER NOT NULL,
    expression TEXT,
    truncated  INTEGER,
    PRIMARY KEY (owner, index_name, position)
);

CREATE TABLE part_tables (
    owner               TEXT NOT NULL,
    table_name          TEXT NOT NULL,
    partitioning_type   TEXT,
    subpartitioning_type TEXT,
    partition_count     INTEGER,
    interval            TEXT,
    PRIMARY KEY (owner, table_name)
);

CREATE TABLE part_key_columns (
    owner       TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    column_name TEXT,
    position    INTEGER NOT NULL,
    PRIMARY KEY (owner, table_name, position)
);

CREATE TABLE synonyms (
    owner        TEXT NOT NULL,
    synonym_name TEXT NOT NULL,
    table_owner  TEXT,
    table_name   TEXT,
    db_link      TEXT,
    PRIMARY KEY (owner, synonym_name)
);

CREATE TABLE triggers (
    owner            TEXT NOT NULL,
    trigger_name     TEXT NOT NULL,
    trigger_type     TEXT,
    triggering_event TEXT,
    table_name       TEXT,
    status           TEXT,
    PRIMARY KEY (owner, trigger_name)
);

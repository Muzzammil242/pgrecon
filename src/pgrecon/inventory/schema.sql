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

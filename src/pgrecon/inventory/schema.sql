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
    degree      TEXT,
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
-- parse_quality records how deep the parse went: 'full' when a real
-- syntax tree came back, 'fallback' when sqlglot accepted the text
-- only as an opaque command, which usually flags exotic syntax.
CREATE TABLE ddl (
    owner         TEXT NOT NULL,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL,
    ddl           TEXT,
    parse_ok      INTEGER NOT NULL,
    parse_error   TEXT,
    parse_quality TEXT,
    PRIMARY KEY (owner, name, type)
);

CREATE TABLE db_links (
    owner    TEXT NOT NULL,
    db_link  TEXT NOT NULL,
    username TEXT,
    host     TEXT,
    PRIMARY KEY (owner, db_link)
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
    degree     TEXT,
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

CREATE TABLE part_subkey_columns (
    owner       TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    column_name TEXT,
    position    INTEGER NOT NULL,
    PRIMARY KEY (owner, table_name, position)
);

-- Partition bounds. HIGH_VALUE is a LONG in the dictionary, read
-- through the same PL/SQL chunker as check conditions; a bound
-- longer than the chunk is flagged truncated and the converter
-- declines it rather than emitting a wrong one.
CREATE TABLE part_partitions (
    owner          TEXT NOT NULL,
    table_name     TEXT NOT NULL,
    partition_name TEXT NOT NULL,
    position       INTEGER,
    high_value     TEXT,
    truncated      INTEGER,
    PRIMARY KEY (owner, table_name, partition_name)
);

CREATE TABLE part_subpartitions (
    owner             TEXT NOT NULL,
    table_name        TEXT NOT NULL,
    partition_name    TEXT NOT NULL,
    subpartition_name TEXT NOT NULL,
    position          INTEGER,
    high_value        TEXT,
    truncated         INTEGER,
    PRIMARY KEY (owner, table_name, partition_name, subpartition_name)
);

-- Sequence bounds stay text: Oracle allows values to 1e28, past any
-- integer type here; the converter validates ranges when emitting.
CREATE TABLE sequences (
    owner         TEXT NOT NULL,
    sequence_name TEXT NOT NULL,
    min_value     TEXT,
    max_value     TEXT,
    increment_by  TEXT,
    cycle_flag    TEXT,
    cache_size    TEXT,
    last_number   TEXT,
    PRIMARY KEY (owner, sequence_name)
);

-- Column defaults and virtual-column expressions, read from a LONG
-- through the chunked path; truncated expressions are declined by
-- the converter rather than guessed at.
CREATE TABLE column_defaults (
    owner        TEXT NOT NULL,
    table_name   TEXT NOT NULL,
    column_name  TEXT NOT NULL,
    default_text TEXT,
    virtual      TEXT,
    truncated    INTEGER,
    PRIMARY KEY (owner, table_name, column_name)
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

CREATE TABLE plsql_units (
    owner       TEXT NOT NULL,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    parse_mode  TEXT NOT NULL,
    error_count INTEGER NOT NULL,
    first_error TEXT,
    PRIMARY KEY (owner, name, type)
);

CREATE TABLE plsql_features (
    owner   TEXT NOT NULL,
    name    TEXT NOT NULL,
    type    TEXT NOT NULL,
    feature TEXT NOT NULL,
    line    INTEGER NOT NULL,
    detail  TEXT
);

CREATE TABLE plsql_calls (
    owner  TEXT NOT NULL,
    name   TEXT NOT NULL,
    type   TEXT NOT NULL,
    callee TEXT NOT NULL,
    line   INTEGER NOT NULL
);

CREATE TABLE part_indexes (
    owner      TEXT NOT NULL,
    index_name TEXT NOT NULL,
    table_name TEXT,
    locality   TEXT,
    PRIMARY KEY (owner, index_name)
);

CREATE TABLE mviews (
    owner           TEXT NOT NULL,
    mview_name      TEXT NOT NULL,
    rewrite_enabled TEXT,
    refresh_method  TEXT,
    query           TEXT,
    PRIMARY KEY (owner, mview_name)
);

CREATE TABLE plan_management (
    kind    TEXT NOT NULL,
    name    TEXT NOT NULL,
    enabled TEXT
);

CREATE TABLE grants (
    grantee    TEXT NOT NULL,
    owner      TEXT NOT NULL,
    table_name TEXT NOT NULL,
    privilege  TEXT NOT NULL,
    grantable  TEXT,
    PRIMARY KEY (grantee, owner, table_name, privilege)
);

CREATE TABLE table_comments (
    owner      TEXT NOT NULL,
    table_name TEXT NOT NULL,
    comments   TEXT,
    PRIMARY KEY (owner, table_name)
);

CREATE TABLE column_comments (
    owner       TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    column_name TEXT NOT NULL,
    comments    TEXT,
    PRIMARY KEY (owner, table_name, column_name)
);

CREATE TABLE nls_params (
    key   TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (key)
);

-- Database-wide license posture: edition banner, cpu counts. Facts
-- only; any interpretation of what they cost belongs to a human with
-- the client's contract in hand.
CREATE TABLE license_facts (
    key   TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (key)
);

-- DBA_FEATURE_USAGE_STATISTICS, database-wide by nature. Readable
-- with SELECT_CATALOG_ROLE; accounts without it produce an empty
-- table, never a failed load.
CREATE TABLE feature_usage (
    name            TEXT NOT NULL,
    version         TEXT,
    detected_usages INTEGER,
    currently_used  TEXT,
    last_usage      TEXT,
    PRIMARY KEY (name, version)
);

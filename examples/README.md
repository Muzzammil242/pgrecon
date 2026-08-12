# Example extraction dump

`dump_oracle21c/` is a real dump: the packaged extraction script
(`src/pgrecon/extract/pgrecon_extract.sql`) run by SQL*Plus against an
Oracle XE 21c instance (gvenzl/oracle-xe:21 container), spooling the
RECON_TEST schema. The files are byte-for-byte what SQL*Plus produced,
including the blank line that opens every spool.

The schema behind it is `tests/fixtures/synthetic/synthetic_schema.sql`,
written to concentrate the constructs that make Oracle to PostgreSQL
migrations expensive: a package with state and an initialization block,
compound and autonomous-transaction triggers, an interval-partitioned
table, LONG and XMLTYPE columns, a global temporary table, a
materialized view, a scheduler job, an object type, a function-based
index, a loopback database link, and hierarchical and (+) join views.

Load and assess it without any Oracle installation:

    uv run pgrecon load examples/dump_oracle21c --db sample.db
    uv run pgrecon report --db sample.db

Expected result: 29 objects, 41 findings, effort points 57.4.

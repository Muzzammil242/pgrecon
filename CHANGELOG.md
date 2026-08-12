# Changelog

Release notes are written by hand, grouped by area. Dates use YYYY-MM-DD.

## Unreleased

- Initial scaffold: project layout, CI, offline extract script,
  SQLite inventory schema, dump loader, PostgreSQL syntax check harness.
- Synthetic assessment schema covering the constructs that drive
  migration cost; used end to end against Oracle XE 21c.
- Loader hardened against real SQL*Plus output: the blank line that
  opens every spool, constraint-state keywords, identity column
  options, and the VIRTUAL marker on generated columns.
- Legacy extract script for Oracle 9.2 through 11.1: hand-built CSV
  for old SQL*Plus clients, catalog reconstruction instead of
  DBMS_METADATA. Verified end to end against Oracle XE 11g.

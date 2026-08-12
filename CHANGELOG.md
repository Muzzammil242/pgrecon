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
- Structured facts on both tiers: constraints with their columns and
  check conditions, indexes with columns and function-based
  expressions, partitioning strategy and key columns, synonym targets,
  trigger metadata. Verified against both containers.
- Runtime version guards in the standard script: a too-old client or
  server stops with a message pointing at the legacy variant instead
  of spooling a broken dump.
- pgrecon script --source-version picks the right variant from the
  Oracle version; --legacy remains as an explicit override.
- Rule engine with the first fifteen assessment rules over the
  inventory, and a report command printing findings by severity in
  text or JSON. Effort points are a provisional weight sum until the
  effort model lands.

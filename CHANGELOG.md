# Changelog

Release notes are written by hand, grouped by area. Dates use YYYY-MM-DD.

## 0.1.0 - 2026-08-13

First public release: offline extraction, a queryable inventory, and a
49-rule assessment engine, verified end to end against real Oracle XE
11g and 21c instances.

Extraction

- Offline SQL*Plus script over dictionary views only; SELECT
  statements a DBA can review line by line. DDL via DBMS_METADATA,
  structured facts (constraints, indexes, partitioning, synonyms,
  triggers, database links) via dedicated spools. LONG-typed dictionary
  columns (check conditions, index expressions) read through PL/SQL
  chunkers.
- Legacy script variant for Oracle 9.2 through 11.1: hand-built CSV
  for old SQL*Plus clients, DDL reconstructed from the catalog instead
  of DBMS_METADATA, byte-safe line chunking for pre-10.2 DBMS_OUTPUT
  limits.
- Runtime guards stop a too-old client or server with a message
  pointing at the right variant instead of spooling a broken dump.
  pgrecon script --source-version picks the variant automatically.
- Scripts instruct the DBA to export NLS_LANG=.AL32UTF8 so dumps spool
  as UTF-8 regardless of the database character set.

Inventory

- SQLite database with seventeen fact tables covering objects, tables,
  columns, source, dependencies, features, DDL, constraints and their
  columns, check conditions, indexes with columns and expressions,
  partitioning, synonyms, triggers, and database links.
- Extracted DDL is parsed with sqlglot's Oracle dialect. The stored
  text stays verbatim; parsing runs on a normalized copy that strips
  DBMS_METADATA artifacts (constraint-state keywords, identity column
  options, the VIRTUAL marker). Parse failures and opaque fallback
  parses are recorded as data.
- Loads tolerate partial dumps and real SQL*Plus quirks such as the
  blank line that opens every spool.
- Dumps in any encoding load without crashing: undecodable bytes
  degrade to replacement characters and leave a warning row in the
  inventory, and pgrecon load --encoding recovers full fidelity when
  the code page is known. Verified with Korean, Chinese, Japanese,
  Hebrew, Arabic, Cyrillic, and German object names.

Rules

- 49 deterministic rules across data types, storage, PL/SQL code, SQL
  constructs, package structure, system package usage, and schema
  objects. Every rule ships with fixture tests.
- Findings carry a stable rule id, severity, the object, and the
  evidence seen, including source line numbers for code findings.
- Parse failures surface as findings (R-DDL-01, R-DDL-02) so nothing
  drops out of the assessment silently.

CLI

- pgrecon script, load, report, and info. Reports print text or JSON;
  the JSON payload includes a severity summary and a provisional
  effort-point total.
- A bundled example dump (examples/dump_oracle21c, extracted from a
  real Oracle XE 21c instance) makes the whole pipeline runnable
  without an Oracle installation.

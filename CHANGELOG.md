# Changelog

Release notes are written by hand, grouped by area. Dates use YYYY-MM-DD.

## 0.1.1 - 2026-08-14

Packaging and attribution; no behavior changes.

- The unused PostgreSQL-syntax validation helper and its pglast
  dependency are removed from the core. pglast is GPL-3.0 licensed,
  which does not belong in the requirements of an Apache-2.0
  package; server-grade validation returns with the report layer,
  where it can live under its own terms.
- A NOTICE file attributes the vendored grammars-v4 PL/SQL parser,
  and the README acknowledges the projects pgrecon builds on.

## 0.1.0 - 2026-08-14

First public release: offline extraction, a queryable inventory, and a
61-rule assessment engine, verified end to end against real Oracle XE
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
- Performance posture is extracted: partitioned-index locality,
  per-object parallel degree, query-rewrite and refresh settings of
  materialized views, and SQL plan baselines and stored outlines
  (outlines only on the legacy tier).
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

PL/SQL analysis

- Stored units are parsed at load time with a full PL/SQL grammar
  (grammars-v4 via ANTLR, vendored as generated code so installation
  never needs Java). Parsing tries fast SLL prediction first, retries
  in full LL only when that bails, and records the outcome per unit.
- A tree walk plus a token-channel scan store migration-relevant
  facts in the inventory: transaction control, dynamic SQL, GOTO,
  FORALL, collection types, autonomous transactions, swallowed
  exceptions, SYSDATE, DECODE, ROWNUM, pipelined functions, implicit
  cursor attributes, CONNECT BY, and (+) joins.
- Code rules read those facts first, so constructs sitting in
  comments or string literals stop producing findings. Units that
  fail to parse keep token-level coverage, and inventories loaded by
  older versions still report through the same fallback.
- Call sites land in a plsql_calls table (caller, callee, line): the
  supplied-package rules read it instead of matching text, and it is
  the raw material for dependency clustering in the report stage.

Rules

- 61 deterministic rules across data types, storage, PL/SQL code, SQL
  constructs, package structure, system package usage, schema
  objects, and performance. Every rule ships with fixture tests.
- ROWID, UROWID, and BFILE columns get type rules, and ROWID usage in
  code is read from the token stream: ctid is not a stable row
  address, and BFILE has no counterpart at all.
- The empty-string trap gets its own rule: Oracle treats '' as NULL
  and PostgreSQL does not, so every empty-string literal is a site
  where behavior changes silently. The lexer tells a real '' from the
  escaped quote in 'don''t', which text matching cannot.
- The performance category starts with optimizer hints: statements
  tuned by hand for Oracle's planner are marked for a fresh plan on
  PostgreSQL instead of a blind rewrite.
- Findings carry a stable rule id, severity, the object, and the
  evidence seen, including source line numbers for code findings.
- Parse failures surface as findings (R-DDL-01, R-DDL-02) so nothing
  drops out of the assessment silently.

CLI

- pgrecon script, load, report, and info. Reports print text or JSON;
  the JSON payload includes a severity summary and a provisional
  effort-point total.
- pgrecon -v logs progress and per-unit parse warnings to stderr;
  stdout stays clean for report output, and logs never carry PL/SQL
  body text.
- Remedies are part of the output: report --remedies appends each
  fired rule's guidance with its helping extension, pgrecon explain
  shows one rule's writeup or lists the catalog, and the JSON payload
  carries a rules map with title, severity, effort, remedy, and
  extension for every rule that fired.
- pgrecon estimate prices the migration in person-days from named
  components: baseline, schema conversion, finding remediation with
  severity-dependent repetition discounts, code volume, and data
  movement, with a testing-and-stabilization factor range on top.
  Every run prints its assumptions, and the JSON output carries the
  same breakdown.
- A bundled example dump (examples/dump_oracle21c, extracted from a
  real Oracle XE 21c instance) makes the whole pipeline runnable
  without an Oracle installation.

# Changelog

Release notes are written by hand, grouped by area. Dates use YYYY-MM-DD.

## Unreleased

- Materialized views convert for real when the dump carries their
  defining query: CREATE MATERIALIZED VIEW with the container's
  column names, the query through the same translation and guards as
  views, and notes for the refresh method and query rewrite.
  Constraints, foreign keys, and triggers that target a materialized
  view refuse by name - PostgreSQL does not allow them there.
  Query-less dumps keep the container-table behavior.
- Ten rules from the field close the gap catalog at 74: MODEL,
  PIVOT/UNPIVOT, flashback queries, multi-table INSERT, WITH
  FUNCTION, SQL macros, invisible columns, read-only tables,
  DEFAULT ON NULL, and materialized view logs. The SQL constructs
  detect at the token level, so a PIVOT in a comment stays silent.
- pgrecon runbook generates the data-movement artifacts: a data-only
  ora2pg configuration, row-count and spot-sum validation SQL for
  both engines, post-load sequence alignment, materialized view
  refresh and ANALYZE steps, and the cutover checklist. The tool
  still never connects to a database; it directs the move instead.
- The extraction scripts capture license posture and the two facts
  that were LONG-locked. license.csv carries the edition banner and
  cpu counts; feature_usage.csv carries DBA_FEATURE_USAGE_STATISTICS
  (both need SELECT_CATALOG_ROLE and degrade to empty files without
  it). Materialized views now arrive with their defining query, and
  partitions with their full HIGH_VALUE - complete in the modern
  script via SET LONG, and in the legacy script through the same
  PL/SQL streaming the view DDL already used, where HIGH_VALUE keeps
  the 180-byte cut with its truncated flag. The inventory gains
  license_facts and feature_usage tables and a query column on
  mviews.

## 0.4.0 - 2026-08-21

- CONNECT BY views convert to WITH RECURSIVE: one table, one PRIOR
  equality, projections of plain columns, LEVEL, and
  SYS_CONNECT_BY_PATH with a literal separator. START WITH filters
  the base branch, a WHERE applies after the hierarchy as Oracle
  evaluates it, and a hidden key column carries the parent join so
  the projection list does not have to. NOCYCLE, ORDER SIBLINGS BY,
  joins, and PRIOR expressions refuse by name. Verified row-for-row
  against a live Oracle database running the original view.
- DECODE translates with Oracle's null rules intact: an empty-string
  argument is a NULL search, result, or default, so it becomes IS
  NULL or a NULL literal instead of a comparison against '' that
  could never match. Literal searches keep plain equality; a column
  search carries the both-NULL match DECODE gives it.
- Views over JSON_TABLE refuse by name instead of surfacing a parser
  error: PostgreSQL adds JSON_TABLE in version 17 with different
  clause syntax, and the residue line now says so.
- Materialized views stop converting silently: DBMS_METADATA hands
  them over as container tables, so the table still converts and a
  residue line now names the loss - the defining query is not in the
  inventory, refresh must be scheduled by hand, and query rewrite has
  no PostgreSQL counterpart.

## 0.3.0 - 2026-08-20

- Triggers convert: a simple DML trigger becomes a trigger function
  plus the CREATE TRIGGER statement PostgreSQL wants. :NEW and :OLD
  lose their colons, INSERTING/UPDATING/DELETING become TG_OP tests,
  bare RETURN gains the row result, UPDATE OF column lists survive
  from the parse tree, WHEN clauses translate through the same
  folding as views, and disabled triggers stay disabled via ALTER
  TABLE. Compound triggers, INSTEAD OF, system triggers, and
  UPDATING('column') refuse by name; sequence-fed triggers convert
  and carry a note pointing at generated identity columns.
- Concatenation carries Oracle's NULL semantics: every || chain
  becomes NULLIF(concat(...), ''), in PL/SQL bodies and trigger
  functions through the mechanical rewriter and in views, check
  conditions, defaults, and trigger WHEN clauses through the
  expression folding. Oracle treats NULL as the empty string where
  PostgreSQL || yields NULL; concat() ignores NULLs, and NULLIF
  restores the one case Oracle does return NULL - every part empty.
  Inner rewrites (SYSDATE, NVL, bind folding) compose inside the
  operands, and Oracle's CONCAT() function folds the same way.
- Five emission guards from a nine-schema live sweep: Oracle identity
  columns (ISEQ$$ defaults) become integer identity columns instead of
  leaking their internal sequence reference; SYSTIMESTAMP folds to
  CURRENT_TIMESTAMP in expressions; SYS_OP_* internal functions refuse
  in defaults and index expressions; Oracle's I_SNAP$ materialized
  view support indexes are skipped with a note; object views refuse by
  name. Database links now ship as a commented oracle_fdw recipe
  rather than live DDL, keeping every emitted statement applicable on
  a vanilla server. Divisions in folded expressions cast their
  numerator to decimal - Oracle NUMBER arithmetic is exact decimal,
  where the generator's double precision broke two-argument ROUND.

## 0.2.1 - 2026-08-19

- Bare procedure-call statements become CALL statements with the
  parentheses CALL requires, resolved against the extracted
  procedures.
- Two more provable code rewrites: EXIT WHEN cursor%NOTFOUND directly
  after a FETCH of the same cursor becomes EXIT WHEN NOT FOUND, which
  is what plpgsql's FOUND reports at that point; and :name bind
  placeholders inside EXECUTE IMMEDIATE literals fold to numbered
  parameters when their count matches the USING arity, because Oracle
  binds them by position exactly as PostgreSQL numbers them. OUT bind
  arguments refuse; mismatched counts stay verbatim under the
  existing verify-by-hand note.
- Sized character declarations in code (VARCHAR2(200) and friends)
  now map; the size pattern never matched type names containing a
  digit, so they were refused as unsupported.

## 0.2.0 - 2026-08-19

- The converter grows a code lane: standalone functions and
  procedures whose every construct is provably equivalent convert
  mechanically to PL/pgSQL - headers, parameter modes and defaults,
  a documented type mapping for declarations, cursor declarations,
  cursor%ROWTYPE as record variables, NVL to COALESCE, SYSDATE to
  CURRENT_TIMESTAMP, sequence NEXTVAL to nextval validated against
  extracted sequences, DBMS_OUTPUT.PUT_LINE to RAISE NOTICE,
  EXECUTE IMMEDIATE to EXECUTE, q-quoted literals, FROM DUAL
  removal, and exception conditions mapped only where behavior
  matches (DUP_VAL_ON_INDEX, ZERO_DIVIDE). Comments and formatting
  survive, because edits splice the original source. Everything
  semantic refuses by name and line into the residue report -
  autonomous transactions, REF CURSOR, BULK COLLECT and FORALL,
  collections, CONNECT BY, ROWNUM, DECODE, cursor attributes,
  unproven calls and anchors - and a unit that calls a refused unit
  refuses with it. Function bodies validate on the target with
  check_function_bodies on, never disabled.
- Expression guards walk the re-parsed syntax tree instead of
  matching text, so a string literal that merely mentions SYS_GUID
  stays innocent while real calls still decline, and TO_DATE guards
  inspect the actual first argument.
- The converter covers the rest of schema structure: sequences
  restarted at their extracted position with bigint-safe bounds,
  schema-local synonyms as updatable views, database links
  scaffolded as oracle_fdw servers awaiting credentials, column
  defaults translated through the same folding as views (SYSDATE
  becomes CURRENT_TIMESTAMP), and virtual columns as PostgreSQL
  generated columns. Defaults with no PostgreSQL counterpart, such
  as SYS_GUID, decline by name instead of failing on the target.
- pgrecon convert begins: schema structure to PostgreSQL DDL, offline
  from the inventory's dictionary facts. Tables with a documented
  type mapping, primary and unique keys, checks, and foreign keys;
  everything the converter cannot port faithfully lands in a residue
  report naming the object and the reason instead of becoming wrong
  DDL. Global temporary tables are residue with a pointer to pgtt.
- Partition bounds are extracted (HIGH_VALUE through the same chunked
  path as check conditions, subpartitions and subpartition keys
  included) and converted to native partition children: RANGE with
  correct LESS-THAN to FROM/TO translation and MAXVALUE, LIST with
  DEFAULT partitions, HASH with MODULUS/REMAINDER, and composite
  shapes. A bound the converter cannot translate faithfully omits
  that table's whole child set with a named reason; interval-driven
  creation carries a note pointing at scheduled creation such as
  pg_partman.

## 0.1.5 - 2026-08-18

- Conditional compilation is handled and flagged (R-SRC-21): $IF
  directives are blanked before parsing so every branch's code stays
  analyzed, inquiry references such as $$plsql_unit parse as
  expressions, and the directive itself becomes a finding, because
  the port has to pick a branch. 64 rules.
- Object-type methods with DEFAULT parameter values and type
  declarations carrying OID identity clauses no longer count as
  parse failures; both are legal Oracle the vendored grammar
  predates. Found by feeding pljson, Logger, utPLSQL, and the legacy
  Oracle sample schemas through the tool.

## 0.1.4 - 2026-08-18

Fixes from an independent code review; thanks to its author.

- Indexes whose GENERATED flag arrives NULL from a partial dump no
  longer silently escape the function-based and global-index rules.
- The effort baseline no longer scales per table: environments and
  cutover scaffolding do not grow linearly with table count, and at
  estate scale the old rate produced an indefensible number. The
  baseline is flat; per-object work stays in schema conversion where
  it belongs.
- The effort rates are described as what they are: the author's
  field defaults, uncited and visible, to be calibrated per
  engagement.
- The import boundary check now also covers the commercial report
  package, so deterministic code cannot grow a dependency on it.
- orafce is credited on the rules it genuinely helps: UTL_FILE,
  DBMS_OUTPUT, and DECODE.
- A hand-mangled numeric field in a dump degrades to a missing value
  instead of aborting the load, and pgrecon load says out loud that
  it replaces an existing database file.
- The SQL% fallback grep no longer matches PLSQL%.

## 0.1.3 - 2026-08-15

- Wrapped PL/SQL gets its own rule (R-SRC-20): a wrapped unit is
  obfuscated bytecode with nothing to assess from the database, so it
  is reported as needing its original source instead of producing a
  parse failure and garbage token matches. 63 rules.
- Assessment scale is measured: a synthetic estate of 5,000 tables
  and 100,000 lines of PL/SQL across 1,600 stored units, including a
  16,000-line package body, loads and deep-parses in under two
  minutes and reports in seconds. tools/make_scale_dump.py generates
  the estate, so the measurement is reproducible.

## 0.1.2 - 2026-08-15

- Table DDL as DBMS_METADATA emits it in the field now parses:
  spelled-out partition specification lists, DEFERRABLE constraint
  states, INTERVAL column types with spaced precision, LONG RAW, and
  virtual column visibility markers no longer count as parse
  failures. Found by assessing real extracted corpora, including
  Oracle's official sample schemas.
- Evolved object types are handled and flagged: DBA_SOURCE lists the
  CREATE and the ALTER TYPE statements that changed it in one
  listing, which used to defeat the parse. The original definition
  now parses alone and the evolution is a finding of its own
  (R-OBJ-09), because in-place type evolution has no PostgreSQL
  equivalent. 62 rules.
- XDB's machine-generated helper triggers (PURCHASEORDER$xd and
  friends) are recorded as generated instead of parse failures; they
  are Oracle's machinery, not user code to port.

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

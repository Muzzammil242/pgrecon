# <img src=".github/logo.svg" width="32" alt=""> pgrecon

[![CI](https://github.com/Muzzammil242/pgrecon/actions/workflows/ci.yml/badge.svg)](https://github.com/Muzzammil242/pgrecon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pgrecon.svg)](https://pypi.org/project/pgrecon/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Migration reconnaissance for PostgreSQL. pgrecon inventories an Oracle
database from an offline dump and runs a deterministic rule engine over
it, reporting the constructs that decide the real cost of a move:
package-level state, autonomous transactions, LONG columns, interval
partitioning, database links, and several dozen other things that
surface late and expensively when nobody looks for them first. The
same inventory drives an offline converter that emits PostgreSQL DDL
for everything it can prove and a named refusal for everything it
cannot.

pgrecon never connects to the database. A reviewable SQL*Plus script is
run by the DBA with a read-only account; only files cross the boundary.
The analysis side needs Python 3.11 or newer; the extraction side needs
nothing but SQL*Plus.

## How it works

    pgrecon script   ->  extraction script, reviewed and run by the DBA
    dump folder      ->  pgrecon load    ->  local SQLite inventory
    inventory        ->  pgrecon report  ->  findings by severity
    inventory        ->  pgrecon convert ->  PostgreSQL DDL + residue

Every finding is produced by a rule with a stable id running a query
against the inventory. Same dump in, same findings out; nothing is
estimated by guesswork. DDL that fails to parse is itself recorded and
reported as a finding rather than silently skipped.

## Try it without an Oracle database

The repository bundles a real extraction dump, taken by the packaged
script from an Oracle XE 21c instance loaded with a deliberately nasty
schema (see [examples/dump_oracle21c](examples/dump_oracle21c)):

    git clone https://github.com/Muzzammil242/pgrecon
    cd pgrecon
    uv sync
    uv run pgrecon load examples/dump_oracle21c --db sample.db
    uv run pgrecon report --db sample.db

Output (excerpt):

    high    R-OBJ-01   LOOPBACK                    to //localhost:1521/XEPDB1 as RECON_TEST
    high    R-PART-01  SALES                       INTERVAL NUMTOYMINTERVAL(1, 'MONTH')
    high    R-PERF-02  SALES_AMOUNT_GIX            GLOBAL partitioned index on SALES
    high    R-PKG-01   PKG_LEDGER                  2 package-level declaration(s), first at line 2
    high    R-PKG-01   PKG_LEDGER (body)           1 package-level declaration(s), first at line 2
    high    R-SYS-01   ARCHIVE_NOTES               UTL_FILE (first at line 16)
    high    R-TRG-01   TRG_EMP_SAL_GUARD           on EMP
    high    R-TRG-02   TRG_EMP_AUDIT               PRAGMA AUTONOMOUS_TRANSACTION (first at line 5)
    high    R-TYPE-01  LEGACY_NOTES.BODY           LONG
    high    R-TYPE-07  LEGACY_REFS.SCAN_DOC        BFILE
    medium  R-OBJ-02   NIGHTLY_ROLLUP              scheduler job
    ...

    57 findings (10 high, 18 medium, 16 low, 13 info); effort points 77.2

Add `--remedies` to append what to do about each fired rule, or ask
about one directly: `uv run pgrecon explain R-PKG-01`.

## Assessing a real database

1. Generate the extraction script for the source version:

       pgrecon script --source-version 19

2. Hand `pgrecon_extract.sql` to the DBA. It is plain SQL*Plus, SELECT
   only, against dictionary views; it is meant to be read before it is
   run:

       sqlplus readonly_user@service @pgrecon_extract.sql SCHEMA_NAME

3. Load the returned dump folder and report:

       pgrecon load dump_dir --db inventory.db
       pgrecon report --db inventory.db
       pgrecon report --db inventory.db --format json > findings.json

   Pass -v to watch progress on stderr; loading parses every stored
   PL/SQL unit, which takes a few minutes on a large schema.

The extracting account needs SELECT_CATALOG_ROLE (or equivalent SELECT
grants on the dictionary views the script names).

### Character sets

Dumps are read as UTF-8. The script tells the DBA to set
`NLS_LANG=.AL32UTF8` before running it; when a dump was spooled in a
local code page anyway, pass it explicitly:

    pgrecon load dump_dir --encoding cp949

Bytes that do not decode degrade to replacement characters and leave a
warning in the inventory. A bad code page never crashes a load.

## Supported Oracle versions

| Source version     | Script                    | Status |
| ------------------ | ------------------------- | ------ |
| 11.2 and later     | `pgrecon script`          | Verified nightly in CI against Oracle XE 21c and Oracle Free 23ai |
| 9.2 through 11.1   | `pgrecon script --legacy` | Script verified nightly in CI against Oracle XE 11g; 9.2 to 11.1 servers by design, no containers exist |

The standard script needs a 12.2 or newer SQL*Plus client. The legacy
variant runs on the old sqlplus already sitting on the database host:
it uses no DBMS_METADATA and reconstructs DDL from the catalog, because
on old systems DBMS_METADATA is slow on tables when it works at all.
Both scripts carry runtime guards that stop with a clear message rather
than spool a broken dump, and `--source-version` picks the right
variant for you.

## What it checks

79 rules at present, each shipping with fixture tests:

| Category        | Rules | Among them |
| --------------- | ----- | ---------- |
| Environment     | 2     | character-set encoding decision, object grants to migrate |
| Data types      | 8     | LONG, XMLTYPE, ROWID and BFILE, SDO_GEOMETRY, TIMESTAMP WITH LOCAL TIME ZONE |
| Storage         | 12    | interval partitioning, global temporary tables, IOTs, read-only tables, bitmap and function-based indexes |
| PL/SQL code     | 18    | autonomous transactions, dynamic SQL, FORALL, collection types, the empty-string NULL trap |
| SQL constructs  | 13    | CONNECT BY, (+) outer joins, ROWNUM, MERGE, SYS_CONTEXT, the MODEL clause, PIVOT, flashback queries |
| Packages        | 2     | package-level state, initialization blocks |
| System packages | 5     | UTL_FILE, UTL_HTTP/SMTP/TCP, DBMS_SQL, DBMS_LOB, DBMS_OUTPUT |
| Schema objects  | 14    | database links and remote calls over them, scheduler jobs, materialized view logs, queues, evolved types, unparseable DDL |
| Performance     | 5     | optimizer hints, global indexes on partitioned tables, plan baselines, query-rewrite MVs |

Stored PL/SQL is parsed with a full grammar, and code findings come
from the syntax tree and token stream, never from comments or string
literals. A unit the parser rejects keeps token-level coverage and is
itself reported. The parse also records every call site into a
queryable call graph, which is what the supplied-package rules read:
UTL_FILE in a comment is not usage, UTL_FILE.FOPEN(...) is.

Findings carry the rule id, severity (info to blocker), the object, and
what was seen. Every rule also defines remedy guidance and the
PostgreSQL extension that helps (orafce, pgtt, and so on):
`pgrecon report --remedies` appends it for each fired rule, `pgrecon
explain R-PKG-01` prints one rule's writeup (bare `pgrecon explain`
lists the catalog), and the JSON payload carries the same metadata in
a rules map for integrations.

## Estimating effort

    uv run pgrecon estimate --db sample.db

    Migration effort estimate (person-days)

      baseline and environment       5.0
      schema conversion              1.7
      finding remediation           73.8
      PL/SQL porting by volume       0.8
      data movement                  0.0
      development subtotal          81.2

    With testing and stabilization:
      low 106, expected 130, high 179 person-days (5.0 to 8.5 person-months)

The estimate is a sum of named components, so it can be argued with
line by line, and it is a range, because a point estimate for a
migration is a lie. Repeated findings of one rule cost a
severity-dependent fraction of the first fix, testing and
stabilization is applied on top at the share field reports actually
describe, and every run prints its assumptions. The rates are a
deliberately conservative default calibration; treat the output as a
scoping instrument, not a quote.

## Converting

    uv run pgrecon convert --db sample.db

The converter writes two files from the same inventory, offline like
everything else. The first is PostgreSQL DDL for what it can prove:
tables under a documented type mapping (NUMBER stays exact, never a
float), keys, checks, foreign keys, secondary indexes, native
partition children for range, list, hash, and composite layouts,
views transpiled with (+) joins folded to ANSI, sequences restarted
at their extracted position, synonyms as views, database links
scaffolded as oracle_fdw servers, generated columns, and standalone
functions and procedures whose every construct has a provably
equivalent PL/pgSQL form - comments and formatting carried through,
SELECT INTO made STRICT so NO_DATA_FOUND still raises, function
bodies left to PostgreSQL's own validation rather than disabling it.

The second file is the residue: one line per declined object, naming
the construct and the line number. Packages, triggers, CONNECT BY,
autonomous transactions, REF CURSOR interfaces, BULK COLLECT - the
work that needs a person is refused by name, never guessed at, and a
routine that calls a refused routine is refused with it.

Two rules hold everywhere. Nothing invalid ships: CI applies the
bundled sample's conversion to live PostgreSQL 16, 17, and 18 on
every commit (the live-apply job in ci.yml), and development applies every change
the same way, check_function_bodies on, before it lands. Nothing is
lost silently: whatever the converter cannot carry faithfully becomes
a named residue line instead of quietly wrong output.

## Status

Alpha. The extraction scripts and inventory are stable; the rule
catalog is growing. Effort points in the report are relative weights
for sorting findings; person-day ranges come from pgrecon estimate
and its visible calibration. The converter has shipped since 0.2 and
now covers schema structure, views, materialized views, triggers,
grants, and comments end to end on the test estates; the code lane
deliberately converts only what it can prove.

Scale is measured, not hoped for: a synthetic estate of 5,000 tables
and 100,000 lines of PL/SQL across 1,600 stored units, one of them a
16,000-line package body, loads and deep-parses in under 40 seconds
on a laptop, and reporting runs in about two. The generator lives at
tools/make_scale_dump.py, so the measurement is reproducible.

## Development

    uv sync
    uv run pytest
    uv run ruff check .
    uv run mypy src

See [CONTRIBUTING.md](CONTRIBUTING.md) for the commit conventions and
how to add a rule. Every rule lands with its fixture test.

## Commercial support

The maintainer offers commercial migration assessment and delivery
through [DevCrafter](https://devcrafterai.com), built on this core:
narrative reports with per-finding remedies, effort estimation, and
hands-on Oracle to PostgreSQL migration work. The core stays open
under Apache-2.0. See [SUPPORT.md](SUPPORT.md) for the full support
and partner directory.

## Acknowledgements

pgrecon stands on excellent open source: the PL/SQL grammar from
[grammars-v4](https://github.com/antlr/grammars-v4) by Alexandre
Porcelli, Ivan Kochurkin, and Mark Adams, turned into a parser by
[ANTLR](https://www.antlr.org); Oracle-dialect SQL parsing by
[sqlglot](https://github.com/tobymao/sqlglot); the CLI by
[Typer](https://typer.tiangolo.com); and test infrastructure on
Gerald Venzl's
[Oracle XE container images](https://github.com/gvenzl/oci-oracle-xe).
Attributions are in [NOTICE](NOTICE).

## License

Apache-2.0. See [LICENSE](LICENSE).

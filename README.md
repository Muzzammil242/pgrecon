# pgrecon

[![CI](https://github.com/Muzzammil242/pgrecon/actions/workflows/ci.yml/badge.svg)](https://github.com/Muzzammil242/pgrecon/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Migration reconnaissance for PostgreSQL. pgrecon inventories an Oracle
database from an offline dump and runs a deterministic rule engine over
it, reporting the constructs that decide the real cost of a move:
package-level state, autonomous transactions, LONG columns, interval
partitioning, database links, and several dozen other things that
surface late and expensively when nobody looks for them first.

pgrecon never connects to the database. A reviewable SQL*Plus script is
run by the DBA with a read-only account; only files cross the boundary.
The analysis side needs Python 3.11 or newer; the extraction side needs
nothing but SQL*Plus.

## How it works

    pgrecon script   ->  extraction script, reviewed and run by the DBA
    dump folder      ->  pgrecon load   ->  local SQLite inventory
    inventory        ->  pgrecon report ->  findings by severity

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

    high    R-OBJ-01   LOOPBACK           to //localhost:1521/XEPDB1 as RECON_TEST
    high    R-PART-01  SALES              INTERVAL NUMTOYMINTERVAL(1, 'MONTH')
    high    R-PKG-01   PKG_LEDGER         2 package-level declaration(s), first at line 2
    high    R-PKG-01   PKG_LEDGER (body)  1 package-level declaration(s), first at line 2
    high    R-TRG-01   TRG_EMP_SAL_GUARD  on EMP
    high    R-TRG-02   TRG_EMP_AUDIT      PRAGMA AUTONOMOUS_TRANSACTION (first at line 5)
    high    R-TYPE-01  LEGACY_NOTES.BODY  LONG
    medium  R-OBJ-02   NIGHTLY_ROLLUP     scheduler job
    medium  R-SRC-01   PKG_LEDGER         EXECUTE IMMEDIATE (first at line 27)
    medium  R-TAB-01   STAGING_ROWS       GLOBAL TEMPORARY
    ...

    41 findings (7 high, 12 medium, 11 low, 11 info); effort points 57.4

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
| 11.2 and later     | `pgrecon script`          | Tested against Oracle XE 11g and 21c |
| 9.2 through 11.1   | `pgrecon script --legacy` | Best effort; validated by design, not by container |

The standard script needs a 12.2 or newer SQL*Plus client. The legacy
variant runs on the old sqlplus already sitting on the database host:
it uses no DBMS_METADATA and reconstructs DDL from the catalog, because
on old systems DBMS_METADATA is slow on tables when it works at all.
Both scripts carry runtime guards that stop with a clear message rather
than spool a broken dump, and `--source-version` picks the right
variant for you.

## What it checks

49 rules at present, each shipping with fixture tests:

| Category        | Rules | Among them |
| --------------- | ----- | ---------- |
| Data types      | 5     | LONG, XMLTYPE, TIMESTAMP WITH LOCAL TIME ZONE, bare NUMBER |
| Storage         | 9     | interval partitioning, global temporary tables, IOTs, bitmap and function-based indexes |
| PL/SQL code     | 11    | autonomous transactions, dynamic SQL, GOTO, commit inside triggers, swallowed exceptions |
| SQL constructs  | 6     | CONNECT BY, (+) outer joins, ROWNUM, MERGE, DECODE null handling |
| Packages        | 2     | package-level state, initialization blocks |
| System packages | 5     | UTL_FILE, UTL_HTTP/SMTP/TCP, DBMS_SQL, DBMS_LOB, DBMS_OUTPUT |
| Schema objects  | 11    | database links, scheduler jobs, materialized views, queues, VPD policies, unparseable DDL |

Findings carry the rule id, severity (info to blocker), the object, and
what was seen. The JSON output adds a summary with counts by severity
and a provisional effort-point total. Each rule also defines remedy
guidance and the PostgreSQL extension that helps (orafce, pgtt, and so
on); surfacing those in a narrative report is where the project is
headed next.

## Status

Alpha. The extraction scripts and inventory are stable; the rule
catalog is growing. Source-level rules currently work at token level,
which is deliberate and conservative; a full PL/SQL parse is the next
milestone and will sharpen the code rules. Effort points are relative
weights for comparing findings, not hours.

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
under Apache-2.0.

## License

Apache-2.0. See [LICENSE](LICENSE).

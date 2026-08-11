# pgrecon

Migration reconnaissance for PostgreSQL.

pgrecon inventories an Oracle database and assesses what it will take to
move it to PostgreSQL: object counts, data types, PL/SQL constructs,
feature usage, and the compatibility risks that decide the real cost of
a migration. Findings are produced by deterministic rules over a local
inventory; nothing is estimated by guesswork.

Status: early development, not yet released.

## How it works

    offline extract script  ->  dump folder  ->  local inventory (SQLite)
                                                      |
                                              rule engine -> findings

1. `pgrecon script` writes a reviewable SQL*Plus script. The client DBA
   inspects it, runs it with a read-only account, and returns the dump
   folder. No direct database access is required.
2. `pgrecon load DUMP_DIR` parses the dump into a local SQLite
   inventory, including a syntax parse of extracted DDL.
3. `pgrecon info` summarizes the inventory. The rule engine and report
   stages build on top of it.

## Development

Requires Python 3.11 or newer, and uv.

    uv sync
    uv run pytest
    uv run ruff check .
    uv run mypy src

See CONTRIBUTING.md for conventions.

## License

Apache-2.0. See LICENSE.

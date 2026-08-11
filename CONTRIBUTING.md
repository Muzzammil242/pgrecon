# Contributing

## Build and test

Requires Python 3.11 or newer, and uv.

    uv sync
    uv run pytest
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy src
    uv run pre-commit install    # once, to enable the local hooks

## Commit conventions

Commit style follows the PostgreSQL and Linux kernel projects, not
"conventional commits".

    area: short imperative summary, no trailing period

    Body wrapped at 72 columns. State the problem, then the fix and the
    reasoning. Complete sentences. The message must make sense without
    the diff.

- Area prefixes: extract, inventory, rules, report, cli, docs, build,
  tests.
- One logical change per commit. No "WIP", no "misc", no "update file".
- Plain ASCII everywhere: source, comments, docs, commit messages.
  No emoji, no unicode symbols. Test fixtures are the only exemption,
  and only for encoding-related tests.
- History is linear: rebase onto main and fast-forward. No merge
  commits.

## Code conventions

- Comments explain why, not what. Dense where logic is subtle, absent
  where the code is obvious.
- Catch the exception you expect; never a bare except; never swallow an
  error silently. A parse failure is recorded data, not a crash.
- No dead code, no commented-out blocks, no speculative abstractions.
- SQL uses bound parameters. Identifier quoting goes through a shared
  helper.

## Adding a rule

Every rule ships with fixture tests: sample input in tests/fixtures and
an assertion of the expected findings. A rule without tests will not be
merged.

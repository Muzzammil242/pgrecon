"""Command-line interface."""

import json
import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from pgrecon import __version__
from pgrecon.extract import needs_legacy, script_text
from pgrecon.inventory import load_dump
from pgrecon.rules.engine import run_rules, summarize

# sqlglot logs a warning whenever exotic syntax makes it fall back to an
# opaque statement; the outcome is already recorded in the inventory, so
# the console noise helps nobody.
logging.getLogger("sqlglot").setLevel(logging.ERROR)

app = typer.Typer(
    help="Migration reconnaissance for PostgreSQL.",
    no_args_is_help=True,
    add_completion=False,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"pgrecon {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Print the version and exit.",
        ),
    ] = False,
) -> None:
    pass


@app.command()
def script(
    out: Annotated[
        Path, typer.Option(help="Where to write the extraction script.")
    ] = Path("pgrecon_extract.sql"),
    source_version: Annotated[
        str | None,
        typer.Option(
            "--source-version",
            help="Oracle version of the source, e.g. 9.2, 11.2, 19."
            " Picks the right script variant.",
        ),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            help="Force the variant for Oracle 9.2-11.1 or old clients.",
        ),
    ] = False,
) -> None:
    """Write the offline SQL*Plus extraction script for the client DBA."""
    if source_version is not None:
        try:
            legacy = legacy or needs_legacy(source_version)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
    if legacy and out.name == "pgrecon_extract.sql":
        out = out.with_name("pgrecon_extract_legacy.sql")
    out.write_text(script_text(legacy), encoding="ascii", newline="\n")
    typer.echo(f"Wrote {out}" + (" (legacy variant)" if legacy else ""))
    typer.echo("Run it as: sqlplus readonly_user@service @" + out.name + " SCHEMA")


@app.command()
def load(
    dump_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, help="Extraction dump folder."),
    ],
    db: Annotated[Path, typer.Option(help="Inventory database to create.")] = Path(
        "inventory.db"
    ),
) -> None:
    """Load an extraction dump into a local SQLite inventory."""
    counts = load_dump(dump_dir, db)
    width = max(len(name) for name in counts)
    for name, count in sorted(counts.items()):
        typer.echo(f"{name:<{width}}  {count}")
    typer.echo(f"Inventory written to {db}")


@app.command()
def report(
    db: Annotated[
        Path,
        typer.Option(exists=True, dir_okay=False, help="Inventory database."),
    ] = Path("inventory.db"),
    fmt: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
) -> None:
    """Run the assessment rules and print the findings."""
    findings = run_rules(db)
    summary = summarize(findings)

    if fmt == "json":
        payload = {"summary": summary, "findings": [asdict(f) for f in findings]}
        typer.echo(json.dumps(payload, indent=2))
        return
    if fmt != "text":
        raise typer.BadParameter("format must be text or json")

    if not findings:
        typer.echo("No findings.")
        return
    widths = (
        max(len(f.severity.value) for f in findings),
        max(len(f.rule_id) for f in findings),
        max(len(f.name) for f in findings),
    )
    for f in findings:
        typer.echo(
            f"{f.severity.value:<{widths[0]}}  {f.rule_id:<{widths[1]}}"
            f"  {f.name:<{widths[2]}}  {f.detail}"
        )
    typer.echo("")
    parts = [f"{n} {sev}" for sev, n in summary["by_severity"].items()]
    typer.echo(
        f"{summary['findings']} findings ({', '.join(parts)});"
        f" effort points {summary['effort_points']}"
    )


@app.command()
def info(
    db: Annotated[
        Path,
        typer.Option(exists=True, dir_okay=False, help="Inventory database."),
    ] = Path("inventory.db"),
) -> None:
    """Summarize an inventory database."""
    conn = sqlite3.connect(db)
    try:
        for key, value in conn.execute("SELECT key, value FROM meta ORDER BY key"):
            typer.echo(f"{key}: {value}")
        rows = conn.execute(
            "SELECT type, COUNT(*) FROM objects GROUP BY type ORDER BY type"
        ).fetchall()
        if rows:
            typer.echo("objects:")
            for obj_type, count in rows:
                typer.echo(f"  {obj_type}: {count}")
        failed = conn.execute("SELECT COUNT(*) FROM ddl WHERE parse_ok = 0").fetchone()[
            0
        ]
        total = conn.execute("SELECT COUNT(*) FROM ddl").fetchone()[0]
        typer.echo(f"ddl parsed: {total - failed}/{total}")
    finally:
        conn.close()

"""Command-line interface."""

import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from pgrecon import __version__
from pgrecon.extract import script_text
from pgrecon.inventory import load_dump

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
) -> None:
    """Write the offline SQL*Plus extraction script for the client DBA."""
    out.write_text(script_text(), encoding="ascii", newline="\n")
    typer.echo(f"Wrote {out}")
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

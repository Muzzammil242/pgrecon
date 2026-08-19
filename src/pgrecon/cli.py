"""Command-line interface."""

import json
import logging
import sqlite3
import sys
import textwrap
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from pgrecon import __version__
from pgrecon.effort import estimate as build_estimate
from pgrecon.effort import person_months
from pgrecon.extract import needs_legacy, script_text
from pgrecon.inventory import load_dump
from pgrecon.rules import Rule, all_rules
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
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Log progress to stderr; repeat for debug detail.",
        ),
    ] = 0,
) -> None:
    # Logs go to stderr and never carry PL/SQL body text, so stdout
    # stays clean for reports and the log stays safe to share.
    logging.basicConfig(
        level=logging.WARNING - 10 * min(verbose, 2),
        stream=sys.stderr,
        format="%(levelname)s: %(message)s",
    )


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
    db: Annotated[
        Path,
        typer.Option(
            help="Inventory database to create. Replaces the file if it already exists."
        ),
    ] = Path("inventory.db"),
    encoding: Annotated[
        str,
        typer.Option(
            help="Encoding of the dump files, e.g. cp949 for a Korean"
            " Windows client. Defaults to UTF-8."
        ),
    ] = "utf-8-sig",
) -> None:
    """Load an extraction dump into a local SQLite inventory."""
    counts = load_dump(dump_dir, db, encoding)
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
    remedies: Annotated[
        bool,
        typer.Option(
            "--remedies",
            help="Append each fired rule's remedy to the text report.",
        ),
    ] = False,
) -> None:
    """Run the assessment rules and print the findings."""
    findings = run_rules(db)
    summary = summarize(findings)
    by_id = {rule.id: rule for rule in all_rules()}
    fired = {f.rule_id: by_id[f.rule_id] for f in findings}

    if fmt == "json":
        payload = {
            "summary": summary,
            "findings": [asdict(f) for f in findings],
            "rules": {
                rule_id: _rule_meta(rule) for rule_id, rule in sorted(fired.items())
            },
        }
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

    if remedies:
        counts = Counter(f.rule_id for f in findings)
        typer.echo("")
        typer.echo("Remedies:")
        for rule_id in dict.fromkeys(f.rule_id for f in findings):
            rule = fired[rule_id]
            n = counts[rule_id]
            tags = [rule.severity.value, f"{n} finding" + ("s" if n != 1 else "")]
            if rule.extension:
                tags.append(f"extension {rule.extension}")
            typer.echo("")
            typer.echo(f"{rule.id}  {rule.title}  [{', '.join(tags)}]")
            typer.echo(_wrap(rule.remedy))


def _rule_meta(rule: Rule) -> dict[str, object]:
    return {
        "title": rule.title,
        "category": rule.category,
        "severity": rule.severity.value,
        "effort": rule.effort,
        "remedy": rule.remedy,
        "extension": rule.extension,
    }


def _wrap(text: str) -> str:
    return textwrap.fill(text, width=76, initial_indent="  ", subsequent_indent="  ")


@app.command()
def estimate(
    db: Annotated[
        Path,
        typer.Option(exists=True, dir_okay=False, help="Inventory database."),
    ] = Path("inventory.db"),
    fmt: Annotated[
        str, typer.Option("--format", help="Output format: text or json.")
    ] = "text",
) -> None:
    """Estimate migration effort in person-days, as a range."""
    findings = run_rules(db)
    result = build_estimate(db, findings)

    if fmt == "json":
        payload = {
            "components": {c.label: c.person_days for c in result.components},
            "development_person_days": result.development,
            "person_days": {
                "low": result.low,
                "expected": result.expected,
                "high": result.high,
            },
            "person_months": {
                "low": person_months(result.low),
                "expected": person_months(result.expected),
                "high": person_months(result.high),
            },
            "assumptions": list(result.assumptions),
        }
        typer.echo(json.dumps(payload, indent=2))
        return
    if fmt != "text":
        raise typer.BadParameter("format must be text or json")

    typer.echo("Migration effort estimate (person-days)")
    typer.echo("")
    width = max(len(c.label) for c in result.components)
    for c in result.components:
        typer.echo(f"  {c.label:<{width}}  {c.person_days:8.1f}")
    typer.echo(f"  {'development subtotal':<{width}}  {result.development:8.1f}")
    typer.echo("")
    typer.echo("With testing and stabilization:")
    typer.echo(
        f"  low {result.low:.0f}, expected {result.expected:.0f},"
        f" high {result.high:.0f} person-days"
        f" ({person_months(result.low):.1f} to"
        f" {person_months(result.high):.1f} person-months)"
    )
    typer.echo("")
    typer.echo("Assumptions:")
    for line in result.assumptions:
        typer.echo(_wrap("- " + line))


@app.command()
def convert(
    db: Annotated[
        Path,
        typer.Option(exists=True, dir_okay=False, help="Inventory database."),
    ] = Path("inventory.db"),
    out: Annotated[
        Path, typer.Option(help="Where to write the PostgreSQL schema DDL.")
    ] = Path("schema_pg.sql"),
    residue: Annotated[
        Path,
        typer.Option(help="Where to write the residue report."),
    ] = Path("schema_residue.txt"),
) -> None:
    """Convert schema structure to PostgreSQL DDL, offline.

    Tables, columns, keys, checks, and foreign keys come from the
    inventory's dictionary facts. Everything the converter cannot
    port faithfully lands in the residue report instead of the DDL.
    """
    from pgrecon.convert import convert_schema, residue_report

    result = convert_schema(db)
    out.write_text(result.sql, encoding="utf-8", newline="\n")
    residue.write_text(residue_report(result.residue), encoding="utf-8", newline="\n")
    typer.echo(
        f"Wrote {out} ({result.tables} tables, {result.partitions} partition"
        f" children, {result.constraints} constraints, {result.indexes} indexes,"
        f" {result.views} views, {result.sequences} sequences,"
        f" {result.synonyms} synonyms, {result.db_links} db links,"
        f" {result.routines} routines, {result.triggers} triggers)"
    )
    typer.echo(f"Wrote {residue} ({len(result.residue)} residue items)")


@app.command()
def explain(
    rule_id: Annotated[
        str | None,
        typer.Argument(help="Rule id, e.g. R-SRC-18. Omit to list the catalog."),
    ] = None,
) -> None:
    """Show one rule's remedy, or list the whole catalog."""
    rules = all_rules()
    if rule_id is None:
        width = max(len(rule.id) for rule in rules)
        for rule in sorted(rules, key=lambda r: r.id):
            typer.echo(f"{rule.id:<{width}}  {rule.severity.value:<7}  {rule.title}")
        typer.echo("")
        typer.echo(f"{len(rules)} rules")
        return
    match = {rule.id: rule for rule in rules}.get(rule_id.upper())
    if match is None:
        raise typer.BadParameter(f"unknown rule id: {rule_id}")
    typer.echo(f"{match.id}: {match.title}")
    line = (
        f"severity: {match.severity.value}  effort: {match.effort}"
        f"  category: {match.category}"
    )
    if match.extension:
        line += f"  extension: {match.extension}"
    typer.echo(line)
    typer.echo("")
    typer.echo(_wrap(match.remedy))


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

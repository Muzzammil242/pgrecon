"""Measure the converter the way the benchmark page counts.

For every schema dump under a work directory: load it, convert it,
apply the DDL to a fresh database on a live PostgreSQL with
check_function_bodies on and ON_ERROR_STOP off, and count the lines
PostgreSQL answered with ERROR. Then classify every inventory object
the converter is answerable for as created (its CREATE statement is in
the DDL), refused (named in the residue), or lost (neither), so the
coverage figure is stated with the same precision as the error count.

    uv run python tools/benchmark_measure.py dumps/ \
        --pg "host=127.0.0.1 user=postgres password=ci" --out results

`dumps/` holds one extraction dump per schema, named after the schema.
The run fails only if an object is lost - that is the converter's law -
never on rejected statements; those are the measurement.
"""

import argparse
import importlib.util
import json
import logging
import re
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType

from pgrecon.convert import convert_schema, residue_report
from pgrecon.convert.identifiers import ident
from pgrecon.convert.residue import Residue
from pgrecon.inventory import load_dump

HERE = Path(__file__).resolve().parent


def fuzz_runner() -> ModuleType:
    """The fuzzer's notion of which objects the converter answers for."""
    spec = importlib.util.spec_from_file_location("fuzz_run", HERE / "fuzz_run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class SchemaResult:
    schema: str
    objects: int = 0
    answerable: int = 0
    created: int = 0
    refused: int = 0
    lost: int = 0
    residue_lines: int = 0
    ddl_bytes: int = 0
    statements: int = 0
    errors: int = 0
    first_errors: list[str] = field(default_factory=list)
    lost_names: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.created / self.answerable if self.answerable else 0.0


def classify(
    fz: ModuleType, conn: sqlite3.Connection, sql: str, residue: tuple[Residue, ...]
) -> tuple[list[str], list[str], list[str]]:
    """Split the answerable objects into created, refused, and lost.

    Mirrors fuzz_run.unaccounted exactly, keeping the two accounted
    groups apart instead of discarding them.
    """
    created_tokens: dict[str, set[str]] = {
        kind: {m.group(1) for m in pattern.finditer(sql)}
        for kind, pattern in fz._CREATED.items()
    }
    bare = {
        kind: {fz._bare(t) for t in tokens} for kind, tokens in created_tokens.items()
    }
    named: dict[str, set[str]] = {}
    for r in residue:
        named.setdefault(r.object_name, set()).add(r.kind)

    created: list[str] = []
    refused: list[str] = []
    lost: list[str] = []
    for kind, name in fz.universe(conn):
        label = f"{kind} {name}"
        variants = [ident(name)]
        if kind in ("table", "view", "mview"):
            variants.append(ident(name.lower()))
        if kind == "index":
            variants.append(ident(name + "_IX"))
        if kind == "constraint":
            variants += [ident(name + "_PK"), ident(name + "_UK")]
        kinds = named.get(name, set())
        created_kind = "view" if kind == "synonym" else kind
        is_created = (
            created_kind in created_tokens
            and any(v in created_tokens[created_kind] for v in variants)
        ) or (kind in ("routine", "trigger") and name.lower() in bare[kind])
        # A note is enough of an answer for a database link or an
        # Oracle-internal snapshot index; everything else needs a refusal.
        note_suffices = kind == "dblink" or (
            kind == "index" and name.upper().startswith("I_SNAP$")
        )
        is_refused = bool(kinds - {"note"}) or (note_suffices and bool(kinds))
        if is_created:
            created.append(label)
        elif is_refused:
            refused.append(label)
        else:
            lost.append(label)
    return created, refused, lost


def apply_counting(conninfo: str, dbname: str, sql_path: Path) -> tuple[int, list[str]]:
    """Apply the DDL with ON_ERROR_STOP off; return the ERROR count."""
    admin = re.sub(r"\bdbname=\S+", "", conninfo).strip()
    for statement in (f"DROP DATABASE IF EXISTS {dbname}", f"CREATE DATABASE {dbname}"):
        subprocess.run(
            ["psql", f"{admin} dbname=postgres", "-qX", "-c", statement],
            check=True,
            capture_output=True,
            text=True,
        )
    proc = subprocess.run(
        [
            "psql",
            f"{admin} dbname={dbname}",
            "-qX",
            "-v",
            "ON_ERROR_STOP=0",
            "-c",
            "SET check_function_bodies = on",
            "-f",
            str(sql_path),
        ],
        capture_output=True,
        text=True,
    )
    errors = [line for line in proc.stderr.splitlines() if "ERROR:" in line]
    return len(errors), errors[:5]


def count_statements(sql: str) -> int:
    """Statements as psql would split them: semicolons outside dollar quotes."""
    count = 0
    in_dollar = None
    i = 0
    while i < len(sql):
        if in_dollar:
            if sql.startswith(in_dollar, i):
                i += len(in_dollar)
                in_dollar = None
                continue
        else:
            m = re.match(r"\$[A-Za-z_]*\$", sql[i : i + 64])
            if m:
                in_dollar = m.group(0)
                i += len(in_dollar)
                continue
            if sql[i] == ";":
                count += 1
        i += 1
    return count


def measure(
    schema: str, dump: Path, work: Path, pg: str | None, fz: ModuleType
) -> SchemaResult:
    result = SchemaResult(schema)
    db = work / f"{schema}.db"
    load_dump(dump, db)
    conn = sqlite3.connect(db)
    try:
        result.objects = conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
        conversion = convert_schema(db)
        report = residue_report(conversion.residue)
        sql_path = work / f"{schema}_pg.sql"
        sql_path.write_text(conversion.sql, encoding="utf-8", newline="\n")
        (work / f"{schema}_residue.txt").write_text(
            report, encoding="utf-8", newline="\n"
        )
        result.residue_lines = len(conversion.residue)
        result.ddl_bytes = len(conversion.sql.encode("utf-8"))
        result.statements = count_statements(conversion.sql)
        created, refused, lost = classify(fz, conn, conversion.sql, conversion.residue)
        result.answerable = len(created) + len(refused) + len(lost)
        result.created, result.refused, result.lost = (
            len(created),
            len(refused),
            len(lost),
        )
        result.lost_names = lost[:10]
    finally:
        conn.close()
    if pg:
        result.errors, result.first_errors = apply_counting(
            pg, f"bench_{schema.lower()}", sql_path
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("dumps", type=Path, help="directory of per-schema dump folders")
    parser.add_argument("--pg", help="libpq conninfo of the PostgreSQL to apply to")
    parser.add_argument("--out", type=Path, default=Path("bench-work"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.getLogger("sqlglot").setLevel(logging.ERROR)
    logging.getLogger("pgrecon").setLevel(logging.ERROR)
    fz = fuzz_runner()

    results: list[SchemaResult] = []
    for dump in sorted(p for p in args.dumps.iterdir() if p.is_dir()):
        r = measure(dump.name, dump, args.out, args.pg, fz)
        results.append(r)
        print(
            f"{r.schema:<12} {r.objects:>4} objects {r.answerable:>4} answerable"
            f" {r.created:>4} created {r.refused:>4} refused {r.lost:>3} lost"
            f" {r.statements:>5} statements {r.errors:>4} errors",
            flush=True,
        )
        for line in r.first_errors:
            print(f"    ! {line}")
        for name in r.lost_names:
            print(f"    lost: {name}")

    total = SchemaResult("all")
    for r in results:
        for f in (
            "objects",
            "answerable",
            "created",
            "refused",
            "lost",
            "statements",
            "errors",
        ):
            setattr(total, f, getattr(total, f) + getattr(r, f))
    print(
        f"\n{'total':<12} {total.objects:>4} objects {total.answerable:>4} answerable"
        f" {total.created:>4} created {total.refused:>4} refused {total.lost:>3} lost"
        f" {total.statements:>5} statements {total.errors:>4} errors"
        f"  coverage {100 * total.coverage:.0f}%"
    )
    (args.out / "results.json").write_text(
        json.dumps(
            {"schemas": [asdict(r) for r in results], "total": asdict(total)},
            indent=2,
        ),
        encoding="utf-8",
    )
    lines = [
        "| Schema | Objects | Answerable | Created | Refused | Coverage"
        " | Statements | Rejected |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in results + [total]:
        lines.append(
            f"| {r.schema} | {r.objects} | {r.answerable} | {r.created} | {r.refused}"
            f" | {100 * r.coverage:.0f}% | {r.statements} | {r.errors} |"
        )
    (args.out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if total.lost else 0


if __name__ == "__main__":
    sys.exit(main())

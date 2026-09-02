"""Drive adversarial dumps through the pipeline and check the two laws.

For every seed: generate the dump (tools/fuzz_dump.py), load it, run
the rule engine, convert, and then check what the converter promises:

  never crashes    load, report, and convert complete on every input;
  never loses      every object the loader stored is either created in
                   the emitted DDL or named in the residue - nothing
                   vanishes between the inventory and the output;
  degrades visibly a spool carrying an Oracle error or a foreign code
                   page leaves a warning row in the inventory;
  applies          with --pg, the DDL applies to a live PostgreSQL with
                   check_function_bodies on and zero rejected statements.

    uv run python tools/fuzz_run.py --seeds 20
    uv run python tools/fuzz_run.py --seeds 5 --start 100 \
        --pg "host=127.0.0.1 user=postgres password=ci"

Every failure prints its seed; the dump, DDL, and residue of a failing
seed stay under the work directory for reproduction.
"""

import argparse
import importlib.util
import logging
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from pgrecon.convert import convert_schema, residue_report
from pgrecon.convert.identifiers import ident
from pgrecon.convert.residue import Residue
from pgrecon.inventory import load_dump
from pgrecon.rules.engine import run_rules

HERE = Path(__file__).resolve().parent


def generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("fuzz_dump", HERE / "fuzz_dump.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# A PostgreSQL identifier as the converter writes it: folded and bare,
# or double-quoted with doubled inner quotes.
_IDENT = r'("(?:[^"]|"")+"|[^\s(;]+)'
_CREATED = {
    "table": re.compile(r"^CREATE TABLE " + _IDENT, re.MULTILINE),
    "view": re.compile(r"^CREATE (?:OR REPLACE )?VIEW " + _IDENT, re.MULTILINE),
    "mview": re.compile(r"^CREATE MATERIALIZED VIEW " + _IDENT, re.MULTILINE),
    "sequence": re.compile(r"^CREATE SEQUENCE " + _IDENT, re.MULTILINE),
    "index": re.compile(r"^CREATE (?:UNIQUE )?INDEX " + _IDENT, re.MULTILINE),
    "constraint": re.compile(r"ADD CONSTRAINT " + _IDENT),
    "routine": re.compile(
        r"^CREATE OR REPLACE (?:FUNCTION|PROCEDURE) " + _IDENT, re.MULTILINE
    ),
    "trigger": re.compile(r"^CREATE TRIGGER " + _IDENT, re.MULTILINE),
}


@dataclass
class SeedResult:
    seed: int
    objects: int = 0
    findings: int = 0
    residue: int = 0
    ddl_bytes: int = 0
    seconds: float = 0.0
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def _bare(token: str) -> str:
    if token.startswith('"'):
        return token[1:-1].replace('""', '"').lower()
    return token.lower()


def universe(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Every inventory object the converter is answerable for."""
    items: list[tuple[str, str]] = []
    mviews = {r[0] for r in conn.execute("SELECT mview_name FROM mviews")}
    for (name,) in conn.execute("SELECT table_name FROM tables"):
        if name not in mviews:
            items.append(("table", name))
    items += [("mview", name) for name in sorted(mviews)]
    for otype, kind in (
        ("VIEW", "view"),
        ("FUNCTION", "routine"),
        ("PROCEDURE", "routine"),
        ("PACKAGE", "package"),
        ("TYPE", "type"),
    ):
        items += [
            (kind, r[0])
            for r in conn.execute("SELECT name FROM objects WHERE type = ?", (otype,))
        ]
    items += [
        ("sequence", r[0]) for r in conn.execute("SELECT sequence_name FROM sequences")
    ]
    items += [
        ("synonym", r[0]) for r in conn.execute("SELECT synonym_name FROM synonyms")
    ]
    items += [("dblink", r[0]) for r in conn.execute("SELECT db_link FROM db_links")]
    items += [
        ("trigger", r[0]) for r in conn.execute("SELECT trigger_name FROM triggers")
    ]
    # Key-backing and generated indexes are the constraints' business;
    # LOB segment indexes are storage.
    items += [
        ("index", r[0])
        for r in conn.execute(
            "SELECT i.index_name FROM indexes i"
            " WHERE COALESCE(i.generated, 'N') <> 'Y'"
            " AND COALESCE(i.index_type, '') <> 'LOB'"
            " AND NOT EXISTS (SELECT 1 FROM constraints c"
            "   WHERE c.owner = i.owner AND c.constraint_name = i.index_name)"
        )
    ]
    # NOT NULL checks live on the column; every other constraint must
    # come out the other side by name.
    not_null = re.compile(r'^"?[A-Za-z0-9_$#]+"?\s+IS\s+NOT\s+NULL$', re.IGNORECASE)
    for name, ctype, condition in conn.execute(
        "SELECT c.constraint_name, c.type, k.condition FROM constraints c"
        " LEFT JOIN check_conditions k"
        " ON k.owner = c.owner AND k.constraint_name = c.constraint_name"
    ):
        if ctype == "C" and condition is not None:
            stripped = condition.strip()
            if not stripped or not_null.match(stripped):
                continue
        if ctype in ("P", "U", "R", "C"):
            items.append(("constraint", name))
    return items


def unaccounted(
    conn: sqlite3.Connection, sql: str, residue: tuple[Residue, ...]
) -> list[str]:
    created: dict[str, set[str]] = {
        kind: {m.group(1) for m in pattern.finditer(sql)}
        for kind, pattern in _CREATED.items()
    }
    bare = {kind: {_bare(t) for t in tokens} for kind, tokens in created.items()}
    named: dict[str, set[str]] = {}
    for r in residue:
        named.setdefault(r.object_name, set()).add(r.kind)

    lost = []
    for kind, name in universe(conn):
        variants = [ident(name)]
        if kind in ("table", "view", "mview"):
            variants.append(ident(name.lower()))
        if kind == "index":
            variants.append(ident(name + "_IX"))
        if kind == "constraint":
            variants += [ident(name + "_PK"), ident(name + "_UK")]
        kinds = named.get(name, set())
        created_kind = "view" if kind == "synonym" else kind
        if created_kind in created and any(
            v in created[created_kind] for v in variants
        ):
            continue
        if kind in ("routine", "trigger") and name.lower() in bare[kind]:
            continue
        if kind == "dblink" and kinds:
            continue
        if kind == "index" and name.upper().startswith("I_SNAP$") and kinds:
            continue
        if kinds - {"note"}:
            continue
        lost.append(f"{kind} {name}")
    return lost


def apply_live(conninfo: str, seed: int, sql_path: Path) -> str | None:
    """Apply the DDL to a fresh database; return the first error, if any."""
    dbname = f"fuzz_{seed}"
    admin = re.sub(r"\bdbname=\S+", "", conninfo).strip()
    setup = subprocess.run(
        [
            "psql",
            f"{admin} dbname=postgres",
            "-qX",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            f"DROP DATABASE IF EXISTS {dbname}",
            "-c",
            f"CREATE DATABASE {dbname}",
        ],
        capture_output=True,
        text=True,
    )
    if setup.returncode != 0:
        return "could not create the scratch database: " + setup.stderr.strip()
    proc = subprocess.run(
        [
            "psql",
            f"{admin} dbname={dbname}",
            "-qX",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            "SET check_function_bodies = on",
            "-f",
            str(sql_path),
        ],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["psql", f"{admin} dbname=postgres", "-qX", "-c", f"DROP DATABASE {dbname}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        lines = [line for line in proc.stderr.strip().splitlines() if line.strip()]
        return " | ".join(lines[-3:]) if lines else "psql failed without a message"
    return None


def check_seed(
    seed: int, work: Path, pg: str | None, gen: ModuleType | None = None
) -> SeedResult:
    gen = gen or generator()
    started = time.perf_counter()
    result = SeedResult(seed)
    dump = work / f"seed-{seed}"
    if dump.exists():
        shutil.rmtree(dump)
    manifest = gen.generate(seed, dump)
    db = work / f"seed-{seed}.db"

    try:
        load_dump(dump, db)
    except Exception as exc:
        result.failures.append(f"load crashed: {exc!r}")
        result.seconds = time.perf_counter() - started
        return result

    conn = sqlite3.connect(db)
    try:
        have = set(conn.execute("SELECT owner, name, type FROM objects"))
        result.objects = len(have)
        missing = [tuple(o) for o in manifest.objects if tuple(o) not in have]
        if missing:
            result.failures.append(
                f"{len(missing)} generated objects never reached the inventory,"
                f" first {missing[0]}"
            )
        meta = dict(conn.execute("SELECT key, value FROM meta"))
        for spool in manifest.error_spools:
            if f"load_warning:{spool[:-4]}" not in meta:
                result.failures.append(
                    f"{spool} carried an Oracle error but no load_warning row"
                    " was left for it"
                )
        for spool in manifest.lossy_spools:
            if f"encoding_warning:{spool}" not in meta:
                result.failures.append(
                    f"{spool} was in a foreign code page but no encoding_warning"
                    " row was left"
                )

        try:
            result.findings = len(run_rules(db))
        except Exception as exc:
            result.failures.append(f"report crashed: {exc!r}")

        try:
            conversion = convert_schema(db)
            report = residue_report(conversion.residue)
        except Exception as exc:
            result.failures.append(f"convert crashed: {exc!r}")
            result.seconds = time.perf_counter() - started
            return result
        sql_path = dump / "schema_pg.sql"
        sql_path.write_text(conversion.sql, encoding="utf-8", newline="\n")
        (dump / "residue.txt").write_text(report, encoding="utf-8", newline="\n")
        result.residue = len(conversion.residue)
        result.ddl_bytes = len(conversion.sql.encode("utf-8"))

        lost = unaccounted(conn, conversion.sql, conversion.residue)
        if lost:
            shown = ", ".join(lost[:4])
            more = f" and {len(lost) - 4} more" if len(lost) > 4 else ""
            result.failures.append(
                f"{len(lost)} objects neither created nor in the residue: {shown}{more}"
            )
    finally:
        conn.close()

    if pg and result.ok:
        error = apply_live(pg, seed, sql_path)
        if error:
            result.failures.append(f"DDL rejected by PostgreSQL: {error}")

    result.seconds = time.perf_counter() - started
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seeds", type=int, default=10, help="how many seeds")
    parser.add_argument("--start", type=int, default=1, help="first seed")
    parser.add_argument(
        "--pg",
        help="libpq conninfo (key=value form) of a PostgreSQL to apply the DDL to",
    )
    parser.add_argument("--work", type=Path, default=Path("fuzz-work"))
    parser.add_argument(
        "--keep", action="store_true", help="keep the dumps of passing seeds too"
    )
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    # Names in the dumps are deliberately not ASCII; Windows consoles
    # are deliberately not UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.getLogger("sqlglot").setLevel(logging.ERROR)
    logging.getLogger("pgrecon").setLevel(logging.ERROR)
    gen = generator()

    failed: list[SeedResult] = []
    for seed in range(args.start, args.start + args.seeds):
        result = check_seed(seed, args.work, args.pg, gen)
        status = "ok " if result.ok else "FAIL"
        print(
            f"seed {seed:>8} {status} {result.objects:>4} objects"
            f" {result.findings:>4} findings {result.residue:>4} residue"
            f" {result.ddl_bytes:>7} bytes DDL {result.seconds:5.1f}s",
            flush=True,
        )
        for failure in result.failures:
            print(f"    - {failure}", flush=True)
        if not result.ok:
            failed.append(result)
        elif not args.keep:
            shutil.rmtree(args.work / f"seed-{seed}", ignore_errors=True)
            (args.work / f"seed-{seed}.db").unlink(missing_ok=True)
    print()
    if failed:
        seeds = ", ".join(str(r.seed) for r in failed)
        print(f"{len(failed)} of {args.seeds} seeds failed: {seeds}")
        print(
            "reproduce one with:"
            f" uv run python tools/fuzz_dump.py --seed {failed[0].seed}"
            f" {args.work / f'seed-{failed[0].seed}'}"
        )
        return 1
    print(f"all {args.seeds} seeds obeyed the laws")
    return 0


if __name__ == "__main__":
    sys.exit(main())

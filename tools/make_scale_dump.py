"""Generate a large synthetic dump for scale testing.

Produces a dump folder shaped like real SQL*Plus output (leading
blank line per spool) with thousands of tables and hundreds of
packages of plausible PL/SQL, including one deliberately huge package
body, so load-and-assess timing can be measured and quoted honestly.

    uv run python tools/make_scale_dump.py DUMP_DIR \
        --tables 5000 --packages 800 --monster-lines 25000
"""

import argparse
import random
from pathlib import Path

HEADERS = {
    "meta.csv": '"KEY","VALUE"',
    "objects.csv": (
        '"OWNER","OBJECT_NAME","OBJECT_TYPE","STATUS","CREATED","LAST_DDL_TIME"'
    ),
    "tables.csv": (
        '"OWNER","TABLE_NAME","NUM_ROWS","AVG_ROW_LEN","PARTITIONED",'
        '"TEMPORARY","DEGREE"'
    ),
    "columns.csv": (
        '"OWNER","TABLE_NAME","COLUMN_NAME","COLUMN_ID","DATA_TYPE",'
        '"DATA_LENGTH","DATA_PRECISION","DATA_SCALE","NULLABLE"'
    ),
    "source.csv": '"OWNER","NAME","TYPE","LINE","TEXT"',
}

STAMP = "2024-01-01 10:00:00"
OWNER = "SCALE"


def spool(path: Path, header: str, rows: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n" + header + "\n")
        for row in rows:
            fh.write(row + "\n")


def body_lines(
    name: str, rng: random.Random, procs: int, callees: list[str]
) -> list[str]:
    lines = [f"PACKAGE BODY {name} AS"]
    for p in range(procs):
        lines.append(f"  PROCEDURE step_{p} (p_id IN NUMBER) IS")
        lines.append("    l_total NUMBER := 0;")
        lines.append("  BEGIN")
        lines.append(
            f"    UPDATE t_{rng.randrange(200)} SET c_2 = p_id WHERE c_1 = p_id;"
        )
        if p % 3 == 0:
            lines.append("    l_total := l_total + TO_CHAR(SYSDATE, 'J');")
        if p % 5 == 0:
            lines.append("    l_total := DECODE(p_id, 0, 1, l_total);")
        if p % 7 == 0 and callees:
            lines.append(f"    {rng.choice(callees)}.step_0(p_id);")
        if p % 11 == 0:
            lines.append("    COMMIT;")
        lines.append("  END;")
    lines.append(f"END {name};")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--tables", type=int, default=5000)
    parser.add_argument("--packages", type=int, default=800)
    parser.add_argument("--monster-lines", type=int, default=25000)
    args = parser.parse_args()
    rng = random.Random(42)
    args.out.mkdir(parents=True, exist_ok=True)

    objects: list[str] = []
    tables: list[str] = []
    columns: list[str] = []
    source: list[str] = []
    ddl: list[str] = []

    for t in range(args.tables):
        name = f"T_{t}"
        objects.append(f'"{OWNER}","{name}","TABLE","VALID","{STAMP}","{STAMP}"')
        part = "YES" if t % 50 == 0 else "NO"
        tables.append(
            f'"{OWNER}","{name}",{rng.randrange(1, 9)}000,'
            f'{rng.randrange(40, 200)},"{part}","N","1"'
        )
        ncols = 8 + t % 8
        for c in range(ncols):
            dtype = ["NUMBER", "VARCHAR2", "DATE", "NUMBER", "CLOB"][c % 5]
            precision = "10" if dtype == "NUMBER" else ""
            columns.append(
                f'"{OWNER}","{name}","C_{c}",{c + 1},"{dtype}",22,{precision},,"Y"'
            )
        ddl.append(f"-- PGRECON_OBJECT TABLE {OWNER}.{name}")
        cols = ", ".join(f'"C_{c}" NUMBER(10,0)' for c in range(4))
        if part == "YES":
            ddl.append(
                f'CREATE TABLE "{OWNER}"."{name}" ({cols})'
                ' PARTITION BY RANGE ("C_0")'
                ' (PARTITION "P1" VALUES LESS THAN (100),'
                ' PARTITION "P2" VALUES LESS THAN (MAXVALUE)) ;'
            )
        else:
            ddl.append(f'CREATE TABLE "{OWNER}"."{name}" ({cols}) ;')

    pkg_names = [f"PKG_{p}" for p in range(args.packages)]
    for p, name in enumerate(pkg_names):
        objects.append(f'"{OWNER}","{name}","PACKAGE","VALID","{STAMP}","{STAMP}"')
        objects.append(f'"{OWNER}","{name}","PACKAGE BODY","VALID","{STAMP}","{STAMP}"')
        spec = (
            [f"PACKAGE {name} AS"]
            + [f"  PROCEDURE step_{i} (p_id IN NUMBER);" for i in range(6)]
            + [f"END {name};"]
        )
        for i, text in enumerate(spec, start=1):
            source.append(f'"{OWNER}","{name}","PACKAGE",{i},"{text}"')
        callees = [pkg_names[(p + k) % len(pkg_names)] for k in (1, 7)]
        body = body_lines(name, rng, procs=18, callees=callees)
        for i, text in enumerate(body, start=1):
            source.append(f'"{OWNER}","{name}","PACKAGE BODY",{i},"{text}"')

    objects.append(
        f'"{OWNER}","PKG_MONSTER","PACKAGE BODY","VALID","{STAMP}","{STAMP}"'
    )
    procs = max(1, args.monster_lines // 9)
    monster = body_lines("PKG_MONSTER", rng, procs=procs, callees=pkg_names[:5])
    for i, text in enumerate(monster, start=1):
        source.append(f'"{OWNER}","PKG_MONSTER","PACKAGE BODY",{i},"{text}"')

    spool(
        args.out / "meta.csv",
        HEADERS["meta.csv"],
        [f'"schema","{OWNER}"', '"version","21.0.0.0.0"'],
    )
    spool(args.out / "objects.csv", HEADERS["objects.csv"], objects)
    spool(args.out / "tables.csv", HEADERS["tables.csv"], tables)
    spool(args.out / "columns.csv", HEADERS["columns.csv"], columns)
    spool(args.out / "source.csv", HEADERS["source.csv"], source)
    with (args.out / "ddl_tables.sql").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n")
        for line in ddl:
            fh.write(line + "\n")

    print(f"tables={args.tables} packages={args.packages} source_lines={len(source)}")


if __name__ == "__main__":
    main()

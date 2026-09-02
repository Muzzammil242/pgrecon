"""Generate an adversarial extraction dump from a seed.

The dump is shaped exactly like the SQL*Plus spools the packaged
script produces - one blank line, a quoted CSV header, rows - but the
content is chosen to hurt: identifiers past PostgreSQL's 63 bytes in
ASCII and in Hangul, names that collide once Oracle's separate
namespaces fold into pg_class, reserved words as column names, every
Oracle data type the catalog can spell, partition layouts of every
kind, sequences with 28-digit bounds, views over views, stored code
that must convert next to code that must refuse, and spools that
carry an Oracle error, a foreign code page, or a torn last row where
data should be.

    uv run python tools/fuzz_dump.py --seed 17 fuzz-work/seed-17

Same seed, same dump, byte for byte. tools/fuzz_run.py drives many
seeds through load, report, convert, and a live PostgreSQL apply and
checks the converter's two laws on each one.
"""

import argparse
import csv
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

OWNER = "FUZZ"
STAMP = "2025-06-01 09:00:00"

HEADERS: dict[str, list[str]] = {
    "meta.csv": ["KEY", "VALUE"],
    "objects.csv": [
        "OWNER",
        "OBJECT_NAME",
        "OBJECT_TYPE",
        "STATUS",
        "CREATED",
        "LAST_DDL_TIME",
    ],
    "tables.csv": [
        "OWNER",
        "TABLE_NAME",
        "NUM_ROWS",
        "AVG_ROW_LEN",
        "PARTITIONED",
        "TEMPORARY",
        "DEGREE",
    ],
    "columns.csv": [
        "OWNER",
        "TABLE_NAME",
        "COLUMN_NAME",
        "COLUMN_ID",
        "DATA_TYPE",
        "DATA_LENGTH",
        "DATA_PRECISION",
        "DATA_SCALE",
        "NULLABLE",
        "CHAR_LENGTH",
        "CHAR_USED",
    ],
    "source.csv": ["OWNER", "NAME", "TYPE", "LINE", "TEXT"],
    "features.csv": ["FEATURE", "DETAIL", "CNT"],
    "dependencies.csv": [
        "OWNER",
        "NAME",
        "TYPE",
        "REFERENCED_OWNER",
        "REFERENCED_NAME",
        "REFERENCED_TYPE",
    ],
    "constraints.csv": [
        "OWNER",
        "CONSTRAINT_NAME",
        "TABLE_NAME",
        "CONSTRAINT_TYPE",
        "STATUS",
        "R_OWNER",
        "R_CONSTRAINT_NAME",
        "DELETE_RULE",
    ],
    "constraint_columns.csv": ["OWNER", "CONSTRAINT_NAME", "COLUMN_NAME", "POSITION"],
    "check_conditions.csv": ["OWNER", "CONSTRAINT_NAME", "CONDITION", "TRUNCATED"],
    "indexes.csv": [
        "OWNER",
        "INDEX_NAME",
        "TABLE_NAME",
        "INDEX_TYPE",
        "UNIQUENESS",
        "STATUS",
        "GENERATED",
        "DEGREE",
    ],
    "index_columns.csv": ["OWNER", "INDEX_NAME", "COLUMN_NAME", "COLUMN_POSITION"],
    "index_expressions.csv": [
        "OWNER",
        "INDEX_NAME",
        "COLUMN_POSITION",
        "COLUMN_EXPRESSION",
        "TRUNCATED",
    ],
    "part_tables.csv": [
        "OWNER",
        "TABLE_NAME",
        "PARTITIONING_TYPE",
        "SUBPARTITIONING_TYPE",
        "PARTITION_COUNT",
        "INTERVAL",
    ],
    "part_key_columns.csv": ["OWNER", "NAME", "COLUMN_NAME", "COLUMN_POSITION"],
    "part_subkey_columns.csv": ["OWNER", "NAME", "COLUMN_NAME", "COLUMN_POSITION"],
    "part_partitions.csv": [
        "OWNER",
        "TABLE_NAME",
        "PARTITION_NAME",
        "POSITION",
        "HIGH_VALUE",
        "TRUNCATED",
    ],
    "part_subpartitions.csv": [
        "OWNER",
        "TABLE_NAME",
        "PARTITION_NAME",
        "SUBPARTITION_NAME",
        "POSITION",
        "HIGH_VALUE",
        "TRUNCATED",
    ],
    "sequences.csv": [
        "OWNER",
        "SEQUENCE_NAME",
        "MIN_VALUE",
        "MAX_VALUE",
        "INCREMENT_BY",
        "CYCLE_FLAG",
        "CACHE_SIZE",
        "LAST_NUMBER",
    ],
    "column_defaults.csv": [
        "OWNER",
        "TABLE_NAME",
        "COLUMN_NAME",
        "DEFAULT_TEXT",
        "VIRTUAL",
        "TRUNCATED",
    ],
    "synonyms.csv": ["OWNER", "SYNONYM_NAME", "TABLE_OWNER", "TABLE_NAME", "DB_LINK"],
    "triggers.csv": [
        "OWNER",
        "TRIGGER_NAME",
        "TRIGGER_TYPE",
        "TRIGGERING_EVENT",
        "TABLE_NAME",
        "STATUS",
    ],
    "db_links.csv": ["OWNER", "DB_LINK", "USERNAME", "HOST"],
    "part_indexes.csv": ["OWNER", "INDEX_NAME", "TABLE_NAME", "LOCALITY"],
    "mviews.csv": ["OWNER", "MVIEW_NAME", "REWRITE_ENABLED", "REFRESH_METHOD", "QUERY"],
    "license.csv": ["KEY", "VALUE"],
    "grants.csv": ["GRANTEE", "OWNER", "TABLE_NAME", "PRIVILEGE", "GRANTABLE"],
    "table_comments.csv": ["OWNER", "TABLE_NAME", "COMMENTS"],
    "column_comments.csv": ["OWNER", "TABLE_NAME", "COLUMN_NAME", "COMMENTS"],
    "nls.csv": ["KEY", "VALUE"],
    "feature_usage.csv": [
        "NAME",
        "VERSION",
        "DETECTED_USAGES",
        "CURRENTLY_USED",
        "LAST_USAGE",
    ],
    "plan_management.csv": ["KIND", "NAME", "ENABLED"],
}

TABLE_WORDS = [
    "ORDERS",
    "EMP",
    "DEPT",
    "SALES",
    "AUDIT",
    "LEDGER",
    "INVOICE",
    "STOCK",
    "CUSTOMER",
    "PAYMENT",
    "SHIPMENT",
    "EVENT",
    "RATE",
    "REGION",
    "TICKET",
    "ASSET",
]
COLUMN_WORDS = [
    "NAME",
    "CREATED",
    "AMOUNT",
    "STATUS",
    "QTY",
    "NOTE",
    "EMAIL",
    "PRICE",
    "UPDATED",
    "CODE",
    "FLAG",
    "TOTAL",
    "REGION",
    "PAYLOAD",
    "DOC",
    "RANK",
]
# Reserved in PostgreSQL, legal as quoted identifiers in Oracle.
RESERVED = [
    "ORDER",
    "USER",
    "GROUP",
    "SELECT",
    "END",
    "CHECK",
    "LIMIT",
    "OFFSET",
    "WINDOW",
    "TABLE",
    "COLUMN",
    "DEFAULT",
    "ANALYZE",
    "CAST",
    "PRIMARY",
    "DESC",
    "FROM",
    "WHERE",
    "LEVEL",
    "START",
    "ARRAY",
    "LATERAL",
]
# Hangul and CJK words: three bytes per character in UTF-8, so a
# 25-character name is 75 bytes, past the limit while short to look at.
CJK = [
    "\uc9c1\uc6d0",
    "\ubd80\uc11c",
    "\u90e8\u9580",
    "\u793e\u54e1",
    "\u9867\u5ba2",
    "\uc8fc\ubb38",
    "\ud14c\uc774\ube14",
]

# (catalog data_type, data_length, precision, scale, DDL spelling, weight)
TYPES: list[tuple[str, int, int | None, int | None, str, int]] = [
    ("NUMBER", 22, None, None, "NUMBER", 10),
    ("NUMBER", 22, 10, 0, "NUMBER(10,0)", 10),
    ("NUMBER", 22, 38, 0, "NUMBER(38,0)", 3),
    ("NUMBER", 22, 12, 2, "NUMBER(12,2)", 8),
    ("NUMBER", 22, None, 0, "NUMBER(*,0)", 3),
    ("NUMBER", 22, 5, -2, "NUMBER(5,-2)", 1),
    ("NUMBER", 22, 5, 10, "NUMBER(5,10)", 1),
    ("NUMBER", 22, 1, 0, "NUMBER(1,0)", 4),
    ("FLOAT", 22, 126, None, "FLOAT(126)", 2),
    ("BINARY_DOUBLE", 8, None, None, "BINARY_DOUBLE", 2),
    ("BINARY_FLOAT", 4, None, None, "BINARY_FLOAT", 1),
    ("VARCHAR2", 1, None, None, "VARCHAR2(1 BYTE)", 4),
    ("VARCHAR2", 30, None, None, "VARCHAR2(30 BYTE)", 12),
    ("VARCHAR2", 255, None, None, "VARCHAR2(255 CHAR)", 8),
    ("VARCHAR2", 4000, None, None, "VARCHAR2(4000 BYTE)", 4),
    ("VARCHAR2", 32767, None, None, "VARCHAR2(32767 BYTE)", 1),
    ("NVARCHAR2", 400, None, None, "NVARCHAR2(200)", 2),
    ("CHAR", 1, None, None, "CHAR(1 BYTE)", 4),
    ("CHAR", 10, None, None, "CHAR(10 BYTE)", 2),
    ("NCHAR", 10, None, None, "NCHAR(5)", 1),
    ("DATE", 7, None, None, "DATE", 10),
    ("TIMESTAMP(6)", 11, None, 6, "TIMESTAMP (6)", 6),
    ("TIMESTAMP(9)", 11, None, 9, "TIMESTAMP (9)", 1),
    ("TIMESTAMP(0)", 7, None, 0, "TIMESTAMP (0)", 1),
    ("TIMESTAMP(6) WITH TIME ZONE", 13, None, 6, "TIMESTAMP (6) WITH TIME ZONE", 3),
    (
        "TIMESTAMP(6) WITH LOCAL TIME ZONE",
        11,
        None,
        6,
        "TIMESTAMP (6) WITH LOCAL TIME ZONE",
        2,
    ),
    ("INTERVAL DAY(2) TO SECOND(6)", 11, 2, 6, "INTERVAL DAY (2) TO SECOND (6)", 2),
    ("INTERVAL YEAR(2) TO MONTH", 5, 2, None, "INTERVAL YEAR (2) TO MONTH", 1),
    ("CLOB", 4000, None, None, "CLOB", 5),
    ("NCLOB", 4000, None, None, "NCLOB", 1),
    ("BLOB", 4000, None, None, "BLOB", 4),
    ("LONG", 0, None, None, "LONG", 2),
    ("LONG RAW", 0, None, None, "LONG RAW", 1),
    ("RAW", 16, None, None, "RAW(16)", 3),
    ("RAW", 2000, None, None, "RAW(2000)", 1),
    ("ROWID", 10, None, None, "ROWID", 1),
    ("UROWID", 4000, None, None, "UROWID(4000)", 1),
    ("XMLTYPE", 2000, None, None, '"SYS"."XMLTYPE"', 2),
    ("BFILE", 530, None, None, "BFILE", 1),
    ("SDO_GEOMETRY", 1, None, None, '"MDSYS"."SDO_GEOMETRY"', 1),
    ("ANYDATA", 1, None, None, '"SYS"."ANYDATA"', 1),
    ("ADDR_T", 1, None, None, '"FUZZ"."ADDR_T"', 1),
    ("JSON", 8200, None, None, "JSON", 1),
    ("BOOLEAN", 1, None, None, "BOOLEAN", 1),
]
TYPE_WEIGHTS = [t[5] for t in TYPES]

NUMERIC = {"NUMBER", "FLOAT", "BINARY_DOUBLE", "BINARY_FLOAT"}
TEXTUAL = {"VARCHAR2", "NVARCHAR2", "CHAR", "NCHAR"}
LOBS = {"CLOB", "NCLOB", "BLOB"}


COMMENT_TEXTS = [
    "Plain comment",
    "Has 'quotes' inside",
    "Two lines\nof comment",
    "Caf\u00e9 latt\u00e9 with accents",
    "\uc9c1\uc6d0 \ud14c\uc774\ube14 (Hangul)",
    "Semi; colon -- and dashes",
    "",
]

FEATURES = [
    ("materialized_views", "schema total"),
    ("db_links", "owned or public"),
    ("vpd_policies", "row level security"),
    ("scheduler_jobs", "schema total"),
    ("legacy_jobs", "dbms_job"),
    ("queues", "advanced queuing"),
    ("triggers", "schema total"),
    ("object_types", "user defined"),
    ("partitioned_tables", "schema total"),
    ("iot_tables", "index organized"),
    ("external_tables", "schema total"),
    ("temporary_tables", "global temporary"),
]

CHARSETS = ["AL32UTF8", "AL32UTF8", "WE8ISO8859P1", "KO16MSWIN949", "WE8MSWIN1252"]
VERSIONS = [
    ("Oracle Database 11g Enterprise Edition ", "11.2.0.4.0"),
    ("Oracle Database 12c Enterprise Edition ", "12.2.0.1.0"),
    ("Oracle Database 19c Enterprise Edition ", "19.0.0.0.0"),
    ("Oracle Database 21c Express Edition ", "21.0.0.0.0"),
    ("Oracle Database 23ai Free ", "23.0.0.0.0"),
]

ERROR_SPOOL = "\n\nERROR at line 1:\nORA-00942: table or view does not exist\n\n\n"


def q(name: str) -> str:
    """Quote an identifier the way Oracle SQL needs it."""
    return '"' + name + '"'


_DECLARED_WIDTH = re.compile(r"\((\d+)( CHAR| BYTE)?\)")


def char_facts(data_type: str, ddl: str) -> tuple[int | None, str | None]:
    """CHAR_LENGTH and CHAR_USED as the catalog reports them for a
    string column: the declared width in characters, and B or C."""
    if data_type not in TEXTUAL:
        return None, None
    m = _DECLARED_WIDTH.search(ddl)
    if m is None:
        return None, None
    used = "C" if (m.group(2) or "").strip() == "CHAR" or data_type[0] == "N" else "B"
    return int(m.group(1)), used


def esc(text: str) -> str:
    return text.replace("'", "''")


@dataclass
class Column:
    name: str
    data_type: str
    length: int | None
    precision: int | None
    scale: int | None
    nullable: bool
    ddl: str


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    pk: str | None = None
    pk_cols: list[str] = field(default_factory=list)
    uk: str | None = None
    uk_cols: list[str] = field(default_factory=list)
    partitioned: bool = False
    temporary: bool = False
    partition_clause: str = ""
    plain: bool = True

    def column(self, kinds: set[str]) -> Column | None:
        for c in self.columns:
            if c.data_type in kinds:
                return c
        return None

    def numeric(self) -> Column | None:
        return self.column(NUMERIC)

    def textual(self) -> Column | None:
        return self.column(TEXTUAL)

    def dated(self) -> Column | None:
        return self.column({"DATE"})


@dataclass
class Manifest:
    """What the generator produced, for the runner's expectations."""

    seed: int
    objects: list[tuple[str, str, str]]
    error_spools: list[str] = field(default_factory=list)
    lossy_spools: list[str] = field(default_factory=list)
    torn_spools: list[str] = field(default_factory=list)
    missing_spools: list[str] = field(default_factory=list)

    def as_json(self) -> str:
        return json.dumps(
            {
                "seed": self.seed,
                "objects": self.objects,
                "error_spools": self.error_spools,
                "lossy_spools": self.lossy_spools,
                "torn_spools": self.torn_spools,
                "missing_spools": self.missing_spools,
            },
            ensure_ascii=True,
            indent=1,
        )


class Estate:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.rows: dict[str, list[list[object]]] = {name: [] for name in HEADERS}
        self.ddl: dict[str, list[str]] = {
            "ddl_tables.sql": [],
            "ddl_views.sql": [],
            "ddl_sequences.sql": [],
        }
        self.tables: list[Table] = []
        self.views: list[tuple[str, list[str]]] = []
        self.sequences: list[str] = []
        self.routines: list[tuple[str, str]] = []
        self.packages: list[str] = []
        self.used_names: dict[str, bool] = {}
        self.reserved_left = list(RESERVED)
        self.rng.shuffle(self.reserved_left)
        self.sys_counter = 8000
        self.objects: list[tuple[str, str, str]] = []
        self.virtual: dict[str, set[str]] = {}

    # -- helpers ---------------------------------------------------------

    def add(self, spool: str, *values: object) -> None:
        self.rows[spool].append(list(values))

    def obj(self, name: str, otype: str, status: str = "VALID") -> None:
        self.add("objects.csv", OWNER, name, otype, status, STAMP, STAMP)
        self.objects.append((OWNER, name, otype))

    def sysname(self, prefix: str = "SYS_C00") -> str:
        self.sys_counter += 1
        return f"{prefix}{self.sys_counter}"

    def unique(self, candidate: str) -> str:
        name = candidate
        while name in self.used_names:
            name = f"{candidate}_{self.rng.randrange(10, 99)}"
        self.used_names[name] = True
        return name

    def styled_name(self, base: str, i: int, allow_reserved: bool = True) -> str:
        """A name in one of the adversarial styles."""
        roll = self.rng.random()
        if roll < 0.50:
            return f"{base}_{i}"
        if roll < 0.58 and allow_reserved and self.reserved_left:
            return self.reserved_left.pop()
        if roll < 0.66:
            return f"Mixed{base.title()}{i}"
        if roll < 0.72:
            return f"{base}${i}#X"
        if roll < 0.76:
            return f"{base} WITH SPACE {i}"
        if roll < 0.79:
            return f"{base}, COMMA {i}"
        if roll < 0.87:
            return f"LONG_{base}_" + "X" * 66 + f"_{i}"
        if roll < 0.94:
            return f"{self.rng.choice(CJK)}_{base}_{i}"
        return self.rng.choice(CJK[-1:]) * 8 + f"_{i}"

    def pick_type(self) -> tuple[str, int, int | None, int | None, str]:
        t = self.rng.choices(TYPES, weights=TYPE_WEIGHTS)[0]
        return t[0], t[1], t[2], t[3], t[4]

    # -- tables ----------------------------------------------------------

    def make_tables(self) -> None:
        count = self.rng.randint(12, 28)
        for i in range(count):
            self.make_table(i)
        # A pair whose names agree on their first 63 bytes: PostgreSQL
        # would fold them together, so the converter must refuse one.
        if self.rng.random() < 0.6:
            stem = "CLASH_" + "Z" * 57
            for tag in ("A", "B"):
                self.make_table(count + 1, forced_name=self.unique(f"{stem}_{tag}"))
        # A table named exactly like a partition child of another one.
        if self.rng.random() < 0.4:
            parents = [t for t in self.tables if t.partitioned and t.plain]
            if parents:
                parent = self.rng.choice(parents)
                self.make_table(
                    count + 3, forced_name=self.unique(f"{parent.name}_P_1")
                )

    def make_table(self, i: int, forced_name: str | None = None) -> None:
        rng = self.rng
        word = rng.choice(TABLE_WORDS)
        name = forced_name or self.unique(self.styled_name(word, i))
        table = Table(name=name, plain=name.isidentifier() and name.isupper())
        used: dict[str, bool] = {}

        def col_name(base: str) -> str:
            candidate = base
            while candidate in used:
                candidate = f"{base}_{rng.randrange(1, 99)}"
            used[candidate] = True
            return candidate

        with_id = rng.random() < 0.85
        if with_id:
            table.columns.append(
                Column(col_name("ID"), "NUMBER", 22, 10, 0, False, "NUMBER(10,0)")
            )
        for k in range(rng.randint(2, 9)):
            dtype, length, precision, scale, ddl = self.pick_type()
            base = rng.choice(COLUMN_WORDS)
            roll = rng.random()
            if roll < 0.10 and self.reserved_left:
                base = self.reserved_left.pop()
            elif roll < 0.16:
                base = f"Mixed{base.title()}"
            elif roll < 0.20:
                base = f"{base}$#{k}"
            elif roll < 0.25:
                base = f"{rng.choice(CJK)}_{base}"
            elif roll < 0.29:
                base = "LONGCOL_" + "Y" * 60 + f"_{k}"
            table.columns.append(
                Column(
                    col_name(base),
                    dtype,
                    length,
                    precision,
                    scale,
                    rng.random() < 0.7,
                    ddl,
                )
            )
        table.temporary = not forced_name and rng.random() < 0.05

        # Keys.
        if with_id and rng.random() < 0.9:
            table.pk = (
                self.sysname()
                if rng.random() < 0.3
                else self.unique(f"PK_{name}"[:120])
            )
            table.pk_cols = [table.columns[0].name]
            if rng.random() < 0.15 and len(table.columns) > 2:
                second = table.columns[1]
                if second.data_type not in LOBS | {"LONG", "LONG RAW"}:
                    second.nullable = False
                    table.pk_cols.append(second.name)
        candidates = [
            c for c in table.columns[1:] if c.data_type in TEXTUAL | {"DATE"} | NUMERIC
        ]
        if candidates and rng.random() < 0.3:
            table.uk = self.unique(f"UK_{name}"[:120])
            table.uk_cols = [rng.choice(candidates).name]

        self.tables.append(table)
        self.emit_table(table, i)

    def emit_table(self, table: Table, i: int) -> None:
        rng = self.rng
        name = table.name
        self.obj(name, "TABLE")
        self.add(
            "tables.csv",
            OWNER,
            name,
            rng.choice([None, 0, 12, 4500, 1_200_000]),
            rng.choice([None, 40, 180]),
            "NO",
            "Y" if table.temporary else "N",
            "         1",
        )
        for pos, c in enumerate(table.columns, start=1):
            self.add(
                "columns.csv",
                OWNER,
                name,
                c.name,
                pos,
                c.data_type,
                c.length,
                c.precision,
                c.scale,
                "Y" if c.nullable else "N",
                *char_facts(c.data_type, c.ddl),
            )
            if c.data_type in LOBS:
                lob = f"SYS_LOB{self.sys_counter:07d}C{pos:05d}$$"
                self.obj(lob, "LOB")
                self.add(
                    "indexes.csv",
                    OWNER,
                    f"SYS_IL{self.sys_counter:07d}C{pos:05d}$$",
                    name,
                    "LOB",
                    "UNIQUE",
                    "VALID",
                    "Y",
                    "1",
                )
                self.obj(f"SYS_IL{self.sys_counter:07d}C{pos:05d}$$", "INDEX")
            if not c.nullable:
                self.add(
                    "constraints.csv",
                    OWNER,
                    self.sysname(),
                    name,
                    "C",
                    "ENABLED",
                    None,
                    None,
                    None,
                )
                self.add(
                    "check_conditions.csv",
                    OWNER,
                    f"SYS_C00{self.sys_counter}",
                    f'"{c.name}" IS NOT NULL',
                    0,
                )
            if c.data_type not in {"LONG", "LONG RAW"} and rng.random() < 0.2:
                self.add_default(table, c)
            if rng.random() < 0.2:
                self.add(
                    "column_comments.csv",
                    OWNER,
                    name,
                    c.name,
                    rng.choice(COMMENT_TEXTS),
                )
        if rng.random() < 0.35:
            self.add("table_comments.csv", OWNER, name, rng.choice(COMMENT_TEXTS))

        # Keys, their backing indexes, and the constraint rows.
        for cname, cols, ctype in (
            (table.pk, table.pk_cols, "P"),
            (table.uk, table.uk_cols, "U"),
        ):
            if not cname:
                continue
            self.add(
                "constraints.csv",
                OWNER,
                cname,
                name,
                ctype,
                "DISABLED" if rng.random() < 0.05 else "ENABLED",
                None,
                None,
                None,
            )
            for pos, col in enumerate(cols, start=1):
                self.add("constraint_columns.csv", OWNER, cname, col, pos)
            self.add(
                "indexes.csv",
                OWNER,
                cname,
                name,
                "NORMAL",
                "UNIQUE",
                "VALID",
                "Y" if cname.startswith("SYS_C") else "N",
                "1",
            )
            self.obj(cname, "INDEX")
            for pos, col in enumerate(cols, start=1):
                self.add("index_columns.csv", OWNER, cname, col, pos)

        self.add_foreign_keys(table)
        self.add_checks(table)
        self.add_indexes(table)
        if not table.temporary and rng.random() < 0.3:
            self.add_partitioning(table)
        self.add_grants(name, "TABLE")
        self.ddl["ddl_tables.sql"].append(self.table_ddl(table))

    def table_ddl(self, table: Table) -> str:
        cols = []
        for c in table.columns:
            line = f"\t{q(c.name)} {c.ddl}"
            if not c.nullable:
                line += " NOT NULL ENABLE"
            cols.append(line)
        if table.pk:
            keys = ", ".join(q(c) for c in table.pk_cols)
            cols.append(
                f"\t CONSTRAINT {q(table.pk)} PRIMARY KEY ({keys})\n"
                "  USING INDEX  ENABLE"
            )
        head = "GLOBAL TEMPORARY TABLE" if table.temporary else "TABLE"
        body = ",\n".join(cols)
        text = (
            f"-- PGRECON_OBJECT TABLE {OWNER}.{table.name}\n\n"
            f"  CREATE {head} {q(OWNER)}.{q(table.name)}\n   ({body}\n   ) "
        )
        if table.temporary:
            text += "ON COMMIT PRESERVE ROWS "
        text += table.partition_clause + ";\n"
        return text

    def add_default(self, table: Table, c: Column) -> None:
        """A default Oracle would accept for the column's type."""
        rng = self.rng
        dtype = c.data_type
        if dtype in NUMERIC:
            pool = ["0 ", "1.5 ", "-1 ", "NULL "]
        elif dtype in TEXTUAL:
            # Sized to the column: Oracle accepts an oversized default at
            # CREATE and fails the row; that is not the shape to fuzz.
            width = (c.length or 0) // (2 if dtype.startswith("N") else 1)
            pool = ["'N' ", "NULL "]
            if width >= 8:
                pool += ["'O''Brien' ", "TO_CHAR(SYSDATE, 'YYYY') "]
            if width >= 32:
                pool += [
                    "USER ",
                    "SYS_CONTEXT('USERENV', 'SESSION_USER') ",
                    "sys_guid() ",
                ]
        elif dtype == "DATE" or dtype.startswith("TIMESTAMP"):
            pool = [
                "SYSDATE ",
                "SYSTIMESTAMP ",
                "TRUNC(SYSDATE) ",
                "TO_DATE('2020-01-01', 'YYYY-MM-DD') ",
                "CURRENT_TIMESTAMP ",
            ]
        elif dtype in ("CLOB", "NCLOB"):
            pool = ["EMPTY_CLOB() "]
        elif dtype == "BLOB":
            pool = ["EMPTY_BLOB() "]
        elif dtype == "RAW":
            pool = ["sys_guid() ", "HEXTORAW('FF') "]
        else:
            pool = ["NULL "]
        roll = rng.random()
        if roll < 0.12 and dtype == "NUMBER" and self.sequences:
            seq = rng.choice(self.sequences)
            spelled = rng.choice(
                [
                    f'{q(OWNER)}.{q(seq)}."NEXTVAL"',
                    f"{q(OWNER)}.{q(seq)}.nextval",
                    f"{q(seq)}.NEXTVAL",
                ]
            )
            self.add("column_defaults.csv", OWNER, table.name, c.name, spelled, "NO", 0)
        elif roll < 0.20 and dtype == "NUMBER":
            seq = f"ISEQ$$_{self.sys_counter + 70000}"
            self.sysname()
            self.obj(seq, "SEQUENCE")
            self.add("sequences.csv", OWNER, seq, "1", "9" * 28, "1", "N", "20", "41")
            text = f"{q(OWNER)}.{q(seq)}.nextval"
            self.add("column_defaults.csv", OWNER, table.name, c.name, text, "NO", 0)
        elif roll < 0.30:
            # A virtual column reads earlier plain columns only: Oracle
            # refuses one virtual column over another.
            earlier = table.columns[: table.columns.index(c)]
            virtual = self.virtual.setdefault(table.name, set())
            others = [
                o for o in earlier if o.data_type in NUMERIC and o.name not in virtual
            ]
            if dtype in NUMERIC and others:
                text = f"{q(others[0].name)} * 2"
                virtual.add(c.name)
                self.add(
                    "column_defaults.csv", OWNER, table.name, c.name, text, "YES", 0
                )
            elif dtype in TEXTUAL:
                texts = [
                    o
                    for o in earlier
                    if o.data_type in TEXTUAL and o.name not in virtual
                ]
                if texts:
                    text = f"UPPER({q(texts[0].name)})"
                    virtual.add(c.name)
                    self.add(
                        "column_defaults.csv",
                        OWNER,
                        table.name,
                        c.name,
                        text,
                        "YES",
                        0,
                    )
        elif roll < 0.36:
            self.add(
                "column_defaults.csv",
                OWNER,
                table.name,
                c.name,
                "TO_DATE('2020-01-01', 'YY",
                "NO",
                1,
            )
        else:
            self.add(
                "column_defaults.csv",
                OWNER,
                table.name,
                c.name,
                rng.choice(pool),
                "NO",
                0,
            )

    def add_foreign_keys(self, table: Table) -> None:
        rng = self.rng
        parents = [t for t in self.tables[:-1] if t.pk]
        if not parents or rng.random() > 0.5:
            pass
        else:
            parent = rng.choice(parents)
            self.foreign_key(table, parent, parent.pk or "", parent.pk_cols)
        if table.pk and len(table.pk_cols) == 1 and rng.random() < 0.1:
            self.foreign_key(table, table, table.pk, table.pk_cols, self_ref=True)
        uk_parents = [t for t in self.tables[:-1] if t.uk]
        if uk_parents and rng.random() < 0.15:
            parent = rng.choice(uk_parents)
            self.foreign_key(table, parent, parent.uk or "", parent.uk_cols)
        if rng.random() < 0.06:
            # A parent in another schema that is not in the dump.
            cname = self.unique(f"FK_{table.name}_EXT"[:120])
            col = self.fk_column(table, "EXT")
            self.add(
                "constraints.csv",
                OWNER,
                cname,
                table.name,
                "R",
                "ENABLED",
                "OTHER_SCHEMA",
                "PK_ELSEWHERE",
                "NO ACTION",
            )
            self.add("constraint_columns.csv", OWNER, cname, col, 1)

    def fk_column(self, table: Table, tag: str, like: Column | None = None) -> str:
        """A referencing column, typed like the referenced one, as
        Oracle requires."""
        base = f"{tag}_ID"
        existing = {c.name for c in table.columns}
        name = base
        while name in existing:
            name = f"{base}_{self.rng.randrange(1, 99)}"
        if like is None:
            col = Column(name, "NUMBER", 22, 10, 0, True, "NUMBER(10,0)")
        else:
            col = Column(
                name,
                like.data_type,
                like.length,
                like.precision,
                like.scale,
                True,
                like.ddl,
            )
        table.columns.append(col)
        self.add(
            "columns.csv",
            OWNER,
            table.name,
            name,
            len(table.columns),
            col.data_type,
            col.length,
            col.precision,
            col.scale,
            "Y",
            *char_facts(col.data_type, col.ddl),
        )
        return name

    def foreign_key(
        self,
        table: Table,
        parent: Table,
        ref_constraint: str,
        ref_cols: list[str],
        self_ref: bool = False,
    ) -> None:
        rng = self.rng
        tag = "PARENT" if self_ref else parent.name[:12].replace(" ", "_")
        cname = self.unique(f"FK_{table.name}_{tag}"[:120])
        by_name = {c.name: c for c in parent.columns}
        cols = [self.fk_column(table, tag, by_name.get(ref)) for ref in ref_cols]
        if rng.random() < 0.05:
            # Column count that does not match the referenced key.
            cols.append(self.fk_column(table, tag + "_X"))
        self.add(
            "constraints.csv",
            OWNER,
            cname,
            table.name,
            "R",
            "DISABLED" if rng.random() < 0.05 else "ENABLED",
            OWNER,
            ref_constraint,
            rng.choice(["NO ACTION", "CASCADE", "SET NULL"]),
        )
        for pos, col in enumerate(cols, start=1):
            self.add("constraint_columns.csv", OWNER, cname, col, pos)
        if rng.random() < 0.5:
            iname = self.unique(f"IX_{cname}"[:120])
            self.add(
                "indexes.csv",
                OWNER,
                iname,
                table.name,
                "NORMAL",
                "NONUNIQUE",
                "VALID",
                "N",
                "1",
            )
            self.obj(iname, "INDEX")
            for pos, col in enumerate(cols, start=1):
                self.add("index_columns.csv", OWNER, iname, col, pos)

    def add_checks(self, table: Table) -> None:
        rng = self.rng
        if rng.random() > 0.55:
            return
        num = table.numeric()
        txt = table.textual()
        dat = table.dated()
        pool: list[str] = []
        if num:
            n = q(num.name)
            pool += [f"{n} > 0", f"{n} BETWEEN 1 AND 10", f"NVL({n}, 0) >= 0"]
        if txt:
            t = q(txt.name)
            pool += [
                f"{t} IN ('A', 'B', 'C')",
                f"LENGTH({t}) < 50",
                f"REGEXP_LIKE({t}, '^[A-Z]')",
                f"UPPER({t}) = {t}",
                f"DECODE({t}, 'X', 1, 0) = 1",
                f"{t} <> ''",
            ]
        if dat:
            d = q(dat.name)
            pool += [
                f"{d} > TO_DATE('2000-01-01', 'YYYY-MM-DD')",
                f"{d} <= SYSDATE",
                f"TRUNC({d}) = {d}",
            ]
        if num and dat:
            pool.append(f"{q(num.name)} < 100 OR {q(dat.name)} IS NULL")
        long_col = table.column({"LONG", "LONG RAW"})
        if long_col:
            pool.append(f"{q(long_col.name)} IS NOT NULL OR 1 = 1")
        for k, condition in enumerate(rng.sample(pool, min(len(pool), 2))):
            cname = self.unique(f"CK_{table.name}_{k}"[:120])
            self.add(
                "constraints.csv",
                OWNER,
                cname,
                table.name,
                "C",
                "ENABLED",
                None,
                None,
                None,
            )
            roll = rng.random()
            if roll < 0.06:
                self.add("check_conditions.csv", OWNER, cname, condition[:8], 1)
            elif roll < 0.10:
                pass  # a check with no condition row at all
            else:
                self.add("check_conditions.csv", OWNER, cname, condition, 0)

    def add_indexes(self, table: Table) -> None:
        rng = self.rng
        plain_cols = [
            c
            for c in table.columns
            if c.data_type not in LOBS | {"LONG", "LONG RAW", "BFILE"}
        ]
        if not plain_cols:
            return
        for k in range(rng.randint(0, 3)):
            roll = rng.random()
            if roll < 0.05:
                iname = table.name  # collides with its own table
            elif roll < 0.09 and self.sequences:
                iname = rng.choice(self.sequences)
            else:
                iname = self.unique(f"IX_{table.name}_{k}"[:120])
            itype = rng.choices(
                [
                    "NORMAL",
                    "NORMAL",
                    "NORMAL",
                    "BITMAP",
                    "FUNCTION-BASED NORMAL",
                    "DOMAIN",
                    "NORMAL/REV",
                ],
                weights=[40, 20, 10, 10, 15, 3, 2],
            )[0]
            unique = "UNIQUE" if rng.random() < 0.2 else "NONUNIQUE"
            status = "UNUSABLE" if rng.random() < 0.05 else "VALID"
            self.add(
                "indexes.csv", OWNER, iname, table.name, itype, unique, status, "N", "1"
            )
            self.obj(iname, "INDEX")
            if rng.random() < 0.03:
                continue  # an index with no column facts at all
            cols = rng.sample(plain_cols, min(len(plain_cols), rng.randint(1, 3)))
            for pos, c in enumerate(cols, start=1):
                if itype == "FUNCTION-BASED NORMAL" and pos == 1:
                    expr = rng.choice(
                        [
                            f"UPPER({q(c.name)})",
                            f"NVL({q(c.name)}, 0)",
                            f"SYS_OP_MAP_NONNULL({q(c.name)})",
                            f"{q(c.name)} DESC",
                            f"TRUNC({q(c.name)})",
                        ]
                    )
                    self.add(
                        "index_columns.csv", OWNER, iname, f"SYS_NC0000{pos}$", pos
                    )
                    torn = rng.random() < 0.1
                    self.add(
                        "index_expressions.csv",
                        OWNER,
                        iname,
                        pos,
                        expr[:6] if torn else expr,
                        1 if torn else 0,
                    )
                else:
                    self.add("index_columns.csv", OWNER, iname, c.name, pos)
            if table.partitioned or rng.random() < 0.05:
                self.add(
                    "part_indexes.csv",
                    OWNER,
                    iname,
                    table.name,
                    rng.choice(["LOCAL", "GLOBAL"]),
                )

    def add_partitioning(self, table: Table) -> None:
        rng = self.rng
        name = table.name
        dat, num = table.dated(), table.numeric()
        # List bounds must fit the key column, as Oracle insists.
        txt = next(
            (
                c
                for c in table.columns
                if c.data_type in TEXTUAL and (c.length or 0) >= 8
            ),
            None,
        )
        kinds = []
        if dat:
            kinds.append("RANGE_DATE")
        if num:
            kinds += ["RANGE_NUM", "HASH"]
        if txt:
            kinds.append("LIST")
        kinds += ["REFERENCE", "SYSTEM"] if rng.random() < 0.12 else []
        if not kinds:
            return
        kind = rng.choice(kinds)
        table.partitioned = True
        self.rows["tables.csv"][-1][4] = "YES"
        parts: list[tuple[str, str | None, int]] = []
        interval = None
        sub = "NONE"
        key: list[str] = []
        if kind == "RANGE_DATE" and dat:
            ptype = "RANGE"
            key = [dat.name]
            for k, year in enumerate((2023, 2024, 2025), start=1):
                parts.append(
                    (
                        f"P_{k}",
                        f"TO_DATE(' {year}-01-01 00:00:00', 'SYYYY-MM-DD"
                        " HH24:MI:SS', 'NLS_CALENDAR=GREGORIAN')",
                        0,
                    )
                )
            if rng.random() < 0.5:
                parts.append(("P_MAX", "MAXVALUE", 0))
            elif rng.random() < 0.4:
                interval = "NUMTOYMINTERVAL(1, 'MONTH')"
        elif kind == "RANGE_NUM" and num:
            ptype = "RANGE"
            key = [num.name]
            parts = [
                ("P_LOW", "100", 0),
                ("P_MID", "1000", 0),
                ("P_HIGH", "MAXVALUE", 0),
            ]
            if rng.random() < 0.15 and len(table.columns) > 2:
                # A second key column with a bound of its own type.
                other = next(
                    (
                        c
                        for c in table.columns
                        if c is not num and c.data_type in NUMERIC | TEXTUAL
                    ),
                    None,
                )
                if other is not None:
                    key.append(other.name)
                    second = "200" if other.data_type in NUMERIC else "'X'"
                    parts = [
                        ("P_A", f"100, {second}", 0),
                        ("P_B", "MAXVALUE, MAXVALUE", 0),
                    ]
        elif kind == "LIST" and txt:
            ptype = "LIST"
            key = [txt.name]
            parts = [("P_AB", "'A', 'B'", 0), ("P_C", "'O''Brien', 'C'", 0)]
            parts.append(("P_REST", rng.choice(["DEFAULT", "NULL", "'Z', NULL"]), 0))
        elif kind == "HASH" and num:
            ptype = "HASH"
            key = [num.name]
            parts = [(f"SYS_P{100 + k}", None, 0) for k in range(4)]
        elif kind == "REFERENCE":
            ptype = "REFERENCE"
            parts = [("P_REF_1", None, 0), ("P_REF_2", None, 0)]
        else:
            ptype = "SYSTEM"
            parts = [("P_SYS_1", None, 0), ("P_SYS_2", None, 0)]
        if parts and rng.random() < 0.08:
            pname, high, _ = parts[-1]
            parts[-1] = (pname, (high or "")[:10], 1)
        if ptype in ("RANGE", "LIST") and rng.random() < 0.3:
            sub = "HASH" if num else "LIST"
            subkey = num.name if num else (txt.name if txt else key[0])
            self.add("part_subkey_columns.csv", OWNER, name, subkey, 1)
            for pname, _, _ in parts:
                for s in range(2):
                    high = None if sub == "HASH" else ("'S1'" if s == 0 else "DEFAULT")
                    self.add(
                        "part_subpartitions.csv",
                        OWNER,
                        name,
                        pname,
                        f"{pname}_SP{s + 1}",
                        s + 1,
                        high,
                        0,
                    )
        count = 1048575 if interval else len(parts)
        self.add("part_tables.csv", OWNER, name, ptype, sub, count, interval)
        for pos, col in enumerate(key, start=1):
            self.add("part_key_columns.csv", OWNER, name, col, pos)
        for pos, (pname, high, truncated) in enumerate(parts, start=1):
            self.add("part_partitions.csv", OWNER, name, pname, pos, high, truncated)
        if key:
            spec = ", ".join(q(c) for c in key)
            table.partition_clause = f"\n  PARTITION BY {ptype} ({spec})\n (PARTITION "
            table.partition_clause += ", PARTITION ".join(
                f"{q(p)} VALUES LESS THAN ({h})" if h else q(p) for p, h, _ in parts
            )
            table.partition_clause += ")"

    # -- everything else -------------------------------------------------

    def make_sequences(self) -> None:
        rng = self.rng
        for i in range(max(2, len(self.tables) // 3)):
            name = self.unique(self.styled_name("SEQ", i, allow_reserved=False))
            self.sequences.append(name)
            self.obj(name, "SEQUENCE")
            shape = rng.random()
            if shape < 0.55:
                row = ("1", "9" * 28, "1", "N", "20", str(rng.randrange(1, 10**6)))
            elif shape < 0.70:
                row = ("1", "999999", "1", "Y", "0", "17")
            elif shape < 0.80:
                row = ("-1000", "-1", "-1", "N", "20", "-5")
            elif shape < 0.88:
                row = ("1", "9" * 28, "1", "N", "20", "9" * 20)
            elif shape < 0.94:
                row = ("1", "100", "1", "N", "20", "500")
            else:
                row = ("1", "1.5E+28", "1", "N", "20", "abc")
            self.add("sequences.csv", OWNER, name, *row)
            self.ddl["ddl_sequences.sql"].append(
                f"-- PGRECON_OBJECT SEQUENCE {OWNER}.{name}\n\n"
                f"   CREATE SEQUENCE  {q(OWNER)}.{q(name)}  MINVALUE {row[0]}"
                f" MAXVALUE {row[1]} INCREMENT BY {row[2]} START WITH {row[5]}"
                f" CACHE 20 NOORDER  {'CYCLE' if row[3] == 'Y' else 'NOCYCLE'} ;\n"
            )
            self.add_grants(name, "SEQUENCE")

    def make_colliding_sequence(self) -> None:
        if self.tables and self.rng.random() < 0.15:
            name = self.rng.choice(self.tables).name
            self.sequences.append(name)
            self.obj(name, "SEQUENCE")
            self.add("sequences.csv", OWNER, name, "1", "9" * 28, "1", "N", "20", "7")

    def make_views(self) -> None:
        rng = self.rng
        tables = [t for t in self.tables if t.columns]
        for i in range(max(2, len(tables) // 3)):
            base = rng.choice(tables)
            roll = rng.random()
            if roll < 0.05:
                name = rng.choice(tables).name  # collides with a table
            else:
                name = self.unique(self.styled_name("V", i, allow_reserved=False))
            cols, body, deps = self.view_body(base)
            header = ", ".join(q(c) for c in cols)
            self.views.append((name, cols))
            self.obj(name, "VIEW")
            self.ddl["ddl_views.sql"].append(
                f"-- PGRECON_OBJECT VIEW {OWNER}.{name}\n\n"
                f"  CREATE OR REPLACE FORCE EDITIONABLE VIEW {q(OWNER)}.{q(name)}"
                f" ({header}) AS\n  {body};\n"
            )
            for dep_name, dep_type in deps:
                self.add(
                    "dependencies.csv", OWNER, name, "VIEW", OWNER, dep_name, dep_type
                )
            self.add_grants(name, "VIEW")

    def view_body(self, base: Table) -> tuple[list[str], str, list[tuple[str, str]]]:
        rng = self.rng
        t = q(base.name)
        c1 = base.columns[0]
        c2 = base.columns[-1]
        num, txt, dat = base.numeric(), base.textual(), base.dated()
        deps = [(base.name, "TABLE")]
        roll = rng.random()
        if roll < 0.25:
            return (
                [c1.name, c2.name],
                f"SELECT {q(c1.name)}, {q(c2.name)}\n  FROM {t}\n"
                f" WHERE {q(c1.name)} IS NOT NULL",
                deps,
            )
        if roll < 0.40 and num and txt:
            return (
                [txt.name, "CNT", "TOTAL"],
                f"SELECT {q(txt.name)}, COUNT(*) AS CNT, SUM(NVL({q(num.name)}, 0))"
                f" AS TOTAL\n  FROM {t}\n GROUP BY {q(txt.name)}",
                deps,
            )
        if roll < 0.50 and len(self.tables) > 1:
            # Join columns of one family; Oracle rejects the rest too.
            other = rng.choice(self.tables)
            pair = None
            for family in (NUMERIC, TEXTUAL, {"DATE"}):
                left = base.column(family)
                right = other.column(family)
                if left and right:
                    pair = (left, right)
                    break
            if pair is not None:
                deps.append((other.name, "TABLE"))
                left, right = pair
                return (
                    ["A_COL", "B_COL"],
                    f"SELECT a.{q(left.name)} AS A_COL, b.{q(right.name)} AS B_COL\n"
                    f"  FROM {t} a, {q(other.name)} b\n"
                    f" WHERE a.{q(left.name)} = b.{q(right.name)} (+)",
                    deps,
                )
        if roll < 0.58:
            # The hierarchy joins the key to a column of its own family.
            mate = next(
                (
                    c
                    for c in base.columns[1:]
                    if (c.data_type in NUMERIC) == (c1.data_type in NUMERIC)
                    and (c.data_type in TEXTUAL) == (c1.data_type in TEXTUAL)
                ),
                None,
            )
            if mate is None:
                # No column of the key's family: a plain projection instead.
                return (
                    [c1.name, c2.name],
                    f"SELECT {q(c1.name)}, {q(c2.name)} FROM {t}",
                    deps,
                )
            return (
                [c1.name, "LVL"],
                f"SELECT {q(c1.name)}, LEVEL AS LVL\n  FROM {t}\n"
                f" START WITH {q(mate.name)} IS NULL\n"
                f" CONNECT BY PRIOR {q(c1.name)} = {q(mate.name)}",
                deps,
            )
        if roll < 0.66:
            return (
                [c1.name],
                f"SELECT {q(c1.name)}\n  FROM (SELECT {q(c1.name)} FROM {t}"
                f" ORDER BY {q(c1.name)})\n WHERE ROWNUM <= 10",
                deps,
            )
        if roll < 0.76 and self.views:
            vname, vcols = rng.choice(self.views)
            deps = [(vname, "VIEW")]
            return (
                vcols,
                f"SELECT {', '.join(q(c) for c in vcols)}\n  FROM {q(vname)}\n"
                f" WHERE {q(vcols[0])} IS NOT NULL",
                deps,
            )
        if roll < 0.84 and txt and dat:
            return (
                ["ST", "YM"],
                f"SELECT DECODE({q(txt.name)}, 'A', 'Active', 'Other') AS ST,"
                f" TO_CHAR({q(dat.name)}, 'YYYY-MM') AS YM\n  FROM {t}",
                deps,
            )
        if roll < 0.90:
            return ["X"], "SELECT FROM WHERE (((", []
        if roll < 0.95 and txt and num:
            return (
                ["A", "B"],
                f"SELECT * FROM (SELECT {q(txt.name)} AS K, {q(num.name)} AS V"
                f" FROM {t})\n PIVOT (SUM(V) FOR K IN ('A' AS A, 'B' AS B))",
                deps,
            )
        return (
            [c.name for c in base.columns],
            f"SELECT {', '.join(q(c.name) for c in base.columns)}\n  FROM {t}"
            " WITH READ ONLY",
            deps,
        )

    def make_mviews(self) -> None:
        rng = self.rng
        candidates = [t for t in self.tables if t.numeric() and t.textual()]
        for i in range(rng.randint(0, 2)):
            if not candidates:
                return
            base = rng.choice(candidates)
            num, txt = base.numeric(), base.textual()
            assert num is not None and txt is not None
            name = self.unique(f"MV_{base.name}_{i}"[:120])
            self.obj(name, "MATERIALIZED VIEW")
            self.obj(name, "TABLE")
            # Aliases that cannot repeat the grouping column's name.
            cnt = "HEADCOUNT" if txt.name.upper() != "HEADCOUNT" else "HEADCOUNT_2"
            tot = "TOTAL" if txt.name.upper() != "TOTAL" else "TOTAL_2"
            if rng.random() < 0.3:
                query = (
                    f"SELECT {q(txt.name)}, COUNT(*) AS {cnt}, 0 AS {tot}"
                    f" FROM {q(OWNER)}.NOPE"
                )
            else:
                query = (
                    f"SELECT {q(txt.name)}, COUNT(*) AS {cnt},"
                    f" SUM({q(num.name)}) AS {tot}\n  FROM {q(base.name)}\n"
                    f" GROUP BY {q(txt.name)}"
                )
            self.add(
                "mviews.csv",
                OWNER,
                name,
                rng.choice(["Y", "N"]),
                rng.choice(["COMPLETE", "FAST", "FORCE"]),
                query,
            )
            self.add("tables.csv", OWNER, name, 12, 40, "NO", "N", "         1")
            for pos, (col, dtype) in enumerate(
                ((txt.name, txt), (cnt, None), (tot, None)), start=1
            ):
                self.add(
                    "columns.csv",
                    OWNER,
                    name,
                    col,
                    pos,
                    dtype.data_type if dtype else "NUMBER",
                    dtype.length if dtype else 22,
                    dtype.precision if dtype else None,
                    dtype.scale if dtype else None,
                    "Y",
                    *(
                        char_facts(dtype.data_type, dtype.ddl)
                        if dtype
                        else (None, None)
                    ),
                )
            iname = f"I_SNAP$_{name}"[:120]
            self.add(
                "indexes.csv",
                OWNER,
                iname,
                name,
                "FUNCTION-BASED NORMAL",
                "UNIQUE",
                "VALID",
                "N",
                "1",
            )
            self.obj(iname, "INDEX")
            self.add("index_columns.csv", OWNER, iname, "SYS_NC00004$", 1)
            self.add(
                "index_expressions.csv",
                OWNER,
                iname,
                1,
                f"SYS_OP_MAP_NONNULL({q(txt.name)})",
                0,
            )
            self.add(
                "dependencies.csv",
                OWNER,
                name,
                "MATERIALIZED VIEW",
                OWNER,
                base.name,
                "TABLE",
            )

    def make_links_and_synonyms(self) -> None:
        rng = self.rng
        links = []
        for i in range(rng.randint(1, 2)):
            name = rng.choice([f"LINK_{i}", f"LINK_{i}.WORLD", f"REMOTE{i}"])
            links.append(name)
            self.obj(name, "DATABASE LINK")
            self.add(
                "db_links.csv",
                OWNER,
                name,
                rng.choice(["REMOTE_USER", "APP", None]),
                rng.choice([f"//host{i}:1521/SVC", "svc'quoted", "TNSALIAS", None]),
            )
        targets = [(t.name, "TABLE") for t in self.tables] + [
            (v, "VIEW") for v, _ in self.views
        ]
        for i in range(rng.randint(3, 6)):
            roll = rng.random()
            owner = "PUBLIC" if roll < 0.15 else OWNER
            if roll < 0.05 and self.tables:
                name = rng.choice(self.tables).name
            else:
                name = self.unique(self.styled_name("SYN", i, allow_reserved=False))
            if owner == OWNER:
                self.obj(name, "SYNONYM")
            target, _ = rng.choice(targets)
            link = None
            if rng.random() < 0.15:
                target, link = "REMOTE_TABLE", rng.choice(links)
            elif rng.random() < 0.1:
                target = "DOES_NOT_EXIST"
            self.add("synonyms.csv", owner, name, OWNER, target, link)

    # -- stored code -----------------------------------------------------

    def unit(
        self, name: str, otype: str, text: str, deps: list[tuple[str, str]]
    ) -> None:
        self.obj(name, otype)
        for line_no, line in enumerate(text.split("\n"), start=1):
            self.add("source.csv", OWNER, name, otype, line_no, line + "\n")
        for dep_name, dep_type in deps:
            self.add("dependencies.csv", OWNER, name, otype, OWNER, dep_name, dep_type)

    def ref(self, name: str) -> str:
        if name.isidentifier() and name.isupper() and name not in RESERVED:
            return name
        return q(name)

    def make_code(self) -> None:
        rng = self.rng
        tables = [t for t in self.tables if t.pk and t.numeric() and t.textual()]
        if not tables:
            return
        funcs: list[str] = []
        for i in range(rng.randint(4, 8)):
            t = rng.choice(tables)
            pk = self.ref(t.pk_cols[0])
            tbl = self.ref(t.name)
            num = t.numeric()
            txt = t.textual()
            assert num is not None and txt is not None
            ncol, tcol = self.ref(num.name), self.ref(txt.name)
            fname = f"F_{rng.choice(TABLE_WORDS)}_{i}"
            if rng.random() < 0.08:
                fname = f"myFunc{i}"
            deps = [(t.name, "TABLE")]
            shape = rng.random()
            if shape < 0.18:
                body = (
                    f"FUNCTION {self.ref(fname)}(p_id IN NUMBER) RETURN NUMBER IS\n"
                    "  l_count NUMBER := 0;\nBEGIN\n"
                    f"  SELECT COUNT(*) INTO l_count FROM {tbl} WHERE {pk} = p_id;\n"
                    "  RETURN NVL(l_count, 0);\n"
                    f"END {self.ref(fname)};"
                )
            elif shape < 0.30:
                body = (
                    f"FUNCTION {fname}(p_v IN VARCHAR2) RETURN VARCHAR2 IS\nBEGIN\n"
                    "  IF p_v IS NULL THEN\n    RETURN 'none';\n"
                    "  ELSIF LENGTH(p_v) > 10 THEN\n    RETURN SUBSTR(p_v, 1, 10);\n"
                    "  ELSE\n    RETURN UPPER(p_v);\n  END IF;\nEND;"
                )
                deps = []
            elif shape < 0.42:
                body = (
                    f"FUNCTION {fname} RETURN NUMBER IS\n  l_total NUMBER := 0;\n"
                    f"BEGIN\n  FOR r IN (SELECT {ncol} FROM {tbl}) LOOP\n"
                    f"    l_total := l_total + NVL(r.{ncol}, 0);\n  END LOOP;\n"
                    "  RETURN l_total;\nEND;"
                )
            elif shape < 0.52:
                body = (
                    f"FUNCTION {fname}(p_id IN NUMBER) RETURN VARCHAR2 IS\n"
                    "  l_v VARCHAR2(4000);\nBEGIN\n"
                    f"  SELECT {tcol} INTO l_v FROM {tbl} WHERE {pk} = p_id;\n"
                    "  RETURN l_v;\nEXCEPTION\n  WHEN NO_DATA_FOUND THEN\n"
                    "    RETURN NULL;\nEND;"
                )
            elif shape < 0.60:
                body = (
                    f"FUNCTION {fname}(p_id IN NUMBER) RETURN NUMBER IS\n"
                    "  PRAGMA AUTONOMOUS_TRANSACTION;\nBEGIN\n"
                    f"  UPDATE {tbl} SET {ncol} = {ncol} + 1 WHERE {pk} = p_id;\n"
                    "  COMMIT;\n  RETURN SQL%ROWCOUNT;\nEND;"
                )
            elif shape < 0.66:
                body = (
                    f"FUNCTION {fname}(p_t IN VARCHAR2) RETURN NUMBER IS\nBEGIN\n"
                    "  EXECUTE IMMEDIATE 'TRUNCATE TABLE ' || p_t;\n  RETURN 1;\nEND;"
                )
                deps = []
            elif shape < 0.72:
                body = (
                    f"FUNCTION {fname} RETURN NUMBER IS\n"
                    "  TYPE t_ids IS TABLE OF NUMBER;\n  l_ids t_ids;\nBEGIN\n"
                    f"  SELECT {pk} BULK COLLECT INTO l_ids FROM {tbl};\n"
                    "  RETURN l_ids.COUNT;\nEND;"
                )
            elif shape < 0.78:
                body = (
                    f"FUNCTION {fname} RETURN VARCHAR2 IS\nBEGIN\n"
                    "  RETURN SYS_CONTEXT('USERENV', 'SESSION_USER');\nEND;"
                )
                deps = []
            elif shape < 0.84 and funcs:
                callee = rng.choice(funcs)
                body = (
                    f"FUNCTION {fname}(p_id IN NUMBER) RETURN NUMBER IS\nBEGIN\n"
                    f"  RETURN {self.ref(callee)}(p_id) * 2;\nEND;"
                )
                deps = [(callee, "FUNCTION")]
            elif shape < 0.90:
                body = (
                    f"FUNCTION {fname}(p_id IN NUMBER) RETURN NUMBER IS\nBEGIN\n"
                    "  REMOTE_PKG.LOG_IT@SALES_LINK(p_id);\n  RETURN 0;\nEND;"
                )
                deps = []
            elif shape < 0.95:
                body = f"FUNCTION {fname} RETURN NUMBER IS\nBEGIN\n  RETURN 1 +;\nEND;"
                deps = []
            else:
                body = (
                    f"FUNCTION {fname}(p_id IN NUMBER) RETURN {tbl}%ROWTYPE IS\n"
                    f"  l_row {tbl}%ROWTYPE;\nBEGIN\n"
                    f"  SELECT * INTO l_row FROM {tbl}"
                    f" WHERE {pk} = p_id AND ROWNUM = 1;\n"
                    "  DBMS_OUTPUT.PUT_LINE('found');\n  RETURN l_row;\nEND;"
                )
            body = body.replace(f"FUNCTION {fname}", f"FUNCTION {self.ref(fname)}", 1)
            funcs.append(fname)
            self.routines.append((fname, "FUNCTION"))
            self.unit(fname, "FUNCTION", body, deps)

        for i in range(rng.randint(2, 4)):
            t = rng.choice(tables)
            pk = self.ref(t.pk_cols[0])
            tbl = self.ref(t.name)
            txt = t.textual()
            assert txt is not None
            tcol = self.ref(txt.name)
            pname = f"P_{rng.choice(TABLE_WORDS)}_{i}"
            deps = [(t.name, "TABLE")]
            shape = rng.random()
            if shape < 0.3 and self.sequences:
                seq = rng.choice(self.sequences)
                body = (
                    f"PROCEDURE {pname}(p_name IN VARCHAR2) IS\nBEGIN\n"
                    f"  INSERT INTO {tbl} ({pk}, {tcol})"
                    f" VALUES ({self.ref(seq)}.NEXTVAL, p_name);\nEND;"
                )
                deps.append((seq, "SEQUENCE"))
            elif shape < 0.55:
                body = (
                    f"PROCEDURE {pname}(p_id IN NUMBER, p_name IN VARCHAR2) IS\n"
                    f"BEGIN\n  UPDATE {tbl} SET {tcol} = p_name WHERE {pk} = p_id;\n"
                    "  IF SQL%ROWCOUNT = 0 THEN\n"
                    "    RAISE_APPLICATION_ERROR(-20001, 'no such row');\n"
                    "  END IF;\nEND;"
                )
            elif shape < 0.75:
                body = (
                    f"PROCEDURE {pname}(p_id IN NUMBER, p_out OUT VARCHAR2) IS\n"
                    f"BEGIN\n  SELECT {tcol} INTO p_out FROM {tbl} WHERE {pk} = p_id;\n"
                    "  IF p_out = '' THEN\n    p_out := 'empty';\n  END IF;\nEND;"
                )
            elif shape < 0.82 and funcs:
                callee = rng.choice(funcs)
                body = (
                    f"PROCEDURE {pname}(p_id IN NUMBER) IS\n  l NUMBER;\nBEGIN\n"
                    f"  l := {self.ref(callee)}(p_id);\n  COMMIT;\nEND;"
                )
                deps = [(callee, "FUNCTION")]
            elif shape < 0.88:
                body = (
                    f"PROCEDURE {pname}(p_id IN NUMBER, p_name IN VARCHAR2) IS\n"
                    f"BEGIN\n  MERGE INTO {tbl} t\n"
                    "  USING (SELECT p_id AS id, p_name AS name FROM dual) s\n"
                    f"  ON (t.{pk} = s.id)\n"
                    f"  WHEN MATCHED THEN UPDATE SET t.{tcol} = s.name"
                    " WHERE s.name IS NOT NULL\n"
                    f"  WHEN NOT MATCHED THEN INSERT ({pk}, {tcol})"
                    " VALUES (s.id, s.name);\n"
                    "END;"
                )
            elif shape < 0.94:
                body = (
                    f"PROCEDURE {pname}(p_min IN NUMBER, p_out OUT VARCHAR2)"
                    " IS\nBEGIN\n"
                    f"  SELECT {tcol} INTO p_out FROM {tbl}"
                    f" WHERE {pk} > p_min AND ROWNUM = 1;\n"
                    "END;"
                )
            else:
                body = (
                    f"PROCEDURE {pname} IS\n  l_f UTL_FILE.FILE_TYPE;\nBEGIN\n"
                    "  l_f := UTL_FILE.FOPEN('DIR', 'x.txt', 'w');\n"
                    "  UTL_FILE.PUT_LINE(l_f, 'hello');\n  UTL_FILE.FCLOSE(l_f);\nEND;"
                )
                deps = []
            self.routines.append((pname, "PROCEDURE"))
            self.unit(pname, "PROCEDURE", body, deps)

        for i in range(rng.randint(1, 2)):
            pkg = f"PKG_{rng.choice(TABLE_WORDS)}_{i}"
            self.packages.append(pkg)
            spec = (
                f"PACKAGE {pkg} AS\n  g_count NUMBER := 0;\n"
                "  PROCEDURE bump(p_by IN NUMBER);\n"
                "  FUNCTION current_count RETURN NUMBER;\nEND;"
            )
            self.unit(pkg, "PACKAGE", spec, [])
            t = rng.choice(tables)
            body = (
                f"PACKAGE BODY {pkg} AS\n  PROCEDURE bump(p_by IN NUMBER) IS\n"
                "  BEGIN\n    g_count := g_count + p_by;\n"
                f"    UPDATE {self.ref(t.name)} SET {self.ref(t.pk_cols[0])} ="
                f" {self.ref(t.pk_cols[0])} WHERE 1 = 0;\n  END;\n"
                "  FUNCTION current_count RETURN NUMBER IS\n  BEGIN\n"
                "    RETURN g_count;\n  END;\nBEGIN\n  g_count := 1;\nEND;"
            )
            if rng.random() < 0.15:
                body = f"PACKAGE BODY {pkg} wrapped\na000000\n369\nabcd\nabcd\n1\n2 :e:"
            self.unit(pkg, "PACKAGE BODY", body, [(t.name, "TABLE")])

        if rng.random() < 0.5:
            self.unit(
                "ADDR_T",
                "TYPE",
                "TYPE ADDR_T AS OBJECT (\n  street VARCHAR2(100),\n"
                "  city VARCHAR2(50),\n  MEMBER FUNCTION label RETURN VARCHAR2\n);",
                [],
            )
            if rng.random() < 0.5:
                self.unit(
                    "ADDR_T",
                    "TYPE BODY",
                    "TYPE BODY ADDR_T AS\n  MEMBER FUNCTION label RETURN VARCHAR2 IS\n"
                    "  BEGIN\n    RETURN street || ', ' || city;\n  END;\nEND;",
                    [],
                )

        if rng.random() < 0.4:
            job = f"JOB_{rng.choice(TABLE_WORDS)}"
            self.obj(job, "JOB")

        self.make_triggers(tables)

    def make_triggers(self, tables: list[Table]) -> None:
        rng = self.rng
        for i in range(rng.randint(2, 5)):
            t = rng.choice(tables)
            tbl = self.ref(t.name)
            pk = self.ref(t.pk_cols[0])
            dat = t.dated()
            num = t.numeric()
            assert num is not None
            ncol = self.ref(num.name)
            name = self.unique(f"TRG_{t.name}_{i}"[:120])
            status = "DISABLED" if rng.random() < 0.1 else "ENABLED"
            shape = rng.random()
            deps = [(t.name, "TABLE")]
            if shape < 0.25 and dat:
                ttype, event = "BEFORE EACH ROW", "INSERT"
                body = (
                    f"TRIGGER {name}\n  BEFORE INSERT ON {tbl}\n  FOR EACH ROW\n"
                    f"BEGIN\n  :NEW.{self.ref(dat.name)} := SYSDATE;\nEND;"
                )
            elif shape < 0.45 and self.sequences:
                seq = self.ref(rng.choice(self.sequences))
                ttype, event = "BEFORE EACH ROW", "INSERT OR UPDATE"
                body = (
                    f"TRIGGER {name}\n  BEFORE INSERT OR UPDATE ON {tbl}\n"
                    "  FOR EACH ROW\nBEGIN\n"
                    f"  IF :NEW.{pk} IS NULL THEN\n"
                    f"    SELECT {seq}.NEXTVAL INTO :NEW.{pk} FROM dual;\n"
                    "  END IF;\nEND;"
                )
            elif shape < 0.60:
                other = rng.choice(tables)
                ttype, event = "AFTER STATEMENT", "INSERT OR UPDATE OR DELETE"
                body = (
                    f"TRIGGER {name}\n  AFTER INSERT OR UPDATE OR DELETE ON {tbl}\n"
                    f"BEGIN\n  UPDATE {self.ref(other.name)} SET"
                    f" {self.ref(other.pk_cols[0])} = {self.ref(other.pk_cols[0])}"
                    " WHERE 1 = 0;\nEND;"
                )
                deps.append((other.name, "TABLE"))
            elif shape < 0.72:
                ttype, event = "AFTER EACH ROW", "UPDATE"
                body = (
                    f"TRIGGER {name}\n  AFTER UPDATE ON {tbl}\n  FOR EACH ROW\n"
                    f"  WHEN (NEW.{ncol} > 100)\nBEGIN\n"
                    f"  IF :OLD.{ncol} <> :NEW.{ncol} THEN\n    NULL;\n  END IF;\nEND;"
                )
            elif shape < 0.82:
                ttype, event = "COMPOUND", "INSERT"
                body = (
                    f"TRIGGER {name}\n  FOR INSERT ON {tbl}\n  COMPOUND TRIGGER\n"
                    "  BEFORE STATEMENT IS\n  BEGIN\n    NULL;\n"
                    "  END BEFORE STATEMENT;\n"
                    "  AFTER EACH ROW IS\n  BEGIN\n    NULL;\n  END AFTER EACH ROW;\n"
                    "END;"
                )
            elif shape < 0.90:
                ttype, event = "AFTER EACH ROW", "DELETE"
                body = (
                    f"TRIGGER {name}\n  AFTER DELETE ON {tbl}\n  FOR EACH ROW\n"
                    "DECLARE\n  PRAGMA AUTONOMOUS_TRANSACTION;\nBEGIN\n"
                    f"  INSERT INTO {tbl} ({pk}) VALUES (:OLD.{pk});\n  COMMIT;\nEND;"
                )
            elif shape < 0.95 and self.views:
                vname, vcols = rng.choice(self.views)
                ttype, event = "INSTEAD OF", "INSERT"
                body = (
                    f"TRIGGER {name}\n  INSTEAD OF INSERT ON {self.ref(vname)}\n"
                    f"  FOR EACH ROW\nBEGIN\n  INSERT INTO {tbl} ({pk})"
                    f" VALUES (:NEW.{self.ref(vcols[0])});\nEND;"
                )
                deps = [(vname, "VIEW"), (t.name, "TABLE")]
                self.add("triggers.csv", OWNER, name, ttype, event, vname, status)
                self.unit(name, "TRIGGER", body, deps)
                continue
            else:
                ttype, event = "BEFORE EACH ROW", "INSERT"
                body = (
                    f"TRIGGER {name}\n  BEFORE INSERT ON GONE_TABLE\n  FOR EACH ROW\n"
                    "BEGIN\n  NULL;\nEND;"
                )
                deps = []
                self.add(
                    "triggers.csv", OWNER, name, ttype, event, "GONE_TABLE", status
                )
                self.unit(name, "TRIGGER", body, deps)
                continue
            self.add("triggers.csv", OWNER, name, ttype, event, t.name, status)
            self.unit(name, "TRIGGER", body, deps)

    # -- environment -----------------------------------------------------

    def add_grants(self, name: str, kind: str) -> None:
        rng = self.rng
        if rng.random() > 0.5:
            return
        privileges = {
            "TABLE": [
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "REFERENCES",
                "ALTER",
                "INDEX",
                "FLASHBACK",
                "DEBUG",
                "READ",
                "ON COMMIT REFRESH",
                "QUERY REWRITE",
            ],
            "VIEW": ["SELECT", "READ", "DEBUG"],
            "SEQUENCE": ["SELECT", "ALTER"],
        }[kind]
        grantees = ["APP_RO", "APP_RW", "PUBLIC", "app_reader", "REPORTING ROLE"]
        for privilege in rng.sample(
            privileges, min(len(privileges), rng.randint(1, 3))
        ):
            self.add(
                "grants.csv",
                rng.choice(grantees),
                OWNER,
                name,
                privilege,
                "YES" if rng.random() < 0.15 else "NO",
            )

    def make_environment(self) -> None:
        rng = self.rng
        product, version = rng.choice(VERSIONS)
        self.add("meta.csv", "schema", OWNER)
        self.add("meta.csv", "extracted_at", STAMP)
        self.add("meta.csv", "product", product)
        self.add("meta.csv", "version", version)
        self.add("nls.csv", "NLS_CHARACTERSET", rng.choice(CHARSETS))
        self.add("nls.csv", "NLS_LANGUAGE", "AMERICAN")
        self.add("nls.csv", "NLS_NCHAR_CHARACTERSET", "AL16UTF16")
        self.add("nls.csv", "NLS_TERRITORY", "AMERICA")
        self.add("license.csv", "banner", product.strip() + " Release " + version)
        self.add("license.csv", "cpu_count", str(rng.choice([2, 8, 64])))
        for feature, detail in FEATURES:
            self.add("features.csv", feature, detail, rng.choice([0, 0, 1, 3]))
        for feature in (
            "Partitioning",
            "Advanced Compression",
            "Real Application Security",
        ):
            self.add(
                "feature_usage.csv",
                feature,
                version,
                rng.choice([0, 5]),
                rng.choice(["TRUE", "FALSE"]),
                None,
            )
        if rng.random() < 0.3:
            self.add("plan_management.csv", "SQL_PLAN_BASELINE", "SQL_PLAN_1", "YES")
        self.add("grants.csv", "PUBLIC", OWNER, OWNER, "INHERIT PRIVILEGES", "NO")
        if rng.random() < 0.3:
            self.add("grants.csv", "APP_RO", OWNER, "NOT_IN_DUMP", "SELECT", "NO")

    # -- output ----------------------------------------------------------

    def build(self) -> None:
        self.make_sequences()
        self.make_tables()
        self.make_colliding_sequence()
        self.make_views()
        self.make_mviews()
        self.make_links_and_synonyms()
        self.make_code()
        self.make_environment()

    def write(self, out: Path) -> Manifest:
        out.mkdir(parents=True, exist_ok=True)
        for spool, header in HEADERS.items():
            with (out / spool).open("w", encoding="utf-8", newline="") as fh:
                fh.write("\n")
                writer = csv.writer(
                    fh, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n"
                )
                writer.writerow(header)
                writer.writerows(self.rows[spool])
        for name, chunks in self.ddl.items():
            (out / name).write_text(
                "\n" + "\n".join(chunks), encoding="utf-8", newline="\n"
            )
        manifest = Manifest(self.seed, list(self.objects))
        self.corrupt(out, manifest)
        (out / "fuzz_manifest.json").write_text(manifest.as_json(), encoding="ascii")
        return manifest

    def corrupt(self, out: Path, manifest: Manifest) -> None:
        """Hostile spools: what real client dumps actually contain.

        Each spool suffers at most one fate, so the runner's expectation
        for it stays well defined.
        """
        rng = self.rng
        touched: set[str] = set()

        def pick(candidates: list[str]) -> str | None:
            free = [c for c in candidates if c not in touched]
            if not free:
                return None
            chosen = rng.choice(free)
            touched.add(chosen)
            return chosen

        if rng.random() < 0.35:
            spool = pick(
                [
                    "grants.csv",
                    "plan_management.csv",
                    "check_conditions.csv",
                    "column_defaults.csv",
                    "index_expressions.csv",
                    "feature_usage.csv",
                ]
            )
            if spool:
                (out / spool).write_text(ERROR_SPOOL, encoding="utf-8", newline="\n")
                manifest.error_spools.append(spool)
        if rng.random() < 0.25:
            spool = pick(["table_comments.csv", "column_comments.csv"])
            if spool:
                path = out / spool
                text = path.read_text(encoding="utf-8")
                hangul = "\uc9c1\uc6d0 \uba85\ub2e8 \ubcf4\uace0\uc11c"
                while True:
                    data = (text + hangul).encode("cp949", errors="replace")
                    try:
                        data.decode("utf-8")
                    except UnicodeDecodeError:
                        break
                    hangul += "\ud55c\uae00"
                path.write_bytes(data)
                manifest.lossy_spools.append(spool)
        if rng.random() < 0.25:
            spool = pick(["columns.csv", "source.csv", "index_columns.csv"])
            if spool:
                path = out / spool
                data = path.read_bytes()
                path.write_bytes(data[: max(len(data) - 37, 0)])
                manifest.torn_spools.append(spool)
        if rng.random() < 0.2:
            spool = pick(
                [
                    "part_partitions.csv",
                    "index_expressions.csv",
                    "column_defaults.csv",
                    "constraint_columns.csv",
                    "dependencies.csv",
                ]
            )
            if spool:
                (out / spool).unlink()
                manifest.missing_spools.append(spool)


def generate(seed: int, out: Path) -> Manifest:
    estate = Estate(seed)
    estate.build()
    return estate.write(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    manifest = generate(args.seed, args.out)
    print(f"seed {args.seed}: {len(manifest.objects)} objects in {args.out}")
    for label, spools in (
        ("error spools", manifest.error_spools),
        ("foreign code page", manifest.lossy_spools),
        ("torn", manifest.torn_spools),
        ("missing", manifest.missing_spools),
    ):
        if spools:
            print(f"  {label}: {', '.join(spools)}")


if __name__ == "__main__":
    main()

"""Partitioning facts and child partition emission."""

import re
import sqlite3
from dataclasses import dataclass

from pgrecon.convert.identifiers import ident
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.residue import Residue


@dataclass(frozen=True)
class _PartMeta:
    clause: str
    ptype: str
    subtype: str
    interval: str | None
    subkeys: str


_BOUND_DATE = re.compile(
    r"TO_(?:DATE|TIMESTAMP)\(\s*'([^']*)'\s*,\s*'[^']*'(?:\s*,\s*'[^']*')?\s*\)",
    re.IGNORECASE,
)


def _bound_to_pg(value: str | None) -> str | None:
    """One partition bound as a PostgreSQL literal, or None to decline."""
    v = (value or "").strip()
    if not v:
        return None
    if v.upper() == "MAXVALUE":
        return "MAXVALUE"
    v = _BOUND_DATE.sub(lambda m: "'" + m.group(1).strip() + "'", v)
    if "TO_DATE" in v.upper() or "TO_TIMESTAMP" in v.upper():
        return None
    return v


def _part_keys(
    conn: sqlite3.Connection, owner: str, table: str, fact_table: str
) -> str:
    return ", ".join(
        ident(r["column_name"])
        for r in conn.execute(
            f"SELECT column_name FROM {fact_table}"
            " WHERE owner = ? AND table_name = ? ORDER BY position",
            (owner, table),
        )
    )


def _partition_meta(
    conn: sqlite3.Connection, owner: str, table: str
) -> tuple[_PartMeta | None, str | None]:
    """Partitioning facts for one table, or a residue reason."""
    part = conn.execute(
        "SELECT partitioning_type, subpartitioning_type, interval"
        " FROM part_tables WHERE owner = ? AND table_name = ?",
        (owner, table),
    ).fetchone()
    if part is None:
        return None, None
    ptype = (part["partitioning_type"] or "").upper()
    subtype = (part["subpartitioning_type"] or "NONE").upper()
    keys = _part_keys(conn, owner, table, "part_key_columns")
    if ptype not in ("RANGE", "LIST", "HASH") or not keys:
        return None, f"{ptype or 'unknown'} partitioning needs a hand-designed layout"
    subkeys = ""
    if subtype in ("RANGE", "LIST", "HASH"):
        subkeys = _part_keys(conn, owner, table, "part_subkey_columns")
        if not subkeys:
            subtype = "NONE"
    return (
        _PartMeta(
            clause=f" PARTITION BY {ptype} ({keys})",
            ptype=ptype,
            subtype=subtype,
            interval=part["interval"],
            subkeys=subkeys,
        ),
        None,
    )


def _child_spec(
    ptype: str,
    high_value: str | None,
    truncated: int | None,
    position: int,
    total: int,
    prev: str,
) -> tuple[str | None, str]:
    """One child's FOR VALUES spec and the next range floor."""
    if ptype == "HASH":
        return f"FOR VALUES WITH (MODULUS {total}, REMAINDER {position - 1})", prev
    if truncated:
        return None, prev
    if ptype == "LIST":
        hv = (high_value or "").strip()
        if hv.upper() == "DEFAULT":
            return "DEFAULT", prev
        bound = _bound_to_pg(hv)
        return (f"FOR VALUES IN ({bound})" if bound else None), prev
    bound = _bound_to_pg(high_value)
    if bound is None:
        return None, prev
    return f"FOR VALUES FROM ({prev}) TO ({bound})", bound


def _emit_partition_children(
    conn: sqlite3.Connection,
    owner: str,
    table: str,
    meta: _PartMeta,
    out: list[str],
    residue: list[Residue],
    names: NameRegistry,
) -> int:
    parts = conn.execute(
        "SELECT partition_name, position, high_value, truncated"
        " FROM part_partitions WHERE owner = ? AND table_name = ?"
        " ORDER BY position",
        (owner, table),
    ).fetchall()
    if not parts:
        residue.append(
            Residue(
                owner,
                table,
                "partitioning",
                "partition bounds are not in this dump (older extraction"
                " script); child partitions must be defined by hand",
            )
        )
        return 0

    statements: list[str] = []
    prev = "MINVALUE"
    for p in parts:
        child = f"{table}_{p['partition_name']}"
        if len(child) > 63:
            residue.append(
                Residue(
                    owner,
                    table,
                    "partitioning",
                    f"child name {child} exceeds PostgreSQL's 63-character"
                    " limit; children omitted, name them by hand",
                )
            )
            return 0
        holder = names.peek(child)
        if holder is not None:
            residue.append(
                Residue(
                    owner,
                    table,
                    "partitioning",
                    f"child name {child} collides with {holder[1]}"
                    f" {holder[0]} in PostgreSQL's relation namespace;"
                    " children omitted, name them by hand",
                )
            )
            return 0
        names.claim(child, "partition child", owner, residue)
        spec, prev = _child_spec(
            meta.ptype,
            p["high_value"],
            p["truncated"],
            p["position"] or 1,
            len(parts),
            prev,
        )
        if spec is None:
            residue.append(
                Residue(
                    owner,
                    table,
                    "partitioning",
                    f"bound of partition {p['partition_name']} could not be"
                    " converted faithfully; children omitted",
                )
            )
            return 0
        stmt = f"CREATE TABLE {ident(child)} PARTITION OF {ident(table)} {spec}"
        if meta.subtype != "NONE":
            stmt += f" PARTITION BY {meta.subtype} ({meta.subkeys})"
        statements.append(stmt + ";")
        if meta.subtype != "NONE":
            subs = conn.execute(
                "SELECT subpartition_name, position, high_value, truncated"
                " FROM part_subpartitions"
                " WHERE owner = ? AND table_name = ? AND partition_name = ?"
                " ORDER BY position",
                (owner, table, p["partition_name"]),
            ).fetchall()
            if not subs:
                residue.append(
                    Residue(
                        owner,
                        table,
                        "partitioning",
                        f"subpartitions of {p['partition_name']} are not in"
                        " the dump; children omitted",
                    )
                )
                return 0
            sub_prev = "MINVALUE"
            for s in subs:
                sub_child = f"{table}_{p['partition_name']}_{s['subpartition_name']}"
                if len(sub_child) > 63:
                    residue.append(
                        Residue(
                            owner,
                            table,
                            "partitioning",
                            f"child name {sub_child} exceeds PostgreSQL's"
                            " 63-character limit; children omitted",
                        )
                    )
                    return 0
                sub_holder = names.peek(sub_child)
                if sub_holder is not None:
                    residue.append(
                        Residue(
                            owner,
                            table,
                            "partitioning",
                            f"child name {sub_child} collides with"
                            f" {sub_holder[1]} {sub_holder[0]} in"
                            " PostgreSQL's relation namespace; children"
                            " omitted, name them by hand",
                        )
                    )
                    return 0
                names.claim(sub_child, "partition child", owner, residue)
                sub_spec, sub_prev = _child_spec(
                    meta.subtype,
                    s["high_value"],
                    s["truncated"],
                    s["position"] or 1,
                    len(subs),
                    sub_prev,
                )
                if sub_spec is None:
                    residue.append(
                        Residue(
                            owner,
                            table,
                            "partitioning",
                            f"bound of subpartition {s['subpartition_name']}"
                            " could not be converted; children omitted",
                        )
                    )
                    return 0
                statements.append(
                    f"CREATE TABLE {ident(sub_child)} PARTITION OF"
                    f" {ident(child)} {sub_spec};"
                )

    out.extend(statements)
    out.append("")
    if meta.interval:
        residue.append(
            Residue(
                owner,
                table,
                "note",
                "existing partitions are emitted; Oracle was creating new"
                " ones automatically by interval, which needs scheduled"
                " creation on PostgreSQL (for example pg_partman)",
            )
        )
    return len(statements)

"""Constraint emission: keys, checks, and foreign keys."""

import re
import sqlite3

from pgrecon.convert.identifiers import _fold_condition, _referenced_columns, ident
from pgrecon.convert.residue import Residue

_NOT_NULL_CONDITION = re.compile(
    r'^"?[A-Za-z0-9_$#]+"?\s+IS\s+NOT\s+NULL$', re.IGNORECASE
)


def _constraint_guard(
    conn: sqlite3.Connection,
    owner: str,
    table: str,
    raw_columns: list[str],
    emitted: dict[tuple[str, str], set[str]],
    unique: bool,
) -> str | None:
    """Why a constraint cannot be emitted faithfully, or None."""
    if (owner, table) not in emitted:
        return (
            "its table is outside the converted set (nested or IOT"
            " storage, remote, or every column was unconvertible)"
        )
    if any(c.upper().startswith("SYS_NC") for c in raw_columns):
        return (
            "it is built on a hidden system column; recreate it from"
            " the source definition"
        )
    missing = [c for c in raw_columns if c.upper() not in emitted[(owner, table)]]
    if missing:
        return f"column {missing[0]} was not converted"
    if unique:
        part_keys = [
            (r["column_name"] or "").upper()
            for r in conn.execute(
                "SELECT column_name FROM part_key_columns"
                " WHERE owner = ? AND table_name = ?",
                (owner, table),
            )
        ]
        cols = {c.upper() for c in raw_columns}
        uncovered = [k for k in part_keys if k not in cols]
        if uncovered:
            return (
                "PostgreSQL requires unique constraints on a"
                " partitioned table to include every partition key;"
                f" {uncovered[0]} is missing - widen the key or"
                " enforce uniqueness another way"
            )
    return None


def _raw_constraint_columns(
    conn: sqlite3.Connection, owner: str, name: str
) -> list[str]:
    return [
        r["column_name"]
        for r in conn.execute(
            "SELECT column_name FROM constraint_columns"
            " WHERE owner = ? AND constraint_name = ? ORDER BY position",
            (owner, name),
        )
        if r["column_name"]
    ]


def _emit_keys(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    matviews: set[str] | None = None,
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT owner, constraint_name, table_name, type FROM constraints"
        " WHERE type IN ('P', 'U') ORDER BY type, owner, table_name, constraint_name"
    ).fetchall()
    for r in rows:
        if matviews and (r["table_name"] or "").upper() in matviews:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "constraint",
                    "PostgreSQL materialized views cannot carry"
                    " constraints; enforce it on the base tables",
                )
            )
            continue
        raw = _raw_constraint_columns(conn, r["owner"], r["constraint_name"])
        if not raw:
            residue.append(
                Residue(
                    r["owner"], r["constraint_name"], "constraint", "no column facts"
                )
            )
            continue
        reason = _constraint_guard(
            conn, r["owner"], r["table_name"], raw, emitted, unique=True
        )
        if reason is not None:
            residue.append(
                Residue(r["owner"], r["constraint_name"], "constraint", reason)
            )
            continue
        kind = "PRIMARY KEY" if r["type"] == "P" else "UNIQUE"
        cols = ", ".join(ident(c) for c in raw)
        name = ident(r["constraint_name"])
        # Oracle keeps constraints in their own namespace; PostgreSQL
        # backs PRIMARY KEY and UNIQUE with an index that shares the
        # relation namespace, so a constraint named after a table
        # collides with it.
        if (r["constraint_name"] or "").upper() in {t for (_, t) in emitted}:
            suffix = "_pk" if r["type"] == "P" else "_uk"
            name = ident(r["constraint_name"] + suffix.upper())
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "note",
                    f"shares its name with a table; created as"
                    f" {name} because PostgreSQL backs the constraint"
                    " with an index in the relation namespace",
                )
            )
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {name} {kind} ({cols});"
        )
        count += 1
    if rows:
        out.append("")
    return count


def _emit_checks(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    matviews: set[str] | None = None,
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT c.owner, c.constraint_name, c.table_name, k.condition, k.truncated"
        " FROM constraints c JOIN check_conditions k"
        " ON k.owner = c.owner AND k.constraint_name = c.constraint_name"
        " WHERE c.type = 'C' ORDER BY c.owner, c.table_name, c.constraint_name"
    ).fetchall()
    wrote = False
    for r in rows:
        condition = (r["condition"] or "").strip()
        if not condition or _NOT_NULL_CONDITION.match(condition):
            # Column-level NOT NULL already lives on the column.
            continue
        if matviews and (r["table_name"] or "").upper() in matviews:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "PostgreSQL materialized views cannot carry"
                    " constraints; enforce it on the base tables",
                )
            )
            continue
        if r["truncated"]:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "condition was truncated during extraction; recover it"
                    " from the source before porting",
                )
            )
            continue
        if (r["owner"], r["table_name"]) not in emitted:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "its table is outside the converted set",
                )
            )
            continue
        folded = _fold_condition(condition)
        if folded is None:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "condition could not be translated; port it by hand",
                )
            )
            continue
        gone = dropped.get((r["owner"], r["table_name"]), set())
        referenced = _referenced_columns(folded)
        if referenced is None:
            # The reparse should never fail on our own output; the
            # token scan stays as the safe fallback if it does.
            referenced = {
                t.upper() for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_$#]*", folded)
            }
        lost = sorted(referenced & gone)
        if lost:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    f"condition references {lost[0]}, a column that was not converted",
                )
            )
            continue
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} CHECK ({folded});"
        )
        wrote = True
        count += 1
    if wrote:
        out.append("")
    return count


def _emit_foreign_keys(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    matviews: set[str] | None = None,
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT owner, constraint_name, table_name, ref_owner, ref_constraint,"
        " delete_rule FROM constraints WHERE type = 'R'"
        " ORDER BY owner, table_name, constraint_name"
    ).fetchall()
    for r in rows:
        if matviews and (r["table_name"] or "").upper() in matviews:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "foreign key",
                    "PostgreSQL materialized views cannot carry"
                    " constraints; enforce it on the base tables",
                )
            )
            continue
        raw = _raw_constraint_columns(conn, r["owner"], r["constraint_name"])
        ref = conn.execute(
            "SELECT table_name FROM constraints"
            " WHERE owner = ? AND constraint_name = ?",
            (r["ref_owner"], r["ref_constraint"]),
        ).fetchone()
        ref_raw = (
            _raw_constraint_columns(conn, r["ref_owner"], r["ref_constraint"])
            if ref
            else []
        )
        if not raw or ref is None or not ref_raw:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "foreign key",
                    "referenced key is outside the extracted schema",
                )
            )
            continue
        if matviews and (ref["table_name"] or "").upper() in matviews:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "foreign key",
                    "references a materialized view, which cannot carry"
                    " the referenced unique constraint in PostgreSQL",
                )
            )
            continue
        reason = _constraint_guard(
            conn, r["owner"], r["table_name"], raw, emitted, unique=False
        ) or _constraint_guard(
            conn, r["ref_owner"], ref["table_name"], ref_raw, emitted, unique=False
        )
        if reason is not None:
            residue.append(
                Residue(r["owner"], r["constraint_name"], "foreign key", reason)
            )
            continue
        action = ""
        if (r["delete_rule"] or "").upper() == "CASCADE":
            action = " ON DELETE CASCADE"
        elif (r["delete_rule"] or "").upper() == "SET NULL":
            action = " ON DELETE SET NULL"
        cols = ", ".join(ident(c) for c in raw)
        ref_cols = ", ".join(ident(c) for c in ref_raw)
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} FOREIGN KEY ({cols})"
            f" REFERENCES {ident(ref['table_name'])} ({ref_cols}){action};"
        )
        count += 1
    if rows:
        out.append("")
    return count

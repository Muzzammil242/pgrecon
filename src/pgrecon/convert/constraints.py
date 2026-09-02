"""Constraint emission: keys, checks, and foreign keys."""

import re
import sqlite3

from pgrecon.convert.identifiers import (
    _date_function_guard,
    _default_guard,
    _fold_condition,
    _referenced_columns,
    _type_mismatch_guard,
    ident,
    over_limit,
)
from pgrecon.convert.namespace import NameRegistry
from pgrecon.convert.residue import Residue
from pgrecon.convert.tables import _column_families, _date_columns
from pgrecon.convert.typemap import fk_compatible, indexable, map_type

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
    for col, pg_type in zip(
        raw_columns, _mapped_types(conn, owner, table, raw_columns), strict=True
    ):
        if pg_type is not None and not indexable(pg_type):
            return (
                f"column {col} lands as {pg_type}, which has no btree operator"
                " class and cannot be a key on PostgreSQL"
            )
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


def _mapped_types(
    conn: sqlite3.Connection, owner: str, table: str, columns: list[str]
) -> list[str | None]:
    types: list[str | None] = []
    for name in columns:
        row = conn.execute(
            "SELECT data_type, data_length, data_precision, data_scale FROM columns"
            " WHERE owner = ? AND table_name = ? AND UPPER(column_name) = ?",
            (owner, table, name.upper()),
        ).fetchone()
        if row is None:
            types.append(None)
            continue
        types.append(
            map_type(
                row["data_type"],
                row["data_length"],
                row["data_precision"],
                row["data_scale"],
            ).pg_type
        )
    return types


def _fk_type_guard(
    conn: sqlite3.Connection,
    owner: str,
    table: str,
    columns: list[str],
    ref_owner: str,
    ref_table: str,
    ref_columns: list[str],
) -> str | None:
    """Why a foreign key cannot be implemented on PostgreSQL, or None.

    Oracle checks that referencing and referenced columns are
    compatible in its own type system; after mapping, a NUMBER child
    against a NUMBER(10) parent is numeric against bigint, which
    PostgreSQL rejects, and a column count that differs from the
    referenced key never applied anywhere.
    """
    if len(columns) != len(ref_columns):
        return (
            f"{len(columns)} columns reference a key of {len(ref_columns)};"
            " the constraint facts disagree - recreate it from the source"
        )
    child_types = _mapped_types(conn, owner, table, columns)
    parent_types = _mapped_types(conn, ref_owner, ref_table, ref_columns)
    for col, child, ref_col, parent in zip(
        columns, child_types, ref_columns, parent_types, strict=True
    ):
        if child is None or parent is None:
            continue
        if not fk_compatible(child, parent):
            return (
                f"column {col} maps to {child} while the referenced {ref_col}"
                f" maps to {parent}; PostgreSQL cannot compare them through"
                " the key - align the types by hand"
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
    names: NameRegistry,
    matviews: set[str] | None = None,
) -> tuple[int, set[tuple[str, str]]]:
    """Primary and unique keys; returns the count and the (owner, name)
    pairs that were actually emitted, which foreign keys must point at."""
    count = 0
    created: set[tuple[str, str]] = set()
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
        raw_name = r["constraint_name"] or ""
        # Oracle keeps constraints in their own namespace; PostgreSQL
        # backs PRIMARY KEY and UNIQUE with an index that shares the
        # relation namespace, so a colliding constraint takes a
        # suffixed name. A collision caused by 63-byte truncation
        # cannot be suffixed away and refuses.
        holder = names.peek(raw_name)
        if holder is None:
            names.claim(raw_name, "constraint", r["owner"], residue)
            claimed_name = raw_name
        elif over_limit(raw_name):
            names.claim(raw_name, "constraint", r["owner"], residue)
            continue
        else:
            suffix = "_PK" if r["type"] == "P" else "_UK"
            claimed_name = raw_name + suffix
            if not names.claim(claimed_name, "constraint", r["owner"], residue):
                continue
            residue.append(
                Residue(
                    r["owner"],
                    raw_name,
                    "note",
                    f"shares its name with {holder[1]} {holder[0]};"
                    f" created as {ident(claimed_name)} because PostgreSQL"
                    " backs the constraint with an index in the relation"
                    " namespace",
                )
            )
        name = ident(claimed_name)
        names.claim(
            claimed_name,
            "constraint",
            r["owner"],
            residue,
            scope=f"constraint:{(r['table_name'] or '').upper()}",
            note=False,
        )
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {name} {kind} ({cols});"
        )
        created.add((r["owner"], r["constraint_name"]))
        count += 1
    if rows:
        out.append("")
    return count, created


def _emit_checks(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    dropped: dict[tuple[str, str], set[str]],
    names: NameRegistry,
    matviews: set[str] | None = None,
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT c.owner, c.constraint_name, c.table_name, k.condition, k.truncated"
        " FROM constraints c LEFT JOIN check_conditions k"
        " ON k.owner = c.owner AND k.constraint_name = c.constraint_name"
        " WHERE c.type = 'C' ORDER BY c.owner, c.table_name, c.constraint_name"
    ).fetchall()
    wrote = False
    for r in rows:
        condition = (r["condition"] or "").strip()
        if not condition:
            # Conditions travel through their own spool, read from a
            # LONG; a constraint whose text never arrived is declined
            # by name, not forgotten.
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    "its condition was not captured in the inventory;"
                    " recover it from the source before porting",
                )
            )
            continue
        if _NOT_NULL_CONDITION.match(condition):
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
        date_guard = (
            None
            if folded is None
            else _default_guard(folded)
            or _date_function_guard(
                folded, _date_columns(conn, r["owner"], r["table_name"])
            )
            or _type_mismatch_guard(
                folded, _column_families(conn, r["owner"], r["table_name"])
            )
        )
        if folded is None or date_guard is not None:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    date_guard or "condition could not be translated; port it by hand",
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
        present = {c.upper() for c in emitted[(r["owner"], r["table_name"])]}
        unknown = sorted(referenced - present)
        if unknown:
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "check",
                    f"condition references {unknown[0]}, which is not a column"
                    " of the converted table",
                )
            )
            continue
        if not names.claim(
            r["constraint_name"] or "",
            "check",
            r["owner"],
            residue,
            scope=f"constraint:{(r['table_name'] or '').upper()}",
        ):
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
    names: NameRegistry,
    matviews: set[str] | None = None,
    emitted_keys: set[tuple[str, str]] | None = None,
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
        if (
            emitted_keys is not None
            and (r["ref_owner"], r["ref_constraint"]) not in emitted_keys
        ):
            residue.append(
                Residue(
                    r["owner"],
                    r["constraint_name"],
                    "foreign key",
                    f"the referenced key {r['ref_constraint']} was not"
                    " converted, so there is nothing to point at",
                )
            )
            continue
        reason = (
            _constraint_guard(
                conn, r["owner"], r["table_name"], raw, emitted, unique=False
            )
            or _constraint_guard(
                conn, r["ref_owner"], ref["table_name"], ref_raw, emitted, unique=False
            )
            or _fk_type_guard(
                conn,
                r["owner"],
                r["table_name"],
                raw,
                r["ref_owner"],
                ref["table_name"],
                ref_raw,
            )
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
        if not names.claim(
            r["constraint_name"] or "",
            "foreign key",
            r["owner"],
            residue,
            scope=f"constraint:{(r['table_name'] or '').upper()}",
        ):
            continue
        out.append(
            f"ALTER TABLE {ident(r['table_name'])} ADD CONSTRAINT"
            f" {ident(r['constraint_name'])} FOREIGN KEY ({cols})"
            f" REFERENCES {ident(ref['table_name'])} ({ref_cols}){action};"
        )
        count += 1
    if rows:
        out.append("")
    return count

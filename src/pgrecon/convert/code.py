"""Code-unit emission: the mechanically convertible functions and
procedures, and named refusals for everything semantic.

The boundary is the rule engine's own facts: a unit converts only
when its deep-parse features, its recorded calls, and its dictionary
dependencies all prove out. Every refusal names the construct and the
line, so the residue report reads as a work list, not an apology.
"""

import sqlite3

from pgrecon.convert.namespace import ROUTINES, NameRegistry
from pgrecon.convert.plsql_rewrite import rewrite_unit
from pgrecon.convert.residue import Residue

_REFUSE_FEATURES = {
    "autonomous_transaction": (
        "runs an autonomous transaction; redesign with dblink or a queue"
    ),
    "ref_cursor": "REF CURSOR interfaces change shape; redesign the interface",
    "forall": "FORALL bulk DML needs a set-based rewrite",
    "bulk_collect": "BULK COLLECT needs an array or set-based rewrite",
    "connect_by": "CONNECT BY becomes a WITH RECURSIVE query",
    "outer_join_plus": "(+) outer joins in embedded SQL need the ANSI form",
    "goto": "GOTO has no counterpart; restructure the control flow",
    "merge": "MERGE clauses differ between the engines; port it by hand",
    "rownum": "ROWNUM needs LIMIT or row_number(); rewrite the query",
    "rowid": "ROWID access paths do not exist; use the primary key",
    "decode_call": ("DECODE matches NULLs; rewrite as CASE with IS NOT DISTINCT FROM"),
    "sql_cursor_attribute": (
        "SQL%ROWCOUNT and friends become GET DIAGNOSTICS; rewrite by hand"
    ),
    "empty_string_literal": (
        "'' is NULL on Oracle but an empty string on PostgreSQL; audit each use"
    ),
    "conditional_compilation": (
        "conditional compilation branches must be chosen before porting"
    ),
    "pipelined": (
        "pipelined table functions become set-returning functions;"
        " redesign the interface"
    ),
}

# Callees whose PostgreSQL behavior is the same, or that the rewriter
# itself refines (NVL, INSTR, SUBSTR, the TO_* family).
_SAFE_CALLS = {
    "ABS",
    "ASCII",
    "AVG",
    "CAST",
    "CEIL",
    "CHR",
    "COALESCE",
    "CONCAT",
    "COUNT",
    "DENSE_RANK",
    "EXP",
    "EXTRACT",
    "FLOOR",
    "GREATEST",
    "INITCAP",
    "INSTR",
    "LAG",
    "LEAD",
    "LEAST",
    "LENGTH",
    "LN",
    "LOWER",
    "LPAD",
    "LTRIM",
    "MAX",
    "MIN",
    "MOD",
    "NULLIF",
    "NVL",
    "POWER",
    "RANK",
    "REPLACE",
    "ROW_NUMBER",
    "RPAD",
    "RTRIM",
    "SIGN",
    "SQLERRM",
    "SQRT",
    "STDDEV",
    "SUBSTR",
    "SUM",
    "TO_CHAR",
    "TO_DATE",
    "TO_NUMBER",
    "TO_TIMESTAMP",
    "TRANSLATE",
    "TRIM",
    "UPPER",
    "VARIANCE",
}

_CALL_REASONS = {
    "TRUNC": (
        "TRUNC over dates becomes date_trunc and over numbers maps"
        " directly; the converter cannot prove which - rewrite by hand"
    ),
    "ROUND": (
        "ROUND over dates has no counterpart and over numbers maps"
        " directly; the converter cannot prove which - rewrite by hand"
    ),
    "RAISE_APPLICATION_ERROR": (
        "RAISE_APPLICATION_ERROR carries an Oracle error code; choose"
        " a RAISE EXCEPTION ... USING ERRCODE mapping"
    ),
}

_DBMS_OUTPUT_SAFE = {"PUT_LINE", "ENABLE", "DISABLE"}


def _unit_text(conn: sqlite3.Connection, owner: str, name: str, otype: str) -> str:
    lines = []
    for r in conn.execute(
        "SELECT text FROM source WHERE owner = ? AND name = ? AND type = ?"
        " ORDER BY line",
        (owner, name, otype),
    ):
        line = r["text"] or "\n"
        if not line.endswith("\n"):
            line += "\n"
        lines.append(line)
    return "".join(lines)


def _feature_gate(
    conn: sqlite3.Connection, owner: str, name: str, otype: str
) -> tuple[list[str], list[str]]:
    """Refusal reasons and notes from the unit's deep-parse features."""
    reasons: list[str] = []
    notes: list[str] = []
    for r in conn.execute(
        "SELECT feature, line, detail FROM plsql_features"
        " WHERE owner = ? AND name = ? AND type = ? ORDER BY line",
        (owner, name, otype),
    ):
        feature = r["feature"]
        if feature in _REFUSE_FEATURES:
            reasons.append(f"{_REFUSE_FEATURES[feature]} (line {r['line']})")
        elif feature == "collection_type":
            kind = r["detail"] or "collection"
            reasons.append(
                f"declares a {kind}; redesign with arrays or a temporary"
                f" table (line {r['line']})"
            )
        elif feature in ("commit", "rollback"):
            if otype == "FUNCTION":
                reasons.append(
                    "transaction control inside a function is impossible;"
                    f" move {feature.upper()} to the caller (line {r['line']})"
                )
            else:
                notes.append(
                    "transaction control requires a top-level CALL on"
                    " PostgreSQL; invocations inside an open transaction"
                    " will fail"
                )
    return reasons, notes


def _call_gate(
    conn: sqlite3.Connection,
    owner: str,
    name: str,
    otype: str,
    owners: set[str],
    callables: set[str],
    packages: set[str],
) -> tuple[list[str], set[str]]:
    """Refusal reasons from recorded call sites, plus local call edges."""
    reasons: list[str] = []
    edges: set[str] = set()
    seen: set[str] = set()
    for r in conn.execute(
        "SELECT callee, line FROM plsql_calls"
        " WHERE owner = ? AND name = ? AND type = ? ORDER BY line",
        (owner, name, otype),
    ):
        callee = (r["callee"] or "").upper()
        if not callee or callee in seen:
            continue
        seen.add(callee)
        parts = callee.split(".")
        if len(parts) > 1 and parts[0] in owners:
            parts = parts[1:]
        head = parts[0]
        if len(parts) == 1:
            if head in _SAFE_CALLS:
                continue
            if head in callables:
                edges.add(head)
                continue
            if head in packages:
                reasons.append(
                    f"calls into package {head}; flatten the package"
                    f" first (line {r['line']})"
                )
            elif head in _CALL_REASONS:
                reasons.append(f"{_CALL_REASONS[head]} (line {r['line']})")
            else:
                reasons.append(
                    f"calls {head}, which the converter cannot prove"
                    f" equivalent (line {r['line']})"
                )
        elif head == "DBMS_OUTPUT" and parts[1] in _DBMS_OUTPUT_SAFE:
            continue
        elif head in packages:
            reasons.append(
                f"calls into package {head}; flatten the package first"
                f" (line {r['line']})"
            )
        else:
            reasons.append(
                f"calls {callee}; map it to a PostgreSQL equivalent"
                f" by hand (line {r['line']})"
            )
    return reasons, edges


def _dependency_gate(
    conn: sqlite3.Connection,
    owner: str,
    name: str,
    otype: str,
    owners: set[str],
    tables: set[str],
    created_views: set[str],
    sequences: set[str],
    synonyms: set[str],
) -> tuple[list[str], set[str]]:
    """Refusal reasons from dictionary dependencies, plus call edges."""
    reasons: list[str] = []
    edges: set[str] = set()
    for r in conn.execute(
        "SELECT DISTINCT ref_owner, ref_name, ref_type FROM dependencies"
        " WHERE owner = ? AND name = ? AND type = ?",
        (owner, name, otype),
    ):
        ref_owner = (r["ref_owner"] or "").upper()
        ref_name = (r["ref_name"] or "").upper()
        ref_type = (r["ref_type"] or "").upper()
        if ref_owner not in owners:
            continue
        if ref_type == "TABLE" and ref_name not in tables:
            reasons.append(f"references table {ref_name}, which was not converted")
        elif ref_type == "VIEW" and ref_name not in created_views:
            reasons.append(f"references view {ref_name}, which was not converted")
        elif ref_type == "SYNONYM" and ref_name not in synonyms:
            reasons.append(f"references synonym {ref_name}, which was not converted")
        elif ref_type == "SEQUENCE" and ref_name not in sequences:
            reasons.append(f"references sequence {ref_name}, which was not converted")
        elif ref_type == "MATERIALIZED VIEW":
            reasons.append(
                f"references materialized view {ref_name}; materialized"
                " views are not converted"
            )
        elif ref_type in ("PACKAGE", "PACKAGE BODY"):
            reasons.append(f"calls into package {ref_name}; flatten the package first")
        elif ref_type in ("TYPE", "TYPE BODY"):
            reasons.append(f"uses object type {ref_name}, which has no counterpart")
        elif ref_type in ("FUNCTION", "PROCEDURE"):
            edges.add(ref_name)
    return reasons, edges


def _join(reasons: list[str]) -> str:
    unique = list(dict.fromkeys(reasons))
    text = "; ".join(unique[:3])
    if len(unique) > 3:
        text += f"; and {len(unique) - 3} more"
    return text


def _emit_code(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    created_views: set[str],
    sequences: set[str],
    synonyms: set[str],
    names: NameRegistry,
) -> int:
    """Functions and procedures through the mechanical rewriter.

    Packages, triggers, and object types are never attempted: each
    lands in the residue with what porting it actually takes.
    """
    owners = {
        (r["owner"] or "").upper()
        for r in conn.execute("SELECT DISTINCT owner FROM objects")
    }
    callables = {
        (r["name"] or "").upper()
        for r in conn.execute(
            "SELECT name FROM objects WHERE type IN ('FUNCTION', 'PROCEDURE')"
        )
    }
    procedures = frozenset(
        (r["name"] or "").upper()
        for r in conn.execute("SELECT name FROM objects WHERE type = 'PROCEDURE'")
    )
    packages = {
        (r["name"] or "").upper()
        for r in conn.execute("SELECT name FROM objects WHERE type = 'PACKAGE'")
    }
    tables = {t.upper() for (_, t) in emitted}

    for r in conn.execute(
        "SELECT owner, name FROM objects WHERE type = 'PACKAGE' ORDER BY owner, name"
    ):
        residue.append(
            Residue(
                r["owner"],
                r["name"],
                "package",
                "packages carry session state, overloads, and"
                " initialization; flattening them is a redesign, not a"
                " mechanical rewrite",
            )
        )
    for r in conn.execute(
        "SELECT owner, name FROM objects WHERE type = 'TYPE' ORDER BY owner, name"
    ):
        residue.append(
            Residue(
                r["owner"],
                r["name"],
                "type",
                "object types have no mechanical counterpart; redesign"
                " as tables and functions",
            )
        )

    units = conn.execute(
        "SELECT owner, name, type, parse_mode, error_count, first_error"
        " FROM plsql_units WHERE type IN ('FUNCTION', 'PROCEDURE')"
        " ORDER BY owner, name"
    ).fetchall()
    # A unit the catalog lists but whose source never reached the dump
    # is declined by name rather than forgotten.
    with_source = {(u["owner"], u["name"], u["type"]) for u in units}
    for r in conn.execute(
        "SELECT owner, name, type FROM objects"
        " WHERE type IN ('FUNCTION', 'PROCEDURE') ORDER BY owner, name"
    ):
        if (r["owner"], r["name"], r["type"]) not in with_source:
            residue.append(
                Residue(
                    r["owner"],
                    r["name"],
                    r["type"].lower(),
                    "no source for this unit reached the dump; extract it by hand",
                )
            )

    accepted: dict[str, tuple[str, str, str, list[str]]] = {}
    edges: dict[str, set[str]] = {}
    kinds: dict[str, tuple[str, str]] = {}
    for u in units:
        owner, name, otype = u["owner"], u["name"], u["type"]
        kind = otype.lower()
        kinds[name.upper()] = (owner, kind)
        if u["parse_mode"] == "generated":
            continue
        if u["parse_mode"] == "wrapped":
            residue.append(
                Residue(
                    owner,
                    name,
                    kind,
                    "source is wrapped; obtain the original source",
                )
            )
            continue
        if u["error_count"]:
            residue.append(
                Residue(
                    owner,
                    name,
                    kind,
                    f"did not parse cleanly ({u['first_error']}); rewrite it by hand",
                )
            )
            continue
        reasons, notes = _feature_gate(conn, owner, name, otype)
        call_reasons, call_edges = _call_gate(
            conn, owner, name, otype, owners, callables, packages
        )
        dep_reasons, dep_edges = _dependency_gate(
            conn,
            owner,
            name,
            otype,
            owners,
            tables,
            created_views,
            sequences,
            synonyms,
        )
        reasons += call_reasons + dep_reasons
        if not reasons:
            text = _unit_text(conn, owner, name, otype)
            relations = tables | created_views | synonyms
            result = rewrite_unit(text, otype, sequences, relations, procedures)
            reasons += list(result.reasons)
            notes += list(result.notes)
            sql = result.sql
        else:
            sql = None
        if reasons or sql is None:
            residue.append(Residue(owner, name, kind, _join(reasons)))
            continue
        accepted[name.upper()] = (owner, name, sql, notes)
        edges[name.upper()] = call_edges | dep_edges

    # A unit that calls a refused unit cannot ship either; iterate
    # until nothing else falls.
    changed = True
    while changed:
        changed = False
        for key in list(accepted):
            missing = [d for d in edges.get(key, set()) if d not in accepted]
            if missing:
                owner, name, _, _ = accepted.pop(key)
                _, kind = kinds.get(key, (owner, "function"))
                residue.append(
                    Residue(
                        owner,
                        name,
                        kind,
                        f"calls {missing[0]}, which was not converted",
                    )
                )
                changed = True

    # Callee-first order; cycles fall back to name order.
    remaining = {k: set(edges.get(k, set())) & set(accepted) for k in accepted}
    ordered: list[str] = []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps - set(ordered))
        if not ready:
            ordered.extend(sorted(remaining))
            break
        ordered.extend(ready)
        for k in ready:
            remaining.pop(k)

    count = 0
    for key in ordered:
        owner, name, sql, notes = accepted[key]
        _, kind = kinds.get(key, (owner, "function"))
        # Routines have their own namespace (pg_proc); a truncation
        # collision there would make CREATE OR REPLACE silently
        # replace the earlier routine.
        if not names.claim(name, kind, owner, residue, scope=ROUTINES):
            continue
        out.append(sql)
        out.append("")
        for note in dict.fromkeys(notes):
            residue.append(Residue(owner, name, "note", note))
        count += 1
    return count

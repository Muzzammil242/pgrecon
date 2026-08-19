"""Trigger emission: the body through the mechanical rewriter, paired
with the CREATE TRIGGER statement PostgreSQL wants.

A simple DML trigger maps mechanically: the block becomes a trigger
function, :NEW and :OLD lose their colons, the event predicates
become TG_OP tests, and the header is rebuilt from the parse tree so
UPDATE OF column lists survive. Everything else - compound triggers,
system triggers, INSTEAD OF, UPDATING('col') - refuses by name.
"""

import sqlite3
from typing import Any

from pgrecon.convert.code import (
    _call_gate,
    _dependency_gate,
    _feature_gate,
    _unit_text,
)
from pgrecon.convert.identifiers import _fold_condition
from pgrecon.convert.plsql_rewrite import (
    _apply,
    _first_descendant,
    _fold_written,
    rewrite_unit,
)
from pgrecon.convert.residue import Residue
from pgrecon.plsql import parse_source
from pgrecon.plsql._generated.PlSqlLexer import PlSqlLexer as L

_PREDICATES = {
    "INSERTING": "(TG_OP = 'INSERT')",
    "UPDATING": "(TG_OP = 'UPDATE')",
    "DELETING": "(TG_OP = 'DELETE')",
}


def _tree_of(ctx: Any, name: str) -> Any | None:
    return _first_descendant(ctx, name)


def _walk_all(node: Any, name: str) -> list[Any]:
    found = []
    stack = [node]
    while stack:
        current = stack.pop()
        for i in range(current.getChildCount()):
            child = current.getChild(i)
            if not hasattr(child, "getChildCount"):
                continue
            if type(child).__name__.replace("Context", "") == name:
                found.append(child)
            stack.append(child)
    return found


def _span(text: str, ctx: Any) -> str:
    return text[ctx.start.start : ctx.stop.stop + 1]


def _trigger_function(
    text: str,
    tree: Any,
    tokens: Any,
    fn_name: str,
    row_level: bool,
    sequences: set[str],
    relations: set[str],
    procedures: frozenset[str],
) -> tuple[str | None, list[str], list[str]]:
    """The trigger block as a PostgreSQL trigger function."""
    block = _tree_of(tree, "Trigger_block")
    if block is None:
        return None, ["the trigger body shape is not a plain block"], []
    start, stop = block.start.start, block.stop.stop
    stream = [t for t in tokens.tokens if t.channel == 0]
    edits: list[tuple[int, int, str]] = []
    reasons: list[str] = []
    fallthrough = "COALESCE(NEW, OLD)" if row_level else "NULL"

    for i, tok in enumerate(stream):
        if not (start <= tok.start <= stop):
            continue
        upper = (tok.text or "").upper()
        nxt = stream[i + 1] if i + 1 < len(stream) else None
        if upper in (":NEW", ":OLD"):
            edits.append((tok.start, tok.stop, upper[1:]))
        elif upper in _PREDICATES:
            if nxt is not None and nxt.type == L.LEFT_PAREN:
                reasons.append(
                    f"{upper}('column') tests which columns the UPDATE"
                    " names; PostgreSQL has no counterpart - rewrite by hand"
                )
            else:
                edits.append((tok.start, tok.stop, _PREDICATES[upper]))
        elif tok.type == L.DECLARE and tok.start == start:
            edits.append((tok.start, tok.stop, ""))

    for statement in _walk_all(block, "Return_statement"):
        if statement.getChildCount() == 1:
            edits.append(
                (statement.start.start, statement.stop.stop, f"RETURN {fallthrough}")
            )

    last_end = next(
        (t for t in reversed(stream) if t.type == L.END and start <= t.start <= stop),
        None,
    )
    if last_end is None:
        return None, ["the trigger body has no closing END"], []
    edits.append((last_end.start, last_end.stop, f"RETURN {fallthrough};\nEND"))

    if reasons:
        return None, reasons, []
    shifted = [(s - start, e - start, r) for s, e, r in edits]
    body = _apply(text[start : stop + 1], shifted)
    if body is None:
        return None, ["trigger rewrites collided; port it by hand"], []
    result = rewrite_unit(
        f"PROCEDURE {fn_name} IS\n{body}", "PROCEDURE", sequences, relations, procedures
    )
    if result.sql is None:
        return None, list(result.reasons), list(result.notes)
    sql = result.sql.replace(
        f"CREATE OR REPLACE PROCEDURE {fn_name}()",
        f"CREATE OR REPLACE FUNCTION {fn_name}() RETURNS trigger",
        1,
    )
    return sql, [], list(result.notes)


def _emit_triggers(
    conn: sqlite3.Connection,
    out: list[str],
    residue: list[Residue],
    emitted: dict[tuple[str, str], set[str]],
    sequences: set[str],
    relations: set[str],
    procedures: frozenset[str],
    owners: set[str],
    callables: set[str],
    packages: set[str],
) -> int:
    count = 0
    rows = conn.execute(
        "SELECT owner, trigger_name, trigger_type, status FROM triggers"
        " ORDER BY owner, trigger_name"
    ).fetchall()
    tables = {t for (_, t) in emitted}
    for r in rows:
        owner, name = r["owner"], r["trigger_name"]
        kind = (r["trigger_type"] or "").upper()
        if "COMPOUND" in kind:
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    "compound triggers combine timing points; restructure"
                    " as separate triggers by hand",
                )
            )
            continue
        if "INSTEAD OF" in kind:
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    "INSTEAD OF triggers need the view and its update"
                    " semantics reviewed; port by hand",
                )
            )
            continue
        unit = conn.execute(
            "SELECT parse_mode, error_count, first_error FROM plsql_units"
            " WHERE owner = ? AND name = ? AND type = 'TRIGGER'",
            (owner, name),
        ).fetchone()
        if unit is None or unit["parse_mode"] in ("wrapped", "generated"):
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    "no parseable trigger source was extracted",
                )
            )
            continue
        if unit["error_count"]:
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    f"did not parse cleanly ({unit['first_error']}); port it by hand",
                )
            )
            continue
        reasons, notes = _feature_gate(conn, owner, name, "TRIGGER")
        call_reasons, _ = _call_gate(
            conn, owner, name, "TRIGGER", owners, callables, packages
        )
        # The event predicates parse as calls when they carry a column
        # argument; the body rewriter names that case precisely.
        call_reasons = [
            x
            for x in call_reasons
            if not any(
                f"calls {p}," in x for p in ("INSERTING", "UPDATING", "DELETING")
            )
        ]
        dep_reasons, _ = _dependency_gate(
            conn, owner, name, "TRIGGER", owners, tables, set(), sequences, set()
        )
        reasons += call_reasons + dep_reasons
        if reasons:
            residue.append(Residue(owner, name, "trigger", "; ".join(reasons[:3])))
            continue

        text = "CREATE OR REPLACE " + _unit_text(conn, owner, name, "TRIGGER").rstrip()
        parse = parse_source(_unit_text(conn, owner, name, "TRIGGER").rstrip())
        if parse.tree is None or parse.errors:
            residue.append(
                Residue(owner, name, "trigger", "trigger source did not re-parse")
            )
            continue
        simple = _tree_of(parse.tree, "Simple_dml_trigger")
        if simple is None:
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    "only simple DML triggers convert mechanically;"
                    " port this shape by hand",
                )
            )
            continue
        event_clause = _tree_of(simple, "Dml_event_clause")
        table_ctx = (
            _tree_of(event_clause, "Tableview_name")
            if event_clause is not None
            else None
        )
        if event_clause is None or table_ctx is None:
            residue.append(
                Residue(owner, name, "trigger", "the trigger header did not dissect")
            )
            continue
        table = _fold_written(_span(text, table_ctx)).lower()
        if table.upper() not in tables:
            residue.append(
                Residue(
                    owner,
                    name,
                    "trigger",
                    f"its table {table.upper()} is not in the converted set",
                )
            )
            continue
        events = " OR ".join(
            " ".join(_span(text, e).lower().split())
            for e in _walk_all(event_clause, "Dml_event_element")
        )
        timing = "BEFORE"
        for i in range(simple.getChildCount()):
            child = simple.getChild(i)
            symbol = getattr(child, "symbol", None)
            if symbol is not None and symbol.type == L.AFTER:
                timing = "AFTER"
        row_level = _tree_of(simple, "For_each_row") is not None

        when_sql = ""
        when = _tree_of(parse.tree, "Trigger_when_clause")
        if when is not None:
            condition = _tree_of(when, "Condition")
            folded = (
                _fold_condition(_span(text, condition))
                if condition is not None
                else None
            )
            if folded is None:
                residue.append(
                    Residue(
                        owner,
                        name,
                        "trigger",
                        "the WHEN condition could not be translated; port it by hand",
                    )
                )
                continue
            when_sql = f" WHEN ({folded})"

        fn_name = f"{name.lower()}_fn"
        fn_sql, fn_reasons, fn_notes = _trigger_function(
            text,
            parse.tree,
            parse.tokens,
            fn_name,
            row_level,
            sequences,
            relations,
            procedures,
        )
        if fn_sql is None:
            residue.append(Residue(owner, name, "trigger", "; ".join(fn_reasons[:3])))
            continue
        out.append(fn_sql)
        out.append("")
        level = "FOR EACH ROW" if row_level else "FOR EACH STATEMENT"
        out.append(
            f"CREATE TRIGGER {name.lower()} {timing} {events} ON {table}\n"
            f"{level}{when_sql}\n"
            f"EXECUTE FUNCTION {fn_name}();"
        )
        if (r["status"] or "").upper() == "DISABLED":
            out.append(f"ALTER TABLE {table} DISABLE TRIGGER {name.lower()};")
        out.append("")
        for note in fn_notes:
            residue.append(Residue(owner, name, "note", note))
        if "nextval(" in fn_sql:
            residue.append(
                Residue(
                    owner,
                    name,
                    "note",
                    "sequence-fed trigger; a generated identity column is"
                    " the modern PostgreSQL shape for this",
                )
            )
        count += 1
    return count

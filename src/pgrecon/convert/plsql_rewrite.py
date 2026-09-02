"""Mechanical PL/SQL-to-PL/pgSQL rewriting of one stored unit.

Every change is a provably equivalent token or clause replacement
computed from the unit's parse tree - the same parse the assessment
ran. Anything the rewriter cannot prove becomes a named reason that
refuses the whole unit; a refused unit ships as residue, never as
DDL that might be wrong. Comments and formatting survive because the
edits are character-exact splices into the original text.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from antlr4 import ParseTreeWalker
from antlr4.tree.Tree import TerminalNode

from pgrecon.convert.identifiers import ident
from pgrecon.convert.typemap import map_code_type
from pgrecon.plsql import parse_source
from pgrecon.plsql._generated.PlSqlLexer import PlSqlLexer as L
from pgrecon.plsql._generated.PlSqlParserListener import PlSqlParserListener

_BODY_OPEN = "\x01"

_FORMAT_NOTE = (
    "TO_CHAR/TO_DATE format models overlap but are not identical;"
    " verify the format strings"
)

# Exception names whose PostgreSQL condition is the same behavior,
# not merely a similar name. Everything else refuses.
_CONDITION_MAP = {
    "OTHERS": None,
    "NO_DATA_FOUND": None,
    "TOO_MANY_ROWS": None,
    "DUP_VAL_ON_INDEX": "unique_violation",
    "ZERO_DIVIDE": "division_by_zero",
}


@dataclass(frozen=True)
class RewriteResult:
    sql: str | None
    reasons: tuple[str, ...]
    notes: tuple[str, ...]


def _fold_written(name: str) -> str:
    """A name as written in source, folded the way ident() folds.

    Generated DDL writes '"ADD_DATA"'; the converted schema knows that
    object as add_data, and '"RATE WITH SPACE"' as "rate with space".
    A quoted name carrying lowercase letters was case-sensitive on
    Oracle and stays verbatim, as the DDL emitters keep it.
    """
    if len(name) > 2 and name[0] == '"' and name[-1] == '"':
        inner = name[1:-1]
        if inner == inner.upper():
            return ident(inner)
    return name


class _Rewriter(PlSqlParserListener):  # type: ignore[misc]
    def __init__(
        self,
        text: str,
        is_function: bool,
        sequences: set[str],
        relations: set[str],
        procedures: frozenset[str],
    ) -> None:
        self.text = text
        self.is_function = is_function
        self.sequences = sequences
        self.relations = relations
        self.procedures = procedures
        self.edits: list[tuple[int, int, str]] = []
        # Loop variables of cursor FOR loops, which Oracle declares by
        # itself and PL/pgSQL wants declared as records.
        self.records: list[str] = []
        # MERGE action conditions to move onto their WHEN clause at
        # assembly: (matched start, stop, where start, stop, condition
        # start, stop).
        self.merge_moves: list[tuple[int, int, int, int, int, int]] = []
        # Statement terminators that already carry a LIMIT.
        self.limited: set[int] = set()
        self.reasons: list[str] = []
        self.notes: list[str] = []
        self.suppressed: list[tuple[int, int]] = []
        self.declares = False
        self.cursors: set[str] = set()
        self.locals: set[str] = set()
        # Cursor-attribute spans proven equivalent by adjacency, which
        # the token scan must not refuse a second time.
        self.handled: list[tuple[int, int]] = []
        # (span start, span end, USING arity) of each dynamic statement
        # whose literals are candidates for bind-placeholder folding.
        self.dynamic_specs: list[tuple[int, int, int]] = []

    # -- plumbing ---------------------------------------------------

    def _edit(self, start: int, stop: int, replacement: str) -> None:
        if not any(s <= start and stop <= e for s, e in self.suppressed):
            self.edits.append((start, stop, replacement))

    def _edit_ctx(self, ctx: Any, replacement: str) -> None:
        self._edit(ctx.start.start, ctx.stop.stop, replacement)

    def _reason(self, ctx: Any, message: str) -> None:
        self.reasons.append(f"{message} (line {ctx.start.line})")

    def _span_text(self, ctx: Any) -> str:
        return self.text[ctx.start.start : ctx.stop.stop + 1]

    def _terminals(self, ctx: Any) -> list[Any]:
        return [
            c.symbol
            for c in getattr(ctx, "children", None) or []
            if isinstance(c, TerminalNode)
        ]

    # -- unit header ------------------------------------------------

    def _header(self, ctx: Any) -> None:
        terminals = self._terminals(ctx)
        for tok in terminals:
            if tok.type == L.RETURN:
                self._edit(tok.start, tok.stop, "RETURNS")
            elif tok.type in (L.IS, L.AS):
                self._edit(tok.start, tok.stop, _BODY_OPEN)
            elif tok.type == L.DETERMINISTIC:
                self._edit(tok.start, tok.stop, "IMMUTABLE")
        if not any(t.type == L.LEFT_PAREN for t in terminals):
            name = ctx.function_name() if self.is_function else ctx.procedure_name()
            if name is not None:
                self._edit_ctx(name, _fold_written(self._span_text(name)) + "()")
                self.suppressed.append((name.start.start, name.stop.stop))
        if self.is_function:
            spec = ctx.type_spec()
            if (
                spec is not None
                and spec.PERCENT_ROWTYPE() is not None
                and spec.type_name() is not None
            ):
                # A function returns a table's row type by the table's
                # name on PostgreSQL; %ROWTYPE is for declarations only.
                # The anchor itself is validated as any declaration is.
                parts = [p.strip('"') for p in spec.type_name().getText().split(".")]
                self._edit_ctx(spec, ident(parts[-1]))
        if ctx.seq_of_declare_specs() is not None:
            self.declares = True
        body = ctx.body()
        if body is not None and body.label_name() is not None:
            label = body.label_name()
            self._edit(label.start.start, label.stop.stop, "")

    def enterCreate_function_body(self, ctx: Any) -> None:
        self._header(ctx)

    def enterCreate_procedure_body(self, ctx: Any) -> None:
        self._header(ctx)

    def enterInvoker_rights_clause(self, ctx: Any) -> None:
        target = (
            "SECURITY INVOKER"
            if "CURRENT_USER" in ctx.getText().upper()
            else "SECURITY DEFINER"
        )
        self._edit_ctx(ctx, target)

    def _drop_hint(self, ctx: Any, hint: str) -> None:
        self._edit_ctx(ctx, "")
        self.suppressed.append((ctx.start.start, ctx.stop.stop))
        self.notes.append(
            f"the {hint} hint has no PostgreSQL counterpart and was dropped"
        )

    def enterResult_cache_clause(self, ctx: Any) -> None:
        self._drop_hint(ctx, "RESULT_CACHE")

    def enterParallel_enable_clause(self, ctx: Any) -> None:
        self._drop_hint(ctx, "PARALLEL_ENABLE")

    # -- parameters -------------------------------------------------

    def enterParameter(self, ctx: Any) -> None:
        pname = ctx.parameter_name()
        if pname is not None:
            self.locals.add(pname.getText().strip('"').upper())
        modes = [t for t in self._terminals(ctx) if t.type in (L.IN, L.OUT, L.INOUT)]
        has_in = any(t.type == L.IN for t in modes)
        has_out = any(t.type == L.OUT for t in modes)
        if has_out and self.is_function:
            self._reason(
                ctx,
                "functions with OUT parameters change the call shape;"
                " redesign the interface",
            )
        elif has_in and has_out:
            first, second = modes[0], modes[1]
            self._edit(first.start, first.stop, "INOUT")
            self._edit(second.start, second.stop, "")
        for tok in self._terminals(ctx):
            if tok.type == L.NOCOPY:
                self._edit(tok.start, tok.stop, "")
        default = ctx.default_value_part()
        if default is not None:
            assign = default.start
            if assign.type == L.ASSIGN_OP:
                self._edit(assign.start, assign.stop, "DEFAULT")

    def enterParameter_spec(self, ctx: Any) -> None:
        if ctx.default_value_part() is not None:
            self._reason(
                ctx,
                "cursor parameter defaults are not supported; pass the value at OPEN",
            )

    def enterCursor_loop_param(self, ctx: Any) -> None:
        record = ctx.record_name()
        if record is not None:
            name = _fold_written(self._span_text(record))
            if name not in self.records:
                self.records.append(name)

    # -- MERGE ------------------------------------------------------

    def enterMerge_update_clause(self, ctx: Any) -> None:
        if ctx.merge_update_delete_part() is not None:
            self._reason(
                ctx,
                "MERGE ... WHEN MATCHED ... DELETE has no PostgreSQL form;"
                " express the delete as a second WHEN MATCHED clause by hand",
            )
            return
        self._merge_condition(ctx)

    def enterMerge_insert_clause(self, ctx: Any) -> None:
        self._merge_condition(ctx)

    def _merge_condition(self, ctx: Any) -> None:
        """Oracle filters a MERGE action with a trailing WHERE; PostgreSQL
        puts the condition on the WHEN. The move happens at assembly so
        the condition keeps every token rewrite made inside it."""
        where = ctx.where_clause()
        if where is None:
            return
        condition = where.condition()
        matched = ctx.MATCHED()
        if condition is None or matched is None:
            self._reason(
                ctx, "the MERGE action's WHERE did not dissect; port it by hand"
            )
            return
        self.merge_moves.append(
            (
                matched.symbol.start,
                matched.symbol.stop,
                where.start.start,
                where.stop.stop,
                condition.start.start,
                condition.stop.stop,
            )
        )

    def enterMerge_element(self, ctx: Any) -> None:
        # SET t.col = ... on Oracle; PostgreSQL wants the bare column.
        column = ctx.column_name()
        if column is None:
            return
        written = self._span_text(column)
        if "." in written:
            self._edit_ctx(column, _fold_written(written.rsplit(".", 1)[1]))

    # -- declarations -----------------------------------------------

    def enterType_spec(self, ctx: Any) -> None:
        anchored = ctx.PERCENT_TYPE() is not None or ctx.PERCENT_ROWTYPE() is not None
        if anchored:
            self._anchored_type(ctx)
            return
        datatype = ctx.datatype()
        if datatype is None:
            self._reason(
                ctx,
                f"type {ctx.getText()} has no mechanical mapping;"
                " choose the target type by hand",
            )
            return
        mapped = map_code_type(self._span_text(datatype))
        if mapped.pg_type is None:
            self._reason(ctx, mapped.note or "type has no counterpart")
            return
        self._edit_ctx(datatype, mapped.pg_type)

    def _anchored_type(self, ctx: Any) -> None:
        """%TYPE and %ROWTYPE survive only when their anchor will exist.

        PostgreSQL resolves the anchor at CREATE time against real
        relations and earlier declarations. A cursor%ROWTYPE anchor
        becomes a record variable, which is what FETCH INTO fills
        either way; anything unprovable refuses.
        """
        name = ctx.type_name()
        if name is None:
            return
        parts = [p.strip('"').upper() for p in name.getText().split(".")]
        rowtype = ctx.PERCENT_ROWTYPE() is not None
        if rowtype:
            if len(parts) == 1 and parts[0] in self.cursors:
                self._edit_ctx(ctx, "record")
                return
            if parts[-1] in self.relations:
                return
            self._reason(
                ctx,
                f"%ROWTYPE anchor {parts[-1]} is not a converted"
                " relation; declare the record by hand",
            )
            return
        if len(parts) == 1:
            if parts[0] in self.locals:
                return
            self._reason(
                ctx,
                f"%TYPE anchor {parts[0]} is not a local declaration;"
                " name the type by hand",
            )
            return
        if parts[-2] in self.relations:
            return
        self._reason(
            ctx,
            f"%TYPE anchor {parts[-2]} is not a converted relation;"
            " name the type by hand",
        )

    def enterVariable_declaration(self, ctx: Any) -> None:
        name = ctx.identifier()
        if name is not None:
            self.locals.add(name.getText().strip('"').upper())

    def enterCursor_declaration(self, ctx: Any) -> None:
        name = ctx.identifier()
        if name is None:
            return
        self.cursors.add(name.getText().strip('"').upper())
        for tok in self._terminals(ctx):
            if tok.type == L.CURSOR:
                self._edit(tok.start, tok.stop, "")
            elif tok.type == L.IS:
                self._edit(tok.start, tok.stop, "FOR")
            elif tok.type == L.RETURN:
                self._reason(
                    ctx,
                    "cursor RETURN clauses have no counterpart;"
                    " drop the clause by hand",
                )
        self._edit_ctx(name, self._span_text(name) + " CURSOR")

    def enterType_declaration(self, ctx: Any) -> None:
        self._reason(
            ctx,
            "local TYPE declarations have no counterpart; use %ROWTYPE"
            " or a schema-level composite type",
        )

    def enterSubtype_declaration(self, ctx: Any) -> None:
        self._reason(ctx, "SUBTYPE declarations have no counterpart")

    def enterException_declaration(self, ctx: Any) -> None:
        self._reason(
            ctx,
            "user-defined exceptions become RAISE EXCEPTION with a"
            " chosen SQLSTATE; rewrite them by hand",
        )

    def enterPragma_declaration(self, ctx: Any) -> None:
        self._reason(ctx, "PRAGMA directives have no counterpart")

    def _nested(self, ctx: Any) -> None:
        self._reason(
            ctx,
            "nested subprograms are not supported; extract them to"
            " standalone functions",
        )

    def enterFunction_body(self, ctx: Any) -> None:
        self._nested(ctx)

    def enterProcedure_body(self, ctx: Any) -> None:
        self._nested(ctx)

    def enterFunction_spec(self, ctx: Any) -> None:
        self._nested(ctx)

    def enterProcedure_spec(self, ctx: Any) -> None:
        self._nested(ctx)

    # -- statements -------------------------------------------------

    def enterExecute_immediate(self, ctx: Any) -> None:
        for tok in self._terminals(ctx):
            if tok.type == L.IMMEDIATE:
                self._edit(tok.start, tok.stop, "")
        self.notes.append(
            "dynamic SQL strings are not translated; verify each"
            " statement text against PostgreSQL"
        )
        using = ctx.using_clause()
        if isinstance(using, list):
            using = using[0] if using else None
        if using is None:
            return
        elements = using.using_element()
        if not isinstance(elements, list):
            elements = [elements] if elements is not None else []
        for element in elements:
            if any(t.type == L.OUT for t in self._terminals(element)):
                self._reason(
                    ctx,
                    "OUT bind arguments have no counterpart in"
                    " EXECUTE ... USING; rewrite the call by hand",
                )
                return
        # Literals live between the statement keyword and USING; the
        # token scan folds :name placeholders to $N when their count
        # matches the USING arity, because Oracle binds these by
        # position exactly as PostgreSQL numbers them.
        self.dynamic_specs.append(
            (ctx.start.start, using.start.start - 1, len(elements))
        )

    def enterInto_clause(self, ctx: Any) -> None:
        # Oracle SELECT INTO raises NO_DATA_FOUND on zero rows and
        # TOO_MANY_ROWS past one; plain plpgsql INTO does neither.
        # STRICT is the equivalent, for static and dynamic queries
        # alike. RETURNING INTO already behaves the same on both.
        parent = type(ctx.parentCtx).__name__
        if parent not in ("Query_blockContext", "Execute_immediateContext"):
            return
        for tok in self._terminals(ctx):
            if tok.type == L.INTO:
                self._edit(tok.start, tok.stop, "INTO STRICT")
                return

    def enterSeq_of_statements(self, ctx: Any) -> None:
        # EXIT WHEN c%NOTFOUND directly after FETCH c is the one
        # cursor-attribute shape with a proven equivalent: plpgsql's
        # FOUND reflects exactly the preceding FETCH.
        statements = ctx.statement()
        if not isinstance(statements, list):
            return
        for prev, nxt in zip(statements, statements[1:], strict=False):
            fetch = _first_descendant(prev, "Fetch_statement")
            exit_stmt = _first_descendant(nxt, "Exit_statement")
            if fetch is None or exit_stmt is None:
                continue
            cursor = fetch.cursor_name()
            condition = exit_stmt.condition()
            if cursor is None or condition is None:
                continue
            name = cursor.getText().strip('"').upper()
            spelled = condition.getText().strip().strip('"').upper()
            spelled = spelled.replace('"', "").replace(" ", "")
            if spelled == f"{name}%NOTFOUND":
                self._edit_ctx(condition, "NOT FOUND")
            elif spelled == f"{name}%FOUND":
                self._edit_ctx(condition, "FOUND")
            else:
                continue
            self.handled.append((condition.start.start, condition.stop.stop))

    def enterSavepoint_statement(self, ctx: Any) -> None:
        self._reason(
            ctx,
            "savepoints become exception-block subtransactions;"
            " restructure the error handling",
        )

    def enterLock_table_statement(self, ctx: Any) -> None:
        self._reason(ctx, "LOCK TABLE modes differ; port the locking by hand")

    def enterCall_statement(self, ctx: Any) -> None:
        names = ctx.routine_name()
        routine = names[0] if names else None
        if routine is None:
            return
        callee = routine.getText().upper()
        argument = ctx.function_argument()
        args = argument[0] if argument else None
        if callee == "DBMS_OUTPUT.PUT_LINE" and args is not None:
            self._edit_ctx(routine, "RAISE NOTICE '%',")
            self._edit(args.start.start, args.start.stop, " ")
            self._edit(args.stop.start, args.stop.stop, "")
        elif callee in ("DBMS_OUTPUT.ENABLE", "DBMS_OUTPUT.DISABLE"):
            # Buffer control around RAISE NOTICE is a no-op.
            self._edit_ctx(ctx, "NULL")
            self.suppressed.append((ctx.start.start, ctx.stop.stop))
        elif callee == "RAISE_APPLICATION_ERROR":
            self._reason(
                ctx,
                "RAISE_APPLICATION_ERROR carries an Oracle error code;"
                " choose a RAISE EXCEPTION ... USING ERRCODE mapping",
            )
        elif callee.replace('"', "") in self.procedures:
            # A bare procedure-call statement is not a statement on
            # PostgreSQL; it becomes CALL, with the parentheses CALL
            # requires.
            spelled = _fold_written(self._span_text(routine))
            if args is None:
                self._edit_ctx(routine, f"CALL {spelled}()")
            else:
                self._edit_ctx(routine, f"CALL {spelled}")

    def enterConcatenation(self, ctx: Any) -> None:
        # Oracle || treats NULL as the empty string; PostgreSQL ||
        # yields NULL when any part is NULL. concat() ignores NULLs,
        # and NULLIF restores the one case where Oracle does return
        # NULL: every part empty, because in Oracle '' IS NULL.
        if len(ctx.BAR()) != 2:
            return
        parent = ctx.parentCtx
        if type(parent).__name__ == "ConcatenationContext" and len(parent.BAR()) == 2:
            return
        links: list[Any] = []
        stack = [ctx]
        while stack:
            node = stack.pop()
            bars = node.BAR()
            if len(bars) == 2:
                links.append(bars)
                stack.extend(node.concatenation())
        self._edit(ctx.start.start, ctx.start.start - 1, "NULLIF(concat(")
        for first, second in links:
            self._edit(first.symbol.start, second.symbol.stop, ",")
        self._edit(ctx.stop.stop + 1, ctx.stop.stop, "), '')")

    def enterException_handler(self, ctx: Any) -> None:
        for name in ctx.exception_name():
            self._condition(name)

    def enterRaise_statement(self, ctx: Any) -> None:
        name = ctx.exception_name()
        if isinstance(name, list):
            name = name[0] if name else None
        if name is not None:
            self._condition(name)

    def _condition(self, name_ctx: Any) -> None:
        upper = name_ctx.getText().upper()
        if upper not in _CONDITION_MAP:
            self._reason(
                name_ctx,
                f"exception {upper} has no matching PostgreSQL"
                " condition; map it by hand",
            )
            return
        replacement = _CONDITION_MAP[upper]
        if replacement is not None:
            self._edit_ctx(name_ctx, replacement)


def _first_descendant(ctx: Any, name: str) -> Any | None:
    """The first descendant context of the given class inside one
    statement, without crossing into nested statement lists."""
    for i in range(ctx.getChildCount()):
        child = ctx.getChild(i)
        if not hasattr(child, "getChildCount"):
            continue
        kind = type(child).__name__.replace("Context", "")
        if kind == name:
            return child
        if kind == "Seq_of_statements":
            continue
        found = _first_descendant(child, name)
        if found is not None:
            return found
    return None


def _top_level_commas(tokens: list[Any], open_index: int) -> tuple[int, list[int]]:
    """Comma count and their indexes inside one balanced paren span."""
    depth = 0
    commas: list[int] = []
    for j in range(open_index, len(tokens)):
        t = tokens[j]
        if t.type == L.LEFT_PAREN:
            depth += 1
        elif t.type == L.RIGHT_PAREN:
            depth -= 1
            if depth == 0:
                return len(commas), commas
        elif t.type == L.COMMA and depth == 1:
            commas.append(j)
    return len(commas), commas


_CURSOR_ATTRIBUTES = {
    L.PERCENT_FOUND,
    L.PERCENT_NOTFOUND,
    L.PERCENT_ISOPEN,
    L.PERCENT_ROWCOUNT,
}

_Q_PAIRS = {"[": "]", "(": ")", "{": "}", "<": ">"}

_BIND = re.compile(r":([A-Za-z][A-Za-z0-9_]*)")


def _number_binds(body: str, counter: Iterator[int]) -> str:
    return _BIND.sub(lambda m: f"${next(counter)}", body)


def _fold_binds(rewriter: _Rewriter, tokens: list[Any]) -> set[int]:
    """Fold :name placeholders to $N inside dynamic statement literals.

    Oracle associates EXECUTE IMMEDIATE placeholders with USING
    arguments by position, which is exactly PostgreSQL's numbering, so
    the fold is safe precisely when the placeholder count across the
    statement's literals equals the USING arity. Anything else stays
    verbatim under the standing verify-by-hand note. Returns the
    token starts this pass rewrote, so the main scan leaves them be.
    """
    consumed: set[int] = set()
    for start, end, arity in rewriter.dynamic_specs:
        if arity == 0:
            continue
        literals = []
        total = 0
        for tok in tokens:
            if tok.type != L.CHAR_STRING or not start <= tok.start <= end:
                continue
            standard = _q_literal(tok.text or "") or (tok.text or "")
            count = len(_BIND.findall(standard[1:-1]))
            literals.append((tok, standard, count))
            total += count
        if total != arity:
            continue
        counter = iter(range(1, total + 1))
        for tok, standard, count in literals:
            if count == 0:
                continue
            body = _number_binds(standard[1:-1], counter)
            rewriter._edit(tok.start, tok.stop, "'" + body + "'")
            consumed.add(tok.start)
    return consumed


def _q_literal(text: str) -> str | None:
    """A q-quoted literal as a standard one, or None if not q-quoted."""
    if len(text) < 5 or text[0] not in "qQ" or text[1] != "'" or text[-1] != "'":
        return None
    opener = text[2]
    if text[-2] != _Q_PAIRS.get(opener, opener):
        return None
    return "'" + text[3:-2].replace("'", "''") + "'"


_AGGREGATES = {"COUNT", "SUM", "MIN", "MAX", "AVG", "LISTAGG", "STDDEV", "VARIANCE"}
_ROWNUM_BREAKERS = {
    L.ORDER: "ORDER BY",
    L.GROUP: "GROUP BY",
    L.HAVING: "HAVING",
    L.UNION: "UNION",
    L.INTERSECT: "INTERSECT",
    L.MINUS: "MINUS",
    L.CONNECT: "CONNECT BY",
    L.START: "START WITH",
}
_ROWNUM_GENERIC = (
    "ROWNUM outside a plain top-N bound needs LIMIT or row_number(); rewrite by hand"
)


def _fold_rownum(rewriter: _Rewriter, tokens: list[Any]) -> None:
    """Every ROWNUM either becomes a LIMIT or names its refusal."""
    for i, tok in enumerate(tokens):
        if tok.type == L.ROWNUM:
            reason = _rownum_to_limit(rewriter, tokens, i)
            if reason is not None:
                rewriter.reasons.append(f"{reason} (line {tok.line})")


def _rownum_to_limit(rewriter: _Rewriter, tokens: list[Any], i: int) -> str | None:
    """Turn the top-N idiom into LIMIT on its query, or say why not.

    The shape that converts: ROWNUM compared with an integer literal,
    as a plain conjunct of a SELECT's WHERE, with no ORDER BY, GROUP
    BY, set operation, DISTINCT, or aggregate in that same query -
    Oracle numbers rows before all of those, so LIMIT would mean
    something else. The bound is removed from the WHERE and LIMIT n
    goes at the end of that query, ahead of any FOR UPDATE.
    """
    j = i + 1
    if j >= len(tokens):
        return _ROWNUM_GENERIC
    op = tokens[j]
    if op.type == L.LESS_THAN_OP:
        kind = "lt"
        if (
            j + 1 < len(tokens)
            and tokens[j + 1].type == L.EQUALS_OP
            and tokens[j + 1].start == op.stop + 1
        ):
            kind = "lte"
            j += 1
    elif op.type == L.EQUALS_OP:
        kind = "eq"
    else:
        return _ROWNUM_GENERIC
    if j + 1 >= len(tokens) or tokens[j + 1].type != L.UNSIGNED_INTEGER:
        return _ROWNUM_GENERIC
    num = tokens[j + 1]
    bound = int(num.text or "0")
    if kind == "lt":
        bound -= 1
    if kind == "eq" and bound != 1:
        return (
            "ROWNUM = n above 1 never matches a row on Oracle; rewrite the query"
            " by hand"
        )
    if bound < 1:
        return _ROWNUM_GENERIC
    prev = tokens[i - 1] if i > 0 else None
    if prev is None or prev.type not in (L.WHERE, L.AND):
        return _ROWNUM_GENERIC

    # The query this WHERE belongs to, walking left at depth 0.
    depth = 0
    k = i - 1
    where_at = select_at = None
    while k >= 0:
        t = tokens[k]
        if t.type == L.RIGHT_PAREN:
            depth += 1
        elif t.type == L.LEFT_PAREN:
            if depth == 0:
                return "ROWNUM inside a parenthesized condition needs a rewrite by hand"
            depth -= 1
        elif depth == 0:
            if t.type == L.WHERE and where_at is None:
                where_at = k
            elif where_at is not None and t.type == L.SELECT:
                select_at = k
                break
            elif where_at is not None and t.type in (L.DELETE, L.UPDATE):
                return (
                    "ROWNUM in DELETE or UPDATE has no LIMIT on PostgreSQL; bound"
                    " the rows through the key in a subquery by hand"
                )
            elif t.type in (L.SEMICOLON, L.BEGIN, L.LOOP, L.THEN, L.ELSE):
                break
            elif where_at is not None and t.type == L.OR:
                return "ROWNUM under OR needs a rewrite by hand"
        k -= 1
    if select_at is None or where_at is None:
        return _ROWNUM_GENERIC

    # The select list: no DISTINCT, no aggregate ahead of the bound.
    depth = 0
    for k in range(select_at + 1, where_at):
        t = tokens[k]
        if t.type == L.LEFT_PAREN:
            depth += 1
        elif t.type == L.RIGHT_PAREN:
            depth -= 1
        elif depth == 0:
            if k == select_at + 1 and t.type in (L.DISTINCT, L.UNIQUE):
                return "ROWNUM with DISTINCT is not a top-N bound; rewrite by hand"
            if t.type == L.FROM:
                break
            nxt = tokens[k + 1] if k + 1 < len(tokens) else None
            if (
                (t.text or "").upper() in _AGGREGATES
                and nxt is not None
                and nxt.type == L.LEFT_PAREN
            ):
                return (
                    "ROWNUM ahead of an aggregate bounds the rows counted, which"
                    " LIMIT does not; rewrite by hand"
                )

    # The rest of the query, walking right at depth 0 to its end.
    depth = 0
    m = j + 2
    terminator = None
    while m < len(tokens):
        t = tokens[m]
        if t.type == L.LEFT_PAREN:
            depth += 1
        elif t.type == L.RIGHT_PAREN:
            if depth == 0:
                terminator = m
                break
            depth -= 1
        elif depth == 0:
            if t.type in (L.SEMICOLON, L.FOR):
                terminator = m
                break
            if t.type in _ROWNUM_BREAKERS:
                return (
                    f"ROWNUM beside {_ROWNUM_BREAKERS[t.type]} in the same query"
                    " is not a top-N bound on Oracle either; sort or group in a"
                    " subquery, then bound, by hand"
                )
            if t.type == L.OR:
                return "ROWNUM under OR needs a rewrite by hand"
        m += 1
    if terminator is None:
        return _ROWNUM_GENERIC
    if terminator in rewriter.limited:
        return "ROWNUM bounded twice in one query; rewrite by hand"
    rewriter.limited.add(terminator)

    following = tokens[j + 2]
    if prev.type == L.WHERE and following.type == L.AND:
        rewriter._edit(tokens[i].start, following.stop, "")
    else:
        rewriter._edit(prev.start, num.stop, "")
    term = tokens[terminator]
    if term.type == L.FOR:
        rewriter._edit(term.start, term.stop, f"LIMIT {bound} FOR")
    else:
        rewriter._edit(term.start, term.stop, f" LIMIT {bound}{term.text}")
    return None


def _merge_moves(text: str, rewriter: _Rewriter) -> list[tuple[int, int, str]]:
    """Move each MERGE action's trailing WHERE onto its WHEN clause,
    carrying the token rewrites made inside the condition along."""
    edits = list(rewriter.edits)
    for m_start, m_stop, w_start, w_stop, c_start, c_stop in rewriter.merge_moves:
        inner = [e for e in edits if c_start <= e[0] and e[1] <= c_stop]
        edits = [e for e in edits if e not in inner]
        shifted = [(s - c_start, e - c_start, r) for s, e, r in inner]
        folded = _apply(text[c_start : c_stop + 1], shifted)
        if folded is None:
            rewriter.reasons.append(
                "MERGE condition rewrites collided; port it by hand"
            )
            return edits
        edits.append((w_start, w_stop, ""))
        edits.append((m_start, m_stop, f"MATCHED AND ({folded.strip()})"))
    return edits


def _scan_tokens(rewriter: _Rewriter, stream: Any) -> None:
    """Function-level rewrites off the default token channel.

    Everything here is either a pure token swap (SYSDATE, NVL, FROM
    DUAL, q-literals) or a refusal that needs argument shape the tree
    listeners do not expose (TO_DATE arity, INSTR arity, negative
    SUBSTR starts). Comments and strings live on other channels, so a
    match here is live code.
    """
    tokens = [t for t in stream.tokens if t.channel == 0]
    folded_literals = _fold_binds(rewriter, tokens)
    _fold_rownum(rewriter, tokens)
    for i, tok in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        prev = tokens[i - 1] if i > 0 else None
        after = tokens[i + 2] if i + 2 < len(tokens) else None
        text = (tok.text or "").upper()
        if tok.type == L.SYSDATE:
            rewriter._edit(tok.start, tok.stop, "CURRENT_TIMESTAMP")
        elif (
            tok.type == L.FROM
            and nxt is not None
            and (nxt.text or "").upper() == "DUAL"
            and (after is None or after.type != L.PERIOD)
        ):
            rewriter._edit(tok.start, nxt.stop, "")
        elif (
            tok.type == L.USING
            and nxt is not None
            and (nxt.text or "").upper() == "DUAL"
        ):
            # MERGE ... USING dual: a one-row source PostgreSQL lacks.
            alias = " AS dual" if after is None or after.type == L.ON else ""
            rewriter._edit(nxt.start, nxt.stop, "(SELECT 1)" + alias)
        elif tok.type == L.CHAR_STRING:
            if tok.start not in folded_literals:
                standard = _q_literal(tok.text or "")
                if standard is not None:
                    rewriter._edit(tok.start, tok.stop, standard)
        elif tok.type == L.DELIMITED_ID:
            folded = _fold_written(tok.text or "")
            if folded != (tok.text or ""):
                rewriter._edit(tok.start, tok.stop, folded)
        elif tok.type in _CURSOR_ATTRIBUTES and (prev is None or prev.type != L.SQL):
            if not any(s <= tok.start <= e for s, e in rewriter.handled):
                rewriter.reasons.append(
                    "cursor attributes become the FOUND variable or GET"
                    f" DIAGNOSTICS; rewrite them by hand (line {tok.line})"
                )
        elif text == "SQLCODE":
            rewriter.reasons.append(
                "SQLCODE becomes SQLSTATE with different values;"
                f" rewrite the handler by hand (line {tok.line})"
            )
        elif text == "@":
            rewriter.reasons.append(f"reads through a database link (line {tok.line})")
        elif (
            nxt is not None
            and nxt.type == L.PERIOD
            and after is not None
            and (after.text or "").upper() in ("NEXTVAL", "CURRVAL")
            and tok.type != L.PERIOD
        ):
            call = "nextval" if (after.text or "").upper() == "NEXTVAL" else "currval"
            # An owner-qualified reference spans back over the schema
            # prefix; single-schema conversion drops it either way.
            start = tok.start
            if prev is not None and prev.type == L.PERIOD and i >= 2:
                start = tokens[i - 2].start
            if text in rewriter.sequences:
                rewriter._edit(
                    start, after.stop, f"{call}('{ident(tok.text.lower())}')"
                )
            else:
                rewriter.reasons.append(
                    f"references {text}.{(after.text or '').upper()} but"
                    f" {text} is not an extracted sequence (line {tok.line})"
                )
        elif nxt is not None and nxt.type == L.LEFT_PAREN:
            if text == "NVL":
                rewriter._edit(tok.start, tok.stop, "COALESCE")
            elif text in ("TO_DATE", "TO_TIMESTAMP"):
                count, _ = _top_level_commas(tokens, i + 1)
                if count == 0:
                    rewriter.reasons.append(
                        f"{text} over a single argument has no PostgreSQL"
                        f" signature; rewrite it by hand (line {tok.line})"
                    )
                else:
                    rewriter.notes.append(_FORMAT_NOTE)
            elif text == "TO_CHAR":
                count, _ = _top_level_commas(tokens, i + 1)
                if count:
                    rewriter.notes.append(_FORMAT_NOTE)
            elif text == "INSTR":
                count, _ = _top_level_commas(tokens, i + 1)
                if count == 1:
                    rewriter._edit(tok.start, tok.stop, "strpos")
                else:
                    rewriter.reasons.append(
                        "INSTR with position or occurrence arguments"
                        f" needs a rewrite by hand (line {tok.line})"
                    )
            elif text == "SUBSTR":
                _, commas = _top_level_commas(tokens, i + 1)
                if commas:
                    arg = tokens[commas[0] + 1] if commas[0] + 1 < len(tokens) else None
                    if arg is not None and (arg.text or "") == "-":
                        rewriter.reasons.append(
                            "SUBSTR with a negative start counts from the"
                            f" end on Oracle; rewrite it by hand (line {tok.line})"
                        )


def _apply(text: str, edits: list[tuple[int, int, str]]) -> str | None:
    """Splice non-overlapping edits into the text; None on conflict."""
    ordered = sorted(edits)
    last = -1
    for start, stop, _ in ordered:
        if start <= last:
            return None
        last = stop
    parts: list[str] = []
    pos = 0
    for start, stop, replacement in ordered:
        parts.append(text[pos:start])
        parts.append(replacement)
        pos = stop + 1
    parts.append(text[pos:])
    return "".join(parts)


def rewrite_unit(
    text: str,
    unit_type: str,
    sequences: set[str],
    relations: set[str],
    procedures: frozenset[str] = frozenset(),
) -> RewriteResult:
    """One stored FUNCTION or PROCEDURE as PostgreSQL DDL, or reasons.

    The input is the unit exactly as ALL_SOURCE stored it, starting at
    its type keyword; the output is a complete CREATE OR REPLACE
    statement in dollar quoting, or None with every reason the unit
    was refused. Callees named in procedures are procedure-call
    statements on the source side and gain the CALL PostgreSQL needs.
    """
    parse = parse_source(text.rstrip())
    if parse.tree is None or parse.errors:
        first = parse.errors[0] if parse.errors else "no parse tree"
        return RewriteResult(None, (f"did not parse cleanly ({first})",), ())
    full = "CREATE OR REPLACE " + text.rstrip()
    rewriter = _Rewriter(
        full, unit_type.upper() == "FUNCTION", sequences, relations, procedures
    )
    ParseTreeWalker.DEFAULT.walk(rewriter, parse.tree)
    _scan_tokens(rewriter, parse.tokens)
    edits = _merge_moves(full, rewriter)
    notes = tuple(dict.fromkeys(rewriter.notes))
    if rewriter.reasons:
        return RewriteResult(None, tuple(dict.fromkeys(rewriter.reasons)), notes)
    edited = _apply(full, edits)
    if edited is None or _BODY_OPEN not in edited:
        # Overlapping edits, or a shape with no IS/AS body such as an
        # external call specification: refuse rather than guess.
        return RewriteResult(
            None, ("the unit's shape defeated the rewriter; port it by hand",), notes
        )
    delimiter = "$body$"
    while delimiter in edited:
        delimiter = delimiter[:-1] + "_$"
    opener = f"LANGUAGE plpgsql\nAS {delimiter}\n"
    records = "".join(f"\n  {name} record;" for name in rewriter.records)
    if rewriter.declares or records:
        opener += "DECLARE" + records
    edited = edited.replace(_BODY_OPEN, opener, 1)
    return RewriteResult(edited.rstrip() + f"\n{delimiter};", (), notes)

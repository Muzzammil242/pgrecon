"""Mechanical PL/SQL-to-PL/pgSQL rewriting of one stored unit.

Every change is a provably equivalent token or clause replacement
computed from the unit's parse tree - the same parse the assessment
ran. Anything the rewriter cannot prove becomes a named reason that
refuses the whole unit; a refused unit ships as residue, never as
DDL that might be wrong. Comments and formatting survive because the
edits are character-exact splices into the original text.
"""

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


class _Rewriter(PlSqlParserListener):  # type: ignore[misc]
    def __init__(self, text: str, is_function: bool, sequences: set[str]) -> None:
        self.text = text
        self.is_function = is_function
        self.sequences = sequences
        self.edits: list[tuple[int, int, str]] = []
        self.reasons: list[str] = []
        self.notes: list[str] = []
        self.suppressed: list[tuple[int, int]] = []
        self.declares = False

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
                self._edit_ctx(name, self._span_text(name) + "()")
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

    # -- declarations -----------------------------------------------

    def enterType_spec(self, ctx: Any) -> None:
        if ctx.PERCENT_TYPE() is not None or ctx.PERCENT_ROWTYPE() is not None:
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

    def enterCursor_declaration(self, ctx: Any) -> None:
        name = ctx.identifier()
        if name is None:
            return
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


def _q_literal(text: str) -> str | None:
    """A q-quoted literal as a standard one, or None if not q-quoted."""
    if len(text) < 5 or text[0] not in "qQ" or text[1] != "'" or text[-1] != "'":
        return None
    opener = text[2]
    if text[-2] != _Q_PAIRS.get(opener, opener):
        return None
    return "'" + text[3:-2].replace("'", "''") + "'"


def _scan_tokens(rewriter: _Rewriter, stream: Any) -> None:
    """Function-level rewrites off the default token channel.

    Everything here is either a pure token swap (SYSDATE, NVL, FROM
    DUAL, q-literals) or a refusal that needs argument shape the tree
    listeners do not expose (TO_DATE arity, INSTR arity, negative
    SUBSTR starts). Comments and strings live on other channels, so a
    match here is live code.
    """
    tokens = [t for t in stream.tokens if t.channel == 0]
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
        elif tok.type == L.CHAR_STRING:
            standard = _q_literal(tok.text or "")
            if standard is not None:
                rewriter._edit(tok.start, tok.stop, standard)
        elif tok.type in _CURSOR_ATTRIBUTES and (prev is None or prev.type != L.SQL):
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


def rewrite_unit(text: str, unit_type: str, sequences: set[str]) -> RewriteResult:
    """One stored FUNCTION or PROCEDURE as PostgreSQL DDL, or reasons.

    The input is the unit exactly as ALL_SOURCE stored it, starting at
    its type keyword; the output is a complete CREATE OR REPLACE
    statement in dollar quoting, or None with every reason the unit
    was refused.
    """
    parse = parse_source(text.rstrip())
    if parse.tree is None or parse.errors:
        first = parse.errors[0] if parse.errors else "no parse tree"
        return RewriteResult(None, (f"did not parse cleanly ({first})",), ())
    full = "CREATE OR REPLACE " + text.rstrip()
    rewriter = _Rewriter(full, unit_type.upper() == "FUNCTION", sequences)
    ParseTreeWalker.DEFAULT.walk(rewriter, parse.tree)
    _scan_tokens(rewriter, parse.tokens)
    notes = tuple(dict.fromkeys(rewriter.notes))
    if rewriter.reasons:
        return RewriteResult(None, tuple(dict.fromkeys(rewriter.reasons)), notes)
    edited = _apply(full, rewriter.edits)
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
    if rewriter.declares:
        opener += "DECLARE"
    edited = edited.replace(_BODY_OPEN, opener, 1)
    return RewriteResult(edited.rstrip() + f"\n{delimiter};", (), notes)

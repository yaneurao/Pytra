"""Profile-driven common renderer for shared EAST3 node walking.

This base class owns language-neutral expression/statement dispatch and reads
operator/syntax tables from the canonical emit profile JSON. Language emitters
override only the nodes or statement forms they need to specialize.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal

from toolchain2.emit.common.profile_loader import load_profile_doc


@dataclass
class CommonRendererState:
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)


class CommonRenderer(ABC):
    def __init__(self, language: str) -> None:
        self.language = language
        self.profile = load_profile_doc(language)
        self.state = CommonRendererState()

    # ------------------------------------------------------------------
    # profile helpers
    # ------------------------------------------------------------------

    def _lowering(self) -> dict[str, JsonVal]:
        raw = self.profile.get("lowering")
        return raw if isinstance(raw, dict) else {}

    def _syntax(self) -> dict[str, JsonVal]:
        raw = self.profile.get("syntax")
        return raw if isinstance(raw, dict) else {}

    def _operators(self) -> dict[str, JsonVal]:
        raw = self.profile.get("operators")
        return raw if isinstance(raw, dict) else {}

    def _syntax_text(self, key: str, default: str) -> str:
        value = self._syntax().get(key)
        return value if isinstance(value, str) and value != "" else default

    def _stmt_terminator(self) -> str:
        value = self._lowering().get("stmt_terminator")
        return value if isinstance(value, str) else ""

    def _condition_parens(self) -> bool:
        value = self._lowering().get("condition_parens")
        return value if isinstance(value, bool) else True

    def _none_literal(self) -> str:
        value = self._lowering().get("none_literal")
        return value if isinstance(value, str) and value != "" else "null"

    def _bool_literal(self, value: bool) -> str:
        raw = self._lowering().get("bool_literals")
        if isinstance(raw, list) and len(raw) == 2:
            true_lit = raw[0]
            false_lit = raw[1]
            if isinstance(true_lit, str) and isinstance(false_lit, str):
                return true_lit if value else false_lit
        return "true" if value else "false"

    def _operator_text(self, group: str, op: str, default: str) -> str:
        operators = self._operators().get(group)
        if isinstance(operators, dict):
            value = operators.get(op)
            if isinstance(value, str) and value != "":
                return value
        return default

    # ------------------------------------------------------------------
    # line helpers
    # ------------------------------------------------------------------

    def _indent(self) -> str:
        return "    " * self.state.indent_level

    def _emit(self, line: str) -> None:
        self.state.lines.append(self._indent() + line)

    def _emit_blank(self) -> None:
        self.state.lines.append("")

    def finish(self) -> str:
        return "\n".join(self.state.lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # node helpers
    # ------------------------------------------------------------------

    def _str(self, node: JsonVal, key: str) -> str:
        if isinstance(node, dict):
            value = node.get(key)
            if isinstance(value, str):
                return value
        return ""

    def _list(self, node: JsonVal, key: str) -> list[JsonVal]:
        if isinstance(node, dict):
            value = node.get(key)
            if isinstance(value, list):
                return value
        return []

    def _quote_string(self, value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

    def _format_condition(self, rendered: str) -> str:
        return "(" + rendered + ")" if self._condition_parens() else rendered

    def _emit_stmt_line(self, text: str) -> None:
        term = self._stmt_terminator()
        if term != "" and not text.endswith(term):
            text = text + term
        self._emit(text)

    # ------------------------------------------------------------------
    # overridable hooks
    # ------------------------------------------------------------------

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return self._str(node, "id")

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("common renderer requires attribute override for " + self.language)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("common renderer requires call override for " + self.language)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("common renderer requires assign override for " + self.language)

    def render_expr_extension(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("unsupported expr kind in common renderer: " + self._str(node, "kind"))

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        raise RuntimeError("unsupported stmt kind in common renderer: " + self._str(node, "kind"))

    # ------------------------------------------------------------------
    # expression rendering
    # ------------------------------------------------------------------

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        value = node.get("value")
        if value is None:
            return self._none_literal()
        if isinstance(value, bool):
            return self._bool_literal(value)
        if isinstance(value, str):
            return self._quote_string(value)
        return str(value)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        left = self.render_expr(node.get("left"))
        right = self.render_expr(node.get("right"))
        op = self._operator_text("bin", self._str(node, "op"), self._str(node, "op"))
        return "(" + left + " " + op + " " + right + ")"

    def render_unaryop(self, node: dict[str, JsonVal]) -> str:
        operand = self.render_expr(node.get("operand"))
        op = self._operator_text("unary", self._str(node, "op"), self._str(node, "op"))
        return "(" + op + operand + ")"

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        left = self.render_expr(node.get("left"))
        comparators = self._list(node, "comparators")
        ops = self._list(node, "ops")
        if len(comparators) == 0 or len(ops) == 0:
            return left
        parts: list[str] = []
        current_left = left
        for idx, comparator in enumerate(comparators):
            op_obj = ops[idx] if idx < len(ops) else None
            op_name = op_obj if isinstance(op_obj, str) else self._str(op_obj, "kind")
            op_text = self._operator_text("cmp", op_name, op_name)
            right = self.render_expr(comparator)
            parts.append("(" + current_left + " " + op_text + " " + right + ")")
            current_left = right
        if len(parts) == 1:
            return parts[0]
        joiner = " " + self._operator_text("bool", "And", "&&") + " "
        return "(" + joiner.join(parts) + ")"

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        values = self._list(node, "values")
        op_text = self._operator_text("bool", self._str(node, "op"), self._str(node, "op"))
        return "(" + (" " + op_text + " ").join(self.render_expr(value) for value in values) + ")"

    def render_expr(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            raise RuntimeError("common renderer expected dict expr node")
        kind = self._str(node, "kind")
        if kind == "Constant":
            return self.render_constant(node)
        if kind == "Name":
            return self.render_name(node)
        if kind == "BinOp":
            return self.render_binop(node)
        if kind == "UnaryOp":
            return self.render_unaryop(node)
        if kind == "Compare":
            return self.render_compare(node)
        if kind == "BoolOp":
            return self.render_boolop(node)
        if kind == "Attribute":
            return self.render_attribute(node)
        if kind == "Call":
            return self.render_call(node)
        return self.render_expr_extension(node)

    # ------------------------------------------------------------------
    # statement emission
    # ------------------------------------------------------------------

    def emit_body(self, body: list[JsonVal]) -> None:
        for stmt in body:
            self.emit_stmt(stmt)

    def emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            return
        kind = self._str(node, "kind")
        if kind == "Expr":
            self._emit_stmt_line(self.render_expr(node.get("value")))
            return
        if kind == "Return":
            value = node.get("value")
            if isinstance(value, dict):
                self._emit_stmt_line(self._syntax_text("return", "return") + " " + self.render_expr(value))
            else:
                self._emit_stmt_line(self._syntax_text("return", "return"))
            return
        if kind == "Assign" or kind == "AnnAssign":
            self._emit_stmt_line(self.render_assign_stmt(node))
            return
        if kind == "If":
            test = self._format_condition(self.render_expr(node.get("test")))
            self._emit(self._syntax_text("if", "if ({cond}) {").replace("{cond}", test))
            self.state.indent_level += 1
            self.emit_body(self._list(node, "body"))
            self.state.indent_level -= 1
            orelse = self._list(node, "orelse")
            if len(orelse) > 0:
                self._emit(self._syntax_text("else", "} else {"))
                self.state.indent_level += 1
                self.emit_body(orelse)
                self.state.indent_level -= 1
            self._emit(self._syntax_text("block_close", "}"))
            return
        if kind == "While":
            test = self._format_condition(self.render_expr(node.get("test")))
            self._emit(self._syntax_text("while", "while ({cond}) {").replace("{cond}", test))
            self.state.indent_level += 1
            self.emit_body(self._list(node, "body"))
            self.state.indent_level -= 1
            self._emit(self._syntax_text("block_close", "}"))
            return
        self.emit_stmt_extension(node)

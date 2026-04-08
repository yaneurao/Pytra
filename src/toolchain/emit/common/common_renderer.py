"""Profile-driven common renderer for shared EAST3 node walking.

This base class owns language-neutral expression/statement dispatch and reads
operator/syntax tables from the canonical emit profile JSON. Language emitters
override only the nodes or statement forms they need to specialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal

from toolchain.emit.common.profile_loader import load_profile_doc


@dataclass
class CommonRendererState:
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    tmp_counter: int = 0


class CommonRenderer:
    def __init__(self, language: str) -> None:
        self.language = language
        self.profile = load_profile_doc(language)
        self.state = CommonRendererState()
        self._op_prec_table: dict[str, int] = {}
        self._literal_nowrap_ranges: dict[str, tuple[int, int] | str] = {}
        operators = self.profile.get("operators")
        precedence = operators.get("precedence") if isinstance(operators, dict) else None
        if isinstance(precedence, dict):
            for key, value in precedence.items():
                if isinstance(key, str) and isinstance(value, int):
                    self._op_prec_table[key] = value
        literal_nowrap = self.profile.get("literal_nowrap_ranges")
        if isinstance(literal_nowrap, dict):
            for key, value in literal_nowrap.items():
                if not isinstance(key, str):
                    continue
                if value == "always":
                    self._literal_nowrap_ranges[key] = "always"
                    continue
                if (
                    isinstance(value, list)
                    and len(value) == 2
                    and isinstance(value[0], int)
                    and isinstance(value[1], int)
                ):
                    self._literal_nowrap_ranges[key] = (value[0], value[1])

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

    def _syntax_text(self, key: str, fallback: str) -> str:
        value = self._syntax().get(key)
        return value if isinstance(value, str) and value != "" else fallback

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

    def _operator_text(self, group: str, op: str, fallback: str) -> str:
        operators = self._operators().get(group)
        if isinstance(operators, dict):
            value = operators.get(op)
            if isinstance(value, str) and value != "":
                return value
        return fallback

    def _operator_precedence(self, op: str) -> int:
        value = self._op_prec_table.get(op)
        return value if isinstance(value, int) else -1

    def _literal_type_text(self, resolved_type: str) -> str:
        raw = self.profile.get("types")
        if isinstance(raw, dict):
            mapped = raw.get(resolved_type)
            if isinstance(mapped, str) and mapped != "":
                return mapped
        return resolved_type

    def _literal_can_omit_wrap(self, resolved_type: str, value: int) -> bool:
        spec = self._literal_nowrap_ranges.get(resolved_type)
        if spec == "always":
            return True
        if isinstance(spec, tuple):
            return spec[0] <= value <= spec[1]
        return False

    def _wrap_int_literal(self, resolved_type: str, value: int) -> str:
        literal_type = self._literal_type_text(resolved_type)
        if literal_type == "":
            literal_type = resolved_type
        if literal_type == "":
            return str(value)
        return literal_type + "(" + str(value) + ")"

    def _expr_precedence(self, node: JsonVal) -> int:
        if not isinstance(node, dict):
            return 100
        kind = self._str(node, "kind")
        if kind == "BinOp":
            return self._operator_precedence(self._str(node, "op"))
        if kind == "BoolOp":
            return self._operator_precedence(self._str(node, "op"))
        if kind == "Compare":
            ops = self._list(node, "ops")
            if len(ops) == 0:
                return 100
            op_obj = ops[0]
            op_name = op_obj if isinstance(op_obj, str) else self._str(op_obj, "kind")
            return self._operator_precedence(op_name)
        if kind == "UnaryOp":
            return self._operator_precedence(self._str(node, "op"))
        return 100

    def _needs_parentheses(self, child: JsonVal, parent_op: str, *, is_right: bool = False) -> bool:
        parent_prec = self._operator_precedence(parent_op)
        if parent_prec < 0:
            return False
        child_prec = self._expr_precedence(child)
        if child_prec < 0:
            return False
        if child_prec < parent_prec:
            return True
        if is_right and child_prec == parent_prec and isinstance(child, dict):
            kind = self._str(child, "kind")
            if kind in ("BinOp", "BoolOp", "Compare"):
                return True
        return False

    def _wrap_expr_for_precedence(
        self,
        rendered: str,
        node: JsonVal,
        parent_op: str,
        *,
        is_right: bool = False,
    ) -> str:
        if self._needs_parentheses(node, parent_op, is_right=is_right):
            return "(" + rendered + ")"
        return rendered

    def _render_infix_expr(
        self,
        left_node: JsonVal,
        left_rendered: str,
        right_node: JsonVal,
        right_rendered: str,
        op_name: str,
        op_text: str,
    ) -> str:
        if len(self._op_prec_table) == 0:
            return "(" + left_rendered + " " + op_text + " " + right_rendered + ")"
        left = self._wrap_expr_for_precedence(left_rendered, left_node, op_name)
        right = self._wrap_expr_for_precedence(right_rendered, right_node, op_name, is_right=True)
        return left + " " + op_text + " " + right

    def _render_prefix_expr(
        self,
        operand_node: JsonVal,
        operand_rendered: str,
        op_name: str,
        op_text: str,
    ) -> str:
        if len(self._op_prec_table) == 0:
            return "(" + op_text + operand_rendered + ")"
        operand = self._wrap_expr_for_precedence(operand_rendered, operand_node, op_name, is_right=True)
        return op_text + operand

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

    def _boundary_target_name(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            return ""
        kind = self._str(node, "kind")
        if kind == "Unbox":
            target = self._str(node, "target")
            if target != "":
                return target
        return self._str(node, "resolved_type")

    def _normalize_boundary_expr(self, node: JsonVal) -> JsonVal:
        current = node
        while isinstance(current, dict):
            kind = self._str(current, "kind")
            if kind not in ("Box", "Unbox"):
                return current
            inner = current.get("value")
            if not isinstance(inner, dict) or self._str(inner, "kind") != kind:
                return current
            outer_target = self._boundary_target_name(current)
            inner_target = self._boundary_target_name(inner)
            if outer_target == "" or outer_target != inner_target:
                return current
            current = inner
        return current

    def _format_condition(self, rendered: str) -> str:
        return "(" + rendered + ")" if self._condition_parens() else rendered

    def _emit_stmt_line(self, text: str) -> None:
        term = self._stmt_terminator()
        if term != "" and not text.endswith(term):
            text = text + term
        self._emit(text)

    def emit_backend_line(self, text: str) -> None:
        self._emit(text)

    def _next_tmp(self, prefix: str) -> str:
        self.state.tmp_counter += 1
        return prefix + "_" + str(self.state.tmp_counter)

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

    def render_condition_expr(self, node: JsonVal) -> str:
        return self._format_condition(self.render_expr(node))

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        value = node.get("value")
        if isinstance(value, dict):
            self._emit_stmt_line(self._syntax_text("return", "return") + " " + self.render_expr(value))
        else:
            self._emit_stmt_line(self._syntax_text("return", "return"))

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit_stmt_line(self.render_expr(node.get("value")))

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit_stmt_line(self.render_assign_stmt(node))

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("common renderer requires raise override for " + self.language)

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        raise RuntimeError("common renderer requires except override for " + self.language)

    def emit_try_setup(self, node: dict[str, JsonVal]) -> None:
        return None

    def emit_try_teardown(self, node: dict[str, JsonVal]) -> None:
        return None

    def emit_try_handler_body(self, handler: dict[str, JsonVal]) -> None:
        self.emit_body(self._list(handler, "body"))

    def emit_exception_handler_prelude(self, handler: dict[str, JsonVal]) -> None:
        del handler
        return None

    def emit_exception_handler_teardown(self, handler: dict[str, JsonVal]) -> None:
        del handler
        return None

    def emit_exception_handler(self, handler: dict[str, JsonVal]) -> None:
        self.emit_exception_handler_prelude(handler)
        self.emit_try_handler_body(handler)
        self.emit_exception_handler_teardown(handler)

    def is_user_exception_handler(self, handler: dict[str, JsonVal]) -> bool:
        return False

    def is_catch_all_exception_handler(self, handler: dict[str, JsonVal]) -> bool:
        return False

    def iter_exception_match_type_names(self, handler: dict[str, JsonVal]) -> list[str]:
        type_node = handler.get("type")
        if isinstance(type_node, dict):
            type_name = self._str(type_node, "id")
            if type_name != "":
                return [type_name]
        return []

    def exception_handler_name(self, handler: dict[str, JsonVal]) -> str:
        return self._str(handler, "name")

    def exception_handler_body(self, handler: dict[str, JsonVal]) -> list[JsonVal]:
        return self._list(handler, "body")

    def exception_handler_type_name(self, handler: dict[str, JsonVal]) -> str:
        type_node = handler.get("type")
        if isinstance(type_node, dict):
            return self._str(type_node, "id")
        return ""

    def render_exception_match_condition(
        self,
        handler: dict[str, JsonVal],
        caught_type_expr: str,
    ) -> str:
        del handler, caught_type_expr
        return "true"

    def render_user_exception_handler_open(
        self,
        handler: dict[str, JsonVal],
        caught_expr: str,
        is_first: bool,
    ) -> str:
        del handler, caught_expr, is_first
        raise RuntimeError("common renderer requires user exception handler open override for " + self.language)

    def emit_string_exception_binding(self, caught_expr: str, target_name: str) -> None:
        del caught_expr, target_name
        return None

    def render_string_exception_handler_else_open(self) -> str:
        return "} else {"

    def render_string_exception_handler_else_close(self) -> str:
        return "}"

    def render_try_success_arm(self, ok_binding: str, returns_value: bool) -> str:
        del ok_binding, returns_value
        raise RuntimeError("common renderer requires try success arm override for " + self.language)

    def render_try_error_arm_open(self, err_binding: str, borrowed: bool = False) -> str:
        del err_binding, borrowed
        raise RuntimeError("common renderer requires try error arm hook for " + self.language)

    def render_try_error_arm_close(self) -> str:
        return "}"

    def render_try_match_open(self, result_name: str) -> str:
        del result_name
        raise RuntimeError("common renderer requires try match open hook for " + self.language)

    def render_try_match_close(self) -> str:
        raise RuntimeError("common renderer requires try match close hook for " + self.language)

    def emit_try_capture(self, result_name: str, body: list[JsonVal]) -> None:
        del result_name, body
        raise RuntimeError("common renderer requires try capture hook for " + self.language)

    def render_try_rethrow_fallback(self, result_name: str, err_binding: str) -> str:
        del result_name, err_binding
        raise RuntimeError("common renderer requires try rethrow fallback hook for " + self.language)

    def render_exception_dispatch_open(self, caught_type_expr: str) -> str:
        del caught_type_expr
        return ""

    def render_exception_dispatch_close(self) -> str:
        return "}"

    def emit_exception_dispatch_state_init(self, handled_name: str) -> None:
        del handled_name
        return None

    def render_exception_handler_guard_open(
        self,
        handler: dict[str, JsonVal],
        handled_name: str,
        caught_type_expr: str,
    ) -> str:
        del handler, handled_name, caught_type_expr
        raise RuntimeError("common renderer requires exception handler guard hook for " + self.language)

    def render_exception_handler_guard_close(self, handler: dict[str, JsonVal]) -> str:
        del handler
        return "}"

    def partition_exception_handlers(
        self,
        handlers: list[JsonVal],
    ) -> tuple[list[dict[str, JsonVal]], list[dict[str, JsonVal]]]:
        user_handlers: list[dict[str, JsonVal]] = []
        other_handlers: list[dict[str, JsonVal]] = []
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            if self.is_user_exception_handler(handler):
                user_handlers.append(handler)
            else:
                other_handlers.append(handler)
        return user_handlers, other_handlers

    def emit_exception_handler_mark_handled(self, handled_name: str) -> None:
        del handled_name
        return None

    def emit_exception_dispatch_handlers(
        self,
        caught_type_expr: str,
        handled_name: str,
        handlers: list[JsonVal],
    ) -> None:
        self.emit_backend_line(self.render_exception_dispatch_open(caught_type_expr))
        self.state.indent_level += 1
        self.emit_exception_dispatch_state_init(handled_name)
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            self.emit_backend_line(
                self.render_exception_handler_guard_open(handler, handled_name, caught_type_expr)
            )
            self.state.indent_level += 1
            self.emit_exception_handler_mark_handled(handled_name)
            self.emit_exception_handler(handler)
            self.state.indent_level -= 1
            self.emit_backend_line(self.render_exception_handler_guard_close(handler))
        self.state.indent_level -= 1
        self.emit_backend_line(self.render_exception_dispatch_close())

    def emit_user_exception_handler_chain(
        self,
        caught_expr: str,
        handlers: list[dict[str, JsonVal]],
    ) -> None:
        for index, handler in enumerate(handlers):
            self.emit_backend_line(self.render_user_exception_handler_open(handler, caught_expr, index == 0))
            self.state.indent_level += 1
            self.emit_exception_handler(handler)
            self.state.indent_level -= 1

    def emit_string_exception_handler_chain(
        self,
        caught_expr: str,
        bind_name: str,
        handlers: list[dict[str, JsonVal]],
    ) -> None:
        self.emit_string_exception_binding(caught_expr, bind_name)
        for handler in handlers:
            self.emit_exception_handler(handler)

    def emit_partitioned_exception_handlers(
        self,
        caught_expr: str,
        user_handlers: list[dict[str, JsonVal]],
        string_bind_name: str,
        string_handlers: list[dict[str, JsonVal]],
    ) -> None:
        if len(user_handlers) > 0:
            self.emit_user_exception_handler_chain(caught_expr, user_handlers)
            if len(string_handlers) > 0:
                self.emit_backend_line(self.render_string_exception_handler_else_open())
                self.state.indent_level += 1
                self.emit_string_exception_handler_chain(caught_expr, string_bind_name, string_handlers)
                self.state.indent_level -= 1
            self.emit_backend_line(self.render_string_exception_handler_else_close())
            return
        self.emit_string_exception_handler_chain(caught_expr, string_bind_name, string_handlers)

    def emit_try_body_post_stmt(self, stmt: dict[str, JsonVal], try_label: str) -> None:
        del stmt, try_label
        return None

    def render_try_body_open(self, try_label: str) -> str:
        del try_label
        return self._syntax_text("try", "try {")

    def render_try_body_close(self, try_label: str) -> str:
        del try_label
        return self._syntax_text("block_close", "}")

    def emit_bare_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        keyword = self._syntax_text("raise", "throw")
        self._emit_stmt_line(keyword)

    def emit_raise_call_stmt(
        self,
        node: dict[str, JsonVal],
        call_node: dict[str, JsonVal],
        func_name: str,
        args: list[JsonVal],
    ) -> None:
        self.emit_raise_value_stmt(node, call_node)

    def emit_raise_value_stmt(self, node: dict[str, JsonVal], value: JsonVal) -> None:
        rendered = self.render_raise_value(node)
        keyword = self._syntax_text("raise", "throw")
        if rendered != "":
            self._emit_stmt_line(keyword + " " + rendered)
        else:
            self._emit_stmt_line(keyword)

    def emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        exc = node.get("exc")
        if exc is None:
            self.emit_bare_raise_stmt(node)
            return
        if isinstance(exc, dict) and self._str(exc, "kind") == "Call":
            func = exc.get("func")
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                self.emit_raise_call_stmt(node, exc, self._str(func, "id"), self._list(exc, "args"))
                return
        self.emit_raise_value_stmt(node, exc)

    def emit_try_stmt(self, node: dict[str, JsonVal]) -> None:
        if len(self._list(node, "orelse")) > 0:
            raise RuntimeError("try/except/else is not supported in common renderer")
        body = self._list(node, "body")
        handlers = self._list(node, "handlers")
        finalbody = self._list(node, "finalbody")
        if len(handlers) == 0:
            self.emit_try_no_handler_stmt(node, body, finalbody)
            return
        self.emit_try_with_handlers_stmt(node, body, handlers, finalbody)

    def emit_try_no_handler_stmt(
        self,
        node: dict[str, JsonVal],
        body: list[JsonVal],
        finalbody: list[JsonVal],
    ) -> None:
        self.emit_try_setup(node)
        self.emit_body(body)
        if len(finalbody) > 0:
            self.emit_body(finalbody)
        self.emit_try_teardown(node)

    def emit_try_with_handlers_stmt(
        self,
        node: dict[str, JsonVal],
        body: list[JsonVal],
        handlers: list[JsonVal],
        finalbody: list[JsonVal],
    ) -> None:
        self.emit_try_setup(node)
        self._emit(self._syntax_text("try", "try {"))
        self.state.indent_level += 1
        self.emit_body(body)
        self.state.indent_level -= 1
        self._emit(self._syntax_text("block_close", "}"))
        for raw_handler in handlers:
            if not isinstance(raw_handler, dict):
                continue
            self._emit(self.render_except_open(raw_handler))
            self.state.indent_level += 1
            self.emit_try_handler_body(raw_handler)
            self.state.indent_level -= 1
            self._emit(self._syntax_text("block_close", "}"))
        if len(finalbody) > 0:
            self.emit_body(finalbody)
        self.emit_try_teardown(node)

    def _collect_with_hoisted_names(self, body: list[JsonVal]) -> list[dict[str, JsonVal]]:
        out: list[dict[str, JsonVal]] = []
        seen: set[str] = set()

        def add_name(name: str, resolved_type: str) -> None:
            if name == "" or name in seen:
                return
            seen.add(name)
            out.append(
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": name, "resolved_type": resolved_type},
                    "decl_type": resolved_type,
                    "value": None,
                    "declare": True,
                }
            )

        def walk(stmts: list[JsonVal]) -> None:
            for raw_stmt in stmts:
                if not isinstance(raw_stmt, dict):
                    continue
                kind = self._str(raw_stmt, "kind")
                if kind == "AnnAssign":
                    target = raw_stmt.get("target")
                    if isinstance(target, dict) and self._str(target, "kind") == "Name":
                        add_name(self._str(target, "id"), self._str(raw_stmt, "decl_type"))
                elif kind == "Assign":
                    target = raw_stmt.get("target")
                    if not isinstance(target, dict):
                        targets = self._list(raw_stmt, "targets")
                        if len(targets) > 0 and isinstance(targets[0], dict):
                            target = targets[0]
                    if isinstance(target, dict) and self._str(target, "kind") == "Name":
                        add_name(self._str(target, "id"), self._str(raw_stmt, "decl_type"))
                elif kind in ("If", "While", "Try", "With", "ForCore"):
                    walk(self._list(raw_stmt, "body"))
                    walk(self._list(raw_stmt, "orelse"))
                    walk(self._list(raw_stmt, "finalbody"))
                    for handler in self._list(raw_stmt, "handlers"):
                        if isinstance(handler, dict):
                            walk(self._list(handler, "body"))

        walk(body)
        return out

    def emit_with_stmt(self, node: dict[str, JsonVal]) -> None:
        body = self._list(node, "body")
        for hoisted in self._collect_with_hoisted_names(body):
            self.emit_assign_stmt(hoisted)
        ctx_name = self._next_tmp("__with_ctx")
        enter_name = self._str(node, "var_name")
        if enter_name == "":
            enter_name = self._next_tmp("__with_value")
        context_expr = node.get("context_expr")
        context_type = self._str(context_expr, "resolved_type") if isinstance(context_expr, dict) else ""
        context_kind = self._str(context_expr, "kind") if isinstance(context_expr, dict) else ""
        enter_type = self._str(node, "with_enter_type")
        self.emit_with_enter_prelude(node, enter_name, enter_type)
        ctx_assign = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": ctx_name, "resolved_type": context_type},
            "value": context_expr,
            "declare": True,
            "decl_type": context_type,
        }
        if context_kind in ("Name", "Attribute", "Subscript"):
            ctx_assign["bind_ref"] = True
        self.emit_assign_stmt(ctx_assign)
        enter_call = {
            "kind": "Call",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": ctx_name, "resolved_type": context_type},
                "attr": "__enter__",
                "resolved_type": "callable",
            },
            "args": [],
            "keywords": [],
            "resolved_type": enter_type,
        }
        if self._str(node, "with_enter_runtime_call") != "":
            enter_call["runtime_call"] = self._str(node, "with_enter_runtime_call")
            enter_call["resolved_runtime_call"] = self._str(node, "with_enter_runtime_call")
            enter_call["runtime_symbol"] = self._str(node, "with_enter_runtime_symbol")
            enter_call["runtime_module_id"] = self._str(node, "with_enter_runtime_module_id")
            enter_call["semantic_tag"] = self._str(node, "with_enter_semantic_tag")
        if context_type != "" and enter_type != "" and context_type == enter_type:
            self.emit_expr_stmt({"kind": "Expr", "value": enter_call})
        else:
            self.emit_assign_stmt(self.build_with_enter_assign(node, enter_name, enter_type, enter_call))
        exit_call = {
            "kind": "Call",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": ctx_name, "resolved_type": context_type},
                "attr": "__exit__",
                "resolved_type": "callable",
            },
            "args": [
                {"kind": "Constant", "value": None, "resolved_type": "None"},
                {"kind": "Constant", "value": None, "resolved_type": "None"},
                {"kind": "Constant", "value": None, "resolved_type": "None"},
            ],
            "keywords": [],
            "resolved_type": "None",
        }
        if self._str(node, "with_exit_runtime_call") != "":
            exit_call["runtime_call"] = self._str(node, "with_exit_runtime_call")
            exit_call["resolved_runtime_call"] = self._str(node, "with_exit_runtime_call")
            exit_call["runtime_symbol"] = self._str(node, "with_exit_runtime_symbol")
            exit_call["runtime_module_id"] = self._str(node, "with_exit_runtime_module_id")
            exit_call["semantic_tag"] = self._str(node, "with_exit_semantic_tag")
        try_body = body
        if context_type != "" and enter_type != "" and context_type == enter_type:
            try_body = [
                self.build_with_enter_assign(
                    node,
                    enter_name,
                    enter_type,
                    {"kind": "Name", "id": ctx_name, "resolved_type": context_type},
                    bind_ref=True,
                )
            ] + body
        try_node = {
            "kind": "Try",
            "body": try_body,
            "handlers": [],
            "orelse": [],
            "finalbody": [{"kind": "Expr", "value": exit_call}],
        }
        self.emit_try_stmt(try_node)

    def emit_with_enter_prelude(
        self,
        node: dict[str, JsonVal],
        enter_name: str,
        enter_type: str,
    ) -> None:
        return None

    def build_with_enter_assign(
        self,
        node: dict[str, JsonVal],
        enter_name: str,
        enter_type: str,
        value: JsonVal,
        bind_ref: bool = False,
    ) -> dict[str, JsonVal]:
        enter_assign: dict[str, JsonVal] = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": enter_name, "resolved_type": enter_type},
            "value": value,
            "declare": True,
            "decl_type": enter_type,
        }
        if bind_ref:
            enter_assign["bind_ref"] = True
        return enter_assign

    def emit_pass_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit("// pass")

    def emit_comment_stmt(self, node: dict[str, JsonVal]) -> None:
        text = self._str(node, "text")
        if text != "":
            self._emit("// " + text)

    def emit_blank_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit_blank()

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
        if isinstance(value, int):
            resolved_type = self._str(node, "resolved_type")
            if self._literal_can_omit_wrap(resolved_type, value):
                return str(value)
            return self._wrap_int_literal(resolved_type, value)
        return str(value)

    def render_binop(self, node: dict[str, JsonVal]) -> str:
        left = self.render_expr(node.get("left"))
        right = self.render_expr(node.get("right"))
        op_name = self._str(node, "op")
        op = self._operator_text("bin", op_name, self._str(node, "op"))
        return self._render_infix_expr(node.get("left"), left, node.get("right"), right, op_name, op)

    def render_unaryop(self, node: dict[str, JsonVal]) -> str:
        operand = self.render_expr(node.get("operand"))
        op_name = self._str(node, "op")
        op = self._operator_text("unary", op_name, self._str(node, "op"))
        return self._render_prefix_expr(node.get("operand"), operand, op_name, op)

    def render_compare(self, node: dict[str, JsonVal]) -> str:
        left = self.render_expr(node.get("left"))
        comparators = self._list(node, "comparators")
        ops = self._list(node, "ops")
        if len(comparators) == 0 or len(ops) == 0:
            return left
        if len(self._op_prec_table) == 0:
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
        parts: list[str] = []
        current_left = left
        current_left_node = node.get("left")
        for idx, comparator in enumerate(comparators):
            op_obj = ops[idx] if idx < len(ops) else None
            op_name = op_obj if isinstance(op_obj, str) else self._str(op_obj, "kind")
            op_text = self._operator_text("cmp", op_name, op_name)
            right = self.render_expr(comparator)
            left_part = self._wrap_expr_for_precedence(current_left, current_left_node, op_name)
            right_part = self._wrap_expr_for_precedence(right, comparator, op_name, is_right=True)
            parts.append(left_part + " " + op_text + " " + right_part)
            current_left = right
            current_left_node = comparator
        if len(parts) == 1:
            return parts[0]
        joiner = " " + self._operator_text("bool", "And", "&&") + " "
        return joiner.join(parts)

    def render_boolop(self, node: dict[str, JsonVal]) -> str:
        values = self._list(node, "values")
        op_text = self._operator_text("bool", self._str(node, "op"), self._str(node, "op"))
        if len(self._op_prec_table) == 0:
            return "(" + (" " + op_text + " ").join(self.render_expr(value) for value in values) + ")"
        op_name = self._str(node, "op")
        parts: list[str] = []
        for idx, value in enumerate(values):
            rendered = self.render_expr(value)
            parts.append(self._wrap_expr_for_precedence(rendered, value, op_name, is_right=idx > 0))
        return (" " + op_text + " ").join(parts)

    def render_expr(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            raise RuntimeError("common renderer expected dict expr node")
        node = self._normalize_boundary_expr(node)
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

    def _emit_if_chain(self, node: dict[str, JsonVal], *, is_elif: bool = False) -> None:
        test = self.render_condition_expr(node.get("test"))
        syntax_key = "elif" if is_elif else "if"
        default_open = "} else if ({cond}) {" if is_elif else "if ({cond}) {"
        self._emit(self._syntax_text(syntax_key, default_open).replace("{cond}", test))
        self.state.indent_level += 1
        self.emit_body(self._list(node, "body"))
        self.state.indent_level -= 1
        orelse = self._list(node, "orelse")
        if len(orelse) > 0:
            if len(orelse) == 1 and isinstance(orelse[0], dict) and self._str(orelse[0], "kind") == "If":
                self._emit_if_chain(orelse[0], is_elif=True)
                return
            self._emit(self._syntax_text("else", "} else {"))
            self.state.indent_level += 1
            self.emit_body(orelse)
            self.state.indent_level -= 1
        self._emit(self._syntax_text("block_close", "}"))

    def emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            return
        kind = self._str(node, "kind")
        if kind == "Expr":
            self.emit_expr_stmt(node)
            return
        if kind == "Return":
            self.emit_return_stmt(node)
            return
        if kind == "Assign" or kind == "AnnAssign":
            self.emit_assign_stmt(node)
            return
        if kind == "Pass":
            self.emit_pass_stmt(node)
            return
        if kind == "Raise":
            self.emit_raise_stmt(node)
            return
        if kind == "Try":
            self.emit_try_stmt(node)
            return
        if kind == "comment":
            self.emit_comment_stmt(node)
            return
        if kind == "blank":
            self.emit_blank_stmt(node)
            return
        if kind == "If":
            self._emit_if_chain(node)
            return
        if kind == "While":
            test = self.render_condition_expr(node.get("test"))
            self._emit(self._syntax_text("while", "while ({cond}) {").replace("{cond}", test))
            self.state.indent_level += 1
            self.emit_body(self._list(node, "body"))
            self.state.indent_level -= 1
            self._emit(self._syntax_text("block_close", "}"))
            return
        if kind == "With":
            self.emit_with_stmt(node)
            return
        self.emit_stmt_extension(node)

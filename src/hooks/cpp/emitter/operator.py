from __future__ import annotations

from pytra.std.typing import Any

from hooks.cpp.profile import BIN_OPS
from pytra.compiler.transpile_cli import join_str_list


class CppBinaryOperatorEmitter:
    """Binary operator renderers moved out from cpp_emitter for focused responsibility."""

    def _render_binop_expr(self, expr: dict[str, Any]) -> str:
        """BinOp ノードを C++ 式へ変換する。"""
        fallback = self._render_binop_expr_fallback(expr)
        if fallback is not None:
            return fallback
        return self._render_binop_expr_with_dunder(expr)

    def _render_binop_expr_fallback(self, expr: dict[str, Any]) -> str | None:
        """cast 除去/表層式変換だけを行う。失敗時は None を返す。"""
        if expr.get("left") is None or expr.get("right") is None:
            rep = self.any_to_str(expr.get("repr"))
            if rep != "":
                return rep
        return None

    def _apply_binop_cast_rules(
        self,
        expr: dict[str, Any],
    ) -> tuple[dict[str, Any], str, str]:
        """BinOp の cast 属性を左右に反映する。"""
        left_expr = expr.get("left")
        right_expr = expr.get("right")
        left_node = self.any_to_dict_or_empty(left_expr)
        right_node = self.any_to_dict_or_empty(right_expr)
        left = self.render_expr(left_expr)
        right = self.render_expr(right_expr)
        cast_rules = self._dict_stmt_list(expr.get("casts"))
        for cast_rule in cast_rules:
            on = self.any_to_str(cast_rule.get("on"))
            to_txt = self.any_to_str(cast_rule.get("to"))
            if on == "left":
                left = self.apply_cast(left, to_txt)
            elif on == "right":
                right = self.apply_cast(right, to_txt)
        return {"left_node": left_node, "right_node": right_node, "cast_rules": cast_rules}, left, right

    def _render_binop_dunder_call(
        self,
        expr: dict[str, Any],
        left: str,
        right: str,
        left_node: dict[str, Any],
    ) -> str:
        """`+`/`-`/`*`/`/`/`**` の dunder ベース分岐をまとめる。"""
        op_name = expr.get("op")
        op_name_str = str(op_name)
        dunder_by_binop: dict[str, str] = {
            "Add": "__add__",
            "Sub": "__sub__",
            "Mult": "__mul__",
            "Div": "__truediv__",
            "Pow": "__pow__",
        }
        dunder_name = dunder_by_binop.get(op_name_str, "")
        if dunder_name == "":
            return ""
        left_t0 = self.get_expr_type(expr.get("left"))
        left_t = left_t0 if isinstance(left_t0, str) else ""
        left_t_norm = self.normalize_type_name(left_t)
        if left_t_norm in {"", "unknown", "Any", "object"}:
            return ""
        method_sig = self._class_method_sig(left_t, dunder_name)
        if len(method_sig) == 0:
            return ""
        call_args = self._coerce_args_for_class_method(
            left_t,
            dunder_name,
            [right],
            [expr.get("right")],
        )
        owner = f"({left})"
        if left_t_norm in self.ref_classes and not left.strip().startswith("*"):
            return f"{owner}->{dunder_name}({join_str_list(', ', call_args)})"
        return f"{owner}.{dunder_name}({join_str_list(', ', call_args)})"

    def _render_binop_expr_with_dunder(self, expr: dict[str, Any]) -> str:
        """cast 適用 + dunder object receiver + fallback の総合レンダラ。"""
        binop_state, left, right = self._apply_binop_cast_rules(expr)
        left_node = binop_state["left_node"]
        cast_rules = binop_state["cast_rules"]

        dunder_rendered = self._render_binop_dunder_call(expr, left, right, left_node)
        if dunder_rendered != "":
            return dunder_rendered

        left_expr = expr.get("left")
        right_expr = expr.get("right")
        left = self._wrap_for_binop_operand(left, left_expr, str(expr.get("op")), False)
        right = self._wrap_for_binop_operand(right, right_expr, str(expr.get("op")), True)

        hook_binop_raw = self.hook_on_render_binop(expr, left, right)
        hook_binop_txt = ""
        if isinstance(hook_binop_raw, str):
            hook_binop_txt = str(hook_binop_raw)
        if hook_binop_txt != "":
            return hook_binop_txt

        return self._render_binop_operator(expr, left, right, cast_rules)

    def _render_binop_operator(
        self,
        expr: dict[str, Any],
        left: str,
        right: str,
        cast_rules: list[Any],
    ) -> str:
        """`op` 分岐を `emit_binary_op` の実体としてまとめる。"""
        op_name = str(expr.get("op"))
        if op_name == "Div":
            left_t_raw = self.get_expr_type(expr.get("left"))
            right_t_raw = self.get_expr_type(expr.get("right"))
            left_t = self.normalize_type_name(left_t_raw if isinstance(left_t_raw, str) else "")
            right_t = self.normalize_type_name(right_t_raw if isinstance(right_t_raw, str) else "")
            i = 0
            while i < len(cast_rules):
                cast_rule = self.any_to_dict_or_empty(cast_rules[i])
                on = self.any_to_str(cast_rule.get("on"))
                to_t = self.normalize_type_name(self.any_to_str(cast_rule.get("to")))
                if on == "left" and to_t != "":
                    left_t = to_t
                elif on == "right" and to_t != "":
                    right_t = to_t
                i += 1
            if left_t == "Path" and right_t in {"str", "Path"}:
                return f"{left} / {right}"
            if left_t in {"float32", "float64"} and right_t in {"float32", "float64"}:
                return f"{left} / {right}"
            return f"py_div({left}, {right})"
        if op_name == "Pow":
            return f"::std::pow(py_to_float64({left}), py_to_float64({right}))"
        if op_name == "FloorDiv":
            if self.floor_div_mode == "python":
                return f"py_floordiv({left}, {right})"
            return f"{left} / {right}"
        if op_name == "Mod":
            if self.mod_mode == "python":
                return f"py_mod({left}, {right})"
            left_t0 = self.get_expr_type(expr.get("left"))
            right_t0 = self.get_expr_type(expr.get("right"))
            left_t = left_t0 if isinstance(left_t0, str) else ""
            right_t = right_t0 if isinstance(right_t0, str) else ""
            int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
            if left_t not in int_types or right_t not in int_types:
                return f"py_mod({left}, {right})"
            return f"{left} % {right}"
        if op_name == "Mult":
            left_t0 = self.get_expr_type(expr.get("left"))
            right_t0 = self.get_expr_type(expr.get("right"))
            left_t = left_t0 if isinstance(left_t0, str) else ""
            right_t = right_t0 if isinstance(right_t0, str) else ""
            list_model = self.any_to_str(getattr(self, "cpp_list_model", "value"))
            if left_t.startswith("list[") and right_t in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                list_expr = left
                left_node = self.any_to_dict_or_empty(expr.get("left"))
                if list_model == "pyobj" and not self._expr_is_stack_list_local(left_node):
                    list_cpp_t = self._cpp_list_value_model_type_text(left_t)
                    list_expr = f"{list_cpp_t}({left})"
                return f"py_repeat({list_expr}, {right})"
            if right_t.startswith("list[") and left_t in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                list_expr = right
                right_node = self.any_to_dict_or_empty(expr.get("right"))
                if list_model == "pyobj" and not self._expr_is_stack_list_local(right_node):
                    list_cpp_t = self._cpp_list_value_model_type_text(right_t)
                    list_expr = f"{list_cpp_t}({right})"
                return f"py_repeat({list_expr}, {left})"
            if left_t == "str" and right_t in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({left}, {right})"
            if right_t == "str" and left_t in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({right}, {left})"

        op_txt = str(BIN_OPS.get(op_name, ""))
        if op_txt != "":
            return f"{left} {op_txt} {right}"
        return f"{left} {op_name} {right}"

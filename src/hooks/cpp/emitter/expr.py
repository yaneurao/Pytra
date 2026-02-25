from __future__ import annotations

from pytra.std.typing import Any


class CppExpressionEmitter:
    """Expression rendering helpers extracted from :class:`CppEmitter`."""

    def apply_cast(self, rendered_expr: str, to_type: str) -> str:
        """EAST の cast 指示に従い C++ 側の明示キャストを適用する。"""
        to_type_text = to_type if isinstance(to_type, str) else ""
        if to_type_text == "byte":
            to_type_text = "uint8"
        if to_type_text == "":
            return rendered_expr
        norm_t = self.normalize_type_name(to_type_text)
        if norm_t in {"float32", "float64"}:
            return f"py_to<float64>({rendered_expr})"
        if norm_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return f"{norm_t}(py_to<int64>({rendered_expr}))"
        if norm_t == "bool":
            return f"py_to<bool>({rendered_expr})"
        if norm_t == "str":
            return f"py_to_string({rendered_expr})"
        cast_cpp = self._cpp_type_text(norm_t)
        if cast_cpp in {"", "auto"}:
            return rendered_expr
        return f"static_cast<{cast_cpp}>({rendered_expr})"

    def render_to_string(self, expr: Any) -> str:
        """式を文字列化する（型に応じて最適な変換関数を選ぶ）。"""
        rendered = self.render_expr(expr)
        t0 = self.get_expr_type(expr)
        t = t0 if isinstance(t0, str) else ""
        if t == "str":
            return rendered
        if t == "bool":
            return f"py_bool_to_string({rendered})"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64"}:
            return f"::std::to_string({rendered})"
        return f"py_to_string({rendered})"

    def render_expr_as_any(self, expr: Any) -> str:
        """式を `object`（Any 相当）へ昇格する式文字列を返す。"""
        rendered = self.render_expr(expr)
        return self._box_expr_for_any(rendered, expr)

    def render_boolop(self, expr: Any, force_value_select: bool = False) -> str:
        """BoolOp を真偽演算または値選択式として出力する。"""
        expr_dict = self.any_to_dict_or_empty(expr)
        if len(expr_dict) == 0:
            return "false"
        raw_values = self.any_to_list(expr_dict.get("values"))
        value_nodes: list[Any] = []
        for v in raw_values:
            if isinstance(v, dict):
                value_nodes.append(v)
        if len(value_nodes) == 0:
            return "false"
        value_texts = [self.render_expr(v) for v in value_nodes]
        if not force_value_select and self.get_expr_type(expr) == "bool":
            return self.render_boolop_chain_common(
                value_nodes,
                self.any_dict_get_str(expr_dict, "op", ""),
                and_token="&&",
                or_token="||",
                empty_literal="false",
                wrap_each=True,
                wrap_whole=False,
            )

        op_name = self.any_dict_get_str(expr_dict, "op", "")
        out = value_texts[-1]
        prev_nodes = value_nodes[:-1]
        prev_texts = value_texts[:-1]
        for value_node, cur in zip(reversed(prev_nodes), reversed(prev_texts)):
            cond = self.render_cond(value_node)
            out = f"({cond} ? {out} : {cur})" if op_name == "And" else f"({cond} ? {cur} : {out})"
        return out

    def render_cond(self, expr: Any) -> str:
        """条件式文脈向けに式を真偽値へ正規化して出力する。"""
        expr_node = self.any_to_dict_or_empty(expr)
        if len(expr_node) == 0:
            return "false"
        t = self.get_expr_type(expr)
        body_raw = self.render_expr(expr)
        body = self._strip_outer_parens(body_raw)
        if body == "":
            rep_txt = self.any_dict_get_str(expr_node, "repr", "")
            body = self._strip_outer_parens(self._trim_ws(rep_txt))
        if body != "" and self._looks_like_python_expr_text(body):
            body_cpp = self._render_repr_expr(body)
            if body_cpp != "":
                body = self._strip_outer_parens(body_cpp)
        if body == "":
            return "false"
        if t == "bool":
            return body
        if self.is_any_like_type(t):
            return self.render_expr(
                {
                    "kind": "ObjBool",
                    "value": expr_node,
                    "resolved_type": "bool",
                    "borrow_kind": "value",
                    "casts": [],
                }
            )
        if t == "str" or t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return self.truthy_len_expr(body)
        return body

    def _str_index_char_access(self, node: Any) -> str:
        """str 添字アクセスを `at()` ベースの char 比較式へ変換する。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0 or self._node_kind_from_dict(nd) != "Subscript":
            return ""
        value_node: Any = nd.get("value")
        if self.get_expr_type(value_node) != "str":
            return ""
        sl: Any = nd.get("slice")
        sl_node = self.any_to_dict_or_empty(sl)
        if len(sl_node) > 0 and self._node_kind_from_dict(sl_node) == "Slice":
            return ""
        if self.negative_index_mode != "off" and self._is_negative_const_index(sl):
            return ""
        base = self.render_expr(value_node)
        base_node = self.any_to_dict_or_empty(value_node)
        if len(base_node) > 0 and self._node_kind_from_dict(base_node) in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            base = f"({base})"
        idx = self.render_expr(sl)
        return f"{base}.at({idx})"

    def render_minmax(self, fn: str, args: list[str], out_type: str, arg_nodes: list[Any]) -> str:
        """min/max 呼び出しを型情報付きで C++ 式へ変換する。"""
        if len(args) == 0:
            return "/* invalid min/max */"
        if len(args) == 1:
            return args[0]
        t = "auto"
        if out_type != "":
            t = self._cpp_type_text(out_type)
        arg_nodes_safe: list[Any] = arg_nodes
        if t in {"auto", "object"}:
            saw_float = False
            saw_int = False
            for node in arg_nodes_safe:
                at0 = self.get_expr_type(node)
                at = at0 if isinstance(at0, str) else ""
                if at in {"float32", "float64"}:
                    saw_float = True
                elif at in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                    saw_int = True
            if saw_float:
                t = "float64"
            elif saw_int:
                t = "int64"
        if t == "auto":
            call = f"py_{fn}({args[0]}, {args[1]})"
            for a in args[2:]:
                call = f"py_{fn}({call}, {a})"
            return call
        casted: list[str] = []
        for i, a in enumerate(args):
            n: Any = arg_nodes_safe[i] if i < len(arg_nodes_safe) else {}
            at0 = self.get_expr_type(n)
            at = at0 if isinstance(at0, str) else ""
            if self.is_any_like_type(at):
                casted.append(self.apply_cast(a, t))
            else:
                casted.append(f"static_cast<{t}>({a})")
        call = f"::std::{fn}<{t}>({casted[0]}, {casted[1]})"
        for a in casted[2:]:
            call = f"::std::{fn}<{t}>({call}, {a})"
        return call

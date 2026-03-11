#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for precedence parsing."""

from __future__ import annotations

from typing import Any

from toolchain.ir.core_numeric_types import INT_TYPES
from toolchain.ir.core_ast_builders import _sh_make_arg_node
from toolchain.ir.core_ast_builders import _sh_make_boolop_expr
from toolchain.ir.core_ast_builders import _sh_make_compare_expr
from toolchain.ir.core_ast_builders import _sh_make_ifexp_expr
from toolchain.ir.core_ast_builders import _sh_make_lambda_arg_entry
from toolchain.ir.core_ast_builders import _sh_make_lambda_expr
from toolchain.ir.core_ast_builders import _sh_make_unaryop_expr


class _ShExprPrecedenceParserMixin:
    def _parse_lambda(self) -> dict[str, Any]:
        """lambda 式を解析する。lambda でなければ次順位へ委譲する。"""
        tok = self._cur()
        if not (tok["k"] == "NAME" and tok["v"] == "lambda"):
            return self._parse_or()
        lam_tok = self._eat("NAME")
        arg_entries: list[dict[str, Any]] = []
        seen_default = False
        while self._cur()["k"] != ":":
            if self._cur()["k"] == ",":
                self._eat(",")
                continue
            if self._cur()["k"] == "NAME":
                nm = str(self._eat("NAME")["v"])
                default_expr: dict[str, Any] | None = None
                if self._cur()["k"] == "=":
                    self._eat("=")
                    default_expr = self._parse_ifexp()
                    seen_default = True
                elif seen_default:
                    cur = self._cur()
                    raise self._raise_expr_build_error(
                        kind="unsupported_syntax",
                        message="lambda non-default parameter follows default parameter",
                        source_span=self._node_span(cur["s"], cur["e"]),
                        hint="Reorder lambda parameters so defaulted ones come last.",
                    )
                param_t = "unknown"
                if isinstance(default_expr, dict):
                    default_t = str(default_expr.get("resolved_type", "unknown"))
                    if default_t != "":
                        param_t = default_t
                arg_entries.append(_sh_make_lambda_arg_entry(nm, default_expr, param_t))
                continue
            cur = self._cur()
            raise self._raise_expr_build_error(
                kind="unsupported_syntax",
                message=f"unsupported lambda parameter token: {cur['k']}",
                source_span=self._node_span(cur["s"], cur["e"]),
                hint="Use `lambda x, y=default: expr` form (annotations are not supported).",
            )
        self._eat(":")
        bak: dict[str, str] = {}
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            bak[nm] = self.name_types.get(nm, "")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            self.name_types[nm] = param_t
        body = self._parse_ifexp()
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            if nm == "":
                continue
            old = bak.get(nm, "")
            if old == "":
                self.name_types.pop(nm, None)
            else:
                self.name_types[nm] = old
        s = lam_tok["s"]
        e = int(body["source_span"]["end_col"]) - self.col_base
        body_t = str(body.get("resolved_type", "unknown"))
        ret_t = body_t if body_t != "" else "unknown"
        param_types: list[str] = []
        for ent in arg_entries:
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            param_types.append(param_t)
        params = ",".join(param_types)
        callable_t = f"callable[{params}->{ret_t}]"
        args: list[dict[str, Any]] = []
        for ent in arg_entries:
            nm = str(ent.get("name", ""))
            default_expr = ent.get("default")
            param_t = str(ent.get("resolved_type", "unknown"))
            if param_t == "":
                param_t = "unknown"
            args.append(
                _sh_make_arg_node(
                    nm,
                    annotation=None,
                    resolved_type=param_t,
                    default=default_expr if isinstance(default_expr, dict) else None,
                )
            )
        return _sh_make_lambda_expr(
            self._node_span(s, e),
            args,
            body,
            return_type=ret_t,
            resolved_type=callable_t,
            repr_text=self._src_slice(s, e),
        )

    def _parse_ifexp(self) -> dict[str, Any]:
        """条件式 `a if cond else b` を解析する。"""
        body = self._parse_lambda()
        if self._cur()["k"] == "NAME" and self._cur()["v"] == "if":
            self._eat("NAME")
            test = self._parse_lambda()
            else_tok = self._eat("NAME")
            if else_tok["v"] != "else":
                raise self._raise_expr_build_error(
                    kind="unsupported_syntax",
                    message="expected 'else' in conditional expression",
                    source_span=self._node_span(else_tok["s"], else_tok["e"]),
                    hint="Use `a if cond else b` syntax.",
                )
            orelse = self._parse_ifexp()
            s = int(body["source_span"]["col"]) - self.col_base
            e = int(orelse["source_span"]["end_col"]) - self.col_base
            return _sh_make_ifexp_expr(
                self._node_span(s, e),
                test,
                body,
                orelse,
                repr_text=self._src_slice(s, e),
            )
        return body

    def _parse_or(self) -> dict[str, Any]:
        """論理和（or）式を解析する。"""
        node = self._parse_and()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "or":
            self._eat("NAME")
            values.append(self._parse_and())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_boolop_expr(self._node_span(s, e), "Or", values, repr_text=self._src_slice(s, e))

    def _parse_and(self) -> dict[str, Any]:
        """論理積（and）式を解析する。"""
        node = self._parse_not()
        values = [node]
        while self._cur()["k"] == "NAME" and self._cur()["v"] == "and":
            self._eat("NAME")
            values.append(self._parse_not())
        if len(values) == 1:
            return node
        s = int(values[0]["source_span"]["col"]) - self.col_base
        e = int(values[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_boolop_expr(self._node_span(s, e), "And", values, repr_text=self._src_slice(s, e))

    def _parse_not(self) -> dict[str, Any]:
        """単項 not を解析する。"""
        tok = self._cur()
        if tok["k"] == "NAME" and tok["v"] == "not":
            self._eat("NAME")
            operand = self._parse_not()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            return _sh_make_unaryop_expr(
                self._node_span(s, e),
                "Not",
                operand,
                resolved_type="bool",
                repr_text=self._src_slice(s, e),
            )
        return self._parse_compare()

    def _parse_compare(self) -> dict[str, Any]:
        """比較演算（連鎖比較含む）を解析する。"""
        node = self._parse_bitor()
        cmp_map = {"<": "Lt", "<=": "LtE", ">": "Gt", ">=": "GtE", "==": "Eq", "!=": "NotEq"}
        ops: list[str] = []
        comparators: list[dict[str, Any]] = []
        while True:
            if self._cur()["k"] in cmp_map:
                tok = self._eat()
                ops.append(cmp_map[tok["k"]])
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                self._eat("NAME")
                ops.append("In")
                comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "is":
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                    self._eat("NAME")
                    ops.append("IsNot")
                    comparators.append(self._parse_bitor())
                else:
                    ops.append("Is")
                    comparators.append(self._parse_bitor())
                continue
            if self._cur()["k"] == "NAME" and self._cur()["v"] == "not":
                pos = self.pos
                self._eat("NAME")
                if self._cur()["k"] == "NAME" and self._cur()["v"] == "in":
                    self._eat("NAME")
                    ops.append("NotIn")
                    comparators.append(self._parse_bitor())
                    continue
                self.pos = pos
            break
        if len(ops) == 0:
            return node
        start_col = int(node["source_span"]["col"]) - self.col_base
        end_col = int(comparators[-1]["source_span"]["end_col"]) - self.col_base
        return _sh_make_compare_expr(
            self._node_span(start_col, end_col),
            node,
            ops,
            comparators,
            repr_text=self._src_slice(start_col, end_col),
        )

    def _parse_bitor(self) -> dict[str, Any]:
        """ビット OR を解析する。"""
        node = self._parse_bitxor()
        while self._cur()["k"] == "|":
            op_tok = self._eat()
            right = self._parse_bitxor()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitxor(self) -> dict[str, Any]:
        """ビット XOR を解析する。"""
        node = self._parse_bitand()
        while self._cur()["k"] == "^":
            op_tok = self._eat()
            right = self._parse_bitand()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_bitand(self) -> dict[str, Any]:
        """ビット AND を解析する。"""
        node = self._parse_shift()
        while self._cur()["k"] == "&":
            op_tok = self._eat()
            right = self._parse_shift()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_shift(self) -> dict[str, Any]:
        """シフト演算を解析する。"""
        node = self._parse_addsub()
        while self._cur()["k"] in {"<<", ">>"}:
            op_tok = self._eat()
            right = self._parse_addsub()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_addsub(self) -> dict[str, Any]:
        """加減算を解析する。"""
        node = self._parse_muldiv()
        while self._cur()["k"] in {"+", "-"}:
            op_tok = self._eat()
            right = self._parse_muldiv()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_muldiv(self) -> dict[str, Any]:
        """乗除算（`* / // %`）を解析する。"""
        node = self._parse_unary()
        while self._cur()["k"] in {"*", "/", "//", "%"}:
            op_tok = self._eat()
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_power(self) -> dict[str, Any]:
        """べき乗（`**`）を右結合で解析する。"""
        node = self._parse_postfix()
        if self._cur()["k"] == "**":
            op_tok = self._eat("**")
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_unary(self) -> dict[str, Any]:
        """単項演算（`+` / `-` / `~`）を解析する。"""
        if self._cur()["k"] in {"+", "-", "~"}:
            tok = self._eat()
            operand = self._parse_unary()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            operand_t = str(operand.get("resolved_type", "unknown"))
            out_t = operand_t
            op_name = "USub" if tok["k"] == "-" else "UAdd"
            if tok["k"] == "~":
                op_name = "Invert"
                if operand_t in INT_TYPES or operand_t == "bool":
                    out_t = "int64"
                else:
                    invert_ret = self._lookup_method_return(operand_t, "__invert__")
                    if invert_ret != "unknown":
                        out_t = invert_ret
                    elif operand_t in {"", "unknown"}:
                        out_t = "unknown"
            return _sh_make_unaryop_expr(
                self._node_span(s, e),
                op_name,
                operand,
                resolved_type=out_t if tok["k"] == "~" else (out_t if out_t in {"int64", "float64"} else "unknown"),
                repr_text=self._src_slice(s, e),
            )
        return self._parse_power()

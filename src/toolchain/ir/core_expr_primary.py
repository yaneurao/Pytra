#!/usr/bin/env python3
"""Self-hosted EAST expression parser helpers for primary expressions."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.signature_registry import is_stdlib_path_type
from toolchain.ir.core_ast_builders import _sh_make_binop_expr
from toolchain.ir.core_ast_builders import _sh_make_cast_entry
from toolchain.ir.core_ast_builders import _sh_make_constant_expr
from toolchain.ir.core_ast_builders import _sh_make_dict_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_dict_expr
from toolchain.ir.core_ast_builders import _sh_make_formatted_value_node
from toolchain.ir.core_ast_builders import _sh_make_joined_str_expr
from toolchain.ir.core_ast_builders import _sh_make_list_comp_expr
from toolchain.ir.core_ast_builders import _sh_make_list_expr
from toolchain.ir.core_ast_builders import _sh_make_range_expr
from toolchain.ir.core_ast_builders import _sh_make_set_expr
from toolchain.ir.core_builder_base import _sh_make_name_expr
from toolchain.ir.core_builder_base import _sh_make_tuple_expr
from toolchain.ir.core_entrypoints import _make_east_build_error
from toolchain.ir.core_stmt_text_semantics import _sh_find_top_char
from toolchain.ir.core_string_semantics import _sh_append_fstring_literal
from toolchain.ir.core_string_semantics import _sh_decode_py_string_body

INT_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
}
FLOAT_TYPES = {"float32", "float64"}


def _reparse_expr_with_context(parser: Any, expr_text: str, *, col_base: int) -> dict[str, Any]:
    """Re-enter `_sh_parse_expr` using the current parser environment."""
    from toolchain.ir.core_expr_shell import _sh_parse_expr

    return _sh_parse_expr(
        expr_text,
        line_no=parser.line_no,
        col_base=col_base,
        name_types=parser.name_types,
        fn_return_types=parser.fn_return_types,
        class_method_return_types=parser.class_method_return_types,
        class_base=parser.class_base,
    )


def _make_bin_impl(parser: Any, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
    """Build a binary op node, adding numeric-promotion casts when needed."""
    op_map = {
        "+": "Add",
        "-": "Sub",
        "*": "Mult",
        "**": "Pow",
        "/": "Div",
        "//": "FloorDiv",
        "%": "Mod",
        "&": "BitAnd",
        "|": "BitOr",
        "^": "BitXor",
        "<<": "LShift",
        ">>": "RShift",
    }
    lt = str(left.get("resolved_type", "unknown"))
    rt = str(right.get("resolved_type", "unknown"))
    casts: list[dict[str, Any]] = []
    if op_sym == "/":
        if is_stdlib_path_type(lt) and (rt == "str" or is_stdlib_path_type(rt)):
            out_t = "Path"
        elif (lt in INT_TYPES or lt in FLOAT_TYPES) and (rt in INT_TYPES or rt in FLOAT_TYPES):
            out_t = "float64"
            if lt in INT_TYPES:
                casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
            if rt in INT_TYPES:
                casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
        else:
            out_t = "unknown"
    elif op_sym == "//":
        out_t = "int64" if lt in {"int64", "unknown"} and rt in {"int64", "unknown"} else "float64"
    elif op_sym == "+" and (
        (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) or (lt == "str" and rt == "str")
    ):
        out_t = "bytes" if (lt in {"bytes", "bytearray"} and rt in {"bytes", "bytearray"}) else "str"
    elif op_sym == "**" and lt in {"int64", "float64"} and rt in {"int64", "float64"}:
        out_t = "float64"
        if lt == "int64":
            casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
        if rt == "int64":
            casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
    elif lt == rt and lt in {"int64", "float64"}:
        out_t = lt
    elif lt in {"int64", "float64"} and rt in {"int64", "float64"}:
        out_t = "float64"
        if lt == "int64":
            casts.append(_sh_make_cast_entry("left", "int64", "float64", "numeric_promotion"))
        if rt == "int64":
            casts.append(_sh_make_cast_entry("right", "int64", "float64", "numeric_promotion"))
    elif op_sym in {"&", "|", "^", "<<", ">>"} and lt == "int64" and rt == "int64":
        out_t = "int64"
    else:
        out_t = "unknown"

    ls = int(left["source_span"]["col"]) - parser.col_base
    rs = int(right["source_span"]["end_col"]) - parser.col_base
    return _sh_make_binop_expr(
        parser._node_span(ls, rs),
        left,
        op_map[op_sym],
        right,
        resolved_type=out_t,
        casts=casts,
        repr_text=parser._src_slice(ls, rs),
    )


def _parse_primary_impl(parser: Any) -> dict[str, Any]:
    """Parse literal/name/grouping/list/dict/set primary expressions."""
    tok = parser._cur()
    if tok["k"] == "INT":
        parser._eat("INT")
        tok_v: str = str(tok["v"])
        if tok_v.startswith("0x") or tok_v.startswith("0X"):
            tok_value = int(tok_v[2:], 16)
        elif tok_v.startswith("0b") or tok_v.startswith("0B"):
            tok_value = int(tok_v[2:], 2)
        elif tok_v.startswith("0o") or tok_v.startswith("0O"):
            tok_value = int(tok_v[2:], 8)
        else:
            tok_value = int(tok_v)
        return _sh_make_constant_expr(
            parser._node_span(tok["s"], tok["e"]),
            tok_value,
            resolved_type="int64",
            repr_text=str(tok["v"]),
        )
    if tok["k"] == "FLOAT":
        parser._eat("FLOAT")
        return _sh_make_constant_expr(
            parser._node_span(tok["s"], tok["e"]),
            float(tok["v"]),
            resolved_type="float64",
            repr_text=str(tok["v"]),
        )
    if tok["k"] == "STR":
        str_parts: list[dict[str, Any]] = [parser._eat("STR")]
        while parser._cur()["k"] == "STR":
            str_parts.append(parser._eat("STR"))
        if len(str_parts) > 1:
            str_nodes = [
                _reparse_expr_with_context(parser, part["v"], col_base=parser.col_base + int(part["s"]))
                for part in str_parts
            ]
            node = str_nodes[0]
            for str_rhs in str_nodes[1:]:
                node = _sh_make_binop_expr(
                    parser._node_span(str_parts[0]["s"], str_parts[-1]["e"]),
                    node,
                    "Add",
                    str_rhs,
                    resolved_type="str",
                    repr_text=parser._src_slice(str_parts[0]["s"], str_parts[-1]["e"]),
                )
            return node

        tok = str_parts[0]
        raw: str = tok["v"]
        p = 0
        while p < len(raw) and raw[p] in "rRbBuUfF":
            p += 1
        prefix = raw[:p].lower()
        if p >= len(raw):
            p = 0

        is_triple = p + 2 < len(raw) and raw[p : p + 3] in {"'''", '"""'}
        if is_triple:
            body = raw[p + 3 : -3]
        else:
            body = raw[p + 1 : -1]

        if "f" in prefix:
            values: list[dict[str, Any]] = []
            is_raw = "r" in prefix

            i = 0
            while i < len(body):
                j = body.find("{", i)
                if j < 0:
                    _sh_append_fstring_literal(values, body[i:], parser._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                    break
                if j + 1 < len(body) and body[j + 1] == "{":
                    _sh_append_fstring_literal(
                        values,
                        body[i : j + 1],
                        parser._node_span(tok["s"], tok["e"]),
                        raw_mode=is_raw,
                    )
                    i = j + 2
                    continue
                if j > i:
                    _sh_append_fstring_literal(values, body[i:j], parser._node_span(tok["s"], tok["e"]), raw_mode=is_raw)
                k = body.find("}", j + 1)
                if k < 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="unterminated f-string placeholder in self_hosted parser",
                        source_span=parser._node_span(tok["s"], tok["e"]),
                        hint="Close f-string placeholder with `}`.",
                    )
                inner_expr = body[j + 1 : k].strip()
                expr_txt = inner_expr
                conv_txt = ""
                fmt_txt = ""
                conv_pos = _sh_find_top_char(inner_expr, "!")
                fmt_pos = _sh_find_top_char(inner_expr, ":")
                if conv_pos >= 0 and (fmt_pos < 0 or conv_pos < fmt_pos):
                    expr_txt = inner_expr[:conv_pos].strip()
                    conv_tail_end = fmt_pos if fmt_pos >= 0 else len(inner_expr)
                    conv_txt = inner_expr[conv_pos + 1 : conv_tail_end].strip()
                    if fmt_pos >= 0:
                        fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                elif fmt_pos >= 0:
                    expr_txt = inner_expr[:fmt_pos].strip()
                    fmt_txt = inner_expr[fmt_pos + 1 :].strip()
                if expr_txt == "":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="empty f-string placeholder expression in self_hosted parser",
                        source_span=parser._node_span(tok["s"], tok["e"]),
                        hint="Use `{expr}` form inside f-string placeholders.",
                    )
                values.append(
                    _sh_make_formatted_value_node(
                        _reparse_expr_with_context(
                            parser,
                            expr_txt,
                            col_base=parser.col_base + tok["s"] + j + 1,
                        ),
                        conversion=conv_txt,
                        format_spec=fmt_txt,
                    )
                )
                i = k + 1
            return _sh_make_joined_str_expr(parser._node_span(tok["s"], tok["e"]), values, repr_text=raw)
        resolved_type = "str"
        if "b" in prefix and "f" not in prefix:
            resolved_type = "bytes"
        body = _sh_decode_py_string_body(body, "r" in prefix)
        return _sh_make_constant_expr(
            parser._node_span(tok["s"], tok["e"]),
            body,
            resolved_type=resolved_type,
            repr_text=raw,
        )
    if tok["k"] == "NAME":
        name_tok = parser._eat("NAME")
        nm = str(name_tok["v"])
        if nm in {"True", "False"}:
            return _sh_make_constant_expr(
                parser._node_span(name_tok["s"], name_tok["e"]),
                nm == "True",
                resolved_type="bool",
                repr_text=nm,
            )
        if nm == "None":
            return _sh_make_constant_expr(
                parser._node_span(name_tok["s"], name_tok["e"]),
                None,
                resolved_type="None",
                repr_text=nm,
            )
        t = parser.name_types.get(nm, "unknown")
        return _sh_make_name_expr(
            parser._node_span(name_tok["s"], name_tok["e"]),
            nm,
            resolved_type=t,
            borrow_kind="readonly_ref" if t != "unknown" else "value",
        )
    if tok["k"] == "(":
        l = parser._eat("(")
        if parser._cur()["k"] == ")":
            r = parser._eat(")")
            return _sh_make_tuple_expr(
                parser._node_span(l["s"], r["e"]),
                [],
                resolved_type="tuple[]",
                repr_text=parser._src_slice(l["s"], r["e"]),
            )
        first = parser._parse_ifexp()
        if parser._cur()["k"] == "NAME" and parser._cur()["v"] == "for":
            parser._eat("NAME")
            target = parser._parse_comp_target()
            in_tok = parser._eat("NAME")
            if in_tok["v"] != "in":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="expected 'in' in generator expression",
                    source_span=parser._node_span(in_tok["s"], in_tok["e"]),
                    hint="Use `(expr for x in iterable)` syntax.",
                )
            iter_expr = parser._parse_or()
            ifs: list[dict[str, Any]] = []
            while parser._cur()["k"] == "NAME" and parser._cur()["v"] == "if":
                parser._eat("NAME")
                ifs.append(parser._parse_or())
            r = parser._eat(")")
            return _sh_make_list_comp_expr(
                parser._node_span(l["s"], r["e"]),
                first,
                [_sh_make_comp_generator(target, iter_expr, ifs)],
                repr_text=parser._src_slice(l["s"], r["e"]),
                lowered_kind="GeneratorArg",
            )
        if parser._cur()["k"] == ",":
            elements = [first]
            while parser._cur()["k"] == ",":
                parser._eat(",")
                if parser._cur()["k"] == ")":
                    break
                elements.append(parser._parse_ifexp())
            r = parser._eat(")")
            return _sh_make_tuple_expr(
                parser._node_span(l["s"], r["e"]),
                elements,
                repr_text=parser._src_slice(l["s"], r["e"]),
            )
        r = parser._eat(")")
        first["source_span"] = parser._node_span(l["s"], r["e"])
        first["repr"] = parser._src_slice(l["s"], r["e"])
        return first
    if tok["k"] == "[":
        l = parser._eat("[")
        elements: list[dict[str, Any]] = []
        if parser._cur()["k"] != "]":
            first = parser._parse_ifexp()
            if parser._cur()["k"] == "NAME" and parser._cur()["v"] == "for":
                parser._eat("NAME")
                target = parser._parse_comp_target()
                in_tok = parser._eat("NAME")
                if in_tok["v"] != "in":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="expected 'in' in list comprehension",
                        source_span=parser._node_span(in_tok["s"], in_tok["e"]),
                        hint="Use `[x for x in iterable]` syntax.",
                    )
                iter_expr = parser._parse_or()
                if (
                    isinstance(iter_expr, dict)
                    and iter_expr.get("kind") == "Call"
                    and isinstance(iter_expr.get("func"), dict)
                    and iter_expr.get("func", {}).get("kind") == "Name"
                    and iter_expr.get("func", {}).get("id") == "range"
                ):
                    rargs = list(iter_expr.get("args", []))
                    range_target_span = parser._node_span(parser.col_base, parser.col_base)
                    if isinstance(target, dict):
                        target_span_obj = target.get("source_span")
                        if isinstance(target_span_obj, dict):
                            ts = target_span_obj.get("col")
                            te = target_span_obj.get("end_col")
                        else:
                            ts = None
                            te = None
                        if isinstance(ts, int) and isinstance(te, int):
                            range_target_span = parser._node_span(ts, te)
                    if len(rargs) == 1:
                        start_node = _sh_make_constant_expr(range_target_span, 0, resolved_type="int64", repr_text="0")
                        stop_node = rargs[0]
                        step_node = _sh_make_constant_expr(range_target_span, 1, resolved_type="int64", repr_text="1")
                    elif len(rargs) == 2:
                        start_node = rargs[0]
                        stop_node = rargs[1]
                        step_node = _sh_make_constant_expr(range_target_span, 1, resolved_type="int64", repr_text="1")
                    else:
                        start_node = rargs[0]
                        stop_node = rargs[1]
                        step_node = rargs[2]
                    iter_expr = _sh_make_range_expr(
                        iter_expr.get("source_span"),
                        start_node,
                        stop_node,
                        step_node,
                        repr_text=str(iter_expr.get("repr", "range(...)")),
                    )
                ifs: list[dict[str, Any]] = []
                while parser._cur()["k"] == "NAME" and parser._cur()["v"] == "if":
                    parser._eat("NAME")
                    ifs.append(parser._parse_or())
                r = parser._eat("]")
                tgt_ty = parser._iter_item_type(iter_expr)
                first_norm = first
                ifs_norm = ifs
                if tgt_ty != "unknown":
                    snaps: dict[str, str] = {}
                    parser._collect_and_bind_comp_target_types(target, tgt_ty, snaps)
                    first_repr = first.get("repr")
                    first_col = int(first.get("source_span", {}).get("col", parser.col_base))
                    if isinstance(first_repr, str) and first_repr != "":
                        first_norm = _reparse_expr_with_context(parser, first_repr, col_base=first_col)
                    ifs_norm = []
                    for cond in ifs:
                        cond_repr = cond.get("repr")
                        cond_col = int(cond.get("source_span", {}).get("col", parser.col_base))
                        if isinstance(cond_repr, str) and cond_repr != "":
                            ifs_norm.append(_reparse_expr_with_context(parser, cond_repr, col_base=cond_col))
                        else:
                            ifs_norm.append(cond)
                    parser._restore_comp_target_types(snaps)
                return _sh_make_list_comp_expr(
                    parser._node_span(l["s"], r["e"]),
                    first_norm,
                    [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                    repr_text=parser._src_slice(l["s"], r["e"]),
                )
            elements.append(first)
            while True:
                if parser._cur()["k"] == ",":
                    parser._eat(",")
                    if parser._cur()["k"] == "]":
                        break
                    elements.append(parser._parse_ifexp())
                    continue
                break
        r = parser._eat("]")
        return _sh_make_list_expr(
            parser._node_span(l["s"], r["e"]),
            elements,
            repr_text=parser._src_slice(l["s"], r["e"]),
        )
    if tok["k"] == "{":
        l = parser._eat("{")
        if parser._cur()["k"] == "}":
            r = parser._eat("}")
            return _sh_make_dict_expr(
                parser._node_span(l["s"], r["e"]),
                keys=[],
                values=[],
                repr_text=parser._src_slice(l["s"], r["e"]),
            )
        first = parser._parse_ifexp()
        if parser._cur()["k"] == ":":
            keys = [first]
            vals: list[dict[str, Any]] = []
            parser._eat(":")
            vals.append(parser._parse_ifexp())
            first_key = keys[0]
            first_val = vals[0]
            if parser._cur()["k"] == "NAME" and parser._cur()["v"] == "for":
                parser._eat("NAME")
                target = parser._parse_comp_target()
                in_tok = parser._eat("NAME")
                if in_tok["v"] != "in":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="expected 'in' in dict comprehension",
                        source_span=parser._node_span(in_tok["s"], in_tok["e"]),
                        hint="Use `for x in iterable` form.",
                    )
                iter_expr = parser._parse_or()
                ifs: list[dict[str, Any]] = []
                while parser._cur()["k"] == "NAME" and parser._cur()["v"] == "if":
                    parser._eat("NAME")
                    ifs.append(parser._parse_or())

                key_node = first_key
                val_node = first_val
                ifs_norm: list[dict[str, Any]] = list(ifs)
                iter_ty = parser._iter_item_type(iter_expr)
                if iter_ty != "unknown":
                    snapshots: dict[str, str] = {}
                    parser._collect_and_bind_comp_target_types(target, iter_ty, snapshots)
                    try:
                        key_repr = first_key.get("repr")
                        val_repr = first_val.get("repr")
                        if isinstance(key_repr, str) and key_repr != "":
                            key_node = _reparse_expr_with_context(
                                parser,
                                key_repr,
                                col_base=int(first_key.get("source_span", {}).get("col", parser.col_base)),
                            )
                        if isinstance(val_repr, str) and val_repr != "":
                            val_node = _reparse_expr_with_context(
                                parser,
                                val_repr,
                                col_base=int(first_val.get("source_span", {}).get("col", parser.col_base)),
                            )
                        ifs_norm = []
                        for cond in ifs:
                            cond_repr = cond.get("repr")
                            cond_col = int(cond.get("source_span", {}).get("col", parser.col_base))
                            if isinstance(cond_repr, str) and cond_repr != "":
                                ifs_norm.append(_reparse_expr_with_context(parser, cond_repr, col_base=cond_col))
                            else:
                                ifs_norm.append(cond)
                    finally:
                        parser._restore_comp_target_types(snapshots)
                end_node = ifs_norm[-1] if len(ifs_norm) > 0 else iter_expr
                end_col = int(end_node.get("source_span", {}).get("end_col", parser.col_base))
                parser._eat("}")
                return _sh_make_dict_comp_expr(
                    parser._node_span(l["s"], end_col - parser.col_base),
                    key_node,
                    val_node,
                    [_sh_make_comp_generator(target, iter_expr, ifs_norm)],
                    repr_text=parser._src_slice(l["s"], end_col - parser.col_base),
                )
            while parser._cur()["k"] == ",":
                parser._eat(",")
                if parser._cur()["k"] == "}":
                    break
                keys.append(parser._parse_ifexp())
                parser._eat(":")
                vals.append(parser._parse_ifexp())
            r = parser._eat("}")
            return _sh_make_dict_expr(
                parser._node_span(l["s"], r["e"]),
                keys=keys,
                values=vals,
                repr_text=parser._src_slice(l["s"], r["e"]),
            )
        elements = [first]
        while parser._cur()["k"] == ",":
            parser._eat(",")
            if parser._cur()["k"] == "}":
                break
            elements.append(parser._parse_ifexp())
        r = parser._eat("}")
        return _sh_make_set_expr(
            parser._node_span(l["s"], r["e"]),
            elements,
            repr_text=parser._src_slice(l["s"], r["e"]),
        )
    raise _make_east_build_error(
        kind="unsupported_syntax",
        message=f"self_hosted parser cannot parse expression token: {tok['k']}",
        source_span=parser._node_span(tok["s"], tok["e"]),
        hint="Extend self_hosted expression parser for this syntax.",
    )


class _ShExprPrimaryParserMixin:
    def _parse_primary(self) -> dict[str, Any]:
        """primary expression parse を split module 側へ寄せる。"""
        return _parse_primary_impl(self)

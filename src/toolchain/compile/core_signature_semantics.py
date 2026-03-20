#!/usr/bin/env python3
"""Self-hosted EAST signature helper semantics."""

from __future__ import annotations

from typing import Any

from pytra.std import re

from toolchain.compile.core_stmt_text_semantics import _sh_split_top_level_assign
from toolchain.compile.core_type_semantics import _sh_ann_to_type_expr
from toolchain.compile.core_type_semantics import _sh_split_args_with_offsets
from toolchain.compile.core_type_semantics import _sh_type_expr_to_type_name


def _sh_parse_typed_binding(text: str, *, allow_dotted_name: bool = False) -> tuple[str, str, str] | None:
    """`name: Type` / `name: Type = expr` を手書きパースし、(name, type, default) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    colon = raw.find(":")
    if colon <= 0:
        return None
    name_txt = raw[:colon].strip()
    ann_txt = raw[colon + 1 :].strip()
    if ann_txt == "":
        return None
    if allow_dotted_name:
        name_parts = name_txt.split(".")
        if len(name_parts) == 0:
            return None
        norm_parts: list[str] = []
        for seg in name_parts:
            seg_norm = seg.strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", seg_norm) is None:
                return None
            norm_parts.append(seg_norm)
        name_txt = ".".join(norm_parts)
    else:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name_txt) is None:
            return None
    default_txt = ""
    split_ann = _sh_split_top_level_assign(ann_txt)
    if split_ann is not None:
        ann_lhs, ann_rhs = split_ann
        ann_txt = ann_lhs.strip()
        default_txt = ann_rhs.strip()
    if ann_txt == "":
        return None
    return name_txt, ann_txt, default_txt


def _sh_parse_augassign(text: str) -> tuple[str, str, str] | None:
    """`target <op>= expr` をトップレベルで分解して返す。"""
    raw = text.strip()
    if raw == "":
        return None
    ops = ["<<=", ">>=", "//=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="]
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(raw):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0:
            for op in ops:
                if raw[i : i + len(op)] == op:
                    left = raw[:i].strip()
                    right = raw[i + len(op) :].strip()
                    if left == "" or right == "":
                        return None
                    if left.count("=") > 0:
                        return None
                    return left, op, right
    return None


def _sh_parse_def_sig(
    ln_no: int,
    ln: str,
    *,
    in_class: str = "",
    type_aliases: dict[str, str],
    make_east_build_error: Any,
    make_span: Any,
    make_def_sig_info: Any,
) -> dict[str, Any] | None:
    """`def ...` 行から関数名・引数型・戻り型を抽出する。"""
    ln_norm: str = re.sub(r"\s+", " ", ln.strip())
    if not ln_norm.startswith("def ") or not ln_norm.endswith(":"):
        return None
    head = ln_norm[4:-1].strip()
    lp = head.find("(")
    rp = head.rfind(")")
    if lp <= 0 or rp < lp:
        return None
    fn_name = head[:lp].strip()
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", fn_name) is None:
        return None
    args_raw = head[lp + 1 : rp]
    tail = head[rp + 1 :].strip()
    if tail == "":
        ret_group = ""
    elif tail.startswith("->"):
        ret_group = tail[2:].strip()
        if ret_group == "":
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="self_hosted parser cannot parse return annotation in function signature",
                source_span=make_span(ln_no, 0, len(ln_norm)),
                hint="Use `def name(args) -> Type:` style signature.",
            )
    else:
        return None
    arg_types: dict[str, str] = {}
    arg_type_exprs: dict[str, dict[str, Any]] = {}
    arg_order: list[str] = []
    arg_defaults: dict[str, str] = {}
    vararg_name = ""
    vararg_type = ""
    vararg_type_expr: dict[str, Any] | None = None
    if args_raw.strip() != "":
        for p_txt, _off in _sh_split_args_with_offsets(args_raw):
            p = p_txt.strip()
            if p == "":
                continue
            if p == "*":
                continue
            if p == "/":
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message="self_hosted parser cannot parse positional-only marker '/' in parameter list",
                    source_span=make_span(ln_no, 0, len(ln_norm)),
                    hint="Remove '/' from signature for now.",
                )
            if p.startswith("**"):
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse variadic kwargs parameter: {p_txt}",
                    source_span=make_span(ln_no, 0, len(ln_norm)),
                    hint="Use explicit parameters instead of **kwargs.",
                )
            if p.startswith("*"):
                if vararg_name != "":
                    raise make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse duplicate variadic args parameter: {p_txt}",
                        source_span=make_span(ln_no, 0, len(ln_norm)),
                        hint="Use at most one typed *args parameter.",
                    )
                parsed_vararg = _sh_parse_typed_binding(p[1:].strip(), allow_dotted_name=False)
                if parsed_vararg is None:
                    raise make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse variadic args parameter: {p_txt}",
                        source_span=make_span(ln_no, 0, len(ln_norm)),
                        hint="Use `*name: Type` for typed variadic positional parameters.",
                    )
                vn, vt, vdef = parsed_vararg
                if vdef != "":
                    raise make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse default value on variadic args parameter: {p_txt}",
                        source_span=make_span(ln_no, 0, len(ln_norm)),
                        hint="Remove the default from `*args` and initialize inside the function body instead.",
                    )
                vararg_expr = _sh_ann_to_type_expr(vt, type_aliases=type_aliases)
                vararg_name = vn
                vararg_type = _sh_type_expr_to_type_name(vararg_expr)
                vararg_type_expr = vararg_expr
                continue
            if in_class != "" and p == "self":
                arg_types["self"] = in_class
                arg_type_exprs["self"] = _sh_ann_to_type_expr(in_class, type_aliases=type_aliases)
                arg_order.append("self")
                continue
            if ":" not in p:
                p_name = p
                p_default = ""
                p_assign = _sh_split_top_level_assign(p)
                if p_assign is not None:
                    p_name = p_assign[0].strip()
                    p_default = p_assign[1].strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", p_name):
                    raise make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter name: {p_txt}",
                        source_span=make_span(ln_no, 0, len(ln_norm)),
                        hint="Use valid identifier for parameter name.",
                    )
                if in_class != "" and p_name == "self":
                    arg_types["self"] = in_class
                    arg_type_exprs["self"] = _sh_ann_to_type_expr(in_class, type_aliases=type_aliases)
                    arg_order.append("self")
                    if p_default != "":
                        arg_defaults["self"] = p_default
                    continue
                arg_types[p_name] = "unknown"
                arg_type_exprs[p_name] = _sh_ann_to_type_expr("unknown", type_aliases=type_aliases)
                arg_order.append(p_name)
                if p_default != "":
                    arg_defaults[p_name] = p_default
                continue
            parsed_param = _sh_parse_typed_binding(p, allow_dotted_name=False)
            if parsed_param is None:
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter: {p_txt}",
                    source_span=make_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            pn, pt, pdef = parsed_param
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter name: {pn}",
                    source_span=make_span(ln_no, 0, len(ln_norm)),
                    hint="Use valid identifier for parameter name.",
                )
            if pt == "":
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                    source_span=make_span(ln_no, 0, len(ln_norm)),
                    hint="Use `name: Type` style parameters.",
                )
            arg_expr = _sh_ann_to_type_expr(pt, type_aliases=type_aliases)
            arg_types[pn] = _sh_type_expr_to_type_name(arg_expr)
            arg_type_exprs[pn] = arg_expr
            arg_order.append(pn)
            if pdef != "":
                default_txt = pdef.strip()
                if default_txt != "":
                    arg_defaults[pn] = default_txt
    ret_expr = (
        _sh_ann_to_type_expr(ret_group.strip(), type_aliases=type_aliases)
        if ret_group != ""
        else _sh_ann_to_type_expr("None", type_aliases=type_aliases)
    )
    return make_def_sig_info(
        fn_name,
        _sh_type_expr_to_type_name(ret_expr),
        arg_types,
        arg_type_exprs,
        ret_expr,
        arg_order,
        arg_defaults,
        vararg_name=vararg_name,
        vararg_type=vararg_type,
        vararg_type_expr=vararg_type_expr,
    )

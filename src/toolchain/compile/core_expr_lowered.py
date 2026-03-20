#!/usr/bin/env python3
"""Self-hosted lowered expression parsing helpers for EAST core."""

from __future__ import annotations

from pytra.std import re
from typing import Any

from toolchain.frontends.frontend_semantics import lookup_builtin_semantic_tag


def _find_colon_outside_strings(text: str) -> int:
    """文字列リテラル外の最初の `:` 位置を返す。見つからなければ -1。"""
    in_str: str = ""
    esc: bool = False
    for i, ch in enumerate(text):
        if in_str != "":
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = ""
            continue
        if ch == "'" or ch == '"':
            in_str = ch
            continue
        if ch == ":":
            return i
    return -1
from toolchain.compile.core_ast_builders import _sh_make_binop_expr
from toolchain.compile.core_ast_builders import _sh_make_builtin_listcomp_call_expr
from toolchain.compile.core_ast_builders import _sh_make_comp_generator
from toolchain.compile.core_ast_builders import _sh_make_constant_expr
from toolchain.compile.core_ast_builders import _sh_make_dict_comp_expr
from toolchain.compile.core_ast_builders import _sh_make_dict_entry
from toolchain.compile.core_ast_builders import _sh_make_dict_expr
from toolchain.compile.core_ast_builders import _sh_make_ifexp_expr
from toolchain.compile.core_ast_builders import _sh_make_list_comp_expr
from toolchain.compile.core_ast_builders import _sh_make_range_expr
from toolchain.compile.core_ast_builders import _sh_make_set_comp_expr
from toolchain.compile.core_builder_base import _sh_make_tuple_expr
from toolchain.compile.core_builder_base import _sh_span
from toolchain.compile.core_entrypoints import _make_east_build_error
from toolchain.compile.core_parse_context import _SH_CLASS_BASE
from toolchain.compile.core_parse_context import _SH_CLASS_METHOD_RETURNS
from toolchain.compile.core_parse_context import _SH_FN_RETURNS
from toolchain.compile.core_stmt_text_semantics import _sh_bind_comp_target_types
from toolchain.compile.core_stmt_text_semantics import _sh_split_top_commas
from toolchain.compile.core_stmt_text_semantics import _sh_split_top_plus
from toolchain.compile.core_string_semantics import _sh_extract_adjacent_string_parts
from toolchain.compile.core_text_semantics import _sh_split_top_keyword


def _sh_parse_expr_lowered_impl(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
    """Convert expression text into an EAST expression node with light lowering."""
    from toolchain.compile.core_expr_shell import _sh_parse_expr

    _sh_parse_expr_lowered = _sh_parse_expr_lowered_impl
    raw = expr_txt
    txt = raw.strip()

    # lambda is lower precedence than if-expression, so delegate to the full parser.
    if txt.startswith("lambda "):
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # if-expression: a if cond else b
    p_if = _sh_split_top_keyword(txt, "if")
    p_else = _sh_split_top_keyword(txt, "else")
    if p_if >= 0 and p_else > p_if:
        body_txt = txt[:p_if].strip()
        test_txt = txt[p_if + 2 : p_else].strip()
        else_txt = txt[p_else + 4 :].strip()
        body_node = _sh_parse_expr_lowered(body_txt, ln_no=ln_no, col=col + txt.find(body_txt), name_types=dict(name_types))
        test_node = _sh_parse_expr_lowered(test_txt, ln_no=ln_no, col=col + txt.find(test_txt), name_types=dict(name_types))
        else_node = _sh_parse_expr_lowered(else_txt, ln_no=ln_no, col=col + txt.rfind(else_txt), name_types=dict(name_types))
        return _sh_make_ifexp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            test_node,
            body_node,
            else_node,
            repr_text=txt,
        )

    # Normalize generator-arg any/all into list-comp form for the self-hosted parser.
    m_any_all: re.Match | None = re.match(r"^(any|all)\((.+)\)$", txt, flags=re.S)
    if m_any_all is not None:
        fn_name = re.group(m_any_all, 1)
        inner_arg = re.strip_group(m_any_all, 2)
        if _sh_split_top_keyword(inner_arg, "for") > 0 and _sh_split_top_keyword(inner_arg, "in") > 0:
            lc = _sh_parse_expr_lowered(f"[{inner_arg}]", ln_no=ln_no, col=col + txt.find(inner_arg), name_types=dict(name_types))
            runtime_call = "py_any" if fn_name == "any" else ("py_all" if fn_name == "all" else "")
            semantic_tag = lookup_builtin_semantic_tag(fn_name)
            return _sh_make_builtin_listcomp_call_expr(
                _sh_span(ln_no, col, col + len(raw)),
                line_no=ln_no,
                base_col=col,
                func_name=fn_name,
                arg=lc,
                repr_text=txt,
                runtime_call=runtime_call,
                semantic_tag=semantic_tag,
            )

    # Normalize single generator-argument calls into list-comp argument form.
    # Example: ", ".join(f(x) for x in items) -> ", ".join([f(x) for x in items])
    if txt.endswith(")"):
        depth = 0
        in_str: str | None = None
        esc = False
        open_idx = -1
        close_idx = -1
        for idx, ch in enumerate(txt):
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
            if ch == "(":
                if depth == 0 and open_idx < 0:
                    open_idx = idx
                depth += 1
                continue
            if ch == ")":
                depth -= 1
                if depth == 0:
                    close_idx = idx
                continue
            if open_idx > 0 and close_idx == len(txt) - 1:
                inner = txt[open_idx + 1 : close_idx].strip()
                inner_parts: list[str] = _sh_split_top_commas(inner)
                if len(inner_parts) == 1 and inner_parts[0] == inner and _sh_split_top_keyword(inner, "for") > 0 and _sh_split_top_keyword(inner, "in") > 0:
                    rewritten = txt[: open_idx + 1] + "[" + inner + "]" + txt[close_idx:]
                    return _sh_parse_expr_lowered(rewritten, ln_no=ln_no, col=col, name_types=dict(name_types))

    # Handle concatenation chains that include f-strings before generic parsing.
    top_comma_parts = _sh_split_top_commas(txt)
    is_single_top_expr = len(top_comma_parts) == 1

    adjacent_strings = _sh_extract_adjacent_string_parts(txt, ln_no, col, name_types)
    if adjacent_strings is not None and len(adjacent_strings) >= 2:
        nodes = [
            _sh_parse_expr(
                part,
                line_no=ln_no,
                col_base=part_col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )
            for part, part_col in adjacent_strings
        ]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node

    plus_parts = _sh_split_top_plus(txt)
    if len(plus_parts) >= 2 and any(p.startswith("f\"") or p.startswith("f'") for p in plus_parts):
        nodes = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in plus_parts]
        node = nodes[0]
        for rhs in nodes[1:]:
            node = _sh_make_binop_expr(
                _sh_span(ln_no, col, col + len(raw)),
                node,
                "Add",
                rhs,
                resolved_type="str",
                repr_text=txt,
            )
        return node
    if len(plus_parts) >= 2 and is_single_top_expr:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    # dict-comp support: {k: v for x in it} / {k: v for a, b in it}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            head = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{key: value for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            if ":" not in head:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid dict comprehension pair in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `key: value` pair before `for`.",
                )
            ktxt, vtxt = head.split(":", 1)
            ktxt = ktxt.strip()
            vtxt = vtxt.strip()
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            key_node = _sh_parse_expr_lowered(ktxt, ln_no=ln_no, col=col + txt.find(ktxt), name_types=dict(comp_types))
            val_node = _sh_parse_expr_lowered(vtxt, ln_no=ln_no, col=col + txt.find(vtxt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            kt = str(key_node.get("resolved_type", "unknown"))
            vt = str(val_node.get("resolved_type", "unknown"))
            return _sh_make_dict_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                key_node,
                val_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                resolved_type=f"dict[{kt},{vt}]",
                repr_text=txt,
            )

    # set-comp support: {x for x in it} / {x for a, b in it if cond}
    if txt.startswith("{") and txt.endswith("}") and ":" not in txt and is_single_top_expr:
        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            tail = inner[p_for + 3 :].strip()
            p_in = _sh_split_top_keyword(tail, "in")
            if p_in <= 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"invalid set comprehension in self_hosted parser: {txt}",
                    source_span=_sh_span(ln_no, col, col + len(raw)),
                    hint="Use `{elem for item in iterable}` form.",
                )
            tgt_txt = tail[:p_in].strip()
            iter_and_if_txt = tail[p_in + 2 :].strip()
            p_if = _sh_split_top_keyword(iter_and_if_txt, "if")
            if p_if >= 0:
                iter_txt = iter_and_if_txt[:p_if].strip()
                if_txt = iter_and_if_txt[p_if + 2 :].strip()
            else:
                iter_txt = iter_and_if_txt
                if_txt = ""
            iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
            target_node = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=col + txt.find(tgt_txt), name_types=dict(name_types))
            comp_types = _sh_bind_comp_target_types(dict(name_types), target_node, iter_node)
            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            if_nodes: list[dict[str, Any]] = []
            if if_txt != "":
                if_nodes.append(_sh_parse_expr_lowered(if_txt, ln_no=ln_no, col=col + txt.find(if_txt), name_types=dict(comp_types)))
            return _sh_make_set_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                [_sh_make_comp_generator(target_node, iter_node, if_nodes)],
                repr_text=txt,
            )

    # dict literal: {"a": 1, "b": 2}
    if txt.startswith("{") and txt.endswith("}") and ":" in txt:
        inner = txt[1:-1].strip()
        entries: list[dict[str, Any]] = []
        if inner != "":
            for part in _sh_split_top_commas(inner):
                colon_pos = _find_colon_outside_strings(part)
                if colon_pos < 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid dict entry in self_hosted parser: {part}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `key: value` form in dict literals.",
                    )
                ktxt, vtxt = part[:colon_pos], part[colon_pos + 1:]
                ktxt = ktxt.strip()
                vtxt = vtxt.strip()
                entries.append(
                    _sh_make_dict_entry(
                        _sh_parse_expr_lowered(
                            ktxt,
                            ln_no=ln_no,
                            col=col + txt.find(ktxt),
                            name_types=dict(name_types),
                        ),
                        _sh_parse_expr_lowered(
                            vtxt,
                            ln_no=ln_no,
                            col=col + txt.find(vtxt),
                            name_types=dict(name_types),
                        ),
                    )
                )
        return _sh_make_dict_expr(
            _sh_span(ln_no, col, col + len(raw)),
            entries=entries,
            repr_text=txt,
        )

    # list-comp support: [expr for target in iter if cond] + chained for-clauses
    if txt.startswith("[") and txt.endswith("]") and is_single_top_expr:
        first_closing = -1
        depth = 0
        in_str3: str | None = None
        esc3 = False
        for i, ch in enumerate(txt):
            if in_str3 is not None:
                if esc3:
                    esc3 = False
                    continue
                if ch == "\\":
                    esc3 = True
                elif ch == in_str3:
                    in_str3 = None
                continue
            if ch in {"'", '"'}:
                in_str3 = ch
                continue
            if ch == "[":
                depth += 1
            elif ch == "]":
                if depth == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid bracket nesting in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Check list/tuple bracket balance.",
                    )
                depth -= 1
                if depth == 0:
                    first_closing = i
                    break
        if first_closing != len(txt) - 1:
            # Delegate to full parser when this is not a standalone list expression
            # (e.g. list-comprehension result with trailing slice/index).
            return _sh_parse_expr(
                txt,
                line_no=ln_no,
                col_base=col,
                name_types=name_types,
                fn_return_types=_SH_FN_RETURNS,
                class_method_return_types=_SH_CLASS_METHOD_RETURNS,
                class_base=_SH_CLASS_BASE,
            )

        inner = txt[1:-1].strip()
        p_for = _sh_split_top_keyword(inner, "for")
        if p_for > 0:
            elt_txt = inner[:p_for].strip()
            rest = inner[p_for + 3 :].strip()
            generators: list[dict[str, Any]] = []
            comp_types: dict[str, str] = dict(name_types)
            while True:
                p_in = _sh_split_top_keyword(rest, "in")
                if p_in <= 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid list comprehension in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `[elem for item in iterable]` form.",
                    )
                tgt_txt = rest[:p_in].strip()
                iter_and_suffix_txt = rest[p_in + 2 :].strip()
                if tgt_txt == "" or iter_and_suffix_txt == "":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid list comprehension in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `[elem for item in iterable]` form.",
                    )
                p_next_for = _sh_split_top_keyword(iter_and_suffix_txt, "for")
                p_next_if = _sh_split_top_keyword(iter_and_suffix_txt, "if")
                next_pos = -1
                if p_next_for >= 0 and (p_next_if < 0 or p_next_for < p_next_if):
                    next_pos = p_next_for
                elif p_next_if >= 0:
                    next_pos = p_next_if
                iter_txt = iter_and_suffix_txt
                suffix_txt = ""
                if next_pos >= 0:
                    iter_txt = iter_and_suffix_txt[:next_pos].strip()
                    suffix_txt = iter_and_suffix_txt[next_pos:].strip()
                if iter_txt == "":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid list comprehension in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `[elem for item in iterable]` form.",
                    )

                target_node = _sh_parse_expr_lowered(
                    tgt_txt,
                    ln_no=ln_no,
                    col=col + txt.find(tgt_txt),
                    name_types=dict(comp_types),
                )
                iter_node = _sh_parse_expr_lowered(
                    iter_txt,
                    ln_no=ln_no,
                    col=col + txt.find(iter_txt),
                    name_types=dict(comp_types),
                )
                if (
                    isinstance(iter_node, dict)
                    and iter_node.get("kind") == "Call"
                    and isinstance(iter_node.get("func"), dict)
                    and iter_node.get("func", {}).get("kind") == "Name"
                    and iter_node.get("func", {}).get("id") == "range"
                ):
                    rargs = list(iter_node.get("args", []))
                    if len(rargs) == 1:
                        start_node = _sh_make_constant_expr(
                            _sh_span(ln_no, col, col),
                            0,
                            resolved_type="int64",
                            repr_text="0",
                        )
                        stop_node = rargs[0]
                        step_node = _sh_make_constant_expr(
                            _sh_span(ln_no, col, col),
                            1,
                            resolved_type="int64",
                            repr_text="1",
                        )
                    elif len(rargs) == 2:
                        start_node = rargs[0]
                        stop_node = rargs[1]
                        step_node = _sh_make_constant_expr(
                            _sh_span(ln_no, col, col),
                            1,
                            resolved_type="int64",
                            repr_text="1",
                        )
                    else:
                        start_node = rargs[0]
                        stop_node = rargs[1]
                        step_node = rargs[2]
                    iter_node = _sh_make_range_expr(
                        iter_node.get("source_span"),
                        start_node,
                        stop_node,
                        step_node,
                        repr_text=str(iter_node.get("repr", "range(...)")),
                    )

                comp_types = _sh_bind_comp_target_types(dict(comp_types), target_node, iter_node)
                if_nodes: list[dict[str, Any]] = []
                while suffix_txt.startswith("if "):
                    cond_tail = suffix_txt[3:].strip()
                    p_cond_for = _sh_split_top_keyword(cond_tail, "for")
                    p_cond_if = _sh_split_top_keyword(cond_tail, "if")
                    split_pos = -1
                    if p_cond_for >= 0 and (p_cond_if < 0 or p_cond_for < p_cond_if):
                        split_pos = p_cond_for
                    elif p_cond_if >= 0:
                        split_pos = p_cond_if
                    cond_txt = cond_tail
                    suffix_txt = ""
                    if split_pos >= 0:
                        cond_txt = cond_tail[:split_pos].strip()
                        suffix_txt = cond_tail[split_pos:].strip()
                    if cond_txt == "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"invalid list comprehension condition in self_hosted parser: {txt}",
                            source_span=_sh_span(ln_no, col, col + len(raw)),
                            hint="Use `[elem for item in iterable if cond]` form.",
                        )
                    if_nodes.append(
                        _sh_parse_expr_lowered(
                            cond_txt,
                            ln_no=ln_no,
                            col=col + txt.find(cond_txt),
                            name_types=dict(comp_types),
                        )
                    )

                generators.append(_sh_make_comp_generator(target_node, iter_node, if_nodes))
                if suffix_txt == "":
                    break
                if not suffix_txt.startswith("for "):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid list comprehension in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                    )
                rest = suffix_txt[4:].strip()
                if rest == "":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"invalid list comprehension in self_hosted parser: {txt}",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Use `[elem for item in iterable for item2 in iterable2]` form.",
                    )

            elt_node = _sh_parse_expr_lowered(elt_txt, ln_no=ln_no, col=col + txt.find(elt_txt), name_types=dict(comp_types))
            elem_t = str(elt_node.get("resolved_type", "unknown"))
            return _sh_make_list_comp_expr(
                _sh_span(ln_no, col, col + len(raw)),
                elt_node,
                generators,
                resolved_type=f"list[{elem_t}]",
                repr_text=txt,
            )

    # Very simple list-comp support: [x for x in <iter>]
    m_lc: re.Match | None = re.match(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s+for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)\]$", txt)
    if m_lc is not None:
        elt_name = re.group(m_lc, 1)
        tgt_name = re.group(m_lc, 2)
        iter_txt = re.strip_group(m_lc, 3)
        iter_node = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=col + txt.find(iter_txt), name_types=dict(name_types))
        it_t = str(iter_node.get("resolved_type", "unknown"))
        elem_t = "unknown"
        if it_t.startswith("list[") and it_t.endswith("]"):
            elem_t = it_t[5:-1]
        return _sh_make_simple_name_list_comp_expr(
            _sh_span(ln_no, col, col + len(raw)),
            line_no=ln_no,
            base_col=col,
            elt_name=elt_name,
            target_name=tgt_name,
            iter_expr=iter_node,
            elem_type=elem_t,
            repr_text=txt,
        )

    if len(txt) >= 3 and txt[0] == "f" and txt[1] in {"'", '"'} and txt[-1] == txt[1]:
        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=_SH_FN_RETURNS,
            class_method_return_types=_SH_CLASS_METHOD_RETURNS,
            class_base=_SH_CLASS_BASE,
        )

    tuple_parts = _sh_split_top_commas(txt)
    if len(tuple_parts) >= 2 or (len(tuple_parts) == 1 and txt.endswith(",")):
        elems = [_sh_parse_expr_lowered(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
        elem_ts = [str(e.get("resolved_type", "unknown")) for e in elems]
        return _sh_make_tuple_expr(
            _sh_span(ln_no, col, col + len(raw)),
            elems,
            resolved_type="tuple[" + ", ".join(elem_ts) + "]",
            repr_text=txt,
        )

    return _sh_parse_expr(
        txt,
        line_no=ln_no,
        col_base=col,
        name_types=name_types,
        fn_return_types=_SH_FN_RETURNS,
        class_method_return_types=_SH_CLASS_METHOD_RETURNS,
        class_base=_SH_CLASS_BASE,
    )

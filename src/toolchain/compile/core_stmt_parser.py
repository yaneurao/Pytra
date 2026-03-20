#!/usr/bin/env python3
"""Self-hosted EAST statement block parser cluster."""

from __future__ import annotations

from pytra.std import re
from typing import Any


def _sh_parse_stmt_block_mutable(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """インデントブロックを文単位で解析し、EAST 文リストを返す。"""
    from toolchain.compile.core_stmt_parser_support import (
        _SH_FN_RETURNS,
        _SH_IMPORT_MODULES,
        _SH_IMPORT_SYMBOLS,
        _SH_TYPE_ALIASES,
        _make_east_build_error,
        _sh_ann_to_type,
        _sh_ann_to_type_expr,
        _sh_block_end_span,
        _sh_build_arg_usage_map,
        _sh_collect_indented_block,
        _sh_collect_yield_value_types,
        _sh_extract_leading_docstring,
        _sh_infer_return_type_for_untyped_def,
        _sh_is_host_only_alias,
        _sh_make_ann_assign_stmt,
        _sh_make_assign_stmt,
        _sh_make_augassign_stmt,
        _sh_make_constant_expr,
        _sh_make_def_sig_info,
        _sh_make_except_handler,
        _sh_make_expr_stmt,
        _sh_make_for_range_stmt,
        _sh_make_for_stmt,
        _sh_make_function_def_stmt,
        _sh_make_generator_return_type,
        _sh_make_if_stmt,
        _sh_make_import_alias,
        _sh_make_import_from_stmt,
        _sh_make_import_stmt,
        _sh_make_import_symbol_binding,
        _sh_make_name_expr,
        _sh_make_pass_stmt,
        _sh_make_raise_stmt,
        _sh_make_return_stmt,
        _sh_make_stmt_node,
        _sh_make_swap_stmt,
        _sh_make_trivia_blank,
        _sh_make_trivia_comment,
        _sh_make_try_stmt,
        _sh_make_tuple_destructure_assign_stmt,
        _sh_make_while_stmt,
        _sh_make_yield_stmt,
        _sh_merge_logical_lines,
        _sh_parse_augassign,
        _sh_parse_def_sig,
        _sh_parse_except_clause,
        _sh_parse_expr_lowered,
        _sh_parse_if_tail,
        _sh_parse_import_alias,
        _sh_parse_import_from_clause,
        _sh_parse_typed_binding,
        _sh_push_stmt_with_trivia,
        _sh_raise_if_trailing_stmt_terminator,
        _sh_register_import_module,
        _sh_register_import_symbol,
        _sh_span,
        _sh_split_def_header_and_inline_stmt,
        _sh_split_top_commas,
        _sh_split_top_level_assign,
        _sh_split_top_level_colon,
        _sh_split_top_level_from,
        _sh_split_top_level_in,
        _sh_stmt_span,
        _sh_strip_inline_comment,
    )

    def _maybe_bind_self_field(
        target_expr: dict[str, Any] | None,
        value_type: str | None,
        *,
        explicit: str | None = None,
    ) -> None:
        """`self.xxx` への代入時、self フィールドの型推論を更新する。"""
        if not isinstance(target_expr, dict):
            return
        if target_expr.get("kind") != "Attribute":
            return
        owner = target_expr.get("value")
        if not isinstance(owner, dict):
            return
        if owner.get("kind") != "Name" or owner.get("id") != "self":
            return
        field_name = str(target_expr.get("attr", "")).strip()
        if field_name == "":
            return
        candidate = value_type or ""
        if candidate != "":
            name_types[field_name] = candidate
            return
        if isinstance(explicit, str) and explicit.strip() != "":
            name_types[field_name] = explicit.strip()

    body_lines, merged_line_end = _sh_merge_logical_lines(body_lines)

    stmts: list[dict[str, Any]] = []
    pending_leading_trivia: list[dict[str, Any]] = []
    pending_blank_count = 0

    skip = 0
    for i, (_, ln_txt) in enumerate(body_lines):
        if skip > 0:
            skip -= 1
            continue
        ln_no, ln_txt = body_lines[i]
        indent = len(ln_txt) - len(ln_txt.lstrip(" "))
        raw_s = ln_txt.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(
            s,
            line_no=ln_no,
            line_text=ln_txt,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
        )

        if raw_s == "":
            pending_blank_count += 1
            continue
        if raw_s.startswith("#"):
            if pending_blank_count > 0:
                pending_leading_trivia.append(_sh_make_trivia_blank(pending_blank_count))
                pending_blank_count = 0
            text = raw_s[1:]
            if text.startswith(" "):
                text = text[1:]
            pending_leading_trivia.append(_sh_make_trivia_comment(text))
            continue
        if s == "":
            continue

        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(
            ln_no,
            sig_line,
            type_aliases=_SH_TYPE_ALIASES,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
            make_def_sig_info=_sh_make_def_sig_info,
        )
        if sig is not None:
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types: dict[str, str] = dict(sig["arg_types"])
            arg_type_exprs_obj: Any = sig.get("arg_type_exprs")
            arg_type_exprs: dict[str, Any] = arg_type_exprs_obj if isinstance(arg_type_exprs_obj, dict) else {}
            arg_order: list[str] = list(sig["arg_order"])
            arg_defaults_raw_obj: Any = sig.get("arg_defaults")
            arg_defaults_raw: dict[str, Any] = arg_defaults_raw_obj if isinstance(arg_defaults_raw_obj, dict) else {}
            vararg_name = str(sig.get("vararg_name", ""))
            vararg_type = str(sig.get("vararg_type", ""))
            vararg_type_expr_obj: Any = sig.get("vararg_type_expr")
            vararg_type_expr = vararg_type_expr_obj if isinstance(vararg_type_expr_obj, dict) else None
            fn_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_fn_stmt != "":
                fn_block = [(ln_no, " " * (indent + 4) + inline_fn_stmt)]
            else:
                fn_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(fn_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty nested function body '{fn_name}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add nested function statements.",
                    )
            fn_scope_types: dict[str, str] = dict(name_types)
            for arg_name, arg_ty in arg_types.items():
                fn_scope_types[arg_name] = arg_ty
            if vararg_name != "":
                fn_scope_types[vararg_name] = f"list[{vararg_type if vararg_type != '' else 'unknown'}]"
            fn_stmts = _sh_parse_stmt_block(fn_block, name_types=fn_scope_types, scope_label=f"{scope_label}.{fn_name}")
            docstring, fn_stmts = _sh_extract_leading_docstring(fn_stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, fn_stmts)
            yield_types = _sh_collect_yield_value_types(fn_stmts)
            is_generator = len(yield_types) > 0
            fn_ret_effective = fn_ret
            yield_value_type = "unknown"
            if is_generator:
                fn_ret_effective, yield_value_type = _sh_make_generator_return_type(fn_ret, yield_types)
            fn_ret_type_expr = _sh_ann_to_type_expr(fn_ret_effective, type_aliases=_SH_TYPE_ALIASES)
            arg_defaults: dict[str, Any] = {}
            arg_index_map: dict[str, int] = {}
            for arg_pos, arg_name in enumerate(arg_order):
                arg_index_map[arg_name] = int(arg_pos)
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = ln_txt.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=ln_no,
                            col=default_col,
                            name_types=dict(name_types),
                        )
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, fn_stmts)
            callable_parts: list[str] = []
            for arg_name in arg_order:
                callable_parts.append(arg_types.get(arg_name, "unknown"))
            name_types[fn_name] = "callable[" + ", ".join(callable_parts) + "->" + fn_ret_effective + "]"
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_function_def_stmt(
                    fn_name,
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    arg_types,
                    arg_order,
                    fn_ret_effective,
                    fn_stmts,
                    arg_type_exprs=arg_type_exprs,
                    arg_defaults=arg_defaults,
                    arg_index=arg_index_map,
                    return_type_expr=fn_ret_type_expr,
                    arg_usage=arg_usage_map,
                    docstring=docstring,
                    is_generator=is_generator,
                    yield_value_type=yield_value_type,
                    vararg_name=vararg_name,
                    vararg_type=vararg_type,
                    vararg_type_expr=vararg_type_expr,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("if ") and s.endswith(":"):
            cond_txt = s[len("if ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            then_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(then_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"if body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented if-body.",
                )
            else_stmt_list, j = _sh_parse_if_tail(
                start_idx=j,
                parent_indent=indent,
                body_lines=body_lines,
                name_types=dict(name_types),
                scope_label=scope_label,
                strip_inline_comment=_sh_strip_inline_comment,
                raise_if_trailing_stmt_terminator=_sh_raise_if_trailing_stmt_terminator,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
                collect_indented_block=_sh_collect_indented_block,
                parse_expr_lowered=_sh_parse_expr_lowered,
                parse_stmt_block=_sh_parse_stmt_block,
                make_if_stmt=_sh_make_if_stmt,
                block_end_span=_sh_block_end_span,
            )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_if_stmt(
                    _sh_block_end_span(body_lines, ln_no, ln_txt.find("if "), len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                    orelse=else_stmt_list,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("for "):
            for_full = s[len("for ") :].strip()
            for_head = ""
            inline_stmt_text = ""
            if for_full.endswith(":"):
                for_head = for_full[:-1].strip()
            else:
                split_colon = _sh_split_top_level_colon(for_full)
                if split_colon is not None:
                    for_head = split_colon[0]
                    inline_stmt_text = split_colon[1]
            if for_head == "":
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            split_for = _sh_split_top_level_in(for_head)
            if split_for is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse for statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `for target in iterable:` form.",
                )
            tgt_txt, iter_txt = split_for
            tgt_col = ln_txt.find(tgt_txt)
            iter_col = ln_txt.find(iter_txt)
            target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no=ln_no, col=tgt_col, name_types=dict(name_types))
            iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
            body_block: list[tuple[int, str]] = []
            j = i + 1
            if inline_stmt_text != "":
                body_block.append((ln_no, " " * (indent + 4) + inline_stmt_text))
            else:
                body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
                if len(body_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"for body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented for-body.",
                    )
            t_ty = "unknown"
            i_ty = str(iter_expr.get("resolved_type", "unknown"))
            i_ty_norm = i_ty.strip()
            iter_mode = "static_fastpath"
            iterable_trait = "unknown"
            iter_protocol = "static_range"
            tuple_target_elem_types: list[str] = []
            if i_ty.startswith("list[") and i_ty.endswith("]"):
                inner_t = i_ty[5:-1].strip()
                t_ty = inner_t
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
                if inner_t.startswith("tuple[") and inner_t.endswith("]"):
                    tuple_inner = inner_t[6:-1].strip()
                    if tuple_inner != "":
                        tuple_target_elem_types = _sh_split_top_commas(tuple_inner)
            elif i_ty.startswith("dict[") and i_ty.endswith("]"):
                dict_inner = i_ty[5:-1].strip()
                dict_parts = _sh_split_top_commas(dict_inner)
                if len(dict_parts) >= 1:
                    key_t = dict_parts[0].strip()
                    t_ty = key_t if key_t != "" else "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                t_ty = "unknown"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty.startswith("set[") and i_ty.endswith("]"):
                t_ty = i_ty[4:-1]
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty == "str":
                t_ty = "str"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty in {"bytes", "bytearray"}:
                t_ty = "uint8"
                iter_mode = "static_fastpath"
                iterable_trait = "yes"
                iter_protocol = "static_range"
            elif i_ty_norm == "Any" or i_ty_norm == "object":
                iter_mode = "runtime_protocol"
                iterable_trait = "unknown"
                iter_protocol = "runtime_protocol"
            elif i_ty_norm in {"int", "int64", "float", "float64", "bool"}:
                iterable_trait = "no"
                iter_mode = "runtime_protocol"
                iter_protocol = "runtime_protocol"
            elif "|" in i_ty_norm:
                union_parts = _sh_split_top_commas(i_ty_norm.replace("|", ","))
                for up in union_parts:
                    u = up.strip()
                    if u == "Any" or u == "object":
                        iter_mode = "runtime_protocol"
                        iter_protocol = "runtime_protocol"
                        break
            if isinstance(iter_expr, dict):
                iter_expr["iterable_trait"] = iterable_trait
                iter_expr["iter_protocol"] = iter_protocol
                iter_expr["iter_element_type"] = t_ty
            target_names: list[str] = []
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    target_names.append(nm)
            elif isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                elem_nodes_obj: Any = target_expr.get("elements", [])
                elem_nodes: list[dict[str, Any]] = elem_nodes_obj if isinstance(elem_nodes_obj, list) else []
                for e in elem_nodes:
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = str(e.get("id", ""))
                        if nm != "":
                            target_names.append(nm)
            if len(tuple_target_elem_types) > 0 and isinstance(target_expr, dict) and target_expr.get("kind") == "Tuple":
                target_expr["resolved_type"] = f"tuple[{','.join([t.strip() if t.strip() != '' else 'unknown' for t in tuple_target_elem_types])}]"
                for idx, nm in enumerate(target_names):
                    if idx < len(tuple_target_elem_types):
                        et = tuple_target_elem_types[idx].strip()
                        if et == "":
                            et = "unknown"
                        name_types[nm] = et
                        try:
                            elem_nodes[idx]["resolved_type"] = et
                        except Exception:
                            pass
                    else:
                        name_types[nm] = "unknown"
                        try:
                            elem_nodes[idx]["resolved_type"] = "unknown"
                        except Exception:
                            pass
            elif t_ty != "unknown":
                for nm in target_names:
                    name_types[nm] = t_ty
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_expr["resolved_type"] = t_ty
            if (
                isinstance(target_expr, dict)
                and target_expr.get("kind") == "Name"
                and
                isinstance(iter_expr, dict)
                and iter_expr.get("kind") == "Call"
                and isinstance(iter_expr.get("func"), dict)
                and iter_expr.get("func", {}).get("kind") == "Name"
                and iter_expr.get("func", {}).get("id") == "range"
            ):
                rargs = list(iter_expr.get("args", []))
                start_node: dict[str, Any]
                stop_node: dict[str, Any]
                step_node: dict[str, Any]
                if len(rargs) == 1:
                    start_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        0,
                        resolved_type="int64",
                        repr_text="0",
                    )
                    stop_node = rargs[0]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                elif len(rargs) == 2:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = _sh_make_constant_expr(
                        _sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5),
                        1,
                        resolved_type="int64",
                        repr_text="1",
                    )
                else:
                    start_node = rargs[0]
                    stop_node = rargs[1]
                    step_node = rargs[2]
                tgt = str(target_expr.get("id", ""))
                if tgt != "":
                    name_types[tgt] = "int64"
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_for_range_stmt(
                        _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                        target_expr,
                        start_node,
                        stop_node,
                        step_node,
                        _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    ),
                )
                skip = j - i - 1
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_for_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    target_expr,
                    iter_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                    target_type=t_ty,
                    iter_mode=iter_mode,
                    iter_source_type=i_ty_norm if i_ty_norm != "" else "unknown",
                    iter_element_type=t_ty,
                ),
            )
            skip = j - i - 1
            continue

        m_import: re.Match | None = re.match(r"^import\s+(.+)$", s, flags=re.S)
        if m_import is not None:
            names_txt = re.strip_group(m_import, 1)
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="import statement has no module names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name == "typing":
                    # `typing` は注釈専用モジュールとして扱い、EAST 依存には積まない。
                    continue
                if mod_name == "dataclasses":
                    # `dataclasses` は decorator 解決専用モジュールとして扱い、EAST 依存には積まない。
                    bind_name_dc = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    _sh_register_import_module(_SH_IMPORT_MODULES, bind_name_dc, mod_name)
                    continue
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(_SH_IMPORT_MODULES, bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        aliases,
                    ),
                )
            continue

        import_from_clause = _sh_parse_import_from_clause(s)
        if import_from_clause is not None:
            mod_name, names_txt, mod_level = import_from_clause
            if mod_name == "typing":
                # `from typing import ...` は注釈解決専用で、EAST には出力しない。
                continue
            if mod_name == "dataclasses":
                # `from dataclasses import ...` は decorator 解決専用で、EAST には出力しない。
                if names_txt != "*":
                    raw_parts_dc: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts_dc.append(p2)
                    for part in raw_parts_dc:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_name, as_name_txt = parsed_alias
                        bind_name_dc = as_name_txt if as_name_txt != "" else sym_name
                        _sh_register_import_symbol(
                            _SH_IMPORT_SYMBOLS,
                            bind_name_dc,
                            mod_name,
                            sym_name,
                            make_import_symbol_binding=_sh_make_import_symbol_binding,
                        )
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from __future__ import annotations` only.",
                    )
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2: str = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                if len(raw_parts) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from-import statement has no symbol names",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(ln_no, 0, len(ln_txt)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                continue
            if names_txt == "*":
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                        level=mod_level,
                    ),
                )
                continue
            raw_parts: list[str] = []
            for p in names_txt.split(","):
                p2: str = p.strip()
                if p2 != "":
                    raw_parts.append(p2)
            if len(raw_parts) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message="from-import statement has no symbol names",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `from module import name` or `... as alias`.",
                    )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                _sh_register_import_symbol(
                    _SH_IMPORT_SYMBOLS,
                    bind_name,
                    mod_name,
                    sym_name,
                    make_import_symbol_binding=_sh_make_import_symbol_binding,
                )
                if _sh_is_host_only_alias(bind_name):
                    continue
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                pending_blank_count = _sh_push_stmt_with_trivia(
                    stmts,
                    pending_leading_trivia,
                    pending_blank_count,
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_stmt_span(merged_line_end, ln_no, 0, len(ln_txt)),
                        mod_name,
                        aliases,
                        level=mod_level,
                    ),
                )
            continue

        if s.startswith("with ") and s.endswith(":"):
            m_with: re.Match | None = re.match(r"^with\s+(.+)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", s, flags=re.S)
            if m_with is None:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse with statement: {s}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use `with expr as name:` form.",
                )
            ctx_txt = re.strip_group(m_with, 1)
            as_name = re.strip_group(m_with, 2)
            ctx_col = ln_txt.find(ctx_txt)
            as_col = ln_txt.find(as_name, ctx_col + len(ctx_txt))
            ctx_expr = _sh_parse_expr_lowered(ctx_txt, ln_no=ln_no, col=ctx_col, name_types=dict(name_types))
            name_types[as_name] = str(ctx_expr.get("resolved_type", "unknown"))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"with body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented with-body.",
                )
            assign_stmt = _sh_make_assign_stmt(
                _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)),
                _sh_make_name_expr(
                    _sh_span(ln_no, as_col, as_col + len(as_name)),
                    as_name,
                    resolved_type=str(ctx_expr.get("resolved_type", "unknown")),
                ),
                ctx_expr,
                declare=True,
                declare_init=True,
                decl_type=str(ctx_expr.get("resolved_type", "unknown")),
            )
            close_expr = _sh_parse_expr_lowered(f"{as_name}.close()", ln_no=ln_no, col=as_col, name_types=dict(name_types))
            try_stmt = _sh_make_try_stmt(
                _sh_block_end_span(body_lines, ln_no, ln_txt.find("with "), len(ln_txt), j),
                _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                finalbody=[_sh_make_expr_stmt(close_expr, _sh_stmt_span(merged_line_end, ln_no, as_col, len(ln_txt)))],
            )
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, assign_stmt)
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, try_stmt)
            skip = j - i - 1
            continue

        if s.startswith("while ") and s.endswith(":"):
            cond_txt = s[len("while ") : -1].strip()
            cond_col = ln_txt.find(cond_txt)
            cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
            body_block, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(body_block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"while body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented while-body.",
                )
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_while_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    cond_expr,
                    _sh_parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                ),
            )
            skip = j - i - 1
            continue

        if s == "try:":
            try_body, j = _sh_collect_indented_block(body_lines, i + 1, indent)
            if len(try_body) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"try body is missing in '{scope_label}'",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Add indented try-body.",
                )
            handlers: list[dict[str, Any]] = []
            finalbody: list[dict[str, Any]] = []
            while j < len(body_lines):
                h_no, h_ln = body_lines[j]
                h_s = h_ln.strip()
                h_indent = len(h_ln) - len(h_ln.lstrip(" "))
                if h_indent != indent:
                    break
                exc_clause = _sh_parse_except_clause(h_s)
                if exc_clause is not None:
                    ex_type_txt, ex_name = exc_clause
                    ex_type_col = h_ln.find(ex_type_txt)
                    if ex_type_col < 0:
                        ex_type_col = h_ln.find("except")
                        if ex_type_col < 0:
                            ex_type_col = 0
                    h_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    handlers.append(
                        _sh_make_except_handler(
                            _sh_parse_expr_lowered(
                                ex_type_txt,
                                ln_no=h_no,
                                col=ex_type_col,
                                name_types=dict(name_types),
                            ),
                            _sh_parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                            name=ex_name,
                        )
                    )
                    j = k
                    continue
                if h_s == "finally:":
                    f_body, k = _sh_collect_indented_block(body_lines, j + 1, indent)
                    finalbody = _sh_parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                    j = k
                    continue
                break
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_try_stmt(
                    _sh_block_end_span(body_lines, ln_no, 0, len(ln_txt), j),
                    _sh_parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
                    handlers=handlers,
                    finalbody=finalbody,
                ),
            )
            skip = j - i - 1
            continue

        if s.startswith("raise "):
            expr_txt = s[len("raise ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            cause_expr = None
            cause_split = _sh_split_top_level_from(expr_txt)
            if cause_split is not None:
                exc_txt, cause_txt = cause_split
                expr_txt = exc_txt
                expr_col = ln_txt.find(expr_txt)
                cause_col = ln_txt.find(cause_txt)
                cause_expr = _sh_parse_expr_lowered(cause_txt, ln_no=ln_no, col=cause_col, name_types=dict(name_types))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_raise_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ln_txt.find("raise "), len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    cause=cause_expr,
                )
            )
            continue

        if s == "pass":
            pass_stmt = _sh_make_pass_stmt(_sh_stmt_span(merged_line_end, ln_no, indent, indent + 4))
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, pass_stmt)
            continue

        if s == "return":
            rcol = ln_txt.find("return")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(_sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)))
            )
            continue

        if s.startswith("return "):
            rcol = ln_txt.find("return ")
            expr_txt = s[len("return ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = rcol + len("return ")
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_return_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, rcol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                )
            )
            continue

        if s == "yield":
            ycol = ln_txt.find("yield")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(_sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt))),
            )
            continue

        if s.startswith("yield "):
            ycol = ln_txt.find("yield ")
            expr_txt = s[len("yield ") :].strip()
            expr_col = ln_txt.find(expr_txt)
            if expr_col < 0:
                expr_col = ycol + len("yield ")
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_yield_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, ycol, len(ln_txt)),
                    _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                ),
            )
            continue

        parsed_typed = _sh_parse_typed_binding(s, allow_dotted_name=True)
        if parsed_typed is not None:
            typed_target, typed_ann, typed_default = parsed_typed
        else:
            typed_target, typed_ann, typed_default = "", "", ""
        if parsed_typed is not None and typed_default == "":
            target_txt = typed_target
            ann_txt = typed_ann
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=None,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        if parsed_typed is not None and typed_default != "":
            target_txt = typed_target
            ann_txt = typed_ann
            expr_txt = typed_default
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            expr_col = ln_txt.find(expr_txt)
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            _maybe_bind_self_field(target_expr, None, explicit=ann)
            if isinstance(target_expr, dict):
                target_expr["type_expr"] = ann_expr
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                name_types[str(target_expr.get("id", ""))] = ann
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_ann_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    ann,
                    annotation_type_expr=ann_expr,
                    value=val_expr,
                    declare=True,
                    decl_type=ann,
                    decl_type_expr=ann_expr,
                ),
            )
            continue

        parsed_aug = _sh_parse_augassign(s)
        if parsed_aug is not None:
            target_txt, aug_op, expr_txt = parsed_aug
            op_map = {
                "+=": "Add",
                "-=": "Sub",
                "*=": "Mult",
                "/=": "Div",
                "//=": "FloorDiv",
                "%=": "Mod",
                "&=": "BitAnd",
                "|=": "BitOr",
                "^=": "BitXor",
                "<<=": "LShift",
                ">>=": "RShift",
            }
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            target_ty = "unknown"
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
            decl_type: str | None = None
            if target_ty != "unknown":
                decl_type = target_ty
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                _sh_make_augassign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    op_map[aug_op],
                    val_expr,
                    declare=False,
                    decl_type=decl_type,
                )
            )
            continue

        m_tasg: re.Match | None = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
        if m_tasg is not None:
            n1 = re.group(m_tasg, 1)
            n2 = re.group(m_tasg, 2)
            expr_txt = re.strip_group(m_tasg, 3)
            expr_col = ln_txt.find(expr_txt)
            rhs = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            c1 = ln_txt.find(n1)
            c2 = ln_txt.find(n2, c1 + len(n1))
            if (
                isinstance(rhs, dict)
                and rhs.get("kind") == "Tuple"
                and len(rhs.get("elements", [])) == 2
                and isinstance(rhs.get("elements")[0], dict)
                and isinstance(rhs.get("elements")[1], dict)
                and rhs.get("elements")[0].get("kind") == "Name"
                and rhs.get("elements")[1].get("kind") == "Name"
                and str(rhs.get("elements")[0].get("id", "")) == n2
                and str(rhs.get("elements")[1].get("id", "")) == n1
            ):
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, 
                    _sh_make_swap_stmt(
                        _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c1, c1 + len(n1)),
                            n1,
                            resolved_type=name_types.get(n1, "unknown"),
                        ),
                        _sh_make_name_expr(
                            _sh_span(ln_no, c2, c2 + len(n2)),
                            n2,
                            resolved_type=name_types.get(n2, "unknown"),
                        ),
                    )
                )
                continue
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_tuple_destructure_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, c1, len(ln_txt)),
                    line_no=ln_no,
                    first_name=n1,
                    first_col=c1,
                    first_type=name_types.get(n1, "unknown"),
                    second_name=n2,
                    second_col=c2,
                    second_type=name_types.get(n2, "unknown"),
                    value=rhs,
                ),
            )
            continue

        asg_split = _sh_split_top_level_assign(s)
        if asg_split is not None:
            target_txt, expr_txt = asg_split
            expr_col = ln_txt.find(expr_txt)
            target_col = ln_txt.find(target_txt)
            target_expr = _sh_parse_expr_lowered(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
            val_expr = _sh_parse_expr_lowered(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            decl_type = val_expr.get("resolved_type", "unknown")
            _maybe_bind_self_field(target_expr, str(decl_type) if isinstance(decl_type, str) else "")
            if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                nm = str(target_expr.get("id", ""))
                if nm != "":
                    name_types[nm] = str(decl_type)
            pending_blank_count = _sh_push_stmt_with_trivia(
                stmts,
                pending_leading_trivia,
                pending_blank_count,
                _sh_make_assign_stmt(
                    _sh_stmt_span(merged_line_end, ln_no, target_col, len(ln_txt)),
                    target_expr,
                    val_expr,
                    declare=True,
                    declare_init=True,
                    decl_type=str(decl_type),
                ),
            )
            continue

        expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
        expr_stmt = _sh_parse_expr_lowered(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
        pending_blank_count = _sh_push_stmt_with_trivia(
            stmts,
            pending_leading_trivia,
            pending_blank_count,
            _sh_make_expr_stmt(expr_stmt, _sh_stmt_span(merged_line_end, ln_no, expr_col, len(ln_txt))),
        )
    return stmts


def _sh_parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
    """読み取り専用引数で受け取り、mutable 実体へコピーを渡す。"""
    body_lines_copy: list[tuple[int, str]] = list(body_lines)
    name_types_copy: dict[str, str] = dict(name_types)
    return _sh_parse_stmt_block_mutable(body_lines_copy, name_types=name_types_copy, scope_label=scope_label)

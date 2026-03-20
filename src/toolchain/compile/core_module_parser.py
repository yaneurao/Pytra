#!/usr/bin/env python3
"""Self-hosted module parser cluster for EAST core."""

from __future__ import annotations

from pytra.std import re
from typing import Any


def convert_source_to_east_self_hosted_impl(source: str, filename: str) -> dict[str, Any]:
    """Python ソースを self-hosted パーサで EAST Module に変換する。"""
    from toolchain.compile.core_module_parser_support import (
        _SH_CLASS_BASE,
        _SH_CLASS_METHOD_RETURNS,
        _SH_FN_RETURNS,
        _SH_IMPORT_MODULES,
        _SH_IMPORT_SYMBOLS,
        _SH_RUNTIME_ABI_ARG_MODES,
        _SH_RUNTIME_ABI_MODE_ALIASES,
        _SH_RUNTIME_ABI_RET_MODES,
        _SH_TEMPLATE_INSTANTIATION_MODE,
        _SH_TEMPLATE_SCOPE,
        _SH_TYPE_ALIASES,
        _make_east_build_error,
        _make_import_build_error,
        _sh_ann_to_type,
        _sh_ann_to_type_expr,
        _sh_append_import_binding,
        _sh_block_end_span,
        _sh_build_arg_usage_map,
        _sh_collect_extern_var_metadata,
        _sh_collect_function_runtime_decl_metadata,
        _sh_collect_dataclass_field_metadata,
        _sh_collect_indented_block,
        _sh_collect_nominal_adt_class_metadata,
        _sh_collect_yield_value_types,
        _sh_default_type_aliases,
        _sh_extract_leading_docstring,
        _sh_infer_return_type_for_untyped_def,
        _sh_import_binding_fields,
        _sh_is_abi_decorator,
        _sh_is_dataclass_decorator,
        _sh_is_host_only_alias,
        _sh_is_identifier,
        _sh_is_sealed_decorator,
        _sh_is_template_decorator,
        _sh_is_value_safe_dataclass_candidate,
        _sh_make_ann_assign_stmt,
        _sh_make_assign_stmt,
        _sh_make_class_def_stmt,
        _sh_make_decl_meta,
        _sh_make_def_sig_info,
        _sh_make_expr_stmt,
        _sh_make_function_def_stmt,
        _sh_make_if_stmt,
        _sh_make_import_alias,
        _sh_make_import_binding,
        _sh_make_import_from_stmt,
        _sh_make_import_resolution_binding,
        _sh_make_import_stmt,
        _sh_make_import_symbol_binding,
        _sh_make_module_root,
        _sh_make_name_expr,
        _sh_make_node,
        _sh_make_pass_stmt,
        _sh_make_qualified_symbol_ref,
        _sh_make_stmt_node,
        _sh_make_trivia_blank,
        _sh_make_trivia_comment,
        _sh_make_generator_return_type,
        _sh_merge_logical_lines,
        _sh_parse_class_header,
        _sh_parse_class_header_base_list,
        _sh_parse_dataclass_decorator_options,
        _sh_parse_decorator_head_and_args,
        _sh_parse_def_sig,
        _sh_parse_expr_lowered,
        _sh_parse_if_tail,
        _sh_parse_import_alias,
        _sh_parse_import_from_clause,
        _sh_parse_stmt_block,
        _sh_parse_typed_binding,
        _sh_raise_if_trailing_stmt_terminator,
        _sh_register_import_module,
        _sh_register_import_symbol,
        _sh_register_type_alias,
        _sh_reject_runtime_decl_class_decorators,
        _sh_reject_runtime_decl_method_decorator,
        _sh_reject_runtime_decl_nonfunction_decorators,
        _sh_set_parse_context,
        _sh_span,
        _sh_split_def_header_and_inline_stmt,
        _sh_split_top_commas,
        _sh_split_top_keyword,
        _sh_split_top_level_assign,
        _sh_split_top_level_colon,
        _sh_split_top_level_in,
        _sh_strip_inline_comment,
        _sh_strip_utf8_bom,
        _sh_typing_alias_to_type_name,
        sync_type_expr_mirrors,
        validate_runtime_abi_module,
        validate_template_module,
    )
    source = _sh_strip_utf8_bom(source)
    lines = source.splitlines()
    leading_file_comments: list[str] = []
    leading_file_trivia: list[dict[str, Any]] = []
    for ln in lines:
        s = ln.strip()
        if s == "":
            if len(leading_file_comments) > 0:
                leading_file_trivia.append(_sh_make_trivia_blank(1))
            continue
        if s.startswith("#"):
            text = s[1:].lstrip()
            leading_file_comments.append(text)
            leading_file_trivia.append(_sh_make_trivia_comment(text))
            continue
        break

    class_method_return_types: dict[str, dict[str, str]] = {}
    class_base: dict[str, str | None] = {}
    fn_returns: dict[str, str] = {}
    pre_import_symbol_bindings: dict[str, dict[str, str]] = {}
    pre_import_module_bindings: dict[str, str] = {}
    type_aliases: dict[str, str] = _sh_default_type_aliases()

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = _sh_strip_inline_comment(ln.strip())
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        if cur_cls is None and indent == 0:
            m_import = re.match(r"^import\s+(.+)$", s, flags=re.S)
            if m_import is not None:
                names_txt = re.strip_group(m_import, 1)
                raw_parts: list[str] = []
                for p in names_txt.split(","):
                    p2 = p.strip()
                    if p2 != "":
                        raw_parts.append(p2)
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                    if parsed_alias is None:
                        continue
                    mod_name, as_name_txt = parsed_alias
                    bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                    if bind_name != "":
                        pre_import_module_bindings[bind_name] = mod_name
                continue
            m_import_from = re.match(r"^from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+(.+)$", s, flags=re.S)
            if m_import_from is not None:
                mod_txt = re.strip_group(m_import_from, 1)
                names_txt = re.strip_group(m_import_from, 2)
                if names_txt != "*":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2 = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        if alias_name != "":
                            pre_import_symbol_bindings[alias_name] = _sh_make_import_symbol_binding(
                                mod_txt,
                                sym_txt,
                            )
                if mod_txt == "typing":
                    raw_parts: list[str] = []
                    for p in names_txt.split(","):
                        p2: str = p.strip()
                        if p2 != "":
                            raw_parts.append(p2)
                    for part in raw_parts:
                        parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                        if parsed_alias is None:
                            continue
                        sym_txt, as_name = parsed_alias
                        alias_name = as_name if as_name != "" else sym_txt
                        target = _sh_typing_alias_to_type_name(sym_txt)
                        if target != "":
                            type_aliases[alias_name] = target
                continue
            m_pep695_pre = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
            if m_pep695_pre is not None:
                # PEP 695 type alias: 名前を type_aliases に入れない（展開抑止）。
                # パーサーは名前をそのまま NamedType として扱う。
                continue
            asg_pre = _sh_split_top_level_assign(s)
            if asg_pre is not None:
                pre_left, pre_right = asg_pre
                _sh_register_type_alias(type_aliases, pre_left, pre_right)
                continue
        cls_hdr_info = _sh_parse_class_header_base_list(s, split_top_commas=_sh_split_top_commas)
        cls_hdr = _sh_parse_class_header(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr is not None:
            cur_cls_name, cur_base = cls_hdr
            cur_cls = cur_cls_name
            cur_cls_indent = indent
            if cur_base != "":
                class_base[cur_cls_name] = cur_base
            else:
                class_base[cur_cls_name] = None
            if cur_cls_name not in class_method_return_types:
                empty_methods: dict[str, str] = {}
                class_method_return_types[cur_cls_name] = empty_methods
            continue
        if cur_cls is None:
            sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
            sig = _sh_parse_def_sig(
                ln_no,
                sig_line_scan,
                type_aliases=_SH_TYPE_ALIASES,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
                make_def_sig_info=_sh_make_def_sig_info,
            )
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        cur_cls_name: str = cur_cls
        sig_line_scan, _inline_scan = _sh_split_def_header_and_inline_stmt(s)
        sig = _sh_parse_def_sig(
            ln_no,
            sig_line_scan,
            in_class=cur_cls_name,
            type_aliases=_SH_TYPE_ALIASES,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
            make_def_sig_info=_sh_make_def_sig_info,
        )
        if sig is not None:
            methods: dict[str, str] = class_method_return_types[cur_cls_name]
            methods[str(sig["name"])] = str(sig["ret"])
            class_method_return_types[cur_cls_name] = methods

    _sh_set_parse_context(fn_returns, class_method_return_types, class_base, type_aliases)
    _SH_IMPORT_SYMBOLS.clear()
    _SH_IMPORT_SYMBOLS.update(pre_import_symbol_bindings)
    _SH_IMPORT_MODULES.clear()
    _SH_IMPORT_MODULES.update(pre_import_module_bindings)

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    import_module_bindings: dict[str, str] = {}
    import_symbol_bindings: dict[str, dict[str, str]] = {}
    import_bindings: list[dict[str, Any]] = []
    import_binding_names: set[str] = set()
    first_item_attached = False
    pending_dataclass = False
    pending_dataclass_options: dict[str, bool] = {}
    pending_top_level_decorators: list[str] = []
    sealed_families: set[str] = set()

    top_lines: list[tuple[int, str]] = []
    line_idx = 1
    while line_idx <= len(lines):
        top_lines.append((line_idx, lines[line_idx - 1]))
        line_idx += 1
    top_merged_lines, top_merged_end = _sh_merge_logical_lines(top_lines)
    top_merged_map: dict[int, str] = {}
    top_merged_index: dict[int, int] = {}
    for top_idx, top_pair in enumerate(top_merged_lines):
        top_ln_no, top_txt = top_pair
        top_merged_map[int(top_ln_no)] = str(top_txt)
        top_merged_index[int(top_ln_no)] = int(top_idx)
    i = 1
    while i <= len(lines):
        ln_obj = top_merged_map.get(i, lines[i - 1])
        ln: str = str(ln_obj)
        logical_end_pair = top_merged_end.get(i, (i, len(lines[i - 1])))
        logical_end = int(logical_end_pair[0])
        raw_s = ln.strip()
        s = _sh_strip_inline_comment(raw_s)
        _sh_raise_if_trailing_stmt_terminator(
            s,
            line_no=i,
            line_text=ln,
            make_east_build_error=_make_east_build_error,
            make_span=_sh_span,
        )
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue
        if s.startswith("@"):
            dec_name = s[1:].strip()
            if _sh_is_dataclass_decorator(
                dec_name,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            ):
                pending_dataclass = True
                _dec_head, args_txt = _sh_parse_decorator_head_and_args(dec_name)
                if args_txt != "":
                    parsed_opts = _sh_parse_dataclass_decorator_options(
                        args_txt,
                        line_no=i,
                        line_text=ln,
                        split_top_commas=_sh_split_top_commas,
                        split_top_level_assign=_sh_split_top_level_assign,
                        is_identifier=_sh_is_identifier,
                        make_east_build_error=_make_east_build_error,
                        make_span=_sh_span,
                    )
                    for k_opt, v_opt in parsed_opts.items():
                        pending_dataclass_options[k_opt] = v_opt
            elif dec_name != "":
                pending_top_level_decorators.append(dec_name)
            i += 1
            continue

        ln_main = s
        is_main_guard = False
        if ln_main.startswith("if ") and ln_main.endswith(":"):
            cond = ln_main[3:-1].strip()
            if cond in {
                "__name__ == \"__main__\"",
                "__name__ == '__main__'",
                "\"__main__\" == __name__",
                "'__main__' == __name__",
            }:
                is_main_guard = True
        if is_main_guard:
            block: list[tuple[int, str]] = []
            if i < len(top_lines):
                block, block_end_idx = _sh_collect_indented_block(top_lines, i, 0)
                j = block_end_idx + 1
            main_name_types: dict[str, str] = {}
            main_stmts = _sh_parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue
        sig_line_full: str = s
        sig_line, inline_fn_stmt = _sh_split_def_header_and_inline_stmt(sig_line_full)
        sig_end_line = logical_end
        sig = _sh_parse_def_sig(
            i,
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
            block: list[tuple[int, str]] = []
            j = sig_end_line + 1
            if inline_fn_stmt != "":
                block = [(i, "    " + inline_fn_stmt)]
                j = i + 1
            else:
                block, block_end_idx = _sh_collect_indented_block(top_lines, j - 1, 0)
                j = block_end_idx + 1
                if len(block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                        source_span=_sh_span(i, 0, len(sig_line)),
                        hint="Add return or assignment statements in function body.",
                    )
            fn_scope_types: dict[str, str] = dict(arg_types)
            if vararg_name != "":
                fn_scope_types[vararg_name] = f"list[{vararg_type if vararg_type != '' else 'unknown'}]"
            stmts = _sh_parse_stmt_block(block, name_types=fn_scope_types, scope_label=fn_name)
            docstring, stmts = _sh_extract_leading_docstring(stmts)
            fn_ret = _sh_infer_return_type_for_untyped_def(fn_ret, stmts)
            yield_types = _sh_collect_yield_value_types(stmts)
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
            arg_usage_map = _sh_build_arg_usage_map(arg_order, arg_types, stmts)
            for arg_name in arg_order:
                if arg_name in arg_defaults_raw:
                    default_obj: Any = arg_defaults_raw[arg_name]
                    default_txt: str = str(default_obj).strip()
                    if default_txt != "":
                        default_col = sig_line.find(default_txt)
                        if default_col < 0:
                            default_col = 0
                        arg_defaults[arg_name] = _sh_parse_expr_lowered(
                            default_txt,
                            ln_no=i,
                            col=default_col,
                            name_types=fn_scope_types,
                        )
            fn_decorators = list(pending_top_level_decorators)
            pending_top_level_decorators = []
            for decorator_text in fn_decorators:
                if _sh_is_sealed_decorator(decorator_text):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@sealed is supported on top-level classes only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Move `@sealed` to a family class declaration.",
                    )
            runtime_abi_meta, template_meta = _sh_collect_function_runtime_decl_metadata(
                fn_decorators,
                arg_order=arg_order,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                parse_decorator_head_and_args=_sh_parse_decorator_head_and_args,
                split_top_commas=_sh_split_top_commas,
                split_top_level_assign=_sh_split_top_level_assign,
                split_top_level_colon=_sh_split_top_level_colon,
                is_identifier=_sh_is_identifier,
                runtime_abi_arg_modes=_SH_RUNTIME_ABI_ARG_MODES,
                runtime_abi_ret_modes=_SH_RUNTIME_ABI_RET_MODES,
                runtime_abi_mode_aliases=_SH_RUNTIME_ABI_MODE_ALIASES,
                template_scope=_SH_TEMPLATE_SCOPE,
                template_instantiation_mode=_SH_TEMPLATE_INSTANTIATION_MODE,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            item = _sh_make_function_def_stmt(
                fn_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                arg_types,
                arg_order,
                fn_ret_effective,
                stmts,
                arg_type_exprs=arg_type_exprs,
                arg_defaults=arg_defaults,
                arg_index=arg_index_map,
                return_type_expr=fn_ret_type_expr,
                arg_usage=arg_usage_map,
                decorators=list(fn_decorators) if len(fn_decorators) > 0 else None,
                leading_comments=[],
                leading_trivia=[],
                docstring=docstring,
                is_generator=is_generator,
                yield_value_type=yield_value_type,
                vararg_name=vararg_name,
                vararg_type=vararg_type,
                vararg_type_expr=vararg_type_expr,
            )
            if runtime_abi_meta is not None or template_meta is not None:
                item["meta"] = _sh_make_decl_meta(
                    runtime_abi_v1=runtime_abi_meta,
                    template_v1=template_meta,
                )
            fn_returns[fn_name] = fn_ret_effective
            _SH_FN_RETURNS[fn_name] = fn_ret_effective
            if not first_item_attached:
                item["leading_comments"] = list(leading_file_comments)
                item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(item)
            i = j
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
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `import module` or `import module as alias`.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=True)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `import module` or `import module as alias` form.",
                    )
                mod_name, as_name_txt = parsed_alias
                if mod_name in {"typing", "dataclasses", "enum", "collections"}:
                    pytra_mod = f"pytra.std.{mod_name}" if mod_name == "collections" else f"pytra.{mod_name}"
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"import {mod_name} is not allowed. Use `from {pytra_mod} import ...` instead.",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint=f"Replace with: from pytra.{mod_name} import ...",
                    )
                bind_name = as_name_txt if as_name_txt != "" else mod_name.split(".")[0]
                _sh_register_import_module(_SH_IMPORT_MODULES, bind_name, mod_name)
                if _sh_is_host_only_alias(bind_name):
                    continue
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="",
                    local_name=bind_name,
                    binding_kind="module",
                    source_file=filename,
                    source_line=i,
                    make_east_build_error=_make_east_build_error,
                    make_import_build_error=_make_import_build_error,
                    make_span=_sh_span,
                    make_import_binding=_sh_make_import_binding,
                )
                aliases.append(_sh_make_import_alias(mod_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(_sh_make_import_stmt(_sh_make_stmt_node, _sh_span(i, 0, len(ln)), aliases))
            i = logical_end + 1
            continue
        import_from_clause = _sh_parse_import_from_clause(s)
        if import_from_clause is not None:
            mod_name, names_txt, mod_level = import_from_clause
            if mod_name in {"enum", "collections"}:
                pytra_mod = f"pytra.std.{mod_name}" if mod_name == "collections" else f"pytra.{mod_name}"
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"from {mod_name} import ... is not allowed. Use `from {pytra_mod} import ...` instead.",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint=f"Replace with: from {pytra_mod} import ...",
                )
            if mod_name in {"typing", "dataclasses", "pytra.types", "pytra.typing", "pytra.enum", "pytra.dataclasses"}:
                # 言語補助モジュール: パーサーが型名・構文を既に認識しているため、import を無視する。
                i = logical_end + 1
                continue
            if mod_name == "__future__":
                if names_txt == "*":
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="from __future__ import * is not supported",
                        source_span=_sh_span(i, 0, len(ln)),
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
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` form.",
                    )
                for part in raw_parts:
                    parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                    if parsed_alias is None:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported from-import clause: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Use `from module import name` or `... as alias`.",
                        )
                    sym_name, as_name_txt = parsed_alias
                    if sym_name != "annotations" or as_name_txt != "":
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message=f"unsupported __future__ feature: {part}",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Only `from __future__ import annotations` is supported.",
                        )
                # `from __future__ import annotations` is frontend-only and does not appear in EAST.
                i = logical_end + 1
                continue
            if names_txt == "*":
                wildcard_local = "__wildcard__" + mod_name.replace(".", "_")
                _sh_append_import_binding(
                    import_bindings=import_bindings,
                    import_binding_names=import_binding_names,
                    module_id=mod_name,
                    export_name="*",
                    local_name=wildcard_local,
                    binding_kind="wildcard",
                    source_file=filename,
                    source_line=i,
                    make_east_build_error=_make_east_build_error,
                    make_import_build_error=_make_import_build_error,
                    make_span=_sh_span,
                    make_import_binding=_sh_make_import_binding,
                )
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        [_sh_make_import_alias("*")],
                        level=mod_level,
                    )
                )
                i = logical_end + 1
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
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Use `from module import name` form.",
                )
            aliases: list[dict[str, str | None]] = []
            for part in raw_parts:
                parsed_alias = _sh_parse_import_alias(part, allow_dotted_name=False)
                if parsed_alias is None:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"unsupported from-import clause: {part}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `from module import name` or `... as alias`.",
                )
                sym_name, as_name_txt = parsed_alias
                bind_name = as_name_txt if as_name_txt != "" else sym_name
                if _sh_is_host_only_alias(bind_name):
                    _sh_register_import_symbol(
                        _SH_IMPORT_SYMBOLS,
                        bind_name,
                        mod_name,
                        sym_name,
                        make_import_symbol_binding=_sh_make_import_symbol_binding,
                    )
                    continue
                # `Enum/IntEnum/IntFlag` は class 定義の lowering で吸収されるため、
                # 依存ヘッダ解決用の ImportBinding には積まない。
                if not (mod_name in {"enum", "pytra.std.enum"} and sym_name in {"Enum", "IntEnum", "IntFlag"}):
                    _sh_append_import_binding(
                        import_bindings=import_bindings,
                        import_binding_names=import_binding_names,
                        module_id=mod_name,
                        export_name=sym_name,
                        local_name=bind_name,
                        binding_kind="symbol",
                        source_file=filename,
                        source_line=i,
                        make_east_build_error=_make_east_build_error,
                        make_import_build_error=_make_import_build_error,
                        make_span=_sh_span,
                        make_import_binding=_sh_make_import_binding,
                    )
                    import_symbol_bindings[bind_name] = _sh_make_import_symbol_binding(
                        mod_name,
                        sym_name,
                    )
                    _sh_register_import_symbol(
                        _SH_IMPORT_SYMBOLS,
                        bind_name,
                        mod_name,
                        sym_name,
                        make_import_symbol_binding=_sh_make_import_symbol_binding,
                    )
                aliases.append(_sh_make_import_alias(sym_name, as_name_txt if as_name_txt != "" else None))
            if len(aliases) > 0:
                body_items.append(
                    _sh_make_import_from_stmt(
                        _sh_make_stmt_node,
                        _sh_span(i, 0, len(ln)),
                        mod_name,
                        aliases,
                        level=mod_level,
                    )
                )
            i = logical_end + 1
            continue
        cls_hdr_info = _sh_parse_class_header_base_list(s, split_top_commas=_sh_split_top_commas)
        pending_mixin_bases: list[str] = []
        if cls_hdr_info is not None:
            _cls_name_info, bases_info = cls_hdr_info
            if len(bases_info) > 1:
                # Store additional bases (2nd, 3rd, ...) as mixin bases for later expansion.
                pending_mixin_bases = [b for b in bases_info[1:] if b != ""]
        cls_hdr = _sh_parse_class_header(s, split_top_commas=_sh_split_top_commas)
        if cls_hdr is not None:
            class_decorators = list(pending_top_level_decorators)
            pending_top_level_decorators = []
            _sh_reject_runtime_decl_class_decorators(
                class_decorators,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            cls_name, base = cls_hdr
            base_name = base
            is_enum_base = base_name in {"Enum", "IntEnum", "IntFlag"}
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    block.append((j, bl))
                    j += 1
                    continue
                bind = len(bl) - len(bl.lstrip(" "))
                if bind <= cls_indent:
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty class body '{cls_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add field or method definitions.",
                )
            class_block, _class_line_end = _sh_merge_logical_lines(block)

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            pending_method_decorators: list[str] = []
            class_storage_hint_override = ""
            k = 0
            while k < len(class_block):
                ln_no_raw, ln_txt_raw = class_block[k]
                ln_no = int(ln_no_raw)
                ln_txt: str = str(ln_txt_raw)
                s2 = re.sub(r"\s+#.*$", "", ln_txt).strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if s2 == "":
                    k += 1
                    continue
                if bind == cls_indent + 4 and s2.startswith("@"):
                    dec_name = s2[1:].strip()
                    if dec_name != "":
                        _sh_reject_runtime_decl_method_decorator(
                            dec_name,
                            import_module_bindings=import_module_bindings,
                            import_symbol_bindings=import_symbol_bindings,
                            line_no=ln_no,
                            line_text=ln_txt,
                            is_abi_decorator=_sh_is_abi_decorator,
                            is_template_decorator=_sh_is_template_decorator,
                            make_east_build_error=_make_east_build_error,
                            make_span=_sh_span,
                        )
                        if _sh_is_sealed_decorator(dec_name):
                            raise _make_east_build_error(
                                kind="unsupported_syntax",
                                message="@sealed is not supported on methods",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Use @sealed on top-level family classes only.",
                            )
                        pending_method_decorators.append(dec_name)
                    k += 1
                    continue
                if bind == cls_indent + 4 and (s2.startswith('"""') or s2.startswith("'''")):
                    q = s2[:3]
                    if s2.count(q) >= 2 and len(s2) > 3:
                        k += 1
                        continue
                    k += 1
                    while k < len(class_block):
                        _doc_no, doc_txt = class_block[k]
                        if q in doc_txt:
                            k += 1
                            break
                        k += 1
                    continue
                if bind == cls_indent + 4:
                    if s2 == "pass":
                        class_body.append(
                            _sh_make_pass_stmt(_sh_span(ln_no, 0, len(ln_txt)))
                        )
                        k += 1
                        continue
                    if s2.startswith("__pytra_class_storage_hint__") or s2.startswith("__pytra_storage_hint__"):
                        parts = s2.split("=", 1)
                        if len(parts) == 2:
                            rhs = parts[1].strip()
                            if rhs in {'"value"', "'value'"}:
                                class_storage_hint_override = "value"
                                k += 1
                                continue
                            if rhs in {'"ref"', "'ref'"}:
                                class_storage_hint_override = "ref"
                                k += 1
                                continue
                    parsed_field = _sh_parse_typed_binding(s2, allow_dotted_name=False)
                    if parsed_field is not None:
                        fname, fty_txt, fdefault = parsed_field
                        fty = _sh_ann_to_type(fty_txt, type_aliases=_SH_TYPE_ALIASES)
                        fty_expr = _sh_ann_to_type_expr(fty, type_aliases=_SH_TYPE_ALIASES)
                        field_types[fname] = fty
                        val_node: dict[str, Any] | None = None
                        field_meta: dict[str, Any] | None = None
                        if fdefault != "":
                            fexpr_txt = fdefault.strip()
                            fexpr_col = ln_txt.find(fexpr_txt)
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={})
                            if pending_dataclass:
                                field_meta = _sh_collect_dataclass_field_metadata(
                                    val_node,
                                    import_module_bindings=import_module_bindings,
                                    import_symbol_bindings=import_symbol_bindings,
                                    line_no=ln_no,
                                    line_text=ln_txt,
                                    make_east_build_error=_make_east_build_error,
                                    make_span=_sh_span,
                                )
                                if field_meta is not None:
                                    val_node = None
                        class_body.append(
                            _sh_make_ann_assign_stmt(
                                _sh_span(ln_no, ln_txt.find(fname), len(ln_txt)),
                                _sh_make_name_expr(
                                    _sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + len(fname)),
                                    fname,
                                    resolved_type=fty,
                                    type_expr=fty_expr,
                                ),
                                fty,
                                annotation_type_expr=fty_expr,
                                value=val_node,
                                declare=True,
                                decl_type=fty,
                                decl_type_expr=fty_expr,
                                meta=_sh_make_decl_meta(dataclass_field_v1=field_meta) if field_meta is not None else None,
                            )
                        )
                        k += 1
                        continue
                    class_assign = _sh_split_top_level_assign(s2)
                    if class_assign is not None:
                        fname, fexpr_txt = class_assign
                        fname = fname.strip()
                        fexpr_txt = fexpr_txt.strip()
                        if _sh_is_identifier(fname) and fexpr_txt != "":
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    if is_enum_base:
                        enum_assign = _sh_split_top_level_assign(s2)
                        if enum_assign is not None:
                            fname, fexpr_txt = enum_assign
                            fname = fname.strip()
                            fexpr_txt = fexpr_txt.strip()
                            if not _sh_is_identifier(fname) or fexpr_txt == "":
                                k += 1
                                continue
                            name_col = ln_txt.find(fname)
                            if name_col < 0:
                                name_col = 0
                            expr_col = ln_txt.find(fexpr_txt, name_col + len(fname))
                            if expr_col < 0:
                                expr_col = name_col + len(fname) + 1
                            val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no=ln_no, col=expr_col, name_types={})
                            class_body.append(
                                _sh_make_assign_stmt(
                                    _sh_span(ln_no, name_col, len(ln_txt)),
                                    _sh_make_name_expr(
                                        _sh_span(ln_no, name_col, name_col + len(fname)),
                                        fname,
                                        resolved_type=str(val_node.get("resolved_type", "unknown")),
                                    ),
                                    val_node,
                                    declare=True,
                                    declare_init=True,
                                    decl_type=str(val_node.get("resolved_type", "unknown")),
                                )
                            )
                            k += 1
                            continue
                    sig_line, inline_method_stmt = _sh_split_def_header_and_inline_stmt(s2)
                    sig = _sh_parse_def_sig(
                        ln_no,
                        sig_line,
                        in_class=cls_name,
                        type_aliases=_SH_TYPE_ALIASES,
                        make_east_build_error=_make_east_build_error,
                        make_span=_sh_span,
                        make_def_sig_info=_sh_make_def_sig_info,
                    )
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types: dict[str, str] = dict(sig["arg_types"])
                        marg_order: list[str] = list(sig["arg_order"])
                        marg_defaults_raw_obj: Any = sig.get("arg_defaults")
                        marg_defaults_raw: dict[str, Any] = marg_defaults_raw_obj if isinstance(marg_defaults_raw_obj, dict) else {}
                        mvararg_name = str(sig.get("vararg_name", ""))
                        mvararg_type = str(sig.get("vararg_type", ""))
                        mvararg_type_expr_obj: Any = sig.get("vararg_type_expr")
                        mvararg_type_expr = mvararg_type_expr_obj if isinstance(mvararg_type_expr_obj, dict) else None
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        if inline_method_stmt != "":
                            method_block = [(ln_no, " " * (bind + 4) + inline_method_stmt)]
                        else:
                            while m < len(class_block):
                                n_pair: tuple[int, str] = class_block[m]
                                n_no: int = int(n_pair[0])
                                n_txt: str = str(n_pair[1])
                                if n_txt.strip() == "":
                                    t = m + 1
                                    while t < len(class_block) and class_block[t][1].strip() == "":
                                        t += 1
                                    if t >= len(class_block):
                                        break
                                    t_pair: tuple[int, str] = class_block[t]
                                    t_txt: str = str(t_pair[1])
                                    t_indent = len(t_txt) - len(t_txt.lstrip(" "))
                                    if t_indent <= bind:
                                        break
                                    method_block.append((n_no, n_txt))
                                    m += 1
                                    continue
                                n_indent = len(n_txt) - len(n_txt.lstrip(" "))
                                if n_indent <= bind:
                                    break
                                method_block.append((n_no, n_txt))
                                m += 1
                            if len(method_block) == 0:
                                raise _make_east_build_error(
                                    kind="unsupported_syntax",
                                    message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                    hint="Add method statements.",
                                )
                        local_types: dict[str, str] = dict(marg_types)
                        if mvararg_name != "":
                            local_types[mvararg_name] = f"list[{mvararg_type if mvararg_type != '' else 'unknown'}]"
                        field_names: list[str] = list(field_types.keys())
                        for fnm in field_names:
                            fty: str = field_types[fnm]
                            local_types[fnm] = fty
                        stmts = _sh_parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        docstring, stmts = _sh_extract_leading_docstring(stmts)
                        mret = _sh_infer_return_type_for_untyped_def(mret, stmts)
                        yield_types = _sh_collect_yield_value_types(stmts)
                        is_generator = len(yield_types) > 0
                        mret_effective = mret
                        yield_value_type = "unknown"
                        if is_generator:
                            mret_effective, yield_value_type = _sh_make_generator_return_type(mret, yield_types)
                        marg_defaults: dict[str, Any] = {}
                        for arg_name in marg_order:
                            if arg_name in marg_defaults_raw:
                                default_obj: Any = marg_defaults_raw[arg_name]
                                default_txt: str = str(default_obj).strip()
                                if default_txt != "":
                                    default_col = ln_txt.find(default_txt)
                                    if default_col < 0:
                                        default_col = bind
                                    marg_defaults[arg_name] = _sh_parse_expr_lowered(
                                        default_txt,
                                        ln_no=ln_no,
                                        col=default_col,
                                        name_types=local_types,
                                    )
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            st_value = st.get("value")
                                            st_value_rt: Any = None
                                            if isinstance(st_value, dict):
                                                st_value_rt = st_value.get("resolved_type")
                                            t_val: Any = st.get("decl_type")
                                            if not isinstance(t_val, str) or t_val == "":
                                                t_val = st_value_rt
                                            if isinstance(t_val, str) and t_val != "":
                                                field_types[fname] = t_val
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    tgt_value: Any = None
                                    if isinstance(tgt, dict):
                                        tgt_value = tgt.get("value")
                                    tgt_value_dict: dict[str, Any] | None = None
                                    if isinstance(tgt_value, dict):
                                        tgt_value_dict = tgt_value
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and tgt_value_dict is not None
                                        and tgt_value_dict.get("kind") == "Name"
                                        and tgt_value_dict.get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
                        arg_index_map: dict[str, int] = {}
                        arg_pos = 0
                        while arg_pos < len(marg_order):
                            arg_name = marg_order[arg_pos]
                            arg_index_map[arg_name] = arg_pos
                            arg_pos += 1
                        arg_usage_map = _sh_build_arg_usage_map(marg_order, marg_types, stmts)
                        if cls_name in class_method_return_types:
                            methods_map = class_method_return_types[cls_name]
                            methods_map[mname] = mret_effective
                            class_method_return_types[cls_name] = methods_map
                        if cls_name in _SH_CLASS_METHOD_RETURNS:
                            methods_map2 = _SH_CLASS_METHOD_RETURNS[cls_name]
                            methods_map2[mname] = mret_effective
                            _SH_CLASS_METHOD_RETURNS[cls_name] = methods_map2
                        class_body.append(
                            _sh_make_function_def_stmt(
                                mname,
                                _sh_block_end_span(method_block, ln_no, bind, len(ln_txt), len(method_block)),
                                marg_types,
                                marg_order,
                                mret_effective,
                                stmts,
                                arg_defaults=marg_defaults,
                                arg_index=arg_index_map,
                                arg_usage=arg_usage_map,
                                decorators=list(pending_method_decorators),
                                docstring=docstring,
                                is_generator=is_generator,
                                yield_value_type=yield_value_type,
                                vararg_name=mvararg_name,
                                vararg_type=mvararg_type,
                                vararg_type_expr=mvararg_type_expr,
                            )
                        )
                        pending_method_decorators = []
                        k = m
                        continue
                raise _make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            storage_hint_override = class_storage_hint_override
            base_value: str | None = None
            if base != "":
                base_value = base
            class_meta = _sh_collect_nominal_adt_class_metadata(
                cls_name,
                base=base_value,
                decorators=class_decorators,
                is_dataclass=pending_dataclass,
                field_types=field_types,
                line_no=i,
                line_text=ln,
                sealed_families=sealed_families,
                is_sealed_decorator=_sh_is_sealed_decorator,
                parse_decorator_head_and_args=_sh_parse_decorator_head_and_args,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )

            cls_item = _sh_make_class_def_stmt(
                cls_name,
                _sh_block_end_span(block, i, 0, len(ln), len(block)),
                field_types,
                class_body,
                base=base_value,
                dataclass=pending_dataclass,
                dataclass_options=dict(pending_dataclass_options) if len(pending_dataclass_options) > 0 else None,
                decorators=list(class_decorators) if len(class_decorators) > 0 else None,
                meta=class_meta,
                mixin_bases=list(pending_mixin_bases) if len(pending_mixin_bases) > 0 else None,
            )
            static_field_names: set[str] = set()
            if not pending_dataclass:
                for st in class_body:
                    if st.get("kind") == "AnnAssign":
                        tgt = st.get("target")
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            fname = str(tgt.get("id", ""))
                            if fname != "":
                                static_field_names.add(fname)
            has_del = any(
                isinstance(st, dict) and st.get("kind") == "FunctionDef" and st.get("name") == "__del__"
                for st in class_body
            )
            instance_field_names: set[str] = set()
            for field_name in field_types.keys():
                if field_name not in static_field_names:
                    instance_field_names.add(field_name)
            # conservative hint:
            # - classes with instance state / __del__ / inheritance should keep reference semantics
            # - stateless, non-inherited classes can be value candidates
            if storage_hint_override != "":
                cls_item["class_storage_hint"] = storage_hint_override
            elif _sh_is_value_safe_dataclass_candidate(
                is_dataclass=pending_dataclass,
                base=base,
                has_del=has_del,
                class_body=class_body,
                field_types=field_types,
            ):
                cls_item["class_storage_hint"] = "value"
            elif base_name in {"Enum", "IntEnum", "IntFlag"}:
                cls_item["class_storage_hint"] = "value"
            elif len(instance_field_names) == 0 and not has_del and base == "":
                cls_item["class_storage_hint"] = "value"
            else:
                cls_item["class_storage_hint"] = "ref"
            if isinstance(class_meta, dict):
                nominal_adt_meta = class_meta.get("nominal_adt_v1")
                if isinstance(nominal_adt_meta, dict) and nominal_adt_meta.get("role") == "family":
                    sealed_families.add(cls_name)
            pending_dataclass = False
            pending_dataclass_options.clear()
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        if len(pending_top_level_decorators) > 0:
            for decorator_text in pending_top_level_decorators:
                if _sh_is_sealed_decorator(decorator_text):
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="@sealed is supported on top-level classes only",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Place `@sealed` immediately above a family class definition.",
                    )
            _sh_reject_runtime_decl_nonfunction_decorators(
                pending_top_level_decorators,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
                line_no=i,
                line_text=ln,
                is_abi_decorator=_sh_is_abi_decorator,
                is_template_decorator=_sh_is_template_decorator,
                make_east_build_error=_make_east_build_error,
                make_span=_sh_span,
            )
            pending_top_level_decorators = []

        top_indent = len(ln) - len(ln.lstrip(" "))
        if s.startswith("if ") and s.endswith(":"):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                then_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                if len(then_block) == 0:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message="if body is missing in 'module'",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Add indented if-body.",
                    )
                _else_stmt_list, j_idx = _sh_parse_if_tail(
                    start_idx=j_idx,
                    parent_indent=top_indent,
                    body_lines=top_merged_lines,
                    name_types={},
                    scope_label="module",
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
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        if s.startswith("for "):
            cur_idx_obj = top_merged_index.get(i)
            if isinstance(cur_idx_obj, int):
                cur_idx = int(cur_idx_obj)
                for_full = s[len("for ") :].strip()
                inline_for = False
                if not for_full.endswith(":"):
                    inline_for = _sh_split_top_level_colon(for_full) is not None
                j_idx = cur_idx + 1
                if for_full.endswith(":"):
                    body_block, j_idx = _sh_collect_indented_block(top_merged_lines, cur_idx + 1, top_indent)
                    if len(body_block) == 0:
                        raise _make_east_build_error(
                            kind="unsupported_syntax",
                            message="for body is missing in 'module'",
                            source_span=_sh_span(i, 0, len(ln)),
                            hint="Add indented for-body.",
                        )
                elif not inline_for:
                    raise _make_east_build_error(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(i, 0, len(ln)),
                        hint="Use `for target in iterable:` form.",
                    )
                stmt_chunk = top_merged_lines[cur_idx:j_idx]
                parsed_items = _sh_parse_stmt_block(stmt_chunk, name_types={}, scope_label="module")
                if not first_item_attached and len(parsed_items) > 0:
                    first_item = parsed_items[0]
                    if isinstance(first_item, dict):
                        first_item["leading_comments"] = list(leading_file_comments)
                        first_item["leading_trivia"] = list(leading_file_trivia)
                        first_item_attached = True
                for parsed_item in parsed_items:
                    body_items.append(parsed_item)
                if j_idx < len(top_merged_lines):
                    i = int(top_merged_lines[j_idx][0])
                else:
                    i = len(lines) + 1
                continue

        parsed_top_typed = _sh_parse_typed_binding(s, allow_dotted_name=False)
        if parsed_top_typed is not None:
            top_name, top_ann, top_default = parsed_top_typed
        else:
            top_name, top_ann, top_default = "", "", ""
        if parsed_top_typed is not None and top_default != "":
            name = top_name
            ann_txt = top_ann
            expr_txt = top_default
            ann = _sh_ann_to_type(ann_txt, type_aliases=_SH_TYPE_ALIASES)
            ann_expr = _sh_ann_to_type_expr(ann, type_aliases=_SH_TYPE_ALIASES)
            expr_col = ln.find(expr_txt)
            value_expr = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            ann_item = _sh_make_ann_assign_stmt(
                _sh_span(i, ln.find(name), len(ln)),
                _sh_make_name_expr(
                    _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                    name,
                    resolved_type=ann,
                    type_expr=ann_expr,
                ),
                ann,
                annotation_type_expr=ann_expr,
                value=value_expr,
                declare=True,
                decl_type=ann,
                decl_type_expr=ann_expr,
            )
            extern_var_meta = _sh_collect_extern_var_metadata(
                target_name=name,
                annotation=ann,
                value_expr=value_expr,
                import_module_bindings=import_module_bindings,
                import_symbol_bindings=import_symbol_bindings,
            )
            if extern_var_meta is not None:
                ann_item["meta"] = _sh_make_decl_meta(extern_var_v1=extern_var_meta)
            body_items.append(ann_item)
            i = logical_end + 1
            continue

        m_pep695 = re.match(r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
        if m_pep695 is not None:
            alias_name = re.strip_group(m_pep695, 1)
            alias_rhs = re.strip_group(m_pep695, 2).strip()
            normalized = _sh_ann_to_type(alias_rhs, type_aliases=_SH_TYPE_ALIASES)
            if normalized == "" or normalized == "unknown":
                normalized = alias_rhs
            body_items.append(
                _sh_make_node("TypeAlias", source_span=_sh_span(i, 0, len(ln)), name=alias_name, type_expr=normalized)
            )
            i = logical_end + 1
            continue
        asg_top = _sh_split_top_level_assign(s)
        if asg_top is not None:
            asg_left, asg_right = asg_top
            target_txt = asg_left.strip()
            expr_txt = asg_right.strip()
            expr_col = ln.find(expr_txt)
            if expr_col < 0:
                expr_col = 0
            target_col = ln.find(target_txt)
            if target_col < 0:
                target_col = 0
            target_node = _sh_parse_expr_lowered(target_txt, ln_no=i, col=target_col, name_types={})
            val_node = _sh_parse_expr_lowered(expr_txt, ln_no=i, col=expr_col, name_types={})
            decl_type = str(val_node.get("resolved_type", "unknown"))
            declare_name = isinstance(target_node, dict) and target_node.get("kind") == "Name"
            body_items.append(
                _sh_make_assign_stmt(
                    _sh_span(i, target_col, len(ln)),
                    target_node,
                    val_node,
                    declare=declare_name,
                    declare_init=declare_name,
                    decl_type=decl_type if declare_name else None,
                )
            )
            i = logical_end + 1
            continue

        if (s.startswith('"""') and s.endswith('"""')) or (s.startswith("'''") and s.endswith("'''")):
            # Module-level docstring / standalone string expression.
            body_items.append(
                _sh_make_expr_stmt(
                    _sh_parse_expr_lowered(s, ln_no=i, col=0, name_types={}),
                    _sh_span(i, 0, len(ln)),
                )
            )
            i = logical_end + 1
            continue

        expr_col = len(ln) - len(ln.lstrip(" "))
        body_items.append(
            _sh_make_expr_stmt(
                _sh_parse_expr_lowered(s, ln_no=i, col=expr_col, name_types={}),
                _sh_span(i, expr_col, len(ln)),
            )
        )
        i = logical_end + 1
        continue

    renamed_symbols: dict[str, str] = {}
    for item in body_items:
        if item.get("kind") == "FunctionDef" and item.get("name") == "main":
            renamed_symbols["main"] = "__pytra_main"
            item["name"] = "__pytra_main"

    # 互換メタデータは ImportBinding 正本から導出する。
    import_module_bindings = {}
    import_symbol_bindings = {}
    qualified_symbol_refs: list[dict[str, str]] = []
    import_resolution_bindings: list[dict[str, Any]] = []
    for binding in import_bindings:
        import_resolution_bindings.append(
            _sh_make_import_resolution_binding(binding, make_import_binding=_sh_make_import_binding)
        )
        module_id, export_name, local_name, binding_kind, _source_file, _source_line = _sh_import_binding_fields(binding)
        if module_id == "" or local_name == "":
            continue
        if binding_kind == "module":
            import_module_bindings[local_name] = module_id
            continue
        if binding_kind == "symbol" and export_name != "":
            import_symbol_bindings[local_name] = _sh_make_import_symbol_binding(module_id, export_name)
            qualified_symbol_refs.append(_sh_make_qualified_symbol_ref(module_id, export_name, local_name))

    out = _sh_make_module_root(
        filename=filename,
        body_items=body_items,
        main_stmts=main_stmts,
        renamed_symbols=renamed_symbols,
        import_resolution_bindings=import_resolution_bindings,
        qualified_symbol_refs=qualified_symbol_refs,
        import_bindings=import_bindings,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
        make_node=_sh_make_node,
    )
    sync_type_expr_mirrors(out)
    return validate_template_module(validate_runtime_abi_module(out))

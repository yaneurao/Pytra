#!/usr/bin/env python3
"""Prepare selfhost/py2cpp.py as a self-contained source.

This script inlines CodeEmitter into the C++ CLI source so transpiling selfhost input
no longer depends on cross-module import resolution.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CPP = ROOT / "src" / "backends" / "cpp" / "cli.py"
SRC_BASE = ROOT / "src" / "backends" / "common" / "emitter" / "code_emitter.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cpp.py"
SRC_TRANSPILE_CLI = ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py"
SRC_IMPORT_GRAPH_ANALYSIS_HELPERS = ROOT / "src" / "toolchain" / "frontends" / "import_graph_analysis_helpers.py"
SRC_IMPORT_GRAPH_FRONTEND_HELPERS = ROOT / "src" / "toolchain" / "frontends" / "import_graph_frontend_helpers.py"
SRC_IMPORT_GRAPH_PATH_HELPERS = ROOT / "src" / "toolchain" / "frontends" / "import_graph_path_helpers.py"
SRC_RELATIVE_IMPORT_NORMALIZATION = ROOT / "src" / "toolchain" / "frontends" / "relative_import_normalization.py"
SRC_TYPE_EXPR = ROOT / "src" / "toolchain" / "frontends" / "type_expr.py"


def _extract_code_emitter_class(text: str) -> str:
    marker = "class EmitterHooks:"
    i = text.find(marker)
    if i < 0:
        marker = "class CodeEmitter:"
        i = text.find(marker)
    if i < 0:
        raise RuntimeError("CodeEmitter class not found")
    return text[i:].rstrip() + "\n"


def _strip_triple_quoted_docstrings(text: str) -> str:
    out: list[str] = []
    in_doc = False
    quote = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if not in_doc:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                q = stripped[:3]
                # one-line docstring
                if stripped.count(q) >= 2 and len(stripped) > 3:
                    continue
                in_doc = True
                quote = q
                continue
            out.append(line)
        else:
            if quote in stripped:
                in_doc = False
                quote = ""
            continue
    return "\n".join(out) + "\n"


def _remove_import_line(text: str) -> str:
    def _remove_first_import_with_prefix(src: str, prefix: str) -> tuple[str, bool]:
        lines = src.splitlines(keepends=True)
        out_lines: list[str] = []
        removed = False
        skipping_block = False
        paren_depth = 0
        for line in lines:
            if skipping_block:
                paren_depth += line.count("(") - line.count(")")
                if paren_depth <= 0:
                    skipping_block = False
                continue
            if (not removed) and line.startswith(prefix):
                removed = True
                paren_depth = line.count("(") - line.count(")")
                if paren_depth > 0:
                    skipping_block = True
                continue
            out_lines.append(line)
        return "".join(out_lines), removed

    targets: list[tuple[str, str, bool]] = [
        # `CodeEmitter` import は py2cpp 側から hooks 側へ移ったため、存在しない版も許容する。
        ("from toolchain.compiler.east_parts.code_emitter import CodeEmitter", "CodeEmitter import", False),
        ("from toolchain.compiler.transpile_cli import ", "transpile_cli import", True),
        ("from toolchain.emit.cpp.emitter.hooks_registry import build_cpp_hooks as _build_cpp_hooks_impl", "build_cpp_hooks import", True),
    ]
    out = text
    missing: list[str] = []
    for prefix, label, required in targets:
        out_next, removed = _remove_first_import_with_prefix(out, prefix)
        if not removed:
            if required:
                missing.append(label)
            continue
        out = out_next
    if len(missing) > 0:
        raise RuntimeError("failed to remove required import lines: " + ", ".join(missing))
    return out


def _extract_top_level_block(text: str, name: str, kind: str) -> str:
    lines = text.splitlines(keepends=True)
    marker = f"{kind} {name}"
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(marker):
            rest = line[len(marker) :]
            if kind == "def" and not rest.startswith("("):
                continue
            if kind == "class" and not (rest.startswith("(") or rest.startswith(":")):
                continue
            start = i
            if i > 0 and lines[i - 1].startswith("@"):
                start = i - 1
            break
    if start < 0:
        raise RuntimeError(f"block not found: {kind} {name}")
    end = len(lines)
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("def ") or line.startswith("class ") or line.startswith("@"):
            end = i
            break
        i += 1
    block = "".join(lines[start:end]).rstrip() + "\n"
    return block


def _extract_type_expr_support_blocks() -> str:
    text = SRC_TYPE_EXPR.read_text(encoding="utf-8")
    constants_start = text.find("_PRIMITIVE_NAMES:")
    if constants_start < 0:
        raise RuntimeError("type_expr constants not found")
    first_def = text.find("def _strip_quotes", constants_start)
    if first_def < 0:
        raise RuntimeError("type_expr helper blocks not found")
    parts = [text[constants_start:first_def].rstrip() + "\n"]
    names = [
        "_strip_quotes",
        "_strip_typing_prefix",
        "_split_top_level",
        "_is_simple_identifier",
        "_normalize_head_name",
        "_is_none_expr",
        "_is_dynamic_expr",
        "_make_named_like",
        "_make_union_type_expr",
        "_parse_type_expr_inner",
        "parse_type_expr_text",
        "type_expr_to_string",
        "normalize_type_text",
    ]
    for name in names:
        parts.append(_extract_top_level_block(text, name, "def"))
    return "".join(parts)


def _extract_support_blocks() -> str:
    cli_text = SRC_TRANSPILE_CLI.read_text(encoding="utf-8")
    import_graph_analysis_text = SRC_IMPORT_GRAPH_ANALYSIS_HELPERS.read_text(encoding="utf-8")
    import_graph_helper_text = SRC_IMPORT_GRAPH_FRONTEND_HELPERS.read_text(encoding="utf-8")
    path_helper_text = SRC_IMPORT_GRAPH_PATH_HELPERS.read_text(encoding="utf-8")
    relative_import_text = SRC_RELATIVE_IMPORT_NORMALIZATION.read_text(encoding="utf-8")
    names = [
        "join_str_list",
        "mkdirs_for_cli",
        "replace_first",
        "inject_after_includes_block",
        "split_infix_once",
        "local_binding_name",
        "split_top_level_csv",
        "split_top_level_union",
        "split_type_args",
        "split_ws_tokens",
        "append_unique_non_empty",
        "resolve_codegen_options",
        "validate_codegen_options",
        "dump_codegen_options_text",
        "normalize_param_annotation",
        "extract_function_signatures_from_python_source",
        "extract_function_arg_types_from_python_source",
        "count_text_lines",
        "dict_any_get",
        "dict_any_get_str",
        "dict_any_get_list",
        "dict_any_get_dict",
        "dict_any_get_dict_list",
        "dict_any_get_str_list",
        "dict_any_kind",
        "name_target_id",
        "stmt_target_name",
        "assign_targets",
        "stmt_assigned_names",
        "stmt_child_stmt_lists",
        "collect_store_names_from_target",
        "collect_store_names_from_target_plan",
        "collect_symbols_from_stmt",
        "collect_symbols_from_stmt_list",
        "stmt_list_parse_metrics",
        "stmt_list_scope_depth",
        "dict_str_get",
        "looks_like_runtime_function_name",
        "first_import_detail_line",
        "make_user_error",
        "parse_user_error",
        "print_user_error",
        "normalize_east_root_document",
        "normalize_east1_to_east2_document",
        "load_east_document",
        "module_export_table",
        "_const_string_value",
        "_literal_string_sequence",
        "_module_static_all_symbols",
        "build_module_type_schema",
        "append_import_validation_detail",
        "resolve_wildcard_exports_for_import_validation",
        "bind_import_symbol_or_duplicate",
        "meta_import_bindings",
        "meta_qualified_symbol_refs",
        "dump_deps_text",
        "python_module_exists_under",
        "module_parse_metrics",
        "module_analyze_metrics",
        "select_guard_module_map",
        "set_import_module_binding",
        "set_import_symbol_binding",
        "set_import_symbol_binding_and_module_set",
        "build_module_symbol_index",
        "analyze_import_graph",
        "build_module_east_map",
        "dump_deps_graph_text",
        "validate_from_import_symbols_or_raise",
        "build_module_east_map_from_analysis",
        "write_text_file",
        "empty_parse_dict",
        "_parse_error_dict",
        "parse_py2cpp_argv",
        "parse_guard_limit_or_raise",
        "guard_profile_base_limits",
        "resolve_guard_limits",
        "raise_guard_limit_exceeded",
        "check_guard_limit",
        "check_parse_stage_guards",
        "check_analyze_stage_guards",
    ]
    parts: list[str] = [_extract_type_expr_support_blocks()]
    for name in ["path_parent_text", "path_key_for_graph", "module_name_from_path_for_graph"]:
        parts.append(_extract_top_level_block(path_helper_text, name, "def"))
    for name in [
        "split_graph_issue_entry",
        "make_graph_issue_entry",
        "normalize_graph_issue_entry",
        "format_graph_issue_entry",
        "append_unique_graph_issue_entry",
        "dict_any_get_graph_issue_entries",
        "graph_issue_entries_to_text_list",
        "graph_cycle_dfs",
        "format_graph_list_section",
        "format_import_graph_report",
        "validate_import_graph_or_raise",
        "finalize_import_graph_analysis",
        "is_known_non_user_import",
        "resolve_module_name_for_graph",
        "resolve_module_name",
    ]:
        parts.append(_extract_top_level_block(import_graph_analysis_text, name, "def"))
    for name in [
        "sort_str_list_copy",
        "collect_user_module_files_for_graph",
        "is_pytra_module_name",
        "rel_disp_for_graph",
        "sanitize_module_label",
        "module_rel_label",
        "module_id_from_east_for_graph",
        "resolve_user_module_path_for_graph",
        "collect_reserved_import_conflicts",
        "collect_import_requests",
        "collect_import_from_request_modules",
        "collect_import_request_modules",
        "collect_import_modules",
    ]:
        parts.append(_extract_top_level_block(import_graph_helper_text, name, "def"))
    for name in [
        "relative_module_level",
        "relative_module_tail",
        "_path_is_under_root_for_graph",
        "resolve_import_graph_entry_root",
        "resolve_relative_module_anchor_dir",
        "relative_module_id_from_anchor",
        "resolve_relative_module_name_for_graph",
        "normalize_relative_module_id",
    ]:
        parts.append(_extract_top_level_block(relative_import_text, name, "def"))
    for name in names:
        parts.append(_extract_top_level_block(cli_text, name, "def"))
    parts.append(
        "\n".join(
            [
                "def load_east3_document(",
                "    input_path: Path,",
                "    parser_backend: str = \"self_hosted\",",
                "    object_dispatch_mode: str = \"\",",
                ") -> dict[str, object]:",
                "    \"\"\"selfhost 互換: EAST3 入力は EAST2 読み込みへフォールバックする。\"\"\"",
                "    _ = object_dispatch_mode",
                "    return load_east_document(input_path, parser_backend=parser_backend)",
                "",
            ]
        )
    )
    parts.append(
        "\n".join(
            [
                "def build_module_east_map_common(",
                "    entry_path: Path,",
                "    load_east_fn: object,",
                "    parser_backend: str = \"self_hosted\",",
                "    east_stage: str = \"2\",",
                "    object_dispatch_mode: str = \"\",",
                "    runtime_std_source_root: Path = Path(\"src/pytra/std\"),",
                "    runtime_utils_source_root: Path = Path(\"src/pytra/utils\"),",
                ") -> dict[str, dict[str, object]]:",
                "    return build_module_east_map(",
                "        entry_path,",
                "        load_east_fn,",
                "        parser_backend,",
                "        east_stage,",
                "        object_dispatch_mode,",
                "        runtime_std_source_root,",
                "        runtime_utils_source_root,",
                "    )",
                "",
                "",
                "def dump_deps_graph_text_common(",
                "    entry_path: Path,",
                "    runtime_std_source_root: Path = Path(\"src/pytra/std\"),",
                "    runtime_utils_source_root: Path = Path(\"src/pytra/utils\"),",
                "    load_east_fn: object = load_east_document,",
                ") -> str:",
                "    return dump_deps_graph_text(",
                "        entry_path,",
                "        runtime_std_source_root,",
                "        runtime_utils_source_root,",
                "        load_east_fn,",
                "    )",
                "",
            ]
        )
    )
    parts.append(
        "\n".join(
            [
                "def _build_cpp_hooks_impl() -> dict[str, Any]:",
                "    \"\"\"selfhost 互換: dynamic hooks 実装が利用できない場合の安全な既定値。\"\"\"",
                "    return {}",
                "",
            ]
        )
    )
    return "\n".join(parts)


def _insert_code_emitter(text: str, base_class_text: str, support_blocks: str) -> str:
    support_marker = "RUNTIME_STD_SOURCE_ROOT = "
    i = text.find(support_marker)
    if i < 0:
        raise RuntimeError("RUNTIME_STD_SOURCE_ROOT marker not found in py2cpp.py")
    prefix = text[:i]
    suffix = text[i:]
    out = prefix.rstrip() + "\n\n" + support_blocks + "\n" + suffix

    marker = "CPP_HEADER = "
    j = out.find(marker)
    if j < 0:
        raise RuntimeError("CPP_HEADER marker not found in py2cpp.py")
    prefix2 = out[:j]
    suffix2 = out[j:]
    return prefix2.rstrip() + "\n\n" + base_class_text + "\n" + suffix2


def _patch_code_emitter_hooks_for_selfhost(text: str) -> str:
    """selfhost 向けに dynamic hooks 依存コードを安全化する。"""
    call_hook_marker = "    def _call_hook(\n"
    call_hook_start = text.find(call_hook_marker)
    if call_hook_start < 0:
        raise RuntimeError("failed to find _call_hook in merged selfhost source")
    call_hook_end_marker = "\n    def _call_hook1("
    call_hook_end = text.find(call_hook_end_marker, call_hook_start + len(call_hook_marker))
    if call_hook_end < 0:
        raise RuntimeError("failed to find _call_hook1 marker in merged selfhost source")
    call_hook_stub = (
        "    def _call_hook(\n"
        "        self,\n"
        "        name: str,\n"
        "        arg0: Any = None,\n"
        "        arg1: Any = None,\n"
        "        arg2: Any = None,\n"
        "        arg3: Any = None,\n"
        "        arg4: Any = None,\n"
        "        arg5: Any = None,\n"
        "        argc: int = 0,\n"
        "    ) -> Any:\n"
        "        \"\"\"selfhost 互換: dynamic hooks は無効化済みなので常に未処理を返す。\"\"\"\n"
        "        return None\n"
        "\n"
    )
    out = text[:call_hook_start] + call_hook_stub + text[call_hook_end:]

    target = "self.init_base_state("
    j = out.find(target)
    if j < 0:
        raise RuntimeError("failed to find init_base_state call in CodeEmitter.__init__")

    line_start = out.rfind("\n", 0, j)
    if line_start < 0:
        line_start = 0
    else:
        line_start += 1
    line_end = out.find("\n", j)
    if line_end < 0:
        line_end = len(out)
    line = out[line_start:line_end]
    indent = ""
    for ch in line:
        if ch == " ":
            indent += " "
        else:
            break
    inserted = indent + "self.set_dynamic_hooks_enabled(False)\n"
    insert_pos = line_end + 1 if line_end < len(out) else len(out)
    if out.startswith(inserted, insert_pos):
        return out
    return out[:insert_pos] + inserted + out[insert_pos:]


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    support_blocks = _extract_support_blocks()

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class, support_blocks)
    out = _patch_code_emitter_hooks_for_selfhost(out)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

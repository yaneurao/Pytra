#!/usr/bin/env python3
"""Prepare selfhost/py2cpp.py as a self-contained source.

This script inlines CodeEmitter into py2cpp.py so transpiling selfhost input
no longer depends on cross-module import resolution.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CPP = ROOT / "src" / "py2cpp.py"
SRC_BASE = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "code_emitter.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cpp.py"
SRC_TRANSPILE_CLI = ROOT / "src" / "pytra" / "compiler" / "transpile_cli.py"


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
    targets: list[tuple[str, str]] = [
        ("from pytra.compiler.east_parts.code_emitter import CodeEmitter\n", "CodeEmitter import"),
        (
            "from pytra.compiler.transpile_cli import append_unique_non_empty, assign_targets, collect_import_modules, collect_store_names_from_target, collect_symbols_from_stmt, count_text_lines, dict_any_get, dict_any_get_str, dict_any_get_list, dict_any_get_dict, dict_any_get_dict_list, dict_any_get_str_list, dict_any_kind, dict_str_get, dump_codegen_options_text, first_import_detail_line, format_graph_list_section, graph_cycle_dfs, inject_after_includes_block, is_known_non_user_import, is_pytra_module_name, join_str_list, local_binding_name, looks_like_runtime_function_name, make_user_error, meta_import_bindings, meta_qualified_symbol_refs, mkdirs_for_cli, module_id_from_east_for_graph, module_name_from_path_for_graph, module_parse_metrics, module_rel_label, name_target_id, parse_py2cpp_argv, parse_user_error, path_key_for_graph, path_parent_text, python_module_exists_under, rel_disp_for_graph, replace_first, resolve_codegen_options, resolve_module_name_for_graph, resolve_user_module_path_for_graph, sanitize_module_label, sort_str_list_copy, split_graph_issue_entry, split_infix_once, split_top_level_csv, split_top_level_union, split_type_args, split_ws_tokens, stmt_assigned_names, stmt_child_stmt_lists, stmt_list_parse_metrics, stmt_list_scope_depth, stmt_target_name, validate_codegen_options, write_text_file\n",
            "transpile_cli import",
        ),
        ("from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks\n", "build_cpp_hooks import"),
    ]
    out = text
    missing: list[str] = []
    for target, label in targets:
        if target in out:
            out = out.replace(target, "", 1)
        else:
            missing.append(label)
    if len(missing) > 0:
        raise RuntimeError("failed to remove required import lines: " + ", ".join(missing))
    return out


def _extract_top_level_block(text: str, name: str, kind: str) -> str:
    lines = text.splitlines(keepends=True)
    marker = f"{kind} {name}"
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(marker):
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


def _extract_support_blocks() -> str:
    cli_text = SRC_TRANSPILE_CLI.read_text(encoding="utf-8")
    names = [
        "join_str_list",
        "mkdirs_for_cli",
        "path_parent_text",
        "replace_first",
        "inject_after_includes_block",
        "split_infix_once",
        "local_binding_name",
        "split_graph_issue_entry",
        "split_top_level_csv",
        "split_top_level_union",
        "graph_cycle_dfs",
        "split_type_args",
        "split_ws_tokens",
        "append_unique_non_empty",
        "resolve_codegen_options",
        "validate_codegen_options",
        "dump_codegen_options_text",
        "sort_str_list_copy",
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
        "collect_symbols_from_stmt",
        "stmt_list_parse_metrics",
        "stmt_list_scope_depth",
        "dict_str_get",
        "looks_like_runtime_function_name",
        "first_import_detail_line",
        "make_user_error",
        "parse_user_error",
        "is_pytra_module_name",
        "module_name_from_path_for_graph",
        "module_id_from_east_for_graph",
        "sanitize_module_label",
        "module_rel_label",
        "meta_import_bindings",
        "meta_qualified_symbol_refs",
        "path_key_for_graph",
        "rel_disp_for_graph",
        "python_module_exists_under",
        "module_parse_metrics",
        "resolve_user_module_path_for_graph",
        "format_graph_list_section",
        "collect_import_modules",
        "is_known_non_user_import",
        "resolve_module_name_for_graph",
        "write_text_file",
        "empty_parse_dict",
        "_parse_error_dict",
        "parse_py2cpp_argv",
    ]
    parts: list[str] = []
    for name in names:
        parts.append(_extract_top_level_block(cli_text, name, "def"))
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
    """CodeEmitter の hook 呼び出しヘルパを selfhost 用に no-op 化する。"""
    start_marker = "    def _call_hook("
    end_marker = "\n    def _call_hook1("
    i = text.find(start_marker)
    j = text.find(end_marker)
    if i < 0:
        raise RuntimeError("failed to find _call_hook block in merged selfhost source")
    if j <= i:
        raise RuntimeError("failed to find _call_hook1 marker after _call_hook in merged selfhost source")
    block = text[i:j]
    lines = block.splitlines(keepends=True)
    out_lines: list[str] = []
    replaced = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("return fn(") and stripped.endswith(")"):
            indent = line[: len(line) - len(line.lstrip())]
            out_lines.append(indent + "return None\n")
            replaced += 1
            continue
        out_lines.append(line)
    if replaced != 7:
        raise RuntimeError("failed to neutralize _call_hook dynamic calls: replaced=" + str(replaced))
    block = "".join(out_lines)
    return text[:i] + block + text[j:]


def _patch_load_cpp_hooks_for_selfhost(text: str) -> str:
    """`load_cpp_hooks` 内の hooks 取得を selfhost 用に空 dict へ固定化する。"""
    start_marker = "def load_cpp_hooks("
    end_marker = "\n\ndef load_cpp_identifier_rules("
    i = text.find(start_marker)
    if i < 0:
        raise RuntimeError("failed to find load_cpp_hooks block in merged selfhost source")
    j = text.find(end_marker, i + len(start_marker))
    if j <= i:
        raise RuntimeError("failed to find load_cpp_identifier_rules marker after load_cpp_hooks in merged selfhost source")
    block = text[i:j]
    target = "        hooks = build_cpp_hooks()\n"
    replacement = "        hooks = {}\n"
    if target not in block:
        raise RuntimeError("failed to patch load_cpp_hooks call: hooks = build_cpp_hooks()")
    block = block.replace(target, replacement, 1)
    return text[:i] + block + text[j:]


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    support_blocks = _extract_support_blocks()

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class, support_blocks)
    out = _patch_load_cpp_hooks_for_selfhost(out)
    out = _patch_code_emitter_hooks_for_selfhost(out)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

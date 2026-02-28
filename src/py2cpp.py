#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/pytra/compiler/east.py conversion.
"""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.east1_build import East1BuildHelpers
from pytra.compiler.east_parts.core import convert_path, convert_source_to_east_with_backend
from pytra.compiler.transpile_cli import (
    add_common_transpile_args,
    append_unique_non_empty,
    assign_targets,
    check_analyze_stage_guards,
    check_guard_limit,
    check_parse_stage_guards,
    collect_import_modules,
    collect_reserved_import_conflicts,
    collect_store_names_from_target,
    collect_symbols_from_stmt,
    collect_symbols_from_stmt_list,
    collect_user_module_files_for_graph,
    count_text_lines,
    dict_any_get,
    dict_any_get_dict,
    dict_any_get_dict_list,
    dict_any_get_list,
    dict_any_get_str,
    dict_any_get_str_list,
    dict_any_kind,
    dict_str_get,
    dump_deps_graph_text as dump_deps_graph_text_common,
    dump_deps_text,
    extract_function_arg_types_from_python_source,
    extract_function_signatures_from_python_source,
    finalize_import_graph_analysis,
    format_graph_list_section,
    format_import_graph_report,
    first_import_detail_line,
    graph_cycle_dfs,
    inject_after_includes_block,
    is_known_non_user_import,
    is_pytra_module_name,
    join_str_list,
    looks_like_runtime_function_name,
    load_east3_document,
    load_east_document,
    local_binding_name,
    make_user_error,
    module_analyze_metrics,
    module_export_table,
    module_id_from_east_for_graph,
    module_name_from_path_for_graph,
    module_parse_metrics,
    module_rel_label,
    mkdirs_for_cli,
    name_target_id,
    normalize_common_transpile_args,
    normalize_param_annotation,
    parse_py2cpp_argv,
    parse_user_error,
    path_key_for_graph,
    path_parent_text,
    print_user_error,
    python_module_exists_under,
    rel_disp_for_graph,
    replace_first,
    resolve_codegen_options,
    resolve_guard_limits,
    resolve_module_name,
    resolve_module_name_for_graph,
    resolve_user_module_path_for_graph,
    sanitize_module_label,
    select_guard_module_map,
    set_import_module_binding,
    set_import_symbol_binding_and_module_set,
    sort_str_list_copy,
    split_graph_issue_entry,
    split_infix_once,
    split_top_level_csv,
    split_top_level_union,
    split_type_args,
    split_ws_tokens,
    stmt_assigned_names,
    stmt_child_stmt_lists,
    stmt_list_parse_metrics,
    stmt_list_scope_depth,
    stmt_target_name,
    validate_codegen_options,
    validate_from_import_symbols_or_raise,
    validate_import_graph_or_raise,
    write_text_file,
    dump_codegen_options_text,
)
from pytra.std import json
from pytra.std import os
from pytra.std.pathlib import Path
from pytra.std import sys
from hooks.cpp.profile import CMP_OPS as CPP_CMP_OPS
from hooks.cpp.profile import AUG_BIN as CPP_AUG_BIN
from hooks.cpp.profile import AUG_OPS as CPP_AUG_OPS
from hooks.cpp.profile import BIN_OPS as CPP_BIN_OPS
from hooks.cpp.profile import load_cpp_identifier_rules as _load_cpp_identifier_rules
from hooks.cpp.profile import load_cpp_module_attr_call_map as _load_cpp_module_attr_call_map
from hooks.cpp.profile import load_cpp_profile as _load_cpp_profile
from hooks.cpp.profile import load_cpp_type_map as _load_cpp_type_map
from hooks.cpp.profile import load_cpp_bin_ops as _load_cpp_bin_ops
from hooks.cpp.profile import load_cpp_cmp_ops as _load_cpp_cmp_ops
from hooks.cpp.profile import load_cpp_aug_ops as _load_cpp_aug_ops
from hooks.cpp.profile import load_cpp_aug_bin as _load_cpp_aug_bin
from hooks.cpp.header import build_cpp_header_from_east as _build_cpp_header_from_east
from hooks.cpp.multifile import write_multi_file_cpp as _write_multi_file_cpp_impl
from hooks.cpp.optimizer import parse_cpp_opt_pass_overrides

build_module_symbol_index = East1BuildHelpers.build_module_symbol_index
build_module_type_schema = East1BuildHelpers.build_module_type_schema
from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks as _build_cpp_hooks_impl


from hooks.cpp.runtime_emit import RUNTIME_CPP_COMPAT_ROOT
from hooks.cpp.runtime_emit import RUNTIME_CPP_GEN_ROOT
from hooks.cpp.runtime_emit import _is_runtime_emit_input_path as _is_runtime_emit_input_path_impl
from hooks.cpp.runtime_emit import _join_runtime_path as _join_runtime_path_impl
from hooks.cpp.runtime_emit import _module_tail_to_cpp_header_path as _module_tail_to_cpp_header_path_impl
from hooks.cpp.runtime_emit import _prepend_generated_cpp_banner as _prepend_generated_cpp_banner_impl
from hooks.cpp.runtime_emit import _runtime_cpp_header_exists_for_module as _runtime_cpp_header_exists_for_module_impl
from hooks.cpp.runtime_emit import _runtime_module_tail_from_source_path as _runtime_module_tail_from_source_path_impl
from hooks.cpp.runtime_emit import _runtime_namespace_for_tail as _runtime_namespace_for_tail_impl
from hooks.cpp.runtime_emit import _runtime_output_rel_tail as _runtime_output_rel_tail_impl


RUNTIME_STD_SOURCE_ROOT = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT = Path("src/pytra/utils")
RUNTIME_COMPILER_SOURCE_ROOT = Path("src/pytra/compiler")
RUNTIME_BUILT_IN_SOURCE_ROOT = Path("src/pytra/built_in")


def _module_tail_to_cpp_header_path(module_tail: str) -> str:
    """Delegate to runtime emit module."""
    return _module_tail_to_cpp_header_path_impl(module_tail)


def _join_runtime_path(base_dir: Path, rel_path: str) -> Path:
    """Delegate to runtime emit module."""
    return _join_runtime_path_impl(base_dir, rel_path)


def _runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """Delegate to runtime emit module."""
    return _runtime_cpp_header_exists_for_module_impl(module_name_norm)


def _runtime_module_tail_from_source_path(input_path: Path) -> str:
    """Delegate to runtime emit module."""
    return _runtime_module_tail_from_source_path_impl(input_path)


def _prepend_generated_cpp_banner(cpp_text: str, source_path: Path) -> str:
    """Delegate to runtime emit module."""
    return _prepend_generated_cpp_banner_impl(cpp_text, source_path)


def _is_runtime_emit_input_path(input_path: Path) -> bool:
    """Delegate to runtime emit module."""
    return _is_runtime_emit_input_path_impl(input_path)


def _runtime_output_rel_tail(module_tail: str) -> str:
    """Delegate to runtime emit module."""
    return _runtime_output_rel_tail_impl(module_tail)


def _runtime_namespace_for_tail(module_tail: str) -> str:
    """Delegate to runtime emit module."""
    return _runtime_namespace_for_tail_impl(module_tail)



SCOPE_NESTING_KINDS: set[str] = {
    "FunctionDef",
    "AsyncFunctionDef",
    "ClassDef",
    "If",
    "For",
    "ForCore",
    "While",
    "With",
    "Try",
    "ExceptHandler",
    "Match",
    "MatchCase",
}


CPP_HEADER = """#include "runtime/cpp/pytra/built_in/py_runtime.h"

"""

# `"\n"` のエスケープ解釈に依存しないため、実改行を定数化して使う。
NEWLINE_CHAR = """
"""


def load_cpp_profile() -> dict[str, Any]:
    """C++ 用 LanguageProfile を読み込む（失敗時は最小既定）。"""
    return _load_cpp_profile()


def load_cpp_bin_ops() -> dict[str, str]:
    """C++ 用二項演算子マップを返す。"""
    return _load_cpp_bin_ops()


def load_cpp_cmp_ops() -> dict[str, str]:
    """C++ 用比較演算子マップを返す。"""
    return _load_cpp_cmp_ops()


def load_cpp_aug_ops() -> dict[str, str]:
    """C++ 用複合代入演算子マップを返す。"""
    return _load_cpp_aug_ops()


def load_cpp_aug_bin() -> dict[str, str]:
    """C++ 用複合代入分解時の演算子マップを返す。"""
    return _load_cpp_aug_bin()


def load_cpp_type_map(profile: dict[str, Any] = {}) -> dict[str, str]:
    """EAST 型 -> C++ 型の基本マップを返す（profile の `types` で上書き可能）。"""
    return _load_cpp_type_map(profile)


def load_cpp_hooks(profile: dict[str, Any] = {}) -> dict[str, Any]:
    """C++ 用 hooks 設定を返す。"""
    _ = profile
    hooks: Any = {}
    try:
        hooks = _build_cpp_hooks_impl()
    except Exception:
        return {}
    if isinstance(hooks, dict):
        return hooks
    return {}


def load_cpp_identifier_rules(profile: dict[str, Any] = {}) -> tuple[set[str], str]:
    """識別子リネーム規則を返す（profile.syntax.identifiers で上書き可能）。"""
    return _load_cpp_identifier_rules(profile)


def load_cpp_module_attr_call_map(profile: dict[str, Any] = {}) -> dict[str, dict[str, str]]:
    """C++ の `module.attr(...)` -> ランタイム呼び出しマップを返す。"""
    return _load_cpp_module_attr_call_map(profile)


BIN_OPS: dict[str, str] = CPP_BIN_OPS
CMP_OPS: dict[str, str] = CPP_CMP_OPS
AUG_OPS: dict[str, str] = CPP_AUG_OPS
AUG_BIN: dict[str, str] = CPP_AUG_BIN


def cpp_string_lit(s: str) -> str:
    """Python 文字列を C++ 文字列リテラルへエスケープ変換する。"""
    out_chars: list[str] = []
    for ch in s:
        if ch == "\\":
            out_chars.append("\\\\")
        elif ch == "\"":
            out_chars.append("\\\"")
        elif ch == "\n":
            out_chars.append("\\n")
        elif ch == "\r":
            out_chars.append("\\r")
        elif ch == "\t":
            out_chars.append("\\t")
        else:
            out_chars.append(ch)
    return "\"" + "".join(out_chars) + "\""


def cpp_char_lit(ch: str) -> str:
    """1文字文字列を C++ 文字リテラルへ変換する。"""
    if ch == "\\":
        return "'\\\\'"
    if ch == "'":
        return "'\\''"
    if ch == "\n":
        return "'\\n'"
    if ch == "\r":
        return "'\\r'"
    if ch == "\t":
        return "'\\t'"
    if ch == "\0":
        return "'\\0'"
    return "'" + str(ch) + "'"


from hooks.cpp.emitter import CppEmitter
from hooks.cpp.emitter import emit_cpp_from_east
from hooks.cpp.emitter import install_py2cpp_runtime_symbols
install_py2cpp_runtime_symbols(globals())


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
) -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    if east_stage != "3":
        raise RuntimeError("py2cpp supports only --east-stage 3: " + east_stage)
    east3_doc = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="cpp",
    )
    east_doc: dict[str, Any] = east3_doc if isinstance(east3_doc, dict) else {}
    return east_doc if isinstance(east_doc, dict) else {}


def _transpile_to_cpp_with_map(
    east_module: dict[str, Any],
    module_namespace_map: dict[str, str],
    negative_index_mode: str = "const_only",
    bounds_check_mode: str = "off",
    floor_div_mode: str = "native",
    mod_mode: str = "native",
    int_width: str = "64",
    str_index_mode: str = "native",
    str_slice_mode: str = "byte",
    opt_level: str = "2",
    top_namespace: str = "",
    emit_main: bool = True,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
    cpp_list_model: str = "",
) -> str:
    """EAST Module を C++ ソース文字列へ変換する。"""
    return emit_cpp_from_east(
        east_module,
        module_namespace_map,
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
        top_namespace,
        emit_main,
        cpp_opt_level,
        cpp_opt_pass,
        dump_cpp_ir_before_opt,
        dump_cpp_ir_after_opt,
        dump_cpp_opt_trace,
        cpp_list_model,
    )


def transpile_to_cpp(
    east_module: dict[str, Any],
    negative_index_mode: str = "const_only",
    bounds_check_mode: str = "off",
    floor_div_mode: str = "native",
    mod_mode: str = "native",
    int_width: str = "64",
    str_index_mode: str = "native",
    str_slice_mode: str = "byte",
    opt_level: str = "2",
    top_namespace: str = "",
    emit_main: bool = True,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
    cpp_list_model: str = "",
) -> str:
    """後方互換を維持した公開 API。"""
    ns_map: dict[str, str] = {}
    return _transpile_to_cpp_with_map(
        east_module,
        ns_map,
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
        top_namespace,
        emit_main,
        cpp_opt_level,
        cpp_opt_pass,
        dump_cpp_ir_before_opt,
        dump_cpp_ir_after_opt,
        dump_cpp_opt_trace,
        cpp_list_model,
    )


def build_cpp_header_from_east(
    east_module: dict[str, Any],
    source_path: Path,
    output_path: Path,
    top_namespace: str = "",
) -> str:
    """EAST から最小宣言のみの C++ ヘッダ文字列を生成する。"""
    return _build_cpp_header_from_east(east_module, source_path, output_path, top_namespace)




def _analyze_import_graph(entry_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """ユーザーモジュール依存解析（`east1_build` 入口 API への委譲）。"""
    analysis = East1BuildHelpers.analyze_import_graph(
        entry_path,
        runtime_std_source_root=RUNTIME_STD_SOURCE_ROOT,
        runtime_utils_source_root=RUNTIME_UTILS_SOURCE_ROOT,
        parser_backend=parser_backend,
    )
    return analysis if isinstance(analysis, dict) else {}


def build_module_east_map(
    entry_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
) -> dict[str, dict[str, Any]]:
    """入口 + 依存ユーザーモジュールの EAST map 構築（`east1_build` API への委譲）。"""

    def _build_module_doc(path_obj: Path, parser_backend: str = "self_hosted", object_dispatch_mode: str = "") -> dict[str, Any]:
        is_entry = str(path_obj) == str(entry_path)
        return load_east(
            path_obj,
            parser_backend=parser_backend,
            east_stage=east_stage,
            object_dispatch_mode=object_dispatch_mode,
            east3_opt_level=east3_opt_level,
            east3_opt_pass=east3_opt_pass,
            dump_east3_before_opt=dump_east3_before_opt if is_entry else "",
            dump_east3_after_opt=dump_east3_after_opt if is_entry else "",
            dump_east3_opt_trace=dump_east3_opt_trace if is_entry else "",
        )

    mp = East1BuildHelpers.build_module_east_map(
        entry_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        runtime_std_source_root=RUNTIME_STD_SOURCE_ROOT,
        runtime_utils_source_root=RUNTIME_UTILS_SOURCE_ROOT,
        build_module_document_fn=_build_module_doc,
    )
    return {key: value for key, value in mp.items() if isinstance(value, dict)}


def _write_multi_file_cpp(
    entry_path: Path,
    module_east_map: dict[str, dict[str, Any]],
    output_dir: Path,
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
    top_namespace: str,
    emit_main: bool,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
    max_generated_lines: int = 0,
    cpp_list_model: str = "",
) -> dict[str, Any]:
    """Delegate multi-file output generation to hooks.cpp.multifile."""
    return _write_multi_file_cpp_impl(
        entry_path,
        module_east_map,
        output_dir,
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
        top_namespace,
        emit_main,
        cpp_opt_level,
        cpp_opt_pass,
        dump_cpp_ir_before_opt,
        dump_cpp_ir_after_opt,
        dump_cpp_opt_trace,
        max_generated_lines,
        cpp_list_model,
    )


def dump_deps_graph_text(entry_path: Path) -> str:
    """入力 `.py` から辿れるユーザーモジュール依存グラフを整形して返す。"""
    return dump_deps_graph_text_common(
        entry_path,
        runtime_std_source_root=RUNTIME_STD_SOURCE_ROOT,
        runtime_utils_source_root=RUNTIME_UTILS_SOURCE_ROOT,
        load_east_fn=load_east,
    )


def _is_valid_cpp_namespace_name(ns: str) -> bool:
    """selfhost 安定性優先の簡易チェック。"""
    return True


def main(argv: list[str]) -> int:
    """CLI エントリポイント。変換実行と入出力を担当する。"""
    argv_list: list[str] = []
    for a in argv:
        argv_list.append(a)
    parse_argv = argv_list
    # selfhost 実行時に実行ファイル名が argv に混入する経路を吸収する。
    if len(argv_list) >= 2:
        head = str(argv_list[0])
        is_exec_name = head[-4:] == ".out" or head[-4:] == ".exe" or head[-6:] == "py2cpp"
        if is_exec_name and not head.startswith("-"):
            parse_argv = list(argv_list[1:])
    parsed = parse_py2cpp_argv(parse_argv)
    parse_err = dict_str_get(parsed, "__error", "")
    if parse_err != "":
        print(f"error: {parse_err}", file=sys.stderr)
        return 1
    input_txt = dict_str_get(parsed, "input", "")
    output_txt = dict_str_get(parsed, "output", "")
    header_output_txt = dict_str_get(parsed, "header_output", "")
    output_dir_txt = dict_str_get(parsed, "output_dir", "")
    top_namespace_opt = dict_str_get(parsed, "top_namespace_opt", "")
    negative_index_mode_opt = dict_str_get(parsed, "negative_index_mode_opt", "")
    cpp_list_model_opt = dict_str_get(parsed, "cpp_list_model_opt", "")
    object_dispatch_mode_opt = dict_str_get(parsed, "object_dispatch_mode_opt", "")
    east3_opt_level_opt = dict_str_get(parsed, "east3_opt_level_opt", "1")
    east3_opt_pass_opt = dict_str_get(parsed, "east3_opt_pass_opt", "")
    dump_east3_before_opt = dict_str_get(parsed, "dump_east3_before_opt", "")
    dump_east3_after_opt = dict_str_get(parsed, "dump_east3_after_opt", "")
    dump_east3_opt_trace = dict_str_get(parsed, "dump_east3_opt_trace", "")
    cpp_opt_level_opt = dict_str_get(parsed, "cpp_opt_level_opt", "1")
    cpp_opt_pass_opt = dict_str_get(parsed, "cpp_opt_pass_opt", "")
    dump_cpp_ir_before_opt = dict_str_get(parsed, "dump_cpp_ir_before_opt", "")
    dump_cpp_ir_after_opt = dict_str_get(parsed, "dump_cpp_ir_after_opt", "")
    dump_cpp_opt_trace = dict_str_get(parsed, "dump_cpp_opt_trace", "")
    bounds_check_mode_opt = dict_str_get(parsed, "bounds_check_mode_opt", "")
    floor_div_mode_opt = dict_str_get(parsed, "floor_div_mode_opt", "")
    mod_mode_opt = dict_str_get(parsed, "mod_mode_opt", "")
    int_width_opt = dict_str_get(parsed, "int_width_opt", "")
    str_index_mode_opt = dict_str_get(parsed, "str_index_mode_opt", "")
    str_slice_mode_opt = dict_str_get(parsed, "str_slice_mode_opt", "")
    opt_level_opt = dict_str_get(parsed, "opt_level_opt", "")
    preset = dict_str_get(parsed, "preset", "")
    parser_backend = dict_str_get(parsed, "parser_backend", "self_hosted")
    east_stage = dict_str_get(parsed, "east_stage", "3")
    guard_profile = dict_str_get(parsed, "guard_profile", "default")
    max_ast_depth_raw = dict_str_get(parsed, "max_ast_depth", "")
    max_parse_nodes_raw = dict_str_get(parsed, "max_parse_nodes", "")
    max_symbols_per_module_raw = dict_str_get(parsed, "max_symbols_per_module", "")
    max_scope_depth_raw = dict_str_get(parsed, "max_scope_depth", "")
    max_import_graph_nodes_raw = dict_str_get(parsed, "max_import_graph_nodes", "")
    max_import_graph_edges_raw = dict_str_get(parsed, "max_import_graph_edges", "")
    max_generated_lines_raw = dict_str_get(parsed, "max_generated_lines", "")
    no_main = dict_str_get(parsed, "no_main", "0") == "1"
    single_file = dict_str_get(parsed, "single_file", "1") == "1"
    output_mode_explicit = dict_str_get(parsed, "output_mode_explicit", "0") == "1"
    dump_deps = dict_str_get(parsed, "dump_deps", "0") == "1"
    dump_options = dict_str_get(parsed, "dump_options", "0") == "1"
    emit_runtime_cpp = dict_str_get(parsed, "emit_runtime_cpp", "0") == "1"
    show_help = dict_str_get(parsed, "help", "0") == "1"
    negative_index_mode = ""
    object_dispatch_mode = ""
    bounds_check_mode = ""
    floor_div_mode = ""
    mod_mode = ""
    int_width = ""
    str_index_mode = ""
    str_slice_mode = ""
    opt_level = ""
    usage_text = "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--header-output OUTPUT.h] [--emit-runtime-cpp] [--output-dir DIR] [--single-file|--multi-file] [--top-namespace NS] [--preset MODE] [--negative-index-mode MODE] [--cpp-list-model {value,pyobj}] [--object-dispatch-mode {native,type_id}] [--east-stage {3} (default:3)] [--east3-opt-level {0,1,2}] [--east3-opt-pass SPEC] [--dump-east3-before-opt PATH] [--dump-east3-after-opt PATH] [--dump-east3-opt-trace PATH] [--cpp-opt-level {0,1,2}] [--cpp-opt-pass SPEC] [--dump-cpp-ir-before-opt PATH] [--dump-cpp-ir-after-opt PATH] [--dump-cpp-opt-trace PATH] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--guard-profile {off,default,strict}] [--max-ast-depth N] [--max-parse-nodes N] [--max-symbols-per-module N] [--max-scope-depth N] [--max-import-graph-nodes N] [--max-import-graph-edges N] [--max-generated-lines N] [--no-main] [--dump-deps] [--dump-options]"
    guard_limits: dict[str, int] = {}

    if show_help:
        print(usage_text, file=sys.stderr)
        return 0
    if input_txt == "":
        print(usage_text, file=sys.stderr)
        return 1
    if east_stage != "3":
        if east_stage == "2":
            print("error: --east-stage 2 is removed; py2cpp supports only --east-stage 3.", file=sys.stderr)
        else:
            print(f"error: invalid --east-stage: {east_stage} (py2cpp supports only 3)", file=sys.stderr)
        return 1
    if object_dispatch_mode_opt not in {"", "native", "type_id"}:
        print(f"error: invalid --object-dispatch-mode: {object_dispatch_mode_opt}", file=sys.stderr)
        return 1
    if cpp_list_model_opt not in {"", "value", "pyobj"}:
        print(f"error: invalid --cpp-list-model: {cpp_list_model_opt}", file=sys.stderr)
        return 1
    if east3_opt_level_opt not in {"0", "1", "2"}:
        print(f"error: invalid --east3-opt-level: {east3_opt_level_opt}", file=sys.stderr)
        return 1
    if cpp_opt_level_opt not in {"0", "1", "2"}:
        print(f"error: invalid --cpp-opt-level: {cpp_opt_level_opt}", file=sys.stderr)
        return 1
    try:
        parse_cpp_opt_pass_overrides(cpp_opt_pass_opt)
    except ValueError as ex:
        print("error: " + str(ex), file=sys.stderr)
        return 1
    object_dispatch_mode = object_dispatch_mode_opt if object_dispatch_mode_opt != "" else "native"
    if not _is_valid_cpp_namespace_name(top_namespace_opt):
        print(f"error: invalid --top-namespace: {top_namespace_opt}", file=sys.stderr)
        return 1
    try:
        negative_index_mode, bounds_check_mode, floor_div_mode, mod_mode, int_width, str_index_mode, str_slice_mode, opt_level = resolve_codegen_options(
            preset,
            negative_index_mode_opt,
            bounds_check_mode_opt,
            floor_div_mode_opt,
            mod_mode_opt,
            int_width_opt,
            str_index_mode_opt,
            str_slice_mode_opt,
            opt_level_opt,
        )
    except ValueError:
        print("error: invalid codegen options", file=sys.stderr)
        return 1
    opt_err: str = validate_codegen_options(
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
    )
    allowed_planned = [
        "--int-width=bigint is not implemented yet",
        "--str-index-mode=codepoint is not implemented yet",
        "--str-slice-mode=codepoint is not implemented yet",
    ]
    allow_planned = False
    if dump_options and opt_err != "":
        for s in allowed_planned:
            if opt_err == s:
                allow_planned = True
    if opt_err != "" and not allow_planned:
        print(f"error: {opt_err}", file=sys.stderr)
        return 1
    try:
        guard_limits = resolve_guard_limits(
            guard_profile,
            max_ast_depth_raw,
            max_parse_nodes_raw,
            max_symbols_per_module_raw,
            max_scope_depth_raw,
            max_import_graph_nodes_raw,
            max_import_graph_edges_raw,
            max_generated_lines_raw,
        )
    except ValueError as ex:
        print("error: " + str(ex), file=sys.stderr)
        return 1

    input_path = Path(input_txt)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1
    # 互換維持: 出力先が `.cpp` の場合は明示モード指定がなくても single-file 扱いにする。
    if (not output_mode_explicit) and output_txt.endswith(".cpp"):
        single_file = True
        if dump_options:
            options_text: str = dump_codegen_options_text(
            preset,
            negative_index_mode,
            bounds_check_mode,
            floor_div_mode,
            mod_mode,
            int_width,
            str_index_mode,
            str_slice_mode,
            opt_level,
        )
            if output_txt != "":
                out_path = Path(output_txt)
                mkdirs_for_cli(path_parent_text(out_path))
                write_text_file(out_path, options_text)
            else:
                print(options_text, end="")
            return 0

    cpp = ""
    try:
        module_east_map_cache: dict[str, dict[str, Any]] = {}
        import_graph_analysis: dict[str, Any] = {"user_module_files": [], "edges": []}
        if input_txt.endswith(".py") and not (emit_runtime_cpp and _is_runtime_emit_input_path(input_path)):
            analysis = _analyze_import_graph(input_path, parser_backend=parser_backend)
            validate_import_graph_or_raise(analysis)
            import_graph_analysis = analysis
            module_east_map_cache = build_module_east_map(
                input_path,
                parser_backend,
                east_stage=east_stage,
                object_dispatch_mode=object_dispatch_mode,
                east3_opt_level=east3_opt_level_opt,
                east3_opt_pass=east3_opt_pass_opt,
                dump_east3_before_opt=dump_east3_before_opt,
                dump_east3_after_opt=dump_east3_after_opt,
                dump_east3_opt_trace=dump_east3_opt_trace,
            )
        east_module: dict[str, Any] = (
            module_east_map_cache[input_txt]
            if input_txt.endswith(".py") and input_txt in module_east_map_cache
            else load_east(
                input_path,
                parser_backend,
                east_stage=east_stage,
                object_dispatch_mode=object_dispatch_mode,
                east3_opt_level=east3_opt_level_opt,
                east3_opt_pass=east3_opt_pass_opt,
                dump_east3_before_opt=dump_east3_before_opt,
                dump_east3_after_opt=dump_east3_after_opt,
                dump_east3_opt_trace=dump_east3_opt_trace,
            )
        )
        guard_module_map = select_guard_module_map(input_txt, east_module, module_east_map_cache)
        check_parse_stage_guards(guard_module_map, guard_limits)
        check_analyze_stage_guards(guard_module_map, import_graph_analysis, guard_limits, SCOPE_NESTING_KINDS)
        if dump_deps:
            dep_text = dump_deps_text(east_module)
            if input_txt.endswith(".py"):
                dep_text += dump_deps_graph_text(input_path)
            if output_txt != "":
                out_path = Path(output_txt)
                mkdirs_for_cli(path_parent_text(out_path))
                write_text_file(out_path, dep_text)
            else:
                print(dep_text, end="")
            return 0
        if emit_runtime_cpp:
            if not input_txt.endswith(".py"):
                print("error: --emit-runtime-cpp requires .py input", file=sys.stderr)
                return 1
            module_tail = _runtime_module_tail_from_source_path(input_path)
            if module_tail == "":
                print(
                    "error: --emit-runtime-cpp input must be under src/pytra/std/, src/pytra/utils/, src/pytra/compiler/, or src/pytra/built_in/",
                    file=sys.stderr,
                )
                return 1
            if module_tail.endswith("_impl"):
                print("skip: impl module is hand-written on C++ side: " + module_tail)
                return 0
            ns = top_namespace_opt
            ns = ns if ns != "" else _runtime_namespace_for_tail(module_tail)
            rel_tail = _runtime_output_rel_tail(module_tail)
            out_root = RUNTIME_CPP_GEN_ROOT
            compat_root = RUNTIME_CPP_COMPAT_ROOT
            cpp_out = _join_runtime_path(out_root, rel_tail + ".cpp")
            hdr_out = _join_runtime_path(out_root, rel_tail + ".h")
            compat_cpp_out = _join_runtime_path(compat_root, rel_tail + ".cpp")
            compat_hdr_out = _join_runtime_path(compat_root, rel_tail + ".h")
            mkdirs_for_cli(path_parent_text(cpp_out))
            mkdirs_for_cli(path_parent_text(hdr_out))
            mkdirs_for_cli(path_parent_text(compat_cpp_out))
            mkdirs_for_cli(path_parent_text(compat_hdr_out))
            runtime_ns_map: dict[str, str] = {}
            cpp_txt_runtime: str = _transpile_to_cpp_with_map(
                east_module,
                runtime_ns_map,
                negative_index_mode,
                bounds_check_mode,
                floor_div_mode,
                mod_mode,
                int_width,
                str_index_mode,
                str_slice_mode,
                opt_level,
                ns,
                False,
                cpp_opt_level_opt,
                cpp_opt_pass_opt,
                dump_cpp_ir_before_opt,
                dump_cpp_ir_after_opt,
                dump_cpp_opt_trace,
                cpp_list_model_opt,
            )
            own_runtime_header = '#include "pytra/' + rel_tail + '.h"'
            if own_runtime_header not in cpp_txt_runtime:
                old_runtime_include = '#include "runtime/cpp/pytra/built_in/py_runtime.h"\n'
                new_runtime_include = (
                    '#include "runtime/cpp/pytra/built_in/py_runtime.h"\n\n' + own_runtime_header + "\n"
                )
                cpp_txt_runtime = replace_first(
                    cpp_txt_runtime,
                    old_runtime_include,
                    new_runtime_include,
                )
            cpp_txt_runtime = _prepend_generated_cpp_banner(cpp_txt_runtime, input_path)
            hdr_txt_runtime = build_cpp_header_from_east(east_module, input_path, hdr_out, ns)
            generated_lines_runtime = count_text_lines(cpp_txt_runtime) + count_text_lines(hdr_txt_runtime)
            check_guard_limit("emit", "max_generated_lines", generated_lines_runtime, guard_limits, str(input_path))
            write_text_file(cpp_out, cpp_txt_runtime)
            write_text_file(hdr_out, hdr_txt_runtime)
            compat_hdr_txt = (
                join_str_list(
                    "\n",
                    [
                        "// FORWARDER: generated runtime header moved to pytra-gen.",
                        "#pragma once",
                        "",
                        f'#include "runtime/cpp/pytra-gen/{rel_tail}.h"',
                    ],
                )
                + "\n"
            )
            compat_cpp_txt = (
                join_str_list(
                    "\n",
                    [
                        "// FORWARDER TU: generated runtime source moved to pytra-gen.",
                        f'#include "runtime/cpp/pytra-gen/{rel_tail}.cpp"',
                    ],
                )
                + "\n"
            )
            write_text_file(compat_hdr_out, compat_hdr_txt)
            write_text_file(compat_cpp_out, compat_cpp_txt)
            print("generated: " + str(hdr_out))
            print("generated: " + str(cpp_out))
            print("updated: " + str(compat_hdr_out))
            print("updated: " + str(compat_cpp_out))
            return 0
        if single_file:
            empty_ns: dict[str, str] = {}
            cpp = _transpile_to_cpp_with_map(
                east_module,
                empty_ns,
                negative_index_mode,
                bounds_check_mode,
                floor_div_mode,
                mod_mode,
                int_width,
                str_index_mode,
                str_slice_mode,
                opt_level,
                top_namespace_opt,
                not no_main,
                cpp_opt_level_opt,
                cpp_opt_pass_opt,
                dump_cpp_ir_before_opt,
                dump_cpp_ir_after_opt,
                dump_cpp_opt_trace,
                cpp_list_model_opt,
            )
            check_guard_limit("emit", "max_generated_lines", count_text_lines(cpp), guard_limits, str(input_path))
            if header_output_txt != "":
                hdr_path = Path(header_output_txt)
                mkdirs_for_cli(path_parent_text(hdr_path))
                hdr_txt = build_cpp_header_from_east(east_module, input_path, hdr_path, top_namespace_opt)
                generated_lines_single = count_text_lines(cpp) + count_text_lines(hdr_txt)
                check_guard_limit("emit", "max_generated_lines", generated_lines_single, guard_limits, str(input_path))
                write_text_file(hdr_path, hdr_txt)
        else:
            if input_txt.endswith(".py"):
                module_east_map: dict[str, dict[str, Any]] = (
                    module_east_map_cache
                    if len(module_east_map_cache) > 0
                    else build_module_east_map(
                        input_path,
                        parser_backend,
                        east_stage=east_stage,
                        object_dispatch_mode=object_dispatch_mode,
                    )
                )
            else:
                module_east_map: dict[str, dict[str, Any]] = {str(input_path): east_module}
            out_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out")
            out_dir = Path(output_txt) if output_txt != "" else out_dir
            mf = _write_multi_file_cpp(
                input_path,
                module_east_map,
                out_dir,
                negative_index_mode,
                bounds_check_mode,
                floor_div_mode,
                mod_mode,
                int_width,
                str_index_mode,
                str_slice_mode,
                opt_level,
                top_namespace_opt,
                not no_main,
                cpp_opt_level_opt,
                cpp_opt_pass_opt,
                dump_cpp_ir_before_opt,
                dump_cpp_ir_after_opt,
                dump_cpp_opt_trace,
                guard_limits["max_generated_lines"] if "max_generated_lines" in guard_limits else 0,
                cpp_list_model_opt,
            )
            msg = "multi-file output generated at: " + str(out_dir)
            manifest_obj: Any = mf.get("manifest")
            manifest_txt = manifest_obj if isinstance(manifest_obj, str) else ""
            msg += "\nmanifest: " + manifest_txt + "\n" if manifest_txt != "" else "\n"
            print(msg, end="")
            return 0
    except Exception as ex:
        parsed_err = parse_user_error(str(ex))
        cat = dict_any_get_str(parsed_err, "category")
        if cat != "":
            print_user_error(str(ex))
            return 1
        detail = str(ex)
        print("error: internal error occurred during transpilation.", file=sys.stderr)
        print("[internal_error] this may be a bug; report it with a reproducible case.", file=sys.stderr)
        if detail != "":
            print("detail: " + detail, file=sys.stderr)
        return 1

    if output_txt != "":
        out_path = Path(output_txt)
        mkdirs_for_cli(path_parent_text(out_path))
        write_text_file(out_path, cpp)
    else:
        print(cpp)
    return 0


if __name__ == "__main__":
    sys.exit(main(list(sys.argv[1:])))

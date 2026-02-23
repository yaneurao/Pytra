#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/pytra/compiler/east.py conversion.
"""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.compiler.transpile_cli import append_unique_non_empty, assign_targets, collect_import_modules, collect_store_names_from_target, collect_symbols_from_stmt, collect_symbols_from_stmt_list, count_text_lines, dict_any_get, dict_any_get_str, dict_any_get_list, dict_any_get_dict, dict_any_get_dict_list, dict_any_get_str_list, dict_any_kind, dict_str_get, dump_codegen_options_text, dump_deps_text, extract_function_arg_types_from_python_source, extract_function_signatures_from_python_source, first_import_detail_line, format_graph_list_section, format_import_graph_report, graph_cycle_dfs, inject_after_includes_block, is_known_non_user_import, is_pytra_module_name, join_str_list, local_binding_name, load_east_document, load_east3_document, looks_like_runtime_function_name, make_user_error, meta_import_bindings, meta_qualified_symbol_refs, mkdirs_for_cli, module_analyze_metrics, module_id_from_east_for_graph, module_name_from_path_for_graph, module_parse_metrics, module_export_table, build_module_symbol_index, build_module_east_map_from_analysis, build_module_type_schema, module_rel_label, name_target_id, normalize_param_annotation, parse_py2cpp_argv, check_analyze_stage_guards, check_guard_limit, check_parse_stage_guards, resolve_guard_limits, parse_user_error, print_user_error, path_key_for_graph, path_parent_text, python_module_exists_under, collect_reserved_import_conflicts, rel_disp_for_graph, replace_first, resolve_codegen_options, resolve_module_name, resolve_module_name_for_graph, resolve_user_module_path_for_graph, sanitize_module_label, select_guard_module_map, set_import_module_binding, set_import_symbol_binding, set_import_symbol_binding_and_module_set, sort_str_list_copy, collect_user_module_files_for_graph, finalize_import_graph_analysis, split_graph_issue_entry, split_infix_once, split_top_level_csv, split_top_level_union, split_type_args, split_ws_tokens, stmt_assigned_names, stmt_child_stmt_lists, stmt_list_parse_metrics, stmt_list_scope_depth, stmt_target_name, validate_codegen_options, validate_from_import_symbols_or_raise, validate_import_graph_or_raise, write_text_file
from pytra.compiler.east_parts.core import convert_path, convert_source_to_east_with_backend
from pytra.std import json
from pytra.std import os
from pytra.std.pathlib import Path
from pytra.std import sys


def _build_cpp_hooks_impl() -> dict[str, Any]:
    """selfhost 生成時の既定フック実装（空 dict）。"""
    return {}


from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks as _build_cpp_hooks_impl


RUNTIME_STD_SOURCE_ROOT = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT = Path("src/pytra/utils")
RUNTIME_COMPILER_SOURCE_ROOT = Path("src/pytra/compiler")
RUNTIME_BUILT_IN_SOURCE_ROOT = Path("src/pytra/built_in")
RUNTIME_CPP_COMPAT_ROOT = Path("src/runtime/cpp/pytra")
RUNTIME_CPP_GEN_ROOT = Path("src/runtime/cpp/pytra-gen")


def _module_tail_to_cpp_header_path(module_tail: str) -> str:
    """`a.b.c_impl` を `a/b/c-impl.h` へ変換する。"""
    path_tail = module_tail.replace(".", "/")
    parts: list[str] = path_tail.split("/")
    if parts:
        leaf = parts[-1]
        leaf = leaf[: len(leaf) - 5] + "-impl" if leaf.endswith("_impl") else leaf
        parts[-1] = leaf
    return join_str_list("/", parts) + ".h"


def _runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """`pytra.*` モジュールの runtime C++ ヘッダ実在有無を返す。"""
    def _exists_under_runtime_roots(rel_hdr: str) -> bool:
        return (RUNTIME_CPP_COMPAT_ROOT / rel_hdr).exists() or (RUNTIME_CPP_GEN_ROOT / rel_hdr).exists()

    if module_name_norm.startswith("pytra.std."):
        tail = module_name_norm[10:]
        rel = _module_tail_to_cpp_header_path(tail) if tail else ""
        return bool(rel) and _exists_under_runtime_roots("std/" + rel)
    if module_name_norm.startswith("pytra.utils."):
        tail = module_name_norm[12:]
        rel = _module_tail_to_cpp_header_path(tail) if tail else ""
        return bool(rel) and _exists_under_runtime_roots("utils/" + rel)
    if module_name_norm.startswith("pytra.compiler."):
        tail = module_name_norm[15:]
        rel = _module_tail_to_cpp_header_path(tail) if tail else ""
        return bool(rel) and _exists_under_runtime_roots("compiler/" + rel)
    if module_name_norm.startswith("pytra.built_in."):
        tail = module_name_norm[15:]
        rel = _module_tail_to_cpp_header_path(tail) if tail else ""
        return bool(rel) and _exists_under_runtime_roots("built_in/" + rel)
    return False


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


DEFAULT_BIN_OPS = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "/",
    "Mod": "%",
    "BitAnd": "&",
    "BitOr": "|",
    "BitXor": "^",
    "LShift": "<<",
    "RShift": ">>",
}

DEFAULT_CMP_OPS = {
    "Eq": "==",
    "NotEq": "!=",
    "Lt": "<",
    "LtE": "<=",
    "Gt": ">",
    "GtE": ">=",
    "In": "/* in */",
    "NotIn": "/* not in */",
    "Is": "==",
    "IsNot": "!=",
}

DEFAULT_AUG_OPS = {
    "Add": "+=",
    "Sub": "-=",
    "Mult": "*=",
    "Div": "/=",
    "FloorDiv": "/=",
    "Mod": "%=",
    "BitAnd": "&=",
    "BitOr": "|=",
    "BitXor": "^=",
    "LShift": "<<=",
    "RShift": ">>=",
}

DEFAULT_AUG_BIN = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "//",
    "Mod": "%",
    "BitAnd": "&",
    "BitOr": "|",
    "BitXor": "^",
    "LShift": "<<",
    "RShift": ">>",
}

def load_cpp_profile() -> dict[str, Any]:
    """C++ 用 LanguageProfile を読み込む（失敗時は最小既定）。"""
    profile_loader = CodeEmitter({}, {}, {})
    loaded = profile_loader.load_profile_with_includes(
        "src/profiles/cpp/profile.json",
        anchor_file="src/py2cpp.py",
    )
    if not isinstance(loaded, dict):
        return {"syntax": {}}
    if "syntax" not in loaded or not isinstance(loaded.get("syntax"), dict):
        loaded["syntax"] = {}
    return loaded


def load_cpp_bin_ops() -> dict[str, str]:
    """C++ 用二項演算子マップを返す。"""
    return dict(DEFAULT_BIN_OPS)


def load_cpp_cmp_ops() -> dict[str, str]:
    """C++ 用比較演算子マップを返す。"""
    return dict(DEFAULT_CMP_OPS)


def load_cpp_aug_ops() -> dict[str, str]:
    """C++ 用複合代入演算子マップを返す。"""
    return dict(DEFAULT_AUG_OPS)


def load_cpp_aug_bin() -> dict[str, str]:
    """C++ 用複合代入分解時の演算子マップを返す。"""
    return dict(DEFAULT_AUG_BIN)


def load_cpp_type_map(profile: dict[str, Any] | None = None) -> dict[str, str]:
    """EAST 型 -> C++ 型の基本マップを返す（profile の `types` で上書き可能）。"""
    out: dict[str, str] = {
        "int8": "int8",
        "uint8": "uint8",
        "int16": "int16",
        "uint16": "uint16",
        "int32": "int32",
        "uint32": "uint32",
        "int64": "int64",
        "uint64": "uint64",
        "float32": "float32",
        "float64": "float64",
        "bool": "bool",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
        "Path": "Path",
        "Exception": "::std::runtime_error",
        "Any": "object",
        "object": "object",
    }
    if isinstance(profile, dict):
        type_map = dict_any_get_dict(profile, "types")
        for name, mapped in type_map.items():
            if isinstance(name, str) and isinstance(mapped, str) and name != "" and mapped != "":
                out[name] = mapped
    return out


def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:
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


def load_cpp_identifier_rules(profile: dict[str, Any] | None = None) -> tuple[set[str], str]:
    """識別子リネーム規則を返す（profile.syntax.identifiers で上書き可能）。"""
    reserved: set[str] = {
        "alignas", "alignof", "asm", "auto", "break", "case", "catch", "char", "class", "const", "constexpr",
        "continue", "default", "delete", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "namespace", "new", "operator", "private", "protected", "public", "register",
        "return", "short", "signed", "sizeof", "static", "struct", "switch", "template", "this", "throw", "try",
        "typedef", "typename", "union", "unsigned", "virtual", "void", "volatile", "while",
    }
    rename_prefix = "py_"
    if isinstance(profile, dict):
        syntax_map = dict_any_get_dict(profile, "syntax")
        identifiers = dict_any_get_dict(syntax_map, "identifiers")
        configured = dict_any_get_list(identifiers, "reserved_words")
        if len(configured) > 0:
            reserved = set()
            for item in configured:
                if isinstance(item, str) and item != "":
                    reserved.add(item)
        configured_prefix = dict_any_get_str(identifiers, "rename_prefix", "")
        if configured_prefix != "":
            rename_prefix = configured_prefix
    return reserved, rename_prefix


def load_cpp_module_attr_call_map(profile: dict[str, Any] = {}) -> dict[str, dict[str, str]]:
    """C++ の `module.attr(...)` -> ランタイム呼び出しマップを返す。"""
    out: dict[str, dict[str, str]] = {}
    if not isinstance(profile, dict):
        return out
    runtime_calls = dict_any_get_dict(profile, "runtime_calls")
    module_attr = dict_any_get_dict(runtime_calls, "module_attr_call")
    for module_name, ent_obj in module_attr.items():
        if not isinstance(module_name, str):
            continue
        ent = ent_obj if isinstance(ent_obj, dict) else {}
        mapped: dict[str, str] = {}
        for attr_name, runtime_name in ent.items():
            if isinstance(attr_name, str) and isinstance(runtime_name, str):
                if runtime_name:
                    mapped[attr_name] = runtime_name
        if mapped:
            out[module_name] = mapped
    return out


BIN_OPS: dict[str, str] = load_cpp_bin_ops()
CMP_OPS: dict[str, str] = load_cpp_cmp_ops()
AUG_OPS: dict[str, str] = load_cpp_aug_ops()
AUG_BIN: dict[str, str] = load_cpp_aug_bin()


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


class CppEmitter(CodeEmitter):
    def __init__(
        self,
        east_doc: dict[str, Any],
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
    ) -> None:
        """変換設定とクラス解析用の状態を初期化する。"""
        profile = load_cpp_profile()
        hooks: dict[str, Any] = load_cpp_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        self.negative_index_mode = negative_index_mode
        self.bounds_check_mode = bounds_check_mode
        self.floor_div_mode = floor_div_mode
        self.mod_mode = mod_mode
        self.int_width = int_width
        self.str_index_mode = str_index_mode
        self.str_slice_mode = str_slice_mode
        self.opt_level = opt_level
        self.top_namespace = top_namespace
        self.emit_main = emit_main
        # NOTE:
        # self-host compile path currently treats EAST payload values as dynamic,
        # so dict[str, Any] -> dict iteration for renaming is disabled for now.
        self.renamed_symbols: dict[str, str] = {}
        self.current_class_name: str | None = None
        self.current_class_base_name: str = ""
        self.current_class_fields: dict[str, str] = {}
        self.current_class_static_fields: set[str] = set()
        self.class_method_names: dict[str, set[str]] = {}
        self.class_method_arg_types: dict[str, dict[str, list[str]]] = {}
        self.class_method_arg_names: dict[str, dict[str, list[str]]] = {}
        self.class_base: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_storage_hints: dict[str, str] = {}
        self.ref_classes: set[str] = set()
        self.value_classes: set[str] = set()
        self.type_map: dict[str, str] = load_cpp_type_map(self.profile)
        if self.int_width == "32":
            self.type_map["int64"] = "int32"
            self.type_map["uint64"] = "uint32"
        self.module_attr_call_map: dict[str, dict[str, str]] = load_cpp_module_attr_call_map(self.profile)
        self.reserved_words: set[str] = set()
        self.rename_prefix: str = "py_"
        self.reserved_words, self.rename_prefix = load_cpp_identifier_rules(self.profile)
        self.reserved_words.add("main")
        # import 解決テーブルは init_base_state() 側を正とする。
        # CppEmitter 側で再代入すると selfhost 生成C++で基底メンバと
        # 派生メンバが分離し、基底 helper から空テーブルを参照しうる。
        self.module_namespace_map = module_namespace_map
        self.function_arg_types: dict[str, list[str]] = {}
        self.function_return_types: dict[str, str] = {}
        self.current_function_return_type: str = ""
        self.current_function_is_generator: bool = False
        self.current_function_yield_buffer: str = ""
        self.current_function_yield_type: str = "unknown"
        self.declared_var_types: dict[str, str] = {}
        self._module_fn_arg_type_cache: dict[str, dict[str, list[str]]] = {}

    def current_scope_names(self) -> set[str]:
        """現在スコープの識別子集合を返す（selfhost では CppEmitter 側を正とする）。"""
        if len(self.scope_stack) == 0:
            self.scope_stack.append(set())
        return self.scope_stack[-1]

    def declare_in_current_scope(self, name: str) -> None:
        """現在スコープへ識別子を追加する。"""
        if not name:
            return
        scope = self.current_scope_names()
        scope.add(name)
        self.scope_stack[-1] = scope

    def is_declared(self, name: str) -> bool:
        """現在の可視スコープで識別子が宣言済みかを返す。"""
        for scope in reversed(self.scope_stack):
            if name in scope:
                return True
        return False

    def get_expr_type(self, expr: Any) -> str:
        """EAST 型に加えて現在スコープの推論型テーブルも参照する。"""
        node_for_base = self.any_to_dict_or_empty(expr)
        t = self.any_dict_get_str(node_for_base, "resolved_type", "")
        if t:
            t = self.normalize_type_name(t)
        if t not in {"", "unknown"}:
            return t
        kind = self._node_kind_from_dict(node_for_base)
        if kind == "Name":
            nm = self.any_to_str(node_for_base.get("id"))
            if nm in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[nm])
        if kind == "Attribute":
            owner = self.any_to_dict_or_empty(node_for_base.get("value"))
            if self._node_kind_from_dict(owner) == "Name":
                owner_name = self.any_to_str(owner.get("id"))
                attr = self.any_to_str(node_for_base.get("attr"))
                if owner_name == "self" and attr in self.current_class_fields:
                    return self.normalize_type_name(self.current_class_fields[attr])
        return ""

    def _normalize_runtime_module_name(self, module_name: str) -> str:
        """旧 `pylib.*` 名を `pytra.*` 名へ正規化する。"""
        if module_name.startswith("pytra.std."):
            return module_name
        if module_name == "pytra.std":
            return "pytra.std"
        if module_name.startswith("pytra.utils."):
            return module_name
        if module_name == "pytra.utils":
            return "pytra.utils"
        if module_name.startswith("pytra.compiler."):
            return module_name
        if module_name == "pytra.compiler":
            return "pytra.compiler"
        if module_name.startswith("pytra.built_in."):
            return module_name
        if module_name == "pytra.built_in":
            return "pytra.built_in"
        if module_name.startswith("pytra.runtime."):
            # 旧互換: runtime 名は utils 名へ正規化する。
            return "pytra.utils." + module_name[14:]
        if module_name == "pytra.runtime":
            return "pytra.utils"
        if module_name.startswith("pylib.tra."):
            return "pytra.utils." + module_name[10:]
        if module_name == "pylib.tra":
            return "pytra.utils"
        if python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, module_name):
            return "pytra.std." + module_name
        if python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, module_name):
            return "pytra.utils." + module_name
        if python_module_exists_under(RUNTIME_COMPILER_SOURCE_ROOT, module_name):
            return "pytra.compiler." + module_name
        if python_module_exists_under(RUNTIME_BUILT_IN_SOURCE_ROOT, module_name):
            return "pytra.built_in." + module_name
        return module_name

    def _module_name_to_cpp_include(self, module_name: str) -> str:
        """Python import モジュール名を C++ include へ解決する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/std/" + _module_tail_to_cpp_header_path(tail)
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/utils/" + _module_tail_to_cpp_header_path(tail)
        if module_name_norm.startswith("pytra.compiler."):
            tail = module_name_norm[15:]
            if python_module_exists_under(RUNTIME_COMPILER_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/compiler/" + _module_tail_to_cpp_header_path(tail)
        if module_name_norm.startswith("pytra.built_in."):
            tail = module_name_norm[15:]
            if python_module_exists_under(RUNTIME_BUILT_IN_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/built_in/" + _module_tail_to_cpp_header_path(tail)
        return ""

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """Python import モジュール名を C++ namespace へ解決する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if tail:
                return "pytra::std::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if tail:
                return "pytra::utils::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.compiler."):
            tail = module_name_norm[15:]
            if tail:
                return "pytra::compiler::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.built_in."):
            return ""
        if module_name_norm.startswith("pytra."):
            tail = module_name_norm[6:]
            if tail:
                return "pytra::" + tail.replace(".", "::")
            return "pytra"
        inc = self._module_name_to_cpp_include(module_name_norm)
        if inc.startswith("pytra/std/") and inc.endswith(".h"):
            tail: str = inc[10 : len(inc) - 2].replace("/", "::")
            if tail:
                return "pytra::" + tail
        if inc.startswith("pytra/utils/") and inc.endswith(".h"):
            tail: str = inc[12 : len(inc) - 2].replace("/", "::")
            if tail:
                return "pytra::utils::" + tail
        if inc.startswith("pytra/compiler/") and inc.endswith(".h"):
            tail = inc[15 : len(inc) - 2].replace("/", "::")
            if tail:
                return "pytra::compiler::" + tail
        return ""

    def _runtime_symbol_module_prefix(self, mod_name: str) -> str:
        """runtime symbol include 解決で使う module prefix（`pytra.std.` 等）を返す。"""
        if mod_name == "pytra.std":
            return "pytra.std."
        if mod_name == "pytra.utils":
            return "pytra.utils."
        if mod_name == "pytra.built_in":
            return "pytra.built_in."
        return ""

    def _append_runtime_symbol_include(
        self,
        includes: list[str],
        seen: set[str],
        mod_name: str,
        symbol: str,
    ) -> None:
        """`pytra.std/utils` の symbol include を必要時のみ追加する。"""
        runtime_prefix = self._runtime_symbol_module_prefix(mod_name)
        if not runtime_prefix or not symbol:
            return
        sym_inc = self._module_name_to_cpp_include(runtime_prefix + symbol)
        append_unique_non_empty(includes, seen, sym_inc)

    def _collect_import_cpp_includes(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """EAST body から必要な C++ include を収集する。"""
        includes: list[str] = []
        seen: set[str] = set()
        bindings = dict_any_get_dict_list(meta, "import_bindings")
        if bindings:
            for item in bindings:
                mod_name = self._normalize_runtime_module_name(dict_any_get_str(item, "module_id"))
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                if dict_any_get_str(item, "binding_kind") == "symbol":
                    self._append_runtime_symbol_include(includes, seen, mod_name, dict_any_get_str(item, "export_name"))
            return sort_str_list_copy(includes)
        for stmt in body:
            kind = self._node_kind_from_dict(stmt)
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    append_unique_non_empty(
                        includes, seen, self._module_name_to_cpp_include(dict_any_get_str(ent, "name"))
                    )
            elif kind == "ImportFrom":
                mod_name = self._normalize_runtime_module_name(dict_any_get_str(stmt, "module"))
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                for ent in self._dict_stmt_list(stmt.get("names")):
                    self._append_runtime_symbol_include(includes, seen, mod_name, dict_any_get_str(ent, "name"))
        return sort_str_list_copy(includes)

    def _seed_legacy_import_symbols_from_meta(self, meta: dict[str, Any]) -> None:
        """legacy `meta.import_symbols` を `self.import_symbols` へ反映する。"""
        for local_name, sym_obj in dict_any_get_dict(meta, "import_symbols").items():
            if not isinstance(local_name, str):
                continue
            set_import_symbol_binding_and_module_set(
                self.import_symbols,
                self.import_symbol_modules,
                local_name,
                dict_any_get_str(sym_obj if isinstance(sym_obj, dict) else {}, "module"),
                dict_any_get_str(sym_obj if isinstance(sym_obj, dict) else {}, "name"),
            )

    def _seed_legacy_import_modules_from_meta(self, meta: dict[str, Any]) -> None:
        """legacy `meta.import_modules` を `self.import_modules` へ反映する。"""
        for local_name, module_id_any in dict_any_get_dict(meta, "import_modules").items():
            if not isinstance(local_name, str):
                continue
            set_import_module_binding(self.import_modules, local_name, self.any_to_str(module_id_any))

    def _seed_legacy_import_maps_from_meta(self, meta: dict[str, Any]) -> None:
        """legacy import メタを symbols/modules の両方へ反映する。"""
        self._seed_legacy_import_symbols_from_meta(meta)
        self._seed_legacy_import_modules_from_meta(meta)

    def _seed_import_maps_from_meta(self) -> None:
        """`meta.import_bindings`（または互換メタ）から import 束縛マップを初期化する。"""
        meta = dict_any_get_dict(self.doc, "meta")
        refs = meta_qualified_symbol_refs(self.doc)
        bindings = meta_import_bindings(self.doc)
        if bindings:
            for ref_item in refs:
                set_import_symbol_binding_and_module_set(
                    self.import_symbols,
                    self.import_symbol_modules,
                    dict_str_get(ref_item, "local_name", ""),
                    dict_str_get(ref_item, "module_id", ""),
                    dict_str_get(ref_item, "symbol", ""),
                )
            for item in bindings:
                binding_kind = dict_str_get(item, "binding_kind", "")
                if binding_kind == "module":
                    set_import_module_binding(
                        self.import_modules,
                        dict_str_get(item, "local_name", ""),
                        dict_str_get(item, "module_id", ""),
                    )
                elif binding_kind == "symbol" and not refs:
                    set_import_symbol_binding_and_module_set(
                        self.import_symbols,
                        self.import_symbol_modules,
                        dict_str_get(item, "local_name", ""),
                        dict_str_get(item, "module_id", ""),
                        dict_str_get(item, "export_name", ""),
                    )
            if not self.import_symbols:
                self._seed_legacy_import_symbols_from_meta(meta)
            if not self.import_modules:
                self._seed_legacy_import_modules_from_meta(meta)
            return
        # canonical メタが空の場合は legacy メタへフォールバックする。
        self._seed_legacy_import_maps_from_meta(meta)
        return

    def emit_block_comment(self, text: str) -> None:
        """Emit docstring/comment as C-style block comment."""
        self.emit("/* " + text + " */")

    def _module_source_path_for_name(self, module_name: str) -> Path:
        """`pytra.*` モジュール名から runtime source `.py` パスを返す（未解決時は空 Path）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail: str = str(module_name_norm[10:].replace(".", "/"))
            std_root_txt: str = str(RUNTIME_STD_SOURCE_ROOT)
            p_txt: str = std_root_txt + "/" + tail + ".py"
            p = Path(p_txt)
            if p.exists():
                return p
            init_txt: str = std_root_txt + "/" + tail + "/__init__.py"
            init_p = Path(init_txt)
            if init_p.exists():
                return init_p
            return Path("")
        if module_name_norm.startswith("pytra.utils."):
            tail: str = str(module_name_norm[12:].replace(".", "/"))
            utils_root_txt: str = str(RUNTIME_UTILS_SOURCE_ROOT)
            p_txt: str = utils_root_txt + "/" + tail + ".py"
            p = Path(p_txt)
            if p.exists():
                return p
            init_txt: str = utils_root_txt + "/" + tail + "/__init__.py"
            init_p = Path(init_txt)
            if init_p.exists():
                return init_p
            return Path("")
        return Path("")

    def _module_function_arg_types(self, module_name: str, fn_name: str) -> list[str]:
        """モジュール関数の引数型列を返す（不明時は空 list）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_fn_arg_type_cache.get(module_name_norm)
        if isinstance(cached, dict):
            sig = cached.get(fn_name)
            if isinstance(sig, list):
                return sig
            return []
        fn_map: dict[str, list[str]] = {}
        src_path: Path = self._module_source_path_for_name(module_name_norm)
        if not str(src_path):
            self._module_fn_arg_type_cache[module_name_norm] = fn_map
            return []
        fn_map = extract_function_arg_types_from_python_source(src_path)
        self._module_fn_arg_type_cache[module_name_norm] = fn_map
        sig = fn_map.get(fn_name)
        if isinstance(sig, list):
            return sig
        return []

    def _coerce_args_for_module_function(
        self,
        module_name: str,
        fn_name: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """モジュール関数シグネチャに基づいて引数を必要最小限で boxing する。"""
        target_types = self._module_function_arg_types(module_name, fn_name)
        if len(target_types) == 0:
            return args
        out: list[str] = []
        for i, arg in enumerate(args):
            a = arg
            if i < len(target_types):
                tt = target_types[i]
                arg_t = "unknown"
                if i < len(arg_nodes):
                    arg_t_obj = self.get_expr_type(arg_nodes[i])
                    if isinstance(arg_t_obj, str):
                        arg_t = arg_t_obj
                arg_t = self.infer_rendered_arg_type(a, arg_t, self.declared_var_types)
                arg_is_unknown = arg_t == "" or arg_t == "unknown"
                if self.is_any_like_type(tt) and (arg_is_unknown or not self.is_any_like_type(arg_t)):
                    if not self.is_boxed_object_expr(a):
                        arg_node = arg_nodes[i] if i < len(arg_nodes) else {}
                        arg_node_d = self.any_to_dict_or_empty(arg_node)
                        if len(arg_node_d) > 0:
                            a = self.render_expr(self._build_box_expr_node(arg_node))
                        else:
                            a = f"make_object({a})"
            out.append(a)
        return out

    def _coerce_py_assert_args(
        self,
        fn_name: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """`py_assert_*` 呼び出しで object 引数が必要な位置を boxing する。"""
        out: list[str] = []
        nodes = arg_nodes
        for i, arg in enumerate(args):
            a = arg
            needs_object = False
            if fn_name == "py_assert_stdout":
                needs_object = i == 1
            elif fn_name == "py_assert_eq":
                needs_object = i < 2
            if needs_object and not self.is_boxed_object_expr(a):
                arg_t = ""
                if i < len(nodes):
                    at = self.get_expr_type(nodes[i])
                    if isinstance(at, str):
                        arg_t = at
                arg_t = self.infer_rendered_arg_type(a, arg_t, self.declared_var_types)
                if not self.is_any_like_type(arg_t):
                    arg_node = nodes[i] if i < len(nodes) else {}
                    arg_node_d = self.any_to_dict_or_empty(arg_node)
                    if len(arg_node_d) > 0:
                        a = self.render_expr(self._build_box_expr_node(arg_node))
                    else:
                        a = f"make_object({a})"
            out.append(a)
        return out

    def _lookup_module_attr_runtime_call(self, module_name: str, attr: str) -> str:
        """`module.attr` から runtime_call 名を引く（pytra.* は短縮名フォールバックしない）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        owner_keys: list[str] = [module_name_norm]
        short_name = self._last_dotted_name(module_name_norm)
        # `pytra.*` は正規モジュール名で解決し、短縮名への暗黙フォールバックは使わない。
        if short_name != module_name_norm and not module_name_norm.startswith("pytra."):
            owner_keys.append(short_name)
        for owner_key in owner_keys:
            if owner_key in self.module_attr_call_map:
                owner_map = self.module_attr_call_map[owner_key]
                if attr in owner_map:
                    mapped = owner_map[attr]
                    if mapped:
                        return mapped
        return ""

    def _resolve_runtime_call_for_imported_symbol(self, module_name: str, symbol_name: str) -> str | None:
        """`from X import Y` で取り込まれた Y 呼び出しの runtime 名を返す。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        mapped = self._lookup_module_attr_runtime_call(module_name_norm, symbol_name)
        if mapped:
            return mapped
        ns = self._module_name_to_cpp_namespace(module_name_norm)
        if ns:
            return f"{ns}::{symbol_name}"
        return None

    def _is_module_definition_stmt(self, stmt: dict[str, Any]) -> bool:
        """トップレベルで namespace 直下に置ける定義文かを返す。"""
        kind = self._node_kind_from_dict(stmt)
        return kind in {"ClassDef", "FunctionDef", "Import", "ImportFrom"}

    def _split_module_top_level_stmts(
        self,
        body: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """トップレベル文を「定義文」と「実行文」へ分割する。"""
        defs: list[dict[str, Any]] = []
        runtime: list[dict[str, Any]] = []
        for stmt in body:
            if self._is_module_definition_stmt(stmt):
                defs.append(stmt)
            else:
                runtime.append(stmt)
        return defs, runtime

    def _infer_module_global_decl_type(self, stmt: dict[str, Any]) -> str:
        """トップレベル Name 代入を global 宣言する際の型を推定する。"""
        kind = self._node_kind_from_dict(stmt)
        if kind == "AnnAssign":
            ann_t = self.normalize_type_name(self.any_to_str(stmt.get("annotation")))
            if ann_t not in {"", "unknown"}:
                return ann_t
        d0 = self.normalize_type_name(self.any_dict_get_str(stmt, "decl_type", ""))
        d1 = self.normalize_type_name(self.get_expr_type(stmt.get("target")))
        d2 = self.normalize_type_name(self.get_expr_type(stmt.get("value")))
        picked = ""
        for t in [d0, d1, d2]:
            if t not in {"", "unknown"}:
                picked = t
                break
        if not picked:
            picked = d2 or d1 or d0
        picked = "Any" if picked == "None" else picked
        picked = picked or "object"
        return picked

    def _collect_module_global_decls(self, runtime_stmts: list[dict[str, Any]]) -> list[tuple[str, str]]:
        """トップレベル実行文から global 先行宣言すべき Name と型を抽出する。"""
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in runtime_stmts:
            kind = self._node_kind_from_dict(stmt)
            if kind not in {"Assign", "AnnAssign"}:
                continue
            target_obj: object = stmt.get("target")
            if not self.is_plain_name_expr(target_obj):
                continue
            target = self.any_to_dict_or_empty(target_obj)
            raw_name = self.any_dict_get_str(target, "id", "")
            if not raw_name:
                continue
            name = self.rename_if_reserved(raw_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            if name in seen:
                continue
            ty = self._infer_module_global_decl_type(stmt)
            cpp_t = self._cpp_type_text(ty)
            # callable/unknown 由来の auto は先行宣言せず、init 関数内ローカル宣言へ委譲する。
            if cpp_t == "auto":
                continue
            seen.add(name)
            out.append((name, ty))
        return out

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
        self._seed_import_maps_from_meta()
        meta: dict[str, Any] = dict_any_get_dict(self.doc, "meta")
        body: list[dict[str, Any]] = []
        raw_body = self.any_dict_get_list(self.doc, "body")
        if isinstance(raw_body, list):
            for s in raw_body:
                if isinstance(s, dict):
                    body.append(s)
        for stmt in body:
            if self._node_kind_from_dict(stmt) == "ClassDef":
                cls_name = self.any_dict_get_str(stmt, "name", "")
                if cls_name != "":
                    self.class_names.add(cls_name)
                    mset: set[str] = set()
                    marg: dict[str, list[str]] = {}
                    marg_names: dict[str, list[str]] = {}
                    class_body: list[dict[str, Any]] = []
                    raw_class_body = self.any_dict_get_list(stmt, "body")
                    if isinstance(raw_class_body, list):
                        for s in raw_class_body:
                            if isinstance(s, dict):
                                class_body.append(s)
                    for s in class_body:
                        if self._node_kind_from_dict(s) == "FunctionDef":
                            fn_name = self.any_dict_get_str(s, "name", "")
                            mset.add(fn_name)
                            arg_types = self.any_to_dict_or_empty(s.get("arg_types"))
                            arg_order = self.any_dict_get_list(s, "arg_order")
                            ordered: list[str] = []
                            ordered_names: list[str] = []
                            for raw_n in arg_order:
                                if isinstance(raw_n, str):
                                    n = str(raw_n)
                                    if n != "self":
                                        ordered_names.append(n)
                                        if n in arg_types:
                                            ordered.append(self.any_to_str(arg_types.get(n)))
                            marg[fn_name] = ordered
                            marg_names[fn_name] = ordered_names
                    self.class_method_names[cls_name] = mset
                    self.class_method_arg_types[cls_name] = marg
                    self.class_method_arg_names[cls_name] = marg_names
                    base_raw = stmt.get("base")
                    base = str(base_raw) if isinstance(base_raw, str) else ""
                    self.class_base[cls_name] = base
                    hint = self.any_dict_get_str(stmt, "class_storage_hint", "ref")
                    self.class_storage_hints[cls_name] = hint if hint in {"value", "ref"} else "ref"
            elif self._node_kind_from_dict(stmt) == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                if fn_name != "":
                    fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                    arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
                    arg_order = self.any_dict_get_list(stmt, "arg_order")
                    ordered: list[str] = []
                    for raw_n in arg_order:
                        if isinstance(raw_n, str):
                            n = str(raw_n)
                            if n in arg_types:
                                ordered.append(self.any_to_str(arg_types.get(n)))
                    self.function_arg_types[fn_name] = ordered
                    self.function_return_types[fn_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))

        self.ref_classes = {name for name, hint in self.class_storage_hints.items() if hint == "ref"}
        changed = True
        while changed:
            changed = False
            for name, base in self.class_base.items():
                if base != "" and base in self.ref_classes and name not in self.ref_classes:
                    self.ref_classes.add(name)
                    changed = True
                if base != "" and name in self.ref_classes and base in self.class_names and base not in self.ref_classes:
                    self.ref_classes.add(base)
                    changed = True
        self.value_classes = {name for name in self.class_names if name not in self.ref_classes}

        self.emit_module_leading_trivia()
        header_text: str = CPP_HEADER
        if len(header_text) > 0 and header_text[-1] == NEWLINE_CHAR:
            header_text = header_text[:-1]
        self.emit(header_text)
        extra_includes = self._collect_import_cpp_includes(body, meta)
        for inc in extra_includes:
            self.emit(f"#include \"{inc}\"")
        self.emit("")

        if self.top_namespace != "":
            self.emit(f"namespace {self.top_namespace} {{")
            self.emit("")
            self.indent += 1

        module_defs, module_runtime = self._split_module_top_level_stmts(body)
        module_globals = self._collect_module_global_decls(module_runtime)

        for g_name, g_ty in module_globals:
            self.emit(f"{self._cpp_type_text(g_ty)} {g_name};")
            self.declare_in_current_scope(g_name)
            self.declared_var_types[g_name] = g_ty
        if len(module_globals) > 0:
            self.emit("")

        for stmt in module_defs:
            self.emit_stmt(stmt)
            self.emit("")

        has_module_runtime = len(module_runtime) > 0
        if has_module_runtime:
            self.emit("static void __pytra_module_init() {")
            self.indent += 1
            self.emit("static bool __initialized = false;")
            self.emit("if (__initialized) return;")
            self.emit("__initialized = true;")
            self.scope_stack.append(set())
            self.emit_stmt_list(module_runtime)
            self.scope_stack.pop()
            self.indent -= 1
            self.emit("}")
            self.emit("")

        if self.emit_main:
            if self.top_namespace != "":
                self.indent -= 1
                self.emit(f"}}  // namespace {self.top_namespace}")
                self.emit("")
            has_pytra_main = False
            for stmt in body:
                if self._node_kind_from_dict(stmt) == "FunctionDef" and self.any_to_str(stmt.get("name")) == "__pytra_main":
                    has_pytra_main = True
                    break
            self.emit("int main(int argc, char** argv) {")
            self.indent += 1
            self.emit("pytra_configure_from_argv(argc, argv);")
            self.scope_stack.append(set())
            if has_module_runtime:
                if self.top_namespace != "":
                    self.emit(f"{self.top_namespace}::__pytra_module_init();")
                else:
                    self.emit("__pytra_module_init();")
            main_guard: list[dict[str, Any]] = []
            raw_main_guard = self.any_dict_get_list(self.doc, "main_guard_body")
            if isinstance(raw_main_guard, list):
                for s in raw_main_guard:
                    if isinstance(s, dict):
                        main_guard.append(s)
            if has_pytra_main:
                default_args: list[str] = []
                pytra_args = self.function_arg_types.get("__pytra_main", default_args)
                if isinstance(pytra_args, list) and len(pytra_args) >= 1:
                    if self.top_namespace != "":
                        self.emit(f"{self.top_namespace}::__pytra_main(py_runtime_argv());")
                    else:
                        self.emit("__pytra_main(py_runtime_argv());")
                else:
                    if self.top_namespace != "":
                        self.emit(f"{self.top_namespace}::__pytra_main();")
                    else:
                        self.emit("__pytra_main();")
            else:
                if self.top_namespace != "":
                    self.emit(f"using namespace {self.top_namespace};")
                self.emit_stmt_list(main_guard)
            self.scope_stack.pop()
            self.emit("return 0;")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        elif self.top_namespace != "":
            self.indent -= 1
            self.emit(f"}}  // namespace {self.top_namespace}")
            self.emit("")
        return NEWLINE_CHAR.join(self.lines)

    def apply_cast(self, rendered_expr: str, to_type: str) -> str:
        """EAST の cast 指示に従い C++ 側の明示キャストを適用する。"""
        to_type_text = to_type if isinstance(to_type, str) else ""
        if to_type_text == "byte":
            to_type_text = "uint8"
        if to_type_text == "":
            return rendered_expr
        norm_t = self.normalize_type_name(to_type_text)
        if norm_t in {"float32", "float64"}:
            return f"py_to_float64({rendered_expr})"
        if norm_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return f"{norm_t}(py_to_int64({rendered_expr}))"
        if norm_t == "bool":
            return f"py_to_bool({rendered_expr})"
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
            op = "&&" if self.any_dict_get_str(expr_dict, "op", "") == "And" else "||"
            wrapped_values = [f"({txt})" for txt in value_texts]
            sep = f" {op} "
            return sep.join(wrapped_values)

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

    def _try_optimize_char_compare(
        self,
        left_node: Any,
        op: str,
        right_node: Any,
    ) -> str:
        """1文字比較を `'x'` / `.at(i)` 形へ最適化できるか判定する。"""
        if not self._opt_ge(3):
            return ""
        if op not in {"Eq", "NotEq"}:
            return ""
        cop = "==" if op == "Eq" else "!="
        l_access = self._str_index_char_access(left_node)
        r_ch = self._one_char_str_const(right_node)
        if l_access != "" and r_ch != "":
            return f"{l_access} {cop} {cpp_char_lit(r_ch)}"
        r_access = self._str_index_char_access(right_node)
        l_ch = self._one_char_str_const(left_node)
        if r_access != "" and l_ch != "":
            return f"{cpp_char_lit(l_ch)} {cop} {r_access}"
        l_ty = self.get_expr_type(left_node)
        if l_ty == "uint8" and r_ch != "":
            return f"{self.render_expr(left_node)} {cop} {cpp_char_lit(r_ch)}"
        r_ty = self.get_expr_type(right_node)
        if r_ty == "uint8" and l_ch != "":
            return f"{cpp_char_lit(l_ch)} {cop} {self.render_expr(right_node)}"
        return ""

    def _byte_from_str_expr(self, node: Any) -> str:
        """str 系式を uint8 初期化向けの char 式へ変換する。"""
        ch = self._one_char_str_const(node)
        if ch != "":
            return cpp_char_lit(ch)
        return self._str_index_char_access(node)

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

    def _infer_name_assign_type(self, stmt: dict[str, Any], target_node: dict[str, Any]) -> str:
        """`Name = ...` / `AnnAssign Name` の宣言候補型を推定する。"""
        decl_t = self.any_dict_get_str(stmt, "decl_type", "")
        if decl_t != "":
            return self.normalize_type_name(decl_t)
        ann_t = self.any_dict_get_str(stmt, "annotation", "")
        if ann_t != "":
            return self.normalize_type_name(ann_t)
        t_target = self.get_expr_type(stmt.get("target"))
        if isinstance(t_target, str) and t_target != "":
            return self.normalize_type_name(t_target)
        t_value = self.get_expr_type(stmt.get("value"))
        if isinstance(t_value, str) and t_value != "":
            return self.normalize_type_name(t_value)
        return ""

    def _collect_assigned_name_types(self, stmts: list[dict[str, Any]]) -> dict[str, str]:
        """文リスト中の `Name` 代入候補型を収集する。"""
        out: dict[str, str] = {}
        for st in stmts:
            kind = self._node_kind_from_dict(st)
            if kind == "Assign":
                tgt = self.any_to_dict_or_empty(st.get("target"))
                if self._node_kind_from_dict(tgt) == "Name":
                    name = self.any_to_str(tgt.get("id"))
                    if name != "":
                        out[name] = self._infer_name_assign_type(st, tgt)
                elif self._node_kind_from_dict(tgt) == "Tuple":
                    elems = self.any_dict_get_list(tgt, "elements")
                    value_t_obj = self.get_expr_type(st.get("value"))
                    value_t = value_t_obj if isinstance(value_t_obj, str) else ""
                    tuple_t = ""
                    if value_t.startswith("tuple[") and value_t.endswith("]"):
                        tuple_t = value_t
                    elif self._contains_text(value_t, "|"):
                        for part in self.split_union(value_t):
                            if part.startswith("tuple[") and part.endswith("]"):
                                tuple_t = part
                                break
                    elem_types: list[str] = []
                    if tuple_t != "":
                        elem_types = self.split_generic(tuple_t[6:-1])
                    for i, elem in enumerate(elems):
                        ent = self.any_to_dict_or_empty(elem)
                        if self._node_kind_from_dict(ent) == "Name":
                            nm = self.any_to_str(ent.get("id"))
                            if nm != "":
                                et = ""
                                if i < len(elem_types):
                                    et = self.normalize_type_name(elem_types[i])
                                if et == "":
                                    t_ent = self.get_expr_type(elem)
                                    if isinstance(t_ent, str):
                                        et = self.normalize_type_name(t_ent)
                                out[nm] = et
            elif kind == "AnnAssign":
                tgt = self.any_to_dict_or_empty(st.get("target"))
                if self._node_kind_from_dict(tgt) == "Name":
                    name = self.any_to_str(tgt.get("id"))
                    if name != "":
                        out[name] = self._infer_name_assign_type(st, tgt)
            elif kind == "If":
                child_body = self._collect_assigned_name_types(self._dict_stmt_list(st.get("body")))
                child_else = self._collect_assigned_name_types(self._dict_stmt_list(st.get("orelse")))
                for nm, ty in child_body.items():
                    out[nm] = ty
                for nm, ty in child_else.items():
                    if nm in out:
                        out[nm] = self._merge_decl_types_for_branch_join(out[nm], ty)
                    else:
                        out[nm] = ty
            elif kind == "Try":
                child_groups: list[list[dict[str, Any]]] = []
                child_groups.append(self._dict_stmt_list(st.get("body")))
                child_groups.append(self._dict_stmt_list(st.get("orelse")))
                child_groups.append(self._dict_stmt_list(st.get("finalbody")))
                for h in self._dict_stmt_list(st.get("handlers")):
                    child_groups.append(self._dict_stmt_list(h.get("body")))
                for grp in child_groups:
                    child_map = self._collect_assigned_name_types(grp)
                    for nm, ty in child_map.items():
                        if nm in out:
                            out[nm] = self._merge_decl_types_for_branch_join(out[nm], ty)
                        else:
                            out[nm] = ty
        return out

    def _mark_mutated_param_from_target(self, target_obj: Any, params: set[str], out: set[str]) -> None:
        """代入ターゲットから、破壊的変更対象の引数名を再帰的に抽出する。"""
        tgt = self.any_to_dict_or_empty(target_obj)
        tkind = self._node_kind_from_dict(tgt)
        if tkind == "Name":
            nm = self.any_to_str(tgt.get("id"))
            if nm in params:
                out.add(nm)
            return
        if tkind == "Subscript":
            base = self.any_to_dict_or_empty(tgt.get("value"))
            if self._node_kind_from_dict(base) == "Name":
                nm = self.any_to_str(base.get("id"))
                if nm in params:
                    out.add(nm)
            return
        if tkind == "Attribute":
            owner = self.any_to_dict_or_empty(tgt.get("value"))
            if self._node_kind_from_dict(owner) == "Name":
                nm = self.any_to_str(owner.get("id"))
                if nm in params:
                    out.add(nm)
            return
        if tkind == "Tuple":
            elems = self.any_dict_get_list(tgt, "elements")
            for elem in elems:
                self._mark_mutated_param_from_target(elem, params, out)

    def _collect_mutated_params_from_stmt(self, stmt: dict[str, Any], params: set[str], out: set[str]) -> None:
        """1文から「破壊的に使われる引数名」を再帰的に収集する。"""
        kind = self._node_kind_from_dict(stmt)

        if kind in {"Assign", "AnnAssign", "AugAssign"}:
            self._mark_mutated_param_from_target(stmt.get("target"), params, out)
        elif kind == "Swap":
            lhs = self.any_to_dict_or_empty(stmt.get("lhs"))
            rhs = self.any_to_dict_or_empty(stmt.get("rhs"))
            if self._node_kind_from_dict(lhs) == "Name":
                ln = self.any_to_str(lhs.get("id"))
                if ln in params:
                    out.add(ln)
            if self._node_kind_from_dict(rhs) == "Name":
                rn = self.any_to_str(rhs.get("id"))
                if rn in params:
                    out.add(rn)
        elif kind == "Expr":
            call = self.any_to_dict_or_empty(stmt.get("value"))
            if self._node_kind_from_dict(call) == "Call":
                fn = self.any_to_dict_or_empty(call.get("func"))
                if self._node_kind_from_dict(fn) == "Attribute":
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    if self._node_kind_from_dict(owner) == "Name":
                        nm = self.any_to_str(owner.get("id"))
                        attr = self.any_to_str(fn.get("attr"))
                        mutating_attrs = {
                            "append",
                            "extend",
                            "insert",
                            "pop",
                            "clear",
                            "remove",
                            "discard",
                            "add",
                            "update",
                            "setdefault",
                            "sort",
                            "reverse",
                            "mkdir",
                            "write",
                            "write_text",
                            "close",
                        }
                        if nm in params and attr in mutating_attrs:
                            out.add(nm)

        if kind == "If":
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return
        if kind == "While" or kind == "For":
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return
        if kind == "Try":
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for h in self._dict_stmt_list(stmt.get("handlers")):
                for s in self._dict_stmt_list(h.get("body")):
                    self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("finalbody")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return

    def _collect_mutated_params(self, body_stmts: list[dict[str, Any]], arg_names: list[str]) -> set[str]:
        """関数本体から `mutable` 扱いすべき引数名を推定する。"""
        params: set[str] = set()
        for arg_name in arg_names:
            params.add(arg_name)
        out: set[str] = set()
        for st in body_stmts:
            self._collect_mutated_params_from_stmt(st, params, out)
        return out

    def _node_contains_call_name(self, node: Any, fn_name: str) -> bool:
        """ノード配下に `fn_name(...)` 呼び出しが含まれるかを返す。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) > 0:
            if self._node_kind_from_dict(node_dict) == "Call":
                fn = self.any_to_dict_or_empty(dict_any_get(node_dict, "func"))
                if self._node_kind_from_dict(fn) == "Name":
                    if self.any_dict_get_str(fn, "id", "") == fn_name:
                        return True
            for _k, v in node_dict.items():
                if self._node_contains_call_name(v, fn_name):
                    return True
            return False
        node_list = self.any_to_list(node)
        if len(node_list) > 0:
            for item in node_list:
                if self._node_contains_call_name(item, fn_name):
                    return True
        return False

    def _stmt_list_contains_call_name(self, body_stmts: list[dict[str, Any]], fn_name: str) -> bool:
        """文リストに `fn_name(...)` 呼び出しが含まれるかを返す。"""
        for st in body_stmts:
            if self._node_contains_call_name(st, fn_name):
                return True
        return False

    def _allows_none_default(self, east_t: str) -> bool:
        """型が `None` 既定値（optional）を許容するか判定する。"""
        t = self.normalize_type_name(east_t)
        if t == "None":
            return True
        if t.startswith("optional[") and t.endswith("]"):
            return True
        if self._contains_text(t, "|"):
            parts = self.split_union(t)
            for part in parts:
                if part == "None":
                    return True
        return False

    def _none_default_expr_for_type(self, east_t: str) -> str:
        """`None` 既定値を C++ 側の型別既定値へ変換する。"""
        t = self.normalize_type_name(east_t)
        if t in {"", "unknown", "Any", "object"}:
            return "object{}"
        if self._allows_none_default(t):
            return "::std::nullopt"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return "0"
        if t in {"float32", "float64"}:
            return "0.0"
        if t == "bool":
            return "false"
        if t == "str":
            return "str()"
        if t == "bytes":
            return "bytes()"
        if t == "bytearray":
            return "bytearray()"
        if t == "Path":
            return "Path()"
        cpp_t = self._cpp_type_text(t)
        if cpp_t.startswith("::std::optional<"):
            return "::std::nullopt"
        return cpp_t + "{}"

    def _rewrite_nullopt_default_for_typed_target(self, rendered_expr: str, east_target_t: str) -> str:
        """`dict_get_node/py_dict_get_default(..., nullopt)` を型付き既定値へ置換する。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        if t == "" or self.is_any_like_type(t) or self._allows_none_default(t):
            return rendered_expr
        typed_default = self._none_default_expr_for_type(t)
        if typed_default in {"", "::std::nullopt", "std::nullopt"}:
            return rendered_expr
        if not (
            rendered_expr.startswith("dict_get_node(") or rendered_expr.startswith("py_dict_get_default(")
        ):
            return rendered_expr
        tail_a = ", ::std::nullopt)"
        tail_b = ", std::nullopt)"
        if rendered_expr.endswith(tail_a):
            return rendered_expr[: -len(tail_a)] + ", " + typed_default + ")"
        if rendered_expr.endswith(tail_b):
            return rendered_expr[: -len(tail_b)] + ", " + typed_default + ")"
        return rendered_expr

    def _coerce_param_signature_default(self, rendered_expr: str, east_target_t: str) -> str:
        """関数シグネチャ既定値を引数型に合わせて整形する。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        out = self._rewrite_nullopt_default_for_typed_target(rendered_expr, t)
        if not self.is_any_like_type(t):
            return out
        if out in {"object{}", "object()"}:
            return out
        if self.is_boxed_object_expr(out):
            return out
        return f"make_object({out})"

    def _render_param_default_expr(self, node: Any, east_target_t: str) -> str:
        """関数引数既定値ノードを C++ 式へ変換する。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0:
            return ""
        kind = self._node_kind_from_dict(nd)
        if kind == "Constant":
            if "value" not in nd:
                return ""
            val = nd["value"]
            if val is None:
                return self._none_default_expr_for_type(east_target_t)
            if isinstance(val, bool):
                return "true" if val else "false"
            if isinstance(val, int):
                return str(val)
            if isinstance(val, float):
                return str(val)
            if isinstance(val, str):
                return cpp_string_lit(val)
            return ""
        if kind == "Name":
            ident = self.any_to_str(nd.get("id"))
            if ident == "None":
                return self._none_default_expr_for_type(east_target_t)
            if ident == "True":
                return "true"
            if ident == "False":
                return "false"
            return ""
        if kind == "Tuple":
            elems = self.any_dict_get_list(nd, "elements")
            parts: list[str] = []
            for elem in elems:
                txt = self._render_param_default_expr(elem, "Any")
                if txt == "":
                    return ""
                parts.append(txt)
            return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
        _ = east_target_t
        return ""

    def _merge_decl_types_for_branch_join(self, left_t: str, right_t: str) -> str:
        """if/else 合流時の宣言型候補をマージする。"""
        l = self.normalize_type_name(left_t)
        r = self.normalize_type_name(right_t)
        if l in {"", "unknown"}:
            l = ""
        if r in {"", "unknown"}:
            r = ""
        if l == "":
            return r
        if r == "":
            return l
        if l == r:
            return l
        int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_types = {"float32", "float64"}
        if (l in int_types or l in float_types) and (r in int_types or r in float_types):
            if l in float_types or r in float_types:
                return "float64"
            return "int64"
        if self.is_any_like_type(l) or self.is_any_like_type(r):
            return "object"
        return l

    def _predeclare_if_join_names(self, body_stmts: list[dict[str, Any]], else_stmts: list[dict[str, Any]]) -> None:
        """if/else 両分岐で代入される名前を外側スコープへ事前宣言する。"""
        if len(else_stmts) == 0:
            return
        body_types = self._collect_assigned_name_types(body_stmts)
        else_types = self._collect_assigned_name_types(else_stmts)
        for name, _body_ty in body_types.items():
            _ = _body_ty
            if name == "":
                continue
            if name not in else_types:
                continue
            if self.is_declared(name):
                continue
            decl_t = self._merge_decl_types_for_branch_join(body_types[name], else_types[name])
            decl_t = decl_t if decl_t != "" else "object"
            cpp_t = self._cpp_type_text(decl_t)
            fallback_to_object = cpp_t in {"", "auto"}
            decl_t = "object" if fallback_to_object else decl_t
            cpp_t = "object" if fallback_to_object else cpp_t
            self.emit(f"{cpp_t} {name};")
            self.declare_in_current_scope(name)
            self.declared_var_types[name] = decl_t

    def _emit_if_stmt(self, stmt: dict[str, Any]) -> None:
        """If ノードを出力する。"""
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        else_stmts = self._dict_stmt_list(stmt.get("orelse"))
        cond_txt = self.render_cond(stmt.get("test"))
        cond_fix = self._render_repr_expr(cond_txt)
        if cond_fix != "":
            cond_txt = cond_fix
        if cond_txt == "":
            test_node = self.any_to_dict_or_empty(stmt.get("test"))
            cond_repr = self.any_dict_get_str(test_node, "repr", "")
            cond_txt = cond_repr if cond_repr != "" else "false"
        self._predeclare_if_join_names(body_stmts, else_stmts)
        omit_braces = self.hook_on_stmt_omit_braces("If", stmt, False)
        if omit_braces and len(body_stmts) == 1 and len(else_stmts) <= 1:
            self.emit(self.syntax_line("if_no_brace", "if ({cond})", {"cond": cond_txt}))
            self.emit_scoped_stmt_list([body_stmts[0]], set())
            if len(else_stmts) > 0:
                self.emit(self.syntax_text("else_no_brace", "else"))
                self.emit_scoped_stmt_list([else_stmts[0]], set())
            return

        self.emit(self.syntax_line("if_open", "if ({cond}) {", {"cond": cond_txt}))
        self.emit_scoped_stmt_list(body_stmts, set())
        if len(else_stmts) > 0:
            self.emit(self.syntax_text("else_open", "} else {"))
            self.emit_scoped_stmt_list(else_stmts, set())
            self.emit_block_close()
        else:
            self.emit_block_close()

    def _emit_while_stmt(self, stmt: dict[str, Any]) -> None:
        """While ノードを出力する。"""
        cond_txt = self.render_cond(stmt.get("test"))
        cond_fix = self._render_repr_expr(cond_txt)
        if cond_fix != "":
            cond_txt = cond_fix
        if cond_txt == "":
            test_node = self.any_to_dict_or_empty(stmt.get("test"))
            cond_repr = self.any_dict_get_str(test_node, "repr", "")
            cond_txt = cond_repr if cond_repr != "" else "false"
        self.emit_scoped_block(
            self.syntax_line("while_open", "while ({cond}) {", {"cond": cond_txt}),
            self._dict_stmt_list(stmt.get("body")),
            set(),
        )

    def _render_lvalue_for_augassign(self, target_expr: Any) -> str:
        """AugAssign 向けに左辺を簡易レンダリングする。"""
        target_node = self.any_to_dict_or_empty(target_expr)
        if self._node_kind_from_dict(target_node) == "Name":
            return self.any_dict_get_str(target_node, "id", "_")
        return self.render_lvalue(target_expr)

    def _emit_annassign_stmt(self, stmt: dict[str, Any]) -> None:
        """AnnAssign ノードを出力する。"""
        t = self.cpp_type(stmt.get("annotation"))
        decl_hint = self.any_dict_get_str(stmt, "decl_type", "")
        decl_hint_fallback = str(stmt.get("decl_type"))
        ann_text_fallback = str(stmt.get("annotation"))
        if decl_hint == "" and decl_hint_fallback not in {"", "{}", "None"}:
            decl_hint = decl_hint_fallback
        if decl_hint != "":
            t = self._cpp_type_text(decl_hint)
        elif t == "auto":
            t = self.cpp_type(stmt.get("decl_type"))
            if t == "auto" and ann_text_fallback not in {"", "{}", "None"}:
                t = self._cpp_type_text(self.normalize_type_name(ann_text_fallback))
        target = self.render_expr(stmt.get("target"))
        val = self.any_to_dict_or_empty(stmt.get("value"))
        val_is_dict: bool = len(val) > 0
        rendered_val: str = ""
        if val_is_dict:
            rendered_val = self.render_expr(stmt.get("value"))
        ann_t_str = self.any_dict_get_str(stmt, "annotation", "")
        ann_fallback = ann_text_fallback if ann_text_fallback not in {"", "{}", "None"} else ""
        ann_t_str = ann_t_str if ann_t_str != "" else (decl_hint if decl_hint != "" else ann_fallback)
        if rendered_val != "" and ann_t_str != "":
            rendered_val = self._rewrite_nullopt_default_for_typed_target(rendered_val, ann_t_str)
        if ann_t_str in {"byte", "uint8"} and val_is_dict:
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rendered_val = str(byte_val)
        val_kind = self.any_dict_get_str(val, "kind", "")
        if val_is_dict and val_kind == "Dict" and ann_t_str.startswith("dict[") and ann_t_str.endswith("]"):
            inner_ann = self.split_generic(ann_t_str[5:-1])
            if len(inner_ann) == 2 and self.is_any_like_type(inner_ann[1]):
                items: list[str] = []
                for kv in self._dict_stmt_list(val.get("entries")):
                    k = self.render_expr(kv.get("key"))
                    v = self.render_expr_as_any(kv.get("value"))
                    items.append(f"{{{k}, {v}}}")
                rendered_val = f"{t}{{{join_str_list(', ', items)}}}"
        if val_is_dict and t != "auto":
            vkind = val_kind
            if vkind == "BoolOp":
                if ann_t_str != "bool":
                    rendered_val = self.render_boolop(stmt.get("value"), True)
            if vkind == "List" and len(self._dict_stmt_list(val.get("elements"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "Dict" and len(self._dict_stmt_list(val.get("entries"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "Set" and len(self._dict_stmt_list(val.get("elements"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "ListComp" and isinstance(rendered_val, str):
                if self._contains_text(rendered_val, "[&]() -> list<object> {"):
                    rendered_val = rendered_val.replace("[&]() -> list<object> {", f"[&]() -> {t} {{")
                    rendered_val = rendered_val.replace("list<object> __out;", f"{t} __out;")
        val_t0 = self.get_expr_type(stmt.get("value"))
        val_t = val_t0 if isinstance(val_t0, str) else ""
        if rendered_val != "" and ann_t_str != "" and self._contains_text(val_t, "|"):
            union_parts = self.split_union(val_t)
            has_none = False
            non_none_norm: list[str] = []
            for p in union_parts:
                pn = self.normalize_type_name(p)
                if pn == "None":
                    has_none = True
                    continue
                if pn != "":
                    non_none_norm.append(pn)
            ann_norm = self.normalize_type_name(ann_t_str)
            if has_none and len(non_none_norm) == 1 and non_none_norm[0] == ann_norm:
                rendered_val = f"({rendered_val}).value()"
        if self._can_runtime_cast_target(ann_t_str) and self.is_any_like_type(val_t) and rendered_val != "":
            rendered_val = self._coerce_any_expr_to_target(rendered_val, ann_t_str, f"annassign:{target}")
        if self.is_any_like_type(ann_t_str) and val_is_dict:
            rendered_val = self._box_any_target_value(rendered_val, stmt.get("value"))
        declare = self.any_dict_get_int(stmt, "declare", 1) != 0
        already_declared = self.is_declared(target) if self.is_plain_name_expr(stmt.get("target")) else False
        if target.startswith("this->"):
            if not val_is_dict:
                self.emit(f"{target};")
            else:
                self.emit(f"{target} = {rendered_val};")
            return
        if not val_is_dict:
            if declare and self.is_plain_name_expr(stmt.get("target")) and not already_declared:
                self.declare_in_current_scope(target)
            if declare and not already_declared:
                self.emit(f"{t} {target};")
            return
        if declare and self.is_plain_name_expr(stmt.get("target")) and not already_declared:
            self.declare_in_current_scope(target)
            picked_decl_t = ann_t_str if ann_t_str != "" else decl_hint
            picked_decl_t = (
                picked_decl_t if picked_decl_t != "" else (val_t if val_t != "" else self.get_expr_type(stmt.get("target")))
            )
            self.declared_var_types[target] = self.normalize_type_name(picked_decl_t)
        if declare and not already_declared:
            self.emit(f"{t} {target} = {rendered_val};")
        else:
            self.emit(f"{target} = {rendered_val};")

    def _emit_augassign_stmt(self, stmt: dict[str, Any]) -> None:
        """AugAssign ノードを出力する。"""
        op = "+="
        target_expr_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self._render_lvalue_for_augassign(stmt.get("target"))
        declare = self.any_dict_get_int(stmt, "declare", 0) != 0
        if declare and self._node_kind_from_dict(target_expr_node) == "Name" and target not in self.current_scope():
            decl_t_raw = stmt.get("decl_type")
            decl_t = str(decl_t_raw) if isinstance(decl_t_raw, str) else ""
            inferred_t = self.get_expr_type(stmt.get("target"))
            picked_t = decl_t if decl_t != "" else inferred_t
            t = self._cpp_type_text(picked_t)
            self.declare_in_current_scope(target)
            self.emit(f"{t} {target} = {self.render_expr(stmt.get('value'))};")
            return
        val = self.render_expr(stmt.get("value"))
        target_t = self.get_expr_type(stmt.get("target"))
        value_t = self.get_expr_type(stmt.get("value"))
        if self.is_any_like_type(value_t):
            if target_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                val = f"py_to_int64({val})"
            elif target_t in {"float32", "float64"}:
                val = f"static_cast<float64>(py_to_int64({val}))"
        op_name = str(stmt.get("op"))
        op_txt = str(AUG_OPS.get(op_name, ""))
        if op_txt != "":
            op = op_txt
        if str(AUG_BIN.get(op_name, "")) != "":
            # Prefer idiomatic ++/-- for +/-1 updates.
            if self._opt_ge(2) and op_name in {"Add", "Sub"} and val == "1":
                if op_name == "Add":
                    self.emit(f"{target}++;")
                else:
                    self.emit(f"{target}--;")
                return
            if op_name == "FloorDiv":
                if self.floor_div_mode == "python":
                    self.emit(f"{target} = py_floordiv({target}, {val});")
                else:
                    self.emit(f"{target} /= {val};")
            elif op_name == "Mod":
                if self.mod_mode == "python":
                    self.emit(f"{target} = py_mod({target}, {val});")
                else:
                    self.emit(f"{target} {op} {val};")
            else:
                self.emit(f"{target} {op} {val};")
            return
        self.emit(f"{target} {op} {val};")

    def _emit_stmt_kind_fallback(self, kind: str, stmt: dict[str, Any]) -> bool:
        """`on_emit_stmt_kind` 未処理時の C++ 既定ディスパッチ。"""
        handlers: dict[str, Any] = {
            "Expr": self._emit_expr_stmt,
            "Return": self._emit_return_stmt,
            "Assign": self._emit_assign_stmt,
            "Swap": self._emit_swap_stmt,
            "AnnAssign": self._emit_annassign_stmt,
            "AugAssign": self._emit_augassign_stmt,
            "If": self._emit_if_stmt,
            "While": self._emit_while_stmt,
            "ForRange": self.emit_for_range,
            "For": self.emit_for_each,
            "ForCore": self.emit_for_core,
            "Raise": self._emit_raise_stmt,
            "Try": self._emit_try_stmt,
            "FunctionDef": self._emit_function_stmt,
            "ClassDef": self._emit_class_stmt,
            "Pass": self._emit_pass_stmt,
            "Break": self._emit_break_stmt,
            "Continue": self._emit_continue_stmt,
            "Yield": self._emit_yield_stmt,
            "Import": self._emit_noop_stmt,
            "ImportFrom": self._emit_noop_stmt,
        }
        handler = handlers.get(kind)
        if handler is None:
            return False
        self.emit_leading_comments(stmt)
        handler(stmt)
        return True

    def hook_on_emit_stmt_kind(
        self,
        kind: str,
        stmt: dict[str, Any],
    ) -> bool | None:
        """dynamic hook 優先 + C++ 既定フォールバックで kind 処理を解決する。"""
        handled_by_hook = super().hook_on_emit_stmt_kind(kind, stmt)
        if isinstance(handled_by_hook, bool) and handled_by_hook:
            return True
        if self._emit_stmt_kind_fallback(kind, stmt):
            return True
        return handled_by_hook

    def hook_on_render_expr_kind(
        self,
        kind: str,
        expr_node: dict[str, Any],
    ) -> str:
        """dynamic hook 優先で式 kind 処理を解決し、未処理は fallback へ渡す。"""
        rendered_specific = self.hook_on_render_expr_kind_specific(kind, expr_node)
        if rendered_specific != "":
            return rendered_specific
        rendered_kind = super().hook_on_render_expr_kind(kind, expr_node)
        if rendered_kind != "":
            return rendered_kind
        if kind in {"JoinedStr", "Lambda", "ListComp", "SetComp", "DictComp"}:
            rendered_complex = self.hook_on_render_expr_complex(expr_node)
            if rendered_complex != "":
                return rendered_complex
        if kind in {"Name", "Constant", "Attribute"}:
            rendered_leaf = self.hook_on_render_expr_leaf(kind, expr_node)
            if rendered_leaf != "":
                return rendered_leaf
        return ""

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """1つの文ノードを C++ 文へ変換して出力する。"""
        hook_stmt = self.hook_on_emit_stmt(stmt)
        if hook_stmt:
            return
        kind = self._node_kind_from_dict(stmt)
        if self.hook_on_emit_stmt_kind(kind, stmt):
            return
        self.emit_leading_comments(stmt)
        self.emit(f"/* unsupported stmt kind: {kind} */")

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        """CppEmitter 側で文ディスパッチを固定し、selfhost時の静的束縛を避ける。"""
        for stmt in stmts:
            self.emit_stmt(stmt)

    def emit_scoped_stmt_list(self, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """selfhost C++ で base 実装へ静的束縛されるのを避ける。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        for stmt in stmts:
            self.emit_stmt(stmt)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """selfhost C++ 向けに scoped block も CppEmitter 側で固定する。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def _emit_noop_stmt(self, stmt: dict[str, Any]) -> None:
        kind = self._node_kind_from_dict(stmt)
        ents = self._dict_stmt_list(stmt.get("names"))
        if kind == "Import":
            for ent in ents:
                name = dict_any_get_str(ent, "name")
                asname = dict_any_get_str(ent, "asname")
                local_name = asname if asname else self._last_dotted_name(name)
                set_import_module_binding(self.import_modules, local_name, name)
            return
        if kind == "ImportFrom":
            mod = dict_any_get_str(stmt, "module")
            for ent in ents:
                name = dict_any_get_str(ent, "name")
                asname = dict_any_get_str(ent, "asname")
                local_name = asname if asname else name
                set_import_symbol_binding_and_module_set(
                    self.import_symbols, self.import_symbol_modules, local_name, mod, name
                )
        return

    def _emit_pass_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("pass_stmt", "/* pass */"))

    def _emit_break_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("break_stmt", "break;"))

    def _emit_continue_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("continue_stmt", "continue;"))

    def _emit_swap_stmt(self, stmt: dict[str, Any]) -> None:
        left = self.render_expr(stmt.get("left"))
        right = self.render_expr(stmt.get("right"))
        self.emit(
            self.syntax_line(
                "swap_stmt",
                "::std::swap({left}, {right});",
                {"left": left, "right": right},
            )
        )

    def _emit_raise_stmt(self, stmt: dict[str, Any]) -> None:
        if not isinstance(stmt.get("exc"), dict):
            self.emit(self.syntax_text("raise_default", 'throw ::std::runtime_error("raise");'))
        else:
            self.emit(
                self.syntax_line(
                    "raise_expr",
                    "throw {exc};",
                    {"exc": self.render_expr(stmt.get("exc"))},
                )
            )

    def _emit_local_function_stmt(self, stmt: dict[str, Any]) -> None:
        """ローカル関数定義をラムダ変数へ lowering して出力する。"""
        name = self.any_dict_get_str(stmt, "name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        ret = self.cpp_type(stmt.get("return_type"))
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_defaults = self.any_to_dict_or_empty(stmt.get("arg_defaults"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        params: list[str] = []
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "" and raw_n in arg_types:
                arg_names.append(str(raw_n))
        arg_type_ordered: list[str] = []
        for n in arg_names:
            t = self.normalize_type_name(self.any_to_str(arg_types.get(n)))
            t = t if t != "" else "unknown"
            arg_type_ordered.append(t)
        mutated_params = self._collect_mutated_params(body_stmts, arg_names)
        is_recursive_local_fn = self._stmt_list_contains_call_name(body_stmts, emitted_name)
        # ローカル関数呼び出しの coercion に使うため、現在スコープ中は登録を維持する。
        self.function_arg_types[emitted_name] = arg_type_ordered
        self.function_return_types[emitted_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
        fn_scope: set[str] = set()
        fn_sig_params: list[str] = []
        for n in arg_names:
            t = self.any_to_str(arg_types.get(n))
            ct = self._cpp_type_text(t)
            usage = self.any_to_str(arg_usage.get(n))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and n in mutated_params:
                usage = "mutable"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            param_txt = ""
            if by_ref and usage == "mutable":
                use_object_param = ct == "object"
                param_txt = f"{ct} {n}" if use_object_param else f"{ct}& {n}"
                fn_sig_params.append(ct if use_object_param else f"{ct}&")
            elif by_ref:
                param_txt = f"const {ct}& {n}"
                fn_sig_params.append(f"const {ct}&")
            else:
                param_txt = f"{ct} {n}"
                fn_sig_params.append(ct)
            if n in arg_defaults:
                default_txt = self._render_param_default_expr(arg_defaults.get(n), t)
                if default_txt != "":
                    default_txt = self._coerce_param_signature_default(default_txt, t)
                    param_txt += f" = {default_txt}"
            params.append(param_txt)
            fn_scope.add(n)
        params_txt = ", ".join(params)
        if is_recursive_local_fn:
            fn_sig = ", ".join(fn_sig_params)
            self.emit(f"::std::function<{ret}({fn_sig})> {emitted_name};")
            self.emit(f"{emitted_name} = [&]({params_txt}) -> {ret} {{")
        else:
            self.emit(f"auto {emitted_name} = [&]({params_txt}) -> {ret} {{")
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        prev_ret = self.current_function_return_type
        prev_decl_types = self.declared_var_types
        self.declared_var_types = {}
        for an in arg_names:
            at = self.any_to_str(arg_types.get(an))
            if at != "":
                self.declared_var_types[an] = self.normalize_type_name(at)
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        docstring = self.any_to_str(stmt.get("docstring"))
        if docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(body_stmts)
        self.current_function_return_type = prev_ret
        self.declared_var_types = prev_decl_types
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("};")

    def _emit_function_stmt(self, stmt: dict[str, Any]) -> None:
        # class body 直下の FunctionDef は class method として扱う。
        # 関数本体（scope_stack>1）での nested def は local lambda へ落とす。
        if self.current_class_name is not None and len(self.scope_stack) == 1:
            self.emit_function(stmt, True)
            return
        if len(self.scope_stack) > 1:
            self._emit_local_function_stmt(stmt)
            return
        self.emit_function(stmt, False)

    def _emit_class_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_class(stmt)

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        value_is_dict: bool = len(value_node) > 0
        if value_is_dict and self._node_kind_from_dict(value_node) == "Constant" and isinstance(value_node.get("value"), str):
            self.emit_block_comment(str(value_node.get("value")))
            return
        if value_is_dict and self._is_redundant_super_init_call(stmt.get("value")):
            self.emit("/* super().__init__ omitted: base ctor is called implicitly */")
            return
        if not value_is_dict:
            self.emit("/* unsupported expr */")
            return
        self.emit_bridge_comment(value_node)
        rendered = self.render_expr(stmt.get("value"))
        # Guard against stray identifier-only expression statements (e.g. "r;").
        if isinstance(rendered, str) and self._is_identifier_expr(rendered):
            if rendered == "break" or rendered == "py_break":
                self.emit("break;")
            elif rendered == "continue" or rendered == "py_continue":
                self.emit("continue;")
            elif rendered == "pass":
                self.emit("/* pass */")
            else:
                self.emit(f"/* omitted bare identifier expression: {rendered} */")
            return
        self.emit(
            self.syntax_line(
                "expr_stmt",
                "{expr};",
                {"expr": rendered},
            )
        )

    def _emit_return_stmt(self, stmt: dict[str, Any]) -> None:
        if self.current_function_is_generator:
            buf = self.current_function_yield_buffer
            if buf == "":
                self.emit("/* invalid generator return */")
                return
            self.emit(f"return {buf};")
            return
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        v_is_dict: bool = len(value_node) > 0
        if not v_is_dict:
            self.emit(self.syntax_text("return_void", "return;"))
            return
        rv = self.render_expr(stmt.get("value"))
        ret_t = self.current_function_return_type
        if ret_t != "":
            rv = self._rewrite_nullopt_default_for_typed_target(rv, ret_t)
        expr_t0 = self.get_expr_type(stmt.get("value"))
        expr_t = expr_t0 if isinstance(expr_t0, str) else ""
        if self.is_any_like_type(ret_t) and (not self.is_any_like_type(expr_t)):
            rv = self.render_expr_as_any(stmt.get("value"))
        if self._can_runtime_cast_target(ret_t) and self.is_any_like_type(expr_t):
            rv = self._coerce_any_expr_to_target(rv, ret_t, f"return:{ret_t}")
        self.emit(
            self.syntax_line(
                "return_value",
                "return {value};",
                {"value": rv},
            )
        )

    def _emit_yield_stmt(self, stmt: dict[str, Any]) -> None:
        if not self.current_function_is_generator or self.current_function_yield_buffer == "":
            self.emit("/* unsupported yield outside generator */")
            return
        buf = self.current_function_yield_buffer
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        if len(value_node) == 0:
            yty = self.current_function_yield_type
            default_expr = "object()"
            if yty in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                default_expr = "0"
            elif yty in {"float32", "float64"}:
                default_expr = "0.0"
            elif yty == "bool":
                default_expr = "false"
            elif yty == "str":
                default_expr = "str()"
            self.emit(f"{buf}.append({default_expr});")
            return
        yv = self.render_expr(stmt.get("value"))
        yv_t = self.get_expr_type(stmt.get("value"))
        if self.current_function_yield_type not in {"", "unknown", "Any", "object"} and self.is_any_like_type(yv_t):
            yv = self._coerce_any_expr_to_target(yv, self.current_function_yield_type, f"yield:{self.current_function_yield_type}")
        self.emit(f"{buf}.append({yv});")

    def _emit_assign_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_assign(stmt)

    def _emit_try_stmt(self, stmt: dict[str, Any]) -> None:
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        has_effective_finally = False
        for s in finalbody:
            if isinstance(s, dict) and self._node_kind_from_dict(s) != "Pass":
                has_effective_finally = True
                break
        if has_effective_finally:
            self.emit(self.syntax_text("scope_open", "{"))
            self.indent += 1
            gid = self.next_tmp("__finally")
            self.emit(
                self.syntax_line(
                    "scope_exit_open",
                    "auto {guard} = py_make_scope_exit([&]() {",
                    {"guard": gid},
                )
            )
            self.indent += 1
            self.emit_stmt_list(finalbody)
            self.indent -= 1
            self.emit(self.syntax_text("scope_exit_close", "});"))
        if len(handlers) == 0:
            self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
            if has_effective_finally:
                self.indent -= 1
                self.emit_block_close()
            return
        self.emit(self.syntax_text("try_open", "try {"))
        self.indent += 1
        self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
        self.indent -= 1
        self.emit_block_close()
        for h in handlers:
            name_raw = h.get("name")
            name = "ex"
            if isinstance(name_raw, str) and name_raw != "":
                name = name_raw
            self.emit(
                self.syntax_line(
                    "catch_open",
                    "catch (const ::std::exception& {name}) {",
                    {"name": name},
                )
            )
            self.indent += 1
            self.emit_stmt_list(self._dict_stmt_list(h.get("body")))
            self.indent -= 1
            self.emit_block_close()
        if has_effective_finally:
            self.indent -= 1
            self.emit_block_close()

    def emit_assign(self, stmt: dict[str, Any]) -> None:
        """代入文（通常代入/タプル代入）を C++ へ出力する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        value = self.any_to_dict_or_empty(stmt.get("value"))
        if len(target) == 0 or len(value) == 0:
            self.emit("/* invalid assign */")
            return
        # `X = imported.Y` / `X = imported` の純再エクスポートは
        # C++ 側では宣言変数に落とすと未使用・型退化の温床になるため省略する。
        if self._is_reexport_assign(target, value):
            return
        if self._node_kind_from_dict(target) == "Tuple":
            lhs_elems = self.any_dict_get_list(target, "elements")
            if len(lhs_elems) == 0:
                fallback_names = self._fallback_tuple_target_names_from_repr(target)
                if len(fallback_names) == 0:
                    stmt_repr = self.any_dict_get_str(stmt, "repr", "")
                    if stmt_repr != "":
                        eq_pos = stmt_repr.find("=")
                        lhs_txt = stmt_repr
                        if eq_pos >= 0:
                            lhs_txt = stmt_repr[:eq_pos]
                        pseudo_target: dict[str, Any] = {"repr": lhs_txt}
                        fallback_names = self._fallback_tuple_target_names_from_repr(pseudo_target)
                if len(fallback_names) > 0:
                    recovered: list[Any] = []
                    for nm in fallback_names:
                        rec: dict[str, Any] = {
                            "kind": "Name",
                            "id": nm,
                            "resolved_type": "unknown",
                            "repr": nm,
                        }
                        rec_any: Any = rec
                        recovered.append(rec_any)
                    lhs_elems = recovered
            if self._opt_ge(2) and isinstance(value, dict) and self._node_kind_from_dict(value) == "Tuple":
                rhs_elems = self.any_dict_get_list(value, "elements")
                if (
                    len(lhs_elems) == 2
                    and len(rhs_elems) == 2
                    and self._expr_repr_eq(lhs_elems[0], rhs_elems[1])
                    and self._expr_repr_eq(lhs_elems[1], rhs_elems[0])
                ):
                    self.emit(f"::std::swap({self.render_lvalue(lhs_elems[0])}, {self.render_lvalue(lhs_elems[1])});")
                    return
            tmp = self.next_tmp("__tuple")
            value_expr = self.render_expr(stmt.get("value"))
            tuple_elem_types: list[str] = []
            value_t = self.get_expr_type(stmt.get("value"))
            value_is_optional_tuple = False
            rhs_is_tuple = False
            if isinstance(value_t, str):
                tuple_type_text = ""
                if value_t.startswith("tuple[") and value_t.endswith("]"):
                    tuple_type_text = value_t
                elif self._contains_text(value_t, "|"):
                    for part in self.split_union(value_t):
                        if part.startswith("tuple[") and part.endswith("]"):
                            tuple_type_text = part
                            break
                if tuple_type_text != "":
                    rhs_is_tuple = True
                    tuple_elem_types = self.split_generic(tuple_type_text[6:-1])
                    if tuple_type_text != value_t:
                        value_is_optional_tuple = True
            if not rhs_is_tuple:
                value_node = self.any_to_dict_or_empty(stmt.get("value"))
                if self._node_kind_from_dict(value_node) == "Call":
                    fn_node = self.any_to_dict_or_empty(value_node.get("func"))
                    fn_name = ""
                    if self._node_kind_from_dict(fn_node) == "Name":
                        fn_name = self.any_to_str(fn_node.get("id"))
                    if fn_name != "":
                        fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                        ret_t = self.function_return_types.get(fn_name, "")
                        if ret_t.startswith("tuple[") and ret_t.endswith("]"):
                            rhs_is_tuple = True
                            tuple_elem_types = self.split_generic(ret_t[6:-1])
            if value_is_optional_tuple:
                self.emit(f"auto {tmp} = *({value_expr});")
            else:
                self.emit(f"auto {tmp} = {value_expr};")
            for i, elt in enumerate(lhs_elems):
                lhs = self.render_expr(elt)
                rhs_item = f"::std::get<{i}>({tmp})" if rhs_is_tuple else f"py_at({tmp}, {i})"
                if self.is_plain_name_expr(elt):
                    elt_dict = self.any_to_dict_or_empty(elt)
                    name = self.any_dict_get_str(elt_dict, "id", "")
                    if not self.is_declared(name):
                        decl_t_txt = tuple_elem_types[i] if i < len(tuple_elem_types) else self.get_expr_type(elt)
                        self.declare_in_current_scope(name)
                        self.declared_var_types[name] = decl_t_txt
                        if decl_t_txt in {"", "unknown", "Any", "object"}:
                            self.emit(f"auto {lhs} = {rhs_item};")
                            continue
                        decl_t = self._cpp_type_text(decl_t_txt)
                        self.emit(f"{decl_t} {lhs} = {rhs_item};")
                        continue
                self.emit(f"{lhs} = {rhs_item};")
            return
        texpr = self.render_lvalue(stmt.get("target"))
        if self.is_plain_name_expr(stmt.get("target")) and not self.is_declared(texpr):
            d0 = self.normalize_type_name(self.any_dict_get_str(stmt, "decl_type", ""))
            d1 = self.normalize_type_name(self.get_expr_type(stmt.get("target")))
            d2 = self.normalize_type_name(self.get_expr_type(stmt.get("value")))
            if d0 == "unknown":
                d0 = ""
            if d1 == "unknown":
                d1 = ""
            if d2 == "unknown":
                d2 = ""
            picked = d0 if d0 != "" else (d1 if d1 != "" else d2)
            if picked == "None":
                picked = "Any"
            if picked in {"", "unknown", "Any", "object"} and isinstance(value, dict) and self._node_kind_from_dict(value) == "BinOp":
                lt0 = self.get_expr_type(value.get("left"))
                rt0 = self.get_expr_type(value.get("right"))
                lt = lt0 if isinstance(lt0, str) else ""
                rt = rt0 if isinstance(rt0, str) else ""
                left_node = self.any_to_dict_or_empty(value.get("left"))
                right_node = self.any_to_dict_or_empty(value.get("right"))
                if (lt == "" or lt == "unknown") and self._node_kind_from_dict(left_node) == "Name":
                    ln = self.any_to_str(left_node.get("id"))
                    if ln in self.declared_var_types:
                        lt = self.declared_var_types[ln]
                if (rt == "" or rt == "unknown") and self._node_kind_from_dict(right_node) == "Name":
                    rn = self.any_to_str(right_node.get("id"))
                    if rn in self.declared_var_types:
                        rt = self.declared_var_types[rn]
                int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
                float_types = {"float32", "float64"}
                if lt in float_types or rt in float_types:
                    picked = "float64"
                elif lt in int_types and rt in int_types:
                    picked = "int64"
            dtype = self._cpp_type_text(picked)
            self.declare_in_current_scope(texpr)
            self.declared_var_types[texpr] = picked
            rval = self.render_expr(stmt.get("value"))
            rval = self._rewrite_nullopt_default_for_typed_target(rval, picked)
            if dtype.startswith("list<") and self._contains_text(rval, "[&]() -> list<object> {"):
                rval = rval.replace("[&]() -> list<object> {", f"[&]() -> {dtype} {{")
                rval = rval.replace("list<object> __out;", f"{dtype} __out;")
            if dtype == "uint8" and isinstance(value, dict):
                byte_val = self._byte_from_str_expr(stmt.get("value"))
                if byte_val != "":
                    rval = str(byte_val)
            if isinstance(value, dict) and self._node_kind_from_dict(value) == "BoolOp" and picked != "bool":
                rval = self.render_boolop(stmt.get("value"), True)
            rval_t0 = self.get_expr_type(stmt.get("value"))
            rval_t = rval_t0 if isinstance(rval_t0, str) else ""
            if self._can_runtime_cast_target(picked) and self.is_any_like_type(rval_t):
                rval = self._coerce_any_expr_to_target(rval, picked, f"assign:{texpr}")
            if self.is_any_like_type(picked):
                rval = self._box_any_target_value(rval, stmt.get("value"))
            self.emit(f"{dtype} {texpr} = {rval};")
            return
        rval = self.render_expr(stmt.get("value"))
        t_target = self.get_expr_type(stmt.get("target"))
        if t_target == "None":
            t_target = "Any"
        if self.is_plain_name_expr(stmt.get("target")) and t_target in {"", "unknown"}:
            if texpr in self.declared_var_types:
                t_target = self.declared_var_types[texpr]
        if t_target != "":
            rval = self._rewrite_nullopt_default_for_typed_target(rval, t_target)
        if t_target == "uint8" and isinstance(value, dict):
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rval = str(byte_val)
        if isinstance(value, dict) and self._node_kind_from_dict(value) == "BoolOp" and t_target != "bool":
            rval = self.render_boolop(stmt.get("value"), True)
        rval_t0 = self.get_expr_type(stmt.get("value"))
        rval_t = rval_t0 if isinstance(rval_t0, str) else ""
        if self._can_runtime_cast_target(t_target) and self.is_any_like_type(rval_t):
            rval = self._coerce_any_expr_to_target(rval, t_target, f"assign:{texpr}")
        if self.is_any_like_type(t_target):
            rval = self._box_any_target_value(rval, stmt.get("value"))
        self.emit(f"{texpr} = {rval};")

    def _is_reexport_assign(self, target: dict[str, Any], value: dict[str, Any]) -> bool:
        """`Name = imported_symbol` 形式の再エクスポート代入かを返す。"""
        if len(self.scope_stack) != 1:
            return False
        if self._node_kind_from_dict(target) != "Name":
            return False
        kind = self._node_kind_from_dict(value)
        if kind == "Name":
            name = dict_any_get_str(value, "id")
            if name in self.import_modules:
                return True
            if name in self.import_symbols:
                return True
            return False
        if kind == "Attribute":
            owner = dict_any_get_dict(value, "value")
            if self._node_kind_from_dict(owner) != "Name":
                return False
            owner_name = dict_any_get_str(owner, "id")
            if owner_name in self.import_modules:
                return True
            if owner_name in self.import_symbols:
                return True
        return False

    def _fallback_tuple_target_names_from_repr(self, target: dict[str, Any]) -> list[str]:
        """selfhost で tuple target 要素が欠落したとき、repr から簡易復元する。"""
        out: list[str] = []
        repr_txt = self.any_dict_get_str(target, "repr", "")
        if repr_txt == "" or "," not in repr_txt:
            return out
        parts: list[str] = []
        cur = ""
        for ch in repr_txt:
            if ch == ",":
                parts.append(cur.strip())
                cur = ""
            else:
                cur += ch
        parts.append(cur.strip())
        for nm in parts:
            if nm != "":
                ok = True
                for k, c in enumerate(nm):
                    if k == 0:
                        if not (c == "_" or c.isalpha()):
                            ok = False
                            break
                    else:
                        if not (c == "_" or c.isalnum()):
                            ok = False
                            break
                if ok:
                    out.append(nm)
        return out

    def render_lvalue(self, expr: Any) -> str:
        """左辺値文脈の式（添字代入含む）を C++ 文字列へ変換する。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return self.render_expr(expr)
        if self._node_kind_from_dict(node) != "Subscript":
            return self.render_expr(expr)
        val = self.render_expr(node.get("value"))
        val_ty0 = self.get_expr_type(node.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        idx = self.render_expr(node.get("slice"))
        idx_t0 = self.get_expr_type(node.get("slice"))
        idx_t = idx_t0 if isinstance(idx_t0, str) else ""
        if val_ty.startswith("dict["):
            idx = self._coerce_dict_key_expr(node.get("value"), idx, node.get("slice"))
            return f"{val}[{idx}]"
        if self.is_indexable_sequence_type(val_ty):
            if self.is_any_like_type(idx_t):
                idx = f"py_to_int64({idx})"
            return self._render_sequence_index(val, idx, node.get("slice"))
        return f"{val}[{idx}]"

    def _render_sequence_index(self, value_expr: str, index_expr: str, index_node: Any) -> str:
        """list/str 添字アクセスのモード別コード生成を行う。"""
        if self.negative_index_mode == "always":
            return f"py_at({value_expr}, {index_expr})"
        if self.negative_index_mode == "const_only" and self._is_negative_const_index(index_node):
            return f"py_at({value_expr}, {index_expr})"
        if self.bounds_check_mode == "always":
            return f"py_at_bounds({value_expr}, {index_expr})"
        if self.bounds_check_mode == "debug":
            return f"py_at_bounds_debug({value_expr}, {index_expr})"
        return f"{value_expr}[{index_expr}]"

    def _coerce_dict_key_expr(self, owner_node: Any, key_expr: str, key_node: Any) -> str:
        """`dict[K, V]` 参照用の key 式を K に合わせて整形する。"""
        owner_t0 = self.get_expr_type(owner_node)
        owner_t = owner_t0 if isinstance(owner_t0, str) else ""
        if self.is_any_like_type(owner_t):
            return key_expr
        if not owner_t.startswith("dict[") or not owner_t.endswith("]"):
            return key_expr
        inner = self.split_generic(owner_t[5:-1])
        if len(inner) != 2:
            return key_expr
        key_t = self.normalize_type_name(inner[0])
        if key_t in {"", "unknown"}:
            return key_expr
        if self.is_any_like_type(key_t):
            if self.is_boxed_object_expr(key_expr):
                return key_expr
            key_node_d = self.any_to_dict_or_empty(key_node)
            if len(key_node_d) > 0:
                return self.render_expr(self._build_box_expr_node(key_node))
            return f"make_object({key_expr})"
        return self.apply_cast(key_expr, key_t)

    def _target_bound_names(self, target: dict[str, Any]) -> set[str]:
        """for ターゲットが束縛する識別子名を収集する。"""
        names: set[str] = set()
        if not isinstance(target, dict) or len(target) == 0:
            return names
        if self._node_kind_from_dict(target) == "Name":
            names.add(self.any_dict_get_str(target, "id", "_"))
            return names
        if self._node_kind_from_dict(target) == "Tuple":
            for e_dict in self._dict_stmt_list(target.get("elements")):
                if self._node_kind_from_dict(e_dict) == "Name":
                    names.add(self.any_dict_get_str(e_dict, "id", "_"))
        return names

    def _emit_target_unpack(self, target: dict[str, Any], src: str, iter_expr: dict[str, Any]) -> None:
        """タプルターゲットへのアンパック代入を出力する。"""
        if not isinstance(target, dict) or len(target) == 0:
            return
        if self._node_kind_from_dict(target) != "Tuple":
            return
        elem_types: list[str] = []
        iter_node: dict[str, Any] = iter_expr
        if len(iter_node) > 0:
            iter_kind: str = self._node_kind_from_dict(iter_node)
            iter_t: str = self.any_dict_get_str(iter_node, "resolved_type", "")
            if iter_t.startswith("list[") and iter_t.endswith("]"):
                inner_txt: str = iter_t[5:-1]
                if inner_txt.startswith("tuple[") and inner_txt.endswith("]"):
                    elem_types = self.split_generic(inner_txt[6:-1])
            elif iter_t.startswith("set[") and iter_t.endswith("]"):
                inner_txt = iter_t[4:-1]
                if inner_txt.startswith("tuple[") and inner_txt.endswith("]"):
                    elem_types = self.split_generic(inner_txt[6:-1])
            elif iter_kind == "Call":
                runtime_call: str = self.any_dict_get_str(iter_node, "runtime_call", "")
                if runtime_call == "dict.items":
                    fn_node = self.any_to_dict_or_empty(iter_node.get("func"))
                    owner_obj = fn_node.get("value")
                    owner_t: str = self.get_expr_type(owner_obj)
                    if owner_t.startswith("dict[") and owner_t.endswith("]"):
                        dict_inner_parts: list[str] = self.split_generic(owner_t[5:-1])
                        if len(dict_inner_parts) == 2:
                            elem_types = [self.normalize_type_name(dict_inner_parts[0]), self.normalize_type_name(dict_inner_parts[1])]
        for i, e in enumerate(self.any_dict_get_list(target, "elements")):
            if isinstance(e, dict) and self._node_kind_from_dict(e) == "Name":
                nm = self.render_expr(e)
                elem_decl_t = self.normalize_type_name(elem_types[i]) if i < len(elem_types) else ""
                decl_t = elem_decl_t if elem_decl_t != "" else self.normalize_type_name(self.get_expr_type(e))
                decl_t = decl_t if decl_t != "" else "unknown"
                self.declared_var_types[nm] = decl_t
                if self.is_any_like_type(decl_t):
                    self.emit(f"auto {nm} = ::std::get<{i}>({src});")
                else:
                    self.emit(f"{self._cpp_type_text(decl_t)} {nm} = ::std::get<{i}>({src});")

    def emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノードを C++ の for ループとして出力する。"""
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target_node) == 0:
            self.emit("/* invalid for-range target */")
            return
        tgt = self.render_expr(stmt.get("target"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        tgt_ty_txt = t0 if t0 != "" else t1
        tgt_ty = self._cpp_type_text(tgt_ty_txt)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_braces = self.hook_on_stmt_omit_braces("ForRange", stmt, False)
        if len(body_stmts) != 1:
            omit_braces = False
        mode = self.hook_on_for_range_mode(stmt, "dynamic")
        if mode not in {"ascending", "descending", "dynamic"}:
            mode = "dynamic"
        cond = (
            f"{tgt} < {stop}"
            if mode == "ascending"
            else (f"{tgt} > {stop}" if mode == "descending" else f"{step} > 0 ? {tgt} < {stop} : {tgt} > {stop}")
        )
        inc = (
            f"++{tgt}"
            if self._opt_ge(2) and step == "1"
            else (f"--{tgt}" if self._opt_ge(2) and step == "-1" else f"{tgt} += {step}")
        )
        hdr: str = self.syntax_line(
            "for_range_open",
            "for ({type} {target} = {start}; {cond}; {inc})",
            {"type": tgt_ty, "target": tgt, "start": start, "cond": cond, "inc": inc},
        )
        self.declared_var_types[tgt] = tgt_ty_txt
        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            scope_names: set[str] = set()
            scope_names.add(tgt)
            self.scope_stack.append(scope_names)
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(
            self.syntax_line(
                "for_open_block",
                "{header} {",
                {"header": hdr},
            )
        )
        scope_names: set[str] = set()
        scope_names.add(tgt)
        self.emit_scoped_stmt_list(body_stmts, scope_names)
        self.emit_block_close()

    def emit_for_each(self, stmt: dict[str, Any]) -> None:
        """For ノード（反復）を C++ range-for として出力する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        iter_expr = self.any_to_dict_or_empty(stmt.get("iter"))
        if len(target) == 0 or len(iter_expr) == 0:
            self.emit("/* invalid for */")
            return
        if self._node_kind_from_dict(iter_expr) == "RangeExpr":
            t_raw = stmt.get("target_type")
            target_type_txt = "int64"
            if isinstance(t_raw, str) and t_raw != "":
                target_type_txt = t_raw
            self.emit_for_range(
                {
                    "target": stmt.get("target"),
                    "target_type": target_type_txt,
                    "start": iter_expr.get("start"),
                    "stop": iter_expr.get("stop"),
                    "step": iter_expr.get("step"),
                    "range_mode": self.any_dict_get_str(iter_expr, "range_mode", "dynamic"),
                    "body": self.any_dict_get_list(stmt, "body"),
                    "orelse": self.any_dict_get_list(stmt, "orelse"),
                }
            )
            return
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_braces = self.hook_on_stmt_omit_braces("For", stmt, False)
        if len(body_stmts) != 1:
            omit_braces = False
        iter_mode = self._resolve_for_iter_mode(stmt, iter_expr)
        if iter_mode == "runtime_protocol":
            self._emit_for_each_runtime(stmt, target, iter_expr, body_stmts, omit_braces)
            return
        t = self.render_expr(stmt.get("target"))
        it = self.render_expr(stmt.get("iter"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        t_ty = self._cpp_type_text(t0 if t0 != "" else t1)
        target_names = self._target_bound_names(target)
        unpack_tuple = self._node_kind_from_dict(target) == "Tuple"
        iter_tmp = ""
        hdr = ""
        if unpack_tuple:
            iter_tmp = self.next_tmp("__it")
            hdr = self.syntax_line(
                "for_each_unpack_open",
                "for (auto {iter_tmp} : {iter})",
                {"iter_tmp": iter_tmp, "iter": it},
            )
        else:
            hdr = (
                self.syntax_line(
                    "for_each_auto_ref_open",
                    "for (auto& {target} : {iter})",
                    {"target": t, "iter": it},
                )
                if t_ty == "auto"
                else self.syntax_line(
                    "for_each_typed_open",
                    "for ({type} {target} : {iter})",
                    {"type": t_ty, "target": t, "iter": it},
                )
            )
            if t_ty != "auto":
                self.declared_var_types[t] = t0 if t0 != "" else t1
        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            self.scope_stack.append(set(target_names))
            if unpack_tuple:
                self._emit_target_unpack(target, iter_tmp, iter_expr)
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(
            self.syntax_line(
                "for_open_block",
                "{header} {",
                {"header": hdr},
            )
        )
        self.indent += 1
        self.scope_stack.append(set(target_names))
        if unpack_tuple:
            self._emit_target_unpack(target, iter_tmp, iter_expr)
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def _target_expr_from_target_plan(self, target_plan: dict[str, Any]) -> dict[str, Any]:
        """EAST3 `target_plan` を既存 For/ForRange 互換の target ノードへ変換する。"""
        plan_kind = self.any_dict_get_str(target_plan, "kind", "")
        target_type = self.any_dict_get_str(target_plan, "target_type", "unknown")
        if plan_kind == "NameTarget":
            target_id = self.any_dict_get_str(target_plan, "id", "")
            if target_id != "":
                return {
                    "kind": "Name",
                    "id": target_id,
                    "resolved_type": target_type,
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": target_id,
                }
            return {}
        if plan_kind == "TupleTarget":
            elem_plans = self.any_to_list(target_plan.get("elements"))
            elements: list[dict[str, Any]] = []
            for elem_plan_obj in elem_plans:
                elem_plan = self.any_to_dict_or_empty(elem_plan_obj)
                elem_target = self._target_expr_from_target_plan(elem_plan)
                if len(elem_target) > 0:
                    elements.append(elem_target)
            return {
                "kind": "Tuple",
                "resolved_type": target_type if target_type != "" else "unknown",
                "borrow_kind": "value",
                "casts": [],
                "repr": "",
                "elements": elements,
            }
        if plan_kind == "ExprTarget":
            target_expr = self.any_to_dict_or_empty(target_plan.get("target"))
            if len(target_expr) > 0:
                return target_expr
        return {}

    def _range_mode_from_step_expr(self, step_expr: dict[str, Any]) -> str:
        """`step` 式から `range_mode`（ascending/descending/dynamic）を求める。"""
        step_value = step_expr.get("value")
        if isinstance(step_value, int):
            if step_value == 1:
                return "ascending"
            if step_value == -1:
                return "descending"
        return "dynamic"

    def emit_for_core(self, stmt: dict[str, Any]) -> None:
        """EAST3 `ForCore` を既存 For/ForRange 出力へ写像する。"""
        iter_plan = self.any_to_dict_or_empty(stmt.get("iter_plan"))
        plan_kind = self.any_dict_get_str(iter_plan, "kind", "")
        target_plan = self.any_to_dict_or_empty(stmt.get("target_plan"))
        target_expr = self._target_expr_from_target_plan(target_plan)
        if len(target_expr) == 0:
            self.emit("/* invalid forcore target */")
            return
        target_type = self.any_dict_get_str(target_plan, "target_type", "unknown")
        body_stmts = self.any_dict_get_list(stmt, "body")
        orelse_stmts = self.any_dict_get_list(stmt, "orelse")

        if plan_kind == "StaticRangeForPlan":
            start_expr = iter_plan.get("start")
            stop_expr = iter_plan.get("stop")
            step_obj = iter_plan.get("step")
            step_expr = self.any_to_dict_or_empty(step_obj)
            if len(step_expr) == 0:
                step_expr = {"kind": "Constant", "resolved_type": "int64", "value": 1, "repr": "1"}
            self.emit_for_range(
                {
                    "target": target_expr,
                    "target_type": target_type if target_type != "" else "int64",
                    "start": start_expr,
                    "stop": stop_expr,
                    "step": step_expr,
                    "range_mode": self._range_mode_from_step_expr(step_expr),
                    "body": body_stmts,
                    "orelse": orelse_stmts,
                }
            )
            return

        if plan_kind == "RuntimeIterForPlan":
            iter_expr = self.any_to_dict_or_empty(iter_plan.get("iter_expr"))
            if len(iter_expr) == 0:
                self.emit("/* invalid forcore runtime iter_plan */")
                return
            self.emit_for_each(
                {
                    "target": target_expr,
                    "target_type": target_type,
                    "iter_mode": "runtime_protocol",
                    "iter": iter_expr,
                    "body": body_stmts,
                    "orelse": orelse_stmts,
                }
            )
            return

        self.emit(f"/* unsupported ForCore iter_plan kind: {plan_kind} */")

    def _resolve_for_iter_mode(self, stmt: dict[str, Any], iter_expr: dict[str, Any]) -> str:
        """`For` の反復モード（static/runtime）を決定する。"""
        mode_txt = self.any_to_str(stmt.get("iter_mode"))
        if mode_txt == "static_fastpath" or mode_txt == "runtime_protocol":
            return mode_txt
        iter_t = self.normalize_type_name(self.get_expr_type(iter_expr))
        if iter_t == "":
            iter_t = self.normalize_type_name(self.any_dict_get_str(iter_expr, "resolved_type", ""))
        if iter_t == "Any" or iter_t == "object":
            return "runtime_protocol"
        # 明示 `iter_mode` が無い既存 EAST では selfhost 互換を優先し、unknown は static 側に倒す。
        if iter_t == "" or iter_t == "unknown":
            return "static_fastpath"
        if self._contains_text(iter_t, "|"):
            parts = self.split_union(iter_t)
            for p in parts:
                p_norm = self.normalize_type_name(p)
                if p_norm == "Any" or p_norm == "object":
                    return "runtime_protocol"
            return "static_fastpath"
        return "static_fastpath"

    def _emit_target_unpack_runtime(self, target: dict[str, Any], src_obj: str) -> None:
        """runtime iterable プロトコル用のタプル unpack（`py_at` ベース）。"""
        if self._node_kind_from_dict(target) != "Tuple":
            return
        elems = self.any_to_list(target.get("elements"))
        for i, e in enumerate(elems):
            e_node = self.any_to_dict_or_empty(e)
            if self._node_kind_from_dict(e_node) != "Name":
                continue
            nm = self.render_expr(e)
            rhs = f"py_at({src_obj}, {i})"
            decl_t = self.normalize_type_name(self.get_expr_type(e))
            if self._can_runtime_cast_target(decl_t) and not self.is_any_like_type(decl_t):
                rhs = self.render_expr(
                    self._build_unbox_expr_node(
                        self._build_py_at_expr_node(src_obj, i),
                        decl_t,
                        f"for_unpack:{nm}",
                    )
                )
                self.emit(f"{self._cpp_type_text(decl_t)} {nm} = {rhs};")
                self.declared_var_types[nm] = decl_t
            else:
                self.emit(f"auto {nm} = {rhs};")
                self.declared_var_types[nm] = "object"

    def _emit_for_each_runtime(
        self,
        stmt: dict[str, Any],
        target: dict[str, Any],
        iter_expr: dict[str, Any],
        body_stmts: list[dict[str, Any]],
        omit_braces: bool,
    ) -> None:
        """`For` を runtime iterable プロトコル（`py_dyn_range`）で出力する。"""
        t = self.render_expr(stmt.get("target"))
        it = self.render_expr(stmt.get("iter"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        t_decl = self.normalize_type_name(t0 if t0 != "" else t1)
        unpack_tuple = self._node_kind_from_dict(target) == "Tuple"
        target_names = self._target_bound_names(target)
        iter_tmp = ""
        hdr = ""
        needs_tmp = unpack_tuple or self._node_kind_from_dict(target) != "Name" or not self.is_any_like_type(t_decl)
        if needs_tmp:
            iter_tmp = self.next_tmp("__itobj")
            hdr = self.syntax_line(
                "for_each_runtime_open",
                "for (object {iter_tmp} : py_dyn_range({iter}))",
                {"iter_tmp": iter_tmp, "iter": it},
            )
        else:
            hdr = self.syntax_line(
                "for_each_runtime_target_open",
                "for (object {target} : py_dyn_range({iter}))",
                {"target": t, "iter": it},
            )
            if t != "":
                self.declared_var_types[t] = "object"

        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            self.scope_stack.append(set(target_names))
            if unpack_tuple:
                self._emit_target_unpack_runtime(target, iter_tmp)
            elif iter_tmp != "" and self._node_kind_from_dict(target) == "Name":
                rhs = iter_tmp
                if self._can_runtime_cast_target(t_decl):
                    rhs = self.render_expr(
                        self._build_unbox_expr_node(
                            self._build_name_expr_node(iter_tmp, "object"),
                            t_decl,
                            f"for_target:{t}",
                        )
                    )
                    self.emit(f"{self._cpp_type_text(t_decl)} {t} = {rhs};")
                    self.declared_var_types[t] = t_decl
                else:
                    self.emit(f"auto {t} = {rhs};")
                    self.declared_var_types[t] = "object"
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(
            self.syntax_line(
                "for_open_block",
                "{header} {",
                {"header": hdr},
            )
        )
        self.indent += 1
        self.scope_stack.append(set(target_names))
        if unpack_tuple:
            self._emit_target_unpack_runtime(target, iter_tmp)
        elif iter_tmp != "" and self._node_kind_from_dict(target) == "Name":
            rhs = iter_tmp
            if self._can_runtime_cast_target(t_decl):
                rhs = self.render_expr(
                    self._build_unbox_expr_node(
                        self._build_name_expr_node(iter_tmp, "object"),
                        t_decl,
                        f"for_target:{t}",
                    )
                )
                self.emit(f"{self._cpp_type_text(t_decl)} {t} = {rhs};")
                self.declared_var_types[t] = t_decl
            else:
                self.emit(f"auto {t} = {rhs};")
                self.declared_var_types[t] = "object"
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def emit_function(self, stmt: dict[str, Any], in_class: bool = False) -> None:
        """関数定義ノードを C++ 関数として出力する。"""
        name = self.any_dict_get_str(stmt, "name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        is_generator = self.any_dict_get_int(stmt, "is_generator", 0) != 0
        yield_value_type = self.any_to_str(stmt.get("yield_value_type"))
        ret = self.cpp_type(stmt.get("return_type"))
        if is_generator:
            elem_type_for_cpp = yield_value_type
            if elem_type_for_cpp in {"", "unknown"}:
                elem_type_for_cpp = "Any"
            elem_cpp = self._cpp_type_text(elem_type_for_cpp)
            ret = f"list<{elem_cpp}>"
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_defaults = self.any_to_dict_or_empty(stmt.get("arg_defaults"))
        arg_index = self.any_to_dict_or_empty(stmt.get("arg_index"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        params: list[str] = []
        fn_scope: set[str] = set()
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "":
                n = str(raw_n)
                if n in arg_types:
                    arg_names.append(n)
        mutated_params = self._collect_mutated_params(body_stmts, arg_names)
        for idx, n in enumerate(arg_names):
            t = self.any_to_str(arg_types.get(n))
            skip_self = in_class and idx == 0 and n == "self"
            ct = self._cpp_type_text(t)
            usage = self.any_to_str(arg_usage.get(n))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and n in mutated_params:
                usage = "mutable"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if skip_self:
                pass
            else:
                param_txt = (
                    (f"{ct} {n}" if ct == "object" else f"{ct}& {n}")
                    if by_ref and usage == "mutable"
                    else (f"const {ct}& {n}" if by_ref else f"{ct} {n}")
                )
                if n in arg_defaults:
                    default_txt = self._render_param_default_expr(arg_defaults.get(n), t)
                    if default_txt != "":
                        default_txt = self._coerce_param_signature_default(default_txt, t)
                        param_txt += f" = {default_txt}"
                params.append(param_txt)
                fn_scope.add(n)
        if in_class and name == "__init__" and self.current_class_name is not None:
            param_sep = ", "
            params_txt = param_sep.join(params)
            if self.current_class_base_name == "CodeEmitter":
                self.emit(f"{self.current_class_name}({params_txt}) : CodeEmitter(east_doc, load_cpp_profile(), dict<str, object>{{}}) {{")
            else:
                self.emit_ctor_open(str(self.current_class_name), params_txt)
        elif in_class and name == "__del__" and self.current_class_name is not None:
            self.emit_dtor_open(str(self.current_class_name))
        else:
            param_sep = ", "
            params_txt = param_sep.join(params)
            self.emit_function_open(ret, str(emitted_name), params_txt)
        docstring = self.any_to_str(stmt.get("docstring"))
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        prev_ret = self.current_function_return_type
        prev_is_gen = self.current_function_is_generator
        prev_yield_buf = self.current_function_yield_buffer
        prev_yield_ty = self.current_function_yield_type
        prev_decl_types = self.declared_var_types
        empty_decl_types: dict[str, str] = {}
        self.declared_var_types = empty_decl_types
        for i, an in enumerate(arg_names):
            if not (in_class and i == 0 and an == "self"):
                at = self.any_to_str(arg_types.get(an))
                if at != "":
                    self.declared_var_types[an] = self.normalize_type_name(at)
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        self.current_function_is_generator = is_generator
        self.current_function_yield_type = yield_value_type if yield_value_type != "" else "Any"
        self.current_function_yield_buffer = self.next_tmp("__yield_values") if is_generator else ""
        is_gc_ctor = (
            in_class
            and name == "__init__"
            and self.current_class_name is not None
            and self.current_class_name in self.ref_classes
        )
        if is_gc_ctor:
            self.emit("this->set_type_id(PYTRA_TYPE_ID);")
        if docstring != "":
            self.emit_block_comment(docstring)
        if is_generator:
            yield_elem_ty = self.current_function_yield_type
            if yield_elem_ty in {"", "unknown"}:
                yield_elem_ty = "Any"
            yield_elem_cpp = self._cpp_type_text(yield_elem_ty)
            self.emit(f"list<{yield_elem_cpp}> {self.current_function_yield_buffer} = list<{yield_elem_cpp}>{{}};")
        self.emit_stmt_list(body_stmts)
        if is_generator and self.current_function_yield_buffer != "":
            self.emit(f"return {self.current_function_yield_buffer};")
        self.current_function_return_type = prev_ret
        self.current_function_is_generator = prev_is_gen
        self.current_function_yield_buffer = prev_yield_buf
        self.current_function_yield_type = prev_yield_ty
        self.declared_var_types = prev_decl_types
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def emit_class(self, stmt: dict[str, Any]) -> None:
        """クラス定義ノードを C++ クラス/struct として出力する。"""
        name = self.any_dict_get_str(stmt, "name", "Class")
        is_dataclass = self.any_dict_get_int(stmt, "dataclass", 0) != 0
        base = self.any_to_str(stmt.get("base"))
        if base in {"Exception", "BaseException", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError"}:
            # Python 例外継承は runtime 側の C++ 例外階層と1対1対応しないため、
            # クラス本体（フィールド/メソッド）を優先して継承は省略する。
            base = ""
        is_enum_base = base in {"Enum", "IntEnum", "IntFlag"}
        if is_enum_base:
            cls_name = str(name)
            enum_members: list[str] = []
            enum_values: list[str] = []
            class_body = self._dict_stmt_list(stmt.get("body"))
            for s in class_body:
                sk = self._node_kind_from_dict(s)
                if sk == "Assign":
                    texpr = self.any_to_dict_or_empty(s.get("target"))
                    if self.is_name(s.get("target"), None):
                        member = self.any_to_str(texpr.get("id"))
                        if member != "":
                            enum_members.append(member)
                            enum_values.append(self.render_expr(s.get("value")))
                elif sk == "AnnAssign":
                    texpr = self.any_to_dict_or_empty(s.get("target"))
                    if self.is_name(s.get("target"), None):
                        member = self.any_to_str(texpr.get("id"))
                        if member != "":
                            val = "0"
                            if s.get("value") is not None:
                                val = self.render_expr(s.get("value"))
                            enum_members.append(member)
                            enum_values.append(val)
            self.emit(f"enum class {cls_name} : int64 {{")
            self.indent += 1
            for i, member in enumerate(enum_members):
                value_txt = enum_values[i]
                sep = "," if i + 1 < len(enum_members) else ""
                self.emit(f"{member} = {value_txt}{sep}")
            self.indent -= 1
            self.emit("};")
            self.emit("")
            if base in {"IntEnum", "IntFlag"}:
                self.emit(f"static inline int64 py_to_int64({cls_name} v) {{ return static_cast<int64>(v); }}")
                self.emit(f"static inline bool operator==({cls_name} lhs, int64 rhs) {{ return static_cast<int64>(lhs) == rhs; }}")
                self.emit(f"static inline bool operator==(int64 lhs, {cls_name} rhs) {{ return lhs == static_cast<int64>(rhs); }}")
                self.emit(f"static inline bool operator!=({cls_name} lhs, int64 rhs) {{ return !(lhs == rhs); }}")
                self.emit(f"static inline bool operator!=(int64 lhs, {cls_name} rhs) {{ return !(lhs == rhs); }}")
                if base == "IntFlag":
                    self.emit(f"static inline {cls_name} operator|({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) | static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator&({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) & static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator^({cls_name} lhs, {cls_name} rhs) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(static_cast<int64>(lhs) ^ static_cast<int64>(rhs));")
                    self.indent -= 1
                    self.emit("}")
                    self.emit(f"static inline {cls_name} operator~({cls_name} v) {{")
                    self.indent += 1
                    self.emit(f"return static_cast<{cls_name}>(~static_cast<int64>(v));")
                    self.indent -= 1
                    self.emit("}")
            self.emit("")
            return
        cls_name = str(name)
        gc_managed = cls_name in self.ref_classes
        bases: list[str] = []
        if base != "" and not is_enum_base:
            bases.append(f"public {base}")
        base_is_gc = base in self.ref_classes
        if gc_managed and not base_is_gc:
            bases.append("public PyObj")
        base_txt: str = ""
        if len(bases) > 0:
            sep = ", "
            base_txt = " : " + sep.join(bases)
        self.emit_class_open(str(name), base_txt)
        self.indent += 1
        prev_class = self.current_class_name
        prev_class_base = self.current_class_base_name
        prev_fields = self.current_class_fields
        prev_static_fields = self.current_class_static_fields
        self.current_class_name = str(name)
        self.current_class_base_name = str(base) if isinstance(base, str) else ""
        self.current_class_fields.clear()
        for fk, fv in self.any_to_dict_or_empty(stmt.get("field_types")).items():
            if isinstance(fk, str):
                self.current_class_fields[fk] = self.any_to_str(fv)
        class_body = self._dict_stmt_list(stmt.get("body"))
        static_field_types: dict[str, str] = {}
        static_field_defaults: dict[str, str] = {}
        instance_field_defaults: dict[str, str] = {}
        field_decl_order: list[str] = []
        static_field_order: list[str] = []
        consumed_assign_fields: set[str] = set()
        for s in class_body:
            if self._node_kind_from_dict(s) == "AnnAssign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_plain_name_expr(s.get("target")):
                    fname = self.any_dict_get_str(texpr, "id", "")
                    ann = self.any_to_str(s.get("annotation"))
                    if ann != "":
                        if fname != "" and fname not in field_decl_order:
                            field_decl_order.append(fname)
                        if fname != "":
                            cur_t = self.current_class_fields.get(fname, "")
                            if not isinstance(cur_t, str) or cur_t == "" or cur_t == "unknown":
                                self.current_class_fields[fname] = ann
                        if is_dataclass:
                            instance_field_defaults[fname] = self.render_expr(s.get("value")) if s.get("value") is not None else instance_field_defaults.get(fname, "")
                        else:
                            # クラス直下 `AnnAssign` は、値ありのみ static 扱い。
                            # 値なしはインスタンスフィールド宣言（型ヒント）として扱う。
                            if s.get("value") is not None:
                                static_field_types[fname] = ann
                                if fname not in static_field_order:
                                    static_field_order.append(fname)
                                static_field_defaults[fname] = self.render_expr(s.get("value"))
            elif is_enum_base and self._node_kind_from_dict(s) == "Assign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_name(s.get("target"), None):
                    fname = self.any_to_str(texpr.get("id"))
                    if fname != "":
                        inferred = self.get_expr_type(s.get("value"))
                        ann = inferred if isinstance(inferred, str) else ""
                        if ann == "" or ann == "unknown":
                            ann = "int64" if base in {"IntEnum", "IntFlag"} else "int64"
                        static_field_types[fname] = ann
                        if fname not in static_field_order:
                            static_field_order.append(fname)
                        if s.get("value") is not None:
                            static_field_defaults[fname] = self.render_expr(s.get("value"))
                        consumed_assign_fields.add(fname)
        self.current_class_static_fields.clear()
        for k, _ in static_field_types.items():
            if isinstance(k, str) and k != "":
                self.current_class_static_fields.add(k)
        instance_fields_ordered: list[tuple[str, str]] = []
        seen_instance_fields: set[str] = set()
        for fname in field_decl_order:
            if fname in self.current_class_static_fields:
                continue
            fty_any = self.current_class_fields.get(fname, "")
            if not isinstance(fty_any, str):
                continue
            if fname in seen_instance_fields:
                continue
            instance_fields_ordered.append((fname, fty_any))
            seen_instance_fields.add(fname)
        remaining_instance_keys: list[str] = []
        for k, v in self.current_class_fields.items():
            if (
                isinstance(k, str)
                and isinstance(v, str)
                and k not in self.current_class_static_fields
                and k not in seen_instance_fields
            ):
                remaining_instance_keys.append(k)
        remaining_instance_keys = sort_str_list_copy(remaining_instance_keys)
        for fname in remaining_instance_keys:
            fty_fallback = self.current_class_fields.get(fname, "")
            if isinstance(fty_fallback, str):
                instance_fields_ordered.append((fname, fty_fallback))
                seen_instance_fields.add(fname)
        has_init = False
        for s in class_body:
            if self._node_kind_from_dict(s) == "FunctionDef" and s.get("name") == "__init__":
                has_init = True
                break
        static_emit_names: list[str] = []
        for fname in static_field_order:
            if fname in static_field_types and fname not in static_emit_names:
                static_emit_names.append(fname)
        extra_static_names: list[str] = []
        for fname, _ in static_field_types.items():
            if fname not in static_emit_names:
                extra_static_names.append(fname)
        extra_static_names = sort_str_list_copy(extra_static_names)
        for fname in extra_static_names:
            static_emit_names.append(fname)
        for fname in static_emit_names:
            fty = static_field_types.get(fname, "")
            if not isinstance(fty, str) or fty == "":
                continue
            if fname in static_field_defaults:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname} = {static_field_defaults[fname]};")
            else:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname};")
        for fname, fty in instance_fields_ordered:
            self.emit(f"{self._cpp_type_text(fty)} {fname};")
        if gc_managed:
            base_type_id_expr = f"{base}::PYTRA_TYPE_ID" if base_is_gc else "PYTRA_TID_OBJECT"
            self.emit(f"inline static uint32 PYTRA_TYPE_ID = py_register_class_type(list<uint32>{{{base_type_id_expr}}});")
        if len(static_emit_names) > 0 or len(instance_fields_ordered) > 0 or gc_managed:
            self.emit("")
        if (len(instance_fields_ordered) > 0 or gc_managed) and not has_init:
            params: list[str] = []
            for fname, fty in instance_fields_ordered:
                p = f"{self._cpp_type_text(fty)} {fname}"
                if fname in instance_field_defaults and instance_field_defaults[fname] != "":
                    p += f" = {instance_field_defaults[fname]}"
                params.append(p)
            self.emit(f"{name}({join_str_list(', ', params)}) {{")
            self.indent += 1
            self.scope_stack.append(set())
            if gc_managed:
                self.emit("this->set_type_id(PYTRA_TYPE_ID);")
            for fname, _ in instance_fields_ordered:
                self.emit(f"this->{fname} = {fname};")
            self.scope_stack.pop()
            self.indent -= 1
            self.emit_block_close()
            self.emit("")
        for s in class_body:
            if self._node_kind_from_dict(s) == "AnnAssign":
                t = self.cpp_type(s.get("annotation"))
                target = self.render_expr(s.get("target"))
                if self.is_plain_name_expr(s.get("target")) and target in self.current_class_fields:
                    pass
                elif s.get("value") is None:
                    self.emit(f"{t} {target};")
                else:
                    self.emit(f"{t} {target} = {self.render_expr(s.get('value'))};")
            elif is_enum_base and self._node_kind_from_dict(s) == "Assign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                skip_stmt = False
                if self.is_name(s.get("target"), None):
                    fname = self.any_to_str(texpr.get("id"))
                    if fname in consumed_assign_fields:
                        skip_stmt = True
                if not skip_stmt:
                    self.emit_stmt(s)
            else:
                self.emit_stmt(s)
        self.current_class_name = prev_class
        self.current_class_base_name = prev_class_base
        self.current_class_fields = prev_fields
        self.current_class_static_fields = prev_static_fields
        self.indent -= 1
        self.emit_class_close()

    def _render_binop_expr(self, expr: dict[str, Any]) -> str:
        """BinOp ノードを C++ 式へ変換する。"""
        if expr.get("left") is None or expr.get("right") is None:
            rep = self.any_to_str(expr.get("repr"))
            if rep != "":
                return rep
        left_expr = self.any_to_dict_or_empty(expr.get("left"))
        right_expr = self.any_to_dict_or_empty(expr.get("right"))
        left = self.render_expr(expr.get("left"))
        right = self.render_expr(expr.get("right"))
        cast_rules = self._dict_stmt_list(expr.get("casts"))
        for c in cast_rules:
            on = self.any_to_str(c.get("on"))
            to_txt = self.any_to_str(c.get("to"))
            if on == "left":
                left = self.apply_cast(left, to_txt)
            elif on == "right":
                right = self.apply_cast(right, to_txt)
        op_name = expr.get("op")
        op_name_str = str(op_name)
        dunder_by_binop: dict[str, str] = {
            "Add": "__add__",
            "Sub": "__sub__",
            "Mult": "__mul__",
            "Div": "__truediv__",
            "Pow": "__pow__",
        }
        dunder_name = dunder_by_binop.get(op_name_str, "")
        if dunder_name != "":
            left_t0 = self.get_expr_type(expr.get("left"))
            left_t = left_t0 if isinstance(left_t0, str) else ""
            left_t_norm = self.normalize_type_name(left_t)
            method_sig = self._class_method_sig(left_t, dunder_name)
            if left_t_norm not in {"", "unknown", "Any", "object"} and len(method_sig) > 0:
                call_args = self._coerce_args_for_class_method(left_t, dunder_name, [right], [expr.get("right")])
                owner = f"({left})"
                if left_t_norm in self.ref_classes and not left.strip().startswith("*"):
                    return f"{owner}->{dunder_name}({join_str_list(', ', call_args)})"
                return f"{owner}.{dunder_name}({join_str_list(', ', call_args)})"
        left = self._wrap_for_binop_operand(left, left_expr, op_name_str, False)
        right = self._wrap_for_binop_operand(right, right_expr, op_name_str, True)
        hook_binop_raw = self.hook_on_render_binop(expr, left, right)
        hook_binop_txt = ""
        if isinstance(hook_binop_raw, str):
            hook_binop_txt = str(hook_binop_raw)
        if hook_binop_txt != "":
            return hook_binop_txt
        if op_name == "Div":
            # Prefer direct C++ division when float is involved (or EAST already injected casts).
            # Keep py_div fallback for int/int Python semantics.
            lt0 = self.get_expr_type(expr.get("left"))
            rt0 = self.get_expr_type(expr.get("right"))
            lt = lt0 if isinstance(lt0, str) else ""
            rt = rt0 if isinstance(rt0, str) else ""
            if lt == "Path" and rt in {"str", "Path"}:
                return f"{left} / {right}"
            if len(cast_rules) > 0 or lt in {"float32", "float64"} or rt in {"float32", "float64"}:
                return f"{left} / {right}"
            return f"py_div({left}, {right})"
        if op_name == "Pow":
            return f"::std::pow(py_to_float64({left}), py_to_float64({right}))"
        if op_name == "FloorDiv":
            if self.floor_div_mode == "python":
                return f"py_floordiv({left}, {right})"
            return f"{left} / {right}"
        if op_name == "Mod":
            if self.mod_mode == "python":
                return f"py_mod({left}, {right})"
            return f"{left} % {right}"
        if op_name == "Mult":
            lt0 = self.get_expr_type(expr.get("left"))
            rt0 = self.get_expr_type(expr.get("right"))
            lt = lt0 if isinstance(lt0, str) else ""
            rt = rt0 if isinstance(rt0, str) else ""
            if lt.startswith("list[") and rt in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({left}, {right})"
            if rt.startswith("list[") and lt in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({right}, {left})"
            if lt == "str" and rt in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({left}, {right})"
            if rt == "str" and lt in {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}:
                return f"py_repeat({right}, {left})"
        op = "+"
        op_txt = str(BIN_OPS.get(op_name_str, ""))
        if op_txt != "":
            op = op_txt
        return f"{left} {op} {right}"

    def _render_builtin_call(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        first_arg: Any,
    ) -> str:
        """lowered_kind=BuiltinCall の呼び出しを処理する。"""
        runtime_call = self.any_dict_get_str(expr, "runtime_call", "")
        builtin_name = self.any_dict_get_str(expr, "builtin_name", "")
        owner_expr = self._render_builtin_call_owner_expr(expr, fn)
        any_boundary_expr = self._build_any_boundary_expr_from_builtin_call(
            builtin_name,
            runtime_call,
            arg_nodes,
        )
        if any_boundary_expr is not None:
            return self.render_expr(any_boundary_expr)
        if runtime_call == "static_cast":
            static_cast_rendered = self._render_builtin_static_cast_call(expr, builtin_name, args, first_arg)
            if static_cast_rendered is not None:
                return str(static_cast_rendered)
        list_ops_rendered = self._render_builtin_runtime_list_ops(runtime_call, expr, fn, args, arg_nodes)
        if list_ops_rendered is not None:
            return str(list_ops_rendered)
        set_ops_rendered = self._render_builtin_runtime_set_ops(runtime_call, fn, args, arg_nodes)
        if set_ops_rendered is not None:
            return str(set_ops_rendered)
        dict_ops_rendered = self._render_builtin_runtime_dict_ops(runtime_call, expr, fn, args)
        if dict_ops_rendered is not None:
            return str(dict_ops_rendered)
        str_ops_rendered = self._render_builtin_runtime_str_ops(runtime_call, fn, args, arg_nodes)
        if str_ops_rendered is not None:
            return str(str_ops_rendered)
        special_runtime_rendered = self._render_builtin_runtime_special_ops(runtime_call, fn, args, kw)
        if special_runtime_rendered is not None:
            return str(special_runtime_rendered)
        runtime_fallback = self._render_builtin_runtime_fallback(
            runtime_call,
            expr,
            fn,
            args,
            arg_nodes,
            first_arg,
            owner_expr,
        )
        if runtime_fallback is not None:
            return str(runtime_fallback)
        if builtin_name == "bytes":
            return f"bytes({join_str_list(', ', args)})" if len(args) >= 1 else "bytes{}"
        if builtin_name == "bytearray":
            return f"bytearray({join_str_list(', ', args)})" if len(args) >= 1 else "bytearray{}"
        return ""

    def _render_builtin_runtime_list_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の list 系 runtime_call を処理する。"""
        _ = expr
        if runtime_call not in {"list.append", "list.extend", "list.pop", "list.clear", "list.reverse", "list.sort"}:
            return None
        owner_node: Any = fn.get("value")
        owner = self.render_expr(owner_node)
        owner_t0 = self.get_expr_type(owner_node)
        owner_t = owner_t0 if isinstance(owner_t0, str) else ""
        owner_types: list[str] = [owner_t]
        if self._contains_text(owner_t, "|"):
            owner_types = self.split_union(owner_t)
        if runtime_call == "list.append":
            if len(arg_nodes) >= 1:
                append_node = {
                    "kind": "ListAppend",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(append_node)
            append_rendered = self._render_append_call_object_method(owner_types, owner, args, arg_nodes)
            if append_rendered is not None:
                return append_rendered
            if len(args) >= 1:
                return f"{owner}.append({args[0]})"
            return f"{owner}.append(/* missing */)"
        if runtime_call == "list.extend":
            if len(arg_nodes) >= 1:
                extend_node = {
                    "kind": "ListExtend",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(extend_node)
            a0 = args[0] if len(args) >= 1 else "{}"
            return f"{owner}.insert({owner}.end(), {a0}.begin(), {a0}.end())"
        if runtime_call == "list.pop":
            pop_node = {
                "kind": "ListPop",
                "owner": owner_node,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                pop_node["index"] = arg_nodes[0]
            return self.render_expr(pop_node)
        if runtime_call == "list.clear":
            clear_node = {
                "kind": "ListClear",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(clear_node)
        if runtime_call == "list.reverse":
            reverse_node = {
                "kind": "ListReverse",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(reverse_node)
        if runtime_call == "list.sort":
            sort_node = {
                "kind": "ListSort",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(sort_node)
        return None

    def _render_builtin_runtime_set_ops(
        self,
        runtime_call: str,
        fn: dict[str, Any],
        args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の set 系 runtime_call を処理する。"""
        if runtime_call == "set.add":
            owner_node = fn.get("value")
            if len(arg_nodes) >= 1:
                set_add_node = {
                    "kind": "SetAdd",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(set_add_node)
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            return f"{owner}.insert({a0})"
        if runtime_call in {"set.discard", "set.remove"}:
            owner_node = fn.get("value")
            if len(arg_nodes) >= 1:
                set_erase_node = {
                    "kind": "SetErase",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(set_erase_node)
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            return f"{owner}.erase({a0})"
        if runtime_call == "set.clear":
            clear_node = {
                "kind": "SetClear",
                "owner": fn.get("value"),
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(clear_node)
        return None

    def _render_builtin_runtime_dict_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
    ) -> str | None:
        """BuiltinCall の dict 系 runtime_call を処理する。"""
        if runtime_call not in {"dict.get", "dict.pop", "dict.items", "dict.keys", "dict.values"}:
            return None
        owner_node: Any = fn.get("value")
        owner = self.render_expr(owner_node)
        owner_t = self.get_expr_type(owner_node)
        if runtime_call == "dict.get":
            owner_value_t = ""
            owner_optional_object_dict = False
            if owner_t.startswith("dict[") and owner_t.endswith("]"):
                owner_inner = self.split_generic(owner_t[5:-1])
                if len(owner_inner) == 2:
                    owner_value_t = self.normalize_type_name(owner_inner[1])
            owner_parts: list[str] = []
            if self._contains_text(owner_t, "|"):
                owner_parts = self.split_union(owner_t)
            else:
                owner_parts = [owner_t]
            if len(owner_parts) >= 2:
                has_none = False
                has_dict_object_part = False
                i = 0
                while i < len(owner_parts):
                    p = self.normalize_type_name(owner_parts[i])
                    if p == "None":
                        has_none = True
                    elif p.startswith("dict[") and p.endswith("]"):
                        inner = self.split_generic(p[5:-1])
                        if len(inner) == 2 and self.is_any_like_type(self.normalize_type_name(inner[1])):
                            has_dict_object_part = True
                            if owner_value_t == "":
                                owner_value_t = self.normalize_type_name(inner[1])
                    i += 1
                if has_none and has_dict_object_part:
                    owner_optional_object_dict = True
            objectish_owner = (
                self.is_any_like_type(owner_t)
                or self.is_any_like_type(owner_value_t)
                or owner_optional_object_dict
            )
            key_expr = args[0] if len(args) >= 1 else "/* missing */"
            arg_nodes = self.any_to_list(expr.get("args"))
            key_node: Any = None
            if len(arg_nodes) >= 1:
                key_node = arg_nodes[0]
            if not objectish_owner:
                key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            if len(args) >= 2:
                out_t = self.normalize_type_name(self.any_to_str(expr.get("resolved_type")))
                int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
                float_out_types = {"float32", "float64"}
                default_t = ""
                default_node: Any = None
                if len(arg_nodes) >= 2:
                    default_node = arg_nodes[1]
                if default_node is not None:
                    default_t = self.normalize_type_name(self.get_expr_type(default_node))
                if len(arg_nodes) >= 2:
                    get_default_node = {
                        "kind": "DictGetDefault",
                        "owner": owner_node,
                        "key": arg_nodes[0],
                        "default": default_node,
                        "out_type": out_t,
                        "default_type": default_t,
                        "owner_value_type": owner_value_t,
                        "objectish_owner": objectish_owner,
                        "owner_optional_object_dict": owner_optional_object_dict,
                        "resolved_type": self.any_to_str(expr.get("resolved_type")),
                        "borrow_kind": "value",
                        "casts": [],
                    }
                    return self.render_expr(get_default_node)
                if objectish_owner and out_t == "bool":
                    return f"dict_get_bool({owner}, {key_expr}, {args[1]})"
                if objectish_owner and out_t == "str":
                    return f"dict_get_str({owner}, {key_expr}, {args[1]})"
                if objectish_owner and out_t in int_out_types:
                    cast_t = self._cpp_type_text(out_t)
                    return f"static_cast<{cast_t}>(dict_get_int({owner}, {key_expr}, py_to_int64({args[1]})))"
                if objectish_owner and out_t in float_out_types:
                    cast_t = self._cpp_type_text(out_t)
                    return f"static_cast<{cast_t}>(dict_get_float({owner}, {key_expr}, py_to_float64({args[1]})))"
                if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "bool":
                    return f"dict_get_bool({owner}, {key_expr}, {args[1]})"
                if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "str":
                    return f"dict_get_str({owner}, {key_expr}, {args[1]})"
                if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in int_out_types:
                    return f"dict_get_int({owner}, {key_expr}, py_to_int64({args[1]}))"
                if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in float_out_types:
                    return f"dict_get_float({owner}, {key_expr}, py_to_float64({args[1]}))"
                if objectish_owner and out_t in {"", "unknown"} and default_t.startswith("list["):
                    return f"dict_get_list({owner}, {key_expr}, {args[1]})"
                if objectish_owner and out_t.startswith("list["):
                    return f"dict_get_list({owner}, {key_expr}, {args[1]})"
                if objectish_owner and (self.is_any_like_type(out_t) or out_t == "object"):
                    if owner_optional_object_dict:
                        boxed_default = self._box_any_target_value(args[1], default_node)
                        return f"py_dict_get_default({owner}, {key_expr}, {boxed_default})"
                    return f"dict_get_node({owner}, {key_expr}, {args[1]})"
                if not objectish_owner:
                    default_expr = args[1]
                    val_t = self.normalize_type_name(owner_value_t)
                    if default_expr in {"::std::nullopt", "std::nullopt"} and val_t not in {"", "None"}:
                        allows_nullopt = False
                        if val_t.startswith("optional[") and val_t.endswith("]"):
                            allows_nullopt = True
                        elif self._contains_text(val_t, "|"):
                            parts = self.split_union(val_t)
                            i = 0
                            while i < len(parts):
                                if self.normalize_type_name(parts[i]) == "None":
                                    allows_nullopt = True
                                    break
                                i += 1
                        if (not allows_nullopt) and (not self.is_any_like_type(val_t)):
                            default_expr = self._cpp_type_text(val_t) + "()"
                    return f"{owner}.get({key_expr}, {default_expr})"
                if owner_optional_object_dict:
                    boxed_default = self._box_any_target_value(args[1], default_node)
                    return f"py_dict_get_default({owner}, {key_expr}, {boxed_default})"
                return f"py_dict_get_default({owner}, {key_expr}, {args[1]})"
            if len(args) == 1:
                if len(arg_nodes) >= 1:
                    maybe_node = {
                        "kind": "DictGetMaybe",
                        "owner": owner_node,
                        "key": arg_nodes[0],
                        "resolved_type": self.any_to_str(expr.get("resolved_type")),
                        "borrow_kind": "value",
                        "casts": [],
                    }
                    return self.render_expr(maybe_node)
                return f"py_dict_get_maybe({owner}, {key_expr})"
            return ""
        if runtime_call == "dict.pop":
            key_expr = args[0] if len(args) >= 1 else "/* missing */"
            arg_nodes = self.any_to_list(expr.get("args"))
            key_node: Any = None
            if len(arg_nodes) >= 1:
                key_node = arg_nodes[0]
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            if len(args) <= 1:
                if len(arg_nodes) >= 1:
                    pop_node = {
                        "kind": "DictPop",
                        "owner": owner_node,
                        "key": arg_nodes[0],
                        "resolved_type": self.any_to_str(expr.get("resolved_type")),
                        "borrow_kind": "value",
                        "casts": [],
                    }
                    return self.render_expr(pop_node)
                return f"{owner}.pop({key_expr})"
            owner_t0 = self.get_expr_type(owner_node)
            owner_t2 = owner_t0 if isinstance(owner_t0, str) else ""
            val_t = "Any"
            if owner_t2.startswith("dict[") and owner_t2.endswith("]"):
                inner = self.split_generic(owner_t2[5:-1])
                if len(inner) == 2 and inner[1] != "":
                    val_t = self.normalize_type_name(inner[1])
            if len(arg_nodes) >= 2:
                pop_default_node = {
                    "kind": "DictPopDefault",
                    "owner": owner_node,
                    "key": arg_nodes[0],
                    "default": arg_nodes[1],
                    "value_type": val_t,
                    "resolved_type": self.any_to_str(expr.get("resolved_type")),
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(pop_default_node)
            default_expr = args[1]
            if default_expr in {"::std::nullopt", "std::nullopt"} and not self.is_any_like_type(val_t) and val_t != "None":
                default_expr = self._cpp_type_text(val_t) + "()"
            return f"({owner}.contains({key_expr}) ? {owner}.pop({key_expr}) : {default_expr})"
        if runtime_call == "dict.items":
            items_node = {
                "kind": "DictItems",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(items_node)
        if runtime_call == "dict.keys":
            keys_node = {
                "kind": "DictKeys",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(keys_node)
        if runtime_call == "dict.values":
            values_node = {
                "kind": "DictValues",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(values_node)
        return None

    def _render_builtin_runtime_str_ops(
        self,
        runtime_call: str,
        fn: dict[str, Any],
        args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の文字列系 runtime_call を処理する。"""
        if runtime_call not in {
            "py_isdigit",
            "py_isalpha",
            "py_strip",
            "py_rstrip",
            "py_lstrip",
            "py_startswith",
            "py_endswith",
            "py_replace",
            "py_join",
        }:
            return None
        owner_node = self.any_to_dict_or_empty(fn.get("value"))
        owner = self.render_expr(fn.get("value"))
        owner_kind = self._node_kind_from_dict(owner_node)
        if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            owner = "(" + owner + ")"
        if runtime_call == "py_isdigit":
            if len(args) == 0:
                return owner + ".isdigit()"
            if len(args) == 1:
                return args[0] + ".isdigit()"
        if runtime_call == "py_isalpha":
            if len(args) == 0:
                return owner + ".isalpha()"
            if len(args) == 1:
                return args[0] + ".isalpha()"
        if runtime_call == "py_strip":
            strip_node = {
                "kind": "StrStripOp",
                "mode": "strip",
                "owner": fn.get("value"),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                strip_node["chars"] = arg_nodes[0]
            return self.render_expr(strip_node)
            if len(args) == 0:
                return f"py_strip({owner})"
            if len(args) == 1:
                return f"{owner}.strip({args[0]})"
        if runtime_call == "py_rstrip":
            rstrip_node = {
                "kind": "StrStripOp",
                "mode": "rstrip",
                "owner": fn.get("value"),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                rstrip_node["chars"] = arg_nodes[0]
            return self.render_expr(rstrip_node)
            if len(args) == 0:
                return f"py_rstrip({owner})"
            if len(args) == 1:
                return f"{owner}.rstrip({args[0]})"
        if runtime_call == "py_lstrip":
            lstrip_node = {
                "kind": "StrStripOp",
                "mode": "lstrip",
                "owner": fn.get("value"),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                lstrip_node["chars"] = arg_nodes[0]
            return self.render_expr(lstrip_node)
            if len(args) == 0:
                return f"py_lstrip({owner})"
            if len(args) == 1:
                return f"{owner}.lstrip({args[0]})"
        if runtime_call == "py_startswith":
            if len(args) == 1:
                return f"py_startswith({owner}, {args[0]})"
            if len(args) == 2:
                start = f"py_to_int64({args[1]})"
                return f"py_startswith(py_slice({owner}, {start}, py_len({owner})), {args[0]})"
            if len(args) >= 3:
                start = f"py_to_int64({args[1]})"
                end = f"py_to_int64({args[2]})"
                return f"py_startswith(py_slice({owner}, {start}, {end}), {args[0]})"
        if runtime_call == "py_endswith":
            if len(args) == 1:
                return f"py_endswith({owner}, {args[0]})"
            if len(args) == 2:
                start = f"py_to_int64({args[1]})"
                return f"py_endswith(py_slice({owner}, {start}, py_len({owner})), {args[0]})"
            if len(args) >= 3:
                start = f"py_to_int64({args[1]})"
                end = f"py_to_int64({args[2]})"
                return f"py_endswith(py_slice({owner}, {start}, {end}), {args[0]})"
        if runtime_call == "py_replace" and len(args) == 2:
            return f"py_replace({owner}, {args[0]}, {args[1]})"
        if runtime_call == "py_join" and len(args) == 1:
            return f"str({owner}).join({args[0]})"
        return None

    def _render_builtin_runtime_special_ops(
        self,
        runtime_call: str,
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
    ) -> str | None:
        """BuiltinCall の Path/utility 系 runtime_call を処理する。"""
        owner_node = self.any_to_dict_or_empty(fn.get("value"))
        owner = self.render_expr(fn.get("value"))
        owner_kind = self._node_kind_from_dict(owner_node)
        if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            owner = "(" + owner + ")"
        if runtime_call == "std::filesystem::create_directories":
            parents = kw.get("parents", "false")
            exist_ok = kw.get("exist_ok", "false")
            if len(args) >= 1:
                parents = args[0]
            if len(args) >= 2:
                exist_ok = args[1]
            return f"{owner}.mkdir({parents}, {exist_ok})"
        if runtime_call == "std::filesystem::exists":
            return f"{owner}.exists()"
        if runtime_call == "py_write_text":
            write_arg = args[0] if len(args) >= 1 else '""'
            return f"{owner}.write_text({write_arg})"
        if runtime_call == "py_read_text":
            return f"{owner}.read_text()"
        if runtime_call == "path_parent":
            return f"{owner}.parent()"
        if runtime_call == "path_name":
            return f"{owner}.name()"
        if runtime_call == "path_stem":
            return f"{owner}.stem()"
        if runtime_call == "identity":
            return owner
        return None

    def _render_builtin_runtime_fallback(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        arg_nodes: list[Any],
        first_arg: Any,
        owner_expr: str,
    ) -> str | None:
        """hooks 無効時に BuiltinCall の runtime 分岐を描画する。"""
        if runtime_call == "py_print":
            return f"py_print({join_str_list(', ', args)})"
        if runtime_call == "py_len" and len(args) == 1:
            return f"py_len({args[0]})"
        if runtime_call == "py_to_string" and len(args) == 1:
            src_expr = first_arg
            return self.render_to_string(src_expr)
        if runtime_call in {"py_min", "py_max"} and len(args) >= 1:
            fn_name = "min" if runtime_call == "py_min" else "max"
            return self.render_minmax(fn_name, args, self.any_to_str(expr.get("resolved_type")), arg_nodes)
        if runtime_call == "perf_counter":
            return "pytra::std::time::perf_counter()"
        if runtime_call == "open":
            return f"open({join_str_list(', ', args)})"
        if runtime_call == "py_int_to_bytes":
            owner = self.render_expr(fn.get("value"))
            length = args[0] if len(args) >= 1 else "0"
            byteorder = args[1] if len(args) >= 2 else '"little"'
            return f"py_int_to_bytes({owner}, {length}, {byteorder})"
        if runtime_call == "py_join":
            join_rendered = self._render_builtin_join_call(owner_expr, args)
            if join_rendered is not None:
                return str(join_rendered)
        if runtime_call in {"std::runtime_error", "::std::runtime_error"}:
            if len(args) == 0:
                return '::std::runtime_error("error")'
            return f"::std::runtime_error({args[0]})"
        if runtime_call == "Path":
            return f"Path({join_str_list(', ', args)})"
        owner_runtime_rendered = self._render_builtin_call_owner_runtime(runtime_call, owner_expr, args)
        if owner_runtime_rendered is not None:
            return str(owner_runtime_rendered)
        return None

    def _render_builtin_call_owner_expr(self, expr: dict[str, Any], fn: dict[str, Any]) -> str:
        """BuiltinCall の owner 式（`obj.method` 側）を解決する。"""
        if self._node_kind_from_dict(fn) != "Attribute":
            return ""
        runtime_owner_obj = expr.get("runtime_owner")
        runtime_owner_node = self.any_to_dict_or_empty(runtime_owner_obj)
        if len(runtime_owner_node) > 0:
            return self.render_expr(runtime_owner_obj)
        return self.render_expr(fn.get("value"))

    def _render_builtin_call_owner_runtime(
        self,
        runtime_call: str,
        owner_expr: str,
        args: list[str],
    ) -> str | None:
        """BuiltinCall の owner 付き runtime_call 分岐を描画する。"""
        if runtime_call in {"std::filesystem::exists", "::std::filesystem::exists"} and owner_expr != "" and len(args) == 0:
            return f"{runtime_call}({owner_expr})"
        if runtime_call == "py_replace" and owner_expr != "" and len(args) >= 2:
            return f"py_replace({owner_expr}, {args[0]}, {args[1]})"
        if runtime_call in {"py_startswith", "py_endswith", "py_find", "py_rfind"} and owner_expr != "" and len(args) >= 1:
            return f"{runtime_call}({owner_expr}, {join_str_list(', ', args)})"
        if runtime_call != "" and (self._is_std_runtime_call(runtime_call) or runtime_call.startswith("py_")):
            if owner_expr != "" and runtime_call.startswith("py_") and len(args) == 0:
                return f"{runtime_call}({owner_expr})"
            return f"{runtime_call}({join_str_list(', ', args)})"
        return None

    def _render_dict_get_default_expr(
        self,
        owner_node: Any,
        key_node: Any,
        default_node: Any,
        out_t: str,
        default_t: str,
        owner_value_t: str,
        objectish_owner: bool,
        owner_optional_object_dict: bool,
    ) -> str:
        """`dict.get(key, default)` の既定値あり経路を描画する。"""
        owner_expr = self.render_expr(owner_node)
        key_expr = self.render_expr(key_node)
        default_expr = self.render_expr(default_node)
        if not objectish_owner:
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
        int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_out_types = {"float32", "float64"}
        if objectish_owner and out_t == "bool":
            return f"dict_get_bool({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t == "str":
            return f"dict_get_str({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in int_out_types:
            cast_t = self._cpp_type_text(out_t)
            return f"static_cast<{cast_t}>(dict_get_int({owner_expr}, {key_expr}, py_to_int64({default_expr})))"
        if objectish_owner and out_t in float_out_types:
            cast_t = self._cpp_type_text(out_t)
            return f"static_cast<{cast_t}>(dict_get_float({owner_expr}, {key_expr}, py_to_float64({default_expr})))"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "bool":
            return f"dict_get_bool({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "str":
            return f"dict_get_str({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in int_out_types:
            return f"dict_get_int({owner_expr}, {key_expr}, py_to_int64({default_expr}))"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in float_out_types:
            return f"dict_get_float({owner_expr}, {key_expr}, py_to_float64({default_expr}))"
        if objectish_owner and out_t in {"", "unknown"} and default_t.startswith("list["):
            return f"dict_get_list({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t.startswith("list["):
            return f"dict_get_list({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and (self.is_any_like_type(out_t) or out_t == "object"):
            if owner_optional_object_dict:
                boxed_default = self._box_any_target_value(default_expr, default_node)
                return f"py_dict_get_default({owner_expr}, {key_expr}, {boxed_default})"
            return f"dict_get_node({owner_expr}, {key_expr}, {default_expr})"
        if not objectish_owner:
            if default_expr in {"::std::nullopt", "std::nullopt"}:
                val_t = self.normalize_type_name(owner_value_t)
                if val_t not in {"", "None"}:
                    allows_nullopt = False
                    if val_t.startswith("optional[") and val_t.endswith("]"):
                        allows_nullopt = True
                    elif self._contains_text(val_t, "|"):
                        parts = self.split_union(val_t)
                        i = 0
                        while i < len(parts):
                            if self.normalize_type_name(parts[i]) == "None":
                                allows_nullopt = True
                                break
                            i += 1
                    if (not allows_nullopt) and (not self.is_any_like_type(val_t)):
                        default_expr = self._cpp_type_text(val_t) + "()"
            return f"{owner_expr}.get({key_expr}, {default_expr})"
        if owner_optional_object_dict:
            boxed_default = self._box_any_target_value(default_expr, default_node)
            return f"py_dict_get_default({owner_expr}, {key_expr}, {boxed_default})"
        return f"py_dict_get_default({owner_expr}, {key_expr}, {default_expr})"

    def _render_builtin_static_cast_call(
        self,
        expr: dict[str, Any],
        builtin_name: str,
        args: list[str],
        first_arg: Any,
    ) -> str | None:
        """BuiltinCall の `runtime_call=static_cast` 分岐を描画する。"""
        if len(args) == 1:
            target = self.cpp_type(expr.get("resolved_type"))
            arg_t = self.get_expr_type(first_arg)
            numeric_t = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if target == "int64" and arg_t == "str":
                return f"py_to_int64({args[0]})"
            if target in {"float64", "float32"} and arg_t == "str":
                return f"py_to_float64({args[0]})"
            if target == "int64" and arg_t in numeric_t:
                return f"int64({args[0]})"
            if target == "int64" and self.is_any_like_type(arg_t):
                return f"py_to_int64({args[0]})"
            if target in {"float64", "float32"} and self.is_any_like_type(arg_t):
                return f"py_to_float64({args[0]})"
            if target == "bool" and self.is_any_like_type(arg_t):
                return f"py_to_bool({args[0]})"
            if target == "int64":
                return f"py_to_int64({args[0]})"
            return f"static_cast<{target}>({args[0]})"
        if len(args) == 2 and builtin_name == "int":
            return f"py_to_int64_base({args[0]}, py_to_int64({args[1]}))"
        return None

    def _render_builtin_join_call(
        self,
        owner_expr: str,
        args: list[str],
    ) -> str | None:
        """BuiltinCall の `runtime_call=py_join` 分岐を描画する。"""
        if len(args) != 1 or owner_expr == "":
            return None
        return f"str({owner_expr}).join({args[0]})"

    def _render_collection_constructor_call(
        self,
        raw: str,
        expr: dict[str, Any],
        args: list[str],
        first_arg: Any,
    ) -> str | None:
        """`set/list/dict` コンストラクタ呼び出しの型依存分岐を共通化する。"""
        if raw not in {"set", "list", "dict"}:
            return None
        t = self.cpp_type(expr.get("resolved_type"))
        if len(args) == 0:
            return f"{t}{{}}"
        if len(args) != 1:
            return None
        at0 = self.get_expr_type(first_arg)
        at = at0 if isinstance(at0, str) else ""
        head = f"{raw}["
        if at.startswith(head):
            return args[0]
        any_obj_t = "set<object>"
        starts = "set<"
        ctor_name = "set"
        if raw == "list":
            any_obj_t = "list<object>"
            starts = "list<"
            ctor_name = "list"
        if raw == "dict":
            any_obj_t = "dict<str, object>"
            starts = "dict<"
            ctor_name = "dict"
        if t == any_obj_t and at in {"Any", "object"}:
            return f"{t}({args[0]})"
        if t.startswith(starts):
            if t == any_obj_t and at not in {"Any", "object"}:
                return args[0]
            return f"{t}({args[0]})"
        return f"{ctor_name}({args[0]})"

    def _render_scalar_cast_builtin_call(
        self,
        raw: str,
        expr: dict[str, Any],
        args: list[str],
        first_arg: Any,
    ) -> str | None:
        """`int/float/bool` の1引数キャスト呼び出しを共通化する。"""
        if raw not in {"int", "float", "bool"}:
            return None
        if len(args) != 1:
            return None
        target = self.cpp_type(expr.get("resolved_type"))
        arg_t = self.get_expr_type(first_arg)
        numeric_t = {
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
            "float32",
            "float64",
            "bool",
        }
        if raw == "bool" and self.is_any_like_type(arg_t):
            return f"py_to_bool({args[0]})"
        if raw == "float" and self.is_any_like_type(arg_t):
            return f"py_to_float64({args[0]})"
        if raw == "float" and arg_t == "str":
            return f"py_to_float64({args[0]})"
        if raw == "int" and target == "int64" and arg_t == "str":
            return f"py_to_int64({args[0]})"
        if raw == "int" and target == "int64" and arg_t in numeric_t:
            return f"int64({args[0]})"
        if raw == "int" and target == "int64":
            return f"py_to_int64({args[0]})"
        return f"static_cast<{target}>({args[0]})"

    def _render_isinstance_type_check(self, value_expr: str, type_name: str) -> str:
        """`isinstance(x, T)` の `T` に対応する runtime 判定式を返す。"""
        type_id_expr = self._render_type_id_operand_expr({"kind": "Name", "id": type_name})
        if type_id_expr != "":
            return f"py_isinstance({value_expr}, {type_id_expr})"
        return "false"

    def _build_box_expr_node(self, value_node: Any) -> dict[str, Any]:
        return {
            "kind": "Box",
            "value": value_node,
            "resolved_type": "object",
            "borrow_kind": "value",
            "casts": [],
        }

    def _build_unbox_expr_node(self, value_node: Any, target_t: str, ctx: str) -> dict[str, Any]:
        t_norm = self.normalize_type_name(target_t)
        return {
            "kind": "Unbox",
            "value": value_node,
            "target": t_norm,
            "ctx": ctx,
            "resolved_type": t_norm,
            "borrow_kind": "value",
            "casts": [],
        }

    def _build_name_expr_node(self, name: str, resolved_type: str = "unknown") -> dict[str, Any]:
        return {
            "kind": "Name",
            "id": name,
            "resolved_type": resolved_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": name,
        }

    def _build_constant_int_expr_node(self, value: int) -> dict[str, Any]:
        return {
            "kind": "Constant",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": str(value),
            "value": value,
        }

    def _build_py_at_expr_node(self, container_name: str, index: int) -> dict[str, Any]:
        return {
            "kind": "Call",
            "func": self._build_name_expr_node("py_at"),
            "args": [
                self._build_name_expr_node(container_name, "object"),
                self._build_constant_int_expr_node(index),
            ],
            "keywords": [],
            "resolved_type": "object",
            "borrow_kind": "value",
            "casts": [],
            "repr": f"py_at({container_name}, {index})",
        }

    def _render_type_id_operand_expr(self, type_id_node: Any) -> str:
        """type_id 式ノードを C++ の type_id 式へ写像する。"""
        node = self.any_to_dict_or_empty(type_id_node)
        if len(node) == 0:
            return ""
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            type_name = self.any_to_str(node.get("id")).strip()
            if type_name == "":
                return ""
            if type_name == "PYTRA_TID_NONE":
                return "PYTRA_TID_NONE"
            if type_name == "PYTRA_TID_BOOL":
                return "PYTRA_TID_BOOL"
            if type_name == "PYTRA_TID_INT":
                return "PYTRA_TID_INT"
            if type_name == "PYTRA_TID_FLOAT":
                return "PYTRA_TID_FLOAT"
            if type_name == "PYTRA_TID_STR":
                return "PYTRA_TID_STR"
            if type_name == "PYTRA_TID_LIST":
                return "PYTRA_TID_LIST"
            if type_name == "PYTRA_TID_DICT":
                return "PYTRA_TID_DICT"
            if type_name == "PYTRA_TID_SET":
                return "PYTRA_TID_SET"
            if type_name == "PYTRA_TID_OBJECT":
                return "PYTRA_TID_OBJECT"
            if type_name == "None":
                return "PYTRA_TID_NONE"
            if type_name == "bool":
                return "PYTRA_TID_BOOL"
            if type_name == "int":
                return "PYTRA_TID_INT"
            if type_name == "float":
                return "PYTRA_TID_FLOAT"
            if type_name == "str":
                return "PYTRA_TID_STR"
            if type_name == "list":
                return "PYTRA_TID_LIST"
            if type_name == "dict":
                return "PYTRA_TID_DICT"
            if type_name == "set":
                return "PYTRA_TID_SET"
            if type_name == "object":
                return "PYTRA_TID_OBJECT"
            if type_name in self.ref_classes:
                return f"{type_name}::PYTRA_TYPE_ID"
            if self.is_declared(type_name):
                return type_name
            return ""
        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(node.get("value"))
            owner_kind = self._node_kind_from_dict(owner_node)
            owner_name = self.any_to_str(owner_node.get("id")).strip()
            attr_name = self.any_to_str(node.get("attr")).strip()
            if owner_kind == "Name" and attr_name == "PYTRA_TYPE_ID" and owner_name in self.ref_classes:
                return f"{owner_name}::PYTRA_TYPE_ID"
        rendered = self.render_expr(type_id_node)
        if rendered == "/* none */":
            return ""
        return rendered

    def _const_false_expr_node(self) -> dict[str, Any]:
        return {
            "kind": "Constant",
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": "False",
            "value": False,
        }

    def _boolop_or_expr_node(self, values: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "kind": "BoolOp",
            "op": "Or",
            "values": values,
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
        }

    def _collect_type_ref_nodes_for_isinstance(self, type_node: Any) -> list[dict[str, Any]]:
        node = self.any_to_dict_or_empty(type_node)
        if len(node) == 0:
            return []
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            return [node]
        if kind == "Tuple":
            out: list[dict[str, Any]] = []
            for elt in self.tuple_elements(node):
                ent = self.any_to_dict_or_empty(elt)
                if self._node_kind_from_dict(ent) == "Name":
                    out.append(ent)
            return out
        return []

    def _build_type_id_expr_from_call_name(
        self,
        raw_name: str,
        arg_nodes: list[Any],
    ) -> dict[str, Any] | None:
        if raw_name == "isinstance":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            value_node = arg_nodes[0]
            type_nodes = self._collect_type_ref_nodes_for_isinstance(arg_nodes[1])
            if len(type_nodes) == 0:
                return self._const_false_expr_node()
            checks: list[dict[str, Any]] = []
            for type_node in type_nodes:
                checks.append(
                    {
                        "kind": "IsInstance",
                        "value": value_node,
                        "expected_type_id": type_node,
                        "resolved_type": "bool",
                        "borrow_kind": "value",
                        "casts": [],
                    }
                )
            if len(checks) == 1:
                return checks[0]
            return self._boolop_or_expr_node(checks)
        if raw_name == "issubclass":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            actual_type_node = arg_nodes[0]
            expected_nodes = self._collect_type_ref_nodes_for_isinstance(arg_nodes[1])
            if len(expected_nodes) == 0:
                return self._const_false_expr_node()
            checks = []
            for expected_node in expected_nodes:
                checks.append(
                    {
                        "kind": "IsSubclass",
                        "actual_type_id": actual_type_node,
                        "expected_type_id": expected_node,
                        "resolved_type": "bool",
                        "borrow_kind": "value",
                        "casts": [],
                    }
                )
            if len(checks) == 1:
                return checks[0]
            return self._boolop_or_expr_node(checks)
        if raw_name == "py_isinstance" or raw_name == "py_tid_isinstance":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsInstance",
                "value": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "py_issubclass" or raw_name == "py_tid_issubclass":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsSubclass",
                "actual_type_id": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "py_is_subtype" or raw_name == "py_tid_is_subtype":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsSubtype",
                "actual_type_id": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "py_runtime_type_id" or raw_name == "py_tid_runtime_type_id":
            if len(arg_nodes) != 1:
                return None
            return {
                "kind": "ObjTypeId",
                "value": arg_nodes[0],
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
        return None

    def _build_any_boundary_expr_from_call_name(
        self,
        raw_name: str,
        arg_nodes: list[Any],
    ) -> dict[str, Any] | None:
        if len(arg_nodes) != 1:
            return None
        arg0 = arg_nodes[0]
        arg0_t = self.get_expr_type(arg0)
        if not self.is_any_like_type(arg0_t):
            return None
        if raw_name == "bool":
            return {
                "kind": "ObjBool",
                "value": arg0,
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "len":
            return {
                "kind": "ObjLen",
                "value": arg0,
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "str":
            return {
                "kind": "ObjStr",
                "value": arg0,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "iter":
            return {
                "kind": "ObjIterInit",
                "value": arg0,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
        if raw_name == "next":
            return {
                "kind": "ObjIterNext",
                "iter": arg0,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
        return None

    def _build_any_boundary_expr_from_builtin_call(
        self,
        builtin_name: str,
        runtime_call: str,
        arg_nodes: list[Any],
    ) -> dict[str, Any] | None:
        if len(arg_nodes) != 1:
            return None
        arg0 = arg_nodes[0]
        arg0_t = self.get_expr_type(arg0)
        if not self.is_any_like_type(arg0_t):
            return None
        if builtin_name == "bool" or runtime_call == "py_to_bool":
            return {
                "kind": "ObjBool",
                "value": arg0,
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if builtin_name == "len" or runtime_call == "py_len":
            return {
                "kind": "ObjLen",
                "value": arg0,
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
        if builtin_name == "str" or runtime_call == "py_to_string":
            return {
                "kind": "ObjStr",
                "value": arg0,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
        if builtin_name == "iter" or runtime_call == "py_iter_or_raise":
            return {
                "kind": "ObjIterInit",
                "value": arg0,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
        if builtin_name == "next" or runtime_call == "py_next_or_stop":
            return {
                "kind": "ObjIterNext",
                "iter": arg0,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
        return None

    def _render_simple_name_builtin_call(self, raw: str, args: list[str]) -> str | None:
        """Name 呼び出しの単純ビルトイン分岐を描画する。"""
        if raw == "print":
            return f"py_print({join_str_list(', ', args)})"
        if raw == "len" and len(args) == 1:
            return f"py_len({args[0]})"
        if raw == "reversed" and len(args) == 1:
            return f"py_reversed({args[0]})"
        if raw == "enumerate" and len(args) == 1:
            return f"py_enumerate({args[0]})"
        if raw == "enumerate" and len(args) >= 2:
            return f"py_enumerate({args[0]}, py_to_int64({args[1]}))"
        if raw == "any" and len(args) == 1:
            return f"py_any({args[0]})"
        if raw == "all" and len(args) == 1:
            return f"py_all({args[0]})"
        return None

    def _render_range_name_call(self, args: list[str], kw: dict[str, str]) -> str | None:
        """`range(...)` の Name 呼び出しを `py_range(start, stop, step)` へ lower する。"""
        if len(kw) == 0:
            if len(args) == 1:
                return f"py_range(0, {args[0]}, 1)"
            if len(args) == 2:
                return f"py_range({args[0]}, {args[1]}, 1)"
            if len(args) == 3:
                return f"py_range({args[0]}, {args[1]}, {args[2]})"
            return None
        known_kw = {"start", "stop", "step"}
        for name, _value in kw.items():
            if name not in known_kw:
                return None
        if len(args) == 0 and "stop" in kw:
            start = kw.get("start", "0")
            stop = kw["stop"]
            step = kw.get("step", "1")
            return f"py_range({start}, {stop}, {step})"
        if len(args) == 1 and "stop" in kw and "start" not in kw:
            step = kw.get("step", "1")
            return f"py_range({args[0]}, {kw['stop']}, {step})"
        if len(args) == 2 and "step" in kw and "start" not in kw and "stop" not in kw:
            return f"py_range({args[0]}, {args[1]}, {kw['step']})"
        return None

    def _resolve_or_render_imported_symbol_name_call(
        self,
        raw_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> tuple[str | None, str]:
        """`Call(Name)` で import 済みシンボルを解決し、必要なら直接呼び出しへ変換する。"""
        raw = raw_name
        imported_module = ""
        if raw and not self.is_declared(raw):
            resolved = self._resolve_imported_symbol(raw)
            imported_module = dict_str_get(resolved, "module", "")
            raw = dict_str_get(resolved, "name", "") or raw
        if not raw or not imported_module:
            return None, raw
        mapped_runtime_txt = self._resolve_runtime_call_for_imported_symbol(imported_module, raw) or ""
        if (
            mapped_runtime_txt
            and mapped_runtime_txt not in {"perf_counter", "Path"}
            and looks_like_runtime_function_name(mapped_runtime_txt)
        ):
            call_args = self.merge_call_args(args, kw)
            if self._contains_text(mapped_runtime_txt, "::"):
                call_args = self._coerce_args_for_module_function(imported_module, raw, call_args, arg_nodes)
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, call_args, arg_nodes)
            return f"{mapped_runtime_txt}({join_str_list(', ', call_args)})", raw
        target_ns = self.module_namespace_map.get(self._normalize_runtime_module_name(imported_module), "")
        if target_ns:
            namespaced = self._render_namespaced_module_call(
                imported_module,
                target_ns,
                raw,
                args,
                arg_nodes,
            )
            if namespaced is not None:
                return namespaced, raw
        return None, raw

    def _render_misc_name_builtin_call(
        self,
        raw: str,
        expr: dict[str, Any],
        args: list[str],
        arg_nodes: list[Any],
        first_arg: Any,
    ) -> str | None:
        """`Call(Name)` の残りビルトイン分岐を処理する。"""
        if raw == "bytes":
            return f"bytes({join_str_list(', ', args)})" if len(args) >= 1 else "bytes{}"
        if raw == "bytearray":
            return f"bytearray({join_str_list(', ', args)})" if len(args) >= 1 else "bytearray{}"
        if raw == "str" and len(args) == 1:
            src_expr = first_arg
            return self.render_to_string(src_expr)
        scalar_cast_rendered = self._render_scalar_cast_builtin_call(raw, expr, args, first_arg)
        if scalar_cast_rendered is not None:
            return scalar_cast_rendered
        if raw == "int" and len(args) == 2:
            return f"py_to_int64_base({args[0]}, py_to_int64({args[1]}))"
        if raw == "ord" and len(args) == 1:
            return f"py_ord({args[0]})"
        if raw == "chr" and len(args) == 1:
            return f"py_chr({args[0]})"
        if raw in {"min", "max"} and len(args) >= 1:
            return self.render_minmax(raw, args, self.any_to_str(expr.get("resolved_type")), arg_nodes)
        if raw == "perf_counter":
            return "pytra::std::time::perf_counter()"
        if raw in {"Exception", "RuntimeError"}:
            if len(args) == 0:
                return '::std::runtime_error("error")'
            return f"::std::runtime_error({args[0]})"
        if raw == "Path":
            return f"Path({join_str_list(', ', args)})"
        return None

    def _render_call_name_or_attr(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        fn_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        first_arg: Any,
    ) -> str | None:
        """Call の Name/Attribute 分岐を処理する。"""
        fn_kind = self._node_kind_from_dict(fn)
        if fn_kind == "Name":
            raw = dict_any_get_str(fn, "id")
            imported_rendered, raw = self._resolve_or_render_imported_symbol_name_call(raw, args, kw, arg_nodes)
            if imported_rendered is not None:
                return imported_rendered
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, args, arg_nodes)
                return f"pytra::utils::assertions::{raw}({join_str_list(', ', call_args)})"
            if raw == "range":
                range_rendered = self._render_range_name_call(args, kw)
                if range_rendered is not None:
                    return range_rendered
                return None
            if isinstance(raw, str) and raw in self.ref_classes:
                ctor_args = args
                if len(kw) > 0:
                    ctor_arg_names = self._class_method_name_sig(raw, "__init__")
                    ctor_args = self._merge_args_with_kw_by_name(args, kw, ctor_arg_names)
                return f"::rc_new<{raw}>({join_str_list(', ', ctor_args)})"
            any_boundary_expr = self._build_any_boundary_expr_from_call_name(raw, arg_nodes)
            if any_boundary_expr is not None:
                return self.render_expr(any_boundary_expr)
            simple_builtin_rendered = self._render_simple_name_builtin_call(raw, args)
            if simple_builtin_rendered is not None:
                return simple_builtin_rendered
            type_id_expr = self._build_type_id_expr_from_call_name(raw, arg_nodes)
            if type_id_expr is not None:
                return self.render_expr(type_id_expr)
            collection_ctor_rendered = self._render_collection_constructor_call(raw, expr, args, first_arg)
            if collection_ctor_rendered is not None:
                return collection_ctor_rendered
            misc_builtin_rendered = self._render_misc_name_builtin_call(raw, expr, args, arg_nodes, first_arg)
            if misc_builtin_rendered is not None:
                return misc_builtin_rendered
        if fn_kind == "Attribute":
            attr_rendered_txt = ""
            attr_rendered = self._render_call_attribute(expr, fn, args, kw, arg_nodes)
            if isinstance(attr_rendered, str):
                attr_rendered_txt = str(attr_rendered)
            if attr_rendered_txt != "":
                return attr_rendered_txt
        return None

    def _render_call_module_method(
        self,
        owner_mod: str,
        attr: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> str | None:
        """module.method(...) 呼び出しを処理する。"""
        hook_rendered = self.hook_on_render_module_method(owner_mod, attr, args, kw, arg_nodes)
        if isinstance(hook_rendered, str) and hook_rendered != "":
            return hook_rendered
        merged_args = self.merge_call_args(args, kw)
        owner_mod_norm = self._normalize_runtime_module_name(owner_mod)
        if owner_mod_norm in self.module_namespace_map:
            mapped = self._render_call_module_method_with_namespace(
                owner_mod,
                attr,
                self.module_namespace_map[owner_mod_norm],
                merged_args,
                arg_nodes,
            )
            if mapped is not None:
                return mapped
        fallback = self._render_call_module_method_with_namespace(
            owner_mod,
            attr,
            self._module_name_to_cpp_namespace(owner_mod_norm),
            merged_args,
            arg_nodes,
        )
        if fallback is not None:
            return fallback
        return None

    def _render_call_module_method_with_namespace(
        self,
        owner_mod: str,
        attr: str,
        ns_name: str,
        merged_args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`namespace::func(...)` 形式の module call を共通描画する。"""
        return self._render_namespaced_module_call(owner_mod, ns_name, attr, merged_args, arg_nodes)

    def _render_namespaced_module_call(
        self,
        module_name: str,
        namespace_name: str,
        func_name: str,
        rendered_args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`namespace::func(...)` 呼び出しを描画する共通 helper。"""
        if namespace_name == "":
            return None
        call_args = self._coerce_args_for_module_function(module_name, func_name, rendered_args, arg_nodes)
        if func_name.startswith("py_assert_"):
            call_args = self._coerce_py_assert_args(func_name, call_args, arg_nodes)
        return f"{namespace_name}::{func_name}({join_str_list(', ', call_args)})"

    def _render_call_class_method(
        self,
        owner_t: str,
        attr: str,
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`Class.method(...)` 分岐を処理する。"""
        method_sig = self._class_method_sig(owner_t, attr)
        if len(method_sig) == 0:
            return None
        call_args = self.merge_call_args(args, kw)
        call_args = self._coerce_args_for_class_method(owner_t, attr, call_args, arg_nodes)
        fn_expr = self._render_attribute_expr(fn)
        return f"{fn_expr}({join_str_list(', ', call_args)})"

    def _render_append_call_object_method(
        self,
        owner_types: list[str],
        owner_expr: str,
        args: list[str],
        arg_nodes: list[Any] | None = None,
    ) -> str | None:
        """`obj.append(...)` の型依存特殊処理を描画する。"""
        a0 = args[0] if len(args) >= 1 else "/* missing */"
        arg0_node: Any = {}
        if isinstance(arg_nodes, list) and len(arg_nodes) >= 1:
            arg0_node = arg_nodes[0]
        if "bytearray" in owner_types:
            a0 = f"static_cast<uint8>(py_to_int64({a0}))"
            return f"{owner_expr}.append({a0})"
        list_owner_t = ""
        for t in owner_types:
            if t.startswith("list[") and t.endswith("]"):
                list_owner_t = t
                break
        if list_owner_t != "":
            inner_t: str = list_owner_t[5:-1].strip()
            if inner_t == "uint8":
                a0 = f"static_cast<uint8>(py_to_int64({a0}))"
            elif self.is_any_like_type(inner_t):
                if not self.is_boxed_object_expr(a0):
                    arg0_node_d = self.any_to_dict_or_empty(arg0_node)
                    if len(arg0_node_d) > 0:
                        a0 = self.render_expr(self._build_box_expr_node(arg0_node))
                    else:
                        a0 = f"make_object({a0})"
            elif inner_t != "" and not self.is_any_like_type(inner_t):
                a0 = f"{self._cpp_type_text(inner_t)}({a0})"
            return f"{owner_expr}.append({a0})"
        return None

    def _render_call_attribute(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> str | None:
        """Attribute 形式の呼び出しを module/object/fallback の順で処理する。"""
        _ = expr
        owner_obj = fn.get("value")
        owner_rendered = self.render_expr(owner_obj)
        call_ctx = self.resolve_call_attribute_context(owner_obj, owner_rendered, fn, self.declared_var_types)
        owner_expr = self.any_dict_get_str(call_ctx, "owner_expr", "")
        owner_mod = self._normalize_runtime_module_name(self.any_dict_get_str(call_ctx, "owner_mod", ""))
        owner_t = self.any_dict_get_str(call_ctx, "owner_type", "")
        attr = self.any_dict_get_str(call_ctx, "attr", "")
        if attr == "":
            return None
        if owner_mod != "":
            module_rendered_1 = self._render_call_module_method(owner_mod, attr, args, kw, arg_nodes)
            if module_rendered_1 is not None and module_rendered_1 != "":
                return module_rendered_1
        return self._render_call_attribute_non_module(owner_t, owner_expr, attr, fn, args, kw, arg_nodes)

    def _make_missing_symbol_import_error(self, base_name: str, attr: str) -> Exception:
        """`from-import` 束縛名の module 参照エラーを生成する（C++ 向け）。"""
        src = dict_any_get_str(self.doc, "source_path", "(input)")
        if src == "":
            src = "(input)"
        return make_user_error(
            "input_invalid",
            "Module names are not bound by from-import statements.",
            [f"kind=missing_symbol file={src} import={base_name}.{attr}"],
        )

    def _render_call_attribute_non_module(
        self,
        owner_t: str,
        owner_expr: str,
        attr: str,
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`Call(Attribute)` の object/class 系分岐（非 module）を処理する。"""
        hook_object_rendered = self.hook_on_render_object_method(owner_t, owner_expr, attr, args)
        if isinstance(hook_object_rendered, str) and hook_object_rendered != "":
            return hook_object_rendered
        hook_class_rendered = self.hook_on_render_class_method(owner_t, attr, fn, args, kw, arg_nodes)
        if isinstance(hook_class_rendered, str) and hook_class_rendered != "":
            return hook_class_rendered
        class_rendered = self._render_call_class_method(owner_t, attr, fn, args, kw, arg_nodes)
        if class_rendered is not None and class_rendered != "":
            return class_rendered
        return None

    def _coerce_any_expr_to_target(self, expr_txt: str, target_t: str, ctx: str) -> str:
        """Any/object 式を target_t へ変換する（失敗契約は fail-fast）。"""
        t_norm = self.normalize_type_name(target_t)
        if t_norm in self.ref_classes:
            cpp_t = self._cpp_type_text(t_norm)
            ref_inner = t_norm
            if cpp_t.startswith("rc<") and cpp_t.endswith(">"):
                ref_inner = cpp_t[3:-1]
            ctx_safe = ctx.replace("\\", "\\\\").replace('"', '\\"')
            return f'obj_to_rc_or_raise<{ref_inner}>({expr_txt}, "{ctx_safe}")'
        if t_norm in {"float32", "float64"}:
            return f"py_to_float64({expr_txt})"
        if t_norm in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return f"{t_norm}(py_to_int64({expr_txt}))"
        if t_norm == "bool":
            return f"py_to_bool({expr_txt})"
        if t_norm == "str":
            return f"py_to_string({expr_txt})"
        if t_norm.startswith("list[") or t_norm.startswith("dict[") or t_norm.startswith("set["):
            return f"{self._cpp_type_text(t_norm)}({expr_txt})"
        return expr_txt

    def _coerce_call_arg(self, arg_txt: str, arg_node: Any, target_t: str) -> str:
        """関数シグネチャに合わせて引数を必要最小限キャストする。"""
        at0 = self.get_expr_type(arg_node)
        at = at0 if isinstance(at0, str) else ""
        t_norm = self.normalize_type_name(target_t)
        arg_node_dict = self.any_to_dict_or_empty(arg_node)
        if self.is_any_like_type(t_norm):
            if self.is_boxed_object_expr(arg_txt):
                return arg_txt
            if arg_txt == "*this":
                return "object(static_cast<PyObj*>(this), true)"
            if self.is_any_like_type(at):
                return arg_txt
            if len(arg_node_dict) > 0:
                return self.render_expr(self._build_box_expr_node(arg_node))
            return f"make_object({arg_txt})"
        if not self._can_runtime_cast_target(target_t):
            return arg_txt
        if not self.is_any_like_type(at):
            return arg_txt
        if len(arg_node_dict) > 0:
            return self.render_expr(self._build_unbox_expr_node(arg_node, t_norm, f"call_arg:{t_norm}"))
        return self._coerce_any_expr_to_target(arg_txt, target_t, f"call_arg:{t_norm}")

    def _coerce_args_by_signature(
        self,
        args: list[str],
        arg_nodes: list[Any],
        sig: list[str],
    ) -> list[str]:
        """シグネチャ配列に基づいて引数列を順序保持でキャストする。"""
        if len(sig) == 0:
            return args
        out: list[str] = []
        for i, arg_txt in enumerate(args):
            if i < len(sig):
                node: Any = arg_nodes[i] if i < len(arg_nodes) else {}
                out.append(self._coerce_call_arg(arg_txt, node, sig[i]))
            else:
                out.append(arg_txt)
        return out

    def _coerce_args_for_known_function(self, fn_name: str, args: list[str], arg_nodes: list[Any]) -> list[str]:
        """既知関数呼び出しに対して引数型を合わせる。"""
        if fn_name not in self.function_arg_types:
            return args
        return self._coerce_args_by_signature(args, arg_nodes, self.function_arg_types[fn_name])

    def _class_method_sig(self, owner_t: str, method: str) -> list[str]:
        """クラスメソッドの引数型シグネチャを返す。未知なら空配列。"""
        t_norm = self.normalize_type_name(owner_t)
        candidates: list[str] = []
        if self._contains_text(t_norm, "|"):
            candidates = self.split_union(t_norm)
        elif t_norm != "":
            candidates = [t_norm]
        if self.current_class_name is not None and owner_t in {"", "unknown"}:
            candidates.append(self.current_class_name)
        for c in candidates:
            if c in self.class_method_arg_types:
                mm = self.class_method_arg_types[c]
                if method in mm:
                    return mm[method]
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_types:
                mm = self.class_method_arg_types[self.current_class_name]
            if method in mm:
                return mm[method]
        return []

    def _has_class_method(self, owner_t: str, method: str) -> bool:
        """クラスメソッドが存在するかを返す（0引数メソッド対応）。"""
        t_norm = self.normalize_type_name(owner_t)
        candidates: list[str] = []
        if self._contains_text(t_norm, "|"):
            candidates = self.split_union(t_norm)
        elif t_norm != "":
            candidates = [t_norm]
        if self.current_class_name is not None and owner_t in {"", "unknown"}:
            candidates.append(self.current_class_name)
        for c in candidates:
            if c in self.class_method_arg_types:
                mm = self.class_method_arg_types[c]
                if method in mm:
                    return True
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm2: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_types:
                mm2 = self.class_method_arg_types[self.current_class_name]
            if method in mm2:
                return True
        return False

    def _class_method_name_sig(self, owner_t: str, method: str) -> list[str]:
        """クラスメソッドの引数名シグネチャを返す。未知なら空配列。"""
        t_norm = self.normalize_type_name(owner_t)
        candidates: list[str] = []
        if self._contains_text(t_norm, "|"):
            candidates = self.split_union(t_norm)
        elif t_norm != "":
            candidates = [t_norm]
        if self.current_class_name is not None and owner_t in {"", "unknown"}:
            candidates.append(self.current_class_name)
        for c in candidates:
            if c in self.class_method_arg_names:
                mm = self.class_method_arg_names[c]
                if method in mm:
                    return mm[method]
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm2: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_names:
                mm2 = self.class_method_arg_names[self.current_class_name]
            if method in mm2:
                return mm2[method]
        return []

    def _merge_args_with_kw_by_name(self, args: list[str], kw: dict[str, str], arg_names: list[str]) -> list[str]:
        """位置引数+キーワード引数を、引数名順に 1 本化する。"""
        out: list[str] = []
        for arg in args:
            out.append(arg)
        used_kw: set[str] = set()
        positional_count = len(out)
        for j, nm in enumerate(arg_names):
            if j < positional_count:
                continue
            if nm in kw:
                out.append(kw[nm])
                used_kw.add(nm)
        for nm, val in kw.items():
            if nm not in used_kw:
                out.append(val)
        return out

    def _coerce_args_for_class_method(
        self,
        owner_t: str,
        method: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """クラスメソッド呼び出しに対して引数型を合わせる。"""
        sig_raw = self._class_method_sig(owner_t, method)
        sig: list[str] = []
        for t in sig_raw:
            t_norm = self.normalize_type_name(t)
            if t_norm in {"", "unknown"}:
                sig.append("object")
            else:
                sig.append(t_norm)
        return self._coerce_args_by_signature(args, arg_nodes, sig)

    def _render_call_fallback(self, fn_name: str, args: list[str]) -> str:
        """Call の最終フォールバック（通常の関数呼び出し）を返す。"""
        if fn_name == "len" and len(args) == 1:
            return f"py_len({args[0]})"
        if fn_name == "isinstance" and len(args) == 2:
            ty = args[1].strip()
            return self._render_isinstance_type_check(args[0], ty)
        if fn_name.startswith("py_assert_"):
            call_args = self._coerce_py_assert_args(fn_name, args, [])
            return f"pytra::utils::assertions::{fn_name}({join_str_list(', ', call_args)})"
        append_fallback_rendered = self._render_append_fallback_call(fn_name, args)
        if append_fallback_rendered is not None and append_fallback_rendered != "":
            return str(append_fallback_rendered)
        if fn_name == "print":
            return f"py_print({join_str_list(', ', args)})"
        return f"{fn_name}({join_str_list(', ', args)})"

    def _render_append_fallback_call(self, fn_name: str, args: list[str]) -> str | None:
        """`obj.append(...)` の fallback 文字列呼び出しを型付き helper 経由で処理する。"""
        if not fn_name.endswith(".append") or len(args) != 1:
            return None
        owner_expr = fn_name[: len(fn_name) - 7]
        owner_t = ""
        if owner_expr in self.declared_var_types:
            owner_t = self.declared_var_types[owner_expr]
        owner_types: list[str] = [owner_t]
        if self._contains_text(owner_t, "|"):
            owner_types = self.split_union(owner_t)
        rendered = self._render_append_call_object_method(owner_types, owner_expr, args, [])
        if rendered is not None:
            return rendered
        return f"{owner_expr}.append({args[0]})"

    def _render_call_expr_from_context(
        self,
        expr_d: dict[str, Any],
        fn: dict[str, Any],
        fn_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_values: list[str],
        kw_nodes: list[Any],
        first_arg: object,
    ) -> str:
        """`Call` ノードの描画本体（前処理済みコンテキスト版）。"""
        self.validate_call_receiver_or_raise(fn)
        hook_call = self.hook_on_render_call(expr_d, fn, args, kw)
        hook_call_txt = ""
        if isinstance(hook_call, str):
            hook_call_txt = str(hook_call)
        if hook_call_txt != "":
            return hook_call_txt
        lowered_kind = self.any_dict_get_str(expr_d, "lowered_kind", "")
        has_runtime_call = self.any_dict_has(expr_d, "runtime_call")
        if lowered_kind == "BuiltinCall" or has_runtime_call:
            builtin_rendered: str = self._render_builtin_call(expr_d, fn, args, kw, arg_nodes, first_arg)
            if builtin_rendered != "":
                return builtin_rendered
        name_or_attr = self._render_call_name_or_attr(expr_d, fn, fn_name, args, kw, arg_nodes, first_arg)
        name_or_attr_txt = ""
        if isinstance(name_or_attr, str):
            name_or_attr_txt = str(name_or_attr)
        if name_or_attr_txt != "":
            return name_or_attr_txt
        merged_args = self.merge_call_kw_values(args, kw_values)
        merged_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        merged_args = self._coerce_args_for_known_function(fn_name, merged_args, merged_arg_nodes)
        return self._render_call_fallback(fn_name, merged_args)

    def _prepare_call_parts(
        self,
        expr: dict[str, Any],
    ) -> dict[str, Any]:
        """Call ノード前処理（selfhost での静的束縛回避用オーバーライド）。

        NOTE:
        基底 `CodeEmitter._prepare_call_parts` は `render_expr(...)` を呼ぶが、
        selfhost 生成 C++ では基底メソッド内からの呼び出しが静的束縛される。
        その結果、基底 `render_expr`（空文字返却）が使われて Call が `()` に崩れる。
        CppEmitter 側で同処理を持つことで `CppEmitter.render_expr` 経路を維持する。
        """
        fn_obj: object = expr.get("func")
        fn_name = self.render_expr(fn_obj)
        arg_nodes_obj: object = self.any_dict_get_list(expr, "args")
        arg_nodes = self.any_to_list(arg_nodes_obj)
        args: list[str] = []
        for arg_node in arg_nodes:
            args.append(self.render_expr(arg_node))
        keywords_obj: object = self.any_dict_get_list(expr, "keywords")
        keywords = self.any_to_list(keywords_obj)
        first_arg: object = expr
        if len(arg_nodes) > 0:
            first_arg = arg_nodes[0]
        kw: dict[str, str] = {}
        kw_values: list[str] = []
        kw_nodes: list[Any] = []
        for k in keywords:
            kd = self.any_to_dict_or_empty(k)
            if len(kd) > 0:
                kw_name = self.any_to_str(kd.get("arg"))
                if kw_name != "":
                    kw_val_node: Any = kd.get("value")
                    kw_val = self.render_expr(kw_val_node)
                    kw[kw_name] = kw_val
                    kw_values.append(kw_val)
                    kw_nodes.append(kw_val_node)
        return {
            "fn": fn_obj,
            "fn_name": fn_name,
            "arg_nodes": arg_nodes,
            "args": args,
            "kw": kw,
            "kw_values": kw_values,
            "kw_nodes": kw_nodes,
            "first_arg": first_arg,
        }

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）を式へ変換する。

        NOTE:
        C++ selfhost では、基底 CodeEmitter 側の同名メソッドをそのまま使うと
        `render_expr` が静的束縛で基底実装（空文字返却）へ落ちる。
        CppEmitter 側で明示オーバーライドして、IfExp の各部分式が
        `CppEmitter.render_expr` を通るようにする。
        """
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for c in casts:
            on = self.any_to_str(c.get("on"))
            to_t = self.any_to_str(c.get("to"))
            if on == "body":
                body = self.apply_cast(body, to_t)
            elif on == "orelse":
                orelse = self.apply_cast(orelse, to_t)
        test_expr = self.render_expr(expr.get("test"))
        test_node = self.any_to_dict_or_empty(expr.get("test"))
        if self._node_kind_from_dict(test_node) == "Constant" and isinstance(test_node.get("value"), bool):
            return body if bool(test_node.get("value")) else orelse
        if self._node_kind_from_dict(test_node) == "Name":
            ident = self.any_to_str(test_node.get("id"))
            if ident == "True":
                return body
            if ident == "False":
                return orelse
        test_txt = test_expr.strip()
        if test_txt == "true":
            return body
        if test_txt == "false":
            return orelse
        return f"({test_expr} ? {body} : {orelse})"

    def _render_operator_family_expr(
        self,
        kind: str,
        expr: Any,
        expr_d: dict[str, Any],
    ) -> str:
        """算術/比較/条件演算系ノードをまとめて描画する。"""
        if kind == "RangeExpr":
            start = self.render_expr(expr_d.get("start"))
            stop = self.render_expr(expr_d.get("stop"))
            step = self.render_expr(expr_d.get("step"))
            return f"py_range({start}, {stop}, {step})"
        if kind == "BinOp":
            return self._render_binop_expr(expr_d)
        if kind == "UnaryOp":
            return self._render_unary_expr(expr_d)
        if kind == "BoolOp":
            return self.render_boolop(expr, False)
        if kind == "Compare":
            return self._render_compare_expr(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        return ""

    def _render_unary_expr(self, expr: dict[str, Any]) -> str:
        """UnaryOp ノードを C++ 式へ変換する。"""
        operand_obj: object = expr.get("operand")
        operand_expr = self.any_to_dict_or_empty(operand_obj)
        operand = self.render_expr(operand_obj)
        op = self.any_to_str(expr.get("op"))
        if op == "Not":
            if len(operand_expr) > 0 and self._node_kind_from_dict(operand_expr) == "Compare":
                if self.any_dict_get_str(operand_expr, "lowered_kind", "") == "Contains":
                    container = self.render_expr(operand_expr.get("container"))
                    key = self.render_expr(operand_expr.get("key"))
                    ctype0 = self.get_expr_type(operand_expr.get("container"))
                    ctype = ctype0 if isinstance(ctype0, str) else ""
                    if ctype.startswith("dict["):
                        return f"{container}.find({key}) == {container}.end()"
                    return f"::std::find({container}.begin(), {container}.end(), {key}) == {container}.end()"
                ops = self.any_to_str_list(operand_expr.get("ops"))
                cmps = self._dict_stmt_list(operand_expr.get("comparators"))
                if len(ops) == 1 and len(cmps) == 1:
                    left = self.render_expr(operand_expr.get("left"))
                    rhs_node0: object = cmps[0]
                    rhs = self.render_expr(rhs_node0)
                    op0 = ops[0]
                    inv = {
                        "Eq": "!=",
                        "NotEq": "==",
                        "Lt": ">=",
                        "LtE": ">",
                        "Gt": "<=",
                        "GtE": "<",
                        "Is": "!=",
                        "IsNot": "==",
                    }
                    if op0 in inv:
                        return f"{left} {inv[op0]} {rhs}"
                    if op0 in {"In", "NotIn"}:
                        found = f"py_contains({rhs}, {left})"
                        return f"!({found})" if op0 == "In" else found
            return f"!({operand})"
        if op == "USub":
            operand_t0 = self.get_expr_type(operand_obj)
            operand_t = operand_t0 if isinstance(operand_t0, str) else ""
            operand_t_norm = self.normalize_type_name(operand_t)
            if operand_t_norm not in {"", "unknown", "Any", "object"} and self._has_class_method(operand_t, "__neg__"):
                owner = f"({operand})"
                if operand_t_norm in self.ref_classes and not operand.strip().startswith("*"):
                    return f"{owner}->__neg__()"
                return f"{owner}.__neg__()"
            return f"-{operand}"
        if op == "UAdd":
            return f"+{operand}"
        return operand

    def _render_compare_expr(self, expr: dict[str, Any]) -> str:
        """Compare ノードを C++ 式へ変換する。"""
        if self.any_dict_get_str(expr, "lowered_kind", "") == "Contains":
            container = self.render_expr(expr.get("container"))
            key = self.render_expr(expr.get("key"))
            base = f"py_contains({container}, {key})"
            if self.any_to_bool(expr.get("negated")):
                return f"!({base})"
            return base
        left = self.render_expr(expr.get("left"))
        if self._looks_like_python_expr_text(left):
            left_cpp = self._render_repr_expr(left)
            if left_cpp != "":
                left = left_cpp
        ops = self.any_to_str_list(expr.get("ops"))
        if len(ops) == 0:
            rep = self.any_dict_get_str(expr, "repr", "")
            lhs, rhs, ok = split_infix_once(rep, " not in ")
            if ok:
                lhs = self._trim_ws(lhs)
                rhs = self._trim_ws(rhs)
                if lhs != "" and rhs != "":
                    return f"!py_contains({rhs}, {lhs})"
            lhs, rhs, ok = split_infix_once(rep, " in ")
            if ok:
                lhs = self._trim_ws(lhs)
                rhs = self._trim_ws(rhs)
                if lhs != "" and rhs != "":
                    return f"py_contains({rhs}, {lhs})"
            if rep != "":
                return rep
            return "true"
        cmps = self._dict_stmt_list(expr.get("comparators"))
        parts: list[str] = []
        cur = left
        cur_node: object = expr.get("left")
        for i, op in enumerate(ops):
            rhs_node: object = cmps[i] if i < len(cmps) else {}
            rhs = self.render_expr(rhs_node)
            if self._looks_like_python_expr_text(rhs):
                rhs_cpp = self._render_repr_expr(rhs)
                if rhs_cpp != "":
                    rhs = rhs_cpp
            op_name: str = op
            cop = "=="
            cop_txt = str(CMP_OPS.get(op_name, ""))
            if cop_txt != "":
                cop = cop_txt
            if cop == "/* in */":
                parts.append(f"py_contains({rhs}, {cur})")
            elif cop == "/* not in */":
                parts.append(f"!py_contains({rhs}, {cur})")
            else:
                opt_cmp = self._try_optimize_char_compare(
                    cur_node,
                    op_name,
                    rhs_node,
                )
                if opt_cmp != "":
                    parts.append(opt_cmp)
                elif op_name in {"Is", "IsNot"} and rhs in {"std::nullopt", "::std::nullopt"}:
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({cur})")
                elif op_name in {"Is", "IsNot"} and cur in {"std::nullopt", "::std::nullopt"}:
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({rhs})")
                else:
                    parts.append(f"{cur} {cop} {rhs}")
            cur = rhs
            cur_node = rhs_node
        return join_str_list(" && ", parts) if len(parts) > 0 else "true"

    def _box_expr_for_any(self, expr_txt: str, source_node: Any) -> str:
        """Any/object 向けの boxing を必要時のみ適用する。"""
        if self.is_boxed_object_expr(expr_txt):
            return expr_txt
        src_t = self.get_expr_type(source_node)
        # `source_node` の型が unknown でも、描画済みテキストが既知変数なら
        # 宣言型ヒントから再判定して過剰 boxing を避ける。
        src_t = self.infer_rendered_arg_type(expr_txt, src_t, self.declared_var_types)
        if self.is_any_like_type(src_t):
            return expr_txt
        return f"make_object({expr_txt})"

    def _box_any_target_value(self, expr_txt: str, source_node: Any) -> str:
        """Any/object ターゲット代入用に値を boxing する（None は object{}）。"""
        if expr_txt == "":
            return expr_txt
        if expr_txt in {"object{}", "object()"}:
            return expr_txt
        source_d = self.any_to_dict_or_empty(source_node)
        if self._node_kind_from_dict(source_d) == "Constant" and source_d.get("value") is None:
            return "object{}"
        if self.is_boxed_object_expr(expr_txt):
            return expr_txt
        if len(source_d) > 0:
            boxed_expr = self.render_expr(self._build_box_expr_node(source_node))
            # 既存挙動互換: source が Any/object の場合も代入先 Any では明示 boxing を維持する。
            if boxed_expr == expr_txt and not self.is_boxed_object_expr(expr_txt):
                return f"make_object({expr_txt})"
            return boxed_expr
        return f"make_object({expr_txt})"

    def _split_call_repr(self, text: str) -> tuple[str, list[str], bool]:
        """`fn(arg0, ...)` 形式の文字列を分解する。"""
        t = self._trim_ws(text)
        if t == "" or not t.endswith(")"):
            return "", [], False
        p0 = t.find("(")
        if p0 <= 0:
            return "", [], False
        depth = 0
        n = len(t)
        for i in range(p0, n):
            ch = t[i : i + 1]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != n - 1:
                    return "", [], False
                if depth < 0:
                    return "", [], False
        if depth != 0:
            return "", [], False
        fn = self._trim_ws(t[:p0])
        inner = self._trim_ws(t[p0 + 1 : n - 1])
        args: list[str] = []
        if inner != "":
            args = split_top_level_csv(inner)
        return fn, args, True

    def _split_top_level_infix_text(self, text: str, sep: str) -> list[str]:
        """括弧/クォート外の `sep` で文字列を分割する。"""
        if sep == "":
            return []
        parts: list[str] = []
        cur = ""
        n = len(text)
        m = len(sep)
        depth_paren = 0
        depth_brack = 0
        depth_brace = 0
        quote = ""
        skip_until = 0
        for i in range(n):
            if i < skip_until:
                continue
            ch = text[i : i + 1]
            if quote != "":
                cur += ch
                if ch == quote and (i == 0 or text[i - 1 : i] != "\\"):
                    quote = ""
                continue
            if ch == "'" or ch == '"':
                quote = ch
                cur += ch
                continue
            if ch == "(":
                depth_paren += 1
                cur += ch
                continue
            if ch == ")":
                if depth_paren > 0:
                    depth_paren -= 1
                cur += ch
                continue
            if ch == "[":
                depth_brack += 1
                cur += ch
                continue
            if ch == "]":
                if depth_brack > 0:
                    depth_brack -= 1
                cur += ch
                continue
            if ch == "{":
                depth_brace += 1
                cur += ch
                continue
            if ch == "}":
                if depth_brace > 0:
                    depth_brace -= 1
                cur += ch
                continue
            if depth_paren == 0 and depth_brack == 0 and depth_brace == 0 and text[i : i + m] == sep:
                parts.append(self._trim_ws(cur))
                cur = ""
                skip_until = i + m
                continue
            cur += ch
        tail = self._trim_ws(cur)
        if tail != "":
            parts.append(tail)
        if len(parts) >= 2:
            return parts
        return []

    def _replace_all_text(self, text: str, old: str, new_txt: str) -> str:
        """`text` 内の `old` をすべて `new` へ置換する（selfhost 安定化用）。"""
        if old == "":
            return text
        out = ""
        n = len(text)
        m = len(old)
        skip_until = 0
        for i in range(n):
            if i < skip_until:
                continue
            if i + m <= n:
                matched = True
                for j in range(m):
                    if text[i + j] != old[j]:
                        matched = False
                        break
                if matched:
                    out += new_txt
                    skip_until = i + m
                    continue
            out += text[i]
        return out

    def _looks_like_python_expr_text(self, text: str) -> bool:
        """render 済み文字列に Python 構文が残っていそうかを判定する。"""
        if text == "":
            return False
        if self._contains_text(text, " or "):
            return True
        if self._contains_text(text, " and "):
            return True
        if self._contains_text(text, " not "):
            return True
        if self._contains_text(text, " in "):
            return True
        if self._contains_text(text, " is "):
            return True
        if self._contains_text(text, "[:") or self._contains_text(text, "[-") or self._contains_text(text, "[0:"):
            return True
        return False

    def _render_set_literal_repr(self, text: str) -> str:
        """`{\"a\", ...}` 形式の repr を `set<str>{...}` へ変換する。"""
        t = self._trim_ws(text)
        if len(t) < 2 or not t.startswith("{") or not t.endswith("}"):
            return ""
        inner = self._trim_ws(t[1:-1])
        if inner == "":
            return "set<str>{}"
        items = split_top_level_csv(inner)
        out_items: list[str] = []
        for item in items:
            token = self._trim_ws(item)
            if len(token) >= 2 and token.startswith('"') and token.endswith('"'):
                out_items.append(cpp_string_lit(token[1:-1]))
                continue
            if len(token) >= 2 and token.startswith("'") and token.endswith("'"):
                out_items.append(cpp_string_lit(token[1:-1]))
                continue
            return ""
        return f"set<str>{{{join_str_list(', ', out_items)}}}"

    def _render_repr_expr(self, rep: str) -> str:
        """repr 生文字列を最小限 C++ 式へ補正する。"""
        t = self._trim_ws(rep)
        if t == "":
            return ""

        or_parts = self._split_top_level_infix_text(t, " or ")
        if len(or_parts) >= 2:
            rendered: list[str] = []
            for p in or_parts:
                c = self._render_repr_expr(p)
                if c != "":
                    rendered.append(c)
                else:
                    rendered.append(self._trim_ws(p))
            wrapped = [f"({c})" for c in rendered]
            return join_str_list(" || ", wrapped)

        and_parts = self._split_top_level_infix_text(t, " and ")
        if len(and_parts) >= 2:
            rendered: list[str] = []
            for p in and_parts:
                c = self._render_repr_expr(p)
                if c != "":
                    rendered.append(c)
                else:
                    rendered.append(self._trim_ws(p))
            wrapped = [f"({c})" for c in rendered]
            return join_str_list(" && ", wrapped)

        if t.startswith("not "):
            inner = self._trim_ws(t[4:])
            inner_cpp = self._render_repr_expr(inner)
            inner_cpp = inner_cpp if inner_cpp != "" else inner
            return f"!({inner_cpp})"

        not_in_parts = self._split_top_level_infix_text(t, " not in ")
        if len(not_in_parts) == 2:
            lhs = not_in_parts[0]
            rhs = not_in_parts[1]
            lhs_cpp = self._render_repr_expr(lhs)
            lhs_cpp = lhs_cpp if lhs_cpp != "" else self._trim_ws(lhs)
            rhs_cpp = self._render_repr_expr(rhs)
            rhs_cpp = rhs_cpp if rhs_cpp != "" else self._trim_ws(rhs)
            rhs_set = self._render_set_literal_repr(rhs_cpp)
            if rhs_set != "":
                rhs_cpp = rhs_set
            return f"!py_contains({rhs_cpp}, {lhs_cpp})"

        in_parts = self._split_top_level_infix_text(t, " in ")
        if len(in_parts) == 2:
            lhs = in_parts[0]
            rhs = in_parts[1]
            lhs_cpp = self._render_repr_expr(lhs)
            lhs_cpp = lhs_cpp if lhs_cpp != "" else self._trim_ws(lhs)
            rhs_cpp = self._render_repr_expr(rhs)
            rhs_cpp = rhs_cpp if rhs_cpp != "" else self._trim_ws(rhs)
            rhs_set = self._render_set_literal_repr(rhs_cpp)
            if rhs_set != "":
                rhs_cpp = rhs_set
            return f"py_contains({rhs_cpp}, {lhs_cpp})"

        for sep in [" <= ", " >= ", " < ", " > ", " == ", " != "]:
            cmp_parts = self._split_top_level_infix_text(t, sep)
            if len(cmp_parts) >= 3:
                op = self._trim_ws(sep)
                cmp_terms: list[str] = []
                for part in cmp_parts:
                    p_cpp = self._render_repr_expr(part)
                    p_cpp = p_cpp if p_cpp != "" else self._trim_ws(part)
                    cmp_terms.append(p_cpp)
                pair_parts: list[str] = []
                prev_term = ""
                has_prev = False
                for term in cmp_terms:
                    if has_prev:
                        pair_parts.append(f"{prev_term} {op} {term}")
                    prev_term = term
                    has_prev = True
                if len(pair_parts) > 0:
                    wrapped = [f"({x})" for x in pair_parts]
                    return join_str_list(" && ", wrapped)

        fn_name, fn_args, call_ok = self._split_call_repr(t)
        if call_ok:
            if fn_name == "len" and len(fn_args) == 1:
                arg0 = self._render_repr_expr(fn_args[0])
                arg0 = arg0 if arg0 != "" else self._trim_ws(fn_args[0])
                return f"py_len({arg0})"
            if fn_name == "isinstance" and len(fn_args) == 2:
                arg0 = self._render_repr_expr(fn_args[0])
                arg0 = arg0 if arg0 != "" else self._trim_ws(fn_args[0])
                ty = self._trim_ws(fn_args[1])
                type_id_expr = self._render_type_id_operand_expr({"kind": "Name", "id": ty})
                if type_id_expr != "":
                    return f"py_isinstance({arg0}, {type_id_expr})"

        if t.endswith("]"):
            p: int64 = t.find("[")
            if p > 0:
                base = self._trim_ws(t[:p])
                body = self._trim_ws(t[p + 1 : -1])
                lo, hi, has_colon = split_infix_once(body, ":")
                if has_colon:
                    base_cpp = self._render_repr_expr(base)
                    base_cpp = base_cpp if base_cpp != "" else base
                    lo_cpp = self._render_repr_expr(lo)
                    lo_cpp = lo_cpp if lo_cpp != "" else self._trim_ws(lo)
                    hi_cpp = self._render_repr_expr(hi)
                    hi_cpp = hi_cpp if hi_cpp != "" else self._trim_ws(hi)
                    lo_cpp = lo_cpp if lo_cpp != "" else "0"
                    hi_cpp = hi_cpp if hi_cpp != "" else f"py_len({base_cpp})"
                    return f"py_slice({base_cpp}, {lo_cpp}, {hi_cpp})"
        out = t
        out = self._replace_all_text(out, " is not None", " != ::std::nullopt")
        out = self._replace_all_text(out, " is None", " == ::std::nullopt")
        out = self._replace_all_text(out, " is True", " == true")
        out = self._replace_all_text(out, " is False", " == false")
        out = self._replace_all_text(out, "self.", "this->")
        return out

    def _render_subscript_expr(self, expr: dict[str, Any]) -> str:
        """Subscript/Slice 式を C++ 式へ変換する。"""
        val = self.render_expr(expr.get("value"))
        val_ty0 = self.get_expr_type(expr.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        if self.any_dict_get_str(expr, "lowered_kind", "") == "SliceExpr":
            lo = self.render_expr(expr.get("lower")) if expr.get("lower") is not None else "0"
            up = self.render_expr(expr.get("upper")) if expr.get("upper") is not None else f"py_len({val})"
            return f"py_slice({val}, {lo}, {up})"
        sl: object = expr.get("slice")
        sl_node = self.any_to_dict_or_empty(sl)
        if len(sl_node) > 0 and self._node_kind_from_dict(sl_node) == "Slice":
            lo = self.render_expr(sl_node.get("lower")) if sl_node.get("lower") is not None else "0"
            up = self.render_expr(sl_node.get("upper")) if sl_node.get("upper") is not None else f"py_len({val})"
            return f"py_slice({val}, {lo}, {up})"
        idx = self.render_expr(sl)
        idx_ty0 = self.get_expr_type(sl)
        idx_ty = idx_ty0 if isinstance(idx_ty0, str) else ""
        idx_node = self.any_to_dict_or_empty(sl)
        idx_is_str_key = idx_ty == "str" or (
            self._node_kind_from_dict(idx_node) == "Constant" and isinstance(idx_node.get("value"), str)
        )
        idx_const = self._const_int_literal(sl)
        idx_is_int = idx_const is not None or idx_ty in {
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
        }
        if val_ty.startswith("dict["):
            idx = self._coerce_dict_key_expr(expr.get("value"), idx, sl)
            return f"py_dict_get({val}, {idx})"
        if (val_ty in {"", "unknown"} or self.is_any_like_type(val_ty)) and idx_is_str_key:
            return f"py_dict_get({val}, {idx})"
        if (val_ty in {"", "unknown"} or self.is_any_like_type(val_ty)) and idx_is_int:
            return f"py_at({val}, py_to_int64({idx}))"
        if val_ty.startswith("tuple[") and val_ty.endswith("]"):
            parts = self.split_generic(val_ty[6:-1])
            if idx_const is None:
                return f"py_at({val}, py_to_int64({idx}))"
            n_parts = len(parts)
            idx_norm = int(idx_const)
            if idx_norm < 0:
                idx_norm += n_parts
            if idx_norm < 0 or idx_norm >= n_parts:
                raise RuntimeError("tuple index out of range in EAST -> C++ lowering")
            return f"::std::get<{idx_norm}>({val})"
        if self.is_indexable_sequence_type(val_ty):
            idx_t0 = self.get_expr_type(sl)
            idx_t = idx_t0 if isinstance(idx_t0, str) else ""
            if self.is_any_like_type(idx_t):
                idx = f"py_to_int64({idx})"
            return self._render_sequence_index(val, idx, sl)
        return f"{val}[{idx}]"

    def _render_name_expr(self, expr_d: dict[str, Any]) -> str:
        """Name ノードを C++ 式へ変換する。"""
        name_txt = self.any_dict_get_str(expr_d, "id", "")
        if name_txt != "":
            rep_like = self._render_repr_expr(name_txt)
            if rep_like != "" and rep_like != name_txt:
                return rep_like
        return self.render_name_expr_common(
            expr_d,
            self.reserved_words,
            self.rename_prefix,
            self.renamed_symbols,
            "_",
            rewrite_self=self.current_class_name is not None,
            self_is_declared=self.is_declared("self"),
            self_rendered="*this",
        )

    def _render_constant_expr(self, expr: Any, expr_d: dict[str, Any]) -> str:
        """Constant ノードを C++ リテラル式へ変換する。"""
        return self.render_constant_expr_common(
            expr,
            expr_d,
            none_non_any_literal="::std::nullopt",
            none_any_literal="object{}",
            bytes_ctor_name="bytes",
            bytes_lit_fn_name="py_bytes_lit",
        )

    def _render_attribute_expr(self, expr_d: dict[str, Any]) -> str:
        """Attribute ノードを C++ 式へ変換する。

        NOTE:
        `CodeEmitter.render_attribute_expr_common` は内部で `render_expr(...)` を呼ぶ。
        selfhost 生成 C++ では基底メソッド内呼び出しが静的束縛されるため、
        基底 `render_expr`（空文字）へ落ちて `.<attr>` 化する。
        CppEmitter 側で実装して `CppEmitter.render_expr` 経路を維持する。
        """
        owner_t = self.get_expr_type(expr_d.get("value"))
        if self.is_forbidden_object_receiver_type(owner_t):
            raise RuntimeError(
                "object receiver method call / attribute access is forbidden by language constraints"
            )
        base_rendered = self.render_expr(expr_d.get("value"))
        base_ctx = self.resolve_attribute_owner_context(expr_d.get("value"), base_rendered)
        base = self.any_dict_get_str(base_ctx, "expr", "")
        base_node = self.any_to_dict_or_empty(base_ctx.get("node"))
        base_kind = self._node_kind_from_dict(base_node)
        attr = self.attr_name(expr_d)
        direct_self_or_class = self.render_attribute_self_or_class_access(
            base,
            attr,
            self.current_class_name,
            self.current_class_static_fields,
            self.class_base,
            self.class_method_names,
        )
        if direct_self_or_class != "":
            return direct_self_or_class
        base_module_name = self._normalize_runtime_module_name(
            self.any_dict_get_str(base_ctx, "module", "")
        )
        if base_module_name != "":
            mapped = self._lookup_module_attr_runtime_call(base_module_name, attr)
            ns = self._module_name_to_cpp_namespace(base_module_name)
            direct_module = self.render_attribute_module_access(
                base_module_name,
                attr,
                mapped,
                ns,
            )
            if direct_module != "":
                return direct_module
        if base_kind == "Name":
            base_name = dict_any_get_str(base_node, "id")
            if (
                base_name != ""
                and not self.is_declared(base_name)
                and base_name not in self.import_modules
                and base_name in self.import_symbol_modules
            ):
                raise self._make_missing_symbol_import_error(base_name, attr)
        bt = self.get_expr_type(expr_d.get("value"))
        if bt == "Path" and attr in {"name", "stem", "parent"}:
            return f"{base}.{attr}()"
        if (
            self.current_class_name is not None
            and attr in self.current_class_fields
            and (bt in {"", "unknown"} or self.is_any_like_type(bt))
        ):
            ctx = f"{self.current_class_name}.{attr}"
            return f"obj_to_rc_or_raise<{self.current_class_name}>({base}, \"{ctx}\")->{attr}"
        if bt in self.ref_classes:
            return f"{base}->{attr}"
        return f"{base}.{attr}"

    def _render_joinedstr_expr(self, expr_d: dict[str, Any]) -> str:
        """JoinedStr（f-string）ノードを C++ の文字列連結式へ変換する。"""
        if self.any_dict_get_str(expr_d, "lowered_kind", "") == "Concat":
            parts: list[str] = []
            for p in self._dict_stmt_list(expr_d.get("concat_parts")):
                if self._node_kind_from_dict(p) == "literal":
                    parts.append(cpp_string_lit(self.any_dict_get_str(p, "value", "")))
                elif self._node_kind_from_dict(p) == "expr":
                    val: object = p.get("value")
                    if val is None:
                        parts.append('""')
                    else:
                        vtxt = self.render_expr(val)
                        vty = self.get_expr_type(val)
                        if vty == "str":
                            parts.append(vtxt)
                        else:
                            parts.append(self.render_to_string(val))
            if len(parts) == 0:
                return '""'
            return join_str_list(" + ", parts)
        parts: list[str] = []
        for p in self._dict_stmt_list(expr_d.get("values")):
            pk = self._node_kind_from_dict(p)
            if pk == "Constant":
                parts.append(cpp_string_lit(self.any_dict_get_str(p, "value", "")))
            elif pk == "FormattedValue":
                v: object = p.get("value")
                vtxt = self.render_expr(v)
                vty = self.get_expr_type(v)
                if vty == "str":
                    parts.append(vtxt)
                else:
                    parts.append(self.render_to_string(v))
        if len(parts) == 0:
            return '""'
        return join_str_list(" + ", parts)

    def _render_lambda_expr(self, expr_d: dict[str, Any]) -> str:
        """Lambda ノードを C++ のラムダ式へ変換する。"""
        arg_texts: list[str] = []
        for a in self._dict_stmt_list(expr_d.get("args")):
            nm = self.any_to_str(a.get("arg")).strip()
            if nm != "":
                default_node = a.get("default")
                param_t = "auto"
                ann_t = self.any_to_str(a.get("resolved_type")).strip()
                if isinstance(default_node, dict):
                    default_t = self.get_expr_type(default_node)
                    if default_t in {"", "unknown"}:
                        default_t = ann_t
                    if default_t not in {"", "unknown", "Any", "object"}:
                        param_t = self._cpp_type_text(default_t)
                elif ann_t not in {"", "unknown", "Any", "object"}:
                    param_t = self._cpp_type_text(ann_t)
                arg_txt = f"{param_t} {nm}"
                if isinstance(default_node, dict):
                    arg_txt += f" = {self.render_expr(default_node)}"
                arg_texts.append(arg_txt)
        body_expr = self.render_expr(expr_d.get("body"))
        return f"[&]({join_str_list(', ', arg_texts)}) {{ return {body_expr}; }}"

    def render_expr(self, expr: Any) -> str:
        """式ノードを C++ の式文字列へ変換する中核処理。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "/* none */"
        kind = self._node_kind_from_dict(expr_d)
        hook_kind = self.hook_on_render_expr_kind(kind, expr_d)
        if hook_kind != "":
            return hook_kind

        if kind == "Name":
            return self._render_name_expr(expr_d)
        if kind == "Constant":
            return self._render_constant_expr(expr, expr_d)
        if kind == "Attribute":
            return self._render_attribute_expr(expr_d)
        if kind == "Call":
            call_parts: dict[str, Any] = self._prepare_call_parts(expr_d)
            call_ctx = self.unpack_prepared_call_parts(call_parts)
            fn = self.any_to_dict_or_empty(call_ctx.get("fn"))
            fn_name = self.any_to_str(call_ctx.get("fn_name"))
            arg_nodes = self.any_to_list(call_ctx.get("arg_nodes"))
            args = self.any_to_str_list(call_ctx.get("args"))
            kw = self.any_to_str_dict_or_empty(call_ctx.get("kw"))
            kw_values = self.any_to_str_list(call_ctx.get("kw_values"))
            kw_nodes = self.any_to_list(call_ctx.get("kw_nodes"))
            first_arg: object = call_ctx.get("first_arg")
            return self._render_call_expr_from_context(
                expr_d,
                fn,
                fn_name,
                args,
                kw,
                arg_nodes,
                kw_values,
                kw_nodes,
                first_arg,
            )
        if kind == "Box":
            value_node = expr_d.get("value")
            value_expr = self.render_expr(value_node)
            return self._box_expr_for_any(value_expr, value_node)
        if kind == "Unbox":
            value_expr = self.render_expr(expr_d.get("value"))
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
            if target_t == "" or target_t == "unknown":
                target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
            if target_t == "" or target_t == "unknown" or self.is_any_like_type(target_t):
                return value_expr
            ctx = self.any_dict_get_str(expr_d, "ctx", "east3_unbox")
            return self._coerce_any_expr_to_target(value_expr, target_t, ctx)
        if kind == "CastOrRaise":
            value_expr = self.render_expr(expr_d.get("value"))
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
            if target_t == "" or target_t == "unknown":
                target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
            if target_t == "" or target_t == "unknown":
                return value_expr
            if self.is_any_like_type(target_t):
                return self._box_expr_for_any(value_expr, expr_d.get("value"))
            return self._coerce_any_expr_to_target(value_expr, target_t, "east3_cast_or_raise")
        if kind == "ObjBool":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_to_bool({value_expr})"
        if kind == "ObjLen":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_len({value_expr})"
        if kind == "ObjStr":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_to_string({value_expr})"
        if kind == "ObjIterInit":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_iter_or_raise({value_expr})"
        if kind == "ObjIterNext":
            iter_expr = self.render_expr(expr_d.get("iter"))
            return f"py_next_or_stop({iter_expr})"
        if kind == "ObjTypeId":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_runtime_type_id({value_expr})"
        if kind == "ListAppend":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            owner_t0 = self.get_expr_type(owner_node)
            owner_t = owner_t0 if isinstance(owner_t0, str) else ""
            owner_types: list[str] = [owner_t]
            if self._contains_text(owner_t, "|"):
                owner_types = self.split_union(owner_t)
            append_rendered = self._render_append_call_object_method(owner_types, owner_expr, [value_expr], [value_node])
            if append_rendered is not None:
                return append_rendered
            return f"{owner_expr}.append({value_expr})"
        if kind == "ListExtend":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.insert({owner_expr}.end(), {value_expr}.begin(), {value_expr}.end())"
        if kind == "SetAdd":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.insert({value_expr})"
        if kind == "ListPop":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            has_index = self.any_dict_has(expr_d, "index")
            if not has_index:
                return f"{owner_expr}.pop()"
            index_node = expr_d.get("index")
            index_expr = self.render_expr(index_node)
            if index_expr in {"", "/* none */"}:
                return f"{owner_expr}.pop()"
            return f"{owner_expr}.pop({index_expr})"
        if kind == "ListClear":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"{owner_expr}.clear()"
        if kind == "ListReverse":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"::std::reverse({owner_expr}.begin(), {owner_expr}.end())"
        if kind == "ListSort":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"::std::sort({owner_expr}.begin(), {owner_expr}.end())"
        if kind == "SetErase":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.erase({value_expr})"
        if kind == "SetClear":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"{owner_expr}.clear()"
        if kind == "DictItems":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return owner_expr
        if kind == "DictKeys":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"py_dict_keys({owner_expr})"
        if kind == "DictValues":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"py_dict_values({owner_expr})"
        if kind == "DictPop":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            return f"{owner_expr}.pop({key_expr})"
        if kind == "DictGetMaybe":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            return f"py_dict_get_maybe({owner_expr}, {key_expr})"
        if kind == "DictPopDefault":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            default_node = expr_d.get("default")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            default_expr = self.render_expr(default_node)
            val_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "value_type", "Any"))
            if default_expr in {"::std::nullopt", "std::nullopt"} and not self.is_any_like_type(val_t) and val_t != "None":
                default_expr = self._cpp_type_text(val_t) + "()"
            return f"({owner_expr}.contains({key_expr}) ? {owner_expr}.pop({key_expr}) : {default_expr})"
        if kind == "DictGetDefault":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            default_node = expr_d.get("default")
            out_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "out_type", ""))
            default_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "default_type", ""))
            owner_value_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "owner_value_type", ""))
            objectish_owner = self.any_to_bool(expr_d.get("objectish_owner"))
            owner_optional_object_dict = self.any_to_bool(expr_d.get("owner_optional_object_dict"))
            return self._render_dict_get_default_expr(
                owner_node,
                key_node,
                default_node,
                out_t,
                default_t,
                owner_value_t,
                objectish_owner,
                owner_optional_object_dict,
            )
        if kind == "StrStripOp":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            mode = self.any_dict_get_str(expr_d, "mode", "strip")
            has_chars = self.any_dict_has(expr_d, "chars")
            if has_chars:
                chars_expr = self.render_expr(expr_d.get("chars"))
                if mode == "rstrip":
                    return f"{owner_expr}.rstrip({chars_expr})"
                if mode == "lstrip":
                    return f"{owner_expr}.lstrip({chars_expr})"
                return f"{owner_expr}.strip({chars_expr})"
            if mode == "rstrip":
                return f"py_rstrip({owner_expr})"
            if mode == "lstrip":
                return f"py_lstrip({owner_expr})"
            return f"py_strip({owner_expr})"
        if kind == "IsSubtype":
            actual_type_id_expr = self.render_expr(expr_d.get("actual_type_id"))
            expected_type_id_expr = self.render_expr(expr_d.get("expected_type_id"))
            if actual_type_id_expr == "" or expected_type_id_expr == "":
                return "false"
            return f"py_is_subtype({actual_type_id_expr}, {expected_type_id_expr})"
        if kind == "IsSubclass":
            actual_type_id_expr = self._render_type_id_operand_expr(expr_d.get("actual_type_id"))
            expected_type_id_expr = self._render_type_id_operand_expr(expr_d.get("expected_type_id"))
            if actual_type_id_expr == "" or expected_type_id_expr == "":
                return "false"
            return f"py_issubclass({actual_type_id_expr}, {expected_type_id_expr})"
        if kind == "IsInstance":
            value_expr = self.render_expr(expr_d.get("value"))
            expected_type_id_expr = self._render_type_id_operand_expr(expr_d.get("expected_type_id"))
            if expected_type_id_expr == "":
                return "false"
            return f"py_isinstance({value_expr}, {expected_type_id_expr})"
        op_rendered = self._render_operator_family_expr(kind, expr, expr_d)
        if op_rendered != "":
            return op_rendered
        if kind == "List":
            t = self.cpp_type(expr_d.get("resolved_type"))
            elem_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("list[") and rt.endswith("]"):
                elem_t = rt[5:-1].strip()
            parts: list[str] = []
            ctor_elem = ""
            ctor_mixed = False
            elements = self.any_to_list(expr_d.get("elements"))
            for e in elements:
                rv = self.render_expr(e)
                brace_pos = rv.find("{")
                if brace_pos > 0:
                    cand = rv[:brace_pos].strip()
                    if cand.startswith("dict<") or cand.startswith("list<") or cand.startswith("set<"):
                        first_ctor_elem = ctor_elem == ""
                        ctor_elem = cand if first_ctor_elem else ctor_elem
                        if not first_ctor_elem and ctor_elem != cand:
                            ctor_mixed = True
                if self.is_any_like_type(elem_t):
                    rv = self._box_expr_for_any(rv, e)
                parts.append(rv)
            if t.startswith("list<") and ctor_elem != "" and not ctor_mixed:
                expect_t = f"list<{ctor_elem}>"
                if t != expect_t:
                    t = expect_t
            sep = ", "
            items = sep.join(parts)
            return f"{t}{{{items}}}"
        if kind == "Tuple":
            elements = self.any_to_list(expr_d.get("elements"))
            elem_types: list[str] = []
            rt0 = self.get_expr_type(expr)
            rt = rt0 if isinstance(rt0, str) else ""
            if rt.startswith("tuple[") and rt.endswith("]"):
                elem_types = self.split_generic(rt[6:-1])
            rendered_items: list[str] = []
            for i, e in enumerate(elements):
                item = self.render_expr(e)
                target_t = elem_types[i] if i < len(elem_types) else ""
                src_t0 = self.get_expr_type(e)
                src_t = src_t0 if isinstance(src_t0, str) else ""
                if target_t != "" and not self.is_any_like_type(target_t) and src_t != target_t:
                    item = self.apply_cast(item, target_t)
                rendered_items.append(item)
            sep = ", "
            items = sep.join(rendered_items)
            return f"::std::make_tuple({items})"
        if kind == "Set":
            t = self.cpp_type(expr_d.get("resolved_type"))
            elements = self.any_to_list(expr_d.get("elements"))
            rendered: list[str] = []
            for e in elements:
                rendered.append(self.render_expr(e))
            sep = ", "
            items = sep.join(rendered)
            return f"{t}{{{items}}}"
        if kind == "Dict":
            t = self.cpp_type(expr_d.get("resolved_type"))
            key_t = ""
            val_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("dict[") and rt.endswith("]"):
                inner = self.split_generic(rt[5:-1])
                if len(inner) == 2:
                    key_t = inner[0]
                    val_t = inner[1]
            entries = self._dict_stmt_list(expr_d.get("entries"))
            if len(entries) == 0:
                keys_raw = self.any_to_list(expr_d.get("keys"))
                vals_raw = self.any_to_list(expr_d.get("values"))
                n = len(keys_raw)
                if len(vals_raw) < n:
                    n = len(vals_raw)
                for i in range(n):
                    entries.append({"key": keys_raw[i], "value": vals_raw[i]})
            if len(entries) == 0:
                return f"{t}{{}}"
            # resolved_type が空/不正確な場合は key/value ノードから最低限を再推定する。
            inferred_key = ""
            inferred_val = ""
            key_mixed = False
            val_mixed = False
            for kv in entries:
                key_node: Any = kv.get("key")
                val_node: Any = kv.get("value")
                kt0 = self.get_expr_type(key_node)
                kt = kt0 if isinstance(kt0, str) else ""
                if kt not in {"", "unknown"}:
                    first_inferred_key = inferred_key == ""
                    inferred_key = kt if first_inferred_key else inferred_key
                    if not first_inferred_key and kt != inferred_key:
                        key_mixed = True
                vt0 = self.get_expr_type(val_node)
                vt = vt0 if isinstance(vt0, str) else ""
                if vt not in {"", "unknown"}:
                    first_inferred_val = inferred_val == ""
                    inferred_val = vt if first_inferred_val else inferred_val
                    if not first_inferred_val and vt != inferred_val:
                        val_mixed = True
            if key_t in {"", "unknown"} and inferred_key != "" and not key_mixed:
                key_t = inferred_key
            if val_t in {"", "unknown"} and inferred_val != "" and not val_mixed:
                val_t = inferred_val
            if val_mixed:
                key_pick = key_t if key_t not in {"", "unknown"} and not key_mixed else "str"
                if key_pick == "str" and inferred_key != "" and not key_mixed:
                    key_pick = inferred_key
                t = f"dict<{self._cpp_type_text(key_pick)}, object>"
                val_t = "Any"
            elif t in {"auto", "dict<str, str>", "dict<str, object>"}:
                key_pick = key_t if key_t not in {"", "unknown"} and not key_mixed else "str"
                val_pick = val_t if val_t not in {"", "unknown"} else (inferred_val if inferred_val != "" else "str")
                val_is_any_like = self.is_any_like_type(val_pick)
                t = (
                    f"dict<{self._cpp_type_text(key_pick)}, object>"
                    if val_is_any_like
                    else f"dict<{self._cpp_type_text(key_pick)}, {self._cpp_type_text(val_pick)}>"
                )
                val_t = "Any" if val_is_any_like else val_t
            items: list[str] = []
            for kv in entries:
                key_node: Any = kv.get("key")
                val_node: Any = kv.get("value")
                k = self.render_expr(key_node)
                v = self.render_expr(val_node)
                if self.is_any_like_type(key_t):
                    k = self._box_expr_for_any(k, key_node)
                if self.is_any_like_type(val_t):
                    v = self._box_expr_for_any(v, val_node)
                items.append(f"{{{k}, {v}}}")
            return f"{t}{{{join_str_list(', ', items)}}}"
        if kind == "Subscript":
            return self._render_subscript_expr(expr)
        if kind == "JoinedStr":
            return self._render_joinedstr_expr(expr_d)
        if kind == "Lambda":
            return self._render_lambda_expr(expr_d)
        if kind == "ListComp":
            gens = self.any_to_list(expr_d.get("generators"))
            if len(gens) != 1:
                return "{}"
            g_obj = gens[0]
            g = self.any_to_dict_or_empty(g_obj)
            g_target_raw: object = g.get("target")
            g_target = self.any_to_dict_or_empty(g_target_raw)
            tgt = self.render_expr(g_target_raw)
            it = self.render_expr(g.get("iter"))
            elt = self.render_expr(expr_d.get("elt"))
            out_t = self.cpp_type(expr_d.get("resolved_type"))
            elt_t0 = self.get_expr_type(expr_d.get("elt"))
            elt_t = elt_t0 if isinstance(elt_t0, str) else ""
            expected_out_t = ""
            if elt_t != "" and elt_t != "unknown":
                expected_out_t = self._cpp_type_text(f"list[{elt_t}]")
            out_is_dynamic = out_t == "list<object>" or out_t == "object" or out_t == "auto"
            if out_is_dynamic:
                if elt_t != "" and elt_t != "unknown":
                    out_t = self._cpp_type_text(f"list[{elt_t}]")
            elif expected_out_t != "" and out_t != expected_out_t:
                out_t = expected_out_t
            brace_pos = elt.find("{")
            if brace_pos > 0:
                elt_ctor = elt[:brace_pos].strip()
                if elt_ctor.startswith("dict<") or elt_ctor.startswith("list<") or elt_ctor.startswith("set<"):
                    out_t = f"list<{elt_ctor}>"
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
            iter_tmp = self.next_tmp("__it")
            rg = self.any_to_dict_or_empty(g.get("iter"))
            if self._node_kind_from_dict(rg) == "RangeExpr":
                start = self.render_expr(rg.get("start"))
                stop = self.render_expr(rg.get("stop"))
                step = self.render_expr(rg.get("step"))
                mode = self.any_to_str(rg.get("range_mode"))
                mode = mode if mode != "" else "dynamic"
                cond = (
                    f"({tgt} < {stop})"
                    if mode == "ascending"
                    else (
                        f"({tgt} > {stop})"
                        if mode == "descending"
                        else f"(({step}) > 0 ? ({tgt} < {stop}) : ({tgt} > {stop}))"
                    )
                )
                lines.append(f"    for (int64 {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
            else:
                if tuple_unpack:
                    lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                    target_elements = self.any_to_list(g_target.get("elements"))
                    for i, e in enumerate(target_elements):
                        e_node = self.any_to_dict_or_empty(e)
                        if self._node_kind_from_dict(e_node) == "Name":
                            nm = self.render_expr(e)
                            lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
                else:
                    lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = self.any_to_list(g.get("ifs"))
            list_elt = elt
            if out_t == "list<object>" and not self.is_boxed_object_expr(list_elt):
                list_elt = self._box_any_target_value(list_elt, expr_d.get("elt"))
            if len(ifs) == 0:
                lines.append(f"        __out.append({list_elt});")
            else:
                cond_parts: list[str] = []
                for c in ifs:
                    c_txt = self.render_expr(c)
                    if c_txt in {"", "true"}:
                        c_node = self.any_to_dict_or_empty(c)
                        c_rep = self.any_dict_get_str(c_node, "repr", "")
                        if c_rep != "":
                            c_txt = c_rep
                    cond_parts.append(c_txt if c_txt != "" else "true")
                cond: str = join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out.append({list_elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            sep = " "
            return sep.join(lines)
        if kind == "SetComp":
            gens = self.any_to_list(expr_d.get("generators"))
            if len(gens) != 1:
                return "{}"
            g_obj = gens[0]
            g = self.any_to_dict_or_empty(g_obj)
            g_target_raw: object = g.get("target")
            g_target = self.any_to_dict_or_empty(g_target_raw)
            tgt = self.render_expr(g_target_raw)
            it = self.render_expr(g.get("iter"))
            elt = self.render_expr(expr_d.get("elt"))
            out_t = self.cpp_type(expr_d.get("resolved_type"))
            elt_t0 = self.get_expr_type(expr_d.get("elt"))
            elt_t = elt_t0 if isinstance(elt_t0, str) else ""
            expected_out_t = ""
            if elt_t != "" and elt_t != "unknown":
                expected_out_t = self._cpp_type_text(f"set[{elt_t}]")
            out_is_dynamic = out_t == "set<object>" or out_t == "object" or out_t == "auto"
            if out_is_dynamic:
                if elt_t != "" and elt_t != "unknown":
                    out_t = self._cpp_type_text(f"set[{elt_t}]")
            elif expected_out_t != "" and out_t != expected_out_t:
                out_t = expected_out_t
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                target_elements = self.any_to_list(g_target.get("elements"))
                for i, e in enumerate(target_elements):
                    e_node = self.any_to_dict_or_empty(e)
                    if self._node_kind_from_dict(e_node) == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = self.any_to_list(g.get("ifs"))
            set_elt = elt
            if out_t == "set<object>" and not self.is_boxed_object_expr(set_elt):
                set_elt = self._box_any_target_value(set_elt, expr_d.get("elt"))
            if len(ifs) == 0:
                lines.append(f"        __out.insert({set_elt});")
            else:
                cond_parts: list[str] = []
                for c in ifs:
                    c_txt = self.render_expr(c)
                    if c_txt in {"", "true"}:
                        c_node = self.any_to_dict_or_empty(c)
                        c_rep = self.any_dict_get_str(c_node, "repr", "")
                        if c_rep != "":
                            c_txt = c_rep
                    cond_parts.append(c_txt if c_txt != "" else "true")
                cond: str = join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out.insert({set_elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            sep = " "
            return sep.join(lines)
        if kind == "DictComp":
            gens = self.any_to_list(expr_d.get("generators"))
            if len(gens) != 1:
                return "{}"
            g_obj = gens[0]
            g = self.any_to_dict_or_empty(g_obj)
            g_target_raw: object = g.get("target")
            g_target = self.any_to_dict_or_empty(g_target_raw)
            tgt = self.render_expr(g_target_raw)
            it = self.render_expr(g.get("iter"))
            key = self.render_expr(expr_d.get("key"))
            val = self.render_expr(expr_d.get("value"))
            out_t = self.cpp_type(expr_d.get("resolved_type"))
            key_t0 = self.get_expr_type(expr_d.get("key"))
            val_t0 = self.get_expr_type(expr_d.get("value"))
            key_t = key_t0 if isinstance(key_t0, str) else ""
            val_t = val_t0 if isinstance(val_t0, str) else ""
            expected_out_t = ""
            if key_t != "" and key_t != "unknown" and val_t != "" and val_t != "unknown":
                expected_out_t = self._cpp_type_text(f"dict[{key_t},{val_t}]")
            out_is_dynamic = out_t == "dict<str, object>" or out_t == "object" or out_t == "auto"
            if out_is_dynamic:
                if key_t != "" and key_t != "unknown" and val_t != "" and val_t != "unknown":
                    out_t = self._cpp_type_text(f"dict[{key_t},{val_t}]")
            elif expected_out_t != "" and out_t != expected_out_t:
                out_t = expected_out_t
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                target_elements = self.any_to_list(g_target.get("elements"))
                for i, e in enumerate(target_elements):
                    e_node = self.any_to_dict_or_empty(e)
                    if self._node_kind_from_dict(e_node) == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = self.any_to_list(g.get("ifs"))
            if len(ifs) == 0:
                lines.append(f"        __out[{key}] = {val};")
            else:
                cond_parts: list[str] = []
                for c in ifs:
                    c_txt = self.render_expr(c)
                    if c_txt in {"", "true"}:
                        c_node = self.any_to_dict_or_empty(c)
                        c_rep = self.any_dict_get_str(c_node, "repr", "")
                        if c_rep != "":
                            c_txt = c_rep
                    cond_parts.append(c_txt if c_txt != "" else "true")
                cond: str = join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out[{key}] = {val};")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            sep = " "
            return sep.join(lines)

        rep = self.any_to_str(expr_d.get("repr"))
        if rep != "":
            rep_rendered = self._render_repr_expr(rep)
            if rep_rendered != "":
                return rep_rendered
            return rep
        return f"/* unsupported expr: {kind} */"

    def emit_bridge_comment(self, expr: dict[str, Any] | None) -> None:
        """ランタイムブリッジ呼び出しの補助コメントを必要時に付与する。"""
        _ = expr
        return

    def cpp_type(self, east_type: Any) -> str:
        """EAST 型名を C++ 型名へマッピングする。"""
        east_type_txt = self.any_to_str(east_type)
        if east_type_txt == "" and east_type is not None:
            ttxt = str(east_type)
            if ttxt != "" and ttxt not in {"{}", "[]"}:
                east_type_txt = ttxt
        east_type_txt = self.normalize_type_name(east_type_txt)
        return self._cpp_type_text(east_type_txt)

    def _cpp_type_text(self, east_type: str) -> str:
        """正規化済み型名（str）を C++ 型名へマッピングする。"""
        if east_type == "":
            return "auto"
        if east_type in self.ref_classes:
            return f"rc<{east_type}>"
        if east_type in self.class_names:
            return east_type
        mapped = ""
        if east_type in self.type_map:
            mapped = self.type_map[east_type]
        if mapped != "":
            return mapped
        if east_type in {"Any", "object"}:
            return "object"
        if east_type.find("|") != -1:
            parts = self.split_union(east_type)
            if len(parts) >= 2:
                non_none: list[str] = []
                has_none = False
                for p in parts:
                    if p == "None":
                        has_none = True
                        continue
                    if p not in non_none:
                        non_none.append(p)
                if len(non_none) >= 1:
                    only_bytes = True
                    for p in non_none:
                        if p not in {"bytes", "bytearray"}:
                            only_bytes = False
                            break
                    if only_bytes:
                        return "bytes"
                has_any_like = False
                for p in non_none:
                    if self.is_any_like_type(p):
                        has_any_like = True
                        break
                if has_any_like:
                    return "object"
                if has_none and len(non_none) == 1:
                    return f"::std::optional<{self._cpp_type_text(non_none[0])}>"
                if (not has_none) and len(non_none) == 1:
                    return self._cpp_type_text(non_none[0])
                return "object"
        if east_type == "None":
            return "void"
        if east_type == "PyFile":
            return "pytra::runtime::cpp::base::PyFile"
        if east_type.startswith("list[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 1:
                if inner[0] == "None":
                    return "list<object>"
                if inner[0] == "uint8":
                    return "bytearray"
                if self.is_any_like_type(inner[0]):
                    return "list<object>"
                if inner[0] == "unknown":
                    return "list<object>"
                return f"list<{self._cpp_type_text(inner[0])}>"
        if east_type.startswith("set[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[4:-1])
            if len(inner) == 1:
                if inner[0] == "None":
                    return "set<object>"
                if inner[0] == "unknown":
                    return "set<str>"
                return f"set<{self._cpp_type_text(inner[0])}>"
        if east_type.startswith("dict[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 2:
                if inner[1] == "None":
                    key_t = inner[0] if inner[0] not in {"", "unknown"} else "str"
                    return f"dict<{self._cpp_type_text(key_t)}, object>"
                if self.is_any_like_type(inner[1]):
                    return f"dict<{self._cpp_type_text(inner[0] if inner[0] != 'unknown' else 'str')}, object>"
                if inner[0] == "unknown" and inner[1] == "unknown":
                    return "dict<str, object>"
                if inner[0] == "unknown":
                    return f"dict<str, {self._cpp_type_text(inner[1])}>"
                if inner[1] == "unknown":
                    return f"dict<{self._cpp_type_text(inner[0])}, object>"
                return f"dict<{self._cpp_type_text(inner[0])}, {self._cpp_type_text(inner[1])}>"
        if east_type.startswith("tuple[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[6:-1])
            inner_cpp: list[str] = []
            for x in inner:
                inner_cpp.append(self._cpp_type_text(x))
            sep = ", "
            return "::std::tuple<" + sep.join(inner_cpp) + ">"
        if east_type == "unknown":
            return "object"
        if east_type.startswith("callable["):
            return "auto"
        if east_type == "callable":
            return "auto"
        if east_type == "module":
            return "auto"
        if east_type.find(".") >= 0:
            dot = east_type.rfind(".")
            owner = east_type[:dot]
            leaf = east_type[dot + 1 :]
            if owner != "" and leaf != "":
                mod_name = self._normalize_runtime_module_name(self._resolve_imported_module_name(owner))
                ns = self._module_name_to_cpp_namespace(mod_name)
                looks_like_class = leaf != "" and (leaf[0] >= "A" and leaf[0] <= "Z")
                if ns != "":
                    if looks_like_class:
                        return f"rc<{ns}::{leaf}>"
                    return f"{ns}::{leaf}"
                if owner.startswith("pytra."):
                    owner_ns = "pytra::" + owner[6:].replace(".", "::")
                    if looks_like_class:
                        return f"rc<{owner_ns}::{leaf}>"
                    return owner_ns + "::" + leaf
                owner_ns = owner.replace(".", "::")
                if looks_like_class:
                    return f"rc<{owner_ns}::{leaf}>"
                return owner_ns + "::" + leaf
        return east_type


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "2",
    object_dispatch_mode: str = "",
) -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    east_doc: dict[str, Any]
    if east_stage == "3":
        east3_doc = load_east3_document(
            input_path,
            parser_backend=parser_backend,
            object_dispatch_mode=object_dispatch_mode,
        )
        east_doc = east3_doc if isinstance(east3_doc, dict) else {}
    else:
        east2_doc = load_east_document(input_path, parser_backend)
        east_doc = east2_doc if isinstance(east2_doc, dict) else {}
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
    ) -> str:
    """EAST Module を C++ ソース文字列へ変換する。"""
    return CppEmitter(
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
    ).transpile()


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
    )


def _header_cpp_type_from_east(
    east_t: str,
    ref_classes: set[str],
    class_names: set[str],
) -> str:
    """EAST 型名を runtime header 向け C++ 型名へ変換する。"""
    t: str = east_t.strip()
    if t == "":
        return "object"
    if t in ref_classes:
        return "rc<" + t + ">"
    if t in class_names:
        return t
    prim: dict[str, str] = {
        "int8": "int8",
        "uint8": "uint8",
        "int16": "int16",
        "uint16": "uint16",
        "int32": "int32",
        "uint32": "uint32",
        "int64": "int64",
        "uint64": "uint64",
        "float32": "float32",
        "float64": "float64",
        "bool": "bool",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
        "None": "void",
        "Any": "object",
        "object": "object",
        "unknown": "object",
    }
    if t in prim:
        return prim[t]
    parts_union = split_top_level_union(t)
    if len(parts_union) > 1:
        parts = parts_union
        non_none: list[str] = []
        for part in parts:
            p = part.strip()
            if p != "None":
                non_none.append(p)
        if len(parts) == 2 and len(non_none) == 1:
            return "::std::optional<" + _header_cpp_type_from_east(non_none[0], ref_classes, class_names) + ">"
        folded: list[str] = []
        for part in non_none:
            p = part
            if p == "bytearray":
                p = "bytes"
            if p not in folded:
                folded.append(p)
        if len(folded) == 1:
            only: str = folded[0]
            return _header_cpp_type_from_east(only, ref_classes, class_names)
        return "object"
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        return "list<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        return "set<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("dict[") and t.endswith("]"):
        inner = split_type_args(t[5:-1].strip())
        if len(inner) == 2:
            return "dict<" + _header_cpp_type_from_east(inner[0], ref_classes, class_names) + ", " + _header_cpp_type_from_east(inner[1], ref_classes, class_names) + ">"
        return "dict<str, object>"
    if t.startswith("tuple[") and t.endswith("]"):
        inner = split_type_args(t[6:-1].strip())
        vals: list[str] = []
        for part in inner:
            vals.append(_header_cpp_type_from_east(part, ref_classes, class_names))
        sep = ", "
        return "::std::tuple<" + sep.join(vals) + ">"
    if "." in t:
        ns_t = t.replace(".", "::")
        dot = t.rfind(".")
        leaf = t[dot + 1 :] if dot >= 0 else t
        if leaf != "" and (leaf[0] >= "A" and leaf[0] <= "Z"):
            return "rc<" + ns_t + ">"
        return ns_t
    return t


def _header_guard_from_path(path: str) -> str:
    """ヘッダパスから include guard を生成する。"""
    src = path.replace("\\", "/")
    prefix1 = "src/runtime/cpp/pytra/"
    prefix2 = "runtime/cpp/pytra/"
    if src.startswith(prefix1):
        src = src[len(prefix1) :]
    elif src.startswith(prefix2):
        src = src[len(prefix2) :]
    src = "PYTRA_" + src.upper()
    out_chars: list[str] = []
    for ch in src:
        ok = ((ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9"))
        if ok:
            out_chars.append(ch)
        else:
            out_chars.append("_")
    out = "".join(out_chars).lstrip("_")
    if not out.endswith("_H"):
        out += "_H"
    return out


def _header_allows_none_default(east_t: str) -> bool:
    """ヘッダ既定値で `None`（optional）を許容する型か判定する。"""
    txt = east_t.strip()
    if txt.startswith("optional[") and txt.endswith("]"):
        return True
    if "|" in txt:
        parts = txt.split("|")
        for part in parts:
            if part.strip() == "None":
                return True
    return txt == "None"


def _header_none_default_expr_for_type(east_t: str) -> str:
    """ヘッダ既定値で `None` を型別既定値へ変換する。"""
    txt = east_t.strip()
    if txt in {"", "unknown", "Any", "object"}:
        return "object{}"
    if _header_allows_none_default(txt):
        return "::std::nullopt"
    if txt in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
        return "0"
    if txt in {"float32", "float64"}:
        return "0.0"
    if txt == "bool":
        return "false"
    if txt == "str":
        return "str()"
    if txt == "bytes":
        return "bytes()"
    if txt == "bytearray":
        return "bytearray()"
    if txt == "Path":
        return "Path()"
    cpp_t = _header_cpp_type_from_east(txt, set(), set())
    if cpp_t.startswith("::std::optional<"):
        return "::std::nullopt"
    return cpp_t + "{}"


def _header_render_default_expr(node: dict[str, Any], east_target_t: str) -> str:
    """EAST の既定値ノードを C++ ヘッダ宣言用の式文字列へ変換する。"""
    kind = dict_any_get_str(node, "kind")
    if kind == "Constant":
        val = node.get("value")
        if val is None:
            return _header_none_default_expr_for_type(east_target_t)
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            return str(val)
        if isinstance(val, str):
            return cpp_string_lit(val)
        return ""
    if kind == "Name":
        ident = dict_any_get_str(node, "id")
        if ident == "None":
            return _header_none_default_expr_for_type(east_target_t)
        if ident == "True":
            return "true"
        if ident == "False":
            return "false"
        return ""
    if kind == "Tuple":
        elems = dict_any_get_dict_list(node, "elements")
        if len(elems) == 0:
            return "::std::tuple<>{}"
        parts: list[str] = []
        for e in elems:
            txt = _header_render_default_expr(e, "Any")
            if txt == "":
                return ""
            parts.append(txt)
        if len(parts) == 0:
            return ""
        return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
    _ = east_target_t
    return ""


def build_cpp_header_from_east(
    east_module: dict[str, Any],
    source_path: Path,
    output_path: Path,
    top_namespace: str = "",
) -> str:
    """EAST から最小宣言のみの C++ ヘッダ文字列を生成する。"""
    body = dict_any_get_dict_list(east_module, "body")

    class_lines: list[str] = []
    fn_lines: list[str] = []
    var_lines: list[str] = []
    used_types: set[str] = set()
    seen_classes: set[str] = set()
    class_names: set[str] = set()
    ref_classes: set[str] = set()

    for st in body:
        if dict_any_get_str(st, "kind") == "ClassDef":
            cls_name = dict_any_get_str(st, "name")
            if cls_name != "":
                class_names.add(cls_name)
                hint = dict_any_get_str(st, "class_storage_hint", "ref")
                if hint == "ref":
                    ref_classes.add(cls_name)

    by_value_types = {
        "bool",
        "int8",
        "uint8",
        "int16",
        "uint16",
        "int32",
        "uint32",
        "int64",
        "uint64",
        "float32",
        "float64",
    }

    for st in body:
        kind = dict_any_get_str(st, "kind")
        if kind == "ClassDef":
            cls_name = dict_any_get_str(st, "name")
            if cls_name != "" and cls_name not in seen_classes:
                class_lines.append("struct " + cls_name + ";")
                seen_classes.add(cls_name)
        elif kind == "FunctionDef":
            name = dict_any_get_str(st, "name")
            if name != "":
                ret_t = dict_any_get_str(st, "return_type", "None")
                ret_cpp = _header_cpp_type_from_east(ret_t, ref_classes, class_names)
                used_types.add(ret_cpp)
                arg_types = dict_any_get_dict(st, "arg_types")
                arg_order = dict_any_get_list(st, "arg_order")
                parts: list[str] = []
                for an in arg_order:
                    if not isinstance(an, str):
                        continue
                    at = dict_any_get_str(arg_types, an, "Any")
                    at_cpp = _header_cpp_type_from_east(at, ref_classes, class_names)
                    used_types.add(at_cpp)
                    param_txt = (
                        at_cpp + " " + an if at_cpp in by_value_types else "const " + at_cpp + "& " + an
                    )
                    # NOTE:
                    # 既定引数は `.cpp` 側の定義にのみ付与する。
                    # ヘッダと定義の二重指定によるコンパイルエラーを避けるため、
                    # 宣言側では既定値を埋め込まない。
                    parts.append(param_txt)
                sep = ", "
                fn_lines.append(ret_cpp + " " + name + "(" + sep.join(parts) + ");")
        elif kind in {"Assign", "AnnAssign"}:
            name = stmt_target_name(st)
            if name == "":
                continue
            decl_t = dict_any_get_str(st, "decl_type")
            if decl_t == "" or decl_t == "unknown":
                tgt = dict_any_get_dict(st, "target")
                decl_t = dict_any_get_str(tgt, "resolved_type")
            if decl_t == "" or decl_t == "unknown":
                continue
            cpp_t = _header_cpp_type_from_east(decl_t, ref_classes, class_names)
            used_types.add(cpp_t)
            var_lines.append("extern " + cpp_t + " " + name + ";")

    includes: list[str] = []
    has_std_any = False
    has_std_int = False
    has_std_string = False
    has_std_vector = False
    has_std_tuple = False
    has_std_optional = False
    has_std_umap = False
    has_std_uset = False
    for t in used_types:
        if "::std::any" in t:
            has_std_any = True
        if "::std::int" in t or "::std::uint" in t:
            has_std_int = True
        if "::std::string" in t:
            has_std_string = True
        if "::std::vector" in t:
            has_std_vector = True
        if "::std::tuple" in t:
            has_std_tuple = True
        if "::std::optional" in t:
            has_std_optional = True
        if "::std::unordered_map" in t:
            has_std_umap = True
        if "::std::unordered_set" in t:
            has_std_uset = True
    if has_std_any:
        includes.append("#include <any>")
    if has_std_int:
        includes.append("#include <cstdint>")
    if has_std_string:
        includes.append("#include <string>")
    if has_std_vector:
        includes.append("#include <vector>")
    if has_std_tuple:
        includes.append("#include <tuple>")
    if has_std_optional:
        includes.append("#include <optional>")
    if has_std_umap:
        includes.append("#include <unordered_map>")
    if has_std_uset:
        includes.append("#include <unordered_set>")

    guard = _header_guard_from_path(str(output_path))
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append("// source: " + str(source_path))
    lines.append("// generated-by: src/py2cpp.py")
    lines.append("")
    lines.append("#ifndef " + guard)
    lines.append("#define " + guard)
    lines.append("")
    for include in includes:
        lines.append(include)
    if len(includes) > 0:
        lines.append("")
    ns = top_namespace.strip()
    if ns != "":
        lines.append("namespace " + ns + " {")
        lines.append("")
    for class_line in class_lines:
        lines.append(class_line)
    if len(class_lines) > 0:
        lines.append("")
    for var_line in var_lines:
        lines.append(var_line)
    if len(var_lines) > 0 and len(fn_lines) > 0:
        lines.append("")
    for fn_line in fn_lines:
        lines.append(fn_line)
    if ns != "":
        lines.append("")
        lines.append("}  // namespace " + ns)
    lines.append("")
    lines.append("#endif  // " + guard)
    lines.append("")
    return join_str_list("\n", lines)


def _runtime_module_tail_from_source_path(input_path: Path) -> str:
    """`src/pytra/std|utils|compiler` から runtime tail を返す。"""
    src = str(input_path)
    rel = ""
    std_prefix = "src/pytra/std/"
    utils_prefix = "src/pytra/utils/"
    compiler_prefix = "src/pytra/compiler/"
    built_in_prefix = "src/pytra/built_in/"
    if src.startswith(std_prefix):
        rel = "std/" + src[len(std_prefix) :]
    elif src.startswith(utils_prefix):
        rel = src[len(utils_prefix) :]
    elif src.startswith(compiler_prefix):
        rel = "compiler/" + src[len(compiler_prefix) :]
    elif src.startswith(built_in_prefix):
        rel = "built_in/" + src[len(built_in_prefix) :]
    else:
        return ""
    if rel.endswith(".py"):
        rel = rel[: len(rel) - 3]
    if rel.endswith("/__init__"):
        rel = rel[: len(rel) - 9]
    return rel


def _prepend_generated_cpp_banner(cpp_text: str, source_path: Path) -> str:
    """生成 C++ ソースへ AUTO-GENERATED バナーを先頭付与する。"""
    marker = "// AUTO-GENERATED FILE. DO NOT EDIT."
    if cpp_text.startswith(marker):
        return cpp_text
    lines = [
        marker,
        "// source: " + str(source_path),
        "// generated-by: src/py2cpp.py",
        "",
    ]
    return join_str_list("\n", lines) + cpp_text


def _is_runtime_emit_input_path(input_path: Path) -> bool:
    """`--emit-runtime-cpp` 対象パスか（`src/pytra/std|utils|compiler|built_in` 配下）を返す。"""
    return _runtime_module_tail_from_source_path(input_path) != ""


def _runtime_output_rel_tail(module_tail: str) -> str:
    """module tail（`std/<name>_impl` など）を runtime/cpp 相対パス tail へ写像する。"""
    parts: list[str] = module_tail.split("/")
    if parts:
        leaf = parts[-1]
        if leaf.endswith("_impl"):
            parts[-1] = leaf[: len(leaf) - 5] + "-impl"
    rel = join_str_list("/", parts)
    if rel == "std" or rel.startswith("std/"):
        return rel
    if rel == "compiler" or rel.startswith("compiler/"):
        return rel
    if rel == "built_in" or rel.startswith("built_in/"):
        return rel
    return "utils/" + rel


def _runtime_namespace_for_tail(module_tail: str) -> str:
    """runtime source tail から C++ namespace を導出する。"""
    if module_tail == "":
        return ""
    if module_tail.startswith("std/"):
        rest: str = module_tail[4:].replace("/", "::")
        return "pytra::std::" + rest
    if module_tail == "std":
        return "pytra::std"
    if module_tail.startswith("compiler/"):
        rest = module_tail[9:].replace("/", "::")
        return "pytra::compiler::" + rest
    if module_tail == "compiler":
        return "pytra::compiler"
    if module_tail.startswith("built_in/"):
        return ""
    if module_tail == "built_in":
        return ""
    return "pytra::utils::" + module_tail.replace("/", "::")


def _analyze_import_graph(entry_path: Path) -> dict[str, Any]:
    """ユーザーモジュール依存を解析し、衝突/未解決/循環を返す。"""
    root = Path(path_parent_text(entry_path))
    queue: list[Path] = [entry_path]
    queued: set[str] = {path_key_for_graph(entry_path)}
    visited: set[str] = set()
    visited_order: list[str] = []
    edges: list[str] = []
    edge_seen: set[str] = set()
    missing_modules: list[str] = []
    missing_seen: set[str] = set()
    relative_imports: list[str] = []
    relative_seen: set[str] = set()
    graph_adj: dict[str, list[str]] = {}
    graph_keys: list[str] = []
    key_to_disp: dict[str, str] = {}
    key_to_path: dict[str, Path] = {}
    module_id_map: dict[str, str] = {}

    reserved_conflicts = collect_reserved_import_conflicts(root)

    while queue:
        cur_path = queue.pop(0)
        cur_key = path_key_for_graph(cur_path)
        if cur_key in visited:
            continue
        visited.add(cur_key)
        visited_order.append(cur_key)
        key_to_path[cur_key] = cur_path
        key_to_disp[cur_key] = rel_disp_for_graph(root, cur_path)
        if cur_key not in module_id_map:
            module_id_map[cur_key] = module_name_from_path_for_graph(root, cur_path)
        try:
            east_cur = load_east(cur_path)
        except Exception:
            continue
        mods = collect_import_modules(east_cur)
        if cur_key not in graph_adj:
            graph_adj[cur_key] = []
            graph_keys.append(cur_key)
        cur_disp = key_to_disp[cur_key]
        search_root = Path(path_parent_text(cur_path))
        for mod in mods:
            resolved = resolve_module_name_for_graph(
                mod,
                search_root,
                RUNTIME_STD_SOURCE_ROOT,
                RUNTIME_UTILS_SOURCE_ROOT,
            )
            status = dict_any_get_str(resolved, "status")
            dep_txt = dict_any_get_str(resolved, "path")
            resolved_mod_id = dict_any_get_str(resolved, "module_id")
            if status == "relative":
                rel_item = cur_disp + ": " + mod
                append_unique_non_empty(relative_imports, relative_seen, rel_item)
                continue
            dep_disp = mod
            if status == "user":
                if dep_txt == "":
                    continue
                dep_file = Path(dep_txt)
                dep_key = path_key_for_graph(dep_file)
                dep_disp = rel_disp_for_graph(root, dep_file)
                module_id = resolved_mod_id or mod
                if dep_key not in module_id_map or module_id_map[dep_key] == "":
                    module_id_map[dep_key] = module_id
                graph_adj[cur_key].append(dep_key)
                key_to_path[dep_key] = dep_file
                key_to_disp[dep_key] = dep_disp
                if dep_key not in queued and dep_key not in visited:
                    queued.add(dep_key)
                    queue.append(dep_file)
            elif status == "missing":
                miss = cur_disp + ": " + mod
                append_unique_non_empty(missing_modules, missing_seen, miss)
            edge = cur_disp + " -> " + dep_disp
            append_unique_non_empty(edges, edge_seen, edge)

    return finalize_import_graph_analysis(
        graph_adj,
        graph_keys,
        key_to_disp,
        visited_order,
        key_to_path,
        edges,
        missing_modules,
        relative_imports,
        reserved_conflicts,
        module_id_map,
    )


def build_module_east_map(
    entry_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "2",
    object_dispatch_mode: str = "",
) -> dict[str, dict[str, Any]]:
    """入口 + 依存ユーザーモジュールを個別に EAST 化して返す。"""
    analysis = _analyze_import_graph(entry_path)
    files = dict_any_get_str_list(analysis, "user_module_files")
    module_east_raw: dict[str, dict[str, Any]] = {}
    for f in files:
        p = Path(f)
        module_east_raw[str(p)] = load_east(
            p,
            parser_backend,
            east_stage=east_stage,
            object_dispatch_mode=object_dispatch_mode,
        )
    return build_module_east_map_from_analysis(
        entry_path,
        analysis,
        module_east_raw,
    )


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
    max_generated_lines: int = 0,
) -> dict[str, Any]:
    """モジュールごとに `.h/.cpp` を `out/include`, `out/src` へ出力する。"""
    include_dir = output_dir / "include"
    src_dir = output_dir / "src"
    mkdirs_for_cli(str(include_dir))
    mkdirs_for_cli(str(src_dir))
    prelude_hdr = include_dir / "pytra_multi_prelude.h"
    prelude_txt = "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
    prelude_txt += "#ifndef PYTRA_MULTI_PRELUDE_H\n"
    prelude_txt += "#define PYTRA_MULTI_PRELUDE_H\n\n"
    prelude_txt += "#include \"runtime/cpp/pytra/built_in/py_runtime.h\"\n\n"
    prelude_txt += "#endif  // PYTRA_MULTI_PRELUDE_H\n"
    generated_lines_total = 0
    generated_lines_total += count_text_lines(prelude_txt)
    if max_generated_lines > 0:
        check_guard_limit("emit", "max_generated_lines", generated_lines_total, {"max_generated_lines": max_generated_lines})
    write_text_file(prelude_hdr, prelude_txt)

    root = Path(path_parent_text(entry_path))
    entry_key = str(entry_path)
    files: list[str] = []
    for mod_key in module_east_map:
        files.append(mod_key)
    files = sort_str_list_copy(files)
    module_ns_map: dict[str, str] = {}
    module_label_map: dict[str, str] = {}
    module_name_by_key: dict[str, str] = {}
    module_key_by_name: dict[str, str] = {}
    for mod_key in files:
        mod_path = Path(mod_key)
        east0 = dict_any_get_dict(module_east_map, mod_key)
        label = module_rel_label(root, mod_path)
        module_label_map[mod_key] = label
        mod_name = module_id_from_east_for_graph(root, mod_path, east0)
        module_name_by_key[mod_key] = mod_name
        if mod_name != "":
            module_ns_map[mod_name] = "pytra_mod_" + label
            if mod_name not in module_key_by_name:
                module_key_by_name[mod_name] = mod_key

    type_schema = build_module_type_schema(module_east_map)

    manifest_modules: list[dict[str, Any]] = []

    for mod_key in files:
        east = dict_any_get_dict(module_east_map, mod_key)
        if len(east) == 0:
            continue
        mod_path = Path(mod_key)
        label = module_label_map[mod_key] if mod_key in module_label_map else ""
        hdr_path = include_dir / (label + ".h")
        cpp_path = src_dir / (label + ".cpp")
        guard = "PYTRA_MULTI_" + sanitize_module_label(label).upper() + "_H"
        hdr_text = "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        hdr_text += "#ifndef " + guard + "\n"
        hdr_text += "#define " + guard + "\n\n"
        hdr_text += "namespace pytra_multi {\n"
        hdr_text += "void module_" + label + "();\n"
        hdr_text += "}  // namespace pytra_multi\n\n"
        hdr_text += "#endif  // " + guard + "\n"
        generated_lines_total += count_text_lines(hdr_text)
        if max_generated_lines > 0:
            check_guard_limit(
                "emit",
                "max_generated_lines",
                generated_lines_total,
                {"max_generated_lines": max_generated_lines},
                str(mod_path),
            )
        write_text_file(hdr_path, hdr_text)

        is_entry = mod_key == entry_key
        cpp_txt = _transpile_to_cpp_with_map(
            east,
            module_ns_map,
            negative_index_mode,
            bounds_check_mode,
            floor_div_mode,
            mod_mode,
            int_width,
            str_index_mode,
            str_slice_mode,
            opt_level,
            "pytra_mod_" + label,
            emit_main if is_entry else False,
        )
        # multi-file モードでは共通 prelude を使い、ランタイム include 重複を避ける。
        cpp_txt = replace_first(
            cpp_txt,
            '#include "runtime/cpp/pytra/built_in/py_runtime.h"',
            '#include "pytra_multi_prelude.h"',
        )
        # ユーザーモジュール import 呼び出しを解決するため、参照先関数の前方宣言を補う。
        meta = dict_any_get_dict(east, "meta")
        type_emitter = CppEmitter(
            east,
            {},
            negative_index_mode,
            bounds_check_mode,
            floor_div_mode,
            mod_mode,
            int_width,
            str_index_mode,
            str_slice_mode,
            opt_level,
            "",
            False,
        )
        import_modules = dict_any_get_dict(meta, "import_modules")
        import_symbols = dict_any_get_dict(meta, "import_symbols")
        dep_modules: set[str] = set()
        for module_id_obj in import_modules.values():
            if isinstance(module_id_obj, str) and module_id_obj:
                dep_modules.add(module_id_obj)
        for sym_obj in import_symbols.values():
            module_id = dict_any_get_str(sym_obj if isinstance(sym_obj, dict) else {}, "module")
            if module_id:
                dep_modules.add(module_id)
        fwd_lines: list[str] = []
        for mod_name in dep_modules:
            target_ns = module_ns_map.get(mod_name, "")
            if target_ns == "":
                continue
            target_key = module_key_by_name.get(mod_name, "")
            if target_key == "":
                continue
            target_schema = dict_any_get_dict(type_schema, target_key)
            funcs = dict_any_get_dict(target_schema, "functions")
            # `main` は他モジュールから呼ばれない前提。
            fn_decls: list[str] = []
            for fn_name_any, fn_sig_obj in funcs.items():
                if not isinstance(fn_name_any, str):
                    continue
                if fn_name_any == "main":
                    continue
                fn_name = fn_name_any
                sig = fn_sig_obj if isinstance(fn_sig_obj, dict) else {}
                ret_t = dict_any_get_str(sig, "return_type", "None")
                ret_cpp = "void" if ret_t == "None" else type_emitter._cpp_type_text(ret_t)
                arg_types = dict_any_get_dict(sig, "arg_types")
                arg_order = dict_any_get_list(sig, "arg_order")
                parts: list[str] = []
                for an in arg_order:
                    if not isinstance(an, str):
                        continue
                    at = dict_any_get_str(arg_types, an, "object")
                    at_cpp = type_emitter._cpp_type_text(at)
                    parts.append(at_cpp + " " + an)
                sep = ", "
                fn_decls.append("    " + ret_cpp + " " + fn_name + "(" + sep.join(parts) + ");")
            if len(fn_decls) > 0:
                fwd_lines.append("namespace " + target_ns + " {")
                fwd_lines.extend(fn_decls)
                fwd_lines.append("}  // namespace " + target_ns)
        if len(fwd_lines) > 0:
            cpp_txt = inject_after_includes_block(cpp_txt, join_str_list("\n", fwd_lines))
        generated_lines_total += count_text_lines(cpp_txt)
        if max_generated_lines > 0:
            check_guard_limit(
                "emit",
                "max_generated_lines",
                generated_lines_total,
                {"max_generated_lines": max_generated_lines},
                str(mod_path),
            )
        write_text_file(cpp_path, cpp_txt)

        manifest_modules.append(
            {
                "module": mod_key,
                "label": label,
                "header": str(hdr_path),
                "source": str(cpp_path),
                "is_entry": is_entry,
            }
        )

    manifest_for_dump: dict[str, Any] = {
        "entry": entry_key,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_obj: Any = manifest_for_dump
    manifest_txt = json.dumps(manifest_obj, ensure_ascii=False, indent=2)
    generated_lines_total += count_text_lines(manifest_txt)
    if max_generated_lines > 0:
        check_guard_limit(
            "emit",
            "max_generated_lines",
            generated_lines_total,
            {"max_generated_lines": max_generated_lines},
            str(entry_path),
        )
    write_text_file(manifest_path, manifest_txt)
    return {
        "entry": entry_key,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
        "manifest": str(manifest_path),
        "generated_lines_total": generated_lines_total,
    }


def dump_deps_graph_text(entry_path: Path) -> str:
    """入力 `.py` から辿れるユーザーモジュール依存グラフを整形して返す。"""
    analysis = _analyze_import_graph(entry_path)
    return format_import_graph_report(analysis)


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
    object_dispatch_mode_opt = dict_str_get(parsed, "object_dispatch_mode_opt", "")
    bounds_check_mode_opt = dict_str_get(parsed, "bounds_check_mode_opt", "")
    floor_div_mode_opt = dict_str_get(parsed, "floor_div_mode_opt", "")
    mod_mode_opt = dict_str_get(parsed, "mod_mode_opt", "")
    int_width_opt = dict_str_get(parsed, "int_width_opt", "")
    str_index_mode_opt = dict_str_get(parsed, "str_index_mode_opt", "")
    str_slice_mode_opt = dict_str_get(parsed, "str_slice_mode_opt", "")
    opt_level_opt = dict_str_get(parsed, "opt_level_opt", "")
    preset = dict_str_get(parsed, "preset", "")
    parser_backend = dict_str_get(parsed, "parser_backend", "self_hosted")
    east_stage = dict_str_get(parsed, "east_stage", "2")
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
    usage_text = "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--header-output OUTPUT.h] [--emit-runtime-cpp] [--output-dir DIR] [--single-file|--multi-file] [--top-namespace NS] [--preset MODE] [--negative-index-mode MODE] [--object-dispatch-mode {native,type_id}] [--east-stage {2,3}] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--guard-profile {off,default,strict}] [--max-ast-depth N] [--max-parse-nodes N] [--max-symbols-per-module N] [--max-scope-depth N] [--max-import-graph-nodes N] [--max-import-graph-edges N] [--max-generated-lines N] [--no-main] [--dump-deps] [--dump-options]"
    guard_limits: dict[str, int] = {}

    if show_help:
        print(usage_text, file=sys.stderr)
        return 0
    if input_txt == "":
        print(usage_text, file=sys.stderr)
        return 1
    if east_stage != "2" and east_stage != "3":
        print(f"error: invalid --east-stage: {east_stage}", file=sys.stderr)
        return 1
    if object_dispatch_mode_opt not in {"", "native", "type_id"}:
        print(f"error: invalid --object-dispatch-mode: {object_dispatch_mode_opt}", file=sys.stderr)
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
            analysis = _analyze_import_graph(input_path)
            validate_import_graph_or_raise(analysis)
            import_graph_analysis = analysis
            module_east_map_cache = build_module_east_map(
                input_path,
                parser_backend,
                east_stage=east_stage,
                object_dispatch_mode=object_dispatch_mode,
            )
        east_module: dict[str, Any] = (
            module_east_map_cache[input_txt]
            if input_txt.endswith(".py") and input_txt in module_east_map_cache
            else load_east(
                input_path,
                parser_backend,
                east_stage=east_stage,
                object_dispatch_mode=object_dispatch_mode,
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
            cpp_out = out_root / (rel_tail + ".cpp")
            hdr_out = out_root / (rel_tail + ".h")
            compat_cpp_out = compat_root / (rel_tail + ".cpp")
            compat_hdr_out = compat_root / (rel_tail + ".h")
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
                "// FORWARDER: generated runtime header moved to pytra-gen.\n"
                + "#pragma once\n\n"
                + '#include "runtime/cpp/pytra-gen/'
                + rel_tail
                + '.h"\n'
            )
            compat_cpp_txt = (
                "// FORWARDER TU: generated runtime source moved to pytra-gen.\n"
                + '#include "runtime/cpp/pytra-gen/'
                + rel_tail
                + '.cpp"\n'
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
            module_east_map: dict[str, dict[str, Any]] = {}
            if input_txt.endswith(".py"):
                module_east_map = (
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
                module_east_map[str(input_path)] = east_module
            out_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out")
            if output_txt != "":
                out_dir = Path(output_txt)
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
                guard_limits["max_generated_lines"] if "max_generated_lines" in guard_limits else 0,
            )
            msg = "multi-file output generated at: " + str(out_dir)
            manifest_obj: Any = mf.get("manifest")
            manifest_txt = ""
            if isinstance(manifest_obj, str):
                manifest_txt = manifest_obj
            if manifest_txt != "":
                msg += "\nmanifest: " + manifest_txt + "\n"
            else:
                msg += "\n"
            print(msg, end="")
            return 0
    except Exception as ex:
        parsed_err = parse_user_error(str(ex))
        cat = dict_any_get_str(parsed_err, "category")
        if cat != "":
            print_user_error(str(ex))
            return 1
        print("error: internal error occurred during transpilation.", file=sys.stderr)
        print("[internal_error] this may be a bug; report it with a reproducible case.", file=sys.stderr)
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

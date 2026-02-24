#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/pytra/compiler/east.py conversion.
"""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.compiler.east_parts.east1_build import East1BuildHelpers
from pytra.compiler.transpile_cli import CodegenOptionHelpers, EastAnalysisHelpers, EastDocumentHelpers, ErrorHelpers, GuardHelpers, ImportGraphHelpers, Py2CppArgvHelpers, TextPathHelpers
from pytra.compiler.east_parts.core import convert_path, convert_source_to_east_with_backend
from pytra.std import json
from pytra.std import os
from pytra.std.pathlib import Path
from pytra.std import sys


_HELPER_GROUPS: list[tuple[object | None, list[str]]] = [
    (
        globals().get("ErrorHelpers"),
        [
            "make_user_error",
            "parse_user_error",
            "print_user_error",
        ],
    ),
    (
        globals().get("EastDocumentHelpers"),
        [
            "load_east_document",
            "load_east3_document",
        ],
    ),
    (
        globals().get("TextPathHelpers"),
        [
            "join_str_list",
            "split_infix_once",
            "local_binding_name",
            "split_graph_issue_entry",
            "replace_first",
            "inject_after_includes_block",
            "split_ws_tokens",
            "first_import_detail_line",
            "append_unique_non_empty",
            "split_top_level_csv",
            "normalize_param_annotation",
            "extract_function_signatures_from_python_source",
            "extract_function_arg_types_from_python_source",
            "split_type_args",
            "split_top_level_union",
            "path_parent_text",
            "python_module_exists_under",
            "mkdirs_for_cli",
            "write_text_file",
            "count_text_lines",
            "sort_str_list_copy",
        ],
    ),
    (
        globals().get("EastAnalysisHelpers"),
        [
            "dict_any_get",
            "dict_any_get_str",
            "dict_any_get_list",
            "dict_any_get_dict",
            "dict_any_get_dict_list",
            "dict_any_get_str_list",
            "dict_any_kind",
            "dict_str_get",
            "name_target_id",
            "stmt_target_name",
            "assign_targets",
            "stmt_assigned_names",
            "stmt_child_stmt_lists",
            "collect_store_names_from_target",
            "collect_symbols_from_stmt",
            "collect_symbols_from_stmt_list",
            "stmt_list_parse_metrics",
            "stmt_list_scope_depth",
            "looks_like_runtime_function_name",
            "module_parse_metrics",
            "module_analyze_metrics",
            "select_guard_module_map",
        ],
    ),
    (
        globals().get("ImportGraphHelpers"),
        [
            "collect_import_modules",
            "module_id_from_east_for_graph",
            "module_name_from_path_for_graph",
            "module_export_table",
            "module_rel_label",
            "path_key_for_graph",
            "collect_reserved_import_conflicts",
            "rel_disp_for_graph",
            "format_graph_list_section",
            "format_import_graph_report",
            "graph_cycle_dfs",
            "is_known_non_user_import",
            "is_pytra_module_name",
            "resolve_module_name",
            "resolve_module_name_for_graph",
            "resolve_user_module_path_for_graph",
            "sanitize_module_label",
            "set_import_module_binding",
            "set_import_symbol_binding_and_module_set",
            "validate_from_import_symbols_or_raise",
            "validate_import_graph_or_raise",
            "collect_user_module_files_for_graph",
            "finalize_import_graph_analysis",
            "dump_deps_text",
        ],
    ),
    (
        globals().get("CodegenOptionHelpers"),
        [
            "resolve_codegen_options",
            "validate_codegen_options",
            "dump_codegen_options_text",
        ],
    ),
    (
        globals().get("GuardHelpers"),
        [
            "check_analyze_stage_guards",
            "check_guard_limit",
            "check_parse_stage_guards",
            "resolve_guard_limits",
        ],
    ),
    (
        globals().get("Py2CppArgvHelpers"),
        [
            "parse_py2cpp_argv",
        ],
    ),
]
for _helper_class, _helper_names in _HELPER_GROUPS:
    if _helper_class is None:
        continue
    for _helper_name in _helper_names:
        globals()[_helper_name] = getattr(_helper_class, _helper_name)
if "ImportGraphHelpers" in globals():
    dump_deps_graph_text_common = ImportGraphHelpers.dump_deps_graph_text
build_module_symbol_index = East1BuildHelpers.build_module_symbol_index
build_module_type_schema = East1BuildHelpers.build_module_type_schema
del _helper_class
del _helper_name
del _helper_names
del _HELPER_GROUPS


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
    if len(parts) > 0:
        leaf = parts[-1]
        leaf = leaf[: len(leaf) - 5] + "-impl" if leaf.endswith("_impl") else leaf
        parts[-1] = leaf
    return join_str_list("/", parts) + ".h"


def _join_runtime_path(base_dir: Path, rel_path: str) -> Path:
    """selfhost-safe な Path 連結（`/` 演算子依存を避ける）。"""
    base_txt = str(base_dir)
    if base_txt.endswith("/"):
        return Path(base_txt + rel_path)
    return Path(base_txt + "/" + rel_path)


def _runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """`pytra.*` モジュールの runtime C++ ヘッダ実在有無を返す。"""
    def _exists_under_runtime_roots(rel_hdr: str) -> bool:
        compat_hdr = _join_runtime_path(RUNTIME_CPP_COMPAT_ROOT, rel_hdr)
        gen_hdr = _join_runtime_path(RUNTIME_CPP_GEN_ROOT, rel_hdr)
        return compat_hdr.exists() or gen_hdr.exists()

    if module_name_norm.startswith("pytra.std."):
        tail = module_name_norm[10:]
        rel = _module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("std/" + rel)
    if module_name_norm.startswith("pytra.utils."):
        tail = module_name_norm[12:]
        rel = _module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("utils/" + rel)
    if module_name_norm.startswith("pytra.compiler."):
        tail = module_name_norm[15:]
        rel = _module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("compiler/" + rel)
    if module_name_norm.startswith("pytra.built_in."):
        tail = module_name_norm[15:]
        rel = _module_tail_to_cpp_header_path(tail) if tail != "" else ""
        return rel != "" and _exists_under_runtime_roots("built_in/" + rel)
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


def load_cpp_type_map(profile: dict[str, Any] = {}) -> dict[str, str]:
    """EAST 型 -> C++ 型の基本マップを返す（profile の `types` で上書き可能）。"""
    defaults: dict[str, str] = {
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
    return CodeEmitter.load_type_map(profile, defaults)


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
                if runtime_name != "":
                    mapped[attr_name] = runtime_name
        if len(mapped) > 0:
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


from hooks.cpp.emitter.cpp_emitter import CppEmitter, install_py2cpp_runtime_symbols
install_py2cpp_runtime_symbols(globals())

def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "",
) -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    if east_stage != "3":
        raise RuntimeError("py2cpp supports only --east-stage 3: " + east_stage)
    east3_doc = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
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
    i = 0
    while i < len(src):
        ch = src[i]
        ok = ((ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9"))
        if ok:
            out_chars.append(ch)
        else:
            out_chars.append("_")
        i += 1
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
        i = 0
        while i < len(parts):
            part = str(parts[i])
            if part.strip() == "None":
                return True
            i += 1
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
) -> dict[str, dict[str, Any]]:
    """入口 + 依存ユーザーモジュールの EAST map 構築（`east1_build` API への委譲）。"""

    def _build_module_doc(path_obj: Path, parser_backend: str = "self_hosted", object_dispatch_mode: str = "") -> dict[str, Any]:
        return load_east(
            path_obj,
            parser_backend=parser_backend,
            east_stage=east_stage,
            object_dispatch_mode=object_dispatch_mode,
        )

    mp = East1BuildHelpers.build_module_east_map(
        entry_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        runtime_std_source_root=RUNTIME_STD_SOURCE_ROOT,
        runtime_utils_source_root=RUNTIME_UTILS_SOURCE_ROOT,
        build_module_document_fn=_build_module_doc,
    )
    out: dict[str, dict[str, Any]] = {}
    for key, value in mp.items():
        if isinstance(value, dict):
            out[key] = value
    return out


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
    for mod_key, _mod_doc in module_east_map.items():
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

    type_schema = East1BuildHelpers.build_module_type_schema(module_east_map)

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
    usage_text = "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--header-output OUTPUT.h] [--emit-runtime-cpp] [--output-dir DIR] [--single-file|--multi-file] [--top-namespace NS] [--preset MODE] [--negative-index-mode MODE] [--object-dispatch-mode {native,type_id}] [--east-stage {3} (default:3)] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--guard-profile {off,default,strict}] [--max-ast-depth N] [--max-parse-nodes N] [--max-symbols-per-module N] [--max-scope-depth N] [--max-import-graph-nodes N] [--max-import-graph-edges N] [--max-generated-lines N] [--no-main] [--dump-deps] [--dump-options]"
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

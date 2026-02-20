#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/pytra/compiler/east.py conversion.
"""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.compiler.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options
from pytra.compiler.east_parts.core import convert_path, convert_source_to_east_with_backend
from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.std import sys


RUNTIME_STD_SOURCE_ROOT = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT = Path("src/pytra/utils")


def _join_str_list(sep: str, items: list[str]) -> str:
    """selfhost 安定化用: 区切り文字列による結合を明示関数化する。"""
    return sep.join(items)


def _python_module_exists_under(root_dir: Path, module_tail: str) -> bool:
    """`root_dir` 配下に `module_tail` 相当の `.py` / package があるかを返す。"""
    if module_tail == "":
        return False
    rel = module_tail.replace(".", "/")
    mod_py = root_dir / (rel + ".py")
    if mod_py.exists():
        return True
    pkg_init = root_dir / rel / "__init__.py"
    if pkg_init.exists():
        return True
    return False


def _module_tail_to_cpp_header_path(module_tail: str) -> str:
    """`a.b.c_impl` を `a/b/c-impl.h` へ変換する。"""
    path_tail = module_tail.replace(".", "/")
    parts: list[str] = []
    cur = ""
    i = 0
    while i < len(path_tail):
        ch = path_tail[i : i + 1]
        if ch == "/":
            parts.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    parts.append(cur)
    if len(parts) > 0:
        leaf = parts[len(parts) - 1]
        if leaf.endswith("_impl"):
            leaf = leaf[: len(leaf) - 5] + "-impl"
            parts[len(parts) - 1] = leaf
    return _join_str_list("/", parts) + ".h"


def _runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    """`pytra.*` モジュールの runtime C++ ヘッダ実在有無を返す。"""
    if module_name_norm.startswith("pytra.std."):
        tail = module_name_norm[10:]
        if tail == "":
            return False
        rel = _module_tail_to_cpp_header_path(tail)
        return (Path("src/runtime/cpp/pytra/std") / rel).exists()
    if module_name_norm.startswith("pytra.utils."):
        tail = module_name_norm[12:]
        if tail == "":
            return False
        rel = _module_tail_to_cpp_header_path(tail)
        return (Path("src/runtime/cpp/pytra/utils") / rel).exists()
    return False


def _make_user_error(category: str, summary: str, details: list[str]) -> Exception:
    payload = "__PYTRA_USER_ERROR__|" + category + "|" + summary
    i = 0
    while i < len(details):
        payload += "\n" + details[i]
        i += 1
    return RuntimeError(payload)


def _parse_user_error(err_text: str) -> dict[str, Any]:
    text = err_text
    tag = "__PYTRA_USER_ERROR__|"
    if not text.startswith(tag):
        out0: dict[str, Any] = {}
        out0["category"] = ""
        out0["summary"] = ""
        out0["details"] = []
        return out0
    lines: list[str] = []
    cur = ""
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch == "\n":
            lines.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    lines.append(cur)
    head = lines[0] if len(lines) > 0 else ""
    parts: list[str] = []
    cur = ""
    split_count = 0
    i = 0
    while i < len(head):
        ch = head[i : i + 1]
        if ch == "|" and split_count < 2:
            parts.append(cur)
            cur = ""
            split_count += 1
        else:
            cur += ch
        i += 1
    parts.append(cur)
    if len(parts) != 3:
        out1: dict[str, Any] = {}
        out1["category"] = ""
        out1["summary"] = ""
        out1["details"] = []
        return out1
    category = parts[1]
    summary = parts[2]
    details: list[str] = []
    i = 1
    while i < len(lines):
        line = lines[i]
        if line != "":
            details.append(line)
        i += 1
    out: dict[str, Any] = {}
    out["category"] = category
    out["summary"] = summary
    out["details"] = details
    return out

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

def _looks_like_runtime_function_name(name: str) -> bool:
    """ランタイム関数名（`py_*` か `ns::func`）らしい文字列か判定する。"""
    if name == "":
        return False
    if name.find("::") != -1:
        return True
    if name.startswith("py_"):
        return True
    return False


def _split_top_level_csv(text: str) -> list[str]:
    """括弧ネストを考慮してカンマ区切りを分割する。"""
    out: list[str] = []
    cur = ""
    depth_paren = 0
    depth_brack = 0
    depth_brace = 0
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch == "(":
            depth_paren += 1
            cur += ch
        elif ch == ")":
            if depth_paren > 0:
                depth_paren -= 1
            cur += ch
        elif ch == "[":
            depth_brack += 1
            cur += ch
        elif ch == "]":
            if depth_brack > 0:
                depth_brack -= 1
            cur += ch
        elif ch == "{":
            depth_brace += 1
            cur += ch
        elif ch == "}":
            if depth_brace > 0:
                depth_brace -= 1
            cur += ch
        elif ch == "," and depth_paren == 0 and depth_brack == 0 and depth_brace == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    tail = cur.strip()
    if tail != "":
        out.append(tail)
    return out


def _normalize_param_annotation(ann: str) -> str:
    """関数引数注釈文字列を EAST 互換の粗い型名へ正規化する。"""
    t = ann.strip()
    if t == "":
        return "unknown"
    if "Any" in t:
        return "Any"
    if "object" in t:
        return "object"
    if t in {"int", "float", "str", "bool", "bytes", "bytearray"}:
        return t
    if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
        return t
    return t


def _extract_function_arg_types_from_python_source(src_path: Path) -> dict[str, list[str]]:
    """EAST 化に失敗するモジュール用の関数シグネチャ簡易抽出。"""
    sigs = _extract_function_signatures_from_python_source(src_path)
    out: dict[str, list[str]] = {}
    for fn_name in sigs:
        sig = sigs[fn_name]
        arg_types_obj = sig.get("arg_types")
        if isinstance(arg_types_obj, list):
            out[fn_name] = arg_types_obj
    return out


def _extract_function_signatures_from_python_source(src_path: Path) -> dict[str, dict[str, list[str]]]:
    """`def` シグネチャから引数型とデフォルト値（テキスト）を抽出する。"""
    try:
        text = src_path.read_text(encoding="utf-8")
    except Exception:
        empty: dict[str, dict[str, list[str]]] = {}
        return empty
    lines: list[str] = text.splitlines()
    sig_map: dict[str, dict[str, list[str]]] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if (len(line) - len(line.lstrip(" "))) == 0 and stripped.startswith("def "):
            sig = stripped
            j = i + 1
            while (not sig.endswith(":")) and j < len(lines):
                sig += " " + lines[j].strip()
                j += 1
            i = j - 1
            if not sig.endswith(":"):
                i += 1
                continue
            sig0 = sig[:-1].strip()
            if not sig0.startswith("def "):
                i += 1
                continue
            p0 = sig0.find("(")
            if p0 < 0:
                i += 1
                continue
            name = sig0[4:p0].strip()
            if name == "":
                i += 1
                continue
            depth = 0
            p1 = -1
            k = p0
            while k < len(sig0):
                ch = sig0[k : k + 1]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        p1 = k
                        break
                k += 1
            if p1 < 0:
                i += 1
                continue
            params = sig0[p0 + 1 : p1]
            arg_types: list[str] = []
            arg_defaults: list[str] = []
            parts = _split_top_level_csv(params)
            p = 0
            while p < len(parts):
                prm = parts[p].strip()
                p += 1
                if prm == "" or prm.startswith("*"):
                    continue
                default_txt = ""
                eq_top = prm.find("=")
                if eq_top >= 0:
                    default_txt = prm[eq_top + 1 :].strip()
                    prm = prm[:eq_top].strip()
                colon = prm.find(":")
                if colon < 0:
                    arg_types.append("unknown")
                    arg_defaults.append(default_txt)
                    continue
                ann = prm[colon + 1 :]
                arg_types.append(_normalize_param_annotation(ann))
                arg_defaults.append(default_txt)
            sig: dict[str, list[str]] = {}
            sig["arg_types"] = arg_types
            sig["arg_defaults"] = arg_defaults
            sig_map[name] = sig
        i += 1
    return sig_map


def load_cpp_profile() -> dict[str, Any]:
    """C++ 用 LanguageProfile を読み込む（失敗時は最小既定）。"""
    out: dict[str, Any] = {}
    out["syntax"] = {}
    p = Path("src/profiles/cpp/runtime_calls.json")
    if not p.exists():
        return out
    try:
        txt = p.read_text(encoding="utf-8")
        raw_obj = json.loads(txt)
    except Exception:
        return out
    raw = raw_obj if isinstance(raw_obj, dict) else {}
    runtime_calls_obj = raw.get("runtime_calls")
    if isinstance(runtime_calls_obj, dict):
        out["runtime_calls"] = runtime_calls_obj
    return out


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


def load_cpp_type_map() -> dict[str, str]:
    """EAST 型 -> C++ 型の基本マップを profile から取得する。"""
    return {
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


def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """C++ 用 hooks 設定を返す。"""
    _ = profile
    hooks = build_cpp_hooks()
    if isinstance(hooks, dict):
        return hooks
    out: dict[str, Any] = {}
    return out


def load_cpp_identifier_rules() -> tuple[set[str], str]:
    """識別子リネーム規則を profile から取得する。"""
    reserved: set[str] = {
        "alignas", "alignof", "asm", "auto", "break", "case", "catch", "char", "class", "const", "constexpr",
        "continue", "default", "delete", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "namespace", "new", "operator", "private", "protected", "public", "register",
        "return", "short", "signed", "sizeof", "static", "struct", "switch", "template", "this", "throw", "try",
        "typedef", "typename", "union", "unsigned", "virtual", "void", "volatile", "while",
    }
    return reserved, "py_"


def load_cpp_module_attr_call_map(profile: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """C++ の `module.attr(...)` -> ランタイム呼び出しマップを返す。"""
    out: dict[str, dict[str, str]] = {}
    if not isinstance(profile, dict):
        return out
    runtime_calls_obj = profile.get("runtime_calls")
    runtime_calls = runtime_calls_obj if isinstance(runtime_calls_obj, dict) else {}
    module_attr_obj = runtime_calls.get("module_attr_call")
    module_attr = module_attr_obj if isinstance(module_attr_obj, dict) else {}
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
    out: str = '"'
    i = 0
    n = len(s)
    while i < n:
        ch = s[i : i + 1]
        if ch == "\\":
            out += "\\\\"
        elif ch == '"':
            out += '\\"'
        elif ch == "\n":
            out += "\\n"
        elif ch == "\r":
            out += "\\r"
        elif ch == "\t":
            out += "\\t"
        else:
            out += ch
        i += 1
    out += '"'
    return out


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
        module_namespace_map: dict[str, str] = {},
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
        self.class_base: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_storage_hints: dict[str, str] = {}
        self.ref_classes: set[str] = set()
        self.value_classes: set[str] = set()
        self.type_map: dict[str, str] = load_cpp_type_map()
        if self.int_width == "32":
            self.type_map["int64"] = "int32"
            self.type_map["uint64"] = "uint32"
        self.module_attr_call_map: dict[str, dict[str, str]] = load_cpp_module_attr_call_map(self.profile)
        self.reserved_words: set[str] = set()
        self.rename_prefix: str = "py_"
        self.reserved_words, self.rename_prefix = load_cpp_identifier_rules()
        self.reserved_words.add("main")
        self.import_modules: dict[str, str] = {}
        self.import_symbols: dict[str, dict[str, str]] = {}
        self.import_symbol_modules: set[str] = set()
        self.module_namespace_map = module_namespace_map
        self.function_arg_types: dict[str, list[str]] = {}
        self.current_function_return_type: str = ""
        self.declared_var_types: dict[str, str] = {}
        self._module_fn_arg_type_cache: dict[str, dict[str, list[str]]] = {}

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
        if module_name.startswith("pytra.runtime."):
            # 旧互換: runtime 名は utils 名へ正規化する。
            return "pytra.utils." + module_name[14:]
        if module_name == "pytra.runtime":
            return "pytra.utils"
        if module_name.startswith("pylib.tra."):
            return "pytra.utils." + module_name[10:]
        if module_name == "pylib.tra":
            return "pytra.utils"
        if _python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, module_name):
            return "pytra.std." + module_name
        if _python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, module_name):
            return "pytra.utils." + module_name
        return module_name

    def _module_name_to_cpp_include(self, module_name: str) -> str:
        """Python import モジュール名を C++ include へ解決する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if _python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/std/" + _module_tail_to_cpp_header_path(tail)
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if _python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return "pytra/utils/" + _module_tail_to_cpp_header_path(tail)
        return ""

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """Python import モジュール名を C++ namespace へ解決する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if tail != "":
                return "pytra::std::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if tail != "":
                return "pytra::utils::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra."):
            tail = module_name_norm[6:]
            if tail != "":
                return "pytra::" + tail.replace(".", "::")
            return "pytra"
        inc = self._module_name_to_cpp_include(module_name_norm)
        if inc.startswith("pytra/std/") and inc.endswith(".h"):
            tail: str = inc[10 : len(inc) - 2].replace("/", "::")
            if tail != "":
                return "pytra::" + tail
        if inc.startswith("pytra/utils/") and inc.endswith(".h"):
            tail: str = inc[12 : len(inc) - 2].replace("/", "::")
            if tail != "":
                return "pytra::utils::" + tail
        return ""

    def _collect_import_cpp_includes(self, body: list[dict[str, Any]], meta: dict[str, Any] | None = None) -> list[str]:
        """EAST body から必要な C++ include を収集する。"""
        includes: list[str] = []
        seen: set[str] = set()
        if isinstance(meta, dict):
            bindings: list[dict[str, Any]] = self._dict_stmt_list(meta.get("import_bindings"))
            if len(bindings) > 0:
                i = 0
                while i < len(bindings):
                    item = bindings[i]
                    module_id = self.any_to_str(item.get("module_id"))
                    export_name = self.any_to_str(item.get("export_name"))
                    binding_kind = self.any_to_str(item.get("binding_kind"))
                    if module_id != "":
                        mod_name = self._normalize_runtime_module_name(module_id)
                        inc = self._module_name_to_cpp_include(mod_name)
                        if inc != "" and inc not in seen:
                            seen.add(inc)
                            includes.append(inc)
                        if binding_kind == "symbol" and export_name != "":
                            if mod_name == "pytra.std":
                                sym_inc = self._module_name_to_cpp_include("pytra.std." + export_name)
                                if sym_inc != "" and sym_inc not in seen:
                                    seen.add(sym_inc)
                                    includes.append(sym_inc)
                            elif mod_name == "pytra.utils":
                                sym_inc = self._module_name_to_cpp_include("pytra.utils." + export_name)
                                if sym_inc != "" and sym_inc not in seen:
                                    seen.add(sym_inc)
                                    includes.append(sym_inc)
                    i += 1
                includes.sort()
                return includes
        for stmt in body:
            kind = self.any_to_str(stmt.get("kind"))
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    mod_name = self.any_to_str(ent.get("name"))
                    inc = self._module_name_to_cpp_include(mod_name)
                    if inc != "" and inc not in seen:
                        seen.add(inc)
                        includes.append(inc)
            elif kind == "ImportFrom":
                mod_name = self.any_to_str(stmt.get("module"))
                mod_name = self._normalize_runtime_module_name(mod_name)
                inc = self._module_name_to_cpp_include(mod_name)
                if inc != "" and inc not in seen:
                    seen.add(inc)
                    includes.append(inc)
                if mod_name == "pytra.std":
                    for ent in self._dict_stmt_list(stmt.get("names")):
                        sym = self.any_to_str(ent.get("name"))
                        if sym == "":
                            continue
                        sym_inc = self._module_name_to_cpp_include("pytra.std." + sym)
                        if sym_inc != "" and sym_inc not in seen:
                            seen.add(sym_inc)
                            includes.append(sym_inc)
                if mod_name == "pytra.utils":
                    for ent in self._dict_stmt_list(stmt.get("names")):
                        sym = self.any_to_str(ent.get("name"))
                        if sym == "":
                            continue
                        sym_inc = self._module_name_to_cpp_include("pytra.utils." + sym)
                        if sym_inc != "" and sym_inc not in seen:
                            seen.add(sym_inc)
                            includes.append(sym_inc)
        includes.sort()
        return includes

    def _seed_import_maps_from_meta(self) -> None:
        """`meta.import_bindings`（または互換メタ）から import 束縛マップを初期化する。"""
        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        refs = self.any_to_dict_list(meta.get("qualified_symbol_refs"))
        bindings = self.any_to_dict_list(meta.get("import_bindings"))
        if len(bindings) > 0:
            if len(refs) > 0:
                r = 0
                while r < len(refs):
                    ref_item = refs[r]
                    module_id = self.any_to_str(ref_item.get("module_id"))
                    symbol = self.any_to_str(ref_item.get("symbol"))
                    local_name = self.any_to_str(ref_item.get("local_name"))
                    if module_id != "" and symbol != "" and local_name != "":
                        sym_ent: dict[str, str] = {}
                        sym_ent["module"] = module_id
                        sym_ent["name"] = symbol
                        self.import_symbols[local_name] = sym_ent
                        self.import_symbol_modules.add(module_id)
                    r += 1
            i = 0
            while i < len(bindings):
                item = bindings[i]
                module_id = self.any_to_str(item.get("module_id"))
                export_name = self.any_to_str(item.get("export_name"))
                local_name = self.any_to_str(item.get("local_name"))
                binding_kind = self.any_to_str(item.get("binding_kind"))
                if module_id == "" or local_name == "":
                    i += 1
                    continue
                if binding_kind == "module":
                    self.import_modules[local_name] = module_id
                elif binding_kind == "symbol" and export_name != "" and len(refs) == 0:
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = module_id
                    sym_ent["name"] = export_name
                    self.import_symbols[local_name] = sym_ent
                    self.import_symbol_modules.add(module_id)
                i += 1
            if len(self.import_symbols) == 0:
                legacy_syms = self.any_to_dict_or_empty(meta.get("import_symbols"))
                for local_name, sym_obj in legacy_syms.items():
                    if not isinstance(local_name, str):
                        continue
                    sym = self.any_to_dict_or_empty(sym_obj)
                    module_id = self.any_to_str(sym.get("module"))
                    symbol_name = self.any_to_str(sym.get("name"))
                    if module_id != "" and symbol_name != "":
                        sym_ent2: dict[str, str] = {}
                        sym_ent2["module"] = module_id
                        sym_ent2["name"] = symbol_name
                        self.import_symbols[local_name] = sym_ent2
                        self.import_symbol_modules.add(module_id)
            if len(self.import_modules) == 0:
                legacy_mods = self.any_to_dict_or_empty(meta.get("import_modules"))
                for local_name, module_id_obj in legacy_mods.items():
                    if not isinstance(local_name, str):
                        continue
                    module_id = self.any_to_str(module_id_obj)
                    if module_id != "":
                        self.import_modules[local_name] = module_id
            return
        # canonical メタが空の場合は legacy メタへフォールバックする。
        legacy_syms = self.any_to_dict_or_empty(meta.get("import_symbols"))
        for local_name, sym_obj in legacy_syms.items():
            if not isinstance(local_name, str):
                continue
            sym = self.any_to_dict_or_empty(sym_obj)
            module_id = self.any_to_str(sym.get("module"))
            symbol_name = self.any_to_str(sym.get("name"))
            if module_id != "" and symbol_name != "":
                sym_ent3: dict[str, str] = {}
                sym_ent3["module"] = module_id
                sym_ent3["name"] = symbol_name
                self.import_symbols[local_name] = sym_ent3
                self.import_symbol_modules.add(module_id)
        legacy_mods = self.any_to_dict_or_empty(meta.get("import_modules"))
        for local_name, module_id_obj in legacy_mods.items():
            if not isinstance(local_name, str):
                continue
            module_id = self.any_to_str(module_id_obj)
            if module_id != "":
                self.import_modules[local_name] = module_id
        return

    def _opt_ge(self, level: int) -> bool:
        """最適化レベルが指定値以上かを返す。"""
        cur = 3
        if self.opt_level in {"0", "1", "2", "3"}:
            cur = int(self.opt_level)
        return cur >= level

    def emit_block_comment(self, text: str) -> None:
        """Emit docstring/comment as C-style block comment."""
        self.emit("/* " + text + " */")

    def emit_function_open(self, ret: str, name: str, args: str) -> None:
        """C++ 関数ヘッダを直接出力する（selfhost の syntax_line 崩れ回避）。"""
        self.emit(f"{ret} {name}({args}) {{")

    def emit_ctor_open(self, name: str, args: str) -> None:
        """C++ コンストラクタヘッダを直接出力する。"""
        self.emit(f"{name}({args}) {{")

    def emit_dtor_open(self, name: str) -> None:
        """C++ デストラクタヘッダを直接出力する。"""
        self.emit(f"~{name}() {{")

    def emit_class_open(self, name: str, base_txt: str) -> None:
        """C++ クラス（struct）ヘッダを直接出力する。"""
        self.emit(f"struct {name}{base_txt} {{")

    def emit_class_close(self) -> None:
        """C++ クラス終端を出力する。"""
        self.emit("};")

    def emit_block_close(self) -> None:
        """C++ ブロック終端を出力する。"""
        self.emit("}")

    def _is_std_runtime_call(self, runtime_call: str) -> bool:
        """`std::` 直呼び出しとして扱う runtime_call か判定する。"""
        return runtime_call[0:5] == "std::" or runtime_call[0:7] == "::std::"

    def _contains_text(self, text: str, needle: str) -> bool:
        """`needle in text` 相当を selfhost でも安全に判定する。"""
        if needle == "":
            return True
        i = 0
        n = len(text)
        m = len(needle)
        while i + m <= n:
            if text[i : i + m] == needle:
                return True
            i += 1
        return False

    def _resolve_imported_module_name(self, name: str) -> str:
        """import で束縛された識別子名を実モジュール名へ解決する。"""
        if self.is_declared(name):
            return ""
        if name in self.import_modules:
            mod_name = self.import_modules[name]
            if mod_name != "":
                return mod_name
        if name in self.import_symbols:
            sym = self.import_symbols[name]
            parent = ""
            child = ""
            if "module" in sym:
                parent = sym["module"]
            if "name" in sym:
                child = sym["name"]
            if parent != "" and child != "":
                return f"{parent}.{child}"
        return ""

    def _cpp_expr_to_module_name(self, expr: str) -> str:
        """`pytra::std::x` 形式の C++ 式を `pytra.std.x` へ戻す。"""
        if expr.startswith("pytra::"):
            return expr.replace("::", ".")
        return ""

    def _last_dotted_name(self, name: str) -> str:
        """`a.b.c` の末尾要素 `c` を返す。"""
        last = name
        i = 0
        n = len(name)
        while i < n:
            ch = name[i : i + 1]
            if ch == ".":
                last = name[i + 1 :]
            i += 1
        return last

    def _resolve_imported_symbol(self, name: str) -> dict[str, str]:
        """from-import で束縛された識別子を返す（無ければ空 dict）。"""
        if name in self.import_symbols:
            return self.import_symbols[name]
        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        refs = self.any_to_dict_list(meta.get("qualified_symbol_refs"))
        i = 0
        while i < len(refs):
            ref = refs[i]
            local_name = self.any_to_str(ref.get("local_name"))
            if local_name == name:
                module_id = self.any_to_str(ref.get("module_id"))
                symbol = self.any_to_str(ref.get("symbol"))
                if module_id != "" and symbol != "":
                    out_ref: dict[str, str] = {}
                    out_ref["module"] = module_id
                    out_ref["name"] = symbol
                    return out_ref
            i += 1
        binds = self.any_to_dict_list(meta.get("import_bindings"))
        i = 0
        while i < len(binds):
            ent = binds[i]
            if self.any_to_str(ent.get("binding_kind")) == "symbol":
                local_name = self.any_to_str(ent.get("local_name"))
                if local_name == name:
                    module_id = self.any_to_str(ent.get("module_id"))
                    export_name = self.any_to_str(ent.get("export_name"))
                    if module_id != "" and export_name != "":
                        out_bind: dict[str, str] = {}
                        out_bind["module"] = module_id
                        out_bind["name"] = export_name
                        return out_bind
            i += 1
        out: dict[str, str] = {}
        return out

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
        if module_name_norm in self._module_fn_arg_type_cache:
            fn_map = self._module_fn_arg_type_cache[module_name_norm]
            if fn_name in fn_map:
                return fn_map[fn_name]
            return []
        fn_map: dict[str, list[str]] = {}
        src_path: Path = self._module_source_path_for_name(module_name_norm)
        if str(src_path) == "":
            self._module_fn_arg_type_cache[module_name_norm] = fn_map
            return []
        fn_map = _extract_function_arg_types_from_python_source(src_path)
        self._module_fn_arg_type_cache[module_name_norm] = fn_map
        if fn_name in fn_map:
            return fn_map[fn_name]
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
        i = 0
        while i < len(args):
            a = args[i]
            if i < len(target_types):
                tt = target_types[i]
                arg_t = "unknown"
                if i < len(arg_nodes):
                    arg_t_obj = self.get_expr_type(arg_nodes[i])
                    if isinstance(arg_t_obj, str):
                        arg_t = arg_t_obj
                if self.is_any_like_type(tt) and (arg_t in {"", "unknown"} or not self.is_any_like_type(arg_t)):
                    if not a.startswith("make_object("):
                        a = f"make_object({a})"
            out.append(a)
            i += 1
        return out

    def _resolve_runtime_call_for_imported_symbol(self, module_name: str, symbol_name: str) -> str | None:
        """`from X import Y` で取り込まれた Y 呼び出しの runtime 名を返す。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        owner_keys: list[str] = [module_name_norm]
        short = self._last_dotted_name(module_name_norm)
        # `pytra.*` は正規モジュール名で解決し、短縮名への暗黙フォールバックは使わない。
        if short != module_name_norm and not module_name_norm.startswith("pytra."):
            owner_keys.append(short)
        for owner_key in owner_keys:
            if owner_key in self.module_attr_call_map:
                owner_map = self.module_attr_call_map[owner_key]
                if symbol_name in owner_map:
                    mapped = owner_map[symbol_name]
                    if mapped != "":
                        return mapped
        ns = self._module_name_to_cpp_namespace(module_name_norm)
        if ns != "":
            return f"{ns}::{symbol_name}"
        return None

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
        self._seed_import_maps_from_meta()
        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        body: list[dict[str, Any]] = []
        raw_body = self.any_dict_get_list(self.doc, "body")
        if isinstance(raw_body, list):
            for s in raw_body:
                if isinstance(s, dict):
                    body.append(s)
        for stmt in body:
            if stmt.get("kind") == "ClassDef":
                cls_name = str(stmt.get("name", ""))
                if cls_name != "":
                    self.class_names.add(cls_name)
                    mset: set[str] = set()
                    class_body: list[dict[str, Any]] = []
                    raw_class_body = self.any_dict_get_list(stmt, "body")
                    if isinstance(raw_class_body, list):
                        for s in raw_class_body:
                            if isinstance(s, dict):
                                class_body.append(s)
                    for s in class_body:
                        if s.get("kind") == "FunctionDef":
                            fn_name = str(s.get("name"))
                            mset.add(fn_name)
                    self.class_method_names[cls_name] = mset
                    base_raw = stmt.get("base")
                    base = str(base_raw) if isinstance(base_raw, str) else ""
                    self.class_base[cls_name] = base
                    hint = str(stmt.get("class_storage_hint", "ref"))
                    self.class_storage_hints[cls_name] = hint if hint in {"value", "ref"} else "ref"
            elif stmt.get("kind") == "FunctionDef":
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

        self.ref_classes = {name for name, hint in self.class_storage_hints.items() if hint == "ref"}
        changed = True
        while changed:
            changed = False
            for name, base in self.class_base.items():
                if base != "" and base in self.ref_classes and name not in self.ref_classes:
                    self.ref_classes.add(name)
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

        for stmt in body:
            self.emit_stmt(stmt)
            self.emit("")

        if self.emit_main:
            if self.top_namespace != "":
                self.indent -= 1
                self.emit(f"}}  // namespace {self.top_namespace}")
                self.emit("")
            has_pytra_main = False
            for stmt in body:
                if stmt.get("kind") == "FunctionDef" and self.any_to_str(stmt.get("name")) == "__pytra_main":
                    has_pytra_main = True
                    break
            self.emit("int main(int argc, char** argv) {")
            self.indent += 1
            self.emit("pytra_configure_from_argv(argc, argv);")
            self.scope_stack.append(set())
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
        out: str = ""
        i = 0
        while i < len(self.lines):
            if i > 0:
                out += NEWLINE_CHAR
            out += self.lines[i]
            i += 1
        return out

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

    def _can_runtime_cast_target(self, target_t: str) -> bool:
        """実行時キャストを安全に適用できる型か判定する。"""
        if target_t == "" or target_t in {"unknown", "Any", "object"}:
            return False
        if self._contains_text(target_t, "|") or self._contains_text(target_t, "Any") or self._contains_text(target_t, "None"):
            return False
        return True

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
        return f"make_object({self.render_expr(expr)})"

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
        i = len(value_nodes) - 2
        while i >= 0:
            cond = self.render_cond(value_nodes[i])
            cur = value_texts[i]
            if op_name == "And":
                out = f"({cond} ? {out} : {cur})"
            else:
                out = f"({cond} ? {cur} : {out})"
            i -= 1
        return out

    def _dict_stmt_list(self, raw: Any) -> list[dict[str, Any]]:
        """動的値から `list[dict]` を安全に取り出す。"""
        out: list[dict[str, Any]] = []
        items = self.any_to_list(raw)
        for item in items:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _binop_precedence(self, op_name: str) -> int:
        """二項演算子の優先順位を返す。"""
        if op_name in {"Mult", "Div", "FloorDiv", "Mod"}:
            return 12
        if op_name in {"Add", "Sub"}:
            return 11
        if op_name in {"LShift", "RShift"}:
            return 10
        if op_name == "BitAnd":
            return 9
        if op_name == "BitXor":
            return 8
        if op_name == "BitOr":
            return 7
        return 0

    def _one_char_str_const(self, node: Any) -> str:
        """1文字文字列定数ならその実文字を返す。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0 or nd.get("kind") != "Constant":
            return ""
        v = ""
        if "value" in nd:
            v = self.any_to_str(nd["value"])
        if v == "":
            return ""
        if len(v) == 1:
            return v
        if len(v) == 2 and v[0:1] == "\\":
            c = v[1:2]
            if c == "n":
                return "\n"
            if c == "r":
                return "\r"
            if c == "t":
                return "\t"
            if c == "\\":
                return "\\"
            if c == "'":
                return "'"
            if c == "0":
                return "\0"
            return ""
        return ""

    def _str_index_char_access(self, node: Any) -> str:
        """str 添字アクセスを `at()` ベースの char 比較式へ変換する。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0 or nd.get("kind") != "Subscript":
            return ""
        value_node: Any = nd.get("value")
        if self.get_expr_type(value_node) != "str":
            return ""
        sl: Any = nd.get("slice")
        sl_node = self.any_to_dict_or_empty(sl)
        if len(sl_node) > 0 and sl_node.get("kind") == "Slice":
            return ""
        if self.negative_index_mode != "off" and self._is_negative_const_index(sl):
            return ""
        base = self.render_expr(value_node)
        base_node = self.any_to_dict_or_empty(value_node)
        if len(base_node) > 0 and base_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
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

    def _wrap_for_binop_operand(
        self,
        rendered: str,
        operand_expr: dict[str, Any] | None,
        parent_op: str,
        is_right: bool = False,
    ) -> str:
        """二項演算の結合順を壊さないため必要時に括弧を補う。"""
        if not isinstance(operand_expr, dict):
            return rendered
        kind = str(operand_expr.get("kind", ""))
        if kind in {"IfExp", "BoolOp", "Compare"}:
            return f"({rendered})"
        if kind != "BinOp":
            return rendered

        child_op = str(operand_expr.get("op", ""))
        parent_prec = self._binop_precedence(parent_op)
        child_prec = self._binop_precedence(child_op)
        if child_prec < parent_prec:
            return f"({rendered})"
        # Keep explicit grouping for multiplication with a division subtree, e.g. a * (b / c).
        if parent_op == "Mult" and child_op in {"Div", "FloorDiv"}:
            return f"({rendered})"
        if is_right and child_prec == parent_prec and parent_op in {"Sub", "Div", "FloorDiv", "Mod", "LShift", "RShift"}:
            return f"({rendered})"
        return rendered

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
        if t in {"auto", "object", "std::any", "::std::any"}:
            saw_float = False
            saw_int = False
            i = 0
            while i < len(arg_nodes_safe):
                at0 = self.get_expr_type(arg_nodes_safe[i])
                at = at0 if isinstance(at0, str) else ""
                if at in {"float32", "float64"}:
                    saw_float = True
                elif at in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                    saw_int = True
                i += 1
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
            kind = self.any_to_str(st.get("kind"))
            if kind == "Assign":
                tgt = self.any_to_dict_or_empty(st.get("target"))
                if self.any_to_str(tgt.get("kind")) == "Name":
                    name = self.any_to_str(tgt.get("id"))
                    if name != "":
                        out[name] = self._infer_name_assign_type(st, tgt)
                elif self.any_to_str(tgt.get("kind")) == "Tuple":
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
                    i = 0
                    while i < len(elems):
                        ent = self.any_to_dict_or_empty(elems[i])
                        if self.any_to_str(ent.get("kind")) == "Name":
                            nm = self.any_to_str(ent.get("id"))
                            if nm != "":
                                et = ""
                                if i < len(elem_types):
                                    et = self.normalize_type_name(elem_types[i])
                                if et == "":
                                    t_ent = self.get_expr_type(elems[i])
                                    if isinstance(t_ent, str):
                                        et = self.normalize_type_name(t_ent)
                                out[nm] = et
                        i += 1
            elif kind == "AnnAssign":
                tgt = self.any_to_dict_or_empty(st.get("target"))
                if self.any_to_str(tgt.get("kind")) == "Name":
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
            if decl_t == "":
                decl_t = "object"
            cpp_t = self._cpp_type_text(decl_t)
            if cpp_t in {"", "auto"}:
                decl_t = "object"
                cpp_t = "object"
            self.emit(f"{cpp_t} {name};")
            self.declare_in_current_scope(name)
            self.declared_var_types[name] = decl_t

    def _emit_if_stmt(self, stmt: dict[str, Any]) -> None:
        """If ノードを出力する。"""
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        else_stmts = self._dict_stmt_list(stmt.get("orelse"))
        cond_txt = self.render_cond(stmt.get("test"))
        if cond_txt == "":
            test_node = self.any_to_dict_or_empty(stmt.get("test"))
            cond_txt = self.any_dict_get_str(test_node, "repr", "")
            if cond_txt == "":
                cond_txt = "false"
        self._predeclare_if_join_names(body_stmts, else_stmts)
        if self._can_omit_braces_for_single_stmt(body_stmts) and (len(else_stmts) == 0 or self._can_omit_braces_for_single_stmt(else_stmts)):
            self.emit(f"if ({cond_txt})")
            self.emit_scoped_stmt_list([body_stmts[0]], set())
            if len(else_stmts) > 0:
                self.emit("else")
                self.emit_scoped_stmt_list([else_stmts[0]], set())
            return

        self.emit(f"if ({cond_txt}) {{")
        self.emit_scoped_stmt_list(body_stmts, set())
        if len(else_stmts) > 0:
            self.emit("} else {")
            self.emit_scoped_stmt_list(else_stmts, set())
            self.emit_block_close()
        else:
            self.emit_block_close()

    def _emit_while_stmt(self, stmt: dict[str, Any]) -> None:
        """While ノードを出力する。"""
        cond_txt = self.render_cond(stmt.get("test"))
        if cond_txt == "":
            test_node = self.any_to_dict_or_empty(stmt.get("test"))
            cond_txt = self.any_dict_get_str(test_node, "repr", "")
            if cond_txt == "":
                cond_txt = "false"
        self.emit_scoped_block(
            f"while ({cond_txt}) {{",
            self._dict_stmt_list(stmt.get("body")),
            set(),
        )

    def _render_lvalue_for_augassign(self, target_expr: Any) -> str:
        """AugAssign 向けに左辺を簡易レンダリングする。"""
        target_node = self.any_to_dict_or_empty(target_expr)
        if target_node.get("kind") == "Name":
            return str(target_node.get("id", "_"))
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
        if ann_t_str == "":
            ann_t_str = decl_hint
        if ann_t_str == "" and ann_text_fallback not in {"", "{}", "None"}:
            ann_t_str = ann_text_fallback
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
                rendered_val = f"{t}{{{_join_str_list(', ', items)}}}"
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
        if self._can_runtime_cast_target(ann_t_str) and self.is_any_like_type(val_t) and rendered_val != "":
            rendered_val = self.apply_cast(rendered_val, ann_t_str)
        if self.is_any_like_type(ann_t_str) and val_is_dict:
            if val_kind == "Constant" and val.get("value") is None:
                rendered_val = "object{}"
            elif not rendered_val.startswith("make_object("):
                rendered_val = f"make_object({rendered_val})"
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
            if picked_decl_t == "":
                picked_decl_t = val_t
            if picked_decl_t == "":
                picked_decl_t = self.get_expr_type(stmt.get("target"))
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
        if declare and target_expr_node.get("kind") == "Name" and target not in self.current_scope():
            decl_t_raw = stmt.get("decl_type")
            decl_t = str(decl_t_raw) if isinstance(decl_t_raw, str) else ""
            inferred_t = self.get_expr_type(stmt.get("target"))
            picked_t = decl_t
            if picked_t == "":
                picked_t = inferred_t
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

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """1つの文ノードを C++ 文へ変換して出力する。"""
        hook_stmt = self.hook_on_emit_stmt(stmt)
        if hook_stmt is True:
            return
        kind = self.any_to_str(stmt.get("kind"))
        if self.hook_on_emit_stmt_kind(kind, stmt) is True:
            return
        self.emit_leading_comments(stmt)
        if kind == "Expr":
            self._emit_expr_stmt(stmt)
            return
        if kind == "Return":
            self._emit_return_stmt(stmt)
            return
        if kind == "Assign":
            self._emit_assign_stmt(stmt)
            return
        if kind == "Swap":
            self._emit_swap_stmt(stmt)
            return
        if kind == "AnnAssign":
            self._emit_annassign_stmt(stmt)
            return
        if kind == "AugAssign":
            self._emit_augassign_stmt(stmt)
            return
        if kind == "If":
            self._emit_if_stmt(stmt)
            return
        if kind == "While":
            self._emit_while_stmt(stmt)
            return
        if kind == "ForRange":
            self.emit_for_range(stmt)
            return
        if kind == "For":
            self.emit_for_each(stmt)
            return
        if kind == "Raise":
            self._emit_raise_stmt(stmt)
            return
        if kind == "Try":
            self._emit_try_stmt(stmt)
            return
        if kind == "FunctionDef":
            self._emit_function_stmt(stmt)
            return
        if kind == "ClassDef":
            self._emit_class_stmt(stmt)
            return
        if kind == "Pass":
            self._emit_pass_stmt(stmt)
            return
        if kind == "Break":
            self._emit_break_stmt(stmt)
            return
        if kind == "Continue":
            self._emit_continue_stmt(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            self._emit_noop_stmt(stmt)
            return
        self.emit(f"/* unsupported stmt kind: {kind} */")

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        """CppEmitter 側で文ディスパッチを固定し、selfhost時の静的束縛を避ける。"""
        for stmt in stmts:
            self.emit_stmt(stmt)

    def emit_scoped_stmt_list(self, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """スコープ付き文リスト出力（CppEmitter 固有ディスパッチ）。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        self.emit_stmt_list(stmts)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """ブロック開始行を出力し、スコープ付きで本文を出力して閉じる。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def _emit_noop_stmt(self, stmt: dict[str, Any]) -> None:
        kind = self.any_to_str(stmt.get("kind"))
        if kind == "Import":
            ents = self._dict_stmt_list(stmt.get("names"))
            if len(ents) == 0:
                raw_names = self.any_to_list(stmt.get("names"))
                i = 0
                while i < len(raw_names):
                    ent = self.any_to_dict_or_empty(raw_names[i])
                    if len(ent) > 0:
                        ents.append(ent)
                    i += 1
            for ent in ents:
                name = self.any_to_str(ent.get("name"))
                asname = self.any_to_str(ent.get("asname"))
                if name == "":
                    continue
                if asname != "":
                    self.import_modules[asname] = name
                else:
                    base = self._last_dotted_name(name)
                    if base != "":
                        self.import_modules[base] = name
            return
        if kind == "ImportFrom":
            mod = self.any_to_str(stmt.get("module"))
            ents = self._dict_stmt_list(stmt.get("names"))
            if len(ents) == 0:
                raw_names = self.any_to_list(stmt.get("names"))
                i = 0
                while i < len(raw_names):
                    ent = self.any_to_dict_or_empty(raw_names[i])
                    if len(ent) > 0:
                        ents.append(ent)
                    i += 1
            for ent in ents:
                name = self.any_to_str(ent.get("name"))
                asname = self.any_to_str(ent.get("asname"))
                if mod == "" or name == "":
                    continue
                if asname != "":
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = mod
                    sym_ent["name"] = name
                    self.import_symbols[asname] = sym_ent
                    self.import_symbol_modules.add(mod)
                else:
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = mod
                    sym_ent["name"] = name
                    self.import_symbols[name] = sym_ent
                    self.import_symbol_modules.add(mod)
        return

    def _emit_pass_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit("/* pass */")

    def _emit_break_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit("break;")

    def _emit_continue_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit("continue;")

    def _emit_swap_stmt(self, stmt: dict[str, Any]) -> None:
        left = self.render_expr(stmt.get("left"))
        right = self.render_expr(stmt.get("right"))
        self.emit(f"::std::swap({left}, {right});")

    def _emit_raise_stmt(self, stmt: dict[str, Any]) -> None:
        if not isinstance(stmt.get("exc"), dict):
            self.emit('throw ::std::runtime_error("raise");')
        else:
            self.emit(f"throw {self.render_expr(stmt.get('exc'))};")

    def _emit_function_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_function(stmt, False)

    def _emit_class_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_class(stmt)

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        value_is_dict: bool = len(value_node) > 0
        if value_is_dict and value_node.get("kind") == "Constant" and isinstance(value_node.get("value"), str):
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
        self.emit(rendered + ";")

    def _emit_return_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        v_is_dict: bool = len(value_node) > 0
        if not v_is_dict:
            self.emit("return;")
            return
        rv = self.render_expr(stmt.get("value"))
        ret_t = self.current_function_return_type
        expr_t0 = self.get_expr_type(stmt.get("value"))
        expr_t = expr_t0 if isinstance(expr_t0, str) else ""
        if self.is_any_like_type(ret_t) and (not self.is_any_like_type(expr_t)):
            rv = self.render_expr_as_any(stmt.get("value"))
        if self._can_runtime_cast_target(ret_t) and self.is_any_like_type(expr_t):
            rv = self.apply_cast(rv, ret_t)
        self.emit(f"return {rv};")

    def _emit_assign_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_assign(stmt)

    def _emit_try_stmt(self, stmt: dict[str, Any]) -> None:
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        has_effective_finally = any(isinstance(s, dict) and s.get("kind") != "Pass" for s in finalbody)
        if has_effective_finally:
            self.emit("{")
            self.indent += 1
            gid = self.next_tmp("__finally")
            self.emit(f"auto {gid} = py_make_scope_exit([&]() {{")
            self.indent += 1
            self.emit_stmt_list(finalbody)
            self.indent -= 1
            self.emit("});")
        if len(handlers) == 0:
            self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
            if has_effective_finally:
                self.indent -= 1
                self.emit("}")
            return
        self.emit("try {")
        self.indent += 1
        self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
        self.indent -= 1
        self.emit("}")
        for h in handlers:
            name_raw = h.get("name")
            name = name_raw if isinstance(name_raw, str) and name_raw != "" else "ex"
            self.emit(f"catch (const ::std::exception& {name}) {{")
            self.indent += 1
            self.emit_stmt_list(self._dict_stmt_list(h.get("body")))
            self.indent -= 1
            self.emit("}")
        if has_effective_finally:
            self.indent -= 1
            self.emit("}")

    def _can_omit_braces_for_single_stmt(self, stmts: list[dict[str, Any]]) -> bool:
        """単文ブロックで波括弧を省略可能か判定する。"""
        if not self._opt_ge(1):
            return False
        filtered: list[dict[str, Any]] = []
        for s in stmts:
            if isinstance(s, dict):
                filtered.append(s)
        if len(filtered) != 1:
            return False
        one = filtered[0]
        k = str(one.get("kind", ""))
        if k == "Assign":
            tgt = self.any_to_dict_or_empty(one.get("target"))
            # tuple assign は C++ で複数行へ展開されるため単文扱い不可
            if self.any_to_str(tgt.get("kind")) == "Tuple":
                return False
        return k in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}

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
        if target.get("kind") == "Tuple":
            lhs_elems = self.any_dict_get_list(target, "elements")
            if self._opt_ge(2) and isinstance(value, dict) and value.get("kind") == "Tuple":
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
                    tuple_elem_types = self.split_generic(tuple_type_text[6:-1])
                    if tuple_type_text != value_t:
                        value_is_optional_tuple = True
            if value_is_optional_tuple:
                self.emit(f"auto {tmp} = *({value_expr});")
            else:
                self.emit(f"auto {tmp} = {value_expr};")
            for i, elt in enumerate(self.any_dict_get_list(target, "elements")):
                lhs = self.render_expr(elt)
                if self.is_plain_name_expr(elt):
                    elt_dict = self.any_to_dict_or_empty(elt)
                    name = str(elt_dict.get("id", ""))
                    if not self.is_declared(name):
                        decl_t_txt = ""
                        if i < len(tuple_elem_types):
                            decl_t_txt = tuple_elem_types[i]
                        else:
                            decl_t_txt = self.get_expr_type(elt)
                        decl_t = self._cpp_type_text(decl_t_txt)
                        self.declare_in_current_scope(name)
                        self.declared_var_types[name] = decl_t_txt
                        self.emit(f"{decl_t} {lhs} = ::std::get<{i}>({tmp});")
                        continue
                self.emit(f"{lhs} = ::std::get<{i}>({tmp});")
            return
        texpr = self.render_lvalue(stmt.get("target"))
        if self.is_plain_name_expr(stmt.get("target")) and not self.is_declared(texpr):
            d0 = str(stmt.get("decl_type", ""))
            d1 = self.get_expr_type(stmt.get("target"))
            d2 = self.get_expr_type(stmt.get("value"))
            picked = d0 if d0 != "" else (d1 if d1 != "" else d2)
            if picked in {"", "unknown", "Any", "object"} and isinstance(value, dict) and value.get("kind") == "BinOp":
                lt0 = self.get_expr_type(value.get("left"))
                rt0 = self.get_expr_type(value.get("right"))
                lt = lt0 if isinstance(lt0, str) else ""
                rt = rt0 if isinstance(rt0, str) else ""
                left_node = self.any_to_dict_or_empty(value.get("left"))
                right_node = self.any_to_dict_or_empty(value.get("right"))
                if (lt == "" or lt == "unknown") and left_node.get("kind") == "Name":
                    ln = self.any_to_str(left_node.get("id"))
                    if ln in self.declared_var_types:
                        lt = self.declared_var_types[ln]
                if (rt == "" or rt == "unknown") and right_node.get("kind") == "Name":
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
            if dtype.startswith("list<") and self._contains_text(rval, "[&]() -> list<object> {"):
                rval = rval.replace("[&]() -> list<object> {", f"[&]() -> {dtype} {{")
                rval = rval.replace("list<object> __out;", f"{dtype} __out;")
            if dtype == "uint8" and isinstance(value, dict):
                byte_val = self._byte_from_str_expr(stmt.get("value"))
                if byte_val != "":
                    rval = str(byte_val)
            if isinstance(value, dict) and value.get("kind") == "BoolOp" and picked != "bool":
                rval = self.render_boolop(stmt.get("value"), True)
            rval_t0 = self.get_expr_type(stmt.get("value"))
            rval_t = rval_t0 if isinstance(rval_t0, str) else ""
            if self._can_runtime_cast_target(picked) and self.is_any_like_type(rval_t):
                rval = self.apply_cast(rval, picked)
            if self.is_any_like_type(picked):
                if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                    rval = "object{}"
                elif not rval.startswith("make_object("):
                    rval = f"make_object({rval})"
            self.emit(f"{dtype} {texpr} = {rval};")
            return
        rval = self.render_expr(stmt.get("value"))
        t_target = self.get_expr_type(stmt.get("target"))
        if self.is_plain_name_expr(stmt.get("target")) and t_target in {"", "unknown"}:
            if texpr in self.declared_var_types:
                t_target = self.declared_var_types[texpr]
        if t_target == "uint8" and isinstance(value, dict):
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rval = str(byte_val)
        if isinstance(value, dict) and value.get("kind") == "BoolOp" and t_target != "bool":
            rval = self.render_boolop(stmt.get("value"), True)
        rval_t0 = self.get_expr_type(stmt.get("value"))
        rval_t = rval_t0 if isinstance(rval_t0, str) else ""
        if self._can_runtime_cast_target(t_target) and self.is_any_like_type(rval_t):
            rval = self.apply_cast(rval, t_target)
        if self.is_any_like_type(t_target):
            if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                rval = "object{}"
            elif not rval.startswith("make_object("):
                rval = f"make_object({rval})"
        self.emit(f"{texpr} = {rval};")

    def _is_reexport_assign(self, target: dict[str, Any], value: dict[str, Any]) -> bool:
        """`Name = imported_symbol` 形式の再エクスポート代入かを返す。"""
        if len(self.scope_stack) != 1:
            return False
        if self.any_to_str(target.get("kind")) != "Name":
            return False
        kind = self.any_to_str(value.get("kind"))
        if kind == "Name":
            name = self.any_to_str(value.get("id"))
            if name in self.import_modules:
                return True
            if name in self.import_symbols:
                return True
            return False
        if kind == "Attribute":
            owner = self.any_to_dict_or_empty(value.get("value"))
            if self.any_to_str(owner.get("kind")) != "Name":
                return False
            owner_name = self.any_to_str(owner.get("id"))
            if owner_name in self.import_modules:
                return True
            if owner_name in self.import_symbols:
                return True
        return False

    def render_lvalue(self, expr: Any) -> str:
        """左辺値文脈の式（添字代入含む）を C++ 文字列へ変換する。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return self.render_expr(expr)
        if node.get("kind") != "Subscript":
            return self.render_expr(expr)
        val = self.render_expr(node.get("value"))
        val_ty0 = self.get_expr_type(node.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        idx = self.render_expr(node.get("slice"))
        idx_t0 = self.get_expr_type(node.get("slice"))
        idx_t = idx_t0 if isinstance(idx_t0, str) else ""
        if val_ty.startswith("dict["):
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

    def _target_bound_names(self, target: dict[str, Any]) -> set[str]:
        """for ターゲットが束縛する識別子名を収集する。"""
        names: set[str] = set()
        if not isinstance(target, dict) or len(target) == 0:
            return names
        if target.get("kind") == "Name":
            names.add(str(target.get("id", "_")))
            return names
        if target.get("kind") == "Tuple":
            for e_dict in self._dict_stmt_list(target.get("elements")):
                if e_dict.get("kind") == "Name":
                    names.add(str(e_dict.get("id", "_")))
        return names

    def _emit_target_unpack(self, target: dict[str, Any], src: str) -> None:
        """タプルターゲットへのアンパック代入を出力する。"""
        if not isinstance(target, dict) or len(target) == 0:
            return
        if target.get("kind") != "Tuple":
            return
        for i, e in enumerate(self.any_dict_get_list(target, "elements")):
            if isinstance(e, dict) and e.get("kind") == "Name":
                nm = self.render_expr(e)
                self.emit(f"auto {nm} = ::std::get<{i}>({src});")

    def emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノードを C++ の for ループとして出力する。"""
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target_node) == 0:
            self.emit("/* invalid for-range target */")
            return
        tgt = self.render_expr(stmt.get("target"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        tgt_ty_txt = ""
        if t0 != "":
            tgt_ty_txt = t0
        else:
            tgt_ty_txt = t1
        tgt_ty = self._cpp_type_text(tgt_ty_txt)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_braces = len(self.any_dict_get_list(stmt, "orelse")) == 0 and self._can_omit_braces_for_single_stmt(body_stmts)
        mode = self.any_to_str(stmt.get("range_mode"))
        if mode == "":
            mode = "dynamic"
        cond = ""
        if mode == "ascending":
            cond = f"{tgt} < {stop}"
        elif mode == "descending":
            cond = f"{tgt} > {stop}"
        else:
            cond = f"{step} > 0 ? {tgt} < {stop} : {tgt} > {stop}"
        inc = ""
        if self._opt_ge(2) and step == "1":
            inc = f"++{tgt}"
        elif self._opt_ge(2) and step == "-1":
            inc = f"--{tgt}"
        else:
            inc = f"{tgt} += {step}"
        hdr: str = f"for ({tgt_ty} {tgt} = {start}; {cond}; {inc})"
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

        self.emit(hdr + " {")
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
        if iter_expr.get("kind") == "RangeExpr":
            pseudo: dict[str, Any] = {}
            pseudo["target"] = stmt.get("target")
            t_raw = stmt.get("target_type")
            pseudo["target_type"] = t_raw if isinstance(t_raw, str) and t_raw != "" else "int64"
            pseudo["start"] = iter_expr.get("start")
            pseudo["stop"] = iter_expr.get("stop")
            pseudo["step"] = iter_expr.get("step")
            pseudo["range_mode"] = iter_expr.get("range_mode", "dynamic")
            pseudo["body"] = self.any_dict_get_list(stmt, "body")
            self.emit_for_range(pseudo)
            return
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_braces = len(self.any_dict_get_list(stmt, "orelse")) == 0 and self._can_omit_braces_for_single_stmt(body_stmts)
        t = self.render_expr(stmt.get("target"))
        it = self.render_expr(stmt.get("iter"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        t_ty = self._cpp_type_text(t0 if t0 != "" else t1)
        target_names = self._target_bound_names(target)
        unpack_tuple = target.get("kind") == "Tuple"
        if unpack_tuple:
            # tuple unpack emits extra binding lines before the loop body; keep braces for correctness.
            omit_braces = False
        iter_tmp = ""
        hdr = ""
        if unpack_tuple:
            iter_tmp = self.next_tmp("__it")
            hdr = f"for (auto {iter_tmp} : {it})"
        else:
            if t_ty == "auto":
                hdr = f"for (auto& {t} : {it})"
            else:
                hdr = f"for ({t_ty} {t} : {it})"
                self.declared_var_types[t] = t0 if t0 != "" else t1
        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            self.scope_stack.append(set(target_names))
            if unpack_tuple:
                self._emit_target_unpack(target, iter_tmp)
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(hdr + " {")
        self.indent += 1
        self.scope_stack.append(set(target_names))
        if unpack_tuple:
            self._emit_target_unpack(target, iter_tmp)
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def emit_function(self, stmt: dict[str, Any], in_class: bool = False) -> None:
        """関数定義ノードを C++ 関数として出力する。"""
        name = stmt.get("name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        ret = self.cpp_type(stmt.get("return_type"))
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_index = self.any_to_dict_or_empty(stmt.get("arg_index"))
        params: list[str] = []
        fn_scope: set[str] = set()
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "":
                n = str(raw_n)
                if n in arg_types:
                    arg_names.append(n)
        for idx, n in enumerate(arg_names):
            t = self.any_to_str(arg_types.get(n))
            skip_self = in_class and idx == 0 and n == "self"
            ct = self._cpp_type_text(t)
            usage = self.any_to_str(arg_usage.get(n))
            if usage == "":
                usage = "readonly"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if skip_self:
                pass
            elif by_ref and usage == "mutable":
                params.append(f"{ct}& {n}")
                fn_scope.add(n)
            elif by_ref:
                params.append(f"const {ct}& {n}")
                fn_scope.add(n)
            else:
                params.append(f"{ct} {n}")
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
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        prev_ret = self.current_function_return_type
        prev_decl_types = self.declared_var_types
        empty_decl_types: dict[str, str] = {}
        self.declared_var_types = empty_decl_types
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        if docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(body_stmts)
        self.current_function_return_type = prev_ret
        self.declared_var_types = prev_decl_types
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

    def emit_class(self, stmt: dict[str, Any]) -> None:
        """クラス定義ノードを C++ クラス/struct として出力する。"""
        name = stmt.get("name", "Class")
        is_dataclass = self.any_dict_get_int(stmt, "dataclass", 0) != 0
        base = self.any_to_str(stmt.get("base"))
        is_enum_base = base in {"Enum", "IntEnum", "IntFlag"}
        if is_enum_base:
            cls_name = str(name)
            enum_members: list[str] = []
            enum_values: list[str] = []
            class_body = self._dict_stmt_list(stmt.get("body"))
            for s in class_body:
                sk = self.any_to_str(s.get("kind"))
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
        consumed_assign_fields: set[str] = set()
        for s in class_body:
            if s.get("kind") == "AnnAssign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_plain_name_expr(s.get("target")):
                    fname = str(texpr.get("id", ""))
                    ann = self.any_to_str(s.get("annotation"))
                    if ann != "":
                        if is_dataclass:
                            instance_field_defaults[fname] = self.render_expr(s.get("value")) if s.get("value") is not None else instance_field_defaults.get(fname, "")
                        else:
                            static_field_types[fname] = ann
                            if s.get("value") is not None:
                                static_field_defaults[fname] = self.render_expr(s.get("value"))
            elif is_enum_base and s.get("kind") == "Assign":
                texpr = self.any_to_dict_or_empty(s.get("target"))
                if self.is_name(s.get("target"), None):
                    fname = self.any_to_str(texpr.get("id"))
                    if fname != "":
                        inferred = self.get_expr_type(s.get("value"))
                        ann = inferred if isinstance(inferred, str) else ""
                        if ann == "" or ann == "unknown":
                            ann = "int64" if base in {"IntEnum", "IntFlag"} else "int64"
                        static_field_types[fname] = ann
                        if s.get("value") is not None:
                            static_field_defaults[fname] = self.render_expr(s.get("value"))
                        consumed_assign_fields.add(fname)
        self.current_class_static_fields.clear()
        for k, _ in static_field_types.items():
            if isinstance(k, str) and k != "":
                self.current_class_static_fields.add(k)
        instance_fields: dict[str, str] = {}
        for k, v in self.current_class_fields.items():
            if isinstance(k, str) and isinstance(v, str) and k not in self.current_class_static_fields:
                instance_fields[k] = v
        has_init = any(s.get("kind") == "FunctionDef" and s.get("name") == "__init__" for s in class_body)
        for fname, fty in static_field_types.items():
            if fname in static_field_defaults:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname} = {static_field_defaults[fname]};")
            else:
                self.emit(f"inline static {self._cpp_type_text(fty)} {fname};")
        for fname, fty in instance_fields.items():
            self.emit(f"{self._cpp_type_text(fty)} {fname};")
        if len(static_field_types) > 0 or len(instance_fields) > 0:
            self.emit("")
        if len(instance_fields) > 0 and not has_init:
            params: list[str] = []
            for fname, fty in instance_fields.items():
                p = f"{self._cpp_type_text(fty)} {fname}"
                if fname in instance_field_defaults and instance_field_defaults[fname] != "":
                    p += f" = {instance_field_defaults[fname]}"
                params.append(p)
            self.emit(f"{name}({_join_str_list(', ', params)}) {{")
            self.indent += 1
            self.scope_stack.append(set())
            for fname in instance_fields.keys():
                self.emit(f"this->{fname} = {fname};")
            self.scope_stack.pop()
            self.indent -= 1
            self.emit_block_close()
            self.emit("")
        for s in class_body:
            if s.get("kind") == "FunctionDef":
                self.emit_function(s, True)
            elif s.get("kind") == "AnnAssign":
                t = self.cpp_type(s.get("annotation"))
                target = self.render_expr(s.get("target"))
                if self.is_plain_name_expr(s.get("target")) and target in self.current_class_fields:
                    pass
                elif s.get("value") is None:
                    self.emit(f"{t} {target};")
                else:
                    self.emit(f"{t} {target} = {self.render_expr(s.get('value'))};")
            elif is_enum_base and s.get("kind") == "Assign":
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
        if runtime_call == "py_print":
            return f"py_print({_join_str_list(', ', args)})"
        if runtime_call == "py_len" and len(args) == 1:
            return f"py_len({args[0]})"
        if runtime_call == "py_to_string" and len(args) == 1:
            src_expr = first_arg
            return self.render_to_string(src_expr)
        if runtime_call == "static_cast" and len(args) == 1:
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
        if runtime_call == "static_cast" and len(args) == 2 and builtin_name == "int":
            return f"py_to_int64_base({args[0]}, py_to_int64({args[1]}))"
        if runtime_call in {"py_min", "py_max"} and len(args) >= 1:
            fn_name = "min" if runtime_call == "py_min" else "max"
            return self.render_minmax(fn_name, args, self.any_to_str(expr.get("resolved_type")), arg_nodes)
        if runtime_call == "perf_counter":
            return "pytra::std::time::perf_counter()"
        if runtime_call == "open":
            return f"open({_join_str_list(', ', args)})"
        if runtime_call == "py_int_to_bytes":
            owner = self.render_expr(fn.get("value"))
            length = args[0] if len(args) >= 1 else "0"
            byteorder = args[1] if len(args) >= 2 else '"little"'
            return f"py_int_to_bytes({owner}, {length}, {byteorder})"
        if runtime_call == "py_isdigit" and len(args) == 1:
            return f"py_isdigit({args[0]})"
        if runtime_call == "py_isalpha" and len(args) == 1:
            return f"py_isalpha({args[0]})"
        if runtime_call == "py_strip" and len(args) == 0:
            owner = self.render_expr(fn.get("value"))
            return f"py_strip({owner})"
        if runtime_call == "py_rstrip" and len(args) == 0:
            owner = self.render_expr(fn.get("value"))
            return f"py_rstrip({owner})"
        if runtime_call == "py_startswith" and len(args) == 1:
            owner = self.render_expr(fn.get("value"))
            return f"py_startswith({owner}, {args[0]})"
        if runtime_call == "py_endswith" and len(args) == 1:
            owner = self.render_expr(fn.get("value"))
            return f"py_endswith({owner}, {args[0]})"
        if runtime_call == "py_replace" and len(args) == 2:
            owner = self.render_expr(fn.get("value"))
            return f"py_replace({owner}, {args[0]}, {args[1]})"
        if runtime_call == "py_join" and len(args) == 1:
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.join({args[0]})"
        if runtime_call in {"std::runtime_error", "::std::runtime_error"}:
            if len(args) == 0:
                return '::std::runtime_error("error")'
            return f"::std::runtime_error({args[0]})"
        if runtime_call == "Path":
            return f"Path({_join_str_list(', ', args)})"
        if runtime_call == "list.append":
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            owner_t0 = self.get_expr_type(fn.get("value"))
            owner_t = owner_t0 if isinstance(owner_t0, str) else ""
            if owner_t == "bytearray":
                a0 = f"static_cast<uint8>(py_to_int64({a0}))"
            if owner_t.startswith("list[") and owner_t.endswith("]"):
                inner_t: str = owner_t[5:-1].strip()
                if inner_t != "" and not self.is_any_like_type(inner_t):
                    if inner_t == "uint8":
                        a0 = f"static_cast<uint8>(py_to_int64({a0}))"
                    else:
                        a0 = f"{self._cpp_type_text(inner_t)}({a0})"
            return f"{owner}.append({a0})"
        if runtime_call == "list.extend":
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "{}"
            return f"{owner}.insert({owner}.end(), {a0}.begin(), {a0}.end())"
        if runtime_call == "list.pop":
            owner = self.render_expr(fn.get("value"))
            if len(args) == 0:
                return f"{owner}.pop()"
            return f"{owner}.pop({args[0]})"
        if runtime_call == "list.clear":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.clear()"
        if runtime_call == "list.reverse":
            owner = self.render_expr(fn.get("value"))
            return f"::std::reverse({owner}.begin(), {owner}.end())"
        if runtime_call == "list.sort":
            owner = self.render_expr(fn.get("value"))
            return f"::std::sort({owner}.begin(), {owner}.end())"
        if runtime_call == "set.add":
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            return f"{owner}.insert({a0})"
        if runtime_call in {"set.discard", "set.remove"}:
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            return f"{owner}.erase({a0})"
        if runtime_call == "set.clear":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.clear()"
        if runtime_call == "dict.get":
            owner = self.render_expr(fn.get("value"))
            owner_t = self.get_expr_type(fn.get("value"))
            objectish_owner = self.is_any_like_type(owner_t)
            if len(args) >= 2:
                out_t = self.any_to_str(expr.get("resolved_type"))
                if objectish_owner and out_t == "bool":
                    return f"dict_get_bool({owner}, {args[0]}, {args[1]})"
                if objectish_owner and out_t == "str":
                    return f"dict_get_str({owner}, {args[0]}, {args[1]})"
                if objectish_owner and out_t.startswith("list["):
                    return f"dict_get_list({owner}, {args[0]}, {args[1]})"
                if objectish_owner and (self.is_any_like_type(out_t) or out_t == "object"):
                    return f"dict_get_node({owner}, {args[0]}, {args[1]})"
                return f"py_dict_get_default({owner}, {args[0]}, {args[1]})"
            if len(args) == 1:
                return f"py_dict_get({owner}, {args[0]})"
        if runtime_call == "dict.items":
            owner = self.render_expr(fn.get("value"))
            return owner
        if runtime_call == "dict.keys":
            owner = self.render_expr(fn.get("value"))
            return f"py_dict_keys({owner})"
        if runtime_call == "dict.values":
            owner = self.render_expr(fn.get("value"))
            return f"py_dict_values({owner})"
        if runtime_call != "" and (self._is_std_runtime_call(runtime_call) or runtime_call.startswith("py_")):
            return f"{runtime_call}({_join_str_list(', ', args)})"
        if builtin_name == "bytes":
            return f"bytes({_join_str_list(', ', args)})" if len(args) >= 1 else "bytes{}"
        if builtin_name == "bytearray":
            return f"bytearray({_join_str_list(', ', args)})" if len(args) >= 1 else "bytearray{}"
        return ""

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
        fn_kind = self.any_to_str(fn.get("kind"))
        if fn_kind == "":
            fn_kind_obj = fn.get("kind")
            if fn_kind_obj is not None:
                fn_kind_txt = str(fn_kind_obj)
                if fn_kind_txt not in {"", "None", "{}", "[]"}:
                    fn_kind = fn_kind_txt
        if fn_kind == "Name":
            raw = self.any_to_str(fn.get("id"))
            imported_module = ""
            if raw != "" and not self.is_declared(raw):
                resolved = self._resolve_imported_symbol(raw)
                imported_module = resolved["module"] if "module" in resolved else ""
                resolved_name = resolved["name"] if "name" in resolved else ""
                if resolved_name != "":
                    raw = resolved_name
            if raw != "" and imported_module != "":
                mapped_runtime = self._resolve_runtime_call_for_imported_symbol(imported_module, raw)
                mapped_runtime_txt = ""
                if mapped_runtime is not None:
                    mapped_runtime_txt = str(mapped_runtime)
                if (
                    mapped_runtime_txt != ""
                    and mapped_runtime_txt not in {"perf_counter", "Path"}
                    and _looks_like_runtime_function_name(mapped_runtime_txt)
                ):
                    merged_args = self._merge_runtime_call_args(args, kw)
                    call_args: list[str] = merged_args
                    if self._contains_text(mapped_runtime_txt, "::"):
                        call_args = self._coerce_args_for_module_function(imported_module, raw, merged_args, arg_nodes)
                    return f"{mapped_runtime_txt}({_join_str_list(', ', call_args)})"
                imported_module_norm = self._normalize_runtime_module_name(imported_module)
                if imported_module_norm in self.module_namespace_map:
                    ns = self.module_namespace_map[imported_module_norm]
                    if ns != "":
                        call_args: list[str] = self._coerce_args_for_module_function(imported_module, raw, args, arg_nodes)
                        return f"{ns}::{raw}({_join_str_list(', ', call_args)})"
            if raw.startswith("py_assert_"):
                call_args: list[str] = []
                i = 0
                while i < len(args):
                    a = args[i]
                    if raw == "py_assert_stdout":
                        if i == 1 and not a.startswith("make_object("):
                            a = f"make_object({a})"
                    elif raw == "py_assert_eq":
                        if i < 2 and not a.startswith("make_object("):
                            a = f"make_object({a})"
                    call_args.append(a)
                    i += 1
                return f"pytra::utils::assertions::{raw}({_join_str_list(', ', call_args)})"
            if raw == "range":
                raise RuntimeError("unexpected raw range Call in EAST; expected RangeExpr lowering")
            if isinstance(raw, str) and raw in self.ref_classes:
                return f"::rc_new<{raw}>({_join_str_list(', ', args)})"
            if raw == "print":
                return f"py_print({_join_str_list(', ', args)})"
            if raw == "len" and len(args) == 1:
                return f"py_len({args[0]})"
            if raw == "reversed" and len(args) == 1:
                return f"py_reversed({args[0]})"
            if raw == "enumerate" and len(args) == 1:
                return f"py_enumerate({args[0]})"
            if raw == "any" and len(args) == 1:
                return f"py_any({args[0]})"
            if raw == "all" and len(args) == 1:
                return f"py_all({args[0]})"
            if raw == "isinstance" and len(args) == 2:
                type_name = ""
                rhs: dict[str, Any] = {}
                if len(arg_nodes) > 1:
                    rhs = self.any_to_dict_or_empty(arg_nodes[1])
                if rhs.get("kind") == "Name":
                    type_name = self.any_to_str(rhs.get("id"))
                a0 = args[0]
                if type_name == "dict":
                    return f"py_is_dict({a0})"
                if type_name == "list":
                    return f"py_is_list({a0})"
                if type_name == "set":
                    return f"py_is_set({a0})"
                if type_name == "str":
                    return f"py_is_str({a0})"
                if type_name == "int":
                    return f"py_is_int({a0})"
                if type_name == "float":
                    return f"py_is_float({a0})"
                if type_name == "bool":
                    return f"py_is_bool({a0})"
                return "false"
            if raw == "set" and len(args) == 0:
                t = self.cpp_type(expr.get("resolved_type"))
                return f"{t}{{}}"
            if raw == "set" and len(args) == 1:
                t = self.cpp_type(expr.get("resolved_type"))
                at0 = self.get_expr_type(first_arg)
                at = at0 if isinstance(at0, str) else ""
                if at.startswith("set["):
                    return args[0]
                if t == "set<object>" and at in {"Any", "object"}:
                    return f"{t}({args[0]})"
                if t.startswith("set<"):
                    if t == "set<object>" and at not in {"Any", "object"}:
                        return args[0]
                    return f"{t}({args[0]})"
                return f"set({args[0]})"
            if raw == "list" and len(args) == 0:
                t = self.cpp_type(expr.get("resolved_type"))
                return f"{t}{{}}"
            if raw == "list" and len(args) == 1:
                t = self.cpp_type(expr.get("resolved_type"))
                at0 = self.get_expr_type(first_arg)
                at = at0 if isinstance(at0, str) else ""
                if at.startswith("list["):
                    return args[0]
                if t == "list<object>" and at in {"Any", "object"}:
                    return f"{t}({args[0]})"
                if t.startswith("list<"):
                    if t == "list<object>" and at not in {"Any", "object"}:
                        return args[0]
                    return f"{t}({args[0]})"
                return f"list({args[0]})"
            if raw == "dict" and len(args) == 0:
                t = self.cpp_type(expr.get("resolved_type"))
                return f"{t}{{}}"
            if raw == "dict" and len(args) == 1:
                t = self.cpp_type(expr.get("resolved_type"))
                at0 = self.get_expr_type(first_arg)
                at = at0 if isinstance(at0, str) else ""
                if at.startswith("dict["):
                    return args[0]
                if t == "dict<str, object>" and at in {"Any", "object"}:
                    return f"{t}({args[0]})"
                if t.startswith("dict<"):
                    if t == "dict<str, object>" and at not in {"Any", "object"}:
                        return args[0]
                    return f"{t}({args[0]})"
                return f"dict({args[0]})"
            if raw == "bytes":
                return f"bytes({_join_str_list(', ', args)})" if len(args) >= 1 else "bytes{}"
            if raw == "bytearray":
                return f"bytearray({_join_str_list(', ', args)})" if len(args) >= 1 else "bytearray{}"
            if raw == "str" and len(args) == 1:
                src_expr = first_arg
                return self.render_to_string(src_expr)
            if raw in {"int", "float", "bool"} and len(args) == 1:
                target = self.cpp_type(expr.get("resolved_type"))
                arg_t = self.get_expr_type(first_arg)
                numeric_t = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
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
                return f"Path({_join_str_list(', ', args)})"
        if fn_kind == "Attribute":
            attr_rendered_txt = ""
            attr_rendered = self._render_call_attribute(expr, fn, args, kw)
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
        merged_args = self._merge_runtime_call_args(args, kw)
        call_args = merged_args
        owner_mod_norm = self._normalize_runtime_module_name(owner_mod)
        if owner_mod_norm in self.module_namespace_map:
            ns = self.module_namespace_map[owner_mod_norm]
            if ns != "":
                call_args = self._coerce_args_for_module_function(owner_mod, attr, merged_args, arg_nodes)
                return f"{ns}::{attr}({_join_str_list(', ', call_args)})"
        owner_keys: list[str] = [owner_mod_norm]
        short = self._last_dotted_name(owner_mod_norm)
        # `pytra.*` は正規モジュール名で解決し、短縮名への暗黙フォールバックは使わない。
        if short != owner_mod_norm and not owner_mod_norm.startswith("pytra."):
            owner_keys.append(short)
        for owner_key in owner_keys:
            if owner_key in self.module_attr_call_map:
                owner_map = self.module_attr_call_map[owner_key]
                if attr in owner_map:
                    mapped = owner_map[attr]
                    if mapped != "" and _looks_like_runtime_function_name(mapped):
                        if self._contains_text(mapped, "::"):
                            call_args = self._coerce_args_for_module_function(owner_mod, attr, merged_args, arg_nodes)
                        else:
                            call_args = merged_args
                        return f"{mapped}({_join_str_list(', ', call_args)})"
        ns = self._module_name_to_cpp_namespace(owner_mod_norm)
        if ns != "":
            call_args = self._coerce_args_for_module_function(owner_mod, attr, merged_args, arg_nodes)
            return f"{ns}::{attr}({_join_str_list(', ', call_args)})"
        return None

    def _merge_runtime_call_args(self, args: list[str], kw: dict[str, str]) -> list[str]:
        """runtime 呼び出し用に `args + keyword values` を並べた引数列を返す。"""
        if len(kw) == 0:
            return args
        out: list[str] = []
        i = 0
        while i < len(args):
            out.append(args[i])
            i += 1
        kw_keys: list[str] = []
        for key in kw:
            if isinstance(key, str):
                kw_keys.append(key)
        k = 0
        while k < len(kw_keys):
            key = kw_keys[k]
            out.append(kw[key])
            k += 1
        return out

    def _render_call_object_method(
        self, owner_t: str, owner_expr: str, attr: str, args: list[str]
    ) -> str | None:
        """obj.method(...) 呼び出しのうち、型依存の特殊ケースを処理する。"""
        owner_types: list[str] = [owner_t]
        if self._contains_text(owner_t, "|"):
            owner_types = self.split_union(owner_t)
        if owner_t == "unknown" and attr == "clear":
            return f"{owner_expr}.clear()"
        if attr == "append":
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            if "bytearray" in owner_types:
                a0 = f"static_cast<uint8>(py_to_int64({a0}))"
                return f"{owner_expr}.append({a0})"
            list_owner_t = ""
            i = 0
            while i < len(owner_types):
                t = owner_types[i]
                if t.startswith("list[") and t.endswith("]"):
                    list_owner_t = t
                    break
                i += 1
            if list_owner_t != "":
                inner_t: str = list_owner_t[5:-1].strip()
                if inner_t == "uint8":
                    a0 = f"static_cast<uint8>(py_to_int64({a0}))"
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
    ) -> str | None:
        """Attribute 形式の呼び出しを module/object/fallback の順で処理する。"""
        owner_obj: object = fn.get("value")
        owner = self.any_to_dict_or_empty(owner_obj)
        owner_t = self.get_expr_type(owner_obj)
        owner_kind = self.any_to_str(owner.get("kind"))
        if owner_kind == "":
            owner_kind_obj = owner.get("kind")
            if owner_kind_obj is not None:
                owner_kind_txt = str(owner_kind_obj)
                if owner_kind_txt not in {"", "None", "{}", "[]"}:
                    owner_kind = owner_kind_txt
        if owner_kind == "Name":
            owner_name = self.any_to_str(owner.get("id"))
            if owner_name in self.declared_var_types:
                declared_owner_t = self.declared_var_types[owner_name]
                if declared_owner_t not in {"", "unknown"}:
                    owner_t = declared_owner_t
        owner_expr = self.render_expr(owner_obj)
        if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            owner_expr = f"({owner_expr})"
        owner_mod = self._resolve_imported_module_name(owner_expr)
        if owner_mod == "":
            owner_mod = self._cpp_expr_to_module_name(owner_expr)
        owner_mod = self._normalize_runtime_module_name(owner_mod)
        arg_nodes_obj: object = expr.get("args")
        arg_nodes = self.any_to_list(arg_nodes_obj)
        attr = self.any_to_str(fn.get("attr"))
        if attr == "":
            attr = str(fn.get("attr"))
        if attr == "":
            return None
        module_rendered_txt = ""
        if owner_mod != "":
            module_rendered = self._render_call_module_method(owner_mod, attr, args, kw, arg_nodes)
            if isinstance(module_rendered, str):
                module_rendered_txt = str(module_rendered)
        elif owner_expr.startswith("pytra."):
            module_rendered = self._render_call_module_method(owner_expr, attr, args, kw, arg_nodes)
            if isinstance(module_rendered, str):
                module_rendered_txt = str(module_rendered)
        if module_rendered_txt != "":
            return module_rendered_txt
        object_rendered_txt = ""
        object_rendered = self._render_call_object_method(owner_t, owner_expr, attr, args)
        if isinstance(object_rendered, str):
            object_rendered_txt = str(object_rendered)
        if object_rendered_txt != "":
            return object_rendered_txt
        return None

    def _coerce_call_arg(self, arg_txt: str, arg_node: Any, target_t: str) -> str:
        """関数シグネチャに合わせて引数を必要最小限キャストする。"""
        if not self._can_runtime_cast_target(target_t):
            return arg_txt
        at0 = self.get_expr_type(arg_node)
        at = at0 if isinstance(at0, str) else ""
        if not self.is_any_like_type(at):
            return arg_txt
        if target_t in {"float32", "float64"}:
            return f"py_to_float64({arg_txt})"
        if target_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return f"{target_t}(py_to_int64({arg_txt}))"
        if target_t == "bool":
            return f"py_to_bool({arg_txt})"
        if target_t == "str":
            return f"py_to_string({arg_txt})"
        if target_t.startswith("list[") or target_t.startswith("dict[") or target_t.startswith("set["):
            return f"{self._cpp_type_text(target_t)}({arg_txt})"
        return arg_txt

    def _coerce_args_for_known_function(self, fn_name: str, args: list[str], arg_nodes: list[Any]) -> list[str]:
        """既知関数呼び出しに対して引数型を合わせる。"""
        if fn_name not in self.function_arg_types:
            return args
        sig = self.function_arg_types[fn_name]
        out: list[str] = []
        i = 0
        while i < len(args):
            a = args[i]
            if i < len(sig):
                n: Any = arg_nodes[i] if i < len(arg_nodes) else {}
                out.append(self._coerce_call_arg(a, n, sig[i]))
            else:
                out.append(a)
            i += 1
        return out

    def _render_call_fallback(self, fn_name: str, args: list[str]) -> str:
        """Call の最終フォールバック（通常の関数呼び出し）を返す。"""
        if fn_name.startswith("py_assert_"):
            call_args: list[str] = []
            i = 0
            while i < len(args):
                a = args[i]
                if fn_name == "py_assert_stdout":
                    if i == 1 and not a.startswith("make_object("):
                        a = f"make_object({a})"
                elif fn_name == "py_assert_eq":
                    if i < 2 and not a.startswith("make_object("):
                        a = f"make_object({a})"
                call_args.append(a)
                i += 1
            return f"pytra::utils::assertions::{fn_name}({_join_str_list(', ', call_args)})"
        if fn_name.endswith(".append") and len(args) == 1:
            owner_expr = fn_name[: len(fn_name) - 7]
            a0 = args[0]
            owner_t = ""
            if owner_expr in self.declared_var_types:
                owner_t = self.declared_var_types[owner_expr]
            if owner_t == "bytearray":
                a0 = f"static_cast<uint8>(py_to_int64({a0}))"
            elif owner_t.startswith("list[") and owner_t.endswith("]"):
                inner_t = owner_t[5:-1].strip()
                if inner_t == "uint8":
                    a0 = f"static_cast<uint8>(py_to_int64({a0}))"
                elif inner_t != "" and not self.is_any_like_type(inner_t):
                    a0 = f"{self._cpp_type_text(inner_t)}({a0})"
            return f"{owner_expr}.append({a0})"
        if fn_name == "print":
            return f"py_print({_join_str_list(', ', args)})"
        return f"{fn_name}({_join_str_list(', ', args)})"

    def _prepare_call_parts(
        self,
        expr: dict[str, Any],
    ) -> dict[str, Any]:
        """Call ノードの前処理（func/args/kw 展開）を共通化する。"""
        fn_obj: object = expr.get("func")
        fn = self.any_to_dict_or_empty(fn_obj)
        fn_name = self.render_expr(fn_obj)
        arg_nodes_obj: object = self.any_dict_get_list(expr, "args")
        arg_nodes = self.any_to_list(arg_nodes_obj)
        args = [self.render_expr(a) for a in arg_nodes]
        keywords_obj: object = self.any_dict_get_list(expr, "keywords")
        keywords = self.any_to_list(keywords_obj)
        first_arg: object = expr
        if len(arg_nodes) > 0:
            first_arg = arg_nodes[0]
        kw: dict[str, str] = {}
        for k in keywords:
            kd = self.any_to_dict_or_empty(k)
            if len(kd) > 0:
                kw_name = self.any_to_str(kd.get("arg"))
                if kw_name != "":
                    kw[kw_name] = self.render_expr(kd.get("value"))
        out: dict[str, Any] = {}
        out["fn"] = fn_obj
        out["fn_name"] = fn_name
        out["arg_nodes"] = arg_nodes
        out["args"] = args
        out["kw"] = kw
        out["first_arg"] = first_arg
        return out

    def _render_unary_expr(self, expr: dict[str, Any]) -> str:
        """UnaryOp ノードを C++ 式へ変換する。"""
        operand_obj: object = expr.get("operand")
        operand_expr = self.any_to_dict_or_empty(operand_obj)
        operand = self.render_expr(operand_obj)
        op = self.any_to_str(expr.get("op"))
        if op == "Not":
            if len(operand_expr) > 0 and operand_expr.get("kind") == "Compare":
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
                        rhs_type0 = self.get_expr_type(rhs_node0)
                        rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                        found = ""
                        if rhs_type.startswith("dict["):
                            found = f"{rhs}.find({left}) != {rhs}.end()"
                        else:
                            found = f"::std::find({rhs}.begin(), {rhs}.end(), {left}) != {rhs}.end()"
                        return f"!({found})" if op0 == "In" else found
            return f"!({operand})"
        if op == "USub":
            return f"-{operand}"
        if op == "UAdd":
            return f"+{operand}"
        return operand

    def _render_compare_expr(self, expr: dict[str, Any]) -> str:
        """Compare ノードを C++ 式へ変換する。"""
        if self.any_dict_get_str(expr, "lowered_kind", "") == "Contains":
            container = self.render_expr(expr.get("container"))
            key = self.render_expr(expr.get("key"))
            ctype0 = self.get_expr_type(expr.get("container"))
            ctype = ctype0 if isinstance(ctype0, str) else ""
            base = ""
            if ctype.startswith("dict["):
                base = f"{container}.find({key}) != {container}.end()"
            else:
                base = f"::std::find({container}.begin(), {container}.end(), {key}) != {container}.end()"
            if self.any_to_bool(expr.get("negated")):
                return f"!({base})"
            return base
        left = self.render_expr(expr.get("left"))
        ops = self.any_to_str_list(expr.get("ops"))
        if len(ops) == 0:
            rep = self.any_dict_get_str(expr, "repr", "")
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
            op_name: str = op
            cop = "=="
            cop_txt = str(CMP_OPS.get(op_name, ""))
            if cop_txt != "":
                cop = cop_txt
            if cop == "/* in */":
                rhs_type0 = self.get_expr_type(rhs_node)
                rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                if rhs_type.startswith("dict["):
                    parts.append(f"{rhs}.find({cur}) != {rhs}.end()")
                elif rhs_type.startswith("tuple["):
                    parts.append(f"py_tuple_contains({rhs}, {cur})")
                else:
                    parts.append(f"::std::find({rhs}.begin(), {rhs}.end(), {cur}) != {rhs}.end()")
            elif cop == "/* not in */":
                rhs_type0 = self.get_expr_type(rhs_node)
                rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                if rhs_type.startswith("dict["):
                    parts.append(f"{rhs}.find({cur}) == {rhs}.end()")
                elif rhs_type.startswith("tuple["):
                    parts.append(f"!py_tuple_contains({rhs}, {cur})")
                else:
                    parts.append(f"::std::find({rhs}.begin(), {rhs}.end(), {cur}) == {rhs}.end()")
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
        return _join_str_list(" && ", parts) if len(parts) > 0 else "true"

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
        if len(sl_node) > 0 and sl_node.get("kind") == "Slice":
            lo = self.render_expr(sl_node.get("lower")) if sl_node.get("lower") is not None else "0"
            up = self.render_expr(sl_node.get("upper")) if sl_node.get("upper") is not None else f"py_len({val})"
            return f"py_slice({val}, {lo}, {up})"
        idx = self.render_expr(sl)
        if val_ty.startswith("dict["):
            return f"py_dict_get({val}, {idx})"
        if self.is_indexable_sequence_type(val_ty):
            idx_t0 = self.get_expr_type(sl)
            idx_t = idx_t0 if isinstance(idx_t0, str) else ""
            if self.is_any_like_type(idx_t):
                idx = f"py_to_int64({idx})"
            return self._render_sequence_index(val, idx, sl)
        return f"{val}[{idx}]"

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）を C++ 式へ変換する。"""
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
        return f"({test_expr} ? {body} : {orelse})"

    def render_expr(self, expr: Any) -> str:
        """式ノードを C++ の式文字列へ変換する中核処理。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "/* none */"
        kind = self.any_to_str(expr_d.get("kind"))
        if kind == "":
            raw_kind_obj = expr_d.get("kind")
            if raw_kind_obj is not None:
                raw_kind_txt = str(raw_kind_obj)
                if raw_kind_txt not in {"", "None", "{}", "[]"}:
                    kind = raw_kind_txt
        hook_kind = self.hook_on_render_expr_kind(kind, expr_d)
        if isinstance(hook_kind, str) and hook_kind != "":
            return hook_kind
        if kind in {"JoinedStr", "Lambda", "ListComp", "SetComp", "DictComp"}:
            hook_complex = self.hook_on_render_expr_complex(expr_d)
            if isinstance(hook_complex, str) and hook_complex != "":
                return hook_complex

        if kind == "Name":
            name = str(expr_d.get("id", "_"))
            return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
        if kind == "Constant":
            v = expr_d.get("value")
            raw_repr = self.any_to_str(expr_d.get("repr"))
            if raw_repr != "" and not isinstance(v, bool) and v is not None and not isinstance(v, str):
                return raw_repr
            if isinstance(v, bool):
                return "true" if str(v) == "True" else "false"
            if v is None:
                t = self.get_expr_type(expr)
                if self.is_any_like_type(t):
                    return "make_object(1)"
                return "::std::nullopt"
            if isinstance(v, str):
                v_txt: str = str(v)
                if self.get_expr_type(expr) == "bytes":
                    raw = self.any_to_str(expr_d.get("repr"))
                    if raw != "":
                        qpos = -1
                        i = 0
                        while i < len(raw):
                            if raw[i] in {'"', "'"}:
                                qpos = i
                                break
                            i += 1
                        if qpos >= 0:
                            return f"py_bytes_lit({raw[qpos:]})"
                    return f"bytes({cpp_string_lit(v_txt)})"
                return cpp_string_lit(v_txt)
            return str(v)
        if kind == "Attribute":
            owner_t = self.get_expr_type(expr_d.get("value"))
            if self.is_forbidden_object_receiver_type(owner_t):
                raise RuntimeError(
                    "object receiver method call / attribute access is forbidden by language constraints"
                )
            base = self.render_expr(expr_d.get("value"))
            base_node = self.any_to_dict_or_empty(expr_d.get("value"))
            base_kind = self.any_dict_get_str(base_node, "kind", "")
            if base_kind == "":
                base_kind_obj = base_node.get("kind")
                if base_kind_obj is not None:
                    base_kind_txt = str(base_kind_obj)
                    if base_kind_txt not in {"", "None", "{}", "[]"}:
                        base_kind = base_kind_txt
            if base_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                base = f"({base})"
            attr = self.any_to_str(expr_d.get("attr"))
            if base == "self":
                if self.current_class_name is not None and str(attr) in self.current_class_static_fields:
                    return f"{self.current_class_name}::{attr}"
                return f"this->{attr}"
            # Class-name qualified member access in EAST uses dot syntax.
            # Emit C++ scope resolution for static members/methods.
            if base in self.class_base or base in self.class_method_names:
                return f"{base}::{attr}"
            # import モジュールの属性参照は map -> namespace の順で解決する。
            base_module_name = self._normalize_runtime_module_name(self._resolve_imported_module_name(base))
            if base_module_name != "":
                owner_keys: list[str] = [base_module_name]
                short = self._last_dotted_name(base_module_name)
                if short != base_module_name and not base_module_name.startswith("pytra."):
                    owner_keys.append(short)
                for owner_key in owner_keys:
                    if owner_key in self.module_attr_call_map:
                        owner_map = self.module_attr_call_map[owner_key]
                        if attr in owner_map:
                            mapped = owner_map[attr]
                            if mapped != "":
                                return mapped
                ns = self._module_name_to_cpp_namespace(base_module_name)
                if ns != "":
                    return f"{ns}::{attr}"
            if base_kind == "Name":
                base_name = self.any_to_str(base_node.get("id"))
                if (
                    base_name != ""
                    and not self.is_declared(base_name)
                    and base_name not in self.import_modules
                    and base_name in self.import_symbol_modules
                ):
                    src_obj = self.doc.get("source_path")
                    src = src_obj if isinstance(src_obj, str) and src_obj != "" else "(input)"
                    raise _make_user_error(
                        "input_invalid",
                        "from-import ではモジュール名は束縛されません。",
                        [f"kind=missing_symbol file={src} import={base_name}.{attr}"],
                    )
            bt = self.get_expr_type(expr_d.get("value"))
            if bt in self.ref_classes:
                return f"{base}->{attr}"
            return f"{base}.{attr}"
        if kind == "Call":
            call_parts: dict[str, Any] = self._prepare_call_parts(expr_d)
            fn = self.any_to_dict_or_empty(call_parts.get("fn"))
            fn_name = self.any_to_str(call_parts.get("fn_name"))
            arg_nodes = self.any_to_list(call_parts.get("arg_nodes"))
            args = [self.any_to_str(a) for a in self.any_to_list(call_parts.get("args"))]
            kw_raw = self.any_to_dict_or_empty(call_parts.get("kw"))
            kw: dict[str, str] = {}
            for k, v in kw_raw.items():
                if isinstance(k, str):
                    kw[k] = self.any_to_str(v)
            first_arg: object = call_parts.get("first_arg")
            fn_kind_for_call = self.any_to_str(fn.get("kind"))
            if fn_kind_for_call == "":
                fn_kind_obj = fn.get("kind")
                if fn_kind_obj is not None:
                    fn_kind_txt = str(fn_kind_obj)
                    if fn_kind_txt not in {"", "None", "{}", "[]"}:
                        fn_kind_for_call = fn_kind_txt
            if fn_kind_for_call == "Attribute":
                owner_node: object = fn.get("value")
                owner_t = self.get_expr_type(owner_node)
                if self.is_forbidden_object_receiver_type(owner_t):
                    raise RuntimeError(
                        "object receiver method call is forbidden by language constraints"
                    )
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
            args = self._coerce_args_for_known_function(fn_name, args, arg_nodes)
            return self._render_call_fallback(fn_name, args)
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
        if kind == "List":
            t = self.cpp_type(expr_d.get("resolved_type"))
            elem_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("list[") and rt.endswith("]"):
                elem_t = rt[5:-1].strip()
            parts: list[str] = []
            elements = self.any_to_list(expr_d.get("elements"))
            for e in elements:
                rv = self.render_expr(e)
                if self.is_any_like_type(elem_t):
                    rv = f"make_object({rv})"
                parts.append(rv)
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
            items: list[str] = []
            key_t = ""
            val_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("dict[") and rt.endswith("]"):
                inner = self.split_generic(rt[5:-1])
                if len(inner) == 2:
                    key_t = inner[0]
                    val_t = inner[1]
            entries = self._dict_stmt_list(expr_d.get("entries"))
            for kv in entries:
                k = self.render_expr(kv.get("key"))
                v = self.render_expr(kv.get("value"))
                if self.is_any_like_type(key_t):
                    k = f"make_object({k})"
                if self.is_any_like_type(val_t):
                    v = f"make_object({v})"
                items.append(f"{{{k}, {v}}}")
            return f"{t}{{{_join_str_list(', ', items)}}}"
        if kind == "Subscript":
            return self._render_subscript_expr(expr)
        if kind == "JoinedStr":
            if self.any_dict_get_str(expr_d, "lowered_kind", "") == "Concat":
                parts: list[str] = []
                for p in self._dict_stmt_list(expr_d.get("concat_parts")):
                    if p.get("kind") == "literal":
                        parts.append(cpp_string_lit(str(p.get("value", ""))))
                    elif p.get("kind") == "expr":
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
                return _join_str_list(" + ", parts)
            parts: list[str] = []
            for p in self._dict_stmt_list(expr_d.get("values")):
                pk = p.get("kind")
                if pk == "Constant":
                    parts.append(cpp_string_lit(str(p.get("value", ""))))
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
            return _join_str_list(" + ", parts)
        if kind == "Lambda":
            arg_texts: list[str] = []
            for a in self._dict_stmt_list(expr_d.get("args")):
                nm = self.any_to_str(a.get("arg")).strip()
                if nm != "":
                    arg_texts.append(f"auto {nm}")
            body_expr = self.render_expr(expr_d.get("body"))
            return f"[&]({_join_str_list(', ', arg_texts)}) {{ return {body_expr}; }}"
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
            if out_t in {"list<object>", "object", "std::any", "::std::any", "auto"}:
                elt_t0 = self.get_expr_type(expr_d.get("elt"))
                elt_t = elt_t0 if isinstance(elt_t0, str) else ""
                if elt_t != "" and elt_t != "unknown":
                    out_t = self._cpp_type_text(f"list[{elt_t}]")
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            rg = self.any_to_dict_or_empty(g.get("iter"))
            if rg.get("kind") == "RangeExpr":
                start = self.render_expr(rg.get("start"))
                stop = self.render_expr(rg.get("stop"))
                step = self.render_expr(rg.get("step"))
                mode = self.any_to_str(rg.get("range_mode"))
                if mode == "":
                    mode = "dynamic"
                cond = ""
                if mode == "ascending":
                    cond = f"({tgt} < {stop})"
                elif mode == "descending":
                    cond = f"({tgt} > {stop})"
                else:
                    cond = f"(({step}) > 0 ? ({tgt} < {stop}) : ({tgt} > {stop}))"
                lines.append(f"    for (int64 {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
            else:
                if tuple_unpack:
                    lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                    target_elements = self.any_to_list(g_target.get("elements"))
                    for i, e in enumerate(target_elements):
                        e_node = self.any_to_dict_or_empty(e)
                        if e_node.get("kind") == "Name":
                            nm = self.render_expr(e)
                            lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
                else:
                    lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = self.any_to_list(g.get("ifs"))
            if len(ifs) == 0:
                lines.append(f"        __out.append({elt});")
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
                cond: str = _join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out.append({elt});")
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
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                target_elements = self.any_to_list(g_target.get("elements"))
                for i, e in enumerate(target_elements):
                    e_node = self.any_to_dict_or_empty(e)
                    if e_node.get("kind") == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = self.any_to_list(g.get("ifs"))
            if len(ifs) == 0:
                lines.append(f"        __out.insert({elt});")
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
                cond: str = _join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out.insert({elt});")
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
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                target_elements = self.any_to_list(g_target.get("elements"))
                for i, e in enumerate(target_elements):
                    e_node = self.any_to_dict_or_empty(e)
                    if e_node.get("kind") == "Name":
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
                cond: str = _join_str_list(" && ", cond_parts)
                lines.append(f"        if ({cond}) __out[{key}] = {val};")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            sep = " "
            return sep.join(lines)

        rep = self.any_to_str(expr_d.get("repr"))
        if rep != "":
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
                non_none = [p for p in parts if p != "None"]
                if len(non_none) >= 1:
                    only_bytes = True
                    for p in non_none:
                        if p not in {"bytes", "bytearray"}:
                            only_bytes = False
                            break
                    if only_bytes:
                        return "bytes"
                if any(self.is_any_like_type(p) for p in non_none):
                    return "object"
                if len(parts) == 2 and len(non_none) == 1:
                    return f"::std::optional<{self._cpp_type_text(non_none[0])}>"
                return "::std::any"
        if east_type in self.ref_classes:
            return f"rc<{east_type}>"
        if east_type in self.class_names:
            return east_type
        if east_type == "None":
            return "void"
        if east_type == "PyFile":
            return "pytra::runtime::cpp::base::PyFile"
        if east_type.startswith("list[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 1:
                if inner[0] == "uint8":
                    return "bytearray"
                if self.is_any_like_type(inner[0]):
                    return "list<object>"
                if inner[0] == "unknown":
                    return "list<::std::any>"
                return f"list<{self._cpp_type_text(inner[0])}>"
        if east_type.startswith("set[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[4:-1])
            if len(inner) == 1:
                if inner[0] == "unknown":
                    return "set<str>"
                return f"set<{self._cpp_type_text(inner[0])}>"
        if east_type.startswith("dict[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 2:
                if self.is_any_like_type(inner[1]):
                    return f"dict<{self._cpp_type_text(inner[0] if inner[0] != 'unknown' else 'str')}, object>"
                if inner[0] == "unknown" and inner[1] == "unknown":
                    return "dict<str, ::std::any>"
                if inner[0] == "unknown":
                    return f"dict<str, {self._cpp_type_text(inner[1])}>"
                if inner[1] == "unknown":
                    return f"dict<{self._cpp_type_text(inner[0])}, ::std::any>"
                return f"dict<{self._cpp_type_text(inner[0])}, {self._cpp_type_text(inner[1])}>"
        if east_type.startswith("tuple[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[6:-1])
            inner_cpp: list[str] = []
            for x in inner:
                inner_cpp.append(self._cpp_type_text(x))
            sep = ", "
            return "::std::tuple<" + sep.join(inner_cpp) + ">"
        if east_type == "unknown":
            return "::std::any"
        if east_type.startswith("callable["):
            return "auto"
        if east_type == "callable":
            return "auto"
        if east_type == "module":
            return "auto"
        return east_type


def load_east(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    if input_path.suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            if payload.get("ok") is True and isinstance(payload.get("east"), dict):
                return payload.get("east")
            if payload.get("kind") == "Module":
                return payload
        raise _make_user_error(
            "input_invalid",
            "EAST JSON の形式が不正です。",
            ["期待形式: {'ok': true, 'east': {...}} または {'kind': 'Module', ...}"],
        )
    try:
        source_text = input_path.read_text(encoding="utf-8")
        if parser_backend == "self_hosted":
            east = convert_path(input_path)
        else:
            east = convert_source_to_east_with_backend(source_text, str(input_path), parser_backend=parser_backend)
    except SyntaxError as ex:
        msg = str(ex)
        raise _make_user_error(
            "user_syntax_error",
            "Python の文法エラーです。",
            [msg],
        ) from ex
    except Exception as ex:
        parsed_err = _parse_user_error(str(ex))
        ex_cat = str(parsed_err.get("category", ""))
        ex_details = parsed_err.get("details", [])
        if not isinstance(ex_details, list):
            ex_details = []
        if ex_cat != "":
            if ex_cat == "not_implemented":
                first = ""
                if len(ex_details) > 0 and isinstance(ex_details[0], str):
                    first = ex_details[0]
                if first == "":
                    raise _make_user_error(
                        "user_syntax_error",
                        "Python の文法エラーです。",
                        [],
                    ) from ex
            raise ex
        msg = str(ex)
        msg_attr = getattr(ex, "message", None)
        if msg == "" and isinstance(msg_attr, str):
            msg = msg_attr
        source_line = ""
        source_span_obj = getattr(ex, "source_span", None)
        if isinstance(source_span_obj, dict):
            line_obj = source_span_obj.get("lineno")
            line_no = line_obj if isinstance(line_obj, int) else 0
            if line_no > 0:
                src_lines = source_text.splitlines()
                idx = line_no - 1
                if idx >= 0 and idx < len(src_lines):
                    source_line = src_lines[idx].strip()
        if "from-import wildcard is not supported" in msg:
            import_txt = source_line if source_line != "" else "from ... import *"
            raise _make_user_error(
                "input_invalid",
                "import 構文が未対応です。",
                [f"kind=unsupported_import_form file={input_path} import={import_txt}"],
            ) from ex
        if "relative import is not supported" in msg:
            import_txt = source_line if source_line != "" else "from .module import symbol"
            raise _make_user_error(
                "input_invalid",
                "import 構文が未対応です。",
                [f"kind=unsupported_import_form file={input_path} import={import_txt}"],
            ) from ex
        if "duplicate import binding:" in msg:
            import_txt = source_line if source_line != "" else msg
            raise _make_user_error(
                "input_invalid",
                "import 束縛が重複しています。",
                [f"kind=duplicate_binding file={input_path} import={import_txt}"],
            ) from ex
        category = "not_implemented"
        summary = "この構文はまだ実装されていません。"
        if msg == "":
            category = "user_syntax_error"
            summary = "Python の文法エラーです。"
        if ("cannot parse" in msg) or ("unexpected token" in msg) or ("invalid syntax" in msg):
            category = "user_syntax_error"
            summary = "Python の文法エラーです。"
        if "forbidden by language constraints" in msg:
            category = "unsupported_by_design"
            summary = "この構文は言語仕様上サポート対象外です。"
        raise _make_user_error(category, summary, [msg]) from ex
    if isinstance(east, dict):
        return east
    raise _make_user_error(
        "input_invalid",
        "EAST の生成に失敗しました。",
        ["EAST ルートが dict ではありません。"],
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
    module_namespace_map: dict[str, str] = {},
) -> str:
    """EAST Module を C++ ソース文字列へ変換する。"""
    return CppEmitter(
        east_module,
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
        module_namespace_map,
    ).transpile()


def _split_type_args(text: str) -> list[str]:
    """`A[B,C[D]]` の `B,C[D]` をトップレベルで分割する。"""
    out: list[str] = []
    cur = ""
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            part: str = cur.strip()
            if part != "":
                out.append(part)
            cur = ""
        else:
            cur += ch
        i += 1
    tail: str = cur.strip()
    if tail != "":
        out.append(tail)
    return out


def _header_cpp_type_from_east(east_t: str) -> str:
    """EAST 型名を runtime header 向け C++ 型名へ変換する。"""
    t: str = east_t.strip()
    if t == "":
        return "object"
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
    if "|" in t:
        parts = _split_type_args(t.replace("|", ","))
        non_none: list[str] = []
        i = 0
        while i < len(parts):
            p = parts[i].strip()
            if p != "None":
                non_none.append(p)
            i += 1
        if len(parts) == 2 and len(non_none) == 1:
            return "::std::optional<" + _header_cpp_type_from_east(non_none[0]) + ">"
        folded: list[str] = []
        i = 0
        while i < len(non_none):
            p = non_none[i]
            if p == "bytearray":
                p = "bytes"
            if p not in folded:
                folded.append(p)
            i += 1
        if len(folded) == 1:
            only: str = folded[0]
            return _header_cpp_type_from_east(only)
        return "object"
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        return "list<" + _header_cpp_type_from_east(inner) + ">"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        return "set<" + _header_cpp_type_from_east(inner) + ">"
    if t.startswith("dict[") and t.endswith("]"):
        inner = _split_type_args(t[5:-1].strip())
        if len(inner) == 2:
            return "dict<" + _header_cpp_type_from_east(inner[0]) + ", " + _header_cpp_type_from_east(inner[1]) + ">"
        return "dict<str, object>"
    if t.startswith("tuple[") and t.endswith("]"):
        inner = _split_type_args(t[6:-1].strip())
        vals: list[str] = []
        i = 0
        while i < len(inner):
            vals.append(_header_cpp_type_from_east(inner[i]))
            i += 1
        sep = ", "
        return "::std::tuple<" + sep.join(vals) + ">"
    return t


def _header_guard_from_path(path: Path) -> str:
    """ヘッダパスから include guard を生成する。"""
    src = str(path).replace("\\", "/")
    prefix1 = "src/runtime/cpp/pytra/"
    prefix2 = "runtime/cpp/pytra/"
    if src.startswith(prefix1):
        src = src[len(prefix1) :]
    elif src.startswith(prefix2):
        src = src[len(prefix2) :]
    src = "PYTRA_" + src.upper()
    out = ""
    i = 0
    while i < len(src):
        ch: str = src[i : i + 1]
        ok = ("A" <= ch <= "Z") or ("0" <= ch <= "9")
        if ok:
            out += ch
        else:
            out += "_"
        i += 1
    while out.startswith("_"):
        out = out[1:]
    if not out.endswith("_H"):
        out += "_H"
    return out


def _header_render_default_expr(node: dict[str, Any], east_target_t: str) -> str:
    """EAST の既定値ノードを C++ ヘッダ宣言用の式文字列へ変換する。"""
    kind = str(node.get("kind", ""))
    if kind == "Constant":
        val = node.get("value")
        if val is None:
            return "::std::nullopt"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            return str(val)
        if isinstance(val, str):
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            return '"' + escaped + '"'
        return ""
    if kind == "Name":
        ident = str(node.get("id", ""))
        if ident == "None":
            return "::std::nullopt"
        if ident == "True":
            return "true"
        if ident == "False":
            return "false"
        return ""
    if kind == "Tuple":
        elems_obj = node.get("elements")
        elems = elems_obj if isinstance(elems_obj, list) else []
        if len(elems) == 0:
            return "::std::tuple<>{}"
        parts: list[str] = []
        i = 0
        while i < len(elems):
            e = elems[i]
            if isinstance(e, dict):
                txt = _header_render_default_expr(e, "Any")
                if txt == "":
                    return ""
                parts.append(txt)
            i += 1
        if len(parts) == 0:
            return ""
        return "::std::make_tuple(" + _join_str_list(", ", parts) + ")"
    _ = east_target_t
    return ""


def build_cpp_header_from_east(
    east_module: dict[str, Any],
    top_namespace: str = "",
    source_path: Path = Path(""),
    output_path: Path = Path(""),
) -> str:
    """EAST から最小宣言のみの C++ ヘッダ文字列を生成する。"""
    body_obj = east_module.get("body")
    body: list[dict[str, Any]] = []
    if isinstance(body_obj, list):
        i = 0
        while i < len(body_obj):
            item = body_obj[i]
            if isinstance(item, dict):
                body.append(item)
            i += 1

    fn_lines: list[str] = []
    var_lines: list[str] = []
    used_types: set[str] = set()

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

    i = 0
    while i < len(body):
        st = body[i]
        kind = str(st.get("kind", ""))
        if kind == "FunctionDef":
            name = str(st.get("name", ""))
            if name != "":
                ret_t = str(st.get("return_type", "None"))
                ret_cpp = _header_cpp_type_from_east(ret_t)
                used_types.add(ret_cpp)
                arg_types_obj = st.get("arg_types")
                arg_types = arg_types_obj if isinstance(arg_types_obj, dict) else {}
                arg_order_obj = st.get("arg_order")
                arg_order = arg_order_obj if isinstance(arg_order_obj, list) else []
                arg_defaults_obj = st.get("arg_defaults")
                arg_defaults = arg_defaults_obj if isinstance(arg_defaults_obj, dict) else {}
                parts: list[str] = []
                j = 0
                while j < len(arg_order):
                    an = arg_order[j]
                    if isinstance(an, str):
                        at_obj = arg_types.get(an)
                        at = at_obj if isinstance(at_obj, str) else "Any"
                        at_cpp = _header_cpp_type_from_east(at)
                        used_types.add(at_cpp)
                        param_txt = ""
                        if at_cpp in by_value_types:
                            param_txt = at_cpp + " " + an
                        else:
                            param_txt = "const " + at_cpp + "& " + an
                        if an in arg_defaults:
                            default_node_obj = arg_defaults.get(an)
                            default_node = default_node_obj if isinstance(default_node_obj, dict) else {}
                            if len(default_node) > 0:
                                default_txt = _header_render_default_expr(default_node, at)
                                if default_txt != "":
                                    param_txt += " = " + default_txt
                        parts.append(param_txt)
                    j += 1
                sep = ", "
                fn_lines.append(ret_cpp + " " + name + "(" + sep.join(parts) + ");")
        elif kind in {"Assign", "AnnAssign"}:
            tgt_obj = st.get("target")
            tgt = tgt_obj if isinstance(tgt_obj, dict) else {}
            if str(tgt.get("kind", "")) != "Name":
                i += 1
                continue
            name = str(tgt.get("id", ""))
            if name == "":
                i += 1
                continue
            decl_t = str(st.get("decl_type", ""))
            if decl_t == "" or decl_t == "unknown":
                decl_t = str(tgt.get("resolved_type", ""))
            if decl_t == "" or decl_t == "unknown":
                i += 1
                continue
            cpp_t = _header_cpp_type_from_east(decl_t)
            used_types.add(cpp_t)
            var_lines.append("extern " + cpp_t + " " + name + ";")
        i += 1

    includes: list[str] = []
    if any("::std::any" in t for t in used_types):
        includes.append("#include <any>")
    if any("::std::int" in t or "::std::uint" in t for t in used_types):
        includes.append("#include <cstdint>")
    if any("::std::string" in t for t in used_types):
        includes.append("#include <string>")
    if any("::std::vector" in t for t in used_types):
        includes.append("#include <vector>")
    if any("::std::tuple" in t for t in used_types):
        includes.append("#include <tuple>")
    if any("::std::optional" in t for t in used_types):
        includes.append("#include <optional>")
    if any("::std::unordered_map" in t for t in used_types):
        includes.append("#include <unordered_map>")
    if any("::std::unordered_set" in t for t in used_types):
        includes.append("#include <unordered_set>")

    guard = _header_guard_from_path(output_path)
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append("// source: " + str(source_path))
    lines.append("// generated-by: src/py2cpp.py")
    lines.append("")
    lines.append("#ifndef " + guard)
    lines.append("#define " + guard)
    lines.append("")
    k = 0
    while k < len(includes):
        lines.append(includes[k])
        k += 1
    if len(includes) > 0:
        lines.append("")
    ns = top_namespace.strip()
    if ns != "":
        lines.append("namespace " + ns + " {")
        lines.append("")
    k = 0
    while k < len(var_lines):
        lines.append(var_lines[k])
        k += 1
    if len(var_lines) > 0 and len(fn_lines) > 0:
        lines.append("")
    k = 0
    while k < len(fn_lines):
        lines.append(fn_lines[k])
        k += 1
    if ns != "":
        lines.append("")
        lines.append("}  // namespace " + ns)
    lines.append("")
    lines.append("#endif  // " + guard)
    lines.append("")
    return _join_str_list("\n", lines)


def _runtime_module_tail_from_source_path(input_path: Path) -> str:
    """`src/pytra/std` / `src/pytra/utils` から runtime tail を返す。"""
    src = str(input_path)
    rel = ""
    std_prefix = "src/pytra/std/"
    utils_prefix = "src/pytra/utils/"
    if src.startswith(std_prefix):
        rel = "std/" + src[len(std_prefix) :]
    elif src.startswith(utils_prefix):
        rel = src[len(utils_prefix) :]
    else:
        return ""
    if rel.endswith(".py"):
        rel = rel[: len(rel) - 3]
    if rel.endswith("/__init__"):
        rel = rel[: len(rel) - 9]
    return rel


def _is_runtime_emit_input_path(input_path: Path) -> bool:
    """`--emit-runtime-cpp` 対象パスか（`src/pytra/std|utils` 配下）を返す。"""
    return _runtime_module_tail_from_source_path(input_path) != ""


def _runtime_output_rel_tail(module_tail: str) -> str:
    """module tail（`std/<name>_impl` など）を runtime/cpp 相対パス tail へ写像する。"""
    parts: list[str] = []
    cur = ""
    i = 0
    while i < len(module_tail):
        ch = module_tail[i : i + 1]
        if ch == "/":
            parts.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    parts.append(cur)
    if len(parts) > 0:
        leaf = parts[len(parts) - 1]
        if leaf.endswith("_impl"):
            leaf = leaf[: len(leaf) - 5] + "-impl"
            parts[len(parts) - 1] = leaf
    rel = _join_str_list("/", parts)
    if rel == "std" or rel.startswith("std/"):
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
    return "pytra::utils::" + module_tail.replace("/", "::")


def _meta_import_bindings(east_module: dict[str, Any]) -> list[dict[str, str]]:
    """EAST `meta.import_bindings` を正規化して返す（無い場合は空）。"""
    out: list[dict[str, str]] = []
    meta_obj = east_module.get("meta")
    meta: dict[str, Any] = {}
    if isinstance(meta_obj, dict):
        meta = meta_obj
    binds_obj = meta.get("import_bindings")
    binds: list[Any] = []
    if isinstance(binds_obj, list):
        binds = binds_obj
    i = 0
    while i < len(binds):
        item_obj = binds[i]
        item = item_obj if isinstance(item_obj, dict) else {}
        if len(item) > 0:
            module_id_obj: object = item.get("module_id")
            export_name_obj: object = item.get("export_name")
            local_name_obj: object = item.get("local_name")
            binding_kind_obj: object = item.get("binding_kind")
            module_id = module_id_obj if isinstance(module_id_obj, str) else ""
            export_name = export_name_obj if isinstance(export_name_obj, str) else ""
            local_name = local_name_obj if isinstance(local_name_obj, str) else ""
            binding_kind = binding_kind_obj if isinstance(binding_kind_obj, str) else ""
            if module_id != "" and local_name != "" and binding_kind in {"module", "symbol"}:
                ent: dict[str, str] = {}
                ent["module_id"] = module_id
                ent["export_name"] = export_name
                ent["local_name"] = local_name
                ent["binding_kind"] = binding_kind
                out.append(ent)
        i += 1
    return out


def _meta_qualified_symbol_refs(east_module: dict[str, Any]) -> list[dict[str, str]]:
    """EAST `meta.qualified_symbol_refs` を正規化して返す（無い場合は空）。"""
    out: list[dict[str, str]] = []
    meta_obj = east_module.get("meta")
    meta: dict[str, Any] = {}
    if isinstance(meta_obj, dict):
        meta = meta_obj
    refs_obj = meta.get("qualified_symbol_refs")
    refs: list[Any] = []
    if isinstance(refs_obj, list):
        refs = refs_obj
    i = 0
    while i < len(refs):
        item_obj = refs[i]
        item = item_obj if isinstance(item_obj, dict) else {}
        if len(item) > 0:
            module_id_obj: object = item.get("module_id")
            symbol_obj: object = item.get("symbol")
            local_name_obj: object = item.get("local_name")
            module_id = module_id_obj if isinstance(module_id_obj, str) else ""
            symbol = symbol_obj if isinstance(symbol_obj, str) else ""
            local_name = local_name_obj if isinstance(local_name_obj, str) else ""
            if module_id != "" and symbol != "" and local_name != "":
                ent: dict[str, str] = {}
                ent["module_id"] = module_id
                ent["symbol"] = symbol
                ent["local_name"] = local_name
                out.append(ent)
        i += 1
    return out


def dump_deps_text(east_module: dict[str, Any]) -> str:
    """EAST の import メタデータを人間向けテキストへ整形する。"""
    import_bindings = _meta_import_bindings(east_module)
    body_obj: object = east_module.get("body")
    body: list[dict[str, Any]] = []
    if isinstance(body_obj, list):
        i = 0
        while i < len(body_obj):
            item = body_obj[i]
            if isinstance(item, dict):
                body.append(item)
            i += 1

    modules: list[str] = []
    module_seen: set[str] = set()
    symbols: list[str] = []
    symbol_seen: set[str] = set()

    if len(import_bindings) > 0:
        i = 0
        while i < len(import_bindings):
            ent = import_bindings[i]
            mod_name = ent["module_id"]
            export_name = ent["export_name"]
            local_name = ent["local_name"]
            binding_kind = ent["binding_kind"]
            if mod_name != "" and mod_name not in module_seen:
                module_seen.add(mod_name)
                modules.append(mod_name)
            if binding_kind == "symbol" and export_name != "":
                label = mod_name + "." + export_name
                if local_name != "" and local_name != export_name:
                    label += " as " + local_name
                if label not in symbol_seen:
                    symbol_seen.add(label)
                    symbols.append(label)
            i += 1
    else:
        i = 0
        while i < len(body):
            stmt = body[i]
            kind = stmt.get("kind")
            if kind == "Import":
                names_obj: object = stmt.get("names")
                if isinstance(names_obj, list):
                    j = 0
                    while j < len(names_obj):
                        ent = names_obj[j]
                        if isinstance(ent, dict):
                            mod_name_obj: object = ent.get("name")
                            mod_name = mod_name_obj if isinstance(mod_name_obj, str) else ""
                            if mod_name != "" and mod_name not in module_seen:
                                module_seen.add(mod_name)
                                modules.append(mod_name)
                        j += 1
            elif kind == "ImportFrom":
                mod_obj: object = stmt.get("module")
                mod_name = mod_obj if isinstance(mod_obj, str) else ""
                if mod_name != "" and mod_name not in module_seen:
                    module_seen.add(mod_name)
                    modules.append(mod_name)
                names_obj = stmt.get("names")
                if isinstance(names_obj, list):
                    j = 0
                    while j < len(names_obj):
                        ent = names_obj[j]
                        if isinstance(ent, dict):
                            sym_obj: object = ent.get("name")
                            alias_obj: object = ent.get("asname")
                            sym_name = sym_obj if isinstance(sym_obj, str) else ""
                            alias = alias_obj if isinstance(alias_obj, str) else ""
                            if sym_name != "":
                                label = mod_name + "." + sym_name
                                if alias != "":
                                    label += " as " + alias
                                if label not in symbol_seen:
                                    symbol_seen.add(label)
                                    symbols.append(label)
                        j += 1
            i += 1

    out = "modules:\n"
    if len(modules) == 0:
        out += "  (none)\n"
    else:
        i = 0
        while i < len(modules):
            out += "  - " + modules[i] + "\n"
            i += 1
    out += "symbols:\n"
    if len(symbols) == 0:
        out += "  (none)\n"
    else:
        i = 0
        while i < len(symbols):
            out += "  - " + symbols[i] + "\n"
            i += 1
    return out


def _collect_import_modules(east_module: dict[str, Any]) -> list[str]:
    """EAST module から import / from-import のモジュール名を抽出する。"""
    out: list[str] = []
    seen: set[str] = set()
    body_obj: object = east_module.get("body")
    if not isinstance(body_obj, list):
        return out
    i = 0
    while i < len(body_obj):
        stmt = body_obj[i]
        if isinstance(stmt, dict):
            kind_obj: object = stmt.get("kind")
            kind = kind_obj if isinstance(kind_obj, str) else ""
            if kind == "Import":
                names_obj: object = stmt.get("names")
                if isinstance(names_obj, list):
                    j = 0
                    while j < len(names_obj):
                        ent = names_obj[j]
                        if isinstance(ent, dict):
                            name_obj: object = ent.get("name")
                            name = name_obj if isinstance(name_obj, str) else ""
                            if name != "" and name not in seen:
                                seen.add(name)
                                out.append(name)
                        j += 1
            elif kind == "ImportFrom":
                mod_obj: object = stmt.get("module")
                mod = mod_obj if isinstance(mod_obj, str) else ""
                if mod != "" and mod not in seen:
                    seen.add(mod)
                    out.append(mod)
        i += 1
    return out


NON_FILE_STANDARD_IMPORTS: set[str] = {
    "__future__",
    "os",
    "glob",
}


def _is_known_non_user_import(module_name: str) -> bool:
    """依存グラフで「ユーザーファイル解決不要」とみなす import か判定する。"""
    if module_name in NON_FILE_STANDARD_IMPORTS:
        return True
    if _python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, module_name):
        return True
    if _python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, module_name):
        return True
    return False


def _is_pytra_module_name(module_name: str) -> bool:
    return module_name == "pytra" or module_name.startswith("pytra.")


def _path_key_for_graph(p: Path) -> str:
    """依存グラフ内部で使うパス文字列キーを返す。"""
    return str(p)


def _rel_disp_for_graph(base: Path, p: Path) -> str:
    """表示用に `base` からの相対パス文字列を返す。"""
    base_txt = str(base)
    p_txt = str(p)
    if base_txt.endswith("/"):
        base_prefix = base_txt
    else:
        base_prefix = base_txt + "/"
    if p_txt.startswith(base_prefix):
        return p_txt[len(base_prefix) :]
    if p_txt == base_txt:
        return "."
    return p_txt


def _analyze_import_graph(entry_path: Path) -> dict[str, Any]:
    """ユーザーモジュール依存を解析し、衝突/未解決/循環を返す。"""
    root = entry_path.parent
    queue: list[Path] = [entry_path]
    queued: set[str] = {_path_key_for_graph(entry_path)}
    visited: set[str] = set()
    edges: list[str] = []
    edge_seen: set[str] = set()
    missing_modules: list[str] = []
    missing_seen: set[str] = set()
    relative_imports: list[str] = []
    relative_seen: set[str] = set()
    graph_adj: dict[str, list[str]] = {}
    key_to_disp: dict[str, str] = {}
    key_to_path: dict[str, Path] = {}

    reserved_conflicts: list[str] = []
    if (root / "pytra.py").exists():
        reserved_conflicts.append(str(root / "pytra.py"))
    if (root / "pytra" / "__init__.py").exists():
        reserved_conflicts.append(str(root / "pytra" / "__init__.py"))

    while len(queue) > 0:
        cur_path = queue.pop(0)
        cur_key = _path_key_for_graph(cur_path)
        if cur_key in visited:
            continue
        visited.add(cur_key)
        key_to_path[cur_key] = cur_path
        key_to_disp[cur_key] = _rel_disp_for_graph(root, cur_path)
        try:
            east_cur = load_east(cur_path)
        except Exception:
            continue
        mods = _collect_import_modules(east_cur)
        if cur_key not in graph_adj:
            graph_adj[cur_key] = []
        cur_disp = key_to_disp[cur_key]
        i = 0
        while i < len(mods):
            mod = mods[i]
            resolved = resolve_module_name(mod, root)
            status_obj = resolved.get("status")
            status = status_obj if isinstance(status_obj, str) else "missing"
            if status == "relative":
                rel_item = cur_disp + ": " + mod
                if rel_item not in relative_seen:
                    relative_seen.add(rel_item)
                    relative_imports.append(rel_item)
                i += 1
                continue
            dep_disp = mod
            if status == "user":
                dep_path_obj = resolved.get("path")
                dep_file: Path | None = None
                if dep_path_obj is not None:
                    dep_file = Path(str(dep_path_obj))
                if dep_file is None:
                    i += 1
                    continue
                dep_key = _path_key_for_graph(dep_file)
                dep_disp = _rel_disp_for_graph(root, dep_file)
                graph_adj[cur_key].append(dep_key)
                key_to_path[dep_key] = dep_file
                key_to_disp[dep_key] = dep_disp
                if dep_key not in queued and dep_key not in visited:
                    queued.add(dep_key)
                    queue.append(dep_file)
            elif status == "missing":
                miss = cur_disp + ": " + mod
                if miss not in missing_seen:
                    missing_seen.add(miss)
                    missing_modules.append(miss)
            edge = cur_disp + " -> " + dep_disp
            if edge not in edge_seen:
                edge_seen.add(edge)
                edges.append(edge)
            i += 1

    cycles: list[str] = []
    cycle_seen: set[str] = set()
    color: dict[str, int] = {}
    stack: list[str] = []

    def _dfs(key: str) -> None:
        color[key] = 1
        stack.append(key)
        nxts = graph_adj.get(key, [])
        i = 0
        while i < len(nxts):
            nxt = nxts[i]
            c = color.get(nxt, 0)
            if c == 0:
                _dfs(nxt)
            elif c == 1:
                j = len(stack) - 1
                while j >= 0 and stack[j] != nxt:
                    j -= 1
                if j >= 0:
                    nodes = stack[j:] + [nxt]
                    disp_nodes: list[str] = []
                    k = 0
                    while k < len(nodes):
                        dk = nodes[k]
                        disp_nodes.append(key_to_disp.get(dk, dk))
                        k += 1
                    cycle_txt = _join_str_list(" -> ", disp_nodes)
                    if cycle_txt not in cycle_seen:
                        cycle_seen.add(cycle_txt)
                        cycles.append(cycle_txt)
            i += 1
        stack.pop()
        color[key] = 2

    keys = list(graph_adj.keys())
    i = 0
    while i < len(keys):
        k = keys[i]
        if color.get(k, 0) == 0:
            _dfs(k)
        i += 1

    out: dict[str, Any] = {}
    out["edges"] = edges
    out["missing_modules"] = missing_modules
    out["relative_imports"] = relative_imports
    out["reserved_conflicts"] = reserved_conflicts
    out["cycles"] = cycles
    user_module_files: list[str] = []
    visited_keys = list(visited)
    visited_keys.sort()
    for key in visited_keys:
        if key in key_to_path:
            user_module_files.append(str(key_to_path[key]))
    out["user_module_files"] = user_module_files
    return out


def _format_import_graph_report(analysis: dict[str, Any]) -> str:
    """依存解析結果を `--dump-deps` 向けテキストへ整形する。"""
    edges_obj = analysis.get("edges")
    edges: list[str] = edges_obj if isinstance(edges_obj, list) else []
    out = "graph:\n"
    if len(edges) == 0:
        out += "  (none)\n"
    else:
        i = 0
        while i < len(edges):
            item = edges[i]
            if isinstance(item, str):
                out += "  - " + item + "\n"
            i += 1

    def _append_list_section(label: str, key: str) -> None:
        nonlocal out
        items_obj = analysis.get(key)
        items: list[str] = items_obj if isinstance(items_obj, list) else []
        out += label + ":\n"
        if len(items) == 0:
            out += "  (none)\n"
        else:
            j = 0
            while j < len(items):
                val = items[j]
                if isinstance(val, str):
                    out += "  - " + val + "\n"
                j += 1

    _append_list_section("cycles", "cycles")
    _append_list_section("missing", "missing_modules")
    _append_list_section("relative", "relative_imports")
    _append_list_section("reserved", "reserved_conflicts")
    return out


def _validate_import_graph_or_raise(analysis: dict[str, Any]) -> None:
    """依存解析の重大問題を `input_invalid` として報告する。"""
    details: list[str] = []
    reserved_obj = analysis.get("reserved_conflicts")
    reserved = reserved_obj if isinstance(reserved_obj, list) else []
    i = 0
    while i < len(reserved):
        v = reserved[i]
        if isinstance(v, str) and v != "":
            details.append(f"kind=reserved_conflict file={v} import=pytra")
        i += 1

    relative_obj = analysis.get("relative_imports")
    relative = relative_obj if isinstance(relative_obj, list) else []
    i = 0
    while i < len(relative):
        v = relative[i]
        if isinstance(v, str) and v != "":
            file_part = v
            mod_part = v
            sep = ": "
            if sep in v:
                pos = v.find(sep)
                file_part = v[:pos]
                mod_part = v[pos + len(sep) :]
            details.append(f"kind=unsupported_import_form file={file_part} import=from {mod_part} import ...")
        i += 1

    missing_obj = analysis.get("missing_modules")
    missing = missing_obj if isinstance(missing_obj, list) else []
    i = 0
    while i < len(missing):
        v = missing[i]
        if isinstance(v, str) and v != "":
            file_part = v
            mod_part = v
            sep = ": "
            if sep in v:
                pos = v.find(sep)
                file_part = v[:pos]
                mod_part = v[pos + len(sep) :]
            details.append(f"kind=missing_module file={file_part} import={mod_part}")
        i += 1

    cycles_obj = analysis.get("cycles")
    cycles = cycles_obj if isinstance(cycles_obj, list) else []
    i = 0
    while i < len(cycles):
        v = cycles[i]
        if isinstance(v, str) and v != "":
            details.append(f"kind=import_cycle file=(graph) import={v}")
        i += 1
    if len(details) > 0:
        raise _make_user_error(
            "input_invalid",
            "import 解決に失敗しました（未解決/衝突/循環）。",
            details,
        )


def _module_export_table(module_east_map: dict[str, dict[str, Any]], root: Path) -> dict[str, set[str]]:
    """ユーザーモジュールの公開シンボル表（関数/クラス/代入名）を構築する。"""
    out: dict[str, set[str]] = {}
    for mod_key, east in module_east_map.items():
        mod_name = _module_name_from_path(root, Path(mod_key))
        if mod_name == "":
            continue
        body_obj = east.get("body")
        body = body_obj if isinstance(body_obj, list) else []
        exports: set[str] = set()
        i = 0
        while i < len(body):
            st = body[i]
            if isinstance(st, dict):
                kind_obj = st.get("kind")
                kind = kind_obj if isinstance(kind_obj, str) else ""
                if kind == "FunctionDef" or kind == "ClassDef":
                    name_obj = st.get("name")
                    if isinstance(name_obj, str) and name_obj != "":
                        exports.add(name_obj)
                elif kind == "Assign":
                    targets_obj = st.get("targets")
                    targets = targets_obj if isinstance(targets_obj, list) else []
                    j = 0
                    while j < len(targets):
                        tgt = targets[j]
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            name_obj = tgt.get("id")
                            if isinstance(name_obj, str) and name_obj != "":
                                exports.add(name_obj)
                        j += 1
                elif kind == "AnnAssign":
                    tgt = st.get("target")
                    if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                        name_obj = tgt.get("id")
                        if isinstance(name_obj, str) and name_obj != "":
                            exports.add(name_obj)
            i += 1
        out[mod_name] = exports
    return out


def _validate_from_import_symbols_or_raise(module_east_map: dict[str, dict[str, Any]], root: Path) -> None:
    """`from M import S` の `S` が `M` の公開シンボルに存在するか検証する。"""
    exports = _module_export_table(module_east_map, root)
    if len(exports) == 0:
        return
    details: list[str] = []
    for mod_key, east in module_east_map.items():
        file_disp = _rel_disp_for_graph(root, Path(mod_key))
        body_obj = east.get("body")
        body = body_obj if isinstance(body_obj, list) else []
        i = 0
        while i < len(body):
            st = body[i]
            if isinstance(st, dict) and st.get("kind") == "ImportFrom":
                mod_obj = st.get("module")
                imported_mod = mod_obj if isinstance(mod_obj, str) else ""
                if imported_mod in exports:
                    names_obj = st.get("names")
                    names = names_obj if isinstance(names_obj, list) else []
                    j = 0
                    while j < len(names):
                        ent = names[j]
                        if isinstance(ent, dict):
                            sym_obj = ent.get("name")
                            sym = sym_obj if isinstance(sym_obj, str) else ""
                            if sym != "" and sym not in exports[imported_mod]:
                                details.append(
                                    f"kind=missing_symbol file={file_disp} import=from {imported_mod} import {sym}"
                                )
                        j += 1
            i += 1
    if len(details) > 0:
        raise _make_user_error(
            "input_invalid",
            "import 解決に失敗しました（未定義シンボル）。",
            details,
        )


def build_module_east_map(entry_path: Path, parser_backend: str = "self_hosted") -> dict[str, dict[str, Any]]:
    """入口 + 依存ユーザーモジュールを個別に EAST 化して返す。"""
    analysis = _analyze_import_graph(entry_path)
    _validate_import_graph_or_raise(analysis)
    files_obj = analysis.get("user_module_files")
    files: list[str] = files_obj if isinstance(files_obj, list) else []
    out: dict[str, dict[str, Any]] = {}
    i = 0
    while i < len(files):
        f = files[i]
        if isinstance(f, str):
            p = Path(f)
            east = load_east(p, parser_backend)
            out[str(p)] = east
        i += 1
    _validate_from_import_symbols_or_raise(out, root=entry_path.parent)
    return out


def build_module_symbol_index(module_east_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """モジュール単位 EAST から公開シンボルと import alias 情報を抽出する。"""
    out: dict[str, dict[str, Any]] = {}
    for mod_path, east in module_east_map.items():
        body_obj: object = east.get("body")
        body: list[dict[str, Any]] = []
        if isinstance(body_obj, list):
            i = 0
            while i < len(body_obj):
                item = body_obj[i]
                if isinstance(item, dict):
                    body.append(item)
                i += 1
        funcs: list[str] = []
        classes: list[str] = []
        variables: list[str] = []
        i = 0
        while i < len(body):
            st = body[i]
            kind_obj: object = st.get("kind")
            kind = kind_obj if isinstance(kind_obj, str) else ""
            if kind == "FunctionDef":
                name_obj: object = st.get("name")
                if isinstance(name_obj, str) and name_obj != "":
                    funcs.append(name_obj)
            elif kind == "ClassDef":
                name_obj = st.get("name")
                if isinstance(name_obj, str) and name_obj != "":
                    classes.append(name_obj)
            elif kind == "Assign":
                targets_obj = st.get("targets")
                targets = targets_obj if isinstance(targets_obj, list) else []
                j = 0
                while j < len(targets):
                    tgt = targets[j]
                    if isinstance(tgt, dict):
                        if tgt.get("kind") == "Name":
                            name_obj = tgt.get("id")
                            if isinstance(name_obj, str) and name_obj != "" and name_obj not in variables:
                                variables.append(name_obj)
                    j += 1
            elif kind == "AnnAssign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    name_obj = tgt.get("id")
                    if isinstance(name_obj, str) and name_obj != "" and name_obj not in variables:
                        variables.append(name_obj)
            i += 1
        meta_obj: object = east.get("meta")
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        import_bindings = _meta_import_bindings(east)
        qualified_symbol_refs = _meta_qualified_symbol_refs(east)
        import_modules: dict[str, str] = {}
        import_symbols: dict[str, dict[str, str]] = {}
        if len(import_bindings) > 0:
            i = 0
            while i < len(import_bindings):
                ent = import_bindings[i]
                module_id = ent["module_id"]
                export_name = ent["export_name"]
                local_name = ent["local_name"]
                binding_kind = ent["binding_kind"]
                if binding_kind == "module":
                    import_modules[local_name] = module_id
                elif binding_kind == "symbol" and export_name != "" and len(qualified_symbol_refs) == 0:
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = module_id
                    sym_ent["name"] = export_name
                    import_symbols[local_name] = sym_ent
                i += 1
            if len(qualified_symbol_refs) > 0:
                j = 0
                while j < len(qualified_symbol_refs):
                    ref = qualified_symbol_refs[j]
                    module_id = ref["module_id"]
                    symbol = ref["symbol"]
                    local_name = ref["local_name"]
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = module_id
                    sym_ent["name"] = symbol
                    import_symbols[local_name] = sym_ent
                    j += 1
        else:
            import_modules_obj: object = meta.get("import_modules")
            import_symbols_obj: object = meta.get("import_symbols")
            import_modules_obj2 = import_modules_obj if isinstance(import_modules_obj, dict) else {}
            import_symbols_obj2 = import_symbols_obj if isinstance(import_symbols_obj, dict) else {}
            import_modules = dict(import_modules_obj2)
            import_symbols = dict(import_symbols_obj2)
        out[mod_path] = {
            "functions": funcs,
            "classes": classes,
            "variables": variables,
            "import_bindings": import_bindings,
            "import_modules": import_modules,
            "import_symbols": import_symbols,
        }
    return out


def build_module_type_schema(module_east_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """モジュール間共有用の最小型スキーマ（関数/クラス）を構築する。"""
    out: dict[str, dict[str, Any]] = {}
    for mod_path, east in module_east_map.items():
        body_obj: object = east.get("body")
        body: list[dict[str, Any]] = []
        if isinstance(body_obj, list):
            i = 0
            while i < len(body_obj):
                item = body_obj[i]
                if isinstance(item, dict):
                    body.append(item)
                i += 1
        fn_schema: dict[str, dict[str, Any]] = {}
        cls_schema: dict[str, dict[str, Any]] = {}
        i = 0
        while i < len(body):
            st = body[i]
            kind_obj: object = st.get("kind")
            kind = kind_obj if isinstance(kind_obj, str) else ""
            if kind == "FunctionDef":
                name_obj: object = st.get("name")
                if isinstance(name_obj, str) and name_obj != "":
                    arg_types_obj: object = st.get("arg_types")
                    arg_types = arg_types_obj if isinstance(arg_types_obj, dict) else {}
                    arg_order_obj: object = st.get("arg_order")
                    arg_order = arg_order_obj if isinstance(arg_order_obj, list) else []
                    ret_obj: object = st.get("return_type")
                    ret_type = ret_obj if isinstance(ret_obj, str) else "None"
                    fn_schema[name_obj] = {"arg_types": arg_types, "arg_order": arg_order, "return_type": ret_type}
            elif kind == "ClassDef":
                name_obj = st.get("name")
                if isinstance(name_obj, str) and name_obj != "":
                    fields_obj: object = st.get("field_types")
                    fields = fields_obj if isinstance(fields_obj, dict) else {}
                    cls_schema[name_obj] = {"field_types": fields}
            i += 1
        out[mod_path] = {"functions": fn_schema, "classes": cls_schema}
    return out


def _sanitize_module_label(s: str) -> str:
    out = ""
    i = 0
    while i < len(s):
        ch = s[i : i + 1]
        ok = ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9") or ch == "_"
        if ok:
            out += ch
        else:
            out += "_"
        i += 1
    if out == "":
        out = "module"
    if "0" <= out[0:1] <= "9":
        out = "_" + out
    return out


def _module_rel_label(root: Path, module_path: Path) -> str:
    root_txt = str(root)
    path_txt = str(module_path)
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", "__")
    return _sanitize_module_label(rel)


def _module_name_from_path(root: Path, module_path: Path) -> str:
    root_txt = str(root)
    path_txt = str(module_path)
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", ".")
    if rel.endswith(".__init__"):
        rel = rel[: -9]
    return rel


def _write_multi_file_cpp(
    *,
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
) -> dict[str, Any]:
    """モジュールごとに `.h/.cpp` を `out/include`, `out/src` へ出力する。"""
    include_dir = output_dir / "include"
    src_dir = output_dir / "src"
    include_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)
    prelude_hdr = include_dir / "pytra_multi_prelude.h"
    prelude_hdr.write_text(
        "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        "#ifndef PYTRA_MULTI_PRELUDE_H\n"
        "#define PYTRA_MULTI_PRELUDE_H\n\n"
        "#include \"runtime/cpp/pytra/built_in/py_runtime.h\"\n\n"
        "#endif  // PYTRA_MULTI_PRELUDE_H\n",
        encoding="utf-8",
    )

    root = entry_path.parent
    entry_key = str(entry_path)
    files_obj = module_east_map.keys()
    files = list(files_obj)
    files.sort()
    module_ns_map: dict[str, str] = {}
    module_label_map: dict[str, str] = {}
    i = 0
    while i < len(files):
        mod_key = files[i]
        mod_path = Path(mod_key)
        label = _module_rel_label(root, mod_path)
        module_label_map[mod_key] = label
        mod_name = _module_name_from_path(root, mod_path)
        if mod_name != "":
            module_ns_map[mod_name] = "pytra_mod_" + label
        i += 1

    symbol_index = build_module_symbol_index(module_east_map)
    type_schema = build_module_type_schema(module_east_map)

    def _inject_after_includes(cpp_text: str, block: str) -> str:
        if block == "":
            return cpp_text
        pos = cpp_text.find("\n\n")
        if pos < 0:
            return cpp_text + "\n" + block + "\n"
        head = cpp_text[: pos + 2]
        tail = cpp_text[pos + 2 :]
        return head + block + "\n" + tail

    manifest: dict[str, Any] = {}
    manifest["entry"] = entry_key
    manifest["include_dir"] = str(include_dir)
    manifest["src_dir"] = str(src_dir)
    manifest["modules"] = []

    i = 0
    while i < len(files):
        mod_key = files[i]
        east = module_east_map[mod_key]
        mod_path = Path(mod_key)
        label = module_label_map[mod_key]
        hdr_path = include_dir / (label + ".h")
        cpp_path = src_dir / (label + ".cpp")
        guard = "PYTRA_MULTI_" + _sanitize_module_label(label).upper() + "_H"
        hdr_text = (
            "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
            "#ifndef " + guard + "\n"
            "#define " + guard + "\n\n"
            "namespace pytra_multi {\n"
            "void module_" + label + "();\n"
            "}  // namespace pytra_multi\n\n"
            "#endif  // " + guard + "\n"
        )
        hdr_path.write_text(hdr_text, encoding="utf-8")

        is_entry = mod_key == entry_key
        cpp_txt = transpile_to_cpp(
            east,
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
            module_ns_map,
        )
        # multi-file モードでは共通 prelude を使い、ランタイム include 重複を避ける。
        cpp_txt = cpp_txt.replace(
            '#include "runtime/cpp/pytra/built_in/py_runtime.h"',
            '#include "pytra_multi_prelude.h"',
            1,
        )
        # ユーザーモジュール import 呼び出しを解決するため、参照先関数の前方宣言を補う。
        meta_obj = east.get("meta")
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        type_emitter = CppEmitter(
            east,
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
            {},
        )
        import_modules_obj = meta.get("import_modules")
        import_modules = import_modules_obj if isinstance(import_modules_obj, dict) else {}
        import_symbols_obj = meta.get("import_symbols")
        import_symbols = import_symbols_obj if isinstance(import_symbols_obj, dict) else {}
        dep_modules: set[str] = set()
        for _alias, mod_name_obj in import_modules.items():
            if isinstance(mod_name_obj, str) and mod_name_obj != "":
                dep_modules.add(mod_name_obj)
        for _alias, sym_obj in import_symbols.items():
            sym = sym_obj if isinstance(sym_obj, dict) else {}
            mod_name_obj = sym.get("module")
            if isinstance(mod_name_obj, str) and mod_name_obj != "":
                dep_modules.add(mod_name_obj)
        fwd_lines: list[str] = []
        for mod_name in dep_modules:
            if mod_name not in module_ns_map:
                continue
            target_ns = module_ns_map[mod_name]
            target_key = ""
            for k2, p2 in module_east_map.items():
                if _module_name_from_path(root, Path(k2)) == mod_name:
                    target_key = k2
                    break
            if target_key == "":
                continue
            target_schema_obj = type_schema.get(target_key)
            target_schema = target_schema_obj if isinstance(target_schema_obj, dict) else {}
            funcs_obj = target_schema.get("functions")
            funcs = funcs_obj if isinstance(funcs_obj, dict) else {}
            # `main` は他モジュールから呼ばれない前提。
            fn_decls: list[str] = []
            for fn_name, sig_obj in funcs.items():
                if not isinstance(fn_name, str) or fn_name == "main":
                    continue
                sig = sig_obj if isinstance(sig_obj, dict) else {}
                ret_obj = sig.get("return_type")
                ret_t = ret_obj if isinstance(ret_obj, str) else "None"
                if ret_t == "None":
                    ret_cpp = "void"
                else:
                    ret_cpp = type_emitter._cpp_type_text(ret_t)
                arg_types_obj = sig.get("arg_types")
                arg_types = arg_types_obj if isinstance(arg_types_obj, dict) else {}
                arg_order_obj = sig.get("arg_order")
                arg_order = arg_order_obj if isinstance(arg_order_obj, list) else []
                parts: list[str] = []
                j = 0
                while j < len(arg_order):
                    an = arg_order[j]
                    if not isinstance(an, str):
                        j += 1
                        continue
                    at_obj = arg_types.get(an)
                    at = at_obj if isinstance(at_obj, str) else "object"
                    at_cpp = type_emitter._cpp_type_text(at)
                    parts.append(at_cpp + " " + an)
                    j += 1
                sep = ", "
                fn_decls.append("    " + ret_cpp + " " + fn_name + "(" + sep.join(parts) + ");")
            if len(fn_decls) > 0:
                fwd_lines.append("namespace " + target_ns + " {")
                fwd_lines.extend(fn_decls)
                fwd_lines.append("}  // namespace " + target_ns)
        if len(fwd_lines) > 0:
            cpp_txt = _inject_after_includes(cpp_txt, _join_str_list("\n", fwd_lines))
        cpp_path.write_text(cpp_txt, encoding="utf-8")

        modules_obj = manifest.get("modules")
        modules = modules_obj if isinstance(modules_obj, list) else []
        modules.append(
            {
                "module": mod_key,
                "label": label,
                "header": str(hdr_path),
                "source": str(cpp_path),
                "is_entry": is_entry,
            }
        )
        manifest["modules"] = modules
        i += 1

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    return manifest


def _resolve_user_module_path(module_name: str, search_root: Path) -> Path | None:
    """ユーザーモジュール名を `search_root` 基準で `.py` パスへ解決する。"""
    if module_name.startswith("pytra.") or module_name == "pytra":
        return None
    rel = module_name.replace(".", "/")
    cand_py = search_root / (rel + ".py")
    if cand_py.exists():
        return cand_py
    cand_pkg = search_root / rel / "__init__.py"
    if cand_pkg.exists():
        return cand_pkg
    return None


def resolve_module_name(raw_name: str, root_dir: Path) -> dict[str, Any]:
    """モジュール名を `user/pytra/known/missing/relative` に分類して解決する。"""
    out: dict[str, Any] = {}
    out["status"] = "missing"
    out["module_id"] = raw_name
    out["path"] = None
    if raw_name.startswith("."):
        out["status"] = "relative"
        return out
    if _is_pytra_module_name(raw_name):
        out["status"] = "pytra"
        return out
    dep_file = _resolve_user_module_path(raw_name, root_dir)
    if dep_file is not None:
        out["status"] = "user"
        out["path"] = dep_file
        mod_id = _module_name_from_path(root_dir, dep_file)
        out["module_id"] = mod_id if mod_id != "" else raw_name
        return out
    if _is_known_non_user_import(raw_name):
        out["status"] = "known"
        return out
    return out


def dump_deps_graph_text(entry_path: Path) -> str:
    """入力 `.py` から辿れるユーザーモジュール依存グラフを整形して返す。"""
    analysis = _analyze_import_graph(entry_path)
    return _format_import_graph_report(analysis)


def print_user_error(err_text: str) -> None:
    """分類済みユーザーエラーをカテゴリ別に表示する。"""
    parsed_err = _parse_user_error(err_text)
    cat = str(parsed_err.get("category", ""))
    details: list[str] = []
    raw_details = parsed_err.get("details", [])
    if isinstance(raw_details, list):
        for item in raw_details:
            if isinstance(item, str):
                details.append(str(item))
    if cat == "":
        print("error: 変換に失敗しました。", file=sys.stderr)
        print("[transpile_error] 入力コードまたはサポート状況を確認してください。", file=sys.stderr)
        return
    if cat == "user_syntax_error":
        print("error: 入力 Python の文法エラーです。", file=sys.stderr)
        print("[user_syntax_error] 構文を修正してください。", file=sys.stderr)
    elif cat == "unsupported_by_design":
        print("error: 言語仕様上サポート対象外の構文です。", file=sys.stderr)
        print("[unsupported_by_design] 仕様に沿った書き方へ変更してください。", file=sys.stderr)
    elif cat == "not_implemented":
        print("error: まだ未実装の構文です。", file=sys.stderr)
        print("[not_implemented] TODO の実装状況を確認してください。", file=sys.stderr)
    elif cat == "input_invalid":
        print("error: 入力ファイル形式が不正です。", file=sys.stderr)
        print("[input_invalid] .py か正しい EAST JSON を指定してください。", file=sys.stderr)
    else:
        print("error: 変換に失敗しました。", file=sys.stderr)
        print(f"[{cat}] 入力コードまたはサポート状況を確認してください。", file=sys.stderr)
    for line in details:
        if line != "":
            print(line, file=sys.stderr)


def _dict_str_get(src: dict[str, str], key: str, default_value: str = "") -> str:
    """`dict[str, str]` から文字列値を安全に取得する。"""
    if key in src:
        return src[key]
    return default_value


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
    parse_err = _dict_str_get(parsed, "__error", "")
    if parse_err != "":
        print(f"error: {parse_err}", file=sys.stderr)
        return 1
    input_txt = _dict_str_get(parsed, "input", "")
    output_txt = _dict_str_get(parsed, "output", "")
    header_output_txt = _dict_str_get(parsed, "header_output", "")
    output_dir_txt = _dict_str_get(parsed, "output_dir", "")
    top_namespace_opt = _dict_str_get(parsed, "top_namespace_opt", "")
    negative_index_mode_opt = _dict_str_get(parsed, "negative_index_mode_opt", "")
    bounds_check_mode_opt = _dict_str_get(parsed, "bounds_check_mode_opt", "")
    floor_div_mode_opt = _dict_str_get(parsed, "floor_div_mode_opt", "")
    mod_mode_opt = _dict_str_get(parsed, "mod_mode_opt", "")
    int_width_opt = _dict_str_get(parsed, "int_width_opt", "")
    str_index_mode_opt = _dict_str_get(parsed, "str_index_mode_opt", "")
    str_slice_mode_opt = _dict_str_get(parsed, "str_slice_mode_opt", "")
    opt_level_opt = _dict_str_get(parsed, "opt_level_opt", "")
    preset = _dict_str_get(parsed, "preset", "")
    parser_backend = _dict_str_get(parsed, "parser_backend", "self_hosted")
    no_main = _dict_str_get(parsed, "no_main", "0") == "1"
    single_file = _dict_str_get(parsed, "single_file", "1") == "1"
    output_mode_explicit = _dict_str_get(parsed, "output_mode_explicit", "0") == "1"
    dump_deps = _dict_str_get(parsed, "dump_deps", "0") == "1"
    dump_options = _dict_str_get(parsed, "dump_options", "0") == "1"
    emit_runtime_cpp = _dict_str_get(parsed, "emit_runtime_cpp", "0") == "1"
    show_help = _dict_str_get(parsed, "help", "0") == "1"
    negative_index_mode = ""
    bounds_check_mode = ""
    floor_div_mode = ""
    mod_mode = ""
    int_width = ""
    str_index_mode = ""
    str_slice_mode = ""
    opt_level = ""

    if show_help:
        print(
            "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--header-output OUTPUT.h] [--emit-runtime-cpp] [--output-dir DIR] [--single-file|--multi-file] [--top-namespace NS] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]",
            file=sys.stderr,
        )
        return 0
    if input_txt == "":
        print(
            "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--header-output OUTPUT.h] [--emit-runtime-cpp] [--output-dir DIR] [--single-file|--multi-file] [--top-namespace NS] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]",
            file=sys.stderr,
        )
        return 1
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
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(options_text, encoding="utf-8")
        else:
            print(options_text, end="")
        return 0

    cpp = ""
    try:
        module_east_map_cache: dict[str, dict[str, Any]] = {}
        if input_txt.endswith(".py") and not (emit_runtime_cpp and _is_runtime_emit_input_path(input_path)):
            analysis = _analyze_import_graph(input_path)
            _validate_import_graph_or_raise(analysis)
            module_east_map_cache = build_module_east_map(input_path, parser_backend)
        east_module: dict[str, Any]
        if input_txt.endswith(".py") and input_txt in module_east_map_cache:
            east_module = module_east_map_cache[input_txt]
        else:
            east_module = load_east(input_path, parser_backend)
        if dump_deps:
            dep_text = dump_deps_text(east_module)
            if input_txt.endswith(".py"):
                dep_text += dump_deps_graph_text(input_path)
            if output_txt != "":
                out_path = Path(output_txt)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(dep_text, encoding="utf-8")
            else:
                print(dep_text, end="")
            return 0
        if emit_runtime_cpp:
            if not input_txt.endswith(".py"):
                print("error: --emit-runtime-cpp requires .py input", file=sys.stderr)
                return 1
            module_tail = _runtime_module_tail_from_source_path(input_path)
            if module_tail == "":
                print("error: --emit-runtime-cpp input must be under src/pytra/utils/ or src/pytra/std/", file=sys.stderr)
                return 1
            if module_tail.endswith("_impl"):
                print("skip: impl module is hand-written on C++ side: " + module_tail)
                return 0
            ns = top_namespace_opt
            if ns == "":
                ns = _runtime_namespace_for_tail(module_tail)
            rel_tail = _runtime_output_rel_tail(module_tail)
            out_root = Path("src/runtime/cpp/pytra")
            cpp_out = out_root / (rel_tail + ".cpp")
            hdr_out = out_root / (rel_tail + ".h")
            cpp_out.parent.mkdir(parents=True, exist_ok=True)
            hdr_out.parent.mkdir(parents=True, exist_ok=True)
            runtime_ns_map: dict[str, str] = {}
            cpp_txt_runtime: str = transpile_to_cpp(
                east_module,
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
                runtime_ns_map,
            )
            own_runtime_header = '#include "pytra/' + rel_tail + '.h"'
            if own_runtime_header not in cpp_txt_runtime:
                cpp_txt_runtime = cpp_txt_runtime.replace(
                    '#include "runtime/cpp/pytra/built_in/py_runtime.h"\n',
                    '#include "runtime/cpp/pytra/built_in/py_runtime.h"\n\n' + own_runtime_header + "\n",
                    1,
                )
            hdr_txt_runtime = build_cpp_header_from_east(east_module, ns, input_path, hdr_out)
            cpp_out.write_text(cpp_txt_runtime, encoding="utf-8")
            hdr_out.write_text(hdr_txt_runtime, encoding="utf-8")
            print("generated: " + str(hdr_out))
            print("generated: " + str(cpp_out))
            return 0
        if single_file:
            empty_ns: dict[str, str] = {}
            cpp = transpile_to_cpp(
                east_module,
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
                empty_ns,
            )
            if header_output_txt != "":
                hdr_path = Path(header_output_txt)
                hdr_path.parent.mkdir(parents=True, exist_ok=True)
                hdr_txt = build_cpp_header_from_east(east_module, top_namespace_opt, input_path, hdr_path)
                hdr_path.write_text(hdr_txt, encoding="utf-8")
        else:
            module_east_map: dict[str, dict[str, Any]] = {}
            if input_txt.endswith(".py"):
                if len(module_east_map_cache) > 0:
                    module_east_map = module_east_map_cache
                else:
                    module_east_map = build_module_east_map(input_path, parser_backend)
            else:
                module_east_map[str(input_path)] = east_module
            out_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out")
            if output_txt != "":
                out_dir = Path(output_txt)
            mf = _write_multi_file_cpp(
                entry_path=input_path,
                module_east_map=module_east_map,
                output_dir=out_dir,
                negative_index_mode=negative_index_mode,
                bounds_check_mode=bounds_check_mode,
                floor_div_mode=floor_div_mode,
                mod_mode=mod_mode,
                int_width=int_width,
                str_index_mode=str_index_mode,
                str_slice_mode=str_slice_mode,
                opt_level=opt_level,
                top_namespace=top_namespace_opt,
                emit_main=not no_main,
            )
            msg = "multi-file output generated at: " + str(out_dir)
            manifest_txt = mf.get("manifest")
            if isinstance(manifest_txt, str) and manifest_txt != "":
                msg += "\nmanifest: " + manifest_txt + "\n"
            else:
                msg += "\n"
            print(msg, end="")
            return 0
    except Exception as ex:
        parsed_err = _parse_user_error(str(ex))
        cat = str(parsed_err.get("category", ""))
        if cat != "":
            print_user_error(str(ex))
            return 1
        print("error: 変換中に内部エラーが発生しました。", file=sys.stderr)
        print("[internal_error] バグの可能性があります。再現コードを添えて報告してください。", file=sys.stderr)
        return 1

    if output_txt != "":
        out_path = Path(output_txt)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cpp, encoding="utf-8")
    else:
        print(cpp)
    return 0


if __name__ == "__main__":
    sys.exit(main(list(sys.argv[1:])))

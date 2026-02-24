"""C++ profile loading and operator/rule helpers."""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.compiler.transpile_cli import dict_any_get_dict, dict_any_get_str, dict_any_get_list
from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks as _build_cpp_hooks_impl


DEFAULT_BIN_OPS: dict[str, str] = {
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

DEFAULT_CMP_OPS: dict[str, str] = {
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

DEFAULT_AUG_OPS: dict[str, str] = {
    "Add": "+=",
    "Sub": "-=",
    "Mult": "*=",
    "Div": "/=",
    "FloorDiv": "/=",
    "Mod": "%",
    "BitAnd": "&=",
    "BitOr": "|=",
    "BitXor": "^=",
    "LShift": "<<=",
    "RShift": ">>=",
}

DEFAULT_AUG_BIN: dict[str, str] = {
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

AUG_BIN = dict(DEFAULT_AUG_BIN)
CMP_OPS = dict(DEFAULT_CMP_OPS)
AUG_OPS = dict(DEFAULT_AUG_OPS)
BIN_OPS = dict(DEFAULT_BIN_OPS)

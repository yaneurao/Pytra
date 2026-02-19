#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/pylib/east.py conversion.
"""

from __future__ import annotations

from pylib.std.typing import Any

from pylib.tra.east_parts.code_emitter import CodeEmitter
from common.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options
from pylib.tra.east import convert_path, convert_source_to_east_with_backend
from pylib.std import json
from pylib.std.pathlib import Path
from pylib.std import sys


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

CPP_HEADER = """#include "runtime/cpp/py_runtime.h"

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

def _default_cpp_module_attr_call_map() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    out["math"] = {
        "sqrt": "py_math::sqrt",
        "sin": "py_math::sin",
        "cos": "py_math::cos",
        "tan": "py_math::tan",
        "exp": "py_math::exp",
        "log": "py_math::log",
        "log10": "py_math::log10",
        "fabs": "py_math::fabs",
        "floor": "py_math::floor",
        "ceil": "py_math::ceil",
        "pow": "py_math::pow",
    }
    return out


_DEFAULT_CPP_MODULE_ATTR_CALL_MAP: dict[str, dict[str, str]] = _default_cpp_module_attr_call_map()
CPP_RESERVED_WORDS: list[str] = [
    "alignas", "alignof", "asm", "auto", "break", "case", "catch", "char", "class", "const", "constexpr",
    "continue", "default", "delete", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "inline", "int", "long", "namespace", "new", "operator", "private", "protected", "public", "register",
    "return", "short", "signed", "sizeof", "static", "struct", "switch", "template", "this", "throw", "try",
    "typedef", "typename", "union", "unsigned", "virtual", "void", "volatile", "while",
]

def _deep_copy_str_map(v: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for k, inner in v.items():
        out[k] = dict(inner)
    return out


def _copy_str_map(src: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in src.items():
        out[k] = v
    return out


def _map_get_str(src: dict[str, str], key: str) -> str:
    """dict[str, str] から文字列値を安全に取得する。"""
    v = src.get(key)
    if isinstance(v, str):
        return str(v)
    return ""


def load_cpp_profile() -> dict[str, Any]:
    """C++ 用 LanguageProfile を読み込む（失敗時は空 dict）。"""
    out: dict[str, Any] = {}
    out["syntax"] = {}
    return out


def load_cpp_bin_ops() -> dict[str, str]:
    """C++ 用二項演算子マップを返す。"""
    return _copy_str_map(DEFAULT_BIN_OPS)


def load_cpp_cmp_ops() -> dict[str, str]:
    """C++ 用比較演算子マップを返す。"""
    return _copy_str_map(DEFAULT_CMP_OPS)


def load_cpp_aug_ops() -> dict[str, str]:
    """C++ 用複合代入演算子マップを返す。"""
    return _copy_str_map(DEFAULT_AUG_OPS)


def load_cpp_aug_bin() -> dict[str, str]:
    """C++ 用複合代入分解時の演算子マップを返す。"""
    return _copy_str_map(DEFAULT_AUG_BIN)


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
        "Exception": "std::runtime_error",
        "Any": "object",
        "object": "object",
    }


def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """C++ 用 hooks 設定を返す（現状は no-op）。"""
    _ = profile
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
    _ = profile
    return _deep_copy_str_map(_DEFAULT_CPP_MODULE_ATTR_CALL_MAP)


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
        emit_main: bool = True,
    ) -> None:
        """変換設定とクラス解析用の状態を初期化する。"""
        profile = load_cpp_profile()
        hooks = load_cpp_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        self.negative_index_mode = negative_index_mode
        self.bounds_check_mode = bounds_check_mode
        self.floor_div_mode = floor_div_mode
        self.mod_mode = mod_mode
        self.int_width = int_width
        self.str_index_mode = str_index_mode
        self.str_slice_mode = str_slice_mode
        self.opt_level = opt_level
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
        self.bridge_comment_emitted: set[str] = set()
        self.type_map: dict[str, str] = load_cpp_type_map()
        if self.int_width == "32":
            self.type_map["int64"] = "int32"
            self.type_map["uint64"] = "uint32"
        self.module_attr_call_map: dict[str, dict[str, str]] = load_cpp_module_attr_call_map(self.profile)
        self.reserved_words: set[str] = set()
        self.rename_prefix: str = "py_"
        self.reserved_words, self.rename_prefix = load_cpp_identifier_rules()
        self.import_modules: dict[str, str] = {}
        self.import_symbols: dict[str, dict[str, str]] = {}

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
        return runtime_call.startswith("std::")

    def _resolve_imported_module_name(self, name: str) -> str:
        """import で束縛された識別子名を実モジュール名へ解決する。"""
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
        return name

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
        out: dict[str, str] = {}
        return out

    def _resolve_runtime_call_for_imported_symbol(self, module_name: str, symbol_name: str) -> str | None:
        """`from X import Y` で取り込まれた Y 呼び出しの runtime 名を返す。"""
        if module_name in self.module_attr_call_map:
            owner_map = self.module_attr_call_map[module_name]
            if symbol_name in owner_map:
                mapped = owner_map[symbol_name]
                if mapped != "":
                    return mapped
        if module_name == "pylib.tra.png" and symbol_name == "write_rgb_png":
            return "png_helper::write_rgb_png"
        if module_name == "pylib.tra.gif" and symbol_name == "save_gif":
            return "save_gif"
        if module_name == "time" and symbol_name == "perf_counter":
            return "perf_counter"
        if module_name == "pathlib" and symbol_name == "Path":
            return "Path"
        if module_name == "pylib.tra.assertions" and symbol_name.startswith("py_assert_"):
            return symbol_name
        return None

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
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
        self.emit("")

        for stmt in body:
            self.emit_stmt(stmt)
            self.emit("")

        if self.emit_main:
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
            self.emit_stmt_list(main_guard)
            self.scope_stack.pop()
            self.emit("return 0;")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        out: str = ""
        i = 0
        while i < len(self.lines):
            if i > 0:
                out += NEWLINE_CHAR
            out += self.lines[i]
            i += 1
        return out

    def apply_cast(self, rendered_expr: str, to_type: Any) -> str:
        """EAST の cast 指示に従い C++ 側の明示キャストを適用する。"""
        to_type_text = ""
        if isinstance(to_type, str):
            to_type_text = to_type
        if to_type_text == "byte":
            to_type_text = "uint8"
        if to_type_text == "":
            return rendered_expr
        return f"static_cast<{to_type_text}>({rendered_expr})"

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
            return f"std::to_string({rendered})"
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
            return f" {op} ".join(wrapped_values)

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
    ) -> str | None:
        """1文字比較を `'x'` / `.at(i)` 形へ最適化できるか判定する。"""
        if not self._opt_ge(3):
            return None
        if op not in {"Eq", "NotEq"}:
            return None
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
        return None

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

    def render_minmax(self, fn: str, args: list[str], out_type: str) -> str:
        """min/max 呼び出しを型情報付きで C++ 式へ変換する。"""
        if len(args) == 0:
            return "/* invalid min/max */"
        if len(args) == 1:
            return args[0]
        t = "auto"
        if out_type != "":
            t = self._cpp_type_text(out_type)
        if t == "auto":
            call = f"py_{fn}({args[0]}, {args[1]})"
            for a in args[2:]:
                call = f"py_{fn}({call}, {a})"
            return call
        casted = [f"static_cast<{t}>({a})" for a in args]
        call = f"std::{fn}<{t}>({casted[0]}, {casted[1]})"
        for a in casted[2:]:
            call = f"std::{fn}<{t}>({call}, {a})"
        return call

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
        val_is_dict: bool = isinstance(stmt.get("value"), dict)
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
                rendered_val = f"{t}{{{', '.join(items)}}}"
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
                # Keep as-is for selfhost stability; list-comp explicit typing can be improved later.
                rendered_val = rendered_val
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
        op_txt = _map_get_str(AUG_OPS, op_name)
        if op_txt != "":
            op = op_txt
        if _map_get_str(AUG_BIN, op_name) != "":
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
            for ent in self._dict_stmt_list(stmt.get("names")):
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
            for ent in self._dict_stmt_list(stmt.get("names")):
                name = self.any_to_str(ent.get("name"))
                asname = self.any_to_str(ent.get("asname"))
                if mod == "" or name == "":
                    continue
                if asname != "":
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = mod
                    sym_ent["name"] = name
                    self.import_symbols[asname] = sym_ent
                else:
                    sym_ent: dict[str, str] = {}
                    sym_ent["module"] = mod
                    sym_ent["name"] = name
                    self.import_symbols[name] = sym_ent
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
        self.emit(f"std::swap({left}, {right});")

    def _emit_raise_stmt(self, stmt: dict[str, Any]) -> None:
        if not isinstance(stmt.get("exc"), dict):
            self.emit('throw std::runtime_error("raise");')
        else:
            self.emit(f"throw {self.render_expr(stmt.get('exc'))};")

    def _emit_function_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_function(stmt, False)

    def _emit_class_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_class(stmt)

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        value_is_dict: bool = isinstance(stmt.get("value"), dict)
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
        v_is_dict: bool = isinstance(stmt.get("value"), dict)
        if not v_is_dict:
            self.emit("return;")
            return
        self.emit(f"return {self.render_expr(stmt.get('value'))};")

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
            self.emit(f"catch (const std::exception& {name}) {{")
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
        k = str(filtered[0].get("kind", ""))
        return k in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}

    def emit_assign(self, stmt: dict[str, Any]) -> None:
        """代入文（通常代入/タプル代入）を C++ へ出力する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        value = self.any_to_dict_or_empty(stmt.get("value"))
        if len(target) == 0 or len(value) == 0:
            self.emit("/* invalid assign */")
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
                    self.emit(f"std::swap({self.render_lvalue(lhs_elems[0])}, {self.render_lvalue(lhs_elems[1])});")
                    return
            tmp = self.next_tmp("__tuple")
            self.emit(f"auto {tmp} = {self.render_expr(stmt.get('value'))};")
            tuple_elem_types: list[str] = []
            value_t = self.get_expr_type(stmt.get("value"))
            if isinstance(value_t, str) and value_t.startswith("tuple[") and value_t.endswith("]"):
                tuple_elem_types = self.split_generic(value_t[6:-1])
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
                        self.emit(f"{decl_t} {lhs} = std::get<{i}>({tmp});")
                        continue
                self.emit(f"{lhs} = std::get<{i}>({tmp});")
            return
        texpr = self.render_lvalue(stmt.get("target"))
        if self.is_plain_name_expr(stmt.get("target")) and not self.is_declared(texpr):
            d0 = str(stmt.get("decl_type", ""))
            d1 = self.get_expr_type(stmt.get("target"))
            d2 = self.get_expr_type(stmt.get("value"))
            picked = d0 if d0 != "" else (d1 if d1 != "" else d2)
            dtype = self._cpp_type_text(picked)
            self.declare_in_current_scope(texpr)
            rval = self.render_expr(stmt.get("value"))
            if dtype == "uint8" and isinstance(value, dict):
                byte_val = self._byte_from_str_expr(stmt.get("value"))
                if byte_val != "":
                    rval = str(byte_val)
            if isinstance(value, dict) and value.get("kind") == "BoolOp" and picked != "bool":
                rval = self.render_boolop(stmt.get("value"), True)
            if self.is_any_like_type(picked):
                if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                    rval = "object{}"
                elif not rval.startswith("make_object("):
                    rval = f"make_object({rval})"
            self.emit(f"{dtype} {texpr} = {rval};")
            return
        rval = self.render_expr(stmt.get("value"))
        t_target = self.get_expr_type(stmt.get("target"))
        if t_target == "uint8" and isinstance(value, dict):
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rval = str(byte_val)
        if isinstance(value, dict) and value.get("kind") == "BoolOp" and t_target != "bool":
            rval = self.render_boolop(stmt.get("value"), True)
        if self.is_any_like_type(t_target):
            if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                rval = "object{}"
            elif not rval.startswith("make_object("):
                rval = f"make_object({rval})"
        self.emit(f"{texpr} = {rval};")

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
        if val_ty.startswith("dict["):
            return f"{val}[{idx}]"
        if self.is_indexable_sequence_type(val_ty):
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
                self.emit(f"auto {nm} = std::get<{i}>({src});")

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
        ret = self.cpp_type(stmt.get("return_type"))
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_index = self.any_to_dict_or_empty(stmt.get("arg_index"))
        params: list[str] = []
        fn_scope: set[str] = set()
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "" and raw_n in arg_types:
                arg_names.append(raw_n)
        if len(arg_names) == 0:
            remaining: list[str] = []
            for raw_n in arg_types.keys():
                if isinstance(raw_n, str):
                    remaining.append(raw_n)
            while len(remaining) > 0:
                best_name = ""
                best_idx = 1000000000
                for n in remaining:
                    idx = self.any_dict_get_int(arg_index, n, 1000000000)
                    if idx < best_idx or (idx == best_idx and (best_name == "" or n < best_name)):
                        best_idx = idx
                        best_name = n
                if best_name == "":
                    break
                arg_names.append(best_name)
                next_remaining: list[str] = []
                for n in remaining:
                    if n != best_name:
                        next_remaining.append(n)
                remaining = next_remaining
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
            if self.current_class_base_name == "CodeEmitter":
                self.emit(f"{self.current_class_name}({', '.join(params)}) : CodeEmitter(east_doc, load_cpp_profile(), dict<str, object>{{}}) {{")
            else:
                self.emit_ctor_open(str(self.current_class_name), ", ".join(params))
        elif in_class and name == "__del__" and self.current_class_name is not None:
            self.emit_dtor_open(str(self.current_class_name))
        else:
            self.emit_function_open(ret, str(name), ", ".join(params))
        docstring = self.any_to_str(stmt.get("docstring"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        if docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(body_stmts)
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
            base_txt = " : " + ", ".join(bases)
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
            self.emit(f"{name}({', '.join(params)}) {{")
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
            if on == "left":
                left = self.apply_cast(left, c.get("to"))
            elif on == "right":
                right = self.apply_cast(right, c.get("to"))
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
        op_txt = _map_get_str(BIN_OPS, op_name_str)
        if op_txt != "":
            op = op_txt
        return f"{left} {op} {right}"

    def _render_builtin_call(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        first_arg: Any,
    ) -> str:
        """lowered_kind=BuiltinCall の呼び出しを処理する。"""
        runtime_call = self.any_dict_get_str(expr, "runtime_call", "")
        builtin_name = self.any_dict_get_str(expr, "builtin_name", "")
        if runtime_call == "py_print":
            return f"py_print({', '.join(args)})"
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
            if runtime_call in {"py_min", "py_max"} and len(args) >= 1:
                fn_name = "min" if runtime_call == "py_min" else "max"
                return self.render_minmax(fn_name, args, self.any_to_str(expr.get("resolved_type")))
        if runtime_call == "perf_counter":
            return "perf_counter()"
        if runtime_call == "open":
            return f"open({', '.join(args)})"
        if runtime_call == "py_int_to_bytes":
            owner = self.render_expr(fn.get("value"))
            length = args[0] if len(args) >= 1 else "0"
            byteorder = args[1] if len(args) >= 2 else '"little"'
            return f"py_int_to_bytes({owner}, {length}, {byteorder})"
        if runtime_call == "write_rgb_png":
            return f"png_helper::write_rgb_png({', '.join(args)})"
        if runtime_call == "grayscale_palette":
            return "grayscale_palette()"
        if runtime_call == "save_gif":
            path = args[0] if len(args) >= 1 else '""'
            w = args[1] if len(args) >= 2 else "0"
            h = args[2] if len(args) >= 3 else "0"
            frames = args[3] if len(args) >= 4 else "list<list<uint8>>{}"
            palette = args[4] if len(args) >= 5 else "grayscale_palette()"
            if palette in {"nullptr", "std::nullopt"}:
                palette = "grayscale_palette()"
            delay_cs = kw.get("delay_cs", "4")
            loop = kw.get("loop", "0")
            return f"save_gif({path}, {w}, {h}, {frames}, {palette}, {delay_cs}, {loop})"
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
            return f"py_join({owner}, {args[0]})"
        if runtime_call == "std::runtime_error":
            if len(args) == 0:
                return 'std::runtime_error("error")'
            return f"std::runtime_error({args[0]})"
        if runtime_call == "Path":
            return f"Path({', '.join(args)})"
        if runtime_call == "std::filesystem::create_directories":
            owner_node = self.any_to_dict_or_empty(fn.get("value"))
            owner = self.render_expr(fn.get("value"))
            if len(owner_node) > 0 and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            parents = kw.get("parents", "false")
            exist_ok = kw.get("exist_ok", "false")
            if len(args) >= 1:
                parents = args[0]
            if len(args) >= 2:
                exist_ok = args[1]
            return f"{owner}.mkdir({parents}, {exist_ok})"
        if runtime_call == "std::filesystem::exists":
            owner_node = self.any_to_dict_or_empty(fn.get("value"))
            owner = self.render_expr(fn.get("value"))
            if len(owner_node) > 0 and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            return f"{owner}.exists()"
        if runtime_call == "py_write_text":
            owner_node = self.any_to_dict_or_empty(fn.get("value"))
            owner = self.render_expr(fn.get("value"))
            if len(owner_node) > 0 and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            write_arg = args[0] if len(args) >= 1 else '""'
            return f"{owner}.write_text({write_arg})"
        if runtime_call == "py_read_text":
            owner_node = self.any_to_dict_or_empty(fn.get("value"))
            owner = self.render_expr(fn.get("value"))
            if len(owner_node) > 0 and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            return f"{owner}.read_text()"
        if runtime_call == "path_parent":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.parent()"
        if runtime_call == "path_name":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.name()"
        if runtime_call == "path_stem":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.stem()"
        if runtime_call == "identity":
            owner = self.render_expr(fn.get("value"))
            return owner
        if runtime_call == "list.append":
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "/* missing */"
            return f"{owner}.append({a0})"
        if runtime_call == "list.extend":
            owner = self.render_expr(fn.get("value"))
            a0 = args[0] if len(args) >= 1 else "{}"
            return f"{owner}.insert({owner}.end(), {a0}.begin(), {a0}.end())"
        if runtime_call == "list.pop":
            owner = self.render_expr(fn.get("value"))
            if len(args) == 0:
                return f"py_pop({owner})"
            return f"py_pop({owner}, {args[0]})"
        if runtime_call == "list.clear":
            owner = self.render_expr(fn.get("value"))
            return f"{owner}.clear()"
        if runtime_call == "list.reverse":
            owner = self.render_expr(fn.get("value"))
            return f"std::reverse({owner}.begin(), {owner}.end())"
        if runtime_call == "list.sort":
            owner = self.render_expr(fn.get("value"))
            return f"std::sort({owner}.begin(), {owner}.end())"
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
        if runtime_call != "" and self._is_std_runtime_call(runtime_call):
            return f"{runtime_call}({', '.join(args)})"
        if builtin_name == "bytes":
            return f"bytes({', '.join(args)})" if len(args) >= 1 else "bytes{}"
        if builtin_name == "bytearray":
            return f"bytearray({', '.join(args)})" if len(args) >= 1 else "bytearray{}"
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
                if isinstance(mapped_runtime, str) and mapped_runtime not in {"perf_counter", "save_gif", "Path"}:
                    return f"{mapped_runtime}({', '.join(args)})"
            if raw == "range":
                raise RuntimeError("unexpected raw range Call in EAST; expected RangeExpr lowering")
            if isinstance(raw, str) and raw in self.ref_classes:
                return f"::rc_new<{raw}>({', '.join(args)})"
            if raw == "print":
                return f"py_print({', '.join(args)})"
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
            if raw == "list" and len(args) == 0:
                t = self.cpp_type(expr.get("resolved_type"))
                return f"{t}{{}}"
            if raw == "dict" and len(args) == 0:
                t = self.cpp_type(expr.get("resolved_type"))
                return f"{t}{{}}"
            if raw == "bytes":
                return f"bytes({', '.join(args)})" if len(args) >= 1 else "bytes{}"
            if raw == "bytearray":
                return f"bytearray({', '.join(args)})" if len(args) >= 1 else "bytearray{}"
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
                if raw == "int" and target == "int64" and arg_t == "str":
                    return f"py_to_int64({args[0]})"
                if raw == "int" and target == "int64" and arg_t in numeric_t:
                    return f"int64({args[0]})"
                if raw == "int" and target == "int64":
                    return f"py_to_int64({args[0]})"
                return f"static_cast<{target}>({args[0]})"
            if raw in {"min", "max"} and len(args) >= 1:
                return self.render_minmax(raw, args, self.any_to_str(expr.get("resolved_type")))
            if raw == "perf_counter":
                return "perf_counter()"
            if raw in {"Exception", "RuntimeError"}:
                if len(args) == 0:
                    return 'std::runtime_error("error")'
                return f"std::runtime_error({args[0]})"
            if raw == "Path":
                return f"Path({', '.join(args)})"
            if raw == "save_gif":
                path = args[0] if len(args) >= 1 else '""'
                w = args[1] if len(args) >= 2 else "0"
                h = args[2] if len(args) >= 3 else "0"
                frames = args[3] if len(args) >= 4 else "list<bytearray>{}"
                palette = args[4] if len(args) >= 5 else "grayscale_palette()"
                delay_cs = kw.get("delay_cs", args[5] if len(args) >= 6 else "4")
                loop = kw.get("loop", args[6] if len(args) >= 7 else "0")
                return f"save_gif({path}, {w}, {h}, {frames}, {palette}, {delay_cs}, {loop})"
        if fn_kind == "Attribute":
            attr_rendered_txt = ""
            attr_rendered = self._render_call_attribute(expr, fn, args, kw)
            if isinstance(attr_rendered, str):
                attr_rendered_txt = str(attr_rendered)
            if attr_rendered_txt != "":
                return attr_rendered_txt
        return None

    def _render_call_module_method(
        self, owner_mod: str, attr: str, args: list[str], kw: dict[str, str]
    ) -> str | None:
        """module.method(...) 呼び出しを処理する。"""
        if owner_mod in self.module_attr_call_map:
            owner_map = self.module_attr_call_map[owner_mod]
            if attr in owner_map:
                mapped = owner_map[attr]
                if mapped != "":
                    return f"{mapped}({', '.join(args)})"
        if owner_mod in {"png_helper", "png", "pylib.tra.png"} and attr == "write_rgb_png":
            return f"png_helper::write_rgb_png({', '.join(args)})"
        if owner_mod in {"gif_helper", "gif", "pylib.tra.gif"} and attr == "save_gif":
            path = args[0] if len(args) >= 1 else '""'
            w = args[1] if len(args) >= 2 else "0"
            h = args[2] if len(args) >= 3 else "0"
            frames = args[3] if len(args) >= 4 else "list<bytearray>{}"
            palette = args[4] if len(args) >= 5 else "grayscale_palette()"
            if palette in {"nullptr", "std::nullopt"}:
                palette = "grayscale_palette()"
            delay_cs = kw.get("delay_cs", args[5] if len(args) >= 6 else "4")
            loop = kw.get("loop", args[6] if len(args) >= 7 else "0")
            return f"save_gif({path}, {w}, {h}, {frames}, {palette}, {delay_cs}, {loop})"
        return None

    def _render_call_object_method(self, owner_t: str, owner_expr: str, attr: str) -> str | None:
        """obj.method(...) 呼び出しのうち、型依存の特殊ケースを処理する。"""
        if owner_t == "unknown" and attr == "clear":
            return f"{owner_expr}.clear()"
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
        owner_expr = self.render_expr(owner_obj)
        if owner.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            owner_expr = f"({owner_expr})"
        owner_mod = self._resolve_imported_module_name(owner_expr)
        attr = self.any_to_str(fn.get("attr"))
        if attr == "":
            attr = str(fn.get("attr"))
        if attr == "":
            return None
        if owner_mod == "":
            owner_mod = owner_expr
        module_rendered_txt = ""
        module_rendered = self._render_call_module_method(owner_mod, attr, args, kw)
        if isinstance(module_rendered, str):
            module_rendered_txt = str(module_rendered)
        if module_rendered_txt != "":
            return module_rendered_txt
        object_rendered_txt = ""
        object_rendered = self._render_call_object_method(owner_t, owner_expr, attr)
        if isinstance(object_rendered, str):
            object_rendered_txt = str(object_rendered)
        if object_rendered_txt != "":
            return object_rendered_txt
        return None

    def _render_call_fallback(self, fn_name: str, args: list[str]) -> str:
        """Call の最終フォールバック（通常の関数呼び出し）を返す。"""
        if fn_name == "print":
            return f"py_print({', '.join(args)})"
        return f"{fn_name}({', '.join(args)})"

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
                    return f"std::find({container}.begin(), {container}.end(), {key}) == {container}.end()"
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
                            found = f"std::find({rhs}.begin(), {rhs}.end(), {left}) != {rhs}.end()"
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
                base = f"std::find({container}.begin(), {container}.end(), {key}) != {container}.end()"
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
            cop_txt = _map_get_str(CMP_OPS, op_name)
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
                    parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) != {rhs}.end()")
            elif cop == "/* not in */":
                rhs_type0 = self.get_expr_type(rhs_node)
                rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                if rhs_type.startswith("dict["):
                    parts.append(f"{rhs}.find({cur}) == {rhs}.end()")
                elif rhs_type.startswith("tuple["):
                    parts.append(f"!py_tuple_contains({rhs}, {cur})")
                else:
                    parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) == {rhs}.end()")
            else:
                opt_cmp = self._try_optimize_char_compare(
                    cur_node,
                    op_name,
                    rhs_node,
                )
                if opt_cmp is not None:
                    parts.append(opt_cmp)
                elif op_name in {"Is", "IsNot"} and rhs == "std::nullopt":
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({cur})")
                elif op_name in {"Is", "IsNot"} and cur == "std::nullopt":
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({rhs})")
                else:
                    parts.append(f"{cur} {cop} {rhs}")
            cur = rhs
            cur_node = rhs_node
        return " && ".join(parts) if len(parts) > 0 else "true"

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
            return self._render_sequence_index(val, idx, sl)
        return f"{val}[{idx}]"

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）を C++ 式へ変換する。"""
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for c in casts:
            on = self.any_to_str(c.get("on"))
            to_t: object = c.get("to")
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
        _ = self.hook_on_render_expr_kind(kind, expr_d)
        if kind in {"JoinedStr", "Lambda", "ListComp", "SetComp", "DictComp"}:
            _ = self.hook_on_render_expr_complex(expr_d)

        if kind == "Name":
            name = str(expr_d.get("id", "_"))
            if name in self.renamed_symbols:
                return self.renamed_symbols[name]
            if name in self.reserved_words:
                renamed = f"{self.rename_prefix}{name}"
                self.renamed_symbols[name] = renamed
                return renamed
            return name
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
                    return "object{}"
                return "std::nullopt"
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
            if base_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                base = f"({base})"
            attr = expr_d.get("attr", "")
            if base == "self":
                if self.current_class_name is not None and str(attr) in self.current_class_static_fields:
                    return f"{self.current_class_name}::{attr}"
                return f"this->{attr}"
            # Class-name qualified member access in EAST uses dot syntax.
            # Emit C++ scope resolution for static members/methods.
            if base in self.class_base or base in self.class_method_names:
                return f"{base}::{attr}"
            base_module_name = self._resolve_imported_module_name(base)
            if base_module_name in {"png", "png_helper", "pylib.tra.png"} and str(attr) == "write_rgb_png":
                return "png_helper::write_rgb_png"
            if base_module_name in {"gif", "gif_helper", "pylib.tra.gif"} and str(attr) == "save_gif":
                return "save_gif"
            if base_module_name == "math":
                if attr == "pi":
                    return "py_math::pi"
                if attr == "e":
                    return "py_math::e"
            bt = self.get_expr_type(expr_d.get("value"))
            if bt in self.ref_classes:
                return f"{base}->{attr}"
            if bt == "Path":
                if attr == "name":
                    return f"{base}.name()"
                if attr == "stem":
                    return f"{base}.stem()"
                if attr == "parent":
                    return f"{base}.parent()"
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
            if self.any_to_str(fn.get("kind")) == "Attribute":
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
                builtin_rendered: str = self._render_builtin_call(expr_d, fn, args, kw, first_arg)
                if builtin_rendered != "":
                    return builtin_rendered
            name_or_attr = self._render_call_name_or_attr(expr_d, fn, fn_name, args, kw, arg_nodes, first_arg)
            name_or_attr_txt = ""
            if isinstance(name_or_attr, str):
                name_or_attr_txt = str(name_or_attr)
            if name_or_attr_txt != "":
                return name_or_attr_txt
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
            items = ", ".join(parts)
            return f"{t}{{{items}}}"
        if kind == "Tuple":
            elements = self.any_to_list(expr_d.get("elements"))
            items = ", ".join(self.render_expr(e) for e in elements)
            return f"std::make_tuple({items})"
        if kind == "Set":
            t = self.cpp_type(expr_d.get("resolved_type"))
            elements = self.any_to_list(expr_d.get("elements"))
            items = ", ".join(self.render_expr(e) for e in elements)
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
            return f"{t}{{{', '.join(items)}}}"
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
                return " + ".join(parts)
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
            return " + ".join(parts)
        if kind == "Lambda":
            arg_texts: list[str] = []
            for a in self._dict_stmt_list(expr_d.get("args")):
                nm = self.any_to_str(a.get("arg")).strip()
                if nm != "":
                    arg_texts.append(f"auto {nm}")
            body_expr = self.render_expr(expr_d.get("body"))
            return f"[&]({', '.join(arg_texts)}) {{ return {body_expr}; }}"
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
                            lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
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
                cond: str = " && ".join(cond_parts)
                lines.append(f"        if ({cond}) __out.append({elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)
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
                        lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
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
                cond: str = " && ".join(cond_parts)
                lines.append(f"        if ({cond}) __out.insert({elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)
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
                        lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
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
                cond: str = " && ".join(cond_parts)
                lines.append(f"        if ({cond}) __out[{key}] = {val};")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)

        rep = self.any_to_str(expr_d.get("repr"))
        if rep != "":
            return rep
        return f"/* unsupported expr: {kind} */"

    def emit_bridge_comment(self, expr: dict[str, Any] | None) -> None:
        """ランタイムブリッジ呼び出しの補助コメントを必要時に付与する。"""
        # 変換後ソースを原文に近づけるため、ブリッジ補助コメントは既定で出力しない。
        return
        if expr is None or expr.get("kind") != "Call":
            return
        fn = self.any_to_dict_or_empty(expr.get("func"))
        if len(fn) == 0:
            return
        key = ""
        text = ""
        fn_kind = self.any_to_str(fn.get("kind"))
        if fn_kind == "Name":
            name = str(fn.get("id", ""))
            if name == "save_gif":
                key = "save_gif"
                text = "// bridge: Python gif.save_gif -> C++ runtime save_gif"
            elif name == "write_rgb_png":
                key = "write_rgb_png"
                text = "// bridge: Python png.write_rgb_png -> C++ runtime png_helper::write_rgb_png"
        elif fn_kind == "Attribute":
            owner = self.any_to_dict_or_empty(fn.get("value"))
            owner_name = ""
            if len(owner) > 0 and owner.get("kind") == "Name":
                owner_name = str(owner.get("id", ""))
            attr = str(fn.get("attr", ""))
            if owner_name in {"gif_helper", "gif"} and attr == "save_gif":
                key = "save_gif"
                text = "// bridge: Python gif.save_gif -> C++ runtime save_gif"
            elif owner_name in {"png_helper", "png"} and attr == "write_rgb_png":
                key = "write_rgb_png"
                text = "// bridge: Python png.write_rgb_png -> C++ runtime png_helper::write_rgb_png"
        if key != "" and key not in self.bridge_comment_emitted:
            self.emit(text)
            self.bridge_comment_emitted.add(key)

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
                    return f"std::optional<{self._cpp_type_text(non_none[0])}>"
                return "std::any"
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
                    return "list<std::any>"
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
                    return "dict<str, std::any>"
                if inner[0] == "unknown":
                    return f"dict<str, {self._cpp_type_text(inner[1])}>"
                if inner[1] == "unknown":
                    return f"dict<{self._cpp_type_text(inner[0])}, std::any>"
                return f"dict<{self._cpp_type_text(inner[0])}, {self._cpp_type_text(inner[1])}>"
        if east_type.startswith("tuple[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[6:-1])
            return "std::tuple<" + ", ".join(self._cpp_type_text(x) for x in inner) + ">"
        if east_type == "unknown":
            return "std::any"
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
    emit_main: bool = True,
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
        emit_main,
    ).transpile()


def dump_deps_text(east_module: dict[str, Any]) -> str:
    """EAST の import メタデータを人間向けテキストへ整形する。"""
    # selfhost 安定性優先で固定フォーマットを返す。
    return "modules:\n  (none)\nsymbols:\n  (none)\n"


def print_user_error(err_text: str) -> None:
    """分類済みユーザーエラーをカテゴリ別に表示する。"""
    parsed_err = _parse_user_error(err_text)
    cat = str(parsed_err.get("category", ""))
    details: list[str] = []
    raw_details = parsed_err.get("details", [])
    if isinstance(raw_details, list):
        for item in raw_details:
            if isinstance(item, str):
                details.append(item)
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


def main(argv: list[str]) -> int:
    """CLI エントリポイント。変換実行と入出力を担当する。"""
    argv_list: list[str] = []
    for a in argv:
        argv_list.append(a)
    parsed, parse_err = parse_py2cpp_argv(argv_list)
    if parse_err != "":
        print(f"error: {parse_err}", file=sys.stderr)
        return 1
    input_txt = _dict_str_get(parsed, "input", "")
    output_txt = _dict_str_get(parsed, "output", "")
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
    dump_deps = _dict_str_get(parsed, "dump_deps", "0") == "1"
    dump_options = _dict_str_get(parsed, "dump_options", "0") == "1"
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
            "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]",
            file=sys.stderr,
        )
        return 0
    if input_txt == "":
        print(
            "usage: py2cpp.py INPUT.py [-o OUTPUT.cpp] [--preset MODE] [--negative-index-mode MODE] [--bounds-check-mode MODE] [--floor-div-mode MODE] [--mod-mode MODE] [--int-width MODE] [--str-index-mode MODE] [--str-slice-mode MODE] [-O0|-O1|-O2|-O3] [--no-main] [--dump-deps] [--dump-options]",
            file=sys.stderr,
        )
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
        east_module = load_east(input_path, parser_backend)
        if dump_deps:
            dep_text = dump_deps_text(east_module)
            if output_txt != "":
                out_path = Path(output_txt)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(dep_text, encoding="utf-8")
            else:
                print(dep_text, end="")
            return 0
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
            not no_main,
        )
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

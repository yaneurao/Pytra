#!/usr/bin/env python3
"""EAST -> C++ transpiler.

This tool transpiles Pytra EAST JSON into C++ source.
It can also accept a Python source file and internally run src/common/east.py conversion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from common.code_emitter import CodeEmitter
from common.east_io import load_east_from_path
from common.language_profile import load_language_profile
from common.transpile_cli import add_common_transpile_args, normalize_common_transpile_args

CPP_HEADER = """#include "runtime/cpp/py_runtime.h"

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
    out["math"] = {"sqrt": "py_math::sqrt"}
    return out


_DEFAULT_CPP_MODULE_ATTR_CALL_MAP: dict[str, dict[str, str]] = _default_cpp_module_attr_call_map()
_CPP_PROFILE_CACHE_BOX: dict[str, Any] = {"loaded": False, "value": {}}

def _safe_nested_dict(obj: Any, keys: list[str]) -> dict[str, Any] | None:
    return None


def _deep_copy_str_map(v: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for k, inner in v.items():
        out[k] = dict(inner)
    return out


def _safe_nested_str_map(obj: Any, keys: list[str]) -> dict[str, str] | None:
    return None


def _copy_str_map(src: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in src.items():
        out[k] = v
    return out


def load_cpp_profile() -> dict[str, Any]:
    """C++ 用 LanguageProfile を読み込む（失敗時は空 dict）。"""
    return {}


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
    out: dict[str, str] = {}
    return out


def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """C++ 用 hooks 設定を返す（現状は no-op）。"""
    out: dict[str, Any] = {}
    return out


def _safe_nested_str_list(obj: Any, keys: list[str]) -> list[str] | None:
    return None


def load_cpp_identifier_rules() -> tuple[set[str], str]:
    """識別子リネーム規則を profile から取得する。"""
    reserved: set[str] = set()
    rename_prefix = "py_"
    return reserved, rename_prefix


def _load_cpp_runtime_call_map_json() -> dict[str, Any] | None:
    return None


def load_cpp_module_attr_call_map(profile: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """C++ の `module.attr(...)` -> ランタイム呼び出しマップを返す。"""
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
        ch: byte = s[i]
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


def cpp_char_lit(ch: byte) -> str:
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
        *,
        negative_index_mode: str = "const_only",
        emit_main: bool = True,
    ) -> None:
        """変換設定とクラス解析用の状態を初期化する。"""
        profile = load_cpp_profile()
        hooks = load_cpp_hooks(profile)
        self.doc: dict[str, Any] = east_doc
        self.profile: dict[str, Any] = profile
        self.hooks: dict[str, Any] = hooks
        self.lines: list[str] = []
        self.indent: int64 = 0
        self.tmp_id: int64 = 0
        self.scope_stack: list[set[str]] = [set()]
        self.negative_index_mode = negative_index_mode
        self.emit_main = emit_main
        # NOTE:
        # self-host compile path currently treats EAST payload values as dynamic,
        # so dict[str, Any] -> dict iteration for renaming is disabled for now.
        self.renamed_symbols: dict[str, str] = {}
        self.scope_stack: list[set[str]] = [set()]
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
        self.module_attr_call_map: dict[str, dict[str, str]] = load_cpp_module_attr_call_map(self.profile)
        self.reserved_words: set[str] = set()
        self.rename_prefix: str = "py_"
        self.reserved_words, self.rename_prefix = load_cpp_identifier_rules()
        self.import_modules: dict[str, str] = {}
        self.import_symbols: dict[str, dict[str, str]] = {}
        # NOTE:
        # selfhost 安定化を優先し、meta 由来の import 解決は段階的に戻す。

    def emit_block_comment(self, text: str) -> None:
        """Emit docstring/comment as C-style block comment."""
        self.emit("/* " + text + " */")

    def _is_std_runtime_call(self, runtime_call: str) -> bool:
        """`std::` 直呼び出しとして扱う runtime_call か判定する。"""
        return runtime_call.startswith("std::")

    def _resolve_imported_module_name(self, name: str) -> str:
        """import で束縛された識別子名を実モジュール名へ解決する。"""
        return name

    def _resolve_imported_symbol(self, name: str) -> dict[str, str] | None:
        """from-import で束縛された識別子を返す（無ければ None）。"""
        return None

    def _resolve_runtime_call_for_imported_symbol(self, module_name: str, symbol_name: str) -> str | None:
        """`from X import Y` で取り込まれた Y 呼び出しの runtime 名を返す。"""
        return None

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
        body: list[dict[str, Any]] = []
        raw_body = self.doc.get("body", [])
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
                    raw_class_body = stmt.get("body", [])
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
        if len(header_text) > 0 and header_text[-1] == "\n":
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
            raw_main_guard = self.doc.get("main_guard_body", [])
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
                out += "\n"
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
        values = self.any_to_list(self.any_dict_get(expr_dict, "values", []))
        value_nodes: list[dict[str, Any]] = []
        for v in values:
            vd = self.any_to_dict(v)
            if vd is not None:
                value_nodes.append(vd)
        if len(value_nodes) == 0:
            return "false"
        value_texts = [self.render_expr(v) for v in value_nodes]
        if not force_value_select and self.get_expr_type(expr_dict) == "bool":
            op = "&&" if self.any_to_str(self.any_dict_get(expr_dict, "op", "")) == "And" else "||"
            wrapped_values = [f"({txt})" for txt in value_texts]
            return f" {op} ".join(wrapped_values)

        op_name = str(self.any_dict_get(expr_dict, "op", ""))
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

    def _one_char_str_const(self, node: Any) -> str | None:
        """1文字文字列定数ならその実文字を返す。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) == 0 or node_dict.get("kind") != "Constant":
            return None
        v = node_dict.get("value")
        if isinstance(v, str):
            if len(v) == 1:
                return v
            if len(v) == 2 and v[0] == "\\":
                esc = {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "\\": "\\",
                    "'": "'",
                    "0": "\0",
                }
                return esc.get(v[1])
        return None

    def _str_index_char_access(self, node: Any) -> str | None:
        """str 添字アクセスを `at()` ベースの char 比較式へ変換する。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) == 0 or node_dict.get("kind") != "Subscript":
            return None
        value_node = node_dict.get("value")
        if self.get_expr_type(value_node) != "str":
            return None
        sl = node_dict.get("slice")
        if isinstance(sl, dict) and sl.get("kind") == "Slice":
            return None
        if self.negative_index_mode != "off" and self._is_negative_const_index(sl):
            return None
        base = self.render_expr(value_node)
        if isinstance(value_node, dict) and value_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            base = f"({base})"
        idx = self.render_expr(sl)
        return f"{base}.at({idx})"

    def _try_optimize_char_compare(
        self,
        left_node: dict[str, Any] | None,
        op: str,
        right_node: dict[str, Any] | None,
    ) -> str | None:
        """1文字比較を `'x'` / `.at(i)` 形へ最適化できるか判定する。"""
        if op not in {"Eq", "NotEq"}:
            return None
        cop = "==" if op == "Eq" else "!="
        l_access = self._str_index_char_access(left_node)
        r_ch = self._one_char_str_const(right_node)
        if l_access is not None and r_ch is not None:
            return f"{l_access} {cop} {cpp_char_lit(r_ch)}"
        r_access = self._str_index_char_access(right_node)
        l_ch = self._one_char_str_const(left_node)
        if r_access is not None and l_ch is not None:
            return f"{cpp_char_lit(l_ch)} {cop} {r_access}"
        l_ty = self.get_expr_type(left_node)
        if l_ty == "uint8" and r_ch is not None:
            return f"{self.render_expr(left_node)} {cop} {cpp_char_lit(r_ch)}"
        r_ty = self.get_expr_type(right_node)
        if r_ty == "uint8" and l_ch is not None:
            return f"{cpp_char_lit(l_ch)} {cop} {self.render_expr(right_node)}"
        return None

    def _byte_from_str_expr(self, node: dict[str, Any] | None) -> str | None:
        """str 系式を uint8 初期化向けの char 式へ変換する。"""
        ch = self._one_char_str_const(node)
        if ch is not None:
            return cpp_char_lit(ch)
        return self._str_index_char_access(node)

    def _wrap_for_binop_operand(
        self,
        rendered: str,
        operand_expr: dict[str, Any] | None,
        parent_op: str,
        *,
        is_right: bool,
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

    def render_minmax(self, fn: str, args: list[str], out_type: str | None) -> str:
        """min/max 呼び出しを型情報付きで C++ 式へ変換する。"""
        if len(args) == 0:
            return "/* invalid min/max */"
        if len(args) == 1:
            return args[0]
        t = "auto"
        if isinstance(out_type, str) and out_type != "":
            t = self.cpp_type(out_type)
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
        body_stmts = [s for s in stmt.get("body", []) if isinstance(s, dict)]
        else_stmts = [s for s in stmt.get("orelse", []) if isinstance(s, dict)]
        if self._can_omit_braces_for_single_stmt(body_stmts) and (len(else_stmts) == 0 or self._can_omit_braces_for_single_stmt(else_stmts)):
            self.emit(self.syntax_line("if_no_brace", "if ({cond})", {"cond": self.render_cond(stmt.get("test"))}))
            self.indent += 1
            self.scope_stack.append(set())
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            if len(else_stmts) > 0:
                self.emit(self.syntax_text("else_no_brace", "else"))
                self.indent += 1
                self.scope_stack.append(set())
                self.emit_stmt(else_stmts[0])
                self.scope_stack.pop()
                self.indent -= 1
            return

        self.emit(self.syntax_line("if_open", "if ({cond}) {", {"cond": self.render_cond(stmt.get("test"))}))
        self.indent += 1
        self.scope_stack.append(set())
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        if len(else_stmts) > 0:
            self.emit(self.syntax_text("else_open", "} else {"))
            self.indent += 1
            self.scope_stack.append(set())
            self.emit_stmt_list(else_stmts)
            self.scope_stack.pop()
            self.indent -= 1
            self.emit(self.syntax_text("block_close", "}"))
        else:
            self.emit(self.syntax_text("block_close", "}"))

    def _emit_while_stmt(self, stmt: dict[str, Any]) -> None:
        """While ノードを出力する。"""
        self.emit(self.syntax_line("while_open", "while ({cond}) {", {"cond": self.render_cond(stmt.get("test"))}))
        self.indent += 1
        self.scope_stack.append(set())
        self.emit_stmt_list(list(stmt.get("body", [])))
        self.scope_stack.pop()
        self.indent -= 1
        self.emit(self.syntax_text("block_close", "}"))

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """1つの文ノードを C++ 文へ変換して出力する。"""
        hook_stmt = self.hook_on_emit_stmt(self, stmt)
        if hook_stmt is True:
            return
        kind = stmt.get("kind")
        self.emit_leading_comments(stmt)
        if kind in {"Import", "ImportFrom"}:
            return
        if kind == "Pass":
            self.emit("/* pass */")
            return
        if kind == "Break":
            self.emit("break;")
            return
        if kind == "Continue":
            self.emit("continue;")
            return
        if kind == "Expr":
            value_raw = stmt.get("value")
            value = value_raw if isinstance(value_raw, dict) else None
            if isinstance(value, dict) and value.get("kind") == "Constant" and isinstance(value.get("value"), str):
                self.emit_block_comment(str(value.get("value")))
            elif self._is_redundant_super_init_call(value):
                self.emit("/* super().__init__ omitted: base ctor is called implicitly */")
            else:
                self.emit_bridge_comment(value)
                rendered = self.render_expr(value)
                # Guard against stray identifier-only expression statements (e.g. "r;").
                if isinstance(rendered, str) and self._is_identifier_expr(rendered):
                    if rendered == "break":
                        self.emit("break;")
                    elif rendered == "continue":
                        self.emit("continue;")
                    elif rendered == "pass":
                        self.emit("/* pass */")
                    else:
                        self.emit(f"/* omitted bare identifier expression: {rendered} */")
                else:
                    self.emit(rendered + ";")
            return
        if kind == "Return":
            v_raw = stmt.get("value")
            v = v_raw if isinstance(v_raw, dict) else None
            if v is None:
                self.emit("return;")
            else:
                self.emit(f"return {self.render_expr(v)};")
            return
        if kind == "Assign":
            self.emit_assign(stmt)
            return
        if kind == "Swap":
            left = self.render_expr(stmt.get("left"))
            right = self.render_expr(stmt.get("right"))
            self.emit(f"std::swap({left}, {right});")
            return
        if kind == "AnnAssign":
            t = self.cpp_type(stmt.get("annotation"))
            target = self.render_expr(stmt.get("target"))
            val_raw = stmt.get("value")
            val = val_raw if isinstance(val_raw, dict) else None
            rendered_val: str = ""
            if val is not None:
                rendered_val = self.render_expr(val)
            ann_t_raw = stmt.get("annotation")
            ann_t_str: str = str(ann_t_raw) if isinstance(ann_t_raw, str) else ""
            if ann_t_str in {"byte", "uint8"} and isinstance(val, dict):
                byte_val = self._byte_from_str_expr(val)
                if byte_val is not None:
                    rendered_val = byte_val
            if isinstance(val, dict) and val.get("kind") == "Dict" and ann_t_str.startswith("dict[") and ann_t_str.endswith("]"):
                inner_ann = self.split_generic(ann_t_str[5:-1])
                if len(inner_ann) == 2 and self.is_any_like_type(inner_ann[1]):
                    items: list[str] = []
                    for kv in val.get("entries", []):
                        if not isinstance(kv, dict):
                            continue
                        k = self.render_expr(kv.get("key"))
                        v = self.render_expr_as_any(kv.get("value"))
                        items.append(f"{{{k}, {v}}}")
                    rendered_val = f"{t}{{{', '.join(items)}}}"
            if isinstance(val, dict) and t != "auto":
                vkind = val.get("kind")
                if vkind == "BoolOp":
                    if ann_t_str != "bool":
                        rendered_val = self.render_boolop(val, True)
                if vkind == "List" and len(val.get("elements", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "Dict" and len(val.get("entries", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "Set" and len(val.get("elements", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "ListComp" and isinstance(rendered_val, str):
                    # Keep as-is for selfhost stability; list-comp explicit typing can be improved later.
                    rendered_val = rendered_val
            if self.is_any_like_type(ann_t_str) and val is not None:
                if isinstance(val, dict) and val.get("kind") == "Constant" and val.get("value") is None:
                    rendered_val = "object{}"
                elif not rendered_val.startswith("make_object("):
                    rendered_val = f"make_object({rendered_val})"
            declare = bool(stmt.get("declare", True))
            already_declared = self.is_declared(target) if self.is_plain_name_expr(stmt.get("target")) else False
            if target.startswith("this->"):
                if val is None:
                    self.emit(f"{target};")
                else:
                    self.emit(f"{target} = {rendered_val};")
                return
            if val is None:
                if declare and self.is_plain_name_expr(stmt.get("target")) and not already_declared:
                    self.current_scope().add(target)
                if declare and not already_declared:
                    self.emit(f"{t} {target};")
            else:
                if declare and self.is_plain_name_expr(stmt.get("target")) and not already_declared:
                    self.current_scope().add(target)
                if declare and not already_declared:
                    self.emit(f"{t} {target} = {rendered_val};")
                else:
                    self.emit(f"{target} = {rendered_val};")
            return
        if kind == "AugAssign":
            op = "+="
            target_expr = stmt.get("target")
            target = self.render_lvalue(target_expr)
            declare = bool(stmt.get("declare", False))
            if declare and self.is_plain_name_expr(target_expr) and target not in self.current_scope():
                decl_t = stmt.get("decl_type")
                inferred_t = self.get_expr_type(target_expr)
                t = self.cpp_type(decl_t if isinstance(decl_t, str) and decl_t != "" else inferred_t)
                self.current_scope().add(target)
                self.emit(f"{t} {target} = {self.render_expr(stmt.get('value'))};")
                return
            val = self.render_expr(stmt.get("value"))
            target_t = self.get_expr_type(target_expr)
            value_t = self.get_expr_type(stmt.get("value"))
            if self.is_any_like_type(value_t):
                if target_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                    val = f"py_to_int64({val})"
                elif target_t in {"float32", "float64"}:
                    val = f"static_cast<float64>(py_to_int64({val}))"
            op_name = str(stmt.get("op"))
            if op_name in AUG_OPS:
                op = AUG_OPS[op_name]
            if op_name in AUG_BIN:
                bop = AUG_BIN[op_name]
                # Prefer idiomatic ++/-- for +/-1 updates.
                if op_name in {"Add", "Sub"} and val == "1":
                    self.emit(f"{target}{'++' if op_name == 'Add' else '--'};")
                    return
                if op_name == "FloorDiv":
                    self.emit(f"{target} = py_floordiv({target}, {val});")
                else:
                    self.emit(f"{target} {op} {val};")
            else:
                self.emit(f"{target} {op} {val};")
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
            exc = stmt.get("exc")
            if exc is None:
                self.emit('throw std::runtime_error("raise");')
            else:
                self.emit(f"throw {self.render_expr(exc)};")
            return
        if kind == "Try":
            finalbody = list(stmt.get("finalbody", []))
            handlers = list(stmt.get("handlers", []))
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
                self.emit_stmt_list(list(stmt.get("body", [])))
                if has_effective_finally:
                    self.indent -= 1
                    self.emit("}")
                return
            self.emit("try {")
            self.indent += 1
            self.emit_stmt_list(list(stmt.get("body", [])))
            self.indent -= 1
            self.emit("}")
            for h in handlers:
                name_raw = h.get("name")
                name = name_raw if isinstance(name_raw, str) and name_raw != "" else "ex"
                self.emit(f"catch (const std::exception& {name}) {{")
                self.indent += 1
                self.emit_stmt_list(list(h.get("body", [])))
                self.indent -= 1
                self.emit("}")
            if has_effective_finally:
                self.indent -= 1
                self.emit("}")
            return
        if kind == "FunctionDef":
            self.emit_function(stmt, False)
            return
        if kind == "ClassDef":
            self.emit_class(stmt)
            return

        self.emit(f"/* unsupported stmt kind: {kind} */")

    def _can_omit_braces_for_single_stmt(self, stmts: list[dict[str, Any]]) -> bool:
        """単文ブロックで波括弧を省略可能か判定する。"""
        filtered: list[dict[str, Any]] = [s for s in stmts if isinstance(s, dict)]
        if len(filtered) != 1:
            return False
        k = filtered[0].get("kind")
        return k in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}

    def emit_assign(self, stmt: Any) -> None:
        """代入文（通常代入/タプル代入）を C++ へ出力する。"""
        stmt_node = self.any_to_dict(stmt)
        if stmt_node is None:
            self.emit("/* invalid assign */")
            return
        stmt = stmt_node
        target = stmt.get("target")
        value = stmt.get("value")
        if target is None or value is None:
            self.emit("/* invalid assign */")
            return
        if target.get("kind") == "Tuple":
            lhs_elems = list(target.get("elements", []))
            if isinstance(value, dict) and value.get("kind") == "Tuple":
                rhs_elems = list(value.get("elements", []))
                if (
                    len(lhs_elems) == 2
                    and len(rhs_elems) == 2
                    and self._expr_repr_eq(lhs_elems[0], rhs_elems[1])
                    and self._expr_repr_eq(lhs_elems[1], rhs_elems[0])
                ):
                    self.emit(f"std::swap({self.render_lvalue(lhs_elems[0])}, {self.render_lvalue(lhs_elems[1])});")
                    return
            tmp = self.next_tmp("__tuple")
            self.emit(f"auto {tmp} = {self.render_expr(value)};")
            tuple_elem_types: list[str] = []
            value_t = self.get_expr_type(value)
            if isinstance(value_t, str) and value_t.startswith("tuple[") and value_t.endswith("]"):
                tuple_elem_types = self.split_generic(value_t[6:-1])
            for i, elt in enumerate(target.get("elements", [])):
                lhs = self.render_expr(elt)
                if self.is_plain_name_expr(elt):
                    name = str(elt.get("id", ""))
                    if not self.is_declared(name):
                        decl_t = self.cpp_type(tuple_elem_types[i] if i < len(tuple_elem_types) else self.get_expr_type(elt))
                        self.current_scope().add(name)
                        self.emit(f"{decl_t} {lhs} = std::get<{i}>({tmp});")
                        continue
                self.emit(f"{lhs} = std::get<{i}>({tmp});")
            return
        texpr = self.render_lvalue(target)
        if self.is_plain_name_expr(target) and not self.is_declared(texpr):
            d0 = stmt.get("decl_type")
            d1 = self.get_expr_type(target)
            d2 = self.get_expr_type(value)
            picked = d0 if isinstance(d0, str) and d0 != "" else (d1 if isinstance(d1, str) and d1 != "" else d2)
            dtype = self.cpp_type(picked)
            self.current_scope().add(texpr)
            rval = self.render_expr(value)
            if dtype == "uint8" and isinstance(value, dict):
                byte_val = self._byte_from_str_expr(value)
                if byte_val is not None:
                    rval = byte_val
            if isinstance(value, dict) and value.get("kind") == "BoolOp" and picked != "bool":
                rval = self.render_boolop(value, True)
            if self.is_any_like_type(picked):
                if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                    rval = "object{}"
                elif not rval.startswith("make_object("):
                    rval = f"make_object({rval})"
            self.emit(f"{dtype} {texpr} = {rval};")
            return
        rval = self.render_expr(value)
        t_target = self.get_expr_type(target)
        if t_target == "uint8" and isinstance(value, dict):
            byte_val = self._byte_from_str_expr(value)
            if byte_val is not None:
                rval = byte_val
        if isinstance(value, dict) and value.get("kind") == "BoolOp" and t_target != "bool":
            rval = self.render_boolop(value, True)
        if self.is_any_like_type(t_target):
            if isinstance(value, dict) and value.get("kind") == "Constant" and value.get("value") is None:
                rval = "object{}"
            elif not rval.startswith("make_object("):
                rval = f"make_object({rval})"
        self.emit(f"{texpr} = {rval};")

    def render_lvalue(self, expr: Any) -> str:
        """左辺値文脈の式（添字代入含む）を C++ 文字列へ変換する。"""
        expr_node = self.any_to_dict(expr)
        if expr_node is None:
            return self.render_expr(expr)
        node = expr_node
        if node.get("kind") != "Subscript":
            return self.render_expr(node)
        val_expr = node.get("value")
        val = self.render_expr(val_expr)
        val_ty0 = self.get_expr_type(val_expr)
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        sl = node.get("slice")
        idx = self.render_expr(sl)
        if val_ty.startswith("dict["):
            return f"{val}[{idx}]"
        if self.is_indexable_sequence_type(val_ty):
            if self.negative_index_mode == "off":
                return f"{val}[{idx}]"
            if self.negative_index_mode == "const_only":
                if self._is_negative_const_index(sl):
                    return f"py_at({val}, {idx})"
                return f"{val}[{idx}]"
            return f"py_at({val}, {idx})"
        return f"{val}[{idx}]"

    def _target_bound_names(self, target: dict[str, Any] | None) -> set[str]:
        """for ターゲットが束縛する識別子名を収集する。"""
        names: set[str] = set()
        if not isinstance(target, dict):
            return names
        if target.get("kind") == "Name":
            names.add(str(target.get("id", "_")))
            return names
        if target.get("kind") == "Tuple":
            for e in target.get("elements", []):
                if isinstance(e, dict) and e.get("kind") == "Name":
                    names.add(str(e.get("id", "_")))
        return names

    def _emit_target_unpack(self, target: dict[str, Any] | None, src: str) -> None:
        """タプルターゲットへのアンパック代入を出力する。"""
        if not isinstance(target, dict):
            return
        if target.get("kind") != "Tuple":
            return
        for i, e in enumerate(target.get("elements", [])):
            if isinstance(e, dict) and e.get("kind") == "Name":
                nm = self.render_expr(e)
                self.emit(f"auto {nm} = std::get<{i}>({src});")

    def emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノードを C++ の for ループとして出力する。"""
        tgt = self.render_expr(stmt.get("target"))
        t0 = stmt.get("target_type")
        t1 = self.get_expr_type(stmt.get("target"))
        tgt_ty = self.cpp_type(t0 if isinstance(t0, str) and t0 != "" else t1)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        body_stmts = list(stmt.get("body", []))
        omit_braces = len(stmt.get("orelse", [])) == 0 and self._can_omit_braces_for_single_stmt(body_stmts)
        mode = stmt.get("range_mode")
        if mode == "ascending":
            cond = f"{tgt} < {stop}"
        elif mode == "descending":
            cond = f"{tgt} > {stop}"
        else:
            cond = f"{step} > 0 ? {tgt} < {stop} : {tgt} > {stop}"
        if step == "1":
            inc = f"++{tgt}"
        elif step == "-1":
            inc = f"--{tgt}"
        else:
            inc = f"{tgt} += {step}"
        hdr = f"for ({tgt_ty} {tgt} = {start}; {cond}; {inc})"
        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            self.scope_stack.append({tgt})
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(hdr + " {")
        self.indent += 1
        self.scope_stack.append({tgt})
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("}")

    def emit_for_each(self, stmt: dict[str, Any]) -> None:
        """For ノード（反復）を C++ range-for として出力する。"""
        target = stmt.get("target")
        iter_expr = stmt.get("iter")
        if isinstance(iter_expr, dict) and iter_expr.get("kind") == "RangeExpr":
            pseudo = {
                "target": target,
                "target_type": stmt.get("target_type") if isinstance(stmt.get("target_type"), str) and stmt.get("target_type") != "" else "int64",
                "start": iter_expr.get("start"),
                "stop": iter_expr.get("stop"),
                "step": iter_expr.get("step"),
                "range_mode": iter_expr.get("range_mode", "dynamic"),
                "body": stmt.get("body", []),
            }
            self.emit_for_range(pseudo)
            return
        body_stmts = list(stmt.get("body", []))
        omit_braces = len(stmt.get("orelse", [])) == 0 and self._can_omit_braces_for_single_stmt(body_stmts)
        t = self.render_expr(target)
        it = self.render_expr(iter_expr)
        t0 = stmt.get("target_type")
        t1 = self.get_expr_type(target)
        t_ty = self.cpp_type(t0 if isinstance(t0, str) and t0 != "" else t1)
        target_names = self._target_bound_names(target if isinstance(target, dict) else None)
        unpack_tuple = isinstance(target, dict) and target.get("kind") == "Tuple"
        if unpack_tuple:
            # tuple unpack emits extra binding lines before the loop body; keep braces for correctness.
            omit_braces = False
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
            self.scope_stack.append(target_names)
            if unpack_tuple:
                self._emit_target_unpack(target if isinstance(target, dict) else None, iter_tmp)
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(hdr + " {")
        self.indent += 1
        self.scope_stack.append(target_names)
        if unpack_tuple:
            self._emit_target_unpack(target if isinstance(target, dict) else None, iter_tmp)
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("}")

    def emit_function(self, stmt: dict[str, Any], in_class: bool = False) -> None:
        """関数定義ノードを C++ 関数として出力する。"""
        name = stmt.get("name", "fn")
        ret = self.cpp_type(stmt.get("return_type"))
        arg_types: dict[str, str] = stmt.get("arg_types", {})
        arg_usage: dict[str, str] = stmt.get("arg_usage", {})
        params: list[str] = []
        fn_scope: set[str] = set()
        for idx, (n, t) in enumerate(arg_types.items()):
            if in_class and idx == 0 and n == "self":
                continue
            ct = self.cpp_type(t)
            usage = arg_usage.get(n, "readonly")
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if by_ref and usage == "mutable":
                params.append(f"{ct}& {n}")
            elif by_ref:
                params.append(f"const {ct}& {n}")
            else:
                params.append(f"{ct} {n}")
            fn_scope.add(n)
        if in_class and name == "__init__" and self.current_class_name is not None:
            if self.current_class_base_name == "CodeEmitter":
                self.emit(f"{self.current_class_name}({', '.join(params)}) : CodeEmitter(east_doc, dict<str, object>{{}}, dict<str, object>{{}}) {{")
            else:
                self.emit(
                    self.syntax_line(
                        "ctor_open",
                        "{name}({args}) {",
                        {"name": self.current_class_name, "args": ", ".join(params)},
                    )
                )
        elif in_class and name == "__del__" and self.current_class_name is not None:
            self.emit(self.syntax_line("dtor_open", "~{name}() {", {"name": self.current_class_name}))
        else:
            self.emit(
                self.syntax_line(
                    "function_open",
                    "{ret} {name}({args}) {",
                    {"ret": ret, "name": str(name), "args": ", ".join(params)},
                )
            )
        self.indent += 1
        self.scope_stack.append(fn_scope)
        docstring = stmt.get("docstring")
        if isinstance(docstring, str) and docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(list(stmt.get("body", [])))
        self.scope_stack.pop()
        self.indent -= 1
        self.emit(self.syntax_text("block_close", "}"))

    def emit_class(self, stmt: dict[str, Any]) -> None:
        """クラス定義ノードを C++ クラス/struct として出力する。"""
        name = stmt.get("name", "Class")
        is_dataclass = bool(stmt.get("dataclass", False))
        base = stmt.get("base")
        cls_name = str(name)
        gc_managed = cls_name in self.ref_classes
        bases: list[str] = []
        if isinstance(base, str) and base != "":
            bases.append(f"public {base}")
        base_is_gc = isinstance(base, str) and base in self.ref_classes
        if gc_managed and not base_is_gc:
            bases.append("public PyObj")
        base_txt = "" if len(bases) == 0 else " : " + ", ".join(bases)
        self.emit(self.syntax_line("class_open", "struct {name}{base_txt} {", {"name": str(name), "base_txt": base_txt}))
        self.indent += 1
        prev_class = self.current_class_name
        prev_class_base = self.current_class_base_name
        prev_fields = self.current_class_fields
        prev_static_fields = self.current_class_static_fields
        self.current_class_name = str(name)
        self.current_class_base_name = str(base) if isinstance(base, str) else ""
        self.current_class_fields = dict(stmt.get("field_types", {}))
        class_body = list(stmt.get("body", []))
        static_field_types: dict[str, str] = {}
        static_field_defaults: dict[str, str] = {}
        instance_field_defaults: dict[str, str] = {}
        for s in class_body:
            if s.get("kind") == "AnnAssign":
                texpr = s.get("target")
                if self.is_plain_name_expr(texpr):
                    fname = str(texpr.get("id", ""))
                    ann = s.get("annotation")
                    if isinstance(ann, str) and ann != "":
                        if is_dataclass:
                            instance_field_defaults[fname] = self.render_expr(s.get("value")) if s.get("value") is not None else instance_field_defaults.get(fname, "")
                        else:
                            static_field_types[fname] = ann
                            if s.get("value") is not None:
                                static_field_defaults[fname] = self.render_expr(s.get("value"))
        self.current_class_static_fields = set(static_field_types.keys())
        instance_fields: dict[str, str] = {
            k: v for k, v in self.current_class_fields.items() if k not in self.current_class_static_fields
        }
        has_init = any(s.get("kind") == "FunctionDef" and s.get("name") == "__init__" for s in class_body)
        for fname, fty in static_field_types.items():
            if fname in static_field_defaults:
                self.emit(f"inline static {self.cpp_type(fty)} {fname} = {static_field_defaults[fname]};")
            else:
                self.emit(f"inline static {self.cpp_type(fty)} {fname};")
        for fname, fty in instance_fields.items():
            self.emit(f"{self.cpp_type(fty)} {fname};")
        if len(static_field_types) > 0 or len(instance_fields) > 0:
            self.emit("")
        if len(instance_fields) > 0 and not has_init:
            params: list[str] = []
            for fname, fty in instance_fields.items():
                p = f"{self.cpp_type(fty)} {fname}"
                if fname in instance_field_defaults and instance_field_defaults[fname] != "":
                    p += f" = {instance_field_defaults[fname]}"
                params.append(p)
            self.emit(f"{name}({', '.join(params)}) {{")
            self.indent += 1
            for fname in instance_fields:
                self.emit(f"this->{fname} = {fname};")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        for s in class_body:
            if s.get("kind") == "FunctionDef":
                self.emit_function(s, in_class=True)
            elif s.get("kind") == "AnnAssign":
                t = self.cpp_type(s.get("annotation"))
                target_expr = s.get("target")
                target = self.render_expr(target_expr)
                if self.is_plain_name_expr(target_expr) and target in self.current_class_fields:
                    continue
                val = s.get("value")
                if val is None:
                    self.emit(f"{t} {target};")
                else:
                    self.emit(f"{t} {target} = {self.render_expr(val)};")
            else:
                self.emit_stmt(s)
        self.current_class_name = prev_class
        self.current_class_base_name = prev_class_base
        self.current_class_fields = prev_fields
        self.current_class_static_fields = prev_static_fields
        self.indent -= 1
        self.emit(self.syntax_text("class_close", "};"))

    def _render_binop_expr(self, expr: dict[str, Any]) -> str:
        """BinOp ノードを C++ 式へ変換する。"""
        if expr.get("left") is None or expr.get("right") is None:
            rep = expr.get("repr")
            if isinstance(rep, str) and rep != "":
                return rep
        left_expr = expr.get("left")
        right_expr = expr.get("right")
        left = self.render_expr(left_expr)
        right = self.render_expr(right_expr)
        cast_rules = expr.get("casts", [])
        for c in cast_rules:
            on = c.get("on")
            to_t = c.get("to")
            if on == "left":
                left = self.apply_cast(left, to_t)
            elif on == "right":
                right = self.apply_cast(right, to_t)
        op_name = expr.get("op")
        op_name_str = str(op_name)
        left = self._wrap_for_binop_operand(left, left_expr if isinstance(left_expr, dict) else None, op_name_str, is_right=False)
        right = self._wrap_for_binop_operand(right, right_expr if isinstance(right_expr, dict) else None, op_name_str, is_right=True)
        hook_binop = self.hook_on_render_binop(
            self,
            expr,
            left,
            right,
        )
        if isinstance(hook_binop, str) and hook_binop != "":
            return hook_binop
        if op_name == "Div":
            # Prefer direct C++ division when float is involved (or EAST already injected casts).
            # Keep py_div fallback for int/int Python semantics.
            lt0 = self.get_expr_type(left_expr if isinstance(left_expr, dict) else None)
            rt0 = self.get_expr_type(right_expr if isinstance(right_expr, dict) else None)
            lt = lt0 if isinstance(lt0, str) else ""
            rt = rt0 if isinstance(rt0, str) else ""
            if lt == "Path" and rt in {"str", "Path"}:
                return f"{left} / {right}"
            if len(cast_rules) > 0 or lt in {"float32", "float64"} or rt in {"float32", "float64"}:
                return f"{left} / {right}"
            return f"py_div({left}, {right})"
        if op_name == "FloorDiv":
            return f"py_floordiv({left}, {right})"
        if op_name == "Mod":
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
        op = BIN_OPS.get(op_name, "+")
        return f"{left} {op} {right}"

    def _render_builtin_call(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        first_arg: Any,
    ) -> str | None:
        """lowered_kind=BuiltinCall の呼び出しを処理する。"""
        runtime_call = expr.get("runtime_call")
        builtin_name = expr.get("builtin_name")
        if runtime_call == "py_print":
            return f"py_print({', '.join(args)})"
        if runtime_call == "py_len" and len(args) == 1:
            return f"py_len({args[0]})"
        if runtime_call == "py_to_string" and len(args) == 1:
            src_expr = first_arg
            return self.render_to_string(src_expr if isinstance(src_expr, dict) else None)
        if runtime_call == "static_cast" and len(args) == 1:
            target = self.cpp_type(expr.get("resolved_type"))
            arg_t = self.get_expr_type(first_arg if isinstance(first_arg, dict) else None)
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
            return self.render_minmax(fn_name, args, self.get_expr_type(expr))
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
            owner_node = fn.get("value")
            owner = self.render_expr(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            parents = kw.get("parents", "false")
            exist_ok = kw.get("exist_ok", "false")
            if len(args) >= 1:
                parents = args[0]
            if len(args) >= 2:
                exist_ok = args[1]
            return f"{owner}.mkdir({parents}, {exist_ok})"
        if runtime_call == "std::filesystem::exists":
            owner_node = fn.get("value")
            owner = self.render_expr(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            return f"{owner}.exists()"
        if runtime_call == "py_write_text":
            owner_node = fn.get("value")
            owner = self.render_expr(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner = f"({owner})"
            write_arg = args[0] if len(args) >= 1 else '""'
            return f"{owner}.write_text({write_arg})"
        if runtime_call == "py_read_text":
            owner_node = fn.get("value")
            owner = self.render_expr(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
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
                out_t = self.get_expr_type(expr)
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
        if isinstance(runtime_call, str) and self._is_std_runtime_call(runtime_call):
            return f"{runtime_call}({', '.join(args)})"
        if builtin_name == "bytes":
            return f"bytes({', '.join(args)})" if len(args) >= 1 else "bytes{}"
        if builtin_name == "bytearray":
            return f"bytearray({', '.join(args)})" if len(args) >= 1 else "bytearray{}"
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
        if fn.get("kind") == "Name":
            raw = fn.get("id")
            imported = None
            imported_module = ""
            if isinstance(raw, str) and not self.is_declared(raw):
                imported = self._resolve_imported_symbol(raw)
                if isinstance(imported, dict):
                    imported_module = imported.get("module", "")
                    raw = imported.get("name", raw)
            if isinstance(raw, str) and imported_module != "":
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
                rhs = arg_nodes[1] if isinstance(arg_nodes, list) and len(arg_nodes) > 1 else None
                if isinstance(rhs, dict) and rhs.get("kind") == "Name":
                    type_name = str(rhs.get("id", ""))
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
                return self.render_to_string(src_expr if isinstance(src_expr, dict) else None)
            if raw in {"int", "float", "bool"} and len(args) == 1:
                target = self.cpp_type(expr.get("resolved_type"))
                arg_t = self.get_expr_type(first_arg if isinstance(first_arg, dict) else None)
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
                return self.render_minmax(raw, args, self.get_expr_type(expr))
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
        if fn.get("kind") == "Attribute":
            owner = fn.get("value")
            owner_t = self.get_expr_type(owner)
            owner_expr = self.render_expr(owner)
            if isinstance(owner, dict) and owner.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                owner_expr = f"({owner_expr})"
            owner_mod = self._resolve_imported_module_name(owner_expr)
            attr = fn.get("attr")
            if isinstance(attr, str):
                owner_map = self.module_attr_call_map.get(owner_mod)
                if isinstance(owner_map, dict):
                    runtime_call = owner_map.get(attr)
                    if isinstance(runtime_call, str):
                        return f"{runtime_call}({', '.join(args)})"
            if owner_mod in {"png_helper", "png", "pylib.png"} and attr == "write_rgb_png":
                return f"png_helper::write_rgb_png({', '.join(args)})"
            if owner_mod in {"gif_helper", "gif", "pylib.gif"} and attr == "save_gif":
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
            if owner_t == "unknown":
                if attr == "clear":
                    return f"{owner_expr}.clear()"
        return None

    def render_expr(self, expr: Any) -> str:
        """式ノードを C++ の式文字列へ変換する中核処理。"""
        expr_node = self.any_to_dict(expr)
        if expr_node is None:
            return "/* none */"
        expr = expr_node
        kind = expr.get("kind")

        if kind == "Name":
            name = str(expr.get("id", "_"))
            if name in self.renamed_symbols:
                return self.renamed_symbols[name]
            if name in self.reserved_words:
                renamed = f"{self.rename_prefix}{name}"
                self.renamed_symbols[name] = renamed
                return renamed
            return name
        if kind == "Constant":
            v = expr.get("value")
            if isinstance(v, bool):
                return "true" if v else "false"
            if v is None:
                t = self.get_expr_type(expr)
                if self.is_any_like_type(t):
                    return "object{}"
                return "std::nullopt"
            if isinstance(v, str):
                if self.get_expr_type(expr) == "bytes":
                    raw = expr.get("repr")
                    if isinstance(raw, str):
                        qpos = -1
                        i = 0
                        while i < len(raw):
                            if raw[i] in {'"', "'"}:
                                qpos = i
                                break
                            i += 1
                        if qpos >= 0:
                            return f"py_bytes_lit({raw[qpos:]})"
                    return f"bytes({cpp_string_lit(v)})"
                return cpp_string_lit(v)
            return str(v)
        if kind == "Attribute":
            owner_t = self.get_expr_type(expr.get("value"))
            if self.is_forbidden_object_receiver_type(owner_t):
                raise RuntimeError(
                    "object receiver attribute access is forbidden by language constraints"
                )
            base = self.render_expr(expr.get("value"))
            base_node = expr.get("value")
            if isinstance(base_node, dict) and base_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                base = f"({base})"
            attr = expr.get("attr", "")
            if base == "self":
                if self.current_class_name is not None and str(attr) in self.current_class_static_fields:
                    return f"{self.current_class_name}::{attr}"
                return f"this->{attr}"
            # Class-name qualified member access in EAST uses dot syntax.
            # Emit C++ scope resolution for static members/methods.
            if base in self.class_base or base in self.class_method_names:
                return f"{base}::{attr}"
            base_module_name = self._resolve_imported_module_name(base)
            if base_module_name == "math":
                if attr == "pi":
                    return "py_math::pi"
                if attr == "e":
                    return "py_math::e"
            bt = self.get_expr_type(expr.get("value"))
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
            fn_raw = expr.get("func")
            fn = fn_raw if isinstance(fn_raw, dict) else {}
            if fn.get("kind") == "Attribute":
                owner_node = fn.get("value")
                owner_t = self.get_expr_type(owner_node)
                if self.is_forbidden_object_receiver_type(owner_t):
                    raise RuntimeError(
                        "object receiver method call is forbidden by language constraints"
                    )
            fn_name = self.render_expr(fn)
            arg_nodes = expr.get("args", [])
            args = [self.render_expr(a) for a in arg_nodes]
            keywords = expr.get("keywords", [])
            first_arg = arg_nodes[0] if isinstance(arg_nodes, list) and len(arg_nodes) > 0 else None
            kw: dict[str, str] = {}
            for k in keywords:
                kname = k.get("arg")
                if isinstance(kname, str):
                    kw[kname] = self.render_expr(k.get("value"))
            hook_call = self.hook_on_render_call(
                self,
                expr,
                fn,
                list(args),
                dict(kw),
            )
            if isinstance(hook_call, str) and hook_call != "":
                return hook_call
            if expr.get("lowered_kind") == "BuiltinCall":
                builtin_rendered = self._render_builtin_call(expr, fn, args, kw, first_arg)
                if isinstance(builtin_rendered, str):
                    return builtin_rendered
            name_or_attr = self._render_call_name_or_attr(expr, fn, fn_name, args, kw, arg_nodes, first_arg)
            if isinstance(name_or_attr, str) and name_or_attr != "":
                return name_or_attr
            return f"{fn_name}({', '.join(args)})"
        if kind == "RangeExpr":
            start = self.render_expr(expr.get("start"))
            stop = self.render_expr(expr.get("stop"))
            step = self.render_expr(expr.get("step"))
            return f"py_range({start}, {stop}, {step})"
        if kind == "BinOp":
            return self._render_binop_expr(expr)
        if kind == "UnaryOp":
            operand_expr = expr.get("operand")
            operand = self.render_expr(operand_expr)
            op = expr.get("op")
            if op == "Not":
                if isinstance(operand_expr, dict) and operand_expr.get("kind") == "Compare":
                    if operand_expr.get("lowered_kind") == "Contains":
                        container = self.render_expr(operand_expr.get("container"))
                        key = self.render_expr(operand_expr.get("key"))
                        ctype0 = self.get_expr_type(operand_expr.get("container"))
                        ctype = ctype0 if isinstance(ctype0, str) else ""
                        if ctype.startswith("dict["):
                            return f"{container}.find({key}) == {container}.end()"
                        return f"std::find({container}.begin(), {container}.end(), {key}) == {container}.end()"
                    ops = operand_expr.get("ops", [])
                    cmps = operand_expr.get("comparators", [])
                    if len(ops) == 1 and len(cmps) == 1:
                        left = self.render_expr(operand_expr.get("left"))
                        rhs = self.render_expr(cmps[0])
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
                            rhs_type0 = self.get_expr_type(cmps[0])
                            rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
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
        if kind == "BoolOp":
            return self.render_boolop(expr, False)
        if kind == "Compare":
            if expr.get("lowered_kind") == "Contains":
                container = self.render_expr(expr.get("container"))
                key = self.render_expr(expr.get("key"))
                ctype0 = self.get_expr_type(expr.get("container"))
                ctype = ctype0 if isinstance(ctype0, str) else ""
                if ctype.startswith("dict["):
                    base = f"{container}.find({key}) != {container}.end()"
                else:
                    base = f"std::find({container}.begin(), {container}.end(), {key}) != {container}.end()"
                if bool(expr.get("negated", False)):
                    return f"!({base})"
                return base
            left = self.render_expr(expr.get("left"))
            ops = expr.get("ops", [])
            cmps = expr.get("comparators", [])
            parts: list[str] = []
            cur = left
            cur_node = expr.get("left")
            for i, op in enumerate(ops):
                rhs_node = cmps[i] if i < len(cmps) and isinstance(cmps[i], dict) else None
                rhs = self.render_expr(rhs_node)
                cop = CMP_OPS.get(op, "==")
                if cop == "/* in */":
                    rhs_type0 = self.get_expr_type(rhs_node)
                    rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                    if rhs_type.startswith("dict["):
                        parts.append(f"{rhs}.find({cur}) != {rhs}.end()")
                    else:
                        parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) != {rhs}.end()")
                elif cop == "/* not in */":
                    rhs_type0 = self.get_expr_type(rhs_node)
                    rhs_type = rhs_type0 if isinstance(rhs_type0, str) else ""
                    if rhs_type.startswith("dict["):
                        parts.append(f"{rhs}.find({cur}) == {rhs}.end()")
                    else:
                        parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) == {rhs}.end()")
                else:
                    opt_cmp = self._try_optimize_char_compare(cur_node if isinstance(cur_node, dict) else None, op, rhs_node)
                    if opt_cmp is not None:
                        parts.append(opt_cmp)
                    elif op in {"Is", "IsNot"} and rhs == "std::nullopt":
                        parts.append(f"{'!' if op == 'IsNot' else ''}py_is_none({cur})")
                    elif op in {"Is", "IsNot"} and cur == "std::nullopt":
                        parts.append(f"{'!' if op == 'IsNot' else ''}py_is_none({rhs})")
                    else:
                        parts.append(f"{cur} {cop} {rhs}")
                cur = rhs
                cur_node = rhs_node
            return " && ".join(parts) if parts else "true"
        if kind == "IfExp":
            body = self.render_expr(expr.get("body"))
            orelse = self.render_expr(expr.get("orelse"))
            for c in expr.get("casts", []):
                on = c.get("on")
                to_t = c.get("to")
                if on == "body":
                    body = self.apply_cast(body, to_t)
                elif on == "orelse":
                    orelse = self.apply_cast(orelse, to_t)
            return f"({self.render_expr(expr.get('test'))} ? {body} : {orelse})"
        if kind == "List":
            t = self.cpp_type(expr.get("resolved_type"))
            elem_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("list[") and rt.endswith("]"):
                elem_t = rt[5:-1].strip()
            parts: list[str] = []
            for e in expr.get("elements", []):
                rv = self.render_expr(e)
                if self.is_any_like_type(elem_t):
                    rv = f"make_object({rv})"
                parts.append(rv)
            items = ", ".join(parts)
            return f"{t}{{{items}}}"
        if kind == "Tuple":
            items = ", ".join(self.render_expr(e) for e in expr.get("elements", []))
            return f"std::make_tuple({items})"
        if kind == "Set":
            t = self.cpp_type(expr.get("resolved_type"))
            items = ", ".join(self.render_expr(e) for e in expr.get("elements", []))
            return f"{t}{{{items}}}"
        if kind == "Dict":
            t = self.cpp_type(expr.get("resolved_type"))
            items: list[str] = []
            key_t = ""
            val_t = ""
            rt = self.get_expr_type(expr)
            if isinstance(rt, str) and rt.startswith("dict[") and rt.endswith("]"):
                inner = self.split_generic(rt[5:-1])
                if len(inner) == 2:
                    key_t = inner[0]
                    val_t = inner[1]
            for kv in expr.get("entries", []):
                k = self.render_expr(kv.get("key"))
                v = self.render_expr(kv.get("value"))
                if self.is_any_like_type(key_t):
                    k = f"make_object({k})"
                if self.is_any_like_type(val_t):
                    v = f"make_object({v})"
                items.append(f"{{{k}, {v}}}")
            return f"{t}{{{', '.join(items)}}}"
        if kind == "Subscript":
            val = self.render_expr(expr.get("value"))
            val_ty0 = self.get_expr_type(expr.get("value"))
            val_ty = val_ty0 if isinstance(val_ty0, str) else ""
            if expr.get("lowered_kind") == "SliceExpr":
                lo = self.render_expr(expr.get("lower")) if expr.get("lower") is not None else "0"
                up = self.render_expr(expr.get("upper")) if expr.get("upper") is not None else f"py_len({val})"
                return f"py_slice({val}, {lo}, {up})"
            sl = expr.get("slice")
            if isinstance(sl, dict) and sl.get("kind") == "Slice":
                lo = self.render_expr(sl.get("lower")) if sl.get("lower") is not None else "0"
                up = self.render_expr(sl.get("upper")) if sl.get("upper") is not None else f"py_len({val})"
                return f"py_slice({val}, {lo}, {up})"
            idx = self.render_expr(sl)
            if val_ty.startswith("dict["):
                return f"py_dict_get({val}, {idx})"
            if self.is_indexable_sequence_type(val_ty):
                if self.negative_index_mode == "off":
                    return f"{val}[{idx}]"
                if self.negative_index_mode == "const_only":
                    if self._is_negative_const_index(sl):
                        return f"py_at({val}, {idx})"
                    return f"{val}[{idx}]"
                return f"py_at({val}, {idx})"
            return f"{val}[{idx}]"
        if kind == "JoinedStr":
            if expr.get("lowered_kind") == "Concat":
                parts: list[str] = []
                for p in expr.get("concat_parts", []):
                    if p.get("kind") == "literal":
                        parts.append(cpp_string_lit(str(p.get("value", ""))))
                    elif p.get("kind") == "expr":
                        val = p.get("value")
                        if val is None:
                            parts.append('""')
                        else:
                            vtxt = self.render_expr(val)
                            vty = self.get_expr_type(val)
                            if vty == "str":
                                parts.append(vtxt)
                            else:
                                parts.append(self.render_to_string(val if isinstance(val, dict) else None))
                if len(parts) == 0:
                    return '""'
                return " + ".join(parts)
            parts: list[str] = []
            for p in expr.get("values", []):
                pk = p.get("kind")
                if pk == "Constant":
                    parts.append(cpp_string_lit(str(p.get("value", ""))))
                elif pk == "FormattedValue":
                    v = p.get("value")
                    vtxt = self.render_expr(v)
                    vty = self.get_expr_type(v if isinstance(v, dict) else None)
                    if vty == "str":
                        parts.append(vtxt)
                    else:
                        parts.append(self.render_to_string(v if isinstance(v, dict) else None))
            if not parts:
                return '""'
            return " + ".join(parts)
        if kind == "Lambda":
            arg_texts: list[str] = []
            for a in expr.get("args", []):
                if isinstance(a, dict):
                    nm = str(a.get("arg", "")).strip()
                    if nm != "":
                        arg_texts.append(f"auto {nm}")
            body_expr = self.render_expr(expr.get("body"))
            return f"[&]({', '.join(arg_texts)}) {{ return {body_expr}; }}"
        if kind == "ListComp":
            gens = expr.get("generators", [])
            if len(gens) != 1:
                return "{}"
            g = gens[0]
            g_target = g.get("target")
            tgt = self.render_expr(g_target)
            it = self.render_expr(g.get("iter"))
            elt = self.render_expr(expr.get("elt"))
            out_t = self.cpp_type(expr.get("resolved_type"))
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = isinstance(g_target, dict) and g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if isinstance(g.get("iter"), dict) and g.get("iter", {}).get("kind") == "RangeExpr":
                rg = g.get("iter", {})
                start = self.render_expr(rg.get("start"))
                stop = self.render_expr(rg.get("stop"))
                step = self.render_expr(rg.get("step"))
                mode = rg.get("range_mode")
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
                    for i, e in enumerate(g_target.get("elements", [])):
                        if isinstance(e, dict) and e.get("kind") == "Name":
                            nm = self.render_expr(e)
                            lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
                else:
                    lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = g.get("ifs", [])
            if len(ifs) == 0:
                lines.append(f"        __out.append({elt});")
            else:
                cond = " && ".join(self.render_expr(c) for c in ifs)
                lines.append(f"        if ({cond}) __out.append({elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)
        if kind == "SetComp":
            gens = expr.get("generators", [])
            if len(gens) != 1:
                return "{}"
            g = gens[0]
            g_target = g.get("target")
            tgt = self.render_expr(g_target)
            it = self.render_expr(g.get("iter"))
            elt = self.render_expr(expr.get("elt"))
            out_t = self.cpp_type(expr.get("resolved_type"))
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = isinstance(g_target, dict) and g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                for i, e in enumerate(g_target.get("elements", [])):
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = g.get("ifs", [])
            if len(ifs) == 0:
                lines.append(f"        __out.insert({elt});")
            else:
                cond = " && ".join(self.render_expr(c) for c in ifs)
                lines.append(f"        if ({cond}) __out.insert({elt});")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)
        if kind == "DictComp":
            gens = expr.get("generators", [])
            if len(gens) != 1:
                return "{}"
            g = gens[0]
            g_target = g.get("target")
            tgt = self.render_expr(g_target)
            it = self.render_expr(g.get("iter"))
            key = self.render_expr(expr.get("key"))
            val = self.render_expr(expr.get("value"))
            out_t = self.cpp_type(expr.get("resolved_type"))
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
            tuple_unpack = isinstance(g_target, dict) and g_target.get("kind") == "Tuple"
            iter_tmp = self.next_tmp("__it")
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                for i, e in enumerate(g_target.get("elements", [])):
                    if isinstance(e, dict) and e.get("kind") == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
            ifs = g.get("ifs", [])
            if len(ifs) == 0:
                lines.append(f"        __out[{key}] = {val};")
            else:
                cond = " && ".join(self.render_expr(c) for c in ifs)
                lines.append(f"        if ({cond}) __out[{key}] = {val};")
            lines.append("    }")
            lines.append("    return __out;")
            lines.append("}()")
            return " ".join(lines)

        rep = expr.get("repr")
        if isinstance(rep, str) and rep != "":
            return rep
        return f"/* unsupported expr: {kind} */"

    def emit_bridge_comment(self, expr: dict[str, Any] | None) -> None:
        """ランタイムブリッジ呼び出しの補助コメントを必要時に付与する。"""
        if expr is None or expr.get("kind") != "Call":
            return
        fn = expr.get("func")
        if not isinstance(fn, dict):
            return
        key = ""
        text = ""
        if fn.get("kind") == "Name":
            name = str(fn.get("id", ""))
            if name == "save_gif":
                key = "save_gif"
                text = "// bridge: Python gif.save_gif -> C++ runtime save_gif"
            elif name == "write_rgb_png":
                key = "write_rgb_png"
                text = "// bridge: Python png.write_rgb_png -> C++ runtime png_helper::write_rgb_png"
        elif fn.get("kind") == "Attribute":
            owner = fn.get("value")
            owner_name = ""
            if isinstance(owner, dict) and owner.get("kind") == "Name":
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
        east_type = self.normalize_type_name(east_type)
        if east_type == "":
            return "auto"
        mapped = self.type_map.get(east_type)
        if isinstance(mapped, str) and mapped != "":
            return mapped
        if east_type in {"Any", "object"}:
            return "object"
        if "|" in east_type:
            parts = self.split_union(east_type)
            if len(parts) >= 2:
                non_none = [p for p in parts if p != "None"]
                if len(non_none) >= 1 and set(non_none).issubset({"bytes", "bytearray"}):
                    return "bytes"
                if any(self.is_any_like_type(p) for p in non_none):
                    return "object"
                if len(parts) == 2 and len(non_none) == 1:
                    return f"std::optional<{self.cpp_type(non_none[0])}>"
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
                return f"list<{self.cpp_type(inner[0])}>"
        if east_type.startswith("set[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[4:-1])
            if len(inner) == 1:
                if inner[0] == "unknown":
                    return "set<str>"
                return f"set<{self.cpp_type(inner[0])}>"
        if east_type.startswith("dict[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 2:
                if self.is_any_like_type(inner[1]):
                    return f"dict<{self.cpp_type(inner[0] if inner[0] != 'unknown' else 'str')}, object>"
                if inner[0] == "unknown" and inner[1] == "unknown":
                    return "dict<str, std::any>"
                if inner[0] == "unknown":
                    return f"dict<str, {self.cpp_type(inner[1])}>"
                if inner[1] == "unknown":
                    return f"dict<{self.cpp_type(inner[0])}, std::any>"
                return f"dict<{self.cpp_type(inner[0])}, {self.cpp_type(inner[1])}>"
        if east_type.startswith("tuple[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[6:-1])
            return "std::tuple<" + ", ".join(self.cpp_type(x) for x in inner) + ">"
        if east_type == "unknown":
            return "std::any"
        if east_type.startswith("callable["):
            return "auto"
        if east_type == "callable":
            return "auto"
        if east_type == "module":
            return "auto"
        return east_type


def load_east(input_path: Path, *, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    return load_east_from_path(input_path, parser_backend=parser_backend)


def transpile_to_cpp(
    east_module: dict[str, Any],
    *,
    negative_index_mode: str = "const_only",
    emit_main: bool = True,
) -> str:
    """EAST Module を C++ ソース文字列へ変換する。"""
    return CppEmitter(
        east_module,
        negative_index_mode=negative_index_mode,
        emit_main=emit_main,
    ).transpile()


def main(argv: list[str] | None = None) -> int:
    """CLI エントリポイント。変換実行と入出力を担当する。"""
    ap = argparse.ArgumentParser(description="Transpile Python/EAST to C++ via EAST")
    add_common_transpile_args(
        ap,
        enable_negative_index_mode=True,
        parser_backends=["self_hosted"],
    )
    ap.add_argument(
        "--no-main",
        action="store_true",
        help="Do not emit C++ main() (library/module output mode).",
    )
    args = normalize_common_transpile_args(
        ap.parse_args(argv),
        default_negative_index_mode="const_only",
        default_parser_backend="self_hosted",
    )

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east_module = load_east(input_path, parser_backend=args.parser_backend)
        cpp = transpile_to_cpp(
            east_module,
            negative_index_mode=args.negative_index_mode,
            emit_main=not bool(args.no_main),
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cpp, encoding="utf-8")
    else:
        print(cpp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

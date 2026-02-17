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

from common.east import EastBuildError, convert_path


CPP_HEADER = """#include "cpp_module/py_runtime.h"

"""


BIN_OPS = {
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

CMP_OPS = {
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

AUG_OPS = {
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

AUG_BIN = {
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


class CppEmitter:
    def __init__(self, east_doc: dict[str, Any], *, negative_index_mode: str = "const_only") -> None:
        self.doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_id = 0
        self.negative_index_mode = negative_index_mode
        self.renamed_symbols: dict[str, str] = {
            str(k): str(v) for k, v in self.doc.get("renamed_symbols", {}).items()
        }
        self.scope_stack: list[set[str]] = [set()]
        self.current_class_name: str | None = None
        self.current_class_fields: dict[str, str] = {}
        self.current_class_static_fields: set[str] = set()
        self.class_method_names: dict[str, set[str]] = {}
        self.class_base: dict[str, str | None] = {}

    def emit(self, line: str = "") -> None:
        self.lines.append(("    " * self.indent) + line)

    def _stmt_start_line(self, stmt: dict[str, Any]) -> int | None:
        span = stmt.get("source_span")
        if isinstance(span, dict):
            v = span.get("lineno")
            if isinstance(v, int) and v > 0:
                return v
        return None

    def _stmt_end_line(self, stmt: dict[str, Any]) -> int | None:
        span = stmt.get("source_span")
        if isinstance(span, dict):
            v = span.get("end_lineno")
            if isinstance(v, int) and v > 0:
                return v
            v2 = span.get("lineno")
            if isinstance(v2, int) and v2 > 0:
                return v2
        return None

    def _has_leading_trivia(self, stmt: dict[str, Any]) -> bool:
        trivia = stmt.get("leading_trivia")
        return isinstance(trivia, list) and len(trivia) > 0

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        prev_end: int | None = None
        for stmt in stmts:
            start = self._stmt_start_line(stmt)
            if (
                prev_end is not None
                and start is not None
                and start > prev_end + 1
                and not self._has_leading_trivia(stmt)
            ):
                for _ in range(start - prev_end - 1):
                    self.emit()
            self.emit_stmt(stmt)
            end = self._stmt_end_line(stmt)
            if end is not None:
                prev_end = end

    def emit_block_comment(self, text: str) -> None:
        """Emit C-style block comment for docstring-like standalone strings."""
        safe = text.replace("*/", "* /")
        parts = safe.splitlines()
        if len(parts) == 0:
            self.emit("/* */")
            return
        if len(parts) == 1:
            self.emit(f"/* {parts[0]} */")
            return
        self.emit("/*")
        for line in parts:
            self.emit(line)
        self.emit("*/")

    def emit_leading_comments(self, stmt: dict[str, Any]) -> None:
        trivia = stmt.get("leading_trivia")
        if isinstance(trivia, list):
            for item in trivia:
                if not isinstance(item, dict):
                    continue
                k = item.get("kind")
                if k == "comment":
                    text = item.get("text")
                    if isinstance(text, str) and text != "":
                        self.emit("// " + text)
                elif k == "blank":
                    count_raw = item.get("count", 1)
                    count = count_raw if isinstance(count_raw, int) and count_raw > 0 else 1
                    for _ in range(count):
                        self.emit()
            return

        # Backward compatibility for older EAST payloads.
        comments = stmt.get("leading_comments")
        if isinstance(comments, list):
            for c in comments:
                if isinstance(c, str) and c != "":
                    self.emit("// " + c)

    def next_tmp(self, prefix: str = "__tmp") -> str:
        self.tmp_id += 1
        return f"{prefix}_{self.tmp_id}"

    def transpile(self) -> str:
        for stmt in self.doc.get("body", []):
            if stmt.get("kind") == "ClassDef":
                cls_name = str(stmt.get("name", ""))
                if cls_name != "":
                    mset: set[str] = set()
                    for s in stmt.get("body", []):
                        if s.get("kind") == "FunctionDef":
                            mset.add(str(s.get("name")))
                    self.class_method_names[cls_name] = mset
                    base = stmt.get("base")
                    self.class_base[cls_name] = str(base) if isinstance(base, str) else None

        self.emit_module_leading_trivia()
        self.emit(CPP_HEADER.rstrip("\n"))
        self.emit()

        for stmt in self.doc.get("body", []):
            self.emit_stmt(stmt)
            self.emit()

        self.emit("int main(int argc, char** argv) {")
        self.indent += 1
        self.emit("pytra_configure_from_argv(argc, argv);")
        self.scope_stack.append(set())
        self.emit_stmt_list(list(self.doc.get("main_guard_body", [])))
        self.scope_stack.pop()
        self.emit("return 0;")
        self.indent -= 1
        self.emit("}")
        self.emit()
        return "\n".join(self.lines)

    def emit_module_leading_trivia(self) -> None:
        trivia = self.doc.get("module_leading_trivia")
        if not isinstance(trivia, list):
            return
        for item in trivia:
            if not isinstance(item, dict):
                continue
            k = item.get("kind")
            if k == "comment":
                text = item.get("text")
                if isinstance(text, str):
                    self.emit("// " + text)
            elif k == "blank":
                count_raw = item.get("count", 1)
                count = count_raw if isinstance(count_raw, int) and count_raw > 0 else 1
                for _ in range(count):
                    self.emit()
        if len(trivia) > 0:
            self.emit()

    def current_scope(self) -> set[str]:
        return self.scope_stack[-1]

    def is_declared(self, name: str) -> bool:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return True
        return False

    def render_cond(self, expr: dict[str, Any] | None) -> str:
        t = self.get_expr_type(expr) or ""
        body = self._strip_outer_parens(self.render_expr(expr))
        if t in {"bool"}:
            return body
        if t == "str" or t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return f"py_len({body}) != 0"
        return body

    def _strip_outer_parens(self, text: str) -> str:
        s = text.strip()
        while len(s) >= 2 and s.startswith("(") and s.endswith(")"):
            depth = 0
            in_str = False
            esc = False
            quote = ""
            wrapped = True
            for i, ch in enumerate(s):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == quote:
                        in_str = False
                    continue
                if ch in {"'", '"'}:
                    in_str = True
                    quote = ch
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0 and i != len(s) - 1:
                        wrapped = False
                        break
            if wrapped and depth == 0:
                s = s[1:-1].strip()
                continue
            break
        return s

    def apply_cast(self, rendered_expr: str, to_type: str | None) -> str:
        if not isinstance(to_type, str) or to_type == "":
            return rendered_expr
        return f"static_cast<{self.cpp_type(to_type)}>({rendered_expr})"

    def render_to_string(self, expr: dict[str, Any] | None) -> str:
        rendered = self.render_expr(expr)
        t = self.get_expr_type(expr) or ""
        if t == "str":
            return rendered
        if t == "bool":
            return f"py_bool_to_string({rendered})"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64"}:
            return f"std::to_string({rendered})"
        return f"py_to_string({rendered})"

    def _binop_precedence(self, op_name: str) -> int:
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

    def _wrap_for_binop_operand(
        self,
        rendered: str,
        operand_expr: dict[str, Any] | None,
        parent_op: str,
        *,
        is_right: bool,
    ) -> str:
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
        if is_right and child_prec == parent_prec and parent_op in {"Sub", "Div", "FloorDiv", "Mod", "LShift", "RShift"}:
            return f"({rendered})"
        return rendered

    def render_minmax(self, fn: str, args: list[str], out_type: str | None) -> str:
        if len(args) == 0:
            return "/* invalid min/max */"
        if len(args) == 1:
            return args[0]
        t = self.cpp_type(out_type or "auto")
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

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
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
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "Constant" and isinstance(value.get("value"), str):
                self.emit_block_comment(str(value.get("value")))
            else:
                self.emit(self.render_expr(value) + ";")
            return
        if kind == "Return":
            v = stmt.get("value")
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
            self.emit(f"py_swap({left}, {right});")
            return
        if kind == "AnnAssign":
            t = self.cpp_type(stmt.get("annotation"))
            target = self.render_expr(stmt.get("target"))
            val = stmt.get("value")
            rendered_val = self.render_expr(val) if val is not None else None
            if isinstance(val, dict) and t != "auto":
                vkind = val.get("kind")
                if vkind == "List" and len(val.get("elements", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "Dict" and len(val.get("entries", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "Set" and len(val.get("elements", [])) == 0:
                    rendered_val = f"{t}{{}}"
                elif vkind == "ListComp" and isinstance(rendered_val, str):
                    rendered_val = rendered_val.replace("-> auto", f"-> {t}", 1).replace("auto __out", f"{t} __out", 1)
                    rendered_val = rendered_val.replace("-> list<auto>", f"-> {t}", 1).replace("list<auto> __out", f"{t} __out", 1)
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
            op = AUG_OPS.get(stmt.get("op"), "+=")
            target_expr = stmt.get("target")
            target = self.render_lvalue(target_expr)
            declare = bool(stmt.get("declare", False))
            if declare and self.is_plain_name_expr(target_expr) and target not in self.current_scope():
                t = self.cpp_type(stmt.get("decl_type") or self.get_expr_type(target_expr))
                self.current_scope().add(target)
                self.emit(f"{t} {target} = {self.render_expr(stmt.get('value'))};")
                return
            val = self.render_expr(stmt.get("value"))
            op_name = str(stmt.get("op"))
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
            body_stmts = list(stmt.get("body", []))
            else_stmts = list(stmt.get("orelse", []))
            if self._can_omit_braces_for_single_stmt(body_stmts) and (len(else_stmts) == 0 or self._can_omit_braces_for_single_stmt(else_stmts)):
                self.emit(f"if ({self.render_cond(stmt.get('test'))})")
                self.indent += 1
                self.scope_stack.append(set())
                self.emit_stmt(body_stmts[0])
                self.scope_stack.pop()
                self.indent -= 1
                if len(else_stmts) > 0:
                    self.emit("else")
                    self.indent += 1
                    self.scope_stack.append(set())
                    self.emit_stmt(else_stmts[0])
                    self.scope_stack.pop()
                    self.indent -= 1
                return

            self.emit(f"if ({self.render_cond(stmt.get('test'))}) {{")
            self.indent += 1
            self.scope_stack.append(set())
            self.emit_stmt_list(body_stmts)
            self.scope_stack.pop()
            self.indent -= 1
            if len(else_stmts) > 0:
                self.emit("} else {")
                self.indent += 1
                self.scope_stack.append(set())
                self.emit_stmt_list(else_stmts)
                self.scope_stack.pop()
                self.indent -= 1
                self.emit("}")
            else:
                self.emit("}")
            return
        if kind == "While":
            self.emit(f"while ({self.render_cond(stmt.get('test'))}) {{")
            self.indent += 1
            self.scope_stack.append(set())
            self.emit_stmt_list(list(stmt.get("body", [])))
            self.scope_stack.pop()
            self.indent -= 1
            self.emit("}")
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
            self.emit("try {")
            self.indent += 1
            self.emit_stmt_list(list(stmt.get("body", [])))
            self.indent -= 1
            self.emit("}")
            for h in stmt.get("handlers", []):
                name = h.get("name") or "ex"
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
            self.emit_function(stmt)
            return
        if kind == "ClassDef":
            self.emit_class(stmt)
            return

        self.emit(f"/* unsupported stmt kind: {kind} */")

    def _can_omit_braces_for_single_stmt(self, stmts: list[dict[str, Any]]) -> bool:
        if len(stmts) != 1:
            return False
        k = stmts[0].get("kind")
        return k in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}

    def emit_assign(self, stmt: dict[str, Any]) -> None:
        target = stmt.get("target")
        value = stmt.get("value")
        if target is None or value is None:
            self.emit("/* invalid assign */")
            return
        if target.get("kind") == "Tuple":
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
            dtype = self.cpp_type(stmt.get("decl_type") or self.get_expr_type(target) or self.get_expr_type(value))
            self.current_scope().add(texpr)
            self.emit(f"{dtype} {texpr} = {self.render_expr(value)};")
            return
        self.emit(f"{texpr} = {self.render_expr(value)};")

    def is_plain_name_expr(self, expr: dict[str, Any] | None) -> bool:
        return isinstance(expr, dict) and expr.get("kind") == "Name"

    def render_lvalue(self, expr: dict[str, Any] | None) -> str:
        if not isinstance(expr, dict):
            return self.render_expr(expr)
        if expr.get("kind") != "Subscript":
            return self.render_expr(expr)
        val_expr = expr.get("value")
        val = self.render_expr(val_expr)
        val_ty = self.get_expr_type(val_expr) or ""
        sl = expr.get("slice")
        idx = self.render_expr(sl)
        if val_ty.startswith("dict["):
            return f"{val}[{idx}]"
        if val_ty.startswith("list["):
            if self.negative_index_mode == "off":
                return f"{val}[{idx}]"
            if self.negative_index_mode == "const_only":
                is_neg_const = False
                if isinstance(sl, dict) and sl.get("kind") == "Constant":
                    v = sl.get("value")
                    is_neg_const = isinstance(v, int) and v < 0
                elif isinstance(sl, dict) and sl.get("kind") == "UnaryOp" and sl.get("op") == "USub":
                    opd = sl.get("operand")
                    if isinstance(opd, dict) and opd.get("kind") == "Constant" and isinstance(opd.get("value"), int):
                        is_neg_const = True
                if is_neg_const:
                    return f"py_at({val}, {idx})"
                return f"{val}[{idx}]"
            return f"py_at({val}, {idx})"
        return f"{val}[{idx}]"

    def emit_for_range(self, stmt: dict[str, Any]) -> None:
        tgt = self.render_expr(stmt.get("target"))
        tgt_ty = self.cpp_type(stmt.get("target_type") or self.get_expr_type(stmt.get("target")))
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
        target = stmt.get("target")
        iter_expr = stmt.get("iter")
        if isinstance(iter_expr, dict) and iter_expr.get("kind") == "RangeExpr":
            pseudo = {
                "target": target,
                "target_type": stmt.get("target_type") or "int64",
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
        t_ty = self.cpp_type(stmt.get("target_type") or self.get_expr_type(target))
        if t_ty == "auto":
            hdr = f"for (auto& {t} : {it})"
        else:
            hdr = f"for ({t_ty} {t} : {it})"
        if omit_braces:
            self.emit(hdr)
            self.indent += 1
            self.scope_stack.append({t})
            self.emit_stmt(body_stmts[0])
            self.scope_stack.pop()
            self.indent -= 1
            return

        self.emit(hdr + " {")
        self.indent += 1
        self.scope_stack.append({t})
        self.emit_stmt_list(body_stmts)
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("}")

    def emit_function(self, stmt: dict[str, Any], *, in_class: bool = False) -> None:
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
            self.emit(f"{self.current_class_name}({', '.join(params)}) {{")
        else:
            self.emit(f"{ret} {name}({', '.join(params)}) {{")
        self.indent += 1
        self.scope_stack.append(fn_scope)
        self.emit_stmt_list(list(stmt.get("body", [])))
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("}")

    def emit_class(self, stmt: dict[str, Any]) -> None:
        name = stmt.get("name", "Class")
        is_dataclass = bool(stmt.get("dataclass", False))
        base = stmt.get("base")
        base_txt = f" : public {base}" if isinstance(base, str) and base != "" else ""
        self.emit(f"struct {name}{base_txt} {{")
        self.indent += 1
        prev_class = self.current_class_name
        prev_fields = self.current_class_fields
        prev_static_fields = self.current_class_static_fields
        self.current_class_name = str(name)
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
            self.emit()
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
            self.emit()
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
        self.current_class_fields = prev_fields
        self.current_class_static_fields = prev_static_fields
        self.indent -= 1
        self.emit("};")

    def render_expr(self, expr: dict[str, Any] | None) -> str:
        if expr is None:
            return "/* none */"
        kind = expr.get("kind")

        if kind == "Name":
            name = str(expr.get("id", "_"))
            return self.renamed_symbols.get(name, name)
        if kind == "Constant":
            v = expr.get("value")
            if isinstance(v, bool):
                return "true" if v else "false"
            if v is None:
                return "nullptr"
            if isinstance(v, str):
                return json.dumps(v)
            return str(v)
        if kind == "Attribute":
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
            if base == "math":
                if attr == "pi":
                    return "py_math::pi"
                if attr == "e":
                    return "py_math::e"
            bt = self.get_expr_type(expr.get("value"))
            if bt == "Path":
                if attr == "name":
                    return f"{base}.name()"
                if attr == "stem":
                    return f"{base}.stem()"
                if attr == "parent":
                    return f"{base}.parent()"
            return f"{base}.{attr}"
        if kind == "Call":
            fn = expr.get("func") or {}
            fn_name = self.render_expr(fn)
            args = [self.render_expr(a) for a in expr.get("args", [])]
            keywords = expr.get("keywords", [])
            kw: dict[str, str] = {}
            for k in keywords:
                kname = k.get("arg")
                if isinstance(kname, str):
                    kw[kname] = self.render_expr(k.get("value"))
            if expr.get("lowered_kind") == "BuiltinCall":
                runtime_call = expr.get("runtime_call")
                builtin_name = expr.get("builtin_name")
                if runtime_call == "py_print":
                    return f"py_print({', '.join(args)})"
                if runtime_call == "py_len" and len(args) == 1:
                    return f"py_len({args[0]})"
                if runtime_call == "py_to_string" and len(args) == 1:
                    src_expr = (expr.get("args") or [None])[0] if isinstance(expr.get("args"), list) and len(expr.get("args")) > 0 else None
                    return self.render_to_string(src_expr if isinstance(src_expr, dict) else None)
                if runtime_call == "static_cast" and len(args) == 1:
                    target = self.cpp_type(expr.get("resolved_type"))
                    arg_t = self.get_expr_type((expr.get("args") or [None])[0] if isinstance(expr.get("args"), list) and len(expr.get("args")) > 0 else None)
                    numeric_t = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
                    if target == "int64" and arg_t == "str":
                        return f"py_to_int64({args[0]})"
                    if target == "int64" and arg_t in numeric_t:
                        return f"int64({args[0]})"
                    if target == "int64":
                        return f"py_to_int64({args[0]})"
                    return f"static_cast<{target}>({args[0]})"
                if runtime_call in {"py_min", "py_max"} and len(args) >= 1:
                    fn = "min" if runtime_call == "py_min" else "max"
                    return self.render_minmax(fn, args, self.get_expr_type(expr))
                if runtime_call == "perf_counter":
                    return "perf_counter()"
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
                    if palette == "nullptr":
                        palette = "grayscale_palette()"
                    delay_cs = kw.get("delay_cs", "4")
                    loop = kw.get("loop", "0")
                    return f"save_gif({path}, {w}, {h}, {frames}, {palette}, {delay_cs}, {loop})"
                if runtime_call == "py_isdigit" and len(args) == 1:
                    return f"py_isdigit({args[0]})"
                if runtime_call == "py_isalpha" and len(args) == 1:
                    return f"py_isalpha({args[0]})"
                if runtime_call == "std::runtime_error":
                    if len(args) == 0:
                        return 'std::runtime_error("error")'
                    return f"std::runtime_error({args[0]})"
                if runtime_call == "Path":
                    return f"Path({', '.join(args)})"
                if runtime_call == "std::filesystem::create_directories":
                    owner_node = (fn or {}).get("value")
                    owner = self.render_expr(owner_node)
                    if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                        owner = f"({owner})"
                    return f"{owner}.mkdir(true, true)"
                if runtime_call == "std::filesystem::exists":
                    owner_node = (fn or {}).get("value")
                    owner = self.render_expr(owner_node)
                    if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                        owner = f"({owner})"
                    return f"{owner}.exists()"
                if runtime_call == "py_write_text":
                    owner_node = (fn or {}).get("value")
                    owner = self.render_expr(owner_node)
                    if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                        owner = f"({owner})"
                    write_arg = args[0] if len(args) >= 1 else '""'
                    return f"{owner}.write_text({write_arg})"
                if runtime_call == "py_read_text":
                    owner_node = (fn or {}).get("value")
                    owner = self.render_expr(owner_node)
                    if isinstance(owner_node, dict) and owner_node.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                        owner = f"({owner})"
                    return f"{owner}.read_text()"
                if runtime_call == "path_parent":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"{owner}.parent()"
                if runtime_call == "path_name":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"{owner}.name()"
                if runtime_call == "path_stem":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"{owner}.stem()"
                if runtime_call == "identity":
                    owner = self.render_expr((fn or {}).get("value"))
                    return owner
                if runtime_call == "list.append":
                    owner = self.render_expr((fn or {}).get("value"))
                    a0 = args[0] if len(args) >= 1 else "/* missing */"
                    return f"{owner}.append({a0})"
                if runtime_call == "list.extend":
                    owner = self.render_expr((fn or {}).get("value"))
                    a0 = args[0] if len(args) >= 1 else "{}"
                    return f"{owner}.insert({owner}.end(), {a0}.begin(), {a0}.end())"
                if runtime_call == "list.pop":
                    owner = self.render_expr((fn or {}).get("value"))
                    if len(args) == 0:
                        return f"py_pop({owner})"
                    return f"py_pop({owner}, {args[0]})"
                if runtime_call == "list.clear":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"{owner}.clear()"
                if runtime_call == "list.reverse":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"std::reverse({owner}.begin(), {owner}.end())"
                if runtime_call == "list.sort":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"std::sort({owner}.begin(), {owner}.end())"
                if runtime_call == "set.add":
                    owner = self.render_expr((fn or {}).get("value"))
                    a0 = args[0] if len(args) >= 1 else "/* missing */"
                    return f"{owner}.insert({a0})"
                if runtime_call in {"set.discard", "set.remove"}:
                    owner = self.render_expr((fn or {}).get("value"))
                    a0 = args[0] if len(args) >= 1 else "/* missing */"
                    return f"{owner}.erase({a0})"
                if runtime_call == "set.clear":
                    owner = self.render_expr((fn or {}).get("value"))
                    return f"{owner}.clear()"
                if isinstance(runtime_call, str) and runtime_call.startswith("std::"):
                    return f"{runtime_call}({', '.join(args)})"
                if builtin_name in {"bytes", "bytearray"}:
                    return f"bytearray({', '.join(args)})" if len(args) >= 1 else "bytearray{}"
            if fn.get("kind") == "Name":
                raw = fn.get("id")
                if raw == "range":
                    raise RuntimeError("unexpected raw range Call in EAST; expected RangeExpr lowering")
                if raw == "print":
                    return f"py_print({', '.join(args)})"
                if raw == "len" and len(args) == 1:
                    return f"py_len({args[0]})"
                if raw in {"bytes", "bytearray"}:
                    return f"bytearray({', '.join(args)})" if len(args) >= 1 else "bytearray{}"
                if raw == "str" and len(args) == 1:
                    src_expr = (expr.get("args") or [None])[0] if isinstance(expr.get("args"), list) and len(expr.get("args")) > 0 else None
                    return self.render_to_string(src_expr if isinstance(src_expr, dict) else None)
                if raw in {"int", "float", "bool"} and len(args) == 1:
                    target = self.cpp_type(expr.get("resolved_type"))
                    arg_t = self.get_expr_type((expr.get("args") or [None])[0] if isinstance(expr.get("args"), list) and len(expr.get("args")) > 0 else None)
                    numeric_t = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
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
            if fn.get("kind") == "Attribute":
                owner = fn.get("value")
                owner_t = self.get_expr_type(owner)
                owner_expr = self.render_expr(owner)
                if isinstance(owner, dict) and owner.get("kind") in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                    owner_expr = f"({owner_expr})"
                attr = fn.get("attr")
                if owner_expr == "math":
                    math_map = {
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
                    if attr in math_map:
                        return f"{math_map[attr]}({', '.join(args)})"
                if owner_expr == "png_helper" and attr == "write_rgb_png":
                    return f"png_helper::write_rgb_png({', '.join(args)})"
                if owner_t == "Path":
                    if attr == "mkdir":
                        parents = kw.get("parents", "false")
                        exist_ok = kw.get("exist_ok", "false")
                        if len(args) >= 1:
                            parents = args[0]
                        if len(args) >= 2:
                            exist_ok = args[1]
                        return f"{owner_expr}.mkdir({parents}, {exist_ok})"
                    if attr == "exists":
                        return f"{owner_expr}.exists()"
                    if attr == "write_text":
                        write_arg = args[0] if len(args) >= 1 else '""'
                        return f"{owner_expr}.write_text({write_arg})"
                    if attr == "read_text":
                        return f"{owner_expr}.read_text()"
                if attr == "isdigit":
                    return f"py_isdigit({owner_expr})"
                if attr == "isalpha":
                    return f"py_isalpha({owner_expr})"
                if owner_t.startswith("list["):
                    if attr == "append":
                        a0 = args[0] if len(args) >= 1 else "/* missing */"
                        return f"{owner_expr}.append({a0})"
                    if attr == "extend":
                        a0 = args[0] if len(args) >= 1 else "{}"
                        return f"{owner_expr}.insert({owner_expr}.end(), {a0}.begin(), {a0}.end())"
                    if attr == "pop":
                        if len(args) == 0:
                            return f"py_pop({owner_expr})"
                        return f"py_pop({owner_expr}, {args[0]})"
                    if attr == "clear":
                        return f"{owner_expr}.clear()"
                    if attr == "reverse":
                        return f"std::reverse({owner_expr}.begin(), {owner_expr}.end())"
                    if attr == "sort":
                        return f"std::sort({owner_expr}.begin(), {owner_expr}.end())"
                if owner_t.startswith("set["):
                    if attr == "add":
                        a0 = args[0] if len(args) >= 1 else "/* missing */"
                        return f"{owner_expr}.insert({a0})"
                    if attr in {"discard", "remove"}:
                        a0 = args[0] if len(args) >= 1 else "/* missing */"
                        return f"{owner_expr}.erase({a0})"
                    if attr == "clear":
                        return f"{owner_expr}.clear()"
                if owner_t == "unknown":
                    if attr == "append":
                        a0 = args[0] if len(args) >= 1 else "/* missing */"
                        return f"{owner_expr}.append({a0})"
                    if attr == "extend":
                        a0 = args[0] if len(args) >= 1 else "{}"
                        return f"{owner_expr}.insert({owner_expr}.end(), {a0}.begin(), {a0}.end())"
                    if attr == "pop":
                        if len(args) == 0:
                            return f"py_pop({owner_expr})"
                        return f"py_pop({owner_expr}, {args[0]})"
                    if attr == "clear":
                        return f"{owner_expr}.clear()"
            return f"{fn_name}({', '.join(args)})"
        if kind == "RangeExpr":
            start = self.render_expr(expr.get("start"))
            stop = self.render_expr(expr.get("stop"))
            step = self.render_expr(expr.get("step"))
            return f"py_range({start}, {stop}, {step})"
        if kind == "BinOp":
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
            if op_name == "Div":
                # Prefer direct C++ division when float is involved (or EAST already injected casts).
                # Keep py_div fallback for int/int Python semantics.
                lt = self.get_expr_type(left_expr if isinstance(left_expr, dict) else None) or ""
                rt = self.get_expr_type(right_expr if isinstance(right_expr, dict) else None) or ""
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
                lt = self.get_expr_type(expr.get("left")) or ""
                rt = self.get_expr_type(expr.get("right")) or ""
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
        if kind == "UnaryOp":
            operand_expr = expr.get("operand")
            operand = self.render_expr(operand_expr)
            op = expr.get("op")
            if op == "Not":
                if isinstance(operand_expr, dict) and operand_expr.get("kind") == "Compare":
                    if operand_expr.get("lowered_kind") == "Contains":
                        container = self.render_expr(operand_expr.get("container"))
                        key = self.render_expr(operand_expr.get("key"))
                        ctype = self.get_expr_type(operand_expr.get("container")) or ""
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
                            rhs_type = self.get_expr_type(cmps[0]) or ""
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
            values: list[str] = []
            for v in expr.get("values", []):
                txt = self.render_expr(v)
                values.append(f"({txt})")
            op = "&&" if expr.get("op") == "And" else "||"
            return f" {op} ".join(values) if len(values) > 0 else "false"
        if kind == "Compare":
            if expr.get("lowered_kind") == "Contains":
                container = self.render_expr(expr.get("container"))
                key = self.render_expr(expr.get("key"))
                ctype = self.get_expr_type(expr.get("container")) or ""
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
            for i, op in enumerate(ops):
                rhs = self.render_expr(cmps[i])
                cop = CMP_OPS.get(op, "==")
                if cop == "/* in */":
                    rhs_type = self.get_expr_type(cmps[i]) or ""
                    if rhs_type.startswith("dict["):
                        parts.append(f"{rhs}.find({cur}) != {rhs}.end()")
                    else:
                        parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) != {rhs}.end()")
                elif cop == "/* not in */":
                    rhs_type = self.get_expr_type(cmps[i]) or ""
                    if rhs_type.startswith("dict["):
                        parts.append(f"{rhs}.find({cur}) == {rhs}.end()")
                    else:
                        parts.append(f"std::find({rhs}.begin(), {rhs}.end(), {cur}) == {rhs}.end()")
                else:
                    parts.append(f"{cur} {cop} {rhs}")
                cur = rhs
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
            items = ", ".join(self.render_expr(e) for e in expr.get("elements", []))
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
            for kv in expr.get("entries", []):
                k = self.render_expr(kv.get("key"))
                v = self.render_expr(kv.get("value"))
                items.append(f"{{{k}, {v}}}")
            return f"{t}{{{', '.join(items)}}}"
        if kind == "Subscript":
            val = self.render_expr(expr.get("value"))
            val_ty = self.get_expr_type(expr.get("value")) or ""
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
            if val_ty.startswith("list[") or val_ty == "str":
                if self.negative_index_mode == "off":
                    return f"{val}[{idx}]"
                if self.negative_index_mode == "const_only":
                    is_neg_const = False
                    if isinstance(sl, dict) and sl.get("kind") == "Constant":
                        v = sl.get("value")
                        is_neg_const = isinstance(v, int) and v < 0
                    elif isinstance(sl, dict) and sl.get("kind") == "UnaryOp" and sl.get("op") == "USub":
                        opd = sl.get("operand")
                        if isinstance(opd, dict) and opd.get("kind") == "Constant" and isinstance(opd.get("value"), int):
                            is_neg_const = True
                    if is_neg_const:
                        return f"py_at({val}, {idx})"
                    return f"{val}[{idx}]"
                return f"py_at({val}, {idx})"
            return f"{val}[{idx}]"
        if kind == "JoinedStr":
            if expr.get("lowered_kind") == "Concat":
                parts: list[str] = []
                for p in expr.get("concat_parts", []):
                    if p.get("kind") == "literal":
                        parts.append(json.dumps(p.get("value", "")))
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
                    parts.append(json.dumps(p.get("value", "")))
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
        if kind == "ListComp":
            gens = expr.get("generators", [])
            if len(gens) != 1:
                return "{}"
            g = gens[0]
            tgt = self.render_expr(g.get("target"))
            it = self.render_expr(g.get("iter"))
            elt = self.render_expr(expr.get("elt"))
            out_t = self.cpp_type(expr.get("resolved_type"))
            lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
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

        rep = expr.get("repr")
        if isinstance(rep, str) and rep != "":
            return rep
        return f"/* unsupported expr: {kind} */"

    def get_expr_type(self, expr: dict[str, Any] | None) -> str | None:
        if expr is None:
            return None
        t = expr.get("resolved_type")
        return t if isinstance(t, str) else None

    def cpp_type(self, east_type: str | None) -> str:
        if east_type is None:
            return "auto"
        if east_type == "None":
            return "void"
        if east_type in {
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
            "str",
        }:
            return east_type
        if east_type == "Path":
            return "Path"
        if east_type == "Exception":
            return "std::runtime_error"
        if east_type.startswith("list[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 1:
                if inner[0] == "uint8":
                    return "bytearray"
                return f"list<{self.cpp_type(inner[0])}>"
        if east_type.startswith("set[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[4:-1])
            if len(inner) == 1:
                return f"set<{self.cpp_type(inner[0])}>"
        if east_type.startswith("dict[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[5:-1])
            if len(inner) == 2:
                return f"dict<{self.cpp_type(inner[0])}, {self.cpp_type(inner[1])}>"
        if east_type.startswith("tuple[") and east_type.endswith("]"):
            inner = self.split_generic(east_type[6:-1])
            return "std::tuple<" + ", ".join(self.cpp_type(x) for x in inner) + ">"
        if east_type == "unknown":
            return "auto"
        if east_type.startswith("callable["):
            return "auto"
        if east_type == "module":
            return "auto"
        return east_type

    def split_generic(self, s: str) -> list[str]:
        if s == "":
            return []
        out: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(s):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(s[start:i].strip())
                start = i + 1
        out.append(s[start:].strip())
        return out


def load_east(input_path: Path) -> dict[str, Any]:
    if input_path.suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid EAST JSON payload")
        if payload.get("ok") is False:
            raise RuntimeError(f"EAST error: {payload.get('error')}")
        if payload.get("ok") is True and isinstance(payload.get("east"), dict):
            return payload["east"]
        if payload.get("kind") == "Module":
            return payload
        raise RuntimeError("Invalid EAST JSON structure")

    try:
        source_text = input_path.read_text(encoding="utf-8")
        east = convert_path(input_path)
    except (SyntaxError, EastBuildError) as exc:
        raise RuntimeError(f"EAST conversion failed: {exc}") from exc
    if isinstance(east, dict):
        has_stmt_leading_trivia = False
        body = east.get("body")
        if isinstance(body, list) and len(body) > 0 and isinstance(body[0], dict):
            trivia = body[0].get("leading_trivia")
            has_stmt_leading_trivia = isinstance(trivia, list) and len(trivia) > 0
        if not has_stmt_leading_trivia:
            east["module_leading_trivia"] = extract_module_leading_trivia(source_text)
    return east


def extract_module_leading_trivia(source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    blank_count = 0
    for raw in source.splitlines():
        s = raw.strip()
        if s == "":
            blank_count += 1
            continue
        if s.startswith("#"):
            if blank_count > 0:
                out.append({"kind": "blank", "count": blank_count})
                blank_count = 0
            text = s[1:]
            if text.startswith(" "):
                text = text[1:]
            out.append({"kind": "comment", "text": text})
            continue
        break
    if blank_count > 0:
        out.append({"kind": "blank", "count": blank_count})
    return out


def transpile_to_cpp(east_module: dict[str, Any], *, negative_index_mode: str = "const_only") -> str:
    return CppEmitter(east_module, negative_index_mode=negative_index_mode).transpile()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Transpile Python/EAST to C++ via EAST")
    ap.add_argument("input", help="Input .py or EAST .json")
    ap.add_argument("-o", "--output", help="Output .cpp path")
    ap.add_argument(
        "--negative-index-mode",
        choices=["always", "const_only", "off"],
        default="const_only",
        help="Policy for Python-style negative indexing on list/str subscripts",
    )
    args = ap.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east_module = load_east(input_path)
        cpp = transpile_to_cpp(east_module, negative_index_mode=args.negative_index_mode)
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

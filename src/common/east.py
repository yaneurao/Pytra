#!/usr/bin/env python3
"""Python source -> EAST converter.

This script converts Python AST into a language-neutral EAST JSON document.
It focuses on Phase 1 requirements in docs/spec-east.md:
 - syntax normalization (`if __name__ == "__main__"` extraction, symbol rename)
 - type resolution (annotation + inference)
 - readonly analysis for function args
 - explicit cast metadata for mixed numeric binops
 - error contract with kind/source_span/hint
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


BorrowKind = str  # "value" | "readonly_ref" | "mutable_ref" | "move"
INT_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
}
FLOAT_TYPES = {"float32", "float64"}


@dataclass
class EastBuildError(Exception):
    """EAST generation error with contract fields."""

    kind: str
    message: str
    source_span: dict[str, int | None]
    hint: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": self.message,
            "source_span": self.source_span,
            "hint": self.hint,
        }


def span_of(node: ast.AST | None) -> dict[str, int | None]:
    """Return stable source span dict for AST node or null-span for None."""
    if node is None:
        return {"lineno": None, "col": None, "end_lineno": None, "end_col": None}
    return {
        "lineno": getattr(node, "lineno", None),
        "col": getattr(node, "col_offset", None),
        "end_lineno": getattr(node, "end_lineno", None),
        "end_col": getattr(node, "end_col_offset", None),
    }


def is_main_guard(stmt: ast.stmt) -> bool:
    """Check whether stmt is `if __name__ == "__main__":`."""
    if not isinstance(stmt, ast.If):
        return False
    test = stmt.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    left = test.left
    right = test.comparators[0]
    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def annotation_to_type(ann: ast.expr | None) -> str | None:
    """Normalize Python annotation AST into EAST type string."""
    if ann is None:
        return None
    if isinstance(ann, ast.Name):
        if ann.id == "int":
            return "int64"
        if ann.id in INT_TYPES:
            return ann.id
        if ann.id in FLOAT_TYPES:
            return ann.id
        if ann.id == "float":
            return "float64"
        if ann.id in {"bytes", "bytearray"}:
            return "list[uint8]"
        if ann.id in {"bool", "str", "Path"}:
            return ann.id
        if ann.id in {"None", "NoneType"}:
            return "None"
        return ann.id
    if isinstance(ann, ast.Constant) and ann.value is None:
        return "None"
    if isinstance(ann, ast.Subscript):
        base = annotation_to_type(ann.value)
        if base is None:
            return None
        if isinstance(ann.slice, ast.Tuple):
            args = [annotation_to_type(x) or "?" for x in ann.slice.elts]
            return f"{base}[{','.join(args)}]"
        arg = annotation_to_type(ann.slice) or "?"
        return f"{base}[{arg}]"
    if isinstance(ann, ast.Attribute):
        if isinstance(ann.value, ast.Name) and ann.value.id == "pathlib" and ann.attr == "Path":
            return "Path"
        return ann.attr
    return None


class ArgUsageAnalyzer(ast.NodeVisitor):
    """Conservative readonly/mutable classifier for function args."""

    MUTATING_METHODS = {
        "append",
        "extend",
        "insert",
        "pop",
        "clear",
        "remove",
        "discard",
        "add",
        "update",
        "sort",
        "reverse",
        "write",
        "write_text",
        "mkdir",
    }
    PURE_BUILTINS = {"len", "print", "int", "float", "str", "bool", "range", "min", "max", "ord", "chr"}

    def __init__(self, arg_names: set[str]) -> None:
        """Initialize analyzer for one function scope."""
        self.arg_names = set(arg_names)
        self.mutable: set[str] = set()

    def _mark_if_arg(self, node: ast.expr) -> None:
        """Mark name as mutable if expression directly references an arg."""
        if isinstance(node, ast.Name) and node.id in self.arg_names:
            self.mutable.add(node.id)

    def visit_Assign(self, node: ast.Assign) -> Any:
        """Assignment to arg/arg-substructure means mutable usage."""
        for t in node.targets:
            self._mark_mutation_target(t)
        self.generic_visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        """Augmented assignment mutates arg targets."""
        self._mark_mutation_target(node.target)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        """Annotated assignment mutates arg targets too."""
        self._mark_mutation_target(node.target)
        if node.value is not None:
            self.generic_visit(node.value)

    def visit_Call(self, node: ast.Call) -> Any:
        """Method calls on args are mutable when method is in mutating set."""
        if isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id in self.arg_names and node.func.attr in self.MUTATING_METHODS:
                self.mutable.add(owner.id)
        elif isinstance(node.func, ast.Name):
            fn = node.func.id
            if fn not in self.PURE_BUILTINS:
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id in self.arg_names:
                        self.mutable.add(arg.id)
        self.generic_visit(node)

    def _mark_mutation_target(self, target: ast.expr) -> None:
        """Mark mutation when target writes arg itself/field/item."""
        if isinstance(target, ast.Name) and target.id in self.arg_names:
            self.mutable.add(target.id)
            return
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id in self.arg_names:
            self.mutable.add(target.value.id)
            return
        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id in self.arg_names:
            self.mutable.add(target.value.id)
            return


class EastBuilder:
    """Build EAST JSON from Python AST with type and normalization passes."""

    RESERVED = {"main", "py_main", "__pytra_main"}

    def __init__(self, source: str, filename: str) -> None:
        """Prepare parser state, type env stacks, and precompute tables."""
        self.source = source
        self.filename = filename
        self.module = ast.parse(source, filename=filename)
        self.type_env_stack: list[dict[str, str]] = []
        self.arg_usage_stack: list[dict[str, str]] = []
        self.renamed_symbols: dict[str, str] = {}
        self._scope_defined: set[str] = set()
        self.function_return_types: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_method_return_types: dict[str, dict[str, str]] = {}
        self.class_field_types: dict[str, dict[str, str]] = {}
        self.class_base: dict[str, str | None] = {}
        self.current_class_stack: list[str] = []

    def build(self) -> dict[str, Any]:
        """Build module-level EAST document."""
        body: list[dict[str, Any]] = []
        main_body: list[dict[str, Any]] = []
        self._precompute_module_renames(self.module)
        self.type_env_stack.append({})

        for stmt in self.module.body:
            if is_main_guard(stmt):
                for inner in stmt.body:
                    main_body.append(self._stmt(inner))
                continue
            body.append(self._stmt(stmt))

        self.type_env_stack.pop()
        return {
            "kind": "Module",
            "source_path": self.filename,
            "source_span": span_of(self.module),
            "body": body,
            "main_guard_body": main_body,
            "renamed_symbols": dict(self.renamed_symbols),
        }

    def _precompute_module_renames(self, module: ast.Module) -> None:
        """Collect rename/type/class metadata before node conversion."""
        counts: dict[str, int] = {}
        for stmt in module.body:
            if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
                counts[stmt.name] = counts.get(stmt.name, 0) + 1
            if isinstance(stmt, ast.FunctionDef):
                ret = annotation_to_type(stmt.returns) if stmt.returns is not None else "None"
                if ret is not None:
                    self.function_return_types[stmt.name] = ret
            if isinstance(stmt, ast.ClassDef):
                self.class_names.add(stmt.name)
                base_name: str | None = None
                if len(stmt.bases) >= 1 and isinstance(stmt.bases[0], ast.Name):
                    base_name = stmt.bases[0].id
                self.class_base[stmt.name] = base_name
                methods: dict[str, str] = {}
                fields: dict[str, str] = {}
                for n in stmt.body:
                    if isinstance(n, ast.FunctionDef):
                        r = annotation_to_type(n.returns) if n.returns is not None else "None"
                        if r is not None:
                            methods[n.name] = r
                        if n.name == "__init__":
                            arg_map: dict[str, str] = {}
                            for a in n.args.args:
                                t = annotation_to_type(a.annotation)
                                if t is not None:
                                    arg_map[a.arg] = t
                            for st in n.body:
                                if isinstance(st, ast.Assign):
                                    for tgt in st.targets:
                                        if (
                                            isinstance(tgt, ast.Attribute)
                                            and isinstance(tgt.value, ast.Name)
                                            and tgt.value.id == "self"
                                        ):
                                            if isinstance(st.value, ast.Name) and st.value.id in arg_map:
                                                fields[tgt.attr] = arg_map[st.value.id]
                                if isinstance(st, ast.AnnAssign):
                                    if (
                                        isinstance(st.target, ast.Attribute)
                                        and isinstance(st.target.value, ast.Name)
                                        and st.target.value.id == "self"
                                    ):
                                        ft = annotation_to_type(st.annotation)
                                        if ft is not None:
                                            fields[st.target.attr] = ft
                    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                        ft = annotation_to_type(n.annotation)
                        if ft is not None:
                            fields[n.target.id] = ft
                self.class_method_return_types[stmt.name] = methods
                self.class_field_types[stmt.name] = fields
        for name, count in counts.items():
            if count > 1 or name in self.RESERVED:
                self.renamed_symbols[name] = f"__pytra_{name}"

    def _stmt(self, stmt: ast.stmt) -> dict[str, Any]:
        """Convert one Python statement node into EAST statement node."""
        if isinstance(stmt, ast.FunctionDef):
            return self._function(stmt)
        if isinstance(stmt, ast.ClassDef):
            self.current_class_stack.append(stmt.name)
            out = {
                "kind": "ClassDef",
                "name": self._renamed(stmt.name),
                "original_name": stmt.name,
                "base": self.class_base.get(stmt.name),
                "field_types": self.class_field_types.get(stmt.name, {}),
                "source_span": span_of(stmt),
                "body": [self._stmt(s) for s in stmt.body],
            }
            self.current_class_stack.pop()
            return out
        if isinstance(stmt, ast.Return):
            return {
                "kind": "Return",
                "source_span": span_of(stmt),
                "value": self._expr(stmt.value) if stmt.value is not None else None,
            }
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                raise self._error("unsupported_syntax", "only single-target assignment is supported", stmt, "Split assignment into one target per statement.")
            target = stmt.targets[0]
            value = self._expr(stmt.value)
            declare = False
            decl_type: str | None = None
            if isinstance(target, ast.Name):
                declare = target.id not in self.type_env_stack[-1]
                decl_type = value["resolved_type"]
                self._bind_name_type(target.id, value["resolved_type"], stmt)
            elif isinstance(target, ast.Tuple):
                tuple_elem_types = self._tuple_element_types(value["resolved_type"])
                if tuple_elem_types is not None and len(tuple_elem_types) == len(target.elts):
                    for idx, elt in enumerate(target.elts):
                        if isinstance(elt, ast.Name):
                            self._bind_name_type(elt.id, tuple_elem_types[idx], stmt)
            return {
                "kind": "Assign",
                "source_span": span_of(stmt),
                "target": self._expr(target),
                "value": value,
                "declare": declare,
                "decl_type": decl_type,
            }
        if isinstance(stmt, ast.AugAssign):
            target_expr = self._expr(stmt.target)
            value_expr = self._expr(stmt.value)
            if isinstance(stmt.target, ast.Name):
                current = self._lookup_name_type(stmt.target.id)
                rhs_t = value_expr["resolved_type"]
                if current is not None and self._is_numeric_type(current) and self._is_numeric_type(rhs_t):
                    self._bind_name_type(stmt.target.id, self._promote_numeric_type(current, rhs_t), stmt)
            return {
                "kind": "AugAssign",
                "source_span": span_of(stmt),
                "target": target_expr,
                "op": type(stmt.op).__name__,
                "value": value_expr,
                "declare": False,
                "decl_type": None,
            }
        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Attribute):
                ann_ty = annotation_to_type(stmt.annotation)
                if ann_ty is None:
                    raise self._error("unsupported_syntax", "unsupported type annotation", stmt.annotation, "Use supported Python-style annotations.")
                value = self._expr_with_expected_type(stmt.value, ann_ty) if stmt.value is not None else None
                if value is not None and not self._types_compatible(ann_ty, value["resolved_type"]):
                    raise self._error(
                        "semantic_conflict",
                        f"annotated type '{ann_ty}' conflicts with value type '{value['resolved_type']}'",
                        stmt,
                        "Align annotation and assigned value type.",
                    )
                return {
                    "kind": "AnnAssign",
                    "source_span": span_of(stmt),
                    "target": self._expr(stmt.target),
                    "annotation": ann_ty,
                    "value": value,
                }
            if not isinstance(stmt.target, ast.Name):
                raise self._error("unsupported_syntax", "annotated assignment target must be Name/Attribute", stmt, "Use simple variable annotation.")
            ann_ty = annotation_to_type(stmt.annotation)
            if ann_ty is None:
                raise self._error("unsupported_syntax", "unsupported type annotation", stmt.annotation, "Use supported Python-style annotations.")
            value = self._expr_with_expected_type(stmt.value, ann_ty) if stmt.value is not None else None
            declare = stmt.target.id not in self.type_env_stack[-1] if len(self.type_env_stack) > 0 else True
            if value is not None and not self._types_compatible(ann_ty, value["resolved_type"]):
                raise self._error(
                    "semantic_conflict",
                    f"annotated type '{ann_ty}' conflicts with value type '{value['resolved_type']}'",
                    stmt,
                    "Align annotation and assigned value type.",
                )
            self._bind_name_type(stmt.target.id, ann_ty, stmt)
            return {
                "kind": "AnnAssign",
                "source_span": span_of(stmt),
                "target": self._expr(stmt.target),
                "annotation": ann_ty,
                "value": value,
                "declare": declare,
                "decl_type": ann_ty,
            }
        if isinstance(stmt, ast.Expr):
            return {"kind": "Expr", "source_span": span_of(stmt), "value": self._expr(stmt.value)}
        if isinstance(stmt, ast.If):
            return {
                "kind": "If",
                "source_span": span_of(stmt),
                "test": self._expr(stmt.test),
                "body": [self._stmt(s) for s in stmt.body],
                "orelse": [self._stmt(s) for s in stmt.orelse],
            }
        if isinstance(stmt, ast.For):
            rng = self._parse_range_iter(stmt.iter)
            if rng is not None:
                start_node, stop_node, step_node = rng
                range_mode = self._range_mode_from_step(step_node, stmt)
                if isinstance(stmt.target, ast.Name):
                    self._bind_name_type(stmt.target.id, "int64", stmt)
                return {
                    "kind": "ForRange",
                    "source_span": span_of(stmt),
                    "target": self._expr(stmt.target),
                    "target_type": "int64",
                    "start": self._expr(start_node),
                    "stop": self._expr(stop_node),
                    "step": self._expr(step_node),
                    "range_mode": range_mode,
                    "body": [self._stmt(s) for s in stmt.body],
                    "orelse": [self._stmt(s) for s in stmt.orelse],
                }
            if isinstance(stmt.target, ast.Name):
                it_type, _ = self._resolve_expr_type(stmt.iter)
                bind_t = self._iter_element_type(it_type)
                if bind_t is not None:
                    self._bind_name_type(stmt.target.id, bind_t, stmt)
            return {
                "kind": "For",
                "source_span": span_of(stmt),
                "target": self._expr(stmt.target),
                "target_type": self._lookup_name_type(stmt.target.id) if isinstance(stmt.target, ast.Name) else None,
                "iter": self._expr(stmt.iter),
                "body": [self._stmt(s) for s in stmt.body],
                "orelse": [self._stmt(s) for s in stmt.orelse],
            }
        if isinstance(stmt, ast.While):
            return {
                "kind": "While",
                "source_span": span_of(stmt),
                "test": self._expr(stmt.test),
                "body": [self._stmt(s) for s in stmt.body],
                "orelse": [self._stmt(s) for s in stmt.orelse],
            }
        if isinstance(stmt, ast.Try):
            return {
                "kind": "Try",
                "source_span": span_of(stmt),
                "body": [self._stmt(s) for s in stmt.body],
                "handlers": [self._except_handler(h) for h in stmt.handlers],
                "orelse": [self._stmt(s) for s in stmt.orelse],
                "finalbody": [self._stmt(s) for s in stmt.finalbody],
            }
        if isinstance(stmt, ast.Raise):
            return {
                "kind": "Raise",
                "source_span": span_of(stmt),
                "exc": self._expr(stmt.exc) if stmt.exc is not None else None,
            }
        if isinstance(stmt, ast.Import):
            for a in stmt.names:
                bind_name = a.asname or a.name.split(".")[0]
                self._bind_name_type(bind_name, "module", stmt)
            return {
                "kind": "Import",
                "source_span": span_of(stmt),
                "names": [{"name": a.name, "asname": a.asname} for a in stmt.names],
            }
        if isinstance(stmt, ast.ImportFrom):
            for a in stmt.names:
                bind_name = a.asname or a.name
                if stmt.module == "time" and a.name == "perf_counter":
                    self._bind_name_type(bind_name, "callable[float64]", stmt)
                elif stmt.module == "math":
                    self._bind_name_type(bind_name, "callable[float64]", stmt)
                else:
                    self._bind_name_type(bind_name, "unknown", stmt)
            return {
                "kind": "ImportFrom",
                "source_span": span_of(stmt),
                "module": stmt.module,
                "level": stmt.level,
                "names": [{"name": a.name, "asname": a.asname} for a in stmt.names],
            }
        if isinstance(stmt, ast.Pass):
            return {"kind": "Pass", "source_span": span_of(stmt)}
        if isinstance(stmt, ast.Break):
            return {"kind": "Break", "source_span": span_of(stmt)}
        if isinstance(stmt, ast.Continue):
            return {"kind": "Continue", "source_span": span_of(stmt)}
        raise self._error("unsupported_syntax", f"unsupported statement: {type(stmt).__name__}", stmt, "Rewrite to supported subset.")

    def _except_handler(self, h: ast.ExceptHandler) -> dict[str, Any]:
        """Convert `except` clause into EAST handler node."""
        return {
            "kind": "ExceptHandler",
            "source_span": span_of(h),
            "type": self._expr(h.type) if h.type is not None else None,
            "name": h.name,
            "body": [self._stmt(s) for s in h.body],
        }

    def _function(self, fn: ast.FunctionDef) -> dict[str, Any]:
        """Convert function definition with arg usage + scoped typing."""
        fn_name = self._renamed(fn.name)
        arg_types: dict[str, str] = {}
        in_class = len(self.current_class_stack) > 0
        cur_cls = self.current_class_stack[-1] if in_class else None
        for idx, arg in enumerate(fn.args.args):
            ann = annotation_to_type(arg.annotation)
            if ann is None:
                if in_class and idx == 0 and arg.arg == "self" and cur_cls is not None:
                    ann = cur_cls
                else:
                    raise self._error(
                        "inference_failure",
                        f"function argument '{arg.arg}' requires type annotation or inferable type",
                        arg,
                        "Add a type annotation to the argument.",
                    )
            arg_types[arg.arg] = ann
        ret_ty = annotation_to_type(fn.returns) if fn.returns is not None else "None"
        if ret_ty is None:
            raise self._error("unsupported_syntax", "unsupported return annotation", fn.returns, "Use supported return annotation.")

        analyzer = ArgUsageAnalyzer(set(arg_types.keys()))
        for st in fn.body:
            analyzer.visit(st)
        arg_usage = {name: ("mutable" if name in analyzer.mutable else "readonly") for name in arg_types}

        self.type_env_stack.append(dict(arg_types))
        self.arg_usage_stack.append(arg_usage)
        body = [self._stmt(s) for s in fn.body]
        self.arg_usage_stack.pop()
        self.type_env_stack.pop()
        return {
            "kind": "FunctionDef",
            "name": fn_name,
            "original_name": fn.name,
            "source_span": span_of(fn),
            "arg_types": arg_types,
            "return_type": ret_ty,
            "arg_usage": arg_usage,
            "renamed_symbols": {k: v for k, v in self.renamed_symbols.items() if k == fn.name},
            "body": body,
        }

    def _expr(self, expr: ast.expr) -> dict[str, Any]:
        """Convert expression and attach resolved type/cast/borrow metadata."""
        resolved_type, casts = self._resolve_expr_type(expr)
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "range":
            parsed = self._parse_range_iter(expr)
            assert parsed is not None  # _parse_range_iter handles range() contract checks
            start_node, stop_node, step_node = parsed
            return {
                "kind": "RangeExpr",
                "source_span": span_of(expr),
                "resolved_type": resolved_type,
                "borrow_kind": self._borrow_kind(expr),
                "casts": casts,
                "repr": ast.unparse(expr) if hasattr(ast, "unparse") else None,
                "start": self._expr_maybe(start_node),
                "stop": self._expr_maybe(stop_node),
                "step": self._expr_maybe(step_node),
                "range_mode": self._range_mode_from_step(step_node, expr),
            }
        out = {
            "kind": type(expr).__name__,
            "source_span": span_of(expr),
            "resolved_type": resolved_type,
            "borrow_kind": self._borrow_kind(expr),
            "casts": casts,
            "repr": ast.unparse(expr) if hasattr(ast, "unparse") else None,
        }
        out.update(self._expr_children(expr))
        return out

    def _expr_with_expected_type(self, expr: ast.expr, expected_type: str) -> dict[str, Any]:
        """Allow annotated empty container literals to reuse annotation type."""
        if self._is_annotated_empty_container(expr, expected_type):
            out = {
                "kind": type(expr).__name__,
                "source_span": span_of(expr),
                "resolved_type": expected_type,
                "borrow_kind": self._borrow_kind(expr),
                "casts": [],
                "repr": ast.unparse(expr) if hasattr(ast, "unparse") else None,
            }
            out.update(self._expr_children(expr))
            return out
        return self._expr(expr)

    def _expr_maybe(self, expr: ast.expr) -> dict[str, Any]:
        """Best-effort child serializer: keep structure even if strict typing fails."""
        try:
            return self._expr(expr)
        except EastBuildError:
            out: dict[str, Any] = {
                "kind": type(expr).__name__,
                "source_span": span_of(expr),
                "resolved_type": "unknown",
                "borrow_kind": "value",
                "casts": [],
                "repr": ast.unparse(expr) if hasattr(ast, "unparse") else None,
            }
            if isinstance(expr, ast.Name):
                out["id"] = expr.id
            if isinstance(expr, ast.Constant):
                out["value"] = expr.value
            return out

    def _expr_children(self, expr: ast.expr) -> dict[str, Any]:
        """Attach structured child nodes so literals/args keep explicit types in EAST."""
        if isinstance(expr, ast.Name):
            return {"id": expr.id}
        if isinstance(expr, ast.Constant):
            return {"value": expr.value}
        if isinstance(expr, ast.Attribute):
            return {"value": self._expr_maybe(expr.value), "attr": expr.attr}
        if isinstance(expr, ast.Call):
            payload = {
                "func": self._expr_maybe(expr.func),
                "args": [self._expr_maybe(a) for a in expr.args],
                "keywords": [
                    {"arg": kw.arg, "value": self._expr_maybe(kw.value)}
                    for kw in expr.keywords
                ],
            }
            lower = self._lower_call_info(expr)
            if lower is not None:
                payload.update(lower)
            return payload
        if isinstance(expr, ast.BinOp):
            return {
                "left": self._expr_maybe(expr.left),
                "op": type(expr.op).__name__,
                "right": self._expr_maybe(expr.right),
            }
        if isinstance(expr, ast.UnaryOp):
            return {"op": type(expr.op).__name__, "operand": self._expr_maybe(expr.operand)}
        if isinstance(expr, ast.BoolOp):
            return {"op": type(expr.op).__name__, "values": [self._expr_maybe(v) for v in expr.values]}
        if isinstance(expr, ast.Compare):
            payload = {
                "left": self._expr_maybe(expr.left),
                "ops": [type(o).__name__ for o in expr.ops],
                "comparators": [self._expr_maybe(c) for c in expr.comparators],
            }
            if len(expr.ops) == 1 and len(expr.comparators) == 1:
                if isinstance(expr.ops[0], ast.In):
                    payload.update(
                        {
                            "lowered_kind": "Contains",
                            "container": self._expr_maybe(expr.comparators[0]),
                            "key": self._expr_maybe(expr.left),
                            "negated": False,
                        }
                    )
                if isinstance(expr.ops[0], ast.NotIn):
                    payload.update(
                        {
                            "lowered_kind": "Contains",
                            "container": self._expr_maybe(expr.comparators[0]),
                            "key": self._expr_maybe(expr.left),
                            "negated": True,
                        }
                    )
            return payload
        if isinstance(expr, ast.IfExp):
            return {
                "test": self._expr_maybe(expr.test),
                "body": self._expr_maybe(expr.body),
                "orelse": self._expr_maybe(expr.orelse),
            }
        if isinstance(expr, ast.List):
            return {"elements": [self._expr_maybe(e) for e in expr.elts]}
        if isinstance(expr, ast.Tuple):
            return {"elements": [self._expr_maybe(e) for e in expr.elts]}
        if isinstance(expr, ast.Set):
            return {"elements": [self._expr_maybe(e) for e in expr.elts]}
        if isinstance(expr, ast.Dict):
            entries = []
            for k, v in zip(expr.keys, expr.values):
                entries.append(
                    {
                        "key": self._expr_maybe(k) if k is not None else None,
                        "value": self._expr_maybe(v),
                    }
                )
            return {"entries": entries}
        if isinstance(expr, ast.Subscript):
            payload: dict[str, Any] = {"value": self._expr_maybe(expr.value)}
            if isinstance(expr.slice, ast.Slice):
                payload["slice"] = {
                    "kind": "Slice",
                    "lower": self._expr_maybe(expr.slice.lower) if expr.slice.lower is not None else None,
                    "upper": self._expr_maybe(expr.slice.upper) if expr.slice.upper is not None else None,
                    "step": self._expr_maybe(expr.slice.step) if expr.slice.step is not None else None,
                }
                payload["lowered_kind"] = "SliceExpr"
                payload["lower"] = payload["slice"]["lower"]
                payload["upper"] = payload["slice"]["upper"]
                payload["step"] = payload["slice"]["step"]
            else:
                payload["slice"] = self._expr_maybe(expr.slice)
            return payload
        if isinstance(expr, ast.JoinedStr):
            values: list[dict[str, Any]] = []
            concat_parts: list[dict[str, Any]] = []
            for part in expr.values:
                if isinstance(part, ast.Constant):
                    node = {"kind": "Constant", "value": part.value}
                    values.append(node)
                    concat_parts.append({"kind": "literal", "value": part.value})
                elif isinstance(part, ast.FormattedValue):
                    inner = self._expr_maybe(part.value)
                    values.append({"kind": "FormattedValue", "value": inner})
                    concat_parts.append({"kind": "expr", "value": inner})
            return {"values": values, "lowered_kind": "Concat", "concat_parts": concat_parts}
        if isinstance(expr, ast.ListComp):
            gens = []
            for g in expr.generators:
                gens.append(
                    {
                        "target": self._expr_maybe(g.target),  # type: ignore[arg-type]
                        "iter": self._expr_maybe(g.iter),
                        "ifs": [self._expr_maybe(c) for c in g.ifs],
                        "is_async": bool(g.is_async),
                    }
                )
            payload = {"elt": self._expr_maybe(expr.elt), "generators": gens}
            if len(expr.generators) == 1:
                payload["lowered_kind"] = "ListCompSimple"
            return payload
        return {}

    def _lower_call_info(self, expr: ast.Call) -> dict[str, Any] | None:
        """Annotate call nodes with language-neutral lowered builtin mapping."""
        if isinstance(expr.func, ast.Name):
            fn = expr.func.id
            runtime = {
                "print": "py_print",
                "len": "py_len",
                "str": "py_to_string",
                "int": "static_cast",
                "float": "static_cast",
                "bool": "static_cast",
                "bytes": "list[uint8]",
                "bytearray": "list[uint8]",
                "write_rgb_png": "write_rgb_png",
                "save_gif": "save_gif",
                "grayscale_palette": "grayscale_palette",
                "min": "py_min",
                "max": "py_max",
                "perf_counter": "perf_counter",
                "Path": "Path",
                "Exception": "std::runtime_error",
                "RuntimeError": "std::runtime_error",
            }.get(fn)
            if runtime is not None:
                return {"lowered_kind": "BuiltinCall", "builtin_name": fn, "runtime_call": runtime}
            return None
        if isinstance(expr.func, ast.Attribute):
            owner = expr.func.value
            attr = expr.func.attr
            if isinstance(owner, ast.Name) and owner.id == "math":
                runtime = {
                    "sqrt": "pycs::cpp_module::math::sqrt",
                    "sin": "pycs::cpp_module::math::sin",
                    "cos": "pycs::cpp_module::math::cos",
                    "tan": "pycs::cpp_module::math::tan",
                    "exp": "pycs::cpp_module::math::exp",
                    "log": "pycs::cpp_module::math::log",
                    "log10": "pycs::cpp_module::math::log10",
                    "fabs": "pycs::cpp_module::math::fabs",
                    "floor": "pycs::cpp_module::math::floor",
                    "ceil": "pycs::cpp_module::math::ceil",
                    "pow": "pycs::cpp_module::math::pow",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"math.{attr}", "runtime_call": runtime}
            if isinstance(owner, ast.Name) and owner.id == "png_helper" and attr == "write_rgb_png":
                return {"lowered_kind": "BuiltinCall", "builtin_name": "png_helper.write_rgb_png", "runtime_call": "write_rgb_png"}
            if isinstance(owner, ast.Name) and owner.id == "gif_helper":
                runtime = {
                    "save_gif": "save_gif",
                    "grayscale_palette": "grayscale_palette",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"gif_helper.{attr}", "runtime_call": runtime}
            try:
                owner_t, _ = self._resolve_expr_type(owner)
            except EastBuildError:
                owner_t = "unknown"
            if owner_t == "Path":
                runtime = {
                    "mkdir": "std::filesystem::create_directories",
                    "exists": "std::filesystem::exists",
                    "write_text": "py_write_text",
                    "read_text": "py_read_text",
                    "resolve": "identity",
                    "parent": "path_parent",
                    "name": "path_name",
                    "stem": "path_stem",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"Path.{attr}", "runtime_call": runtime}
            if owner_t == "str":
                runtime = {
                    "isdigit": "py_isdigit",
                    "isalpha": "py_isalpha",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"str.{attr}", "runtime_call": runtime}
            if owner_t.startswith("list["):
                runtime = {
                    "append": "list.append",
                    "extend": "list.extend",
                    "pop": "list.pop",
                    "clear": "list.clear",
                    "reverse": "list.reverse",
                    "sort": "list.sort",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"list.{attr}", "runtime_call": runtime}
            if owner_t.startswith("set["):
                runtime = {
                    "add": "set.add",
                    "discard": "set.discard",
                    "remove": "set.remove",
                    "clear": "set.clear",
                }.get(attr)
                if runtime is not None:
                    return {"lowered_kind": "BuiltinCall", "builtin_name": f"set.{attr}", "runtime_call": runtime}
        return None

    def _resolve_expr_type(self, expr: ast.expr) -> tuple[str, list[dict[str, Any]]]:
        """Infer expression type and required numeric cast annotations."""
        if isinstance(expr, ast.Name):
            if expr.id in {"True", "False"}:
                return "bool", []
            if expr.id == "None":
                return "None", []
            if expr.id in {"Exception", "RuntimeError"}:
                return "Exception", []
            t = self._lookup_name_type(expr.id)
            if t is None:
                raise self._error(
                    "inference_failure",
                    f"type of name '{expr.id}' is unknown",
                    expr,
                    "Add an annotation or assign a concrete typed value before use.",
                )
            return t, []
        if isinstance(expr, ast.Constant):
            if isinstance(expr.value, bool):
                return "bool", []
            if isinstance(expr.value, int):
                return "int64", []
            if isinstance(expr.value, float):
                return "float64", []
            if isinstance(expr.value, str):
                return "str", []
            if expr.value is None:
                return "None", []
            raise self._error("unsupported_syntax", f"unsupported constant type: {type(expr.value).__name__}", expr, "Use supported literal.")
        if isinstance(expr, ast.List):
            if len(expr.elts) == 0:
                raise self._error("inference_failure", "empty list type is ambiguous", expr, "Annotate variable type, e.g. x: list[int] = [].")
            elem_types = [self._resolve_expr_type(e)[0] for e in expr.elts]
            t = self._unify_types(elem_types, expr)
            return f"list[{t}]", []
        if isinstance(expr, ast.Set):
            if len(expr.elts) == 0:
                raise self._error("inference_failure", "empty set type is ambiguous", expr, "Annotate variable type, e.g. x: set[str] = set().")
            elem_types = [self._resolve_expr_type(e)[0] for e in expr.elts]
            t = self._unify_types(elem_types, expr)
            return f"set[{t}]", []
        if isinstance(expr, ast.Tuple):
            item_types = [self._resolve_expr_type(e)[0] for e in expr.elts]
            return f"tuple[{','.join(item_types)}]", []
        if isinstance(expr, ast.Dict):
            if len(expr.keys) == 0:
                raise self._error("inference_failure", "empty dict type is ambiguous", expr, "Annotate variable type, e.g. x: dict[str,int] = {}.")
            key_types = [self._resolve_expr_type(k)[0] for k in expr.keys if k is not None]
            val_types = [self._resolve_expr_type(v)[0] for v in expr.values]
            kt = self._unify_types(key_types, expr)
            vt = self._unify_types(val_types, expr)
            return f"dict[{kt},{vt}]", []
        if isinstance(expr, ast.BinOp):
            lt, _ = self._resolve_expr_type(expr.left)
            rt, _ = self._resolve_expr_type(expr.right)
            casts: list[dict[str, Any]] = []
            if isinstance(expr.op, ast.Div):
                if lt == "Path":
                    return "Path", []
                if self._is_numeric_type(lt) and self._is_numeric_type(rt):
                    out_t = self._promote_numeric_type(lt, rt, for_division=True)
                    if lt != out_t:
                        casts.append({"on": "left", "from": lt, "to": out_t, "reason": "numeric_promotion"})
                    if rt != out_t:
                        casts.append({"on": "right", "from": rt, "to": out_t, "reason": "numeric_promotion"})
                    return out_t, casts
            if isinstance(expr.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
                if lt == "str" and rt == "str" and isinstance(expr.op, ast.Add):
                    return "str", []
                if isinstance(expr.op, ast.Add):
                    if (lt == "str" and rt == "unknown") or (rt == "str" and lt == "unknown"):
                        return "str", []
                if isinstance(expr.op, ast.Mult):
                    if lt == "str" and self._is_int_type(rt):
                        return "str", []
                    if rt == "str" and self._is_int_type(lt):
                        return "str", []
                    if lt.startswith("list[") and lt.endswith("]") and self._is_int_type(rt):
                        return lt, []
                    if rt.startswith("list[") and rt.endswith("]") and self._is_int_type(lt):
                        return rt, []
                if self._is_numeric_type(lt) and self._is_numeric_type(rt):
                    if lt != rt:
                        out_t = self._promote_numeric_type(lt, rt)
                        if self._is_int_type(lt):
                            casts.append({"on": "left", "from": lt, "to": out_t, "reason": "numeric_promotion"})
                        if lt in FLOAT_TYPES and lt != out_t:
                            casts.append({"on": "left", "from": lt, "to": out_t, "reason": "numeric_promotion"})
                        if self._is_int_type(rt):
                            casts.append({"on": "right", "from": rt, "to": out_t, "reason": "numeric_promotion"})
                        if rt in FLOAT_TYPES and rt != out_t:
                            casts.append({"on": "right", "from": rt, "to": out_t, "reason": "numeric_promotion"})
                        return out_t, casts
                    return lt, []
            if isinstance(expr.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
                if self._is_int_type(lt) and self._is_int_type(rt):
                    if lt == rt:
                        return lt, []
                    has_signed = lt.startswith("int") or rt.startswith("int")
                    return ("int64" if has_signed else "uint64"), []
            raise self._error("inference_failure", f"cannot infer binop type: {lt} op {rt}", expr, "Add explicit cast or simplify expression.")
        if isinstance(expr, ast.UnaryOp):
            t, _ = self._resolve_expr_type(expr.operand)
            if isinstance(expr.op, ast.Not):
                return "bool", []
            if isinstance(expr.op, ast.USub) and self._is_numeric_type(t):
                return t, []
            raise self._error("inference_failure", f"cannot infer unary op type for {t}", expr, "Use explicit cast.")
        if isinstance(expr, ast.BoolOp):
            return "bool", []
        if isinstance(expr, ast.Compare):
            return "bool", []
        if isinstance(expr, ast.IfExp):
            bt, _ = self._resolve_expr_type(expr.body)
            ot, _ = self._resolve_expr_type(expr.orelse)
            if bt == ot:
                return bt, []
            if self._is_numeric_type(bt) and self._is_numeric_type(ot):
                out_t = self._promote_numeric_type(bt, ot)
                casts: list[dict[str, Any]] = []
                if bt != out_t:
                    casts.append({"on": "body", "from": bt, "to": out_t, "reason": "ifexp_numeric_promotion"})
                if ot != out_t:
                    casts.append({"on": "orelse", "from": ot, "to": out_t, "reason": "ifexp_numeric_promotion"})
                return out_t, casts
            raise self._error("inference_failure", f"if-expression branch types mismatch: {bt} vs {ot}", expr, "Align both branches to same type.")
        if isinstance(expr, ast.Attribute):
            bt, _ = self._resolve_expr_type(expr.value)
            if isinstance(expr.value, ast.Name) and expr.value.id == "self" and bt in self.class_names:
                fty = self._lookup_field_type(bt, expr.attr)
                if fty is not None:
                    return fty, []
            if bt == "Path":
                if expr.attr == "parent":
                    return "Path", []
                if expr.attr in {"name", "stem"}:
                    return "str", []
            if isinstance(expr.value, ast.Name) and expr.value.id == "math" and expr.attr in {
                "pi",
                "e",
            }:
                return "float64", []
            # user-class/member unknown type is kept as dynamic marker
            return "unknown", []
        if isinstance(expr, ast.Subscript):
            bt, _ = self._resolve_expr_type(expr.value)
            if isinstance(expr.slice, ast.Slice):
                if bt.startswith("list[") and bt.endswith("]"):
                    return bt, []
                if bt == "str":
                    return "str", []
                return "unknown", []
            if bt.startswith("list[") and bt.endswith("]"):
                return bt[5:-1], []
            if bt.startswith("dict[") and bt.endswith("]"):
                inside = bt[5:-1]
                parts = inside.split(",", 1)
                return parts[1] if len(parts) == 2 else "unknown", []
            if bt.startswith("tuple[") and bt.endswith("]"):
                return "unknown", []
            if bt == "str":
                return "str", []
            return "unknown", []
        if isinstance(expr, ast.Call):
            return self._resolve_call_type(expr)
        if isinstance(expr, ast.ListComp):
            if len(expr.generators) != 1:
                raise self._error("unsupported_syntax", "only single-generator list comprehension is supported", expr, "Use one generator in list comprehension.")
            gen = expr.generators[0]
            if not isinstance(gen.target, ast.Name):
                raise self._error("unsupported_syntax", "list comprehension target must be Name", gen.target, "Use simple name as comprehension target.")
            iter_t, _ = self._resolve_expr_type(gen.iter)
            target_t = self._iter_element_type(iter_t)
            if target_t is None:
                raise self._error("inference_failure", f"cannot infer comprehension target type from '{iter_t}'", gen.iter, "Add explicit annotation to iterable.")
            self.type_env_stack.append(dict(self.type_env_stack[-1] if self.type_env_stack else {}))
            self.type_env_stack[-1][gen.target.id] = target_t
            for cond in gen.ifs:
                self._resolve_expr_type(cond)
            et, _ = self._resolve_expr_type(expr.elt)
            self.type_env_stack.pop()
            return f"list[{et}]", []
        if isinstance(expr, ast.JoinedStr):
            return "str", []
        raise self._error("unsupported_syntax", f"unsupported expression: {type(expr).__name__}", expr, "Rewrite expression to supported subset.")

    def _resolve_call_type(self, expr: ast.Call) -> tuple[str, list[dict[str, Any]]]:
        """Infer return type of call expressions from known symbols/types."""
        if isinstance(expr.func, ast.Name):
            fn = expr.func.id
            if fn == "perf_counter":
                return "float64", []
            if fn == "int":
                return "int64", []
            if fn == "float":
                return "float64", []
            if fn == "bytearray":
                return "list[uint8]", []
            if fn == "bytes":
                return "list[uint8]", []
            if fn in {"bool", "str"}:
                return fn, []
            if fn == "len":
                return "int64", []
            if fn == "range":
                return "list[int64]", []
            if fn == "grayscale_palette":
                return "list[uint8]", []
            if fn == "Path":
                return "Path", []
            if fn in {"min", "max"}:
                if len(expr.args) == 0:
                    raise self._error("inference_failure", f"{fn} requires at least one argument", expr, f"Pass at least one argument to {fn}().")
                ts = [self._resolve_expr_type(a)[0] for a in expr.args]
                return self._unify_types(ts, expr), []
            if fn == "round":
                return "float64", []
            if fn in {"print", "write_rgb_png", "save_gif"}:
                return "None", []
            if fn in {"Exception", "RuntimeError"}:
                return "Exception", []
            if fn in self.class_names:
                return fn, []
            known_ret = self.function_return_types.get(fn)
            if known_ret is not None:
                return known_ret, []
            raise self._error("inference_failure", f"cannot infer return type of call '{fn}(...)'", expr, "Add return annotation and EAST resolver support.")
        if isinstance(expr.func, ast.Attribute):
            owner_t, _ = self._resolve_expr_type(expr.func.value)
            m = expr.func.attr
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "pathlib" and m == "Path":
                return "Path", []
            if owner_t == "Path":
                if m in {"resolve", "parent"}:
                    return "Path", []
                if m in {"name", "stem", "read_text"}:
                    return "str", []
                if m == "exists":
                    return "bool", []
                if m in {"write_text", "mkdir"}:
                    return "None", []
            if isinstance(expr.func.value, ast.Name) and expr.func.value.id == "math":
                if m in {"sqrt", "sin", "cos", "tan", "exp", "log", "log10", "fabs", "floor", "ceil", "pow"}:
                    return "float64", []
            if isinstance(expr.func.value, ast.Name):
                owner_name = expr.func.value.id
                owner_t = self._lookup_name_type(owner_name)
                if owner_t in self.class_names:
                    r = self._lookup_method_return_type(owner_t, m)
                    if r is not None:
                        return r, []
            # container methods
            if m in {"append", "extend", "insert", "clear", "sort", "reverse", "update", "add"}:
                return "None", []
            if m == "pop":
                return "unknown", []
            if m in {"isdigit", "isalpha", "exists"}:
                return "bool", []
            return "unknown", []
        raise self._error("inference_failure", "cannot infer call expression type", expr, "Add annotation or extend EAST resolver.")

    def _borrow_kind(self, expr: ast.expr) -> BorrowKind:
        """Map expression usage to value/readonly_ref/mutable_ref marker."""
        if isinstance(expr, ast.Name) and len(self.arg_usage_stack) > 0:
            usage = self.arg_usage_stack[-1].get(expr.id)
            if usage == "readonly":
                return "readonly_ref"
            if usage == "mutable":
                return "mutable_ref"
        return "value"

    def _lookup_name_type(self, name: str) -> str | None:
        """Lookup name type from innermost to outer scope."""
        for env in reversed(self.type_env_stack):
            if name in env:
                return env[name]
        return None

    def _bind_name_type(self, name: str, new_type: str, node: ast.AST) -> None:
        """Bind inferred type to current scope with conflict detection."""
        if len(self.type_env_stack) == 0:
            return
        env = self.type_env_stack[-1]
        prev = env.get(name)
        if prev is not None and not self._types_compatible(prev, new_type):
            raise self._error(
                "semantic_conflict",
                f"type conflict on '{name}': '{prev}' vs '{new_type}'",
                node,
                "Use explicit cast or split variable into different names.",
            )
        env[name] = new_type

    def _types_compatible(self, t1: str, t2: str) -> bool:
        """Return whether two types can coexist for same symbol."""
        if t1 == t2:
            return True
        if "unknown" in {t1, t2}:
            return True
        return self._is_numeric_type(t1) and self._is_numeric_type(t2)

    def _unify_types(self, types: list[str], node: ast.AST) -> str:
        """Unify multiple candidate types into one deterministic type."""
        uniq = sorted(set(types))
        if len(uniq) == 1:
            return uniq[0]
        if all(self._is_int_type(t) for t in uniq):
            has_signed = any(t.startswith("int") for t in uniq)
            return "int64" if has_signed else "uint64"
        if all(self._is_numeric_type(t) for t in uniq):
            out = uniq[0]
            for t in uniq[1:]:
                out = self._promote_numeric_type(out, t)
            return out
        raise self._error("inference_failure", f"ambiguous types: {uniq}", node, "Add explicit annotation/cast to make the type unique.")

    def _iter_element_type(self, iterable_type: str) -> str | None:
        """Extract element type from iterable-like EAST type."""
        if iterable_type.startswith("list[") and iterable_type.endswith("]"):
            return iterable_type[5:-1]
        if iterable_type.startswith("set[") and iterable_type.endswith("]"):
            return iterable_type[4:-1]
        if iterable_type.startswith("tuple[") and iterable_type.endswith("]"):
            inside = iterable_type[6:-1]
            if inside == "":
                return None
            first = inside.split(",", 1)[0]
            return first
        if iterable_type == "str":
            return "str"
        if iterable_type == "unknown":
            return "unknown"
        return None

    def _is_int_type(self, t: str) -> bool:
        """Check integer scalar type."""
        return t in INT_TYPES

    def _is_numeric_type(self, t: str) -> bool:
        """Check numeric scalar type (int/float families)."""
        return self._is_int_type(t) or t in FLOAT_TYPES

    def _promote_numeric_type(self, t1: str, t2: str, *, for_division: bool = False) -> str:
        """Apply EAST numeric promotion rules."""
        if for_division:
            return "float64"
        if t1 == t2:
            return t1
        if "float64" in {t1, t2}:
            return "float64"
        if "float32" in {t1, t2}:
            return "float32"
        if self._is_int_type(t1) and self._is_int_type(t2):
            has_signed = t1.startswith("int") or t2.startswith("int")
            return "int64" if has_signed else "uint64"
        return "float64"

    def _is_annotated_empty_container(self, expr: ast.expr, expected_type: str) -> bool:
        """Allow empty literal only when annotation gives concrete container type."""
        if isinstance(expr, ast.List):
            return len(expr.elts) == 0 and expected_type.startswith("list[") and expected_type.endswith("]")
        if isinstance(expr, ast.Set):
            return len(expr.elts) == 0 and expected_type.startswith("set[") and expected_type.endswith("]")
        if isinstance(expr, ast.Dict):
            return len(expr.keys) == 0 and expected_type.startswith("dict[") and expected_type.endswith("]")
        return False

    def _tuple_element_types(self, tuple_type: str) -> list[str] | None:
        """Parse `tuple[...]` type string into per-element type list."""
        if not (tuple_type.startswith("tuple[") and tuple_type.endswith("]")):
            return None
        inside = tuple_type[6:-1]
        if inside == "":
            return []
        parts: list[str] = []
        depth = 0
        start = 0
        for i, ch in enumerate(inside):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(inside[start:i].strip())
                start = i + 1
        parts.append(inside[start:].strip())
        return [p for p in parts if p]

    def _lookup_method_return_type(self, class_name: str, method: str) -> str | None:
        """Resolve method return type following class inheritance chain."""
        cur: str | None = class_name
        while cur is not None:
            methods = self.class_method_return_types.get(cur, {})
            if method in methods:
                return methods[method]
            cur = self.class_base.get(cur)
        return None

    def _lookup_field_type(self, class_name: str, field: str) -> str | None:
        """Resolve field type following class inheritance chain."""
        cur: str | None = class_name
        while cur is not None:
            fields = self.class_field_types.get(cur, {})
            if field in fields:
                return fields[field]
            cur = self.class_base.get(cur)
        return None

    def _parse_range_iter(self, expr: ast.expr) -> tuple[ast.expr, ast.expr, ast.expr] | None:
        """Parse `range(...)` call into normalized `(start, stop, step)`."""
        if not (isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "range"):
            return None
        if expr.keywords:
            raise self._error("unsupported_syntax", "range() with keyword args is not supported", expr, "Use positional range arguments.")
        argc = len(expr.args)
        if argc == 1:
            return ast.Constant(value=0), expr.args[0], ast.Constant(value=1)
        if argc == 2:
            return expr.args[0], expr.args[1], ast.Constant(value=1)
        if argc == 3:
            return expr.args[0], expr.args[1], expr.args[2]
        raise self._error("unsupported_syntax", "range() accepts 1..3 positional args", expr, "Use range(stop), range(start, stop), or range(start, stop, step).")

    def _range_mode_from_step(self, step_node: ast.expr, node_for_error: ast.AST) -> str:
        """Return range mode: 'ascending' | 'descending' | 'dynamic'."""
        if isinstance(step_node, ast.Constant) and isinstance(step_node.value, int):
            if step_node.value == 0:
                raise self._error("semantic_conflict", "range() step must not be zero", node_for_error, "Use non-zero step in range().")
            return "ascending" if step_node.value > 0 else "descending"
        if isinstance(step_node, ast.UnaryOp) and isinstance(step_node.op, ast.USub):
            if isinstance(step_node.operand, ast.Constant) and isinstance(step_node.operand.value, int):
                val = -step_node.operand.value
                if val == 0:
                    raise self._error("semantic_conflict", "range() step must not be zero", node_for_error, "Use non-zero step in range().")
                return "ascending" if val > 0 else "descending"
        return "dynamic"

    def _renamed(self, name: str) -> str:
        """Return renamed symbol when collision/reserved-name rewrite exists."""
        return self.renamed_symbols.get(name, name)

    def _error(self, kind: str, message: str, node: ast.AST | None, hint: str) -> EastBuildError:
        """Construct EAST error payload object with normalized source span."""
        return EastBuildError(kind=kind, message=message, source_span=span_of(node), hint=hint)


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """Convert Python source string to EAST document."""
    return EastBuilder(source=source, filename=filename).build()


def _sh_span(line: int, col: int, end_col: int) -> dict[str, int]:
    return {"lineno": line, "col": col, "end_lineno": line, "end_col": end_col}


def _sh_ann_to_type(ann: str) -> str:
    mapping = {
        "int": "int64",
        "float": "float64",
        "bool": "bool",
        "str": "str",
        "None": "None",
        "bytes": "list[uint8]",
        "bytearray": "list[uint8]",
    }
    txt = ann.strip()
    if txt in mapping:
        return mapping[txt]
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$", txt)
    if m is None:
        return txt
    head = m.group(1)
    inner = m.group(2).strip()
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(inner):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:i].strip())
            start = i + 1
    tail = inner[start:].strip()
    if tail != "":
        parts.append(tail)
    norm = [_sh_ann_to_type(p) for p in parts]
    return f"{head}[{', '.join(norm)}]"


def _sh_split_args_with_offsets(arg_text: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    depth = 0
    start = 0
    i = 0
    while i < len(arg_text):
        ch = arg_text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            part = arg_text[start:i]
            out.append((part.strip(), start + (len(part) - len(part.lstrip()))))
            start = i + 1
        i += 1
    tail = arg_text[start:]
    if tail.strip() != "":
        out.append((tail.strip(), start + (len(tail) - len(tail.lstrip()))))
    return out


class _ShExprParser:
    def __init__(
        self,
        text: str,
        *,
        line_no: int,
        col_base: int,
        name_types: dict[str, str],
        fn_return_types: dict[str, str],
        class_method_return_types: dict[str, dict[str, str]] | None = None,
        class_base: dict[str, str | None] | None = None,
    ) -> None:
        self.src = text
        self.line_no = line_no
        self.col_base = col_base
        self.name_types = name_types
        self.fn_return_types = fn_return_types
        self.class_method_return_types = class_method_return_types or {}
        self.class_base = class_base or {}
        self.tokens: list[dict[str, Any]] = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            if ch.isdigit():
                j = i + 1
                while j < len(text) and text[j].isdigit():
                    j += 1
                if j < len(text) and text[j] == ".":
                    k = j + 1
                    while k < len(text) and text[k].isdigit():
                        k += 1
                    if k > j + 1:
                        out.append({"k": "FLOAT", "v": text[i:k], "s": i, "e": k})
                        i = k
                        continue
                out.append({"k": "INT", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if ch.isalpha() or ch == "_":
                j = i + 1
                while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                out.append({"k": "NAME", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if ch in {"'", '"'}:
                q = ch
                j = i + 1
                while j < len(text):
                    if text[j] == "\\":
                        j += 2
                        continue
                    if text[j] == q:
                        j += 1
                        break
                    j += 1
                if j > len(text) or text[j - 1] != q:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="unterminated string literal in self_hosted parser",
                        source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + len(text)),
                        hint="Close string literal with matching quote.",
                    )
                out.append({"k": "STR", "v": text[i:j], "s": i, "e": j})
                i = j
                continue
            if i + 1 < len(text) and text[i : i + 2] in {"<=", ">=", "==", "!="}:
                out.append({"k": text[i : i + 2], "v": text[i : i + 2], "s": i, "e": i + 2})
                i += 2
                continue
            if ch in {"<", ">"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                i += 1
                continue
            if ch in {"+", "-", "*", "/", "%", "(", ")", ",", ".", "[", "]"}:
                out.append({"k": ch, "v": ch, "s": i, "e": i + 1})
                i += 1
                continue
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"unsupported token '{ch}' in self_hosted parser",
                source_span=_sh_span(self.line_no, self.col_base + i, self.col_base + i + 1),
                hint="Extend tokenizer for this syntax or use parser_backend=python_ast.",
            )
        out.append({"k": "EOF", "v": "", "s": len(text), "e": len(text)})
        return out

    def _cur(self) -> dict[str, Any]:
        return self.tokens[self.pos]

    def _eat(self, kind: str | None = None) -> dict[str, Any]:
        tok = self._cur()
        if kind is not None and tok["k"] != kind:
            raise EastBuildError(
                kind="unsupported_syntax",
                message=f"expected token {kind}, got {tok['k']}",
                source_span=_sh_span(self.line_no, self.col_base + tok["s"], self.col_base + tok["e"]),
                hint="Fix expression syntax for self_hosted parser.",
            )
        self.pos += 1
        return tok

    def _node_span(self, s: int, e: int) -> dict[str, int]:
        return _sh_span(self.line_no, self.col_base + s, self.col_base + e)

    def _src_slice(self, s: int, e: int) -> str:
        return self.src[s:e].strip()

    def parse(self) -> dict[str, Any]:
        node = self._parse_not()
        self._eat("EOF")
        return node

    def _parse_not(self) -> dict[str, Any]:
        tok = self._cur()
        if tok["k"] == "NAME" and tok["v"] == "not":
            self._eat("NAME")
            operand = self._parse_not()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            return {
                "kind": "UnaryOp",
                "source_span": self._node_span(s, e),
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(s, e),
                "op": "Not",
                "operand": operand,
            }
        return self._parse_compare()

    def _parse_compare(self) -> dict[str, Any]:
        node = self._parse_addsub()
        cmp_map = {"<": "Lt", "<=": "LtE", ">": "Gt", ">=": "GtE", "==": "Eq", "!=": "NotEq"}
        ops: list[str] = []
        comparators: list[dict[str, Any]] = []
        while self._cur()["k"] in cmp_map:
            tok = self._eat()
            ops.append(cmp_map[tok["k"]])
            comparators.append(self._parse_addsub())
        if len(ops) == 0:
            return node
        start_col = int(node["source_span"]["col"]) - self.col_base
        end_col = int(comparators[-1]["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "Compare",
            "source_span": self._node_span(start_col, end_col),
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": self._src_slice(start_col, end_col),
            "left": node,
            "ops": ops,
            "comparators": comparators,
        }

    def _parse_addsub(self) -> dict[str, Any]:
        node = self._parse_muldiv()
        while self._cur()["k"] in {"+", "-"}:
            op_tok = self._eat()
            right = self._parse_muldiv()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_muldiv(self) -> dict[str, Any]:
        node = self._parse_unary()
        while self._cur()["k"] in {"*", "/", "%"}:
            op_tok = self._eat()
            right = self._parse_unary()
            node = self._make_bin(node, op_tok["k"], right)
        return node

    def _parse_unary(self) -> dict[str, Any]:
        if self._cur()["k"] in {"+", "-"}:
            tok = self._eat()
            operand = self._parse_unary()
            s = tok["s"]
            e = int(operand["source_span"]["end_col"]) - self.col_base
            out_t = str(operand.get("resolved_type", "unknown"))
            return {
                "kind": "UnaryOp",
                "source_span": self._node_span(s, e),
                "resolved_type": out_t if out_t in {"int64", "float64"} else "unknown",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(s, e),
                "op": "USub" if tok["k"] == "-" else "UAdd",
                "operand": operand,
            }
        return self._parse_postfix()

    def _lookup_method_return(self, cls_name: str, method: str) -> str:
        cur: str | None = cls_name
        while cur is not None:
            methods = self.class_method_return_types.get(cur, {})
            if method in methods:
                return methods[method]
            cur = self.class_base.get(cur)
        return "unknown"

    def _parse_postfix(self) -> dict[str, Any]:
        node = self._parse_primary()
        while True:
            tok = self._cur()
            if tok["k"] == ".":
                self._eat(".")
                name_tok = self._eat("NAME")
                s = int(node["source_span"]["col"]) - self.col_base
                e = name_tok["e"]
                node = {
                    "kind": "Attribute",
                    "source_span": self._node_span(s, e),
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "value": node,
                    "attr": str(name_tok["v"]),
                }
                continue
            if tok["k"] == "(":
                ltok = self._eat("(")
                args: list[dict[str, Any]] = []
                if self._cur()["k"] != ")":
                    while True:
                        args.append(self._parse_addsub())
                        if self._cur()["k"] == ",":
                            self._eat(",")
                            continue
                        break
                rtok = self._eat(")")
                s = int(node["source_span"]["col"]) - self.col_base
                e = rtok["e"]
                call_ret = "unknown"
                fn_name = ""
                if isinstance(node, dict) and node.get("kind") == "Name":
                    fn_name = str(node.get("id", ""))
                    if fn_name == "print":
                        call_ret = "None"
                    elif fn_name in self.fn_return_types:
                        call_ret = self.fn_return_types[fn_name]
                    elif fn_name in self.class_method_return_types:
                        call_ret = fn_name
                elif isinstance(node, dict) and node.get("kind") == "Attribute":
                    owner = node.get("value")
                    attr = str(node.get("attr", ""))
                    if isinstance(owner, dict) and owner.get("kind") == "Name":
                        owner_t = self.name_types.get(str(owner.get("id", "")), "unknown")
                        if owner_t != "unknown":
                            call_ret = self._lookup_method_return(owner_t, attr)
                payload: dict[str, Any] = {
                    "kind": "Call",
                    "source_span": self._node_span(s, e),
                    "resolved_type": call_ret,
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": self._src_slice(s, e),
                    "func": node,
                    "args": args,
                    "keywords": [],
                }
                if fn_name == "print":
                    payload["lowered_kind"] = "BuiltinCall"
                    payload["builtin_name"] = "print"
                    payload["runtime_call"] = "py_print"
                node = payload
                continue
            return node

    def _make_bin(self, left: dict[str, Any], op_sym: str, right: dict[str, Any]) -> dict[str, Any]:
        op_map = {"+": "Add", "-": "Sub", "*": "Mult", "/": "Div", "%": "Mod"}
        lt = str(left.get("resolved_type", "unknown"))
        rt = str(right.get("resolved_type", "unknown"))
        casts: list[dict[str, Any]] = []
        if op_sym == "/":
            out_t = "float64"
            if lt == "int64":
                casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
            if rt == "int64":
                casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
        elif lt == rt and lt in {"int64", "float64"}:
            out_t = lt
        elif lt in {"int64", "float64"} and rt in {"int64", "float64"}:
            out_t = "float64"
            if lt == "int64":
                casts.append({"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
            if rt == "int64":
                casts.append({"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"})
        else:
            out_t = "unknown"

        ls = int(left["source_span"]["col"]) - self.col_base
        rs = int(right["source_span"]["end_col"]) - self.col_base
        return {
            "kind": "BinOp",
            "source_span": self._node_span(ls, rs),
            "resolved_type": out_t,
            "borrow_kind": "value",
            "casts": casts,
            "repr": self._src_slice(ls, rs),
            "left": left,
            "op": op_map[op_sym],
            "right": right,
        }

    def _parse_primary(self) -> dict[str, Any]:
        tok = self._cur()
        if tok["k"] == "INT":
            self._eat("INT")
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
                "repr": tok["v"],
                "value": int(tok["v"]),
            }
        if tok["k"] == "FLOAT":
            self._eat("FLOAT")
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "float64",
                "borrow_kind": "value",
                "casts": [],
                "repr": tok["v"],
                "value": float(tok["v"]),
            }
        if tok["k"] == "STR":
            self._eat("STR")
            raw = tok["v"]
            return {
                "kind": "Constant",
                "source_span": self._node_span(tok["s"], tok["e"]),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
                "repr": raw,
                "value": raw[1:-1],
            }
        if tok["k"] == "NAME":
            name_tok = self._eat("NAME")
            nm = str(name_tok["v"])
            if nm in {"True", "False"}:
                return {
                    "kind": "Constant",
                    "source_span": self._node_span(name_tok["s"], name_tok["e"]),
                    "resolved_type": "bool",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": nm,
                    "value": (nm == "True"),
                }
            t = self.name_types.get(nm, "unknown")
            return {
                "kind": "Name",
                "source_span": self._node_span(name_tok["s"], name_tok["e"]),
                "resolved_type": t,
                "borrow_kind": "readonly_ref" if t != "unknown" else "value",
                "casts": [],
                "repr": nm,
                "id": nm,
            }
        if tok["k"] == "(":
            l = self._eat("(")
            inner = self._parse_addsub()
            r = self._eat(")")
            inner["source_span"] = self._node_span(l["s"], r["e"])
            inner["repr"] = self._src_slice(l["s"], r["e"])
            return inner
        if tok["k"] == "[":
            l = self._eat("[")
            elements: list[dict[str, Any]] = []
            if self._cur()["k"] != "]":
                while True:
                    elements.append(self._parse_addsub())
                    if self._cur()["k"] == ",":
                        self._eat(",")
                        continue
                    break
            r = self._eat("]")
            et = "unknown"
            if len(elements) > 0:
                et = str(elements[0].get("resolved_type", "unknown"))
                for e in elements[1:]:
                    if str(e.get("resolved_type", "unknown")) != et:
                        et = "unknown"
                        break
            return {
                "kind": "List",
                "source_span": self._node_span(l["s"], r["e"]),
                "resolved_type": f"list[{et}]",
                "borrow_kind": "value",
                "casts": [],
                "repr": self._src_slice(l["s"], r["e"]),
                "elements": elements,
            }
        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse expression token: {tok['k']}",
            source_span=self._node_span(tok["s"], tok["e"]),
            hint="Extend self_hosted expression parser for this syntax.",
        )


def _sh_parse_expr(
    text: str,
    *,
    line_no: int,
    col_base: int,
    name_types: dict[str, str],
    fn_return_types: dict[str, str],
    class_method_return_types: dict[str, dict[str, str]] | None = None,
    class_base: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    txt = text.strip()
    if txt == "":
        raise EastBuildError(
            kind="unsupported_syntax",
            message="empty expression in self_hosted backend",
            source_span=_sh_span(line_no, col_base, col_base),
            hint="Provide a non-empty expression.",
        )
    parser = _ShExprParser(
        txt,
        line_no=line_no,
        col_base=col_base + (len(text) - len(text.lstrip())),
        name_types=name_types,
        fn_return_types=fn_return_types,
        class_method_return_types=class_method_return_types,
        class_base=class_base,
    )
    return parser.parse()


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Self-hosted parser path for the growing EAST subset."""
    lines = source.splitlines()
    leading_file_comments: list[str] = []
    leading_file_trivia: list[dict[str, Any]] = []
    for ln in lines:
        s = ln.strip()
        if s == "":
            if len(leading_file_comments) > 0:
                leading_file_trivia.append({"kind": "blank", "count": 1})
            continue
        if s.startswith("#"):
            text = s[1:].lstrip()
            leading_file_comments.append(text)
            leading_file_trivia.append({"kind": "comment", "text": text})
            continue
        break

    def parse_def_sig(ln_no: int, ln: str, *, in_class: str | None = None) -> dict[str, Any] | None:
        m_def = re.match(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*->\s*(.+)\s*:\s*$", ln)
        if m_def is None:
            return None
        arg_types: dict[str, str] = {}
        args_raw = m_def.group(2)
        if args_raw.strip() != "":
            for p_txt, _off in _sh_split_args_with_offsets(args_raw):
                p = p_txt.strip()
                if p == "":
                    continue
                if in_class is not None and p == "self":
                    arg_types["self"] = in_class
                    continue
                if ":" not in p:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use `name: Type` style parameters.",
                    )
                pn, pt = p.split(":", 1)
                pn = pn.strip()
                pt = pt.strip()
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pn):
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter name: {pn}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use valid identifier for parameter name.",
                    )
                if pt == "":
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse parameter type: {p_txt}",
                        source_span=_sh_span(ln_no, 0, len(ln)),
                        hint="Use `name: Type` style parameters.",
                    )
                arg_types[pn] = _sh_ann_to_type(pt)
        return {
            "name": m_def.group(1),
            "ret": _sh_ann_to_type(m_def.group(3).strip()),
            "arg_types": arg_types,
        }

    class_method_return_types: dict[str, dict[str, str]] = {}
    class_base: dict[str, str | None] = {}
    fn_returns: dict[str, str] = {}

    cur_cls: str | None = None
    cur_cls_indent = 0
    for ln_no, ln in enumerate(lines, start=1):
        s = ln.strip()
        if s == "":
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if cur_cls is not None and indent <= cur_cls_indent and not s.startswith("#"):
            cur_cls = None
        m_cls = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cur_cls = m_cls.group(1)
            cur_cls_indent = indent
            class_base[cur_cls] = m_cls.group(2)
            class_method_return_types.setdefault(cur_cls, {})
            continue
        if cur_cls is None:
            sig = parse_def_sig(ln_no, ln)
            if sig is not None:
                fn_returns[str(sig["name"])] = str(sig["ret"])
            continue
        sig = parse_def_sig(ln_no, ln, in_class=cur_cls)
        if sig is not None:
            class_method_return_types[cur_cls][str(sig["name"])] = str(sig["ret"])

    def split_top_commas(txt: str) -> list[str]:
        out: list[str] = []
        depth = 0
        in_str: str | None = None
        esc = False
        start = 0
        for i, ch in enumerate(txt):
            if in_str is not None:
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if ch == in_str:
                    in_str = None
                continue
            if ch in {"'", '"'}:
                in_str = ch
                continue
            if ch in {"(", "[", "{"}:
                depth += 1
                continue
            if ch in {")", "]", "}"}:
                depth -= 1
                continue
            if ch == "," and depth == 0:
                out.append(txt[start:i].strip())
                start = i + 1
        tail = txt[start:].strip()
        if tail != "":
            out.append(tail)
        return out

    def parse_expr(expr_txt: str, *, ln_no: int, col: int, name_types: dict[str, str]) -> dict[str, Any]:
        raw = expr_txt
        txt = raw.strip()
        if len(txt) >= 3 and txt[0] == "f" and txt[1] in {"'", '"'} and txt[-1] == txt[1]:
            quote = txt[1]
            inner = txt[2:-1]
            values: list[dict[str, Any]] = []
            i = 0
            while i < len(inner):
                j = inner.find("{", i)
                if j < 0:
                    tail = inner[i:]
                    if tail != "":
                        values.append(
                            {
                                "kind": "Constant",
                                "source_span": _sh_span(ln_no, col, col + len(raw)),
                                "resolved_type": "str",
                                "borrow_kind": "value",
                                "casts": [],
                                "repr": repr(tail),
                                "value": tail,
                            }
                        )
                    break
                if j > i:
                    lit = inner[i:j]
                    values.append(
                        {
                            "kind": "Constant",
                            "source_span": _sh_span(ln_no, col, col + len(raw)),
                            "resolved_type": "str",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": repr(lit),
                            "value": lit,
                        }
                    )
                k = inner.find("}", j + 1)
                if k < 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message="unterminated f-string placeholder in self_hosted parser",
                        source_span=_sh_span(ln_no, col, col + len(raw)),
                        hint="Close f-string placeholder with `}`.",
                    )
                inner_expr = inner[j + 1 : k].strip()
                values.append({"kind": "FormattedValue", "value": parse_expr(inner_expr, ln_no=ln_no, col=col, name_types=dict(name_types))})
                i = k + 1
            return {
                "kind": "JoinedStr",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "values": values,
            }

        tuple_parts = split_top_commas(txt)
        if len(tuple_parts) >= 2:
            elems = [parse_expr(p, ln_no=ln_no, col=col + txt.find(p), name_types=dict(name_types)) for p in tuple_parts]
            elem_ts = [str(e.get("resolved_type", "unknown")) for e in elems]
            return {
                "kind": "Tuple",
                "source_span": _sh_span(ln_no, col, col + len(raw)),
                "resolved_type": "tuple[" + ", ".join(elem_ts) + "]",
                "borrow_kind": "value",
                "casts": [],
                "repr": txt,
                "elements": elems,
            }

        return _sh_parse_expr(
            txt,
            line_no=ln_no,
            col_base=col,
            name_types=name_types,
            fn_return_types=fn_returns,
            class_method_return_types=class_method_return_types,
            class_base=class_base,
        )

    def parse_stmt_block(body_lines: list[tuple[int, str]], *, name_types: dict[str, str], scope_label: str) -> list[dict[str, Any]]:
        stmts: list[dict[str, Any]] = []

        def collect_indented_block(start: int, parent_indent: int) -> tuple[list[tuple[int, str]], int]:
            out: list[tuple[int, str]] = []
            j = start
            while j < len(body_lines):
                n_no, n_ln = body_lines[j]
                if n_ln.strip() == "":
                    j += 1
                    continue
                n_indent = len(n_ln) - len(n_ln.lstrip(" "))
                if n_indent <= parent_indent:
                    break
                out.append((n_no, n_ln))
                j += 1
            return out, j

        i = 0
        while i < len(body_lines):
            ln_no, ln_txt = body_lines[i]
            indent = len(ln_txt) - len(ln_txt.lstrip(" "))
            s = ln_txt.strip()

            if s.startswith("if ") and s.endswith(":"):
                cond_txt = s[len("if ") : -1].strip()
                cond_col = ln_txt.find(cond_txt)
                cond_expr = parse_expr(cond_txt, ln_no=ln_no, col=cond_col, name_types=dict(name_types))
                then_block, j = collect_indented_block(i + 1, indent)
                if len(then_block) == 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"if body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented if-body.",
                    )
                else_stmt_list: list[dict[str, Any]] = []
                if j < len(body_lines):
                    e_no, e_ln = body_lines[j]
                    e_indent = len(e_ln) - len(e_ln.lstrip(" "))
                    if e_indent == indent and e_ln.strip() == "else:":
                        else_block, k = collect_indented_block(j + 1, indent)
                        if len(else_block) == 0:
                            raise EastBuildError(
                                kind="unsupported_syntax",
                                message=f"else body is missing in '{scope_label}'",
                                source_span=_sh_span(e_no, 0, len(e_ln)),
                                hint="Add indented else-body.",
                            )
                        else_stmt_list = parse_stmt_block(else_block, name_types=dict(name_types), scope_label=scope_label)
                        j = k
                stmts.append(
                    {
                        "kind": "If",
                        "source_span": _sh_span(ln_no, ln_txt.find("if "), len(ln_txt)),
                        "test": cond_expr,
                        "body": parse_stmt_block(then_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": else_stmt_list,
                    }
                )
                i = j
                continue

            if s.startswith("for ") and s.endswith(":"):
                m_for = re.match(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+):$", s)
                if m_for is None:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"self_hosted parser cannot parse for statement: {s}",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Use `for name in iterable:` form.",
                    )
                tgt = m_for.group(1)
                iter_txt = m_for.group(2).strip()
                iter_col = ln_txt.find(iter_txt)
                iter_expr = parse_expr(iter_txt, ln_no=ln_no, col=iter_col, name_types=dict(name_types))
                body_block, j = collect_indented_block(i + 1, indent)
                if len(body_block) == 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"for body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented for-body.",
                    )
                t_ty = "unknown"
                i_ty = str(iter_expr.get("resolved_type", "unknown"))
                if i_ty.startswith("list[") and i_ty.endswith("]"):
                    t_ty = i_ty[5:-1]
                elif i_ty.startswith("tuple[") and i_ty.endswith("]"):
                    t_ty = "unknown"
                elif i_ty.startswith("set[") and i_ty.endswith("]"):
                    t_ty = i_ty[4:-1]
                if t_ty != "unknown":
                    name_types[tgt] = t_ty
                stmts.append(
                    {
                        "kind": "For",
                        "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                        "target": {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, ln_txt.find(tgt), ln_txt.find(tgt) + len(tgt)),
                            "resolved_type": name_types.get(tgt, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": tgt,
                            "id": tgt,
                        },
                        "target_type": name_types.get(tgt, "unknown"),
                        "iter": iter_expr,
                        "body": parse_stmt_block(body_block, name_types=dict(name_types), scope_label=scope_label),
                        "orelse": [],
                    }
                )
                i = j
                continue

            if s == "try:":
                try_body, j = collect_indented_block(i + 1, indent)
                if len(try_body) == 0:
                    raise EastBuildError(
                        kind="unsupported_syntax",
                        message=f"try body is missing in '{scope_label}'",
                        source_span=_sh_span(ln_no, 0, len(ln_txt)),
                        hint="Add indented try-body.",
                    )
                handlers: list[dict[str, Any]] = []
                finalbody: list[dict[str, Any]] = []
                while j < len(body_lines):
                    h_no, h_ln = body_lines[j]
                    h_s = h_ln.strip()
                    h_indent = len(h_ln) - len(h_ln.lstrip(" "))
                    if h_indent != indent:
                        break
                    m_exc = re.match(r"^except\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", h_s)
                    if m_exc is not None:
                        ex_type = m_exc.group(1)
                        ex_name = m_exc.group(2)
                        h_body, k = collect_indented_block(j + 1, indent)
                        handlers.append(
                            {
                                "kind": "ExceptHandler",
                                "type": {
                                    "kind": "Name",
                                    "source_span": _sh_span(h_no, h_ln.find(ex_type), h_ln.find(ex_type) + len(ex_type)),
                                    "resolved_type": "unknown",
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": ex_type,
                                    "id": ex_type,
                                },
                                "name": ex_name,
                                "body": parse_stmt_block(h_body, name_types=dict(name_types), scope_label=scope_label),
                            }
                        )
                        j = k
                        continue
                    if h_s == "finally:":
                        f_body, k = collect_indented_block(j + 1, indent)
                        finalbody = parse_stmt_block(f_body, name_types=dict(name_types), scope_label=scope_label)
                        j = k
                        continue
                    break
                stmts.append(
                    {
                        "kind": "Try",
                        "source_span": _sh_span(ln_no, 0, len(ln_txt)),
                        "body": parse_stmt_block(try_body, name_types=dict(name_types), scope_label=scope_label),
                        "handlers": handlers,
                        "orelse": [],
                        "finalbody": finalbody,
                    }
                )
                i = j
                continue

            if s.startswith("raise "):
                expr_txt = s[len("raise ") :].strip()
                expr_col = ln_txt.find(expr_txt)
                stmts.append(
                    {
                        "kind": "Raise",
                        "source_span": _sh_span(ln_no, ln_txt.find("raise "), len(ln_txt)),
                        "exc": parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    }
                )
                i += 1
                continue

            if s == "pass":
                stmts.append({"kind": "Pass", "source_span": _sh_span(ln_no, indent, indent + 4)})
                i += 1
                continue

            if s.startswith("return "):
                rcol = ln_txt.find("return ")
                expr_txt = ln_txt[rcol + len("return ") :].strip()
                expr_col = ln_txt.find(expr_txt, rcol + len("return "))
                stmts.append(
                    {
                        "kind": "Return",
                        "source_span": _sh_span(ln_no, rcol, len(ln_txt)),
                        "value": parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types)),
                    }
                )
                i += 1
                continue

            m_ann = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
            if m_ann is not None:
                target_txt = m_ann.group(1)
                ann = _sh_ann_to_type(m_ann.group(2))
                expr_txt = m_ann.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    name_types[str(target_expr.get("id", ""))] = ann
                stmts.append(
                    {
                        "kind": "AnnAssign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "annotation": ann,
                        "value": val_expr,
                        "declare": True,
                        "decl_type": ann,
                    }
                )
                i += 1
                continue

            m_aug = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\+=|-=|\*=|/=)\s*(.+)$", s)
            if m_aug is not None:
                target_txt = m_aug.group(1)
                op_map = {"+=": "Add", "-=": "Sub", "*=": "Mult", "/=": "Div"}
                expr_txt = m_aug.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                target_ty = "unknown"
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    target_ty = name_types.get(str(target_expr.get("id", "")), "unknown")
                stmts.append(
                    {
                        "kind": "AugAssign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "op": op_map[m_aug.group(2)],
                        "value": val_expr,
                        "declare": False,
                        "decl_type": target_ty if target_ty != "unknown" else None,
                    }
                )
                i += 1
                continue

            m_tasg = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", s)
            if m_tasg is not None:
                n1 = m_tasg.group(1)
                n2 = m_tasg.group(2)
                expr_txt = m_tasg.group(3).strip()
                expr_col = ln_txt.find(expr_txt)
                rhs = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                c1 = ln_txt.find(n1)
                c2 = ln_txt.find(n2, c1 + len(n1))
                target_expr = {
                    "kind": "Tuple",
                    "source_span": _sh_span(ln_no, c1, c2 + len(n2)),
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": f"{n1}, {n2}",
                    "elements": [
                        {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, c1, c1 + len(n1)),
                            "resolved_type": name_types.get(n1, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": n1,
                            "id": n1,
                        },
                        {
                            "kind": "Name",
                            "source_span": _sh_span(ln_no, c2, c2 + len(n2)),
                            "resolved_type": name_types.get(n2, "unknown"),
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": n2,
                            "id": n2,
                        },
                    ],
                }
                stmts.append(
                    {
                        "kind": "Assign",
                        "source_span": _sh_span(ln_no, c1, len(ln_txt)),
                        "target": target_expr,
                        "value": rhs,
                        "declare": False,
                        "decl_type": None,
                    }
                )
                i += 1
                continue

            m_asg = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*=\s*(.+)$", s)
            if m_asg is not None:
                target_txt = m_asg.group(1)
                expr_txt = m_asg.group(2).strip()
                expr_col = ln_txt.find(expr_txt)
                target_col = ln_txt.find(target_txt)
                target_expr = parse_expr(target_txt, ln_no=ln_no, col=target_col, name_types=dict(name_types))
                val_expr = parse_expr(expr_txt, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
                decl_type = val_expr.get("resolved_type", "unknown")
                if isinstance(target_expr, dict) and target_expr.get("kind") == "Name":
                    nm = str(target_expr.get("id", ""))
                    if nm != "":
                        name_types[nm] = str(decl_type)
                stmts.append(
                    {
                        "kind": "Assign",
                        "source_span": _sh_span(ln_no, target_col, len(ln_txt)),
                        "target": target_expr,
                        "value": val_expr,
                        "declare": True,
                        "declare_init": True,
                        "decl_type": decl_type,
                    }
                )
                i += 1
                continue

            expr_col = len(ln_txt) - len(ln_txt.lstrip(" "))
            expr_stmt = parse_expr(s, ln_no=ln_no, col=expr_col, name_types=dict(name_types))
            stmts.append({"kind": "Expr", "source_span": _sh_span(ln_no, expr_col, len(ln_txt)), "value": expr_stmt})
            i += 1
        return stmts

    body_items: list[dict[str, Any]] = []
    main_stmts: list[dict[str, Any]] = []
    first_item_attached = False

    i = 1
    while i <= len(lines):
        ln = lines[i - 1]
        s = ln.strip()
        if s == "" or s.startswith("#"):
            i += 1
            continue
        if ln.startswith(" "):
            i += 1
            continue

        m_main = re.match(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*$", ln)
        if m_main is not None:
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    j += 1
                    continue
                if not bl.startswith(" "):
                    break
                block.append((j, bl))
                j += 1
            main_name_types: dict[str, str] = {}
            main_stmts = parse_stmt_block(block, name_types=main_name_types, scope_label="__main__")
            i = j
            continue

        m_def = re.match(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*->\s*(.+)\s*:\s*$", ln)
        if m_def is not None:
            sig = parse_def_sig(i, ln)
            assert sig is not None
            fn_name = str(sig["name"])
            fn_ret = str(sig["ret"])
            arg_types = dict(sig["arg_types"])
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    j += 1
                    continue
                if not bl.startswith(" "):
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty function body '{fn_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add return or assignment statements in function body.",
                )
            stmts = parse_stmt_block(block, name_types=dict(arg_types), scope_label=fn_name)
            item = {
                "kind": "FunctionDef",
                "name": fn_name,
                "original_name": fn_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "arg_types": arg_types,
                "return_type": fn_ret,
                "arg_usage": {n: "readonly" for n in arg_types.keys()},
                "renamed_symbols": {},
                "leading_comments": [],
                "leading_trivia": [],
                "body": stmts,
            }
            if not first_item_attached:
                item["leading_comments"] = list(leading_file_comments)
                item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(item)
            i = j
            continue

        m_cls = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$", ln)
        if m_cls is not None:
            cls_name = m_cls.group(1)
            base = m_cls.group(2)
            cls_indent = len(ln) - len(ln.lstrip(" "))
            block: list[tuple[int, str]] = []
            j = i + 1
            while j <= len(lines):
                bl = lines[j - 1]
                if bl.strip() == "":
                    j += 1
                    continue
                bind = len(bl) - len(bl.lstrip(" "))
                if bind <= cls_indent:
                    break
                block.append((j, bl))
                j += 1
            if len(block) == 0:
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser requires non-empty class body '{cls_name}'",
                    source_span=_sh_span(i, 0, len(ln)),
                    hint="Add field or method definitions.",
                )

            field_types: dict[str, str] = {}
            class_body: list[dict[str, Any]] = []
            k = 0
            while k < len(block):
                ln_no, ln_txt = block[k]
                s2 = ln_txt.strip()
                bind = len(ln_txt) - len(ln_txt.lstrip(" "))
                if bind == cls_indent + 4:
                    m_field = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s2)
                    if m_field is not None:
                        fname = m_field.group(1)
                        fty = _sh_ann_to_type(m_field.group(2))
                        fexpr_txt = m_field.group(3).strip()
                        fexpr_col = ln_txt.find(fexpr_txt)
                        field_types[fname] = fty
                        class_body.append(
                            {
                                "kind": "AnnAssign",
                                "source_span": _sh_span(ln_no, ln_txt.find(fname), len(ln_txt)),
                                "target": {
                                    "kind": "Name",
                                    "source_span": _sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + len(fname)),
                                    "resolved_type": fty,
                                    "borrow_kind": "value",
                                    "casts": [],
                                    "repr": fname,
                                    "id": fname,
                                },
                                "annotation": fty,
                                "value": parse_expr(fexpr_txt, ln_no=ln_no, col=fexpr_col, name_types={}),
                                "declare": True,
                                "decl_type": fty,
                            }
                        )
                        k += 1
                        continue
                    sig = parse_def_sig(ln_no, ln_txt, in_class=cls_name)
                    if sig is not None:
                        mname = str(sig["name"])
                        marg_types = dict(sig["arg_types"])
                        mret = str(sig["ret"])
                        method_block: list[tuple[int, str]] = []
                        m = k + 1
                        while m < len(block):
                            n_no, n_txt = block[m]
                            n_indent = len(n_txt) - len(n_txt.lstrip(" "))
                            if n_indent <= bind:
                                break
                            method_block.append((n_no, n_txt))
                            m += 1
                        if len(method_block) == 0:
                            raise EastBuildError(
                                kind="unsupported_syntax",
                                message=f"self_hosted parser requires non-empty method body '{cls_name}.{mname}'",
                                source_span=_sh_span(ln_no, 0, len(ln_txt)),
                                hint="Add method statements.",
                            )
                        local_types = dict(marg_types)
                        for fnm, fty in field_types.items():
                            local_types[fnm] = fty
                        stmts = parse_stmt_block(method_block, name_types=local_types, scope_label=f"{cls_name}.{mname}")
                        if mname == "__init__":
                            for st in stmts:
                                if st.get("kind") == "Assign":
                                    tgt = st.get("target")
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt.get("value"), dict)
                                        and tgt.get("value", {}).get("kind") == "Name"
                                        and tgt.get("value", {}).get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        if fname != "":
                                            t = st.get("decl_type") or (st.get("value") or {}).get("resolved_type")
                                            if isinstance(t, str) and t != "":
                                                field_types[fname] = t
                                if st.get("kind") == "AnnAssign":
                                    tgt = st.get("target")
                                    if (
                                        isinstance(tgt, dict)
                                        and tgt.get("kind") == "Attribute"
                                        and isinstance(tgt.get("value"), dict)
                                        and tgt.get("value", {}).get("kind") == "Name"
                                        and tgt.get("value", {}).get("id") == "self"
                                    ):
                                        fname = str(tgt.get("attr", ""))
                                        ann = st.get("annotation")
                                        if fname != "" and isinstance(ann, str) and ann != "":
                                            field_types[fname] = ann
                        class_body.append(
                            {
                                "kind": "FunctionDef",
                                "name": mname,
                                "original_name": mname,
                                "source_span": {
                                    "lineno": ln_no,
                                    "col": bind,
                                    "end_lineno": method_block[-1][0],
                                    "end_col": len(method_block[-1][1]),
                                },
                                "arg_types": marg_types,
                                "return_type": mret,
                                "arg_usage": {n: "readonly" for n in marg_types.keys()},
                                "renamed_symbols": {},
                                "body": stmts,
                            }
                        )
                        k = m
                        continue
                raise EastBuildError(
                    kind="unsupported_syntax",
                    message=f"self_hosted parser cannot parse class statement: {s2}",
                    source_span=_sh_span(ln_no, 0, len(ln_txt)),
                    hint="Use field annotation or method definitions in class body.",
                )

            cls_item = {
                "kind": "ClassDef",
                "name": cls_name,
                "original_name": cls_name,
                "source_span": {"lineno": i, "col": 0, "end_lineno": block[-1][0], "end_col": len(block[-1][1])},
                "base": base,
                "field_types": field_types,
                "body": class_body,
            }
            if not first_item_attached:
                cls_item["leading_comments"] = list(leading_file_comments)
                cls_item["leading_trivia"] = list(leading_file_trivia)
                first_item_attached = True
            body_items.append(cls_item)
            i = j
            continue

        m_ann_top = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^=]+?)\s*=\s*(.+)$", s)
        if m_ann_top is not None:
            name = m_ann_top.group(1)
            ann = _sh_ann_to_type(m_ann_top.group(2))
            expr_txt = m_ann_top.group(3).strip()
            expr_col = ln.find(expr_txt)
            body_items.append(
                {
                    "kind": "AnnAssign",
                    "source_span": _sh_span(i, ln.find(name), len(ln)),
                    "target": {
                        "kind": "Name",
                        "source_span": _sh_span(i, ln.find(name), ln.find(name) + len(name)),
                        "resolved_type": ann,
                        "borrow_kind": "value",
                        "casts": [],
                        "repr": name,
                        "id": name,
                    },
                    "annotation": ann,
                    "value": parse_expr(expr_txt, ln_no=i, col=expr_col, name_types={}),
                    "declare": True,
                    "decl_type": ann,
                }
            )
            i += 1
            continue

        raise EastBuildError(
            kind="unsupported_syntax",
            message=f"self_hosted parser cannot parse top-level statement: {s}",
            source_span=_sh_span(i, 0, len(ln)),
            hint="Use def/class/top-level typed assignment/main guard.",
        )

    if len(main_stmts) == 0:
        raise EastBuildError(
            kind="unsupported_syntax",
            message="self_hosted parser requires if __name__ == \"__main__\": block",
            source_span={"lineno": None, "col": None, "end_lineno": None, "end_col": None},
            hint="Add main guard block with print(...).",
        )

    return {
        "kind": "Module",
        "source_path": filename,
        "source_span": {"lineno": None, "col": None, "end_lineno": None, "end_col": None},
        "body": body_items,
        "main_guard_body": main_stmts,
        "renamed_symbols": {},
        "meta": {"parser_backend": "self_hosted"},
    }


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "python_ast") -> dict[str, Any]:
    if parser_backend == "python_ast":
        return convert_source_to_east(source, filename)
    if parser_backend == "self_hosted":
        return convert_source_to_east_self_hosted(source, filename)
    raise EastBuildError(
        kind="unsupported_syntax",
        message=f"unknown parser backend: {parser_backend}",
        source_span={"lineno": None, "col": None, "end_lineno": None, "end_col": None},
        hint="Use parser_backend in {python_ast, self_hosted}.",
    )


def convert_path(input_path: Path, parser_backend: str = "python_ast") -> dict[str, Any]:
    """Read Python file and convert to EAST document."""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)


def _dump_json(obj: dict[str, Any], *, pretty: bool) -> str:
    """Serialize output JSON in compact or pretty mode."""
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _indent(lines: list[str], level: int = 1) -> list[str]:
    """Indent helper for human-readable C++-style rendering."""
    prefix = "    " * level
    return [prefix + ln if ln else "" for ln in lines]


def _fmt_span(span: dict[str, Any] | None) -> str:
    """Format source span as `line:col` for comments."""
    if not span:
        return "?:?"
    ln = span.get("lineno")
    col = span.get("col")
    if ln is None or col is None:
        return "?:?"
    return f"{ln}:{col}"


def _render_expr(expr: dict[str, Any] | None) -> str:
    """Render EAST expression as compact C++-style pseudo expression."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        rep = f"<{expr.get('kind', 'Expr')}>"
    typ = expr.get("resolved_type", "unknown")
    borrow = expr.get("borrow_kind", "value")
    casts = expr.get("casts", [])
    cast_txt = ""
    if casts:
        cast_parts = []
        for c in casts:
            cast_parts.append(f"{c.get('on')}:{c.get('from')}->{c.get('to')}({c.get('reason')})")
        cast_txt = " casts=" + ",".join(cast_parts)
    return f"{rep} /* type={typ}, borrow={borrow}{cast_txt} */"


def _expr_repr(expr: dict[str, Any] | None) -> str:
    """Best-effort expression representation (without metadata suffix)."""
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        return f"<{expr.get('kind', 'Expr')}>"
    return rep


def _cpp_type_name(east_type: str | None) -> str:
    """Map EAST type names to human-view C++-like type labels."""
    if east_type is None:
        return "auto"
    if east_type in INT_TYPES | FLOAT_TYPES | {"bool", "str", "Path", "Exception", "None"}:
        return east_type
    if east_type.startswith("list["):
        return east_type
    if east_type.startswith("dict["):
        return east_type
    if east_type.startswith("set["):
        return east_type
    if east_type.startswith("tuple["):
        return east_type
    return "auto"


def _render_stmt(stmt: dict[str, Any], level: int = 1) -> list[str]:
    """Render one EAST statement as C++-style pseudo source lines."""
    k = stmt.get("kind")
    sp = _fmt_span(stmt.get("source_span"))
    pad = "    " * level
    out: list[str] = []

    if k == "Import":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] import {names};")
        return _indent(out, level)
    if k == "ImportFrom":
        names = ", ".join((n["name"] if n.get("asname") is None else f"{n['name']} as {n['asname']}") for n in stmt.get("names", []))
        out.append(f"// [{sp}] from {stmt.get('module')} import {names};")
        return _indent(out, level)
    if k == "Pass":
        return _indent([f"// [{sp}] pass;"], level)
    if k == "Break":
        return _indent([f"// [{sp}] break;"], level)
    if k == "Continue":
        return _indent([f"// [{sp}] continue;"], level)
    if k == "Return":
        v = _render_expr(stmt.get("value")) if stmt.get("value") is not None else "/* void */"
        return _indent([f"// [{sp}]", f"return {v};"], level)
    if k == "Expr":
        return _indent([f"// [{sp}]", f"{_render_expr(stmt.get('value'))};"], level)
    if k == "Assign":
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "AnnAssign":
        ann = stmt.get("annotation", "auto")
        return _indent(
            [
                f"// [{sp}]",
                f"{ann} {_render_expr(stmt.get('target'))} = {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "AugAssign":
        op = stmt.get("op", "Op")
        return _indent(
            [
                f"// [{sp}]",
                f"{_render_expr(stmt.get('target'))} /* {op} */= {_render_expr(stmt.get('value'))};",
            ],
            level,
        )
    if k == "If":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}if ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}else {{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "For":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} : { _render_expr(stmt.get('iter')) }) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "ForRange":
        tgt_expr = stmt.get("target")
        tgt = _expr_repr(tgt_expr)
        tgt_ty = _cpp_type_name((tgt_expr or {}).get("resolved_type") if isinstance(tgt_expr, dict) else None)
        start = _render_expr(stmt.get("start"))
        stop = _render_expr(stmt.get("stop"))
        step = _render_expr(stmt.get("step"))
        mode = stmt.get("range_mode", "dynamic")
        if mode == "ascending":
            cond = f"({tgt}) < ({stop})"
        elif mode == "descending":
            cond = f"({tgt}) > ({stop})"
        else:
            cond = f"({step}) > 0 ? ({tgt}) < ({stop}) : ({tgt}) > ({stop})"
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}for ({tgt_ty} {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// for-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "While":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}while ({_render_expr(stmt.get('test'))}) {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// while-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "Raise":
        return _indent([f"// [{sp}]", f"throw {_render_expr(stmt.get('exc'))};"], level)
    if k == "Try":
        out.append(f"{pad}// [{sp}]")
        out.append(f"{pad}try {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        for h in stmt.get("handlers", []):
            ex_name = h.get("name") or "ex"
            ex_type = _render_expr(h.get("type"))
            out.append(f"{pad}catch ({ex_type} as {ex_name}) {{")
            for s in h.get("body", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("orelse"):
            out.append(f"{pad}// try-else")
            out.append(f"{pad}{{")
            for s in stmt.get("orelse", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        if stmt.get("finalbody"):
            out.append(f"{pad}/* finally */ {{")
            for s in stmt.get("finalbody", []):
                out.extend(_render_stmt(s, level + 1))
            out.append(f"{pad}}}")
        return out
    if k == "FunctionDef":
        name = stmt.get("name", "fn")
        ret = stmt.get("return_type", "None")
        arg_types: dict[str, str] = stmt.get("arg_types", {})
        arg_usage: dict[str, str] = stmt.get("arg_usage", {})
        params = []
        for n, t in arg_types.items():
            usage = arg_usage.get(n, "readonly")
            params.append(f"{t} {n} /* {usage} */")
        out.append(f"{pad}// [{sp}] function original={stmt.get('original_name', name)}")
        out.append(f"{pad}{ret} {name}({', '.join(params)}) {{")
        rs = stmt.get("renamed_symbols", {})
        if rs:
            out.append(("    " * (level + 1)) + f"// renamed_symbols: {rs}")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}}")
        return out
    if k == "ClassDef":
        name = stmt.get("name", "Class")
        out.append(f"{pad}// [{sp}] class original={stmt.get('original_name', name)}")
        out.append(f"{pad}struct {name} {{")
        for s in stmt.get("body", []):
            out.extend(_render_stmt(s, level + 1))
        out.append(f"{pad}}};")
        return out

    return _indent([f"// [{sp}] <unsupported stmt kind={k}>"], level)


def render_east_human_cpp(out_doc: dict[str, Any]) -> str:
    """Render whole EAST output into human-readable C++-style pseudo code."""
    lines: list[str] = []
    lines.append("// EAST Human View (C++-style pseudo source)")
    lines.append("// Generated by src/east.py")
    lines.append("")
    if not out_doc.get("ok", False):
        err = out_doc.get("error", {})
        lines.append("/* EAST generation failed */")
        lines.append(f"// kind: {err.get('kind')}")
        lines.append(f"// message: {err.get('message')}")
        lines.append(f"// source_span: {err.get('source_span')}")
        lines.append(f"// hint: {err.get('hint')}")
        lines.append("")
        return "\n".join(lines) + "\n"

    east = out_doc["east"]
    lines.append(f"namespace east_view /* source: {east.get('source_path')} */ {{")
    lines.append("")
    rs = east.get("renamed_symbols", {})
    if rs:
        lines.append("    // renamed_symbols")
        for k, v in rs.items():
            lines.append(f"    //   {k} -> {v}")
        lines.append("")

    lines.append("    // module body")
    for s in east.get("body", []):
        lines.extend(_render_stmt(s, 1))
    lines.append("")

    lines.append("    // main guard body")
    lines.append("    int64 __east_main_guard() {")
    for s in east.get("main_guard_body", []):
        lines.extend(_render_stmt(s, 2))
    lines.append("        return 0;")
    lines.append("    }")
    lines.append("")
    lines.append("} // namespace east_view")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for EAST JSON/human-view generation."""
    parser = argparse.ArgumentParser(description="Convert Python source into EAST JSON")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("-o", "--output", help="Output EAST JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--human-output", help="Output human-readable C++-style EAST path")
    parser.add_argument("--parser-backend", choices=["python_ast", "self_hosted"], default="python_ast", help="Parser backend")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east = convert_path(input_path, parser_backend=args.parser_backend)
    except SyntaxError as exc:
        err = {
            "kind": "unsupported_syntax",
            "message": str(exc),
            "source_span": {
                "lineno": exc.lineno,
                "col": exc.offset,
                "end_lineno": exc.end_lineno,
                "end_col": exc.end_offset,
            },
            "hint": "Fix Python syntax errors before EAST conversion.",
        }
        out = {"ok": False, "error": err}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1
    except EastBuildError as exc:
        out = {"ok": False, "error": exc.to_payload()}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1

    out = {"ok": True, "east": east}
    payload = _dump_json(out, pretty=args.pretty)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.human_output:
        human_path = Path(args.human_output)
        human_path.parent.mkdir(parents=True, exist_ok=True)
        human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

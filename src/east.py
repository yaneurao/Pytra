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
    if node is None:
        return {"lineno": None, "col": None, "end_lineno": None, "end_col": None}
    return {
        "lineno": getattr(node, "lineno", None),
        "col": getattr(node, "col_offset", None),
        "end_lineno": getattr(node, "end_lineno", None),
        "end_col": getattr(node, "end_col_offset", None),
    }


def is_main_guard(stmt: ast.stmt) -> bool:
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
    if ann is None:
        return None
    if isinstance(ann, ast.Name):
        float_aliases = {"float32", "float64"}
        if ann.id == "int":
            return "int64"
        if ann.id in INT_TYPES:
            return ann.id
        if ann.id in float_aliases:
            return "float"
        if ann.id in {"float", "bool", "str", "bytes", "bytearray", "Path"}:
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
        self.arg_names = set(arg_names)
        self.mutable: set[str] = set()

    def _mark_if_arg(self, node: ast.expr) -> None:
        if isinstance(node, ast.Name) and node.id in self.arg_names:
            self.mutable.add(node.id)

    def visit_Assign(self, node: ast.Assign) -> Any:
        for t in node.targets:
            self._mark_mutation_target(t)
        self.generic_visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        self._mark_mutation_target(node.target)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        self._mark_mutation_target(node.target)
        if node.value is not None:
            self.generic_visit(node.value)

    def visit_Call(self, node: ast.Call) -> Any:
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
    RESERVED = {"main", "py_main", "__pytra_main"}

    def __init__(self, source: str, filename: str) -> None:
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
        if isinstance(stmt, ast.FunctionDef):
            return self._function(stmt)
        if isinstance(stmt, ast.ClassDef):
            self.current_class_stack.append(stmt.name)
            out = {
                "kind": "ClassDef",
                "name": self._renamed(stmt.name),
                "original_name": stmt.name,
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
            if isinstance(target, ast.Name):
                self._bind_name_type(target.id, value["resolved_type"], stmt)
            return {
                "kind": "Assign",
                "source_span": span_of(stmt),
                "target": self._expr(target),
                "value": value,
            }
        if isinstance(stmt, ast.AugAssign):
            target_expr = self._expr(stmt.target)
            value_expr = self._expr(stmt.value)
            if isinstance(stmt.target, ast.Name):
                current = self._lookup_name_type(stmt.target.id)
                rhs_t = value_expr["resolved_type"]
                if current is not None and self._is_numeric_type(current) and self._is_numeric_type(rhs_t):
                    self._bind_name_type(stmt.target.id, "float" if "float" in {current, rhs_t} else current, stmt)
            return {
                "kind": "AugAssign",
                "source_span": span_of(stmt),
                "target": target_expr,
                "op": type(stmt.op).__name__,
                "value": value_expr,
            }
        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Attribute):
                value = self._expr(stmt.value) if stmt.value is not None else None
                ann_ty = annotation_to_type(stmt.annotation)
                if ann_ty is None:
                    raise self._error("unsupported_syntax", "unsupported type annotation", stmt.annotation, "Use supported Python-style annotations.")
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
            value = self._expr(stmt.value) if stmt.value is not None else None
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
            return {
                "kind": "Import",
                "source_span": span_of(stmt),
                "names": [{"name": a.name, "asname": a.asname} for a in stmt.names],
            }
        if isinstance(stmt, ast.ImportFrom):
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
        return {
            "kind": "ExceptHandler",
            "source_span": span_of(h),
            "type": self._expr(h.type) if h.type is not None else None,
            "name": h.name,
            "body": [self._stmt(s) for s in h.body],
        }

    def _function(self, fn: ast.FunctionDef) -> dict[str, Any]:
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
        resolved_type, casts = self._resolve_expr_type(expr)
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
            return {
                "func": self._expr_maybe(expr.func),
                "args": [self._expr_maybe(a) for a in expr.args],
                "keywords": [
                    {"arg": kw.arg, "value": self._expr_maybe(kw.value)}
                    for kw in expr.keywords
                ],
            }
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
            return {
                "left": self._expr_maybe(expr.left),
                "ops": [type(o).__name__ for o in expr.ops],
                "comparators": [self._expr_maybe(c) for c in expr.comparators],
            }
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
            else:
                payload["slice"] = self._expr_maybe(expr.slice)
            return payload
        if isinstance(expr, ast.JoinedStr):
            values: list[dict[str, Any]] = []
            for part in expr.values:
                if isinstance(part, ast.Constant):
                    values.append({"kind": "Constant", "value": part.value})
                elif isinstance(part, ast.FormattedValue):
                    values.append({"kind": "FormattedValue", "value": self._expr_maybe(part.value)})
            return {"values": values}
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
            return {"elt": self._expr_maybe(expr.elt), "generators": gens}
        return {}

    def _resolve_expr_type(self, expr: ast.expr) -> tuple[str, list[dict[str, Any]]]:
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
                return "float", []
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
                    if self._is_int_type(lt):
                        casts.append({"on": "left", "from": lt, "to": "float", "reason": "numeric_promotion"})
                    if self._is_int_type(rt):
                        casts.append({"on": "right", "from": rt, "to": "float", "reason": "numeric_promotion"})
                    return "float", casts
            if isinstance(expr.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.FloorDiv)):
                if lt == "str" and rt == "str" and isinstance(expr.op, ast.Add):
                    return "str", []
                if self._is_numeric_type(lt) and self._is_numeric_type(rt):
                    if lt != rt:
                        if self._is_int_type(lt):
                            casts.append({"on": "left", "from": lt, "to": "float", "reason": "numeric_promotion"})
                        if self._is_int_type(rt):
                            casts.append({"on": "right", "from": rt, "to": "float", "reason": "numeric_promotion"})
                        return "float", casts
                    return lt, []
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
                return "float", [
                    {"on": "body", "from": bt, "to": "float", "reason": "ifexp_numeric_promotion"},
                    {"on": "orelse", "from": ot, "to": "float", "reason": "ifexp_numeric_promotion"},
                ]
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
                return "float", []
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
        if isinstance(expr.func, ast.Name):
            fn = expr.func.id
            if fn == "int":
                return "int64", []
            if fn in {"float", "bool", "str", "bytes", "bytearray"}:
                return fn, []
            if fn == "len":
                return "int64", []
            if fn == "range":
                return "list[int64]", []
            if fn == "Path":
                return "Path", []
            if fn in {"min", "max"}:
                if len(expr.args) == 0:
                    raise self._error("inference_failure", f"{fn} requires at least one argument", expr, f"Pass at least one argument to {fn}().")
                ts = [self._resolve_expr_type(a)[0] for a in expr.args]
                return self._unify_types(ts, expr), []
            if fn == "round":
                return "float", []
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
                    return "float", []
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
        if isinstance(expr, ast.Name) and len(self.arg_usage_stack) > 0:
            usage = self.arg_usage_stack[-1].get(expr.id)
            if usage == "readonly":
                return "readonly_ref"
            if usage == "mutable":
                return "mutable_ref"
        return "value"

    def _lookup_name_type(self, name: str) -> str | None:
        for env in reversed(self.type_env_stack):
            if name in env:
                return env[name]
        return None

    def _bind_name_type(self, name: str, new_type: str, node: ast.AST) -> None:
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
        if t1 == t2:
            return True
        if "unknown" in {t1, t2}:
            return True
        return self._is_numeric_type(t1) and self._is_numeric_type(t2)

    def _unify_types(self, types: list[str], node: ast.AST) -> str:
        uniq = sorted(set(types))
        if len(uniq) == 1:
            return uniq[0]
        if all(self._is_int_type(t) for t in uniq):
            has_signed = any(t.startswith("int") for t in uniq)
            return "int64" if has_signed else "uint64"
        if all(self._is_numeric_type(t) for t in uniq):
            return "float"
        raise self._error("inference_failure", f"ambiguous types: {uniq}", node, "Add explicit annotation/cast to make the type unique.")

    def _iter_element_type(self, iterable_type: str) -> str | None:
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
        if iterable_type == "bytes" or iterable_type == "bytearray":
            return "uint8"
        if iterable_type == "unknown":
            return "unknown"
        return None

    def _is_int_type(self, t: str) -> bool:
        return t in INT_TYPES

    def _is_numeric_type(self, t: str) -> bool:
        return self._is_int_type(t) or t == "float"

    def _lookup_method_return_type(self, class_name: str, method: str) -> str | None:
        cur: str | None = class_name
        while cur is not None:
            methods = self.class_method_return_types.get(cur, {})
            if method in methods:
                return methods[method]
            cur = self.class_base.get(cur)
        return None

    def _lookup_field_type(self, class_name: str, field: str) -> str | None:
        cur: str | None = class_name
        while cur is not None:
            fields = self.class_field_types.get(cur, {})
            if field in fields:
                return fields[field]
            cur = self.class_base.get(cur)
        return None

    def _parse_range_iter(self, expr: ast.expr) -> tuple[ast.expr, ast.expr, ast.expr] | None:
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
        return self.renamed_symbols.get(name, name)

    def _error(self, kind: str, message: str, node: ast.AST | None, hint: str) -> EastBuildError:
        return EastBuildError(kind=kind, message=message, source_span=span_of(node), hint=hint)


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    return EastBuilder(source=source, filename=filename).build()


def convert_path(input_path: Path) -> dict[str, Any]:
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east(source, str(input_path))


def _dump_json(obj: dict[str, Any], *, pretty: bool) -> str:
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _indent(lines: list[str], level: int = 1) -> list[str]:
    prefix = "    " * level
    return [prefix + ln if ln else "" for ln in lines]


def _fmt_span(span: dict[str, Any] | None) -> str:
    if not span:
        return "?:?"
    ln = span.get("lineno")
    col = span.get("col")
    if ln is None or col is None:
        return "?:?"
    return f"{ln}:{col}"


def _render_expr(expr: dict[str, Any] | None) -> str:
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
    if expr is None:
        return "/* none */"
    rep = expr.get("repr")
    if rep is None:
        return f"<{expr.get('kind', 'Expr')}>"
    return rep


def _cpp_type_name(east_type: str | None) -> str:
    if east_type is None:
        return "auto"
    if east_type in INT_TYPES | {"float", "bool", "str", "Path", "bytes", "bytearray", "Exception", "None"}:
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
    parser = argparse.ArgumentParser(description="Convert Python source into EAST JSON")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("-o", "--output", help="Output EAST JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--human-output", help="Output human-readable C++-style EAST path")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east = convert_path(input_path)
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

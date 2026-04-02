"""EAST3 -> Scala source emitter.

Initial scaffold for the toolchain2 Scala backend.
This file intentionally supports only a narrow bootstrap subset so the
backend can be wired incrementally under `docs/ja/todo/java.md`.
"""

from __future__ import annotations

from pathlib import Path

from pytra.std.json import JsonVal

from toolchain2.emit.common.code_emitter import RuntimeMapping, load_runtime_mapping
from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.emit.scala.types import _safe_scala_ident
from toolchain2.emit.scala.types import scala_type


class ScalaRenderer(CommonRenderer):
    def __init__(self, mapping: RuntimeMapping) -> None:
        super().__init__("scala")
        self.mapping = mapping

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        module_id = self._str(east3_doc, "module_id")
        if module_id == "":
            meta = east3_doc.get("meta")
            if isinstance(meta, dict):
                module_id = self._str(meta, "module_id")
        object_name = _safe_scala_ident(module_id.replace(".", "_") if module_id != "" else "Main")
        self._emit("import scala.collection.mutable")
        self._emit_blank()
        self._emit("object " + object_name + " {")
        self.state.indent_level += 1
        body = self._list(east3_doc, "body")
        if len(body) == 0:
            self._emit("// bootstrap scaffold")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")
        return self.finish()

    def _emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            raise RuntimeError("scala emitter: stmt node must be dict")
        kind = self._str(node, "kind")
        if kind == "Pass":
            self._emit("()")
            return
        if kind == "AnnAssign":
            target = node.get("target")
            target_name = _safe_scala_ident(self._str(target, "id"))
            decl_type = self._str(node, "decl_type")
            value = self._emit_expr(node.get("value"))
            self._emit("val " + target_name + ": " + scala_type(decl_type) + " = " + value)
            return
        if kind == "Assign":
            target = node.get("target")
            target_name = _safe_scala_ident(self._str(target, "id"))
            value = self._emit_expr(node.get("value"))
            self._emit("var " + target_name + " = " + value)
            return
        if kind == "ImportFrom":
            module_name = self._str(node, "module")
            self._emit("// import from " + module_name)
            return
        if kind == "Import":
            self._emit("// import")
            return
        if kind == "FunctionDef":
            self._emit_function_def(node)
            return
        if kind == "ForCore":
            self._emit_for_core(node)
            return
        if kind == "If":
            test = self._emit_expr(node.get("test"))
            self._emit("if (" + test + ") {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            orelse = self._list(node, "orelse")
            if len(orelse) == 0:
                self._emit("}")
            else:
                self._emit("} else {")
                self.state.indent_level += 1
                for stmt in orelse:
                    self._emit_stmt(stmt)
                self.state.indent_level -= 1
                self._emit("}")
            return
        if kind == "While":
            test = self._emit_expr(node.get("test"))
            self._emit("while (" + test + ") {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
            return
        if kind == "AugAssign":
            target = self._emit_expr(node.get("target"))
            value = self._emit_expr(node.get("value"))
            op = self._str(node, "op")
            op_text = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/"}.get(op, op)
            self._emit(target + " = " + target + " " + op_text + " " + value)
            return
        if kind == "Return":
            value = node.get("value")
            if isinstance(value, dict):
                self._emit("return " + self._emit_expr(value))
            else:
                self._emit("return ()")
            return
        if kind == "Expr":
            self._emit(self._emit_expr(node.get("value")))
            return
        raise RuntimeError("scala emitter: unsupported stmt kind: " + kind)

    def _emit_function_def(self, node: dict[str, JsonVal]) -> None:
        name = _safe_scala_ident(self._str(node, "name"))
        arg_order = self._list(node, "arg_order")
        arg_types = node.get("arg_types")
        arg_type_map = arg_types if isinstance(arg_types, dict) else {}
        params: list[str] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            params.append(_safe_scala_ident(arg) + ": " + scala_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
        return_type = scala_type(self._str(node, "return_type"))
        self._emit("def " + name + "(" + ", ".join(params) + "): " + return_type + " = {")
        self.state.indent_level += 1
        body = self._list(node, "body")
        if len(body) == 0:
            self._emit("()")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")

    def _for_target_name(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            return "item"
        name = self._str(node, "id")
        if name == "":
            return "item"
        return _safe_scala_ident(name)

    def _emit_for_core(self, node: dict[str, JsonVal]) -> None:
        target_node = node.get("target_plan")
        if target_node is None:
            target_node = node.get("target")
        target_name = self._for_target_name(target_node)
        iter_plan = node.get("iter_plan")
        body = self._list(node, "body")
        if isinstance(iter_plan, dict) and self._str(iter_plan, "kind") == "StaticRangeForPlan":
            start = self._emit_expr(iter_plan.get("start"))
            stop = self._emit_expr(iter_plan.get("stop"))
            step_node = iter_plan.get("step")
            step = self._emit_expr(step_node) if isinstance(step_node, dict) else "1L"
            idx_name = "_idx_" + target_name
            descending = self._str(iter_plan, "range_mode") == "descending"
            cmp_op = ">" if descending else "<"
            update = idx_name + " = " + idx_name + (" - " if descending else " + ") + step.replace("-", "")
            self._emit("var " + idx_name + " = " + start)
            self._emit("while (" + idx_name + " " + cmp_op + " " + stop + ") {")
            self.state.indent_level += 1
            self._emit("val " + target_name + " = " + idx_name)
            for stmt in body:
                self._emit_stmt(stmt)
            self._emit(update)
            self.state.indent_level -= 1
            self._emit("}")
            return
        iter_expr = "Nil"
        if isinstance(iter_plan, dict) and self._str(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_expr = self._emit_expr(iter_plan.get("iter_expr"))
        elif isinstance(node.get("iter"), dict):
            iter_expr = self._emit_expr(node.get("iter"))
        self._emit("for (" + target_name + " <- " + iter_expr + ") {")
        self.state.indent_level += 1
        for stmt in body:
            self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")

    def _emit_expr(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            return "null"
        kind = self._str(node, "kind")
        if kind == "Constant":
            value = node.get("value")
            if value is None:
                return "null"
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, int) and not isinstance(value, bool):
                return str(value) + "L"
            if isinstance(value, float):
                return repr(value)
            if isinstance(value, str):
                return self._quote_string(value)
        if kind == "Name":
            return _safe_scala_ident(self._str(node, "id"))
        if kind == "Attribute":
            owner = self._emit_expr(node.get("value"))
            return owner + "." + _safe_scala_ident(self._str(node, "attr"))
        if kind == "Subscript":
            owner = self._emit_expr(node.get("value"))
            index = self._emit_expr(node.get("slice"))
            return owner + "(" + index + ")"
        if kind == "List":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutable.ArrayBuffer(" + ", ".join(elems) + ")"
        if kind == "Unbox" or kind == "Box":
            return self._emit_expr(node.get("value"))
        if kind == "Call":
            func = node.get("func")
            func_name = self._emit_expr(func)
            args = [self._emit_expr(arg) for arg in self._list(node, "args")]
            return func_name + "(" + ", ".join(args) + ")"
        if kind == "BinOp":
            left = self._emit_expr(node.get("left"))
            right = self._emit_expr(node.get("right"))
            op = self._str(node, "op")
            op_text = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/"}.get(op, op)
            return left + " " + op_text + " " + right
        if kind == "Compare":
            left = self._emit_expr(node.get("left"))
            comparators = self._list(node, "comparators")
            ops = self._list(node, "ops")
            if len(comparators) == 1 and len(ops) == 1:
                right = self._emit_expr(comparators[0])
                op = ops[0] if isinstance(ops[0], str) else self._str(ops[0], "kind")
                op_text = {"Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">="}.get(op, op)
                return left + " " + op_text + " " + right
        if kind == "UnaryOp":
            operand = self._emit_expr(node.get("operand"))
            op = self._str(node, "op")
            if op == "Not":
                return "!" + operand
            if op == "USub":
                return "-" + operand
        raise RuntimeError("scala emitter: unsupported expr kind: " + kind)


def emit_scala_module(east3_doc: dict[str, JsonVal]) -> str:
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "scala" / "mapping.json"
    renderer = ScalaRenderer(load_runtime_mapping(mapping_path))
    return renderer.render_module(east3_doc)


__all__ = ["emit_scala_module"]

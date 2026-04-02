"""EAST3 -> Kotlin source emitter.

Initial scaffold for the toolchain2 Kotlin backend.
This intentionally supports only a narrow bootstrap subset.
"""

from __future__ import annotations

from pathlib import Path

from pytra.std.json import JsonVal

from toolchain2.emit.common.code_emitter import RuntimeMapping, load_runtime_mapping
from toolchain2.emit.common.common_renderer import CommonRenderer
from toolchain2.emit.kotlin.types import _safe_kotlin_ident
from toolchain2.emit.kotlin.types import kotlin_type
from toolchain2.emit.kotlin.types import kotlin_zero_value


class KotlinRenderer(CommonRenderer):
    def __init__(self, mapping: RuntimeMapping) -> None:
        super().__init__("kotlin")
        self.mapping = mapping
        self.current_class_name: str | None = None
        self.import_symbols: dict[str, str] = {}
        self.module_function_names: set[str] = set()
        self.local_function_aliases: dict[str, str] = {}

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        module_id = self._str(east3_doc, "module_id")
        meta = east3_doc.get("meta")
        if module_id == "":
            if isinstance(meta, dict):
                module_id = self._str(meta, "module_id")
        self.import_symbols = {}
        if isinstance(meta, dict):
            import_symbols = meta.get("import_symbols")
            if isinstance(import_symbols, dict):
                for local_name, spec in import_symbols.items():
                    if isinstance(local_name, str) and isinstance(spec, dict):
                        mod = self._str(spec, "module")
                        name = self._str(spec, "name")
                        if mod != "" and name != "":
                            self.import_symbols[local_name] = _safe_kotlin_ident(mod.replace(".", "_")) + "." + _safe_kotlin_ident(name)
        self.module_function_names = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") in ("FunctionDef", "ClosureDef")
        }
        self.local_function_aliases = {}
        for emitted_name in self.module_function_names:
            if emitted_name.startswith("__pytra_") and len(emitted_name) > len("__pytra_"):
                self.local_function_aliases[emitted_name[len("__pytra_"):]] = emitted_name
        is_entry = False
        if isinstance(meta, dict):
            emit_context = meta.get("emit_context")
            if isinstance(emit_context, dict):
                is_entry = bool(emit_context.get("is_entry"))
            if not is_entry:
                is_entry = bool(meta.get("is_entry"))
        object_name = _safe_kotlin_ident(module_id.replace(".", "_") if module_id != "" else "Main")
        self._emit("object " + object_name + " {")
        self.state.indent_level += 1
        body = self._list(east3_doc, "body")
        main_guard_body = self._list(east3_doc, "main_guard_body")
        if len(body) == 0:
            self._emit("// bootstrap scaffold")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        if len(main_guard_body) > 0:
            self._emit("@JvmStatic")
            self._emit("fun main(args: Array<String>) {")
            self.state.indent_level += 1
            for stmt in main_guard_body:
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
        elif is_entry:
            self._emit("@JvmStatic")
            self._emit("fun main(args: Array<String>) {")
            self.state.indent_level += 1
            self._emit("_case_main()")
            self.state.indent_level -= 1
            self._emit("}")
        self.state.indent_level -= 1
        self._emit("}")
        return self.finish()

    def _emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            raise RuntimeError("kotlin emitter: stmt node must be dict")
        kind = self._str(node, "kind")
        if kind == "Pass":
            self._emit("Unit")
            return
        if kind == "AnnAssign":
            target = node.get("target")
            target_name = _safe_kotlin_ident(self._str(target, "id"))
            decl_type = self._str(node, "decl_type")
            value = self._emit_expr(node.get("value"))
            self._emit("val " + target_name + ": " + kotlin_type(decl_type) + " = " + value)
            return
        if kind == "Assign":
            target = node.get("target")
            value = self._emit_expr(node.get("value"))
            if isinstance(target, dict) and self._str(target, "kind") == "Attribute":
                self._emit(self._emit_expr(target) + " = " + value)
                return
            target_name = _safe_kotlin_ident(self._str(target, "id"))
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
        if kind == "ClosureDef":
            self._emit_function_def(node, is_method=self.current_class_name is not None)
            return
        if kind == "ClassDef":
            self._emit_class_def(node)
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
                self._emit("return Unit")
            return
        if kind == "Expr":
            self._emit(self._emit_expr(node.get("value")))
            return
        if kind == "Raise":
            exc = node.get("exc")
            message = self._emit_expr(exc) if isinstance(exc, dict) else "\"raise\""
            self._emit("throw RuntimeException(" + message + ".toString())")
            return
        if kind == "Try":
            self._emit("try {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            handlers = self._list(node, "handlers")
            if len(handlers) == 0:
                self._emit("} finally {")
            else:
                self._emit("} catch (_: Throwable) {")
                self.state.indent_level += 1
                for handler in handlers:
                    if isinstance(handler, dict):
                        for stmt in self._list(handler, "body"):
                            self._emit_stmt(stmt)
                self.state.indent_level -= 1
                self._emit("} finally {")
            self.state.indent_level += 1
            for stmt in self._list(node, "finalbody"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
            return
        raise RuntimeError("kotlin emitter: unsupported stmt kind: " + kind)

    def _emit_function_def(self, node: dict[str, JsonVal], is_method: bool = False) -> None:
        name = _safe_kotlin_ident(self._str(node, "name"))
        arg_order = self._list(node, "arg_order")
        arg_types = node.get("arg_types")
        arg_type_map = arg_types if isinstance(arg_types, dict) else {}
        params: list[str] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if is_method and arg == "self":
                continue
            params.append(_safe_kotlin_ident(arg) + ": " + kotlin_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
        return_type = kotlin_type(self._str(node, "return_type"))
        self._emit("fun " + name + "(" + ", ".join(params) + "): " + return_type + " {")
        self.state.indent_level += 1
        body = self._list(node, "body")
        if len(body) == 0:
            self._emit("Unit")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")

    def _emit_class_def(self, node: dict[str, JsonVal]) -> None:
        class_name = _safe_kotlin_ident(self._str(node, "name"))
        prev_class_name = self.current_class_name
        self.current_class_name = class_name
        self._emit("class " + class_name + " {")
        self.state.indent_level += 1
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = self._str(stmt, "kind")
            if kind == "AnnAssign":
                target = stmt.get("target")
                field_name = _safe_kotlin_ident(self._str(target, "id"))
                decl_type = self._str(stmt, "decl_type")
                value_node = stmt.get("value")
                value = self._emit_expr(value_node) if isinstance(value_node, dict) else kotlin_zero_value(decl_type)
                self._emit("var " + field_name + ": " + kotlin_type(decl_type) + " = " + value)
                continue
            self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")
        self.current_class_name = prev_class_name

    def _for_target_name(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            return "item"
        name = self._str(node, "id")
        if name == "":
            return "item"
        return _safe_kotlin_ident(name)

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
        iter_expr = "emptyList<Any?>()"
        if isinstance(iter_plan, dict) and self._str(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_expr = self._emit_expr(iter_plan.get("iter_expr"))
        elif isinstance(node.get("iter"), dict):
            iter_expr = self._emit_expr(node.get("iter"))
        self._emit("for (" + target_name + " in " + iter_expr + ") {")
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
            ident = self._str(node, "id")
            if ident == "self" and self.current_class_name is not None:
                return "this"
            if ident in self.import_symbols:
                return self.import_symbols[ident]
            if ident in self.local_function_aliases:
                return _safe_kotlin_ident(self.local_function_aliases[ident])
            return _safe_kotlin_ident(ident)
        if kind == "Attribute":
            owner = self._emit_expr(node.get("value"))
            return owner + "." + _safe_kotlin_ident(self._str(node, "attr"))
        if kind == "Subscript":
            owner = self._emit_expr(node.get("value"))
            slice_node = node.get("slice")
            if isinstance(slice_node, dict) and self._str(slice_node, "kind") == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                lower = self._emit_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._emit_expr(upper_node) if isinstance(upper_node, dict) else owner + ".size"
                return owner + ".slice(" + lower + " until " + upper + ")"
            index = self._emit_expr(slice_node)
            return owner + "[" + index + "]"
        if kind == "List":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutableListOf(" + ", ".join(elems) + ")"
        if kind == "Tuple":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutableListOf(" + ", ".join(elems) + ")"
        if kind == "Dict":
            keys = self._list(node, "keys")
            values = self._list(node, "values")
            pairs: list[str] = []
            for key_node, value_node in zip(keys, values):
                pairs.append(self._emit_expr(key_node) + " to " + self._emit_expr(value_node))
            return "linkedMapOf(" + ", ".join(pairs) + ")"
        if kind == "Unbox" or kind == "Box":
            return self._emit_expr(node.get("value"))
        if kind == "BoolOp":
            op = " && " if self._str(node, "op") == "And" else " || "
            values = [self._emit_expr(elem) for elem in self._list(node, "values")]
            return "(" + op.join(values) + ")"
        if kind == "IfExp":
            test = self._emit_expr(node.get("test"))
            body = self._emit_expr(node.get("body"))
            orelse = self._emit_expr(node.get("orelse"))
            return "(if (" + test + ") " + body + " else " + orelse + ")"
        if kind == "IsInstance":
            value = self._emit_expr(node.get("value"))
            expected = self._emit_expr(node.get("expected_type_id"))
            return "pytraIsInstance(" + value + ", " + expected + ")"
        if kind == "ObjTypeId":
            value = self._emit_expr(node.get("value"))
            return "pyTidRuntimeTypeId(" + value + ")"
        if kind == "IsSubtype":
            actual = self._emit_expr(node.get("actual_type_id"))
            expected = self._emit_expr(node.get("expected_type_id"))
            return "pyTidIsSubtype(" + actual + ", " + expected + ")"
        if kind == "Call":
            func = node.get("func")
            func_name = self._emit_expr(func)
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                mapped = self.mapping.calls.get(func_id)
                if isinstance(mapped, str) and mapped != "":
                    func_name = mapped
            args: list[str] = []
            for arg in self._list(node, "args"):
                if isinstance(arg, dict) and self._str(arg, "kind") == "Name":
                    arg_id = self._str(arg, "id")
                    resolved_type = self._str(arg, "resolved_type")
                    if arg_id in self.module_function_names or resolved_type.startswith("callable[") or resolved_type.startswith("Callable["):
                        args.append("{ " + _safe_kotlin_ident(arg_id) + "() }")
                        continue
                args.append(self._emit_expr(arg))
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
                op_text = {
                    "Eq": "==",
                    "NotEq": "!=",
                    "Lt": "<",
                    "LtE": "<=",
                    "Gt": ">",
                    "GtE": ">=",
                    "Is": "==",
                    "IsNot": "!=",
                }.get(op, op)
                return left + " " + op_text + " " + right
        if kind == "UnaryOp":
            operand = self._emit_expr(node.get("operand"))
            op = self._str(node, "op")
            if op == "Not":
                return "!" + operand
            if op == "USub":
                return "-" + operand
        raise RuntimeError("kotlin emitter: unsupported expr kind: " + kind)


def emit_kotlin_module(east3_doc: dict[str, JsonVal]) -> str:
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "kotlin" / "mapping.json"
    renderer = KotlinRenderer(load_runtime_mapping(mapping_path))
    return renderer.render_module(east3_doc)


__all__ = ["emit_kotlin_module"]

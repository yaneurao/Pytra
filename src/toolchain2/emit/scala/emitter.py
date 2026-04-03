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
from toolchain2.emit.scala.types import scala_zero_value


class ScalaRenderer(CommonRenderer):
    def __init__(self, mapping: RuntimeMapping) -> None:
        super().__init__("scala")
        self.mapping = mapping
        self.current_class_name: str | None = None
        self.import_symbols: dict[str, str] = {}
        self.module_function_names: set[str] = set()
        self.local_function_aliases: dict[str, str] = {}
        self.module_class_names: set[str] = set()
        self.class_has_init: dict[str, bool] = {}
        self._tmp_counter = 0

    def _collect_class_fields(self, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = []
        field_types = node.get("field_types")
        if isinstance(field_types, dict) and len(field_types) > 0:
            for field_name, field_type in field_types.items():
                if isinstance(field_name, str) and isinstance(field_type, str):
                    fields.append((field_name, field_type))
            return fields
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            if self._str(stmt, "kind") != "FunctionDef" or self._str(stmt, "name") != "__init__":
                continue
            for init_stmt in self._list(stmt, "body"):
                if not isinstance(init_stmt, dict):
                    continue
                if self._str(init_stmt, "kind") not in ("Assign", "AnnAssign"):
                    continue
                target = init_stmt.get("target")
                if not isinstance(target, dict) or self._str(target, "kind") != "Attribute":
                    continue
                owner = target.get("value")
                if not isinstance(owner, dict) or self._str(owner, "id") != "self":
                    continue
                attr = self._str(target, "attr")
                decl_type = self._str(init_stmt, "decl_type")
                if decl_type == "":
                    decl_type = self._str(init_stmt, "resolved_type")
                if decl_type == "":
                    decl_type = "Any"
                fields.append((attr, decl_type))
        return fields

    def _next_tmp(self, prefix: str) -> str:
        self._tmp_counter += 1
        return prefix + str(self._tmp_counter)

    def _emit_store_target(self, target: JsonVal, value_code: str) -> None:
        if not isinstance(target, dict):
            raise RuntimeError("scala emitter: store target must be dict")
        kind = self._str(target, "kind")
        if kind == "Name":
            self._emit(_safe_scala_ident(self._str(target, "id")) + " = " + value_code)
            return
        if kind == "Attribute":
            self._emit(self._emit_expr(target) + " = " + value_code)
            return
        raise RuntimeError("scala emitter: unsupported store target: " + kind)

    def _emit_boolop_value_expr(self, values: list[JsonVal], is_and: bool) -> str:
        if len(values) == 0:
            return "false" if is_and else "null"
        expr = self._emit_expr(values[-1])
        for value in reversed(values[:-1]):
            tmp_name = self._next_tmp("__pytra_boolop_")
            current = self._emit_expr(value)
            if is_and:
                expr = "{ val " + tmp_name + " = " + current + "; if (__pytra_truthy(" + tmp_name + ")) " + expr + " else " + tmp_name + " }"
            else:
                expr = "{ val " + tmp_name + " = " + current + "; if (__pytra_truthy(" + tmp_name + ")) " + tmp_name + " else " + expr + " }"
        return expr

    def _emit_comp_loops(self, generators: list[JsonVal], index: int, leaf_stmt: str) -> str:
        if index >= len(generators):
            return leaf_stmt
        gen = generators[index]
        if not isinstance(gen, dict):
            return leaf_stmt
        target = gen.get("target")
        target_name = self._for_target_name(target)
        iter_expr = self._emit_expr(gen.get("iter"))
        inner = self._emit_comp_loops(generators, index + 1, leaf_stmt)
        filters = [self._emit_expr(cond) for cond in self._list(gen, "ifs") if isinstance(cond, dict)]
        if len(filters) > 0:
            inner = "if (" + " && ".join(filters) + ") { " + inner + " }"
        return "for (" + target_name + " <- " + iter_expr + ") { " + inner + " }"

    def _emit_comp_expr(self, node: dict[str, JsonVal], result_type: str, init_expr: str, leaf_stmt: str) -> str:
        result_name = self._next_tmp("__pytra_comp_")
        body = self._emit_comp_loops(self._list(node, "generators"), 0, leaf_stmt.replace("__RESULT__", result_name))
        return "{ val " + result_name + ": " + result_type + " = " + init_expr + "; " + body + "; " + result_name + " }"

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
                            if mod == "pytra.std.math":
                                self.import_symbols[local_name] = "math_native." + _safe_scala_ident(name)
                                continue
                            self.import_symbols[local_name] = _safe_scala_ident(mod.replace(".", "_")) + "." + _safe_scala_ident(name)
        self.module_function_names = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") in ("FunctionDef", "ClosureDef")
        }
        self.module_class_names = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") == "ClassDef"
        }
        self.class_has_init = {}
        for stmt in self._list(east3_doc, "body"):
            if not isinstance(stmt, dict) or self._str(stmt, "kind") != "ClassDef":
                continue
            class_name = self._str(stmt, "name")
            self.class_has_init[class_name] = any(
                isinstance(item, dict)
                and self._str(item, "kind") in ("FunctionDef", "ClosureDef")
                and self._str(item, "name") == "__init__"
                for item in self._list(stmt, "body")
            )
        self.local_function_aliases = {}
        self._tmp_counter = 0
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
        object_name = _safe_scala_ident(module_id.replace(".", "_") if module_id != "" else "Main")
        self._emit("import scala.collection.mutable")
        self._emit_blank()
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
            self._emit("def main(args: Array[String]): Unit = {")
            self.state.indent_level += 1
            for stmt in main_guard_body:
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
        elif is_entry:
            self._emit("def main(args: Array[String]): Unit = {")
            self.state.indent_level += 1
            self._emit("_case_main()")
            self.state.indent_level -= 1
            self._emit("}")
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
            decl_type = self._str(node, "decl_type")
            value = self._emit_expr(node.get("value"))
            if isinstance(target, dict) and self._str(target, "kind") == "Attribute":
                self._emit(self._emit_expr(target) + " = " + value)
                return
            target_name = _safe_scala_ident(self._str(target, "id"))
            self._emit("var " + target_name + ": " + scala_type(decl_type) + " = " + value)
            return
        if kind == "Assign":
            target = node.get("target")
            value = self._emit_expr(node.get("value"))
            if isinstance(target, dict) and self._str(target, "kind") == "Attribute":
                self._emit(self._emit_expr(target) + " = " + value)
                return
            target_name = _safe_scala_ident(self._str(target, "id"))
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
        if kind == "Swap":
            left = node.get("left")
            right = node.get("right")
            left_code = self._emit_expr(left)
            right_code = self._emit_expr(right)
            tmp_name = "__pytra_swap_tmp"
            tmp_type = "Any"
            if isinstance(left, dict):
                tmp_type = scala_type(self._str(left, "resolved_type"))
            self._emit("val " + tmp_name + ": " + tmp_type + " = " + left_code)
            self._emit_store_target(left, right_code)
            self._emit_store_target(right, tmp_name)
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
        if kind == "Raise":
            exc = node.get("exc")
            message = "\"raise\""
            if isinstance(exc, dict) and self._str(exc, "kind") == "Call":
                args = self._list(exc, "args")
                if len(args) >= 1 and isinstance(args[0], dict):
                    message = self._emit_expr(args[0])
                else:
                    message = self._emit_expr(exc)
            elif isinstance(exc, dict):
                message = self._emit_expr(exc)
            self._emit("throw new RuntimeException(String.valueOf(" + message + "))")
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
                self._emit("} catch {")
                self.state.indent_level += 1
                self._emit("case _ : Throwable =>")
                self.state.indent_level += 1
                for handler in handlers:
                    if isinstance(handler, dict):
                        for stmt in self._list(handler, "body"):
                            if isinstance(stmt, dict) and self._str(stmt, "kind") == "Assign":
                                target = stmt.get("target")
                                if isinstance(target, dict) and self._str(target, "kind") in ("Name", "Attribute"):
                                    self._emit_store_target(target, self._emit_expr(stmt.get("value")))
                                    continue
                            self._emit_stmt(stmt)
                self.state.indent_level -= 2
                self._emit("} finally {")
            self.state.indent_level += 1
            for stmt in self._list(node, "finalbody"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
            return
        raise RuntimeError("scala emitter: unsupported stmt kind: " + kind)

    def _emit_function_def(self, node: dict[str, JsonVal], is_method: bool = False) -> None:
        name = _safe_scala_ident(self._str(node, "name"))
        arg_order = self._list(node, "arg_order")
        arg_types = node.get("arg_types")
        arg_type_map = arg_types if isinstance(arg_types, dict) else {}
        params: list[str] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if is_method and arg == "self":
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

    def _emit_class_def(self, node: dict[str, JsonVal]) -> None:
        class_name = _safe_scala_ident(self._str(node, "name"))
        prev_class_name = self.current_class_name
        self.current_class_name = class_name
        instance_fields = self._collect_class_fields(node)
        static_fields: list[tuple[str, str, str]] = []
        self._emit("class " + class_name + " {")
        self.state.indent_level += 1
        seen_instance_fields: set[str] = set()
        for field_name, decl_type in instance_fields:
            safe_field_name = _safe_scala_ident(field_name)
            if safe_field_name in seen_instance_fields:
                continue
            seen_instance_fields.add(safe_field_name)
            self._emit("var " + safe_field_name + ": " + scala_type(decl_type) + " = " + scala_zero_value(decl_type))
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = self._str(stmt, "kind")
            if kind == "AnnAssign":
                target = stmt.get("target")
                field_name = _safe_scala_ident(self._str(target, "id"))
                decl_type = self._str(stmt, "decl_type")
                value_node = stmt.get("value")
                if isinstance(value_node, dict):
                    value = self._emit_expr(value_node)
                    static_fields.append((field_name, decl_type, value))
                continue
            if kind == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and self._str(target, "kind") == "Name":
                    field_name = _safe_scala_ident(self._str(target, "id"))
                    decl_type = self._str(stmt, "decl_type")
                    if decl_type == "":
                        decl_type = self._str(target, "resolved_type")
                    value_node = stmt.get("value")
                    value = self._emit_expr(value_node) if isinstance(value_node, dict) else scala_zero_value(decl_type)
                    static_fields.append((field_name, decl_type, value))
                    continue
            self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")
        if len(static_fields) > 0:
            self._emit("object " + class_name + " {")
            self.state.indent_level += 1
            for field_name, decl_type, value in static_fields:
                self._emit("var " + field_name + ": " + scala_type(decl_type) + " = " + value)
            self.state.indent_level -= 1
            self._emit("}")
        self.current_class_name = prev_class_name

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
            ident = self._str(node, "id")
            if ident == "self" and self.current_class_name is not None:
                return "this"
            if ident in self.import_symbols:
                return self.import_symbols[ident]
            if ident in self.local_function_aliases:
                return _safe_scala_ident(self.local_function_aliases[ident])
            return _safe_scala_ident(ident)
        if kind == "Attribute":
            owner = self._emit_expr(node.get("value"))
            return owner + "." + _safe_scala_ident(self._str(node, "attr"))
        if kind == "Subscript":
            owner = self._emit_expr(node.get("value"))
            slice_node = node.get("slice")
            if isinstance(slice_node, dict) and self._str(slice_node, "kind") == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                lower = self._emit_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._emit_expr(upper_node) if isinstance(upper_node, dict) else owner + ".length"
                return owner + ".slice((" + lower + ").toInt, (" + upper + ").toInt)"
            index = self._emit_expr(slice_node)
            result_type = scala_type(self._str(node, "resolved_type"))
            return "__pytra_get_index(" + owner + ", " + index + ").asInstanceOf[" + result_type + "]"
        if kind == "List":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutable.ArrayBuffer(" + ", ".join(elems) + ")"
        if kind == "Tuple":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutable.ArrayBuffer(" + ", ".join(elems) + ")"
        if kind == "Set":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutable.LinkedHashSet(" + ", ".join(elems) + ")"
        if kind == "ListComp":
            elt_code = self._emit_expr(node.get("elt"))
            return self._emit_comp_expr(
                node,
                scala_type(self._str(node, "resolved_type")),
                "mutable.ArrayBuffer()",
                "__RESULT__ += " + elt_code,
            )
        if kind == "Lambda":
            arg_order = self._list(node, "arg_order")
            arg_types = node.get("arg_types")
            arg_type_map = arg_types if isinstance(arg_types, dict) else {}
            params: list[str] = []
            for arg in arg_order:
                if isinstance(arg, str):
                    arg_type = arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"
                    params.append(_safe_scala_ident(arg) + ": " + scala_type(arg_type))
            return "(" + ", ".join(params) + ") => " + self._emit_expr(node.get("body"))
        if kind == "Dict":
            pairs: list[str] = []
            entries = node.get("entries")
            if isinstance(entries, list) and len(entries) > 0:
                for entry in entries:
                    if isinstance(entry, dict):
                        key_node = entry.get("key")
                        value_node = entry.get("value")
                        if isinstance(key_node, dict) and isinstance(value_node, dict):
                            pairs.append("(" + self._emit_expr(key_node) + ", " + self._emit_expr(value_node) + ")")
            else:
                keys = self._list(node, "keys")
                values = self._list(node, "values")
                for key_node, value_node in zip(keys, values):
                    pairs.append("(" + self._emit_expr(key_node) + ", " + self._emit_expr(value_node) + ")")
            return "mutable.LinkedHashMap(" + ", ".join(pairs) + ")"
        if kind == "SetComp":
            elt_code = self._emit_expr(node.get("elt"))
            return self._emit_comp_expr(
                node,
                scala_type(self._str(node, "resolved_type")),
                "mutable.LinkedHashSet()",
                "__RESULT__ += " + elt_code,
            )
        if kind == "DictComp":
            key_code = self._emit_expr(node.get("key"))
            value_code = self._emit_expr(node.get("value"))
            return self._emit_comp_expr(
                node,
                scala_type(self._str(node, "resolved_type")),
                "mutable.LinkedHashMap()",
                "__RESULT__(" + key_code + ") = " + value_code,
            )
        if kind == "Unbox" or kind == "Box":
            return self._emit_expr(node.get("value"))
        if kind == "BoolOp":
            return self._emit_boolop_value_expr(self._list(node, "values"), self._str(node, "op") == "And")
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
            if isinstance(func, dict) and self._str(func, "kind") == "Attribute":
                owner_node = func.get("value")
                attr = self._str(func, "attr")
                owner_expr = self._emit_expr(owner_node)
                owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                arg_nodes = self._list(node, "args")
                if owner_type in ("str", "string"):
                    if attr == "join" and len(arg_nodes) == 1:
                        return "__pytra_join(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "split":
                        sep = self._emit_expr(arg_nodes[0]) if len(arg_nodes) >= 1 else "null"
                        return "__pytra_split(" + owner_expr + ", " + sep + ")"
                    if attr == "strip":
                        return "__pytra_strip(" + owner_expr + ")"
                    if attr == "lstrip":
                        return "__pytra_lstrip(" + owner_expr + ")"
                    if attr == "rstrip":
                        return "__pytra_rstrip(" + owner_expr + ")"
                    if attr == "replace" and len(arg_nodes) >= 2:
                        return "__pytra_replace(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                    if attr == "startswith" and len(arg_nodes) >= 1:
                        return "__pytra_startswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "endswith" and len(arg_nodes) >= 1:
                        return "__pytra_endswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "upper":
                        return "__pytra_upper(" + owner_expr + ")"
                    if attr == "lower":
                        return "__pytra_lower(" + owner_expr + ")"
                    if attr == "find" and len(arg_nodes) >= 1:
                        return "__pytra_find(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "count" and len(arg_nodes) >= 1:
                        return "__pytra_count_substr(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                if owner_type.startswith("dict[") and attr == "get" and len(arg_nodes) == 2:
                    return owner_expr + ".getOrElse(" + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                if owner_type.startswith("dict["):
                    if attr == "keys":
                        return "__pytra_dict_keys(" + owner_expr + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    if attr == "values":
                        return "__pytra_dict_values(" + owner_expr + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    if attr == "items":
                        return "__pytra_dict_items(" + owner_expr + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    if attr == "pop" and len(arg_nodes) >= 1:
                        key_expr = self._emit_expr(arg_nodes[0])
                        value_type = "Any"
                        owner_rt = owner_type
                        if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
                            inner = owner_rt[5:-1]
                            parts = [part.strip() for part in inner.split(",", 1)]
                            if len(parts) == 2:
                                value_type = scala_type(parts[1])
                        return "{ val __pytra_pop_key = " + key_expr + "; val __pytra_pop_val = " + owner_expr + "(__pytra_pop_key); " + owner_expr + ".remove(__pytra_pop_key); __pytra_pop_val.asInstanceOf[" + value_type + "] }"
                    if attr == "setdefault" and len(arg_nodes) >= 2:
                        key_expr = self._emit_expr(arg_nodes[0])
                        default_expr = self._emit_expr(arg_nodes[1])
                        return owner_expr + ".getOrElseUpdate(" + key_expr + ", " + default_expr + ")"
                if owner_type.startswith("list[") or owner_type in ("list", "bytearray", "bytes"):
                    if attr == "sort":
                        return "{ val __pytra_sorted = " + owner_expr + ".sorted; " + owner_expr + ".clear(); " + owner_expr + " ++= __pytra_sorted; () }"
                    if attr == "reverse":
                        return "{ val __pytra_reversed = " + owner_expr + ".reverse; " + owner_expr + ".clear(); " + owner_expr + " ++= __pytra_reversed; () }"
                    if attr == "pop":
                        if len(arg_nodes) == 0:
                            return "{ val __pytra_idx = " + owner_expr + ".size - 1; val __pytra_val = " + owner_expr + "(__pytra_idx); " + owner_expr + ".remove(__pytra_idx); __pytra_val }"
                        idx_expr = self._emit_expr(arg_nodes[0])
                        return "{ val __pytra_idx = __pytra_index(__pytra_int(" + idx_expr + "), " + owner_expr + ".size.toLong).toInt; val __pytra_val = " + owner_expr + "(__pytra_idx); " + owner_expr + ".remove(__pytra_idx); __pytra_val }"
                if owner_type.startswith("set[") or owner_type == "set":
                    if attr == "discard" and len(arg_nodes) >= 1:
                        return "{ " + owner_expr + ".subtractOne(" + self._emit_expr(arg_nodes[0]) + "); () }"
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                call_result_type = self._str(node, "resolved_type")
                mapped = self.mapping.calls.get(func_id)
                if isinstance(mapped, str) and mapped != "":
                    if func_id == "set":
                        return mapped + "(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    func_name = mapped
                elif func_id in self.module_class_names or (call_result_type != "" and call_result_type == func_id):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    class_name = func_name if "." in func_name else _safe_scala_ident(func_id)
                    tmp_name = "__pytra_obj"
                    if self.class_has_init.get(func_id, True):
                        return "{ val " + tmp_name + " = new " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
                    return "new " + class_name + "(" + ", ".join(ctor_args) + ")"
            args: list[str] = []
            for arg in self._list(node, "args"):
                if isinstance(arg, dict) and self._str(arg, "kind") == "Name":
                    arg_id = self._str(arg, "id")
                    if arg_id in self.module_function_names:
                        args.append(_safe_scala_ident(arg_id) + " _")
                        continue
                args.append(self._emit_expr(arg))
            if isinstance(func, dict) and self._str(func, "kind") == "Lambda":
                return "(" + func_name + ")(" + ", ".join(args) + ")"
            return func_name + "(" + ", ".join(args) + ")"
        if kind == "BinOp":
            left = self._emit_expr(node.get("left"))
            right = self._emit_expr(node.get("right"))
            op = self._str(node, "op")
            left_type = self._str(node.get("left"), "resolved_type") if isinstance(node.get("left"), dict) else ""
            if op == "Mult" and (left_type.startswith("list[") or left_type == "list"):
                return "__pytra_list_repeat(" + left + ", " + right + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
            if op == "BitAnd":
                return "((" + left + ") & (" + right + "))"
            if op == "BitOr":
                return "((" + left + ") | (" + right + "))"
            if op == "BitXor":
                return "((" + left + ") ^ (" + right + "))"
            if op == "LShift":
                return "((" + left + ") << (" + right + ").toInt)"
            if op == "RShift":
                return "((" + left + ") >> (" + right + ").toInt)"
            op_text = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%"}.get(op, op)
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
                if op == "In":
                    return "__pytra_contains(" + right + ", " + left + ")"
                if op == "NotIn":
                    return "!__pytra_contains(" + right + ", " + left + ")"
                return left + " " + op_text + " " + right
        if kind == "UnaryOp":
            operand = self._emit_expr(node.get("operand"))
            op = self._str(node, "op")
            if op == "Not":
                return "!" + operand
            if op == "USub":
                return "-" + operand
            if op == "Invert":
                return "~(" + operand + ")"
        raise RuntimeError("scala emitter: unsupported expr kind: " + kind)


def emit_scala_module(east3_doc: dict[str, JsonVal]) -> str:
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "scala" / "mapping.json"
    renderer = ScalaRenderer(load_runtime_mapping(mapping_path))
    return renderer.render_module(east3_doc)


__all__ = ["emit_scala_module"]

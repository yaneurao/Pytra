"""EAST3 -> Scala source emitter.

Initial scaffold for the toolchain2 Scala backend.
This file intentionally supports only a narrow bootstrap subset so the
backend can be wired incrementally under `docs/ja/todo/java.md`.
"""

from __future__ import annotations

from pathlib import Path

from pytra.std.json import JsonVal

from toolchain.emit.common.code_emitter import (
    RuntimeMapping,
    build_import_alias_map,
    build_runtime_import_map,
    load_runtime_mapping,
    resolve_runtime_symbol_name,
    should_skip_module,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.emit.scala.types import _safe_scala_ident
from toolchain.emit.scala.types import scala_type
from toolchain.emit.scala.types import scala_zero_value


class ScalaRenderer(CommonRenderer):
    def __init__(self, mapping: RuntimeMapping) -> None:
        super().__init__("scala")
        self.mapping = mapping
        self.current_class_name: str | None = None
        self.import_symbols: dict[str, str] = {}
        self.import_modules: dict[str, str] = {}
        self.import_alias_modules: dict[str, str] = {}
        self.runtime_imports: dict[str, str] = {}
        self.module_function_names: set[str] = set()
        self.module_function_varargs: dict[str, tuple[int, str]] = {}
        self.local_function_aliases: dict[str, str] = {}
        self.module_class_names: set[str] = set()
        self.class_property_names: dict[str, set[str]] = {}
        self.class_method_names: dict[str, set[str]] = {}
        self.enum_like_classes: set[str] = set()
        self.current_class_base: str | None = None
        self.class_has_init: dict[str, bool] = {}
        self.class_without_init: set[str] = set()
        self.exception_class_names: set[str] = set()
        self.local_decl_stack: list[set[str]] = []
        self.local_type_stack: list[dict[str, str]] = []
        self._tmp_counter = 0

    def _mapping_call(self, key: str) -> str:
        mapped = self.mapping.calls.get(key)
        return mapped if isinstance(mapped, str) else ""

    def _module_namespace_expr(self, module_id: str) -> str:
        expr = self.mapping.module_namespace_exprs.get(module_id, "")
        return expr if isinstance(expr, str) else ""

    def _is_exception_name(self, name: str) -> bool:
        return name in self.mapping.exception_types or name in self.exception_class_names

    def _exception_class_name(self, name: str) -> str:
        if name == "":
            return "Throwable"
        if self._is_exception_name(name):
            return _safe_scala_ident(name)
        return _safe_scala_ident(name)

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

    def _has_decorator(self, node: dict[str, JsonVal], name: str) -> bool:
        return any(isinstance(dec, str) and dec == name for dec in self._list(node, "decorators"))

    def _implements_traits(self, node: dict[str, JsonVal]) -> list[str]:
        traits: list[str] = []
        for dec in self._list(node, "decorators"):
            if not isinstance(dec, str) or not dec.startswith("implements(") or not dec.endswith(")"):
                continue
            inner = dec[len("implements("):-1]
            for part in inner.split(","):
                name = part.strip()
                if name != "":
                    traits.append(_safe_scala_ident(name))
        return traits

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
        if kind == "Subscript":
            owner = target.get("value")
            index = target.get("slice")
            self._emit("__pytra_set_index(" + self._emit_expr(owner) + ", " + self._emit_expr(index) + ", " + value_code + ")")
            return
        raise RuntimeError("scala emitter: unsupported store target: " + kind)

    def _should_declare_name(self, target_name: str, requested: bool) -> bool:
        if len(self.local_decl_stack) == 0:
            return requested
        scope = self.local_decl_stack[-1]
        if target_name in scope:
            return False
        scope.add(target_name)
        return True

    def _record_local_type(self, name: str, resolved_type: str) -> None:
        if len(self.local_type_stack) == 0 or resolved_type == "":
            return
        self.local_type_stack[-1][name] = resolved_type

    def _lookup_local_type(self, name: str) -> str:
        for scope in reversed(self.local_type_stack):
            if name in scope:
                return scope[name]
        return ""

    def _callable_type(self, resolved_type: str) -> str:
        if resolved_type in ("Callable", "callable") or resolved_type.startswith("callable[") or resolved_type.startswith("Callable["):
            return resolved_type
        if "|" not in resolved_type:
            return ""
        parts = [part.strip() for part in resolved_type.split("|")]
        callable_parts = [
            part for part in parts
            if part in ("Callable", "callable") or part.startswith("callable[") or part.startswith("Callable[")
        ]
        none_parts = [part for part in parts if part in ("None", "none")]
        if len(callable_parts) == 1 and len(callable_parts) + len(none_parts) == len(parts):
            return callable_parts[0]
        return ""

    def _emit_call_parts(self, args: list[JsonVal]) -> list[str]:
        parts: list[str] = []
        for arg in args:
            if isinstance(arg, dict) and self._str(arg, "kind") == "Name":
                arg_id = self._str(arg, "id")
                if arg_id in self.module_function_names:
                    parts.append(_safe_scala_ident(arg_id) + " _")
                    continue
            parts.append(self._emit_expr(arg))
        return parts

    def _with_hoisted_names(self, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = self._str(stmt, "kind")
            target = stmt.get("target")
            if not isinstance(target, dict) or self._str(target, "kind") not in ("Name", "NameTarget"):
                continue
            name = self._str(target, "id")
            if name == "" or name in seen:
                continue
            decl_type = ""
            if kind == "AnnAssign":
                decl_type = self._str(stmt, "decl_type") or self._str(stmt, "annotation") or self._str(target, "resolved_type")
            elif kind == "Assign" and bool(stmt.get("declare")):
                decl_type = self._str(stmt, "decl_type") or self._str(target, "resolved_type")
            if decl_type == "":
                continue
            seen.add(name)
            out.append((name, decl_type))
        return out

    def _try_hoisted_names(self, node: dict[str, JsonVal]) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = self._str(stmt, "kind")
            target = stmt.get("target")
            if not isinstance(target, dict) or self._str(target, "kind") not in ("Name", "NameTarget"):
                continue
            name = self._str(target, "id")
            if name == "" or name in seen:
                continue
            decl_type = ""
            if kind == "AnnAssign":
                decl_type = self._str(stmt, "decl_type") or self._str(stmt, "annotation") or self._str(target, "resolved_type")
            elif kind == "Assign" and bool(stmt.get("declare")):
                decl_type = self._str(stmt, "decl_type") or self._str(target, "resolved_type")
            if decl_type == "":
                continue
            seen.add(name)
            out.append((name, decl_type))
        return out

    def _emit_keyword_parts(self, keywords: list[JsonVal]) -> list[str]:
        parts: list[str] = []
        for keyword in keywords:
            if not isinstance(keyword, dict):
                continue
            name = self._str(keyword, "arg")
            value = keyword.get("value")
            if name == "" or not isinstance(value, dict):
                continue
            parts.append(_safe_scala_ident(name) + " = " + self._emit_expr(value))
        return parts

    def _emit_argparse_add_argument_parts(self, args: list[JsonVal], keywords: list[JsonVal]) -> list[str]:
        parts = self._emit_call_parts(args)
        kw_map: dict[str, str] = {}
        for keyword in keywords:
            if not isinstance(keyword, dict):
                continue
            name = self._str(keyword, "arg")
            value = keyword.get("value")
            if name == "" or not isinstance(value, dict):
                continue
            kw_map[name] = self._emit_expr(value)
        while len(parts) < 4:
            parts.append("null")
        parts.append(kw_map.get("action", "\"\""))
        parts.append(kw_map.get("choices", "null"))
        parts.append(kw_map.get("default", "null"))
        parts.append(kw_map.get("help_text", "\"\""))
        return parts

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
        iter_expr = self._emit_expr(gen.get("iter"))
        iter_node = gen.get("iter")
        iter_type = self._str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
        if iter_type in ("str", "string"):
            iter_expr = "__pytra_as_list(" + iter_expr + ")"
        inner = self._emit_comp_loops(generators, index + 1, leaf_stmt)
        filters = [self._emit_expr(cond) for cond in self._list(gen, "ifs") if isinstance(cond, dict)]
        if len(filters) > 0:
            inner = "if (" + " && ".join(filters) + ") { " + inner + " }"
        loop_var = self._for_target_name(target)
        prelude: list[str] = []
        if isinstance(target, dict) and self._str(target, "kind") == "Tuple":
            loop_var = self._next_tmp("__pytra_item_")
            tuple_expr = "__pytra_as_list(" + loop_var + ")"
            for idx2, elem in enumerate(self._list(target, "elements")):
                if not isinstance(elem, dict) or self._str(elem, "kind") != "Name":
                    continue
                elem_name = _safe_scala_ident(self._str(elem, "id"))
                elem_type = scala_type(self._str(elem, "resolved_type"))
                prelude.append("val " + elem_name + " = " + tuple_expr + "(" + str(idx2) + ").asInstanceOf[" + elem_type + "]")
        if len(prelude) > 0:
            inner = " ".join(line + "; " for line in prelude) + inner
        return "for (" + loop_var + " <- " + iter_expr + ") { " + inner + " }"

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
        self.import_modules = {}
        self.import_alias_modules = build_import_alias_map(meta if isinstance(meta, dict) else {})
        self.runtime_imports = build_runtime_import_map(meta if isinstance(meta, dict) else {}, self.mapping)
        if isinstance(meta, dict):
            import_modules = meta.get("import_modules")
            if isinstance(import_modules, dict):
                for local_name, mod in import_modules.items():
                    if isinstance(local_name, str) and isinstance(mod, str) and mod != "":
                        self.import_modules[local_name] = mod
            import_symbols = meta.get("import_symbols")
            if isinstance(import_symbols, dict):
                for local_name, spec in import_symbols.items():
                    if isinstance(local_name, str) and isinstance(spec, dict):
                        mod = self._str(spec, "module")
                        name = self._str(spec, "name")
                        if mod == "":
                            continue
                        if name == "":
                            self.import_modules[local_name] = mod
                            continue
                        std_mod = "pytra.std." + mod if "." not in mod else ""
                        if std_mod != "" and std_mod + "." + name in self.mapping.calls:
                            self.runtime_imports[local_name] = self.mapping.calls[std_mod + "." + name]
                            continue
                        if should_skip_module(mod, self.mapping) or should_skip_module(mod + "." + name, self.mapping):
                            resolved = self.mapping.calls.get(mod + "." + name, "")
                            if not isinstance(resolved, str) or resolved == "":
                                resolved = resolve_runtime_symbol_name(name, self.mapping, module_id=mod)
                            if isinstance(resolved, str) and resolved != "":
                                self.runtime_imports[local_name] = resolved
                                continue
                        namespace_expr = self._module_namespace_expr(mod)
                        if namespace_expr != "":
                            self.import_symbols[local_name] = namespace_expr + "." + _safe_scala_ident(name)
                            continue
                        self.import_symbols[local_name] = _safe_scala_ident(mod.replace(".", "_")) + "." + _safe_scala_ident(name)
        self.module_function_names = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") in ("FunctionDef", "ClosureDef")
        }
        self.module_function_varargs = {
            self._str(stmt, "name"): (len(self._list(stmt, "arg_order")), self._str(stmt, "vararg_name"))
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict)
            and self._str(stmt, "kind") in ("FunctionDef", "ClosureDef")
            and self._str(stmt, "vararg_name") != ""
        }
        self.module_class_names = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") == "ClassDef"
        }
        self.enum_like_classes = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") == "ClassDef" and self._str(stmt, "base") in ("IntEnum", "IntFlag")
        }
        self.class_has_init = {}
        self.class_without_init = set()
        self.exception_class_names = set()
        self.class_property_names = {}
        self.class_method_names = {}
        for stmt in self._list(east3_doc, "body"):
            if not isinstance(stmt, dict) or self._str(stmt, "kind") != "ClassDef":
                continue
            class_name = self._str(stmt, "name")
            if self._str(stmt, "base") in self.mapping.exception_types:
                self.exception_class_names.add(class_name)
            self.class_has_init[class_name] = any(
                isinstance(item, dict)
                and self._str(item, "kind") in ("FunctionDef", "ClosureDef")
                and self._str(item, "name") == "__init__"
                for item in self._list(stmt, "body")
            )
            if not self.class_has_init[class_name]:
                self.class_without_init.add(class_name)
            methods: set[str] = set()
            props: set[str] = set()
            for item in self._list(stmt, "body"):
                if not isinstance(item, dict) or self._str(item, "kind") not in ("FunctionDef", "ClosureDef"):
                    continue
                methods.add(self._str(item, "name"))
                for dec in self._list(item, "decorators"):
                    if isinstance(dec, str) and dec == "property":
                        props.add(self._str(item, "name"))
            self.class_method_names[class_name] = methods
            self.class_property_names[class_name] = props
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
        self._emit("import scala.util.control.NoStackTrace")
        self._emit_blank()
        self._emit("object " + object_name + " {")
        self.state.indent_level += 1
        self._emit("private object __pytra_continue_signal extends Throwable with NoStackTrace")
        self._emit_blank()
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
            if "main" in self.module_function_names:
                self._emit("main()")
            elif "_case_main" in self.module_function_names:
                self._emit("_case_main()")
            else:
                self._emit("()")
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
            if decl_type == "":
                decl_type = self._str(node, "resolved_type")
            if decl_type == "" and isinstance(target, dict):
                decl_type = self._str(target, "resolved_type")
            if decl_type == "":
                decl_type = "Any"
            if decl_type in self.enum_like_classes:
                decl_type = "int64"
            value_node = node.get("value")
            value = self._emit_expr(value_node) if isinstance(value_node, dict) else scala_zero_value(decl_type)
            if isinstance(target, dict) and self._str(target, "kind") in ("Attribute", "Subscript"):
                self._emit_store_target(target, value)
                return
            target_name = _safe_scala_ident(self._str(target, "id"))
            if self._should_declare_name(target_name, bool(node.get("declare"))):
                self._emit("var " + target_name + ": " + scala_type(decl_type) + " = " + value)
            else:
                self._emit(target_name + " = " + value)
            self._record_local_type(target_name, decl_type)
            return
        if kind == "Assign":
            target = node.get("target")
            value = self._emit_expr(node.get("value"))
            if isinstance(target, dict) and self._str(target, "kind") in ("Attribute", "Subscript"):
                self._emit_store_target(target, value)
                return
            target_name = _safe_scala_ident(self._str(target, "id"))
            if self._should_declare_name(target_name, bool(node.get("declare"))):
                self._emit("var " + target_name + " = " + value)
            else:
                self._emit(target_name + " = " + value)
            return
        if kind == "VarDecl":
            name = _safe_scala_ident(self._str(node, "name"))
            decl_type = self._str(node, "type")
            if decl_type == "":
                decl_type = self._str(node, "decl_type")
            if decl_type == "":
                decl_type = self._str(node, "resolved_type")
            if decl_type == "":
                decl_type = "Any"
            if decl_type in self.enum_like_classes:
                decl_type = "int64"
            if self._should_declare_name(name, True):
                self._emit("var " + name + ": " + scala_type(decl_type) + " = " + scala_zero_value(decl_type))
            self._record_local_type(name, decl_type)
            return
        if kind == "ImportFrom":
            module_name = self._str(node, "module")
            self._emit("// import from " + module_name)
            return
        if kind == "Import":
            self._emit("// import")
            return
        if kind == "TypeAlias":
            self._emit("// type alias")
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
            self._emit("if (__pytra_truthy(" + test + ")) {")
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
            self._emit("scala.util.control.Breaks.breakable {")
            self.state.indent_level += 1
            self._emit("while (__pytra_truthy(" + test + ")) {")
            self.state.indent_level += 1
            self._emit("try {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("} catch {")
            self.state.indent_level += 1
            self._emit("case _: __pytra_continue_signal.type => ()")
            self.state.indent_level -= 1
            self._emit("}")
            self.state.indent_level -= 1
            self._emit("}")
            self.state.indent_level -= 1
            self._emit("}")
            return
        if kind == "AugAssign":
            target_node = node.get("target")
            if isinstance(target_node, dict) and self._str(target_node, "kind") == "Name":
                target = _safe_scala_ident(self._str(target_node, "id"))
            else:
                target = self._emit_expr(target_node)
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
            value = node.get("value")
            if isinstance(value, dict) and self._str(value, "kind") == "Name":
                ident = self._str(value, "id")
                if ident == "continue":
                    self._emit("throw __pytra_continue_signal")
                    return
                if ident == "break":
                    self._emit("scala.util.control.Breaks.break()")
                    return
            self._emit(self._emit_expr(value))
            return
        if kind == "Raise":
            exc = node.get("exc")
            if exc is None:
                self._emit("throw __pytra_active_exc")
                return
            if isinstance(exc, dict):
                exc_type = self._str(exc, "resolved_type")
                if self._is_exception_name(exc_type):
                    self._emit("throw " + self._emit_expr(exc))
                    return
            message = "\"raise\""
            if isinstance(exc, dict) and self._str(exc, "kind") == "Call":
                func = exc.get("func")
                if isinstance(func, dict):
                    if self._str(func, "kind") == "Name" and self._is_exception_name(self._str(func, "id")):
                        self._emit("throw " + self._emit_expr(exc))
                        return
                    if self._str(func, "kind") == "Attribute" and self._is_exception_name(self._str(func, "attr")):
                        self._emit("throw " + self._emit_expr(exc))
                        return
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
            for hoisted_name, hoisted_type in self._try_hoisted_names(node):
                safe_name = _safe_scala_ident(hoisted_name)
                if len(self.local_decl_stack) > 0 and safe_name in self.local_decl_stack[-1]:
                    continue
                if len(self.local_decl_stack) > 0:
                    self.local_decl_stack[-1].add(safe_name)
                self._emit("var " + safe_name + ": " + scala_type(hoisted_type) + " = " + scala_zero_value(hoisted_type))
                self._record_local_type(safe_name, hoisted_type)
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
                for handler in handlers:
                    if not isinstance(handler, dict):
                        continue
                    type_node = handler.get("type")
                    catch_type = "Throwable"
                    if isinstance(type_node, dict):
                        catch_type = self._exception_class_name(self._str(type_node, "id"))
                    bound_name = _safe_scala_ident(self._str(handler, "name"))
                    raw_name = bound_name if bound_name != "" else "__pytraErr"
                    self._emit("case " + raw_name + ": " + catch_type + " =>")
                    self.state.indent_level += 1
                    self._emit("val __pytra_active_exc = " + raw_name)
                    for stmt in self._list(handler, "body"):
                        if isinstance(stmt, dict) and self._str(stmt, "kind") == "Assign":
                            target = stmt.get("target")
                            if isinstance(target, dict) and self._str(target, "kind") in ("Name", "Attribute"):
                                self._emit_store_target(target, self._emit_expr(stmt.get("value")))
                                continue
                        self._emit_stmt(stmt)
                    self.state.indent_level -= 1
                self.state.indent_level -= 1
                self._emit("} finally {")
            self.state.indent_level += 1
            for stmt in self._list(node, "finalbody"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("}")
            return
        if kind == "With":
            context_expr = node.get("context_expr")
            context_type = self._str(context_expr, "resolved_type") or "Any"
            scala_ctx_type = scala_type(context_type)
            comp_name = self._next_tmp("__pytra_with_ctx_")
            entered_name = self._next_tmp("__pytra_with_value_")
            self._emit("val " + comp_name + ": " + scala_ctx_type + " = " + self._emit_expr(context_expr))
            var_name = self._str(node, "var_name")
            if var_name != "":
                safe_name = _safe_scala_ident(var_name)
                if self._should_declare_name(safe_name, True):
                    self._emit("var " + safe_name + ": " + scala_ctx_type + " = " + comp_name + ".__enter__()")
                else:
                    self._emit(safe_name + " = " + comp_name + ".__enter__()")
                self._record_local_type(safe_name, context_type)
            else:
                self._emit("val " + entered_name + ": " + scala_ctx_type + " = " + comp_name + ".__enter__()")
            for hoisted_name, hoisted_type in self._with_hoisted_names(node):
                safe_name = _safe_scala_ident(hoisted_name)
                if len(self.local_decl_stack) > 0:
                    self.local_decl_stack[-1].add(safe_name)
                self._emit("var " + safe_name + ": " + scala_type(hoisted_type) + " = " + scala_zero_value(hoisted_type))
                self._record_local_type(safe_name, hoisted_type)
            self._emit("try {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("} finally {")
            self.state.indent_level += 1
            self._emit(comp_name + ".__exit__(null, null, null)")
            self.state.indent_level -= 1
            self._emit("}")
            return
        raise RuntimeError("scala emitter: unsupported stmt kind: " + kind)

    def _emit_function_def(self, node: dict[str, JsonVal], is_method: bool = False) -> None:
        name = _safe_scala_ident(self._str(node, "name"))
        arg_order = self._list(node, "arg_order")
        arg_types = node.get("arg_types")
        arg_type_map = arg_types if isinstance(arg_types, dict) else {}
        arg_usage = node.get("arg_usage")
        arg_usage_map = arg_usage if isinstance(arg_usage, dict) else {}
        vararg_name = self._str(node, "vararg_name")
        vararg_type = self._str(node, "vararg_type")
        decorators = self._list(node, "decorators")
        is_property = any(isinstance(d, str) and d == "property" for d in decorators)
        params: list[str] = []
        rebinding: list[tuple[str, str]] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if is_method and arg == "self":
                continue
            safe_arg = _safe_scala_ident(arg)
            param_name = safe_arg
            if isinstance(arg_usage_map.get(arg), str) and arg_usage_map.get(arg) == "reassigned":
                param_name = safe_arg + "__in"
                rebinding.append((safe_arg, param_name))
            params.append(param_name + ": " + scala_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
        if vararg_name != "":
            safe_vararg = _safe_scala_ident(vararg_name)
            params.append(safe_vararg + "__in: " + scala_type(vararg_type if vararg_type != "" else "Any") + "*")
        return_type = scala_type(self._str(node, "return_type"))
        method_prefix = ""
        base_methods = self.class_method_names.get(self.current_class_base or "", set())
        if is_method and self.current_class_base not in (None, "", "None", "object", "Obj") and name in base_methods:
            method_prefix = "override "
        sig = method_prefix + "def " + name
        if not (is_method and is_property):
            sig += "(" + ", ".join(params) + ")"
        sig += ": " + return_type + " = {"
        self._emit(sig)
        self.state.indent_level += 1
        scope_names = {_safe_scala_ident(arg) for arg in arg_order if isinstance(arg, str)}
        self.local_decl_stack.append(scope_names)
        self.local_type_stack.append({})
        for arg in arg_order:
            if isinstance(arg, str):
                arg_type = arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"
                self._record_local_type(_safe_scala_ident(arg), arg_type)
        if vararg_name != "":
            safe_vararg = _safe_scala_ident(vararg_name)
            self._emit("val " + safe_vararg + " = mutable.ArrayBuffer.from(" + safe_vararg + "__in)")
            self._record_local_type(safe_vararg, "list[" + (vararg_type if vararg_type != "" else "Any") + "]")
        for local_name, param_name in rebinding:
            self._emit("var " + local_name + " = " + param_name)
            self._record_local_type(local_name, self._lookup_local_type(param_name))
        body = self._list(node, "body")
        if len(body) == 0:
            self._emit("()")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        self.local_decl_stack.pop()
        self.local_type_stack.pop()
        self.state.indent_level -= 1
        self._emit("}")

    def _emit_class_def(self, node: dict[str, JsonVal]) -> None:
        class_name = _safe_scala_ident(self._str(node, "name"))
        base_name = self._str(node, "base")
        is_trait = self._has_decorator(node, "trait")
        implements_traits = self._implements_traits(node)
        prev_class_name = self.current_class_name
        prev_class_base = self.current_class_base
        self.current_class_name = class_name
        self.current_class_base = base_name
        if is_trait:
            trait_head = "trait " + class_name
            if base_name not in ("", "None", "object", "Obj"):
                trait_head += " extends " + _safe_scala_ident(base_name)
            self._emit(trait_head + " {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                if not isinstance(stmt, dict) or self._str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
                    continue
                name = _safe_scala_ident(self._str(stmt, "name"))
                arg_order = self._list(stmt, "arg_order")
                arg_types = stmt.get("arg_types")
                arg_type_map = arg_types if isinstance(arg_types, dict) else {}
                params: list[str] = []
                for arg in arg_order:
                    if not isinstance(arg, str) or arg == "self":
                        continue
                    params.append(_safe_scala_ident(arg) + ": " + scala_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
                return_type = scala_type(self._str(stmt, "return_type"))
                self._emit("def " + name + "(" + ", ".join(params) + "): " + return_type)
            self.state.indent_level -= 1
            self._emit("}")
            self.current_class_name = prev_class_name
            self.current_class_base = prev_class_base
            return
        instance_fields = self._collect_class_fields(node)
        static_fields: list[tuple[str, str, str]] = []
        static_methods: list[dict[str, JsonVal]] = []
        dataclass_fields: list[tuple[str, str, str | None]] = []
        is_dataclass = any(isinstance(dec, str) and dec == "dataclass" for dec in self._list(node, "decorators"))
        if is_dataclass:
            for stmt in self._list(node, "body"):
                if not isinstance(stmt, dict) or self._str(stmt, "kind") != "AnnAssign":
                    continue
                target = stmt.get("target")
                if not isinstance(target, dict) or self._str(target, "kind") != "Name":
                    continue
                field_name = _safe_scala_ident(self._str(target, "id"))
                decl_type = self._str(stmt, "decl_type") or self._str(stmt, "resolved_type") or self._str(target, "resolved_type") or "Any"
                value_node = stmt.get("value")
                default_value = self._emit_expr(value_node) if isinstance(value_node, dict) else None
                dataclass_fields.append((field_name, decl_type, default_value))
        dataclass_field_names = {field_name for field_name, _, _ in dataclass_fields}
        class_head = "class " + class_name
        if len(dataclass_fields) > 0:
            ctor_parts: list[str] = []
            for field_name, decl_type, default_value in dataclass_fields:
                part = "var " + field_name + ": " + scala_type(decl_type)
                if default_value is not None:
                    part += " = " + default_value
                ctor_parts.append(part)
            class_head += "(" + ", ".join(ctor_parts) + ")"
        if base_name not in ("", "None", "object", "Obj", "Enum", "IntEnum", "IntFlag"):
            class_head += " extends " + _safe_scala_ident(base_name)
            if len(implements_traits) > 0:
                class_head += " with " + " with ".join(implements_traits)
        elif len(implements_traits) > 0:
            class_head += " extends " + " with ".join(implements_traits)
        self._emit(class_head + " {")
        self.state.indent_level += 1
        seen_instance_fields: set[str] = set()
        for field_name, decl_type in instance_fields:
            safe_field_name = _safe_scala_ident(field_name)
            if safe_field_name in dataclass_field_names:
                continue
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
                if is_dataclass and isinstance(target, dict) and self._str(target, "kind") == "Name":
                    continue
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
            if kind in ("FunctionDef", "ClosureDef"):
                decorators = self._list(stmt, "decorators")
                if any(isinstance(dec, str) and dec == "staticmethod" for dec in decorators):
                    static_methods.append(stmt)
                    continue
            self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("}")
        if len(static_fields) > 0 or len(static_methods) > 0:
            self._emit("object " + class_name + " {")
            self.state.indent_level += 1
            for field_name, decl_type, value in static_fields:
                self._emit("var " + field_name + ": " + scala_type(decl_type) + " = " + value)
            for method in static_methods:
                self._emit_function_def(method, False)
            self.state.indent_level -= 1
            self._emit("}")
        self.current_class_name = prev_class_name
        self.current_class_base = prev_class_base

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
            idx_name = self._next_tmp("_idx_")
            descending = self._str(iter_plan, "range_mode") == "descending" or step.strip().startswith("-")
            cmp_op = ">" if descending else "<"
            update = idx_name + " = " + idx_name + " + (" + step + ")"
            self._emit("scala.util.control.Breaks.breakable {")
            self.state.indent_level += 1
            self._emit("var " + idx_name + " = " + start)
            self._emit("while (" + idx_name + " " + cmp_op + " " + stop + ") {")
            self.state.indent_level += 1
            self._emit("val " + target_name + " = " + idx_name)
            self._emit("try {")
            self.state.indent_level += 1
            for stmt in body:
                self._emit_stmt(stmt)
            self.state.indent_level -= 1
            self._emit("} catch {")
            self.state.indent_level += 1
            self._emit("case _: __pytra_continue_signal.type => ()")
            self.state.indent_level -= 1
            self._emit("}")
            self._emit(update)
            self.state.indent_level -= 1
            self._emit("}")
            self.state.indent_level -= 1
            self._emit("}")
            return
        iter_expr = "Nil"
        if isinstance(iter_plan, dict) and self._str(iter_plan, "kind") == "RuntimeIterForPlan":
            iter_expr = self._emit_expr(iter_plan.get("iter_expr"))
        elif isinstance(node.get("iter"), dict):
            iter_expr = self._emit_expr(node.get("iter"))
        iter_node = iter_plan.get("iter_expr") if isinstance(iter_plan, dict) else node.get("iter")
        iter_type = self._str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
        if iter_type in ("str", "string"):
            iter_expr = "__pytra_as_list(" + iter_expr + ")"
        if iter_type == "list" or iter_type.startswith("list["):
            iter_expr = "__pytra_as_list(" + iter_expr + ")"
        elif any(part.strip().startswith("list[") for part in iter_type.split("|")):
            iter_expr = "__pytra_as_list(" + iter_expr + ")"
        loop_var = target_name
        prelude: list[str] = []
        if isinstance(target_node, dict):
            resolved_target_type = self._str(target_node, "resolved_type")
            if resolved_target_type in ("", "unknown", "Any", "object"):
                if iter_type.startswith("list[") and iter_type.endswith("]"):
                    resolved_target_type = iter_type[5:-1]
                elif iter_type.startswith("tuple[") and iter_type.endswith("]"):
                    resolved_target_type = "Any"
                elif iter_type.startswith("set[") and iter_type.endswith("]"):
                    resolved_target_type = iter_type[4:-1]
            if resolved_target_type not in ("", "unknown", "Any", "object"):
                loop_var = self._next_tmp("__iter_tmp_")
                if loop_var != target_name:
                    prelude.append("val " + target_name + " = " + loop_var + ".asInstanceOf[" + scala_type(resolved_target_type) + "]")
            self._record_local_type(target_name, resolved_target_type if resolved_target_type != "" else "Any")
        self._emit("scala.util.control.Breaks.breakable {")
        self.state.indent_level += 1
        self._emit("for (" + loop_var + " <- " + iter_expr + ") {")
        self.state.indent_level += 1
        for line in prelude:
            self._emit(line)
        self._emit("try {")
        self.state.indent_level += 1
        for stmt in body:
            self._emit_stmt(stmt)
        self.state.indent_level -= 1
        self._emit("} catch {")
        self.state.indent_level += 1
        self._emit("case _: __pytra_continue_signal.type => ()")
        self.state.indent_level -= 1
        self._emit("}")
        self.state.indent_level -= 1
        self._emit("}")
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
            resolved_type = self._str(node, "resolved_type")
            local_resolved_type = self._lookup_local_type(_safe_scala_ident(ident))
            if local_resolved_type in ("str", "string") and resolved_type in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
                resolved_type = local_resolved_type
            if resolved_type in ("", "unknown"):
                resolved_type = local_resolved_type
            callable_type = self._callable_type(resolved_type)
            if ident == "self" and self.current_class_name is not None:
                return "this"
            if ident in self.runtime_imports:
                return self.runtime_imports[ident]
            if ident in self.import_symbols:
                import_path = self.import_symbols[ident]
                import_leaf = import_path.rsplit(".", 1)[-1]
                if self._is_exception_name(import_leaf):
                    return _safe_scala_ident(import_leaf)
                return import_path
            if ident in self.import_alias_modules:
                module_id = self.import_alias_modules[ident]
                namespace_expr = self._module_namespace_expr(module_id)
                if namespace_expr != "":
                    return namespace_expr
                return _safe_scala_ident(module_id.replace(".", "_"))
            if ident in self.local_function_aliases:
                if callable_type != "":
                    return _safe_scala_ident(self.local_function_aliases[ident])
                return _safe_scala_ident(self.local_function_aliases[ident])
            if ident in self.module_function_names and callable_type != "":
                return _safe_scala_ident(ident)
            rendered = _safe_scala_ident(ident)
            if resolved_type in self.enum_like_classes:
                return rendered
            rendered_type = scala_type(resolved_type)
            if resolved_type not in ("", "unknown", "Any", "object") and rendered_type != "Any":
                return rendered + ".asInstanceOf[" + rendered_type + "]"
            return rendered
        if kind == "Attribute":
            owner_node = node.get("value")
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Call":
                func = owner_node.get("func")
                if isinstance(func, dict) and self._str(func, "kind") == "Name" and self._str(func, "id") == "type" and self._str(node, "attr") == "__name__":
                    args = self._list(owner_node, "args")
                    arg_expr = self._emit_expr(args[0]) if len(args) > 0 else "null"
                    return "__pytra_type_name(" + arg_expr + ")"
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Call" and self._str(owner_node, "special_form") == "super":
                return "super." + _safe_scala_ident(self._str(node, "attr"))
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Name":
                owner_id = self._str(owner_node, "id")
                module_id = self.import_alias_modules.get(owner_id, "")
                attr = _safe_scala_ident(self._str(node, "attr"))
                if owner_id in self.module_class_names or owner_id in self.enum_like_classes:
                    return _safe_scala_ident(owner_id) + "." + attr
                if self._module_namespace_expr(module_id) != "" and self._is_exception_name(attr):
                    return attr
                namespace_expr = self._module_namespace_expr(module_id)
                if namespace_expr != "":
                    return namespace_expr + "." + attr
                qualified = self._str(node, "repr")
                if qualified != "" and qualified in self.mapping.calls:
                    return self.mapping.calls[qualified]
                if module_id != "" and should_skip_module(module_id, self.mapping):
                    resolved = resolve_runtime_symbol_name(
                        self._str(node, "attr"),
                        self.mapping,
                        module_id=module_id,
                        resolved_runtime_call=self._str(node, "resolved_runtime_call"),
                        runtime_call=self._str(node, "runtime_call"),
                    )
                    if resolved != "":
                        return resolved
                if module_id != "":
                    return _safe_scala_ident((module_id + "." + self._str(node, "attr")).replace(".", "_"))
            owner = self._emit_expr(owner_node)
            owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            attr = _safe_scala_ident(self._str(node, "attr"))
            if owner_type in self.class_property_names and attr in self.class_property_names.get(owner_type, set()):
                return owner + "." + attr
            return owner + "." + attr
        if kind == "Subscript":
            owner_node = node.get("value")
            owner = self._emit_expr(owner_node)
            owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            slice_node = node.get("slice")
            if isinstance(slice_node, dict) and self._str(slice_node, "kind") == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                lower = self._emit_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._emit_expr(upper_node) if isinstance(upper_node, dict) else "__pytra_len(" + owner + ")"
                if owner_type in ("str", "string"):
                    return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ").asInstanceOf[String]"
                return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
            index = self._emit_expr(slice_node)
            result_type = scala_type(self._str(node, "resolved_type"))
            return "__pytra_get_index(" + owner + ", " + index + ").asInstanceOf[" + result_type + "]"
        if kind == "List":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "mutable.ArrayBuffer(" + ", ".join(elems) + ")"
        if kind == "Tuple":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            return "__pytra_tuple(" + ", ".join(elems) + ")"
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
            value_code = self._emit_expr(node.get("value"))
            target = self._str(node, "target")
            resolved_type = self._str(node, "resolved_type")
            if self._callable_type(target) != "" or self._callable_type(resolved_type) != "":
                return value_code
            if target == "str":
                return "__pytra_str(" + value_code + ")"
            if target == "Obj":
                return value_code
            if target == "bool":
                return "__pytra_truthy(" + value_code + ")"
            if target in self.enum_like_classes or resolved_type in self.enum_like_classes:
                return "__pytra_int(" + value_code + ")"
            if target in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
                return "__pytra_int(" + value_code + ")"
            if target in ("float", "float32", "float64"):
                return "__pytra_float(" + value_code + ")"
            cast_type = scala_type(resolved_type if resolved_type != "" else target)
            if target.startswith("dict[") or target == "dict":
                return "__pytra_as_dict(" + value_code + ").asInstanceOf[" + cast_type + "]"
            if target.startswith("list[") or target in ("list", "tuple", "bytes", "bytearray"):
                return "__pytra_as_list(" + value_code + ").asInstanceOf[" + cast_type + "]"
            if target.startswith("set[") or target == "set":
                return "__pytra_set_new(" + value_code + ").asInstanceOf[" + cast_type + "]"
            if cast_type not in ("", "Any"):
                return value_code + ".asInstanceOf[" + cast_type + "]"
            return value_code
        if kind == "BoolOp":
            return self._emit_boolop_value_expr(self._list(node, "values"), self._str(node, "op") == "And")
        if kind == "IfExp":
            test = self._emit_expr(node.get("test"))
            body = self._emit_expr(node.get("body"))
            orelse = self._emit_expr(node.get("orelse"))
            return "(if (__pytra_truthy(" + test + ")) " + body + " else " + orelse + ")"
        if kind == "IsInstance":
            value = self._emit_expr(node.get("value"))
            expected = self._quote_string(self._str(node, "expected_type_name"))
            return "__pytra_is_instance(" + value + ", " + expected + ")"
        if kind == "ObjTypeId":
            value = self._emit_expr(node.get("value"))
            return "pyTidRuntimeTypeId(" + value + ")"
        if kind == "IsSubtype":
            actual = self._emit_expr(node.get("actual_type_id"))
            expected = self._emit_expr(node.get("expected_type_id"))
            return "pyTidIsSubtype(" + actual + ", " + expected + ")"
        if kind == "Call":
            runtime_module_id = self._str(node, "runtime_module_id")
            runtime_symbol = self._str(node, "runtime_symbol")
            runtime_adapter = self._str(node, "runtime_call_adapter_kind")
            if runtime_module_id == "pytra.std.math" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                return "math_native." + _safe_scala_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            if runtime_module_id == "pytra.std.time" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                return "time_native." + _safe_scala_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            if runtime_adapter == "extern_delegate" and runtime_module_id != "" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                if runtime_module_id == "pytra.std.math":
                    return "math_native." + _safe_scala_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
                if runtime_module_id == "pytra.std.time":
                    return "time_native." + _safe_scala_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            func = node.get("func")
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                early_func_id = self._str(func, "id")
                early_result_type = self._str(node, "resolved_type")
                if early_func_id != "" and not self._is_exception_name(early_func_id) and early_result_type == early_func_id and (early_func_id in self.module_class_names or early_func_id[:1].isupper()):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    class_name = _safe_scala_ident(early_func_id)
                    if early_func_id in self.class_without_init or not self.class_has_init.get(early_func_id, False):
                        return "new " + class_name + "(" + ", ".join(ctor_args) + ")"
                    tmp_name = "__pytra_obj"
                    return "{ val " + tmp_name + " = new " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
            func_name = self._emit_expr(func)
            func_is_named_function = False
            func_resolved_type = self._str(func, "resolved_type") if isinstance(func, dict) else ""
            local_callable_type = ""
            if isinstance(func, dict) and self._str(func, "kind") == "Name" and func_resolved_type in ("", "unknown"):
                local_callable_type = self._lookup_local_type(_safe_scala_ident(self._str(func, "id")))
                func_resolved_type = local_callable_type
            if isinstance(func, dict) and self._str(func, "kind") in ("Box", "Unbox"):
                local_callable_type = self._callable_type(func_resolved_type)
                if local_callable_type == "":
                    local_callable_type = self._callable_type(self._str(func, "target"))
                if local_callable_type != "":
                    func_resolved_type = local_callable_type
            if isinstance(func, dict) and self._str(func, "kind") == "Attribute":
                owner_node = func.get("value")
                attr = self._str(func, "attr")
                owner_expr = self._emit_expr(owner_node)
                owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                arg_nodes = self._list(node, "args")
                if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Name":
                    owner_id = self._str(owner_node, "id")
                    module_id = self.import_alias_modules.get(owner_id, "")
                    qualified = self._str(func, "repr")
                    keyword_nodes = self._list(node, "keywords")
                    if attr == "add_argument" and (self._str(node, "semantic_tag") == "stdlib.method.add_argument" or len(keyword_nodes) > 0):
                        call_parts = self._emit_argparse_add_argument_parts(arg_nodes, keyword_nodes)
                        return owner_expr + "." + _safe_scala_ident(attr) + "(" + ", ".join(call_parts) + ")"
                    if qualified != "" and qualified in self.mapping.calls:
                        call_parts = self._emit_call_parts(arg_nodes) + self._emit_keyword_parts(keyword_nodes)
                        return self.mapping.calls[qualified] + "(" + ", ".join(call_parts) + ")"
                    if module_id != "" and should_skip_module(module_id, self.mapping):
                        resolved = resolve_runtime_symbol_name(
                            attr,
                            self.mapping,
                            module_id=module_id,
                            resolved_runtime_call=self._str(node, "resolved_runtime_call"),
                            runtime_call=self._str(node, "runtime_call"),
                        )
                        if resolved != "":
                            call_parts = self._emit_call_parts(arg_nodes) + self._emit_keyword_parts(keyword_nodes)
                            return resolved + "(" + ", ".join(call_parts) + ")"
                resolved_method = resolve_runtime_symbol_name(
                    attr,
                    self.mapping,
                    module_id=self._str(node, "runtime_module_id"),
                    resolved_runtime_call=self._str(node, "resolved_runtime_call"),
                    runtime_call=self._str(node, "runtime_call"),
                )
                if self._is_exception_name(attr) and isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Name":
                    owner_id = self._str(owner_node, "id")
                    owner_module_id = self.import_alias_modules.get(owner_id, "")
                    if self._module_namespace_expr(owner_module_id) != "":
                        first_arg = self._emit_expr(arg_nodes[0]) if len(arg_nodes) > 0 else "\"error\""
                        return "{ val __pytra_obj = new " + _safe_scala_ident(attr) + "(); __pytra_obj.__init__(" + first_arg + "); __pytra_obj }"
                owner_union_lanes = [part.strip() for part in owner_type.split("|")]
                union_dict_owner = any(part == "dict" or part.startswith("dict[") for part in owner_union_lanes)
                dynamic_dict_owner = owner_type in ("JsonVal", "Any", "object", "unknown", "pytra.std.json.JsonVal", "pytra_std_json.JsonVal") or union_dict_owner
                if dynamic_dict_owner and (resolved_method == self._mapping_call("dict.get") or attr == "get") and len(arg_nodes) == 1:
                    return "__pytra_as_dict(" + owner_expr + ").get(" + self._emit_expr(arg_nodes[0]) + ")"
                if dynamic_dict_owner and (resolved_method == self._mapping_call("dict.get") or attr == "get") and len(arg_nodes) == 2:
                    expr = "__pytra_as_dict(" + owner_expr + ").getOrElse(" + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                    result_type = self._str(node, "resolved_type")
                    if result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                        return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                    return expr
                if dynamic_dict_owner and (resolved_method == self._mapping_call("dict.items") or attr == "items") and len(arg_nodes) == 0:
                    return "__pytra_dict_items(__pytra_as_dict(" + owner_expr + "))"
                if dynamic_dict_owner and (resolved_method == self._mapping_call("dict.keys") or attr == "keys") and len(arg_nodes) == 0:
                    return "__pytra_dict_keys(__pytra_as_dict(" + owner_expr + "))"
                if dynamic_dict_owner and (resolved_method == self._mapping_call("dict.values") or attr == "values") and len(arg_nodes) == 0:
                    return "__pytra_dict_values(__pytra_as_dict(" + owner_expr + "))"
                if owner_type in ("str", "string"):
                    if resolved_method == self._mapping_call("str.join") and len(arg_nodes) == 1:
                        return "__pytra_join(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.isalpha") and len(arg_nodes) == 0:
                        return "__pytra_isalpha(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.split"):
                        sep = self._emit_expr(arg_nodes[0]) if len(arg_nodes) >= 1 else "null"
                        return "__pytra_split(" + owner_expr + ", " + sep + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    if resolved_method == self._mapping_call("str.strip"):
                        return "__pytra_strip(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.lstrip"):
                        return "__pytra_lstrip(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.rstrip"):
                        return "__pytra_rstrip(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.replace") and len(arg_nodes) >= 2:
                        return "__pytra_replace(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                    if resolved_method == self._mapping_call("str.startswith") and len(arg_nodes) >= 1:
                        return "__pytra_startswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.endswith") and len(arg_nodes) >= 1:
                        return "__pytra_endswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.upper"):
                        return "__pytra_upper(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.lower"):
                        return "__pytra_lower(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.find") and len(arg_nodes) >= 1:
                        return "__pytra_find(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.count") and len(arg_nodes) >= 1:
                        return "__pytra_count_substr(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.index") and len(arg_nodes) >= 1:
                        return "__pytra_str_index(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.rfind") and len(arg_nodes) >= 1:
                        return "__pytra_rfind(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.isalnum") and len(arg_nodes) == 0:
                        return "__pytra_isalnum(" + owner_expr + ")"
                    if self._str(func, "attr") == "isspace" and len(arg_nodes) == 0:
                        return "(" + owner_expr + ".nonEmpty && " + owner_expr + ".forall(_.isWhitespace))"
                    if resolved_method == self._mapping_call("str.isdigit") and len(arg_nodes) == 0:
                        return "__pytra_isdigit(" + owner_expr + ")"
                if (owner_type.startswith("dict[") or owner_type == "dict") and resolved_method == self._mapping_call("dict.get") and len(arg_nodes) == 1:
                    expr = "__pytra_as_dict(" + owner_expr + ").getOrElse(" + self._emit_expr(arg_nodes[0]) + ", null)"
                    return expr
                if (owner_type.startswith("dict[") or owner_type == "dict") and resolved_method == self._mapping_call("dict.get") and len(arg_nodes) == 2:
                    result_type = self._str(node, "resolved_type")
                    expr = "__pytra_as_dict(" + owner_expr + ").getOrElse(" + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                    default_node = arg_nodes[1]
                    default_is_none = isinstance(default_node, dict) and self._str(default_node, "kind") == "Constant" and default_node.get("value") is None
                    if not default_is_none and result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                        return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                    return expr
                if owner_type.startswith("dict[") or owner_type == "dict":
                    if resolved_method == self._mapping_call("dict.keys"):
                        result_type = self._str(node, "resolved_type")
                        expr = "__pytra_dict_keys(__pytra_as_dict(" + owner_expr + "))"
                        if result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                            return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                        return expr
                    if resolved_method == self._mapping_call("dict.values"):
                        result_type = self._str(node, "resolved_type")
                        expr = "__pytra_dict_values(__pytra_as_dict(" + owner_expr + "))"
                        if result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                            return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                        return expr
                    if resolved_method == self._mapping_call("dict.items"):
                        result_type = self._str(node, "resolved_type")
                        expr = "__pytra_dict_items(__pytra_as_dict(" + owner_expr + "))"
                        if result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                            return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                        return expr
                    if resolved_method == self._mapping_call("dict.pop") and len(arg_nodes) >= 1:
                        key_expr = self._emit_expr(arg_nodes[0])
                        value_type = "Any"
                        owner_rt = owner_type
                        if owner_rt.startswith("dict[") and owner_rt.endswith("]"):
                            inner = owner_rt[5:-1]
                            parts = [part.strip() for part in inner.split(",", 1)]
                            if len(parts) == 2:
                                value_type = scala_type(parts[1])
                        dict_expr = "__pytra_as_dict(" + owner_expr + ")"
                        return "{ val __pytra_pop_key = " + key_expr + "; val __pytra_pop_val = " + dict_expr + "(__pytra_pop_key); " + dict_expr + ".remove(__pytra_pop_key); __pytra_pop_val.asInstanceOf[" + value_type + "] }"
                    if resolved_method == self._mapping_call("dict.setdefault") and len(arg_nodes) >= 2:
                        key_expr = self._emit_expr(arg_nodes[0])
                        default_expr = self._emit_expr(arg_nodes[1])
                        result_type = self._str(node, "resolved_type")
                        expr = "__pytra_as_dict(" + owner_expr + ").getOrElseUpdate(" + key_expr + ", " + default_expr + ")"
                        if result_type not in ("", "unknown", "Any", "object", "JsonVal"):
                            return expr + ".asInstanceOf[" + scala_type(result_type) + "]"
                        return expr
                if owner_type.startswith("list[") or owner_type in ("list", "bytearray", "bytes"):
                    if resolved_method == self._mapping_call("list.append") and len(arg_nodes) == 1:
                        arg_expr = self._emit_expr(arg_nodes[0])
                        if owner_type.startswith("list[") and owner_type.endswith("]"):
                            arg_expr = arg_expr + ".asInstanceOf[" + scala_type(owner_type[5:-1]) + "]"
                        return owner_expr + ".append(" + arg_expr + ")"
                    if resolved_method == self._mapping_call("list.index") and len(arg_nodes) >= 1:
                        return owner_expr + ".indexOf(" + self._emit_expr(arg_nodes[0]) + ").toLong"
                    if resolved_method == self._mapping_call("list.extend") and len(arg_nodes) == 1:
                        arg_expr = self._emit_expr(arg_nodes[0])
                        if owner_type in ("bytearray", "bytes"):
                            return owner_expr + " ++= __pytra_bytes(" + arg_expr + ")"
                        if owner_type.startswith("list[") and owner_type.endswith("]"):
                            elem_type = scala_type(owner_type[5:-1])
                            return owner_expr + " ++= __pytra_as_list(" + arg_expr + ").asInstanceOf[mutable.ArrayBuffer[" + elem_type + "]]"
                        return owner_expr + " ++= __pytra_as_list(" + arg_expr + ")"
                    if resolved_method == self._mapping_call("list.sort"):
                        return "{ val __pytra_sorted = " + owner_expr + ".sorted; " + owner_expr + ".clear(); " + owner_expr + " ++= __pytra_sorted; () }"
                    if resolved_method == self._mapping_call("list.reverse"):
                        return "{ val __pytra_reversed = " + owner_expr + ".reverse; " + owner_expr + ".clear(); " + owner_expr + " ++= __pytra_reversed; () }"
                    if resolved_method == self._mapping_call("list.pop"):
                        if len(arg_nodes) == 0:
                            return "{ val __pytra_idx = " + owner_expr + ".size - 1; val __pytra_val = " + owner_expr + "(__pytra_idx); " + owner_expr + ".remove(__pytra_idx); __pytra_val }"
                        idx_expr = self._emit_expr(arg_nodes[0])
                        return "{ val __pytra_idx = __pytra_index(__pytra_int(" + idx_expr + "), " + owner_expr + ".size.toLong).toInt; val __pytra_val = " + owner_expr + "(__pytra_idx); " + owner_expr + ".remove(__pytra_idx); __pytra_val }"
                if owner_type.startswith("set[") or owner_type == "set":
                    if resolved_method == self._mapping_call("set.update") and len(arg_nodes) >= 1:
                        return "{ __pytra_set_update(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + "); () }"
                    if resolved_method in (self._mapping_call("set.discard"), self._mapping_call("set.remove")) and len(arg_nodes) >= 1:
                        return "{ " + owner_expr + ".subtractOne(" + self._emit_expr(arg_nodes[0]) + "); () }"
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                if func_id == "isinstance":
                    call_args = self._list(node, "args")
                    if len(call_args) >= 2 and isinstance(call_args[1], dict):
                        type_node = call_args[1]
                        if self._str(type_node, "kind") == "Tuple":
                            checks: list[str] = []
                            for elem in self._list(type_node, "elements"):
                                if not isinstance(elem, dict):
                                    continue
                                elem_name = self._str(elem, "id") or self._str(elem, "type_object_of") or self._str(elem, "repr")
                                if elem_name == "":
                                    continue
                                if elem_name in ("dict", "list", "set", "tuple", "str", "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64", "bool"):
                                    checks.append("__pytra_is_instance(" + self._emit_expr(call_args[0]) + ", " + self._quote_string(elem_name) + ")")
                                else:
                                    checks.append(self._emit_expr(call_args[0]) + ".isInstanceOf[" + _safe_scala_ident(elem_name) + "]")
                            if len(checks) > 0:
                                return "(" + " || ".join(checks) + ")"
                        type_name = self._str(call_args[1], "id")
                        if type_name == "":
                            type_name = self._str(call_args[1], "type_object_of")
                        if type_name == "":
                            type_name = self._str(call_args[1], "repr")
                        if type_name != "":
                            pod_types = {"int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float32", "float64"}
                            actual_type = self._str(call_args[0], "resolved_type") if isinstance(call_args[0], dict) else ""
                            if type_name in pod_types and actual_type in pod_types:
                                return "true" if actual_type == type_name else "false"
                            if type_name in ("dict", "list", "set", "tuple", "str", "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64", "bool"):
                                return "__pytra_is_instance(" + self._emit_expr(call_args[0]) + ", " + self._quote_string(type_name) + ")"
                            return self._emit_expr(call_args[0]) + ".isInstanceOf[" + _safe_scala_ident(type_name) + "]"
                node_runtime_symbol = self._str(node, "runtime_symbol")
                node_runtime_call = self._str(node, "runtime_call")
                node_resolved_runtime_call = self._str(node, "resolved_runtime_call")
                has_runtime_metadata = any(v != "" for v in (node_runtime_symbol, node_runtime_call, node_resolved_runtime_call))
                resolved = ""
                if has_runtime_metadata:
                    resolved = resolve_runtime_symbol_name(
                        func_id,
                        self.mapping,
                        module_id=self._str(node, "runtime_module_id"),
                        resolved_runtime_call=node_resolved_runtime_call,
                        runtime_call=node_runtime_call,
                    )
                if func_id in self.local_function_aliases:
                    func_name = _safe_scala_ident(self.local_function_aliases[func_id])
                    func_is_named_function = True
                elif func_id in self.module_function_names:
                    func_name = _safe_scala_ident(func_id)
                    func_is_named_function = True
                call_result_type = self._str(node, "resolved_type")
                if resolved != "":
                    if resolved == "__pytra_set_new":
                        return resolved + "(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                    func_name = resolved
                elif func_id in self.runtime_imports:
                    func_name = self.runtime_imports[func_id]
                else:
                    mapped = self.mapping.calls.get(func_id)
                    if isinstance(mapped, str) and mapped != "":
                        if func_id == "set":
                            return mapped + "(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                        func_name = mapped
                if func_id == "sum":
                    return "__pytra_sum(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
                if func_id == "zip":
                    return "__pytra_zip(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ")"
                if func_id == "bytearray":
                    args_text = ", ".join(self._emit_expr(arg) for arg in self._list(node, "args"))
                    return "__pytra_bytearray(" + args_text + ")"
                if func_id == "bytes":
                    args_text = ", ".join(self._emit_expr(arg) for arg in self._list(node, "args"))
                    return "__pytra_bytes(" + args_text + ")"
                if func_id == "bool" or (node_runtime_call == "static_cast" and node_runtime_symbol == "bool"):
                    args_for_bool = self._list(node, "args")
                    if len(args_for_bool) >= 1:
                        return "__pytra_truthy(" + self._emit_expr(args_for_bool[0]) + ")"
                if self._is_exception_name(func_id):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    class_name = _safe_scala_ident(func_id)
                    tmp_name = "__pytra_obj"
                    return "{ val " + tmp_name + " = new " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
                if func_id in self.module_class_names or (call_result_type != "" and call_result_type == func_id):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    if func_name != "" and (func_name.startswith("__pytra_") or "." in func_name):
                        return func_name + "(" + ", ".join(ctor_args) + ")"
                    class_name = _safe_scala_ident(func_id)
                    tmp_name = "__pytra_obj"
                    if func_id in self.class_without_init:
                        return "new " + class_name + "(" + ", ".join(ctor_args) + ")"
                    if self.class_has_init.get(func_id, False):
                        return "{ val " + tmp_name + " = new " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
                    return "new " + class_name + "(" + ", ".join(ctor_args) + ")"
            func_leaf = func_name.rsplit(".", 1)[-1]
            if func_leaf in self.module_class_names:
                ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                if func_leaf in self.class_without_init:
                    return "new " + func_leaf + "(" + ", ".join(ctor_args) + ")"
                if self.class_has_init.get(func_leaf, False):
                    tmp_name = "__pytra_obj"
                    return "{ val " + tmp_name + " = new " + func_leaf + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
                return "new " + func_leaf + "(" + ", ".join(ctor_args) + ")"
            if self._is_exception_name(func_leaf):
                bare_name = _safe_scala_ident(func_leaf)
                ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                tmp_name = "__pytra_obj"
                return "{ val " + tmp_name + " = new " + bare_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
            raw_args = self._list(node, "args")
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                vararg_info = self.module_function_varargs.get(func_id)
                if vararg_info is not None and len(raw_args) >= vararg_info[0] + 1:
                    last_arg = raw_args[-1]
                    if isinstance(last_arg, dict) and self._str(last_arg, "kind") == "List":
                        raw_args = raw_args[:-1] + self._list(last_arg, "elements")
            args: list[str] = []
            args = self._emit_call_parts(raw_args)
            args.extend(self._emit_keyword_parts(self._list(node, "keywords")))
            if isinstance(func, dict) and self._str(func, "kind") == "Lambda":
                return "(" + func_name + ")(" + ", ".join(args) + ")"
            callable_type = self._callable_type(local_callable_type)
            if not func_is_named_function and callable_type != "":
                if len(args) == 0:
                    invoke_type = "() => Any"
                elif len(args) == 1:
                    invoke_type = "Any => Any"
                else:
                    invoke_type = "(" + ", ".join("Any" for _ in args) + ") => Any"
                return "(" + func_name + ").asInstanceOf[" + invoke_type + "](" + ", ".join(args) + ")"
            return func_name + "(" + ", ".join(args) + ")"
        if kind == "BinOp":
            left = self._emit_expr(node.get("left"))
            right = self._emit_expr(node.get("right"))
            op = self._str(node, "op")
            left_type = self._str(node.get("left"), "resolved_type") if isinstance(node.get("left"), dict) else ""
            right_type = self._str(node.get("right"), "resolved_type") if isinstance(node.get("right"), dict) else ""
            if op == "Mult" and (left_type.startswith("list[") or left_type == "list"):
                return "__pytra_list_repeat(" + left + ", " + right + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
            if op == "Mult" and (right_type.startswith("list[") or right_type == "list"):
                return "__pytra_list_repeat(" + right + ", " + left + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
            if op == "Add" and ((left_type.startswith("list[") or left_type in ("list", "tuple", "bytes", "bytearray")) or (right_type.startswith("list[") or right_type in ("list", "tuple", "bytes", "bytearray"))):
                return "__pytra_list_concat(" + left + ", " + right + ").asInstanceOf[" + scala_type(self._str(node, "resolved_type")) + "]"
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
            if op == "Div" and left_type in ("Path", "pathlib.Path", "pytra.std.pathlib.Path"):
                return "(" + left + " / " + right + ")"
            if op == "Div":
                return "((" + left + ").toDouble / (" + right + ").toDouble)"
            if op == "FloorDiv":
                return "scala.math.floor((" + left + ").toDouble / (" + right + ").toDouble).toLong"
            op_text = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%"}.get(op, op)
            return "(" + left + " " + op_text + " " + right + ")"
        if kind == "Compare":
            left = self._emit_expr(node.get("left"))
            comparators = self._list(node, "comparators")
            ops = self._list(node, "ops")
            if len(comparators) == 1 and len(ops) == 1:
                right = self._emit_expr(comparators[0])
                op = ops[0] if isinstance(ops[0], str) else self._str(ops[0], "kind")
                left_node = node.get("left")
                right_node = comparators[0] if len(comparators) > 0 and isinstance(comparators[0], dict) else None
                if isinstance(left_node, dict) and self._str(left_node, "kind") == "Unbox" and isinstance(left_node.get("value"), dict):
                    left_node = left_node.get("value")
                if isinstance(right_node, dict) and self._str(right_node, "kind") == "Unbox" and isinstance(right_node.get("value"), dict):
                    right_node = right_node.get("value")
                left_is_none = isinstance(left_node, dict) and self._str(left_node, "kind") == "Constant" and left_node.get("value") is None
                right_is_none = isinstance(right_node, dict) and self._str(right_node, "kind") == "Constant" and right_node.get("value") is None
                if op in {"Eq", "NotEq", "Is", "IsNot"} and (left_is_none or right_is_none):
                    obj_node = right_node if left_is_none else left_node
                    obj_expr = self._emit_expr(obj_node) if isinstance(obj_node, dict) else (right if left_is_none else left)
                    if isinstance(obj_node, dict) and self._str(obj_node, "kind") == "Name":
                        obj_expr = _safe_scala_ident(self._str(obj_node, "id"))
                    op_text = "==" if op in {"Eq", "Is"} else "!="
                    return obj_expr + " " + op_text + " null"
                if op == "Eq":
                    return "__pytra_eq(" + left + ", " + right + ")"
                if op == "NotEq":
                    return "!__pytra_eq(" + left + ", " + right + ")"
                op_text = {
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
                return "!__pytra_truthy(" + operand + ")"
            if op == "USub":
                return "-" + operand
            if op == "Invert":
                return "~(" + operand + ")"
        if kind == "JoinedStr":
            parts: list[str] = []
            for value in self._list(node, "values"):
                if not isinstance(value, dict):
                    continue
                value_kind = self._str(value, "kind")
                if value_kind == "Constant" and isinstance(value.get("value"), str):
                    parts.append(self._quote_string(str(value.get("value"))))
                else:
                    parts.append(self._emit_expr(value))
            return "\"\"" if len(parts) == 0 else "(" + " + ".join(parts) + ")"
        if kind == "FormattedValue":
            format_spec = self._str(node, "format_spec")
            value_expr = self._emit_expr(node.get("value"))
            if format_spec != "":
                return "__pytra_format(" + value_expr + ", " + self._quote_string(format_spec) + ")"
            return "__pytra_str(" + value_expr + ")"
        raise RuntimeError("scala emitter: unsupported expr kind: " + kind)


def emit_scala_module(east3_doc: dict[str, JsonVal]) -> str:
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "scala" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)
    module_id = ""
    if isinstance(east3_doc, dict):
        module_id = east3_doc.get("module_id") if isinstance(east3_doc.get("module_id"), str) else ""
        if module_id == "":
            meta = east3_doc.get("meta")
            if isinstance(meta, dict):
                module_id = meta.get("module_id") if isinstance(meta.get("module_id"), str) else ""
    if should_skip_module(module_id, mapping):
        return ""
    renderer = ScalaRenderer(mapping)
    return renderer.render_module(east3_doc)


__all__ = ["emit_scala_module"]

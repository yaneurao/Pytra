"""EAST3 -> Kotlin source emitter.

Initial scaffold for the toolchain2 Kotlin backend.
This intentionally supports only a narrow bootstrap subset.
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
from toolchain.emit.kotlin.types import _safe_kotlin_ident
from toolchain.emit.kotlin.types import _split_generic_args
from toolchain.emit.kotlin.types import kotlin_type
from toolchain.emit.kotlin.types import kotlin_zero_value


class KotlinRenderer(CommonRenderer):
    def __init__(self, mapping: RuntimeMapping) -> None:
        super().__init__("kotlin")
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
        self.subclassed_class_names: set[str] = set()
        self.enum_like_classes: set[str] = set()
        self.class_has_init: dict[str, bool] = {}
        self.class_property_names: dict[str, set[str]] = {}
        self.class_method_names: dict[str, set[str]] = {}
        self.class_base_names: dict[str, str] = {}
        self.current_class_interfaces: list[str] = []
        self.current_class_base: str | None = None
        self._tmp_counter = 0
        self._local_var_scopes: list[set[str]] = []
        self._local_type_scopes: list[dict[str, str]] = []

    def _mapping_call(self, key: str) -> str:
        mapped = self.mapping.calls.get(key)
        return mapped if isinstance(mapped, str) else ""

    def _module_namespace_expr(self, module_id: str) -> str:
        expr = self.mapping.module_namespace_exprs.get(module_id, "")
        return expr if isinstance(expr, str) else ""

    def _module_member_expr(self, module_id: str, name: str) -> str:
        namespace_expr = self._module_namespace_expr(module_id)
        if namespace_expr == "":
            return ""
        safe_name = _safe_kotlin_ident(name)
        if namespace_expr == "math_native" and safe_name in ("pi", "e"):
            return namespace_expr + "_" + safe_name + "()"
        if namespace_expr in ("math_native", "time_native"):
            return namespace_expr + "_" + safe_name
        return namespace_expr + "." + safe_name

    def _path_type_name(self) -> str:
        for source_name, rendered_name in self.mapping.types.items():
            if source_name.lower() == "path" and isinstance(rendered_name, str) and rendered_name != "":
                return rendered_name
        return "Any?"

    def _is_path_type(self, resolved_type: str) -> bool:
        path_type = self._path_type_name()
        if resolved_type == path_type and path_type != "":
            return True
        for source_name, rendered_name in self.mapping.types.items():
            if not isinstance(source_name, str) or source_name.lower() != "path":
                continue
            if resolved_type == source_name:
                return True
            if isinstance(rendered_name, str) and rendered_name != "" and resolved_type == rendered_name:
                return True
        return False

    def _is_exception_name(self, name: str) -> bool:
        return name in self.mapping.exception_types or name in self.module_class_names

    def _exception_class_name(self, name: str) -> str:
        if name == "":
            return "Throwable"
        if self._is_exception_name(name):
            return _safe_kotlin_ident(name)
        return _safe_kotlin_ident(name)

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
            if self._str(stmt, "kind") not in ("FunctionDef", "ClosureDef") or self._str(stmt, "name") != "__init__":
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
                    traits.append(_safe_kotlin_ident(name))
        return traits

    def _collect_trait_methods(self, class_name: str) -> set[str]:
        methods = set(self.class_method_names.get(class_name, set()))
        base_name = self.class_base_names.get(class_name, "")
        if base_name not in ("", "None", "object", "Obj"):
            methods.update(self._collect_trait_methods(base_name))
        return methods

    def _next_tmp(self, prefix: str) -> str:
        self._tmp_counter += 1
        return prefix + str(self._tmp_counter)

    def _render_type(self, resolved_type: str) -> str:
        if resolved_type in ("JsonVal", "__pytra_JsonVal"):
            return "Any?"
        if self._is_path_type(resolved_type):
            return self._path_type_name()
        if resolved_type == "Obj":
            if resolved_type in self.module_class_names:
                return _safe_kotlin_ident(resolved_type)
            return "Any?"
        if resolved_type in self.enum_like_classes:
            return "Long"
        if resolved_type in self.runtime_imports:
            return self.runtime_imports[resolved_type]
        if resolved_type in self.import_symbols:
            import_path = self.import_symbols[resolved_type]
            if import_path.endswith(".JsonVal"):
                return "Any?"
            return import_path
        return kotlin_type(resolved_type)

    def _nullable_type(self, resolved_type: str) -> str:
        rendered = self._render_type(resolved_type)
        if rendered.endswith("?"):
            return rendered
        path_type = self._path_type_name()
        if rendered in ("Long", "Double", "Boolean", "String", path_type):
            return rendered + "?"
        if rendered.endswith(">"):
            return rendered + "?"
        return rendered + "?"

    def _emit_store_target(self, target: JsonVal, value_code: str) -> None:
        if not isinstance(target, dict):
            raise RuntimeError("kotlin emitter: store target must be dict")
        kind = self._str(target, "kind")
        if kind == "Name":
            self._emit(_safe_kotlin_ident(self._str(target, "id")) + " = " + value_code)
            return
        if kind == "Attribute":
            self._emit(self._emit_expr(target) + " = " + value_code)
            return
        if kind == "Subscript":
            owner_node = target.get("value")
            slice_node = target.get("slice")
            owner_expr = self._emit_expr(owner_node)
            owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            index_expr = self._emit_expr(slice_node)
            if owner_type.startswith("dict["):
                self._emit("__pytra_set_index(" + owner_expr + ", " + index_expr + ", " + value_code + ")")
                return
            if owner_type in ("str", "string"):
                raise RuntimeError("kotlin emitter: string subscript assignment unsupported")
            self._emit("__pytra_set_index(" + owner_expr + ", " + index_expr + ", " + value_code + ")")
            return
        raise RuntimeError("kotlin emitter: unsupported store target: " + kind)

    def _is_declared_local(self, name: str) -> bool:
        if len(self._local_var_scopes) == 0:
            return False
        return name in self._local_var_scopes[-1]

    def _declare_local(self, name: str) -> None:
        if len(self._local_var_scopes) == 0:
            return
        self._local_var_scopes[-1].add(name)

    def _record_local_type(self, name: str, resolved_type: str) -> None:
        if len(self._local_type_scopes) == 0 or resolved_type == "":
            return
        self._local_type_scopes[-1][name] = resolved_type

    def _lookup_local_type(self, name: str) -> str:
        for scope in reversed(self._local_type_scopes):
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
                resolved_type = self._str(arg, "resolved_type")
                if arg_id in self.local_function_aliases:
                    parts.append("::" + _safe_kotlin_ident(self.local_function_aliases[arg_id]))
                    continue
                if arg_id in self.module_function_names:
                    parts.append("::" + _safe_kotlin_ident(arg_id))
                    continue
                if resolved_type.startswith("callable[") or resolved_type.startswith("Callable["):
                    parts.append(_safe_kotlin_ident(arg_id))
                    continue
            parts.append(self._emit_expr(arg))
        return parts

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
            parts.append(_safe_kotlin_ident(name) + " = " + self._emit_expr(value))
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
            tmp_name = self._next_tmp("__pytraBoolop")
            current = self._emit_expr(value)
            if is_and:
                expr = "run { val " + tmp_name + " = " + current + "; if (__pytra_truthy(" + tmp_name + ")) " + expr + " else " + tmp_name + " }"
            else:
                expr = "run { val " + tmp_name + " = " + current + "; if (__pytra_truthy(" + tmp_name + ")) " + tmp_name + " else " + expr + " }"
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
            loop_var = self._next_tmp("__iterItem")
            tuple_expr = "__pytra_as_list(" + loop_var + ")"
            for idx2, elem in enumerate(self._list(target, "elements")):
                if not isinstance(elem, dict) or self._str(elem, "kind") != "Name":
                    continue
                elem_name = _safe_kotlin_ident(self._str(elem, "id"))
                elem_type = kotlin_type(self._str(elem, "resolved_type"))
                prelude.append("val " + elem_name + " = (" + tuple_expr + "[" + str(idx2) + "] as " + elem_type + ")")
        if len(prelude) > 0:
            inner = " ".join(line + "; " for line in prelude) + inner
        return "for (" + loop_var + " in " + iter_expr + ") { " + inner + " }"

    def _emit_comp_expr(self, node: dict[str, JsonVal], result_type: str, init_expr: str, leaf_stmt: str) -> str:
        result_name = self._next_tmp("__pytraComp")
        body = self._emit_comp_loops(self._list(node, "generators"), 0, leaf_stmt.replace("__RESULT__", result_name))
        return "run { val " + result_name + ": " + result_type + " = " + init_expr + "; " + body + "; " + result_name + " }"

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        module_id = self._str(east3_doc, "module_id")
        meta = east3_doc.get("meta")
        if module_id == "":
            if isinstance(meta, dict):
                module_id = self._str(meta, "module_id")
                if module_id == "":
                    emit_context = meta.get("emit_context")
                    if isinstance(emit_context, dict):
                        module_id = self._str(emit_context, "module_id")
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
                                resolved = self._mapping_call(name)
                            if resolved == "":
                                resolved = resolve_runtime_symbol_name(name, self.mapping, module_id=mod)
                            if isinstance(resolved, str) and resolved != "":
                                self.runtime_imports[local_name] = resolved
                                continue
                        namespace_expr = self._module_namespace_expr(mod)
                        if namespace_expr != "":
                            self.import_symbols[local_name] = self._module_member_expr(mod, name)
                            continue
                        self.import_symbols[local_name] = _safe_kotlin_ident(mod.replace(".", "_")) + "." + _safe_kotlin_ident(name)
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
        self.subclassed_class_names = {
            self._str(stmt, "base")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict) and self._str(stmt, "kind") == "ClassDef" and self._str(stmt, "base") != ""
        }
        self.enum_like_classes = {
            self._str(stmt, "name")
            for stmt in self._list(east3_doc, "body")
            if isinstance(stmt, dict)
            and self._str(stmt, "kind") == "ClassDef"
            and self._str(stmt, "base") in ("IntEnum", "IntFlag")
        }
        self.class_has_init = {}
        self.class_property_names = {}
        self.class_method_names = {}
        self.class_base_names = {}
        for stmt in self._list(east3_doc, "body"):
            if not isinstance(stmt, dict) or self._str(stmt, "kind") != "ClassDef":
                continue
            class_name = self._str(stmt, "name")
            self.class_base_names[class_name] = self._str(stmt, "base")
            self.class_has_init[class_name] = any(
                isinstance(item, dict)
                and self._str(item, "kind") in ("FunctionDef", "ClosureDef")
                and self._str(item, "name") == "__init__"
                for item in self._list(stmt, "body")
            )
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
            if "_case_main" in self.module_function_names:
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
            if self.current_class_name is None:
                self._emit("Unit")
            else:
                self._emit("// pass")
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
            value_node = node.get("value")
            value = self._emit_expr(value_node) if isinstance(value_node, dict) else kotlin_zero_value(decl_type)
            if isinstance(target, dict) and self._str(target, "kind") in ("Attribute", "Subscript"):
                self._emit_store_target(target, value)
                return
            target_name = _safe_kotlin_ident(self._str(target, "id"))
            if self._is_declared_local(target_name):
                self._emit(target_name + " = " + value)
            else:
                self._emit("var " + target_name + ": " + self._render_type(decl_type) + " = " + value)
                self._declare_local(target_name)
            self._record_local_type(target_name, decl_type)
            return
        if kind == "TypeAlias":
            return
        if kind == "Assign":
            target = node.get("target")
            value = self._emit_expr(node.get("value"))
            if isinstance(target, dict) and self._str(target, "kind") in ("Attribute", "Subscript"):
                self._emit_store_target(target, value)
                return
            target_name = _safe_kotlin_ident(self._str(target, "id"))
            if self._is_declared_local(target_name):
                self._emit(target_name + " = " + value)
            else:
                self._emit("var " + target_name + " = " + value)
                self._declare_local(target_name)
            return
        if kind == "VarDecl":
            name = _safe_kotlin_ident(self._str(node, "name"))
            decl_type = self._str(node, "type")
            if decl_type == "":
                decl_type = self._str(node, "decl_type")
            if decl_type == "":
                decl_type = self._str(node, "resolved_type")
            if decl_type == "":
                decl_type = "Any"
            if not self._is_declared_local(name):
                self._emit("var " + name + ": " + self._render_type(decl_type) + " = " + kotlin_zero_value(decl_type))
                self._declare_local(name)
            self._record_local_type(name, decl_type)
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
            tmp_type = "Any?"
            if isinstance(left, dict):
                tmp_type = kotlin_type(self._str(left, "resolved_type"))
            self._emit("val __pytraSwapTmp: " + tmp_type + " = " + left_code)
            self._emit_store_target(left, right_code)
            self._emit_store_target(right, "__pytraSwapTmp")
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
            self._emit("while (__pytra_truthy(" + test + ")) {")
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
            value = node.get("value")
            if isinstance(value, dict) and self._str(value, "kind") == "Name":
                ident = self._str(value, "id")
                if ident == "continue":
                    self._emit("continue")
                    return
                if ident == "break":
                    self._emit("break")
                    return
            if isinstance(value, dict) and self._str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
                for line in str(value.get("value")).splitlines():
                    self._emit("// " + line)
            else:
                self._emit(self._emit_expr(value))
            return
        if kind == "Raise":
            exc = node.get("exc")
            if exc is None:
                self._emit("throw __pytra_active_exc")
                return
            if isinstance(exc, dict) and self._str(exc, "kind") == "Call":
                func = exc.get("func")
                if isinstance(func, dict):
                    func_kind = self._str(func, "kind")
                    if func_kind == "Name" and self._is_exception_name(self._str(func, "id")):
                        self._emit("throw " + self._emit_expr(exc))
                        return
                    if func_kind == "Attribute" and self._is_exception_name(self._str(func, "attr")):
                        self._emit("throw " + self._emit_expr(exc))
                        return
            message = self._emit_expr(exc) if isinstance(exc, dict) else "\"raise\""
            self._emit("throw RuntimeException(" + message + ".toString())")
            return
        if kind == "Continue":
            self._emit("continue")
            return
        if kind == "Break":
            self._emit("break")
            return
        if kind == "Try":
            for hoisted_name, hoisted_type in self._try_hoisted_names(node):
                safe_name = _safe_kotlin_ident(hoisted_name)
                if self._is_declared_local(safe_name):
                    continue
                self._declare_local(safe_name)
                self._emit("var " + safe_name + ": " + self._nullable_type(hoisted_type) + " = null")
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
                for idx, handler in enumerate(handlers):
                    if not isinstance(handler, dict):
                        continue
                    raw_exc_name = "__pytraErr" + str(idx)
                    bound_name = _safe_kotlin_ident(self._str(handler, "name"))
                    type_node = handler.get("type")
                    catch_type = "Throwable"
                    if isinstance(type_node, dict):
                        catch_type = self._exception_class_name(self._str(type_node, "id"))
                    catch_kw = "} catch (" + raw_exc_name + ": " + catch_type + ") {"
                    self._emit(catch_kw)
                    self.state.indent_level += 1
                    self._emit("val __pytra_active_exc = " + raw_exc_name)
                    if bound_name != "":
                        self._emit("val " + bound_name + " = " + raw_exc_name)
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
        arg_usage = node.get("arg_usage")
        arg_usage_map = arg_usage if isinstance(arg_usage, dict) else {}
        vararg_name = self._str(node, "vararg_name")
        vararg_type = self._str(node, "vararg_type")
        decorators = self._list(node, "decorators")
        is_property = any(isinstance(d, str) and d == "property" for d in decorators)
        params: list[str] = []
        local_scope: set[str] = set()
        rebinding: list[tuple[str, str]] = []
        for arg in arg_order:
            if not isinstance(arg, str):
                continue
            if is_method and arg == "self":
                continue
            safe_arg = _safe_kotlin_ident(arg)
            param_name = safe_arg
            if isinstance(arg_usage_map.get(arg), str) and arg_usage_map.get(arg) == "reassigned":
                param_name = safe_arg + "__in"
                rebinding.append((safe_arg, param_name))
            params.append(param_name + ": " + self._render_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
            local_scope.add(safe_arg)
        if vararg_name != "":
            safe_vararg = _safe_kotlin_ident(vararg_name)
            params.append("vararg " + safe_vararg + ": " + self._render_type(vararg_type if vararg_type != "" else "Any"))
            local_scope.add(safe_vararg)
        return_type_name = self._str(node, "return_type")
        if return_type_name in ("", "None", "none", "Unit"):
            for stmt in self._list(node, "body"):
                if isinstance(stmt, dict) and self._str(stmt, "kind") == "Return" and isinstance(stmt.get("value"), dict):
                    return_type_name = "Any"
                    break
        return_type = self._render_type(return_type_name)
        method_prefix = ""
        if is_method:
            base_methods = self.class_method_names.get(self.current_class_base or "", set())
            interface_methods: set[str] = set()
            for iface in self.current_class_interfaces:
                interface_methods.update(self._collect_trait_methods(iface))
            if self.current_class_base not in (None, "", "None", "object", "Obj") and name in base_methods:
                method_prefix = "override "
            elif name in interface_methods:
                method_prefix = "override "
            elif self.current_class_name in self.subclassed_class_names:
                method_prefix = "open "
        if is_method and is_property:
            self._emit(method_prefix + "val " + name + ": " + return_type)
            self.state.indent_level += 1
            self._emit("get() {")
            self.state.indent_level += 1
        else:
            self._emit(method_prefix + "fun " + name + "(" + ", ".join(params) + "): " + return_type + " {")
            self.state.indent_level += 1
        self._local_var_scopes.append(local_scope)
        self._local_type_scopes.append({})
        for arg in arg_order:
            if isinstance(arg, str):
                arg_type = arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"
                self._record_local_type(_safe_kotlin_ident(arg), arg_type)
        if vararg_name != "":
            self._record_local_type(_safe_kotlin_ident(vararg_name), "list[" + (vararg_type if vararg_type != "" else "Any") + "]")
        for local_name, param_name in rebinding:
            self._emit("var " + local_name + " = " + param_name)
            self._record_local_type(local_name, self._lookup_local_type(param_name))
        body = self._list(node, "body")
        if len(body) == 0:
            self._emit("Unit")
        else:
            for stmt in body:
                self._emit_stmt(stmt)
        self._local_var_scopes.pop()
        self._local_type_scopes.pop()
        self.state.indent_level -= 1
        self._emit("}")
        if is_method and is_property:
            self.state.indent_level -= 1

    def _emit_class_def(self, node: dict[str, JsonVal]) -> None:
        class_name = _safe_kotlin_ident(self._str(node, "name"))
        base_name = self._str(node, "base")
        is_trait = self._has_decorator(node, "trait")
        implements_traits = self._implements_traits(node)
        if base_name in ("IntEnum", "IntFlag"):
            self._emit("object " + class_name + " {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                if not isinstance(stmt, dict) or self._str(stmt, "kind") != "Assign":
                    continue
                target = stmt.get("target")
                if not isinstance(target, dict) or self._str(target, "kind") != "Name":
                    continue
                field_name = _safe_kotlin_ident(self._str(target, "id"))
                value_node = stmt.get("value")
                value = self._emit_expr(value_node) if isinstance(value_node, dict) else "0L"
                self._emit("const val " + field_name + ": Long = " + value)
            self.state.indent_level -= 1
            self._emit("}")
            return
        if base_name == "Enum":
            enum_members: list[tuple[str, str]] = []
            for stmt in self._list(node, "body"):
                if not isinstance(stmt, dict) or self._str(stmt, "kind") != "Assign":
                    continue
                target = stmt.get("target")
                if not isinstance(target, dict) or self._str(target, "kind") != "Name":
                    continue
                field_name = _safe_kotlin_ident(self._str(target, "id"))
                value_node = stmt.get("value")
                value = self._emit_expr(value_node) if isinstance(value_node, dict) else "null"
                enum_members.append((field_name, value))
            self._emit("class " + class_name + " private constructor(val value: Any?) {")
            self.state.indent_level += 1
            if len(enum_members) > 0:
                self._emit("companion object {")
                self.state.indent_level += 1
                for field_name, value in enum_members:
                    self._emit("val " + field_name + ": " + class_name + " = " + class_name + "(" + value + ")")
                self.state.indent_level -= 1
                self._emit("}")
            self.state.indent_level -= 1
            self._emit("}")
            return
        prev_class_name = self.current_class_name
        prev_class_base = self.current_class_base
        prev_class_interfaces = self.current_class_interfaces
        self.current_class_name = class_name
        self.current_class_base = base_name
        self.current_class_interfaces = implements_traits[:]
        if is_trait:
            interface_head = "interface " + class_name
            bases: list[str] = []
            if base_name not in ("", "None", "object", "Obj"):
                bases.append(_safe_kotlin_ident(base_name))
            if len(bases) > 0:
                interface_head += " : " + ", ".join(bases)
            self._emit(interface_head + " {")
            self.state.indent_level += 1
            for stmt in self._list(node, "body"):
                if not isinstance(stmt, dict) or self._str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
                    continue
                name = _safe_kotlin_ident(self._str(stmt, "name"))
                arg_order = self._list(stmt, "arg_order")
                arg_types = stmt.get("arg_types")
                arg_type_map = arg_types if isinstance(arg_types, dict) else {}
                params: list[str] = []
                for arg in arg_order:
                    if not isinstance(arg, str) or arg == "self":
                        continue
                    params.append(_safe_kotlin_ident(arg) + ": " + self._render_type(arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"))
                return_type = self._render_type(self._str(stmt, "return_type"))
                self._emit("fun " + name + "(" + ", ".join(params) + "): " + return_type)
            self.state.indent_level -= 1
            self._emit("}")
            self.current_class_name = prev_class_name
            self.current_class_base = prev_class_base
            self.current_class_interfaces = prev_class_interfaces
            return
        instance_fields = self._collect_class_fields(node)
        class_fields: list[tuple[str, str, str]] = []
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
                field_name = _safe_kotlin_ident(self._str(target, "id"))
                decl_type = self._str(stmt, "decl_type") or self._str(stmt, "resolved_type") or self._str(target, "resolved_type") or "Any"
                value_node = stmt.get("value")
                default_value = self._emit_expr(value_node) if isinstance(value_node, dict) else None
                dataclass_fields.append((field_name, decl_type, default_value))
        dataclass_field_names = {field_name for field_name, _, _ in dataclass_fields}
        class_head = ("open class " if class_name in self.subclassed_class_names else "class ") + class_name
        if len(dataclass_fields) > 0:
            ctor_parts: list[str] = []
            for field_name, decl_type, default_value in dataclass_fields:
                part = "var " + field_name + ": " + self._render_type(decl_type)
                if default_value is not None:
                    part += " = " + default_value
                ctor_parts.append(part)
            class_head += "(" + ", ".join(ctor_parts) + ")"
        class_bases: list[str] = []
        if base_name not in ("", "None", "object", "Obj", "Enum", "IntEnum", "IntFlag"):
            class_bases.append(_safe_kotlin_ident(base_name) + "()")
        class_bases.extend(implements_traits)
        if len(class_bases) > 0:
            class_head += " : " + ", ".join(class_bases)
        self._emit(class_head + " {")
        self.state.indent_level += 1
        seen_instance_fields: set[str] = set()
        for field_name, decl_type in instance_fields:
            safe_field_name = _safe_kotlin_ident(field_name)
            if safe_field_name in dataclass_field_names:
                continue
            if safe_field_name in seen_instance_fields:
                continue
            seen_instance_fields.add(safe_field_name)
            self._emit("var " + safe_field_name + ": " + self._render_type(decl_type) + " = " + kotlin_zero_value(decl_type))
        for stmt in self._list(node, "body"):
            if not isinstance(stmt, dict):
                continue
            kind = self._str(stmt, "kind")
            if kind == "AnnAssign":
                target = stmt.get("target")
                if is_dataclass and isinstance(target, dict) and self._str(target, "kind") == "Name":
                    continue
                field_name = _safe_kotlin_ident(self._str(target, "id"))
                decl_type = self._str(stmt, "decl_type")
                value_node = stmt.get("value")
                if isinstance(value_node, dict):
                    value = self._emit_expr(value_node)
                    class_fields.append((field_name, decl_type, value))
                continue
            if kind == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and self._str(target, "kind") == "Name":
                    field_name = _safe_kotlin_ident(self._str(target, "id"))
                    decl_type = self._str(stmt, "decl_type")
                    if decl_type == "":
                        decl_type = self._str(target, "resolved_type")
                    value_node = stmt.get("value")
                    value = self._emit_expr(value_node) if isinstance(value_node, dict) else kotlin_zero_value(decl_type)
                    class_fields.append((field_name, decl_type, value))
                    continue
            if kind in ("FunctionDef", "ClosureDef"):
                decorators = self._list(stmt, "decorators")
                if any(isinstance(dec, str) and dec == "staticmethod" for dec in decorators):
                    static_methods.append(stmt)
                    continue
            self._emit_stmt(stmt)
        if len(class_fields) > 0:
            self._emit("companion object {")
            self.state.indent_level += 1
            for field_name, decl_type, value in class_fields:
                self._emit("var " + field_name + ": " + self._render_type(decl_type) + " = " + value)
            for method in static_methods:
                self._emit_function_def(method, False)
            self.state.indent_level -= 1
            self._emit("}")
        elif len(static_methods) > 0:
            self._emit("companion object {")
            self.state.indent_level += 1
            for method in static_methods:
                self._emit_function_def(method, False)
            self.state.indent_level -= 1
            self._emit("}")
        self.state.indent_level -= 1
        self._emit("}")
        self.current_class_name = prev_class_name
        self.current_class_base = prev_class_base
        self.current_class_interfaces = prev_class_interfaces

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
            idx_name = self._next_tmp("_idx_")
            descending = self._str(iter_plan, "range_mode") == "descending" or step.strip().startswith("-")
            cmp_op = ">" if descending else "<"
            update = idx_name + " = " + idx_name + " + (" + step + ")"
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
        iter_node = iter_plan.get("iter_expr") if isinstance(iter_plan, dict) else node.get("iter")
        iter_type = self._str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
        if iter_type in ("str", "string"):
            iter_expr = "__pytra_as_list(" + iter_expr + ")"
        loop_var = target_name
        prelude: list[str] = []
        if isinstance(target_node, dict):
            direct_unpack = target_node.get("direct_unpack_names")
            target_type = self._str(target_node, "target_type")
            if (isinstance(direct_unpack, list) and len(direct_unpack) > 0) or target_type == "tuple":
                loop_var = self._next_tmp("__iterItem")
                tuple_var = target_name
                prelude.append("val " + tuple_var + " = (__pytra_as_list(" + loop_var + ") as MutableList<Any?>)")
            else:
                resolved_target_type = self._str(target_node, "resolved_type")
                iter_expr_node = iter_plan.get("iter_expr") if isinstance(iter_plan, dict) else node.get("iter")
                if resolved_target_type in ("", "unknown", "Any", "object") and isinstance(iter_expr_node, dict) and self._str(iter_expr_node, "kind") == "Call":
                    func_node = iter_expr_node.get("func")
                    if isinstance(func_node, dict) and self._str(func_node, "kind") == "Attribute":
                        attr = self._str(func_node, "attr")
                        owner_node = func_node.get("value")
                        owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                        if owner_type.startswith("dict[") and owner_type.endswith("]"):
                            parts = _split_generic_args(owner_type[5:-1])
                            if len(parts) == 2:
                                if attr == "keys":
                                    resolved_target_type = parts[0]
                                elif attr == "values":
                                    resolved_target_type = parts[1]
                if resolved_target_type not in ("", "unknown", "Any", "object"):
                    loop_var = self._next_tmp("__iterItem")
                    prelude.append("val " + target_name + " = (" + loop_var + " as " + self._render_type(resolved_target_type) + ")")
        self._emit("for (" + loop_var + " in " + iter_expr + ") {")
        self.state.indent_level += 1
        for line in prelude:
            self._emit(line)
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
            resolved_type = self._str(node, "resolved_type")
            if resolved_type in ("", "unknown"):
                resolved_type = self._lookup_local_type(_safe_kotlin_ident(ident))
            callable_type = self._callable_type(resolved_type)
            if ident == "self" and self.current_class_name is not None:
                return "this"
            if ident in self.runtime_imports:
                return self.runtime_imports[ident]
            if ident in self.import_symbols:
                return self.import_symbols[ident]
            if ident in self.import_alias_modules:
                module_id = self.import_alias_modules[ident]
                namespace_expr = self._module_namespace_expr(module_id)
                if namespace_expr != "":
                    return namespace_expr
                return _safe_kotlin_ident(module_id.replace(".", "_"))
            if ident in self.local_function_aliases:
                if callable_type != "":
                    return "::" + _safe_kotlin_ident(self.local_function_aliases[ident])
                return _safe_kotlin_ident(self.local_function_aliases[ident])
            if ident in self.module_function_names and callable_type != "":
                return "::" + _safe_kotlin_ident(ident)
            return _safe_kotlin_ident(ident)
        if kind == "Attribute":
            owner_node = node.get("value")
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Call":
                func = owner_node.get("func")
                if isinstance(func, dict) and self._str(func, "kind") == "Name" and self._str(func, "id") == "type" and self._str(node, "attr") == "__name__":
                    args = self._list(owner_node, "args")
                    arg_expr = self._emit_expr(args[0]) if len(args) > 0 else "null"
                    return "__pytra_type_name(" + arg_expr + ")"
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Call" and self._str(owner_node, "special_form") == "super":
                return "super." + _safe_kotlin_ident(self._str(node, "attr"))
            if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Name":
                owner_id = self._str(owner_node, "id")
                module_id = self.import_alias_modules.get(owner_id, "")
                attr_name = _safe_kotlin_ident(self._str(node, "attr"))
                namespace_expr = self._module_namespace_expr(module_id)
                if namespace_expr != "":
                    return self._module_member_expr(module_id, attr_name)
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
                    return _safe_kotlin_ident((module_id + "." + self._str(node, "attr")).replace(".", "_"))
            owner = self._emit_expr(owner_node)
            owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            attr = _safe_kotlin_ident(self._str(node, "attr"))
            if owner_type in self.class_property_names and attr in self.class_property_names.get(owner_type, set()):
                return owner + "." + attr
            return owner + "." + attr
        if kind == "Subscript":
            owner = self._emit_expr(node.get("value"))
            owner_node = node.get("value")
            owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            slice_node = node.get("slice")
            if isinstance(slice_node, dict) and self._str(slice_node, "kind") == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                lower = self._emit_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._emit_expr(upper_node) if isinstance(upper_node, dict) else "__pytra_len(" + owner + ")"
                if owner_type in ("str", "string"):
                    return "(__pytra_slice(" + owner + ", " + lower + ", " + upper + ") as String)"
                if owner_type.startswith("list[") or owner_type.startswith("tuple[") or owner_type in ("list", "tuple", "bytes", "bytearray"):
                    return owner + ".slice((" + lower + ").toInt() until (" + upper + ").toInt()).toMutableList()"
                return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"
            index = self._emit_expr(slice_node)
            if owner_type.startswith("dict["):
                key_node = slice_node if isinstance(slice_node, dict) else None
                key_code = index
                if isinstance(key_node, dict):
                    key_type = self._str(key_node, "resolved_type")
                    if key_type == "str":
                        key_code = self._emit_expr(key_node)
                expr = owner + "[" + key_code + "]"
                resolved = self._str(node, "resolved_type")
                if resolved not in ("", "unknown", "Any", "Any?", "object", "None", "none") and "|" not in resolved:
                    return "(" + expr + "!! as " + self._render_type(resolved) + ")"
                return expr
            if owner_type in ("str", "string"):
                return "(__pytra_get_index(" + owner + ", " + index + ") as String)"
            if owner_type.startswith("list[") or owner_type.startswith("tuple[") or owner_type in ("list", "tuple", "bytes", "bytearray"):
                expr = "__pytra_get_index(" + owner + ", " + index + ")"
                resolved = self._str(node, "resolved_type")
                if resolved not in ("", "unknown", "Any", "object"):
                    return "(" + expr + " as " + self._render_type(resolved) + ")"
                return expr
            return owner + "[(" + index + ").toInt()]"
        if kind == "List":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            if len(elems) == 0:
                resolved_type = self._str(node, "resolved_type")
                list_type = self._render_type(resolved_type)
                if list_type.startswith("MutableList<") and list_type.endswith(">"):
                    inner = list_type[len("MutableList<"):-1]
                    return "mutableListOf<" + inner + ">()"
            return "mutableListOf(" + ", ".join(elems) + ")"
        if kind == "Tuple":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            if len(elems) == 0:
                return "__pytra_tuple()"
            return "__pytra_tuple(" + ", ".join(elems) + ")"
        if kind == "Set":
            elems = [self._emit_expr(elem) for elem in self._list(node, "elements")]
            if len(elems) == 0:
                resolved_type = self._str(node, "resolved_type")
                set_type = self._render_type(resolved_type)
                if set_type.startswith("MutableSet<") and set_type.endswith(">"):
                    inner = set_type[len("MutableSet<"):-1]
                    return "linkedSetOf<" + inner + ">()"
            return "linkedSetOf(" + ", ".join(elems) + ")"
        if kind == "ListComp":
            elt_code = self._emit_expr(node.get("elt"))
            return self._emit_comp_expr(
                node,
                kotlin_type(self._str(node, "resolved_type")),
                "mutableListOf()",
                "__RESULT__.add(" + elt_code + ")",
            )
        if kind == "SetComp":
            elt_code = self._emit_expr(node.get("elt"))
            return self._emit_comp_expr(
                node,
                kotlin_type(self._str(node, "resolved_type")),
                "linkedSetOf()",
                "__RESULT__.add(" + elt_code + ")",
            )
        if kind == "DictComp":
            key_code = self._emit_expr(node.get("key"))
            value_code = self._emit_expr(node.get("value"))
            return self._emit_comp_expr(
                node,
                kotlin_type(self._str(node, "resolved_type")),
                "linkedMapOf()",
                "__RESULT__[" + key_code + "] = " + value_code,
            )
        if kind == "Lambda":
            arg_order = self._list(node, "arg_order")
            arg_types = node.get("arg_types")
            arg_type_map = arg_types if isinstance(arg_types, dict) else {}
            params: list[str] = []
            for arg in arg_order:
                if isinstance(arg, str):
                    arg_type = arg_type_map.get(arg, "Any") if isinstance(arg_type_map.get(arg), str) else "Any"
                    params.append(_safe_kotlin_ident(arg) + ": " + kotlin_type(arg_type))
            return "{ " + ", ".join(params) + " -> " + self._emit_expr(node.get("body")) + " }"
        if kind == "Dict":
            pairs: list[str] = []
            entries = node.get("entries")
            if isinstance(entries, list) and len(entries) > 0:
                for entry in entries:
                    if isinstance(entry, dict):
                        key_node = entry.get("key")
                        value_node = entry.get("value")
                        if isinstance(key_node, dict) and isinstance(value_node, dict):
                            pairs.append(self._emit_expr(key_node) + " to " + self._emit_expr(value_node))
            else:
                keys = self._list(node, "keys")
                values = self._list(node, "values")
                for key_node, value_node in zip(keys, values):
                    pairs.append(self._emit_expr(key_node) + " to " + self._emit_expr(value_node))
            if len(pairs) == 0:
                resolved_type = self._str(node, "resolved_type")
                dict_type = self._render_type(resolved_type)
                if dict_type.startswith("MutableMap<") and dict_type.endswith(">"):
                    inner = dict_type[len("MutableMap<"):-1]
                    return "linkedMapOf<" + inner + ">()"
            return "linkedMapOf(" + ", ".join(pairs) + ")"
        if kind == "Unbox" or kind == "Box":
            value_code = self._emit_expr(node.get("value"))
            target = self._str(node, "target")
            resolved_type = self._str(node, "resolved_type")
            if self._callable_type(target) != "" or self._callable_type(resolved_type) != "":
                return value_code
            if target == "str":
                return "__pytra_str(" + value_code + ")"
            if target == "bool":
                return "__pytra_truthy(" + value_code + ")"
            if target in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
                return "__pytra_int(" + value_code + ")"
            if target in ("float", "float32", "float64"):
                return "__pytra_float(" + value_code + ")"
            cast_type = self._render_type(resolved_type if resolved_type != "" else target)
            if target.startswith("dict[") or target == "dict":
                return "(__pytra_as_dict(" + value_code + ") as " + cast_type + ")"
            if target.startswith("list[") or target in ("list", "tuple", "bytes", "bytearray"):
                return "(__pytra_as_list(" + value_code + ") as " + cast_type + ")"
            if target.startswith("set[") or target == "set":
                return "(__pytra_set_new(" + value_code + ") as " + cast_type + ")"
            if cast_type not in ("", "Any?"):
                return "(" + value_code + " as " + cast_type + ")"
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
            return "__pytra_type_name(" + value + ")"
        if kind == "IsSubtype":
            actual = self._emit_expr(node.get("actual_type_id"))
            expected = self._emit_expr(node.get("expected_type_id"))
            return "__pytra_is_subtype(" + actual + ", " + expected + ")"
        if kind == "Call":
            runtime_module_id = self._str(node, "runtime_module_id")
            runtime_symbol = self._str(node, "runtime_symbol")
            runtime_adapter = self._str(node, "runtime_call_adapter_kind")
            if runtime_module_id == "pytra.std.math" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                if runtime_symbol == "pi":
                    return "math_native_pi()"
                if runtime_symbol == "e":
                    return "math_native_e()"
                return "math_native_" + _safe_kotlin_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            if runtime_module_id == "pytra.std.time" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                return "time_native_" + _safe_kotlin_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            if runtime_adapter == "extern_delegate" and runtime_module_id != "" and runtime_symbol != "":
                args = self._emit_call_parts(self._list(node, "args")) + self._emit_keyword_parts(self._list(node, "keywords"))
                if runtime_module_id == "pytra.std.math":
                    if runtime_symbol == "pi":
                        return "math_native_pi()"
                    if runtime_symbol == "e":
                        return "math_native_e()"
                    return "math_native_" + _safe_kotlin_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
                if runtime_module_id == "pytra.std.time":
                    return "time_native_" + _safe_kotlin_ident(runtime_symbol) + "(" + ", ".join(args) + ")"
            func = node.get("func")
            func_name = self._emit_expr(func)
            func_is_named_function = False
            func_resolved_type = self._str(func, "resolved_type") if isinstance(func, dict) else ""
            local_callable_type = ""
            if isinstance(func, dict) and self._str(func, "kind") == "Name" and func_resolved_type in ("", "unknown"):
                local_callable_type = self._lookup_local_type(_safe_kotlin_ident(self._str(func, "id")))
                func_resolved_type = local_callable_type
            if isinstance(func, dict) and self._str(func, "kind") == "Attribute":
                owner_node = func.get("value")
                attr = self._str(func, "attr")
                owner_expr = self._emit_expr(owner_node)
                owner_type = self._str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                arg_nodes = self._list(node, "args")
                resolved_method = resolve_runtime_symbol_name(
                    attr,
                    self.mapping,
                    module_id=self._str(node, "runtime_module_id"),
                    resolved_runtime_call=self._str(node, "resolved_runtime_call"),
                    runtime_call=self._str(node, "runtime_call"),
                )
                if isinstance(owner_node, dict) and self._str(owner_node, "kind") == "Name":
                    owner_id = self._str(owner_node, "id")
                    module_id = self.import_alias_modules.get(owner_id, "")
                    qualified = self._str(func, "repr")
                    keyword_nodes = self._list(node, "keywords")
                    if attr == "add_argument" and (self._str(node, "semantic_tag") == "stdlib.method.add_argument" or len(keyword_nodes) > 0):
                        call_parts = self._emit_argparse_add_argument_parts(arg_nodes, keyword_nodes)
                        return owner_expr + "." + _safe_kotlin_ident(attr) + "(" + ", ".join(call_parts) + ")"
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
                dynamic_dict_owner = owner_type in ("JsonVal", "Any", "object", "unknown", "pytra.std.json.JsonVal", "pytra_std_json.JsonVal") or "dict[" in owner_type
                if owner_expr == "pytra_built_in_error" and self._is_exception_name(attr):
                    first_arg = self._emit_expr(arg_nodes[0]) if len(arg_nodes) > 0 else "\"error\""
                    return "RuntimeException(" + first_arg + ".toString())"
                if dynamic_dict_owner and attr == "get" and len(arg_nodes) == 1:
                    return "__pytra_as_dict(" + owner_expr + ").get(" + self._emit_expr(arg_nodes[0]) + ")"
                if dynamic_dict_owner and attr == "get" and len(arg_nodes) == 2:
                    default_expr = self._emit_expr(arg_nodes[1])
                    result_type = self._str(node, "resolved_type")
                    if result_type != "":
                        default_expr = "(" + default_expr + " as " + self._render_type(result_type) + ")"
                    expr = "__pytra_as_dict(" + owner_expr + ").getOrElse(" + self._emit_expr(arg_nodes[0]) + ") { " + default_expr + " }"
                    return "(" + expr + " as " + self._render_type(result_type if result_type != "" else "Any") + ")"
                if dynamic_dict_owner and attr == "items" and len(arg_nodes) == 0:
                    return "__pytra_dict_items(__pytra_as_dict(" + owner_expr + "))"
                if dynamic_dict_owner and attr == "keys" and len(arg_nodes) == 0:
                    return "__pytra_as_dict(" + owner_expr + ").keys.toMutableList()"
                if dynamic_dict_owner and attr == "values" and len(arg_nodes) == 0:
                    return "__pytra_as_dict(" + owner_expr + ").values.toMutableList()"
                if owner_type in ("str", "string"):
                    if resolved_method == self._mapping_call("str.join") and len(arg_nodes) == 1:
                        return "__pytra_join(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.isalpha") and len(arg_nodes) == 0:
                        return "__pytra_isalpha(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.isdigit") and len(arg_nodes) == 0:
                        return "__pytra_isdigit(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.isalnum") and len(arg_nodes) == 0:
                        return "__pytra_isalnum(" + owner_expr + ")"
                    if attr == "upper" and len(arg_nodes) == 0:
                        return "__pytra_upper(" + owner_expr + ")"
                    if attr == "lower" and len(arg_nodes) == 0:
                        return "__pytra_lower(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.startswith") and len(arg_nodes) >= 1:
                        return "__pytra_startswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.endswith") and len(arg_nodes) >= 1:
                        return "__pytra_endswith(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.strip") and len(arg_nodes) == 0:
                        return "__pytra_strip(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.lstrip") and len(arg_nodes) == 0:
                        return "__pytra_lstrip(" + owner_expr + ")"
                    if resolved_method == self._mapping_call("str.rstrip") and len(arg_nodes) == 0:
                        return "__pytra_rstrip(" + owner_expr + ")"
                    if attr == "replace" and len(arg_nodes) >= 2:
                        return "__pytra_replace(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ", " + self._emit_expr(arg_nodes[1]) + ")"
                    if attr == "find" and len(arg_nodes) >= 1:
                        return "__pytra_find(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "count" and len(arg_nodes) >= 1:
                        return "__pytra_count_substr(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if attr == "index" and len(arg_nodes) >= 1:
                        return "__pytra_str_index(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.rfind") and len(arg_nodes) >= 1:
                        return "__pytra_rfind(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("str.split"):
                        sep = self._emit_expr(arg_nodes[0]) if len(arg_nodes) >= 1 else "null"
                        return "(__pytra_split(" + owner_expr + ", " + sep + ") as MutableList<String>)"
                if owner_type.startswith("dict[") and attr == "get" and len(arg_nodes) == 1:
                    return "__pytra_as_dict(" + owner_expr + ").get(" + self._emit_expr(arg_nodes[0]) + ")"
                if owner_type.startswith("dict[") and attr == "get" and len(arg_nodes) == 2:
                    default_expr = self._emit_expr(arg_nodes[1])
                    result_type = self._str(node, "resolved_type")
                    if result_type != "":
                        default_expr = "(" + default_expr + " as " + self._render_type(result_type) + ")"
                    expr = "__pytra_as_dict(" + owner_expr + ").getOrElse(" + self._emit_expr(arg_nodes[0]) + ") { " + default_expr + " }"
                    return "(" + expr + " as " + self._render_type(result_type if result_type != "" else "Any") + ")"
                if owner_type.startswith("dict["):
                    if resolved_method == self._mapping_call("dict.clear") and len(arg_nodes) == 0:
                        return "__pytra_as_dict(" + owner_expr + ").clear()"
                    if resolved_method == self._mapping_call("dict.pop") and len(arg_nodes) == 1:
                        result_type = self._str(node, "resolved_type")
                        zero = kotlin_zero_value(result_type)
                        expr = "(__pytra_as_dict(" + owner_expr + ").remove(" + self._emit_expr(arg_nodes[0]) + ") ?: " + zero + ")"
                        if result_type not in ("", "unknown", "Any", "object"):
                            return "(" + expr + " as " + self._render_type(result_type) + ")"
                        return expr
                    if resolved_method == self._mapping_call("dict.setdefault") and len(arg_nodes) == 2:
                        expr = "__pytra_as_dict(" + owner_expr + ").getOrPut(" + self._emit_expr(arg_nodes[0]) + ") { " + self._emit_expr(arg_nodes[1]) + " }"
                        result_type = self._str(node, "resolved_type")
                        if result_type not in ("", "unknown", "Any", "object"):
                            return "(" + expr + " as " + self._render_type(result_type) + ")"
                        return expr
                    if attr == "keys" and len(arg_nodes) == 0:
                        value_type = "Any?"
                        if owner_type.startswith("dict[") and owner_type.endswith("]"):
                            parts = _split_generic_args(owner_type[5:-1])
                            if len(parts) == 2:
                                value_type = self._render_type(parts[0])
                        return "(__pytra_as_dict(" + owner_expr + ").keys.toMutableList() as MutableList<" + value_type + ">)"
                    if attr == "values" and len(arg_nodes) == 0:
                        value_type = "Any?"
                        if owner_type.startswith("dict[") and owner_type.endswith("]"):
                            parts = _split_generic_args(owner_type[5:-1])
                            if len(parts) == 2:
                                value_type = self._render_type(parts[1])
                        return "(__pytra_as_dict(" + owner_expr + ").values.toMutableList() as MutableList<" + value_type + ">)"
                    if attr == "items" and len(arg_nodes) == 0:
                        return "__pytra_dict_items(__pytra_as_dict(" + owner_expr + "))"
                if owner_type.startswith("list[") or owner_type in ("list", "bytes", "bytearray"):
                    if attr == "index" and len(arg_nodes) == 1:
                        return owner_expr + ".indexOf(" + self._emit_expr(arg_nodes[0]) + ").toLong()"
                    if resolved_method == self._mapping_call("list.append") and len(arg_nodes) == 1:
                        return owner_expr + ".add(" + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("list.extend") and len(arg_nodes) == 1:
                        if owner_type in ("bytes", "bytearray"):
                            return owner_expr + ".addAll(__pytra_bytes(" + self._emit_expr(arg_nodes[0]) + "))"
                        elem_type = "Any?"
                        if owner_type.startswith("list[") and owner_type.endswith("]"):
                            elem_type = self._render_type(owner_type[5:-1])
                        return owner_expr + ".addAll((__pytra_as_list(" + self._emit_expr(arg_nodes[0]) + ") as MutableList<" + elem_type + ">))"
                    if resolved_method == self._mapping_call("list.clear") and len(arg_nodes) == 0:
                        return owner_expr + ".clear()"
                    if resolved_method == self._mapping_call("list.pop") and len(arg_nodes) == 0:
                        return owner_expr + ".removeAt(" + owner_expr + ".size - 1)"
                if owner_type.startswith("set[") or owner_type == "set":
                    if resolved_method == self._mapping_call("set.update") and len(arg_nodes) == 1:
                        return "__pytra_set_update(" + owner_expr + ", " + self._emit_expr(arg_nodes[0]) + ")"
                    if resolved_method == self._mapping_call("set.discard") and len(arg_nodes) == 1:
                        return owner_expr + ".remove(" + self._emit_expr(arg_nodes[0]) + ")"
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                if func_id == "isinstance":
                    call_args = self._list(node, "args")
                    if len(call_args) >= 2 and isinstance(call_args[1], dict):
                        type_name = self._str(call_args[1], "id")
                        if type_name == "":
                            type_name = self._str(call_args[1], "type_object_of")
                        if type_name == "":
                            type_name = self._str(call_args[1], "repr")
                        if type_name != "":
                            if type_name in ("dict", "list", "set", "tuple", "str", "int", "int64", "float", "float64", "bool"):
                                return "__pytra_is_instance(" + self._emit_expr(call_args[0]) + ", " + self._quote_string(type_name) + ")"
                            return "(" + self._emit_expr(call_args[0]) + " is " + _safe_kotlin_ident(type_name) + ")"
                mapped = self.mapping.calls.get(func_id)
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
                    func_name = _safe_kotlin_ident(self.local_function_aliases[func_id])
                    func_is_named_function = True
                elif func_id in self.module_function_names:
                    func_name = _safe_kotlin_ident(func_id)
                    func_is_named_function = True
                if resolved != "":
                    func_name = resolved
                    func_is_named_function = True
                elif func_id in self.runtime_imports:
                    func_name = self.runtime_imports[func_id]
                    func_is_named_function = True
                else:
                    if isinstance(mapped, str) and mapped != "":
                        func_name = mapped
                        func_is_named_function = True
                semantic_tag = self._str(node, "semantic_tag")
                if semantic_tag == "core.bytearray_ctor":
                    args_rendered = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    if len(args_rendered) == 0:
                        return "__pytra_bytearray()"
                    return "__pytra_bytearray(" + ", ".join(args_rendered) + ")"
                if semantic_tag == "core.bytes_ctor":
                    args_rendered = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    if len(args_rendered) == 0:
                        return "__pytra_bytes()"
                    return "__pytra_bytes(" + ", ".join(args_rendered) + ")"
                if func_id == "sum":
                    return "(__pytra_sum(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ") as " + self._render_type(self._str(node, "resolved_type")) + ")"
                if func_id == "zip":
                    return "__pytra_zip(" + ", ".join(self._emit_expr(arg) for arg in self._list(node, "args")) + ")"
                if func_id == "bool":
                    arg_nodes = self._list(node, "args")
                    arg_expr = self._emit_expr(arg_nodes[0]) if len(arg_nodes) > 0 else "null"
                    return "__pytra_truthy(" + arg_expr + ")"
                if func_id in self.import_symbols:
                    import_path = self.import_symbols[func_id]
                    func_name = import_path
                    func_is_named_function = True
                    if import_path.startswith("pytra_built_in_error.") and self._is_exception_name(func_id):
                        first_arg = self._emit_expr(self._list(node, "args")[0]) if len(self._list(node, "args")) > 0 else "\"error\""
                        return "RuntimeException(" + first_arg + ".toString())"
                elif resolved == "" and not (isinstance(mapped, str) and mapped != "") and (func_id in self.module_class_names or self._str(node, "resolved_type") == func_id):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    if func_name != "" and (func_name.startswith("__pytra_") or "." in func_name):
                        return func_name + "(" + ", ".join(ctor_args) + ")"
                    class_name = _safe_kotlin_ident(func_id)
                    tmp_name = "__pytraObj"
                    if self.class_has_init.get(func_id, True):
                        return "run { val " + tmp_name + " = " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
                    return class_name + "(" + ", ".join(ctor_args) + ")"
                if self._is_exception_name(func_id):
                    ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                    class_name = _safe_kotlin_ident(func_id)
                    tmp_name = "__pytraObj"
                    return "run { val " + tmp_name + " = " + class_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
            func_leaf = func_name.rsplit(".", 1)[-1]
            if self._is_exception_name(func_leaf):
                bare_name = _safe_kotlin_ident(func_leaf)
                ctor_args = [self._emit_expr(arg) for arg in self._list(node, "args")]
                tmp_name = "__pytraObj"
                return "run { val " + tmp_name + " = " + bare_name + "(); " + tmp_name + ".__init__(" + ", ".join(ctor_args) + "); " + tmp_name + " }"
            raw_args = self._list(node, "args")
            if func_name == "__pytra_list":
                rendered_list_args = self._emit_call_parts(raw_args)
                list_type = self._str(node, "resolved_type")
                type_arg = "Any?"
                if list_type.startswith("list[") and list_type.endswith("]"):
                    type_arg = self._render_type(list_type[5:-1])
                return "__pytra_list<" + type_arg + ">(" + (rendered_list_args[0] if len(rendered_list_args) > 0 else "null") + ")"
            if isinstance(func, dict) and self._str(func, "kind") == "Name":
                func_id = self._str(func, "id")
                vararg_info = self.module_function_varargs.get(func_id)
                if vararg_info is not None and len(raw_args) >= vararg_info[0] + 1:
                    last_arg = raw_args[-1]
                    if isinstance(last_arg, dict) and self._str(last_arg, "kind") == "List":
                        raw_args = raw_args[:-1] + self._list(last_arg, "elements")
            args: list[str] = self._emit_call_parts(raw_args)
            args.extend(self._emit_keyword_parts(self._list(node, "keywords")))
            if isinstance(func, dict) and self._str(func, "kind") == "Lambda":
                return "(" + func_name + ")(" + ", ".join(args) + ")"
            if isinstance(func, dict) and self._str(func, "kind") == "Attribute":
                func_is_named_function = True
            if "." in func_name or func_name.startswith("__pytra_"):
                func_is_named_function = True
            callable_source_type = local_callable_type if local_callable_type != "" else func_resolved_type
            callable_type = self._callable_type(callable_source_type)
            if not func_is_named_function and callable_type != "":
                expected_arg_types: list[str] = []
                if (callable_source_type.startswith("callable[") or callable_source_type.startswith("Callable[")) and callable_source_type.endswith("]"):
                    prefix_len = len("Callable[") if callable_source_type.startswith("Callable[") else len("callable[")
                    inner = callable_source_type[prefix_len:-1]
                    parts = _split_generic_args(inner)
                    if len(parts) == 2:
                        arg_spec = parts[0].strip()
                        if arg_spec.startswith("[") and arg_spec.endswith("]"):
                            expected_arg_types = [item.strip() for item in _split_generic_args(arg_spec[1:-1])]
                coerced_args: list[str] = []
                for idx, arg in enumerate(raw_args):
                    rendered = args[idx]
                    if idx < len(expected_arg_types) and isinstance(arg, dict):
                        arg_rt = self._str(arg, "resolved_type")
                        if expected_arg_types[idx] in ("float", "float32", "float64") and arg_rt in ("int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"):
                            rendered = "__pytra_float(" + self._emit_expr(arg) + ")"
                    coerced_args.append(rendered)
                args = coerced_args
                if len(args) == 0:
                    invoke_type = "() -> Any?"
                else:
                    invoke_type = "(" + ", ".join("Any?" for _ in args) + ") -> Any?"
                invoke_expr = "((" + func_name + ") as " + invoke_type + ")(" + ", ".join(args) + ")"
                resolved_type = self._str(node, "resolved_type")
                if resolved_type not in ("", "unknown", "Any", "object", "JsonVal"):
                    return "(" + invoke_expr + " as " + self._render_type(resolved_type) + ")"
                return invoke_expr
            call_expr = func_name + "(" + ", ".join(args) + ")"
            resolved_type = self._str(node, "resolved_type")
            if func_name in ("__pytra_bytes", "__pytra_bytearray", "__pytra_set_new", "__pytra_list_repeat") and resolved_type != "":
                return "(" + call_expr + " as " + self._render_type(resolved_type) + ")"
            return call_expr
        if kind == "BinOp":
            left = self._emit_expr(node.get("left"))
            right = self._emit_expr(node.get("right"))
            op = self._str(node, "op")
            left_node = node.get("left")
            right_node = node.get("right")
            left_type = self._str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
            right_type = self._str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
            if op == "Mult" and (left_type.startswith("list[") or left_type in ("list", "bytes", "bytearray")):
                return "(__pytra_list_repeat(" + left + ", " + right + ") as " + self._render_type(self._str(node, "resolved_type")) + ")"
            if op == "Mult" and (right_type.startswith("list[") or right_type in ("list", "bytes", "bytearray")):
                return "(__pytra_list_repeat(" + right + ", " + left + ") as " + self._render_type(self._str(node, "resolved_type")) + ")"
            if op == "Add" and ((left_type.startswith("list[") or left_type in ("list", "tuple", "bytes", "bytearray")) or (right_type.startswith("list[") or right_type in ("list", "tuple", "bytes", "bytearray"))):
                return "(__pytra_list_concat(" + left + ", " + right + ") as " + self._render_type(self._str(node, "resolved_type")) + ")"
            if op == "Div":
                return "((" + left + ").toDouble() / (" + right + ").toDouble())"
            if op == "FloorDiv":
                return "kotlin.math.floor(((" + left + ").toDouble() / (" + right + ").toDouble())).toLong()"
            if op == "BitAnd":
                return "((" + left + ") and (" + right + "))"
            if op == "BitOr":
                return "((" + left + ") or (" + right + "))"
            if op == "BitXor":
                return "((" + left + ") xor (" + right + "))"
            if op == "LShift":
                return "((" + left + ") shl ((" + right + ").toInt()))"
            if op == "RShift":
                return "((" + left + ") shr ((" + right + ").toInt()))"
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
                        obj_expr = _safe_kotlin_ident(self._str(obj_node, "id"))
                    op_text = "==" if op in {"Eq", "Is"} else "!="
                    return obj_expr + " " + op_text + " null"
                if op == "Eq":
                    return "__pytra_eq(" + left + ", " + right + ")"
                if op == "NotEq":
                    return "!__pytra_eq(" + left + ", " + right + ")"
                if op == "In":
                    return "__pytra_contains(" + right + ", " + left + ")"
                if op == "NotIn":
                    return "!__pytra_contains(" + right + ", " + left + ")"
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
                return "!__pytra_truthy(" + operand + ")"
            if op == "USub":
                return "-" + operand
            if op == "Invert":
                return operand + ".inv()"
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
        raise RuntimeError("kotlin emitter: unsupported expr kind: " + kind)


def emit_kotlin_module(east3_doc: dict[str, JsonVal]) -> str:
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "kotlin" / "mapping.json"
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
    renderer = KotlinRenderer(mapping)
    return renderer.render_module(east3_doc)


__all__ = ["emit_kotlin_module"]

from __future__ import annotations

from pytra.std.pathlib import Path

from pytra.typing import Any
from toolchain.emit.cpp.emitter.runtime_paths import (
    module_name_to_cpp_include as _module_name_to_cpp_include_impl,
)
from toolchain.frontends.runtime_symbol_index import lookup_cpp_namespace_for_runtime_module
from toolchain.frontends.runtime_symbol_index import lookup_runtime_module_group
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_runtime_module
from toolchain.compiler.transpile_cli import (
    append_unique_non_empty,
    dict_any_get_dict,
    dict_any_get_dict_list,
    dict_any_get_str,
    extract_function_arg_types_from_python_source,
    extract_function_signatures_from_python_source,
    load_east_document,
    python_module_exists_under,
    split_top_level_csv,
    sort_str_list_copy,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_STD_SOURCE_ROOT = REPO_ROOT / "src/pytra/std"
RUNTIME_UTILS_SOURCE_ROOT = REPO_ROOT / "src/pytra/utils"
RUNTIME_BUILT_IN_SOURCE_ROOT = REPO_ROOT / "src/pytra/built_in"
_CPP_HELPER_MODULE_BY_SPECIAL_OP = {
    "all": "pytra.built_in.predicates",
    "any": "pytra.built_in.predicates",
    "enumerate": "pytra.built_in.iter_ops",
    "minmax": "pytra.built_in.numeric_ops",
    "range": "pytra.built_in.sequence",
    "reversed": "pytra.built_in.iter_ops",
    "zip": "pytra.built_in.zip_ops",
}
_CPP_HELPER_MODULE_BY_DIRECT_CALL = {
    "sum": "pytra.built_in.numeric_ops",
}
_CPP_HELPER_MODULE_BY_RUNTIME_CALL = {
    "zip": "pytra.built_in.zip_ops",
    "py_min": "pytra.built_in.numeric_ops",
    "py_max": "pytra.built_in.numeric_ops",
}
_CPP_REPEAT_INT_TYPES = {"int", "uint", "int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}
RUNTIME_CPP_GENERATED_ROOT = REPO_ROOT / "src/runtime/cpp/generated"
TOOLCHAIN_COMPILER_PREFIX = "toolchain.compiler."
TOOLCHAIN_COMPILER_PREFIX_LEN = len(TOOLCHAIN_COMPILER_PREFIX)


class CppModuleEmitter:
    """Import/include/namespace/module-init helpers extracted from CppEmitter."""

    def _current_user_module_name(self) -> str:
        """現在 emit 中の user module 名を返す。未解決時は空文字。"""
        meta = dict_any_get_dict(self.doc, "meta")
        module_id = dict_any_get_str(meta, "module_id")
        if module_id != "":
            return module_id
        module_ns_map = getattr(self, "module_namespace_map", {})
        if isinstance(module_ns_map, dict):
            for module_name, namespace in module_ns_map.items():
                if isinstance(module_name, str) and isinstance(namespace, str) and namespace == self.top_namespace:
                    return module_name
        return ""

    def _resolve_relative_user_module_name(self, current_module_name: str, raw_module_name: str) -> str:
        """相対 import 名を current module 基準の user module 名へ正規化する。"""
        raw = raw_module_name.strip()
        if raw == "" or not raw.startswith("."):
            return raw
        dot_count = 0
        while dot_count < len(raw) and raw[dot_count] == ".":
            dot_count += 1
        tail = raw[dot_count:].strip(".")
        current_parts = [part for part in current_module_name.split(".") if part != ""] if current_module_name != "" else []
        package_parts = current_parts[:-1] if len(current_parts) > 0 else []
        up_count = dot_count - 1
        if up_count > 0:
            if up_count >= len(package_parts):
                package_parts = []
            else:
                package_parts = package_parts[: len(package_parts) - up_count]
        if tail != "":
            package_parts.extend([part for part in tail.split(".") if part != ""])
        return ".".join(package_parts)

    def _resolve_user_class_binding(
        self,
        module_name: str,
        east_doc: dict[str, Any],
        class_name: str,
    ) -> tuple[str, str]:
        """user module 内の class 参照を (module_name, class_name) へ解決する。"""
        if class_name == "":
            return "", ""
        body = self.any_to_list(east_doc.get("body"))
        for stmt_any in body:
            stmt = stmt_any if isinstance(stmt_any, dict) else {}
            if dict_any_get_str(stmt, "kind") != "ClassDef":
                continue
            if dict_any_get_str(stmt, "name") == class_name:
                return module_name, class_name
        meta = self.any_to_dict_or_empty(east_doc.get("meta"))
        import_symbols = self.any_to_dict_or_empty(meta.get("import_symbols"))
        imported = self.any_to_dict_or_empty(import_symbols.get(class_name))
        imported_module = dict_any_get_str(imported, "module")
        imported_name = dict_any_get_str(imported, "name")
        if imported_module != "" and imported_name != "":
            return self._resolve_relative_user_module_name(module_name, imported_module), imported_name
        resolution = self.any_to_dict_or_empty(meta.get("import_resolution"))
        bindings = self.any_to_dict_list(resolution.get("bindings"))
        for binding in bindings:
            local_name = dict_any_get_str(binding, "local_name")
            export_name = dict_any_get_str(binding, "export_name")
            if class_name not in {local_name, export_name}:
                continue
            target_module = dict_any_get_str(binding, "runtime_module_id")
            if target_module == "":
                target_module = dict_any_get_str(binding, "source_module_id")
            if target_module == "":
                target_module = dict_any_get_str(binding, "module_id")
            target_name = dict_any_get_str(binding, "runtime_symbol")
            if target_name == "":
                target_name = dict_any_get_str(binding, "source_export_name")
            if target_name == "":
                target_name = export_name
            if target_module == "" or target_name == "":
                continue
            return self._resolve_relative_user_module_name(module_name, target_module), target_name
        return "", ""

    def _build_user_class_index(self) -> dict[tuple[str, str], dict[str, Any]]:
        """multi-file bundle 全体の user class metadata を構築する。"""
        cached = getattr(self, "_user_class_index_cache", None)
        if isinstance(cached, dict):
            return cached
        out: dict[tuple[str, str], dict[str, Any]] = {}
        user_module_docs = getattr(self, "user_module_east_map", {})
        if not isinstance(user_module_docs, dict):
            self._user_class_index_cache = out
            return out
        for module_name_obj, east_any in user_module_docs.items():
            if not isinstance(module_name_obj, str):
                continue
            module_name = module_name_obj
            east_doc = east_any if isinstance(east_any, dict) else {}
            if len(east_doc) == 0:
                continue
            ns = self._module_name_to_cpp_namespace(module_name)
            body = self.any_to_list(east_doc.get("body"))
            for stmt_any in body:
                stmt = stmt_any if isinstance(stmt_any, dict) else {}
                if dict_any_get_str(stmt, "kind") != "ClassDef":
                    continue
                class_name = dict_any_get_str(stmt, "name")
                if class_name == "":
                    continue
                raw_base = dict_any_get_str(stmt, "base")
                base_module = ""
                base_name = ""
                base_cpp_name = ""
                if raw_base != "":
                    base_module, base_name = self._resolve_user_class_binding(module_name, east_doc, raw_base)
                    if base_module != "" and base_name != "":
                        base_ns = self._module_name_to_cpp_namespace(base_module)
                        base_cpp_name = f"{base_ns}::{base_name}" if base_ns != "" else base_name
                methods = self.any_to_list(stmt.get("body"))
                method_names: set[str] = set()
                for method_any in methods:
                    method_stmt = method_any if isinstance(method_any, dict) else {}
                    if dict_any_get_str(method_stmt, "kind") != "FunctionDef":
                        continue
                    method_name = dict_any_get_str(method_stmt, "name")
                    if method_name != "":
                        method_names.add(method_name)
                raw_hint = dict_any_get_str(stmt, "class_storage_hint", "ref")
                if raw_hint not in {"value", "ref"}:
                    raw_hint = "ref"
                cpp_name = f"{ns}::{class_name}" if ns != "" else class_name
                out[(module_name, class_name)] = {
                    "module_name": module_name,
                    "class_name": class_name,
                    "cpp_name": cpp_name,
                    "raw_storage_hint": raw_hint,
                    "storage_hint": raw_hint,
                    "base_module": base_module,
                    "base_name": base_name,
                    "base_cpp_name": base_cpp_name,
                    "method_names": set(method_names),
                }
        ref_keys: set[tuple[str, str]] = set()
        for key, doc in out.items():
            if self.any_to_str(doc.get("raw_storage_hint")) == "ref":
                ref_keys.add(key)
        changed = True
        while changed:
            changed = False
            for key, doc in out.items():
                base_module = self.any_to_str(doc.get("base_module"))
                base_name = self.any_to_str(doc.get("base_name"))
                if base_module == "" or base_name == "":
                    continue
                base_key = (base_module, base_name)
                if base_key not in out:
                    continue
                if key in ref_keys and base_key not in ref_keys:
                    ref_keys.add(base_key)
                    changed = True
                if base_key in ref_keys and key not in ref_keys:
                    ref_keys.add(key)
                    changed = True
        for key, doc in out.items():
            doc["storage_hint"] = "ref" if key in ref_keys else self.any_to_str(doc.get("raw_storage_hint"))
        self._user_class_index_cache = out
        return out

    def _effective_user_class_storage_hint(self, module_name: str, class_name: str, fallback: str) -> str:
        """user class の実効 storage hint を返す。"""
        doc = self._build_user_class_index().get((module_name, class_name))
        if isinstance(doc, dict):
            hint = self.any_to_str(doc.get("storage_hint"))
            if hint in {"value", "ref"}:
                return hint
        return fallback if fallback in {"value", "ref"} else "ref"

    def _global_user_virtual_methods_by_base_cpp_name(self) -> dict[str, set[str]]:
        """cross-module 継承から base class 側で virtual にすべき method 集合を返す。"""
        out: dict[str, set[str]] = {}
        class_index = self._build_user_class_index()
        for _, doc in class_index.items():
            methods_any = doc.get("method_names")
            methods = methods_any if isinstance(methods_any, set) else set()
            if len(methods) == 0:
                continue
            seen: set[tuple[str, str]] = set()
            base_module = self.any_to_str(doc.get("base_module"))
            base_name = self.any_to_str(doc.get("base_name"))
            while base_module != "" and base_name != "":
                base_key = (base_module, base_name)
                if base_key in seen or base_key not in class_index:
                    break
                seen.add(base_key)
                base_doc = class_index.get(base_key, {})
                base_methods_any = base_doc.get("method_names")
                base_methods = base_methods_any if isinstance(base_methods_any, set) else set()
                common = set()
                for method_name in methods:
                    if method_name in base_methods:
                        common.add(method_name)
                base_cpp_name = self.any_to_str(base_doc.get("cpp_name"))
                if base_cpp_name != "" and len(common) > 0:
                    cur = out.get(base_cpp_name)
                    if not isinstance(cur, set):
                        cur = set()
                        out[base_cpp_name] = cur
                    cur.update(common)
                base_module = self.any_to_str(base_doc.get("base_module"))
                base_name = self.any_to_str(base_doc.get("base_name"))
        return out

    def _global_user_nonconst_methods_by_base_cpp_name(self) -> dict[str, set[str]]:
        """cross-module override が self mutation を持つ場合に base 側で const を外す method 集合を返す。"""
        out: dict[str, set[str]] = {}
        class_index = self._build_user_class_index()
        user_module_docs = getattr(self, "user_module_east_map", {})
        if not isinstance(user_module_docs, dict):
            return out
        for module_name_obj, east_any in user_module_docs.items():
            if not isinstance(module_name_obj, str):
                continue
            module_name = module_name_obj
            east_doc = east_any if isinstance(east_any, dict) else {}
            if len(east_doc) == 0:
                continue
            body = self.any_to_list(east_doc.get("body"))
            for stmt_any in body:
                stmt = stmt_any if isinstance(stmt_any, dict) else {}
                if dict_any_get_str(stmt, "kind") != "ClassDef":
                    continue
                class_name = dict_any_get_str(stmt, "name")
                if class_name == "":
                    continue
                class_key = (module_name, class_name)
                class_doc = class_index.get(class_key)
                if not isinstance(class_doc, dict):
                    continue
                methods = self.any_to_list(stmt.get("body"))
                mutating_methods = self._collect_nonconst_method_names_in_class_body(
                    [method_any for method_any in methods if isinstance(method_any, dict)]
                )
                if len(mutating_methods) == 0:
                    continue
                seen: set[tuple[str, str]] = set()
                base_module = self.any_to_str(class_doc.get("base_module"))
                base_name = self.any_to_str(class_doc.get("base_name"))
                while base_module != "" and base_name != "":
                    base_key = (base_module, base_name)
                    if base_key in seen or base_key not in class_index:
                        break
                    seen.add(base_key)
                    base_doc = class_index.get(base_key, {})
                    base_methods_any = base_doc.get("method_names")
                    base_methods = base_methods_any if isinstance(base_methods_any, set) else set()
                    common = set()
                    for method_name in mutating_methods:
                        if method_name in base_methods:
                            common.add(method_name)
                    base_cpp_name = self.any_to_str(base_doc.get("cpp_name"))
                    if base_cpp_name != "" and len(common) > 0:
                        cur = out.get(base_cpp_name)
                        if not isinstance(cur, set):
                            cur = set()
                            out[base_cpp_name] = cur
                        cur.update(common)
                    base_module = self.any_to_str(base_doc.get("base_module"))
                    base_name = self.any_to_str(base_doc.get("base_name"))
        return out

    def _class_key_for_cpp_name(self, cpp_name: str) -> str:
        """canonical cpp_name を現在 emitter の class key へ写像する。"""
        if cpp_name in self.class_method_names or cpp_name in self.class_names:
            return cpp_name
        ns = self.top_namespace.strip()
        if ns != "":
            prefix = ns + "::"
            if cpp_name.startswith(prefix):
                leaf = cpp_name[len(prefix) :]
                if leaf in self.class_method_names or leaf in self.class_names:
                    return leaf
        return ""

    def _resolve_local_class_base_cpp_name(self, base_name: str) -> str:
        """現在 module の class base 名を emitted C++ 名へ解決する。"""
        if base_name == "":
            return ""
        if base_name in self.class_names:
            return base_name
        imported = self._resolve_imported_symbol(base_name)
        imported_module = self.any_dict_get_str(imported, "module", "")
        imported_name = self.any_dict_get_str(imported, "name", "")
        if imported_module != "" and imported_name != "":
            imported_doc = self._module_class_doc(imported_module, imported_name)
            cpp_name = self.any_to_str(imported_doc.get("cpp_name"))
            if cpp_name != "":
                return cpp_name
        return base_name

    def _normalize_user_class_signature_arg_type(
        self,
        module_name: str,
        east_doc: dict[str, Any],
        raw_type: str,
    ) -> str:
        """user class 引数型を function/method signature 用の canonical 形へ正規化する。"""
        type_name = self.normalize_type_name(raw_type)
        if type_name in {"", "unknown", "Any", "object", "None"}:
            return type_name
        target_module, target_class = self._resolve_user_class_binding(module_name, east_doc, type_name)
        if target_module == "" or target_class == "":
            return type_name
        doc = self._build_user_class_index().get((target_module, target_class), {})
        cpp_name = self.any_to_str(doc.get("cpp_name"))
        if cpp_name == "":
            return type_name
        storage_hint = self.any_to_str(doc.get("storage_hint"))
        cpp_t = f"rc<{cpp_name}>" if storage_hint == "ref" else cpp_name
        if self._is_cpp_class_borrow_param_type(type_name, cpp_t):
            return cpp_name
        return cpp_t

    def _normalize_runtime_module_name(self, module_name: str) -> str:
        module_name_norm = module_name
        if module_name_norm.find(".") < 0:
            bare_src = RUNTIME_STD_SOURCE_ROOT / (module_name_norm.replace(".", "/") + ".py")
            if bare_src.exists():
                return "pytra.std." + module_name_norm
        return module_name_norm

    def _resolve_class_doc_module_name(self, module_name: str, class_name: str) -> str:
        """Class signature/doc lookup 用に import target module を正規化する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm == "" or class_name == "":
            return module_name_norm
        resolved_module = resolve_import_binding_runtime_module(module_name_norm, class_name, "symbol")
        if resolved_module != "":
            return self._normalize_runtime_module_name(resolved_module)
        user_module_docs = getattr(self, "user_module_east_map", {})
        if isinstance(user_module_docs, dict) and len(user_module_docs) > 0:
            if module_name_norm in user_module_docs:
                return module_name_norm
            stripped_module = module_name_norm.lstrip(".")
            if stripped_module in user_module_docs:
                return stripped_module
            bare_module = stripped_module.split(".")[-1] if stripped_module != "" else ""
            if bare_module != "":
                if bare_module in user_module_docs:
                    return bare_module
                for candidate in user_module_docs.keys():
                    if not isinstance(candidate, str):
                        continue
                    if candidate == bare_module or candidate.endswith("." + bare_module):
                        return candidate
        return module_name_norm

    def _module_name_to_cpp_include(self, module_name: str) -> str:
        """Python import モジュール名を C++ include へ解決する。"""
        return _module_name_to_cpp_include_impl(module_name)

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """Python import モジュール名を C++ namespace へ解決する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        module_ns_map = getattr(self, "module_namespace_map", {})
        if isinstance(module_ns_map, dict):
            mapped_ns = module_ns_map.get(module_name_norm)
            if isinstance(mapped_ns, str) and mapped_ns != "":
                return mapped_ns
        ns = lookup_cpp_namespace_for_runtime_module(module_name_norm)
        if ns != "" or module_name_norm.startswith("pytra.core.") or module_name_norm.startswith("pytra.built_in."):
            return ns
        return ""

    def _import_binding_cpp_include(self, binding: dict[str, Any]) -> str:
        """import binding 1件から include 対象 module を index 経由で解決する。"""
        module_id = dict_any_get_str(binding, "module_id")
        export_name = dict_any_get_str(binding, "export_name")
        binding_kind = dict_any_get_str(binding, "binding_kind")
        resolved_module = resolve_import_binding_runtime_module(module_id, export_name, binding_kind)
        if resolved_module != "":
            return self._module_name_to_cpp_include(resolved_module)
        return self._module_name_to_cpp_include(module_id)

    def _collect_runtime_modules_from_node(self, node: Any, out: set[str]) -> None:
        if isinstance(node, dict):
            d: dict[str, Any] = node
            module_id = dict_any_get_str(d, "runtime_module_id")
            if module_id != "":
                out.add(module_id)
            attr_module_id = self._module_attr_runtime_module_from_node(d)
            if attr_module_id != "":
                out.add(attr_module_id)
            for value in d.values():
                self._collect_runtime_modules_from_node(value, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_runtime_modules_from_node(item, out)

    def _collect_cpp_helper_includes_from_node(self, node: Any, out: set[str]) -> None:
        if isinstance(node, dict):
            d2: dict[str, Any] = node
            kind = self._node_kind_from_dict(d2)
            if kind in {"RuntimeSpecialOp", "PathRuntimeOp"}:
                op = dict_any_get_str(d2, "op")
                helper_include = self._module_name_to_cpp_include(
                    _CPP_HELPER_MODULE_BY_SPECIAL_OP.get(op, "")
                )
                if helper_include != "":
                    out.add(helper_include)
            elif kind == "Call":
                helper_include = self._module_name_to_cpp_include(
                    _CPP_HELPER_MODULE_BY_RUNTIME_CALL.get(dict_any_get_str(d2, "runtime_call"), "")
                )
                if helper_include != "":
                    out.add(helper_include)
                func_node = self.any_to_dict_or_empty(d2.get("func"))
                if self._node_kind_from_dict(func_node) == "Name":
                    helper_include = self._module_name_to_cpp_include(
                        _CPP_HELPER_MODULE_BY_DIRECT_CALL.get(dict_any_get_str(func_node, "id"), "")
                    )
                    if helper_include != "":
                        out.add(helper_include)
            elif kind == "Compare":
                if dict_any_get_str(d2, "lowered_kind") == "Contains":
                    helper_include = self._module_name_to_cpp_include("pytra.built_in.contains")
                    if helper_include != "":
                        out.add(helper_include)
                else:
                    for op_name in self.any_to_str_list(d2.get("ops")):
                        if op_name in {"In", "NotIn"}:
                            helper_include = self._module_name_to_cpp_include("pytra.built_in.contains")
                            if helper_include != "":
                                out.add(helper_include)
                            break
            elif kind == "BinOp" and dict_any_get_str(d2, "op") == "Mult":
                left_t = self.normalize_type_name(self.get_expr_type(d2.get("left")))
                right_t = self.normalize_type_name(self.get_expr_type(d2.get("right")))
                left_is_repeatable = left_t == "str" or self.is_list_type(left_t)
                right_is_repeatable = right_t == "str" or self.is_list_type(right_t)
                if (left_is_repeatable and right_t in _CPP_REPEAT_INT_TYPES) or (
                    right_is_repeatable and left_t in _CPP_REPEAT_INT_TYPES
                ):
                    helper_include = self._module_name_to_cpp_include("pytra.built_in.sequence")
                    if helper_include != "":
                        out.add(helper_include)
            for value in d2.values():
                self._collect_cpp_helper_includes_from_node(value, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_cpp_helper_includes_from_node(item, out)

    def _module_attr_runtime_module_from_node(self, node: dict[str, Any]) -> str:
        """module attr access が別 runtime module を指す場合、その module_id を返す。"""
        if self._node_kind_from_dict(node) != "Attribute":
            return ""
        owner_node = self.any_to_dict_or_empty(node.get("value"))
        owner_name = self._raw_dotted_owner_name(owner_node)
        if owner_name == "":
            return ""
        owner_module = self._resolve_imported_module_name(owner_name)
        if owner_module == "":
            return ""
        attr = self.attr_name(node)
        if attr == "":
            return ""
        mapped = self._lookup_module_attr_runtime_call(owner_module, attr)
        if mapped != "":
            mapped_module = self._cpp_expr_to_module_name(mapped)
            if mapped_module != "":
                return mapped_module
            if self._contains_text(mapped, "::"):
                mapped_prefix = mapped.rsplit("::", 1)[0]
                mapped_module = self._cpp_expr_to_module_name(mapped_prefix)
                if mapped_module != "":
                    return mapped_module
        ns = self._module_name_to_cpp_namespace(owner_module)
        if ns != "":
            return self._cpp_expr_to_module_name(ns + "::" + attr)
        return ""

    def _body_references_process_runtime(self, body: list[Any]) -> bool:
        """body 内で process_runtime.h が必要な参照があるか判定する。"""
        import json as _json
        body_txt = _json.dumps(body, default=str, ensure_ascii=False)
        return "sys.argv" in body_txt or "pytra.std.sys" in body_txt or "py_runtime_argv" in body_txt

    def _body_references_scope_exit(self, body: list[Any]) -> bool:
        """body 内で scope_exit.h が必要な参照（try/finally）があるか判定する。"""
        import json as _json
        body_txt = _json.dumps(body, default=str, ensure_ascii=False)
        return '"Try"' in body_txt

    def _includes_from_resolved_dependencies(self, deps: list[object], body: list[dict[str, Any]]) -> list[str]:
        """Convert linker-resolved module IDs to C++ include paths."""
        includes: list[str] = []
        seen: set[str] = set()
        for dep in deps:
            if not isinstance(dep, str) or dep == "":
                continue
            inc = self._module_name_to_cpp_include(dep)
            if inc != "" and inc not in seen:
                seen.add(inc)
                includes.append(inc)
        # Helper includes (C++ specific: RuntimeSpecialOp, PathRuntimeOp, etc.)
        # These are language-specific and stay in the emitter.
        scan_nodes: list[dict[str, Any]] = list(body)
        raw_main_guard = self.any_dict_get_list(self.doc, "main_guard_body")
        if isinstance(raw_main_guard, list):
            for item in raw_main_guard:
                if isinstance(item, dict):
                    scan_nodes.append(item)
        helper_includes: set[str] = set()
        for stmt in scan_nodes:
            self._collect_cpp_helper_includes_from_node(stmt, helper_includes)
        for inc in sorted(helper_includes):
            append_unique_non_empty(includes, seen, inc)
        return sort_str_list_copy(includes)

    def _collect_import_cpp_includes(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """EAST body から必要な C++ include を収集する。"""
        # If linker has resolved dependencies, use them directly.
        linked_meta = dict_any_get_dict(meta, "linked_program_v1")
        resolved_deps = linked_meta.get("resolved_dependencies_v1") if isinstance(linked_meta, dict) else None
        if isinstance(resolved_deps, list) and len(resolved_deps) > 0:
            return self._includes_from_resolved_dependencies(resolved_deps, body)
        # Fallback: legacy emitter-side include resolution.
        includes: list[str] = []
        seen: set[str] = set()
        scan_nodes: list[dict[str, Any]] = list(body)
        raw_main_guard = self.any_dict_get_list(self.doc, "main_guard_body")
        if isinstance(raw_main_guard, list):
            for item in raw_main_guard:
                if isinstance(item, dict):
                    scan_nodes.append(item)
        bindings = dict_any_get_dict_list(meta, "import_bindings")
        if len(bindings) > 0:
            for item in bindings:
                mod_name = dict_any_get_str(item, "module_id")
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                append_unique_non_empty(includes, seen, self._import_binding_cpp_include(item))
        else:
            for stmt in scan_nodes:
                kind = self._node_kind_from_dict(stmt)
                if kind == "Import":
                    for ent in self._dict_stmt_list(stmt.get("names")):
                        append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(dict_any_get_str(ent, "name")))
                elif kind == "ImportFrom":
                    mod_name = dict_any_get_str(stmt, "module")
                    append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                    for ent in self._dict_stmt_list(stmt.get("names")):
                        binding: dict[str, Any] = {
                            "module_id": mod_name,
                            "export_name": dict_any_get_str(ent, "name"),
                            "binding_kind": "symbol",
                        }
                        append_unique_non_empty(includes, seen, self._import_binding_cpp_include(binding))
        runtime_modules: set[str] = set()
        for stmt in scan_nodes:
            self._collect_runtime_modules_from_node(stmt, runtime_modules)
        for module_id in sorted(runtime_modules):
            if lookup_runtime_module_group(module_id) == "core":
                continue
            append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(module_id))
        helper_includes: set[str] = set()
        for stmt in scan_nodes:
            self._collect_cpp_helper_includes_from_node(stmt, helper_includes)
        for inc in sorted(helper_includes):
            append_unique_non_empty(includes, seen, inc)
        return sort_str_list_copy(includes)

    def _seed_import_maps_from_meta(self) -> None:
        """`meta.import_bindings`（または互換メタ）から import 束縛マップを初期化する。"""
        meta = dict_any_get_dict(self.doc, "meta")
        self.load_import_bindings_from_meta(meta)

    def emit_block_comment(self, text: str) -> None:
        """Emit docstring/comment as C-style block comment."""
        self.emit("/* " + text + " */")

    def _module_source_path_for_name(self, module_name: str) -> Path:
        """`pytra.*` モジュール名から runtime source `.py` パスを返す（未解決時は空 Path）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if module_name_norm.startswith("pytra.std."):
            tail: str = str(module_name_norm[10:].replace(".", "/"))
            std_root_txt: str = str(RUNTIME_STD_SOURCE_ROOT)
            p_txt: str = std_root_txt + "/" + tail + ".py"
            p = Path(p_txt)
            if p.exists():
                return p
            init_txt: str = std_root_txt + "/" + tail + "/__init__.py"
            init_p = Path(init_txt)
            if init_p.exists():
                return init_p
            return Path("")
        if module_name_norm.startswith("pytra.utils."):
            tail = str(module_name_norm[12:].replace(".", "/"))
            utils_root_txt = str(RUNTIME_UTILS_SOURCE_ROOT)
            p_txt = utils_root_txt + "/" + tail + ".py"
            p = Path(p_txt)
            if p.exists():
                return p
            init_txt = utils_root_txt + "/" + tail + "/__init__.py"
            init_p = Path(init_txt)
            if init_p.exists():
                return init_p
            return Path("")
        if module_name_norm.startswith("pytra.built_in."):
            tail = str(module_name_norm[15:].replace(".", "/"))
            built_in_root_txt = str(RUNTIME_BUILT_IN_SOURCE_ROOT)
            p_txt = built_in_root_txt + "/" + tail + ".py"
            p = Path(p_txt)
            if p.exists():
                return p
            init_txt = built_in_root_txt + "/" + tail + "/__init__.py"
            init_p = Path(init_txt)
            if init_p.exists():
                return init_p
            return Path("")
        return Path("")

    def _module_class_signature_docs_from_east(
        self,
        module_name: str,
        east_doc: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """EAST doc から class/method シグネチャを抽出する。"""
        out: dict[str, dict[str, Any]] = {}
        body = east_doc.get("body")
        stmts = body if isinstance(body, list) else []
        ns = self._module_name_to_cpp_namespace(module_name)
        for stmt in stmts:
            if not isinstance(stmt, dict) or stmt.get("kind") != "ClassDef":
                continue
            class_name = dict_any_get_str(stmt, "name")
            if class_name == "":
                continue
            cpp_name = f"{ns}::{class_name}" if ns != "" else class_name
            class_index_doc = self._build_user_class_index().get((module_name, class_name), {})
            methods = stmt.get("body")
            method_stmts = methods if isinstance(methods, list) else []
            method_arg_names: dict[str, list[str]] = {}
            method_arg_types: dict[str, list[str]] = {}
            method_arg_defaults: dict[str, dict[str, Any]] = {}
            method_returns: dict[str, str] = {}
            method_names: set[str] = set()
            field_types: dict[str, str] = {}
            raw_field_types = stmt.get("field_types")
            field_types_map = raw_field_types if isinstance(raw_field_types, dict) else {}
            for raw_attr, raw_ft in field_types_map.items():
                if not isinstance(raw_attr, str) or raw_attr == "":
                    continue
                field_t = self.normalize_type_name(self.any_to_str(raw_ft))
                if field_t != "":
                    field_types[raw_attr] = field_t
            for method_stmt in method_stmts:
                if not isinstance(method_stmt, dict) or method_stmt.get("kind") != "FunctionDef":
                    continue
                method_name = dict_any_get_str(method_stmt, "name")
                if method_name == "":
                    continue
                method_names.add(method_name)
                method_returns[method_name] = self.normalize_type_name(self.any_to_str(method_stmt.get("return_type")))
                arg_types = method_stmt.get("arg_types")
                arg_types_map = arg_types if isinstance(arg_types, dict) else {}
                arg_defaults = method_stmt.get("arg_defaults")
                arg_defaults_map = arg_defaults if isinstance(arg_defaults, dict) else {}
                arg_order = method_stmt.get("arg_order")
                arg_order_list = arg_order if isinstance(arg_order, list) else []
                ordered_names: list[str] = []
                ordered_types: list[str] = []
                ordered_defaults: dict[str, Any] = {}
                for raw_arg in arg_order_list:
                    if not isinstance(raw_arg, str) or raw_arg == "self":
                        continue
                    ordered_names.append(raw_arg)
                    ordered_types.append(
                        self._normalize_user_class_signature_arg_type(
                            module_name,
                            east_doc,
                            self.any_to_str(arg_types_map.get(raw_arg)),
                        )
                    )
                    if raw_arg in arg_defaults_map:
                        ordered_defaults[raw_arg] = arg_defaults_map.get(raw_arg)
                method_arg_names[method_name] = ordered_names
                method_arg_types[method_name] = ordered_types
                method_arg_defaults[method_name] = ordered_defaults
            raw_hint = dict_any_get_str(stmt, "class_storage_hint", "ref")
            effective_hint = self._effective_user_class_storage_hint(module_name, class_name, raw_hint)
            out[class_name] = {
                "storage_hint": effective_hint,
                "cpp_name": cpp_name,
                "base_cpp_name": self.any_to_str(class_index_doc.get("base_cpp_name")),
                "method_arg_names": method_arg_names,
                "method_arg_types": method_arg_types,
                "method_arg_defaults": method_arg_defaults,
                "method_returns": method_returns,
                "method_names": sorted(method_names),
                "field_types": field_types,
            }
        return out

    def _module_generated_header_path(self, module_name: str) -> Path:
        """runtime module の generated header パスを返す（未解決時は空 Path）。"""
        src_path = self._module_source_path_for_name(module_name)
        if str(src_path) in {"", "."}:
            return Path("")
        prefix = ""
        rel_path = Path("")
        try:
            rel_path = src_path.relative_to(RUNTIME_STD_SOURCE_ROOT)
            prefix = "std"
        except ValueError:
            try:
                rel_path = src_path.relative_to(RUNTIME_UTILS_SOURCE_ROOT)
                prefix = "utils"
            except ValueError:
                try:
                    rel_path = src_path.relative_to(RUNTIME_BUILT_IN_SOURCE_ROOT)
                    prefix = "built_in"
                except ValueError:
                    return Path("")
        if rel_path.name == "__init__.py":
            rel_no_suffix = rel_path.parent
        else:
            rel_no_suffix = rel_path.with_suffix("")
        return RUNTIME_CPP_GENERATED_ROOT / prefix / rel_no_suffix.with_suffix(".h")

    def _module_class_signature_docs(self, module_name: str) -> dict[str, dict[str, Any]]:
        """runtime module の class/method シグネチャを SoT から抽出する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_class_signature_cache.get(module_name_norm)
        if isinstance(cached, dict):
            return cached
        # sentinel: 再帰呼び出しで無限ループしないよう、空 dict を先行キャッシュする。
        out: dict[str, dict[str, Any]] = {}
        self._module_class_signature_cache[module_name_norm] = out
        user_module_docs = getattr(self, "user_module_east_map", {})
        if isinstance(user_module_docs, dict):
            east_doc = user_module_docs.get(module_name_norm)
            if isinstance(east_doc, dict) and len(east_doc) > 0:
                out = self._module_class_signature_docs_from_east(module_name_norm, east_doc)
                self._module_class_signature_cache[module_name_norm] = out
                return out
        src_path = self._module_source_path_for_name(module_name_norm)
        if str(src_path) == "":
            self._module_class_signature_cache[module_name_norm] = out
            return out
        try:
            east = load_east_document(src_path)
        except Exception:
            self._module_class_signature_cache[module_name_norm] = out
            return out
        out = self._module_class_signature_docs_from_east(module_name_norm, east)
        self._module_class_signature_cache[module_name_norm] = out
        return out

    def _module_class_doc(self, module_name: str, class_name: str) -> dict[str, Any]:
        return self._module_class_doc_inner(module_name, class_name, set())

    def _module_class_doc_inner(
        self,
        module_name: str,
        class_name: str,
        seen: set[tuple[str, str]],
    ) -> dict[str, Any]:
        module_name_norm = self._normalize_runtime_module_name(module_name)
        if class_name == "":
            return {}
        cache_key = (module_name_norm, class_name)
        if cache_key in seen:
            return {}
        seen.add(cache_key)
        docs = self._module_class_signature_docs(module_name)
        doc = docs.get(class_name)
        if isinstance(doc, dict):
            return doc
        user_module_docs = getattr(self, "user_module_east_map", {})
        east_doc: dict[str, Any] = {}
        if isinstance(user_module_docs, dict):
            east_any = user_module_docs.get(module_name_norm)
            if isinstance(east_any, dict):
                east_doc = east_any
        if len(east_doc) == 0:
            src_path = self._module_source_path_for_name(module_name_norm)
            if str(src_path) not in {"", "."}:
                try:
                    loaded = load_east_document(src_path)
                    if isinstance(loaded, dict):
                        east_doc = loaded
                except Exception:
                    east_doc = {}
        meta = self.any_to_dict_or_empty(east_doc.get("meta"))
        import_symbols = self.any_to_dict_or_empty(meta.get("import_symbols"))
        imported = self.any_to_dict_or_empty(import_symbols.get(class_name))
        imported_module = dict_any_get_str(imported, "module")
        imported_name = dict_any_get_str(imported, "name")
        if imported_module != "" and imported_name != "":
            imported_doc = self._module_class_doc_inner(imported_module, imported_name, seen)
            if len(imported_doc) > 0:
                return imported_doc
        resolution = self.any_to_dict_or_empty(meta.get("import_resolution"))
        bindings = self.any_to_dict_list(resolution.get("bindings"))
        for binding in bindings:
            local_name = dict_any_get_str(binding, "local_name")
            export_name = dict_any_get_str(binding, "export_name")
            if class_name not in {local_name, export_name}:
                continue
            target_module = dict_any_get_str(binding, "runtime_module_id")
            if target_module == "":
                target_module = dict_any_get_str(binding, "source_module_id")
            if target_module == "":
                target_module = dict_any_get_str(binding, "module_id")
            target_name = dict_any_get_str(binding, "runtime_symbol")
            if target_name == "":
                target_name = dict_any_get_str(binding, "source_export_name")
            if target_name == "":
                target_name = export_name
            if target_module == "" or target_name == "":
                continue
            rebound_doc = self._module_class_doc_inner(target_module, target_name, seen)
            if len(rebound_doc) > 0:
                return rebound_doc
        return {}

    def _imported_runtime_class_cpp_type(self, module_name: str, class_name: str) -> str:
        module_name = self._resolve_class_doc_module_name(module_name, class_name)
        doc = self._module_class_doc(module_name, class_name)
        cpp_name = self.any_to_str(doc.get("cpp_name"))
        if cpp_name == "":
            return ""
        hint = self.any_to_str(doc.get("storage_hint"))
        if hint == "value":
            return cpp_name
        return f"rc<{cpp_name}>"

    def _resolve_imported_symbol_class_cpp_type(self, symbol_name: str) -> str:
        """from-import 済み class symbol を runtime class の C++ 型へ解決する。"""
        symbol_norm = self.normalize_type_name(symbol_name)
        if symbol_norm == "":
            return ""
        imported = self._resolve_imported_symbol(symbol_norm)
        module_name = self.any_dict_get_str(imported, "module", "")
        class_name = self.any_dict_get_str(imported, "name", "")
        if module_name == "" or class_name == "":
            return ""
        return self._imported_runtime_class_cpp_type(module_name, class_name)

    def _module_class_method_arg_names(self, module_name: str, class_name: str, method_name: str) -> list[str]:
        module_name = self._resolve_class_doc_module_name(module_name, class_name)
        doc = self._module_class_doc(module_name, class_name)
        items = doc.get("method_arg_names")
        method_map = items if isinstance(items, dict) else {}
        names = method_map.get(method_name)
        if not isinstance(names, list):
            return []
        out: list[str] = []
        for item in names:
            if isinstance(item, str) and item != "":
                out.append(item)
        return out

    def _module_class_method_arg_types(self, module_name: str, class_name: str, method_name: str) -> list[str]:
        module_name = self._resolve_class_doc_module_name(module_name, class_name)
        doc = self._module_class_doc(module_name, class_name)
        items = doc.get("method_arg_types")
        method_map = items if isinstance(items, dict) else {}
        types = method_map.get(method_name)
        if not isinstance(types, list):
            return []
        out: list[str] = []
        for item in types:
            if isinstance(item, str) and item != "":
                out.append(item)
        return out

    def _module_class_method_arg_defaults(self, module_name: str, class_name: str, method_name: str) -> dict[str, Any]:
        module_name = self._resolve_class_doc_module_name(module_name, class_name)
        doc = self._module_class_doc(module_name, class_name)
        items = doc.get("method_arg_defaults")
        method_map = items if isinstance(items, dict) else {}
        defaults = method_map.get(method_name)
        if isinstance(defaults, dict):
            return defaults
        return {}

    def _register_imported_runtime_class_metadata(self) -> None:
        """from-import された runtime class の型/メソッド情報を emitter へ注入する。"""
        for local_name, sym in self.import_symbols.items():
            if not isinstance(local_name, str) or local_name == "":
                continue
            module_name = dict_any_get_str(sym, "module")
            class_name = dict_any_get_str(sym, "name")
            module_name = self._resolve_class_doc_module_name(module_name, class_name)
            cpp_type = self._imported_runtime_class_cpp_type(module_name, class_name)
            if cpp_type == "":
                continue
            self.type_map[local_name] = cpp_type
            doc = self._module_class_doc(module_name, class_name)
            cpp_name = self.any_to_str(doc.get("cpp_name"))
            if cpp_name == "":
                continue
            method_names_raw = doc.get("method_names")
            method_names = method_names_raw if isinstance(method_names_raw, list) else []
            name_set: set[str] = set()
            for item in method_names:
                if isinstance(item, str) and item != "":
                    name_set.add(item)
            self.class_names.add(cpp_name)
            storage_hint = self.any_to_str(doc.get("storage_hint"))
            if storage_hint not in {"value", "ref"}:
                storage_hint = "ref"
            self.class_storage_hints[cpp_name] = storage_hint
            if storage_hint == "value":
                self.value_classes.add(cpp_name)
            else:
                self.ref_classes.add(cpp_name)
            self.class_method_names[cpp_name] = name_set
            self.class_method_arg_names[cpp_name] = dict(doc.get("method_arg_names", {}))
            self.class_method_arg_types[cpp_name] = dict(doc.get("method_arg_types", {}))
            self.class_method_arg_defaults[cpp_name] = dict(doc.get("method_arg_defaults", {}))
            self.class_method_return_types[cpp_name] = dict(doc.get("method_returns", {}))
            base_cpp_name = self.any_to_str(doc.get("base_cpp_name"))
            if base_cpp_name != "":
                self.class_base[cpp_name] = base_cpp_name
            field_types_raw = doc.get("field_types")
            field_types = field_types_raw if isinstance(field_types_raw, dict) else {}
            class_field_types: dict[str, str] = {}
            for raw_attr, raw_ft in field_types.items():
                if not isinstance(raw_attr, str) or raw_attr == "":
                    continue
                field_t = self.normalize_type_name(self.any_to_str(raw_ft))
                if field_t != "":
                    class_field_types[raw_attr] = field_t
            self.class_field_types[cpp_name] = class_field_types

    def _module_function_arg_types(self, module_name: str, fn_name: str) -> list[str]:
        """モジュール関数の引数型列を返す（不明時は空 list）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_fn_arg_type_cache.get(module_name_norm)
        if isinstance(cached, dict):
            sig = cached.get(fn_name)
            if isinstance(sig, list):
                return sig
            return []
        fn_map: dict[str, list[str]] = {}
        src_path: Path = self._module_source_path_for_name(module_name_norm)
        if str(src_path) == "":
            self._module_fn_arg_type_cache[module_name_norm] = fn_map
            return []
        fn_map = extract_function_arg_types_from_python_source(src_path)
        self._module_fn_arg_type_cache[module_name_norm] = fn_map
        sig = fn_map.get(fn_name)
        if isinstance(sig, list):
            return sig
        return []

    def _module_function_return_type(self, module_name: str, fn_name: str) -> str:
        """モジュール関数の返り値型を返す（不明時は空文字）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_fn_return_type_cache.get(module_name_norm)
        if not isinstance(cached, dict):
            ret_map: dict[str, str] = {}
            src_path = self._module_source_path_for_name(module_name_norm)
            if str(src_path) not in {"", "."}:
                try:
                    east = load_east_document(src_path)
                    for stmt in self.any_to_list(east.get("body")):
                        stmt_d = stmt if isinstance(stmt, dict) else {}
                        if self._node_kind_from_dict(stmt_d) != "FunctionDef":
                            continue
                        name = dict_any_get_str(stmt_d, "name")
                        if name == "":
                            continue
                        ret_map[name] = self.normalize_type_name(self.any_to_str(stmt_d.get("return_type")))
                except Exception:
                    ret_map = {}
            self._module_fn_return_type_cache[module_name_norm] = ret_map
            cached = ret_map
        return self.normalize_type_name(self.any_to_str(cached.get(fn_name, "")))

    def _module_function_cpp_signature_docs(self, module_name: str) -> dict[str, dict[str, Any]]:
        """generated header から module function の C++ 実シグネチャを抽出する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_fn_cpp_signature_cache.get(module_name_norm)
        if isinstance(cached, dict):
            return cached
        docs: dict[str, dict[str, Any]] = {}
        hdr_path = self._module_generated_header_path(module_name_norm)
        if str(hdr_path) in {"", "."} or not hdr_path.exists():
            self._module_fn_cpp_signature_cache[module_name_norm] = docs
            return docs
        try:
            for raw_line in hdr_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line.endswith(";") or "(" not in line or ")" not in line:
                    continue
                line = line[:-1]
                before, after = line.split("(", 1)
                params_txt = after.rsplit(")", 1)[0]
                before_txt = before.strip()
                fn_name = before_txt.split(" ")[-1].strip()
                if fn_name == "":
                    continue
                ret_cpp = before_txt[: before_txt.rfind(fn_name)].strip()
                arg_cpp_types: list[str] = []
                for param in split_top_level_csv(params_txt):
                    param_txt = param.strip()
                    if param_txt == "":
                        continue
                    arg_cpp_types.append(param_txt.split("=", 1)[0].strip())
                docs[fn_name] = {
                    "arg_cpp_types": arg_cpp_types,
                    "return_cpp_type": ret_cpp,
                }
        except Exception:
            docs = {}
        self._module_fn_cpp_signature_cache[module_name_norm] = docs
        return docs

    def _module_function_cpp_arg_types(self, module_name: str, fn_name: str) -> list[str]:
        doc = self._module_function_cpp_signature_docs(module_name).get(fn_name)
        if not isinstance(doc, dict):
            return []
        raw = doc.get("arg_cpp_types")
        if not isinstance(raw, list):
            return []
        out: list[str] = []
        for item in raw:
            if isinstance(item, str):
                out.append(item)
        return out

    def _module_function_cpp_return_type(self, module_name: str, fn_name: str) -> str:
        doc = self._module_function_cpp_signature_docs(module_name).get(fn_name)
        if not isinstance(doc, dict):
            return ""
        return self.any_to_str(doc.get("return_cpp_type"))

    def _module_function_arg_names(self, module_name: str, fn_name: str) -> list[str]:
        """モジュール関数の引数名列を返す（不明時は空 list）。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_fn_signature_cache.get(module_name_norm)
        if not isinstance(cached, dict):
            sig_map: dict[str, dict[str, list[str]]] = {}
            src_path: Path = self._module_source_path_for_name(module_name_norm)
            if str(src_path) != "":
                sig_map = extract_function_signatures_from_python_source(src_path)
            self._module_fn_signature_cache[module_name_norm] = sig_map
            cached = sig_map
        sig = cached.get(fn_name)
        if not isinstance(sig, dict):
            return []
        names = sig.get("arg_names")
        if not isinstance(names, list):
            return []
        out: list[str] = []
        for name_obj in names:
            if isinstance(name_obj, str):
                name_txt = name_obj.strip()
                if name_txt != "":
                    out.append(name_txt)
        return out

    def _coerce_args_for_module_function(
        self,
        module_name: str,
        fn_name: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """モジュール関数シグネチャに基づいて引数を必要最小限で coercion する。"""
        # py_assert_* は S6 で template 化済みのため boxing 不要
        if fn_name.startswith("py_assert_"):
            return args
        target_types = self._module_function_arg_types(module_name, fn_name)
        if len(target_types) == 0:
            return args
        cpp_arg_types = self._module_function_cpp_arg_types(module_name, fn_name)
        out: list[str] = []
        for i, arg in enumerate(args):
            if i >= len(target_types):
                out.append(arg)
                continue
            arg_node = arg_nodes[i] if i < len(arg_nodes) else {}
            list_target_is_value = True
            if i < len(cpp_arg_types):
                cpp_arg_t = cpp_arg_types[i]
                if "rc<list<" in cpp_arg_t:
                    list_target_is_value = False
            out.append(
                self._coerce_call_arg(
                    arg,
                    arg_node,
                    target_types[i],
                    list_target_is_value=list_target_is_value,
                )
            )
        return out

    def _is_module_definition_stmt(self, stmt: dict[str, Any]) -> bool:
        """トップレベルで namespace 直下に置ける定義文かを返す。"""
        kind = self._node_kind_from_dict(stmt)
        return kind in {"ClassDef", "FunctionDef", "Import", "ImportFrom", "TypeAlias"}

    def _is_module_noop_stmt(self, stmt: dict[str, Any]) -> bool:
        """トップレベル runtime を汚さない no-op 文かを返す。"""
        kind = self._node_kind_from_dict(stmt)
        if kind == "Pass":
            return True
        if kind != "Expr":
            return False
        value = self.any_to_dict_or_empty(stmt.get("value"))
        if self._node_kind_from_dict(value) != "Constant":
            return False
        return isinstance(value.get("value"), str)

    def _split_module_top_level_stmts(
        self,
        body: list[dict[str, Any]],
    ) -> tuple[list[Any], list[Any]]:
        """トップレベル文を「定義文」と「実行文」へ分割する。"""
        defs: list[Any] = []
        runtime: list[Any] = []
        for stmt in body:
            if self._is_module_definition_stmt(stmt) or self._is_module_noop_stmt(stmt):
                defs.append(stmt)
            else:
                runtime.append(stmt)
        return defs, runtime

    def _infer_module_global_decl_type(self, stmt: dict[str, Any]) -> str:
        """トップレベル Name 代入を global 宣言する際の型を推定する。"""
        kind = self._node_kind_from_dict(stmt)
        if kind == "AnnAssign":
            ann_t = self.normalize_type_name(self.any_to_str(stmt.get("annotation")))
            if ann_t not in {"", "unknown"}:
                return ann_t
        d0 = self.normalize_type_name(self.any_dict_get_str(stmt, "decl_type", ""))
        d1 = self.normalize_type_name(self.get_expr_type(stmt.get("target")))
        d2 = self.normalize_type_name(self.get_expr_type(stmt.get("value")))
        picked = ""
        for t in [d0, d1, d2]:
            if t not in {"", "unknown"}:
                picked = t
                break
        if picked == "":
            picked = d2 if d2 != "" else (d1 if d1 != "" else d0)
        picked = "Any" if picked == "None" else picked
        picked = picked if picked != "" else "object"
        return picked

    def _collect_module_global_decls(self, runtime_stmts: list[Any]) -> list[tuple[str, str]]:
        """トップレベル実行文から global 先行宣言すべき Name と型を抽出する。"""
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt_any in runtime_stmts:
            stmt = self.any_to_dict_or_empty(stmt_any)
            if len(stmt) == 0:
                continue
            kind = self._node_kind_from_dict(stmt)
            if kind not in {"Assign", "AnnAssign"}:
                continue
            target_obj: object = stmt.get("target")
            if not self.is_plain_name_expr(target_obj):
                continue
            target = self.any_to_dict_or_empty(target_obj)
            raw_name = self.any_dict_get_str(target, "id", "")
            if raw_name == "":
                continue
            name = self.rename_if_reserved(raw_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            if name in seen:
                continue
            ty = self._infer_module_global_decl_type(stmt)
            cpp_t = self._cpp_type_text(ty)
            if cpp_t == "auto":
                continue
            seen.add(name)
            out.append((name, ty))
        return out

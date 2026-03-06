from __future__ import annotations

from pathlib import Path

from typing import Any
from backends.cpp.emitter.runtime_paths import (
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
    sort_str_list_copy,
)


RUNTIME_STD_SOURCE_ROOT = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT = Path("src/pytra/utils")
TOOLCHAIN_COMPILER_PREFIX = "toolchain.compiler."
TOOLCHAIN_COMPILER_PREFIX_LEN = len(TOOLCHAIN_COMPILER_PREFIX)


class CppModuleEmitter:
    """Import/include/namespace/module-init helpers extracted from CppEmitter."""

    def _normalize_runtime_module_name(self, module_name: str) -> str:
        module_name_norm = module_name
        if module_name_norm.find(".") < 0:
            bare_src = RUNTIME_STD_SOURCE_ROOT / (module_name_norm.replace(".", "/") + ".py")
            if bare_src.exists():
                return "pytra.std." + module_name_norm
        return module_name_norm

    def _module_name_to_cpp_include(self, module_name: str) -> str:
        """Python import モジュール名を C++ include へ解決する。"""
        return _module_name_to_cpp_include_impl(module_name)

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """Python import モジュール名を C++ namespace へ解決する。"""
        module_name_norm = module_name
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
            module_id = dict_any_get_str(node, "runtime_module_id")
            if module_id != "":
                out.add(module_id)
            for value in node.values():
                self._collect_runtime_modules_from_node(value, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_runtime_modules_from_node(item, out)

    def _collect_import_cpp_includes(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """EAST body から必要な C++ include を収集する。"""
        includes: list[str] = []
        seen: set[str] = set()
        bindings = dict_any_get_dict_list(meta, "import_bindings")
        if len(bindings) > 0:
            for item in bindings:
                mod_name = dict_any_get_str(item, "module_id")
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                append_unique_non_empty(includes, seen, self._import_binding_cpp_include(item))
        else:
            for stmt in body:
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
        for stmt in body:
            self._collect_runtime_modules_from_node(stmt, runtime_modules)
        for module_id in sorted(runtime_modules):
            if lookup_runtime_module_group(module_id) == "core":
                continue
            append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(module_id))
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
        return Path("")

    def _module_class_signature_docs(self, module_name: str) -> dict[str, dict[str, Any]]:
        """runtime module の class/method シグネチャを SoT から抽出する。"""
        module_name_norm = self._normalize_runtime_module_name(module_name)
        cached = self._module_class_signature_cache.get(module_name_norm)
        if isinstance(cached, dict):
            return cached
        out: dict[str, dict[str, Any]] = {}
        src_path = self._module_source_path_for_name(module_name_norm)
        if str(src_path) == "":
            self._module_class_signature_cache[module_name_norm] = out
            return out
        try:
            east = load_east_document(src_path)
        except Exception:
            self._module_class_signature_cache[module_name_norm] = out
            return out
        body = east.get("body")
        stmts = body if isinstance(body, list) else []
        ns = self._module_name_to_cpp_namespace(module_name_norm)
        for stmt in stmts:
            if not isinstance(stmt, dict) or stmt.get("kind") != "ClassDef":
                continue
            class_name = dict_any_get_str(stmt, "name")
            if class_name == "":
                continue
            cpp_name = f"{ns}::{class_name}" if ns != "" else class_name
            methods = stmt.get("body")
            method_stmts = methods if isinstance(methods, list) else []
            method_arg_names: dict[str, list[str]] = {}
            method_arg_types: dict[str, list[str]] = {}
            method_arg_defaults: dict[str, dict[str, Any]] = {}
            method_returns: dict[str, str] = {}
            method_names: set[str] = set()
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
                    ordered_types.append(self.normalize_type_name(self.any_to_str(arg_types_map.get(raw_arg))))
                    if raw_arg in arg_defaults_map:
                        ordered_defaults[raw_arg] = arg_defaults_map.get(raw_arg)
                method_arg_names[method_name] = ordered_names
                method_arg_types[method_name] = ordered_types
                method_arg_defaults[method_name] = ordered_defaults
            out[class_name] = {
                "storage_hint": dict_any_get_str(stmt, "class_storage_hint", "ref"),
                "cpp_name": cpp_name,
                "method_arg_names": method_arg_names,
                "method_arg_types": method_arg_types,
                "method_arg_defaults": method_arg_defaults,
                "method_returns": method_returns,
                "method_names": sorted(method_names),
            }
        self._module_class_signature_cache[module_name_norm] = out
        return out

    def _module_class_doc(self, module_name: str, class_name: str) -> dict[str, Any]:
        docs = self._module_class_signature_docs(module_name)
        doc = docs.get(class_name)
        if isinstance(doc, dict):
            return doc
        return {}

    def _imported_runtime_class_cpp_type(self, module_name: str, class_name: str) -> str:
        doc = self._module_class_doc(module_name, class_name)
        cpp_name = self.any_to_str(doc.get("cpp_name"))
        if cpp_name == "":
            return ""
        hint = self.any_to_str(doc.get("storage_hint"))
        if hint == "value":
            return cpp_name
        return f"rc<{cpp_name}>"

    def _module_class_method_arg_names(self, module_name: str, class_name: str, method_name: str) -> list[str]:
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
            if self.any_to_str(doc.get("storage_hint")) == "value":
                self.value_classes.add(cpp_name)
            else:
                self.ref_classes.add(cpp_name)
            self.class_method_names[cpp_name] = name_set
            self.class_method_arg_names[cpp_name] = dict(doc.get("method_arg_names", {}))
            self.class_method_arg_types[cpp_name] = dict(doc.get("method_arg_types", {}))
            self.class_method_arg_defaults[cpp_name] = dict(doc.get("method_arg_defaults", {}))
            self.class_method_return_types[cpp_name] = dict(doc.get("method_returns", {}))

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
        """モジュール関数シグネチャに基づいて引数を必要最小限で boxing する。"""
        target_types = self._module_function_arg_types(module_name, fn_name)
        if len(target_types) == 0:
            return args
        out: list[str] = []
        for i, arg in enumerate(args):
            a = arg
            if i < len(target_types):
                tt = target_types[i]
                arg_t = "unknown"
                if i < len(arg_nodes):
                    arg_t_obj = self.get_expr_type(arg_nodes[i])
                    if isinstance(arg_t_obj, str):
                        arg_t = arg_t_obj
                arg_t = self.infer_rendered_arg_type(a, arg_t, self.declared_var_types)
                arg_is_unknown = arg_t == "" or arg_t == "unknown"
                arg_node = arg_nodes[i] if i < len(arg_nodes) else {}
                arg_node_d = arg_node if isinstance(arg_node, dict) else {}
                if self._uses_pyobj_rc_list_expr(arg_node) and tt.startswith("list[") and tt.endswith("]"):
                    a = f"rc_list_ref({a})"
                elif self.is_any_like_type(tt) and (arg_is_unknown or not self.is_any_like_type(arg_t)):
                    if not self.is_boxed_object_expr(a):
                        if len(arg_node_d) > 0:
                            a = self.render_expr(self._build_box_expr_node(arg_node))
                        else:
                            a = f"make_object({a})"
                elif self._can_runtime_cast_target(tt) and (arg_is_unknown or self.is_any_like_type(arg_t)):
                    t_norm = self.normalize_type_name(tt)
                    if len(arg_node_d) > 0:
                        a = self.render_expr(self._build_unbox_expr_node(arg_node, t_norm, f"module_arg:{t_norm}"))
                    else:
                        a = self._coerce_any_expr_to_target(a, tt, f"module_arg:{t_norm}")
            out.append(a)
        return out

    def _is_module_definition_stmt(self, stmt: dict[str, Any]) -> bool:
        """トップレベルで namespace 直下に置ける定義文かを返す。"""
        kind = self._node_kind_from_dict(stmt)
        return kind in {"ClassDef", "FunctionDef", "Import", "ImportFrom"}

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

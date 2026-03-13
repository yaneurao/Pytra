from __future__ import annotations

from typing import Any
from toolchain.compiler.transpile_cli import (
    join_str_list,
    looks_like_runtime_function_name,
    make_user_error,
)
from toolchain.frontends.runtime_symbol_index import resolve_import_binding_runtime_module


_PYOBJ_RUNTIME_LIST_BRIDGE_CONTEXTS = {
    "append": "append",
    "extend": "extend",
    "pop": "pop",
    "clear": "clear",
    "reverse": "reverse",
    "sort": "sort",
    "set_at": "set_at",
}


class CppCallEmitter:
    """Runtime-call / import / cast-related helpers split out from CppEmitter."""

    def _resolve_imported_symbol_cpp_target(self, module_name: str, symbol_name: str) -> tuple[str, str]:
        """Return the C++ target module/namespace for an imported symbol.

        This re-resolves frontend facade imports through the runtime symbol index so
        single-module transpile paths still reach the canonical runtime namespace.
        """
        target_module = module_name
        if module_name != "" and symbol_name != "":
            resolved_module = resolve_import_binding_runtime_module(module_name, symbol_name, "symbol")
            if resolved_module != "":
                target_module = resolved_module
        target_ns = self.module_namespace_map.get(target_module, "")
        if target_ns == "" and target_module != "":
            target_ns = self._module_name_to_cpp_namespace(target_module)
        return target_module, target_ns

    def _render_pyobj_runtime_list_bridge_ref(self, owner_expr: str, ctx: str) -> str:
        """Render the low-level object-list bridge used by pyobj runtime list fallbacks."""
        return f'obj_to_list_ref_or_raise({owner_expr}, "{ctx}")'

    def _pyobj_runtime_list_bridge_context(self, op: str) -> str:
        """Return the canonical object-list bridge helper label for the given operation."""
        ctx = _PYOBJ_RUNTIME_LIST_BRIDGE_CONTEXTS.get(op, "")
        if ctx == "":
            raise ValueError("unsupported pyobj runtime list bridge op: " + op)
        return ctx

    def _render_pyobj_runtime_list_bridge_ref_for_op(self, owner_expr: str, op: str) -> str:
        """Render the object-list bridge using the canonical per-operation helper label."""
        return self._render_pyobj_runtime_list_bridge_ref(
            owner_expr,
            self._pyobj_runtime_list_bridge_context(op),
        )

    def _render_json_decode_call(self, expr_d: dict[str, Any]) -> str:
        lowered_kind = self.any_dict_get_str(expr_d, "lowered_kind", "")
        if lowered_kind != "JsonDecodeCall":
            return ""
        semantic_tag = self.any_dict_get_str(expr_d, "semantic_tag", "")
        receiver_node = expr_d.get("json_decode_receiver")
        receiver_expr = self.render_expr(receiver_node)
        if receiver_expr == "":
            raise ValueError("JsonDecodeCall missing receiver")
        if semantic_tag == "json.value.as_obj":
            return f"{receiver_expr}.as_obj()"
        raise ValueError("unsupported JsonDecodeCall semantic tag: " + semantic_tag)

    def _lookup_module_attr_runtime_call(self, module_name: str, attr: str) -> str:
        """`module.attr` から runtime_call 名を引く（pytra.* は短縮名フォールバックしない）。"""
        owner_keys: list[str] = [module_name]
        short_name = self._last_dotted_name(module_name)
        # `pytra.*` は正規モジュール名で解決し、短縮名への暗黙フォールバックは使わない。
        if short_name != module_name and not module_name.startswith("pytra."):
            owner_keys.append(short_name)
        for owner_key in owner_keys:
            if owner_key in self.module_attr_call_map:
                owner_map = self.module_attr_call_map[owner_key]
                if attr in owner_map:
                    mapped = owner_map[attr]
                    if mapped:
                        return mapped
        return ""

    def _resolve_runtime_call_for_imported_symbol(self, module_name: str, symbol_name: str) -> str | None:
        """`from X import Y` で取り込まれた Y 呼び出しの runtime 名を返す。"""
        mapped = self._lookup_module_attr_runtime_call(module_name, symbol_name)
        if mapped:
            return mapped
        ns = self._module_name_to_cpp_namespace(module_name)
        if ns:
            return f"{ns}::{symbol_name}"
        return None

    def _resolve_or_render_imported_symbol_name_call(
        self,
        expr: dict[str, Any],
        raw_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> tuple[str | None, str]:
        """`Call(Name)` で import 済みシンボルを解決し、必要なら直接呼び出しへ変換する。"""
        raw = raw_name
        imported_module = ""
        has_import_context = raw != "" and not self.is_locally_declared(raw)
        if has_import_context:
            resolved = self._resolve_imported_symbol(raw)
            imported_module = self.any_dict_get_str(resolved, "module", "")
            if imported_module != "":
                raw = self.any_dict_get_str(resolved, "name", "") or raw
                imported_module, _ = self._resolve_imported_symbol_cpp_target(imported_module, raw)
        has_import_target = raw != "" and imported_module != ""
        if not has_import_target:
            return None, raw
        imported_class_cpp_type = self._imported_runtime_class_cpp_type(imported_module, raw)
        if imported_class_cpp_type != "":
            ctor_args = args
            ctor_arg_nodes = arg_nodes
            ctor_arg_names = self._module_class_method_arg_names(imported_module, raw, "__init__")
            ctor_arg_types = self._module_class_method_arg_types(imported_module, raw, "__init__")
            ctor_arg_defaults = self._module_class_method_arg_defaults(imported_module, raw, "__init__")
            if len(kw) > 0 and len(ctor_arg_names) > 0:
                ctor_args, ctor_arg_nodes = self._merge_args_with_kw_defaults(
                    args,
                    kw,
                    arg_nodes,
                    kw_nodes,
                    ctor_arg_names,
                    ctor_arg_defaults,
                    ctor_arg_types,
                )
            if len(ctor_arg_types) > 0:
                ctor_args = self._coerce_args_by_signature(ctor_args, ctor_arg_nodes, ctor_arg_types)
            ctor_cpp_name = self._strip_rc_wrapper(imported_class_cpp_type)
            if imported_class_cpp_type.startswith("rc<"):
                return f"::rc_new<{ctor_cpp_name}>({join_str_list(', ', ctor_args)})", raw
            return f"{ctor_cpp_name}({join_str_list(', ', ctor_args)})", raw
        if imported_module == "collections" and raw == "deque":
            call_args = self.merge_call_args(args, kw)
            if len(kw) == 0:
                first_arg_node = arg_nodes[0] if len(arg_nodes) > 0 else expr
                rendered = self._render_collection_constructor_call("deque", expr, call_args, first_arg_node)
                if rendered is not None and rendered != "":
                    return rendered, raw
        runtime_module_id = self.any_dict_get_str(expr, "runtime_module_id", "")
        runtime_symbol = self.any_dict_get_str(expr, "runtime_symbol", "")
        if runtime_module_id != "" and runtime_symbol == raw:
            target_ns = self._module_name_to_cpp_namespace(runtime_module_id)
            if target_ns != "":
                call_args = self.merge_call_args(args, kw)
                call_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
                module_arg_names = self._module_function_arg_names(runtime_module_id, raw)
                if len(module_arg_names) > 0 and len(kw) > 0:
                    call_args = self._merge_args_with_kw_by_name(args, kw, module_arg_names)
                    call_arg_nodes = self._merge_arg_nodes_with_kw_by_name(arg_nodes, kw, kw_nodes, module_arg_names)
                namespaced = self._render_namespaced_module_call(
                    runtime_module_id,
                    target_ns,
                    raw,
                    call_args,
                    call_arg_nodes,
                )
                if namespaced is not None:
                    return namespaced, raw
        mapped_runtime_txt = self._resolve_runtime_call_for_imported_symbol(imported_module, raw) or ""
        route_runtime_call = (
            mapped_runtime_txt != ""
            and mapped_runtime_txt not in {"perf_counter", "Path"}
            and looks_like_runtime_function_name(mapped_runtime_txt)
        )
        if route_runtime_call:
            call_args = self.merge_call_args(args, kw)
            call_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
            module_arg_names = self._module_function_arg_names(imported_module, raw)
            if len(module_arg_names) > 0 and len(kw) > 0:
                call_args = self._merge_args_with_kw_by_name(args, kw, module_arg_names)
                call_arg_nodes = self._merge_arg_nodes_with_kw_by_name(arg_nodes, kw, kw_nodes, module_arg_names)
            if self._contains_text(mapped_runtime_txt, "::"):
                call_args = self._coerce_args_for_module_function(imported_module, raw, call_args, call_arg_nodes)
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, call_args, call_arg_nodes)
            return f"{mapped_runtime_txt}({join_str_list(', ', call_args)})", raw
        _, target_ns = self._resolve_imported_symbol_cpp_target(imported_module, raw)
        if target_ns != "":
            call_args = self.merge_call_args(args, kw)
            call_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
            module_arg_names = self._module_function_arg_names(imported_module, raw)
            if len(module_arg_names) > 0 and len(kw) > 0:
                call_args = self._merge_args_with_kw_by_name(args, kw, module_arg_names)
                call_arg_nodes = self._merge_arg_nodes_with_kw_by_name(arg_nodes, kw, kw_nodes, module_arg_names)
            namespaced = self._render_namespaced_module_call(
                imported_module,
                target_ns,
                raw,
                call_args,
                call_arg_nodes,
            )
            if namespaced is not None:
                return namespaced, raw
        return None, raw

    def _render_builtin_static_cast_call(
        self,
        expr: dict[str, Any],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の `runtime_call=static_cast` 分岐を描画する。"""
        if len(arg_nodes) == 1:
            arg_expr = self.render_expr(arg_nodes[0])
            target = self.cpp_type(expr.get("resolved_type"))
            arg_t = self.get_expr_type(arg_nodes[0])
            numeric_t = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if target == "int64" and arg_t == "str":
                return f"py_to_int64({arg_expr})"
            if target in {"float64", "float32"} and arg_t == "str":
                return f"py_to_float64({arg_expr})"
            if target == "int64" and arg_t in numeric_t:
                if self.should_skip_same_type_cast(arg_expr, "int64") or arg_expr.startswith("py_to<int64>("):
                    return arg_expr
                return f"int64({arg_expr})"
            if target == "int64" and self.is_any_like_type(arg_t):
                return f"py_to_int64({arg_expr})"
            if target in {"float64", "float32"} and self.is_any_like_type(arg_t):
                return f"py_to_float64({arg_expr})"
            if target == "bool" and self.is_any_like_type(arg_t):
                return f"py_to_bool({arg_expr})"
            if target == "int64":
                return f"py_to_int64({arg_expr})"
            if target in {"float64", "float32"}:
                return f"{target}({arg_expr})"
            return f"static_cast<{target}>({arg_expr})"
        return None

    def _coerce_py_assert_args(
        self,
        fn_name: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """`py_assert_*` 呼び出しで object 引数が必要な位置を boxing する。"""
        out: list[str] = []
        nodes = arg_nodes
        for i, arg in enumerate(args):
            a = arg
            needs_object = False
            if fn_name == "py_assert_stdout":
                needs_object = i == 1
            elif fn_name == "py_assert_eq":
                needs_object = i < 2
            if needs_object and not self.is_boxed_object_expr(a):
                arg_t = ""
                if i < len(nodes):
                    at = self.get_expr_type(nodes[i])
                    if isinstance(at, str):
                        arg_t = at
                arg_t = self.infer_rendered_arg_type(a, arg_t, self.declared_var_types)
                if not self.is_any_like_type(arg_t):
                    arg_node = nodes[i] if i < len(nodes) else {}
                    arg_node_d = arg_node if isinstance(arg_node, dict) else {}
                    if len(arg_node_d) > 0:
                        a = self.render_expr(self._build_box_expr_node(arg_node))
                    else:
                        a = f"make_object({a})"
            out.append(a)
        return out

    def _requires_builtin_call_lowering(self, raw: str) -> bool:
        """parser 側で BuiltinCall へ lower 済みであるべき Name を返す。"""
        return raw in {
            "print",
            "len",
            "str",
            "int",
            "float",
            "bool",
            "range",
            "zip",
            "min",
            "max",
            "perf_counter",
            "Exception",
            "RuntimeError",
            "open",
            "iter",
            "next",
            "bytes",
            "bytearray",
            "reversed",
            "enumerate",
            "any",
            "all",
            "ord",
            "chr",
            "list",
            "set",
            "dict",
        }

    def _requires_builtin_method_call_lowering(self, owner_t: str, attr: str) -> bool:
        """parser 側で BuiltinCall へ lower 済みであるべき method 呼び出しか判定する。"""
        method = attr if isinstance(attr, str) else str(attr)
        if method == "":
            return False
        int_like_types = ["int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"]
        owner_norm = self.normalize_type_name(owner_t)
        owner_parts: list[str] = [owner_norm]
        if self._contains_text(owner_norm, "|"):
            owner_parts = self.split_union(owner_norm)
        for part in owner_parts:
            t = self.normalize_type_name(part)
            if t == "str" and method in [
                "strip",
                "lstrip",
                "rstrip",
                "startswith",
                "endswith",
                "find",
                "rfind",
                "replace",
                "join",
                "isdigit",
                "isalpha",
            ]:
                return True
            if t == "Path" and method in [
                "mkdir",
                "exists",
                "write_text",
                "read_text",
                "parent",
                "name",
                "stem",
            ]:
                return True
            if (t in int_like_types or t == "int") and method == "to_bytes":
                return True
            if t.startswith("list[") and method in ["append", "extend", "pop", "clear", "reverse", "sort"]:
                return True
            if t.startswith("set[") and method in ["add", "discard", "remove", "clear"]:
                return True
            if t.startswith("dict[") and method in ["get", "pop", "items", "keys", "values"]:
                return True
        return False

    def _is_self_hosted_parser_doc(self) -> bool:
        """入力 EAST が self_hosted parser 由来かを返す。"""
        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        return self.any_dict_get_str(meta, "parser_backend", "") == "self_hosted"

    def _is_east3_doc(self) -> bool:
        """入力 EAST が strict な EAST3 契約かを返す。"""
        meta = self.any_to_dict_or_empty(self.doc.get("meta"))
        return self.any_to_str(meta.get("east_stage")).strip() == "3"

    def _render_range_name_call(self, args: list[str], kw: dict[str, str]) -> str | None:
        """`range(...)` 引数を `py_range(start, stop, step)` 形式へ正規化する。"""
        if len(kw) == 0:
            if len(args) == 1:
                return f"py_range(0, {args[0]}, 1)"
            if len(args) == 2:
                return f"py_range({args[0]}, {args[1]}, 1)"
            if len(args) == 3:
                return f"py_range({args[0]}, {args[1]}, {args[2]})"
            return None
        known_kw = {"start", "stop", "step"}
        for name, _value in kw.items():
            if name not in known_kw:
                return None
        if len(args) == 0 and "stop" in kw:
            start = kw.get("start", "0")
            stop = kw["stop"]
            step = kw.get("step", "1")
            return f"py_range({start}, {stop}, {step})"
        if len(args) == 1 and "stop" in kw and "start" not in kw:
            step = kw.get("step", "1")
            return f"py_range({args[0]}, {kw['stop']}, {step})"
        if len(args) == 2 and "step" in kw and "start" not in kw and "stop" not in kw:
            return f"py_range({args[0]}, {args[1]}, {kw['step']})"
        return None

    def _render_call_name_or_attr(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        fn_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
        first_arg: Any,
    ) -> str | None:
        """Call の Name/Attribute 分岐を処理する。"""
        _ = expr
        _ = fn_name
        _ = first_arg
        fn_kind = self._node_kind_from_dict(fn)
        if fn_kind == "Name":
            raw = self.any_dict_get_str(fn, "id", "")
            name_call_kind = self._type_id_name_call_kind(raw)
            imported_rendered, raw = self._resolve_or_render_imported_symbol_name_call(expr, raw, args, kw, arg_nodes, kw_nodes)
            if imported_rendered is not None:
                return imported_rendered
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, args, arg_nodes)
                return f"pytra::utils::assertions::{raw}({join_str_list(', ', call_args)})"
            if isinstance(raw, str) and raw in self.class_names:
                ctor_args = args
                if len(kw) > 0:
                    ctor_arg_names = self._class_method_name_sig(raw, "__init__")
                    ctor_args = self._merge_args_with_kw_by_name(args, kw, ctor_arg_names)
                else:
                    # class ctor でも __init__ シグネチャに合わせて boxing/unboxing を適用する。
                    ctor_args = self._coerce_args_for_class_method(raw, "__init__", ctor_args, arg_nodes)
                if raw in self.ref_classes:
                    return f"::rc_new<{raw}>({join_str_list(', ', ctor_args)})"
                return f"{raw}({join_str_list(', ', ctor_args)})"
            if self._requires_builtin_call_lowering(raw):
                raise ValueError("builtin call must be lowered_kind=BuiltinCall: " + raw)
            if name_call_kind in {"legacy_isinstance", "legacy_issubclass"}:
                raise ValueError("type_id call must be lowered to EAST3 node: " + raw)
            if name_call_kind != "":
                type_id_expr = self._build_type_id_expr_from_call_name(raw, arg_nodes)
                if type_id_expr is not None:
                    return self.render_expr(type_id_expr)
        if fn_kind == "Attribute":
            attr_rendered_txt = ""
            attr_rendered = self._render_call_attribute(expr, fn, args, kw, arg_nodes, kw_nodes)
            if isinstance(attr_rendered, str):
                attr_rendered_txt = str(attr_rendered)
            if attr_rendered_txt != "":
                return attr_rendered_txt
        return None

    def _render_call_module_method(
        self,
        owner_mod: str,
        attr: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """module.method(...) 呼び出しを処理する。"""
        hook_rendered = self.hook_on_render_module_method(owner_mod, attr, args, kw, arg_nodes)
        if isinstance(hook_rendered, str) and hook_rendered != "":
            return hook_rendered
        merged_args = self.merge_call_args(args, kw)
        merged_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        module_arg_names = self._module_function_arg_names(owner_mod, attr)
        if len(module_arg_names) > 0 and len(kw) > 0:
            merged_args = self._merge_args_with_kw_by_name(args, kw, module_arg_names)
            merged_arg_nodes = self._merge_arg_nodes_with_kw_by_name(arg_nodes, kw, kw_nodes, module_arg_names)
        mapped_runtime = self._lookup_module_attr_runtime_call(owner_mod, attr)
        if mapped_runtime != "":
            call_args = merged_args
            if self._contains_text(mapped_runtime, "::"):
                call_args = self._coerce_args_for_module_function(owner_mod, attr, call_args, merged_arg_nodes)
            if attr.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(attr, call_args, merged_arg_nodes)
            return f"{mapped_runtime}({join_str_list(', ', call_args)})"
        owner_mod_norm = owner_mod
        if owner_mod_norm in self.module_namespace_map:
            mapped = self._render_call_module_method_with_namespace(
                owner_mod,
                attr,
                self.module_namespace_map[owner_mod_norm],
                merged_args,
                merged_arg_nodes,
            )
            if mapped is not None:
                return mapped
        fallback = self._render_call_module_method_with_namespace(
            owner_mod,
            attr,
            self._module_name_to_cpp_namespace(owner_mod_norm),
            merged_args,
            merged_arg_nodes,
        )
        if fallback is not None:
            return fallback
        return None

    def _render_call_module_method_with_namespace(
        self,
        owner_mod: str,
        attr: str,
        ns_name: str,
        merged_args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`namespace::func(...)` 形式の module call を共通描画する。"""
        return self._render_namespaced_module_call(owner_mod, ns_name, attr, merged_args, arg_nodes)

    def _render_namespaced_module_call(
        self,
        module_name: str,
        namespace_name: str,
        func_name: str,
        rendered_args: list[str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`namespace::func(...)` 呼び出しを描画する共通 helper。"""
        if namespace_name == "":
            return None
        call_args = self._coerce_args_for_module_function(module_name, func_name, rendered_args, arg_nodes)
        if func_name.startswith("py_assert_"):
            call_args = self._coerce_py_assert_args(func_name, call_args, arg_nodes)
        return f"{namespace_name}::{func_name}({join_str_list(', ', call_args)})"

    def _render_call_class_method(
        self,
        owner_t: str,
        attr: str,
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """`Class.method(...)` 分岐を処理する。"""
        dispatch_mode = self._class_method_dispatch_mode(owner_t, attr)
        if dispatch_mode == "fallback":
            return None
        call_args = args
        call_arg_nodes = arg_nodes
        if len(kw) > 0:
            arg_names = self._class_method_name_sig(owner_t, attr)
            if len(arg_names) > 0:
                call_args, call_arg_nodes = self._merge_args_with_kw_defaults(
                    args,
                    kw,
                    arg_nodes,
                    kw_nodes,
                    arg_names,
                    self._class_method_default_sig(owner_t, attr),
                    self._class_method_sig(owner_t, attr),
                )
            else:
                call_args = self.merge_call_args(args, kw)
                call_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        else:
            call_args = self.merge_call_args(args, kw)
        call_args = self._coerce_args_for_class_method(owner_t, attr, call_args, call_arg_nodes)
        fn_expr = self._render_attribute_expr(fn)
        dispatch_table = {
            "virtual": self._render_virtual_class_method_call,
            "direct": self._render_direct_class_method_call,
        }
        handler = dispatch_table.get(dispatch_mode)
        if handler is None:
            return None
        return handler(fn_expr, call_args)

    def _render_append_call_object_method(
        self,
        owner_types: list[str],
        owner_expr: str,
        args: list[str],
        arg_nodes: Any = None,
    ) -> str | None:
        """`obj.append(...)` の型依存特殊処理を描画する。"""
        a0 = args[0] if len(args) >= 1 else "/* missing */"
        arg0_node: Any = {}
        arg_nodes_list: list[Any] = self.any_to_list(arg_nodes)
        if len(arg_nodes_list) >= 1:
            arg0_node = arg_nodes_list[0]
        arg0_t_raw = self.get_expr_type(arg0_node)
        arg0_t = self.normalize_type_name(arg0_t_raw) if isinstance(arg0_t_raw, str) else ""
        normalized_owner_types: list[str] = []
        for owner_t in owner_types:
            owner_t_norm = self.normalize_type_name(owner_t)
            if owner_t_norm != "" and owner_t_norm not in normalized_owner_types:
                normalized_owner_types.append(owner_t_norm)
        inferred_owner_t = self.normalize_type_name(
            self.infer_rendered_arg_type(
                owner_expr,
                normalized_owner_types[0] if len(normalized_owner_types) > 0 else "",
                self.declared_var_types,
            )
        )
        if self._contains_text(inferred_owner_t, "|"):
            for part in self.split_union(inferred_owner_t):
                part_norm = self.normalize_type_name(part)
                if part_norm != "" and part_norm not in normalized_owner_types:
                    normalized_owner_types.append(part_norm)
        elif inferred_owner_t != "" and inferred_owner_t not in normalized_owner_types:
            normalized_owner_types.append(inferred_owner_t)
        if "bytearray" in normalized_owner_types:
            a0 = f"static_cast<uint8>(py_to<int64>({a0}))"
            return f"{owner_expr}.append({a0})"
        list_owner_t = ""
        for t in normalized_owner_types:
            if t.startswith("list[") and t.endswith("]"):
                list_owner_t = t
                break
        if list_owner_t != "":
            inner_t: str = list_owner_t[5:-1].strip()
            if inner_t == "uint8":
                a0 = f"static_cast<uint8>(py_to<int64>({a0}))"
            elif self.is_any_like_type(inner_t):
                if not self.is_boxed_object_expr(a0):
                    arg0_node_d = self.any_to_dict_or_empty(arg0_node)
                    if len(arg0_node_d) > 0:
                        a0 = self.render_expr(self._build_box_expr_node(arg0_node))
                    else:
                        a0 = f"make_object({a0})"
            elif inner_t != "" and not self.is_any_like_type(inner_t):
                inner_t_norm = self.normalize_type_name(inner_t)
                if not (inner_t_norm == "bytes" and arg0_t == "bytes"):
                    inner_cpp_t = self._cpp_type_text(inner_t)
                    # `list<tuple[...]>.append((...))` は `::std::make_tuple(...)` が
                    # そのまま受理されるため、`::std::tuple<...>(::std::make_tuple(...))`
                    # の二重ラップを避ける。
                    if inner_cpp_t.startswith("::std::tuple<") and a0.startswith("::std::make_tuple("):
                        return f"{owner_expr}.append({a0})"
                    if not self.should_skip_same_type_cast(a0, inner_cpp_t):
                        a0 = f"{inner_cpp_t}({a0})"
            return f"{owner_expr}.append({a0})"
        deque_owner_t = ""
        for t in normalized_owner_types:
            if t.startswith("deque[") and t.endswith("]"):
                deque_owner_t = t
                break
        if deque_owner_t != "":
            return self._render_typed_deque_push_call(deque_owner_t, owner_expr, a0, arg0_node, "push_back")
        has_any_like_owner = False
        for t in normalized_owner_types:
            t_norm = self.normalize_type_name(t)
            if t_norm in {"", "unknown"} or self.is_any_like_type(t_norm):
                has_any_like_owner = True
                break
        if has_any_like_owner:
            if not self.is_boxed_object_expr(a0):
                arg0_node_d = self.any_to_dict_or_empty(arg0_node)
                if len(arg0_node_d) > 0:
                    a0 = self.render_expr(self._build_box_expr_node(arg0_node))
                else:
                    a0 = f"make_object({a0})"
            list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "append")
            return f"py_list_append_mut({list_ref_expr}, {a0})"
        return None

    def _render_typed_deque_push_call(
        self,
        deque_owner_t: str,
        owner_expr: str,
        value_expr: str,
        value_node: Any,
        push_method: str,
    ) -> str:
        """typed deque の要素追加を `push_front/back` へ lower する。"""
        coerced_expr = self._coerce_typed_deque_item_expr(deque_owner_t, value_expr, value_node)
        return f"{owner_expr}.{push_method}({coerced_expr})"

    def _render_typed_deque_copy_call(
        self,
        deque_owner_t: str,
        owner_expr: str,
    ) -> str:
        """typed deque の `copy()` を copy-construction surface へ lower する。"""
        owner_cpp_t = self._cpp_type_text(deque_owner_t)
        source_tmp = self.next_tmp("__deque_src")
        return (
            f"([&]() -> {owner_cpp_t} {{ "
            f"auto&& {source_tmp} = {owner_expr}; "
            f"return {owner_cpp_t}({source_tmp}); "
            "}())"
        )

    def _render_typed_deque_index_call(
        self,
        deque_owner_t: str,
        owner_expr: str,
        value_expr: str,
        value_node: Any,
    ) -> str:
        """typed deque の `index(value)` を `find + iterator差分` へ lower する。"""
        index_expr = self._coerce_typed_deque_item_expr(deque_owner_t, value_expr, value_node)
        source_tmp = self.next_tmp("__deque_src")
        iter_tmp = self.next_tmp("__deque_it")
        return (
            "([&]() -> int64 { "
            f"auto&& {source_tmp} = {owner_expr}; "
            f"auto {iter_tmp} = ::std::find({source_tmp}.begin(), {source_tmp}.end(), {index_expr}); "
            f"if ({iter_tmp} == {source_tmp}.end()) throw ValueError(\"deque.index missing value\"); "
            f"return static_cast<int64>({iter_tmp} - {source_tmp}.begin()); "
            "}())"
        )

    def _coerce_typed_deque_item_expr(
        self,
        deque_owner_t: str,
        value_expr: str,
        value_node: Any,
    ) -> str:
        """typed deque に push する要素式を inner type に合わせて整形する。"""
        a0 = value_expr
        arg0_t_raw = self.get_expr_type(value_node)
        arg0_t = self.normalize_type_name(arg0_t_raw) if isinstance(arg0_t_raw, str) else ""
        inner_t = deque_owner_t[6:-1].strip()
        if inner_t == "uint8":
            a0 = f"static_cast<uint8>(py_to<int64>({a0}))"
        elif self.is_any_like_type(inner_t):
            if not self.is_boxed_object_expr(a0):
                arg0_node_d = self.any_to_dict_or_empty(value_node)
                if len(arg0_node_d) > 0:
                    a0 = self.render_expr(self._build_box_expr_node(value_node))
                else:
                    a0 = f"make_object({a0})"
        elif inner_t != "" and not self.is_any_like_type(inner_t):
            inner_t_norm = self.normalize_type_name(inner_t)
            if not (inner_t_norm == "bytes" and arg0_t == "bytes"):
                inner_cpp_t = self._cpp_type_text(inner_t)
                if inner_cpp_t.startswith("::std::tuple<") and a0.startswith("::std::make_tuple("):
                    return a0
                if not self.should_skip_same_type_cast(a0, inner_cpp_t):
                    a0 = f"{inner_cpp_t}({a0})"
        return a0

    def _render_typed_deque_extendleft_call(
        self,
        deque_owner_t: str,
        owner_expr: str,
        value_expr: str,
        value_node: Any,
    ) -> str:
        """typed deque の `extendleft(iterable)` を snapshot + push_front loop へ lower する。"""
        source_t = self.normalize_type_name(self.get_expr_type(value_node))
        if source_t in {"", "unknown"}:
            source_t = self.normalize_type_name(self.infer_rendered_arg_type(value_expr, source_t, self.declared_var_types))
        if source_t in {"", "unknown"}:
            source_t = self.normalize_type_name(self.infer_rendered_arg_type(value_expr, source_t, self.module_global_var_types))
        if not (
            (source_t.startswith("list[") and source_t.endswith("]"))
            or (source_t.startswith("deque[") and source_t.endswith("]"))
        ):
            return ""
        source_expr = self._trim_ws(value_expr)
        if source_expr == "":
            return ""
        source_tmp = self.next_tmp("__deque_src")
        iter_tmp = self.next_tmp("__deque_it")
        elem_t = ""
        if source_t.startswith("list[") and source_t.endswith("]"):
            elem_t = source_t[5:-1].strip()
        elif source_t.startswith("deque[") and source_t.endswith("]"):
            elem_t = source_t[6:-1].strip()
        elem_node = self._build_name_expr_node(iter_tmp, elem_t or "unknown")
        pushed_expr = self._coerce_typed_deque_item_expr(deque_owner_t, f"*{iter_tmp}", elem_node)
        return (
            "([&]() { "
            f"auto {source_tmp} = {source_expr}; "
            f"for (auto {iter_tmp} = {source_tmp}.begin(); {iter_tmp} != {source_tmp}.end(); ++{iter_tmp}) "
            "{ "
            f"{owner_expr}.push_front({pushed_expr}); "
            "} "
            "}())"
        )

    def _is_super_call_expr(self, node: Any) -> bool:
        """`super()` 呼び出し式か判定する。"""
        node_d = self.any_to_dict_or_empty(node)
        if self._node_kind_from_dict(node_d) != "Call":
            return False
        fn = self.any_to_dict_or_empty(node_d.get("func"))
        if self._node_kind_from_dict(fn) != "Name":
            return False
        if self.any_dict_get_str(fn, "id", "") != "super":
            return False
        args = self.any_to_list(node_d.get("args"))
        return len(args) == 0

    def _render_super_attribute_call(
        self,
        owner_obj: Any,
        attr: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> str | None:
        """`super().method(...)` を `Base::method(...)` へ変換する。"""
        if not self._is_super_call_expr(owner_obj):
            return None
        base = self.current_class_base_name
        if base == "":
            return None
        if not self._has_class_method(base, attr):
            return None
        call_args = self.merge_call_args(args, kw)
        call_args = self._coerce_args_for_class_method(base, attr, call_args, arg_nodes)
        if len(call_args) == 0:
            return f"{base}::{attr}()"
        return f"{base}::{attr}({join_str_list(', ', call_args)})"

    def _render_call_attribute(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """Attribute 形式の呼び出しを module/object/fallback の順で処理する。"""
        _ = expr
        owner_obj = fn.get("value")
        owner_rendered = self.render_expr(owner_obj)
        call_ctx = self.resolve_call_attribute_context(owner_obj, owner_rendered, fn, self.declared_var_types)
        owner_expr = self.any_dict_get_str(call_ctx, "owner_expr", "")
        owner_mod = self.any_dict_get_str(call_ctx, "owner_mod", "")
        owner_t = self.any_dict_get_str(call_ctx, "owner_type", "")
        attr = self.any_dict_get_str(call_ctx, "attr", "")
        if attr == "":
            return None
        merged_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        super_rendered = self._render_super_attribute_call(owner_obj, attr, args, kw, merged_arg_nodes)
        if super_rendered is not None and super_rendered != "":
            return super_rendered
        if owner_mod != "":
            module_rendered_1 = self._render_call_module_method(owner_mod, attr, args, kw, arg_nodes, kw_nodes)
            if module_rendered_1 is not None and module_rendered_1 != "":
                return module_rendered_1
        selfhost_fallback = self._render_selfhost_builtin_method_call(
            owner_t,
            owner_expr,
            attr,
            args,
            kw,
        )
        if selfhost_fallback is not None and selfhost_fallback != "":
            return selfhost_fallback
        runtime_builtin_fallback = self._render_runtime_builtin_method_call_fallback(
            owner_t,
            owner_obj,
            attr,
            arg_nodes,
            kw_nodes,
        )
        if runtime_builtin_fallback is not None and runtime_builtin_fallback != "":
            return runtime_builtin_fallback
        if self._requires_builtin_method_call_lowering(owner_t, attr):
            owner_label = self.normalize_type_name(owner_t)
            if owner_label == "":
                owner_label = "unknown"
            raise ValueError("builtin method call must be lowered_kind=BuiltinCall: " + owner_label + "." + attr)
        return self._render_call_attribute_non_module(owner_t, owner_expr, attr, fn, args, kw, arg_nodes, kw_nodes)

    def _render_selfhost_builtin_method_call(
        self,
        owner_t: str,
        owner_expr: str,
        attr: str,
        args: list[str],
        kw: dict[str, str],
    ) -> str | None:
        """self_hosted parser 由来で BuiltinCall 未lower の method を最小フォールバックする。"""
        if not self._is_self_hosted_parser_doc():
            return None
        src = self.any_dict_get_str(self.doc, "source_path", "")
        # Restrict fallback to known selfhost bootstrap sources.
        if not (
            src.endswith("/selfhost/py2cpp.py")
            or src.endswith("/src/backends/cpp/cli.py")
            or src.endswith("/src/py2x-selfhost.py")
        ):
            return None
        owner_norm = self.normalize_type_name(owner_t)
        if owner_norm != "str":
            return None
        call_args = self.merge_call_args(args, kw)
        if attr in {"strip", "lstrip", "rstrip"}:
            if len(call_args) == 0:
                return f"py_{attr}({owner_expr})"
            if len(call_args) == 1:
                return f"py_{attr}_chars({owner_expr}, {call_args[0]})"
            return None
        if attr in {"startswith", "endswith"}:
            if len(call_args) == 1:
                return f"py_{attr}({owner_expr}, {call_args[0]})"
            return None
        if attr in {"find", "rfind"}:
            fn_name = f"py_{attr}"
            window_name = f"py_{attr}_window"
            if len(call_args) == 1:
                return f"{fn_name}({owner_expr}, {call_args[0]})"
            if len(call_args) == 2:
                return f"{window_name}({owner_expr}, {call_args[0]}, {call_args[1]}, py_len({owner_expr}))"
            if len(call_args) == 3:
                return f"{window_name}({owner_expr}, {call_args[0]}, {call_args[1]}, {call_args[2]})"
            return None
        if attr == "replace":
            if len(call_args) == 2:
                return f"py_replace({owner_expr}, {call_args[0]}, {call_args[1]})"
            return None
        if attr == "join":
            if len(call_args) == 1:
                return f"py_join({owner_expr}, {call_args[0]})"
            return None
        if attr in {"isdigit", "isalpha"}:
            if len(call_args) == 0:
                return f"py_{attr}({owner_expr})"
            return None
        return None

    def _render_runtime_builtin_method_call_fallback(
        self,
        owner_t: str,
        owner_node: Any,
        attr: str,
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """runtime SoT のみ、未 lower の builtin method を BuiltinCall 経路へ戻す。"""
        if len(kw_nodes) != 0:
            return None
        src = self.any_dict_get_str(self.doc, "source_path", "")
        if not (
            src.startswith("src/pytra/std/")
            or src.startswith("src/pytra/utils/")
            or src.startswith("src/pytra/built_in/")
            or src.startswith("src/toolchain/compiler/")
        ):
            return None
        owner_norm = self.normalize_type_name(owner_t)
        runtime_call = ""
        if owner_norm.startswith("list[") and attr in {"append", "extend", "pop", "clear", "reverse", "sort"}:
            runtime_call = "list." + attr
        elif owner_norm.startswith("set[") and attr in {"add", "discard", "remove", "clear"}:
            runtime_call = "set." + attr
        elif owner_norm.startswith("dict[") and attr in {"get", "pop", "items", "keys", "values"}:
            runtime_call = "dict." + attr
        if runtime_call == "":
            return None
        builtin_expr: dict[str, Any] = {
            "kind": "BuiltinCall",
            "runtime_call": runtime_call,
            "runtime_owner": owner_node,
            "resolved_type": "unknown",
            "borrow_kind": "value",
            "casts": [],
        }
        rendered = self._render_builtin_call(builtin_expr, arg_nodes, kw_nodes)
        if rendered == "":
            return None
        return rendered

    def _make_missing_symbol_import_error(self, base_name: str, attr: str) -> Exception:
        """`from-import` 束縛名の module 参照エラーを生成する（C++ 向け）。"""
        src = self.any_dict_get_str(self.doc, "source_path", "(input)")
        if src == "":
            src = "(input)"
        return make_user_error(
            "input_invalid",
            "Module names are not bound by from-import statements.",
            [f"kind=missing_symbol file={src} import={base_name}.{attr}"],
        )

    def _render_call_attribute_non_module(
        self,
        owner_t: str,
        owner_expr: str,
        attr: str,
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """`Call(Attribute)` の object/class 系分岐（非 module）を処理する。"""
        owner_t = self.infer_rendered_arg_type(owner_expr, owner_t, self.declared_var_types)
        owner_t = self.infer_rendered_arg_type(owner_expr, owner_t, self.module_global_var_types)
        owner_t = self.normalize_type_name(owner_t)
        hook_object_rendered = self.hook_on_render_object_method(owner_t, owner_expr, attr, args)
        if isinstance(hook_object_rendered, str) and hook_object_rendered != "":
            return hook_object_rendered
        if attr == "append" and len(args) == 1 and len(kw) == 0:
            owner_types: list[str] = [owner_t]
            if self._contains_text(owner_t, "|"):
                owner_types = self.split_union(owner_t)
            append_rendered = self._render_append_call_object_method(owner_types, owner_expr, args, arg_nodes)
            if append_rendered is not None and append_rendered != "":
                return append_rendered
        if owner_t.startswith("deque[") and owner_t.endswith("]"):
            if attr == "copy" and len(args) == 0 and len(kw) == 0:
                return self._render_typed_deque_copy_call(owner_t, owner_expr)
            if attr == "count" and len(args) == 1 and len(kw) == 0:
                value_node = arg_nodes[0] if len(arg_nodes) > 0 else {}
                count_expr = self._coerce_typed_deque_item_expr(owner_t, args[0], value_node)
                return f"static_cast<int64>(::std::count({owner_expr}.begin(), {owner_expr}.end(), {count_expr}))"
            if attr == "index" and len(args) == 1 and len(kw) == 0:
                value_node = arg_nodes[0] if len(arg_nodes) > 0 else {}
                return self._render_typed_deque_index_call(owner_t, owner_expr, args[0], value_node)
            if attr == "remove" and len(args) == 1 and len(kw) == 0:
                value_node = arg_nodes[0] if len(arg_nodes) > 0 else {}
                remove_expr = self._coerce_typed_deque_item_expr(owner_t, args[0], value_node)
                iter_tmp = self.next_tmp("__deque_it")
                return (
                    "([&]() -> decltype(nullptr) { "
                    f"auto {iter_tmp} = ::std::find({owner_expr}.begin(), {owner_expr}.end(), {remove_expr}); "
                    f"if ({iter_tmp} == {owner_expr}.end()) throw ValueError(\"deque.remove missing value\"); "
                    f"{owner_expr}.erase({iter_tmp}); "
                    "return nullptr; "
                    "}())"
                )
            if attr == "reverse" and len(args) == 0 and len(kw) == 0:
                return f"::std::reverse({owner_expr}.begin(), {owner_expr}.end())"
            if attr == "rotate" and len(kw) == 0 and len(args) <= 1:
                rotate_expr = "1"
                if len(args) == 1:
                    rotate_expr = args[0]
                rotate_tmp = self.next_tmp("__deque_rotate")
                size_tmp = self.next_tmp("__deque_size")
                cut_tmp = self.next_tmp("__deque_cut")
                return (
                    "([&]() -> decltype(nullptr) { "
                    f"if (!{owner_expr}.empty()) {{ "
                    f"int64 {rotate_tmp} = static_cast<int64>({rotate_expr}); "
                    f"int64 {size_tmp} = static_cast<int64>({owner_expr}.size()); "
                    f"{rotate_tmp} %= {size_tmp}; "
                    f"if ({rotate_tmp} < 0) {rotate_tmp} += {size_tmp}; "
                    f"if ({rotate_tmp} != 0) {{ "
                    f"auto {cut_tmp} = {owner_expr}.begin() + ({size_tmp} - {rotate_tmp}); "
                    f"::std::rotate({owner_expr}.begin(), {cut_tmp}, {owner_expr}.end()); "
                    "} "
                    "} "
                    "return nullptr; "
                    "}())"
                )
            if attr == "extendleft" and len(args) == 1 and len(kw) == 0:
                value_node = arg_nodes[0] if len(arg_nodes) > 0 else {}
                rendered = self._render_typed_deque_extendleft_call(owner_t, owner_expr, args[0], value_node)
                if rendered != "":
                    return rendered
            if attr == "appendleft" and len(args) == 1 and len(kw) == 0:
                value_node = arg_nodes[0] if len(arg_nodes) > 0 else {}
                return self._render_typed_deque_push_call(owner_t, owner_expr, args[0], value_node, "push_front")
            if attr == "pop" and len(args) == 0 and len(kw) == 0:
                tmp_name = self.next_tmp("__deque_back")
                return (
                    "([&]() { "
                    f"auto {tmp_name} = {owner_expr}.back(); "
                    f"{owner_expr}.pop_back(); "
                    f"return {tmp_name}; "
                    "}())"
                )
            if attr == "popleft" and len(args) == 0 and len(kw) == 0:
                tmp_name = self.next_tmp("__deque_front")
                return (
                    "([&]() { "
                    f"auto {tmp_name} = {owner_expr}.front(); "
                    f"{owner_expr}.pop_front(); "
                    f"return {tmp_name}; "
                    "}())"
                )
        hook_class_rendered = self.hook_on_render_class_method(owner_t, attr, fn, args, kw, arg_nodes)
        if isinstance(hook_class_rendered, str) and hook_class_rendered != "":
            return hook_class_rendered
        class_rendered = self._render_call_class_method(owner_t, attr, fn, args, kw, arg_nodes, kw_nodes)
        if class_rendered is not None and class_rendered != "":
            return class_rendered
        return None

    def _collect_class_method_candidates(self, owner_t: str) -> list[str]:
        """class method シグネチャ探索で使う候補クラス名を返す。"""
        candidates = self._expand_runtime_class_candidates(owner_t)
        if self.current_class_name is not None and owner_t in {"", "unknown"}:
            candidates.append(self.current_class_name)
        return candidates

    def _class_method_dispatch_mode(self, owner_t: str, method: str) -> str:
        """class method 呼び出しの dispatch mode（virtual/direct/fallback）を返す。"""
        if not self._has_class_method(owner_t, method):
            return "fallback"
        candidates = self._collect_class_method_candidates(owner_t)
        for cls_name in candidates:
            if method in self.class_method_virtual.get(cls_name, set()):
                return "virtual"
        return "direct"

    def _render_virtual_class_method_call(self, fn_expr: str, call_args: list[str]) -> str:
        """virtual 経路の class method 呼び出しを描画する。"""
        return f"{fn_expr}({join_str_list(', ', call_args)})"

    def _render_direct_class_method_call(self, fn_expr: str, call_args: list[str]) -> str:
        """non-virtual 経路の class method 呼び出しを描画する。"""
        return f"{fn_expr}({join_str_list(', ', call_args)})"

    def _class_method_sig(self, owner_t: str, method: str) -> list[str]:
        """クラスメソッドの引数型シグネチャを返す。未知なら空配列。"""
        candidates = self._collect_class_method_candidates(owner_t)
        for c in candidates:
            if c in self.class_method_arg_types:
                mm = self.class_method_arg_types[c]
                if method in mm:
                    return mm[method]
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_types:
                mm = self.class_method_arg_types[self.current_class_name]
            if method in mm:
                return mm[method]
        return []

    def _has_class_method(self, owner_t: str, method: str) -> bool:
        """クラスメソッドが存在するかを返す（0引数メソッド対応）。"""
        candidates = self._collect_class_method_candidates(owner_t)
        for c in candidates:
            if c in self.class_method_arg_types:
                mm = self.class_method_arg_types[c]
                if method in mm:
                    return True
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm2: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_types:
                mm2 = self.class_method_arg_types[self.current_class_name]
            if method in mm2:
                return True
        return False

    def _class_method_name_sig(self, owner_t: str, method: str) -> list[str]:
        """クラスメソッドの引数名シグネチャを返す。未知なら空配列。"""
        candidates = self._collect_class_method_candidates(owner_t)
        for c in candidates:
            if c in self.class_method_arg_names:
                mm = self.class_method_arg_names[c]
                if method in mm:
                    return mm[method]
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm2: dict[str, list[str]] = {}
            if self.current_class_name in self.class_method_arg_names:
                mm2 = self.class_method_arg_names[self.current_class_name]
                if method in mm2:
                    return mm2[method]
        return []

    def _class_method_default_sig(self, owner_t: str, method: str) -> dict[str, Any]:
        """クラスメソッドの既定引数ノードを返す。未知なら空 dict。"""
        candidates = self._collect_class_method_candidates(owner_t)
        for c in candidates:
            if c in self.class_method_arg_defaults:
                mm = self.class_method_arg_defaults[c]
                if method in mm:
                    defaults = mm[method]
                    if isinstance(defaults, dict):
                        return defaults
        if owner_t in {"", "unknown"} and self.current_class_name is not None:
            mm2: dict[str, Any] = {}
            if self.current_class_name in self.class_method_arg_defaults:
                mm2 = self.class_method_arg_defaults[self.current_class_name]
            if method in mm2:
                defaults = mm2.get(method)
                if isinstance(defaults, dict):
                    return defaults
        return {}

    def _merge_args_with_kw_by_name(self, args: list[str], kw: dict[str, str], arg_names: list[str]) -> list[str]:
        """位置引数+キーワード引数を、引数名順に 1 本化する。"""
        out: list[str] = []
        for arg in args:
            out.append(arg)
        used_kw: set[str] = set()
        positional_count = len(out)
        for j, nm in enumerate(arg_names):
            if j < positional_count:
                continue
            if nm in kw:
                out.append(kw[nm])
                used_kw.add(nm)
        for nm, val in kw.items():
            if nm not in used_kw:
                out.append(val)
        return out

    def _merge_arg_nodes_with_kw_by_name(
        self,
        arg_nodes: list[Any],
        kw: dict[str, str],
        kw_nodes: list[Any],
        arg_names: list[str],
    ) -> list[Any]:
        """位置引数+キーワード値ノードを、引数名順で 1 本化する。"""
        out: list[Any] = []
        for node in arg_nodes:
            out.append(node)
        if len(kw) == 0:
            return out
        kw_name_list: list[str] = []
        for key, _ in kw.items():
            kw_name_list.append(key)
        kw_node_map: dict[str, Any] = {}
        i = 0
        while i < len(kw_name_list):
            kw_name = kw_name_list[i]
            kw_node_map[kw_name] = kw_nodes[i] if i < len(kw_nodes) else {}
            i += 1
        used_kw: set[str] = set()
        positional_count = len(out)
        for j, name in enumerate(arg_names):
            if j < positional_count:
                continue
            if name in kw_node_map:
                out.append(kw_node_map[name])
                used_kw.add(name)
        for kw_name in kw_name_list:
            if kw_name not in used_kw:
                out.append(kw_node_map.get(kw_name, {}))
        return out

    def _merge_args_with_kw_defaults(
        self,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
        arg_names: list[str],
        arg_defaults: dict[str, Any],
        arg_types: list[str],
    ) -> tuple[list[str], list[Any]]:
        """C++ positional call 用に keyword と途中 default を埋める。"""
        if len(kw) == 0 or len(arg_names) == 0:
            return args, arg_nodes
        kw_name_list: list[str] = []
        for key, _ in kw.items():
            kw_name_list.append(key)
        kw_node_map: dict[str, Any] = {}
        i = 0
        while i < len(kw_name_list):
            kw_name = kw_name_list[i]
            kw_node_map[kw_name] = kw_nodes[i] if i < len(kw_nodes) else {}
            i += 1
        highest_index = len(args) - 1
        found_named_slot = False
        for kw_name in kw_name_list:
            if kw_name not in arg_names:
                continue
            idx = arg_names.index(kw_name)
            if idx > highest_index:
                highest_index = idx
            found_named_slot = True
        if not found_named_slot:
            return self.merge_call_args(args, kw), self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        out_args: list[str] = []
        out_nodes: list[Any] = []
        used_kw: set[str] = set()
        idx = 0
        while idx <= highest_index:
            if idx < len(args):
                out_args.append(args[idx])
                out_nodes.append(arg_nodes[idx] if idx < len(arg_nodes) else {})
                idx += 1
                continue
            if idx >= len(arg_names):
                break
            arg_name = arg_names[idx]
            if arg_name in kw:
                out_args.append(kw[arg_name])
                out_nodes.append(kw_node_map.get(arg_name, {}))
                used_kw.add(arg_name)
                idx += 1
                continue
            if arg_name in arg_defaults:
                default_node = arg_defaults.get(arg_name)
                target_t = arg_types[idx] if idx < len(arg_types) else "Any"
                default_txt = ""
                if isinstance(default_node, dict):
                    default_txt = self._render_param_default_expr(default_node, target_t)
                if default_txt != "":
                    out_args.append(default_txt)
                    out_nodes.append(default_node)
                    idx += 1
                    continue
            return self.merge_call_args(args, kw), self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        while idx < len(args):
            out_args.append(args[idx])
            out_nodes.append(arg_nodes[idx] if idx < len(arg_nodes) else {})
            idx += 1
        for kw_name in kw_name_list:
            if kw_name not in used_kw:
                out_args.append(kw[kw_name])
                out_nodes.append(kw_node_map.get(kw_name, {}))
        return out_args, out_nodes

    def _coerce_args_for_class_method(
        self,
        owner_t: str,
        method: str,
        args: list[str],
        arg_nodes: list[Any],
    ) -> list[str]:
        """クラスメソッド呼び出しに対して引数型を合わせる。"""
        sig_raw = self._class_method_sig(owner_t, method)
        sig: list[str] = []
        for t in sig_raw:
            t_norm = self.normalize_type_name(t)
            if t_norm in {"", "unknown"}:
                sig.append("object")
            else:
                sig.append(t_norm)
        return self._coerce_args_by_signature(args, arg_nodes, sig)

    def _render_call_fallback(self, fn_name: str, args: list[str]) -> str:
        """Call の最終フォールバック（通常の関数呼び出し）を返す。"""
        if self._requires_builtin_call_lowering(fn_name):
            raise ValueError("builtin call must be lowered_kind=BuiltinCall: " + fn_name)
        dot_pos = fn_name.rfind(".")
        if dot_pos > 0:
            owner_expr = fn_name[:dot_pos]
            method = fn_name[dot_pos + 1 :]
            owner_t = "unknown"
            if owner_expr in self.declared_var_types:
                owner_t = self.declared_var_types[owner_expr]
            if self._requires_builtin_method_call_lowering(owner_t, method):
                if not self._is_self_hosted_parser_doc():
                    owner_label = self.normalize_type_name(owner_t)
                    if owner_label == "":
                        owner_label = "unknown"
                    raise ValueError("builtin method call must be lowered_kind=BuiltinCall: " + owner_label + "." + method)
        if fn_name.startswith("py_assert_"):
            call_args = self._coerce_py_assert_args(fn_name, args, [])
            return f"pytra::utils::assertions::{fn_name}({join_str_list(', ', call_args)})"
        return f"{fn_name}({join_str_list(', ', args)})"

    def _render_call_expr_from_context(
        self,
        expr_d: dict[str, Any],
        fn: dict[str, Any],
        fn_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
        kw_values: list[str],
        kw_nodes: list[Any],
        first_arg: object,
    ) -> str:
        """`Call` ノードの描画本体（前処理済みコンテキスト版）。"""
        _ = first_arg
        self.validate_call_receiver_or_raise(fn)
        hook_call = self.hook_on_render_call(expr_d, fn, args, kw)
        hook_call_txt = ""
        if isinstance(hook_call, str):
            hook_call_txt = str(hook_call)
        if hook_call_txt != "":
            return hook_call_txt
        json_decode_call = self._render_json_decode_call(expr_d)
        if json_decode_call != "":
            return json_decode_call
        lowered_kind = self.any_dict_get_str(expr_d, "lowered_kind", "")
        if lowered_kind == "BuiltinCall":
            builtin_rendered: str = self._render_builtin_call(expr_d, arg_nodes, kw_nodes)
            if builtin_rendered != "":
                return builtin_rendered
            runtime_call_txt = self.any_dict_get_str(expr_d, "runtime_call", "")
            builtin_name_txt = self.any_dict_get_str(expr_d, "builtin_name", "")
            raise ValueError(
                "unhandled BuiltinCall: runtime_call="
                + runtime_call_txt
                + ", builtin_name="
                + builtin_name_txt
            )
        name_or_attr = self._render_call_name_or_attr(expr_d, fn, fn_name, args, kw, arg_nodes, kw_nodes, first_arg)
        name_or_attr_txt = ""
        if isinstance(name_or_attr, str):
            name_or_attr_txt = str(name_or_attr)
        if name_or_attr_txt != "":
            return name_or_attr_txt
        merged_args = self.merge_call_kw_values(args, kw_values)
        merged_arg_nodes = self.merge_call_arg_nodes(arg_nodes, kw_nodes)
        merged_args = self._coerce_args_for_known_function(fn_name, merged_args, merged_arg_nodes)
        return self._render_call_fallback(fn_name, merged_args)

    def _prepare_call_parts(
        self,
        expr: dict[str, Any],
    ) -> dict[str, Any]:
        """Call ノード前処理（selfhost での静的束縛回避用オーバーライド）。"""
        fn_obj: object = expr.get("func")
        fn_name = self.render_expr(fn_obj)
        arg_nodes_obj: object = self.any_dict_get_list(expr, "args")
        arg_nodes = self.any_to_list(arg_nodes_obj)
        args: list[str] = []
        for arg_node in arg_nodes:
            args.append(self.render_expr(arg_node))
        keywords_obj: object = self.any_dict_get_list(expr, "keywords")
        keywords = self.any_to_list(keywords_obj)
        first_arg: object = expr
        if len(arg_nodes) > 0:
            first_arg = arg_nodes[0]
        kw: dict[str, str] = {}
        kw_values: list[str] = []
        kw_nodes: list[Any] = []
        for k in keywords:
            kd = self.any_to_dict_or_empty(k)
            if len(kd) > 0:
                kw_name = self.any_to_str(kd.get("arg"))
                if kw_name != "":
                    kw_val_node: Any = kd.get("value")
                    kw_val = self.render_expr(kw_val_node)
                    kw[kw_name] = kw_val
                    kw_values.append(kw_val)
                    kw_nodes.append(kw_val_node)
        return {
            "fn": fn_obj,
            "fn_name": fn_name,
            "arg_nodes": arg_nodes,
            "args": args,
            "kw": kw,
            "kw_values": kw_values,
            "kw_nodes": kw_nodes,
            "first_arg": first_arg,
        }

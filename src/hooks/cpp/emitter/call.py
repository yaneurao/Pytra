from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import (
    join_str_list,
    looks_like_runtime_function_name,
    make_user_error,
)


class CppCallEmitter:
    """Runtime-call / import / cast-related helpers split out from CppEmitter."""

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
        raw_name: str,
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
    ) -> tuple[str | None, str]:
        """`Call(Name)` で import 済みシンボルを解決し、必要なら直接呼び出しへ変換する。"""
        raw = raw_name
        imported_module = ""
        has_import_context = raw != "" and not self.is_declared(raw)
        if has_import_context:
            resolved = self._resolve_imported_symbol(raw)
            imported_module = self.any_dict_get_str(resolved, "module", "")
            if imported_module != "":
                raw = self.any_dict_get_str(resolved, "name", "") or raw
        has_import_target = raw != "" and imported_module != ""
        if not has_import_target:
            return None, raw
        mapped_runtime_txt = self._resolve_runtime_call_for_imported_symbol(imported_module, raw) or ""
        route_runtime_call = (
            mapped_runtime_txt != ""
            and mapped_runtime_txt not in {"perf_counter", "Path"}
            and looks_like_runtime_function_name(mapped_runtime_txt)
        )
        if route_runtime_call:
            call_args = self.merge_call_args(args, kw)
            if self._contains_text(mapped_runtime_txt, "::"):
                call_args = self._coerce_args_for_module_function(imported_module, raw, call_args, arg_nodes)
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, call_args, arg_nodes)
            return f"{mapped_runtime_txt}({join_str_list(', ', call_args)})", raw
        has_namespace_map = imported_module in self.module_namespace_map
        target_ns = ""
        if has_namespace_map:
            target_ns = self.module_namespace_map[imported_module]
        if has_namespace_map and target_ns != "":
            namespaced = self._render_namespaced_module_call(
                imported_module,
                target_ns,
                raw,
                args,
                arg_nodes,
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
                return f"int64({arg_expr})"
            if target == "int64" and self.is_any_like_type(arg_t):
                return f"py_to_int64({arg_expr})"
            if target in {"float64", "float32"} and self.is_any_like_type(arg_t):
                return f"py_to_float64({arg_expr})"
            if target == "bool" and self.is_any_like_type(arg_t):
                return f"py_to_bool({arg_expr})"
            if target == "int64":
                return f"py_to_int64({arg_expr})"
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
            "Path",
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
            imported_rendered, raw = self._resolve_or_render_imported_symbol_name_call(raw, args, kw, arg_nodes)
            if imported_rendered is not None:
                return imported_rendered
            if raw.startswith("py_assert_"):
                call_args = self._coerce_py_assert_args(raw, args, arg_nodes)
                return f"pytra::utils::assertions::{raw}({join_str_list(', ', call_args)})"
            if isinstance(raw, str) and raw in self.ref_classes:
                ctor_args = args
                if len(kw) > 0:
                    ctor_arg_names = self._class_method_name_sig(raw, "__init__")
                    ctor_args = self._merge_args_with_kw_by_name(args, kw, ctor_arg_names)
                else:
                    # class ctor でも __init__ シグネチャに合わせて boxing/unboxing を適用する。
                    ctor_args = self._coerce_args_for_class_method(raw, "__init__", ctor_args, arg_nodes)
                return f"::rc_new<{raw}>({join_str_list(', ', ctor_args)})"
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
            attr_rendered = self._render_call_attribute(expr, fn, args, kw, arg_nodes)
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
    ) -> str | None:
        """module.method(...) 呼び出しを処理する。"""
        hook_rendered = self.hook_on_render_module_method(owner_mod, attr, args, kw, arg_nodes)
        if isinstance(hook_rendered, str) and hook_rendered != "":
            return hook_rendered
        merged_args = self.merge_call_args(args, kw)
        owner_mod_norm = owner_mod
        if owner_mod_norm in self.module_namespace_map:
            mapped = self._render_call_module_method_with_namespace(
                owner_mod,
                attr,
                self.module_namespace_map[owner_mod_norm],
                merged_args,
                arg_nodes,
            )
            if mapped is not None:
                return mapped
        fallback = self._render_call_module_method_with_namespace(
            owner_mod,
            attr,
            self._module_name_to_cpp_namespace(owner_mod_norm),
            merged_args,
            arg_nodes,
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
    ) -> str | None:
        """`Class.method(...)` 分岐を処理する。"""
        dispatch_mode = self._class_method_dispatch_mode(owner_t, attr)
        if dispatch_mode == "fallback":
            return None
        call_args = self.merge_call_args(args, kw)
        call_args = self._coerce_args_for_class_method(owner_t, attr, call_args, arg_nodes)
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
        if "bytearray" in owner_types:
            a0 = f"static_cast<uint8>(py_to<int64>({a0}))"
            return f"{owner_expr}.append({a0})"
        list_owner_t = ""
        for t in owner_types:
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
                    a0 = f"{self._cpp_type_text(inner_t)}({a0})"
            return f"{owner_expr}.append({a0})"
        has_any_like_owner = False
        for t in owner_types:
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
            return f"py_append({owner_expr}, {a0})"
        return None

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
        """`super().method(...)` を `Base::method(*this, ...)` へ変換する。"""
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
            return f"{base}::{attr}(*this)"
        return f"{base}::{attr}(*this, {join_str_list(', ', call_args)})"

    def _render_call_attribute(
        self,
        expr: dict[str, Any],
        fn: dict[str, Any],
        args: list[str],
        kw: dict[str, str],
        arg_nodes: list[Any],
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
        super_rendered = self._render_super_attribute_call(owner_obj, attr, args, kw, arg_nodes)
        if super_rendered is not None and super_rendered != "":
            return super_rendered
        if owner_mod != "":
            module_rendered_1 = self._render_call_module_method(owner_mod, attr, args, kw, arg_nodes)
            if module_rendered_1 is not None and module_rendered_1 != "":
                return module_rendered_1
        if self._requires_builtin_method_call_lowering(owner_t, attr):
            owner_label = self.normalize_type_name(owner_t)
            if owner_label == "":
                owner_label = "unknown"
            raise ValueError("builtin method call must be lowered_kind=BuiltinCall: " + owner_label + "." + attr)
        return self._render_call_attribute_non_module(owner_t, owner_expr, attr, fn, args, kw, arg_nodes)

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
    ) -> str | None:
        """`Call(Attribute)` の object/class 系分岐（非 module）を処理する。"""
        hook_object_rendered = self.hook_on_render_object_method(owner_t, owner_expr, attr, args)
        if isinstance(hook_object_rendered, str) and hook_object_rendered != "":
            return hook_object_rendered
        hook_class_rendered = self.hook_on_render_class_method(owner_t, attr, fn, args, kw, arg_nodes)
        if isinstance(hook_class_rendered, str) and hook_class_rendered != "":
            return hook_class_rendered
        class_rendered = self._render_call_class_method(owner_t, attr, fn, args, kw, arg_nodes)
        if class_rendered is not None and class_rendered != "":
            return class_rendered
        return None

    def _collect_class_method_candidates(self, owner_t: str) -> list[str]:
        """class method シグネチャ探索で使う候補クラス名を返す。"""
        t_norm = self.normalize_type_name(owner_t)
        candidates: list[str] = []
        if self._contains_text(t_norm, "|"):
            candidates = self.split_union(t_norm)
        elif t_norm != "":
            candidates = [t_norm]
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
        name_or_attr = self._render_call_name_or_attr(expr_d, fn, fn_name, args, kw, arg_nodes, first_arg)
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

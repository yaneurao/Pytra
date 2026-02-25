from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import join_str_list, looks_like_runtime_function_name


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

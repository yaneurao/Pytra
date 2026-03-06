from __future__ import annotations

from pathlib import Path

from typing import Any
from backends.cpp.emitter.runtime_paths import (
    module_name_to_cpp_include as _module_name_to_cpp_include_impl,
    module_tail_to_cpp_header_path as _module_tail_to_cpp_header_path_impl,
    runtime_cpp_header_exists_for_module as _runtime_cpp_header_exists_for_module_impl,
)
from toolchain.compiler.transpile_cli import (
    append_unique_non_empty,
    dict_any_get_dict,
    dict_any_get_dict_list,
    dict_any_get_str,
    extract_function_arg_types_from_python_source,
    extract_function_signatures_from_python_source,
    python_module_exists_under,
    sort_str_list_copy,
)


RUNTIME_STD_SOURCE_ROOT = Path("src/pytra/std")
RUNTIME_UTILS_SOURCE_ROOT = Path("src/pytra/utils")
RUNTIME_COMPILER_SOURCE_ROOT = Path("src/toolchain/compiler")
RUNTIME_BUILT_IN_SOURCE_ROOT = Path("src/pytra/built_in")
TOOLCHAIN_COMPILER_PREFIX = "toolchain.compiler."
TOOLCHAIN_COMPILER_PREFIX_LEN = len(TOOLCHAIN_COMPILER_PREFIX)


def _module_tail_to_cpp_header_path(module_tail: str) -> str:
    return _module_tail_to_cpp_header_path_impl(module_tail)


def _runtime_cpp_header_exists_for_module(module_name_norm: str) -> bool:
    return _runtime_cpp_header_exists_for_module_impl(module_name_norm)


def _strip_runtime_header_suffix(path_or_tail: str) -> str:
    """`foo.gen` / `foo.ext` suffix を namespace 解決前に剥がす。"""
    if path_or_tail.endswith(".gen") or path_or_tail.endswith(".ext"):
        return path_or_tail[: len(path_or_tail) - 4]
    return path_or_tail


class CppModuleEmitter:
    """Import/include/namespace/module-init helpers extracted from CppEmitter."""

    def _module_name_to_cpp_include(self, module_name: str) -> str:
        """Python import モジュール名を C++ include へ解決する。"""
        module_name_norm = module_name
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return _module_name_to_cpp_include_impl(module_name_norm)
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if python_module_exists_under(RUNTIME_UTILS_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return _module_name_to_cpp_include_impl(module_name_norm)
        if module_name_norm.startswith(TOOLCHAIN_COMPILER_PREFIX):
            tail = module_name_norm[TOOLCHAIN_COMPILER_PREFIX_LEN:]
            if python_module_exists_under(RUNTIME_COMPILER_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return _module_name_to_cpp_include_impl(module_name_norm)
        if module_name_norm.startswith("pytra.built_in."):
            tail = module_name_norm[15:]
            if python_module_exists_under(RUNTIME_BUILT_IN_SOURCE_ROOT, tail) and _runtime_cpp_header_exists_for_module(module_name_norm):
                return _module_name_to_cpp_include_impl(module_name_norm)
        if module_name_norm.find(".") < 0:
            # Accept bare stdlib-style imports such as `import math` / `import time`.
            bare_tail = module_name_norm
            mapped_module = "pytra.std." + bare_tail
            if (
                python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, bare_tail)
                and _runtime_cpp_header_exists_for_module(mapped_module)
            ):
                return _module_name_to_cpp_include_impl(mapped_module)
        return ""

    def _module_name_to_cpp_namespace(self, module_name: str) -> str:
        """Python import モジュール名を C++ namespace へ解決する。"""
        module_name_norm = module_name
        if module_name_norm.startswith("pytra.std."):
            tail = module_name_norm[10:]
            if tail != "":
                return "pytra::std::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.utils."):
            tail = module_name_norm[12:]
            if tail != "":
                return "pytra::utils::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith(TOOLCHAIN_COMPILER_PREFIX):
            tail = module_name_norm[TOOLCHAIN_COMPILER_PREFIX_LEN:]
            if tail != "":
                return "pytra::compiler::" + tail.replace(".", "::")
            return ""
        if module_name_norm.startswith("pytra.built_in."):
            return ""
        if module_name_norm.startswith("pytra."):
            tail = module_name_norm[6:]
            if tail != "":
                return "pytra::" + tail.replace(".", "::")
            return "pytra"
        if module_name_norm.find(".") < 0:
            bare_tail = module_name_norm
            mapped_module = "pytra.std." + bare_tail
            if (
                python_module_exists_under(RUNTIME_STD_SOURCE_ROOT, bare_tail)
                and _runtime_cpp_header_exists_for_module(mapped_module)
            ):
                return "pytra::std::" + bare_tail.replace(".", "::")
        inc = self._module_name_to_cpp_include(module_name_norm)
        if inc.startswith("runtime/cpp/std/") and inc.endswith(".h"):
            tail = _strip_runtime_header_suffix(inc[16 : len(inc) - 2]).replace("/", "::")
            if tail != "":
                return "pytra::std::" + tail
        if inc.startswith("runtime/cpp/utils/") and inc.endswith(".h"):
            tail = _strip_runtime_header_suffix(inc[18 : len(inc) - 2]).replace("/", "::")
            if tail != "":
                return "pytra::utils::" + tail
        if inc.startswith("runtime/cpp/compiler/") and inc.endswith(".h"):
            tail = _strip_runtime_header_suffix(inc[21 : len(inc) - 2]).replace("/", "::")
            if tail != "":
                return "pytra::compiler::" + tail
        return ""

    def _runtime_symbol_module_prefix(self, mod_name: str) -> str:
        """runtime symbol include 解決で使う module prefix（`pytra.std.` 等）を返す。"""
        if mod_name == "pytra.std":
            return "pytra.std."
        if mod_name == "pytra.utils":
            return "pytra.utils."
        if mod_name == "pytra.built_in":
            return "pytra.built_in."
        return ""

    def _runtime_symbol_include(
        self,
        mod_name: str,
        symbol: str,
    ) -> str:
        """`pytra.std/utils` symbol の include path を返す（不要時は空）。"""
        runtime_prefix = self._runtime_symbol_module_prefix(mod_name)
        if runtime_prefix == "" or symbol == "":
            return ""
        return self._module_name_to_cpp_include(runtime_prefix + symbol)

    def _collect_import_cpp_includes(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """EAST body から必要な C++ include を収集する。"""
        includes: list[str] = []
        seen: set[str] = set()
        bindings = dict_any_get_dict_list(meta, "import_bindings")
        if len(bindings) > 0:
            for item in bindings:
                mod_name = dict_any_get_str(item, "module_id")
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                if dict_any_get_str(item, "binding_kind") == "symbol":
                    append_unique_non_empty(
                        includes,
                        seen,
                        self._runtime_symbol_include(mod_name, dict_any_get_str(item, "export_name")),
                    )
            return sort_str_list_copy(includes)
        for stmt in body:
            kind = self._node_kind_from_dict(stmt)
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(dict_any_get_str(ent, "name")))
            elif kind == "ImportFrom":
                mod_name = dict_any_get_str(stmt, "module")
                append_unique_non_empty(includes, seen, self._module_name_to_cpp_include(mod_name))
                for ent in self._dict_stmt_list(stmt.get("names")):
                    append_unique_non_empty(
                        includes,
                        seen,
                        self._runtime_symbol_include(mod_name, dict_any_get_str(ent, "name")),
                    )
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
        module_name_norm = module_name
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

    def _module_function_arg_types(self, module_name: str, fn_name: str) -> list[str]:
        """モジュール関数の引数型列を返す（不明時は空 list）。"""
        module_name_norm = module_name
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
        module_name_norm = module_name
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

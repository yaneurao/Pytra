from __future__ import annotations

from pytra.std import json
from pytra.std import os
from pytra.std.typing import Any
from pytra.std.pathlib import Path

from pytra.compiler.east_parts.code_emitter import CodeEmitter
from hooks.cpp.emitter.analysis import CppAnalysisEmitter
from hooks.cpp.emitter.builtin_runtime import CppBuiltinRuntimeEmitter
from hooks.cpp.emitter.call import CppCallEmitter
from hooks.cpp.emitter.class_def import CppClassEmitter
from hooks.cpp.emitter.collection_expr import CppCollectionExprEmitter
from hooks.cpp.emitter.module import CppModuleEmitter
from hooks.cpp.emitter.operator import CppBinaryOperatorEmitter
from hooks.cpp.emitter.runtime_expr import CppRuntimeExprEmitter
from hooks.cpp.emitter.expr import CppExpressionEmitter
from hooks.cpp.emitter.stmt import CppStatementEmitter
from hooks.cpp.emitter.type_bridge import CppTypeBridgeEmitter
from hooks.cpp.emitter.tmp import CppTemporaryEmitter
from hooks.cpp.emitter.trivia import CppTriviaEmitter
from hooks.cpp.profile import (
    CMP_OPS,
    load_cpp_hooks,
    load_cpp_identifier_rules,
    load_cpp_module_attr_call_map,
    load_cpp_profile,
    load_cpp_type_map,
)
from hooks.cpp.optimizer import optimize_cpp_ir
from hooks.cpp.optimizer import render_cpp_opt_trace


def _write_text_file(path_text: str, text: str) -> None:
    """Write text output while creating parent directory if needed."""
    if path_text == "":
        return
    out_path = Path(path_text)
    parent_txt = str(out_path.parent)
    if parent_txt != "":
        os.makedirs(parent_txt, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")


def _dump_json_file(path_text: str, payload: dict[str, Any]) -> None:
    """Write JSON dump with stable formatting."""
    json_obj: Any = payload
    text = json.dumps(json_obj, ensure_ascii=False, indent=2) + "\n"
    _write_text_file(path_text, text)


def emit_cpp_from_east(
    east_module: dict[str, Any],
    module_namespace_map: dict[str, str],
    negative_index_mode: str = "const_only",
    bounds_check_mode: str = "off",
    floor_div_mode: str = "native",
    mod_mode: str = "native",
    int_width: str = "64",
    str_index_mode: str = "native",
    str_slice_mode: str = "byte",
    opt_level: str = "2",
    top_namespace: str = "",
    emit_main: bool = True,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
) -> str:
    """Emit C++ text from EAST module via CppEmitter (public bridge)."""
    cpp_ir = east_module
    if isinstance(east_module, dict):
        if dump_cpp_ir_before_opt != "":
            _dump_json_file(dump_cpp_ir_before_opt, east_module)
        optimized_ir, report = optimize_cpp_ir(
            east_module,
            opt_level=cpp_opt_level,
            opt_pass_spec=cpp_opt_pass,
            debug_flags={
                "negative_index_mode": negative_index_mode,
                "bounds_check_mode": bounds_check_mode,
                "floor_div_mode": floor_div_mode,
                "mod_mode": mod_mode,
                "int_width": int_width,
                "str_index_mode": str_index_mode,
                "str_slice_mode": str_slice_mode,
                "opt_level": opt_level,
            },
        )
        cpp_ir = optimized_ir
        if dump_cpp_ir_after_opt != "":
            _dump_json_file(dump_cpp_ir_after_opt, cpp_ir)
        if dump_cpp_opt_trace != "":
            _write_text_file(dump_cpp_opt_trace, render_cpp_opt_trace(report))
    return CppEmitter(
        cpp_ir,
        module_namespace_map,
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
        top_namespace,
        emit_main,
    ).transpile()


def install_py2cpp_runtime_symbols(globals_snapshot: dict[str, Any]) -> None:
    """Inject py2cpp globals required by `CppEmitter` dynamic globals."""
    for key, value in globals_snapshot.items():
        if key.startswith("__"):
            continue
        globals()[key] = value


def _attach_cpp_emitter_helper_methods(target_cls: type[CodeEmitter]) -> None:
    """Attach helper handlers directly to CppEmitter to keep single inheritance."""
    helper_classes = (
        CppAnalysisEmitter,
        CppModuleEmitter,
        CppClassEmitter,
        CppTypeBridgeEmitter,
        CppBuiltinRuntimeEmitter,
        CppCollectionExprEmitter,
        CppRuntimeExprEmitter,
        CppCallEmitter,
        CppStatementEmitter,
        CppExpressionEmitter,
        CppBinaryOperatorEmitter,
        CppTriviaEmitter,
        CppTemporaryEmitter,
    )
    for helper_cls in helper_classes:
        for attr_name, attr_value in helper_cls.__dict__.items():
            if attr_name.startswith("__"):
                continue
            if not callable(attr_value):
                continue
            if attr_name in target_cls.__dict__:
                continue
            setattr(target_cls, attr_name, attr_value)


class CppEmitter(
    CodeEmitter,
):
    def __init__(
        self,
        east_doc: dict[str, Any],
        module_namespace_map: dict[str, str],
        negative_index_mode: str = "const_only",
        bounds_check_mode: str = "off",
        floor_div_mode: str = "native",
        mod_mode: str = "native",
        int_width: str = "64",
        str_index_mode: str = "native",
        str_slice_mode: str = "byte",
        opt_level: str = "2",
        top_namespace: str = "",
        emit_main: bool = True,
    ) -> None:
        """変換設定とクラス解析用の状態を初期化する。"""
        profile = load_cpp_profile()
        hooks: dict[str, Any] = load_cpp_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        self.negative_index_mode = negative_index_mode
        self.bounds_check_mode = bounds_check_mode
        self.floor_div_mode = floor_div_mode
        self.mod_mode = mod_mode
        self.int_width = int_width
        self.str_index_mode = str_index_mode
        self.str_slice_mode = str_slice_mode
        self.opt_level = opt_level
        self.top_namespace = top_namespace
        self.emit_main = emit_main
        # NOTE:
        # self-host compile path currently treats EAST payload values as dynamic,
        # so dict[str, Any] -> dict iteration for renaming is disabled for now.
        self.renamed_symbols: dict[str, str] = {}
        self.current_class_name: str | None = None
        self.current_class_base_name: str = ""
        self.current_class_fields: dict[str, str] = {}
        self.current_class_static_fields: set[str] = set()
        self.class_method_names: dict[str, set[str]] = {}
        self.class_method_virtual: dict[str, set[str]] = {}
        self.class_method_arg_types: dict[str, dict[str, list[str]]] = {}
        self.class_method_arg_names: dict[str, dict[str, list[str]]] = {}
        self.class_base: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_storage_hints: dict[str, str] = {}
        self.ref_classes: set[str] = set()
        self.value_classes: set[str] = set()
        self.class_field_owner_unique: dict[str, str] = {}
        self.class_method_owner_unique: dict[str, str] = {}
        self.type_map: dict[str, str] = load_cpp_type_map(self.profile)
        if self.int_width == "32":
            self.type_map["int64"] = "int32"
            self.type_map["uint64"] = "uint32"
        self.module_attr_call_map: dict[str, dict[str, str]] = load_cpp_module_attr_call_map(self.profile)
        self.reserved_words: set[str] = set()
        self.rename_prefix: str = "py_"
        self.reserved_words, self.rename_prefix = load_cpp_identifier_rules(self.profile)
        self.reserved_words.add("main")
        # import 解決テーブルは init_base_state() 側を正とする。
        # CppEmitter 側で再代入すると selfhost 生成C++で基底メンバと
        # 派生メンバが分離し、基底 helper から空テーブルを参照しうる。
        self.module_namespace_map = module_namespace_map
        self.function_arg_types: dict[str, list[str]] = {}
        self.function_return_types: dict[str, str] = {}
        self.current_function_return_type: str = ""
        self.current_function_is_generator: bool = False
        self.current_function_yield_buffer: str = ""
        self.current_function_yield_type: str = "unknown"
        self.declared_var_types: dict[str, str] = {}
        self._module_fn_arg_type_cache: dict[str, dict[str, list[str]]] = {}

    def current_scope_names(self) -> set[str]:
        """現在スコープの識別子集合を返す（selfhost では CppEmitter 側を正とする）。"""
        if len(self.scope_stack) == 0:
            self.scope_stack.append(set())
        return self.scope_stack[-1]

    def declare_in_current_scope(self, name: str) -> None:
        """現在スコープへ識別子を追加する。"""
        if name == "":
            return
        if len(self.scope_stack) == 0:
            self.scope_stack.append(set())
        self.scope_stack[-1].add(name)

    def is_declared(self, name: str) -> bool:
        """現在の可視スコープで識別子が宣言済みかを返す。"""
        i = len(self.scope_stack) - 1
        while i >= 0:
            scope = self.scope_stack[i]
            if name in scope:
                return True
            i -= 1
        return False

    def is_declared_for_name_binding(self, name: str) -> bool:
        """Name 代入の宣言判定用。関数内では module scope を除外する。"""
        if name == "":
            return False
        scope_len = len(self.scope_stack)
        if scope_len <= 1:
            return self.is_declared(name)
        i = scope_len - 1
        while i >= 1:
            scope = self.scope_stack[i]
            if name in scope:
                return True
            i -= 1
        return False

    def should_declare_name_binding(
        self,
        stmt: dict[str, Any],
        name_raw: str,
        default_declare: bool,
    ) -> bool:
        """Name 代入時の宣言判定を Python の local shadow 規則へ寄せる。"""
        if name_raw == "":
            return False
        declare = self.stmt_declare_flag(stmt, default_declare)
        return declare and not self.is_declared_for_name_binding(name_raw)

    def get_expr_type(self, expr: Any) -> str:
        """EAST 型に加えて現在スコープの推論型テーブルも参照する。"""
        node_for_base = self.any_to_dict_or_empty(expr)
        t = self.any_dict_get_str(node_for_base, "resolved_type", "")
        if t != "":
            t = self.normalize_type_name(t)
        kind = self._node_kind_from_dict(node_for_base)
        if kind == "Name":
            nm = self.any_to_str(node_for_base.get("id"))
            if nm in self.declared_var_types:
                declared_t = self.normalize_type_name(self.declared_var_types[nm])
                if declared_t not in {"", "unknown"}:
                    return declared_t
        if kind == "Call":
            call_t = self.normalize_type_name(self._infer_numeric_call_expr_type(node_for_base))
            if call_t != "":
                return call_t
        if kind == "BinOp":
            numeric_t = self.normalize_type_name(self._infer_numeric_expr_type(node_for_base))
            if numeric_t != "":
                return numeric_t
            left_t = self.normalize_type_name(self.get_expr_type(node_for_base.get("left")))
            right_t = self.normalize_type_name(self.get_expr_type(node_for_base.get("right")))
            if self.is_any_like_type(left_t) or self.is_any_like_type(right_t):
                return "object"
        if t not in {"", "unknown"}:
            return t
        if kind == "Name":
            nm = self.any_to_str(node_for_base.get("id"))
            if nm in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[nm])
        if kind == "Attribute":
            owner = self.any_to_dict_or_empty(node_for_base.get("value"))
            if self._node_kind_from_dict(owner) == "Name":
                owner_name = self.any_to_str(owner.get("id"))
                attr = self.any_to_str(node_for_base.get("attr"))
                if owner_name == "self" and attr in self.current_class_fields:
                    return self.normalize_type_name(self.current_class_fields[attr])
        if kind == "Subscript":
            owner_t0 = self.get_expr_type(node_for_base.get("value"))
            owner_t = self.normalize_type_name(owner_t0 if isinstance(owner_t0, str) else "")
            if owner_t.startswith("dict[") and owner_t.endswith("]"):
                dict_parts = self.split_generic(owner_t[5:-1])
                if len(dict_parts) == 2:
                    return self.normalize_type_name(dict_parts[1])
            if owner_t.startswith("list[") and owner_t.endswith("]"):
                list_parts = self.split_generic(owner_t[5:-1])
                if len(list_parts) == 1:
                    return self.normalize_type_name(list_parts[0])
            if owner_t.startswith("tuple[") and owner_t.endswith("]"):
                tuple_parts = self.split_generic(owner_t[6:-1])
                if len(tuple_parts) == 1:
                    return self.normalize_type_name(tuple_parts[0])
        return ""

    # module/import helpers moved to hooks.cpp.emitter.module.CppModuleEmitter.

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
        self._seed_import_maps_from_meta()
        meta: dict[str, Any] = dict_any_get_dict(self.doc, "meta")
        body: list[dict[str, Any]] = []
        raw_body = self.any_dict_get_list(self.doc, "body")
        if isinstance(raw_body, list):
            for s in raw_body:
                if isinstance(s, dict):
                    body.append(s)
        for stmt in body:
            if self._node_kind_from_dict(stmt) == "ClassDef":
                cls_name = self.any_dict_get_str(stmt, "name", "")
                if cls_name != "":
                    self.class_names.add(cls_name)
                    mset: set[str] = set()
                    marg: dict[str, list[str]] = {}
                    marg_names: dict[str, list[str]] = {}
                    class_body: list[dict[str, Any]] = []
                    raw_class_body = self.any_dict_get_list(stmt, "body")
                    if isinstance(raw_class_body, list):
                        for s in raw_class_body:
                            if isinstance(s, dict):
                                class_body.append(s)
                    for s in class_body:
                        if self._node_kind_from_dict(s) == "FunctionDef":
                            fn_name = self.any_dict_get_str(s, "name", "")
                            mset.add(fn_name)
                            arg_types = self.any_to_dict_or_empty(s.get("arg_types"))
                            arg_order = self.any_dict_get_list(s, "arg_order")
                            ordered: list[str] = []
                            ordered_names: list[str] = []
                            for raw_n in arg_order:
                                if isinstance(raw_n, str):
                                    n = str(raw_n)
                                    if n != "self":
                                        ordered_names.append(n)
                                        if n in arg_types:
                                            ordered.append(self.any_to_str(arg_types.get(n)))
                            marg[fn_name] = ordered
                            marg_names[fn_name] = ordered_names
                    self.class_method_names[cls_name] = mset
                    self.class_method_arg_types[cls_name] = marg
                    self.class_method_arg_names[cls_name] = marg_names
                    base_raw = stmt.get("base")
                    base = str(base_raw) if isinstance(base_raw, str) else ""
                    self.class_base[cls_name] = base
                    hint = self.any_dict_get_str(stmt, "class_storage_hint", "ref")
                    self.class_storage_hints[cls_name] = hint if hint in {"value", "ref"} else "ref"
            elif self._node_kind_from_dict(stmt) == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                if fn_name != "":
                    fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                    arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
                    arg_order = self.any_dict_get_list(stmt, "arg_order")
                    ordered: list[str] = []
                    for raw_n in arg_order:
                        if isinstance(raw_n, str):
                            n = str(raw_n)
                            if n in arg_types:
                                ordered.append(self.any_to_str(arg_types.get(n)))
                    self.function_arg_types[fn_name] = ordered
                    self.function_return_types[fn_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))

        self.ref_classes = {name for name, hint in self.class_storage_hints.items() if hint == "ref"}
        changed = True
        while changed:
            changed = False
            for name, base in self.class_base.items():
                if base != "" and base in self.ref_classes and name not in self.ref_classes:
                    self.ref_classes.add(name)
                    changed = True
                if base != "" and name in self.ref_classes and base in self.class_names and base not in self.ref_classes:
                    self.ref_classes.add(base)
                    changed = True
        self.value_classes = {name for name in self.class_names if name not in self.ref_classes}
        field_owner_candidates: dict[str, set[str]] = {}
        for stmt in body:
            if self._node_kind_from_dict(stmt) != "ClassDef":
                continue
            cls_name = self.any_dict_get_str(stmt, "name", "")
            if cls_name == "" or cls_name not in self.ref_classes:
                continue
            field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
            for raw_attr in field_types.keys():
                if not isinstance(raw_attr, str):
                    continue
                attr = raw_attr
                if attr == "":
                    continue
                cur = field_owner_candidates.get(attr)
                if not isinstance(cur, set):
                    cur = set()
                    field_owner_candidates[attr] = cur
                cur.add(cls_name)
        self.class_field_owner_unique = {}
        for attr, owners in field_owner_candidates.items():
            if len(owners) == 1:
                for owner in owners:
                    self.class_field_owner_unique[attr] = owner
        method_owner_candidates: dict[str, set[str]] = {}
        for cls_name, method_names in self.class_method_names.items():
            if cls_name not in self.ref_classes:
                continue
            for raw_method in method_names:
                if not isinstance(raw_method, str):
                    continue
                method = raw_method
                if method == "":
                    continue
                cur = method_owner_candidates.get(method)
                if not isinstance(cur, set):
                    cur = set()
                    method_owner_candidates[method] = cur
                cur.add(cls_name)
        self.class_method_owner_unique = {}
        for method, owners in method_owner_candidates.items():
            if len(owners) == 1:
                for owner in owners:
                    self.class_method_owner_unique[method] = owner

        self.class_method_virtual = {cls: set() for cls in self.class_method_names}
        for derived_cls, methods in self.class_method_names.items():
            for raw_name in methods:
                if not isinstance(raw_name, str):
                    continue
                m = raw_name
                base = self.class_base.get(derived_cls, "")
                while base != "":
                    if m in self.class_method_names.get(base, set()):
                        self.class_method_virtual[base].add(m)
                    base = self.class_base.get(base, "")

        self.emit_module_leading_trivia()
        header_text: str = CPP_HEADER
        if len(header_text) > 0 and header_text[-1] == NEWLINE_CHAR:
            header_text = header_text[:-1]
        self.emit(header_text)
        extra_includes = self._collect_import_cpp_includes(body, meta)
        for inc in extra_includes:
            self.emit(f"#include \"{inc}\"")
        self.emit("")

        if self.top_namespace != "":
            self.emit(f"namespace {self.top_namespace} {{")
            self.emit("")
            self.indent += 1

        module_defs, module_runtime = self._split_module_top_level_stmts(body)
        module_runtime_dicts: list[dict[str, Any]] = []
        for stmt_any in module_runtime:
            stmt = self.any_to_dict_or_empty(stmt_any)
            if len(stmt) > 0:
                module_runtime_dicts.append(stmt)
        module_globals = self._collect_module_global_decls(module_runtime)

        for g_name, g_ty in module_globals:
            self.emit(f"{self._cpp_type_text(g_ty)} {g_name};")
            self.declare_in_current_scope(g_name)
            self.declared_var_types[g_name] = g_ty
        if len(module_globals) > 0:
            self.emit("")

        for stmt_any in module_defs:
            stmt = self.any_to_dict_or_empty(stmt_any)
            if len(stmt) == 0:
                continue
            lines_before_stmt = len(self.lines)
            self.emit_stmt(stmt)
            # Import/ImportFrom など出力を持たない文では余分な空行を増やさない。
            if len(self.lines) == lines_before_stmt:
                continue
            self.emit("")

        has_module_runtime = len(module_runtime_dicts) > 0
        if has_module_runtime:
            self.emit("static void __pytra_module_init() {")
            self.indent += 1
            self.emit("static bool __initialized = false;")
            self.emit("if (__initialized) return;")
            self.emit("__initialized = true;")
            self.scope_stack.append(set())
            self.emit_stmt_list(module_runtime_dicts)
            self.scope_stack.pop()
            self.indent -= 1
            self.emit("}")
            self.emit("")

        if self.emit_main:
            if self.top_namespace != "":
                self.indent -= 1
                self.emit(f"}}  // namespace {self.top_namespace}")
                self.emit("")
            has_pytra_main = False
            for stmt in body:
                if self._node_kind_from_dict(stmt) == "FunctionDef" and self.any_to_str(stmt.get("name")) == "__pytra_main":
                    has_pytra_main = True
                    break
            self.emit("int main(int argc, char** argv) {")
            self.indent += 1
            self.emit("pytra_configure_from_argv(argc, argv);")
            self.scope_stack.append(set())
            if has_module_runtime:
                if self.top_namespace != "":
                    self.emit(f"{self.top_namespace}::__pytra_module_init();")
                else:
                    self.emit("__pytra_module_init();")
            main_guard: list[dict[str, Any]] = []
            raw_main_guard = self.any_dict_get_list(self.doc, "main_guard_body")
            if isinstance(raw_main_guard, list):
                for s in raw_main_guard:
                    if isinstance(s, dict):
                        main_guard.append(s)
            if has_pytra_main:
                default_args: list[str] = []
                pytra_args = self.function_arg_types.get("__pytra_main", default_args)
                if isinstance(pytra_args, list) and len(pytra_args) >= 1:
                    if self.top_namespace != "":
                        self.emit(f"{self.top_namespace}::__pytra_main(py_runtime_argv());")
                    else:
                        self.emit("__pytra_main(py_runtime_argv());")
                else:
                    if self.top_namespace != "":
                        self.emit(f"{self.top_namespace}::__pytra_main();")
                    else:
                        self.emit("__pytra_main();")
            else:
                if self.top_namespace != "":
                    self.emit(f"using namespace {self.top_namespace};")
                self.emit_stmt_list(main_guard)
            self.scope_stack.pop()
            self.emit("return 0;")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        elif self.top_namespace != "":
            self.indent -= 1
            self.emit(f"}}  // namespace {self.top_namespace}")
            self.emit("")
        return NEWLINE_CHAR.join(self.lines)

    def _infer_name_assign_type(self, stmt: dict[str, Any], target_node: dict[str, Any]) -> str:
        """`Name = ...` / `AnnAssign Name` の宣言候補型を推定する。"""
        decl_t = self.normalize_type_name(self.any_dict_get_str(stmt, "decl_type", ""))
        if decl_t not in {"", "unknown"}:
            return decl_t
        ann_t = self.normalize_type_name(self.any_dict_get_str(stmt, "annotation", ""))
        if ann_t not in {"", "unknown"}:
            return ann_t
        t_target = self.get_expr_type(stmt.get("target"))
        t_target_norm = self.normalize_type_name(t_target) if isinstance(t_target, str) else ""
        if t_target_norm not in {"", "unknown"} and (not self.is_any_like_type(t_target_norm)):
            return t_target_norm
        t_value = self.get_expr_type(stmt.get("value"))
        t_value_norm = self.normalize_type_name(t_value) if isinstance(t_value, str) else ""
        if t_value_norm not in {"", "unknown"} and (not self.is_any_like_type(t_value_norm)):
            return t_value_norm
        t_value_numeric = self._infer_numeric_expr_type(stmt.get("value"))
        if t_value_numeric != "":
            return self.normalize_type_name(t_value_numeric)
        if t_value_norm not in {"", "unknown"}:
            return t_value_norm
        if t_target_norm not in {"", "unknown"}:
            return t_target_norm
        return ""

    def _is_int_decl_type(self, t: str) -> bool:
        """整数系 decl type か判定する。"""
        t_norm = self.normalize_type_name(t)
        return t_norm in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}

    def _is_float_decl_type(self, t: str) -> bool:
        """浮動小数点系 decl type か判定する。"""
        t_norm = self.normalize_type_name(t)
        return t_norm in {"float32", "float64"}

    def _is_numeric_decl_type(self, t: str) -> bool:
        """数値系 decl type（int/float）か判定する。"""
        return self._is_int_decl_type(t) or self._is_float_decl_type(t)

    def _infer_numeric_expr_type(self, expr: Any) -> str:
        """数値式から宣言候補型（`int64`/`float64`）を推定する。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return ""
        kind = self._node_kind_from_dict(node)
        if kind == "Constant":
            value_obj = node.get("value")
            if isinstance(value_obj, bool):
                return "bool"
            if isinstance(value_obj, int):
                return "int64"
            if isinstance(value_obj, float):
                return "float64"
            return ""
        if kind == "Name":
            name = self.any_to_str(node.get("id"))
            if name != "" and name in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[name])
            return ""
        if kind == "UnaryOp":
            op = self.any_to_str(node.get("op"))
            if op in {"USub", "UAdd"}:
                operand_t = self.normalize_type_name(self._infer_numeric_expr_type(node.get("operand")))
                if self._is_numeric_decl_type(operand_t):
                    return operand_t
            return ""
        if kind == "Call":
            return self._infer_numeric_call_expr_type(node)
        if kind != "BinOp":
            return ""
        left_t = self.normalize_type_name(self.get_expr_type(node.get("left")))
        right_t = self.normalize_type_name(self.get_expr_type(node.get("right")))
        if left_t in {"", "unknown"}:
            left_t = self.normalize_type_name(self._infer_numeric_expr_type(node.get("left")))
        if right_t in {"", "unknown"}:
            right_t = self.normalize_type_name(self._infer_numeric_expr_type(node.get("right")))
        if (not self._is_numeric_decl_type(left_t)) or (not self._is_numeric_decl_type(right_t)):
            return ""
        op = self.any_to_str(node.get("op"))
        if op == "Div":
            return "float64"
        if self._is_float_decl_type(left_t) or self._is_float_decl_type(right_t):
            return "float64"
        return "int64"

    def _infer_numeric_call_expr_type(self, call_node: dict[str, Any]) -> str:
        """Call ノードから数値返り値型を推定する。"""
        if len(call_node) == 0:
            return ""
        fn_node = self.any_to_dict_or_empty(call_node.get("func"))
        fn_kind = self._node_kind_from_dict(fn_node)
        fn_name = ""
        if fn_kind == "Name":
            fn_name = self.any_to_str(fn_node.get("id"))
            if fn_name != "":
                ret_t = self.normalize_type_name(self.function_return_types.get(fn_name, ""))
                if self._is_numeric_decl_type(ret_t):
                    return ret_t
        elif fn_kind == "Attribute":
            owner = self.any_to_dict_or_empty(fn_node.get("value"))
            owner_kind = self._node_kind_from_dict(owner)
            owner_name = self.any_to_str(owner.get("id")) if owner_kind == "Name" else ""
            attr = self.any_to_str(fn_node.get("attr"))
            if owner_name == "math" and attr in {"sin", "cos", "tan", "sqrt", "exp", "log", "log10", "fabs", "floor", "ceil"}:
                return "float64"
        if fn_name in {"int"}:
            return "int64"
        if fn_name in {"float"}:
            return "float64"
        if fn_name in {"max", "min"}:
            args = self.any_dict_get_list(call_node, "args")
            if len(args) == 0:
                return ""
            saw_float = False
            for arg in args:
                at = self.normalize_type_name(self.get_expr_type(arg))
                if at in {"", "unknown"}:
                    at = self.normalize_type_name(self._infer_numeric_expr_type(arg))
                if not self._is_numeric_decl_type(at):
                    return ""
                if self._is_float_decl_type(at):
                    saw_float = True
            return "float64" if saw_float else "int64"
        return ""

    def _byte_from_str_expr(self, node: Any) -> str:
        """str 系式を uint8 初期化向けの char 式へ変換する。"""
        ch = self._one_char_str_const(node)
        if ch != "":
            return cpp_char_lit(ch)
        return self._str_index_char_access(node)

    def _allows_none_default(self, east_t: str) -> bool:
        """型が `None` 既定値（optional）を許容するか判定する。"""
        t = self.normalize_type_name(east_t)
        if t == "None":
            return True
        if t.startswith("optional[") and t.endswith("]"):
            return True
        if self._contains_text(t, "|"):
            parts = self.split_union(t)
            for part in parts:
                if part == "None":
                    return True
        return False

    def _none_default_expr_for_type(self, east_t: str) -> str:
        """`None` 既定値を C++ 側の型別既定値へ変換する。"""
        t = self.normalize_type_name(east_t)
        if t in {"", "unknown", "Any", "object"}:
            return "object{}"
        if self._allows_none_default(t):
            return "::std::nullopt"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return "0"
        if t in {"float32", "float64"}:
            return "0.0"
        if t == "bool":
            return "false"
        if t == "str":
            return "str()"
        if t == "bytes":
            return "bytes()"
        if t == "bytearray":
            return "bytearray()"
        if t == "Path":
            return "Path()"
        cpp_t = self._cpp_type_text(t)
        if cpp_t.startswith("::std::optional<"):
            return "::std::nullopt"
        return cpp_t + "{}"

    def _rewrite_nullopt_default_for_typed_target(self, rendered_expr: str, east_target_t: str) -> str:
        """`dict_get_node/py_dict_get_default(..., nullopt)` を型付き既定値へ置換する。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        if t == "" or self.is_any_like_type(t) or self._allows_none_default(t):
            return rendered_expr
        typed_default = self._none_default_expr_for_type(t)
        if typed_default in {"", "::std::nullopt", "std::nullopt"}:
            return rendered_expr
        if not (
            rendered_expr.startswith("dict_get_node(") or rendered_expr.startswith("py_dict_get_default(")
        ):
            return rendered_expr
        tail_a = ", ::std::nullopt)"
        tail_b = ", std::nullopt)"
        if rendered_expr.endswith(tail_a):
            return rendered_expr[: -len(tail_a)] + ", " + typed_default + ")"
        if rendered_expr.endswith(tail_b):
            return rendered_expr[: -len(tail_b)] + ", " + typed_default + ")"
        return rendered_expr

    def _coerce_param_signature_default(self, rendered_expr: str, east_target_t: str) -> str:
        """関数シグネチャ既定値を引数型に合わせて整形する。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        out = self._rewrite_nullopt_default_for_typed_target(rendered_expr, t)
        if not self.is_any_like_type(t):
            return out
        if out in {"object{}", "object()"}:
            return out
        if self.is_boxed_object_expr(out):
            return out
        return f"make_object({out})"

    def _render_param_default_expr(self, node: Any, east_target_t: str) -> str:
        """関数引数既定値ノードを C++ 式へ変換する。"""
        nd = self.any_to_dict_or_empty(node)
        if len(nd) == 0:
            return ""
        kind = self._node_kind_from_dict(nd)
        if kind == "Constant":
            if "value" not in nd:
                return ""
            val = nd["value"]
            if val is None:
                return self._none_default_expr_for_type(east_target_t)
            if isinstance(val, bool):
                return "true" if val else "false"
            if isinstance(val, int):
                return str(val)
            if isinstance(val, float):
                return str(val)
            if isinstance(val, str):
                return cpp_string_lit(val)
            return ""
        if kind == "Name":
            ident = self.any_to_str(nd.get("id"))
            if ident == "None":
                return self._none_default_expr_for_type(east_target_t)
            if ident == "True":
                return "true"
            if ident == "False":
                return "false"
            return ""
        if kind == "Tuple":
            elems = self.any_dict_get_list(nd, "elements")
            parts: list[str] = []
            for elem in elems:
                txt = self._render_param_default_expr(elem, "Any")
                if txt == "":
                    return ""
                parts.append(txt)
            return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
        _ = east_target_t
        return ""

    def _expr_node_has_payload(self, node: Any) -> bool:
        """式ノードとして有効な実体を持つとき true を返す。"""
        node_d = self.any_to_dict_or_empty(node)
        if len(node_d) == 0:
            return False
        return self._node_kind_from_dict(node_d) != ""

    def _expr_is_none_marker(self, expr_txt: str) -> bool:
        """`/* none */` を示す式文字列か判定する。"""
        return expr_txt.strip() == "/* none */"

    def _merge_decl_types_for_branch_join(self, left_t: str, right_t: str) -> str:
        """if/else 合流時の宣言型候補をマージする。"""
        l = self.normalize_type_name(left_t)
        r = self.normalize_type_name(right_t)
        if l in {"", "unknown"}:
            l = ""
        if r in {"", "unknown"}:
            r = ""
        if l == "":
            return r
        if r == "":
            return l
        if l == r:
            return l
        int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_types = {"float32", "float64"}
        if l in int_types and r in int_types:
            return "int64"
        if l in float_types and r in float_types:
            return "float64"
        if (l in int_types and r in float_types) or (l in float_types and r in int_types):
            return "float64"
        if self.is_any_like_type(l) or self.is_any_like_type(r):
            return "object"
        return l

    def _predeclare_if_join_names(self, body_stmts: list[dict[str, Any]], else_stmts: list[dict[str, Any]]) -> None:
        """if/else 両分岐で代入される名前を外側スコープへ事前宣言する。"""
        if len(else_stmts) == 0:
            return
        body_types = self._collect_assigned_name_types(body_stmts)
        else_types = self._collect_assigned_name_types(else_stmts)
        for name, _body_ty in body_types.items():
            _ = _body_ty
            if name == "":
                continue
            if name not in else_types:
                continue
            if self.is_declared(name):
                continue
            decl_t = self._merge_decl_types_for_branch_join(body_types[name], else_types[name])
            decl_t = decl_t if decl_t != "" else "object"
            cpp_t = self._cpp_type_text(decl_t)
            fallback_to_object = cpp_t in {"", "auto"}
            decl_t = "object" if fallback_to_object else decl_t
            cpp_t = "object" if fallback_to_object else cpp_t
            self.emit(f"{cpp_t} {name};")
            self.declare_in_current_scope(name)
            self.declared_var_types[name] = decl_t

    def _can_omit_braces_for_single_stmt(self, stmts: list[dict[str, Any]]) -> bool:
        """単文ブロックで波括弧を省略可能か判定する。"""
        if not self._opt_ge(1):
            return False
        if len(stmts) != 1:
            return False
        one = stmts[0]
        kind = self.any_dict_get_str(one, "kind", "")
        if kind == "Assign":
            target = self.any_to_dict_or_empty(one.get("target"))
            if self._node_kind_from_dict(target) == "Tuple":
                return False
        return kind in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}

    def _default_stmt_omit_braces(self, kind: str, stmt: dict[str, Any], default_value: bool = False) -> bool:
        """hooks 無効時にも C++ 既定方針で brace 省略を決める。"""
        if not self._opt_ge(1):
            return False
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        if kind == "If":
            else_stmts = self._dict_stmt_list(stmt.get("orelse"))
            if not self._can_omit_braces_for_single_stmt(body_stmts):
                return False
            if len(else_stmts) == 0:
                return True
            return self._can_omit_braces_for_single_stmt(else_stmts)
        if kind == "ForRange":
            if len(self.any_dict_get_list(stmt, "orelse")) != 0:
                return False
            return self._can_omit_braces_for_single_stmt(body_stmts)
        if kind == "For":
            if len(self.any_dict_get_list(stmt, "orelse")) != 0:
                return False
            target = self.any_to_dict_or_empty(stmt.get("target"))
            if self._node_kind_from_dict(target) == "Tuple":
                return False
            return self._can_omit_braces_for_single_stmt(body_stmts)
        return default_value

    def _default_for_range_mode(self, stmt: dict[str, Any], default_mode: str, step_expr: str) -> str:
        """hooks 無効時の ForRange mode を C++ 既定方針で解決する。"""
        mode = self.any_to_str(stmt.get("range_mode"))
        if mode == "":
            mode = default_mode
        if mode not in {"ascending", "descending", "dynamic"}:
            mode = default_mode if default_mode in {"ascending", "descending", "dynamic"} else "dynamic"
        if mode == "dynamic":
            step_txt = step_expr.strip()
            if step_txt in {"1", "+1"}:
                return "ascending"
            if step_txt == "-1":
                return "descending"
        return mode

    def _emit_stmt_kind_fallback(self, kind: str, stmt: dict[str, Any]) -> bool:
        """`on_emit_stmt_kind` 未処理時の C++ 既定ディスパッチ。"""
        self.render_trivia(stmt)
        if kind == "Expr":
            self._emit_expr_stmt(stmt)
        elif kind == "Return":
            self._emit_return_stmt(stmt)
        elif kind == "Assign":
            self._emit_assign_stmt(stmt)
        elif kind == "Swap":
            self._emit_swap_stmt(stmt)
        elif kind == "AnnAssign":
            self._emit_annassign_stmt(stmt)
        elif kind == "AugAssign":
            self._emit_augassign_stmt(stmt)
        elif kind == "If":
            self._emit_if_stmt(stmt)
        elif kind == "While":
            self._emit_while_stmt(stmt)
        elif kind == "ForRange" or kind == "For":
            raise ValueError("legacy loop node is unsupported in EAST3; lower to ForCore: " + kind)
        elif kind == "ForCore":
            self.emit_for_core(stmt)
        elif kind == "Raise":
            self._emit_raise_stmt(stmt)
        elif kind == "Try":
            self._emit_try_stmt(stmt)
        elif kind == "FunctionDef":
            self._emit_function_stmt(stmt)
        elif kind == "ClassDef":
            self._emit_class_stmt(stmt)
        elif kind == "Pass":
            self._emit_pass_stmt(stmt)
        elif kind == "Break":
            self._emit_break_stmt(stmt)
        elif kind == "Continue":
            self._emit_continue_stmt(stmt)
        elif kind == "Yield":
            self._emit_yield_stmt(stmt)
        elif kind == "Import" or kind == "ImportFrom":
            self._emit_noop_stmt(stmt)
        else:
            return False
        return True

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """1つの文ノードを C++ 文へ変換して出力する。"""
        hook_stmt = self.hook_on_emit_stmt(stmt)
        if hook_stmt:
            return
        kind = self._node_kind_from_dict(stmt)
        if self.hook_on_emit_stmt_kind(kind, stmt):
            return
        self.render_trivia(stmt)
        self.emit(f"/* unsupported stmt kind: {kind} */")

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        """CppEmitter 側で文ディスパッチを固定し、selfhost時の静的束縛を避ける。"""
        for stmt in stmts:
            self.emit_stmt(stmt)

    def emit_scoped_stmt_list(self, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """selfhost C++ で base 実装へ静的束縛されるのを避ける。"""
        self.indent += 1
        self.scope_stack.append(scope_names)
        for stmt in stmts:
            self.emit_stmt(stmt)
        self.scope_stack.pop()
        self.indent -= 1

    def emit_scoped_block(self, open_line: str, stmts: list[dict[str, Any]], scope_names: set[str]) -> None:
        """selfhost C++ 向けに scoped block も CppEmitter 側で固定する。"""
        self.emit(open_line)
        self.emit_scoped_stmt_list(stmts, scope_names)
        self.emit_block_close()

    def _emit_noop_stmt(self, stmt: dict[str, Any]) -> None:
        kind = self._node_kind_from_dict(stmt)
        ents = self._dict_stmt_list(stmt.get("names"))
        if kind == "Import":
            for ent in ents:
                name = dict_any_get_str(ent, "name")
                asname = dict_any_get_str(ent, "asname")
                local_name = asname if asname != "" else self._last_dotted_name(name)
                set_import_module_binding(self.import_modules, local_name, name)
            return
        if kind == "ImportFrom":
            mod = dict_any_get_str(stmt, "module")
            for ent in ents:
                name = dict_any_get_str(ent, "name")
                asname = dict_any_get_str(ent, "asname")
                local_name = asname if asname != "" else name
                set_import_symbol_binding_and_module_set(
                    self.import_symbols, self.import_symbol_modules, local_name, mod, name
                )
        return

    def _emit_pass_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("pass_stmt", "/* pass */"))

    def _emit_break_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("break_stmt", "break;"))

    def _emit_continue_stmt(self, stmt: dict[str, Any]) -> None:
        _ = stmt
        self.emit(self.syntax_text("continue_stmt", "continue;"))

    def _emit_swap_stmt(self, stmt: dict[str, Any]) -> None:
        left = self.render_expr(stmt.get("left"))
        right = self.render_expr(stmt.get("right"))
        self.emit(
            self.syntax_line(
                "swap_stmt",
                "::std::swap({left}, {right});",
                {"left": left, "right": right},
            )
        )

    def _emit_raise_stmt(self, stmt: dict[str, Any]) -> None:
        if not isinstance(stmt.get("exc"), dict):
            self.emit(self.syntax_text("raise_default", 'throw ::std::runtime_error("raise");'))
        else:
            self.emit(
                self.syntax_line(
                    "raise_expr",
                    "throw {exc};",
                    {"exc": self.render_expr(stmt.get("exc"))},
                )
            )

    def _emit_local_function_stmt(self, stmt: dict[str, Any]) -> None:
        """ローカル関数定義をラムダ変数へ lowering して出力する。"""
        name = self.any_dict_get_str(stmt, "name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        ret = self.cpp_type(stmt.get("return_type"))
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_defaults = self.any_to_dict_or_empty(stmt.get("arg_defaults"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        params: list[str] = []
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "" and raw_n in arg_types:
                arg_names.append(str(raw_n))
        arg_type_ordered: list[str] = []
        for n in arg_names:
            t = self.normalize_type_name(self.any_to_str(arg_types.get(n)))
            t = t if t != "" else "unknown"
            arg_type_ordered.append(t)
        mutated_params = self._collect_mutated_params(body_stmts, arg_names)
        is_recursive_local_fn = self._stmt_list_contains_call_name(body_stmts, emitted_name)
        # ローカル関数呼び出しの coercion に使うため、現在スコープ中は登録を維持する。
        self.function_arg_types[emitted_name] = arg_type_ordered
        self.function_return_types[emitted_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
        fn_scope: set[str] = set()
        fn_sig_params: list[str] = []
        for n in arg_names:
            t = self.any_to_str(arg_types.get(n))
            ct = self._cpp_type_text(t)
            usage = self.any_to_str(arg_usage.get(n))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and n in mutated_params:
                usage = "mutable"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            param_txt = ""
            if by_ref and usage == "mutable":
                use_object_param = ct == "object"
                param_txt = f"{ct} {n}" if use_object_param else f"{ct}& {n}"
                fn_sig_params.append(ct if use_object_param else f"{ct}&")
            elif by_ref:
                param_txt = f"const {ct}& {n}"
                fn_sig_params.append(f"const {ct}&")
            else:
                param_txt = f"{ct} {n}"
                fn_sig_params.append(ct)
            if n in arg_defaults:
                default_txt = self._render_param_default_expr(arg_defaults.get(n), t)
                if default_txt != "":
                    default_txt = self._coerce_param_signature_default(default_txt, t)
                    param_txt += f" = {default_txt}"
            params.append(param_txt)
            fn_scope.add(n)
        params_txt = ", ".join(params)
        if is_recursive_local_fn:
            fn_sig = ", ".join(fn_sig_params)
            self.emit(f"::std::function<{ret}({fn_sig})> {emitted_name};")
            self.emit(f"{emitted_name} = [&]({params_txt}) -> {ret} {{")
        else:
            self.emit(f"auto {emitted_name} = [&]({params_txt}) -> {ret} {{")
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        prev_ret = self.current_function_return_type
        prev_decl_types = self.declared_var_types
        self.declared_var_types = {}
        for an in arg_names:
            at = self.any_to_str(arg_types.get(an))
            if at != "":
                self.declared_var_types[an] = self.normalize_type_name(at)
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        docstring = self.any_to_str(stmt.get("docstring"))
        if docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(body_stmts)
        self.current_function_return_type = prev_ret
        self.declared_var_types = prev_decl_types
        self.scope_stack.pop()
        self.indent -= 1
        self.emit("};")

    def _emit_function_stmt(self, stmt: dict[str, Any]) -> None:
        # class body 直下の FunctionDef は class method として扱う。
        # 関数本体（scope_stack>1）での nested def は local lambda へ落とす。
        if self.current_class_name is not None and len(self.scope_stack) == 1:
            self.emit_function(stmt, True)
            return
        if len(self.scope_stack) > 1:
            self._emit_local_function_stmt(stmt)
            return
        self.emit_function(stmt, False)

    def _emit_class_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_class(stmt)

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        value_is_dict: bool = len(value_node) > 0
        if value_is_dict and self._node_kind_from_dict(value_node) == "Constant" and isinstance(value_node.get("value"), str):
            self.emit_block_comment(str(value_node.get("value")))
            return
        if value_is_dict and self._is_redundant_super_init_call(stmt.get("value")):
            self.emit("/* super().__init__ omitted: base ctor is called implicitly */")
            return
        if not value_is_dict:
            self.emit("/* unsupported expr */")
            return
        self.emit_bridge_comment(value_node)
        rendered = self.render_expr(stmt.get("value"))
        # Guard against stray identifier-only expression statements (e.g. "r;").
        if isinstance(rendered, str) and self._is_identifier_expr(rendered):
            if rendered == "break" or rendered == "py_break":
                self.emit("break;")
            elif rendered == "continue" or rendered == "py_continue":
                self.emit("continue;")
            elif rendered == "pass":
                self.emit("/* pass */")
            else:
                self.emit(f"/* omitted bare identifier expression: {rendered} */")
            return
        self.emit(
            self.syntax_line(
                "expr_stmt",
                "{expr};",
                {"expr": rendered},
            )
        )

    def _emit_return_stmt(self, stmt: dict[str, Any]) -> None:
        if self.current_function_is_generator:
            buf = self.current_function_yield_buffer
            if buf == "":
                self.emit("/* invalid generator return */")
                return
            self.emit(f"return {buf};")
            return
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        v_is_dict: bool = len(value_node) > 0
        if not v_is_dict:
            self.emit(self.syntax_text("return_void", "return;"))
            return
        rv = self.render_expr(stmt.get("value"))
        ret_t = self.current_function_return_type
        if ret_t != "":
            rv = self._rewrite_nullopt_default_for_typed_target(rv, ret_t)
        expr_t0 = self.get_expr_type(stmt.get("value"))
        expr_t = expr_t0 if isinstance(expr_t0, str) else ""
        if self.is_any_like_type(ret_t) and (not self.is_any_like_type(expr_t)):
            rv = self.render_expr_as_any(stmt.get("value"))
        if self._can_runtime_cast_target(ret_t) and self.is_any_like_type(expr_t):
            rv = self._coerce_any_expr_to_target_via_unbox(
                rv,
                stmt.get("value"),
                ret_t,
                f"return:{ret_t}",
            )
        self.emit(
            self.syntax_line(
                "return_value",
                "return {value};",
                {"value": rv},
            )
        )

    def _emit_yield_stmt(self, stmt: dict[str, Any]) -> None:
        if not self.current_function_is_generator or self.current_function_yield_buffer == "":
            self.emit("/* unsupported yield outside generator */")
            return
        buf = self.current_function_yield_buffer
        value_node = self.any_to_dict_or_empty(stmt.get("value"))
        if len(value_node) == 0:
            yty = self.current_function_yield_type
            default_expr = "object()"
            if yty in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                default_expr = "0"
            elif yty in {"float32", "float64"}:
                default_expr = "0.0"
            elif yty == "bool":
                default_expr = "false"
            elif yty == "str":
                default_expr = "str()"
            self.emit(f"{buf}.append({default_expr});")
            return
        yv = self.render_expr(stmt.get("value"))
        yv_t = self.get_expr_type(stmt.get("value"))
        if self.current_function_yield_type not in {"", "unknown", "Any", "object"} and self.is_any_like_type(yv_t):
            yv = self._coerce_any_expr_to_target_via_unbox(
                yv,
                stmt.get("value"),
                self.current_function_yield_type,
                f"yield:{self.current_function_yield_type}",
            )
        self.emit(f"{buf}.append({yv});")

    def _emit_assign_stmt(self, stmt: dict[str, Any]) -> None:
        self.emit_assign(stmt)

    def _is_reexport_assign(self, target: dict[str, Any], value: dict[str, Any]) -> bool:
        """`Name = imported_symbol` 形式の再エクスポート代入かを返す。"""
        if len(self.scope_stack) != 1:
            return False
        if self._node_kind_from_dict(target) != "Name":
            return False
        kind = self._node_kind_from_dict(value)
        if kind == "Name":
            name = dict_any_get_str(value, "id")
            if name in self.import_modules:
                return True
            if name in self.import_symbols:
                return True
            return False
        if kind == "Attribute":
            owner = dict_any_get_dict(value, "value")
            if self._node_kind_from_dict(owner) != "Name":
                return False
            owner_name = dict_any_get_str(owner, "id")
            if owner_name in self.import_modules:
                return True
            if owner_name in self.import_symbols:
                return True
        return False

    def render_lvalue(self, expr: Any) -> str:
        """左辺値文脈の式（添字代入含む）を C++ 文字列へ変換する。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return self.render_expr(expr)
        if self._node_kind_from_dict(node) != "Subscript":
            return self.render_expr(expr)
        val = self.render_expr(node.get("value"))
        val_ty0 = self.get_expr_type(node.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        idx = self.render_expr(node.get("slice"))
        idx_t0 = self.get_expr_type(node.get("slice"))
        idx_t = idx_t0 if isinstance(idx_t0, str) else ""
        if val_ty.startswith("dict["):
            idx = self._coerce_dict_key_expr(node.get("value"), idx, node.get("slice"))
            return f"{val}[{idx}]"
        if self.is_indexable_sequence_type(val_ty):
            if self.is_any_like_type(idx_t):
                idx = f"py_to<int64>({idx})"
            return self._render_sequence_index(val, idx, node.get("slice"))
        return f"{val}[{idx}]"

    def _render_sequence_index(self, value_expr: str, index_expr: str, index_node: Any) -> str:
        """list/str 添字アクセスのモード別コード生成を行う。"""
        if self.negative_index_mode == "always":
            return f"py_at({value_expr}, {index_expr})"
        if self.negative_index_mode == "const_only" and self._is_negative_const_index(index_node):
            return f"py_at({value_expr}, {index_expr})"
        if self.bounds_check_mode == "always":
            return f"py_at_bounds({value_expr}, {index_expr})"
        if self.bounds_check_mode == "debug":
            return f"py_at_bounds_debug({value_expr}, {index_expr})"
        return f"{value_expr}[{index_expr}]"

    def _coerce_dict_key_expr(self, owner_node: Any, key_expr: str, key_node: Any) -> str:
        """`dict[K, V]` 参照用の key 式を K に合わせて整形する。"""
        owner_t0 = self.get_expr_type(owner_node)
        owner_t = owner_t0 if isinstance(owner_t0, str) else ""
        if self.is_any_like_type(owner_t):
            return key_expr
        if not owner_t.startswith("dict[") or not owner_t.endswith("]"):
            return key_expr
        inner = self.split_generic(owner_t[5:-1])
        if len(inner) != 2:
            return key_expr
        key_t = self.normalize_type_name(inner[0])
        if key_t in {"", "unknown"}:
            return key_expr
        if self.is_any_like_type(key_t):
            if self.is_boxed_object_expr(key_expr):
                return key_expr
            key_node_d = self.any_to_dict_or_empty(key_node)
            if len(key_node_d) > 0:
                return self.render_expr(self._build_box_expr_node(key_node))
            return f"make_object({key_expr})"
        if key_t == "str":
            return f"py_to_string({key_expr})"
        return key_expr

    # class emit helpers moved to hooks.cpp.emitter.class_def.CppClassEmitter.

    # builtin runtime_call dispatch helpers moved to hooks.cpp.emitter.builtin_runtime.CppBuiltinRuntimeEmitter.

    def _render_dict_get_default_expr(
        self,
        owner_node: Any,
        key_node: Any,
        default_node: Any,
        out_t: str,
        default_t: str,
        owner_value_t: str,
        objectish_owner: bool,
        owner_optional_object_dict: bool,
    ) -> str:
        """`dict.get(key, default)` の既定値あり経路を描画する。"""
        owner_expr = self.render_expr(owner_node)
        key_expr = self.render_expr(key_node)
        default_expr = self.render_expr(default_node)
        if not objectish_owner:
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
        int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_out_types = {"float32", "float64"}
        if objectish_owner and out_t == "bool":
            return f"dict_get_bool({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t == "str":
            return f"dict_get_str({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in int_out_types:
            cast_t = self._cpp_type_text(out_t)
            return f"static_cast<{cast_t}>(dict_get_int({owner_expr}, {key_expr}, py_to<int64>({default_expr})))"
        if objectish_owner and out_t in float_out_types:
            cast_t = self._cpp_type_text(out_t)
            return f"static_cast<{cast_t}>(dict_get_float({owner_expr}, {key_expr}, py_to<float64>({default_expr})))"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "bool":
            return f"dict_get_bool({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "str":
            return f"dict_get_str({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in int_out_types:
            return f"dict_get_int({owner_expr}, {key_expr}, py_to<int64>({default_expr}))"
        if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in float_out_types:
            return f"dict_get_float({owner_expr}, {key_expr}, py_to<float64>({default_expr}))"
        if objectish_owner and out_t in {"", "unknown"} and default_t.startswith("list["):
            return f"dict_get_list({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and out_t.startswith("list["):
            return f"dict_get_list({owner_expr}, {key_expr}, {default_expr})"
        if objectish_owner and (self.is_any_like_type(out_t) or out_t == "object"):
            if owner_optional_object_dict:
                boxed_default = self._box_any_target_value(default_expr, default_node)
                return f"py_dict_get_default({owner_expr}, {key_expr}, {boxed_default})"
            return f"dict_get_node({owner_expr}, {key_expr}, {default_expr})"
        if not objectish_owner:
            if default_expr in {"::std::nullopt", "std::nullopt"}:
                val_t = self.normalize_type_name(owner_value_t)
                if val_t not in {"", "None"}:
                    allows_nullopt = False
                    if val_t.startswith("optional[") and val_t.endswith("]"):
                        allows_nullopt = True
                    elif self._contains_text(val_t, "|"):
                        parts = self.split_union(val_t)
                        i = 0
                        while i < len(parts):
                            if self.normalize_type_name(parts[i]) == "None":
                                allows_nullopt = True
                                break
                            i += 1
                    if (not allows_nullopt) and (not self.is_any_like_type(val_t)):
                        default_expr = self._cpp_type_text(val_t) + "()"
            return f"{owner_expr}.get({key_expr}, {default_expr})"
        if owner_optional_object_dict:
            boxed_default = self._box_any_target_value(default_expr, default_node)
            return f"py_dict_get_default({owner_expr}, {key_expr}, {boxed_default})"
        return f"py_dict_get_default({owner_expr}, {key_expr}, {default_expr})"

    def _render_collection_constructor_call(
        self,
        raw: str,
        expr: dict[str, Any],
        args: list[str],
        first_arg: Any,
    ) -> str | None:
        """`set/list/dict` コンストラクタ呼び出しの型依存分岐を共通化する。"""
        if raw not in {"set", "list", "dict"}:
            return None
        t = self.cpp_type(expr.get("resolved_type"))
        if len(args) == 0:
            return f"{t}{{}}"
        if len(args) != 1:
            return None
        at0 = self.get_expr_type(first_arg)
        at = at0 if isinstance(at0, str) else ""
        head = f"{raw}["
        if at.startswith(head):
            return args[0]
        any_obj_t = "set<object>"
        starts = "set<"
        ctor_name = "set"
        if raw == "list":
            any_obj_t = "list<object>"
            starts = "list<"
            ctor_name = "list"
        if raw == "dict":
            any_obj_t = "dict<str, object>"
            starts = "dict<"
            ctor_name = "dict"
        if t == any_obj_t and at in {"Any", "object"}:
            return f"{t}({args[0]})"
        if t.startswith(starts):
            if t == any_obj_t and at not in {"Any", "object"}:
                return args[0]
            return f"{t}({args[0]})"
        return f"{ctor_name}({args[0]})"

    # type conversion / any-boundary helpers moved to hooks.cpp.emitter.type_bridge.CppTypeBridgeEmitter.

    def _build_name_expr_node(self, name: str, resolved_type: str = "unknown") -> dict[str, Any]:
        return {
            "kind": "Name",
            "id": name,
            "resolved_type": resolved_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": name,
        }

    def _build_constant_int_expr_node(self, value: int) -> dict[str, Any]:
        return {
            "kind": "Constant",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": str(value),
            "value": value,
        }

    def _build_py_at_expr_node(self, container_name: str, index: int) -> dict[str, Any]:
        return {
            "kind": "Call",
            "func": self._build_name_expr_node("py_at"),
            "args": [
                self._build_name_expr_node(container_name, "object"),
                self._build_constant_int_expr_node(index),
            ],
            "keywords": [],
            "resolved_type": "object",
            "borrow_kind": "value",
            "casts": [],
            "repr": f"py_at({container_name}, {index})",
        }

    def _render_type_id_operand_expr(self, type_id_node: Any) -> str:
        """type_id 式ノードを C++ の type_id 式へ写像する。"""
        node = self.any_to_dict_or_empty(type_id_node)
        if len(node) == 0:
            return ""
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            type_name = self.any_to_str(node.get("id")).strip()
            if type_name == "":
                return ""
            if type_name == "PYTRA_TID_NONE":
                return "PYTRA_TID_NONE"
            if type_name == "PYTRA_TID_BOOL":
                return "PYTRA_TID_BOOL"
            if type_name == "PYTRA_TID_INT":
                return "PYTRA_TID_INT"
            if type_name == "PYTRA_TID_FLOAT":
                return "PYTRA_TID_FLOAT"
            if type_name == "PYTRA_TID_STR":
                return "PYTRA_TID_STR"
            if type_name == "PYTRA_TID_LIST":
                return "PYTRA_TID_LIST"
            if type_name == "PYTRA_TID_DICT":
                return "PYTRA_TID_DICT"
            if type_name == "PYTRA_TID_SET":
                return "PYTRA_TID_SET"
            if type_name == "PYTRA_TID_OBJECT":
                return "PYTRA_TID_OBJECT"
            if type_name == "None":
                return "PYTRA_TID_NONE"
            if type_name == "bool":
                return "PYTRA_TID_BOOL"
            if type_name == "int":
                return "PYTRA_TID_INT"
            if type_name == "float":
                return "PYTRA_TID_FLOAT"
            if type_name == "str":
                return "PYTRA_TID_STR"
            if type_name == "list":
                return "PYTRA_TID_LIST"
            if type_name == "dict":
                return "PYTRA_TID_DICT"
            if type_name == "set":
                return "PYTRA_TID_SET"
            if type_name == "object":
                return "PYTRA_TID_OBJECT"
            if type_name in self.ref_classes:
                return f"{type_name}::PYTRA_TYPE_ID"
            if self.is_declared(type_name):
                return type_name
            return ""
        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(node.get("value"))
            owner_kind = self._node_kind_from_dict(owner_node)
            owner_name = self.any_to_str(owner_node.get("id")).strip()
            attr_name = self.any_to_str(node.get("attr")).strip()
            if owner_kind == "Name" and attr_name == "PYTRA_TYPE_ID" and owner_name in self.ref_classes:
                return f"{owner_name}::PYTRA_TYPE_ID"
        rendered = self.render_expr(type_id_node)
        if rendered == "/* none */":
            return ""
        return rendered

    def _const_false_expr_node(self) -> dict[str, Any]:
        return {
            "kind": "Constant",
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
            "repr": "False",
            "value": False,
        }

    def _boolop_or_expr_node(self, values: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "kind": "BoolOp",
            "op": "Or",
            "values": values,
            "resolved_type": "bool",
            "borrow_kind": "value",
            "casts": [],
        }

    def _type_id_name_call_kind(self, raw_name: str) -> str:
        raw = self._trim_ws(self.any_to_str(raw_name))
        if raw == "isinstance":
            return "legacy_isinstance"
        if raw == "issubclass":
            return "legacy_issubclass"
        if raw in {"py_isinstance", "py_tid_isinstance"}:
            return "runtime_isinstance"
        if raw in {"py_issubclass", "py_tid_issubclass"}:
            return "runtime_issubclass"
        if raw in {"py_is_subtype", "py_tid_is_subtype"}:
            return "runtime_is_subtype"
        if raw in {"py_runtime_type_id", "py_tid_runtime_type_id"}:
            return "runtime_type_id"
        return ""

    def _build_type_id_expr_from_call_name(
        self,
        raw_name: str,
        arg_nodes: list[Any],
    ) -> dict[str, Any] | None:
        kind = self._type_id_name_call_kind(raw_name)
        if kind == "runtime_isinstance":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsInstance",
                "value": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if kind == "runtime_issubclass":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsSubclass",
                "actual_type_id": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if kind == "runtime_is_subtype":
            if len(arg_nodes) != 2:
                return self._const_false_expr_node()
            return {
                "kind": "IsSubtype",
                "actual_type_id": arg_nodes[0],
                "expected_type_id": arg_nodes[1],
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if kind == "runtime_type_id":
            if len(arg_nodes) != 1:
                return None
            return {
                "kind": "ObjTypeId",
                "value": arg_nodes[0],
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
        return None

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp（三項演算）を式へ変換する。

        NOTE:
        C++ selfhost では、基底 CodeEmitter 側の同名メソッドをそのまま使うと
        `render_expr` が静的束縛で基底実装（空文字返却）へ落ちる。
        CppEmitter 側で明示オーバーライドして、IfExp の各部分式が
        `CppEmitter.render_expr` を通るようにする。
        """
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for c in casts:
            on = self.any_to_str(c.get("on"))
            to_t = self.any_to_str(c.get("to"))
            if on == "body":
                body = self.apply_cast(body, to_t)
            elif on == "orelse":
                orelse = self.apply_cast(orelse, to_t)
        test_node = self.any_to_dict_or_empty(expr.get("test"))
        body_node = self.any_to_dict_or_empty(expr.get("body"))
        orelse_node = self.any_to_dict_or_empty(expr.get("orelse"))
        if self._is_isinstance_ctor_ifexp_pattern(test_node, body_node, orelse_node):
            if not self.is_boxed_object_expr(orelse):
                orelse = f"make_object({orelse})"
        test_expr = self.render_expr(test_node)
        return self.render_ifexp_common(
            test_expr,
            body,
            orelse,
            test_node=test_node,
            fold_bool_literal=True,
        )

    def _is_isinstance_ctor_ifexp_pattern(
        self,
        test_node: dict[str, Any],
        body_node: dict[str, Any],
        orelse_node: dict[str, Any],
    ) -> bool:
        """`x if isinstance(x, T) else T(x)` 形を検出する。"""
        if self.any_dict_get_str(test_node, "kind", "") != "Call":
            return False
        fn_node = self.any_to_dict_or_empty(test_node.get("func"))
        if self.any_dict_get_str(fn_node, "kind", "") != "Name":
            return False
        if self.any_dict_get_str(fn_node, "id", "") != "isinstance":
            return False
        test_args = self.any_to_list(test_node.get("args"))
        if len(test_args) < 2:
            return False
        lhs = self.any_to_dict_or_empty(test_args[0])
        if self.any_dict_get_str(lhs, "kind", "") != "Name":
            return False
        lhs_name = self.any_dict_get_str(lhs, "id", "")
        if lhs_name == "":
            return False

        if self.any_dict_get_str(body_node, "kind", "") != "Name":
            return False
        if self.any_dict_get_str(body_node, "id", "") != lhs_name:
            return False

        if self.any_dict_get_str(orelse_node, "kind", "") != "Call":
            return False
        ctor_node = self.any_to_dict_or_empty(orelse_node.get("func"))
        if self.any_dict_get_str(ctor_node, "kind", "") != "Name":
            return False
        ctor_name = self.any_dict_get_str(ctor_node, "id", "")
        if ctor_name == "":
            return False
        orelse_args = self.any_to_list(orelse_node.get("args"))
        if len(orelse_args) < 1:
            return False
        first_arg = self.any_to_dict_or_empty(orelse_args[0])
        if self.any_dict_get_str(first_arg, "kind", "") != "Name":
            return False
        if self.any_dict_get_str(first_arg, "id", "") != lhs_name:
            return False
        return True

    def _render_operator_family_expr(
        self,
        kind: str,
        expr: Any,
        expr_d: dict[str, Any],
    ) -> str:
        """算術/比較/条件演算系ノードをまとめて描画する。"""
        if kind == "RangeExpr":
            start = self.render_expr(expr_d.get("start"))
            stop = self.render_expr(expr_d.get("stop"))
            step = self.render_expr(expr_d.get("step"))
            return f"py_range({start}, {stop}, {step})"
        if kind == "BinOp":
            return self._render_binop_expr(expr_d)
        if kind == "UnaryOp":
            return self._render_unary_expr(expr_d)
        if kind == "BoolOp":
            return self.render_boolop(expr, False)
        if kind == "Compare":
            return self._render_compare_expr(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        return ""

    def _render_unary_expr(self, expr: dict[str, Any]) -> str:
        """UnaryOp ノードを C++ 式へ変換する。"""
        operand_obj: object = expr.get("operand")
        operand_expr = self.any_to_dict_or_empty(operand_obj)
        operand = self.render_expr(operand_obj)
        op = self.any_to_str(expr.get("op"))
        if op == "Not":
            if len(operand_expr) > 0 and self._node_kind_from_dict(operand_expr) == "Compare":
                if self.any_dict_get_str(operand_expr, "lowered_kind", "") == "Contains":
                    container = self.render_expr(operand_expr.get("container"))
                    key = self.render_expr(operand_expr.get("key"))
                    ctype0 = self.get_expr_type(operand_expr.get("container"))
                    ctype = ctype0 if isinstance(ctype0, str) else ""
                    if ctype.startswith("dict["):
                        return f"{container}.find({key}) == {container}.end()"
                    return f"::std::find({container}.begin(), {container}.end(), {key}) == {container}.end()"
                ops = self.any_to_str_list(operand_expr.get("ops"))
                cmps = self._dict_stmt_list(operand_expr.get("comparators"))
                if len(ops) == 1 and len(cmps) == 1:
                    left = self.render_expr(operand_expr.get("left"))
                    rhs_node0: object = cmps[0]
                    rhs = self.render_expr(rhs_node0)
                    op0 = ops[0]
                    inv = {
                        "Eq": "!=",
                        "NotEq": "==",
                        "Lt": ">=",
                        "LtE": ">",
                        "Gt": "<=",
                        "GtE": "<",
                        "Is": "!=",
                        "IsNot": "==",
                    }
                    if op0 in inv:
                        return f"{left} {inv[op0]} {rhs}"
                    if op0 in {"In", "NotIn"}:
                        found = f"py_contains({rhs}, {left})"
                        return f"!({found})" if op0 == "In" else found
            return f"!({operand})"
        if op == "USub":
            operand_t0 = self.get_expr_type(operand_obj)
            operand_t = operand_t0 if isinstance(operand_t0, str) else ""
            operand_t_norm = self.normalize_type_name(operand_t)
            if operand_t_norm not in {"", "unknown", "Any", "object"} and self._has_class_method(operand_t, "__neg__"):
                owner = f"({operand})"
                if operand_t_norm in self.ref_classes and not operand.strip().startswith("*"):
                    return f"{owner}->__neg__()"
                return f"{owner}.__neg__()"
            return f"-{operand}"
        if op == "UAdd":
            return f"+{operand}"
        return operand

    def _render_compare_expr(self, expr: dict[str, Any]) -> str:
        """Compare ノードを C++ 式へ変換する。"""
        if self.any_dict_get_str(expr, "lowered_kind", "") == "Contains":
            container = self.render_expr(expr.get("container"))
            key = self.render_expr(expr.get("key"))
            base = f"py_contains({container}, {key})"
            if self.any_to_bool(expr.get("negated")):
                return f"!({base})"
            return base
        left = self.render_expr(expr.get("left"))
        ops = self.any_to_str_list(expr.get("ops"))
        if len(ops) == 0:
            return "true"
        cmps = self._dict_stmt_list(expr.get("comparators"))
        rhs_nodes: list[Any] = []
        rhs_texts: list[str] = []
        has_special_case = False
        cur_probe_node: object = expr.get("left")
        for i, op_name in enumerate(ops):
            rhs_node = cmps[i] if i < len(cmps) else {}
            rhs = self.render_expr(rhs_node)
            rhs_nodes.append(rhs_node)
            rhs_texts.append(rhs)
            if op_name in {"In", "NotIn", "Is", "IsNot"}:
                has_special_case = True
            cur_probe_node = rhs_node
        if not has_special_case:
            return self.render_compare_chain_from_rendered(
                left,
                ops,
                rhs_texts,
                CMP_OPS,
                empty_literal="true",
                wrap_terms=False,
                wrap_whole=False,
            )
        parts: list[str] = []
        cur = left
        cur_node: object = expr.get("left")
        for i, op in enumerate(ops):
            rhs_node: object = rhs_nodes[i] if i < len(rhs_nodes) else {}
            rhs = rhs_texts[i] if i < len(rhs_texts) else ""
            op_name: str = op
            cop = "=="
            cop_txt = str(CMP_OPS.get(op_name, ""))
            if cop_txt != "":
                cop = cop_txt
            if cop == "/* in */":
                parts.append(f"py_contains({rhs}, {cur})")
            elif cop == "/* not in */":
                parts.append(f"!py_contains({rhs}, {cur})")
            else:
                if op_name in {"Is", "IsNot"} and rhs in {"std::nullopt", "::std::nullopt"}:
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({cur})")
                elif op_name in {"Is", "IsNot"} and cur in {"std::nullopt", "::std::nullopt"}:
                    prefix = "!" if op_name == "IsNot" else ""
                    parts.append(f"{prefix}py_is_none({rhs})")
                else:
                    parts.append(f"{cur} {cop} {rhs}")
            cur = rhs
            cur_node = rhs_node
        return join_str_list(" && ", parts) if len(parts) > 0 else "true"

    def _box_expr_for_any(self, expr_txt: str, source_node: Any) -> str:
        """Any/object 向けの boxing を必要時のみ適用する。"""
        if self.is_boxed_object_expr(expr_txt):
            return expr_txt
        src_t = self.get_expr_type(source_node)
        # `source_node` の型が unknown でも、描画済みテキストが既知変数なら
        # 宣言型ヒントから再判定して過剰 boxing を避ける。
        src_t = self.infer_rendered_arg_type(expr_txt, src_t, self.declared_var_types)
        if self.is_any_like_type(src_t):
            return expr_txt
        return f"make_object({expr_txt})"

    def _box_any_target_value(self, expr_txt: str, source_node: Any) -> str:
        """Any/object ターゲット代入用に値を boxing する（None は object{}）。"""
        if expr_txt == "":
            return expr_txt
        if expr_txt in {"object{}", "object()"}:
            return expr_txt
        source_d = self.any_to_dict_or_empty(source_node)
        if self._node_kind_from_dict(source_d) == "Constant" and source_d.get("value") is None:
            return "object{}"
        if self.is_boxed_object_expr(expr_txt):
            return expr_txt
        if len(source_d) > 0:
            boxed_expr = self.render_expr(self._build_box_expr_node(source_node))
            # 既存挙動互換: source が Any/object の場合も代入先 Any では明示 boxing を維持する。
            if boxed_expr == expr_txt and not self.is_boxed_object_expr(expr_txt):
                return f"make_object({expr_txt})"
            return boxed_expr
        return f"make_object({expr_txt})"

    # repr-string fallback helpers removed; keep EAST3 structured-node path only.

    def _render_subscript_expr(self, expr: dict[str, Any]) -> str:
        """Subscript/Slice 式を C++ 式へ変換する。"""
        val = self.render_expr(expr.get("value"))
        val_ty0 = self.get_expr_type(expr.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        if self.any_dict_get_str(expr, "lowered_kind", "") == "SliceExpr":
            lo = self.render_expr(expr.get("lower")) if expr.get("lower") is not None else "0"
            up = self.render_expr(expr.get("upper")) if expr.get("upper") is not None else f"py_len({val})"
            return f"py_slice({val}, {lo}, {up})"
        sl: object = expr.get("slice")
        sl_node = self.any_to_dict_or_empty(sl)
        if len(sl_node) > 0 and self._node_kind_from_dict(sl_node) == "Slice":
            lo = self.render_expr(sl_node.get("lower")) if sl_node.get("lower") is not None else "0"
            up = self.render_expr(sl_node.get("upper")) if sl_node.get("upper") is not None else f"py_len({val})"
            return f"py_slice({val}, {lo}, {up})"
        idx = self.render_expr(sl)
        idx_ty0 = self.get_expr_type(sl)
        idx_ty = idx_ty0 if isinstance(idx_ty0, str) else ""
        idx_node = self.any_to_dict_or_empty(sl)
        idx_is_str_key = idx_ty == "str" or (
            self._node_kind_from_dict(idx_node) == "Constant" and isinstance(idx_node.get("value"), str)
        )
        idx_const = self._const_int_literal(sl)
        idx_is_int = idx_const is not None or idx_ty in {
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
        }
        if val_ty.startswith("dict["):
            idx = self._coerce_dict_key_expr(expr.get("value"), idx, sl)
            return f"py_dict_get({val}, {idx})"
        if val_ty in {"", "unknown"} or self.is_any_like_type(val_ty):
            if idx_is_str_key:
                return f"py_dict_get({val}, {idx})"
            return f"py_at({val}, py_to<int64>({idx}))"
        if val_ty.startswith("tuple[") and val_ty.endswith("]"):
            parts = self.split_generic(val_ty[6:-1])
            if idx_const is None:
                return f"py_at({val}, py_to<int64>({idx}))"
            n_parts = len(parts)
            idx_norm = int(idx_const)
            if idx_norm < 0:
                idx_norm += n_parts
            if idx_norm < 0 or idx_norm >= n_parts:
                raise RuntimeError("tuple index out of range in EAST -> C++ lowering")
            return f"::std::get<{idx_norm}>({val})"
        if self.is_indexable_sequence_type(val_ty):
            idx_t0 = self.get_expr_type(sl)
            idx_t = idx_t0 if isinstance(idx_t0, str) else ""
            if self.is_any_like_type(idx_t):
                idx = f"py_to<int64>({idx})"
            return self._render_sequence_index(val, idx, sl)
        return f"{val}[{idx}]"

    def _render_name_expr(self, expr_d: dict[str, Any]) -> str:
        """Name ノードを C++ 式へ変換する。"""
        return self.render_name_expr_common(
            expr_d,
            self.reserved_words,
            self.rename_prefix,
            self.renamed_symbols,
            "_",
            rewrite_self=self.current_class_name is not None,
            self_is_declared=self.is_declared("self"),
            self_rendered="*this",
        )

    def _render_constant_expr(self, expr: Any, expr_d: dict[str, Any]) -> str:
        """Constant ノードを C++ リテラル式へ変換する。"""
        return self.render_constant_expr_common(
            expr,
            expr_d,
            none_non_any_literal="::std::nullopt",
            none_any_literal="object{}",
            bytes_ctor_name="bytes",
            bytes_lit_fn_name="py_bytes_lit",
        )

    def _render_attribute_expr(self, expr_d: dict[str, Any]) -> str:
        """Attribute ノードを C++ 式へ変換する。

        NOTE:
        `CodeEmitter.render_attribute_expr_common` は内部で `render_expr(...)` を呼ぶ。
        selfhost 生成 C++ では基底メソッド内呼び出しが静的束縛されるため、
        基底 `render_expr`（空文字）へ落ちて `.<attr>` 化する。
        CppEmitter 側で実装して `CppEmitter.render_expr` 経路を維持する。
        """
        owner_t = self.get_expr_type(expr_d.get("value"))
        if self.is_forbidden_object_receiver_type(owner_t):
            attr = self.attr_name(expr_d)
            owner_cls = self.class_field_owner_unique.get(attr, "")
            owner_m_cls = self.class_method_owner_unique.get(attr, "")
            if (
                owner_cls in self.ref_classes
                or owner_m_cls in self.ref_classes
            ):
                pass
            else:
                raise RuntimeError(
                    "object receiver method call / attribute access is forbidden by language constraints"
                )
        base_rendered = self.render_expr(expr_d.get("value"))
        base_ctx = self.resolve_attribute_owner_context(expr_d.get("value"), base_rendered)
        base = self.any_dict_get_str(base_ctx, "expr", "")
        base_node = self.any_to_dict_or_empty(base_ctx.get("node"))
        base_kind = self._node_kind_from_dict(base_node)
        attr = self.attr_name(expr_d)
        direct_self_or_class = self.render_attribute_self_or_class_access(
            base,
            attr,
            self.current_class_name,
            self.current_class_static_fields,
            self.class_base,
            self.class_method_names,
        )
        if direct_self_or_class != "":
            return direct_self_or_class
        base_module_name = self.any_dict_get_str(base_ctx, "module", "")
        if base_module_name != "":
            mapped = self._lookup_module_attr_runtime_call(base_module_name, attr)
            ns = self._module_name_to_cpp_namespace(base_module_name)
            direct_module = self.render_attribute_module_access(
                base_module_name,
                attr,
                mapped,
                ns,
            )
            if direct_module != "":
                return direct_module
        if base_kind == "Name":
            base_name = dict_any_get_str(base_node, "id")
            if (
                base_name != ""
                and not self.is_declared(base_name)
                and base_name not in self.import_modules
                and base_name in self.import_symbol_modules
            ):
                raise self._make_missing_symbol_import_error(base_name, attr)
        bt = self.get_expr_type(expr_d.get("value"))
        if bt == "Path" and attr in {"name", "stem", "parent"}:
            return f"{base}.{attr}()"
        if (
            self.current_class_name is not None
            and attr in self.current_class_fields
            and (bt in {"", "unknown"} or self.is_any_like_type(bt))
        ):
            ctx = f"{self.current_class_name}.{attr}"
            base_obj = base
            if not self.is_boxed_object_expr(base_obj):
                base_obj = f"make_object({base_obj})"
            return f"obj_to_rc_or_raise<{self.current_class_name}>({base_obj}, \"{ctx}\")->{attr}"
        if bt in {"", "unknown"} or self.is_any_like_type(bt):
            owner_cls = self.class_field_owner_unique.get(attr, "")
            if owner_cls != "" and owner_cls in self.ref_classes:
                ctx = f"{owner_cls}.{attr}"
                base_obj = base
                if not self.is_boxed_object_expr(base_obj):
                    base_obj = f"make_object({base_obj})"
                return f"obj_to_rc_or_raise<{owner_cls}>({base_obj}, \"{ctx}\")->{attr}"
            owner_m_cls = self.class_method_owner_unique.get(attr, "")
            if owner_m_cls != "" and owner_m_cls in self.ref_classes:
                ctx = f"{owner_m_cls}.{attr}"
                base_obj = base
                if not self.is_boxed_object_expr(base_obj):
                    base_obj = f"make_object({base_obj})"
                return f"obj_to_rc_or_raise<{owner_m_cls}>({base_obj}, \"{ctx}\")->{attr}"
        if bt in self.ref_classes:
            return f"{base}->{attr}"
        return f"{base}.{attr}"

    def _render_joinedstr_expr(self, expr_d: dict[str, Any]) -> str:
        """JoinedStr（f-string）ノードを C++ の文字列連結式へ変換する。"""
        if self.any_dict_get_str(expr_d, "lowered_kind", "") == "Concat":
            parts: list[str] = []
            for p in self._dict_stmt_list(expr_d.get("concat_parts")):
                if self._node_kind_from_dict(p) == "literal":
                    parts.append(cpp_string_lit(self.any_dict_get_str(p, "value", "")))
                elif self._node_kind_from_dict(p) == "expr":
                    val: object = p.get("value")
                    if val is None:
                        parts.append('""')
                    else:
                        vtxt = self.render_expr(val)
                        vty = self.get_expr_type(val)
                        if vty == "str":
                            parts.append(vtxt)
                        else:
                            parts.append(self.render_to_string(val))
            if len(parts) == 0:
                return '""'
            return join_str_list(" + ", parts)
        parts: list[str] = []
        for p in self._dict_stmt_list(expr_d.get("values")):
            pk = self._node_kind_from_dict(p)
            if pk == "Constant":
                parts.append(cpp_string_lit(self.any_dict_get_str(p, "value", "")))
            elif pk == "FormattedValue":
                v: object = p.get("value")
                vtxt = self.render_expr(v)
                vty = self.get_expr_type(v)
                if vty == "str":
                    parts.append(vtxt)
                else:
                    parts.append(self.render_to_string(v))
        if len(parts) == 0:
            return '""'
        return join_str_list(" + ", parts)

    def _render_lambda_expr(self, expr_d: dict[str, Any]) -> str:
        """Lambda ノードを C++ のラムダ式へ変換する。"""
        arg_texts: list[str] = []
        for a in self._dict_stmt_list(expr_d.get("args")):
            nm = self.any_to_str(a.get("arg")).strip()
            if nm != "":
                default_node = a.get("default")
                param_t = "auto"
                ann_t = self.any_to_str(a.get("resolved_type")).strip()
                if isinstance(default_node, dict):
                    default_t = self.get_expr_type(default_node)
                    if default_t in {"", "unknown"}:
                        default_t = ann_t
                    if default_t not in {"", "unknown", "Any", "object"}:
                        param_t = self._cpp_type_text(default_t)
                elif ann_t not in {"", "unknown", "Any", "object"}:
                    param_t = self._cpp_type_text(ann_t)
                arg_txt = f"{param_t} {nm}"
                if isinstance(default_node, dict):
                    arg_txt += f" = {self.render_expr(default_node)}"
                arg_texts.append(arg_txt)
        body_expr = self.render_expr(expr_d.get("body"))
        return f"[&]({join_str_list(', ', arg_texts)}) {{ return {body_expr}; }}"

    def _render_expr_dispatch_table(self) -> dict[str, Any]:
        """`render_expr` の kind->handler テーブル骨格を返す。"""
        return {
            "Name": self._render_expr_kind_name,
            "Constant": self._render_expr_kind_constant,
            "Attribute": self._render_expr_kind_attribute,
            "Call": self._render_expr_kind_call,
            "Box": self._render_expr_kind_box,
            "Unbox": self._render_expr_kind_unbox,
            "CastOrRaise": self._render_expr_kind_cast_or_raise,
            "ObjBool": self._render_expr_kind_obj_bool,
            "ObjLen": self._render_expr_kind_obj_len,
            "ObjStr": self._render_expr_kind_obj_str,
            "ObjIterInit": self._render_expr_kind_obj_iter_init,
            "ObjIterNext": self._render_expr_kind_obj_iter_next,
            "ObjTypeId": self._render_expr_kind_obj_type_id,
            "Subscript": self._render_expr_kind_subscript,
            "JoinedStr": self._render_expr_kind_joinedstr,
            "Lambda": self._render_expr_kind_lambda,
            "List": self._render_expr_kind_list,
            "Tuple": self._render_expr_kind_tuple,
            "Set": self._render_expr_kind_set,
            "Dict": self._render_expr_kind_dict,
            "ListComp": self._render_expr_kind_list_comp,
            "SetComp": self._render_expr_kind_set_comp,
            "DictComp": self._render_expr_kind_dict_comp,
            "PathRuntimeOp": self._render_expr_kind_path_runtime_op,
            "RuntimeSpecialOp": self._render_expr_kind_runtime_special_op,
            "IsSubtype": self._render_expr_kind_is_subtype,
            "IsSubclass": self._render_expr_kind_is_subclass,
            "IsInstance": self._render_expr_kind_is_instance,
        }

    def _render_expr_kind_name(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        return self._render_name_expr(expr_d)

    def _render_expr_kind_constant(self, expr: Any, expr_d: dict[str, Any]) -> str:
        return self._render_constant_expr(expr, expr_d)

    def _render_expr_kind_attribute(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        return self._render_attribute_expr(expr_d)

    def _render_expr_kind_call(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        call_ctx = self.prepare_call_context(expr_d)
        fn = self.any_to_dict_or_empty(call_ctx.get("fn"))
        fn_name = self.any_to_str(call_ctx.get("fn_name"))
        arg_nodes = self.any_to_list(call_ctx.get("arg_nodes"))
        args = self.any_to_str_list(call_ctx.get("args"))
        kw = self.any_to_str_dict_or_empty(call_ctx.get("kw"))
        kw_values = self.any_to_str_list(call_ctx.get("kw_values"))
        kw_nodes = self.any_to_list(call_ctx.get("kw_nodes"))
        first_arg: object = call_ctx.get("first_arg")
        return self._render_call_expr_from_context(
            expr_d,
            fn,
            fn_name,
            args,
            kw,
            arg_nodes,
            kw_values,
            kw_nodes,
            first_arg,
        )

    def _render_expr_kind_box(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        expr_dict = self.any_to_dict_or_empty(expr)
        value_node = expr_dict.get("value")
        value_expr = self.render_expr(value_node)
        return self._box_expr_for_any(value_expr, value_node)

    def _render_expr_kind_unbox(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
        if target_t == "" or target_t == "unknown":
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
        if target_t == "" or target_t == "unknown" or self.is_any_like_type(target_t):
            return value_expr
        ctx = self.any_dict_get_str(expr_d, "ctx", "east3_unbox")
        return self._render_unbox_target_cast(value_expr, target_t, ctx)

    def _render_expr_kind_cast_or_raise(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
        if target_t == "" or target_t == "unknown":
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
        if target_t == "" or target_t == "unknown":
            return value_expr
        if self.is_any_like_type(target_t):
            return self._box_expr_for_any(value_expr, expr_d.get("value"))
        return self._render_unbox_target_cast(value_expr, target_t, "east3_cast_or_raise")

    def _render_expr_kind_obj_bool(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_to<bool>({value_expr})"

    def _render_expr_kind_obj_len(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_len({value_expr})"

    def _render_expr_kind_obj_str(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_to_string({value_expr})"

    def _render_expr_kind_obj_iter_init(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_iter_or_raise({value_expr})"

    def _render_expr_kind_obj_iter_next(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        iter_expr = self.render_expr(expr_d.get("iter"))
        return f"py_next_or_stop({iter_expr})"

    def _render_expr_kind_obj_type_id(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_runtime_type_id({value_expr})"

    def _render_expr_kind_subscript(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr_d
        return self._render_subscript_expr(expr)

    def _render_expr_kind_joinedstr(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        return self._render_joinedstr_expr(expr_d)

    def _render_expr_kind_lambda(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        return self._render_lambda_expr(expr_d)

    def render_cond(self, expr: Any) -> str:
        """条件式文脈向けに Any/object を `py_to_bool` 判定へ寄せる。"""
        expr_node = self.any_to_dict_or_empty(expr)
        if len(expr_node) == 0:
            return "false"
        expr_t = self.normalize_type_name(self.get_expr_type(expr))
        if not self.is_any_like_type(expr_t):
            return super().render_cond(expr)
        body_raw = self.render_expr(expr)
        body = self._strip_outer_parens(body_raw)
        if body == "":
            return "false"
        return f"py_to<bool>({body})"

    def render_expr(self, expr: Any) -> str:
        """式ノードを C++ の式文字列へ変換する中核処理。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "/* none */"
        kind = self._node_kind_from_dict(expr_d)
        hook_kind = self.hook_on_render_expr_kind(kind, expr_d)
        if hook_kind != "":
            return hook_kind

        dispatch_handler = self._render_expr_dispatch_table().get(kind)
        if dispatch_handler is not None:
            return dispatch_handler(expr, expr_d)
        if kind == "ListAppend":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            owner_t0 = self.get_expr_type(owner_node)
            owner_t = owner_t0 if isinstance(owner_t0, str) else ""
            owner_types: list[str] = [owner_t]
            if self._contains_text(owner_t, "|"):
                owner_types = self.split_union(owner_t)
            append_rendered = self._render_append_call_object_method(owner_types, owner_expr, [value_expr], [value_node])
            if append_rendered is not None:
                return str(append_rendered)
            return f"{owner_expr}.append({value_expr})"
        if kind == "ListExtend":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.insert({owner_expr}.end(), {value_expr}.begin(), {value_expr}.end())"
        if kind == "SetAdd":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.insert({value_expr})"
        if kind == "ListPop":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            has_index = self.any_dict_has(expr_d, "index")
            if not has_index:
                return f"{owner_expr}.pop()"
            index_node = expr_d.get("index")
            index_expr = self.render_expr(index_node)
            if index_expr in {"", "/* none */"}:
                return f"{owner_expr}.pop()"
            return f"{owner_expr}.pop({index_expr})"
        if kind == "ListClear":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"{owner_expr}.clear()"
        if kind == "ListReverse":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"::std::reverse({owner_expr}.begin(), {owner_expr}.end())"
        if kind == "ListSort":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"::std::sort({owner_expr}.begin(), {owner_expr}.end())"
        if kind == "SetErase":
            owner_node = expr_d.get("owner")
            value_node = expr_d.get("value")
            owner_expr = self.render_expr(owner_node)
            value_expr = self.render_expr(value_node)
            return f"{owner_expr}.erase({value_expr})"
        if kind == "SetClear":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"{owner_expr}.clear()"
        if kind == "DictItems":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return owner_expr
        if kind == "DictKeys":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"py_dict_keys({owner_expr})"
        if kind == "DictValues":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            return f"py_dict_values({owner_expr})"
        if kind == "DictPop":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            return f"{owner_expr}.pop({key_expr})"
        if kind == "DictGetMaybe":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            return f"py_dict_get_maybe({owner_expr}, {key_expr})"
        if kind == "DictPopDefault":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            default_node = expr_d.get("default")
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(key_node)
            key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
            default_expr = self.render_expr(default_node)
            val_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "value_type", "Any"))
            if default_expr in {"::std::nullopt", "std::nullopt"} and not self.is_any_like_type(val_t) and val_t != "None":
                default_expr = self._cpp_type_text(val_t) + "()"
            return f"({owner_expr}.contains({key_expr}) ? {owner_expr}.pop({key_expr}) : {default_expr})"
        if kind == "DictGetDefault":
            owner_node = expr_d.get("owner")
            key_node = expr_d.get("key")
            default_node = expr_d.get("default")
            out_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "out_type", ""))
            default_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "default_type", ""))
            owner_value_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "owner_value_type", ""))
            objectish_owner = self.any_to_bool(expr_d.get("objectish_owner"))
            owner_optional_object_dict = self.any_to_bool(expr_d.get("owner_optional_object_dict"))
            return self._render_dict_get_default_expr(
                owner_node,
                key_node,
                default_node,
                out_t,
                default_t,
                owner_value_t,
                objectish_owner,
                owner_optional_object_dict,
            )
        if kind == "StrStripOp":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            mode = self.any_dict_get_str(expr_d, "mode", "strip")
            has_chars = self.any_dict_has(expr_d, "chars")
            if has_chars:
                chars_expr = self.render_expr(expr_d.get("chars"))
                if mode == "rstrip":
                    return f"{owner_expr}.rstrip({chars_expr})"
                if mode == "lstrip":
                    return f"{owner_expr}.lstrip({chars_expr})"
                return f"{owner_expr}.strip({chars_expr})"
            if mode == "rstrip":
                return f"py_rstrip({owner_expr})"
            if mode == "lstrip":
                return f"py_lstrip({owner_expr})"
            return f"py_strip({owner_expr})"
        if kind == "StrStartsEndsWith":
            owner_node = expr_d.get("owner")
            needle_node = expr_d.get("needle")
            owner_expr = self.render_expr(owner_node)
            needle_expr = self.render_expr(needle_node)
            mode = self.any_dict_get_str(expr_d, "mode", "startswith")
            has_start = self.any_dict_has(expr_d, "start")
            fn_name = "py_startswith" if mode != "endswith" else "py_endswith"
            if not has_start:
                return f"{fn_name}({owner_expr}, {needle_expr})"
            start_expr = self.render_expr(expr_d.get("start"))
            start_cast = f"py_to<int64>({start_expr})"
            end_expr = f"py_len({owner_expr})"
            if self.any_dict_has(expr_d, "end"):
                end_raw = self.render_expr(expr_d.get("end"))
                end_expr = f"py_to<int64>({end_raw})"
            sliced = f"py_slice({owner_expr}, {start_cast}, {end_expr})"
            return f"{fn_name}({sliced}, {needle_expr})"
        if kind == "StrFindOp":
            owner_expr = self.render_expr(expr_d.get("owner"))
            needle_expr = self.render_expr(expr_d.get("needle"))
            mode = self.any_dict_get_str(expr_d, "mode", "find")
            fn_name = "py_rfind" if mode == "rfind" else "py_find"
            args: list[str] = [owner_expr, needle_expr]
            if self.any_dict_has(expr_d, "start"):
                args.append(self.render_expr(expr_d.get("start")))
            if self.any_dict_has(expr_d, "end"):
                args.append(self.render_expr(expr_d.get("end")))
            return f"{fn_name}({join_str_list(', ', args)})"
        if kind == "StrCharClassOp":
            value_node = expr_d.get("value")
            value_expr = self.render_expr(value_node)
            mode = self.any_dict_get_str(expr_d, "mode", "isdigit")
            if mode == "isalpha":
                return f"{value_expr}.isalpha()"
            return f"{value_expr}.isdigit()"
        if kind == "StrReplace":
            owner_expr = self.render_expr(expr_d.get("owner"))
            old_expr = self.render_expr(expr_d.get("old"))
            new_expr = self.render_expr(expr_d.get("new"))
            return f"py_replace({owner_expr}, {old_expr}, {new_expr})"
        if kind == "StrJoin":
            owner_expr = self.render_expr(expr_d.get("owner"))
            items_expr = self.render_expr(expr_d.get("items"))
            return f"str({owner_expr}).join({items_expr})"
        # runtime/path/type_id handlers moved to hooks.cpp.emitter.runtime_expr.CppRuntimeExprEmitter.
        op_rendered = self._render_operator_family_expr(kind, expr, expr_d)
        if op_rendered != "":
            return op_rendered
        # collection literal/comprehension handlers moved to hooks.cpp.emitter.collection_expr.CppCollectionExprEmitter.
        return f"/* unsupported expr: {kind} */"

    def emit_bridge_comment(self, expr: dict[str, Any] | None) -> None:
        """ランタイムブリッジ呼び出しの補助コメントを必要時に付与する。"""
        _ = expr
        return

    # type conversion / any-boundary helpers moved to hooks.cpp.emitter.type_bridge.CppTypeBridgeEmitter.


_attach_cpp_emitter_helper_methods(CppEmitter)

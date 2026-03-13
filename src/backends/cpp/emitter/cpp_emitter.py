from __future__ import annotations

from pytra.std import json
from pytra.std import os
from typing import Any
from pytra.std.pathlib import Path

from backends.common.emitter.code_emitter import CodeEmitter
from toolchain.compiler.transpile_cli import (
    dict_any_get_dict,
    dict_any_get_str,
    join_str_list,
    set_import_module_binding,
    set_import_symbol_binding_and_module_set,
)
from backends.cpp.emitter.analysis import CppAnalysisEmitter
from backends.cpp.emitter.builtin_runtime import CppBuiltinRuntimeEmitter
from backends.cpp.emitter.call import CppCallEmitter
from backends.cpp.emitter.class_def import CppClassEmitter
from backends.cpp.emitter.collection_expr import CppCollectionExprEmitter
from backends.cpp.emitter.module import CppModuleEmitter
from backends.cpp.emitter.operator import CppBinaryOperatorEmitter
from backends.cpp.emitter.runtime_expr import CppRuntimeExprEmitter
from backends.cpp.emitter.expr import CppExpressionEmitter
from backends.cpp.emitter.stmt import CppStatementEmitter
from backends.cpp.emitter.type_bridge import CppTypeBridgeEmitter
from backends.cpp.emitter.tmp import CppTemporaryEmitter
from backends.cpp.emitter.trivia import CppTriviaEmitter
from backends.cpp.emitter.profile_loader import (
    CMP_OPS,
    load_cpp_hooks,
    load_cpp_identifier_rules,
    load_cpp_module_attr_call_map,
    load_cpp_profile,
    load_cpp_type_map,
)
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id
from backends.cpp.lower import lower_cpp_from_east3
from backends.cpp.optimizer import optimize_cpp_ir_module
from backends.cpp.optimizer import render_cpp_opt_trace


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
    cpp_list_model: str = "",
) -> str:
    """Emit C++ text from EAST module via CppEmitter (public bridge)."""
    cpp_ir = east_module
    if isinstance(east_module, dict):
        lower_debug_flags: dict[str, object] = {
            "negative_index_mode": negative_index_mode,
            "bounds_check_mode": bounds_check_mode,
            "floor_div_mode": floor_div_mode,
            "mod_mode": mod_mode,
            "int_width": int_width,
            "str_index_mode": str_index_mode,
            "str_slice_mode": str_slice_mode,
            "opt_level": opt_level,
            "cpp_list_model": cpp_list_model,
        }
        lowered_ir, lower_report = lower_cpp_from_east3(
            east_module,
            debug_flags=lower_debug_flags,
        )
        cpp_ir = lowered_ir
        if dump_cpp_ir_before_opt != "":
            _dump_json_file(dump_cpp_ir_before_opt, cpp_ir)
        optimized_ir, report = optimize_cpp_ir_module(
            cpp_ir,
            opt_level=cpp_opt_level,
            opt_pass_spec=cpp_opt_pass,
            debug_flags=lower_debug_flags,
        )
        cpp_ir = optimized_ir
        if dump_cpp_ir_after_opt != "":
            _dump_json_file(dump_cpp_ir_after_opt, cpp_ir)
        if dump_cpp_opt_trace != "":
            trace_text = (
                "cpp_lower_trace:\n"
                + "- mode="
                + str(lower_report.get("mode", "unknown"))
                + " changed="
                + str(lower_report.get("changed", False)).lower()
                + " change_count="
                + str(lower_report.get("change_count", 0))
                + "\n"
                + render_cpp_opt_trace(report)
            )
            _write_text_file(dump_cpp_opt_trace, trace_text)
    emitter = CppEmitter(
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
    )
    if cpp_list_model in {"value", "pyobj"}:
        emitter.cpp_list_model = cpp_list_model
    return emitter.transpile()


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
        self.cpp_list_model = "value"
        profile_cpp_any = self.profile.get("cpp") if isinstance(self.profile, dict) else {}
        if isinstance(profile_cpp_any, dict):
            list_model_any = profile_cpp_any.get("list_model")
            if isinstance(list_model_any, str) and list_model_any in {"value", "pyobj"}:
                self.cpp_list_model = list_model_any
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
        self.class_method_arg_defaults: dict[str, dict[str, dict[str, Any]]] = {}
        self.class_method_return_types: dict[str, dict[str, str]] = {}
        self.class_property_names: dict[str, set[str]] = {}
        self.class_base: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_storage_hints: dict[str, str] = {}
        self.ref_classes: set[str] = set()
        self.value_classes: set[str] = set()
        self.class_field_types: dict[str, dict[str, str]] = {}
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
        self.function_arg_abi_modes: dict[str, list[str]] = {}
        self.function_vararg_list_types: dict[str, str] = {}
        self.function_mutated_param_positions: dict[str, set[int]] = {}
        self.function_return_types: dict[str, str] = {}
        self.function_return_abi_modes: dict[str, str] = {}
        self.extern_function_names: set[str] = set()
        self.current_function_return_type: str = ""
        self.current_function_return_abi_mode: str = "default"
        self.current_function_is_generator: bool = False
        self.current_function_yield_buffer: str = ""
        self.enable_helper_artifact_lane = False
        self.current_function_yield_type: str = "unknown"
        self.current_function_symbol: str = ""
        self.current_function_non_escape_summary: dict[str, Any] = {}
        self.current_function_stack_list_locals: set[str] = set()
        self.current_function_pyobj_runtime_list_alias_names: set[str] = set()
        self.current_function_value_list_params: set[str] = set()
        self.current_function_value_list_locals: set[str] = set()
        self.current_function_typed_list_str_params: set[str] = set()
        self.current_function_typed_list_str_locals: set[str] = set()
        self.current_function_reassigned_names: set[str] = set()
        self.declared_var_types: dict[str, str] = {}
        self.module_global_var_types: dict[str, str] = {}
        self._module_fn_arg_type_cache: dict[str, dict[str, list[str]]] = {}
        self._module_fn_signature_cache: dict[str, dict[str, dict[str, list[str]]]] = {}
        self._module_fn_return_type_cache: dict[str, dict[str, str]] = {}
        self._module_fn_cpp_signature_cache: dict[str, dict[str, dict[str, Any]]] = {}
        self._module_class_signature_cache: dict[str, dict[str, dict[str, Any]]] = {}
        self.non_escape_summary_map: dict[str, dict[str, Any]] = {}
        self.function_non_escape_summary_map: dict[str, dict[str, Any]] = {}
        self.function_stack_list_locals_map: dict[str, list[str]] = {}
        self.function_pyobj_runtime_list_alias_map: dict[str, list[str]] = {}
        self.non_escape_callsite_records: list[dict[str, Any]] = []

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

    def _expand_runtime_class_candidates(self, owner_t: str) -> list[str]:
        """owner 型名から class/ref 判定に使う候補型列を返す。"""
        t_norm = self.normalize_type_name(owner_t)
        base_candidates: list[str] = []
        if self._contains_text(t_norm, "|"):
            base_candidates = self.split_union(t_norm)
        elif t_norm != "":
            base_candidates = [t_norm]
        out: list[str] = []
        for base in base_candidates:
            if base == "":
                continue
            stripped = self._strip_rc_wrapper(base)
            if base not in out:
                out.append(base)
            if stripped != "" and stripped not in out:
                out.append(stripped)
            mapped = self.normalize_type_name(self.any_to_str(self.type_map.get(base)))
            if mapped != "":
                if mapped not in out:
                    out.append(mapped)
                mapped_stripped = self._strip_rc_wrapper(mapped)
                if mapped_stripped != "" and mapped_stripped not in out:
                    out.append(mapped_stripped)
        return out

    def _type_is_ref_class(self, owner_t: str) -> bool:
        """owner_t が ref class として扱うべき型か返す。"""
        for candidate in self._expand_runtime_class_candidates(owner_t):
            if candidate in self.ref_classes:
                return True
        return False

    def _is_cpp_class_borrow_param_type(self, raw_t: str, cpp_t: str) -> bool:
        """関数シグネチャで non-const borrow に寄せるべき user/runtime class 型か判定する。"""
        t_norm = self.normalize_type_name(raw_t)
        if t_norm in {"", "unknown"} or self.is_any_like_type(t_norm):
            return False
        for prefix in ("list[", "dict[", "set[", "tuple[", "deque[", "::std::optional<"):
            if t_norm.startswith(prefix):
                return False
        if t_norm in {"str", "bytes", "bytearray"}:
            return False
        imported_cpp = self.normalize_type_name(self._resolve_imported_symbol_class_cpp_type(t_norm))
        if imported_cpp != "":
            return True
        cpp_t_norm = self.normalize_type_name(cpp_t)
        if cpp_t_norm.startswith("rc<"):
            return False
        cpp_norm = self._strip_rc_wrapper(cpp_t_norm)
        if cpp_norm in self.ref_classes:
            return False
        if cpp_norm in self.class_names or cpp_norm in self.value_classes:
            return True
        return False

    def _is_current_function_cpp_class_borrow_name(self, expr_node: dict[str, Any]) -> bool:
        """現在関数で borrow 署名に落とした class param 名か判定する。"""
        if self._node_kind_from_dict(expr_node) != "Name":
            return False
        name = dict_any_get_str(expr_node, "id")
        if name == "":
            return False
        borrow_names = getattr(self, "current_function_cpp_class_borrow_params", set())
        return isinstance(borrow_names, set) and name in borrow_names

    def _use_ref_class_member_arrow(self, expr_node: dict[str, Any], base_expr: str, owner_t: str) -> bool:
        """ref class member access を `->` にするか判定する。"""
        if not self._type_is_ref_class(owner_t):
            return False
        if self._is_current_function_cpp_class_borrow_name(expr_node):
            return False
        return not self._trim_ws(base_expr).startswith("*")

    def _class_has_property_getter(self, owner_t: str, attr: str) -> bool:
        """owner_t かその base に property getter が定義されているか返す。"""
        seen: set[str] = set()
        for candidate in self._expand_runtime_class_candidates(owner_t):
            cur = candidate
            while cur != "" and cur not in seen:
                seen.add(cur)
                if attr in self.class_property_names.get(cur, set()):
                    return True
                cur = self.class_base.get(cur, "")
        return False

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

    def is_locally_declared(self, name: str) -> bool:
        """Module import binding を除いた local shadow 判定。"""
        if name == "":
            return False
        scope_len = len(self.scope_stack)
        if scope_len <= 1:
            return False
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
            if nm in self.module_global_var_types:
                global_t = self.normalize_type_name(self.module_global_var_types[nm])
                if global_t not in {"", "unknown"}:
                    return global_t
        if kind == "Call":
            call_t = self.normalize_type_name(self._infer_numeric_call_expr_type(node_for_base))
            if call_t != "":
                return call_t
            call_ret_t = self.normalize_type_name(self._infer_call_expr_type(node_for_base))
            if call_ret_t not in {"", "unknown"}:
                return call_ret_t
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
            if nm in self.module_global_var_types:
                return self.normalize_type_name(self.module_global_var_types[nm])
        if kind == "Attribute":
            owner = self.any_to_dict_or_empty(node_for_base.get("value"))
            owner_t0 = self.get_expr_type(node_for_base.get("value"))
            owner_t = self._strip_rc_wrapper(self.normalize_type_name(owner_t0 if isinstance(owner_t0, str) else ""))
            attr = self.any_to_str(node_for_base.get("attr"))
            for owner_candidate in self._expand_runtime_class_candidates(owner_t):
                owner_fields = self.class_field_types.get(owner_candidate, {})
                if isinstance(owner_fields, dict):
                    field_t = self.normalize_type_name(self.any_to_str(owner_fields.get(attr)))
                    if field_t not in {"", "unknown"}:
                        return field_t
            if self._node_kind_from_dict(owner) == "Name":
                owner_name = self.any_to_str(owner.get("id"))
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
                homogeneous_tuple_item_t = self._homogeneous_tuple_ellipsis_item_type(owner_t)
                if homogeneous_tuple_item_t != "":
                    return homogeneous_tuple_item_t
                tuple_parts = self.split_generic(owner_t[6:-1])
                if len(tuple_parts) == 1:
                    return self.normalize_type_name(tuple_parts[0])
            if owner_t == "str":
                sl_node = self.any_to_dict_or_empty(node_for_base.get("slice"))
                if self._node_kind_from_dict(sl_node) != "Slice":
                    return "str"
        return ""

    # module/import helpers moved to backends.cpp.emitter.module.CppModuleEmitter.

    def _seed_non_escape_summary_from_meta(self, meta: dict[str, Any]) -> None:
        """module meta の `non_escape_summary` を C++ 側状態へ取り込む。"""
        out: dict[str, dict[str, Any]] = {}
        summary_any = meta.get("non_escape_summary")
        if isinstance(summary_any, dict):
            for symbol_any, payload_any in summary_any.items():
                if not isinstance(symbol_any, str):
                    continue
                symbol = self.any_to_str(symbol_any).strip()
                if symbol == "":
                    continue
                if isinstance(payload_any, dict):
                    out[symbol] = dict(payload_any)
        self.non_escape_summary_map = out

    def _resolve_function_non_escape_summary(
        self,
        stmt: dict[str, Any],
        function_symbol: str,
    ) -> dict[str, Any]:
        """FunctionDef ノードの non-escape 注釈を module summary から解決する。"""
        meta = self.any_to_dict_or_empty(stmt.get("meta"))
        local = self.any_to_dict_or_empty(meta.get("escape_summary"))
        if len(local) > 0:
            return dict(local)
        if function_symbol in self.non_escape_summary_map:
            payload = self.any_to_dict_or_empty(self.non_escape_summary_map.get(function_symbol))
            if len(payload) > 0:
                return dict(payload)
        return {}

    def _record_non_escape_callsite(self, call_node: dict[str, Any]) -> None:
        """Call ノードの non-escape 注釈を C++ 側レコードへ保存する。"""
        meta = self.any_to_dict_or_empty(call_node.get("meta"))
        callsite = self.any_to_dict_or_empty(meta.get("non_escape_callsite"))
        if len(callsite) == 0:
            return
        callee = self.any_dict_get_str(callsite, "callee", "")
        record: dict[str, Any] = {
            "function_symbol": self.current_function_symbol,
            "callee": callee,
            "resolved": bool(callsite.get("resolved", False)),
            "callee_return_escape": bool(callsite.get("callee_return_escape", False)),
            "callee_arg_escape": self.any_to_list(callsite.get("callee_arg_escape")),
        }
        self.non_escape_callsite_records.append(record)

    def _is_stack_list_local_name(self, name: str) -> bool:
        """現在関数で stack/value 縮退対象になった list ローカルか判定する。"""
        if name == "":
            return False
        return name in self.current_function_stack_list_locals

    def _expr_is_stack_list_local(self, expr_node: Any) -> bool:
        """式が stack/value list ローカル参照かを返す（Name 限定）。"""
        node = self.any_to_dict_or_empty(expr_node)
        if self._node_kind_from_dict(node) != "Name":
            return False
        name = self.any_dict_get_str(node, "id", "")
        return self._is_stack_list_local_name(name)

    def _is_typed_list_str_name(self, name: str) -> bool:
        """現在関数で `list[str]` を value-model 扱いする識別子か判定する。"""
        if name == "":
            return False
        if name in self.current_function_typed_list_str_params:
            return True
        return name in self.current_function_typed_list_str_locals

    def _is_pyobj_runtime_list_alias_name(self, name: str) -> bool:
        """`cpp_list_model=pyobj` で handle-backed list として扱う識別子か判定する。"""
        if name == "":
            return False
        return name in self.current_function_pyobj_runtime_list_alias_names

    def _is_named_value_list_name(self, name: str) -> bool:
        """現在関数で concrete value list として出力される識別子か判定する。"""
        if name == "":
            return False
        if name in self.current_function_value_list_params:
            return True
        return name in self.current_function_value_list_locals

    def _expr_is_named_value_list(self, expr_node: Any) -> bool:
        """Name 式が value-model の concrete list local/param か判定する。"""
        node = self.any_to_dict_or_empty(expr_node)
        if self._node_kind_from_dict(node) != "Name":
            return False
        expr_name = self.any_dict_get_str(node, "id", "")
        return self._is_named_value_list_name(expr_name)

    def _unwrap_pyobj_list_source_expr(self, expr_node: Any) -> dict[str, Any]:
        """list source 判定時に無視してよい wrapper を剥がす。"""
        node = self.any_to_dict_or_empty(expr_node)
        while len(node) > 0:
            kind = self._node_kind_from_dict(node)
            if kind not in {"Unbox", "CastOrRaise"}:
                break
            target_t = self.normalize_type_name(self.any_to_str(node.get("target")))
            if target_t in {"", "unknown"}:
                target_t = self.normalize_type_name(self.any_to_str(node.get("resolved_type")))
            if not (target_t.startswith("list[") and target_t.endswith("]")):
                break
            inner = self.any_to_dict_or_empty(node.get("value"))
            if len(inner) == 0:
                break
            node = inner
        return node

    def _render_unwrapped_pyobj_list_source_expr(self, rendered_expr: str, expr_node: Any) -> str:
        """透過 wrapper を剥がした list source の描画を返す。"""
        node = self.any_to_dict_or_empty(expr_node)
        unwrapped = self._unwrap_pyobj_list_source_expr(expr_node)
        if len(unwrapped) == 0 or unwrapped == node:
            return rendered_expr
        unwrapped_expr = self.render_expr(unwrapped)
        if unwrapped_expr == "":
            return rendered_expr
        return unwrapped_expr

    def _render_pyobj_ref_first_list_container_item(self, owner_node: Any, value_expr: str, value_node: Any) -> str:
        """ref-first outer list へ格納する要素に必要な adapter を適用する。"""
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        if owner_t in {"", "unknown"}:
            owner_t = self.normalize_type_name(self.any_dict_get_str(self.any_to_dict_or_empty(owner_node), "resolved_type", ""))
        inner_parts = self.type_generic_args(owner_t, "list")
        if len(inner_parts) != 1:
            return value_expr
        item_t = self.normalize_type_name(inner_parts[0])
        if self._is_pyobj_value_model_list_type(item_t):
            return self._render_pyobj_value_list_copy_adapter(value_expr, value_node, item_t)
        return value_expr

    def _function_runtime_abi_meta(self, fn_node: Any) -> dict[str, Any]:
        fn = self.any_to_dict_or_empty(fn_node)
        meta = self.any_to_dict_or_empty(fn.get("meta"))
        runtime_abi = self.any_to_dict_or_empty(meta.get("runtime_abi_v1"))
        schema_version = runtime_abi.get("schema_version", 0)
        if not isinstance(schema_version, int) or int(schema_version) != 1:
            return {}
        return runtime_abi

    def _function_runtime_abi_arg_mode(self, fn_node: Any, arg_name: str) -> str:
        runtime_abi = self._function_runtime_abi_meta(fn_node)
        args = self.any_to_dict_or_empty(runtime_abi.get("args"))
        mode = self.any_to_str(args.get(arg_name))
        return mode if mode != "" else "default"

    def _function_runtime_abi_ret_mode(self, fn_node: Any) -> str:
        runtime_abi = self._function_runtime_abi_meta(fn_node)
        mode = self.any_to_str(runtime_abi.get("ret"))
        return mode if mode != "" else "default"

    def _is_known_pyobj_value_list_source_expr(self, expr_node: Any) -> bool:
        """ref-first target へ `rc_list_from_value(...)` で昇格すべき value-list source か判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self._unwrap_pyobj_list_source_expr(expr_node)
        if len(node) == 0:
            return False
        if self._uses_pyobj_ref_first_list_lvalue_expr(node) or self._call_expr_returns_known_pyobj_list_handle(node):
            return False
        source_t = self.normalize_type_name(self.get_expr_type(node))
        if source_t in {"", "unknown"}:
            source_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        if self._is_pyobj_value_model_list_type(source_t):
            return True
        if self._node_kind_from_dict(node) != "Call":
            return False
        if self.any_dict_get_str(node, "lowered_kind", "") != "BuiltinCall":
            return False
        runtime_call = self.any_dict_get_str(node, "runtime_call", "")
        return runtime_call in {"dict.keys", "dict.values", "dict.items"}

    def _call_expr_returns_known_pyobj_list_handle(self, expr_node: Any) -> bool:
        """既知関数/メソッド call が ref-first list handle を返すか判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self._unwrap_pyobj_list_source_expr(expr_node)
        if self._node_kind_from_dict(node) != "Call":
            return False
        if self.any_dict_get_str(node, "lowered_kind", "") == "BuiltinCall":
            return False
        fn_node = self.any_to_dict_or_empty(node.get("func"))
        fn_kind = self._node_kind_from_dict(fn_node)
        if fn_kind == "Name":
            fn_name = self.any_to_str(fn_node.get("id"))
            if fn_name == "":
                return False
            fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            ret_abi_mode = self.any_to_str(self.function_return_abi_modes.get(fn_name, "default"))
            if ret_abi_mode in {"value", "value_readonly"}:
                return False
            ret_t = self.normalize_type_name(self.function_return_types.get(fn_name, ""))
            return self._is_pyobj_ref_first_list_type(ret_t)
        if fn_kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            owner_rendered = self.render_expr(owner_node)
            owner_ctx = self.resolve_attribute_owner_context(owner_node, owner_rendered)
            owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
            attr = self.any_to_str(fn_node.get("attr"))
            if owner_mod != "" and attr != "":
                ret_cpp = self.any_to_str(self._module_function_cpp_return_type(owner_mod, attr))
                if "rc<list<" in ret_cpp:
                    ret_t = self.normalize_type_name(self._module_function_return_type(owner_mod, attr))
                    return self._is_pyobj_ref_first_list_type(ret_t)
                if "list<" in ret_cpp:
                    return False
            ret_t = self.normalize_type_name(self._infer_call_expr_type(node))
            return self._is_pyobj_ref_first_list_type(ret_t)
        return False

    def _uses_pyobj_rc_list_expr(self, expr_node: Any) -> bool:
        """list 式が `rc<list<T>>` alias handle 経路を使うべきか判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0:
            return False
        if self._node_kind_from_dict(node) != "Name":
            return False
        expr_name = self.any_dict_get_str(node, "id", "")
        if expr_name == "" or self._is_typed_list_str_name(expr_name):
            return False
        return self._is_pyobj_runtime_list_alias_name(expr_name)

    def _is_pyobj_ref_first_list_target_expr(self, expr_node: Any, east_type: str = "") -> bool:
        """Name/Attribute 左辺が ref-first list handle 正本か判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0:
            return False
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            expr_name = self.any_dict_get_str(node, "id", "")
            if expr_name == "":
                return False
            if self._expr_is_stack_list_local(node):
                return False
            return self._is_pyobj_runtime_list_alias_name(expr_name)
        if kind != "Attribute":
            return False
        expr_t = self.normalize_type_name(east_type)
        if expr_t in {"", "unknown"}:
            expr_t = self.normalize_type_name(self.get_expr_type(node))
        if expr_t in {"", "unknown"}:
            expr_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        return self._is_pyobj_ref_first_list_type(expr_t)

    def _uses_pyobj_ref_first_list_lvalue_expr(self, expr_node: Any) -> bool:
        """`rc_list_ref(...)` を安全に使える ref-first list 式か判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0 or self._expr_is_stack_list_local(node):
            return False
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            expr_name = self.any_dict_get_str(node, "id", "")
            if expr_name == "":
                return False
            if self._uses_pyobj_rc_list_expr(node):
                return True
            if not self._is_typed_list_str_name(expr_name):
                return False
            expr_t = self.normalize_type_name(self.get_expr_type(node))
            if expr_t in {"", "unknown"}:
                expr_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
            return self._is_pyobj_ref_first_list_type(expr_t)
        if kind == "Attribute":
            expr_t = self.normalize_type_name(self.get_expr_type(node))
            if expr_t in {"", "unknown"}:
                expr_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
            return self._is_pyobj_ref_first_list_type(expr_t)
        if self._is_pyobj_ref_first_list_target_expr(node):
            return True
        return False

    def _uses_pyobj_ref_first_list_ops(self, expr_node: Any) -> bool:
        """`py_*` の ref-first list helper を使うべき式か判定する。"""
        if self._uses_pyobj_ref_first_list_lvalue_expr(expr_node) or self._call_expr_returns_known_pyobj_list_handle(
            expr_node
        ):
            return True
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0 or self._expr_is_stack_list_local(node):
            return False
        if self._node_kind_from_dict(node) != "Subscript":
            return False
        expr_t = self.normalize_type_name(self.get_expr_type(node))
        if expr_t in {"", "unknown"}:
            expr_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        return self._is_pyobj_ref_first_list_type(expr_t)

    def _uses_pyobj_runtime_list_expr(self, expr_node: Any) -> bool:
        """list 式が pyobj runtime list 経路（`py_*` 操作）を使うべきか判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0:
            return False
        if self._expr_is_stack_list_local(node):
            return False
        if self._node_kind_from_dict(node) == "Name":
            expr_name = self.any_dict_get_str(node, "id", "")
            if self._is_typed_list_str_name(expr_name):
                return False
            if self._is_pyobj_runtime_list_alias_name(expr_name):
                return False
            if self._expr_is_named_value_list(node):
                return False
        expr_t = self.normalize_type_name(self.get_expr_type(node))
        if expr_t in {"", "unknown"}:
            expr_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        if self._is_pyobj_value_model_list_type(expr_t):
            return False
        if expr_t in {"", "unknown"} or self.is_any_like_type(expr_t):
            return True
        if self._contains_text(expr_t, "|"):
            for part in self.split_union(expr_t):
                part_norm = self.normalize_type_name(part)
                if self._is_pyobj_value_model_list_type(part_norm):
                    continue
                if part_norm in {"", "unknown"} or self.is_any_like_type(part_norm):
                    return True
                if part_norm.startswith("list[") and part_norm.endswith("]") and self._is_pyobj_runtime_list_type(part_norm):
                    return True
            return False
        if expr_t.startswith("list[") and expr_t.endswith("]"):
            return self._is_pyobj_runtime_list_type(expr_t)
        return False

    def _cpp_list_value_model_type_text(self, east_type: str) -> str:
        """`cpp_list_model=pyobj` 下でも list を value-model 型文字列へ展開する。"""
        t = self.normalize_type_name(east_type)
        parts = self.type_generic_args(t, "list")
        if len(parts) != 1:
            return "list<object>"
        elem = self.normalize_type_name(parts[0])
        if elem in {"", "unknown", "Any", "object", "None"}:
            return "list<object>"
        if elem == "uint8":
            return "bytearray"
        if elem.startswith("list[") and elem.endswith("]"):
            return f"list<{self._cpp_list_value_model_type_text(elem)}>"
        return f"list<{self._cpp_type_text(elem)}>"

    def _cpp_pyobj_alias_list_handle_type_text(self, east_type: str) -> str:
        """alias 維持用の `rc<list<T>>` 型文字列を返す。"""
        return f"rc<{self._cpp_list_value_model_type_text(east_type)}>"

    def _render_pyobj_alias_list_value(self, rendered_expr: str, value_node: Any, east_type: str) -> str:
        """list 値を `rc<list<T>>` handle 初期化へ寄せる。"""
        rendered_trim = self._trim_ws(rendered_expr)
        if rendered_trim == "":
            return rendered_expr
        source_expr = self._render_unwrapped_pyobj_list_source_expr(rendered_expr, value_node)
        list_t = self.normalize_type_name(east_type)
        handle_cpp_t = self._cpp_pyobj_alias_list_handle_type_text(list_t)
        value_cpp_t = self._cpp_list_value_model_type_text(list_t)
        if rendered_trim.startswith(f"py_to<{handle_cpp_t}>(") or rendered_trim.startswith("rc_list_from_value("):
            return rendered_expr

        value = self._unwrap_pyobj_list_source_expr(value_node)
        if self._uses_pyobj_ref_first_list_lvalue_expr(value):
            return source_expr
        kind = self._node_kind_from_dict(value)
        if kind == "Name":
            src_name = self.any_dict_get_str(value, "id", "")
            if self._is_pyobj_runtime_list_alias_name(src_name):
                return source_expr
        if kind == "Call" and self._call_expr_returns_known_pyobj_list_handle(value):
            return source_expr
        if kind == "List":
            elems = self._dict_stmt_list(value.get("elements"))
            inner_parts = self.type_generic_args(list_t, "list")
            inner_t = self.normalize_type_name(inner_parts[0]) if len(inner_parts) == 1 else ""
            rendered_items: list[str] = []
            for elem in elems:
                item_txt = self.render_expr(elem)
                elem_t = self.normalize_type_name(self.get_expr_type(elem))
                if inner_t != "" and self.is_any_like_type(elem_t) and self._can_runtime_cast_target(inner_t):
                    item_txt = self._coerce_any_expr_to_target_via_unbox(
                        item_txt,
                        elem,
                        inner_t,
                        "assign:pyobj_alias_list_literal",
                    )
                rendered_items.append(item_txt)
            return f"rc_list_from_value({value_cpp_t}{{{join_str_list(', ', rendered_items)}}})"
        if kind == "ListComp":
            rewritten = rendered_expr
            if rendered_trim.startswith("[&]() -> list<object> {"):
                rewritten = rendered_expr.replace("[&]() -> list<object> {", f"[&]() -> {value_cpp_t} {{", 1)
                rewritten = rewritten.replace("list<object> __out;", f"{value_cpp_t} __out;", 1)
            value_t = self.normalize_type_name(self.get_expr_type(value_node))
            if (
                rewritten.startswith("[&]() -> object {")
                or self.is_any_like_type(value_t)
                or self._uses_pyobj_runtime_list_expr(value_node)
            ):
                return f"py_to<{handle_cpp_t}>({rewritten})"
            return f"rc_list_from_value({rewritten})"

        value_t = self.normalize_type_name(self.get_expr_type(value))
        if self.is_any_like_type(value_t) or self._uses_pyobj_runtime_list_expr(value_node):
            return f"py_to<{handle_cpp_t}>({rendered_expr})"
        if value_t.startswith("list[") and value_t.endswith("]"):
            return f"rc_list_from_value({rendered_expr})"
        return rendered_expr

    def _uses_pyobj_ref_first_list_value_source(self, expr_node: Any) -> bool:
        """ref-first handle 由来の list source か判定する。"""
        return self._uses_pyobj_ref_first_list_lvalue_expr(expr_node) or self._call_expr_returns_known_pyobj_list_handle(
            expr_node
        )

    def _render_pyobj_value_list_copy_adapter(self, rendered_expr: str, value_node: Any, east_type: str) -> str:
        """ref-first handle から value list を要求する箇所向け copy adapter。"""
        rendered_trim = self._trim_ws(rendered_expr)
        if rendered_trim == "":
            return rendered_expr
        source_expr = self._render_unwrapped_pyobj_list_source_expr(rendered_expr, value_node)
        source_node = self._unwrap_pyobj_list_source_expr(value_node)
        list_t = self.normalize_type_name(east_type)
        if not self._is_pyobj_value_model_list_type(list_t):
            return rendered_expr
        if rendered_trim.startswith("rc_list_copy_value("):
            return rendered_expr
        if self._uses_pyobj_ref_first_list_value_source(source_node):
            return f"rc_list_copy_value({source_expr})"
        return rendered_expr

    def _render_pyobj_value_list_arg_adapter(self, rendered_expr: str, value_node: Any, east_type: str) -> str:
        """ref-first handle を `list<T>` 引数へ渡すための ABI adapter。"""
        rendered_trim = self._trim_ws(rendered_expr)
        if rendered_trim == "":
            return rendered_expr
        source_expr = self._render_unwrapped_pyobj_list_source_expr(rendered_expr, value_node)
        source_node = self._unwrap_pyobj_list_source_expr(value_node)
        list_t = self.normalize_type_name(east_type)
        if not self._is_pyobj_value_model_list_type(list_t):
            return rendered_expr
        if rendered_trim.startswith("rc_list_ref(") or rendered_trim.startswith("rc_list_copy_value("):
            return rendered_expr
        if self._uses_pyobj_ref_first_list_lvalue_expr(source_node):
            return f"rc_list_ref({source_expr})"
        if self._call_expr_returns_known_pyobj_list_handle(source_node):
            return f"rc_list_copy_value({source_expr})"
        return rendered_expr

    def _collect_name_reads(self, node: Any, out: set[str]) -> None:
        """式/文ノード内の Name 参照を抽出する。"""
        if isinstance(node, list):
            i = 0
            while i < len(node):
                self._collect_name_reads(node[i], out)
                i += 1
            return
        if not isinstance(node, dict):
            return
        if node.get("kind") == "Name":
            ident = self.any_dict_get_str(node, "id", "")
            if ident != "":
                out.add(ident)
        for value in node.values():
            self._collect_name_reads(value, out)

    def _collect_name_targets(self, target_node: Any, out: set[str]) -> None:
        """代入ターゲットの Name 集合を抽出する。"""
        if isinstance(target_node, list):
            i = 0
            while i < len(target_node):
                self._collect_name_targets(target_node[i], out)
                i += 1
            return
        node = self.any_to_dict_or_empty(target_node)
        kind = self._node_kind_from_dict(node)
        if kind == "Name":
            ident = self.any_dict_get_str(node, "id", "")
            if ident != "":
                out.add(ident)
            return
        if kind == "Tuple":
            elems = self.any_to_list(node.get("elements"))
            i = 0
            while i < len(elems):
                self._collect_name_targets(elems[i], out)
                i += 1

    def _collect_stack_list_locals(self, fn_stmt: dict[str, Any]) -> set[str]:
        """optimizer が付けた value-local hint を読み取る。"""
        out: set[str] = set()
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return out
        meta = self.any_to_dict_or_empty(fn_stmt.get("meta"))
        payload = self.any_to_dict_or_empty(meta.get("cpp_value_list_locals_v1"))
        locals_any = payload.get("locals")
        if not isinstance(locals_any, list):
            return out
        for item in locals_any:
            if isinstance(item, str) and item != "":
                out.add(item)
        return out

    def _collect_pyobj_runtime_list_alias_names(
        self,
        fn_stmt: dict[str, Any],
        stack_list_locals: set[str] | None = None,
    ) -> set[str]:
        """`pyobj` で handle-backed に保つ typed list 名を収集する。"""
        out: set[str] = set()
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return out
        stack_lowered = set(stack_list_locals or set())
        body = self._dict_stmt_list(fn_stmt.get("body"))
        assigned_types = self._collect_assigned_name_types(body)
        list_like_names: set[str] = set()
        for raw_name, raw_type in assigned_types.items():
            if not isinstance(raw_name, str):
                continue
            name = raw_name
            if name == "":
                continue
            type_norm = self.normalize_type_name(self.any_to_str(raw_type))
            if self._is_pyobj_ref_first_list_type(type_norm):
                list_like_names.add(name)

        if len(list_like_names) == 0:
            return out

        for name in list_like_names:
            if name not in stack_lowered:
                out.add(name)

        changed = True
        while changed:
            changed = False

            def _mark(name: str) -> None:
                nonlocal changed
                if name == "" or name in out:
                    return
                out.add(name)
                changed = True

            def _scan(cur: Any) -> None:
                node = self.any_to_dict_or_empty(cur)
                if len(node) == 0:
                    return
                kind = self._node_kind_from_dict(node)
                if kind in {"Assign", "AnnAssign"}:
                    targets: set[str] = set()
                    self._collect_name_targets(node.get("target"), targets)
                    value_node = self.any_to_dict_or_empty(node.get("value"))
                    if self._node_kind_from_dict(value_node) == "Name":
                        src_name = self.any_dict_get_str(value_node, "id", "")
                        if src_name in list_like_names or src_name in out:
                            if not (len(targets) == 1 and src_name in targets):
                                _mark(src_name)
                                for target_name in targets:
                                    _mark(target_name)
                for value in node.values():
                    if isinstance(value, dict) or isinstance(value, list):
                        _scan(value)

            i = 0
            while i < len(body):
                _scan(body[i])
                i += 1
        return out

    def _cpp_helper_owner_module_id(self) -> str:
        meta = dict_any_get_dict(self.doc, "meta")
        module_id = self.any_dict_get_str(meta, "module_id", "")
        if module_id != "":
            return module_id
        if self.top_namespace != "":
            return self.top_namespace
        return "__module__"

    def _sanitize_cpp_helper_label(self, text: str) -> str:
        out_parts: list[str] = []
        last_sep = False
        for ch in text:
            if ch.isalnum():
                out_parts.append(ch.lower())
                last_sep = False
                continue
            if not last_sep:
                out_parts.append("_")
                last_sep = True
        out = "".join(out_parts).strip("_")
        if out == "":
            return "module"
        return out

    def _cpp_object_iter_helper_label(self) -> str:
        owner_id = self._cpp_helper_owner_module_id()
        return self._sanitize_cpp_helper_label(owner_id) + "_cpp_object_iter_helper"

    def _cpp_object_iter_helper_module_id(self) -> str:
        owner_id = self._cpp_helper_owner_module_id()
        return "__pytra_helper__.cpp." + self._sanitize_cpp_helper_label(owner_id) + ".object_iter"

    def _cpp_object_iter_helper_header_include(self) -> str:
        return self._cpp_object_iter_helper_label() + ".h"

    def _cpp_helper_artifact_registered(self, helper_id: str) -> bool:
        for artifact in self.helper_artifacts:
            if not isinstance(artifact, dict):
                continue
            metadata = artifact.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if self.any_to_str(metadata.get("helper_id")) == helper_id:
                return True
        return False

    def _render_cpp_helper_call(self, helper_id: str, fn_name: str, args: list[str]) -> str:
        if not self.enable_helper_artifact_lane:
            return ""
        if not self._cpp_helper_artifact_registered(helper_id):
            return ""
        return "pytra_multi_helper::" + fn_name + "(" + join_str_list(", ", args) + ")"

    def _cpp_helper_header_includes(self) -> list[str]:
        includes: list[str] = []
        seen: set[str] = set()
        for artifact in self.helper_artifacts:
            if not isinstance(artifact, dict):
                continue
            metadata = artifact.get("metadata")
            if not isinstance(metadata, dict):
                continue
            inc = self.any_to_str(metadata.get("header_include"))
            if inc == "" or inc in seen:
                continue
            seen.add(inc)
            includes.append(inc)
        includes.sort()
        return includes

    def _body_uses_cpp_object_iter_helper(self, body: list[dict[str, Any]]) -> bool:
        found = False

        def _scan(cur: Any) -> None:
            nonlocal found
            if found:
                return
            if isinstance(cur, list):
                for item in cur:
                    _scan(item)
                return
            node = self.any_to_dict_or_empty(cur)
            if len(node) == 0:
                return
            kind = self._node_kind_from_dict(node)
            if kind in {"ObjIterInit", "ObjIterNext"}:
                found = True
                return
            if kind == "RuntimeSpecialOp":
                op = self.any_dict_get_str(node, "op", "")
                if op in {"iter_or_raise", "next_or_stop"}:
                    found = True
                    return
            runtime_call = self.any_dict_get_str(node, "runtime_call", "")
            if runtime_call in {"py_iter_or_raise", "py_next_or_stop"}:
                found = True
                return
            if self.any_dict_get_str(node, "iter_mode", "") == "runtime_protocol":
                found = True
                return
            if self.any_dict_get_str(node, "hint_mode", "") == "runtime_protocol":
                found = True
                return
            for value in node.values():
                if isinstance(value, dict) or isinstance(value, list):
                    _scan(value)

        _scan(body)
        return found

    def _cpp_object_iter_helper_header_text(self) -> str:
        label = self._cpp_object_iter_helper_label()
        guard = "PYTRA_MULTI_" + self._sanitize_cpp_helper_label(label).upper() + "_H"
        return (
            "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
            "#ifndef " + guard + "\n"
            "#define " + guard + "\n\n"
            '#include "runtime/cpp/native/core/py_runtime.h"\n\n'
            "namespace pytra_multi_helper {\n"
            "object object_iter_or_raise(const object& value);\n"
            "::std::optional<object> object_iter_next_or_stop(const object& iter_obj);\n"
            "}  // namespace pytra_multi_helper\n\n"
            "#endif  // " + guard + "\n"
        )

    def _cpp_object_iter_helper_source_text(self) -> str:
        header_include = self._cpp_object_iter_helper_header_include()
        return (
            "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
            '#include "pytra_multi_prelude.h"\n'
            '#include "' + header_include + '"\n\n'
            "namespace pytra_multi_helper {\n"
            "object object_iter_or_raise(const object& value) {\n"
            "    object __obj = value;\n"
            '    if (!__obj) throw TypeError("NoneType is not iterable");\n'
            "    return __obj->py_iter_or_raise();\n"
            "}\n\n"
            "::std::optional<object> object_iter_next_or_stop(const object& iter_obj) {\n"
            "    object __iter = iter_obj;\n"
            '    if (!__iter) throw TypeError("NoneType is not an iterator");\n'
            "    return __iter->py_next_or_stop();\n"
            "}\n"
            "}  // namespace pytra_multi_helper\n"
        )

    def _ensure_cpp_object_iter_helper_artifact(self) -> None:
        helper_id = "cpp.object_iter"
        if self._cpp_helper_artifact_registered(helper_id):
            return
        owner_module_id = self._cpp_helper_owner_module_id()
        header_text = self._cpp_object_iter_helper_header_text()
        source_text = self._cpp_object_iter_helper_source_text()
        self.add_helper_artifact(
            {
                "module_id": self._cpp_object_iter_helper_module_id(),
                "kind": "helper",
                "label": self._cpp_object_iter_helper_label(),
                "extension": ".cpp",
                "text": source_text,
                "is_entry": False,
                "dependencies": [],
                "metadata": {
                    "helper_id": helper_id,
                    "owner_module_id": owner_module_id,
                    "generated_by": "cpp_emitter",
                    "header_text": header_text,
                    "source_text": source_text,
                    "header_include": self._cpp_object_iter_helper_header_include(),
                },
            }
        )

    def _register_cpp_helper_artifacts_from_body(self, body: list[dict[str, Any]]) -> None:
        if self._body_uses_cpp_object_iter_helper(body):
            self._ensure_cpp_object_iter_helper_artifact()

    def transpile(self) -> str:
        """EAST ドキュメント全体を C++ ソース文字列へ変換する。"""
        self.helper_artifacts = []
        self._seed_import_maps_from_meta()
        meta: dict[str, Any] = dict_any_get_dict(self.doc, "meta")
        self._seed_non_escape_summary_from_meta(meta)
        body: list[dict[str, Any]] = []
        raw_body = self.any_dict_get_list(self.doc, "body")
        if isinstance(raw_body, list):
            for s in raw_body:
                if isinstance(s, dict):
                    body.append(s)
        self._prime_import_bindings_from_body(body)
        if self.enable_helper_artifact_lane:
            self._register_cpp_helper_artifacts_from_body(body)
        current_module_name = self._current_user_module_name()
        for stmt in body:
            if self._node_kind_from_dict(stmt) == "ClassDef":
                cls_name = self.any_dict_get_str(stmt, "name", "")
                if cls_name != "":
                    self.class_names.add(cls_name)
                    cls_field_types: dict[str, str] = {}
                    mset: set[str] = set()
                    marg: dict[str, list[str]] = {}
                    marg_names: dict[str, list[str]] = {}
                    mdefaults: dict[str, dict[str, Any]] = {}
                    mret: dict[str, str] = {}
                    props: set[str] = set()
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
                            decorators = self.any_to_list(s.get("decorators"))
                            for decorator in decorators:
                                if not isinstance(decorator, str):
                                    continue
                                head = decorator.strip()
                                if head == "":
                                    continue
                                if "(" in head:
                                    head = head.split("(", 1)[0].strip()
                                if head.split(".")[-1] == "property":
                                    props.add(fn_name)
                                    break
                            mret[fn_name] = self.normalize_type_name(self.any_to_str(s.get("return_type")))
                            arg_types = self.any_to_dict_or_empty(s.get("arg_types"))
                            arg_defaults = self.any_to_dict_or_empty(s.get("arg_defaults"))
                            arg_order = self.any_dict_get_list(s, "arg_order")
                            ordered: list[str] = []
                            ordered_names: list[str] = []
                            ordered_defaults: dict[str, Any] = {}
                            for raw_n in arg_order:
                                if isinstance(raw_n, str):
                                    n = str(raw_n)
                                    if n != "self":
                                        ordered_names.append(n)
                                        if n in arg_types:
                                            ordered.append(
                                                self._normalize_user_class_signature_arg_type(
                                                    current_module_name,
                                                    self.doc,
                                                    self.any_to_str(arg_types.get(n)),
                                                )
                                            )
                                        if n in arg_defaults:
                                            ordered_defaults[n] = arg_defaults.get(n)
                            marg[fn_name] = ordered
                            marg_names[fn_name] = ordered_names
                            mdefaults[fn_name] = ordered_defaults
                    self.class_method_names[cls_name] = mset
                    self.class_method_arg_types[cls_name] = marg
                    self.class_method_arg_names[cls_name] = marg_names
                    self.class_method_arg_defaults[cls_name] = mdefaults
                    self.class_method_return_types[cls_name] = mret
                    self.class_property_names[cls_name] = props
                    field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
                    for raw_attr, raw_ft in field_types.items():
                        if not isinstance(raw_attr, str):
                            continue
                        attr = raw_attr
                        if attr == "":
                            continue
                        ft = self.normalize_type_name(self.any_to_str(raw_ft))
                        if ft != "":
                            cls_field_types[attr] = ft
                    self.class_field_types[cls_name] = cls_field_types
                    base_raw = stmt.get("base")
                    base = str(base_raw) if isinstance(base_raw, str) else ""
                    if base != "":
                        base = self._resolve_local_class_base_cpp_name(base)
                    self.class_base[cls_name] = base
                    hint = self.any_dict_get_str(stmt, "class_storage_hint", "ref")
                    hint = self._effective_user_class_storage_hint(current_module_name, cls_name, hint)
                    self.class_storage_hints[cls_name] = hint if hint in {"value", "ref"} else "ref"
            elif self._node_kind_from_dict(stmt) == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                if fn_name != "":
                    fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                    arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
                    arg_order = self.any_dict_get_list(stmt, "arg_order")
                    body_stmts = self._dict_stmt_list(stmt.get("body"))
                    ordered: list[str] = []
                    abi_modes: list[str] = []
                    arg_names_for_mutation: list[str] = []
                    for raw_n in arg_order:
                        if isinstance(raw_n, str):
                            n = str(raw_n)
                            if n in arg_types:
                                arg_names_for_mutation.append(n)
                                ordered.append(
                                    self._normalize_user_class_signature_arg_type(
                                        current_module_name,
                                        self.doc,
                                        self.any_to_str(arg_types.get(n)),
                                    )
                                )
                                abi_modes.append(self._function_runtime_abi_arg_mode(stmt, n))
                    self.function_arg_types[fn_name] = ordered
                    self.function_arg_abi_modes[fn_name] = abi_modes
                    mutated_positions: set[int] = set()
                    vararg_type = self.normalize_type_name(self.any_dict_get_str(stmt, "vararg_type", ""))
                    vararg_name = self.any_dict_get_str(stmt, "vararg_name", "")
                    if vararg_name != "" and vararg_type != "":
                        arg_names_for_mutation.append(vararg_name)
                        self.function_vararg_list_types[fn_name] = f"list[{vararg_type}]"
                    mutated_params = self._collect_mutated_params(body_stmts, arg_names_for_mutation)
                    for idx, arg_name in enumerate(arg_names_for_mutation):
                        if arg_name in mutated_params:
                            mutated_positions.add(idx)
                    self.function_mutated_param_positions[fn_name] = mutated_positions
                    self.function_return_types[fn_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
                    self.function_return_abi_modes[fn_name] = self._function_runtime_abi_ret_mode(stmt)
                    decorators = self.any_to_list(stmt.get("decorators"))
                    for decorator in decorators:
                        if not isinstance(decorator, str):
                            continue
                        head = decorator.strip()
                        if head == "":
                            continue
                        if "(" in head:
                            head = head.split("(", 1)[0].strip()
                        if head.split(".")[-1] == "extern":
                            self.extern_function_names.add(fn_name)
                            break

        self._register_imported_runtime_class_metadata()
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
        for base_cpp_name, methods in self._global_user_virtual_methods_by_base_cpp_name().items():
            class_key = self._class_key_for_cpp_name(base_cpp_name)
            if class_key == "" or class_key not in self.class_method_virtual:
                continue
            self.class_method_virtual[class_key].update(methods)
        self.class_method_force_nonconst = {cls: set() for cls in self.class_method_names}
        for base_cpp_name, methods in self._global_user_nonconst_methods_by_base_cpp_name().items():
            class_key = self._class_key_for_cpp_name(base_cpp_name)
            if class_key == "":
                continue
            current = self.class_method_force_nonconst.get(class_key)
            if not isinstance(current, set):
                current = set()
                self.class_method_force_nonconst[class_key] = current
            current.update(methods)

        self.emit_module_leading_trivia()
        header_text: str = CPP_HEADER
        if len(header_text) > 0 and header_text[-1] == NEWLINE_CHAR:
            header_text = header_text[:-1]
        self.emit(header_text)
        extra_includes = self._collect_import_cpp_includes(body, meta)
        helper_includes = self._cpp_helper_header_includes()
        for inc in helper_includes:
            if inc not in extra_includes:
                extra_includes.append(inc)
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
        self.module_global_var_types = {}

        module_global_names: set[str] = set()
        for g_name, g_ty in module_globals:
            self.emit(f"{self._cpp_type_text(g_ty)} {g_name};")
            self.declare_in_current_scope(g_name)
            self.declared_var_types[g_name] = g_ty
            self.module_global_var_types[g_name] = g_ty
            module_global_names.add(g_name)
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
            # module init 内で top-level 代入を実行する際、global 変数の再宣言を防ぐ。
            self.scope_stack.append(set(module_global_names))
            self.emit_stmt_list(module_runtime_dicts)
            self.scope_stack.pop()
            self.indent -= 1
            self.emit("}")
            self.emit("")
            # runtime モジュール（--emit-runtime-cpp, emit_main=False）では
            # main() 経由で module init が呼ばれないため、静的初期化で1度だけ実行する。
            if not self.emit_main:
                self.emit("namespace {")
                self.indent += 1
                self.emit("struct __pytra_module_initializer {")
                self.indent += 1
                self.emit("__pytra_module_initializer() { __pytra_module_init(); }")
                self.indent -= 1
                self.emit("};")
                self.emit("static const __pytra_module_initializer __pytra_module_initializer_instance{};")
                self.indent -= 1
                self.emit("}  // namespace")
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
            if op in {"USub", "UAdd", "Invert"}:
                operand_t = self.normalize_type_name(self._infer_numeric_expr_type(node.get("operand")))
                if self._is_numeric_decl_type(operand_t) or op == "Invert":
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
        runtime_module_id = canonical_runtime_module_id(self.any_to_str(call_node.get("runtime_module_id")))
        runtime_symbol = self.any_to_str(call_node.get("runtime_symbol"))
        semantic_tag = self.any_to_str(call_node.get("semantic_tag"))
        if runtime_module_id == "pytra.std.math" and runtime_symbol in {
            "sin",
            "cos",
            "tan",
            "sqrt",
            "exp",
            "log",
            "log10",
            "fabs",
            "floor",
            "ceil",
        }:
            return "float64"
        if semantic_tag in {
            "stdlib.fn.sin",
            "stdlib.fn.cos",
            "stdlib.fn.tan",
            "stdlib.fn.sqrt",
            "stdlib.fn.exp",
            "stdlib.fn.log",
            "stdlib.fn.log10",
            "stdlib.fn.fabs",
            "stdlib.fn.floor",
            "stdlib.fn.ceil",
        }:
            return "float64"
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
            attr = self.any_to_str(fn_node.get("attr"))
            if attr in {"sin", "cos", "tan", "sqrt", "exp", "log", "log10", "fabs", "floor", "ceil"}:
                owner_name = self.any_to_str(owner.get("id")) if owner_kind == "Name" else ""
                owner_module = canonical_runtime_module_id(self._resolve_imported_module_name(owner_name))
                if owner_module == "":
                    owner_module = canonical_runtime_module_id(owner_name)
                if owner_module == "pytra.std.math":
                    return "float64"
            if runtime_module_id == "pytra.std.math" and attr in {"sin", "cos", "tan", "sqrt", "exp", "log", "log10", "fabs", "floor", "ceil"}:
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

    def _infer_call_expr_type(self, call_node: dict[str, Any]) -> str:
        """Call ノードの一般返り値型（非数値含む）を推定する。"""
        if len(call_node) == 0:
            return ""
        fn_node = self.any_to_dict_or_empty(call_node.get("func"))
        fn_kind = self._node_kind_from_dict(fn_node)
        if fn_kind == "Name":
            fn_name = self.any_to_str(fn_node.get("id"))
            if fn_name == "":
                return ""
            imported = self._resolve_imported_symbol(fn_name)
            imported_module = self.any_dict_get_str(imported, "module", "")
            imported_name = self.any_dict_get_str(imported, "name", "")
            if imported_module != "" and imported_name != "":
                imported_cpp_t = self._imported_runtime_class_cpp_type(imported_module, imported_name)
                imported_cpp_t = self.normalize_type_name(imported_cpp_t)
                if imported_cpp_t != "":
                    return imported_cpp_t
            mapped_t = self.normalize_type_name(self.type_map.get(fn_name, ""))
            if mapped_t != "":
                return mapped_t
            ret_t = self.normalize_type_name(self.function_return_types.get(fn_name, ""))
            if ret_t != "":
                return ret_t
            if fn_name in self.ref_classes:
                return f"rc<{fn_name}>"
            if fn_name in self.class_names:
                return fn_name
            return ""
        if fn_kind != "Attribute":
            return ""
        owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
        attr = self.any_to_str(fn_node.get("attr"))
        if attr == "":
            return ""
        owner_rendered = self.render_expr(owner_node)
        owner_ctx = self.resolve_attribute_owner_context(owner_node, owner_rendered)
        owner_mod = canonical_runtime_module_id(self.any_dict_get_str(owner_ctx, "module", ""))
        if owner_mod != "":
            ret = self.normalize_type_name(self._module_function_return_type(owner_mod, attr))
            if ret != "":
                return ret
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        owner_candidates = self._expand_runtime_class_candidates(owner_t)
        owner_t = owner_candidates[0] if len(owner_candidates) > 0 else self._strip_rc_wrapper(owner_t)
        if owner_t == "" and self._node_kind_from_dict(owner_node) == "Name":
            owner_name = self.any_to_str(owner_node.get("id"))
            if owner_name == "self" and self.current_class_name is not None:
                owner_t = self.current_class_name
        if owner_t == "":
            return ""
        for candidate in owner_candidates if len(owner_candidates) > 0 else [owner_t]:
            owner_methods = self.class_method_return_types.get(candidate, {})
            if not isinstance(owner_methods, dict):
                continue
            ret = self.normalize_type_name(self.any_to_str(owner_methods.get(attr)))
            if ret != "":
                return ret
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
            return 'pytra::std::pathlib::Path("")'
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

    def _rewrite_empty_collection_literal_for_typed_target(
        self,
        rendered_expr: str,
        value_node: Any,
        east_target_t: str,
    ) -> str:
        """空コレクション literal を既知ターゲット型へ寄せる。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        if t == "" or self.is_any_like_type(t):
            return rendered_expr
        node = self.any_to_dict_or_empty(value_node)
        if len(node) == 0:
            return rendered_expr
        kind = self._node_kind_from_dict(node)
        if kind == "List" and t.startswith("list[") and t.endswith("]"):
            if len(self._dict_stmt_list(node.get("elements"))) == 0:
                if self._is_pyobj_runtime_list_type(t):
                    return "make_object(list<object>{})"
                return f"{self._cpp_type_text(t)}{{}}"
        if kind == "Dict" and t.startswith("dict[") and t.endswith("]"):
            if len(self._dict_stmt_list(node.get("entries"))) == 0:
                return f"{self._cpp_type_text(t)}{{}}"
        if kind == "Set" and t.startswith("set[") and t.endswith("]"):
            if len(self._dict_stmt_list(node.get("elements"))) == 0:
                return f"{self._cpp_type_text(t)}{{}}"
        return rendered_expr

    def _coerce_param_signature_default(self, rendered_expr: str, east_target_t: str) -> str:
        """関数シグネチャ既定値を引数型に合わせて整形する。"""
        if rendered_expr == "":
            return rendered_expr
        t = self.normalize_type_name(east_target_t)
        out = self._rewrite_nullopt_default_for_typed_target(rendered_expr, t)
        if self._is_pyobj_ref_first_list_type(t):
            value_default = self._cpp_list_value_model_type_text(t) + "{}"
            if out == value_default:
                return f"rc_list_from_value({out})"
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
            homogeneous_tuple_item_t = self._homogeneous_tuple_ellipsis_item_type(east_target_t)
            parts: list[str] = []
            for elem in elems:
                txt = self._render_param_default_expr(elem, homogeneous_tuple_item_t if homogeneous_tuple_item_t != "" else "Any")
                if txt == "":
                    return ""
                parts.append(txt)
            if homogeneous_tuple_item_t != "":
                return self._cpp_type_text(east_target_t) + "{" + join_str_list(", ", parts) + "}"
            return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
        if kind == "List":
            elems = self.any_dict_get_list(nd, "elements")
            if len(elems) == 0:
                t = self.normalize_type_name(east_target_t)
                if t.startswith("list[") and t.endswith("]"):
                    return self._cpp_type_text(t) + "{}"
        if kind == "Dict":
            entries = self.any_dict_get_list(nd, "entries")
            if len(entries) == 0:
                t = self.normalize_type_name(east_target_t)
                if t.startswith("dict[") and t.endswith("]"):
                    return self._cpp_type_text(t) + "{}"
        if kind == "Set":
            elems = self.any_dict_get_list(nd, "elements")
            if len(elems) == 0:
                t = self.normalize_type_name(east_target_t)
                if t.startswith("set[") and t.endswith("]"):
                    return self._cpp_type_text(t) + "{}"
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
        if kind == "ForCore":
            if len(self.any_dict_get_list(stmt, "orelse")) != 0:
                return False
            iter_plan = self.any_to_dict_or_empty(stmt.get("iter_plan"))
            target_plan = self.any_to_dict_or_empty(stmt.get("target_plan"))
            if self.any_dict_get_str(iter_plan, "kind", "") != "StaticRangeForPlan":
                return False
            if self.any_dict_get_str(target_plan, "kind", "") != "NameTarget":
                return False
            return self._can_omit_braces_for_single_stmt(body_stmts)
        return default_value

    def _stmt_omit_braces_default(self, kind: str, stmt: dict[str, Any], fallback: bool = False) -> bool:
        """Prefer optimizer-provided hint and fallback to emitter local default."""
        hint_any = stmt.get("cpp_omit_braces_v1")
        if isinstance(hint_any, bool):
            return hint_any
        return self._default_stmt_omit_braces(kind, stmt, fallback)

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
        if kind == "ForRange" or kind == "For":
            raise ValueError("legacy loop node is unsupported in EAST3; lower to ForCore: " + kind)
        dispatch: dict[str, Any] = {
            "Expr": self._emit_expr_stmt,
            "Match": self._emit_match_stmt,
            "Return": self._emit_return_stmt,
            "Assign": self._emit_assign_stmt,
            "Swap": self._emit_swap_stmt,
            "AnnAssign": self._emit_annassign_stmt,
            "AugAssign": self._emit_augassign_stmt,
            "If": self._emit_if_stmt,
            "While": self._emit_while_stmt,
            "ForCore": self.emit_for_core,
            "Raise": self._emit_raise_stmt,
            "Try": self._emit_try_stmt,
            "FunctionDef": self._emit_function_stmt,
            "ClassDef": self._emit_class_stmt,
            "Pass": self._emit_pass_stmt,
            "Break": self._emit_break_stmt,
            "Continue": self._emit_continue_stmt,
            "Yield": self._emit_yield_stmt,
            "Import": self._emit_noop_stmt,
            "ImportFrom": self._emit_noop_stmt,
        }
        handler = dispatch.get(kind)
        if not callable(handler):
            if not self.dynamic_hooks_enabled:
                self.emit("/* unsupported stmt kind: " + kind + " */")
                return True
            return False
        handler(stmt)
        return True

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """1つの文ノードを C++ 文へ変換して出力する。"""
        hook_stmt = self.hook_on_emit_stmt(stmt)
        if hook_stmt:
            return
        kind = self.any_to_str(stmt.get("cpp_stmt_kind_v1"))
        if kind == "":
            kind = self._node_kind_from_dict(stmt)
        if self.hook_on_emit_stmt_kind(kind, stmt):
            return
        raise RuntimeError("cpp emitter: unsupported stmt kind: " + kind)

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
        if kind in {"Import", "ImportFrom"}:
            self._prime_import_bindings_from_stmt(stmt)
        return

    def _prime_import_bindings_from_stmt(self, stmt: dict[str, Any]) -> None:
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
                    self.import_symbols,
                    self.import_symbol_modules,
                    local_name,
                    mod,
                    name,
                )

    def _prime_import_bindings_from_body(self, body: list[dict[str, Any]]) -> None:
        for stmt in body:
            kind = self._node_kind_from_dict(stmt)
            if kind in {"Import", "ImportFrom"}:
                self._prime_import_bindings_from_stmt(stmt)

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
        exc_node = stmt.get("exc")
        if not isinstance(exc_node, dict):
            self.emit(self.syntax_text("raise_default", 'throw ::std::runtime_error("raise");'))
            return
        if self.is_name(exc_node, None):
            exc_name = self.any_to_str(self.any_to_dict_or_empty(exc_node).get("id"))
            if exc_name in {
                "Exception",
                "RuntimeError",
                "NotImplementedError",
                "ValueError",
                "TypeError",
                "IndexError",
                "KeyError",
            }:
                self.emit(
                    self.syntax_line(
                        "raise_named_exception_type",
                        'throw {exc}("{message}");',
                        {"exc": exc_name, "message": exc_name},
                    )
                )
                return
        self.emit(
            self.syntax_line(
                "raise_expr",
                "throw {exc};",
                {"exc": self.render_expr(exc_node)},
            )
        )

    def _emit_local_function_stmt(self, stmt: dict[str, Any]) -> None:
        """ローカル関数定義をラムダ変数へ lowering して出力する。"""
        name = self.any_dict_get_str(stmt, "name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        return_type_expr = stmt.get("return_type_expr")
        ret = self.cpp_signature_type(
            return_type_expr if self._is_type_expr_payload(return_type_expr) else stmt.get("return_type")
        )
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_type_exprs = self.any_to_dict_or_empty(stmt.get("arg_type_exprs"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_defaults = self.any_to_dict_or_empty(stmt.get("arg_defaults"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        params: list[str] = []
        arg_names: list[str] = []
        arg_names_for_mutation: list[str] = []
        ref_first_param_names: set[str] = set()
        borrow_param_names: set[str] = set()
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "" and raw_n in arg_types:
                arg_names.append(str(raw_n))
        arg_names_for_mutation.extend(arg_names)
        vararg_name = self.any_dict_get_str(stmt, "vararg_name", "")
        vararg_type = self.normalize_type_name(self.any_dict_get_str(stmt, "vararg_type", ""))
        vararg_type_expr = stmt.get("vararg_type_expr")
        vararg_list_t = f"list[{vararg_type}]" if vararg_name != "" and vararg_type != "" else ""
        if vararg_name != "" and vararg_list_t != "":
            arg_names_for_mutation.append(vararg_name)
        arg_type_ordered: list[str] = []
        for n in arg_names:
            t = self.normalize_type_name(self.any_to_str(arg_types.get(n)))
            t = t if t != "" else "unknown"
            arg_type_ordered.append(t)
        mutated_params = self._collect_mutated_params(body_stmts, arg_names_for_mutation)
        is_recursive_local_fn = self._stmt_list_contains_call_name(body_stmts, emitted_name)
        # ローカル関数呼び出しの coercion に使うため、現在スコープ中は登録を維持する。
        self.function_arg_types[emitted_name] = arg_type_ordered
        if vararg_list_t != "":
            self.function_vararg_list_types[emitted_name] = vararg_list_t
        self.function_mutated_param_positions[emitted_name] = {
            idx for idx, arg_name in enumerate(arg_names_for_mutation) if arg_name in mutated_params
        }
        self.function_return_types[emitted_name] = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
        fn_scope: set[str] = set()
        fn_sig_params: list[str] = []
        for n in arg_names:
            t = self.any_to_str(arg_types.get(n))
            type_expr_obj = arg_type_exprs.get(n)
            if self._is_type_expr_payload(type_expr_obj):
                ct = self.cpp_signature_type(type_expr_obj)
            else:
                imported_cpp_type = self._resolve_imported_symbol_class_cpp_type(t)
                ct = imported_cpp_type if imported_cpp_type != "" else self.cpp_signature_type(t)
            if self._is_pyobj_ref_first_list_type(t):
                ref_first_param_names.add(n)
            emitted_n = self.rename_if_reserved(n, self.reserved_words, self.rename_prefix, self.renamed_symbols)
            usage = self.any_to_str(arg_usage.get(n))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and n in mutated_params:
                usage = "mutable"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            borrow_param = self._is_cpp_class_borrow_param_type(t, ct)
            if borrow_param:
                borrow_param_names.add(n)
            borrow_ct = self._strip_rc_wrapper(ct) if borrow_param else ct
            param_txt = ""
            if by_ref and usage == "mutable":
                if ct.startswith("rc<") and not borrow_param:
                    param_txt = f"const {ct}& {emitted_n}"
                    fn_sig_params.append(f"const {ct}&")
                else:
                    use_object_param = borrow_ct == "object"
                    param_txt = f"{borrow_ct} {emitted_n}" if use_object_param else f"{borrow_ct}& {emitted_n}"
                    fn_sig_params.append(borrow_ct if use_object_param else f"{borrow_ct}&")
            elif by_ref:
                if borrow_param:
                    param_txt = f"{borrow_ct}& {emitted_n}"
                    fn_sig_params.append(f"{borrow_ct}&")
                else:
                    param_txt = f"const {borrow_ct}& {emitted_n}"
                    fn_sig_params.append(f"const {borrow_ct}&")
            else:
                param_txt = f"{borrow_ct} {emitted_n}"
                fn_sig_params.append(borrow_ct)
            if n in arg_defaults:
                default_txt = self._render_param_default_expr(arg_defaults.get(n), t)
                if default_txt != "":
                    default_txt = self._coerce_param_signature_default(default_txt, t)
                    param_txt += f" = {default_txt}"
            params.append(param_txt)
            fn_scope.add(n)
        if vararg_name != "" and vararg_list_t != "":
            ct = self.cpp_signature_type(vararg_list_t)
            if self._is_pyobj_ref_first_list_type(vararg_list_t):
                ref_first_param_names.add(vararg_name)
            emitted_vararg = self.rename_if_reserved(
                vararg_name,
                self.reserved_words,
                self.rename_prefix,
                self.renamed_symbols,
            )
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            borrow_param = self._is_cpp_class_borrow_param_type(vararg_list_t, ct)
            if borrow_param:
                borrow_param_names.add(vararg_name)
            borrow_ct = self._strip_rc_wrapper(ct) if borrow_param else ct
            usage = self.any_to_str(arg_usage.get(vararg_name))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and vararg_name in mutated_params:
                usage = "mutable"
            if by_ref and usage == "mutable":
                param_txt = f"{borrow_ct} {emitted_vararg}" if borrow_ct == "object" else f"{borrow_ct}& {emitted_vararg}"
                fn_sig_params.append(borrow_ct if borrow_ct == "object" else f"{borrow_ct}&")
            elif by_ref:
                if borrow_param:
                    param_txt = f"{borrow_ct}& {emitted_vararg}"
                    fn_sig_params.append(f"{borrow_ct}&")
                else:
                    param_txt = f"const {borrow_ct}& {emitted_vararg}"
                    fn_sig_params.append(f"const {borrow_ct}&")
            else:
                param_txt = f"{borrow_ct} {emitted_vararg}"
                fn_sig_params.append(borrow_ct)
            params.append(param_txt)
            fn_scope.add(vararg_name)
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
        prev_ret_abi = self.current_function_return_abi_mode
        prev_decl_types = self.declared_var_types
        prev_reassigned_names = self.current_function_reassigned_names
        prev_runtime_list_alias_names = self.current_function_pyobj_runtime_list_alias_names
        prev_cpp_class_borrow_params = getattr(self, "current_function_cpp_class_borrow_params", set())
        assign_counts = self._collect_assigned_name_counts(body_stmts)
        self.current_function_reassigned_names = {name for name, count in assign_counts.items() if int(count) > 1}
        self.declared_var_types = {}
        self.current_function_pyobj_runtime_list_alias_names = set(prev_runtime_list_alias_names) | set(ref_first_param_names)
        self.current_function_cpp_class_borrow_params = set(borrow_param_names)
        for an in arg_names:
            at = self.any_to_str(arg_types.get(an))
            if at != "":
                imported_cpp_type = self._resolve_imported_symbol_class_cpp_type(at)
                if imported_cpp_type != "":
                    self.declared_var_types[an] = self.normalize_type_name(imported_cpp_type)
                else:
                    self.declared_var_types[an] = self.normalize_type_name(at)
        if vararg_name != "" and vararg_list_t != "":
            self.declared_var_types[vararg_name] = vararg_list_t
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        self.current_function_return_abi_mode = "default"
        docstring = self.any_to_str(stmt.get("docstring"))
        if docstring != "":
            self.emit_block_comment(docstring)
        self.emit_stmt_list(body_stmts)
        self.current_function_return_type = prev_ret
        self.current_function_return_abi_mode = prev_ret_abi
        self.declared_var_types = prev_decl_types
        self.current_function_reassigned_names = set(prev_reassigned_names)
        self.current_function_pyobj_runtime_list_alias_names = set(prev_runtime_list_alias_names)
        self.current_function_cpp_class_borrow_params = set(prev_cpp_class_borrow_params)
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
            return
        if not value_is_dict:
            raise RuntimeError("cpp emitter: Expr without value node")
        self.emit_bridge_comment(value_node)
        rendered = self.render_expr(stmt.get("value"))
        # Guard against stray identifier-only expression statements (e.g. "r;").
        if isinstance(rendered, str) and self._is_identifier_expr(rendered):
            if rendered == "break" or rendered == "py_break":
                self.emit("break;")
            elif rendered == "continue" or rendered == "py_continue":
                self.emit("continue;")
            elif rendered == "pass":
                self.emit(";")
            else:
                self.emit(";")
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
                raise RuntimeError("cpp emitter: invalid generator return")
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
            rv = self._rewrite_empty_collection_literal_for_typed_target(rv, value_node, ret_t)
        expr_t0 = self.get_expr_type(stmt.get("value"))
        expr_t = expr_t0 if isinstance(expr_t0, str) else ""
        ret_abi_mode = self.any_to_str(getattr(self, "current_function_return_abi_mode", "default"))
        if ret_abi_mode in {"value", "value_readonly", "value_mut"}:
            list_ctor_return = self._render_value_return_list_ctor(value_node, ret_t)
            if list_ctor_return != "":
                rv = list_ctor_return
        if ret_abi_mode in {"value", "value_readonly"}:
            rv = self._render_pyobj_value_list_copy_adapter(rv, stmt.get("value"), ret_t)
        elif self._is_pyobj_ref_first_list_type(ret_t):
            rv = self._render_pyobj_alias_list_value(rv, stmt.get("value"), ret_t)
        if self.is_any_like_type(ret_t):
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

    def _render_value_return_list_ctor(self, value_node: dict[str, Any], ret_t: str) -> str:
        """`@abi(ret="value")` の `return list(x)` を value-list 返却へ正規化する。"""
        ret_norm = self.normalize_type_name(ret_t)
        if not (ret_norm.startswith("list[") and ret_norm.endswith("]")):
            return ""
        if self._node_kind_from_dict(value_node) != "Call":
            return ""
        if self.any_dict_get_str(value_node, "lowered_kind", "") != "BuiltinCall":
            return ""
        if self.any_dict_get_str(value_node, "runtime_call", "") != "list_ctor":
            return ""
        args = self.any_to_list(value_node.get("args"))
        value_cpp_t = self._cpp_list_value_model_type_text(ret_norm)
        if len(args) == 0:
            return f"{value_cpp_t}{{}}"
        if len(args) != 1:
            return ""
        arg_node = self.any_to_dict_or_empty(args[0])
        arg_txt = self.render_expr(arg_node)
        if arg_txt == "":
            return ""
        arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
        if arg_t.startswith("list[") and not self._is_pyobj_ref_first_list_type(arg_t):
            return arg_txt
        return f"{value_cpp_t}({arg_txt})"

    def _emit_yield_stmt(self, stmt: dict[str, Any]) -> None:
        if not self.current_function_is_generator or self.current_function_yield_buffer == "":
            raise RuntimeError("cpp emitter: unsupported yield outside generator")
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
        value_node = node.get("value")
        if self._node_kind_from_dict(self.any_to_dict_or_empty(value_node)) == "Subscript":
            val = self.render_lvalue(value_node)
        else:
            val = self.render_expr(value_node)
        val_ty0 = self.get_expr_type(node.get("value"))
        val_ty = val_ty0 if isinstance(val_ty0, str) else ""
        idx = self.render_expr(node.get("slice"))
        idx_t0 = self.get_expr_type(node.get("slice"))
        idx_t = idx_t0 if isinstance(idx_t0, str) else ""
        if val_ty.startswith("dict["):
            idx = self._coerce_dict_key_expr(node.get("value"), idx, node.get("slice"))
            return f"{val}[{idx}]"
        if self._uses_pyobj_ref_first_list_ops(node.get("value")):
            if (
                (not self._uses_pyobj_ref_first_list_lvalue_expr(node.get("value")))
                and self._is_pyobj_value_model_list_type(self.normalize_type_name(val_ty))
            ):
                return f"py_list_at_ref({val}, py_to<int64>({idx}))"
            return f"py_at({val}, py_to<int64>({idx}))"
        if self.is_indexable_sequence_type(val_ty):
            if self.is_any_like_type(idx_t):
                idx = f"py_to<int64>({idx})"
            return self._render_sequence_index(val, idx, node.get("slice"), val_ty)
        return f"{val}[{idx}]"

    def _render_sequence_index(
        self, value_expr: str, index_expr: str, index_node: Any, value_type: str = ""
    ) -> str:
        """list/str 添字アクセスのモード別コード生成を行う。"""
        if self.normalize_type_name(value_type) == "str":
            return f"{value_expr}[{index_expr}]"
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
            key_node_d = self.any_to_dict_or_empty(key_node)
            key_verified = bool(key_node_d.get("dict_key_verified", False))
            if self._node_kind_from_dict(key_node_d) == "Constant" and isinstance(key_node_d.get("value"), str):
                return f"str({key_expr})"
            if key_verified:
                return key_expr
            return f"str({key_expr})"
        int_key_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_key_types = {"float32", "float64"}
        if key_t in int_key_types or key_t in float_key_types or key_t == "bool":
            key_node_d = self.any_to_dict_or_empty(key_node)
            key_kind = self._node_kind_from_dict(key_node_d)
            if key_kind == "Constant":
                if self.should_skip_same_type_cast(key_expr, key_t):
                    return key_expr
                return f"{self._cpp_type_text(key_t)}({key_expr})"
        return key_expr

    # class emit helpers moved to backends.cpp.emitter.class_def.CppClassEmitter.

    # builtin runtime_call dispatch helpers moved to backends.cpp.emitter.builtin_runtime.CppBuiltinRuntimeEmitter.

    def _objectish_dict_get_effective_type(self, out_t: str, default_t: str) -> str:
        """object-dict `get` の戻り値型を既定値込みで正規化する。"""
        out_norm = self.normalize_type_name(out_t)
        default_norm = self.normalize_type_name(default_t)
        int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_out_types = {"float32", "float64"}
        if out_norm == "bool" or out_norm == "str" or out_norm in int_out_types or out_norm in float_out_types:
            return out_norm
        if out_norm.startswith("list[") or out_norm.startswith("dict["):
            return out_norm
        if out_norm in {"", "unknown", "Any", "object"}:
            if default_norm == "bool" or default_norm == "str":
                return default_norm
            if default_norm in int_out_types or default_norm in float_out_types:
                return default_norm
            if default_norm.startswith("list[") or default_norm.startswith("dict["):
                return default_norm
            return "object"
        return out_norm

    def _objectish_dict_get_default_expr_for_type(
        self,
        effective_t: str,
        default_expr: str,
        default_node: Any,
    ) -> str:
        """object-dict `get` の既定値を最終戻り値型に合わせて整形する。"""
        eff_t = self.normalize_type_name(effective_t)
        if default_expr in {"::std::nullopt", "std::nullopt"}:
            if eff_t in {"", "unknown", "Any", "object"}:
                return default_expr
            return self._none_default_expr_for_type(eff_t)
        if eff_t in {"", "unknown", "Any", "object"}:
            return self._box_any_target_value(default_expr, default_node)
        if eff_t == "str":
            return f"str({default_expr})"
        int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_out_types = {"float32", "float64"}
        if eff_t in int_out_types or eff_t in float_out_types:
            return f"py_to<{self._cpp_type_text(eff_t)}>({default_expr})"
        return default_expr

    def _objectish_dict_get_value_expr(self, value_expr: str, effective_t: str) -> str:
        """object-dict `get` の取得値を型付き戻り値へ変換する。"""
        eff_t = self.normalize_type_name(effective_t)
        if eff_t in {"", "unknown", "Any", "object"}:
            return value_expr
        if eff_t == "dict[str, object]":
            return f"obj_to_dict({value_expr})"
        if eff_t == "str":
            return f"py_to<str>({value_expr})"
        if eff_t == "bool":
            return f"py_to<bool>({value_expr})"
        int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        float_out_types = {"float32", "float64"}
        if eff_t in int_out_types or eff_t in float_out_types or eff_t.startswith("list["):
            return f"py_to<{self._cpp_type_text(eff_t)}>({value_expr})"
        return value_expr

    def _render_objectish_dict_value_or_default_stmt(
        self,
        value_expr: str,
        effective_t: str,
        typed_default: str,
    ) -> str:
        """`dict[str, object]` の値取得を decode-first / soft fallback で描画する。"""
        eff_t = self.normalize_type_name(effective_t)
        if eff_t in {"", "unknown", "Any", "object"}:
            return f"return {value_expr}; "
        if eff_t == "str":
            return f"return py_to_string({value_expr}); "
        if eff_t.startswith("list["):
            converted_expr = self._objectish_dict_get_value_expr(value_expr, eff_t)
            return f"return {converted_expr}; "
        cpp_t = self._cpp_type_text(eff_t)
        return (
            f"if (auto __dict_cast = py_object_try_cast<{cpp_t}>({value_expr})) return *__dict_cast; "
            f"return {typed_default}; "
        )

    def _render_objectish_dict_get_default_expr(
        self,
        owner_node: Any,
        owner_expr: str,
        key_node: Any,
        key_expr: str,
        default_node: Any,
        default_expr: str,
        out_t: str,
        default_t: str,
        owner_optional_object_dict: bool,
    ) -> str:
        """`dict[str, object]` / optional object-dict の `get(key, default)` を式展開する。"""
        key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
        effective_t = self._objectish_dict_get_effective_type(out_t, default_t)
        typed_default = self._objectish_dict_get_default_expr_for_type(effective_t, default_expr, default_node)
        owner_tmp = self.next_tmp("__dict")
        key_tmp = self.next_tmp("__dict_key")
        it_tmp = self.next_tmp("__dict_it")
        cpp_ret_t = "object" if self.is_any_like_type(effective_t) or effective_t == "object" else self._cpp_type_text(effective_t)
        owner_value_expr = owner_tmp if not owner_optional_object_dict else f"{owner_tmp}.value()"
        value_stmt = self._render_objectish_dict_value_or_default_stmt(f"{it_tmp}->second", effective_t, typed_default)
        guard = ""
        if owner_optional_object_dict:
            guard = f"if (!{owner_tmp}.has_value()) return {typed_default}; "
        return (
            f"([&]() -> {cpp_ret_t} {{ "
            f"auto&& {owner_tmp} = {owner_expr}; "
            f"auto {key_tmp} = {key_expr}; "
            f"{guard}"
            f"auto {it_tmp} = {owner_value_expr}.find({key_tmp}); "
            f"if ({it_tmp} == {owner_value_expr}.end()) return {typed_default}; "
            f"{value_stmt}"
            f"}}())"
        )

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
        if objectish_owner:
            return self._render_objectish_dict_get_default_expr(
                owner_node,
                owner_expr,
                key_node,
                key_expr,
                default_node,
                default_expr,
                out_t,
                default_t,
                owner_optional_object_dict,
            )
        key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
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

    def _dict_get_maybe_inner_type(self, resolved_t: str) -> str:
        """`dict.get(key)` の戻り値型から optional 内側型を取り出す。"""
        t = self.normalize_type_name(resolved_t)
        if t.startswith("optional[") and t.endswith("]"):
            return self.normalize_type_name(t[9:-1])
        if self._contains_text(t, "|"):
            parts = self.split_union(t)
            non_none: list[str] = []
            has_none = False
            for part in parts:
                p = self.normalize_type_name(part)
                if p == "None":
                    has_none = True
                elif p != "":
                    non_none.append(p)
            if has_none and len(non_none) == 1:
                return self.normalize_type_name(non_none[0])
        return ""

    def _render_dict_get_maybe_expr(
        self,
        owner_node: Any,
        key_node: Any,
        resolved_t: str,
    ) -> str:
        """`dict.get(key)` の default 省略経路を optional/value 式へ展開する。"""
        owner_expr = self.render_expr(owner_node)
        key_expr = self.render_expr(key_node)
        key_expr = self._coerce_dict_key_expr(owner_node, key_expr, key_node)
        owner_tmp = self.next_tmp("__dict")
        key_tmp = self.next_tmp("__dict_key")
        inner_t = self._dict_get_maybe_inner_type(resolved_t)
        if inner_t != "":
            cpp_inner_t = self._cpp_type_text(inner_t)
            return (
                f"([&]() -> ::std::optional<{cpp_inner_t}> {{ "
                f"auto&& {owner_tmp} = {owner_expr}; "
                f"auto {key_tmp} = {key_expr}; "
                f"return {owner_tmp}.contains({key_tmp}) ? "
                f"::std::optional<{cpp_inner_t}>({owner_tmp}.at({key_tmp})) : ::std::nullopt; "
                f"}}())"
            )
        default_expr = self._none_default_expr_for_type(resolved_t)
        return (
            f"([&]() {{ "
            f"auto&& {owner_tmp} = {owner_expr}; "
            f"auto {key_tmp} = {key_expr}; "
            f"return {owner_tmp}.contains({key_tmp}) ? {owner_tmp}.at({key_tmp}) : {default_expr}; "
            f"}}())"
        )

    def _render_dict_view_expr(
        self,
        owner_node: Any,
        resolved_t: str,
        *,
        member_name: str,
    ) -> str:
        """`dict.keys()` / `dict.values()` を explicit loop へ展開する。"""
        owner_expr = self.render_expr(owner_node)
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        if owner_t in {"", "unknown"}:
            owner_t = self.normalize_type_name(self.any_dict_get_str(self.any_to_dict_or_empty(owner_node), "resolved_type", ""))
        cpp_list_t = ""
        if owner_t.startswith("dict[") and owner_t.endswith("]"):
            owner_inner = self.split_generic(owner_t[5:-1])
            if len(owner_inner) == 2:
                item_t = self.normalize_type_name(owner_inner[0] if member_name == "first" else owner_inner[1])
                cpp_list_t = self._cpp_list_value_model_type_text(f"list[{item_t}]")
        if cpp_list_t == "":
            resolved_norm = self.normalize_type_name(resolved_t)
            if resolved_norm.startswith("list[") and resolved_norm.endswith("]"):
                cpp_list_t = self._cpp_list_value_model_type_text(resolved_norm)
            else:
                cpp_list_t = self._cpp_type_text(resolved_norm)
        owner_tmp = self.next_tmp("__dict")
        out_tmp = self.next_tmp("__out")
        return (
            f"([&]() -> {cpp_list_t} {{ "
            f"auto&& {owner_tmp} = {owner_expr}; "
            f"{cpp_list_t} {out_tmp}; "
            f"{out_tmp}.reserve({owner_tmp}.size()); "
            f"for (const auto& __kv : {owner_tmp}) {out_tmp}.push_back(__kv.{member_name}); "
            f"return {out_tmp}; "
            f"}}())"
        )

    def _render_collection_constructor_call(
        self,
        raw: str,
        expr: dict[str, Any],
        args: list[str],
        first_arg: Any,
    ) -> str | None:
        """`set/list/dict` コンストラクタ呼び出しの型依存分岐を共通化する。"""
        if raw not in {"set", "list", "dict", "deque"}:
            return None
        resolved_t = self.normalize_type_name(self.any_to_str(expr.get("resolved_type")))
        if resolved_t in {"", "unknown"}:
            resolved_t = self.normalize_type_name(self.get_expr_type(expr))
        if raw == "list" and self.any_to_str(getattr(self, "cpp_list_model", "value")) == "pyobj":
            runtime_list_ctor = resolved_t in {"", "unknown", "Any", "object"} or (
                self._is_pyobj_runtime_list_type(resolved_t)
                and (not self._is_pyobj_value_model_list_type(resolved_t))
            )
            if runtime_list_ctor:
                if len(args) == 0:
                    return "make_object(list<object>{})"
                if len(args) != 1:
                    return None
                at0 = self.get_expr_type(first_arg)
                at = at0 if isinstance(at0, str) else ""
                if at.startswith("list["):
                    return args[0]
                if at in {"Any", "object"}:
                    return f"make_object(list<object>({args[0]}))"
                return f"make_object(list<object>({args[0]}))"
        t = self.cpp_type(expr.get("resolved_type"))
        if raw == "list" and self._is_pyobj_value_model_list_type(resolved_t):
            t = self._cpp_list_value_model_type_text(resolved_t)
        if len(args) == 0:
            return f"{t}{{}}"
        if raw == "deque":
            if len(args) != 1:
                return None
            at0 = self.get_expr_type(first_arg)
            at = self.normalize_type_name(at0) if isinstance(at0, str) else ""
            if at in {"", "unknown"}:
                at = self.normalize_type_name(self.infer_rendered_arg_type(args[0], at, self.declared_var_types))
            if at in {"", "unknown"}:
                at = self.normalize_type_name(self.infer_rendered_arg_type(args[0], at, self.module_global_var_types))
            if not (
                (at.startswith("list[") and at.endswith("]"))
                or (at.startswith("tuple[") and at.endswith("]"))
                or (at.startswith("set[") and at.endswith("]"))
                or (at.startswith("deque[") and at.endswith("]"))
            ):
                return None
            src_expr = self._trim_ws(args[0])
            if src_expr == "":
                return None
            if self._is_identifier_expr(src_expr):
                return f"{t}({src_expr}.begin(), {src_expr}.end())"
            tmp_name = self.next_tmp("__deque_src")
            return (
                "([&]() { "
                f"auto {tmp_name} = {src_expr}; "
                f"return {t}({tmp_name}.begin(), {tmp_name}.end()); "
                "}())"
            )
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

    # type conversion / any-boundary helpers moved to backends.cpp.emitter.type_bridge.CppTypeBridgeEmitter.

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
        test_expr = self.render_cond(test_node)
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
            cond = self._strip_outer_parens(self.render_cond(operand_obj))
            if cond == "":
                return "true"
            return f"!({cond})"
        if op == "USub":
            operand_t0 = self.get_expr_type(operand_obj)
            operand_t = operand_t0 if isinstance(operand_t0, str) else ""
            operand_t_norm = self.normalize_type_name(operand_t)
            if operand_t_norm not in {"", "unknown", "Any", "object"} and self._has_class_method(operand_t, "__neg__"):
                owner = f"({operand})"
                if operand_t_norm in self.ref_classes and not operand.strip().startswith("*"):
                    return f"{owner}->__neg__()"
                return f"{owner}.__neg__()"
            return f"-({operand})"
        if op == "UAdd":
            return f"+({operand})"
        if op == "Invert":
            operand_t0 = self.get_expr_type(operand_obj)
            operand_t = operand_t0 if isinstance(operand_t0, str) else ""
            operand_t_norm = self.normalize_type_name(operand_t)
            if operand_t_norm not in {"", "unknown", "Any", "object"} and self._has_class_method(operand_t, "__invert__"):
                owner = f"({operand})"
                if operand_t_norm in self.ref_classes and not operand.strip().startswith("*"):
                    return f"{owner}->__invert__()"
                return f"{owner}.__invert__()"
            return f"~({operand})"
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
        empty_fastpath = self._render_typed_list_len_compare_as_empty(expr)
        if empty_fastpath != "":
            return empty_fastpath
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

    def _extract_len_target_expr(self, expr_node: Any) -> Any | None:
        """`len(x)`/`ObjLen(x)` から `x` を返す。該当しない場合は None。"""
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0:
            return None
        kind = self._node_kind_from_dict(node)
        if kind == "ObjLen":
            return node.get("value")
        if kind != "Call":
            return None
        fn = self.any_to_dict_or_empty(node.get("func"))
        if self._node_kind_from_dict(fn) != "Name":
            return None
        if self.any_dict_get_str(fn, "id", "") != "len":
            return None
        args = self.any_to_list(node.get("args"))
        if len(args) != 1:
            return None
        kws = self.any_to_list(node.get("keywords"))
        if len(kws) != 0:
            return None
        return args[0]

    def _typed_list_empty_fastpath_target(self, list_expr_node: Any) -> bool:
        """`.empty()` fastpath を適用可能な typed list 式かを判定する。"""
        node = self.any_to_dict_or_empty(list_expr_node)
        if len(node) == 0:
            return False
        list_t = self.normalize_type_name(self.get_expr_type(list_expr_node))
        if list_t in {"", "unknown"}:
            list_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        if list_t in {"", "unknown"}:
            rendered = self.render_expr(list_expr_node)
            list_t = self.normalize_type_name(self.infer_rendered_arg_type(rendered, list_t, self.declared_var_types))
        if list_t in {"", "unknown"}:
            rendered = self.render_expr(list_expr_node)
            list_t = self.normalize_type_name(self.infer_rendered_arg_type(rendered, list_t, self.module_global_var_types))
        if not (list_t.startswith("list[") and list_t.endswith("]")):
            return False
        if self._uses_pyobj_runtime_list_expr(list_expr_node):
            return False
        return True

    def _render_container_empty_expr(self, container_expr: str) -> str:
        """コンテナ式を `.empty()` 判定へ変換する。"""
        base = self._trim_ws(container_expr)
        if base == "":
            return ""
        if self._is_identifier_expr(base):
            return f"{base}.empty()"
        return f"({base}).empty()"

    def _render_container_size_expr(self, container_expr: str) -> str:
        """コンテナ式を `.size()` 参照へ変換する。"""
        base = self._trim_ws(container_expr)
        if base == "":
            return ""
        if self._is_identifier_expr(base):
            return f"{base}.size()"
        return f"({base}).size()"

    def _typed_deque_fastpath_target(self, expr_node: Any) -> bool:
        """typed deque fastpath を適用可能な式かを判定する。"""
        node = self.any_to_dict_or_empty(expr_node)
        if len(node) == 0:
            return False
        deque_t = self.normalize_type_name(self.get_expr_type(expr_node))
        if deque_t in {"", "unknown"}:
            deque_t = self.normalize_type_name(self.any_dict_get_str(node, "resolved_type", ""))
        if deque_t in {"", "unknown"}:
            rendered = self.render_expr(expr_node)
            deque_t = self.normalize_type_name(self.infer_rendered_arg_type(rendered, deque_t, self.declared_var_types))
        if deque_t in {"", "unknown"}:
            rendered = self.render_expr(expr_node)
            deque_t = self.normalize_type_name(self.infer_rendered_arg_type(rendered, deque_t, self.module_global_var_types))
        return deque_t.startswith("deque[") and deque_t.endswith("]")

    def _render_typed_list_len_compare_as_empty(self, expr: dict[str, Any]) -> str:
        """`py_len(list) ==/!= 0` を `list.empty()` へ縮退する。"""
        ops = self.any_to_str_list(expr.get("ops"))
        cmps = self._dict_stmt_list(expr.get("comparators"))
        if len(ops) != 1 or len(cmps) != 1:
            return ""
        op_name = ops[0]
        if op_name not in {"Eq", "NotEq"}:
            return ""
        left_node = expr.get("left")
        right_node = cmps[0]
        left_target = self._extract_len_target_expr(left_node)
        right_target = self._extract_len_target_expr(right_node)
        left_is_zero = self._const_int_literal(left_node) == 0
        right_is_zero = self._const_int_literal(right_node) == 0
        list_node: Any = None
        if left_target is not None and right_is_zero:
            list_node = left_target
        elif right_target is not None and left_is_zero:
            list_node = right_target
        if list_node is None or not self._typed_list_empty_fastpath_target(list_node):
            return ""
        list_expr = self.render_expr(list_node)
        if self._uses_pyobj_ref_first_list_lvalue_expr(list_node):
            list_expr = f"rc_list_ref({list_expr})"
        empty_expr = self._render_container_empty_expr(list_expr)
        if empty_expr == "":
            return ""
        if op_name == "Eq":
            return empty_expr
        return f"!({empty_expr})"

    def _render_typed_list_truthy_cond(self, expr_node: Any) -> str:
        """typed list の truthy 条件を `!list.empty()` へ縮退する。"""
        if not self._typed_list_empty_fastpath_target(expr_node):
            return ""
        body = self._strip_outer_parens(self.render_expr(expr_node))
        if body == "":
            return ""
        if self._uses_pyobj_ref_first_list_lvalue_expr(expr_node):
            body = f"rc_list_ref({body})"
        empty_expr = self._render_container_empty_expr(body)
        if empty_expr == "":
            return ""
        return f"!({empty_expr})"

    def _render_typed_list_len_expr(self, expr_node: Any) -> str:
        """typed list の `len(...)` を `.size()` へ縮退する。"""
        if not self._typed_list_empty_fastpath_target(expr_node):
            return ""
        body = self._strip_outer_parens(self.render_expr(expr_node))
        if body == "":
            return ""
        if self._uses_pyobj_ref_first_list_lvalue_expr(expr_node):
            body = f"rc_list_ref({body})"
        return self._render_container_size_expr(body)

    def _render_typed_deque_truthy_cond(self, expr_node: Any) -> str:
        """typed deque の truthy 条件を `!deque.empty()` へ縮退する。"""
        if not self._typed_deque_fastpath_target(expr_node):
            return ""
        body = self._strip_outer_parens(self.render_expr(expr_node))
        if body == "":
            return ""
        empty_expr = self._render_container_empty_expr(body)
        if empty_expr == "":
            return ""
        return f"!({empty_expr})"

    def _render_typed_deque_len_expr(self, expr_node: Any) -> str:
        """typed deque の `len(...)` を `.size()` へ縮退する。"""
        if not self._typed_deque_fastpath_target(expr_node):
            return ""
        body = self._strip_outer_parens(self.render_expr(expr_node))
        if body == "":
            return ""
        return self._render_container_size_expr(body)

    def _render_zero_arg_deque_ctor_for_target(self, value_node: Any, target_t: str) -> str:
        """`deque()` を `::std::deque<T>{}` へ直接 lower できる場合は返す。"""
        target_norm = self.normalize_type_name(target_t)
        if not (target_norm.startswith("deque[") and target_norm.endswith("]")):
            return ""
        value_d = self.any_to_dict_or_empty(value_node)
        if self._node_kind_from_dict(value_d) != "Call":
            return ""
        fn = self.any_to_dict_or_empty(value_d.get("func"))
        if self._node_kind_from_dict(fn) != "Name":
            return ""
        if self.any_dict_get_str(fn, "id", "") != "deque":
            return ""
        if len(self.any_to_list(value_d.get("args"))) != 0:
            return ""
        if len(self.any_to_list(value_d.get("keywords"))) != 0:
            return ""
        return f"{self._cpp_type_text(target_norm)}{{}}"

    def _render_single_arg_deque_ctor_for_target(self, value_node: Any, target_t: str) -> str:
        """`deque(iterable)` を typed `::std::deque<T>` range ctor へ lower できる場合は返す。"""
        target_norm = self.normalize_type_name(target_t)
        if not (target_norm.startswith("deque[") and target_norm.endswith("]")):
            return ""
        value_d = self.any_to_dict_or_empty(value_node)
        if self._node_kind_from_dict(value_d) != "Call":
            return ""
        fn = self.any_to_dict_or_empty(value_d.get("func"))
        if self._node_kind_from_dict(fn) != "Name":
            return ""
        if self.any_dict_get_str(fn, "id", "") != "deque":
            return ""
        if len(self.any_to_list(value_d.get("keywords"))) != 0:
            return ""
        arg_nodes = self.any_to_list(value_d.get("args"))
        if len(arg_nodes) != 1:
            return ""
        source_node = arg_nodes[0]
        source_expr = self._trim_ws(self.render_expr(source_node))
        if source_expr == "":
            return ""
        source_t = self.normalize_type_name(self.get_expr_type(source_node))
        if source_t in {"", "unknown"}:
            source_t = self.normalize_type_name(self.infer_rendered_arg_type(source_expr, source_t, self.declared_var_types))
        if source_t in {"", "unknown"}:
            source_t = self.normalize_type_name(self.infer_rendered_arg_type(source_expr, source_t, self.module_global_var_types))
        if not (
            (source_t.startswith("list[") and source_t.endswith("]"))
            or (source_t.startswith("tuple[") and source_t.endswith("]"))
            or (source_t.startswith("set[") and source_t.endswith("]"))
            or (source_t.startswith("deque[") and source_t.endswith("]"))
        ):
            return ""
        target_cpp_t = self._cpp_type_text(target_norm)
        if self._is_identifier_expr(source_expr):
            return f"{target_cpp_t}({source_expr}.begin(), {source_expr}.end())"
        tmp_name = self.next_tmp("__deque_src")
        return (
            "([&]() { "
            f"auto {tmp_name} = {source_expr}; "
            f"return {target_cpp_t}({tmp_name}.begin(), {tmp_name}.end()); "
            "}())"
        )

    def _box_expr_for_any(self, expr_txt: str, source_node: Any) -> str:
        """Any/object 向けの boxing を必要時のみ適用する。"""
        if self.is_boxed_object_expr(expr_txt):
            return expr_txt
        src_t = self.get_expr_type(source_node)
        # `source_node` の型が unknown でも、描画済みテキストが既知変数なら
        # 宣言型ヒントから再判定して過剰 boxing を避ける。
        src_t = self.infer_rendered_arg_type(expr_txt, src_t, self.declared_var_types)
        if self.is_any_like_type(src_t):
            rendered_name = self._strip_outer_parens(self._trim_ws(expr_txt))
            declared_t = self.normalize_type_name(self.any_to_str(self.declared_var_types.get(rendered_name, "")))
            if declared_t not in {"", "unknown"} and (not self.is_any_like_type(declared_t)):
                src_t = declared_t
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
            owner_tmp = self.next_tmp("__dict")
            key_tmp = self.next_tmp("__dict_key")
            return (
                f"([&]() {{ "
                f"auto&& {owner_tmp} = {val}; "
                f"auto {key_tmp} = {idx}; "
                f"return {owner_tmp}.at({key_tmp}); "
                f"}}())"
            )
        if val_ty in {"", "unknown"} or self.is_any_like_type(val_ty):
            if idx_is_str_key:
                return f"py_at({val}, {idx})"
            return f"py_at({val}, py_to<int64>({idx}))"
        if self._uses_pyobj_ref_first_list_ops(expr.get("value")):
            at_expr = f"py_at({val}, py_to<int64>({idx}))"
            return at_expr
        if (
            self._is_pyobj_runtime_list_type(val_ty)
            and (not self._is_pyobj_value_model_list_type(val_ty))
            and not self._expr_is_stack_list_local(expr.get("value"))
        ):
            at_expr = f"py_at({val}, py_to<int64>({idx}))"
            expr_t = self.normalize_type_name(self.get_expr_type(expr))
            if expr_t != "" and not self.is_any_like_type(expr_t) and self._can_runtime_cast_target(expr_t):
                return self._render_unbox_target_cast(at_expr, expr_t, "subscript:list")
            return at_expr
        if val_ty.startswith("tuple[") and val_ty.endswith("]"):
            homogeneous_tuple_item_t = self._homogeneous_tuple_ellipsis_item_type(val_ty)
            if homogeneous_tuple_item_t != "":
                if self.is_any_like_type(idx_ty):
                    idx = f"py_to<int64>({idx})"
                return self._render_sequence_index(val, idx, sl, f"list[{homogeneous_tuple_item_t}]")
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
            return self._render_sequence_index(val, idx, sl, val_ty)
        return f"{val}[{idx}]"

    def _render_name_expr(self, expr_d: dict[str, Any]) -> str:
        """Name ノードを C++ 式へ変換する。"""
        name_txt = dict_any_get_str(expr_d, "id")
        if name_txt != "" and not self.is_locally_declared(name_txt):
            imported = self._resolve_imported_symbol(name_txt)
            imported_module = dict_any_get_str(imported, "module")
            imported_name = dict_any_get_str(imported, "name")
            imported_module, imported_ns = self._resolve_imported_symbol_cpp_target(imported_module, imported_name)
            if imported_ns != "" and imported_name != "":
                emitted_name = self.rename_if_reserved(
                    imported_name,
                    self.reserved_words,
                    self.rename_prefix,
                    self.renamed_symbols,
                )
                return f"{imported_ns}::{emitted_name}"
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
            if getattr(self, "_is_self_hosted_parser_doc", None) is not None and self._is_self_hosted_parser_doc():
                owner_t = "object"
            else:
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
        bt = self.get_expr_type(expr_d.get("value"))
        emitted_attr = self.rename_if_reserved(attr, self.reserved_words, self.rename_prefix, self.renamed_symbols)
        if self.any_dict_get_str(expr_d, "lowered_kind", "") == "NominalAdtProjection":
            projection_meta = self.any_to_dict_or_empty(expr_d.get("nominal_adt_projection_v1"))
            variant_name = self.any_dict_get_str(projection_meta, "variant_name", "")
            field_name = self.any_dict_get_str(projection_meta, "field_name", "")
            if variant_name == "" or field_name == "":
                raise RuntimeError("cpp emitter: nominal ADT projection requires variant metadata")
            emitted_field_name = self.rename_if_reserved(
                field_name,
                self.reserved_words,
                self.rename_prefix,
                self.renamed_symbols,
            )
            ctx = f"{variant_name}.{field_name}"
            base_obj = base
            if not self.is_boxed_object_expr(base_obj):
                base_obj = f"make_object({base_obj})"
            return f'obj_to_rc_or_raise<{variant_name}>({base_obj}, "{ctx}")->' + emitted_field_name
        if base == "self" or base == "*this":
            if self.current_class_name is not None and attr in self.current_class_static_fields:
                return f"{self.current_class_name}::{emitted_attr}"
            if (
                self.current_class_name is not None
                and attr in self.class_property_names.get(self.current_class_name, set())
            ):
                return f"this->{emitted_attr}()"
            return f"this->{emitted_attr}"
        if base in self.class_base or base in self.class_method_names:
            return f"{base}::{emitted_attr}"
        if self._class_has_property_getter(bt, attr):
            if base == "self" or base == "*this":
                return f"this->{emitted_attr}()"
            if self._use_ref_class_member_arrow(base_node, base, bt):
                return f"{base}->{emitted_attr}()"
            return f"{base}.{emitted_attr}()"
        base_module_name = self.any_dict_get_str(base_ctx, "module", "")
        if base_module_name != "":
            mapped = self._lookup_module_attr_runtime_call(base_module_name, attr)
            ns = self._module_name_to_cpp_namespace(base_module_name)
            direct_module = self.render_attribute_module_access(
                base_module_name,
                emitted_attr,
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
        if bt in {"Path", "pytra::std::pathlib::Path"} and attr in {"name", "stem", "parent"}:
            return f"{base}.{emitted_attr}()"
        if (
            self.current_class_name is not None
            and attr in self.class_property_names.get(self.current_class_name, set())
            and (
                base == "self"
                or base == "*this"
                or bt in {"", "unknown"}
                or self.is_any_like_type(bt)
            )
        ):
            return f"this->{emitted_attr}()"
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
                return f"obj_to_rc_or_raise<{owner_cls}>({base_obj}, \"{ctx}\")->{emitted_attr}"
            owner_m_cls = self.class_method_owner_unique.get(attr, "")
            if owner_m_cls != "" and owner_m_cls in self.ref_classes:
                ctx = f"{owner_m_cls}.{attr}"
                base_obj = base
                if not self.is_boxed_object_expr(base_obj):
                    base_obj = f"make_object({base_obj})"
                return f"obj_to_rc_or_raise<{owner_m_cls}>({base_obj}, \"{ctx}\")->{emitted_attr}"
        owner_cls = self.class_field_owner_unique.get(attr, "")
        if (
            owner_cls != ""
            and owner_cls in self.ref_classes
            and self._type_is_ref_class(bt)
            and bt != owner_cls
        ):
            ctx = f"{owner_cls}.{attr}"
            base_obj = base
            if not self.is_boxed_object_expr(base_obj):
                base_obj = f"make_object({base_obj})"
            return f"obj_to_rc_or_raise<{owner_cls}>({base_obj}, \"{ctx}\")->{emitted_attr}"
        if self._use_ref_class_member_arrow(base_node, base, bt):
            return f"{base}->{emitted_attr}"
        return f"{base}.{emitted_attr}"

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
        self._record_non_escape_callsite(expr_d)
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
        value_node = expr_d.get("value")
        value_expr = self.render_expr(value_node)
        target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
        if target_t == "" or target_t == "unknown":
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
        if target_t == "" or target_t == "unknown" or self.is_any_like_type(target_t):
            return value_expr
        deque_ctor_expr = self._render_zero_arg_deque_ctor_for_target(value_node, target_t)
        if deque_ctor_expr != "":
            return deque_ctor_expr
        deque_ctor_expr = self._render_single_arg_deque_ctor_for_target(value_node, target_t)
        if deque_ctor_expr != "":
            return deque_ctor_expr
        if self._is_pyobj_ref_first_list_type(target_t):
            if self._uses_pyobj_ref_first_list_lvalue_expr(value_node) or self._call_expr_returns_known_pyobj_list_handle(
                value_node
            ):
                return value_expr
            if self._is_known_pyobj_value_list_source_expr(value_node):
                return f"rc_list_from_value({self._render_unwrapped_pyobj_list_source_expr(value_expr, value_node)})"
        source_t = self.normalize_type_name(self.get_expr_type(value_node))
        if source_t not in {"", "unknown"} and (not self.is_any_like_type(source_t)):
            if self._strip_rc_wrapper(source_t) == self._strip_rc_wrapper(target_t):
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
        value_node = expr_d.get("value")
        deque_truthy = self._render_typed_deque_truthy_cond(value_node)
        if deque_truthy != "":
            return deque_truthy
        value_expr = self.render_expr(value_node)
        return f"py_to<bool>({value_expr})"

    def _render_expr_kind_obj_len(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_node = expr_d.get("value")
        list_len = self._render_typed_list_len_expr(value_node)
        if list_len != "":
            return list_len
        deque_len = self._render_typed_deque_len_expr(value_node)
        if deque_len != "":
            return deque_len
        value_expr = self.render_expr(value_node)
        return f"py_len({value_expr})"

    def _render_expr_kind_obj_str(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_node = expr_d.get("value")
        value_expr = self.render_expr(value_node)
        value_t = self.normalize_type_name(self.get_expr_type(value_node))
        if value_t == "str":
            return value_expr
        if self._is_path_like_type(value_t):
            return f"{value_expr}.__str__()"
        return f"py_to_string({value_expr})"

    def _render_expr_kind_obj_iter_init(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return self._render_object_iter_or_raise_expr(value_expr)

    def _render_expr_kind_obj_iter_next(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        iter_expr = self.render_expr(expr_d.get("iter"))
        return self._render_object_iter_next_expr(iter_expr)

    def _prefer_internal_py_tid_subtype_calls(self) -> bool:
        """`pytra.built_in.type_id` 自身では subtype 判定だけ `py_tid_*` を優先する。"""
        src = self.any_dict_get_str(self.doc, "source_path", "")
        return src.endswith("src/pytra/built_in/type_id.py")

    def _render_expr_kind_obj_type_id(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        return f"py_runtime_value_type_id({value_expr})"

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
            if expr_t == "bytes":
                body = self._strip_outer_parens(self.render_expr(expr))
                if body == "":
                    return "false"
                return self.truthy_len_expr(body)
            typed_list_cond = self._render_typed_list_truthy_cond(expr)
            if typed_list_cond != "":
                return typed_list_cond
            typed_deque_cond = self._render_typed_deque_truthy_cond(expr)
            if typed_deque_cond != "":
                return typed_deque_cond
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
        kind = self.any_to_str(expr_d.get("cpp_expr_kind_v1"))
        if kind == "":
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
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                value_expr = self._render_pyobj_ref_first_list_container_item(owner_node, value_expr, value_node)
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_append_mut(rc_list_ref({owner_expr}), {value_expr})"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"py_list_append_mut(rc_list_ref({list_tmp}), {value_expr}); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                boxed_value = self._box_expr_for_any(value_expr, value_node)
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "append")
                return f"py_list_append_mut({list_ref_expr}, {boxed_value})"
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
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_extend_mut(rc_list_ref({owner_expr}), {value_expr})"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"py_list_extend_mut(rc_list_ref({list_tmp}), {value_expr}); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                boxed_value = self._box_expr_for_any(value_expr, value_node)
                extend_ctx = self._pyobj_runtime_list_bridge_context("extend")
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref(owner_expr, extend_ctx)
                return (
                    f"py_list_extend_mut("
                    f"{list_ref_expr}, "
                    f"obj_to_list_ref_or_raise({boxed_value}, \"{extend_ctx}\"))"
                )
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
            if self._typed_deque_fastpath_target(owner_node):
                if not has_index:
                    tmp_name = self.next_tmp("__deque_back")
                    return (
                        "([&]() { "
                        f"auto {tmp_name} = {owner_expr}.back(); "
                        f"{owner_expr}.pop_back(); "
                        f"return {tmp_name}; "
                        "}())"
                    )
                index_node = expr_d.get("index")
                index_expr = self.render_expr(index_node)
                if index_expr in {"", "/* none */"}:
                    tmp_name = self.next_tmp("__deque_back")
                    return (
                        "([&]() { "
                        f"auto {tmp_name} = {owner_expr}.back(); "
                        f"{owner_expr}.pop_back(); "
                        f"return {tmp_name}; "
                        "}())"
                    )
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                list_ref_expr = f"rc_list_ref({owner_expr})"
                if not has_index:
                    if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                        return f"py_list_pop_mut({list_ref_expr})"
                    list_tmp = self.next_tmp("__list")
                    return (
                        f"([&]() {{ "
                        f"auto {list_tmp} = {owner_expr}; "
                        f"return py_list_pop_mut(rc_list_ref({list_tmp})); "
                        f"}}())"
                    )
                index_node = expr_d.get("index")
                index_expr = self.render_expr(index_node)
                if index_expr in {"", "/* none */"}:
                    if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                        return f"py_list_pop_mut({list_ref_expr})"
                    list_tmp = self.next_tmp("__list")
                    return (
                        f"([&]() {{ "
                        f"auto {list_tmp} = {owner_expr}; "
                        f"return py_list_pop_mut(rc_list_ref({list_tmp})); "
                        f"}}())"
                    )
                index_expr = f"py_to<int64>({index_expr})"
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_pop_mut({list_ref_expr}, {index_expr})"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"return py_list_pop_mut(rc_list_ref({list_tmp}), {index_expr}); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "pop")
                if not has_index:
                    return f"py_list_pop_mut({list_ref_expr})"
                index_node = expr_d.get("index")
                index_expr = self.render_expr(index_node)
                if index_expr in {"", "/* none */"}:
                    return f"py_list_pop_mut({list_ref_expr})"
                return f"py_list_pop_mut({list_ref_expr}, py_to<int64>({index_expr}))"
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
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_clear_mut(rc_list_ref({owner_expr}))"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"py_list_clear_mut(rc_list_ref({list_tmp})); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "clear")
                return f"py_list_clear_mut({list_ref_expr})"
            return f"{owner_expr}.clear()"
        if kind == "ListReverse":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_reverse_mut(rc_list_ref({owner_expr}))"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"py_list_reverse_mut(rc_list_ref({list_tmp})); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "reverse")
                return f"py_list_reverse_mut({list_ref_expr})"
            return f"::std::reverse({owner_expr}.begin(), {owner_expr}.end())"
        if kind == "ListSort":
            owner_node = expr_d.get("owner")
            owner_expr = self.render_expr(owner_node)
            if self._uses_pyobj_ref_first_list_ops(owner_node):
                if self._uses_pyobj_ref_first_list_lvalue_expr(owner_node):
                    return f"py_list_sort_mut(rc_list_ref({owner_expr}))"
                list_tmp = self.next_tmp("__list")
                return (
                    f"([&]() {{ "
                    f"auto {list_tmp} = {owner_expr}; "
                    f"py_list_sort_mut(rc_list_ref({list_tmp})); "
                    f"}}())"
                )
            if self._uses_pyobj_runtime_list_expr(owner_node):
                list_ref_expr = self._render_pyobj_runtime_list_bridge_ref_for_op(owner_expr, "sort")
                return f"py_list_sort_mut({list_ref_expr})"
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
            objectish_owner = self.any_to_bool(expr_d.get("objectish_owner"))
            owner_optional_object_dict = self.any_to_bool(expr_d.get("owner_optional_object_dict"))
            if owner_expr.startswith("dict_get_node(") or owner_expr.startswith("py_dict_get_default("):
                return f"py_dict_items({owner_expr})"
            if objectish_owner or owner_optional_object_dict:
                return f"py_dict_items({owner_expr})"
            return owner_expr
        if kind == "DictKeys":
            owner_node = expr_d.get("owner")
            return self._render_dict_view_expr(
                owner_node,
                self.any_to_str(expr_d.get("resolved_type")),
                member_name="first",
            )
        if kind == "DictValues":
            owner_node = expr_d.get("owner")
            return self._render_dict_view_expr(
                owner_node,
                self.any_to_str(expr_d.get("resolved_type")),
                member_name="second",
            )
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
            resolved_t = self.normalize_type_name(self.any_dict_get_str(expr_d, "resolved_type", ""))
            return self._render_dict_get_maybe_expr(owner_node, key_node, resolved_t)
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
            window_name = "py_rfind_window" if mode == "rfind" else "py_find_window"
            args: list[str] = [owner_expr, needle_expr]
            if self.any_dict_has(expr_d, "start"):
                args.append(self.render_expr(expr_d.get("start")))
            if self.any_dict_has(expr_d, "end"):
                args.append(self.render_expr(expr_d.get("end")))
            if len(args) == 2:
                return f"{fn_name}({join_str_list(', ', args)})"
            if len(args) == 3:
                return f"{window_name}({args[0]}, {args[1]}, {args[2]}, py_len({owner_expr}))"
            return f"{window_name}({join_str_list(', ', args)})"
        if kind == "StrCharClassOp":
            value_node = expr_d.get("value")
            value_expr = self.render_expr(value_node)
            mode = self.any_dict_get_str(expr_d, "mode", "isdigit")
            value_t = self.normalize_type_name(self.get_expr_type(value_node))
            value_t = self.normalize_type_name(self.infer_rendered_arg_type(value_expr, value_t, self.declared_var_types))
            receiver_expr = value_expr
            value_node_d = self.any_to_dict_or_empty(value_node)
            if self._node_kind_from_dict(value_node_d) in {"BinOp", "BoolOp", "Compare", "IfExp"}:
                receiver_expr = f"({receiver_expr})"
            # `str` が確定している経路では同型 cast を入れない。
            if value_t != "str":
                # `Subscript` 等で object 側に落ちる経路だけ defensive cast を維持する。
                receiver_expr = f"str({receiver_expr})"
            if mode == "isalpha":
                return f"{receiver_expr}.isalpha()"
            return f"{receiver_expr}.isdigit()"
        if kind == "StrReplace":
            owner_expr = self.render_expr(expr_d.get("owner"))
            old_expr = self.render_expr(expr_d.get("old"))
            new_expr = self.render_expr(expr_d.get("new"))
            return f"py_replace({owner_expr}, {old_expr}, {new_expr})"
        if kind == "StrJoin":
            owner_expr = self.render_expr(expr_d.get("owner"))
            items_expr = self.render_expr(expr_d.get("items"))
            return f"str({owner_expr}).join({items_expr})"
        # runtime/path/type_id handlers moved to backends.cpp.emitter.runtime_expr.CppRuntimeExprEmitter.
        op_rendered = self._render_operator_family_expr(kind, expr, expr_d)
        if op_rendered != "":
            return op_rendered
        # collection literal/comprehension handlers moved to backends.cpp.emitter.collection_expr.CppCollectionExprEmitter.
        raise RuntimeError("cpp emitter: unsupported expr kind: " + kind)

    def emit_bridge_comment(self, expr: dict[str, Any] | None) -> None:
        """ランタイムブリッジ呼び出しの補助コメントを必要時に付与する。"""
        _ = expr
        return

    # type conversion / any-boundary helpers moved to backends.cpp.emitter.type_bridge.CppTypeBridgeEmitter.


_attach_cpp_emitter_helper_methods(CppEmitter)

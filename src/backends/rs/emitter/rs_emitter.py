"""EAST -> Rust transpiler."""

from __future__ import annotations

from typing import Any

from backends.rs.hooks.rs_hooks import build_rs_hooks
from backends.common.emitter.code_emitter import CodeEmitter
from toolchain.compiler.transpile_cli import make_user_error
from toolchain.frontends.type_expr import type_expr_to_string
from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id


def load_rs_profile() -> dict[str, Any]:
    """Rust 用 profile を読み込む。"""
    return CodeEmitter.load_profile_with_includes(
        "src/backends/rs/profiles/profile.json",
        anchor_file=__file__,
    )


def load_rs_hooks(profile: dict[str, Any]) -> dict[str, Any]:
    """Rust 用 hook を読み込む。"""
    _ = profile
    hooks = build_rs_hooks()
    if isinstance(hooks, dict):
        return hooks
    return {}


class RustEmitter(CodeEmitter):
    """EAST を Rust ソースへ変換する最小エミッタ。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        profile = load_rs_profile()
        hooks = load_rs_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        self.type_map = self.load_type_map(profile)
        operators = self.any_to_dict_or_empty(profile.get("operators"))
        self.bin_ops = self.any_to_str_dict_or_empty(operators.get("binop"))
        self.cmp_ops = self.any_to_str_dict_or_empty(operators.get("cmp"))
        self.aug_ops = self.any_to_str_dict_or_empty(operators.get("aug"))
        syntax = self.any_to_dict_or_empty(profile.get("syntax"))
        identifiers = self.any_to_dict_or_empty(syntax.get("identifiers"))
        self.reserved_words: set[str] = set(self.any_to_str_list(identifiers.get("reserved_words")))
        self.rename_prefix = self.any_to_str(identifiers.get("rename_prefix"))
        if self.rename_prefix == "":
            self.rename_prefix = "py_"
        self.function_return_types: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_base_map: dict[str, str] = {}
        self.class_method_defs: dict[str, dict[str, dict[str, Any]]] = {}
        self.class_field_types: dict[str, dict[str, str]] = {}
        self.class_method_mutability: dict[str, dict[str, bool]] = {}
        self.function_arg_ref_modes: dict[str, list[bool]] = {}
        self.class_method_arg_ref_modes: dict[str, dict[str, list[bool]]] = {}
        self.class_type_id_map: dict[str, int] = {}
        self.type_info_map: dict[int, tuple[int, int, int]] = {}
        self.declared_var_types: dict[str, str] = {}
        self.uses_pyany: bool = False
        self.uses_isinstance_runtime: bool = False
        self.current_fn_write_counts: dict[str, int] = {}
        self.current_fn_mutating_call_counts: dict[str, int] = {}
        self.current_ref_vars: set[str] = set()
        self.current_non_negative_vars: set[str] = set()
        self.current_positive_vars: set[str] = set()
        self.assumed_non_negative_vars: set[str] = set()
        self.assumed_positive_vars: set[str] = set()
        self.current_const_string_dict_bindings: dict[str, dict[str, str]] = {}
        self.current_hashmap_dict_names: set[str] = set()
        self.current_class_name: str = ""
        self.uses_string_helpers: bool = False
        self._stmt_list_stack: list[list[dict[str, Any]]] = []
        self._stmt_index_stack: list[int] = []

    def _is_type_expr_payload(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        kind = self.any_dict_get_str(value, "kind", "")
        return kind in {
            "NamedType",
            "DynamicType",
            "OptionalType",
            "GenericType",
            "UnionType",
            "NominalAdtType",
        }

    def _find_unsupported_general_union_type_expr(self, value: Any) -> dict[str, Any] | None:
        if not self._is_type_expr_payload(value):
            return None
        kind = self.any_dict_get_str(value, "kind", "")
        if kind == "UnionType":
            if self.any_dict_get_str(value, "union_mode", "") != "dynamic":
                return value
            for option in self.any_to_list(value.get("options")):
                found = self._find_unsupported_general_union_type_expr(option)
                if found is not None:
                    return found
            return None
        if kind == "OptionalType":
            return self._find_unsupported_general_union_type_expr(value.get("inner"))
        if kind == "GenericType":
            for arg in self.any_to_list(value.get("args")):
                found = self._find_unsupported_general_union_type_expr(arg)
                if found is not None:
                    return found
        return None

    def _reject_unsupported_general_union_type_expr(self, value: Any, *, context: str) -> None:
        if not self._is_type_expr_payload(value):
            return
        unsupported = self._find_unsupported_general_union_type_expr(value)
        if unsupported is None:
            return
        carrier = type_expr_to_string(value)
        lane = type_expr_to_string(unsupported)
        details: list[str] = [context + ": " + carrier]
        if lane != "":
            details.append("unsupported general-union lane: " + lane)
        details.append("Use Optional[T], a dynamic union, or a nominal ADT lane instead.")
        raise make_user_error(
            "unsupported_syntax",
            "Rust backend does not support general union TypeExpr yet",
            details,
        )

    def _raise_unsupported_nominal_adt_lane(self, *, lane: str, context: str) -> None:
        details = [context]
        details.append("unsupported nominal ADT lane: " + lane)
        details.append("Representative nominal ADT rollout is implemented only in the C++ backend right now.")
        raise make_user_error(
            "unsupported_syntax",
            "Rust backend does not support nominal ADT v1 lanes yet",
            details,
        )

    def emit_stmt_list(self, stmts: list[dict[str, Any]]) -> None:
        """現在ブロック文脈を保持しつつ文リストを出力する。"""
        self._stmt_list_stack.append(stmts)
        self._stmt_index_stack.append(0)
        i = 0
        while i < len(stmts):
            self._stmt_index_stack[-1] = i
            self.emit_stmt(stmts[i])
            i += 1
        self._stmt_index_stack.pop()
        self._stmt_list_stack.pop()

    def get_expr_type(self, expr: Any) -> str:
        """解決済み型 + ローカル宣言テーブルで式型を返す。"""
        t = super().get_expr_type(expr)
        if t not in {"", "unknown"}:
            return t
        node = self.any_to_dict_or_empty(expr)
        if self.any_dict_get_str(node, "kind", "") == "Name":
            name = self.any_dict_get_str(node, "id", "")
            if name in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[name])
        return t

    def _safe_name(self, name: str) -> str:
        if name == "self":
            return "self"
        if name == "_":
            return "py_underscore"
        if name == "main" and "__pytra_main" in self.function_return_types and "main" not in self.function_return_types:
            return "__pytra_main"
        return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, {})

    def _increment_name_count(self, counts: dict[str, int], name: str) -> None:
        """識別子カウントを 1 増やす。"""
        if name == "":
            return
        if name in counts:
            counts[name] += 1
            return
        counts[name] = 1

    def _collect_store_name_counts_from_target(self, target: Any, counts: dict[str, int]) -> None:
        """代入 target から束縛名書き込み回数を収集する。"""
        if isinstance(target, dict):
            kind = self.any_dict_get_str(target, "kind", "")
            if kind == "Name":
                self._increment_name_count(counts, self.any_dict_get_str(target, "id", ""))
                return
            if kind == "Attribute" or kind == "Subscript":
                self._collect_store_name_counts_from_target(target.get("value"), counts)
                return
            if kind == "Tuple" or kind == "List":
                elems_obj: Any = target.get("elements")
                elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
                for elem in elems:
                    self._collect_store_name_counts_from_target(elem, counts)
                return
            return
        if isinstance(target, list):
            for item in target:
                self._collect_store_name_counts_from_target(item, counts)

    def _collect_store_name_counts_from_target_plan(self, target_plan: Any, counts: dict[str, int]) -> None:
        """ForCore target_plan から束縛名書き込み回数を収集する。"""
        d = self.any_to_dict_or_empty(target_plan)
        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "NameTarget":
            self._increment_name_count(counts, self.any_dict_get_str(d, "id", ""))
            return
        if kind == "TupleTarget":
            for elem in self.any_to_list(d.get("elements")):
                self._collect_store_name_counts_from_target_plan(elem, counts)
            return
        if kind == "ExprTarget":
            self._collect_store_name_counts_from_target(d.get("target"), counts)

    def _collect_name_write_counts(self, stmts: list[dict[str, Any]]) -> dict[str, int]:
        """関数本文の書き込み回数（束縛名単位）を収集する。"""
        out: dict[str, int] = {}
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind == "FunctionDef" or kind == "ClassDef":
                continue
            if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
                if kind == "Assign":
                    target_any = st.get("target")
                    target_d = self.any_to_dict_or_empty(target_any)
                    if len(target_d) > 0:
                        self._collect_store_name_counts_from_target(target_d, out)
                    else:
                        targets = self._dict_stmt_list(st.get("targets"))
                        for tgt in targets:
                            self._collect_store_name_counts_from_target(tgt, out)
                else:
                    self._collect_store_name_counts_from_target(st.get("target"), out)
                continue
            if kind == "Swap":
                self._collect_store_name_counts_from_target(st.get("left"), out)
                self._collect_store_name_counts_from_target(st.get("right"), out)
                continue
            if kind == "For" or kind == "ForRange":
                self._collect_store_name_counts_from_target(st.get("target"), out)
                body_obj: Any = st.get("body")
                body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj: Any = st.get("orelse")
                orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "ForCore":
                self._collect_store_name_counts_from_target_plan(st.get("target_plan"), out)
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "If" or kind == "While":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "Try":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                final_obj = st.get("finalbody")
                finalbody = final_obj if isinstance(final_obj, list) else []
                final_counts = self._collect_name_write_counts(finalbody)
                for name, cnt in final_counts.items():
                    out[name] = out.get(name, 0) + cnt
                handlers_obj: Any = st.get("handlers")
                handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
                for handler in handlers:
                    if not isinstance(handler, dict):
                        continue
                    h_name = handler.get("name")
                    if isinstance(h_name, str) and h_name != "":
                        self._increment_name_count(out, h_name)
                    h_body_obj: Any = handler.get("body")
                    h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                    h_counts = self._collect_name_write_counts(h_body)
                    for name, cnt in h_counts.items():
                        out[name] = out.get(name, 0) + cnt
        return out

    def _expr_mentions_name(self, node: Any, name: str) -> bool:
        """式/文サブツリーに `Name(name)` が含まれるかを返す。"""
        if isinstance(node, dict):
            if self.any_dict_get_str(node, "kind", "") == "Name" and self.any_dict_get_str(node, "id", "") == name:
                return True
            for _k, v in node.items():
                if self._expr_mentions_name(v, name):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._expr_mentions_name(item, name):
                    return True
        return False

    def _current_stmt_uses_name_later(self, name: str) -> bool:
        """現在ブロックの後続文で `name` が参照される場合に True。"""
        if name == "":
            return False
        if len(self._stmt_list_stack) == 0 or len(self._stmt_index_stack) == 0:
            return False
        stmts = self._stmt_list_stack[-1]
        idx = self._stmt_index_stack[-1]
        j = idx + 1
        while j < len(stmts):
            if self._expr_mentions_name(stmts[j], name):
                return True
            j += 1
        return False

    def _mutating_method_names(self) -> set[str]:
        return {
            "append",
            "pop",
            "clear",
            "insert",
            "remove",
            "sort",
            "reverse",
            "extend",
            "update",
            "setdefault",
            "add",
            "discard",
        }

    def _all_mutating_class_method_names(self) -> set[str]:
        """既知クラスで `&mut self` が必要なメソッド名集合を返す。"""
        out: set[str] = set()
        for _cls, method_map in self.class_method_mutability.items():
            for name, is_mut in method_map.items():
                if is_mut:
                    out.add(name)
        return out

    def _should_pass_arg_by_ref_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if t == "str" or t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        if t in self.class_names:
            return True
        return False

    def _should_pass_method_arg_by_ref_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if t == "str" or t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        return False

    def _borrowed_arg_type_text(self, east_type: str, rust_type: str, *, allow_trait_impl: bool) -> str:
        arg_norm = self.normalize_type_name(east_type)
        if allow_trait_impl and arg_norm in self.class_names and self._is_inheritance_class(arg_norm):
            return "&impl " + self._class_trait_name(arg_norm)
        if arg_norm == "str":
            return "&str"
        if arg_norm.startswith("list["):
            inner = self.type_generic_args(arg_norm, "list")
            if len(inner) == 1:
                return "&[" + self._rust_type(inner[0]) + "]"
        return "&" + rust_type

    def _dict_key_supports_hashmap(self, key_t: str) -> bool:
        key_norm = self.normalize_type_name(key_t)
        return key_norm in {"str", "int64", "bool"}

    def _can_hashmap_backend(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if not t.startswith("dict["):
            return False
        key_t, _val_t = self._dict_key_value_types(t)
        if key_t == "":
            return False
        return self._dict_key_supports_hashmap(key_t)

    def _rust_type_for_binding(self, name_raw: str, east_type: str) -> str:
        t = self.normalize_type_name(east_type)
        base = self._rust_type(t)
        if t.startswith("dict[") and name_raw in self.current_hashmap_dict_names and self._can_hashmap_backend(t):
            return base.replace("::std::collections::BTreeMap<", "::std::collections::HashMap<")
        return base

    def _collect_local_dict_decl_types(self, stmts: list[dict[str, Any]], out: dict[str, str]) -> None:
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind == "AnnAssign":
                target = self.any_to_dict_or_empty(st.get("target"))
                if self.any_dict_get_str(target, "kind", "") == "Name":
                    name_raw = self.any_dict_get_str(target, "id", "")
                    ann = self.any_to_str(st.get("annotation"))
                    decl_t = self.any_to_str(st.get("decl_type"))
                    value_t = self.normalize_type_name(self.get_expr_type(st.get("value")))
                    t = self.normalize_type_name(ann if ann != "" else decl_t)
                    if t == "":
                        t = value_t
                    if self._can_hashmap_backend(t):
                        out[name_raw] = t
                continue
            if kind == "Assign":
                target = self.primary_assign_target(st)
                target_d = self.any_to_dict_or_empty(target)
                if self.any_dict_get_str(target_d, "kind", "") == "Name":
                    name_raw = self.any_dict_get_str(target_d, "id", "")
                    t = self.normalize_type_name(self.get_expr_type(st.get("value")))
                    if self._can_hashmap_backend(t):
                        out[name_raw] = t
                continue
            nested: list[dict[str, Any]] = []
            if kind in {"If", "While", "For", "ForRange", "ForCore"}:
                nested.extend(self._dict_stmt_list(st.get("body")))
                nested.extend(self._dict_stmt_list(st.get("orelse")))
            elif kind == "Try":
                nested.extend(self._dict_stmt_list(st.get("body")))
                nested.extend(self._dict_stmt_list(st.get("orelse")))
                nested.extend(self._dict_stmt_list(st.get("finalbody")))
                for h in self.any_to_list(st.get("handlers")):
                    nested.extend(self._dict_stmt_list(self.any_to_dict_or_empty(h).get("body")))
            if len(nested) > 0:
                self._collect_local_dict_decl_types(nested, out)

    def _collect_dict_order_sensitive_names_from_expr(self, node: Any, dict_types: dict[str, str], out: set[str]) -> None:
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                mark_call_args_unsafe = False
                if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                    attr = self.any_dict_get_str(fn, "attr", "")
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    if self.any_dict_get_str(owner, "kind", "") == "Name":
                        owner_name = self.any_dict_get_str(owner, "id", "")
                        if owner_name in dict_types and attr in {"items", "keys", "values"}:
                            out.add(owner_name)
                    elif attr not in {"get", "insert", "contains_key", "len", "clear", "remove", "pop", "update"}:
                        mark_call_args_unsafe = True
                elif self.any_dict_get_str(fn, "kind", "") == "Name":
                    fn_name = self.any_dict_get_str(fn, "id", "")
                    if fn_name not in self.function_return_types and fn_name not in {
                        "str",
                        "int",
                        "float",
                        "bool",
                        "len",
                        "max",
                        "min",
                        "print",
                        "range",
                        "enumerate",
                        "isinstance",
                        "bytearray",
                        "bytes",
                        "list",
                        "dict",
                        "set",
                        "tuple",
                        "py_assert_stdout",
                    }:
                        mark_call_args_unsafe = True
                else:
                    mark_call_args_unsafe = True
                if mark_call_args_unsafe:
                    for arg_node in self.any_to_list(node.get("args")):
                        arg_d = self.any_to_dict_or_empty(arg_node)
                        if self.any_dict_get_str(arg_d, "kind", "") == "Name":
                            arg_name = self.any_dict_get_str(arg_d, "id", "")
                            if arg_name in dict_types:
                                out.add(arg_name)
            if kind == "Name":
                return
            for _k, v in node.items():
                self._collect_dict_order_sensitive_names_from_expr(v, dict_types, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_dict_order_sensitive_names_from_expr(item, dict_types, out)

    def _collect_dict_order_sensitive_names(self, stmts: list[dict[str, Any]], dict_types: dict[str, str], out: set[str]) -> None:
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind in {"For", "ForCore"}:
                iter_node = st.get("iter") if kind == "For" else self.any_to_dict_or_empty(st.get("iter_plan")).get("iter_expr")
                iter_d = self.any_to_dict_or_empty(iter_node)
                if self.any_dict_get_str(iter_d, "kind", "") == "Name":
                    iter_name = self.any_dict_get_str(iter_d, "id", "")
                    if iter_name in dict_types:
                        out.add(iter_name)
            self._collect_dict_order_sensitive_names_from_expr(st, dict_types, out)

    def _analyze_function_hashmap_dict_names(self, fn: dict[str, Any], *, in_class: str | None) -> set[str]:
        _ = in_class
        out: set[str] = set()
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        dict_types: dict[str, str] = {}
        for arg_name in arg_order:
            if arg_name == "self":
                continue
            t = self.normalize_type_name(self.any_to_str(arg_types.get(arg_name)))
            if self._can_hashmap_backend(t):
                dict_types[arg_name] = t
        body = self._dict_stmt_list(fn.get("body"))
        self._collect_local_dict_decl_types(body, dict_types)
        for name_raw in dict_types.keys():
            out.add(name_raw)
        if len(out) == 0:
            return out
        sensitive: set[str] = set()
        self._collect_dict_order_sensitive_names(body, dict_types, sensitive)
        for name_raw in list(out):
            if name_raw in sensitive:
                out.discard(name_raw)
        return out

    def _compute_function_arg_ref_modes(self, fn: dict[str, Any], *, for_method: bool = False) -> list[bool]:
        """関数の各引数を `&T` で受けるべきかを返す（top-level 用）。"""
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(fn.get("arg_usage"))
        body = self._dict_stmt_list(fn.get("body"))
        write_counts = self._collect_name_write_counts(body)
        mut_call_counts = self._collect_mutating_receiver_name_counts(body)
        pass_by_ref_pred = self._should_pass_method_arg_by_ref_type if for_method else self._should_pass_arg_by_ref_type
        modes: list[bool] = []
        for arg_name in arg_order:
            if arg_name == "self":
                continue
            usage = self.any_to_str(arg_usage.get(arg_name))
            write_count = write_counts.get(arg_name, 0)
            mut_call_count = mut_call_counts.get(arg_name, 0)
            is_mut = usage == "reassigned" or usage == "mutable" or usage == "write" or write_count > 0 or mut_call_count > 0
            modes.append((not is_mut) and pass_by_ref_pred(self.any_to_str(arg_types.get(arg_name))))
        return modes

    def _receiver_root_name(self, node: dict[str, Any]) -> str:
        """Attribute 連鎖の最左端 Name を返す。見つからなければ空文字。"""
        cur = self.any_to_dict_or_empty(node)
        while self.any_dict_get_str(cur, "kind", "") == "Attribute":
            cur = self.any_to_dict_or_empty(cur.get("value"))
        if self.any_dict_get_str(cur, "kind", "") == "Name":
            return self.any_dict_get_str(cur, "id", "")
        return ""

    def _collect_self_called_methods_from_expr(self, node: Any, out: set[str]) -> None:
        """式木から `self.method(...)` 呼び出しの method 名を収集する。"""
        if isinstance(node, dict):
            if self.any_dict_get_str(node, "kind", "") == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    if self.any_dict_get_str(owner, "kind", "") == "Name" and self.any_dict_get_str(owner, "id", "") == "self":
                        attr = self.any_dict_get_str(fn, "attr", "")
                        if attr != "":
                            out.add(attr)
            for _k, v in node.items():
                self._collect_self_called_methods_from_expr(v, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_self_called_methods_from_expr(item, out)

    def _collect_self_called_methods(self, stmts: list[dict[str, Any]]) -> set[str]:
        """文リスト中の `self.method(...)` 呼び出し集合を返す。"""
        out: set[str] = set()
        for st in stmts:
            self._collect_self_called_methods_from_expr(st, out)
        return out

    def _analyze_class_method_mutability(self, members: list[dict[str, Any]]) -> dict[str, bool]:
        """クラス内メソッドの `self` 可変性を固定点で推定する。"""
        method_bodies: dict[str, list[dict[str, Any]]] = {}
        mut_map: dict[str, bool] = {}
        deps: dict[str, set[str]] = {}
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "":
                continue
            body = self._dict_stmt_list(member.get("body"))
            method_bodies[name] = body
            writes = self._collect_name_write_counts(body)
            mut_calls = self._collect_mutating_receiver_name_counts(body)
            mut_map[name] = writes.get("self", 0) > 0 or mut_calls.get("self", 0) > 0
            deps[name] = self._collect_self_called_methods(body)

        changed = True
        while changed:
            changed = False
            for name, called in deps.items():
                if mut_map.get(name, False):
                    continue
                for callee in called:
                    if mut_map.get(callee, False):
                        mut_map[name] = True
                        changed = True
                        break
        return mut_map

    def _count_self_calls_to_mut_methods(self, stmts: list[dict[str, Any]], method_mut_map: dict[str, bool]) -> int:
        """本文中の `self.<mut_method>()` 呼び出し数を返す。"""
        called = self._collect_self_called_methods(stmts)
        count = 0
        for name in called:
            if method_mut_map.get(name, False):
                count += 1
        return count

    def _collect_mutating_call_counts_from_expr(self, node: Any, out: dict[str, int]) -> None:
        """破壊的メソッド呼び出し receiver 名の出現回数を収集する。"""
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                    attr = self.any_dict_get_str(fn, "attr", "")
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    owner_name = self._receiver_root_name(owner)
                    if owner_name != "":
                        if attr in self._mutating_method_names():
                            self._increment_name_count(out, owner_name)
                        if attr in self._all_mutating_class_method_names():
                            self._increment_name_count(out, owner_name)
                        root_owner: dict[str, Any] = {"kind": "Name", "id": owner_name}
                        owner_t = self.normalize_type_name(self.get_expr_type(root_owner))
                        if owner_t in self.class_names:
                            self._increment_name_count(out, owner_name)
            for _k, v in node.items():
                self._collect_mutating_call_counts_from_expr(v, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_mutating_call_counts_from_expr(item, out)

    def _collect_mutating_receiver_name_counts(self, stmts: list[dict[str, Any]]) -> dict[str, int]:
        """関数本文から破壊的メソッド呼び出し receiver 名を収集する。"""
        out: dict[str, int] = {}
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind == "FunctionDef" or kind == "ClassDef":
                continue
            if kind == "If" or kind == "While" or kind == "For" or kind == "ForRange" or kind == "ForCore":
                self._collect_mutating_call_counts_from_expr(st.get("test"), out)
                self._collect_mutating_call_counts_from_expr(st.get("iter"), out)
                self._collect_mutating_call_counts_from_expr(st.get("iter_plan"), out)
                self._collect_mutating_call_counts_from_expr(st.get("start"), out)
                self._collect_mutating_call_counts_from_expr(st.get("stop"), out)
                self._collect_mutating_call_counts_from_expr(st.get("step"), out)
                body_obj: Any = st.get("body")
                body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_mutating_receiver_name_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj: Any = st.get("orelse")
                orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_mutating_receiver_name_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "Try":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_mutating_receiver_name_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_mutating_receiver_name_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                final_obj = st.get("finalbody")
                finalbody = final_obj if isinstance(final_obj, list) else []
                final_counts = self._collect_mutating_receiver_name_counts(finalbody)
                for name, cnt in final_counts.items():
                    out[name] = out.get(name, 0) + cnt
                handlers_obj: Any = st.get("handlers")
                handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
                for handler in handlers:
                    if not isinstance(handler, dict):
                        continue
                    h_body_obj: Any = handler.get("body")
                    h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                    h_counts = self._collect_mutating_receiver_name_counts(h_body)
                    for name, cnt in h_counts.items():
                        out[name] = out.get(name, 0) + cnt
                continue
            self._collect_mutating_call_counts_from_expr(st, out)
        return out

    def _should_declare_mut(self, name_raw: str, has_init_write: bool) -> bool:
        """現在関数内の書き込み情報から `let mut` 必要性を判定する。"""
        write_count = self.current_fn_write_counts.get(name_raw, 0)
        mut_call_count = self.current_fn_mutating_call_counts.get(name_raw, 0)
        threshold = 1 if has_init_write else 0
        if write_count > threshold:
            return True
        if mut_call_count > 0:
            return True
        return False

    def _doc_mentions_any(self, node: Any) -> bool:
        """EAST 全体に `Any/object` 型が含まれるかを粗く判定する。"""
        if isinstance(node, dict):
            for _k, v in node.items():
                if self._doc_mentions_any(v):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._doc_mentions_any(item):
                    return True
            return False
        if isinstance(node, str):
            t = self.normalize_type_name(node)
            if t == "Any" or t == "object":
                return True
            if self._contains_text(t, "Any") or self._contains_text(t, "object"):
                return True
        return False

    def _doc_mentions_isinstance(self, node: Any) -> bool:
        """EAST 全体に type_id runtime helper が必要なノードが含まれるかを判定する。"""
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind in {"IsInstance", "IsSubtype", "IsSubclass", "ObjTypeId"}:
                return True
            if kind == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Name":
                    fn_name = self.any_dict_get_str(fn, "id", "")
                    if fn_name in {
                        "isinstance",
                        "py_isinstance",
                        "py_tid_isinstance",
                        "py_issubclass",
                        "py_tid_issubclass",
                        "py_is_subtype",
                        "py_tid_is_subtype",
                        "py_runtime_type_id",
                        "py_tid_runtime_type_id",
                    }:
                        return True
            for _k, v in node.items():
                if self._doc_mentions_isinstance(v):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._doc_mentions_isinstance(item):
                    return True
            return False
        return False

    def _builtin_type_id_expr(self, type_name: str) -> str:
        """型名を Rust runtime の `PYTRA_TID_*` 定数式へ変換する。"""
        t = self.normalize_type_name(type_name)
        if t == "None":
            return "PYTRA_TID_NONE"
        if t == "bool":
            return "PYTRA_TID_BOOL"
        if t == "int" or self._is_int_type(t):
            return "PYTRA_TID_INT"
        if t == "float" or self._is_float_type(t):
            return "PYTRA_TID_FLOAT"
        if t == "str":
            return "PYTRA_TID_STR"
        if t == "bytes" or t == "bytearray" or t.startswith("list[") or t == "list":
            return "PYTRA_TID_LIST"
        if t.startswith("dict[") or t == "dict":
            return "PYTRA_TID_DICT"
        if t.startswith("set[") or t == "set":
            return "PYTRA_TID_SET"
        if t == "object":
            return "PYTRA_TID_OBJECT"
        if t in self.class_names:
            return self._safe_name(t) + "::PYTRA_TYPE_ID"
        return ""

    def _base_type_id_for_name(self, base_name: str) -> int:
        """基底型名を type_id へ変換する（未知は object）。"""
        expr = self._builtin_type_id_expr(base_name)
        if expr == "PYTRA_TID_NONE":
            return 0
        if expr == "PYTRA_TID_BOOL":
            return 1
        if expr == "PYTRA_TID_INT":
            return 2
        if expr == "PYTRA_TID_FLOAT":
            return 3
        if expr == "PYTRA_TID_STR":
            return 4
        if expr == "PYTRA_TID_LIST":
            return 5
        if expr == "PYTRA_TID_DICT":
            return 6
        if expr == "PYTRA_TID_SET":
            return 7
        if expr == "PYTRA_TID_OBJECT":
            return 8
        normalized = self.normalize_type_name(base_name)
        if normalized in self.class_type_id_map:
            return self.class_type_id_map[normalized]
        return 8

    def _prepare_type_id_table(self) -> None:
        """Rust 出力に埋め込む `type_id` 範囲テーブルを計算する。"""
        self.class_type_id_map = {}
        self.type_info_map = {}

        type_ids: list[int] = []
        type_base: dict[int, int] = {}
        type_children: dict[int, list[int]] = {}

        def _register(tid: int, base_tid: int) -> None:
            if tid not in type_ids:
                type_ids.append(tid)
            prev_base = type_base.get(tid, -1)
            if prev_base >= 0 and prev_base in type_children:
                prev_children = type_children[prev_base]
                if tid in prev_children:
                    prev_children.remove(tid)
            type_base[tid] = base_tid
            if tid not in type_children:
                type_children[tid] = []
            if base_tid < 0:
                return
            if base_tid not in type_children:
                type_children[base_tid] = []
            children = type_children[base_tid]
            if tid not in children:
                children.append(tid)

        # built-in hierarchy: object <- {int(bool), float, str, list, dict, set}
        _register(0, -1)
        _register(8, -1)
        _register(2, 8)
        _register(1, 2)
        _register(3, 8)
        _register(4, 8)
        _register(5, 8)
        _register(6, 8)
        _register(7, 8)

        next_user_tid = 1000
        for class_name in sorted(self.class_names):
            while next_user_tid in type_base:
                next_user_tid += 1
            self.class_type_id_map[class_name] = next_user_tid
            next_user_tid += 1

        for class_name in sorted(self.class_names):
            tid = self.class_type_id_map[class_name]
            base_name = self.normalize_type_name(self.class_base_map.get(class_name, ""))
            if base_name == "":
                base_name = "object"
            _register(tid, self._base_type_id_for_name(base_name))

        def _sorted_ints(items: list[int]) -> list[int]:
            out = list(items)
            out.sort()
            return out

        def _collect_roots() -> list[int]:
            roots: list[int] = []
            for tid in type_ids:
                base_tid = type_base.get(tid, -1)
                if base_tid < 0 or base_tid not in type_base:
                    roots.append(tid)
            return _sorted_ints(roots)

        type_order: dict[int, int] = {}
        type_min: dict[int, int] = {}
        type_max: dict[int, int] = {}

        def _assign_dfs(tid: int, next_order: int) -> int:
            type_order[tid] = next_order
            type_min[tid] = next_order
            cur = next_order + 1
            for child_tid in _sorted_ints(type_children.get(tid, [])):
                cur = _assign_dfs(child_tid, cur)
            type_max[tid] = cur - 1
            return cur

        next_order = 0
        for root_tid in _collect_roots():
            next_order = _assign_dfs(root_tid, next_order)
        for tid in _sorted_ints(type_ids):
            if tid not in type_order:
                next_order = _assign_dfs(tid, next_order)

        for tid in _sorted_ints(type_ids):
            self.type_info_map[tid] = (
                type_order[tid],
                type_min[tid],
                type_max[tid],
            )

    def _emit_isinstance_runtime_helpers(self) -> None:
        """`isinstance` 用 `type_id` runtime helper を出力する。"""
        self.emit("const PYTRA_TID_NONE: i64 = 0;")
        self.emit("const PYTRA_TID_BOOL: i64 = 1;")
        self.emit("const PYTRA_TID_INT: i64 = 2;")
        self.emit("const PYTRA_TID_FLOAT: i64 = 3;")
        self.emit("const PYTRA_TID_STR: i64 = 4;")
        self.emit("const PYTRA_TID_LIST: i64 = 5;")
        self.emit("const PYTRA_TID_DICT: i64 = 6;")
        self.emit("const PYTRA_TID_SET: i64 = 7;")
        self.emit("const PYTRA_TID_OBJECT: i64 = 8;")
        self.emit("")
        self.emit("#[derive(Clone, Copy)]")
        self.emit("struct PyTypeInfo {")
        self.indent += 1
        self.emit("order: i64,")
        self.emit("min: i64,")
        self.emit("max: i64,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_type_info(type_id: i64) -> Option<PyTypeInfo> {")
        self.indent += 1
        self.emit("match type_id {")
        self.indent += 1
        for tid in sorted(self.type_info_map.keys()):
            order, min_id, max_id = self.type_info_map[tid]
            self.emit(
                f"{tid} => Some(PyTypeInfo {{ order: {order}, min: {min_id}, max: {max_id} }}),"
            )
        self.emit("_ => None,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyRuntimeTypeId {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for bool {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_BOOL")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for i64 {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_INT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for f64 {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_FLOAT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for String {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_STR")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T> PyRuntimeTypeId for Vec<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_LIST")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<K: Ord, V> PyRuntimeTypeId for ::std::collections::BTreeMap<K, V> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_DICT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T: Ord> PyRuntimeTypeId for ::std::collections::BTreeSet<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_SET")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T: PyRuntimeTypeId> PyRuntimeTypeId for Option<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("Some(v) => v.py_runtime_type_id(),")
        self.emit("None => PYTRA_TID_NONE,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        if self.uses_pyany:
            self.emit("")
            self.emit("impl PyRuntimeTypeId for PyAny {")
            self.indent += 1
            self.emit("fn py_runtime_type_id(&self) -> i64 {")
            self.indent += 1
            self.emit("match self {")
            self.indent += 1
            self.emit("PyAny::Int(_) => PYTRA_TID_INT,")
            self.emit("PyAny::Float(_) => PYTRA_TID_FLOAT,")
            self.emit("PyAny::Bool(_) => PYTRA_TID_BOOL,")
            self.emit("PyAny::Str(_) => PYTRA_TID_STR,")
            self.emit("PyAny::List(_) => PYTRA_TID_LIST,")
            self.emit("PyAny::Dict(_) => PYTRA_TID_DICT,")
            self.emit("PyAny::Set(_) => PYTRA_TID_SET,")
            self.emit("PyAny::None => PYTRA_TID_NONE,")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")
        self.emit("")
        self.emit("fn py_runtime_type_id<T: PyRuntimeTypeId>(value: &T) -> i64 {")
        self.indent += 1
        self.emit("value.py_runtime_type_id()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("let actual = match py_type_info(actual_type_id) {")
        self.indent += 1
        self.emit("Some(info) => info,")
        self.emit("None => return false,")
        self.indent -= 1
        self.emit("};")
        self.emit("let expected = match py_type_info(expected_type_id) {")
        self.indent += 1
        self.emit("Some(info) => info,")
        self.emit("None => return false,")
        self.indent -= 1
        self.emit("};")
        self.emit("expected.min <= actual.order && actual.order <= expected.max")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("py_is_subtype(actual_type_id, expected_type_id)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_isinstance<T: PyRuntimeTypeId>(value: &T, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("py_is_subtype(py_runtime_type_id(value), expected_type_id)")
        self.indent -= 1
        self.emit("}")

    def _is_any_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t == "Any" or t == "object"

    def _is_int_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}

    def _is_float_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"float32", "float64"}

    def _list_elem_type(self, east_type: str) -> str:
        t = self.normalize_type_name(east_type)
        if not t.startswith("list[") or not t.endswith("]"):
            return ""
        parts = self.split_generic(t[5:-1].strip())
        if len(parts) != 1:
            return ""
        return self.normalize_type_name(parts[0])

    def _can_borrow_iter_node(self, iter_node: Any) -> bool:
        """for/enumerate の反復対象を借用で回して良いかを保守的に判定する。"""
        d = self.any_to_dict_or_empty(iter_node)
        if self.any_dict_get_str(d, "kind", "") != "Name":
            return True
        name_raw = self.any_dict_get_str(d, "id", "")
        if name_raw == "":
            return False
        write_count = self.current_fn_write_counts.get(name_raw, 0)
        mut_call_count = self.current_fn_mutating_call_counts.get(name_raw, 0)
        return write_count == 0 and mut_call_count == 0

    def _render_list_iter_expr(self, list_expr: str, list_type: str, can_borrow: bool) -> str:
        """list 反復の Rust 式を生成する（必要最小限の clone/copy に寄せる）。"""
        elem_t = self._list_elem_type(list_type)
        if self._is_copy_type(elem_t):
            return "(" + list_expr + ").iter().copied()"
        if can_borrow and (elem_t in self.class_names or elem_t == "str"):
            return "(" + list_expr + ").iter()"
        return "(" + list_expr + ").iter().cloned()"

    def _is_copy_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if self._is_int_type(t):
            return True
        if self._is_float_type(t):
            return True
        return t in {"bool", "char", "int", "float", "usize", "isize"}

    def _expr_is_positive(self, node: Any) -> bool:
        d = self.any_to_dict_or_empty(node)
        if len(d) == 0:
            return False
        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "Constant":
            value_any = d.get("value")
            if isinstance(value_any, bool):
                return False
            if isinstance(value_any, int):
                return value_any > 0
            if isinstance(value_any, float):
                return value_any > 0.0
            return False
        if kind == "Name":
            name = self.any_dict_get_str(d, "id", "")
            return name in self.current_positive_vars or name in self.assumed_positive_vars
        if kind == "Call":
            fn = self.any_to_dict_or_empty(d.get("func"))
            if self.any_dict_get_str(fn, "kind", "") == "Name":
                fn_name = self.any_dict_get_str(fn, "id", "")
                args = self.any_to_list(d.get("args"))
                if (fn_name == "int" or fn_name == "float") and len(args) > 0:
                    return self._expr_is_positive(args[0])
            return False
        if kind == "BinOp":
            op = self.any_dict_get_str(d, "op", "")
            left = d.get("left")
            right = d.get("right")
            if op == "Add":
                return self._expr_is_positive(left) and self._expr_is_non_negative(right)
            if op == "Mult":
                return self._expr_is_positive(left) and self._expr_is_positive(right)
            if op == "FloorDiv" or op == "Div":
                return self._expr_is_positive(left) and self._expr_is_positive(right)
        return False

    def _expr_is_non_negative(self, node: Any) -> bool:
        d = self.any_to_dict_or_empty(node)
        if len(d) == 0:
            return False
        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "Constant":
            value_any = d.get("value")
            if isinstance(value_any, bool):
                return False
            if isinstance(value_any, int):
                return value_any >= 0
            if isinstance(value_any, float):
                return value_any >= 0.0
            return False
        if kind == "Name":
            name = self.any_dict_get_str(d, "id", "")
            return name in self.current_non_negative_vars or name in self.assumed_non_negative_vars
        if kind == "Call":
            fn = self.any_to_dict_or_empty(d.get("func"))
            if self.any_dict_get_str(fn, "kind", "") == "Name":
                fn_name = self.any_dict_get_str(fn, "id", "")
                args = self.any_to_list(d.get("args"))
                if (fn_name == "int" or fn_name == "float") and len(args) > 0:
                    return self._expr_is_non_negative(args[0])
            return False
        if kind == "UnaryOp":
            op = self.any_dict_get_str(d, "op", "")
            if op == "UAdd":
                return self._expr_is_non_negative(d.get("operand"))
            return False
        if kind == "BinOp":
            op = self.any_dict_get_str(d, "op", "")
            left = d.get("left")
            right = d.get("right")
            if op == "Add":
                return self._expr_is_non_negative(left) and self._expr_is_non_negative(right)
            if op == "Sub":
                right_lit = self._const_int_literal(right)
                if right_lit == 0:
                    return self._expr_is_non_negative(left)
                if right_lit == 1:
                    return self._expr_is_positive(left)
                return False
            if op == "Mult":
                return self._expr_is_non_negative(left) and self._expr_is_non_negative(right)
            if op == "FloorDiv" or op == "Div":
                return self._expr_is_non_negative(left) and self._expr_is_positive(right)
            if op == "Mod":
                return self._expr_is_positive(right)
        return False

    def _const_number_literal(self, node: Any) -> int | float | None:
        d = self.any_to_dict_or_empty(node)
        if len(d) == 0:
            return None
        if self.any_dict_get_str(d, "kind", "") != "Constant":
            return None
        value_any = d.get("value")
        if isinstance(value_any, bool):
            return None
        if isinstance(value_any, int):
            return int(value_any)
        if isinstance(value_any, float):
            return float(value_any)
        return None

    def _sign_name_candidate(self, node: Any) -> str:
        d = self.any_to_dict_or_empty(node)
        if len(d) == 0:
            return ""
        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "Name":
            return self.any_dict_get_str(d, "id", "")
        if kind == "Call":
            fn = self.any_to_dict_or_empty(d.get("func"))
            fn_kind = self.any_dict_get_str(fn, "kind", "")
            if fn_kind != "Name":
                return ""
            fn_name = self.any_dict_get_str(fn, "id", "")
            if fn_name != "int" and fn_name != "float":
                return ""
            args = self.any_to_list(d.get("args"))
            if len(args) == 0:
                return ""
            return self._sign_name_candidate(args[0])
        if kind == "UnaryOp" and self.any_dict_get_str(d, "op", "") == "UAdd":
            return self._sign_name_candidate(d.get("operand"))
        return ""

    def _flip_compare_op(self, op: str) -> str:
        if op == "Lt":
            return "Gt"
        if op == "LtE":
            return "GtE"
        if op == "Gt":
            return "Lt"
        if op == "GtE":
            return "LtE"
        return op

    def _apply_sign_hint_from_name_const_compare(self, name: str, op: str, const_value: int | float, non_negative: set[str], positive: set[str]) -> None:
        if name == "":
            return
        if op == "Gt":
            if const_value >= 0:
                positive.add(name)
                non_negative.add(name)
            return
        if op == "GtE":
            if const_value >= 1:
                positive.add(name)
                non_negative.add(name)
                return
            if const_value >= 0:
                non_negative.add(name)
            return
        if op == "Eq":
            if const_value > 0:
                positive.add(name)
                non_negative.add(name)
                return
            if const_value == 0:
                non_negative.add(name)

    def _infer_then_sign_assumptions_from_test(self, test_node: Any) -> tuple[set[str], set[str]]:
        non_negative: set[str] = set()
        positive: set[str] = set()
        d = self.any_to_dict_or_empty(test_node)
        if len(d) == 0:
            return non_negative, positive

        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "BoolOp" and self.any_dict_get_str(d, "op", "") == "And":
            for value_node in self.any_to_list(d.get("values")):
                add_non_negative, add_positive = self._infer_then_sign_assumptions_from_test(value_node)
                non_negative.update(add_non_negative)
                positive.update(add_positive)
            return non_negative, positive

        if kind != "Compare":
            return non_negative, positive

        ops = self.any_to_str_list(d.get("ops"))
        comps = self.any_to_list(d.get("comparators"))
        if len(ops) == 0 or len(comps) == 0:
            return non_negative, positive

        op = ops[0]
        left_node = self.any_to_dict_or_empty(d.get("left"))
        right_node = self.any_to_dict_or_empty(comps[0])
        left_name = self._sign_name_candidate(left_node)
        right_name = self._sign_name_candidate(right_node)
        left_const = self._const_number_literal(left_node)
        right_const = self._const_number_literal(right_node)

        if left_name != "" and right_const is not None:
            self._apply_sign_hint_from_name_const_compare(left_name, op, right_const, non_negative, positive)
            return non_negative, positive

        if right_name != "" and left_const is not None:
            self._apply_sign_hint_from_name_const_compare(
                right_name,
                self._flip_compare_op(op),
                left_const,
                non_negative,
                positive,
            )
            return non_negative, positive

        return non_negative, positive

    def _update_name_sign_info(self, name_raw: str, value_node: Any) -> None:
        if name_raw == "":
            return
        if self._expr_is_non_negative(value_node):
            self.current_non_negative_vars.add(name_raw)
        else:
            self.current_non_negative_vars.discard(name_raw)
        if self._expr_is_positive(value_node):
            self.current_positive_vars.add(name_raw)
        else:
            self.current_positive_vars.discard(name_raw)

    def _const_int_literal(self, node: Any) -> int | None:
        d = self.any_to_dict_or_empty(node)
        if len(d) == 0:
            return None
        if self.any_dict_get_str(d, "kind", "") == "Constant":
            value_any = d.get("value")
            if isinstance(value_any, bool):
                return None
            if isinstance(value_any, int):
                return int(value_any)
        return None

    def _string_constant_literal(self, node: Any) -> str:
        d = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(d, "kind", "") != "Constant":
            return ""
        v = d.get("value")
        if not isinstance(v, str):
            return ""
        return self.quote_string_literal(v)

    def _ensure_string_owned(self, text: str) -> str:
        expr_trim = self._strip_outer_parens(text)
        if expr_trim.endswith(".to_string()") or expr_trim.endswith(".to_owned()"):
            return text
        if expr_trim.startswith("String::from("):
            return text
        return "((" + text + ").to_string())"

    def _dict_key_value_types(self, east_type: str) -> tuple[str, str]:
        t = self.normalize_type_name(east_type)
        if not t.startswith("dict[") or not t.endswith("]"):
            return "", ""
        parts = self.split_generic(t[5:-1].strip())
        if len(parts) != 2:
            return "", ""
        return self.normalize_type_name(parts[0]), self.normalize_type_name(parts[1])

    def _coerce_dict_key_expr(self, key_expr: str, key_type: str, require_owned: bool = True) -> str:
        """dict key 型に合わせて key 式を補正する。"""
        if self.normalize_type_name(key_type) == "str":
            if require_owned:
                return self._ensure_string_owned(key_expr)
            return key_expr
        return key_expr

    def _is_dict_with_any_value(self, east_type: str) -> bool:
        key_t, val_t = self._dict_key_value_types(east_type)
        _ = key_t
        return self._is_any_type(val_t)

    def _dict_get_owner_value_type(self, call_node: Any) -> str:
        """`dict.get(...)` 呼び出しなら owner の value 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "get":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            _key_t, val_t = self._dict_key_value_types(owner_t)
            return val_t
        return ""

    def _dict_items_owner_type(self, call_node: Any) -> str:
        """`dict.items()` 呼び出しなら owner の dict 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "items":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            return owner_t
        return ""

    def _const_string_literal_value(self, node: Any) -> str | None:
        d = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(d, "kind", "") != "Constant":
            return None
        v = d.get("value")
        if isinstance(v, str):
            return v
        return None

    def _extract_const_string_dict_binding(self, value_node: Any) -> dict[str, str] | None:
        value_d = self.any_to_dict_or_empty(value_node)
        if self.any_dict_get_str(value_d, "kind", "") != "Dict":
            return None
        out: dict[str, str] = {}
        entries = self.any_to_list(value_d.get("entries"))
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_raw = self._const_string_literal_value(ent.get("key"))
                if key_raw is None:
                    return None
                out[key_raw] = self.render_expr(ent.get("value"))
                i += 1
            return out

        keys = self.any_to_list(value_d.get("keys"))
        values = self.any_to_list(value_d.get("values"))
        if len(keys) != len(values):
            return None
        i = 0
        while i < len(keys):
            key_raw = self._const_string_literal_value(keys[i])
            if key_raw is None:
                return None
            out[key_raw] = self.render_expr(values[i])
            i += 1
        return out

    def _update_const_string_dict_binding(self, name_raw: str, value_node: Any, is_mut: bool) -> None:
        if name_raw == "":
            return
        if is_mut:
            self.current_const_string_dict_bindings.pop(name_raw, None)
            return
        entries = self._extract_const_string_dict_binding(value_node)
        if entries is None:
            self.current_const_string_dict_bindings.pop(name_raw, None)
            return
        self.current_const_string_dict_bindings[name_raw] = entries

    def _render_const_string_dict_get(self, owner_name_raw: str, key_expr: str, key_node: Any, default_expr: str) -> str:
        entries = self.current_const_string_dict_bindings.get(owner_name_raw)
        if entries is None:
            return ""
        key_lit = self._const_string_literal_value(key_node)
        if key_lit is not None:
            return entries.get(key_lit, default_expr)
        if len(entries) == 0:
            return default_expr
        arms: list[str] = []
        for key_raw, value_txt in sorted(entries.items(), key=lambda kv: kv[0]):
            arms.append(self.quote_string_literal(key_raw) + " => " + value_txt)
        return "(match (" + key_expr + ").as_str() { " + ", ".join(arms) + ", _ => " + default_expr + " })"

    def _emit_pyany_runtime(self) -> None:
        """Any/object 用の最小ランタイム（PyAny）を出力する。"""
        self.emit("#[derive(Clone, Debug, Default)]")
        self.emit("enum PyAny {")
        self.indent += 1
        self.emit("Int(i64),")
        self.emit("Float(f64),")
        self.emit("Bool(bool),")
        self.emit("Str(String),")
        self.emit("Dict(::std::collections::BTreeMap<String, PyAny>),")
        self.emit("List(Vec<PyAny>),")
        self.emit("Set(Vec<PyAny>),")
        self.emit("#[default]")
        self.emit("None,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_as_dict(v: PyAny) -> ::std::collections::BTreeMap<String, PyAny> {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Dict(d) => d,")
        self.emit("_ => ::std::collections::BTreeMap::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyAnyToI64Arg {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64;")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for PyAny {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n,")
        self.emit("PyAny::Float(f) => *f as i64,")
        self.emit("PyAny::Bool(b) => if *b { 1 } else { 0 },")
        self.emit("PyAny::Str(s) => s.parse::<i64>().unwrap_or(0),")
        self.emit("_ => 0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for i64 {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { *self }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for i32 {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for f64 {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for f32 {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for bool {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { if *self { 1 } else { 0 } }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for String {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { self.parse::<i64>().unwrap_or(0) }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToI64Arg for str {")
        self.indent += 1
        self.emit("fn py_any_to_i64_arg(&self) -> i64 { self.parse::<i64>().unwrap_or(0) }")
        self.indent -= 1
        self.emit("}")
        self.emit("fn py_any_to_i64<T: PyAnyToI64Arg + ?Sized>(v: &T) -> i64 {")
        self.indent += 1
        self.emit("v.py_any_to_i64_arg()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyAnyToF64Arg {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64;")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for PyAny {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n as f64,")
        self.emit("PyAny::Float(f) => *f,")
        self.emit("PyAny::Bool(b) => if *b { 1.0 } else { 0.0 },")
        self.emit("PyAny::Str(s) => s.parse::<f64>().unwrap_or(0.0),")
        self.emit("_ => 0.0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for f64 {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { *self }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for f32 {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for i64 {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for i32 {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for bool {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { if *self { 1.0 } else { 0.0 } }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for String {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { self.parse::<f64>().unwrap_or(0.0) }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToF64Arg for str {")
        self.indent += 1
        self.emit("fn py_any_to_f64_arg(&self) -> f64 { self.parse::<f64>().unwrap_or(0.0) }")
        self.indent -= 1
        self.emit("}")
        self.emit("fn py_any_to_f64<T: PyAnyToF64Arg + ?Sized>(v: &T) -> f64 {")
        self.indent += 1
        self.emit("v.py_any_to_f64_arg()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyAnyToBoolArg {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool;")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for PyAny {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n != 0,")
        self.emit("PyAny::Float(f) => *f != 0.0,")
        self.emit("PyAny::Bool(b) => *b,")
        self.emit("PyAny::Str(s) => !s.is_empty(),")
        self.emit("PyAny::Dict(d) => !d.is_empty(),")
        self.emit("PyAny::List(xs) => !xs.is_empty(),")
        self.emit("PyAny::Set(xs) => !xs.is_empty(),")
        self.emit("PyAny::None => false,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for bool {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool { *self }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for i64 {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool { *self != 0 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for f64 {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool { *self != 0.0 }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for String {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool { !self.is_empty() }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToBoolArg for str {")
        self.indent += 1
        self.emit("fn py_any_to_bool_arg(&self) -> bool { !self.is_empty() }")
        self.indent -= 1
        self.emit("}")
        self.emit("fn py_any_to_bool<T: PyAnyToBoolArg + ?Sized>(v: &T) -> bool {")
        self.indent += 1
        self.emit("v.py_any_to_bool_arg()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyAnyToStringArg {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String;")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for PyAny {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("PyAny::Int(n) => n.to_string(),")
        self.emit("PyAny::Float(f) => f.to_string(),")
        self.emit("PyAny::Bool(b) => b.to_string(),")
        self.emit("PyAny::Str(s) => s.clone(),")
        self.emit("PyAny::Dict(d) => format!(\"{:?}\", d),")
        self.emit("PyAny::List(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::Set(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::None => String::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for String {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String { self.clone() }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for str {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String { self.to_string() }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for i64 {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String { self.to_string() }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for f64 {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String { self.to_string() }")
        self.indent -= 1
        self.emit("}")
        self.emit("impl PyAnyToStringArg for bool {")
        self.indent += 1
        self.emit("fn py_any_to_string_arg(&self) -> String { self.to_string() }")
        self.indent -= 1
        self.emit("}")
        self.emit("fn py_any_to_string<T: PyAnyToStringArg + ?Sized>(v: &T) -> String {")
        self.indent += 1
        self.emit("v.py_any_to_string_arg()")
        self.indent -= 1
        self.emit("}")

    def _module_id_to_rust_use_path(self, module_id: str) -> str:
        """Python 形式モジュール名を Rust `use` パスへ変換する。"""
        module_name = canonical_runtime_module_id(module_id.strip())
        if module_name == "":
            return ""
        return "crate::" + module_name.replace(".", "::")

    def _is_assertions_module(self, module_id: str) -> bool:
        if module_id == "":
            return False
        if module_id.endswith(".assertions"):
            return True
        if module_id == "assertions":
            return True
        return False

    def _is_image_utils_module(self, module_id: str) -> bool:
        module_name = canonical_runtime_module_id(module_id.strip())
        if not module_name.startswith("pytra.utils."):
            return False
        leaf = self._last_dotted_name(module_name)
        return leaf == "gif" or leaf == "png"

    def _should_skip_module_use_line(self, module_id: str, local_name: str) -> bool:
        """互換 prelude と衝突する `use crate::pytra::std::{math,time};` を抑止する。"""
        module_name = canonical_runtime_module_id(module_id.strip())
        if module_name not in {"pytra.std.math", "pytra.std.time"}:
            return False
        leaf = self._last_dotted_name(module_name)
        return local_name == "" or local_name == leaf

    def _apply_image_runtime_ref_args(self, call_args: list[str]) -> list[str]:
        if len(call_args) > 0:
            call_args[0] = "&(" + call_args[0] + ")"
        if len(call_args) >= 4:
            call_args[3] = "&(" + call_args[3] + ")"
        if len(call_args) >= 5:
            call_args[4] = "&(" + call_args[4] + ")"
        return call_args

    def _collect_use_lines(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """import 情報を Rust `use` 行へ変換する。"""
        out: list[str] = []
        seen: set[str] = set()

        def _add(line: str) -> None:
            if line == "" or line in seen:
                return
            seen.add(line)
            out.append(line)

        bindings = self.get_import_resolution_bindings(meta)
        if len(bindings) > 0:
            i = 0
            while i < len(bindings):
                ent = bindings[i]
                binding_kind = self.any_to_str(ent.get("binding_kind"))
                module_id = self.any_to_str(ent.get("module_id"))
                runtime_module_id = self.any_to_str(ent.get("runtime_module_id"))
                resolved_binding_kind = self.any_to_str(ent.get("resolved_binding_kind"))
                local_name = self.any_to_str(ent.get("local_name"))
                export_name = self.any_to_str(ent.get("runtime_symbol"))
                if export_name == "":
                    export_name = self.any_to_str(ent.get("export_name"))
                if runtime_module_id != "":
                    module_id = runtime_module_id
                if resolved_binding_kind == "":
                    resolved_binding_kind = binding_kind
                if module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                    i += 1
                    continue
                if self._is_assertions_module(module_id):
                    i += 1
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if (binding_kind == "module" or resolved_binding_kind == "module") and base_path != "":
                    if self._should_skip_module_use_line(module_id, local_name):
                        i += 1
                        continue
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if local_name != "" and local_name != leaf:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                elif binding_kind == "symbol" and base_path != "" and export_name != "":
                    line = "use " + base_path + "::" + export_name
                    if local_name != "" and local_name != export_name:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                        continue
                    if self._is_assertions_module(module_id):
                        continue
                    base_path = self._module_id_to_rust_use_path(module_id)
                    if base_path == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    if self._should_skip_module_use_line(module_id, asname):
                        continue
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if asname != "" and asname != leaf:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                    continue
                if self._is_assertions_module(module_id):
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if base_path == "":
                    continue
                for ent in self._dict_stmt_list(stmt.get("names")):
                    name = self.any_to_str(ent.get("name"))
                    if name == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    line = "use " + base_path + "::" + name
                    if asname != "" and asname != name:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
        return out

    def _infer_default_for_type(self, east_type: str) -> str:
        """型ごとの既定値（Rust）を返す。"""
        t = self.normalize_type_name(east_type)
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny::None"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return "0"
        if t in {"float32", "float64"}:
            return "0.0"
        if t == "bool":
            return "false"
        if t == "str":
            return "String::new()"
        if t == "bytes" or t == "bytearray" or t.startswith("list["):
            return "Vec::new()"
        if t.startswith("set["):
            return "::std::collections::BTreeSet::new()"
        if t.startswith("dict["):
            return "::std::collections::BTreeMap::new()"
        if t.startswith("tuple["):
            return "()"
        if t == "None":
            return "()"
        if t.startswith("Option[") and t.endswith("]"):
            return "None"
        if t in self.class_names:
            return f"{t}::new()"
        return "Default::default()"

    def apply_cast(self, rendered_expr: str, to_type: str) -> str:
        """Rust 向けの最小キャストを適用する。"""
        t = self.normalize_type_name(to_type)
        if t == "":
            return rendered_expr
        rust_t = self._rust_type(t)
        if rust_t == "String":
            return self._ensure_string_owned(rendered_expr)
        if rust_t == "bool":
            return "((" + rendered_expr + ") != 0)"
        return "((" + rendered_expr + ") as " + rust_t + ")"

    def _refine_decl_type_from_value(self, declared_type: str, value_node: Any) -> str:
        """`Any` を含む宣言型より値側の具体型が有用なら値側を優先する。"""
        d = self.normalize_type_name(declared_type)
        if d == "":
            return self.get_expr_type(value_node)
        v = self.normalize_type_name(self.get_expr_type(value_node))
        if v == "":
            return d
        if self.is_any_like_type(d):
            return v
        if self._contains_text(d, "Any"):
            # `dict[str, Any]` などのコンテナ注釈は、Rust 側の型整合を優先して
            # 宣言型を保持する。値側推論で過度に具体化すると、混在値辞書が壊れる。
            if d.startswith("dict[") or d.startswith("list[") or d.startswith("tuple["):
                return d
            if d.startswith("dict[") and v.startswith("dict["):
                return v
            if d.startswith("list[") and v.startswith("list["):
                return v
            if d.startswith("tuple[") and v.startswith("tuple["):
                return v
        return d

    def _rust_type(self, east_type: str) -> str:
        """EAST 型名を Rust 型名へ変換する。"""
        t, mapped = self.normalize_type_and_lookup_map(east_type, self.type_map)
        if t == "":
            return "i64"
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny"
        if mapped != "":
            return mapped
        list_inner = self.type_generic_args(t, "list")
        if len(list_inner) == 1:
            return f"Vec<{self._rust_type(list_inner[0])}>"
        set_inner = self.type_generic_args(t, "set")
        if len(set_inner) == 1:
            return f"::std::collections::BTreeSet<{self._rust_type(set_inner[0])}>"
        dict_inner = self.type_generic_args(t, "dict")
        if len(dict_inner) == 2:
            parts = dict_inner
            return (
                "::std::collections::BTreeMap<"
                + self._rust_type(parts[0])
                + ", "
                + self._rust_type(parts[1])
                + ">"
            )
        tuple_inner = self.type_generic_args(t, "tuple")
        if len(tuple_inner) > 0:
            rendered: list[str] = []
            for part in tuple_inner:
                rendered.append(self._rust_type(part))
            if len(rendered) == 1:
                return f"({rendered[0]},)"
            return "(" + ", ".join(rendered) + ")"
        if t.find("|") >= 0:
            union_parts = self.split_union(t)
            if len(union_parts) >= 2:
                non_none, has_none = self.split_union_non_none(t)
                any_like = False
                for part in non_none:
                    if self._is_any_type(part):
                        any_like = True
                        break
                if any_like:
                    self.uses_pyany = True
                    return "PyAny"
                if has_none and len(non_none) == 1:
                    return f"Option<{self._rust_type(non_none[0])}>"
                if (not has_none) and len(non_none) == 1:
                    return self._rust_type(non_none[0])
                return "String"
        if t == "None":
            return "()"
        return t

    def _emit_runtime_prelude(self) -> None:
        """外部 runtime 参照の基本宣言を出力する。"""
        self.emit("mod py_runtime;")
        self.emit("pub use crate::py_runtime::{math, pytra, time};")
        self.emit("use crate::py_runtime::*;")

    def _emit_type_info_registration_helper(self) -> None:
        """`isinstance` 用の生成済み type table 登録関数を出力する。"""
        if not self.uses_isinstance_runtime:
            return
        self.emit("fn py_register_generated_type_info() {")
        self.indent += 1
        self.emit("static INIT: ::std::sync::Once = ::std::sync::Once::new();")
        self.emit("INIT.call_once(|| {")
        self.indent += 1
        for tid in sorted(self.type_info_map.keys()):
            order, min_id, max_id = self.type_info_map[tid]
            self.emit(f"py_register_type_info({tid}, {order}, {min_id}, {max_id});")
        self.indent -= 1
        self.emit("});")
        self.indent -= 1
        self.emit("}")

    def transpile(self) -> str:
        """モジュール全体を Rust ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}
        self.uses_pyany = self._doc_mentions_any(self.doc)
        self.uses_isinstance_runtime = self._doc_mentions_isinstance(self.doc)
        self.class_type_id_map = {}
        self.type_info_map = {}
        self.function_arg_ref_modes = {}
        self.class_method_arg_ref_modes = {}
        self.current_ref_vars = set()

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.class_names = set()
        self.class_base_map = self._collect_class_base_map(body)
        self.class_method_defs = {}
        self.function_return_types = {}
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "ClassDef":
                class_name = self.any_to_str(stmt.get("name"))
                if class_name != "":
                    self.class_names.add(class_name)
                    method_defs: dict[str, dict[str, Any]] = {}
                    members = self._dict_stmt_list(stmt.get("body"))
                    for member in members:
                        if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                            continue
                        member_name = self.any_to_str(member.get("name"))
                        if member_name == "" or member_name == "__init__":
                            continue
                        method_defs[member_name] = member
                    self.class_method_defs[class_name] = method_defs
            if kind == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                ret_type = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
                if fn_name != "":
                    self.function_return_types[fn_name] = ret_type
                    self.function_arg_ref_modes[self._safe_name(fn_name)] = self._compute_function_arg_ref_modes(stmt)

        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()
        self._emit_runtime_prelude()
        self.emit("")
        use_lines = self._collect_use_lines(body, meta)
        for line in use_lines:
            self.emit(line)
        if len(use_lines) > 0:
            self.emit("")
        if self.uses_isinstance_runtime:
            self._prepare_type_id_table()
            self._emit_type_info_registration_helper()
            self.emit("")
        self._emit_inheritance_trait_declarations()

        top_level_stmts: list[dict[str, Any]] = []
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                continue
            if kind == "FunctionDef":
                self.emit_leading_comments(stmt)
                self._emit_function(stmt, in_class=None)
                self.emit("")
                continue
            if kind == "ClassDef":
                self.emit_leading_comments(stmt)
                self._emit_class(stmt)
                self.emit("")
                continue
            top_level_stmts.append(stmt)

        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        should_emit_main = len(main_guard_body) > 0 or len(top_level_stmts) > 0
        if should_emit_main:
            self.emit("fn main() {")
            if self.uses_isinstance_runtime:
                self.indent += 1
                self.emit("py_register_generated_type_info();")
                self.indent -= 1
            scope: set[str] = set()
            self.emit_scoped_stmt_list(top_level_stmts + main_guard_body, scope)
            self.emit("}")

        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を最小構成の `struct + impl` として出力する。"""
        class_name_raw = self.any_to_str(stmt.get("name"))
        class_meta = self.any_to_dict_or_empty(stmt.get("meta"))
        if len(self.any_to_dict_or_empty(class_meta.get("nominal_adt_v1"))) > 0:
            self._raise_unsupported_nominal_adt_lane(
                lane="declaration",
                context="ClassDef " + class_name_raw,
            )
        class_name = self._safe_name(class_name_raw)
        field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
        norm_field_types: dict[str, str] = {}
        for key, val in field_types.items():
            if isinstance(key, str):
                norm_field_types[key] = self.normalize_type_name(self.any_to_str(val))
        self.class_field_types[class_name_raw] = norm_field_types

        self.emit("#[derive(Clone, Debug)]")
        if len(norm_field_types) == 0:
            self.emit(f"struct {class_name};")
        else:
            self.emit(f"struct {class_name} {{")
            self.indent += 1
            for name, t in norm_field_types.items():
                self.emit(f"{self._safe_name(name)}: {self._rust_type(t)},")
            self.indent -= 1
            self.emit("}")

        self.emit(f"impl {class_name} {{")
        self.indent += 1
        if class_name_raw in self.class_type_id_map:
            self.emit(f"const PYTRA_TYPE_ID: i64 = {self.class_type_id_map[class_name_raw]};")
            self.emit("")
        members = self._dict_stmt_list(stmt.get("body"))
        method_mut_map = self._analyze_class_method_mutability(members)
        self.class_method_mutability[class_name_raw] = method_mut_map
        self.class_method_mutability[class_name] = method_mut_map
        method_ref_modes: dict[str, list[bool]] = {}
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            method_ref_modes[self._safe_name(name)] = self._compute_function_arg_ref_modes(member, for_method=True)
        self.class_method_arg_ref_modes[class_name_raw] = method_ref_modes
        self.class_method_arg_ref_modes[class_name] = method_ref_modes
        self._emit_constructor(class_name, stmt, norm_field_types)
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            self.emit("")
            self._emit_function(member, in_class=class_name_raw)
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self._emit_inheritance_trait_impls_for_class(class_name_raw)
        if self.uses_isinstance_runtime and class_name_raw in self.class_type_id_map:
            self.emit(f"impl PyRuntimeTypeId for {class_name} {{")
            self.indent += 1
            self.emit("fn py_runtime_type_id(&self) -> i64 {")
            self.indent += 1
            self.emit(f"{class_name}::PYTRA_TYPE_ID")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")

    def _emit_constructor(self, class_name: str, cls: dict[str, Any], field_types: dict[str, str]) -> None:
        """`__init__` から `new` を生成する。"""
        init_fn: dict[str, Any] | None = None
        body = self._dict_stmt_list(cls.get("body"))
        for member in body:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                init_fn = member
                break

        arg_items: list[str] = []
        init_scope: set[str] = set()
        if init_fn is not None:
            arg_order = self.any_to_str_list(init_fn.get("arg_order"))
            arg_types = self.any_to_dict_or_empty(init_fn.get("arg_types"))
            for arg_name in arg_order:
                if arg_name == "self":
                    continue
                arg_type = self._rust_type(self.any_to_str(arg_types.get(arg_name)))
                safe = self._safe_name(arg_name)
                arg_items.append(f"{safe}: {arg_type}")
                init_scope.add(arg_name)
        elif len(field_types) > 0:
            for field_name, field_t in field_types.items():
                safe = self._safe_name(field_name)
                arg_items.append(f"{safe}: {self._rust_type(field_t)}")
                init_scope.add(field_name)

        args_text = ", ".join(arg_items)
        self.emit(f"fn new({args_text}) -> Self {{")
        self.indent += 1

        field_values: dict[str, str] = {}
        for field_name, field_t in field_types.items():
            field_values[field_name] = self._infer_default_for_type(field_t)

        if init_fn is not None:
            init_body = self._dict_stmt_list(init_fn.get("body"))
            for stmt in init_body:
                kind = self.any_dict_get_str(stmt, "kind", "")
                if kind != "Assign" and kind != "AnnAssign":
                    continue
                target = self.any_to_dict_or_empty(stmt.get("target"))
                if len(target) == 0:
                    targets = self._dict_stmt_list(stmt.get("targets"))
                    if len(targets) > 0:
                        target = targets[0]
                if self.any_dict_get_str(target, "kind", "") != "Attribute":
                    continue
                owner = self.any_to_dict_or_empty(target.get("value"))
                if self.any_dict_get_str(owner, "kind", "") != "Name":
                    continue
                if self.any_to_str(owner.get("id")) != "self":
                    continue
                field_name = self.any_to_str(target.get("attr"))
                if field_name == "":
                    continue
                value_node = stmt.get("value")
                if value_node is None:
                    continue
                if self._expr_mentions_name(value_node, "self"):
                    continue
                field_values[field_name] = self.render_expr(value_node)
        elif len(field_types) > 0:
            for field_name in field_types.keys():
                field_values[field_name] = self._safe_name(field_name)

        if len(field_types) == 0:
            if len(init_scope) > 0:
                args_names: list[str] = []
                for arg_name in init_scope:
                    args_names.append(self._safe_name(arg_name))
                self.emit("let _ = (" + ", ".join(args_names) + ");")
            self.emit("Self")
        else:
            self.emit("Self {")
            self.indent += 1
            for field_name in field_types.keys():
                safe = self._safe_name(field_name)
                self.emit(f"{safe}: {field_values.get(field_name, 'Default::default()')},")
            self.indent -= 1
            self.emit("}")

        self.indent -= 1
        self.emit("}")

    def _emit_function(self, fn: dict[str, Any], in_class: str | None) -> None:
        """FunctionDef を Rust 関数として出力する。"""
        fn_name_raw = self.any_to_str(fn.get("name"))
        fn_name = self._safe_name(fn_name_raw)
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        arg_type_exprs = self.any_to_dict_or_empty(fn.get("arg_type_exprs"))
        arg_usage = self.any_to_dict_or_empty(fn.get("arg_usage"))
        body = self._dict_stmt_list(fn.get("body"))
        prev_write_counts = self.current_fn_write_counts
        prev_mut_call_counts = self.current_fn_mutating_call_counts
        prev_ref_vars = self.current_ref_vars
        prev_non_negative_vars = self.current_non_negative_vars
        prev_positive_vars = self.current_positive_vars
        prev_assumed_non_negative_vars = self.assumed_non_negative_vars
        prev_assumed_positive_vars = self.assumed_positive_vars
        prev_const_string_dict_bindings = self.current_const_string_dict_bindings
        prev_hashmap_dict_names = self.current_hashmap_dict_names
        prev_class_name = self.current_class_name
        self.current_class_name = self.normalize_type_name(in_class) if in_class is not None else ""
        self.current_fn_write_counts = self._collect_name_write_counts(body)
        self.current_fn_mutating_call_counts = self._collect_mutating_receiver_name_counts(body)
        self.current_ref_vars = set()
        self.current_non_negative_vars = set()
        self.current_positive_vars = set()
        self.assumed_non_negative_vars = set()
        self.assumed_positive_vars = set()
        self.current_const_string_dict_bindings = {}
        self.current_hashmap_dict_names = self._analyze_function_hashmap_dict_names(fn, in_class=in_class)
        args_text_list: list[str] = []
        scope_names: set[str] = set()
        if in_class is None:
            fn_ref_modes = self.function_arg_ref_modes.get(fn_name, [])
        else:
            fn_ref_modes = self.class_method_arg_ref_modes.get(in_class, {}).get(fn_name, [])
        arg_pos = 0

        if in_class is not None:
            if len(arg_order) > 0 and arg_order[0] == "self":
                self_write_count = self.current_fn_write_counts.get("self", 0)
                self_mut_call_count = self.current_fn_mutating_call_counts.get("self", 0)
                method_mut_map = self.class_method_mutability.get(in_class, {})
                self_mut_call_count += self._count_self_calls_to_mut_methods(body, method_mut_map)
                self_ref = "&mut self" if (self_write_count > 0 or self_mut_call_count > 0) else "&self"
                args_text_list.append(self_ref)
                scope_names.add("self")
                arg_order = arg_order[1:]

        for arg_name in arg_order:
            safe = self._safe_name(arg_name)
            arg_east_t = self.any_to_str(arg_types.get(arg_name))
            self._reject_unsupported_general_union_type_expr(
                arg_type_exprs.get(arg_name),
                context="FunctionDef arg " + arg_name,
            )
            arg_t = self._rust_type_for_binding(arg_name, arg_east_t)
            usage = self.any_to_str(arg_usage.get(arg_name))
            write_count = self.current_fn_write_counts.get(arg_name, 0)
            mut_call_count = self.current_fn_mutating_call_counts.get(arg_name, 0)
            is_mut = usage == "reassigned" or usage == "mutable" or usage == "write" or write_count > 0 or mut_call_count > 0
            pass_by_ref = False
            if arg_pos < len(fn_ref_modes):
                pass_by_ref = fn_ref_modes[arg_pos]
            arg_pos += 1
            if pass_by_ref:
                arg_t = self._borrowed_arg_type_text(arg_east_t, arg_t, allow_trait_impl=True)
            prefix = "mut " if is_mut else ""
            args_text_list.append(f"{prefix}{safe}: {arg_t}")
            scope_names.add(arg_name)
            if pass_by_ref:
                self.current_ref_vars.add(arg_name)
            self.declared_var_types[arg_name] = self.normalize_type_name(self.any_to_str(arg_types.get(arg_name)))

        self._reject_unsupported_general_union_type_expr(
            fn.get("return_type_expr"),
            context="FunctionDef return type for " + fn_name_raw,
        )
        ret_t_east = self.normalize_type_name(self.any_to_str(fn.get("return_type")))
        ret_t = self._rust_type(ret_t_east)
        ret_txt = ""
        if ret_t != "()":
            ret_txt = " -> " + ret_t
        line = self.syntax_line(
            "function_open",
            "fn {name}({args}){ret_txt} {",
            {"name": fn_name, "args": ", ".join(args_text_list), "ret_txt": ret_txt},
        )
        self.emit(line)

        self.emit_scoped_stmt_list(body, scope_names)
        self.emit("}")
        self.current_fn_write_counts = prev_write_counts
        self.current_fn_mutating_call_counts = prev_mut_call_counts
        self.current_ref_vars = prev_ref_vars
        self.current_non_negative_vars = prev_non_negative_vars
        self.current_positive_vars = prev_positive_vars
        self.assumed_non_negative_vars = prev_assumed_non_negative_vars
        self.assumed_positive_vars = prev_assumed_positive_vars
        self.current_const_string_dict_bindings = prev_const_string_dict_bindings
        self.current_hashmap_dict_names = prev_hashmap_dict_names
        self.current_class_name = prev_class_name

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを Rust へ出力する。"""
        self.emit_leading_comments(stmt)
        hooked = self.hook_on_emit_stmt(stmt)
        if hooked is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        hooked_kind = self.hook_on_emit_stmt_kind(kind, stmt)
        if hooked_kind is True:
            return
        if kind == "Match":
            self._raise_unsupported_nominal_adt_lane(
                lane="match",
                context="Match statement",
            )

        if kind == "Pass":
            self.emit(self.syntax_text("pass_stmt", "();"))
            return
        if kind == "Break":
            self.emit(self.syntax_text("break_stmt", "break;"))
            return
        if kind == "Continue":
            self.emit(self.syntax_text("continue_stmt", "continue;"))
            return
        if kind == "Expr":
            expr_d = self.any_to_dict_or_empty(stmt.get("value"))
            if self.any_dict_get_str(expr_d, "kind", "") == "Name":
                expr_name = self.any_dict_get_str(expr_d, "id", "")
                if expr_name == "break":
                    self.emit(self.syntax_text("break_stmt", "break;"))
                    return
                if expr_name == "continue":
                    self.emit(self.syntax_text("continue_stmt", "continue;"))
                    return
                if expr_name == "pass":
                    self.emit(self.syntax_text("pass_stmt", "();"))
                    return
            expr_txt = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("expr_stmt", "{expr};", {"expr": expr_txt}))
            return
        if kind == "Return":
            if stmt.get("value") is None:
                self.emit(self.syntax_text("return_void", "return;"))
            else:
                val = self._render_return_expr(stmt.get("value"))
                self.emit(self.syntax_line("return_value", "return {value};", {"value": val}))
            return
        if kind == "AnnAssign":
            self._emit_annassign(stmt)
            return
        if kind == "Assign":
            self._emit_assign(stmt)
            return
        if kind == "AugAssign":
            self._emit_augassign(stmt)
            return
        if kind == "Raise":
            exc_node = self.any_to_dict_or_empty(stmt.get("exc"))
            msg_expr = "\"runtime error\".to_string()"
            if self.any_dict_get_str(exc_node, "kind", "") == "Call":
                args = self.any_to_list(exc_node.get("args"))
                if len(args) > 0:
                    msg_expr = self.render_expr(args[0])
            elif len(exc_node) > 0:
                msg_expr = self.render_expr(exc_node)
            self.emit("panic!(\"{}\", " + msg_expr + ");")
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "CaptureCounterIfPlan":
            loop_var_raw = self.any_to_str(stmt.get("loop_var"))
            loop_var = self._safe_name(loop_var_raw)
            next_counter = self.any_to_str(stmt.get("next_counter_name"))
            step_expr = self.render_expr(stmt.get("step"))
            body_stmts = self._dict_stmt_list(stmt.get("body"))
            self.emit(f"if {loop_var} == {next_counter} {{")
            self.emit_scoped_stmt_list(body_stmts, set())
            self.emit(f"{next_counter} += {step_expr};")
            self.emit("}")
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
            return
        if kind == "For":
            self._emit_for(stmt)
            return
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "Try":
            self._emit_try(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            return

        raise RuntimeError("rust emitter: unsupported stmt kind: " + kind)

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond, body_stmts, else_stmts = self.prepare_if_stmt_parts(
            stmt,
            cond_empty_default="false",
        )
        test_node = stmt.get("test")
        if self.any_to_str(stmt.get("normalized_expr_version")) == "east3_expr_v1":
            normalized_exprs = self.any_to_dict_or_empty(stmt.get("normalized_exprs"))
            cond_node = normalized_exprs.get("if_cond_expr")
            if cond_node is not None:
                test_node = cond_node
        then_non_negative, then_positive = self._infer_then_sign_assumptions_from_test(test_node)
        self.emit(self.syntax_line("if_open", "if {cond} {", {"cond": cond}))
        prev_assumed_non_negative = self.assumed_non_negative_vars
        prev_assumed_positive = self.assumed_positive_vars
        if len(then_non_negative) > 0 or len(then_positive) > 0:
            self.assumed_non_negative_vars = set(prev_assumed_non_negative)
            self.assumed_positive_vars = set(prev_assumed_positive)
            self.assumed_non_negative_vars.update(then_non_negative)
            self.assumed_positive_vars.update(then_positive)
        self.emit_scoped_stmt_list(body_stmts, set())
        self.assumed_non_negative_vars = prev_assumed_non_negative
        self.assumed_positive_vars = prev_assumed_positive
        self._emit_if_else_chain(else_stmts)

    def _emit_try(self, stmt: dict[str, Any]) -> None:
        """Try/Finally を Rust の逐次ブロックへ縮退して出力する。"""
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        orelse_stmts = self._dict_stmt_list(stmt.get("orelse"))
        final_stmts = self._dict_stmt_list(stmt.get("finalbody"))
        handlers = self.any_to_list(stmt.get("handlers"))

        # Rust backend では例外機構を持たないため、Try は逐次実行へ縮退する。
        self.emit("{")
        self.emit_scoped_stmt_list(body_stmts, set())
        self.emit("}")
        if len(handlers) > 0:
            i = 0
            while i < len(handlers):
                h = self.any_to_dict_or_empty(handlers[i])
                h_body = self._dict_stmt_list(h.get("body"))
                if len(h_body) > 0:
                    self.emit("{")
                    self.emit_scoped_stmt_list(h_body, set())
                    self.emit("}")
                i += 1
        if len(orelse_stmts) > 0:
            self.emit("{")
            self.emit_scoped_stmt_list(orelse_stmts, set())
            self.emit("}")
        if len(final_stmts) > 0:
            self.emit("{")
            self.emit_scoped_stmt_list(final_stmts, set())
            self.emit("}")

    def _emit_if_else_chain(self, else_stmts: list[dict[str, Any]]) -> None:
        if len(else_stmts) == 0:
            self.emit(self.syntax_text("block_close", "}"))
            return
        if len(else_stmts) == 1 and self.any_dict_get_str(else_stmts[0], "kind", "") == "If":
            nested = else_stmts[0]
            nested_cond, nested_body, nested_else = self.prepare_if_stmt_parts(
                nested,
                cond_empty_default="false",
            )
            nested_test_node = nested.get("test")
            if self.any_to_str(nested.get("normalized_expr_version")) == "east3_expr_v1":
                normalized_exprs = self.any_to_dict_or_empty(nested.get("normalized_exprs"))
                cond_node = normalized_exprs.get("if_cond_expr")
                if cond_node is not None:
                    nested_test_node = cond_node
            then_non_negative, then_positive = self._infer_then_sign_assumptions_from_test(nested_test_node)
            self.emit(self.syntax_line("else_if_open", "} else if {cond} {", {"cond": nested_cond}))
            prev_assumed_non_negative = self.assumed_non_negative_vars
            prev_assumed_positive = self.assumed_positive_vars
            if len(then_non_negative) > 0 or len(then_positive) > 0:
                self.assumed_non_negative_vars = set(prev_assumed_non_negative)
                self.assumed_positive_vars = set(prev_assumed_positive)
                self.assumed_non_negative_vars.update(then_non_negative)
                self.assumed_positive_vars.update(then_positive)
            self.emit_scoped_stmt_list(nested_body, set())
            self.assumed_non_negative_vars = prev_assumed_non_negative
            self.assumed_positive_vars = prev_assumed_positive
            self._emit_if_else_chain(nested_else)
            return
        self.emit(self.syntax_text("else_open", "} else {"))
        self.emit_scoped_stmt_list(else_stmts, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _match_capture_mod_if_plan(self, stmt: dict[str, Any], loop_var_raw: str) -> dict[str, Any] | None:
        if self.any_dict_get_str(stmt, "kind", "") != "If":
            return None
        if len(self._dict_stmt_list(stmt.get("orelse"))) > 0:
            return None
        test_d = self.any_to_dict_or_empty(stmt.get("test"))
        if self.any_dict_get_str(test_d, "kind", "") != "Compare":
            return None
        ops = self.any_to_str_list(test_d.get("ops"))
        comps = self.any_to_list(test_d.get("comparators"))
        if len(ops) != 1 or len(comps) != 1 or ops[0] != "Eq":
            return None
        rhs_zero = self._const_int_literal(comps[0])
        if rhs_zero != 0:
            return None
        mod_d = self.any_to_dict_or_empty(test_d.get("left"))
        if self.any_dict_get_str(mod_d, "kind", "") != "BinOp":
            return None
        if self.any_dict_get_str(mod_d, "op", "") != "Mod":
            return None
        left_d = self.any_to_dict_or_empty(mod_d.get("left"))
        if self.any_dict_get_str(left_d, "kind", "") != "Name":
            return None
        if self.any_dict_get_str(left_d, "id", "") != loop_var_raw:
            return None
        step_node = mod_d.get("right")
        if step_node is None:
            return None
        if self._expr_mentions_name(step_node, loop_var_raw):
            return None
        if not self._expr_is_positive(step_node):
            return None
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        reserve_owner = ""
        if len(body_stmts) == 1:
            b0 = self.any_to_dict_or_empty(body_stmts[0])
            if self.any_dict_get_str(b0, "kind", "") == "Expr":
                call = self.any_to_dict_or_empty(b0.get("value"))
                if self.any_dict_get_str(call, "kind", "") == "Call":
                    fn = self.any_to_dict_or_empty(call.get("func"))
                    if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                        attr = self.any_dict_get_str(fn, "attr", "")
                        owner = self.any_to_dict_or_empty(fn.get("value"))
                        if attr in {"append", "push"} and self.any_dict_get_str(owner, "kind", "") == "Name":
                            reserve_owner = self.any_dict_get_str(owner, "id", "")
        return {
            "step": step_node,
            "body": body_stmts,
            "reserve_owner": reserve_owner,
            "leading_comments": self.any_to_list(stmt.get("leading_comments")),
            "trailing_comment": self.any_to_str(stmt.get("trailing_comment")),
        }

    def _rewrite_capture_mod_if_in_body(
        self,
        body: list[dict[str, Any]],
        loop_var_raw: str,
        next_counter_name: str,
    ) -> tuple[list[dict[str, Any]], bool, Any, str]:
        rewritten: list[dict[str, Any]] = []
        replaced = False
        matched_step: Any = None
        matched_reserve_owner = ""
        for st in body:
            if not replaced:
                plan = self._match_capture_mod_if_plan(st, loop_var_raw)
                if plan is not None:
                    matched_step = plan.get("step")
                    matched_reserve_owner = self.any_to_str(plan.get("reserve_owner"))
                    rewritten.append(
                        {
                            "kind": "CaptureCounterIfPlan",
                            "loop_var": loop_var_raw,
                            "next_counter_name": next_counter_name,
                            "step": plan.get("step"),
                            "body": plan.get("body"),
                            "leading_comments": plan.get("leading_comments", []),
                            "trailing_comment": plan.get("trailing_comment", ""),
                        }
                    )
                    replaced = True
                    continue
            rewritten.append(st)
        return rewritten, replaced, matched_step, matched_reserve_owner

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond, body_stmts = self.prepare_while_stmt_parts(
            stmt,
            cond_empty_default="false",
        )
        self.emit_while_stmt_skeleton(
            cond,
            body_stmts,
            while_open_default="while {cond} {",
        )

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self._safe_name(self.any_dict_get_str(target_node, "id", "_i"))
        target_raw = self.any_dict_get_str(target_node, "id", "")
        target_type = self._rust_type(self.any_to_str(stmt.get("target_type")))
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))
        step_const = self._const_int_literal(stmt.get("step"))
        body_scope: set[str] = set()
        if target_raw != "":
            body_scope.add(target_raw)
        body = self._dict_stmt_list(stmt.get("body"))

        default_ascending_cond = f"{target} < {stop}"
        cond = default_ascending_cond
        if range_mode == "descending":
            cond = f"{target} > {stop}"
        elif range_mode == "dynamic":
            cond = f"(({step}) > 0 && {target} < {stop}) || (({step}) < 0 && {target} > {stop})"
        has_normalized_cond = False
        normalized_exprs = self.any_to_dict_or_empty(stmt.get("normalized_exprs"))
        if self.any_to_str(stmt.get("normalized_expr_version")) == "east3_expr_v1":
            cond_expr = self.any_to_dict_or_empty(normalized_exprs.get("for_cond_expr"))
            if self.any_dict_get_str(cond_expr, "kind", "") == "Compare":
                cond_rendered = self._strip_outer_parens(self.render_expr(cond_expr))
                if cond_rendered != "":
                    cond = cond_rendered
                    has_normalized_cond = True
        target_used_after = target_raw != "" and self._current_stmt_uses_name_later(target_raw)

        # Fastpath: canonical ascending step=1 range uses Rust for-loop.
        is_ascending_mode = range_mode == "ascending" or range_mode == ""
        normalized_matches_default = (not has_normalized_cond) or (cond == default_ascending_cond)
        if is_ascending_mode and step_const == 1 and normalized_matches_default:
            body_to_emit = body
            if self._const_int_literal(stmt.get("start")) == 0 and target_raw != "":
                next_counter_name = self.next_tmp("__next_capture")
                rewritten_body, replaced, capture_step_node, reserve_owner_raw = self._rewrite_capture_mod_if_in_body(
                    body,
                    target_raw,
                    next_counter_name,
                )
                if replaced:
                    step_expr = self.render_expr(capture_step_node)
                    if reserve_owner_raw != "":
                        reserve_owner = self._safe_name(reserve_owner_raw)
                        reserve_count_expr = "(if (" + stop + ") <= 0 { 0 } else { ((" + stop + ") + (" + step_expr + ") - 1) / (" + step_expr + ") })"
                        self.emit(reserve_owner + ".reserve((" + reserve_count_expr + ") as usize);")
                    self.emit(f"let mut {next_counter_name}: {target_type} = 0;")
                    body_to_emit = rewritten_body
            prev_target_non_negative = target_raw in self.current_non_negative_vars
            prev_target_positive = target_raw in self.current_positive_vars
            if target_raw != "" and self._expr_is_non_negative(stmt.get("start")):
                self.current_non_negative_vars.add(target_raw)
                self.current_positive_vars.discard(target_raw)
            if target_raw != "" and (not target_used_after):
                target_writes_in_body = self._collect_name_write_counts(body_to_emit).get(target_raw, 0)
                target_bind = ("mut " if target_writes_in_body > 0 else "") + target
                self.emit(f"for {target_bind} in ({start})..({stop}) {{")
                self.indent += 1
                self.emit_scoped_stmt_list(body_to_emit, body_scope)
                self.indent -= 1
                self.emit("}")
            else:
                self.emit(f"let mut {target}: {target_type} = {start};")
                loop_index = self.next_tmp("__for_i")
                self.emit(f"for {loop_index} in ({start})..({stop}) {{")
                self.indent += 1
                self.emit(f"{target} = {loop_index};")
                self.emit_scoped_stmt_list(body_to_emit, body_scope)
                self.indent -= 1
                self.emit("}")
            if target_raw != "":
                if prev_target_non_negative:
                    self.current_non_negative_vars.add(target_raw)
                else:
                    self.current_non_negative_vars.discard(target_raw)
                if prev_target_positive:
                    self.current_positive_vars.add(target_raw)
                else:
                    self.current_positive_vars.discard(target_raw)
            return

        self.emit(f"let mut {target}: {target_type} = {start};")
        loop_target_raw = self.any_dict_get_str(target_node, "id", "")
        prev_loop_non_negative = loop_target_raw in self.current_non_negative_vars
        prev_loop_positive = loop_target_raw in self.current_positive_vars
        if loop_target_raw != "" and is_ascending_mode and self._expr_is_non_negative(stmt.get("start")):
            self.current_non_negative_vars.add(loop_target_raw)
            self.current_positive_vars.discard(loop_target_raw)
        self.emit_scoped_block_with_tail_lines(
            self.syntax_line("for_range_open", "while {cond} {", {"cond": cond}),
            body,
            body_scope,
            [f"{target} += {step};"],
        )
        if loop_target_raw != "":
            if prev_loop_non_negative:
                self.current_non_negative_vars.add(loop_target_raw)
            else:
                self.current_non_negative_vars.discard(loop_target_raw)
            if prev_loop_positive:
                self.current_positive_vars.add(loop_target_raw)
            else:
                self.current_positive_vars.discard(loop_target_raw)

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_it")
        target = self._safe_name(target_name)
        body_scope: set[str] = set()
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind == "Name":
            body_scope.add(target_name)
        elif target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            parts: list[str] = []
            for elt in elts:
                d = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(d, "kind", "") == "Name":
                    name = self.any_dict_get_str(d, "id", "_")
                    parts.append(self._safe_name(name))
                    body_scope.add(name)
                else:
                    parts.append("_")
            if len(parts) == 1:
                target = "(" + parts[0] + ",)"
            elif len(parts) > 1:
                target = "(" + ", ".join(parts) + ")"

        iter_node = stmt.get("iter")
        iter_d = self.any_to_dict_or_empty(iter_node)
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        iter_is_attr_view = False
        iter_is_enumerate_call = False
        if self.any_dict_get_str(iter_d, "kind", "") == "Call":
            fn_d = self.any_to_dict_or_empty(iter_d.get("func"))
            fn_kind = self.any_dict_get_str(fn_d, "kind", "")
            if fn_kind == "Attribute":
                attr_name = self.any_dict_get_str(fn_d, "attr", "")
                if attr_name == "items" or attr_name == "keys" or attr_name == "values":
                    iter_is_attr_view = True
            elif fn_kind == "Name":
                iter_is_enumerate_call = self.any_dict_get_str(fn_d, "id", "") == "enumerate"
        if iter_type == "" or iter_type == "unknown":
            iter_type = self._dict_items_owner_type(iter_node)
        iter_key_t = ""
        iter_val_t = ""
        if iter_type.startswith("dict["):
            iter_key_t, iter_val_t = self._dict_key_value_types(iter_type)
        if iter_type == "str":
            iter_expr = iter_expr + ".chars()"
        elif (
            iter_type.startswith("list[")
            or iter_type.startswith("set[")
            or iter_type.startswith("dict[")
        ) and (not iter_is_attr_view) and (not iter_is_enumerate_call):
            if iter_type.startswith("list["):
                iter_expr = self._render_list_iter_expr(iter_expr, iter_type, self._can_borrow_iter_node(iter_node))
            else:
                iter_expr = "(" + iter_expr + ").clone()"

        if target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            if len(elts) >= 2 and iter_key_t != "" and iter_val_t != "":
                k_node = self.any_to_dict_or_empty(elts[0])
                v_node = self.any_to_dict_or_empty(elts[1])
                if self.any_dict_get_str(k_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(k_node, "id", "")] = iter_key_t
                if self.any_dict_get_str(v_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(v_node, "id", "")] = iter_val_t

        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block(
            self.syntax_line("for_open", "for {target} in {iter} {", {"target": target, "iter": iter_expr}),
            body,
            body_scope,
        )

    def _legacy_target_from_for_core_plan(self, plan_node: Any) -> dict[str, Any]:
        """ForCore target_plan を既存 For/ForRange target 形へ変換する。"""
        plan = self.any_to_dict_or_empty(plan_node)
        kind = self.any_dict_get_str(plan, "kind", "")
        if kind == "NameTarget":
            return {"kind": "Name", "id": self.any_dict_get_str(plan, "id", "_")}
        if kind == "TupleTarget":
            elements = self.any_to_list(plan.get("elements"))
            legacy_elements: list[dict[str, Any]] = []
            for elem in elements:
                legacy_elements.append(self._legacy_target_from_for_core_plan(elem))
            return {"kind": "Tuple", "elements": legacy_elements}
        if kind == "ExprTarget":
            target_any = plan.get("target")
            if isinstance(target_any, dict):
                return target_any
        return {"kind": "Name", "id": "_"}

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        """ForCore を既存 For/ForRange emit へ内部変換して処理する。"""
        iter_plan = self.any_to_dict_or_empty(stmt.get("iter_plan"))
        target_plan = self.any_to_dict_or_empty(stmt.get("target_plan"))
        plan_kind = self.any_dict_get_str(iter_plan, "kind", "")
        target = self._legacy_target_from_for_core_plan(target_plan)
        target_type = self.any_dict_get_str(target_plan, "target_type", "")
        body = self._dict_stmt_list(stmt.get("body"))
        orelse = self._dict_stmt_list(stmt.get("orelse"))
        if plan_kind == "StaticRangeForPlan":
            self._emit_for_range(
                {
                    "kind": "ForRange",
                    "target": target,
                    "target_type": target_type,
                    "start": iter_plan.get("start"),
                    "stop": iter_plan.get("stop"),
                    "step": iter_plan.get("step"),
                    "range_mode": self.resolve_forcore_static_range_mode(iter_plan, "dynamic"),
                    "normalized_expr_version": self.any_to_str(stmt.get("normalized_expr_version")),
                    "normalized_exprs": stmt.get("normalized_exprs"),
                    "body": body,
                    "orelse": orelse,
                }
            )
            return
        if plan_kind == "RuntimeIterForPlan":
            self._emit_for(
                {
                    "kind": "For",
                    "target": target,
                    "target_type": target_type,
                    "iter_mode": "runtime_protocol",
                    "iter": iter_plan.get("iter_expr"),
                    "body": body,
                    "orelse": orelse,
                }
            )
            return
        raise RuntimeError("rust emitter: unsupported ForCore iter_plan: " + plan_kind)

    def _render_as_pyany(self, expr: Any) -> str:
        """式を `PyAny` へ昇格する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        kind = self.any_dict_get_str(expr_d, "kind", "")
        src_t = self.normalize_type_name(self.get_expr_type(expr))
        self.uses_pyany = True
        if src_t == "PyAny" or self._is_any_type(src_t):
            return self.render_expr(expr)
        if kind == "Dict":
            return "PyAny::Dict(" + self._render_dict_expr(expr_d, force_any_values=True) + ")"
        if kind == "List":
            items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::List(vec![" + ", ".join(vals) + "])"
        if kind == "Set":
            items = self.any_to_list(expr_d.get("elements"))
            if len(items) == 0:
                items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::Set(vec![" + ", ".join(vals) + "])"
        rendered = self.render_expr(expr)
        if self._is_int_type(src_t):
            return "PyAny::Int((" + rendered + ") as i64)"
        if self._is_float_type(src_t):
            return "PyAny::Float((" + rendered + ") as f64)"
        if src_t == "bool":
            return "PyAny::Bool(" + rendered + ")"
        if src_t == "str":
            return "PyAny::Str(" + self._ensure_string_owned(rendered) + ")"
        if src_t == "None":
            return "PyAny::None"
        return "PyAny::Str(format!(\"{:?}\", " + rendered + "))"

    def _render_dict_expr(
        self,
        expr_d: dict[str, Any],
        *,
        force_any_values: bool = False,
        prefer_hash_map: bool = False,
    ) -> str:
        """Dict リテラルを Rust `BTreeMap::from([...])` へ描画する。"""
        dict_t = self.normalize_type_name(self.get_expr_type(expr_d))
        key_t = ""
        val_t = ""
        if dict_t.startswith("dict[") and dict_t.endswith("]"):
            key_t, val_t = self._dict_key_value_types(dict_t)
        if force_any_values:
            val_t = "Any"

        pairs: list[str] = []
        entries = self.any_to_list(expr_d.get("entries"))
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_node = ent.get("key")
                val_node = ent.get("value")
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = self._ensure_string_owned(key_txt)
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        else:
            keys = self.any_to_list(expr_d.get("keys"))
            vals = self.any_to_list(expr_d.get("values"))
            i = 0
            while i < len(keys) and i < len(vals):
                key_node = keys[i]
                val_node = vals[i]
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = self._ensure_string_owned(key_txt)
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        backend = "::std::collections::BTreeMap::from(["
        if prefer_hash_map:
            backend = "::std::collections::HashMap::from(["
        return backend + ", ".join(pairs) + "])"

    def _render_value_for_decl_type(self, value_obj: Any, target_type: str, *, prefer_hash_map: bool = False) -> str:
        """宣言型に合わせて右辺式を補正する。"""
        t = self.normalize_type_name(target_type)
        value_d = self.any_to_dict_or_empty(value_obj)
        value_kind = self.any_dict_get_str(value_d, "kind", "")
        if self._is_any_type(t):
            return self._render_as_pyany(value_obj)
        if self._is_dict_with_any_value(t):
            if value_kind == "Dict":
                return self._render_dict_expr(value_d, force_any_values=True, prefer_hash_map=prefer_hash_map)
            rendered = self.render_expr(value_obj)
            src_t = self.normalize_type_name(self.get_expr_type(value_obj))
            if self._is_any_type(src_t):
                self.uses_pyany = True
                return "py_any_as_dict(" + rendered + ")"
            if value_kind == "Call":
                owner_val_t = self._dict_get_owner_value_type(value_obj)
                if self._is_any_type(owner_val_t):
                    self.uses_pyany = True
                    return "py_any_as_dict(" + rendered + ")"
            return rendered
        if t.startswith("dict[") and value_kind == "Dict":
            return self._render_dict_expr(value_d, force_any_values=False, prefer_hash_map=prefer_hash_map)
        if value_kind == "Name":
            value_name_raw = self.any_dict_get_str(value_d, "id", "")
            if value_name_raw in self.current_ref_vars:
                rendered_ref = self.render_expr(value_obj)
                if t.startswith("list[") or t in {"bytes", "bytearray"}:
                    return "(" + rendered_ref + ").to_vec()"
                if t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple[") or t in self.class_names:
                    return "(" + rendered_ref + ").clone()"
        if t == "str":
            return self._ensure_string_owned(self.render_expr(value_obj))
        return self.render_expr(value_obj)

    def _infer_byte_buffer_capacity_expr(self, target_name_raw: str) -> str:
        """`bytearray()/bytes()` 初期化向けの容量式を推定する。"""
        name = target_name_raw.lower()
        width_name = ""
        height_name = ""
        if self.is_declared("width"):
            width_name = "width"
        elif self.is_declared("w"):
            width_name = "w"
        if self.is_declared("height"):
            height_name = "height"
        elif self.is_declared("h"):
            height_name = "h"

        if width_name != "" and height_name != "":
            w = self._safe_name(width_name)
            h = self._safe_name(height_name)
            area = "((" + w + ") * (" + h + "))"
            if "pixel" in name:
                return "(" + area + " * 3)"
            if "scanline" in name:
                return "((" + h + ") * (((" + w + ") * 3) + 1))"
            if "frame" in name:
                return area
            return area
        if "palette" in name:
            return "(256 * 3)"
        return ""

    def _maybe_render_preallocated_byte_buffer_init(self, target_name_raw: str, target_type: str, value_obj: Any) -> str:
        """空 `bytearray()/bytes()` 初期化で `with_capacity` を返す。"""
        t = self.normalize_type_name(target_type)
        if t not in {"bytearray", "bytes"}:
            return ""
        value_d = self.any_to_dict_or_empty(value_obj)
        if self.any_dict_get_str(value_d, "kind", "") != "Call":
            return ""
        fn_d = self.any_to_dict_or_empty(value_d.get("func"))
        if self.any_dict_get_str(fn_d, "kind", "") != "Name":
            return ""
        fn_name = self.any_dict_get_str(fn_d, "id", "")
        if fn_name != "bytearray" and fn_name != "bytes":
            return ""
        call_args = self.any_to_list(value_d.get("args"))
        call_kws = self.any_to_list(value_d.get("keywords"))
        call_kw_values = self.any_to_list(value_d.get("kw_values"))
        if len(call_args) != 0 or len(call_kws) != 0 or len(call_kw_values) != 0:
            return ""
        cap_expr = self._infer_byte_buffer_capacity_expr(target_name_raw)
        if cap_expr == "":
            return ""
        return "Vec::<u8>::with_capacity((" + cap_expr + ") as usize)"

    def _emit_annassign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        self._reject_unsupported_general_union_type_expr(stmt.get("annotation_type_expr"), context="AnnAssign annotation")
        self._reject_unsupported_general_union_type_expr(stmt.get("decl_type_expr"), context="AnnAssign decl_type")
        if target_kind != "Name":
            t = self.render_expr(target)
            if target_kind == "Subscript":
                v = self.render_expr(stmt.get("value"))
                self._emit_subscript_set(target, v)
                return
            v = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("annassign_assign", "{target} = {value};", {"target": t, "value": v}))
            return

        name_raw = self.any_dict_get_str(target, "id", "_")
        name = self._safe_name(name_raw)
        ann = self.any_to_str(stmt.get("annotation"))
        decl_t = self.any_to_str(stmt.get("decl_type"))
        t_east = ann if ann != "" else decl_t
        if t_east == "":
            t_east = self.get_expr_type(stmt.get("value"))
        else:
            t_east = self._refine_decl_type_from_value(t_east, stmt.get("value"))
        value_obj = stmt.get("value")
        value_t = self.normalize_type_name(self.get_expr_type(value_obj))
        if value_t in self.class_names and self._is_class_subtype(value_t, t_east):
            t_east = value_t
        prefer_hash_map = name_raw in self.current_hashmap_dict_names and self._can_hashmap_backend(t_east)
        t = self._rust_type_for_binding(name_raw, t_east)
        self.declare_in_current_scope(name_raw)
        self.declared_var_types[name_raw] = self.normalize_type_name(t_east)
        if value_obj is None:
            mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=False) else ""
            self.emit(self.syntax_line("annassign_decl_noinit", "let {mut_kw}{target}: {type};", {"mut_kw": mut_kw, "target": name, "type": t}))
            self.current_const_string_dict_bindings.pop(name_raw, None)
            self.current_non_negative_vars.discard(name_raw)
            self.current_positive_vars.discard(name_raw)
            return
        borrowed_init = self._try_render_borrowed_annassign_init(name_raw, t_east, value_obj)
        if borrowed_init != "":
            self.emit("let " + name + ": &" + t + " = " + borrowed_init + ";")
            self.current_const_string_dict_bindings.pop(name_raw, None)
            self.current_ref_vars.add(name_raw)
            self._update_name_sign_info(name_raw, value_obj)
            return
        value = self._maybe_render_preallocated_byte_buffer_init(name_raw, t_east, value_obj)
        if value == "":
            value = self._render_value_for_decl_type(value_obj, t_east, prefer_hash_map=prefer_hash_map)
        is_mut = self._should_declare_mut(name_raw, has_init_write=True)
        self._update_const_string_dict_binding(name_raw, value_obj, is_mut)
        mut_kw = "mut " if is_mut else ""
        self.emit(
            self.syntax_line(
                "annassign_decl_init",
                "let {mut_kw}{target}: {type} = {value};",
                {"mut_kw": mut_kw, "target": name, "type": t, "value": value},
            )
        )
        self._update_name_sign_info(name_raw, value_obj)

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.primary_assign_target(stmt)
        value = self.render_expr(stmt.get("value"))
        if self.any_dict_get_str(target, "kind", "") == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            if self.should_declare_name_binding(stmt, name_raw, False):
                self.declare_in_current_scope(name_raw)
                t = self.get_expr_type(stmt.get("value"))
                if t != "":
                    self.declared_var_types[name_raw] = t
                is_mut = self._should_declare_mut(name_raw, has_init_write=True)
                self._update_const_string_dict_binding(name_raw, stmt.get("value"), is_mut)
                mut_kw = "mut " if is_mut else ""
                prealloc_value = self._maybe_render_preallocated_byte_buffer_init(name_raw, t, stmt.get("value"))
                if prealloc_value != "":
                    value = prealloc_value
                elif self.any_dict_get_str(self.any_to_dict_or_empty(stmt.get("value")), "kind", "") == "Dict":
                    t_norm = self.normalize_type_name(t)
                    if name_raw in self.current_hashmap_dict_names and self._can_hashmap_backend(t_norm):
                        value = self._render_dict_expr(self.any_to_dict_or_empty(stmt.get("value")), prefer_hash_map=True)
                self.emit(self.syntax_line("assign_decl_init", "let {mut_kw}{target} = {value};", {"mut_kw": mut_kw, "target": name, "value": value}))
                self._update_name_sign_info(name_raw, stmt.get("value"))
                return
            self.current_const_string_dict_bindings.pop(name_raw, None)
            self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": name, "value": value}))
            self._update_name_sign_info(name_raw, stmt.get("value"))
            return

        if self._emit_tuple_assign(target, value):
            return

        rendered_target = self.render_expr(target)
        if self.any_dict_get_str(target, "kind", "") == "Subscript":
            owner_node = self.any_to_dict_or_empty(target.get("value"))
            owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
            if owner_t in {"bytes", "bytearray"}:
                value = "((" + value + ") as u8)"
            self._emit_subscript_set(target, value)
            return
        self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": rendered_target, "value": value}))

    def _render_subscript_lvalue(self, subscript_expr: dict[str, Any]) -> str:
        """Subscript を代入先として描画する（clone を付けない）。"""
        owner = self.render_expr(subscript_expr.get("value"))
        slice_node = subscript_expr.get("slice")
        idx = self.render_expr(slice_node)
        if self._expr_is_non_negative(slice_node):
            idx_usize = "((" + idx + ") as usize)"
        else:
            idx_i64 = "((" + idx + ") as i64)"
            idx_usize = "((if " + idx_i64 + " < 0 { (" + owner + ".len() as i64 + " + idx_i64 + ") } else { " + idx_i64 + " }) as usize)"
        return owner + "[" + idx_usize + "]"

    def _render_list_subscript_borrow_expr(self, subscript_expr: dict[str, Any]) -> str:
        """`list[T][idx]` を borrow で参照する式（`&(owner[idx])`）を返す。"""
        owner_node = self.any_to_dict_or_empty(subscript_expr.get("value"))
        owner = self.render_expr(owner_node)
        if self.any_dict_get_str(owner_node, "kind", "") == "Subscript":
            owner_owner_t = self.normalize_type_name(self.get_expr_type(owner_node.get("value")))
            if owner_owner_t.startswith("list[") or owner_owner_t.startswith("tuple[") or owner_owner_t in {"bytes", "bytearray"}:
                owner = self._render_subscript_lvalue(owner_node)
        idx_node = subscript_expr.get("slice")
        idx_txt = self.render_expr(idx_node)
        if self._expr_is_non_negative(idx_node):
            idx_usize = "((" + idx_txt + ") as usize)"
        else:
            idx_i64 = "((" + idx_txt + ") as i64)"
            idx_usize = "((if " + idx_i64 + " < 0 { (" + owner + ".len() as i64 + " + idx_i64 + ") } else { " + idx_i64 + " }) as usize)"
        return "&(" + owner + "[" + idx_usize + "])"

    def _try_render_borrowed_annassign_init(self, name_raw: str, target_type_east: str, value_obj: Any) -> str:
        """`AnnAssign` 初期化を borrow で描画できる場合は式を返す。"""
        if self._should_declare_mut(name_raw, has_init_write=True):
            return ""
        t_norm = self.normalize_type_name(target_type_east)
        if t_norm == "" or self._is_copy_type(t_norm):
            return ""
        value_d = self.any_to_dict_or_empty(value_obj)
        if self.any_dict_get_str(value_d, "kind", "") != "Subscript":
            return ""
        owner_node = self.any_to_dict_or_empty(value_d.get("value"))
        owner_kind = self.any_dict_get_str(owner_node, "kind", "")
        if owner_kind != "Name" and owner_kind != "Attribute":
            return ""
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        if not owner_t.startswith("list["):
            return ""
        elem_t = self._list_elem_type(owner_t)
        if elem_t == "":
            return ""
        if elem_t != t_norm:
            if not (elem_t in self.class_names and self._is_class_subtype(elem_t, t_norm)):
                return ""
        return self._render_list_subscript_borrow_expr(value_d)

    def _collect_subscript_chain(self, subscript_expr: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """`a[b][c]` を `(a, [a[b], a[b][c]])` 形式に分解する。"""
        chain: list[dict[str, Any]] = []
        cur = self.any_to_dict_or_empty(subscript_expr)
        while self.any_dict_get_str(cur, "kind", "") == "Subscript":
            chain.append(cur)
            cur = self.any_to_dict_or_empty(cur.get("value"))
        chain.reverse()
        return cur, chain

    def _emit_subscript_set(self, subscript_expr: dict[str, Any], value_expr: str) -> None:
        """Subscript 代入を borrow-safe な `let idx` 形式で出力する。"""
        owner_node = self.any_to_dict_or_empty(subscript_expr.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        if owner_t.startswith("dict["):
            key_t, _val_t = self._dict_key_value_types(owner_t)
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(subscript_expr.get("slice"))
            key_expr = self._coerce_dict_key_expr(key_expr, key_t)
            self.emit(owner_expr + ".insert(" + key_expr + ", " + value_expr + ");")
            return

        base_node, chain = self._collect_subscript_chain(subscript_expr)
        if self.any_dict_get_str(base_node, "kind", "") == "Name":
            base_name_raw = self.any_dict_get_str(base_node, "id", "")
            self.current_const_string_dict_bindings.pop(base_name_raw, None)
        if len(chain) == 0:
            self.emit(self._render_subscript_lvalue(subscript_expr) + " = " + value_expr + ";")
            return

        owner_expr = self.render_expr(base_node)
        i = 0
        while i < len(chain):
            level = self.any_to_dict_or_empty(chain[i])
            slice_node = self.any_to_dict_or_empty(level.get("slice"))
            if self.any_dict_get_str(slice_node, "kind", "") == "Slice":
                self.emit(self._render_subscript_lvalue(subscript_expr) + " = " + value_expr + ";")
                return
            idx_txt = self.render_expr(slice_node)
            idx_tmp = self.next_tmp("__idx")
            if self._expr_is_non_negative(slice_node):
                self.emit("let " + idx_tmp + " = ((" + idx_txt + ") as usize);")
            else:
                idx_i64_tmp = self.next_tmp("__idx_i64")
                self.emit("let " + idx_i64_tmp + " = ((" + idx_txt + ") as i64);")
                self.emit(
                    "let "
                    + idx_tmp
                    + " = if "
                    + idx_i64_tmp
                    + " < 0 { ("
                    + owner_expr
                    + ".len() as i64 + "
                    + idx_i64_tmp
                    + ") as usize } else { "
                    + idx_i64_tmp
                    + " as usize };"
                )
            owner_expr = owner_expr + "[" + idx_tmp + "]"
            i += 1
        self.emit(owner_expr + " = " + value_expr + ";")

    def _emit_tuple_assign(self, target_node: dict[str, Any], value_expr: str) -> bool:
        """Tuple unpack 代入を `tmp.N` へ lower する（任意要素数対応）。"""
        if self.any_dict_get_str(target_node, "kind", "") != "Tuple":
            return False
        targets = self.tuple_elements(target_node)
        if len(targets) == 0:
            return False
        tmp_name = self.next_tmp("__tmp")
        self.emit("let " + tmp_name + " = " + value_expr + ";")
        i = 0
        while i < len(targets):
            elem = self.any_to_dict_or_empty(targets[i])
            item_expr = tmp_name + "." + str(i)
            elem_kind = self.any_dict_get_str(elem, "kind", "")
            if elem_kind == "Name":
                name_raw = self.any_dict_get_str(elem, "id", "")
                name = self._safe_name(name_raw)
                if name_raw != "" and not self.is_declared(name_raw):
                    self.declare_in_current_scope(name_raw)
                    mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=True) else ""
                    self.emit("let " + mut_kw + name + " = " + item_expr + ";")
                else:
                    self.emit(name + " = " + item_expr + ";")
                i += 1
                continue
            if elem_kind == "Subscript":
                self._emit_subscript_set(elem, item_expr)
                i += 1
                continue
            self.emit(self.render_expr(elem) + " = " + item_expr + ";")
            i += 1
        return True

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target_obj = stmt.get("target")
        value_obj = stmt.get("value")
        target, value, mapped = self.render_augassign_basic(stmt, self.aug_ops, "+=")
        target_t = self.normalize_type_name(self.get_expr_type(target_obj))
        value_t = self.normalize_type_name(self.get_expr_type(value_obj))
        if self._is_any_type(value_t):
            self.uses_pyany = True
            if self._is_int_type(target_t):
                value = "py_any_to_i64(&" + value + ")"
            elif self._is_float_type(target_t):
                value = "py_any_to_f64(&(" + value + "))"
            elif target_t == "bool":
                value = "py_any_to_bool(&" + value + ")"
            elif target_t == "str" and mapped == "+=":
                value = "py_any_to_string(&" + value + ")"
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))
        target_d = self.any_to_dict_or_empty(target_obj)
        if self.any_dict_get_str(target_d, "kind", "") == "Name":
            name_raw = self.any_dict_get_str(target_d, "id", "")
            self.current_const_string_dict_bindings.pop(name_raw, None)
            self.current_non_negative_vars.discard(name_raw)
            self.current_positive_vars.discard(name_raw)

    def _collect_class_base_map(self, body: list[dict[str, Any]]) -> dict[str, str]:
        """ClassDef から `child -> base` の継承表を抽出する。"""
        out: dict[str, str] = {}
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") != "ClassDef":
                continue
            child = self.any_to_str(stmt.get("name"))
            if child == "":
                continue
            base = self.any_to_str(stmt.get("base"))
            if base != "":
                out[child] = self.normalize_type_name(base)
        return out

    def _is_inheritance_class(self, class_name: str) -> bool:
        cls = self.normalize_type_name(class_name)
        if cls == "":
            return False
        if cls in self.class_base_map:
            return True
        for base in self.class_base_map.values():
            if self.normalize_type_name(base) == cls:
                return True
        return False

    def _class_trait_name(self, class_name: str) -> str:
        return "__pytra_trait_" + self._safe_name(class_name)

    def _iter_class_ancestors(self, class_name: str) -> list[str]:
        out: list[str] = []
        cur = self.normalize_type_name(class_name)
        seen: set[str] = set()
        while cur != "" and cur not in seen:
            out.append(cur)
            seen.add(cur)
            cur = self.normalize_type_name(self.class_base_map.get(cur, ""))
        return out

    def _trait_method_signature(self, fn_node: dict[str, Any], method_name: str) -> str:
        arg_order = self.any_to_str_list(fn_node.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn_node.get("arg_types"))
        params: list[str] = []
        for arg_name in arg_order:
            if arg_name == "self":
                continue
            arg_east_t = self.any_to_str(arg_types.get(arg_name))
            arg_t = self._rust_type(arg_east_t)
            if self._should_pass_method_arg_by_ref_type(arg_east_t):
                arg_t = self._borrowed_arg_type_text(arg_east_t, arg_t, allow_trait_impl=False)
            params.append(self._safe_name(arg_name) + ": " + arg_t)
        ret_t = self._rust_type(self.normalize_type_name(self.any_to_str(fn_node.get("return_type"))))
        ret_txt = "" if ret_t == "()" else " -> " + ret_t
        args_txt = "&self"
        if len(params) > 0:
            args_txt += ", " + ", ".join(params)
        return "fn " + self._safe_name(method_name) + "(" + args_txt + ")" + ret_txt

    def _find_method_owner_for_class(self, class_name: str, method_name: str) -> str:
        for anc in self._iter_class_ancestors(class_name):
            methods = self.class_method_defs.get(anc, {})
            if method_name in methods:
                return anc
        return ""

    def _trait_decl_method_defs(self, class_name: str) -> dict[str, dict[str, Any]]:
        own = self.class_method_defs.get(class_name, {})
        if len(own) == 0:
            return {}
        inherited: set[str] = set()
        ancestors = self._iter_class_ancestors(class_name)
        i = 1
        while i < len(ancestors):
            anc = ancestors[i]
            for method_name in self.class_method_defs.get(anc, {}).keys():
                inherited.add(method_name)
            i += 1
        out: dict[str, dict[str, Any]] = {}
        for method_name, method_node in own.items():
            if method_name in inherited:
                continue
            out[method_name] = method_node
        return out

    def _emit_inheritance_trait_declarations(self) -> None:
        targets = [c for c in sorted(self.class_names) if self._is_inheritance_class(c)]
        if len(targets) == 0:
            return
        for cls in targets:
            trait_name = self._class_trait_name(cls)
            base = self.normalize_type_name(self.class_base_map.get(cls, ""))
            header = "trait " + trait_name
            if base != "":
                header += ": " + self._class_trait_name(base)
            header += " {"
            self.emit(header)
            self.indent += 1
            method_defs = self._trait_decl_method_defs(cls)
            for method_name in sorted(method_defs.keys()):
                method_node = method_defs[method_name]
                self.emit(self._trait_method_signature(method_node, method_name) + ";")
            self.indent -= 1
            self.emit("}")
            self.emit("")

    def _emit_inheritance_trait_impls_for_class(self, class_name_raw: str) -> None:
        if not self._is_inheritance_class(class_name_raw):
            return
        cls = self.normalize_type_name(class_name_raw)
        cls_safe = self._safe_name(cls)
        for anc in self._iter_class_ancestors(cls):
            if not self._is_inheritance_class(anc):
                continue
            anc_methods = self._trait_decl_method_defs(anc)
            self.emit(f"impl {self._class_trait_name(anc)} for {cls_safe} {{")
            self.indent += 1
            for method_name in sorted(anc_methods.keys()):
                method_node = anc_methods[method_name]
                self.emit(self._trait_method_signature(method_node, method_name) + " {")
                self.indent += 1
                call_args: list[str] = []
                arg_order = self.any_to_str_list(method_node.get("arg_order"))
                for arg_name in arg_order:
                    if arg_name == "self":
                        continue
                    call_args.append(self._safe_name(arg_name))
                owner = self._find_method_owner_for_class(cls, method_name)
                if owner == "":
                    owner = anc
                owner_safe = self._safe_name(owner)
                recv = "self" if owner == cls else "&" + owner_safe + "::new()"
                call_txt = owner_safe + "::" + self._safe_name(method_name) + "(" + recv
                if len(call_args) > 0:
                    call_txt += ", " + ", ".join(call_args)
                call_txt += ")"
                ret_t = self._rust_type(self.normalize_type_name(self.any_to_str(method_node.get("return_type"))))
                if ret_t == "()":
                    self.emit(call_txt + ";")
                else:
                    self.emit("return " + call_txt + ";")
                self.indent -= 1
                self.emit("}")
            self.indent -= 1
            self.emit("}")
            self.emit("")

    def _is_class_subtype(self, actual: str, expected: str) -> bool:
        """`actual` が `expected` の派生型かを継承表で判定する。"""
        cur = self.normalize_type_name(actual)
        want = self.normalize_type_name(expected)
        if cur == "" or want == "":
            return False
        if cur == want:
            return True
        visited: set[str] = set()
        while cur != "" and cur not in visited:
            visited.add(cur)
            if cur == want:
                return True
            if cur not in self.class_base_map:
                break
            cur = self.normalize_type_name(self.class_base_map[cur])
        return False

    def _render_isinstance_type_check(self, value_expr: str, value_node: Any, type_name: str) -> str:
        """`isinstance(x, T)` の `T` を Rust 式へ lower する。"""
        expected_tid = self._builtin_type_id_expr(type_name)
        if expected_tid == "":
            return "false"
        actual = self.normalize_type_name(self.get_expr_type(value_node))
        if self._is_any_type(actual):
            self.uses_pyany = True
        self.uses_isinstance_runtime = True
        return "({ py_register_generated_type_info(); py_isinstance(&" + value_expr + ", " + expected_tid + ") })"

    def _render_isinstance_call(self, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """`isinstance(...)` 呼び出しを Rust へ lower する。"""
        if len(rendered_args) != 2:
            return "false"
        rhs_node = self.any_to_dict_or_empty(arg_nodes[1] if len(arg_nodes) > 1 else None)
        rhs_kind = self.any_dict_get_str(rhs_node, "kind", "")
        if rhs_kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, rhs_name)
            if lowered != "":
                return lowered
            return "false"
        if rhs_kind == "Tuple":
            checks: list[str] = []
            for elt in self.tuple_elements(rhs_node):
                e_node = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(e_node, "kind", "") != "Name":
                    continue
                e_name = self.any_dict_get_str(e_node, "id", "")
                lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, e_name)
                if lowered != "":
                    checks.append(lowered)
            if len(checks) > 0:
                return "(" + " || ".join(checks) + ")"
        return "false"

    def _render_type_id_expr(self, expr_node: Any) -> str:
        """type_id 式を Rust runtime 互換の識別子へ変換する。"""
        expr_d = self.any_to_dict_or_empty(expr_node)
        if self.any_dict_get_str(expr_d, "kind", "") == "Name":
            name = self.any_dict_get_str(expr_d, "id", "")
            builtin_tid = self._builtin_type_id_expr(name)
            if builtin_tid != "":
                return builtin_tid
            normalized = self.normalize_type_name(name)
            if normalized in self.class_names:
                return self._safe_name(normalized) + "::PYTRA_TYPE_ID"
        return self.render_expr(expr_node)

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        left = self.render_expr(left_node)
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        if len(ops) == 0 or len(comps) == 0:
            return "false"
        terms: list[str] = []
        cur_left_node = left_node
        cur_left = left
        pair_count = len(ops)
        if len(comps) < pair_count:
            pair_count = len(comps)
        i = 0
        while i < pair_count:
            right_node = self.any_to_dict_or_empty(comps[i])
            right = self.render_expr(right_node)
            op = ops[i]
            if op == "In" or op == "NotIn":
                terms.append("(" + self._render_membership_compare_term(op, cur_left, cur_left_node, right, right_node) + ")")
            else:
                mapped = self.cmp_ops.get(op, "==")
                cmp_left = cur_left
                cmp_right = right
                if mapped in {"==", "!="}:
                    lit_right = self._string_constant_literal(right_node)
                    lit_left = self._string_constant_literal(cur_left_node)
                    if lit_right != "":
                        cmp_right = lit_right
                    if lit_left != "":
                        cmp_left = lit_left
                terms.append("(" + cmp_left + " " + mapped + " " + cmp_right + ")")
            cur_left_node = right_node
            cur_left = right
            i += 1
        if len(terms) == 0:
            return "false"
        if len(terms) == 1:
            return terms[0]
        return "(" + " && ".join(terms) + ")"

    def _render_membership_compare_term(
        self,
        op: str,
        left_expr: str,
        left_node: dict[str, Any],
        right_expr: str,
        right_node: dict[str, Any],
    ) -> str:
        """`in` / `not in` を owner 型に応じて lower する。"""
        right_t = self.normalize_type_name(self.get_expr_type(right_node))
        left_t = self.normalize_type_name(self.get_expr_type(left_node))
        term = left_expr + " == " + right_expr
        if right_t.startswith("dict["):
            key_t, _val_t = self._dict_key_value_types(right_t)
            key_expr = self._coerce_dict_key_expr(left_expr, key_t, require_owned=False)
            term = right_expr + ".contains_key(&" + key_expr + ")"
        elif right_t == "str":
            if left_t == "str":
                term = right_expr + ".contains(&(" + left_expr + "))"
            else:
                term = right_expr + ".contains(&(" + left_expr + ").to_string())"
        elif (
            right_t.startswith("list[")
            or right_t.startswith("tuple[")
            or right_t.startswith("set[")
            or right_t in {"bytes", "bytearray"}
        ):
            term = right_expr + ".contains(&(" + left_expr + "))"
        if op == "NotIn":
            return "!(" + term + ")"
        return term

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp を Rust if 式へ描画する。"""
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for cast_info in casts:
            on = self.any_to_str(cast_info.get("on"))
            to_t = self.any_to_str(cast_info.get("to"))
            if on == "body":
                body = self.apply_cast(body, to_t)
            elif on == "orelse":
                orelse = self.apply_cast(orelse, to_t)
        test_expr = self.render_cond(expr.get("test"))
        return self.render_ifexp_common(
            test_expr,
            body,
            orelse,
            test_node=self.any_to_dict_or_empty(expr.get("test")),
            fold_bool_literal=True,
        )

    def render_ifexp_common(
        self,
        test_expr: str,
        body_expr: str,
        orelse_expr: str,
        *,
        test_node: dict[str, Any] | None = None,
        fold_bool_literal: bool = False,
    ) -> str:
        """Rust の if 式として IfExp を描画する。"""
        if fold_bool_literal:
            node = test_node if isinstance(test_node, dict) else {}
            if self._node_kind_from_dict(node) == "Constant" and isinstance(node.get("value"), bool):
                return body_expr if bool(node.get("value")) else orelse_expr
            if self._node_kind_from_dict(node) == "Name":
                ident = self.any_to_str(node.get("id"))
                if ident == "True":
                    return body_expr
                if ident == "False":
                    return orelse_expr
            t = test_expr.strip()
            if t == "true":
                return body_expr
            if t == "false":
                return orelse_expr
        return "(if " + test_expr + " { " + body_expr + " } else { " + orelse_expr + " })"

    def _render_range_expr(self, expr_d: dict[str, Any]) -> str:
        """RangeExpr を Rust range 式へ描画する。"""
        start = self.render_expr(expr_d.get("start"))
        stop = self.render_expr(expr_d.get("stop"))
        step = self.render_expr(expr_d.get("step"))
        if step == "1":
            return "((" + start + ")..(" + stop + "))"
        return "((" + start + ")..(" + stop + ")).step_by(((" + step + ") as usize))"

    def _render_list_comp(self, expr_d: dict[str, Any]) -> str:
        """最小限の ListComp（単一 generator）を Rust へ描画する。"""
        generators = self.any_to_list(expr_d.get("generators"))
        if len(generators) != 1:
            return "vec![]"
        gen = self.any_to_dict_or_empty(generators[0])
        if len(self.any_to_list(gen.get("ifs"))) > 0:
            return "vec![]"
        target_node = self.any_to_dict_or_empty(gen.get("target"))
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind != "Name":
            return "vec![]"
        target_name = self._safe_name(self.any_dict_get_str(target_node, "id", "_item"))
        iter_node = self.any_to_dict_or_empty(gen.get("iter"))
        iter_expr = self.render_expr(iter_node)
        if self.any_dict_get_str(iter_node, "kind", "") == "RangeExpr":
            iter_expr = self._render_range_expr(iter_node)
        elt_expr = self.render_expr(expr_d.get("elt"))
        return "(" + iter_expr + ").map(|" + target_name + "| " + elt_expr + ").collect::<Vec<_>>()"

    def _render_binop(self, expr: dict[str, Any]) -> str:
        op = self.any_to_str(expr.get("op"))
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        right_node = self.any_to_dict_or_empty(expr.get("right"))
        left_t = self.normalize_type_name(self.get_expr_type(left_node))
        right_t = self.normalize_type_name(self.get_expr_type(right_node))
        if op == "Mult":
            left_kind = self.any_dict_get_str(left_node, "kind", "")
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            if left_kind == "List":
                left_items = self.any_to_list(left_node.get("elts"))
                if len(left_items) == 0:
                    left_items = self.any_to_list(left_node.get("elements"))
                if len(left_items) == 1:
                    item_txt = self.render_expr(left_items[0])
                    repeat_txt = self.render_expr(right_node)
                    return "vec![" + item_txt + "; ((" + repeat_txt + ") as usize)]"
            if right_kind == "List":
                right_items = self.any_to_list(right_node.get("elts"))
                if len(right_items) == 0:
                    right_items = self.any_to_list(right_node.get("elements"))
                if len(right_items) == 1:
                    item_txt = self.render_expr(right_items[0])
                    repeat_txt = self.render_expr(left_node)
                    return "vec![" + item_txt + "; ((" + repeat_txt + ") as usize)]"
        left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, self.any_dict_get_str(expr, "op", ""), is_right=False)
        right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, self.any_dict_get_str(expr, "op", ""), is_right=True)
        casts = self._dict_stmt_list(expr.get("casts"))
        for cast_info in casts:
            on = self.any_to_str(cast_info.get("on"))
            to_t = self.any_to_str(cast_info.get("to"))
            if on == "left":
                left = self.apply_cast(left, to_t)
                if self.normalize_type_name(to_t) == "str":
                    left_t = "str"
            elif on == "right":
                right = self.apply_cast(right, to_t)
                if self.normalize_type_name(to_t) == "str":
                    right_t = "str"
        if op == "Add" and (left_t == "str" or right_t == "str"):
            flat_terms = self._try_flatten_string_add_terms(expr)
            if flat_terms is not None and len(flat_terms) >= 2:
                return "format!(\"" + ("{}" * len(flat_terms)) + "\", " + ", ".join(flat_terms) + ")"
            return "format!(\"{}{}\", " + left + ", " + right + ")"
        custom = self.hook_on_render_binop(expr, left, right)
        if custom != "":
            return custom
        mapped = self.bin_ops.get(op, "+")
        return left + " " + mapped + " " + right

    def _try_flatten_string_add_terms(self, expr_node: Any) -> list[str] | None:
        """cast無しの `str` 連結 Add を平坦化し、`format!` 引数列へ変換する。"""
        d = self.any_to_dict_or_empty(expr_node)
        if self.any_dict_get_str(d, "kind", "") != "BinOp":
            return None
        if self.any_dict_get_str(d, "op", "") != "Add":
            return None
        if len(self._dict_stmt_list(d.get("casts"))) > 0:
            return None

        left_node = self.any_to_dict_or_empty(d.get("left"))
        right_node = self.any_to_dict_or_empty(d.get("right"))
        left_t = self.normalize_type_name(self.get_expr_type(left_node))
        right_t = self.normalize_type_name(self.get_expr_type(right_node))
        if left_t != "str" and right_t != "str":
            return None

        out: list[str] = []
        left_terms = self._try_flatten_string_add_terms(left_node)
        if left_terms is not None:
            out.extend(left_terms)
        else:
            out.append(self.render_expr(left_node))

        right_terms = self._try_flatten_string_add_terms(right_node)
        if right_terms is not None:
            out.extend(right_terms)
        else:
            out.append(self.render_expr(right_node))

        return out

    def _should_clone_call_arg_type(self, arg_type: str) -> bool:
        t = self.normalize_type_name(arg_type)
        if t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        if t in self.class_names:
            return True
        return False

    def _infer_expr_type_for_call_arg(self, node: Any) -> str:
        t = self.normalize_type_name(self.get_expr_type(node))
        if t != "" and t != "unknown":
            return t
        d = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(d, "kind", "") == "Attribute":
            owner = self.any_to_dict_or_empty(d.get("value"))
            owner_t = self.normalize_type_name(self.get_expr_type(owner))
            attr = self.any_dict_get_str(d, "attr", "")
            field_types = self.class_field_types.get(owner_t, {})
            if attr in field_types:
                return self.normalize_type_name(field_types[attr])
        return t

    def _clone_owned_call_args(self, rendered_args: list[str], arg_nodes: list[Any]) -> list[str]:
        out = list(rendered_args)
        i = 0
        while i < len(arg_nodes) and i < len(out):
            t = self._infer_expr_type_for_call_arg(arg_nodes[i])
            if self._should_clone_call_arg_type(t):
                out[i] = "(" + out[i] + ").clone()"
            i += 1
        return out

    def _render_by_ref_call_arg(self, arg_txt: str, arg_node: Any) -> str:
        """`&T` / `&str` 引数向けに最小コストの渡し方を選ぶ。"""
        str_lit = self._string_constant_literal(arg_node)
        if str_lit != "":
            return str_lit
        arg_d = self.any_to_dict_or_empty(arg_node)
        if self.any_dict_get_str(arg_d, "kind", "") == "Name":
            raw = self.any_dict_get_str(arg_d, "id", "")
            if raw in self.current_ref_vars:
                return arg_txt
        if arg_txt.startswith("&"):
            return arg_txt
        return "&(" + arg_txt + ")"

    def _call_is_in_return_expr(self, expr: dict[str, Any]) -> bool:
        meta = self.any_to_dict_or_empty(expr.get("meta"))
        non_escape = self.any_to_dict_or_empty(meta.get("non_escape_callsite"))
        return bool(non_escape.get("in_return_expr"))

    def _render_return_expr(self, expr: Any) -> str:
        expr_d = self.any_to_dict_or_empty(expr)
        if self.any_dict_get_str(expr_d, "kind", "") == "Call":
            fn_node = self.any_to_dict_or_empty(expr_d.get("func"))
            fn_name = self.any_dict_get_str(fn_node, "id", "")
            args = self.any_to_list(expr_d.get("args"))
            if fn_name in {"bytes", "bytearray"} and len(args) == 1:
                arg_node = args[0]
                arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
                if arg_t in {"bytes", "bytearray"}:
                    return self.render_expr(arg_node)
        return self.render_expr(expr)

    def _resolved_runtime_call(self, expr: dict[str, Any]) -> str:
        runtime_call = self.any_dict_get_str(expr, "runtime_call", "")
        if runtime_call != "":
            return runtime_call
        resolved_runtime_call = self.any_dict_get_str(expr, "resolved_runtime_call", "")
        if resolved_runtime_call != "":
            return resolved_runtime_call
        return ""

    def _render_call(self, expr: dict[str, Any]) -> str:
        semantic_tag = self.any_dict_get_str(expr, "semantic_tag", "")
        runtime_call = self._resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and semantic_tag != "stdlib.symbol.Path" and runtime_call == "":
            raise RuntimeError("rust emitter: unresolved stdlib runtime call: " + semantic_tag)

        parts = self.prepare_call_context(expr)
        fn_node = self.any_to_dict_or_empty(parts.get("fn"))
        fn_kind = self.any_dict_get_str(fn_node, "kind", "")
        args = self.any_to_list(parts.get("args"))
        arg_nodes = self.any_to_list(parts.get("arg_nodes"))
        kw_values = self.any_to_list(parts.get("kw_values"))

        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(self.any_to_str(args[i]))
            i += 1
        rendered_kw_values: list[str] = []
        j = 0
        while j < len(kw_values):
            rendered_kw_values.append(self.any_to_str(kw_values[j]))
            j += 1
        merged_args = self.merge_call_kw_values(rendered_args, rendered_kw_values)

        if fn_kind == "Name":
            fn_name_raw = self.any_dict_get_str(fn_node, "id", "")
            fn_name = self._safe_name(fn_name_raw)
            if fn_name_raw.startswith("py_assert_"):
                assert_suffix = fn_name_raw[10:]
                if assert_suffix == "stdout":
                    return "(\"True\").to_string()"
                if len(merged_args) == 0:
                    return "true"
                return "({ let _ = (" + ", ".join(merged_args) + "); true })"
            if fn_name_raw in self.class_names:
                ctor_args = self._clone_owned_call_args(merged_args, arg_nodes)
                field_types = self.class_field_types.get(fn_name_raw, {})
                if len(field_types) == len(ctor_args):
                    coerced: list[str] = []
                    idx = 0
                    for _field_name, field_t in field_types.items():
                        if idx >= len(ctor_args):
                            break
                        arg_txt = ctor_args[idx]
                        if self.normalize_type_name(field_t) == "str":
                            arg_txt = self._ensure_string_owned(arg_txt)
                        coerced.append(arg_txt)
                        idx += 1
                    if len(coerced) == len(ctor_args):
                        ctor_args = coerced
                return f"{self._safe_name(fn_name_raw)}::new(" + ", ".join(ctor_args) + ")"
            if fn_name_raw == "isinstance":
                return self._render_isinstance_call(rendered_args, arg_nodes)
            if fn_name_raw == "enumerate" and len(merged_args) == 1:
                arg_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
                if arg_t.startswith("list["):
                    iter_expr = self._render_list_iter_expr(
                        merged_args[0], arg_t, self._can_borrow_iter_node(arg_node)
                    )
                    return iter_expr + ".enumerate().map(|(i, v)| (i as i64, v))"
                return "(" + merged_args[0] + ").clone().into_iter().enumerate().map(|(i, v)| (i as i64, v))"
            if fn_name_raw == "bytearray":
                if len(merged_args) == 0:
                    return "Vec::<u8>::new()"
                if len(merged_args) == 1:
                    arg0_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                    arg0_t = self.normalize_type_name(self.get_expr_type(arg0_node))
                    if self._is_int_type(arg0_t):
                        return "vec![0u8; (" + merged_args[0] + ") as usize]"
                    if arg0_t == "bytes" or arg0_t == "bytearray" or arg0_t.startswith("list["):
                        return "(" + merged_args[0] + ").clone()"
                    return "(" + merged_args[0] + ").into_iter().map(|v| v as u8).collect::<Vec<u8>>()"
                return "Vec::<u8>::new()"
            if fn_name_raw == "bytes":
                if len(merged_args) == 0:
                    return "Vec::<u8>::new()"
                arg0_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg0_t = self.normalize_type_name(self.get_expr_type(arg0_node))
                if arg0_t == "str":
                    return "(" + merged_args[0] + ").as_bytes().to_vec()"
                if self._call_is_in_return_expr(expr) and arg0_t in {"bytes", "bytearray"}:
                    return merged_args[0]
                return "(" + merged_args[0] + ").clone()"
            if fn_name_raw == "print":
                if len(merged_args) == 0:
                    return "println!(\"\")"
                if len(merged_args) == 1:
                    return "println!(\"{}\", " + merged_args[0] + ")"
                placeholders: list[str] = []
                for _ in merged_args:
                    placeholders.append("{}")
                return "println!(\"" + " ".join(placeholders) + "\", " + ", ".join(merged_args) + ")"
            if fn_name_raw == "len" and len(merged_args) == 1:
                arg_type = self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None)
                if arg_type.startswith("dict["):
                    return merged_args[0] + ".len() as i64"
                return merged_args[0] + ".len() as i64"
            if fn_name_raw == "max" and len(merged_args) >= 2:
                expr_txt = merged_args[0]
                k = 1
                while k < len(merged_args):
                    rhs = merged_args[k]
                    expr_txt = "(if " + expr_txt + " > " + rhs + " { " + expr_txt + " } else { " + rhs + " })"
                    k += 1
                return expr_txt
            if fn_name_raw == "min" and len(merged_args) >= 2:
                expr_txt = merged_args[0]
                k = 1
                while k < len(merged_args):
                    rhs = merged_args[k]
                    expr_txt = "(if " + expr_txt + " < " + rhs + " { " + expr_txt + " } else { " + rhs + " })"
                    k += 1
                return expr_txt
            if fn_name_raw == "str" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_string(&" + merged_args[0] + ")"
                return "(" + merged_args[0] + ").to_string()"
            if fn_name_raw == "int" and len(merged_args) == 1:
                arg_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
                if (arg_t == "" or arg_t == "unknown") and len(arg_nodes) > 0:
                    arg_d = self.any_to_dict_or_empty(arg_node)
                    if self.any_dict_get_str(arg_d, "kind", "") == "Attribute":
                        owner_node = self.any_to_dict_or_empty(arg_d.get("value"))
                        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
                        attr_name = self.any_dict_get_str(arg_d, "attr", "")
                        field_types = self.class_field_types.get(owner_t, {})
                        if attr_name in field_types:
                            arg_t = self.normalize_type_name(field_types[attr_name])
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_i64(&" + merged_args[0] + ")"
                if arg_t == "str":
                    return "((" + merged_args[0] + ").parse::<i64>().unwrap_or(0))"
                return "((" + merged_args[0] + ") as i64)"
            if fn_name_raw == "float" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_f64(&(" + merged_args[0] + "))"
                return "((" + merged_args[0] + ") as f64)"
            if fn_name_raw == "bool" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_bool(&" + merged_args[0] + ")"
                return "((" + merged_args[0] + ") != 0)"
            imported_sym = self._resolve_imported_symbol(fn_name_raw)
            imported_mod = self.any_dict_get_str(imported_sym, "module", "")
            if self._is_image_utils_module(imported_mod) and len(merged_args) > 0:
                call_args = self._apply_image_runtime_ref_args(list(merged_args))
                return fn_name + "(" + ", ".join(call_args) + ")"
            ref_modes = self.function_arg_ref_modes.get(fn_name, [])
            call_args: list[str] = []
            i = 0
            while i < len(merged_args):
                arg_txt = merged_args[i]
                by_ref = i < len(ref_modes) and ref_modes[i]
                if by_ref:
                    arg_node = arg_nodes[i] if i < len(arg_nodes) else None
                    call_args.append(self._render_by_ref_call_arg(arg_txt, arg_node))
                else:
                    if i < len(arg_nodes):
                        t = self._infer_expr_type_for_call_arg(arg_nodes[i])
                        if self._should_clone_call_arg_type(t):
                            arg_txt = "(" + arg_txt + ").clone()"
                    call_args.append(arg_txt)
                i += 1
            return fn_name + "(" + ", ".join(call_args) + ")"

        if fn_kind == "Attribute":
            owner_expr = self.render_expr(fn_node.get("value"))
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            if self.any_dict_get_str(owner_node, "kind", "") == "Call":
                super_fn = self.any_to_dict_or_empty(owner_node.get("func"))
                if self.any_dict_get_str(super_fn, "kind", "") == "Name" and self.any_dict_get_str(super_fn, "id", "") == "super":
                    attr_raw = self.any_dict_get_str(fn_node, "attr", "")
                    if attr_raw == "__init__":
                        return "()"
                    base_name = self.normalize_type_name(self.class_base_map.get(self.current_class_name, ""))
                    if base_name == "":
                        return "()"
                    base_safe = self._safe_name(base_name)
                    call_txt = base_safe + "::" + self._safe_name(attr_raw) + "(&" + base_safe + "::new()"
                    if len(merged_args) > 0:
                        call_txt += ", " + ", ".join(merged_args)
                    call_txt += ")"
                    return call_txt
            owner_type = self.get_expr_type(owner_node)
            owner_ctx = self.resolve_attribute_owner_context(fn_node.get("value"), owner_expr)
            owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
            attr_raw = self.any_dict_get_str(fn_node, "attr", "")
            attr = self._safe_name(attr_raw)
            if owner_mod != "":
                if self._is_image_utils_module(owner_mod) and len(merged_args) > 0:
                    call_args = self._apply_image_runtime_ref_args(list(merged_args))
                    return owner_mod.replace(".", "::") + "::" + attr_raw + "(" + ", ".join(call_args) + ")"
                call_args = self._clone_owned_call_args(merged_args, arg_nodes)
                return owner_mod.replace(".", "::") + "::" + attr_raw + "(" + ", ".join(call_args) + ")"
            if attr_raw == "items" and len(merged_args) == 0:
                return "(" + owner_expr + ").clone().into_iter()"
            if attr_raw == "keys" and len(merged_args) == 0:
                return "(" + owner_expr + ").keys().cloned()"
            if attr_raw == "values" and len(merged_args) == 0:
                return "(" + owner_expr + ").values().cloned()"
            if owner_type == "str" and attr_raw == "isdigit" and len(merged_args) == 0:
                self.uses_string_helpers = True
                return "py_isdigit(&" + owner_expr + ")"
            if owner_type == "str" and attr_raw == "isalpha" and len(merged_args) == 0:
                self.uses_string_helpers = True
                return "py_isalpha(&" + owner_expr + ")"
            if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
                if attr_raw == "append" and len(merged_args) == 1:
                    if owner_type in {"bytes", "bytearray"}:
                        return owner_expr + ".push(((" + merged_args[0] + ") as u8))"
                    return owner_expr + ".push(" + merged_args[0] + ")"
                if attr_raw == "pop" and len(merged_args) == 0:
                    return owner_expr + ".pop().unwrap_or_default()"
                if attr_raw == "clear" and len(merged_args) == 0:
                    return owner_expr + ".clear()"
            if owner_type.startswith("dict["):
                key_t, owner_val_t = self._dict_key_value_types(owner_type)
                if attr_raw == "get" and len(merged_args) == 1:
                    if key_t == "str" and self.any_dict_get_str(owner_node, "kind", "") == "Name" and len(arg_nodes) >= 1:
                        owner_name_raw = self.any_dict_get_str(owner_node, "id", "")
                        const_lookup = self._render_const_string_dict_get(
                            owner_name_raw,
                            merged_args[0],
                            arg_nodes[0],
                            "Default::default()",
                        )
                        if const_lookup != "":
                            return const_lookup
                    key_expr = self._coerce_dict_key_expr(merged_args[0], key_t, require_owned=False)
                    return owner_expr + ".get(&" + key_expr + ").cloned().unwrap_or_default()"
                if attr_raw == "get" and len(merged_args) >= 2:
                    default_txt = merged_args[1]
                    if self._is_any_type(owner_val_t) and len(arg_nodes) >= 2:
                        self.uses_pyany = True
                        default_txt = self._render_as_pyany(arg_nodes[1])
                    if key_t == "str" and self.any_dict_get_str(owner_node, "kind", "") == "Name" and len(arg_nodes) >= 1:
                        owner_name_raw = self.any_dict_get_str(owner_node, "id", "")
                        const_lookup = self._render_const_string_dict_get(
                            owner_name_raw,
                            merged_args[0],
                            arg_nodes[0],
                            default_txt,
                        )
                        if const_lookup != "":
                            return const_lookup
                    key_expr = self._coerce_dict_key_expr(merged_args[0], key_t, require_owned=False)
                    return owner_expr + ".get(&" + key_expr + ").cloned().unwrap_or(" + default_txt + ")"
            owner_type_norm = self.normalize_type_name(owner_type)
            method_ref_modes = self.class_method_arg_ref_modes.get(owner_type_norm, {}).get(attr, [])
            if len(method_ref_modes) > 0:
                call_args: list[str] = []
                i = 0
                while i < len(merged_args):
                    arg_txt = merged_args[i]
                    by_ref = i < len(method_ref_modes) and method_ref_modes[i]
                    if by_ref:
                        arg_node = arg_nodes[i] if i < len(arg_nodes) else None
                        call_args.append(self._render_by_ref_call_arg(arg_txt, arg_node))
                    else:
                        call_args.append(arg_txt)
                    i += 1
                return owner_expr + "." + attr + "(" + ", ".join(call_args) + ")"
            return owner_expr + "." + attr + "(" + ", ".join(merged_args) + ")"

        fn_expr = self.render_expr(fn_node)
        call_args = self._clone_owned_call_args(merged_args, arg_nodes)
        return fn_expr + "(" + ", ".join(call_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを Rust へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "()"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_specific = self.hook_on_render_expr_kind_specific(kind, expr_d)
        if hook_specific != "":
            return hook_specific
        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            return self._safe_name(name)
        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "()", "()")
            if tag == "1":
                return non_str
            val = self.any_to_str(expr_d.get("value"))
            return "(" + self.quote_string_literal(val) + ").to_string()"
        if kind == "Attribute":
            if self.any_dict_get_str(expr_d, "lowered_kind", "") == "NominalAdtProjection":
                self._raise_unsupported_nominal_adt_lane(
                    lane="projection",
                    context="Attribute projection " + self.any_dict_get_str(expr_d, "attr", ""),
                )
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            semantic_tag = self.any_dict_get_str(expr_d, "semantic_tag", "")
            runtime_call = self._resolved_runtime_call(expr_d)
            if semantic_tag.startswith("stdlib.") and runtime_call == "":
                raise RuntimeError("rust emitter: unresolved stdlib runtime attribute: " + semantic_tag)
            owner_ctx = self.resolve_attribute_owner_context(owner_node, owner)
            owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
            attr_raw = self.any_dict_get_str(expr_d, "attr", "")
            if owner_mod != "":
                return owner_mod.replace(".", "::") + "::" + attr_raw
            owner_kind = self.any_dict_get_str(owner_node, "kind", "")
            attr = self._safe_name(attr_raw)
            if owner_kind == "Subscript":
                owner_owner_t = self.normalize_type_name(self.get_expr_type(owner_node.get("value")))
                owner_expr = owner
                if owner_owner_t.startswith("list[") or owner_owner_t.startswith("tuple[") or owner_owner_t in {"bytes", "bytearray"}:
                    owner_expr = self._render_subscript_lvalue(owner_node)
                attr_t = self.normalize_type_name(self.get_expr_type(expr_d))
                if self._is_copy_type(attr_t):
                    return owner_expr + "." + attr
                return "(" + owner_expr + "." + attr + ").clone()"
            return owner + "." + attr
        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            right_node = self.any_to_dict_or_empty(expr_d.get("operand"))
            right = self.render_expr(right_node)
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            simple_right = right_kind in {"Name", "Constant", "Call", "Attribute", "Subscript"}
            if op == "USub":
                return "-" + right if simple_right else "-(" + right + ")"
            if op == "Not":
                return "!" + right if simple_right else "!(" + right + ")"
            return right
        if kind == "BinOp":
            return self._render_binop(expr_d)
        if kind == "RangeExpr":
            return self._render_range_expr(expr_d)
        if kind == "Compare":
            return self._render_compare(expr_d)
        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_common(vals, op, and_token="&&", or_token="||", empty_literal="false")
        if kind == "Call":
            call_hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if call_hook != "":
                return call_hook
            return self._render_call(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        if kind == "ObjBool":
            value = self.render_expr(expr_d.get("value"))
            self.uses_pyany = True
            return "py_any_to_bool(&" + value + ")"
        if kind == "ObjLen":
            value_node = expr_d.get("value")
            value = self.render_expr(value_node)
            value_t = self.normalize_type_name(self.get_expr_type(value_node))
            if self._is_any_type(value_t):
                self.uses_pyany = True
                return (
                    "(match &" + value + " { "
                    "PyAny::Str(s) => s.len() as i64, "
                    "PyAny::Dict(d) => d.len() as i64, "
                    "PyAny::List(xs) => xs.len() as i64, "
                    "PyAny::Set(xs) => xs.len() as i64, "
                    "PyAny::None => 0, "
                    "_ => 0 })"
                )
            return value + ".len() as i64"
        if kind == "ObjStr":
            value = self.render_expr(expr_d.get("value"))
            self.uses_pyany = True
            return "py_any_to_string(&" + value + ")"
        if kind == "ObjIterInit":
            value = self.render_expr(expr_d.get("value"))
            return "iter(" + value + ")"
        if kind == "ObjIterNext":
            iter_expr = self.render_expr(expr_d.get("iter"))
            return "next(" + iter_expr + ")"
        if kind == "ObjTypeId":
            value = self.render_expr(expr_d.get("value"))
            self.uses_isinstance_runtime = True
            return "py_runtime_type_id(&" + value + ")"
        if kind == "IsInstance":
            value = self.render_expr(expr_d.get("value"))
            expected = self._render_type_id_expr(expr_d.get("expected_type_id"))
            self.uses_isinstance_runtime = True
            return "({ py_register_generated_type_info(); py_isinstance(&" + value + ", " + expected + ") })"
        if kind == "IsSubtype":
            actual = self._render_type_id_expr(expr_d.get("actual_type_id"))
            expected = self._render_type_id_expr(expr_d.get("expected_type_id"))
            self.uses_isinstance_runtime = True
            return "({ py_register_generated_type_info(); py_is_subtype(" + actual + ", " + expected + ") })"
        if kind == "IsSubclass":
            actual = self._render_type_id_expr(expr_d.get("actual_type_id"))
            expected = self._render_type_id_expr(expr_d.get("expected_type_id"))
            self.uses_isinstance_runtime = True
            return "({ py_register_generated_type_info(); py_issubclass(" + actual + ", " + expected + ") })"
        if kind == "Box":
            self.uses_pyany = True
            return self._render_as_pyany(expr_d.get("value"))
        if kind == "Unbox":
            value = self.render_expr(expr_d.get("value"))
            target_t = self.normalize_type_name(self.any_to_str(expr_d.get("target")))
            if target_t == "":
                target_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
            if self._is_int_type(target_t):
                self.uses_pyany = True
                return "py_any_to_i64(&" + value + ")"
            if self._is_float_type(target_t):
                self.uses_pyany = True
                return "py_any_to_f64(&(" + value + "))"
            if target_t == "bool":
                self.uses_pyany = True
                return "py_any_to_bool(&" + value + ")"
            if target_t == "str":
                self.uses_pyany = True
                return "py_any_to_string(&" + value + ")"
            if self._is_dict_with_any_value(target_t):
                self.uses_pyany = True
                return "py_any_as_dict(" + value + ")"
            return value
        if kind == "List":
            elts = self.any_to_list(expr_d.get("elts"))
            if len(elts) == 0:
                elts = self.any_to_list(expr_d.get("elements"))
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            return "vec![" + ", ".join(rendered) + "]"
        if kind == "Tuple":
            elts: list[Any] = self.tuple_elements(expr_d)
            rendered = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"
        if kind == "Dict":
            return self._render_dict_expr(expr_d, force_any_values=False)
        if kind == "ListComp":
            return self._render_list_comp(expr_d)
        if kind == "Subscript":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            owner_node_kind = self.any_dict_get_str(owner_node, "kind", "")
            if owner_node_kind == "Subscript":
                owner_owner_t = self.normalize_type_name(self.get_expr_type(owner_node.get("value")))
                if owner_owner_t.startswith("list[") or owner_owner_t.startswith("tuple[") or owner_owner_t in {"bytes", "bytearray"}:
                    owner = self._render_subscript_lvalue(owner_node)
            owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
            slice_node = self.any_to_dict_or_empty(expr_d.get("slice"))
            slice_kind = self.any_dict_get_str(slice_node, "kind", "")
            if owner_t.startswith("dict["):
                key_t, _val_t = self._dict_key_value_types(owner_t)
                key_expr = self.render_expr(expr_d.get("slice"))
                key_expr = self._coerce_dict_key_expr(key_expr, key_t, require_owned=False)
                return owner + ".get(&" + key_expr + ").cloned().expect(\"dict key not found\")"
            if slice_kind == "Slice":
                self.uses_string_helpers = True
                start_node = slice_node.get("lower")
                end_node = slice_node.get("upper")
                start_txt = "None"
                end_txt = "None"
                if start_node is not None:
                    start_txt = "Some((" + self.render_expr(start_node) + ") as i64)"
                if end_node is not None:
                    end_txt = "Some((" + self.render_expr(end_node) + ") as i64)"
                if owner_t == "str":
                    return "py_slice_str(&" + owner + ", " + start_txt + ", " + end_txt + ")"
                return owner + "[" + self.render_expr(slice_node) + "]"
            idx = self.render_expr(expr_d.get("slice"))
            if owner_t == "str":
                self.uses_string_helpers = True
                if self._expr_is_non_negative(expr_d.get("slice")):
                    return "py_str_at_nonneg(&" + owner + ", ((" + idx + ") as usize))"
                return "py_str_at(&" + owner + ", ((" + idx + ") as i64))"
            if self._expr_is_non_negative(expr_d.get("slice")):
                idx_usize = "((" + idx + ") as usize)"
            else:
                idx_i64 = "((" + idx + ") as i64)"
                idx_usize = "((if " + idx_i64 + " < 0 { (" + owner + ".len() as i64 + " + idx_i64 + ") } else { " + idx_i64 + " }) as usize)"
            indexed = owner + "[" + idx_usize + "]"
            if owner_t in {"bytes", "bytearray"}:
                return "((" + indexed + ") as i64)"
            if owner_t.startswith("list["):
                elem_t = self._list_elem_type(owner_t)
                if self._is_copy_type(elem_t):
                    return indexed
                return "(" + indexed + ").clone()"
            return indexed
        if kind == "Slice":
            lower_node = expr_d.get("lower")
            upper_node = expr_d.get("upper")
            lower_txt = self.render_expr(lower_node) if lower_node is not None else ""
            upper_txt = self.render_expr(upper_node) if upper_node is not None else ""
            if lower_txt == "" and upper_txt == "":
                return ".."
            if lower_txt == "":
                return ".." + upper_txt
            if upper_txt == "":
                return lower_txt + ".."
            return lower_txt + ".." + upper_txt
        if kind == "Lambda":
            args = self.any_to_list(self.any_to_dict_or_empty(expr_d.get("args")).get("args"))
            names: list[str] = []
            for arg in args:
                names.append(self._safe_name(self.any_to_str(self.any_to_dict_or_empty(arg).get("arg"))))
            body = self.render_expr(expr_d.get("body"))
            return "|" + ", ".join(names) + "| " + body

        hook_complex = self.hook_on_render_expr_complex(expr_d)
        if hook_complex != "":
            return hook_complex
        return self.any_to_str(expr_d.get("repr"))

    def render_cond(self, expr: Any) -> str:
        """条件式向け描画（数値等を bool 条件へ寄せる）。"""
        return self.render_truthy_cond_common(
            expr,
            str_non_empty_pattern="!{expr}.is_empty()",
            collection_non_empty_pattern="{expr}.len() != 0",
            number_non_zero_pattern="{expr} != 0",
        )
def transpile_to_rust(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Rust コードへ変換する。"""
    emitter = RustEmitter(east_doc)
    return emitter.transpile()

from __future__ import annotations

from pytra.typing import Any
from toolchain.misc.transpile_cli import dict_any_get_str, join_str_list, make_user_error
from toolchain.frontends.type_expr import type_expr_to_string


# Pairs (src_t, dst_t) where C++ performs implicit widening conversion — no explicit cast needed.
_SAFE_WIDENING_PAIRS: set[tuple[str, str]] = {
    ("bool", "int8"), ("bool", "uint8"), ("bool", "int16"), ("bool", "uint16"),
    ("bool", "int32"), ("bool", "uint32"), ("bool", "int64"), ("bool", "uint64"),
    ("bool", "float32"), ("bool", "float64"),
    ("int8", "int16"), ("int8", "int32"), ("int8", "int64"),
    ("int8", "float32"), ("int8", "float64"),
    ("uint8", "uint16"), ("uint8", "uint32"), ("uint8", "uint64"),
    ("uint8", "int16"), ("uint8", "int32"), ("uint8", "int64"),
    ("uint8", "float32"), ("uint8", "float64"),
    ("int16", "int32"), ("int16", "int64"),
    ("int16", "float32"), ("int16", "float64"),
    ("uint16", "uint32"), ("uint16", "uint64"),
    ("uint16", "int32"), ("uint16", "int64"),
    ("uint16", "float32"), ("uint16", "float64"),
    ("int32", "int64"), ("int32", "float64"),
    ("uint32", "uint64"), ("uint32", "int64"), ("uint32", "float64"),
    ("float32", "float64"),
}


class CppTypeBridgeEmitter:
    """Type conversion and Any-boundary helpers extracted from CppEmitter."""

    def _variant_union_parts_for_type(self, value_t: str) -> tuple[list[str], bool]:
        t_norm = self.normalize_type_name(value_t)
        tagged_union_types = getattr(self, "_tagged_union_types", {})
        tagged_union_has_none = getattr(self, "_tagged_union_has_none", {})
        alias_map = getattr(self, "_type_alias_reverse_map", {})
        union_name = alias_map.get(t_norm, "")
        if union_name == "" and t_norm in tagged_union_types:
            union_name = t_norm
        if union_name != "" and union_name in tagged_union_types:
            return list(tagged_union_types.get(union_name, [])), bool(tagged_union_has_none.get(union_name, False))
        if "|" in t_norm:
            non_none, has_none = self.split_union_non_none(t_norm)
            if len(non_none) >= 2:
                return non_none, has_none
        return [], False

    def _variant_alt_cpp_type_for_target_type(self, source_t: str, target_t: str) -> str:
        union_parts, _ = self._variant_union_parts_for_type(source_t)
        if len(union_parts) == 0:
            return ""
        target_norm = self.normalize_type_name(target_t)
        if target_norm == "None":
            return "::std::monostate"
        for part in union_parts:
            if self.normalize_type_name(part) == target_norm:
                return self._cpp_type_text(part)
        return ""

    def _is_safe_widening_cast(self, src_t: str, dst_t: str) -> bool:
        """src_t → dst_t が C++ 暗黙変換で安全に行われる widening cast かを返す。同型は False。"""
        if src_t in {"", "unknown"} or dst_t in {"", "unknown"}:
            return False
        return (src_t, dst_t) in _SAFE_WIDENING_PAIRS

    def _homogeneous_tuple_ellipsis_item_type(self, east_type: str) -> str:
        """`tuple[T, ...]` の要素型を返す。該当しない場合は空文字。"""
        t_norm = self.normalize_type_name(east_type)
        tuple_inner = self.type_generic_args(t_norm, "tuple")
        if len(tuple_inner) != 2:
            return ""
        item_t = self.normalize_type_name(tuple_inner[0])
        tail_t = self.normalize_type_name(tuple_inner[1])
        if item_t == "" or tail_t != "...":
            return ""
        return item_t

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

    def _find_unsupported_cpp_general_union_type_expr(self, value: Any) -> dict[str, Any] | None:
        if not self._is_type_expr_payload(value):
            return None
        d: dict[str, Any] = self.any_to_dict_or_empty(value)
        kind = self.any_dict_get_str(d, "kind", "")
        if kind == "UnionType":
            union_mode = self.any_dict_get_str(d, "union_mode", "")
            if union_mode != "dynamic":
                return d
            for option in self.any_to_list(d.get("options")):
                found = self._find_unsupported_cpp_general_union_type_expr(option)
                if found is not None:
                    return found
            return None
        if kind == "OptionalType":
            return self._find_unsupported_cpp_general_union_type_expr(d.get("inner"))
        if kind == "GenericType":
            for arg in self.any_to_list(d.get("args")):
                found = self._find_unsupported_cpp_general_union_type_expr(arg)
                if found is not None:
                    return found
        return None

    def _reject_unsupported_cpp_general_union_type_expr(self, value: Any, *, context: str) -> None:
        if not self._is_type_expr_payload(value):
            return
        unsupported = self._find_unsupported_cpp_general_union_type_expr(value)
        if unsupported is None:
            return
        carrier = type_expr_to_string(value)
        lane = type_expr_to_string(unsupported)
        details: list[str] = [context + ": " + carrier]
        if lane != "" and lane != carrier:
            details.append("unsupported general-union lane: " + lane)
        details.append("Use Optional[T], a dynamic union, or a nominal ADT lane instead.")
        raise make_user_error(
            "unsupported_syntax",
            "C++ backend does not support general union TypeExpr yet",
            details,
        )

    def _is_concrete_type_for_typed_list(self, east_type: str, _depth: int = 0) -> bool:
        """typed list 判定向けに Any/unknown を含まない concrete 型か判定する。"""
        if _depth > 20:
            return False
        t_norm = self.normalize_type_name(east_type)
        if t_norm == "None":
            return True
        if t_norm in {"", "unknown", "Any", "object"}:
            return False
        if self._contains_text(t_norm, "|"):
            for part in self.split_union(t_norm):
                if not self._is_concrete_type_for_typed_list(part, _depth + 1):
                    return False
            return True
        list_inner = self.type_generic_args(t_norm, "list")
        if len(list_inner) == 1:
            return self._is_concrete_type_for_typed_list(list_inner[0], _depth + 1)
        tuple_inner = self.type_generic_args(t_norm, "tuple")
        if len(tuple_inner) > 0:
            for part in tuple_inner:
                if not self._is_concrete_type_for_typed_list(part, _depth + 1):
                    return False
            return True
        dict_inner = self.type_generic_args(t_norm, "dict")
        if len(dict_inner) == 2:
            return self._is_concrete_type_for_typed_list(dict_inner[0], _depth + 1) and self._is_concrete_type_for_typed_list(
                dict_inner[1], _depth + 1
            )
        set_inner = self.type_generic_args(t_norm, "set")
        if len(set_inner) == 1:
            return self._is_concrete_type_for_typed_list(set_inner[0], _depth + 1)
        return True

    def _is_pyobj_value_model_list_type(self, east_type: str) -> bool:
        """`pyobj` でも typed value-model で扱える list 型か判定する。"""
        t_norm = self.normalize_type_name(east_type)
        if not (t_norm.startswith("list[") and t_norm.endswith("]")):
            return False
        list_inner = self.type_generic_args(t_norm, "list")
        if len(list_inner) != 1:
            return False
        elem_t = self.normalize_type_name(list_inner[0])
        if elem_t == "object":
            return True
        if not self._is_concrete_type_for_typed_list(elem_t):
            return False
        return True

    def _is_pyobj_ref_first_list_type(self, east_type: str) -> bool:
        """`pyobj` で backend 内部の ref-first handle を使う typed list 型か判定する。"""
        t_norm = self.normalize_type_name(east_type)
        if not (t_norm.startswith("list[") and t_norm.endswith("]")):
            return False
        list_inner = self.type_generic_args(t_norm, "list")
        if len(list_inner) != 1:
            return False
        elem_t = self.normalize_type_name(list_inner[0])
        if not self._is_concrete_type_for_typed_list(elem_t):
            return False
        return self._cpp_list_value_model_type_text(t_norm) != "bytearray"

    def _is_pyobj_runtime_list_type(self, east_type: str) -> bool:
        """`cpp_list_model=pyobj` で object runtime 経路を使う list 型か判定する。"""
        t_norm = self.normalize_type_name(east_type)
        if not (t_norm.startswith("list[") and t_norm.endswith("]")):
            return False
        list_inner = self.type_generic_args(t_norm, "list")
        if len(list_inner) != 1:
            return True
        elem_t = self.normalize_type_name(list_inner[0])
        if elem_t == "object":
            return False
        if elem_t == "None":
            return False
        # list[RefClass] は pyobj モデルでも typed container へ寄せる。
        if elem_t in self.ref_classes:
            return False
        # list[ValueClass] も typed container を維持する（sample/18 AST 値型化向け）。
        if elem_t in self.class_names:
            return False
        return True

    def _build_box_expr_node(self, value_node: Any) -> dict[str, Any]:
        return {
            "kind": "Box",
            "value": value_node,
            "resolved_type": "object",
            "borrow_kind": "value",
            "casts": [],
        }

    def _build_unbox_expr_node(self, value_node: Any, target_t: str, ctx: str) -> dict[str, Any]:
        t_norm = self.normalize_type_name(target_t)
        return {
            "kind": "Unbox",
            "value": value_node,
            "target": t_norm,
            "ctx": ctx,
            "resolved_type": t_norm,
            "borrow_kind": "value",
            "casts": [],
        }

    def _build_any_boundary_expr_from_builtin_call(
        self,
        runtime_call: str,
        arg_nodes: list[Any],
    ) -> dict[str, Any] | None:
        if len(arg_nodes) != 1:
            return None
        arg0 = arg_nodes[0]
        arg0_t = self.get_expr_type(arg0)
        if not self.is_any_like_type(arg0_t):
            return None
        if runtime_call == "py_to_bool":
            return {
                "kind": "ObjBool",
                "value": arg0,
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
        if runtime_call == "py_len":
            return {
                "kind": "ObjLen",
                "value": arg0,
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
        if runtime_call == "py_to_string":
            return {
                "kind": "ObjStr",
                "value": arg0,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
        return None

    def _render_unbox_target_cast(self, expr_txt: str, target_t: str, ctx: str) -> str:
        """`Unbox` / `CastOrRaise` の最終 C++ 変換を行う。"""
        t_norm = self.normalize_type_name(target_t)
        homogeneous_tuple_item_t = self._homogeneous_tuple_ellipsis_item_type(t_norm)
        if homogeneous_tuple_item_t != "":
            return self._render_unbox_target_cast(expr_txt, f"list[{homogeneous_tuple_item_t}]", ctx)
        if self.should_skip_same_type_cast(expr_txt, t_norm):
            return expr_txt
        if t_norm in self.ref_classes:
            cpp_t = self._cpp_type_text(t_norm)
            ref_inner = t_norm
            if cpp_t.startswith("rc<") and cpp_t.endswith(">"):
                ref_inner = cpp_t[3:-1]
            ctx_safe = ctx.replace("\\", "\\\\").replace('"', '\\"')
            return f'({expr_txt}).as<{ref_inner}>()'
        if t_norm in {"float32", "float64"}:
            if t_norm == "float64" and (
                expr_txt.startswith("float64(")
                or expr_txt.startswith("static_cast<float64>(")
                or expr_txt.startswith("py_to<float64>(")
                or expr_txt.startswith("py_to_float64(")
            ):
                return expr_txt
            return f"py_to_{t_norm}({expr_txt})"
        if t_norm in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            if t_norm == "int64" and (
                expr_txt.startswith("int64(")
                or expr_txt.startswith("static_cast<int64>(")
                or expr_txt.startswith("py_to<int64>(")
                or expr_txt.startswith("py_to_int64(")
            ):
                return expr_txt
            return f"py_to_{t_norm}({expr_txt})"
        if t_norm == "bool":
            return f"py_to_bool({expr_txt})"
        if t_norm == "str":
            return f"py_to_string({expr_txt})"
        if t_norm.startswith("tuple[") and t_norm.endswith("]"):
            elems = self.split_generic(t_norm[6:-1])
            if len(elems) == 0:
                return "::std::tuple<>{}"
            items: list[str] = []
            i = 0
            while i < len(elems):
                elem_t = self.normalize_type_name(self.any_to_str(elems[i]))
                item_expr = f"py_at({expr_txt}, {i})"
                if elem_t not in {"", "unknown"} and not self.is_any_like_type(elem_t) and self._can_runtime_cast_target(elem_t):
                    item_expr = self._render_unbox_target_cast(item_expr, elem_t, f"{ctx}:tuple[{i}]")
                items.append(item_expr)
                i += 1
            return f"::std::make_tuple({join_str_list(', ', items)})"
        if t_norm.startswith("list[") and t_norm.endswith("]"):
            if self._is_pyobj_ref_first_list_type(t_norm):
                return f"py_to<{self._cpp_type_text(t_norm, pyobj_ref_lists=True)}>({expr_txt})"
            list_inner = self.type_generic_args(t_norm, "list")
            if len(list_inner) == 1:
                elem_t = self.normalize_type_name(list_inner[0])
                if elem_t in self.ref_classes:
                    ctx_safe = ctx.replace("\\", "\\\\").replace('"', '\\"')
                    return f'py_to_rc_list_from_object<{elem_t}>({expr_txt}, "{ctx_safe}")'
        if t_norm.startswith("list[") or t_norm.startswith("dict[") or t_norm.startswith("set["):
            return f"{self._cpp_type_text(t_norm)}({expr_txt})"
        return expr_txt

    def _coerce_any_expr_to_target(self, expr_txt: str, target_t: str, ctx: str) -> str:
        """Any/object 式を target_t へ変換する（legacy 互換 wrapper）。"""
        return self._render_unbox_target_cast(expr_txt, target_t, ctx)

    def _coerce_any_expr_to_target_via_unbox(self, expr_txt: str, source_node: Any, target_t: str, ctx: str) -> str:
        """Any/object から型付き値への変換を EAST3 `Unbox` 命令写像へ寄せる。"""
        if expr_txt == "":
            return expr_txt
        t_norm = self.normalize_type_name(target_t)
        if t_norm in {"", "unknown"} or self.is_any_like_type(t_norm):
            return expr_txt
        source_d = self.any_to_dict_or_empty(source_node)
        if len(source_d) > 0:
            return self.render_expr(self._build_unbox_expr_node(source_node, t_norm, ctx))
        return self._coerce_any_expr_to_target(expr_txt, t_norm, ctx)

    def _coerce_call_arg(
        self,
        arg_txt: str,
        arg_node: Any,
        target_t: str,
        *,
        list_target_is_value: bool = False,
    ) -> str:
        """関数シグネチャに合わせて引数を必要最小限キャストする。"""
        at0 = self.get_expr_type(arg_node)
        at = at0 if isinstance(at0, str) else ""
        t_norm = self.normalize_type_name(target_t)
        if self._is_pyobj_ref_first_list_type(t_norm) and (not list_target_is_value):
            return self._render_pyobj_alias_list_value(arg_txt, arg_node, t_norm)
        # `cpp_list_model=pyobj` でも list[RefClass] は typed container として扱う。
        # それ以外の list[...] は callsite coercion の target を object へ寄せる。
        if (
            self._is_pyobj_runtime_list_type(t_norm)
            and (not self._is_pyobj_value_model_list_type(t_norm))
            and t_norm != "list[str]"
        ):
            t_norm = "object"
        arg_node_dict = self.any_to_dict_or_empty(arg_node)
        list_arg_adapter = self._render_pyobj_value_list_arg_adapter(arg_txt, arg_node, t_norm)
        if list_target_is_value and list_arg_adapter != arg_txt:
            return list_arg_adapter
        if self._class_borrow_accepts_ref_handle(at, t_norm):
            return self._render_class_borrow_arg(arg_txt)
        if self.is_any_like_type(t_norm):
            if self.is_boxed_object_expr(arg_txt):
                return arg_txt
            if arg_txt == "*this":
                return "object(static_cast<PyObj*>(this), true)"
            if (
                self._is_pyobj_runtime_list_type(at)
                and (not self._is_pyobj_value_model_list_type(at))
                and len(arg_node_dict) > 0
            ):
                if (not self._expr_is_stack_list_local(arg_node_dict)) and (
                    not self._uses_pyobj_ref_first_list_lvalue_expr(arg_node_dict)
                ):
                    return arg_txt
            if self.is_any_like_type(at):
                return arg_txt
            if len(arg_node_dict) > 0:
                if self._node_kind_from_dict(arg_node_dict) == "Tuple":
                    items: list[str] = []
                    for elem in self.any_to_list(arg_node_dict.get("elements")):
                        elem_d = self.any_to_dict_or_empty(elem)
                        if (
                            self._node_kind_from_dict(elem_d) == "Name"
                            and dict_any_get_str(elem_d, "id", "") == "self"
                            and self.current_class_name is not None
                            and self.current_class_name in self.ref_classes
                        ):
                            items.append("object(static_cast<PyObj*>(this), true)")
                        else:
                            items.append(self.render_expr(elem))
                    return f"object(::std::make_tuple({join_str_list(', ', items)}))"
                return self.render_expr(self._build_box_expr_node(arg_node))
            return f"object({arg_txt})"
        if not self._can_runtime_cast_target(target_t):
            return arg_txt
        if t_norm == "list[str]" and self._is_pyobj_runtime_list_type(at):
            list_cpp_t = self._cpp_type_text(t_norm)
            if len(arg_node_dict) == 0:
                return f"{list_cpp_t}({arg_txt})"
            if self._node_kind_from_dict(arg_node_dict) == "Name":
                arg_name = dict_any_get_str(arg_node_dict, "id", "")
                if self._is_typed_list_str_name(arg_name):
                    return arg_txt
            if not self._expr_is_stack_list_local(arg_node_dict):
                return f"{list_cpp_t}({arg_txt})"
        if not self.is_any_like_type(at):
            return arg_txt
        if len(arg_node_dict) > 0:
            return self.render_expr(self._build_unbox_expr_node(arg_node, t_norm, f"call_arg:{t_norm}"))
        return self._coerce_any_expr_to_target(arg_txt, target_t, f"call_arg:{t_norm}")

    def _render_class_borrow_arg(self, arg_txt: str) -> str:
        """`rc<T>` を borrowed class parameter へ渡すときの参照式を返す。"""
        if arg_txt.startswith("*"):
            return arg_txt
        return f"*{arg_txt}"

    def _class_borrow_accepts_ref_handle(self, source_t: str, target_t: str) -> bool:
        """`rc<Derived>` を `Base&` へ渡せる representative lane か判定する。"""
        source_norm = self.normalize_type_name(source_t)
        target_norm = self.normalize_type_name(target_t)
        if source_norm in {"", "unknown"} or target_norm in {"", "unknown"}:
            return False
        if target_norm.startswith("rc<"):
            return False
        if not self._is_cpp_class_borrow_type(target_norm):
            return False
        if not self._type_is_ref_class(source_norm):
            return False
        return self._is_cpp_class_subtype(source_norm, target_norm)

    def _is_cpp_class_borrow_type(self, type_name: str) -> bool:
        """関数境界で borrowed class として扱う target 型か判定する。"""
        type_norm = self.normalize_type_name(type_name)
        if type_norm in {"", "unknown"} or self.is_any_like_type(type_norm):
            return False
        for prefix in (
            "list[",
            "dict[",
            "set[",
            "tuple[",
            "deque[",
            "iter[",
            "iterator[",
            "generator[",
            "callable[",
            "::std::optional<",
        ):
            if type_norm.startswith(prefix):
                return False
        if type_norm in {
            "str",
            "bytes",
            "bytearray",
            "int8",
            "uint8",
            "int16",
            "uint16",
            "int32",
            "uint32",
            "int64",
            "uint64",
            "float32",
            "float64",
            "bool",
        }:
            return False
        for candidate in self._expand_runtime_class_candidates(type_norm):
            stripped = self._strip_rc_wrapper(candidate)
            if stripped in self.class_names or stripped in self.ref_classes or stripped in self.value_classes:
                return True
        return False

    def _is_cpp_class_subtype(self, source_t: str, target_t: str) -> bool:
        """source_t が target_t と同型か派生型なら True。"""
        target_candidates = {
            self._strip_rc_wrapper(candidate)
            for candidate in self._expand_runtime_class_candidates(target_t)
            if self._strip_rc_wrapper(candidate) != ""
        }
        if len(target_candidates) == 0:
            return False
        for source_candidate in self._expand_runtime_class_candidates(source_t):
            current = self._strip_rc_wrapper(source_candidate)
            seen: set[str] = set()
            while current != "" and current not in seen:
                if current in target_candidates:
                    return True
                seen.add(current)
                current = self.class_base.get(current, "")
        return False

    def _coerce_args_by_signature(
        self,
        args: list[str],
        arg_nodes: list[Any],
        sig: list[str],
        *,
        arg_abi_modes: list[str] | None = None,
        list_targets_are_value: bool = False,
    ) -> list[str]:
        """シグネチャ配列に基づいて引数列を順序保持でキャストする。"""
        if len(sig) == 0:
            return args
        out: list[str] = []
        for i, arg_txt in enumerate(args):
            if i < len(sig):
                node: Any = arg_nodes[i] if i < len(arg_nodes) else {}
                abi_mode = "default"
                if isinstance(arg_abi_modes, list) and i < len(arg_abi_modes):
                    abi_mode = self.any_to_str(arg_abi_modes[i]) or "default"
                out.append(
                    self._coerce_call_arg(
                        arg_txt,
                        node,
                        sig[i],
                        list_target_is_value=list_targets_are_value or abi_mode in {"value", "value_mut", "value_readonly"},
                    )
                )
            else:
                out.append(arg_txt)
        return out

    def _pack_known_function_varargs(self, fn_name: str, args: list[str], arg_nodes: list[Any]) -> list[str]:
        """typed `*args` を trailing list parameter へ pack する。"""
        vararg_list_t = self.normalize_type_name(self.any_to_str(self.function_vararg_list_types.get(fn_name, "")))
        if vararg_list_t == "":
            return args
        fixed_sig = self.function_arg_types.get(fn_name, [])
        fixed_args = self._coerce_args_by_signature(
            args[: len(fixed_sig)],
            arg_nodes[: len(fixed_sig)],
            fixed_sig,
            arg_abi_modes=self.function_arg_abi_modes.get(fn_name, []),
            list_targets_are_value=fn_name in self.extern_function_names,
        )
        vararg_inner = self.type_generic_args(vararg_list_t, "list")
        vararg_elem_t = self.normalize_type_name(vararg_inner[0]) if len(vararg_inner) == 1 else ""
        packed_items: list[str] = []
        packed_nodes: list[Any] = []
        for idx, arg_txt in enumerate(args[len(fixed_sig) :]):
            node = arg_nodes[len(fixed_sig) + idx] if len(fixed_sig) + idx < len(arg_nodes) else {}
            packed_nodes.append(node)
            if vararg_elem_t != "":
                packed_items.append(self._coerce_call_arg(arg_txt, node, vararg_elem_t))
            else:
                packed_items.append(arg_txt)
        packed_node: dict[str, Any] = {
            "kind": "List",
            "elements": packed_nodes,
            "resolved_type": vararg_list_t,
        }
        packed_expr = self.render_expr(packed_node)
        return fixed_args + [self._coerce_call_arg(packed_expr, packed_node, vararg_list_t)]

    def _coerce_args_for_known_function(self, fn_name: str, args: list[str], arg_nodes: list[Any]) -> list[str]:
        """既知関数呼び出しに対して引数型を合わせる。"""
        if fn_name not in self.function_arg_types and fn_name not in self.function_vararg_list_types:
            return args
        if fn_name in self.function_vararg_list_types:
            return self._pack_known_function_varargs(fn_name, args, arg_nodes)
        return self._coerce_args_by_signature(
            args,
            arg_nodes,
            self.function_arg_types[fn_name],
            arg_abi_modes=self.function_arg_abi_modes.get(fn_name, []),
            list_targets_are_value=fn_name in self.extern_function_names,
        )

    def cpp_type(self, east_type: Any) -> str:
        """EAST 型名を C++ 型名へマッピングする。"""
        if self._is_type_expr_payload(east_type):
            return self._cpp_type_text(type_expr_to_string(east_type))
        east_type_txt = self.any_to_str(east_type)
        if east_type_txt == "" and east_type is not None:
            ttxt = str(east_type)
            if ttxt != "" and ttxt not in {"{}", "[]"}:
                east_type_txt = ttxt
        east_type_txt = self.normalize_type_name(east_type_txt)
        return self._cpp_type_text(east_type_txt)

    def cpp_signature_type(self, east_type: Any, *, runtime_abi_mode: str = "default") -> str:
        """関数境界/宣言向けに ref-first list を反映した型文字列を返す。"""
        if self._is_type_expr_payload(east_type):
            east_type_txt = type_expr_to_string(east_type)
        else:
            east_type_txt = self.any_to_str(east_type)
        if east_type_txt == "" and east_type is not None:
            ttxt = str(east_type)
            if ttxt != "" and ttxt not in {"{}", "[]"}:
                east_type_txt = ttxt
        east_type_txt = self.normalize_type_name(east_type_txt)
        if runtime_abi_mode in {"value", "value_mut", "value_readonly"}:
            list_inner = self.type_generic_args(east_type_txt, "list")
            if len(list_inner) == 1:
                return self._cpp_list_value_model_type_text(east_type_txt)
        use_ref_first_lists = runtime_abi_mode not in {"value", "value_mut", "value_readonly"}
        return self._cpp_type_text(east_type_txt, pyobj_ref_lists=use_ref_first_lists)

    def _cpp_type_text(self, east_type: str, *, pyobj_ref_lists: bool = False) -> str:
        """正規化済み型名（str）を C++ 型名へマッピングする。"""
        t_norm, mapped = self.normalize_type_and_lookup_map(east_type, self.type_map)
        east_type = t_norm
        alias = getattr(self, "_type_alias_reverse_map", {}).get(east_type)
        if alias is not None:
            return alias
        if east_type == "":
            return "auto"
        if east_type in self.ref_classes:
            if getattr(self, "use_object_t", False):
                return f"Object<{east_type}>"
            return f"rc<{east_type}>"
        if east_type in self.class_names:
            return east_type
        if mapped != "":
            return mapped
        imported_class_cpp_type = self._resolve_imported_symbol_class_cpp_type(east_type)
        if imported_class_cpp_type != "":
            return imported_class_cpp_type
        if east_type in {"Any", "object"}:
            return "object"
        if east_type.find("|") != -1:
            union_parts = self.split_union(east_type)
            if len(union_parts) >= 2:
                non_none, has_none = self.split_union_non_none(east_type)
                if len(non_none) >= 1:
                    only_bytes = True
                    for p in non_none:
                        if p not in {"bytes", "bytearray"}:
                            only_bytes = False
                            break
                    if only_bytes:
                        return "bytes"
                    has_any_like = False
                    for p in non_none:
                        if self.is_any_like_type(p):
                            has_any_like = True
                            break
                    if has_any_like:
                        # object は全型を包含するため、union 内に Any 相当型があれば object に退化させる。
                        return "object"
                if has_none and len(non_none) == 1:
                    return f"::std::optional<{self._cpp_type_text(non_none[0], pyobj_ref_lists=pyobj_ref_lists)}>"
                if (not has_none) and len(non_none) == 1:
                    return self._cpp_type_text(non_none[0], pyobj_ref_lists=pyobj_ref_lists)
                # 一般ユニオン（2型以上）→ std::variant<...>。
                # Narrowing / cast の object 経路互換のため union metadata は引き続き登録する。
                tagged_union_types = getattr(self, "_tagged_union_types", {})
                tagged_union_has_none = getattr(self, "_tagged_union_has_none", {})
                # Use east_type as key for inline union lookup.
                tagged_union_types[east_type] = non_none
                tagged_union_has_none[east_type] = has_none
                variant_parts: list[str] = []
                for part in non_none:
                    cpp_part = self._cpp_type_text(part, pyobj_ref_lists=pyobj_ref_lists)
                    if cpp_part not in variant_parts:
                        variant_parts.append(cpp_part)
                if has_none:
                    variant_parts.append("::std::monostate")
                return "::std::variant<" + join_str_list(", ", variant_parts) + ">"
        if east_type == "None":
            return "void"
        if east_type == "PyFile":
            return "pytra::runtime::cpp::base::PyFile"
        list_inner = self.type_generic_args(east_type, "list")
        if len(list_inner) == 1:
            if pyobj_ref_lists and self._is_pyobj_ref_first_list_type(east_type):
                return self._cpp_pyobj_alias_list_handle_type_text(east_type)
            if self._is_pyobj_runtime_list_type(east_type) and (not self._is_pyobj_value_model_list_type(east_type)):
                return "object"
            list_elem = list_inner[0]
            if list_elem == "None":
                return "list<::std::monostate>"
            if list_elem == "uint8":
                return "bytearray"
            if self.is_any_like_type(list_elem):
                return "list<object>"
            if list_elem == "unknown":
                return "list<object>"
            return f"list<{self._cpp_type_text(list_elem, pyobj_ref_lists=pyobj_ref_lists)}>"
        deque_inner = self.type_generic_args(east_type, "deque")
        if len(deque_inner) == 1:
            deque_elem = deque_inner[0]
            if deque_elem == "None":
                return "::std::deque<::std::monostate>"
            if self.is_any_like_type(deque_elem):
                return "::std::deque<object>"
            if deque_elem == "unknown":
                return "::std::deque<object>"
            return f"::std::deque<{self._cpp_type_text(deque_elem, pyobj_ref_lists=pyobj_ref_lists)}>"
        set_inner = self.type_generic_args(east_type, "set")
        if len(set_inner) == 1:
            set_elem = set_inner[0]
            if set_elem == "None":
                return "set<::std::monostate>"
            if set_elem == "unknown":
                return "set<str>"
            return f"set<{self._cpp_type_text(set_elem, pyobj_ref_lists=pyobj_ref_lists)}>"
        dict_inner = self.type_generic_args(east_type, "dict")
        if len(dict_inner) == 2:
            dict_key = dict_inner[0]
            dict_val = dict_inner[1]
            if dict_val == "None":
                key_t = dict_key if dict_key not in {"", "unknown"} else "str"
                return f"dict<{self._cpp_type_text(key_t, pyobj_ref_lists=pyobj_ref_lists)}, ::std::monostate>"
            if self.is_any_like_type(dict_val):
                return (
                    f"dict<{self._cpp_type_text(dict_key if dict_key != 'unknown' else 'str', pyobj_ref_lists=pyobj_ref_lists)}, "
                    "object>"
                )
            if dict_key == "unknown" and dict_val == "unknown":
                return "dict<str, object>"
            if dict_key == "unknown":
                return f"dict<str, {self._cpp_type_text(dict_val, pyobj_ref_lists=pyobj_ref_lists)}>"
            if dict_val == "unknown":
                return f"dict<{self._cpp_type_text(dict_key, pyobj_ref_lists=pyobj_ref_lists)}, object>"
            return (
                f"dict<{self._cpp_type_text(dict_key, pyobj_ref_lists=pyobj_ref_lists)}, "
                f"{self._cpp_type_text(dict_val, pyobj_ref_lists=pyobj_ref_lists)}>"
            )
        tuple_inner = self.type_generic_args(east_type, "tuple")
        if len(tuple_inner) > 0:
            homogeneous_tuple_item_t = self._homogeneous_tuple_ellipsis_item_type(east_type)
            if homogeneous_tuple_item_t != "":
                return f"list<{self._cpp_type_text(homogeneous_tuple_item_t, pyobj_ref_lists=pyobj_ref_lists)}>"
            inner_cpp: list[str] = []
            for x in tuple_inner:
                inner_cpp.append(self._cpp_type_text(x, pyobj_ref_lists=pyobj_ref_lists))
            sep = ", "
            return "::std::tuple<" + sep.join(inner_cpp) + ">"
        if east_type == "unknown":
            return "object"
        if east_type.startswith("callable["):
            return "auto"
        if east_type == "callable":
            return "auto"
        if east_type == "module":
            return "auto"
        if east_type.find(".") >= 0:
            dot = east_type.rfind(".")
            owner = east_type[:dot]
            leaf = east_type[dot + 1 :]
            if owner != "" and leaf != "":
                mod_name = self._resolve_imported_module_name(owner)
                ns = self._module_name_to_cpp_namespace(mod_name)
                looks_like_class = leaf != "" and (leaf[0] >= "A" and leaf[0] <= "Z")
                if ns != "":
                    if looks_like_class:
                        return f"rc<{ns}::{leaf}>"
                    return f"{ns}::{leaf}"
                if owner.startswith("pytra."):
                    owner_ns = "pytra::" + owner[6:].replace(".", "::")
                    if looks_like_class:
                        return f"rc<{owner_ns}::{leaf}>"
                    return owner_ns + "::" + leaf
                owner_ns = owner.replace(".", "::")
                if looks_like_class:
                    return f"rc<{owner_ns}::{leaf}>"
                return owner_ns + "::" + leaf
        return east_type

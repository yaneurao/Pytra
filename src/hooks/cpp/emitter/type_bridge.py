from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import dict_any_get_str, join_str_list


class CppTypeBridgeEmitter:
    """Type conversion and Any-boundary helpers extracted from CppEmitter."""

    def _is_pyobj_runtime_list_type(self, east_type: str) -> bool:
        """`cpp_list_model=pyobj` で object runtime 経路を使う list 型か判定する。"""
        if self.any_to_str(getattr(self, "cpp_list_model", "value")) != "pyobj":
            return False
        t_norm = self.normalize_type_name(east_type)
        if not (t_norm.startswith("list[") and t_norm.endswith("]")):
            return False
        list_inner = self.type_generic_args(t_norm, "list")
        if len(list_inner) != 1:
            return True
        elem_t = self.normalize_type_name(list_inner[0])
        # list[RefClass] は pyobj モデルでも typed container へ寄せる。
        if elem_t in self.ref_classes:
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
        if self.should_skip_same_type_cast(expr_txt, t_norm):
            return expr_txt
        if t_norm in self.ref_classes:
            cpp_t = self._cpp_type_text(t_norm)
            ref_inner = t_norm
            if cpp_t.startswith("rc<") and cpp_t.endswith(">"):
                ref_inner = cpp_t[3:-1]
            ctx_safe = ctx.replace("\\", "\\\\").replace('"', '\\"')
            return f'obj_to_rc_or_raise<{ref_inner}>({expr_txt}, "{ctx_safe}")'
        if t_norm in {"float32", "float64"}:
            return f"py_to<float64>({expr_txt})"
        if t_norm in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return f"{t_norm}(py_to<int64>({expr_txt}))"
        if t_norm == "bool":
            return f"py_to<bool>({expr_txt})"
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

    def _coerce_call_arg(self, arg_txt: str, arg_node: Any, target_t: str) -> str:
        """関数シグネチャに合わせて引数を必要最小限キャストする。"""
        at0 = self.get_expr_type(arg_node)
        at = at0 if isinstance(at0, str) else ""
        t_norm = self.normalize_type_name(target_t)
        # `cpp_list_model=pyobj` でも list[RefClass] は typed container として扱う。
        # それ以外の list[...] は callsite coercion の target を object へ寄せる。
        if self._is_pyobj_runtime_list_type(t_norm):
            t_norm = "object"
        arg_node_dict = self.any_to_dict_or_empty(arg_node)
        if self.is_any_like_type(t_norm):
            if self.is_boxed_object_expr(arg_txt):
                return arg_txt
            if arg_txt == "*this":
                return "object(static_cast<PyObj*>(this), true)"
            if self._is_pyobj_runtime_list_type(at) and len(arg_node_dict) > 0:
                if not self._expr_is_stack_list_local(arg_node_dict):
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
                    return f"make_object(::std::make_tuple({join_str_list(', ', items)}))"
                return self.render_expr(self._build_box_expr_node(arg_node))
            return f"make_object({arg_txt})"
        if not self._can_runtime_cast_target(target_t):
            return arg_txt
        if not self.is_any_like_type(at):
            return arg_txt
        if len(arg_node_dict) > 0:
            return self.render_expr(self._build_unbox_expr_node(arg_node, t_norm, f"call_arg:{t_norm}"))
        return self._coerce_any_expr_to_target(arg_txt, target_t, f"call_arg:{t_norm}")

    def _coerce_args_by_signature(
        self,
        args: list[str],
        arg_nodes: list[Any],
        sig: list[str],
    ) -> list[str]:
        """シグネチャ配列に基づいて引数列を順序保持でキャストする。"""
        if len(sig) == 0:
            return args
        out: list[str] = []
        for i, arg_txt in enumerate(args):
            if i < len(sig):
                node: Any = arg_nodes[i] if i < len(arg_nodes) else {}
                out.append(self._coerce_call_arg(arg_txt, node, sig[i]))
            else:
                out.append(arg_txt)
        return out

    def _coerce_args_for_known_function(self, fn_name: str, args: list[str], arg_nodes: list[Any]) -> list[str]:
        """既知関数呼び出しに対して引数型を合わせる。"""
        if fn_name not in self.function_arg_types:
            return args
        return self._coerce_args_by_signature(args, arg_nodes, self.function_arg_types[fn_name])

    def cpp_type(self, east_type: Any) -> str:
        """EAST 型名を C++ 型名へマッピングする。"""
        east_type_txt = self.any_to_str(east_type)
        if east_type_txt == "" and east_type is not None:
            ttxt = str(east_type)
            if ttxt != "" and ttxt not in {"{}", "[]"}:
                east_type_txt = ttxt
        east_type_txt = self.normalize_type_name(east_type_txt)
        return self._cpp_type_text(east_type_txt)

    def _cpp_type_text(self, east_type: str) -> str:
        """正規化済み型名（str）を C++ 型名へマッピングする。"""
        t_norm, mapped = self.normalize_type_and_lookup_map(east_type, self.type_map)
        east_type = t_norm
        if east_type == "":
            return "auto"
        if east_type in self.ref_classes:
            return f"rc<{east_type}>"
        if east_type in self.class_names:
            return east_type
        if mapped != "":
            return mapped
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
                        return "object"
                    if has_none and len(non_none) == 1:
                        return f"::std::optional<{self._cpp_type_text(non_none[0])}>"
                    if (not has_none) and len(non_none) == 1:
                        return self._cpp_type_text(non_none[0])
                    return "object"
        if east_type == "None":
            return "void"
        if east_type == "PyFile":
            return "pytra::runtime::cpp::base::PyFile"
        list_inner = self.type_generic_args(east_type, "list")
        if len(list_inner) == 1:
            if self._is_pyobj_runtime_list_type(east_type):
                return "object"
            list_elem = list_inner[0]
            if list_elem == "None":
                return "list<object>"
            if list_elem == "uint8":
                return "bytearray"
            if self.is_any_like_type(list_elem):
                return "list<object>"
            if list_elem == "unknown":
                return "list<object>"
            return f"list<{self._cpp_type_text(list_elem)}>"
        set_inner = self.type_generic_args(east_type, "set")
        if len(set_inner) == 1:
            set_elem = set_inner[0]
            if set_elem == "None":
                return "set<object>"
            if set_elem == "unknown":
                return "set<str>"
            return f"set<{self._cpp_type_text(set_elem)}>"
        dict_inner = self.type_generic_args(east_type, "dict")
        if len(dict_inner) == 2:
            dict_key = dict_inner[0]
            dict_val = dict_inner[1]
            if dict_val == "None":
                key_t = dict_key if dict_key not in {"", "unknown"} else "str"
                return f"dict<{self._cpp_type_text(key_t)}, object>"
            if self.is_any_like_type(dict_val):
                return f"dict<{self._cpp_type_text(dict_key if dict_key != 'unknown' else 'str')}, object>"
            if dict_key == "unknown" and dict_val == "unknown":
                return "dict<str, object>"
            if dict_key == "unknown":
                return f"dict<str, {self._cpp_type_text(dict_val)}>"
            if dict_val == "unknown":
                return f"dict<{self._cpp_type_text(dict_key)}, object>"
            return f"dict<{self._cpp_type_text(dict_key)}, {self._cpp_type_text(dict_val)}>"
        tuple_inner = self.type_generic_args(east_type, "tuple")
        if len(tuple_inner) > 0:
            inner_cpp: list[str] = []
            for x in tuple_inner:
                inner_cpp.append(self._cpp_type_text(x))
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

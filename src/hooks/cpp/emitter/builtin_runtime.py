from __future__ import annotations

from pytra.std.typing import Any


class CppBuiltinRuntimeEmitter:
    """Builtin runtime_call dispatch helpers extracted from CppEmitter."""

    def _render_builtin_call(
        self,
        expr: dict[str, Any],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str:
        """lowered_kind=BuiltinCall の呼び出しを処理する。"""
        runtime_call = self.any_dict_get_str(expr, "runtime_call", "")
        if runtime_call == "":
            legacy_builtin_name = self.any_dict_get_str(expr, "builtin_name", "")
            raise ValueError(
                "builtin call must define runtime_call in EAST3: " + legacy_builtin_name
            )
        any_boundary_expr = self._build_any_boundary_expr_from_builtin_call(
            runtime_call,
            arg_nodes,
        )
        if any_boundary_expr is not None:
            return self.render_expr(any_boundary_expr)
        if runtime_call == "static_cast" and len(arg_nodes) == 1:
            static_cast_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "static_cast",
                "target": self.any_to_str(expr.get("resolved_type")),
                "value": arg_nodes[0],
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(static_cast_node)
        list_ops_rendered = self._render_builtin_runtime_list_ops(runtime_call, expr, arg_nodes)
        if list_ops_rendered is not None:
            return str(list_ops_rendered)
        set_ops_rendered = self._render_builtin_runtime_set_ops(runtime_call, expr, arg_nodes)
        if set_ops_rendered is not None:
            return str(set_ops_rendered)
        dict_ops_rendered = self._render_builtin_runtime_dict_ops(runtime_call, expr, arg_nodes)
        if dict_ops_rendered is not None:
            return str(dict_ops_rendered)
        str_ops_rendered = self._render_builtin_runtime_str_ops(runtime_call, expr, arg_nodes)
        if str_ops_rendered is not None:
            return str(str_ops_rendered)
        special_runtime_rendered = self._render_builtin_runtime_special_ops(runtime_call, expr, arg_nodes, kw_nodes)
        if special_runtime_rendered is not None:
            return str(special_runtime_rendered)
        return ""

    def _builtin_runtime_owner_node(self, expr: dict[str, Any], runtime_call: str = "") -> Any:
        """BuiltinCall の receiver ノードを `runtime_owner` 優先で返す。"""
        owner_required_runtime_calls = [
            "list.append",
            "list.extend",
            "list.pop",
            "list.clear",
            "list.reverse",
            "list.sort",
            "set.add",
            "set.discard",
            "set.remove",
            "set.clear",
            "dict.get",
            "dict.pop",
            "dict.items",
            "dict.keys",
            "dict.values",
            "py_isdigit",
            "py_isalpha",
            "py_strip",
            "py_rstrip",
            "py_lstrip",
            "py_startswith",
            "py_endswith",
            "py_find",
            "py_rfind",
            "py_replace",
            "py_join",
            "std::filesystem::create_directories",
            "std::filesystem::exists",
            "py_write_text",
            "py_read_text",
            "path_parent",
            "path_name",
            "path_stem",
            "identity",
            "py_int_to_bytes",
        ]
        runtime_owner = expr.get("runtime_owner")
        if len(self.any_to_dict_or_empty(runtime_owner)) > 0:
            return runtime_owner
        func_node = self.any_to_dict_or_empty(expr.get("func"))
        if len(func_node) > 0:
            func_value = func_node.get("value")
            if len(self.any_to_dict_or_empty(func_value)) > 0:
                return func_value
        if runtime_call in owner_required_runtime_calls:
            raise ValueError("builtin runtime owner is required: " + runtime_call)
        return None

    def _render_builtin_runtime_list_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の list 系 runtime_call を処理する。"""
        if runtime_call not in {"list.append", "list.extend", "list.pop", "list.clear", "list.reverse", "list.sort"}:
            return None
        owner_node = self._builtin_runtime_owner_node(expr, runtime_call)
        if runtime_call == "list.append":
            if len(arg_nodes) >= 1:
                append_node: dict[str, Any] = {
                    "kind": "ListAppend",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(append_node)
            return None
        if runtime_call == "list.extend":
            if len(arg_nodes) >= 1:
                extend_node: dict[str, Any] = {
                    "kind": "ListExtend",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(extend_node)
            return None
        if runtime_call == "list.pop":
            pop_node: dict[str, Any] = {
                "kind": "ListPop",
                "owner": owner_node,
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                pop_node["index"] = arg_nodes[0]
            return self.render_expr(pop_node)
        if runtime_call == "list.clear":
            clear_node: dict[str, Any] = {
                "kind": "ListClear",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(clear_node)
        if runtime_call == "list.reverse":
            reverse_node: dict[str, Any] = {
                "kind": "ListReverse",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(reverse_node)
        if runtime_call == "list.sort":
            sort_node: dict[str, Any] = {
                "kind": "ListSort",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(sort_node)
        return None

    def _render_builtin_runtime_set_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の set 系 runtime_call を処理する。"""
        owner_node = self._builtin_runtime_owner_node(expr, runtime_call)
        if runtime_call == "set.add":
            if len(arg_nodes) >= 1:
                set_add_node: dict[str, Any] = {
                    "kind": "SetAdd",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(set_add_node)
            return None
        if runtime_call in {"set.discard", "set.remove"}:
            if len(arg_nodes) >= 1:
                set_erase_node: dict[str, Any] = {
                    "kind": "SetErase",
                    "owner": owner_node,
                    "value": arg_nodes[0],
                    "resolved_type": "None",
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(set_erase_node)
            return None
        if runtime_call == "set.clear":
            clear_node: dict[str, Any] = {
                "kind": "SetClear",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(clear_node)
        return None

    def _render_builtin_runtime_dict_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の dict 系 runtime_call を処理する。"""
        if runtime_call not in {"dict.get", "dict.pop", "dict.items", "dict.keys", "dict.values"}:
            return None
        owner_node = self._builtin_runtime_owner_node(expr, runtime_call)
        owner_t = self.get_expr_type(owner_node)
        if runtime_call == "dict.get":
            owner_value_t = ""
            owner_optional_object_dict = False
            if owner_t.startswith("dict[") and owner_t.endswith("]"):
                owner_inner = self.split_generic(owner_t[5:-1])
                if len(owner_inner) == 2:
                    owner_value_t = self.normalize_type_name(owner_inner[1])
            owner_parts: list[str] = []
            if self._contains_text(owner_t, "|"):
                owner_parts = self.split_union(owner_t)
            else:
                owner_parts = [owner_t]
            if len(owner_parts) >= 2:
                has_none = False
                has_dict_object_part = False
                i = 0
                while i < len(owner_parts):
                    p = self.normalize_type_name(owner_parts[i])
                    if p == "None":
                        has_none = True
                    elif p.startswith("dict[") and p.endswith("]"):
                        inner = self.split_generic(p[5:-1])
                        if len(inner) == 2 and self.is_any_like_type(self.normalize_type_name(inner[1])):
                            has_dict_object_part = True
                            if owner_value_t == "":
                                owner_value_t = self.normalize_type_name(inner[1])
                    i += 1
                if has_none and has_dict_object_part:
                    owner_optional_object_dict = True
            objectish_owner = (
                self.is_any_like_type(owner_t)
                or self.is_any_like_type(owner_value_t)
                or owner_optional_object_dict
            )
            if len(arg_nodes) >= 2:
                default_node: Any = arg_nodes[1]
                default_t = self.normalize_type_name(self.get_expr_type(default_node))
                get_default_node: dict[str, Any] = {
                    "kind": "DictGetDefault",
                    "owner": owner_node,
                    "key": arg_nodes[0],
                    "default": default_node,
                    "out_type": self.normalize_type_name(self.any_to_str(expr.get("resolved_type"))),
                    "default_type": default_t,
                    "owner_value_type": owner_value_t,
                    "objectish_owner": objectish_owner,
                    "owner_optional_object_dict": owner_optional_object_dict,
                    "resolved_type": self.any_to_str(expr.get("resolved_type")),
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(get_default_node)
            if len(arg_nodes) == 1:
                maybe_node: dict[str, Any] = {
                    "kind": "DictGetMaybe",
                    "owner": owner_node,
                    "key": arg_nodes[0],
                    "resolved_type": self.any_to_str(expr.get("resolved_type")),
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(maybe_node)
            return None
        if runtime_call == "dict.pop":
            if len(arg_nodes) == 1:
                pop_node: dict[str, Any] = {
                    "kind": "DictPop",
                    "owner": owner_node,
                    "key": arg_nodes[0],
                    "resolved_type": self.any_to_str(expr.get("resolved_type")),
                    "borrow_kind": "value",
                    "casts": [],
                }
                return self.render_expr(pop_node)
            if len(arg_nodes) < 2:
                return None
            owner_t0 = self.get_expr_type(owner_node)
            owner_t2 = owner_t0 if isinstance(owner_t0, str) else ""
            val_t = "Any"
            if owner_t2.startswith("dict[") and owner_t2.endswith("]"):
                inner = self.split_generic(owner_t2[5:-1])
                if len(inner) == 2 and inner[1] != "":
                    val_t = self.normalize_type_name(inner[1])
            pop_default_node: dict[str, Any] = {
                "kind": "DictPopDefault",
                "owner": owner_node,
                "key": arg_nodes[0],
                "default": arg_nodes[1],
                "value_type": val_t,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(pop_default_node)
        if runtime_call == "dict.items":
            items_node: dict[str, Any] = {
                "kind": "DictItems",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(items_node)
        if runtime_call == "dict.keys":
            keys_node: dict[str, Any] = {
                "kind": "DictKeys",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(keys_node)
        if runtime_call == "dict.values":
            values_node: dict[str, Any] = {
                "kind": "DictValues",
                "owner": owner_node,
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(values_node)
        return None

    def _render_builtin_runtime_str_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        arg_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の文字列系 runtime_call を処理する。"""
        if runtime_call not in {
            "py_isdigit",
            "py_isalpha",
            "py_strip",
            "py_rstrip",
            "py_lstrip",
            "py_startswith",
            "py_endswith",
            "py_find",
            "py_rfind",
            "py_replace",
            "py_join",
        }:
            return None
        owner_node = self._builtin_runtime_owner_node(expr, runtime_call)
        if runtime_call == "py_isdigit":
            charclass_node: dict[str, Any] = {
                "kind": "StrCharClassOp",
                "mode": "isdigit",
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                charclass_node["value"] = arg_nodes[0]
            else:
                charclass_node["value"] = owner_node
            return self.render_expr(charclass_node)
        if runtime_call == "py_isalpha":
            charclass_node: dict[str, Any] = {
                "kind": "StrCharClassOp",
                "mode": "isalpha",
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                charclass_node["value"] = arg_nodes[0]
            else:
                charclass_node["value"] = owner_node
            return self.render_expr(charclass_node)
        if runtime_call == "py_strip":
            strip_node: dict[str, Any] = {
                "kind": "StrStripOp",
                "mode": "strip",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                strip_node["chars"] = arg_nodes[0]
            return self.render_expr(strip_node)
        if runtime_call == "py_rstrip":
            rstrip_node: dict[str, Any] = {
                "kind": "StrStripOp",
                "mode": "rstrip",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                rstrip_node["chars"] = arg_nodes[0]
            return self.render_expr(rstrip_node)
        if runtime_call == "py_lstrip":
            lstrip_node: dict[str, Any] = {
                "kind": "StrStripOp",
                "mode": "lstrip",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                lstrip_node["chars"] = arg_nodes[0]
            return self.render_expr(lstrip_node)
        if runtime_call == "py_startswith":
            if len(arg_nodes) >= 1:
                starts_node: dict[str, Any] = {
                    "kind": "StrStartsEndsWith",
                    "mode": "startswith",
                    "owner": owner_node,
                    "needle": arg_nodes[0],
                    "resolved_type": "bool",
                    "borrow_kind": "value",
                    "casts": [],
                }
                if len(arg_nodes) >= 2:
                    starts_node["start"] = arg_nodes[1]
                if len(arg_nodes) >= 3:
                    starts_node["end"] = arg_nodes[2]
                return self.render_expr(starts_node)
        if runtime_call == "py_endswith":
            if len(arg_nodes) >= 1:
                ends_node: dict[str, Any] = {
                    "kind": "StrStartsEndsWith",
                    "mode": "endswith",
                    "owner": owner_node,
                    "needle": arg_nodes[0],
                    "resolved_type": "bool",
                    "borrow_kind": "value",
                    "casts": [],
                }
                if len(arg_nodes) >= 2:
                    ends_node["start"] = arg_nodes[1]
                if len(arg_nodes) >= 3:
                    ends_node["end"] = arg_nodes[2]
                return self.render_expr(ends_node)
        if runtime_call in {"py_find", "py_rfind"}:
            if len(arg_nodes) >= 1:
                find_node: dict[str, Any] = {
                    "kind": "StrFindOp",
                    "mode": "rfind" if runtime_call == "py_rfind" else "find",
                    "owner": owner_node,
                    "needle": arg_nodes[0],
                    "resolved_type": "int64",
                    "borrow_kind": "value",
                    "casts": [],
                }
                if len(arg_nodes) >= 2:
                    find_node["start"] = arg_nodes[1]
                if len(arg_nodes) >= 3:
                    find_node["end"] = arg_nodes[2]
                return self.render_expr(find_node)
        if runtime_call == "py_replace" and len(arg_nodes) >= 2:
            replace_node: dict[str, Any] = {
                "kind": "StrReplace",
                "owner": owner_node,
                "old": arg_nodes[0],
                "new": arg_nodes[1],
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(replace_node)
        if runtime_call == "py_join" and len(arg_nodes) >= 1:
            join_node: dict[str, Any] = {
                "kind": "StrJoin",
                "owner": owner_node,
                "items": arg_nodes[0],
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(join_node)
        return None

    def _render_builtin_runtime_special_ops(
        self,
        runtime_call: str,
        expr: dict[str, Any],
        arg_nodes: list[Any],
        kw_nodes: list[Any],
    ) -> str | None:
        """BuiltinCall の Path/utility 系 runtime_call を処理する。"""
        owner_node = self._builtin_runtime_owner_node(expr, runtime_call)
        if runtime_call == "std::filesystem::create_directories":
            parents_node: Any = None
            exist_ok_node: Any = None
            if len(arg_nodes) >= 1:
                parents_node = arg_nodes[0]
            if len(arg_nodes) >= 2:
                exist_ok_node = arg_nodes[1]
            if parents_node is None:
                kw_names = self._keyword_names_from_builtin_call(expr)
                parents_node = self._keyword_node_by_name(kw_nodes, kw_names, "parents")
            if exist_ok_node is None:
                kw_names = self._keyword_names_from_builtin_call(expr)
                exist_ok_node = self._keyword_node_by_name(kw_nodes, kw_names, "exist_ok")
            mkdir_node: dict[str, Any] = {
                "kind": "PathRuntimeOp",
                "op": "mkdir",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            if parents_node is not None:
                mkdir_node["parents"] = parents_node
            if exist_ok_node is not None:
                mkdir_node["exist_ok"] = exist_ok_node
            return self.render_expr(mkdir_node)
        if runtime_call == "std::filesystem::exists":
            exists_node = {
                "kind": "PathRuntimeOp",
                "op": "exists",
                "owner": owner_node,
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(exists_node)
        if runtime_call == "py_write_text":
            write_node: dict[str, Any] = {
                "kind": "PathRuntimeOp",
                "op": "write_text",
                "owner": owner_node,
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                write_node["value"] = arg_nodes[0]
            return self.render_expr(write_node)
        if runtime_call == "py_read_text":
            read_node = {
                "kind": "PathRuntimeOp",
                "op": "read_text",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(read_node)
        if runtime_call == "path_parent":
            parent_node = {
                "kind": "PathRuntimeOp",
                "op": "parent",
                "owner": owner_node,
                "resolved_type": "Path",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(parent_node)
        if runtime_call == "path_name":
            name_node = {
                "kind": "PathRuntimeOp",
                "op": "name",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(name_node)
        if runtime_call == "path_stem":
            stem_node = {
                "kind": "PathRuntimeOp",
                "op": "stem",
                "owner": owner_node,
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(stem_node)
        if runtime_call == "identity":
            identity_node = {
                "kind": "PathRuntimeOp",
                "op": "identity",
                "owner": owner_node,
                "resolved_type": self.get_expr_type(owner_node),
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(identity_node)
        if runtime_call == "py_print":
            print_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "print",
                "resolved_type": "None",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                print_node["args"] = arg_nodes
            return self.render_expr(print_node)
        if runtime_call == "py_len" and len(arg_nodes) >= 1:
            len_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "len",
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
            len_node["value"] = arg_nodes[0]
            return self.render_expr(len_node)
        if runtime_call == "py_to_string" and len(arg_nodes) >= 1:
            to_string_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "to_string",
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            to_string_node["value"] = arg_nodes[0]
            return self.render_expr(to_string_node)
        if runtime_call == "py_to_int64_base" and len(arg_nodes) >= 2:
            int_base_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "int_base",
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
            int_base_node["args"] = [arg_nodes[0], arg_nodes[1]]
            return self.render_expr(int_base_node)
        if runtime_call == "py_iter_or_raise" and len(arg_nodes) >= 1:
            iter_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "iter_or_raise",
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            iter_node["value"] = arg_nodes[0]
            return self.render_expr(iter_node)
        if runtime_call == "py_next_or_stop" and len(arg_nodes) >= 1:
            next_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "next_or_stop",
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            next_node["value"] = arg_nodes[0]
            return self.render_expr(next_node)
        if runtime_call == "py_reversed" and len(arg_nodes) >= 1:
            reversed_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "reversed",
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            reversed_node["value"] = arg_nodes[0]
            return self.render_expr(reversed_node)
        if runtime_call == "py_enumerate" and len(arg_nodes) >= 1:
            enumerate_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "enumerate",
                "resolved_type": "object",
                "borrow_kind": "value",
                "casts": [],
            }
            enumerate_args: list[Any] = [arg_nodes[0]]
            if len(arg_nodes) >= 2:
                enumerate_args.append(arg_nodes[1])
            enumerate_node["args"] = enumerate_args
            return self.render_expr(enumerate_node)
        if runtime_call == "py_any" and len(arg_nodes) >= 1:
            any_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "any",
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
            any_node["value"] = arg_nodes[0]
            return self.render_expr(any_node)
        if runtime_call == "py_all" and len(arg_nodes) >= 1:
            all_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "all",
                "resolved_type": "bool",
                "borrow_kind": "value",
                "casts": [],
            }
            all_node["value"] = arg_nodes[0]
            return self.render_expr(all_node)
        if runtime_call == "py_ord" and len(arg_nodes) >= 1:
            ord_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "ord",
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            }
            ord_node["value"] = arg_nodes[0]
            return self.render_expr(ord_node)
        if runtime_call == "py_chr" and len(arg_nodes) >= 1:
            chr_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "chr",
                "resolved_type": "str",
                "borrow_kind": "value",
                "casts": [],
            }
            chr_node["value"] = arg_nodes[0]
            return self.render_expr(chr_node)
        if runtime_call == "py_range":
            range_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "range",
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                range_node["args"] = arg_nodes
            kw_names = self._keyword_names_from_builtin_call(expr)
            if len(kw_names) > 0:
                range_node["kw_names"] = kw_names
                range_node["kw_values"] = kw_nodes
            return self.render_expr(range_node)
        if runtime_call == "zip" and len(arg_nodes) >= 2:
            zip_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "zip",
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            zip_node["args"] = [arg_nodes[0], arg_nodes[1]]
            return self.render_expr(zip_node)
        if runtime_call in {"list_ctor", "set_ctor", "dict_ctor"}:
            collection_ctor_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "collection_ctor",
                "ctor_name": runtime_call[:-5],
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                collection_ctor_node["args"] = arg_nodes
            return self.render_expr(collection_ctor_node)
        if runtime_call in {"py_min", "py_max"} and len(arg_nodes) >= 1:
            minmax_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "minmax",
                "mode": "min" if runtime_call == "py_min" else "max",
                "resolved_type": self.any_to_str(expr.get("resolved_type")),
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                minmax_node["args"] = arg_nodes
            return self.render_expr(minmax_node)
        if runtime_call == "perf_counter":
            perf_node = {
                "kind": "RuntimeSpecialOp",
                "op": "perf_counter",
                "resolved_type": "float64",
                "borrow_kind": "value",
                "casts": [],
            }
            return self.render_expr(perf_node)
        if runtime_call == "open":
            open_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "open",
                "resolved_type": "unknown",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                open_node["args"] = arg_nodes
            return self.render_expr(open_node)
        if runtime_call in {"std::runtime_error", "::std::runtime_error"}:
            runtime_error_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "runtime_error",
                "resolved_type": "::std::runtime_error",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                runtime_error_node["message"] = arg_nodes[0]
            return self.render_expr(runtime_error_node)
        if runtime_call == "Path":
            path_ctor_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "path_ctor",
                "resolved_type": "Path",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                path_ctor_node["args"] = arg_nodes
            return self.render_expr(path_ctor_node)
        if runtime_call == "py_int_to_bytes":
            int_to_bytes_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "int_to_bytes",
                "owner": owner_node,
                "resolved_type": "bytes",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) >= 1:
                int_to_bytes_node["length"] = arg_nodes[0]
            if len(arg_nodes) >= 2:
                int_to_bytes_node["byteorder"] = arg_nodes[1]
            return self.render_expr(int_to_bytes_node)
        if runtime_call == "bytes_ctor":
            bytes_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "bytes_ctor",
                "resolved_type": "bytes",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                bytes_node["args"] = arg_nodes
            return self.render_expr(bytes_node)
        if runtime_call == "bytearray_ctor":
            bytearray_node: dict[str, Any] = {
                "kind": "RuntimeSpecialOp",
                "op": "bytearray_ctor",
                "resolved_type": "bytearray",
                "borrow_kind": "value",
                "casts": [],
            }
            if len(arg_nodes) > 0:
                bytearray_node["args"] = arg_nodes
            return self.render_expr(bytearray_node)
        return None

    def _keyword_names_from_builtin_call(self, expr: dict[str, Any]) -> list[str]:
        """BuiltinCall の keyword 名を呼び出し順で返す。"""
        names: list[str] = []
        for kw_obj in self.any_to_list(expr.get("keywords")):
            kw_dict = self.any_to_dict_or_empty(kw_obj)
            if len(kw_dict) == 0:
                continue
            names.append(self.any_dict_get_str(kw_dict, "arg", ""))
        return names

    def _keyword_node_by_name(self, kw_nodes: list[Any], kw_names: list[str], name: str) -> Any | None:
        """keyword ノード列から指定名の value ノードを取得する。"""
        i = 0
        while i < len(kw_nodes):
            if i < len(kw_names) and kw_names[i] == name:
                return kw_nodes[i]
            i += 1
        return None


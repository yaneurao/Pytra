"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.code_emitter import EmitterHooks


def _render_owner_expr(emitter: Any, func_node: dict[str, Any]) -> str:
    """Attribute call の owner 式を C++ 向けに整形する。"""
    owner_node = emitter.any_to_dict_or_empty(func_node.get("value"))
    owner_expr = emitter.render_expr(func_node.get("value"))
    owner_kind = emitter.any_dict_get_str(owner_node, "kind", "")
    if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
        owner_expr = "(" + owner_expr + ")"
    return owner_expr


def _infer_runtime_call_from_func_node(emitter: Any, func_node: dict[str, Any]) -> str:
    """Call ノードの func から runtime_call を推定する。"""
    fn_kind = emitter.any_dict_get_str(func_node, "kind", "")
    if fn_kind == "Name":
        fn_name = emitter.any_dict_get_str(func_node, "id", "")
        if fn_name == "":
            return ""
        sym = emitter._resolve_imported_symbol(fn_name)
        module_name = emitter.any_dict_get_str(sym, "module", "")
        symbol_name = emitter.any_dict_get_str(sym, "name", "")
        if module_name != "" and symbol_name != "":
            mapped = emitter._resolve_runtime_call_for_imported_symbol(module_name, symbol_name)
            if isinstance(mapped, str) and mapped != "":
                return mapped
        return ""
    if fn_kind == "Attribute":
        owner_expr = emitter.render_expr(func_node.get("value"))
        owner_mod = emitter._resolve_imported_module_name(owner_expr)
        if owner_mod == "":
            owner_mod = emitter._cpp_expr_to_module_name(owner_expr)
        owner_mod = emitter._normalize_runtime_module_name(owner_mod)
        attr = emitter.any_dict_get_str(func_node, "attr", "")
        if owner_mod != "" and attr != "":
            return emitter._lookup_module_attr_runtime_call(owner_mod, attr)
    return ""


def _looks_like_runtime_symbol(name: str) -> bool:
    """ランタイム関数シンボルとして直接出力できる文字列か判定する。"""
    if name == "":
        return False
    if "::" in name:
        return True
    if name.startswith("py_"):
        return True
    ch0 = name[0:1]
    if ch0 != "" and ((ch0 >= "0" and ch0 <= "9") or ch0 == "-" or ch0 == "+"):
        return True
    return False


def _render_runtime_call_list_ops(
    emitter: Any,
    runtime_call: str,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
) -> str:
    """`runtime_call` の list 系（append/extend/pop/clear/reverse/sort）を処理する。"""
    if runtime_call == "list.append":
        owner_node: object = func_node.get("value")
        owner = emitter.render_expr(owner_node)
        a0 = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        owner_t0 = emitter.get_expr_type(owner_node)
        owner_t = owner_t0 if isinstance(owner_t0, str) else ""
        if owner_t == "bytearray":
            a0 = "static_cast<uint8>(py_to_int64(" + a0 + "))"
        if owner_t.startswith("list[") and owner_t.endswith("]"):
            inner_t = owner_t[5:-1].strip()
            if inner_t != "" and not emitter.is_any_like_type(inner_t):
                if inner_t == "uint8":
                    a0 = "static_cast<uint8>(py_to_int64(" + a0 + "))"
                else:
                    a0 = emitter._cpp_type_text(inner_t) + "(" + a0 + ")"
        return owner + ".append(" + a0 + ")"
    if runtime_call == "list.extend":
        owner = emitter.render_expr(func_node.get("value"))
        a0 = rendered_args[0] if len(rendered_args) >= 1 else "{}"
        return owner + ".insert(" + owner + ".end(), " + a0 + ".begin(), " + a0 + ".end())"
    if runtime_call == "list.pop":
        owner = emitter.render_expr(func_node.get("value"))
        if len(rendered_args) == 0:
            return owner + ".pop()"
        return owner + ".pop(" + rendered_args[0] + ")"
    if runtime_call == "list.clear":
        owner = emitter.render_expr(func_node.get("value"))
        return owner + ".clear()"
    if runtime_call == "list.reverse":
        owner = emitter.render_expr(func_node.get("value"))
        return "::std::reverse(" + owner + ".begin(), " + owner + ".end())"
    if runtime_call == "list.sort":
        owner = emitter.render_expr(func_node.get("value"))
        return "::std::sort(" + owner + ".begin(), " + owner + ".end())"
    return ""


def _render_runtime_call_set_ops(
    emitter: Any,
    runtime_call: str,
    func_node: dict[str, Any],
    rendered_args: list[str],
) -> str:
    """`runtime_call` の set 系（add/discard/remove/clear）を処理する。"""
    if runtime_call == "set.add":
        owner = emitter.render_expr(func_node.get("value"))
        a0 = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        return owner + ".insert(" + a0 + ")"
    if runtime_call in {"set.discard", "set.remove"}:
        owner = emitter.render_expr(func_node.get("value"))
        a0 = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        return owner + ".erase(" + a0 + ")"
    if runtime_call == "set.clear":
        owner = emitter.render_expr(func_node.get("value"))
        return owner + ".clear()"
    return ""


def _render_runtime_call_dict_ops(
    emitter: Any,
    runtime_call: str,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
) -> str:
    """`runtime_call` の dict 系（get/pop/items/keys/values）を処理する。"""
    if runtime_call == "dict.get":
        owner_node: object = func_node.get("value")
        owner = emitter.render_expr(owner_node)
        owner_t = emitter.get_expr_type(owner_node)
        owner_value_t = ""
        owner_optional_object_dict = False
        if owner_t.startswith("dict[") and owner_t.endswith("]"):
            owner_inner = emitter.split_generic(owner_t[5:-1])
            if len(owner_inner) == 2:
                owner_value_t = emitter.normalize_type_name(owner_inner[1])
        owner_parts: list[str] = []
        if emitter._contains_text(owner_t, "|"):
            owner_parts = emitter.split_union(owner_t)
        else:
            owner_parts = [owner_t]
        if len(owner_parts) >= 2:
            has_none = False
            has_dict_object_part = False
            i = 0
            while i < len(owner_parts):
                p = emitter.normalize_type_name(owner_parts[i])
                if p == "None":
                    has_none = True
                elif p.startswith("dict[") and p.endswith("]"):
                    inner = emitter.split_generic(p[5:-1])
                    if len(inner) == 2 and emitter.is_any_like_type(emitter.normalize_type_name(inner[1])):
                        has_dict_object_part = True
                        if owner_value_t == "":
                            owner_value_t = emitter.normalize_type_name(inner[1])
                i += 1
            if has_none and has_dict_object_part:
                owner_optional_object_dict = True
        objectish_owner = (
            emitter.is_any_like_type(owner_t)
            or emitter.is_any_like_type(owner_value_t)
            or owner_optional_object_dict
        )
        key_expr = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        arg_nodes = emitter.any_to_list(call_node.get("args"))
        key_node: Any = None
        if len(arg_nodes) >= 1:
            key_node = arg_nodes[0]
        if not objectish_owner:
            key_expr = emitter._coerce_dict_key_expr(owner_node, key_expr, key_node)
        if len(rendered_args) >= 2:
            out_t = emitter.normalize_type_name(emitter.any_to_str(call_node.get("resolved_type")))
            int_out_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
            float_out_types = {"float32", "float64"}
            default_t = ""
            default_node: Any = None
            if len(arg_nodes) >= 2:
                default_node = arg_nodes[1]
            if default_node is not None:
                default_t = emitter.normalize_type_name(emitter.get_expr_type(default_node))
            if objectish_owner and out_t == "bool":
                return "dict_get_bool(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t == "str":
                return "dict_get_str(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t in int_out_types:
                cast_t = emitter._cpp_type_text(out_t)
                return "static_cast<" + cast_t + ">(dict_get_int(" + owner + ", " + key_expr + ", py_to_int64(" + rendered_args[1] + ")))"
            if objectish_owner and out_t in float_out_types:
                cast_t = emitter._cpp_type_text(out_t)
                return "static_cast<" + cast_t + ">(dict_get_float(" + owner + ", " + key_expr + ", py_to_float64(" + rendered_args[1] + ")))"
            if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "bool":
                return "dict_get_bool(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t == "str":
                return "dict_get_str(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in int_out_types:
                return "dict_get_int(" + owner + ", " + key_expr + ", py_to_int64(" + rendered_args[1] + "))"
            if objectish_owner and out_t in {"", "unknown", "Any", "object"} and default_t in float_out_types:
                return "dict_get_float(" + owner + ", " + key_expr + ", py_to_float64(" + rendered_args[1] + "))"
            # `resolved_type` が unknown でも list 既定値から型が分かる場合は
            # `py_dict_get_default(..., make_object(...))` を避ける。
            if objectish_owner and out_t in {"", "unknown"} and default_t.startswith("list["):
                return "dict_get_list(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t.startswith("list["):
                return "dict_get_list(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and (emitter.is_any_like_type(out_t) or out_t == "object"):
                if owner_optional_object_dict:
                    return "py_dict_get_default(" + owner + ", " + key_expr + ", make_object(" + rendered_args[1] + "))"
                return "dict_get_node(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if not objectish_owner:
                default_expr = rendered_args[1]
                val_t = emitter.normalize_type_name(owner_value_t)
                # `dict[K, V].get(key, None)` で V が optional でない場合は、
                # C++ 既定値を V{} に変換して `::std::nullopt` 混入を防ぐ。
                if default_expr in {"::std::nullopt", "std::nullopt"} and val_t not in {"", "None"}:
                    allows_nullopt = False
                    if val_t.startswith("optional[") and val_t.endswith("]"):
                        allows_nullopt = True
                    elif emitter._contains_text(val_t, "|"):
                        parts = emitter.split_union(val_t)
                        i = 0
                        while i < len(parts):
                            if emitter.normalize_type_name(parts[i]) == "None":
                                allows_nullopt = True
                                break
                            i += 1
                    if (not allows_nullopt) and (not emitter.is_any_like_type(val_t)):
                        default_expr = emitter._cpp_type_text(val_t) + "()"
                return owner + ".get(" + key_expr + ", " + default_expr + ")"
            if owner_optional_object_dict:
                return "py_dict_get_default(" + owner + ", " + key_expr + ", make_object(" + rendered_args[1] + "))"
            return "py_dict_get_default(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
        if len(rendered_args) == 1:
            return "py_dict_get_maybe(" + owner + ", " + key_expr + ")"
        return ""
    if runtime_call == "dict.pop":
        owner_node = func_node.get("value")
        owner = emitter.render_expr(owner_node)
        key_expr = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        arg_nodes = emitter.any_to_list(call_node.get("args"))
        key_node: Any = None
        if len(arg_nodes) >= 1:
            key_node = arg_nodes[0]
        key_expr = emitter._coerce_dict_key_expr(owner_node, key_expr, key_node)
        if len(rendered_args) <= 1:
            return owner + ".pop(" + key_expr + ")"
        owner_t0 = emitter.get_expr_type(owner_node)
        owner_t = owner_t0 if isinstance(owner_t0, str) else ""
        val_t = "Any"
        if owner_t.startswith("dict[") and owner_t.endswith("]"):
            inner = emitter.split_generic(owner_t[5:-1])
            if len(inner) == 2 and inner[1] != "":
                val_t = emitter.normalize_type_name(inner[1])
        default_expr = rendered_args[1]
        if default_expr in {"::std::nullopt", "std::nullopt"} and not emitter.is_any_like_type(val_t) and val_t != "None":
            default_expr = emitter._cpp_type_text(val_t) + "()"
        return "(" + owner + ".contains(" + key_expr + ") ? " + owner + ".pop(" + key_expr + ") : " + default_expr + ")"
    if runtime_call == "dict.items":
        return emitter.render_expr(func_node.get("value"))
    if runtime_call == "dict.keys":
        owner = emitter.render_expr(func_node.get("value"))
        return "py_dict_keys(" + owner + ")"
    if runtime_call == "dict.values":
        owner = emitter.render_expr(func_node.get("value"))
        return "py_dict_values(" + owner + ")"
    return ""


def _render_runtime_call_str_ops(
    emitter: Any,
    runtime_call: str,
    func_node: dict[str, Any],
    rendered_args: list[str],
) -> str:
    """`runtime_call` の文字列系（strip/startswith/replace/join など）を処理する。"""
    owner_node = emitter.any_to_dict_or_empty(func_node.get("value"))
    owner = emitter.render_expr(func_node.get("value"))
    owner_kind = emitter._node_kind_from_dict(owner_node)
    if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
        owner = "(" + owner + ")"
    if runtime_call == "py_isdigit":
        if len(rendered_args) == 0:
            return owner + ".isdigit()"
        if len(rendered_args) == 1:
            return rendered_args[0] + ".isdigit()"
    if runtime_call == "py_isalpha":
        if len(rendered_args) == 0:
            return owner + ".isalpha()"
        if len(rendered_args) == 1:
            return rendered_args[0] + ".isalpha()"
    if runtime_call == "py_strip":
        if len(rendered_args) == 0:
            return "py_strip(" + owner + ")"
        if len(rendered_args) == 1:
            return owner + ".strip(" + rendered_args[0] + ")"
    if runtime_call == "py_rstrip":
        if len(rendered_args) == 0:
            return "py_rstrip(" + owner + ")"
        if len(rendered_args) == 1:
            return owner + ".rstrip(" + rendered_args[0] + ")"
    if runtime_call == "py_lstrip":
        if len(rendered_args) == 0:
            return "py_lstrip(" + owner + ")"
        if len(rendered_args) == 1:
            return owner + ".lstrip(" + rendered_args[0] + ")"
    if runtime_call == "py_startswith":
        if len(rendered_args) == 1:
            return "py_startswith(" + owner + ", " + rendered_args[0] + ")"
        if len(rendered_args) == 2:
            start = "py_to_int64(" + rendered_args[1] + ")"
            return "py_startswith(py_slice(" + owner + ", " + start + ", py_len(" + owner + ")), " + rendered_args[0] + ")"
        if len(rendered_args) >= 3:
            start = "py_to_int64(" + rendered_args[1] + ")"
            end = "py_to_int64(" + rendered_args[2] + ")"
            return "py_startswith(py_slice(" + owner + ", " + start + ", " + end + "), " + rendered_args[0] + ")"
    if runtime_call == "py_endswith":
        if len(rendered_args) == 1:
            return "py_endswith(" + owner + ", " + rendered_args[0] + ")"
        if len(rendered_args) == 2:
            start = "py_to_int64(" + rendered_args[1] + ")"
            return "py_endswith(py_slice(" + owner + ", " + start + ", py_len(" + owner + ")), " + rendered_args[0] + ")"
        if len(rendered_args) >= 3:
            start = "py_to_int64(" + rendered_args[1] + ")"
            end = "py_to_int64(" + rendered_args[2] + ")"
            return "py_endswith(py_slice(" + owner + ", " + start + ", " + end + "), " + rendered_args[0] + ")"
    if runtime_call == "py_replace" and len(rendered_args) == 2:
        return "py_replace(" + owner + ", " + rendered_args[0] + ", " + rendered_args[1] + ")"
    if runtime_call == "py_join" and len(rendered_args) == 1:
        return "str(" + owner + ").join(" + rendered_args[0] + ")"
    return ""


def _resolve_runtime_owner_expr(
    emitter: Any,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
) -> str:
    """BuiltinCall の owner 式（`obj.method` 側）を解決する。"""
    if emitter.any_dict_get_str(func_node, "kind", "") != "Attribute":
        return ""
    runtime_owner_obj: object = call_node.get("runtime_owner")
    runtime_owner_node = emitter.any_to_dict_or_empty(runtime_owner_obj)
    if len(runtime_owner_node) > 0:
        return emitter.render_expr(runtime_owner_obj)
    return _render_owner_expr(emitter, func_node)


def _render_runtime_call_direct_builtin(
    emitter: Any,
    runtime_call: str,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
) -> str:
    """BuiltinCall の汎用 runtime_call（py_/std:: 直接呼び出し）を処理する。"""
    if runtime_call == "static_cast":
        if len(rendered_args) == 1:
            target = emitter.cpp_type(call_node.get("resolved_type"))
            arg_nodes = emitter.any_to_list(call_node.get("args"))
            first_arg: object = call_node
            if len(arg_nodes) > 0:
                first_arg = arg_nodes[0]
            arg_t = emitter.get_expr_type(first_arg)
            numeric_t = {
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
            }
            if target == "int64" and arg_t == "str":
                return "py_to_int64(" + rendered_args[0] + ")"
            if target in {"float64", "float32"} and arg_t == "str":
                return "py_to_float64(" + rendered_args[0] + ")"
            if target == "int64" and arg_t in numeric_t:
                return "int64(" + rendered_args[0] + ")"
            if target == "int64" and emitter.is_any_like_type(arg_t):
                return "py_to_int64(" + rendered_args[0] + ")"
            if target in {"float64", "float32"} and emitter.is_any_like_type(arg_t):
                return "py_to_float64(" + rendered_args[0] + ")"
            if target == "bool" and emitter.is_any_like_type(arg_t):
                return "py_to_bool(" + rendered_args[0] + ")"
            if target == "int64":
                return "py_to_int64(" + rendered_args[0] + ")"
            return "static_cast<" + target + ">(" + rendered_args[0] + ")"
        if len(rendered_args) == 2 and emitter.any_dict_get_str(call_node, "builtin_name", "") == "int":
            return "py_to_int64_base(" + rendered_args[0] + ", py_to_int64(" + rendered_args[1] + "))"
    if runtime_call == "py_print":
        return "py_print(" + ", ".join(rendered_args) + ")"
    if runtime_call == "py_len" and len(rendered_args) == 1:
        return "py_len(" + rendered_args[0] + ")"
    if runtime_call == "py_to_string" and len(rendered_args) == 1:
        arg_nodes = emitter.any_to_list(call_node.get("args"))
        src_expr: object = call_node
        if len(arg_nodes) > 0:
            src_expr = arg_nodes[0]
        return emitter.render_to_string(src_expr)
    if runtime_call in {"py_min", "py_max"} and len(rendered_args) >= 1:
        fn_name = "min" if runtime_call == "py_min" else "max"
        arg_nodes = emitter.any_to_list(call_node.get("args"))
        resolved_type = emitter.any_to_str(call_node.get("resolved_type"))
        return emitter.render_minmax(fn_name, rendered_args, resolved_type, arg_nodes)
    if runtime_call == "perf_counter":
        return "pytra::std::time::perf_counter()"
    if runtime_call == "open":
        return "open(" + ", ".join(rendered_args) + ")"
    if runtime_call == "py_int_to_bytes":
        owner = emitter.render_expr(func_node.get("value"))
        length = rendered_args[0] if len(rendered_args) >= 1 else "0"
        byteorder = rendered_args[1] if len(rendered_args) >= 2 else '"little"'
        return "py_int_to_bytes(" + owner + ", " + length + ", " + byteorder + ")"
    if runtime_call == "py_join" and len(rendered_args) == 1:
        owner = _resolve_runtime_owner_expr(emitter, call_node, func_node)
        if owner != "":
            return "str(" + owner + ").join(" + rendered_args[0] + ")"
    if runtime_call in {"std::runtime_error", "::std::runtime_error"}:
        if len(rendered_args) == 0:
            return '::std::runtime_error("error")'
        return "::std::runtime_error(" + rendered_args[0] + ")"
    if runtime_call == "Path":
        return "Path(" + ", ".join(rendered_args) + ")"
    if runtime_call in {"std::filesystem::exists", "::std::filesystem::exists"}:
        owner = _resolve_runtime_owner_expr(emitter, call_node, func_node)
        if owner != "" and len(rendered_args) == 0:
            return runtime_call + "(" + owner + ")"
    if runtime_call == "py_replace":
        owner = _resolve_runtime_owner_expr(emitter, call_node, func_node)
        if owner != "" and len(rendered_args) >= 2:
            return "py_replace(" + owner + ", " + rendered_args[0] + ", " + rendered_args[1] + ")"
    if runtime_call in {"py_startswith", "py_endswith", "py_find", "py_rfind"}:
        owner = _resolve_runtime_owner_expr(emitter, call_node, func_node)
        if owner != "" and len(rendered_args) >= 1:
            return runtime_call + "(" + owner + ", " + ", ".join(rendered_args) + ")"
    if runtime_call != "" and (emitter._is_std_runtime_call(runtime_call) or runtime_call.startswith("py_")):
        owner = _resolve_runtime_owner_expr(emitter, call_node, func_node)
        if owner != "" and runtime_call.startswith("py_") and len(rendered_args) == 0:
            return runtime_call + "(" + owner + ")"
        return runtime_call + "(" + ", ".join(rendered_args) + ")"
    return ""


def on_render_call(
    emitter: Any,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
    rendered_kwargs: dict[str, str],
) -> str | None:
    """Call 式出力フック。文字列を返すとその式を採用する。"""
    runtime_call = emitter.any_dict_get_str(call_node, "runtime_call", "")
    if runtime_call == "":
        runtime_call = _infer_runtime_call_from_func_node(emitter, func_node)
    direct = _render_runtime_call_direct_builtin(emitter, runtime_call, call_node, func_node, rendered_args)
    if direct != "":
        return direct
    list_ops = _render_runtime_call_list_ops(emitter, runtime_call, call_node, func_node, rendered_args)
    if list_ops != "":
        return list_ops
    set_ops = _render_runtime_call_set_ops(emitter, runtime_call, func_node, rendered_args)
    if set_ops != "":
        return set_ops
    dict_ops = _render_runtime_call_dict_ops(emitter, runtime_call, call_node, func_node, rendered_args)
    if dict_ops != "":
        return dict_ops
    str_ops = _render_runtime_call_str_ops(emitter, runtime_call, func_node, rendered_args)
    if str_ops != "":
        return str_ops
    if runtime_call == "std::filesystem::create_directories":
        owner = _render_owner_expr(emitter, func_node)
        parents = rendered_kwargs.get("parents", "false")
        exist_ok = rendered_kwargs.get("exist_ok", "false")
        if len(rendered_args) >= 1:
            parents = rendered_args[0]
        if len(rendered_args) >= 2:
            exist_ok = rendered_args[1]
        return owner + ".mkdir(" + parents + ", " + exist_ok + ")"
    if runtime_call == "std::filesystem::exists":
        owner = _render_owner_expr(emitter, func_node)
        return owner + ".exists()"
    if runtime_call == "py_write_text":
        owner = _render_owner_expr(emitter, func_node)
        write_arg = rendered_args[0] if len(rendered_args) >= 1 else '""'
        return owner + ".write_text(" + write_arg + ")"
    if runtime_call == "py_read_text":
        owner = _render_owner_expr(emitter, func_node)
        return owner + ".read_text()"
    if runtime_call == "path_parent":
        owner = _render_owner_expr(emitter, func_node)
        return owner + ".parent()"
    if runtime_call == "path_name":
        owner = _render_owner_expr(emitter, func_node)
        return owner + ".name()"
    if runtime_call == "path_stem":
        owner = _render_owner_expr(emitter, func_node)
        return owner + ".stem()"
    if runtime_call == "identity":
        owner = _render_owner_expr(emitter, func_node)
        return owner
    return None


def on_emit_stmt_kind(
    emitter: Any,
    kind: str,
    stmt: dict[str, Any],
) -> bool | None:
    """stmt kind 単位の出力フック。terminal 文の処理を先行させる。"""
    if kind in {"Expr", "Return", "Pass", "Break", "Continue", "Import", "ImportFrom"}:
        emitter.emit_leading_comments(stmt)
    if kind == "Expr":
        emitter._emit_expr_stmt(stmt)
        return True
    if kind == "Return":
        emitter._emit_return_stmt(stmt)
        return True
    if kind == "Pass":
        emitter._emit_pass_stmt(stmt)
        return True
    if kind == "Break":
        emitter._emit_break_stmt(stmt)
        return True
    if kind == "Continue":
        emitter._emit_continue_stmt(stmt)
        return True
    if kind == "Import" or kind == "ImportFrom":
        emitter._emit_noop_stmt(stmt)
        return True
    return None


def _can_omit_braces_for_single_stmt(emitter: Any, stmts: list[dict[str, Any]]) -> bool:
    """単文ブロックで波括弧を省略可能か判定する。"""
    if not emitter._opt_ge(1):
        return False
    if len(stmts) != 1:
        return False
    one = stmts[0]
    k = emitter.any_dict_get_str(one, "kind", "")
    if k == "Assign":
        tgt = emitter.any_to_dict_or_empty(one.get("target"))
        # tuple assign は C++ で複数行へ展開されるため単文扱い不可
        if emitter._node_kind_from_dict(tgt) == "Tuple":
            return False
    return k in {"Return", "Expr", "Assign", "AnnAssign", "AugAssign", "Swap", "Raise", "Break", "Continue"}


def on_stmt_omit_braces(
    emitter: Any,
    kind: str,
    stmt: dict[str, Any],
    default_value: bool,
) -> bool:
    """制御構文の brace 省略可否を C++ 方針で決定する。"""
    if not emitter._opt_ge(1):
        return False
    body_stmts = emitter._dict_stmt_list(stmt.get("body"))
    if kind == "If":
        else_stmts = emitter._dict_stmt_list(stmt.get("orelse"))
        if not _can_omit_braces_for_single_stmt(emitter, body_stmts):
            return False
        if len(else_stmts) == 0:
            return True
        return _can_omit_braces_for_single_stmt(emitter, else_stmts)
    if kind == "ForRange":
        if len(emitter.any_dict_get_list(stmt, "orelse")) != 0:
            return False
        return _can_omit_braces_for_single_stmt(emitter, body_stmts)
    if kind == "For":
        if len(emitter.any_dict_get_list(stmt, "orelse")) != 0:
            return False
        target = emitter.any_to_dict_or_empty(stmt.get("target"))
        if emitter._node_kind_from_dict(target) == "Tuple":
            # tuple unpack は束縛文を追加出力するため常に block 必須。
            return False
        return _can_omit_braces_for_single_stmt(emitter, body_stmts)
    return default_value


def on_for_range_mode(
    emitter: Any,
    stmt: dict[str, Any],
    default_mode: str,
) -> str:
    """ForRange の mode を C++ 側で解決する。"""
    mode = emitter.any_to_str(stmt.get("range_mode"))
    if mode == "":
        mode = default_mode
    if mode in {"ascending", "descending", "dynamic"}:
        return mode
    return default_mode


def on_render_module_method(
    emitter: Any,
    module_name: str,
    attr: str,
    rendered_args: list[str],
    rendered_kwargs: dict[str, str],
    arg_nodes: list[Any],
) -> str | None:
    """module.method(...) の C++ 固有分岐を処理する。"""
    merged_args = emitter.merge_call_args(rendered_args, rendered_kwargs)
    owner_mod_norm = emitter._normalize_runtime_module_name(module_name)
    render_namespaced = getattr(emitter, "_render_namespaced_module_call", None)
    if owner_mod_norm in emitter.module_namespace_map:
        ns = emitter.module_namespace_map[owner_mod_norm]
        if callable(render_namespaced):
            rendered = render_namespaced(module_name, ns, attr, merged_args, arg_nodes)
            if isinstance(rendered, str) and rendered != "":
                return rendered
        if ns != "":
            call_args = emitter._coerce_args_for_module_function(module_name, attr, merged_args, arg_nodes)
            return ns + "::" + attr + "(" + ", ".join(call_args) + ")"
    mapped = emitter._lookup_module_attr_runtime_call(owner_mod_norm, attr)
    if mapped != "" and _looks_like_runtime_symbol(mapped):
        if emitter._contains_text(mapped, "::"):
            call_args = emitter._coerce_args_for_module_function(module_name, attr, merged_args, arg_nodes)
        else:
            call_args = merged_args
        return mapped + "(" + ", ".join(call_args) + ")"
    ns = emitter._module_name_to_cpp_namespace(owner_mod_norm)
    if callable(render_namespaced):
        rendered = render_namespaced(module_name, ns, attr, merged_args, arg_nodes)
        if isinstance(rendered, str) and rendered != "":
            return rendered
    if ns != "":
        call_args = emitter._coerce_args_for_module_function(module_name, attr, merged_args, arg_nodes)
        return ns + "::" + attr + "(" + ", ".join(call_args) + ")"
    return None


def on_render_object_method(
    emitter: Any,
    owner_type: str,
    owner_expr: str,
    attr: str,
    rendered_args: list[str],
) -> str | None:
    """obj.method(...) の C++ 固有分岐を処理する。"""
    owner_types: list[str] = [owner_type]
    if emitter._contains_text(owner_type, "|"):
        owner_types = emitter.split_union(owner_type)
    if owner_type == "unknown" and attr == "clear":
        return owner_expr + ".clear()"
    if attr == "append":
        append_rendered = emitter._render_append_call_object_method(owner_types, owner_expr, rendered_args)
        if isinstance(append_rendered, str) and append_rendered != "":
            return append_rendered
    if attr in {"strip", "lstrip", "rstrip"}:
        if len(rendered_args) == 0:
            return "py_" + attr + "(" + owner_expr + ")"
        if len(rendered_args) == 1:
            return "py_" + attr + "(" + owner_expr + ", " + rendered_args[0] + ")"
    if attr in {"startswith", "endswith"} and len(rendered_args) >= 1:
        return "py_" + attr + "(" + owner_expr + ", " + rendered_args[0] + ")"
    if attr == "replace" and len(rendered_args) >= 2:
        return "py_replace(" + owner_expr + ", " + rendered_args[0] + ", " + rendered_args[1] + ")"
    if "str" in owner_types:
        if attr in {"isdigit", "isalpha", "isalnum", "isspace", "lower", "upper"} and len(rendered_args) == 0:
            return owner_expr + "." + attr + "()"
        if attr in {"find", "rfind"}:
            return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"
    return None


def on_render_class_method(
    emitter: Any,
    owner_type: str,
    attr: str,
    func_node: dict[str, Any],
    rendered_args: list[str],
    rendered_kwargs: dict[str, str],
    arg_nodes: list[Any],
) -> str | None:
    """`Class.method(...)` の C++ 固有分岐を処理する。"""
    method_sig = emitter._class_method_sig(owner_type, attr)
    if len(method_sig) == 0:
        return None
    call_args = emitter.merge_call_args(rendered_args, rendered_kwargs)
    call_args = emitter._coerce_args_for_class_method(owner_type, attr, call_args, arg_nodes)
    fn_expr = emitter._render_attribute_expr(func_node)
    return fn_expr + "(" + ", ".join(call_args) + ")"


def on_render_binop(
    emitter: Any,
    binop_node: dict[str, Any],
    left: str,
    right: str,
) -> str | None:
    """BinOp の C++ 固有分岐を処理する。"""
    op_name = emitter.any_to_str(binop_node.get("op"))
    casts = emitter.any_to_list(binop_node.get("casts"))

    if op_name == "Div":
        lt0 = emitter.get_expr_type(binop_node.get("left"))
        rt0 = emitter.get_expr_type(binop_node.get("right"))
        lt = lt0 if isinstance(lt0, str) else ""
        rt = rt0 if isinstance(rt0, str) else ""
        if lt == "Path" and rt in {"str", "Path"}:
            return left + " / " + right
        if len(casts) > 0 or lt in {"float32", "float64"} or rt in {"float32", "float64"}:
            return left + " / " + right
        return "py_div(" + left + ", " + right + ")"

    if op_name == "FloorDiv":
        if emitter.floor_div_mode == "python":
            return "py_floordiv(" + left + ", " + right + ")"
        return left + " / " + right

    if op_name == "Mod":
        if emitter.mod_mode == "python":
            return "py_mod(" + left + ", " + right + ")"
        return left + " % " + right

    if op_name == "Mult":
        lt0 = emitter.get_expr_type(binop_node.get("left"))
        rt0 = emitter.get_expr_type(binop_node.get("right"))
        lt = lt0 if isinstance(lt0, str) else ""
        rt = rt0 if isinstance(rt0, str) else ""
        int_types = {"int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8"}
        if lt.startswith("list[") and rt in int_types:
            return "py_repeat(" + left + ", " + right + ")"
        if rt.startswith("list[") and lt in int_types:
            return "py_repeat(" + right + ", " + left + ")"
        if lt == "str" and rt in int_types:
            return "py_repeat(" + left + ", " + right + ")"
        if rt == "str" and lt in int_types:
            return "py_repeat(" + right + ", " + left + ")"

    return None


def on_render_expr_kind(
    emitter: Any,
    kind: str,
    expr_node: dict[str, Any],
) -> str | None:
    """式 kind 単位の出力フック。"""
    if kind == "RangeExpr":
        start = emitter.render_expr(expr_node.get("start"))
        stop = emitter.render_expr(expr_node.get("stop"))
        step = emitter.render_expr(expr_node.get("step"))
        return "py_range(" + start + ", " + stop + ", " + step + ")"
    if kind == "Compare":
        if emitter.any_dict_get_str(expr_node, "lowered_kind", "") == "Contains":
            container = emitter.render_expr(expr_node.get("container"))
            key = emitter.render_expr(expr_node.get("key"))
            base = "py_contains(" + container + ", " + key + ")"
            if emitter.any_to_bool(expr_node.get("negated")):
                return "!(" + base + ")"
            return base
        return None
    return None


def on_render_expr_leaf(
    emitter: Any,
    kind: str,
    expr_node: dict[str, Any],
) -> str | None:
    """leaf 式（Name/Constant/Attribute）向けの出力フック。"""
    if kind != "Attribute":
        return None
    base_raw = emitter.render_expr(expr_node.get("value"))
    owner_ctx = emitter.resolve_attribute_owner_context(expr_node.get("value"), base_raw)
    owner_node = emitter.any_to_dict_or_empty(owner_ctx.get("node"))
    owner_kind = emitter.any_dict_get_str(owner_ctx, "kind", "")
    base_expr = emitter.any_dict_get_str(owner_ctx, "expr", "")
    attr = emitter.attr_name(expr_node)
    direct_self_or_class = emitter.render_attribute_self_or_class_access(
        base_expr,
        attr,
        emitter.current_class_name,
        emitter.current_class_static_fields,
        emitter.class_base,
        emitter.class_method_names,
    )
    if direct_self_or_class != "":
        return direct_self_or_class
    owner_t = emitter.get_expr_type(expr_node.get("value"))
    base_mod = emitter.any_dict_get_str(owner_ctx, "module", "")
    if base_mod == "":
        base_mod = emitter._cpp_expr_to_module_name(base_raw)
    base_mod = emitter._normalize_runtime_module_name(base_mod)
    if owner_t == "Path":
        if attr == "name":
            return base_expr + ".name()"
        if attr == "stem":
            return base_expr + ".stem()"
        if attr == "parent":
            return base_expr + ".parent()"
    mapped = ""
    if owner_kind in {"Name", "Attribute"} and attr != "":
        mapped = emitter._lookup_module_attr_runtime_call(base_mod, attr)
    if _looks_like_runtime_symbol(mapped) or (base_mod != "" and attr != ""):
        ns = emitter._module_name_to_cpp_namespace(base_mod) if base_mod != "" else ""
        direct_module = emitter.render_attribute_module_access(base_mod, attr, mapped, ns)
        if direct_module != "":
            return direct_module
    return None


def on_render_expr_complex(
    emitter: Any,
    expr_node: dict[str, Any],
) -> str | None:
    """複雑式（JoinedStr/Lambda など）向けの出力フック。"""
    kind = emitter.any_dict_get_str(expr_node, "kind", "")
    if kind == "JoinedStr":
        render_joined = getattr(emitter, "_render_joinedstr_expr", None)
        if callable(render_joined):
            return render_joined(expr_node)
    if kind == "Lambda":
        render_lambda = getattr(emitter, "_render_lambda_expr", None)
        if callable(render_lambda):
            return render_lambda(expr_node)
    return None


def build_cpp_hooks() -> dict[str, Any]:
    """C++ エミッタへ注入する hooks dict を構築する。"""
    hooks = EmitterHooks()
    hooks.add("on_emit_stmt_kind", on_emit_stmt_kind)
    hooks.add("on_stmt_omit_braces", on_stmt_omit_braces)
    hooks.add("on_for_range_mode", on_for_range_mode)
    hooks.add("on_render_call", on_render_call)
    hooks.add("on_render_module_method", on_render_module_method)
    hooks.add("on_render_object_method", on_render_object_method)
    hooks.add("on_render_class_method", on_render_class_method)
    hooks.add("on_render_binop", on_render_binop)
    hooks.add("on_render_expr_kind", on_render_expr_kind)
    hooks.add("on_render_expr_leaf", on_render_expr_leaf)
    hooks.add("on_render_expr_complex", on_render_expr_complex)
    return hooks.to_dict()

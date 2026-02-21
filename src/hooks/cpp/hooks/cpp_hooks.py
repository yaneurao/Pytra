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


def _lookup_module_attr_runtime_call(emitter: Any, module_name: str, attr: str) -> str:
    """`module.attr` から runtime_call 名を引く（pytra.* は短縮名フォールバックしない）。"""
    module_name_norm = emitter._normalize_runtime_module_name(module_name)
    keys: list[str] = [module_name_norm]
    short = emitter._last_dotted_name(module_name_norm)
    if short != module_name_norm and not module_name_norm.startswith("pytra."):
        keys.append(short)
    for key in keys:
        if key in emitter.module_attr_call_map:
            owner_map = emitter.module_attr_call_map[key]
            if attr in owner_map:
                mapped = owner_map[attr]
                if isinstance(mapped, str) and mapped != "":
                    return mapped
    return ""


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
            return _lookup_module_attr_runtime_call(emitter, owner_mod, attr)
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
        if owner_t.startswith("dict[") and owner_t.endswith("]"):
            owner_inner = emitter.split_generic(owner_t[5:-1])
            if len(owner_inner) == 2:
                owner_value_t = emitter.normalize_type_name(owner_inner[1])
        objectish_owner = emitter.is_any_like_type(owner_t) or emitter.is_any_like_type(owner_value_t)
        key_expr = rendered_args[0] if len(rendered_args) >= 1 else "/* missing */"
        arg_nodes = emitter.any_to_list(call_node.get("args"))
        key_node: Any = None
        if len(arg_nodes) >= 1:
            key_node = arg_nodes[0]
        if not objectish_owner:
            key_expr = emitter._coerce_dict_key_expr(owner_node, key_expr, key_node)
        if len(rendered_args) >= 2:
            out_t = emitter.any_to_str(call_node.get("resolved_type"))
            if objectish_owner and out_t == "bool":
                return "dict_get_bool(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t == "str":
                return "dict_get_str(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and out_t.startswith("list["):
                return "dict_get_list(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if objectish_owner and (emitter.is_any_like_type(out_t) or out_t == "object"):
                return "dict_get_node(" + owner + ", " + key_expr + ", " + rendered_args[1] + ")"
            if not objectish_owner:
                return owner + ".get(" + key_expr + ", " + rendered_args[1] + ")"
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
    if kind != "Attribute":
        return None
    owner_node = emitter.any_to_dict_or_empty(expr_node.get("value"))
    base_expr = emitter.render_expr(expr_node.get("value"))
    owner_kind = emitter.any_dict_get_str(owner_node, "kind", "")
    if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
        base_expr = "(" + base_expr + ")"
    owner_t = emitter.get_expr_type(expr_node.get("value"))
    base_mod = emitter._resolve_imported_module_name(base_expr)
    if base_mod == "":
        base_mod = emitter._cpp_expr_to_module_name(base_expr)
    base_mod = emitter._normalize_runtime_module_name(base_mod)
    attr = emitter.any_dict_get_str(expr_node, "attr", "")
    if owner_t == "Path":
        if attr == "name":
            return base_expr + ".name()"
        if attr == "stem":
            return base_expr + ".stem()"
        if attr == "parent":
            return base_expr + ".parent()"
    mapped = ""
    if owner_kind in {"Name", "Attribute"} and attr != "":
        mapped = _lookup_module_attr_runtime_call(emitter, base_mod, attr)
    if _looks_like_runtime_symbol(mapped):
        return mapped
    if base_mod != "" and attr != "":
        ns = emitter._module_name_to_cpp_namespace(base_mod)
        if isinstance(ns, str) and ns != "":
            return ns + "::" + attr
    return None


def build_cpp_hooks() -> dict[str, Any]:
    """C++ エミッタへ注入する hooks dict を構築する。"""
    hooks = EmitterHooks()
    hooks.add("on_render_call", on_render_call)
    hooks.add("on_render_binop", on_render_binop)
    hooks.add("on_render_expr_kind", on_render_expr_kind)
    return hooks.to_dict()

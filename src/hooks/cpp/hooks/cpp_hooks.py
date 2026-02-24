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


def on_render_call(
    emitter: Any,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
    rendered_kwargs: dict[str, str],
) -> str | None:
    """Call 式出力フック。

    runtime_call / built-in の意味論は `CppEmitter._render_builtin_call` 側へ統一したため、
    C++ hook はここでは介入しない（構文差分専任）。
    """
    _ = emitter
    _ = call_node
    _ = func_node
    _ = rendered_args
    _ = rendered_kwargs
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
    impl = getattr(emitter, "_can_omit_braces_for_single_stmt", None)
    if callable(impl):
        return bool(impl(stmts))
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
    default_impl = getattr(emitter, "_default_stmt_omit_braces", None)
    if callable(default_impl):
        return bool(default_impl(kind, stmt, default_value))
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
    default_impl = getattr(emitter, "_default_for_range_mode", None)
    if callable(default_impl):
        step_expr = emitter.render_expr(stmt.get("step"))
        resolved = default_impl(stmt, default_mode, step_expr)
        if isinstance(resolved, str) and resolved in {"ascending", "descending", "dynamic"}:
            return resolved
        return default_mode
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

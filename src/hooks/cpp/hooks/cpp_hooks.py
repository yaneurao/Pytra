"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.code_emitter import EmitterHooks


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


def on_stmt_omit_braces(
    emitter: Any,
    kind: str,
    stmt: dict[str, Any],
    default_value: bool,
) -> bool:
    """制御構文の brace 省略可否を core 既定方針へ委譲する。"""
    default_impl = getattr(emitter, "_default_stmt_omit_braces", None)
    if callable(default_impl):
        return bool(default_impl(kind, stmt, default_value))
    return bool(default_value)


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
    hooks.add("on_stmt_omit_braces", on_stmt_omit_braces)
    hooks.add("on_render_module_method", on_render_module_method)
    hooks.add("on_render_class_method", on_render_class_method)
    hooks.add("on_render_expr_leaf", on_render_expr_leaf)
    hooks.add("on_render_expr_complex", on_render_expr_complex)
    return hooks.to_dict()

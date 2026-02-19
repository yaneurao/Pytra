"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pytra.std.typing import Any


def _render_write_rgb_png(args: list[str]) -> str:
    """`write_rgb_png` 呼び出しを `pytra::png` 直呼びへ整形する。"""
    path = args[0] if len(args) >= 1 else '""'
    w = args[1] if len(args) >= 2 else "0"
    h = args[2] if len(args) >= 3 else "0"
    pixels = args[3] if len(args) >= 4 else "list<uint8>{}"
    return (
        f"pytra::png::write_rgb_png({path}, int({w}), int({h}), "
        f"std::vector<uint8>({pixels}.begin(), {pixels}.end()))"
    )


def _render_save_gif(args: list[str], kw: dict[str, str]) -> str:
    """`save_gif` 呼び出しを C++ ランタイムシグネチャへ整形する。"""
    path = args[0] if len(args) >= 1 else '""'
    w = args[1] if len(args) >= 2 else "0"
    h = args[2] if len(args) >= 3 else "0"
    frames = args[3] if len(args) >= 4 else "list<bytearray>{}"
    palette = args[4] if len(args) >= 5 else "py_gif_grayscale_palette_list()"
    if palette in {"nullptr", "std::nullopt"}:
        palette = "py_gif_grayscale_palette_list()"
    delay_cs = kw.get("delay_cs", args[5] if len(args) >= 6 else "4")
    loop = kw.get("loop", args[6] if len(args) >= 7 else "0")
    return (
        f"pytra::gif::save_gif({path}, int({w}), int({h}), "
        f"py_u8_matrix({frames}), py_u8_vector({palette}), int({delay_cs}), int({loop}))"
    )


def _render_owner_expr(emitter: Any, func_node: dict[str, Any]) -> str:
    """Attribute call の owner 式を C++ 向けに整形する。"""
    owner_node = emitter.any_to_dict_or_empty(func_node.get("value"))
    owner_expr = emitter.render_expr(func_node.get("value"))
    owner_kind = emitter.any_dict_get_str(owner_node, "kind", "")
    if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
        owner_expr = "(" + owner_expr + ")"
    return owner_expr


def on_render_call(
    emitter: Any,
    call_node: dict[str, Any],
    func_node: dict[str, Any],
    rendered_args: list[str],
    rendered_kwargs: dict[str, str],
) -> str | None:
    """Call 式出力フック。文字列を返すとその式を採用する。"""
    runtime_call = emitter.any_dict_get_str(call_node, "runtime_call", "")
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
    if runtime_call == "save_gif":
        return _render_save_gif(rendered_args, rendered_kwargs)
    if runtime_call == "write_rgb_png":
        return _render_write_rgb_png(rendered_args)
    fn_kind = emitter.any_dict_get_str(func_node, "kind", "")
    if fn_kind == "Name":
        fn_name = emitter.any_dict_get_str(func_node, "id", "")
        if fn_name == "write_rgb_png":
            return _render_write_rgb_png(rendered_args)
        if fn_name == "save_gif":
            return _render_save_gif(rendered_args, rendered_kwargs)
        sym = emitter._resolve_imported_symbol(fn_name)
        module_name = emitter.any_dict_get_str(sym, "module", "")
        module_name = emitter._normalize_runtime_module_name(module_name)
        symbol_name = emitter.any_dict_get_str(sym, "name", "")
        module_key = emitter._last_dotted_name(module_name)
        if module_name in {"pytra", "pytra.runtime"} and symbol_name == "png":
            return _render_write_rgb_png(rendered_args)
        if module_name in {"pytra", "pytra.runtime"} and symbol_name == "gif":
            return _render_save_gif(rendered_args, rendered_kwargs)
        if module_key in {"png", "png_helper"} and symbol_name == "write_rgb_png":
            return _render_write_rgb_png(rendered_args)
        if module_key in {"gif", "gif_helper"} and symbol_name == "save_gif":
            return _render_save_gif(rendered_args, rendered_kwargs)

    if fn_kind == "Attribute":
        owner_node = emitter.any_to_dict_or_empty(func_node.get("value"))
        owner_expr = emitter.render_expr(func_node.get("value"))
        owner_mod = emitter._resolve_imported_module_name(owner_expr)
        owner_mod = emitter._normalize_runtime_module_name(owner_mod)
        owner_key = emitter._last_dotted_name(owner_mod)
        attr = emitter.any_dict_get_str(func_node, "attr", "")
        if owner_node.get("kind") in {"Name", "Attribute"}:
            if owner_key in {"png", "png_helper"} and attr == "write_rgb_png":
                return _render_write_rgb_png(rendered_args)
            if owner_key in {"gif", "gif_helper"} and attr == "save_gif":
                return _render_save_gif(rendered_args, rendered_kwargs)
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
    base_mod = emitter._normalize_runtime_module_name(base_mod)
    base_key = emitter._last_dotted_name(base_mod)
    attr = emitter.any_dict_get_str(expr_node, "attr", "")
    if owner_t == "Path":
        if attr == "name":
            return base_expr + ".name()"
        if attr == "stem":
            return base_expr + ".stem()"
        if attr == "parent":
            return base_expr + ".parent()"
    if base_key in {"png", "png_helper"} and attr == "write_rgb_png":
        return "pytra::png::write_rgb_png"
    if base_key in {"gif", "gif_helper"} and attr == "save_gif":
        return "pytra::gif::save_gif"
    return None


def build_cpp_hooks() -> dict[str, Any]:
    """C++ エミッタへ注入する hooks dict を構築する。"""
    hooks: dict[str, Any] = {}
    hooks["on_render_call"] = on_render_call
    hooks["on_render_expr_kind"] = on_render_expr_kind
    return hooks

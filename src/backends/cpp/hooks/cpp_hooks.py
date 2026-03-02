"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.east_parts.code_emitter import EmitterHooks


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
    hooks.add("on_render_expr_complex", on_render_expr_complex)
    return hooks.to_dict()

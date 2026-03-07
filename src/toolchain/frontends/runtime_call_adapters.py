from __future__ import annotations


def normalize_rendered_runtime_args(
    adapter_kind: str,
    rendered_args: list[str],
    rendered_keywords: list[tuple[str, str]],
    *,
    default_values: dict[str, str] | None = None,
    error_prefix: str,
) -> list[str]:
    defaults = default_values if isinstance(default_values, dict) else {}
    if adapter_kind == "":
        return list(rendered_args)
    if adapter_kind != "image.save_gif.keyword_defaults":
        raise RuntimeError(error_prefix + ": unsupported runtime adapter kind: " + adapter_kind)
    if len(rendered_args) < 5 or len(rendered_args) > 7:
        raise RuntimeError(error_prefix + ": save_gif expects 5-7 positional args")
    delay_expr = rendered_args[5] if len(rendered_args) >= 6 else defaults.get("delay_cs", "4")
    loop_expr = rendered_args[6] if len(rendered_args) >= 7 else defaults.get("loop", "0")
    for kw_name, kw_val in rendered_keywords:
        if kw_name == "delay_cs":
            if len(rendered_args) >= 6:
                raise RuntimeError(error_prefix + ": save_gif duplicate delay_cs argument")
            delay_expr = kw_val
            continue
        if kw_name == "loop":
            if len(rendered_args) >= 7:
                raise RuntimeError(error_prefix + ": save_gif duplicate loop argument")
            loop_expr = kw_val
            continue
        raise RuntimeError(error_prefix + ": unsupported save_gif keyword: " + kw_name)
    return rendered_args[:5] + [delay_expr, loop_expr]


#!/usr/bin/env python3
"""Self-hosted EAST runtime declaration helper semantics."""

from __future__ import annotations

from typing import Any


def _sh_parse_runtime_abi_string_literal(
    text: str,
    *,
    line_no: int,
    line_text: str,
    field_name: str,
    make_east_build_error: Any,
    make_span: Any,
) -> str:
    raw = text.strip()
    if len(raw) >= 2 and raw[0] in {"'", '"'} and raw[-1] == raw[0]:
        return raw[1:-1]
    raise make_east_build_error(
        kind="unsupported_syntax",
        message=f"{field_name} must be a string literal: {raw}",
        source_span=make_span(line_no, 0, len(line_text)),
        hint='Use quoted string literals such as "value" or "parts".',
    )


def _sh_parse_runtime_abi_mode(
    text: str,
    *,
    line_no: int,
    line_text: str,
    field_name: str,
    allowed_modes: set[str],
    hint_text: str,
    runtime_abi_mode_aliases: dict[str, str],
    make_east_build_error: Any,
    make_span: Any,
) -> str:
    mode = _sh_parse_runtime_abi_string_literal(
        text,
        line_no=line_no,
        line_text=line_text,
        field_name=field_name,
        make_east_build_error=make_east_build_error,
        make_span=make_span,
    )
    normalized = runtime_abi_mode_aliases.get(mode, mode)
    if normalized in allowed_modes:
        return normalized
    raise make_east_build_error(
        kind="unsupported_syntax",
        message=f"unsupported abi mode for {field_name}: {mode}",
        source_span=make_span(line_no, 0, len(line_text)),
        hint=hint_text,
    )


def _sh_parse_runtime_abi_args_map(
    text: str,
    *,
    line_no: int,
    line_text: str,
    split_top_commas: Any,
    split_top_level_colon: Any,
    is_identifier: Any,
    runtime_abi_arg_modes: set[str],
    runtime_abi_mode_aliases: dict[str, str],
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, str]:
    raw = text.strip()
    if raw in {"", "None"}:
        return {}
    if not (raw.startswith("{") and raw.endswith("}")):
        raise make_east_build_error(
            kind="unsupported_syntax",
            message=f"abi args must be a dict literal: {raw}",
            source_span=make_span(line_no, 0, len(line_text)),
            hint='Use args={"param": "value"} form.',
        )
    inner = raw[1:-1].strip()
    if inner == "":
        return {}
    out: dict[str, str] = {}
    for part_raw in split_top_commas(inner):
        part = part_raw.strip()
        if part == "":
            continue
        split = split_top_level_colon(part)
        if split is None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported abi args entry: {part}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use args={"param": "value"} entries only.',
            )
        key_txt, value_txt = split
        key = _sh_parse_runtime_abi_string_literal(
            key_txt,
            line_no=line_no,
            line_text=line_text,
            field_name="abi args key",
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
        if not is_identifier(key):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi args key must be an identifier name: {key}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use quoted parameter names such as "parts".',
            )
        if key in out:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate abi args entry: {key}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Specify each parameter at most once.",
            )
        out[key] = _sh_parse_runtime_abi_mode(
            value_txt,
            line_no=line_no,
            line_text=line_text,
            field_name=f"abi args[{key}]",
            allowed_modes=runtime_abi_arg_modes,
            hint_text='Use one of "default", "value", or "value_mut".',
            runtime_abi_mode_aliases=runtime_abi_mode_aliases,
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
    return out


def _sh_parse_runtime_abi_decorator(
    decorator_text: str,
    *,
    arg_order: list[str],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    parse_decorator_head_and_args: Any,
    split_top_commas: Any,
    split_top_level_assign: Any,
    split_top_level_colon: Any,
    is_identifier: Any,
    runtime_abi_arg_modes: set[str],
    runtime_abi_ret_modes: set[str],
    runtime_abi_mode_aliases: dict[str, str],
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, Any] | None:
    if not is_abi_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    _head, args_txt = parse_decorator_head_and_args(decorator_text)
    if args_txt == "":
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="abi decorator requires keyword-only call form",
            source_span=make_span(line_no, 0, len(line_text)),
            hint='Use `@abi(args={"name": "value"}, ret="value")`.',
        )
    out_args: dict[str, str] = {}
    out_ret = "default"
    seen_keys: set[str] = set()
    for part_raw in split_top_commas(args_txt):
        part = part_raw.strip()
        if part == "":
            continue
        split = split_top_level_assign(part)
        if split is None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi decorator accepts keyword arguments only: {part}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use `args=...` and `ret=...` keyword arguments only.',
            )
        key_txt, value_txt = split
        key = key_txt.strip()
        if key in seen_keys:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate abi decorator option: {key}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Specify each abi decorator option at most once.",
            )
        seen_keys.add(key)
        if key == "args":
            out_args = _sh_parse_runtime_abi_args_map(
                value_txt,
                line_no=line_no,
                line_text=line_text,
                split_top_commas=split_top_commas,
                split_top_level_colon=split_top_level_colon,
                is_identifier=is_identifier,
                runtime_abi_arg_modes=runtime_abi_arg_modes,
                runtime_abi_mode_aliases=runtime_abi_mode_aliases,
                make_east_build_error=make_east_build_error,
                make_span=make_span,
            )
            continue
        if key == "ret":
            out_ret = _sh_parse_runtime_abi_mode(
                value_txt,
                line_no=line_no,
                line_text=line_text,
                field_name="abi ret",
                allowed_modes=runtime_abi_ret_modes,
                hint_text='Use one of "default" or "value".',
                runtime_abi_mode_aliases=runtime_abi_mode_aliases,
                make_east_build_error=make_east_build_error,
                make_span=make_span,
            )
            continue
        raise make_east_build_error(
            kind="unsupported_syntax",
            message=f"unsupported abi decorator option: {key}",
            source_span=make_span(line_no, 0, len(line_text)),
            hint='Supported keys are `args` and `ret` only.',
        )
    valid_args = set(arg_order)
    for param_name in out_args.keys():
        if param_name not in valid_args:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"abi decorator references unknown parameter: {param_name}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use only declared function parameter names in abi args.",
            )
    return {
        "schema_version": 1,
        "args": out_args,
        "ret": out_ret,
    }


def _sh_collect_runtime_abi_metadata(
    decorators: list[str],
    *,
    arg_order: list[str],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    parse_decorator_head_and_args: Any,
    split_top_commas: Any,
    split_top_level_assign: Any,
    split_top_level_colon: Any,
    is_identifier: Any,
    runtime_abi_arg_modes: set[str],
    runtime_abi_ret_modes: set[str],
    runtime_abi_mode_aliases: dict[str, str],
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, Any] | None:
    runtime_abi_meta: dict[str, Any] | None = None
    for decorator_text in decorators:
        parsed = _sh_parse_runtime_abi_decorator(
            decorator_text,
            arg_order=arg_order,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
            line_no=line_no,
            line_text=line_text,
            is_abi_decorator=is_abi_decorator,
            parse_decorator_head_and_args=parse_decorator_head_and_args,
            split_top_commas=split_top_commas,
            split_top_level_assign=split_top_level_assign,
            split_top_level_colon=split_top_level_colon,
            is_identifier=is_identifier,
            runtime_abi_arg_modes=runtime_abi_arg_modes,
            runtime_abi_ret_modes=runtime_abi_ret_modes,
            runtime_abi_mode_aliases=runtime_abi_mode_aliases,
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
        if parsed is None:
            continue
        if runtime_abi_meta is not None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="multiple abi decorators on one function are not supported",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use a single @abi(args=..., ret=...) decorator.",
            )
        runtime_abi_meta = parsed
    return runtime_abi_meta


def _sh_parse_template_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_template_decorator: Any,
    parse_decorator_head_and_args: Any,
    split_top_commas: Any,
    split_top_level_assign: Any,
    is_identifier: Any,
    template_scope: str,
    template_instantiation_mode: str,
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, Any] | None:
    if not is_template_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    _head, args_txt = parse_decorator_head_and_args(decorator_text)
    if args_txt == "":
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="template decorator requires one or more string literal parameters",
            source_span=make_span(line_no, 0, len(line_text)),
            hint='Use `@template("T")` or `@template("K", "V")`.',
        )
    params: list[str] = []
    seen: set[str] = set()
    for part_raw in split_top_commas(args_txt):
        part = part_raw.strip()
        if part == "":
            continue
        if split_top_level_assign(part) is not None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"template decorator accepts positional string literal parameters only: {part}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use `@template("T", "U")` form.',
            )
        param = _sh_parse_runtime_abi_string_literal(
            part,
            line_no=line_no,
            line_text=line_text,
            field_name="template parameter",
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
        if not is_identifier(param):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"template parameter must be an identifier name: {param}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use identifier-like strings such as "T" or "Value".',
            )
        if param in seen:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate template parameter: {param}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Specify each template parameter at most once.",
            )
        seen.add(param)
        params.append(param)
    if len(params) == 0:
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="template decorator requires one or more string literal parameters",
            source_span=make_span(line_no, 0, len(line_text)),
            hint='Use `@template("T")` or `@template("K", "V")`.',
        )
    return {
        "schema_version": 1,
        "params": params,
        "scope": template_scope,
        "instantiation_mode": template_instantiation_mode,
    }


def _sh_collect_template_metadata(
    decorators: list[str],
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_template_decorator: Any,
    parse_decorator_head_and_args: Any,
    split_top_commas: Any,
    split_top_level_assign: Any,
    is_identifier: Any,
    template_scope: str,
    template_instantiation_mode: str,
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, Any] | None:
    template_meta: dict[str, Any] | None = None
    for decorator_text in decorators:
        parsed = _sh_parse_template_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
            line_no=line_no,
            line_text=line_text,
            is_template_decorator=is_template_decorator,
            parse_decorator_head_and_args=parse_decorator_head_and_args,
            split_top_commas=split_top_commas,
            split_top_level_assign=split_top_level_assign,
            is_identifier=is_identifier,
            template_scope=template_scope,
            template_instantiation_mode=template_instantiation_mode,
            make_east_build_error=make_east_build_error,
            make_span=make_span,
        )
        if parsed is None:
            continue
        if template_meta is not None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="multiple template decorators on one function are not supported",
                source_span=make_span(line_no, 0, len(line_text)),
                hint='Use a single `@template("T", ...)` decorator.',
            )
        template_meta = parsed
    return template_meta


def _sh_collect_function_runtime_decl_metadata(
    decorators: list[str],
    *,
    arg_order: list[str],
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    is_template_decorator: Any,
    parse_decorator_head_and_args: Any,
    split_top_commas: Any,
    split_top_level_assign: Any,
    split_top_level_colon: Any,
    is_identifier: Any,
    runtime_abi_arg_modes: set[str],
    runtime_abi_ret_modes: set[str],
    runtime_abi_mode_aliases: dict[str, str],
    template_scope: str,
    template_instantiation_mode: str,
    make_east_build_error: Any,
    make_span: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    runtime_abi_meta = _sh_collect_runtime_abi_metadata(
        decorators,
        arg_order=arg_order,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
        line_no=line_no,
        line_text=line_text,
        is_abi_decorator=is_abi_decorator,
        parse_decorator_head_and_args=parse_decorator_head_and_args,
        split_top_commas=split_top_commas,
        split_top_level_assign=split_top_level_assign,
        split_top_level_colon=split_top_level_colon,
        is_identifier=is_identifier,
        runtime_abi_arg_modes=runtime_abi_arg_modes,
        runtime_abi_ret_modes=runtime_abi_ret_modes,
        runtime_abi_mode_aliases=runtime_abi_mode_aliases,
        make_east_build_error=make_east_build_error,
        make_span=make_span,
    )
    template_meta = _sh_collect_template_metadata(
        decorators,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
        line_no=line_no,
        line_text=line_text,
        is_template_decorator=is_template_decorator,
        parse_decorator_head_and_args=parse_decorator_head_and_args,
        split_top_commas=split_top_commas,
        split_top_level_assign=split_top_level_assign,
        is_identifier=is_identifier,
        template_scope=template_scope,
        template_instantiation_mode=template_instantiation_mode,
        make_east_build_error=make_east_build_error,
        make_span=make_span,
    )
    return runtime_abi_meta, template_meta


def _sh_reject_runtime_decl_class_decorators(
    decorators: list[str],
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    is_template_decorator: Any,
    make_east_build_error: Any,
    make_span: Any,
) -> None:
    for decorator_text in decorators:
        if is_abi_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
        ):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="@abi is not supported on class definitions",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use @abi on top-level runtime helper functions only.",
            )
        if is_template_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
        ):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="@template is not supported on class definitions",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use @template on top-level runtime helper functions only.",
            )


def _sh_reject_runtime_decl_method_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    is_template_decorator: Any,
    make_east_build_error: Any,
    make_span: Any,
) -> None:
    if is_abi_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="@abi is not supported on methods",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Use @abi on top-level runtime helper functions only.",
        )
    if is_template_decorator(
        decorator_text,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="@template is not supported on methods",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Use @template on top-level runtime helper functions only.",
        )


def _sh_reject_runtime_decl_nonfunction_decorators(
    decorators: list[str],
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    is_abi_decorator: Any,
    is_template_decorator: Any,
    make_east_build_error: Any,
    make_span: Any,
) -> None:
    for decorator_text in decorators:
        if is_abi_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
        ):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="@abi is supported on top-level functions only",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Move @abi to a top-level runtime helper function definition.",
            )
        if is_template_decorator(
            decorator_text,
            import_module_bindings=import_module_bindings,
            import_symbol_bindings=import_symbol_bindings,
        ):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="@template is supported on top-level functions only",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Move @template to a top-level runtime helper function definition.",
            )

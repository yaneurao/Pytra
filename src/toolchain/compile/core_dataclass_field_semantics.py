#!/usr/bin/env python3
"""Static metadata helpers for dataclass field(...) declarations."""

from __future__ import annotations

from typing import Any
from typing import Callable


_SH_DATACLASS_FIELD_BOOL_OPTIONS = {"init", "repr", "compare"}
_SH_DATACLASS_FIELD_EXPR_OPTIONS = {"default", "default_factory"}
_SH_DATACLASS_FIELD_SUPPORTED_OPTIONS = _SH_DATACLASS_FIELD_BOOL_OPTIONS | _SH_DATACLASS_FIELD_EXPR_OPTIONS


def _sh_make_dataclass_field_v1_meta(
    *,
    default_expr: dict[str, Any] | None = None,
    default_factory_expr: dict[str, Any] | None = None,
    init: bool | None = None,
    repr_enabled: bool | None = None,
    compare: bool | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {"schema_version": 1}
    if default_expr is not None:
        meta["default_expr"] = default_expr
    if default_factory_expr is not None:
        meta["default_factory_expr"] = default_factory_expr
    if init is not None:
        meta["init"] = bool(init)
    if repr_enabled is not None:
        meta["repr_enabled"] = bool(repr_enabled)
    if compare is not None:
        meta["compare"] = bool(compare)
    return meta


def _sh_is_dataclass_field_call(
    value_expr: Any,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    if not isinstance(value_expr, dict) or value_expr.get("kind") != "Call":
        return False
    func_obj = value_expr.get("func")
    if not isinstance(func_obj, dict):
        return False
    if func_obj.get("kind") == "Name":
        func_name = str(func_obj.get("id", ""))
        if func_name == "field":
            return True
        ent = import_symbol_bindings.get(func_name)
        if not isinstance(ent, dict):
            return False
        return str(ent.get("module", "")) == "dataclasses" and str(ent.get("name", "")) == "field"
    if func_obj.get("kind") == "Attribute":
        owner = func_obj.get("value")
        if not isinstance(owner, dict) or owner.get("kind") != "Name":
            return False
        if str(func_obj.get("attr", "")) != "field":
            return False
        owner_name = str(owner.get("id", ""))
        if owner_name == "dataclasses":
            return True
        return import_module_bindings.get(owner_name, "") == "dataclasses"
    return False


def _sh_collect_dataclass_field_metadata(
    value_expr: Any,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
    line_no: int,
    line_text: str,
    make_east_build_error: Callable[..., Exception],
    make_span: Callable[..., dict[str, int]],
) -> dict[str, Any] | None:
    if not _sh_is_dataclass_field_call(
        value_expr,
        import_module_bindings=import_module_bindings,
        import_symbol_bindings=import_symbol_bindings,
    ):
        return None
    if not isinstance(value_expr, dict):
        return None
    args_obj = value_expr.get("args")
    args = args_obj if isinstance(args_obj, list) else []
    if len(args) > 0:
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="dataclass field(...) requires keyword-only arguments",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Use field(default=..., default_factory=..., init=..., repr=..., compare=...).",
        )
    keywords_obj = value_expr.get("keywords")
    keywords = keywords_obj if isinstance(keywords_obj, list) else []
    default_expr: dict[str, Any] | None = None
    default_factory_expr: dict[str, Any] | None = None
    init_value: bool | None = None
    repr_value: bool | None = None
    compare_value: bool | None = None
    seen: set[str] = set()
    for kw in keywords:
        if not isinstance(kw, dict):
            continue
        arg = str(kw.get("arg", ""))
        if arg == "":
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="dataclass field(...) does not support bare **kwargs",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use explicit keyword arguments only.",
            )
        if arg not in _SH_DATACLASS_FIELD_SUPPORTED_OPTIONS:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported dataclass field option: {arg}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use only default/default_factory/init/repr/compare in Pytra v1.",
            )
        if arg in seen:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"duplicate dataclass field option: {arg}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Specify each dataclass field option at most once.",
            )
        seen.add(arg)
        val = kw.get("value")
        if arg in _SH_DATACLASS_FIELD_BOOL_OPTIONS:
            if not isinstance(val, dict) or val.get("kind") != "Constant" or not isinstance(val.get("value"), bool):
                raise make_east_build_error(
                    kind="unsupported_syntax",
                    message=f"dataclass field option {arg} must be True/False",
                    source_span=make_span(line_no, 0, len(line_text)),
                    hint="Use literal bool values for init/repr/compare.",
                )
            bool_value = bool(val.get("value"))
            if arg == "init":
                init_value = bool_value
            elif arg == "repr":
                repr_value = bool_value
            else:
                compare_value = bool_value
            continue
        if not isinstance(val, dict):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"dataclass field option {arg} requires an expression value",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use an explicit expression for default/default_factory.",
            )
        if arg == "default":
            default_expr = val
        else:
            default_factory_expr = val
    if default_expr is not None and default_factory_expr is not None:
        raise make_east_build_error(
            kind="unsupported_syntax",
            message="dataclass field(...) cannot use both default and default_factory",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Choose either default or default_factory.",
        )
    return _sh_make_dataclass_field_v1_meta(
        default_expr=default_expr,
        default_factory_expr=default_factory_expr,
        init=init_value,
        repr_enabled=repr_value,
        compare=compare_value,
    )

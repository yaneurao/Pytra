#!/usr/bin/env python3
"""Self-hosted EAST class/declaration semantics helpers."""

from __future__ import annotations

from typing import Any
from typing import Callable

_SH_VALUE_SAFE_CLASS_FIELD_TYPES: set[str] = {
    "bool",
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
    "str",
    "bytes",
    "bytearray",
}


def _split_top_commas(txt: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current = ""
    in_str: str | None = None
    esc = False
    for ch in txt:
        if in_str is not None:
            current += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            current += ch
            continue
        if ch in {"(", "[", "{"}:
            depth += 1
            current += ch
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            current += ch
            continue
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += ch
    if current.strip() != "":
        parts.append(current.strip())
    return parts


def _sh_make_decl_meta(
    *,
    runtime_abi_v1: dict[str, Any] | None = None,
    template_v1: dict[str, Any] | None = None,
    extern_var_v1: dict[str, Any] | None = None,
    dataclass_field_v1: dict[str, Any] | None = None,
    nominal_adt_v1: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """宣言 node の metadata carrier を構築する。"""
    meta: dict[str, Any] = {}
    if runtime_abi_v1 is not None:
        meta["runtime_abi_v1"] = runtime_abi_v1
    if template_v1 is not None:
        meta["template_v1"] = template_v1
    if extern_var_v1 is not None:
        meta["extern_var_v1"] = extern_var_v1
    if dataclass_field_v1 is not None:
        meta["dataclass_field_v1"] = dataclass_field_v1
    if nominal_adt_v1 is not None:
        meta["nominal_adt_v1"] = nominal_adt_v1
    return meta


def _sh_make_nominal_adt_v1_meta(
    *,
    role: str,
    family_name: str,
    variant_name: str | None = None,
    payload_style: str | None = None,
) -> dict[str, Any]:
    """`meta.nominal_adt_v1` carrier を構築する。"""
    meta: dict[str, Any] = {
        "schema_version": 1,
        "role": role,
        "family_name": family_name,
        "surface_phase": "declaration_v1",
    }
    if role == "family":
        meta["closed"] = 1
    if variant_name is not None:
        meta["variant_name"] = variant_name
    if payload_style is not None:
        meta["payload_style"] = payload_style
    return meta


def _sh_is_value_safe_dataclass_field_type(type_name: str) -> bool:
    """dataclass 自動 value 判定用の保守的な型チェック。"""
    t = type_name.strip()
    if t in _SH_VALUE_SAFE_CLASS_FIELD_TYPES:
        return True
    if t.startswith("tuple[") and t.endswith("]"):
        inner = t[6:-1].strip()
        if inner == "":
            return True
        parts = _split_top_commas(inner)
        if len(parts) == 0:
            return False
        for part in parts:
            if not _sh_is_value_safe_dataclass_field_type(part):
                return False
        return True
    return False


def _sh_is_value_safe_dataclass_candidate(
    *,
    is_dataclass: bool,
    base: str,
    has_del: bool,
    class_body: list[dict[str, Any]],
    field_types: dict[str, str],
) -> bool:
    """参照共有が不要な dataclass を value 候補として判定する。"""
    if not is_dataclass or base != "" or has_del:
        return False
    for st in class_body:
        if isinstance(st, dict) and st.get("kind") == "FunctionDef":
            return False
    if len(field_types) == 0:
        return True
    for field_t in field_types.values():
        if not isinstance(field_t, str):
            return False
        if not _sh_is_value_safe_dataclass_field_type(field_t):
            return False
    return True


def _sh_collect_nominal_adt_class_metadata(
    class_name: str,
    *,
    base: str | None,
    decorators: list[str],
    is_dataclass: bool,
    field_types: dict[str, str],
    line_no: int,
    line_text: str,
    sealed_families: set[str],
    is_sealed_decorator: Callable[[str], bool],
    parse_decorator_head_and_args: Callable[[str], tuple[str, str]],
    make_east_build_error: Callable[..., Exception],
    make_span: Callable[[int, int, int], dict[str, Any]],
) -> dict[str, Any] | None:
    """Stage A nominal ADT class metadata を収集する。"""
    sealed_count = 0
    for decorator_text in decorators:
        if not is_sealed_decorator(decorator_text):
            continue
        head, args_txt = parse_decorator_head_and_args(decorator_text)
        if head == "sealed" and args_txt != "":
            raise make_east_build_error(
                kind="unsupported_syntax",
                message="@sealed does not accept arguments",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use bare `@sealed` on the family class.",
            )
        sealed_count += 1
    if sealed_count > 1:
        raise make_east_build_error(
            kind="unsupported_syntax",
            message=f"multiple @sealed decorators are not supported on class '{class_name}'",
            source_span=make_span(line_no, 0, len(line_text)),
            hint="Use a single `@sealed` decorator on the family class.",
        )
    has_sealed = sealed_count == 1
    base_name = base if isinstance(base, str) and base != "" else None
    if has_sealed:
        if base_name is not None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"sealed family '{class_name}' cannot inherit from '{base_name}'",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use `@sealed class Family:` with no base; declare variants as subclasses.",
            )
        if is_dataclass:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"sealed family '{class_name}' cannot be a dataclass",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use `@sealed` on the family and `@dataclass` only on payload variants.",
            )
        if len(field_types) > 0:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"sealed family '{class_name}' cannot declare payload fields",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Keep payload fields on variant classes only.",
            )
        return _sh_make_decl_meta(
            nominal_adt_v1=_sh_make_nominal_adt_v1_meta(
                role="family",
                family_name=class_name,
            )
        )
    if base_name is not None and base_name in sealed_families:
        if len(field_types) > 0 and not is_dataclass:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"payload variant '{class_name}' must use @dataclass",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Add `@dataclass` to variants that declare payload fields.",
            )
        return _sh_make_decl_meta(
            nominal_adt_v1=_sh_make_nominal_adt_v1_meta(
                role="variant",
                family_name=base_name,
                variant_name=class_name,
                payload_style="dataclass" if is_dataclass else "unit",
            )
        )
    return None

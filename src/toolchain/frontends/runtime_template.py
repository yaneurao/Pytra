"""Shared validation helpers for `FunctionDef.meta.template_v1`."""

from __future__ import annotations

from typing import Any


_TEMPLATE_SCOPE = "runtime_helper"
_TEMPLATE_INSTANTIATION_MODE = "linked_implicit"
_RUNTIME_TEMPLATE_MODULE_PREFIXES = ("pytra.built_in",)
_RUNTIME_TEMPLATE_SOURCE_SEGMENTS = ("/src/pytra/built_in/", "src/pytra/built_in/")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _kind(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    d: dict[str, Any] = node
    return str(d.get("kind", ""))


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        text = s.strip()
        if text != "":
            return text
    return ""


def _function_symbol(module_id: str, scope: tuple[str, ...], fn_node: dict[str, Any]) -> str:
    fn_name = _safe_name(fn_node.get("name"))
    parts = [module_id]
    if len(scope) > 0:
        parts.append(".".join(scope))
    if fn_name != "":
        parts.append(fn_name)
    if len(parts) > 1:
        joined_parts: list[str] = [parts[0], ".".join(parts[1:])]
        return "::".join(joined_parts)
    return "::".join(parts)


def _is_runtime_helper_module(module_doc: dict[str, Any]) -> bool:
    module_meta = _as_dict(module_doc.get("meta"))
    module_id = _safe_name(module_meta.get("module_id"))
    found_prefix = False
    for prefix in _RUNTIME_TEMPLATE_MODULE_PREFIXES:
        if module_id == prefix or module_id.startswith(prefix + "."):
            found_prefix = True
            break
    if found_prefix:
        return True
    source_path = _safe_name(module_doc.get("source_path"))
    normalized_source = source_path.replace("\\", "/")
    for segment in _RUNTIME_TEMPLATE_SOURCE_SEGMENTS:
        if segment in normalized_source:
            return True
    return False


def _validate_template_shape(fn_node: dict[str, Any], *, symbol: str, top_level: bool) -> dict[str, Any] | None:
    meta = _as_dict(fn_node.get("meta"))
    template_any = meta.get("template_v1")
    if template_any is None:
        return None
    if top_level is False:
        raise RuntimeError("template_violation: @template is supported on top-level functions only: " + symbol)
    template_meta = _as_dict(template_any)
    schema_version = template_meta.get("schema_version", 0)
    if not isinstance(schema_version, int) or int(schema_version) != 1:
        raise RuntimeError("template_violation: template_v1.schema_version must be 1: " + symbol)
    params_any = template_meta.get("params", [])
    if not isinstance(params_any, list):
        raise RuntimeError("template_violation: template_v1.params must be an array: " + symbol)
    params: list[str] = []
    seen: set[str] = set()
    for raw in params_any:
        name = _safe_name(raw)
        if name == "":
            raise RuntimeError("template_violation: template_v1.params entries must be non-empty strings: " + symbol)
        if name in seen:
            raise RuntimeError("template_violation: duplicate template_v1 param: " + symbol + ": " + name)
        seen.add(name)
        params.append(name)
    if len(params) == 0:
        raise RuntimeError("template_violation: template_v1.params must not be empty: " + symbol)
    scope_name = _safe_name(template_meta.get("scope"))
    if scope_name != _TEMPLATE_SCOPE:
        raise RuntimeError("template_violation: template_v1.scope must be runtime_helper: " + symbol)
    instantiation_mode = _safe_name(template_meta.get("instantiation_mode"))
    if instantiation_mode != _TEMPLATE_INSTANTIATION_MODE:
        raise RuntimeError("template_violation: template_v1.instantiation_mode must be linked_implicit: " + symbol)
    canonical = {
        "schema_version": 1,
        "params": params,
        "scope": _TEMPLATE_SCOPE,
        "instantiation_mode": _TEMPLATE_INSTANTIATION_MODE,
    }
    meta_obj = fn_node.get("meta")
    if isinstance(meta_obj, dict):
        meta_obj["template_v1"] = canonical
    return canonical


def _walk_function_nodes(
    items: list[Any],
    *,
    module_id: str,
    scope: tuple[str, ...],
    top_level: bool,
) -> None:
    for raw_item in items:
        item = _as_dict(raw_item)
        kind = _kind(item)
        if kind == "FunctionDef":
            _ = _validate_template_shape(item, symbol=_function_symbol(module_id, scope, item), top_level=top_level)
            next_scope = scope + (_safe_name(item.get("name")),)
            _walk_function_nodes(_as_list(item.get("body")), module_id=module_id, scope=next_scope, top_level=False)
            continue
        if kind == "ClassDef":
            class_name = _safe_name(item.get("name"))
            next_scope = scope + ((class_name,) if class_name != "" else ())
            _walk_function_nodes(_as_list(item.get("body")), module_id=module_id, scope=next_scope, top_level=False)
            continue
        for key in ("body", "orelse", "finalbody"):
            child_list = _as_list(item.get(key))
            if len(child_list) > 0:
                _walk_function_nodes(child_list, module_id=module_id, scope=scope, top_level=False)
        if kind == "Try":
            for handler in _as_list(item.get("handlers")):
                handler_body = _as_list(_as_dict(handler).get("body"))
                if len(handler_body) > 0:
                    _walk_function_nodes(handler_body, module_id=module_id, scope=scope, top_level=False)


def validate_template_module(module_doc: dict[str, Any]) -> dict[str, Any]:
    module_meta = _as_dict(module_doc.get("meta"))
    module_id = _safe_name(module_meta.get("module_id"))
    if module_id == "":
        module_id = _safe_name(module_doc.get("source_path"))
    if module_id == "":
        module_id = "<module>"
    if not _is_runtime_helper_module(module_doc):
        for raw_item in _as_list(module_doc.get("body")):
            item = _as_dict(raw_item)
            if _kind(item) != "FunctionDef":
                continue
            meta = _as_dict(item.get("meta"))
            if isinstance(meta.get("template_v1"), dict):
                symbol = _function_symbol(module_id, (), item)
                raise RuntimeError(
                    "template_violation: @template is supported on runtime helper modules only: " + symbol
                )
    _walk_function_nodes(_as_list(module_doc.get("body")), module_id=module_id, scope=(), top_level=True)
    return module_doc


__all__ = [
    "validate_template_module",
]

"""Shared validation helpers for ambient global extern variables."""

from __future__ import annotations

from typing import Any


_AMBIENT_EXTERN_SUPPORTED_TARGETS = {"js", "ts"}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _module_id(east_doc: dict[str, Any]) -> str:
    meta = _as_dict(east_doc.get("meta"))
    module_id = _safe_name(meta.get("module_id"))
    if module_id != "":
        return module_id
    return "<module>"


def collect_ambient_global_extern_bindings(east_doc: dict[str, Any]) -> list[dict[str, str]]:
    """Collect top-level `name: Any = extern(...)` bindings from an EAST module."""
    out: list[dict[str, str]] = []
    for raw_stmt in _as_list(east_doc.get("body")):
        stmt = _as_dict(raw_stmt)
        kind = _safe_name(stmt.get("kind"))
        if kind not in {"Assign", "AnnAssign"}:
            continue
        meta = _as_dict(stmt.get("meta"))
        extern_meta = _as_dict(meta.get("extern_var_v1"))
        if extern_meta.get("schema_version") != 1:
            continue
        symbol = _safe_name(extern_meta.get("symbol"))
        target = _as_dict(stmt.get("target"))
        if _safe_name(target.get("kind")) != "Name":
            continue
        local_name = _safe_name(target.get("id"))
        if local_name == "" or symbol == "":
            continue
        out.append({"local_name": local_name, "symbol": symbol})
    return out


def validate_ambient_global_target_support(east_doc: dict[str, Any], *, target: str) -> dict[str, Any]:
    """Reject ambient extern variables on unsupported targets."""
    if target in _AMBIENT_EXTERN_SUPPORTED_TARGETS:
        return east_doc
    bindings = collect_ambient_global_extern_bindings(east_doc)
    if len(bindings) == 0:
        return east_doc
    module_id = _module_id(east_doc)
    formatted = ", ".join(
        module_id + "::" + item["local_name"] + " -> " + item["symbol"]
        for item in bindings
    )
    raise RuntimeError(
        "ambient extern variables are not supported for target "
        + target
        + ": "
        + formatted
    )

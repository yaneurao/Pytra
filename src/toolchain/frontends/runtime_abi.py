"""Shared validation helpers for `FunctionDef.meta.runtime_abi_v1`."""

from __future__ import annotations

from typing import Any


_RUNTIME_ABI_MODES = {"default", "value", "value_readonly"}
_MUTATING_ATTRS = {
    "append",
    "extend",
    "insert",
    "pop",
    "clear",
    "remove",
    "discard",
    "add",
    "update",
    "setdefault",
    "sort",
    "reverse",
    "mkdir",
    "write",
    "write_text",
    "close",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _kind(node: Any) -> str:
    return str(node.get("kind", "")) if isinstance(node, dict) else ""


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _mark_mutated_param_from_target(target_obj: Any, params: set[str], out: set[str]) -> None:
    tgt = _as_dict(target_obj)
    tkind = _kind(tgt)
    if tkind == "Name":
        name = _safe_name(tgt.get("id"))
        if name in params:
            out.add(name)
        return
    if tkind == "Subscript":
        base = _as_dict(tgt.get("value"))
        if _kind(base) == "Name":
            name = _safe_name(base.get("id"))
            if name in params:
                out.add(name)
        else:
            _mark_mutated_param_from_target(base, params, out)
        return
    if tkind == "Attribute":
        owner = _as_dict(tgt.get("value"))
        if _kind(owner) == "Name":
            name = _safe_name(owner.get("id"))
            if name in params:
                out.add(name)
        return
    if tkind == "Tuple":
        for elem in _as_list(tgt.get("elements")):
            _mark_mutated_param_from_target(elem, params, out)


def _collect_mutated_params_from_stmt(stmt: dict[str, Any], params: set[str], out: set[str]) -> None:
    kind = _kind(stmt)

    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        _mark_mutated_param_from_target(stmt.get("target"), params, out)
    elif kind == "Swap":
        lhs = _as_dict(stmt.get("lhs"))
        rhs = _as_dict(stmt.get("rhs"))
        if _kind(lhs) == "Name":
            left_name = _safe_name(lhs.get("id"))
            if left_name in params:
                out.add(left_name)
        if _kind(rhs) == "Name":
            right_name = _safe_name(rhs.get("id"))
            if right_name in params:
                out.add(right_name)
    elif kind == "Expr":
        call = _as_dict(stmt.get("value"))
        if _kind(call) == "Call":
            func = _as_dict(call.get("func"))
            if _kind(func) == "Attribute":
                owner = _as_dict(func.get("value"))
                if _kind(owner) == "Name":
                    owner_name = _safe_name(owner.get("id"))
                    attr = _safe_name(func.get("attr"))
                    if owner_name in params and attr in _MUTATING_ATTRS:
                        out.add(owner_name)

    if kind == "If":
        for item in _as_list(stmt.get("body")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        for item in _as_list(stmt.get("orelse")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        return
    if kind in {"While", "For"}:
        for item in _as_list(stmt.get("body")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        for item in _as_list(stmt.get("orelse")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        return
    if kind == "Try":
        for item in _as_list(stmt.get("body")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        for handler in _as_list(stmt.get("handlers")):
            for item in _as_list(_as_dict(handler).get("body")):
                _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        for item in _as_list(stmt.get("orelse")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)
        for item in _as_list(stmt.get("finalbody")):
            _collect_mutated_params_from_stmt(_as_dict(item), params, out)


def collect_mutated_params(body_stmts: list[dict[str, Any]], arg_names: list[str]) -> set[str]:
    params = {_safe_name(name) for name in arg_names if _safe_name(name) != ""}
    out: set[str] = set()
    for stmt in body_stmts:
        _collect_mutated_params_from_stmt(_as_dict(stmt), params, out)
    return out


def _function_symbol(module_id: str, scope: tuple[str, ...], fn_node: dict[str, Any]) -> str:
    fn_name = _safe_name(fn_node.get("name"))
    parts = [module_id]
    if len(scope) > 0:
        parts.append(".".join(scope))
    if fn_name != "":
        parts.append(fn_name)
    return "::".join(parts[:1] + [".".join(parts[1:])] if len(parts) > 1 else parts)


def _validate_runtime_abi_shape(fn_node: dict[str, Any], *, symbol: str, top_level: bool) -> dict[str, Any] | None:
    meta = _as_dict(fn_node.get("meta"))
    runtime_abi_any = meta.get("runtime_abi_v1")
    if runtime_abi_any is None:
        return None
    if top_level is False:
        raise RuntimeError("runtime_abi_violation: @abi is supported on top-level functions only: " + symbol)
    runtime_abi = _as_dict(runtime_abi_any)
    schema_version = runtime_abi.get("schema_version", 0)
    if not isinstance(schema_version, int) or int(schema_version) != 1:
        raise RuntimeError("runtime_abi_violation: runtime_abi_v1.schema_version must be 1: " + symbol)
    args_any = runtime_abi.get("args", {})
    if not isinstance(args_any, dict):
        raise RuntimeError("runtime_abi_violation: runtime_abi_v1.args must be an object: " + symbol)
    ret_mode = runtime_abi.get("ret", "default")
    if not isinstance(ret_mode, str) or ret_mode not in _RUNTIME_ABI_MODES:
        raise RuntimeError("runtime_abi_violation: unsupported runtime_abi_v1.ret mode: " + symbol)
    out_args: dict[str, str] = {}
    for key_any, mode_any in args_any.items():
        key = _safe_name(key_any)
        if key == "":
            raise RuntimeError("runtime_abi_violation: runtime_abi_v1.args keys must be non-empty strings: " + symbol)
        if not isinstance(mode_any, str) or mode_any not in _RUNTIME_ABI_MODES:
            raise RuntimeError("runtime_abi_violation: unsupported runtime_abi_v1 arg mode: " + symbol + ": " + key)
        out_args[key] = mode_any
    return {
        "schema_version": 1,
        "args": out_args,
        "ret": ret_mode,
    }


def _validate_runtime_abi_function(
    fn_node: dict[str, Any],
    *,
    module_id: str,
    scope: tuple[str, ...],
    top_level: bool,
) -> None:
    symbol = _function_symbol(module_id, scope, fn_node)
    runtime_abi = _validate_runtime_abi_shape(fn_node, symbol=symbol, top_level=top_level)
    if runtime_abi is None:
        return
    arg_order = [_safe_name(name) for name in _as_list(fn_node.get("arg_order"))]
    arg_names = [name for name in arg_order if name != ""]
    arg_types = _as_dict(fn_node.get("arg_types"))
    if len(arg_names) == 0:
        arg_names = [_safe_name(name) for name in arg_types.keys()]
        arg_names = [name for name in arg_names if name != ""]
    valid_args = set(arg_names)
    readonly_args: set[str] = set()
    for arg_name, mode in runtime_abi["args"].items():
        if arg_name not in valid_args:
            raise RuntimeError("runtime_abi_violation: runtime_abi_v1 references unknown parameter: " + symbol + ": " + arg_name)
        if mode == "value_readonly":
            readonly_args.add(arg_name)
    if len(readonly_args) == 0:
        return
    body = _as_list(fn_node.get("body"))
    mutated = collect_mutated_params([_as_dict(stmt) for stmt in body], arg_names)
    violated = sorted(name for name in readonly_args if name in mutated)
    if len(violated) > 0:
        raise RuntimeError(
            "runtime_abi_violation: value_readonly parameter mutated: "
            + symbol
            + ": "
            + ", ".join(violated)
        )


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
            _validate_runtime_abi_function(
                item,
                module_id=module_id,
                scope=scope,
                top_level=top_level,
            )
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


def validate_runtime_abi_module(module_doc: dict[str, Any]) -> dict[str, Any]:
    module_meta = _as_dict(module_doc.get("meta"))
    module_id = _safe_name(module_meta.get("module_id"))
    if module_id == "":
        module_id = _safe_name(module_doc.get("source_path"))
    if module_id == "":
        module_id = "<module>"
    _walk_function_nodes(_as_list(module_doc.get("body")), module_id=module_id, scope=(), top_level=True)
    return module_doc


__all__ = [
    "collect_mutated_params",
    "validate_runtime_abi_module",
]

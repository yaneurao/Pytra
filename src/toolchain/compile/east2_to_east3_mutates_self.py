"""EAST3 mutates_self detection pass.

Walks class methods and detects whether they mutate ``self`` (direct
field assignment or calling another method that mutates self).
Sets ``mutates_self: true`` on FunctionDef nodes that mutate self.
"""

from __future__ import annotations

from typing import Any


def _method_directly_mutates_self(body: list[Any]) -> bool:
    """Check if any statement in body directly mutates self."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _node_mutates_self(stmt):
            return True
    return False


def _node_mutates_self(node: Any) -> bool:
    """Recursively check if node contains a self mutation."""
    if not isinstance(node, dict):
        return False
    kind = node.get("kind", "")

    # self.attr = ... / self.attr += ...
    if kind in ("Assign", "AnnAssign", "AugAssign"):
        target = node.get("target")
        if isinstance(target, dict):
            if _is_self_attr(target):
                return True
            # self.list.append(...) via Subscript
            if target.get("kind") == "Subscript":
                value = target.get("value")
                if isinstance(value, dict) and _is_self_attr(value):
                    return True

    # self.list.append(...) etc. as Expr Call
    if kind == "Expr":
        value = node.get("value")
        if isinstance(value, dict) and value.get("kind") == "Call":
            func = value.get("func")
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                owner = func.get("value")
                if isinstance(owner, dict) and _is_self_attr(owner):
                    return True

    # Recurse into blocks
    for key in ("body", "orelse", "finalbody"):
        nested = node.get(key)
        if isinstance(nested, list):
            for item in nested:
                if _node_mutates_self(item):
                    return True
    if kind == "Try":
        handlers = node.get("handlers")
        if isinstance(handlers, list):
            for h in handlers:
                if isinstance(h, dict):
                    hbody = h.get("body")
                    if isinstance(hbody, list):
                        for item in hbody:
                            if _node_mutates_self(item):
                                return True
    return False


def _is_self_attr(node: dict[str, Any]) -> bool:
    """Check if node is self.something."""
    if node.get("kind") != "Attribute":
        return False
    value = node.get("value")
    if isinstance(value, dict) and value.get("kind") == "Name" and value.get("id") == "self":
        return True
    return False


def _collect_self_method_calls(body: list[Any]) -> set[str]:
    """Collect method names called as self.method(...)."""
    out: set[str] = set()
    _walk_self_calls(body, out)
    return out


def _walk_self_calls(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_self_calls(item, out)
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Call":
        func = node.get("func")
        if isinstance(func, dict) and func.get("kind") == "Attribute":
            owner = func.get("value")
            if isinstance(owner, dict) and owner.get("kind") == "Name" and owner.get("id") == "self":
                method_name = func.get("attr")
                if isinstance(method_name, str) and method_name != "":
                    out.add(method_name)
    for value in node.values():
        if isinstance(value, (dict, list)):
            _walk_self_calls(value, out)


def _detect_mutates_self_in_class(class_def: dict[str, Any]) -> None:
    """Detect and mark mutates_self for all methods in a ClassDef."""
    body = class_def.get("body")
    if not isinstance(body, list):
        return

    methods: dict[str, dict[str, Any]] = {}
    direct_mutators: set[str] = set()
    call_graph: dict[str, set[str]] = {}

    for stmt in body:
        if not isinstance(stmt, dict) or stmt.get("kind") != "FunctionDef":
            continue
        name = stmt.get("name", "")
        if not isinstance(name, str) or name == "":
            continue
        methods[name] = stmt
        method_body = stmt.get("body")
        if isinstance(method_body, list) and _method_directly_mutates_self(method_body):
            direct_mutators.add(name)
        call_graph[name] = _collect_self_method_calls(method_body) if isinstance(method_body, list) else set()

    # Propagate: if method A calls method B which mutates self, A also mutates self
    mutators = set(direct_mutators)
    changed = True
    while changed:
        changed = False
        for name, callees in call_graph.items():
            if name in mutators:
                continue
            for callee in callees:
                if callee in mutators:
                    mutators.add(name)
                    changed = True
                    break

    # __init__ and __del__ always mutate self
    for special in ("__init__", "__del__"):
        if special in methods:
            mutators.add(special)

    # Set flags
    for name, stmt in methods.items():
        stmt["mutates_self"] = name in mutators


def _walk_and_detect(node: Any) -> None:
    """Walk EAST3 and detect mutates_self in all ClassDefs."""
    if isinstance(node, list):
        for item in node:
            _walk_and_detect(item)
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "ClassDef":
        _detect_mutates_self_in_class(node)
    for value in node.values():
        if isinstance(value, (dict, list)):
            _walk_and_detect(value)


def detect_mutates_self(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: detect mutates_self in all class methods."""
    _walk_and_detect(module)
    return module

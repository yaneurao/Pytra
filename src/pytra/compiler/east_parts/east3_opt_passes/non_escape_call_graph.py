"""Call graph extraction and SCC utilities for non-escape IPA."""

from __future__ import annotations

from pytra.std.typing import Any


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _collect_function_symbols(module_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    symbols: dict[str, dict[str, Any]] = {}
    body_any = module_doc.get("body")
    body = body_any if isinstance(body_any, list) else []

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            name = _safe_name(node.get("name"))
            if name != "":
                symbols[name] = node
        if isinstance(node, dict) and node.get("kind") == "ClassDef":
            cls_name = _safe_name(node.get("name"))
            cls_body_any = node.get("body")
            cls_body = cls_body_any if isinstance(cls_body_any, list) else []
            j = 0
            while j < len(cls_body):
                child = cls_body[j]
                if isinstance(child, dict) and child.get("kind") == "FunctionDef":
                    fn_name = _safe_name(child.get("name"))
                    if cls_name != "" and fn_name != "":
                        symbols[cls_name + "." + fn_name] = child
                j += 1
        i += 1
    return symbols


def _collect_calls(node: Any, out: list[dict[str, Any]]) -> None:
    if isinstance(node, list):
        i = 0
        while i < len(node):
            _collect_calls(node[i], out)
            i += 1
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Call":
        out.append(node)
    for value in node.values():
        _collect_calls(value, out)


def _resolve_call_target(
    call_node: dict[str, Any],
    *,
    owner_class: str,
    known_symbols: set[str],
) -> str:
    func_any = call_node.get("func")
    if not isinstance(func_any, dict):
        return ""
    kind = _safe_name(func_any.get("kind"))
    if kind == "Name":
        callee = _safe_name(func_any.get("id"))
        if callee in known_symbols:
            return callee
        return ""
    if kind != "Attribute":
        return ""
    attr_name = _safe_name(func_any.get("attr"))
    value_any = func_any.get("value")
    if not isinstance(value_any, dict):
        return ""
    if _safe_name(value_any.get("kind")) != "Name":
        return ""
    owner_name = _safe_name(value_any.get("id"))
    if owner_name == "self" and owner_class != "":
        target = owner_class + "." + attr_name
        if target in known_symbols:
            return target
    target = owner_name + "." + attr_name
    if target in known_symbols:
        return target
    return ""


def build_non_escape_call_graph(module_doc: dict[str, Any]) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Build function-level call graph and unresolved call counts.

    Returns:
        graph:
          key=caller symbol, value=set of resolved callee symbols.
        unresolved_calls:
          key=caller symbol, value=count of unresolved/dynamic calls.
    """
    symbols = _collect_function_symbols(module_doc)
    known_symbols = set(symbols.keys())
    graph: dict[str, set[str]] = {}
    unresolved_calls: dict[str, int] = {}

    for caller in sorted(symbols.keys()):
        fn_node = symbols[caller]
        owner_class = ""
        if "." in caller:
            owner_class = caller.split(".", 1)[0]
        calls: list[dict[str, Any]] = []
        _collect_calls(fn_node.get("body"), calls)
        edges: set[str] = set()
        unresolved = 0
        i = 0
        while i < len(calls):
            target = _resolve_call_target(
                calls[i],
                owner_class=owner_class,
                known_symbols=known_symbols,
            )
            if target == "":
                unresolved += 1
            else:
                edges.add(target)
            i += 1
        graph[caller] = edges
        unresolved_calls[caller] = unresolved
    return graph, unresolved_calls


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    """Deterministic Tarjan SCC decomposition."""
    index = 0
    index_map: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    sccs: list[list[str]] = []

    def _strong_connect(v: str) -> None:
        nonlocal index
        index_map[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        neighbors = graph.get(v, set())
        for w in sorted(neighbors):
            if w not in index_map:
                _strong_connect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index_map[w])

        if lowlink[v] == index_map[v]:
            comp: list[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            comp.sort()
            sccs.append(comp)

    for node in sorted(graph.keys()):
        if node not in index_map:
            _strong_connect(node)
    return sccs

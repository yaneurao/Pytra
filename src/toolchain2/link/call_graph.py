"""Call graph construction for linked programs.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/program_call_graph.py (import はしない)。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytra.std.json import JsonVal

if TYPE_CHECKING:
    from toolchain2.link.linker import LinkedModule


def _collect_symbols(
    east_doc: dict[str, JsonVal],
    module_id: str,
) -> dict[str, str]:
    """Collect function symbols from a module's EAST3.

    Returns: {qualified_name: module_id}
    """
    symbols: dict[str, str] = {}
    body_val = east_doc.get("body")
    if not isinstance(body_val, list):
        return symbols

    for stmt in body_val:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind == "FunctionDef":
            name = stmt.get("name")
            if isinstance(name, str) and name.strip() != "":
                qualified = module_id + "::" + name.strip()
                symbols[qualified] = module_id
        elif kind == "ClassDef":
            class_name = stmt.get("name")
            if not isinstance(class_name, str):
                continue
            class_body = stmt.get("body")
            if not isinstance(class_body, list):
                continue
            for method in class_body:
                if not isinstance(method, dict):
                    continue
                if method.get("kind") == "FunctionDef":
                    method_name = method.get("name")
                    if isinstance(method_name, str) and method_name.strip() != "":
                        qualified = module_id + "::" + class_name.strip() + "." + method_name.strip()
                        symbols[qualified] = module_id

    return symbols


def _collect_calls_in_node(
    node: JsonVal,
    known_symbols: set[str],
    module_id: str,
    current_fn: str,
    graph: dict[str, set[str]],
    unresolved: dict[str, int],
) -> None:
    """Recursively collect call edges from a node."""
    if isinstance(node, dict):
        if node.get("kind") == "Call":
            func = node.get("func")
            callee = ""
            if isinstance(func, dict):
                func_kind = func.get("kind")
                if func_kind == "Name":
                    name_id = func.get("id")
                    if isinstance(name_id, str):
                        # Try qualified name first
                        qualified = module_id + "::" + name_id.strip()
                        if qualified in known_symbols:
                            callee = qualified
                        else:
                            # Try as-is
                            for sym in known_symbols:
                                if sym.endswith("::" + name_id.strip()):
                                    callee = sym
                                    break
                elif func_kind == "Attribute":
                    attr = func.get("attr")
                    if isinstance(attr, str):
                        # Try meta.non_escape_callsite
                        meta_val = node.get("meta")
                        if isinstance(meta_val, dict):
                            nec = meta_val.get("non_escape_callsite")
                            if isinstance(nec, dict):
                                callee_val = nec.get("callee")
                                if isinstance(callee_val, str) and callee_val in known_symbols:
                                    callee = callee_val
            if callee != "":
                if current_fn not in graph:
                    graph[current_fn] = set()
                graph[current_fn].add(callee)
            else:
                if current_fn != "":
                    unresolved[current_fn] = unresolved.get(current_fn, 0) + 1

        for v in node.values():
            _collect_calls_in_node(v, known_symbols, module_id, current_fn, graph, unresolved)
    elif isinstance(node, list):
        for item in node:
            _collect_calls_in_node(item, known_symbols, module_id, current_fn, graph, unresolved)


def _build_module_call_graph(
    east_doc: dict[str, JsonVal],
    module_id: str,
    known_symbols: set[str],
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Build call graph for a single module."""
    graph: dict[str, set[str]] = {}
    unresolved: dict[str, int] = {}

    body_val = east_doc.get("body")
    if not isinstance(body_val, list):
        return graph, unresolved

    for stmt in body_val:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind == "FunctionDef":
            name = stmt.get("name")
            if isinstance(name, str):
                fn_qualified = module_id + "::" + name.strip()
                if fn_qualified not in graph:
                    graph[fn_qualified] = set()
                _collect_calls_in_node(
                    stmt.get("body", []),
                    known_symbols, module_id, fn_qualified, graph, unresolved,
                )
        elif kind == "ClassDef":
            class_name = stmt.get("name")
            if not isinstance(class_name, str):
                continue
            class_body = stmt.get("body")
            if not isinstance(class_body, list):
                continue
            for method in class_body:
                if not isinstance(method, dict) or method.get("kind") != "FunctionDef":
                    continue
                method_name = method.get("name")
                if isinstance(method_name, str):
                    fn_qualified = module_id + "::" + class_name.strip() + "." + method_name.strip()
                    if fn_qualified not in graph:
                        graph[fn_qualified] = set()
                    _collect_calls_in_node(
                        method.get("body", []),
                        known_symbols, module_id, fn_qualified, graph, unresolved,
                    )

    # Also scan main_guard_body
    main_guard = east_doc.get("main_guard_body")
    if isinstance(main_guard, list):
        has_main_guard = False
        for item in main_guard:
            _ = item
            has_main_guard = True
            break
        if has_main_guard:
            main_fn = module_id + "::__main__"
            if main_fn not in graph:
                graph[main_fn] = set()
            _collect_calls_in_node(main_guard, known_symbols, module_id, main_fn, graph, unresolved)

    return graph, unresolved


def _strongly_connected_components(
    graph: dict[str, set[str]],
) -> list[tuple[str, ...]]:
    """Tarjan's SCC algorithm."""
    index_counter: list[int] = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    index_map: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[tuple[str, ...]] = []

    def _strongconnect(v: str) -> None:
        index_map[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] = index_counter[0] + 1
        stack.append(v)
        on_stack.add(v)

        for w in sorted(graph.get(v, set())):
            if w not in index_map:
                _strongconnect(w)
                if lowlink[w] < lowlink[v]:
                    lowlink[v] = lowlink[w]
            elif w in on_stack:
                if index_map[w] < lowlink[v]:
                    lowlink[v] = index_map[w]

        if lowlink[v] == index_map[v]:
            component: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == v:
                    break
            result.append(tuple(sorted(component)))

    for node in sorted(graph.keys()):
        if node not in index_map:
            _strongconnect(node)

    return result


def build_call_graph(
    modules: list[LinkedModule],
) -> tuple[dict[str, tuple[str, ...]], list[tuple[str, ...]]]:
    """Build program-wide call graph.

    Returns:
        (graph, sccs)
        - graph: {caller: (callee, ...)}
        - sccs: list of strongly connected components
    """
    # Collect all known symbols
    known_symbols: set[str] = set()
    for module in sorted(modules, key=lambda m: m.module_id):
        doc = module.east_doc
        if isinstance(doc, dict):
            syms = _collect_symbols(doc, module.module_id)
            known_symbols.update(syms.keys())

    # Build per-module call graphs and merge
    raw_graph: dict[str, set[str]] = {}
    all_unresolved: dict[str, int] = {}

    for module in sorted(modules, key=lambda m: m.module_id):
        doc = module.east_doc
        if not isinstance(doc, dict):
            continue
        module_graph, module_unresolved = _build_module_call_graph(
            doc, module.module_id, known_symbols,
        )
        for caller in sorted(module_graph.keys()):
            raw_graph[caller] = set(sorted(module_graph[caller]))
            all_unresolved[caller] = int(module_unresolved.get(caller, 0))

    # Compute SCCs
    sccs = _strongly_connected_components(raw_graph)

    # Convert to sorted tuples for determinism
    graph: dict[str, tuple[str, ...]] = {}
    for caller in sorted(raw_graph.keys()):
        graph[caller] = tuple(sorted(raw_graph[caller]))

    return graph, sccs

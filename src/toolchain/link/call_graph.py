"""Call graph construction for linked programs.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/program_call_graph.py (import はしない)。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.typing import cast

from toolchain.link.shared_types import LinkedModule
from toolchain.compile.jv import jv_is_dict, jv_is_list, jv_dict, jv_list, nd_get_str, nd_get_dict, nd_get_list


def _collect_symbols(
    east_doc: dict[str, JsonVal],
    module_id: str,
) -> dict[str, str]:
    """Collect function symbols from a module's EAST3.

    Returns: {qualified_name: module_id}
    """
    symbols: dict[str, str] = {}
    body_val: JsonVal = east_doc.get("body")
    if not jv_is_list(body_val):
        return symbols

    for stmt in jv_list(body_val):
        if not jv_is_dict(stmt):
            continue
        stmt_node = jv_dict(stmt)
        kind = nd_get_str(stmt_node, "kind")
        if kind == "FunctionDef":
            name = nd_get_str(stmt_node, "name").strip()
            if name != "":
                qualified = module_id + "::" + name
                symbols[qualified] = module_id
        elif kind == "ClassDef":
            class_name = nd_get_str(stmt_node, "name").strip()
            if class_name == "":
                continue
            class_body = nd_get_list(stmt, "body")
            if len(class_body) == 0:
                continue
            for method in class_body:
                if not jv_is_dict(method):
                    continue
                method_node = jv_dict(method)
                if nd_get_str(method_node, "kind") == "FunctionDef":
                    method_name = nd_get_str(method_node, "name").strip()
                    if method_name != "":
                        qualified = module_id + "::" + class_name + "." + method_name
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
    if jv_is_dict(node):
        node_map = jv_dict(node)
        if nd_get_str(node_map, "kind") == "Call":
            func_node = nd_get_dict(node, "func")
            callee = ""
            func_kind = nd_get_str(func_node, "kind")
            if func_kind != "":
                if func_kind == "Name":
                    name_id = nd_get_str(func_node, "id").strip()
                    if name_id != "":
                        qualified = module_id + "::" + name_id
                        if qualified in known_symbols:
                            callee = qualified
                        else:
                            for sym in known_symbols:
                                if sym.endswith("::" + name_id):
                                    callee = sym
                                    break
                elif func_kind == "Attribute":
                    attr = nd_get_str(func_node, "attr")
                    if attr != "":
                        meta_val = nd_get_dict(node, "meta")
                        nec = nd_get_dict(meta_val, "non_escape_callsite")
                        callee_val = nd_get_str(nec, "callee")
                        if callee_val in known_symbols:
                            callee = "" + callee_val
            if callee != "":
                if current_fn not in graph:
                    graph[current_fn] = set()
                graph[current_fn].add(callee)
            else:
                if current_fn != "":
                    unresolved[current_fn] = unresolved.get(current_fn, 0) + 1

        for _k, v in node_map.items():
            _collect_calls_in_node(v, known_symbols, module_id, current_fn, graph, unresolved)
    elif jv_is_list(node):
        for item in jv_list(node):
            _collect_calls_in_node(item, known_symbols, module_id, current_fn, graph, unresolved)

def _build_module_call_graph(
    east_doc: dict[str, JsonVal],
    module_id: str,
    known_symbols: set[str],
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Build call graph for a single module."""
    graph: dict[str, set[str]] = {}
    unresolved: dict[str, int] = {}

    body_val: JsonVal = east_doc.get("body")
    if not jv_is_list(body_val):
        return graph, unresolved

    for stmt in jv_list(body_val):
        if not jv_is_dict(stmt):
            continue
        stmt_node = jv_dict(stmt)
        kind = nd_get_str(stmt_node, "kind")
        if kind == "FunctionDef":
            name = nd_get_str(stmt_node, "name").strip()
            if name != "":
                fn_qualified = module_id + "::" + name
                if fn_qualified not in graph:
                    graph[fn_qualified] = set()
                _collect_calls_in_node(
                    nd_get_list(stmt, "body"),
                    known_symbols, module_id, fn_qualified, graph, unresolved,
                )
        elif kind == "ClassDef":
            class_name = nd_get_str(stmt_node, "name").strip()
            if class_name == "":
                continue
            class_body = nd_get_list(stmt, "body")
            if len(class_body) == 0:
                continue
            for method in class_body:
                if not jv_is_dict(method):
                    continue
                method_node = jv_dict(method)
                if nd_get_str(method_node, "kind") != "FunctionDef":
                    continue
                method_name = nd_get_str(method_node, "name").strip()
                if method_name != "":
                    fn_qualified = module_id + "::" + class_name + "." + method_name
                    if fn_qualified not in graph:
                        graph[fn_qualified] = set()
                    _collect_calls_in_node(
                        nd_get_list(method, "body"),
                        known_symbols, module_id, fn_qualified, graph, unresolved,
                    )

    main_guard: JsonVal = east_doc.get("main_guard_body")
    if jv_is_list(main_guard) and len(jv_list(main_guard)) != 0:
        main_fn = module_id + "::__main__"
        if main_fn not in graph:
            graph[main_fn] = set()
        _collect_calls_in_node(main_guard, known_symbols, module_id, main_fn, graph, unresolved)

    return graph, unresolved

def _strongly_connected_components(
    graph: dict[str, set[str]],
) -> list[list[str]]:
    """Tarjan's SCC algorithm."""
    index_counter: list[int] = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    index_map: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[list[str]] = []

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
            result.append(sorted(component))

    for node in sorted(graph.keys()):
        if node not in index_map:
            _strongconnect(node)

    return result


def build_call_graph(
    modules: list[LinkedModule],
) -> tuple[dict[str, list[str]], list[list[str]]]:
    """Build program-wide call graph.

    Returns:
        (graph, sccs)
        - graph: {caller: [callee, ...]}
        - sccs: list of strongly connected components
    """
    known_symbols: set[str] = set()
    modules_sorted = sorted(modules, key=lambda m: m.module_id)
    for module in modules_sorted:
        doc_node: dict[str, JsonVal] = module.east_doc
        syms = _collect_symbols(doc_node, module.module_id)
        for sym in syms.keys():
            known_symbols.add(sym)

    raw_graph: dict[str, set[str]] = {}
    all_unresolved: dict[str, int] = {}

    for module in modules_sorted:
        doc_node: dict[str, JsonVal] = module.east_doc
        module_graph, module_unresolved = _build_module_call_graph(
            doc_node, module.module_id, known_symbols,
        )
        for caller in sorted(module_graph.keys()):
            raw_graph[caller] = set(sorted(module_graph[caller]))
            all_unresolved[caller] = int(module_unresolved.get(caller, 0))

    sccs = _strongly_connected_components(raw_graph)

    graph: dict[str, list[str]] = {}
    for caller in sorted(raw_graph.keys()):
        callee_list: list[str] = []
        for callee in sorted(raw_graph[caller]):
            callee_list.append(callee)
        graph[caller] = callee_list

    return graph, sccs


"""Call graph extraction and SCC utilities for non-escape IPA."""

from __future__ import annotations

from pytra.std.typing import Any


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _normalize_module_id(raw: str) -> str:
    text = raw.strip()
    if text == "":
        return ""
    norm = text.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    if norm.endswith(".py"):
        norm = norm[:-3]
    norm = norm.replace("/", ".")
    while ".." in norm:
        norm = norm.replace("..", ".")
    if norm.startswith("."):
        norm = norm[1:]
    if norm.endswith("."):
        norm = norm[:-1]
    return norm


def module_id_for_doc(module_doc: dict[str, Any]) -> str:
    meta_any = module_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    module_id = _normalize_module_id(_safe_name(meta.get("module_id")))
    if module_id != "":
        return module_id
    source_path = _normalize_module_id(_safe_name(module_doc.get("source_path")))
    if source_path != "":
        return source_path
    return "__module__"


def qualify_non_escape_symbol(module_id: str, symbol: str) -> str:
    mod = _normalize_module_id(module_id)
    sym = _safe_name(symbol)
    if sym == "":
        return ""
    if mod == "":
        mod = "__module__"
    return mod + "::" + sym


def collect_non_escape_symbols(module_doc: dict[str, Any]) -> tuple[str, dict[str, dict[str, Any]], dict[str, str]]:
    module_id = module_id_for_doc(module_doc)
    symbols: dict[str, dict[str, Any]] = {}
    local_to_qualified: dict[str, str] = {}
    body_any = module_doc.get("body")
    body = body_any if isinstance(body_any, list) else []

    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "FunctionDef":
            name = _safe_name(node.get("name"))
            if name != "":
                qualified = qualify_non_escape_symbol(module_id, name)
                if qualified != "":
                    symbols[qualified] = node
                    local_to_qualified[name] = qualified
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
                        local_symbol = cls_name + "." + fn_name
                        qualified = qualify_non_escape_symbol(module_id, local_symbol)
                        if qualified != "":
                            symbols[qualified] = child
                            local_to_qualified[local_symbol] = qualified
                j += 1
        i += 1
    return module_id, symbols, local_to_qualified


def collect_non_escape_import_maps(module_doc: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    import_modules: dict[str, str] = {}
    import_symbols: dict[str, str] = {}
    meta_any = module_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}

    legacy_modules_any = meta.get("import_modules")
    if isinstance(legacy_modules_any, dict):
        for local_any, module_any in legacy_modules_any.items():
            local_name = _safe_name(local_any)
            module_id = _normalize_module_id(_safe_name(module_any))
            if local_name != "" and module_id != "":
                import_modules[local_name] = module_id

    legacy_symbols_any = meta.get("import_symbols")
    if isinstance(legacy_symbols_any, dict):
        for local_any, payload_any in legacy_symbols_any.items():
            local_name = _safe_name(local_any)
            payload = payload_any if isinstance(payload_any, dict) else {}
            module_id = _normalize_module_id(_safe_name(payload.get("module")))
            export_name = _safe_name(payload.get("name"))
            if local_name != "" and module_id != "" and export_name != "":
                import_symbols[local_name] = qualify_non_escape_symbol(module_id, export_name)

    bindings_any = meta.get("import_bindings")
    bindings = bindings_any if isinstance(bindings_any, list) else []
    i = 0
    while i < len(bindings):
        ent = bindings[i]
        if not isinstance(ent, dict):
            i += 1
            continue
        binding_kind = _safe_name(ent.get("binding_kind"))
        module_id = _normalize_module_id(_safe_name(ent.get("module_id")))
        local_name = _safe_name(ent.get("local_name"))
        export_name = _safe_name(ent.get("export_name"))
        if binding_kind == "module":
            if local_name != "" and module_id != "":
                import_modules[local_name] = module_id
        elif binding_kind == "symbol":
            if local_name != "" and module_id != "" and export_name != "":
                import_symbols[local_name] = qualify_non_escape_symbol(module_id, export_name)
        i += 1

    return import_modules, import_symbols


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


def resolve_non_escape_call_target(
    call_node: dict[str, Any],
    *,
    owner_class: str,
    local_symbol_map: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
    known_symbols: set[str],
) -> tuple[str, bool]:
    func_any = call_node.get("func")
    if not isinstance(func_any, dict):
        return "", False
    kind = _safe_name(func_any.get("kind"))
    if kind == "Name":
        callee = _safe_name(func_any.get("id"))
        if callee == "":
            return "", False
        candidate = local_symbol_map.get(callee, "")
        if candidate == "":
            candidate = import_symbols.get(callee, "")
        if candidate == "":
            return "", False
        return candidate, candidate in known_symbols
    if kind != "Attribute":
        return "", False
    attr_name = _safe_name(func_any.get("attr"))
    value_any = func_any.get("value")
    if not isinstance(value_any, dict):
        return "", False
    if _safe_name(value_any.get("kind")) != "Name":
        return "", False
    owner_name = _safe_name(value_any.get("id"))
    if owner_name == "self" and owner_class != "":
        self_local = owner_class + "." + attr_name
        candidate = local_symbol_map.get(self_local, "")
        if candidate != "":
            return candidate, candidate in known_symbols
    local_target = owner_name + "." + attr_name
    candidate = local_symbol_map.get(local_target, "")
    if candidate != "":
        return candidate, candidate in known_symbols
    imported_module = import_modules.get(owner_name, "")
    if imported_module != "":
        candidate = qualify_non_escape_symbol(imported_module, attr_name)
        return candidate, candidate in known_symbols
    return "", False


def build_non_escape_call_graph(
    module_doc: dict[str, Any],
    *,
    known_symbols: set[str] | None = None,
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Build function-level call graph and unresolved call counts.

    Returns:
        graph:
          key=caller symbol, value=set of resolved callee symbols.
        unresolved_calls:
          key=caller symbol, value=count of unresolved/dynamic calls.
    """
    _module_id, symbols, local_symbol_map = collect_non_escape_symbols(module_doc)
    import_modules, import_symbols = collect_non_escape_import_maps(module_doc)
    known = set(symbols.keys()) if known_symbols is None else set(known_symbols)
    graph: dict[str, set[str]] = {}
    unresolved_calls: dict[str, int] = {}

    for caller in sorted(symbols.keys()):
        fn_node = symbols[caller]
        owner_class = ""
        local_caller = caller
        if "::" in local_caller:
            local_caller = local_caller.split("::", 1)[1]
        if "." in local_caller:
            owner_class = local_caller.split(".", 1)[0]
        calls: list[dict[str, Any]] = []
        _collect_calls(fn_node.get("body"), calls)
        edges: set[str] = set()
        unresolved = 0
        i = 0
        while i < len(calls):
            target, resolved = resolve_non_escape_call_target(
                calls[i],
                owner_class=owner_class,
                local_symbol_map=local_symbol_map,
                import_modules=import_modules,
                import_symbols=import_symbols,
                known_symbols=known,
            )
            if not resolved:
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

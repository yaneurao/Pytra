"""Interprocedural non-escape summary analysis for EAST3."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import build_non_escape_call_graph
from pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import collect_non_escape_import_maps
from pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import collect_non_escape_symbols
from pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import module_id_for_doc
from pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import resolve_non_escape_call_target
from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _collect_calls(node: Any, out: list[tuple[dict[str, Any], bool]]) -> None:
    def _walk(cur: Any, in_return_expr: bool) -> None:
        if isinstance(cur, list):
            i = 0
            while i < len(cur):
                _walk(cur[i], in_return_expr=False)
                i += 1
            return
        if not isinstance(cur, dict):
            return
        kind = cur.get("kind")
        if kind == "Return":
            value_any = cur.get("value")
            if isinstance(value_any, dict):
                _walk(value_any, in_return_expr=True)
            return
        if kind == "Call":
            out.append((cur, in_return_expr))
        for value in cur.values():
            _walk(value, in_return_expr=False)

    _walk(node, in_return_expr=False)


def _collect_arg_refs(node: Any, arg_index: dict[str, int], out: set[int]) -> None:
    if isinstance(node, list):
        i = 0
        while i < len(node):
            _collect_arg_refs(node[i], arg_index, out)
            i += 1
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Name":
        ident = _safe_name(node.get("id"))
        if ident in arg_index:
            out.add(arg_index[ident])
    for value in node.values():
        _collect_arg_refs(value, arg_index, out)


def _ensure_meta(node: dict[str, Any]) -> dict[str, Any]:
    meta_any = node.get("meta")
    if isinstance(meta_any, dict):
        return meta_any
    meta: dict[str, Any] = {}
    node["meta"] = meta
    return meta


def _set_meta_value(node: dict[str, Any], key: str, value: Any) -> bool:
    meta = _ensure_meta(node)
    if meta.get(key) == value:
        return False
    meta[key] = value
    return True


def _collect_non_escape_module_closure(module_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    root_module_id = module_id_for_doc(module_doc)
    out[root_module_id] = module_doc
    meta_any = module_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    closure_any = meta.get("non_escape_import_closure")
    closure = closure_any if isinstance(closure_any, dict) else {}
    for module_id_any, doc_any in closure.items():
        module_id = _safe_name(module_id_any)
        if module_id == "":
            continue
        if not isinstance(doc_any, dict) or doc_any.get("kind") != "Module":
            continue
        child_doc = doc_any
        child_meta_any = child_doc.get("meta")
        child_meta = child_meta_any if isinstance(child_meta_any, dict) else {}
        if _safe_name(child_meta.get("module_id")) == "":
            child_meta["module_id"] = module_id
            child_doc["meta"] = child_meta
        out[module_id] = child_doc
    return out


def _collect_return_from_args(node: Any, arg_index: dict[str, int], out: set[int]) -> tuple[bool, int]:
    """Collect direct return escapes.

    Returns:
      (has_non_none_return, direct_return_stmt_count)
    """
    has_return_value = False
    direct_return_count = 0
    if isinstance(node, list):
        i = 0
        while i < len(node):
            has_val_i, cnt_i = _collect_return_from_args(node[i], arg_index, out)
            has_return_value = has_return_value or has_val_i
            direct_return_count += cnt_i
            i += 1
        return has_return_value, direct_return_count
    if not isinstance(node, dict):
        return False, 0
    if node.get("kind") == "Return":
        value_any = node.get("value")
        if isinstance(value_any, dict):
            has_return_value = True
            direct_return_count = 1
            refs: set[int] = set()
            _collect_arg_refs(value_any, arg_index, refs)
            for idx in refs:
                out.add(idx)
        return has_return_value, direct_return_count
    for value in node.values():
        has_val_i, cnt_i = _collect_return_from_args(value, arg_index, out)
        has_return_value = has_return_value or has_val_i
        direct_return_count += cnt_i
    return has_return_value, direct_return_count


class NonEscapeInterproceduralPass(East3OptimizerPass):
    """Compute conservative function summaries for non-escape decisions."""

    name = "NonEscapeInterproceduralPass"
    min_opt_level = 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        module_doc = east3_doc if isinstance(east3_doc, dict) else {}
        if module_doc.get("kind") != "Module":
            return PassResult()

        module_docs = _collect_non_escape_module_closure(module_doc)
        symbols: dict[str, dict[str, Any]] = {}
        symbol_module_ids: dict[str, str] = {}
        module_local_symbol_maps: dict[str, dict[str, str]] = {}
        module_import_modules_maps: dict[str, dict[str, str]] = {}
        module_import_symbols_maps: dict[str, dict[str, str]] = {}
        for module_id, mod_doc in module_docs.items():
            _mod_id, mod_symbols, local_symbol_map = collect_non_escape_symbols(mod_doc)
            module_local_symbol_maps[module_id] = local_symbol_map
            import_modules, import_symbols = collect_non_escape_import_maps(mod_doc)
            module_import_modules_maps[module_id] = import_modules
            module_import_symbols_maps[module_id] = import_symbols
            for symbol, fn_node in mod_symbols.items():
                symbols[symbol] = fn_node
                symbol_module_ids[symbol] = module_id
        if len(symbols) == 0:
            return PassResult()

        known_symbols = set(symbols.keys())
        graph: dict[str, set[str]] = {}
        unresolved_counts: dict[str, int] = {}
        for _module_id, mod_doc in module_docs.items():
            mod_graph, mod_unresolved = build_non_escape_call_graph(mod_doc, known_symbols=known_symbols)
            graph.update(mod_graph)
            unresolved_counts.update(mod_unresolved)

        callsites_by_symbol: dict[str, list[dict[str, object]]] = {}
        summary: dict[str, dict[str, object]] = {}
        sorted_symbols = sorted(symbols.keys())

        i = 0
        while i < len(sorted_symbols):
            symbol = sorted_symbols[i]
            fn_node = symbols[symbol]
            arg_order_any = fn_node.get("arg_order")
            arg_order_raw = arg_order_any if isinstance(arg_order_any, list) else []
            arg_order: list[str] = []
            j = 0
            while j < len(arg_order_raw):
                nm = _safe_name(arg_order_raw[j])
                if nm != "":
                    arg_order.append(nm)
                j += 1
            arg_index = {name: idx for idx, name in enumerate(arg_order)}

            direct_return_from_args: set[int] = set()
            has_return_value, _ = _collect_return_from_args(fn_node.get("body"), arg_index, direct_return_from_args)
            direct_arg_escape = [False] * len(arg_order)

            owner_module_id = symbol_module_ids.get(symbol, "")
            local_symbol_map = module_local_symbol_maps.get(owner_module_id, {})
            import_modules = module_import_modules_maps.get(owner_module_id, {})
            import_symbols = module_import_symbols_maps.get(owner_module_id, {})
            owner_class = ""
            local_symbol = symbol.split("::", 1)[1] if "::" in symbol else symbol
            if "." in local_symbol:
                owner_class = local_symbol.split(".", 1)[0]
            calls: list[tuple[dict[str, Any], bool]] = []
            _collect_calls(fn_node.get("body"), calls)
            sites: list[dict[str, object]] = []
            k = 0
            while k < len(calls):
                call_node, in_return_expr = calls[k]
                target, resolved = resolve_non_escape_call_target(
                    call_node,
                    owner_class=owner_class,
                    local_symbol_map=local_symbol_map,
                    import_modules=import_modules,
                    import_symbols=import_symbols,
                    known_symbols=known_symbols,
                )
                args_any = call_node.get("args")
                args = args_any if isinstance(args_any, list) else []
                arg_sources: list[list[int]] = []
                a = 0
                while a < len(args):
                    refs: set[int] = set()
                    _collect_arg_refs(args[a], arg_index, refs)
                    arg_sources.append(sorted(refs))
                    a += 1

                if not resolved and bool(context.non_escape_policy.get("unknown_call_escape", True)):
                    a = 0
                    while a < len(arg_sources):
                        refs = arg_sources[a]
                        b = 0
                        while b < len(refs):
                            direct_arg_escape[refs[b]] = True
                            b += 1
                        a += 1

                sites.append(
                    {
                        "callee": target,
                        "resolved": resolved,
                        "arg_sources": arg_sources,
                        "in_return_expr": in_return_expr,
                        "call_node": call_node,
                    }
                )
                k += 1

            callsites_by_symbol[symbol] = sites
            ret_from_args = [False] * len(arg_order)
            for idx in direct_return_from_args:
                if idx >= 0 and idx < len(ret_from_args):
                    ret_from_args[idx] = True
            ret_escape = bool(has_return_value or any(ret_from_args))
            if bool(context.non_escape_policy.get("unknown_call_escape", True)) and int(unresolved_counts.get(symbol, 0)) > 0:
                ret_escape = True
            summary[symbol] = {
                "symbol": symbol,
                "arg_order": list(arg_order),
                "arg_escape": list(direct_arg_escape),
                "return_escape": ret_escape,
                "return_from_args": ret_from_args,
                "unresolved_calls": int(unresolved_counts.get(symbol, 0)),
            }
            i += 1

        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(sorted_symbols):
                symbol = sorted_symbols[i]
                cur = summary[symbol]
                arg_escape = list(cur.get("arg_escape", []))
                ret_from_args = list(cur.get("return_from_args", []))
                ret_escape = bool(cur.get("return_escape", False))
                sites = callsites_by_symbol.get(symbol, [])
                s = 0
                while s < len(sites):
                    site = sites[s]
                    callee = site.get("callee")
                    if not isinstance(callee, str) or callee == "":
                        s += 1
                        continue
                    callee_sum = summary.get(callee)
                    if not isinstance(callee_sum, dict):
                        s += 1
                        continue
                    src_lists_any = site.get("arg_sources")
                    src_lists = src_lists_any if isinstance(src_lists_any, list) else []
                    callee_arg_escape_any = callee_sum.get("arg_escape")
                    callee_arg_escape = callee_arg_escape_any if isinstance(callee_arg_escape_any, list) else []
                    j = 0
                    while j < len(callee_arg_escape):
                        if bool(callee_arg_escape[j]) and j < len(src_lists):
                            refs_any = src_lists[j]
                            refs = refs_any if isinstance(refs_any, list) else []
                            r = 0
                            while r < len(refs):
                                src_idx = int(refs[r])
                                if src_idx >= 0 and src_idx < len(arg_escape) and not arg_escape[src_idx]:
                                    arg_escape[src_idx] = True
                                    changed = True
                                r += 1
                        j += 1
                    if bool(site.get("in_return_expr", False)):
                        if bool(callee_sum.get("return_escape", False)) and not ret_escape:
                            ret_escape = True
                            changed = True
                        callee_ret_from_any = callee_sum.get("return_from_args")
                        callee_ret_from = callee_ret_from_any if isinstance(callee_ret_from_any, list) else []
                        j = 0
                        while j < len(callee_ret_from):
                            if bool(callee_ret_from[j]) and j < len(src_lists):
                                refs_any = src_lists[j]
                                refs = refs_any if isinstance(refs_any, list) else []
                                r = 0
                                while r < len(refs):
                                    src_idx = int(refs[r])
                                    if src_idx >= 0 and src_idx < len(ret_from_args) and not ret_from_args[src_idx]:
                                        ret_from_args[src_idx] = True
                                        changed = True
                                    r += 1
                            j += 1
                    s += 1
                if any(ret_from_args) and not ret_escape:
                    ret_escape = True
                    changed = True
                cur["arg_escape"] = arg_escape
                cur["return_from_args"] = ret_from_args
                cur["return_escape"] = ret_escape
                i += 1

        meta_any = module_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        old_summary = meta.get("non_escape_summary")
        out_summary: dict[str, object] = {}
        annotation_changes = 0
        i = 0
        while i < len(sorted_symbols):
            symbol = sorted_symbols[i]
            fn_summary = summary[symbol]
            out_summary[symbol] = fn_summary
            fn_node = symbols[symbol]
            fn_payload = {
                "symbol": symbol,
                "arg_order": list(fn_summary.get("arg_order", [])),
                "arg_escape": list(fn_summary.get("arg_escape", [])),
                "return_escape": bool(fn_summary.get("return_escape", False)),
                "return_from_args": list(fn_summary.get("return_from_args", [])),
                "unresolved_calls": int(fn_summary.get("unresolved_calls", 0)),
            }
            if _set_meta_value(fn_node, "escape_summary", fn_payload):
                annotation_changes += 1
            sites = callsites_by_symbol.get(symbol, [])
            s = 0
            while s < len(sites):
                site = sites[s]
                call_node = site.get("call_node")
                if isinstance(call_node, dict):
                    callee = site.get("callee")
                    callee_symbol = callee if isinstance(callee, str) else ""
                    callee_summary = summary.get(callee_symbol, {})
                    resolved = bool(site.get("resolved", False))
                    payload = {
                        "callee": callee_symbol,
                        "resolved": resolved,
                        "in_return_expr": bool(site.get("in_return_expr", False)),
                        "arg_sources": site.get("arg_sources", []),
                        "callee_arg_escape": list(callee_summary.get("arg_escape", [])) if isinstance(callee_summary, dict) else [],
                        "callee_return_from_args": (
                            list(callee_summary.get("return_from_args", []))
                            if isinstance(callee_summary, dict)
                            else []
                        ),
                        "callee_return_escape": bool(callee_summary.get("return_escape", False))
                        if isinstance(callee_summary, dict)
                        else False,
                    }
                    if _set_meta_value(call_node, "non_escape_callsite", payload):
                        annotation_changes += 1
                s += 1
            i += 1
        meta["non_escape_summary"] = out_summary
        module_doc["meta"] = meta
        changed_out = old_summary != out_summary
        changed_flag = changed_out or annotation_changes > 0
        change_count = 0
        if changed_out:
            change_count += len(sorted_symbols)
        change_count += annotation_changes
        return PassResult(changed=changed_flag, change_count=change_count)

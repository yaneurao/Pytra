"""Interprocedural non-escape summary analysis for EAST3."""

from __future__ import annotations

from typing import Any

from toolchain.compile.east3_opt_passes.non_escape_call_graph import collect_non_escape_import_maps
from toolchain.compile.east3_opt_passes.non_escape_call_graph import collect_non_escape_symbols
from toolchain.compile.east3_opt_passes.non_escape_call_graph import module_id_for_doc
from toolchain.compile.east3_opt_passes.non_escape_call_graph import resolve_non_escape_call_target
from toolchain.compile.east3_optimizer import East3OptimizerPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import PassResult


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        text = s.strip()
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
        cd: dict[str, Any] = cur
        kind = cd.get("kind")
        if kind == "Return":
            value_any = cd.get("value")
            if isinstance(value_any, dict):
                _walk(value_any, in_return_expr=True)
            return
        if kind == "Call":
            out.append((cd, in_return_expr))
        for value in cd.values():
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
    nd: dict[str, Any] = node
    if nd.get("kind") == "Name":
        ident = _safe_name(nd.get("id"))
        if ident in arg_index:
            out.add(arg_index[ident])
    for value in nd.values():
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


def _resolve_callee_symbol_alias(
    symbol_ref: str,
    *,
    known_symbols: set[str],
    module_import_symbols_maps: dict[str, dict[str, str]],
) -> tuple[str, bool]:
    cur = _safe_name(symbol_ref)
    if cur == "":
        return "", False
    visited: set[str] = set()
    while cur not in visited:
        if cur in known_symbols:
            return cur, True
        visited.add(cur)
        if "::" not in cur:
            break
        module_id, local_symbol = cur.split("::", 1)
        import_symbols = module_import_symbols_maps.get(module_id, {})
        next_symbol = _safe_name(import_symbols.get(local_symbol))
        if next_symbol == "":
            break
        cur = next_symbol
    return _safe_name(symbol_ref), False


def _collect_non_escape_module_closure(module_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    root_module_id = module_id_for_doc(module_doc)
    root_meta = _ensure_meta(module_doc)
    if _safe_name(root_meta.get("module_id")) == "":
        root_meta["module_id"] = root_module_id
        module_doc["meta"] = root_meta
    out[root_module_id] = module_doc
    meta_any = module_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    closure_any = meta.get("non_escape_import_closure")
    closure = closure_any if isinstance(closure_any, dict) else {}
    for module_id_any, doc_any in closure.items():
        module_id = _safe_name(module_id_any)
        if module_id == "":
            continue
        if not isinstance(doc_any, dict):
            continue
        da: dict[str, Any] = doc_any
        if da.get("kind") != "Module":
            continue
        child_doc = da
        child_meta_any = child_doc.get("meta")
        child_meta = child_meta_any if isinstance(child_meta_any, dict) else {}
        if _safe_name(child_meta.get("module_id")) == "":
            child_meta["module_id"] = module_id
            child_doc["meta"] = child_meta
        if module_id not in out:
            out[module_id] = child_doc
    return out


def _infer_builtin_callee_arg_escape(call_node: dict[str, Any]) -> list[bool]:
    args_any = call_node.get("args")
    args = args_any if isinstance(args_any, list) else []
    arg_count = len(args)
    if arg_count == 0:
        return []
    runtime_call = _safe_name(call_node.get("runtime_call"))
    builtin_name = _safe_name(call_node.get("builtin_name"))
    if runtime_call == "py_len" or runtime_call == "py_to_string" or runtime_call == "py_to_bool" or runtime_call == "py_to_int64" or runtime_call == "py_to_float64":
        return [False] * arg_count
    if builtin_name == "len" or builtin_name == "str" or builtin_name == "bool" or builtin_name == "int" or builtin_name == "float":
        return [False] * arg_count
    func_any = call_node.get("func")
    if isinstance(func_any, dict):
        fad: dict[str, Any] = func_any
        if _safe_name(fad.get("kind")) == "Name":
            fn_name = _safe_name(fad.get("id"))
            if fn_name == "len" or fn_name == "str" or fn_name == "bool" or fn_name == "int" or fn_name == "float":
                return [False] * arg_count
    return []


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
    nd2: dict[str, Any] = node
    if nd2.get("kind") == "Return":
        value_any = nd2.get("value")
        if isinstance(value_any, dict):
            has_return_value = True
            direct_return_count = 1
            refs: set[int] = set()
            _collect_arg_refs(value_any, arg_index, refs)
            for idx in refs:
                out.add(idx)
        return has_return_value, direct_return_count
    for value in nd2.values():
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
            arg_index: dict[str, int] = {}
            for _ai in range(len(arg_order)):
                arg_index[arg_order[_ai]] = _ai

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
            unresolved_site_count = 0
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
                if not resolved:
                    resolved_target, alias_resolved = _resolve_callee_symbol_alias(
                        target,
                        known_symbols=known_symbols,
                        module_import_symbols_maps=module_import_symbols_maps,
                    )
                    if alias_resolved:
                        target = resolved_target
                        resolved = True
                args_any = call_node.get("args")
                args = args_any if isinstance(args_any, list) else []
                arg_sources: list[list[int]] = []
                a = 0
                while a < len(args):
                    refs: set[int] = set()
                    _collect_arg_refs(args[a], arg_index, refs)
                    arg_sources.append(sorted(refs))
                    a += 1

                # If callee has union type parameters, args passed to those positions escape
                # (they get boxed into object).
                if resolved and target in symbols:
                    callee_node = symbols[target]
                    callee_arg_types = callee_node.get("arg_types")
                    if isinstance(callee_arg_types, dict):
                        cat: dict[str, Any] = callee_arg_types
                        callee_arg_order = callee_node.get("arg_order")
                        callee_arg_order = callee_arg_order if isinstance(callee_arg_order, list) else []
                        param_idx = 0
                        while param_idx < len(callee_arg_order):
                            param_name = _safe_name(callee_arg_order[param_idx])
                            param_type = _safe_name(cat.get(param_name))
                            if "|" in param_type:
                                # This parameter is a union type → arg escapes (boxed to object).
                                call_arg_idx = param_idx
                                if call_arg_idx < len(arg_sources):
                                    for ref_idx in arg_sources[call_arg_idx]:
                                        if ref_idx >= 0 and ref_idx < len(direct_arg_escape):
                                            direct_arg_escape[ref_idx] = True
                            param_idx += 1

                if not resolved:
                    unresolved_site_count += 1
                    if bool(context.non_escape_policy.get("unknown_call_escape", True)):
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
            _has_any_ret = False
            for _rfa in ret_from_args:
                if _rfa:
                    _has_any_ret = True
                    break
            ret_escape = bool(has_return_value or _has_any_ret)
            if bool(context.non_escape_policy.get("unknown_call_escape", True)) and unresolved_site_count > 0:
                ret_escape = True
            summary[symbol] = {
                "symbol": symbol,
                "arg_order": list(arg_order),
                "arg_escape": list(direct_arg_escape),
                "return_escape": ret_escape,
                "return_from_args": ret_from_args,
                "unresolved_calls": int(unresolved_site_count),
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
                _has_any_ret2 = False
                for _rfa2 in ret_from_args:
                    if _rfa2:
                        _has_any_ret2 = True
                        break
                if _has_any_ret2 and not ret_escape:
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
        root_module_id = module_id_for_doc(module_doc)
        i = 0
        while i < len(sorted_symbols):
            symbol = sorted_symbols[i]
            fn_summary = summary[symbol]
            out_summary[symbol] = fn_summary
            fn_node = symbols[symbol]
            annotate_symbol = symbol_module_ids.get(symbol, "") == root_module_id
            fn_payload = {
                "symbol": symbol,
                "arg_order": list(fn_summary.get("arg_order", [])),
                "arg_escape": list(fn_summary.get("arg_escape", [])),
                "return_escape": bool(fn_summary.get("return_escape", False)),
                "return_from_args": list(fn_summary.get("return_from_args", [])),
                "unresolved_calls": int(fn_summary.get("unresolved_calls", 0)),
            }
            if annotate_symbol and _set_meta_value(fn_node, "escape_summary", fn_payload):
                annotation_changes += 1
            sites = callsites_by_symbol.get(symbol, [])
            s = 0
            while s < len(sites):
                site = sites[s]
                call_node = site.get("call_node")
                if annotate_symbol and isinstance(call_node, dict):
                    callee = site.get("callee")
                    callee_symbol = callee if isinstance(callee, str) else ""
                    callee_summary = summary.get(callee_symbol, {})
                    resolved = bool(site.get("resolved", False))
                    callee_arg_escape_payload: list[bool] = []
                    if callee_symbol != "" and isinstance(callee_summary, dict):
                        arg_escape_any = callee_summary.get("arg_escape")
                        if isinstance(arg_escape_any, list):
                            for item in arg_escape_any:
                                callee_arg_escape_payload.append(bool(item))
                    elif not resolved:
                        callee_arg_escape_payload = _infer_builtin_callee_arg_escape(call_node)
                    crfa: list[Any] = []
                    cre = False
                    if isinstance(callee_summary, dict):
                        csd: dict[str, Any] = callee_summary
                        crfa = list(csd.get("return_from_args", []))
                        cre = bool(csd.get("return_escape", False))
                    payload: dict[str, Any] = {
                        "callee": callee_symbol,
                        "resolved": resolved,
                        "in_return_expr": bool(site.get("in_return_expr", False)),
                        "arg_sources": site.get("arg_sources", []),
                        "callee_arg_escape": callee_arg_escape_payload,
                        "callee_return_from_args": crfa,
                        "callee_return_escape": cre,
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

"""Post-lowering passes for EAST2 → EAST3.

Consolidated port of all toolchain/compile/east2_to_east3_*_*.py passes.
§5.1: Any/object 禁止 — uses JsonVal throughout.
§5.3: Python 標準モジュール直接 import 禁止。
"""

from __future__ import annotations

from typing import Union

from toolchain2.compile.jv import JsonVal, Node, CompileContext, deep_copy_json
from toolchain2.compile.jv import jv_str, jv_is_dict, jv_is_list
from toolchain2.compile.jv import normalize_type_name

# Re-export stubs — these are imported by lower.py
# Each function mutates the module in place and returns it.

# ===========================================================================
# yield lowering
# ===========================================================================

def _contains_yield(node: JsonVal) -> bool:
    if isinstance(node, dict):
        if node.get("kind") == "Yield":
            return True
        for v in node.values():
            if _contains_yield(v):
                return True
    elif isinstance(node, list):
        for item in node:
            if _contains_yield(item):
                return True
    return False


def _replace_yield_with_append(node: JsonVal, acc: str, list_type: str) -> JsonVal:
    if isinstance(node, list):
        result: list[JsonVal] = []
        for item in node:
            replaced = _replace_yield_with_append(item, acc, list_type)
            if isinstance(replaced, list):
                result.extend(replaced)
            else:
                result.append(replaced)
        return result
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == "Yield":
        value = nd.get("value")
        if value is None:
            value = {"kind": "Constant", "value": None, "resolved_type": "None"}
        ac: Node = {
            "kind": "Expr",
            "value": {
                "kind": "Call",
                "func": {"kind": "Attribute", "value": {"kind": "Name", "id": acc, "resolved_type": list_type}, "attr": "append"},
                "args": [value],
                "resolved_type": "None",
            },
        }
        span = nd.get("source_span")
        if isinstance(span, dict):
            ac["source_span"] = span
        return ac
    out: Node = {}
    for key, val in nd.items():
        if key == "body" or key == "orelse" or key == "finalbody":
            out[key] = _replace_yield_with_append(val, acc, list_type)
        elif key == "handlers" and isinstance(val, list):
            hs: list[JsonVal] = []
            for h in val:
                if isinstance(h, dict):
                    nh = dict(h)
                    if "body" in nh:
                        nh["body"] = _replace_yield_with_append(nh["body"], acc, list_type)
                    hs.append(nh)
                else:
                    hs.append(h)
            out[key] = hs
        else:
            out[key] = val
    return out


def _lower_generator_function(func: Node) -> None:
    body = func.get("body")
    if not isinstance(body, list):
        return
    ret_type = jv_str(func.get("return_type", "")).strip()
    elem_type = "unknown"
    if ret_type.startswith("list[") and ret_type.endswith("]"):
        elem_type = ret_type[5:-1]
    elif ret_type not in ("", "unknown"):
        elem_type = ret_type
        func["return_type"] = "list[" + ret_type + "]"
    acc = "__yield_values"
    lt = "list[" + elem_type + "]"
    init: Node = {
        "kind": "AnnAssign",
        "target": {"kind": "Name", "id": acc, "resolved_type": lt},
        "annotation": lt, "decl_type": lt, "declare": True,
        "value": {"kind": "List", "elements": [], "resolved_type": lt},
    }
    new_body = _replace_yield_with_append(body, acc, lt)
    if not isinstance(new_body, list):
        new_body = body
    ret_stmt: Node = {"kind": "Return", "value": {"kind": "Name", "id": acc, "resolved_type": lt}}
    func["body"] = [init] + new_body + [ret_stmt]


def _yield_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _yield_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == "FunctionDef":
        body = nd.get("body")
        if isinstance(body, list) and _contains_yield(body):
            _lower_generator_function(nd)
        body2 = nd.get("body")
        if isinstance(body2, list):
            for s in body2:
                _yield_walk(s)
        return
    if kind in ("ClassDef", "Module"):
        body = nd.get("body")
        if isinstance(body, list):
            for s in body:
                _yield_walk(s)
        return
    for val in nd.values():
        if isinstance(val, (dict, list)):
            _yield_walk(val)


def lower_yield_generators(module: Node, ctx: CompileContext) -> Node:
    _yield_walk(module)
    return module


# ===========================================================================
# listcomp lowering
# ===========================================================================

def _build_lc_target_plan(target: JsonVal) -> Node:
    if isinstance(target, dict):
        kind = target.get("kind", "")
        if kind == "Name":
            plan: Node = {"kind": "NameTarget", "id": target.get("id", "_")}
            rt = jv_str(target.get("resolved_type", "")).strip()
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
        if kind == "Tuple":
            elements = target.get("elements") or target.get("elts") or []
            eps: list[JsonVal] = []
            if isinstance(elements, list):
                for elem in elements:
                    eps.append(_build_lc_target_plan(elem))
            plan = {"kind": "TupleTarget", "elements": eps}
            rt = jv_str(target.get("resolved_type", "")).strip()
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
    return {"kind": "NameTarget", "id": "_"}


def _expand_lc_to_stmts(lc: Node, result_name: str, annotation_type: str = "") -> list[Node]:
    rt = jv_str(lc.get("resolved_type", "")).strip()
    if rt in ("", "unknown") or "unknown" in rt:
        if annotation_type != "":
            rt = annotation_type
        elif rt in ("", "unknown"):
            rt = "list[unknown]"
    init: Node = {
        "kind": "AnnAssign",
        "target": {"kind": "Name", "id": result_name, "resolved_type": rt},
        "annotation": rt, "decl_type": rt, "declare": True,
        "value": {"kind": "List", "elements": [], "resolved_type": rt},
    }
    elt = lc.get("elt")
    generators = lc.get("generators", [])
    if not isinstance(generators, list):
        generators = []
    append_stmt: Node = {
        "kind": "Expr",
        "value": {
            "kind": "Call",
            "func": {"kind": "Attribute", "value": {"kind": "Name", "id": result_name, "resolved_type": rt}, "attr": "append"},
            "args": [deep_copy_json(elt)] if elt is not None else [],
            "resolved_type": "None",
        },
    }
    body: list[JsonVal] = [append_stmt]
    for gen in reversed(generators):
        if not isinstance(gen, dict):
            continue
        ifs = gen.get("ifs")
        if isinstance(ifs, list) and len(ifs) > 0:
            for cond in reversed(ifs):
                if isinstance(cond, dict):
                    body = [{"kind": "If", "test": deep_copy_json(cond), "body": body, "orelse": []}]
        target = gen.get("target")
        iter_expr = gen.get("iter")
        tp = _build_lc_target_plan(target)
        if isinstance(iter_expr, dict) and iter_expr.get("kind") in ("RangeExpr", "ForRange"):
            fs: Node = {
                "kind": "ForCore", "iter_mode": "static_fastpath",
                "iter_plan": {
                    "kind": "StaticRangeForPlan",
                    "start": deep_copy_json(iter_expr.get("start", {"kind": "Constant", "value": 0, "resolved_type": "int64"})),
                    "stop": deep_copy_json(iter_expr.get("stop", {"kind": "Constant", "value": 0})),
                    "step": deep_copy_json(iter_expr.get("step", {"kind": "Constant", "value": 1, "resolved_type": "int64"})),
                },
                "target_plan": tp, "body": body, "orelse": [],
            }
        else:
            fs = {
                "kind": "ForCore", "iter_mode": "runtime_protocol",
                "iter_plan": {
                    "kind": "RuntimeIterForPlan",
                    "iter_expr": deep_copy_json(iter_expr) if iter_expr else {"kind": "Name", "id": "__empty"},
                    "dispatch_mode": "generic", "init_op": "ObjIterInit", "next_op": "ObjIterNext",
                },
                "target_plan": tp, "body": body, "orelse": [],
            }
        body = [fs]
    return [init] + body


def _lc_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = stmt.get("kind", "")
        if kind in ("Assign", "AnnAssign"):
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "ListComp":
                target = stmt.get("target")
                tn = ""
                if isinstance(target, dict) and target.get("kind") == "Name":
                    tn = jv_str(target.get("id", "")).strip()
                cn = tn if tn != "" else ctx.next_comp_name()
                at = ""
                if kind == "AnnAssign":
                    ann = stmt.get("annotation")
                    if isinstance(ann, str) and ann != "" and "unknown" not in ann:
                        at = ann
                expanded = _expand_lc_to_stmts(value, cn, at)
                if cn != tn and tn != "":
                    expanded.append({
                        "kind": "Assign",
                        "target": deep_copy_json(target),
                        "value": {"kind": "Name", "id": cn, "resolved_type": jv_str(value.get("resolved_type", ""))},
                    })
                result.extend(expanded)
                continue
        if kind == "Expr":
            ev = stmt.get("value")
            if isinstance(ev, dict) and ev.get("kind") == "ListComp":
                tmp = ctx.next_comp_name()
                result.extend(_expand_lc_to_stmts(ev, tmp))
                continue
        # Recurse
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _lc_in_stmts(nested, ctx)
        if kind == "Try":
            hs = stmt.get("handlers")
            if isinstance(hs, list):
                for h in hs:
                    if isinstance(h, dict):
                        hb = h.get("body")
                        if isinstance(hb, list):
                            h["body"] = _lc_in_stmts(hb, ctx)
        result.append(stmt)
    return result


def lower_listcomp(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if isinstance(body, list):
        module["body"] = _lc_in_stmts(body, ctx)
    return module


# ===========================================================================
# default argument expansion
# ===========================================================================

def _collect_fn_sigs(module: Node) -> dict[str, Node]:
    sigs: dict[str, Node] = {}
    body = module.get("body")
    if not isinstance(body, list):
        return sigs
    for stmt in body:
        if isinstance(stmt, dict):
            _collect_sig_node(stmt, sigs, "")
    return sigs


def _collect_sig_node(node: Node, sigs: dict[str, Node], class_name: str) -> None:
    kind = node.get("kind", "")
    if kind == "FunctionDef":
        name = jv_str(node.get("name", ""))
        if name == "":
            return
        ao = node.get("arg_order")
        ad = node.get("arg_defaults")
        if not isinstance(ao, list):
            return
        sig: Node = {"arg_order": ao, "arg_defaults": ad if isinstance(ad, dict) else {}}
        full = class_name + "." + name if class_name != "" else name
        sigs[name] = sig
        if full != name:
            sigs[full] = sig
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, "")
    elif kind == "ClassDef":
        cn = jv_str(node.get("name", ""))
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, cn)


def _expand_defaults_walk(node: JsonVal, sigs: dict[str, Node]) -> None:
    if isinstance(node, list):
        for item in node:
            _expand_defaults_walk(item, sigs)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "Call":
        func = nd.get("func")
        cn = ""
        if isinstance(func, dict):
            if func.get("kind") == "Name":
                cn = jv_str(func.get("id", ""))
            elif func.get("kind") == "Attribute":
                cn = jv_str(func.get("attr", ""))
        if cn != "" and cn in sigs:
            sig = sigs[cn]
            ao = sig.get("arg_order")
            ad = sig.get("arg_defaults")
            args = nd.get("args")
            if isinstance(args, list) and isinstance(ao, list) and isinstance(ad, dict):
                ep = [p for p in ao if isinstance(p, str) and p != "self"]
                ne = len(ep)
                kw_map: dict[str, JsonVal] = {}
                kws = nd.get("keywords")
                if isinstance(kws, list):
                    for kw in kws:
                        if isinstance(kw, dict):
                            ka = jv_str(kw.get("arg", ""))
                            kv = kw.get("value")
                            if ka != "":
                                kw_map[ka] = kv
                if len(args) < ne:
                    for i in range(len(args), ne):
                        pn = ep[i]
                        if pn in kw_map:
                            kv2 = kw_map[pn]
                            args.append(deep_copy_json(kv2) if isinstance(kv2, dict) else kv2)
                        elif pn in ad:
                            dn = ad[pn]
                            if isinstance(dn, dict):
                                args.append(deep_copy_json(dn))
                    if isinstance(kws, list) and len(kw_map) > 0:
                        remaining: list[JsonVal] = []
                        for kw in kws:
                            if isinstance(kw, dict):
                                ka = jv_str(kw.get("arg", ""))
                                if ka in kw_map:
                                    continue
                            remaining.append(kw)
                        nd["keywords"] = remaining
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _expand_defaults_walk(v, sigs)


def expand_default_arguments(module: Node, ctx: CompileContext) -> Node:
    sigs = _collect_fn_sigs(module)
    if sigs:
        _expand_defaults_walk(module, sigs)
    return module


# ===========================================================================
# ForCore TupleTarget expansion (stub — usually already handled by main lowering)
# ===========================================================================

def _tte_subscript(owner: str, index: int, elem_type: str) -> Node:
    return {
        "kind": "Subscript",
        "value": {"kind": "Name", "id": owner, "resolved_type": "tuple"},
        "slice": {"kind": "Constant", "value": index, "resolved_type": "int64"},
        "resolved_type": elem_type if elem_type != "" else "unknown",
    }


def _tte_walk(node: JsonVal, ctx: CompileContext) -> None:
    if isinstance(node, list):
        for item in node:
            _tte_walk(item, ctx)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "ForCore":
        tp = nd.get("target_plan")
        if isinstance(tp, dict) and tp.get("kind") == "TupleTarget":
            elements = tp.get("elements")
            if isinstance(elements, list) and len(elements) >= 2:
                tmp = ctx.next_tte_name()
                assigns: list[JsonVal] = []
                direct_names: list[JsonVal] = []
                for i, elem in enumerate(elements):
                    if not isinstance(elem, dict) or elem.get("kind") != "NameTarget":
                        continue
                    en = elem.get("id", "")
                    et = elem.get("target_type", "")
                    if not isinstance(en, str) or en == "":
                        continue
                    if not isinstance(et, str):
                        et = ""
                    assign: Node = {
                        "kind": "Assign",
                        "target": {"kind": "Name", "id": en, "resolved_type": et if et != "" else "unknown"},
                        "value": _tte_subscript(tmp, i, et),
                        "decl_type": et if et != "" else "unknown",
                        "declare": True,
                    }
                    assigns.append(assign)
                    direct_names.append(en)
                nd["target_plan"] = {
                    "kind": "NameTarget",
                    "id": tmp,
                    "target_type": tp.get("target_type", ""),
                    "direct_unpack_names": direct_names,
                    "tuple_expanded": True,
                }
                body = nd.get("body")
                if isinstance(body, list):
                    nd["body"] = assigns + body
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _tte_walk(v, ctx)


def expand_forcore_tuple_targets(module: Node, ctx: CompileContext) -> Node:
    _tte_walk(module, ctx)
    return module


# ===========================================================================
# enumerate lowering
# ===========================================================================

def _try_lower_enum_forcore(stmt: Node, ctx: CompileContext) -> list[Node] | None:
    ip = stmt.get("iter_plan")
    if not isinstance(ip, dict) or ip.get("kind") != "RuntimeIterForPlan":
        return None
    ie = ip.get("iter_expr")
    if not isinstance(ie, dict):
        return None
    st = jv_str(ie.get("semantic_tag", "")).strip()
    is_enum = st == "iter.enumerate"
    if not is_enum:
        func = ie.get("func")
        if isinstance(func, dict):
            is_enum = func.get("id") == "enumerate" or func.get("attr") == "enumerate"
    if not is_enum:
        return None
    args = ie.get("args", [])
    if not isinstance(args, list) or len(args) < 1:
        return None
    iterable = args[0]
    start_val = 0
    if len(args) >= 2:
        sa = args[1]
        if isinstance(sa, dict) and sa.get("kind") == "Constant":
            sv = sa.get("value")
            if isinstance(sv, int):
                start_val = sv
    tp = stmt.get("target_plan", {})
    if not isinstance(tp, dict):
        return None
    body = stmt.get("body", [])
    if not isinstance(body, list):
        return None
    idx_name = ""
    val_name = ""
    remaining: list[JsonVal] = []
    iter_tmp = jv_str(tp.get("id", "")).strip()
    for s in body:
        if not isinstance(s, dict):
            remaining.append(s)
            continue
        if s.get("kind") == "Assign":
            target = s.get("target")
            value = s.get("value")
            if isinstance(target, dict) and isinstance(value, dict) and value.get("kind") == "Subscript":
                sl = value.get("slice", {})
                if isinstance(sl, dict) and sl.get("kind") == "Constant":
                    idx_v = sl.get("value")
                    owner = value.get("value", {})
                    if isinstance(owner, dict) and jv_str(owner.get("id", "")).strip() == iter_tmp:
                        name = jv_str(target.get("id", "")).strip()
                        if idx_v == 0 and name != "":
                            idx_name = name
                            continue
                        elif idx_v == 1 and name != "":
                            val_name = name
                            continue
        remaining.append(s)
    if idx_name == "" or val_name == "":
        return None
    counter = ctx.next_enum_name()
    init: Node = {
        "kind": "Assign",
        "target": {"kind": "Name", "id": counter, "resolved_type": "int64"},
        "value": {"kind": "Constant", "value": start_val, "resolved_type": "int64"},
        "decl_type": "int64", "declare": True,
    }
    raw_tt = jv_str(tp.get("target_type", "")).strip()
    vtt = raw_tt
    if raw_tt.startswith("tuple[") and raw_tt.endswith("]"):
        inner = raw_tt[6:-1]
        parts = _split_comma_types(inner)
        if len(parts) >= 2:
            vtt = parts[1]
    ntp: Node = {"kind": "NameTarget", "id": val_name, "target_type": vtt}
    nip: Node = {
        "kind": "RuntimeIterForPlan",
        "iter_expr": deep_copy_json(iterable),
        "dispatch_mode": ip.get("dispatch_mode", "native"),
        "init_op": "ObjIterInit", "next_op": "ObjIterNext",
    }
    assign_idx: Node = {
        "kind": "Assign",
        "target": {"kind": "Name", "id": idx_name, "resolved_type": "int64"},
        "value": {"kind": "Name", "id": counter, "resolved_type": "int64"},
        "decl_type": "int64", "declare": True,
    }
    increment: Node = {
        "kind": "AugAssign",
        "target": {"kind": "Name", "id": counter, "resolved_type": "int64"},
        "op": "Add",
        "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
    }
    nb = [assign_idx] + remaining + [increment]
    nf: Node = {
        "kind": "ForCore", "iter_mode": stmt.get("iter_mode", "runtime_protocol"),
        "iter_plan": nip, "target_plan": ntp,
        "body": nb, "orelse": stmt.get("orelse", []),
    }
    return [init, nf]


def _enum_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = stmt.get("kind", "")
        if kind == "ForCore":
            expanded = _try_lower_enum_forcore(stmt, ctx)
            if expanded is not None:
                result.extend(expanded)
                continue
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _enum_in_stmts(nested, ctx)
        result.append(stmt)
    return result


def lower_enumerate(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if isinstance(body, list):
        module["body"] = _enum_in_stmts(body, ctx)
    return module


# ===========================================================================
# block scope hoist — full port of east2_to_east3_block_scope_hoist.py
# ===========================================================================

def _sk(node: JsonVal) -> str:
    if isinstance(node, dict):
        k = node.get("kind")
        if isinstance(k, str):
            return k
    return ""


def _split_comma_types(tn: str) -> list[str]:
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in tn:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            p = cur.strip()
            if p != "":
                parts.append(p)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _resolve_atype(stmt: Node) -> str:
    dt = stmt.get("decl_type")
    if isinstance(dt, str) and dt.strip() not in ("", "unknown"):
        return dt.strip()
    ann = stmt.get("annotation")
    if isinstance(ann, str) and ann.strip() not in ("", "unknown"):
        return ann.strip()
    target = stmt.get("target")
    if isinstance(target, dict):
        rt = target.get("resolved_type")
        if isinstance(rt, str) and rt.strip() not in ("", "unknown"):
            return rt.strip()
    return ""


def _collect_assign_names(stmt: Node, out: dict[str, str]) -> None:
    target = stmt.get("target")
    if isinstance(target, dict):
        tk = target.get("kind")
        if tk == "Name":
            n = target.get("id")
            if isinstance(n, str) and n != "" and n not in out:
                out[n] = _resolve_atype(stmt)
        elif tk == "Tuple":
            _collect_tuple_tgt_names(target, stmt, out)
    targets = stmt.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict):
                if t.get("kind") == "Name":
                    n = t.get("id")
                    if isinstance(n, str) and n != "" and n not in out:
                        out[n] = _resolve_atype(stmt)
                elif t.get("kind") == "Tuple":
                    _collect_tuple_tgt_names(t, stmt, out)


def _collect_tuple_tgt_names(tn: Node, stmt: Node, out: dict[str, str]) -> None:
    elements = tn.get("elements")
    if not isinstance(elements, list):
        return
    vt = _resolve_atype(stmt)
    ets: list[str] = []
    if vt.startswith("tuple[") and vt.endswith("]"):
        ets = _split_comma_types(vt[6:-1])
    for i, elem in enumerate(elements):
        if not isinstance(elem, dict) or elem.get("kind") != "Name":
            continue
        n = elem.get("id")
        if not isinstance(n, str) or n == "":
            continue
        et = ""
        if i < len(ets):
            et = ets[i]
        if et == "":
            rt = elem.get("resolved_type")
            if isinstance(rt, str):
                et = rt
        if n not in out:
            out[n] = et


def _collect_assigned_in_stmts(stmts: list[JsonVal]) -> dict[str, str]:
    out: dict[str, str] = {}
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _sk(stmt)
        if kind in ("Assign", "AnnAssign"):
            _collect_assign_names(stmt, out)
        elif kind == "If":
            for key in ("body", "orelse"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    sub = _collect_assigned_in_stmts(nested)
                    for n, t in sub.items():
                        if n not in out:
                            out[n] = t
                        elif out[n] == "" and t != "":
                            out[n] = t
        elif kind in ("While", "For", "ForRange", "ForCore"):
            if kind == "ForCore":
                tp = stmt.get("target_plan")
                if isinstance(tp, dict):
                    tpk = tp.get("kind")
                    if tpk == "NameTarget":
                        tpn = tp.get("id")
                        tpt = tp.get("target_type", "")
                        if isinstance(tpn, str) and tpn != "" and tpn not in out:
                            out[tpn] = tpt if isinstance(tpt, str) else ""
                    elif tpk == "TupleTarget":
                        elems = tp.get("elements")
                        if isinstance(elems, list):
                            for e in elems:
                                if isinstance(e, dict) and e.get("kind") == "NameTarget":
                                    en = e.get("id")
                                    et2 = e.get("target_type", "")
                                    if isinstance(en, str) and en != "" and en not in out:
                                        out[en] = et2 if isinstance(et2, str) else ""
            for key in ("body", "orelse"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    sub = _collect_assigned_in_stmts(nested)
                    for n, t in sub.items():
                        if n not in out:
                            out[n] = t
                        elif out[n] == "" and t != "":
                            out[n] = t
    return out


def _collect_refs(node: JsonVal, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_refs(item, out)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "Name":
        n = nd.get("id")
        if isinstance(n, str) and n != "":
            out.add(n)
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _collect_refs(v, out)


def _collect_tuple_names_flat(tn: Node, out: set[str]) -> None:
    elements = tn.get("elements")
    if not isinstance(elements, list):
        return
    for elem in elements:
        if isinstance(elem, dict) and elem.get("kind") == "Name":
            n = elem.get("id")
            if isinstance(n, str) and n != "":
                out.add(n)


def _mark_reassign(stmts: list[JsonVal], hoisted: set[str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _sk(stmt)
        if kind in ("Assign", "AnnAssign"):
            target = stmt.get("target")
            if isinstance(target, dict):
                if target.get("kind") == "Name":
                    n = target.get("id")
                    if isinstance(n, str) and n in hoisted:
                        stmt["is_reassign"] = True
                elif target.get("kind") == "Tuple":
                    elements = target.get("elements")
                    if isinstance(elements, list):
                        for elem in elements:
                            if isinstance(elem, dict) and elem.get("kind") == "Name":
                                en = elem.get("id")
                                if isinstance(en, str) and en in hoisted:
                                    stmt["is_reassign"] = True
                                    break
        if kind in ("If", "While", "For", "ForRange", "ForCore"):
            for key in ("body", "orelse"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    _mark_reassign(nested, hoisted)


def _collect_multi_branch(if_stmt: Node) -> set[str]:
    branches: list[set[str]] = []
    def _walk_chain(node: Node) -> None:
        body = node.get("body")
        orelse = node.get("orelse")
        if isinstance(body, list):
            bn: set[str] = set()
            ba = _collect_assigned_in_stmts(body)
            for n in ba:
                bn.add(n)
            branches.append(bn)
        if isinstance(orelse, list) and len(orelse) == 1:
            nested = orelse[0]
            if isinstance(nested, dict) and _sk(nested) == "If":
                _walk_chain(nested)
                return
        if isinstance(orelse, list) and len(orelse) > 0:
            bn2: set[str] = set()
            oa = _collect_assigned_in_stmts(orelse)
            for n in oa:
                bn2.add(n)
            branches.append(bn2)
    _walk_chain(if_stmt)
    if len(branches) < 2:
        return set()
    count: dict[str, int] = {}
    for br in branches:
        for n in br:
            count[n] = count.get(n, 0) + 1
    return {n for n, c in count.items() if c >= 2}


def _hoist_in_stmt_list(stmts: list[JsonVal], param_names: set[str]) -> list[JsonVal]:
    result: list[JsonVal] = []
    already: set[str] = set(param_names)
    for i in range(len(stmts)):
        stmt = stmts[i]
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = _sk(stmt)
        if kind in ("Assign", "AnnAssign"):
            target = stmt.get("target")
            if isinstance(target, dict):
                if target.get("kind") == "Name":
                    n = target.get("id")
                    if isinstance(n, str) and n != "":
                        already.add(n)
                elif target.get("kind") == "Tuple":
                    _collect_tuple_names_flat(target, already)
            targets = stmt.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict):
                        if t.get("kind") == "Name":
                            n = t.get("id")
                            if isinstance(n, str) and n != "":
                                already.add(n)
                        elif t.get("kind") == "Tuple":
                            _collect_tuple_names_flat(t, already)
            result.append(stmt)
            continue
        if kind == "VarDecl":
            n = stmt.get("name")
            if isinstance(n, str) and n != "":
                already.add(n)
            result.append(stmt)
            continue
        if kind not in ("If", "While", "For", "ForRange", "ForCore"):
            result.append(stmt)
            continue
        # Block-creating statement
        ba2 = _collect_block_assigned(stmt)
        names_after: set[str] = set()
        for j in range(i + 1, len(stmts)):
            _collect_refs(stmts[j], names_after)
        multi_branch: set[str] = set()
        if kind == "If":
            multi_branch = _collect_multi_branch(stmt)
        to_hoist: dict[str, str] = {}
        for n, vt in ba2.items():
            if n in already:
                continue
            if n not in names_after and n not in multi_branch:
                continue
            to_hoist[n] = vt
        for n in sorted(to_hoist.keys()):
            if n is None or n == "":
                continue
            vd: Node = {"kind": "VarDecl", "name": n, "type": to_hoist[n] if to_hoist[n] != "" else "unknown", "hoisted": True}
            result.append(vd)
            already.add(n)
        if to_hoist:
            hs = set(to_hoist.keys())
            _mark_reassign_block(stmt, hs)
        _recurse_hoist(stmt, already)
        result.append(stmt)
    return result


def _collect_block_assigned(stmt: Node) -> dict[str, str]:
    kind = _sk(stmt)
    all_names: dict[str, str] = {}
    if kind == "If":
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                sub = _collect_assigned_in_stmts(nested)
                for n, t in sub.items():
                    if n not in all_names:
                        all_names[n] = t
                    elif all_names[n] == "" and t != "":
                        all_names[n] = t
    elif kind in ("While", "For", "ForRange", "ForCore"):
        if kind == "ForCore":
            tp = stmt.get("target_plan")
            if isinstance(tp, dict):
                tpk = tp.get("kind")
                if tpk == "NameTarget":
                    tpn = tp.get("id")
                    tpt = tp.get("target_type", "")
                    if isinstance(tpn, str) and tpn != "" and tpn not in all_names:
                        all_names[tpn] = tpt if isinstance(tpt, str) else ""
                elif tpk == "TupleTarget":
                    elems = tp.get("elements")
                    if isinstance(elems, list):
                        for e in elems:
                            if isinstance(e, dict) and e.get("kind") == "NameTarget":
                                en = e.get("id")
                                et2 = e.get("target_type", "")
                                if isinstance(en, str) and en != "" and en not in all_names:
                                    all_names[en] = et2 if isinstance(et2, str) else ""
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                sub = _collect_assigned_in_stmts(nested)
                for n, t in sub.items():
                    if n not in all_names:
                        all_names[n] = t
                    elif all_names[n] == "" and t != "":
                        all_names[n] = t
    return all_names


def _mark_reassign_block(stmt: Node, hoisted: set[str]) -> None:
    kind = _sk(stmt)
    for key in ("body", "orelse"):
        nested = stmt.get(key)
        if isinstance(nested, list):
            _mark_reassign(nested, hoisted)


def _recurse_hoist(stmt: Node, parent: set[str]) -> None:
    for key in ("body", "orelse"):
        nested = stmt.get(key)
        if isinstance(nested, list):
            stmt[key] = _hoist_in_stmt_list(nested, parent)


def _fn_param_names(func: Node) -> set[str]:
    params: set[str] = set()
    ao = func.get("arg_order")
    if isinstance(ao, list):
        for arg in ao:
            if isinstance(arg, str) and arg != "":
                params.add(arg)
    args = func.get("args")
    if isinstance(args, list):
        for arg in args:
            if isinstance(arg, dict):
                n = arg.get("arg")
                if isinstance(n, str) and n != "":
                    params.add(n)
    return params


def _hoist_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _hoist_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = _sk(nd)
    if kind == "FunctionDef":
        body = nd.get("body")
        if isinstance(body, list):
            nd["body"] = _hoist_in_stmt_list(body, _fn_param_names(nd))
            for s in nd["body"]:
                _hoist_walk(s)
        return
    if kind in ("ClassDef", "Module"):
        body = nd.get("body")
        if isinstance(body, list):
            for s in body:
                _hoist_walk(s)
        return
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _hoist_walk(v)


def hoist_block_scope_variables(module: Node, ctx: CompileContext) -> Node:
    _hoist_walk(module)
    return module


# ===========================================================================
# integer promotion
# ===========================================================================

_SMALL_INTS: set[str] = {"int8", "uint8", "int16", "uint16"}
_ARITH_OPS: set[str] = {"Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow", "LShift", "RShift", "BitOr", "BitXor", "BitAnd"}
_UNARY_OPS: set[str] = {"UAdd", "USub", "Invert"}
_INT_WIDTH: dict[str, int] = {"int8": 8, "uint8": 8, "int16": 16, "uint16": 16, "int32": 32, "uint32": 32, "int64": 64, "uint64": 64}


def _nt(t: JsonVal) -> str:
    if isinstance(t, str):
        return t.strip()
    return ""


def _promoted(t: str) -> str:
    if t in _SMALL_INTS:
        return "int32"
    return t


def _promote_result(lt: str, rt: str) -> str:
    l2 = _nt(lt)
    r2 = _nt(rt)
    fts = {"float32", "float64"}
    if l2 in fts or r2 in fts:
        if l2 in fts and r2 in fts:
            return "float64" if l2 == "float64" or r2 == "float64" else "float32"
        return l2 if l2 in fts else r2
    if l2 == "" or l2 == "unknown" or r2 == "" or r2 == "unknown":
        return ""
    lp = _promoted(l2)
    rp = _promoted(r2)
    rank = {"int32": 0, "uint32": 1, "int64": 2, "uint64": 3}
    lr = rank.get(lp, -1)
    rr = rank.get(rp, -1)
    if lr < 0 and rr < 0:
        return ""
    return lp if lr >= rr else rp


def _int_promo_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _int_promo_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind")
    if kind == "BinOp":
        op = nd.get("op", "")
        if op in _ARITH_OPS:
            left = nd.get("left")
            right = nd.get("right")
            lt2 = _nt(left.get("resolved_type")) if isinstance(left, dict) else ""
            rt2 = _nt(right.get("resolved_type")) if isinstance(right, dict) else ""
            promoted = _promote_result(lt2, rt2)
            if promoted != "":
                if isinstance(left, dict) and lt2 in _SMALL_INTS:
                    left["resolved_type"] = promoted
                if isinstance(right, dict) and rt2 in _SMALL_INTS:
                    right["resolved_type"] = promoted
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = promoted
    if kind == "UnaryOp":
        op = nd.get("op", "")
        if op in _UNARY_OPS:
            operand = nd.get("operand")
            ot = _nt(operand.get("resolved_type")) if isinstance(operand, dict) else ""
            if ot in _SMALL_INTS and isinstance(operand, dict):
                tgt = _promoted(ot)
                operand["resolved_type"] = tgt
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = tgt
    if kind == "ForCore":
        tp = nd.get("target_plan")
        if isinstance(tp, dict):
            tt = _nt(tp.get("target_type"))
            if tt == "uint8":
                tp["target_type"] = "int32"
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _int_promo_walk(v)


def _narrowing_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _narrowing_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind")
    if kind in ("Assign", "AnnAssign"):
        target = nd.get("target")
        value = nd.get("value")
        if isinstance(target, dict) and isinstance(value, dict):
            tt = _nt(nd.get("decl_type"))
            if tt == "" or tt == "unknown":
                tt = _nt(nd.get("annotation"))
            if tt == "" or tt == "unknown":
                tt = _nt(target.get("resolved_type"))
            if tt in _INT_WIDTH:
                _narrow_value(value, tt)
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _narrowing_walk(v)


def _narrow_value(vn: Node, tt: str) -> None:
    kind = vn.get("kind")
    rt = _nt(vn.get("resolved_type"))
    tw = _INT_WIDTH.get(tt, 0)
    if tw <= 0 or tt not in _INT_WIDTH:
        return
    rw = _INT_WIDTH.get(rt, 0)
    if rw <= 0 or tw >= rw:
        return
    if kind == "BinOp":
        left = vn.get("left")
        right = vn.get("right")
        lt2 = _nt(left.get("resolved_type")) if isinstance(left, dict) else ""
        rt2 = _nt(right.get("resolved_type")) if isinstance(right, dict) else ""
        lw = _INT_WIDTH.get(lt2, 0) if lt2 in _INT_WIDTH else 0
        rw2 = _INT_WIDTH.get(rt2, 0) if rt2 in _INT_WIDTH else 0
        if lw > 0 and rw2 > 0 and tw >= lw and tw >= rw2:
            vn["resolved_type"] = tt
    elif kind == "UnaryOp":
        operand = vn.get("operand")
        ot = _nt(operand.get("resolved_type")) if isinstance(operand, dict) else ""
        ow = _INT_WIDTH.get(ot, 0) if ot in _INT_WIDTH else 0
        if ow > 0 and tw >= ow:
            vn["resolved_type"] = tt


def _remove_redundant_unbox(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _remove_redundant_unbox(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind")
    if kind in ("Assign", "AnnAssign"):
        value = nd.get("value")
        if isinstance(value, dict) and value.get("kind") == "Unbox":
            inner = value.get("value")
            if isinstance(inner, dict):
                ut = _nt(value.get("target"))
                it = _nt(inner.get("resolved_type"))
                if ut != "" and ut == it:
                    nd["value"] = inner
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _remove_redundant_unbox(v)


def apply_integer_promotion(module: Node, ctx: CompileContext) -> Node:
    _int_promo_walk(module)
    _narrowing_walk(module)
    _remove_redundant_unbox(module)
    return module


# ===========================================================================
# type propagation
# ===========================================================================

def _tp_safe(v: JsonVal) -> str:
    if isinstance(v, str):
        return v.strip()
    return ""


def _tp_assign_target(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _tp_assign_target(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == "FunctionDef":
        rt = _tp_safe(nd.get("return_type"))
        returns = nd.get("returns")
        if returns is None and rt not in ("", "unknown"):
            nd["returns"] = rt
    if kind in ("Assign", "AnnAssign"):
        target = nd.get("target")
        value = nd.get("value")
        if isinstance(target, dict):
            tt = _tp_safe(target.get("resolved_type"))
            if tt in ("", "unknown"):
                inf = _tp_safe(nd.get("decl_type"))
                if inf in ("", "unknown"):
                    inf = _tp_safe(nd.get("annotation"))
                if inf in ("", "unknown") and isinstance(value, dict):
                    inf = _tp_safe(value.get("resolved_type"))
                if inf not in ("", "unknown"):
                    target["resolved_type"] = inf
                    if _tp_safe(nd.get("decl_type")) in ("", "unknown"):
                        nd["decl_type"] = inf
            if isinstance(value, dict):
                vt = _tp_safe(value.get("resolved_type"))
                dt = _tp_safe(nd.get("decl_type"))
                if dt not in ("", "unknown") and "unknown" in vt:
                    vk = value.get("kind", "")
                    if vk in ("List", "Dict", "Set"):
                        value["resolved_type"] = dt
            if target.get("kind") == "Tuple" and isinstance(value, dict):
                _tp_tuple_targets(target, value)
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _tp_assign_target(v)


def _tp_tuple_targets(target: Node, value: Node) -> None:
    vt = _tp_safe(value.get("resolved_type"))
    if not (vt.startswith("tuple[") and vt.endswith("]")):
        return
    inner = vt[6:-1]
    ets = _split_comma_types(inner)
    elements = target.get("elements")
    if not isinstance(elements, list):
        return
    for i, elem in enumerate(elements):
        if not isinstance(elem, dict) or i >= len(ets):
            continue
        et = _tp_safe(elem.get("resolved_type"))
        if et in ("", "unknown"):
            elem["resolved_type"] = ets[i].strip()


def _tp_binop(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _tp_binop(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _tp_binop(v)
    if nd.get("kind") == "BinOp":
        rt = _tp_safe(nd.get("resolved_type"))
        if rt not in ("", "unknown"):
            return
        left = nd.get("left")
        right = nd.get("right")
        lt2 = _tp_safe(left.get("resolved_type")) if isinstance(left, dict) else ""
        rt2 = _tp_safe(right.get("resolved_type")) if isinstance(right, dict) else ""
        if lt2 in ("", "unknown") and rt2 in ("", "unknown"):
            return
        fts = {"float32", "float64"}
        its = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        if lt2 in fts or rt2 in fts:
            nd["resolved_type"] = "float64"
        elif lt2 in its and rt2 in its:
            nd["resolved_type"] = "int64"
        elif lt2 == "str" or rt2 == "str":
            if nd.get("op", "") == "Add":
                nd["resolved_type"] = "str"
        elif lt2 not in ("", "unknown"):
            nd["resolved_type"] = lt2
        elif rt2 not in ("", "unknown"):
            nd["resolved_type"] = rt2
    if nd.get("kind") == "Compare":
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            nd["resolved_type"] = "bool"
    if nd.get("kind") == "Subscript":
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            value = nd.get("value")
            if isinstance(value, dict):
                vt = _tp_safe(value.get("resolved_type"))
                if vt == "str":
                    nd["resolved_type"] = "str"
                elif vt in ("bytes", "bytearray"):
                    nd["resolved_type"] = "int32"
                elif vt.startswith("list[") and vt.endswith("]"):
                    nd["resolved_type"] = vt[5:-1].strip()
                elif vt.startswith("dict[") and vt.endswith("]"):
                    parts = _split_comma_types(vt[5:-1])
                    if len(parts) >= 2:
                        nd["resolved_type"] = parts[1].strip()
    if nd.get("kind") == "UnaryOp":
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            operand = nd.get("operand")
            if isinstance(operand, dict):
                ot = _tp_safe(operand.get("resolved_type"))
                if ot == "bool" and nd.get("op") == "Not":
                    nd["resolved_type"] = "bool"
                elif ot not in ("", "unknown"):
                    nd["resolved_type"] = ot


def _tp_truediv(node: JsonVal) -> None:
    if isinstance(node, list):
        for i in range(len(node)):
            r = _try_truediv(node[i])
            if r is not None:
                node[i] = r
            _tp_truediv(node[i])
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    for key in list(nd.keys()):
        val = nd[key]
        if isinstance(val, dict):
            r = _try_truediv(val)
            if r is not None:
                nd[key] = r
            else:
                _tp_truediv(val)
        elif isinstance(val, list):
            _tp_truediv(val)


def _try_truediv(node: JsonVal) -> Node | None:
    if not isinstance(node, dict):
        return None
    if node.get("kind") != "BinOp" or node.get("op") != "Div":
        return None
    left = node.get("left")
    if not isinstance(left, dict):
        return None
    lt = _tp_safe(left.get("resolved_type"))
    if lt != "Path":
        return None
    right = node.get("right")
    call: Node = {
        "kind": "Call",
        "func": {"kind": "Attribute", "value": left, "attr": "joinpath", "resolved_type": "Path"},
        "args": [right] if right is not None else [],
        "keywords": [],
        "resolved_type": "Path",
    }
    span = node.get("source_span")
    if isinstance(span, dict):
        call["source_span"] = span
    return call


def _collect_fn_callable_types(module: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    renamed: dict[str, str] = {}
    rs = module.get("renamed_symbols")
    if isinstance(rs, dict):
        for orig, rn in rs.items():
            if isinstance(orig, str) and isinstance(rn, str):
                renamed[rn] = orig
    body = module.get("body")
    if not isinstance(body, list):
        return out
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind == "FunctionDef":
            name = _tp_safe(stmt.get("name"))
            ret = _tp_safe(stmt.get("return_type"))
            if name != "" and ret not in ("", "unknown"):
                ao = stmt.get("arg_order")
                at = stmt.get("arg_types")
                if isinstance(ao, list) and isinstance(at, dict):
                    params = [p for p in ao if isinstance(p, str) and p != "self"]
                    pts = [_tp_safe(at.get(p)) for p in params]
                    ct = "callable[[" + ",".join(pts) + "]," + ret + "]"
                else:
                    ct = "callable[[],"+ret+"]"
                out[name] = ct
                if name in renamed:
                    out[renamed[name]] = ct
        elif kind == "ClassDef":
            cb = stmt.get("body")
            if isinstance(cb, list):
                for m in cb:
                    if isinstance(m, dict) and m.get("kind") == "FunctionDef":
                        mn = _tp_safe(m.get("name"))
                        if mn != "":
                            ret = _tp_safe(m.get("return_type"))
                            if ret not in ("", "unknown"):
                                out[mn] = "callable"
    return out


def _tp_fn_refs(node: JsonVal, ft: dict[str, str]) -> None:
    if isinstance(node, list):
        for item in node:
            _tp_fn_refs(item, ft)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "Call":
        args = nd.get("args")
        if isinstance(args, list):
            for arg in args:
                if isinstance(arg, dict) and arg.get("kind") == "Name":
                    n = _tp_safe(arg.get("id"))
                    if n in ft:
                        cur = _tp_safe(arg.get("resolved_type"))
                        if cur in ("", "unknown"):
                            arg["resolved_type"] = ft[n]
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _tp_fn_refs(v, ft)


_FLOAT_TAGS: set[str] = {
    "stdlib.method.sqrt", "stdlib.method.sin", "stdlib.method.cos",
    "stdlib.method.tan", "stdlib.method.exp", "stdlib.method.log",
    "stdlib.method.log10", "stdlib.method.fabs", "stdlib.method.floor",
    "stdlib.method.ceil", "stdlib.method.pow",
}
_INT_TYPES: set[str] = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}


def _tp_numeric_casts(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _tp_numeric_casts(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "Call":
        cr = _tp_safe(nd.get("resolved_type"))
        is_float = cr == "float64"
        if not is_float:
            st = _tp_safe(nd.get("semantic_tag"))
            is_float = st in _FLOAT_TAGS
        if is_float:
            args = nd.get("args")
            if isinstance(args, list):
                for arg in args:
                    if isinstance(arg, dict):
                        at = _tp_safe(arg.get("resolved_type"))
                        if at in _INT_TYPES:
                            ec = arg.get("casts")
                            if not isinstance(ec, list):
                                ec = []
                            ec.append({"on": "body", "from": at, "to": "float64", "reason": "numeric_promotion"})
                            arg["casts"] = ec
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _tp_numeric_casts(v)


def apply_type_propagation(module: Node, ctx: CompileContext) -> Node:
    _tp_binop(module)
    _tp_truediv(module)
    _tp_assign_target(module)
    ft = _collect_fn_callable_types(module)
    if ft:
        _tp_fn_refs(module, ft)
    _tp_numeric_casts(module)
    return module


# ===========================================================================
# yields_dynamic
# ===========================================================================

def _yd_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _yd_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == "IfExp":
        nd["yields_dynamic"] = True
    if kind == "Call":
        func = nd.get("func")
        if isinstance(func, dict):
            fk = func.get("kind", "")
            if fk == "Name":
                cn = func.get("id", "")
                if cn == "min" or cn == "max":
                    nd["yields_dynamic"] = True
            if fk == "Attribute":
                attr = func.get("attr", "")
                if attr == "get":
                    owner = func.get("value")
                    if isinstance(owner, dict):
                        ot = jv_str(owner.get("resolved_type", ""))
                        if ot.startswith("dict["):
                            nd["yields_dynamic"] = True
    for v in nd.values():
        if isinstance(v, dict):
            _yd_walk(v)
        elif isinstance(v, list):
            _yd_walk(v)


def apply_yields_dynamic(module: Node, ctx: CompileContext) -> None:
    _yd_walk(module)


# ===========================================================================
# swap detection
# ===========================================================================

def _expr_key(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    kind = node.get("kind", "")
    if kind == "Name":
        return "Name:" + jv_str(node.get("id", ""))
    if kind == "Subscript":
        val = _expr_key(node.get("value"))
        slc = _expr_key(node.get("slice"))
        return "Sub:" + val + "[" + slc + "]"
    if kind == "Constant":
        return "Const:" + str(node.get("value", ""))
    if kind == "BinOp":
        l2 = _expr_key(node.get("left"))
        r2 = _expr_key(node.get("right"))
        return "BinOp:" + l2 + jv_str(node.get("op", "")) + r2
    return ""


def _swap_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = stmt.get("kind", "")
        if kind == "Assign":
            target = stmt.get("target")
            value = stmt.get("value")
            if isinstance(target, dict) and target.get("kind") == "Tuple" and isinstance(value, dict) and value.get("kind") == "Tuple":
                te = target.get("elements", target.get("elts", []))
                ve = value.get("elements", value.get("elts", []))
                if isinstance(te, list) and isinstance(ve, list) and len(te) == 2 and len(ve) == 2:
                    t0 = _expr_key(te[0])
                    t1 = _expr_key(te[1])
                    v0 = _expr_key(ve[0])
                    v1 = _expr_key(ve[1])
                    if t0 != "" and t1 != "" and t0 == v1 and t1 == v0:
                        span = stmt.get("source_span")
                        if isinstance(te[0], dict) and te[0].get("kind") == "Name" and isinstance(te[1], dict) and te[1].get("kind") == "Name":
                            swap: Node = {"kind": "Swap", "left": te[0], "right": te[1], "lhs": te[0], "rhs": te[1]}
                            if isinstance(span, dict):
                                swap["source_span"] = span
                            result.append(swap)
                            continue
                        # Subscript swap expansion
                        tmp = ctx.next_swap_name()
                        bs: Node = span if isinstance(span, dict) else {}
                        tt: Node = {"kind": "Name", "id": tmp}
                        if bs:
                            tt["source_span"] = bs
                        a1: Node = {"kind": "Assign", "target": tt, "value": te[0], "declare": True}
                        if bs:
                            a1["source_span"] = bs
                        a2: Node = {"kind": "Assign", "target": te[0], "value": te[1]}
                        if bs:
                            a2["source_span"] = bs
                        tr: Node = {"kind": "Name", "id": tmp}
                        if bs:
                            tr["source_span"] = bs
                        a3: Node = {"kind": "Assign", "target": te[1], "value": tr}
                        if bs:
                            a3["source_span"] = bs
                        result.extend([a1, a2, a3])
                        continue
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _swap_in_stmts(nested, ctx)
        if kind == "FunctionDef" or kind == "ClassDef":
            body = stmt.get("body")
            if isinstance(body, list):
                stmt["body"] = _swap_in_stmts(body, ctx)
        elif kind == "Try":
            for key in ("body", "orelse", "finalbody"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    stmt[key] = _swap_in_stmts(nested, ctx)
            hs = stmt.get("handlers")
            if isinstance(hs, list):
                for h in hs:
                    if isinstance(h, dict):
                        hb = h.get("body")
                        if isinstance(hb, list):
                            h["body"] = _swap_in_stmts(hb, ctx)
        result.append(stmt)
    return result


def detect_swap_patterns(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if isinstance(body, list):
        module["body"] = _swap_in_stmts(body, ctx)
    return module


# ===========================================================================
# mutates_self detection
# ===========================================================================

def _is_self_attr(node: Node) -> bool:
    if node.get("kind") != "Attribute":
        return False
    value = node.get("value")
    return isinstance(value, dict) and value.get("kind") == "Name" and value.get("id") == "self"


def _node_mutates(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = node.get("kind", "")
    if kind in ("Assign", "AnnAssign", "AugAssign"):
        target = node.get("target")
        if isinstance(target, dict):
            if _is_self_attr(target):
                return True
            if target.get("kind") == "Subscript":
                val = target.get("value")
                if isinstance(val, dict) and _is_self_attr(val):
                    return True
    if kind == "Expr":
        value = node.get("value")
        if isinstance(value, dict) and value.get("kind") == "Call":
            func = value.get("func")
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                owner = func.get("value")
                if isinstance(owner, dict) and _is_self_attr(owner):
                    return True
    for key in ("body", "orelse", "finalbody"):
        nested = node.get(key)
        if isinstance(nested, list):
            for item in nested:
                if _node_mutates(item):
                    return True
    if kind == "Try":
        hs = node.get("handlers")
        if isinstance(hs, list):
            for h in hs:
                if isinstance(h, dict):
                    hb = h.get("body")
                    if isinstance(hb, list):
                        for item in hb:
                            if _node_mutates(item):
                                return True
    return False


def _collect_self_calls(node: JsonVal, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_self_calls(item, out)
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Call":
        func = node.get("func")
        if isinstance(func, dict) and func.get("kind") == "Attribute":
            owner = func.get("value")
            if isinstance(owner, dict) and owner.get("kind") == "Name" and owner.get("id") == "self":
                mn = func.get("attr")
                if isinstance(mn, str) and mn != "":
                    out.add(mn)
    for v in node.values():
        if isinstance(v, (dict, list)):
            _collect_self_calls(v, out)


def _detect_ms_class(cd: Node) -> None:
    body = cd.get("body")
    if not isinstance(body, list):
        return
    methods: dict[str, Node] = {}
    direct: set[str] = set()
    cg: dict[str, set[str]] = {}
    for stmt in body:
        if not isinstance(stmt, dict) or stmt.get("kind") != "FunctionDef":
            continue
        name = jv_str(stmt.get("name", ""))
        if name == "":
            continue
        methods[name] = stmt
        mb = stmt.get("body")
        if isinstance(mb, list):
            for s in mb:
                if _node_mutates(s):
                    direct.add(name)
                    break
        sc: set[str] = set()
        if isinstance(mb, list):
            _collect_self_calls(mb, sc)
        cg[name] = sc
    mutators = set(direct)
    changed = True
    while changed:
        changed = False
        for name, callees in cg.items():
            if name in mutators:
                continue
            for callee in callees:
                if callee in mutators:
                    mutators.add(name)
                    changed = True
                    break
    for special in ("__init__", "__del__"):
        if special in methods:
            mutators.add(special)
    for name, stmt in methods.items():
        stmt["mutates_self"] = name in mutators


def _ms_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _ms_walk(item)
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "ClassDef":
        _detect_ms_class(node)
    for v in node.values():
        if isinstance(v, (dict, list)):
            _ms_walk(v)


def detect_mutates_self(module: Node, ctx: CompileContext) -> Node:
    _ms_walk(module)
    return module


# ===========================================================================
# unused variable detection
# ===========================================================================

def _uv_refs(node: JsonVal, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _uv_refs(item, out)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == "Name":
        n = nd.get("id")
        if isinstance(n, str) and n != "":
            out.add(n)
    elif kind in ("Assign", "AnnAssign", "AugAssign"):
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            _uv_refs(value, out)
        if kind == "AugAssign":
            target = nd.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                n = target.get("id")
                if isinstance(n, str) and n != "":
                    out.add(n)
        return
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _uv_refs(v, out)


def _uv_mark_fn(func: Node) -> None:
    body = func.get("body")
    if not isinstance(body, list):
        return
    all_refs: set[str] = set()
    _uv_refs(body, all_refs)
    ao = func.get("arg_order")
    if isinstance(ao, list):
        for arg in ao:
            if isinstance(arg, str):
                all_refs.add(arg)
    _uv_mark_stmts(body, all_refs)


def _uv_mark_stmts(stmts: list[JsonVal], all_refs: set[str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind == "VarDecl":
            n = stmt.get("name")
            if isinstance(n, str) and n != "" and n not in all_refs:
                stmt["unused"] = True
        elif kind in ("Assign", "AnnAssign"):
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                n = target.get("id")
                if isinstance(n, str) and n != "" and n not in all_refs:
                    stmt["unused"] = True
            elif isinstance(target, dict) and target.get("kind") == "Tuple":
                elements = target.get("elements")
                if isinstance(elements, list):
                    for elem in elements:
                        if isinstance(elem, dict) and elem.get("kind") == "Name":
                            en = elem.get("id")
                            if isinstance(en, str) and en != "" and en not in all_refs:
                                elem["unused"] = True
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                _uv_mark_stmts(nested, all_refs)
        if kind == "Try":
            hs = stmt.get("handlers")
            if isinstance(hs, list):
                for h in hs:
                    if isinstance(h, dict):
                        hb = h.get("body")
                        if isinstance(hb, list):
                            _uv_mark_stmts(hb, all_refs)


def _uv_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _uv_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == "FunctionDef":
        _uv_mark_fn(nd)
    for v in nd.values():
        if isinstance(v, (dict, list)):
            _uv_walk(v)


def detect_unused_variables(module: Node, ctx: CompileContext) -> Node:
    _uv_walk(module)
    return module


# ===========================================================================
# main guard discard
# ===========================================================================

def _mgd_stmts(stmts: list[JsonVal]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        if stmt.get("kind") == "Expr":
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "Call":
                stmt["discard_result"] = True


def mark_main_guard_discard(module: Node, ctx: CompileContext) -> Node:
    mg = module.get("main_guard_body")
    if isinstance(mg, list):
        _mgd_stmts(mg)
    body = module.get("body")
    if isinstance(body, list):
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef":
                name = stmt.get("name", "")
                if name == "__pytra_main":
                    fb = stmt.get("body")
                    if isinstance(fb, list):
                        _mgd_stmts(fb)
    return module

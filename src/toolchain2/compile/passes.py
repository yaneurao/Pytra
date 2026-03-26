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
from toolchain2.common.kinds import (
    MODULE, FUNCTION_DEF, CLASS_DEF, VAR_DECL,
    ASSIGN, ANN_ASSIGN, AUG_ASSIGN, EXPR, RETURN, YIELD,
    IF, WHILE, FOR, FOR_RANGE, FOR_CORE, TRY, SWAP,
    NAME, CONSTANT, CALL, ATTRIBUTE, SUBSCRIPT,
    BIN_OP, UNARY_OP, COMPARE, IF_EXP, BOOL_OP,
    LIST, DICT, SET, TUPLE, LIST_COMP,
    UNBOX,
    STATIC_RANGE_FOR_PLAN, RUNTIME_ITER_FOR_PLAN,
    NAME_TARGET, TUPLE_TARGET,
    ASSIGNMENT_KINDS,
)

# Re-export stubs — these are imported by lower.py
# Each function mutates the module in place and returns it.

# ===========================================================================
# yield lowering
# ===========================================================================

def _contains_yield(node: JsonVal) -> bool:
    if isinstance(node, dict):
        if node.get("kind") == YIELD:
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
    if kind == YIELD:
        value = nd.get("value")
        if value is None:
            value = {"kind": CONSTANT, "value": None, "resolved_type": "None"}
        ac: Node = {
            "kind": EXPR,
            "value": {
                "kind": CALL,
                "func": {"kind": ATTRIBUTE, "value": {"kind": NAME, "id": acc, "resolved_type": list_type}, "attr": "append"},
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
        "kind": ANN_ASSIGN,
        "target": {"kind": NAME, "id": acc, "resolved_type": lt},
        "annotation": lt, "decl_type": lt, "declare": True,
        "value": {"kind": LIST, "elements": [], "resolved_type": lt},
    }
    new_body = _replace_yield_with_append(body, acc, lt)
    if not isinstance(new_body, list):
        new_body = body
    ret_stmt: Node = {"kind": RETURN, "value": {"kind": NAME, "id": acc, "resolved_type": lt}}
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
    if kind == FUNCTION_DEF:
        body = nd.get("body")
        if isinstance(body, list) and _contains_yield(body):
            _lower_generator_function(nd)
        body2 = nd.get("body")
        if isinstance(body2, list):
            for s in body2:
                _yield_walk(s)
        return
    if kind in (CLASS_DEF, MODULE):
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
        if kind == NAME:
            plan: Node = {"kind": NAME_TARGET, "id": target.get("id", "_")}
            rt = jv_str(target.get("resolved_type", "")).strip()
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
        if kind == TUPLE:
            elements = target.get("elements") or target.get("elts") or []
            eps: list[JsonVal] = []
            if isinstance(elements, list):
                for elem in elements:
                    eps.append(_build_lc_target_plan(elem))
            plan = {"kind": TUPLE_TARGET, "elements": eps}
            rt = jv_str(target.get("resolved_type", "")).strip()
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
    return {"kind": NAME_TARGET, "id": "_"}


def _expand_lc_to_stmts(lc: Node, result_name: str, annotation_type: str = "") -> list[Node]:
    rt = jv_str(lc.get("resolved_type", "")).strip()
    if rt in ("", "unknown") or "unknown" in rt:
        if annotation_type != "":
            rt = annotation_type
        elif rt in ("", "unknown"):
            rt = "list[unknown]"
    init: Node = {
        "kind": ANN_ASSIGN,
        "target": {"kind": NAME, "id": result_name, "resolved_type": rt},
        "annotation": rt, "decl_type": rt, "declare": True,
        "value": {"kind": LIST, "elements": [], "resolved_type": rt},
    }
    elt = lc.get("elt")
    append_arg = deep_copy_json(elt) if elt is not None else None
    elem_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        elem_type = rt[5:-1]
    if isinstance(append_arg, dict) and elem_type != "":
        append_arg["call_arg_type"] = elem_type
        append_kind = append_arg.get("kind", "")
        append_rt = jv_str(append_arg.get("resolved_type", "")).strip()
        if append_kind == LIST and append_rt in ("", "unknown", "list[unknown]"):
            append_arg["resolved_type"] = elem_type
        elif append_kind == DICT and append_rt in ("", "unknown", "dict[unknown,unknown]"):
            append_arg["resolved_type"] = elem_type
        elif append_kind == SET and append_rt in ("", "unknown", "set[unknown]"):
            append_arg["resolved_type"] = elem_type
    generators = lc.get("generators", [])
    if not isinstance(generators, list):
        generators = []
    append_stmt: Node = {
        "kind": EXPR,
        "value": {
            "kind": CALL,
            "func": {"kind": ATTRIBUTE, "value": {"kind": NAME, "id": result_name, "resolved_type": rt}, "attr": "append"},
            "args": [append_arg] if append_arg is not None else [],
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
                    body = [{"kind": IF, "test": deep_copy_json(cond), "body": body, "orelse": []}]
        target = gen.get("target")
        iter_expr = gen.get("iter")
        tp = _build_lc_target_plan(target)
        if isinstance(iter_expr, dict) and iter_expr.get("kind") in ("RangeExpr", FOR_RANGE):
            fs: Node = {
                "kind": FOR_CORE, "iter_mode": "static_fastpath",
                "iter_plan": {
                    "kind": STATIC_RANGE_FOR_PLAN,
                    "start": deep_copy_json(iter_expr.get("start", {"kind": CONSTANT, "value": 0, "resolved_type": "int64"})),
                    "stop": deep_copy_json(iter_expr.get("stop", {"kind": CONSTANT, "value": 0})),
                    "step": deep_copy_json(iter_expr.get("step", {"kind": CONSTANT, "value": 1, "resolved_type": "int64"})),
                },
                "target_plan": tp, "body": body, "orelse": [],
            }
        else:
            fs = {
                "kind": FOR_CORE, "iter_mode": "runtime_protocol",
                "iter_plan": {
                    "kind": RUNTIME_ITER_FOR_PLAN,
                    "iter_expr": deep_copy_json(iter_expr) if iter_expr else {"kind": NAME, "id": "__empty"},
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
        if kind in (ASSIGN, ANN_ASSIGN):
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == LIST_COMP:
                target = stmt.get("target")
                tn = ""
                if isinstance(target, dict) and target.get("kind") == NAME:
                    tn = jv_str(target.get("id", "")).strip()
                cn = tn if tn != "" else ctx.next_comp_name()
                at = ""
                if kind == ANN_ASSIGN:
                    ann = stmt.get("annotation")
                    if isinstance(ann, str) and ann != "" and "unknown" not in ann:
                        at = ann
                expanded = _expand_lc_to_stmts(value, cn, at)
                if cn != tn and tn != "":
                    expanded.append({
                        "kind": ASSIGN,
                        "target": deep_copy_json(target),
                        "value": {"kind": NAME, "id": cn, "resolved_type": jv_str(value.get("resolved_type", ""))},
                    })
                result.extend(expanded)
                continue
        if kind == EXPR:
            ev = stmt.get("value")
            if isinstance(ev, dict) and ev.get("kind") == LIST_COMP:
                tmp = ctx.next_comp_name()
                result.extend(_expand_lc_to_stmts(ev, tmp))
                continue
        # Recurse
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _lc_in_stmts(nested, ctx)
        if kind == TRY:
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
    if kind == FUNCTION_DEF:
        name = jv_str(node.get("name", ""))
        if name == "":
            return
        ao = node.get("arg_order")
        ad = node.get("arg_defaults")
        if not isinstance(ao, list):
            return
        sig: Node = {"arg_order": ao, "arg_defaults": ad if isinstance(ad, dict) else {}}
        full = class_name + "." + name if class_name != "" else name
        if class_name == "":
            sigs[name] = sig
        if full != name:
            sigs[full] = sig
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, "")
    elif kind == CLASS_DEF:
        cn = jv_str(node.get("name", ""))
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, cn)
    elif kind == ASSIGN or kind == ANN_ASSIGN:
        target: JsonVal = node.get("target")
        if not isinstance(target, dict):
            targets = node.get("targets")
            if isinstance(targets, list) and len(targets) == 1 and isinstance(targets[0], dict):
                target = targets[0]
        value = node.get("value")
        if (
            isinstance(target, dict)
            and target.get("kind") == NAME
            and isinstance(value, dict)
            and value.get("kind") == "Lambda"
        ):
            lambda_name = jv_str(target.get("id", ""))
            args = value.get("args")
            if lambda_name != "" and isinstance(args, list):
                arg_order: list[str] = []
                arg_defaults: dict[str, JsonVal] = {}
                for arg in args:
                    if not isinstance(arg, dict):
                        continue
                    arg_name = jv_str(arg.get("arg", ""))
                    if arg_name == "":
                        continue
                    arg_order.append(arg_name)
                    default_node = arg.get("default")
                    if isinstance(default_node, dict):
                        arg_defaults[arg_name] = deep_copy_json(default_node)
                sigs[lambda_name] = {
                    "arg_order": arg_order,
                    "arg_defaults": arg_defaults,
                }


def _expand_defaults_walk(node: JsonVal, sigs: dict[str, Node]) -> None:
    if isinstance(node, list):
        for item in node:
            _expand_defaults_walk(item, sigs)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    if nd.get("kind") == CALL:
        func = nd.get("func")
        cn = ""
        if isinstance(func, dict):
            if func.get("kind") == NAME:
                cn = jv_str(func.get("id", ""))
            elif func.get("kind") == ATTRIBUTE:
                attr = jv_str(func.get("attr", ""))
                owner = func.get("value")
                if isinstance(owner, dict):
                    owner_type = jv_str(owner.get("resolved_type", ""))
                    if owner_type != "" and owner_type != "unknown":
                        qualified = owner_type + "." + attr
                        if qualified in sigs:
                            cn = qualified
                        else:
                            cn = attr
                    else:
                        cn = attr
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
        "kind": SUBSCRIPT,
        "value": {"kind": NAME, "id": owner, "resolved_type": "tuple"},
        "slice": {"kind": CONSTANT, "value": index, "resolved_type": "int64"},
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
    if nd.get("kind") == FOR_CORE:
        tp = nd.get("target_plan")
        if isinstance(tp, dict) and tp.get("kind") == TUPLE_TARGET:
            elements = tp.get("elements")
            if isinstance(elements, list) and len(elements) >= 2:
                tmp = ctx.next_tte_name()
                assigns: list[JsonVal] = []
                direct_names: list[JsonVal] = []
                for i, elem in enumerate(elements):
                    if not isinstance(elem, dict) or elem.get("kind") != NAME_TARGET:
                        continue
                    en = elem.get("id", "")
                    et = elem.get("target_type", "")
                    if not isinstance(en, str) or en == "":
                        continue
                    if not isinstance(et, str):
                        et = ""
                    assign: Node = {
                        "kind": ASSIGN,
                        "target": {"kind": NAME, "id": en, "resolved_type": et if et != "" else "unknown"},
                        "value": _tte_subscript(tmp, i, et),
                        "decl_type": et if et != "" else "unknown",
                        "declare": True,
                    }
                    assigns.append(assign)
                    direct_names.append(en)
                nd["target_plan"] = {
                    "kind": NAME_TARGET,
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
# tuple unpack expansion: x, y = expr → _tmp = expr; x = _tmp[0]; y = _tmp[1]
# ===========================================================================

def _expand_tuple_unpack_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    """Expand Assign(target=Tuple, value=expr) into temp + individual assigns."""
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = _sk(stmt)
        # Recurse into block-creating statements first
        if kind == FUNCTION_DEF or kind == CLASS_DEF:
            body = stmt.get("body")
            if isinstance(body, list):
                stmt["body"] = _expand_tuple_unpack_in_stmts(body, ctx)
            mg = stmt.get("main_guard_body")
            if isinstance(mg, list):
                stmt["main_guard_body"] = _expand_tuple_unpack_in_stmts(mg, ctx)
        elif kind in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE, TRY):
            for key in ("body", "orelse", "finalbody"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    stmt[key] = _expand_tuple_unpack_in_stmts(nested, ctx)
            handlers = stmt.get("handlers")
            if isinstance(handlers, list):
                for h in handlers:
                    if isinstance(h, dict):
                        hb = h.get("body")
                        if isinstance(hb, list):
                            h["body"] = _expand_tuple_unpack_in_stmts(hb, ctx)

        # Check for tuple unpack Assign
        if kind != ASSIGN:
            result.append(stmt)
            continue
        target = stmt.get("target")
        if not isinstance(target, dict) or target.get("kind") != TUPLE:
            result.append(stmt)
            continue
        elements = target.get("elements")
        if not isinstance(elements, list) or len(elements) == 0:
            result.append(stmt)
            continue
        value = stmt.get("value")

        # Detect swap pattern: a, b = b, a → Swap node
        if isinstance(value, dict) and value.get("kind") == TUPLE and len(elements) == 2:
            val_elements = value.get("elements")
            if isinstance(val_elements, list) and len(val_elements) == 2:
                le0 = elements[0] if isinstance(elements[0], dict) else {}
                le1 = elements[1] if isinstance(elements[1], dict) else {}
                re0 = val_elements[0] if isinstance(val_elements[0], dict) else {}
                re1 = val_elements[1] if isinstance(val_elements[1], dict) else {}
                # Check if targets[0]=rhs[1] and targets[1]=rhs[0] (cross reference)
                if _same_lvalue(le0, re1) and _same_lvalue(le1, re0):
                    swap_node: Node = {
                        "kind": SWAP,
                        "left": deep_copy_json(le0),
                        "right": deep_copy_json(le1),
                    }
                    result.append(swap_node)
                    continue

        # Generate: _tmp = value
        tmp_name: str = ctx.next_tuple_tmp_name()
        val_rt = ""
        if isinstance(value, dict):
            val_rt = jv_str(value.get("resolved_type"))
        target_rt = jv_str(target.get("resolved_type"))
        tmp_value, tmp_rt = _make_tuple_unpack_source(value, val_rt, target_rt)
        tmp_assign: Node = {
            "kind": ASSIGN,
            "target": {"kind": NAME, "id": tmp_name, "resolved_type": tmp_rt},
            "value": tmp_value,
            "declare": True,
            "decl_type": tmp_rt,
        }
        result.append(tmp_assign)

        # Parse tuple element types from the effective tuple source.
        elem_types: list[str] = _parse_tuple_element_types(tmp_rt)
        if len(elem_types) == 0:
            elem_types = _parse_tuple_element_types(target_rt)

        # Generate: x = _tmp[0], y = _tmp[1], ...
        for i, elem in enumerate(elements):
            if not isinstance(elem, dict):
                continue
            elem_name = elem.get("id")
            if not isinstance(elem_name, str) or elem_name == "":
                continue
            elem_rt = elem_types[i] if i < len(elem_types) else "unknown"
            idx_node: Node = {
                "kind": SUBSCRIPT,
                "value": {"kind": NAME, "id": tmp_name, "resolved_type": tmp_rt},
                "slice": {"kind": CONSTANT, "value": i, "resolved_type": "int64"},
                "resolved_type": elem_rt,
            }
            elem_assign: Node = {
                "kind": ASSIGN,
                "target": {"kind": NAME, "id": elem_name, "resolved_type": elem_rt},
                "value": idx_node,
                "declare": True,
                "decl_type": elem_rt,
            }
            result.append(elem_assign)

    return result


def _same_lvalue(a: Node, b: Node) -> bool:
    """Check if two nodes refer to the same l-value (Name or Subscript)."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    ak = a.get("kind", "")
    bk = b.get("kind", "")
    if ak != bk:
        return False
    if ak == NAME:
        return a.get("id", "") == b.get("id", "") and a.get("id", "") != ""
    if ak == SUBSCRIPT:
        av = a.get("value")
        bv = b.get("value")
        asl = a.get("slice")
        bsl = b.get("slice")
        return _same_lvalue(av, bv) and _same_lvalue(asl, bsl)
    if ak == "Constant":
        return a.get("value") == b.get("value")
    if ak == ATTRIBUTE:
        return (a.get("attr", "") == b.get("attr", "") and
                _same_lvalue(a.get("value"), b.get("value")))
    if ak == BIN_OP:
        return (a.get("op", "") == b.get("op", "") and
                _same_lvalue(a.get("left"), b.get("left")) and
                _same_lvalue(a.get("right"), b.get("right")))
    return False


def _parse_tuple_element_types(rt: str) -> list[str]:
    """Parse "tuple[int64,str,float64]" into ["int64", "str", "float64"]."""
    if not rt.startswith("tuple[") or not rt.endswith("]"):
        return []
    inner = rt[6:-1]
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in inner:
        if ch == "[":
            depth += 1
            cur.append(ch)
        elif ch == "]":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _make_tuple_unpack_source(value: JsonVal, source_type: str, target_type: str) -> tuple[JsonVal, str]:
    normalized_source = normalize_type_name(source_type)
    normalized_target = normalize_type_name(target_type)
    if normalized_target.startswith("tuple["):
        if normalized_source.startswith("tuple["):
            return value, normalized_source
        if "None" in normalized_source.split(" | "):
            out: Node = {
                "kind": UNBOX,
                "value": deep_copy_json(value),
                "resolved_type": normalized_target,
                "borrow_kind": "value",
                "casts": [],
                "target": normalized_target,
                "on_fail": "raise",
            }
            if isinstance(value, dict):
                span = value.get("source_span")
                if isinstance(span, dict):
                    out["source_span"] = span
                repr_text = value.get("repr")
                if isinstance(repr_text, str) and repr_text != "":
                    out["repr"] = repr_text
            return out, normalized_target
    return value, normalized_source


def expand_tuple_unpack(module: Node, ctx: CompileContext) -> Node:
    """Expand all Assign(target=Tuple, ...) in the module."""
    body = module.get("body")
    if isinstance(body, list):
        module["body"] = _expand_tuple_unpack_in_stmts(body, ctx)
    mg = module.get("main_guard_body")
    if isinstance(mg, list):
        module["main_guard_body"] = _expand_tuple_unpack_in_stmts(mg, ctx)
    return module


# ===========================================================================
# enumerate lowering
# ===========================================================================

def _try_lower_enum_forcore(stmt: Node, ctx: CompileContext) -> list[Node] | None:
    ip = stmt.get("iter_plan")
    if not isinstance(ip, dict) or ip.get("kind") != RUNTIME_ITER_FOR_PLAN:
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
        if isinstance(sa, dict) and sa.get("kind") == CONSTANT:
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
        if s.get("kind") == ASSIGN:
            target = s.get("target")
            value = s.get("value")
            if isinstance(target, dict) and isinstance(value, dict) and value.get("kind") == SUBSCRIPT:
                sl = value.get("slice", {})
                if isinstance(sl, dict) and sl.get("kind") == CONSTANT:
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
        "kind": ASSIGN,
        "target": {"kind": NAME, "id": counter, "resolved_type": "int64"},
        "value": {"kind": CONSTANT, "value": start_val, "resolved_type": "int64"},
        "decl_type": "int64", "declare": True,
    }
    raw_tt = jv_str(tp.get("target_type", "")).strip()
    vtt = raw_tt
    if raw_tt.startswith("tuple[") and raw_tt.endswith("]"):
        inner = raw_tt[6:-1]
        parts = _split_comma_types(inner)
        if len(parts) >= 2:
            vtt = parts[1]
    ntp: Node = {"kind": NAME_TARGET, "id": val_name, "target_type": vtt}
    nip: Node = {
        "kind": RUNTIME_ITER_FOR_PLAN,
        "iter_expr": deep_copy_json(iterable),
        "dispatch_mode": ip.get("dispatch_mode", "native"),
        "init_op": "ObjIterInit", "next_op": "ObjIterNext",
    }
    assign_idx: Node = {
        "kind": ASSIGN,
        "target": {"kind": NAME, "id": idx_name, "resolved_type": "int64"},
        "value": {"kind": NAME, "id": counter, "resolved_type": "int64"},
        "decl_type": "int64", "declare": True,
    }
    increment: Node = {
        "kind": AUG_ASSIGN,
        "target": {"kind": NAME, "id": counter, "resolved_type": "int64"},
        "op": "Add",
        "value": {"kind": CONSTANT, "value": 1, "resolved_type": "int64"},
    }
    nb = [assign_idx] + remaining + [increment]
    nf: Node = {
        "kind": FOR_CORE, "iter_mode": stmt.get("iter_mode", "runtime_protocol"),
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
        if kind == FOR_CORE:
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
    # Also check value's resolved_type (for computed assignments)
    value = stmt.get("value")
    if isinstance(value, dict):
        vrt = value.get("resolved_type")
        if isinstance(vrt, str) and vrt.strip() not in ("", "unknown"):
            return vrt.strip()
    return ""


def _collect_assign_names(stmt: Node, out: dict[str, str]) -> None:
    target = stmt.get("target")
    if isinstance(target, dict):
        tk = target.get("kind")
        if tk == NAME:
            n = target.get("id")
            if isinstance(n, str) and n != "" and n not in out:
                out[n] = _resolve_atype(stmt)
        elif tk == TUPLE:
            _collect_tuple_tgt_names(target, stmt, out)
    targets = stmt.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict):
                if t.get("kind") == NAME:
                    n = t.get("id")
                    if isinstance(n, str) and n != "" and n not in out:
                        out[n] = _resolve_atype(stmt)
                elif t.get("kind") == TUPLE:
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
        if not isinstance(elem, dict) or elem.get("kind") != NAME:
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
        if kind in (ASSIGN, ANN_ASSIGN):
            _collect_assign_names(stmt, out)
        elif kind == IF:
            for key in ("body", "orelse"):
                nested = stmt.get(key)
                if isinstance(nested, list):
                    sub = _collect_assigned_in_stmts(nested)
                    for n, t in sub.items():
                        if n not in out:
                            out[n] = t
                        elif out[n] == "" and t != "":
                            out[n] = t
        elif kind in (WHILE, FOR, FOR_RANGE, FOR_CORE):
            if kind == FOR_CORE:
                tp = stmt.get("target_plan")
                if isinstance(tp, dict):
                    tpk = tp.get("kind")
                    if tpk == NAME_TARGET:
                        tpn = tp.get("id")
                        tpt = tp.get("target_type", "")
                        if isinstance(tpn, str) and tpn != "" and tpn not in out:
                            out[tpn] = tpt if isinstance(tpt, str) else ""
                    elif tpk == TUPLE_TARGET:
                        elems = tp.get("elements")
                        if isinstance(elems, list):
                            for e in elems:
                                if isinstance(e, dict) and e.get("kind") == NAME_TARGET:
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
    if nd.get("kind") == NAME:
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
        if isinstance(elem, dict) and elem.get("kind") == NAME:
            n = elem.get("id")
            if isinstance(n, str) and n != "":
                out.add(n)


def _mark_reassign(stmts: list[JsonVal], hoisted: set[str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _sk(stmt)
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt.get("target")
            if isinstance(target, dict):
                if target.get("kind") == NAME:
                    n = target.get("id")
                    if isinstance(n, str) and n in hoisted:
                        stmt["is_reassign"] = True
                elif target.get("kind") == TUPLE:
                    elements = target.get("elements")
                    if isinstance(elements, list):
                        for elem in elements:
                            if isinstance(elem, dict) and elem.get("kind") == NAME:
                                en = elem.get("id")
                                if isinstance(en, str) and en in hoisted:
                                    stmt["is_reassign"] = True
                                    break
        if kind in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE):
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
            if isinstance(nested, dict) and _sk(nested) == IF:
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
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt.get("target")
            if isinstance(target, dict):
                if target.get("kind") == NAME:
                    n = target.get("id")
                    if isinstance(n, str) and n != "":
                        already.add(n)
                elif target.get("kind") == TUPLE:
                    _collect_tuple_names_flat(target, already)
            targets = stmt.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict):
                        if t.get("kind") == NAME:
                            n = t.get("id")
                            if isinstance(n, str) and n != "":
                                already.add(n)
                        elif t.get("kind") == TUPLE:
                            _collect_tuple_names_flat(t, already)
            result.append(stmt)
            continue
        if kind == VAR_DECL:
            n = stmt.get("name")
            if isinstance(n, str) and n != "":
                already.add(n)
            result.append(stmt)
            continue
        if kind not in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE):
            result.append(stmt)
            continue
        # Block-creating statement
        ba2 = _collect_block_assigned(stmt)
        names_after: set[str] = set()
        for j in range(i + 1, len(stmts)):
            _collect_refs(stmts[j], names_after)
        multi_branch: set[str] = set()
        if kind == IF:
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
            vd: Node = {"kind": VAR_DECL, "name": n, "type": to_hoist[n] if to_hoist[n] != "" else "unknown", "hoisted": True}
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
    if kind == IF:
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                sub = _collect_assigned_in_stmts(nested)
                for n, t in sub.items():
                    if n not in all_names:
                        all_names[n] = t
                    elif all_names[n] == "" and t != "":
                        all_names[n] = t
    elif kind in (WHILE, FOR, FOR_RANGE, FOR_CORE):
        if kind == FOR_CORE:
            tp = stmt.get("target_plan")
            if isinstance(tp, dict):
                tpk = tp.get("kind")
                if tpk == NAME_TARGET:
                    tpn = tp.get("id")
                    tpt = tp.get("target_type", "")
                    if isinstance(tpn, str) and tpn != "" and tpn not in all_names:
                        all_names[tpn] = tpt if isinstance(tpt, str) else ""
                elif tpk == TUPLE_TARGET:
                    elems = tp.get("elements")
                    if isinstance(elems, list):
                        for e in elems:
                            if isinstance(e, dict) and e.get("kind") == NAME_TARGET:
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
    if kind == FUNCTION_DEF:
        body = nd.get("body")
        if isinstance(body, list):
            nd["body"] = _hoist_in_stmt_list(body, _fn_param_names(nd))
            for s in nd["body"]:
                _hoist_walk(s)
        return
    if kind in (CLASS_DEF, MODULE):
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
    if kind == BIN_OP:
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
    if kind == UNARY_OP:
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
    if kind == FOR_CORE:
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
    if kind in (ASSIGN, ANN_ASSIGN):
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
    if kind == BIN_OP:
        left = vn.get("left")
        right = vn.get("right")
        lt2 = _nt(left.get("resolved_type")) if isinstance(left, dict) else ""
        rt2 = _nt(right.get("resolved_type")) if isinstance(right, dict) else ""
        lw = _INT_WIDTH.get(lt2, 0) if lt2 in _INT_WIDTH else 0
        rw2 = _INT_WIDTH.get(rt2, 0) if rt2 in _INT_WIDTH else 0
        if lw > 0 and rw2 > 0 and tw >= lw and tw >= rw2:
            vn["resolved_type"] = tt
    elif kind == UNARY_OP:
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
    if kind in (ASSIGN, ANN_ASSIGN):
        value = nd.get("value")
        if isinstance(value, dict) and value.get("kind") == UNBOX:
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
# guard narrowing
# ===========================================================================

_TYPE_GUARD_DEFAULTS: dict[str, str] = {
    "PYTRA_TID_NONE": "None",
    "PYTRA_TID_BOOL": "bool",
    "PYTRA_TID_INT": "int64",
    "PYTRA_TID_FLOAT": "float64",
    "PYTRA_TID_STR": "str",
    "PYTRA_TID_LIST": "list",
    "PYTRA_TID_DICT": "dict",
    "PYTRA_TID_SET": "set",
    "PYTRA_TID_TUPLE": "tuple",
}


def _split_union_members(type_name: str) -> list[str]:
    parts: list[str] = []
    cur = ""
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "|" and depth == 0:
            part = cur.strip()
            if part != "":
                parts.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        parts.append(tail)
    return parts


def _type_matches_guard(type_name: str, guard_type: str) -> bool:
    norm = normalize_type_name(type_name)
    guard = normalize_type_name(guard_type)
    if norm == "" or norm == "unknown" or guard == "" or guard == "unknown":
        return False
    if guard == "None":
        return norm == "None"
    if guard == "bool":
        return norm == "bool"
    if guard == "int":
        return norm in _INT_WIDTH or norm == "int"
    if guard == "float":
        return norm in ("float", "float32", "float64")
    if guard == "str":
        return norm == "str"
    if guard in ("list", "dict", "set", "tuple"):
        return norm == guard or norm.startswith(guard + "[")
    return norm == guard


def _select_guard_target_type(source_type: str, expected_name: str) -> str:
    src = normalize_type_name(source_type)
    expected = normalize_type_name(expected_name)
    if src == "" or src == "unknown" or expected == "" or expected == "unknown":
        return ""
    guard_type = expected
    default_type = _TYPE_GUARD_DEFAULTS.get(expected, "")
    if default_type != "":
        guard_type = default_type
        if expected == "PYTRA_TID_INT":
            guard_type = "int"
        elif expected == "PYTRA_TID_FLOAT":
            guard_type = "float"
    members = _split_union_members(src)
    if len(members) == 0:
        members = [src]
    for member in members:
        if _type_matches_guard(member, guard_type):
            return normalize_type_name(member)
    if default_type != "":
        return normalize_type_name(default_type)
    if _type_matches_guard(src, guard_type):
        return src
    return expected


def _guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    if not isinstance(expr, dict):
        return {}
    nd: Node = expr
    kind = nd.get("kind", "")
    if kind == "IsInstance":
        value = nd.get("value")
        expected = nd.get("expected_type_id")
        if not isinstance(value, dict) or value.get("kind") != NAME:
            return {}
        name = _tp_safe(value.get("id"))
        if name == "":
            return {}
        expected_name = ""
        if isinstance(expected, dict):
            expected_name = _tp_safe(expected.get("id"))
            if expected_name == "":
                expected_name = _tp_safe(expected.get("repr"))
        target_type = _select_guard_target_type(_tp_safe(value.get("resolved_type")), expected_name)
        if target_type == "" or target_type == "unknown":
            return {}
        return {name: target_type}
    if kind == COMPARE:
        left = nd.get("left")
        comparators = nd.get("comparators")
        ops = nd.get("ops")
        if (
            isinstance(left, dict)
            and left.get("kind") == NAME
            and isinstance(comparators, list)
            and len(comparators) == 1
            and isinstance(comparators[0], dict)
            and comparators[0].get("kind") == CONSTANT
            and comparators[0].get("value") is None
            and isinstance(ops, list)
            and len(ops) == 1
        ):
            name2 = _tp_safe(left.get("id"))
            src_type = _tp_safe(left.get("resolved_type"))
            if name2 == "" or src_type == "":
                return {}
            members = [member for member in _split_union_members(src_type) if normalize_type_name(member) != "None"]
            op = _tp_safe(ops[0])
            if op == "IsNot":
                if len(members) == 0:
                    return {}
                if len(members) == 1:
                    return {name2: normalize_type_name(members[0])}
                return {name2: " | ".join([normalize_type_name(member) for member in members])}
        return {}
    if kind == BOOL_OP and _tp_safe(nd.get("op")) == "And":
        merged: dict[str, str] = {}
        values = nd.get("values")
        if not isinstance(values, list):
            return merged
        for value in values:
            child = _guard_narrowing_from_expr(value)
            for name, target_type in child.items():
                cur = merged.get(name, "")
                if cur == "" or cur == target_type:
                    merged[name] = target_type
                else:
                    merged.pop(name, None)
        return merged
    return {}


def _invert_guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    if not isinstance(expr, dict):
        return {}
    nd: Node = expr
    if nd.get("kind", "") != COMPARE:
        return {}
    left = nd.get("left")
    comparators = nd.get("comparators")
    ops = nd.get("ops")
    if (
        not isinstance(left, dict)
        or left.get("kind") != NAME
        or not isinstance(comparators, list)
        or len(comparators) != 1
        or not isinstance(comparators[0], dict)
        or comparators[0].get("kind") != CONSTANT
        or comparators[0].get("value") is not None
        or not isinstance(ops, list)
        or len(ops) != 1
    ):
        return {}
    name = _tp_safe(left.get("id"))
    src_type = _tp_safe(left.get("resolved_type"))
    if name == "" or src_type == "":
        return {}
    members = [member for member in _split_union_members(src_type) if normalize_type_name(member) != "None"]
    if len(members) == 0:
        return {}
    narrowed = members[0] if len(members) == 1 else " | ".join(members)
    op = _tp_safe(ops[0])
    if op == "Is":
        return {name: normalize_type_name(narrowed)}
    return {}


def _make_guard_unbox(name_node: Node, target_type: str) -> Node:
    out: Node = {
        "kind": UNBOX,
        "value": deep_copy_json(name_node),
        "resolved_type": target_type,
        "borrow_kind": "value",
        "casts": [],
        "target": target_type,
        "on_fail": "raise",
    }
    span = name_node.get("source_span")
    if isinstance(span, dict):
        out["source_span"] = span
    repr_obj = name_node.get("repr")
    if isinstance(repr_obj, str) and repr_obj != "":
        out["repr"] = repr_obj
    return out


def _guard_expr(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if isinstance(node, list):
        for i in range(len(node)):
            node[i] = _guard_expr(node[i], env)
        return node
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == NAME:
        name = _tp_safe(nd.get("id"))
        target_type = env.get(name, "")
        current_type = _tp_safe(nd.get("resolved_type"))
        if target_type != "" and target_type != current_type:
            return _make_guard_unbox(nd, target_type)
        return nd
    if kind in (FUNCTION_DEF, CLASS_DEF, UNBOX):
        return nd
    for key in list(nd.keys()):
        value = nd[key]
        if isinstance(value, (dict, list)):
            nd[key] = _guard_expr(value, env)
    return nd


def _guard_lvalue(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == ATTRIBUTE:
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            nd["value"] = _guard_expr(value, env)
        return nd
    if kind == SUBSCRIPT:
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            nd["value"] = _guard_expr(value, env)
        slice_obj = nd.get("slice")
        if isinstance(slice_obj, (dict, list)):
            nd["slice"] = _guard_expr(slice_obj, env)
        return nd
    if kind in (TUPLE, LIST):
        elements = nd.get("elements")
        if isinstance(elements, list):
            for i in range(len(elements)):
                elements[i] = _guard_lvalue(elements[i], env)
        return nd
    return nd


def _target_names(node: JsonVal) -> set[str]:
    if not isinstance(node, dict):
        return set()
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == NAME:
        name = _tp_safe(nd.get("id"))
        return {name} if name != "" else set()
    if kind == NAME_TARGET:
        name = _tp_safe(nd.get("id"))
        return {name} if name != "" else set()
    if kind in (TUPLE, LIST):
        out: set[str] = set()
        elements = nd.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                out.update(_target_names(elem))
        return out
    if kind == TUPLE_TARGET:
        out = set()
        elements = nd.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                out.update(_target_names(elem))
        return out
    return set()


def _guard_stmt_list(stmts: JsonVal, env: dict[str, str]) -> JsonVal:
    if not isinstance(stmts, list):
        return stmts
    local_env = dict(env)
    for stmt in stmts:
        _guard_stmt(stmt, local_env)
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind", "")
        if kind == IF:
            body = stmt.get("body")
            orelse = stmt.get("orelse")
            body_exits = _guard_block_guarantees_exit(body)
            orelse_exits = _guard_block_guarantees_exit(orelse)
            if body_exits and not orelse_exits:
                local_env.update(_invert_guard_narrowing_from_expr(stmt.get("test")))
            elif orelse_exits and not body_exits:
                local_env.update(_guard_narrowing_from_expr(stmt.get("test")))
        if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN, FOR, FOR_RANGE):
            for name in _target_names(stmt.get("target")):
                local_env.pop(name, None)
        elif kind == FOR_CORE:
            for name in _target_names(stmt.get("target_plan")):
                local_env.pop(name, None)
    return stmts


def _guard_stmt_guarantees_exit(stmt: JsonVal) -> bool:
    if not isinstance(stmt, dict):
        return False
    kind = _tp_safe(stmt.get("kind"))
    if kind in (RETURN, "Raise"):
        return True
    if kind == IF:
        return _guard_block_guarantees_exit(stmt.get("body")) and _guard_block_guarantees_exit(stmt.get("orelse"))
    return False


def _guard_block_guarantees_exit(stmts: JsonVal) -> bool:
    if not isinstance(stmts, list) or len(stmts) == 0:
        return False
    return _guard_stmt_guarantees_exit(stmts[-1])


def _guard_stmt(stmt: JsonVal, env: dict[str, str]) -> None:
    if not isinstance(stmt, dict):
        return
    nd: Node = stmt
    kind = nd.get("kind", "")
    if kind == FUNCTION_DEF:
        _guard_stmt_list(nd.get("body"), {})
        return
    if kind == CLASS_DEF:
        body = nd.get("body")
        if isinstance(body, list):
            for item in body:
                _guard_stmt(item, {})
        return
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        target = nd.get("target")
        if isinstance(target, dict):
            nd["target"] = _guard_lvalue(target, env)
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == EXPR:
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == RETURN:
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == IF:
        test = nd.get("test")
        if isinstance(test, (dict, list)):
            nd["test"] = _guard_expr(test, env)
        body_env = dict(env)
        body_env.update(_guard_narrowing_from_expr(nd.get("test")))
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == WHILE:
        test = nd.get("test")
        if isinstance(test, (dict, list)):
            nd["test"] = _guard_expr(test, env)
        body_env = dict(env)
        body_env.update(_guard_narrowing_from_expr(nd.get("test")))
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR:
        iter_obj = nd.get("iter")
        if isinstance(iter_obj, (dict, list)):
            nd["iter"] = _guard_expr(iter_obj, env)
        body_env = dict(env)
        for name in _target_names(nd.get("target")):
            body_env.pop(name, None)
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR_RANGE:
        for key in ("start", "stop", "step"):
            value = nd.get(key)
            if isinstance(value, (dict, list)):
                nd[key] = _guard_expr(value, env)
        body_env = dict(env)
        for name in _target_names(nd.get("target")):
            body_env.pop(name, None)
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR_CORE:
        iter_plan = nd.get("iter_plan")
        if isinstance(iter_plan, dict):
            for key in ("iter_expr", "start", "stop", "step"):
                value = iter_plan.get(key)
                if isinstance(value, (dict, list)):
                    iter_plan[key] = _guard_expr(value, env)
        body_env = dict(env)
        for name in _target_names(nd.get("target_plan")):
            body_env.pop(name, None)
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == TRY:
        _guard_stmt_list(nd.get("body"), env)
        handlers = nd.get("handlers")
        if isinstance(handlers, list):
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                body = handler.get("body")
                if isinstance(body, list):
                    _guard_stmt_list(body, env)
        _guard_stmt_list(nd.get("orelse"), env)
        _guard_stmt_list(nd.get("finalbody"), env)
        return
    for key in list(nd.keys()):
        value = nd[key]
        if isinstance(value, (dict, list)):
            nd[key] = _guard_expr(value, env)


def apply_guard_narrowing(module: Node, ctx: CompileContext) -> Node:
    _guard_stmt_list(module.get("body"), {})
    _guard_stmt_list(module.get("main_guard_body"), {})
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
    if kind == FUNCTION_DEF:
        rt = _tp_safe(nd.get("return_type"))
        returns = nd.get("returns")
        if returns is None and rt not in ("", "unknown"):
            nd["returns"] = rt
    if kind in (ASSIGN, ANN_ASSIGN):
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
                    if vk in (LIST, DICT, SET):
                        value["resolved_type"] = dt
            if target.get("kind") == TUPLE and isinstance(value, dict):
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
    if nd.get("kind") == BIN_OP:
        rt = _tp_safe(nd.get("resolved_type"))
        if rt not in ("", "unknown") and "|" not in rt:
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
    if nd.get("kind") == COMPARE:
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            nd["resolved_type"] = "bool"
    if nd.get("kind") == SUBSCRIPT:
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
    if nd.get("kind") == UNARY_OP:
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
    if node.get("kind") != BIN_OP or node.get("op") != "Div":
        return None
    left = node.get("left")
    if not isinstance(left, dict):
        return None
    lt = _tp_safe(left.get("resolved_type"))
    if lt != "Path":
        return None
    right = node.get("right")
    call: Node = {
        "kind": CALL,
        "func": {"kind": ATTRIBUTE, "value": left, "attr": "joinpath", "resolved_type": "Path"},
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
        if kind == FUNCTION_DEF:
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
        elif kind == CLASS_DEF:
            cb = stmt.get("body")
            if isinstance(cb, list):
                for m in cb:
                    if isinstance(m, dict) and m.get("kind") == FUNCTION_DEF:
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
    if nd.get("kind") == CALL:
        args = nd.get("args")
        if isinstance(args, list):
            for arg in args:
                if isinstance(arg, dict) and arg.get("kind") == NAME:
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
    if nd.get("kind") == CALL:
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
    if kind == IF_EXP:
        nd["yields_dynamic"] = True
    if kind == CALL:
        func = nd.get("func")
        if isinstance(func, dict):
            fk = func.get("kind", "")
            if fk == NAME:
                cn = func.get("id", "")
                if cn == "min" or cn == "max":
                    nd["yields_dynamic"] = True
            if fk == ATTRIBUTE:
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
    if kind == NAME:
        return "Name:" + jv_str(node.get("id", ""))
    if kind == SUBSCRIPT:
        val = _expr_key(node.get("value"))
        slc = _expr_key(node.get("slice"))
        return "Sub:" + val + "[" + slc + "]"
    if kind == CONSTANT:
        return "Const:" + str(node.get("value", ""))
    if kind == BIN_OP:
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
        if kind == ASSIGN:
            target = stmt.get("target")
            value = stmt.get("value")
            if isinstance(target, dict) and target.get("kind") == TUPLE and isinstance(value, dict) and value.get("kind") == TUPLE:
                te = target.get("elements", target.get("elts", []))
                ve = value.get("elements", value.get("elts", []))
                if isinstance(te, list) and isinstance(ve, list) and len(te) == 2 and len(ve) == 2:
                    t0 = _expr_key(te[0])
                    t1 = _expr_key(te[1])
                    v0 = _expr_key(ve[0])
                    v1 = _expr_key(ve[1])
                    if t0 != "" and t1 != "" and t0 == v1 and t1 == v0:
                        span = stmt.get("source_span")
                        if isinstance(te[0], dict) and te[0].get("kind") == NAME and isinstance(te[1], dict) and te[1].get("kind") == NAME:
                            swap: Node = {"kind": SWAP, "left": te[0], "right": te[1], "lhs": te[0], "rhs": te[1]}
                            if isinstance(span, dict):
                                swap["source_span"] = span
                            result.append(swap)
                            continue
                        # Subscript swap expansion
                        tmp = ctx.next_swap_name()
                        bs: Node = span if isinstance(span, dict) else {}
                        tt: Node = {"kind": NAME, "id": tmp}
                        if bs:
                            tt["source_span"] = bs
                        a1: Node = {"kind": ASSIGN, "target": tt, "value": te[0], "declare": True}
                        if bs:
                            a1["source_span"] = bs
                        a2: Node = {"kind": ASSIGN, "target": te[0], "value": te[1]}
                        if bs:
                            a2["source_span"] = bs
                        tr: Node = {"kind": NAME, "id": tmp}
                        if bs:
                            tr["source_span"] = bs
                        a3: Node = {"kind": ASSIGN, "target": te[1], "value": tr}
                        if bs:
                            a3["source_span"] = bs
                        result.extend([a1, a2, a3])
                        continue
        for key in ("body", "orelse"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _swap_in_stmts(nested, ctx)
        if kind == FUNCTION_DEF or kind == CLASS_DEF:
            body = stmt.get("body")
            if isinstance(body, list):
                stmt["body"] = _swap_in_stmts(body, ctx)
        elif kind == TRY:
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
    if node.get("kind") != ATTRIBUTE:
        return False
    value = node.get("value")
    return isinstance(value, dict) and value.get("kind") == NAME and value.get("id") == "self"


def _node_mutates(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = node.get("kind", "")
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        target = node.get("target")
        if isinstance(target, dict):
            if _is_self_attr(target):
                return True
            if target.get("kind") == SUBSCRIPT:
                val = target.get("value")
                if isinstance(val, dict) and _is_self_attr(val):
                    return True
    if kind == EXPR:
        value = node.get("value")
        if isinstance(value, dict) and value.get("kind") == CALL:
            func = value.get("func")
            if isinstance(func, dict) and func.get("kind") == ATTRIBUTE:
                owner = func.get("value")
                if isinstance(owner, dict) and _is_self_attr(owner):
                    return True
    for key in ("body", "orelse", "finalbody"):
        nested = node.get(key)
        if isinstance(nested, list):
            for item in nested:
                if _node_mutates(item):
                    return True
    if kind == TRY:
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
    if node.get("kind") == CALL:
        func = node.get("func")
        if isinstance(func, dict) and func.get("kind") == ATTRIBUTE:
            owner = func.get("value")
            if isinstance(owner, dict) and owner.get("kind") == NAME and owner.get("id") == "self":
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
        if not isinstance(stmt, dict) or stmt.get("kind") != FUNCTION_DEF:
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
    if node.get("kind") == CLASS_DEF:
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
    if kind == NAME:
        n = nd.get("id")
        if isinstance(n, str) and n != "":
            out.add(n)
    elif kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        value = nd.get("value")
        if isinstance(value, (dict, list)):
            _uv_refs(value, out)
        if kind == AUG_ASSIGN:
            target = nd.get("target")
            if isinstance(target, dict) and target.get("kind") == NAME:
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
        if kind == VAR_DECL:
            n = stmt.get("name")
            if isinstance(n, str) and n != "" and n not in all_refs:
                stmt["unused"] = True
        elif kind in (ASSIGN, ANN_ASSIGN):
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == NAME:
                n = target.get("id")
                if isinstance(n, str) and n != "" and n not in all_refs:
                    stmt["unused"] = True
            elif isinstance(target, dict) and target.get("kind") == TUPLE:
                elements = target.get("elements")
                if isinstance(elements, list):
                    for elem in elements:
                        if isinstance(elem, dict) and elem.get("kind") == NAME:
                            en = elem.get("id")
                            if isinstance(en, str) and en != "" and en not in all_refs:
                                elem["unused"] = True
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                _uv_mark_stmts(nested, all_refs)
        if kind == TRY:
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
    if nd.get("kind") == FUNCTION_DEF:
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
        if stmt.get("kind") == EXPR:
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == CALL:
                stmt["discard_result"] = True


def mark_main_guard_discard(module: Node, ctx: CompileContext) -> Node:
    mg = module.get("main_guard_body")
    if isinstance(mg, list):
        _mgd_stmts(mg)
    body = module.get("body")
    if isinstance(body, list):
        for stmt in body:
            if isinstance(stmt, dict) and stmt.get("kind") == FUNCTION_DEF:
                name = stmt.get("name", "")
                if name == "__pytra_main":
                    fb = stmt.get("body")
                    if isinstance(fb, list):
                        _mgd_stmts(fb)
    return module

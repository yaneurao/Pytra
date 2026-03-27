"""Post-lowering passes for EAST2 → EAST3.

Consolidated port of all toolchain/compile/east2_to_east3_*_*.py passes.
§5.1: Any/object 禁止 — uses JsonVal throughout.
§5.3: Python 標準モジュール直接 import 禁止。
"""

from __future__ import annotations

from typing import Union
from pytra.typing import cast

from toolchain2.compile.jv import JsonVal, Node, CompileContext, deep_copy_json
from toolchain2.compile.jv import jv_str, jv_is_dict, jv_is_list
from toolchain2.compile.jv import normalize_type_name
from toolchain2.common.kinds import (
    MODULE, FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF, VAR_DECL,
    ASSIGN, ANN_ASSIGN, AUG_ASSIGN, EXPR, RETURN, YIELD,
    IF, WHILE, FOR, FOR_RANGE, FOR_CORE, TRY, WITH, SWAP,
    NAME, CONSTANT, CALL, ATTRIBUTE, SUBSCRIPT,
    BIN_OP, UNARY_OP, COMPARE, IF_EXP, BOOL_OP,
    LIST, DICT, SET, TUPLE, LIST_COMP,
    UNBOX,
    STATIC_RANGE_FOR_PLAN, RUNTIME_ITER_FOR_PLAN,
    NAME_TARGET, TUPLE_TARGET,
    ASSIGNMENT_KINDS,
)


def _is_function_like_kind(kind: str) -> bool:
    return kind == FUNCTION_DEF or kind == CLOSURE_DEF


def _is_function_like(node: JsonVal) -> bool:
    return isinstance(node, dict) and _is_function_like_kind(jv_str(node.get("kind", "")))

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
                replaced_list: list[JsonVal] = replaced
                for elem in replaced_list:
                    result.append(elem)
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
            value_node: Node = {}
            value_node["kind"] = CONSTANT
            value_node["value"] = None
            value_node["resolved_type"] = "None"
            value = value_node
        recv: Node = {}
        recv["kind"] = NAME
        recv["id"] = acc
        recv["resolved_type"] = list_type
        func_attr: Node = {}
        func_attr["kind"] = ATTRIBUTE
        func_attr["value"] = recv
        func_attr["attr"] = "append"
        call_args: list[JsonVal] = []
        call_args.append(value)
        call_node: Node = {}
        call_node["kind"] = CALL
        call_node["func"] = func_attr
        call_node["args"] = call_args
        call_node["resolved_type"] = "None"
        ac: Node = {}
        ac["kind"] = EXPR
        ac["value"] = call_node
        span = nd.get("source_span")
        if isinstance(span, dict):
            ac["source_span"] = span
        return ac
    out: Node = {}
    for key in nd.keys():
        key_s: str = key if isinstance(key, str) else ""
        if key_s == "":
            continue
        val = nd[key_s]
        if key_s == "body" or key_s == "orelse" or key_s == "finalbody":
            out[key_s] = _replace_yield_with_append(val, acc, list_type)
        elif key_s == "handlers" and isinstance(val, list):
            handlers: list[JsonVal] = cast(list[JsonVal], val)
            hs: list[JsonVal] = []
            for h in handlers:
                if isinstance(h, dict):
                    hd: Node = h
                    nh: Node = {}
                    for hk in hd.keys():
                        hk_s: str = hk if isinstance(hk, str) else ""
                        if hk_s != "":
                            nh[hk_s] = hd[hk_s]
                    if "body" in nh:
                        nh["body"] = _replace_yield_with_append(nh["body"], acc, list_type)
                    hs.append(nh)
                else:
                    hs.append(h)
            out[key_s] = hs
        else:
            out[key_s] = val
    return out


def _lower_generator_function(func: Node) -> None:
    body = func.get("body")
    if not isinstance(body, list):
        return
    ret_type: str = jv_str(func.get("return_type", ""))
    elem_type = "unknown"
    if ret_type.startswith("list[") and ret_type.endswith("]"):
        elem_type = ret_type[5:-1]
    elif ret_type not in ("", "unknown"):
        elem_type = ret_type
        func["return_type"] = "list[" + ret_type + "]"
    acc = "__yield_values"
    lt = "list[" + elem_type + "]"
    target: Node = {}
    target["kind"] = NAME
    target["id"] = acc
    target["resolved_type"] = lt
    list_value: Node = {}
    list_value["kind"] = LIST
    list_value["elements"] = []
    list_value["resolved_type"] = lt
    init: Node = {}
    init["kind"] = ANN_ASSIGN
    init["target"] = target
    init["annotation"] = lt
    init["decl_type"] = lt
    init["declare"] = True
    init["value"] = list_value
    new_body = _replace_yield_with_append(body, acc, lt)
    if not isinstance(new_body, list):
        new_body = body
    new_body_list: list[JsonVal] = cast(list[JsonVal], new_body) if isinstance(new_body, list) else cast(list[JsonVal], body)
    ret_name: Node = {}
    ret_name["kind"] = NAME
    ret_name["id"] = acc
    ret_name["resolved_type"] = lt
    ret_stmt: Node = {}
    ret_stmt["kind"] = RETURN
    ret_stmt["value"] = ret_name
    final_body: list[JsonVal] = [init]
    for stmt in new_body_list:
        final_body.append(stmt)
    final_body.append(ret_stmt)
    func["body"] = final_body


def _yield_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        for item in node:
            _yield_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind", "")
    if _is_function_like_kind(kind):
        body = nd.get("body")
        if isinstance(body, list) and _contains_yield(body):
            _lower_generator_function(nd)
        body2 = nd.get("body")
        if isinstance(body2, list):
            body2_list: list[JsonVal] = cast(list[JsonVal], body2)
            for s in body2_list:
                _yield_walk(s)
        return
    if kind in (CLASS_DEF, MODULE):
        body = nd.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            for s in body_list:
                _yield_walk(s)
        return
    for val in nd.values():
        if isinstance(val, dict):
            _yield_walk(val)
        elif isinstance(val, list):
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
            plan: Node = {}
            plan["kind"] = NAME_TARGET
            plan["id"] = target.get("id", "_")
            rt: str = jv_str(target.get("resolved_type", ""))
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
        if kind == TUPLE:
            elements = target.get("elements") or target.get("elts") or []
            eps: list[JsonVal] = []
            if isinstance(elements, list):
                for elem in elements:
                    eps.append(_build_lc_target_plan(elem))
            plan: Node = {}
            plan["kind"] = TUPLE_TARGET
            plan["elements"] = eps
            rt: str = jv_str(target.get("resolved_type", ""))
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
    out: Node = {}
    out["kind"] = NAME_TARGET
    out["id"] = "_"
    return out


def _expand_lc_to_stmts(lc: Node, result_name: str, annotation_type: str = "") -> list[Node]:
    rt: str = jv_str(lc.get("resolved_type", ""))
    if rt in ("", "unknown") or "unknown" in rt:
        if annotation_type != "":
            rt = annotation_type
        elif rt in ("", "unknown"):
            rt = "list[unknown]"
    target_node: Node = {}
    target_node["kind"] = NAME
    target_node["id"] = result_name
    target_node["resolved_type"] = rt
    value_node: Node = {}
    value_node["kind"] = LIST
    value_node["elements"] = []
    value_node["resolved_type"] = rt
    init: Node = {}
    init["kind"] = ANN_ASSIGN
    init["target"] = target_node
    init["annotation"] = rt
    init["decl_type"] = rt
    init["declare"] = True
    init["value"] = value_node
    elt = lc.get("elt")
    append_arg = deep_copy_json(elt) if elt is not None else None
    elem_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        elem_type = rt[5:-1]
    if isinstance(append_arg, dict) and elem_type != "":
        append_node: Node = cast(dict[str, JsonVal], append_arg)
        append_node["call_arg_type"] = elem_type
        append_kind = append_node.get("kind", "")
        append_rt: str = jv_str(append_node.get("resolved_type", ""))
        if append_kind == LIST and append_rt in ("", "unknown", "list[unknown]"):
            append_node["resolved_type"] = elem_type
        elif append_kind == DICT and append_rt in ("", "unknown", "dict[unknown,unknown]"):
            append_node["resolved_type"] = elem_type
        elif append_kind == SET and append_rt in ("", "unknown", "set[unknown]"):
            append_node["resolved_type"] = elem_type
    generators = lc.get("generators", [])
    if not isinstance(generators, list):
        generators = []
    generator_list: list[JsonVal] = cast(list[JsonVal], generators)
    recv: Node = {}
    recv["kind"] = NAME
    recv["id"] = result_name
    recv["resolved_type"] = rt
    append_func: Node = {}
    append_func["kind"] = ATTRIBUTE
    append_func["value"] = recv
    append_func["attr"] = "append"
    append_args: list[JsonVal] = []
    if append_arg is not None:
        append_args.append(append_arg)
    append_call: Node = {}
    append_call["kind"] = CALL
    append_call["func"] = append_func
    append_call["args"] = append_args
    append_call["resolved_type"] = "None"
    append_stmt: Node = {}
    append_stmt["kind"] = EXPR
    append_stmt["value"] = append_call
    body: list[JsonVal] = [append_stmt]
    for gen_idx in range(len(generator_list) - 1, -1, -1):
        gen = generator_list[gen_idx]
        if not isinstance(gen, dict):
            continue
        gen_node: Node = cast(dict[str, JsonVal], gen)
        ifs = gen_node.get("ifs")
        if isinstance(ifs, list):
            ifs_list: list[JsonVal] = cast(list[JsonVal], ifs)
            if len(ifs_list) > 0:
                for cond_idx in range(len(ifs_list) - 1, -1, -1):
                    cond = ifs_list[cond_idx]
                    if isinstance(cond, dict):
                        if_stmt: Node = {}
                        if_stmt["kind"] = IF
                        if_stmt["test"] = deep_copy_json(cond)
                        if_stmt["body"] = body
                        if_stmt["orelse"] = []
                        body2: list[JsonVal] = []
                        body2.append(if_stmt)
                        body = body2
        target = gen_node.get("target")
        iter_expr = gen_node.get("iter")
        iter_kind = ""
        iter_node: Node = {}
        if isinstance(iter_expr, dict):
            iter_node = cast(dict[str, JsonVal], iter_expr)
            iter_kind = jv_str(iter_node.get("kind", ""))
        tp = _build_lc_target_plan(target)
        if iter_kind in ("RangeExpr", FOR_RANGE):
            iter_plan: Node = {}
            iter_plan["kind"] = STATIC_RANGE_FOR_PLAN
            start_default: Node = {}
            start_default["kind"] = CONSTANT
            start_default["value"] = 0
            start_default["resolved_type"] = "int64"
            stop_default: Node = {}
            stop_default["kind"] = CONSTANT
            stop_default["value"] = 0
            step_default: Node = {}
            step_default["kind"] = CONSTANT
            step_default["value"] = 1
            step_default["resolved_type"] = "int64"
            iter_plan["start"] = deep_copy_json(iter_node.get("start", start_default))
            iter_plan["stop"] = deep_copy_json(iter_node.get("stop", stop_default))
            iter_plan["step"] = deep_copy_json(iter_node.get("step", step_default))
            fs: Node = {}
            fs["kind"] = FOR_CORE
            fs["iter_mode"] = "static_fastpath"
            fs["iter_plan"] = iter_plan
            fs["target_plan"] = tp
            fs["body"] = body
            fs["orelse"] = []
        else:
            iter_plan: Node = {}
            iter_plan["kind"] = RUNTIME_ITER_FOR_PLAN
            if iter_expr:
                iter_plan["iter_expr"] = deep_copy_json(iter_expr)
            else:
                empty_name: Node = {}
                empty_name["kind"] = NAME
                empty_name["id"] = "__empty"
                iter_plan["iter_expr"] = empty_name
            iter_plan["dispatch_mode"] = "generic"
            iter_plan["init_op"] = "ObjIterInit"
            iter_plan["next_op"] = "ObjIterNext"
            fs: Node = {}
            fs["kind"] = FOR_CORE
            fs["iter_mode"] = "runtime_protocol"
            fs["iter_plan"] = iter_plan
            fs["target_plan"] = tp
            fs["body"] = body
            fs["orelse"] = []
        body3: list[JsonVal] = []
        body3.append(fs)
        body = body3
    out: list[Node] = [init]
    for stmt in body:
        if isinstance(stmt, dict):
            out.append(cast(dict[str, JsonVal], stmt))
    return out


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
                    tn = jv_str(target.get("id", ""))
                cn = tn if tn != "" else ctx.next_comp_name()
                at = ""
                if kind == ANN_ASSIGN:
                    ann = stmt.get("annotation")
                    if isinstance(ann, str) and ann != "" and "unknown" not in ann:
                        at = ann
                expanded = _expand_lc_to_stmts(value, cn, at)
                if cn != tn and tn != "":
                    assign_value: Node = {}
                    assign_value["kind"] = NAME
                    assign_value["id"] = cn
                    assign_value["resolved_type"] = jv_str(value.get("resolved_type", ""))
                    assign_stmt: Node = {}
                    assign_stmt["kind"] = ASSIGN
                    assign_stmt["target"] = deep_copy_json(target)
                    assign_stmt["value"] = assign_value
                    expanded.append(assign_stmt)
                for ex in expanded:
                    result.append(ex)
                continue
        if kind == EXPR:
            ev = stmt.get("value")
            if isinstance(ev, dict) and ev.get("kind") == LIST_COMP:
                tmp: str = ctx.next_comp_name()
                expanded_expr = _expand_lc_to_stmts(ev, tmp)
                for ex in expanded_expr:
                    result.append(ex)
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
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        module["body"] = _lc_in_stmts(body_list, ctx)
    return module


# ===========================================================================
# nested FunctionDef -> ClosureDef lowering
# ===========================================================================

def _collect_function_locals(stmts: list[JsonVal], out: dict[str, str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _sk(stmt)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            name = jv_str(stmt.get("name", ""))
            if name != "" and name not in out:
                if kind == CLASS_DEF:
                    out[name] = name
                else:
                    out[name] = _closure_callable_type(stmt)
            continue
        if kind == VAR_DECL:
            name2 = jv_str(stmt.get("name", ""))
            type2 = jv_str(stmt.get("type", ""))
            if name2 != "" and name2 not in out:
                out[name2] = type2
        elif kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
            _collect_assign_names(stmt, out)
        elif kind == FOR:
            _collect_target_local_types(stmt.get("target"), jv_str(stmt.get("target_type", "")), out)
        elif kind == FOR_RANGE:
            _collect_target_local_types(stmt.get("target"), jv_str(stmt.get("target_type", "int64")), out)
        elif kind == FOR_CORE:
            _collect_target_plan_local_types(stmt.get("target_plan"), out)
        elif kind == WITH:
            items = stmt.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    _collect_target_local_types(item.get("optional_vars"), "", out)
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                _collect_function_locals(nested, out)
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                name3 = jv_str(handler.get("name", ""))
                if name3 != "" and name3 not in out:
                    out[name3] = "BaseException"
                hbody = handler.get("body")
                if isinstance(hbody, list):
                    _collect_function_locals(hbody, out)


def _collect_target_local_types(target: JsonVal, inferred_type: str, out: dict[str, str]) -> None:
    if not isinstance(target, dict):
        return
    kind = _sk(target)
    if kind == NAME:
        name = jv_str(target.get("id", ""))
        if name != "" and name not in out:
            target_type = jv_str(target.get("resolved_type", ""))
            out[name] = target_type if target_type != "" else inferred_type
        return
    if kind == TUPLE:
        elements = target.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _collect_target_local_types(elem, inferred_type, out)


def _collect_target_plan_local_types(target_plan: JsonVal, out: dict[str, str]) -> None:
    if not isinstance(target_plan, dict):
        return
    kind = _sk(target_plan)
    if kind == NAME_TARGET:
        name = jv_str(target_plan.get("id", ""))
        if name != "" and name not in out:
            out[name] = jv_str(target_plan.get("target_type", ""))
        return
    if kind == TUPLE_TARGET:
        elements = target_plan.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _collect_target_plan_local_types(elem, out)


def _collect_function_scope_types(func: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    self_name = jv_str(func.get("name", ""))
    if self_name != "":
        out[self_name] = _closure_callable_type(func)
    arg_types = func.get("arg_types")
    if isinstance(arg_types, dict):
        for name, value in arg_types.items():
            if isinstance(name, str) and name != "" and isinstance(value, str):
                out[name] = value
    captures = func.get("captures")
    if isinstance(captures, list):
        capture_list: list[JsonVal] = cast(list[JsonVal], captures)
        for capture in capture_list:
            if not isinstance(capture, dict):
                continue
            capture_node: Node = cast(dict[str, JsonVal], capture)
            name2 = jv_str(capture_node.get("name", ""))
            type2 = jv_str(capture_node.get("type", ""))
            if name2 != "" and name2 not in out:
                out[name2] = type2
    body = func.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        _collect_function_locals(body_list, out)
    return out


def _collect_function_reassigned_names(func: Node) -> set[str]:
    counts: dict[str, int] = {}
    body = func.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        _collect_reassigned_lexical(body_list, counts)
    out: set[str] = set()
    arg_order = func.get("arg_order")
    param_names: set[str] = set()
    if isinstance(arg_order, list):
        arg_order_list: list[JsonVal] = cast(list[JsonVal], arg_order)
        for arg in arg_order_list:
            if isinstance(arg, str) and arg != "":
                param_names.add(arg)
    for name, count in counts.items():
        if name in param_names:
            out.add(name)
        elif count > 1:
            out.add(name)
    return out


def _bump_reassigned(out: dict[str, int], name: str) -> None:
    out[name] = out.get(name, 0) + 1


def _collect_reassigned_lexical(stmts: list[JsonVal], out: dict[str, int]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _sk(stmt)
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == NAME:
                name = target.get("id")
                if isinstance(name, str) and name != "":
                    _bump_reassigned(out, name)
            elif isinstance(target, dict) and target.get("kind") == TUPLE:
                _collect_target_write_counts(target, out)
        elif kind == AUG_ASSIGN:
            target2 = stmt.get("target")
            if isinstance(target2, dict) and target2.get("kind") == NAME:
                name2 = target2.get("id")
                if isinstance(name2, str) and name2 != "":
                    _bump_reassigned(out, name2)
        elif kind == FOR or kind == FOR_RANGE:
            _collect_target_write_counts(stmt.get("target"), out)
        elif kind == FOR_CORE:
            _collect_target_plan_write_counts(stmt.get("target_plan"), out)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            continue
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                nested_list: list[JsonVal] = cast(list[JsonVal], nested)
                _collect_reassigned_lexical(nested_list, out)
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            handler_list: list[JsonVal] = cast(list[JsonVal], handlers)
            for handler in handler_list:
                if isinstance(handler, dict):
                    handler_node: Node = cast(dict[str, JsonVal], handler)
                    hbody = handler_node.get("body")
                    if isinstance(hbody, list):
                        hbody_list: list[JsonVal] = cast(list[JsonVal], hbody)
                        _collect_reassigned_lexical(hbody_list, out)


def _collect_target_write_counts(target: JsonVal, out: dict[str, int]) -> None:
    if not isinstance(target, dict):
        return
    kind = _sk(target)
    if kind == NAME:
        name = jv_str(target.get("id", ""))
        if name != "":
            _bump_reassigned(out, name)
        return
    if kind == TUPLE:
        elements = target.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _collect_target_write_counts(elem, out)


def _collect_target_plan_write_counts(target_plan: JsonVal, out: dict[str, int]) -> None:
    if not isinstance(target_plan, dict):
        return
    kind = _sk(target_plan)
    if kind == NAME_TARGET:
        name = jv_str(target_plan.get("id", ""))
        if name != "":
            _bump_reassigned(out, name)
        return
    if kind == TUPLE_TARGET:
        elements = target_plan.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _collect_target_plan_write_counts(elem, out)


def _collect_name_refs_lexical(node: JsonVal, out: set[str], *, descend_into_root: bool = True) -> None:
    if isinstance(node, list):
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for item in node_list:
            _collect_name_refs_lexical(item, out, descend_into_root=True)
        return
    if not isinstance(node, dict):
        return
    kind = _sk(node)
    if not descend_into_root and (_is_function_like_kind(kind) or kind == CLASS_DEF):
        return
    if kind == NAME:
        name = jv_str(node.get("id", ""))
        if name != "":
            out.add(name)
    for key, value in node.items():
        if key == "body" and (_is_function_like_kind(kind) or kind == CLASS_DEF):
            if descend_into_root and isinstance(value, list):
                value_list: list[JsonVal] = cast(list[JsonVal], value)
                for item in value_list:
                    _collect_name_refs_lexical(item, out, descend_into_root=False)
            continue
        if isinstance(value, dict):
            _collect_name_refs_lexical(value, out, descend_into_root=True)
        elif isinstance(value, list):
            _collect_name_refs_lexical(value, out, descend_into_root=True)


def _closure_callable_type(node: Node) -> str:
    arg_order = node.get("arg_order")
    arg_types = node.get("arg_types")
    params: list[str] = []
    if isinstance(arg_order, list) and isinstance(arg_types, dict):
        arg_order_list: list[JsonVal] = cast(list[JsonVal], arg_order)
        arg_types_node: Node = cast(dict[str, JsonVal], arg_types)
        for arg in arg_order_list:
            if not isinstance(arg, str) or arg == "":
                continue
            if arg == "self":
                continue
            arg_type = arg_types_node.get(arg)
            params.append(arg_type if isinstance(arg_type, str) and arg_type != "" else "unknown")
    ret = jv_str(node.get("return_type", ""))
    if ret == "":
        ret = "unknown"
    return "callable[[" + ",".join(params) + "]," + ret + "]"


def _closure_capture_entries(
    visible_types: dict[str, str],
    visible_mutable: set[str],
    func: Node,
) -> tuple[list[Node], bool]:
    local_types = _collect_function_scope_types(func)
    used_names: set[str] = set()
    defaults = func.get("arg_defaults")
    if isinstance(defaults, dict):
        _collect_name_refs_lexical(defaults, used_names, descend_into_root=True)
    body = func.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        for stmt in body_list:
            _collect_name_refs_lexical(stmt, used_names, descend_into_root=False)
    captures: list[Node] = []
    for name in sorted(used_names):
        if name in local_types or name not in visible_types:
            continue
        capture_type = visible_types.get(name, "")
        capture_mode = "mutable" if name in visible_mutable else "readonly"
        capture: Node = {}
        capture["name"] = name
        capture["mode"] = capture_mode
        capture["type"] = capture_type
        captures.append(capture)
    return captures, jv_str(func.get("name", "")) in used_names


def _lower_closure_stmt_list(
    stmts: list[JsonVal],
    visible_types: dict[str, str],
    visible_mutable: set[str],
) -> list[JsonVal]:
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = _sk(stmt)
        if kind == FUNCTION_DEF:
            captures, is_recursive = _closure_capture_entries(visible_types, visible_mutable, stmt)
            stmt["kind"] = CLOSURE_DEF
            stmt["captures"] = captures
            capture_types: dict[str, str] = {}
            capture_modes: dict[str, str] = {}
            for capture in captures:
                capture_name = jv_str(capture.get("name", ""))
                if capture_name == "":
                    continue
                capture_types[capture_name] = jv_str(capture.get("type", ""))
                capture_modes[capture_name] = jv_str(capture.get("mode", ""))
            stmt["capture_types"] = capture_types
            stmt["capture_modes"] = capture_modes
            if is_recursive:
                stmt["is_recursive"] = True
            _lower_closure_function(stmt, visible_types, visible_mutable)
            result.append(stmt)
            continue
        if kind == CLASS_DEF:
            body = stmt.get("body")
            if isinstance(body, list):
                body_list: list[JsonVal] = cast(list[JsonVal], body)
                class_visible: dict[str, str] = {}
                for name, value in visible_types.items():
                    class_visible[name] = value
                class_name = jv_str(stmt.get("name", ""))
                if class_name != "":
                    class_visible[class_name] = class_name
                stmt["body"] = _lower_closure_stmt_list(body_list, class_visible, visible_mutable)
            result.append(stmt)
            continue
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                stmt[key] = _lower_closure_stmt_list(nested, visible_types, visible_mutable)
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            handler_list: list[JsonVal] = cast(list[JsonVal], handlers)
            for handler in handler_list:
                if not isinstance(handler, dict):
                    continue
                handler_node: Node = cast(dict[str, JsonVal], handler)
                hbody = handler_node.get("body")
                if isinstance(hbody, list):
                    hbody_list: list[JsonVal] = cast(list[JsonVal], hbody)
                    handler_node["body"] = _lower_closure_stmt_list(hbody_list, visible_types, visible_mutable)
        result.append(stmt)
    return result


def _lower_closure_function(
    func: Node,
    outer_visible_types: dict[str, str],
    outer_visible_mutable: set[str],
) -> None:
    body = func.get("body")
    if not isinstance(body, list):
        return
    body_list: list[JsonVal] = cast(list[JsonVal], body)
    current_visible: dict[str, str] = {}
    for name, value in outer_visible_types.items():
        current_visible[name] = value
    for name, value in _collect_function_scope_types(func).items():
        current_visible[name] = value
    current_mutable = set(outer_visible_mutable)
    current_mutable.update(_collect_function_reassigned_names(func))
    func["body"] = _lower_closure_stmt_list(body_list, current_visible, current_mutable)


def lower_nested_function_defs(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        for stmt in body_list:
            if isinstance(stmt, dict) and _is_function_like_kind(_sk(stmt)):
                _lower_closure_function(stmt, {}, set())
            elif isinstance(stmt, dict) and _sk(stmt) == CLASS_DEF:
                class_body = stmt.get("body")
                if isinstance(class_body, list):
                    class_body_list: list[JsonVal] = cast(list[JsonVal], class_body)
                    stmt["body"] = _lower_closure_stmt_list(class_body_list, {}, set())
    return module


# ===========================================================================
# default argument expansion
# ===========================================================================

def _collect_fn_sigs(module: Node) -> dict[str, Node]:
    sigs: dict[str, Node] = {}
    body = module.get("body")
    if not isinstance(body, list):
        return sigs
    body_list: list[JsonVal] = cast(list[JsonVal], body)
    for stmt in body_list:
        if isinstance(stmt, dict):
            _collect_sig_node(stmt, sigs, "")
    return sigs


def _collect_sig_node(node: Node, sigs: dict[str, Node], class_name: str) -> None:
    kind = node.get("kind", "")
    if _is_function_like_kind(kind):
        name: str = jv_str(node.get("name", ""))
        if name == "":
            return
        ao = node.get("arg_order")
        ad = node.get("arg_defaults")
        if not isinstance(ao, list):
            return
        ao_list: list[JsonVal] = cast(list[JsonVal], ao)
        sig: Node = {}
        sig["arg_order"] = ao_list
        if isinstance(ad, dict):
            sig["arg_defaults"] = cast(dict[str, JsonVal], ad)
        else:
            sig["arg_defaults"] = {}
        full = name
        if class_name != "":
            full = class_name + "." + name
        if class_name == "":
            sigs[name] = sig
        if full != name:
            sigs[full] = sig
        body = node.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            for s in body_list:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, "")
    elif kind == CLASS_DEF:
        cn: str = jv_str(node.get("name", ""))
        body = node.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            for s in body_list:
                if isinstance(s, dict):
                    _collect_sig_node(s, sigs, cn)
    elif kind == ASSIGN or kind == ANN_ASSIGN:
        target: JsonVal = node.get("target")
        if not isinstance(target, dict):
            targets = node.get("targets")
            if isinstance(targets, list):
                targets_list: list[JsonVal] = cast(list[JsonVal], targets)
                if len(targets_list) == 1 and isinstance(targets_list[0], dict):
                    target = cast(dict[str, JsonVal], targets_list[0])
        value = node.get("value")
        value_node2: Node = cast(dict[str, JsonVal], value) if isinstance(value, dict) else {}
        if (
            isinstance(target, dict)
            and target.get("kind") == NAME
            and isinstance(value, dict)
            and value_node2.get("kind") == "Lambda"
        ):
            target_node: Node = cast(dict[str, JsonVal], target)
            value_node: Node = value_node2
            lambda_name: str = jv_str(target_node.get("id", ""))
            args = value_node.get("args")
            if lambda_name != "" and isinstance(args, list):
                arg_order: list[str] = []
                arg_defaults: dict[str, JsonVal] = {}
                args_list: list[JsonVal] = cast(list[JsonVal], args)
                for arg in args_list:
                    if not isinstance(arg, dict):
                        continue
                    arg_node: Node = cast(dict[str, JsonVal], arg)
                    arg_name: str = jv_str(arg_node.get("arg", ""))
                    if arg_name == "":
                        continue
                    arg_order.append(arg_name)
                    default_node = arg_node.get("default")
                    if isinstance(default_node, dict):
                        arg_defaults[arg_name] = deep_copy_json(default_node)
                lambda_sig: Node = {}
                lambda_sig["arg_order"] = arg_order
                lambda_sig["arg_defaults"] = arg_defaults
                sigs[lambda_name] = lambda_sig


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
            func_node: Node = cast(dict[str, JsonVal], func)
            if func_node.get("kind") == NAME:
                cn = jv_str(func_node.get("id", ""))
            elif func_node.get("kind") == ATTRIBUTE:
                attr: str = jv_str(func_node.get("attr", ""))
                owner = func_node.get("value")
                if isinstance(owner, dict):
                    owner_node: Node = cast(dict[str, JsonVal], owner)
                    owner_type: str = jv_str(owner_node.get("resolved_type", ""))
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
                args_list: list[JsonVal] = cast(list[JsonVal], args)
                ao_list: list[JsonVal] = cast(list[JsonVal], ao)
                ad_node: Node = cast(dict[str, JsonVal], ad)
                ep: list[str] = []
                for p in ao_list:
                    if isinstance(p, str) and p != "self":
                        ep.append(p)
                ne = len(ep)
                kw_map: dict[str, JsonVal] = {}
                kws = nd.get("keywords")
                if isinstance(kws, list):
                    kw_list: list[JsonVal] = cast(list[JsonVal], kws)
                    for kw in kw_list:
                        if isinstance(kw, dict):
                            kw_node: Node = cast(dict[str, JsonVal], kw)
                            ka = jv_str(kw_node.get("arg", ""))
                            kv = kw_node.get("value")
                            if ka != "":
                                kw_map[ka] = kv
                if len(args_list) < ne:
                    for i in range(len(args_list), ne):
                        pn = ep[i]
                        if pn in kw_map:
                            kv2 = kw_map[pn]
                            args_list.append(deep_copy_json(kv2) if isinstance(kv2, dict) else kv2)
                        elif pn in ad_node:
                            dn = ad_node[pn]
                            if isinstance(dn, dict):
                                args_list.append(deep_copy_json(dn))
                    nd["args"] = args_list
                    if isinstance(kws, list) and len(kw_map) > 0:
                        remaining: list[JsonVal] = []
                        kw_list2: list[JsonVal] = cast(list[JsonVal], kws)
                        for kw in kw_list2:
                            if isinstance(kw, dict):
                                kw_node2: Node = cast(dict[str, JsonVal], kw)
                                ka = jv_str(kw_node2.get("arg", ""))
                                if ka in kw_map:
                                    continue
                            remaining.append(kw)
                        nd["keywords"] = remaining
    for v in nd.values():
        if isinstance(v, dict):
            _expand_defaults_walk(v, sigs)
        elif isinstance(v, list):
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
    value_node: Node = {}
    value_node["kind"] = NAME
    value_node["id"] = owner
    value_node["resolved_type"] = "tuple"
    slice_node: Node = {}
    slice_node["kind"] = CONSTANT
    slice_node["value"] = index
    slice_node["resolved_type"] = "int64"
    out: Node = {}
    out["kind"] = SUBSCRIPT
    out["value"] = value_node
    out["slice"] = slice_node
    out["resolved_type"] = elem_type if elem_type != "" else "unknown"
    return out


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
        if isinstance(tp, dict):
            tp_node: Node = cast(dict[str, JsonVal], tp)
            if tp_node.get("kind") != TUPLE_TARGET:
                pass
            else:
                elements = tp_node.get("elements")
                if isinstance(elements, list):
                    elements_list: list[JsonVal] = cast(list[JsonVal], elements)
                    if len(elements_list) < 2:
                        pass
                    else:
                        tmp = ctx.next_tte_name()
                        assigns: list[JsonVal] = []
                        direct_names: list[JsonVal] = []
                        for i, elem in enumerate(elements_list):
                            if not isinstance(elem, dict):
                                continue
                            elem_node: Node = cast(dict[str, JsonVal], elem)
                            if elem_node.get("kind") != NAME_TARGET:
                                continue
                            en = elem_node.get("id", "")
                            et = elem_node.get("target_type", "")
                            if not isinstance(en, str) or en == "":
                                continue
                            if not isinstance(et, str):
                                et = ""
                            target_node: Node = {}
                            target_node["kind"] = NAME
                            target_node["id"] = en
                            target_node["resolved_type"] = et if et != "" else "unknown"
                            assign: Node = {}
                            assign["kind"] = ASSIGN
                            assign["target"] = target_node
                            assign["value"] = _tte_subscript(tmp, i, et)
                            assign["decl_type"] = et if et != "" else "unknown"
                            assign["declare"] = True
                            assigns.append(assign)
                            direct_names.append(en)
                        tp_out: Node = {}
                        tp_out["kind"] = NAME_TARGET
                        tp_out["id"] = tmp
                        tp_out["target_type"] = tp_node.get("target_type", "")
                        tp_out["direct_unpack_names"] = direct_names
                        tp_out["tuple_expanded"] = True
                        nd["target_plan"] = tp_out
                        body = nd.get("body")
                        if isinstance(body, list):
                            body_list: list[JsonVal] = cast(list[JsonVal], body)
                            new_body: list[JsonVal] = []
                            for stmt in assigns:
                                new_body.append(stmt)
                            for stmt in body_list:
                                new_body.append(stmt)
                            nd["body"] = new_body
    for v in nd.values():
        if isinstance(v, dict):
            _tte_walk(v, ctx)
        elif isinstance(v, list):
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
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
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
        target_node: Node = cast(dict[str, JsonVal], target)
        elements = target_node.get("elements")
        if not isinstance(elements, list):
            result.append(stmt)
            continue
        elements_list: list[JsonVal] = cast(list[JsonVal], elements)
        if len(elements_list) == 0:
            result.append(stmt)
            continue
        value = stmt.get("value")

        # Detect swap pattern: a, b = b, a → Swap node
        if isinstance(value, dict) and value.get("kind") == TUPLE and len(elements_list) == 2:
            val_elements = value.get("elements")
            if isinstance(val_elements, list) and len(val_elements) == 2:
                val_elements_list: list[JsonVal] = cast(list[JsonVal], val_elements)
                le0 = cast(dict[str, JsonVal], elements_list[0]) if isinstance(elements_list[0], dict) else {}
                le1 = cast(dict[str, JsonVal], elements_list[1]) if isinstance(elements_list[1], dict) else {}
                re0 = cast(dict[str, JsonVal], val_elements_list[0]) if isinstance(val_elements_list[0], dict) else {}
                re1 = cast(dict[str, JsonVal], val_elements_list[1]) if isinstance(val_elements_list[1], dict) else {}
                # Check if targets[0]=rhs[1] and targets[1]=rhs[0] (cross reference)
                if _same_lvalue(le0, re1) and _same_lvalue(le1, re0):
                    swap_node: Node = {}
                    swap_node["kind"] = SWAP
                    swap_node["left"] = deep_copy_json(le0)
                    swap_node["right"] = deep_copy_json(le1)
                    result.append(swap_node)
                    continue

        # Generate: _tmp = value
        tmp_name: str = ctx.next_tuple_tmp_name()
        val_rt = ""
        if isinstance(value, dict):
            value_node: Node = cast(dict[str, JsonVal], value)
            val_rt = jv_str(value_node.get("resolved_type"))
        target_rt = jv_str(target_node.get("resolved_type"))
        tmp_value, tmp_rt = _make_tuple_unpack_source(value, val_rt, target_rt)
        tmp_target: Node = {}
        tmp_target["kind"] = NAME
        tmp_target["id"] = tmp_name
        tmp_target["resolved_type"] = tmp_rt
        tmp_assign: Node = {}
        tmp_assign["kind"] = ASSIGN
        tmp_assign["target"] = tmp_target
        tmp_assign["value"] = tmp_value
        tmp_assign["declare"] = True
        tmp_assign["decl_type"] = tmp_rt
        result.append(tmp_assign)

        # Parse tuple element types from the effective tuple source.
        elem_types: list[str] = _parse_tuple_element_types(tmp_rt)
        if len(elem_types) == 0:
            elem_types = _parse_tuple_element_types(target_rt)

        # Generate: x = _tmp[0], y = _tmp[1], ...
        for i, elem in enumerate(elements_list):
            if not isinstance(elem, dict):
                continue
            elem_name = elem.get("id")
            if not isinstance(elem_name, str) or elem_name == "":
                continue
            elem_rt = elem_types[i] if i < len(elem_types) else "unknown"
            idx_value: Node = {}
            idx_value["kind"] = NAME
            idx_value["id"] = tmp_name
            idx_value["resolved_type"] = tmp_rt
            idx_slice: Node = {}
            idx_slice["kind"] = CONSTANT
            idx_slice["value"] = i
            idx_slice["resolved_type"] = "int64"
            idx_node: Node = {}
            idx_node["kind"] = SUBSCRIPT
            idx_node["value"] = idx_value
            idx_node["slice"] = idx_slice
            idx_node["resolved_type"] = elem_rt
            elem_target: Node = {}
            elem_target["kind"] = NAME
            elem_target["id"] = elem_name
            elem_target["resolved_type"] = elem_rt
            elem_assign: Node = {}
            elem_assign["kind"] = ASSIGN
            elem_assign["target"] = elem_target
            elem_assign["value"] = idx_node
            elem_assign["declare"] = True
            elem_assign["decl_type"] = elem_rt
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
        av_node: Node = {}
        bv_node: Node = {}
        asl_node: Node = {}
        bsl_node: Node = {}
        if isinstance(av, dict):
            av_node = cast(dict[str, JsonVal], av)
        if isinstance(bv, dict):
            bv_node = cast(dict[str, JsonVal], bv)
        if isinstance(asl, dict):
            asl_node = cast(dict[str, JsonVal], asl)
        if isinstance(bsl, dict):
            bsl_node = cast(dict[str, JsonVal], bsl)
        return _same_lvalue(av_node, bv_node) and _same_lvalue(asl_node, bsl_node)
    if ak == "Constant":
        return a.get("value") == b.get("value")
    if ak == ATTRIBUTE:
        av = a.get("value")
        bv = b.get("value")
        av_node: Node = {}
        bv_node: Node = {}
        if isinstance(av, dict):
            av_node = cast(dict[str, JsonVal], av)
        if isinstance(bv, dict):
            bv_node = cast(dict[str, JsonVal], bv)
        return (a.get("attr", "") == b.get("attr", "") and
                _same_lvalue(av_node, bv_node))
    if ak == BIN_OP:
        al = a.get("left")
        bl = b.get("left")
        ar = a.get("right")
        br = b.get("right")
        al_node: Node = {}
        bl_node: Node = {}
        ar_node: Node = {}
        br_node: Node = {}
        if isinstance(al, dict):
            al_node = cast(dict[str, JsonVal], al)
        if isinstance(bl, dict):
            bl_node = cast(dict[str, JsonVal], bl)
        if isinstance(ar, dict):
            ar_node = cast(dict[str, JsonVal], ar)
        if isinstance(br, dict):
            br_node = cast(dict[str, JsonVal], br)
        return (a.get("op", "") == b.get("op", "") and
                _same_lvalue(al_node, bl_node) and
                _same_lvalue(ar_node, br_node))
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
    normalized_source: str = normalize_type_name(source_type)
    normalized_target: str = normalize_type_name(target_type)
    if normalized_target.startswith("tuple["):
        if normalized_source.startswith("tuple["):
            return value, normalized_source
        if "None" in normalized_source.split(" | "):
            out: Node = {}
            out["kind"] = UNBOX
            out["value"] = deep_copy_json(value)
            out["resolved_type"] = normalized_target
            out["borrow_kind"] = "value"
            out["casts"] = []
            out["target"] = normalized_target
            out["on_fail"] = "raise"
            if isinstance(value, dict):
                value_node: Node = cast(dict[str, JsonVal], value)
                span = value_node.get("source_span")
                if isinstance(span, dict):
                    out["source_span"] = span
                repr_text = value_node.get("repr")
                if isinstance(repr_text, str) and repr_text != "":
                    out["repr"] = repr_text
            return out, normalized_target
    return value, normalized_source


def expand_tuple_unpack(module: Node, ctx: CompileContext) -> Node:
    """Expand all Assign(target=Tuple, ...) in the module."""
    body = module.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        module["body"] = _expand_tuple_unpack_in_stmts(body_list, ctx)
    mg = module.get("main_guard_body")
    if isinstance(mg, list):
        mg_list: list[JsonVal] = cast(list[JsonVal], mg)
        module["main_guard_body"] = _expand_tuple_unpack_in_stmts(mg_list, ctx)
    return module


# ===========================================================================
# enumerate lowering
# ===========================================================================

def _try_lower_enum_forcore(stmt: Node, ctx: CompileContext) -> JsonVal:
    ip = stmt.get("iter_plan")
    if not isinstance(ip, dict):
        return None
    ip_node: Node = cast(dict[str, JsonVal], ip)
    if ip_node.get("kind") != RUNTIME_ITER_FOR_PLAN:
        return None
    ie = ip_node.get("iter_expr")
    if not isinstance(ie, dict):
        return None
    ie_node: Node = cast(dict[str, JsonVal], ie)
    st: str = jv_str(ie_node.get("semantic_tag", ""))
    is_enum = st == "iter.enumerate"
    if not is_enum:
        func = ie_node.get("func")
        if isinstance(func, dict):
            func_node: Node = cast(dict[str, JsonVal], func)
            is_enum = func_node.get("id") == "enumerate" or func_node.get("attr") == "enumerate"
    if not is_enum:
        return None
    args = ie_node.get("args", [])
    if not isinstance(args, list):
        return None
    args_list: list[JsonVal] = cast(list[JsonVal], args)
    if len(args_list) < 1:
        return None
    iterable = args_list[0]
    start_val = 0
    if len(args_list) >= 2:
        sa = args_list[1]
        if isinstance(sa, dict) and sa.get("kind") == CONSTANT:
            sa_node: Node = cast(dict[str, JsonVal], sa)
            sv = sa_node.get("value")
            if isinstance(sv, int):
                start_val = sv
    tp = stmt.get("target_plan", {})
    if not isinstance(tp, dict):
        return None
    tp_node: Node = cast(dict[str, JsonVal], tp)
    body = stmt.get("body", [])
    if not isinstance(body, list):
        return None
    body_list: list[JsonVal] = cast(list[JsonVal], body)
    idx_name = ""
    val_name = ""
    remaining: list[JsonVal] = []
    iter_tmp: str = jv_str(tp_node.get("id", ""))
    for s in body_list:
        if not isinstance(s, dict):
            remaining.append(s)
            continue
        s_node: Node = cast(dict[str, JsonVal], s)
        if s_node.get("kind") == ASSIGN:
            target = s_node.get("target")
            value = s_node.get("value")
            if isinstance(target, dict) and isinstance(value, dict):
                target_node: Node = cast(dict[str, JsonVal], target)
                value_node: Node = cast(dict[str, JsonVal], value)
                if value_node.get("kind") != SUBSCRIPT:
                    remaining.append(s)
                    continue
                sl = value_node.get("slice")
                if isinstance(sl, dict):
                    sl_node: Node = cast(dict[str, JsonVal], sl)
                    if sl_node.get("kind") != CONSTANT:
                        remaining.append(s)
                        continue
                    idx_v = sl_node.get("value")
                    owner = value_node.get("value")
                    if isinstance(owner, dict):
                        owner_node: Node = cast(dict[str, JsonVal], owner)
                        if jv_str(owner_node.get("id", "")) != iter_tmp:
                            remaining.append(s)
                            continue
                        name: str = jv_str(target_node.get("id", ""))
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
    init_target: Node = {}
    init_target["kind"] = NAME
    init_target["id"] = counter
    init_target["resolved_type"] = "int64"
    init_value: Node = {}
    init_value["kind"] = CONSTANT
    init_value["value"] = start_val
    init_value["resolved_type"] = "int64"
    init: Node = {}
    init["kind"] = ASSIGN
    init["target"] = init_target
    init["value"] = init_value
    init["decl_type"] = "int64"
    init["declare"] = True
    raw_tt: str = jv_str(tp_node.get("target_type", ""))
    vtt = raw_tt
    if raw_tt.startswith("tuple[") and raw_tt.endswith("]"):
        inner = raw_tt[6:-1]
        parts = _split_comma_types(inner)
        if len(parts) >= 2:
            vtt = parts[1]
    ntp: Node = {}
    ntp["kind"] = NAME_TARGET
    ntp["id"] = val_name
    ntp["target_type"] = vtt
    nip: Node = {}
    nip["kind"] = RUNTIME_ITER_FOR_PLAN
    nip["iter_expr"] = deep_copy_json(iterable)
    nip["dispatch_mode"] = ip_node.get("dispatch_mode", "native")
    nip["init_op"] = "ObjIterInit"
    nip["next_op"] = "ObjIterNext"
    assign_target: Node = {}
    assign_target["kind"] = NAME
    assign_target["id"] = idx_name
    assign_target["resolved_type"] = "int64"
    assign_value: Node = {}
    assign_value["kind"] = NAME
    assign_value["id"] = counter
    assign_value["resolved_type"] = "int64"
    assign_idx: Node = {}
    assign_idx["kind"] = ASSIGN
    assign_idx["target"] = assign_target
    assign_idx["value"] = assign_value
    assign_idx["decl_type"] = "int64"
    assign_idx["declare"] = True
    increment_target: Node = {}
    increment_target["kind"] = NAME
    increment_target["id"] = counter
    increment_target["resolved_type"] = "int64"
    increment_value: Node = {}
    increment_value["kind"] = CONSTANT
    increment_value["value"] = 1
    increment_value["resolved_type"] = "int64"
    increment: Node = {}
    increment["kind"] = AUG_ASSIGN
    increment["target"] = increment_target
    increment["op"] = "Add"
    increment["value"] = increment_value
    nb: list[JsonVal] = []
    nb.append(assign_idx)
    for item in remaining:
        nb.append(item)
    nb.append(increment)
    nf: Node = {}
    nf["kind"] = FOR_CORE
    nf["iter_mode"] = stmt.get("iter_mode", "runtime_protocol")
    nf["iter_plan"] = nip
    nf["target_plan"] = ntp
    nf["body"] = nb
    nf["orelse"] = stmt.get("orelse", [])
    out_nodes: list[JsonVal] = []
    out_nodes.append(init)
    out_nodes.append(nf)
    return out_nodes


def _enum_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = []
    for stmt in stmts:
        if not isinstance(stmt, dict):
            result.append(stmt)
            continue
        kind = stmt.get("kind", "")
        if kind == FOR_CORE:
            expanded = _try_lower_enum_forcore(stmt, ctx)
            if isinstance(expanded, list):
                expanded_list: list[JsonVal] = cast(list[JsonVal], expanded)
                for item in expanded_list:
                    result.append(item)
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
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        module["body"] = _enum_in_stmts(body_list, ctx)
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
        target_node: Node = cast(dict[str, JsonVal], target)
        rt = target_node.get("resolved_type")
        if isinstance(rt, str) and rt.strip() not in ("", "unknown"):
            return rt.strip()
    # Also check value's resolved_type (for computed assignments)
    value = stmt.get("value")
    if isinstance(value, dict):
        value_node: Node = cast(dict[str, JsonVal], value)
        vrt = value_node.get("resolved_type")
        if isinstance(vrt, str) and vrt.strip() not in ("", "unknown"):
            return vrt.strip()
    return ""


def _collect_assign_names(stmt: Node, out: dict[str, str]) -> None:
    target = stmt.get("target")
    if isinstance(target, dict):
        target_node: Node = cast(dict[str, JsonVal], target)
        tk = target_node.get("kind")
        if tk == NAME:
            n = target_node.get("id")
            if isinstance(n, str) and n != "" and n not in out:
                out[n] = _resolve_atype(stmt)
        elif tk == TUPLE:
            _collect_tuple_tgt_names(target_node, stmt, out)
    targets = stmt.get("targets")
    if isinstance(targets, list):
        targets_list: list[JsonVal] = cast(list[JsonVal], targets)
        for t in targets_list:
            if isinstance(t, dict):
                t_node: Node = cast(dict[str, JsonVal], t)
                if t_node.get("kind") == NAME:
                    n = t_node.get("id")
                    if isinstance(n, str) and n != "" and n not in out:
                        out[n] = _resolve_atype(stmt)
                elif t_node.get("kind") == TUPLE:
                    _collect_tuple_tgt_names(t_node, stmt, out)


def _collect_tuple_tgt_names(tn: Node, stmt: Node, out: dict[str, str]) -> None:
    elements = tn.get("elements")
    if not isinstance(elements, list):
        return
    element_list: list[JsonVal] = cast(list[JsonVal], elements)
    vt = _resolve_atype(stmt)
    ets: list[str] = []
    if vt.startswith("tuple[") and vt.endswith("]"):
        ets = _split_comma_types(vt[6:-1])
    for i, elem in enumerate(element_list):
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
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for item in node_list:
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
        if isinstance(v, dict):
            _collect_refs(v, out)
        elif isinstance(v, list):
            _collect_refs(v, out)


def _collect_tuple_names_flat(tn: Node, out: set[str]) -> None:
    elements = tn.get("elements")
    if not isinstance(elements, list):
        return
    element_list: list[JsonVal] = cast(list[JsonVal], elements)
    for elem in element_list:
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
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            bn: set[str] = set()
            ba = _collect_assigned_in_stmts(body_list)
            for n in ba:
                bn.add(n)
            branches.append(bn)
        if isinstance(orelse, list):
            orelse_list: list[JsonVal] = cast(list[JsonVal], orelse)
            if len(orelse_list) == 1:
                nested = orelse_list[0]
                if isinstance(nested, dict) and _sk(nested) == IF:
                    nested_node: Node = cast(dict[str, JsonVal], nested)
                    _walk_chain(nested_node)
                    return
            if len(orelse_list) > 0:
                bn2: set[str] = set()
                oa = _collect_assigned_in_stmts(orelse_list)
                for n in oa:
                    bn2.add(n)
                branches.append(bn2)
    _walk_chain(if_stmt)
    if len(branches) < 2:
        empty: set[str] = set()
        return empty
    count: dict[str, int] = {}
    for br in branches:
        for n in br:
            count[n] = count.get(n, 0) + 1
    out: set[str] = set()
    for n, c in count.items():
        if c >= 2:
            out.add(n)
    return out


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
            if n == "":
                continue
            vd: Node = {}
            vd["kind"] = VAR_DECL
            vd["name"] = n
            vd["type"] = to_hoist[n] if to_hoist[n] != "" else "unknown"
            vd["hoisted"] = True
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
        body = stmt.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            sub = _collect_assigned_in_stmts(body_list)
            for n, t in sub.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
        orelse = stmt.get("orelse")
        if isinstance(orelse, list):
            orelse_list: list[JsonVal] = cast(list[JsonVal], orelse)
            sub2 = _collect_assigned_in_stmts(orelse_list)
            for n, t in sub2.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
    elif kind in (WHILE, FOR, FOR_RANGE, FOR_CORE):
        if kind == FOR_CORE:
            tp = stmt.get("target_plan")
            if isinstance(tp, dict):
                tp_node: Node = cast(dict[str, JsonVal], tp)
                tpk = tp_node.get("kind")
                if tpk == NAME_TARGET:
                    tpn = tp_node.get("id")
                    tpt = tp_node.get("target_type", "")
                    if isinstance(tpn, str) and tpn != "" and tpn not in all_names:
                        all_names[tpn] = tpt if isinstance(tpt, str) else ""
                elif tpk == TUPLE_TARGET:
                    elems = tp_node.get("elements")
                    if isinstance(elems, list):
                        elem_list: list[JsonVal] = cast(list[JsonVal], elems)
                        for e in elem_list:
                            if isinstance(e, dict) and e.get("kind") == NAME_TARGET:
                                en = e.get("id")
                                et2 = e.get("target_type", "")
                                if isinstance(en, str) and en != "" and en not in all_names:
                                    all_names[en] = et2 if isinstance(et2, str) else ""
        body2 = stmt.get("body")
        if isinstance(body2, list):
            body_list2: list[JsonVal] = cast(list[JsonVal], body2)
            sub3 = _collect_assigned_in_stmts(body_list2)
            for n, t in sub3.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
        orelse2 = stmt.get("orelse")
        if isinstance(orelse2, list):
            orelse_list2: list[JsonVal] = cast(list[JsonVal], orelse2)
            sub4 = _collect_assigned_in_stmts(orelse_list2)
            for n, t in sub4.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
    return all_names


def _mark_reassign_block(stmt: Node, hoisted: set[str]) -> None:
    kind = _sk(stmt)
    _ = kind
    body = stmt.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        _mark_reassign(body_list, hoisted)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        orelse_list: list[JsonVal] = cast(list[JsonVal], orelse)
        _mark_reassign(orelse_list, hoisted)


def _recurse_hoist(stmt: Node, parent: set[str]) -> None:
    body = stmt.get("body")
    if isinstance(body, list):
        body_list: list[JsonVal] = cast(list[JsonVal], body)
        stmt["body"] = _hoist_in_stmt_list(body_list, parent)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        orelse_list: list[JsonVal] = cast(list[JsonVal], orelse)
        stmt["orelse"] = _hoist_in_stmt_list(orelse_list, parent)


def _fn_param_names(func: Node) -> set[str]:
    params: set[str] = set()
    ao = func.get("arg_order")
    if isinstance(ao, list):
        ao_list: list[JsonVal] = cast(list[JsonVal], ao)
        for arg in ao_list:
            if isinstance(arg, str) and arg != "":
                params.add(arg)
    args = func.get("args")
    if isinstance(args, list):
        args_list: list[JsonVal] = cast(list[JsonVal], args)
        for arg in args_list:
            if isinstance(arg, dict):
                arg_node: Node = cast(dict[str, JsonVal], arg)
                n = arg_node.get("arg")
                if isinstance(n, str) and n != "":
                    params.add(n)
    return params


def _hoist_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for item in node_list:
            _hoist_walk(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = _sk(nd)
    if _is_function_like_kind(kind):
        body = nd.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            hoisted_body = _hoist_in_stmt_list(body_list, _fn_param_names(nd))
            nd["body"] = hoisted_body
            for s in hoisted_body:
                _hoist_walk(s)
        return
    if kind in (CLASS_DEF, MODULE):
        body = nd.get("body")
        if isinstance(body, list):
            body_list2: list[JsonVal] = cast(list[JsonVal], body)
            for s in body_list2:
                _hoist_walk(s)
        return
    for v in nd.values():
        if isinstance(v, dict):
            v_node: Node = cast(dict[str, JsonVal], v)
            _hoist_walk(v_node)
        elif isinstance(v, list):
            v_list: list[JsonVal] = cast(list[JsonVal], v)
            _hoist_walk(v_list)


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
            lt2 = ""
            rt2 = ""
            if isinstance(left, dict):
                left_node: Node = cast(dict[str, JsonVal], left)
                lt2 = _nt(left_node.get("resolved_type"))
            if isinstance(right, dict):
                right_node: Node = cast(dict[str, JsonVal], right)
                rt2 = _nt(right_node.get("resolved_type"))
            promoted = _promote_result(lt2, rt2)
            if promoted != "":
                if isinstance(left, dict) and lt2 in _SMALL_INTS:
                    left_node2: Node = cast(dict[str, JsonVal], left)
                    left_node2["resolved_type"] = promoted
                if isinstance(right, dict) and rt2 in _SMALL_INTS:
                    right_node2: Node = cast(dict[str, JsonVal], right)
                    right_node2["resolved_type"] = promoted
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = promoted
    if kind == UNARY_OP:
        op = nd.get("op", "")
        if op in _UNARY_OPS:
            operand = nd.get("operand")
            ot = ""
            if isinstance(operand, dict):
                operand_node: Node = cast(dict[str, JsonVal], operand)
                ot = _nt(operand_node.get("resolved_type"))
            if ot in _SMALL_INTS and isinstance(operand, dict):
                operand_node2: Node = cast(dict[str, JsonVal], operand)
                tgt = _promoted(ot)
                operand_node2["resolved_type"] = tgt
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = tgt
    if kind == FOR_CORE:
        tp = nd.get("target_plan")
        if isinstance(tp, dict):
            tp_node: Node = cast(dict[str, JsonVal], tp)
            tt = _nt(tp_node.get("target_type"))
            if tt == "uint8":
                tp_node["target_type"] = "int64"
    for v in nd.values():
        if isinstance(v, dict):
            v_node: Node = cast(dict[str, JsonVal], v)
            _int_promo_walk(v_node)
        elif isinstance(v, list):
            v_list: list[JsonVal] = cast(list[JsonVal], v)
            _int_promo_walk(v_list)


def _narrowing_walk(node: JsonVal) -> None:
    if isinstance(node, list):
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for item in node_list:
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
            target_node: Node = cast(dict[str, JsonVal], target)
            value_node: Node = cast(dict[str, JsonVal], value)
            tt = _nt(nd.get("decl_type"))
            if tt == "" or tt == "unknown":
                tt = _nt(nd.get("annotation"))
            if tt == "" or tt == "unknown":
                tt = _nt(target_node.get("resolved_type"))
            if tt in _INT_WIDTH:
                _narrow_value(value_node, tt)
    for v in nd.values():
        if isinstance(v, dict):
            v_node2: Node = cast(dict[str, JsonVal], v)
            _narrowing_walk(v_node2)
        elif isinstance(v, list):
            v_list2: list[JsonVal] = cast(list[JsonVal], v)
            _narrowing_walk(v_list2)


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
        lt2 = ""
        rt2 = ""
        if isinstance(left, dict):
            left_node: Node = cast(dict[str, JsonVal], left)
            lt2 = _nt(left_node.get("resolved_type"))
        if isinstance(right, dict):
            right_node: Node = cast(dict[str, JsonVal], right)
            rt2 = _nt(right_node.get("resolved_type"))
        lw = _INT_WIDTH.get(lt2, 0) if lt2 in _INT_WIDTH else 0
        rw2 = _INT_WIDTH.get(rt2, 0) if rt2 in _INT_WIDTH else 0
        if lw > 0 and rw2 > 0 and tw >= lw and tw >= rw2:
            vn["resolved_type"] = tt
    elif kind == UNARY_OP:
        operand = vn.get("operand")
        ot = ""
        if isinstance(operand, dict):
            operand_node: Node = cast(dict[str, JsonVal], operand)
            ot = _nt(operand_node.get("resolved_type"))
        ow = _INT_WIDTH.get(ot, 0) if ot in _INT_WIDTH else 0
        if ow > 0 and tw >= ow:
            vn["resolved_type"] = tt


def _remove_redundant_unbox(node: JsonVal) -> None:
    if isinstance(node, list):
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for item in node_list:
            _remove_redundant_unbox(item)
        return
    if not isinstance(node, dict):
        return
    nd: Node = node
    kind = nd.get("kind")
    if kind in (ASSIGN, ANN_ASSIGN):
        value = nd.get("value")
        if isinstance(value, dict):
            value_node: Node = cast(dict[str, JsonVal], value)
            if value_node.get("kind") != UNBOX:
                inner = None
            else:
                inner = value_node.get("value")
            if isinstance(inner, dict):
                inner_node: Node = cast(dict[str, JsonVal], inner)
                ut = _nt(value_node.get("target"))
                it = _nt(inner_node.get("resolved_type"))
                if ut != "" and ut == it:
                    nd["value"] = inner
    for v in nd.values():
        if isinstance(v, dict):
            v_node: Node = cast(dict[str, JsonVal], v)
            _remove_redundant_unbox(v_node)
        elif isinstance(v, list):
            v_list: list[JsonVal] = cast(list[JsonVal], v)
            _remove_redundant_unbox(v_list)


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
    "PYTRA_TID_LIST": "list[JsonVal]",
    "PYTRA_TID_DICT": "dict[str,JsonVal]",
    "PYTRA_TID_SET": "set[JsonVal]",
    "PYTRA_TID_TUPLE": "tuple[JsonVal]",
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
    norm: str = normalize_type_name(type_name)
    guard: str = normalize_type_name(guard_type)
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
        prefix = guard + "["
        return norm == guard or norm.startswith(prefix)
    return norm == guard


def _select_guard_target_type(source_type: str, expected_name: str) -> str:
    src: str = normalize_type_name(source_type)
    expected: str = normalize_type_name(expected_name)
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
        raw_value = nd.get("value")
        expected = nd.get("expected_type_id")
        if isinstance(raw_value, dict):
            value_node0: Node = cast(dict[str, JsonVal], raw_value)
            if value_node0.get("kind") == UNBOX:
                inner = value_node0.get("value")
                if isinstance(inner, dict):
                    raw_value = inner
        if not isinstance(raw_value, dict):
            return {}
        value_node: Node = cast(dict[str, JsonVal], raw_value)
        if value_node.get("kind") != NAME:
            return {}
        name = _tp_safe(value_node.get("id"))
        if name == "":
            return {}
        expected_name = ""
        if isinstance(expected, dict):
            expected_node: Node = cast(dict[str, JsonVal], expected)
            expected_name = _tp_safe(expected_node.get("id"))
            if expected_name == "":
                expected_name = _tp_safe(expected_node.get("repr"))
        target_type = _select_guard_target_type(_tp_safe(value_node.get("resolved_type")), expected_name)
        if target_type == "" or target_type == "unknown":
            return {}
        return {name: target_type}
    if kind == COMPARE:
        left = nd.get("left")
        comparators = nd.get("comparators")
        ops = nd.get("ops")
        if not isinstance(left, dict):
            return {}
        left_node: Node = cast(dict[str, JsonVal], left)
        if left_node.get("kind") != NAME:
            return {}
        if not isinstance(comparators, list):
            return {}
        comparator_list: list[JsonVal] = cast(list[JsonVal], comparators)
        if len(comparator_list) != 1 or not isinstance(comparator_list[0], dict):
            return {}
        comp0: Node = cast(dict[str, JsonVal], comparator_list[0])
        if comp0.get("kind") != CONSTANT or comp0.get("value") is not None:
            return {}
        if not isinstance(ops, list):
            return {}
        ops_list: list[JsonVal] = cast(list[JsonVal], ops)
        if len(ops_list) != 1:
            return {}
        name2 = _tp_safe(left_node.get("id"))
        src_type = _tp_safe(left_node.get("resolved_type"))
        if name2 == "" or src_type == "":
            return {}
        members: list[str] = []
        for member in _split_union_members(src_type):
            if normalize_type_name(member) != "None":
                members.append(member)
        op = _tp_safe(ops_list[0])
        if op == "IsNot":
            if len(members) == 0:
                return {}
            if len(members) == 1:
                return {name2: normalize_type_name(members[0])}
            member_names: list[str] = []
            for member in members:
                member_names.append(normalize_type_name(member))
            return {name2: " | ".join(member_names)}
        return {}
    if kind == BOOL_OP and _tp_safe(nd.get("op")) == "And":
        merged: dict[str, str] = {}
        values = nd.get("values")
        if not isinstance(values, list):
            return merged
        value_list: list[JsonVal] = cast(list[JsonVal], values)
        for value in value_list:
            child = _guard_narrowing_from_expr(value)
            for name, target_type in child.items():
                cur = merged.get(name, "")
                if cur == "" or cur == target_type:
                    merged[name] = target_type
                else:
                    conflict = "__conflict__"
                    merged[name] = conflict
        out: dict[str, str] = {}
        for name, target_type in merged.items():
            if target_type != "__conflict__":
                out[name] = target_type
        return out
    return {}


def _invert_guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    if not isinstance(expr, dict):
        return {}
    nd: Node = expr
    if nd.get("kind", "") == BOOL_OP and _tp_safe(nd.get("op")) == "Or":
        merged: dict[str, str] = {}
        values = nd.get("values")
        if not isinstance(values, list):
            return merged
        value_list: list[JsonVal] = cast(list[JsonVal], values)
        for value in value_list:
            child = _invert_guard_narrowing_from_expr(value)
            for name, target_type in child.items():
                cur = merged.get(name, "")
                if cur == "" or cur == target_type:
                    merged[name] = target_type
                else:
                    conflict = "__conflict__"
                    merged[name] = conflict
        out: dict[str, str] = {}
        for name, target_type in merged.items():
            if target_type != "__conflict__":
                out[name] = target_type
        return out
    if nd.get("kind", "") != COMPARE:
        return {}
    left = nd.get("left")
    comparators = nd.get("comparators")
    ops = nd.get("ops")
    if not isinstance(left, dict):
        return {}
    left_node: Node = cast(dict[str, JsonVal], left)
    if left_node.get("kind") != NAME:
        return {}
    if not isinstance(comparators, list):
        return {}
    comparator_list: list[JsonVal] = cast(list[JsonVal], comparators)
    if len(comparator_list) != 1 or not isinstance(comparator_list[0], dict):
        return {}
    comp0: Node = cast(dict[str, JsonVal], comparator_list[0])
    if comp0.get("kind") != CONSTANT or comp0.get("value") is not None:
        return {}
    if not isinstance(ops, list):
        return {}
    ops_list: list[JsonVal] = cast(list[JsonVal], ops)
    if len(ops_list) != 1:
        return {}
    name = _tp_safe(left_node.get("id"))
    src_type = _tp_safe(left_node.get("resolved_type"))
    if name == "" or src_type == "":
        return {}
    members: list[str] = []
    for member in _split_union_members(src_type):
        if normalize_type_name(member) != "None":
            members.append(member)
    if len(members) == 0:
        return {}
    member_names: list[str] = []
    for member in members:
        member_names.append(normalize_type_name(member))
    narrowed = member_names[0] if len(member_names) == 1 else " | ".join(member_names)
    op = _tp_safe(ops_list[0])
    if op == "Is":
        return {name: normalize_type_name(narrowed)}
    return {}


def _make_guard_unbox(name_node: Node, target_type: str) -> Node:
    out: Node = {}
    out["kind"] = UNBOX
    out["value"] = deep_copy_json(name_node)
    out["resolved_type"] = target_type
    out["borrow_kind"] = "value"
    out["casts"] = []
    out["target"] = target_type
    out["on_fail"] = "raise"
    span = name_node.get("source_span")
    if isinstance(span, dict):
        out["source_span"] = span
    repr_obj = name_node.get("repr")
    if isinstance(repr_obj, str) and repr_obj != "":
        out["repr"] = repr_obj
    return out


def _guard_needs_unbox(current_type: str, storage_type: str, target_type: str) -> bool:
    if target_type == "":
        return False
    if storage_type != "" and storage_type != target_type:
        if (
            storage_type.endswith(" | None")
            or storage_type.endswith("|None")
            or "|" in storage_type
            or "Any" in storage_type
            or "object" in storage_type
            or storage_type == "Obj"
            or storage_type == "unknown"
        ):
            return True
    return current_type != target_type


def _guard_expr(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if isinstance(node, list):
        node_list: list[JsonVal] = cast(list[JsonVal], node)
        for i in range(len(node_list)):
            node_list[i] = _guard_expr(node_list[i], env)
        return node_list
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == NAME:
        name = _tp_safe(nd.get("id"))
        target_type = env.get(name, "")
        current_type = _tp_safe(nd.get("resolved_type"))
        storage_type = env.get("__storage__:" + name, "")
        if _guard_needs_unbox(current_type, storage_type, target_type):
            return _make_guard_unbox(nd, target_type)
        return nd
    if kind == "IsInstance":
        expected = nd.get("expected_type_id")
        if isinstance(expected, dict):
            expected_node: Node = cast(dict[str, JsonVal], expected)
            nd["expected_type_id"] = _guard_expr(expected_node, env)
        elif isinstance(expected, list):
            expected_list: list[JsonVal] = cast(list[JsonVal], expected)
            nd["expected_type_id"] = _guard_expr(expected_list, env)
        return nd
    if kind in (FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF, UNBOX):
        return nd
    for key in list(nd.keys()):
        value = nd[key]
        if isinstance(value, dict):
            value_node: Node = cast(dict[str, JsonVal], value)
            nd[key] = _guard_expr(value_node, env)
        elif isinstance(value, list):
            value_list: list[JsonVal] = cast(list[JsonVal], value)
            nd[key] = _guard_expr(value_list, env)
    return nd


def _guard_lvalue(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if not isinstance(node, dict):
        return node
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == ATTRIBUTE:
        value = nd.get("value")
        if isinstance(value, dict):
            value_node: Node = cast(dict[str, JsonVal], value)
            nd["value"] = _guard_expr(value_node, env)
        elif isinstance(value, list):
            value_list: list[JsonVal] = cast(list[JsonVal], value)
            nd["value"] = _guard_expr(value_list, env)
        return nd
    if kind == SUBSCRIPT:
        value = nd.get("value")
        if isinstance(value, dict):
            value_node2: Node = cast(dict[str, JsonVal], value)
            nd["value"] = _guard_expr(value_node2, env)
        elif isinstance(value, list):
            value_list2: list[JsonVal] = cast(list[JsonVal], value)
            nd["value"] = _guard_expr(value_list2, env)
        slice_obj = nd.get("slice")
        if isinstance(slice_obj, dict):
            slice_node: Node = cast(dict[str, JsonVal], slice_obj)
            nd["slice"] = _guard_expr(slice_node, env)
        elif isinstance(slice_obj, list):
            slice_list: list[JsonVal] = cast(list[JsonVal], slice_obj)
            nd["slice"] = _guard_expr(slice_list, env)
        return nd
    if kind in (TUPLE, LIST):
        elements = nd.get("elements")
        if isinstance(elements, list):
            element_list: list[JsonVal] = cast(list[JsonVal], elements)
            for i in range(len(element_list)):
                element_list[i] = _guard_lvalue(element_list[i], env)
        return nd
    return nd


def _target_names(node: JsonVal) -> set[str]:
    if not isinstance(node, dict):
        empty: set[str] = set()
        return empty
    nd: Node = node
    kind = nd.get("kind", "")
    if kind == NAME:
        name = _tp_safe(nd.get("id"))
        out_name: set[str] = set()
        if name != "":
            out_name.add(name)
        return out_name
    if kind == NAME_TARGET:
        name = _tp_safe(nd.get("id"))
        out_target: set[str] = set()
        if name != "":
            out_target.add(name)
        return out_target
    if kind in (TUPLE, LIST):
        out: set[str] = set()
        elements = nd.get("elements")
        if isinstance(elements, list):
            element_list: list[JsonVal] = cast(list[JsonVal], elements)
            for elem in element_list:
                out.update(_target_names(elem))
        return out
    if kind == TUPLE_TARGET:
        out: set[str] = set()
        elements = nd.get("elements")
        if isinstance(elements, list):
            element_list2: list[JsonVal] = cast(list[JsonVal], elements)
            for elem in element_list2:
                out.update(_target_names(elem))
        return out
    empty2: set[str] = set()
    return empty2


def _guard_stmt_list(stmts: JsonVal, env: dict[str, str]) -> JsonVal:
    if not isinstance(stmts, list):
        return stmts
    stmt_list: list[JsonVal] = cast(list[JsonVal], stmts)
    local_env: dict[str, str] = {}
    for key, value in env.items():
        local_env[key] = value
    for stmt in stmt_list:
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
                _guard_env_merge(local_env, _invert_guard_narrowing_from_expr(stmt.get("test")))
            elif orelse_exits and not body_exits:
                _guard_env_merge(local_env, _guard_narrowing_from_expr(stmt.get("test")))
        if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN, FOR, FOR_RANGE):
            for name in _target_names(stmt.get("target")):
                if name in local_env:
                    local_env[name] = ""
        elif kind == FOR_CORE:
            for name in _target_names(stmt.get("target_plan")):
                if name in local_env:
                    local_env[name] = ""
    return stmt_list


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
    if not isinstance(stmts, list):
        return False
    stmt_list: list[JsonVal] = cast(list[JsonVal], stmts)
    if len(stmt_list) == 0:
        return False
    return _guard_stmt_guarantees_exit(stmt_list[-1])


def _guard_stmt(stmt: JsonVal, env: dict[str, str]) -> None:
    if not isinstance(stmt, dict):
        return
    nd: Node = stmt
    kind = nd.get("kind", "")
    if _is_function_like_kind(kind):
        _guard_stmt_list(nd.get("body"), _guard_function_env(nd))
        return
    if kind == CLASS_DEF:
        body = nd.get("body")
        if isinstance(body, list):
            body_list: list[JsonVal] = cast(list[JsonVal], body)
            for item in body_list:
                _guard_stmt(item, {})
        return
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        target = nd.get("target")
        if isinstance(target, dict):
            target_node: Node = cast(dict[str, JsonVal], target)
            nd["target"] = _guard_lvalue(target_node, env)
        value = nd.get("value")
        if isinstance(value, dict):
            value_node: Node = cast(dict[str, JsonVal], value)
            nd["value"] = _guard_expr(value_node, env)
        elif isinstance(value, list):
            value_list: list[JsonVal] = cast(list[JsonVal], value)
            nd["value"] = _guard_expr(value_list, env)
        return
    if kind == EXPR:
        value = nd.get("value")
        if isinstance(value, dict):
            value_node2: Node = cast(dict[str, JsonVal], value)
            nd["value"] = _guard_expr(value_node2, env)
        elif isinstance(value, list):
            value_list2: list[JsonVal] = cast(list[JsonVal], value)
            nd["value"] = _guard_expr(value_list2, env)
        return
    if kind == RETURN:
        value = nd.get("value")
        if isinstance(value, dict):
            value_node3: Node = cast(dict[str, JsonVal], value)
            nd["value"] = _guard_expr(value_node3, env)
        elif isinstance(value, list):
            value_list3: list[JsonVal] = cast(list[JsonVal], value)
            nd["value"] = _guard_expr(value_list3, env)
        return
    if kind == IF:
        test = nd.get("test")
        if isinstance(test, dict):
            test_node: Node = cast(dict[str, JsonVal], test)
            nd["test"] = _guard_expr(test_node, env)
        elif isinstance(test, list):
            test_list: list[JsonVal] = cast(list[JsonVal], test)
            nd["test"] = _guard_expr(test_list, env)
        body_env: dict[str, str] = {}
        for key, value in env.items():
            body_env[key] = value
        _guard_env_merge(body_env, _guard_narrowing_from_expr(nd.get("test")))
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == WHILE:
        test = nd.get("test")
        if isinstance(test, dict):
            test_node2: Node = cast(dict[str, JsonVal], test)
            nd["test"] = _guard_expr(test_node2, env)
        elif isinstance(test, list):
            test_list2: list[JsonVal] = cast(list[JsonVal], test)
            nd["test"] = _guard_expr(test_list2, env)
        body_env: dict[str, str] = {}
        for key, value in env.items():
            body_env[key] = value
        _guard_env_merge(body_env, _guard_narrowing_from_expr(nd.get("test")))
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
    env = _guard_storage_env(module)
    _guard_stmt_list(module.get("body"), dict(env))
    _guard_stmt_list(module.get("main_guard_body"), dict(env))
    return module


def _guard_env_merge(dst: dict[str, str], narrowed: dict[str, str]) -> None:
    for name, target_type in narrowed.items():
        dst[name] = target_type


def _guard_storage_env(module: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    body = module.get("body")
    if isinstance(body, list):
        _guard_collect_storage_types(body, out)
    main_guard_body = module.get("main_guard_body")
    if isinstance(main_guard_body, list):
        _guard_collect_storage_types(main_guard_body, out)
    return out


def _guard_function_env(func: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    arg_types = func.get("arg_types")
    if isinstance(arg_types, dict):
        for arg_name, arg_type in arg_types.items():
            if isinstance(arg_name, str) and isinstance(arg_type, str) and arg_name != "":
                out["__storage__:" + arg_name] = arg_type
    body = func.get("body")
    if isinstance(body, list):
        _guard_collect_storage_types(body, out)
    return out


def _guard_collect_storage_types(stmts: list[JsonVal], out: dict[str, str]) -> None:
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        kind = _tp_safe(stmt.get("kind"))
        if kind == FUNCTION_DEF or kind == CLOSURE_DEF:
            name = _tp_safe(stmt.get("name"))
            if name != "":
                out["__storage__:" + name] = _closure_callable_type(stmt)
            arg_types = stmt.get("arg_types")
            if isinstance(arg_types, dict):
                for arg_name, arg_type in arg_types.items():
                    if isinstance(arg_name, str) and isinstance(arg_type, str) and arg_name != "":
                        out["__storage__:" + arg_name] = arg_type
            continue
        if kind == CLASS_DEF:
            name2 = _tp_safe(stmt.get("name"))
            if name2 != "":
                out["__storage__:" + name2] = name2
            continue
        if kind == VAR_DECL:
            name3 = _tp_safe(stmt.get("name"))
            type3 = _tp_safe(stmt.get("type"))
            if name3 != "" and type3 != "":
                out["__storage__:" + name3] = type3
        elif kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
            _guard_collect_target_storage(stmt.get("target"), stmt, out)
        elif kind == FOR or kind == FOR_RANGE:
            target_type = _tp_safe(stmt.get("target_type"))
            _guard_collect_target_storage_direct(stmt.get("target"), target_type, out)
        elif kind == FOR_CORE:
            _guard_collect_target_plan_storage(stmt.get("target_plan"), out)
        for key in ("body", "orelse", "finalbody"):
            nested = stmt.get(key)
            if isinstance(nested, list):
                _guard_collect_storage_types(nested, out)
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                ex_name = _tp_safe(handler.get("name"))
                if ex_name != "":
                    out["__storage__:" + ex_name] = "BaseException"
                hbody = handler.get("body")
                if isinstance(hbody, list):
                    _guard_collect_storage_types(hbody, out)


def _guard_collect_target_storage(target: JsonVal, stmt: Node, out: dict[str, str]) -> None:
    decl_type = _tp_safe(stmt.get("decl_type"))
    if decl_type == "":
        decl_type = _tp_safe(stmt.get("annotation"))
    if decl_type == "":
        value = stmt.get("value")
        if isinstance(value, dict):
            decl_type = _tp_safe(value.get("resolved_type"))
    _guard_collect_target_storage_direct(target, decl_type, out)


def _guard_collect_target_storage_direct(target: JsonVal, target_type: str, out: dict[str, str]) -> None:
    if not isinstance(target, dict):
        return
    kind = _tp_safe(target.get("kind"))
    if kind == NAME:
        name = _tp_safe(target.get("id"))
        if name != "" and target_type != "":
            out["__storage__:" + name] = target_type
        return
    if kind == TUPLE or kind == LIST:
        elements = target.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _guard_collect_target_storage_direct(elem, target_type, out)


def _guard_collect_target_plan_storage(target_plan: JsonVal, out: dict[str, str]) -> None:
    if not isinstance(target_plan, dict):
        return
    kind = _tp_safe(target_plan.get("kind"))
    if kind == NAME_TARGET:
        name = _tp_safe(target_plan.get("id"))
        target_type = _tp_safe(target_plan.get("target_type"))
        if name != "" and target_type != "":
            out["__storage__:" + name] = target_type
        return
    if kind == TUPLE_TARGET:
        elements = target_plan.get("elements")
        if isinstance(elements, list):
            for elem in elements:
                _guard_collect_target_plan_storage(elem, out)


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
    if _is_function_like_kind(kind):
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
        if _is_function_like_kind(kind):
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
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
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
        if not isinstance(stmt, dict) or not _is_function_like_kind(jv_str(stmt.get("kind", ""))):
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
    if _is_function_like(nd):
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
            if isinstance(stmt, dict) and _is_function_like(stmt):
                name = stmt.get("name", "")
                if name == "__pytra_main":
                    fb = stmt.get("body")
                    if isinstance(fb, list):
                        _mgd_stmts(fb)
    return module

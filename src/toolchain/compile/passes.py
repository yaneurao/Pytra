"""Post-lowering passes for EAST2 → EAST3.

Consolidated port of all toolchain/compile/east2_to_east3_*_*.py passes.
§5.1: Any/object 禁止 — uses JsonVal throughout.
§5.3: Python 標準モジュール直接 import 禁止。
"""

from __future__ import annotations

from typing import Union
from pytra.typing import cast

from toolchain.compile.jv import JsonVal, Node, CompileContext, deep_copy_json
from toolchain.compile.jv import jv_str, jv_int, jv_is_int, jv_is_dict, jv_is_list, jv_dict, jv_list, nd_kind, nd_get_str
from toolchain.compile.jv import normalize_type_name
from toolchain.common.kinds import (
    MODULE, FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF, VAR_DECL,
    ASSIGN, ANN_ASSIGN, AUG_ASSIGN, EXPR, RETURN, YIELD,
    IF, WHILE, FOR, FOR_RANGE, FOR_CORE, TRY, WITH, SWAP,
    TUPLE_UNPACK, MULTI_ASSIGN, ERROR_RETURN, ERROR_CHECK, ERROR_CATCH,
    NAME, CONSTANT, CALL, ATTRIBUTE, SUBSCRIPT,
    BIN_OP, UNARY_OP, COMPARE, IF_EXP, BOOL_OP,
    LIST, DICT, SET, TUPLE, LIST_COMP,
    UNBOX, COVARIANT_COPY,
    STATIC_RANGE_FOR_PLAN, RUNTIME_ITER_FOR_PLAN,
    NAME_TARGET, TUPLE_TARGET,
    ASSIGNMENT_KINDS,
)


def _is_function_like_kind(kind: str) -> bool:
    return kind == FUNCTION_DEF or kind == CLOSURE_DEF


def _is_function_like(node: JsonVal) -> bool:
    return jv_is_dict(node) and _is_function_like_kind(nd_kind(jv_dict(node)))


def _passes_empty_jv_list() -> list[JsonVal]:
    out: list[JsonVal] = []
    return out

def _passes_empty_node() -> Node:
    out: dict[str, JsonVal] = {}
    return out



def _lc_temp_name(stmt: Node, ordinal: int) -> str:
    span = stmt.get("source_span")
    if jv_is_dict(span):
        span_node: Node = jv_dict(span)
        line_no = span_node.get("line")
        col_no = span_node.get("col")
        if jv_is_int(line_no) and jv_is_int(col_no):
            return "__comp_" + str(jv_int(line_no)) + "_" + str(jv_int(col_no)) + "_" + str(ordinal)
    return "__comp_" + str(ordinal)

# Re-export stubs — these are imported by lower.py
# Each function mutates the module in place and returns it.

# ===========================================================================
# yield lowering
# ===========================================================================

def _contains_yield(node: JsonVal) -> bool:
    if jv_is_dict(node):
        node_dict: Node = jv_dict(node)
        if nd_kind(node_dict) == YIELD:
            return True
        for key_s in node_dict.keys():
            value_jv = node_dict[key_s]
            if _contains_yield(value_jv):
                return True
    elif jv_is_list(node):
        for item in jv_list(node):
            if _contains_yield(item):
                return True
    return False


def _replace_yield_with_append(node: JsonVal, acc: str, list_type: str) -> JsonVal:
    if jv_is_list(node):
        result: list[JsonVal] = _passes_empty_jv_list()
        for item in jv_list(node):
            replaced = _replace_yield_with_append(item, acc, list_type)
            if jv_is_list(replaced):
                for elem in jv_list(replaced):
                    result.append(elem)
            else:
                result.append(replaced)
        return result
    if not jv_is_dict(node):
        return node
    nd: Node = jv_dict(node)
    kind = nd_kind(nd)
    if kind == YIELD:
        value = nd.get("value")
        if value is None:
            value_node: Node = _passes_empty_node()
            value_node["kind"] = CONSTANT
            value_node["value"] = None
            value_node["resolved_type"] = "None"
            value = value_node
        call_args: list[JsonVal] = _passes_empty_jv_list()
        if value is not None:
            call_args.append(value)
        call_node = _make_container_method_call(
            acc,
            list_type,
            "append",
            args=call_args,
            result_type="None",
        )
        ac: Node = _passes_empty_node()
        ac["kind"] = EXPR
        ac["value"] = call_node
        span = nd.get("source_span")
        if jv_is_dict(span):
            ac["source_span"] = span
        return ac
    out: Node = _passes_empty_node()
    for key_s in nd.keys():
        value_jv = nd[key_s]
        if key_s == "body" or key_s == "orelse" or key_s == "finalbody":
            out[key_s] = _replace_yield_with_append(value_jv, acc, list_type)
        elif key_s == "handlers" and jv_is_list(value_jv):
            hs: list[JsonVal] = _passes_empty_jv_list()
            for h in jv_list(value_jv):
                if jv_is_dict(h):
                    h_copy: JsonVal = deep_copy_json(h)
                    nh: Node = jv_dict(h_copy)
                    if "body" in nh:
                        nh["body"] = _replace_yield_with_append(nh["body"], acc, list_type)
                    hs.append(nh)
                else:
                    hs.append(h)
            out[key_s] = hs
        else:
            out[key_s] = value_jv
    return out


def _lower_generator_function(func: Node) -> None:
    body_obj = func.get("body")
    if not jv_is_list(body_obj):
        return
    body = jv_list(body_obj)
    ret_type = "" + jv_str(func.get("return_type", ""))
    elem_type = "unknown"
    if ret_type.startswith("list[") and ret_type.endswith("]"):
        elem_type = ret_type[5:-1]
    elif ret_type not in ("", "unknown"):
        elem_type = ret_type
        func["return_type"] = "list[" + ret_type + "]"
    acc = "__yield_values"
    lt = "list[" + elem_type + "]"
    target: Node = _passes_empty_node()
    target["kind"] = NAME
    target["id"] = acc
    target["resolved_type"] = lt
    list_value: Node = _passes_empty_node()
    list_value["kind"] = LIST
    list_value["elements"] = _passes_empty_jv_list()
    list_value["resolved_type"] = lt
    init: Node = _passes_empty_node()
    init["kind"] = ANN_ASSIGN
    init["target"] = target
    init["annotation"] = lt
    init["decl_type"] = lt
    init["declare"] = True
    init["value"] = list_value
    new_body = _replace_yield_with_append(body, acc, lt)
    ret_name: Node = _passes_empty_node()
    ret_name["kind"] = NAME
    ret_name["id"] = acc
    ret_name["resolved_type"] = lt
    ret_stmt: Node = _passes_empty_node()
    ret_stmt["kind"] = RETURN
    ret_stmt["value"] = ret_name
    final_body: list[JsonVal] = _passes_empty_jv_list()
    final_body.append(init)
    if jv_is_list(new_body):
        for stmt in jv_list(new_body):
            final_body.append(stmt)
    else:
        for stmt in body:
            final_body.append(stmt)
    final_body.append(ret_stmt)
    func["body"] = final_body


def _yield_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _yield_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if _is_function_like_kind(nd_kind(nd)):
        body_jv: JsonVal = None
        if "body" in nd:
            body_jv = nd["body"]
        if jv_is_list(body_jv) and _contains_yield(body_jv):
            _lower_generator_function(nd)
        body2_jv: JsonVal = None
        if "body" in nd:
            body2_jv = nd["body"]
        if jv_is_list(body2_jv):
            for s in jv_list(body2_jv):
                _yield_walk(s)
        return
    if nd_kind(nd) == CLASS_DEF or nd_kind(nd) == MODULE:
        body_jv: JsonVal = None
        if "body" in nd:
            body_jv = nd["body"]
        if jv_is_list(body_jv):
            for s in jv_list(body_jv):
                _yield_walk(s)
        return
    for key_s in nd.keys():
        value_jv = nd[key_s]
        if jv_is_dict(value_jv):
            _yield_walk(value_jv)
        elif jv_is_list(value_jv):
            _yield_walk(value_jv)


def lower_yield_generators(module: Node, ctx: CompileContext) -> Node:
    _yield_walk(module)
    return module


# ===========================================================================
# listcomp lowering
# ===========================================================================

def _build_lc_target_plan(target: JsonVal) -> Node:
    if jv_is_dict(target):
        target_node: Node = jv_dict(target)
        kind = nd_kind(target_node)
        if kind == NAME:
            plan: Node = _passes_empty_node()
            plan["kind"] = NAME_TARGET
            plan["id"] = target_node["id"] if "id" in target_node else "_"
            rt = "" + jv_str(target_node.get("resolved_type", ""))
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
        if kind == TUPLE:
            elements = _passes_empty_jv_list()
            elems_obj = target_node.get("elements")
            if jv_is_list(elems_obj):
                for elem in jv_list(elems_obj):
                    elements.append(elem)
            else:
                elts_obj = target_node.get("elts")
                if jv_is_list(elts_obj):
                    for elem in jv_list(elts_obj):
                        elements.append(elem)
            eps: list[JsonVal] = _passes_empty_jv_list()
            for elem in elements:
                eps.append(_build_lc_target_plan(elem))
            plan: Node = _passes_empty_node()
            plan["kind"] = TUPLE_TARGET
            plan["elements"] = eps
            rt = "" + jv_str(target_node.get("resolved_type", ""))
            if rt not in ("", "unknown"):
                plan["target_type"] = rt
            return plan
    out: Node = _passes_empty_node()
    out["kind"] = NAME_TARGET
    out["id"] = "_"
    return out


def _expand_lc_to_stmts(lc: Node, result_name: str, annotation_type: str = "") -> list[JsonVal]:
    rt = "" + jv_str(lc.get("resolved_type", ""))
    if rt in ("", "unknown") or "unknown" in rt:
        if annotation_type != "":
            rt = annotation_type
        elif rt in ("", "unknown"):
            rt = "list[unknown]"
    target_node: Node = _passes_empty_node()
    target_node["kind"] = NAME
    target_node["id"] = result_name
    target_node["resolved_type"] = rt
    value_node: Node = _passes_empty_node()
    value_node["kind"] = LIST
    value_node["elements"] = _passes_empty_jv_list()
    value_node["resolved_type"] = rt
    init: Node = _passes_empty_node()
    init["kind"] = ANN_ASSIGN
    init["target"] = target_node
    init["annotation"] = rt
    init["decl_type"] = rt
    init["declare"] = True
    init["value"] = value_node
    elt = lc.get("elt")
    append_arg: JsonVal = None
    if elt is not None:
        append_arg = deep_copy_json(elt)
    elem_type = ""
    if rt.startswith("list[") and rt.endswith("]"):
        elem_type = rt[5:-1]
    if jv_is_dict(append_arg) and elem_type != "":
        append_node: Node = jv_dict(append_arg)
        append_node["call_arg_type"] = elem_type
        append_kind = nd_kind(append_node)
        append_rt = "" + jv_str(append_node.get("resolved_type", ""))
        if append_kind == LIST and append_rt in ("", "unknown", "list[unknown]"):
            append_node["resolved_type"] = elem_type
        elif append_kind == DICT and append_rt in ("", "unknown", "dict[unknown,unknown]"):
            append_node["resolved_type"] = elem_type
        elif append_kind == SET and append_rt in ("", "unknown", "set[unknown]"):
            append_node["resolved_type"] = elem_type
    generator_list: list[JsonVal] = _passes_empty_jv_list()
    generators = lc.get("generators")
    if jv_is_list(generators):
        for gen_item in jv_list(generators):
            generator_list.append(gen_item)
    append_args: list[JsonVal] = _passes_empty_jv_list()
    if append_arg is not None:
        append_args.append(append_arg)
    append_call = _make_container_method_call(
        result_name,
        rt,
        "append",
        args=append_args,
        result_type="None",
    )
    append_stmt: Node = _passes_empty_node()
    append_stmt["kind"] = EXPR
    append_stmt["value"] = append_call
    body: list[JsonVal] = _passes_empty_jv_list()
    body.append(append_stmt)
    for gen_idx in range(len(generator_list) - 1, -1, -1):
        gen = generator_list[gen_idx]
        if not jv_is_dict(gen):
            continue
        gen_node: Node = jv_dict(gen)
        ifs = gen_node.get("ifs")
        if jv_is_list(ifs):
            for cond in jv_list(ifs):
                if jv_is_dict(cond):
                    if_stmt: Node = _passes_empty_node()
                    if_stmt["kind"] = IF
                    if_stmt["test"] = deep_copy_json(cond)
                    if_stmt["body"] = body
                    if_stmt["orelse"] = _passes_empty_jv_list()
                    body2: list[JsonVal] = _passes_empty_jv_list()
                    body2.append(if_stmt)
                    body = body2
        target = gen_node.get("target")
        iter_expr = gen_node.get("iter")
        iter_kind = ""
        iter_node: Node = _passes_empty_node()
        if jv_is_dict(iter_expr):
            iter_node = jv_dict(iter_expr)
            iter_kind = "" + nd_kind(iter_node)
        tp = _build_lc_target_plan(target)
        if iter_kind in ("RangeExpr", FOR_RANGE):
            iter_plan: Node = _passes_empty_node()
            iter_plan["kind"] = STATIC_RANGE_FOR_PLAN
            start_default: Node = _passes_empty_node()
            start_default["kind"] = CONSTANT
            start_default["value"] = 0
            start_default["resolved_type"] = "int64"
            stop_default: Node = _passes_empty_node()
            stop_default["kind"] = CONSTANT
            stop_default["value"] = 0
            step_default: Node = _passes_empty_node()
            step_default["kind"] = CONSTANT
            step_default["value"] = 1
            step_default["resolved_type"] = "int64"
            iter_plan["start"] = deep_copy_json(iter_node.get("start", start_default))
            iter_plan["stop"] = deep_copy_json(iter_node.get("stop", stop_default))
            iter_plan["step"] = deep_copy_json(iter_node.get("step", step_default))
            fs: Node = _passes_empty_node()
            fs["kind"] = FOR_CORE
            fs["iter_mode"] = "static_fastpath"
            fs["iter_plan"] = iter_plan
            fs["target_plan"] = tp
            fs["body"] = body
            fs["orelse"] = _passes_empty_jv_list()
        else:
            iter_plan: Node = _passes_empty_node()
            iter_plan["kind"] = RUNTIME_ITER_FOR_PLAN
            if iter_expr is not None:
                iter_plan["iter_expr"] = deep_copy_json(iter_expr)
            else:
                empty_name: Node = _passes_empty_node()
                empty_name["kind"] = NAME
                empty_name["id"] = "__empty"
                iter_plan["iter_expr"] = empty_name
            iter_plan["dispatch_mode"] = "generic"
            iter_plan["init_op"] = "ObjIterInit"
            iter_plan["next_op"] = "ObjIterNext"
            fs: Node = _passes_empty_node()
            fs["kind"] = FOR_CORE
            fs["iter_mode"] = "runtime_protocol"
            fs["iter_plan"] = iter_plan
            fs["target_plan"] = tp
            fs["body"] = body
            fs["orelse"] = _passes_empty_jv_list()
        body3: list[JsonVal] = _passes_empty_jv_list()
        body3.append(fs)
        body = body3
    out: list[JsonVal] = _passes_empty_jv_list()
    out.append(init)
    for stmt in body:
        if jv_is_dict(stmt):
            out.append(stmt)
    return out


def _lc_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = _passes_empty_jv_list()
    stmt_idx = 0
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            stmt_idx += 1
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind in (ASSIGN, ANN_ASSIGN):
            value = stmt_node.get("value")
            if jv_is_dict(value) and nd_kind(jv_dict(value)) == LIST_COMP:
                target = stmt_node.get("target")
                tn: str = ""
                if jv_is_dict(target):
                    target_node: Node = jv_dict(target)
                    if nd_kind(target_node) == NAME:
                        tn = "" + jv_str(target_node.get("id", ""))
                cn: str = tn if tn != "" else _lc_temp_name(stmt_node, stmt_idx)
                at: str = ""
                if kind == ANN_ASSIGN:
                    ann = stmt_node.get("annotation")
                    ann_text = "" + jv_str(ann)
                    if ann_text != "" and "unknown" not in ann_text:
                        at = ann_text
                value_node = jv_dict(value)
                expanded = _expand_lc_to_stmts(value_node, cn, at)
                if cn != tn and jv_is_dict(target):
                    assign_value: Node = _passes_empty_node()
                    assign_value["kind"] = NAME
                    assign_value["id"] = cn
                    assign_value["resolved_type"] = nd_get_str(value_node, "resolved_type")
                    assign_stmt: Node = _passes_empty_node()
                    assign_stmt["kind"] = ASSIGN
                    assign_stmt["target"] = deep_copy_json(target)
                    assign_stmt["value"] = assign_value
                    assign_stmt["declare"] = False
                    expanded.append(assign_stmt)
                for ex in expanded:
                    result.append(ex)
                stmt_idx += 1
                continue
        if kind == EXPR:
            ev = stmt_node.get("value")
            if jv_is_dict(ev) and nd_kind(jv_dict(ev)) == LIST_COMP:
                tmp: str = _lc_temp_name(stmt_node, stmt_idx)
                expanded_expr = _expand_lc_to_stmts(jv_dict(ev), tmp)
                for ex in expanded_expr:
                    result.append(ex)
                stmt_idx += 1
                continue
        # Recurse
        nested_body = stmt_node.get("body")
        if jv_is_list(nested_body):
            stmt_node["body"] = _lc_in_stmts(jv_list(nested_body), ctx)
        nested_orelse = stmt_node.get("orelse")
        if jv_is_list(nested_orelse):
            stmt_node["orelse"] = _lc_in_stmts(jv_list(nested_orelse), ctx)
        nested_finalbody = stmt_node.get("finalbody")
        if jv_is_list(nested_finalbody):
            stmt_node["finalbody"] = _lc_in_stmts(jv_list(nested_finalbody), ctx)
        if kind == TRY:
            hs = stmt_node.get("handlers")
            if jv_is_list(hs):
                for h in jv_list(hs):
                    if jv_is_dict(h):
                        h_node: Node = jv_dict(h)
                        hb = h_node.get("body")
                        if jv_is_list(hb):
                            h_node["body"] = _lc_in_stmts(jv_list(hb), ctx)
        result.append(stmt_node)
        stmt_idx += 1
    return result


def lower_listcomp(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if jv_is_list(body):
        body_list = jv_list(body)
        module["body"] = _lc_in_stmts(body_list, ctx)
    return module


# ===========================================================================
# nested FunctionDef -> ClosureDef lowering
# ===========================================================================

def _collect_function_locals(stmts: list[JsonVal], out: dict[str, str]) -> None:
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            name_s = "" + jv_str(stmt_node.get("name", ""))
            if name_s != "" and name_s not in out:
                if kind == CLASS_DEF:
                    out[name_s] = name_s
                else:
                    out[name_s] = _closure_callable_type(stmt_node)
            continue
        if kind == VAR_DECL:
            name2_s = "" + jv_str(stmt_node.get("name", ""))
            type2_s = "" + jv_str(stmt_node.get("type", ""))
            if name2_s != "" and name2_s not in out:
                out[name2_s] = type2_s
        elif kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
            _collect_assign_names(stmt_node, out)
        elif kind == FOR:
            _collect_target_local_types(stmt_node.get("target"), "" + jv_str(stmt_node.get("target_type", "")), out)
        elif kind == FOR_RANGE:
            _collect_target_local_types(stmt_node.get("target"), "" + jv_str(stmt_node.get("target_type", "int64")), out)
        elif kind == FOR_CORE:
            _collect_target_plan_local_types(stmt_node.get("target_plan"), out)
        elif kind == WITH:
            items = stmt_node.get("items")
            if jv_is_list(items):
                for item in jv_list(items):
                    if not jv_is_dict(item):
                        continue
                    item_node: Node = jv_dict(item)
                    _collect_target_local_types(item_node.get("optional_vars"), "", out)
        nested_body = stmt_node.get("body")
        if jv_is_list(nested_body):
            _collect_function_locals(jv_list(nested_body), out)
        nested_orelse = stmt_node.get("orelse")
        if jv_is_list(nested_orelse):
            _collect_function_locals(jv_list(nested_orelse), out)
        nested_finalbody = stmt_node.get("finalbody")
        if jv_is_list(nested_finalbody):
            _collect_function_locals(jv_list(nested_finalbody), out)
        handlers = stmt_node.get("handlers")
        if jv_is_list(handlers):
            for handler in jv_list(handlers):
                if not jv_is_dict(handler):
                    continue
                handler_node: Node = jv_dict(handler)
                name3 = "" + jv_str(handler_node.get("name", ""))
                if name3 != "" and name3 not in out:
                    out[name3] = "BaseException"
                hbody = handler_node.get("body")
                if jv_is_list(hbody):
                    _collect_function_locals(jv_list(hbody), out)


def _collect_target_local_types(target: JsonVal, inferred_type: str, out: dict[str, str]) -> None:
    if not jv_is_dict(target):
        return
    target_node: Node = jv_dict(target)
    kind = _sk(target_node)
    if kind == NAME:
        name = "" + jv_str(target_node.get("id", ""))
        if name != "" and name not in out:
            target_type = "" + jv_str(target_node.get("resolved_type", ""))
            out[name] = target_type if target_type != "" else inferred_type
        return
    if kind == TUPLE:
        elements = target_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _collect_target_local_types(elem, inferred_type, out)


def _collect_target_plan_local_types(target_plan: JsonVal, out: dict[str, str]) -> None:
    if not jv_is_dict(target_plan):
        return
    target_plan_node: Node = jv_dict(target_plan)
    kind = _sk(target_plan_node)
    if kind == NAME_TARGET:
        name = "" + jv_str(target_plan_node.get("id", ""))
        if name != "" and name not in out:
            out[name] = "" + jv_str(target_plan_node.get("target_type", ""))
        return
    if kind == TUPLE_TARGET:
        elements = target_plan_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _collect_target_plan_local_types(elem, out)


def _collect_function_scope_types(func: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    self_name = "" + jv_str(func.get("name", ""))
    if self_name != "":
        out[self_name] = _closure_callable_type(func)
    arg_types = func.get("arg_types")
    if jv_is_dict(arg_types):
        arg_types_node: Node = jv_dict(arg_types)
        for name in arg_types_node.keys():
            value = arg_types_node[name]
            value_s = "" + jv_str(value)
            if name != "" and value_s != "":
                out[name] = value_s
    captures = func.get("captures")
    if jv_is_list(captures):
        for capture in jv_list(captures):
            if not jv_is_dict(capture):
                continue
            capture_node: Node = jv_dict(capture)
            name2 = "" + jv_str(capture_node.get("name", ""))
            type2 = "" + jv_str(capture_node.get("type", ""))
            if name2 != "" and name2 not in out:
                out[name2] = type2
    body = func.get("body")
    if jv_is_list(body):
        body_list = jv_list(body)
        _collect_function_locals(body_list, out)
    return out


def _collect_function_reassigned_names(func: Node) -> set[str]:
    counts: dict[str, int] = {}
    body = func.get("body")
    if jv_is_list(body):
        _collect_reassigned_lexical(jv_list(body), counts)
    out: set[str] = set()
    arg_order = func.get("arg_order")
    param_names: set[str] = set()
    if jv_is_list(arg_order):
        for arg in jv_list(arg_order):
            arg_s = "" + jv_str(arg)
            if arg_s != "":
                param_names.add(arg_s)
    for name, count in counts.items():
        if name in param_names:
            out.add(name)
        elif count > 1:
            out.add(name)
    return out


def _bump_reassigned(out: dict[str, int], name: str) -> None:
    out[name] = out.get(name, 0) + 1


def _collect_reassigned_lexical(stmts: list[JsonVal], out: dict[str, int]) -> None:
    out = out
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt_node.get("target")
            if jv_is_dict(target) and nd_kind(jv_dict(target)) == NAME:
                target_node: Node = jv_dict(target)
                name = "" + jv_str(target_node.get("id", ""))
                if name != "":
                    _bump_reassigned(out, name)
            elif jv_is_dict(target) and nd_kind(jv_dict(target)) == TUPLE:
                _collect_target_write_counts(target, out)
        elif kind == AUG_ASSIGN:
            target2 = stmt_node.get("target")
            if jv_is_dict(target2) and nd_kind(jv_dict(target2)) == NAME:
                target2_node: Node = jv_dict(target2)
                name2 = "" + jv_str(target2_node.get("id", ""))
                if name2 != "":
                    _bump_reassigned(out, name2)
        elif kind == FOR or kind == FOR_RANGE:
            _collect_target_write_counts(stmt_node.get("target"), out)
        elif kind == FOR_CORE:
            _collect_target_plan_write_counts(stmt_node.get("target_plan"), out)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            continue
        nested = stmt_node.get("body")
        if jv_is_list(nested):
            _collect_reassigned_lexical(jv_list(nested), out)
        nested = stmt_node.get("orelse")
        if jv_is_list(nested):
            _collect_reassigned_lexical(jv_list(nested), out)
        nested = stmt_node.get("finalbody")
        if jv_is_list(nested):
            _collect_reassigned_lexical(jv_list(nested), out)
        handlers = stmt_node.get("handlers")
        if jv_is_list(handlers):
            for handler in jv_list(handlers):
                if jv_is_dict(handler):
                    handler_node: Node = jv_dict(handler)
                    hbody = handler_node.get("body")
                    if jv_is_list(hbody):
                        _collect_reassigned_lexical(jv_list(hbody), out)


def _collect_target_write_counts(target: JsonVal, out: dict[str, int]) -> None:
    out = out
    if not jv_is_dict(target):
        return
    target_node: Node = jv_dict(target)
    kind = _sk(target_node)
    if kind == NAME:
        name = "" + jv_str(target_node.get("id", ""))
        if name != "":
            _bump_reassigned(out, name)
        return
    if kind == TUPLE:
        elements = target_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _collect_target_write_counts(elem, out)


def _collect_target_plan_write_counts(target_plan: JsonVal, out: dict[str, int]) -> None:
    out = out
    if not jv_is_dict(target_plan):
        return
    target_plan_node: Node = jv_dict(target_plan)
    kind = _sk(target_plan_node)
    if kind == NAME_TARGET:
        name = "" + jv_str(target_plan_node.get("id", ""))
        if name != "":
            _bump_reassigned(out, name)
        return
    if kind == TUPLE_TARGET:
        elements = target_plan_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _collect_target_plan_write_counts(elem, out)


def _collect_name_refs_lexical(node: JsonVal, out: set[str], *, descend_into_root: bool = True) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _collect_name_refs_lexical(item, out, descend_into_root=True)
        return
    if not jv_is_dict(node):
        return
    node_node: Node = jv_dict(node)
    kind = _sk(node_node)
    if not descend_into_root and (_is_function_like_kind(kind) or kind == CLASS_DEF):
        return
    if kind == NAME:
        name = "" + jv_str(node_node.get("id", ""))
        if name != "":
            out.add(name)
    for key, value in node_node.items():
        if key == "body" and (_is_function_like_kind(kind) or kind == CLASS_DEF):
            if descend_into_root and jv_is_list(value):
                for item in jv_list(value):
                    _collect_name_refs_lexical(item, out, descend_into_root=False)
            continue
        if jv_is_dict(value):
            _collect_name_refs_lexical(value, out, descend_into_root=True)
        elif jv_is_list(value):
            _collect_name_refs_lexical(value, out, descend_into_root=True)

def _closure_callable_type(node: Node) -> str:
    arg_order = node.get("arg_order")
    arg_types = node.get("arg_types")
    params: list[str] = []
    if jv_is_list(arg_order) and jv_is_dict(arg_types):
        arg_types_node: Node = jv_dict(arg_types)
        for arg in jv_list(arg_order):
            arg_s = "" + jv_str(arg)
            if arg_s == "":
                continue
            if arg_s == "self":
                continue
            arg_type_s = "" + jv_str(arg_types_node[arg_s] if arg_s in arg_types_node else "")
            params.append(arg_type_s if arg_type_s != "" else "unknown")
    ret = "" + jv_str(node.get("return_type", ""))
    if ret == "":
        ret = "unknown"
    return "callable[[" + ",".join(params) + "]," + ret + "]"


def _closure_capture_entries(
    visible_types: dict[str, str],
    visible_mutable: set[str],
    func: Node,
) -> tuple[list[JsonVal], bool]:
    local_types = _collect_function_scope_types(func)
    used_names: set[str] = set()
    defaults = func.get("arg_defaults")
    if jv_is_dict(defaults):
        _collect_name_refs_lexical(defaults, used_names, descend_into_root=True)
    body = func.get("body")
    if jv_is_list(body):
        for stmt in jv_list(body):
            _collect_name_refs_lexical(stmt, used_names, descend_into_root=False)
    captures: list[JsonVal] = _passes_empty_jv_list()
    sorted_names: list[str] = []
    for used_name in used_names:
        sorted_names.append(used_name)
    sorted_names.sort()
    for name in sorted_names:
        if name in local_types or name not in visible_types:
            continue
        capture_type = visible_types.get(name, "")
        capture_mode = "mutable" if name in visible_mutable else "readonly"
        capture: Node = _passes_empty_node()
        capture["name"] = name
        capture["mode"] = capture_mode
        capture["type"] = capture_type
        captures.append(capture)
    return captures, ("" + jv_str(func.get("name", ""))) in used_names


def _lower_closure_stmt_list(
    stmts: list[JsonVal],
    visible_types: dict[str, str],
    visible_mutable: set[str],
) -> list[JsonVal]:
    result: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind == FUNCTION_DEF:
            captures, is_recursive = _closure_capture_entries(visible_types, visible_mutable, stmt_node)
            stmt_node["kind"] = CLOSURE_DEF
            stmt_node["captures"] = captures
            capture_types: Node = _passes_empty_node()
            capture_modes: Node = _passes_empty_node()
            for capture in captures:
                capture_node: Node = jv_dict(capture)
                capture_name = "" + jv_str(capture_node.get("name", ""))
                if capture_name == "":
                    continue
                capture_types[capture_name] = "" + jv_str(capture_node.get("type", ""))
                capture_modes[capture_name] = "" + jv_str(capture_node.get("mode", ""))
            stmt_node["capture_types"] = capture_types
            stmt_node["capture_modes"] = capture_modes
            if is_recursive:
                stmt_node["is_recursive"] = True
            _lower_closure_function(stmt_node, visible_types, visible_mutable)
            result.append(stmt_node)
            continue
        if kind == CLASS_DEF:
            body = stmt_node.get("body")
            if jv_is_list(body):
                class_visible: dict[str, str] = {}
                for name, value in visible_types.items():
                    class_visible[name] = value
                class_name = "" + jv_str(stmt_node.get("name", ""))
                if class_name != "":
                    class_visible[class_name] = class_name
                stmt_node["body"] = _lower_closure_stmt_list(jv_list(body), class_visible, visible_mutable)
            result.append(stmt_node)
            continue
        nested_body = stmt_node.get("body")
        if jv_is_list(nested_body):
            stmt_node["body"] = _lower_closure_stmt_list(jv_list(nested_body), visible_types, visible_mutable)
        nested_orelse = stmt_node.get("orelse")
        if jv_is_list(nested_orelse):
            stmt_node["orelse"] = _lower_closure_stmt_list(jv_list(nested_orelse), visible_types, visible_mutable)
        nested_finalbody = stmt_node.get("finalbody")
        if jv_is_list(nested_finalbody):
            stmt_node["finalbody"] = _lower_closure_stmt_list(jv_list(nested_finalbody), visible_types, visible_mutable)
        handlers = stmt_node.get("handlers")
        if jv_is_list(handlers):
            for handler in jv_list(handlers):
                if not jv_is_dict(handler):
                    continue
                handler_node: Node = jv_dict(handler)
                hbody = handler_node.get("body")
                if jv_is_list(hbody):
                    handler_node["body"] = _lower_closure_stmt_list(jv_list(hbody), visible_types, visible_mutable)
        result.append(stmt_node)
    return result


def _lower_closure_function(
    func: Node,
    outer_visible_types: dict[str, str],
    outer_visible_mutable: set[str],
) -> None:
    body = func.get("body")
    if not jv_is_list(body):
        return
    current_visible: dict[str, str] = {}
    for name, value in outer_visible_types.items():
        current_visible[name] = value
    for name, value in _collect_function_scope_types(func).items():
        current_visible[name] = value
    current_mutable = set(outer_visible_mutable)
    for reassigned_name in _collect_function_reassigned_names(func):
        current_mutable.add(reassigned_name)
    func["body"] = _lower_closure_stmt_list(jv_list(body), current_visible, current_mutable)


def lower_nested_function_defs(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if jv_is_list(body):
        for stmt in jv_list(body):
            if not jv_is_dict(stmt):
                continue
            stmt_node: Node = jv_dict(stmt)
            if _is_function_like_kind(_sk(stmt_node)):
                _lower_closure_function(stmt_node, {}, set())
            elif _sk(stmt_node) == CLASS_DEF:
                class_body = stmt_node.get("body")
                if jv_is_list(class_body):
                    stmt_node["body"] = _lower_closure_stmt_list(jv_list(class_body), {}, set())
    return module


# ===========================================================================
# default argument expansion
# ===========================================================================

def _collect_fn_sigs(module: Node) -> dict[str, Node]:
    sigs: dict[str, Node] = {}
    body = module.get("body")
    if not jv_is_list(body):
        return sigs
    for stmt in jv_list(body):
        if jv_is_dict(stmt):
            _collect_sig_node(jv_dict(stmt), sigs, "")
    return sigs


def _collect_sig_node(node: Node, sigs: dict[str, Node], class_name: str) -> None:
    kind = nd_kind(node)
    if _is_function_like_kind(kind):
        name = "" + jv_str(node.get("name", ""))
        if name == "":
            return
        ao = node.get("arg_order")
        ad = node.get("arg_defaults")
        if not jv_is_list(ao):
            return
        sig: Node = _passes_empty_node()
        sig["arg_order"] = jv_list(ao)
        if jv_is_dict(ad):
            sig["arg_defaults"] = jv_dict(ad)
        else:
            empty_defaults: Node = _passes_empty_node()
            sig["arg_defaults"] = empty_defaults
        full = name
        if class_name != "":
            full = class_name + "." + name
        if class_name == "":
            sigs[name] = sig
        if full != name:
            sigs[full] = sig
        if jv_is_list(node.get("body")):
            for s in jv_list(node.get("body")):
                if jv_is_dict(s):
                    _collect_sig_node(jv_dict(s), sigs, "")
        return
    if kind == CLASS_DEF:
        cn = "" + jv_str(node.get("name", ""))
        if jv_is_list(node.get("body")):
            for s in jv_list(node.get("body")):
                if jv_is_dict(s):
                    _collect_sig_node(jv_dict(s), sigs, cn)
        return
    if kind != ASSIGN and kind != ANN_ASSIGN:
        return
    target: JsonVal = node.get("target")
    if not jv_is_dict(target):
        targets = node.get("targets")
        if jv_is_list(targets):
            targets_list = jv_list(targets)
            if len(targets_list) == 1:
                for item in targets_list:
                    if jv_is_dict(item):
                        target = jv_dict(item)
                    break
    value = node.get("value")
    if not jv_is_dict(target) or nd_kind(jv_dict(target)) != NAME:
        return
    if not jv_is_dict(value):
        return
    value_node: Node = jv_dict(value)
    if nd_kind(value_node) != "Lambda":
        return
    target_node: Node = jv_dict(target)
    lambda_name = "" + jv_str(target_node.get("id", ""))
    args = value_node.get("args")
    if lambda_name == "" or not jv_is_list(args):
        return
    arg_order: list[JsonVal] = _passes_empty_jv_list()
    arg_defaults: Node = _passes_empty_node()
    for arg in jv_list(args):
        if not jv_is_dict(arg):
            continue
        arg_node: Node = jv_dict(arg)
        arg_name = "" + jv_str(arg_node.get("arg", ""))
        if arg_name == "":
            continue
        arg_order.append(arg_name)
        default_node = arg_node.get("default")
        if jv_is_dict(default_node):
            arg_defaults[arg_name] = deep_copy_json(default_node)
    lambda_sig: Node = _passes_empty_node()
    lambda_sig["arg_order"] = arg_order
    lambda_sig["arg_defaults"] = arg_defaults
    sigs[lambda_name] = lambda_sig

def _expand_defaults_walk(node: JsonVal, sigs: dict[str, Node]) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _expand_defaults_walk(item, sigs)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if nd_kind(nd) == CALL:
        func = nd.get("func")
        cn = ""
        if jv_is_dict(func):
            func_node: Node = jv_dict(func)
            func_kind = nd_kind(func_node)
            if func_kind == NAME:
                cn = "" + jv_str(func_node.get("id", ""))
            elif func_kind == ATTRIBUTE:
                attr = "" + jv_str(func_node.get("attr", ""))
                owner = func_node.get("value")
                if jv_is_dict(owner):
                    owner_node: Node = jv_dict(owner)
                    owner_type = "" + jv_str(owner_node.get("resolved_type", ""))
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
            if jv_is_list(args) and jv_is_list(ao) and jv_is_dict(ad):
                args_list: list[JsonVal] = _passes_empty_jv_list()
                for arg in jv_list(args):
                    args_list.append(arg)
                ad_node: Node = jv_dict(ad)
                ep: list[str] = []
                for p in jv_list(ao):
                    p_s = "" + jv_str(p)
                    if p_s != "" and p_s != "self":
                        ep.append(p_s)
                ne = len(ep)
                kw_map: dict[str, JsonVal] = {}
                kws = nd.get("keywords")
                if jv_is_list(kws):
                    for kw in jv_list(kws):
                        if jv_is_dict(kw):
                            kw_node: Node = jv_dict(kw)
                            ka = "" + jv_str(kw_node.get("arg", ""))
                            kv = kw_node.get("value")
                            if ka != "":
                                kw_map[ka] = kv
                if len(args_list) < ne:
                    for i in range(len(args_list), ne):
                        pn = ep[i]
                        if pn in kw_map:
                            kv2 = kw_map[pn]
                            args_list.append(deep_copy_json(kv2) if jv_is_dict(kv2) else kv2)
                        elif pn in ad_node:
                            dn = ad_node[pn]
                            if jv_is_dict(dn):
                                args_list.append(deep_copy_json(dn))
                    nd["args"] = args_list
                    if jv_is_list(kws) and len(kw_map) > 0:
                        remaining: list[JsonVal] = []
                        for kw in jv_list(kws):
                            if jv_is_dict(kw):
                                kw_node2: Node = jv_dict(kw)
                                ka = "" + jv_str(kw_node2.get("arg", ""))
                                if ka in kw_map:
                                    continue
                            remaining.append(kw)
                        nd["keywords"] = remaining
    for v in nd.values():
        if jv_is_dict(v):
            _expand_defaults_walk(v, sigs)
        elif jv_is_list(v):
            _expand_defaults_walk(v, sigs)

def expand_default_arguments(module: Node, ctx: CompileContext) -> Node:
    sigs = _collect_fn_sigs(module)
    if len(sigs) != 0:
        _expand_defaults_walk(module, sigs)
    return module


# ===========================================================================
# ForCore TupleTarget expansion (stub — usually already handled by main lowering)
# ===========================================================================

def _tte_subscript(owner: str, index: int, elem_type: str) -> Node:
    value_node: Node = _passes_empty_node()
    value_node["kind"] = NAME
    value_node["id"] = owner
    value_node["resolved_type"] = "tuple"
    slice_node: Node = _passes_empty_node()
    slice_node["kind"] = CONSTANT
    slice_node["value"] = index
    slice_node["resolved_type"] = "int64"
    out: Node = _passes_empty_node()
    out["kind"] = SUBSCRIPT
    out["value"] = value_node
    out["slice"] = slice_node
    out["resolved_type"] = elem_type if elem_type != "" else "unknown"
    return out


def _local_tmp_name(prefix: str, node: Node, ordinal: int = 0) -> str:
    span = node.get("source_span")
    if jv_is_dict(span):
        span_node: Node = jv_dict(span)
        line_no = span_node.get("line")
        col_no = span_node.get("col")
        if jv_is_int(line_no) and jv_is_int(col_no):
            return prefix + str(jv_int(line_no)) + "_" + str(jv_int(col_no)) + "_" + str(ordinal)
    return prefix + str(ordinal)


def _tte_walk(node: JsonVal, ctx: CompileContext) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tte_walk(item, ctx)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if nd_kind(nd) == FOR_CORE:
        tp = nd.get("target_plan")
        if jv_is_dict(tp):
            tp_node: Node = jv_dict(tp)
            if nd_kind(tp_node) == TUPLE_TARGET:
                elements = tp_node.get("elements")
                if jv_is_list(elements):
                    elements_list = jv_list(elements)
                    if len(elements_list) >= 2:
                        tmp = _local_tmp_name("__tte_", nd)
                        assigns: list[JsonVal] = _passes_empty_jv_list()
                        direct_names: list[JsonVal] = _passes_empty_jv_list()
                        all_flat_names = True
                        i = 0
                        for elem in elements_list:
                            if not jv_is_dict(elem):
                                all_flat_names = False
                                continue
                            elem_node: Node = jv_dict(elem)
                            if nd_kind(elem_node) != NAME_TARGET:
                                all_flat_names = False
                                continue
                            en = "" + jv_str(elem_node["id"] if "id" in elem_node else "")
                            et = "" + jv_str(elem_node["target_type"] if "target_type" in elem_node else "")
                            if en == "":
                                all_flat_names = False
                                continue
                            target_node: Node = _passes_empty_node()
                            target_node["kind"] = NAME
                            target_node["id"] = en
                            target_node["resolved_type"] = et if et != "" else "unknown"
                            assign: Node = _passes_empty_node()
                            assign["kind"] = ASSIGN
                            assign["target"] = target_node
                            assign["value"] = _tte_subscript(tmp, i, et)
                            assign["decl_type"] = et if et != "" else "unknown"
                            assign["declare"] = True
                            assigns.append(assign)
                            direct_names.append(en)
                            i += 1
                        if all_flat_names and len(direct_names) == len(elements_list):
                            tp_out: Node = _passes_empty_node()
                            tp_out["kind"] = NAME_TARGET
                            tp_out["id"] = tmp
                            tp_out["target_type"] = tp_node.get("target_type", "")
                            tp_out["direct_unpack_names"] = direct_names
                            tp_out["tuple_expanded"] = True
                            nd["target_plan"] = tp_out
                            body = nd.get("body")
                            if jv_is_list(body):
                                new_body: list[JsonVal] = _passes_empty_jv_list()
                                for stmt in assigns:
                                    new_body.append(stmt)
                                for stmt in jv_list(body):
                                    new_body.append(stmt)
                                nd["body"] = new_body
    for v in nd.values():
        if jv_is_dict(v):
            _tte_walk(v, ctx)
        elif jv_is_list(v):
            _tte_walk(v, ctx)

def expand_forcore_tuple_targets(module: Node, ctx: CompileContext) -> Node:
    _tte_walk(module, ctx)
    return module


# ===========================================================================
# tuple unpack expansion: x, y = expr → _tmp = expr; x = _tmp[0]; y = _tmp[1]
# ===========================================================================

def _expand_tuple_unpack_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    """Expand Assign(target=Tuple, value=expr) into temp + individual assigns."""
    result: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            body = stmt_node.get("body")
            if jv_is_list(body):
                stmt_node["body"] = _expand_tuple_unpack_in_stmts(jv_list(body), ctx)
            mg = stmt_node.get("main_guard_body")
            if jv_is_list(mg):
                stmt_node["main_guard_body"] = _expand_tuple_unpack_in_stmts(jv_list(mg), ctx)
        elif kind in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE, TRY):
            for key in ["body", "orelse", "finalbody"]:
                nested = stmt_node.get(key)
                if jv_is_list(nested):
                    stmt_node[key] = _expand_tuple_unpack_in_stmts(jv_list(nested), ctx)
            handlers = stmt_node.get("handlers")
            if jv_is_list(handlers):
                for h in jv_list(handlers):
                    if not jv_is_dict(h):
                        continue
                    h_node: Node = jv_dict(h)
                    hb = h_node.get("body")
                    if jv_is_list(hb):
                        h_node["body"] = _expand_tuple_unpack_in_stmts(jv_list(hb), ctx)
        if kind != ASSIGN:
            result.append(stmt_node)
            continue
        target = stmt_node.get("target")
        if not jv_is_dict(target):
            result.append(stmt_node)
            continue
        target_node: Node = jv_dict(target)
        if nd_kind(target_node) != TUPLE:
            result.append(stmt_node)
            continue
        elements = target_node.get("elements")
        if not jv_is_list(elements):
            result.append(stmt_node)
            continue
        elements_list = jv_list(elements)
        if len(elements_list) == 0:
            result.append(stmt_node)
            continue
        value = stmt_node.get("value")
        if jv_is_dict(value) and nd_kind(jv_dict(value)) == TUPLE and len(elements_list) == 2:
            value_node_tuple: Node = jv_dict(value)
            val_elements = value_node_tuple.get("elements")
            if jv_is_list(val_elements):
                val_elements_list = jv_list(val_elements)
                lefts: list[Node] = []
                rights: list[Node] = []
                for elem in elements_list:
                    if jv_is_dict(elem):
                        lefts.append(jv_dict(elem))
                for elem in val_elements_list:
                    if jv_is_dict(elem):
                        rights.append(jv_dict(elem))
                if len(lefts) == 2 and len(rights) == 2 and _same_lvalue(lefts[0], rights[1]) and _same_lvalue(lefts[1], rights[0]):
                    swap_node: Node = _passes_empty_node()
                    swap_node["kind"] = SWAP
                    swap_node["left"] = deep_copy_json(lefts[0])
                    swap_node["right"] = deep_copy_json(lefts[1])
                    result.append(swap_node)
                    continue
        val_rt = ""
        if jv_is_dict(value):
            value_node: Node = jv_dict(value)
            val_rt = "" + jv_str(value_node.get("resolved_type", ""))
        target_rt = "" + jv_str(target_node.get("resolved_type", ""))
        elem_types: list[str] = _parse_tuple_element_types(target_rt)
        if len(elem_types) == 0:
            elem_types = _parse_tuple_element_types(val_rt)
        if ((ctx.lowering_profile.tuple_unpack_style == "structured_binding") or (ctx.lowering_profile.tuple_unpack_style == "pattern_match")) and _tuple_unpack_targets_are_simple_names(elements_list):
            result.append(_make_tuple_unpack_high_level(TUPLE_UNPACK, elements_list, value, elem_types))
            continue
        if ctx.lowering_profile.tuple_unpack_style == "multi_return" and _tuple_unpack_targets_are_simple_names(elements_list):
            result.append(_make_tuple_unpack_high_level(MULTI_ASSIGN, elements_list, value, elem_types))
            continue
        tmp_name = _local_tmp_name("__tuple_unpack_", stmt_node, len(result))
        tmp_value, tmp_rt = _make_tuple_unpack_source(value, val_rt, target_rt)
        tmp_target: Node = _passes_empty_node()
        tmp_target["kind"] = NAME
        tmp_target["id"] = tmp_name
        tmp_target["resolved_type"] = tmp_rt
        tmp_assign: Node = _passes_empty_node()
        tmp_assign["kind"] = ASSIGN
        tmp_assign["target"] = tmp_target
        tmp_assign["value"] = tmp_value
        tmp_assign["declare"] = True
        tmp_assign["decl_type"] = tmp_rt
        result.append(tmp_assign)
        elem_types = _parse_tuple_element_types(tmp_rt)
        if len(elem_types) == 0:
            elem_types = _parse_tuple_element_types(target_rt)
        i = 0
        for elem in elements_list:
            if not jv_is_dict(elem):
                continue
            elem_rt = elem_types[i] if i < len(elem_types) else "unknown"
            idx_value: Node = _passes_empty_node()
            idx_value["kind"] = NAME
            idx_value["id"] = tmp_name
            idx_value["resolved_type"] = tmp_rt
            idx_slice: Node = _passes_empty_node()
            idx_slice["kind"] = CONSTANT
            idx_slice["value"] = i
            idx_slice["resolved_type"] = "int64"
            idx_node: Node = _passes_empty_node()
            idx_node["kind"] = SUBSCRIPT
            idx_node["value"] = idx_value
            idx_node["slice"] = idx_slice
            idx_node["resolved_type"] = elem_rt
            _append_tuple_unpack_target_assignments(result, jv_dict(elem), idx_node, elem_rt, ctx)
            i += 1
    return result

def _tuple_unpack_targets_are_simple_names(elements: list[JsonVal]) -> bool:
    for elem in elements:
        if not jv_is_dict(elem):
            return False
        elem_node: Node = jv_dict(elem)
        if _sk(elem_node) not in (NAME, "NameTarget"):
            return False
        if "" + jv_str(elem_node.get("id", "")) == "":
            return False
    return True

def _append_tuple_unpack_target_assignments(
    out: list[JsonVal],
    target: Node,
    value: Node,
    elem_rt: str,
    ctx: CompileContext,
) -> None:
    target_kind = _sk(target)
    if target_kind in (NAME, "NameTarget"):
        elem_name = jv_str(target.get("id"))
        if elem_name == "":
            return
        elem_target: Node = _passes_empty_node()
        elem_target["kind"] = NAME
        elem_target["id"] = elem_name
        elem_target["resolved_type"] = elem_rt
        elem_assign: Node = _passes_empty_node()
        elem_assign["kind"] = ASSIGN
        elem_assign["target"] = elem_target
        elem_assign["value"] = value
        elem_assign["declare"] = True
        elem_assign["decl_type"] = elem_rt
        out.append(elem_assign)
        return

    elem_assign: Node = _passes_empty_node()
    elem_assign["kind"] = ASSIGN
    elem_assign["target"] = deep_copy_json(target)
    elem_assign["value"] = value
    elem_assign["declare"] = False
    out.extend(_expand_tuple_unpack_in_stmts([elem_assign], ctx))


def _same_lvalue(a: Node, b: Node) -> bool:
    ak = nd_kind(a)
    bk = nd_kind(b)
    if ak != bk:
        return False
    if ak == NAME:
        a_id = "" + jv_str(a.get("id", ""))
        b_id = "" + jv_str(b.get("id", ""))
        return a_id != "" and a_id == b_id
    if ak == SUBSCRIPT:
        if not jv_is_dict(a.get("value")) or not jv_is_dict(b.get("value")):
            return False
        if not jv_is_dict(a.get("slice")) or not jv_is_dict(b.get("slice")):
            return False
        return _same_lvalue(jv_dict(a.get("value")), jv_dict(b.get("value"))) and _same_lvalue(jv_dict(a.get("slice")), jv_dict(b.get("slice")))
    if ak == CONSTANT:
        return ("" + jv_str(a.get("value", ""))) == ("" + jv_str(b.get("value", "")))
    if ak == ATTRIBUTE:
        if not jv_is_dict(a.get("value")) or not jv_is_dict(b.get("value")):
            return False
        return ("" + jv_str(a.get("attr", ""))) == ("" + jv_str(b.get("attr", ""))) and _same_lvalue(jv_dict(a.get("value")), jv_dict(b.get("value")))
    if ak == BIN_OP:
        if not jv_is_dict(a.get("left")) or not jv_is_dict(b.get("left")):
            return False
        if not jv_is_dict(a.get("right")) or not jv_is_dict(b.get("right")):
            return False
        return ("" + jv_str(a.get("op", ""))) == ("" + jv_str(b.get("op", ""))) and _same_lvalue(jv_dict(a.get("left")), jv_dict(b.get("left"))) and _same_lvalue(jv_dict(a.get("right")), jv_dict(b.get("right")))
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


def _split_type_args(type_name: str) -> list[str]:
    if "[" not in type_name or not type_name.endswith("]"):
        return []
    inner = type_name[type_name.find("[") + 1 : -1]
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
            part = "".join(cur).strip()
            if part != "":
                parts.append(part)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _list_elem_type(type_name: str) -> str:
    norm = "" + normalize_type_name(type_name)
    if not norm.startswith("list[") or not norm.endswith("]"):
        return ""
    parts = _split_type_args(norm)
    if len(parts) != 1:
        return ""
    return parts[0]


def _make_tuple_unpack_source(value: JsonVal, source_type: str, target_type: str) -> tuple[JsonVal, str]:
    normalized_source = "" + normalize_type_name(source_type)
    normalized_target = "" + normalize_type_name(target_type)
    if normalized_target.startswith("tuple["):
        if normalized_source.startswith("tuple["):
            return value, normalized_source
        if normalized_source.find("None") >= 0:
            out: Node = _passes_empty_node()
            out["kind"] = UNBOX
            out["value"] = deep_copy_json(value)
            out["resolved_type"] = normalized_target
            out["borrow_kind"] = "value"
            out["casts"] = _passes_empty_jv_list()
            out["target"] = normalized_target
            out["on_fail"] = "raise"
            if jv_is_dict(value):
                value_node: Node = jv_dict(value)
                span = value_node.get("source_span")
                if jv_is_dict(span):
                    out["source_span"] = span
                repr_text = "" + jv_str(value_node.get("repr", ""))
                if repr_text != "":
                    out["repr"] = repr_text
            return out, normalized_target
    return value, normalized_source


def _make_tuple_unpack_high_level(
    style_kind: str,
    elements_list: list[JsonVal],
    value: JsonVal,
    elem_types: list[str],
) -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = style_kind
    targets: list[JsonVal] = _passes_empty_jv_list()
    target_types: list[JsonVal] = _passes_empty_jv_list()
    i = 0
    for elem in elements_list:
        if not jv_is_dict(elem):
            continue
        elem_node: Node = jv_dict(elem)
        targets.append(deep_copy_json(elem))
        elem_rt = elem_types[i] if i < len(elem_types) else ""
        if elem_rt in ("", "unknown"):
            elem_rt = "" + normalize_type_name("" + jv_str(elem_node.get("resolved_type", "")))
        target_types.append(elem_rt)
    out["targets"] = targets
    out["target_types"] = target_types
    out["value"] = deep_copy_json(value)
    out["declare"] = True
    return out

def expand_tuple_unpack(module: Node, ctx: CompileContext) -> Node:
    """Expand all Assign(target=Tuple, ...) in the module."""
    body = module.get("body")
    if jv_is_list(body):
        module["body"] = _expand_tuple_unpack_in_stmts(jv_list(body), ctx)
    mg = module.get("main_guard_body")
    if jv_is_list(mg):
        module["main_guard_body"] = _expand_tuple_unpack_in_stmts(jv_list(mg), ctx)
    if ctx.lowering_profile.tuple_unpack_style == "multi_return":
        module_jv: JsonVal = module
        _rewrite_multi_return_function_types(module_jv)
    return module

def _rewrite_multi_return_function_types(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _rewrite_multi_return_function_types(item)
        return
    if not jv_is_dict(node):
        return
    node_node: Node = jv_dict(node)
    kind = _sk(node_node)
    if kind == FUNCTION_DEF or kind == CLOSURE_DEF:
        ret = "" + jv_str(node_node.get("return_type", ""))
        if ret != "":
            norm = "" + normalize_type_name(ret)
            if norm.startswith("tuple[") and norm.endswith("]"):
                node_node["return_type"] = "multi_return[" + norm[6:]
    for value in node_node.values():
        if jv_is_dict(value) or jv_is_list(value):
            _rewrite_multi_return_function_types(value)


# ===========================================================================
# enumerate lowering
# ===========================================================================

def _enumerate_tuple_value_type(type_name: str) -> str:
    t = normalize_type_name(type_name)
    if not t.startswith("tuple[") or not t.endswith("]"):
        return "unknown"
    inner = t[6:len(t) - 1]
    depth = 0
    idx = 0
    while idx < len(inner):
        ch = inner[idx:idx + 1]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            tail = inner[idx + 1:len(inner)].strip()
            if tail == "":
                return "unknown"
            return tail + ""
        idx += 1
    return "unknown"

def _try_lower_enum_forcore(stmt: Node, ctx: CompileContext) -> JsonVal:
    ip = stmt.get("iter_plan")
    if not jv_is_dict(ip):
        return None
    ip_node: Node = jv_dict(ip)
    if nd_kind(ip_node) != RUNTIME_ITER_FOR_PLAN:
        return None
    ie = ip_node.get("iter_expr")
    if not jv_is_dict(ie):
        return None
    ie_node: Node = jv_dict(ie)
    st = "" + jv_str(ie_node.get("semantic_tag", ""))
    is_enum = st == "iter.enumerate"
    if not is_enum:
        func = ie_node.get("func")
        if jv_is_dict(func):
            func_node: Node = jv_dict(func)
            is_enum = ("" + jv_str(func_node.get("id", ""))) == "enumerate" or ("" + jv_str(func_node.get("attr", ""))) == "enumerate"
    if not is_enum:
        return None
    args_obj = ie_node.get("args")
    if not jv_is_list(args_obj):
        return None
    xs_nodes: list[Node] = []
    for arg in jv_list(args_obj):
        if jv_is_dict(arg):
            xs_nodes.append(jv_dict(arg))
            break
    if len(xs_nodes) == 0:
        return None
    xs_node = xs_nodes[0]
    xs_type = "" + jv_str(xs_node.get("resolved_type", ""))
    if xs_type in ("", "object", "Any", "unknown"):
        return None
    tp = stmt.get("target_plan")
    if not jv_is_dict(tp):
        return None
    tp_node: Node = jv_dict(tp)
    v_name = "" + jv_str(tp_node.get("id", ""))
    v_type = "" + jv_str(tp_node.get("target_type", ""))
    if v_name == "" or v_type in ("", "object", "Any", "unknown"):
        return None
    body_obj = stmt.get("body")
    if not jv_is_list(body_obj):
        return None
    body_list = jv_list(body_obj)
    counter = _local_tmp_name("__enum_", stmt)
    len_func: Node = _passes_empty_node()
    len_func["kind"] = NAME
    len_func["id"] = "len"
    len_func["resolved_type"] = "callable"
    len_call: Node = _passes_empty_node()
    len_call["kind"] = CALL
    len_call["resolved_type"] = "int64"
    len_call["func"] = len_func
    len_args: list[JsonVal] = _passes_empty_jv_list()
    len_args.append(deep_copy_json(xs_node))
    len_call["args"] = len_args
    len_call["keywords"] = _passes_empty_jv_list()
    len_call["lowered_kind"] = "BuiltinCall"
    len_call["runtime_call"] = "len"
    len_call["runtime_module_id"] = "pytra.core.py_runtime"
    len_call["runtime_symbol"] = "len"
    len_call["runtime_call_adapter_kind"] = "builtin"
    len_call["semantic_tag"] = "core.len"
    one: Node = _passes_empty_node()
    one["kind"] = CONSTANT
    one["value"] = 1
    one["resolved_type"] = "int64"
    zero: Node = _passes_empty_node()
    zero["kind"] = CONSTANT
    zero["value"] = 0
    zero["resolved_type"] = "int64"
    start_expr: Node = zero
    stop_expr: Node = len_call
    step_expr: Node = one
    init_target: Node = _passes_empty_node()
    init_target["kind"] = NAME
    init_target["id"] = counter
    init_target["resolved_type"] = "int64"
    init: Node = _passes_empty_node()
    init["kind"] = ASSIGN
    init["target"] = init_target
    init["value"] = start_expr
    init["declare"] = True
    init["decl_type"] = "int64"
    nip: Node = _passes_empty_node()
    nip["kind"] = STATIC_RANGE_FOR_PLAN
    nip["start"] = start_expr
    nip["stop"] = stop_expr
    nip["step"] = step_expr
    ntp: Node = _passes_empty_node()
    ntp["kind"] = NAME_TARGET
    ntp["id"] = counter
    ntp["target_type"] = "int64"
    assign_idx: Node = _passes_empty_node()
    assign_idx["kind"] = ASSIGN
    idx_target: Node = _passes_empty_node()
    idx_target["kind"] = NAME
    idx_target["id"] = v_name
    idx_target["resolved_type"] = v_type
    assign_idx["target"] = idx_target
    idx_slice: Node = _passes_empty_node()
    idx_slice["kind"] = NAME
    idx_slice["id"] = counter
    idx_slice["resolved_type"] = "int64"
    enum_item_type = _enumerate_tuple_value_type(v_type)
    item_value: Node = _passes_empty_node()
    item_value["kind"] = SUBSCRIPT
    item_value["value"] = deep_copy_json(xs_node)
    item_value["slice"] = idx_slice
    item_value["resolved_type"] = enum_item_type
    enum_index: Node = idx_slice
    if len(jv_list(args_obj)) > 1 and jv_is_dict(jv_list(args_obj)[1]):
        enum_index = _passes_empty_node()
        enum_index["kind"] = BIN_OP
        enum_index["resolved_type"] = "int64"
        enum_index["left"] = deep_copy_json(jv_dict(jv_list(args_obj)[1]))
        enum_index["op"] = "Add"
        enum_index["right"] = idx_slice
    tuple_value: Node = _passes_empty_node()
    tuple_value["kind"] = TUPLE
    tuple_elements: list[JsonVal] = _passes_empty_jv_list()
    tuple_elements.append(enum_index)
    tuple_elements.append(item_value)
    tuple_value["elements"] = tuple_elements
    tuple_value["resolved_type"] = v_type
    assign_idx["value"] = tuple_value
    assign_idx["declare"] = True
    assign_idx["decl_type"] = v_type
    nb: list[JsonVal] = _passes_empty_jv_list()
    nb.append(assign_idx)
    for item in body_list:
        nb.append(item)
    nf: Node = _passes_empty_node()
    nf["kind"] = FOR_CORE
    nf["iter_mode"] = "static_fastpath"
    nf["iter_plan"] = nip
    nf["target_plan"] = ntp
    nf["body"] = nb
    nf["orelse"] = stmt.get("orelse", _passes_empty_jv_list())
    out_nodes: list[JsonVal] = _passes_empty_jv_list()
    out_nodes.append(init)
    out_nodes.append(nf)
    return out_nodes

def _enum_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = "" + jv_str(stmt_node.get("kind", ""))
        if kind == FOR_CORE:
            expanded = _try_lower_enum_forcore(stmt_node, ctx)
            if jv_is_list(expanded):
                for item in jv_list(expanded):
                    result.append(item)
                continue
        for key in ["body", "orelse"]:
            nested = stmt_node.get(key)
            if jv_is_list(nested):
                stmt_node[key] = _enum_in_stmts(jv_list(nested), ctx)
        result.append(stmt_node)
    return result

def lower_enumerate(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if jv_is_list(body):
        module["body"] = _enum_in_stmts(jv_list(body), ctx)
    return module


# ===========================================================================
# reversed lowering
# ===========================================================================

def _try_lower_reversed_forcore(stmt: Node, ctx: CompileContext) -> JsonVal:
    ip = stmt.get("iter_plan")
    if not jv_is_dict(ip):
        return None
    ip_node: Node = jv_dict(ip)
    if nd_kind(ip_node) != RUNTIME_ITER_FOR_PLAN:
        return None
    ie = ip_node.get("iter_expr")
    if not jv_is_dict(ie):
        return None
    ie_node: Node = jv_dict(ie)
    st = "" + jv_str(ie_node.get("semantic_tag", ""))
    is_rev = st == "iter.reversed"
    if not is_rev:
        func = ie_node.get("func")
        if jv_is_dict(func):
            func_node: Node = jv_dict(func)
            is_rev = ("" + jv_str(func_node.get("id", ""))) == "reversed" or ("" + jv_str(func_node.get("attr", ""))) == "reversed"
    if not is_rev:
        return None
    args_obj = ie_node.get("args")
    if not jv_is_list(args_obj):
        return None
    xs_nodes: list[Node] = []
    for arg in jv_list(args_obj):
        if jv_is_dict(arg):
            xs_nodes.append(jv_dict(arg))
            break
    if len(xs_nodes) == 0:
        return None
    xs_node = xs_nodes[0]
    xs_type = "" + jv_str(xs_node.get("resolved_type", ""))
    if xs_type in ("", "object", "Any", "unknown"):
        return None
    tp = stmt.get("target_plan")
    if not jv_is_dict(tp):
        return None
    tp_node: Node = jv_dict(tp)
    v_name = "" + jv_str(tp_node.get("id", ""))
    v_type = "" + jv_str(tp_node.get("target_type", ""))
    if v_name == "" or v_type in ("", "object", "Any", "unknown"):
        return None
    body_obj = stmt.get("body")
    if not jv_is_list(body_obj):
        return None
    body_list = jv_list(body_obj)
    counter = _local_tmp_name("__reversed_", stmt)
    len_func: Node = _passes_empty_node()
    len_func["kind"] = NAME
    len_func["id"] = "len"
    len_func["resolved_type"] = "callable"
    len_call: Node = _passes_empty_node()
    len_call["kind"] = CALL
    len_call["resolved_type"] = "int64"
    len_call["func"] = len_func
    len_args: list[JsonVal] = _passes_empty_jv_list()
    len_args.append(deep_copy_json(xs_node))
    len_call["args"] = len_args
    len_call["keywords"] = _passes_empty_jv_list()
    len_call["lowered_kind"] = "BuiltinCall"
    len_call["runtime_call"] = "len"
    len_call["runtime_module_id"] = "pytra.core.py_runtime"
    len_call["runtime_symbol"] = "len"
    len_call["runtime_call_adapter_kind"] = "builtin"
    len_call["semantic_tag"] = "core.len"
    one: Node = _passes_empty_node()
    one["kind"] = CONSTANT
    one["value"] = 1
    one["resolved_type"] = "int64"
    start_expr: Node = _passes_empty_node()
    start_expr["kind"] = BIN_OP
    start_expr["resolved_type"] = "int64"
    start_expr["left"] = len_call
    start_expr["op"] = "Sub"
    start_expr["right"] = one
    stop_expr: Node = _passes_empty_node()
    stop_expr["kind"] = CONSTANT
    stop_expr["value"] = -1
    stop_expr["resolved_type"] = "int64"
    step_expr: Node = _passes_empty_node()
    step_expr["kind"] = CONSTANT
    step_expr["value"] = -1
    step_expr["resolved_type"] = "int64"
    iter_plan: Node = _passes_empty_node()
    iter_plan["kind"] = STATIC_RANGE_FOR_PLAN
    iter_plan["start"] = start_expr
    iter_plan["stop"] = stop_expr
    iter_plan["step"] = step_expr
    ntp: Node = _passes_empty_node()
    ntp["kind"] = NAME_TARGET
    ntp["id"] = counter
    ntp["target_type"] = "int64"
    idx_name_node: Node = _passes_empty_node()
    idx_name_node["kind"] = NAME
    idx_name_node["id"] = counter
    idx_name_node["resolved_type"] = "int64"
    sub_node: Node = _passes_empty_node()
    sub_node["kind"] = SUBSCRIPT
    sub_node["resolved_type"] = v_type
    sub_node["value"] = deep_copy_json(xs_node)
    sub_node["slice"] = idx_name_node
    assign_target: Node = _passes_empty_node()
    assign_target["kind"] = NAME
    assign_target["id"] = v_name
    assign_target["resolved_type"] = v_type
    elem_assign: Node = _passes_empty_node()
    elem_assign["kind"] = ASSIGN
    elem_assign["target"] = assign_target
    elem_assign["value"] = sub_node
    elem_assign["decl_type"] = v_type
    elem_assign["declare"] = True
    nb: list[JsonVal] = _passes_empty_jv_list()
    nb.append(elem_assign)
    for item in body_list:
        nb.append(item)
    nf: Node = _passes_empty_node()
    nf["kind"] = FOR_CORE
    nf["iter_mode"] = "static_fastpath"
    nf["iter_plan"] = iter_plan
    nf["target_plan"] = ntp
    nf["body"] = nb
    orelse_obj = stmt.get("orelse")
    if jv_is_list(orelse_obj):
        nf["orelse"] = jv_list(orelse_obj)
    else:
        nf["orelse"] = _passes_empty_jv_list()
    return nf

def _reversed_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = "" + jv_str(stmt_node.get("kind", ""))
        if kind == FOR_CORE:
            lowered = _try_lower_reversed_forcore(stmt_node, ctx)
            if jv_is_dict(lowered):
                lowered_node: Node = jv_dict(lowered)
                inner = lowered_node.get("body")
                if jv_is_list(inner):
                    lowered_node["body"] = _reversed_in_stmts(jv_list(inner), ctx)
                result.append(lowered_node)
                continue
        for key in ["body", "orelse"]:
            nested = stmt_node.get(key)
            if jv_is_list(nested):
                stmt_node[key] = _reversed_in_stmts(jv_list(nested), ctx)
        result.append(stmt_node)
    return result


def lower_reversed(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if jv_is_list(body):
        module["body"] = _reversed_in_stmts(jv_list(body), ctx)
    return module


# ===========================================================================
# block scope hoist — full port of east2_to_east3_block_scope_hoist.py
# ===========================================================================

def _sk(node: JsonVal) -> str:
    if jv_is_dict(node):
        node_node: Node = jv_dict(node)
        return "" + jv_str(node_node.get("kind", ""))
    return ""


def _str(node: JsonVal, key: str) -> str:
    if jv_is_dict(node):
        node_node: Node = jv_dict(node)
        return "" + jv_str(node_node.get(key, ""))
    return ""


def _node_list(node: JsonVal, key: str) -> list[JsonVal]:
    if jv_is_dict(node):
        node_node: Node = jv_dict(node)
        value = node_node.get(key)
        if jv_is_list(value):
            items: list[JsonVal] = []
            for item in jv_list(value):
                items.append(item)
            return items
    return []


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
    dt = ("" + jv_str(stmt.get("decl_type", ""))).strip()
    if dt not in ("", "unknown"):
        return dt
    ann = ("" + jv_str(stmt.get("annotation", ""))).strip()
    if ann not in ("", "unknown"):
        return ann
    target = stmt.get("target")
    if jv_is_dict(target):
        target_node: Node = jv_dict(target)
        rt = ("" + jv_str(target_node.get("resolved_type", ""))).strip()
        if rt not in ("", "unknown"):
            return rt
    value = stmt.get("value")
    if jv_is_dict(value):
        value_node: Node = jv_dict(value)
        vrt = ("" + jv_str(value_node.get("resolved_type", ""))).strip()
        if vrt not in ("", "unknown"):
            return vrt
    return ""


def _collect_assign_names(stmt: Node, out: dict[str, str]) -> None:
    target = stmt.get("target")
    if jv_is_dict(target):
        target_node: Node = jv_dict(target)
        tk = "" + jv_str(target_node.get("kind", ""))
        if tk == NAME:
            n = "" + jv_str(target_node.get("id", ""))
            if n != "" and n not in out:
                out[n] = _resolve_atype(stmt)
        elif tk == TUPLE:
            _collect_tuple_tgt_names(target_node, stmt, out)
    targets = stmt.get("targets")
    if jv_is_list(targets):
        for t in jv_list(targets):
            if jv_is_dict(t):
                t_node: Node = jv_dict(t)
                tk = "" + jv_str(t_node.get("kind", ""))
                if tk == NAME:
                    n = "" + jv_str(t_node.get("id", ""))
                    if n != "" and n not in out:
                        out[n] = _resolve_atype(stmt)
                elif tk == TUPLE:
                    _collect_tuple_tgt_names(t_node, stmt, out)


def _collect_tuple_tgt_names(tn: Node, stmt: Node, out: dict[str, str]) -> None:
    elements = tn.get("elements")
    if not jv_is_list(elements):
        return
    vt = _resolve_atype(stmt)
    ets: list[str] = []
    if vt.startswith("tuple[") and vt.endswith("]"):
        ets = _split_comma_types(vt[6:-1])
    i = 0
    for elem in jv_list(elements):
        if not jv_is_dict(elem):
            i += 1
            continue
        elem_node: Node = jv_dict(elem)
        if ("" + jv_str(elem_node.get("kind", ""))) != NAME:
            i += 1
            continue
        n = "" + jv_str(elem_node.get("id", ""))
        if n == "":
            i += 1
            continue
        et = ""
        if i < len(ets):
            et = ets[i]
        if et == "":
            et = "" + jv_str(elem_node.get("resolved_type", ""))
        if n not in out:
            out[n] = et
        i += 1


def _collect_assigned_in_stmts(stmts: list[JsonVal]) -> dict[str, str]:
    out: dict[str, str] = {}
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind in (ASSIGN, ANN_ASSIGN):
            _collect_assign_names(stmt_node, out)
        elif kind == IF:
            for key in ["body", "orelse"]:
                nested: JsonVal = stmt_node.get(key)
                if jv_is_list(nested):
                    sub = _collect_assigned_in_stmts(jv_list(nested))
                    for n, t in sub.items():
                        if n not in out:
                            out[n] = t
                        elif out[n] == "" and t != "":
                            out[n] = t
        elif kind in (WHILE, FOR, FOR_RANGE, FOR_CORE):
            if kind == FOR_CORE:
                tp = stmt_node.get("target_plan")
                if jv_is_dict(tp):
                    tp_node: Node = jv_dict(tp)
                    tpk = "" + jv_str(tp_node.get("kind", ""))
                    if tpk == NAME_TARGET:
                        tpn = "" + jv_str(tp_node.get("id", ""))
                        tpt = "" + jv_str(tp_node.get("target_type", ""))
                        if tpn != "" and tpn not in out:
                            out[tpn] = tpt
                    elif tpk == TUPLE_TARGET:
                        elems = tp_node.get("elements")
                        if jv_is_list(elems):
                            for e in jv_list(elems):
                                if jv_is_dict(e):
                                    e_node: Node = jv_dict(e)
                                    if ("" + jv_str(e_node.get("kind", ""))) == NAME_TARGET:
                                        en = "" + jv_str(e_node.get("id", ""))
                                        et2 = "" + jv_str(e_node.get("target_type", ""))
                                        if en != "" and en not in out:
                                            out[en] = et2
            for key in ["body", "orelse"]:
                nested: JsonVal = stmt_node.get(key)
                if jv_is_list(nested):
                    sub = _collect_assigned_in_stmts(jv_list(nested))
                    for n, t in sub.items():
                        if n not in out:
                            out[n] = t
                        elif out[n] == "" and t != "":
                            out[n] = t
    return out


def _collect_refs(node: JsonVal, out: set[str]) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _collect_refs(item, out)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if ("" + jv_str(nd.get("kind", ""))) == NAME:
        n = "" + jv_str(nd.get("id", ""))
        if n != "":
            out.add(n)
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _collect_refs(v, out)


def _collect_tuple_names_flat(tn: Node, out: set[str]) -> None:
    elements = tn.get("elements")
    if not jv_is_list(elements):
        return
    for elem in jv_list(elements):
        if jv_is_dict(elem):
            elem_node: Node = jv_dict(elem)
            if ("" + jv_str(elem_node.get("kind", ""))) == NAME:
                n = "" + jv_str(elem_node.get("id", ""))
                if n != "":
                    out.add(n)


def _mark_reassign(stmts: list[JsonVal], hoisted: set[str]) -> None:
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt_node.get("target")
            if jv_is_dict(target):
                target_node: Node = jv_dict(target)
                target_kind = "" + jv_str(target_node.get("kind", ""))
                if target_kind == NAME:
                    n = "" + jv_str(target_node.get("id", ""))
                    if n in hoisted:
                        stmt_node["is_reassign"] = True
                elif target_kind == TUPLE:
                    elements = target_node.get("elements")
                    if jv_is_list(elements):
                        for elem in jv_list(elements):
                            if jv_is_dict(elem):
                                elem_node: Node = jv_dict(elem)
                                if ("" + jv_str(elem_node.get("kind", ""))) == NAME:
                                    en = "" + jv_str(elem_node.get("id", ""))
                                    if en in hoisted:
                                        stmt_node["is_reassign"] = True
                                        break
        if kind in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE):
            for key in ["body", "orelse"]:
                nested: JsonVal = stmt_node.get(key)
                if jv_is_list(nested):
                    _mark_reassign(jv_list(nested), hoisted)


def _collect_multi_branch(if_stmt: Node) -> set[str]:
    branches: list[set[str]] = []
    def _walk_chain(node: Node) -> None:
        body = node.get("body")
        orelse = node.get("orelse")
        if jv_is_list(body):
            bn: set[str] = set()
            ba = _collect_assigned_in_stmts(jv_list(body))
            for n in ba:
                bn.add(n)
            branches.append(bn)
        if jv_is_list(orelse):
            orelse_list = jv_list(orelse)
            if len(orelse_list) == 1:
                for nested in orelse_list:
                    if jv_is_dict(nested) and _sk(nested) == IF:
                        _walk_chain(jv_dict(nested))
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
    result: list[JsonVal] = _passes_empty_jv_list()
    already: set[str] = set(param_names)
    for i in range(len(stmts)):
        stmt = stmts[i]
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_kind(stmt_node)
        if kind in (ASSIGN, ANN_ASSIGN):
            target = stmt_node.get("target")
            if jv_is_dict(target):
                target_node: Node = jv_dict(target)
                target_kind = "" + jv_str(target_node.get("kind", ""))
                if target_kind == NAME:
                    n = "" + jv_str(target_node.get("id", ""))
                    if n != "":
                        already.add(n)
                elif target_kind == TUPLE:
                    _collect_tuple_names_flat(target_node, already)
            targets = stmt_node.get("targets")
            if jv_is_list(targets):
                for t in jv_list(targets):
                    if jv_is_dict(t):
                        t_node: Node = jv_dict(t)
                        target_kind = "" + jv_str(t_node.get("kind", ""))
                        if target_kind == NAME:
                            n = "" + jv_str(t_node.get("id", ""))
                            if n != "":
                                already.add(n)
                        elif target_kind == TUPLE:
                            _collect_tuple_names_flat(t_node, already)
            result.append(stmt_node)
            continue
        if kind == VAR_DECL:
            n = "" + jv_str(stmt_node.get("name", ""))
            if n != "":
                already.add(n)
            result.append(stmt_node)
            continue
        if kind not in (IF, WHILE, FOR, FOR_RANGE, FOR_CORE):
            result.append(stmt_node)
            continue
        # Block-creating statement
        ba2 = _collect_block_assigned(stmt_node)
        names_after: set[str] = set()
        for j in range(i + 1, len(stmts)):
            _collect_refs(stmts[j], names_after)
        multi_branch: set[str] = set()
        if kind == IF:
            multi_branch = _collect_multi_branch(stmt_node)
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
            vd: Node = _passes_empty_node()
            vd["kind"] = VAR_DECL
            vd["name"] = n
            vd["type"] = to_hoist[n] if to_hoist[n] != "" else "unknown"
            vd["hoisted"] = True
            result.append(vd)
            already.add(n)
        if to_hoist:
            hs = set(to_hoist.keys())
            _mark_reassign_block(stmt_node, hs)
        _recurse_hoist(stmt_node, already)
        result.append(stmt_node)
    return result


def _collect_block_assigned(stmt: Node) -> dict[str, str]:
    kind = _sk(stmt)
    all_names: dict[str, str] = {}
    if kind == IF:
        body = stmt.get("body")
        if jv_is_list(body):
            sub = _collect_assigned_in_stmts(jv_list(body))
            for n, t in sub.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
        orelse = stmt.get("orelse")
        if jv_is_list(orelse):
            sub2 = _collect_assigned_in_stmts(jv_list(orelse))
            for n, t in sub2.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
    elif kind in (WHILE, FOR, FOR_RANGE, FOR_CORE):
        if kind == FOR_CORE:
            tp = stmt.get("target_plan")
            if jv_is_dict(tp):
                tp_node: Node = jv_dict(tp)
                tpk = "" + jv_str(tp_node.get("kind", ""))
                if tpk == NAME_TARGET:
                    tpn = "" + jv_str(tp_node.get("id", ""))
                    tpt = "" + jv_str(tp_node.get("target_type", ""))
                    if tpn != "" and tpn not in all_names:
                        all_names[tpn] = tpt
                elif tpk == TUPLE_TARGET:
                    elems = tp_node.get("elements")
                    if jv_is_list(elems):
                        for e in jv_list(elems):
                            if jv_is_dict(e):
                                e_node: Node = jv_dict(e)
                                if ("" + jv_str(e_node.get("kind", ""))) == NAME_TARGET:
                                    en = "" + jv_str(e_node.get("id", ""))
                                    et2 = "" + jv_str(e_node.get("target_type", ""))
                                    if en != "" and en not in all_names:
                                        all_names[en] = et2
        body2 = stmt.get("body")
        if jv_is_list(body2):
            sub3 = _collect_assigned_in_stmts(jv_list(body2))
            for n, t in sub3.items():
                if n not in all_names:
                    all_names[n] = t
                elif all_names[n] == "" and t != "":
                    all_names[n] = t
        orelse2 = stmt.get("orelse")
        if jv_is_list(orelse2):
            sub4 = _collect_assigned_in_stmts(jv_list(orelse2))
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
    if jv_is_list(body):
        _mark_reassign(jv_list(body), hoisted)
    orelse = stmt.get("orelse")
    if jv_is_list(orelse):
        _mark_reassign(jv_list(orelse), hoisted)


def _recurse_hoist(stmt: Node, parent: set[str]) -> None:
    body = stmt.get("body")
    if jv_is_list(body):
        stmt["body"] = _hoist_in_stmt_list(jv_list(body), parent)
    orelse = stmt.get("orelse")
    if jv_is_list(orelse):
        stmt["orelse"] = _hoist_in_stmt_list(jv_list(orelse), parent)


def _fn_param_names(func: Node) -> set[str]:
    params: set[str] = set()
    ao = func.get("arg_order")
    if jv_is_list(ao):
        for arg in jv_list(ao):
            arg_name = "" + jv_str(arg)
            if arg_name != "":
                params.add(arg_name)
    args = func.get("args")
    if jv_is_list(args):
        for arg in jv_list(args):
            if jv_is_dict(arg):
                arg_node: Node = jv_dict(arg)
                n = "" + jv_str(arg_node.get("arg", ""))
                if n != "":
                    params.add(n)
    return params


def _hoist_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _hoist_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = _sk(nd)
    if _is_function_like_kind(kind):
        body_obj: JsonVal = nd.get("body")
        if jv_is_list(body_obj):
            hoisted_body = _hoist_in_stmt_list(jv_list(body_obj), _fn_param_names(nd))
            nd["body"] = hoisted_body
            for s in hoisted_body:
                _hoist_walk(s)
        return
    if kind in (CLASS_DEF, MODULE):
        body_obj: JsonVal = nd.get("body")
        if jv_is_list(body_obj):
            for s in jv_list(body_obj):
                _hoist_walk(s)
        return
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
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
    return ("" + jv_str(t)).strip()


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
    if jv_is_list(node):
        for item in jv_list(node):
            _int_promo_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == BIN_OP:
        op = "" + jv_str(nd.get("op", ""))
        if op in _ARITH_OPS:
            left = nd.get("left")
            right = nd.get("right")
            lt2 = ""
            rt2 = ""
            if jv_is_dict(left):
                left_node: Node = jv_dict(left)
                lt2 = _nt(left_node.get("resolved_type"))
            if jv_is_dict(right):
                right_node: Node = jv_dict(right)
                rt2 = _nt(right_node.get("resolved_type"))
            promoted = _promote_result(lt2, rt2)
            if promoted != "":
                if jv_is_dict(left) and lt2 in _SMALL_INTS:
                    left_node2: Node = jv_dict(left)
                    left_node2["resolved_type"] = promoted
                if jv_is_dict(right) and rt2 in _SMALL_INTS:
                    right_node2: Node = jv_dict(right)
                    right_node2["resolved_type"] = promoted
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = promoted
    if kind == UNARY_OP:
        op = "" + jv_str(nd.get("op", ""))
        if op in _UNARY_OPS:
            operand = nd.get("operand")
            ot = ""
            if jv_is_dict(operand):
                operand_node: Node = jv_dict(operand)
                ot = _nt(operand_node.get("resolved_type"))
            if ot in _SMALL_INTS and jv_is_dict(operand):
                operand_node2: Node = jv_dict(operand)
                tgt = _promoted(ot)
                operand_node2["resolved_type"] = tgt
                cur = _nt(nd.get("resolved_type"))
                if cur == "" or cur == "unknown" or cur in _SMALL_INTS:
                    nd["resolved_type"] = tgt
    if kind == FOR_CORE:
        tp = nd.get("target_plan")
        if jv_is_dict(tp):
            tp_node: Node = jv_dict(tp)
            tt = _nt(tp_node.get("target_type"))
            if tt == "uint8":
                tp_node["target_type"] = "int64"
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _int_promo_walk(v)


def _narrowing_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _narrowing_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind in (ASSIGN, ANN_ASSIGN):
        target = nd.get("target")
        value = nd.get("value")
        if jv_is_dict(target) and jv_is_dict(value):
            target_node: Node = jv_dict(target)
            value_node: Node = jv_dict(value)
            tt = _nt(nd.get("decl_type"))
            if tt == "" or tt == "unknown":
                tt = _nt(nd.get("annotation"))
            if tt == "" or tt == "unknown":
                tt = _nt(target_node.get("resolved_type"))
            if tt in _INT_WIDTH:
                _narrow_value(value_node, tt)
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _narrowing_walk(v)


def _narrow_value(vn: Node, tt: str) -> None:
    kind = "" + jv_str(vn.get("kind", ""))
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
        if jv_is_dict(left):
            left_node: Node = jv_dict(left)
            lt2 = _nt(left_node.get("resolved_type"))
        if jv_is_dict(right):
            right_node: Node = jv_dict(right)
            rt2 = _nt(right_node.get("resolved_type"))
        lw = _INT_WIDTH.get(lt2, 0) if lt2 in _INT_WIDTH else 0
        rw2 = _INT_WIDTH.get(rt2, 0) if rt2 in _INT_WIDTH else 0
        if lw > 0 and rw2 > 0 and tw >= lw and tw >= rw2:
            vn["resolved_type"] = tt
    elif kind == UNARY_OP:
        operand = vn.get("operand")
        ot = ""
        if jv_is_dict(operand):
            operand_node: Node = jv_dict(operand)
            ot = _nt(operand_node.get("resolved_type"))
        ow = _INT_WIDTH.get(ot, 0) if ot in _INT_WIDTH else 0
        if ow > 0 and tw >= ow:
            vn["resolved_type"] = tt


def _remove_redundant_unbox(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _remove_redundant_unbox(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind in (ASSIGN, ANN_ASSIGN):
        value = nd.get("value")
        if jv_is_dict(value):
            value_node: Node = jv_dict(value)
            if ("" + jv_str(value_node.get("kind", ""))) == UNBOX:
                inner = value_node.get("value")
                if jv_is_dict(inner):
                    inner_node: Node = jv_dict(inner)
                    ut = _nt(nd.get("decl_type"))
                    if ut == "" or ut == "unknown":
                        ut = _nt(nd.get("annotation"))
                    it = _nt(inner_node.get("resolved_type"))
                    if ut != "" and ut == it:
                        nd["value"] = inner
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _remove_redundant_unbox(v)


def apply_integer_promotion(module: Node, ctx: CompileContext) -> Node:
    _int_promo_walk(module)
    _narrowing_walk(module)
    _remove_redundant_unbox(module)
    return module


# ===========================================================================
# guard narrowing
# ===========================================================================

_TYPE_GUARD_DEFAULTS: dict[str, str] = {}


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


def _split_top_level_generic_args(type_name: str) -> list[str]:
    args: list[str] = []
    start = type_name.find("[")
    end = type_name.rfind("]")
    if start < 0 or end <= start:
        return args
    cur = ""
    depth = 0
    inner = type_name[start + 1 : end]
    for ch in inner:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            part = cur.strip()
            if part != "":
                args.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        args.append(tail)
    return args


def _expr_effective_type(node: JsonVal) -> str:
    if not jv_is_dict(node):
        return ""
    nd: Node = jv_dict(node)
    kind = _tp_safe(nd.get("kind"))
    if kind == UNBOX:
        target = _tp_safe(nd.get("target"))
        if target != "":
            return "" + normalize_type_name(target)
    return "" + normalize_type_name(nd.get("resolved_type"))


def _guard_refine_subscript_type(nd: Node) -> None:
    owner = nd.get("value")
    if not jv_is_dict(owner):
        return
    owner_type = _expr_effective_type(owner)
    if owner_type == "":
        return
    args = _split_top_level_generic_args(owner_type)
    target_type = ""
    if owner_type == "str":
        target_type = "str"
    elif owner_type.startswith("list[") and len(args) == 1:
        target_type = "" + normalize_type_name(args[0])
    elif owner_type.startswith("dict[") and len(args) == 2:
        target_type = "" + normalize_type_name(args[1])
    elif owner_type.startswith("set[") and len(args) == 1:
        target_type = "" + normalize_type_name(args[0])
    if target_type == "":
        return
    nd["resolved_type"] = target_type


def _type_matches_guard(type_name: str, guard_type: str) -> bool:
    norm = "" + normalize_type_name(type_name)
    guard = "" + normalize_type_name(guard_type)
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
    src = "" + normalize_type_name(source_type)
    expected = "" + normalize_type_name(expected_name)
    if src == "" or src == "unknown" or expected == "" or expected == "unknown":
        return ""
    guard_type = expected
    members = _split_union_members(src)
    if len(members) == 0:
        members = [src]
    for member in members:
        if _type_matches_guard(member, guard_type):
            return "" + normalize_type_name(member)
    if _type_matches_guard(src, guard_type):
        return src
    return expected


def _exclude_guard_target_type(source_type: str, expected_name: str) -> str:
    src = "" + normalize_type_name(source_type)
    expected = "" + normalize_type_name(expected_name)
    if src == "" or src == "unknown" or expected == "" or expected == "unknown":
        return ""
    members = _split_union_members(src)
    if len(members) == 0:
        members = [src]
    remaining: list[str] = []
    for member in members:
        normalized_member = normalize_type_name(member)
        if not _type_matches_guard(normalized_member, expected):
            remaining.append(normalized_member)
    if len(remaining) == 0:
        return ""
    if len(remaining) == 1:
        return remaining[0]
    return " | ".join(remaining)


def _guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    if not jv_is_dict(expr):
        return {}
    nd: Node = jv_dict(expr)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == "IsInstance":
        raw_value = nd.get("value")
        if jv_is_dict(raw_value):
            value_node0: Node = jv_dict(raw_value)
            if ("" + jv_str(value_node0.get("kind", ""))) == UNBOX:
                inner = value_node0.get("value")
                if jv_is_dict(inner):
                    raw_value = inner
        if not jv_is_dict(raw_value):
            return {}
        value_node: Node = jv_dict(raw_value)
        if ("" + jv_str(value_node.get("kind", ""))) != NAME:
            return {}
        name = _tp_safe(value_node.get("id"))
        if name == "":
            return {}
        expected_name = _tp_safe(nd.get("expected_type_name"))
        target_type = _select_guard_target_type(_tp_safe(value_node.get("resolved_type")), expected_name)
        if target_type == "" or target_type == "unknown":
            return {}
        return {name: target_type}
    if kind == COMPARE:
        left = nd.get("left")
        comparators = nd.get("comparators")
        ops = nd.get("ops")
        if not jv_is_dict(left):
            return {}
        left_node: Node = jv_dict(left)
        if ("" + jv_str(left_node.get("kind", ""))) != NAME:
            return {}
        if not jv_is_list(comparators):
            return {}
        comparator_list = jv_list(comparators)
        comp0_nodes: list[Node] = []
        for comp in comparator_list:
            if jv_is_dict(comp):
                comp0_nodes.append(jv_dict(comp))
            break
        if len(comparator_list) != 1 or len(comp0_nodes) != 1:
            return {}
        comp0: Node = comp0_nodes[0]
        if (("" + jv_str(comp0.get("kind", ""))) != CONSTANT) or (comp0.get("value") is not None):
            return {}
        if not jv_is_list(ops):
            return {}
        ops_list = jv_list(ops)
        if len(ops_list) != 1:
            return {}
        name2 = _tp_safe(left_node.get("id"))
        src_type = _tp_safe(left_node.get("resolved_type"))
        if name2 == "" or src_type == "":
            return {}
        members: list[str] = []
        for member in _split_union_members(src_type):
            if ("" + normalize_type_name(member)) != "None":
                members.append(member)
        op = ""
        for op_item in ops_list:
            op = _tp_safe(op_item)
            break
        if op == "IsNot":
            if len(members) == 0:
                return {}
            if len(members) == 1:
                return {name2: "" + normalize_type_name(members[0])}
            member_names: list[str] = []
            for member in members:
                member_names.append("" + normalize_type_name(member))
            return {name2: " | ".join(member_names)}
        return {}
    if kind == BOOL_OP and _tp_safe(nd.get("op")) == "And":
        merged: dict[str, str] = {}
        values = nd.get("values")
        if not jv_is_list(values):
            return merged
        value_list = jv_list(values)
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
    if kind == UNARY_OP and _tp_safe(nd.get("op")) == "Not":
        operand = nd.get("operand")
        return _invert_guard_narrowing_from_expr(operand)
    return {}


def _invert_guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    if not jv_is_dict(expr):
        return {}
    nd: Node = jv_dict(expr)
    if ("" + jv_str(nd.get("kind", ""))) == UNARY_OP and _tp_safe(nd.get("op")) == "Not":
        operand = nd.get("operand")
        return _guard_narrowing_from_expr(operand)
    if (("" + jv_str(nd.get("kind", ""))) == "IsInstance"):
        raw_value = nd.get("value")
        if jv_is_dict(raw_value):
            value_node0: Node = jv_dict(raw_value)
            if ("" + jv_str(value_node0.get("kind", ""))) == UNBOX:
                inner = value_node0.get("value")
                if jv_is_dict(inner):
                    raw_value = inner
        if not jv_is_dict(raw_value):
            return {}
        value_node: Node = jv_dict(raw_value)
        if ("" + jv_str(value_node.get("kind", ""))) != NAME:
            return {}
        name = _tp_safe(value_node.get("id"))
        if name == "":
            return {}
        expected_name = _tp_safe(nd.get("expected_type_name"))
        target_type = _exclude_guard_target_type(_tp_safe(value_node.get("resolved_type")), expected_name)
        if target_type == "" or target_type == "unknown":
            return {}
        return {name: target_type}
    if (("" + jv_str(nd.get("kind", ""))) == BOOL_OP) and _tp_safe(nd.get("op")) == "Or":
        merged: dict[str, str] = {}
        values = nd.get("values")
        if not jv_is_list(values):
            return merged
        value_list = jv_list(values)
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
    if (("" + jv_str(nd.get("kind", ""))) != COMPARE):
        return {}
    left = nd.get("left")
    comparators = nd.get("comparators")
    ops = nd.get("ops")
    if not jv_is_dict(left):
        return {}
    left_node: Node = jv_dict(left)
    if ("" + jv_str(left_node.get("kind", ""))) != NAME:
        return {}
    if not jv_is_list(comparators):
        return {}
    comparator_list = jv_list(comparators)
    comp0_nodes: list[Node] = []
    for comp in comparator_list:
        if jv_is_dict(comp):
            comp0_nodes.append(jv_dict(comp))
        break
    if len(comparator_list) != 1 or len(comp0_nodes) != 1:
        return {}
    comp0: Node = comp0_nodes[0]
    if (("" + jv_str(comp0.get("kind", ""))) != CONSTANT) or (comp0.get("value") is not None):
        return {}
    if not jv_is_list(ops):
        return {}
    ops_list = jv_list(ops)
    if len(ops_list) != 1:
        return {}
    name = _tp_safe(left_node.get("id"))
    src_type = _tp_safe(left_node.get("resolved_type"))
    if name == "" or src_type == "":
        return {}
    members: list[str] = []
    for member in _split_union_members(src_type):
        if ("" + normalize_type_name(member)) != "None":
            members.append(member)
    if len(members) == 0:
        return {}
    member_names: list[str] = []
    for member in members:
        member_names.append("" + normalize_type_name(member))
    narrowed = member_names[0] if len(member_names) == 1 else " | ".join(member_names)
    op = ""
    for op_item in ops_list:
        op = _tp_safe(op_item)
        break
    if op == "Is":
        return {name: "" + normalize_type_name(narrowed)}
    return {}


def _make_guard_unbox(name_node: Node, target_type: str, storage_type: str = "") -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = UNBOX
    inner = deep_copy_json(name_node)
    if storage_type != "" and storage_type != target_type and jv_is_dict(inner):
        inner_node: Node = jv_dict(inner)
        inner_node["resolved_type"] = storage_type
    out["value"] = inner
    out["resolved_type"] = target_type
    out["borrow_kind"] = "value"
    out["casts"] = _passes_empty_jv_list()
    out["target"] = target_type
    out["on_fail"] = "raise"
    span = name_node.get("source_span")
    if jv_is_dict(span):
        out["source_span"] = span
    repr_obj = name_node.get("repr")
    repr_text = "" + jv_str(repr_obj)
    if repr_text != "":
        out["repr"] = repr_text
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
            or storage_type == "JsonVal"
        ):
            return True
    return current_type != target_type


def _guard_expr(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if jv_is_list(node):
        out_list: list[JsonVal] = _passes_empty_jv_list()
        for item in jv_list(node):
            out_list.append(_guard_expr(item, env))
        return out_list
    if not jv_is_dict(node):
        return node
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == NAME:
        name = _tp_safe(nd.get("id"))
        target_type = env.get(name, "")
        current_type = _tp_safe(nd.get("resolved_type"))
        storage_type = env.get("__storage__:" + name, "")
        if _guard_needs_unbox(current_type, storage_type, target_type):
            return _make_guard_unbox(nd, target_type, storage_type)
        return nd
    if kind == "IsInstance":
        # expected_type_name is a plain string — no sub-expression to recurse into
        return nd
    if kind in (FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF):
        return nd
    if kind == UNBOX:
        value: JsonVal = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        return nd
    if kind == IF_EXP:
        test = nd.get("test")
        if jv_is_dict(test) or jv_is_list(test):
            nd["test"] = _guard_expr(test, env)
        body_env_ifexp: dict[str, str] = {}
        for key_ifexp, val_ifexp in env.items():
            body_env_ifexp[key_ifexp] = val_ifexp
        _guard_env_merge(body_env_ifexp, _guard_narrowing_from_expr(nd.get("test")))
        orelse_env_ifexp: dict[str, str] = {}
        for key_ifexp, val_ifexp in env.items():
            orelse_env_ifexp[key_ifexp] = val_ifexp
        _guard_env_merge(orelse_env_ifexp, _invert_guard_narrowing_from_expr(nd.get("test")))
        body_ifexp = nd.get("body")
        if jv_is_dict(body_ifexp) or jv_is_list(body_ifexp):
            nd["body"] = _guard_expr(body_ifexp, body_env_ifexp)
        orelse_ifexp = nd.get("orelse")
        if jv_is_dict(orelse_ifexp) or jv_is_list(orelse_ifexp):
            nd["orelse"] = _guard_expr(orelse_ifexp, orelse_env_ifexp)
        return nd
    if kind == BOOL_OP and _tp_safe(nd.get("op")) == "And":
        values = nd.get("values")
        if jv_is_list(values):
            values_list = jv_list(values)
            and_env: dict[str, str] = {}
            for key, val in env.items():
                and_env[key] = val
            out_values: list[JsonVal] = _passes_empty_jv_list()
            for value_item in values_list:
                guarded_value = _guard_expr(value_item, and_env)
                out_values.append(guarded_value)
                extra = _guard_narrowing_from_expr(guarded_value)
                _guard_env_merge(and_env, extra)
            nd["values"] = out_values
        return nd
    if kind == COMPARE:
        left = nd.get("left")
        comparators = nd.get("comparators")
        ops = nd.get("ops")
        left_is_name = False
        if jv_is_dict(left):
            left_node_check: Node = jv_dict(left)
            left_is_name = _tp_safe(left_node_check.get("kind")) == NAME
        single_const_none_comparator = False
        if jv_is_list(comparators):
            comparator_check = jv_list(comparators)
            comparator0_nodes: list[Node] = []
            for comp in comparator_check:
                if jv_is_dict(comp):
                    comparator0_nodes.append(jv_dict(comp))
                break
            if len(comparator_check) == 1 and len(comparator0_nodes) == 1:
                comparator0 = comparator0_nodes[0]
                single_const_none_comparator = (
                    _tp_safe(comparator0.get("kind")) == CONSTANT
                    and comparator0.get("value") is None
                )
        single_is_op = False
        if jv_is_list(ops):
            op_list = jv_list(ops)
            if len(op_list) == 1:
                op0 = ""
                for op_item in op_list:
                    op0 = _tp_safe(op_item)
                    break
                single_is_op = op0 in ("Is", "IsNot")
        is_name_none_compare = (
            left_is_name and single_const_none_comparator and single_is_op
        )
        if jv_is_dict(left) and not is_name_none_compare:
            left_node_cmp: Node = jv_dict(left)
            nd["left"] = _guard_expr(left_node_cmp, env)
        elif jv_is_list(left):
            nd["left"] = _guard_expr(left, env)
        if jv_is_list(comparators):
            comparator_list_cmp = jv_list(comparators)
            out_comparators: list[JsonVal] = _passes_empty_jv_list()
            for comp in comparator_list_cmp:
                out_comparators.append(_guard_expr(comp, env))
            nd["comparators"] = out_comparators
        return nd
    for key in list(nd.keys()):
        value: JsonVal = nd[key]
        if jv_is_dict(value) or jv_is_list(value):
            nd[key] = _guard_expr(value, env)
    return nd


def _guard_lvalue(node: JsonVal, env: dict[str, str]) -> JsonVal:
    if not jv_is_dict(node):
        return node
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == ATTRIBUTE:
        value: JsonVal = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        return nd
    if kind == SUBSCRIPT:
        value = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        slice_obj: JsonVal = nd.get("slice")
        if jv_is_dict(slice_obj) or jv_is_list(slice_obj):
            nd["slice"] = _guard_expr(slice_obj, env)
        _guard_refine_subscript_type(nd)
        return nd
    if kind in (TUPLE, LIST):
        elements = nd.get("elements")
        if jv_is_list(elements):
            out_elements: list[JsonVal] = _passes_empty_jv_list()
            for elem in jv_list(elements):
                out_elements.append(_guard_lvalue(elem, env))
            nd["elements"] = out_elements
        return nd
    return nd


def _target_names(node: JsonVal) -> set[str]:
    if not jv_is_dict(node):
        empty: set[str] = set()
        return empty
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
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
        elements: JsonVal = nd.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                out.update(_target_names(elem))
        return out
    if kind == TUPLE_TARGET:
        out: set[str] = set()
        elements: JsonVal = nd.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                out.update(_target_names(elem))
        return out
    empty2: set[str] = set()
    return empty2


def _guard_stmt_list(stmts: JsonVal, env: dict[str, str]) -> JsonVal:
    if not jv_is_list(stmts):
        return stmts
    stmt_list = jv_list(stmts)
    local_env: dict[str, str] = {}
    for key, value in env.items():
        local_env[key] = value
    for stmt in stmt_list:
        _guard_stmt(stmt, local_env)
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = "" + jv_str(stmt_node.get("kind", ""))
        if kind == IF:
            body: JsonVal = stmt_node.get("body")
            orelse: JsonVal = stmt_node.get("orelse")
            body_exits = _guard_block_guarantees_exit(body)
            orelse_exits = _guard_block_guarantees_exit(orelse)
            if body_exits and not orelse_exits:
                _guard_env_merge(local_env, _invert_guard_narrowing_from_expr(stmt_node.get("test")))
            elif orelse_exits and not body_exits:
                _guard_env_merge(local_env, _guard_narrowing_from_expr(stmt_node.get("test")))
        if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN, FOR, FOR_RANGE):
            for name in _target_names(stmt_node.get("target")):
                if name in local_env:
                    local_env[name] = ""
        elif kind == FOR_CORE:
            for name in _target_names(stmt_node.get("target_plan")):
                if name in local_env:
                    local_env[name] = ""
    return stmt_list


def _guard_stmt_guarantees_exit(stmt: JsonVal) -> bool:
    if not jv_is_dict(stmt):
        return False
    stmt_node: Node = jv_dict(stmt)
    kind = _tp_safe(stmt_node.get("kind"))
    if kind in (RETURN, "Raise"):
        return True
    if kind == IF:
        return _guard_block_guarantees_exit(stmt_node.get("body")) and _guard_block_guarantees_exit(stmt_node.get("orelse"))
    return False


def _guard_block_guarantees_exit(stmts: JsonVal) -> bool:
    if not jv_is_list(stmts):
        return False
    stmt_list = jv_list(stmts)
    if len(stmt_list) == 0:
        return False
    last_stmt: JsonVal = None
    for item in stmt_list:
        last_stmt = item
    return last_stmt is not None and _guard_stmt_guarantees_exit(last_stmt)


def _guard_stmt(stmt: JsonVal, env: dict[str, str]) -> None:
    if not jv_is_dict(stmt):
        return
    nd: Node = jv_dict(stmt)
    kind = "" + jv_str(nd.get("kind", ""))
    if _is_function_like_kind(kind):
        _guard_stmt_list(nd.get("body"), _guard_function_env(nd))
        return
    if kind == CLASS_DEF:
        body: JsonVal = nd.get("body")
        if jv_is_list(body):
            for item in jv_list(body):
                _guard_stmt(item, {})
        return
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        target = nd.get("target")
        if jv_is_dict(target):
            nd["target"] = _guard_lvalue(target, env)
        value: JsonVal = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == EXPR:
        value: JsonVal = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == RETURN:
        value: JsonVal = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            nd["value"] = _guard_expr(value, env)
        return
    if kind == IF:
        test: JsonVal = nd.get("test")
        if jv_is_dict(test) or jv_is_list(test):
            nd["test"] = _guard_expr(test, env)
        body_env: dict[str, str] = {}
        for env_name, env_type in env.items():
            body_env[env_name] = env_type
        _guard_env_merge(body_env, _guard_narrowing_from_expr(nd.get("test")))
        orelse_env: dict[str, str] = {}
        for env_name, env_type in env.items():
            orelse_env[env_name] = env_type
        _guard_env_merge(orelse_env, _invert_guard_narrowing_from_expr(nd.get("test")))
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), orelse_env)
        return
    if kind == WHILE:
        test: JsonVal = nd.get("test")
        if jv_is_dict(test) or jv_is_list(test):
            nd["test"] = _guard_expr(test, env)
        body_env: dict[str, str] = {}
        for env_name, env_type in env.items():
            body_env[env_name] = env_type
        _guard_env_merge(body_env, _guard_narrowing_from_expr(nd.get("test")))
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR:
        iter_obj: JsonVal = nd.get("iter")
        if jv_is_dict(iter_obj) or jv_is_list(iter_obj):
            nd["iter"] = _guard_expr(iter_obj, env)
        body_env: dict[str, str] = {}
        for env_name, env_type in env.items():
            body_env[env_name] = env_type
        for name in _target_names(nd.get("target")):
            if name in body_env:
                body_env[name] = ""
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR_RANGE:
        start_val: JsonVal = nd.get("start")
        if jv_is_dict(start_val) or jv_is_list(start_val):
            nd["start"] = _guard_expr(start_val, env)
        stop_val: JsonVal = nd.get("stop")
        if jv_is_dict(stop_val) or jv_is_list(stop_val):
            nd["stop"] = _guard_expr(stop_val, env)
        step_val: JsonVal = nd.get("step")
        if jv_is_dict(step_val) or jv_is_list(step_val):
            nd["step"] = _guard_expr(step_val, env)
        body_env: dict[str, str] = {}
        for env_name, env_type in env.items():
            body_env[env_name] = env_type
        for name in _target_names(nd.get("target")):
            if name in body_env:
                body_env[name] = ""
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == FOR_CORE:
        iter_plan = nd.get("iter_plan")
        if jv_is_dict(iter_plan):
            iter_plan_node: Node = jv_dict(iter_plan)
            iter_expr_val: JsonVal = iter_plan_node.get("iter_expr")
            if jv_is_dict(iter_expr_val) or jv_is_list(iter_expr_val):
                iter_plan_node["iter_expr"] = _guard_expr(iter_expr_val, env)
            start_val2: JsonVal = iter_plan_node.get("start")
            if jv_is_dict(start_val2) or jv_is_list(start_val2):
                iter_plan_node["start"] = _guard_expr(start_val2, env)
            stop_val2: JsonVal = iter_plan_node.get("stop")
            if jv_is_dict(stop_val2) or jv_is_list(stop_val2):
                iter_plan_node["stop"] = _guard_expr(stop_val2, env)
            step_val2: JsonVal = iter_plan_node.get("step")
            if jv_is_dict(step_val2) or jv_is_list(step_val2):
                iter_plan_node["step"] = _guard_expr(step_val2, env)
        body_env: dict[str, str] = {}
        for env_name2, env_type2 in env.items():
            body_env[env_name2] = env_type2
        for name in _target_names(nd.get("target_plan")):
            if name in body_env:
                body_env[name] = ""
        _guard_stmt_list(nd.get("body"), body_env)
        _guard_stmt_list(nd.get("orelse"), env)
        return
    if kind == TRY:
        _guard_stmt_list(nd.get("body"), env)
        handlers = nd.get("handlers")
        if jv_is_list(handlers):
            for handler in jv_list(handlers):
                if not jv_is_dict(handler):
                    continue
                handler_node: Node = jv_dict(handler)
                body = handler_node.get("body")
                if jv_is_list(body):
                    _guard_stmt_list(jv_list(body), env)
        _guard_stmt_list(nd.get("orelse"), env)
        _guard_stmt_list(nd.get("finalbody"), env)
        return
    for key in list(nd.keys()):
        value: JsonVal = nd[key]
        if jv_is_dict(value) or jv_is_list(value):
            nd[key] = _guard_expr(value, env)


def apply_guard_narrowing(module: Node, ctx: CompileContext) -> Node:
    env = _guard_storage_env(module)
    body_env: dict[str, str] = {}
    for key, value in env.items():
        body_env[key] = value
    main_guard_env: dict[str, str] = {}
    for key, value in env.items():
        main_guard_env[key] = value
    _guard_stmt_list(module.get("body"), body_env)
    _guard_stmt_list(module.get("main_guard_body"), main_guard_env)
    return module


def _guard_env_merge(dst: dict[str, str], narrowed: dict[str, str]) -> None:
    for name, target_type in narrowed.items():
        dst[name] = target_type


def _guard_storage_env(module: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    body = module.get("body")
    if jv_is_list(body):
        _guard_collect_storage_types(jv_list(body), out)
    main_guard_body = module.get("main_guard_body")
    if jv_is_list(main_guard_body):
        _guard_collect_storage_types(jv_list(main_guard_body), out)
    return out


def _guard_function_env(func: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    arg_types = func.get("arg_types")
    if jv_is_dict(arg_types):
        arg_types_node: Node = jv_dict(arg_types)
        for arg_name, arg_type in arg_types_node.items():
            arg_name_text = str(arg_name).strip()
            arg_type_text = _tp_safe(arg_type)
            if arg_name_text != "" and arg_type_text != "":
                out["__storage__:" + arg_name_text] = arg_type_text
    body = func.get("body")
    if jv_is_list(body):
        _guard_collect_storage_types(jv_list(body), out)
    return out


def _guard_collect_storage_types(stmts: list[JsonVal], out: dict[str, str]) -> None:
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = _tp_safe(stmt_node.get("kind"))
        if kind == FUNCTION_DEF or kind == CLOSURE_DEF:
            name = _tp_safe(stmt_node.get("name"))
            if name != "":
                out["__storage__:" + name] = _closure_callable_type(stmt_node)
            arg_types = stmt_node.get("arg_types")
            if jv_is_dict(arg_types):
                arg_types_node: Node = jv_dict(arg_types)
                for arg_name, arg_type in arg_types_node.items():
                    arg_name_text = str(arg_name).strip()
                    arg_type_text = _tp_safe(arg_type)
                    if arg_name_text != "" and arg_type_text != "":
                        out["__storage__:" + arg_name_text] = arg_type_text
            continue
        if kind == CLASS_DEF:
            name2 = _tp_safe(stmt_node.get("name"))
            if name2 != "":
                out["__storage__:" + name2] = name2
            continue
        if kind == VAR_DECL:
            name3 = _tp_safe(stmt_node.get("name"))
            type3 = _tp_safe(stmt_node.get("type"))
            if name3 != "" and type3 != "":
                out["__storage__:" + name3] = type3
        elif kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
            _guard_collect_target_storage(stmt_node.get("target"), stmt_node, out)
        elif kind == FOR or kind == FOR_RANGE:
            target_type = _tp_safe(stmt_node.get("target_type"))
            _guard_collect_target_storage_direct(stmt_node.get("target"), target_type, out)
        elif kind == FOR_CORE:
            _guard_collect_target_plan_storage(stmt_node.get("target_plan"), out)
        body = stmt_node.get("body")
        if jv_is_list(body):
            _guard_collect_storage_types(jv_list(body), out)
        orelse = stmt_node.get("orelse")
        if jv_is_list(orelse):
            _guard_collect_storage_types(jv_list(orelse), out)
        finalbody = stmt_node.get("finalbody")
        if jv_is_list(finalbody):
            _guard_collect_storage_types(jv_list(finalbody), out)
        handlers = stmt_node.get("handlers")
        if jv_is_list(handlers):
            for handler in jv_list(handlers):
                if not jv_is_dict(handler):
                    continue
                handler_node: Node = jv_dict(handler)
                ex_name = _tp_safe(handler_node.get("name"))
                if ex_name != "":
                    out["__storage__:" + ex_name] = "BaseException"
                hbody = handler_node.get("body")
                if jv_is_list(hbody):
                    _guard_collect_storage_types(jv_list(hbody), out)


def _guard_collect_target_storage(target: JsonVal, stmt: Node, out: dict[str, str]) -> None:
    stmt = stmt
    out = out
    decl_type = _tp_safe(stmt.get("decl_type"))
    if decl_type == "":
        decl_type = _tp_safe(stmt.get("annotation"))
    if decl_type == "":
        value = stmt.get("value")
        if jv_is_dict(value):
            value_node: Node = jv_dict(value)
            decl_type = _tp_safe(value_node.get("resolved_type"))
    _guard_collect_target_storage_direct(target, decl_type, out)


def _guard_collect_target_storage_direct(target: JsonVal, target_type: str, out: dict[str, str]) -> None:
    if not jv_is_dict(target):
        return
    target_node: Node = jv_dict(target)
    kind = _tp_safe(target_node.get("kind"))
    if kind == NAME:
        name = _tp_safe(target_node.get("id"))
        if name != "" and target_type != "":
            out["__storage__:" + name] = target_type
        return
    if kind == TUPLE or kind == LIST:
        elements = target_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _guard_collect_target_storage_direct(elem, target_type, out)


def _guard_collect_target_plan_storage(target_plan: JsonVal, out: dict[str, str]) -> None:
    if not jv_is_dict(target_plan):
        return
    target_plan_node: Node = jv_dict(target_plan)
    kind = _tp_safe(target_plan_node.get("kind"))
    if kind == NAME_TARGET:
        name = _tp_safe(target_plan_node.get("id"))
        target_type = _tp_safe(target_plan_node.get("target_type"))
        if name != "" and target_type != "":
            out["__storage__:" + name] = target_type
        return
    if kind == TUPLE_TARGET:
        elements = target_plan_node.get("elements")
        if jv_is_list(elements):
            for elem in jv_list(elements):
                _guard_collect_target_plan_storage(elem, out)


# ===========================================================================
# type propagation
# ===========================================================================

def _tp_safe(v: JsonVal) -> str:
    return ("" + jv_str(v)).strip()


def _tp_assign_target(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tp_assign_target(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if _is_function_like_kind(kind):
        rt = _tp_safe(nd.get("return_type"))
        returns = nd.get("returns")
        if returns is None and rt not in ("", "unknown"):
            nd["returns"] = rt
    if kind in (ASSIGN, ANN_ASSIGN):
        target = nd.get("target")
        value = nd.get("value")
        if jv_is_dict(target):
            target_node: Node = jv_dict(target)
            tt = _tp_safe(target_node.get("resolved_type"))
            if tt in ("", "unknown"):
                inf = _tp_safe(nd.get("decl_type"))
                if inf in ("", "unknown"):
                    inf = _tp_safe(nd.get("annotation"))
                if inf in ("", "unknown") and jv_is_dict(value):
                    value_node: Node = jv_dict(value)
                    inf = _tp_safe(value_node.get("resolved_type"))
                if inf not in ("", "unknown"):
                    target_node["resolved_type"] = inf
                    if _tp_safe(nd.get("decl_type")) in ("", "unknown"):
                        nd["decl_type"] = inf
            if jv_is_dict(value):
                value_node2: Node = jv_dict(value)
                vt = _tp_safe(value_node2.get("resolved_type"))
                dt = _tp_safe(nd.get("decl_type"))
                if dt not in ("", "unknown") and "unknown" in vt:
                    vk = "" + jv_str(value_node2.get("kind", ""))
                    if vk in (LIST, DICT, SET):
                        value_node2["resolved_type"] = dt
            if ("" + jv_str(target_node.get("kind", ""))) == TUPLE and jv_is_dict(value):
                value_node3: Node = jv_dict(value)
                _tp_tuple_targets(target_node, value_node3)
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _tp_assign_target(v)


def _tp_tuple_targets(target: Node, value: Node) -> None:
    vt = _tp_safe(value.get("resolved_type"))
    if not (vt.startswith("tuple[") and vt.endswith("]")):
        return
    inner = vt[6:-1]
    ets = _split_comma_types(inner)
    elements = target.get("elements")
    if not jv_is_list(elements):
        return
    i = 0
    for elem in jv_list(elements):
        if i >= len(ets) or not jv_is_dict(elem):
            i += 1
            continue
        elem_node: Node = jv_dict(elem)
        et = _tp_safe(elem_node.get("resolved_type"))
        if et in ("", "unknown"):
            elem_node["resolved_type"] = ets[i].strip()
        i += 1


def _tp_binop(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tp_binop(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _tp_binop(v)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == BIN_OP:
        resolved_type = _tp_safe(nd.get("resolved_type"))
        if resolved_type not in ("", "unknown") and "|" not in resolved_type:
            return
        left = nd.get("left")
        right = nd.get("right")
        left_type = ""
        right_type = ""
        if jv_is_dict(left):
            left_node: Node = jv_dict(left)
            left_type = _tp_safe(left_node.get("resolved_type"))
        if jv_is_dict(right):
            right_node: Node = jv_dict(right)
            right_type = _tp_safe(right_node.get("resolved_type"))
        if left_type in ("", "unknown") and right_type in ("", "unknown"):
            return
        float_types = {"float32", "float64"}
        int_types = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}
        if left_type in float_types or right_type in float_types:
            nd["resolved_type"] = "float64"
        elif left_type in int_types and right_type in int_types:
            nd["resolved_type"] = "int64"
        elif left_type == "str" or right_type == "str":
            if ("" + jv_str(nd.get("op", ""))) == "Add":
                nd["resolved_type"] = "str"
        elif left_type not in ("", "unknown"):
            nd["resolved_type"] = left_type
        elif right_type not in ("", "unknown"):
            nd["resolved_type"] = right_type
    if kind == COMPARE:
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            nd["resolved_type"] = "bool"
    if kind == SUBSCRIPT:
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            value = nd.get("value")
            if jv_is_dict(value):
                value_node2: Node = jv_dict(value)
                value_type = _tp_safe(value_node2.get("resolved_type"))
                if value_type == "str":
                    nd["resolved_type"] = "str"
                elif value_type in ("bytes", "bytearray"):
                    nd["resolved_type"] = "int32"
                elif value_type.startswith("list[") and value_type.endswith("]"):
                    nd["resolved_type"] = value_type[5:-1].strip()
                elif value_type.startswith("dict[") and value_type.endswith("]"):
                    parts = _split_comma_types(value_type[5:-1])
                    if len(parts) >= 2:
                        nd["resolved_type"] = parts[1].strip()
    if kind == UNARY_OP:
        if _tp_safe(nd.get("resolved_type")) in ("", "unknown"):
            operand = nd.get("operand")
            if jv_is_dict(operand):
                operand_node: Node = jv_dict(operand)
                operand_type = _tp_safe(operand_node.get("resolved_type"))
                if operand_type == "bool" and ("" + jv_str(nd.get("op", ""))) == "Not":
                    nd["resolved_type"] = "bool"
                elif operand_type not in ("", "unknown"):
                    nd["resolved_type"] = operand_type


def _tp_truediv(node: JsonVal) -> JsonVal:
    replacement = _try_truediv(node)
    current = node if replacement is None else replacement
    if jv_is_list(current):
        out_list: list[JsonVal] = _passes_empty_jv_list()
        for item in jv_list(current):
            out_list.append(_tp_truediv(item))
        return out_list
    if not jv_is_dict(current):
        return current
    nd: Node = jv_dict(current)
    out: Node = _passes_empty_node()
    for key in nd.keys():
        key_s = "" + jv_str(key)
        if key_s == "":
            continue
        value = nd.get(key_s)
        if jv_is_dict(value) or jv_is_list(value):
            out[key_s] = _tp_truediv(value)
        else:
            out[key_s] = value
    return out


def _try_truediv(node: JsonVal) -> JsonVal:
    if not jv_is_dict(node):
        return None
    node_obj: Node = jv_dict(node)
    if ("" + jv_str(node_obj.get("kind", ""))) != BIN_OP or ("" + jv_str(node_obj.get("op", ""))) != "Div":
        return None
    left = node_obj.get("left")
    if not jv_is_dict(left):
        return None
    left_node: Node = jv_dict(left)
    left_type = _tp_safe(left_node.get("resolved_type"))
    if left_type != "Path":
        return None
    right = node_obj.get("right")
    func_node: Node = _passes_empty_node()
    func_node["kind"] = ATTRIBUTE
    func_node["value"] = left_node
    func_node["attr"] = "joinpath"
    func_node["resolved_type"] = "Path"
    args: list[JsonVal] = _passes_empty_jv_list()
    if right is not None:
        args.append(right)
    call: Node = _passes_empty_node()
    call["kind"] = CALL
    call["func"] = func_node
    call["args"] = args
    call["keywords"] = _passes_empty_jv_list()
    call["resolved_type"] = "Path"
    span = node_obj.get("source_span")
    if jv_is_dict(span):
        call["source_span"] = jv_dict(span)
    return call


def _collect_fn_callable_types(module: Node) -> dict[str, str]:
    out: dict[str, str] = {}
    renamed: dict[str, str] = {}
    renamed_symbols = module.get("renamed_symbols")
    if jv_is_dict(renamed_symbols):
        renamed_map: Node = jv_dict(renamed_symbols)
        for renamed_name in renamed_map.keys():
            renamed_name_s = "" + jv_str(renamed_name)
            original_name_s = _tp_safe(renamed_map.get(renamed_name_s))
            if renamed_name_s != "" and original_name_s != "":
                renamed[renamed_name_s] = original_name_s
    body = module.get("body")
    if not jv_is_list(body):
        return out
    for stmt in jv_list(body):
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = "" + jv_str(stmt_node.get("kind", ""))
        if _is_function_like_kind(kind):
            name = _tp_safe(stmt_node.get("name"))
            ret = _tp_safe(stmt_node.get("return_type"))
            if name != "" and ret not in ("", "unknown"):
                arg_order = stmt_node.get("arg_order")
                arg_types = stmt_node.get("arg_types")
                if jv_is_list(arg_order) and jv_is_dict(arg_types):
                    params: list[str] = []
                    for param_name in jv_list(arg_order):
                        param_name_s = _tp_safe(param_name)
                        if param_name_s != "" and param_name_s != "self":
                            params.append(param_name_s)
                    param_types: list[str] = []
                    arg_type_map: Node = jv_dict(arg_types)
                    for param_name in params:
                        param_types.append(_tp_safe(arg_type_map.get(param_name)))
                    ct = "callable[[" + ",".join(param_types) + "]," + ret + "]"
                else:
                    ct = "callable[[]," + ret + "]"
                out[name] = ct
                original_name2 = renamed.get(name, "")
                if original_name2 != "":
                    out[original_name2] = ct
        elif kind == CLASS_DEF:
            class_body = stmt_node.get("body")
            if jv_is_list(class_body):
                for method in jv_list(class_body):
                    if jv_is_dict(method):
                        method_node: Node = jv_dict(method)
                        if ("" + jv_str(method_node.get("kind", ""))) == FUNCTION_DEF:
                            method_name = _tp_safe(method_node.get("name"))
                            if method_name != "":
                                ret = _tp_safe(method_node.get("return_type"))
                                if ret not in ("", "unknown"):
                                    out[method_name] = "callable"
    return out

def _tp_fn_refs(node: JsonVal, ft: dict[str, str]) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tp_fn_refs(item, ft)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if _tp_safe(nd.get("kind")) == "Call":
        args = nd.get("args")
        if jv_is_list(args):
            for arg in jv_list(args):
                if jv_is_dict(arg):
                    arg_node: Node = jv_dict(arg)
                    if _tp_safe(arg_node.get("kind")) == "Name":
                        name = _tp_safe(arg_node.get("id"))
                        if name in ft:
                            current_type = _tp_safe(arg_node.get("resolved_type"))
                            if current_type in ("", "unknown"):
                                arg_node["resolved_type"] = ft[name]
    for value in nd.values():
        if jv_is_dict(value) or jv_is_list(value):
            _tp_fn_refs(value, ft)


_FLOAT_TAGS: set[str] = {
    "stdlib.method.sqrt", "stdlib.method.sin", "stdlib.method.cos",
    "stdlib.method.tan", "stdlib.method.exp", "stdlib.method.log",
    "stdlib.method.log10", "stdlib.method.fabs", "stdlib.method.floor",
    "stdlib.method.ceil", "stdlib.method.pow",
}
_PASSES_INT_TYPES: set[str] = {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}


def _tp_numeric_casts(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tp_numeric_casts(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if _tp_safe(nd.get("kind")) == "Call":
        call_resolved_type = _tp_safe(nd.get("resolved_type"))
        is_float = call_resolved_type == "float64"
        if not is_float:
            semantic_tag = _tp_safe(nd.get("semantic_tag"))
            is_float = semantic_tag in _FLOAT_TAGS
        if is_float:
            args = nd.get("args")
            if jv_is_list(args):
                for arg in jv_list(args):
                    if jv_is_dict(arg):
                        arg_node: Node = jv_dict(arg)
                        arg_type = _tp_safe(arg_node.get("resolved_type"))
                        if arg_type in _PASSES_INT_TYPES:
                            existing_casts = arg_node.get("casts")
                            cast_list: list[JsonVal] = _passes_empty_jv_list()
                            if jv_is_list(existing_casts):
                                for cast_item in jv_list(existing_casts):
                                    cast_list.append(cast_item)
                            cast_entry: Node = _passes_empty_node()
                            cast_entry["on"] = "body"
                            cast_entry["from"] = arg_type
                            cast_entry["to"] = "float64"
                            cast_entry["reason"] = "numeric_promotion"
                            cast_list.append(cast_entry)
                            arg_node["casts"] = cast_list
    for value in nd.values():
        if jv_is_dict(value) or jv_is_list(value):
            _tp_numeric_casts(value)


def _tp_is_unknown_container_literal(node: Node) -> bool:
    kind = _tp_safe(node.get("kind"))
    resolved_type = _tp_safe(node.get("resolved_type"))
    if kind == LIST:
        elements = node.get("elements")
        return jv_is_list(elements) and len(jv_list(elements)) == 0 and resolved_type in ("", "unknown", "list[unknown]")
    if kind == DICT:
        entries = node.get("entries")
        return jv_is_list(entries) and len(jv_list(entries)) == 0 and resolved_type in ("", "unknown", "dict[unknown,unknown]")
    if kind == SET:
        elements2 = node.get("elements")
        return jv_is_list(elements2) and len(jv_list(elements2)) == 0 and resolved_type in ("", "unknown", "set[unknown]")
    return False


def _tp_adopt_peer_container_type(candidate: JsonVal, peer: JsonVal) -> None:
    if not jv_is_dict(candidate) or not jv_is_dict(peer):
        return
    candidate_node: Node = jv_dict(candidate)
    if not _tp_is_unknown_container_literal(candidate_node):
        return
    peer_node: Node = jv_dict(peer)
    peer_type = normalize_type_name(peer_node.get("resolved_type"))
    kind = _tp_safe(candidate_node.get("kind"))
    if kind == LIST and peer_type.startswith("list[") and peer_type.endswith("]"):
        candidate_node["resolved_type"] = peer_type
    elif kind == DICT and peer_type.startswith("dict[") and peer_type.endswith("]"):
        candidate_node["resolved_type"] = peer_type
    elif kind == SET and peer_type.startswith("set[") and peer_type.endswith("]"):
        candidate_node["resolved_type"] = peer_type


def _tp_assert_eq_peer_literals(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _tp_assert_eq_peer_literals(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if _tp_safe(nd.get("kind")) == "Call":
        func = nd.get("func")
        if jv_is_dict(func):
            func_node: Node = jv_dict(func)
            if _tp_safe(func_node.get("kind")) == "Name" and _tp_safe(func_node.get("id")) == "py_assert_eq":
                args = nd.get("args")
                if jv_is_list(args):
                    arg_list = jv_list(args)
                    if len(arg_list) >= 2:
                        arg_items: list[JsonVal] = _passes_empty_jv_list()
                        for arg_item in arg_list:
                            arg_items.append(arg_item)
                            if len(arg_items) >= 2:
                                break
                        if len(arg_items) >= 2:
                            _tp_adopt_peer_container_type(arg_items[0], arg_items[1])
                            _tp_adopt_peer_container_type(arg_items[1], arg_items[0])
    for value in nd.values():
        if jv_is_dict(value) or jv_is_list(value):
            _tp_assert_eq_peer_literals(value)

def apply_type_propagation(module: Node, ctx: CompileContext) -> Node:
    _tp_binop(module)
    rewritten = _tp_truediv(module)
    if jv_is_dict(rewritten):
        module = jv_dict(rewritten)
    _tp_assign_target(module)
    ft = _collect_fn_callable_types(module)
    if ft:
        _tp_fn_refs(module, ft)
    _tp_numeric_casts(module)
    _tp_assert_eq_peer_literals(module)
    return module


# ===========================================================================
# yields_dynamic
# ===========================================================================

def _yd_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _yd_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = "" + jv_str(nd.get("kind", ""))
    if kind == IF_EXP:
        nd["yields_dynamic"] = True
    if kind == CALL:
        func = nd.get("func")
        if jv_is_dict(func):
            func_node: Node = jv_dict(func)
            func_kind = "" + jv_str(func_node.get("kind", ""))
            if func_kind == NAME:
                callee_name = _tp_safe(func_node.get("id"))
                if callee_name == "min" or callee_name == "max":
                    nd["yields_dynamic"] = True
            if func_kind == ATTRIBUTE:
                attr = _tp_safe(func_node.get("attr"))
                if attr == "get":
                    owner = func_node.get("value")
                    if jv_is_dict(owner):
                        owner_node: Node = jv_dict(owner)
                        owner_type = _tp_safe(owner_node.get("resolved_type"))
                        if owner_type.startswith("dict["):
                            nd["yields_dynamic"] = True
    for value in nd.values():
        if jv_is_dict(value) or jv_is_list(value):
            _yd_walk(value)


def apply_yields_dynamic(module: Node, ctx: CompileContext) -> None:
    _yd_walk(module)


# ===========================================================================
# lowering profile semantics
# ===========================================================================

def _make_name_ref(name: str, resolved_type: str) -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = NAME
    out["id"] = name
    out["resolved_type"] = resolved_type
    return out


def _make_none_const() -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = CONSTANT
    out["value"] = None
    out["resolved_type"] = "None"
    return out


def _make_container_method_call(
    owner_name: str,
    owner_type: str,
    attr: str,
    *,
    args: list[JsonVal],
    result_type: str,
) -> Node:
    attr_node: Node = _passes_empty_node()
    attr_node["kind"] = ATTRIBUTE
    attr_node["value"] = _make_name_ref(owner_name, owner_type)
    attr_node["attr"] = attr
    attr_node["resolved_type"] = "callable"

    call_node: Node = _passes_empty_node()
    call_node["kind"] = CALL
    call_node["func"] = attr_node
    call_node["args"] = args
    call_node["keywords"] = _passes_empty_jv_list()
    call_node["resolved_type"] = result_type
    call_node["lowered_kind"] = "BuiltinCall"

    owner_base = owner_type
    if owner_base.startswith("list["):
        owner_base = "list"
    elif owner_base.startswith("dict["):
        owner_base = "dict"
    elif owner_base.startswith("set["):
        owner_base = "set"

    runtime_call = owner_base + "." + attr if owner_base != "" else attr
    call_node["runtime_call"] = runtime_call
    call_node["runtime_symbol"] = runtime_call
    call_node["runtime_call_adapter_kind"] = "builtin"
    if owner_base == "list":
        call_node["runtime_module_id"] = "pytra.core.list"
    elif owner_base == "dict":
        call_node["runtime_module_id"] = "pytra.core.dict"
    elif owner_base == "set":
        call_node["runtime_module_id"] = "pytra.core.set"
    call_node["semantic_tag"] = "stdlib.method." + attr
    call_node["runtime_owner"] = deep_copy_json(attr_node["value"])

    if attr in ("append", "extend", "insert", "remove", "pop", "clear", "update", "add", "discard", "setdefault", "sort", "reverse"):
        meta: Node = _passes_empty_node()
        meta["mutates_receiver"] = True
        call_node["meta"] = meta
    return call_node


def _make_with_method_call(
    owner_name: str,
    owner_type: str,
    attr: str,
    *,
    args: list[JsonVal],
    result_type: str,
    runtime_call: str = "",
    runtime_symbol: str = "",
    runtime_module_id: str = "",
    semantic_tag: str = "",
) -> Node:
    attr_node: Node = _passes_empty_node()
    attr_node["kind"] = ATTRIBUTE
    attr_node["value"] = _make_name_ref(owner_name, owner_type)
    attr_node["attr"] = attr
    attr_node["resolved_type"] = "callable"
    call_node: Node = _passes_empty_node()
    call_node["kind"] = CALL
    call_node["func"] = attr_node
    call_node["args"] = args
    call_node["keywords"] = _passes_empty_jv_list()
    call_node["resolved_type"] = result_type
    if runtime_call != "":
        call_node["runtime_call"] = runtime_call
        call_node["resolved_runtime_call"] = runtime_call
    if runtime_symbol != "":
        call_node["runtime_symbol"] = runtime_symbol
    if runtime_module_id != "":
        call_node["runtime_module_id"] = runtime_module_id
    if semantic_tag != "":
        call_node["semantic_tag"] = semantic_tag
    return call_node


def _make_expr_stmt(value: Node) -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = EXPR
    out["value"] = value
    return out


def _lower_covariant_copy(node: Node, ctx: CompileContext) -> JsonVal:
    if _sk(node) != CALL or ctx.lowering_profile.container_covariance:
        return node
    func = node.get("func")
    args = _node_list(node, "args")
    if not jv_is_dict(func) or _str(func, "kind") != NAME or _str(func, "id") != "list" or len(args) != 1:
        return node
    source = args[0]
    if not jv_is_dict(source):
        return node
    source_node: Node = jv_dict(source)
    source_type = normalize_type_name(source_node.get("resolved_type"))
    target_type = normalize_type_name(node.get("resolved_type"))
    source_elem_type = _list_elem_type(source_type)
    target_elem_type = _list_elem_type(target_type)
    if source_elem_type == "" or target_elem_type == "" or source_elem_type == target_elem_type:
        return node
    out: Node = _passes_empty_node()
    out["kind"] = COVARIANT_COPY
    out["source"] = deep_copy_json(source_node)
    out["source_type"] = source_type
    out["source_elem_type"] = source_elem_type
    out["target_type"] = target_type
    out["target_elem_type"] = target_elem_type
    out["resolved_type"] = target_type
    return out


def _apply_profile_expr(node: JsonVal, ctx: CompileContext) -> JsonVal:
    if jv_is_list(node):
        items: list[JsonVal] = _passes_empty_jv_list()
        for item in jv_list(node):
            items.append(_apply_profile_expr(item, ctx))
        return items
    if not jv_is_dict(node):
        return node
    out: Node = _passes_empty_node()
    node_map: Node = jv_dict(node)
    for key in node_map.keys():
        key_s = "" + jv_str(key)
        if key_s == "":
            continue
        value = node_map.get(key_s)
        if jv_is_dict(value) or jv_is_list(value):
            out[key_s] = _apply_profile_expr(value, ctx)
        else:
            out[key_s] = value
    if (
        _sk(out) == ATTRIBUTE
        and ctx.lowering_profile.property_style == "field_access"
        and _str(out, "attribute_access_kind") == "property_getter"
    ):
        out["attribute_access_kind"] = "field_access"
    return _lower_covariant_copy(out, ctx)


def _union_return_type(return_type: str) -> str:
    rt = "" + normalize_type_name(return_type)
    if rt in ("", "unknown", "None"):
        return "Exception"
    if rt.startswith("multi_return["):
        return rt
    return "multi_return[" + rt + ",Exception]"


def _collect_local_can_raise_symbols(module: Node) -> set[str]:
    funcs: dict[str, Node] = {}
    for stmt in _node_list(module, "body"):
        if jv_is_dict(stmt) and _sk(stmt) in (FUNCTION_DEF, CLOSURE_DEF):
            name = _str(stmt, "name")
            if name != "":
                funcs[name] = jv_dict(stmt)

    def _contains_raise(node: JsonVal) -> bool:
        if jv_is_list(node):
            for item in jv_list(node):
                if _contains_raise(item):
                    return True
            return False
        if not jv_is_dict(node):
            return False
        kind = _sk(node)
        if kind == "Raise":
            return True
        if kind in (FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF):
            return False
        node_map: Node = jv_dict(node)
        for value in node_map.values():
            if jv_is_dict(value) or jv_is_list(value):
                if _contains_raise(value):
                    return True
        return False

    def _contains_call_to(node: JsonVal, can_raise: set[str]) -> bool:
        if jv_is_list(node):
            for item in jv_list(node):
                if _contains_call_to(item, can_raise):
                    return True
            return False
        if not jv_is_dict(node):
            return False
        kind = _sk(node)
        if kind == CALL:
            node_map3: Node = jv_dict(node)
            func: JsonVal = None
            if "func" in node_map3:
                func = node_map3["func"]
            if jv_is_dict(func) and _sk(func) == NAME and _str(func, "id") in can_raise:
                return True
        if kind in (FUNCTION_DEF, CLOSURE_DEF, CLASS_DEF):
            return False
        node_map2: Node = jv_dict(node)
        for value in node_map2.values():
            if jv_is_dict(value) or jv_is_list(value):
                if _contains_call_to(value, can_raise):
                    return True
        return False

    can_raise: set[str] = set()
    for name, fn in funcs.items():
        if _contains_raise(_node_list(fn, "body")):
            can_raise.add(name)
    changed = True
    while changed:
        changed = False
        for name, fn in funcs.items():
            if name in can_raise:
                continue
            if _contains_call_to(_node_list(fn, "body"), can_raise):
                can_raise.add(name)
                changed = True
    return can_raise


def _raise_exception_type(stmt: Node) -> str:
    exc = stmt.get("exc")
    if jv_is_dict(exc):
        exc_node: Node = jv_dict(exc)
        if _sk(exc_node) == CALL:
            func: JsonVal = None
            if "func" in exc_node:
                func = exc_node["func"]
            if jv_is_dict(func) and _sk(func) == NAME:
                name = _str(func, "id")
                if name != "":
                    return name
        rt = _str(exc_node, "resolved_type")
        if rt != "":
            return rt
    return "RuntimeError"


def _is_can_raise_call(value: JsonVal, can_raise_symbols: set[str]) -> bool:
    if not jv_is_dict(value) or _sk(value) != CALL:
        return False
    value_node: Node = jv_dict(value)
    func: JsonVal = None
    if "func" in value_node:
        func = value_node["func"]
    return jv_is_dict(func) and _sk(func) == NAME and _str(func, "id") in can_raise_symbols


def _make_error_check(call_node: Node, ok_target: JsonVal, ok_type: str, on_error: str) -> Node:
    out: Node = _passes_empty_node()
    out["kind"] = ERROR_CHECK
    out["call"] = call_node
    out["ok_target"] = ok_target
    out["ok_type"] = ok_type
    out["on_error"] = on_error
    return out


def _rewrite_expr_error_checks(
    node: JsonVal,
    ctx: CompileContext,
    can_raise_symbols: set[str],
    on_error: str,
) -> tuple[list[JsonVal], JsonVal]:
    if jv_is_list(node):
        prefix: list[JsonVal] = _passes_empty_jv_list()
        items: list[JsonVal] = _passes_empty_jv_list()
        for item in jv_list(node):
            item_prefix, item_out = _rewrite_expr_error_checks(item, ctx, can_raise_symbols, on_error)
            prefix.extend(item_prefix)
            items.append(item_out)
        return prefix, items
    if not jv_is_dict(node):
        empty_prefix: list[JsonVal] = _passes_empty_jv_list()
        return empty_prefix, node
    out: Node = _passes_empty_node()
    prefix2: list[JsonVal] = _passes_empty_jv_list()
    node_map4: Node = jv_dict(node)
    for key in node_map4.keys():
        key_s = "" + jv_str(key)
        if key_s == "":
            continue
        value = node_map4.get(key_s)
        if jv_is_dict(value) or jv_is_list(value):
            value_prefix, value_out = _rewrite_expr_error_checks(value, ctx, can_raise_symbols, on_error)
            prefix2.extend(value_prefix)
            out[key_s] = value_out
        else:
            out[key_s] = value
    if _is_can_raise_call(out, can_raise_symbols):
        ok_type = _str(out, "resolved_type")
        ctx2 = ctx
        tmp_name = ctx2.next_comp_name()
        tmp_target = _make_name_ref(tmp_name, ok_type)
        prefix2.append(_make_error_check(out, tmp_target, ok_type, on_error))
        return prefix2, deep_copy_json(tmp_target)
    return prefix2, out


def _apply_profile_stmt(
    stmt: JsonVal,
    ctx: CompileContext,
    can_raise_symbols: set[str] | None = None,
    *,
    current_function_can_raise: bool = False,
    catch_mode: bool = False,
) -> list[JsonVal]:
    if not jv_is_dict(stmt):
        single_stmt: list[JsonVal] = _passes_empty_jv_list()
        single_stmt.append(stmt)
        return single_stmt
    out = _apply_profile_expr(stmt, ctx)
    if not jv_is_dict(out):
        single_out: list[JsonVal] = _passes_empty_jv_list()
        single_out.append(out)
        return single_out
    out_node: Node = jv_dict(out)

    if ctx.lowering_profile.exception_style == "union_return":
        active_symbols: set[str] = set()
        if can_raise_symbols is not None:
            for symbol in can_raise_symbols:
                active_symbols.add(symbol)
        kind0 = _sk(out_node)
        if kind0 in (FUNCTION_DEF, CLOSURE_DEF):
            fn_name = _str(out_node, "name")
            fn_can_raise = fn_name in active_symbols
            out_node["body"] = _apply_profile_stmts(
                _node_list(out_node, "body"),
                ctx,
                active_symbols,
                current_function_can_raise=fn_can_raise,
                catch_mode=False,
            )
            if fn_can_raise:
                out_node["return_type"] = _union_return_type(_str(out_node, "return_type"))
                meta = out_node.get("meta")
                meta_node: Node = _passes_empty_node()
                if jv_is_dict(meta):
                    meta_src: Node = jv_dict(meta)
                    for meta_key_s in meta_src.keys():
                        meta_node[meta_key_s] = meta_src.get(meta_key_s)
                can_raise_meta: Node = _passes_empty_node()
                can_raise_meta["schema_version"] = 1
                can_raise_meta["exception_types"] = _passes_empty_jv_list()
                meta_node["can_raise_v1"] = can_raise_meta
                out_node["meta"] = meta_node
            result_fn: list[JsonVal] = _passes_empty_jv_list()
            result_fn.append(out_node)
            return result_fn
        if kind0 == CLASS_DEF:
            out_node["body"] = _apply_profile_stmts(
                _node_list(out_node, "body"),
                ctx,
                active_symbols,
                current_function_can_raise=False,
                catch_mode=False,
            )
            result_class: list[JsonVal] = _passes_empty_jv_list()
            result_class.append(out_node)
            return result_class
        if kind0 == "Raise":
            err: Node = _passes_empty_node()
            err["kind"] = ERROR_RETURN
            err["value"] = out_node.get("exc")
            err["exception_type"] = _raise_exception_type(out_node)
            result_err: list[JsonVal] = _passes_empty_jv_list()
            result_err.append(err)
            return result_err
        if kind0 == TRY:
            err_catch: Node = _passes_empty_node()
            err_catch["kind"] = ERROR_CATCH
            err_catch["body"] = _apply_profile_stmts(
                _node_list(out_node, "body"),
                ctx,
                active_symbols,
                current_function_can_raise=current_function_can_raise,
                catch_mode=True,
            )
            handlers: list[JsonVal] = _passes_empty_jv_list()
            for handler in _node_list(out_node, "handlers"):
                if jv_is_dict(handler):
                    handler_out = _apply_profile_expr(handler, ctx)
                    if jv_is_dict(handler_out):
                        handler_node: Node = jv_dict(handler_out)
                        handler_node["body"] = _apply_profile_stmts(
                            _node_list(handler_node, "body"),
                            ctx,
                            active_symbols,
                            current_function_can_raise=current_function_can_raise,
                            catch_mode=False,
                        )
                        handlers.append(handler_node)
            err_catch["handlers"] = handlers
            err_catch["finalbody"] = _apply_profile_stmts(
                _node_list(out_node, "finalbody"),
                ctx,
                active_symbols,
                current_function_can_raise=current_function_can_raise,
                catch_mode=False,
            )
            result_try: list[JsonVal] = _passes_empty_jv_list()
            result_try.append(err_catch)
            return result_try
        if kind0 in (ASSIGN, ANN_ASSIGN):
            value = out_node.get("value")
            if _is_can_raise_call(value, active_symbols):
                ok_target = out_node.get("target")
                ok_type = ""
                if jv_is_dict(ok_target):
                    ok_type = _str(jv_dict(ok_target), "resolved_type")
                if ok_type == "" and jv_is_dict(value):
                    ok_type = _str(jv_dict(value), "resolved_type")
                checks: list[JsonVal] = _passes_empty_jv_list()
                if jv_is_dict(value):
                    checks.append(_make_error_check(jv_dict(value), ok_target, ok_type, "catch" if catch_mode else "propagate"))
                    return checks
            value_prefix, value_out = _rewrite_expr_error_checks(value, ctx, active_symbols, "catch" if catch_mode else "propagate")
            if len(value_prefix) != 0:
                out_node["value"] = value_out
                result_assign: list[JsonVal] = _passes_empty_jv_list()
                for item in value_prefix:
                    result_assign.append(item)
                result_assign.append(out_node)
                return result_assign
        if kind0 == RETURN:
            value3 = out_node.get("value")
            if jv_is_dict(value3) or jv_is_list(value3):
                value_prefix2, value_out2 = _rewrite_expr_error_checks(value3, ctx, active_symbols, "catch" if catch_mode else "propagate")
                if len(value_prefix2) != 0:
                    out_node["value"] = value_out2
                    result_return: list[JsonVal] = _passes_empty_jv_list()
                    for item in value_prefix2:
                        result_return.append(item)
                    result_return.append(out_node)
                    return result_return
        if kind0 == EXPR:
            value2 = out_node.get("value")
            if _is_can_raise_call(value2, active_symbols):
                ok_type2 = ""
                expr_checks: list[JsonVal] = _passes_empty_jv_list()
                if jv_is_dict(value2):
                    ok_type2 = _str(jv_dict(value2), "resolved_type")
                    expr_checks.append(_make_error_check(jv_dict(value2), None, ok_type2, "catch" if catch_mode else "propagate"))
                    return expr_checks
            value_prefix3, value_out3 = _rewrite_expr_error_checks(value2, ctx, active_symbols, "catch" if catch_mode else "propagate")
            if len(value_prefix3) != 0:
                out_node["value"] = value_out3
                result_expr: list[JsonVal] = _passes_empty_jv_list()
                for item in value_prefix3:
                    result_expr.append(item)
                result_expr.append(out_node)
                return result_expr
        if kind0 in (IF, WHILE):
            test = out_node.get("test")
            if jv_is_dict(test) or jv_is_list(test):
                test_prefix, test_out = _rewrite_expr_error_checks(test, ctx, active_symbols, "catch" if catch_mode else "propagate")
                if len(test_prefix) != 0:
                    out_node["test"] = test_out
                    result_test: list[JsonVal] = _passes_empty_jv_list()
                    for item in test_prefix:
                        result_test.append(item)
                    result_test.append(out_node)
                    return result_test
        if kind0 == WITH:
            context_expr0 = out_node.get("context_expr")
            if jv_is_dict(context_expr0) or jv_is_list(context_expr0):
                expr_prefix, expr_out = _rewrite_expr_error_checks(context_expr0, ctx, active_symbols, "catch" if catch_mode else "propagate")
                if len(expr_prefix) != 0:
                    out_node["context_expr"] = expr_out
                    result_context: list[JsonVal] = _passes_empty_jv_list()
                    for item in expr_prefix:
                        result_context.append(item)
                    result_context.append(out_node)
                    return result_context

    kind = _sk(out_node)
    if kind == WITH:
        out_node["body"] = _apply_profile_stmts(_node_list(out_node, "body"), ctx, can_raise_symbols, current_function_can_raise=current_function_can_raise, catch_mode=catch_mode)
        style = ctx.lowering_profile.with_style
        out_node["with_lowering_style"] = style
        if style != "try_finally":
            result_with: list[JsonVal] = _passes_empty_jv_list()
            result_with.append(out_node)
            return result_with
        var_name = _str(out_node, "var_name")
        ctx2 = ctx
        ctx_name = ctx2.next_comp_name()
        context_expr = out_node.get("context_expr")
        context_type = ""
        if jv_is_dict(context_expr):
            context_type = "" + normalize_type_name(nd_get_str(context_expr, "resolved_type"))
        bind_ctx_stmt: Node = _passes_empty_node()
        bind_ctx_stmt["kind"] = ASSIGN
        bind_ctx_stmt["target"] = _make_name_ref(ctx_name, context_type)
        bind_ctx_stmt["value"] = context_expr
        bind_ctx_stmt["declare"] = True
        if context_type != "":
            bind_ctx_stmt["decl_type"] = context_type
        enter_type = _str(out_node, "with_enter_type")
        if enter_type == "":
            enter_type = context_type
        enter_call = _make_with_method_call(
            ctx_name,
            context_type,
            "__enter__",
            args=_passes_empty_jv_list(),
            result_type=enter_type if enter_type != "" else context_type,
            runtime_call=_str(out_node, "with_enter_runtime_call"),
            runtime_symbol=_str(out_node, "with_enter_runtime_symbol"),
            runtime_module_id=_str(out_node, "with_enter_runtime_module_id"),
            semantic_tag=_str(out_node, "with_enter_semantic_tag"),
        )
        enter_stmt: Node
        if var_name != "":
            enter_stmt = _passes_empty_node()
            enter_stmt["kind"] = ASSIGN
            enter_stmt["target"] = _make_name_ref(var_name, enter_type)
            enter_stmt["value"] = enter_call
            enter_stmt["declare"] = True
            if enter_type != "":
                enter_stmt["decl_type"] = enter_type
        else:
            enter_stmt = _make_expr_stmt(enter_call)
        exit_args: list[JsonVal] = _passes_empty_jv_list()
        exit_args.append(_make_none_const())
        exit_args.append(_make_none_const())
        exit_args.append(_make_none_const())
        exit_call = _make_with_method_call(
            ctx_name,
            context_type,
            "__exit__",
            args=exit_args,
            result_type="None",
            runtime_call=_str(out_node, "with_exit_runtime_call"),
            runtime_symbol=_str(out_node, "with_exit_runtime_symbol"),
            runtime_module_id=_str(out_node, "with_exit_runtime_module_id"),
            semantic_tag=_str(out_node, "with_exit_semantic_tag"),
        )
        try_stmt: Node = _passes_empty_node()
        try_stmt["kind"] = TRY
        try_stmt["body"] = out_node["body"]
        try_stmt["handlers"] = _passes_empty_jv_list()
        try_stmt["orelse"] = _passes_empty_jv_list()
        finalbody: list[JsonVal] = _passes_empty_jv_list()
        finalbody.append(_make_expr_stmt(exit_call))
        try_stmt["finalbody"] = finalbody
        result_try_finally: list[JsonVal] = _passes_empty_jv_list()
        result_try_finally.append(bind_ctx_stmt)
        result_try_finally.append(enter_stmt)
        result_try_finally.append(try_stmt)
        return result_try_finally
    nested_body = out_node.get("body")
    if jv_is_list(nested_body):
        out_node["body"] = _apply_profile_stmts(jv_list(nested_body), ctx, can_raise_symbols, current_function_can_raise=current_function_can_raise, catch_mode=catch_mode)
    nested_orelse = out_node.get("orelse")
    if jv_is_list(nested_orelse):
        out_node["orelse"] = _apply_profile_stmts(jv_list(nested_orelse), ctx, can_raise_symbols, current_function_can_raise=current_function_can_raise, catch_mode=catch_mode)
    nested_finalbody = out_node.get("finalbody")
    if jv_is_list(nested_finalbody):
        out_node["finalbody"] = _apply_profile_stmts(jv_list(nested_finalbody), ctx, can_raise_symbols, current_function_can_raise=current_function_can_raise, catch_mode=catch_mode)
    handlers_obj = out_node.get("handlers")
    if jv_is_list(handlers_obj):
        new_handlers: list[JsonVal] = _passes_empty_jv_list()
        for handler in jv_list(handlers_obj):
            if jv_is_dict(handler):
                handler_out = _apply_profile_expr(handler, ctx)
                if jv_is_dict(handler_out):
                    handler_node2: Node = jv_dict(handler_out)
                    hb = handler_node2.get("body")
                    if jv_is_list(hb):
                        handler_node2["body"] = _apply_profile_stmts(jv_list(hb), ctx, can_raise_symbols, current_function_can_raise=current_function_can_raise, catch_mode=False)
                    new_handlers.append(handler_node2)
            else:
                new_handlers.append(handler)
        out_node["handlers"] = new_handlers
    result_default: list[JsonVal] = _passes_empty_jv_list()
    result_default.append(out_node)
    return result_default

def _apply_profile_stmts(
    stmts: list[JsonVal],
    ctx: CompileContext,
    can_raise_symbols: set[str] | None = None,
    *,
    current_function_can_raise: bool = False,
    catch_mode: bool = False,
) -> list[JsonVal]:
    out: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        lowered = _apply_profile_stmt(
            stmt,
            ctx,
            can_raise_symbols,
            current_function_can_raise=current_function_can_raise,
            catch_mode=catch_mode,
        )
        for item in lowered:
            out.append(item)
    return out


def apply_profile_lowering(module: Node, ctx: CompileContext) -> Node:
    if ctx.lowering_profile.exception_style == "union_return":
        can_raise_symbols: set[str] = _collect_local_can_raise_symbols(module)
        body_obj: JsonVal = module.get("body")
        if jv_is_list(body_obj):
            module["body"] = _apply_profile_stmts(jv_list(body_obj), ctx, can_raise_symbols)
        mg_obj: JsonVal = module.get("main_guard_body")
        if jv_is_list(mg_obj):
            module["main_guard_body"] = _apply_profile_stmts(jv_list(mg_obj), ctx, can_raise_symbols)
        return module
    body_obj2: JsonVal = module.get("body")
    if jv_is_list(body_obj2):
        module["body"] = _apply_profile_stmts(jv_list(body_obj2), ctx, None)
    mg_obj2: JsonVal = module.get("main_guard_body")
    if jv_is_list(mg_obj2):
        module["main_guard_body"] = _apply_profile_stmts(jv_list(mg_obj2), ctx, None)
    return module


# ===========================================================================
# swap detection
# ===========================================================================

def _expr_key(node: JsonVal) -> str:
    if not jv_is_dict(node):
        return ""
    node_map: Node = jv_dict(node)
    kind = nd_get_str(node_map, "kind")
    if kind == NAME:
        return "Name:" + nd_get_str(node_map, "id")
    if kind == SUBSCRIPT:
        val = _expr_key(node_map.get("value"))
        slc = _expr_key(node_map.get("slice"))
        return "Sub:" + val + "[" + slc + "]"
    if kind == CONSTANT:
        return "Const:" + str(node_map.get("value", ""))
    if kind == BIN_OP:
        l2 = _expr_key(node_map.get("left"))
        r2 = _expr_key(node_map.get("right"))
        return "BinOp:" + l2 + nd_get_str(node_map, "op") + r2
    return ""

def _swap_in_stmts(stmts: list[JsonVal], ctx: CompileContext) -> list[JsonVal]:
    result: list[JsonVal] = _passes_empty_jv_list()
    for stmt in stmts:
        if not jv_is_dict(stmt):
            result.append(stmt)
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_get_str(stmt_node, "kind")
        if kind == ASSIGN:
            target = stmt_node.get("target")
            value = stmt_node.get("value")
            if jv_is_dict(target) and jv_is_dict(value):
                target_node: Node = jv_dict(target)
                value_node: Node = jv_dict(value)
                if nd_get_str(target_node, "kind") == TUPLE and nd_get_str(value_node, "kind") == TUPLE:
                    te = target_node.get("elements")
                    if not jv_is_list(te):
                        te = target_node.get("elts", _passes_empty_jv_list())
                    ve = value_node.get("elements")
                    if not jv_is_list(ve):
                        ve = value_node.get("elts", _passes_empty_jv_list())
                    if jv_is_list(te) and jv_is_list(ve):
                        te_items: list[JsonVal] = _passes_empty_jv_list()
                        for item in jv_list(te):
                            te_items.append(item)
                        ve_items: list[JsonVal] = _passes_empty_jv_list()
                        for item in jv_list(ve):
                            ve_items.append(item)
                        if len(te_items) == 2 and len(ve_items) == 2:
                            left = te_items[0]
                            right = te_items[1]
                            vleft = ve_items[0]
                            vright = ve_items[1]
                            if jv_is_dict(left) and jv_is_dict(right) and jv_is_dict(vleft) and jv_is_dict(vright):
                                left_node: Node = jv_dict(left)
                                right_node: Node = jv_dict(right)
                                vleft_node: Node = jv_dict(vleft)
                                vright_node: Node = jv_dict(vright)
                                if _expr_key(left_node) == _expr_key(vright_node) and _expr_key(right_node) == _expr_key(vleft_node):
                                    ctx2 = ctx
                                    tmp = ctx2.next_swap_name()
                                    span = stmt_node.get("source_span")
                                    bs: Node = _passes_empty_node()
                                    if jv_is_dict(span):
                                        bs = jv_dict(span)
                                    if nd_get_str(left_node, "kind") == NAME and nd_get_str(right_node, "kind") == NAME:
                                        tt: Node = _passes_empty_node()
                                        tt["kind"] = NAME
                                        tt["id"] = tmp
                                        if len(bs) != 0:
                                            tt["source_span"] = bs
                                        a1: Node = _passes_empty_node()
                                        a1["kind"] = ASSIGN
                                        a1["target"] = tt
                                        a1["value"] = te_items[0]
                                        a1["declare"] = True
                                        if len(bs) != 0:
                                            a1["source_span"] = bs
                                        a2: Node = _passes_empty_node()
                                        a2["kind"] = ASSIGN
                                        a2["target"] = te_items[0]
                                        a2["value"] = te_items[1]
                                        if len(bs) != 0:
                                            a2["source_span"] = bs
                                        tr: Node = _passes_empty_node()
                                        tr["kind"] = NAME
                                        tr["id"] = tmp
                                        if len(bs) != 0:
                                            tr["source_span"] = bs
                                        a3: Node = _passes_empty_node()
                                        a3["kind"] = ASSIGN
                                        a3["target"] = te_items[1]
                                        a3["value"] = tr
                                        if len(bs) != 0:
                                            a3["source_span"] = bs
                                        result.append(a1)
                                        result.append(a2)
                                        result.append(a3)
                                        continue
        nested_body = stmt_node.get("body")
        if jv_is_list(nested_body):
            stmt_node["body"] = _swap_in_stmts(jv_list(nested_body), ctx)
        nested_orelse = stmt_node.get("orelse")
        if jv_is_list(nested_orelse):
            stmt_node["orelse"] = _swap_in_stmts(jv_list(nested_orelse), ctx)
        if _is_function_like_kind(kind) or kind == CLASS_DEF:
            body = stmt_node.get("body")
            if jv_is_list(body):
                stmt_node["body"] = _swap_in_stmts(jv_list(body), ctx)
        elif kind == TRY:
            nested_try_body = stmt_node.get("body")
            if jv_is_list(nested_try_body):
                stmt_node["body"] = _swap_in_stmts(jv_list(nested_try_body), ctx)
            nested_try_orelse = stmt_node.get("orelse")
            if jv_is_list(nested_try_orelse):
                stmt_node["orelse"] = _swap_in_stmts(jv_list(nested_try_orelse), ctx)
            nested_try_finalbody = stmt_node.get("finalbody")
            if jv_is_list(nested_try_finalbody):
                stmt_node["finalbody"] = _swap_in_stmts(jv_list(nested_try_finalbody), ctx)
            hs = stmt_node.get("handlers")
            if jv_is_list(hs):
                for h in jv_list(hs):
                    if jv_is_dict(h):
                        handler_node2: Node = jv_dict(h)
                        hb = handler_node2.get("body")
                        if jv_is_list(hb):
                            handler_node2["body"] = _swap_in_stmts(jv_list(hb), ctx)
        result.append(stmt_node)
    return result

def detect_swap_patterns(module: Node, ctx: CompileContext) -> Node:
    body = module.get("body")
    if jv_is_list(body):
        module["body"] = _swap_in_stmts(jv_list(body), ctx)
    return module


# ===========================================================================
# mutates_self detection
# ===========================================================================

def _is_self_attr(node: Node) -> bool:
    if nd_get_str(node, "kind") != ATTRIBUTE:
        return False
    value = node.get("value")
    if not jv_is_dict(value):
        return False
    value_node: Node = jv_dict(value)
    return nd_get_str(value_node, "kind") == NAME and nd_get_str(value_node, "id") == "self"

def _node_mutates(node: JsonVal) -> bool:
    if not jv_is_dict(node):
        return False
    node_obj: Node = jv_dict(node)
    kind = nd_get_str(node_obj, "kind")
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        target = node_obj.get("target")
        if jv_is_dict(target):
            target_node: Node = jv_dict(target)
            if _is_self_attr(target_node):
                return True
            if nd_get_str(target_node, "kind") == SUBSCRIPT:
                val = target_node.get("value")
                if jv_is_dict(val):
                    val_node: Node = jv_dict(val)
                    if _is_self_attr(val_node):
                        return True
    if kind == EXPR:
        value = node_obj.get("value")
        if jv_is_dict(value):
            value_node: Node = jv_dict(value)
            if nd_get_str(value_node, "kind") == CALL:
                func = value_node.get("func")
                if jv_is_dict(func):
                    func_node: Node = jv_dict(func)
                    if nd_get_str(func_node, "kind") == ATTRIBUTE:
                        owner = func_node.get("value")
                        if jv_is_dict(owner):
                            owner_node: Node = jv_dict(owner)
                            if _is_self_attr(owner_node):
                                return True
    nested_body = node_obj.get("body")
    if jv_is_list(nested_body):
        for item in jv_list(nested_body):
            if _node_mutates(item):
                return True
    nested_orelse = node_obj.get("orelse")
    if jv_is_list(nested_orelse):
        for item in jv_list(nested_orelse):
            if _node_mutates(item):
                return True
    nested_finalbody = node_obj.get("finalbody")
    if jv_is_list(nested_finalbody):
        for item in jv_list(nested_finalbody):
            if _node_mutates(item):
                return True
    if kind == TRY:
        hs = node_obj.get("handlers")
        if jv_is_list(hs):
            for h in jv_list(hs):
                if jv_is_dict(h):
                    handler_node: Node = jv_dict(h)
                    hb: JsonVal = handler_node.get("body")
                    if jv_is_list(hb):
                        for item in jv_list(hb):
                            if _node_mutates(item):
                                return True
    return False

def _ms_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _ms_walk(item)
        return
    if not jv_is_dict(node):
        return
    node_obj: Node = jv_dict(node)
    kind = nd_get_str(node_obj, "kind")
    if _is_function_like_kind(kind):
        body_obj: JsonVal = node_obj.get("body")
        node_obj["mutates_self"] = _node_mutates(body_obj)
        if jv_is_list(body_obj):
            for item in jv_list(body_obj):
                _ms_walk(item)
        return
    if kind == CLASS_DEF:
        body_obj2: JsonVal = node_obj.get("body")
        if jv_is_list(body_obj2):
            for item in jv_list(body_obj2):
                _ms_walk(item)
        return
    for value in node_obj.values():
        if jv_is_dict(value) or jv_is_list(value):
            _ms_walk(value)

def detect_mutates_self(module: Node, ctx: CompileContext) -> Node:
    _ms_walk(module)
    return module


# ===========================================================================
# unused variable detection
# ===========================================================================

def _uv_refs(node: JsonVal, out: set[str]) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _uv_refs(item, out)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    kind = nd_get_str(nd, "kind")
    if kind == NAME:
        n = "" + nd_get_str(nd, "id")
        if n != "":
            out.add(n)
        return
    if kind in (ASSIGN, ANN_ASSIGN, AUG_ASSIGN):
        value = nd.get("value")
        if jv_is_dict(value) or jv_is_list(value):
            _uv_refs(value, out)
        if kind == AUG_ASSIGN:
            target = nd.get("target")
            if jv_is_dict(target):
                target_node: Node = jv_dict(target)
                if nd_get_str(target_node, "kind") != NAME:
                    return
                n = "" + nd_get_str(target_node, "id")
                if n != "":
                    out.add(n)
        return
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _uv_refs(v, out)

def _uv_mark_fn(func: Node) -> None:
    body: JsonVal = func.get("body")
    if not jv_is_list(body):
        return
    all_refs: set[str] = set()
    _uv_refs(jv_list(body), all_refs)
    ao = func.get("arg_order")
    if jv_is_list(ao):
        for arg in jv_list(ao):
            arg_name = "" + jv_str(arg)
            if arg_name != "":
                all_refs.add(arg_name)
    _uv_mark_stmts(jv_list(body), all_refs)


def _uv_mark_stmts(stmts: list[JsonVal], all_refs: set[str]) -> None:
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        kind = nd_get_str(stmt_node, "kind")
        if kind == VAR_DECL:
            n = "" + nd_get_str(stmt_node, "name")
            if n != "" and n not in all_refs:
                stmt_node["unused"] = True
        elif kind in (ASSIGN, ANN_ASSIGN):
            target = stmt_node.get("target")
            if jv_is_dict(target) and nd_get_str(jv_dict(target), "kind") == NAME:
                target_node: Node = jv_dict(target)
                n = "" + nd_get_str(target_node, "id")
                if n != "" and n not in all_refs:
                    stmt_node["unused"] = True
            elif jv_is_dict(target) and nd_get_str(jv_dict(target), "kind") == TUPLE:
                target_node: Node = jv_dict(target)
                elements = target_node.get("elements")
                if jv_is_list(elements):
                    for elem in jv_list(elements):
                        if jv_is_dict(elem) and nd_get_str(jv_dict(elem), "kind") == NAME:
                            elem_node: Node = jv_dict(elem)
                            en = "" + nd_get_str(elem_node, "id")
                            if en != "" and en not in all_refs:
                                elem_node["unused"] = True
        nested_body = stmt_node.get("body")
        if jv_is_list(nested_body):
            _uv_mark_stmts(jv_list(nested_body), all_refs)
        nested_orelse = stmt_node.get("orelse")
        if jv_is_list(nested_orelse):
            _uv_mark_stmts(jv_list(nested_orelse), all_refs)
        nested_finalbody = stmt_node.get("finalbody")
        if jv_is_list(nested_finalbody):
            _uv_mark_stmts(jv_list(nested_finalbody), all_refs)
        if kind == TRY:
            hs = stmt_node.get("handlers")
            if jv_is_list(hs):
                for h in jv_list(hs):
                    if jv_is_dict(h):
                        h_node: Node = jv_dict(h)
                        hb = h_node.get("body")
                        if jv_is_list(hb):
                            _uv_mark_stmts(jv_list(hb), all_refs)

def _uv_walk(node: JsonVal) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _uv_walk(item)
        return
    if not jv_is_dict(node):
        return
    nd: Node = jv_dict(node)
    if _is_function_like(nd):
        _uv_mark_fn(nd)
    for v in nd.values():
        if jv_is_dict(v) or jv_is_list(v):
            _uv_walk(v)


def detect_unused_variables(module: Node, ctx: CompileContext) -> Node:
    _uv_walk(module)
    return module


# ===========================================================================
# main guard discard
# ===========================================================================

def _mgd_stmts(stmts: list[JsonVal]) -> None:
    for stmt in stmts:
        if not jv_is_dict(stmt):
            continue
        stmt_node: Node = jv_dict(stmt)
        if nd_get_str(stmt_node, "kind") == EXPR:
            value = stmt_node.get("value")
            if jv_is_dict(value) and nd_get_str(jv_dict(value), "kind") == CALL:
                stmt_node["discard_result"] = True


def mark_main_guard_discard(module: Node, ctx: CompileContext) -> Node:
    mg: JsonVal = module.get("main_guard_body")
    if jv_is_list(mg):
        _mgd_stmts(jv_list(mg))
    body: JsonVal = module.get("body")
    if jv_is_list(body):
        for stmt in jv_list(body):
            if jv_is_dict(stmt):
                stmt_node: Node = jv_dict(stmt)
                if _is_function_like(stmt_node):
                    name = "" + nd_get_str(stmt_node, "name")
                    if name == "__pytra_main":
                        fb: JsonVal = stmt_node.get("body")
                        if jv_is_list(fb):
                            _mgd_stmts(jv_list(fb))
    return module

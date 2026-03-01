"""Attach safe `reserve` hints for provably-fixed append loops."""

from __future__ import annotations

import copy

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_CONTROL_FLOW_KINDS = {"If", "While", "For", "ForCore", "Try", "With"}


def _const_int_value(expr: Any) -> int | None:
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value_obj = expr.get("value")
    if isinstance(value_obj, int):
        return int(value_obj)
    return None


def _collect_target_names(target_node: Any, out: set[str]) -> None:
    if not isinstance(target_node, dict):
        return
    kind = target_node.get("kind")
    if kind == "Name":
        ident = target_node.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
        return
    if kind == "Tuple":
        elements_obj = target_node.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        for elem in elements:
            _collect_target_names(elem, out)


def _collect_target_plan_names(target_plan: Any, out: set[str]) -> None:
    if not isinstance(target_plan, dict):
        return
    kind = target_plan.get("kind")
    if kind == "NameTarget":
        ident = target_plan.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
        return
    if kind == "TupleTarget":
        elements_obj = target_plan.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        for elem in elements:
            _collect_target_plan_names(elem, out)


def _collect_assigned_names(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_assigned_names(item, out)
        return
    if not isinstance(node, dict):
        return

    kind = node.get("kind")
    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        _collect_target_names(node.get("target"), out)
    elif kind in {"For", "ForRange"}:
        _collect_target_names(node.get("target"), out)
    elif kind == "ForCore":
        _collect_target_plan_names(node.get("target_plan"), out)

    for value in node.values():
        _collect_assigned_names(value, out)


def _collect_name_refs(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_name_refs(item, out)
        return
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Name":
        ident = node.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
    for value in node.values():
        _collect_name_refs(value, out)


def _const_int_expr(value: int) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": int(value),
    }


def _binop_expr(op: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "BinOp",
        "op": op,
        "left": left,
        "right": right,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
    }


def _compare_expr(op: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "Compare",
        "left": left,
        "ops": [op],
        "comparators": [right],
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }


def _ifexp_expr(test: dict[str, Any], body: dict[str, Any], orelse: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "IfExp",
        "test": test,
        "body": body,
        "orelse": orelse,
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
    }


def _is_const_int_expr(expr: Any, expected: int) -> bool:
    return _const_int_value(expr) == expected


def _clone_expr(node: Any) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    cloned = copy.deepcopy(node)
    return cloned if isinstance(cloned, dict) else None


def _build_static_range_trip_count_expr(
    *,
    start_expr: Any,
    stop_expr: Any,
    step_value: int,
    range_mode: str,
) -> dict[str, Any] | None:
    if step_value == 0:
        return None
    start = _clone_expr(start_expr)
    stop = _clone_expr(stop_expr)
    if not isinstance(start, dict) or not isinstance(stop, dict):
        return None

    step_abs = abs(int(step_value))
    zero_expr = _const_int_expr(0)
    if range_mode == "ascending":
        test = _compare_expr("LtE", _clone_expr(stop) or stop, _clone_expr(start) or start)
        if step_abs == 1:
            if _is_const_int_expr(start, 0):
                positive = _clone_expr(stop)
            else:
                positive = _binop_expr("Sub", _clone_expr(stop) or stop, _clone_expr(start) or start)
        else:
            diff = _binop_expr("Sub", _clone_expr(stop) or stop, _clone_expr(start) or start)
            numer = _binop_expr("Add", diff, _const_int_expr(step_abs - 1))
            positive = _binop_expr("Div", numer, _const_int_expr(step_abs))
        if not isinstance(positive, dict):
            return None
        return _ifexp_expr(test, zero_expr, positive)

    if range_mode == "descending":
        test = _compare_expr("GtE", _clone_expr(stop) or stop, _clone_expr(start) or start)
        if step_abs == 1:
            if _is_const_int_expr(stop, 0):
                positive = _clone_expr(start)
            else:
                positive = _binop_expr("Sub", _clone_expr(start) or start, _clone_expr(stop) or stop)
        else:
            diff = _binop_expr("Sub", _clone_expr(start) or start, _clone_expr(stop) or stop)
            numer = _binop_expr("Add", diff, _const_int_expr(step_abs - 1))
            positive = _binop_expr("Div", numer, _const_int_expr(step_abs))
        if not isinstance(positive, dict):
            return None
        return _ifexp_expr(test, zero_expr, positive)
    return None


def _is_simple_invariant_expr(expr: Any, mutated_names: set[str]) -> bool:
    if not isinstance(expr, dict):
        return False
    kind = expr.get("kind")
    if kind == "Constant":
        return _const_int_value(expr) is not None
    if kind == "Name":
        ident = expr.get("id")
        if not isinstance(ident, str) or ident == "":
            return False
        return ident not in mutated_names
    return False


def _top_level_unconditional_append_owner(body: list[Any]) -> str:
    append_count = 0
    append_owner = ""
    for stmt_obj in body:
        stmt = stmt_obj if isinstance(stmt_obj, dict) else None
        if stmt is None:
            return ""
        stmt_kind = stmt.get("kind")
        if isinstance(stmt_kind, str) and stmt_kind in _CONTROL_FLOW_KINDS:
            return ""
        if stmt_kind != "Expr":
            continue
        call_obj = stmt.get("value")
        call = call_obj if isinstance(call_obj, dict) else None
        if call is None or call.get("kind") != "Call":
            continue
        func_obj = call.get("func")
        func = func_obj if isinstance(func_obj, dict) else None
        if func is None or func.get("kind") != "Attribute":
            continue
        if func.get("attr") != "append":
            continue
        owner_obj = func.get("value")
        owner = owner_obj if isinstance(owner_obj, dict) else None
        if owner is None or owner.get("kind") != "Name":
            return ""
        owner_id = owner.get("id")
        if not isinstance(owner_id, str) or owner_id == "":
            return ""
        append_count += 1
        if append_owner == "":
            append_owner = owner_id
        elif append_owner != owner_id:
            return ""
    if append_count != 1:
        return ""
    return append_owner


class SafeReserveHintPass(East3OptimizerPass):
    """Mark static loops eligible for conservative pre-`reserve`."""

    name = "SafeReserveHintPass"
    min_opt_level = 1

    def _set_hints(self, stmt: dict[str, Any], hints: list[dict[str, Any]]) -> int:
        current_obj = stmt.get("reserve_hints")
        current = current_obj if isinstance(current_obj, list) else []
        if len(hints) == 0:
            if "reserve_hints" in stmt:
                stmt.pop("reserve_hints", None)
                return 1
            return 0
        if current == hints:
            return 0
        stmt["reserve_hints"] = hints
        return 1

    def _try_tag_forcore(self, stmt: dict[str, Any]) -> int:
        if stmt.get("kind") != "ForCore":
            return 0
        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "StaticRangeForPlan":
            return self._set_hints(stmt, [])

        body_obj = stmt.get("body")
        body = body_obj if isinstance(body_obj, list) else []
        if len(body) == 0:
            return self._set_hints(stmt, [])

        step_obj = iter_plan.get("step")
        step_val = _const_int_value(step_obj)
        if step_val is None or step_val == 0:
            return self._set_hints(stmt, [])
        range_mode_obj = iter_plan.get("range_mode")
        range_mode = str(range_mode_obj).strip() if isinstance(range_mode_obj, str) else ""
        if range_mode == "":
            range_mode = "ascending" if step_val > 0 else "descending"
        if range_mode not in {"ascending", "descending"}:
            return self._set_hints(stmt, [])
        if range_mode == "ascending" and step_val < 0:
            return self._set_hints(stmt, [])
        if range_mode == "descending" and step_val > 0:
            return self._set_hints(stmt, [])

        mutated_names: set[str] = set()
        _collect_assigned_names(body, mutated_names)
        start_expr = iter_plan.get("start")
        stop_expr = iter_plan.get("stop")
        if not _is_simple_invariant_expr(start_expr, mutated_names):
            return self._set_hints(stmt, [])
        if not _is_simple_invariant_expr(stop_expr, mutated_names):
            return self._set_hints(stmt, [])

        stop_refs: set[str] = set()
        _collect_name_refs(stop_expr, stop_refs)
        if len(stop_refs & mutated_names) > 0:
            return self._set_hints(stmt, [])

        owner = _top_level_unconditional_append_owner(body)
        if owner == "":
            return self._set_hints(stmt, [])
        count_expr = _build_static_range_trip_count_expr(
            start_expr=start_expr,
            stop_expr=stop_expr,
            step_value=int(step_val),
            range_mode=range_mode,
        )
        if not isinstance(count_expr, dict):
            return self._set_hints(stmt, [])

        hints = [
            {
                "kind": "StaticRangeReserveHint",
                "owner": owner,
                "count_kind": "static_range_trip_count",
                "count_expr_version": "east3_expr_v1",
                "count_expr": count_expr,
                "safe": True,
                "safety": "proven_unconditional_append",
            }
        ]
        return self._set_hints(stmt, hints)

    def _visit(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0

        changed = self._try_tag_forcore(node)
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

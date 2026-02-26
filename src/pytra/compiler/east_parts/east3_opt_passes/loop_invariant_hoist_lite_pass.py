"""Conservative loop-invariant hoisting for `ForCore` static-range loops."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_DYNAMIC_NAME_CALLS = {"locals", "globals", "vars", "eval", "exec"}


def _contains_dynamic_name_access(node: Any) -> bool:
    if isinstance(node, list):
        for item in node:
            if _contains_dynamic_name_access(item):
                return True
        return False
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Call":
        func_obj = node.get("func")
        if isinstance(func_obj, dict) and func_obj.get("kind") == "Name":
            fn_name = func_obj.get("id")
            if isinstance(fn_name, str) and fn_name in _DYNAMIC_NAME_CALLS:
                return True
    for value in node.values():
        if _contains_dynamic_name_access(value):
            return True
    return False


def _const_int_value(expr: Any) -> int | None:
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value_obj = expr.get("value")
    if isinstance(value_obj, int):
        return int(value_obj)
    return None


def _loop_is_statically_non_empty(iter_plan: dict[str, Any]) -> bool:
    if iter_plan.get("kind") != "StaticRangeForPlan":
        return False
    start_val = _const_int_value(iter_plan.get("start"))
    stop_val = _const_int_value(iter_plan.get("stop"))
    step_val = _const_int_value(iter_plan.get("step"))
    if start_val is None or stop_val is None or step_val is None:
        return False
    if step_val == 0:
        return False
    if step_val > 0:
        return start_val < stop_val
    return start_val > stop_val


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


def _extract_assign_target_name(stmt: dict[str, Any]) -> str:
    kind = stmt.get("kind")
    if kind != "Assign" and kind != "AnnAssign":
        return ""
    target = stmt.get("target")
    if not isinstance(target, dict):
        return ""
    if target.get("kind") != "Name":
        return ""
    ident = target.get("id")
    if isinstance(ident, str):
        return ident
    return ""


def _is_invariant_expr(expr: Any, *, loop_var: str, mutated_names: set[str]) -> bool:
    if not isinstance(expr, dict):
        return False
    kind = expr.get("kind")
    if kind == "Constant":
        value_obj = expr.get("value")
        return isinstance(value_obj, bool) or isinstance(value_obj, int) or isinstance(value_obj, float)
    if kind == "Name":
        ident = expr.get("id")
        if not isinstance(ident, str) or ident == "":
            return False
        if ident == loop_var:
            return False
        return ident not in mutated_names
    if kind == "UnaryOp":
        op = expr.get("op")
        if op not in {"UAdd", "USub"}:
            return False
        return _is_invariant_expr(expr.get("operand"), loop_var=loop_var, mutated_names=mutated_names)
    if kind == "BinOp":
        op = expr.get("op")
        if op not in {"Add", "Sub", "Mult", "Div"}:
            return False
        left = expr.get("left")
        right = expr.get("right")
        return _is_invariant_expr(left, loop_var=loop_var, mutated_names=mutated_names) and _is_invariant_expr(
            right,
            loop_var=loop_var,
            mutated_names=mutated_names,
        )
    return False


class LoopInvariantHoistLitePass(East3OptimizerPass):
    """Hoist one safe invariant assignment from static-range loop preheaders."""

    name = "LoopInvariantHoistLitePass"
    min_opt_level = 2

    def _try_hoist_forcore(self, stmt_list: list[Any], index: int) -> bool:
        stmt_obj = stmt_list[index]
        stmt = stmt_obj if isinstance(stmt_obj, dict) else None
        if stmt is None or stmt.get("kind") != "ForCore":
            return False

        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or not _loop_is_statically_non_empty(iter_plan):
            return False

        target_plan_obj = stmt.get("target_plan")
        target_plan = target_plan_obj if isinstance(target_plan_obj, dict) else None
        if target_plan is None or target_plan.get("kind") != "NameTarget":
            return False
        loop_var_obj = target_plan.get("id")
        loop_var = loop_var_obj if isinstance(loop_var_obj, str) else ""
        if loop_var == "":
            return False

        body_obj = stmt.get("body")
        body = body_obj if isinstance(body_obj, list) else None
        if body is None or len(body) == 0:
            return False
        if _contains_dynamic_name_access(body):
            return False

        first_stmt_obj = body[0]
        first_stmt = first_stmt_obj if isinstance(first_stmt_obj, dict) else None
        if first_stmt is None:
            return False
        target_name = _extract_assign_target_name(first_stmt)
        if target_name == "":
            return False

        mutated_names: set[str] = set()
        _collect_assigned_names(body[1:], mutated_names)
        if target_name in mutated_names:
            return False

        value_expr = first_stmt.get("value")
        if not _is_invariant_expr(value_expr, loop_var=loop_var, mutated_names=mutated_names):
            return False

        hoisted_stmt = body.pop(0)
        stmt_list.insert(index, hoisted_stmt)
        return True

    def _visit(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit(item)
            i = 0
            while i < len(node):
                item = node[i]
                if isinstance(item, dict) and self._try_hoist_forcore(node, i):
                    changed += 1
                    i += 2
                    continue
                i += 1
            return changed

        if not isinstance(node, dict):
            return 0

        changed = 0
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)


"""Canonicalize `for ... in range(...)` runtime plans into static range plans."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


def _const_int_node(value: int) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(value),
        "value": value,
    }


def _is_range_runtime_call(expr: dict[str, Any]) -> bool:
    if expr.get("kind") != "Call":
        return False
    runtime_call = expr.get("runtime_call")
    if runtime_call == "py_range":
        return True
    if expr.get("lowered_kind") != "BuiltinCall":
        return False
    return expr.get("builtin_name") == "range"


def _is_constant_int_expr(expr: Any) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") != "Constant":
        return False
    return isinstance(expr.get("value"), int)


class RangeForCanonicalizationPass(East3OptimizerPass):
    """Convert conservative runtime `range` loops into `StaticRangeForPlan`."""

    name = "RangeForCanonicalizationPass"
    min_opt_level = 1

    def _try_rewrite_forcore(self, stmt: dict[str, Any]) -> bool:
        if stmt.get("kind") != "ForCore":
            return False

        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "RuntimeIterForPlan":
            return False

        target_plan_obj = stmt.get("target_plan")
        target_plan = target_plan_obj if isinstance(target_plan_obj, dict) else None
        if target_plan is None or target_plan.get("kind") != "NameTarget":
            return False
        target_id = target_plan.get("id")
        if not isinstance(target_id, str) or target_id == "":
            return False

        iter_expr_obj = iter_plan.get("iter_expr")
        iter_expr = iter_expr_obj if isinstance(iter_expr_obj, dict) else None
        if iter_expr is None or not _is_range_runtime_call(iter_expr):
            return False

        args_obj = iter_expr.get("args")
        args = args_obj if isinstance(args_obj, list) else []
        if len(args) < 1 or len(args) > 3:
            return False

        for arg in args:
            if not _is_constant_int_expr(arg):
                return False

        start_expr: dict[str, Any]
        stop_expr: dict[str, Any]
        step_expr: dict[str, Any]
        if len(args) == 1:
            start_expr = _const_int_node(0)
            stop_expr = args[0]
            step_expr = _const_int_node(1)
        elif len(args) == 2:
            start_expr = args[0]
            stop_expr = args[1]
            step_expr = _const_int_node(1)
        else:
            start_expr = args[0]
            stop_expr = args[1]
            step_expr = args[2]

        step_val_obj = step_expr.get("value")
        if not isinstance(step_val_obj, int):
            return False
        step_val = int(step_val_obj)
        if step_val == 0:
            return False

        range_mode = "dynamic"
        if step_val > 0:
            range_mode = "ascending"
        elif step_val < 0:
            range_mode = "descending"

        stmt["iter_mode"] = "static_fastpath"
        stmt["iter_plan"] = {
            "kind": "StaticRangeForPlan",
            "start": start_expr,
            "stop": stop_expr,
            "step": step_expr,
            "range_mode": range_mode,
        }
        return True

    def _visit(self, node: Any) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item)
            return changed

        if not isinstance(node, dict):
            return 0

        if self._try_rewrite_forcore(node):
            changed += 1

        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)


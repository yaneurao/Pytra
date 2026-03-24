"""Canonicalize for...in range(...) runtime plans into static range plans."""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.optimize.optimizer import East3OptimizerPass, PassContext, PassResult, make_pass_result
from toolchain2.optimize.utils import const_int_node


def _is_range_runtime_call(expr: dict[str, JsonVal]) -> bool:
    if expr.get("kind") != "Call":
        return False
    runtime_call = expr.get("runtime_call")
    if runtime_call == "py_range":
        return True
    if expr.get("lowered_kind") != "BuiltinCall":
        return False
    return expr.get("builtin_name") == "range"


def _is_constant_int_expr(expr: JsonVal) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") != "Constant":
        return False
    v = expr.get("value")
    return isinstance(v, int) and not isinstance(v, bool)


def _is_int_like_expr(expr: JsonVal) -> bool:
    if _is_constant_int_expr(expr):
        return True
    if not isinstance(expr, dict):
        return False
    resolved_type_obj = expr.get("resolved_type")
    resolved_type = str(resolved_type_obj).strip() if resolved_type_obj is not None else ""
    if resolved_type == "":
        return False
    return resolved_type == "int" or resolved_type == "int64"


class RangeForCanonicalizationPass(East3OptimizerPass):
    """Convert conservative runtime range loops into StaticRangeForPlan."""

    name: str = "RangeForCanonicalizationPass"
    min_opt_level: int = 1

    def _try_rewrite_forcore(self, stmt: dict[str, JsonVal]) -> bool:
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
            if not _is_int_like_expr(arg):
                return False

        start_expr: dict[str, JsonVal]
        stop_expr: dict[str, JsonVal]
        step_expr: dict[str, JsonVal]
        if len(args) == 1:
            a0 = args[0]
            if not isinstance(a0, dict):
                return False
            start_expr = const_int_node(0)
            stop_expr = a0
            step_expr = const_int_node(1)
        elif len(args) == 2:
            a0 = args[0]
            a1 = args[1]
            if not isinstance(a0, dict) or not isinstance(a1, dict):
                return False
            start_expr = a0
            stop_expr = a1
            step_expr = const_int_node(1)
        else:
            a0 = args[0]
            a1 = args[1]
            a2 = args[2]
            if not isinstance(a0, dict) or not isinstance(a1, dict) or not isinstance(a2, dict):
                return False
            start_expr = a0
            stop_expr = a1
            step_expr = a2

        step_val_obj = step_expr.get("value")
        if not isinstance(step_val_obj, int) or isinstance(step_val_obj, bool):
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

    def _visit(self, node: JsonVal) -> int:
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

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return make_pass_result(changed=change_count > 0, change_count=change_count)

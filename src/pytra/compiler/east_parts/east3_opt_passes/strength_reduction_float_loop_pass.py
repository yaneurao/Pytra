"""Conservative float-loop strength reduction (`Div` by power-of-two -> `Mult`)."""

from __future__ import annotations

import math

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"


def _as_finite_non_zero_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) or isinstance(value, float):
        as_float = float(value)
        if not math.isfinite(as_float):
            return None
        if as_float == 0.0:
            return None
        return as_float
    return None


def _is_power_of_two_abs(value: float) -> bool:
    abs_value = value if value >= 0.0 else -value
    if abs_value <= 0.0:
        return False
    mantissa, _ = math.frexp(abs_value)
    return mantissa == 0.5


def _build_float_constant(value: float) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "float64",
        "borrow_kind": "value",
        "casts": [],
        "repr": repr(value),
        "value": value,
    }


class StrengthReductionFloatLoopPass(East3OptimizerPass):
    """Rewrite safe float loop divisions into multiplications by reciprocal."""

    name = "StrengthReductionFloatLoopPass"
    min_opt_level = 2

    def _rewrite_binop(self, expr: dict[str, Any]) -> bool:
        if expr.get("kind") != "BinOp":
            return False
        if expr.get("op") != "Div":
            return False
        expr_t = _normalize_type_name(expr.get("resolved_type"))
        if expr_t != "float64" and expr_t != "float32":
            return False

        right_obj = expr.get("right")
        right = right_obj if isinstance(right_obj, dict) else None
        if right is None or right.get("kind") != "Constant":
            return False
        divisor = _as_finite_non_zero_number(right.get("value"))
        if divisor is None:
            return False
        if not _is_power_of_two_abs(divisor):
            return False

        reciprocal = 1.0 / divisor
        expr["op"] = "Mult"
        expr["right"] = _build_float_constant(reciprocal)
        return True

    def _visit_expr(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit_expr(item)
            return changed
        if not isinstance(node, dict):
            return 0
        changed = 0
        for value in node.values():
            changed += self._visit_expr(value)
        if self._rewrite_binop(node):
            changed += 1
        return changed

    def _visit(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit(item)
            return changed

        if not isinstance(node, dict):
            return 0

        changed = 0
        kind = node.get("kind")
        if kind == "ForCore":
            iter_plan_obj = node.get("iter_plan")
            iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
            if iter_plan is not None and iter_plan.get("kind") == "StaticRangeForPlan":
                changed += self._visit_expr(node.get("body"))
                changed += self._visit(node.get("orelse"))
                changed += self._visit(iter_plan)
                changed += self._visit(node.get("target_plan"))
                return changed
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

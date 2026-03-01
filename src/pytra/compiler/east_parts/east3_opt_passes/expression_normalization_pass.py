"""Attach backend-shared normalized expression metadata (`east3_expr_v1`)."""

from __future__ import annotations

import copy

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_EXPR_V1 = "east3_expr_v1"
_NORM_META_KEYS = {"normalized_expr", "normalized_exprs", "normalized_expr_version"}


def _const_int_expr(value: int) -> dict[str, Any]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(int(value)),
        "value": int(value),
    }


def _const_int_value(expr: Any) -> int | None:
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value_any = expr.get("value")
    if isinstance(value_any, int):
        return int(value_any)
    return None


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
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }


def _strip_norm_meta(node: Any) -> None:
    if isinstance(node, list):
        for item in node:
            _strip_norm_meta(item)
        return
    if not isinstance(node, dict):
        return
    for key in list(node.keys()):
        if key in _NORM_META_KEYS:
            node.pop(key, None)
    for value in list(node.values()):
        _strip_norm_meta(value)


def _clone_expr_without_norm_meta(expr: Any) -> dict[str, Any] | None:
    if not isinstance(expr, dict):
        return None
    cloned_any = copy.deepcopy(expr)
    if not isinstance(cloned_any, dict):
        return None
    _strip_norm_meta(cloned_any)
    return cloned_any


def _resolve_forcore_range_mode(iter_plan: dict[str, Any]) -> str:
    mode_any = iter_plan.get("range_mode")
    if isinstance(mode_any, str) and mode_any in {"ascending", "descending", "dynamic"}:
        return mode_any
    step_any = iter_plan.get("step")
    step_value = _const_int_value(step_any)
    if step_value is None:
        return "dynamic"
    if step_value > 0:
        return "ascending"
    if step_value < 0:
        return "descending"
    return "dynamic"


class ExpressionNormalizationPass(East3OptimizerPass):
    """Attach normalized-expression metadata for backend consumption."""

    name = "ExpressionNormalizationPass"
    min_opt_level = 1

    def _tag_expr_node(self, node: dict[str, Any]) -> int:
        kind_any = node.get("kind")
        kind = kind_any if isinstance(kind_any, str) else ""
        if kind not in {"BinOp", "Compare"}:
            return 0
        normalized = _clone_expr_without_norm_meta(node)
        if not isinstance(normalized, dict):
            return 0
        changed = 0
        if node.get("normalized_expr_version") != _EXPR_V1:
            node["normalized_expr_version"] = _EXPR_V1
            changed += 1
        if node.get("normalized_expr") != normalized:
            node["normalized_expr"] = normalized
            changed += 1
        return changed

    def _build_forcore_cond_expr(self, stmt: dict[str, Any]) -> dict[str, Any] | None:
        if stmt.get("kind") != "ForCore":
            return None
        iter_plan_any = stmt.get("iter_plan")
        iter_plan = iter_plan_any if isinstance(iter_plan_any, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "StaticRangeForPlan":
            return None
        target_plan_any = stmt.get("target_plan")
        target_plan = target_plan_any if isinstance(target_plan_any, dict) else None
        if target_plan is None or target_plan.get("kind") != "NameTarget":
            return None
        target_id_any = target_plan.get("id")
        target_id = target_id_any if isinstance(target_id_any, str) else ""
        if target_id == "":
            return None
        target_type_any = target_plan.get("target_type")
        target_type = target_type_any if isinstance(target_type_any, str) and target_type_any != "" else "int64"
        stop_expr = _clone_expr_without_norm_meta(iter_plan.get("stop"))
        if not isinstance(stop_expr, dict):
            return None
        step_expr = _clone_expr_without_norm_meta(iter_plan.get("step"))
        if not isinstance(step_expr, dict):
            step_expr = _const_int_expr(1)
        target_expr: dict[str, Any] = {
            "kind": "Name",
            "id": target_id,
            "resolved_type": target_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": target_id,
        }
        mode = _resolve_forcore_range_mode(iter_plan)
        if mode == "ascending":
            return _compare_expr("Lt", target_expr, stop_expr)
        if mode == "descending":
            return _compare_expr("Gt", target_expr, stop_expr)
        test = _compare_expr("Gt", step_expr, _const_int_expr(0))
        body = _compare_expr("Lt", _clone_expr_without_norm_meta(target_expr) or target_expr, _clone_expr_without_norm_meta(stop_expr) or stop_expr)
        orelse = _compare_expr("Gt", _clone_expr_without_norm_meta(target_expr) or target_expr, _clone_expr_without_norm_meta(stop_expr) or stop_expr)
        return _ifexp_expr(test, body, orelse)

    def _tag_forcore_cond(self, node: dict[str, Any]) -> int:
        cond_expr = self._build_forcore_cond_expr(node)
        if not isinstance(cond_expr, dict):
            return 0
        changed = 0
        if node.get("normalized_expr_version") != _EXPR_V1:
            node["normalized_expr_version"] = _EXPR_V1
            changed += 1
        exprs_any = node.get("normalized_exprs")
        exprs = exprs_any if isinstance(exprs_any, dict) else {}
        if exprs.get("for_cond_expr") != cond_expr:
            exprs["for_cond_expr"] = cond_expr
            node["normalized_exprs"] = exprs
            changed += 1
        return changed

    def _visit(self, node: Any) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return changed
        changed += self._tag_expr_node(node)
        changed += self._tag_forcore_cond(node)
        for key, value in list(node.items()):
            if key in _NORM_META_KEYS:
                continue
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)


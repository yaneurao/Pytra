"""Attach backend-shared normalized expression metadata (east3_expr_v1)."""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.optimize.optimizer import East3OptimizerPass, PassContext, PassResult, make_pass_result
from toolchain2.common.jv import deep_copy_json
from toolchain2.common.nodes import const_int_node, const_int_value


_EXPR_V1 = "east3_expr_v1"
_NORM_META_KEYS: set[str] = {"normalized_expr", "normalized_exprs", "normalized_expr_version"}


def _compare_expr_bool(op: str, left: dict[str, JsonVal], right: dict[str, JsonVal]) -> dict[str, JsonVal]:
    return {
        "kind": "Compare",
        "left": left,
        "ops": [op],
        "comparators": [right],
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }


def _ifexp_expr_bool(test: dict[str, JsonVal], body: dict[str, JsonVal], orelse: dict[str, JsonVal]) -> dict[str, JsonVal]:
    return {
        "kind": "IfExp",
        "test": test,
        "body": body,
        "orelse": orelse,
        "resolved_type": "bool",
        "borrow_kind": "value",
        "casts": [],
    }


def _strip_norm_meta(node: JsonVal) -> None:
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


def _clone_expr_without_norm_meta(expr: JsonVal) -> dict[str, JsonVal] | None:
    if not isinstance(expr, dict):
        return None
    cloned = deep_copy_json(expr)
    if not isinstance(cloned, dict):
        return None
    _strip_norm_meta(cloned)
    return cloned


def _resolve_forcore_range_mode(iter_plan: dict[str, JsonVal]) -> str:
    mode_val = iter_plan.get("range_mode")
    if isinstance(mode_val, str) and (mode_val == "ascending" or mode_val == "descending" or mode_val == "dynamic"):
        return mode_val
    step_val = const_int_value(iter_plan.get("step"))
    if step_val is None:
        return "dynamic"
    if step_val > 0:
        return "ascending"
    if step_val < 0:
        return "descending"
    return "dynamic"


class ExpressionNormalizationPass(East3OptimizerPass):
    """Attach normalized-expression metadata for backend consumption."""

    name: str = "ExpressionNormalizationPass"
    min_opt_level: int = 1

    def _tag_expr_node(self, node: dict[str, JsonVal]) -> int:
        kind_val = node.get("kind")
        kind = kind_val if isinstance(kind_val, str) else ""
        if kind != "BinOp" and kind != "Compare":
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

    def _build_forcore_cond_expr(self, stmt: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
        if stmt.get("kind") != "ForCore":
            return None
        iter_plan_val = stmt.get("iter_plan")
        iter_plan = iter_plan_val if isinstance(iter_plan_val, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "StaticRangeForPlan":
            return None
        target_plan_val = stmt.get("target_plan")
        target_plan = target_plan_val if isinstance(target_plan_val, dict) else None
        if target_plan is None or target_plan.get("kind") != "NameTarget":
            return None
        target_id_val = target_plan.get("id")
        target_id = target_id_val if isinstance(target_id_val, str) else ""
        if target_id == "":
            return None
        target_type_val = target_plan.get("target_type")
        target_type = target_type_val if isinstance(target_type_val, str) and target_type_val != "" else "int64"
        stop_expr = _clone_expr_without_norm_meta(iter_plan.get("stop"))
        if not isinstance(stop_expr, dict):
            return None
        step_expr = _clone_expr_without_norm_meta(iter_plan.get("step"))
        if not isinstance(step_expr, dict):
            step_expr = const_int_node(1)
        target_expr: dict[str, JsonVal] = {
            "kind": "Name",
            "id": target_id,
            "resolved_type": target_type,
            "borrow_kind": "value",
            "casts": [],
            "repr": target_id,
        }
        mode = _resolve_forcore_range_mode(iter_plan)
        if mode == "ascending":
            return _compare_expr_bool("Lt", target_expr, stop_expr)
        if mode == "descending":
            return _compare_expr_bool("Gt", target_expr, stop_expr)
        test = _compare_expr_bool("Gt", step_expr, const_int_node(0))
        body = _compare_expr_bool("Lt", _clone_expr_without_norm_meta(target_expr) or target_expr, _clone_expr_without_norm_meta(stop_expr) or stop_expr)
        orelse = _compare_expr_bool("Gt", _clone_expr_without_norm_meta(target_expr) or target_expr, _clone_expr_without_norm_meta(stop_expr) or stop_expr)
        return _ifexp_expr_bool(test, body, orelse)

    def _tag_forcore_cond(self, node: dict[str, JsonVal]) -> int:
        cond_expr = self._build_forcore_cond_expr(node)
        if not isinstance(cond_expr, dict):
            return 0
        changed = 0
        if node.get("normalized_expr_version") != _EXPR_V1:
            node["normalized_expr_version"] = _EXPR_V1
            changed += 1
        exprs_val = node.get("normalized_exprs")
        exprs = exprs_val if isinstance(exprs_val, dict) else {}
        if exprs.get("for_cond_expr") != cond_expr:
            exprs["for_cond_expr"] = cond_expr
            node["normalized_exprs"] = exprs
            changed += 1
        return changed

    def _visit(self, node: JsonVal) -> int:
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

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return make_pass_result(changed=change_count > 0, change_count=change_count)

"""Elide unused static-range loop variable bindings conservatively."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_DYNAMIC_NAME_CALLS = {"locals", "globals", "vars", "eval", "exec"}


def _has_dynamic_name_access(node: Any) -> bool:
    if isinstance(node, list):
        for item in node:
            if _has_dynamic_name_access(item):
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
        if _has_dynamic_name_access(value):
            return True
    return False


def _contains_name(node: Any, ident: str) -> bool:
    if isinstance(node, list):
        for item in node:
            if _contains_name(item, ident):
                return True
        return False
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Name" and node.get("id") == ident:
        return True
    for value in node.values():
        if _contains_name(value, ident):
            return True
    return False


class UnusedLoopVarElisionPass(East3OptimizerPass):
    """Rename provably-unused static-range loop vars to `_`."""

    name = "UnusedLoopVarElisionPass"
    min_opt_level = 1

    def _try_elide_forcore(self, stmt: dict[str, Any], later_stmts: list[Any]) -> bool:
        if stmt.get("kind") != "ForCore":
            return False

        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "StaticRangeForPlan":
            return False

        target_plan_obj = stmt.get("target_plan")
        target_plan = target_plan_obj if isinstance(target_plan_obj, dict) else None
        if target_plan is None or target_plan.get("kind") != "NameTarget":
            return False
        target_id = target_plan.get("id")
        if not isinstance(target_id, str) or target_id == "" or target_id == "_":
            return False

        body = stmt.get("body")
        orelse = stmt.get("orelse")
        if _has_dynamic_name_access(body) or _has_dynamic_name_access(orelse):
            return False
        if _has_dynamic_name_access(later_stmts):
            return False

        if _contains_name(body, target_id) or _contains_name(orelse, target_id):
            return False
        if _contains_name(later_stmts, target_id):
            return False

        target_plan["id"] = "_"
        return True

    def _visit(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            for i, item in enumerate(node):
                if isinstance(item, dict):
                    tail = node[i + 1 :]
                    if self._try_elide_forcore(item, tail):
                        changed += 1
                changed += self._visit(item)
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


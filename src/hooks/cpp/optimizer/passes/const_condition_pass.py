"""Simplify constant-condition branches in C++ backend IR."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult


def _const_truth_value(expr: Any) -> bool | None:
    if not isinstance(expr, dict):
        return None
    if expr.get("kind") != "Constant":
        return None
    value = expr.get("value")
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return False
    return None


class CppConstConditionPass(CppOptimizerPass):
    """Replace `if` with statically selected branch when test is constant."""

    name = "CppConstConditionPass"
    min_opt_level = 1

    def _rewrite_stmt_list(self, body: list[Any]) -> int:
        changed = 0
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            changed += self._rewrite_stmt(stmt)

        rewritten: list[dict[str, Any]] = []
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            kind = stmt.get("kind")
            if kind != "If":
                rewritten.append(stmt)
                continue
            truth = _const_truth_value(stmt.get("test"))
            if truth is None:
                rewritten.append(stmt)
                continue
            selected_obj = stmt.get("body" if truth else "orelse")
            selected = selected_obj if isinstance(selected_obj, list) else []
            for selected_stmt in selected:
                if isinstance(selected_stmt, dict):
                    rewritten.append(selected_stmt)
            changed += 1
        body[:] = rewritten
        return changed

    def _rewrite_stmt(self, stmt: dict[str, Any]) -> int:
        changed = 0
        for key in ("body", "orelse", "finalbody"):
            child = stmt.get(key)
            if isinstance(child, list):
                changed += self._rewrite_stmt_list(child)

        handlers_obj = stmt.get("handlers")
        handlers = handlers_obj if isinstance(handlers_obj, list) else []
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            body_obj = handler.get("body")
            if isinstance(body_obj, list):
                changed += self._rewrite_stmt_list(body_obj)

        cases_obj = stmt.get("cases")
        cases = cases_obj if isinstance(cases_obj, list) else []
        for case in cases:
            if not isinstance(case, dict):
                continue
            body_obj = case.get("body")
            if isinstance(body_obj, list):
                changed += self._rewrite_stmt_list(body_obj)
        return changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        body_obj = cpp_ir.get("body")
        if not isinstance(body_obj, list):
            return CppOptResult()
        changed = self._rewrite_stmt_list(body_obj)
        return CppOptResult(changed=changed > 0, change_count=changed)

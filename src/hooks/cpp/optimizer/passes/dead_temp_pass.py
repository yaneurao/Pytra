"""Drop provably dead temporary assignments before C++ emission."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult


TEMP_PREFIXES = ("__tmp", "__tuple", "__it", "__itobj", "__yield_values", "__finally")
WRITE_TARGET_KEYS = {"target", "targets", "target_plan", "optional_vars"}


def _node_kind(node: dict[str, Any]) -> str:
    kind = node.get("kind")
    return kind if isinstance(kind, str) else ""


def _name_target_id(target: Any) -> str:
    target_d = target if isinstance(target, dict) else {}
    if _node_kind(target_d) != "Name":
        return ""
    ident = target_d.get("id")
    return ident if isinstance(ident, str) else ""


def _assignment_target_name(stmt: dict[str, Any]) -> str:
    kind = _node_kind(stmt)
    if kind == "Assign":
        direct = _name_target_id(stmt.get("target"))
        if direct != "":
            return direct
        targets_obj = stmt.get("targets")
        targets = targets_obj if isinstance(targets_obj, list) else []
        if len(targets) == 1:
            return _name_target_id(targets[0])
    elif kind == "AnnAssign":
        return _name_target_id(stmt.get("target"))
    return ""


def _assignment_value_expr(stmt: dict[str, Any]) -> dict[str, Any]:
    value = stmt.get("value")
    return value if isinstance(value, dict) else {}


def _is_temp_name(name: str) -> bool:
    for prefix in TEMP_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def _is_pure_expr(expr: dict[str, Any]) -> bool:
    kind = _node_kind(expr)
    if kind in {"Constant", "Name"}:
        return True
    if kind in {"Tuple", "List", "Set"}:
        items_obj = expr.get("elements")
        items = items_obj if isinstance(items_obj, list) else []
        for item in items:
            if not isinstance(item, dict) or not _is_pure_expr(item):
                return False
        return True
    if kind == "Dict":
        pairs_obj = expr.get("pairs")
        pairs = pairs_obj if isinstance(pairs_obj, list) else []
        for pair in pairs:
            pair_d = pair if isinstance(pair, dict) else {}
            key = pair_d.get("key")
            value = pair_d.get("value")
            if not isinstance(key, dict) or not _is_pure_expr(key):
                return False
            if not isinstance(value, dict) or not _is_pure_expr(value):
                return False
        return True
    if kind == "UnaryOp":
        operand = expr.get("operand")
        return isinstance(operand, dict) and _is_pure_expr(operand)
    if kind == "BinOp":
        left = expr.get("left")
        right = expr.get("right")
        return isinstance(left, dict) and isinstance(right, dict) and _is_pure_expr(left) and _is_pure_expr(right)
    if kind == "BoolOp":
        values_obj = expr.get("values")
        values = values_obj if isinstance(values_obj, list) else []
        for value in values:
            if not isinstance(value, dict) or not _is_pure_expr(value):
                return False
        return True
    if kind == "IfExp":
        test = expr.get("test")
        body = expr.get("body")
        orelse = expr.get("orelse")
        return (
            isinstance(test, dict)
            and isinstance(body, dict)
            and isinstance(orelse, dict)
            and _is_pure_expr(test)
            and _is_pure_expr(body)
            and _is_pure_expr(orelse)
        )
    return False


def _contains_name_read(node: Any, name: str) -> bool:
    if isinstance(node, list):
        for item in node:
            if _contains_name_read(item, name):
                return True
        return False
    if not isinstance(node, dict):
        return False
    if _node_kind(node) == "Name":
        ident = node.get("id")
        return isinstance(ident, str) and ident == name
    for key, value in node.items():
        if key in WRITE_TARGET_KEYS:
            continue
        if _contains_name_read(value, name):
            return True
    return False


def _stmt_child_stmt_lists(stmt: dict[str, Any]) -> list[list[dict[str, Any]]]:
    out: list[list[dict[str, Any]]] = []
    for key in ("body", "orelse", "finalbody"):
        child_obj = stmt.get(key)
        if isinstance(child_obj, list):
            child: list[dict[str, Any]] = []
            for item in child_obj:
                if isinstance(item, dict):
                    child.append(item)
            out.append(child)
    handlers_obj = stmt.get("handlers")
    handlers = handlers_obj if isinstance(handlers_obj, list) else []
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        body_obj = handler.get("body")
        if isinstance(body_obj, list):
            body: list[dict[str, Any]] = []
            for item in body_obj:
                if isinstance(item, dict):
                    body.append(item)
            out.append(body)
    cases_obj = stmt.get("cases")
    cases = cases_obj if isinstance(cases_obj, list) else []
    for case in cases:
        if not isinstance(case, dict):
            continue
        body_obj = case.get("body")
        if isinstance(body_obj, list):
            body: list[dict[str, Any]] = []
            for item in body_obj:
                if isinstance(item, dict):
                    body.append(item)
            out.append(body)
    return out


class CppDeadTempPass(CppOptimizerPass):
    """Remove unused temporary assignments when RHS is side-effect free."""

    name = "CppDeadTempPass"
    min_opt_level = 1

    def _rewrite_stmt(self, stmt: dict[str, Any]) -> int:
        changed = 0
        for child in _stmt_child_stmt_lists(stmt):
            changed += self._rewrite_stmt_list(child)
        return changed

    def _rewrite_stmt_list(self, body: list[dict[str, Any]]) -> int:
        changed = 0
        for stmt in body:
            changed += self._rewrite_stmt(stmt)

        kept: list[dict[str, Any]] = []
        for i, stmt in enumerate(body):
            target_name = _assignment_target_name(stmt)
            if target_name == "" or not _is_temp_name(target_name):
                kept.append(stmt)
                continue
            value_expr = _assignment_value_expr(stmt)
            remaining = body[i + 1 :]
            if len(value_expr) == 0 or not _is_pure_expr(value_expr):
                kept.append(stmt)
                continue
            if _contains_name_read(remaining, target_name):
                kept.append(stmt)
                continue
            changed += 1
        if len(kept) != len(body):
            body[:] = kept
        return changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        body_obj = cpp_ir.get("body")
        body = body_obj if isinstance(body_obj, list) else []
        stmt_list: list[dict[str, Any]] = []
        for item in body:
            if isinstance(item, dict):
                stmt_list.append(item)
        changed = self._rewrite_stmt_list(stmt_list)
        if len(stmt_list) != len(body):
            cpp_ir["body"] = stmt_list
        return CppOptResult(changed=changed > 0, change_count=changed)

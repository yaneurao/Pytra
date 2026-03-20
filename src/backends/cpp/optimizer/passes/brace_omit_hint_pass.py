"""Annotate statement-level brace-omission hints for C++ emitter."""

from __future__ import annotations

from pytra.typing import Any

from backends.cpp.optimizer.context import CppOptContext
from backends.cpp.optimizer.context import CppOptimizerPass
from backends.cpp.optimizer.context import CppOptResult


_SINGLE_STMT_NO_BRACE_KINDS = {
    "Return",
    "Expr",
    "Assign",
    "AnnAssign",
    "AugAssign",
    "Swap",
    "Raise",
    "Break",
    "Continue",
}


def _dict_stmt_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


def _node_kind(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    kind_any = node.get("kind")
    if isinstance(kind_any, str):
        return kind_any
    return ""


def _can_omit_single_stmt(stmts: list[dict[str, Any]]) -> bool:
    if len(stmts) != 1:
        return False
    one = stmts[0]
    kind = _node_kind(one)
    if kind == "Assign":
        target = one.get("target")
        if _node_kind(target) == "Tuple":
            return False
    return kind in _SINGLE_STMT_NO_BRACE_KINDS


def _default_stmt_omit_braces(kind: str, stmt: dict[str, Any]) -> bool:
    body_stmts = _dict_stmt_list(stmt.get("body"))
    if kind == "If":
        else_stmts = _dict_stmt_list(stmt.get("orelse"))
        if not _can_omit_single_stmt(body_stmts):
            return False
        if len(else_stmts) == 0:
            return True
        return _can_omit_single_stmt(else_stmts)
    if kind == "ForRange":
        if len(_dict_stmt_list(stmt.get("orelse"))) != 0:
            return False
        return _can_omit_single_stmt(body_stmts)
    if kind == "For":
        if len(_dict_stmt_list(stmt.get("orelse"))) != 0:
            return False
        target = stmt.get("target")
        if _node_kind(target) == "Tuple":
            return False
        return _can_omit_single_stmt(body_stmts)
    if kind == "ForCore":
        if len(_dict_stmt_list(stmt.get("orelse"))) != 0:
            return False
        iter_plan = stmt.get("iter_plan")
        target_plan = stmt.get("target_plan")
        if _node_kind(iter_plan) != "StaticRangeForPlan":
            return False
        if _node_kind(target_plan) != "NameTarget":
            return False
        return _can_omit_single_stmt(body_stmts)
    return False


class CppBraceOmitHintPass(CppOptimizerPass):
    """Attach `cpp_omit_braces_v1` boolean to loop/if statements."""

    name = "CppBraceOmitHintPass"
    min_opt_level = 1

    def _visit_stmt(self, stmt: dict[str, Any]) -> int:
        changed = 0
        kind = _node_kind(stmt)
        if kind in {"If", "ForRange", "For", "ForCore"}:
            hint = _default_stmt_omit_braces(kind, stmt)
            if stmt.get("cpp_omit_braces_v1") != hint:
                stmt["cpp_omit_braces_v1"] = hint
                changed += 1
        for key in ("body", "orelse", "finalbody"):
            nested = _dict_stmt_list(stmt.get(key))
            changed += self._visit_stmt_list(nested)
        return changed

    def _visit_stmt_list(self, stmts: list[dict[str, Any]]) -> int:
        changed = 0
        for stmt in stmts:
            changed += self._visit_stmt(stmt)
        return changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        if context.opt_level < 1:
            return CppOptResult(changed=False, change_count=0)
        body = _dict_stmt_list(cpp_ir.get("body"))
        changed = self._visit_stmt_list(body)
        return CppOptResult(changed=changed > 0, change_count=changed)

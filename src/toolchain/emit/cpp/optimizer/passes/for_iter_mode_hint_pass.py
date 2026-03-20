"""Annotate resolved iter_mode hints for legacy `For` nodes."""

from __future__ import annotations

from pytra.typing import Any

from toolchain.emit.cpp.optimizer.context import CppOptContext
from toolchain.emit.cpp.optimizer.context import CppOptimizerPass
from toolchain.emit.cpp.optimizer.context import CppOptResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _contains_union(type_name: str) -> bool:
    return "|" in type_name


def _split_union(type_name: str) -> list[str]:
    parts = type_name.split("|")
    out: list[str] = []
    for p in parts:
        t = _normalize_type_name(p)
        if t != "unknown":
            out.append(t)
    return out


def _is_any_like(type_name: str) -> bool:
    return type_name in {"Any", "object"}


def _infer_iter_mode(stmt: dict[str, Any]) -> str | None:
    mode_any = stmt.get("iter_mode")
    mode = mode_any.strip() if isinstance(mode_any, str) else ""
    if mode in {"runtime_protocol", "static_fastpath"}:
        return mode
    if mode != "":
        return None
    iter_expr_any = stmt.get("iter")
    iter_expr = iter_expr_any if isinstance(iter_expr_any, dict) else {}
    iter_t = _normalize_type_name(iter_expr.get("resolved_type"))
    if _is_any_like(iter_t):
        return "runtime_protocol"
    if _contains_union(iter_t):
        for part in _split_union(iter_t):
            if _is_any_like(part):
                return "runtime_protocol"
        return "static_fastpath"
    # Keep legacy behavior: unknown also falls back to static path.
    return "static_fastpath"


class CppForIterModeHintPass(CppOptimizerPass):
    """Move legacy `For` iter-mode choice from emitter to optimizer hint."""

    name = "CppForIterModeHintPass"
    min_opt_level = 1

    def _visit(self, node: Any, *, allow_hint: bool) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item, allow_hint=allow_hint)
            return changed
        if not isinstance(node, dict):
            return 0
        if allow_hint and node.get("kind") == "For":
            mode = _infer_iter_mode(node)
            if mode is not None and node.get("cpp_iter_mode_v1") != mode:
                node["cpp_iter_mode_v1"] = mode
                changed += 1
        for value in node.values():
            changed += self._visit(value, allow_hint=allow_hint)
        return changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        flags = context.debug_flags if isinstance(context.debug_flags, dict) else {}
        allow_hint = False
        changed = self._visit(cpp_ir, allow_hint=allow_hint)
        return CppOptResult(changed=changed > 0, change_count=changed)

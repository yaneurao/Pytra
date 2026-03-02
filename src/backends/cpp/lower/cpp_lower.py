"""C++ lower stage (`EAST3 -> Cpp IR`)."""

from __future__ import annotations

from pytra.std.typing import Any


_CPP_STMT_KINDS = {
    "Expr",
    "Return",
    "Assign",
    "Swap",
    "AnnAssign",
    "AugAssign",
    "If",
    "While",
    "ForRange",
    "For",
    "ForCore",
    "Raise",
    "Try",
    "FunctionDef",
    "ClassDef",
    "Pass",
    "Break",
    "Continue",
    "Yield",
    "Import",
    "ImportFrom",
}


def _annotate_stmt_kind_hints(node: Any) -> int:
    changed = 0
    if isinstance(node, list):
        for item in node:
            changed += _annotate_stmt_kind_hints(item)
        return changed
    if not isinstance(node, dict):
        return 0
    kind_obj = node.get("kind")
    if isinstance(kind_obj, str) and kind_obj in _CPP_STMT_KINDS:
        if node.get("cpp_stmt_kind_v1") != kind_obj:
            node["cpp_stmt_kind_v1"] = kind_obj
            changed += 1
    for value in node.values():
        changed += _annotate_stmt_kind_hints(value)
    return changed


class CppLower:
    """Lower EAST3 module into C++ backend IR.

    Phase-1 keeps the IR shape identical to EAST3 while fixing the stage boundary.
    """

    def lower(
        self,
        east_module: dict[str, Any],
        *,
        debug_flags: dict[str, object] | None = None,
    ) -> tuple[dict[str, Any], dict[str, object]]:
        if not isinstance(east_module, dict):
            raise RuntimeError("C++ lower input must be EAST3 Module dict")
        kind = east_module.get("kind")
        if kind != "Module":
            raise RuntimeError("C++ lower input kind must be Module")
        change_count = _annotate_stmt_kind_hints(east_module)
        report: dict[str, object] = {
            "stage": "cpp_lower",
            "changed": change_count > 0,
            "change_count": change_count,
            "input_kind": "Module",
            "mode": "pass_through_v1_stmt_kind_hint",
        }
        if isinstance(debug_flags, dict) and len(debug_flags) > 0:
            report["debug_flags"] = dict(debug_flags)
        return east_module, report


def lower_cpp_from_east3(
    east_module: dict[str, Any],
    *,
    debug_flags: dict[str, object] | None = None,
) -> tuple[dict[str, Any], dict[str, object]]:
    """Convenience wrapper for C++ lower stage."""
    return CppLower().lower(east_module, debug_flags=debug_flags)

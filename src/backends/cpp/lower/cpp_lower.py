"""C++ lower stage (`EAST3 -> Cpp IR`)."""

from __future__ import annotations

from pytra.std.typing import Any


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
        report: dict[str, object] = {
            "stage": "cpp_lower",
            "changed": False,
            "change_count": 0,
            "input_kind": "Module",
            "mode": "pass_through_v0",
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

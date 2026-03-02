"""Shared context/result contracts for C++ optimizer passes."""

from __future__ import annotations

from pytra.std.typing import Any


class CppOptContext:
    """Runtime context shared by C++ optimizer passes."""

    def __init__(
        self,
        opt_level: int = 1,
        target_cpp_std: str = "c++20",
        debug_flags: dict[str, object] | None = None,
        enabled_passes: set[str] | None = None,
        disabled_passes: set[str] | None = None,
    ) -> None:
        self.opt_level = opt_level
        self.target_cpp_std = target_cpp_std
        self.debug_flags = dict(debug_flags) if isinstance(debug_flags, dict) else {}
        self.enabled_passes = set(enabled_passes) if isinstance(enabled_passes, set) else set()
        self.disabled_passes = set(disabled_passes) if isinstance(disabled_passes, set) else set()


class CppOptResult:
    """One-pass execution result."""

    def __init__(
        self,
        *,
        changed: bool = False,
        change_count: int = 0,
        warnings: list[str] | None = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        self.changed = changed
        self.change_count = change_count
        self.warnings = list(warnings) if isinstance(warnings, list) else []
        self.elapsed_ms = elapsed_ms

    def merge(self, other: "CppOptResult") -> None:
        self.changed = self.changed or other.changed
        self.change_count += other.change_count
        self.elapsed_ms += other.elapsed_ms
        for item in other.warnings:
            self.warnings.append(item)

    def to_dict(self) -> dict[str, object]:
        return {
            "changed": self.changed,
            "change_count": self.change_count,
            "warnings": list(self.warnings),
            "elapsed_ms": self.elapsed_ms,
        }


class CppOptimizerPass:
    """Minimal pass protocol for C++ optimizer."""

    name = "CppOptimizerPass"
    min_opt_level = 1

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = cpp_ir
        _ = context
        return CppOptResult()


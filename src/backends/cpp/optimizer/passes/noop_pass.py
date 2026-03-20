"""No-op pass for phase-1 C++ optimizer scaffolding."""

from __future__ import annotations

from pytra.typing import Any

from backends.cpp.optimizer.context import CppOptContext
from backends.cpp.optimizer.context import CppOptimizerPass
from backends.cpp.optimizer.context import CppOptResult


class CppNoOpPass(CppOptimizerPass):
    """Keep input IR unchanged."""

    name = "CppNoOpPass"
    min_opt_level = 1

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = cpp_ir
        _ = context
        return CppOptResult()


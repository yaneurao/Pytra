"""C++ optimizer package exports."""

from __future__ import annotations

from toolchain.emit.cpp.optimizer.context import CppOptContext
from toolchain.emit.cpp.optimizer.context import CppOptimizerPass
from toolchain.emit.cpp.optimizer.context import CppOptResult
from toolchain.emit.cpp.optimizer.cpp_optimizer import CppPassManager
from toolchain.emit.cpp.optimizer.cpp_optimizer import build_default_cpp_pass_manager
from toolchain.emit.cpp.optimizer.cpp_optimizer import optimize_cpp_ir
from toolchain.emit.cpp.optimizer.cpp_optimizer import parse_cpp_opt_pass_overrides
from toolchain.emit.cpp.optimizer.cpp_optimizer import resolve_cpp_opt_level
from toolchain.emit.cpp.optimizer.cpp_ir_optimizer import CppIrOptimizer
from toolchain.emit.cpp.optimizer.cpp_ir_optimizer import optimize_cpp_ir_module
from toolchain.emit.cpp.optimizer.trace import render_cpp_opt_trace

__all__ = [
    "CppOptContext",
    "CppOptimizerPass",
    "CppOptResult",
    "CppPassManager",
    "CppIrOptimizer",
    "build_default_cpp_pass_manager",
    "optimize_cpp_ir",
    "optimize_cpp_ir_module",
    "parse_cpp_opt_pass_overrides",
    "resolve_cpp_opt_level",
    "render_cpp_opt_trace",
]

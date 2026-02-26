"""C++ optimizer package exports."""

from __future__ import annotations

from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult
from hooks.cpp.optimizer.cpp_optimizer import CppPassManager
from hooks.cpp.optimizer.cpp_optimizer import build_default_cpp_pass_manager
from hooks.cpp.optimizer.cpp_optimizer import optimize_cpp_ir
from hooks.cpp.optimizer.cpp_optimizer import parse_cpp_opt_pass_overrides
from hooks.cpp.optimizer.cpp_optimizer import resolve_cpp_opt_level
from hooks.cpp.optimizer.trace import render_cpp_opt_trace

__all__ = [
    "CppOptContext",
    "CppOptimizerPass",
    "CppOptResult",
    "CppPassManager",
    "build_default_cpp_pass_manager",
    "optimize_cpp_ir",
    "parse_cpp_opt_pass_overrides",
    "resolve_cpp_opt_level",
    "render_cpp_opt_trace",
]


"""C++ IR optimizer stage wrapper (`Cpp IR -> Cpp IR`)."""

from __future__ import annotations

from pytra.typing import Any

from toolchain.emit.cpp.optimizer.cpp_optimizer import optimize_cpp_ir


class CppIrOptimizer:
    """Thin stage wrapper over the existing C++ optimizer pass manager."""

    def optimize(
        self,
        cpp_ir: dict[str, Any],
        *,
        opt_level: str | int | object = 1,
        target_cpp_std: str = "c++20",
        opt_pass_spec: str = "",
        debug_flags: dict[str, object] | None = None,
    ) -> tuple[dict[str, Any], dict[str, object]]:
        return optimize_cpp_ir(
            cpp_ir,
            opt_level=opt_level,
            target_cpp_std=target_cpp_std,
            opt_pass_spec=opt_pass_spec,
            debug_flags=debug_flags,
        )


def optimize_cpp_ir_module(
    cpp_ir: dict[str, Any],
    *,
    opt_level: str | int | object = 1,
    target_cpp_std: str = "c++20",
    opt_pass_spec: str = "",
    debug_flags: dict[str, object] | None = None,
) -> tuple[dict[str, Any], dict[str, object]]:
    """Convenience wrapper for the C++ IR optimizer stage."""
    return CppIrOptimizer().optimize(
        cpp_ir,
        opt_level=opt_level,
        target_cpp_std=target_cpp_std,
        opt_pass_spec=opt_pass_spec,
        debug_flags=debug_flags,
    )

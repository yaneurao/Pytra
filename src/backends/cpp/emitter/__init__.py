"""C++ emitter package exports."""

from __future__ import annotations

from backends.cpp.emitter.cpp_emitter import (
    CppEmitter,
    emit_cpp_from_east,
)
from backends.cpp.emitter.profile_loader import load_cpp_profile
from pytra.typing import Any

__all__ = [
    "CppEmitter",
    "emit_cpp_from_east",
    "load_cpp_profile",
    "transpile_to_cpp",
]


def transpile_to_cpp(
    east_module: dict[str, Any],
    negative_index_mode: str = "const_only",
    bounds_check_mode: str = "off",
    floor_div_mode: str = "native",
    mod_mode: str = "native",
    int_width: str = "64",
    str_index_mode: str = "native",
    str_slice_mode: str = "byte",
    opt_level: str = "2",
    top_namespace: str = "",
    emit_main: bool = True,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
) -> str:
    """Public compatibility API: delegate to the C++ CLI module."""
    from backends.cpp import cli as cpp_cli

    return cpp_cli.transpile_to_cpp(
        east_module,
        negative_index_mode=negative_index_mode,
        bounds_check_mode=bounds_check_mode,
        floor_div_mode=floor_div_mode,
        mod_mode=mod_mode,
        int_width=int_width,
        str_index_mode=str_index_mode,
        str_slice_mode=str_slice_mode,
        opt_level=opt_level,
        top_namespace=top_namespace,
        emit_main=emit_main,
        cpp_opt_level=cpp_opt_level,
        cpp_opt_pass=cpp_opt_pass,
        dump_cpp_ir_before_opt=dump_cpp_ir_before_opt,
        dump_cpp_ir_after_opt=dump_cpp_ir_after_opt,
        dump_cpp_opt_trace=dump_cpp_opt_trace,
    )

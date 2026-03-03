"""C++ emitter package exports."""

from __future__ import annotations

from backends.cpp.emitter.cpp_emitter import (
    CppEmitter,
    emit_cpp_from_east,
    install_py2cpp_runtime_symbols,
)
from backends.cpp.emitter.profile_loader import load_cpp_profile
from pytra.std.typing import Any

__all__ = [
    "CppEmitter",
    "emit_cpp_from_east",
    "install_py2cpp_runtime_symbols",
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
    cpp_list_model: str = "",
) -> str:
    """Public compatibility API: EAST3 module -> C++ source."""
    return emit_cpp_from_east(
        east_module,
        {},
        negative_index_mode,
        bounds_check_mode,
        floor_div_mode,
        mod_mode,
        int_width,
        str_index_mode,
        str_slice_mode,
        opt_level,
        top_namespace,
        emit_main,
        cpp_opt_level,
        cpp_opt_pass,
        dump_cpp_ir_before_opt,
        dump_cpp_ir_after_opt,
        dump_cpp_opt_trace,
        cpp_list_model,
    )

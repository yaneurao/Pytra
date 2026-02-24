"""C++ emitter package exports."""

from __future__ import annotations

from hooks.cpp.emitter.cpp_emitter import CppEmitter, install_py2cpp_runtime_symbols
from hooks.cpp.profile import load_cpp_profile
from pytra.std.typing import Any

__all__ = [
    "CppEmitter",
    "install_py2cpp_runtime_symbols",
    "load_cpp_profile",
    "transpile_to_cpp",
]


def transpile_to_cpp(*args: Any, **kwargs: Any) -> str:
    """Delegate to `py2cpp.transpile_to_cpp` for compatibility."""
    import py2cpp

    return py2cpp.transpile_to_cpp(*args, **kwargs)  # type: ignore[no-any-return]

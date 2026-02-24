"""C++ emitter package exports."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cpp.emitter.cpp_emitter import CppEmitter, install_py2cpp_runtime_symbols

__all__ = [
    "CppEmitter",
    "install_py2cpp_runtime_symbols",
    "load_cpp_profile",
    "transpile_to_cpp",
]


def load_cpp_profile() -> dict[str, Any]:
    """Load C++ language profile via `py2cpp` entrypoint."""
    import py2cpp

    return py2cpp.load_cpp_profile()


def transpile_to_cpp(*args: Any, **kwargs: Any) -> str:
    """Delegate to `py2cpp.transpile_to_cpp` for compatibility."""
    import py2cpp

    return py2cpp.transpile_to_cpp(*args, **kwargs)  # type: ignore[no-any-return]

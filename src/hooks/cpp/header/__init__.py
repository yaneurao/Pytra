from __future__ import annotations

from pytra.std.typing import Any
from hooks.cpp.header.cpp_header import build_cpp_header_from_east as _build_cpp_header_from_east

__all__ = ["build_cpp_header_from_east"]


def build_cpp_header_from_east(*args: Any, **kwargs: Any) -> str:
    """Delegate to the concrete header builder."""
    return _build_cpp_header_from_east(*args, **kwargs)  # type: ignore[no-any-return]

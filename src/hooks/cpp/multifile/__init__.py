from __future__ import annotations

from pytra.std.typing import Any
from hooks.cpp.multifile.cpp_multifile import write_multi_file_cpp as _write_multi_file_cpp_impl

__all__ = ["write_multi_file_cpp"]


def write_multi_file_cpp(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility wrapper to delegate multi-file output generation."""
    return _write_multi_file_cpp_impl(*args, **kwargs)  # type: ignore[no-any-return]

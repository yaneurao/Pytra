"""Frontend bootstrap namespace (`src/pytra/frontends`).

Keep package import side effects minimal to avoid cycles with
``pytra.compiler.transpile_cli`` during staged migration.
"""

from __future__ import annotations

from pytra.std.typing import Any


def add_common_transpile_args(*args: Any, **kwargs: Any) -> None:
    from .python_frontend import add_common_transpile_args as _impl

    _impl(*args, **kwargs)


def normalize_common_transpile_args(*args: Any, **kwargs: Any) -> Any:
    from .python_frontend import normalize_common_transpile_args as _impl

    return _impl(*args, **kwargs)


def load_east3_document(*args: Any, **kwargs: Any) -> dict[str, object]:
    from .python_frontend import load_east3_document as _impl

    return _impl(*args, **kwargs)

__all__ = [
    "add_common_transpile_args",
    "normalize_common_transpile_args",
    "load_east3_document",
]

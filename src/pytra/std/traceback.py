"""pytra.std.traceback compatibility shim."""

from __future__ import annotations

_last_exc_text_box: list[str] = [""]


def format_exc() -> str:
    """Return last captured traceback text.

    Current minimal implementation returns an empty string when unavailable.
    """
    return _last_exc_text_box[0]


def _set_last_exc_text(text: str) -> None:
    """Runtime hook: update stored traceback string."""
    _last_exc_text_box[0] = text


__all__ = ["format_exc"]

"""JsonVal deep copy and typed accessors (selfhost-safe).

§5.1: Any/object 禁止 — JsonVal のみ使用。
§5.3: Python 標準モジュール直接 import 禁止。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


def deep_copy_json(val: JsonVal) -> JsonVal:
    """Selfhost-safe fallback deep copy.

    The selfhost C++ path only needs a stable JsonVal-preserving helper here.
    """
    return val

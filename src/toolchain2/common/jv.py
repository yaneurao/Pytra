"""JsonVal deep copy and typed accessors (selfhost-safe).

§5.1: Any/object 禁止 — JsonVal のみ使用。
§5.3: Python 標準モジュール直接 import 禁止。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


def deep_copy_json(val: JsonVal) -> JsonVal:
    """Deep copy a JSON-compatible value (copy.deepcopy の代替)."""
    if val is None or isinstance(val, bool) or isinstance(val, int) or isinstance(val, float) or isinstance(val, str):
        return val
    if isinstance(val, list):
        return [deep_copy_json(item) for item in val]
    if isinstance(val, dict):
        return {key: deep_copy_json(value) for key, value in val.items()}
    return val

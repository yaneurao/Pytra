"""ランタイム呼び出しマップ（JSON定義）ローダー。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_CPP_MODULE_ATTR_CALL_MAP: dict[str, dict[str, str]] = {
    "math": {
        "sqrt": "py_math::sqrt",
        "sin": "py_math::sin",
        "cos": "py_math::cos",
        "tan": "py_math::tan",
        "exp": "py_math::exp",
        "log": "py_math::log",
        "log10": "py_math::log10",
        "fabs": "py_math::fabs",
        "floor": "py_math::floor",
        "ceil": "py_math::ceil",
        "pow": "py_math::pow",
    }
}

_CACHE_CPP_MODULE_ATTR_CALL_MAP: dict[str, dict[str, str]] | None = None


def _safe_nested_dict(obj: Any, keys: list[str]) -> dict[str, Any] | None:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    if not isinstance(cur, dict):
        return None
    return cur


def _deep_copy_str_map(v: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for k, inner in v.items():
        out[k] = dict(inner)
    return out


def _load_runtime_call_map_json() -> dict[str, Any] | None:
    path = Path(__file__).with_name("runtime_call_map.json")
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def load_cpp_module_attr_call_map() -> dict[str, dict[str, str]]:
    """C++ の `module.attr(...)` -> ランタイム呼び出しマップを返す。"""
    global _CACHE_CPP_MODULE_ATTR_CALL_MAP
    if _CACHE_CPP_MODULE_ATTR_CALL_MAP is not None:
        return _deep_copy_str_map(_CACHE_CPP_MODULE_ATTR_CALL_MAP)

    merged = _deep_copy_str_map(_DEFAULT_CPP_MODULE_ATTR_CALL_MAP)
    payload = _load_runtime_call_map_json()
    node = _safe_nested_dict(payload, ["cpp", "module_attr_call"]) if payload is not None else None
    if node is not None:
        for module_name, raw_map in node.items():
            if not isinstance(module_name, str) or not isinstance(raw_map, dict):
                continue
            cur = dict(merged.get(module_name, {}))
            for attr, runtime_call in raw_map.items():
                if isinstance(attr, str) and isinstance(runtime_call, str) and attr != "" and runtime_call != "":
                    cur[attr] = runtime_call
            merged[module_name] = cur

    _CACHE_CPP_MODULE_ATTR_CALL_MAP = merged
    return _deep_copy_str_map(merged)


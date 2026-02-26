"""Conservative runtime fast-path rewrites for C++ backend IR."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _is_any_like_type(type_name: str) -> bool:
    return type_name in {"", "unknown", "Any", "object"}


def _try_fastpath(node: dict[str, Any]) -> dict[str, Any] | None:
    kind = node.get("kind")
    if kind == "Unbox":
        value_obj = node.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return None
        target_t = _normalize_type_name(node.get("target"))
        source_t = _normalize_type_name(value.get("resolved_type"))
        if target_t == "unknown" or source_t == "unknown":
            return None
        if target_t != source_t or _is_any_like_type(target_t):
            return None
        return dict(value)

    if kind == "Box":
        value_obj = node.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return None
        source_t = _normalize_type_name(value.get("resolved_type"))
        if not _is_any_like_type(source_t):
            return None
        return dict(value)

    if kind == "ObjBool":
        value_obj = node.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return None
        source_t = _normalize_type_name(value.get("resolved_type"))
        if source_t != "bool":
            return None
        return dict(value)

    return None


class CppRuntimeFastPathPass(CppOptimizerPass):
    """Apply limited runtime-contract-equivalent fast paths."""

    name = "CppRuntimeFastPathPass"
    min_opt_level = 2

    def _rewrite(self, node: Any) -> tuple[Any, int]:
        if isinstance(node, list):
            out = node
            changed = 0
            for i, item in enumerate(node):
                new_item, delta = self._rewrite(item)
                if new_item is not item:
                    out[i] = new_item
                changed += delta
            return out, changed

        if not isinstance(node, dict):
            return node, 0

        out = node
        changed = 0
        for key in list(node.keys()):
            value = node.get(key)
            new_value, delta = self._rewrite(value)
            if new_value is not value:
                out[key] = new_value
            changed += delta

        fastpath_node = _try_fastpath(out)
        if fastpath_node is not None:
            return fastpath_node, changed + 1
        return out, changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        _, change_count = self._rewrite(cpp_ir)
        return CppOptResult(changed=change_count > 0, change_count=change_count)

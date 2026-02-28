"""Conservatively reduce redundant numeric cast chains in EAST3."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_ANY_TYPES = {"Any", "any", "object", "unknown", ""}
_NUMERIC_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "int",
    "float32",
    "float64",
    "float",
}


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _canonical_numeric_type(value: Any) -> str:
    t = _normalize_type_name(value)
    if t == "int":
        return "int64"
    if t == "float":
        return "float64"
    if t in _NUMERIC_TYPES:
        return t
    return ""


def _is_any_like_type(value: Any) -> bool:
    t = _normalize_type_name(value)
    if t in _ANY_TYPES:
        return True
    if "|" in t:
        parts = [p.strip() for p in t.split("|")]
        for p in parts:
            if p in {"Any", "any", "object"}:
                return True
    return False


def _is_static_cast_call(node: dict[str, Any]) -> bool:
    if node.get("kind") != "Call":
        return False
    if node.get("lowered_kind") != "BuiltinCall":
        return False
    return _normalize_type_name(node.get("runtime_call")) == "static_cast"


class NumericCastChainReductionPass(East3OptimizerPass):
    """Reduce no-op numeric conversion chains (`static_cast` / `Unbox`)."""

    name = "NumericCastChainReductionPass"
    min_opt_level = 1

    def _fold_static_cast(self, node: dict[str, Any]) -> dict[str, Any] | None:
        if not _is_static_cast_call(node):
            return None
        args_obj = node.get("args")
        args = args_obj if isinstance(args_obj, list) else []
        if len(args) != 1:
            return None
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return None
        dst_t = _canonical_numeric_type(node.get("resolved_type"))
        if dst_t == "":
            return None
        src_t = _canonical_numeric_type(arg0.get("resolved_type"))
        if src_t == "":
            return None
        if src_t != dst_t:
            return None
        if _is_any_like_type(arg0.get("resolved_type")):
            return None
        return arg0

    def _fold_unbox(self, node: dict[str, Any]) -> dict[str, Any] | None:
        if node.get("kind") != "Unbox":
            return None
        value_obj = node.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return None
        dst_t = _canonical_numeric_type(node.get("target"))
        if dst_t == "":
            dst_t = _canonical_numeric_type(node.get("resolved_type"))
        if dst_t == "":
            return None
        src_t = _canonical_numeric_type(value.get("resolved_type"))
        if src_t == "":
            return None
        if src_t != dst_t:
            return None
        if _is_any_like_type(value.get("resolved_type")):
            return None
        return value

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
        keys = list(node.keys())
        for key in keys:
            value = node.get(key)
            new_value, delta = self._rewrite(value)
            if new_value is not value:
                out[key] = new_value
            changed += delta

        folded = self._fold_static_cast(out)
        if folded is not None:
            return folded, changed + 1
        folded = self._fold_unbox(out)
        if folded is not None:
            return folded, changed + 1
        return out, changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        _, change_count = self._rewrite(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

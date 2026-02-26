"""Cleanup pass for no-op cast metadata and static_cast nodes."""

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


def _is_noop_cast_entry(cast_entry: dict[str, Any]) -> bool:
    from_t = _normalize_type_name(cast_entry.get("from"))
    to_t = _normalize_type_name(cast_entry.get("to"))
    if from_t == "unknown" or to_t == "unknown":
        return False
    return from_t == to_t


def _try_fold_noop_static_cast(call_node: dict[str, Any]) -> dict[str, Any] | None:
    if call_node.get("kind") != "Call":
        return None
    if call_node.get("runtime_call") != "static_cast":
        return None
    args_obj = call_node.get("args")
    args = args_obj if isinstance(args_obj, list) else []
    if len(args) != 1:
        return None
    arg = args[0]
    if not isinstance(arg, dict):
        return None
    target_t = _normalize_type_name(call_node.get("resolved_type"))
    source_t = _normalize_type_name(arg.get("resolved_type"))
    if target_t == "unknown" or source_t == "unknown" or target_t != source_t:
        return None
    folded = dict(arg)
    repr_obj = call_node.get("repr")
    if isinstance(repr_obj, str) and repr_obj != "":
        folded["repr"] = repr_obj
    span_obj = call_node.get("source_span")
    if isinstance(span_obj, dict):
        folded["source_span"] = span_obj
    return folded


class CppNoOpCastPass(CppOptimizerPass):
    """Drop statically-proven no-op casts from C++ backend IR."""

    name = "CppNoOpCastPass"
    min_opt_level = 1

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

        casts_obj = out.get("casts")
        casts = casts_obj if isinstance(casts_obj, list) else None
        if casts is not None:
            kept: list[Any] = []
            for cast_entry in casts:
                if isinstance(cast_entry, dict) and _is_noop_cast_entry(cast_entry):
                    changed += 1
                    continue
                kept.append(cast_entry)
            if len(kept) != len(casts):
                out["casts"] = kept

        folded = _try_fold_noop_static_cast(out)
        if folded is not None:
            return folded, changed + 1
        return out, changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        _, change_count = self._rewrite(cpp_ir)
        return CppOptResult(changed=change_count > 0, change_count=change_count)

"""Fold literal `static_cast` calls when conversion is provably no-op."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"


def _try_fold_literal_static_cast(call_node: dict[str, Any]) -> dict[str, Any] | None:
    if call_node.get("kind") != "Call":
        return None
    if call_node.get("lowered_kind") != "BuiltinCall":
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
    if arg.get("kind") != "Constant":
        return None

    target_t = _normalize_type_name(call_node.get("resolved_type"))
    source_t = _normalize_type_name(arg.get("resolved_type"))
    if target_t == "unknown" or source_t == "unknown":
        return None
    if target_t != source_t:
        return None

    folded = dict(arg)
    span_obj = call_node.get("source_span")
    if isinstance(span_obj, dict):
        folded["source_span"] = span_obj
    repr_obj = call_node.get("repr")
    if isinstance(repr_obj, str) and repr_obj != "":
        folded["repr"] = repr_obj
    return folded


class LiteralCastFoldPass(East3OptimizerPass):
    """Fold literal casts conservatively under fail-closed guards."""

    name = "LiteralCastFoldPass"
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
        keys = list(node.keys())
        for key in keys:
            value = node.get(key)
            new_value, delta = self._rewrite(value)
            if new_value is not value:
                out[key] = new_value
            changed += delta

        folded = _try_fold_literal_static_cast(out)
        if folded is not None:
            return folded, changed + 1
        return out, changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        _, change_count = self._rewrite(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)


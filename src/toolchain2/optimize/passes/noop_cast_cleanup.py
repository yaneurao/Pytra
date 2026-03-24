"""Remove statically provable no-op casts from EAST3 metadata."""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.optimize.optimizer import East3OptimizerPass, PassContext, PassResult, make_pass_result
from toolchain2.optimize.utils import normalize_type_name


def _is_noop_cast(cast_entry: dict[str, JsonVal]) -> bool:
    from_t = normalize_type_name(cast_entry.get("from"))
    to_t = normalize_type_name(cast_entry.get("to"))
    if from_t == "unknown" or to_t == "unknown":
        return False
    return from_t == to_t


class NoOpCastCleanupPass(East3OptimizerPass):
    """Drop cast entries that are guaranteed to have no effect."""

    name: str = "NoOpCastCleanupPass"
    min_opt_level: int = 1

    def _visit(self, node: JsonVal) -> int:
        removed = 0
        if isinstance(node, list):
            for item in node:
                removed += self._visit(item)
            return removed

        if not isinstance(node, dict):
            return 0

        casts_obj = node.get("casts")
        casts = casts_obj if isinstance(casts_obj, list) else None
        if casts is not None:
            kept: list[JsonVal] = []
            for cast_entry in casts:
                if isinstance(cast_entry, dict) and _is_noop_cast(cast_entry):
                    removed += 1
                    continue
                kept.append(cast_entry)
            if len(kept) != len(casts):
                node["casts"] = kept

        for value in node.values():
            removed += self._visit(value)
        return removed

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = context
        removed = self._visit(east3_doc)
        return make_pass_result(changed=removed > 0, change_count=removed)

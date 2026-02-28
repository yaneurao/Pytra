"""Normalize `dict[str, V]` key nodes to avoid redundant string casts."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _dict_key_type(owner_type: Any) -> str:
    owner_t = _normalize_type_name(owner_type)
    if not owner_t.startswith("dict[") or not owner_t.endswith("]"):
        return ""
    inner = owner_t[5:-1].strip()
    if inner == "":
        return ""
    depth = 0
    split_at = -1
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "[" or ch == "<":
            depth += 1
        elif ch == "]" or ch == ">":
            if depth > 0:
                depth -= 1
        elif ch == "," and depth == 0:
            split_at = i
            break
        i += 1
    if split_at < 0:
        return ""
    key_t = inner[:split_at].strip()
    return _normalize_type_name(key_t)


class DictStrKeyNormalizationPass(East3OptimizerPass):
    """Annotate dict-string key nodes with normalized key type metadata."""

    name = "DictStrKeyNormalizationPass"
    min_opt_level = 1

    def _mark_key(self, key_node: Any) -> int:
        key = key_node if isinstance(key_node, dict) else None
        if key is None:
            return 0
        changed = 0
        key_t = _normalize_type_name(key.get("resolved_type"))
        if key_t in {"", "unknown"}:
            key["resolved_type"] = "str"
            changed += 1
        if not bool(key.get("dict_key_verified", False)):
            key["dict_key_verified"] = True
            changed += 1
        return changed

    def _visit(self, node: Any) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0

        kind = _normalize_type_name(node.get("kind"))
        if kind == "Subscript":
            owner = node.get("value")
            owner_node = owner if isinstance(owner, dict) else None
            if owner_node is not None and _dict_key_type(owner_node.get("resolved_type")) == "str":
                changed += self._mark_key(node.get("slice"))
        elif kind in {"DictGetMaybe", "DictGetDefault", "DictPop", "DictPopDefault"}:
            owner = node.get("owner")
            owner_node = owner if isinstance(owner, dict) else None
            if owner_node is not None and _dict_key_type(owner_node.get("resolved_type")) == "str":
                changed += self._mark_key(node.get("key"))
        elif kind == "Call":
            runtime_call = _normalize_type_name(node.get("runtime_call"))
            if runtime_call in {"dict.get", "dict.pop"}:
                func_obj = node.get("func")
                func = func_obj if isinstance(func_obj, dict) else None
                owner = func.get("value") if isinstance(func, dict) else None
                owner_node = owner if isinstance(owner, dict) else None
                if owner_node is not None and _dict_key_type(owner_node.get("resolved_type")) == "str":
                    args_obj = node.get("args")
                    args = args_obj if isinstance(args_obj, list) else []
                    if len(args) >= 1:
                        changed += self._mark_key(args[0])

        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

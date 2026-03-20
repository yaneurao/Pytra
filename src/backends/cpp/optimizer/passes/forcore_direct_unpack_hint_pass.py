"""Annotate `ForCore` tuple-target direct unpack hints for C++ emitter."""

from __future__ import annotations

from pytra.typing import Any

from backends.cpp.optimizer.context import CppOptContext
from backends.cpp.optimizer.context import CppOptimizerPass
from backends.cpp.optimizer.context import CppOptResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return "unknown"


def _split_generic(payload: str) -> list[str]:
    out: list[str] = []
    cur: list[str] = []
    depth = 0
    i = 0
    while i < len(payload):
        ch = payload[i]
        if ch == "[":
            depth += 1
            cur.append(ch)
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            token = "".join(cur).strip()
            if token != "":
                out.append(token)
            cur = []
        else:
            cur.append(ch)
        i += 1
    tail = "".join(cur).strip()
    if tail != "":
        out.append(tail)
    return out


def _tuple_elem_types(type_name: str) -> list[str]:
    text = _normalize_type_name(type_name)
    if text.startswith("tuple[") and text.endswith("]"):
        return _split_generic(text[6:-1])
    return []


def _iter_item_type(stmt: dict[str, Any]) -> str:
    iter_plan_any = stmt.get("iter_plan")
    iter_plan = iter_plan_any if isinstance(iter_plan_any, dict) else {}
    item_t = _normalize_type_name(iter_plan.get("iter_item_type"))
    if item_t != "unknown":
        return item_t
    iter_expr_any = iter_plan.get("iter_expr")
    iter_expr = iter_expr_any if isinstance(iter_expr_any, dict) else {}
    expr_item_t = _normalize_type_name(iter_expr.get("iter_element_type"))
    if expr_item_t != "unknown":
        return expr_item_t
    return "unknown"


def _is_known_scalar(type_name: str) -> bool:
    t = _normalize_type_name(type_name)
    return t not in {"unknown", "Any", "object", ""}


class CppForcoreDirectUnpackHintPass(CppOptimizerPass):
    """Set `direct_unpack` hints when tuple target/item types are fully known."""

    name = "CppForcoreDirectUnpackHintPass"
    min_opt_level = 1

    def _try_rewrite_forcore(self, stmt: dict[str, Any]) -> bool:
        if stmt.get("kind") != "ForCore":
            return False
        target_plan_any = stmt.get("target_plan")
        target_plan = target_plan_any if isinstance(target_plan_any, dict) else None
        if target_plan is None or target_plan.get("kind") != "TupleTarget":
            return False
        if bool(target_plan.get("direct_unpack", False)):
            return False

        elems_any = target_plan.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        if len(elems) == 0:
            return False
        names: list[str] = []
        target_types: list[str] = []
        for elem_any in elems:
            elem = elem_any if isinstance(elem_any, dict) else {}
            if elem.get("kind") != "NameTarget":
                return False
            name = elem.get("id")
            if not isinstance(name, str) or name == "":
                return False
            t = _normalize_type_name(elem.get("target_type"))
            if not _is_known_scalar(t):
                return False
            names.append(name)
            target_types.append(t)

        item_t = _iter_item_type(stmt)
        item_elems = _tuple_elem_types(item_t)
        if len(item_elems) == 0:
            return False
        if len(item_elems) != len(target_types):
            return False
        i = 0
        while i < len(item_elems):
            if _normalize_type_name(item_elems[i]) != _normalize_type_name(target_types[i]):
                return False
            i += 1

        target_plan["direct_unpack"] = True
        target_plan["direct_unpack_names"] = list(names)
        target_plan["direct_unpack_types"] = list(target_types)
        return True

    def _visit(self, node: Any) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0
        if self._try_rewrite_forcore(node):
            changed += 1
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> CppOptResult:
        _ = context
        changed = self._visit(cpp_ir)
        return CppOptResult(changed=changed > 0, change_count=changed)

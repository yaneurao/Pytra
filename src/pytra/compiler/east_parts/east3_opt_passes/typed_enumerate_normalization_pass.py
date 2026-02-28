"""Normalize `enumerate(list[T])` runtime loops into typed iterable metadata."""

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


def _split_generic_types(text: str) -> list[str]:
    out: list[str] = []
    part = ""
    depth = 0
    for ch in text:
        if ch == "<" or ch == "[":
            depth += 1
            part += ch
            continue
        if ch == ">" or ch == "]":
            if depth > 0:
                depth -= 1
            part += ch
            continue
        if ch == "," and depth == 0:
            out.append(part.strip())
            part = ""
            continue
        part += ch
    last = part.strip()
    if last != "":
        out.append(last)
    return out


def _list_element_type(type_name: str) -> str:
    type_norm = _normalize_type_name(type_name)
    if not type_norm.startswith("list[") or not type_norm.endswith("]"):
        return "unknown"
    inner = type_norm[5:-1].strip()
    if inner == "":
        return "unknown"
    return inner


def _tuple_element_types(type_name: str) -> list[str]:
    type_norm = _normalize_type_name(type_name)
    if not type_norm.startswith("tuple[") or not type_norm.endswith("]"):
        return []
    inner = type_norm[6:-1].strip()
    if inner == "":
        return []
    return _split_generic_types(inner)


def _enumerate_item_type_from_expr(iter_expr: dict[str, Any]) -> str:
    iter_elem_hint = _normalize_type_name(iter_expr.get("iter_element_type"))
    if iter_elem_hint.startswith("tuple[") and iter_elem_hint.endswith("]"):
        elems = _tuple_element_types(iter_elem_hint)
        if len(elems) == 2 and elems[0] in {"int", "int64"} and elems[1] != "unknown":
            return f"tuple[int64, {elems[1]}]"

    iter_t = _normalize_type_name(iter_expr.get("resolved_type"))
    if iter_t.startswith("list[") and iter_t.endswith("]"):
        list_inner = _list_element_type(iter_t)
        tuple_parts = _tuple_element_types(list_inner)
        if len(tuple_parts) == 2 and tuple_parts[0] in {"int", "int64"} and tuple_parts[1] != "unknown":
            return f"tuple[int64, {tuple_parts[1]}]"

    args_obj = iter_expr.get("args")
    args = args_obj if isinstance(args_obj, list) else []
    if len(args) < 1:
        return "unknown"
    src0 = args[0]
    if not isinstance(src0, dict):
        return "unknown"
    src_elem_t = _list_element_type(_normalize_type_name(src0.get("resolved_type")))
    if src_elem_t == "unknown":
        return "unknown"
    return f"tuple[int64, {src_elem_t}]"


def _is_enumerate_runtime_call(iter_expr: dict[str, Any]) -> bool:
    if iter_expr.get("kind") != "Call":
        return False
    runtime_call = _normalize_type_name(iter_expr.get("runtime_call"))
    if runtime_call == "py_enumerate":
        return True
    if _normalize_type_name(iter_expr.get("lowered_kind")) != "BuiltinCall":
        return False
    return _normalize_type_name(iter_expr.get("builtin_name")) == "enumerate"


class TypedEnumerateNormalizationPass(East3OptimizerPass):
    """Populate typed iterable metadata for `enumerate(list[T])` loops."""

    name = "TypedEnumerateNormalizationPass"
    min_opt_level = 1

    def _rewrite_target_plan(self, target_plan: dict[str, Any], item_type: str) -> int:
        changed = 0
        tuple_items = _tuple_element_types(item_type)
        if len(tuple_items) != 2:
            return changed

        plan_kind = _normalize_type_name(target_plan.get("kind"))
        if plan_kind == "NameTarget":
            current = _normalize_type_name(target_plan.get("target_type"))
            if current == "unknown":
                target_plan["target_type"] = item_type
                changed += 1
            return changed

        if plan_kind != "TupleTarget":
            return changed
        elements_obj = target_plan.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        if len(elements) != 2:
            return changed
        current_tuple = _normalize_type_name(target_plan.get("target_type"))
        if current_tuple == "unknown":
            target_plan["target_type"] = item_type
            changed += 1
        for idx in [0, 1]:
            elem = elements[idx]
            if not isinstance(elem, dict):
                continue
            if _normalize_type_name(elem.get("kind")) != "NameTarget":
                continue
            current_t = _normalize_type_name(elem.get("target_type"))
            desired_t = tuple_items[idx]
            if current_t == "unknown" and desired_t != "unknown":
                elem["target_type"] = desired_t
                changed += 1
        return changed

    def _try_rewrite_forcore(self, stmt: dict[str, Any]) -> int:
        if _normalize_type_name(stmt.get("kind")) != "ForCore":
            return 0

        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or _normalize_type_name(iter_plan.get("kind")) != "RuntimeIterForPlan":
            return 0

        iter_expr_obj = iter_plan.get("iter_expr")
        iter_expr = iter_expr_obj if isinstance(iter_expr_obj, dict) else None
        if iter_expr is None or not _is_enumerate_runtime_call(iter_expr):
            return 0

        item_type = _enumerate_item_type_from_expr(iter_expr)
        tuple_types = _tuple_element_types(item_type)
        if len(tuple_types) != 2:
            return 0
        if tuple_types[1] == "unknown":
            return 0

        changed = 0
        desired_resolved = f"list[{item_type}]"
        if _normalize_type_name(iter_expr.get("resolved_type")) != desired_resolved:
            iter_expr["resolved_type"] = desired_resolved
            changed += 1
        if _normalize_type_name(iter_expr.get("iterable_trait")) != "yes":
            iter_expr["iterable_trait"] = "yes"
            changed += 1
        if _normalize_type_name(iter_expr.get("iter_protocol")) != "static_range":
            iter_expr["iter_protocol"] = "static_range"
            changed += 1
        if _normalize_type_name(iter_expr.get("iter_element_type")) != item_type:
            iter_expr["iter_element_type"] = item_type
            changed += 1
        if _normalize_type_name(iter_plan.get("iter_item_type")) != item_type:
            iter_plan["iter_item_type"] = item_type
            changed += 1

        target_plan_obj = stmt.get("target_plan")
        target_plan = target_plan_obj if isinstance(target_plan_obj, dict) else None
        if target_plan is not None:
            changed += self._rewrite_target_plan(target_plan, item_type)
        return changed

    def _visit(self, node: Any) -> int:
        changed = 0
        if isinstance(node, list):
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0
        changed += self._try_rewrite_forcore(node)
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

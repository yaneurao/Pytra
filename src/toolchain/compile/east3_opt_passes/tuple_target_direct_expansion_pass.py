"""Annotate flat tuple targets for direct unpack expansion in emitters."""

from __future__ import annotations

from typing import Any

from toolchain.compile.east3_optimizer import East3OptimizerPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import PassResult

_CPP_STRUCT_BIND_ASSIGN_HINT_KEY = "cpp_struct_bind_unpack_v1"


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


def _tuple_element_types(type_name: str) -> list[str]:
    t = _normalize_type_name(type_name)
    if not t.startswith("tuple[") or not t.endswith("]"):
        return []
    inner = t[6:-1].strip()
    if inner == "":
        return []
    return _split_generic_types(inner)


def _is_any_like_type(type_name: str) -> bool:
    t = _normalize_type_name(type_name)
    return t in {"", "unknown", "Any", "object"}


def _iter_item_type(iter_plan: dict[str, Any], iter_expr: dict[str, Any]) -> str:
    hint0 = _normalize_type_name(iter_plan.get("iter_item_type"))
    if hint0.startswith("tuple[") and hint0.endswith("]"):
        return hint0
    hint1 = _normalize_type_name(iter_expr.get("iter_element_type"))
    if hint1.startswith("tuple[") and hint1.endswith("]"):
        return hint1
    expr_t = _normalize_type_name(iter_expr.get("resolved_type"))
    if expr_t.startswith("list[") and expr_t.endswith("]"):
        inner = expr_t[5:-1].strip()
        if inner.startswith("tuple[") and inner.endswith("]"):
            return inner
    return ""


class TupleTargetDirectExpansionPass(East3OptimizerPass):
    """Mark flat tuple targets for direct unpack expansion (`[a,b]` in loop header)."""

    name = "TupleTargetDirectExpansionPass"
    min_opt_level = 1

    def _set_assign_hint(self, stmt: dict[str, Any], hint: dict[str, Any] | None) -> int:
        current_any = stmt.get(_CPP_STRUCT_BIND_ASSIGN_HINT_KEY)
        current = current_any if isinstance(current_any, dict) else None
        if hint is None:
            if _CPP_STRUCT_BIND_ASSIGN_HINT_KEY in stmt:
                stmt.pop(_CPP_STRUCT_BIND_ASSIGN_HINT_KEY, None)
                return 1
            return 0
        if current == hint:
            return 0
        stmt[_CPP_STRUCT_BIND_ASSIGN_HINT_KEY] = hint
        return 1

    def _tuple_type_from_assign_value(self, value_node: dict[str, Any]) -> str:
        value_t = _normalize_type_name(value_node.get("resolved_type"))
        if value_t.startswith("tuple[") and value_t.endswith("]"):
            return value_t
        # optional/union tuple は fail-closed（marker 非付与）
        return ""

    def _try_rewrite_assign(self, stmt: dict[str, Any]) -> int:
        if _normalize_type_name(stmt.get("kind")) != "Assign":
            return 0
        target_obj = stmt.get("target")
        target = target_obj if isinstance(target_obj, dict) else None
        if target is None or _normalize_type_name(target.get("kind")) != "Tuple":
            return self._set_assign_hint(stmt, None)
        elems_obj = target.get("elements")
        elems = elems_obj if isinstance(elems_obj, list) else []
        if len(elems) == 0:
            return self._set_assign_hint(stmt, None)

        names: list[str] = []
        for elem_obj in elems:
            elem = elem_obj if isinstance(elem_obj, dict) else None
            if elem is None or _normalize_type_name(elem.get("kind")) != "Name":
                return self._set_assign_hint(stmt, None)
            nm = _normalize_type_name(elem.get("id"))
            if nm == "unknown":
                return self._set_assign_hint(stmt, None)
            names.append(nm)
        if len(set(names)) != len(names):
            return self._set_assign_hint(stmt, None)

        value_obj = stmt.get("value")
        value = value_obj if isinstance(value_obj, dict) else None
        if value is None:
            return self._set_assign_hint(stmt, None)
        tuple_t = self._tuple_type_from_assign_value(value)
        if tuple_t == "":
            return self._set_assign_hint(stmt, None)
        elem_types = _tuple_element_types(tuple_t)
        if len(elem_types) != len(names):
            return self._set_assign_hint(stmt, None)
        if any(_is_any_like_type(t) for t in elem_types):
            return self._set_assign_hint(stmt, None)

        hint = {
            "version": "1",
            "names": names,
            "types": elem_types,
        }
        return self._set_assign_hint(stmt, hint)

    def _try_rewrite_forcore(self, stmt: dict[str, Any]) -> int:
        if _normalize_type_name(stmt.get("kind")) != "ForCore":
            return 0
        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or _normalize_type_name(iter_plan.get("kind")) != "RuntimeIterForPlan":
            return 0
        target_plan_obj = stmt.get("target_plan")
        target_plan = target_plan_obj if isinstance(target_plan_obj, dict) else None
        if target_plan is None or _normalize_type_name(target_plan.get("kind")) != "TupleTarget":
            return 0
        elements_obj = target_plan.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        if len(elements) == 0:
            return 0

        names: list[str] = []
        target_types: list[str] = []
        for elem_obj in elements:
            elem = elem_obj if isinstance(elem_obj, dict) else None
            if elem is None or _normalize_type_name(elem.get("kind")) != "NameTarget":
                return 0
            nm = _normalize_type_name(elem.get("id"))
            if nm == "unknown":
                return 0
            names.append(nm)
            target_types.append(_normalize_type_name(elem.get("target_type")))

        iter_expr_obj = iter_plan.get("iter_expr")
        iter_expr = iter_expr_obj if isinstance(iter_expr_obj, dict) else None
        if iter_expr is None:
            return 0
        item_type = _iter_item_type(iter_plan, iter_expr)
        item_elems = _tuple_element_types(item_type)
        if len(item_elems) != len(elements):
            return 0
        if any(_normalize_type_name(t) in {"", "unknown"} for t in item_elems):
            return 0

        changed = 0
        if _normalize_type_name(iter_plan.get("iter_item_type")) != item_type:
            iter_plan["iter_item_type"] = item_type
            changed += 1
        if _normalize_type_name(target_plan.get("target_type")) == "unknown":
            target_plan["target_type"] = item_type
            changed += 1
        for idx, elem_obj in enumerate(elements):
            elem = elem_obj if isinstance(elem_obj, dict) else None
            if elem is None:
                continue
            current_t = _normalize_type_name(elem.get("target_type"))
            if current_t == "unknown":
                elem["target_type"] = item_elems[idx]
                changed += 1

        direct_now = bool(target_plan.get("direct_unpack", False))
        if not direct_now:
            target_plan["direct_unpack"] = True
            changed += 1
        if target_plan.get("direct_unpack_names") != names:
            target_plan["direct_unpack_names"] = names
            changed += 1
        if target_plan.get("direct_unpack_types") != item_elems:
            target_plan["direct_unpack_types"] = item_elems
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
        changed += self._try_rewrite_forcore(node)
        changed += self._try_rewrite_assign(node)
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

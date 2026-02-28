"""Hoist loop-invariant numeric cast calls into ForCore preheaders."""

from __future__ import annotations

import copy

from pytra.std.typing import Any

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


_DYNAMIC_NAME_CALLS = {"locals", "globals", "vars", "eval", "exec"}
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
_INT_LIKE_TYPES = {
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "int",
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


def _is_int_like_type(value: Any) -> bool:
    return _normalize_type_name(value) in _INT_LIKE_TYPES


def _contains_dynamic_name_access(node: Any) -> bool:
    if isinstance(node, list):
        for item in node:
            if _contains_dynamic_name_access(item):
                return True
        return False
    if not isinstance(node, dict):
        return False
    if node.get("kind") == "Call":
        func_obj = node.get("func")
        if isinstance(func_obj, dict) and func_obj.get("kind") == "Name":
            fn_name = func_obj.get("id")
            if isinstance(fn_name, str) and fn_name in _DYNAMIC_NAME_CALLS:
                return True
    for value in node.values():
        if _contains_dynamic_name_access(value):
            return True
    return False


def _collect_target_plan_names(target_plan: Any, out: set[str]) -> None:
    if not isinstance(target_plan, dict):
        return
    kind = target_plan.get("kind")
    if kind == "NameTarget":
        ident = target_plan.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
        return
    if kind == "TupleTarget":
        elements_obj = target_plan.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        for elem in elements:
            _collect_target_plan_names(elem, out)


def _collect_target_names(target_node: Any, out: set[str]) -> None:
    if not isinstance(target_node, dict):
        return
    kind = target_node.get("kind")
    if kind == "Name":
        ident = target_node.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
        return
    if kind == "Tuple":
        elements_obj = target_node.get("elements")
        elements = elements_obj if isinstance(elements_obj, list) else []
        for elem in elements:
            _collect_target_names(elem, out)


def _collect_assigned_names(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_assigned_names(item, out)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        _collect_target_names(node.get("target"), out)
    elif kind in {"For", "ForRange"}:
        _collect_target_names(node.get("target"), out)
    elif kind == "ForCore":
        _collect_target_plan_names(node.get("target_plan"), out)
    for value in node.values():
        _collect_assigned_names(value, out)


def _collect_name_ids(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_name_ids(item, out)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    if kind == "Name":
        ident = node.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
    if kind == "NameTarget":
        ident = node.get("id")
        if isinstance(ident, str) and ident != "":
            out.add(ident)
    for value in node.values():
        _collect_name_ids(value, out)


def _is_invariant_expr(expr: Any, *, loop_vars: set[str], mutated_names: set[str]) -> bool:
    if not isinstance(expr, dict):
        return False
    kind = expr.get("kind")
    if kind == "Constant":
        value_obj = expr.get("value")
        return isinstance(value_obj, bool) or isinstance(value_obj, int) or isinstance(value_obj, float)
    if kind == "Name":
        ident = expr.get("id")
        if not isinstance(ident, str) or ident == "":
            return False
        if ident in loop_vars:
            return False
        return ident not in mutated_names
    if kind == "UnaryOp":
        op = expr.get("op")
        if op not in {"UAdd", "USub"}:
            return False
        return _is_invariant_expr(expr.get("operand"), loop_vars=loop_vars, mutated_names=mutated_names)
    if kind == "BinOp":
        op = expr.get("op")
        if op not in {"Add", "Sub", "Mult", "Div"}:
            return False
        left = expr.get("left")
        right = expr.get("right")
        return _is_invariant_expr(left, loop_vars=loop_vars, mutated_names=mutated_names) and _is_invariant_expr(
            right,
            loop_vars=loop_vars,
            mutated_names=mutated_names,
        )
    return False


def _expr_key(expr: dict[str, Any]) -> str:
    repr_obj = expr.get("repr")
    if isinstance(repr_obj, str):
        text = repr_obj.strip()
        if text != "":
            return text
    return str(expr)


def _is_static_cast_call(node: dict[str, Any]) -> bool:
    if node.get("kind") != "Call":
        return False
    if node.get("lowered_kind") != "BuiltinCall":
        return False
    return _normalize_type_name(node.get("runtime_call")) == "static_cast"


class LoopInvariantCastHoistPass(East3OptimizerPass):
    """Hoist invariant `static_cast` calls used inside static ForCore loops."""

    name = "LoopInvariantCastHoistPass"
    min_opt_level = 1

    def __init__(self) -> None:
        self._tmp_seq = 0

    def _next_tmp_name(self, used_names: set[str]) -> str:
        while True:
            self._tmp_seq += 1
            name = "__hoisted_cast_" + str(self._tmp_seq)
            if name not in used_names:
                used_names.add(name)
                return name

    def _make_hoisted_annassign(self, name: str, value_expr: dict[str, Any], value_type: str) -> dict[str, Any]:
        return {
            "kind": "AnnAssign",
            "target": {
                "kind": "Name",
                "id": name,
                "resolved_type": value_type,
                "borrow_kind": "value",
                "casts": [],
                "repr": name,
            },
            "annotation": value_type,
            "declare": True,
            "declare_init": True,
            "decl_type": value_type,
            "value": copy.deepcopy(value_expr),
        }

    def _build_name_expr(self, name: str, value_type: str) -> dict[str, Any]:
        return {
            "kind": "Name",
            "id": name,
            "resolved_type": value_type,
            "borrow_kind": "readonly_ref",
            "casts": [],
            "repr": name,
        }

    def _make_static_cast_call(self, value_expr: dict[str, Any], target_type: str) -> dict[str, Any]:
        cast_t = _canonical_numeric_type(target_type)
        builtin_name = "float"
        if cast_t.startswith("int") or cast_t.startswith("uint"):
            builtin_name = "int"
        return {
            "kind": "Call",
            "resolved_type": cast_t,
            "borrow_kind": "value",
            "casts": [],
            "func": {"kind": "Name", "id": builtin_name, "resolved_type": "unknown", "borrow_kind": "value", "casts": []},
            "args": [copy.deepcopy(value_expr)],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "builtin_name": builtin_name,
            "runtime_call": "static_cast",
        }

    def _is_hoist_candidate(
        self,
        node: dict[str, Any],
        *,
        loop_vars: set[str],
        mutated_names: set[str],
    ) -> bool:
        if not _is_static_cast_call(node):
            return False
        cast_t = _canonical_numeric_type(node.get("resolved_type"))
        if cast_t == "":
            return False
        args_obj = node.get("args")
        args = args_obj if isinstance(args_obj, list) else []
        if len(args) != 1:
            return False
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return False
        return _is_invariant_expr(arg0, loop_vars=loop_vars, mutated_names=mutated_names)

    def _rewrite_expr(
        self,
        node: Any,
        *,
        loop_vars: set[str],
        mutated_names: set[str],
        used_names: set[str],
        hoist_map: dict[str, str],
        hoist_stmts: list[dict[str, Any]],
    ) -> tuple[Any, int]:
        if isinstance(node, list):
            out = node
            changed = 0
            for i, item in enumerate(node):
                new_item, delta = self._rewrite_expr(
                    item,
                    loop_vars=loop_vars,
                    mutated_names=mutated_names,
                    used_names=used_names,
                    hoist_map=hoist_map,
                    hoist_stmts=hoist_stmts,
                )
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
            new_value, delta = self._rewrite_expr(
                value,
                loop_vars=loop_vars,
                mutated_names=mutated_names,
                used_names=used_names,
                hoist_map=hoist_map,
                hoist_stmts=hoist_stmts,
            )
            if new_value is not value:
                out[key] = new_value
            changed += delta

        if out.get("kind") == "BinOp":
            cast_rules = out.get("casts")
            cast_list = cast_rules if isinstance(cast_rules, list) else []
            if len(cast_list) > 0:
                right_node = out.get("right")
                right_expr = right_node if isinstance(right_node, dict) else None
                if right_expr is not None and _is_invariant_expr(right_expr, loop_vars=loop_vars, mutated_names=mutated_names):
                    next_casts: list[Any] = []
                    local_change = 0
                    for cast_rule_obj in cast_list:
                        cast_rule = cast_rule_obj if isinstance(cast_rule_obj, dict) else None
                        if cast_rule is None:
                            next_casts.append(cast_rule_obj)
                            continue
                        on = _normalize_type_name(cast_rule.get("on"))
                        to_t = _canonical_numeric_type(cast_rule.get("to"))
                        from_t_raw = cast_rule.get("from")
                        if on != "right" or to_t == "":
                            next_casts.append(cast_rule_obj)
                            continue
                        if not _is_int_like_type(from_t_raw):
                            next_casts.append(cast_rule_obj)
                            continue
                        key = "__binop_right_cast__:" + to_t + ":" + _expr_key(right_expr)
                        tmp_name = hoist_map.get(key)
                        if tmp_name is None:
                            tmp_name = self._next_tmp_name(used_names)
                            hoist_map[key] = tmp_name
                            hoist_expr = self._make_static_cast_call(right_expr, to_t)
                            hoist_stmts.append(self._make_hoisted_annassign(tmp_name, hoist_expr, to_t))
                        out["right"] = self._build_name_expr(tmp_name, to_t)
                        local_change += 1
                    if local_change > 0:
                        out["casts"] = next_casts
                        changed += local_change

        if not self._is_hoist_candidate(out, loop_vars=loop_vars, mutated_names=mutated_names):
            return out, changed

        key = _expr_key(out)
        cast_t = _canonical_numeric_type(out.get("resolved_type"))
        tmp_name = hoist_map.get(key)
        if tmp_name is None:
            tmp_name = self._next_tmp_name(used_names)
            hoist_map[key] = tmp_name
            hoist_stmts.append(self._make_hoisted_annassign(tmp_name, out, cast_t))
        return self._build_name_expr(tmp_name, cast_t), changed + 1

    def _try_hoist_forcore(self, stmt_list: list[Any], index: int) -> int:
        stmt_obj = stmt_list[index]
        stmt = stmt_obj if isinstance(stmt_obj, dict) else None
        if stmt is None or stmt.get("kind") != "ForCore":
            return 0

        iter_plan_obj = stmt.get("iter_plan")
        iter_plan = iter_plan_obj if isinstance(iter_plan_obj, dict) else None
        if iter_plan is None or iter_plan.get("kind") != "StaticRangeForPlan":
            return 0

        body_obj = stmt.get("body")
        body = body_obj if isinstance(body_obj, list) else None
        if body is None or len(body) == 0:
            return 0
        if _contains_dynamic_name_access(body):
            return 0

        loop_vars: set[str] = set()
        _collect_target_plan_names(stmt.get("target_plan"), loop_vars)
        if len(loop_vars) == 0:
            return 0

        mutated_names: set[str] = set()
        _collect_assigned_names(body, mutated_names)
        for loop_var in loop_vars:
            if loop_var in mutated_names:
                mutated_names.remove(loop_var)

        used_names: set[str] = set()
        _collect_name_ids(stmt_list, used_names)

        hoist_map: dict[str, str] = {}
        hoist_stmts: list[dict[str, Any]] = []
        _, change_count = self._rewrite_expr(
            body,
            loop_vars=loop_vars,
            mutated_names=mutated_names,
            used_names=used_names,
            hoist_map=hoist_map,
            hoist_stmts=hoist_stmts,
        )
        if change_count <= 0 or len(hoist_stmts) == 0:
            return 0
        insert_pos = index
        for hoisted in hoist_stmts:
            stmt_list.insert(insert_pos, hoisted)
            insert_pos += 1
        return change_count

    def _visit(self, node: Any) -> int:
        if isinstance(node, list):
            changed = 0
            i = 0
            while i < len(node):
                item = node[i]
                if isinstance(item, dict):
                    delta = self._try_hoist_forcore(node, i)
                    if delta > 0:
                        changed += delta
                        i += 1
                        continue
                i += 1
            for item in node:
                changed += self._visit(item)
            return changed
        if not isinstance(node, dict):
            return 0
        changed = 0
        for value in node.values():
            changed += self._visit(value)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        change_count = self._visit(east3_doc)
        return PassResult(changed=change_count > 0, change_count=change_count)

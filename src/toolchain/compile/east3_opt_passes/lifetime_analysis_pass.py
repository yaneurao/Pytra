"""Function-local lifetime analysis for EAST3 (`CFG + def-use + liveness`)."""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from toolchain.compile.east3_optimizer import East3OptimizerPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import PassResult


_DYNAMIC_NAME_CALLS = {"locals", "globals", "vars", "eval", "exec"}
_LOOP_KINDS = {"For", "ForRange", "ForCore", "While"}


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _ensure_meta(node: dict[str, Any]) -> dict[str, Any]:
    meta_any = node.get("meta")
    if isinstance(meta_any, dict):
        return meta_any
    meta: dict[str, Any] = {}
    node["meta"] = meta
    return meta


def _set_meta_value(node: dict[str, Any], key: str, value: Any) -> bool:
    meta = _ensure_meta(node)
    if meta.get(key) == value:
        return False
    meta[key] = value
    return True


def _iter_stmt_list(value: Any) -> list[dict[str, Any]]:
    src = value if isinstance(value, list) else []
    out: list[dict[str, Any]] = []
    for item in src:
        if isinstance(item, dict):
            out.append(item)
    return out


def _collect_target_defs(node: Any, out: set[str]) -> None:
    if not isinstance(node, dict):
        return
    kind = _safe_name(node.get("kind"))
    if kind == "Name":
        ident = _safe_name(node.get("id"))
        if ident != "":
            out.add(ident)
        return
    if kind in {"Tuple", "List"}:
        elements_any = node.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        for elem in elements:
            _collect_target_defs(elem, out)


def _collect_target_plan_defs(node: Any, out: set[str]) -> None:
    if not isinstance(node, dict):
        return
    kind = _safe_name(node.get("kind"))
    if kind == "NameTarget":
        ident = _safe_name(node.get("id"))
        if ident != "":
            out.add(ident)
        return
    if kind == "TupleTarget":
        elements_any = node.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        for elem in elements:
            _collect_target_plan_defs(elem, out)


def _collect_name_uses(node: Any, out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_name_uses(item, out)
        return
    if not isinstance(node, dict):
        return
    kind = _safe_name(node.get("kind"))
    if kind == "Name":
        ident = _safe_name(node.get("id"))
        if ident != "":
            out.add(ident)
        return
    for value in node.values():
        _collect_name_uses(value, out)


def _has_dynamic_name_access(node: Any) -> bool:
    if isinstance(node, list):
        for item in node:
            if _has_dynamic_name_access(item):
                return True
        return False
    if not isinstance(node, dict):
        return False
    kind = _safe_name(node.get("kind"))
    if kind == "Call":
        func_any = node.get("func")
        if isinstance(func_any, dict) and _safe_name(func_any.get("kind")) == "Name":
            fn_name = _safe_name(func_any.get("id"))
            if fn_name in _DYNAMIC_NAME_CALLS:
                return True
    for value in node.values():
        if _has_dynamic_name_access(value):
            return True
    return False


def _stmt_defs_uses(stmt: dict[str, Any]) -> tuple[set[str], set[str], bool]:
    defs: set[str] = set()
    uses: set[str] = set()
    kind = _safe_name(stmt.get("kind"))

    if kind == "Assign":
        _collect_target_defs(stmt.get("target"), defs)
        _collect_name_uses(stmt.get("value"), uses)
    elif kind == "AnnAssign":
        _collect_target_defs(stmt.get("target"), defs)
        _collect_name_uses(stmt.get("value"), uses)
    elif kind == "AugAssign":
        _collect_target_defs(stmt.get("target"), defs)
        _collect_name_uses(stmt.get("target"), uses)
        _collect_name_uses(stmt.get("value"), uses)
    elif kind == "Expr":
        _collect_name_uses(stmt.get("value"), uses)
    elif kind in {"Return", "Yield"}:
        _collect_name_uses(stmt.get("value"), uses)
    elif kind == "If":
        _collect_name_uses(stmt.get("test"), uses)
    elif kind == "While":
        _collect_name_uses(stmt.get("test"), uses)
    elif kind == "For":
        _collect_target_defs(stmt.get("target"), defs)
        _collect_name_uses(stmt.get("iter"), uses)
    elif kind == "ForRange":
        _collect_target_defs(stmt.get("target"), defs)
        _collect_name_uses(stmt.get("start"), uses)
        _collect_name_uses(stmt.get("stop"), uses)
        _collect_name_uses(stmt.get("step"), uses)
    elif kind == "ForCore":
        _collect_target_plan_defs(stmt.get("target_plan"), defs)
        _collect_name_uses(stmt.get("iter_plan"), uses)
        _collect_name_uses(stmt.get("iter"), uses)
    elif kind == "FunctionDef":
        name = _safe_name(stmt.get("name"))
        if name != "":
            defs.add(name)
    elif kind == "ClassDef":
        name = _safe_name(stmt.get("name"))
        if name != "":
            defs.add(name)
    elif kind == "With":
        _collect_name_uses(stmt.get("items"), uses)
    elif kind == "Try":
        _collect_name_uses(stmt.get("handlers"), uses)
    else:
        _collect_name_uses(stmt, uses)

    return defs, uses, _has_dynamic_name_access(stmt)


def _function_args(fn_node: dict[str, Any]) -> list[str]:
    out: list[str] = []
    arg_order_any = fn_node.get("arg_order")
    if isinstance(arg_order_any, list):
        for item in arg_order_any:
            name = _safe_name(item)
            if name != "":
                out.append(name)
        return out
    args_any = fn_node.get("args")
    args = args_any if isinstance(args_any, list) else []
    for arg_any in args:
        if not isinstance(arg_any, dict):
            continue
        name = _safe_name(arg_any.get("arg"))
        if name == "":
            name = _safe_name(arg_any.get("id"))
        if name != "":
            out.append(name)
    return out


@dataclass
class _CfgNode:
    node_id: str
    stmt: dict[str, Any]
    kind: str
    defs: set[str]
    uses: set[str]
    succ: set[str]


class _CfgBuilder:
    def __init__(self) -> None:
        self._counter = 0
        self.nodes: dict[str, _CfgNode] = {}
        self.order: list[str] = []
        self.dynamic_name_access = False

    def _new_node(self, stmt: dict[str, Any]) -> _CfgNode:
        node_id = "n" + str(self._counter)
        self._counter += 1
        defs, uses, has_dyn = _stmt_defs_uses(stmt)
        if has_dyn:
            self.dynamic_name_access = True
        node = _CfgNode(
            node_id=node_id,
            stmt=stmt,
            kind=_safe_name(stmt.get("kind")),
            defs=set(defs),
            uses=set(uses),
            succ=set(),
        )
        self.nodes[node_id] = node
        self.order.append(node_id)
        return node

    def build_block(
        self,
        stmts: list[dict[str, Any]],
        next_node: str,
        loop_ctx: tuple[str, str] | None,
    ) -> str:
        entry = next_node
        for stmt in reversed(stmts):
            entry = self.build_stmt(stmt, entry, loop_ctx)
        return entry

    def build_stmt(
        self,
        stmt: dict[str, Any],
        next_node: str,
        loop_ctx: tuple[str, str] | None,
    ) -> str:
        node = self._new_node(stmt)
        kind = node.kind

        if kind in {"Return", "Yield"}:
            return node.node_id

        if kind == "Break":
            if loop_ctx is not None and loop_ctx[1] != "":
                node.succ.add(loop_ctx[1])
            elif next_node != "":
                node.succ.add(next_node)
            return node.node_id

        if kind == "Continue":
            if loop_ctx is not None and loop_ctx[0] != "":
                node.succ.add(loop_ctx[0])
            elif next_node != "":
                node.succ.add(next_node)
            return node.node_id

        if kind == "If":
            body = _iter_stmt_list(stmt.get("body"))
            orelse = _iter_stmt_list(stmt.get("orelse"))
            body_entry = self.build_block(body, next_node, loop_ctx)
            orelse_entry = self.build_block(orelse, next_node, loop_ctx)
            if body_entry != "":
                node.succ.add(body_entry)
            elif next_node != "":
                node.succ.add(next_node)
            if orelse_entry != "":
                node.succ.add(orelse_entry)
            elif next_node != "":
                node.succ.add(next_node)
            return node.node_id

        if kind in _LOOP_KINDS:
            body = _iter_stmt_list(stmt.get("body"))
            orelse = _iter_stmt_list(stmt.get("orelse"))
            orelse_entry = self.build_block(orelse, next_node, loop_ctx)
            exit_target = orelse_entry if orelse_entry != "" else next_node
            body_entry = self.build_block(body, node.node_id, (node.node_id, exit_target))
            if body_entry != "":
                node.succ.add(body_entry)
            else:
                node.succ.add(node.node_id)
            if exit_target != "":
                node.succ.add(exit_target)
            return node.node_id

        if next_node != "":
            node.succ.add(next_node)
        return node.node_id


def _sorted_str_list(values: set[str]) -> list[str]:
    return sorted([value for value in values if value != ""])


def _merge_set_map(dst: dict[str, set[str]], key: str, values: set[str]) -> None:
    if key not in dst:
        dst[key] = set()
    dst[key].update(values)


def _compute_liveness(nodes: dict[str, _CfgNode], order: list[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    live_in: dict[str, set[str]] = {node_id: set() for node_id in order}
    live_out: dict[str, set[str]] = {node_id: set() for node_id in order}
    changed = True
    while changed:
        changed = False
        for node_id in reversed(order):
            node = nodes[node_id]
            out_set: set[str] = set()
            for succ in node.succ:
                if succ in live_in:
                    out_set.update(live_in[succ])
            in_set = set(node.uses)
            in_set.update(out_set.difference(node.defs))
            if out_set != live_out[node_id] or in_set != live_in[node_id]:
                live_out[node_id] = out_set
                live_in[node_id] = in_set
                changed = True
    return live_in, live_out


def _non_escape_arg_flags(fn_node: dict[str, Any], context: PassContext) -> list[bool]:
    arg_names = _function_args(fn_node)
    defaults = [bool(context.non_escape_policy.get("return_escape_by_default", True))] * len(arg_names)
    meta_any = fn_node.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    summary_any = meta.get("escape_summary")
    summary = summary_any if isinstance(summary_any, dict) else {}
    flags_any = summary.get("arg_escape")
    flags = flags_any if isinstance(flags_any, list) else []
    if len(flags) == 0:
        return defaults
    out = list(defaults)
    for i, flag_any in enumerate(flags):
        if i >= len(out):
            break
        if isinstance(flag_any, bool):
            out[i] = bool(flag_any)
    return out


class LifetimeAnalysisPass(East3OptimizerPass):
    """Attach deterministic function-local lifetime metadata (`east3_lifetime_v1`)."""

    name = "LifetimeAnalysisPass"
    min_opt_level = 1

    def _analyze_function(self, fn_node: dict[str, Any], context: PassContext) -> bool:
        body = _iter_stmt_list(fn_node.get("body"))
        builder = _CfgBuilder()
        entry_id = builder.build_block(body, "", None)
        order = list(builder.order)
        nodes = builder.nodes

        defs_index: dict[str, set[str]] = {}
        uses_index: dict[str, set[str]] = {}
        return_use_index: dict[str, set[str]] = {}

        for node_id in order:
            node = nodes[node_id]
            for name in node.defs:
                _merge_set_map(defs_index, name, {node_id})
            for name in node.uses:
                _merge_set_map(uses_index, name, {node_id})
            if node.kind in {"Return", "Yield"}:
                for name in node.uses:
                    _merge_set_map(return_use_index, name, {node_id})

        live_in, live_out = _compute_liveness(nodes, order)
        args = _function_args(fn_node)
        arg_escape = _non_escape_arg_flags(fn_node, context)

        all_vars: set[str] = set(args)
        all_vars.update(defs_index.keys())
        all_vars.update(uses_index.keys())

        variables: dict[str, dict[str, Any]] = {}
        fail_closed = bool(builder.dynamic_name_access)
        for name in sorted(all_vars):
            def_nodes = sorted(list(defs_index.get(name, set())))
            use_nodes = sorted(list(uses_index.get(name, set())))
            live_in_nodes = [node_id for node_id in order if name in live_in.get(node_id, set())]
            live_out_nodes = [node_id for node_id in order if name in live_out.get(node_id, set())]
            last_use_nodes: list[str] = []
            for node_id in use_nodes:
                if name not in live_out.get(node_id, set()):
                    last_use_nodes.append(node_id)
            lifetime_class = "local_non_escape_candidate"
            if fail_closed:
                lifetime_class = "escape_or_unknown"
            if name in return_use_index:
                lifetime_class = "escape_or_unknown"
            if name in args:
                arg_index = args.index(name)
                if arg_index < len(arg_escape) and bool(arg_escape[arg_index]):
                    lifetime_class = "escape_or_unknown"
            variables[name] = {
                "def_nodes": def_nodes,
                "use_nodes": use_nodes,
                "live_in_nodes": live_in_nodes,
                "live_out_nodes": live_out_nodes,
                "last_use_nodes": sorted(last_use_nodes),
                "lifetime_class": lifetime_class,
            }

        changed = False
        for node_id in order:
            node = nodes[node_id]
            last_use_vars = [name for name in sorted(node.uses) if name not in live_out.get(node_id, set())]
            changed |= _set_meta_value(node.stmt, "lifetime_node_id", node_id)
            changed |= _set_meta_value(node.stmt, "lifetime_defs", sorted(node.defs))
            changed |= _set_meta_value(node.stmt, "lifetime_uses", sorted(node.uses))
            changed |= _set_meta_value(node.stmt, "lifetime_live_in", _sorted_str_list(live_in.get(node_id, set())))
            changed |= _set_meta_value(node.stmt, "lifetime_live_out", _sorted_str_list(live_out.get(node_id, set())))
            changed |= _set_meta_value(node.stmt, "lifetime_last_use_vars", last_use_vars)

        node_summaries: list[dict[str, Any]] = []
        for node_id in order:
            node = nodes[node_id]
            node_summaries.append(
                {
                    "id": node_id,
                    "kind": node.kind,
                    "defs": sorted(node.defs),
                    "uses": sorted(node.uses),
                    "succ": sorted(node.succ),
                }
            )

        fn_analysis = {
            "schema_version": "east3_lifetime_v1",
            "status": "fail_closed" if fail_closed else "ok",
            "reason": "dynamic_name_access" if fail_closed else "",
            "entry_node": entry_id,
            "order": list(order),
            "cfg": node_summaries,
            "def_use": {
                "defs": {name: sorted(list(node_ids)) for name, node_ids in sorted(defs_index.items())},
                "uses": {name: sorted(list(node_ids)) for name, node_ids in sorted(uses_index.items())},
            },
            "variables": variables,
            "arg_order": list(args),
            "arg_escape": [bool(v) for v in arg_escape],
            "has_dynamic_name_access": fail_closed,
        }
        changed |= _set_meta_value(fn_node, "lifetime_analysis", fn_analysis)
        return changed

    def _visit(self, node: Any, context: PassContext) -> int:
        if isinstance(node, list):
            changed = 0
            for item in node:
                changed += self._visit(item, context)
            return changed
        if not isinstance(node, dict):
            return 0

        kind = _safe_name(node.get("kind"))
        changed = 0
        if kind == "FunctionDef":
            if self._analyze_function(node, context):
                changed += 1
            return changed
        if kind == "ClassDef":
            body = _iter_stmt_list(node.get("body"))
            for item in body:
                if _safe_name(item.get("kind")) != "FunctionDef":
                    continue
                if self._analyze_function(item, context):
                    changed += 1
            return changed

        for value in node.values():
            changed += self._visit(value, context)
        return changed

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        change_count = self._visit(east3_doc, context)
        if _set_meta_value(east3_doc, "lifetime_schema_version", "east3_lifetime_v1"):
            change_count += 1
        return PassResult(changed=change_count > 0, change_count=change_count)

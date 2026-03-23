"""Annotate list locals eligible for value lowering (all backends)."""

from __future__ import annotations

from typing import Any

from toolchain.compile.east3_optimizer import East3OptimizerPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import PassResult


_CONTAINER_VALUE_LOCAL_HINT_KEY = "container_value_locals_v1"


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        txt = s.strip()
        if txt != "":
            return txt
    return "unknown"


def _split_generic_types(text: str) -> list[str]:
    out: list[str] = []
    part = ""
    depth = 0
    for ch in text:
        if ch in "<[":
            depth += 1
            part += ch
            continue
        if ch in ">]":
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


def _is_concrete_type(type_name: str) -> bool:
    t = _normalize_type_name(type_name)
    if t in {"", "unknown", "Any", "object", "None"}:
        return False
    if "|" in t:
        for part in t.split("|"):
            if not _is_concrete_type(part):
                return False
        return True
    if t.startswith("list[") and t.endswith("]"):
        parts = _split_generic_types(t[5:-1])
        return len(parts) == 1 and _is_concrete_type(parts[0])
    if t.startswith("tuple[") and t.endswith("]"):
        parts = _split_generic_types(t[6:-1])
        return len(parts) > 0 and all(_is_concrete_type(part) for part in parts)
    if t.startswith("dict[") and t.endswith("]"):
        parts = _split_generic_types(t[5:-1])
        return len(parts) == 2 and _is_concrete_type(parts[0]) and _is_concrete_type(parts[1])
    if t.startswith("set[") and t.endswith("]"):
        parts = _split_generic_types(t[4:-1])
        return len(parts) == 1 and _is_concrete_type(parts[0])
    return True


def _is_typed_list_type(type_name: str) -> bool:
    t = _normalize_type_name(type_name)
    if not (t.startswith("list[") and t.endswith("]")):
        return False
    parts = _split_generic_types(t[5:-1])
    return len(parts) == 1 and _is_concrete_type(parts[0])


def _dict_items(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return out


class ContainerValueLocalHintPass(East3OptimizerPass):
    """Mark proven-safe list locals for value lowering (all backends)."""

    name = "ContainerValueLocalHintPass"
    min_opt_level = 1

    def _collect_name_reads(self, node: Any, out: set[str]) -> None:
        if isinstance(node, list):
            for item in node:
                self._collect_name_reads(item, out)
            return
        if not isinstance(node, dict):
            return
        nd: dict[str, Any] = node
        if _normalize_type_name(nd.get("kind")) == "Name":
            ident = nd.get("id")
            if isinstance(ident, str) and ident != "":
                out.add(ident)
        for value in nd.values():
            self._collect_name_reads(value, out)

    def _collect_name_targets(self, target_node: Any, out: set[str]) -> None:
        if isinstance(target_node, list):
            for item in target_node:
                self._collect_name_targets(item, out)
            return
        if not isinstance(target_node, dict):
            return
        tnd: dict[str, Any] = target_node
        kind = _normalize_type_name(tnd.get("kind"))
        if kind == "Name":
            ident = tnd.get("id")
            if isinstance(ident, str) and ident != "":
                out.add(ident)
            return
        if kind == "Tuple":
            for elem in _dict_items(tnd.get("elements")):
                self._collect_name_targets(elem, out)

    def _safe_call(self, call_node: dict[str, Any], candidates: set[str]) -> bool:
        runtime_call = _normalize_type_name(call_node.get("runtime_call"))
        builtin_name = _normalize_type_name(call_node.get("builtin_name"))
        if runtime_call == "py_len" or runtime_call == "py_to_string" or runtime_call == "py_to_bool" or runtime_call == "py_to_int64" or runtime_call == "py_to_float64":
            return True
        if builtin_name == "len":
            return True
        fn_node = call_node.get("func")
        fn = fn_node if isinstance(fn_node, dict) else {}
        fn_kind = _normalize_type_name(fn.get("kind"))
        if fn_kind == "Name":
            return _normalize_type_name(fn.get("id")) == "len"
        if fn_kind != "Attribute":
            return False
        owner_node = fn.get("value")
        owner = owner_node if isinstance(owner_node, dict) else {}
        owner_name = _normalize_type_name(owner.get("id"))
        if owner_name not in candidates:
            return False
        attr = _normalize_type_name(fn.get("attr"))
        return attr == "append" or attr == "extend" or attr == "pop" or attr == "clear" or attr == "reverse" or attr == "sort"

    def _value_list_locals_for_function(self, fn_node: dict[str, Any]) -> set[str]:
        body = _dict_items(fn_node.get("body"))
        candidates: set[str] = set()
        for stmt in body:
            if _normalize_type_name(stmt.get("kind")) != "AnnAssign":
                continue
            target = stmt.get("target")
            target_node = target if isinstance(target, dict) else {}
            if _normalize_type_name(target_node.get("kind")) != "Name":
                continue
            ann_t = _normalize_type_name(stmt.get("annotation"))
            if not _is_typed_list_type(ann_t):
                continue
            value = stmt.get("value")
            value_node = value if isinstance(value, dict) else {}
            if _normalize_type_name(value_node.get("kind")) != "List":
                continue
            if len(_dict_items(value_node.get("elements"))) != 0:
                continue
            name = target_node.get("id")
            if isinstance(name, str) and name != "":
                candidates.add(name)
        if len(candidates) == 0:
            return set()

        escaped: set[str] = set()

        def _scan(cur: Any) -> None:
            if not isinstance(cur, dict):
                if isinstance(cur, list):
                    cl: list[Any] = cur
                    for item in cl:
                        _scan(item)
                return
            cd: dict[str, Any] = cur
            kind = _normalize_type_name(cd.get("kind"))
            if kind == "Return":
                value_node = cd.get("value")
                value = value_node if isinstance(value_node, dict) else {}
                value_kind = _normalize_type_name(value.get("kind"))
                if value_kind == "Name":
                    value_name = _normalize_type_name(value.get("id"))
                    if value_name in candidates:
                        escaped.add(value_name)
                elif value_kind == "Tuple" or value_kind == "List" or value_kind == "Set" or value_kind == "Dict":
                    reads: set[str] = set()
                    self._collect_name_reads(value, reads)
                    for nm in reads:
                        if nm in candidates:
                            escaped.add(nm)
            if kind == "Call":
                meta_node = cd.get("meta")
                meta = meta_node if isinstance(meta_node, dict) else {}
                callsite_node = meta.get("non_escape_callsite")
                callsite = callsite_node if isinstance(callsite_node, dict) else {}
                args = _dict_items(cd.get("args"))
                callsite_handled = False
                callee_arg_escape_any = callsite.get("callee_arg_escape")
                if isinstance(callee_arg_escape_any, list):
                    callsite_handled = True
                    for i in range(len(args)):
                        arg = args[i]
                        must_escape = True
                        if i < len(callee_arg_escape_any):
                            must_escape = bool(callee_arg_escape_any[i])
                        if not must_escape:
                            continue
                        reads2: set[str] = set()
                        self._collect_name_reads(arg, reads2)
                        for nm in reads2:
                            if nm in candidates:
                                escaped.add(nm)
                elif isinstance(callsite.get("resolved"), bool):
                    callsite_handled = True
                    for arg in args:
                        reads3: set[str] = set()
                        self._collect_name_reads(arg, reads3)
                        for nm in reads3:
                            if nm in candidates:
                                escaped.add(nm)
                if (not callsite_handled) and (not self._safe_call(cd, candidates)):
                    reads4: set[str] = set()
                    self._collect_name_reads(args, reads4)
                    self._collect_name_reads(cd.get("keywords"), reads4)
                    for nm in reads4:
                        if nm in candidates:
                            escaped.add(nm)
            if kind == "Assign" or kind == "AnnAssign":
                targets: set[str] = set()
                self._collect_name_targets(cd.get("target"), targets)
                value_node2 = cd.get("value")
                value2 = value_node2 if isinstance(value_node2, dict) else {}
                if _normalize_type_name(value2.get("kind")) == "Name":
                    value_name2 = _normalize_type_name(value2.get("id"))
                    if value_name2 in candidates and not (len(targets) == 1 and value_name2 in targets):
                        escaped.add(value_name2)
            for value in cd.values():
                _scan(value)

        for stmt in body:
            _scan(stmt)
        return {name for name in candidates if name not in escaped}

    def _set_hint(self, fn_node: dict[str, Any], names: set[str]) -> int:
        meta_node = fn_node.get("meta")
        meta = meta_node if isinstance(meta_node, dict) else {}
        payload = {"version": "1", "locals": sorted(list(names))} if len(names) > 0 else None
        current = meta.get(_CONTAINER_VALUE_LOCAL_HINT_KEY)
        if payload is None:
            if _CONTAINER_VALUE_LOCAL_HINT_KEY in meta:
                meta.pop(_CONTAINER_VALUE_LOCAL_HINT_KEY, None)
                if len(meta) == 0:
                    fn_node.pop("meta", None)
                else:
                    fn_node["meta"] = meta
                return 1
            return 0
        if current == payload:
            return 0
        meta[_CONTAINER_VALUE_LOCAL_HINT_KEY] = payload
        fn_node["meta"] = meta
        return 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        body = _dict_items(east3_doc.get("body"))
        change_count = 0
        for stmt in body:
            if _normalize_type_name(stmt.get("kind")) != "FunctionDef":
                continue
            locals_hint = self._value_list_locals_for_function(stmt)
            change_count += self._set_hint(stmt, locals_hint)
        return PassResult(changed=change_count > 0, change_count=change_count)

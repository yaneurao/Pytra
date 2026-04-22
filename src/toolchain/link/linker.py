"""Linker: east3-opt modules → linked program (manifest + linked east3).

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/global_optimizer.py (import はしない)。
"""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from pytra.std import json
from pytra.typing import cast

from toolchain.link.shared_types import LinkedModule
from toolchain.link.runtime_discovery import discover_runtime_modules
from toolchain.link.runtime_discovery import resolve_runtime_east_path
from toolchain.link.type_id import build_type_id_table
from toolchain.link.trait_id import build_trait_implementation_map
from toolchain.link.call_graph import build_call_graph
from toolchain.link.dependencies import build_all_resolved_dependencies
from toolchain.link.import_maps import collect_import_maps
from toolchain.link.expand_defaults import expand_cross_module_defaults
from toolchain.resolve.py.type_norm import normalize_type
from toolchain.compile.jv import jv_dict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINK_OUTPUT_SCHEMA = "pytra.link_output.v1"
TYPE_ID_TABLE_MODULE_ID = "pytra.built_in.type_id_table"
TYPE_ID_TABLE_INPUT_PATH = "__linked_helper__/pytra/built_in/type_id_table.east3.json"
TYPE_ID_TABLE_SOURCE_PATH = "src/pytra/built_in/type_id_table.py"
TYPE_ID_TABLE_HELPER_ID = "pytra.built_in.type_id_table"
TYPE_ID_RUNTIME_MODULE_ID = "pytra.built_in.type_id"

_LINK_EXTERNAL_MODULE_PREFIXES: list[str] = [
    "pytra.",
]

@dataclass
class LinkResult:
    """link 段の全出力。"""
    manifest: dict[str, JsonVal]
    linked_modules: list[LinkedModule]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _module_id_from_doc(
    east_doc: dict[str, JsonVal],
    file_path: str,
    runtime_east_root: Path,
) -> str:
    """EAST3 doc から module_id を導出する。"""
    def _normalize_package_module_id(module_id: str) -> str:
        if module_id.endswith(".__init__"):
            return module_id[: -len(".__init__")]
        return module_id

    meta_val = east_doc.get("meta")
    if isinstance(meta_val, dict):
        mid_val = meta_val.get("module_id")
        if isinstance(mid_val, str) and mid_val.strip() != "":
            return _normalize_package_module_id(mid_val.strip())

    source_path_val = east_doc.get("source_path")
    if isinstance(source_path_val, str) and source_path_val.strip() != "":
        source_path_norm = source_path_val.strip().replace("\\", "/")
        # Handle both relative (src/toolchain2/...) and absolute (/path/to/src/toolchain2/...) paths
        _tc2_markers: list[str] = ["src/toolchain2/"]
        for marker in _tc2_markers:
            idx = source_path_norm.find(marker)
            if idx >= 0 and source_path_norm.endswith(".py"):
                rel = source_path_norm[idx + len("src/"):].replace(".py", "")
                module_id = rel.replace("/", ".")
                module_id = _normalize_package_module_id(module_id)
                if module_id != "":
                    return module_id
        if source_path_norm.endswith("src/pytra-cli.py") or source_path_norm == "src/pytra-cli.py":
            return "pytra_cli2"

    # Runtime .east ファイルの場合はパスから導出
    resolved_path = Path(file_path).resolve()
    east_root_path = runtime_east_root.resolve()
    try:
        root_prefix = str(east_root_path).replace("\\", "/")
        resolved_prefix = str(resolved_path).replace("\\", "/")
        if not resolved_prefix.startswith(root_prefix + "/"):
            raise ValueError("outside runtime east root")
        rel_str = resolved_prefix[len(root_prefix) + 1 :]
        if rel_str.endswith(".east"):
            rel_str = rel_str.replace(".east", "")
        module_id = "pytra." + rel_str.replace("/", ".")
        module_id = _normalize_package_module_id(module_id)
        if module_id != "":
            return module_id
    except ValueError:
        pass

    # ファイル名から推測
    name = Path(file_path).name
    if name.endswith(".east3.json"):
        name = name.replace(".east3.json", "")
    elif name.endswith(".east3"):
        name = name.replace(".east3", "")
    elif name.endswith(".east2"):
        name = name.replace(".east2", "")
    elif name.endswith(".east"):
        name = name.replace(".east", "")
    elif name.endswith(".json"):
        name = name.replace(".json", "")
    name = name.replace("-", "_").strip()
    name = _normalize_package_module_id(name)
    if name == "":
        raise RuntimeError("failed to infer module_id from path: " + file_path)
    return name


def _source_path_from_doc(east_doc: dict[str, JsonVal]) -> str:
    """EAST3 doc から source_path を取得する。"""
    sp = east_doc.get("source_path")
    if isinstance(sp, str):
        return sp
    return ""


def _dispatch_mode_from_doc(east_doc: dict[str, JsonVal]) -> str:
    """EAST3 doc から dispatch_mode を取得する。"""
    meta_val = east_doc.get("meta")
    if isinstance(meta_val, dict):
        dm = meta_val.get("dispatch_mode")
        if isinstance(dm, str):
            return dm
    return "native"


def _linked_output_path(module_id: str) -> str:
    """linked module の出力相対パスを生成する。"""
    return "east3/" + module_id.replace(".", "/") + ".east3.json"


def _copy_json(val: JsonVal) -> JsonVal:
    if isinstance(val, list):
        return [_copy_json(item) for item in val]
    if isinstance(val, dict):
        out: dict[str, JsonVal] = {}
        for key, value in val.items():
            out[key] = _copy_json(value)
        return out
    return val


def _program_id(
    target: str,
    dispatch_mode: str,
    module_ids: list[str],
) -> str:
    """決定的な program_id を生成する。"""
    return target + ":" + dispatch_mode + ":" + ",".join(sorted(module_ids))


def _ensure_meta(doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """doc の meta を dict として返す (なければ作成)。"""
    meta_val = doc.get("meta")
    if isinstance(meta_val, dict):
        return meta_val
    meta: dict[str, JsonVal] = {}
    doc["meta"] = meta
    return meta


def _is_link_external_module(module_id: str) -> bool:
    mid = module_id.strip()
    if mid == "":
        return True
    for prefix in _LINK_EXTERNAL_MODULE_PREFIXES:
        if mid.startswith(prefix):
            return True
    return False


def _is_whitelisted_missing_dependency(module: LinkedModule, module_id: str) -> bool:
    if _is_link_external_module(module_id):
        return True
    if module.module_kind == "runtime" and not module_id.startswith("toolchain."):
        return True
    # Python stdlib modules (no dot → top-level package, not toolchain2/pytra)
    if "." not in module_id and not module_id.startswith("toolchain2"):
        return True
    return False


def _append_missing_importer(
    missing: dict[str, list[str]],
    module_id: str,
    importer: str,
) -> None:
    if module_id == "":
        return
    if module_id not in missing:
        missing[module_id] = [importer]
        return
    rows = missing[module_id]
    if importer not in rows:
        rows.append(importer)


def _sorted_doc_map_keys(module_map: dict[str, dict[str, JsonVal]]) -> list[str]:
    return _sorted_str_list(list(module_map.keys()))


def _sorted_str_map_keys(values: dict[str, JsonVal]) -> list[str]:
    return _sorted_str_list(list(values.keys()))


def _sorted_str_list(values: list[str]) -> list[str]:
    out = list(values)
    n = len(out)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if out[j] < out[i]:
                cur = out[i]
                out[i] = out[j]
                out[j] = cur
            j += 1
        i += 1
    return out


def _import_maps(doc: dict[str, JsonVal]) -> tuple[dict[str, str], dict[str, str]]:
    raw = collect_import_maps(doc)
    import_modules: dict[str, str] = {}
    import_symbols: dict[str, str] = {}
    if isinstance(raw, tuple) and len(raw) == 2:
        left = raw[0]
        right = raw[1]
        if isinstance(left, dict):
            for key, value in left.items():
                if isinstance(key, str) and key != "" and isinstance(value, str):
                    import_modules[key] = value
        if isinstance(right, dict):
            for key, value in right.items():
                if isinstance(key, str) and key != "" and isinstance(value, str):
                    import_symbols[key] = value
    return import_modules, import_symbols


def _set_to_sorted_str_list(values: set[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        out.append(value)
    return _sorted_str_list(out)


def _sorted_modules_by_id(modules: list[LinkedModule]) -> list[LinkedModule]:
    out = list(modules)
    n = len(out)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if out[j].module_id < out[i].module_id:
                cur = out[i]
                out[i] = out[j]
                out[j] = cur
            j += 1
        i += 1
    return out


def _dep_rows(dep_map: dict[str, list[str]], module_id: str) -> list[str]:
    if module_id in dep_map:
        return dep_map[module_id]
    return []


def _doc_map_get(module_map: dict[str, dict[str, JsonVal]], path_str: str) -> dict[str, JsonVal]:
    return module_map[path_str]


def _docs_as_json(copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for _module, doc in copied_docs:
        out.append(doc)
    return out


def _walk_nodes(node: JsonVal) -> list[dict[str, JsonVal]]:
    out: list[dict[str, JsonVal]] = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            for child in _walk_nodes(value):
                out.append(child)
    elif isinstance(node, list):
        for item in node:
            for child2 in _walk_nodes(item):
                out.append(child2)
    return out


def _node_str(node: dict[str, JsonVal], key: str) -> str:
    value = node.get(key)
    if isinstance(value, str):
        return value
    return ""


def _node_list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    value = node.get(key)
    if isinstance(value, list):
        return value
    return []


def _json_dict_equal(left: JsonVal, right: dict[str, JsonVal]) -> bool:
    return isinstance(left, dict) and jv_dict(left) == right


def _json_dict_not_equal(left: JsonVal, right: dict[str, JsonVal]) -> bool:
    return not _json_dict_equal(left, right)


def _json_list_item_equal(items: list[JsonVal], index: int, node: dict[str, JsonVal]) -> bool:
    return 0 <= index < len(items) and isinstance(items[index], dict) and jv_dict(items[index]) == node


def _walk_nodes_with_parents(
    node: JsonVal,
    parents: list[dict[str, JsonVal]],
) -> list[tuple[dict[str, JsonVal], list[dict[str, JsonVal]]]]:
    out: list[tuple[dict[str, JsonVal], list[dict[str, JsonVal]]]] = []
    if isinstance(node, dict):
        out.append((node, parents))
        next_parents = list(parents)
        next_parents.append(node)
        for value in node.values():
            for child in _walk_nodes_with_parents(value, next_parents):
                out.append(child)
    elif isinstance(node, list):
        for item in node:
            for child2 in _walk_nodes_with_parents(item, parents):
                out.append(child2)
    return out


def _ensure_node_meta(node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    meta_val = node.get("meta")
    if isinstance(meta_val, dict):
        return meta_val
    meta: dict[str, JsonVal] = {}
    node["meta"] = meta
    return meta


def _is_name_with_id(node: JsonVal, name: str) -> bool:
    return isinstance(node, dict) and node.get("kind") == "Name" and node.get("id") == name


def _is_bytes_from_local_bytearray_call(node: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]] | None:
    if _node_str(node, "kind") != "Call":
        return None
    func = node.get("func")
    args = _node_list(node, "args")
    if not isinstance(func, dict) or _node_str(func, "kind") != "Name" or _node_str(func, "id") != "bytes":
        return None
    if len(args) != 1 or not isinstance(args[0], dict):
        return None
    arg = args[0]
    if _node_str(arg, "kind") != "Name" or _node_str(arg, "resolved_type") != "bytearray":
        return None
    source_name = _node_str(arg, "id")
    if source_name == "":
        return None
    return (source_name, jv_dict(arg))


def _top_level_function_map(doc: dict[str, JsonVal]) -> dict[str, dict[str, JsonVal]]:
    out: dict[str, dict[str, JsonVal]] = {}
    for stmt in _node_list(doc, "body"):
        if not isinstance(stmt, dict):
            continue
        kind = _node_str(stmt, "kind")
        if kind != "FunctionDef" and kind != "ClosureDef":
            continue
        name = _node_str(stmt, "name")
        if name == "":
            continue
        out[name] = jv_dict(stmt)
    return out


def _copy_elision_return_candidate(func_node: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
    for stmt in _node_list(func_node, "body"):
        if not isinstance(stmt, dict) or _node_str(stmt, "kind") != "Return":
            continue
        value = stmt.get("value")
        if not isinstance(value, dict):
            continue
        hit = _is_bytes_from_local_bytearray_call(value)
        if hit is not None:
            return value
    return None


def _find_outer_call_for_arg(
    node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> dict[str, JsonVal] | None:
    i = len(parents) - 1
    while i >= 0:
        parent = parents[i]
        if _node_str(parent, "kind") == "Call":
            args = _node_list(parent, "args")
            for arg in args:
                if _json_dict_equal(arg, node):
                    return parent
        i -= 1
    return None


def _find_direct_parent(
    parents: list[dict[str, JsonVal]],
) -> dict[str, JsonVal] | None:
    if len(parents) == 0:
        return None
    return parents[len(parents) - 1]


def _is_list_append_call_on_name(call_node: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]] | None:
    func = call_node.get("func")
    if not isinstance(func, dict) or _node_str(func, "kind") != "Attribute" or _node_str(func, "attr") != "append":
        return None
    owner = func.get("value")
    if not isinstance(owner, dict) or _node_str(owner, "kind") != "Name":
        return None
    owner_type = _node_str(owner, "resolved_type")
    if owner_type != "list[bytes]":
        return None
    owner_name = _node_str(owner, "id")
    if owner_name == "":
        return None
    return (owner_name, owner)


def _call_arg_usage_is_readonly(
    call_node: dict[str, JsonVal],
    arg_node: dict[str, JsonVal],
) -> bool:
    sig = call_node.get("function_signature_v1")
    if isinstance(sig, dict):
        arg_order = sig.get("arg_order")
        arg_usage = sig.get("arg_usage")
        if isinstance(arg_order, list) and isinstance(arg_usage, dict):
            args = _node_list(call_node, "args")
            i = 0
            while i < len(args):
                if _json_list_item_equal(args, i, arg_node):
                    if i >= len(arg_order):
                        return False
                    arg_name = arg_order[i]
                    if not isinstance(arg_name, str) or arg_name == "":
                        return False
                    return arg_usage.get(arg_name) == "readonly"
                i += 1

            keywords = _node_list(call_node, "keywords")
            for kw in keywords:
                if not isinstance(kw, dict):
                    continue
                if _json_dict_not_equal(kw.get("value"), arg_node):
                    continue
                arg_name = kw.get("arg")
                if not isinstance(arg_name, str) or arg_name == "":
                    return False
                return arg_usage.get(arg_name) == "readonly"
    runtime_call = _node_str(call_node, "runtime_call")
    semantic_tag = _node_str(call_node, "semantic_tag")
    if runtime_call in ("TextIOWrapper.write", "BufferedWriter.write") or semantic_tag == "stdlib.method.write":
        args = _node_list(call_node, "args")
        return _json_list_item_equal(args, 0, arg_node)
    return False


def _call_local_function_arg_is_readonly(
    call_node: dict[str, JsonVal],
    arg_node: dict[str, JsonVal],
    funcs: dict[str, dict[str, JsonVal]],
) -> bool:
    func = call_node.get("func")
    if not isinstance(func, dict) or _node_str(func, "kind") != "Name":
        return False
    callee_name = _node_str(func, "id")
    if callee_name == "":
        return False
    callee = funcs.get(callee_name)
    if not isinstance(callee, dict):
        return False
    arg_order = callee.get("arg_order")
    arg_usage = callee.get("arg_usage")
    if not isinstance(arg_order, list) or not isinstance(arg_usage, dict):
        return False
    args = _node_list(call_node, "args")
    i = 0
    while i < len(args):
        if _json_list_item_equal(args, i, arg_node):
            if i >= len(arg_order):
                return False
            arg_name = arg_order[i]
            if not isinstance(arg_name, str) or arg_name == "":
                return False
            return arg_usage.get(arg_name) == "readonly"
        i += 1
    return False


def _name_used_as_arg_readonly(
    name_node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> bool:
    outer = _find_outer_call_for_arg(name_node, parents)
    if outer is None:
        return False
    return _node_str(name_node, "borrow_kind") == "readonly_ref"


def _name_is_append_owner(
    name_node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> bool:
    direct_parent = _find_direct_parent(parents)
    if direct_parent is None:
        return False
    if _node_str(direct_parent, "kind") == "Call":
        func = direct_parent.get("func")
        if (
            isinstance(func, dict)
            and _node_str(func, "kind") == "Attribute"
            and _is_name_with_id(func.get("value"), _node_str(name_node, "id"))
        ):
            hit = _is_list_append_call_on_name(direct_parent)
            return hit is not None
        return False
    if _node_str(direct_parent, "kind") != "Attribute":
        return False
    if _json_dict_not_equal(direct_parent.get("value"), name_node):
        return False
    outer = _find_direct_parent(parents[: len(parents) - 1])
    if outer is None or _node_str(outer, "kind") != "Call":
        return False
    hit = _is_list_append_call_on_name(outer)
    return hit is not None


def _name_is_readonly_subscript_owner(
    name_node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> bool:
    direct_parent = _find_direct_parent(parents)
    if direct_parent is None or _node_str(direct_parent, "kind") != "Subscript":
        return False
    return _json_dict_equal(direct_parent.get("value"), name_node)


def _name_is_decl_target(
    name_node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> bool:
    direct_parent = _find_direct_parent(parents)
    if direct_parent is None:
        return False
    kind = _node_str(direct_parent, "kind")
    if kind != "AnnAssign" and kind != "Assign":
        return False
    return _json_dict_equal(direct_parent.get("target"), name_node)


def _assigned_local_name(
    node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> str:
    direct_parent = _find_direct_parent(parents)
    if direct_parent is None:
        return ""
    kind = _node_str(direct_parent, "kind")
    if kind != "AnnAssign" and kind != "Assign":
        return ""
    if _json_dict_not_equal(direct_parent.get("value"), node):
        return ""
    target = direct_parent.get("target")
    if not isinstance(target, dict) or _node_str(target, "kind") != "Name":
        return ""
    return _node_str(target, "id")


def _all_name_uses_readonly_in_function(
    func_node: dict[str, JsonVal],
    local_name: str,
) -> bool:
    for node, parents in _walk_nodes_with_parents(func_node, []):
        if not _is_name_with_id(node, local_name):
            continue
        direct_parent = _find_direct_parent(parents)
        direct_kind = _node_str(direct_parent, "kind") if isinstance(direct_parent, dict) else ""
        if direct_kind in ("RuntimeIterForPlan", "StaticRangeForPlan", "ForCore", "TargetPlan"):
            continue
        if _name_is_decl_target(node, parents):
            continue
        if _name_is_append_owner(node, parents):
            continue
        if _name_is_readonly_subscript_owner(node, parents):
            continue
        if _name_used_as_arg_readonly(node, parents):
            continue
        return False
    return True


def _annotate_copy_elision_safe_v1(copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]]) -> None:
    module_funcs: dict[str, dict[str, dict[str, JsonVal]]] = {}
    for module, doc in copied_docs:
        module_funcs[module.module_id] = _top_level_function_map(doc)

    for module, _doc in copied_docs:
        funcs = module_funcs.get(module.module_id, {})
        for func_name in _sorted_str_list(list(funcs.keys())):
            func_node = funcs[func_name]
            for node, parents in _walk_nodes_with_parents(func_node, []):
                if _node_str(node, "kind") != "Call":
                    continue
                hit = _is_bytes_from_local_bytearray_call(node)
                if hit is None:
                    continue
                safe_local = False
                outer_call = _find_outer_call_for_arg(node, parents)
                if outer_call is not None and _call_arg_usage_is_readonly(outer_call, node):
                    safe_local = True
                if not safe_local and outer_call is not None and _call_local_function_arg_is_readonly(outer_call, node, funcs):
                    safe_local = True
                local_name = _assigned_local_name(node, parents)
                if not safe_local and local_name != "" and _all_name_uses_readonly_in_function(func_node, local_name):
                    safe_local = True
                if not safe_local:
                    continue
                meta = _ensure_node_meta(node)
                if "copy_elision_safe_v1" in meta:
                    continue
                copy_meta: dict[str, JsonVal] = {}
                copy_meta["schema_version"] = 1
                copy_meta["operation"] = "bytes_from_bytearray"
                copy_meta["source_name"] = hit[0]
                copy_meta["borrow_kind"] = "readonly_ref"
                copy_meta["analysis_scope"] = "linked_program"
                copy_meta["proof_summary"] = "linker verified local bytes(bytearray) result flows only through readonly uses"
                meta["copy_elision_safe_v1"] = copy_meta

    candidate_calls: dict[str, dict[str, JsonVal]] = {}
    for module, _doc in copied_docs:
        funcs = module_funcs.get(module.module_id, {})
        for func_name in _sorted_str_list(list(funcs.keys())):
            func_node = funcs[func_name]
            call_node = _copy_elision_return_candidate(func_node)
            if call_node is not None:
                candidate_calls[module.module_id + "::" + func_name] = call_node

    for candidate_key in _sorted_str_list(list(candidate_calls.keys())):
        sep = candidate_key.find("::")
        if sep < 0:
            continue
        module_id = candidate_key[:sep]
        func_name = candidate_key[sep + 2 :]
        call_node = candidate_calls[candidate_key]
        hit = _is_bytes_from_local_bytearray_call(call_node)
        if hit is None:
            continue
        source_name = hit[0]

        safe = True
        saw_callsite = False
        caller_lists: dict[str, dict[str, JsonVal]] = {}
        for module, _doc in copied_docs:
            funcs = module_funcs.get(module.module_id, {})
            for caller_name in _sorted_str_list(list(funcs.keys())):
                caller_func = funcs[caller_name]
                for node, parents in _walk_nodes_with_parents(caller_func, []):
                    if _node_str(node, "kind") != "Call":
                        continue
                    func = node.get("func")
                    if not isinstance(func, dict) or _node_str(func, "kind") != "Name" or _node_str(func, "id") != func_name:
                        continue
                    if _json_dict_equal(node, call_node):
                        continue
                    saw_callsite = True
                    outer_call = _find_outer_call_for_arg(node, parents)
                    if outer_call is not None and _call_arg_usage_is_readonly(outer_call, node):
                        continue
                    local_name = _assigned_local_name(node, parents)
                    if local_name != "" and _all_name_uses_readonly_in_function(caller_func, local_name):
                        continue
                    outer_call = _find_outer_call_for_arg(node, parents)
                    if outer_call is None:
                        safe = False
                        break
                    list_hit = _is_list_append_call_on_name(outer_call)
                    if list_hit is None:
                        safe = False
                        break
                    list_name = list_hit[0]
                    caller_lists[caller_name + "::" + list_name] = caller_func
                if not safe:
                    break
            if not safe:
                break
        if not safe or not saw_callsite:
            continue

        for list_key in _sorted_str_list(list(caller_lists.keys())):
            sep2 = list_key.find("::")
            if sep2 < 0:
                safe = False
                break
            list_name = list_key[sep2 + 2 :]
            caller_func = caller_lists[list_key]
            if not _all_name_uses_readonly_in_function(caller_func, list_name):
                safe = False
                break
        if not safe:
            continue

        meta = _ensure_node_meta(call_node)
        copy_meta2: dict[str, JsonVal] = {}
        copy_meta2["schema_version"] = 1
        copy_meta2["operation"] = "bytes_from_bytearray"
        copy_meta2["source_name"] = source_name
        copy_meta2["borrow_kind"] = "readonly_ref"
        copy_meta2["analysis_scope"] = "linked_program"
        copy_meta2["proof_summary"] = "linker verified local bytes(bytearray) result flows only through readonly list[bytes] uses"
        meta["copy_elision_safe_v1"] = copy_meta2


def _raise_types_in_node(node: JsonVal) -> set[str]:
    out: set[str] = set()
    if isinstance(node, dict):
        if node.get("kind") == "Raise":
            exc = node.get("exc")
            if isinstance(exc, dict):
                if exc.get("kind") == "Call":
                    func = exc.get("func")
                    if isinstance(func, dict):
                        func_id = func.get("id")
                        if isinstance(func_id, str) and func_id != "":
                            out.add(func_id)
                rt = exc.get("resolved_type")
                if isinstance(rt, str) and rt != "":
                    out.add(rt)
        if node.get("kind") in ("FunctionDef", "ClosureDef", "ClassDef"):
            return out
        for value in node.values():
            child = _raise_types_in_node(value)
            for item in child:
                out.add(item)
    elif isinstance(node, list):
        for item2 in node:
            child2 = _raise_types_in_node(item2)
            for item3 in child2:
                out.add(item3)
    return out


def _collect_direct_raise_markers(modules: list[LinkedModule]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for module in modules:
        body = module.east_doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if not isinstance(stmt, dict):
                    continue
                kind = stmt.get("kind")
                if kind == "FunctionDef":
                    name = stmt.get("name")
                    if isinstance(name, str) and name != "":
                        raised = _raise_types_in_node(stmt.get("body", []))
                        if len(raised) > 0:
                            out[module.module_id + "::" + name] = raised
                elif kind == "ClassDef":
                    class_name = stmt.get("name")
                    class_body = stmt.get("body")
                    if not isinstance(class_name, str) or not isinstance(class_body, list):
                        continue
                    for method in class_body:
                        if not isinstance(method, dict) or method.get("kind") != "FunctionDef":
                            continue
                        method_name = method.get("name")
                        if isinstance(method_name, str) and method_name != "":
                            raised2 = _raise_types_in_node(method.get("body", []))
                            if len(raised2) > 0:
                                out[module.module_id + "::" + class_name + "." + method_name] = raised2
        main_guard = module.east_doc.get("main_guard_body")
        if isinstance(main_guard, list):
            raised3 = _raise_types_in_node(main_guard)
            if len(raised3) > 0:
                out[module.module_id + "::__main__"] = raised3
    return out


def _propagate_can_raise(
    graph: dict[str, set[str]],
    direct: dict[str, set[str]],
) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for key, value in direct.items():
        out[key] = set(value)
    changed = True
    while changed:
        changed = False
        for caller, callees in graph.items():
            merged: set[str] = set(out.get(caller, set()))
            for callee in callees:
                for exc in out.get(callee, set()):
                    merged.add(exc)
            if caller not in out or merged != out.get(caller, set()):
                out[caller] = merged
                changed = True
    return out


def _attach_can_raise_markers(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
    can_raise: dict[str, set[str]],
) -> None:
    for module, doc in copied_docs:
        body = doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if not isinstance(stmt, dict):
                    continue
                kind = stmt.get("kind")
                if kind == "FunctionDef":
                    name = stmt.get("name")
                    if isinstance(name, str):
                        qualified = module.module_id + "::" + name
                        excs = can_raise.get(qualified, set())
                        if len(excs) > 0:
                            meta = _ensure_meta(stmt)
                            can_raise_meta: dict[str, JsonVal] = {}
                            can_raise_meta["schema_version"] = 1
                            can_raise_meta["exception_types"] = _set_to_sorted_str_list(excs)
                            meta["can_raise_v1"] = can_raise_meta
                elif kind == "ClassDef":
                    class_name = stmt.get("name")
                    class_body = stmt.get("body")
                    if not isinstance(class_name, str) or not isinstance(class_body, list):
                        continue
                    for method in class_body:
                        if not isinstance(method, dict) or method.get("kind") != "FunctionDef":
                            continue
                        method_name = method.get("name")
                        if isinstance(method_name, str):
                            qualified2 = module.module_id + "::" + class_name + "." + method_name
                            excs2 = can_raise.get(qualified2, set())
                            if len(excs2) > 0:
                                meta2 = _ensure_meta(method)
                                can_raise_meta2: dict[str, JsonVal] = {}
                                can_raise_meta2["schema_version"] = 1
                                can_raise_meta2["exception_types"] = _set_to_sorted_str_list(excs2)
                                meta2["can_raise_v1"] = can_raise_meta2
        main_excs = can_raise.get(module.module_id + "::__main__", set())
        if len(main_excs) > 0:
            meta3 = _ensure_meta(doc)
            can_raise_meta3: dict[str, JsonVal] = {}
            can_raise_meta3["schema_version"] = 1
            can_raise_meta3["exception_types"] = _set_to_sorted_str_list(main_excs)
            meta3["can_raise_v1"] = can_raise_meta3


def _link_resolve_trait_ref(
    type_name: str,
    *,
    module_id: str,
    local_traits: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
    all_traits: set[str],
) -> str:
    if type_name == "":
        return ""
    if type_name in all_traits:
        return type_name
    if type_name in local_traits:
        return local_traits[type_name]
    imported_symbol = import_symbols.get(type_name, "")
    if imported_symbol != "" and "::" in imported_symbol:
        delim = imported_symbol.find("::")
        dep_module_id = imported_symbol[:delim]
        export_name = imported_symbol[delim + 2:]
        candidate = dep_module_id + "." + export_name
        if candidate in all_traits:
            return candidate
    if "." in type_name:
        last_dot = -1
        i = len(type_name) - 1
        while i >= 0:
            if type_name[i] == ".":
                last_dot = i
                break
            i -= 1
        owner_name = type_name[:last_dot]
        attr_name = type_name[last_dot + 1:]
        imported_module = import_modules.get(owner_name, "")
        if imported_module != "":
            candidate2 = imported_module + "." + attr_name
            if candidate2 in all_traits:
                return candidate2
    candidate3 = module_id + "." + type_name
    if candidate3 in all_traits:
        return candidate3
    return ""


def _fold_trait_predicates(
    module_id: str,
    doc: dict[str, JsonVal],
    all_traits: set[str],
    trait_impls: dict[str, set[str]],
) -> None:
    import_modules, import_symbols = _import_maps(doc)
    local_traits: dict[str, str] = {}
    body = doc.get("body")
    if isinstance(body, list):
        for item in body:
            if not isinstance(item, dict) or item.get("kind") != "ClassDef":
                continue
            meta = item.get("meta")
            if not isinstance(meta, dict) or not isinstance(meta.get("trait_v1"), dict):
                continue
            class_name = item.get("name")
            if isinstance(class_name, str) and class_name != "":
                local_traits[class_name] = module_id + "." + class_name

    for node in _walk_nodes(doc):
        if node.get("kind") != "IsInstance":
            continue
        expected_name = node.get("expected_type_name")
        if not isinstance(expected_name, str) or expected_name == "":
            continue
        trait_fqcn = _link_resolve_trait_ref(
            expected_name,
            module_id=module_id,
            local_traits=local_traits,
            import_modules=import_modules,
            import_symbols=import_symbols,
            all_traits=all_traits,
        )
        if trait_fqcn == "":
            continue
        value_node = node.get("value")
        value_type = ""
        if isinstance(value_node, dict):
            resolved_type = value_node.get("resolved_type")
            if isinstance(resolved_type, str):
                value_type = resolved_type.strip()
        value_fqcn = _link_resolve_trait_ref(
            value_type,
            module_id=module_id,
            local_traits=local_traits,
            import_modules=import_modules,
            import_symbols=import_symbols,
            all_traits=all_traits,
        )
        if value_fqcn == "":
            candidate = module_id + "." + value_type if value_type != "" else ""
            if candidate in trait_impls:
                value_fqcn = candidate
            elif value_type in trait_impls:
                value_fqcn = value_type
        if value_fqcn == "":
            raise RuntimeError("input_invalid: trait isinstance requires static nominal type: " + module_id + " -> " + expected_name)
        implemented = trait_impls.get(value_fqcn, set())
        folded = trait_fqcn in implemented
        for key in list(node.keys()):
            node.pop(key, None)
        node["kind"] = "Constant"
        node["value"] = folded
        node["resolved_type"] = "bool"


def _copy_doc_rows(copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]]) -> list[tuple[LinkedModule, dict[str, JsonVal]]]:
    out: list[tuple[LinkedModule, dict[str, JsonVal]]] = []
    for module, doc in copied_docs:
        out.append((module, doc))
    return out


def _type_id_const_name(fqcn: str) -> str:
    dotted = fqcn.replace(".", "_")
    chars: list[str] = []
    prev_is_lower = False
    for ch in dotted:
        is_upper = "A" <= ch and ch <= "Z"
        is_lower = "a" <= ch and ch <= "z"
        if is_upper and prev_is_lower:
            chars.append("_")
        chars.append(ch.upper())
        prev_is_lower = is_lower
    result = "".join(chars) + "_TID"
    # C++ identifiers must not start with a digit (e.g. module "18_foo" → "18_FOO_TID").
    if result and "0" <= result[0] and result[0] <= "9":
        result = "_" + result
    return result


def _make_name(id_value: str, resolved_type: str = "") -> dict[str, JsonVal]:
    node: dict[str, JsonVal] = {"kind": "Name", "id": id_value}
    if resolved_type != "":
        node["resolved_type"] = resolved_type
    return node


def _make_constant(value: JsonVal, resolved_type: str) -> dict[str, JsonVal]:
    return {"kind": "Constant", "value": value, "resolved_type": resolved_type}


def _make_list(elements: list[dict[str, JsonVal]], resolved_type: str) -> dict[str, JsonVal]:
    return {"kind": "List", "elements": elements, "resolved_type": resolved_type}


def _collect_local_class_names(doc: dict[str, JsonVal], module_id: str) -> dict[str, str]:
    out: dict[str, str] = {}
    body = doc.get("body")
    if not isinstance(body, list):
        return out
    for item in body:
        if not isinstance(item, dict) or item.get("kind") != "ClassDef":
            continue
        name = item.get("name")
        if isinstance(name, str) and name != "":
            out[name] = module_id + "." + name
    return out


def _collect_class_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for module, doc in copied_docs:
        body = doc.get("body")
        if not isinstance(body, list):
            continue
        for item in body:
            if not isinstance(item, dict) or item.get("kind") != "ClassDef":
                continue
            name = item.get("name")
            hint = item.get("class_storage_hint")
            if not isinstance(name, str) or name == "":
                continue
            if not isinstance(hint, str) or hint == "":
                hint = "value"
            out[module.module_id + "." + name] = hint
    return out


def _collect_class_field_types(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for module, doc in copied_docs:
        body = doc.get("body")
        if not isinstance(body, list):
            continue
        for item in body:
            if not isinstance(item, dict) or item.get("kind") != "ClassDef":
                continue
            name = item.get("name")
            field_types = item.get("field_types")
            if not isinstance(name, str) or name == "" or not isinstance(field_types, dict):
                continue
            typed_fields: dict[str, str] = {}
            for field_name, field_type in field_types.items():
                if isinstance(field_name, str) and field_name != "" and isinstance(field_type, str) and field_type != "":
                    typed_fields[field_name] = field_type
            if len(typed_fields) > 0:
                out[module.module_id + "." + name] = typed_fields
    return out


def _receiver_type_base(type_name: str) -> str:
    t = type_name.strip()
    if t.endswith(" | None"):
        t = t[:-7].strip()
    elif t.endswith("|None"):
        t = t[:-5].strip()
    return t


def _resolve_receiver_class_fqcn(
    receiver_type: str,
    *,
    module_id: str,
    local_classes: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
    class_storage_hints: dict[str, str],
) -> str:
    expected_name = _receiver_type_base(receiver_type)
    if expected_name == "":
        return ""
    def _import_symbol_candidates(imported_symbol: str) -> list[str]:
        out: list[str] = []
        if imported_symbol == "" or "::" not in imported_symbol:
            return out
        dep_module_id, export_name = imported_symbol.split("::", 1)
        dep_module_id = dep_module_id.strip()
        export_name = export_name.strip()
        if dep_module_id == "" or export_name == "":
            return out
        out.append(dep_module_id + "." + export_name)
        if "." not in dep_module_id:
            out.append("pytra.std." + dep_module_id + "." + export_name)
        return out
    if expected_name in class_storage_hints:
        return expected_name
    local_fqcn = local_classes.get(expected_name, "")
    if local_fqcn != "" and local_fqcn in class_storage_hints:
        return local_fqcn
    imported_symbol = import_symbols.get(expected_name, "")
    for candidate in _import_symbol_candidates(imported_symbol):
        if candidate in class_storage_hints:
            return candidate
    if "." in expected_name:
        owner_name, attr_name = expected_name.rsplit(".", 1)
        imported_module = import_modules.get(owner_name, "")
        if imported_module != "":
            candidates = [imported_module + "." + attr_name]
            if "." not in imported_module:
                candidates.append("pytra.std." + imported_module + "." + attr_name)
            for candidate2 in candidates:
                if candidate2 in class_storage_hints:
                    return candidate2
    candidate3 = module_id + "." + expected_name
    if candidate3 in class_storage_hints:
        return candidate3
    return ""


def _attach_receiver_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    class_storage_hints = _collect_class_storage_hints(copied_docs)
    for module, doc in copied_docs:
        import_modules, import_symbols = _import_maps(doc)
        local_classes = _collect_local_class_names(doc, module.module_id)
        for node in _walk_nodes(doc):
            kind = node.get("kind")
            receiver_node: dict[str, JsonVal] | None = None
            if kind == "Attribute":
                value = node.get("value")
                if isinstance(value, dict):
                    receiver_node = value
            elif kind == "Call":
                func = node.get("func")
                if isinstance(func, dict) and func.get("kind") == "Attribute":
                    value2 = func.get("value")
                    if isinstance(value2, dict):
                        receiver_node = value2
            if receiver_node is None:
                continue
            receiver_type = receiver_node.get("resolved_type")
            if not isinstance(receiver_type, str) or receiver_type == "":
                continue
            fqcn = _resolve_receiver_class_fqcn(
                receiver_type,
                module_id=module.module_id,
                local_classes=local_classes,
                import_modules=import_modules,
                import_symbols=import_symbols,
                class_storage_hints=class_storage_hints,
            )
            if fqcn == "":
                hint = receiver_node.get("resolved_storage_hint")
                if isinstance(hint, str) and hint in ("ref", "value"):
                    node["receiver_storage_hint"] = hint
                continue
            hint = class_storage_hints.get(fqcn, "")
            if hint in ("ref", "value"):
                node["receiver_storage_hint"] = hint


def _attach_resolved_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    class_storage_hints = _collect_class_storage_hints(copied_docs)
    for module, doc in copied_docs:
        import_modules, import_symbols = _import_maps(doc)
        local_classes = _collect_local_class_names(doc, module.module_id)
        for node in _walk_nodes(doc):
            resolved_type = node.get("resolved_type")
            if not isinstance(resolved_type, str) or resolved_type == "":
                continue
            fqcn = _resolve_receiver_class_fqcn(
                resolved_type,
                module_id=module.module_id,
                local_classes=local_classes,
                import_modules=import_modules,
                import_symbols=import_symbols,
                class_storage_hints=class_storage_hints,
            )
            if fqcn == "":
                continue
            hint = class_storage_hints.get(fqcn, "")
            if hint in ("ref", "value"):
                node["resolved_storage_hint"] = hint


def _attach_attribute_field_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    class_storage_hints = _collect_class_storage_hints(copied_docs)
    class_field_types = _collect_class_field_types(copied_docs)
    for module, doc in copied_docs:
        import_modules, import_symbols = _import_maps(doc)
        local_classes = _collect_local_class_names(doc, module.module_id)
        for node in _walk_nodes(doc):
            if node.get("kind") != "Attribute":
                continue
            value = node.get("value")
            attr = node.get("attr")
            if not isinstance(value, dict) or not isinstance(attr, str) or attr == "":
                continue
            receiver_type = value.get("resolved_type")
            if not isinstance(receiver_type, str) or receiver_type == "":
                continue
            fqcn = _resolve_receiver_class_fqcn(
                receiver_type,
                module_id=module.module_id,
                local_classes=local_classes,
                import_modules=import_modules,
                import_symbols=import_symbols,
                class_storage_hints=class_storage_hints,
            )
            if fqcn == "":
                continue
            field_type = class_field_types.get(fqcn, {}).get(attr, "")
            if field_type != "":
                current_rt = node.get("resolved_type")
                if not isinstance(current_rt, str) or current_rt in ("", "unknown"):
                    node["resolved_type"] = field_type
                field_fqcn = _resolve_receiver_class_fqcn(
                    field_type,
                    module_id=module.module_id,
                    local_classes=local_classes,
                    import_modules=import_modules,
                    import_symbols=import_symbols,
                    class_storage_hints=class_storage_hints,
                )
                if field_fqcn != "":
                    hint = class_storage_hints.get(field_fqcn, "")
                    if hint in ("ref", "value"):
                        node["resolved_storage_hint"] = hint


def _attach_runtime_iter_target_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    for _, doc in copied_docs:
        for node in _walk_nodes(doc):
            if node.get("kind") != "ForCore":
                continue
            iter_plan = node.get("iter_plan")
            target_plan = node.get("target_plan")
            if not isinstance(iter_plan, dict) or not isinstance(target_plan, dict):
                continue
            if iter_plan.get("kind") != "RuntimeIterForPlan" or target_plan.get("kind") != "NameTarget":
                continue
            iter_expr = iter_plan.get("iter_expr")
            if not isinstance(iter_expr, dict):
                continue
            iter_type = iter_expr.get("resolved_type")
            if not isinstance(iter_type, str) or iter_type == "":
                continue
            if iter_expr.get("iter_element_type") in ("", "unknown", None):
                if iter_type.startswith("list[") and iter_type.endswith("]"):
                    iter_plan["iter_element_type"] = iter_type[5:-1]
            target_type = target_plan.get("target_type")
            elem_type = iter_plan.get("iter_element_type")
            if (not isinstance(target_type, str) or target_type in ("", "unknown")) and isinstance(elem_type, str) and elem_type not in ("", "unknown"):
                target_plan["target_type"] = elem_type


def _attach_for_target_name_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _attach_assign_target_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _collect_class_method_signatures(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, dict[str, dict[str, JsonVal]]]:
    out: dict[str, dict[str, dict[str, JsonVal]]] = {}
    return out


def _collect_module_function_signatures(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, dict[str, JsonVal]]:
    out: dict[str, dict[str, JsonVal]] = {}
    return out


def _attach_function_signature_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _attach_method_signature_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _attach_import_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _propagate_local_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> None:
    return


def _resolve_type_id_target(
    expected_name: str,
    *,
    module_id: str,
    local_classes: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
    type_id_table: dict[str, JsonVal],
) -> str:
    if expected_name == "":
        return ""
    if expected_name in type_id_table:
        return expected_name
    local_fqcn = local_classes.get(expected_name, "")
    if local_fqcn != "" and local_fqcn in type_id_table:
        return local_fqcn
    imported_symbol = import_symbols.get(expected_name, "")
    if imported_symbol != "" and "::" in imported_symbol:
        dep_module_id, export_name = imported_symbol.split("::", 1)
        candidate = dep_module_id.strip() + "." + export_name.strip()
        if candidate in type_id_table:
            return candidate
    if "." in expected_name:
        owner_name, attr_name = expected_name.rsplit(".", 1)
        imported_module = import_modules.get(owner_name, "")
        if imported_module != "":
            candidate2 = imported_module + "." + attr_name
            if candidate2 in type_id_table:
                return candidate2
    candidate3 = module_id + "." + expected_name
    if candidate3 in type_id_table:
        return candidate3
    return ""


def _ensure_symbol_import(meta: dict[str, JsonVal], module_id: str, export_name: str, local_name: str) -> None:
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        bindings = []
        meta["import_bindings"] = bindings
    exists = False
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if binding.get("module_id") == module_id and binding.get("export_name") == export_name and binding.get("local_name") == local_name:
            exists = True
            break
    if not exists:
        bindings.append({
            "module_id": module_id,
            "runtime_module_id": module_id,
            "export_name": export_name,
            "local_name": local_name,
            "binding_kind": "symbol",
        })

    import_symbols = meta.get("import_symbols")
    if not isinstance(import_symbols, dict):
        import_symbols = {}
        meta["import_symbols"] = import_symbols
    import_symbols[local_name] = {"module": module_id, "name": export_name}


def _rewrite_type_id_isinstance(
    module_id: str,
    doc: dict[str, JsonVal],
    type_id_table: dict[str, JsonVal],
    *,
    target: str,
) -> None:
    if target == "cpp":
        return
    import_modules, import_symbols = _import_maps(doc)
    local_classes = _collect_local_class_names(doc, module_id)
    meta = _ensure_meta(doc)
    for node in _walk_nodes(doc):
        if node.get("kind") != "IsInstance":
            continue
        expected_name = node.get("expected_type_name")
        if not isinstance(expected_name, str) or expected_name == "":
            continue
        target_fqcn = _resolve_type_id_target(
            expected_name,
            module_id=module_id,
            local_classes=local_classes,
            import_modules=import_modules,
            import_symbols=import_symbols,
            type_id_table=type_id_table,
        )
        if target_fqcn == "":
            continue
        if target_fqcn == "RuntimeError" or target_fqcn == "ValueError" or target_fqcn == "TypeError" or target_fqcn == "IndexError" or target_fqcn == "KeyError":
            pass
        const_name = _type_id_const_name(target_fqcn)
        value_node = node.get("value")
        new_node: dict[str, JsonVal] = {
            "kind": "Call",
            "resolved_type": "bool",
            "expected_type_name": target_fqcn,
            "func": _make_name("pytra_isinstance", "callable"),
            "args": [
                {"kind": "ObjTypeId", "value": _copy_json(value_node), "resolved_type": "int64"},
                _make_name(const_name, "int64"),
            ],
            "keywords": [],
        }
        for key in list(node.keys()):
            node.pop(key, None)
        for key2, value2 in new_node.items():
            node[key2] = value2
        _ensure_symbol_import(meta, TYPE_ID_RUNTIME_MODULE_ID, "pytra_isinstance", "pytra_isinstance")
        _ensure_symbol_import(meta, TYPE_ID_TABLE_MODULE_ID, const_name, const_name)


def _rewrite_type_id_runtime_id_table(doc: dict[str, JsonVal]) -> None:
    body = doc.get("body")
    if not isinstance(body, list):
        return
    new_body: list[JsonVal] = []
    removed = False
    for stmt in body:
        if not isinstance(stmt, dict):
            new_body.append(stmt)
            continue
        kind = stmt.get("kind")
        if kind != "AnnAssign" and kind != "Assign":
            new_body.append(stmt)
            continue
        target = stmt.get("target")
        if isinstance(target, dict) and target.get("kind") == "Name" and target.get("id") == "id_table":
            removed = True
            continue
        new_body.append(stmt)
    if removed:
        doc["body"] = new_body
        meta = _ensure_meta(doc)
        _ensure_symbol_import(meta, TYPE_ID_TABLE_MODULE_ID, "id_table", "id_table")


def _build_type_id_table_helper_doc(
    dispatch_mode: str,
    type_info_table: dict[str, JsonVal],
) -> dict[str, JsonVal]:
    rows: list[tuple[str, dict[str, int]]] = []
    for fqcn, raw_info in type_info_table.items():
        if not isinstance(fqcn, str) or not isinstance(raw_info, dict):
            continue
        id_val = raw_info.get("id")
        entry = raw_info.get("entry")
        exit_val = raw_info.get("exit")
        if isinstance(id_val, int) and isinstance(entry, int) and isinstance(exit_val, int):
            rows.append((fqcn, {"id": id_val, "entry": entry, "exit": exit_val}))
    rows.sort(key=lambda item: item[1]["id"])

    body: list[dict[str, JsonVal]] = []
    id_table_elements: list[dict[str, JsonVal]] = []
    tid_index = 0
    for fqcn, info in rows:
        id_table_elements.append(_make_constant(info["entry"], "int64"))
        id_table_elements.append(_make_constant(info["exit"] - 1, "int64"))
        body.append({
            "kind": "AnnAssign",
            "target": _make_name(_type_id_const_name(fqcn), "int64"),
            "annotation": "int64",
            "declare": True,
            "decl_type": "int64",
            "value": _make_constant(tid_index, "int64"),
        })
        tid_index += 1

    body.insert(0, {
        "kind": "AnnAssign",
        "target": _make_name("id_table", "list[int64]"),
        "annotation": "list[int64]",
        "declare": True,
        "decl_type": "list[int64]",
        "value": _make_list(id_table_elements, "list[int64]"),
    })

    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "source_path": TYPE_ID_TABLE_SOURCE_PATH,
        "body": body,
        "main_guard_body": [],
        "meta": {
            "module_id": TYPE_ID_TABLE_MODULE_ID,
            "dispatch_mode": dispatch_mode,
            "import_bindings": [],
            "import_modules": {},
            "import_symbols": {},
            "synthetic_helper_v1": {
                "helper_id": TYPE_ID_TABLE_HELPER_ID,
                "owner_module_id": "",
                "generated_by": "linked_optimizer",
            },
        },
    }


def _iter_declared_import_module_ids(doc: dict[str, JsonVal]) -> list[str]:
    meta_val = doc.get("meta")
    if not isinstance(meta_val, dict):
        return []
    out: list[str] = []
    seen: set[str] = set()

    bindings = meta_val.get("import_bindings")
    saw_import_bindings = False
    if isinstance(bindings, list):
        saw_import_bindings = True
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            dep_id = _declared_import_dependency_module_id(binding)
            if dep_id != "" and dep_id not in seen:
                seen.add(dep_id)
                out.append(dep_id)

    if saw_import_bindings:
        return out

    import_modules = meta_val.get("import_modules")
    if isinstance(import_modules, dict):
        for value in import_modules.values():
            if isinstance(value, str):
                mid2 = value.strip()
                if mid2 != "" and mid2 not in seen:
                    seen.add(mid2)
                    out.append(mid2)

    import_symbols = meta_val.get("import_symbols")
    if isinstance(import_symbols, dict):
        for value2 in import_symbols.values():
            if not isinstance(value2, dict):
                continue
            module_id2 = value2.get("module")
            if isinstance(module_id2, str):
                mid3 = module_id2.strip()
                if mid3 != "" and mid3 not in seen:
                    seen.add(mid3)
                    out.append(mid3)

    return out


def _declared_import_dependency_module_id(binding: dict[str, JsonVal]) -> str:
    runtime_module_id = binding.get("runtime_module_id")
    module_id = binding.get("module_id")
    host_only = binding.get("host_only") is True
    binding_kind = binding.get("binding_kind")
    resolved_kind = binding.get("resolved_binding_kind")

    if isinstance(runtime_module_id, str):
        runtime_mid = runtime_module_id.strip()
        if runtime_mid != "":
            if host_only:
                if (binding_kind == "module" or resolved_kind == "module") and runtime_mid.startswith("pytra."):
                    return runtime_mid
                return ""
            return runtime_mid

    if host_only:
        return ""

    if isinstance(module_id, str):
        mid = module_id.strip()
        if mid != "":
            return mid
    return ""


def _validate_link_input_completeness(modules: list[LinkedModule]) -> None:
    provided: set[str] = set()
    for module in modules:
        provided.add(module.module_id)

    missing: dict[str, list[str]] = {}
    for module in modules:
        importer_label = module.source_path if module.source_path != "" else module.module_id
        for dep in _iter_declared_import_module_ids(module.east_doc):
            if dep == module.module_id:
                continue
            if dep in provided or _is_whitelisted_missing_dependency(module, dep):
                continue
            _append_missing_importer(missing, dep, importer_label)

    if len(missing) == 0:
        return

    lines: list[str] = ["link error: unresolved import dependency"]
    for dep in sorted(missing.keys()):
        importers = missing[dep]
        for importer in importers:
            lines.append("  " + importer + " imports " + dep)
            lines.append("  but no link unit provides this module.")
    lines.append("")
    lines.append("  Missing modules:")
    for dep2 in sorted(missing.keys()):
        lines.append("    - " + dep2)
    raise RuntimeError("\n".join(lines))


_TYPE_STRING_KEYS: set[str] = {
    "resolved_type",
    "decl_type",
    "return_type",
    "returns",
    "yield_value_type",
    "annotation",
    "type_expr",
    "iter_element_type",
    "target_type",
    "target",
    "storage_type",
}

_TYPE_MAP_KEYS: set[str] = {
    "arg_types",
    "field_types",
}


def _collect_module_type_aliases(doc: dict[str, JsonVal]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    body = doc.get("body")
    if not isinstance(body, list):
        return aliases
    for stmt in body:
        if not isinstance(stmt, dict) or stmt.get("kind") != "TypeAlias":
            continue
        name = stmt.get("name")
        raw = stmt.get("value")
        if not isinstance(raw, str) or raw == "":
            raw = stmt.get("type_expr")
        if isinstance(name, str) and name != "" and isinstance(raw, str) and raw != "":
            aliases[name] = normalize_type(raw, aliases, {name})
    return aliases


def _default_collection_hint(type_name: str) -> str:
    t = type_name.strip()
    if t.endswith(" | None"):
        t = t[0 : len(t) - 7].strip()
    elif t.endswith("|None"):
        t = t[0 : len(t) - 6].strip()
    if t.startswith("list[") or t.startswith("dict[") or t.startswith("set["):
        return t
    return ""


def _empty_alias_seen() -> set[str]:
    seen: set[str] = set()
    return seen


def _normalize_type_alias(raw: str, aliases: dict[str, str]) -> str:
    return normalize_type(raw, aliases, _empty_alias_seen())


def _apply_collection_hint(node: JsonVal, target_type: str, aliases: dict[str, str]) -> None:
    if not isinstance(node, dict):
        return
    hinted = _default_collection_hint(_normalize_type_alias(target_type, aliases))
    if hinted == "":
        return
    kind = node.get("kind")
    current = node.get("resolved_type")
    current_type = current if isinstance(current, str) else ""
    if kind == "List" and hinted.startswith("list[") and current_type in ("", "unknown", "list[unknown]"):
        node["resolved_type"] = hinted
        return
    if kind == "Dict" and hinted.startswith("dict[") and current_type in ("", "unknown", "dict[unknown,unknown]"):
        node["resolved_type"] = hinted
        return
    if kind == "Set" and hinted.startswith("set[") and current_type in ("", "unknown", "set[unknown]"):
        node["resolved_type"] = hinted
        return


def _normalize_runtime_type_aliases(node: JsonVal, aliases: dict[str, str]) -> None:
    if isinstance(node, list):
        for item in node:
            _normalize_runtime_type_aliases(item, aliases)
        return
    if not isinstance(node, dict):
        return

    for key, value in list(node.items()):
        if key in _TYPE_STRING_KEYS and isinstance(value, str) and value != "":
            node[key] = _normalize_type_alias(value, aliases)
            continue
        if key in _TYPE_MAP_KEYS and isinstance(value, dict):
            normalized_map: dict[str, JsonVal] = {}
            for k, v in value.items():
                if isinstance(v, str):
                    normalized_map[k] = _normalize_type_alias(v, aliases)
                else:
                    normalized_map[k] = v
            node[key] = normalized_map
            continue
        if isinstance(value, dict):
            _normalize_runtime_type_aliases(value, aliases)
            continue
        if isinstance(value, list):
            _normalize_runtime_type_aliases(value, aliases)

    kind = node.get("kind")
    if kind == "TypeAlias":
        raw_alias = node.get("value")
        if isinstance(raw_alias, str) and raw_alias != "":
            node["value"] = _normalize_type_alias(raw_alias, aliases)
        return
    if kind == "FunctionDef":
        arg_types = node.get("arg_types")
        arg_defaults = node.get("arg_defaults")
        if isinstance(arg_types, dict) and isinstance(arg_defaults, dict):
            for name, default_node in arg_defaults.items():
                param_type = arg_types.get(name)
                if isinstance(param_type, str):
                    _apply_collection_hint(default_node, param_type, aliases)
    elif kind in ("Assign", "AnnAssign"):
        target = node.get("target")
        value = node.get("value")
        target_type = ""
        if isinstance(target, dict):
            rt = target.get("resolved_type")
            if isinstance(rt, str):
                target_type = rt
        if target_type == "":
            decl = node.get("decl_type")
            if isinstance(decl, str):
                target_type = decl
        if target_type != "":
            _apply_collection_hint(value, target_type, aliases)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def link_modules(
    entry_east3_paths: list[str],
    *,
    target: str = "cpp",
    dispatch_mode: str = "native",
) -> LinkResult:
    """east3-opt ファイル群を link して manifest + linked modules を返す。

    Args:
        entry_east3_paths: entry module の east3-opt ファイルパス群
        target: 出力ターゲット (e.g. "cpp")
        dispatch_mode: "native" | "type_id"

    Returns:
        LinkResult with manifest dict and linked module list.
    """
    if len(entry_east3_paths) == 0:
        raise RuntimeError("link_modules: at least one entry path is required")

    # 1. entry modules をロード
    module_map: dict[str, dict[str, JsonVal]] = {}
    for path_str in entry_east3_paths:
        p = Path(path_str)
        if not p.exists():
            raise RuntimeError("file not found: " + path_str)
        text = p.read_text(encoding="utf-8")
        doc_obj = json.loads_obj(text)
        if doc_obj is None:
            raise RuntimeError("invalid east3 document: " + path_str)
        doc = doc_obj.raw
        module_map[str(p.resolve())] = doc

    # 2. runtime module を探索・追加 (transitive closure)
    module_map = discover_runtime_modules(module_map, target=target)

    # 3. module_id を割り当て、dispatch_mode を検証
    runtime_east_root = Path(__file__).resolve().parents[2] / "runtime" / "east"

    modules: list[LinkedModule] = []
    entry_resolved: set[str] = set()
    for ep in entry_east3_paths:
        entry_resolved.add(str(Path(ep).resolve()))

    seen_ids: set[str] = set()
    for path_str in _sorted_doc_map_keys(module_map):
        doc_entry = _doc_map_get(module_map, path_str)
        if not isinstance(doc_entry, dict):
            continue

        module_id = _module_id_from_doc(doc_entry, path_str, runtime_east_root)
        if module_id in seen_ids:
            raise RuntimeError("duplicate module_id: " + module_id)
        seen_ids.add(module_id)

        # dispatch_mode 検証
        doc_dm = _dispatch_mode_from_doc(doc_entry)
        if doc_dm != dispatch_mode:
            raise RuntimeError(
                "dispatch_mode mismatch: expected "
                + dispatch_mode
                + " but module "
                + module_id
                + " has "
                + doc_dm
            )

        is_entry = path_str in entry_resolved
        source_path = _source_path_from_doc(doc_entry)

        # runtime module かどうか判定
        module_kind = "user"
        if module_id.startswith("pytra."):
            module_kind = "runtime"

        modules.append(LinkedModule(
            module_id=module_id,
            input_path=path_str,
            source_path=source_path,
            is_entry=is_entry,
            east_doc=doc_entry,
            module_kind=module_kind,
        ))

    # module_id でソート (決定的順序)
    modules = _sorted_modules_by_id(modules)

    # 3.5. import 解決の入力完全性検証
    _validate_link_input_completeness(modules)

    entry_module_ids = sorted([m.module_id for m in modules if m.is_entry])
    if len(entry_module_ids) == 0:
        raise RuntimeError("no entry module found")
    all_module_ids = [m.module_id for m in modules]

    # 4. type_id テーブル構築
    type_id_parts: tuple[JsonVal, JsonVal, JsonVal] = cast(tuple[JsonVal, JsonVal, JsonVal], build_type_id_table(modules))
    type_id_table, type_id_base_map, type_info_table = type_id_parts
    trait_parts: tuple[set[str], dict[str, set[str]]] = build_trait_implementation_map(modules)
    all_traits, trait_impls = trait_parts

    # 5. call graph 構築
    call_graph_parts: tuple[JsonVal, JsonVal] = cast(tuple[JsonVal, JsonVal], build_call_graph(modules))
    call_graph, sccs = call_graph_parts

    # 6. program_id 生成
    pid = _program_id(target, dispatch_mode, all_module_ids)

    # 8. Deep copy all modules
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]] = []
    for module in modules:
        doc_val = _copy_json(module.east_doc)
        if not isinstance(doc_val, dict):
            continue
        doc: dict[str, JsonVal] = doc_val
        aliases = _collect_module_type_aliases(doc)
        if len(aliases) > 0:
            _normalize_runtime_type_aliases(doc, aliases)
        copied_docs.append((module, doc))

    # 9. Cross-module default argument expansion
    all_docs = _docs_as_json(copied_docs)
    expand_cross_module_defaults(all_docs)
    _attach_receiver_storage_hints(copied_docs)
    _attach_resolved_storage_hints(copied_docs)
    _attach_assign_target_hints(copied_docs)
    _attach_runtime_iter_target_hints(copied_docs)
    _attach_for_target_name_hints(copied_docs)
    _attach_attribute_field_hints(copied_docs)
    _attach_function_signature_hints(copied_docs)
    _propagate_local_storage_hints(copied_docs)
    _attach_method_signature_hints(copied_docs)
    _attach_receiver_storage_hints(copied_docs)
    _attach_import_storage_hints(copied_docs)

    # 9.5 exception propagation markers
    direct_raise_markers = _collect_direct_raise_markers(modules)
    propagated_raise_markers = _propagate_can_raise(call_graph, direct_raise_markers)
    _attach_can_raise_markers(copied_docs, propagated_raise_markers)
    _annotate_copy_elision_safe_v1(copied_docs)

    helper_doc = _build_type_id_table_helper_doc(dispatch_mode, type_info_table)
    helper_module = LinkedModule(
        module_id=TYPE_ID_TABLE_MODULE_ID,
        input_path=TYPE_ID_TABLE_INPUT_PATH,
        source_path=TYPE_ID_TABLE_SOURCE_PATH,
        is_entry=False,
        east_doc=helper_doc,
        module_kind="helper",
    )
    copied_docs.append((helper_module, helper_doc))

    for module, doc in copied_docs:
        if module.module_id == TYPE_ID_TABLE_MODULE_ID:
            continue
        if dispatch_mode == "type_id":
            _rewrite_type_id_isinstance(module.module_id, doc, type_id_table, target=target)
        if module.module_id == TYPE_ID_RUNTIME_MODULE_ID:
            _rewrite_type_id_runtime_id_table(doc)

    linked_input_modules: list[LinkedModule] = []
    for module, doc in copied_docs:
        linked_input_modules.append(LinkedModule(
            module_id=module.module_id,
            input_path=module.input_path,
            source_path=module.source_path,
            is_entry=module.is_entry,
            east_doc=doc,
            module_kind=module.module_kind,
        ))

    dependency_parts: tuple[JsonVal, JsonVal] = cast(tuple[JsonVal, JsonVal], build_all_resolved_dependencies(linked_input_modules, target=target))
    resolved_deps = cast(dict[str, list[str]], dependency_parts[0])
    user_deps = cast(dict[str, list[str]], dependency_parts[1])

    # 10. 各 module に linked_program_v1 を注入
    linked_modules: list[LinkedModule] = []
    module_entries: list[dict[str, JsonVal]] = []

    copied_rows = _copy_doc_rows(copied_docs)
    # Re-apply copy-elision annotations on the final linked rows as well.
    # Earlier linker transforms can rewrite nodes after the first pass, so the
    # final emission rows need their own annotation pass.
    _annotate_copy_elision_safe_v1(copied_rows)
    for row in copied_rows:
        module = row[0]
        doc = row[1]
        _fold_trait_predicates(module.module_id, doc, all_traits, trait_impls)
        meta = _ensure_meta(doc)
        meta["emit_context"] = {
            "module_id": module.module_id,
            "is_entry": module.is_entry,
        }
        linked_meta: dict[str, JsonVal] = {
            "program_id": pid,
            "module_id": module.module_id,
            "entry_modules": entry_module_ids,
            "type_id_resolved_v1": type_id_table,
            "type_id_base_map_v1": type_id_base_map,
            "type_info_table_v1": type_info_table,
            "resolved_dependencies_v1": _dep_rows(resolved_deps, module.module_id),
            "user_module_dependencies_v1": _dep_rows(user_deps, module.module_id),
            "non_escape_summary": {},
            "container_ownership_hints_v1": {},
        }
        meta["linked_program_v1"] = linked_meta
        doc["meta"] = meta

        linked_modules.append(LinkedModule(
            module_id=module.module_id,
            input_path=module.input_path,
            source_path=module.source_path,
            is_entry=module.is_entry,
            east_doc=doc,
            module_kind=module.module_kind,
        ))

        me: dict[str, JsonVal] = {
            "module_id": module.module_id,
            "input": module.input_path,
            "output": _linked_output_path(module.module_id),
            "source_path": module.source_path,
            "is_entry": module.is_entry,
            "module_kind": module.module_kind,
        }
        helper_meta = meta.get("synthetic_helper_v1")
        if module.module_kind == "helper" and isinstance(helper_meta, dict):
            helper_id = helper_meta.get("helper_id")
            owner_module_id = helper_meta.get("owner_module_id")
            generated_by = helper_meta.get("generated_by")
            if isinstance(helper_id, str) and helper_id != "":
                me["helper_id"] = helper_id
            if isinstance(owner_module_id, str):
                me["owner_module_id"] = owner_module_id
            if isinstance(generated_by, str) and generated_by != "":
                me["generated_by"] = generated_by
        module_entries.append(me)

    # 9. call_graph dict 変換
    call_graph_map: dict[str, JsonVal] = call_graph
    cg_dict: dict[str, JsonVal] = {}
    for caller in _sorted_str_map_keys(call_graph_map):
        callees = call_graph_map[caller]
        cg_dict[caller] = list(callees)

    sccs_list: list[JsonVal] = []
    for component in sccs:
        sccs_list.append(list(component))

    # 10. manifest (link-output.v1) 構築
    global_section: dict[str, JsonVal] = {
        "type_id_table": type_id_table,
        "type_id_base_map": type_id_base_map,
        "call_graph": cg_dict,
        "sccs": sccs_list,
        "non_escape_summary": {},
        "container_ownership_hints_v1": {},
    }

    manifest: dict[str, JsonVal] = {
        "schema": LINK_OUTPUT_SCHEMA,
        "target": target,
        "dispatch_mode": dispatch_mode,
        "entry_modules": entry_module_ids,
        "modules": module_entries,
        "global": global_section,
        "diagnostics": {"warnings": [], "errors": []},
    }

    return LinkResult(
        manifest=manifest,
        linked_modules=linked_modules,
    )

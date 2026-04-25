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
from toolchain.common.jv import deep_copy_json
from toolchain.link.runtime_discovery import discover_runtime_modules
from toolchain.link.runtime_discovery import resolve_runtime_east_path
from toolchain.link.type_id import build_type_id_table
from toolchain.link.trait_id import build_trait_implementation_map
from toolchain.link.call_graph import build_call_graph
from toolchain.link.dependencies import build_all_resolved_dependencies
from toolchain.link.import_maps import collect_import_maps, collect_import_modules, collect_import_symbols
from toolchain.link.expand_defaults import expand_cross_module_defaults
from toolchain.resolve.py.type_norm import normalize_type
from toolchain.compile.jv import jv_str, jv_int, jv_bool, jv_is_int, jv_is_dict, jv_is_list, jv_dict, jv_list, nd_get_dict, nd_get_list, nd_get_str


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


@dataclass
class EmitContextDraft:
    module_id: str
    is_entry: bool

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "module_id": self.module_id,
            "is_entry": self.is_entry,
        }


@dataclass
class LinkedProgramMetaDraft:
    program_id: str
    module_id: str
    entry_module_ids: list[str]
    type_id_table: JsonVal
    type_id_base_map: JsonVal
    type_info_table: JsonVal
    resolved_dependencies: list[JsonVal]
    user_module_dependencies: list[JsonVal]

    def to_jv(self) -> dict[str, JsonVal]:
        non_escape_summary: dict[str, JsonVal] = {}
        container_ownership_hints: dict[str, JsonVal] = {}
        return {
            "program_id": self.program_id,
            "module_id": self.module_id,
            "entry_modules": _str_list_json(self.entry_module_ids),
            "type_id_resolved_v1": self.type_id_table,
            "type_id_base_map_v1": self.type_id_base_map,
            "type_info_table_v1": self.type_info_table,
            "resolved_dependencies_v1": list(self.resolved_dependencies),
            "user_module_dependencies_v1": list(self.user_module_dependencies),
            "non_escape_summary": non_escape_summary,
            "container_ownership_hints_v1": container_ownership_hints,
        }


@dataclass
class ManifestModuleEntryDraft:
    module_id: str
    input_path: str
    output_path: str
    source_path: str
    is_entry: bool
    module_kind: str
    helper_id: str = ""
    owner_module_id: str = ""
    generated_by: str = ""
    include_owner_module_id: bool = False

    def to_jv(self) -> dict[str, JsonVal]:
        out: dict[str, JsonVal] = {
            "module_id": self.module_id,
            "input": self.input_path,
            "output": self.output_path,
            "source_path": self.source_path,
            "is_entry": self.is_entry,
            "module_kind": self.module_kind,
        }
        if self.helper_id != "":
            out["helper_id"] = self.helper_id
        if self.owner_module_id != "" or self.include_owner_module_id:
            out["owner_module_id"] = self.owner_module_id
        if self.generated_by != "":
            out["generated_by"] = self.generated_by
        return out


@dataclass
class LinkManifestGlobalDraft:
    type_id_table: JsonVal
    type_id_base_map: JsonVal
    call_graph: JsonVal
    sccs: list[JsonVal]

    def to_jv(self) -> dict[str, JsonVal]:
        non_escape_summary: dict[str, JsonVal] = {}
        container_ownership_hints: dict[str, JsonVal] = {}
        return {
            "type_id_table": self.type_id_table,
            "type_id_base_map": self.type_id_base_map,
            "call_graph": self.call_graph,
            "sccs": list(self.sccs),
            "non_escape_summary": non_escape_summary,
            "container_ownership_hints_v1": container_ownership_hints,
        }


@dataclass
class LinkDiagnosticsDraft:
    warnings: list[JsonVal]
    errors: list[JsonVal]

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class LinkManifestDraft:
    target: str
    dispatch_mode: str
    entry_module_ids: list[str]
    module_entries: list[JsonVal]
    global_section: JsonVal
    diagnostics: JsonVal

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "schema": LINK_OUTPUT_SCHEMA,
            "target": self.target,
            "dispatch_mode": self.dispatch_mode,
            "entry_modules": _str_list_json(self.entry_module_ids),
            "modules": list(self.module_entries),
            "global": self.global_section,
            "diagnostics": self.diagnostics,
        }


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

    meta = nd_get_dict(east_doc, "meta")
    mid_val = nd_get_str(meta, "module_id").strip()
    if mid_val != "":
        return _normalize_package_module_id(mid_val)

    source_path_val = nd_get_str(east_doc, "source_path").strip()
    if source_path_val != "":
        source_path_norm = source_path_val.replace("\\", "/")
        _tc2_markers: list[str] = ["src/toolchain2/"]
        for marker in _tc2_markers:
            idx = source_path_norm.find(marker)
            if idx >= 0 and source_path_norm.endswith(".py"):
                rel = "" + source_path_norm[idx + len("src/"):].replace(".py", "")
                module_id = "" + rel.replace("/", ".")
                module_id = _normalize_package_module_id(module_id)
                if module_id != "":
                    return module_id
        if source_path_norm.endswith("src/pytra-cli.py") or source_path_norm == "src/pytra-cli.py":
            return "pytra_cli2"

    resolved_path = Path(file_path).resolve()
    east_root_path = runtime_east_root.resolve()
    try:
        root_prefix = str(east_root_path).replace("\\", "/")
        resolved_prefix = str(resolved_path).replace("\\", "/")
        if not resolved_prefix.startswith(root_prefix + "/"):
            raise ValueError("outside runtime east root")
        rel_str = "" + resolved_prefix[len(root_prefix) + 1 :]
        if rel_str.endswith(".east"):
            rel_str = rel_str.replace(".east", "")
        module_id = "pytra." + rel_str.replace("/", ".")
        module_id = _normalize_package_module_id(module_id)
        if module_id != "":
            return module_id
    except ValueError:
        pass

    path_text = str(Path(file_path)).replace("\\", "/")
    name = "" + path_text.split("/")[-1]
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
    return "" + nd_get_str(east_doc, "source_path")


def _dispatch_mode_from_doc(east_doc: dict[str, JsonVal]) -> str:
    meta = nd_get_dict(east_doc, "meta")
    dm = nd_get_str(meta, "dispatch_mode")
    if dm != "":
        return "" + dm
    return "native"


def _linked_output_path(module_id: str) -> str:
    """linked module の出力相対パスを生成する。"""
    return "east3/" + module_id.replace(".", "/") + ".east3.json"


def _copy_json(val: JsonVal) -> JsonVal:
    return deep_copy_json(val)

def _program_id(
    target: str,
    dispatch_mode: str,
    module_ids: list[str],
) -> str:
    """決定的な program_id を生成する。"""
    return target + ":" + dispatch_mode + ":" + ",".join(sorted(module_ids))


def _ensure_meta(doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """doc の meta を dict として返す (なければ作成)。"""
    meta = nd_get_dict(doc, "meta")
    if len(meta) != 0:
        return meta
    new_meta: dict[str, JsonVal] = {}
    doc["meta"] = new_meta
    return new_meta


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
    return collect_import_modules(doc), collect_import_symbols(doc)


def _set_to_sorted_str_list(values: set[str]) -> list[JsonVal]:
    text_values: list[str] = []
    for value in values:
        text_values.append(value)
    sorted_values = _sorted_str_list(text_values)
    out: list[JsonVal] = []
    for item in sorted_values:
        out.append(item)
    return out


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


def _str_list_json(items: list[str]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for item in items:
        out.append(item)
    return out


def _dep_rows(dep_map: dict[str, list[str]], module_id: str) -> list[JsonVal]:
    if module_id in dep_map:
        return _str_list_json(dep_map[module_id])
    out: list[JsonVal] = []
    return out


def _doc_map_get(module_map: dict[str, dict[str, JsonVal]], path_str: str) -> dict[str, JsonVal]:
    return module_map[path_str]


def _docs_as_json(copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for _module, doc in copied_docs:
        out.append(doc)
    return out


def _walk_nodes(node: JsonVal) -> list[dict[str, JsonVal]]:
    out: list[dict[str, JsonVal]] = []
    if jv_is_dict(node):
        node_dict = jv_dict(node)
        out.append(node_dict)
        for value in node_dict.values():
            for child in _walk_nodes(value):
                out.append(child)
    elif jv_is_list(node):
        for item in jv_list(node):
            for child2 in _walk_nodes(item):
                out.append(child2)
    return out


def _node_str(node: dict[str, JsonVal], key: str) -> str:
    return "" + jv_str(node.get(key))


def _node_list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    return nd_get_list(node, key)


def _json_dict_equal(left: JsonVal, right: dict[str, JsonVal]) -> bool:
    return jv_is_dict(left) and jv_dict(left) == right


def _json_dict_not_equal(left: JsonVal, right: dict[str, JsonVal]) -> bool:
    return not _json_dict_equal(left, right)


def _json_list_item_equal(items: list[JsonVal], index: int, node: dict[str, JsonVal]) -> bool:
    if not (0 <= index < len(items)):
        return False
    item = items[index]
    return jv_is_dict(item) and jv_dict(item) == node


def _walk_nodes_with_parents(
    node: JsonVal,
    parents: list[dict[str, JsonVal]],
) -> list[tuple[dict[str, JsonVal], list[dict[str, JsonVal]]]]:
    out: list[tuple[dict[str, JsonVal], list[dict[str, JsonVal]]]] = []
    if jv_is_dict(node):
        node_dict = jv_dict(node)
        out.append((node_dict, parents))
        next_parents = list(parents)
        next_parents.append(node_dict)
        for value in node_dict.values():
            for child in _walk_nodes_with_parents(value, next_parents):
                out.append(child)
    elif jv_is_list(node):
        for item in jv_list(node):
            for child2 in _walk_nodes_with_parents(item, parents):
                out.append(child2)
    return out


def _ensure_node_meta(node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    meta_val = node.get("meta")
    if jv_is_dict(meta_val):
        return jv_dict(meta_val)
    meta: dict[str, JsonVal] = {}
    node["meta"] = meta
    return meta


def _is_name_with_id(node: JsonVal, name: str) -> bool:
    if not jv_is_dict(node):
        return False
    node_dict = jv_dict(node)
    return _node_str(node_dict, "kind") == "Name" and _node_str(node_dict, "id") == name


def _is_bytes_from_local_bytearray_call(node: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]] | None:
    if _node_str(node, "kind") != "Call":
        return None
    func = nd_get_dict(node, "func")
    args = _node_list(node, "args")
    if _node_str(func, "kind") != "Name" or _node_str(func, "id") != "bytes":
        return None
    if len(args) != 1 or not jv_is_dict(args[0]):
        return None
    arg = jv_dict(args[0])
    if _node_str(arg, "kind") != "Name" or _node_str(arg, "resolved_type") != "bytearray":
        return None
    source_name = _node_str(arg, "id")
    if source_name == "":
        return None
    return (source_name, arg)


def _top_level_function_map(doc: dict[str, JsonVal]) -> dict[str, dict[str, JsonVal]]:
    out: dict[str, dict[str, JsonVal]] = {}
    for stmt in _node_list(doc, "body"):
        if not jv_is_dict(stmt):
            continue
        stmt_dict = jv_dict(stmt)
        kind = _node_str(stmt_dict, "kind")
        if kind != "FunctionDef" and kind != "ClosureDef":
            continue
        name = _node_str(stmt_dict, "name")
        if name == "":
            continue
        out[name] = stmt_dict
    return out


def _copy_elision_return_candidate(func_node: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
    for stmt in _node_list(func_node, "body"):
        if not jv_is_dict(stmt):
            continue
        stmt_dict = jv_dict(stmt)
        if _node_str(stmt_dict, "kind") != "Return":
            continue
        value = stmt_dict.get("value")
        if not jv_is_dict(value):
            continue
        hit = _is_bytes_from_local_bytearray_call(jv_dict(value))
        if hit is not None:
            value_dict: dict[str, JsonVal] = jv_dict(value)
            return value_dict
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
    func = nd_get_dict(call_node, "func")
    if _node_str(func, "kind") != "Attribute" or _node_str(func, "attr") != "append":
        return None
    owner_val = func.get("value")
    if not jv_is_dict(owner_val):
        return None
    owner = jv_dict(owner_val)
    if _node_str(owner, "kind") != "Name":
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
    if jv_is_dict(sig):
        sig_dict = jv_dict(sig)
        arg_order_val = sig_dict.get("arg_order")
        arg_usage_val = sig_dict.get("arg_usage")
        if jv_is_list(arg_order_val) and jv_is_dict(arg_usage_val):
            arg_order = jv_list(arg_order_val)
            arg_usage = jv_dict(arg_usage_val)
            args = _node_list(call_node, "args")
            i = 0
            while i < len(args):
                if _json_list_item_equal(args, i, arg_node):
                    if i >= len(arg_order):
                        return False
                    arg_name = "" + jv_str(arg_order[i])
                    if arg_name == "":
                        return False
                    return jv_str(arg_usage.get(arg_name)) == "readonly"
                i += 1

            keywords = _node_list(call_node, "keywords")
            for kw in keywords:
                if not jv_is_dict(kw):
                    continue
                kw_dict = jv_dict(kw)
                if _json_dict_not_equal(kw_dict.get("value"), arg_node):
                    continue
                kw_arg_name = "" + _node_str(kw_dict, "arg")
                if kw_arg_name == "":
                    return False
                return jv_str(arg_usage.get(kw_arg_name)) == "readonly"
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
    func = nd_get_dict(call_node, "func")
    if _node_str(func, "kind") != "Name":
        return False
    callee_name = _node_str(func, "id")
    if callee_name == "" or callee_name not in funcs:
        return False
    callee = funcs[callee_name]
    arg_order_val = callee.get("arg_order")
    arg_usage_val = callee.get("arg_usage")
    if not jv_is_list(arg_order_val) or not jv_is_dict(arg_usage_val):
        return False
    arg_order = jv_list(arg_order_val)
    arg_usage = jv_dict(arg_usage_val)
    args = _node_list(call_node, "args")
    i = 0
    while i < len(args):
        if _json_list_item_equal(args, i, arg_node):
            if i >= len(arg_order):
                return False
            arg_name = "" + jv_str(arg_order[i])
            if arg_name == "":
                return False
            return jv_str(arg_usage.get(arg_name)) == "readonly"
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
        func_val = direct_parent.get("func")
        if not jv_is_dict(func_val):
            return False
        func = jv_dict(func_val)
        if _node_str(func, "kind") != "Attribute":
            return False
        if not _is_name_with_id(func.get("value"), _node_str(name_node, "id")):
            return False
        hit = _is_list_append_call_on_name(direct_parent)
        return hit is not None
    if _node_str(direct_parent, "kind") != "Attribute":
        return False
    if _json_dict_not_equal(direct_parent.get("value"), name_node):
        return False
    outer_parents: list[dict[str, JsonVal]] = []
    limit = len(parents) - 1
    i = 0
    while i < limit:
        outer_parents.append(parents[i])
        i += 1
    outer = _find_direct_parent(outer_parents)
    if outer is None:
        return False
    outer_node: dict[str, JsonVal] = outer
    if _node_str(outer_node, "kind") != "Call":
        return False
    hit = _is_list_append_call_on_name(outer_node)
    return hit is not None


def _name_is_readonly_subscript_owner(
    name_node: dict[str, JsonVal],
    parents: list[dict[str, JsonVal]],
) -> bool:
    direct_parent = _find_direct_parent(parents)
    if direct_parent is None:
        return False
    parent_node: dict[str, JsonVal] = direct_parent
    if _node_str(parent_node, "kind") != "Subscript":
        return False
    return _json_dict_equal(parent_node.get("value"), name_node)


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
    target_val = direct_parent.get("target")
    if not jv_is_dict(target_val):
        return ""
    target = jv_dict(target_val)
    if _node_str(target, "kind") != "Name":
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
        direct_kind = ""
        if direct_parent is not None:
            direct_kind = _node_str(direct_parent, "kind")
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
            return_candidate = _copy_elision_return_candidate(func_node)
            if return_candidate is not None:
                candidate_calls[module.module_id + "::" + func_name] = return_candidate

    for candidate_key in _sorted_str_list(list(candidate_calls.keys())):
        sep = candidate_key.find("::")
        if sep < 0:
            continue
        module_id = candidate_key[:sep]
        func_name = candidate_key[sep + 2 :]
        candidate_node: dict[str, JsonVal] = candidate_calls[candidate_key]
        hit = _is_bytes_from_local_bytearray_call(candidate_node)
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
                    func = nd_get_dict(node, "func")
                    if _node_str(func, "kind") != "Name" or _node_str(func, "id") != func_name:
                        continue
                    if _json_dict_equal(node, candidate_node):
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
                    outer_call_node: dict[str, JsonVal] = outer_call
                    list_hit = _is_list_append_call_on_name(outer_call_node)
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

        meta = _ensure_node_meta(candidate_node)
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
    if jv_is_dict(node):
        node_dict = jv_dict(node)
        kind = _node_str(node_dict, "kind")
        if kind == "Raise":
            exc_val = node_dict.get("exc")
            if jv_is_dict(exc_val):
                exc = jv_dict(exc_val)
                if _node_str(exc, "kind") == "Call":
                    func_val = exc.get("func")
                    if jv_is_dict(func_val):
                        func = jv_dict(func_val)
                        func_id = _node_str(func, "id")
                        if func_id != "":
                            out.add(func_id)
                rt = _node_str(exc, "resolved_type")
                if rt != "":
                    out.add(rt)
        if kind == "FunctionDef" or kind == "ClosureDef" or kind == "ClassDef":
            return out
        for value in node_dict.values():
            child = _raise_types_in_node(value)
            for item in child:
                out.add(item)
    elif jv_is_list(node):
        for item2 in jv_list(node):
            child2 = _raise_types_in_node(item2)
            for item3 in child2:
                out.add(item3)
    return out


def _collect_direct_raise_markers(modules: list[LinkedModule]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for module in modules:
        body = _node_list(module.east_doc, "body")
        for stmt in body:
            if not jv_is_dict(stmt):
                continue
            stmt_dict = jv_dict(stmt)
            kind = _node_str(stmt_dict, "kind")
            if kind == "FunctionDef":
                name = _node_str(stmt_dict, "name")
                if name != "":
                    raised = _raise_types_in_node(stmt_dict.get("body"))
                    if len(raised) > 0:
                        out[module.module_id + "::" + name] = raised
            elif kind == "ClassDef":
                class_name = _node_str(stmt_dict, "name")
                class_body = _node_list(stmt_dict, "body")
                if class_name == "" or len(class_body) == 0:
                    continue
                for method in class_body:
                    if not jv_is_dict(method):
                        continue
                    method_dict = jv_dict(method)
                    if _node_str(method_dict, "kind") != "FunctionDef":
                        continue
                    method_name = _node_str(method_dict, "name")
                    if method_name != "":
                        raised2 = _raise_types_in_node(method_dict.get("body"))
                        if len(raised2) > 0:
                            out[module.module_id + "::" + class_name + "." + method_name] = raised2
        main_guard = module.east_doc.get("main_guard_body")
        if jv_is_list(main_guard):
            raised3 = _raise_types_in_node(main_guard)
            if len(raised3) > 0:
                out[module.module_id + "::__main__"] = raised3
    return out


def _propagate_can_raise(
    graph: dict[str, list[str]],
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
        body = _node_list(doc, "body")
        for stmt in body:
            if not jv_is_dict(stmt):
                continue
            stmt_dict = jv_dict(stmt)
            kind = _node_str(stmt_dict, "kind")
            if kind == "FunctionDef":
                name = _node_str(stmt_dict, "name")
                if name != "":
                    qualified = module.module_id + "::" + name
                    excs = can_raise.get(qualified, set())
                    if len(excs) > 0:
                        meta = _ensure_meta(stmt_dict)
                        can_raise_meta: dict[str, JsonVal] = {}
                        can_raise_meta["schema_version"] = 1
                        can_raise_meta["exception_types"] = _set_to_sorted_str_list(excs)
                        meta["can_raise_v1"] = can_raise_meta
            elif kind == "ClassDef":
                class_name = _node_str(stmt_dict, "name")
                class_body = _node_list(stmt_dict, "body")
                if class_name == "" or len(class_body) == 0:
                    continue
                for method in class_body:
                    if not jv_is_dict(method):
                        continue
                    method_dict = jv_dict(method)
                    if _node_str(method_dict, "kind") != "FunctionDef":
                        continue
                    method_name = _node_str(method_dict, "name")
                    if method_name != "":
                        qualified2 = module.module_id + "::" + class_name + "." + method_name
                        excs2 = can_raise.get(qualified2, set())
                        if len(excs2) > 0:
                            meta2 = _ensure_meta(method_dict)
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
    body = _node_list(doc, "body")
    for item in body:
        if not jv_is_dict(item):
            continue
        item_dict = jv_dict(item)
        if _node_str(item_dict, "kind") != "ClassDef":
            continue
        meta = nd_get_dict(item_dict, "meta")
        trait_meta = nd_get_dict(meta, "trait_v1")
        if len(trait_meta) == 0:
            continue
        class_name = _node_str(item_dict, "name")
        if class_name != "":
            local_traits[class_name] = module_id + "." + class_name

    for node in _walk_nodes(doc):
        if _node_str(node, "kind") != "IsInstance":
            continue
        expected_name = _node_str(node, "expected_type_name")
        if expected_name == "":
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
        if jv_is_dict(value_node):
            value_type = _node_str(jv_dict(value_node), "resolved_type").strip()
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
    if len(result) > 0 and "0" <= result[0] and result[0] <= "9":
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
    element_values: list[JsonVal] = []
    for element in elements:
        element_values.append(element)
    node: dict[str, JsonVal] = {}
    node["kind"] = "List"
    node["elements"] = element_values
    node["resolved_type"] = resolved_type
    return node


def _collect_local_class_names(doc: dict[str, JsonVal], module_id: str) -> dict[str, str]:
    out: dict[str, str] = {}
    body = _node_list(doc, "body")
    for item in body:
        if not jv_is_dict(item):
            continue
        item_dict = jv_dict(item)
        if _node_str(item_dict, "kind") != "ClassDef":
            continue
        name = _node_str(item_dict, "name")
        if name != "":
            out[name] = module_id + "." + name
    return out


def _collect_class_storage_hints(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for module, doc in copied_docs:
        body = _node_list(doc, "body")
        for item in body:
            if not jv_is_dict(item):
                continue
            item_dict = jv_dict(item)
            if _node_str(item_dict, "kind") != "ClassDef":
                continue
            name = _node_str(item_dict, "name")
            if name == "":
                continue
            hint = _node_str(item_dict, "class_storage_hint")
            if hint == "":
                hint = "value"
            out[module.module_id + "." + name] = hint
    return out


def _collect_class_field_types(
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]],
) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for module, doc in copied_docs:
        body = _node_list(doc, "body")
        for item in body:
            if not jv_is_dict(item):
                continue
            item_dict = jv_dict(item)
            if _node_str(item_dict, "kind") != "ClassDef":
                continue
            name = _node_str(item_dict, "name")
            field_types = nd_get_dict(item_dict, "field_types")
            if name == "" or len(field_types) == 0:
                continue
            typed_fields: dict[str, str] = {}
            for field_name in field_types.keys():
                field_type = "" + jv_str(field_types[field_name])
                if field_name != "" and field_type != "":
                    typed_fields[field_name] = "" + field_type
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
        sep = imported_symbol.find("::")
        dep_module_id = imported_symbol[:sep].strip()
        export_name = imported_symbol[sep + 2:].strip()
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
            return "" + candidate
    if "." in expected_name:
        last_dot = -1
        i = len(expected_name) - 1
        while i >= 0:
            if expected_name[i] == ".":
                last_dot = i
                break
            i -= 1
        owner_name = expected_name[:last_dot]
        attr_name = expected_name[last_dot + 1:]
        imported_module = import_modules.get(owner_name, "")
        if imported_module != "":
            candidates: list[str] = []
            candidates.append(imported_module + "." + attr_name)
            if "." not in imported_module:
                candidates.append("pytra.std." + imported_module + "." + attr_name)
            for candidate2 in candidates:
                if candidate2 in class_storage_hints:
                    return "" + candidate2
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
            kind = _node_str(node, "kind")
            receiver_node: dict[str, JsonVal] = {}
            has_receiver = False
            if kind == "Attribute":
                value = node.get("value")
                if jv_is_dict(value):
                    receiver_node = jv_dict(value)
                    has_receiver = True
            elif kind == "Call":
                func_val = node.get("func")
                if jv_is_dict(func_val):
                    func = jv_dict(func_val)
                    if _node_str(func, "kind") == "Attribute":
                        value2 = func.get("value")
                        if jv_is_dict(value2):
                            receiver_node = jv_dict(value2)
                            has_receiver = True
            if not has_receiver:
                continue
            receiver_type = _node_str(receiver_node, "resolved_type")
            if receiver_type == "":
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
                hint = _node_str(receiver_node, "resolved_storage_hint")
                if hint == "ref" or hint == "value":
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
            resolved_type = _node_str(node, "resolved_type")
            if resolved_type == "":
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
            if _node_str(node, "kind") != "Attribute":
                continue
            value = node.get("value")
            if not jv_is_dict(value):
                continue
            value_dict = jv_dict(value)
            attr = _node_str(node, "attr")
            if attr == "":
                continue
            receiver_type = _node_str(value_dict, "resolved_type")
            if receiver_type == "":
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
                current_rt = _node_str(node, "resolved_type")
                if current_rt == "" or current_rt == "unknown":
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
            if _node_str(node, "kind") != "ForCore":
                continue
            iter_plan = nd_get_dict(node, "iter_plan")
            target_plan = nd_get_dict(node, "target_plan")
            if _node_str(iter_plan, "kind") != "RuntimeIterForPlan" or _node_str(target_plan, "kind") != "NameTarget":
                continue
            iter_expr = nd_get_dict(iter_plan, "iter_expr")
            if len(iter_expr) == 0:
                continue
            iter_type = _node_str(iter_expr, "resolved_type")
            if iter_type == "":
                continue
            iter_element_type = _node_str(iter_expr, "iter_element_type")
            if iter_element_type == "" or iter_element_type == "unknown":
                if iter_type.startswith("list[") and iter_type.endswith("]"):
                    iter_plan["iter_element_type"] = iter_type[5:-1]
            target_type = _node_str(target_plan, "target_type")
            elem_type = _node_str(iter_plan, "iter_element_type")
            if (target_type == "" or target_type == "unknown") and elem_type != "" and elem_type != "unknown":
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
        sep = imported_symbol.find("::")
        dep_module_id = imported_symbol[:sep].strip()
        export_name = imported_symbol[sep + 2:].strip()
        candidate = dep_module_id + "." + export_name
        if candidate in type_id_table:
            return candidate
    if "." in expected_name:
        last_dot = -1
        i = len(expected_name) - 1
        while i >= 0:
            if expected_name[i] == ".":
                last_dot = i
                break
            i -= 1
        owner_name = expected_name[:last_dot]
        attr_name = expected_name[last_dot + 1:]
        imported_module = import_modules.get(owner_name, "")
        if imported_module != "":
            candidate2 = imported_module + "." + attr_name
            if candidate2 in type_id_table:
                return "" + candidate2
    candidate3 = module_id + "." + expected_name
    if candidate3 in type_id_table:
        return candidate3
    return ""


def _ensure_symbol_import(meta: dict[str, JsonVal], module_id: str, export_name: str, local_name: str) -> None:
    bindings_val = meta.get("import_bindings")
    bindings: list[JsonVal] = []
    if jv_is_list(bindings_val):
        bindings = jv_list(bindings_val)
    else:
        meta["import_bindings"] = bindings
    exists = False
    for binding_val in bindings:
        if not jv_is_dict(binding_val):
            continue
        binding = jv_dict(binding_val)
        if _node_str(binding, "module_id") == module_id and _node_str(binding, "export_name") == export_name and _node_str(binding, "local_name") == local_name:
            exists = True
            break
    if not exists:
        binding2: dict[str, JsonVal] = {}
        binding2["module_id"] = module_id
        binding2["runtime_module_id"] = module_id
        binding2["export_name"] = export_name
        binding2["local_name"] = local_name
        binding2["binding_kind"] = "symbol"
        bindings.append(binding2)

    import_symbols_val = meta.get("import_symbols")
    import_symbols: dict[str, JsonVal] = {}
    if jv_is_dict(import_symbols_val):
        import_symbols = jv_dict(import_symbols_val)
    else:
        meta["import_symbols"] = import_symbols
    symbol_info: dict[str, JsonVal] = {}
    symbol_info["module"] = module_id
    symbol_info["name"] = export_name
    import_symbols[local_name] = symbol_info


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
        if _node_str(node, "kind") != "IsInstance":
            continue
        expected_name = _node_str(node, "expected_type_name")
        if expected_name == "":
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
        obj_type_id: dict[str, JsonVal] = {}
        obj_type_id["kind"] = "ObjTypeId"
        obj_type_id["value"] = _copy_json(value_node)
        obj_type_id["resolved_type"] = "int64"
        args: list[JsonVal] = []
        args.append(obj_type_id)
        args.append(_make_name(const_name, "int64"))
        keywords: list[JsonVal] = []
        new_node: dict[str, JsonVal] = {}
        new_node["kind"] = "Call"
        new_node["resolved_type"] = "bool"
        new_node["expected_type_name"] = target_fqcn
        new_node["func"] = _make_name("pytra_isinstance", "callable")
        new_node["args"] = args
        new_node["keywords"] = keywords
        for key in list(node.keys()):
            node.pop(key, None)
        for key2, value2 in new_node.items():
            node[key2] = value2
        _ensure_symbol_import(meta, TYPE_ID_RUNTIME_MODULE_ID, "pytra_isinstance", "pytra_isinstance")
        _ensure_symbol_import(meta, TYPE_ID_TABLE_MODULE_ID, const_name, const_name)


def _rewrite_type_id_runtime_id_table(doc: dict[str, JsonVal]) -> None:
    body = _node_list(doc, "body")
    if len(body) == 0:
        return
    new_body: list[JsonVal] = []
    removed = False
    for stmt in body:
        if not jv_is_dict(stmt):
            new_body.append(stmt)
            continue
        stmt_dict = jv_dict(stmt)
        kind = _node_str(stmt_dict, "kind")
        if kind != "AnnAssign" and kind != "Assign":
            new_body.append(stmt)
            continue
        target = stmt_dict.get("target")
        if jv_is_dict(target):
            target_dict = jv_dict(target)
            if _node_str(target_dict, "kind") == "Name" and _node_str(target_dict, "id") == "id_table":
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
    rows: list[dict[str, JsonVal]] = []
    for fqcn, raw_info in type_info_table.items():
        if fqcn == "" or not jv_is_dict(raw_info):
            continue
        info_dict = jv_dict(raw_info)
        id_val = info_dict.get("id")
        entry = info_dict.get("entry")
        exit_val = info_dict.get("exit")
        if jv_is_int(id_val) and jv_is_int(entry) and jv_is_int(exit_val):
            row_info: dict[str, JsonVal] = {}
            row_info["fqcn"] = fqcn
            row_info["id"] = id_val
            row_info["entry"] = entry
            row_info["exit"] = exit_val
            rows.append(row_info)
    i = 0
    while i < len(rows):
        j = i + 1
        while j < len(rows):
            if jv_int(rows[j].get("id")) < jv_int(rows[i].get("id")):
                tmp = rows[i]
                rows[i] = rows[j]
                rows[j] = tmp
            j += 1
        i += 1

    body: list[JsonVal] = []
    id_table_elements: list[JsonVal] = []
    tid_index = 0
    for info in rows:
        fqcn = "" + jv_str(info.get("fqcn"))
        entry_num = 0 + jv_int(info.get("entry"))
        exit_num = 0 + jv_int(info.get("exit"))
        id_table_elements.append(_make_constant(entry_num, "int64"))
        id_table_elements.append(_make_constant(exit_num - 1, "int64"))
        const_assign: dict[str, JsonVal] = {}
        const_assign["kind"] = "AnnAssign"
        const_assign["target"] = _make_name(_type_id_const_name(fqcn), "int64")
        const_assign["annotation"] = "int64"
        const_assign["declare"] = True
        const_assign["decl_type"] = "int64"
        const_assign["value"] = _make_constant(tid_index, "int64")
        body.append(const_assign)
        tid_index += 1

    id_table_assign: dict[str, JsonVal] = {}
    id_table_assign["kind"] = "AnnAssign"
    id_table_assign["target"] = _make_name("id_table", "list[int64]")
    id_table_assign["annotation"] = "list[int64]"
    id_table_assign["declare"] = True
    id_table_assign["decl_type"] = "list[int64]"
    id_table_assign["value"] = _make_list(id_table_elements, "list[int64]")
    body.insert(0, id_table_assign)

    synthetic_helper: dict[str, JsonVal] = {}
    synthetic_helper["helper_id"] = TYPE_ID_TABLE_HELPER_ID
    synthetic_helper["owner_module_id"] = ""
    synthetic_helper["generated_by"] = "linked_optimizer"

    import_bindings: list[JsonVal] = []
    import_modules: dict[str, JsonVal] = {}
    import_symbols: dict[str, JsonVal] = {}
    meta: dict[str, JsonVal] = {}
    meta["module_id"] = TYPE_ID_TABLE_MODULE_ID
    meta["dispatch_mode"] = dispatch_mode
    meta["import_bindings"] = import_bindings
    meta["import_modules"] = import_modules
    meta["import_symbols"] = import_symbols
    meta["synthetic_helper_v1"] = synthetic_helper

    main_guard_body: list[JsonVal] = []
    doc: dict[str, JsonVal] = {}
    doc["kind"] = "Module"
    doc["east_stage"] = 3
    doc["schema_version"] = 1
    doc["source_path"] = TYPE_ID_TABLE_SOURCE_PATH
    doc["body"] = body
    doc["main_guard_body"] = main_guard_body
    doc["meta"] = meta
    return doc


def _iter_declared_import_module_ids(doc: dict[str, JsonVal]) -> list[str]:
    meta_val = doc.get("meta")
    if not jv_is_dict(meta_val):
        return []
    meta = jv_dict(meta_val)
    out: list[str] = []
    seen: set[str] = set()

    bindings = meta.get("import_bindings")
    saw_import_bindings = False
    if jv_is_list(bindings):
        saw_import_bindings = True
        for binding in jv_list(bindings):
            if not jv_is_dict(binding):
                continue
            dep_id = _declared_import_dependency_module_id(jv_dict(binding))
            if dep_id != "" and dep_id not in seen:
                seen.add(dep_id)
                out.append(dep_id)

    if saw_import_bindings:
        return out

    import_modules = meta.get("import_modules")
    if jv_is_dict(import_modules):
        import_modules_dict = jv_dict(import_modules)
        for key in import_modules_dict.keys():
            mid2 = "" + jv_str(import_modules_dict.get(key)).strip()
            if mid2 != "" and mid2 not in seen:
                seen.add(mid2)
                out.append(mid2)

    import_symbols = meta.get("import_symbols")
    if jv_is_dict(import_symbols):
        import_symbols_dict = jv_dict(import_symbols)
        for key2 in import_symbols_dict.keys():
            value2 = import_symbols_dict.get(key2)
            if not jv_is_dict(value2):
                continue
            module_id2 = jv_dict(value2).get("module")
            mid3 = "" + jv_str(module_id2).strip()
            if mid3 != "" and mid3 not in seen:
                seen.add(mid3)
                out.append(mid3)

    return out


def _declared_import_dependency_module_id(binding: dict[str, JsonVal]) -> str:
    runtime_mid = "" + jv_str(binding.get("runtime_module_id")).strip()
    module_id = "" + jv_str(binding.get("module_id")).strip()
    host_only = jv_bool(binding.get("host_only"))
    binding_kind = "" + jv_str(binding.get("binding_kind"))
    resolved_kind = "" + jv_str(binding.get("resolved_binding_kind"))

    if runtime_mid != "":
        if host_only:
            if (binding_kind == "module" or resolved_kind == "module") and runtime_mid.startswith("pytra."):
                return runtime_mid
            return ""
        return runtime_mid

    if host_only:
        return ""

    if module_id != "":
        return module_id
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
    body_val = doc.get("body")
    if not jv_is_list(body_val):
        return aliases
    for stmt in jv_list(body_val):
        if not jv_is_dict(stmt):
            continue
        stmt_dict = jv_dict(stmt)
        if _node_str(stmt_dict, "kind") != "TypeAlias":
            continue
        name = "" + _node_str(stmt_dict, "name")
        raw = "" + _node_str(stmt_dict, "value")
        if raw == "":
            raw = "" + _node_str(stmt_dict, "type_expr")
        if name != "" and raw != "":
            aliases[name] = "" + normalize_type(raw, aliases, {name})
    return aliases


def _linker_default_collection_hint(type_name: str) -> str:
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
    return "" + normalize_type(raw, aliases, _empty_alias_seen())


def _apply_collection_hint(node: JsonVal, target_type: str, aliases: dict[str, str]) -> None:
    if not jv_is_dict(node):
        return
    node_dict = jv_dict(node)
    hinted = _linker_default_collection_hint(_normalize_type_alias(target_type, aliases))
    if hinted == "":
        return
    kind = "" + _node_str(node_dict, "kind")
    current_type = "" + _node_str(node_dict, "resolved_type")
    if kind == "List" and hinted.startswith("list[") and current_type in ("", "unknown", "list[unknown]"):
        node_dict["resolved_type"] = hinted
        return
    if kind == "Dict" and hinted.startswith("dict[") and current_type in ("", "unknown", "dict[unknown,unknown]"):
        node_dict["resolved_type"] = hinted
        return
    if kind == "Set" and hinted.startswith("set[") and current_type in ("", "unknown", "set[unknown]"):
        node_dict["resolved_type"] = hinted
        return


def _normalize_runtime_type_aliases(node: JsonVal, aliases: dict[str, str]) -> None:
    if jv_is_list(node):
        for item in jv_list(node):
            _normalize_runtime_type_aliases(item, aliases)
        return
    if not jv_is_dict(node):
        return

    node_dict = jv_dict(node)
    for key in list(node_dict.keys()):
        value: JsonVal = node_dict.get(key)
        if key in _TYPE_STRING_KEYS:
            text_value = "" + jv_str(value)
            if text_value != "":
                node_dict[key] = _normalize_type_alias(text_value, aliases)
                continue
        if key in _TYPE_MAP_KEYS and jv_is_dict(value):
            value_dict = jv_dict(value)
            normalized_map: dict[str, JsonVal] = {}
            for map_key in value_dict.keys():
                map_value: JsonVal = value_dict.get(map_key)
                map_text = "" + jv_str(map_value)
                if map_text != "":
                    normalized_map[map_key] = _normalize_type_alias(map_text, aliases)
                else:
                    normalized_map[map_key] = map_value
            node_dict[key] = normalized_map
            continue
        if jv_is_dict(value):
            _normalize_runtime_type_aliases(value, aliases)
            continue
        if jv_is_list(value):
            _normalize_runtime_type_aliases(value, aliases)

    kind = "" + _node_str(node_dict, "kind")
    if kind == "TypeAlias":
        raw_alias = "" + _node_str(node_dict, "value")
        if raw_alias != "":
            node_dict["value"] = _normalize_type_alias(raw_alias, aliases)
        return
    if kind == "FunctionDef":
        arg_types = node_dict.get("arg_types")
        arg_defaults = node_dict.get("arg_defaults")
        if jv_is_dict(arg_types) and jv_is_dict(arg_defaults):
            arg_types_dict = jv_dict(arg_types)
            arg_defaults_dict = jv_dict(arg_defaults)
            for name in arg_defaults_dict.keys():
                default_node: JsonVal = arg_defaults_dict.get(name)
                param_type = "" + jv_str(arg_types_dict.get(name))
                if param_type != "":
                    _apply_collection_hint(default_node, param_type, aliases)
    elif kind == "Assign" or kind == "AnnAssign":
        target: JsonVal = node_dict.get("target")
        value: JsonVal = node_dict.get("value")
        target_type = ""
        if jv_is_dict(target):
            target_type = "" + _node_str(jv_dict(target), "resolved_type")
        if target_type == "":
            target_type = "" + _node_str(node_dict, "decl_type")
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
    linker_file = str(Path(__file__).resolve()).replace("\\", "/")
    linker_suffix = "/toolchain/link/linker.py"
    if linker_file.endswith(linker_suffix):
        runtime_east_root = Path(linker_file[0 : len(linker_file) - len(linker_suffix)] + "/runtime/east")
    else:
        runtime_east_root = Path("src/runtime/east")

    modules: list[LinkedModule] = []
    entry_resolved: set[str] = set()
    for ep in entry_east3_paths:
        entry_resolved.add(str(Path(ep).resolve()))

    seen_ids: set[str] = set()
    for path_str in _sorted_doc_map_keys(module_map):
        doc_entry_val: JsonVal = _doc_map_get(module_map, path_str)
        if not jv_is_dict(doc_entry_val):
            continue
        doc_entry = jv_dict(doc_entry_val)

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

    entry_module_ids: list[str] = []
    all_module_ids: list[str] = []
    for m in modules:
        all_module_ids.append(m.module_id)
        if m.is_entry:
            entry_module_ids.append(m.module_id)
    entry_module_ids.sort()
    if len(entry_module_ids) == 0:
        raise RuntimeError("no entry module found")

    # 4. type_id テーブル構築
    type_id_parts = build_type_id_table(modules)
    type_id_table, type_id_base_map, type_info_table = type_id_parts
    trait_parts = build_trait_implementation_map(modules)
    all_traits, trait_impls = trait_parts

    # 5. call graph 構築
    call_graph, sccs = build_call_graph(modules)

    # 6. program_id 生成
    pid = _program_id(target, dispatch_mode, all_module_ids)

    # 8. Deep copy all modules
    copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]] = []
    for module in modules:
        doc_val: JsonVal = _copy_json(module.east_doc)
        if not jv_is_dict(doc_val):
            continue
        doc: dict[str, JsonVal] = jv_dict(doc_val)
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

    resolved_deps, user_deps = build_all_resolved_dependencies(linked_input_modules, target=target)

    # 10. 各 module に linked_program_v1 を注入
    linked_modules: list[LinkedModule] = []
    module_entries: list[JsonVal] = []

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
        meta["emit_context"] = EmitContextDraft(
            module_id=module.module_id,
            is_entry=module.is_entry,
        ).to_jv()

        meta["linked_program_v1"] = LinkedProgramMetaDraft(
            program_id=pid,
            module_id=module.module_id,
            entry_module_ids=entry_module_ids,
            type_id_table=type_id_table,
            type_id_base_map=type_id_base_map,
            type_info_table=type_info_table,
            resolved_dependencies=_dep_rows(resolved_deps, module.module_id),
            user_module_dependencies=_dep_rows(user_deps, module.module_id),
        ).to_jv()
        doc["meta"] = meta

        linked_modules.append(LinkedModule(
            module_id=module.module_id,
            input_path=module.input_path,
            source_path=module.source_path,
            is_entry=module.is_entry,
            east_doc=doc,
            module_kind=module.module_kind,
        ))

        helper_id = ""
        owner_module_id = ""
        generated_by = ""
        include_owner_module_id = False
        helper_meta = meta.get("synthetic_helper_v1")
        if module.module_kind == "helper" and jv_is_dict(helper_meta):
            include_owner_module_id = True
            helper_meta_dict = jv_dict(helper_meta)
            helper_id = "" + _node_str(helper_meta_dict, "helper_id")
            owner_module_id = "" + _node_str(helper_meta_dict, "owner_module_id")
            generated_by = "" + _node_str(helper_meta_dict, "generated_by")
        module_entries.append(ManifestModuleEntryDraft(
            module_id=module.module_id,
            input_path=module.input_path,
            output_path=_linked_output_path(module.module_id),
            source_path=module.source_path,
            is_entry=module.is_entry,
            module_kind=module.module_kind,
            helper_id=helper_id,
            owner_module_id=owner_module_id,
            generated_by=generated_by,
            include_owner_module_id=include_owner_module_id,
        ).to_jv())

    # 9. call_graph dict 変換
    cg_dict: dict[str, JsonVal] = {}
    for caller in sorted(call_graph.keys()):
        callee_list: list[JsonVal] = []
        for callee in call_graph[caller]:
            callee_list.append(callee)
        cg_dict[caller] = callee_list

    sccs_list: list[JsonVal] = []
    for component in sccs:
        component_items: list[JsonVal] = []
        for item in component:
            component_items.append(item)
        sccs_list.append(component_items)

    # 10. manifest (link-output.v1) 構築
    global_section = LinkManifestGlobalDraft(
        type_id_table=type_id_table,
        type_id_base_map=type_id_base_map,
        call_graph=cg_dict,
        sccs=sccs_list,
    ).to_jv()
    warnings: list[JsonVal] = []
    errors: list[JsonVal] = []
    diagnostics = LinkDiagnosticsDraft(warnings=warnings, errors=errors).to_jv()

    manifest = LinkManifestDraft(
        target=target,
        dispatch_mode=dispatch_mode,
        entry_module_ids=entry_module_ids,
        module_entries=module_entries,
        global_section=global_section,
        diagnostics=diagnostics,
    ).to_jv()

    return LinkResult(
        manifest=manifest,
        linked_modules=linked_modules,
    )

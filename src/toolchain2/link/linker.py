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

from toolchain2.link.runtime_discovery import discover_runtime_modules
from toolchain2.link.runtime_discovery import resolve_runtime_east_path
from toolchain2.link.type_id import build_type_id_table
from toolchain2.link.call_graph import build_call_graph
from toolchain2.link.dependencies import build_all_resolved_dependencies
from toolchain2.link.import_maps import collect_import_maps
from toolchain2.link.expand_defaults import expand_cross_module_defaults
from toolchain2.resolve.py.type_norm import normalize_type


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINK_OUTPUT_SCHEMA = "pytra.link_output.v1"

_LINK_EXTERNAL_MODULE_PREFIXES: tuple[str, ...] = (
    "pytra.",
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class LinkedModule:
    """1 module の linked 結果。"""
    module_id: str
    input_path: str
    source_path: str
    is_entry: bool
    east_doc: dict[str, JsonVal]
    module_kind: str  # "user" | "runtime"


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
    meta_val = east_doc.get("meta")
    if isinstance(meta_val, dict):
        mid_val = meta_val.get("module_id")
        if isinstance(mid_val, str) and mid_val.strip() != "":
            return mid_val.strip()

    source_path_val = east_doc.get("source_path")
    if isinstance(source_path_val, str) and source_path_val.strip() != "":
        source_path_norm = source_path_val.strip().replace("\\", "/")
        if source_path_norm.startswith("src/toolchain2/") and source_path_norm.endswith(".py"):
            rel = source_path_norm.replace("src/", "").replace(".py", "")
            module_id = rel.replace("/", ".")
            if module_id != "":
                return module_id
        if source_path_norm == "src/pytra-cli2.py":
            return "pytra_cli2"

    # Runtime .east ファイルの場合はパスから導出
    resolved = Path(file_path).resolve()
    east_root = runtime_east_root.resolve()
    try:
        rel = str(resolved.relative_to(east_root))
        rel_str = str(rel).replace("\\", "/")
        if rel_str.endswith(".east"):
            rel_str = rel_str.replace(".east", "")
        module_id = "pytra." + rel_str.replace("/", ".")
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
    if module.module_kind == "runtime" and not module_id.startswith("toolchain2."):
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
    return sorted(list(module_map.keys()))


def _sorted_str_map_keys(values: dict[str, JsonVal]) -> list[str]:
    return sorted(list(values.keys()))


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
    for _, doc in copied_docs:
        out.append(doc)
    return out


def _copy_doc_rows(copied_docs: list[tuple[LinkedModule, dict[str, JsonVal]]]) -> list[tuple[LinkedModule, dict[str, JsonVal]]]:
    out: list[tuple[LinkedModule, dict[str, JsonVal]]] = []
    for module, doc in copied_docs:
        out.append((module, doc))
    return out


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
    module_map = discover_runtime_modules(module_map)

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

    # 5. call graph 構築
    call_graph_parts: tuple[JsonVal, JsonVal] = cast(tuple[JsonVal, JsonVal], build_call_graph(modules))
    call_graph, sccs = call_graph_parts

    # 6. dependency table 構築
    dependency_parts: tuple[JsonVal, JsonVal] = cast(tuple[JsonVal, JsonVal], build_all_resolved_dependencies(modules))
    resolved_deps = cast(dict[str, list[str]], dependency_parts[0])
    user_deps = cast(dict[str, list[str]], dependency_parts[1])

    # 7. program_id 生成
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

    # 10. 各 module に linked_program_v1 を注入
    linked_modules: list[LinkedModule] = []
    module_entries: list[dict[str, JsonVal]] = []

    copied_rows = _copy_doc_rows(copied_docs)
    for row in copied_rows:
        module = row[0]
        doc = row[1]
        meta = _ensure_meta(doc)
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

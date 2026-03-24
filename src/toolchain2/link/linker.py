"""Linker: east3-opt modules → linked program (manifest + linked east3).

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/global_optimizer.py (import はしない)。
"""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from pytra.std import json

from toolchain2.common.jv import deep_copy_json
from toolchain2.link.runtime_discovery import discover_runtime_modules
from toolchain2.link.runtime_discovery import resolve_runtime_east_path
from toolchain2.link.type_id import build_type_id_table
from toolchain2.link.call_graph import build_call_graph
from toolchain2.link.dependencies import build_all_resolved_dependencies
from toolchain2.link.import_maps import collect_import_maps
from toolchain2.link.normalize_runtime_calls import normalize_runtime_calls


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINK_OUTPUT_SCHEMA = "pytra.link_output.v1"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class LinkedModule:
    """1 module の linked 結果。"""
    module_id: str
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

    # Runtime .east ファイルの場合はパスから導出
    resolved = Path(file_path).resolve()
    east_root = runtime_east_root.resolve()
    try:
        rel = resolved.relative_to(east_root)
        rel_str = str(rel).replace("\\", "/")
        if rel_str.endswith(".east"):
            rel_str = rel_str[: -len(".east")]
        module_id = "pytra." + rel_str.replace("/", ".")
        if module_id != "":
            return module_id
    except ValueError:
        pass

    # ファイル名から推測
    name = Path(file_path).name
    for suffix in (".east3", ".east3.json", ".json", ".east2", ".east"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
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
        doc = json.loads(text).raw
        if not isinstance(doc, dict):
            raise RuntimeError("invalid east3 document: " + path_str)
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
    for path_str in sorted(module_map.keys()):
        doc = module_map[path_str]
        if not isinstance(doc, dict):
            continue

        module_id = _module_id_from_doc(doc, path_str, runtime_east_root)
        if module_id in seen_ids:
            raise RuntimeError("duplicate module_id: " + module_id)
        seen_ids.add(module_id)

        # dispatch_mode 検証
        doc_dm = _dispatch_mode_from_doc(doc)
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
        source_path = _source_path_from_doc(doc)

        # runtime module かどうか判定
        module_kind = "user"
        if module_id.startswith("pytra."):
            module_kind = "runtime"

        modules.append(LinkedModule(
            module_id=module_id,
            source_path=source_path,
            is_entry=is_entry,
            east_doc=doc,
            module_kind=module_kind,
        ))

    # module_id でソート (決定的順序)
    modules.sort(key=lambda m: m.module_id)

    entry_module_ids = sorted([m.module_id for m in modules if m.is_entry])
    if len(entry_module_ids) == 0:
        raise RuntimeError("no entry module found")
    all_module_ids = [m.module_id for m in modules]

    # 4. type_id テーブル構築
    type_id_table, type_id_base_map, type_info_table = build_type_id_table(modules)

    # 5. call graph 構築
    call_graph, sccs = build_call_graph(modules)

    # 6. dependency table 構築
    resolved_deps, user_deps = build_all_resolved_dependencies(modules)

    # 7. program_id 生成
    pid = _program_id(target, dispatch_mode, all_module_ids)

    # 8. 各 module に linked_program_v1 を注入
    linked_modules: list[LinkedModule] = []
    module_entries: list[dict[str, JsonVal]] = []

    for module in modules:
        doc = deep_copy_json(module.east_doc)
        if not isinstance(doc, dict):
            continue

        # Normalize runtime_call values for emitter compatibility
        normalize_runtime_calls(doc)

        meta = _ensure_meta(doc)
        linked_meta: dict[str, JsonVal] = {
            "program_id": pid,
            "module_id": module.module_id,
            "entry_modules": entry_module_ids,
            "type_id_resolved_v1": type_id_table,
            "type_id_base_map_v1": type_id_base_map,
            "type_info_table_v1": type_info_table,
            "resolved_dependencies_v1": resolved_deps.get(module.module_id, []),
            "user_module_dependencies_v1": user_deps.get(module.module_id, []),
            "non_escape_summary": {},
            "container_ownership_hints_v1": {},
        }
        meta["linked_program_v1"] = linked_meta
        doc["meta"] = meta

        linked_modules.append(LinkedModule(
            module_id=module.module_id,
            source_path=module.source_path,
            is_entry=module.is_entry,
            east_doc=doc,
            module_kind=module.module_kind,
        ))

        me: dict[str, JsonVal] = {
            "module_id": module.module_id,
            "input": module.source_path if module.source_path != "" else module.module_id,
            "output": _linked_output_path(module.module_id),
            "source_path": module.source_path,
            "is_entry": module.is_entry,
            "module_kind": module.module_kind,
        }
        module_entries.append(me)

    # 9. call_graph dict 変換
    cg_dict: dict[str, JsonVal] = {}
    for caller in sorted(call_graph.keys()):
        callees = call_graph[caller]
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

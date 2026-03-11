"""EAST1 build/import-graph entry helpers."""

from __future__ import annotations

from toolchain.ir.east1 import normalize_east1_root_document
from toolchain.frontends.relative_import_normalization import resolve_import_graph_entry_root
from toolchain.frontends.relative_import_normalization import resolve_relative_module_name_for_graph
from toolchain.frontends.transpile_cli import append_unique_non_empty
from toolchain.frontends.transpile_cli import append_unique_graph_issue_entry
from toolchain.frontends.transpile_cli import build_module_east_map_from_analysis as build_module_east_map_from_analysis_core
from toolchain.frontends.transpile_cli import build_module_symbol_index as build_module_symbol_index_core
from toolchain.frontends.transpile_cli import build_module_type_schema as build_module_type_schema_core
from toolchain.frontends.transpile_cli import collect_import_requests
from toolchain.frontends.transpile_cli import collect_import_request_modules
from toolchain.frontends.transpile_cli import collect_reserved_import_conflicts
from toolchain.frontends.transpile_cli import dict_any_get_str
from toolchain.frontends.transpile_cli import finalize_import_graph_analysis
from toolchain.frontends.transpile_cli import load_east_document as load_east_document_core
from toolchain.frontends.transpile_cli import module_name_from_path_for_graph
from toolchain.frontends.transpile_cli import path_key_for_graph
from toolchain.frontends.transpile_cli import path_parent_text
from toolchain.frontends.transpile_cli import rel_disp_for_graph
from toolchain.frontends.transpile_cli import resolve_module_name_for_graph
from pytra.std.pathlib import Path
from typing import Any


def build_east1_document(
    input_path: Path,
    parser_backend: str = "self_hosted",
    load_east_document_fn: Any = None,
) -> dict[str, object]:
    """入力（`.py/.json`）を `EAST1` ルートへ変換して返す。"""
    load_fn = load_east_document_fn
    if load_fn is None:
        load_fn = load_east_document_core
    east_any = load_fn(input_path, parser_backend=parser_backend)
    if isinstance(east_any, dict):
        east_doc: dict[str, object] = east_any
        return normalize_east1_root_document(east_doc)
    raise RuntimeError("EAST1 root must be a dict")


def _analyze_import_graph_impl(
    entry_path: Path,
    runtime_std_source_root: Path,
    runtime_utils_source_root: Path,
    load_east_fn: Any,
    parser_backend: str = "self_hosted",
) -> dict[str, object]:
    """ユーザーモジュール依存を解析し、衝突/未解決/循環を返す。"""
    root = resolve_import_graph_entry_root(entry_path)
    queue: list[Path] = [entry_path]
    queued: set[str] = {path_key_for_graph(entry_path)}
    visited: set[str] = set()
    visited_order: list[str] = []
    edges: list[str] = []
    edge_seen: set[str] = set()
    missing_module_entries: list[dict[str, str]] = []
    missing_seen: set[str] = set()
    relative_import_entries: list[dict[str, str]] = []
    relative_seen: set[str] = set()
    graph_adj: dict[str, list[str]] = {}
    graph_keys: list[str] = []
    key_to_disp: dict[str, str] = {}
    key_to_path: dict[str, Path] = {}
    module_id_map: dict[str, str] = {}

    reserved_conflicts = collect_reserved_import_conflicts(root)

    while queue:
        cur_path = queue.pop(0)
        cur_key = path_key_for_graph(cur_path)
        if cur_key in visited:
            continue
        visited.add(cur_key)
        visited_order.append(cur_key)
        key_to_path[cur_key] = cur_path
        key_to_disp[cur_key] = rel_disp_for_graph(root, cur_path)
        if cur_key not in module_id_map:
            module_id_map[cur_key] = module_name_from_path_for_graph(root, cur_path)

        east_cur: dict[str, object] = {}
        try:
            if callable(load_east_fn):
                loaded = load_east_fn(cur_path)
            else:
                loaded = build_east1_document(cur_path, parser_backend=parser_backend)
            if isinstance(loaded, dict):
                east_cur = loaded
        except Exception:
            continue

        if cur_key not in graph_adj:
            graph_adj[cur_key] = []
            graph_keys.append(cur_key)
        cur_disp = key_to_disp[cur_key]
        for req in collect_import_requests(east_cur):
            for mod in collect_import_request_modules(req):
                if mod.startswith("."):
                    resolved = resolve_relative_module_name_for_graph(mod, root, cur_path)
                else:
                    search_root = Path(path_parent_text(cur_path))
                    resolved = resolve_module_name_for_graph(
                        mod,
                        search_root,
                        runtime_std_source_root,
                        runtime_utils_source_root,
                    )
                status = dict_any_get_str(resolved, "status")
                dep_txt = dict_any_get_str(resolved, "path")
                resolved_mod_id = dict_any_get_str(resolved, "module_id")
                if status == "relative":
                    append_unique_graph_issue_entry(relative_import_entries, relative_seen, cur_disp, mod)
                    continue
                dep_disp = mod
                if status == "user":
                    if dep_txt == "":
                        continue
                    dep_file = Path(dep_txt)
                    dep_key = path_key_for_graph(dep_file)
                    dep_disp = rel_disp_for_graph(root, dep_file)
                    module_id = resolved_mod_id if resolved_mod_id != "" else mod
                    if dep_key not in module_id_map or module_id_map[dep_key] == "":
                        module_id_map[dep_key] = module_id
                    deps: list[str] = []
                    if cur_key in graph_adj:
                        deps = graph_adj[cur_key]
                    deps.append(dep_key)
                    graph_adj[cur_key] = deps
                    key_to_path[dep_key] = dep_file
                    key_to_disp[dep_key] = dep_disp
                    if dep_key not in queued and dep_key not in visited:
                        queued.add(dep_key)
                        queue.append(dep_file)
                elif status == "missing":
                    miss_mod = resolved_mod_id if resolved_mod_id != "" else mod
                    append_unique_graph_issue_entry(missing_module_entries, missing_seen, cur_disp, miss_mod)
                edge = cur_disp + " -> " + dep_disp
                append_unique_non_empty(edges, edge_seen, edge)

    return finalize_import_graph_analysis(
        graph_adj,
        graph_keys,
        key_to_disp,
        visited_order,
        key_to_path,
        edges,
        missing_module_entries,
        relative_import_entries,
        reserved_conflicts,
        module_id_map,
    )


def analyze_import_graph(
    entry_path: Path,
    runtime_std_source_root: Path = Path("src/pytra/std"),
    runtime_utils_source_root: Path = Path("src/pytra/utils"),
    parser_backend: str = "self_hosted",
    load_east1_document_fn: Any = None,
) -> dict[str, object]:
    """`EAST1` build を用いて import graph を解析する。"""
    out_any = _analyze_import_graph_impl(
        entry_path,
        runtime_std_source_root,
        runtime_utils_source_root,
        load_east1_document_fn,
        parser_backend,
    )
    if isinstance(out_any, dict):
        out: dict[str, object] = out_any
        return out
    raise RuntimeError("import graph analysis must be a dict")


def build_module_east_map(
    entry_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "2",
    object_dispatch_mode: str = "",
    runtime_std_source_root: Path = Path("src/pytra/std"),
    runtime_utils_source_root: Path = Path("src/pytra/utils"),
    analyze_import_graph_fn: Any = None,
    build_module_document_fn: Any = None,
) -> dict[str, dict[str, object]]:
    """入口 + 依存ユーザーモジュールを `EAST1` 化した map を返す。"""
    analyze_fn = analyze_import_graph_fn
    if analyze_fn is None:
        analyze_fn = analyze_import_graph
    build_fn = build_module_document_fn
    if build_fn is None:
        build_fn = build_east1_document
    analysis_any = analyze_fn(
        entry_path,
        runtime_std_source_root=runtime_std_source_root,
        runtime_utils_source_root=runtime_utils_source_root,
        parser_backend=parser_backend,
    )
    if not isinstance(analysis_any, dict):
        raise RuntimeError("import graph analysis must be a dict")
    analysis: dict[str, object] = analysis_any

    files: list[str] = []
    files_any = analysis.get("user_module_files")
    if isinstance(files_any, list):
        for f_any in files_any:
            if isinstance(f_any, str) and f_any != "":
                files.append(f_any)

    module_east_raw: dict[str, dict[str, object]] = {}
    for f in files:
        p = Path(f)
        east_any: Any = None
        try:
            east_any = build_fn(
                p,
                parser_backend=parser_backend,
                east_stage=east_stage,
                object_dispatch_mode=object_dispatch_mode,
            )
        except TypeError:
            try:
                east_any = build_fn(p, parser_backend=parser_backend)
            except TypeError:
                east_any = build_fn(p)
        if isinstance(east_any, dict):
            east_one: dict[str, object] = east_any
            module_east_raw[str(p)] = east_one

    module_map_any = build_module_east_map_from_analysis_core(
        entry_path,
        analysis,
        module_east_raw,
    )
    if isinstance(module_map_any, dict):
        module_map: dict[str, dict[str, object]] = module_map_any
        return module_map
    raise RuntimeError("module east map must be a dict")


def build_module_symbol_index(module_east_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """module EAST map からシンボル索引を構築する。"""
    out_any = build_module_symbol_index_core(module_east_map)
    if isinstance(out_any, dict):
        out: dict[str, dict[str, Any]] = out_any
        return out
    raise RuntimeError("module symbol index must be a dict")


def build_module_type_schema(module_east_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """module EAST map から type schema を構築する。"""
    out_any = build_module_type_schema_core(module_east_map)
    if isinstance(out_any, dict):
        out: dict[str, dict[str, Any]] = out_any
        return out
    raise RuntimeError("module type schema must be a dict")


class East1BuildHelpers:
    build_east1_document = staticmethod(build_east1_document)
    analyze_import_graph = staticmethod(analyze_import_graph)
    build_module_east_map = staticmethod(build_module_east_map)
    build_module_symbol_index = staticmethod(build_module_symbol_index)
    build_module_type_schema = staticmethod(build_module_type_schema)

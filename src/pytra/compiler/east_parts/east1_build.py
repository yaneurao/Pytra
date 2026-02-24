"""EAST1 build/import-graph entry helpers."""

from __future__ import annotations

from pytra.compiler.east_parts.east1 import normalize_east1_root_document
from pytra.compiler.transpile_cli import analyze_import_graph as analyze_import_graph_core
from pytra.compiler.transpile_cli import build_module_east_map_from_analysis as build_module_east_map_from_analysis_core
from pytra.compiler.transpile_cli import build_module_symbol_index as build_module_symbol_index_core
from pytra.compiler.transpile_cli import build_module_type_schema as build_module_type_schema_core
from pytra.compiler.transpile_cli import load_east_document as load_east_document_core
from pytra.std.pathlib import Path
from pytra.std.typing import Any


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


def analyze_import_graph(
    entry_path: Path,
    runtime_std_source_root: Path = Path("src/pytra/std"),
    runtime_utils_source_root: Path = Path("src/pytra/utils"),
    parser_backend: str = "self_hosted",
    load_east1_document_fn: Any = None,
) -> dict[str, object]:
    """`EAST1` build を用いて import graph を解析する。"""
    load_fn = load_east1_document_fn
    if load_fn is None:

        def _load_default(path: Path) -> dict[str, object]:
            return build_east1_document(path, parser_backend=parser_backend)

        load_fn = _load_default
    out_any = analyze_import_graph_core(
        entry_path,
        runtime_std_source_root,
        runtime_utils_source_root,
        load_fn,
    )
    if isinstance(out_any, dict):
        out: dict[str, object] = out_any
        return out
    raise RuntimeError("import graph analysis must be a dict")


def build_module_east_map(
    entry_path: Path,
    parser_backend: str = "self_hosted",
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

"""Shared frontend helpers for import-graph analysis/report handling."""

from __future__ import annotations

from toolchain.frontends.import_graph_frontend_helpers import collect_user_module_files_for_graph
from toolchain.frontends.import_graph_frontend_helpers import is_pytra_module_name
from toolchain.frontends.import_graph_frontend_helpers import resolve_user_module_path_for_graph
from toolchain.frontends.known_modules import is_known_module_name
from pytra.std.pathlib import Path


def split_graph_issue_entry(v_txt: str) -> tuple[str, str]:
    """`file: module` 形式を `(file, module)` へ分解する。"""
    marker = ": "
    pos = v_txt.find(marker)
    if pos >= 0:
        return v_txt[:pos], v_txt[pos + len(marker) :]
    return v_txt, v_txt


def make_graph_issue_entry(file_part: str, module_part: str) -> dict[str, str]:
    """import graph issue の canonical carrier を返す。"""
    entry: dict[str, str] = {}
    entry["file"] = file_part
    entry["module"] = module_part
    return entry


def normalize_graph_issue_entry(entry_any: object) -> dict[str, str]:
    """graph issue carrier を `{file, module}` へ正規化する。"""
    if isinstance(entry_any, dict):
        d: dict[str, object] = entry_any
        file_part_any = d.get("file")
        module_part_any = d.get("module")
        file_part = file_part_any if isinstance(file_part_any, str) else ""
        module_part = module_part_any if isinstance(module_part_any, str) else ""
        if file_part != "" or module_part != "":
            if file_part == "":
                file_part = module_part
            if module_part == "":
                module_part = file_part
            return make_graph_issue_entry(file_part, module_part)
    if isinstance(entry_any, str):
        file_part, module_part = split_graph_issue_entry(entry_any)
        return make_graph_issue_entry(file_part, module_part)
    return make_graph_issue_entry("", "")


def format_graph_issue_entry(entry_any: object) -> str:
    """graph issue carrier を legacy text へ戻す。"""
    entry = normalize_graph_issue_entry(entry_any)
    file_part_any = entry.get("file")
    module_part_any = entry.get("module")
    file_part = file_part_any if isinstance(file_part_any, str) else ""
    module_part = module_part_any if isinstance(module_part_any, str) else ""
    if file_part == "" and module_part == "":
        return ""
    if file_part == "" or file_part == module_part:
        return module_part if module_part != "" else file_part
    return file_part + ": " + module_part


def append_unique_graph_issue_entry(
    items: list[dict[str, str]],
    seen: set[str],
    file_part: str,
    module_part: str,
) -> None:
    """graph issue carrier を legacy text dedupe 付きで追加する。"""
    entry = make_graph_issue_entry(file_part, module_part)
    text = format_graph_issue_entry(entry)
    if text == "" or text in seen:
        return
    seen.add(text)
    items.append(entry)


def dict_any_get_graph_issue_entries(
    src: dict[str, object],
    legacy_key: str,
    structured_key: str,
) -> list[dict[str, str]]:
    """analysis から graph issue carrier list を structured-first で返す。"""
    items_any: object = []
    if structured_key in src:
        items_any = src[structured_key]
    elif legacy_key in src:
        items_any = src[legacy_key]
    if not isinstance(items_any, list):
        return []
    out: list[dict[str, str]] = []
    for item_any in items_any:
        entry = normalize_graph_issue_entry(item_any)
        text = format_graph_issue_entry(entry)
        if text != "":
            out.append(entry)
    return out


def graph_issue_entries_to_text_list(entries: list[dict[str, str]]) -> list[str]:
    """structured graph issue carrier list を legacy text list へ戻す。"""
    out: list[str] = []
    for entry in entries:
        text = format_graph_issue_entry(entry)
        if text != "":
            out.append(text)
    return out


def graph_cycle_dfs(
    key: str,
    graph_adj: dict[str, list[str]],
    key_to_disp: dict[str, str],
    color: dict[str, int],
    stack: list[str],
    cycles: list[str],
    cycle_seen: set[str],
) -> None:
    """import graph DFS で循環参照を収集する。"""
    color[key] = 1
    stack.append(key)
    nxts = graph_adj.get(key, [])
    for nxt in nxts:
        c = color.get(nxt, 0)
        if c == 0:
            graph_cycle_dfs(nxt, graph_adj, key_to_disp, color, stack, cycles, cycle_seen)
        elif c == 1:
            start = -1
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx] == nxt:
                    start = idx
                    break
            if start >= 0:
                nodes: list[str] = []
                for pos in range(start, len(stack)):
                    nodes.append(stack[pos])
                nodes.append(nxt)
                disp_nodes: list[str] = []
                for node in nodes:
                    disp_nodes.append(key_to_disp.get(node, node))
                cycle_txt = " -> ".join(disp_nodes)
                if cycle_txt not in cycle_seen:
                    cycle_seen.add(cycle_txt)
                    cycles.append(cycle_txt)
    stack.pop()
    color[key] = 2


def format_graph_list_section(section_text: str, label: str, items: list[str]) -> str:
    """依存解析レポートの1セクションを追記して返す。"""
    out = section_text + label + ":\n"
    if len(items) == 0:
        out += "  (none)\n"
        return out
    for item in items:
        out += "  - " + item + "\n"
    return out


def format_import_graph_report(analysis: dict[str, object]) -> str:
    """依存解析結果を `--dump-deps` 向けテキストへ整形する。"""
    edges_any = analysis.get("edges")
    edges: list[str] = []
    if isinstance(edges_any, list):
        for item_any in edges_any:
            if isinstance(item_any, str):
                edges.append(item_any)
    out = "graph:\n"
    if len(edges) == 0:
        out += "  (none)\n"
    else:
        for item in edges:
            out += "  - " + item + "\n"
    cycles_any = analysis.get("cycles")
    cycles: list[str] = []
    if isinstance(cycles_any, list):
        for item_any in cycles_any:
            if isinstance(item_any, str):
                cycles.append(item_any)
    out = format_graph_list_section(out, "cycles", cycles)
    missing = graph_issue_entries_to_text_list(
        dict_any_get_graph_issue_entries(analysis, "missing_modules", "missing_module_entries")
    )
    out = format_graph_list_section(out, "missing", missing)
    relative = graph_issue_entries_to_text_list(
        dict_any_get_graph_issue_entries(analysis, "relative_imports", "relative_import_entries")
    )
    out = format_graph_list_section(out, "relative", relative)
    reserved_any = analysis.get("reserved_conflicts")
    reserved: list[str] = []
    if isinstance(reserved_any, list):
        for item_any in reserved_any:
            if isinstance(item_any, str):
                reserved.append(item_any)
    out = format_graph_list_section(out, "reserved", reserved)
    return out


def validate_import_graph_or_raise(analysis: dict[str, object]) -> None:
    """依存解析の重大問題を `input_invalid` として報告する。"""
    details: list[str] = []
    has_relative_import_escape = False
    reserved_any = analysis.get("reserved_conflicts")
    if isinstance(reserved_any, list):
        for item_any in reserved_any:
            if isinstance(item_any, str) and item_any != "":
                details.append("kind=reserved_conflict file=" + item_any + " import=pytra")
    for entry in dict_any_get_graph_issue_entries(analysis, "relative_imports", "relative_import_entries"):
        file_part_any = entry.get("file")
        module_part_any = entry.get("module")
        file_part = file_part_any if isinstance(file_part_any, str) else ""
        module_part = module_part_any if isinstance(module_part_any, str) else ""
        has_relative_import_escape = True
        details.append(
            "kind=relative_import_escape file=" + file_part + " import=from " + module_part + " import ..."
        )
    for entry in dict_any_get_graph_issue_entries(analysis, "missing_modules", "missing_module_entries"):
        file_part_any = entry.get("file")
        module_part_any = entry.get("module")
        file_part = file_part_any if isinstance(file_part_any, str) else ""
        module_part = module_part_any if isinstance(module_part_any, str) else ""
        details.append("kind=missing_module file=" + file_part + " import=" + module_part)
    cycles_any = analysis.get("cycles")
    if isinstance(cycles_any, list):
        for item_any in cycles_any:
            if isinstance(item_any, str) and item_any != "":
                details.append("kind=import_cycle file=(graph) import=" + item_any)
    if len(details) > 0:
        summary = "Failed to resolve imports (missing/conflict/cycle)."
        if has_relative_import_escape:
            summary = "Failed to resolve imports (missing/conflict/cycle/relative)."
        payload = "__PYTRA_USER_ERROR__|input_invalid|" + summary
        for detail in details:
            payload += "\n" + detail
        raise RuntimeError(payload)


def finalize_import_graph_analysis(
    graph_adj: dict[str, list[str]],
    graph_keys: list[str],
    key_to_disp: dict[str, str],
    visited_order: list[str],
    key_to_path: dict[str, Path],
    edges: list[str],
    missing_module_entries: list[dict[str, str]],
    relative_import_entries: list[dict[str, str]],
    reserved_conflicts: list[str],
    module_id_map: dict[str, str],
) -> dict[str, object]:
    """import graph の最終整形（循環検出・ファイル一覧・戻り値整形）を行う。"""
    cycles: list[str] = []
    cycle_seen: set[str] = set()
    color: dict[str, int] = {}
    stack: list[str] = []
    keys: list[str] = []
    for key in graph_keys:
        keys.append(key)
    for key in keys:
        if color.get(key, 0) == 0:
            graph_cycle_dfs(key, graph_adj, key_to_disp, color, stack, cycles, cycle_seen)
    user_module_files = collect_user_module_files_for_graph(visited_order, key_to_path)
    return {
        "edges": edges,
        "missing_modules": graph_issue_entries_to_text_list(missing_module_entries),
        "missing_module_entries": missing_module_entries,
        "relative_imports": graph_issue_entries_to_text_list(relative_import_entries),
        "relative_import_entries": relative_import_entries,
        "reserved_conflicts": reserved_conflicts,
        "cycles": cycles,
        "module_id_map": module_id_map,
        "user_module_files": user_module_files,
    }


def is_known_non_user_import(
    module_name: str,
    runtime_std_source_root: Path,
    runtime_utils_source_root: Path,
) -> bool:
    """import graph でユーザーファイル解決不要とみなす import か判定する。"""
    if is_known_module_name(module_name):
        return True
    if module_name == "toolchain" or module_name.startswith("toolchain."):
        return True
    if module_name == "backends" or module_name.startswith("toolchain.emit."):
        return True
    if (
        module_name == "__future__"
        or module_name == "os"
        or module_name == "glob"
        or module_name == "collections"
        or module_name == "statistics"
        or module_name == "typing"
        or module_name == "shutil"
        or module_name == "copy"
        or module_name == "dataclasses"
        or module_name == "pathlib"
    ):
        return True
    rel = module_name.replace(".", "/")
    std_root_txt = str(runtime_std_source_root)
    if std_root_txt != "" and not std_root_txt.endswith("/"):
        std_root_txt += "/"
    utils_root_txt = str(runtime_utils_source_root)
    if utils_root_txt != "" and not utils_root_txt.endswith("/"):
        utils_root_txt += "/"
    if Path(std_root_txt + rel + ".py").exists():
        return True
    if Path(std_root_txt + rel + "/__init__.py").exists():
        return True
    if Path(utils_root_txt + rel + ".py").exists():
        return True
    if Path(utils_root_txt + rel + "/__init__.py").exists():
        return True
    return False


def resolve_module_name_for_graph(
    raw_name: str,
    root_dir: Path,
    runtime_std_source_root: Path,
    runtime_utils_source_root: Path,
) -> dict[str, str]:
    """import graph 用のモジュール解決（順序依存を避ける前段 helper）。"""
    if raw_name.startswith("."):
        return {"status": "relative", "module_id": raw_name, "path": ""}
    if is_pytra_module_name(raw_name):
        return {"status": "pytra", "module_id": raw_name, "path": ""}
    dep_file = resolve_user_module_path_for_graph(raw_name, root_dir)
    if str(dep_file) != "":
        return {"status": "user", "module_id": raw_name, "path": str(dep_file)}
    if is_known_non_user_import(raw_name, runtime_std_source_root, runtime_utils_source_root):
        return {"status": "known", "module_id": raw_name, "path": ""}
    return {"status": "missing", "module_id": raw_name, "path": ""}


def resolve_module_name(
    raw_name: str,
    root_dir: Path,
) -> dict[str, object]:
    """モジュール名を `user/pytra/known/missing/relative` に分類して解決する。"""
    resolved = resolve_module_name_for_graph(
        raw_name,
        root_dir,
        Path("src/pytra/std"),
        Path("src/pytra/utils"),
    )
    status_any = resolved.get("status")
    module_id_any = resolved.get("module_id")
    path_txt_any = resolved.get("path")
    status = status_any if isinstance(status_any, str) else ""
    module_id = module_id_any if isinstance(module_id_any, str) and module_id_any != "" else raw_name
    path_txt = path_txt_any if isinstance(path_txt_any, str) else ""
    path_obj: Path | None = None
    if path_txt != "":
        path_obj = Path(path_txt)
    return {
        "status": status,
        "module_id": module_id,
        "path": path_obj,
    }

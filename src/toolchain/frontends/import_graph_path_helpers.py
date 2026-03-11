"""Shared import-graph path helpers for frontend entrypoints."""

from __future__ import annotations

from pytra.std.pathlib import Path


def path_parent_text(path_obj: Path) -> str:
    """Path から親ディレクトリ文字列を取得する。"""
    path_txt = str(path_obj)
    if path_txt == "":
        return "."
    last_sep = -1
    for i, ch in enumerate(path_txt):
        if ch == "/" or ch == "\\":
            last_sep = i
    if last_sep <= 0:
        return "."
    return path_txt[:last_sep]


def path_key_for_graph(p: Path) -> str:
    """依存グラフ内部で使うパス文字列キーを返す。"""
    return str(p)


def module_name_from_path_for_graph(root: Path, module_path: Path) -> str:
    """import graph 用の module_id フォールバック解決。"""
    root_txt = str(root)
    path_txt = str(module_path)
    in_root = False
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
        in_root = True
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", ".")
    if rel.endswith(".__init__"):
        rel = rel[:-9]
    if not in_root:
        stem = module_path.stem
        stem = module_path.parent.name if stem == "__init__" else stem
        rel = stem
    return rel

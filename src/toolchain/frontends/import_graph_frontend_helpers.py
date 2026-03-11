"""Shared frontend helpers for import-graph path/module-id/request handling."""

from __future__ import annotations

from toolchain.frontends.import_graph_path_helpers import module_name_from_path_for_graph
from toolchain.frontends.import_graph_path_helpers import path_parent_text
from toolchain.frontends.relative_import_normalization import relative_module_tail
from pytra.std.pathlib import Path
from typing import Any


def _append_unique_non_empty_graph(items: list[str], seen: set[str], value: str) -> None:
    if value != "" and value not in seen:
        seen.add(value)
        items.append(value)


def is_pytra_module_name(module_name: str) -> bool:
    """`pytra` 配下モジュール名かを判定する。"""
    return module_name == "pytra" or module_name.startswith("pytra.")


def rel_disp_for_graph(base_path: Path, p: Path) -> str:
    """表示用に `base_path` からの相対パス文字列を返す。"""
    base_txt = str(base_path)
    p_txt = str(p)
    base_prefix = base_txt if base_txt.endswith("/") else base_txt + "/"
    if p_txt.startswith(base_prefix):
        return p_txt[len(base_prefix) :]
    if p_txt == base_txt:
        return "."
    return p_txt


def sanitize_module_label(text: str) -> str:
    """モジュール識別子向けに英数字/`_` のみ残す。"""
    out_chars: list[str] = []
    for ch in text:
        ok = ch == "_" or ch.isalpha() or ch.isdigit()
        if ok:
            out_chars.append(ch)
        else:
            out_chars.append("_")
    out = "".join(out_chars)
    out = out if out != "" else "module"
    if (
        out.find("0") == 0
        or out.find("1") == 0
        or out.find("2") == 0
        or out.find("3") == 0
        or out.find("4") == 0
        or out.find("5") == 0
        or out.find("6") == 0
        or out.find("7") == 0
        or out.find("8") == 0
        or out.find("9") == 0
    ):
        out = "_" + out
    return out


def module_rel_label(root: Path, module_path: Path) -> str:
    """`root` からの相対パスを multi-file 用モジュールラベルへ変換する。"""
    root_txt = str(root)
    path_txt = str(module_path)
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", "__")
    return sanitize_module_label(rel)


def module_id_from_east_for_graph(root: Path, module_path: Path, east_doc: dict[str, Any]) -> str:
    """import graph 用の EAST module_id 抽出。"""
    module_id = ""
    meta_any = east_doc.get("meta")
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str):
            module_id = module_id_any
    return module_id if module_id != "" else module_name_from_path_for_graph(root, module_path)


def resolve_user_module_path_for_graph(module_name: str, search_root: Path) -> Path:
    """import graph 用のユーザーモジュール解決（未解決は空 Path）。"""
    if module_name.startswith("pytra.") or module_name == "pytra":
        return Path("")
    rel = module_name.replace(".", "/")
    parts = module_name.split(".")
    leaf = parts[len(parts) - 1] if len(parts) > 0 else ""
    cur_dir = str(search_root)
    cur_dir = cur_dir if cur_dir != "" else "."
    seen_dirs: set[str] = set()
    best_path = ""
    best_rank = -1
    best_distance = 1000000000
    distance = 0
    while cur_dir not in seen_dirs:
        seen_dirs.add(cur_dir)
        prefix = cur_dir
        if prefix != "" and not prefix.endswith("/"):
            prefix += "/"
        cand_init = prefix + rel + "/__init__.py"
        cand_named = prefix + rel + "/" + leaf + ".py" if leaf != "" else ""
        cand_flat = prefix + rel + ".py"
        candidates: list[tuple[str, int]] = []
        candidates.append((cand_init, 3))
        if cand_named != "":
            candidates.append((cand_named, 2))
        candidates.append((cand_flat, 1))
        for path_txt, rank in candidates:
            if Path(path_txt).exists():
                if rank > best_rank or (rank == best_rank and distance < best_distance):
                    best_path = path_txt
                    best_rank = rank
                    best_distance = distance
        parent_dir = path_parent_text(Path(cur_dir))
        if parent_dir == cur_dir:
            break
        cur_dir = parent_dir if parent_dir != "" else "."
        distance += 1
    if best_path != "":
        return Path(best_path)
    return Path("")


def collect_reserved_import_conflicts(root: Path) -> list[str]:
    """予約名 `pytra` と衝突するユーザーファイルを収集する。"""
    out: list[str] = []
    pytra_file = root / "pytra.py"
    pytra_pkg_init = root / "pytra" / "__init__.py"
    canonical_pytra_pkg = (
        (root / "pytra" / "std").exists()
        and (root / "pytra" / "utils").exists()
        and (root / "pytra" / "built_in").exists()
    )
    if pytra_file.exists():
        out.append(str(pytra_file))
    if pytra_pkg_init.exists() and not canonical_pytra_pkg:
        out.append(str(pytra_pkg_init))
    return out


def collect_import_requests(east_module: dict[str, object]) -> list[dict[str, str]]:
    """EAST module から structured import request を抽出する。"""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    body_any = east_module.get("body")
    if not isinstance(body_any, list):
        return out
    for stmt_any in body_any:
        if not isinstance(stmt_any, dict):
            continue
        kind = ""
        kind_any = stmt_any.get("kind")
        if isinstance(kind_any, str):
            kind = kind_any
        if kind == "Import":
            names_any = stmt_any.get("names")
            if not isinstance(names_any, list):
                continue
            for ent_any in names_any:
                if not isinstance(ent_any, dict):
                    continue
                module_name = ent_any.get("name")
                if not isinstance(module_name, str) or module_name == "":
                    continue
                req = {"kind": "import_module", "module": module_name, "symbol": ""}
                key = req["kind"] + "|" + req["module"] + "|" + req["symbol"]
                if key not in seen:
                    seen.add(key)
                    out.append(req)
        elif kind == "ImportFrom":
            module_name = stmt_any.get("module")
            if not isinstance(module_name, str) or module_name == "":
                continue
            names_any = stmt_any.get("names")
            if not isinstance(names_any, list) or len(names_any) == 0:
                req = {"kind": "from_module", "module": module_name, "symbol": ""}
                key = req["kind"] + "|" + req["module"] + "|" + req["symbol"]
                if key not in seen:
                    seen.add(key)
                    out.append(req)
                continue
            for ent_any in names_any:
                if not isinstance(ent_any, dict):
                    continue
                symbol = ent_any.get("name")
                if not isinstance(symbol, str) or symbol == "":
                    continue
                req = {"kind": "from_module", "module": module_name, "symbol": symbol}
                key = req["kind"] + "|" + req["module"] + "|" + req["symbol"]
                if key not in seen:
                    seen.add(key)
                    out.append(req)
    return out


def collect_import_from_request_modules(module_name: str, symbol: str) -> list[str]:
    """`ImportFrom` request から import graph が辿る module candidate を返す。"""
    if module_name == "":
        return []
    if module_name.startswith(".") and relative_module_tail(module_name) == "":
        if symbol != "" and symbol != "*":
            return [module_name + symbol]
    if symbol == "*" or symbol == "":
        return [module_name]
    if module_name.startswith(".") and relative_module_tail(module_name) == "":
        return [module_name + symbol]
    return [module_name]


def collect_import_request_modules(req: dict[str, str]) -> list[str]:
    """structured import request から import graph の module candidate を返す。"""
    kind = req["kind"] if "kind" in req else ""
    module_name = req["module"] if "module" in req else ""
    symbol = req["symbol"] if "symbol" in req else ""
    if kind == "import_module":
        if module_name == "":
            return []
        return [module_name]
    if kind == "from_module":
        return collect_import_from_request_modules(module_name, symbol)
    return []


def collect_import_modules(east_module: dict[str, object]) -> list[str]:
    """EAST module から import graph 互換の module dependency 候補を抽出する。"""
    out: list[str] = []
    seen: set[str] = set()
    for req in collect_import_requests(east_module):
        for mod_name in collect_import_request_modules(req):
            _append_unique_non_empty_graph(out, seen, mod_name)
    return out


def sort_str_list_copy(items: list[str]) -> list[str]:
    """`list[str]` を昇順へ整列したコピーを返す（selfhost-safe 実装）。"""
    out: list[str] = []
    for item in items:
        out.append(item)
    for i in range(1, len(out)):
        key = out[i]
        insert_at = i
        for j in range(i - 1, -1, -1):
            greater = False
            left = out[j]
            limit = len(left) if len(left) < len(key) else len(key)
            decided = False
            for pos in range(limit):
                lcode = ord(left[pos : pos + 1])
                rcode = ord(key[pos : pos + 1])
                if lcode > rcode:
                    greater = True
                    decided = True
                    break
                if lcode < rcode:
                    decided = True
                    break
            if not decided and len(left) > len(key):
                greater = True
            if greater:
                out[j + 1] = out[j]
                insert_at = j
            else:
                break
        out[insert_at] = key
    return out


def collect_user_module_files_for_graph(visited_order: list[str], key_to_path: dict[str, Path]) -> list[str]:
    """import graph 解析済みキー列と path map からソート済みファイル一覧を返す。"""
    out: list[str] = []
    visited_keys: list[str] = []
    for visited_key in visited_order:
        visited_keys.append(visited_key)
    visited_keys = sort_str_list_copy(visited_keys)
    for key in visited_keys:
        if key in key_to_path:
            out.append(str(key_to_path[key]))
    return out

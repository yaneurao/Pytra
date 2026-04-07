"""
emitter 責務違反チェッカー（P6-EMITTER-LINT）

src/toolchain/emit/*/ 配下の .py ファイルを対象に、禁止パターンを grep して
言語 × カテゴリのマトリクスを stdout に出力する。

exit code は常に 0（違反があっても fail しない。結果はレポートのみ）。

使い方:
    python3 tools/check/check_emitter_hardcode_lint.py
    python3 tools/check/check_emitter_hardcode_lint.py --verbose
    python3 tools/check/check_emitter_hardcode_lint.py --lang go
    python3 tools/check/check_emitter_hardcode_lint.py --category module_name
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMIT_DIR = ROOT / "src" / "toolchain" / "emit"

# README バッジ順の全18言語（表示名 → emit サブディレクトリ名）
ALL_LANGS_ORDERED: list[tuple[str, str]] = [
    ("cpp",    "cpp"),
    ("rs",     "rs"),
    ("cs",     "cs"),
    ("ps1",    "powershell"),
    ("js",     "js"),
    ("ts",     "ts"),
    ("dart",   "dart"),
    ("go",     "go"),
    ("java",   "java"),
    ("scala",  "scala"),
    ("kotlin", "kotlin"),
    ("swift",  "swift"),
    ("ruby",   "ruby"),
    ("lua",    "lua"),
    ("php",    "php"),
    ("nim",    "nim"),
    ("julia",  "julia"),
    ("zig",    "zig"),
]
ALL_LANG_KEYS = [k for k, _ in ALL_LANGS_ORDERED]

# JS は独自 emitter を持たず TS emitter を共用する
LANG_EMITTER_ALIAS: dict[str, str] = {"js": "ts"}

# ---------------------------------------------------------------------------
# 検出カテゴリ定義
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, list[str]] = {
    "module_name": [
        # emitter が runtime_module_id ではなくモジュール名を文字列で知っている
        r'"math"',
        r'"pathlib"',
        r'"json"',
        r'"sys"',
        r'"os"',
        r'"glob"',
        r'"time"',
        r'"subprocess"',
        r'"re"',
        r'"argparse"',
    ],
    "runtime_symbol": [
        # emitter が runtime_call / runtime_symbol ではなく関数名を直接知っている
        r'"perf_counter"',
        r'"py_len"',
        r'"py_print"',
        r'"py_range"',
        r'"write_rgb_png"',
        r'"save_gif"',
        r'"grayscale_palette"',
        # Python メソッド名のハードコード（EAST3 の runtime_call / semantic_tag で判定すべき）
        # Python メソッド名のハードコード（EAST3 の runtime_call / semantic_tag で判定すべき）
        # 除外: "values","keys","items","get","index","add","upper","lower","replace" は
        #        EAST3 フィールド名・演算子名・slice フィールド名と衝突するため
        r'"append"',
        r'"extend"',
        r'"insert"',
        r'"pop"',
        r'"clear"',
        r'"sort"',
        r'"reverse"',
        r'"remove"',
        r'"discard"',
        r'"setdefault"',
        r'"update"',
        r'"split"',
        r'"join"',
        r'"strip"',
        r'"lstrip"',
        r'"rstrip"',
        r'"startswith"',
        r'"endswith"',
        r'"rfind"',
        r'"isdigit"',
        r'"isalpha"',
        r'"isalnum"',
    ],
    "target_constant": [
        # mapping.json の calls テーブルの責務を emitter が横取りしている
        r'"M_PI"',
        r'"M_E"',
        r'"std::sqrt"',
        r'"std::stoll"',
        r'"math\.Sqrt"',
        r'"Math\.PI"',
    ],
    "prefix_match": [
        # runtime_call_adapter_kind で判定すべきところをプレフィックスで分岐
        r'"pytra\.std\."',
        r'"pytra\.core\."',
        r'"pytra\.built_in\."',
    ],
    "class_name": [
        # EAST3 の型情報から来るべき判定を emitter がクラス名で分岐
        r'"Path"',
        r'"ArgumentParser"',
        r'"Exception"',
        # PyFile は廃止済み。IOBase / TextIOWrapper / BufferedWriter / BufferedReader を使う
        r'"PyFile"',
    ],
    "python_syntax": [
        # EAST3 では既に正規化済みの Python 構文が emitter に残っている
        r'"__main__"',
        r'"super\(\)"',
    ],
    "type_id": [
        # EAST3 の isinstance / type_id 情報から来るべき判定を emitter がハードコード
        # spec-adt.md §6: PYTRA_TYPE_ID / pytra_isinstance / type_id_table は廃止予定
        r'"py_runtime_object_isinstance"',
        r'"PYTRA_TID_"',
        r'"py_tid_"',
        r'"g_type_table"',
        r'"PYTRA_TYPE_ID"',
        r'"pytra_isinstance"',
    ],
    # skip_pure_python は grep ではなく mapping.json + ソース解析で判定する
    # パターンリストは空にし、collect_hits で別途処理する
    "skip_pure_python": [],
}

CATEGORY_LABELS: dict[str, str] = {
    "module_name":       "module name   ",
    "runtime_symbol":    "runtime symbol",
    "target_constant":   "target const  ",
    "prefix_match":      "prefix match  ",
    "class_name":        "class name    ",
    "python_syntax":     "Python syntax ",
    "type_id":           "type_id       ",
    "skip_pure_python":  "skip pure py  ",
}

# Runtime lint categories (only checked with --include-runtime)
RUNTIME_CATEGORIES: dict[str, list[str]] = {
    "rt:type_id": [
        r'PYTRA_TYPE_ID',
        r'PYTRA_TID_',
        r'pytra_isinstance',
        r'py_runtime_object_type_id',
        r'py_tid_',
        r'type_id_table',
    ],
    # rt:call_coverage — custom check (not grep-based); patterns list is empty.
    # Logic in _collect_rt_call_coverage_hits().
    "rt:call_coverage": [],
}

RUNTIME_CATEGORY_LABELS: dict[str, str] = {
    "rt:type_id":        "rt: type_id   ",
    "rt:call_coverage":  "rt: call_cov  ",
}

# Runtime file extensions per language
_RUNTIME_EXTENSIONS: dict[str, list[str]] = {
    "cpp":    [".h", ".cpp"],
    "rs":     [".rs"],
    "go":     [".go"],
    "ts":     [".ts"],
    "js":     [".js"],
    "cs":     [".cs"],
    "java":   [".java"],
    "ruby":   [".rb"],
    "lua":    [".lua"],
    "php":    [".php"],
    "nim":    [".nim"],
    "swift":  [".swift"],
    "kotlin": [".kt"],
    "scala":  [".scala"],
    "dart":   [".dart"],
    "zig":    [".zig"],
    "julia":  [".jl"],
    "ps1":    [".ps1"],
}


# ---------------------------------------------------------------------------
# rt:call_coverage — mapping.json calls vs EAST3 golden runtime_calls
# ---------------------------------------------------------------------------

_EAST3_ROOTS_FOR_COVERAGE = [
    ROOT / "test" / "fixture" / "east3",
    ROOT / "test" / "fixture" / "east3-opt",
    ROOT / "test" / "sample" / "east3",
    ROOT / "test" / "sample" / "east3-opt",
    ROOT / "test" / "stdlib" / "east3",
    ROOT / "test" / "stdlib" / "east3-opt",
    ROOT / "test" / "stdlib" / "linked",
    ROOT / "test" / "selfhost" / "east3",
    ROOT / "test" / "selfhost" / "east3-opt",
    ROOT / "test" / "pytra" / "east3",
    ROOT / "test" / "pytra" / "east3-opt",
]

_GOLDEN_CALLS_CACHE: set[str] | None = None


def _collect_golden_runtime_calls() -> set[str]:
    """Walk all EAST3 golden files and collect runtime_call / resolved_runtime_call values."""
    global _GOLDEN_CALLS_CACHE
    if _GOLDEN_CALLS_CACHE is not None:
        return _GOLDEN_CALLS_CACHE

    import json as _json

    def _walk(node: object, result: set[str]) -> None:
        if isinstance(node, dict):
            for key in (
                "runtime_call",
                "resolved_runtime_call",
                "with_enter_runtime_call",
                "with_exit_runtime_call",
            ):
                val = node.get(key)
                if isinstance(val, str) and val:
                    result.add(val)
            # Also collect runtime_module_id + runtime_symbol (fully qualified)
            for mod_key, sym_key in (
                ("runtime_module_id", "runtime_symbol"),
                ("with_enter_runtime_module_id", "with_enter_runtime_symbol"),
                ("with_exit_runtime_module_id", "with_exit_runtime_symbol"),
            ):
                mod_id = node.get(mod_key)
                sym = node.get(sym_key)
                if isinstance(mod_id, str) and mod_id and isinstance(sym, str) and sym:
                    result.add(mod_id + "." + sym)
            for v in node.values():
                _walk(v, result)
        elif isinstance(node, list):
            for item in node:
                _walk(item, result)

    calls: set[str] = set()
    for root in _EAST3_ROOTS_FOR_COVERAGE:
        if not root.exists():
            continue
        for path in root.rglob("*.east3"):
            try:
                doc = _json.loads(path.read_text(encoding="utf-8"))
                _walk(doc, calls)
            except Exception:
                pass

    _GOLDEN_CALLS_CACHE = calls
    return calls


_COVERAGE_META_PREFIXES = ("env.",)


def _collect_rt_call_coverage_hits(
    filter_lang: str | None,
) -> list[tuple[str, str, Path, int, str]]:
    """Return hits for mapping.json calls entries not covered by any EAST3 golden."""
    import json as _json

    all_golden = _collect_golden_runtime_calls()
    hits: list[tuple[str, str, Path, int, str]] = []

    # lang_key → runtime directory name (JS uses its own js/ dir, not ts/)
    lang_dir_map: dict[str, str] = {k: d for k, d in ALL_LANGS_ORDERED}
    lang_dir_map["js"] = "js"

    runtime_root = ROOT / "src" / "runtime"

    for lang_key, runtime_dir_name in sorted(lang_dir_map.items()):
        if filter_lang and lang_key != filter_lang:
            continue
        mapping_path = runtime_root / runtime_dir_name / "mapping.json"
        if not mapping_path.exists():
            continue
        try:
            doc = _json.loads(mapping_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        calls = doc.get("calls", {})
        for key in sorted(calls):
            if any(key.startswith(p) for p in _COVERAGE_META_PREFIXES):
                continue
            if key not in all_golden:
                line = f"calls[\"{key}\"] not found in any EAST3 golden"
                hits.append((lang_key, "rt:call_coverage", mapping_path, 0, line))

    return hits


# ---------------------------------------------------------------------------
# Pure Python module detection for skip_pure_python category
# ---------------------------------------------------------------------------

PYTRA_STD_DIR = ROOT / "src" / "pytra" / "std"


def _is_pure_python_module(module_name: str) -> bool:
    """Check if a pytra.std module is pure Python (no @extern decorators).

    A module with @extern is a native wrapper (OS/C API) and should be skipped.
    A module without @extern is pure Python and must be transpiled, not skipped.
    """
    # module_name may be "pytra.std.json" or "pytra.std." (prefix match)
    # For prefix matches, we can't check individual modules
    parts = module_name.split(".")
    if len(parts) < 3:
        return False
    stem = parts[2] if len(parts) >= 3 else ""
    if stem == "" or stem.startswith("_"):
        return False
    py_file = PYTRA_STD_DIR / (stem + ".py")
    if not py_file.exists():
        return False
    content = py_file.read_text(encoding="utf-8")
    has_extern = "@extern" in content
    return not has_extern


def _check_skip_pure_python(lang_key: str) -> list[tuple[str, str, Path, int, str]]:
    """Check if a language's mapping.json skips pure Python modules."""
    import json as _json
    hits: list[tuple[str, str, Path, int, str]] = []
    # Find mapping.json for this language
    lang_dir_map: dict[str, str] = {
        "cpp": "cpp", "rs": "rs", "go": "go", "ts": "ts",
        "cs": "cs", "java": "java", "kotlin": "kotlin",
        "swift": "swift", "dart": "dart", "ruby": "ruby",
        "lua": "lua", "scala": "scala", "php": "php",
        "nim": "nim", "julia": "julia", "zig": "zig",
        "ps1": "powershell", "js": "ts",
    }
    runtime_dir = lang_dir_map.get(lang_key, lang_key)
    mapping_path = ROOT / "src" / "runtime" / runtime_dir / "mapping.json"
    if not mapping_path.exists():
        return hits
    data = _json.loads(mapping_path.read_text(encoding="utf-8"))
    skip_modules = data.get("skip_modules", [])
    if not isinstance(skip_modules, list):
        return hits
    for entry in skip_modules:
        if not isinstance(entry, str):
            continue
        # Only check pytra.std.* entries (not pytra.built_in. or pytra.core.)
        if not entry.startswith("pytra.std."):
            continue
        # Prefix entries like "pytra.std." skip everything — check each module
        if entry == "pytra.std.":
            for py_file in sorted(PYTRA_STD_DIR.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                mod_name = "pytra.std." + py_file.stem
                if _is_pure_python_module(mod_name):
                    line = f"skip_modules contains \"{entry}\" which skips pure Python module {mod_name}"
                    hits.append((lang_key, "skip_pure_python", mapping_path, 0, line))
            continue
        # Exact or prefix match for specific module
        if _is_pure_python_module(entry):
            line = f"skip_modules contains \"{entry}\" but {entry} is pure Python (no @extern)"
            hits.append((lang_key, "skip_pure_python", mapping_path, 0, line))
    return hits


RUNTIME_LINT_CACHE = ROOT / ".parity-results" / "emitter_lint_runtime.json"


def _save_runtime_hits(hits: list[tuple[str, str, Path, int, str]], now: str) -> None:
    """Save runtime lint hits to a JSON cache so that non-runtime runs can merge them."""
    import json as _json
    entries = [
        {"lang": lang, "cat": cat, "file": str(fpath.relative_to(ROOT)), "lineno": lineno, "line": line}
        for lang, cat, fpath, lineno, line in hits
    ]
    RUNTIME_LINT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_LINT_CACHE.write_text(
        _json.dumps({"timestamp": now, "hits": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_runtime_hits_cache() -> list[tuple[str, str, Path, int, str]]:
    """Load previously saved runtime lint hits from cache."""
    import json as _json
    if not RUNTIME_LINT_CACHE.exists():
        return []
    try:
        data = _json.loads(RUNTIME_LINT_CACHE.read_text(encoding="utf-8"))
        return [
            (e["lang"], e["cat"], ROOT / e["file"], e["lineno"], e["line"])
            for e in data.get("hits", [])
        ]
    except Exception:
        return []


def collect_runtime_hits(
    filter_lang: str | None,
    filter_cat: str | None,
) -> list[tuple[str, str, Path, int, str]]:
    """Collect lint hits from src/runtime/<lang>/ source files."""
    hits: list[tuple[str, str, Path, int, str]] = []
    runtime_root = ROOT / "src" / "runtime"

    # lang_key → runtime directory name
    lang_dir_map: dict[str, str] = {k: d for k, d in ALL_LANGS_ORDERED}
    # JS shares TS runtime alias
    lang_dir_map["js"] = "js"

    for lang_key, runtime_dir_name in lang_dir_map.items():
        if filter_lang and lang_key != filter_lang:
            continue
        exts = _RUNTIME_EXTENSIONS.get(lang_key, [])
        if len(exts) == 0:
            continue
        runtime_dir = runtime_root / runtime_dir_name
        if not runtime_dir.exists():
            continue
        for fpath in sorted(runtime_dir.rglob("*")):
            if not fpath.is_file():
                continue
            if fpath.suffix not in exts:
                continue
            if "__pycache__" in str(fpath):
                continue
            # Skip generated files
            if "generated" in str(fpath):
                continue
            try:
                lines = fpath.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for lineno, raw in enumerate(lines, 1):
                stripped = raw.strip()
                # Skip comment lines (varies by language, simple heuristic)
                if stripped.startswith("//") or stripped.startswith("--") or stripped.startswith("#"):
                    continue
                for cat, patterns in RUNTIME_CATEGORIES.items():
                    if filter_cat and cat != filter_cat:
                        continue
                    if not patterns:
                        continue  # custom check, not grep-based
                    for pat in patterns:
                        if re.search(pat, raw):
                            hits.append((lang_key, cat, fpath, lineno, stripped[:120]))
                            break

    # rt:call_coverage: custom check (not grep-based)
    if not filter_cat or filter_cat == "rt:call_coverage":
        hits.extend(_collect_rt_call_coverage_hits(filter_lang))

    # rt:type_id: check mapping.json types table for deprecated type names
    _DEPRECATED_TYPE_KEYS = {"PyFile"}
    if not filter_cat or filter_cat == "rt:type_id":
        import json as _json2
        runtime_root = ROOT / "src" / "runtime"
        lang_dir_map2: dict[str, str] = {k: d for k, d in ALL_LANGS_ORDERED}
        lang_dir_map2["js"] = "js"
        for lang_key, runtime_dir_name in sorted(lang_dir_map2.items()):
            if filter_lang and lang_key != filter_lang:
                continue
            mapping_path = runtime_root / runtime_dir_name / "mapping.json"
            if not mapping_path.exists():
                continue
            try:
                doc = _json2.loads(mapping_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            types = doc.get("types", {})
            for key in sorted(types):
                if key in _DEPRECATED_TYPE_KEYS:
                    line = f"types[\"{key}\"] is deprecated (§12.7)"
                    hits.append((lang_key, "rt:type_id", mapping_path, 0, line))

    return hits


# ---------------------------------------------------------------------------
# Hit = (lang, category, file, lineno, line)
# ---------------------------------------------------------------------------

def collect_hits(
    filter_lang: str | None,
    filter_cat: str | None,
) -> list[tuple[str, str, Path, int, str]]:
    hits: list[tuple[str, str, Path, int, str]] = []

    def _is_known_false_positive(lang: str, cat: str, stripped: str) -> bool:
        if lang == "nim" and cat == "runtime_symbol":
            if stripped in ('_emit(ctx, "discard")', 'return "discard"'):
                return True
        return False

    # 除外ファイル:
    #   code_emitter.py  — mapping 読み込み共通基盤（禁止パターンの定義場所）
    #   types.py         — 型写像テーブル（"Exception": "Error" 等は正当）
    #   cli.py           — CLI エントリポイント（if __name__ == "__main__" は Python 標準ガード）
    EXCLUDE_NAMES = {"code_emitter.py", "types.py", "__init__.py", "cli.py", "cli_runner.py"}

    files = sorted(
        f for f in EMIT_DIR.rglob("*.py")
        if "__pycache__" not in str(f) and f.name not in EXCLUDE_NAMES
    )

    # emit サブディレクトリ名 → 表示キー（ALL_LANG_KEYS に含まれないものは common 扱い）
    dir_to_key = {d: k for k, d in ALL_LANGS_ORDERED}

    for fpath in files:
        rel = fpath.relative_to(EMIT_DIR)
        dir_name = rel.parts[0] if len(rel.parts) > 1 else "common"
        lang = dir_to_key.get(dir_name, "common")

        if filter_lang and lang != filter_lang:
            continue

        lines = fpath.read_text(encoding="utf-8").splitlines()
        for lineno, raw in enumerate(lines, 1):
            stripped = raw.strip()
            # コメント行はスキップ
            if stripped.startswith("#"):
                continue
            # docstring の先頭行（""" で始まる）はスキップ
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            for cat, patterns in CATEGORIES.items():
                if filter_cat and cat != filter_cat:
                    continue
                for pat in patterns:
                    if re.search(pat, raw):
                        if _is_known_false_positive(lang, cat, stripped):
                            continue
                        hits.append((lang, cat, fpath, lineno, stripped[:120]))
                        break  # 1行につき同カテゴリの重複カウントを避ける

    # skip_pure_python: check mapping.json skip_modules against pure Python sources
    if not filter_cat or filter_cat == "skip_pure_python":
        for lang_key, _dir in ALL_LANGS_ORDERED:
            if filter_lang and lang_key != filter_lang:
                continue
            hits.extend(_check_skip_pure_python(lang_key))

    return hits


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def implemented_langs() -> set[str]:
    """toolchain/emit/ に実際にディレクトリが存在する言語キー + エイリアス先が実装済みの言語キーの集合。"""
    dir_to_key = {d: k for k, d in ALL_LANGS_ORDERED}
    direct = {
        dir_to_key[p.name]
        for p in EMIT_DIR.iterdir()
        if p.is_dir() and p.name in dir_to_key
    }
    aliased = {lang for lang, target in LANG_EMITTER_ALIAS.items() if target in direct}
    return direct | aliased


def build_matrix(
    hits: list[tuple[str, str, Path, int, str]],
    langs: list[str],
    *,
    include_runtime: bool = False,
) -> dict[str, dict[str, int | None]]:
    """None = 未実装、0以上 = 実装済み（違反数）"""
    impl = implemented_langs()
    all_cats: dict[str, list[str]] = dict(CATEGORIES)
    if include_runtime:
        for k, v in RUNTIME_CATEGORIES.items():
            all_cats[k] = v
    mat: dict[str, dict[str, int | None]] = {
        cat: {lang: (0 if lang in impl else None) for lang in langs}
        for cat in all_cats
    }
    # runtime カテゴリは runtime ディレクトリの存在で判定
    if include_runtime:
        runtime_root = ROOT / "src" / "runtime"
        for cat in RUNTIME_CATEGORIES:
            for lang in langs:
                runtime_dir_name = {k: d for k, d in ALL_LANGS_ORDERED}.get(lang, lang)
                if (runtime_root / runtime_dir_name).exists():
                    mat[cat][lang] = 0
                else:
                    mat[cat][lang] = None
    for lang, cat, _f, _ln, _line in hits:
        if cat in mat and lang in mat[cat]:
            mat[cat][lang] = (mat[cat][lang] or 0) + 1
    # エイリアス言語はターゲットの結果をそのままコピー
    for alias, target in LANG_EMITTER_ALIAS.items():
        if alias in langs and target in langs:
            for cat in mat:
                mat[cat][alias] = mat[cat][target]
    return mat


def _cell(n: int | None) -> str:
    if n is None:
        return "⬜"
    return "🟥" if n else "🟩"


def lang_total(mat: dict[str, dict[str, int | None]], lang: str) -> int | None:
    """Sum of all category violation counts for one language. None if unimplemented."""
    total: int | None = None
    for cat_data in mat.values():
        v = cat_data.get(lang)
        if v is None:
            continue
        total = (total or 0) + v
    return total


def _lang_pass_count(mat: dict[str, dict[str, int | None]], lang: str) -> int | None:
    """Number of categories with 0 violations. None if unimplemented."""
    if lang_total(mat, lang) is None:
        return None
    return sum(1 for cat_data in mat.values() if cat_data.get(lang) == 0)


def _lang_fail_count(mat: dict[str, dict[str, int | None]], lang: str) -> int | None:
    """Number of categories with >0 violations. None if unimplemented."""
    if lang_total(mat, lang) is None:
        return None
    return sum(1 for cat_data in mat.values() if (cat_data.get(lang) or 0) > 0)


def _lang_unimpl_count(mat: dict[str, dict[str, int | None]], lang: str) -> int | None:
    """Total category count if lang is unimplemented, else None."""
    if lang_total(mat, lang) is not None:
        return None
    return len(mat)


def _count_cell(n: int | None) -> str:
    """Format a count for totals rows: number or '—'."""
    return "—" if n is None or n == 0 else str(n)


def _all_category_labels(mat: dict[str, dict[str, int | None]]) -> dict[str, str]:
    """Return combined emitter + runtime category labels for categories present in mat."""
    labels: dict[str, str] = {}
    for cat in mat:
        if cat in CATEGORY_LABELS:
            labels[cat] = CATEGORY_LABELS[cat]
        elif cat in RUNTIME_CATEGORY_LABELS:
            labels[cat] = RUNTIME_CATEGORY_LABELS[cat]
        else:
            labels[cat] = cat
    return labels


def print_matrix(mat: dict[str, dict[str, int | None]], langs: list[str]) -> None:
    header = "| カテゴリ           | " + " | ".join(langs) + " |"
    sep    = "|" + "-" * (len(header) - 2) + "|"
    print(header)
    print(sep)
    all_labels = _all_category_labels(mat)
    for cat, label in all_labels.items():
        if cat not in mat:
            continue
        cells = [_cell(mat[cat][l]) for l in langs]
        print(f"| {label} | " + " | ".join(cells) + " |")
    # Totals rows
    pass_cells  = [_count_cell(_lang_pass_count(mat, l))  for l in langs]
    fail_cells  = [_count_cell(_lang_fail_count(mat, l))  for l in langs]
    unimpl_cells = [_count_cell(_lang_unimpl_count(mat, l)) for l in langs]
    print(f"| **🟩 PASS** | " + " | ".join(pass_cells) + " |")
    print(f"| **🟥 FAIL** | " + " | ".join(fail_cells) + " |")
    print(f"| **⬜ 未実装** | " + " | ".join(unimpl_cells) + " |")


def print_verbose(
    hits: list[tuple[str, str, Path, int, str]],
    langs: list[str],
) -> None:
    from itertools import groupby
    key = lambda h: (h[1], h[0])
    for (cat, lang), group in groupby(sorted(hits, key=key), key=key):
        entries = list(group)
        print(f"\n  [{cat}] {lang} ({len(entries)} 件)")
        for _lang, _cat, fpath, lineno, line in entries:
            rel = fpath.relative_to(ROOT)
            print(f"    {rel}:{lineno}: {line}")


# ---------------------------------------------------------------------------
# Markdown ファイル出力
# ---------------------------------------------------------------------------

def _render_md(
    mat: dict[str, dict[str, int]],
    hits: list[tuple[str, str, Path, int, str]],
    langs: list[str],
    now: str,
    lang: str,  # "ja" or "en"
) -> str:
    is_ja = lang == "ja"
    other_lang = "en" if is_ja else "ja"
    badge_label = "Read in English" if is_ja else "日本語で読む"
    badge_color = "2563EB" if is_ja else "DC2626"
    badge_text  = "English" if is_ja else "日本語"

    lines: list[str] = []
    lines.append(f'<a href="../../{other_lang}/progress-preview/emitter-hardcode-lint.md">')
    lines.append(f'  <img alt="{badge_label}" src="https://img.shields.io/badge/docs-{badge_text}-{badge_color}?style=flat-square">')
    lines.append("</a>")
    lines.append("")

    if is_ja:
        lines.append("# emitter ハードコード違反マトリクス")
        lines.append("")
        lines.append("> 機械生成ファイル。`python3 tools/check/check_emitter_hardcode_lint.py` で更新する。")
        lines.append(f"> 生成日時: {now}")
        lines.append("> [関連リンク](./index.md)")
        lines.append("")
        lines.append("emitter が EAST3 の情報を使わず、モジュール名・runtime 関数名・クラス名等を文字列で直書きしている箇所を grep で検出したマトリクス。")
        lines.append("違反数が 0 に近づくほど emitter が EAST3 正本に従った実装になっている。")
        lines.append("")
        lines.append("| アイコン | 意味 |")
        lines.append("|---|---|")
        lines.append("| 🟩 | 違反なし |")
        lines.append("| 🟥 | 違反あり（詳細は下の表を参照） |")
        lines.append("| ⬜ | 未実装（toolchain に emitter なし） |")
        lines.append("")
        lines.append("> **js** は独自 emitter を持たず **ts** emitter を共用するため、js 列は ts と同一の結果を表示する。")
        lines.append("")
        cat_header = "| カテゴリ"
        cat_sep    = "|---"
    else:
        lines.append("# Emitter hardcode violation matrix")
        lines.append("")
        lines.append("> Machine-generated file. Run `python3 tools/check/check_emitter_hardcode_lint.py` to update.")
        lines.append(f"> Generated at: {now}")
        lines.append("> [Links](./index.md)")
        lines.append("")
        lines.append("Matrix of grep-detected violations where the emitter hardcodes module names, runtime symbols, or class names instead of using EAST3 data.")
        lines.append("Fewer violations means the emitter is more faithfully following the EAST3 source of truth.")
        lines.append("")
        lines.append("| Icon | Meaning |")
        lines.append("|---|---|")
        lines.append("| 🟩 | No violations |")
        lines.append("| 🟥 | Violations found (see details below) |")
        lines.append("| ⬜ | Not implemented (no emitter in toolchain) |")
        lines.append("")
        lines.append("> **js** shares the **ts** emitter and has no separate implementation; the js column mirrors ts results.")
        lines.append("")
        cat_header = "| Category"
        cat_sep    = "|---"

    # マトリクステーブル
    header = cat_header + " | " + " | ".join(langs) + " |"
    sep    = cat_sep + " | " + " | ".join(["---:"] * len(langs)) + " |"
    lines.append(header)
    lines.append(sep)
    all_labels = _all_category_labels(mat)
    for cat, label in all_labels.items():
        if cat not in mat:
            continue
        cells = [_cell(mat[cat][l]) for l in langs]
        lines.append(f"| {label.strip()} | " + " | ".join(cells) + " |")
    # Totals rows [P0-PROGRESS-SUMMARY-S3]
    pass_cells   = [_count_cell(_lang_pass_count(mat, l))   for l in langs]
    fail_cells   = [_count_cell(_lang_fail_count(mat, l))   for l in langs]
    unimpl_cells = [_count_cell(_lang_unimpl_count(mat, l)) for l in langs]
    unimpl_label = "**⬜ 未実装**" if is_ja else "**⬜ Not impl.**"
    lines.append(f"| **🟩 PASS** | " + " | ".join(pass_cells) + " |")
    lines.append(f"| **🟥 FAIL** | " + " | ".join(fail_cells) + " |")
    lines.append(f"| {unimpl_label} | " + " | ".join(unimpl_cells) + " |")
    lines.append("")

    # 詳細セクション
    if is_ja:
        lines.append("## 詳細")
    else:
        lines.append("## Details")
    lines.append("")

    from itertools import groupby
    key = lambda h: (h[1], h[0])
    for (cat, l), group in groupby(sorted(hits, key=key), key=key):
        entries = list(group)
        lines.append(f"### {cat} / {l} ({len(entries)})")
        lines.append("")
        lines.append("```")
        for _lang, _cat, fpath, lineno, line in entries:
            rel = fpath.relative_to(ROOT)
            lines.append(f"{rel}:{lineno}: {line}")
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def write_progress_pages(
    mat: dict[str, dict[str, int]],
    hits: list[tuple[str, str, Path, int, str]],
    langs: list[str],
    now: str,
) -> None:
    for lang_code in ("ja", "en"):
        out_path = ROOT / "docs" / lang_code / "progress-preview" / "emitter-hardcode-lint.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        content = _render_md(mat, hits, langs, now, lang_code)
        out_path.write_text(content, encoding="utf-8")
        print(f"  -> {out_path.relative_to(ROOT)}")
    # Write JSON summary for gen_backend_progress.py [P0-PROGRESS-SUMMARY-S3]
    import json
    parity_dir = ROOT / ".parity-results"
    parity_dir.mkdir(parents=True, exist_ok=True)
    json_path = parity_dir / "emitter_lint.json"
    total_cats = len(mat)

    # Load previous results for changelog comparison [P1-LINT-CHANGELOG-S1]
    prev_pass_cats: dict[str, int | None] = {}
    if json_path.exists():
        try:
            prev = json.loads(json_path.read_text(encoding="utf-8"))
            for lang, data in prev.get("langs", {}).items():
                prev_pass_cats[lang] = data.get("pass_cats")
        except Exception:
            pass

    json_data = {
        "timestamp": now,
        "langs": {
            lang: {
                "violations": lang_total(mat, lang),
                "pass_cats": _lang_pass_count(mat, lang),
                "total_cats": total_cats if lang_total(mat, lang) is not None else None,
            }
            for lang in langs
        },
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {json_path.relative_to(ROOT)}")

    # Append changelog entries for changed langs [P1-LINT-CHANGELOG-S1]
    try:
        import sys as _sys
        _tools_check = str(ROOT / "tools" / "check")
        if _tools_check not in _sys.path:
            _sys.path.insert(0, _tools_check)
        from runtime_parity_check import _append_parity_changelog  # type: ignore
        for lang, data in json_data["langs"].items():
            curr = data.get("pass_cats")
            if curr is None:
                continue
            prev = prev_pass_cats.get(lang)
            if prev is None:
                continue
            _append_parity_changelog(lang, "lint", int(prev), int(curr), now)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="emitter 責務違反チェッカー")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="違反箇所を詳細表示する")
    parser.add_argument("--lang", default=None,
                        help="対象言語を絞り込む（例: go, cpp, rs, ts）")
    parser.add_argument("--category", default=None,
                        help="対象カテゴリを絞り込む（例: module_name）")
    parser.add_argument("--no-write", action="store_true",
                        help="docs/progress/ への書き出しをスキップする")
    parser.add_argument("--skip-runtime", action="store_true",
                        help="src/runtime/ の検査をスキップする（デバッグ用）")
    args = parser.parse_args()

    hits = collect_hits(args.lang, args.category)
    runtime_hits: list[tuple[str, str, Path, int, str]] = []
    if not args.skip_runtime:
        runtime_hits = collect_runtime_hits(args.lang, args.category)
    hits.extend(runtime_hits)
    has_runtime = not args.skip_runtime

    # 全18言語を README バッジ順で固定（toolchain 未実装言語は 🟩0 で表示）
    if args.lang:
        all_langs = [args.lang] if args.lang in ALL_LANG_KEYS else [args.lang]
    else:
        all_langs = ALL_LANG_KEYS

    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = len(hits)
    print(f"\n=== emitter hardcode lint — {total} 件の違反 ===\n")

    mat = build_matrix(hits, all_langs, include_runtime=has_runtime)
    print_matrix(mat, all_langs)


    if args.verbose and hits:
        print("\n--- 詳細 ---")
        print_verbose(hits, all_langs)

    # --lang / --category で絞り込んでいる場合はファイル出力しない
    if not args.no_write and not args.lang and not args.category:
        print()
        write_progress_pages(mat, hits, all_langs, now)

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

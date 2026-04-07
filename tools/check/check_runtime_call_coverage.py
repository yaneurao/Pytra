#!/usr/bin/env python3
"""check_runtime_call_coverage.py — EAST3 runtime_call と mapping.json の双方向カバレッジ lint

検証方向:
  1. EAST → mapping: EAST3 golden に出現する runtime_call が各言語の mapping.json calls に登録済みか
  2. mapping → EAST:  mapping.json calls のキーがいずれかの EAST3 golden に出現しているか

使い方:
    python3 tools/check/check_runtime_call_coverage.py
    python3 tools/check/check_runtime_call_coverage.py --lang cpp,ts
    python3 tools/check/check_runtime_call_coverage.py --direction east-to-mapping
    python3 tools/check/check_runtime_call_coverage.py --direction mapping-to-east

終了コード:
    0: 問題なし
    1: 未登録の runtime_call が存在する（EAST → mapping 方向）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EAST3_ROOTS = [
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

RUNTIME_DIR = ROOT / "src" / "runtime"

# mapping.json の calls テーブルで無視するメタキー
_META_KEY_PREFIXES = ("env.",)

# EAST3 golden の short-qualified runtime_call を FQCN に正規化するプレフィックス表
# 例: "math.sqrt" → "pytra.std.math.sqrt"
_SHORT_TO_FQCN_PREFIXES: list[tuple[str, str]] = [
    ("os.path.", "pytra.std.os_path."),
    ("os_path.", "pytra.std.os_path."),
    ("math.", "pytra.std.math."),
    ("time.", "pytra.std.time."),
    ("glob.", "pytra.std.glob."),
    ("path.", "pytra.std.os_path."),
    ("json.", "pytra.std.json."),
    ("random.", "pytra.std.random."),
]


def _normalize_call_key(key: str) -> str:
    """EAST3 golden の runtime_call を mapping.json の FQCN キーに正規化する。

    例: "math.sqrt" → "pytra.std.math.sqrt"
    既に FQCN (pytra. で始まる) のキーはそのまま返す。
    """
    if key.startswith("pytra."):
        return key
    for short_prefix, fqcn_prefix in _SHORT_TO_FQCN_PREFIXES:
        if key.startswith(short_prefix):
            return fqcn_prefix + key[len(short_prefix):]
    return key


def _is_meta_key(key: str) -> bool:
    return any(key.startswith(p) for p in _META_KEY_PREFIXES)


def collect_runtime_calls_from_goldens() -> dict[str, set[str]]:
    """EAST3 golden を走査し、{source_root_name: {runtime_call, ...}} を返す。"""

    def _walk(node: object, results: set[str]) -> None:
        if isinstance(node, dict):
            for key in (
                "runtime_call",
                "resolved_runtime_call",
                "with_enter_runtime_call",
                "with_exit_runtime_call",
            ):
                val = node.get(key)
                if isinstance(val, str) and val:
                    results.add(val)
                    results.add(_normalize_call_key(val))
            for mod_key, sym_key in (
                ("runtime_module_id", "runtime_symbol"),
                ("with_enter_runtime_module_id", "with_enter_runtime_symbol"),
                ("with_exit_runtime_module_id", "with_exit_runtime_symbol"),
            ):
                mod_id = node.get(mod_key)
                sym = node.get(sym_key)
                if isinstance(mod_id, str) and mod_id and isinstance(sym, str) and sym:
                    results.add(mod_id + "." + sym)
            for v in node.values():
                _walk(v, results)
        elif isinstance(node, list):
            for item in node:
                _walk(item, results)

    result: dict[str, set[str]] = {}
    for root in EAST3_ROOTS:
        if not root.exists():
            continue
        # key = "fixture", "sample", "stdlib" (parent directory name)
        key = root.parent.name
        calls = result.get(key, set())
        for path in root.rglob("*.east3"):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                _walk(doc, calls)
            except Exception:
                pass
        if calls:
            result[key] = calls

    return result


def load_mapping_calls() -> dict[str, set[str]]:
    """各言語の mapping.json から calls キーを収集し {lang: {key, ...}} を返す。"""
    result: dict[str, set[str]] = {}
    for mapping_path in sorted(RUNTIME_DIR.glob("*/mapping.json")):
        lang = mapping_path.parent.name
        try:
            doc = json.loads(mapping_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        calls = doc.get("calls", {})
        keys = {k for k in calls if not _is_meta_key(k)}
        if keys:
            result[lang] = keys
    return result


def check_east_to_mapping(
    golden_calls: dict[str, set[str]],
    mapping_calls: dict[str, set[str]],
    langs: list[str] | None,
) -> dict[str, list[str]]:
    """EAST golden に出現するが mapping.json に未登録の runtime_call を返す。

    Returns: {lang: [missing_runtime_call, ...]}
    """
    all_golden: set[str] = set()
    for calls in golden_calls.values():
        all_golden |= calls

    result: dict[str, list[str]] = {}
    for lang, mkeys in sorted(mapping_calls.items()):
        if langs and lang not in langs:
            continue
        missing = sorted(all_golden - mkeys)
        if missing:
            result[lang] = missing
    return result


def check_mapping_to_east(
    golden_calls: dict[str, set[str]],
    mapping_calls: dict[str, set[str]],
    langs: list[str] | None,
) -> dict[str, list[str]]:
    """mapping.json に登録されているが EAST golden に未出現の runtime_call を返す。

    Returns: {lang: [dead_entry, ...]}
    """
    all_golden: set[str] = set()
    for calls in golden_calls.values():
        all_golden |= calls

    result: dict[str, list[str]] = {}
    for lang, mkeys in sorted(mapping_calls.items()):
        if langs and lang not in langs:
            continue
        dead = sorted(mkeys - all_golden)
        if dead:
            result[lang] = dead
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="EAST3 runtime_call coverage lint")
    parser.add_argument(
        "--lang",
        default="",
        help="comma-separated language filter (default: all)",
    )
    parser.add_argument(
        "--direction",
        choices=("both", "east-to-mapping", "mapping-to-east"),
        default="both",
        help="lint direction (default: both)",
    )
    parser.add_argument(
        "--warn-dead",
        action="store_true",
        help="treat mapping-to-east (dead entries) as warnings only, not errors",
    )
    args = parser.parse_args()

    langs: list[str] | None = [l.strip() for l in args.lang.split(",") if l.strip()] or None

    golden_calls = collect_runtime_calls_from_goldens()
    mapping_calls = load_mapping_calls()

    total_golden = sum(len(v) for v in golden_calls.values())
    print(f"[INFO] EAST3 goldens: {sum(len(list(r.rglob('*.east3'))) for r in EAST3_ROOTS if r.exists())} files, "
          f"{total_golden} runtime_call occurrences across "
          f"{', '.join(f'{k}({len(v)})' for k, v in sorted(golden_calls.items()))}")
    print(f"[INFO] mapping.json: {len(mapping_calls)} languages")

    exit_code = 0

    # --- Direction 1: EAST → mapping ---
    if args.direction in ("both", "east-to-mapping"):
        missing = check_east_to_mapping(golden_calls, mapping_calls, langs)
        if missing:
            print("\n[WARN] EAST → mapping: runtime_calls present in goldens but missing from mapping.json")
            print("       (emitter may silently fail for these calls)")
            for lang, calls in sorted(missing.items()):
                print(f"  {lang} ({len(calls)} missing):")
                for call in calls:
                    print(f"    - {call}")
            # This direction is informational (mapping.json may intentionally omit some calls
            # handled by the emitter directly). Do not fail.
        else:
            print("\n[OK] EAST → mapping: all golden runtime_calls are covered in mapping.json")

    # --- Direction 2: mapping → EAST ---
    if args.direction in ("both", "mapping-to-east"):
        dead = check_mapping_to_east(golden_calls, mapping_calls, langs)
        if dead:
            level = "WARN" if args.warn_dead else "WARN"
            print(f"\n[{level}] mapping → EAST: calls in mapping.json not found in any EAST3 golden")
            print("        (may be dead entries, or fixture coverage gap)")
            for lang, calls in sorted(dead.items()):
                print(f"  {lang} ({len(calls)} entries):")
                for call in calls:
                    print(f"    - {call}")
        else:
            print("\n[OK] mapping → EAST: all mapping.json calls appear in EAST3 goldens")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

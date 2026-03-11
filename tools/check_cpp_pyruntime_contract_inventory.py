#!/usr/bin/env python3
"""Guard the remaining py_runtime contract callers by category."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"

SYMBOL_PATTERNS = {
    "py_append": re.compile(r"\bpy_append\("),
    "py_extend": re.compile(r"\bpy_extend\("),
    "py_pop": re.compile(r"\bpy_pop\("),
    "py_clear": re.compile(r"\bpy_clear\("),
    "py_reverse": re.compile(r"\bpy_reverse\("),
    "py_sort": re.compile(r"\bpy_sort\("),
    "py_set_at": re.compile(r"\bpy_set_at\("),
    "py_runtime_type_id": re.compile(r"\bpy_runtime_type_id\("),
    "py_isinstance": re.compile(r"\bpy_isinstance\("),
    "py_is_subtype": re.compile(r"\bpy_is_subtype\("),
}

TRACKED_SUFFIXES = {".py", ".cpp", ".h", ".rs", ".cs"}
EXCLUDED_PATHS = {
    "src/runtime/cpp/native/core/py_runtime.h",
}

EXPECTED_BUCKETS = {
    "typed_lane_removable": {
        ("py_append", "src/backends/cpp/emitter/call.py"),
        ("py_append", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_extend", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_pop", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_clear", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_reverse", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_sort", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_set_at", "src/backends/cpp/emitter/stmt.py"),
    },
    "object_bridge_required": {
        ("py_append", "src/runtime/cpp/generated/built_in/iter_ops.cpp"),
        ("py_append", "src/runtime/cpp/generated/std/json.cpp"),
        ("py_isinstance", "src/runtime/cpp/generated/std/json.cpp"),
    },
    "shared_runtime_contract": {
        ("py_runtime_type_id", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_isinstance", "src/backends/cpp/emitter/runtime_expr.py"),
        ("py_is_subtype", "src/backends/cpp/emitter/runtime_expr.py"),
        ("py_isinstance", "src/backends/cpp/emitter/stmt.py"),
        ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_isinstance", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_is_subtype", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_isinstance", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_is_subtype", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id", "src/runtime/cpp/generated/built_in/type_id.cpp"),
        ("py_isinstance", "src/runtime/cpp/generated/built_in/type_id.cpp"),
        ("py_isinstance", "src/runtime/cpp/native/compiler/backend_registry_static.cpp"),
        ("py_isinstance", "src/runtime/cpp/native/compiler/transpile_cli.cpp"),
        ("py_runtime_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_append", "src/runtime/cs/pytra/utils/gif.cs"),
        ("py_append", "src/runtime/cs/pytra/utils/png.cs"),
        ("py_runtime_type_id", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_isinstance", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_is_subtype", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_runtime_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_type_id", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
        ("py_is_subtype", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
    },
}


def _iter_target_files() -> list[Path]:
    return [
        path
        for path in sorted(SRC_ROOT.rglob("*"))
        if path.is_file()
        and path.suffix in TRACKED_SUFFIXES
        and path.relative_to(ROOT).as_posix() not in EXCLUDED_PATHS
    ]


def _collect_observed_pairs() -> set[tuple[str, str]]:
    observed: set[tuple[str, str]] = set()
    for path in _iter_target_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for symbol, pattern in SYMBOL_PATTERNS.items():
            if pattern.search(text) is not None:
                observed.add((symbol, rel))
    return observed


def _collect_expected_pairs() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for entries in EXPECTED_BUCKETS.values():
        out.update(entries)
    return out


def _collect_bucket_overlaps() -> list[str]:
    issues: list[str] = []
    bucket_names = list(EXPECTED_BUCKETS.keys())
    for idx, left_name in enumerate(bucket_names):
        left = EXPECTED_BUCKETS[left_name]
        for right_name in bucket_names[idx + 1 :]:
            overlap = left & EXPECTED_BUCKETS[right_name]
            for symbol, rel in sorted(overlap):
                issues.append(
                    f"bucket overlap: {left_name} and {right_name} both include {symbol} @ {rel}"
                )
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    for symbol, rel in sorted(expected - observed):
        issues.append(f"expected entry missing from source inventory: {symbol} @ {rel}")
    for symbol, rel in sorted(observed - expected):
        issues.append(f"unclassified py_runtime contract caller: {symbol} @ {rel}")
    for bucket_name, entries in EXPECTED_BUCKETS.items():
        if len(entries) == 0:
            issues.append(f"bucket has no entries: {bucket_name}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    if len(issues) == 0:
        print("[OK] cpp py_runtime contract inventory is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

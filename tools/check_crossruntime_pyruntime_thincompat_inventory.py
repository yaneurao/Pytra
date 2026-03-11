#!/usr/bin/env python3
"""Guard emitter-side blockers for removing the final thin py_runtime helpers."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TRACKED_PATHS = {
    "src/backends/cpp/emitter/runtime_expr.py",
    "src/backends/cpp/emitter/stmt.py",
    "src/backends/rs/emitter/rs_emitter.py",
    "src/backends/cs/emitter/cs_emitter.py",
}

CPP_BLOCKER_RULES = {
    ("py_isinstance", "src/backends/cpp/emitter/runtime_expr.py"): re.compile(r"\bpy_isinstance\s*\("),
    ("py_isinstance", "src/backends/cpp/emitter/stmt.py"): re.compile(r"\bpy_isinstance\s*\("),
}

CROSSRUNTIME_RULES = {
    ("py_runtime_value_type_id", "src/backends/rs/emitter/rs_emitter.py"): re.compile(
        r'return "py_runtime_value_type_id\(&" \+ value_expr \+ "\)"'
    ),
    ("py_runtime_value_isinstance", "src/backends/rs/emitter/rs_emitter.py"): re.compile(
        r'py_runtime_value_isinstance\(&" \+ value_expr'
    ),
    ("py_runtime_type_id_is_subtype", "src/backends/rs/emitter/rs_emitter.py"): re.compile(
        r'py_runtime_type_id_is_subtype\(" \+ actual_type_id'
    ),
    ("py_runtime_type_id_issubclass", "src/backends/rs/emitter/rs_emitter.py"): re.compile(
        r'py_runtime_type_id_issubclass\(" \+ actual_type_id'
    ),
    ("py_runtime_value_type_id", "src/backends/cs/emitter/cs_emitter.py"): re.compile(
        r'Pytra\.CsModule\.py_runtime\.py_runtime_value_type_id\('
    ),
    ("py_runtime_value_isinstance", "src/backends/cs/emitter/cs_emitter.py"): re.compile(
        r'Pytra\.CsModule\.py_runtime\.py_runtime_value_isinstance\('
    ),
    ("py_runtime_type_id_is_subtype", "src/backends/cs/emitter/cs_emitter.py"): re.compile(
        r'Pytra\.CsModule\.py_runtime\.py_runtime_type_id_is_subtype\('
    ),
    ("py_runtime_type_id_issubclass", "src/backends/cs/emitter/cs_emitter.py"): re.compile(
        r'Pytra\.CsModule\.py_runtime\.py_runtime_type_id_issubclass\('
    ),
}

EXPECTED_BUCKETS = {
    "cpp_header_thincompat_blocker": set(),
    "crossruntime_shared_type_id_api": {
        ("py_runtime_value_type_id", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_value_isinstance", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_value_type_id", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_value_isinstance", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/backends/cs/emitter/cs_emitter.py"),
    },
}


def _iter_target_files() -> list[Path]:
    return [ROOT / rel for rel in sorted(TRACKED_PATHS)]


def _collect_observed_pairs() -> set[tuple[str, str]]:
    observed: set[tuple[str, str]] = set()
    for path in _iter_target_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for (symbol, rule_path), pattern in CPP_BLOCKER_RULES.items():
            if rel == rule_path and pattern.search(text) is not None:
                observed.add((symbol, rel))
        for (symbol, rule_path), pattern in CROSSRUNTIME_RULES.items():
            if rel == rule_path and pattern.search(text) is not None:
                observed.add((symbol, rel))
    return observed


def _collect_expected_pairs() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for entries in EXPECTED_BUCKETS.values():
        out.update(entries)
    return out


def _collect_bucket_overlaps() -> list[str]:
    issues: list[str] = []
    names = list(EXPECTED_BUCKETS.keys())
    for idx, left_name in enumerate(names):
        left = EXPECTED_BUCKETS[left_name]
        for right_name in names[idx + 1 :]:
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
        issues.append(f"expected entry missing from thincompat inventory: {symbol} @ {rel}")
    for symbol, rel in sorted(observed - expected):
        issues.append(f"unclassified thincompat blocker/residual: {symbol} @ {rel}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    if not issues:
        print("[OK] crossruntime py_runtime thincompat inventory is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Guard residual py_runtime symbols across the C++/Rust/C# emitters."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SYMBOL_PATTERNS = {
    symbol: re.compile(rf"\b{re.escape(symbol)}\b")
    for symbol in {
        "py_runtime_object_type_id",
        "py_runtime_object_isinstance",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_append",
        "py_extend",
        "py_pop",
        "py_clear",
        "py_reverse",
        "py_sort",
        "py_set_at",
    }
}

TRACKED_PATHS = {
    "src/backends/cpp/emitter/call.py",
    "src/backends/cpp/emitter/cpp_emitter.py",
    "src/backends/cpp/emitter/runtime_expr.py",
    "src/backends/cpp/emitter/stmt.py",
    "src/backends/rs/emitter/rs_emitter.py",
    "src/backends/cs/emitter/cs_emitter.py",
}

EXPECTED_BUCKETS = {
    "cpp_emitter_object_bridge_residual": {
        ("py_runtime_object_type_id", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_runtime_object_isinstance", "src/backends/cpp/emitter/runtime_expr.py"),
        ("py_runtime_object_isinstance", "src/backends/cpp/emitter/stmt.py"),
    },
    "cpp_emitter_shared_type_id_residual": {
        ("py_runtime_type_id_is_subtype", "src/backends/cpp/emitter/runtime_expr.py"),
        ("py_runtime_type_id_issubclass", "src/backends/cpp/emitter/runtime_expr.py"),
    },
    "rs_emitter_shared_type_id_residual": {
        ("py_runtime_value_type_id", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_value_isinstance", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/backends/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/backends/rs/emitter/rs_emitter.py"),
    },
    "cs_emitter_shared_type_id_residual": {
        ("py_runtime_value_type_id", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_value_isinstance", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/backends/cs/emitter/cs_emitter.py"),
    },
    "crossruntime_mutation_helper_residual": {
        ("py_append", "src/backends/cpp/emitter/call.py"),
        ("py_extend", "src/backends/cpp/emitter/call.py"),
        ("py_pop", "src/backends/cpp/emitter/call.py"),
        ("py_clear", "src/backends/cpp/emitter/call.py"),
        ("py_reverse", "src/backends/cpp/emitter/call.py"),
        ("py_sort", "src/backends/cpp/emitter/call.py"),
        ("py_set_at", "src/backends/cpp/emitter/call.py"),
        ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
    },
}


def _iter_target_files() -> list[Path]:
    return [ROOT / rel for rel in sorted(TRACKED_PATHS)]


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
        issues.append(f"unclassified crossruntime emitter py_runtime caller: {symbol} @ {rel}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    if len(issues) == 0:
        print("[OK] crossruntime py_runtime emitter inventory is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

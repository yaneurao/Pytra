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

CPP_TYPED_LANE_DIRECT_MUTATION_SYMBOLS = {
    "py_list_append_mut",
    "py_list_extend_mut",
    "py_list_pop_mut",
    "py_list_clear_mut",
    "py_list_reverse_mut",
    "py_list_sort_mut",
    "py_list_set_at_mut",
}

CPP_OBJECT_BRIDGE_WRAPPER_SYMBOLS = {
    "py_append",
    "py_extend",
    "py_pop",
    "py_clear",
    "py_reverse",
    "py_sort",
    "py_set_at",
}

TRACKED_PATHS = {
    "src/backends/cpp/emitter/call.py",
    "src/backends/cpp/emitter/cpp_emitter.py",
    "src/backends/cpp/emitter/runtime_expr.py",
    "src/backends/cpp/emitter/stmt.py",
    "src/backends/rs/emitter/rs_emitter.py",
    "src/backends/cs/emitter/cs_emitter.py",
}

CPP_TYPED_WRAPPER_SYMBOLS = {
    "py_append",
    "py_extend",
    "py_pop",
    "py_clear",
    "py_reverse",
    "py_sort",
    "py_set_at",
}

CPP_TYPED_WRAPPER_FORBIDDEN_PATHS = {
    "src/backends/cpp/emitter/cpp_emitter.py",
    "src/backends/cpp/emitter/runtime_expr.py",
    "src/backends/cpp/emitter/stmt.py",
}

CPP_TYPED_LANE_DIRECT_PATHS = {
    "src/backends/cpp/emitter/cpp_emitter.py",
    "src/backends/cpp/emitter/stmt.py",
}

CPP_OBJECT_BRIDGE_ONLY_PATHS = {
    "src/backends/cpp/emitter/call.py",
}

EXPECTED_BUCKETS = {
    "cpp_emitter_object_bridge_residual": {
        ("py_runtime_object_type_id", "src/backends/cpp/emitter/cpp_emitter.py"),
        ("py_runtime_object_isinstance", "src/backends/cpp/emitter/runtime_expr.py"),
        ("py_runtime_object_isinstance", "src/backends/cpp/emitter/stmt.py"),
        ("py_append", "src/backends/cpp/emitter/call.py"),
        ("py_extend", "src/backends/cpp/emitter/call.py"),
        ("py_pop", "src/backends/cpp/emitter/call.py"),
        ("py_clear", "src/backends/cpp/emitter/call.py"),
        ("py_reverse", "src/backends/cpp/emitter/call.py"),
        ("py_sort", "src/backends/cpp/emitter/call.py"),
        ("py_set_at", "src/backends/cpp/emitter/call.py"),
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
        ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
    },
}

TARGET_END_STATE = {
    "cpp_emitter_object_bridge_residual": "object_bridge_only_no_typed_lane_reentry",
    "cpp_emitter_shared_type_id_residual": "thin_shared_type_id_only_last_intentional_cpp_contract",
    "rs_emitter_shared_type_id_residual": "thin_shared_type_id_only_no_generic_alias_reentry",
    "cs_emitter_shared_type_id_residual": "thin_shared_type_id_only_no_generic_alias_reentry",
    "crossruntime_mutation_helper_residual": "cs_bytes_bytearray_only",
}

REDUCTION_ORDER = [
    "crossruntime_mutation_helper_residual",
    "cpp_emitter_object_bridge_residual",
    "rs_emitter_shared_type_id_residual",
    "cs_emitter_shared_type_id_residual",
    "cpp_emitter_shared_type_id_residual",
]


def _iter_target_files() -> list[Path]:
    return [ROOT / rel for rel in sorted(TRACKED_PATHS)]


def _collect_symbol_pairs(
    symbols: set[str],
    paths: set[str],
) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    patterns = {
        symbol: re.compile(rf"\b{re.escape(symbol)}\b")
        for symbol in sorted(symbols)
    }
    for rel in sorted(paths):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore")
        for symbol, pattern in patterns.items():
            if pattern.search(text) is not None:
                out.add((symbol, rel))
    return out


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


def _collect_cpp_typed_lane_direct_pairs() -> set[tuple[str, str]]:
    return _collect_symbol_pairs(CPP_TYPED_LANE_DIRECT_MUTATION_SYMBOLS, CPP_TYPED_LANE_DIRECT_PATHS)


def _collect_cpp_object_bridge_wrapper_pairs() -> set[tuple[str, str]]:
    return _collect_symbol_pairs(CPP_OBJECT_BRIDGE_WRAPPER_SYMBOLS, CPP_OBJECT_BRIDGE_ONLY_PATHS)


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


def _collect_cpp_typed_wrapper_reentry_issues() -> list[str]:
    issues: list[str] = []
    for rel in sorted(CPP_TYPED_WRAPPER_FORBIDDEN_PATHS):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore")
        for symbol in sorted(CPP_TYPED_WRAPPER_SYMBOLS):
            if SYMBOL_PATTERNS[symbol].search(text) is not None:
                issues.append(
                    f"cpp typed-lane wrapper reentry: {symbol} must not appear in {rel}"
                )
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_cpp_typed_wrapper_reentry_issues())
    if set(TARGET_END_STATE.keys()) != set(EXPECTED_BUCKETS.keys()):
        issues.append("target end state keys do not match expected buckets")
    if list(dict.fromkeys(REDUCTION_ORDER)) != REDUCTION_ORDER:
        issues.append("reduction order contains duplicate bucket names")
    if set(REDUCTION_ORDER) != set(EXPECTED_BUCKETS.keys()):
        issues.append("reduction order does not cover the same buckets as the inventory")
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

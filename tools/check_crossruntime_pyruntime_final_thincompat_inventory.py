#!/usr/bin/env python3
"""Guard residual final thin-compat helpers before removing them from py_runtime.h."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TRACKED_PATHS = {
    "src/runtime/cpp/native/core/py_runtime.h",
    "src/runtime/cpp/generated/std/json.cpp",
    "src/runtime/rs/pytra/built_in/py_runtime.rs",
    "src/runtime/rs/native/built_in/py_runtime.rs",
    "src/runtime/cs/pytra/built_in/py_runtime.cs",
    "src/runtime/cs/native/built_in/py_runtime.cs",
}

CPP_HEADER_RULES = {
    ("py_runtime_type_id", "src/runtime/cpp/native/core/py_runtime.h"): re.compile(
        r"template <class T>\s*static inline uint32 py_runtime_type_id\s*\("
    ),
    ("py_isinstance", "src/runtime/cpp/native/core/py_runtime.h"): re.compile(
        r"template <class T>\s*static inline bool py_isinstance\s*\("
    ),
}

CPP_GENERATED_RULES = {
}

RS_ALIAS_RULES = {
    ("py_runtime_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(
        r"(?:pub\s+)?fn py_runtime_type_id<"
    ),
    ("py_runtime_type_id", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(
        r"(?:pub\s+)?fn py_runtime_type_id<"
    ),
    ("py_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_is_subtype\("),
    ("py_is_subtype", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_is_subtype\("),
    ("py_issubclass", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_issubclass\("),
    ("py_issubclass", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_issubclass\("),
    ("py_isinstance", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_isinstance<"),
    ("py_isinstance", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"(?:pub\s+)?fn py_isinstance<"),
}

CS_ALIAS_RULES = {
    ("py_runtime_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static long py_runtime_type_id\("
    ),
    ("py_runtime_type_id", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static long py_runtime_type_id\("
    ),
    ("py_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_is_subtype\("
    ),
    ("py_is_subtype", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_is_subtype\("
    ),
    ("py_issubclass", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_issubclass\("
    ),
    ("py_issubclass", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_issubclass\("
    ),
    ("py_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_isinstance\("
    ),
    ("py_isinstance", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(
        r"(?:public|private|internal) static bool py_isinstance\("
    ),
}

RS_PUBLIC_ALIAS_RULES = {
    ("py_runtime_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"pub fn py_runtime_type_id<"),
    ("py_runtime_type_id", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"pub fn py_runtime_type_id<"),
    ("py_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"pub fn py_is_subtype\("),
    ("py_is_subtype", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"pub fn py_is_subtype\("),
    ("py_issubclass", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"pub fn py_issubclass\("),
    ("py_issubclass", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"pub fn py_issubclass\("),
    ("py_isinstance", "src/runtime/rs/pytra/built_in/py_runtime.rs"): re.compile(r"pub fn py_isinstance<"),
    ("py_isinstance", "src/runtime/rs/native/built_in/py_runtime.rs"): re.compile(r"pub fn py_isinstance<"),
}

CS_PUBLIC_ALIAS_RULES = {
    ("py_runtime_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(r"public static long py_runtime_type_id\("),
    ("py_runtime_type_id", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(r"public static long py_runtime_type_id\("),
    ("py_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(r"public static bool py_is_subtype\("),
    ("py_is_subtype", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(r"public static bool py_is_subtype\("),
    ("py_issubclass", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(r"public static bool py_issubclass\("),
    ("py_issubclass", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(r"public static bool py_issubclass\("),
    ("py_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"): re.compile(r"public static bool py_isinstance\("),
    ("py_isinstance", "src/runtime/cs/native/built_in/py_runtime.cs"): re.compile(r"public static bool py_isinstance\("),
}

EXPECTED_BUCKETS = {
    "cpp_header_final_thincompat_defs": {
        ("py_runtime_type_id", "src/runtime/cpp/native/core/py_runtime.h"),
        ("py_isinstance", "src/runtime/cpp/native/core/py_runtime.h"),
    },
    "cpp_generated_final_thincompat_blocker": set(),
    "rs_runtime_generic_alias_surface": {
        ("py_runtime_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_type_id", "src/runtime/rs/native/built_in/py_runtime.rs"),
        ("py_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_is_subtype", "src/runtime/rs/native/built_in/py_runtime.rs"),
        ("py_issubclass", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_issubclass", "src/runtime/rs/native/built_in/py_runtime.rs"),
        ("py_isinstance", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_isinstance", "src/runtime/rs/native/built_in/py_runtime.rs"),
    },
    "cs_runtime_generic_alias_surface": {
        ("py_runtime_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_runtime_type_id", "src/runtime/cs/native/built_in/py_runtime.cs"),
        ("py_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_is_subtype", "src/runtime/cs/native/built_in/py_runtime.cs"),
        ("py_issubclass", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_issubclass", "src/runtime/cs/native/built_in/py_runtime.cs"),
        ("py_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_isinstance", "src/runtime/cs/native/built_in/py_runtime.cs"),
    },
}

TARGET_END_STATE = {
    "cpp_generated_final_thincompat_blocker": "empty_before_header_removal",
    "rs_runtime_generic_alias_surface": "internal_or_private_only_before_header_removal",
    "cs_runtime_generic_alias_surface": "internal_or_private_only_before_header_removal",
    "cpp_header_final_thincompat_defs": "remove_last_after_crossruntime_alignment",
}

REMOVAL_BUNDLE_ORDER = (
    "cpp_generated_final_thincompat_blocker",
    "rs_runtime_generic_alias_surface",
    "cs_runtime_generic_alias_surface",
    "cpp_header_final_thincompat_defs",
)


def _iter_target_files() -> list[Path]:
    return [ROOT / rel for rel in sorted(TRACKED_PATHS)]


def _collect_observed_pairs() -> set[tuple[str, str]]:
    observed: set[tuple[str, str]] = set()
    for path in _iter_target_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for rules in (CPP_HEADER_RULES, CPP_GENERATED_RULES, RS_ALIAS_RULES, CS_ALIAS_RULES):
            for (symbol, rule_path), pattern in rules.items():
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


def _collect_bundle_order_issues() -> list[str]:
    issues: list[str] = []
    known = set(EXPECTED_BUCKETS)
    if tuple(REMOVAL_BUNDLE_ORDER) != tuple(dict.fromkeys(REMOVAL_BUNDLE_ORDER)):
        issues.append("removal bundle order contains duplicates")
    for bucket in sorted(known - set(REMOVAL_BUNDLE_ORDER)):
        issues.append(f"removal bundle order missing bucket: {bucket}")
    for bucket in sorted(set(REMOVAL_BUNDLE_ORDER) - known):
        issues.append(f"removal bundle order references unknown bucket: {bucket}")
    if REMOVAL_BUNDLE_ORDER[-1] != "cpp_header_final_thincompat_defs":
        issues.append("cpp_header_final_thincompat_defs must remain the last removal bundle")
    if REMOVAL_BUNDLE_ORDER.index("cpp_generated_final_thincompat_blocker") > REMOVAL_BUNDLE_ORDER.index(
        "cpp_header_final_thincompat_defs"
    ):
        issues.append("cpp generated blockers must be removed before header thincompat defs")
    return issues


def _collect_target_end_state_issues() -> list[str]:
    issues: list[str] = []
    known = set(EXPECTED_BUCKETS)
    for bucket in sorted(known - set(TARGET_END_STATE)):
        issues.append(f"target end state missing bucket: {bucket}")
    for bucket in sorted(set(TARGET_END_STATE) - known):
        issues.append(f"target end state references unknown bucket: {bucket}")
    visibility_rule_groups = {
        "rs_runtime_generic_alias_surface": RS_PUBLIC_ALIAS_RULES,
        "cs_runtime_generic_alias_surface": CS_PUBLIC_ALIAS_RULES,
    }
    for bucket, rules in visibility_rule_groups.items():
        if TARGET_END_STATE.get(bucket) != "internal_or_private_only_before_header_removal":
            continue
        for path in _iter_target_files():
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
            for (symbol, rule_path), pattern in rules.items():
                if rel == rule_path and pattern.search(text) is not None:
                    issues.append(f"public alias must be removed from {bucket}: {symbol} @ {rel}")
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_bundle_order_issues())
    issues.extend(_collect_target_end_state_issues())
    expected = _collect_expected_pairs()
    for symbol, rel in sorted(observed - expected):
        issues.append(f"unclassified final thincompat residual: {symbol} @ {rel}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    if not issues:
        print("[OK] crossruntime py_runtime final thincompat inventory is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Guard non-emitter residual py_runtime callers before the next header shrink."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PATH_SYMBOLS = {
    "src/runtime/cpp/native/compiler/transpile_cli.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/native/compiler/backend_registry_static.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/generated/std/json.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/generated/built_in/type_id.cpp": {
        "py_runtime_object_type_id",
    },
    "src/runtime/cpp/generated/built_in/iter_ops.cpp": {
        "py_append",
    },
    "src/runtime/rs/pytra/built_in/py_runtime.rs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/rs/pytra-core/built_in/py_runtime.rs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/cs/pytra/built_in/py_runtime.cs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/cs/pytra-core/built_in/py_runtime.cs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/cs/pytra/utils/png.cs": {
        "py_append",
    },
    "src/runtime/cs/pytra/utils/gif.cs": {
        "py_append",
    },
}

SYMBOL_PATTERNS = {
    symbol: re.compile(rf"\b{re.escape(symbol)}\b")
    for symbol in sorted({symbol for symbols in PATH_SYMBOLS.values() for symbol in symbols})
}

EXPECTED_BUCKETS = {
    "native_wrapper_object_bridge_residual": {
        ("py_runtime_object_isinstance", "src/runtime/cpp/native/compiler/transpile_cli.cpp"),
        ("py_runtime_object_isinstance", "src/runtime/cpp/native/compiler/backend_registry_static.cpp"),
    },
    "generated_cpp_object_bridge_residual": {
        ("py_runtime_object_isinstance", "src/runtime/cpp/generated/std/json.cpp"),
        ("py_append", "src/runtime/cpp/generated/built_in/iter_ops.cpp"),
    },
    "generated_cpp_shared_type_id_residual": {
        ("py_runtime_object_type_id", "src/runtime/cpp/generated/built_in/type_id.cpp"),
    },
    "cs_runtime_utils_object_bridge_residual": {
        ("py_append", "src/runtime/cs/pytra/utils/png.cs"),
        ("py_append", "src/runtime/cs/pytra/utils/gif.cs"),
    },
    "rs_runtime_builtin_shared_type_id_residual": {
        ("py_runtime_type_id_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_type_id_issubclass", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_value_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_value_isinstance", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
        ("py_runtime_type_id_is_subtype", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
        ("py_runtime_type_id_issubclass", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
        ("py_runtime_value_type_id", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
        ("py_runtime_value_isinstance", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
    },
    "cs_runtime_builtin_shared_type_id_residual": {
        ("py_runtime_type_id_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_runtime_type_id_issubclass", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_runtime_value_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_runtime_value_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
        ("py_runtime_type_id_is_subtype", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_runtime_type_id_issubclass", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_runtime_value_type_id", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
        ("py_runtime_value_isinstance", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
    },
}

CATEGORY_BUCKETS = {
    "object_bridge_compat": {
        "native_wrapper_object_bridge_residual",
        "generated_cpp_object_bridge_residual",
        "cs_runtime_utils_object_bridge_residual",
    },
    "shared_type_id_contract": {
        "generated_cpp_shared_type_id_residual",
        "rs_runtime_builtin_shared_type_id_residual",
        "cs_runtime_builtin_shared_type_id_residual",
    },
}

TARGET_END_STATE = {
    "native_wrapper_object_bridge_residual": "native_decode_helpers_only",
    "generated_cpp_object_bridge_residual": "generated_runtime_object_bridge_only_until_jsonvalue_rework",
    "generated_cpp_shared_type_id_residual": "generated_type_id_bridge_only",
    "cs_runtime_utils_object_bridge_residual": "runtime_utils_object_bridge_only_until_typed_bytes_lane",
    "rs_runtime_builtin_shared_type_id_residual": "runtime_builtin_thin_type_id_surface_only",
    "cs_runtime_builtin_shared_type_id_residual": "runtime_builtin_thin_type_id_surface_only",
}

SOURCE_GUARD_REQUIRED_SUBSTRINGS = {
    "src/runtime/cpp/native/compiler/transpile_cli.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/native/compiler/backend_registry_static.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/generated/std/json.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/generated/built_in/type_id.cpp": {
        "py_runtime_object_type_id",
    },
    "src/runtime/cpp/generated/built_in/iter_ops.cpp": {
        "py_append(out, make_object(",
    },
    "src/runtime/rs/pytra/built_in/py_runtime.rs": {
        "pub fn py_runtime_value_type_id",
        "pub fn py_runtime_type_id_is_subtype",
        "pub fn py_runtime_type_id_issubclass",
        "pub fn py_runtime_value_isinstance",
    },
    "src/runtime/rs/pytra-core/built_in/py_runtime.rs": {
        "pub fn py_runtime_value_type_id",
        "pub fn py_runtime_type_id_is_subtype",
        "pub fn py_runtime_type_id_issubclass",
        "pub fn py_runtime_value_isinstance",
    },
    "src/runtime/cs/pytra/built_in/py_runtime.cs": {
        "public static long py_runtime_value_type_id",
        "public static bool py_runtime_type_id_is_subtype",
        "public static bool py_runtime_type_id_issubclass",
        "public static bool py_runtime_value_isinstance",
    },
    "src/runtime/cs/pytra-core/built_in/py_runtime.cs": {
        "public static long py_runtime_value_type_id",
        "public static bool py_runtime_type_id_is_subtype",
        "public static bool py_runtime_type_id_issubclass",
        "public static bool py_runtime_value_isinstance",
    },
}

SOURCE_GUARD_FORBIDDEN_SUBSTRINGS = {
    "src/runtime/cpp/native/compiler/transpile_cli.cpp": {
        "py_runtime_type_id(",
        "py_isinstance(",
    },
    "src/runtime/cpp/native/compiler/backend_registry_static.cpp": {
        "py_runtime_type_id(",
        "py_isinstance(",
    },
    "src/runtime/rs/pytra/built_in/py_runtime.rs": {
        "pub fn py_runtime_type_id<",
        "pub fn py_isinstance<",
        "pub fn py_is_subtype(",
        "pub fn py_issubclass(",
    },
    "src/runtime/rs/pytra-core/built_in/py_runtime.rs": {
        "pub fn py_runtime_type_id<",
        "pub fn py_isinstance<",
        "pub fn py_is_subtype(",
        "pub fn py_issubclass(",
    },
    "src/runtime/cs/pytra/built_in/py_runtime.cs": {
        "public static long py_runtime_type_id(",
        "public static bool py_isinstance(",
        "public static bool py_is_subtype(",
        "public static bool py_issubclass(",
    },
    "src/runtime/cs/pytra-core/built_in/py_runtime.cs": {
        "public static long py_runtime_type_id(",
        "public static bool py_isinstance(",
        "public static bool py_is_subtype(",
        "public static bool py_issubclass(",
    },
}

GENERATED_CPP_MUST_REMAIN = {
    ("py_runtime_object_isinstance", "src/runtime/cpp/generated/std/json.cpp"),
    ("py_append", "src/runtime/cpp/generated/built_in/iter_ops.cpp"),
    ("py_runtime_object_type_id", "src/runtime/cpp/generated/built_in/type_id.cpp"),
}

GENERATED_CPP_REDELEGATABLE = set()

RS_RUNTIME_BUILTIN_MUST_REMAIN = {
    ("py_runtime_type_id_is_subtype", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
    ("py_runtime_type_id_issubclass", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
    ("py_runtime_value_type_id", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
    ("py_runtime_value_isinstance", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
    ("py_runtime_type_id_is_subtype", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
    ("py_runtime_type_id_issubclass", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
    ("py_runtime_value_type_id", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
    ("py_runtime_value_isinstance", "src/runtime/rs/pytra-core/built_in/py_runtime.rs"),
}

RS_RUNTIME_BUILTIN_REDELEGATABLE = set()

CS_RUNTIME_BUILTIN_MUST_REMAIN = {
    ("py_runtime_type_id_is_subtype", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
    ("py_runtime_type_id_issubclass", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
    ("py_runtime_value_type_id", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
    ("py_runtime_value_isinstance", "src/runtime/cs/pytra/built_in/py_runtime.cs"),
    ("py_runtime_type_id_is_subtype", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
    ("py_runtime_type_id_issubclass", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
    ("py_runtime_value_type_id", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
    ("py_runtime_value_isinstance", "src/runtime/cs/pytra-core/built_in/py_runtime.cs"),
}

CS_RUNTIME_BUILTIN_REDELEGATABLE = set()


def _iter_target_files() -> list[Path]:
    return [ROOT / rel for rel in sorted(PATH_SYMBOLS)]


def _collect_observed_pairs() -> set[tuple[str, str]]:
    observed: set[tuple[str, str]] = set()
    for path in _iter_target_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for symbol in sorted(PATH_SYMBOLS[rel]):
            pattern = SYMBOL_PATTERNS[symbol]
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
            for pair in sorted(overlap):
                issues.append(
                    f"bucket overlap: {left_name} and {right_name} both include {pair}"
                )
    return issues


def _collect_category_issues() -> list[str]:
    issues: list[str] = []
    bucket_names = set(EXPECTED_BUCKETS.keys())
    category_union = set().union(*CATEGORY_BUCKETS.values())
    if category_union != bucket_names:
        issues.append("category buckets do not cover the same bucket names as EXPECTED_BUCKETS")
    overlap = CATEGORY_BUCKETS["object_bridge_compat"] & CATEGORY_BUCKETS["shared_type_id_contract"]
    if overlap:
        issues.append(f"category buckets overlap: {sorted(overlap)}")
    return issues


def _collect_generated_cpp_policy_issues() -> list[str]:
    issues: list[str] = []
    generated_pairs = (
        EXPECTED_BUCKETS["generated_cpp_object_bridge_residual"]
        | EXPECTED_BUCKETS["generated_cpp_shared_type_id_residual"]
    )
    if GENERATED_CPP_MUST_REMAIN | GENERATED_CPP_REDELEGATABLE != generated_pairs:
        issues.append("generated cpp policy buckets do not cover the same pairs as generated cpp residual buckets")
    overlap = GENERATED_CPP_MUST_REMAIN & GENERATED_CPP_REDELEGATABLE
    if overlap:
        issues.append(f"generated cpp policy buckets overlap: {sorted(overlap)}")
    return issues


def _collect_runtime_builtin_policy_issues() -> list[str]:
    issues: list[str] = []
    rs_pairs = EXPECTED_BUCKETS["rs_runtime_builtin_shared_type_id_residual"]
    cs_pairs = EXPECTED_BUCKETS["cs_runtime_builtin_shared_type_id_residual"]
    if RS_RUNTIME_BUILTIN_MUST_REMAIN | RS_RUNTIME_BUILTIN_REDELEGATABLE != rs_pairs:
        issues.append("rs runtime builtin policy buckets do not cover the same pairs as rs runtime builtin residual bucket")
    if CS_RUNTIME_BUILTIN_MUST_REMAIN | CS_RUNTIME_BUILTIN_REDELEGATABLE != cs_pairs:
        issues.append("cs runtime builtin policy buckets do not cover the same pairs as cs runtime builtin residual bucket")
    rs_overlap = RS_RUNTIME_BUILTIN_MUST_REMAIN & RS_RUNTIME_BUILTIN_REDELEGATABLE
    if rs_overlap:
        issues.append(f"rs runtime builtin policy buckets overlap: {sorted(rs_overlap)}")
    cs_overlap = CS_RUNTIME_BUILTIN_MUST_REMAIN & CS_RUNTIME_BUILTIN_REDELEGATABLE
    if cs_overlap:
        issues.append(f"cs runtime builtin policy buckets overlap: {sorted(cs_overlap)}")
    return issues


def _collect_source_guard_issues() -> list[str]:
    issues: list[str] = []
    for rel, required in sorted(SOURCE_GUARD_REQUIRED_SUBSTRINGS.items()):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        for snippet in sorted(required):
            if snippet not in text:
                issues.append(f"source guard missing required snippet in {rel}: {snippet}")
    for rel, forbidden in sorted(SOURCE_GUARD_FORBIDDEN_SUBSTRINGS.items()):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        for snippet in sorted(forbidden):
            if snippet in text:
                issues.append(f"source guard found forbidden snippet in {rel}: {snippet}")
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_category_issues())
    issues.extend(_collect_generated_cpp_policy_issues())
    issues.extend(_collect_runtime_builtin_policy_issues())
    for pair in sorted(expected - observed):
        issues.append(f"expected residual pair missing: {pair}")
    for pair in sorted(observed - expected):
        issues.append(f"unexpected residual pair present: {pair}")
    issues.extend(_collect_source_guard_issues())
    return issues


def main() -> int:
    issues = _collect_inventory_issues()
    if not issues:
        print("[OK] crossruntime py_runtime residual caller inventory is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

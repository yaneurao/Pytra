#!/usr/bin/env python3
"""Guard non-emitter residual py_runtime callers before the next header shrink."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PATH_SYMBOLS = {
    "src/runtime/cpp/compiler/transpile_cli.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/compiler/backend_registry_static.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/generated/std/json.cpp": {
        "py_runtime_value_isinstance",
    },
    "src/runtime/generated/built_in/type_id.cpp": {
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/rs/built_in/py_runtime.rs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/cs/built_in/py_runtime.cs": {
        "py_runtime_type_id_is_subtype",
        "py_runtime_type_id_issubclass",
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
}

SYMBOL_PATTERNS = {
    symbol: re.compile(rf"\b{re.escape(symbol)}\b")
    for symbol in sorted({symbol for symbols in PATH_SYMBOLS.values() for symbol in symbols})
}

EXPECTED_BUCKETS = {
    "native_wrapper_object_bridge_residual": {
        ("py_runtime_object_isinstance", "src/runtime/cpp/compiler/transpile_cli.cpp"),
        ("py_runtime_object_isinstance", "src/runtime/cpp/compiler/backend_registry_static.cpp"),
    },
    "generated_cpp_shared_type_id_residual": {
        ("py_runtime_value_isinstance", "src/runtime/generated/std/json.cpp"),
        ("py_runtime_value_type_id", "src/runtime/generated/built_in/type_id.cpp"),
        ("py_runtime_value_isinstance", "src/runtime/generated/built_in/type_id.cpp"),
    },
    "rs_runtime_builtin_shared_type_id_residual": {
        ("py_runtime_type_id_is_subtype", "src/runtime/rs/built_in/py_runtime.rs"),
        ("py_runtime_type_id_issubclass", "src/runtime/rs/built_in/py_runtime.rs"),
        ("py_runtime_value_type_id", "src/runtime/rs/built_in/py_runtime.rs"),
        ("py_runtime_value_isinstance", "src/runtime/rs/built_in/py_runtime.rs"),
    },
    "cs_runtime_builtin_shared_type_id_residual": {
        ("py_runtime_type_id_is_subtype", "src/runtime/cs/built_in/py_runtime.cs"),
        ("py_runtime_type_id_issubclass", "src/runtime/cs/built_in/py_runtime.cs"),
        ("py_runtime_value_type_id", "src/runtime/cs/built_in/py_runtime.cs"),
        ("py_runtime_value_isinstance", "src/runtime/cs/built_in/py_runtime.cs"),
    },
}

CATEGORY_BUCKETS = {
    "object_bridge_compat": {
        "native_wrapper_object_bridge_residual",
    },
    "shared_type_id_contract": {
        "generated_cpp_shared_type_id_residual",
        "rs_runtime_builtin_shared_type_id_residual",
        "cs_runtime_builtin_shared_type_id_residual",
    },
}

TARGET_END_STATE = {
    "native_wrapper_object_bridge_residual": "native_decode_helpers_only",
    "generated_cpp_shared_type_id_residual": "generated_value_thin_type_id_bridge_only",
    "rs_runtime_builtin_shared_type_id_residual": "runtime_builtin_thin_type_id_surface_only",
    "cs_runtime_builtin_shared_type_id_residual": "runtime_builtin_thin_type_id_surface_only",
}

SOURCE_GUARD_REQUIRED_SUBSTRINGS = {
    "src/runtime/cpp/compiler/transpile_cli.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/cpp/compiler/backend_registry_static.cpp": {
        "py_runtime_object_isinstance",
    },
    "src/runtime/generated/std/json.cpp": {
        "py_runtime_value_isinstance",
    },
    "src/runtime/generated/built_in/type_id.cpp": {
        "py_runtime_value_type_id",
        "py_runtime_value_isinstance",
    },
    "src/runtime/rs/built_in/py_runtime.rs": {
        "pub fn py_runtime_value_type_id",
        "pub fn py_runtime_type_id_is_subtype",
        "pub fn py_runtime_type_id_issubclass",
        "pub fn py_runtime_value_isinstance",
    },
    "src/runtime/cs/built_in/py_runtime.cs": {
        "public static long py_runtime_value_type_id",
        "public static bool py_runtime_type_id_is_subtype",
        "public static bool py_runtime_type_id_issubclass",
        "public static bool py_runtime_value_isinstance",
    },
}

SOURCE_GUARD_FORBIDDEN_SUBSTRINGS = {
    "src/runtime/cpp/compiler/transpile_cli.cpp": {
        "py_runtime_type_id(",
        "py_isinstance(",
    },
    "src/runtime/cpp/compiler/backend_registry_static.cpp": {
        "py_runtime_type_id(",
        "py_isinstance(",
    },
    "src/runtime/generated/std/json.cpp": {
        "py_runtime_object_isinstance(",
    },
    "src/runtime/generated/built_in/type_id.cpp": {
        "py_runtime_object_type_id(",
        "py_runtime_object_isinstance(",
    },
    "src/runtime/rs/built_in/py_runtime.rs": {
        "pub fn py_runtime_type_id<",
        "pub fn py_isinstance<",
        "pub fn py_is_subtype(",
        "pub fn py_issubclass(",
    },
    "src/runtime/cs/built_in/py_runtime.cs": {
        "public static long py_runtime_type_id(",
        "public static bool py_isinstance(",
        "public static bool py_is_subtype(",
        "public static bool py_issubclass(",
    },
}

SMOKE_LANE_REQUIRED_SUBSTRINGS = {
    "test/unit/common/test_py2x_entrypoints_contract.py": {
        'native_transpile.count("py_runtime_object_isinstance("), 1',
        'native_registry.count("py_runtime_object_isinstance("), 1',
    },
    "test/unit/toolchain/emit/cpp/test_cpp_runtime_iterable.py": {
        "def test_runtime_iterable_protocol_helpers(self) -> None:",
    },
    "test/unit/toolchain/emit/cpp/test_cpp_runtime_type_id.py": {
        "def test_runtime_type_id_subtype_and_isinstance_contract(self) -> None:",
    },
    "test/unit/toolchain/emit/rs/test_py2rs_smoke.py": {
        "def test_type_predicate_nodes_are_lowered_without_legacy_bridge(self) -> None:",
    },
    "test/unit/toolchain/emit/cs/test_py2cs_smoke.py": {
        "def test_runtime_import_resolution_uses_canonical_runtime_helpers(self) -> None:",
        "def test_type_predicate_nodes_are_lowered_without_legacy_bridge(self) -> None:",
        "def test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not(self) -> None:",
        "def test_bytearray_index_and_slice_compat_helpers_stay_explicit(self) -> None:",
    },
}

GENERATED_CPP_MUST_REMAIN = {
    ("py_runtime_value_isinstance", "src/runtime/generated/std/json.cpp"),
    ("py_runtime_value_type_id", "src/runtime/generated/built_in/type_id.cpp"),
    ("py_runtime_value_isinstance", "src/runtime/generated/built_in/type_id.cpp"),
}

GENERATED_CPP_REDELEGATABLE = set()

REPRESENTATIVE_BUCKET_MANIFEST = {
    "native_wrapper_object_bridge_residual": {
        "smoke_file": "test/unit/common/test_py2x_entrypoints_contract.py",
        "smoke_tests": {
            "test_native_cpp_typed_boundary_make_object_usage_stays_on_export_seams",
        },
        "source_guard_paths": {
            "src/runtime/cpp/compiler/transpile_cli.cpp",
            "src/runtime/cpp/compiler/backend_registry_static.cpp",
        },
    },
    "generated_cpp_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/cpp/test_cpp_runtime_iterable.py",
        "smoke_tests": {
            "test_runtime_list_overload_inventory",
        },
        "source_guard_paths": {
            "src/runtime/generated/std/json.cpp",
            "src/runtime/generated/built_in/type_id.cpp",
        },
    },
    "rs_runtime_builtin_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
                "source_guard_paths": {
                        "src/runtime/rs/built_in/py_runtime.rs",
                    },
                },
    "cs_runtime_builtin_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
        "source_guard_paths": {
            "src/runtime/cs/built_in/py_runtime.cs",
        },
    },
}

RS_RUNTIME_BUILTIN_MUST_REMAIN = {
    ("py_runtime_type_id_is_subtype", "src/runtime/rs/built_in/py_runtime.rs"),
    ("py_runtime_type_id_issubclass", "src/runtime/rs/built_in/py_runtime.rs"),
    ("py_runtime_value_type_id", "src/runtime/rs/built_in/py_runtime.rs"),
    ("py_runtime_value_isinstance", "src/runtime/rs/built_in/py_runtime.rs"),
}

RS_RUNTIME_BUILTIN_REDELEGATABLE = set()

CS_RUNTIME_BUILTIN_MUST_REMAIN = {
    ("py_runtime_type_id_is_subtype", "src/runtime/cs/built_in/py_runtime.cs"),
    ("py_runtime_type_id_issubclass", "src/runtime/cs/built_in/py_runtime.cs"),
    ("py_runtime_value_type_id", "src/runtime/cs/built_in/py_runtime.cs"),
    ("py_runtime_value_isinstance", "src/runtime/cs/built_in/py_runtime.cs"),
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
    generated_pairs = EXPECTED_BUCKETS["generated_cpp_shared_type_id_residual"]
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


def _collect_representative_bucket_issues() -> list[str]:
    issues: list[str] = []
    manifest_keys = set(REPRESENTATIVE_BUCKET_MANIFEST.keys())
    if manifest_keys != set(EXPECTED_BUCKETS.keys()):
        issues.append("representative residual bucket manifest keys do not match expected buckets")
        return issues
    for bucket_name in sorted(REPRESENTATIVE_BUCKET_MANIFEST.keys()):
        lane = REPRESENTATIVE_BUCKET_MANIFEST[bucket_name]
        smoke_file = lane["smoke_file"]
        smoke_tests = set(lane["smoke_tests"])
        source_guard_paths = set(lane["source_guard_paths"])
        smoke_text = (ROOT / smoke_file).read_text(encoding="utf-8", errors="ignore")
        for test_name in sorted(smoke_tests):
            if f"def {test_name}(" not in smoke_text:
                issues.append(
                    f"representative smoke missing: {bucket_name}: {smoke_file}: {test_name}"
                )
        missing_paths = source_guard_paths - set(SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys())
        for rel in sorted(missing_paths):
            issues.append(
                f"representative source guard path missing from guard inventory: {bucket_name}: {rel}"
            )
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


def _collect_smoke_lane_issues() -> list[str]:
    issues: list[str] = []
    for rel, required in sorted(SMOKE_LANE_REQUIRED_SUBSTRINGS.items()):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        for snippet in sorted(required):
            if snippet not in text:
                issues.append(f"smoke lane missing required snippet in {rel}: {snippet}")
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_category_issues())
    issues.extend(_collect_generated_cpp_policy_issues())
    issues.extend(_collect_runtime_builtin_policy_issues())
    issues.extend(_collect_representative_bucket_issues())
    for pair in sorted(expected - observed):
        issues.append(f"expected residual pair missing: {pair}")
    for pair in sorted(observed - expected):
        issues.append(f"unexpected residual pair present: {pair}")
    issues.extend(_collect_source_guard_issues())
    issues.extend(_collect_smoke_lane_issues())
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

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
    "crossruntime_mutation_helper_residual": "cs_bytearray_only",
}

REDUCTION_ORDER = [
    "crossruntime_mutation_helper_residual",
    "cpp_emitter_object_bridge_residual",
    "rs_emitter_shared_type_id_residual",
    "cs_emitter_shared_type_id_residual",
    "cpp_emitter_shared_type_id_residual",
]

ACTIVE_REDUCTION_BUNDLES = {
    "crossruntime_mutation_helper_residual": {
        "stage": "S2-01",
        "goal": "minimize the C# bytearray must-remain seam",
        "status": "completed",
    },
    "cpp_emitter_object_bridge_residual": {
        "stage": "S2-02",
        "goal": "return removable callers to typed lanes and drop wrapper-name labels",
        "status": "active",
    },
    "rs_emitter_shared_type_id_residual": {
        "stage": "S3-01",
        "goal": "thin the Rust shared type-id seam",
        "status": "planned",
    },
    "cs_emitter_shared_type_id_residual": {
        "stage": "S3-01",
        "goal": "thin the C# shared type-id seam",
        "status": "planned",
    },
    "cpp_emitter_shared_type_id_residual": {
        "stage": "S3-02",
        "goal": "re-evaluate the final intentional C++ shared type-id contract",
        "status": "planned",
    },
}

SOURCE_GUARD_REQUIRED_SUBSTRINGS = {
    "src/backends/rs/emitter/rs_emitter.py": {
        'return "py_runtime_value_type_id(&" + value_expr + ")"',
        'return "({ py_register_generated_type_info(); py_runtime_value_isinstance(&" + value_expr + ", " + expected_type_id + ") })"',
        'return "({ py_register_generated_type_info(); py_runtime_type_id_is_subtype(" + actual_type_id + ", " + expected_type_id + ") })"',
        'return "({ py_register_generated_type_info(); py_runtime_type_id_issubclass(" + actual_type_id + ", " + expected_type_id + ") })"',
    },
    "src/backends/cs/emitter/cs_emitter.py": {
        'return "Pytra.CsModule.py_runtime.py_runtime_value_type_id(" + value_expr + ")"',
        'return "Pytra.CsModule.py_runtime.py_runtime_value_isinstance(" + value_expr + ", " + expected_type_id + ")"',
        'return "Pytra.CsModule.py_runtime.py_runtime_type_id_is_subtype(" + actual_type_id + ", " + expected_type_id + ")"',
        'return "Pytra.CsModule.py_runtime.py_runtime_type_id_issubclass(" + actual_type_id + ", " + expected_type_id + ")"',
        "def _render_bytes_mutation_call(",
        'if owner_type == "bytes" and attr_raw in {"append", "pop"}:',
        'raise RuntimeError("csharp emitter: bytes mutation helpers are unsupported; use bytearray")',
        'return "Pytra.CsModule.py_runtime.py_append(" + owner_expr + ", " + rendered_args[0] + ")"',
        'return "Pytra.CsModule.py_runtime.py_pop(" + owner_expr + ")"',
        'return "Pytra.CsModule.py_runtime.py_pop(" + owner_expr + ", " + rendered_args[0] + ")"',
        'return "Pytra.CsModule.py_runtime.py_slice(" + owner + ", " + lower_expr + ", " + upper_expr + ")"',
        'return "Pytra.CsModule.py_runtime.py_get(" + owner + ", " + idx + ")"',
        'self.emit("Pytra.CsModule.py_runtime.py_set(" + owner + ", " + idx + ", " + sub_value + ");")',
    },
}

SOURCE_GUARD_FORBIDDEN_SUBSTRINGS = {
    "src/backends/rs/emitter/rs_emitter.py": {
        "fn py_runtime_type_id(actual_type_id:",
        "fn py_is_subtype(",
        "fn py_issubclass(",
        "fn py_isinstance<",
    },
    "src/backends/cs/emitter/cs_emitter.py": {
        "Pytra.CsModule.py_runtime.py_runtime_type_id(",
        "Pytra.CsModule.py_runtime.py_is_subtype(",
        "Pytra.CsModule.py_runtime.py_issubclass(",
        "Pytra.CsModule.py_runtime.py_isinstance(",
    },
}

REPRESENTATIVE_LANE_MANIFEST = {
    "cpp_emitter_object_bridge_residual": {
        "smoke_file": "test/unit/backends/cpp/test_east3_cpp_bridge.py",
        "smoke_tests": {
            "test_render_expr_pyobj_runtime_list_append_uses_low_level_bridge",
            "test_emit_assign_pyobj_runtime_list_store_uses_low_level_bridge",
            "test_transpile_typed_list_append_stays_out_of_object_bridge",
            "test_transpile_typed_list_store_stays_out_of_object_bridge",
        },
        "source_guard_paths": set(),
    },
    "cpp_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/backends/cpp/test_east3_cpp_bridge.py",
        "smoke_tests": {
            "test_render_expr_supports_east3_obj_boundary_nodes",
        },
        "source_guard_paths": set(),
    },
    "rs_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/backends/rs/test_py2rs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
        "source_guard_paths": {"src/backends/rs/emitter/rs_emitter.py"},
    },
    "cs_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
        "source_guard_paths": {"src/backends/cs/emitter/cs_emitter.py"},
    },
    "crossruntime_mutation_helper_residual": {
        "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
        "smoke_tests": {
            "test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not",
            "test_bytearray_index_and_slice_compat_helpers_stay_explicit",
        },
        "source_guard_paths": {"src/backends/cs/emitter/cs_emitter.py"},
    },
}


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


def _collect_source_guard_issues() -> list[str]:
    issues: list[str] = []
    if set(SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys()) != set(SOURCE_GUARD_FORBIDDEN_SUBSTRINGS.keys()):
        issues.append("source guard path keys do not match between required and forbidden sets")
        return issues
    for rel in sorted(SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys()):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        for pattern in sorted(SOURCE_GUARD_REQUIRED_SUBSTRINGS[rel]):
            if pattern not in text:
                issues.append(f"source guard required pattern missing: {rel}: {pattern}")
        for pattern in sorted(SOURCE_GUARD_FORBIDDEN_SUBSTRINGS[rel]):
            if pattern in text:
                issues.append(f"source guard forbidden pattern re-entered: {rel}: {pattern}")
    return issues


def _collect_representative_lane_issues() -> list[str]:
    issues: list[str] = []
    if set(REPRESENTATIVE_LANE_MANIFEST.keys()) != set(EXPECTED_BUCKETS.keys()):
        issues.append("representative lane manifest keys do not match expected buckets")
        return issues
    for bucket_name in sorted(REPRESENTATIVE_LANE_MANIFEST.keys()):
        lane = REPRESENTATIVE_LANE_MANIFEST[bucket_name]
        smoke_file = lane["smoke_file"]
        smoke_tests = set(lane["smoke_tests"])
        source_guard_paths = set(lane["source_guard_paths"])
        smoke_text = (ROOT / smoke_file).read_text(encoding="utf-8", errors="ignore")
        for test_name in sorted(smoke_tests):
            if f"def {test_name}(" not in smoke_text:
                issues.append(
                    f"representative smoke missing: {bucket_name}: {smoke_file}: {test_name}"
                )
        for rel in sorted(source_guard_paths):
            if rel not in SOURCE_GUARD_REQUIRED_SUBSTRINGS:
                issues.append(
                    f"representative source guard path missing from guard inventory: {bucket_name}: {rel}"
                )
    return issues


def _collect_active_reduction_bundle_issues() -> list[str]:
    issues: list[str] = []
    if set(ACTIVE_REDUCTION_BUNDLES.keys()) != set(EXPECTED_BUCKETS.keys()):
        issues.append("active reduction bundle keys do not match expected buckets")
        return issues
    if list(ACTIVE_REDUCTION_BUNDLES.keys()) != REDUCTION_ORDER:
        issues.append("active reduction bundle order does not match reduction order")
    for bucket_name, payload in ACTIVE_REDUCTION_BUNDLES.items():
        stage = str(payload.get("stage", ""))
        goal = str(payload.get("goal", ""))
        status = str(payload.get("status", ""))
        if not stage.startswith("S"):
            issues.append(f"active reduction bundle stage is malformed: {bucket_name}: {stage}")
        if goal.strip() == "":
            issues.append(f"active reduction bundle goal is empty: {bucket_name}")
        if status not in {"planned", "active", "completed"}:
            issues.append(
                f"active reduction bundle status is invalid: {bucket_name}: {status}"
            )
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_cpp_typed_wrapper_reentry_issues())
    issues.extend(_collect_source_guard_issues())
    issues.extend(_collect_representative_lane_issues())
    issues.extend(_collect_active_reduction_bundle_issues())
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

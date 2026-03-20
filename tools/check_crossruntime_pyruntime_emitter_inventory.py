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
    "src/toolchain/emit/cpp/emitter/call.py",
    "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
    "src/toolchain/emit/cpp/emitter/runtime_expr.py",
    "src/toolchain/emit/cpp/emitter/stmt.py",
    "src/toolchain/emit/rs/emitter/rs_emitter.py",
    "src/toolchain/emit/cs/emitter/cs_emitter.py",
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
    "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
    "src/toolchain/emit/cpp/emitter/runtime_expr.py",
    "src/toolchain/emit/cpp/emitter/stmt.py",
}

CPP_TYPED_LANE_DIRECT_PATHS = {
    "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
    "src/toolchain/emit/cpp/emitter/stmt.py",
}

CPP_OBJECT_BRIDGE_ONLY_PATHS = {
    "src/toolchain/emit/cpp/emitter/call.py",
}

EXPECTED_BUCKETS = {
    "cpp_emitter_object_bridge_residual": set(),
    "cpp_emitter_shared_type_id_residual": {
        ("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py"),
        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
        ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
    },
    "rs_emitter_shared_type_id_residual": {
        ("py_runtime_value_type_id", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
        ("py_runtime_value_isinstance", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
    },
    "cs_emitter_shared_type_id_residual": {
        ("py_runtime_value_type_id", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
        ("py_runtime_value_isinstance", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
        ("py_runtime_type_id_issubclass", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
    },
    "crossruntime_mutation_helper_residual": {
        ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
        ("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
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
        "goal": "return removable callers to typed lanes and leave no wrapper-name residuals",
        "status": "completed",
    },
    "rs_emitter_shared_type_id_residual": {
        "stage": "S3-01",
        "goal": "thin the Rust shared type-id seam",
        "status": "completed",
    },
    "cs_emitter_shared_type_id_residual": {
        "stage": "S3-01",
        "goal": "thin the C# shared type-id seam",
        "status": "completed",
    },
    "cpp_emitter_shared_type_id_residual": {
        "stage": "S3-02",
        "goal": "re-evaluate the final intentional C++ shared type-id contract",
        "status": "completed",
    },
}

SOURCE_GUARD_REQUIRED_SUBSTRINGS = {
    "src/toolchain/emit/cpp/emitter/cpp_emitter.py": {
        'return f"py_runtime_value_type_id({value_expr})"',
    },
    "src/toolchain/emit/cpp/emitter/runtime_expr.py": {
        'return f"py_runtime_type_id_is_subtype({actual_type_id_expr}, {expected_type_id_expr})"',
        'return f"py_runtime_type_id_issubclass({actual_type_id_expr}, {expected_type_id_expr})"',
        'return f"py_runtime_value_isinstance({value_expr}, {expected_type_id_expr})"',
    },
    "src/toolchain/emit/cpp/emitter/stmt.py": {
        'cond_txt = f"py_runtime_value_isinstance({subject_tmp}, {variant_name}::PYTRA_TYPE_ID)"',
    },
    "src/toolchain/emit/rs/emitter/rs_emitter.py": {
        'return "py_runtime_value_type_id(&" + value_expr + ")"',
        'return "({ py_register_generated_type_info(); py_runtime_value_isinstance(&" + value_expr + ", " + expected_type_id + ") })"',
        'return "({ py_register_generated_type_info(); py_runtime_type_id_is_subtype(" + actual_type_id + ", " + expected_type_id + ") })"',
        'return "({ py_register_generated_type_info(); py_runtime_type_id_issubclass(" + actual_type_id + ", " + expected_type_id + ") })"',
    },
    "src/toolchain/emit/cs/emitter/cs_emitter.py": {
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
    "src/toolchain/emit/cpp/emitter/cpp_emitter.py": {
        "py_runtime_object_type_id(",
        "py_runtime_object_isinstance(",
        "py_runtime_type_id(",
    },
    "src/toolchain/emit/cpp/emitter/runtime_expr.py": {
        "py_runtime_object_type_id(",
        "py_runtime_object_isinstance(",
        "py_runtime_type_id(",
        "py_isinstance(",
        "py_is_subtype(",
        "py_issubclass(",
    },
    "src/toolchain/emit/cpp/emitter/stmt.py": {
        "py_runtime_object_isinstance(",
        "py_isinstance(",
    },
    "src/toolchain/emit/rs/emitter/rs_emitter.py": {
        "fn py_runtime_type_id(actual_type_id:",
        "fn py_is_subtype(",
        "fn py_issubclass(",
        "fn py_isinstance<",
    },
    "src/toolchain/emit/cs/emitter/cs_emitter.py": {
        "Pytra.CsModule.py_runtime.py_runtime_type_id(",
        "Pytra.CsModule.py_runtime.py_is_subtype(",
        "Pytra.CsModule.py_runtime.py_issubclass(",
        "Pytra.CsModule.py_runtime.py_isinstance(",
    },
}

REPRESENTATIVE_LANE_MANIFEST = {
    "cpp_emitter_object_bridge_residual": {
        "smoke_file": "test/unit/toolchain/emit/cpp/test_east3_cpp_bridge.py",
        "smoke_tests": {
            "test_render_expr_pyobj_runtime_list_append_uses_low_level_bridge",
            "test_emit_assign_pyobj_runtime_list_store_uses_low_level_bridge",
            "test_transpile_typed_list_append_stays_out_of_object_bridge",
            "test_transpile_typed_list_store_stays_out_of_object_bridge",
        },
        "source_guard_paths": set(),
    },
    "cpp_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/cpp/test_east3_cpp_bridge.py",
        "smoke_tests": {
            "test_render_expr_supports_east3_obj_boundary_nodes",
            "test_transpile_representative_nominal_adt_match_emits_if_else_chain",
        },
        "source_guard_paths": {
            "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
            "src/toolchain/emit/cpp/emitter/runtime_expr.py",
            "src/toolchain/emit/cpp/emitter/stmt.py",
        },
    },
    "rs_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
        "source_guard_paths": {"src/toolchain/emit/rs/emitter/rs_emitter.py"},
    },
    "cs_emitter_shared_type_id_residual": {
        "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        "smoke_tests": {
            "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
        },
        "source_guard_paths": {"src/toolchain/emit/cs/emitter/cs_emitter.py"},
    },
    "crossruntime_mutation_helper_residual": {
        "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        "smoke_tests": {
            "test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not",
            "test_bytearray_index_and_slice_compat_helpers_stay_explicit",
        },
        "source_guard_paths": {"src/toolchain/emit/cs/emitter/cs_emitter.py"},
    },
}

FUTURE_FOLLOWUP_TASK_ID = "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01"
FUTURE_FOLLOWUP_PLAN_PATH = "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md"

FUTURE_FOLLOWUP_BASELINE_BUCKETS = (
    "cpp_emitter_shared_type_id_residual",
    "rs_emitter_shared_type_id_residual",
    "cs_emitter_shared_type_id_residual",
    "crossruntime_mutation_helper_residual",
)

FUTURE_REDUCTION_ORDER = [
    "cpp_emitter_shared_type_id_residual",
    "rs_emitter_shared_type_id_residual",
    "cs_emitter_shared_type_id_residual",
    "crossruntime_mutation_helper_residual",
]

FUTURE_REPRESENTATIVE_LANE_MANIFEST = {
    bucket_name: REPRESENTATIVE_LANE_MANIFEST[bucket_name]
    for bucket_name in FUTURE_FOLLOWUP_BASELINE_BUCKETS
}

FUTURE_SOURCE_GUARD_PATHS = {
    path
    for lane in FUTURE_REPRESENTATIVE_LANE_MANIFEST.values()
    for path in lane["source_guard_paths"]
}

FUTURE_HANDOFF_TARGETS = {
    "cpp_header_shrink": {
        "plan_path": "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md",
        "trigger_bucket": "cpp_emitter_shared_type_id_residual",
        "handoff_when": "future_reducible subset stays limited to py_runtime_value_type_id and representative/source guard drift is empty",
    },
    "runtime_sot_followup": {
        "plan_path": "docs/ja/plans/p2-runtime-sot-linked-program-integration.md",
        "trigger_bucket": "rs_emitter_shared_type_id_residual",
        "handoff_when": "shared type-id seams remain must-remain-only until runtime/type-id ownership moves into a runtime SoT task",
    },
    "cs_bytearray_localization": {
        "plan_path": "docs/ja/plans/archive/20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md",
        "trigger_bucket": "crossruntime_mutation_helper_residual",
        "handoff_when": "cs bytearray compat seam stays isolated to py_append/py_pop and does not expand back to list or bytes mutation",
    },
}

FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION = {
    "future_reducible": {
        ("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py"),
    },
    "must_remain_until_runtime_task": {
        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
        ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
        ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
        ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
    },
}

FUTURE_CPP_SHARED_TYPE_ID_REDUCIBLE_ONLY = {
    ("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py"),
}

FUTURE_CPP_SHARED_TYPE_ID_MUST_REMAIN_ONLY = {
    ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
    ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
    ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
    ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
}

FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION = {
    "future_reducible": set(),
    "must_remain_until_runtime_task": EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
}

FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION = {
    "future_reducible": set(),
    "must_remain_until_runtime_task": EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
}

FUTURE_CROSSRUNTIME_MUTATION_CLASSIFICATION = {
    "future_reducible": EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"],
    "must_remain_until_runtime_task": set(),
}

SHARED_TYPE_ID_CLASSIFICATION_TASK_ID = (
    "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02"
)

SHARED_TYPE_ID_CLASSIFICATION_ORDER = (
    "cpp_emitter_shared_type_id_residual",
    "rs_emitter_shared_type_id_residual",
    "cs_emitter_shared_type_id_residual",
)


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


def _collect_future_representative_lane_issues() -> list[str]:
    issues: list[str] = []
    if set(FUTURE_REPRESENTATIVE_LANE_MANIFEST.keys()) != set(FUTURE_FOLLOWUP_BASELINE_BUCKETS):
        issues.append("future representative lane manifest keys do not match follow-up baseline buckets")
        return issues
    for bucket_name in FUTURE_FOLLOWUP_BASELINE_BUCKETS:
        if FUTURE_REPRESENTATIVE_LANE_MANIFEST[bucket_name] != REPRESENTATIVE_LANE_MANIFEST[bucket_name]:
            issues.append(
                "future representative lane manifest drifted from current representative lane manifest: "
                f"{bucket_name}"
            )
    expected_source_guard_paths = {
        path
        for bucket_name in FUTURE_FOLLOWUP_BASELINE_BUCKETS
        for path in REPRESENTATIVE_LANE_MANIFEST[bucket_name]["source_guard_paths"]
    }
    if FUTURE_SOURCE_GUARD_PATHS != expected_source_guard_paths:
        issues.append("future representative source guard path set drifted")
    for bucket_name, lane in FUTURE_REPRESENTATIVE_LANE_MANIFEST.items():
        smoke_file = lane["smoke_file"]
        smoke_tests = set(lane["smoke_tests"])
        source_guard_paths = set(lane["source_guard_paths"])
        smoke_text = (ROOT / smoke_file).read_text(encoding="utf-8", errors="ignore")
        for test_name in sorted(smoke_tests):
            if f"def {test_name}(" not in smoke_text:
                issues.append(
                    "future representative smoke missing: "
                    f"{bucket_name}: {smoke_file}: {test_name}"
                )
        for rel in sorted(source_guard_paths):
            if rel not in SOURCE_GUARD_REQUIRED_SUBSTRINGS:
                issues.append(
                    "future representative source guard path missing from guard inventory: "
                    f"{bucket_name}: {rel}"
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


def _collect_future_followup_issues() -> list[str]:
    issues: list[str] = []
    if not (ROOT / FUTURE_FOLLOWUP_PLAN_PATH).exists():
        issues.append(f"future emitter shrink plan missing: {FUTURE_FOLLOWUP_PLAN_PATH}")
    if FUTURE_FOLLOWUP_BASELINE_BUCKETS != (
        "cpp_emitter_shared_type_id_residual",
        "rs_emitter_shared_type_id_residual",
        "cs_emitter_shared_type_id_residual",
        "crossruntime_mutation_helper_residual",
    ):
        issues.append("future follow-up baseline bucket order drifted")
    if FUTURE_REDUCTION_ORDER != [
        "cpp_emitter_shared_type_id_residual",
        "rs_emitter_shared_type_id_residual",
        "cs_emitter_shared_type_id_residual",
        "crossruntime_mutation_helper_residual",
    ]:
        issues.append("future reduction order drifted")
    if set(FUTURE_FOLLOWUP_BASELINE_BUCKETS) - set(EXPECTED_BUCKETS.keys()):
        issues.append("future follow-up baseline references unknown emitter residual buckets")
    issues.extend(_collect_future_representative_lane_issues())
    issues.extend(_collect_shared_type_id_classification_issues())
    issues.extend(
        _collect_future_bucket_classification_issues(
            label="future crossruntime mutation classification",
            classification=FUTURE_CROSSRUNTIME_MUTATION_CLASSIFICATION,
            expected_future_reducible=EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"],
            expected_must_remain=set(),
            expected_bucket=EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"],
            required_prefix="src/toolchain/emit/cs/",
        )
    )
    issues.extend(_collect_future_handoff_issues())
    return issues


def _collect_cpp_future_shared_type_id_classification_issues() -> list[str]:
    issues: list[str] = []
    if set(FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION.keys()) != {
        "future_reducible",
        "must_remain_until_runtime_task",
    }:
        issues.append("future cpp shared type-id classification keys drifted")
        return issues
    future_reducible = FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION["future_reducible"]
    must_remain = FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION["must_remain_until_runtime_task"]
    overlaps = future_reducible & must_remain
    for symbol, rel in sorted(overlaps):
        issues.append(
            "future cpp shared type-id classification overlap: "
            f"{symbol} @ {rel}"
        )
    union = future_reducible | must_remain
    if union != EXPECTED_BUCKETS["cpp_emitter_shared_type_id_residual"]:
        issues.append("future cpp shared type-id classification drifted from residual bucket")
    if future_reducible != FUTURE_CPP_SHARED_TYPE_ID_REDUCIBLE_ONLY:
        issues.append("future cpp shared type-id reducible classification drifted")
    if must_remain != FUTURE_CPP_SHARED_TYPE_ID_MUST_REMAIN_ONLY:
        issues.append("future cpp shared type-id must-remain classification drifted")
    for symbol, rel in sorted(union):
        if not rel.startswith("src/toolchain/emit/cpp/"):
            issues.append(
                "future cpp shared type-id classification contains non-cpp path: "
                f"{symbol} @ {rel}"
            )
    return issues


def _collect_shared_type_id_classification_issues() -> list[str]:
    issues: list[str] = []
    if SHARED_TYPE_ID_CLASSIFICATION_TASK_ID != (
        "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02"
    ):
        issues.append("shared type-id classification task id drifted")
    if SHARED_TYPE_ID_CLASSIFICATION_ORDER != (
        "cpp_emitter_shared_type_id_residual",
        "rs_emitter_shared_type_id_residual",
        "cs_emitter_shared_type_id_residual",
    ):
        issues.append("shared type-id classification order drifted")
    issues.extend(_collect_cpp_future_shared_type_id_classification_issues())
    issues.extend(
        _collect_future_bucket_classification_issues(
            label="future rs shared type-id classification",
            classification=FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION,
            expected_future_reducible=set(),
            expected_must_remain=EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
            expected_bucket=EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
            required_prefix="src/toolchain/emit/rs/",
        )
    )
    issues.extend(
        _collect_future_bucket_classification_issues(
            label="future cs shared type-id classification",
            classification=FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION,
            expected_future_reducible=set(),
            expected_must_remain=EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
            expected_bucket=EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
            required_prefix="src/toolchain/emit/cs/",
        )
    )
    return issues


def _collect_future_bucket_classification_issues(
    *,
    label: str,
    classification: dict[str, set[tuple[str, str]]],
    expected_future_reducible: set[tuple[str, str]],
    expected_must_remain: set[tuple[str, str]],
    expected_bucket: set[tuple[str, str]],
    required_prefix: str,
) -> list[str]:
    issues: list[str] = []
    if set(classification.keys()) != {
        "future_reducible",
        "must_remain_until_runtime_task",
    }:
        issues.append(f"{label} keys drifted")
        return issues
    future_reducible = classification["future_reducible"]
    must_remain = classification["must_remain_until_runtime_task"]
    overlaps = future_reducible & must_remain
    for symbol, rel in sorted(overlaps):
        issues.append(f"{label} overlap: {symbol} @ {rel}")
    if (future_reducible | must_remain) != expected_bucket:
        issues.append(f"{label} drifted from residual bucket")
    if future_reducible != expected_future_reducible:
        issues.append(f"{label} future-reducible set drifted")
    if must_remain != expected_must_remain:
        issues.append(f"{label} must-remain set drifted")
    for symbol, rel in sorted(future_reducible | must_remain):
        if not rel.startswith(required_prefix):
            issues.append(f"{label} contains unexpected path: {symbol} @ {rel}")
    return issues


def _collect_future_handoff_issues() -> list[str]:
    issues: list[str] = []
    expected_keys = {
        "cpp_header_shrink",
        "runtime_sot_followup",
        "cs_bytearray_localization",
    }
    if set(FUTURE_HANDOFF_TARGETS.keys()) != expected_keys:
        issues.append("future handoff target keys drifted")
        return issues
    for handoff_name, payload in FUTURE_HANDOFF_TARGETS.items():
        plan_path = str(payload.get("plan_path", ""))
        trigger_bucket = str(payload.get("trigger_bucket", ""))
        handoff_when = str(payload.get("handoff_when", "")).strip()
        if plan_path == "":
            issues.append(f"future handoff target plan path missing: {handoff_name}")
        elif not (ROOT / plan_path).exists():
            issues.append(f"future handoff target plan missing: {handoff_name}: {plan_path}")
        if trigger_bucket not in FUTURE_FOLLOWUP_BASELINE_BUCKETS:
            issues.append(
                f"future handoff target references unknown baseline bucket: {handoff_name}: {trigger_bucket}"
            )
        if handoff_when == "":
            issues.append(f"future handoff target condition is empty: {handoff_name}")
    return issues


def _collect_inventory_issues() -> list[str]:
    observed = _collect_observed_pairs()
    expected = _collect_expected_pairs()
    issues = _collect_bucket_overlaps()
    issues.extend(_collect_cpp_typed_wrapper_reentry_issues())
    issues.extend(_collect_source_guard_issues())
    issues.extend(_collect_representative_lane_issues())
    issues.extend(_collect_active_reduction_bundle_issues())
    issues.extend(_collect_future_followup_issues())
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

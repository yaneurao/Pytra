from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_crossruntime_pyruntime_emitter_inventory as inventory_mod


class CheckCrossRuntimePyRuntimeEmitterInventoryTest(unittest.TestCase):
    def test_expected_and_observed_inventory_match(self) -> None:
        self.assertEqual(
            inventory_mod._collect_observed_pairs(),
            inventory_mod._collect_expected_pairs(),
        )

    def test_buckets_do_not_overlap(self) -> None:
        self.assertEqual(inventory_mod._collect_bucket_overlaps(), [])

    def test_cpp_typed_wrapper_reentry_is_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_cpp_typed_wrapper_reentry_issues(), [])

    def test_cpp_object_bridge_bucket_is_cpp_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["cpp_emitter_object_bridge_residual"]
        self.assertTrue(all(path.startswith("src/toolchain/emit/cpp/") for _, path in bucket))
        self.assertEqual({path for _, path in bucket}, set())
        self.assertEqual(
            inventory_mod.CPP_TYPED_WRAPPER_FORBIDDEN_PATHS,
            {
                "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
                "src/toolchain/emit/cpp/emitter/runtime_expr.py",
                "src/toolchain/emit/cpp/emitter/stmt.py",
            },
        )
        self.assertEqual({symbol for symbol, _ in bucket}, set())

    def test_cpp_shared_type_id_bucket_is_cpp_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["cpp_emitter_shared_type_id_residual"]
        self.assertEqual(
            {path for _, path in bucket},
            {
                "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
                "src/toolchain/emit/cpp/emitter/runtime_expr.py",
                "src/toolchain/emit/cpp/emitter/stmt.py",
            },
        )
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {
                "py_runtime_value_type_id",
                "py_runtime_value_isinstance",
                "py_runtime_type_id_is_subtype",
                "py_runtime_type_id_issubclass",
            },
        )

    def test_rs_shared_type_id_bucket_is_rs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"]
        self.assertEqual({path for _, path in bucket}, {"src/toolchain/emit/rs/emitter/rs_emitter.py"})
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {
                "py_runtime_value_type_id",
                "py_runtime_value_isinstance",
                "py_runtime_type_id_is_subtype",
                "py_runtime_type_id_issubclass",
            },
        )

    def test_cs_shared_type_id_bucket_is_cs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"]
        self.assertEqual({path for _, path in bucket}, {"src/toolchain/emit/cs/emitter/cs_emitter.py"})
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {
                "py_runtime_value_type_id",
                "py_runtime_value_isinstance",
                "py_runtime_type_id_is_subtype",
                "py_runtime_type_id_issubclass",
            },
        )

    def test_crossruntime_mutation_bucket_covers_cpp_and_cs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"]
        self.assertEqual({path for _, path in bucket}, {"src/toolchain/emit/cs/emitter/cs_emitter.py"})
        self.assertEqual({symbol for symbol, _ in bucket}, {"py_append", "py_pop"})

    def test_cpp_typed_lane_uses_direct_mutation_helpers(self) -> None:
        # py_list_append/extend/pop/clear/reverse/sort_mut removed from cpp_emitter.py
        # (P6-CPP-LIST-MUT-IR-BYPASS-FIX-01): replaced with direct .method() calls.
        # py_list_set_at_mut remains in stmt.py (no IR node yet for SetAt).
        self.assertEqual(
            inventory_mod._collect_cpp_typed_lane_direct_pairs(),
            {
                ("py_list_set_at_mut", "src/toolchain/emit/cpp/emitter/stmt.py"),
            },
        )

    def test_cpp_object_bridge_wrappers_stay_in_call_py_only(self) -> None:
        self.assertEqual(inventory_mod._collect_cpp_object_bridge_wrapper_pairs(), set())

    def test_cpp_typed_lane_symbols_do_not_overlap_object_bridge_wrappers(self) -> None:
        typed_pairs = inventory_mod._collect_cpp_typed_lane_direct_pairs()
        wrapper_pairs = inventory_mod._collect_cpp_object_bridge_wrapper_pairs()
        self.assertEqual({symbol for symbol, _ in typed_pairs} & {symbol for symbol, _ in wrapper_pairs}, set())
        self.assertEqual({path for _, path in typed_pairs} & {path for _, path in wrapper_pairs}, set())

    def test_target_end_state_keys_match_bucket_names(self) -> None:
        self.assertEqual(
            set(inventory_mod.TARGET_END_STATE.keys()),
            set(inventory_mod.EXPECTED_BUCKETS.keys()),
        )

    def test_representative_lane_manifest_keys_match_bucket_names(self) -> None:
        self.assertEqual(
            set(inventory_mod.REPRESENTATIVE_LANE_MANIFEST.keys()),
            set(inventory_mod.EXPECTED_BUCKETS.keys()),
        )

    def test_representative_lane_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_representative_lane_issues(), [])

    def test_representative_lane_manifest_stays_bucket_specific(self) -> None:
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["cpp_emitter_object_bridge_residual"],
            {
                "smoke_file": "test/unit/toolchain/emit/cpp/test_east3_cpp_bridge.py",
                "smoke_tests": {
                    "test_render_expr_pyobj_runtime_list_append_uses_low_level_bridge",
                    "test_emit_assign_pyobj_runtime_list_store_uses_low_level_bridge",
                    "test_transpile_typed_list_append_stays_out_of_object_bridge",
                    "test_transpile_typed_list_store_stays_out_of_object_bridge",
                },
                "source_guard_paths": set(),
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["cpp_emitter_shared_type_id_residual"],
            {
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
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["rs_emitter_shared_type_id_residual"],
            {
                "smoke_file": "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
                "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
                "source_guard_paths": {"src/toolchain/emit/rs/emitter/rs_emitter.py"},
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["cs_emitter_shared_type_id_residual"],
            {
                "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
                "source_guard_paths": {"src/toolchain/emit/cs/emitter/cs_emitter.py"},
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["crossruntime_mutation_helper_residual"],
            {
                "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                "smoke_tests": {
                    "test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not",
                    "test_bytearray_index_and_slice_compat_helpers_stay_explicit",
                },
                "source_guard_paths": {"src/toolchain/emit/cs/emitter/cs_emitter.py"},
            },
        )

    def test_source_guard_path_keys_match(self) -> None:
        self.assertEqual(
            set(inventory_mod.SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys()),
            {
                "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
                "src/toolchain/emit/cpp/emitter/runtime_expr.py",
                "src/toolchain/emit/cpp/emitter/stmt.py",
                "src/toolchain/emit/rs/emitter/rs_emitter.py",
                "src/toolchain/emit/cs/emitter/cs_emitter.py",
            },
        )
        self.assertEqual(
            set(inventory_mod.SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys()),
            set(inventory_mod.SOURCE_GUARD_FORBIDDEN_SUBSTRINGS.keys()),
        )

    def test_source_guard_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_source_guard_issues(), [])

    def test_source_guard_covers_cs_bytes_residual_lane(self) -> None:
        required = inventory_mod.SOURCE_GUARD_REQUIRED_SUBSTRINGS[
            "src/toolchain/emit/cs/emitter/cs_emitter.py"
        ]
        self.assertTrue(
            {
                "def _render_bytes_mutation_call(",
                'if owner_type == "bytes" and attr_raw in {"append", "pop"}:',
                'raise RuntimeError("csharp emitter: bytes mutation helpers are unsupported; use bytearray")',
                'return "Pytra.CsModule.py_runtime.py_append(" + owner_expr + ", " + rendered_args[0] + ")"',
                'return "Pytra.CsModule.py_runtime.py_pop(" + owner_expr + ")"',
                'return "Pytra.CsModule.py_runtime.py_slice(" + owner + ", " + lower_expr + ", " + upper_expr + ")"',
                'return "Pytra.CsModule.py_runtime.py_get(" + owner + ", " + idx + ")"',
            }.issubset(required)
        )

    def test_future_followup_baseline_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.FUTURE_FOLLOWUP_TASK_ID,
            "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01",
        )
        self.assertEqual(
            inventory_mod.FUTURE_FOLLOWUP_PLAN_PATH,
            "docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md",
        )
        self.assertEqual(
            inventory_mod.FUTURE_FOLLOWUP_BASELINE_BUCKETS,
            (
                "cpp_emitter_shared_type_id_residual",
                "rs_emitter_shared_type_id_residual",
                "cs_emitter_shared_type_id_residual",
                "crossruntime_mutation_helper_residual",
            ),
        )
        self.assertEqual(
            inventory_mod.FUTURE_REDUCTION_ORDER,
            [
                "cpp_emitter_shared_type_id_residual",
                "rs_emitter_shared_type_id_residual",
                "cs_emitter_shared_type_id_residual",
                "crossruntime_mutation_helper_residual",
            ],
        )
        self.assertEqual(inventory_mod._collect_future_followup_issues(), [])

    def test_future_representative_lane_manifest_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.FUTURE_REPRESENTATIVE_LANE_MANIFEST,
            {
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
                    "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
                    "source_guard_paths": {"src/toolchain/emit/rs/emitter/rs_emitter.py"},
                },
                "cs_emitter_shared_type_id_residual": {
                    "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                    "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
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
            },
        )
        self.assertEqual(
            inventory_mod.FUTURE_SOURCE_GUARD_PATHS,
            {
                "src/toolchain/emit/cpp/emitter/cpp_emitter.py",
                "src/toolchain/emit/cpp/emitter/runtime_expr.py",
                "src/toolchain/emit/cpp/emitter/stmt.py",
                "src/toolchain/emit/rs/emitter/rs_emitter.py",
                "src/toolchain/emit/cs/emitter/cs_emitter.py",
            },
        )
        self.assertEqual(inventory_mod._collect_future_representative_lane_issues(), [])

    def test_future_handoff_targets_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.FUTURE_HANDOFF_TARGETS,
            {
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
            },
        )
        self.assertEqual(inventory_mod._collect_future_handoff_issues(), [])

        self.assertEqual(
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION,
            {
                "future_reducible": {
                    ("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py"),
                },
                "must_remain_until_runtime_task": {
                    ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                    ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
                    ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                    ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                },
            },
        )
        self.assertEqual(
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_REDUCIBLE_ONLY,
            {("py_runtime_value_type_id", "src/toolchain/emit/cpp/emitter/cpp_emitter.py")},
        )
        self.assertEqual(
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_MUST_REMAIN_ONLY,
            {
                ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                ("py_runtime_value_isinstance", "src/toolchain/emit/cpp/emitter/stmt.py"),
                ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
                ("py_runtime_type_id_issubclass", "src/toolchain/emit/cpp/emitter/runtime_expr.py"),
            },
        )
        self.assertEqual(
            inventory_mod.FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION,
            {
                "future_reducible": set(),
                "must_remain_until_runtime_task": {
                    ("py_runtime_value_type_id", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                    ("py_runtime_value_isinstance", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                    ("py_runtime_type_id_is_subtype", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                    ("py_runtime_type_id_issubclass", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
                },
            },
        )
        self.assertEqual(
            inventory_mod.FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION,
            {
                "future_reducible": set(),
                "must_remain_until_runtime_task": {
                    ("py_runtime_value_type_id", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    ("py_runtime_value_isinstance", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    ("py_runtime_type_id_is_subtype", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    ("py_runtime_type_id_issubclass", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                },
            },
        )
        self.assertEqual(
            inventory_mod.FUTURE_CROSSRUNTIME_MUTATION_CLASSIFICATION,
            {
                "future_reducible": {
                    ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                    ("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                },
                "must_remain_until_runtime_task": set(),
            },
        )

    def test_shared_type_id_classification_contract_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.SHARED_TYPE_ID_CLASSIFICATION_TASK_ID,
            "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02",
        )
        self.assertEqual(
            inventory_mod.SHARED_TYPE_ID_CLASSIFICATION_ORDER,
            (
                "cpp_emitter_shared_type_id_residual",
                "rs_emitter_shared_type_id_residual",
                "cs_emitter_shared_type_id_residual",
            ),
        )
        self.assertEqual(
            inventory_mod._collect_shared_type_id_classification_issues(),
            [],
        )

    def test_cpp_future_shared_type_id_classification_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod._collect_cpp_future_shared_type_id_classification_issues(),
            [],
        )
        self.assertEqual(
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION["future_reducible"],
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_REDUCIBLE_ONLY,
        )
        self.assertEqual(
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_CLASSIFICATION["must_remain_until_runtime_task"],
            inventory_mod.FUTURE_CPP_SHARED_TYPE_ID_MUST_REMAIN_ONLY,
        )

    def test_non_cpp_future_classifications_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod._collect_future_bucket_classification_issues(
                label="future rs shared type-id classification",
                classification=inventory_mod.FUTURE_RS_SHARED_TYPE_ID_CLASSIFICATION,
                expected_future_reducible=set(),
                expected_must_remain=inventory_mod.EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
                expected_bucket=inventory_mod.EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"],
                required_prefix="src/toolchain/emit/rs/",
            ),
            [],
        )
        self.assertEqual(
            inventory_mod._collect_future_bucket_classification_issues(
                label="future cs shared type-id classification",
                classification=inventory_mod.FUTURE_CS_SHARED_TYPE_ID_CLASSIFICATION,
                expected_future_reducible=set(),
                expected_must_remain=inventory_mod.EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
                expected_bucket=inventory_mod.EXPECTED_BUCKETS["cs_emitter_shared_type_id_residual"],
                required_prefix="src/toolchain/emit/cs/",
            ),
            [],
        )
        self.assertEqual(
            inventory_mod._collect_future_bucket_classification_issues(
                label="future crossruntime mutation classification",
                classification=inventory_mod.FUTURE_CROSSRUNTIME_MUTATION_CLASSIFICATION,
                expected_future_reducible=inventory_mod.EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"],
                expected_must_remain=set(),
                expected_bucket=inventory_mod.EXPECTED_BUCKETS["crossruntime_mutation_helper_residual"],
                required_prefix="src/toolchain/emit/cs/",
            ),
            [],
        )

    def test_reduction_order_is_stable_and_complete(self) -> None:
        self.assertEqual(
            inventory_mod.REDUCTION_ORDER,
            [
                "crossruntime_mutation_helper_residual",
                "cpp_emitter_object_bridge_residual",
                "rs_emitter_shared_type_id_residual",
                "cs_emitter_shared_type_id_residual",
                "cpp_emitter_shared_type_id_residual",
            ],
        )

    def test_active_reduction_bundles_match_bucket_order(self) -> None:
        self.assertEqual(
            list(inventory_mod.ACTIVE_REDUCTION_BUNDLES.keys()),
            inventory_mod.REDUCTION_ORDER,
        )
        self.assertEqual(
            set(inventory_mod.ACTIVE_REDUCTION_BUNDLES.keys()),
            set(inventory_mod.EXPECTED_BUCKETS.keys()),
        )

    def test_active_reduction_bundles_are_classified(self) -> None:
        self.assertEqual(
            inventory_mod.ACTIVE_REDUCTION_BUNDLES,
            {
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
            },
        )
        self.assertEqual(inventory_mod._collect_active_reduction_bundle_issues(), [])

    def test_cpp_typed_wrapper_symbols_match_object_bridge_contexts(self) -> None:
        self.assertEqual(
            inventory_mod.CPP_TYPED_WRAPPER_SYMBOLS,
            {"py_append", "py_extend", "py_pop", "py_clear", "py_reverse", "py_sort", "py_set_at"},
        )


if __name__ == "__main__":
    unittest.main()

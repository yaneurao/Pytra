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
        self.assertTrue(all(path.startswith("src/backends/cpp/") for _, path in bucket))
        self.assertEqual(
            {path for _, path in bucket},
            {
                "src/backends/cpp/emitter/cpp_emitter.py",
                "src/backends/cpp/emitter/runtime_expr.py",
                "src/backends/cpp/emitter/stmt.py",
            },
        )
        self.assertEqual(
            inventory_mod.CPP_TYPED_WRAPPER_FORBIDDEN_PATHS,
            {
                "src/backends/cpp/emitter/cpp_emitter.py",
                "src/backends/cpp/emitter/runtime_expr.py",
                "src/backends/cpp/emitter/stmt.py",
            },
        )
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {
                "py_runtime_object_type_id",
                "py_runtime_object_isinstance",
            },
        )

    def test_cpp_shared_type_id_bucket_is_cpp_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["cpp_emitter_shared_type_id_residual"]
        self.assertEqual({path for _, path in bucket}, {"src/backends/cpp/emitter/runtime_expr.py"})
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {"py_runtime_type_id_is_subtype", "py_runtime_type_id_issubclass"},
        )

    def test_rs_shared_type_id_bucket_is_rs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["rs_emitter_shared_type_id_residual"]
        self.assertEqual({path for _, path in bucket}, {"src/backends/rs/emitter/rs_emitter.py"})
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
        self.assertEqual({path for _, path in bucket}, {"src/backends/cs/emitter/cs_emitter.py"})
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
        self.assertEqual({path for _, path in bucket}, {"src/backends/cs/emitter/cs_emitter.py"})
        self.assertEqual({symbol for symbol, _ in bucket}, {"py_append", "py_pop"})

    def test_cpp_typed_lane_uses_direct_mutation_helpers(self) -> None:
        self.assertEqual(
            inventory_mod._collect_cpp_typed_lane_direct_pairs(),
            {
                ("py_list_append_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_extend_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_pop_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_clear_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_reverse_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_sort_mut", "src/backends/cpp/emitter/cpp_emitter.py"),
                ("py_list_set_at_mut", "src/backends/cpp/emitter/stmt.py"),
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
                "smoke_file": "test/unit/backends/cpp/test_east3_cpp_bridge.py",
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
                "smoke_file": "test/unit/backends/cpp/test_east3_cpp_bridge.py",
                "smoke_tests": {"test_render_expr_supports_east3_obj_boundary_nodes"},
                "source_guard_paths": set(),
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["rs_emitter_shared_type_id_residual"],
            {
                "smoke_file": "test/unit/backends/rs/test_py2rs_smoke.py",
                "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
                "source_guard_paths": {"src/backends/rs/emitter/rs_emitter.py"},
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["cs_emitter_shared_type_id_residual"],
            {
                "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
                "smoke_tests": {"test_type_predicate_nodes_are_lowered_without_legacy_bridge"},
                "source_guard_paths": {"src/backends/cs/emitter/cs_emitter.py"},
            },
        )
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_LANE_MANIFEST["crossruntime_mutation_helper_residual"],
            {
                "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
                "smoke_tests": {
                    "test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not",
                    "test_bytearray_index_and_slice_compat_helpers_stay_explicit",
                },
                "source_guard_paths": {"src/backends/cs/emitter/cs_emitter.py"},
            },
        )

    def test_source_guard_path_keys_match(self) -> None:
        self.assertEqual(
            set(inventory_mod.SOURCE_GUARD_REQUIRED_SUBSTRINGS.keys()),
            {
                "src/backends/rs/emitter/rs_emitter.py",
                "src/backends/cs/emitter/cs_emitter.py",
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
            "src/backends/cs/emitter/cs_emitter.py"
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

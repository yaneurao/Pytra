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
                "src/backends/cpp/emitter/call.py",
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
                "py_append",
                "py_extend",
                "py_pop",
                "py_clear",
                "py_reverse",
                "py_sort",
                "py_set_at",
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
        self.assertEqual(
            inventory_mod._collect_cpp_object_bridge_wrapper_pairs(),
            {
                ("py_append", "src/backends/cpp/emitter/call.py"),
                ("py_extend", "src/backends/cpp/emitter/call.py"),
                ("py_pop", "src/backends/cpp/emitter/call.py"),
                ("py_clear", "src/backends/cpp/emitter/call.py"),
                ("py_reverse", "src/backends/cpp/emitter/call.py"),
                ("py_sort", "src/backends/cpp/emitter/call.py"),
                ("py_set_at", "src/backends/cpp/emitter/call.py"),
            },
        )

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

    def test_cpp_typed_wrapper_symbols_match_object_bridge_contexts(self) -> None:
        self.assertEqual(
            inventory_mod.CPP_TYPED_WRAPPER_SYMBOLS,
            {"py_append", "py_extend", "py_pop", "py_clear", "py_reverse", "py_sort", "py_set_at"},
        )


if __name__ == "__main__":
    unittest.main()

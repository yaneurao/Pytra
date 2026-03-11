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
            {symbol for symbol, _ in bucket},
            {"py_runtime_object_type_id", "py_runtime_object_isinstance"},
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
        self.assertEqual(
            {path for _, path in bucket},
            {
                "src/backends/cpp/emitter/call.py",
                "src/backends/cs/emitter/cs_emitter.py",
            },
        )
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {"py_append", "py_extend", "py_pop", "py_clear", "py_reverse", "py_sort", "py_set_at"},
        )


if __name__ == "__main__":
    unittest.main()

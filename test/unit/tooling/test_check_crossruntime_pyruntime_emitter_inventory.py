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
        bucket = inventory_mod.EXPECTED_BUCKETS["cpp_object_bridge_residual"]
        self.assertTrue(all(path.startswith("src/backends/cpp/") for _, path in bucket))
        self.assertEqual({path for _, path in bucket}, {"src/backends/cpp/emitter/call.py"})
        self.assertEqual(
            {symbol for symbol, _ in bucket},
            {"py_append", "py_extend", "py_pop", "py_clear", "py_reverse", "py_sort", "py_set_at"},
        )

    def test_shared_type_id_bucket_covers_all_three_emitters(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_type_id_contract"]
        self.assertTrue(any(path.startswith("src/backends/cpp/") for _, path in shared))
        self.assertTrue(any(path.startswith("src/backends/rs/") for _, path in shared))
        self.assertTrue(any(path.startswith("src/backends/cs/") for _, path in shared))
        self.assertTrue(
            all(symbol in {"py_runtime_type_id", "py_isinstance", "py_is_subtype", "py_issubclass"} for symbol, _ in shared)
        )

    def test_crossruntime_object_bridge_bucket_is_cs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["crossruntime_object_bridge_residual"]
        self.assertEqual(bucket, {
            ("py_append", "src/backends/cs/emitter/cs_emitter.py"),
            ("py_pop", "src/backends/cs/emitter/cs_emitter.py"),
        })


if __name__ == "__main__":
    unittest.main()

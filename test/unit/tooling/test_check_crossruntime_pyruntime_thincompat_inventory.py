from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_crossruntime_pyruntime_thincompat_inventory as inventory_mod


class CheckCrossRuntimePyRuntimeThinCompatInventoryTest(unittest.TestCase):
    def test_expected_and_observed_inventory_match(self) -> None:
        self.assertEqual(
            inventory_mod._collect_observed_pairs(),
            inventory_mod._collect_expected_pairs(),
        )

    def test_buckets_do_not_overlap(self) -> None:
        self.assertEqual(inventory_mod._collect_bucket_overlaps(), [])

    def test_cpp_header_blocker_bucket_is_cpp_only_and_small(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["cpp_header_thincompat_blocker"]
        self.assertEqual(bucket, set())

    def test_shared_type_id_api_bucket_is_rs_cs_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["crossruntime_shared_type_id_api"]
        self.assertTrue(all(path.startswith("src/backends/rs/") or path.startswith("src/backends/cs/") for _, path in bucket))
        self.assertTrue(
            all(
                symbol in {
                    "py_runtime_value_type_id",
                    "py_runtime_value_isinstance",
                    "py_runtime_type_id_is_subtype",
                    "py_runtime_type_id_issubclass",
                }
                for symbol, _ in bucket
            )
        )


if __name__ == "__main__":
    unittest.main()

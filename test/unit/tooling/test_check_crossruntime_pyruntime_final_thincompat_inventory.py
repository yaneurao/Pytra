from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_crossruntime_pyruntime_final_thincompat_inventory as inventory_mod


class CheckCrossRuntimePyRuntimeFinalThinCompatInventoryTest(unittest.TestCase):
    def test_observed_inventory_stays_within_classified_pairs(self) -> None:
        self.assertLessEqual(
            inventory_mod._collect_observed_pairs(),
            inventory_mod._collect_expected_pairs(),
        )

    def test_buckets_do_not_overlap(self) -> None:
        self.assertEqual(inventory_mod._collect_bucket_overlaps(), [])

    def test_bundle_order_is_locked(self) -> None:
        self.assertEqual(inventory_mod._collect_bundle_order_issues(), [])
        self.assertEqual(
            inventory_mod.REMOVAL_BUNDLE_ORDER,
            (
                "cpp_generated_final_thincompat_blocker",
                "rs_runtime_generic_alias_surface",
                "cs_runtime_generic_alias_surface",
                "cpp_header_final_thincompat_defs",
            ),
        )

    def test_target_end_state_is_locked(self) -> None:
        self.assertEqual(inventory_mod._collect_target_end_state_issues(), [])
        self.assertEqual(
            inventory_mod.TARGET_END_STATE,
            {
                "cpp_generated_final_thincompat_blocker": "empty_before_header_removal",
                "rs_runtime_generic_alias_surface": "internal_or_private_only_before_header_removal",
                "cs_runtime_generic_alias_surface": "internal_or_private_only_before_header_removal",
                "cpp_header_final_thincompat_defs": "remove_last_after_crossruntime_alignment",
            },
        )

    def test_cpp_header_bucket_is_only_the_two_final_templates(self) -> None:
        self.assertEqual(
            inventory_mod.EXPECTED_BUCKETS["cpp_header_final_thincompat_defs"],
            {
                ("py_runtime_type_id", "src/runtime/cpp/native/core/py_runtime.h"),
                ("py_isinstance", "src/runtime/cpp/native/core/py_runtime.h"),
            },
        )

    def test_cpp_generated_bucket_is_empty(self) -> None:
        self.assertEqual(inventory_mod.EXPECTED_BUCKETS["cpp_generated_final_thincompat_blocker"], set())

    def test_rs_and_cs_buckets_only_hold_generic_alias_surface(self) -> None:
        allowed_symbols = {"py_runtime_type_id", "py_is_subtype", "py_issubclass", "py_isinstance"}
        for bucket_name in ("rs_runtime_generic_alias_surface", "cs_runtime_generic_alias_surface"):
            bucket = inventory_mod.EXPECTED_BUCKETS[bucket_name]
            self.assertTrue(all(symbol in allowed_symbols for symbol, _ in bucket))
            if bucket_name.startswith("rs_"):
                self.assertTrue(all(path.startswith("src/runtime/rs/") for _, path in bucket))
            else:
                self.assertTrue(all(path.startswith("src/runtime/cs/") for _, path in bucket))

    def test_rs_and_cs_aliases_are_no_longer_public(self) -> None:
        self.assertEqual(inventory_mod._collect_target_end_state_issues(), [])


if __name__ == "__main__":
    unittest.main()

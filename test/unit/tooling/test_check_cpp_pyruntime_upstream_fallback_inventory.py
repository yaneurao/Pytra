from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from toolchain.compiler import cpp_pyruntime_upstream_fallback_inventory as inventory_mod
from tools import check_cpp_pyruntime_upstream_fallback_inventory as check_mod


class CheckCppPyRuntimeUpstreamFallbackInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_inventory_counts_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_count_issues(), [])

    def test_header_line_baseline_is_fixed(self) -> None:
        self.assertEqual(check_mod._collect_header_line_issues(), [])
        self.assertEqual(inventory_mod.HEADER_LINE_BASELINE, 1287)

    def test_inventory_bucket_order_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.INVENTORY_BUCKET_ORDER,
            (
                "header_bulk",
                "cpp_emitter_residual",
                "generated_runtime_residual",
                "sample_cpp_residual",
            ),
        )

    def test_matcher_and_stage_orders_are_fixed(self) -> None:
        self.assertEqual(inventory_mod.MATCHER_KIND_ORDER, ("literal", "regex"))
        self.assertEqual(
            inventory_mod.SHRINK_STAGE_ORDER,
            (
                "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-01",
                "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01",
                "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02",
                "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03",
                "P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01",
            ),
        )

    def test_header_bulk_inventory_is_fixed(self) -> None:
        by_id = {
            row["inventory_id"]: row
            for row in inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory()
        }
        self.assertEqual(
            by_id["header_object_bridge_mut_list_cast"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_object_bridge_const_list_cast"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_object_bridge_py_at"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_object_bridge_py_append"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_typed_list_copy_from_object"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_generic_make_object_fallback"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_generic_py_to_object_fallback"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["header_object_py_to_call_sites"]["expected_count"],
            5,
        )
        self.assertEqual(
            by_id["header_dict_key_charptr_object_coercion"]["expected_count"],
            2,
        )

    def test_caller_baselines_are_fixed(self) -> None:
        by_id = {
            row["inventory_id"]: row
            for row in inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory()
        }
        self.assertEqual(
            by_id["cpp_emitter_object_list_bridge_sites"]["expected_count"],
            1,
        )
        self.assertEqual(
            by_id["generated_runtime_object_list_bridge_sites"]["expected_count"],
            2,
        )
        self.assertEqual(
            by_id["generated_runtime_generic_index_sites"]["expected_count"],
            44,
        )
        self.assertEqual(
            by_id["sample_cpp_generic_index_sites"]["expected_count"],
            39,
        )

    def test_emitter_boxed_list_seed_inventory_row_is_retired(self) -> None:
        inventory_ids = {
            row["inventory_id"]
            for row in inventory_mod.iter_cpp_pyruntime_upstream_fallback_inventory()
        }
        self.assertNotIn("cpp_emitter_boxed_list_seed_sites", inventory_ids)
        self.assertNotIn("generated_runtime_boxed_list_seed_sites", inventory_ids)
        self.assertNotIn("sample_cpp_py_append_sites", inventory_ids)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from toolchain.compiler import backend_parity_representative_rollout_inventory as inventory_mod
from tools import check_backend_parity_representative_rollout_inventory as check_mod


class CheckBackendParityRepresentativeRolloutInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_bundle_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_bundle_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_cpp_representative_residual_inventory_is_empty(self) -> None:
        self.assertEqual(
            [cell for cell in inventory_mod.iter_representative_rollout_residual_cells() if cell["backend"] == "cpp"],
            [],
        )

    def test_representative_residual_inventory_is_rs_and_cs_only(self) -> None:
        self.assertEqual(
            {cell["backend"] for cell in inventory_mod.iter_representative_rollout_residual_cells()},
            {"rs", "cs"},
        )

    def test_bundle_order_and_next_backend_are_fixed(self) -> None:
        self.assertEqual(
            tuple(bundle["bundle_id"] for bundle in inventory_mod.iter_representative_rollout_bundles()),
            (
                "cpp_locked_baseline",
                "rs_syntax_iter_bundle",
                "rs_stdlib_bundle",
                "cs_syntax_iter_bundle",
                "cs_stdlib_bundle",
            ),
        )
        self.assertEqual(inventory_mod.REPRESENTATIVE_ROLLOUT_HANDOFF_V1["next_backend"], "rs")

    def test_bundle_feature_pairs_cover_exact_residual_set(self) -> None:
        residual_pairs = {
            (cell["backend"], cell["feature_id"])
            for cell in inventory_mod.iter_representative_rollout_residual_cells()
        }
        bundled_pairs = {
            (bundle["backend"], feature_id)
            for bundle in inventory_mod.iter_representative_rollout_bundles()
            for feature_id in bundle["feature_ids"]
        }
        self.assertEqual(residual_pairs, bundled_pairs)


if __name__ == "__main__":
    unittest.main()

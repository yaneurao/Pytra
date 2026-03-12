from __future__ import annotations

import unittest

from toolchain.compiler import backend_parity_secondary_rollout_inventory as inventory_mod
from tools import check_backend_parity_secondary_rollout_inventory as check_mod


class CheckBackendParitySecondaryRolloutInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_bundle_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_bundle_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_backend_order_and_next_bundle_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.SECONDARY_BACKEND_ORDER,
            ("go", "java", "kt", "scala", "swift", "nim"),
        )
        self.assertEqual(
            tuple(bundle["bundle_id"] for bundle in inventory_mod.iter_secondary_rollout_bundles()),
            ("go_java_kt_bundle", "scala_swift_nim_bundle"),
        )
        self.assertEqual(
            inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["completed_backends"],
            ("go", "java", "kt", "scala", "swift", "nim"),
        )
        self.assertIsNone(inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["next_backend"])
        self.assertEqual(inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["remaining_backends"], ())

    def test_bundle_feature_pairs_cover_exact_residual_set(self) -> None:
        residual_pairs = {
            (cell["backend"], cell["feature_id"])
            for cell in inventory_mod.iter_secondary_rollout_residual_cells()
        }
        bundled_pairs = {
            (backend, feature_id)
            for bundle in inventory_mod.iter_secondary_rollout_bundles()
            for backend, feature_ids in bundle["feature_ids_by_backend"].items()
            for feature_id in feature_ids
        }
        self.assertEqual(residual_pairs, bundled_pairs)

    def test_residual_feature_ids_by_backend_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1,
            {
                "go": (),
                "java": (),
                "kt": (),
                "scala": (),
                "swift": (),
                "nim": (),
            },
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_rollout_tier_contract as contract_mod
from tools import check_backend_parity_rollout_tier_contract as check_mod


class CheckBackendParityRolloutTierContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_rollout_tier_constants_are_fixed(self) -> None:
        self.assertEqual(contract_mod.ROLLOUT_TIER_ORDER, ("representative", "secondary", "long_tail"))
        self.assertEqual(
            contract_mod.ROLLOUT_TIER_BACKENDS,
            {
                "representative": ("cpp", "rs", "cs"),
                "secondary": ("go", "java", "kt", "scala", "swift", "nim"),
                "long_tail": ("js", "ts", "lua", "rb", "php"),
            },
        )

    def test_rollout_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_parity_rollout_tier_manifest().keys()),
            {
                "inventory_version",
                "tier_order",
                "backend_order",
                "doc_targets",
                "representative_tiers",
            },
        )


if __name__ == "__main__":
    unittest.main()

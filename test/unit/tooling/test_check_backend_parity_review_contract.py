from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_review_contract as contract_mod
from tools import check_backend_parity_review_contract as check_mod


class CheckBackendParityReviewContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_review_checklist_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_REVIEW_CHECKLIST_ORDER,
            (
                "feature_inventory",
                "matrix_state_recorded",
                "representative_tier_recorded",
                "later_tier_state_recorded",
                "unsupported_lanes_fail_closed",
                "docs_mirror",
            ),
        )
        self.assertEqual(
            contract_mod.PARITY_REVIEW_FAIL_CLOSED_ALLOWED_STATES,
            ("fail_closed", "not_started", "experimental"),
        )

    def test_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_parity_review_manifest().keys()),
            {
                "inventory_version",
                "source_manifests",
                "checklist_order",
                "fail_closed_allowed_states",
                "fail_closed_phase_rules",
                "forbidden_silent_fallback_labels",
                "downstream_task",
                "downstream_plan",
                "checklist",
            },
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_handoff_contract as contract_mod
from tools import check_backend_parity_handoff_contract as check_mod


class CheckBackendParityHandoffContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_target_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_HANDOFF_TARGET_ORDER,
            ("docs_matrix_page", "docs_index", "release_note", "tooling_manifest"),
        )

    def test_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_parity_handoff_manifest().keys()),
            {
                "inventory_version",
                "source_manifests",
                "target_order",
                "doc_targets",
                "release_note_targets",
                "tooling_targets",
                "rules",
                "downstream_task",
                "downstream_plan",
                "handoff_targets",
                "matrix_backend_order",
                "matrix_support_state_order",
                "rollout_tier_order",
                "review_checklist_order",
                "conformance_publish_target_order",
            },
        )


if __name__ == "__main__":
    unittest.main()

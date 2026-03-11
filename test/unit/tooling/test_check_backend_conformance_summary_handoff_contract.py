from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as contract_mod
from tools import check_backend_conformance_summary_handoff_contract as check_mod


class CheckBackendConformanceSummaryHandoffContractTest(unittest.TestCase):
    def test_summary_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_summary_inventory_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_publish_target_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER,
            ("support_matrix", "docs", "tooling"),
        )

    def test_docs_targets_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CONFORMANCE_SUMMARY_DOC_TARGETS,
            (
                "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
                "docs/en/plans/p7-backend-parity-rollout-and-matrix.md",
            ),
        )

    def test_tooling_exports_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CONFORMANCE_SUMMARY_TOOLING_EXPORTS,
            (
                "tools/export_backend_conformance_summary_handoff_manifest.py",
                "tools/check_backend_conformance_summary_handoff_contract.py",
            ),
        )

    def test_source_exports_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CONFORMANCE_SUMMARY_SOURCE_EXPORTS,
            {
                "seed_manifest": "tools/export_backend_conformance_seed_manifest.py",
                "runner_manifest": "tools/export_backend_conformance_runner_manifest.py",
                "runtime_parity_manifest": "tools/export_backend_conformance_runtime_parity_manifest.py",
            },
        )

    def test_summary_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_conformance_summary_handoff_manifest().keys()),
            {
                "inventory_version",
                "summary_kind",
                "publish_target_order",
                "docs_targets",
                "tooling_exports",
                "source_exports",
                "shared_lanes",
                "backend_selectable_lanes",
                "backend_order",
                "support_state_order",
                "representative_summary_entries",
            },
        )


if __name__ == "__main__":
    unittest.main()

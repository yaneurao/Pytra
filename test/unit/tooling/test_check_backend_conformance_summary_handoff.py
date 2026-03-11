from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_summary_handoff as handoff_mod
from tools import check_backend_conformance_summary_handoff as check_mod


class CheckBackendConformanceSummaryHandoffTest(unittest.TestCase):
    def test_handoff_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_handoff_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_summary_constants_are_fixed(self) -> None:
        self.assertEqual(handoff_mod.CONFORMANCE_SUMMARY_DESTINATION_ORDER, ("support_matrix", "docs", "tooling"))
        self.assertEqual(
            handoff_mod.CONFORMANCE_SUMMARY_REQUIRED_MANIFESTS,
            {
                "feature_matrix_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
                "conformance_seed": "backend_conformance_inventory.build_backend_conformance_seed_manifest",
                "runner_seed": "backend_conformance_runner_contract.build_backend_conformance_runner_manifest",
                "stdlib_runtime_seed": "backend_conformance_runtime_parity_contract.build_backend_conformance_runtime_parity_manifest",
            },
        )
        self.assertEqual(handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_TASK, "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01")
        self.assertEqual(handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN, "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md")

    def test_summary_handoff_contract_is_fixed(self) -> None:
        self.assertEqual(
            handoff_mod.iter_representative_conformance_summary_handoff(),
            (
                {
                    "destination": "support_matrix",
                    "source_manifest": "feature_contract_handoff.support_matrix_handoff",
                    "summary_keys": (
                        "feature_id",
                        "category",
                        "representative_fixture",
                        "backend_order",
                        "support_state_order",
                    ),
                    "downstream_task": "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01",
                    "downstream_plan": "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
                },
                {
                    "destination": "docs",
                    "source_manifest": "backend_conformance_runtime_parity_manifest.stdlib_runtime_modules",
                    "summary_keys": (
                        "module_name",
                        "case_stem",
                        "compare_unit",
                        "representative_backends",
                    ),
                    "downstream_task": "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01",
                    "downstream_plan": "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
                },
                {
                    "destination": "tooling",
                    "source_manifest": "backend_conformance_seed_manifest.lane_harness+fixture_lane_policy+runner_manifest",
                    "summary_keys": (
                        "lane_order",
                        "lane_harness",
                        "fixture_lane_policy",
                        "backend_order",
                        "selectable_lanes",
                    ),
                    "downstream_task": "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01",
                    "downstream_plan": "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
                },
            ),
        )

    def test_summary_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(handoff_mod.build_backend_conformance_summary_handoff_manifest().keys()),
            {
                "inventory_version",
                "destination_order",
                "backend_order",
                "support_state_order",
                "required_manifests",
                "summary_handoff",
            },
        )


if __name__ == "__main__":
    unittest.main()

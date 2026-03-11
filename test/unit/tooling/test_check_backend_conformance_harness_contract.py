from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_harness_contract as contract_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from tools import check_backend_conformance_harness_contract as check_mod


class CheckBackendConformanceHarnessContractTest(unittest.TestCase):
    def test_lane_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_lane_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_harness_stage_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CONFORMANCE_HARNESS_STAGE_ORDER,
            ("frontend", "ir", "backend", "runtime"),
        )

    def test_backend_selectable_lane_order_is_fixed(self) -> None:
        self.assertEqual(contract_mod.BACKEND_SELECTABLE_CONFORMANCE_LANES, ("emit", "runtime"))

    def test_representative_lane_contracts_match_feature_contract(self) -> None:
        self.assertEqual(
            tuple(entry["lane_id"] for entry in contract_mod.iter_representative_conformance_lane_contracts()),
            feature_contract_mod.CONFORMANCE_LANE_ORDER,
        )

    def test_lane_contracts_are_fixed(self) -> None:
        self.assertEqual(
            {
                entry["lane_id"]: (
                    entry["stage"],
                    entry["backend_selectable"],
                    entry["artifact_kind"],
                    entry["result_contract"],
                )
                for entry in contract_mod.iter_representative_conformance_lane_contracts()
            },
            {
                "parse": ("frontend", False, "parse_result", "parser_success_or_frontend_diagnostic"),
                "east": ("ir", False, "east_document", "east_document_or_frontend_diagnostic"),
                "east3_lowering": ("ir", False, "east3_document", "east3_document_or_lowering_diagnostic"),
                "emit": ("backend", True, "module_artifact", "artifact_or_fail_closed_backend_diagnostic"),
                "runtime": ("runtime", True, "runtime_execution", "stdout_stderr_exit_or_fail_closed_backend_diagnostic"),
            },
        )

    def test_harness_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_conformance_harness_manifest().keys()),
            {
                "inventory_version",
                "stage_order",
                "lane_order",
                "backend_selectable_lanes",
                "representative_backends",
                "fixture_class_order",
                "lane_contracts",
            },
        )


if __name__ == "__main__":
    unittest.main()

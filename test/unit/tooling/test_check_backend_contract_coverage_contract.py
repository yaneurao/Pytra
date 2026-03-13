from __future__ import annotations

import unittest

from toolchain.compiler import backend_contract_coverage_contract as contract_mod
from tools import check_backend_contract_coverage_contract as check_mod


class CheckBackendContractCoverageContractTest(unittest.TestCase):
    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_doc_wiring_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_doc_wiring_issues(), [])

    def test_plan_wiring_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_plan_wiring_issues(), [])

    def test_role_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.ROLE_ORDER,
            (
                "support_matrix",
                "coverage_matrix",
                "coverage_100_definition",
                "backend_test_matrix",
                "backend_specific_integration",
            ),
        )

    def test_manifest_wiring_is_fixed(self) -> None:
        manifest = contract_mod.build_backend_contract_coverage_contract_manifest()
        self.assertEqual(manifest["contract_status"], "docs_tooling_locked")
        self.assertEqual(
            manifest["backend_test_matrix_doc_paths"],
            (
                "docs/ja/language/backend-test-matrix.md",
                "docs/en/language/backend-test-matrix.md",
            ),
        )
        self.assertEqual(
            manifest["coverage_requirement_keys"],
            ("feature_id", "required_lane", "backend", "bundle_id_or_rule"),
        )


if __name__ == "__main__":
    unittest.main()

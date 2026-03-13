from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    backend_contract_coverage_suite_attachment_contract as contract_mod,
)
from tools import check_backend_contract_coverage_suite_attachment_contract as checker


class BackendContractCoverageSuiteAttachmentContractTest(unittest.TestCase):
    def test_attachment_issues_are_empty(self) -> None:
        self.assertEqual(checker._collect_attachment_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(checker._collect_manifest_issues(), [])

    def test_direct_matrix_suites_stay_bundle_attached(self) -> None:
        direct_rows = [
            row
            for row in contract_mod.iter_backend_contract_coverage_suite_attachments()
            if row["coverage_role"] == "direct_matrix_input"
        ]
        self.assertTrue(direct_rows)
        self.assertEqual({row["attachment_kind"] for row in direct_rows}, {"bundle_attachment"})

    def test_supporting_only_suites_stay_explicit_exclusions(self) -> None:
        excluded_rows = [
            row
            for row in contract_mod.iter_backend_contract_coverage_suite_attachments()
            if row["coverage_role"] == "supporting_only"
        ]
        self.assertTrue(excluded_rows)
        self.assertEqual({row["attachment_kind"] for row in excluded_rows}, {"explicit_exclusion"})
        self.assertEqual(
            {row["exclusion_reason"] for row in excluded_rows},
            set(contract_mod.EXCLUSION_REASON_ORDER),
        )


if __name__ == "__main__":
    unittest.main()

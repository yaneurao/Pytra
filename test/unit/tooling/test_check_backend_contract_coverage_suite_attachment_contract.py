from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    backend_contract_coverage_suite_attachment_contract as contract_mod,
)
from tools import check_backend_contract_coverage_suite_attachment_contract as checker


class BackendContractCoverageSuiteAttachmentContractTest(unittest.TestCase):
    def test_attachment_checker_is_clean(self) -> None:
        self.assertEqual(checker._collect_attachment_issues(), [])
        self.assertEqual(checker._collect_unmapped_issues(), [])
        self.assertEqual(checker._collect_supporting_only_issues(), [])
        self.assertEqual(checker._collect_coverage_accounting_issues(), [])
        self.assertEqual(checker._collect_manifest_issues(), [])

    def test_runtime_gap_stays_explicit_for_unit_backends(self) -> None:
        self.assertEqual(
            contract_mod.iter_unmapped_suite_candidate_rows(),
            (
                {
                    "suite_id": "unit_backends",
                    "bundle_kind": "runtime",
                    "status": "unmapped_candidate",
                    "reason_code": "runtime_rule_owned_seed",
                    "notes": (
                        "Runtime cells are still seeded as explicit case/module follow-up rules, so "
                        "backend unit-runtime checks stay visible as an unmapped candidate until the "
                        "runtime bundle absorbs them."
                    ),
                },
            ),
        )

    def test_supporting_only_suites_must_stay_explicit(self) -> None:
        self.assertEqual(
            tuple(row["suite_id"] for row in contract_mod.iter_supporting_only_suite_rows()),
            ("unit_link", "unit_selfhost", "unit_tooling"),
        )


if __name__ == "__main__":
    unittest.main()

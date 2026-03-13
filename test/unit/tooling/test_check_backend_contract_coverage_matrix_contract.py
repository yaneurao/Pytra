from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_contract_coverage_matrix_contract as contract_mod
from tools import check_backend_contract_coverage_matrix_contract as checker


class BackendContractCoverageMatrixContractTest(unittest.TestCase):
    def test_seed_issues_are_empty(self) -> None:
        self.assertEqual(checker._collect_seed_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(checker._collect_manifest_issues(), [])

    def test_seed_rows_cover_full_representative_product(self) -> None:
        self.assertEqual(
            len(contract_mod.iter_backend_contract_coverage_matrix_seed_rows()),
            contract_mod.expected_seed_row_count(),
        )

    def test_runtime_rows_stay_rule_owned(self) -> None:
        runtime_rows = [
            row
            for row in contract_mod.iter_backend_contract_coverage_matrix_seed_rows()
            if row["required_lane"] == "runtime"
        ]
        self.assertTrue(runtime_rows)
        self.assertEqual({row["owner_kind"] for row in runtime_rows}, {"rule"})
        self.assertEqual(
            {row["bundle_id_or_rule"] for row in runtime_rows},
            {"case_runtime_followup", "module_runtime_strategy_followup"},
        )


if __name__ == "__main__":
    unittest.main()

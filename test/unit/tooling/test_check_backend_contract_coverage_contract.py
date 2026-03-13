from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_contract_coverage_contract as contract_mod
from tools import check_backend_contract_coverage_contract as checker


class BackendContractCoverageContractTest(unittest.TestCase):
    def test_contract_checker_is_clean(self) -> None:
        self.assertEqual(checker._collect_contract_issues(), [])
        self.assertEqual(checker._collect_doc_issues(), [])

    def test_contract_manifest_is_fixed(self) -> None:
        manifest = contract_mod.build_backend_contract_coverage_contract_manifest()
        self.assertEqual(manifest["contract_version"], 1)
        self.assertEqual(manifest["coverage_matrix_status"], "planned_separate_surface")
        self.assertEqual(
            manifest["coverage_requirement_keys"],
            ["feature_id", "required_lane", "backend", "bundle_id_or_rule"],
        )
        self.assertEqual(
            manifest["role_split"],
            {
                "support_matrix": "Canonical feature x backend support-state publication surface.",
                "coverage_matrix": "Separate bundle-based publication surface for feature x required_lane x backend contract coverage.",
                "backend_test_matrix": "Backend-owned suite-health publication surface that must stay distinct from contract coverage.",
            },
        )


if __name__ == "__main__":
    unittest.main()

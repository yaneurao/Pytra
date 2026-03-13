from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    backend_contract_coverage_handoff_contract as contract_mod,
)
from tools import check_backend_contract_coverage_handoff_contract as checker


class BackendContractCoverageHandoffContractTest(unittest.TestCase):
    def test_handoff_checker_is_clean(self) -> None:
        self.assertEqual(checker._collect_manifest_issues(), [])
        self.assertEqual(checker._collect_doc_issues(), [])
        self.assertEqual(checker._collect_export_issues(), [])

    def test_handoff_manifest_is_fixed(self) -> None:
        manifest = contract_mod.build_backend_contract_coverage_handoff_manifest()
        self.assertEqual(manifest["contract_version"], 1)
        self.assertIn("coverage_matrix_ja", manifest["doc_targets"])
        self.assertIn("coverage_matrix_en", manifest["doc_targets"])
        self.assertIn("language_index_ja", manifest["doc_targets"])
        self.assertIn("language_index_en", manifest["doc_targets"])
        self.assertEqual(
            manifest["exports"]["exporter"],
            "tools/export_backend_contract_coverage_docs.py",
        )


if __name__ == "__main__":
    unittest.main()

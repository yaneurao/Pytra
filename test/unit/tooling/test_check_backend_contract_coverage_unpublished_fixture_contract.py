from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    backend_contract_coverage_unpublished_fixture_contract as contract_mod,
)
from tools import check_backend_contract_coverage_unpublished_fixture_contract as checker


class BackendContractCoverageUnpublishedFixtureContractTest(unittest.TestCase):
    def test_unpublished_fixture_checker_is_clean(self) -> None:
        self.assertEqual(checker._collect_classification_issues(), [])
        self.assertEqual(checker._collect_manifest_issues(), [])
        self.assertEqual(checker._collect_doc_issues(), [])

    def test_expected_rows_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.expected_unpublished_fixture_rows(),
            (
                {
                    "fixture_rel": "test/fixtures/typing/property_method_call.py",
                    "fixture_stem": "property_method_call",
                    "status": "support_matrix_promotion_candidate",
                    "target_surface": "support_matrix",
                },
                {
                    "fixture_rel": "test/fixtures/typing/list_bool_index.py",
                    "fixture_stem": "list_bool_index",
                    "status": "coverage_only_representative",
                    "target_surface": "coverage_matrix_only",
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()

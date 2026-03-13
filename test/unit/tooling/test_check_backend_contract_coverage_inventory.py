from __future__ import annotations

import unittest

from toolchain.compiler import backend_contract_coverage_inventory as inventory_mod
from tools import check_backend_contract_coverage_inventory as check_mod


class CheckBackendContractCoverageInventoryTest(unittest.TestCase):
    def test_bundle_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_bundle_issues(), [])

    def test_coverage_only_fixture_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_coverage_only_fixture_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_bundle_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            tuple(bundle["bundle_kind"] for bundle in inventory_mod.iter_backend_contract_coverage_bundles()),
            (
                "frontend",
                "emit",
                "runtime",
                "import_package",
                "ir2lang",
                "integration",
            ),
        )

    def test_coverage_only_fixtures_are_not_yet_in_support_matrix(self) -> None:
        support_fixtures = set(inventory_mod.SUPPORT_MATRIX_FIXTURES)
        self.assertEqual(
            {
                row["fixture_rel"]
                for row in inventory_mod.iter_backend_contract_coverage_only_fixtures()
                if row["fixture_rel"] in support_fixtures
            },
            set(),
        )

    def test_coverage_only_fixtures_cover_every_backend(self) -> None:
        expected = (
            "cpp",
            "rs",
            "cs",
            "go",
            "java",
            "kt",
            "scala",
            "swift",
            "nim",
            "js",
            "ts",
            "lua",
            "rb",
            "php",
        )
        for row in inventory_mod.iter_backend_contract_coverage_only_fixtures():
            self.assertEqual(tuple(item["backend"] for item in row["backend_evidence"]), expected)


if __name__ == "__main__":
    unittest.main()

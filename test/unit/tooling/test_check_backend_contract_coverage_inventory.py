from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod
from tools import check_backend_contract_coverage_inventory as checker


class BackendContractCoverageInventoryTest(unittest.TestCase):
    def test_inventory_checker_is_clean(self) -> None:
        self.assertEqual(checker._collect_seed_issues(), [])
        self.assertEqual(checker._collect_bundle_issues(), [])
        self.assertEqual(checker._collect_live_suite_issues(), [])
        self.assertEqual(checker._collect_unpublished_fixture_issues(), [])

    def test_bundle_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.COVERAGE_BUNDLE_ORDER,
            ("frontend", "emit", "runtime", "import_package", "ir2lang", "integration"),
        )
        by_id = {
            entry["bundle_id"]: entry for entry in inventory_mod.iter_coverage_bundle_taxonomy()
        }
        self.assertEqual(by_id["frontend"]["source_roots"], ("test/unit/common", "test/unit/ir"))
        self.assertEqual(by_id["ir2lang"]["source_roots"], ("test/ir", "tools/check_ir2lang_smoke.py"))
        self.assertIn("runtime_parity_compare", by_id["runtime"]["harness_kinds"])

    def test_live_suite_roles_and_unpublished_fixture_seeds_are_fixed(self) -> None:
        suites = {
            entry["suite_id"]: entry for entry in inventory_mod.iter_live_suite_family_inventory()
        }
        self.assertEqual(suites["unit_backends"]["coverage_role"], "direct_matrix_input")
        self.assertEqual(suites["unit_backends"]["bundle_candidates"], ("emit", "runtime", "import_package"))
        self.assertEqual(suites["unit_tooling"]["coverage_role"], "supporting_only")
        self.assertEqual(suites["unit_tooling"]["bundle_candidates"], ())

        unpublished = {
            entry["fixture_rel"]: entry for entry in inventory_mod.iter_unpublished_multi_backend_fixture_inventory()
        }
        self.assertEqual(
            tuple(unpublished),
            (
                "test/fixtures/typing/property_method_call.py",
                "test/fixtures/typing/list_bool_index.py",
            ),
        )
        self.assertIn("cpp", unpublished["test/fixtures/typing/property_method_call.py"]["observed_backends"])
        self.assertIn("kt", unpublished["test/fixtures/typing/list_bool_index.py"]["observed_backends"])

    def test_seed_manifest_contains_expected_sections(self) -> None:
        manifest = inventory_mod.build_backend_contract_coverage_seed_manifest()
        self.assertEqual(manifest["inventory_version"], 1)
        self.assertEqual(
            manifest["coverage_bundle_order"],
            ["frontend", "emit", "runtime", "import_package", "ir2lang", "integration"],
        )
        self.assertEqual(
            manifest["suite_family_order"],
            [
                "unit_common",
                "unit_backends",
                "unit_ir",
                "unit_link",
                "unit_selfhost",
                "unit_tooling",
                "ir_fixture",
                "integration",
                "transpile_artifact",
            ],
        )
        self.assertEqual(len(manifest["unpublished_multi_backend_fixtures"]), 2)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_operations_contract as contract_mod
from tools import check_backend_parity_operations_contract as check_mod


class CheckBackendParityOperationsContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_filesystem_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_filesystem_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_maintenance_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_OPERATIONS_MAINTENANCE_ORDER,
            (
                "contract_seed",
                "docs_publish",
                "docs_entrypoints",
                "release_note_link",
                "tooling_export",
                "archive_handoff",
            ),
        )


if __name__ == "__main__":
    unittest.main()

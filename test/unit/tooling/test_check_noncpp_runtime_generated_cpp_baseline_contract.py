from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    noncpp_runtime_generated_cpp_baseline_contract as contract_mod,
)
from tools import check_noncpp_runtime_generated_cpp_baseline_contract as check_mod


class CheckNonCppRuntimeGeneratedCppBaselineContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_bucket_order_matches_entries(self) -> None:
        entries = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        self.assertEqual(
            tuple(entry["bucket"] for entry in entries),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_bucket_order(),
        )

    def test_flattened_modules_match_entries(self) -> None:
        entries = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        expected = tuple(
            f"{entry['bucket']}/{module}"
            for entry in entries
            for module in entry["modules"]
        )
        self.assertEqual(expected, contract_mod.iter_noncpp_runtime_generated_cpp_baseline_modules())


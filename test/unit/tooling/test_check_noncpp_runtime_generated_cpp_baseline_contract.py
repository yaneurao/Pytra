from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    noncpp_runtime_generated_cpp_baseline_contract as contract_mod,
)
from tools import check_noncpp_runtime_generated_cpp_baseline_contract as check_mod


class CheckNonCppRuntimeGeneratedCppBaselineContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])
        self.assertEqual(check_mod._collect_policy_wording_issues(), [])

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

    def test_policy_doc_inventories_are_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["path"] for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_policy_files()),
            (
                "src/toolchain/compiler/noncpp_runtime_layout_contract.py",
                "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
                "tools/check_noncpp_runtime_layout_contract.py",
                "tools/check_noncpp_runtime_layout_rollout_remaining_contract.py",
            ),
        )
        self.assertEqual(
            tuple(entry["path"] for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_active_policy_docs()),
            (
                "docs/ja/spec/spec-runtime.md",
                "docs/en/spec/spec-runtime.md",
                "docs/ja/spec/spec-tools.md",
                "docs/en/spec/spec-tools.md",
            ),
        )
        self.assertEqual(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends(),
            ("cs", "go", "java", "rs", "swift", "nim", "kotlin", "scala", "js", "ts", "php"),
        )

    def test_legacy_state_buckets_match_runtime_contracts(self) -> None:
        self.assertEqual(
            check_mod._collect_runtime_layout_legacy_state_buckets(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_state_buckets(),
        )

    def test_helper_artifact_overlap_is_empty(self) -> None:
        self.assertEqual(
            check_mod._collect_helper_artifact_overlap_modules(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_overlap(),
        )

    def test_materialized_backend_baseline_has_no_missing_modules(self) -> None:
        buckets = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends():
            for entry in buckets:
                actual = check_mod._collect_backend_generated_modules(backend, entry["bucket"])
                missing = tuple(module for module in entry["modules"] if module not in actual)
                self.assertEqual(missing, (), msg=f"{backend} {entry['bucket']}")

from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_runtime_parity_contract as contract_mod
from tools import check_backend_conformance_runtime_parity_contract as check_mod


class CheckBackendConformanceRuntimeParityContractTest(unittest.TestCase):
    def test_runtime_strategy_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_runtime_strategy_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_stdlib_runtime_constants_are_fixed(self) -> None:
        self.assertEqual(contract_mod.STDLIB_RUNTIME_PARITY_STRATEGY_KIND, "stdlib_module_runtime_case")
        self.assertEqual(contract_mod.STDLIB_RUNTIME_CASE_ROOT, "fixture")
        self.assertEqual(contract_mod.STDLIB_RUNTIME_RUNNER_LANE, "runtime")
        self.assertEqual(contract_mod.STDLIB_RUNTIME_RUNNER_ENTRYPOINT, "tools/runtime_parity_check.py")
        self.assertEqual(contract_mod.STDLIB_RUNTIME_COMPARE_UNIT, "normalized_stdout_exitcode_artifact_digest")
        self.assertEqual(contract_mod.STDLIB_RUNTIME_BACKEND_ORDER, ("cpp", "rs", "cs"))

    def test_stdlib_runtime_module_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_representative_stdlib_runtime_parity(),
            (
                {
                    "feature_id": "stdlib.json.loads_dumps",
                    "module_name": "json",
                    "case_stem": "json_extended",
                    "representative_fixture": "test/fixtures/stdlib/json_extended.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
                {
                    "feature_id": "stdlib.pathlib.path_ops",
                    "module_name": "pathlib",
                    "case_stem": "pathlib_extended",
                    "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
                {
                    "feature_id": "stdlib.enum.enum_and_intflag",
                    "module_name": "enum",
                    "case_stem": "enum_extended",
                    "representative_fixture": "test/fixtures/stdlib/enum_extended.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
                {
                    "feature_id": "stdlib.argparse.parse_args",
                    "module_name": "argparse",
                    "case_stem": "argparse_extended",
                    "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
                {
                    "feature_id": "stdlib.math.imported_symbols",
                    "module_name": "math",
                    "case_stem": "pytra_std_import_math",
                    "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
                {
                    "feature_id": "stdlib.re.sub",
                    "module_name": "re",
                    "case_stem": "re_extended",
                    "representative_fixture": "test/fixtures/stdlib/re_extended.py",
                    "strategy_kind": "stdlib_module_runtime_case",
                    "case_root": "fixture",
                    "runner_lane": "runtime",
                    "runner_entrypoint": "tools/runtime_parity_check.py",
                    "compare_unit": "normalized_stdout_exitcode_artifact_digest",
                    "representative_backends": ("cpp", "rs", "cs"),
                },
            ),
        )

    def test_runtime_parity_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_conformance_runtime_parity_manifest().keys()),
            {
                "inventory_version",
                "strategy_kind",
                "case_root",
                "runner_lane",
                "runner_entrypoint",
                "compare_unit",
                "backend_order",
                "stdlib_runtime_modules",
            },
        )


if __name__ == "__main__":
    unittest.main()

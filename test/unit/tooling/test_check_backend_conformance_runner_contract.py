from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_conformance_runner_contract as contract_mod
from tools import check_backend_conformance_runner_contract as check_mod


class CheckBackendConformanceRunnerContractTest(unittest.TestCase):
    def test_runner_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_runner_inventory_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_representative_backend_order_is_fixed(self) -> None:
        self.assertEqual(contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS, ("cpp", "rs", "cs"))

    def test_backend_selectable_runner_lanes_are_fixed(self) -> None:
        self.assertEqual(contract_mod.BACKEND_SELECTABLE_RUNNER_LANES, ("emit", "runtime"))

    def test_lane_entrypoints_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.RUNNER_LANE_ENTRYPOINTS,
            {
                "emit": "src/pytra-cli.py",
                "runtime": "tools/runtime_parity_check.py",
            },
        )

    def test_runner_smoke_files_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.RUNNER_SMOKE_FILES,
            {
                "cpp": "test/unit/toolchain/emit/cpp/test_py2cpp_features.py",
                "rs": "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
                "cs": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
            },
        )

    def test_runner_inventory_contract_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_representative_conformance_runner_inventory(),
            (
                {
                    "backend": "cpp",
                    "selectable_lanes": ("emit", "runtime"),
                    "emit_target": "cpp",
                    "runtime_target": "cpp",
                    "emit_entrypoint": "src/pytra-cli.py",
                    "runtime_entrypoint": "tools/runtime_parity_check.py",
                    "smoke_file": "test/unit/toolchain/emit/cpp/test_py2cpp_features.py",
                },
                {
                    "backend": "rs",
                    "selectable_lanes": ("emit", "runtime"),
                    "emit_target": "rs",
                    "runtime_target": "rs",
                    "emit_entrypoint": "src/pytra-cli.py",
                    "runtime_entrypoint": "tools/runtime_parity_check.py",
                    "smoke_file": "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
                },
                {
                    "backend": "cs",
                    "selectable_lanes": ("emit", "runtime"),
                    "emit_target": "cs",
                    "runtime_target": "cs",
                    "emit_entrypoint": "src/pytra-cli.py",
                    "runtime_entrypoint": "tools/runtime_parity_check.py",
                    "smoke_file": "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
                },
            ),
        )

    def test_runner_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_conformance_runner_manifest().keys()),
            {
                "inventory_version",
                "backend_order",
                "selectable_lanes",
                "lane_entrypoints",
                "runner_inventory",
            },
        )


if __name__ == "__main__":
    unittest.main()

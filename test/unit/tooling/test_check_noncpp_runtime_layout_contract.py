from __future__ import annotations

import unittest

from src.toolchain.compiler import noncpp_runtime_layout_contract as contract_mod
from tools import check_noncpp_runtime_layout_contract as check_mod


class CheckNonCppRuntimeLayoutContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_csharp_lane_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_csharp_lane_issues(), [])

    def test_csharp_module_order_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["module_name"] for entry in contract_mod.iter_cs_std_lane_ownership()),
            ("json", "pathlib", "math", "re", "argparse", "enum"),
        )

    def test_generated_state_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CS_STD_GENERATED_STATE_ORDER,
            ("canonical_generated", "compare_artifact", "blocked", "no_runtime_module"),
        )

    def test_canonical_lane_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CS_STD_CANONICAL_LANE_ORDER,
            ("generated/std", "native/std", "native/built_in", "no_runtime_module"),
        )

    def test_csharp_lane_decisions_are_fixed(self) -> None:
        by_module = {
            entry["module_name"]: entry for entry in contract_mod.iter_cs_std_lane_ownership()
        }
        self.assertEqual(
            by_module["json"],
            {
                "module_name": "json",
                "canonical_lane": "native/std",
                "generated_std_state": "blocked",
                "generated_std_rel": "",
                "native_rel": "src/runtime/cs/native/std/json.cs",
                "canonical_runtime_symbol": "Pytra.CsModule.json",
                "representative_fixture": "test/fixtures/stdlib/json_extended.py",
                "smoke_guard_needles": (
                    "def test_representative_json_extended_fixture_transpiles",
                    "Pytra.CsModule.json.loads(s)",
                ),
                "rationale": "json.py cannot yet generate the C# runtime lane because the current ABI/object contract is still handwritten.",
            },
        )
        self.assertEqual(
            by_module["pathlib"]["canonical_lane"],
            "native/std",
        )
        self.assertEqual(
            by_module["pathlib"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["math"]["canonical_lane"],
            "native/built_in",
        )
        self.assertEqual(
            by_module["math"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["re"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["argparse"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["enum"]["canonical_lane"],
            "no_runtime_module",
        )


if __name__ == "__main__":
    unittest.main()

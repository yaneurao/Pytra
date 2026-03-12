from __future__ import annotations

import unittest

from src.toolchain.compiler import noncpp_runtime_layout_contract as contract_mod
from tools import check_noncpp_runtime_layout_contract as check_mod


class CheckNonCppRuntimeLayoutContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_csharp_lane_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_csharp_lane_issues(), [])

    def test_rust_lane_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_rust_lane_issues(), [])

    def test_csharp_module_order_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["module_name"] for entry in contract_mod.iter_cs_std_lane_ownership()),
            ("time", "json", "pathlib", "math", "re", "argparse", "enum"),
        )

    def test_rust_module_order_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["module_name"] for entry in contract_mod.iter_rs_std_lane_ownership()),
            ("time", "math", "pathlib", "os", "os_path", "glob", "json", "re", "argparse", "enum"),
        )

    def test_generated_state_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CS_STD_GENERATED_STATE_ORDER,
            ("canonical_generated", "compare_artifact", "blocked", "no_runtime_module"),
        )
        self.assertEqual(
            contract_mod.RS_STD_GENERATED_STATE_ORDER,
            ("canonical_generated", "compare_artifact", "blocked", "no_runtime_module"),
        )

    def test_canonical_lane_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.CS_STD_CANONICAL_LANE_ORDER,
            ("generated/std", "native/std", "native/built_in", "no_runtime_module"),
        )
        self.assertEqual(
            contract_mod.RS_STD_CANONICAL_LANE_ORDER,
            ("generated/std", "native/std", "native/built_in", "no_runtime_module"),
        )

    def test_csharp_lane_decisions_are_fixed(self) -> None:
        by_module = {
            entry["module_name"]: entry for entry in contract_mod.iter_cs_std_lane_ownership()
        }
        self.assertEqual(
            by_module["time"],
            {
                "module_name": "time",
                "canonical_lane": "native/built_in",
                "generated_std_state": "compare_artifact",
                "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
                "native_rel": "src/runtime/cs/native/built_in/time.cs",
                "canonical_runtime_symbol": "Pytra.CsModule.time",
                "representative_fixture": "test/fixtures/imports/import_time_from.py",
                "smoke_guard_needles": (
                    "def test_representative_time_import_fixture_transpiles",
                    "Pytra.CsModule.time.perf_counter()",
                ),
                "rationale": "generated/std/time.cs is still a compare artifact, but it is the narrowest C# std lane and therefore the first live-generated migration candidate.",
            },
        )
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

    def test_csharp_first_live_generated_candidate_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.get_cs_std_first_live_generated_candidate(),
            {
                "module_name": "time",
                "current_canonical_lane": "native/built_in",
                "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
                "native_rel": "src/runtime/cs/native/built_in/time.cs",
                "representative_fixture": "test/fixtures/imports/import_time_from.py",
                "smoke_guard_needles": (
                    "def test_representative_time_import_fixture_transpiles",
                    "Pytra.CsModule.time.perf_counter()",
                ),
                "deferred_native_canonical_modules": ("json", "pathlib", "math"),
                "deferred_no_runtime_modules": ("re", "argparse", "enum"),
                "rationale": "time is the first live-generated C# std candidate because its representative surface is a single `perf_counter()` lane, while `json` remains blocked and `pathlib/math` still depend on heavier native canonical seams.",
            },
        )

    def test_rust_lane_decisions_are_fixed(self) -> None:
        by_module = {
            entry["module_name"]: entry for entry in contract_mod.iter_rs_std_lane_ownership()
        }
        self.assertEqual(
            by_module["time"],
            {
                "module_name": "time",
                "canonical_lane": "native/built_in",
                "generated_std_state": "compare_artifact",
                "generated_std_rel": "src/runtime/rs/generated/std/time.rs",
                "native_rel": "src/runtime/rs/native/built_in/py_runtime.rs",
                "canonical_runtime_symbol": "pub use super::super::time;",
                "representative_fixture": "test/fixtures/imports/import_time_from.py",
                "smoke_guard_needles": (
                    "def test_runtime_scaffold_exposes_pytra_std_time_and_math",
                ),
                "rationale": "generated/std/time.rs exists for compare, but the live Rust runtime still comes from the native built_in scaffold re-export in py_runtime.rs.",
            },
        )
        self.assertEqual(by_module["math"]["canonical_lane"], "native/built_in")
        self.assertEqual(by_module["math"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["pathlib"]["canonical_lane"], "no_runtime_module")
        self.assertEqual(by_module["pathlib"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["os"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["os_path"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["glob"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["json"]["generated_std_state"], "blocked")
        self.assertEqual(by_module["re"]["canonical_lane"], "no_runtime_module")
        self.assertEqual(by_module["argparse"]["canonical_lane"], "no_runtime_module")
        self.assertEqual(by_module["enum"]["canonical_lane"], "no_runtime_module")


if __name__ == "__main__":
    unittest.main()

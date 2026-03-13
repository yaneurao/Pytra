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

    def test_builtin_lane_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_builtin_lane_issues(), [])

    def test_csharp_module_order_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["module_name"] for entry in contract_mod.iter_cs_std_lane_ownership()),
            ("time", "json", "pathlib", "math", "random", "re", "argparse", "sys", "timeit", "enum"),
        )

    def test_rust_module_order_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["module_name"] for entry in contract_mod.iter_rs_std_lane_ownership()),
            ("time", "math", "pathlib", "os", "os_path", "glob", "json", "random", "re", "argparse", "sys", "timeit", "enum"),
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

    def test_noncpp_generated_builtin_modules_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_generated_builtin_modules(),
            (
                "contains",
                "io_ops",
                "iter_ops",
                "numeric_ops",
                "predicates",
                "scalar_ops",
                "sequence",
                "string_ops",
                "type_id",
                "zip_ops",
            ),
        )

    def test_native_builtin_residual_sets_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_cs_native_builtin_residual_modules(),
            ("py_runtime",),
        )
        self.assertEqual(
            contract_mod.iter_rs_native_builtin_residual_modules(),
            ("py_runtime",),
        )

    def test_pytra_duplicate_and_compat_sets_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_cs_pytra_duplicate_delete_targets(),
            (
                "src/runtime/cs/pytra/built_in/math.cs",
                "src/runtime/cs/pytra/built_in/py_runtime.cs",
                "src/runtime/cs/pytra/built_in/time.cs",
                "src/runtime/cs/pytra/std/json.cs",
                "src/runtime/cs/pytra/std/pathlib.cs",
                "src/runtime/cs/pytra/utils/gif.cs",
                "src/runtime/cs/pytra/utils/png.cs",
            ),
        )
        self.assertEqual(
            contract_mod.iter_cs_pytra_generated_duplicate_delete_targets(),
            (
                "src/runtime/cs/pytra/utils/gif.cs",
                "src/runtime/cs/pytra/utils/png.cs",
            ),
        )
        self.assertEqual(
            contract_mod.iter_cs_pytra_handwritten_duplicate_delete_targets(),
            (
                "src/runtime/cs/pytra/built_in/math.cs",
                "src/runtime/cs/pytra/built_in/py_runtime.cs",
                "src/runtime/cs/pytra/built_in/time.cs",
                "src/runtime/cs/pytra/std/json.cs",
                "src/runtime/cs/pytra/std/pathlib.cs",
            ),
        )
        self.assertEqual(
            contract_mod.iter_rs_pytra_compat_allowlist(),
            (
                "src/runtime/rs/pytra/README.md",
                "src/runtime/rs/pytra/built_in/py_runtime.rs",
                "src/runtime/rs/pytra/compiler/README.md",
                "src/runtime/rs/pytra/std/README.md",
                "src/runtime/rs/pytra/utils/README.md",
            ),
        )
        self.assertEqual(
            check_mod._collect_relative_files(check_mod.CS_PYTRA_ROOT, ".cs"),
            (),
        )

    def test_csharp_lane_decisions_are_fixed(self) -> None:
        by_module = {
            entry["module_name"]: entry for entry in contract_mod.iter_cs_std_lane_ownership()
        }
        self.assertEqual(
            by_module["time"],
            {
                "module_name": "time",
                "canonical_lane": "generated/std",
                "generated_std_state": "canonical_generated",
                "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
                "native_rel": "src/runtime/cs/native/std/time_native.cs",
                "canonical_runtime_symbol": "Pytra.CsModule.time",
                "representative_fixture": "test/fixtures/imports/import_time_from.py",
                "smoke_guard_needles": (
                    "def test_representative_time_import_fixture_transpiles",
                    "Pytra.CsModule.time.perf_counter()",
                ),
                "rationale": "generated/std/time.cs is the first live-generated C# std lane, while native/std/time_native.cs remains only as the backing seam referenced by the generated wrapper.",
            },
        )
        self.assertEqual(
            by_module["json"],
            {
                "module_name": "json",
                "canonical_lane": "generated/std",
                "generated_std_state": "canonical_generated",
                "generated_std_rel": "src/runtime/cs/generated/std/json.cs",
                "native_rel": "",
                "canonical_runtime_symbol": "Pytra.CsModule.json",
                "representative_fixture": "test/fixtures/stdlib/json_extended.py",
                "smoke_guard_needles": (
                    "def test_representative_json_extended_fixture_transpiles",
                    "Pytra.CsModule.json.loads(s)",
                ),
                "rationale": "generated/std/json.cs is now the live C# JSON owner and ships the wrapper-shaped `Pytra.CsModule.json` surface directly from generated code without a handwritten native/std owner.",
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
            "generated/std",
        )
        self.assertEqual(
            by_module["math"]["generated_std_state"],
            "canonical_generated",
        )
        self.assertEqual(by_module["math"]["native_rel"], "")
        self.assertEqual(
            by_module["random"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["re"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["re"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["argparse"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["argparse"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["sys"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["sys"]["generated_std_state"],
            "compare_artifact",
        )
        self.assertEqual(
            by_module["timeit"]["canonical_lane"],
            "no_runtime_module",
        )
        self.assertEqual(
            by_module["timeit"]["generated_std_state"],
            "compare_artifact",
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
                "current_canonical_lane": "generated/std",
                "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
                "native_rel": "src/runtime/cs/native/std/time_native.cs",
                "representative_fixture": "test/fixtures/imports/import_time_from.py",
                "smoke_guard_needles": (
                    "def test_representative_time_import_fixture_transpiles",
                    "Pytra.CsModule.time.perf_counter()",
                ),
                "deferred_native_canonical_modules": ("pathlib",),
                "deferred_no_runtime_modules": ("random", "re", "argparse", "sys", "timeit", "enum"),
                "rationale": "time/math/json are now live-generated C# std lanes; `pathlib` remains the last heavier native canonical seam while the remaining std compare artifacts are not yet wired into the live runtime.",
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
        self.assertEqual(by_module["json"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["random"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["re"]["canonical_lane"], "no_runtime_module")
        self.assertEqual(by_module["re"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["argparse"]["canonical_lane"], "no_runtime_module")
        self.assertEqual(by_module["argparse"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["sys"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["timeit"]["generated_std_state"], "compare_artifact")
        self.assertEqual(by_module["enum"]["canonical_lane"], "no_runtime_module")


if __name__ == "__main__":
    unittest.main()

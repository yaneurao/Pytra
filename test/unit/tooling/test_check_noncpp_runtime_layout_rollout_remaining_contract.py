from __future__ import annotations

import unittest

from src.toolchain.compiler import noncpp_runtime_layout_rollout_remaining_contract as contract_mod
from tools import check_noncpp_runtime_layout_rollout_remaining_contract as check_mod


SCRIPT_FAMILY_COMPARE_BUILT_IN = (
    "built_in/contains",
    "built_in/io_ops",
    "built_in/iter_ops",
    "built_in/numeric_ops",
    "built_in/predicates",
    "built_in/scalar_ops",
    "built_in/sequence",
    "built_in/string_ops",
    "built_in/type_id",
    "built_in/zip_ops",
)

SCRIPT_FAMILY_COMPARE_STD = (
    "std/argparse",
    "std/glob",
    "std/json",
    "std/math",
    "std/os",
    "std/os_path",
    "std/pathlib",
    "std/random",
    "std/re",
    "std/sys",
    "std/time",
    "std/timeit",
)

SCRIPT_FAMILY_COMPARE_UTILS = (
    "utils/assertions",
    "utils/gif",
    "utils/png",
)

SCRIPT_FAMILY_COMPARE_BASELINE = (
    SCRIPT_FAMILY_COMPARE_BUILT_IN + SCRIPT_FAMILY_COMPARE_STD + SCRIPT_FAMILY_COMPARE_UTILS
)

SCRIPT_FAMILY_PARTIAL_GENERATED_COMPARE = SCRIPT_FAMILY_COMPARE_BASELINE

SCRIPT_FAMILY_MISSING_COMPARE_MODULES = ()

WAVE_A_IMAGE_RUNTIME_HELPER_ARTIFACTS = ("utils/image_runtime",)


class CheckNonCppRuntimeLayoutRolloutRemainingContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_current_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_current_inventory_issues(), [])

    def test_target_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_target_inventory_issues(), [])

    def test_wave_a_runtime_hook_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_runtime_hook_issues(), [])

    def test_module_bucket_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_module_bucket_issues(), [])

    def test_wave_b_blocked_reason_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_blocked_reason_issues(), [])

    def test_wave_b_generated_compare_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_generated_compare_issues(), [])

    def test_wave_a_generated_compare_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_generated_compare_issues(), [])

    def test_wave_b_native_residual_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_native_residual_issues(), [])

    def test_wave_b_native_residual_file_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_native_residual_file_issues(), [])

    def test_wave_b_compat_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_compat_issues(), [])

    def test_wave_b_compat_file_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_compat_file_issues(), [])

    def test_wave_b_compat_smoke_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_compat_smoke_issues(), [])

    def test_wave_b_generated_compare_smoke_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_b_generated_compare_smoke_issues(), [])

    def test_wave_a_generated_compare_smoke_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_generated_compare_smoke_issues(), [])

    def test_wave_a_compare_impossible_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_compare_impossible_issues(), [])

    def test_wave_a_generated_smoke_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_generated_smoke_issues(), [])

    def test_wave_a_native_residual_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_native_residual_issues(), [])

    def test_wave_a_native_residual_file_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_wave_a_native_residual_file_issues(), [])

    def test_backend_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_backend_order(),
            (
                "go",
                "java",
                "kotlin",
                "scala",
                "swift",
                "nim",
                "js",
                "ts",
                "lua",
                "ruby",
                "php",
            ),
        )

    def test_backend_hook_keys_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry["runtime_hook_key"]
            for entry in contract_mod.iter_remaining_noncpp_runtime_layout()
        }
        self.assertEqual(
            by_backend,
            {
                "go": "go",
                "java": "java",
                "kotlin": "kotlin",
                "scala": "scala",
                "swift": "swift",
                "nim": "nim",
                "js": "js_shims",
                "ts": "js_shims",
                "lua": "lua",
                "ruby": "ruby",
                "php": "php",
            },
        )

    def test_wave_a_runtime_hook_sources_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry["runtime_hook_files"]
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_a_hook_sources()
        }
        self.assertEqual(
            by_backend,
            {
                "go": (
                    "runtime/go/native/built_in/py_runtime.go",
                    "runtime/go/generated/utils/png.go",
                    "runtime/go/generated/utils/gif.go",
                ),
                "java": (
                    "runtime/java/native/built_in/PyRuntime.java",
                    "runtime/java/generated/utils/assertions.java",
                    "runtime/java/generated/utils/png.java",
                    "runtime/java/generated/utils/gif.java",
                    "runtime/java/generated/std/argparse.java",
                    "runtime/java/generated/std/glob.java",
                    "runtime/java/generated/std/os.java",
                    "runtime/java/generated/std/os_path.java",
                    "runtime/java/generated/std/random.java",
                    "runtime/java/generated/std/re.java",
                    "runtime/java/generated/std/sys.java",
                    "runtime/java/generated/std/time.java",
                    "runtime/java/generated/std/timeit.java",
                    "runtime/java/generated/std/json.java",
                    "runtime/java/generated/std/pathlib.java",
                    "runtime/java/generated/std/math.java",
                ),
                "kotlin": (
                    "runtime/kotlin/native/built_in/py_runtime.kt",
                    "runtime/kotlin/generated/utils/image_runtime.kt",
                ),
                "scala": (
                    "runtime/scala/native/built_in/py_runtime.scala",
                    "runtime/scala/generated/utils/image_runtime.scala",
                ),
                "swift": (
                    "runtime/swift/native/built_in/py_runtime.swift",
                    "runtime/swift/generated/utils/image_runtime.swift",
                ),
                "nim": (
                    "runtime/nim/native/built_in/py_runtime.nim",
                    "runtime/nim/generated/utils/image_runtime.nim",
                ),
            },
        )

    def test_wave_a_generated_smoke_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_wave_a_generated_smoke(),
            (
                {
                    "backend": "go",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.go",
                        "built_in/predicates.go",
                        "built_in/sequence.go",
                        "built_in/string_ops.go",
                        "built_in/type_id.go",
                        "std/argparse.go",
                        "std/glob.go",
                        "std/json.go",
                        "std/math.go",
                        "std/os.go",
                        "std/os_path.go",
                        "std/pathlib.go",
                        "std/random.go",
                        "std/re.go",
                        "std/sys.go",
                        "std/time.go",
                        "std/timeit.go",
                        "utils/assertions.go",
                        "utils/gif.go",
                        "utils/png.go",
                    ),
                },
                {
                    "backend": "java",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.java",
                        "built_in/predicates.java",
                        "built_in/sequence.java",
                        "built_in/string_ops.java",
                        "built_in/type_id.java",
                        "std/argparse.java",
                        "std/glob.java",
                        "std/json.java",
                        "std/math.java",
                        "std/os.java",
                        "std/os_path.java",
                        "std/pathlib.java",
                        "std/random.java",
                        "std/re.java",
                        "std/sys.java",
                        "std/time.java",
                        "std/timeit.java",
                        "utils/assertions.java",
                        "utils/gif.java",
                        "utils/png.java",
                    ),
                },
                {
                    "backend": "kotlin",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.kt",
                        "built_in/io_ops.kt",
                        "built_in/numeric_ops.kt",
                        "built_in/scalar_ops.kt",
                        "built_in/string_ops.kt",
                        "built_in/type_id.kt",
                        "std/argparse.kt",
                        "std/glob.kt",
                        "std/json.kt",
                        "std/math.kt",
                        "std/os.kt",
                        "std/os_path.kt",
                        "std/pathlib.kt",
                        "std/random.kt",
                        "std/re.kt",
                        "std/sys.kt",
                        "std/time.kt",
                        "std/timeit.kt",
                        "utils/assertions.kt",
                        "utils/gif.kt",
                        "utils/image_runtime.kt",
                        "utils/png.kt",
                    ),
                },
                {
                    "backend": "scala",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.scala",
                        "built_in/io_ops.scala",
                        "built_in/numeric_ops.scala",
                        "built_in/scalar_ops.scala",
                        "built_in/string_ops.scala",
                        "built_in/type_id.scala",
                        "std/argparse.scala",
                        "std/glob.scala",
                        "std/json.scala",
                        "std/math.scala",
                        "std/os.scala",
                        "std/os_path.scala",
                        "std/pathlib.scala",
                        "std/random.scala",
                        "std/re.scala",
                        "std/sys.scala",
                        "std/time.scala",
                        "std/timeit.scala",
                        "utils/assertions.scala",
                        "utils/gif.scala",
                        "utils/image_runtime.scala",
                        "utils/png.scala",
                    ),
                },
                {
                    "backend": "swift",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.swift",
                        "built_in/numeric_ops.swift",
                        "built_in/scalar_ops.swift",
                        "built_in/string_ops.swift",
                        "built_in/type_id.swift",
                        "std/argparse.swift",
                        "std/glob.swift",
                        "std/json.swift",
                        "std/math.swift",
                        "std/os.swift",
                        "std/os_path.swift",
                        "std/pathlib.swift",
                        "std/random.swift",
                        "std/re.swift",
                        "std/sys.swift",
                        "std/time.swift",
                        "std/timeit.swift",
                        "utils/assertions.swift",
                        "utils/gif.swift",
                        "utils/image_runtime.swift",
                        "utils/png.swift",
                    ),
                },
                {
                    "backend": "nim",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.nim",
                        "built_in/io_ops.nim",
                        "built_in/scalar_ops.nim",
                        "built_in/sequence.nim",
                        "built_in/string_ops.nim",
                        "built_in/type_id.nim",
                        "std/argparse.nim",
                        "std/glob.nim",
                        "std/json.nim",
                        "std/math.nim",
                        "std/os.nim",
                        "std/os_path.nim",
                        "std/pathlib.nim",
                        "std/random.nim",
                        "std/re.nim",
                        "std/sys.nim",
                        "std/time.nim",
                        "std/timeit.nim",
                        "utils/assertions.nim",
                        "utils/gif.nim",
                        "utils/image_runtime.nim",
                        "utils/png.nim",
                    ),
                },
            ),
        )

    def test_wave_a_generated_compare_smoke_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_wave_a_generated_compare_smoke(),
            (
                {
                    "backend": "go",
                    "smoke_kind": "build_run_smoke",
                    "smoke_targets": ("built_in/contains.go",),
                },
                {
                    "backend": "java",
                    "smoke_kind": "build_run_smoke",
                    "smoke_targets": ("built_in/contains.java",),
                },
                {
                    "backend": "kotlin",
                    "smoke_kind": "build_run_smoke",
                    "smoke_targets": ("built_in/contains.kt",),
                },
                {
                    "backend": "scala",
                    "smoke_kind": "source_guard",
                    "smoke_targets": ("built_in/contains.scala",),
                },
                {
                    "backend": "swift",
                    "smoke_kind": "build_run_smoke",
                    "smoke_targets": ("built_in/contains.swift",),
                },
                {
                    "backend": "nim",
                    "smoke_kind": "build_run_smoke",
                    "smoke_targets": ("built_in/contains.nim",),
                },
            ),
        )

    def test_wave_a_generated_compare_end_state_is_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_a_generated_compare()
        }
        self.assertEqual(
            by_backend,
            {
                "go": {
                    "backend": "go",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": (),
                },
                "java": {
                    "backend": "java",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": (),
                },
                "kotlin": {
                    "backend": "kotlin",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": WAVE_A_IMAGE_RUNTIME_HELPER_ARTIFACTS,
                },
                "scala": {
                    "backend": "scala",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": WAVE_A_IMAGE_RUNTIME_HELPER_ARTIFACTS,
                },
                "swift": {
                    "backend": "swift",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": WAVE_A_IMAGE_RUNTIME_HELPER_ARTIFACTS,
                },
                "nim": {
                    "backend": "nim",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": WAVE_A_IMAGE_RUNTIME_HELPER_ARTIFACTS,
                },
            },
        )

    def test_wave_a_compare_impossible_backend_set_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_wave_a_compare_impossible_backends(),
            (),
        )

    def test_wave_a_native_residuals_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_a_native_residuals()
        }
        self.assertEqual(
            by_backend,
            {
                "go": {
                    "backend": "go",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "java": {
                    "backend": "java",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "kotlin": {
                    "backend": "kotlin",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "scala": {
                    "backend": "scala",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "swift": {
                    "backend": "swift",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "nim": {
                    "backend": "nim",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
            },
        )

    def test_wave_a_native_residual_files_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_a_native_residual_files()
        }
        self.assertEqual(
            by_backend,
            {
                "go": {
                    "backend": "go",
                    "substrate_files": ("built_in/py_runtime.go",),
                    "compare_residual_files": (),
                },
                "java": {
                    "backend": "java",
                    "substrate_files": ("built_in/PyRuntime.java",),
                    "compare_residual_files": (),
                },
                "kotlin": {
                    "backend": "kotlin",
                    "substrate_files": ("built_in/py_runtime.kt",),
                    "compare_residual_files": (),
                },
                "scala": {
                    "backend": "scala",
                    "substrate_files": ("built_in/py_runtime.scala",),
                    "compare_residual_files": (),
                },
                "swift": {
                    "backend": "swift",
                    "substrate_files": ("built_in/py_runtime.swift",),
                    "compare_residual_files": (),
                },
                "nim": {
                    "backend": "nim",
                    "substrate_files": ("built_in/py_runtime.nim",),
                    "compare_residual_files": (),
                },
            },
        )

    def test_wave_b_compat_smoke_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_wave_b_compat_smoke(),
            (
                {
                    "backend": "js",
                    "smoke_kind": "direct_load",
                    "smoke_targets": (
                        "py_runtime.js",
                        "std/json.js",
                        "std/math.js",
                        "std/pathlib.js",
                        "std/time.js",
                        "utils/gif.js",
                        "utils/png.js",
                    ),
                },
                {
                    "backend": "ts",
                    "smoke_kind": "source_reexport",
                    "smoke_targets": (
                        "py_runtime.ts",
                        "std/json.ts",
                        "std/math.ts",
                        "std/pathlib.ts",
                        "std/time.ts",
                        "utils/gif.ts",
                        "utils/png.ts",
                    ),
                },
                {
                    "backend": "lua",
                    "smoke_kind": "direct_load",
                    "smoke_targets": ("built_in/py_runtime.lua",),
                },
                {
                    "backend": "ruby",
                    "smoke_kind": "direct_load",
                    "smoke_targets": ("built_in/py_runtime.rb",),
                },
                {
                    "backend": "php",
                    "smoke_kind": "direct_load",
                    "smoke_targets": (
                        "py_runtime.php",
                        "std/time.php",
                        "utils/gif.php",
                        "utils/png.php",
                    ),
                },
            ),
        )

    def test_wave_b_generated_compare_smoke_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_wave_b_generated_compare_smoke(),
            (
                {
                    "backend": "js",
                    "smoke_kind": "direct_load",
                    "smoke_targets": (
                        "built_in/contains.js",
                        "built_in/predicates.js",
                        "built_in/sequence.js",
                    ),
                },
                {
                    "backend": "ts",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.ts",
                        "built_in/sequence.ts",
                    ),
                },
                {
                    "backend": "php",
                    "smoke_kind": "direct_load",
                    "smoke_targets": (
                        "built_in/contains.php",
                        "built_in/predicates.php",
                        "built_in/sequence.php",
                    ),
                },
            ),
        )

    def test_target_root_taxonomy_is_fixed(self) -> None:
        for entry in contract_mod.iter_remaining_noncpp_runtime_layout():
            self.assertEqual(entry["target_roots"], ("generated", "native", "pytra"))

    def test_generated_compare_baseline_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_remaining_noncpp_runtime_generated_compare_baseline(),
            SCRIPT_FAMILY_COMPARE_BASELINE,
        )

    def test_representative_lane_mappings_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry["lane_mappings"]
            for entry in contract_mod.iter_remaining_noncpp_runtime_layout()
        }
        self.assertIn(
            {
                "current_prefix": "src/runtime/go/generated/utils/",
                "target_prefix": "src/runtime/go/generated/utils/",
                "ownership": "generated",
                "rationale": "Go image helpers already live in the canonical generated/utils lane after the Wave A path cutover.",
            },
            by_backend["go"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/go/generated/built_in/",
                "target_prefix": "src/runtime/go/generated/built_in/",
                "ownership": "generated",
                "rationale": "Go live-generated built_in compare artifacts live in generated/built_in for the compile-safe subset after the S4 alignment bundle.",
            },
            by_backend["go"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/go/generated/std/",
                "target_prefix": "src/runtime/go/generated/std/",
                "ownership": "generated",
                "rationale": "Go SoT-generated std compare artifacts now live in generated/std after the cpp-baseline materialization bundle.",
            },
            by_backend["go"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "target_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "ownership": "compat",
                "rationale": "The public Go runtime shim has already been normalized into pytra/built_in.",
            },
            by_backend["go"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/java/generated/built_in/",
                "target_prefix": "src/runtime/java/generated/built_in/",
                "ownership": "generated",
                "rationale": "Java live-generated built_in compare artifacts live in generated/built_in for the compile-safe subset after the S4 alignment bundle.",
            },
            by_backend["java"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/kotlin/generated/built_in/",
                "target_prefix": "src/runtime/kotlin/generated/built_in/",
                "ownership": "generated",
                "rationale": "Kotlin compile-safe built_in compare artifacts live in generated/built_in after the S4 alignment bundle.",
            },
            by_backend["kotlin"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/kotlin/generated/std/",
                "target_prefix": "src/runtime/kotlin/generated/std/",
                "ownership": "generated",
                "rationale": "Kotlin SoT-generated std compare artifacts now live in generated/std after the cpp-baseline materialization bundle.",
            },
            by_backend["kotlin"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/scala/generated/built_in/",
                "target_prefix": "src/runtime/scala/generated/built_in/",
                "ownership": "generated",
                "rationale": "Scala source-guarded built_in compare artifacts live in generated/built_in after the S4 alignment bundle.",
            },
            by_backend["scala"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/scala/generated/std/",
                "target_prefix": "src/runtime/scala/generated/std/",
                "ownership": "generated",
                "rationale": "Scala SoT-generated std compare artifacts now live in generated/std after the cpp-baseline materialization bundle.",
            },
            by_backend["scala"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/swift/generated/built_in/",
                "target_prefix": "src/runtime/swift/generated/built_in/",
                "ownership": "generated",
                "rationale": "Swift compile-safe built_in compare artifacts live in generated/built_in after the S4 alignment bundle.",
            },
            by_backend["swift"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/swift/generated/std/",
                "target_prefix": "src/runtime/swift/generated/std/",
                "ownership": "generated",
                "rationale": "Swift SoT-generated std compare artifacts now live in generated/std after the cpp-baseline materialization bundle.",
            },
            by_backend["swift"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/nim/generated/built_in/",
                "target_prefix": "src/runtime/nim/generated/built_in/",
                "ownership": "generated",
                "rationale": "Nim compile-safe built_in compare artifacts live in generated/built_in after the S4 alignment bundle.",
            },
            by_backend["nim"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/nim/generated/std/",
                "target_prefix": "src/runtime/nim/generated/std/",
                "ownership": "generated",
                "rationale": "Nim SoT-generated std compare artifacts now live in generated/std after the cpp-baseline materialization bundle.",
            },
            by_backend["nim"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/js/pytra/std/time.js",
                "target_prefix": "src/runtime/js/pytra/std/time.js",
                "ownership": "compat",
                "rationale": "JS public std shims already live in bucketed pytra/std paths after the Wave B path cutover.",
            },
            by_backend["js"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/js/generated/built_in/",
                "target_prefix": "src/runtime/js/generated/built_in/",
                "ownership": "generated",
                "rationale": "JS live-generated built_in compare artifacts live in generated/built_in once the Wave B compare lanes are materialized.",
            },
            by_backend["js"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/js/generated/std/",
                "target_prefix": "src/runtime/js/generated/std/",
                "ownership": "generated",
                "rationale": "JS live-generated std compare artifacts live in generated/std once the Wave B std lanes are materialized.",
            },
            by_backend["js"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/ts/generated/built_in/",
                "target_prefix": "src/runtime/ts/generated/built_in/",
                "ownership": "generated",
                "rationale": "TS live-generated built_in compare artifacts live in generated/built_in once the Wave B compare lanes are materialized.",
            },
            by_backend["ts"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/php/generated/utils/",
                "target_prefix": "src/runtime/php/generated/utils/",
                "ownership": "generated",
                "rationale": "PHP image helpers already live in generated/utils after the Wave B path cutover.",
            },
            by_backend["php"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/php/generated/built_in/",
                "target_prefix": "src/runtime/php/generated/built_in/",
                "ownership": "generated",
                "rationale": "PHP live-generated built_in compare artifacts live in generated/built_in once the Wave B compare lanes are materialized.",
            },
            by_backend["php"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/php/generated/std/",
                "target_prefix": "src/runtime/php/generated/std/",
                "ownership": "generated",
                "rationale": "PHP live-generated std compare artifacts live in generated/std once the Wave B std lanes are materialized.",
            },
            by_backend["php"],
        )

    def test_current_inventory_is_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_current_inventory()
        }
        self.assertEqual(
            by_backend["go"],
            {
                "backend": "go",
                "pytra_core_files": ("built_in/py_runtime.go",),
                "pytra_gen_files": (
                    "built_in/contains.go",
                    "built_in/io_ops.go",
                    "built_in/iter_ops.go",
                    "built_in/numeric_ops.go",
                    "built_in/predicates.go",
                    "built_in/scalar_ops.go",
                    "built_in/sequence.go",
                    "built_in/string_ops.go",
                    "built_in/type_id.go",
                    "built_in/zip_ops.go",
                    "std/argparse.go",
                    "std/glob.go",
                    "std/json.go",
                    "std/math.go",
                    "std/os.go",
                    "std/os_path.go",
                    "std/pathlib.go",
                    "std/random.go",
                    "std/re.go",
                    "std/sys.go",
                    "std/time.go",
                    "std/timeit.go",
                    "utils/assertions.go",
                    "utils/gif.go",
                    "utils/png.go",
                ),
                "pytra_files": ("built_in/py_runtime.go",),
            },
        )
        self.assertEqual(
            by_backend["java"]["pytra_gen_files"],
            (
                "built_in/contains.java",
                "built_in/io_ops.java",
                "built_in/iter_ops.java",
                "built_in/numeric_ops.java",
                "built_in/predicates.java",
                "built_in/scalar_ops.java",
                "built_in/sequence.java",
                "built_in/string_ops.java",
                "built_in/type_id.java",
                "built_in/zip_ops.java",
                "std/argparse.java",
                "std/glob.java",
                "std/json.java",
                "std/math.java",
                "std/os.java",
                "std/os_path.java",
                "std/pathlib.java",
                "std/random.java",
                "std/re.java",
                "std/sys.java",
                "std/time.java",
                "std/timeit.java",
                "utils/assertions.java",
                "utils/gif.java",
                "utils/png.java",
            ),
        )
        self.assertEqual(
            by_backend["kotlin"]["pytra_gen_files"],
            (
                "built_in/contains.kt",
                "built_in/io_ops.kt",
                "built_in/iter_ops.kt",
                "built_in/numeric_ops.kt",
                "built_in/predicates.kt",
                "built_in/scalar_ops.kt",
                "built_in/sequence.kt",
                "built_in/string_ops.kt",
                "built_in/type_id.kt",
                "built_in/zip_ops.kt",
                "std/argparse.kt",
                "std/glob.kt",
                "std/json.kt",
                "std/math.kt",
                "std/os.kt",
                "std/os_path.kt",
                "std/pathlib.kt",
                "std/random.kt",
                "std/re.kt",
                "std/sys.kt",
                "std/time.kt",
                "std/timeit.kt",
                "utils/assertions.kt",
                "utils/gif.kt",
                "utils/image_runtime.kt",
                "utils/png.kt",
            ),
        )
        self.assertEqual(
            by_backend["scala"]["pytra_gen_files"],
            (
                "built_in/contains.scala",
                "built_in/io_ops.scala",
                "built_in/iter_ops.scala",
                "built_in/numeric_ops.scala",
                "built_in/predicates.scala",
                "built_in/scalar_ops.scala",
                "built_in/sequence.scala",
                "built_in/string_ops.scala",
                "built_in/type_id.scala",
                "built_in/zip_ops.scala",
                "std/argparse.scala",
                "std/glob.scala",
                "std/json.scala",
                "std/math.scala",
                "std/os.scala",
                "std/os_path.scala",
                "std/pathlib.scala",
                "std/random.scala",
                "std/re.scala",
                "std/sys.scala",
                "std/time.scala",
                "std/timeit.scala",
                "utils/assertions.scala",
                "utils/gif.scala",
                "utils/image_runtime.scala",
                "utils/png.scala",
            ),
        )
        self.assertEqual(
            by_backend["swift"]["pytra_gen_files"],
            (
                "built_in/contains.swift",
                "built_in/io_ops.swift",
                "built_in/iter_ops.swift",
                "built_in/numeric_ops.swift",
                "built_in/predicates.swift",
                "built_in/scalar_ops.swift",
                "built_in/sequence.swift",
                "built_in/string_ops.swift",
                "built_in/type_id.swift",
                "built_in/zip_ops.swift",
                "std/argparse.swift",
                "std/glob.swift",
                "std/json.swift",
                "std/math.swift",
                "std/os.swift",
                "std/os_path.swift",
                "std/pathlib.swift",
                "std/random.swift",
                "std/re.swift",
                "std/sys.swift",
                "std/time.swift",
                "std/timeit.swift",
                "utils/assertions.swift",
                "utils/gif.swift",
                "utils/image_runtime.swift",
                "utils/png.swift",
            ),
        )
        self.assertEqual(
            by_backend["nim"]["pytra_gen_files"],
            (
                "built_in/contains.nim",
                "built_in/io_ops.nim",
                "built_in/iter_ops.nim",
                "built_in/numeric_ops.nim",
                "built_in/predicates.nim",
                "built_in/scalar_ops.nim",
                "built_in/sequence.nim",
                "built_in/string_ops.nim",
                "built_in/type_id.nim",
                "built_in/zip_ops.nim",
                "std/argparse.nim",
                "std/glob.nim",
                "std/json.nim",
                "std/math.nim",
                "std/os.nim",
                "std/os_path.nim",
                "std/pathlib.nim",
                "std/random.nim",
                "std/re.nim",
                "std/sys.nim",
                "std/time.nim",
                "std/timeit.nim",
                "utils/assertions.nim",
                "utils/gif.nim",
                "utils/image_runtime.nim",
                "utils/png.nim",
            ),
        )
        self.assertEqual(
            by_backend["js"]["pytra_gen_files"],
            (
                "built_in/contains.js",
                "built_in/io_ops.js",
                "built_in/iter_ops.js",
                "built_in/numeric_ops.js",
                "built_in/predicates.js",
                "built_in/scalar_ops.js",
                "built_in/sequence.js",
                "built_in/string_ops.js",
                "built_in/type_id.js",
                "built_in/zip_ops.js",
                "std/argparse.js",
                "std/glob.js",
                "std/json.js",
                "std/math.js",
                "std/os.js",
                "std/os_path.js",
                "std/pathlib.js",
                "std/random.js",
                "std/re.js",
                "std/sys.js",
                "std/time.js",
                "std/timeit.js",
                "utils/assertions.js",
                "utils/gif.js",
                "utils/png.js",
            ),
        )
        self.assertEqual(
            by_backend["php"]["pytra_gen_files"],
            (
                "built_in/contains.php",
                "built_in/io_ops.php",
                "built_in/iter_ops.php",
                "built_in/numeric_ops.php",
                "built_in/predicates.php",
                "built_in/scalar_ops.php",
                "built_in/sequence.php",
                "built_in/string_ops.php",
                "built_in/type_id.php",
                "built_in/zip_ops.php",
                "std/argparse.php",
                "std/glob.php",
                "std/json.php",
                "std/math.php",
                "std/os.php",
                "std/os_path.php",
                "std/pathlib.php",
                "std/random.php",
                "std/re.php",
                "std/sys.php",
                "std/time.php",
                "std/timeit.php",
                "utils/assertions.php",
                "utils/gif.php",
                "utils/png.php",
            ),
        )
        self.assertEqual(
            by_backend["ts"]["pytra_gen_files"],
            (
                "built_in/contains.ts",
                "built_in/io_ops.ts",
                "built_in/iter_ops.ts",
                "built_in/numeric_ops.ts",
                "built_in/predicates.ts",
                "built_in/scalar_ops.ts",
                "built_in/sequence.ts",
                "built_in/string_ops.ts",
                "built_in/type_id.ts",
                "built_in/zip_ops.ts",
                "std/argparse.ts",
                "std/glob.ts",
                "std/json.ts",
                "std/math.ts",
                "std/os.ts",
                "std/os_path.ts",
                "std/pathlib.ts",
                "std/random.ts",
                "std/re.ts",
                "std/sys.ts",
                "std/time.ts",
                "std/timeit.ts",
                "utils/assertions.ts",
                "utils/gif.ts",
                "utils/png.ts",
            ),
        )

    def test_target_inventory_is_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_target_inventory()
        }
        self.assertEqual(
            by_backend["go"],
            {
                "backend": "go",
                "generated_files": (
                    "generated/built_in/contains.go",
                    "generated/built_in/io_ops.go",
                    "generated/built_in/iter_ops.go",
                    "generated/built_in/numeric_ops.go",
                    "generated/built_in/predicates.go",
                    "generated/built_in/scalar_ops.go",
                    "generated/built_in/sequence.go",
                    "generated/built_in/string_ops.go",
                    "generated/built_in/type_id.go",
                    "generated/built_in/zip_ops.go",
                    "generated/std/argparse.go",
                    "generated/std/glob.go",
                    "generated/std/json.go",
                    "generated/std/math.go",
                    "generated/std/os.go",
                    "generated/std/os_path.go",
                    "generated/std/pathlib.go",
                    "generated/std/random.go",
                    "generated/std/re.go",
                    "generated/std/sys.go",
                    "generated/std/time.go",
                    "generated/std/timeit.go",
                    "generated/utils/assertions.go",
                    "generated/utils/gif.go",
                    "generated/utils/png.go",
                ),
                "native_files": ("native/built_in/py_runtime.go",),
                "compat_files": ("pytra/built_in/py_runtime.go",),
            },
        )
        self.assertEqual(
            by_backend["go"]["generated_files"],
            (
                "generated/built_in/contains.go",
                "generated/built_in/io_ops.go",
                "generated/built_in/iter_ops.go",
                "generated/built_in/numeric_ops.go",
                "generated/built_in/predicates.go",
                "generated/built_in/scalar_ops.go",
                "generated/built_in/sequence.go",
                "generated/built_in/string_ops.go",
                "generated/built_in/type_id.go",
                "generated/built_in/zip_ops.go",
                "generated/std/argparse.go",
                "generated/std/glob.go",
                "generated/std/json.go",
                "generated/std/math.go",
                "generated/std/os.go",
                "generated/std/os_path.go",
                "generated/std/pathlib.go",
                "generated/std/random.go",
                "generated/std/re.go",
                "generated/std/sys.go",
                "generated/std/time.go",
                "generated/std/timeit.go",
                "generated/utils/assertions.go",
                "generated/utils/gif.go",
                "generated/utils/png.go",
            ),
        )
        self.assertEqual(
            by_backend["java"]["generated_files"],
            (
                "generated/built_in/contains.java",
                "generated/built_in/io_ops.java",
                "generated/built_in/iter_ops.java",
                "generated/built_in/numeric_ops.java",
                "generated/built_in/predicates.java",
                "generated/built_in/scalar_ops.java",
                "generated/built_in/sequence.java",
                "generated/built_in/string_ops.java",
                "generated/built_in/type_id.java",
                "generated/built_in/zip_ops.java",
                "generated/std/argparse.java",
                "generated/std/glob.java",
                "generated/std/json.java",
                "generated/std/math.java",
                "generated/std/os.java",
                "generated/std/os_path.java",
                "generated/std/pathlib.java",
                "generated/std/random.java",
                "generated/std/re.java",
                "generated/std/sys.java",
                "generated/std/time.java",
                "generated/std/timeit.java",
                "generated/utils/assertions.java",
                "generated/utils/gif.java",
                "generated/utils/png.java",
            ),
        )
        self.assertEqual(
            by_backend["kotlin"]["generated_files"],
            (
                "generated/built_in/contains.kt",
                "generated/built_in/io_ops.kt",
                "generated/built_in/iter_ops.kt",
                "generated/built_in/numeric_ops.kt",
                "generated/built_in/predicates.kt",
                "generated/built_in/scalar_ops.kt",
                "generated/built_in/sequence.kt",
                "generated/built_in/string_ops.kt",
                "generated/built_in/type_id.kt",
                "generated/built_in/zip_ops.kt",
                "generated/std/argparse.kt",
                "generated/std/glob.kt",
                "generated/std/json.kt",
                "generated/std/math.kt",
                "generated/std/os.kt",
                "generated/std/os_path.kt",
                "generated/std/pathlib.kt",
                "generated/std/random.kt",
                "generated/std/re.kt",
                "generated/std/sys.kt",
                "generated/std/time.kt",
                "generated/std/timeit.kt",
                "generated/utils/assertions.kt",
                "generated/utils/gif.kt",
                "generated/utils/image_runtime.kt",
                "generated/utils/png.kt",
            ),
        )
        self.assertEqual(
            by_backend["scala"]["generated_files"],
            (
                "generated/built_in/contains.scala",
                "generated/built_in/io_ops.scala",
                "generated/built_in/iter_ops.scala",
                "generated/built_in/numeric_ops.scala",
                "generated/built_in/predicates.scala",
                "generated/built_in/scalar_ops.scala",
                "generated/built_in/sequence.scala",
                "generated/built_in/string_ops.scala",
                "generated/built_in/type_id.scala",
                "generated/built_in/zip_ops.scala",
                "generated/std/argparse.scala",
                "generated/std/glob.scala",
                "generated/std/json.scala",
                "generated/std/math.scala",
                "generated/std/os.scala",
                "generated/std/os_path.scala",
                "generated/std/pathlib.scala",
                "generated/std/random.scala",
                "generated/std/re.scala",
                "generated/std/sys.scala",
                "generated/std/time.scala",
                "generated/std/timeit.scala",
                "generated/utils/assertions.scala",
                "generated/utils/gif.scala",
                "generated/utils/image_runtime.scala",
                "generated/utils/png.scala",
            ),
        )
        self.assertEqual(
            by_backend["swift"]["generated_files"],
            (
                "generated/built_in/contains.swift",
                "generated/built_in/io_ops.swift",
                "generated/built_in/iter_ops.swift",
                "generated/built_in/numeric_ops.swift",
                "generated/built_in/predicates.swift",
                "generated/built_in/scalar_ops.swift",
                "generated/built_in/sequence.swift",
                "generated/built_in/string_ops.swift",
                "generated/built_in/type_id.swift",
                "generated/built_in/zip_ops.swift",
                "generated/std/argparse.swift",
                "generated/std/glob.swift",
                "generated/std/json.swift",
                "generated/std/math.swift",
                "generated/std/os.swift",
                "generated/std/os_path.swift",
                "generated/std/pathlib.swift",
                "generated/std/random.swift",
                "generated/std/re.swift",
                "generated/std/sys.swift",
                "generated/std/time.swift",
                "generated/std/timeit.swift",
                "generated/utils/assertions.swift",
                "generated/utils/gif.swift",
                "generated/utils/image_runtime.swift",
                "generated/utils/png.swift",
            ),
        )
        self.assertEqual(
            by_backend["nim"]["generated_files"],
            (
                "generated/built_in/contains.nim",
                "generated/built_in/io_ops.nim",
                "generated/built_in/iter_ops.nim",
                "generated/built_in/numeric_ops.nim",
                "generated/built_in/predicates.nim",
                "generated/built_in/scalar_ops.nim",
                "generated/built_in/sequence.nim",
                "generated/built_in/string_ops.nim",
                "generated/built_in/type_id.nim",
                "generated/built_in/zip_ops.nim",
                "generated/std/argparse.nim",
                "generated/std/glob.nim",
                "generated/std/json.nim",
                "generated/std/math.nim",
                "generated/std/os.nim",
                "generated/std/os_path.nim",
                "generated/std/pathlib.nim",
                "generated/std/random.nim",
                "generated/std/re.nim",
                "generated/std/sys.nim",
                "generated/std/time.nim",
                "generated/std/timeit.nim",
                "generated/utils/assertions.nim",
                "generated/utils/gif.nim",
                "generated/utils/image_runtime.nim",
                "generated/utils/png.nim",
            ),
        )
        self.assertEqual(
            by_backend["js"]["generated_files"],
            (
                "generated/built_in/contains.js",
                "generated/built_in/io_ops.js",
                "generated/built_in/iter_ops.js",
                "generated/built_in/numeric_ops.js",
                "generated/built_in/predicates.js",
                "generated/built_in/scalar_ops.js",
                "generated/built_in/sequence.js",
                "generated/built_in/string_ops.js",
                "generated/built_in/type_id.js",
                "generated/built_in/zip_ops.js",
                "generated/std/argparse.js",
                "generated/std/glob.js",
                "generated/std/json.js",
                "generated/std/math.js",
                "generated/std/os.js",
                "generated/std/os_path.js",
                "generated/std/pathlib.js",
                "generated/std/random.js",
                "generated/std/re.js",
                "generated/std/sys.js",
                "generated/std/time.js",
                "generated/std/timeit.js",
                "generated/utils/assertions.js",
                "generated/utils/gif.js",
                "generated/utils/png.js",
            ),
        )
        self.assertEqual(
            by_backend["js"]["compat_files"],
            (
                "pytra/README.md",
                "pytra/py_runtime.js",
                "pytra/std/json.js",
                "pytra/std/math.js",
                "pytra/std/pathlib.js",
                "pytra/std/time.js",
                "pytra/utils/gif.js",
                "pytra/utils/png.js",
            ),
        )
        self.assertEqual(
            by_backend["ts"]["generated_files"],
            (
                "generated/built_in/contains.ts",
                "generated/built_in/io_ops.ts",
                "generated/built_in/iter_ops.ts",
                "generated/built_in/numeric_ops.ts",
                "generated/built_in/predicates.ts",
                "generated/built_in/scalar_ops.ts",
                "generated/built_in/sequence.ts",
                "generated/built_in/string_ops.ts",
                "generated/built_in/type_id.ts",
                "generated/built_in/zip_ops.ts",
                "generated/std/argparse.ts",
                "generated/std/glob.ts",
                "generated/std/json.ts",
                "generated/std/math.ts",
                "generated/std/os.ts",
                "generated/std/os_path.ts",
                "generated/std/pathlib.ts",
                "generated/std/random.ts",
                "generated/std/re.ts",
                "generated/std/sys.ts",
                "generated/std/time.ts",
                "generated/std/timeit.ts",
                "generated/utils/assertions.ts",
                "generated/utils/gif.ts",
                "generated/utils/png.ts",
            ),
        )
        self.assertEqual(
            by_backend["php"],
            {
                "backend": "php",
                "generated_files": (
                    "generated/built_in/contains.php",
                    "generated/built_in/io_ops.php",
                    "generated/built_in/iter_ops.php",
                    "generated/built_in/numeric_ops.php",
                    "generated/built_in/predicates.php",
                    "generated/built_in/scalar_ops.php",
                    "generated/built_in/sequence.php",
                    "generated/built_in/string_ops.php",
                    "generated/built_in/type_id.php",
                    "generated/built_in/zip_ops.php",
                    "generated/std/argparse.php",
                    "generated/std/glob.php",
                    "generated/std/json.php",
                    "generated/std/math.php",
                    "generated/std/os.php",
                    "generated/std/os_path.php",
                    "generated/std/pathlib.php",
                    "generated/std/random.php",
                    "generated/std/re.php",
                    "generated/std/sys.php",
                    "generated/std/time.php",
                    "generated/std/timeit.php",
                    "generated/utils/assertions.php",
                    "generated/utils/gif.php",
                    "generated/utils/png.php",
                ),
                "native_files": ("native/built_in/py_runtime.php", "native/std/time.php"),
                "compat_files": (
                    "pytra/py_runtime.php",
                    "pytra/std/time.php",
                    "pytra/utils/gif.php",
                    "pytra/utils/png.php",
                ),
            },
        )

    def test_module_buckets_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
        }
        self.assertEqual(
            by_backend["go"],
            {
                "backend": "go",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (),
            },
        )
        self.assertEqual(
            by_backend["java"]["generated_modules"],
            (
                "built_in/contains",
                "built_in/io_ops",
                "built_in/iter_ops",
                "built_in/numeric_ops",
                "built_in/predicates",
                "built_in/scalar_ops",
                "built_in/sequence",
                "built_in/string_ops",
                "built_in/type_id",
                "built_in/zip_ops",
                "std/argparse",
                "std/glob",
                "std/json",
                "std/math",
                "std/os",
                "std/os_path",
                "std/pathlib",
                "std/random",
                "std/re",
                "std/sys",
                "std/time",
                "std/timeit",
                "utils/assertions",
                "utils/gif",
                "utils/png",
            ),
        )
        self.assertEqual(by_backend["java"]["blocked_modules"], ())
        self.assertEqual(
            by_backend["kotlin"],
            {
                "backend": "kotlin",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/image_runtime",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (),
            },
        )
        self.assertEqual(
            by_backend["scala"],
            {
                "backend": "scala",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/image_runtime",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (),
            },
        )
        self.assertEqual(
            by_backend["swift"],
            {
                "backend": "swift",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/image_runtime",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (),
            },
        )
        self.assertEqual(
            by_backend["nim"],
            {
                "backend": "nim",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/image_runtime",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (),
            },
        )
        self.assertEqual(
            by_backend["js"]["blocked_modules"],
            SCRIPT_FAMILY_MISSING_COMPARE_MODULES,
        )
        self.assertEqual(
            by_backend["php"],
            {
                "backend": "php",
                "generated_modules": (
                    "built_in/contains",
                    "built_in/io_ops",
                    "built_in/iter_ops",
                    "built_in/numeric_ops",
                    "built_in/predicates",
                    "built_in/scalar_ops",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "built_in/zip_ops",
                    "std/argparse",
                    "std/glob",
                    "std/json",
                    "std/math",
                    "std/os",
                    "std/os_path",
                    "std/pathlib",
                    "std/random",
                    "std/re",
                    "std/sys",
                    "std/time",
                    "std/timeit",
                    "utils/assertions",
                    "utils/gif",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime", "std/time"),
                "compat_modules": ("built_in/py_runtime", "std/time", "utils/gif", "utils/png"),
                "blocked_modules": (),
            },
        )

    def test_wave_b_blocked_reasons_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_blocked_reasons()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "missing_compare_lane_modules": SCRIPT_FAMILY_MISSING_COMPARE_MODULES,
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (),
                },
                "ts": {
                    "backend": "ts",
                    "missing_compare_lane_modules": SCRIPT_FAMILY_MISSING_COMPARE_MODULES,
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (),
                },
                "lua": {
                    "backend": "lua",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                },
                "ruby": {
                    "backend": "ruby",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                },
                "php": {
                    "backend": "php",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (),
                },
            },
        )

    def test_wave_b_generated_compare_end_state_is_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_generated_compare()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "materialized_compare_modules": SCRIPT_FAMILY_PARTIAL_GENERATED_COMPARE,
                    "helper_artifact_modules": (),
                },
                "ts": {
                    "backend": "ts",
                    "materialized_compare_modules": SCRIPT_FAMILY_PARTIAL_GENERATED_COMPARE,
                    "helper_artifact_modules": (),
                },
                "lua": {
                    "backend": "lua",
                    "materialized_compare_modules": (),
                    "helper_artifact_modules": (
                        "utils/gif_helper",
                        "utils/image_runtime",
                        "utils/png_helper",
                    ),
                },
                "ruby": {
                    "backend": "ruby",
                    "materialized_compare_modules": (),
                    "helper_artifact_modules": (
                        "utils/gif_helper",
                        "utils/image_runtime",
                        "utils/png_helper",
                    ),
                },
                "php": {
                    "backend": "php",
                    "materialized_compare_modules": SCRIPT_FAMILY_COMPARE_BASELINE,
                    "helper_artifact_modules": (),
                },
            },
        )

    def test_wave_b_native_residuals_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residuals()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "substrate_modules": ("built_in/py_runtime", "std/math", "std/pathlib", "std/time"),
                    "compare_residual_modules": (),
                },
                "ts": {
                    "backend": "ts",
                    "substrate_modules": ("built_in/py_runtime", "std/math", "std/pathlib", "std/time"),
                    "compare_residual_modules": (),
                },
                "lua": {
                    "backend": "lua",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "ruby": {
                    "backend": "ruby",
                    "substrate_modules": ("built_in/py_runtime",),
                    "compare_residual_modules": (),
                },
                "php": {
                    "backend": "php",
                    "substrate_modules": ("built_in/py_runtime", "std/time"),
                    "compare_residual_modules": (),
                },
            },
        )

    def test_wave_b_native_residual_files_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residual_files()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "substrate_files": ("built_in/py_runtime.js", "std/math.js", "std/pathlib.js", "std/time.js"),
                    "compare_residual_files": (),
                },
                "ts": {
                    "backend": "ts",
                    "substrate_files": ("built_in/py_runtime.ts", "std/math.ts", "std/pathlib.ts", "std/time.ts"),
                    "compare_residual_files": (),
                },
                "lua": {
                    "backend": "lua",
                    "substrate_files": ("built_in/py_runtime.lua",),
                    "compare_residual_files": (),
                },
                "ruby": {
                    "backend": "ruby",
                    "substrate_files": ("built_in/py_runtime.rb",),
                    "compare_residual_files": (),
                },
                "php": {
                    "backend": "php",
                    "substrate_files": ("built_in/py_runtime.php", "std/time.php"),
                    "compare_residual_files": (),
                },
            },
        )

    def test_wave_b_compat_modules_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_compat()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "substrate_shim_modules": ("built_in/py_runtime",),
                    "generated_compare_shim_modules": (
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
                },
                "ts": {
                    "backend": "ts",
                    "substrate_shim_modules": ("built_in/py_runtime",),
                    "generated_compare_shim_modules": (
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
                },
                "lua": {
                    "backend": "lua",
                    "substrate_shim_modules": ("built_in/py_runtime",),
                    "generated_compare_shim_modules": (),
                },
                "ruby": {
                    "backend": "ruby",
                    "substrate_shim_modules": ("built_in/py_runtime",),
                    "generated_compare_shim_modules": (),
                },
                "php": {
                    "backend": "php",
                    "substrate_shim_modules": ("built_in/py_runtime",),
                    "generated_compare_shim_modules": ("std/time", "utils/gif", "utils/png"),
                },
            },
        )

    def test_wave_b_compat_files_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry
            for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_compat_files()
        }
        self.assertEqual(
            by_backend,
            {
                "js": {
                    "backend": "js",
                    "substrate_shim_files": ("py_runtime.js",),
                    "generated_compare_shim_files": (
                        "std/json.js",
                        "std/math.js",
                        "std/pathlib.js",
                        "std/time.js",
                        "utils/gif.js",
                        "utils/png.js",
                    ),
                    "ancillary_files": ("README.md",),
                },
                "ts": {
                    "backend": "ts",
                    "substrate_shim_files": ("py_runtime.ts",),
                    "generated_compare_shim_files": (
                        "std/json.ts",
                        "std/math.ts",
                        "std/pathlib.ts",
                        "std/time.ts",
                        "utils/gif.ts",
                        "utils/png.ts",
                    ),
                    "ancillary_files": ("README.md",),
                },
                "lua": {
                    "backend": "lua",
                    "substrate_shim_files": ("built_in/py_runtime.lua",),
                    "generated_compare_shim_files": (),
                    "ancillary_files": (),
                },
                "ruby": {
                    "backend": "ruby",
                    "substrate_shim_files": ("built_in/py_runtime.rb",),
                    "generated_compare_shim_files": (),
                    "ancillary_files": (),
                },
                "php": {
                    "backend": "php",
                    "substrate_shim_files": ("py_runtime.php",),
                    "generated_compare_shim_files": ("std/time.php", "utils/gif.php", "utils/png.php"),
                    "ancillary_files": (),
                },
            },
        )


if __name__ == "__main__":
    unittest.main()

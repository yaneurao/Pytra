from __future__ import annotations

import unittest

from src.toolchain.compiler import noncpp_runtime_layout_rollout_remaining_contract as contract_mod
from tools import check_noncpp_runtime_layout_rollout_remaining_contract as check_mod


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
                    "runtime/java/generated/utils/png.java",
                    "runtime/java/generated/utils/gif.java",
                    "runtime/java/generated/std/time.java",
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
                        "utils/gif.go",
                        "utils/png.go",
                    ),
                },
                {
                    "backend": "java",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "built_in/contains.java",
                        "std/json.java",
                        "std/math.java",
                        "std/pathlib.java",
                        "std/time.java",
                        "utils/gif.java",
                        "utils/png.java",
                    ),
                },
                {
                    "backend": "kotlin",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.kt",
                        "utils/image_runtime.kt",
                        "utils/png_helper.kt",
                    ),
                },
                {
                    "backend": "scala",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.scala",
                        "utils/image_runtime.scala",
                        "utils/png_helper.scala",
                    ),
                },
                {
                    "backend": "swift",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.swift",
                        "utils/image_runtime.swift",
                        "utils/png_helper.swift",
                    ),
                },
                {
                    "backend": "nim",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.nim",
                        "utils/image_runtime.nim",
                        "utils/png_helper.nim",
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
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.kt",
                        "utils/image_runtime.kt",
                        "utils/png_helper.kt",
                    ),
                },
                {
                    "backend": "scala",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.scala",
                        "utils/image_runtime.scala",
                        "utils/png_helper.scala",
                    ),
                },
                {
                    "backend": "swift",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.swift",
                        "utils/image_runtime.swift",
                        "utils/png_helper.swift",
                    ),
                },
                {
                    "backend": "nim",
                    "smoke_kind": "source_guard",
                    "smoke_targets": (
                        "utils/gif_helper.nim",
                        "utils/image_runtime.nim",
                        "utils/png_helper.nim",
                    ),
                },
            ),
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
                "std/json",
                "std/math",
                "std/pathlib",
                "std/time",
                "utils/gif",
                "utils/png",
            ),
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
                    "built_in/scalar_ops.go",
                    "built_in/zip_ops.go",
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
                "built_in/scalar_ops.java",
                "built_in/zip_ops.java",
                "std/json.java",
                "std/math.java",
                "std/pathlib.java",
                "std/time.java",
                "utils/gif.java",
                "utils/png.java",
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
                "std/json.js",
                "std/math.js",
                "std/pathlib.js",
                "std/time.js",
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
                "std/json.php",
                "std/math.php",
                "std/pathlib.php",
                "std/time.php",
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
                "std/json.ts",
                "std/math.ts",
                "std/pathlib.ts",
                "std/time.ts",
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
                    "generated/built_in/scalar_ops.go",
                    "generated/built_in/zip_ops.go",
                    "generated/utils/gif.go",
                    "generated/utils/png.go",
                ),
                "native_files": ("native/built_in/py_runtime.go",),
                "compat_files": ("pytra/built_in/py_runtime.go",),
            },
        )
        self.assertEqual(
            by_backend["java"]["generated_files"],
            (
                "generated/built_in/contains.java",
                "generated/built_in/io_ops.java",
                "generated/built_in/iter_ops.java",
                "generated/built_in/numeric_ops.java",
                "generated/built_in/scalar_ops.java",
                "generated/built_in/zip_ops.java",
                "generated/std/json.java",
                "generated/std/math.java",
                "generated/std/pathlib.java",
                "generated/std/time.java",
                "generated/utils/gif.java",
                "generated/utils/png.java",
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
                "generated/std/json.ts",
                "generated/std/math.ts",
                "generated/std/pathlib.ts",
                "generated/std/time.ts",
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
                    "generated/std/json.php",
                    "generated/std/math.php",
                    "generated/std/pathlib.php",
                    "generated/std/time.php",
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
                    "built_in/scalar_ops",
                    "built_in/zip_ops",
                    "utils/gif",
                    "utils/png",
                ),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": (
                    "built_in/predicates",
                    "built_in/sequence",
                    "built_in/string_ops",
                    "built_in/type_id",
                    "std/json",
                    "std/math",
                    "std/pathlib",
                    "std/time",
                ),
            },
        )
        self.assertEqual(
            by_backend["java"]["generated_modules"],
            (
                "built_in/contains",
                "built_in/io_ops",
                "built_in/iter_ops",
                "built_in/numeric_ops",
                "built_in/scalar_ops",
                "built_in/zip_ops",
                "std/json",
                "std/math",
                "std/pathlib",
                "std/time",
                "utils/gif",
                "utils/png",
            ),
        )
        self.assertEqual(
            by_backend["java"]["blocked_modules"],
            ("built_in/predicates", "built_in/sequence", "built_in/string_ops", "built_in/type_id"),
        )
        self.assertEqual(
            by_backend["js"]["blocked_modules"],
            (),
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
                    "std/json",
                    "std/math",
                    "std/pathlib",
                    "std/time",
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
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (),
                },
                "ts": {
                    "backend": "ts",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (),
                },
                "lua": {
                    "backend": "lua",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (
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
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
                },
                "ruby": {
                    "backend": "ruby",
                    "missing_compare_lane_modules": (),
                    "native_compare_residual_modules": (),
                    "helper_shaped_compare_gap_modules": (
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
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
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
                    "materialized_compare_modules": (
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
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
                    "helper_artifact_modules": (),
                },
                "ts": {
                    "backend": "ts",
                    "materialized_compare_modules": (
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
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
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
                    "materialized_compare_modules": (
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
                        "std/json",
                        "std/math",
                        "std/pathlib",
                        "std/time",
                        "utils/gif",
                        "utils/png",
                    ),
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

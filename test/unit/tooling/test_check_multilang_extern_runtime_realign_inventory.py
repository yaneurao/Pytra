from __future__ import annotations

import unittest

from src.toolchain.compiler import multilang_extern_runtime_realign_inventory as inventory_mod
from tools import check_multilang_extern_runtime_realign_inventory as check_mod


class CheckMultilangExternRuntimeRealignInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_native_owner_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_native_owner_issues(), [])

    def test_emitter_hardcode_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_emitter_hardcode_issues(), [])

    def test_generated_drift_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_generated_drift_issues(), [])

    def test_representative_smoke_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_representative_smoke_issues(), [])

    def test_module_order_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.MODULE_ORDER,
            (
                "std/math",
                "std/time",
                "std/os",
                "std/os_path",
                "std/sys",
                "std/glob",
                "built_in/io_ops",
                "built_in/scalar_ops",
            ),
        )

    def test_bucket_order_is_fixed(self) -> None:
        self.assertEqual(inventory_mod.BUCKET_ORDER, ("stdlib", "built_in"))

    def test_noncpp_ownership_mode_order_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.NONCPP_OWNERSHIP_MODE_ORDER,
            ("native_owner", "generated_compare_only"),
        )

    def test_inventory_ids_match_fixed_order(self) -> None:
        self.assertEqual(
            tuple(row["module_id"] for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()),
            inventory_mod.MODULE_ORDER,
        )

    def test_math_inventory_row_is_fixed(self) -> None:
        row = inventory_mod.iter_multilang_extern_runtime_realign_inventory()[0]
        self.assertEqual(row["module_id"], "std/math")
        self.assertEqual(
            row["manifest_postprocess_targets"],
            (
                "rs:rs_std_native_owner_wrapper",
                "cs:cs_std_native_owner_wrapper",
                "go:go_program_to_library",
                "java:java_std_native_owner_wrapper",
                "kotlin:kotlin_program_to_library",
                "scala:scala_program_to_library",
                "swift:swift_program_to_library",
                "js:js_std_native_owner_wrapper",
                "ts:ts_std_native_owner_wrapper",
                "php:php_std_native_owner_wrapper",
            ),
        )
        self.assertEqual(row["cpp_native_owner_paths"], ("src/runtime/cpp/native/std/math.cpp",))
        self.assertEqual(
            row["noncpp_native_owner_paths"],
            (
                "src/runtime/rs/native/std/math_native.rs",
                "src/runtime/cs/native/std/math_native.cs",
                "src/runtime/java/native/std/math_native.java",
                "src/runtime/js/native/std/math_native.js",
                "src/runtime/ts/native/std/math_native.ts",
                "src/runtime/php/native/std/math_native.php",
            ),
        )
        self.assertEqual(row["noncpp_ownership_mode"], "native_owner")
        self.assertEqual(row["accepted_generated_compare_residual_targets"], ("nim",))
        self.assertEqual(
            row["representative_smoke_needles"],
            (
                (
                    "test/unit/backends/cs/test_py2cs_smoke.py",
                    "def test_representative_math_import_fixture_transpiles",
                ),
                (
                    "test/unit/backends/go/test_py2go_smoke.py",
                    "def test_go_native_emitter_routes_math_calls_via_runtime_helpers",
                ),
                (
                    "test/unit/backends/java/test_py2java_smoke.py",
                    "def test_java_generated_math_runtime_owner_is_live_wrapper_shaped",
                ),
                (
                    "test/unit/backends/php/test_py2php_smoke.py",
                    "def test_php_generated_math_runtime_owner_is_live_wrapper_shaped",
                ),
                (
                    "test/unit/backends/rs/test_py2rs_smoke.py",
                    "def test_runtime_scaffold_exposes_pytra_std_time_and_math",
                ),
            ),
        )

    def test_time_inventory_noncpp_native_seam_is_fixed(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(
            by_id["std/time"]["manifest_postprocess_targets"],
            (
                "rs:rs_std_native_owner_wrapper",
                "cs:cs_std_native_owner_wrapper",
                "go:go_program_to_library",
                "java:java_std_native_owner_wrapper",
                "kotlin:kotlin_program_to_library",
                "scala:scala_program_to_library",
                "swift:swift_program_to_library",
                "js:js_std_native_owner_wrapper",
                "ts:ts_std_native_owner_wrapper",
                "php:php_std_native_owner_wrapper",
            ),
        )
        self.assertEqual(
            by_id["std/time"]["noncpp_native_owner_paths"],
            (
                "src/runtime/rs/native/std/time_native.rs",
                "src/runtime/cs/native/std/time_native.cs",
                "src/runtime/java/native/std/time_native.java",
                "src/runtime/js/native/std/time_native.js",
                "src/runtime/ts/native/std/time_native.ts",
                "src/runtime/php/native/std/time_native.php",
            ),
        )
        self.assertEqual(by_id["std/time"]["noncpp_ownership_mode"], "native_owner")
        self.assertEqual(by_id["std/time"]["accepted_generated_compare_residual_targets"], ("nim",))
        self.assertEqual(
            by_id["std/time"]["representative_smoke_needles"],
            (
                (
                    "test/unit/backends/cs/test_py2cs_smoke.py",
                    "def test_representative_time_import_fixture_transpiles",
                ),
                (
                    "test/unit/backends/java/test_py2java_smoke.py",
                    "def test_java_native_emitter_routes_perf_counter_via_runtime_helper",
                ),
                (
                    "test/unit/backends/php/test_py2php_smoke.py",
                    "def test_php_generated_time_runtime_owner_is_live_wrapper_shaped",
                ),
                (
                    "test/unit/backends/rs/test_py2rs_smoke.py",
                    "def test_generated_time_and_math_runtime_hook_modules_compile_with_scaffold",
                ),
            ),
        )

    def test_math_inventory_noncpp_native_seam_is_fixed(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(
            by_id["std/math"]["noncpp_native_owner_paths"],
            (
                "src/runtime/rs/native/std/math_native.rs",
                "src/runtime/cs/native/std/math_native.cs",
                "src/runtime/java/native/std/math_native.java",
                "src/runtime/js/native/std/math_native.js",
                "src/runtime/ts/native/std/math_native.ts",
                "src/runtime/php/native/std/math_native.php",
            ),
        )
        self.assertEqual(by_id["std/math"]["noncpp_ownership_mode"], "native_owner")
        self.assertEqual(by_id["std/math"]["emitter_hardcode_needles"], ())

    def test_compare_only_rows_and_residual_targets_are_fixed(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(by_id["std/os"]["noncpp_ownership_mode"], "generated_compare_only")
        self.assertEqual(by_id["std/os"]["accepted_generated_compare_residual_targets"], ("rs",))
        self.assertEqual(by_id["std/os_path"]["noncpp_ownership_mode"], "generated_compare_only")
        self.assertEqual(by_id["std/os_path"]["accepted_generated_compare_residual_targets"], ("rs",))
        self.assertEqual(by_id["std/glob"]["noncpp_ownership_mode"], "native_owner")
        self.assertEqual(by_id["std/glob"]["accepted_generated_compare_residual_targets"], ("rs",))
        self.assertEqual(by_id["built_in/io_ops"]["noncpp_ownership_mode"], "generated_compare_only")
        self.assertEqual(by_id["built_in/io_ops"]["accepted_generated_compare_residual_targets"], ())
        self.assertEqual(by_id["built_in/scalar_ops"]["noncpp_ownership_mode"], "generated_compare_only")
        self.assertEqual(by_id["built_in/scalar_ops"]["accepted_generated_compare_residual_targets"], ())

    def test_time_inventory_has_no_module_specific_hardcodes(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(by_id["std/time"]["emitter_hardcode_needles"], ())

    def test_lua_stdlib_inventory_has_no_module_specific_hardcodes(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        for module_id in ("std/os", "std/os_path", "std/sys", "std/glob"):
            with self.subTest(module_id=module_id):
                self.assertEqual(by_id[module_id]["emitter_hardcode_needles"], ())

    def test_lua_stdlib_inventory_rows_have_no_module_specific_hardcodes(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(by_id["std/os"]["emitter_hardcode_needles"], ())
        self.assertEqual(by_id["std/os_path"]["emitter_hardcode_needles"], ())
        self.assertEqual(by_id["std/sys"]["emitter_hardcode_needles"], ())
        self.assertEqual(by_id["std/glob"]["emitter_hardcode_needles"], ())

    def test_sys_inventory_uses_js_ts_native_owner_wrappers(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(
            by_id["std/sys"]["manifest_postprocess_targets"],
            (
                "go:go_program_to_library",
                "kotlin:kotlin_program_to_library",
                "scala:scala_program_to_library",
                "swift:swift_program_to_library",
                "js:js_std_native_owner_wrapper",
                "ts:ts_std_native_owner_wrapper",
                "php:php_program_to_library",
            ),
        )
        self.assertEqual(
            by_id["std/sys"]["noncpp_native_owner_paths"],
            (
                "src/runtime/js/native/std/sys_native.js",
                "src/runtime/ts/native/std/sys_native.ts",
            ),
        )
        self.assertEqual(by_id["std/sys"]["noncpp_ownership_mode"], "native_owner")
        self.assertEqual(by_id["std/sys"]["accepted_generated_compare_residual_targets"], ())
        self.assertEqual(by_id["std/sys"]["generated_drift_needles"], ())

    def test_io_ops_inventory_has_no_module_specific_hardcodes(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(by_id["built_in/io_ops"]["emitter_hardcode_needles"], ())
        self.assertEqual(by_id["built_in/io_ops"]["generated_drift_needles"], ())
        self.assertEqual(
            by_id["built_in/io_ops"]["representative_smoke_needles"],
            (
                (
                    "test/unit/backends/go/test_py2go_smoke.py",
                    "def test_go_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                ),
                (
                    "test/unit/backends/kotlin/test_py2kotlin_smoke.py",
                    "def test_kotlin_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()

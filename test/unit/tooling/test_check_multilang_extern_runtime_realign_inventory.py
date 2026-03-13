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
                "rs:rs_std_math_live_wrapper",
                "cs:cs_std_math_live_wrapper",
                "go:go_program_to_library",
                "java:java_std_math_live_wrapper",
                "kotlin:kotlin_program_to_library",
                "scala:scala_program_to_library",
                "swift:swift_program_to_library",
                "js:js_std_math_live_wrapper",
                "ts:ts_std_math_live_wrapper",
                "php:php_std_math_live_wrapper",
            ),
        )
        self.assertEqual(row["cpp_native_owner_paths"], ("src/runtime/cpp/native/std/math.cpp",))

    def test_time_inventory_noncpp_native_seam_is_fixed(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertIn(
            "cs:cs_std_native_owner_wrapper",
            by_id["std/time"]["manifest_postprocess_targets"],
        )
        self.assertEqual(
            by_id["std/time"]["noncpp_native_owner_paths"],
            ("src/runtime/cs/native/std/time_native.cs",),
        )

    def test_math_inventory_noncpp_native_seam_is_fixed(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(
            by_id["std/math"]["noncpp_native_owner_paths"],
            ("src/runtime/cs/native/std/math_native.cs",),
        )

    def test_io_ops_inventory_has_no_module_specific_hardcodes(self) -> None:
        by_id = {
            row["module_id"]: row
            for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory()
        }
        self.assertEqual(by_id["built_in/io_ops"]["emitter_hardcode_needles"], ())
        self.assertEqual(by_id["built_in/io_ops"]["generated_drift_needles"], ())


if __name__ == "__main__":
    unittest.main()

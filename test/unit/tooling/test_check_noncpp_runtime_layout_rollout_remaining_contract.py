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

    def test_module_bucket_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_module_bucket_issues(), [])

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

    def test_target_root_taxonomy_is_fixed(self) -> None:
        for entry in contract_mod.iter_remaining_noncpp_runtime_layout():
            self.assertEqual(entry["target_roots"], ("generated", "native", "pytra"))

    def test_representative_lane_mappings_are_fixed(self) -> None:
        by_backend = {
            entry["backend"]: entry["lane_mappings"]
            for entry in contract_mod.iter_remaining_noncpp_runtime_layout()
        }
        self.assertIn(
            {
                "current_prefix": "src/runtime/go/pytra/py_runtime.go",
                "target_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "ownership": "compat",
                "rationale": "The public Go shim is still flat today and will be bucketed under pytra/built_in during rollout.",
            },
            by_backend["go"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/js/pytra/time.js",
                "target_prefix": "src/runtime/js/pytra/std/time.js",
                "ownership": "compat",
                "rationale": "Flat JS std shim files will be bucketed under pytra/std during rollout.",
            },
            by_backend["js"],
        )
        self.assertIn(
            {
                "current_prefix": "src/runtime/php/pytra-gen/runtime/",
                "target_prefix": "src/runtime/php/generated/utils/",
                "ownership": "generated",
                "rationale": "PHP still uses a legacy runtime bucket for SoT-generated image helpers; rollout renames it to generated/utils.",
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
                "pytra_gen_files": ("utils/gif.go", "utils/png.go"),
                "pytra_files": ("py_runtime.go",),
            },
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
                "generated_files": ("generated/utils/gif.go", "generated/utils/png.go"),
                "native_files": ("native/built_in/py_runtime.go",),
                "compat_files": ("pytra/built_in/py_runtime.go",),
            },
        )
        self.assertEqual(
            by_backend["js"]["compat_files"],
            (
                "pytra/README.md",
                "pytra/py_runtime.js",
                "pytra/std/math.js",
                "pytra/std/pathlib.js",
                "pytra/std/time.js",
                "pytra/utils/gif.js",
                "pytra/utils/png.js",
            ),
        )
        self.assertEqual(
            by_backend["php"],
            {
                "backend": "php",
                "generated_files": ("generated/utils/gif.php", "generated/utils/png.php"),
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
                "generated_modules": ("utils/gif", "utils/png"),
                "native_modules": ("built_in/py_runtime",),
                "compat_modules": ("built_in/py_runtime",),
                "blocked_modules": ("std/json", "std/math", "std/pathlib", "std/time"),
            },
        )
        self.assertEqual(
            by_backend["java"]["generated_modules"],
            ("std/json", "std/math", "std/pathlib", "std/time", "utils/gif", "utils/png"),
        )
        self.assertEqual(
            by_backend["js"]["blocked_modules"],
            ("std/json",),
        )
        self.assertEqual(
            by_backend["php"],
            {
                "backend": "php",
                "generated_modules": ("utils/gif", "utils/png"),
                "native_modules": ("built_in/py_runtime", "std/time"),
                "compat_modules": ("built_in/py_runtime", "std/time", "utils/gif", "utils/png"),
                "blocked_modules": ("std/json", "std/math", "std/pathlib"),
            },
        )


if __name__ == "__main__":
    unittest.main()

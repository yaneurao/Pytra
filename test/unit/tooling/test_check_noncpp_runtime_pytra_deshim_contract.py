from __future__ import annotations

import unittest

from src.toolchain.compiler import noncpp_runtime_pytra_deshim_contract as contract_mod
from tools import check_noncpp_runtime_pytra_deshim_contract as check_mod


class CheckNonCppRuntimePytraDeshimContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_blocker_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_blocker_issues(), [])

    def test_doc_policy_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_doc_policy_issues(), [])

    def test_backend_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_pytra_deshim_backend_order(),
            ("rs", "go", "java", "kotlin", "scala", "swift", "nim", "js", "ts", "lua", "ruby", "php"),
        )

    def test_bucket_order_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_pytra_deshim_bucket_order(),
            ("direct_load_smoke", "runtime_shim_writer", "contract_allowlist", "selfhost_stage"),
        )

    def test_current_directory_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_pytra_deshim_current_dirs(),
            (
                "src/runtime/js/pytra",
                "src/runtime/lua/pytra",
                "src/runtime/php/pytra",
                "src/runtime/ruby/pytra",
                "src/runtime/ts/pytra",
            ),
        )

    def test_current_file_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_pytra_deshim_current_files(),
            (
                "src/runtime/js/pytra/README.md",
                "src/runtime/js/pytra/py_runtime.js",
                "src/runtime/js/pytra/std/json.js",
                "src/runtime/js/pytra/std/math.js",
                "src/runtime/js/pytra/std/pathlib.js",
                "src/runtime/js/pytra/std/time.js",
                "src/runtime/js/pytra/utils/gif.js",
                "src/runtime/js/pytra/utils/png.js",
                "src/runtime/lua/pytra/built_in/py_runtime.lua",
                "src/runtime/php/pytra/py_runtime.php",
                "src/runtime/php/pytra/std/time.php",
                "src/runtime/php/pytra/utils/gif.php",
                "src/runtime/php/pytra/utils/png.php",
                "src/runtime/ruby/pytra/built_in/py_runtime.rb",
                "src/runtime/ts/pytra/README.md",
                "src/runtime/ts/pytra/py_runtime.ts",
                "src/runtime/ts/pytra/std/json.ts",
                "src/runtime/ts/pytra/std/math.ts",
                "src/runtime/ts/pytra/std/pathlib.ts",
                "src/runtime/ts/pytra/std/time.ts",
                "src/runtime/ts/pytra/utils/gif.ts",
                "src/runtime/ts/pytra/utils/png.ts",
            ),
        )

    def test_backend_mapping_inventory_is_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["backend"] for entry in contract_mod.iter_noncpp_pytra_deshim_backends()),
            contract_mod.iter_noncpp_pytra_deshim_backend_order(),
        )
        self.assertTrue(
            all(entry["target_roots"] == ("generated", "native") for entry in contract_mod.iter_noncpp_pytra_deshim_backends())
        )
        self.assertTrue(
            all(entry["target_policy"].startswith("delete_target") for entry in contract_mod.iter_noncpp_pytra_deshim_backends())
        )

    def test_blocker_baseline_contains_expected_categories(self) -> None:
        blockers = contract_mod.iter_noncpp_pytra_deshim_blockers()
        self.assertFalse(any(entry["backend"] == "js" for entry in blockers))
        self.assertFalse(any(entry["backend"] == "ts" for entry in blockers))
        self.assertNotIn(
            {
                "backend": "rs",
                "bucket": "contract_allowlist",
                "path": "src/toolchain/compiler/noncpp_runtime_layout_contract.py",
                "needles": ("RS_PYTRA_COMPAT_ALLOWLIST_V1", "src/runtime/rs/pytra/built_in/py_runtime.rs"),
                "rationale": "Rust still has an explicit compat allowlist in the live non-C++ runtime layout contract.",
            },
            blockers,
        )
        self.assertFalse(
            any(
                entry["backend"] == "go" and entry["bucket"] == "contract_allowlist"
                for entry in blockers
            )
        )
        self.assertIn(
            {
                "backend": "php",
                "bucket": "runtime_shim_writer",
                "path": "tools/gen_runtime_from_manifest.py",
                "needles": ("require_once __DIR__ . '/pytra/py_runtime.php';",),
                "rationale": "PHP runtime generation still knows how to emit a repo-tree pytra shim include.",
            },
            blockers,
        )

    def test_doc_policy_baseline_contains_expected_entries(self) -> None:
        blockers = contract_mod.iter_noncpp_pytra_deshim_blockers()
        self.assertEqual(
            contract_mod.iter_noncpp_pytra_deshim_doc_policy(),
            (
                {
                    "path": "docs/ja/spec/spec-folder.md",
                    "needles": (
                        "非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` は互換 lane ではなく delete target とする。",
                        "repo 正本 layout は `src/runtime/<lang>/{generated,native}/` のみを許可する。",
                    ),
                },
                {
                    "path": "docs/en/spec/spec-folder.md",
                    "needles": (
                        "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` is a delete target, not a compatibility lane.",
                        "The canonical repo layout allows only `src/runtime/<lang>/{generated,native}/` as live runtime roots.",
                    ),
                },
                {
                    "path": "docs/ja/spec/spec-dev.md",
                    "needles": (
                        "non-C++ / non-C# backend の checked-in `src/runtime/<lang>/pytra/**` は delete target debt とする。",
                    ),
                },
                {
                    "path": "docs/en/spec/spec-dev.md",
                    "needles": (
                        "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` is delete-target debt only.",
                    ),
                },
                {
                    "path": "docs/ja/spec/spec-java-native-backend.md",
                    "needles": (
                        "実行時依存は Java runtime（repo 正本は `src/runtime/java/{generated,native}/`）へ収束し",
                        "`src/runtime/java/{generated,native}/` 配下の Java runtime API。",
                    ),
                },
                {
                    "path": "docs/en/spec/spec-java-native-backend.md",
                    "needles": (
                        "Runtime dependency converges to Java runtime (the canonical repo roots are `src/runtime/java/{generated,native}/`)",
                        "Java runtime APIs under `src/runtime/java/{generated,native}/`;",
                    ),
                },
                {
                    "path": "docs/ja/spec/spec-lua-native-backend.md",
                    "needles": (
                        "`src/runtime/lua/{generated,native}/` 配下の Lua runtime API（checked-in `src/runtime/lua/pytra/**` は delete target debt）",
                    ),
                },
                {
                    "path": "docs/en/spec/spec-lua-native-backend.md",
                    "needles": (
                        "Lua runtime API under `src/runtime/lua/{generated,native}/` (checked-in `src/runtime/lua/pytra/**` is delete-target debt only)",
                    ),
                },
                {
                    "path": "docs/ja/spec/spec-gsk-native-backend.md",
                    "needles": (
                        "Go: `src/runtime/go/{generated,native}/` + Go 標準ライブラリ。",
                        "Swift: `src/runtime/swift/{generated,native}/` + Swift 標準ライブラリ。",
                        "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM 標準ライブラリ。",
                    ),
                },
                {
                    "path": "docs/en/spec/spec-gsk-native-backend.md",
                    "needles": (
                        "Go: `src/runtime/go/{generated,native}/` + Go standard library.",
                        "Swift: `src/runtime/swift/{generated,native}/` + Swift standard library.",
                        "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM standard library.",
                    ),
                },
            ),
        )
        self.assertIn(
            {
                "backend": "php",
                "bucket": "runtime_shim_writer",
                "path": "tools/gen_runtime_from_manifest.py",
                "needles": ("require_once __DIR__ . '/pytra/py_runtime.php';",),
                "rationale": "PHP runtime generation still knows how to emit a repo-tree pytra shim include.",
            },
            blockers,
        )


if __name__ == "__main__":
    unittest.main()

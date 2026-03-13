from __future__ import annotations

import unittest

from src.toolchain.compiler import (
    noncpp_runtime_generated_cpp_baseline_contract as contract_mod,
)
from tools import check_noncpp_runtime_generated_cpp_baseline_contract as check_mod


class CheckNonCppRuntimeGeneratedCppBaselineContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])
        self.assertEqual(check_mod._collect_policy_wording_issues(), [])

    def test_bucket_order_matches_entries(self) -> None:
        entries = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        self.assertEqual(
            tuple(entry["bucket"] for entry in entries),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_bucket_order(),
        )

    def test_flattened_modules_match_entries(self) -> None:
        entries = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        expected = tuple(
            f"{entry['bucket']}/{module}"
            for entry in entries
            for module in entry["modules"]
        )
        self.assertEqual(expected, contract_mod.iter_noncpp_runtime_generated_cpp_baseline_modules())

    def test_policy_doc_inventories_are_fixed(self) -> None:
        self.assertEqual(
            tuple(entry["path"] for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_policy_files()),
            (
                "src/toolchain/compiler/noncpp_runtime_layout_contract.py",
                "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
                "tools/check_noncpp_runtime_layout_contract.py",
                "tools/check_noncpp_runtime_layout_rollout_remaining_contract.py",
            ),
        )
        self.assertEqual(
            tuple(entry["path"] for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_active_policy_docs()),
            (
                "docs/ja/spec/spec-runtime.md",
                "docs/en/spec/spec-runtime.md",
                "docs/ja/spec/spec-tools.md",
                "docs/en/spec/spec-tools.md",
            ),
        )
        self.assertEqual(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends(),
            ("cs", "go", "java", "rs", "swift", "nim", "kotlin", "scala", "js", "ts", "lua", "ruby", "php"),
        )
        self.assertEqual(
            tuple(
                entry["backend"]
                for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_local_runtime_file_inventory()
            ),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends(),
        )
        self.assertEqual(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_inventory(),
            (
                {"backend": "cs", "helper_artifact_modules": ()},
                {"backend": "go", "helper_artifact_modules": ()},
                {"backend": "java", "helper_artifact_modules": ()},
                {"backend": "rs", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "swift", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "nim", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "kotlin", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "scala", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "js", "helper_artifact_modules": ()},
                {"backend": "ts", "helper_artifact_modules": ()},
                {"backend": "lua", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "ruby", "helper_artifact_modules": ("utils/image_runtime",)},
                {"backend": "php", "helper_artifact_modules": ()},
            ),
        )

    def test_legacy_state_buckets_match_runtime_contracts(self) -> None:
        self.assertEqual(
            check_mod._collect_runtime_layout_legacy_state_buckets(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_state_buckets(),
        )

    def test_helper_artifact_overlap_is_empty(self) -> None:
        self.assertEqual(
            check_mod._collect_helper_artifact_overlap_modules(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_overlap(),
        )
        self.assertEqual(
            check_mod._collect_helper_artifact_inventory(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_inventory(),
        )
        self.assertEqual(
            check_mod._collect_remaining_helper_artifact_inventory(),
            tuple(
                entry
                for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_inventory()
                if entry["backend"] != "cs"
            ),
        )

    def test_materialized_backend_baseline_has_no_missing_modules(self) -> None:
        buckets = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
        for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends():
            for entry in buckets:
                actual = check_mod._collect_backend_generated_modules(backend, entry["bucket"])
                missing = tuple(module for module in entry["modules"] if module not in actual)
                self.assertEqual(missing, (), msg=f"{backend} {entry['bucket']}")

    def test_generated_first_build_profile_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_build_profiles(),
            (
                {
                    "backend": "cs",
                    "wiring_mode": "repo_runtime_bundle_residual",
                    "runtime_refs": (
                        "src/runtime/cs/native/built_in/py_runtime.cs",
                        "src/runtime/cs/generated/std/time.cs",
                        "src/runtime/cs/native/std/time_native.cs",
                        "src/runtime/cs/generated/std/math.cs",
                        "src/runtime/cs/generated/std/json.cs",
                        "src/runtime/cs/generated/std/pathlib.cs",
                        "src/runtime/cs/generated/utils/png.cs",
                        "src/runtime/cs/generated/utils/gif.cs",
                    ),
                },
                {
                    "backend": "go",
                    "wiring_mode": "staged_output_runtime_bundle",
                    "runtime_refs": ("out/py_runtime.go", "out/png.go", "out/gif.go"),
                },
                {
                    "backend": "java",
                    "wiring_mode": "staged_output_runtime_bundle",
                    "runtime_refs": ("out/PyRuntime.java", "out/png.java", "out/gif.java"),
                },
                {
                    "backend": "swift",
                    "wiring_mode": "staged_output_runtime_bundle",
                    "runtime_refs": ("out/py_runtime.swift", "out/image_runtime.swift"),
                },
                {
                    "backend": "kotlin",
                    "wiring_mode": "staged_output_runtime_bundle",
                    "runtime_refs": ("out/py_runtime.kt", "out/image_runtime.kt"),
                },
                {
                    "backend": "scala",
                    "wiring_mode": "staged_output_runner_bundle",
                    "runtime_refs": ("out/py_runtime.scala", "out/image_runtime.scala"),
                },
                {"backend": "nim", "wiring_mode": "standalone_compiler_only", "runtime_refs": ()},
                {"backend": "rs", "wiring_mode": "standalone_compiler_only", "runtime_refs": ()},
                {"backend": "js", "wiring_mode": "direct_script_runner", "runtime_refs": ()},
                {"backend": "ts", "wiring_mode": "direct_script_runner", "runtime_refs": ()},
                {"backend": "lua", "wiring_mode": "direct_script_runner", "runtime_refs": ()},
                {"backend": "ruby", "wiring_mode": "direct_script_runner", "runtime_refs": ()},
                {"backend": "php", "wiring_mode": "direct_script_runner", "runtime_refs": ()},
            ),
        )
        self.assertEqual(
            check_mod._collect_build_profile_inventory(),
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_build_profiles(),
        )

    def test_generated_first_smoke_inventory_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_smoke_inventory(),
            (
                {
                    "backend": "go",
                    "test_path": "test/unit/backends/go/test_py2go_smoke.py",
                    "required_tests": (
                        "test_go_runtime_source_path_is_migrated",
                        "test_go_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                    ),
                },
                {
                    "backend": "java",
                    "test_path": "test/unit/backends/java/test_py2java_smoke.py",
                    "required_tests": (
                        "test_java_runtime_source_path_is_migrated",
                        "test_java_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                    ),
                },
                {
                    "backend": "kotlin",
                    "test_path": "test/unit/backends/kotlin/test_py2kotlin_smoke.py",
                    "required_tests": (
                        "test_kotlin_runtime_source_path_is_migrated",
                        "test_kotlin_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                    ),
                },
                {
                    "backend": "scala",
                    "test_path": "test/unit/backends/scala/test_py2scala_smoke.py",
                    "required_tests": (
                        "test_scala_runtime_source_path_is_migrated",
                        "test_scala_generated_built_in_compare_lane_is_materialized",
                    ),
                },
                {
                    "backend": "swift",
                    "test_path": "test/unit/backends/swift/test_py2swift_smoke.py",
                    "required_tests": (
                        "test_swift_runtime_source_path_is_migrated",
                        "test_swift_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                    ),
                },
                {
                    "backend": "nim",
                    "test_path": "test/unit/backends/nim/test_py2nim_smoke.py",
                    "required_tests": (
                        "test_nim_runtime_source_path_is_migrated",
                        "test_nim_generated_built_in_compare_lane_compiles_with_runtime_bundle",
                    ),
                },
                {
                    "backend": "js",
                    "test_path": "test/unit/backends/js/test_py2js_smoke.py",
                    "required_tests": (
                        "test_js_repo_compat_lane_resolves_runtime_helpers",
                        "test_js_generated_built_in_compare_lane_resolves_native_runtime",
                    ),
                },
                {
                    "backend": "ts",
                    "test_path": "test/unit/backends/ts/test_py2ts_smoke.py",
                    "required_tests": (
                        "test_ts_repo_compat_lane_reexports_runtime_helpers",
                        "test_ts_generated_built_in_compare_lane_rehomes_native_runtime_import",
                    ),
                },
                {
                    "backend": "lua",
                    "test_path": "test/unit/backends/lua/test_py2lua_smoke.py",
                    "required_tests": (
                        "test_lua_runtime_source_path_is_migrated",
                        "test_lua_repo_compat_lane_resolves_runtime_helpers",
                    ),
                },
                {
                    "backend": "ruby",
                    "test_path": "test/unit/backends/rb/test_py2rb_smoke.py",
                    "required_tests": (
                        "test_ruby_runtime_source_path_is_migrated",
                        "test_ruby_repo_compat_lane_resolves_runtime_helpers",
                    ),
                },
                {
                    "backend": "php",
                    "test_path": "test/unit/backends/php/test_py2php_smoke.py",
                    "required_tests": (
                        "test_php_runtime_source_path_is_migrated",
                        "test_php_repo_generated_and_compat_lanes_resolve_native_substrate",
                        "test_php_generated_built_in_compare_lane_resolves_native_runtime",
                        "test_php_repo_public_compat_lane_resolves_remaining_shims",
                    ),
                },
            ),
        )
        self.assertEqual(check_mod._collect_smoke_issues(), [])

    def test_runtime_file_inventory_is_fixed(self) -> None:
        expected_inventory = tuple(
            {
                "backend": entry["backend"],
                "generated_files": entry["generated_files"],
                "native_files": entry["native_files"],
                "delete_target_files": entry["delete_target_files"],
            }
            for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_local_runtime_file_inventory()
        )
        self.assertEqual(
            check_mod._collect_expected_runtime_file_inventory(),
            expected_inventory,
        )
        self.assertEqual(
            tuple(
                check_mod._collect_backend_runtime_file_inventory(backend)
                for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends()
            ),
            expected_inventory,
        )

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_crossruntime_pyruntime_residual_caller_inventory as inventory_mod


class CheckCrossRuntimePyRuntimeResidualCallerInventoryTest(unittest.TestCase):
    def test_expected_and_observed_inventory_match(self) -> None:
        self.assertEqual(
            inventory_mod._collect_observed_pairs(),
            inventory_mod._collect_expected_pairs(),
        )

    def test_bucket_overlaps_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_bucket_overlaps(), [])

    def test_category_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_category_issues(), [])

    def test_source_guard_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_source_guard_issues(), [])

    def test_smoke_lane_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_smoke_lane_issues(), [])

    def test_generated_cpp_policy_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_generated_cpp_policy_issues(), [])

    def test_runtime_builtin_policy_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_runtime_builtin_policy_issues(), [])

    def test_representative_bucket_issues_are_empty(self) -> None:
        self.assertEqual(inventory_mod._collect_representative_bucket_issues(), [])

    def test_object_bridge_category_buckets_are_stable(self) -> None:
        self.assertEqual(
            inventory_mod.CATEGORY_BUCKETS["object_bridge_compat"],
            {
                "native_wrapper_object_bridge_residual",
                "generated_cpp_object_bridge_residual",
                "cs_runtime_utils_object_bridge_residual",
            },
        )

    def test_shared_type_id_category_buckets_are_stable(self) -> None:
        self.assertEqual(
            inventory_mod.CATEGORY_BUCKETS["shared_type_id_contract"],
            {
                "generated_cpp_shared_type_id_residual",
                "rs_runtime_builtin_shared_type_id_residual",
                "cs_runtime_builtin_shared_type_id_residual",
            },
        )

    def test_native_wrapper_bucket_is_cpp_wrapper_only(self) -> None:
        bucket = inventory_mod.EXPECTED_BUCKETS["native_wrapper_object_bridge_residual"]
        self.assertEqual(
            bucket,
            {
                ("py_runtime_object_isinstance", "src/runtime/cpp/native/compiler/transpile_cli.cpp"),
                ("py_runtime_object_isinstance", "src/runtime/cpp/native/compiler/backend_registry_static.cpp"),
            },
        )

    def test_generated_cpp_buckets_are_split_by_contract_type(self) -> None:
        self.assertEqual(
            inventory_mod.EXPECTED_BUCKETS["generated_cpp_object_bridge_residual"],
            {
                ("py_runtime_object_isinstance", "src/runtime/cpp/generated/std/json.cpp"),
                ("py_append", "src/runtime/cpp/generated/built_in/iter_ops.cpp"),
            },
        )
        self.assertEqual(
            inventory_mod.EXPECTED_BUCKETS["generated_cpp_shared_type_id_residual"],
            {
                ("py_runtime_object_type_id", "src/runtime/cpp/generated/built_in/type_id.cpp"),
            },
        )
        self.assertEqual(
            inventory_mod.GENERATED_CPP_MUST_REMAIN,
            {
                ("py_runtime_object_isinstance", "src/runtime/cpp/generated/std/json.cpp"),
                ("py_append", "src/runtime/cpp/generated/built_in/iter_ops.cpp"),
                ("py_runtime_object_type_id", "src/runtime/cpp/generated/built_in/type_id.cpp"),
            },
        )
        self.assertEqual(inventory_mod.GENERATED_CPP_REDELEGATABLE, set())

    def test_cs_runtime_utils_object_bridge_bucket_is_stable(self) -> None:
        self.assertEqual(
            inventory_mod.EXPECTED_BUCKETS["cs_runtime_utils_object_bridge_residual"],
            {
                ("py_append", "src/runtime/cs/pytra/utils/png.cs"),
                ("py_append", "src/runtime/cs/pytra/utils/gif.cs"),
            },
        )

    def test_runtime_builtin_buckets_cover_both_runtime_trees(self) -> None:
        rs_bucket = inventory_mod.EXPECTED_BUCKETS["rs_runtime_builtin_shared_type_id_residual"]
        cs_bucket = inventory_mod.EXPECTED_BUCKETS["cs_runtime_builtin_shared_type_id_residual"]
        self.assertEqual(
            {path for _, path in rs_bucket},
            {
                "src/runtime/rs/pytra/built_in/py_runtime.rs",
                "src/runtime/rs/pytra-core/built_in/py_runtime.rs",
            },
        )
        self.assertEqual(
            {path for _, path in cs_bucket},
            {
                "src/runtime/cs/pytra/built_in/py_runtime.cs",
                "src/runtime/cs/pytra-core/built_in/py_runtime.cs",
            },
        )
        self.assertEqual(inventory_mod.RS_RUNTIME_BUILTIN_MUST_REMAIN, rs_bucket)
        self.assertEqual(inventory_mod.RS_RUNTIME_BUILTIN_REDELEGATABLE, set())
        self.assertEqual(inventory_mod.CS_RUNTIME_BUILTIN_MUST_REMAIN, cs_bucket)
        self.assertEqual(inventory_mod.CS_RUNTIME_BUILTIN_REDELEGATABLE, set())

    def test_target_end_state_keys_match_bucket_names(self) -> None:
        self.assertEqual(
            set(inventory_mod.TARGET_END_STATE.keys()),
            set(inventory_mod.EXPECTED_BUCKETS.keys()),
        )

    def test_smoke_lane_files_are_stable(self) -> None:
        self.assertEqual(
            set(inventory_mod.SMOKE_LANE_REQUIRED_SUBSTRINGS.keys()),
            {
                "test/unit/common/test_py2x_entrypoints_contract.py",
                "test/unit/backends/cpp/test_cpp_runtime_iterable.py",
                "test/unit/backends/cpp/test_cpp_runtime_type_id.py",
                "test/unit/backends/rs/test_py2rs_smoke.py",
                "test/unit/backends/cs/test_py2cs_smoke.py",
            },
        )

    def test_representative_bucket_manifest_is_bucket_complete(self) -> None:
        self.assertEqual(
            inventory_mod.REPRESENTATIVE_BUCKET_MANIFEST,
            {
                "native_wrapper_object_bridge_residual": {
                    "smoke_file": "test/unit/common/test_py2x_entrypoints_contract.py",
                    "smoke_tests": {
                        "test_native_cpp_typed_boundary_make_object_usage_stays_on_export_seams",
                    },
                    "source_guard_paths": {
                        "src/runtime/cpp/native/compiler/transpile_cli.cpp",
                        "src/runtime/cpp/native/compiler/backend_registry_static.cpp",
                    },
                },
                "generated_cpp_object_bridge_residual": {
                    "smoke_file": "test/unit/backends/cpp/test_cpp_runtime_iterable.py",
                    "smoke_tests": {
                        "test_runtime_list_overload_inventory",
                    },
                    "source_guard_paths": {
                        "src/runtime/cpp/generated/std/json.cpp",
                        "src/runtime/cpp/generated/built_in/iter_ops.cpp",
                    },
                },
                "generated_cpp_shared_type_id_residual": {
                    "smoke_file": "test/unit/backends/cpp/test_cpp_runtime_iterable.py",
                    "smoke_tests": {
                        "test_runtime_list_overload_inventory",
                    },
                    "source_guard_paths": {
                        "src/runtime/cpp/generated/built_in/type_id.cpp",
                    },
                },
                "cs_runtime_utils_object_bridge_residual": {
                    "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
                    "smoke_tests": {
                        "test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not",
                        "test_bytearray_index_and_slice_compat_helpers_stay_explicit",
                    },
                    "source_guard_paths": set(),
                },
                "rs_runtime_builtin_shared_type_id_residual": {
                    "smoke_file": "test/unit/backends/rs/test_py2rs_smoke.py",
                    "smoke_tests": {
                        "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
                    },
                    "source_guard_paths": {
                        "src/runtime/rs/pytra/built_in/py_runtime.rs",
                        "src/runtime/rs/pytra-core/built_in/py_runtime.rs",
                    },
                },
                "cs_runtime_builtin_shared_type_id_residual": {
                    "smoke_file": "test/unit/backends/cs/test_py2cs_smoke.py",
                    "smoke_tests": {
                        "test_type_predicate_nodes_are_lowered_without_legacy_bridge",
                    },
                    "source_guard_paths": {
                        "src/runtime/cs/pytra/built_in/py_runtime.cs",
                        "src/runtime/cs/pytra-core/built_in/py_runtime.cs",
                    },
                },
            },
        )


if __name__ == "__main__":
    unittest.main()

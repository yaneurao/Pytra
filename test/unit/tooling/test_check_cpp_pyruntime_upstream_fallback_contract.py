from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import cpp_pyruntime_upstream_fallback_contract as contract_mod
from tools import check_cpp_pyruntime_upstream_fallback_contract as check_mod


class CheckCppPyRuntimeUpstreamFallbackContractTest(unittest.TestCase):
    def test_partition_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_partition_issues(), [])

    def test_boundary_guard_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_boundary_guard_issues(), [])

    def test_boundary_partitions_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.BOUNDARY_CLASS_ORDER,
            (
                "object_only_compat_header",
                "any_object_boundary_header",
                "typed_lane_must_not_use",
            ),
        )
        self.assertEqual(
            contract_mod.OBJECT_ONLY_COMPAT_HEADER_IDS,
            (
                "header_object_bridge_mut_list_cast",
                "header_object_bridge_const_list_cast",
                "header_object_bridge_py_at",
                "header_object_bridge_py_append",
            ),
        )
        self.assertEqual(
            contract_mod.ANY_OBJECT_BOUNDARY_HEADER_IDS,
            (
                "header_typed_list_copy_from_object",
                "header_generic_make_object_fallback",
                "header_generic_py_to_object_fallback",
                "header_object_py_to_call_sites",
                "header_dict_key_charptr_object_coercion",
            ),
        )
        self.assertEqual(
            contract_mod.TYPED_LANE_MUST_NOT_USE_IDS,
            (
                "cpp_emitter_boxed_list_seed_sites",
                "cpp_emitter_object_list_bridge_sites",
                "generated_runtime_object_list_bridge_sites",
                "generated_runtime_boxed_list_seed_sites",
                "generated_runtime_generic_index_sites",
                "sample_cpp_py_append_sites",
                "sample_cpp_generic_index_sites",
            ),
        )


if __name__ == "__main__":
    unittest.main()

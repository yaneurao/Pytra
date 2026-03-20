from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_contract_inventory as inventory_mod


class CheckCppPyRuntimeContractInventoryTest(unittest.TestCase):
    def test_expected_and_observed_inventory_match(self) -> None:
        self.assertEqual(
            inventory_mod._collect_observed_pairs(),
            inventory_mod._collect_expected_pairs(),
        )

    def test_buckets_do_not_overlap(self) -> None:
        self.assertEqual(inventory_mod._collect_bucket_overlaps(), [])

    def test_shared_runtime_contract_excludes_native_compiler_wrappers(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
        self.assertNotIn(
            ("py_isinstance", "src/runtime/cpp/compiler/transpile_cli.cpp"),
            shared,
        )
        self.assertNotIn(
            ("py_isinstance", "src/runtime/cpp/compiler/backend_registry_static.cpp"),
            shared,
        )
        self.assertIn(
            ("py_runtime_object_isinstance", "src/runtime/cpp/compiler/transpile_cli.cpp"),
            shared,
        )
        self.assertIn(
            ("py_runtime_object_isinstance", "src/runtime/cpp/compiler/backend_registry_static.cpp"),
            shared,
        )

    def test_typed_lane_removable_bucket_can_reach_zero_after_upstreaming(self) -> None:
        self.assertEqual(inventory_mod.EXPECTED_BUCKETS["typed_lane_removable"], set())
        self.assertIn("typed_lane_removable", inventory_mod.EMPTY_BUCKETS_ALLOWED)

    def test_object_bridge_required_bucket_is_cs_bytearray_and_runtime_only(self) -> None:
        object_bridge = inventory_mod.EXPECTED_BUCKETS["object_bridge_required"]
        self.assertEqual(
            object_bridge,
            {
                ("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
                ("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
            },
        )
        self.assertTrue(
            all(
                path.startswith("src/toolchain/emit/cs/") or path.startswith("src/runtime/cs/")
                for _, path in object_bridge
            )
        )

    def test_shared_runtime_contract_bucket_is_type_id_and_cross_runtime_only(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
        cpp_emitter_entries = {
            entry
            for entry in shared
            if entry[1].startswith("src/toolchain/emit/cpp/")
        }
        self.assertTrue(
            all(
                symbol
                in {
                    "py_runtime_value_type_id",
                    "py_runtime_value_isinstance",
                    "py_runtime_type_id_is_subtype",
                    "py_runtime_type_id_issubclass",
                }
                for symbol, _ in cpp_emitter_entries
            )
        )
        cpp_generated_entries = {
            entry
            for entry in shared
            if entry[1].startswith("src/runtime/generated/")
        }
        self.assertTrue(
            all(
                symbol
                in {
                    "py_runtime_value_type_id",
                    "py_runtime_value_isinstance",
                }
                for symbol, _ in cpp_generated_entries
            )
        )
        cpp_native_entries = {
            entry
            for entry in shared
            if entry[1].startswith("src/runtime/cpp/")
        }
        self.assertTrue(
            all(
                symbol
                in {
                    "py_runtime_object_isinstance",
                }
                for symbol, _ in cpp_native_entries
            )
        )
        cross_runtime_mutations = {
            entry
            for entry in shared
            if entry[1].startswith("src/runtime/cs/")
            or entry[1].startswith("src/runtime/rs/")
            or entry[1].startswith("src/toolchain/emit/cs/")
            or entry[1].startswith("src/toolchain/emit/rs/")
        }
        self.assertNotIn(("py_append", "src/toolchain/emit/cs/emitter/cs_emitter.py"), shared)
        self.assertNotIn(("py_pop", "src/toolchain/emit/cs/emitter/cs_emitter.py"), shared)
        self.assertIn(
            ("py_runtime_type_id_issubclass", "src/toolchain/emit/rs/emitter/rs_emitter.py"),
            shared,
        )
        self.assertIn(
            ("py_runtime_type_id_issubclass", "src/toolchain/emit/cs/emitter/cs_emitter.py"),
            shared,
        )

    def test_shared_runtime_contract_uses_generated_type_id_cpp_value_contracts(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
        self.assertNotIn(("py_runtime_type_id", "src/runtime/generated/built_in/type_id.cpp"), shared)
        self.assertNotIn(("py_isinstance", "src/runtime/generated/built_in/type_id.cpp"), shared)
        self.assertIn(("py_runtime_value_type_id", "src/runtime/generated/built_in/type_id.cpp"), shared)
        self.assertIn(("py_runtime_value_isinstance", "src/runtime/generated/built_in/type_id.cpp"), shared)
        self.assertIn(("py_runtime_value_isinstance", "src/runtime/generated/std/json.cpp"), shared)
        self.assertIn(("py_runtime_value_isinstance", "src/runtime/generated/compiler/transpile_cli.cpp"), shared)
        self.assertIn(("py_runtime_value_isinstance", "src/runtime/rs/generated/std/json.rs"), shared)

    def test_inventory_scan_ignores_upstream_fallback_inventory_module(self) -> None:
        self.assertIn(
            "src/toolchain/compiler/cpp_pyruntime_upstream_fallback_inventory.py",
            inventory_mod.EXCLUDED_PATHS,
        )


if __name__ == "__main__":
    unittest.main()

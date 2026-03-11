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

    def test_shared_runtime_contract_covers_native_compiler_wrappers(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
        self.assertIn(
            ("py_isinstance", "src/runtime/cpp/native/compiler/transpile_cli.cpp"),
            shared,
        )
        self.assertIn(
            ("py_isinstance", "src/runtime/cpp/native/compiler/backend_registry_static.cpp"),
            shared,
        )

    def test_typed_lane_removable_covers_cpp_emitter_mutation_helpers(self) -> None:
        typed = inventory_mod.EXPECTED_BUCKETS["typed_lane_removable"]
        self.assertIn(("py_append", "src/backends/cpp/emitter/call.py"), typed)
        self.assertIn(("py_set_at", "src/backends/cpp/emitter/stmt.py"), typed)
        self.assertIn(("py_pop", "src/backends/cpp/emitter/cpp_emitter.py"), typed)

    def test_object_bridge_required_bucket_stays_generated_runtime_only(self) -> None:
        object_bridge = inventory_mod.EXPECTED_BUCKETS["object_bridge_required"]
        self.assertTrue(all(path.startswith("src/runtime/cpp/generated/") for _, path in object_bridge))
        self.assertEqual({symbol for symbol, _ in object_bridge}, {"py_append", "py_isinstance"})

    def test_shared_runtime_contract_bucket_is_type_id_and_cross_runtime_only(self) -> None:
        shared = inventory_mod.EXPECTED_BUCKETS["shared_runtime_contract"]
        cpp_runtime_entries = {
            entry
            for entry in shared
            if entry[1].startswith("src/runtime/cpp/")
            or entry[1].startswith("src/backends/cpp/")
        }
        self.assertTrue(
            all(symbol in {"py_runtime_type_id", "py_isinstance", "py_is_subtype"} for symbol, _ in cpp_runtime_entries)
        )
        cross_runtime_mutations = {
            entry
            for entry in shared
            if entry[1].startswith("src/runtime/cs/")
            or entry[1].startswith("src/runtime/rs/")
            or entry[1].startswith("src/backends/cs/")
            or entry[1].startswith("src/backends/rs/")
        }
        self.assertIn(("py_append", "src/runtime/cs/pytra/utils/gif.cs"), cross_runtime_mutations)
        self.assertIn(("py_append", "src/runtime/cs/pytra/utils/png.cs"), cross_runtime_mutations)


if __name__ == "__main__":
    unittest.main()

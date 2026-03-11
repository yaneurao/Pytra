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


if __name__ == "__main__":
    unittest.main()

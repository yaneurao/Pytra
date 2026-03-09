from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_transpiler_version_gate as gate_mod


class CheckTranspilerVersionGateTest(unittest.TestCase):
    def test_collect_required_components_marks_cpp_for_selfhost_entry(self) -> None:
        touched_shared, touched_langs, touched_paths = gate_mod._collect_required_components(["src/py2x-selfhost.py"])
        self.assertFalse(touched_shared)
        self.assertEqual(touched_langs, {"cpp"})
        self.assertEqual(touched_paths, ["src/py2x-selfhost.py"])

    def test_collect_required_components_marks_cpp_for_selfhost_core(self) -> None:
        touched_shared, touched_langs, touched_paths = gate_mod._collect_required_components(
            ["src/toolchain/ir/core.py"]
        )
        self.assertFalse(touched_shared)
        self.assertEqual(touched_langs, {"cpp"})
        self.assertEqual(touched_paths, ["src/toolchain/ir/core.py"])

    def test_collect_required_components_keeps_host_entry_out_of_cpp_lane(self) -> None:
        touched_shared, touched_langs, touched_paths = gate_mod._collect_required_components(["src/py2x.py"])
        self.assertFalse(touched_shared)
        self.assertNotIn("cpp", touched_langs)
        self.assertIn("rs", touched_langs)
        self.assertIn("cs", touched_langs)
        self.assertEqual(touched_paths, ["src/py2x.py"])


if __name__ == "__main__":
    unittest.main()

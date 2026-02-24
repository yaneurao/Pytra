"""Unit tests for EAST1 build entry helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.east_parts.east1_build import build_east1_document
from src.pytra.compiler.east_parts.east1_build import build_module_east_map


class East1BuildTest(unittest.TestCase):
    def test_build_east1_document_marks_stage_one(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            main_py = Path(td) / "main.py"
            main_py.write_text("def main() -> None:\n    print(1)\n", encoding="utf-8")

            east = build_east1_document(main_py)
            self.assertIsInstance(east, dict)
            self.assertEqual(east.get("kind"), "Module")
            self.assertEqual(east.get("east_stage"), 1)

    def test_build_module_east_map_keeps_stage_one_for_user_modules(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            helper_py = root / "helper.py"
            helper_py.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = root / "main.py"
            main_py.write_text("import helper\n\nprint(helper.f())\n", encoding="utf-8")

            module_map = build_module_east_map(main_py)
            self.assertIn(str(main_py), module_map)
            self.assertIn(str(helper_py), module_map)
            for doc in module_map.values():
                self.assertIsInstance(doc, dict)
                self.assertEqual(doc.get("kind"), "Module")
                self.assertEqual(doc.get("east_stage"), 1)


if __name__ == "__main__":
    unittest.main()

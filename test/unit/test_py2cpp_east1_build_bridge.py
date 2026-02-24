"""Regression tests for py2cpp <-> east1_build integration."""

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

from src.py2cpp import _analyze_import_graph
from src.py2cpp import build_module_east_map
from src.py2cpp import build_module_symbol_index
from src.py2cpp import build_module_type_schema


class Py2CppEast1BuildBridgeTest(unittest.TestCase):
    def test_analyze_import_graph_uses_east1_build_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "helper.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = root / "main.py"
            main_py.write_text("import helper\n\nprint(helper.f())\n", encoding="utf-8")

            analysis = _analyze_import_graph(main_py)
            files = analysis.get("user_module_files", [])
            self.assertIsInstance(files, list)
            self.assertIn(str(main_py), files)
            self.assertIn(str(root / "helper.py"), files)

    def test_build_module_east_map_keeps_py2cpp_stage3_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "helper.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = root / "main.py"
            main_py.write_text("import helper\n\nprint(helper.f())\n", encoding="utf-8")

            module_map = build_module_east_map(main_py)
            self.assertIn(str(main_py), module_map)
            self.assertIn(str(root / "helper.py"), module_map)
            for doc in module_map.values():
                self.assertIsInstance(doc, dict)
                self.assertEqual(doc.get("kind"), "Module")
                self.assertEqual(doc.get("east_stage"), 3)

            sym_index = build_module_symbol_index(module_map)
            type_schema = build_module_type_schema(module_map)
            self.assertIsInstance(sym_index, dict)
            self.assertIsInstance(type_schema, dict)


if __name__ == "__main__":
    unittest.main()

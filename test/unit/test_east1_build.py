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
from src.pytra.compiler.transpile_cli import ImportGraphHelpers
from src.pytra.compiler.transpile_cli import load_east_document


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

    def test_transpile_cli_import_graph_helpers_delegate_to_east1_build(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            helper_py = root / "helper.py"
            helper_py.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = root / "main.py"
            main_py.write_text("import helper\n\nprint(helper.f())\n", encoding="utf-8")

            analysis = ImportGraphHelpers.analyze_import_graph(
                main_py,
                Path("src/pytra/std"),
                Path("src/pytra/utils"),
                load_east_document,
            )
            files = analysis.get("user_module_files", [])
            self.assertIsInstance(files, list)
            self.assertIn(str(main_py), files)
            self.assertIn(str(helper_py), files)

            def _load_for_map(
                path_obj: Path,
                parser_backend: str = "self_hosted",
                east_stage: str = "2",
                object_dispatch_mode: str = "",
            ) -> dict[str, object]:
                _ = east_stage
                _ = object_dispatch_mode
                return load_east_document(path_obj, parser_backend=parser_backend)

            module_map = ImportGraphHelpers.build_module_east_map(
                main_py,
                _load_for_map,
            )
            self.assertIn(str(main_py), module_map)
            self.assertIn(str(helper_py), module_map)


if __name__ == "__main__":
    unittest.main()

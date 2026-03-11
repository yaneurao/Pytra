from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.toolchain.frontends.relative_import_normalization as relative_import


class RelativeImportSemanticsTest(unittest.TestCase):
    def test_resolve_import_graph_entry_root_uses_init_chain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            entry = sub / "main.py"
            entry.write_text("print(1)\n", encoding="utf-8")
            self.assertEqual(str(relative_import.resolve_import_graph_entry_root(entry)), str(pkg))

    def test_resolve_relative_module_name_for_graph_accepts_bare_parent_module(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            helper = pkg / "helper.py"
            helper.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = sub / "main.py"
            main_py.write_text("from .. import helper\n", encoding="utf-8")

            resolved = relative_import.resolve_relative_module_name_for_graph("..helper", pkg, main_py)
            self.assertEqual("user", resolved.get("status"))
            self.assertEqual("helper", resolved.get("module_id"))
            self.assertEqual(str(helper), resolved.get("path"))

    def test_resolve_relative_module_name_for_graph_reports_missing_and_escape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            main_py = sub / "main.py"
            main_py.write_text("from .missing import f\n", encoding="utf-8")

            missing = relative_import.resolve_relative_module_name_for_graph(".missing", pkg, main_py)
            escape = relative_import.resolve_relative_module_name_for_graph("...oops", pkg, main_py)
            self.assertEqual("missing", missing.get("status"))
            self.assertEqual("sub.missing", missing.get("module_id"))
            self.assertEqual("relative", escape.get("status"))
            self.assertEqual("...oops", escape.get("module_id"))

    def test_normalize_relative_module_id_returns_absolute_module_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            helper = pkg / "helper.py"
            helper.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = sub / "main.py"
            main_py.write_text("from .. import helper\n", encoding="utf-8")

            normalized = relative_import.normalize_relative_module_id("..helper", pkg, main_py)
            self.assertEqual("helper", normalized)

    def test_rewrite_relative_imports_in_east_doc_rewrites_body_and_meta(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "pkg"
            sub = pkg / "sub"
            sub.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (sub / "__init__.py").write_text("", encoding="utf-8")
            helper = pkg / "helper.py"
            helper.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
            main_py = sub / "main.py"
            main_py.write_text("from .. import helper\n", encoding="utf-8")

            east_doc: dict[str, object] = {
                "body": [{"kind": "ImportFrom", "module": "..helper", "names": [{"name": "f"}]}],
                "meta": {
                    "import_bindings": [{"module_id": "..helper"}],
                    "import_symbols": {"helper": {"module": "..helper"}},
                    "qualified_symbol_refs": [{"module_id": "..helper"}],
                    "import_resolution": {
                        "bindings": [{"module_id": "..helper", "source_module_id": "..helper"}],
                        "qualified_refs": [{"module_id": "..helper"}],
                    },
                },
            }

            out = relative_import.rewrite_relative_imports_in_east_doc(
                east_doc,
                entry_root=pkg,
                importer_path=main_py,
            )
            body = out.get("body")
            self.assertTrue(isinstance(body, list))
            self.assertEqual("helper", body[0].get("module"))
            meta = out.get("meta")
            self.assertTrue(isinstance(meta, dict))
            self.assertEqual("helper", meta["import_bindings"][0]["module_id"])
            self.assertEqual("helper", meta["import_symbols"]["helper"]["module"])
            self.assertEqual("helper", meta["qualified_symbol_refs"][0]["module_id"])
            self.assertEqual("helper", meta["import_resolution"]["bindings"][0]["module_id"])
            self.assertEqual("helper", meta["import_resolution"]["bindings"][0]["source_module_id"])
            self.assertEqual("helper", meta["import_resolution"]["qualified_refs"][0]["module_id"])

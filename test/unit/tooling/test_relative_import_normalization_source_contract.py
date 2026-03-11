from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


class RelativeImportNormalizationSourceContractTest(unittest.TestCase):
    def test_transpile_cli_reexports_split_relative_import_helpers(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py").read_text(encoding="utf-8")
        self.assertIn(
            "from toolchain.frontends.relative_import_normalization import resolve_import_graph_entry_root",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.relative_import_normalization import resolve_relative_module_name_for_graph",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.relative_import_normalization import rewrite_relative_imports_in_module_east_map",
            src,
        )
        self.assertNotIn("def resolve_import_graph_entry_root(", src)
        self.assertNotIn("def resolve_relative_module_name_for_graph(", src)
        self.assertNotIn("def rewrite_relative_imports_in_module_east_map(", src)

    def test_east1_build_uses_split_relative_import_module(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "east1_build.py").read_text(encoding="utf-8")
        self.assertIn(
            "from toolchain.frontends.relative_import_normalization import resolve_import_graph_entry_root",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.relative_import_normalization import resolve_relative_module_name_for_graph",
            src,
        )
        self.assertNotIn(
            "from toolchain.frontends.transpile_cli import resolve_import_graph_entry_root",
            src,
        )
        self.assertNotIn(
            "from toolchain.frontends.transpile_cli import resolve_relative_module_name_for_graph",
            src,
        )

    def test_split_module_owns_relative_import_helpers(self) -> None:
        src = (
            ROOT
            / "src"
            / "toolchain"
            / "frontends"
            / "relative_import_normalization.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def resolve_import_graph_entry_root(", src)
        self.assertIn("def resolve_relative_module_name_for_graph(", src)
        self.assertIn("def normalize_relative_module_id(", src)
        self.assertIn("def rewrite_relative_imports_in_east_doc(", src)
        self.assertIn("def rewrite_relative_imports_in_module_east_map(", src)

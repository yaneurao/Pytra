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
    def test_import_graph_path_helper_module_owns_shared_path_helpers(self) -> None:
        src = (
            ROOT
            / "src"
            / "toolchain"
            / "frontends"
            / "import_graph_path_helpers.py"
        ).read_text(encoding="utf-8")
        self.assertIn("def path_parent_text(", src)
        self.assertIn("def path_key_for_graph(", src)
        self.assertIn("def module_name_from_path_for_graph(", src)

    def test_transpile_cli_reexports_split_relative_import_helpers(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py").read_text(encoding="utf-8")
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import module_name_from_path_for_graph",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import path_key_for_graph",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import path_parent_text",
            src,
        )
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
        self.assertNotIn("def module_name_from_path_for_graph(", src)
        self.assertNotIn("def path_key_for_graph(", src)
        self.assertNotIn("def path_parent_text(", src)

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
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import module_name_from_path_for_graph",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import path_key_for_graph",
            src,
        )
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import path_parent_text",
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
        self.assertNotIn(
            "from toolchain.frontends.transpile_cli import module_name_from_path_for_graph",
            src,
        )
        self.assertNotIn(
            "from toolchain.frontends.transpile_cli import path_key_for_graph",
            src,
        )
        self.assertNotIn(
            "from toolchain.frontends.transpile_cli import path_parent_text",
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
        self.assertIn(
            "from toolchain.frontends.import_graph_path_helpers import module_name_from_path_for_graph as _module_name_from_path_for_graph",
            src,
        )
        self.assertNotIn("def _module_name_from_path_for_graph(", src)
        self.assertNotIn("def _path_key_for_graph(", src)
        self.assertNotIn("def _path_parent_text(", src)

    def test_transpile_cli_does_not_keep_legacy_relative_import_fallback(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py").read_text(encoding="utf-8")
        self.assertNotIn("relative import is not supported", src)
        self.assertNotIn("unsupported_import_form", src)
        self.assertIn('kind="relative_import_escape"', src)

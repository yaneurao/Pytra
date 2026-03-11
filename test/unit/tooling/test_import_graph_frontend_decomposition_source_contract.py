from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


class ImportGraphFrontendDecompositionSourceContractTest(unittest.TestCase):
    def test_split_module_owns_import_graph_frontend_helpers(self) -> None:
        src = (
            ROOT
            / "src"
            / "toolchain"
            / "frontends"
            / "import_graph_frontend_helpers.py"
        ).read_text(encoding="utf-8")
        for name in [
            "is_pytra_module_name",
            "rel_disp_for_graph",
            "sanitize_module_label",
            "module_rel_label",
            "module_id_from_east_for_graph",
            "resolve_user_module_path_for_graph",
            "collect_reserved_import_conflicts",
            "collect_import_requests",
            "collect_import_from_request_modules",
            "collect_import_request_modules",
            "collect_import_modules",
            "sort_str_list_copy",
            "collect_user_module_files_for_graph",
        ]:
            self.assertIn(f"def {name}(", src)

    def test_transpile_cli_reexports_split_import_graph_frontend_helpers(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py").read_text(encoding="utf-8")
        for name in [
            "is_pytra_module_name",
            "rel_disp_for_graph",
            "sanitize_module_label",
            "module_rel_label",
            "module_id_from_east_for_graph",
            "resolve_user_module_path_for_graph",
            "collect_reserved_import_conflicts",
            "collect_import_requests",
            "collect_import_from_request_modules",
            "collect_import_request_modules",
            "collect_import_modules",
            "sort_str_list_copy",
            "collect_user_module_files_for_graph",
        ]:
            self.assertIn(
                f"from toolchain.frontends.import_graph_frontend_helpers import {name}",
                src,
            )
            self.assertNotIn(f"def {name}(", src)

    def test_east1_build_uses_split_import_graph_frontend_helpers(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "east1_build.py").read_text(encoding="utf-8")
        for name in [
            "collect_import_requests",
            "collect_import_request_modules",
            "collect_reserved_import_conflicts",
            "rel_disp_for_graph",
        ]:
            self.assertIn(
                f"from toolchain.frontends.import_graph_frontend_helpers import {name}",
                src,
            )
            self.assertNotIn(
                f"from toolchain.frontends.transpile_cli import {name}",
                src,
            )


if __name__ == "__main__":
    unittest.main()

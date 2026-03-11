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
    def test_split_module_owns_import_graph_analysis_helpers(self) -> None:
        src = (
            ROOT
            / "src"
            / "toolchain"
            / "frontends"
            / "import_graph_analysis_helpers.py"
        ).read_text(encoding="utf-8")
        for name in [
            "split_graph_issue_entry",
            "make_graph_issue_entry",
            "normalize_graph_issue_entry",
            "format_graph_issue_entry",
            "append_unique_graph_issue_entry",
            "dict_any_get_graph_issue_entries",
            "graph_issue_entries_to_text_list",
            "graph_cycle_dfs",
            "format_graph_list_section",
            "format_import_graph_report",
            "validate_import_graph_or_raise",
            "finalize_import_graph_analysis",
            "is_known_non_user_import",
            "resolve_module_name_for_graph",
            "resolve_module_name",
        ]:
            self.assertIn(f"def {name}(", src)

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
            "split_graph_issue_entry",
            "make_graph_issue_entry",
            "normalize_graph_issue_entry",
            "format_graph_issue_entry",
            "append_unique_graph_issue_entry",
            "dict_any_get_graph_issue_entries",
            "graph_issue_entries_to_text_list",
            "graph_cycle_dfs",
            "format_graph_list_section",
            "format_import_graph_report",
            "finalize_import_graph_analysis",
            "is_known_non_user_import",
            "resolve_module_name_for_graph",
            "resolve_module_name",
        ]:
            self.assertIn(
                f"from toolchain.frontends.import_graph_analysis_helpers import {name}",
                src,
            )
            self.assertNotIn(f"def {name}(", src)
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
            "append_unique_graph_issue_entry",
            "finalize_import_graph_analysis",
            "resolve_module_name_for_graph",
        ]:
            self.assertIn(
                f"from toolchain.frontends.import_graph_analysis_helpers import {name}",
                src,
            )
            self.assertNotIn(
                f"from toolchain.frontends.transpile_cli import {name}",
                src,
            )
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

    def test_transpile_cli_retains_import_graph_bridge_entrypoints(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py").read_text(encoding="utf-8")
        for name in [
            "analyze_import_graph_via_east1_build",
            "build_module_east_map_via_east1_build",
            "analyze_import_graph",
            "build_module_east_map",
        ]:
            self.assertIn(f"def {name}(", src)
        self.assertIn("class ImportGraphHelpers:", src)
        self.assertIn(
            "analyze_import_graph = staticmethod(analyze_import_graph_via_east1_build)",
            src,
        )
        self.assertIn(
            "build_module_east_map = staticmethod(build_module_east_map_via_east1_build)",
            src,
        )

    def test_east1_build_retains_import_graph_implementation_entrypoints(self) -> None:
        src = (ROOT / "src" / "toolchain" / "frontends" / "east1_build.py").read_text(encoding="utf-8")
        for name in [
            "build_east1_document",
            "_analyze_import_graph_impl",
            "analyze_import_graph",
            "build_module_east_map",
            "build_module_symbol_index",
            "build_module_type_schema",
        ]:
            self.assertIn(f"def {name}(", src)

    def test_prepare_selfhost_source_reads_split_import_graph_modules(self) -> None:
        src = (ROOT / "tools" / "prepare_selfhost_source.py").read_text(encoding="utf-8")
        self.assertIn('SRC_IMPORT_GRAPH_ANALYSIS_HELPERS = ROOT / "src" / "toolchain" / "frontends" / "import_graph_analysis_helpers.py"', src)
        self.assertIn(
            'SRC_IMPORT_GRAPH_FRONTEND_HELPERS = ROOT / "src" / "toolchain" / "frontends" / "import_graph_frontend_helpers.py"',
            src,
        )
        self.assertIn(
            'import_graph_analysis_text = SRC_IMPORT_GRAPH_ANALYSIS_HELPERS.read_text(encoding="utf-8")',
            src,
        )
        self.assertIn(
            'import_graph_helper_text = SRC_IMPORT_GRAPH_FRONTEND_HELPERS.read_text(encoding="utf-8")',
            src,
        )


if __name__ == "__main__":
    unittest.main()

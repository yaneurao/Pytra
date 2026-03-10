from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

MODULE_PATH = ROOT / "tools" / "check_multilang_selfhost_suite.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_multilang_selfhost_suite", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load check_multilang_selfhost_suite module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckMultilangSelfhostSuiteTest(unittest.TestCase):
    def test_stage1_summary_maps_preview_to_known_block(self) -> None:
        mod = _load_module()
        row = mod._stage1_row_to_summary(["js", "fail", "preview", "blocked", "preview backend output"])
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.lane, "stage1")
        self.assertEqual(row.subject, "js")
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "preview_only")

    def test_stage1_summary_maps_toolchain_gap(self) -> None:
        mod = _load_module()
        row = mod._stage1_row_to_summary(["swift", "missing_toolchain", "native", "skip", "toolchain missing"])
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.top_level_category, "toolchain_missing")
        self.assertEqual(row.detail_category, "toolchain_missing")

    def test_stage1_summary_maps_unsupported_note_to_known_block(self) -> None:
        mod = _load_module()
        row = mod._stage1_row_to_summary(
            ["scala", "fail", "native", "blocked", "[unsupported_by_design] stage1 runner intentionally unavailable"]
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "unsupported_by_design")

    def test_multistage_summary_keeps_detail_category(self) -> None:
        mod = _load_module()
        row = mod._multistage_row_to_summary(
            ["java", "pass", "fail", "skip", "self_retranspile_fail", "selfhost stage2 mismatch"]
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.lane, "multistage")
        self.assertEqual(row.subject, "java")
        self.assertEqual(row.top_level_category, "regression")
        self.assertEqual(row.detail_category, "self_retranspile_fail")

    def test_multistage_summary_maps_unsupported_by_design_to_known_block(self) -> None:
        mod = _load_module()
        row = mod._multistage_row_to_summary(
            ["swift", "pass", "skip", "skip", "unsupported_by_design", "multistage runner is not defined"]
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "unsupported_by_design")


if __name__ == "__main__":
    unittest.main()

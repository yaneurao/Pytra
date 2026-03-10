from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.selfhost_parity_summary import build_direct_e2e_summary_row
from tools.selfhost_parity_summary import build_stage2_diff_summary_row
from tools.selfhost_parity_summary import build_stage2_summary_row
from tools.selfhost_parity_summary import build_summary_row
from tools.selfhost_parity_summary import render_summary_block


class SelfhostParitySummaryTest(unittest.TestCase):
    def test_direct_e2e_not_implemented_maps_to_known_block(self) -> None:
        row = build_direct_e2e_summary_row(
            "test/fixtures/core/add.py",
            "selfhost_transpile_fail",
            "[not_implemented] direct transpile is not ready",
        )
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "not_implemented")

    def test_direct_e2e_compile_fail_maps_to_regression(self) -> None:
        row = build_direct_e2e_summary_row(
            "test/fixtures/core/add.py",
            "compile_fail",
            "compile failed",
        )
        self.assertEqual(row.top_level_category, "regression")
        self.assertEqual(row.detail_category, "direct_compile_fail")

    def test_stage2_missing_binary_maps_to_regression(self) -> None:
        row = build_stage2_summary_row("stage2_binary", "missing_binary", "/tmp/missing")
        self.assertEqual(row.top_level_category, "regression")
        self.assertEqual(row.detail_category, "missing_output")

    def test_stage2_diff_known_diff_maps_to_known_block(self) -> None:
        row = build_stage2_diff_summary_row("test/fixtures/core/add.py", "known_diff", "expected diff")
        self.assertEqual(row.top_level_category, "known_block")
        self.assertEqual(row.detail_category, "known_block")

    def test_render_summary_block_skips_pass_rows_but_keeps_pass_aggregate(self) -> None:
        lines = render_summary_block(
            "direct_e2e",
            [build_summary_row("direct_e2e", "test/fixtures/core/add.py", "pass", "")],
            skip_pass=True,
        )
        self.assertEqual(lines[0], "[direct_e2e summary]")
        self.assertIn("subject=all", lines[1])
        self.assertIn("category=pass", lines[1])
        self.assertIn("detail=pass", lines[1])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.compiler import backend_registry_diagnostics as registry_diagnostics
from tools.selfhost_parity_summary import build_direct_e2e_summary_row
from tools.selfhost_parity_summary import build_stage2_diff_summary_row
from tools.selfhost_parity_summary import build_summary_row


def _row_contract(row: object) -> tuple[str, str]:
    return (row.top_level_category, row.detail_category)


class BackendRegistrySelfhostContractGuardTest(unittest.TestCase):
    def test_known_block_contract_matches_between_host_and_selfhost_lanes(self) -> None:
        cases = [
            {
                "host_message": "unsupported target: scala",
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    "[unsupported_by_design] rewrite using supported form",
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    "RuntimeError: unsupported target: scala",
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "unsupported_by_design",
                    "[unsupported_by_design] stage1 runner intentionally unavailable",
                ),
                "expected": ("known_block", "unsupported_by_design"),
            },
            {
                "host_message": "preview backend: scala emitter is gated",
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    "preview backend: sample target is intentionally blocked",
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    "preview backend: stage2 bridge intentionally unavailable",
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "preview_only",
                    "preview backend: stage1 route is intentionally gated",
                ),
                "expected": ("known_block", "preview_only"),
            },
        ]

        for case in cases:
            with self.subTest(host_message=case["host_message"]):
                self.assertEqual(
                    registry_diagnostics.classify_registry_diagnostic(case["host_message"]),
                    case["expected"],
                )
                self.assertEqual(_row_contract(case["direct_row"]), case["expected"])
                self.assertEqual(_row_contract(case["stage2_diff_row"]), case["expected"])
                self.assertEqual(_row_contract(case["multilang_row"]), case["expected"])

    def test_toolchain_missing_contract_matches_between_host_and_selfhost_summary_lane(self) -> None:
        expected = ("toolchain_missing", "toolchain_missing")
        self.assertEqual(
            registry_diagnostics.classify_registry_diagnostic("clang++ not found"),
            expected,
        )
        self.assertEqual(
            _row_contract(
                build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "toolchain_missing",
                    "clang++ not found",
                )
            ),
            expected,
        )


if __name__ == "__main__":
    unittest.main()

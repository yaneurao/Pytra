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
                "host_message": registry_diagnostics.unsupported_target_message("scala"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_target_message("scala"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_target_message("scala"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "unsupported_by_design",
                    registry_diagnostics.unsupported_target_message("scala"),
                ),
                "expected": ("known_block", "unsupported_by_design"),
            },
            {
                "host_message": registry_diagnostics.unsupported_target_profile_message("scala/preview"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_target_profile_message("scala/preview"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_target_profile_message("scala/preview"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "unsupported_by_design",
                    registry_diagnostics.unsupported_target_profile_message("scala/preview"),
                ),
                "expected": ("known_block", "unsupported_by_design"),
            },
            {
                "host_message": registry_diagnostics.unsupported_noncpp_build_target_message("swift"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_noncpp_build_target_message("swift"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_noncpp_build_target_message("swift"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "swift",
                    "unsupported_by_design",
                    registry_diagnostics.unsupported_noncpp_build_target_message("swift"),
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

    def test_regression_contract_stays_regression_across_host_and_selfhost_lanes(self) -> None:
        cases = [
            {
                "host_message": registry_diagnostics.unsupported_backend_symbol_ref_message("broken.symbol"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_backend_symbol_ref_message("broken.symbol"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_backend_symbol_ref_message("broken.symbol"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "regression",
                    registry_diagnostics.unsupported_backend_symbol_ref_message("broken.symbol"),
                ),
                "expected_detail_categories": (
                    "regression",
                    "sample_transpile_fail",
                    "host_transpile_fail",
                    "regression",
                ),
            },
            {
                "host_message": registry_diagnostics.unsupported_runtime_hook_key_message("broken_hook"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_runtime_hook_key_message("broken_hook"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_runtime_hook_key_message("broken_hook"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "regression",
                    registry_diagnostics.unsupported_runtime_hook_key_message("broken_hook"),
                ),
                "expected_detail_categories": (
                    "regression",
                    "sample_transpile_fail",
                    "host_transpile_fail",
                    "regression",
                ),
            },
            {
                "host_message": registry_diagnostics.unsupported_program_writer_key_message("broken_writer"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_program_writer_key_message("broken_writer"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_program_writer_key_message("broken_writer"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "regression",
                    registry_diagnostics.unsupported_program_writer_key_message("broken_writer"),
                ),
                "expected_detail_categories": (
                    "regression",
                    "sample_transpile_fail",
                    "host_transpile_fail",
                    "regression",
                ),
            },
            {
                "host_message": registry_diagnostics.unsupported_emit_kind_message("broken_emit"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_emit_kind_message("broken_emit"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_emit_kind_message("broken_emit"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "regression",
                    registry_diagnostics.unsupported_emit_kind_message("broken_emit"),
                ),
                "expected_detail_categories": (
                    "regression",
                    "sample_transpile_fail",
                    "host_transpile_fail",
                    "regression",
                ),
            },
            {
                "host_message": registry_diagnostics.unsupported_runtime_hook_kind_message("broken_hook_kind"),
                "direct_row": build_direct_e2e_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "selfhost_transpile_fail",
                    registry_diagnostics.unsupported_runtime_hook_kind_message("broken_hook_kind"),
                ),
                "stage2_diff_row": build_stage2_diff_summary_row(
                    "sample/py/01_mandelbrot.py",
                    "host_transpile_fail",
                    registry_diagnostics.unsupported_runtime_hook_kind_message("broken_hook_kind"),
                ),
                "multilang_row": build_summary_row(
                    "multilang_stage1",
                    "scala",
                    "regression",
                    registry_diagnostics.unsupported_runtime_hook_kind_message("broken_hook_kind"),
                ),
                "expected_detail_categories": (
                    "regression",
                    "sample_transpile_fail",
                    "host_transpile_fail",
                    "regression",
                ),
            },
        ]

        for case in cases:
            with self.subTest(host_message=case["host_message"]):
                host_contract = registry_diagnostics.classify_registry_diagnostic(case["host_message"])
                self.assertEqual(host_contract, ("regression", "regression"))
                self.assertEqual(case["direct_row"].top_level_category, "regression")
                self.assertEqual(case["stage2_diff_row"].top_level_category, "regression")
                self.assertEqual(case["multilang_row"].top_level_category, "regression")
                self.assertEqual(
                    (
                        host_contract[1],
                        case["direct_row"].detail_category,
                        case["stage2_diff_row"].detail_category,
                        case["multilang_row"].detail_category,
                    ),
                    case["expected_detail_categories"],
                )


if __name__ == "__main__":
    unittest.main()

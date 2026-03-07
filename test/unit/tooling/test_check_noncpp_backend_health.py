from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_noncpp_backend_health as health_mod


class CheckNonCppBackendHealthTest(unittest.TestCase):
    def test_resolve_selected_specs_accepts_family_and_explicit_targets(self) -> None:
        wave1 = health_mod._resolve_selected_specs(family_args=["wave1"], targets_arg="")
        explicit = health_mod._resolve_selected_specs(family_args=["wave1"], targets_arg="nim,js")

        self.assertEqual([item.target for item in wave1], ["rs", "cs", "js", "ts"])
        self.assertEqual([item.target for item in explicit], ["nim", "js"])

    def test_collect_target_health_marks_static_failure_as_primary_for_all_targets(self) -> None:
        spec = health_mod.TARGET_SPECS["js"]
        with patch.object(
            health_mod,
            "_run_static_contract",
            return_value=health_mod.StepResult("fail", "static failed"),
        ), patch.object(
            health_mod,
            "_run_common_smoke",
            side_effect=AssertionError("common smoke must not run when static fails"),
        ):
            rows = health_mod.collect_target_health([spec], skip_parity=False)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_failure, "static_contract_fail")
        self.assertEqual(rows[0].target_smoke, "blocked")
        self.assertEqual(rows[0].transpile, "blocked")
        self.assertEqual(rows[0].parity, "blocked")

    def test_collect_target_health_marks_toolchain_missing_from_parity(self) -> None:
        spec = health_mod.TARGET_SPECS["cs"]
        with patch.object(
            health_mod,
            "_run_static_contract",
            return_value=health_mod.StepResult("pass", ""),
        ), patch.object(
            health_mod,
            "_run_common_smoke",
            return_value=health_mod.StepResult("pass", ""),
        ), patch.object(
            health_mod,
            "_run_target_smoke",
            return_value=health_mod.StepResult("pass", ""),
        ), patch.object(
            health_mod,
            "_run_target_transpile",
            return_value=health_mod.StepResult("pass", ""),
        ), patch.object(
            health_mod,
            "_run_target_parity",
            return_value=health_mod.StepResult("toolchain_missing", "missing toolchain"),
        ):
            rows = health_mod.collect_target_health([spec], skip_parity=False)
            families = health_mod.summarize_families(rows)

        self.assertEqual(rows[0].primary_failure, "toolchain_missing")
        self.assertEqual(rows[0].parity, "toolchain_missing")
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0].status, "green")
        self.assertEqual(families[0].toolchain_missing_targets, 1)
        self.assertEqual(families[0].broken_targets, 0)

    def test_classify_parity_summary_returns_ok_and_toolchain_missing(self) -> None:
        ok_summary = {
            "case_total": 18,
            "case_pass": 18,
            "case_fail": 0,
            "records": [{"case": "01_mandelbrot", "target": "js", "category": "ok", "detail": ""}],
        }
        missing_summary = {
            "case_total": 18,
            "case_pass": 18,
            "case_fail": 0,
            "records": [
                {
                    "case": "01_mandelbrot",
                    "target": "cs",
                    "category": "toolchain_missing",
                    "detail": "missing toolchain",
                }
            ],
        }

        ok_result = health_mod._classify_parity_summary(ok_summary, "js")
        missing_result = health_mod._classify_parity_summary(missing_summary, "cs")

        self.assertEqual(ok_result.status, "ok")
        self.assertIn("cases=18/18", ok_result.detail)
        self.assertEqual(missing_result.status, "toolchain_missing")

    def test_main_writes_summary_json_and_returns_nonzero_for_broken_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "summary.json"
            argv = [
                "check_noncpp_backend_health.py",
                "--targets",
                "js,cs",
                "--summary-json",
                str(summary_path),
            ]
            with patch.object(
                health_mod,
                "collect_target_health",
                return_value=[
                    health_mod.TargetHealth(
                        target="js",
                        family="wave1",
                        static_contract="pass",
                        common_smoke="pass",
                        target_smoke="pass",
                        transpile="fail",
                        parity="blocked",
                        primary_failure="transpile_fail",
                        detail="traceback",
                    ),
                    health_mod.TargetHealth(
                        target="cs",
                        family="wave1",
                        static_contract="pass",
                        common_smoke="pass",
                        target_smoke="pass",
                        transpile="pass",
                        parity="toolchain_missing",
                        primary_failure="toolchain_missing",
                        detail="missing toolchain",
                    ),
                ],
            ), patch.object(
                sys,
                "argv",
                argv,
            ), patch(
                "sys.stdout",
                new_callable=io.StringIO,
            ) as stdout:
                rc = health_mod.main()
            out = stdout.getvalue()
            summary_obj = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertIn("FAMILY wave1 status=broken", out)
        self.assertEqual(summary_obj["broken_targets"], 1)
        self.assertEqual(summary_obj["toolchain_missing_targets"], 1)


if __name__ == "__main__":
    unittest.main()

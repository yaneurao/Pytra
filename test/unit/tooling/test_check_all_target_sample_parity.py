from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.check_all_target_sample_parity import (
    build_group_command,
    group_names,
    merge_summary_json,
    parse_groups,
)


class CheckAllTargetSampleParityTest(unittest.TestCase):
    def test_parse_groups_defaults_to_all_groups(self) -> None:
        self.assertEqual(parse_groups(""), list(group_names()))

    def test_parse_groups_rejects_unknown_name(self) -> None:
        with self.assertRaises(ValueError):
            parse_groups("cpp,unknown")

    def test_build_group_command_adds_cpp_codegen_opt_only_for_cpp_group(self) -> None:
        cpp_cmd = build_group_command(
            "cpp",
            east3_opt_level="2",
            cpp_codegen_opt="3",
            summary_json=Path("/tmp/cpp.json"),
        )
        js_cmd = build_group_command(
            "js_ts",
            east3_opt_level="2",
            cpp_codegen_opt="3",
            summary_json=None,
        )
        self.assertIn("--cpp-codegen-opt", cpp_cmd)
        self.assertIn("/tmp/cpp.json", cpp_cmd)
        self.assertNotIn("--cpp-codegen-opt", js_cmd)
        self.assertIn("--all-samples", cpp_cmd)
        self.assertIn("--ignore-unstable-stdout", cpp_cmd)

    def test_merge_summary_json_accumulates_groups(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "cpp.json").write_text(
                json.dumps(
                    {
                        "targets": ["cpp"],
                        "cases": ["01_mandelbrot"],
                        "case_total": 1,
                        "case_pass": 1,
                        "case_fail": 0,
                        "category_counts": {"ok": 1},
                        "records": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "js_ts.json").write_text(
                json.dumps(
                    {
                        "targets": ["js", "ts"],
                        "cases": ["01_mandelbrot"],
                        "case_total": 1,
                        "case_pass": 1,
                        "case_fail": 0,
                        "category_counts": {"ok": 2},
                        "records": [{"case": "01_mandelbrot", "target": "js", "category": "ok", "detail": ""}],
                    }
                ),
                encoding="utf-8",
            )
            merged = merge_summary_json(root, ["cpp", "js_ts"], "2", "3")

        self.assertEqual(merged["case_total"], 2)
        self.assertEqual(merged["case_pass"], 2)
        self.assertEqual(merged["case_fail"], 0)
        self.assertEqual(merged["category_counts"], {"ok": 3})
        self.assertEqual(merged["targets"], ["cpp", "js", "ts"])


if __name__ == "__main__":
    unittest.main()

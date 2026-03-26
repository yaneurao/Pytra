from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
REGENERATE_GOLDEN = ROOT / "tools" / "regenerate_golden.py"


def _load_regenerate_golden_module():
    spec = importlib.util.spec_from_file_location("regenerate_golden", REGENERATE_GOLDEN)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load regenerate_golden module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RegenerateGoldenCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rg = _load_regenerate_golden_module()

    def test_should_report_progress_uses_interval_and_completion(self) -> None:
        self.assertFalse(self.rg._should_report_progress(0, 25, 10))
        self.assertFalse(self.rg._should_report_progress(9, 25, 10))
        self.assertTrue(self.rg._should_report_progress(10, 25, 10))
        self.assertFalse(self.rg._should_report_progress(19, 25, 10))
        self.assertTrue(self.rg._should_report_progress(25, 25, 10))
        self.assertFalse(self.rg._should_report_progress(10, 25, 0))

    def test_print_progress_formats_fraction(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.rg._print_progress("east2", 10, 123)
        self.assertEqual(buf.getvalue(), "  east2 progress: 10/123\n")

    def test_main_parses_progress_every_and_forwards_to_regenerate(self) -> None:
        with patch.object(self.rg, "regenerate", return_value=0) as mock_regenerate, patch.object(
            sys, "argv", ["regenerate_golden.py", "--case-root=fixture", "--progress-every=25"]
        ):
            code = self.rg.main()

        self.assertEqual(code, 0)
        mock_regenerate.assert_called_once_with("fixture", progress_every=25)

    def test_main_rejects_negative_progress_every(self) -> None:
        with patch.object(sys, "argv", ["regenerate_golden.py", "--progress-every=-1"]):
            code = self.rg.main()

        self.assertEqual(code, 1)


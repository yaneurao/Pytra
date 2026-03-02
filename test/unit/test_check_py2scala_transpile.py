"""Unit tests for tools/check_py2scala_transpile.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "check_py2scala_transpile.py"

SPEC = importlib.util.spec_from_file_location("check_py2scala_transpile", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("failed to load check_py2scala_transpile.py")
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class CheckPy2ScalaTranspileTest(unittest.TestCase):
    def test_default_expected_failures_drop_stale_untyped_param(self) -> None:
        self.assertNotIn("test/fixtures/signature/ng_untyped_param.py", MOD.DEFAULT_EXPECTED_FAILURES)
        self.assertIn("test/fixtures/signature/ng_varargs.py", MOD.DEFAULT_EXPECTED_FAILURES)

    def test_extract_user_error_category_parses_marker(self) -> None:
        text = (
            "RuntimeError: __PYTRA_USER_ERROR__|unsupported_by_design|This syntax is unsupported by language design.\n"
            "unsupported_syntax: object receiver attribute/method access is forbidden by language constraints\n"
        )
        self.assertEqual(MOD._extract_user_error_category(text), "unsupported_by_design")

    def test_evaluate_expected_failure_rejects_unexpected_pass(self) -> None:
        spec = MOD.ExpectedFailureSpec(category="user_syntax_error", contains="variadic args parameter")
        run = MOD.RunResult(ok=True, message="", raw="", category="")
        msg = MOD._evaluate_expected_failure("test/fixtures/signature/ng_varargs.py", run, spec)
        self.assertIn("unexpected pass", msg)

    def test_evaluate_expected_failure_rejects_category_mismatch(self) -> None:
        spec = MOD.ExpectedFailureSpec(category="user_syntax_error", contains="variadic args parameter")
        run = MOD.RunResult(
            ok=False,
            message="unsupported_by_design: This syntax is unsupported by language design.",
            raw="RuntimeError: __PYTRA_USER_ERROR__|unsupported_by_design|This syntax is unsupported by language design.",
            category="unsupported_by_design",
        )
        msg = MOD._evaluate_expected_failure("test/fixtures/signature/ng_varargs.py", run, spec)
        self.assertIn("unexpected error category", msg)

    def test_evaluate_expected_failure_accepts_matching_category_and_detail(self) -> None:
        spec = MOD.ExpectedFailureSpec(category="user_syntax_error", contains="variadic args parameter")
        run = MOD.RunResult(
            ok=False,
            message="user_syntax_error: Python syntax error.",
            raw=(
                "RuntimeError: __PYTRA_USER_ERROR__|user_syntax_error|Python syntax error.\n"
                "unsupported_syntax: self_hosted parser cannot parse variadic args parameter: *args: int at 3:0\n"
            ),
            category="user_syntax_error",
        )
        msg = MOD._evaluate_expected_failure("test/fixtures/signature/ng_varargs.py", run, spec)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()

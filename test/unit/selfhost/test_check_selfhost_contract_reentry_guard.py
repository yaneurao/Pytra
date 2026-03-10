from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_selfhost_contract_reentry_guard as guard_mod


class CheckSelfhostContractReentryGuardTest(unittest.TestCase):
    def test_reentry_guard_steps_cover_host_and_selfhost_lanes(self) -> None:
        steps = guard_mod.build_reentry_guard_steps()
        self.assertEqual(
            [label for label, _ in steps],
            [
                "host-selfhost-contract-guard",
                "host-entrypoint-contract",
                "selfhost-source-contract",
                "selfhost-build-verify-contract",
                "selfhost-diff-contract",
                "selfhost-stage2-diff-contract",
            ],
        )
        self.assertEqual(steps[0][1][-1], "test_backend_registry_selfhost_contract_guard.py")
        self.assertEqual(steps[1][1][-1], "test_py2x_entrypoints_contract.py")
        self.assertEqual(steps[2][1][-1], "test_prepare_selfhost_source.py")
        self.assertEqual(steps[3][1][-1], "test_selfhost_build_verify_tools.py")
        self.assertEqual(steps[4][1][-1], "test_check_selfhost_cpp_diff.py")
        self.assertEqual(steps[5][1][-1], "test_check_selfhost_stage2_cpp_diff.py")

    def test_run_reentry_guard_steps_stops_on_first_failure(self) -> None:
        steps = [
            ("first", ["python3", "-m", "unittest", "discover", "-p", "first.py"]),
            ("second", ["python3", "-m", "unittest", "discover", "-p", "second.py"]),
        ]
        calls: list[list[str]] = []

        class _Result:
            def __init__(self, returncode: int) -> None:
                self.returncode = returncode

        def _fake_run(cmd: list[str], cwd: str | None = None):
            calls.append(cmd)
            return _Result(7 if cmd[-1] == "first.py" else 0)

        with patch.object(guard_mod.subprocess, "run", side_effect=_fake_run):
            self.assertEqual(guard_mod.run_reentry_guard_steps(steps), 7)
        self.assertEqual(calls, [steps[0][1]])

    def test_run_reentry_guard_steps_dry_run_skips_subprocess(self) -> None:
        with patch.object(guard_mod.subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
            self.assertEqual(guard_mod.run_reentry_guard_steps(guard_mod.build_reentry_guard_steps(), dry_run=True), 0)


if __name__ == "__main__":
    unittest.main()

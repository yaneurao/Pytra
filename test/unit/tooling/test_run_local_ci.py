from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import run_local_ci as run_local_ci_mod


class RunLocalCiTest(unittest.TestCase):
    def test_build_steps_keeps_selfhost_contract_reentry_guard_before_selfhost_build_and_diff(self) -> None:
        steps = run_local_ci_mod.build_steps()
        reentry_guard = ["python3", "tools/check_selfhost_contract_reentry_guard.py"]
        build_selfhost = ["python3", "tools/build_selfhost.py"]
        selfhost_diff = ["python3", "tools/check_selfhost_cpp_diff.py", "--mode", "strict"]
        selfhost_stage2_diff = [
            "python3",
            "tools/check_selfhost_stage2_cpp_diff.py",
            "--mode",
            "strict",
        ]

        reentry_index = steps.index(reentry_guard)
        self.assertLess(reentry_index, steps.index(build_selfhost))
        self.assertLess(reentry_index, steps.index(selfhost_diff))
        self.assertLess(reentry_index, steps.index(selfhost_stage2_diff))

    def test_build_steps_keeps_selfhost_contract_reentry_guard_after_multilang_suite(self) -> None:
        steps = run_local_ci_mod.build_steps()
        self.assertLess(
            steps.index(["python3", "tools/check_multilang_selfhost_suite.py"]),
            steps.index(["python3", "tools/check_selfhost_contract_reentry_guard.py"]),
        )


if __name__ == "__main__":
    unittest.main()

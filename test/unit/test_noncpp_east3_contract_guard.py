"""Guard tests for non-cpp EAST3 default/compatibility contract."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class NonCppEast3ContractGuardTest(unittest.TestCase):
    def test_noncpp_east3_contract_static_check_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_noncpp_east3_contract.py", "--skip-transpile"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"{cp.stdout}\n{cp.stderr}")
        self.assertIn("static contract checks passed", cp.stdout)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_residual_thin_seam_handoff_contract as handoff_mod


class CheckCppPyRuntimeResidualThinSeamHandoffContractTest(unittest.TestCase):
    def test_handoff_contract_is_fixed(self) -> None:
        self.assertEqual(
            handoff_mod.ACTIVE_TASK_ID,
            "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01",
        )
        self.assertEqual(
            handoff_mod.ACTIVE_PLAN_PATH,
            "docs/ja/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md",
        )
        self.assertEqual(
            handoff_mod.BUNDLE_ORDER,
            (
                "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S1-01",
                "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-01",
                "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-02",
                "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S3-01",
            ),
        )
        self.assertEqual(
            handoff_mod.REPRESENTATIVE_CHECKS,
            (
                "tools/check_cpp_pyruntime_header_surface.py",
                "tools/check_cpp_pyruntime_contract_inventory.py",
                "tools/check_crossruntime_pyruntime_emitter_inventory.py",
                "tools/check_cpp_pyruntime_residual_thin_seam_contract.py",
            ),
        )
        self.assertEqual(
            handoff_mod.REPRESENTATIVE_TEST_FILES,
            (
                "test/unit/tooling/test_check_cpp_pyruntime_header_surface.py",
                "test/unit/tooling/test_check_cpp_pyruntime_contract_inventory.py",
                "test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py",
                "test/unit/tooling/test_check_cpp_pyruntime_residual_thin_seam_contract.py",
            ),
        )
        self.assertEqual(handoff_mod._collect_handoff_issues(), [])


if __name__ == "__main__":
    unittest.main()

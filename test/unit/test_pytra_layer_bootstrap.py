from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.pytra.frontends as frontends
import src.pytra.ir as ir


class PytraLayerBootstrapTest(unittest.TestCase):
    def test_frontends_exports(self) -> None:
        self.assertTrue(callable(frontends.add_common_transpile_args))
        self.assertTrue(callable(frontends.normalize_common_transpile_args))
        self.assertTrue(callable(frontends.load_east3_document))

    def test_ir_exports(self) -> None:
        self.assertTrue(callable(ir.lower_east2_to_east3))
        self.assertTrue(callable(ir.optimize_east3_document))
        self.assertTrue(callable(ir.render_east3_opt_trace))
        self.assertTrue(callable(ir.load_east_from_path))


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path as StdPath

ROOT = StdPath(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pylib.std import glob as py_glob
from src.pylib.std import os as py_os


class PyLibOsGlobTest(unittest.TestCase):
    def test_os_path_subset(self) -> None:
        p = py_os.path.join("a", "b.txt")
        self.assertEqual(py_os.path.basename(p), "b.txt")
        root, ext = py_os.path.splitext(p)
        self.assertTrue(root.endswith("a/b") or root.endswith("a\\b"))
        self.assertEqual(ext, ".txt")

    def test_glob(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d = StdPath(tmpdir)
            (d / "x.txt").write_text("x", encoding="utf-8")
            (d / "y.bin").write_text("y", encoding="utf-8")
            out = py_glob.glob(str(d / "*.txt"))
            self.assertEqual(len(out), 1)
            self.assertTrue(out[0].endswith("x.txt"))


if __name__ == "__main__":
    unittest.main()


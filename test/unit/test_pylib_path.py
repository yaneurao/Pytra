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

from src.pytra.std.pathlib import Path


class PyLibPathTest(unittest.TestCase):
    def test_basic_properties(self) -> None:
        p = Path("a/b/file.txt")
        self.assertEqual(p.name, "file.txt")
        self.assertEqual(p.stem, "file")
        self.assertEqual(p.suffix, ".txt")
        self.assertEqual(str(p.parent), "a/b")

    def test_join_and_resolve(self) -> None:
        p = Path("a") / "b" / "c.txt"
        self.assertEqual(str(p), "a/b/c.txt")
        self.assertTrue(str(p.resolve()).endswith("a/b/c.txt"))

    def test_text_io_and_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            p = d / "x.txt"
            p.write_text("hello", encoding="utf-8")
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(encoding="utf-8"), "hello")

    def test_mkdir_and_glob(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "a" / "b"
            d.mkdir(parents=True, exist_ok=True)
            (d / "f1.txt").write_text("1")
            (d / "f2.py").write_text("2")
            names = sorted(x.name for x in d.glob("*.txt"))
            self.assertEqual(names, ["f1.txt"])

    def test_parents_index(self) -> None:
        p = Path("a/b/c/d.txt")
        self.assertEqual(str(p.parents[0]), "a/b/c")
        self.assertEqual(str(p.parents[1]), "a/b")


if __name__ == "__main__":
    unittest.main()


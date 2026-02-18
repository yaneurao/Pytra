"""py2cpp の主要互換機能を実行レベルで確認する回帰テスト。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import load_east, transpile_to_cpp

def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def transpile(input_py: Path, output_cpp: Path) -> None:
    east = load_east(input_py)
    cpp = transpile_to_cpp(east)
    output_cpp.write_text(cpp, encoding="utf-8")


class Py2CppFeatureTest(unittest.TestCase):
    def test_class_storage_strategy_case15_case34(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)

            case15_py = find_fixture_case("case15_class_member")
            case15_cpp = work / "case15.cpp"
            transpile(case15_py, case15_cpp)
            case15_txt = case15_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Counter {", case15_txt)
            self.assertIn("Counter c = Counter();", case15_txt)
            self.assertNotIn("rc<Counter>", case15_txt)

            case34_py = find_fixture_case("case34_gc_reassign")
            case34_cpp = work / "case34.cpp"
            transpile(case34_py, case34_cpp)
            case34_txt = case34_cpp.read_text(encoding="utf-8")
            self.assertIn("struct Tracked : public PyObj {", case34_txt)
            self.assertIn("rc<Tracked> a = ", case34_txt)
            self.assertIn("rc_new<Tracked>(\"A\")", case34_txt)
            self.assertIn("a = b;", case34_txt)


if __name__ == "__main__":
    unittest.main()

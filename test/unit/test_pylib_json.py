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

from src.pylib.east_parts.east_io import load_east_from_path
from src.pylib import json


class PyLibJsonTest(unittest.TestCase):
    def test_loads_basic_object(self) -> None:
        obj = json.loads('{"a":1,"b":[true,false,null],"c":"x"}')
        self.assertIsInstance(obj, dict)
        self.assertEqual(obj.get("a"), 1)
        self.assertEqual(obj.get("b"), [True, False, None])
        self.assertEqual(obj.get("c"), "x")

    def test_loads_unicode_escape(self) -> None:
        obj = json.loads('{"s":"\\u3042"}')
        self.assertEqual(obj.get("s"), "あ")

    def test_dumps_compact_and_pretty(self) -> None:
        obj = {"x": [1, 2], "y": "z"}
        compact = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        self.assertIn('"x":[1,2]', compact)
        pretty = json.dumps(obj, ensure_ascii=False, indent=2)
        self.assertIn("\n", pretty)
        self.assertIn('  "x"', pretty)

    def test_east_io_reads_json_via_pylib_json(self) -> None:
        payload = {"kind": "Module", "body": [], "functions": [], "classes": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "mod.east.json"
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            out = load_east_from_path(p)
            self.assertEqual(out.get("kind"), "Module")


if __name__ == "__main__":
    unittest.main()

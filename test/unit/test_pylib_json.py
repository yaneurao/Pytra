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

    def test_loads_numbers_and_exponent(self) -> None:
        obj = json.loads('{"i":-12,"f":3.25,"e":1.5e2,"ez":2E-1}')
        self.assertEqual(obj.get("i"), -12)
        self.assertAlmostEqual(obj.get("f"), 3.25)
        self.assertAlmostEqual(obj.get("e"), 150.0)
        self.assertAlmostEqual(obj.get("ez"), 0.2)

    def test_loads_string_escapes(self) -> None:
        obj = json.loads('{"s":"a\\\\b\\n\\t\\\"\\/"}')
        self.assertEqual(obj.get("s"), 'a\\b\n\t"/')

    def test_loads_nested_roundtrip(self) -> None:
        src = {
            "name": "alpha",
            "ok": True,
            "none": None,
            "vals": [1, 2, {"x": "y", "z": [False, 3.5]}],
        }
        txt = json.dumps(src, ensure_ascii=False, separators=(",", ":"))
        back = json.loads(txt)
        self.assertEqual(back, src)

    def test_loads_rejects_invalid_inputs(self) -> None:
        bad_cases = [
            "",
            "{",
            '{"a":1',
            '{"a",1}',
            '{"a":}',
            "[1,2,]",
            '{"a":tru}',
            '{"a":"\\x"}',
            '{"a":"\\u12G4"}',
            '{"a":1} trailing',
        ]
        for case in bad_cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    json.loads(case)

    def test_dumps_compact_and_pretty(self) -> None:
        obj = {"x": [1, 2], "y": "z"}
        compact = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        self.assertIn('"x":[1,2]', compact)
        pretty = json.dumps(obj, ensure_ascii=False, indent=2)
        self.assertIn("\n", pretty)
        self.assertIn('  "x"', pretty)

    def test_dumps_ensure_ascii(self) -> None:
        obj = {"s": "あ"}
        text_ascii = json.dumps(obj, ensure_ascii=True, separators=(",", ":"))
        text_utf8 = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        self.assertIn("\\u3042", text_ascii)
        self.assertIn("あ", text_utf8)

    def test_dumps_escapes_control_chars(self) -> None:
        obj = {"s": "\"\\\b\f\n\r\t"}
        out = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        self.assertIn('\\"', out)
        self.assertIn("\\\\", out)
        self.assertIn("\\b", out)
        self.assertIn("\\f", out)
        self.assertIn("\\n", out)
        self.assertIn("\\r", out)
        self.assertIn("\\t", out)

    def test_dumps_rejects_unsupported_type(self) -> None:
        with self.assertRaises(TypeError):
            json.dumps({"x": {1, 2, 3}})

    def test_east_io_reads_json_via_pylib_json(self) -> None:
        payload = {"kind": "Module", "body": [], "functions": [], "classes": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "mod.east.json"
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            out = load_east_from_path(p)
            self.assertEqual(out.get("kind"), "Module")


if __name__ == "__main__":
    unittest.main()

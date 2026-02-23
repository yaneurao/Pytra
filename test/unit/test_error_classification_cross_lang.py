"""Cross-language load_east error classification tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import py2cs
import py2go
import py2java
import py2js
import py2kotlin
import py2rs
import py2swift
import py2ts


MODULES = [
    py2rs,
    py2js,
    py2cs,
    py2go,
    py2java,
    py2ts,
    py2swift,
    py2kotlin,
]

PHASE2_MODULES = [
    py2cs,
    py2js,
    py2ts,
]


class ErrorClassificationCrossLanguageTest(unittest.TestCase):
    def test_invalid_json_root_is_classified_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.east.json"
            bad.write_text("[]", encoding="utf-8")
            for mod in MODULES:
                with self.subTest(module=mod.__name__):
                    with self.assertRaises(RuntimeError) as cm:
                        mod.load_east(bad)
                    self.assertIn("EAST json root must be object", str(cm.exception))

    def test_invalid_suffix_is_classified_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "input.txt"
            bad.write_text("x = 1\n", encoding="utf-8")
            for mod in MODULES:
                with self.subTest(module=mod.__name__):
                    with self.assertRaises(RuntimeError) as cm:
                        mod.load_east(bad)
                    self.assertIn("input must be .py or .json", str(cm.exception))

    def test_phase2_modules_accept_wrapped_east_json(self) -> None:
        payload = {"ok": True, "east": {"kind": "Module", "body": []}}
        with tempfile.TemporaryDirectory() as td:
            wrapped = Path(td) / "wrapped.east.json"
            wrapped.write_text(json.dumps(payload), encoding="utf-8")
            for mod in PHASE2_MODULES:
                with self.subTest(module=mod.__name__):
                    doc = mod.load_east(wrapped)
                    self.assertIsInstance(doc, dict)
                    self.assertEqual(doc.get("kind"), "Module")


if __name__ == "__main__":
    unittest.main()

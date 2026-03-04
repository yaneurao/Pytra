"""Cross-language load_east error classification tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compiler.transpile_cli import load_east3_document


TARGETS = [
    "rs",
    "js",
    "cs",
    "go",
    "java",
    "ts",
    "swift",
    "kotlin",
]

PHASE2_TARGETS = [
    "cs",
    "js",
    "ts",
]

PHASE3_TARGETS = [
    "go",
    "java",
    "swift",
    "kotlin",
]


def load_east_for_target(target_lang: str, input_path: Path) -> dict[str, object]:
    doc3 = load_east3_document(
        input_path,
        parser_backend="self_hosted",
        object_dispatch_mode="native",
        east3_opt_level="1",
        east3_opt_pass="",
        dump_east3_before_opt="",
        dump_east3_after_opt="",
        dump_east3_opt_trace="",
        target_lang=target_lang,
    )
    return doc3 if isinstance(doc3, dict) else {}


class ErrorClassificationCrossLanguageTest(unittest.TestCase):
    def test_invalid_json_root_is_classified_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.east.json"
            bad.write_text("[]", encoding="utf-8")
            for target in TARGETS:
                with self.subTest(target=target):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = load_east_for_target(target, bad)
                    self.assertIn("Invalid EAST JSON format.", str(cm.exception))

    def test_non_python_suffix_is_treated_as_source_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "input.txt"
            src.write_text("x = 1\n", encoding="utf-8")
            for target in TARGETS:
                with self.subTest(target=target):
                    doc = load_east_for_target(target, src)
                    self.assertIsInstance(doc, dict)
                    self.assertEqual(doc.get("kind"), "Module")

    def test_phase2_modules_accept_wrapped_east_json(self) -> None:
        payload = {"ok": True, "east": {"kind": "Module", "body": []}}
        with tempfile.TemporaryDirectory() as td:
            wrapped = Path(td) / "wrapped.east.json"
            wrapped.write_text(json.dumps(payload), encoding="utf-8")
            for target in PHASE2_TARGETS:
                with self.subTest(target=target):
                    doc = load_east_for_target(target, wrapped)
                    self.assertIsInstance(doc, dict)
                    self.assertEqual(doc.get("kind"), "Module")

    def test_phase3_modules_accept_wrapped_east_json(self) -> None:
        payload = {"ok": True, "east": {"kind": "Module", "body": []}}
        with tempfile.TemporaryDirectory() as td:
            wrapped = Path(td) / "wrapped.east.json"
            wrapped.write_text(json.dumps(payload), encoding="utf-8")
            for target in PHASE3_TARGETS:
                with self.subTest(target=target):
                    doc = load_east_for_target(target, wrapped)
                    self.assertIsInstance(doc, dict)
                    self.assertEqual(doc.get("kind"), "Module")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MANIFEST = ROOT / "tools" / "runtime_generation_manifest.json"


class RuntimeGenerationManifestTest(unittest.TestCase):
    def _load_manifest(self) -> dict[str, object]:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_exists_and_has_required_items(self) -> None:
        self.assertTrue(MANIFEST.exists())
        doc = self._load_manifest()
        items = doc.get("items")
        self.assertIsInstance(items, list)
        ids = {str(item.get("id")) for item in items if isinstance(item, dict)}
        self.assertIn("utils/png", ids)
        self.assertIn("utils/gif", ids)
        self.assertIn("std/time", ids)
        self.assertIn("std/json", ids)
        self.assertIn("std/pathlib", ids)
        self.assertIn("std/math", ids)

    def test_manifest_outputs_are_unique(self) -> None:
        doc = self._load_manifest()
        items = doc.get("items")
        self.assertIsInstance(items, list)
        outputs: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            targets = item.get("targets")
            if not isinstance(targets, list):
                continue
            for entry in targets:
                if not isinstance(entry, dict):
                    continue
                out = entry.get("output")
                if isinstance(out, str) and out != "":
                    outputs.append(out)
        self.assertEqual(len(outputs), len(set(outputs)))

    def test_cs_helper_postprocess_is_declared(self) -> None:
        doc = self._load_manifest()
        items = doc.get("items")
        self.assertIsInstance(items, list)
        helper_map: dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", ""))
            targets = item.get("targets")
            if not isinstance(targets, list):
                continue
            for entry in targets:
                if not isinstance(entry, dict):
                    continue
                if entry.get("target") != "cs":
                    continue
                helper_map[item_id] = str(entry.get("helper_name", ""))
                self.assertEqual(entry.get("postprocess"), "cs_program_to_helper")
        self.assertEqual(helper_map.get("utils/png"), "png_helper")
        self.assertEqual(helper_map.get("utils/gif"), "gif_helper")


if __name__ == "__main__":
    unittest.main()

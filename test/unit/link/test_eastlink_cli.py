from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pytra.std import json

import src.eastlink as eastlink_mod


def _east3_doc(module_id: str, dispatch_mode: str = "native") -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "meta": {
            "dispatch_mode": dispatch_mode,
            "module_id": module_id,
        },
        "body": [],
    }


class EastlinkCliTest(unittest.TestCase):
    def test_eastlink_writes_link_output_and_linked_modules(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_dir = root / "east3"
            build_dir.mkdir(parents=True, exist_ok=True)
            main_east = build_dir / "app.main.east3.json"
            helper_east = build_dir / "app.helper.east3.json"
            main_east.write_text(json.dumps(_east3_doc("app.main"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            helper_east.write_text(json.dumps(_east3_doc("app.helper"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            link_input = root / "link-input.json"
            link_input.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_input.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "path": str(main_east.relative_to(root)).replace("\\", "/"),
                                "source_path": "sample/py/main.py",
                                "is_entry": True,
                            },
                            {
                                "module_id": "app.helper",
                                "path": str(helper_east.relative_to(root)).replace("\\", "/"),
                                "source_path": "sample/py/helper.py",
                                "is_entry": False,
                            },
                        ],
                        "options": {"east3_opt_level": "1"},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            out_dir = root / "linked-out"
            rc = eastlink_mod.main([str(link_input), "--output-dir", str(out_dir)])

            self.assertEqual(rc, 0)
            link_output = json.loads((out_dir / "link-output.json").read_text(encoding="utf-8"))
            self.assertEqual(link_output["schema"], "pytra.link_output.v1")
            self.assertEqual([item["module_id"] for item in link_output["modules"]], ["app.helper", "app.main"])
            self.assertTrue((out_dir / "linked" / "app" / "main.east3.json").exists())
            main_linked = json.loads((out_dir / "linked" / "app" / "main.east3.json").read_text(encoding="utf-8"))
            self.assertIn("linked_program_v1", main_linked["meta"])
            self.assertEqual(main_linked["meta"]["linked_program_v1"]["module_id"], "app.main")

    def test_eastlink_returns_error_for_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rc = eastlink_mod.main([str(root / "missing-link-input.json")])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

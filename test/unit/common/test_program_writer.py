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

from src.toolchain.emit.common.program_writer import write_single_file_program


class SingleFileProgramWriterTest(unittest.TestCase):
    def test_write_single_file_program_ignores_helper_module(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "demo.txt"
            result = write_single_file_program(
                {
                    "program_id": "pkg.demo",
                    "entry_modules": ["pkg.demo"],
                    "modules": [
                        {
                            "module_id": "__pytra_helper__.demo",
                            "kind": "helper",
                            "label": "demo_helper",
                            "extension": ".txt",
                            "text": "// helper\n",
                            "is_entry": False,
                            "dependencies": [],
                            "metadata": {"helper_id": "demo", "owner_module_id": "pkg.demo"},
                        },
                        {
                            "module_id": "pkg.demo",
                            "kind": "user",
                            "label": "demo",
                            "extension": ".txt",
                            "text": "// main\n",
                            "is_entry": True,
                            "dependencies": [],
                            "metadata": {},
                        },
                    ],
                },
                out_path,
                {},
            )

            self.assertEqual(result["layout_mode"], "single_file")
            self.assertEqual(out_path.read_text(encoding="utf-8"), "// main\n")


if __name__ == "__main__":
    unittest.main()

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

from src.toolchain.emit.cpp.program_writer import write_cpp_program
from src.toolchain.emit.cpp.program_writer import write_cpp_rendered_program


class CppProgramWriterTest(unittest.TestCase):
    def test_write_cpp_rendered_program_generates_manifest_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "out"
            entry_path = str(root / "main.py")
            result = write_cpp_rendered_program(
                out_dir,
                [
                    {
                        "module": entry_path,
                        "label": "main",
                        "header_text": "// hdr main\n",
                        "source_text": '#include "pytra_multi_prelude.h"\nvoid main_body() {}\n',
                        "is_entry": True,
                    },
                    {
                        "module": str(root / "helper.py"),
                        "label": "helper",
                        "header_text": "// hdr helper\n",
                        "source_text": '#include "pytra_multi_prelude.h"\nvoid helper_body() {}\n',
                        "is_entry": False,
                    },
                ],
                entry=entry_path,
                entry_modules=["pkg.main"],
                program_id="pkg.main",
            )

            self.assertEqual(result["layout_mode"], "multi_file")
            self.assertTrue((out_dir / "include" / "pytra_multi_prelude.h").exists())
            self.assertTrue((out_dir / "include" / "main.h").exists())
            self.assertTrue((out_dir / "src" / "main.cpp").exists())
            self.assertEqual(result["manifest"], str(out_dir / "manifest.json"))
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["entry"], entry_path)
            self.assertEqual(len(manifest["modules"]), 2)
            self.assertEqual(manifest["modules"][0]["label"], "main")
            self.assertTrue(manifest["modules"][0]["is_entry"])

    def test_write_cpp_program_falls_back_to_single_file_writer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_cpp = root / "demo.cpp"
            result = write_cpp_program(
                {
                    "program_id": "pkg.demo",
                    "entry_modules": ["pkg.demo"],
                    "modules": [
                        {
                            "module_id": "pkg.demo",
                            "label": "demo",
                            "extension": ".cpp",
                            "text": "// demo\n",
                            "is_entry": True,
                            "dependencies": [],
                            "metadata": {},
                        }
                    ],
                },
                out_cpp,
                {},
            )

            self.assertEqual(result["layout_mode"], "single_file")
            self.assertTrue(out_cpp.exists())
            self.assertEqual(out_cpp.read_text(encoding="utf-8"), "// demo\n")

    def test_write_cpp_rendered_program_preserves_helper_manifest_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "out"
            result = write_cpp_rendered_program(
                out_dir,
                [
                    {
                        "module": str(root / "main.py"),
                        "kind": "user",
                        "label": "main",
                        "header_text": "// hdr main\n",
                        "source_text": '#include "pytra_multi_prelude.h"\nvoid main_body() {}\n',
                        "is_entry": True,
                    },
                    {
                        "module": "__pytra_helper__.cpp.demo.py",
                        "kind": "helper",
                        "helper_id": "cpp.demo",
                        "owner_module_id": "pkg.main",
                        "label": "cpp_demo",
                        "header_text": "// hdr helper\n",
                        "source_text": '#include "pytra_multi_prelude.h"\nvoid helper_body() {}\n',
                        "is_entry": False,
                    },
                ],
                entry=str(root / "main.py"),
                entry_modules=["pkg.main"],
                program_id="pkg.main",
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(result["modules"][1]["kind"], "helper")
            self.assertEqual(result["modules"][1]["helper_id"], "cpp.demo")
            self.assertEqual(manifest["modules"][1]["kind"], "helper")
            self.assertEqual(manifest["modules"][1]["owner_module_id"], "pkg.main")


if __name__ == "__main__":
    unittest.main()

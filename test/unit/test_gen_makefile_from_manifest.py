"""Tests for tools/gen_makefile_from_manifest.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "gen_makefile_from_manifest.py"


class GenMakefileTest(unittest.TestCase):
    def test_generates_expected_makefile(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            manifest = ROOT / workdir / "manifest.json"
            output_makefile = Path(workdir) / "Makefile"
            (Path(workdir) / "src").mkdir()
            (Path(workdir) / "src/main.cpp").write_text("int main(){}\n", encoding="utf-8")
            (Path(workdir) / "src/util.cpp").write_text("int util(){}\n", encoding="utf-8")
            manifest_data = {
                "modules": [
                    {"source": "src/main.cpp"},
                    {"source": "src/util.cpp"},
                ],
                "include_dir": "include",
            }
            manifest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(manifest),
                    "-o",
                    str(output_makefile),
                    "--exe",
                    "app.out",
                    "--compiler",
                    "clang++",
                    "--std",
                    "c++20",
                    "--opt",
                    "-O3",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = output_makefile.read_text(encoding="utf-8")
            self.assertIn("CXX := clang++", text)
            self.assertIn("CXXFLAGS := -std=c++20 -O3", text)
            self.assertIn("SRCS := " + str(manifest.parent / "src/main.cpp"), text)
            self.assertIn("SRCS := " + str(manifest.parent / "src/main.cpp") + " " + str(manifest.parent / "src/util.cpp") , text)
            self.assertIn("TARGET := app.out", text)
            self.assertIn("%.o: %.cpp", text)
            self.assertIn("run:", text)
            self.assertIn("clean:", text)

    def test_missing_manifest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            missing = Path(workdir) / "missing.json"
            output_makefile = Path(workdir) / "Makefile"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(missing),
                    "-o",
                    str(output_makefile),
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_makefile.exists())
            self.assertIn("error:", result.stderr)

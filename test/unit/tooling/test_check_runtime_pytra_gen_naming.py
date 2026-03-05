from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_runtime_pytra_gen_naming as naming_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_allowlist(path: Path, keys: list[str]) -> None:
    _write(path, "# test allowlist\n\n" + "\n".join(keys) + ("\n" if len(keys) > 0 else ""))


class CheckRuntimePytraGenNamingTest(unittest.TestCase):
    def test_collect_detects_non_passthrough_name(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "src" / "pytra" / "utils" / "png.py", "def write_rgb_png():\n    return None\n")
            _write(
                root / "src" / "runtime" / "kotlin" / "pytra-gen" / "utils" / "image_runtime.kt",
                "fun pyWriteRGBPNG() {}\n",
            )
            with patch.object(naming_mod, "ROOT", root), patch.object(
                naming_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ), patch.object(
                naming_mod, "PYTRA_STD_ROOT", root / "src" / "pytra" / "std"
            ), patch.object(
                naming_mod, "PYTRA_UTILS_ROOT", root / "src" / "pytra" / "utils"
            ):
                findings = naming_mod._collect_findings()
        self.assertTrue(any(item.reason == "non_passthrough_name" for item in findings))

    def test_collect_detects_invalid_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "src" / "pytra" / "utils" / "gif.py", "def save_gif():\n    return None\n")
            _write(
                root / "src" / "runtime" / "php" / "pytra-gen" / "runtime" / "gif.php",
                "<?php\n",
            )
            with patch.object(naming_mod, "ROOT", root), patch.object(
                naming_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ), patch.object(
                naming_mod, "PYTRA_STD_ROOT", root / "src" / "pytra" / "std"
            ), patch.object(
                naming_mod, "PYTRA_UTILS_ROOT", root / "src" / "pytra" / "utils"
            ):
                findings = naming_mod._collect_findings()
        self.assertTrue(any(item.reason == "invalid_bucket" for item in findings))

    def test_main_passes_when_findings_are_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "src" / "pytra" / "utils" / "gif.py", "def save_gif():\n    return None\n")
            bad_file = root / "src" / "runtime" / "php" / "pytra-gen" / "runtime" / "gif.php"
            _write(bad_file, "<?php\n")
            allowlist_path = root / "tools" / "runtime_pytra_gen_naming_allowlist.txt"
            key = "src/runtime/php/pytra-gen/runtime/gif.php:invalid_bucket"
            _write_allowlist(allowlist_path, [key])
            with patch.object(naming_mod, "ROOT", root), patch.object(
                naming_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ), patch.object(
                naming_mod, "PYTRA_STD_ROOT", root / "src" / "pytra" / "std"
            ), patch.object(
                naming_mod, "PYTRA_UTILS_ROOT", root / "src" / "pytra" / "utils"
            ), patch.object(
                naming_mod, "ALLOWLIST_PATH", allowlist_path
            ), patch.object(
                sys, "argv", ["check_runtime_pytra_gen_naming.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                rc = naming_mod.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

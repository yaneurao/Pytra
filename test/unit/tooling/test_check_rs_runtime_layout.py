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

from tools import check_rs_runtime_layout as layout_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckRsRuntimeLayoutTest(unittest.TestCase):
    def test_main_requires_canonical_native_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(layout_mod, "ROOT", root), patch.object(
                layout_mod, "LEGACY_DIR", root / "src" / "rs_module"
            ), patch.object(
                layout_mod,
                "CANONICAL_RUNTIME",
                root / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs",
            ), patch.object(
                layout_mod,
                "DELETE_TARGET_DIR",
                root / "src" / "runtime" / "rs" / "pytra",
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as stdout:
                rc = layout_mod.main()
        self.assertEqual(rc, 1)
        self.assertIn("missing canonical Rust runtime file", stdout.getvalue())

    def test_main_accepts_native_canonical_when_delete_target_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            canonical = root / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs"
            _write(canonical, "// native runtime\n")
            with patch.object(layout_mod, "ROOT", root), patch.object(
                layout_mod, "LEGACY_DIR", root / "src" / "rs_module"
            ), patch.object(layout_mod, "CANONICAL_RUNTIME", canonical), patch.object(
                layout_mod, "DELETE_TARGET_DIR", root / "src" / "runtime" / "rs" / "pytra"
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
                rc = layout_mod.main()
        self.assertEqual(rc, 0)
        self.assertIn("canonical runtime", stdout.getvalue())
        self.assertIn("delete-target runtime", stdout.getvalue())

    def test_main_rejects_delete_target_pytra_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            canonical = root / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs"
            delete_target_dir = root / "src" / "runtime" / "rs" / "pytra"
            _write(canonical, "// native runtime\n")
            _write(delete_target_dir / "built_in" / "py_runtime.rs", "// delete-target runtime\n")
            with patch.object(layout_mod, "ROOT", root), patch.object(
                layout_mod, "LEGACY_DIR", root / "src" / "rs_module"
            ), patch.object(layout_mod, "CANONICAL_RUNTIME", canonical), patch.object(
                layout_mod, "DELETE_TARGET_DIR", delete_target_dir
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
                rc = layout_mod.main()
        self.assertEqual(rc, 1)
        self.assertIn("delete-target Rust pytra lane still exists", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

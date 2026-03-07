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

from tools import check_runtime_cpp_layout as layout_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_valid_tree(root: Path) -> None:
    marker = "AUTO-GENERATED FILE. DO NOT EDIT."
    _write(root / "src" / "runtime" / "cpp" / "generated" / "std" / "time.h", f"// {marker}\n")
    _write(root / "src" / "runtime" / "cpp" / "native" / "std" / "time.cpp", "// native\n")
    _write(root / "src" / "runtime" / "cpp" / "pytra" / "std" / "time.h", f"// {marker}\n")
    _write(root / "src" / "runtime" / "cpp" / "core" / "dict.ext.h", "#pragma once\n")
    _write(root / "src" / "runtime" / "cpp" / "core" / "py_runtime.ext.h", "#pragma once\n")
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / "gc.ext.cpp", "// native\n")
    _write(
        root / "src" / "runtime" / "cpp" / "generated" / "core" / "dict.ext.cpp",
        f"// {marker}\n",
    )
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / "dict.ext.cpp", "// native\n")


class CheckRuntimeCppLayoutTest(unittest.TestCase):
    def _run_main(self, root: Path) -> tuple[int, str]:
        with patch.object(layout_mod, "ROOT", root), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            rc = layout_mod.main()
        return rc, stdout.getvalue()

    def test_main_passes_for_core_surface_with_future_generated_native_core_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            rc, out = self._run_main(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("[OK] runtime cpp layout guard passed", out)

    def test_main_fails_on_unexpected_core_cpp_reintrusion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(root / "src" / "runtime" / "cpp" / "core" / "dict.ext.cpp", "// should move to native/core\n")
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("core compatibility surface unexpectedly contains implementation sources", out)
        self.assertIn("src/runtime/cpp/core/dict.ext.cpp", out)

    def test_main_fails_when_pytra_core_bucket_is_reintroduced(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(
                root / "src" / "runtime" / "cpp" / "pytra" / "core" / "dict.h",
                "// AUTO-GENERATED FILE. DO NOT EDIT.\n",
            )
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("ownership roots contain unsupported top-level buckets", out)
        self.assertIn("src/runtime/cpp/pytra/core/dict.h", out)


if __name__ == "__main__":
    unittest.main()

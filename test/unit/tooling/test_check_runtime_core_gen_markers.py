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

from tools import check_runtime_core_gen_markers as marker_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_allowlist(path: Path, keys: list[str]) -> None:
    _write(path, "# test allowlist\n\n" + "\n".join(keys) + ("\n" if len(keys) > 0 else ""))


class CheckRuntimeCoreGenMarkersTest(unittest.TestCase):
    def test_collect_detects_missing_generated_markers_in_pytra_gen(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "src" / "runtime" / "js" / "pytra-gen" / "utils" / "png.js", "function f() {}\n")
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ):
                findings = marker_mod._collect_findings()
        reasons = {item.reason for item in findings}
        self.assertIn("gen_missing_source_marker", reasons)
        self.assertIn("gen_missing_generated_by_marker", reasons)

    def test_collect_detects_generated_source_marker_in_pytra_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs",
                "// source: src/pytra/utils/png.py\n",
            )
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ):
                findings = marker_mod._collect_findings()
        self.assertTrue(any(item.reason == "core_contains_generated_source_marker" for item in findings))

    def test_collect_detects_missing_generated_markers_in_cpp_generated_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "src" / "runtime" / "cpp" / "generated" / "core" / "dict.cpp", "// body\n")
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ):
                findings = marker_mod._collect_findings()
        reasons = {item.reason for item in findings}
        self.assertIn("cpp_generated_core_missing_source_marker", reasons)
        self.assertIn("cpp_generated_core_missing_generated_by_marker", reasons)

    def test_collect_detects_generated_markers_in_cpp_native_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root / "src" / "runtime" / "cpp" / "native" / "core" / "dict.h",
                "// source: src/pytra/std/time.py\n// generated-by: test\n",
            )
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ):
                findings = marker_mod._collect_findings()
        reasons = {item.reason for item in findings}
        self.assertIn("cpp_native_core_contains_generated_source_marker", reasons)
        self.assertIn("cpp_native_core_contains_generated_by_marker", reasons)

    def test_collect_detects_generated_markers_in_cpp_core_surface(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root / "src" / "runtime" / "cpp" / "core" / "dict.h",
                "// source: src/pytra/core/dict.py\n// generated-by: test\n",
            )
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ):
                findings = marker_mod._collect_findings()
        reasons = {item.reason for item in findings}
        self.assertIn("cpp_core_surface_contains_generated_source_marker", reasons)
        self.assertIn("cpp_core_surface_contains_generated_by_marker", reasons)

    def test_main_passes_when_findings_are_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = root / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs"
            _write(bad, "// source: src/pytra/utils/gif.py\n")
            allowlist_path = root / "tools" / "runtime_core_gen_markers_allowlist.txt"
            key = "src/runtime/rs/native/built_in/py_runtime.rs:core_contains_generated_source_marker"
            _write_allowlist(allowlist_path, [key])
            with patch.object(marker_mod, "ROOT", root), patch.object(
                marker_mod, "RUNTIME_ROOT", root / "src" / "runtime"
            ), patch.object(
                marker_mod, "ALLOWLIST_PATH", allowlist_path
            ), patch.object(
                sys, "argv", ["check_runtime_core_gen_markers.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                rc = marker_mod.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

"""Tests for C++ runtime source companion discovery."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BUILD_SCRIPT = ROOT / "tools" / "build_multi_cpp.py"
MAKEFILE_SCRIPT = ROOT / "tools" / "gen_makefile_from_manifest.py"

from tools import cpp_runtime_deps as deps_mod
from tools.cpp_runtime_deps import runtime_cpp_candidates_from_header


class CppRuntimeBuildGraphTest(unittest.TestCase):
    def _make_forwarder_project(self, workdir: Path) -> Path:
        src_dir = workdir / "src"
        include_dir = workdir / "include" / "pytra" / "std"
        src_dir.mkdir(parents=True, exist_ok=True)
        include_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "main.cpp").write_text(
            '\n'.join(
                [
                    '#include "pytra/std/math.h"',
                    "",
                    "int main() {",
                    "    return pytra::std::math::sqrt(4.0) == 2.0 ? 0 : 1;",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (include_dir / "math.h").write_text(
            '\n'.join(
                [
                    "#pragma once",
                    '#include "runtime/cpp/pytra/std/math.h"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        manifest = workdir / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "modules": [{"source": str(src_dir / "main.cpp")}],
                    "include_dir": str(workdir / "include"),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest

    def test_build_multi_cpp_follows_forwarder_header_to_native_cpp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            manifest = self._make_forwarder_project(workdir)
            exe = workdir / "app.out"
            build = subprocess.run(
                [sys.executable, str(BUILD_SCRIPT), str(manifest), "-o", str(exe)],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            self.assertTrue(exe.exists())
            run = subprocess.run([str(exe)], capture_output=True, text=True, cwd=str(workdir))
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_makefile_includes_native_cpp_for_forwarder_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            manifest = self._make_forwarder_project(workdir)
            output_makefile = workdir / "Makefile"
            result = subprocess.run(
                [sys.executable, str(MAKEFILE_SCRIPT), str(manifest), "-o", str(output_makefile)],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output_makefile.read_text(encoding="utf-8")
            self.assertIn(str(ROOT / "src/runtime/cpp/native/std/math.cpp"), text)

    def test_runtime_cpp_candidates_support_generated_native_layout(self) -> None:
        header = ROOT / "src/runtime/cpp/generated/std/math.h"
        paths = [path.as_posix() for path in runtime_cpp_candidates_from_header(header)]
        self.assertIn((ROOT / "src/runtime/cpp/generated/std/math.cpp").as_posix(), paths)
        self.assertIn((ROOT / "src/runtime/cpp/native/std/math.cpp").as_posix(), paths)
        self.assertNotIn((ROOT / "src/runtime/cpp/std/math.gen.cpp").as_posix(), paths)
        self.assertNotIn((ROOT / "src/runtime/cpp/std/math.ext.cpp").as_posix(), paths)

    def test_runtime_cpp_candidates_from_public_shim_do_not_reintroduce_legacy_module_paths(self) -> None:
        header = ROOT / "src/runtime/cpp/pytra/std/time.h"
        paths = [path.as_posix() for path in runtime_cpp_candidates_from_header(header)]
        self.assertIn((ROOT / "src/runtime/cpp/native/std/time.cpp").as_posix(), paths)
        self.assertNotIn((ROOT / "src/runtime/cpp/std/time.gen.cpp").as_posix(), paths)
        self.assertNotIn((ROOT / "src/runtime/cpp/std/time.ext.cpp").as_posix(), paths)

    def test_runtime_cpp_candidates_support_future_core_split_from_core_header(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime_root = root / "src/runtime/cpp"
            (runtime_root / "core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "generated/core").mkdir(parents=True, exist_ok=True)
            (runtime_root / "native/core").mkdir(parents=True, exist_ok=True)
            header = runtime_root / "core/dict.ext.h"
            header.write_text("#pragma once\n", encoding="utf-8")

            with patch.object(deps_mod, "ROOT", root), patch.object(
                deps_mod, "RUNTIME_ROOT", runtime_root
            ), patch.object(
                deps_mod, "SRC_ROOT", root / "src"
            ), patch.object(
                deps_mod, "_HEADER_SOURCE_INDEX", None
            ):
                paths = [path.as_posix() for path in deps_mod.runtime_cpp_candidates_from_header(header)]

        self.assertIn((runtime_root / "generated/core/dict.ext.cpp").as_posix(), paths)
        self.assertIn((runtime_root / "native/core/dict.ext.cpp").as_posix(), paths)
        self.assertIn((runtime_root / "core/dict.ext.cpp").as_posix(), paths)

    def test_runtime_cpp_candidates_for_real_core_header_follow_native_core_source(self) -> None:
        header = ROOT / "src/runtime/cpp/core/gc.ext.h"
        paths = [path.as_posix() for path in runtime_cpp_candidates_from_header(header)]
        self.assertIn((ROOT / "src/runtime/cpp/native/core/gc.ext.cpp").as_posix(), paths)
        self.assertNotIn((ROOT / "src/runtime/cpp/core/gc.ext.cpp").as_posix(), paths)

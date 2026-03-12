from __future__ import annotations

import io
import shutil
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


def _make_valid_tree(root: Path, *, legacy_ext_names: bool = False) -> None:
    marker = "AUTO-GENERATED FILE. DO NOT EDIT."
    core_header_name = "dict.ext.h" if legacy_ext_names else "dict.h"
    py_runtime_name = "py_runtime.ext.h" if legacy_ext_names else "py_runtime.h"
    core_cpp_name = "dict.ext.cpp" if legacy_ext_names else "dict.cpp"
    gc_cpp_name = "gc.ext.cpp" if legacy_ext_names else "gc.cpp"
    _write(root / "src" / "runtime" / "cpp" / "generated" / "std" / "time.h", f"// {marker}\n")
    _write(root / "src" / "runtime" / "cpp" / "native" / "std" / "time.cpp", "// native\n")
    _write(root / "src" / "runtime" / "cpp" / "pytra" / "std" / "time.h", f"// {marker}\n")
    _write(
        root / "src" / "runtime" / "cpp" / "generated" / "compiler" / "backend_registry_static.h",
        f"// {marker}\n",
    )
    _write(
        root / "src" / "runtime" / "cpp" / "native" / "compiler" / "backend_registry_static.cpp",
        "// native\n",
    )
    _write(
        root / "src" / "runtime" / "cpp" / "pytra" / "compiler" / "backend_registry_static.h",
        f"// {marker}\n",
    )
    _write(
        root / "src" / "runtime" / "cpp" / "core" / core_header_name,
        f'#pragma once\n#include "runtime/cpp/native/core/{core_header_name}"\n',
    )
    _write(
        root / "src" / "runtime" / "cpp" / "core" / py_runtime_name,
        f'#pragma once\n#include "runtime/cpp/native/core/{py_runtime_name}"\n',
    )
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / core_header_name, "#pragma once\n")
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / py_runtime_name, "#pragma once\n")
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / gc_cpp_name, "// native\n")
    _write(
        root / "src" / "runtime" / "cpp" / "generated" / "core" / core_cpp_name,
        f"// {marker}\n",
    )
    _write(root / "src" / "runtime" / "cpp" / "native" / "core" / core_cpp_name, "// native\n")


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

    def test_main_fails_when_legacy_ext_core_surface_reappears(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root, legacy_ext_names=True)
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("files violating runtime naming policy", out)
        self.assertIn("src/runtime/cpp/core/dict.ext.h", out)
        self.assertIn("src/runtime/cpp/native/core/dict.ext.h", out)

    def test_main_fails_on_unexpected_core_cpp_reintrusion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(root / "src" / "runtime" / "cpp" / "core" / "dict.cpp", "// should move to native/core\n")
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("core compatibility surface unexpectedly contains implementation sources", out)
        self.assertIn("src/runtime/cpp/core/dict.cpp", out)

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

    def test_main_allows_generated_runtime_to_include_native_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(
                root / "src" / "runtime" / "cpp" / "generated" / "std" / "time.cpp",
                '// AUTO-GENERATED FILE. DO NOT EDIT.\n#include "runtime/cpp/native/core/py_runtime.h"\n',
            )
            rc, out = self._run_main(root)
        self.assertEqual(rc, 0, out)
        self.assertIn("[OK] runtime cpp layout guard passed", out)

    def test_main_fails_when_public_shim_directly_includes_native_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(
                root / "src" / "runtime" / "cpp" / "pytra" / "std" / "time.h",
                '// AUTO-GENERATED FILE. DO NOT EDIT.\n#include "runtime/cpp/native/core/py_runtime.h"\n',
            )
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("non-forwarder runtime files directly include native/core headers", out)
        self.assertIn(
            "src/runtime/cpp/pytra/std/time.h -> runtime/cpp/native/core/py_runtime.h",
            out,
        )

    def test_main_fails_when_py_runtime_reaggregates_removed_built_in_headers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(
                root / "src" / "runtime" / "cpp" / "native" / "core" / "py_runtime.h",
                '#pragma once\n#include "runtime/cpp/generated/built_in/sequence.h"\n',
            )
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("py_runtime core header still contains duplicated high-level runtime bodies", out)
        self.assertIn('#include "runtime/cpp/generated/built_in/sequence.h"', out)

    def test_main_fails_when_py_runtime_reintroduces_template_helper_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            _write(
                root / "src" / "runtime" / "cpp" / "native" / "core" / "py_runtime.h",
                "#pragma once\nstatic inline list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs) { return {}; }\n",
            )
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("py_runtime core header still contains duplicated high-level runtime bodies", out)
        self.assertIn("zip(const list<A>& lhs, const list<B>& rhs)", out)

    def test_main_fails_when_generated_core_lane_directory_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _make_valid_tree(root)
            shutil.rmtree(root / "src" / "runtime" / "cpp" / "generated" / "core")
            rc, out = self._run_main(root)
        self.assertEqual(rc, 1)
        self.assertIn("required core ownership directories are missing", out)
        self.assertIn("src/runtime/cpp/generated/core", out)


if __name__ == "__main__":
    unittest.main()

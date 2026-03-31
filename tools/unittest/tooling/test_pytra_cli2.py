"""Regression tests for src/pytra-cli2.py."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

_CLI2_PATH = ROOT / "src" / "pytra-cli2.py"
_SPEC = importlib.util.spec_from_file_location("pytra_cli2_mod", str(_CLI2_PATH))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load pytra-cli2 module spec")
pytra_cli2_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pytra_cli2_mod)


class PytraCli2Test(unittest.TestCase):
    def test_repo_root_is_anchored_to_script_not_cwd(self) -> None:
        old_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                repo_root = pytra_cli2_mod._repo_root()
                builtins_path, containers_path, stdlib_dir = pytra_cli2_mod._builtin_registry_paths()
        finally:
            os.chdir(old_cwd)

        self.assertEqual(str(repo_root), str(ROOT))
        self.assertTrue(Path(str(builtins_path)).exists())
        self.assertTrue(Path(str(containers_path)).exists())
        self.assertTrue(Path(str(stdlib_dir)).exists())

    def test_pytra_cli2_has_no_cpp_runtime_bundle_top_level_import(self) -> None:
        source = _CLI2_PATH.read_text(encoding="utf-8")
        self.assertNotIn("toolchain2.emit.cpp.runtime_bundle", source)
        self.assertIn('"-m", "toolchain2.emit.cpp.cli"', source)


if __name__ == "__main__":
    unittest.main()

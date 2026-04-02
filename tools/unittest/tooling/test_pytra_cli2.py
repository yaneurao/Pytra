"""Regression tests for src/pytra-cli2.py."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain2.link.shared_types import LinkedModule

_CLI2_PATH = ROOT / "src" / "pytra-cli2.py"
_SPEC = importlib.util.spec_from_file_location("pytra_cli2_mod", str(_CLI2_PATH))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load pytra-cli2 module spec")
pytra_cli2_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pytra_cli2_mod)


class PytraCli2Test(unittest.TestCase):
    def test_optimizer_debug_flags_normalize_subscript_modes(self) -> None:
        flags = pytra_cli2_mod._optimizer_debug_flags("always", "debug")
        self.assertEqual(flags, {"negative_index_mode": "always", "bounds_check_mode": "debug"})

    def test_optimizer_debug_flags_apply_defaults(self) -> None:
        flags = pytra_cli2_mod._optimizer_debug_flags("", "")
        self.assertEqual(flags, {"negative_index_mode": "const_only", "bounds_check_mode": "off"})

    def test_cmd_optimize_forwards_subscript_optimizer_modes(self) -> None:
        with patch.object(pytra_cli2_mod, "_optimize_one", return_value=0) as optimize_one:
            rc = pytra_cli2_mod.cmd_optimize(
                [
                    "mod.east3",
                    "--negative-index-mode",
                    "always",
                    "--bounds-check-mode",
                    "debug",
                ]
            )
        self.assertEqual(rc, 0)
        optimize_one.assert_called_once()
        call_args = optimize_one.call_args[0]
        self.assertEqual(str(call_args[0]), "mod.east3")
        self.assertEqual(call_args[1:], ("", False, "always", "debug"))

    def test_optimize_linked_runtime_modules_skips_user_modules(self) -> None:
        user = LinkedModule("app.main", "", "", True, {"kind": "Module", "east_stage": 3}, "user")
        runtime = LinkedModule("pytra.utils.png", "", "", False, {"kind": "Module", "east_stage": 3}, "runtime")
        helper = LinkedModule("__linked_helper__.x", "", "", False, {"kind": "Module", "east_stage": 3}, "helper")
        with patch.object(pytra_cli2_mod, "optimize_east3_doc_only", side_effect=lambda doc, **_: {"kind": "Module", "optimized": doc.get("kind")}) as optimize_doc:
            pytra_cli2_mod._optimize_linked_runtime_modules(
                [user, runtime, helper],
                opt_level=1,
                debug_flags={"negative_index_mode": "const_only", "bounds_check_mode": "off"},
            )
        self.assertEqual(optimize_doc.call_count, 2)
        self.assertNotIn("optimized", user.east_doc)
        self.assertEqual(runtime.east_doc.get("optimized"), "Module")
        self.assertEqual(helper.east_doc.get("optimized"), "Module")

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
        self.assertNotIn("from toolchain2.emit.rs.emitter import", source)
        self.assertNotIn("from toolchain2.link.manifest_loader import", source)
        self.assertIn('"-m", "toolchain2.emit.rs.cli"', source)


if __name__ == "__main__":
    unittest.main()

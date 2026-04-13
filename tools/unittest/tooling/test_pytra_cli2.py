"""Regression tests for src/pytra-cli.py."""

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

from toolchain.link.shared_types import LinkedModule

_CLI2_PATH = ROOT / "src" / "pytra-cli.py"
_SPEC = importlib.util.spec_from_file_location("pytra_cli2_mod", str(_CLI2_PATH))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load pytra-cli module spec")
pytra_cli2_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pytra_cli2_mod)


class PytraCli2Test(unittest.TestCase):
    def test_optimizer_debug_flags_normalize_subscript_modes(self) -> None:
        flags = pytra_cli2_mod._optimizer_debug_flags(1, "always", "debug")
        self.assertEqual(flags, {"negative_index_mode": "always", "bounds_check_mode": "debug"})

    def test_optimizer_debug_flags_apply_defaults(self) -> None:
        flags = pytra_cli2_mod._optimizer_debug_flags(1, "", "")
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
        self.assertEqual(call_args[1:], ("", False, 1, "always", "debug"))

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
                builtins_path, containers_path, containers_source_path, stdlib_dir = pytra_cli2_mod._builtin_registry_paths()
        finally:
            os.chdir(old_cwd)

        self.assertEqual(str(repo_root), str(ROOT))
        self.assertTrue(Path(str(builtins_path)).exists())
        self.assertTrue(Path(str(containers_path)).exists())
        self.assertTrue(Path(str(containers_source_path)).exists())
        self.assertTrue(Path(str(stdlib_dir)).exists())

    def test_pytra_cli2_has_no_cpp_runtime_bundle_top_level_import(self) -> None:
        source = _CLI2_PATH.read_text(encoding="utf-8")
        self.assertNotIn("toolchain.emit.cpp.runtime_bundle", source)
        self.assertIn('"-m", "toolchain.emit.cpp.cli"', source)
        self.assertNotIn("from toolchain.emit.rs.emitter import", source)
        self.assertNotIn("from toolchain.link.manifest_loader import", source)
        self.assertIn('"-m", "toolchain.emit.rs.cli"', source)

    def test_build_pipeline_accepts_swift_target_and_uses_subprocess_emitter(self) -> None:
        with patch.object(pytra_cli2_mod, "_build_pipeline", return_value=0) as build_pipeline:
            rc = pytra_cli2_mod.cmd_build(["entry.py", "--target", "swift"])
        self.assertEqual(rc, 0)
        build_pipeline.assert_called_once()
        self.assertEqual(build_pipeline.call_args[0][2], "swift")

    def test_module_stem_from_source_path_preserves_py_package_segment(self) -> None:
        stem = pytra_cli2_mod._module_stem_from_source_path(
            "/workspace/Pytra/src/toolchain/parse/py/parse_python.py",
            "fallback.py",
        )
        self.assertEqual(stem, "toolchain.parse.py.parse_python")

    def test_build_pipeline_dispatches_swift_to_subprocess_emitter(self) -> None:
        entry_path = str((ROOT / "entry.py").resolve())
        linked_module = LinkedModule(
            "toolchain.cli.main",
            "",
            entry_path,
            True,
            {"source_path": entry_path},
            "user",
        )
        link_result = type("LinkResultStub", (), {"linked_modules": [linked_module], "manifest": {}})()
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "emit"
            with patch.object(pytra_cli2_mod, "_collect_build_sources", return_value=[("entry.py", {})]), \
                patch.object(pytra_cli2_mod, "_builtin_registry_paths", return_value=(Path("a"), Path("b"), Path("c"), Path("d"))), \
                patch.object(pytra_cli2_mod, "load_builtin_registry", return_value=object()), \
                patch.object(pytra_cli2_mod, "resolve_east1_to_east2"), \
                patch.object(pytra_cli2_mod, "lower_east2_to_east3", return_value={"source_path": entry_path}), \
                patch.object(pytra_cli2_mod, "optimize_east3_doc_only", return_value={"source_path": entry_path}), \
                patch.object(pytra_cli2_mod, "link_modules", return_value=link_result), \
                patch.object(pytra_cli2_mod, "_optimize_linked_runtime_modules"), \
                patch.object(pytra_cli2_mod, "_write_link_output"), \
                patch.object(pytra_cli2_mod, "_emit_target_subprocess", return_value=0) as emit_subprocess:
                rc = pytra_cli2_mod._build_pipeline(["entry.py"], str(out_dir), "swift")
        self.assertEqual(rc, 0)
        emit_subprocess.assert_called_once()
        self.assertEqual(emit_subprocess.call_args[0][0], "swift")

    def test_build_pipeline_lowers_js_with_ts_target_language(self) -> None:
        entry_path = str((ROOT / "entry.py").resolve())
        linked_module = LinkedModule(
            "toolchain.cli.main",
            "",
            entry_path,
            True,
            {"source_path": entry_path},
            "user",
        )
        link_result = type("LinkResultStub", (), {"linked_modules": [linked_module], "manifest": {}})()
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "emit"
            with patch.object(pytra_cli2_mod, "_collect_build_sources", return_value=[("entry.py", {})]), \
                patch.object(pytra_cli2_mod, "_builtin_registry_paths", return_value=(Path("a"), Path("b"), Path("c"), Path("d"))), \
                patch.object(pytra_cli2_mod, "load_builtin_registry", return_value=object()), \
                patch.object(pytra_cli2_mod, "resolve_east1_to_east2"), \
                patch.object(pytra_cli2_mod, "lower_east2_to_east3", return_value={"source_path": entry_path}) as lower_mock, \
                patch.object(pytra_cli2_mod, "optimize_east3_doc_only", return_value={"source_path": entry_path}), \
                patch.object(pytra_cli2_mod, "link_modules", return_value=link_result), \
                patch.object(pytra_cli2_mod, "_optimize_linked_runtime_modules"), \
                patch.object(pytra_cli2_mod, "_write_link_output"), \
                patch.object(pytra_cli2_mod, "_emit_ts", return_value=0), \
                patch.object(pytra_cli2_mod, "_emit_target_subprocess", return_value=0):
                rc = pytra_cli2_mod._build_pipeline(["entry.py"], str(out_dir), "js")
        self.assertEqual(rc, 0)
        self.assertEqual(lower_mock.call_args.kwargs["target_language"], "ts")

    def test_collect_build_sources_keeps_expand_defaults_type_norm_closure(self) -> None:
        sources = pytra_cli2_mod._collect_build_sources([str(ROOT / "src" / "pytra-cli.py")])
        paths = {str(Path(path).resolve()) for path, _ in sources}
        self.assertIn(str((ROOT / "src" / "toolchain" / "link" / "expand_defaults.py").resolve()), paths)
        self.assertIn(str((ROOT / "src" / "toolchain" / "resolve" / "py" / "type_norm.py").resolve()), paths)


if __name__ == "__main__":
    unittest.main()

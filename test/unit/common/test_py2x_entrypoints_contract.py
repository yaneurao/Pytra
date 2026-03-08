from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.toolchain.compiler.backend_registry as host_registry
import src.toolchain.compiler.backend_registry_static as static_registry


class Py2xEntrypointsContractTest(unittest.TestCase):
    def test_py2x_entrypoint_registry_binding(self) -> None:
        host_entry = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertIn("from toolchain.compiler.backend_registry import", host_entry)
        self.assertNotIn("backend_registry_static", host_entry)

        selfhost_entry = (ROOT / "src" / "py2x-selfhost.py").read_text(encoding="utf-8")
        self.assertIn("from toolchain.compiler.backend_registry_static import", selfhost_entry)

    def test_backend_registry_host_is_lazy_import_style(self) -> None:
        host_src = (ROOT / "src" / "toolchain" / "compiler" / "backend_registry.py").read_text(encoding="utf-8")
        self.assertIn("import importlib", host_src)
        self.assertNotIn("from backends.", host_src)

        static_src = (ROOT / "src" / "toolchain" / "compiler" / "backend_registry_static.py").read_text(encoding="utf-8")
        self.assertIn("from backends.rs.lower import lower_east3_to_rs_ir", static_src)

    def test_host_registry_loads_only_selected_target_modules(self) -> None:
        host_registry._SPEC_CACHE.clear()
        calls: list[str] = []
        real_import = host_registry.importlib.import_module

        def _tracked_import(module_name: str):
            calls.append(module_name)
            return real_import(module_name)

        with patch.object(host_registry.importlib, "import_module", side_effect=_tracked_import):
            spec = host_registry.get_backend_spec("rs")

        self.assertEqual(spec.get("target_lang"), "rs")
        self.assertIn("backends.rs.lower", calls)
        self.assertIn("backends.rs.optimizer", calls)
        self.assertIn("backends.rs.emitter.rs_emitter", calls)
        self.assertFalse(any(name.startswith("backends.cs") for name in calls))
        self.assertFalse(any(name.startswith("backends.go") for name in calls))
        self.assertFalse(any(name.startswith("backends.js") for name in calls))

    def test_host_registry_uses_spec_cache(self) -> None:
        host_registry._SPEC_CACHE.clear()
        _ = host_registry.get_backend_spec("rs")

        with patch.object(host_registry.importlib, "import_module", side_effect=AssertionError("unexpected import")):
            cached = host_registry.get_backend_spec("rs")
        self.assertEqual(cached.get("target_lang"), "rs")

    def test_backend_specs_expose_emit_module_and_program_writer(self) -> None:
        host_registry._SPEC_CACHE.clear()
        host_spec = host_registry.get_backend_spec("rs")
        static_spec = static_registry.get_backend_spec("rs")
        self.assertTrue(callable(host_spec.get("emit_module")))
        self.assertIn("program_writer", host_spec)
        self.assertTrue(callable(static_spec.get("emit_module")))
        self.assertIn("program_writer", static_spec)

    def test_build_program_artifact_preserves_helper_kind_metadata(self) -> None:
        fake_spec = {"target_lang": "cpp"}
        helper_module = {
            "module_id": "__pytra_helper__.cpp.demo",
            "kind": "helper",
            "label": "cpp_demo",
            "extension": ".cpp",
            "text": "// helper\n",
            "is_entry": False,
            "dependencies": [],
            "metadata": {"helper_id": "cpp.demo", "owner_module_id": "pkg.main"},
        }
        user_module = {
            "module_id": "pkg.main",
            "label": "main",
            "extension": ".cpp",
            "text": "// main\n",
            "is_entry": True,
            "dependencies": [],
            "metadata": {},
        }

        host_artifact = host_registry.build_program_artifact(
            fake_spec,
            [helper_module, user_module],
            program_id="pkg.main",
            entry_modules=["pkg.main"],
        )
        static_artifact = static_registry.build_program_artifact(
            fake_spec,
            [helper_module, user_module],
            program_id="pkg.main",
            entry_modules=["pkg.main"],
        )

        self.assertEqual(host_artifact["modules"][0]["kind"], "helper")
        self.assertEqual(host_artifact["modules"][0]["metadata"]["helper_id"], "cpp.demo")
        self.assertEqual(host_artifact["modules"][1]["kind"], "user")
        self.assertEqual(static_artifact["modules"][0]["kind"], "helper")
        self.assertEqual(static_artifact["modules"][0]["metadata"]["owner_module_id"], "pkg.main")
        self.assertEqual(static_artifact["modules"][1]["kind"], "user")

    def test_collect_program_modules_flattens_helper_modules(self) -> None:
        host_modules = host_registry.collect_program_modules(
            {
                "module_id": "pkg.main",
                "kind": "user",
                "text": "// main\n",
                "helper_modules": [
                    {
                        "module_id": "__pytra_helper__.cpp.demo",
                        "metadata": {"helper_id": "cpp.demo", "owner_module_id": "pkg.main"},
                    }
                ],
            }
        )
        static_modules = static_registry.collect_program_modules(
            {
                "module_id": "pkg.main",
                "kind": "user",
                "text": "// main\n",
                "helper_modules": [
                    {
                        "module_id": "__pytra_helper__.cpp.demo",
                        "metadata": {"helper_id": "cpp.demo", "owner_module_id": "pkg.main"},
                    }
                ],
            }
        )

        self.assertEqual(len(host_modules), 2)
        self.assertEqual(host_modules[1]["kind"], "helper")
        self.assertEqual(host_modules[1]["metadata"]["helper_id"], "cpp.demo")
        self.assertEqual(len(static_modules), 2)
        self.assertEqual(static_modules[1]["kind"], "helper")

    def test_emit_source_uses_emit_module_text_wrapper(self) -> None:
        spec = host_registry._normalize_backend_spec(
            {
                "target_lang": "fake",
                "extension": ".txt",
                "emit": lambda ir, output_path, _opts=None: "// "
                + str(ir.get("kind", ""))
                + " -> "
                + output_path.name,
            }
        )
        artifact = host_registry.emit_module(
            spec,
            {"kind": "Demo"},
            Path("out/demo.txt"),
            {},
            module_id="pkg.demo",
            is_entry=True,
        )
        text = host_registry.emit_source(spec, {"kind": "Demo"}, Path("out/demo.txt"), {})
        self.assertEqual(artifact["module_id"], "pkg.demo")
        self.assertEqual(artifact["label"], "demo")
        self.assertEqual(artifact["extension"], ".txt")
        self.assertEqual(artifact["text"], text)
        self.assertTrue(bool(artifact["is_entry"]))


if __name__ == "__main__":
    unittest.main()

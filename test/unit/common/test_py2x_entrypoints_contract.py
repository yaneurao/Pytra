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
import src.toolchain.compiler.typed_boundary as typed_boundary


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

    def test_selfhost_cpp_entry_keeps_compiler_shims_while_native_headers_expose_typed_wrappers(self) -> None:
        selfhost_cpp = (ROOT / "selfhost" / "py2cpp.cpp").read_text(encoding="utf-8")
        selfhost_stage2 = (ROOT / "selfhost" / "py2cpp_stage2.cpp").read_text(encoding="utf-8")
        selfhost_src = (ROOT / "src" / "py2x-selfhost.py").read_text(encoding="utf-8")
        native_transpile = (ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "transpile_cli.h").read_text(encoding="utf-8")
        native_registry = (ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "backend_registry_static.h").read_text(encoding="utf-8")

        self.assertIn("def _load_east3(", selfhost_src)
        self.assertIn("def _get_spec(", selfhost_src)
        self.assertIn("def _resolve_opts(", selfhost_src)
        self.assertIn("def _emit(", selfhost_src)
        self.assertIn("def _apply_runtime(", selfhost_src)

        self.assertIn("dict<str, object> _load_east3(", selfhost_cpp)
        self.assertIn("dict<str, object> _get_spec(", selfhost_cpp)
        self.assertIn("dict<str, object> _resolve_opts(", selfhost_cpp)
        self.assertIn("str _emit(", selfhost_cpp)
        self.assertIn("void _apply_runtime(", selfhost_cpp)

        self.assertIn("CompilerRootDocument _load_east3_typed(", selfhost_stage2)
        self.assertIn("ResolvedBackendSpec _get_spec_typed(", selfhost_stage2)
        self.assertIn("LayerOptionsCarrier _resolve_opts_typed(", selfhost_stage2)
        self.assertIn("str _emit(", selfhost_stage2)
        self.assertIn("void _apply_runtime(", selfhost_stage2)
        self.assertIn("load_east3_document_typed", selfhost_stage2)
        self.assertIn("get_backend_spec_typed", selfhost_stage2)
        self.assertIn("resolve_layer_options_typed", selfhost_stage2)
        self.assertIn("emit_source_typed", selfhost_stage2)
        self.assertIn("apply_runtime_hook_typed", selfhost_stage2)

        self.assertIn("struct CompilerRootDocument", native_transpile)
        self.assertIn("load_east3_document_typed", native_transpile)
        self.assertIn("struct ResolvedBackendSpec", native_registry)
        self.assertIn("struct LayerOptionsCarrier", native_registry)
        self.assertIn("get_backend_spec_typed", native_registry)
        self.assertIn("emit_source_typed", native_registry)

    def test_native_cpp_typed_boundary_make_object_usage_stays_on_export_seams(self) -> None:
        native_transpile = (
            ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "transpile_cli.cpp"
        ).read_text(encoding="utf-8")
        native_registry = (
            ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "backend_registry_static.cpp"
        ).read_text(encoding="utf-8")

        transpile_make_object_lines = [
            line.strip()
            for line in native_transpile.splitlines()
            if "make_object(" in line
        ]
        registry_make_object_lines = [
            line.strip()
            for line in native_registry.splitlines()
            if "make_object(" in line
        ]

        self.assertEqual(
            transpile_make_object_lines,
            [
                'out["kind"] = make_object(module_kind);',
                'out["source_path"] = make_object(meta.source_path);',
                'out["east_stage"] = make_object(meta.east_stage);',
                'out["schema_version"] = make_object(meta.schema_version);',
                'meta_dict["dispatch_mode"] = make_object(meta.dispatch_mode);',
                'meta_dict["parser_backend"] = make_object(meta.parser_backend);',
                'out["meta"] = make_object(meta_dict);',
            ],
        )
        self.assertEqual(
            registry_make_object_lines,
            [
                'out["target_lang"] = make_object(carrier.target_lang);',
                'out["extension"] = make_object(carrier.extension);',
                'spec["target_lang"] = make_object(target);',
                'spec["extension"] = make_object(_target_extension(target));',
                'ir_path.write_text(pytra::std::json::dumps(make_object(ir), true));',
            ],
        )

    def test_typed_backend_specs_preserve_legacy_metadata(self) -> None:
        host_registry._SPEC_CACHE.clear()
        host_spec = host_registry.get_backend_spec_typed("cpp")
        static_spec = static_registry.get_backend_spec_typed("cpp")

        self.assertEqual(host_spec.carrier.target_lang, "cpp")
        self.assertEqual(static_spec.carrier.target_lang, "cpp")
        self.assertEqual(host_registry.get_backend_spec("cpp").get("target_lang"), host_spec.carrier.target_lang)
        self.assertEqual(static_registry.get_backend_spec("cpp").get("target_lang"), static_spec.carrier.target_lang)

        host_opts = host_registry.resolve_layer_options_typed(host_spec, "emitter", {"mod_mode": "python"})
        static_opts = static_registry.resolve_layer_options_typed(static_spec, "emitter", {"mod_mode": "python"})
        self.assertEqual(host_opts.layer, "emitter")
        self.assertEqual(host_opts.values["mod_mode"], "python")
        self.assertEqual(static_opts.values["mod_mode"], "python")

    def test_compiler_root_document_coercion_accepts_typed_carrier(self) -> None:
        raw_doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
        }
        doc = typed_boundary.coerce_compiler_root_document(
            raw_doc,
            source_path="demo.py",
            parser_backend="self_hosted",
        )
        self.assertIs(typed_boundary.coerce_compiler_root_document(doc), doc)

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
        module_artifact = {
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
        host_modules = host_registry.collect_program_modules(module_artifact)
        static_modules = static_registry.collect_program_modules(module_artifact)
        host_typed_modules = host_registry.collect_program_modules_typed(module_artifact)
        static_typed_modules = static_registry.collect_program_modules_typed(module_artifact)

        self.assertEqual(len(host_modules), 2)
        self.assertEqual(host_modules[1]["kind"], "helper")
        self.assertEqual(host_modules[1]["metadata"]["helper_id"], "cpp.demo")
        self.assertEqual(len(static_modules), 2)
        self.assertEqual(static_modules[1]["kind"], "helper")
        self.assertEqual(len(host_typed_modules), 2)
        self.assertEqual(host_typed_modules[1].kind, "helper")
        self.assertEqual(host_typed_modules[1].metadata["owner_module_id"], "pkg.main")
        self.assertEqual(len(static_typed_modules), 2)
        self.assertEqual(static_typed_modules[1].kind, "helper")

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

    def test_typed_emit_and_program_artifact_wrap_legacy_surface(self) -> None:
        fake_host_spec = host_registry._normalize_backend_runtime_spec(
            {
                "target_lang": "fake",
                "extension": ".txt",
                "emit": lambda ir, output_path, _opts=None: "// "
                + str(ir.get("kind", ""))
                + " -> "
                + output_path.name,
            }
        )
        fake_static_spec = static_registry._normalize_backend_runtime_spec(
            {
                "target_lang": "fake",
                "extension": ".txt",
                "emit": lambda ir, output_path, _opts=None: "// "
                + str(ir.get("kind", ""))
                + " -> "
                + output_path.name,
            }
        )

        host_artifact = host_registry.emit_module_typed(
            fake_host_spec,
            {"kind": "Demo"},
            Path("out/demo.txt"),
            {"mode": "typed"},
            module_id="pkg.demo",
            is_entry=True,
        )
        static_artifact = static_registry.emit_module_typed(
            fake_static_spec,
            {"kind": "Demo"},
            Path("out/demo.txt"),
            {"mode": "typed"},
            module_id="pkg.demo",
            is_entry=True,
        )
        host_program = host_registry.build_program_artifact_typed(
            fake_host_spec,
            [host_artifact],
            program_id="pkg.demo",
            entry_modules=["pkg.demo"],
        )
        static_program = static_registry.build_program_artifact_typed(
            fake_static_spec,
            [static_artifact],
            program_id="pkg.demo",
            entry_modules=["pkg.demo"],
        )

        self.assertEqual(host_artifact.module_id, "pkg.demo")
        self.assertEqual(host_artifact.label, "demo")
        self.assertEqual(static_artifact.text, "// Demo -> demo.txt")
        self.assertEqual(host_program.modules[0].text, host_artifact.text)
        self.assertEqual(static_program.to_legacy_dict()["modules"][0]["module_id"], "pkg.demo")


if __name__ == "__main__":
    unittest.main()

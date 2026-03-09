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

    def test_selfhost_cpp_entry_uses_direct_typed_compiler_path(self) -> None:
        selfhost_cpp = (ROOT / "selfhost" / "py2cpp.cpp").read_text(encoding="utf-8")
        selfhost_stage2 = (ROOT / "selfhost" / "py2cpp_stage2.cpp").read_text(encoding="utf-8")
        selfhost_src = (ROOT / "src" / "py2x-selfhost.py").read_text(encoding="utf-8")
        native_transpile = (ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "transpile_cli.h").read_text(encoding="utf-8")
        native_registry = (ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "backend_registry_static.h").read_text(encoding="utf-8")

        self.assertIn("load_east3_document_typed(", selfhost_src)
        self.assertIn("get_backend_spec_typed(", selfhost_src)
        self.assertIn("resolve_layer_options_typed(", selfhost_src)
        self.assertIn("lower_ir_typed(", selfhost_src)
        self.assertIn("optimize_ir_typed(", selfhost_src)
        self.assertIn("emit_source_typed(", selfhost_src)
        self.assertIn("apply_runtime_hook_typed(", selfhost_src)
        self.assertNotIn("def _load_east3(", selfhost_src)
        self.assertNotIn("def _get_spec(", selfhost_src)
        self.assertNotIn("def _resolve_opts(", selfhost_src)
        self.assertNotIn("def _emit(", selfhost_src)
        self.assertNotIn("def _apply_runtime(", selfhost_src)

        self.assertIn("load_east3_document_typed(", selfhost_cpp)
        self.assertIn("get_backend_spec_typed(", selfhost_cpp)
        self.assertIn("resolve_layer_options_typed(", selfhost_cpp)
        self.assertIn("lower_ir_typed(", selfhost_cpp)
        self.assertIn("optimize_ir_typed(", selfhost_cpp)
        self.assertIn("emit_source_typed(", selfhost_cpp)
        self.assertIn("apply_runtime_hook_typed(", selfhost_cpp)
        self.assertNotIn("_load_east3(", selfhost_cpp)
        self.assertNotIn("_get_spec(", selfhost_cpp)
        self.assertNotIn("_resolve_opts(", selfhost_cpp)
        self.assertNotIn("to_legacy_dict()", selfhost_cpp)

        self.assertIn("load_east3_document_typed", selfhost_stage2)
        self.assertIn("get_backend_spec_typed", selfhost_stage2)
        self.assertIn("resolve_layer_options_typed", selfhost_stage2)
        self.assertIn("lower_ir_typed", selfhost_stage2)
        self.assertIn("optimize_ir_typed", selfhost_stage2)
        self.assertIn("emit_source_typed", selfhost_stage2)
        self.assertIn("apply_runtime_hook_typed", selfhost_stage2)
        self.assertNotIn("_load_east3(", selfhost_stage2)
        self.assertNotIn("_get_spec(", selfhost_stage2)
        self.assertNotIn("_resolve_opts(", selfhost_stage2)
        self.assertNotIn("to_legacy_dict()", selfhost_stage2)

        self.assertIn("struct CompilerRootDocument", native_transpile)
        self.assertIn("load_east3_document_typed", native_transpile)
        self.assertIn("struct ResolvedBackendSpec", native_registry)
        self.assertIn("struct LayerOptionsCarrier", native_registry)
        self.assertIn("get_backend_spec_typed", native_registry)
        self.assertIn("emit_source_typed", native_registry)
        self.assertNotIn("dict<str, object> raw_spec;", native_registry)
        self.assertIn("dict<str, str> values;", native_registry)
        self.assertNotIn("dict<str, object> values;", native_registry)

    def test_native_cpp_typed_boundary_make_object_usage_stays_on_export_seams(self) -> None:
        native_transpile = (
            ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "transpile_cli.cpp"
        ).read_text(encoding="utf-8")
        native_registry = (
            ROOT / "src" / "runtime" / "cpp" / "native" / "compiler" / "backend_registry_static.cpp"
        ).read_text(encoding="utf-8")

        self.assertIn("CompilerRootDocument _load_json_root_document(", native_transpile)
        self.assertNotIn("dict<str, object> _load_json_root_dict(", native_transpile)
        self.assertNotIn("coerce_compiler_root_document(\n            _load_json_root_dict(", native_transpile)
        self.assertNotIn(
            "return pytra::compiler::transpile_cli::coerce_compiler_root_document(raw_doc, source_path, parser_backend);",
            native_transpile,
        )
        self.assertIn("pytra::std::json::JsonObj doc = root;", native_transpile)
        self.assertIn(
            "from toolchain.compiler.typed_boundary import export_compiler_root_document; ",
            native_transpile,
        )
        self.assertIn(
            "json.dumps(export_compiler_root_document(doc), ensure_ascii=False, indent=2)",
            native_transpile,
        )
        self.assertNotIn(
            "json.dumps(doc.to_legacy_dict(), ensure_ascii=False, indent=2)",
            native_transpile,
        )
        self.assertIn("dict<str, object> export_compiler_root_document(const CompilerRootDocument& doc)", native_transpile)
        self.assertIn(
            'str effective_source_path = source_path != "" ? source_path : _dict_get_str(raw_doc, "source_path");',
            native_transpile,
        )
        self.assertIn(
            '_dict_get_str(meta_dict, "parser_backend")',
            native_transpile,
        )
        self.assertIn("return export_compiler_root_document(\n        load_east3_document_typed(", native_transpile)
        self.assertNotIn("CompilerRootDocument::to_legacy_dict()", native_transpile)

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
            [],
        )
        self.assertIn('out.update(dict<str, object>(dict<str, str>{{"kind", doc.module_kind}}));', native_transpile)
        self.assertIn('dict<str, int64>{', native_transpile)
        self.assertIn('meta_dict.update(dict<str, object>(dict<str, str>{{"dispatch_mode", doc.meta.dispatch_mode}}));', native_transpile)
        self.assertIn('out.update(dict<str, object>(dict<str, dict<str, object>>{{"meta", meta_dict}}));', native_transpile)
        self.assertEqual(
            registry_make_object_lines,
            [],
        )
        self.assertIn("dict<str, object> export_backend_spec(const ResolvedBackendSpec& spec)", native_registry)
        self.assertIn("dict<str, object> export_layer_options(const LayerOptionsCarrier& options)", native_registry)
        self.assertIn('return dict<str, object>(', native_registry)
        self.assertIn('dict<str, str>{', native_registry)
        self.assertIn('{"target_lang", spec.carrier.target_lang},', native_registry)
        self.assertIn('{"extension", spec.carrier.extension},', native_registry)
        self.assertIn("return dict<str, object>(options.values);", native_registry)
        self.assertIn("return export_backend_spec(get_backend_spec_typed(target));", native_registry)
        self.assertIn("return LayerOptionsCarrier{layer, raw};", native_registry)
        self.assertIn("return LayerOptionsCarrier{layer, dict<str, str>(raw)};", native_registry)
        self.assertIn("return export_layer_options(resolve_layer_options_typed(_coerce_backend_spec(spec), layer, raw));", native_registry)
        self.assertIn("return pytra::compiler::transpile_cli::export_compiler_root_document(east);", native_registry)
        self.assertIn("return ir;", native_registry)
        self.assertIn("void apply_runtime_hook_typed(\n    const pytra::std::pathlib::Path& output_path\n)", native_registry)
        self.assertIn("apply_runtime_hook_typed(output_path);", native_registry)
        self.assertNotIn("apply_runtime_hook_typed(_coerce_backend_spec(spec), output_path);", native_registry)
        self.assertNotIn("return lower_ir(spec.to_legacy_dict(), east.to_legacy_dict(), lower_options.to_legacy_dict());", native_registry)
        self.assertNotIn("return optimize_ir(spec.to_legacy_dict(), ir, optimizer_options.to_legacy_dict());", native_registry)
        self.assertNotIn("ResolvedBackendSpec::to_legacy_dict()", native_registry)
        self.assertNotIn("LayerOptionsCarrier::to_legacy_dict()", native_registry)
        self.assertIn(
            'ir_path.write_text(pytra::std::json::_dump_json_dict(ir, true, ::std::nullopt, ",", ":", 0));',
            native_registry,
        )

    def test_compiler_transpile_cli_typed_shim_skips_legacy_wrapper(self) -> None:
        shim_src = (ROOT / "src" / "toolchain" / "compiler" / "transpile_cli.py").read_text(encoding="utf-8")
        generated_header = (
            ROOT / "src" / "runtime" / "cpp" / "generated" / "compiler" / "transpile_cli.h"
        ).read_text(encoding="utf-8")
        public_header = (
            ROOT / "src" / "runtime" / "cpp" / "pytra" / "compiler" / "transpile_cli.h"
        ).read_text(encoding="utf-8")
        generated_cpp = ROOT / "src" / "runtime" / "cpp" / "generated" / "compiler" / "transpile_cli.cpp"

        self.assertIn("return _front.load_east3_document_typed(", shim_src)
        self.assertNotIn("return coerce_compiler_root_document(", shim_src)

        self.assertFalse(generated_cpp.exists())
        self.assertIn('#include "runtime/cpp/native/compiler/transpile_cli.h"', generated_header)
        self.assertIn('#include "runtime/cpp/generated/compiler/transpile_cli.h"', public_header)
        self.assertNotIn('#include "runtime/cpp/native/compiler/transpile_cli.h"', public_header)

    def test_typed_backend_specs_preserve_legacy_metadata(self) -> None:
        py2x_src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        ir2lang_src = (ROOT / "src" / "ir2lang.py").read_text(encoding="utf-8")
        host_src = (ROOT / "src" / "toolchain" / "compiler" / "backend_registry.py").read_text(encoding="utf-8")
        static_src = (ROOT / "src" / "toolchain" / "compiler" / "backend_registry_static.py").read_text(encoding="utf-8")

        self.assertIn("from toolchain.compiler.typed_boundary import backend_spec_target", py2x_src)
        self.assertIn("from toolchain.compiler.typed_boundary import compiler_root_module_id", py2x_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_compiler_root_document", py2x_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_program_artifact_any", py2x_src)
        self.assertIn("return export_compiler_root_document(", py2x_src)
        self.assertIn("validate_ambient_global_target_support(linked_module.east_doc, target=target)", py2x_src)
        self.assertIn("program_artifact_any = export_program_artifact_any(", py2x_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_module_artifact", py2x_src)
        self.assertIn("module_carrier = coerce_module_artifact(module_artifact)", py2x_src)
        self.assertIn("module_id = compiler_root_module_id(east, fallback_output_path=output_path)", py2x_src)
        self.assertIn("list(collect_program_modules_typed(module_carrier))", py2x_src)
        self.assertIn("spec_target = backend_spec_target(spec)", py2x_src)
        self.assertIn("fallback_target=spec_target", py2x_src)
        self.assertNotIn("def _module_id_from_east(", py2x_src)
        self.assertNotIn(").to_legacy_dict()", py2x_src)
        self.assertNotIn("program_artifact_any = program_artifact.to_legacy_dict()", py2x_src)
        self.assertNotIn("program_carrier = coerce_program_artifact(", py2x_src)
        self.assertNotIn("if isinstance(program_artifact, dict):", py2x_src)
        self.assertNotIn('spec.carrier.target_lang if not isinstance(spec, dict)', py2x_src)
        self.assertNotIn("hasattr(program_artifact, \"to_legacy_dict\")", py2x_src)
        self.assertNotIn("hasattr(item, \"to_legacy_dict\")", py2x_src)
        self.assertNotIn("getattr(linked_module, \"east_doc\"", py2x_src)

        self.assertIn("from toolchain.compiler.typed_boundary import compiler_root_module_id", ir2lang_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_module_artifact", ir2lang_src)
        self.assertIn("from toolchain.compiler.typed_boundary import module_artifact_text", ir2lang_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_program_artifact_any", ir2lang_src)
        self.assertIn("from toolchain.link import LinkedProgramModule", ir2lang_src)
        self.assertIn("collect_program_modules_typed as collect_program_modules", ir2lang_src)
        self.assertIn("module_id = compiler_root_module_id(east_doc, fallback_output_path=output_path)", ir2lang_src)
        self.assertIn("validate_ambient_global_target_support(linked_module.east_doc, target=target)", ir2lang_src)
        self.assertIn("validate_runtime_abi_target_support(linked_module.east_doc, target=target)", ir2lang_src)
        self.assertIn("if module.is_entry and module.module_id in entry_set:", ir2lang_src)
        self.assertIn("module_path = Path(module.source_path) if module.source_path != \"\" else Path(module.module_id + \".py\")", ir2lang_src)
        self.assertIn("module_carrier = coerce_module_artifact(module_artifact)", ir2lang_src)
        self.assertIn("module_text = module_artifact_text(module_artifact)", ir2lang_src)
        self.assertIn("program_modules = list(collect_program_modules(module_carrier))", ir2lang_src)
        self.assertIn("writer_program_artifact = export_program_artifact_any(program_artifact)", ir2lang_src)
        self.assertNotIn("def _module_id_from_east(", ir2lang_src)
        self.assertNotIn("getattr(module, \"east_doc\"", ir2lang_src)
        self.assertNotIn("getattr(module, \"source_path\"", ir2lang_src)
        self.assertNotIn("getattr(module, \"module_id\"", ir2lang_src)
        self.assertNotIn("getattr(linked_module, \"east_doc\"", ir2lang_src)
        self.assertNotIn("module_artifact_dict = export_module_artifact_any(module_artifact)", ir2lang_src)
        self.assertNotIn("module_text_any = module_artifact_dict.get(", ir2lang_src)
        self.assertNotIn("hasattr(module_artifact, \"to_legacy_dict\")", ir2lang_src)
        self.assertNotIn("module_artifact.to_legacy_dict()", ir2lang_src)
        self.assertNotIn("program_artifact.to_legacy_dict()", ir2lang_src)

        self.assertIn("from toolchain.compiler.typed_boundary import export_compiler_root_document_any", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_compiler_root_document_any", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_resolved_backend_spec_any", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_resolved_backend_spec_any", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_layer_options_any", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_layer_options_any", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_ir_document", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_ir_document", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_module_artifact_or_none", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import coerce_module_artifact_or_none", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_module_artifact_any", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_module_artifact_any", static_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_program_artifact_any", host_src)
        self.assertIn("from toolchain.compiler.typed_boundary import export_program_artifact_any", static_src)
        self.assertIn("doc = export_compiler_root_document_any(east_doc)", host_src)
        self.assertIn("doc = export_compiler_root_document_any(east_doc)", static_src)
        self.assertNotIn(
            "doc = east_doc if isinstance(east_doc, dict) else export_compiler_root_document(coerce_compiler_root_document(east_doc))",
            host_src,
        )
        self.assertNotIn(
            "doc = east_doc if isinstance(east_doc, dict) else export_compiler_root_document(coerce_compiler_root_document(east_doc))",
            static_src,
        )
        self.assertIn("ir = fn(doc, export_layer_options_carrier(options))", host_src)
        self.assertIn("ir = fn(doc, export_layer_options_carrier(options))", static_src)
        self.assertIn("out = fn(ir, export_layer_options_carrier(options))", host_src)
        self.assertIn("out = fn(ir, export_layer_options_carrier(options))", static_src)
        self.assertIn("return coerce_ir_document(ir)", host_src)
        self.assertIn("return coerce_ir_document(ir)", static_src)
        self.assertIn("return coerce_ir_document(out)", host_src)
        self.assertIn("return coerce_ir_document(out)", static_src)
        self.assertIn("return coerce_ir_document(doc)", host_src)
        self.assertIn("return coerce_ir_document(doc)", static_src)
        self.assertIn("ir_document=coerce_ir_document(ir)", host_src)
        self.assertIn("ir_document=coerce_ir_document(ir)", static_src)
        self.assertIn("export_layer_options_carrier(request.emitter_options)", host_src)
        self.assertIn("export_layer_options_carrier(request.emitter_options)", static_src)
        self.assertIn("return export_resolved_backend_spec_any(_normalize_backend_runtime_spec(spec))", host_src)
        self.assertIn("return export_layer_options_any(resolve_layer_options_typed(spec, layer, raw_options))", host_src)
        self.assertIn("return export_layer_options_any(resolve_layer_options_typed(spec, layer, raw_options))", static_src)
        self.assertIn("return export_module_artifact_any(", host_src)
        self.assertIn("return export_module_artifact_any(", static_src)
        self.assertIn("return export_program_artifact_any(", host_src)
        self.assertIn("return export_program_artifact_any(", static_src)
        self.assertIn("return export_resolved_backend_spec_any(get_backend_spec_typed(target))", host_src)
        self.assertIn("_BACKEND_SPECS[target] = export_resolved_backend_spec_any(runtime_spec)", static_src)
        self.assertIn(
            "return [export_module_artifact_any(item) for item in collect_program_modules_typed(module_artifact)]",
            host_src,
        )
        self.assertIn(
            "return [export_module_artifact_any(item) for item in collect_program_modules_typed(module_artifact)]",
            static_src,
        )
        self.assertIn("carrier = coerce_module_artifact_or_none(module_artifact)", host_src)
        self.assertIn("carrier = coerce_module_artifact_or_none(module_artifact)", static_src)
        self.assertIn("coerced = coerce_module_artifact_or_none(item)", host_src)
        self.assertIn("coerced = coerce_module_artifact_or_none(item)", static_src)
        self.assertNotIn("coerce_compiler_root_document(east_doc).to_legacy_dict()", host_src)
        self.assertNotIn("coerce_compiler_root_document(east_doc).to_legacy_dict()", static_src)
        self.assertNotIn("return _normalize_backend_runtime_spec(spec).to_legacy_dict()", host_src)
        self.assertNotIn("return resolve_layer_options_typed(spec, layer, raw_options).to_legacy_dict()", host_src)
        self.assertNotIn("return resolve_layer_options_typed(spec, layer, raw_options).to_legacy_dict()", static_src)
        self.assertNotIn("coerce_module_artifact_carrier(", host_src)
        self.assertNotIn("coerce_module_artifact_carrier(", static_src)
        self.assertNotIn("dict(ir) if isinstance(ir, dict) else {}", host_src)
        self.assertNotIn("dict(ir) if isinstance(ir, dict) else {}", static_src)
        self.assertNotIn("def _normalize_module_artifact(", host_src)
        self.assertNotIn("def _normalize_module_artifact(", static_src)
        self.assertNotIn("def _default_module_label(", host_src)
        self.assertNotIn("def _default_module_label(", static_src)
        self.assertNotIn("def _flatten_helper_modules(", host_src)
        self.assertNotIn("def _coerce_module_artifact(", host_src)
        self.assertNotIn("def _coerce_module_artifact(", static_src)

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

    def test_export_compiler_root_document_matches_legacy_adapter(self) -> None:
        raw_doc = {
            "kind": "Module",
            "body": [],
            "source_path": "legacy.py",
            "meta": {"dispatch_mode": "native", "parser_backend": "legacy_host"},
        }
        doc = typed_boundary.coerce_compiler_root_document(
            raw_doc,
            source_path="demo.py",
            parser_backend="self_hosted",
        )

        self.assertEqual(
            typed_boundary.export_compiler_root_document(doc),
            doc.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_compiler_root_document(doc)["meta"]["parser_backend"],
            "self_hosted",
        )
        self.assertEqual(
            typed_boundary.export_compiler_root_document_any(doc),
            typed_boundary.export_compiler_root_document(doc),
        )
        legacy_doc = typed_boundary.coerce_compiler_root_document(raw_doc)
        self.assertEqual(legacy_doc.meta.source_path, "legacy.py")
        self.assertEqual(legacy_doc.meta.parser_backend, "legacy_host")
        self.assertEqual(
            typed_boundary.export_compiler_root_document_any(raw_doc),
            {
                "kind": "Module",
                "body": [],
                "source_path": "legacy.py",
                "east_stage": 0,
                "schema_version": 0,
                "meta": {
                    "dispatch_mode": "native",
                    "parser_backend": "legacy_host",
                },
            },
        )
        opts = typed_boundary.coerce_layer_options("emitter", {"mod_mode": "python", "debug": True})
        self.assertEqual(
            typed_boundary.export_layer_options_carrier(opts),
            opts.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_layer_options_any(opts),
            typed_boundary.export_layer_options_carrier(opts),
        )
        host_registry._SPEC_CACHE.clear()
        host_spec = host_registry.get_backend_spec_typed("cpp")
        static_spec = static_registry.get_backend_spec_typed("cpp")
        self.assertEqual(
            typed_boundary.export_resolved_backend_spec(host_spec),
            host_spec.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_resolved_backend_spec(static_spec),
            static_spec.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_resolved_backend_spec_any(host_spec),
            typed_boundary.export_resolved_backend_spec(host_spec),
        )
        self.assertEqual(
            typed_boundary.export_resolved_backend_spec_any(static_spec),
            typed_boundary.export_resolved_backend_spec(static_spec),
        )
        self.assertEqual(typed_boundary.backend_spec_target(host_spec), "cpp")
        self.assertEqual(typed_boundary.backend_spec_target(static_spec), "cpp")
        self.assertEqual(typed_boundary.backend_spec_target({"target_lang": "rs", "extension": ".rs"}), "rs")
        self.assertEqual(
            typed_boundary.compiler_root_module_id(
                {
                    "kind": "Module",
                    "meta": {"module_id": "pkg.demo"},
                },
                fallback_output_path=Path("fallback.cpp"),
            ),
            "pkg.demo",
        )
        self.assertEqual(
            typed_boundary.compiler_root_module_id(
                doc,
                fallback_output_path=Path("demo.cpp"),
            ),
            "demo",
        )
        module = typed_boundary.coerce_module_artifact(
            {
                "module_id": "pkg.demo",
                "kind": "user",
                "label": "demo",
                "extension": ".cpp",
                "text": "// demo\n",
                "is_entry": True,
                "dependencies": ["pkg.helper"],
                "metadata": {"owner": "pkg.demo"},
            }
        )
        self.assertEqual(
            typed_boundary.export_module_artifact_carrier(module),
            module.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_module_artifact_any(module),
            typed_boundary.export_module_artifact_carrier(module),
        )
        self.assertEqual(typed_boundary.module_artifact_text(module), "// demo\n")
        program = typed_boundary.build_program_artifact_carrier(
            host_spec,
            [module],
            program_id="pkg.demo",
            entry_modules=["pkg.demo"],
        )
        self.assertEqual(
            typed_boundary.export_program_artifact_carrier(program),
            program.to_legacy_dict(),
        )
        self.assertEqual(
            typed_boundary.export_program_artifact_any(program),
            typed_boundary.export_program_artifact_carrier(program),
        )
        helper_program = typed_boundary.coerce_program_artifact(
            {
                "modules": [
                    {
                        "module_id": "pkg.demo",
                        "kind": "user",
                        "label": "demo",
                        "extension": ".cpp",
                        "text": "// demo\n",
                        "is_entry": True,
                        "helper_modules": [
                            {
                                "module_id": "__pytra_helper__.cpp.demo",
                                "text": "// helper\n",
                                "metadata": {"helper_id": "cpp.demo", "owner_module_id": "pkg.demo"},
                            }
                        ],
                    }
                ]
            },
            fallback_target="cpp",
            fallback_program_id="pkg.demo",
            fallback_entry_modules=["pkg.demo"],
        )
        self.assertEqual(helper_program.target, "cpp")
        self.assertEqual(helper_program.program_id, "pkg.demo")
        self.assertEqual(len(helper_program.modules), 2)
        self.assertEqual(helper_program.modules[1].kind, "helper")
        self.assertEqual(helper_program.modules[1].metadata["owner_module_id"], "pkg.demo")

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
        host_program = host_registry.build_program_artifact_typed(
            fake_spec,
            [helper_module, user_module],
            program_id="pkg.main",
            entry_modules=["pkg.main"],
        )
        self.assertEqual(
            typed_boundary.export_program_artifact_carrier(host_program),
            host_program.to_legacy_dict(),
        )

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

"""Backend registry for unified ``py2x`` frontend."""

from __future__ import annotations

from typing import Any
from pytra.std.pathlib import Path
from toolchain.compiler.typed_boundary import BackendSpecCarrier
from toolchain.compiler.typed_boundary import EmitRequestCarrier
from toolchain.compiler.typed_boundary import LayerOptionsCarrier
from toolchain.compiler.typed_boundary import ModuleArtifactCarrier
from toolchain.compiler.typed_boundary import ProgramArtifactCarrier
from toolchain.compiler.typed_boundary import ResolvedBackendSpec
from toolchain.compiler.typed_boundary import build_program_artifact_carrier
from toolchain.compiler.typed_boundary import coerce_backend_spec
from toolchain.compiler.typed_boundary import coerce_ir_document
from toolchain.compiler.typed_boundary import coerce_layer_options
from toolchain.compiler.typed_boundary import coerce_module_artifact_or_none
from toolchain.compiler.typed_boundary import copy_module_dependencies
from toolchain.compiler.typed_boundary import copy_module_metadata
from toolchain.compiler.typed_boundary import copy_program_writer_options
from toolchain.compiler.typed_boundary import export_compiler_root_document_any
from toolchain.compiler.typed_boundary import export_resolved_backend_spec_any
from toolchain.compiler.typed_boundary import export_layer_options_any
from toolchain.compiler.typed_boundary import export_layer_options_carrier
from toolchain.compiler.typed_boundary import export_module_artifact_any
from toolchain.compiler.typed_boundary import export_module_artifact_carrier
from toolchain.compiler.typed_boundary import export_program_artifact_any
from toolchain.compiler.typed_boundary import export_program_artifact_carrier
from toolchain.compiler.typed_boundary import flatten_module_artifact_carrier
from toolchain.compiler.typed_boundary import normalize_module_artifact_carrier
from toolchain.compiler.typed_boundary import resolve_layer_options_carrier

from backends.cs.lower import lower_east3_to_cs_ir
from backends.cs.optimizer import optimize_cs_ir
from backends.cs.emitter.cs_emitter import transpile_to_csharp
from backends.common.program_writer import write_single_file_program
from backends.cpp.program_writer import write_cpp_program
from backends.go.lower import lower_east3_to_go_ir
from backends.go.optimizer import optimize_go_ir
from backends.go.emitter import transpile_to_go_native
from backends.java.lower import lower_east3_to_java_ir
from backends.java.optimizer import optimize_java_ir
from backends.java.emitter import transpile_to_java_native
from backends.js.lower import lower_east3_to_js_ir
from backends.js.optimizer import optimize_js_ir
from backends.js.emitter.js_emitter import transpile_to_js
from backends.kotlin.lower import lower_east3_to_kotlin_ir
from backends.kotlin.optimizer import optimize_kotlin_ir
from backends.kotlin.emitter import transpile_to_kotlin_native
from backends.lua.lower import lower_east3_to_lua_ir
from backends.lua.optimizer import optimize_lua_ir
from backends.lua.emitter import transpile_to_lua_native
from backends.nim.emitter import transpile_to_nim_native
from backends.php.lower import lower_east3_to_php_ir
from backends.php.optimizer import optimize_php_ir
from backends.php.emitter import transpile_to_php_native
from backends.rs.lower import lower_east3_to_rs_ir
from backends.rs.optimizer import optimize_rs_ir
from backends.rs.emitter.rs_emitter import transpile_to_rust
from backends.ruby.lower import lower_east3_to_ruby_ir
from backends.ruby.optimizer import optimize_ruby_ir
from backends.ruby.emitter import transpile_to_ruby_native
from backends.scala.lower import lower_east3_to_scala_ir
from backends.scala.optimizer import optimize_scala_ir
from backends.scala.emitter import transpile_to_scala_native
from backends.swift.lower import lower_east3_to_swift_ir
from backends.swift.optimizer import optimize_swift_ir
from backends.swift.emitter import transpile_to_swift_native
from backends.ts.lower import lower_east3_to_ts_ir
from backends.ts.optimizer import optimize_ts_ir
from backends.ts.emitter.ts_emitter import transpile_to_typescript
from backends.cpp.emitter import transpile_to_cpp
from toolchain.compiler.js_runtime_shims import write_js_runtime_shims


def _src_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _identity_ir(doc: dict[str, Any]) -> dict[str, Any]:
    return doc if isinstance(doc, dict) else {}


def _empty_emit(_ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return ""


def _default_output_path_for(input_path: Path, ext: str) -> Path:
    stem = str(input_path)
    if stem.endswith(".py"):
        stem = stem[:-3]
    elif stem.endswith(".json"):
        stem = stem[:-5]
    return Path(stem + ext)


def _copy_runtime_file(src_rel: str, output_path: Path, dst_name: str) -> None:
    src = _src_root() / src_rel
    if not src.exists():
        raise RuntimeError("runtime source not found: " + str(src))
    dst = output_path.parent / dst_name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _copy_php_runtime(output_path: Path) -> None:
    src_root = _src_root() / "runtime" / "php"
    if not src_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(src_root))
    dst_root = output_path.parent / "pytra"
    files = [
        ("pytra-core/py_runtime.php", "py_runtime.php"),
        ("pytra-core/std/time.php", "std/time.php"),
        ("pytra-gen/runtime/png.php", "runtime/png.php"),
        ("pytra-gen/runtime/gif.php", "runtime/gif.php"),
    ]
    for src_rel, dst_rel in files:
        src = src_root / src_rel
        if not src.exists():
            raise RuntimeError("php runtime source missing: " + str(src))
        dst = dst_root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _emit_java(ir: dict[str, Any], output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    class_name = output_path.stem if output_path.stem != "" else "Main"
    return transpile_to_java_native(ir, class_name=class_name)


def _emit_cpp(ir: dict[str, Any], _output_path: Path, emitter_options: dict[str, Any] | None = None) -> str:
    opts = emitter_options if isinstance(emitter_options, dict) else {}
    negative_index_mode = str(opts.get("negative_index_mode", "const_only"))
    bounds_check_mode = str(opts.get("bounds_check_mode", "off"))
    floor_div_mode = str(opts.get("floor_div_mode", "native"))
    mod_mode = str(opts.get("mod_mode", "native"))
    return transpile_to_cpp(
        ir,
        negative_index_mode=negative_index_mode,
        bounds_check_mode=bounds_check_mode,
        floor_div_mode=floor_div_mode,
        mod_mode=mod_mode,
    )


def _emit_rs(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_rust(ir)


def _emit_cs(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_csharp(ir)


def _emit_js(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_js(ir)


def _emit_ts(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_typescript(ir)


def _emit_go(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_go_native(ir)


def _emit_kotlin(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_kotlin_native(ir)


def _emit_swift(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_swift_native(ir)


def _emit_ruby(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_ruby_native(ir)


def _emit_lua(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_lua_native(ir)


def _emit_scala(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_scala_native(ir)


def _emit_php(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_php_native(ir)


def _emit_nim(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    return transpile_to_nim_native(ir)


def _runtime_none(_output_path: Path) -> None:
    return


def _runtime_js_shims(output_path: Path) -> None:
    write_js_runtime_shims(output_path.parent)


def _runtime_rs(output_path: Path) -> None:
    _copy_runtime_file("runtime/rs/pytra-core/built_in/py_runtime.rs", output_path, "py_runtime.rs")
    _copy_runtime_file("runtime/rs/pytra-gen/utils/image_runtime.rs", output_path, "image_runtime.rs")


def _runtime_go(output_path: Path) -> None:
    _copy_runtime_file("runtime/go/pytra-core/built_in/py_runtime.go", output_path, "py_runtime.go")
    _copy_runtime_file("runtime/go/pytra-gen/utils/png.go", output_path, "png.go")
    _copy_runtime_file("runtime/go/pytra-gen/utils/gif.go", output_path, "gif.go")


def _runtime_java(output_path: Path) -> None:
    _copy_runtime_file("runtime/java/pytra-core/built_in/PyRuntime.java", output_path, "PyRuntime.java")
    _copy_runtime_file("runtime/java/pytra-core/std/time_impl.java", output_path, "_impl.java")
    _copy_runtime_file("runtime/java/pytra-core/std/math_impl.java", output_path, "_m.java")
    _copy_runtime_file("runtime/java/pytra-gen/utils/png.java", output_path, "png.java")
    _copy_runtime_file("runtime/java/pytra-gen/utils/gif.java", output_path, "gif.java")
    _copy_runtime_file("runtime/java/pytra-gen/std/time.java", output_path, "time.java")
    _copy_runtime_file("runtime/java/pytra-gen/std/json.java", output_path, "json.java")
    _copy_runtime_file("runtime/java/pytra-gen/std/pathlib.java", output_path, "pathlib.java")
    _copy_runtime_file("runtime/java/pytra-gen/std/math.java", output_path, "math.java")


def _runtime_kotlin(output_path: Path) -> None:
    _copy_runtime_file("runtime/kotlin/pytra-core/built_in/py_runtime.kt", output_path, "py_runtime.kt")
    _copy_runtime_file("runtime/kotlin/pytra-gen/utils/image_runtime.kt", output_path, "image_runtime.kt")


def _runtime_swift(output_path: Path) -> None:
    _copy_runtime_file("runtime/swift/pytra-core/built_in/py_runtime.swift", output_path, "py_runtime.swift")
    _copy_runtime_file("runtime/swift/pytra-gen/utils/image_runtime.swift", output_path, "image_runtime.swift")


def _runtime_ruby(output_path: Path) -> None:
    _copy_runtime_file("runtime/ruby/pytra-core/built_in/py_runtime.rb", output_path, "py_runtime.rb")
    _copy_runtime_file("runtime/ruby/pytra-gen/utils/image_runtime.rb", output_path, "image_runtime.rb")


def _runtime_lua(output_path: Path) -> None:
    _copy_runtime_file("runtime/lua/pytra-core/built_in/py_runtime.lua", output_path, "py_runtime.lua")
    _copy_runtime_file("runtime/lua/pytra-gen/utils/image_runtime.lua", output_path, "image_runtime.lua")


def _runtime_scala(output_path: Path) -> None:
    _copy_runtime_file("runtime/scala/pytra-core/built_in/py_runtime.scala", output_path, "py_runtime.scala")
    _copy_runtime_file("runtime/scala/pytra-gen/utils/image_runtime.scala", output_path, "image_runtime.scala")


def _runtime_nim(output_path: Path) -> None:
    _copy_runtime_file("runtime/nim/pytra-core/built_in/py_runtime.nim", output_path, "py_runtime.nim")
    _copy_runtime_file("runtime/nim/pytra-gen/utils/image_runtime.nim", output_path, "image_runtime.nim")


BackendSpec = dict[str, Any]


def _default_module_label(module_id: str, output_path: Path) -> str:
    if output_path.stem != "":
        return output_path.stem
    if module_id != "":
        tail = module_id.rsplit(".", 1)[-1]
        if tail != "":
            return tail
    return "module"


def _normalize_module_artifact(
    artifact_any: Any,
    *,
    module_id: str,
    output_path: Path,
    extension: str,
    is_entry: bool,
) -> dict[str, Any]:
    artifact = artifact_any if isinstance(artifact_any, dict) else {}
    text = artifact_any if isinstance(artifact_any, str) else artifact.get("text", "")
    module_id_out = artifact.get("module_id", module_id)
    if not isinstance(module_id_out, str) or module_id_out == "":
        module_id_out = module_id if module_id != "" else _default_module_label("", output_path)
    label = artifact.get("label", "")
    if not isinstance(label, str) or label == "":
        label = _default_module_label(module_id_out, output_path)
    extension_out = artifact.get("extension", extension)
    if not isinstance(extension_out, str) or extension_out == "":
        extension_out = extension if extension != "" else output_path.suffix
    dependencies_out: list[str] = []
    dependencies_any = artifact.get("dependencies", [])
    if isinstance(dependencies_any, list):
        for item in dependencies_any:
            if isinstance(item, str) and item != "":
                dependencies_out.append(item)
    metadata_any = artifact.get("metadata", {})
    metadata_out = metadata_any if isinstance(metadata_any, dict) else {}
    is_entry_out = artifact.get("is_entry", is_entry)
    return {
        "module_id": module_id_out,
        "label": label,
        "extension": extension_out,
        "text": text if isinstance(text, str) else "",
        "is_entry": bool(is_entry_out),
        "dependencies": dependencies_out,
        "metadata": dict(metadata_out),
    }


def _legacy_emit_module_adapter(emit_impl: Any, *, extension: str) -> Any:
    def _emit_module(
        ir: dict[str, Any],
        output_path: Path,
        emitter_options: dict[str, Any] | None = None,
        *,
        module_id: str = "",
        is_entry: bool = False,
    ) -> dict[str, Any]:
        source_any: Any = ""
        try:
            source_any = emit_impl(ir, output_path, emitter_options if isinstance(emitter_options, dict) else {})
        except TypeError:
            source_any = emit_impl(ir, output_path)
        return _normalize_module_artifact(
            source_any,
            module_id=module_id,
            output_path=output_path,
            extension=extension,
            is_entry=is_entry,
        )

    return _emit_module


_BACKEND_SPECS: dict[str, BackendSpec] = {
    "cpp": {
        "target_lang": "cpp",
        "extension": ".cpp",
        "lower": _identity_ir,
        "optimizer": _identity_ir,
        "emit": _emit_cpp,
        "program_writer": write_cpp_program,
        "runtime_hook": _runtime_none,
        "default_options": {
            "lower": {},
            "optimizer": {},
            "emitter": {
                "negative_index_mode": "const_only",
                "bounds_check_mode": "off",
                "floor_div_mode": "native",
                "mod_mode": "native",
            },
        },
        "option_schema": {
            "lower": {},
            "optimizer": {},
            "emitter": {
                "negative_index_mode": {"type": "str", "choices": ["always", "const_only", "off"]},
                "bounds_check_mode": {"type": "str", "choices": ["off", "always", "debug"]},
                "floor_div_mode": {"type": "str", "choices": ["native", "python"]},
                "mod_mode": {"type": "str", "choices": ["native", "python"]},
            },
        },
    },
    "rs": {
        "target_lang": "rs",
        "extension": ".rs",
        "lower": lower_east3_to_rs_ir,
        "optimizer": optimize_rs_ir,
        "emit": _emit_rs,
        "runtime_hook": _runtime_rs,
    },
    "cs": {
        "target_lang": "cs",
        "extension": ".cs",
        "lower": lower_east3_to_cs_ir,
        "optimizer": optimize_cs_ir,
        "emit": _emit_cs,
        "runtime_hook": _runtime_none,
    },
    "js": {
        "target_lang": "js",
        "extension": ".js",
        "lower": lower_east3_to_js_ir,
        "optimizer": optimize_js_ir,
        "emit": _emit_js,
        "runtime_hook": _runtime_js_shims,
    },
    "ts": {
        "target_lang": "ts",
        "extension": ".ts",
        "lower": lower_east3_to_ts_ir,
        "optimizer": optimize_ts_ir,
        "emit": _emit_ts,
        "runtime_hook": _runtime_js_shims,
    },
    "go": {
        "target_lang": "go",
        "extension": ".go",
        "lower": lower_east3_to_go_ir,
        "optimizer": optimize_go_ir,
        "emit": _emit_go,
        "runtime_hook": _runtime_go,
    },
    "java": {
        "target_lang": "java",
        "extension": ".java",
        "lower": lower_east3_to_java_ir,
        "optimizer": optimize_java_ir,
        "emit": _emit_java,
        "runtime_hook": _runtime_java,
    },
    "kotlin": {
        "target_lang": "kotlin",
        "extension": ".kt",
        "lower": lower_east3_to_kotlin_ir,
        "optimizer": optimize_kotlin_ir,
        "emit": _emit_kotlin,
        "runtime_hook": _runtime_kotlin,
    },
    "swift": {
        "target_lang": "swift",
        "extension": ".swift",
        "lower": lower_east3_to_swift_ir,
        "optimizer": optimize_swift_ir,
        "emit": _emit_swift,
        "runtime_hook": _runtime_swift,
    },
    "ruby": {
        "target_lang": "ruby",
        "extension": ".rb",
        "lower": lower_east3_to_ruby_ir,
        "optimizer": optimize_ruby_ir,
        "emit": _emit_ruby,
        "runtime_hook": _runtime_ruby,
    },
    "lua": {
        "target_lang": "lua",
        "extension": ".lua",
        "lower": lower_east3_to_lua_ir,
        "optimizer": optimize_lua_ir,
        "emit": _emit_lua,
        "runtime_hook": _runtime_lua,
    },
    "scala": {
        "target_lang": "scala",
        "extension": ".scala",
        "lower": lower_east3_to_scala_ir,
        "optimizer": optimize_scala_ir,
        "emit": _emit_scala,
        "runtime_hook": _runtime_scala,
    },
    "php": {
        "target_lang": "php",
        "extension": ".php",
        "lower": lower_east3_to_php_ir,
        "optimizer": optimize_php_ir,
        "emit": _emit_php,
        "runtime_hook": _copy_php_runtime,
    },
    "nim": {
        "target_lang": "nim",
        "extension": ".nim",
        "lower": _identity_ir,
        "optimizer": _identity_ir,
        "emit": _emit_nim,
        "runtime_hook": _runtime_nim,
    },
}


_BACKEND_RUNTIME_SPECS: dict[str, ResolvedBackendSpec] = {}


def _normalize_backend_runtime_spec(spec: BackendSpec) -> ResolvedBackendSpec:
    normalized = dict(spec)
    extension = str(normalized.get("extension", ""))
    defaults = normalized.get("default_options")
    if not isinstance(defaults, dict):
        defaults = {}
    default_lower = defaults.get("lower")
    if not isinstance(default_lower, dict):
        default_lower = {}
    default_optimizer = defaults.get("optimizer")
    if not isinstance(default_optimizer, dict):
        default_optimizer = {}
    default_emitter = defaults.get("emitter")
    if not isinstance(default_emitter, dict):
        default_emitter = {}
    normalized["default_options"] = {
        "lower": dict(default_lower),
        "optimizer": dict(default_optimizer),
        "emitter": dict(default_emitter),
    }

    schemas = normalized.get("option_schema")
    if not isinstance(schemas, dict):
        schemas = {}
    schema_lower = schemas.get("lower")
    if not isinstance(schema_lower, dict):
        schema_lower = {}
    schema_optimizer = schemas.get("optimizer")
    if not isinstance(schema_optimizer, dict):
        schema_optimizer = {}
    schema_emitter = schemas.get("emitter")
    if not isinstance(schema_emitter, dict):
        schema_emitter = {}
    normalized["option_schema"] = {
        "lower": dict(schema_lower),
        "optimizer": dict(schema_optimizer),
        "emitter": dict(schema_emitter),
    }

    lower_impl = normalized.get("lower")
    if not callable(lower_impl):
        lower_impl = _identity_ir
    optimizer_impl = normalized.get("optimizer")
    if not callable(optimizer_impl):
        optimizer_impl = _identity_ir
    emit_impl = normalized.get("emit")
    if not callable(emit_impl):
        emit_impl = _empty_emit
    emit_module_impl = normalized.get("emit_module")
    if not callable(emit_module_impl):
        emit_module_impl = _legacy_emit_module_adapter(emit_impl, extension=extension)
    program_writer_impl = normalized.get("program_writer")
    if not callable(program_writer_impl) and not isinstance(program_writer_impl, dict):
        program_writer_impl = write_single_file_program
    runtime_hook_impl = normalized.get("runtime_hook")
    if runtime_hook_impl is None:
        runtime_hook_impl = _runtime_none

    carrier = BackendSpecCarrier.from_legacy_spec(normalized)
    return ResolvedBackendSpec(
        carrier=carrier,
        lower_impl=lower_impl,
        optimizer_impl=optimizer_impl,
        emit_impl=emit_impl,
        emit_module_impl=emit_module_impl,
        program_writer_impl=program_writer_impl,
        runtime_hook_impl=runtime_hook_impl,
    )


def _normalize_backend_specs() -> None:
    for target, spec in list(_BACKEND_SPECS.items()):
        runtime_spec = _normalize_backend_runtime_spec(spec)
        _BACKEND_RUNTIME_SPECS[target] = runtime_spec
        _BACKEND_SPECS[target] = export_resolved_backend_spec_any(runtime_spec)


def _coerce_runtime_spec(spec: BackendSpec | ResolvedBackendSpec) -> ResolvedBackendSpec:
    return coerce_backend_spec(spec)


def _normalize_module_artifact_typed(
    artifact_any: Any,
    *,
    request: EmitRequestCarrier,
) -> ModuleArtifactCarrier:
    return normalize_module_artifact_carrier(
        artifact_any,
        module_id=request.module_id,
        output_path=request.output_path,
        extension=request.spec.extension,
        is_entry=request.is_entry,
    )


_normalize_backend_specs()


def list_backend_targets() -> list[str]:
    return list(_BACKEND_SPECS.keys())


def get_backend_spec_typed(target: str) -> ResolvedBackendSpec:
    if target not in _BACKEND_RUNTIME_SPECS:
        raise RuntimeError("unsupported target: " + target)
    return _BACKEND_RUNTIME_SPECS[target]


def get_backend_spec(target: str) -> BackendSpec:
    if target not in _BACKEND_SPECS:
        raise RuntimeError("unsupported target: " + target)
    return _BACKEND_SPECS[target]


def default_output_path(input_path: Path, target: str) -> Path:
    spec = get_backend_spec_typed(target)
    return _default_output_path_for(input_path, spec.carrier.extension)


def resolve_layer_options_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    layer: str,
    raw_options: dict[str, str],
) -> LayerOptionsCarrier:
    runtime_spec = _coerce_runtime_spec(spec)
    return resolve_layer_options_carrier(runtime_spec, layer, raw_options)


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict[str, str]) -> dict[str, Any]:
    return export_layer_options_any(resolve_layer_options_typed(spec, layer, raw_options))


def lower_ir_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    east_doc: dict[str, Any] | object,
    lower_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_spec = _coerce_runtime_spec(spec)
    doc = export_compiler_root_document_any(east_doc)
    options = lower_options if isinstance(lower_options, LayerOptionsCarrier) else coerce_layer_options("lower", lower_options)
    fn = runtime_spec.lower_impl
    if not callable(fn):
        return _identity_ir(doc)
    try:
        ir = fn(doc, export_layer_options_carrier(options))
    except TypeError:
        ir = fn(doc)
    return coerce_ir_document(ir)


def lower_ir(spec: BackendSpec, east_doc: dict[str, Any], lower_options: dict[str, Any] | None = None) -> dict[str, Any]:
    return lower_ir_typed(spec, east_doc, lower_options)


def optimize_ir_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    ir: dict[str, Any],
    optimizer_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_spec = _coerce_runtime_spec(spec)
    options = (
        optimizer_options
        if isinstance(optimizer_options, LayerOptionsCarrier)
        else coerce_layer_options("optimizer", optimizer_options)
    )
    fn = runtime_spec.optimizer_impl
    if not callable(fn):
        return _identity_ir(ir)
    try:
        out = fn(ir, export_layer_options_carrier(options))
    except TypeError:
        out = fn(ir)
    return coerce_ir_document(out)


def optimize_ir(spec: BackendSpec, ir: dict[str, Any], optimizer_options: dict[str, Any] | None = None) -> dict[str, Any]:
    return optimize_ir_typed(spec, ir, optimizer_options)


def emit_module_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: LayerOptionsCarrier | dict[str, Any] | None = None,
    *,
    module_id: str = "",
    is_entry: bool = False,
) -> ModuleArtifactCarrier:
    runtime_spec = _coerce_runtime_spec(spec)
    options = (
        emitter_options
        if isinstance(emitter_options, LayerOptionsCarrier)
        else coerce_layer_options("emitter", emitter_options)
    )
    request = EmitRequestCarrier(
        spec=runtime_spec.carrier,
        ir_document=coerce_ir_document(ir),
        output_path=output_path,
        emitter_options=options,
        module_id=module_id,
        is_entry=is_entry,
    )
    fn = runtime_spec.emit_module_impl
    artifact_any: Any = {}
    try:
        artifact_any = fn(
            request.ir_document,
            request.output_path,
            export_layer_options_carrier(request.emitter_options),
            module_id=request.module_id,
            is_entry=request.is_entry,
        )
    except TypeError:
        try:
            artifact_any = fn(request.ir_document, request.output_path, export_layer_options_carrier(request.emitter_options))
        except TypeError:
            artifact_any = fn(request.ir_document, request.output_path)
    return _normalize_module_artifact_typed(artifact_any, request=request)


def emit_module(
    spec: BackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: dict[str, Any] | None = None,
    *,
    module_id: str = "",
    is_entry: bool = False,
) -> dict[str, Any]:
    return export_module_artifact_any(
        emit_module_typed(
            spec,
            ir,
            output_path,
            emitter_options,
            module_id=module_id,
            is_entry=is_entry,
        )
    )


def build_program_artifact_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    modules: list[ModuleArtifactCarrier | dict[str, Any]],
    *,
    program_id: str = "",
    entry_modules: list[str] | None = None,
    layout_mode: str = "single_file",
    link_output_schema: str = "",
    writer_options: dict[str, object] | None = None,
) -> ProgramArtifactCarrier:
    runtime_spec = _coerce_runtime_spec(spec)
    module_list: list[ModuleArtifactCarrier] = []
    for item in modules:
        coerced = coerce_module_artifact_or_none(item)
        if coerced is not None:
            module_list.append(coerced)
    return build_program_artifact_carrier(
        runtime_spec,
        module_list,
        program_id=program_id,
        entry_modules=entry_modules,
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=copy_program_writer_options(writer_options),
    )


def build_program_artifact(
    spec: BackendSpec,
    modules: list[dict[str, Any]],
    *,
    program_id: str = "",
    entry_modules: list[str] | None = None,
    layout_mode: str = "single_file",
    link_output_schema: str = "",
    writer_options: dict[str, object] | None = None,
) -> dict[str, Any]:
    return export_program_artifact_any(
        build_program_artifact_typed(
            spec,
            modules,
            program_id=program_id,
            entry_modules=entry_modules,
            layout_mode=layout_mode,
            link_output_schema=link_output_schema,
            writer_options=writer_options,
        )
    )


def collect_program_modules_typed(module_artifact: ModuleArtifactCarrier | dict[str, Any]) -> tuple[ModuleArtifactCarrier, ...]:
    carrier = coerce_module_artifact_or_none(module_artifact)
    if carrier is None:
        return ()
    return flatten_module_artifact_carrier(carrier)


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return [export_module_artifact_any(item) for item in collect_program_modules_typed(module_artifact)]


def get_program_writer_typed(spec: BackendSpec | ResolvedBackendSpec) -> Any:
    runtime_spec = _coerce_runtime_spec(spec)
    return runtime_spec.program_writer_impl


def get_program_writer(spec: BackendSpec) -> Any:
    return get_program_writer_typed(spec)


def emit_source(
    spec: BackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: dict[str, Any] | None = None,
) -> str:
    return emit_source_typed(spec, ir, output_path, emitter_options)


def emit_source_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> str:
    return emit_module_typed(spec, ir, output_path, emitter_options).text


def apply_runtime_hook_typed(spec: BackendSpec | ResolvedBackendSpec, output_path: Path) -> None:
    runtime_spec = _coerce_runtime_spec(spec)
    fn = runtime_spec.runtime_hook_impl
    if callable(fn):
        fn(output_path)


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    apply_runtime_hook_typed(spec, output_path)

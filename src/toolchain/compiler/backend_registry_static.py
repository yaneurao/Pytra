"""Backend registry for unified ``py2x`` frontend."""

from __future__ import annotations

from typing import Any
from pytra.std.pathlib import Path
from toolchain.compiler.backend_registry_metadata import build_backend_spec_metadata
from toolchain.compiler.backend_registry_metadata import get_backend_emit_kind
from toolchain.compiler.backend_registry_metadata import get_backend_emit_ref
from toolchain.compiler.backend_registry_metadata import get_backend_lower_ref
from toolchain.compiler.backend_registry_metadata import get_backend_optimizer_ref
from toolchain.compiler.backend_registry_metadata import get_backend_program_writer_key
from toolchain.compiler.backend_registry_metadata import get_backend_runtime_hook_key
from toolchain.compiler.backend_registry_metadata import get_program_writer_ref
from toolchain.compiler.backend_registry_metadata import get_runtime_hook_descriptor
from toolchain.compiler.backend_registry_metadata import list_backend_targets as metadata_backend_targets
from toolchain.compiler.typed_boundary import LayerOptionsCarrier
from toolchain.compiler.typed_boundary import ModuleArtifactCarrier
from toolchain.compiler.typed_boundary import ProgramArtifactCarrier
from toolchain.compiler.typed_boundary import ResolvedBackendSpec
from toolchain.compiler.typed_boundary import build_program_artifact_from_modules
from toolchain.compiler.typed_boundary import build_resolved_backend_spec
from toolchain.compiler.typed_boundary import coerce_backend_spec
from toolchain.compiler.typed_boundary import coerce_ir_document
from toolchain.compiler.typed_boundary import collect_program_module_carriers
from toolchain.compiler.typed_boundary import copy_module_dependencies
from toolchain.compiler.typed_boundary import copy_module_metadata
from toolchain.compiler.typed_boundary import emit_source_text_with_spec
from toolchain.compiler.typed_boundary import execute_emit_module_with_spec
from toolchain.compiler.typed_boundary import execute_lower_ir_with_spec
from toolchain.compiler.typed_boundary import execute_optimize_ir_with_spec
from toolchain.compiler.typed_boundary import export_resolved_backend_spec_any
from toolchain.compiler.typed_boundary import export_layer_options_any
from toolchain.compiler.typed_boundary import export_module_artifact_any
from toolchain.compiler.typed_boundary import export_program_module_artifacts
from toolchain.compiler.typed_boundary import export_program_artifact_any
from toolchain.compiler.typed_boundary import get_program_writer_with_spec
from toolchain.compiler.typed_boundary import resolve_layer_options_carrier
from toolchain.compiler.typed_boundary import apply_runtime_hook_with_spec

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
    return coerce_ir_document(doc)


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


def _copy_runtime_files(file_specs: list[object], output_path: Path) -> None:
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid runtime file descriptor")
        src_rel = item[0]
        dst_name = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_name, str):
            raise RuntimeError("invalid runtime file descriptor")
        _copy_runtime_file(src_rel, output_path, dst_name)


def _copy_php_runtime_files(file_specs: list[object], output_path: Path) -> None:
    src_root = _src_root() / "runtime" / "php"
    if not src_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(src_root))
    dst_root = output_path.parent / "pytra"
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid php runtime file descriptor")
        src_rel = item[0]
        dst_rel = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_rel, str):
            raise RuntimeError("invalid php runtime file descriptor")
        src = src_root / src_rel
        if not src.exists():
            raise RuntimeError("php runtime source missing: " + str(src))
        dst = dst_root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _emit_cpp(ir: dict[str, Any], _output_path: Path, emitter_options: dict[str, Any] | None = None) -> str:
    opts = export_layer_options_any(emitter_options, layer="emitter")
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


def _runtime_none(_output_path: Path) -> None:
    return


def _runtime_js_shims(output_path: Path) -> None:
    write_js_runtime_shims(output_path.parent)


def _emit_java(ir: dict[str, Any], output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
    class_name = output_path.stem if output_path.stem != "" else "Main"
    return transpile_to_java_native(ir, class_name=class_name)


def _make_unary_emit(emit_impl: Any) -> Any:
    def _emit(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
        out = emit_impl(ir)
        return out if isinstance(out, str) else ""

    return _emit


_STATIC_CALLABLES: dict[str, Any] = {
    "backends.rs.lower:lower_east3_to_rs_ir": lower_east3_to_rs_ir,
    "backends.rs.optimizer:optimize_rs_ir": optimize_rs_ir,
    "backends.rs.emitter.rs_emitter:transpile_to_rust": transpile_to_rust,
    "backends.cs.lower:lower_east3_to_cs_ir": lower_east3_to_cs_ir,
    "backends.cs.optimizer:optimize_cs_ir": optimize_cs_ir,
    "backends.cs.emitter.cs_emitter:transpile_to_csharp": transpile_to_csharp,
    "backends.js.lower:lower_east3_to_js_ir": lower_east3_to_js_ir,
    "backends.js.optimizer:optimize_js_ir": optimize_js_ir,
    "backends.js.emitter.js_emitter:transpile_to_js": transpile_to_js,
    "backends.ts.lower:lower_east3_to_ts_ir": lower_east3_to_ts_ir,
    "backends.ts.optimizer:optimize_ts_ir": optimize_ts_ir,
    "backends.ts.emitter.ts_emitter:transpile_to_typescript": transpile_to_typescript,
    "backends.go.lower:lower_east3_to_go_ir": lower_east3_to_go_ir,
    "backends.go.optimizer:optimize_go_ir": optimize_go_ir,
    "backends.go.emitter:transpile_to_go_native": transpile_to_go_native,
    "backends.java.lower:lower_east3_to_java_ir": lower_east3_to_java_ir,
    "backends.java.optimizer:optimize_java_ir": optimize_java_ir,
    "backends.java.emitter:transpile_to_java_native": transpile_to_java_native,
    "backends.kotlin.lower:lower_east3_to_kotlin_ir": lower_east3_to_kotlin_ir,
    "backends.kotlin.optimizer:optimize_kotlin_ir": optimize_kotlin_ir,
    "backends.kotlin.emitter:transpile_to_kotlin_native": transpile_to_kotlin_native,
    "backends.swift.lower:lower_east3_to_swift_ir": lower_east3_to_swift_ir,
    "backends.swift.optimizer:optimize_swift_ir": optimize_swift_ir,
    "backends.swift.emitter:transpile_to_swift_native": transpile_to_swift_native,
    "backends.ruby.lower:lower_east3_to_ruby_ir": lower_east3_to_ruby_ir,
    "backends.ruby.optimizer:optimize_ruby_ir": optimize_ruby_ir,
    "backends.ruby.emitter:transpile_to_ruby_native": transpile_to_ruby_native,
    "backends.lua.lower:lower_east3_to_lua_ir": lower_east3_to_lua_ir,
    "backends.lua.optimizer:optimize_lua_ir": optimize_lua_ir,
    "backends.lua.emitter:transpile_to_lua_native": transpile_to_lua_native,
    "backends.scala.lower:lower_east3_to_scala_ir": lower_east3_to_scala_ir,
    "backends.scala.optimizer:optimize_scala_ir": optimize_scala_ir,
    "backends.scala.emitter:transpile_to_scala_native": transpile_to_scala_native,
    "backends.php.lower:lower_east3_to_php_ir": lower_east3_to_php_ir,
    "backends.php.optimizer:optimize_php_ir": optimize_php_ir,
    "backends.php.emitter:transpile_to_php_native": transpile_to_php_native,
    "backends.nim.emitter:transpile_to_nim_native": transpile_to_nim_native,
    "backends.common.program_writer:write_single_file_program": write_single_file_program,
    "backends.cpp.program_writer:write_cpp_program": write_cpp_program,
    "backends.cpp.emitter:transpile_to_cpp": transpile_to_cpp,
}


def _resolve_callable_ref(symbol_ref: str) -> Any:
    fn = _STATIC_CALLABLES.get(symbol_ref)
    if fn is None:
        raise RuntimeError("unsupported backend symbol ref: " + symbol_ref)
    return fn


def _runtime_hook_from_key(runtime_key: str) -> Any:
    descriptor = get_runtime_hook_descriptor(runtime_key)
    kind = str(descriptor.get("kind", ""))
    files_any = descriptor.get("files", [])
    files = files_any if isinstance(files_any, list) else []
    if kind == "none":
        return _runtime_none
    if kind == "js_shims":
        return _runtime_js_shims
    if kind == "copy_files":
        return lambda output_path: _copy_runtime_files(files, output_path)
    if kind == "php_runtime":
        return lambda output_path: _copy_php_runtime_files(files, output_path)
    raise RuntimeError("unsupported runtime hook kind: " + runtime_key)


def _emit_from_target(target: str) -> Any:
    emit_kind = get_backend_emit_kind(target)
    emit_ref = get_backend_emit_ref(target)
    if emit_kind == "cpp":
        return _emit_cpp
    if emit_kind == "java":
        return _emit_java
    if emit_kind == "unary":
        return _make_unary_emit(_resolve_callable_ref(emit_ref))
    raise RuntimeError("unsupported emit kind: " + emit_kind)


def _build_backend_spec(target: str) -> BackendSpec:
    spec = build_backend_spec_metadata(target)
    lower_ref = get_backend_lower_ref(target)
    optimizer_ref = get_backend_optimizer_ref(target)
    spec["lower"] = _identity_ir if lower_ref == "" else _resolve_callable_ref(lower_ref)
    spec["optimizer"] = _identity_ir if optimizer_ref == "" else _resolve_callable_ref(optimizer_ref)
    spec["emit"] = _emit_from_target(target)
    spec["runtime_hook"] = _runtime_hook_from_key(get_backend_runtime_hook_key(target))
    program_writer_key = get_backend_program_writer_key(target)
    if program_writer_key != "":
        spec["program_writer"] = _resolve_callable_ref(get_program_writer_ref(program_writer_key))
    return spec


BackendSpec = dict[str, Any]


_BACKEND_SPECS: dict[str, BackendSpec] = {
    target: _build_backend_spec(target) for target in metadata_backend_targets()
}


_BACKEND_RUNTIME_SPECS: dict[str, ResolvedBackendSpec] = {}


def _normalize_backend_runtime_spec(spec: BackendSpec) -> ResolvedBackendSpec:
    return build_resolved_backend_spec(
        spec,
        identity_ir=_identity_ir,
        empty_emit=_empty_emit,
        runtime_none=_runtime_none,
        default_program_writer=write_single_file_program,
        suppress_emit_exceptions=False,
    )


def _normalize_backend_specs() -> None:
    for target, spec in list(_BACKEND_SPECS.items()):
        runtime_spec = _normalize_backend_runtime_spec(spec)
        _BACKEND_RUNTIME_SPECS[target] = runtime_spec
        _BACKEND_SPECS[target] = export_resolved_backend_spec_any(runtime_spec)


def _coerce_runtime_spec(spec: BackendSpec | ResolvedBackendSpec) -> ResolvedBackendSpec:
    return coerce_backend_spec(spec)


_normalize_backend_specs()


def list_backend_targets() -> list[str]:
    return metadata_backend_targets()


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
    return execute_lower_ir_with_spec(
        runtime_spec,
        east_doc,
        lower_options,
        suppress_exceptions=False,
    )


def lower_ir(spec: BackendSpec, east_doc: dict[str, Any], lower_options: dict[str, Any] | None = None) -> dict[str, Any]:
    return lower_ir_typed(spec, east_doc, lower_options)


def optimize_ir_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    ir: dict[str, Any],
    optimizer_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_spec = _coerce_runtime_spec(spec)
    return execute_optimize_ir_with_spec(
        runtime_spec,
        ir,
        optimizer_options,
        suppress_exceptions=False,
    )


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
    return execute_emit_module_with_spec(
        runtime_spec,
        ir,
        output_path,
        emitter_options,
        module_id=module_id,
        is_entry=is_entry,
        suppress_exceptions=False,
    )


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
    return build_program_artifact_from_modules(
        runtime_spec,
        modules,
        program_id=program_id,
        entry_modules=entry_modules,
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=writer_options,
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
    return collect_program_module_carriers(module_artifact)


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return export_program_module_artifacts(module_artifact)


def get_program_writer_typed(spec: BackendSpec | ResolvedBackendSpec) -> Any:
    runtime_spec = _coerce_runtime_spec(spec)
    return get_program_writer_with_spec(runtime_spec)


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
    runtime_spec = _coerce_runtime_spec(spec)
    return emit_source_text_with_spec(
        runtime_spec,
        ir,
        output_path,
        emitter_options,
        suppress_exceptions=False,
    )


def apply_runtime_hook_typed(spec: BackendSpec | ResolvedBackendSpec, output_path: Path) -> None:
    runtime_spec = _coerce_runtime_spec(spec)
    apply_runtime_hook_with_spec(runtime_spec, output_path)


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    apply_runtime_hook_typed(spec, output_path)

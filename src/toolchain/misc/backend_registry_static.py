"""Backend registry for unified ``py2x`` frontend."""

from __future__ import annotations

from typing import Any
from pytra.std.pathlib import Path
from toolchain.misc.backend_registry_diagnostics import unsupported_backend_symbol_ref_message
from toolchain.misc.backend_registry_diagnostics import unsupported_target_message
from toolchain.misc.backend_registry_metadata import list_backend_targets as metadata_backend_targets
from toolchain.misc.backend_registry_shared import build_cpp_emit
from toolchain.misc.backend_registry_shared import build_emit_from_target
from toolchain.misc.backend_registry_shared import build_java_emit
from toolchain.misc.backend_registry_shared import build_runtime_hook_from_key
from toolchain.misc.backend_registry_shared import build_program_artifact_with_backend_spec
from toolchain.misc.backend_registry_shared import collect_program_modules_from_artifact
from toolchain.misc.backend_registry_shared import default_output_path_from_backend_spec
from toolchain.misc.backend_registry_shared import emit_module_with_backend_spec
from toolchain.misc.backend_registry_shared import emit_source_with_backend_spec
from toolchain.misc.backend_registry_shared import export_layer_options_with_backend_spec
from toolchain.misc.backend_registry_shared import export_module_artifact_with_backend_spec
from toolchain.misc.backend_registry_shared import export_program_artifact_with_backend_spec
from toolchain.misc.backend_registry_shared import export_program_modules_from_artifact
from toolchain.misc.backend_registry_shared import get_program_writer_from_backend_spec
from toolchain.misc.backend_registry_shared import lower_ir_with_backend_spec
from toolchain.misc.backend_registry_shared import build_runtime_bound_backend_spec
from toolchain.misc.backend_registry_shared import normalize_runtime_backend_spec
from toolchain.misc.backend_registry_shared import optimize_ir_with_backend_spec
from toolchain.misc.backend_registry_shared import resolve_layer_options_with_backend_spec
from toolchain.misc.backend_registry_shared import build_unary_emit
from toolchain.misc.backend_registry_shared import empty_emit
from toolchain.misc.backend_registry_shared import identity_ir
from toolchain.misc.backend_registry_shared import apply_runtime_hook_from_backend_spec
from toolchain.misc.backend_registry_shared import registry_src_root
from toolchain.misc.backend_registry_shared import runtime_none
from toolchain.misc.typed_boundary import LayerOptionsCarrier
from toolchain.misc.typed_boundary import ModuleArtifactCarrier
from toolchain.misc.typed_boundary import ProgramArtifactCarrier
from toolchain.misc.typed_boundary import ResolvedBackendSpec
from toolchain.misc.typed_boundary import coerce_backend_spec
from toolchain.misc.typed_boundary import export_resolved_backend_spec_any

from toolchain.emit.cs.lower import lower_east3_to_cs_ir
from toolchain.emit.cs.optimizer import optimize_cs_ir
from toolchain.emit.cs.emitter.cs_emitter import transpile_to_csharp
from toolchain.emit.common.program_writer import write_single_file_program
from toolchain.emit.cpp.program_writer import write_cpp_program
# Go: migrated to toolchain2. Stubs for registry compatibility.
def lower_east3_to_go_ir(doc: object) -> object: return doc
def optimize_go_ir(doc: object) -> object: return doc
def transpile_to_go_native(doc: object) -> str: return ""
from toolchain.emit.java.lower import lower_east3_to_java_ir
from toolchain.emit.java.optimizer import optimize_java_ir
from toolchain.emit.java.emitter import transpile_to_java_native
from toolchain.emit.powershell.emitter.powershell_emitter import transpile_to_powershell
from toolchain.emit.js.lower import lower_east3_to_js_ir
from toolchain.emit.js.optimizer import optimize_js_ir
from toolchain.emit.js.emitter.js_emitter import transpile_to_js
from toolchain.emit.kotlin.lower import lower_east3_to_kotlin_ir
from toolchain.emit.kotlin.optimizer import optimize_kotlin_ir
from toolchain.emit.kotlin.emitter import transpile_to_kotlin_native
from toolchain.emit.lua.lower import lower_east3_to_lua_ir
from toolchain.emit.lua.optimizer import optimize_lua_ir
from toolchain.emit.lua.emitter import transpile_to_lua_native
from toolchain.emit.nim.emitter import transpile_to_nim_native
from toolchain.emit.php.lower import lower_east3_to_php_ir
from toolchain.emit.php.optimizer import optimize_php_ir
from toolchain.emit.php.emitter import transpile_to_php_native
from toolchain.emit.rs.lower import lower_east3_to_rs_ir
from toolchain.emit.rs.optimizer import optimize_rs_ir
from toolchain.emit.rs.emitter.rs_emitter import transpile_to_rust
from toolchain.emit.ruby.lower import lower_east3_to_ruby_ir
from toolchain.emit.ruby.optimizer import optimize_ruby_ir
from toolchain.emit.ruby.emitter import transpile_to_ruby_native
from toolchain.emit.scala.lower import lower_east3_to_scala_ir
from toolchain.emit.scala.optimizer import optimize_scala_ir
from toolchain.emit.scala.emitter import transpile_to_scala_native
from toolchain.emit.swift.lower import lower_east3_to_swift_ir
from toolchain.emit.swift.optimizer import optimize_swift_ir
from toolchain.emit.swift.emitter import transpile_to_swift_native
from toolchain.emit.ts.lower import lower_east3_to_ts_ir
from toolchain.emit.ts.optimizer import optimize_ts_ir
from toolchain.emit.ts.emitter.ts_emitter import transpile_to_typescript
from toolchain.emit.cpp.emitter import transpile_to_cpp
from toolchain.misc.js_runtime_shims import write_js_runtime_shims

_SRC_ROOT = registry_src_root(__file__)


def _runtime_js_shims(output_path: Path) -> None:
    write_js_runtime_shims(output_path.parent)


_STATIC_CALLABLES = {
    "toolchain.emit.rs.lower:lower_east3_to_rs_ir": lower_east3_to_rs_ir,
    "toolchain.emit.rs.optimizer:optimize_rs_ir": optimize_rs_ir,
    "toolchain.emit.rs.emitter.rs_emitter:transpile_to_rust": transpile_to_rust,
    "toolchain.emit.cs.lower:lower_east3_to_cs_ir": lower_east3_to_cs_ir,
    "toolchain.emit.cs.optimizer:optimize_cs_ir": optimize_cs_ir,
    "toolchain.emit.cs.emitter.cs_emitter:transpile_to_csharp": transpile_to_csharp,
    "toolchain.emit.js.lower:lower_east3_to_js_ir": lower_east3_to_js_ir,
    "toolchain.emit.js.optimizer:optimize_js_ir": optimize_js_ir,
    "toolchain.emit.js.emitter.js_emitter:transpile_to_js": transpile_to_js,
    "toolchain.emit.ts.lower:lower_east3_to_ts_ir": lower_east3_to_ts_ir,
    "toolchain.emit.ts.optimizer:optimize_ts_ir": optimize_ts_ir,
    "toolchain.emit.ts.emitter.ts_emitter:transpile_to_typescript": transpile_to_typescript,
    "toolchain.emit.go.lower:lower_east3_to_go_ir": lower_east3_to_go_ir,
    "toolchain.emit.go.optimizer:optimize_go_ir": optimize_go_ir,
    "toolchain.emit.go.emitter:transpile_to_go_native": transpile_to_go_native,
    "toolchain.emit.java.lower:lower_east3_to_java_ir": lower_east3_to_java_ir,
    "toolchain.emit.java.optimizer:optimize_java_ir": optimize_java_ir,
    "toolchain.emit.java.emitter:transpile_to_java_native": transpile_to_java_native,
    "toolchain.emit.kotlin.lower:lower_east3_to_kotlin_ir": lower_east3_to_kotlin_ir,
    "toolchain.emit.kotlin.optimizer:optimize_kotlin_ir": optimize_kotlin_ir,
    "toolchain.emit.kotlin.emitter:transpile_to_kotlin_native": transpile_to_kotlin_native,
    "toolchain.emit.swift.lower:lower_east3_to_swift_ir": lower_east3_to_swift_ir,
    "toolchain.emit.swift.optimizer:optimize_swift_ir": optimize_swift_ir,
    "toolchain.emit.swift.emitter:transpile_to_swift_native": transpile_to_swift_native,
    "toolchain.emit.ruby.lower:lower_east3_to_ruby_ir": lower_east3_to_ruby_ir,
    "toolchain.emit.ruby.optimizer:optimize_ruby_ir": optimize_ruby_ir,
    "toolchain.emit.ruby.emitter:transpile_to_ruby_native": transpile_to_ruby_native,
    "toolchain.emit.lua.lower:lower_east3_to_lua_ir": lower_east3_to_lua_ir,
    "toolchain.emit.lua.optimizer:optimize_lua_ir": optimize_lua_ir,
    "toolchain.emit.lua.emitter:transpile_to_lua_native": transpile_to_lua_native,
    "toolchain.emit.scala.lower:lower_east3_to_scala_ir": lower_east3_to_scala_ir,
    "toolchain.emit.scala.optimizer:optimize_scala_ir": optimize_scala_ir,
    "toolchain.emit.scala.emitter:transpile_to_scala_native": transpile_to_scala_native,
    "toolchain.emit.php.lower:lower_east3_to_php_ir": lower_east3_to_php_ir,
    "toolchain.emit.php.optimizer:optimize_php_ir": optimize_php_ir,
    "toolchain.emit.php.emitter:transpile_to_php_native": transpile_to_php_native,
    "toolchain.emit.nim.emitter:transpile_to_nim_native": transpile_to_nim_native,
    "toolchain.emit.powershell.emitter.powershell_emitter:transpile_to_powershell": transpile_to_powershell,
    "toolchain.emit.common.program_writer:write_single_file_program": write_single_file_program,
    "toolchain.emit.cpp.program_writer:write_cpp_program": write_cpp_program,
    "toolchain.emit.cpp.emitter:transpile_to_cpp": transpile_to_cpp,
}


def _resolve_callable_ref(symbol_ref: str) -> Any:
    fn = _STATIC_CALLABLES.get(symbol_ref)
    if fn is None:
        raise RuntimeError(unsupported_backend_symbol_ref_message(symbol_ref))
    return fn


def _runtime_hook_from_key(runtime_key: str) -> Any:
    return build_runtime_hook_from_key(
        runtime_key,
        src_root=_SRC_ROOT,
        none_hook=runtime_none,
        js_shims_hook=_runtime_js_shims,
    )


def _emit_from_target(target: str) -> Any:
    return build_emit_from_target(
        target,
        resolve_callable_ref=_resolve_callable_ref,
        cpp_emit_factory=build_cpp_emit,
        java_emit_factory=build_java_emit,
        unary_emit_factory=build_unary_emit,
    )


def _build_backend_spec(target: str) -> BackendSpec:
    return build_runtime_bound_backend_spec(
        target,
        resolve_callable_ref=_resolve_callable_ref,
        emit_from_target=_emit_from_target,
        runtime_hook_from_key=_runtime_hook_from_key,
        identity_ir_impl=identity_ir,
    )


BackendSpec = dict[str, Any]


_BACKEND_SPECS: dict[str, BackendSpec] = {
    target: _build_backend_spec(target) for target in metadata_backend_targets()
}


_BACKEND_RUNTIME_SPECS: dict[str, ResolvedBackendSpec] = {}


def _normalize_backend_runtime_spec(spec: BackendSpec) -> ResolvedBackendSpec:
    return normalize_runtime_backend_spec(
        spec,
        default_program_writer=write_single_file_program,
        suppress_emit_exceptions=False,
        identity_ir_impl=identity_ir,
        empty_emit_impl=empty_emit,
        runtime_none_hook=runtime_none,
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
        raise RuntimeError(unsupported_target_message(target))
    return _BACKEND_RUNTIME_SPECS[target]


def get_backend_spec(target: str) -> BackendSpec:
    if target not in _BACKEND_SPECS:
        raise RuntimeError(unsupported_target_message(target))
    return _BACKEND_SPECS[target]


def default_output_path(input_path: Path, target: str) -> Path:
    return default_output_path_from_backend_spec(input_path, target, get_backend_spec_typed=get_backend_spec_typed)


def resolve_layer_options_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    layer: str,
    raw_options: dict[str, str],
) -> LayerOptionsCarrier:
    return resolve_layer_options_with_backend_spec(
        spec,
        layer,
        raw_options,
        coerce_runtime_spec=_coerce_runtime_spec,
    )


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict[str, str]) -> dict[str, Any]:
    return export_layer_options_with_backend_spec(
        spec,
        layer,
        raw_options,
        coerce_runtime_spec=_coerce_runtime_spec,
    )


def lower_ir_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    east_doc: dict[str, Any] | object,
    lower_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> dict[str, Any]:
    return lower_ir_with_backend_spec(
        spec,
        east_doc,
        lower_options,
        coerce_runtime_spec=_coerce_runtime_spec,
        suppress_exceptions=False,
    )


def lower_ir(spec: BackendSpec, east_doc: dict[str, Any], lower_options: dict[str, Any] | None = None) -> dict[str, Any]:
    return lower_ir_typed(spec, east_doc, lower_options)


def optimize_ir_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    ir: dict[str, Any],
    optimizer_options: LayerOptionsCarrier | dict[str, Any] | None = None,
) -> dict[str, Any]:
    return optimize_ir_with_backend_spec(
        spec,
        ir,
        optimizer_options,
        coerce_runtime_spec=_coerce_runtime_spec,
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
    return emit_module_with_backend_spec(
        spec,
        ir,
        output_path,
        emitter_options,
        module_id=module_id,
        is_entry=is_entry,
        coerce_runtime_spec=_coerce_runtime_spec,
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
    return export_module_artifact_with_backend_spec(
        spec,
        ir,
        output_path,
        emitter_options,
        module_id=module_id,
        is_entry=is_entry,
        coerce_runtime_spec=_coerce_runtime_spec,
        suppress_exceptions=False,
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
    return build_program_artifact_with_backend_spec(
        spec,
        modules,
        program_id=program_id,
        entry_modules=entry_modules,
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=writer_options,
        coerce_runtime_spec=_coerce_runtime_spec,
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
    return export_program_artifact_with_backend_spec(
        spec,
        modules,
        program_id=program_id,
        entry_modules=entry_modules,
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=writer_options,
        coerce_runtime_spec=_coerce_runtime_spec,
    )


def collect_program_modules_typed(module_artifact: ModuleArtifactCarrier | dict[str, Any]) -> tuple[ModuleArtifactCarrier, ...]:
    return collect_program_modules_from_artifact(module_artifact)


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return export_program_modules_from_artifact(module_artifact)


def get_program_writer_typed(spec: BackendSpec | ResolvedBackendSpec) -> Any:
    return get_program_writer_from_backend_spec(spec, coerce_runtime_spec=_coerce_runtime_spec)


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
    return emit_source_with_backend_spec(
        spec,
        ir,
        output_path,
        emitter_options,
        coerce_runtime_spec=_coerce_runtime_spec,
        suppress_exceptions=False,
    )


def apply_runtime_hook_typed(spec: BackendSpec | ResolvedBackendSpec, output_path: Path) -> None:
    apply_runtime_hook_from_backend_spec(spec, output_path, coerce_runtime_spec=_coerce_runtime_spec)


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    apply_runtime_hook_typed(spec, output_path)

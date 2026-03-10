"""Host-side backend registry for unified ``py2x`` frontend.

This module keeps target backend imports lazy so regular host execution only loads
modules for the selected target.
"""

from __future__ import annotations

import importlib

from typing import Any
from pytra.std.pathlib import Path
from toolchain.compiler.backend_registry_metadata import get_program_writer_ref
from toolchain.compiler.backend_registry_metadata import get_runtime_hook_descriptor
from toolchain.compiler.backend_registry_metadata import list_backend_targets as metadata_backend_targets
from toolchain.compiler.backend_registry_shared import build_cpp_emit
from toolchain.compiler.backend_registry_shared import build_emit_from_target
from toolchain.compiler.backend_registry_shared import build_java_emit
from toolchain.compiler.backend_registry_shared import copy_php_runtime_files
from toolchain.compiler.backend_registry_shared import copy_runtime_files
from toolchain.compiler.backend_registry_shared import default_output_path_for
from toolchain.compiler.backend_registry_shared import build_runtime_bound_backend_spec
from toolchain.compiler.backend_registry_shared import normalize_runtime_backend_spec
from toolchain.compiler.backend_registry_shared import build_runtime_hook_from_descriptor
from toolchain.compiler.backend_registry_shared import build_unary_emit
from toolchain.compiler.backend_registry_shared import empty_emit
from toolchain.compiler.backend_registry_shared import identity_ir
from toolchain.compiler.backend_registry_shared import registry_src_root
from toolchain.compiler.backend_registry_shared import runtime_none
from toolchain.compiler.typed_boundary import LayerOptionsCarrier
from toolchain.compiler.typed_boundary import ModuleArtifactCarrier
from toolchain.compiler.typed_boundary import ProgramArtifactCarrier
from toolchain.compiler.typed_boundary import ResolvedBackendSpec
from toolchain.compiler.typed_boundary import build_program_artifact_from_modules
from toolchain.compiler.typed_boundary import coerce_backend_spec
from toolchain.compiler.typed_boundary import collect_program_module_carriers
from toolchain.compiler.typed_boundary import copy_module_dependencies
from toolchain.compiler.typed_boundary import copy_module_metadata
from toolchain.compiler.typed_boundary import emit_source_text_with_spec
from toolchain.compiler.typed_boundary import execute_emit_module_with_spec
from toolchain.compiler.typed_boundary import execute_lower_ir_with_spec
from toolchain.compiler.typed_boundary import execute_optimize_ir_with_spec
from toolchain.compiler.typed_boundary import export_resolved_backend_spec_any
from toolchain.compiler.typed_boundary import export_module_artifact_any
from toolchain.compiler.typed_boundary import export_program_module_artifacts
from toolchain.compiler.typed_boundary import export_program_artifact_any
from toolchain.compiler.typed_boundary import get_program_writer_with_spec
from toolchain.compiler.typed_boundary import resolve_layer_options_carrier
from toolchain.compiler.typed_boundary import apply_runtime_hook_with_spec


BackendSpec = dict
_SRC_ROOT = registry_src_root(__file__)


def _module_symbol(mod: Any, symbol_name: str) -> Any:
    if isinstance(mod, dict):
        if symbol_name in mod:
            return mod[symbol_name]
        return None
    try:
        mod_dict = vars(mod)
    except Exception:
        return None
    if isinstance(mod_dict, dict) and symbol_name in mod_dict:
        return mod_dict[symbol_name]
    return None


def _runtime_js_shims(output_path: Path) -> None:
    mod = importlib.import_module("toolchain.compiler.js_runtime_shims")
    writer = _module_symbol(mod, "write_js_runtime_shims")
    if writer is None:
        raise RuntimeError("write_js_runtime_shims not found")
    writer(output_path.parent)


def _load_callable(module_name: str, symbol_name: str) -> Any:
    mod = importlib.import_module(module_name)
    fn = _module_symbol(mod, symbol_name)
    if fn is None:
        raise RuntimeError("missing symbol: " + module_name + "." + symbol_name)
    return fn


def _split_symbol_ref(symbol_ref: str) -> tuple[str, str]:
    parts = symbol_ref.split(":", 1)
    if len(parts) != 2 or parts[0] == "" or parts[1] == "":
        raise RuntimeError("unsupported backend symbol ref: " + symbol_ref)
    return parts[0], parts[1]


def _load_callable_ref(symbol_ref: str) -> Any:
    module_name, symbol_name = _split_symbol_ref(symbol_ref)
    try:
        return _load_callable(module_name, symbol_name)
    except Exception as exc:
        raise RuntimeError("unsupported backend symbol ref: " + symbol_ref) from exc


def _runtime_hook_from_key(runtime_key: str) -> Any:
    return build_runtime_hook_from_descriptor(
        runtime_key,
        get_runtime_hook_descriptor(runtime_key),
        none_hook=runtime_none,
        js_shims_hook=_runtime_js_shims,
        copy_files_factory=lambda files: lambda output_path: copy_runtime_files(_SRC_ROOT, files, output_path),
        php_runtime_factory=lambda files: lambda output_path: copy_php_runtime_files(_SRC_ROOT, files, output_path),
    )


def _emit_from_target(target: str) -> Any:
    return build_emit_from_target(
        target,
        resolve_callable_ref=_load_callable_ref,
        cpp_emit_factory=build_cpp_emit,
        java_emit_factory=build_java_emit,
        unary_emit_factory=build_unary_emit,
    )


def _load_backend_spec(target: str) -> BackendSpec:
    return build_runtime_bound_backend_spec(
        target,
        resolve_callable_ref=_load_callable_ref,
        emit_from_target=_emit_from_target,
        runtime_hook_from_key=_runtime_hook_from_key,
        identity_ir_impl=identity_ir,
    )


_SPEC_CACHE: dict[str, ResolvedBackendSpec] = {}


def _normalize_backend_runtime_spec(spec: BackendSpec) -> ResolvedBackendSpec:
    return normalize_runtime_backend_spec(
        spec,
        default_program_writer=_load_callable_ref(get_program_writer_ref("single_file")),
        suppress_emit_exceptions=True,
        identity_ir_impl=identity_ir,
        empty_emit_impl=empty_emit,
        runtime_none_hook=runtime_none,
    )


def _normalize_backend_spec(spec: BackendSpec) -> BackendSpec:
    return export_resolved_backend_spec_any(_normalize_backend_runtime_spec(spec))


def _coerce_runtime_spec(spec: BackendSpec | ResolvedBackendSpec) -> ResolvedBackendSpec:
    return coerce_backend_spec(spec)


def list_backend_targets() -> list:
    return metadata_backend_targets()


def get_backend_spec_typed(target: str) -> ResolvedBackendSpec:
    cached = _SPEC_CACHE.get(target)
    if isinstance(cached, ResolvedBackendSpec):
        return cached
    spec_any = _load_backend_spec(target)
    if not isinstance(spec_any, dict):
        raise RuntimeError("invalid backend spec for target: " + target)
    spec = _normalize_backend_runtime_spec(spec_any)
    _SPEC_CACHE[target] = spec
    return spec


def get_backend_spec(target: str) -> BackendSpec:
    return export_resolved_backend_spec_any(get_backend_spec_typed(target))


def default_output_path(input_path: Path, target: str) -> Path:
    spec = get_backend_spec_typed(target)
    return default_output_path_for(input_path, spec.carrier.extension)


def resolve_layer_options_typed(
    spec: BackendSpec | ResolvedBackendSpec,
    layer: str,
    raw_options: dict[str, str],
) -> LayerOptionsCarrier:
    runtime_spec = _coerce_runtime_spec(spec)
    return resolve_layer_options_carrier(runtime_spec, layer, raw_options)


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict) -> dict:
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
        suppress_exceptions=True,
    )


def lower_ir(spec: BackendSpec, east_doc: dict, lower_options: Any = None) -> dict:
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
        suppress_exceptions=True,
    )


def optimize_ir(spec: BackendSpec, ir: dict, optimizer_options: Any = None) -> dict:
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
        suppress_exceptions=True,
    )


def emit_module(
    spec: BackendSpec,
    ir: dict,
    output_path: Path,
    emitter_options: Any = None,
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


def collect_program_modules_typed(module_artifact: ModuleArtifactCarrier | dict[str, Any]) -> tuple[ModuleArtifactCarrier, ...]:
    return collect_program_module_carriers(module_artifact)


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return export_program_module_artifacts(module_artifact)


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


def get_program_writer_typed(spec: BackendSpec | ResolvedBackendSpec) -> Any:
    runtime_spec = _coerce_runtime_spec(spec)
    return get_program_writer_with_spec(runtime_spec)


def get_program_writer(spec: BackendSpec) -> Any:
    return get_program_writer_typed(spec)


def emit_source(
    spec: BackendSpec,
    ir: dict,
    output_path: Path,
    emitter_options: Any = None,
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
        suppress_exceptions=True,
    )


def apply_runtime_hook_typed(spec: BackendSpec | ResolvedBackendSpec, output_path: Path) -> None:
    runtime_spec = _coerce_runtime_spec(spec)
    apply_runtime_hook_with_spec(runtime_spec, output_path)


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    apply_runtime_hook_typed(spec, output_path)

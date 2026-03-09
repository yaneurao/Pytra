"""Typed compiler-boundary carrier models and legacy adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pytra.std.pathlib import Path


CompilerOptionScalar = str | int | bool


def _copy_object_dict(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, object] = {}
    for key, value in raw.items():
        if isinstance(key, str):
            out[key] = value
    return out


def _copy_string_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item != "":
            out.append(item)
    return tuple(out)


def _copy_scalar_dict(raw: object) -> dict[str, CompilerOptionScalar]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, CompilerOptionScalar] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, bool):
            out[key] = bool(value)
        elif isinstance(value, int):
            out[key] = int(value)
        elif isinstance(value, str):
            out[key] = value
    return out


def _copy_scalar_layers(raw: object) -> dict[str, dict[str, CompilerOptionScalar]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, CompilerOptionScalar]] = {}
    for layer, values in raw.items():
        if isinstance(layer, str):
            out[layer] = _copy_scalar_dict(values)
    return out


def _copy_schema_layers(raw: object) -> dict[str, dict[str, dict[str, object]]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, dict[str, object]]] = {}
    for layer, values in raw.items():
        if not isinstance(layer, str) or not isinstance(values, dict):
            continue
        layer_out: dict[str, dict[str, object]] = {}
        for key, rule in values.items():
            if isinstance(key, str):
                layer_out[key] = _copy_object_dict(rule)
        out[layer] = layer_out
    return out


def _callable_key(fn: object) -> str:
    if fn is None:
        return ""
    module = getattr(fn, "__module__", "")
    qualname = getattr(fn, "__qualname__", "")
    if isinstance(module, str) and isinstance(qualname, str) and module != "" and qualname != "":
        return module + "." + qualname
    name = getattr(fn, "__name__", "")
    return name if isinstance(name, str) else ""


def _legacy_dict_adapter(value: object) -> dict[str, object] | None:
    to_legacy = getattr(value, "to_legacy_dict", None)
    if not callable(to_legacy):
        return None
    legacy = to_legacy()
    if isinstance(legacy, dict):
        return legacy
    return None


def _meta_dispatch_mode(raw_doc: dict[str, object]) -> str:
    meta_any = raw_doc.get("meta", {})
    if not isinstance(meta_any, dict):
        return ""
    dispatch_any = meta_any.get("dispatch_mode")
    return dispatch_any if isinstance(dispatch_any, str) else ""


def _meta_string(raw_doc: dict[str, object], key: str) -> str:
    meta_any = raw_doc.get("meta", {})
    if not isinstance(meta_any, dict):
        return ""
    value_any = meta_any.get(key)
    return value_any if isinstance(value_any, str) else ""


def _root_string(raw_doc: dict[str, object], key: str) -> str:
    value_any = raw_doc.get(key)
    return value_any if isinstance(value_any, str) else ""


def export_compiler_root_document(doc: "CompilerRootDocument") -> dict[str, object]:
    out = dict(doc.raw_module_doc)
    out["kind"] = doc.module_kind
    if doc.meta.source_path != "":
        out["source_path"] = doc.meta.source_path
    out["east_stage"] = doc.meta.east_stage
    out["schema_version"] = doc.meta.schema_version
    meta_any = out.get("meta", {})
    meta = dict(meta_any) if isinstance(meta_any, dict) else {}
    meta["dispatch_mode"] = doc.meta.dispatch_mode
    if doc.meta.parser_backend != "":
        meta["parser_backend"] = doc.meta.parser_backend
    out["meta"] = meta
    return out


def export_compiler_root_document_any(doc: object) -> dict[str, object]:
    return export_compiler_root_document(coerce_compiler_root_document(doc))


def export_layer_options_carrier(options: "LayerOptionsCarrier") -> dict[str, CompilerOptionScalar]:
    return dict(options.values)


def export_layer_options_any(
    options: object,
    *,
    layer: str = "",
) -> dict[str, CompilerOptionScalar]:
    return export_layer_options_carrier(coerce_layer_options(layer, options))


def export_backend_spec_carrier(carrier: "BackendSpecCarrier") -> dict[str, object]:
    return {
        "target_lang": carrier.target_lang,
        "extension": carrier.extension,
        "default_options": {
            layer: dict(values) for layer, values in carrier.default_options_by_layer.items()
        },
        "option_schema": {
            layer: {key: dict(rule) for key, rule in values.items()}
            for layer, values in carrier.option_schema_by_layer.items()
        },
    }


def export_resolved_backend_spec(spec: "ResolvedBackendSpec") -> dict[str, object]:
    out = export_backend_spec_carrier(spec.carrier)
    out["lower"] = spec.lower_impl
    out["optimizer"] = spec.optimizer_impl
    out["emit"] = spec.emit_impl
    out["emit_module"] = spec.emit_module_impl
    out["program_writer"] = spec.program_writer_impl
    out["runtime_hook"] = spec.runtime_hook_impl
    return out


def export_resolved_backend_spec_any(spec: object) -> dict[str, object]:
    return export_resolved_backend_spec(coerce_backend_spec(spec))


def backend_spec_target(spec: object) -> str:
    return coerce_backend_spec(spec).carrier.target_lang


def compiler_root_module_id(
    doc: object,
    *,
    fallback_output_path: Path | None = None,
) -> str:
    root = coerce_compiler_root_document(doc)
    meta_any = root.raw_module_doc.get("meta", {})
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str) and module_id_any.strip() != "":
            return module_id_any.strip()
    if fallback_output_path is not None and fallback_output_path.stem != "":
        return fallback_output_path.stem
    return "module"


def export_module_artifact_carrier(module: "ModuleArtifactCarrier") -> dict[str, object]:
    out: dict[str, object] = {
        "module_id": module.module_id,
        "kind": module.kind,
        "label": module.label,
        "extension": module.extension,
        "text": module.text,
        "is_entry": module.is_entry,
        "dependencies": list(module.dependencies),
        "metadata": dict(module.metadata),
    }
    if len(module.helper_modules) > 0:
        out["helper_modules"] = [export_module_artifact_carrier(item) for item in module.helper_modules]
    return out


def export_module_artifact_any(module_artifact: object) -> dict[str, object]:
    return export_module_artifact_carrier(coerce_module_artifact(module_artifact))


def module_artifact_text(module_artifact: object) -> str:
    return coerce_module_artifact(module_artifact).text


def export_program_artifact_carrier(program: "ProgramArtifactCarrier") -> dict[str, object]:
    return {
        "target": program.target,
        "program_id": program.program_id,
        "entry_modules": list(program.entry_modules),
        "modules": [export_module_artifact_carrier(module) for module in program.modules],
        "layout_mode": program.layout_mode,
        "link_output_schema": program.link_output_schema,
        "writer_options": dict(program.writer_options),
    }


def export_program_artifact_any(
    program_artifact: object,
    *,
    fallback_target: str = "",
    fallback_program_id: str = "",
    fallback_entry_modules: list[str] | tuple[str, ...] | None = None,
    fallback_layout_mode: str = "single_file",
    fallback_link_output_schema: str = "",
    fallback_writer_options: dict[str, object] | None = None,
) -> dict[str, object]:
    return export_program_artifact_carrier(
        coerce_program_artifact(
            program_artifact,
            fallback_target=fallback_target,
            fallback_program_id=fallback_program_id,
            fallback_entry_modules=fallback_entry_modules,
            fallback_layout_mode=fallback_layout_mode,
            fallback_link_output_schema=fallback_link_output_schema,
            fallback_writer_options=fallback_writer_options,
        )
    )


@dataclass(frozen=True)
class CompilerRootMeta:
    source_path: str
    east_stage: int
    schema_version: int
    dispatch_mode: str
    parser_backend: str

    @staticmethod
    def from_legacy_doc(
        raw_doc: dict[str, object],
        *,
        source_path: str = "",
        parser_backend: str = "",
    ) -> "CompilerRootMeta":
        stage_any = raw_doc.get("east_stage")
        schema_any = raw_doc.get("schema_version")
        return CompilerRootMeta(
            source_path=source_path if source_path != "" else _root_string(raw_doc, "source_path"),
            east_stage=int(stage_any) if isinstance(stage_any, int) else 0,
            schema_version=int(schema_any) if isinstance(schema_any, int) else 0,
            dispatch_mode=_meta_dispatch_mode(raw_doc),
            parser_backend=parser_backend if parser_backend != "" else _meta_string(raw_doc, "parser_backend"),
        )


@dataclass(frozen=True)
class CompilerRootDocument:
    meta: CompilerRootMeta
    module_kind: str
    raw_module_doc: dict[str, object]

    @staticmethod
    def from_legacy_doc(
        raw_doc: dict[str, object],
        *,
        source_path: str = "",
        parser_backend: str = "",
    ) -> "CompilerRootDocument":
        module_kind = raw_doc.get("kind")
        return CompilerRootDocument(
            meta=CompilerRootMeta.from_legacy_doc(
                raw_doc,
                source_path=source_path,
                parser_backend=parser_backend,
            ),
            module_kind=module_kind if isinstance(module_kind, str) else "",
            raw_module_doc=_copy_object_dict(raw_doc),
        )

    def to_legacy_dict(self) -> dict[str, object]:
        return export_compiler_root_document(self)


@dataclass(frozen=True)
class LayerOptionsCarrier:
    layer: str
    values: dict[str, CompilerOptionScalar]

    def to_legacy_dict(self) -> dict[str, CompilerOptionScalar]:
        return export_layer_options_carrier(self)


@dataclass(frozen=True)
class BackendSpecCarrier:
    target_lang: str
    extension: str
    default_options_by_layer: dict[str, dict[str, CompilerOptionScalar]]
    option_schema_by_layer: dict[str, dict[str, dict[str, object]]]
    emit_strategy: str
    lower_strategy: str
    optimizer_strategy: str
    runtime_hook_key: str
    program_writer_key: str

    @staticmethod
    def from_legacy_spec(raw_spec: dict[str, object]) -> "BackendSpecCarrier":
        target = raw_spec.get("target_lang")
        target_lang = target if isinstance(target, str) else ""
        return BackendSpecCarrier(
            target_lang=target_lang,
            extension=raw_spec.get("extension") if isinstance(raw_spec.get("extension"), str) else "",
            default_options_by_layer=_copy_scalar_layers(raw_spec.get("default_options", {})),
            option_schema_by_layer=_copy_schema_layers(raw_spec.get("option_schema", {})),
            emit_strategy=str(raw_spec.get("emit_strategy", _callable_key(raw_spec.get("emit_module")))),
            lower_strategy=str(raw_spec.get("lower_strategy", _callable_key(raw_spec.get("lower")))),
            optimizer_strategy=str(raw_spec.get("optimizer_strategy", _callable_key(raw_spec.get("optimizer")))),
            runtime_hook_key=str(raw_spec.get("runtime_hook_key", _callable_key(raw_spec.get("runtime_hook")))),
            program_writer_key=str(raw_spec.get("program_writer_key", _callable_key(raw_spec.get("program_writer")))),
        )

    def to_legacy_dict(self) -> dict[str, object]:
        return export_backend_spec_carrier(self)


@dataclass(frozen=True)
class ModuleArtifactCarrier:
    module_id: str
    kind: str
    label: str
    extension: str
    text: str
    is_entry: bool
    dependencies: tuple[str, ...]
    metadata: dict[str, object]
    helper_modules: tuple["ModuleArtifactCarrier", ...] = ()

    def to_legacy_dict(self) -> dict[str, object]:
        return export_module_artifact_carrier(self)


@dataclass(frozen=True)
class ProgramArtifactCarrier:
    target: str
    program_id: str
    entry_modules: tuple[str, ...]
    modules: tuple[ModuleArtifactCarrier, ...]
    layout_mode: str
    link_output_schema: str
    writer_options: dict[str, object]

    def to_legacy_dict(self) -> dict[str, object]:
        return export_program_artifact_carrier(self)


@dataclass(frozen=True)
class EmitRequestCarrier:
    spec: BackendSpecCarrier
    ir_document: dict[str, object]
    output_path: Path
    emitter_options: LayerOptionsCarrier
    module_id: str
    is_entry: bool


@dataclass(frozen=True)
class ResolvedBackendSpec:
    carrier: BackendSpecCarrier
    lower_impl: Any
    optimizer_impl: Any
    emit_impl: Any
    emit_module_impl: Any
    program_writer_impl: Any
    runtime_hook_impl: Any

    @staticmethod
    def from_legacy_spec(raw_spec: dict[str, object]) -> "ResolvedBackendSpec":
        emit_module_impl = raw_spec.get("emit_module")
        emit_impl = raw_spec.get("emit")
        return ResolvedBackendSpec(
            carrier=BackendSpecCarrier.from_legacy_spec(raw_spec),
            lower_impl=raw_spec.get("lower"),
            optimizer_impl=raw_spec.get("optimizer"),
            emit_impl=emit_impl,
            emit_module_impl=emit_module_impl,
            program_writer_impl=raw_spec.get("program_writer"),
            runtime_hook_impl=raw_spec.get("runtime_hook"),
        )

    def to_legacy_dict(self) -> dict[str, object]:
        return export_resolved_backend_spec(self)


def coerce_compiler_root_document(
    raw_doc: object,
    *,
    source_path: str = "",
    parser_backend: str = "",
) -> CompilerRootDocument:
    if isinstance(raw_doc, CompilerRootDocument):
        return raw_doc
    legacy_doc = _legacy_dict_adapter(raw_doc)
    if legacy_doc is not None:
        raw_doc = legacy_doc
    if not isinstance(raw_doc, dict):
        raise RuntimeError("compiler root document must be dict")
    return CompilerRootDocument.from_legacy_doc(
        raw_doc,
        source_path=source_path,
        parser_backend=parser_backend,
    )


def coerce_layer_options(
    layer: str,
    raw_options: object,
) -> LayerOptionsCarrier:
    if isinstance(raw_options, LayerOptionsCarrier):
        return raw_options
    legacy_options = _legacy_dict_adapter(raw_options)
    if legacy_options is not None:
        raw_options = legacy_options
    return LayerOptionsCarrier(layer=layer, values=_copy_scalar_dict(raw_options))


def coerce_backend_spec(raw_spec: object) -> ResolvedBackendSpec:
    if isinstance(raw_spec, ResolvedBackendSpec):
        return raw_spec
    legacy_spec = _legacy_dict_adapter(raw_spec)
    if legacy_spec is not None:
        raw_spec = legacy_spec
    if isinstance(raw_spec, dict):
        return ResolvedBackendSpec.from_legacy_spec(raw_spec)
    raise RuntimeError("backend spec must be dict or ResolvedBackendSpec")


def normalize_legacy_backend_spec_dict(raw_spec: object) -> dict[str, object]:
    normalized = _copy_object_dict(raw_spec)
    default_layers = _copy_scalar_layers(normalized.get("default_options", {}))
    normalized["default_options"] = {
        "lower": dict(default_layers.get("lower", {})),
        "optimizer": dict(default_layers.get("optimizer", {})),
        "emitter": dict(default_layers.get("emitter", {})),
    }
    schema_layers = _copy_schema_layers(normalized.get("option_schema", {}))
    normalized["option_schema"] = {
        "lower": {key: dict(rule) for key, rule in schema_layers.get("lower", {}).items()},
        "optimizer": {key: dict(rule) for key, rule in schema_layers.get("optimizer", {}).items()},
        "emitter": {key: dict(rule) for key, rule in schema_layers.get("emitter", {}).items()},
    }
    return normalized


def build_resolved_backend_spec(
    raw_spec: object,
    *,
    identity_ir: Any,
    empty_emit: Any,
    runtime_none: Any,
    default_program_writer: Any,
    suppress_emit_exceptions: bool,
) -> "ResolvedBackendSpec":
    normalized = normalize_legacy_backend_spec_dict(raw_spec)
    extension = str(normalized.get("extension", ""))

    lower_impl = normalized.get("lower")
    if not callable(lower_impl):
        lower_impl = identity_ir
    optimizer_impl = normalized.get("optimizer")
    if not callable(optimizer_impl):
        optimizer_impl = identity_ir
    emit_impl = normalized.get("emit")
    if not callable(emit_impl):
        emit_impl = empty_emit
    emit_module_impl = normalized.get("emit_module")
    if not callable(emit_module_impl):
        emit_module_impl = build_legacy_emit_module_adapter(
            emit_impl,
            extension=extension,
            suppress_emit_exceptions=suppress_emit_exceptions,
        )
    program_writer_impl = normalized.get("program_writer")
    if not callable(program_writer_impl) and not isinstance(program_writer_impl, dict):
        program_writer_impl = default_program_writer
    runtime_hook_impl = normalized.get("runtime_hook")
    if runtime_hook_impl is None:
        runtime_hook_impl = runtime_none

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


def coerce_ir_document(raw: object) -> dict[str, object]:
    return _copy_object_dict(raw)


def copy_program_writer_options(raw: object) -> dict[str, object]:
    return _copy_object_dict(raw)


def copy_module_dependencies(raw: object) -> tuple[str, ...]:
    return _copy_string_tuple(raw)


def copy_module_metadata(raw: object) -> dict[str, object]:
    return _copy_object_dict(raw)


def resolve_layer_options_carrier(
    spec: ResolvedBackendSpec,
    layer: str,
    raw_options: dict[str, str],
) -> LayerOptionsCarrier:
    merged = dict(spec.carrier.default_options_by_layer.get(layer, {}))
    schema = spec.carrier.option_schema_by_layer.get(layer, {})
    for key, raw in raw_options.items():
        if key not in schema:
            raise RuntimeError("unknown " + layer + " option: " + key)
        rule = schema[key]
        typ = str(rule.get("type", "str"))
        value_any: CompilerOptionScalar = raw
        if typ == "str":
            value_any = raw
        elif typ == "int":
            try:
                value_any = int(raw)
            except Exception as ex:
                raise RuntimeError("invalid int for option " + key + ": " + raw) from ex
        elif typ == "bool":
            lowered = raw.lower()
            if lowered in {"1", "true", "yes", "on"}:
                value_any = True
            elif lowered in {"0", "false", "no", "off"}:
                value_any = False
            else:
                raise RuntimeError("invalid bool for option " + key + ": " + raw)
        else:
            raise RuntimeError("unsupported option type for " + key + ": " + typ)
        choices = rule.get("choices", [])
        if isinstance(choices, list) and len(choices) > 0 and value_any not in choices:
            raise RuntimeError("invalid value for option " + key + ": " + str(value_any))
        merged[key] = value_any
    return LayerOptionsCarrier(layer=layer, values=merged)


def _execute_ir_transform(
    fn: Any,
    payload: dict[str, object],
    *,
    options: LayerOptionsCarrier,
    fallback_payload: dict[str, object],
    suppress_exceptions: bool,
) -> dict[str, object]:
    try:
        out = fn(payload, export_layer_options_carrier(options))
    except TypeError:
        try:
            out = fn(payload)
        except Exception:
            if not suppress_exceptions:
                raise
            out = fallback_payload
    except Exception:
        if not suppress_exceptions:
            raise
        out = fallback_payload
    return coerce_ir_document(out)


def execute_lower_ir_with_spec(
    runtime_spec: ResolvedBackendSpec,
    east_doc: object,
    lower_options: LayerOptionsCarrier | dict[str, Any] | None = None,
    *,
    suppress_exceptions: bool,
) -> dict[str, object]:
    doc = export_compiler_root_document_any(east_doc)
    options = lower_options if isinstance(lower_options, LayerOptionsCarrier) else coerce_layer_options("lower", lower_options)
    return _execute_ir_transform(
        runtime_spec.lower_impl,
        doc,
        options=options,
        fallback_payload=doc,
        suppress_exceptions=suppress_exceptions,
    )


def execute_optimize_ir_with_spec(
    runtime_spec: ResolvedBackendSpec,
    ir: dict[str, Any],
    optimizer_options: LayerOptionsCarrier | dict[str, Any] | None = None,
    *,
    suppress_exceptions: bool,
) -> dict[str, object]:
    options = (
        optimizer_options
        if isinstance(optimizer_options, LayerOptionsCarrier)
        else coerce_layer_options("optimizer", optimizer_options)
    )
    doc = coerce_ir_document(ir)
    return _execute_ir_transform(
        runtime_spec.optimizer_impl,
        doc,
        options=options,
        fallback_payload=doc,
        suppress_exceptions=suppress_exceptions,
    )


def normalize_module_artifact_carrier(
    artifact_any: object,
    *,
    module_id: str,
    output_path: Path,
    extension: str,
    is_entry: bool,
    default_kind: str = "user",
) -> ModuleArtifactCarrier:
    artifact = artifact_any if isinstance(artifact_any, dict) else {}
    text = artifact_any if isinstance(artifact_any, str) else artifact.get("text", "")
    module_id_out = artifact.get("module_id", module_id)
    if not isinstance(module_id_out, str) or module_id_out == "":
        module_id_out = module_id if module_id != "" else (output_path.stem if output_path.stem != "" else "module")
    label = artifact.get("label", "")
    if not isinstance(label, str) or label == "":
        if output_path.stem != "":
            label = output_path.stem
        elif module_id_out != "":
            label = module_id_out.rsplit(".", 1)[-1]
        else:
            label = "module"
    extension_out = artifact.get("extension", extension)
    if not isinstance(extension_out, str) or extension_out == "":
        extension_out = extension if extension != "" else output_path.suffix
    helper_modules: list[ModuleArtifactCarrier] = []
    helper_any = artifact.get("helper_modules", [])
    if isinstance(helper_any, list):
        for item in helper_any:
            if not isinstance(item, dict):
                continue
            helper_modules.append(
                normalize_module_artifact_carrier(
                    item,
                    module_id=str(item.get("module_id", "")),
                    output_path=output_path,
                    extension=extension_out,
                    is_entry=bool(item.get("is_entry", False)),
                    default_kind="helper",
                )
            )
    kind_any = artifact.get("kind", default_kind)
    kind_out = kind_any if isinstance(kind_any, str) and kind_any != "" else default_kind
    return ModuleArtifactCarrier(
        module_id=module_id_out,
        kind=kind_out,
        label=label,
        extension=extension_out,
        text=text if isinstance(text, str) else "",
        is_entry=bool(artifact.get("is_entry", is_entry)),
        dependencies=copy_module_dependencies(artifact.get("dependencies", [])),
        metadata=copy_module_metadata(artifact.get("metadata", {})),
        helper_modules=tuple(helper_modules),
    )


def normalize_emitted_module_artifact(
    artifact_any: object,
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


def execute_emit_module_with_spec(
    runtime_spec: ResolvedBackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: LayerOptionsCarrier | dict[str, Any] | None = None,
    *,
    module_id: str = "",
    is_entry: bool = False,
    suppress_exceptions: bool,
) -> ModuleArtifactCarrier:
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
    artifact_any: object = {}
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
            artifact_any = fn(
                request.ir_document,
                request.output_path,
                export_layer_options_carrier(request.emitter_options),
            )
        except TypeError:
            try:
                artifact_any = fn(request.ir_document, request.output_path)
            except Exception:
                if not suppress_exceptions:
                    raise
                artifact_any = {}
        except Exception:
            if not suppress_exceptions:
                raise
            artifact_any = {}
    except Exception:
        if not suppress_exceptions:
            raise
        artifact_any = {}
    return normalize_emitted_module_artifact(artifact_any, request=request)


def emit_source_text_with_spec(
    runtime_spec: ResolvedBackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: LayerOptionsCarrier | dict[str, Any] | None = None,
    *,
    suppress_exceptions: bool,
) -> str:
    return execute_emit_module_with_spec(
        runtime_spec,
        ir,
        output_path,
        emitter_options,
        suppress_exceptions=suppress_exceptions,
    ).text


def build_legacy_emit_module_adapter(
    emit_impl: Any,
    *,
    extension: str,
    suppress_emit_exceptions: bool,
) -> Any:
    def _emit_module(
        ir: dict[str, object],
        output_path: Path,
        emitter_options: object = None,
        *,
        module_id: str = "",
        is_entry: bool = False,
    ) -> dict[str, object]:
        source_any: object = ""
        try:
            source_any = emit_impl(ir, output_path, export_layer_options_any(emitter_options, layer="emitter"))
        except TypeError:
            try:
                source_any = emit_impl(ir, output_path)
            except Exception:
                if not suppress_emit_exceptions:
                    raise
                source_any = ""
        except Exception:
            if not suppress_emit_exceptions:
                raise
            source_any = ""
        return export_module_artifact_any(
            normalize_module_artifact_carrier(
                source_any,
                module_id=module_id,
                output_path=output_path,
                extension=extension,
                is_entry=is_entry,
            )
        )

    return _emit_module


def flatten_module_artifact_carrier(module_artifact: ModuleArtifactCarrier) -> tuple[ModuleArtifactCarrier, ...]:
    primary = ModuleArtifactCarrier(
        module_id=module_artifact.module_id,
        kind=module_artifact.kind,
        label=module_artifact.label,
        extension=module_artifact.extension,
        text=module_artifact.text,
        is_entry=module_artifact.is_entry,
        dependencies=module_artifact.dependencies,
        metadata=dict(module_artifact.metadata),
    )
    out = [primary]
    for helper in module_artifact.helper_modules:
        helper_kind = helper.kind if helper.kind != "" else "helper"
        out.append(
            ModuleArtifactCarrier(
                module_id=helper.module_id,
                kind=helper_kind,
                label=helper.label,
                extension=helper.extension,
                text=helper.text,
                is_entry=helper.is_entry,
                dependencies=helper.dependencies,
                metadata=dict(helper.metadata),
            )
        )
    return tuple(out)


def collect_program_module_carriers(module_artifact: object) -> tuple[ModuleArtifactCarrier, ...]:
    carrier = coerce_module_artifact_or_none(module_artifact)
    if carrier is None:
        return ()
    return flatten_module_artifact_carrier(carrier)


def export_program_module_artifacts(module_artifact: object) -> list[dict[str, object]]:
    return [export_module_artifact_any(item) for item in collect_program_module_carriers(module_artifact)]


def coerce_module_artifact(module_artifact: object) -> ModuleArtifactCarrier:
    if isinstance(module_artifact, ModuleArtifactCarrier):
        return module_artifact
    legacy_module = _legacy_dict_adapter(module_artifact)
    if legacy_module is not None:
        module_artifact = legacy_module
    if isinstance(module_artifact, dict):
        return normalize_module_artifact_carrier(
            module_artifact,
            module_id=str(module_artifact.get("module_id", "")),
            output_path=Path(str(module_artifact.get("label", "module"))),
            extension=str(module_artifact.get("extension", "")),
            is_entry=bool(module_artifact.get("is_entry", False)),
            default_kind=str(module_artifact.get("kind", "user")) if isinstance(module_artifact.get("kind", "user"), str) else "user",
        )
    raise RuntimeError("module artifact must be dict or ModuleArtifactCarrier")


def coerce_module_artifact_or_none(module_artifact: object) -> ModuleArtifactCarrier | None:
    try:
        return coerce_module_artifact(module_artifact)
    except RuntimeError:
        return None


def coerce_program_artifact(
    program_artifact: object,
    *,
    fallback_target: str = "",
    fallback_program_id: str = "",
    fallback_entry_modules: list[str] | tuple[str, ...] | None = None,
    fallback_layout_mode: str = "single_file",
    fallback_link_output_schema: str = "",
    fallback_writer_options: dict[str, object] | None = None,
) -> ProgramArtifactCarrier:
    if isinstance(program_artifact, ProgramArtifactCarrier):
        return program_artifact
    legacy_program = _legacy_dict_adapter(program_artifact)
    if legacy_program is not None:
        program_artifact = legacy_program
    if not isinstance(program_artifact, dict):
        raise RuntimeError("program artifact must be dict or ProgramArtifactCarrier")

    modules_out: list[ModuleArtifactCarrier] = []
    modules_any = program_artifact.get("modules", ())
    if isinstance(modules_any, (list, tuple)):
        for item in modules_any:
            try:
                modules_out.extend(flatten_module_artifact_carrier(coerce_module_artifact(item)))
            except RuntimeError:
                continue

    target_any = program_artifact.get("target", fallback_target)
    target_out = target_any if isinstance(target_any, str) else fallback_target
    program_id_any = program_artifact.get("program_id", fallback_program_id)
    program_id_out = program_id_any if isinstance(program_id_any, str) else fallback_program_id
    if program_id_out == "" and len(modules_out) > 0:
        program_id_out = modules_out[0].module_id
    entry_modules_any = program_artifact.get("entry_modules", fallback_entry_modules if fallback_entry_modules is not None else ())
    layout_mode_any = program_artifact.get("layout_mode", fallback_layout_mode)
    link_output_schema_any = program_artifact.get("link_output_schema", fallback_link_output_schema)
    writer_options_any = program_artifact.get("writer_options", fallback_writer_options if fallback_writer_options is not None else {})
    return ProgramArtifactCarrier(
        target=target_out,
        program_id=program_id_out,
        entry_modules=_copy_string_tuple(entry_modules_any),
        modules=tuple(modules_out),
        layout_mode=layout_mode_any if isinstance(layout_mode_any, str) else fallback_layout_mode,
        link_output_schema=link_output_schema_any if isinstance(link_output_schema_any, str) else fallback_link_output_schema,
        writer_options=copy_program_writer_options(writer_options_any),
    )


def build_program_artifact_carrier(
    spec: ResolvedBackendSpec,
    modules: list[ModuleArtifactCarrier],
    *,
    program_id: str = "",
    entry_modules: list[str] | None = None,
    layout_mode: str = "single_file",
    link_output_schema: str = "",
    writer_options: dict[str, object] | None = None,
) -> ProgramArtifactCarrier:
    effective_program_id = program_id
    if effective_program_id == "" and len(modules) > 0:
        effective_program_id = modules[0].module_id
    entry_out = tuple(item for item in list(entry_modules or []) if isinstance(item, str) and item != "")
    return ProgramArtifactCarrier(
        target=spec.carrier.target_lang,
        program_id=effective_program_id,
        entry_modules=entry_out,
        modules=tuple(modules),
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=copy_program_writer_options(writer_options),
    )


def build_program_artifact_from_modules(
    spec: ResolvedBackendSpec,
    modules: list[object],
    *,
    program_id: str = "",
    entry_modules: list[str] | None = None,
    layout_mode: str = "single_file",
    link_output_schema: str = "",
    writer_options: dict[str, object] | None = None,
) -> ProgramArtifactCarrier:
    module_list: list[ModuleArtifactCarrier] = []
    for item in modules:
        coerced = coerce_module_artifact_or_none(item)
        if coerced is not None:
            module_list.append(coerced)
    return build_program_artifact_carrier(
        spec,
        module_list,
        program_id=program_id,
        entry_modules=entry_modules,
        layout_mode=layout_mode,
        link_output_schema=link_output_schema,
        writer_options=writer_options,
    )


def get_program_writer_with_spec(runtime_spec: ResolvedBackendSpec) -> Any:
    return runtime_spec.program_writer_impl


def apply_runtime_hook_with_spec(runtime_spec: ResolvedBackendSpec, output_path: Path) -> None:
    fn = runtime_spec.runtime_hook_impl
    if callable(fn):
        fn(output_path)

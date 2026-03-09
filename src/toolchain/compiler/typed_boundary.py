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


def _meta_dispatch_mode(raw_doc: dict[str, object]) -> str:
    meta_any = raw_doc.get("meta", {})
    if not isinstance(meta_any, dict):
        return ""
    dispatch_any = meta_any.get("dispatch_mode")
    return dispatch_any if isinstance(dispatch_any, str) else ""


def export_compiler_root_document(doc: "CompilerRootDocument") -> dict[str, object]:
    out = dict(doc.raw_module_doc)
    out["kind"] = doc.module_kind
    if doc.meta.source_path != "":
        out["source_path"] = doc.meta.source_path
    out["east_stage"] = doc.meta.east_stage
    out["schema_version"] = doc.meta.schema_version
    meta_any = out.get("meta", {})
    meta = meta_any if isinstance(meta_any, dict) else {}
    meta["dispatch_mode"] = doc.meta.dispatch_mode
    if doc.meta.parser_backend != "":
        meta["parser_backend"] = doc.meta.parser_backend
    out["meta"] = meta
    return out


def export_layer_options_carrier(options: "LayerOptionsCarrier") -> dict[str, CompilerOptionScalar]:
    return dict(options.values)


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
            source_path=source_path,
            east_stage=int(stage_any) if isinstance(stage_any, int) else 0,
            schema_version=int(schema_any) if isinstance(schema_any, int) else 0,
            dispatch_mode=_meta_dispatch_mode(raw_doc),
            parser_backend=parser_backend,
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
        return {
            "target_lang": self.target_lang,
            "extension": self.extension,
            "default_options": {
                layer: dict(values) for layer, values in self.default_options_by_layer.items()
            },
            "option_schema": {
                layer: {key: dict(rule) for key, rule in values.items()}
                for layer, values in self.option_schema_by_layer.items()
            },
        }


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
        out = {
            "module_id": self.module_id,
            "kind": self.kind,
            "label": self.label,
            "extension": self.extension,
            "text": self.text,
            "is_entry": self.is_entry,
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
        }
        if len(self.helper_modules) > 0:
            out["helper_modules"] = [module.to_legacy_dict() for module in self.helper_modules]
        return out


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
        return {
            "target": self.target,
            "program_id": self.program_id,
            "entry_modules": list(self.entry_modules),
            "modules": [module.to_legacy_dict() for module in self.modules],
            "layout_mode": self.layout_mode,
            "link_output_schema": self.link_output_schema,
            "writer_options": dict(self.writer_options),
        }


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
        out = self.carrier.to_legacy_dict()
        out["lower"] = self.lower_impl
        out["optimizer"] = self.optimizer_impl
        out["emit"] = self.emit_impl
        out["emit_module"] = self.emit_module_impl
        out["program_writer"] = self.program_writer_impl
        out["runtime_hook"] = self.runtime_hook_impl
        return out


def coerce_compiler_root_document(
    raw_doc: object,
    *,
    source_path: str = "",
    parser_backend: str = "",
) -> CompilerRootDocument:
    if isinstance(raw_doc, CompilerRootDocument):
        return raw_doc
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
    return LayerOptionsCarrier(layer=layer, values=_copy_scalar_dict(raw_options))


def coerce_backend_spec(raw_spec: object) -> ResolvedBackendSpec:
    if isinstance(raw_spec, ResolvedBackendSpec):
        return raw_spec
    if isinstance(raw_spec, dict):
        return ResolvedBackendSpec.from_legacy_spec(raw_spec)
    raise RuntimeError("backend spec must be dict or ResolvedBackendSpec")


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


def coerce_module_artifact(module_artifact: object) -> ModuleArtifactCarrier:
    if isinstance(module_artifact, ModuleArtifactCarrier):
        return module_artifact
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

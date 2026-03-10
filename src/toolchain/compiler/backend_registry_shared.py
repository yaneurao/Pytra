"""Shared helpers for host/static backend registries."""

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
from toolchain.compiler.typed_boundary import ResolvedBackendSpec
from toolchain.compiler.typed_boundary import build_resolved_backend_spec
from toolchain.compiler.typed_boundary import coerce_ir_document
from toolchain.compiler.typed_boundary import export_layer_options_any


def registry_src_root(module_file: str) -> Path:
    return Path(module_file).resolve().parents[2]


def identity_ir(doc: object) -> dict[str, object]:
    return coerce_ir_document(doc)


def empty_emit(_ir: object, _output_path: Path, _emitter_options: object = None) -> str:
    return ""


def default_output_path_for(input_path: Path, ext: str) -> Path:
    stem = str(input_path)
    if stem.endswith(".py"):
        stem = stem[:-3]
    elif stem.endswith(".json"):
        stem = stem[:-5]
    return Path(stem + ext)


def copy_runtime_file(src_root: Path, src_rel: str, output_path: Path, dst_name: str) -> None:
    src = src_root / src_rel
    if not src.exists():
        raise RuntimeError("runtime source not found: " + str(src))
    dst = output_path.parent / dst_name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def copy_runtime_files(src_root: Path, file_specs: list[object], output_path: Path) -> None:
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid runtime file descriptor")
        src_rel = item[0]
        dst_name = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_name, str):
            raise RuntimeError("invalid runtime file descriptor")
        copy_runtime_file(src_root, src_rel, output_path, dst_name)


def copy_php_runtime_files(src_root: Path, file_specs: list[object], output_path: Path) -> None:
    php_src_root = src_root / "runtime" / "php"
    if not php_src_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(php_src_root))
    dst_root = output_path.parent / "pytra"
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid php runtime file descriptor")
        src_rel = item[0]
        dst_rel = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_rel, str):
            raise RuntimeError("invalid php runtime file descriptor")
        src = php_src_root / src_rel
        if not src.exists():
            raise RuntimeError("php runtime source missing: " + str(src))
        dst = dst_root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def runtime_none(_output_path: Path) -> None:
    return


def _normalize_emit_text(out: object) -> str:
    return out if isinstance(out, str) else ""


def build_unary_emit(emit_impl: Any) -> Any:
    def _emit(ir: dict[str, object], _output_path: Path, _emitter_options: object = None) -> str:
        return _normalize_emit_text(emit_impl(ir))

    return _emit


def build_cpp_emit(emit_impl: Any) -> Any:
    def _emit_cpp(ir: dict[str, object], _output_path: Path, emitter_options: object = None) -> str:
        opts = export_layer_options_any(emitter_options, layer="emitter")
        return _normalize_emit_text(
            emit_impl(
                ir,
                negative_index_mode=str(opts.get("negative_index_mode", "const_only")),
                bounds_check_mode=str(opts.get("bounds_check_mode", "off")),
                floor_div_mode=str(opts.get("floor_div_mode", "native")),
                mod_mode=str(opts.get("mod_mode", "native")),
            )
        )

    return _emit_cpp


def build_java_emit(emit_impl: Any) -> Any:
    def _emit_java(ir: dict[str, object], output_path: Path, _emitter_options: object = None) -> str:
        class_name = output_path.stem if output_path.stem != "" else "Main"
        return _normalize_emit_text(emit_impl(ir, class_name=class_name))

    return _emit_java


def build_emit_from_target(
    target: str,
    *,
    resolve_callable_ref: Any,
    cpp_emit_factory: Any,
    java_emit_factory: Any,
    unary_emit_factory: Any,
) -> Any:
    emit_kind = get_backend_emit_kind(target)
    emit_impl = resolve_callable_ref(get_backend_emit_ref(target))
    if emit_kind == "cpp":
        return cpp_emit_factory(emit_impl)
    if emit_kind == "java":
        return java_emit_factory(emit_impl)
    if emit_kind == "unary":
        return unary_emit_factory(emit_impl)
    raise RuntimeError("unsupported emit kind: " + emit_kind)


def build_runtime_hook_from_descriptor(
    runtime_key: str,
    descriptor: dict[str, object],
    *,
    none_hook: Any,
    js_shims_hook: Any,
    copy_files_factory: Any,
    php_runtime_factory: Any,
) -> Any:
    kind = str(descriptor.get("kind", ""))
    files_any = descriptor.get("files", [])
    files = files_any if isinstance(files_any, list) else []
    if kind == "none":
        return none_hook
    if kind == "js_shims":
        return js_shims_hook
    if kind == "copy_files":
        return copy_files_factory(files)
    if kind == "php_runtime":
        return php_runtime_factory(files)
    raise RuntimeError("unsupported runtime hook kind: " + runtime_key)


def build_runtime_bound_backend_spec(
    target: str,
    *,
    resolve_callable_ref: Any,
    emit_from_target: Any,
    runtime_hook_from_key: Any,
    identity_ir_impl: Any,
) -> dict[str, Any]:
    spec = build_backend_spec_metadata(target)
    lower_ref = get_backend_lower_ref(target)
    optimizer_ref = get_backend_optimizer_ref(target)
    spec["lower"] = identity_ir_impl if lower_ref == "" else resolve_callable_ref(lower_ref)
    spec["optimizer"] = identity_ir_impl if optimizer_ref == "" else resolve_callable_ref(optimizer_ref)
    spec["emit"] = emit_from_target(target)
    spec["runtime_hook"] = runtime_hook_from_key(get_backend_runtime_hook_key(target))
    program_writer_key = get_backend_program_writer_key(target)
    if program_writer_key != "":
        spec["program_writer"] = resolve_callable_ref(get_program_writer_ref(program_writer_key))
    return spec


def normalize_runtime_backend_spec(
    spec: dict[str, Any],
    *,
    default_program_writer: Any,
    suppress_emit_exceptions: bool,
    identity_ir_impl: Any,
    empty_emit_impl: Any,
    runtime_none_hook: Any,
) -> ResolvedBackendSpec:
    return build_resolved_backend_spec(
        spec,
        identity_ir=identity_ir_impl,
        empty_emit=empty_emit_impl,
        runtime_none=runtime_none_hook,
        default_program_writer=default_program_writer,
        suppress_emit_exceptions=suppress_emit_exceptions,
    )

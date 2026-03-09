"""Host-side backend registry for unified ``py2x`` frontend.

This module keeps target backend imports lazy so regular host execution only loads
modules for the selected target.
"""

from __future__ import annotations

import importlib

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


BackendSpec = dict


def _src_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _identity_ir(doc: Any) -> dict:
    return coerce_ir_document(doc)


def _empty_emit(_ir: Any, _output_path: Path, _emitter_options: Any = None) -> str:
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


def _runtime_none(_output_path: Path) -> None:
    return


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


def _legacy_emit_module_adapter(emit_impl: Any, *, extension: str) -> Any:
    def _emit_module(
        ir: dict[str, Any],
        output_path: Path,
        emitter_options: Any = None,
        *,
        module_id: str = "",
        is_entry: bool = False,
    ) -> dict[str, Any]:
        source_any: Any = ""
        try:
            source_any = emit_impl(ir, output_path, emitter_options if isinstance(emitter_options, dict) else {})
        except TypeError:
            try:
                source_any = emit_impl(ir, output_path)
            except Exception:
                source_any = ""
        except Exception:
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


def _load_callable(module_name: str, symbol_name: str) -> Any:
    mod = importlib.import_module(module_name)
    fn = _module_symbol(mod, symbol_name)
    if fn is None:
        raise RuntimeError("missing symbol: " + module_name + "." + symbol_name)
    return fn


def _make_unary_emit(module_name: str, symbol_name: str) -> Any:
    emit_impl = _load_callable(module_name, symbol_name)

    def _emit(ir: dict, _output_path: Path, _emitter_options: Any = None) -> str:
        out = emit_impl(ir)
        return out if isinstance(out, str) else ""

    return _emit


def _load_cpp_spec() -> BackendSpec:
    transpile_to_cpp = _load_callable("backends.cpp.cli", "transpile_to_cpp")
    write_cpp_program = _load_callable("backends.cpp.program_writer", "write_cpp_program")

    def _emit_cpp(ir: dict, _output_path: Path, emitter_options: Any = None) -> str:
        opts = emitter_options if isinstance(emitter_options, dict) else {}
        negative_index_mode = str(opts.get("negative_index_mode", "const_only"))
        bounds_check_mode = str(opts.get("bounds_check_mode", "off"))
        floor_div_mode = str(opts.get("floor_div_mode", "native"))
        mod_mode = str(opts.get("mod_mode", "native"))
        out = transpile_to_cpp(
            ir,
            negative_index_mode=negative_index_mode,
            bounds_check_mode=bounds_check_mode,
            floor_div_mode=floor_div_mode,
            mod_mode=mod_mode,
        )
        return out if isinstance(out, str) else ""

    return {
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
    }


def _load_rs_spec() -> BackendSpec:
    return {
        "target_lang": "rs",
        "extension": ".rs",
        "lower": _load_callable("backends.rs.lower", "lower_east3_to_rs_ir"),
        "optimizer": _load_callable("backends.rs.optimizer", "optimize_rs_ir"),
        "emit": _make_unary_emit("backends.rs.emitter.rs_emitter", "transpile_to_rust"),
        "runtime_hook": _runtime_rs,
    }


def _load_cs_spec() -> BackendSpec:
    return {
        "target_lang": "cs",
        "extension": ".cs",
        "lower": _load_callable("backends.cs.lower", "lower_east3_to_cs_ir"),
        "optimizer": _load_callable("backends.cs.optimizer", "optimize_cs_ir"),
        "emit": _make_unary_emit("backends.cs.emitter.cs_emitter", "transpile_to_csharp"),
        "runtime_hook": _runtime_none,
    }


def _load_js_spec() -> BackendSpec:
    return {
        "target_lang": "js",
        "extension": ".js",
        "lower": _load_callable("backends.js.lower", "lower_east3_to_js_ir"),
        "optimizer": _load_callable("backends.js.optimizer", "optimize_js_ir"),
        "emit": _make_unary_emit("backends.js.emitter.js_emitter", "transpile_to_js"),
        "runtime_hook": _runtime_js_shims,
    }


def _load_ts_spec() -> BackendSpec:
    return {
        "target_lang": "ts",
        "extension": ".ts",
        "lower": _load_callable("backends.ts.lower", "lower_east3_to_ts_ir"),
        "optimizer": _load_callable("backends.ts.optimizer", "optimize_ts_ir"),
        "emit": _make_unary_emit("backends.ts.emitter.ts_emitter", "transpile_to_typescript"),
        "runtime_hook": _runtime_js_shims,
    }


def _load_go_spec() -> BackendSpec:
    return {
        "target_lang": "go",
        "extension": ".go",
        "lower": _load_callable("backends.go.lower", "lower_east3_to_go_ir"),
        "optimizer": _load_callable("backends.go.optimizer", "optimize_go_ir"),
        "emit": _make_unary_emit("backends.go.emitter", "transpile_to_go_native"),
        "runtime_hook": _runtime_go,
    }


def _load_java_spec() -> BackendSpec:
    lower = _load_callable("backends.java.lower", "lower_east3_to_java_ir")
    optimizer = _load_callable("backends.java.optimizer", "optimize_java_ir")
    emit_impl = _load_callable("backends.java.emitter", "transpile_to_java_native")

    def _emit_java(ir: dict, output_path: Path, _emitter_options: Any = None) -> str:
        class_name = output_path.stem if output_path.stem != "" else "Main"
        out = emit_impl(ir, class_name=class_name)
        return out if isinstance(out, str) else ""

    return {
        "target_lang": "java",
        "extension": ".java",
        "lower": lower,
        "optimizer": optimizer,
        "emit": _emit_java,
        "runtime_hook": _runtime_java,
    }


def _load_kotlin_spec() -> BackendSpec:
    return {
        "target_lang": "kotlin",
        "extension": ".kt",
        "lower": _load_callable("backends.kotlin.lower", "lower_east3_to_kotlin_ir"),
        "optimizer": _load_callable("backends.kotlin.optimizer", "optimize_kotlin_ir"),
        "emit": _make_unary_emit("backends.kotlin.emitter", "transpile_to_kotlin_native"),
        "runtime_hook": _runtime_kotlin,
    }


def _load_swift_spec() -> BackendSpec:
    return {
        "target_lang": "swift",
        "extension": ".swift",
        "lower": _load_callable("backends.swift.lower", "lower_east3_to_swift_ir"),
        "optimizer": _load_callable("backends.swift.optimizer", "optimize_swift_ir"),
        "emit": _make_unary_emit("backends.swift.emitter", "transpile_to_swift_native"),
        "runtime_hook": _runtime_swift,
    }


def _load_ruby_spec() -> BackendSpec:
    return {
        "target_lang": "ruby",
        "extension": ".rb",
        "lower": _load_callable("backends.ruby.lower", "lower_east3_to_ruby_ir"),
        "optimizer": _load_callable("backends.ruby.optimizer", "optimize_ruby_ir"),
        "emit": _make_unary_emit("backends.ruby.emitter", "transpile_to_ruby_native"),
        "runtime_hook": _runtime_ruby,
    }


def _load_lua_spec() -> BackendSpec:
    return {
        "target_lang": "lua",
        "extension": ".lua",
        "lower": _load_callable("backends.lua.lower", "lower_east3_to_lua_ir"),
        "optimizer": _load_callable("backends.lua.optimizer", "optimize_lua_ir"),
        "emit": _make_unary_emit("backends.lua.emitter", "transpile_to_lua_native"),
        "runtime_hook": _runtime_lua,
    }


def _load_scala_spec() -> BackendSpec:
    return {
        "target_lang": "scala",
        "extension": ".scala",
        "lower": _load_callable("backends.scala.lower", "lower_east3_to_scala_ir"),
        "optimizer": _load_callable("backends.scala.optimizer", "optimize_scala_ir"),
        "emit": _make_unary_emit("backends.scala.emitter", "transpile_to_scala_native"),
        "runtime_hook": _runtime_scala,
    }


def _load_php_spec() -> BackendSpec:
    return {
        "target_lang": "php",
        "extension": ".php",
        "lower": _load_callable("backends.php.lower", "lower_east3_to_php_ir"),
        "optimizer": _load_callable("backends.php.optimizer", "optimize_php_ir"),
        "emit": _make_unary_emit("backends.php.emitter", "transpile_to_php_native"),
        "runtime_hook": _copy_php_runtime,
    }


def _load_nim_spec() -> BackendSpec:
    return {
        "target_lang": "nim",
        "extension": ".nim",
        "lower": _identity_ir,
        "optimizer": _identity_ir,
        "emit": _make_unary_emit("backends.nim.emitter", "transpile_to_nim_native"),
        "runtime_hook": _runtime_nim,
    }


_TARGET_ORDER: list = [
    "cpp",
    "rs",
    "cs",
    "js",
    "ts",
    "go",
    "java",
    "kotlin",
    "swift",
    "ruby",
    "lua",
    "scala",
    "php",
    "nim",
]

_TARGET_LOADERS: dict = {
    "cpp": _load_cpp_spec,
    "rs": _load_rs_spec,
    "cs": _load_cs_spec,
    "js": _load_js_spec,
    "ts": _load_ts_spec,
    "go": _load_go_spec,
    "java": _load_java_spec,
    "kotlin": _load_kotlin_spec,
    "swift": _load_swift_spec,
    "ruby": _load_ruby_spec,
    "lua": _load_lua_spec,
    "scala": _load_scala_spec,
    "php": _load_php_spec,
    "nim": _load_nim_spec,
}

_SPEC_CACHE: dict[str, ResolvedBackendSpec] = {}


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
        program_writer_impl = _load_callable("backends.common.program_writer", "write_single_file_program")
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


def _normalize_backend_spec(spec: BackendSpec) -> BackendSpec:
    return export_resolved_backend_spec_any(_normalize_backend_runtime_spec(spec))


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


def list_backend_targets() -> list:
    return list(_TARGET_ORDER)


def get_backend_spec_typed(target: str) -> ResolvedBackendSpec:
    if target not in _TARGET_LOADERS:
        raise RuntimeError("unsupported target: " + target)
    cached = _SPEC_CACHE.get(target)
    if isinstance(cached, ResolvedBackendSpec):
        return cached
    loader = _TARGET_LOADERS[target]
    spec_any = loader()
    if not isinstance(spec_any, dict):
        raise RuntimeError("invalid backend spec for target: " + target)
    spec = _normalize_backend_runtime_spec(spec_any)
    _SPEC_CACHE[target] = spec
    return spec


def get_backend_spec(target: str) -> BackendSpec:
    return export_resolved_backend_spec_any(get_backend_spec_typed(target))


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


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict) -> dict:
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
    try:
        ir = fn(doc, export_layer_options_carrier(options))
    except TypeError:
        try:
            ir = fn(doc)
        except Exception:
            ir = _identity_ir(doc)
    except Exception:
        ir = _identity_ir(doc)
    return coerce_ir_document(ir)


def lower_ir(spec: BackendSpec, east_doc: dict, lower_options: Any = None) -> dict:
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
    try:
        out = fn(ir, export_layer_options_carrier(options))
    except TypeError:
        try:
            out = fn(ir)
        except Exception:
            out = _identity_ir(ir)
    except Exception:
        out = _identity_ir(ir)
    return coerce_ir_document(out)


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
            try:
                artifact_any = fn(request.ir_document, request.output_path)
            except Exception:
                artifact_any = {}
        except Exception:
            artifact_any = {}
    except Exception:
        artifact_any = {}
    return _normalize_module_artifact_typed(artifact_any, request=request)


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
    carrier = coerce_module_artifact_or_none(module_artifact)
    if carrier is None:
        return ()
    return flatten_module_artifact_carrier(carrier)


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return [export_module_artifact_any(item) for item in collect_program_modules_typed(module_artifact)]


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


def get_program_writer_typed(spec: BackendSpec | ResolvedBackendSpec) -> Any:
    runtime_spec = _coerce_runtime_spec(spec)
    return runtime_spec.program_writer_impl


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
    return emit_module_typed(spec, ir, output_path, emitter_options).text


def apply_runtime_hook_typed(spec: BackendSpec | ResolvedBackendSpec, output_path: Path) -> None:
    runtime_spec = _coerce_runtime_spec(spec)
    fn = runtime_spec.runtime_hook_impl
    if fn is not None:
        fn(output_path)


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    apply_runtime_hook_typed(spec, output_path)

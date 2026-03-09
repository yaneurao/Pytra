"""Backend registry for unified ``py2x`` frontend."""

from __future__ import annotations

from typing import Any
from pytra.std.pathlib import Path
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

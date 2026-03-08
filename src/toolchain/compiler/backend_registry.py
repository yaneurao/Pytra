"""Host-side backend registry for unified ``py2x`` frontend.

This module keeps target backend imports lazy so regular host execution only loads
modules for the selected target.
"""

from __future__ import annotations

import importlib

from typing import Any
from pytra.std.pathlib import Path


BackendSpec = dict


def _src_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _identity_ir(doc: Any) -> dict:
    return doc if isinstance(doc, dict) else {}


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
    kind_out = artifact.get("kind", "user")
    if not isinstance(kind_out, str) or kind_out == "":
        kind_out = "user"
    return {
        "module_id": module_id_out,
        "kind": kind_out,
        "label": label,
        "extension": extension_out,
        "text": text if isinstance(text, str) else "",
        "is_entry": bool(is_entry_out),
        "dependencies": dependencies_out,
        "metadata": dict(metadata_out),
    }


def _flatten_helper_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    modules_out: list[dict[str, Any]] = []
    primary = dict(module_artifact)
    if "helper_modules" in primary:
        del primary["helper_modules"]
    modules_out.append(primary)
    helper_any = module_artifact.get("helper_modules", [])
    if not isinstance(helper_any, list):
        return modules_out
    for item in helper_any:
        if not isinstance(item, dict):
            continue
        helper = dict(item)
        kind_any = helper.get("kind", "helper")
        if not isinstance(kind_any, str) or kind_any == "":
            kind_any = "helper"
        helper["kind"] = kind_any
        metadata_any = helper.get("metadata", {})
        helper["metadata"] = dict(metadata_any) if isinstance(metadata_any, dict) else {}
        modules_out.append(helper)
    return modules_out


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
        return _normalize_module_artifact(
            source_any,
            module_id=module_id,
            output_path=output_path,
            extension=extension,
            is_entry=is_entry,
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

_SPEC_CACHE: dict = {}


def _normalize_backend_spec(spec: BackendSpec) -> BackendSpec:
    extension = str(spec.get("extension", ""))
    defaults = spec.get("default_options")
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
    spec["default_options"] = {
        "lower": dict(default_lower),
        "optimizer": dict(default_optimizer),
        "emitter": dict(default_emitter),
    }

    schemas = spec.get("option_schema")
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
    spec["option_schema"] = {
        "lower": dict(schema_lower),
        "optimizer": dict(schema_optimizer),
        "emitter": dict(schema_emitter),
    }
    emit_module_any = spec.get("emit_module")
    if not callable(emit_module_any):
        emit_any = spec.get("emit", _identity_ir)
        emit_module_any = _legacy_emit_module_adapter(emit_any, extension=extension)
    spec["emit_module"] = emit_module_any
    program_writer_any = spec.get("program_writer")
    if not callable(program_writer_any) and not isinstance(program_writer_any, dict):
        program_writer_any = _load_callable("backends.common.program_writer", "write_single_file_program")
    spec["program_writer"] = program_writer_any
    return spec


def list_backend_targets() -> list:
    return list(_TARGET_ORDER)


def get_backend_spec(target: str) -> BackendSpec:
    if target not in _TARGET_LOADERS:
        raise RuntimeError("unsupported target: " + target)
    cached = _SPEC_CACHE.get(target)
    if isinstance(cached, dict):
        return cached
    loader = _TARGET_LOADERS[target]
    spec_any = loader()
    if not isinstance(spec_any, dict):
        raise RuntimeError("invalid backend spec for target: " + target)
    spec = _normalize_backend_spec(spec_any)
    _SPEC_CACHE[target] = spec
    return spec


def default_output_path(input_path: Path, target: str) -> Path:
    spec = get_backend_spec(target)
    ext = str(spec.get("extension", ""))
    return _default_output_path_for(input_path, ext)


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict) -> dict:
    defaults = spec.get("default_options")
    if not isinstance(defaults, dict):
        defaults = {}
    merged = defaults.get(layer)
    if not isinstance(merged, dict):
        merged = {}
    out: dict = dict(merged)

    schemas = spec.get("option_schema")
    if not isinstance(schemas, dict):
        schemas = {}
    schema = schemas.get(layer)
    if not isinstance(schema, dict):
        schema = {}

    for key, raw in raw_options.items():
        if key not in schema:
            raise RuntimeError("unknown " + layer + " option: " + key)
        rule = schema[key]
        if not isinstance(rule, dict):
            raise RuntimeError("invalid schema for option: " + key)
        typ = str(rule.get("type", "str"))
        value_any: Any = raw
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

        choices = rule.get("choices")
        if isinstance(choices, list) and len(choices) > 0 and value_any not in choices:
            raise RuntimeError("invalid value for option " + key + ": " + str(value_any))
        out[key] = value_any
    return out


def lower_ir(spec: BackendSpec, east_doc: dict, lower_options: Any = None) -> dict:
    fn = spec.get("lower", _identity_ir)
    try:
        ir = fn(east_doc, lower_options if isinstance(lower_options, dict) else {})
    except TypeError:
        try:
            ir = fn(east_doc)
        except Exception:
            ir = _identity_ir(east_doc)
    except Exception:
        ir = _identity_ir(east_doc)
    return ir if isinstance(ir, dict) else {}


def optimize_ir(spec: BackendSpec, ir: dict, optimizer_options: Any = None) -> dict:
    fn = spec.get("optimizer", _identity_ir)
    try:
        out = fn(ir, optimizer_options if isinstance(optimizer_options, dict) else {})
    except TypeError:
        try:
            out = fn(ir)
        except Exception:
            out = _identity_ir(ir)
    except Exception:
        out = _identity_ir(ir)
    return out if isinstance(out, dict) else {}


def emit_module(
    spec: BackendSpec,
    ir: dict,
    output_path: Path,
    emitter_options: Any = None,
    *,
    module_id: str = "",
    is_entry: bool = False,
) -> dict[str, Any]:
    fn = spec.get("emit_module")
    extension = str(spec.get("extension", ""))
    if not callable(fn):
        return _normalize_module_artifact(
            "",
            module_id=module_id,
            output_path=output_path,
            extension=extension,
            is_entry=is_entry,
        )
    artifact_any: Any = {}
    try:
        artifact_any = fn(
            ir,
            output_path,
            emitter_options if isinstance(emitter_options, dict) else {},
            module_id=module_id,
            is_entry=is_entry,
        )
    except TypeError:
        try:
            artifact_any = fn(ir, output_path, emitter_options if isinstance(emitter_options, dict) else {})
        except TypeError:
            try:
                artifact_any = fn(ir, output_path)
            except Exception:
                artifact_any = {}
        except Exception:
            artifact_any = {}
    except Exception:
        artifact_any = {}
    return _normalize_module_artifact(
        artifact_any,
        module_id=module_id,
        output_path=output_path,
        extension=extension,
        is_entry=is_entry,
    )


def collect_program_modules(module_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(module_artifact, dict):
        return []
    return _flatten_helper_modules(module_artifact)


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
    target = str(spec.get("target_lang", ""))
    module_list: list[dict[str, Any]] = []
    for item in modules:
        if not isinstance(item, dict):
            continue
        module = dict(item)
        kind_any = module.get("kind", "user")
        if not isinstance(kind_any, str) or kind_any == "":
            kind_any = "user"
        module["kind"] = kind_any
        metadata_any = module.get("metadata", {})
        module["metadata"] = dict(metadata_any) if isinstance(metadata_any, dict) else {}
        module_list.append(module)
    effective_program_id = program_id
    if effective_program_id == "" and len(module_list) > 0:
        first_module_id = module_list[0].get("module_id", "")
        if isinstance(first_module_id, str):
            effective_program_id = first_module_id
    entry_out = [item for item in list(entry_modules or []) if isinstance(item, str) and item != ""]
    return {
        "target": target,
        "program_id": effective_program_id,
        "entry_modules": entry_out,
        "modules": module_list,
        "layout_mode": layout_mode,
        "link_output_schema": link_output_schema,
        "writer_options": dict(writer_options) if isinstance(writer_options, dict) else {},
    }


def get_program_writer(spec: BackendSpec) -> Any:
    return spec.get("program_writer")


def emit_source(
    spec: BackendSpec,
    ir: dict,
    output_path: Path,
    emitter_options: Any = None,
) -> str:
    artifact = emit_module(spec, ir, output_path, emitter_options)
    source = artifact.get("text", "")
    return source if isinstance(source, str) else ""


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    fn = spec.get("runtime_hook", _runtime_none)
    if fn is not None:
        fn(output_path)

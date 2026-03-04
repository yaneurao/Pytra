"""Backend registry for unified ``py2x`` frontend."""

from __future__ import annotations

from pytra.std.typing import Any
from pytra.std.pathlib import Path

from backends.cs.lower import lower_east3_to_cs_ir
from backends.cs.optimizer import optimize_cs_ir
from backends.cs.emitter.cs_emitter import transpile_to_csharp
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
    src_root = _src_root() / "runtime" / "php" / "pytra"
    if not src_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(src_root))
    dst_root = output_path.parent / "pytra"
    files = [
        "py_runtime.php",
        "runtime/png.php",
        "runtime/gif.php",
        "std/time.php",
    ]
    for rel in files:
        src = src_root / rel
        if not src.exists():
            raise RuntimeError("php runtime source missing: " + str(src))
        dst = dst_root / rel
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
    _copy_runtime_file("runtime/java/pytra-gen/utils/PngHelper.java", output_path, "PngHelper.java")
    _copy_runtime_file("runtime/java/pytra-gen/utils/GifHelper.java", output_path, "GifHelper.java")


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
    _copy_runtime_file("runtime/lua/pytra/py_runtime.lua", output_path, "py_runtime.lua")


def _runtime_scala(output_path: Path) -> None:
    _copy_runtime_file("runtime/scala/pytra/py_runtime.scala", output_path, "py_runtime.scala")


def _runtime_nim(output_path: Path) -> None:
    _copy_runtime_file("runtime/nim/pytra/py_runtime.nim", output_path, "py_runtime.nim")


BackendSpec = dict[str, Any]


_BACKEND_SPECS: dict[str, BackendSpec] = {
    "cpp": {
        "target_lang": "cpp",
        "extension": ".cpp",
        "lower": _identity_ir,
        "optimizer": _identity_ir,
        "emit": _emit_cpp,
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


def _normalize_backend_specs() -> None:
    for spec in _BACKEND_SPECS.values():
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


_normalize_backend_specs()


def list_backend_targets() -> list[str]:
    return list(_BACKEND_SPECS.keys())


def get_backend_spec(target: str) -> BackendSpec:
    if target not in _BACKEND_SPECS:
        raise RuntimeError("unsupported target: " + target)
    return _BACKEND_SPECS[target]


def default_output_path(input_path: Path, target: str) -> Path:
    spec = get_backend_spec(target)
    ext = str(spec.get("extension", ""))
    return _default_output_path_for(input_path, ext)


def resolve_layer_options(spec: BackendSpec, layer: str, raw_options: dict[str, str]) -> dict[str, Any]:
    defaults = spec.get("default_options")
    if not isinstance(defaults, dict):
        defaults = {}
    merged = defaults.get(layer)
    if not isinstance(merged, dict):
        merged = {}
    out: dict[str, Any] = dict(merged)

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


def lower_ir(spec: BackendSpec, east_doc: dict[str, Any], lower_options: dict[str, Any] | None = None) -> dict[str, Any]:
    fn = spec.get("lower", _identity_ir)
    if not callable(fn):
        return _identity_ir(east_doc)
    try:
        ir = fn(east_doc, lower_options if isinstance(lower_options, dict) else {})
    except TypeError:
        ir = fn(east_doc)
    return ir if isinstance(ir, dict) else {}


def optimize_ir(spec: BackendSpec, ir: dict[str, Any], optimizer_options: dict[str, Any] | None = None) -> dict[str, Any]:
    fn = spec.get("optimizer", _identity_ir)
    if not callable(fn):
        return _identity_ir(ir)
    try:
        out = fn(ir, optimizer_options if isinstance(optimizer_options, dict) else {})
    except TypeError:
        out = fn(ir)
    return out if isinstance(out, dict) else {}


def emit_source(
    spec: BackendSpec,
    ir: dict[str, Any],
    output_path: Path,
    emitter_options: dict[str, Any] | None = None,
) -> str:
    fn = spec.get("emit", _emit_cpp)
    if not callable(fn):
        return ""
    try:
        source = fn(ir, output_path, emitter_options if isinstance(emitter_options, dict) else {})
    except TypeError:
        source = fn(ir, output_path)
    return source if isinstance(source, str) else ""


def apply_runtime_hook(spec: BackendSpec, output_path: Path) -> None:
    fn = spec.get("runtime_hook", _runtime_none)
    if callable(fn):
        fn(output_path)

"""Host-side backend registry for unified ``py2x`` frontend.

This module keeps target backend imports lazy so regular host execution only loads
modules for the selected target.
"""

from __future__ import annotations

import importlib

from pytra.std.typing import Any
from pytra.std.pathlib import Path


BackendSpec = dict[str, Any]


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


def _runtime_none(_output_path: Path) -> None:
    return


def _runtime_js_shims(output_path: Path) -> None:
    mod = importlib.import_module("toolchain.compiler.js_runtime_shims")
    writer = getattr(mod, "write_js_runtime_shims", None)
    if not callable(writer):
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
    _copy_runtime_file("runtime/java/pytra-gen/utils/PngHelper.java", output_path, "PngHelper.java")
    _copy_runtime_file("runtime/java/pytra-gen/utils/GifHelper.java", output_path, "GifHelper.java")


def _runtime_kotlin(output_path: Path) -> None:
    _copy_runtime_file("runtime/kotlin/pytra/py_runtime.kt", output_path, "py_runtime.kt")


def _runtime_swift(output_path: Path) -> None:
    _copy_runtime_file("runtime/swift/pytra/py_runtime.swift", output_path, "py_runtime.swift")


def _runtime_ruby(output_path: Path) -> None:
    _copy_runtime_file("runtime/ruby/pytra/py_runtime.rb", output_path, "py_runtime.rb")


def _runtime_lua(output_path: Path) -> None:
    _copy_runtime_file("runtime/lua/pytra/py_runtime.lua", output_path, "py_runtime.lua")


def _runtime_scala(output_path: Path) -> None:
    _copy_runtime_file("runtime/scala/pytra/py_runtime.scala", output_path, "py_runtime.scala")


def _runtime_nim(output_path: Path) -> None:
    _copy_runtime_file("runtime/nim/pytra/py_runtime.nim", output_path, "py_runtime.nim")


def _load_callable(module_name: str, symbol_name: str) -> Any:
    mod = importlib.import_module(module_name)
    fn = getattr(mod, symbol_name, None)
    if fn is None:
        raise RuntimeError("missing symbol: " + module_name + "." + symbol_name)
    return fn


def _make_unary_emit(module_name: str, symbol_name: str) -> Any:
    emit_impl = _load_callable(module_name, symbol_name)

    def _emit(ir: dict[str, Any], _output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
        out = emit_impl(ir)
        return out if isinstance(out, str) else ""

    return _emit


def _load_cpp_spec() -> BackendSpec:
    transpile_to_cpp = _load_callable("py2cpp", "transpile_to_cpp")

    def _emit_cpp(ir: dict[str, Any], _output_path: Path, emitter_options: dict[str, Any] | None = None) -> str:
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

    def _emit_java(ir: dict[str, Any], output_path: Path, _emitter_options: dict[str, Any] | None = None) -> str:
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


_TARGET_ORDER: list[str] = [
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

_TARGET_LOADERS: dict[str, Any] = {
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

_SPEC_CACHE: dict[str, BackendSpec] = {}


def _normalize_backend_spec(spec: BackendSpec) -> BackendSpec:
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
    return spec


def list_backend_targets() -> list[str]:
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
    fn = spec.get("emit", _identity_ir)
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

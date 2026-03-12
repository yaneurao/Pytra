"""Canonical metadata shared by host and static backend registries."""

from __future__ import annotations

from typing import Any

from toolchain.compiler.backend_registry_diagnostics import unsupported_program_writer_key_message
from toolchain.compiler.backend_registry_diagnostics import unsupported_runtime_hook_key_message
from toolchain.compiler.backend_registry_diagnostics import unsupported_target_message


CompilerOptionScalar = str | int | bool
BackendDescriptor = dict[str, object]
RuntimeHookDescriptor = dict[str, object]


def _deep_copy(value: object) -> object:
    if isinstance(value, dict):
        out: dict[str, object] = {}
        for key, item in value.items():
            if isinstance(key, str):
                out[key] = _deep_copy(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_deep_copy(item) for item in value]
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str):
        return value
    return value


def _copy_dict(value: object) -> dict[str, object]:
    copied = _deep_copy(value)
    return copied if isinstance(copied, dict) else {}


_CPP_DEFAULT_OPTIONS: dict[str, dict[str, CompilerOptionScalar]] = {
    "lower": {},
    "optimizer": {},
    "emitter": {
        "negative_index_mode": "const_only",
        "bounds_check_mode": "off",
        "floor_div_mode": "native",
        "mod_mode": "native",
    },
}

_CPP_OPTION_SCHEMA: dict[str, dict[str, dict[str, object]]] = {
    "lower": {},
    "optimizer": {},
    "emitter": {
        "negative_index_mode": {"type": "str", "choices": ["always", "const_only", "off"]},
        "bounds_check_mode": {"type": "str", "choices": ["off", "always", "debug"]},
        "floor_div_mode": {"type": "str", "choices": ["native", "python"]},
        "mod_mode": {"type": "str", "choices": ["native", "python"]},
    },
}

_PROGRAM_WRITER_REFS: dict[str, str] = {
    "single_file": "backends.common.program_writer:write_single_file_program",
    "cpp": "backends.cpp.program_writer:write_cpp_program",
}

_RUNTIME_HOOK_DESCRIPTORS: dict[str, RuntimeHookDescriptor] = {
    "none": {"kind": "none"},
    "js_shims": {"kind": "js_shims"},
    "rs": {
        "kind": "copy_files",
        "files": [
            ("runtime/rs/native/built_in/py_runtime.rs", "py_runtime.rs"),
            ("runtime/rs/generated/utils/image_runtime.rs", "image_runtime.rs"),
        ],
    },
    "go": {
        "kind": "copy_files",
        "files": [
            ("runtime/go/native/built_in/py_runtime.go", "py_runtime.go"),
            ("runtime/go/generated/utils/png.go", "png.go"),
            ("runtime/go/generated/utils/gif.go", "gif.go"),
        ],
    },
    "java": {
        "kind": "copy_files",
        "files": [
            ("runtime/java/native/built_in/PyRuntime.java", "PyRuntime.java"),
            ("runtime/java/native/std/time_impl.java", "_impl.java"),
            ("runtime/java/native/std/math_impl.java", "_m.java"),
            ("runtime/java/generated/utils/png.java", "png.java"),
            ("runtime/java/generated/utils/gif.java", "gif.java"),
            ("runtime/java/generated/std/time.java", "time.java"),
            ("runtime/java/generated/std/json.java", "json.java"),
            ("runtime/java/generated/std/pathlib.java", "pathlib.java"),
            ("runtime/java/generated/std/math.java", "math.java"),
        ],
    },
    "kotlin": {
        "kind": "copy_files",
        "files": [
            ("runtime/kotlin/native/built_in/py_runtime.kt", "py_runtime.kt"),
            ("runtime/kotlin/generated/utils/image_runtime.kt", "image_runtime.kt"),
        ],
    },
    "swift": {
        "kind": "copy_files",
        "files": [
            ("runtime/swift/native/built_in/py_runtime.swift", "py_runtime.swift"),
            ("runtime/swift/generated/utils/image_runtime.swift", "image_runtime.swift"),
        ],
    },
    "ruby": {
        "kind": "copy_files",
        "files": [
            ("runtime/ruby/pytra-core/built_in/py_runtime.rb", "py_runtime.rb"),
            ("runtime/ruby/pytra-gen/utils/image_runtime.rb", "image_runtime.rb"),
        ],
    },
    "lua": {
        "kind": "copy_files",
        "files": [
            ("runtime/lua/pytra-core/built_in/py_runtime.lua", "py_runtime.lua"),
            ("runtime/lua/pytra-gen/utils/image_runtime.lua", "image_runtime.lua"),
        ],
    },
    "scala": {
        "kind": "copy_files",
        "files": [
            ("runtime/scala/native/built_in/py_runtime.scala", "py_runtime.scala"),
            ("runtime/scala/generated/utils/image_runtime.scala", "image_runtime.scala"),
        ],
    },
    "php": {
        "kind": "php_runtime",
        "files": [
            ("pytra-core/py_runtime.php", "py_runtime.php"),
            ("pytra-core/std/time.php", "std/time.php"),
            ("pytra-gen/runtime/png.php", "runtime/png.php"),
            ("pytra-gen/runtime/gif.php", "runtime/gif.php"),
        ],
    },
    "nim": {
        "kind": "copy_files",
        "files": [
            ("runtime/nim/native/built_in/py_runtime.nim", "py_runtime.nim"),
            ("runtime/nim/generated/utils/image_runtime.nim", "image_runtime.nim"),
        ],
    },
}

_BACKEND_TARGET_ORDER: tuple[str, ...] = (
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
)

_BACKEND_DESCRIPTORS: dict[str, BackendDescriptor] = {
    "cpp": {
        "target_lang": "cpp",
        "extension": ".cpp",
        "lower_ref": "",
        "optimizer_ref": "",
        "emit_kind": "cpp",
        "emit_ref": "backends.cpp.emitter:transpile_to_cpp",
        "runtime_hook_key": "none",
        "program_writer_key": "cpp",
        "default_options": _CPP_DEFAULT_OPTIONS,
        "option_schema": _CPP_OPTION_SCHEMA,
    },
    "rs": {
        "target_lang": "rs",
        "extension": ".rs",
        "lower_ref": "backends.rs.lower:lower_east3_to_rs_ir",
        "optimizer_ref": "backends.rs.optimizer:optimize_rs_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.rs.emitter.rs_emitter:transpile_to_rust",
        "runtime_hook_key": "rs",
    },
    "cs": {
        "target_lang": "cs",
        "extension": ".cs",
        "lower_ref": "backends.cs.lower:lower_east3_to_cs_ir",
        "optimizer_ref": "backends.cs.optimizer:optimize_cs_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.cs.emitter.cs_emitter:transpile_to_csharp",
        "runtime_hook_key": "none",
    },
    "js": {
        "target_lang": "js",
        "extension": ".js",
        "lower_ref": "backends.js.lower:lower_east3_to_js_ir",
        "optimizer_ref": "backends.js.optimizer:optimize_js_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.js.emitter.js_emitter:transpile_to_js",
        "runtime_hook_key": "js_shims",
    },
    "ts": {
        "target_lang": "ts",
        "extension": ".ts",
        "lower_ref": "backends.ts.lower:lower_east3_to_ts_ir",
        "optimizer_ref": "backends.ts.optimizer:optimize_ts_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.ts.emitter.ts_emitter:transpile_to_typescript",
        "runtime_hook_key": "js_shims",
    },
    "go": {
        "target_lang": "go",
        "extension": ".go",
        "lower_ref": "backends.go.lower:lower_east3_to_go_ir",
        "optimizer_ref": "backends.go.optimizer:optimize_go_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.go.emitter:transpile_to_go_native",
        "runtime_hook_key": "go",
    },
    "java": {
        "target_lang": "java",
        "extension": ".java",
        "lower_ref": "backends.java.lower:lower_east3_to_java_ir",
        "optimizer_ref": "backends.java.optimizer:optimize_java_ir",
        "emit_kind": "java",
        "emit_ref": "backends.java.emitter:transpile_to_java_native",
        "runtime_hook_key": "java",
    },
    "kotlin": {
        "target_lang": "kotlin",
        "extension": ".kt",
        "lower_ref": "backends.kotlin.lower:lower_east3_to_kotlin_ir",
        "optimizer_ref": "backends.kotlin.optimizer:optimize_kotlin_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.kotlin.emitter:transpile_to_kotlin_native",
        "runtime_hook_key": "kotlin",
    },
    "swift": {
        "target_lang": "swift",
        "extension": ".swift",
        "lower_ref": "backends.swift.lower:lower_east3_to_swift_ir",
        "optimizer_ref": "backends.swift.optimizer:optimize_swift_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.swift.emitter:transpile_to_swift_native",
        "runtime_hook_key": "swift",
    },
    "ruby": {
        "target_lang": "ruby",
        "extension": ".rb",
        "lower_ref": "backends.ruby.lower:lower_east3_to_ruby_ir",
        "optimizer_ref": "backends.ruby.optimizer:optimize_ruby_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.ruby.emitter:transpile_to_ruby_native",
        "runtime_hook_key": "ruby",
    },
    "lua": {
        "target_lang": "lua",
        "extension": ".lua",
        "lower_ref": "backends.lua.lower:lower_east3_to_lua_ir",
        "optimizer_ref": "backends.lua.optimizer:optimize_lua_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.lua.emitter:transpile_to_lua_native",
        "runtime_hook_key": "lua",
    },
    "scala": {
        "target_lang": "scala",
        "extension": ".scala",
        "lower_ref": "backends.scala.lower:lower_east3_to_scala_ir",
        "optimizer_ref": "backends.scala.optimizer:optimize_scala_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.scala.emitter:transpile_to_scala_native",
        "runtime_hook_key": "scala",
    },
    "php": {
        "target_lang": "php",
        "extension": ".php",
        "lower_ref": "backends.php.lower:lower_east3_to_php_ir",
        "optimizer_ref": "backends.php.optimizer:optimize_php_ir",
        "emit_kind": "unary",
        "emit_ref": "backends.php.emitter:transpile_to_php_native",
        "runtime_hook_key": "php",
    },
    "nim": {
        "target_lang": "nim",
        "extension": ".nim",
        "lower_ref": "",
        "optimizer_ref": "",
        "emit_kind": "unary",
        "emit_ref": "backends.nim.emitter:transpile_to_nim_native",
        "runtime_hook_key": "nim",
    },
}


def list_backend_targets() -> list[str]:
    return list(_BACKEND_TARGET_ORDER)


def backend_target_order() -> tuple[str, ...]:
    return tuple(_BACKEND_TARGET_ORDER)


def get_backend_descriptor(target: str) -> BackendDescriptor:
    descriptor = _BACKEND_DESCRIPTORS.get(target)
    if descriptor is None:
        raise RuntimeError(unsupported_target_message(target))
    return _copy_dict(descriptor)


def build_backend_spec_metadata(target: str) -> dict[str, object]:
    descriptor = get_backend_descriptor(target)
    out: dict[str, object] = {
        "target_lang": str(descriptor.get("target_lang", "")),
        "extension": str(descriptor.get("extension", "")),
    }
    default_options = descriptor.get("default_options")
    if isinstance(default_options, dict) and len(default_options) > 0:
        out["default_options"] = _copy_dict(default_options)
    option_schema = descriptor.get("option_schema")
    if isinstance(option_schema, dict) and len(option_schema) > 0:
        out["option_schema"] = _copy_dict(option_schema)
    return out


def get_backend_metadata(target: str) -> dict[str, object]:
    return build_backend_spec_metadata(target)


def build_backend_spec_row(
    target: str,
    *,
    lower: object,
    optimizer: object,
    emit: object,
    runtime_hook: object,
    program_writer: object | None = None,
) -> dict[str, object]:
    out = build_backend_spec_metadata(target)
    out["lower"] = lower
    out["optimizer"] = optimizer
    out["emit"] = emit
    out["runtime_hook"] = runtime_hook
    if program_writer is not None:
        out["program_writer"] = program_writer
    return out


def get_backend_lower_ref(target: str) -> str:
    return str(get_backend_descriptor(target).get("lower_ref", ""))


def get_backend_optimizer_ref(target: str) -> str:
    return str(get_backend_descriptor(target).get("optimizer_ref", ""))


def get_backend_emit_kind(target: str) -> str:
    return str(get_backend_descriptor(target).get("emit_kind", ""))


def get_backend_emit_ref(target: str) -> str:
    return str(get_backend_descriptor(target).get("emit_ref", ""))


def get_backend_runtime_hook_key(target: str) -> str:
    return str(get_backend_descriptor(target).get("runtime_hook_key", "none"))


def get_backend_program_writer_key(target: str) -> str:
    return str(get_backend_descriptor(target).get("program_writer_key", ""))


def get_runtime_hook_descriptor(runtime_key: str) -> RuntimeHookDescriptor:
    descriptor = _RUNTIME_HOOK_DESCRIPTORS.get(runtime_key)
    if descriptor is None:
        raise RuntimeError(unsupported_runtime_hook_key_message(runtime_key))
    return _copy_dict(descriptor)


def get_program_writer_ref(writer_key: str) -> str:
    ref = _PROGRAM_WRITER_REFS.get(writer_key)
    if ref is None:
        raise RuntimeError(unsupported_program_writer_key_message(writer_key))
    return ref

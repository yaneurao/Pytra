"""Current inventory for multilang @extern runtime/emitter realignment."""

from __future__ import annotations

from typing import Final, TypedDict


MODULE_ORDER: Final[tuple[str, ...]] = (
    "std/math",
    "std/time",
    "std/os",
    "std/os_path",
    "std/sys",
    "std/glob",
    "built_in/io_ops",
    "built_in/scalar_ops",
)

BUCKET_ORDER: Final[tuple[str, ...]] = ("stdlib", "built_in")


class ExternRuntimeRealignEntry(TypedDict):
    module_id: str
    bucket: str
    source_rel: str
    manifest_postprocess_targets: tuple[str, ...]
    cpp_native_owner_paths: tuple[str, ...]
    noncpp_native_owner_paths: tuple[str, ...]
    emitter_hardcode_needles: tuple[tuple[str, str], ...]
    generated_drift_needles: tuple[tuple[str, str], ...]


MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1: Final[tuple[ExternRuntimeRealignEntry, ...]] = (
    {
        "module_id": "std/math",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/math.py",
        "manifest_postprocess_targets": (
            "rs:rs_std_math_live_wrapper",
            "cs:cs_std_math_live_wrapper",
            "go:go_program_to_library",
            "java:java_std_math_live_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_math_live_wrapper",
            "ts:ts_std_math_live_wrapper",
            "php:php_std_math_live_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/math.cpp",),
        "noncpp_native_owner_paths": ("src/runtime/cs/native/std/math_native.cs",),
        "emitter_hardcode_needles": (
            ("src/backends/go/emitter/go_native_emitter.py", 'return _runtime_module_id(expr) == "pytra.std.math"'),
            ("src/backends/kotlin/emitter/kotlin_native_emitter.py", 'return _runtime_module_id(expr) == "pytra.std.math"'),
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.math":'),
            ("src/backends/nim/emitter/nim_native_emitter.py", 'return _runtime_module_id(expr) == "pytra.std.math"'),
            ("src/backends/php/emitter/php_native_emitter.py", 'if _runtime_module_id(expr) != "pytra.std.math":'),
            ("src/backends/ruby/emitter/ruby_native_emitter.py", 'if _runtime_module_id(expr) != "pytra.std.math":'),
            ("src/backends/scala/emitter/scala_native_emitter.py", 'if runtime_module == "pytra.std.math" and runtime_symbol != ""'),
            ("src/backends/swift/emitter/swift_native_emitter.py", 'return _runtime_module_id(expr) == "pytra.std.math"'),
        ),
        "generated_drift_needles": (
            ("src/runtime/js/generated/std/math.js", "Math.PI"),
            ("src/runtime/ts/generated/std/math.ts", "Math.PI"),
            ("src/runtime/nim/generated/std/math.nim", "Python runtime fallback."),
        ),
    },
    {
        "module_id": "std/time",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/time.py",
        "manifest_postprocess_targets": (
            "rs:rs_std_time_live_wrapper",
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "java:java_std_time_live_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_time_live_wrapper",
            "ts:ts_std_time_live_wrapper",
            "php:php_std_time_live_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/time.cpp",),
        "noncpp_native_owner_paths": ("src/runtime/cs/native/std/time_native.cs",),
        "emitter_hardcode_needles": (
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.time":'),
        ),
        "generated_drift_needles": (
            ("src/runtime/js/generated/std/time.js", "process.hrtime.bigint"),
            ("src/runtime/ts/generated/std/time.ts", "process.hrtime.bigint"),
            ("src/runtime/nim/generated/std/time.nim", "Python runtime fallback."),
        ),
    },
    {
        "module_id": "std/os",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/os.py",
        "manifest_postprocess_targets": (
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_program_to_cjs_module",
            "ts:js_program_to_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/os.cpp",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.os":'),
        ),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/os.rs", "Python runtime fallback."),
        ),
    },
    {
        "module_id": "std/os_path",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/os_path.py",
        "manifest_postprocess_targets": (
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_program_to_cjs_module",
            "ts:js_program_to_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/os_path.cpp",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.os_path":'),
        ),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/os_path.rs", "Python runtime fallback."),
        ),
    },
    {
        "module_id": "std/sys",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/sys.py",
        "manifest_postprocess_targets": (
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_sys_live_wrapper",
            "ts:ts_std_sys_live_wrapper",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/sys.cpp",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.sys":'),
        ),
        "generated_drift_needles": (
            ("src/runtime/js/generated/std/sys.js", "process.argv"),
            ("src/runtime/ts/generated/std/sys.ts", "process.argv"),
        ),
    },
    {
        "module_id": "std/glob",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/glob.py",
        "manifest_postprocess_targets": (
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_program_to_cjs_module",
            "ts:js_program_to_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/glob.cpp",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (
            ("src/backends/lua/emitter/lua_native_emitter.py", 'if mod == "pytra.std.glob":'),
        ),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/glob.rs", "Python runtime fallback."),
        ),
    },
    {
        "module_id": "built_in/io_ops",
        "bucket": "built_in",
        "source_rel": "src/pytra/built_in/io_ops.py",
        "manifest_postprocess_targets": (
            "cs:cs_program_to_helper",
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_ts_built_in_cjs_module",
            "ts:js_ts_built_in_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/built_in/io_ops.h",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
    },
    {
        "module_id": "built_in/scalar_ops",
        "bucket": "built_in",
        "source_rel": "src/pytra/built_in/scalar_ops.py",
        "manifest_postprocess_targets": (
            "cs:cs_program_to_helper",
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_ts_built_in_cjs_module",
            "ts:js_ts_built_in_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/built_in/scalar_ops.h",),
        "noncpp_native_owner_paths": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
    },
)


def iter_multilang_extern_runtime_realign_inventory() -> tuple[ExternRuntimeRealignEntry, ...]:
    return MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1

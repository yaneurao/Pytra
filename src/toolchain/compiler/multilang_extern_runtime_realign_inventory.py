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
    representative_smoke_needles: tuple[tuple[str, str], ...]


MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1: Final[tuple[ExternRuntimeRealignEntry, ...]] = (
    {
        "module_id": "std/math",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/math.py",
        "manifest_postprocess_targets": (
            "rs:rs_std_math_live_wrapper",
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "java:java_std_native_owner_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_native_owner_wrapper",
            "ts:ts_std_native_owner_wrapper",
            "php:php_std_math_live_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/math.cpp",),
        "noncpp_native_owner_paths": (
            "src/runtime/cs/native/std/math_native.cs",
            "src/runtime/java/native/std/math_native.java",
            "src/runtime/js/native/std/math_native.js",
            "src/runtime/ts/native/std/math_native.ts",
        ),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/nim/generated/std/math.nim", "Python runtime fallback."),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/cs/test_py2cs_smoke.py",
                "def test_representative_math_import_fixture_transpiles",
            ),
            (
                "test/unit/backends/go/test_py2go_smoke.py",
                "def test_go_native_emitter_routes_math_calls_via_runtime_helpers",
            ),
            (
                "test/unit/backends/java/test_py2java_smoke.py",
                "def test_java_generated_math_runtime_owner_is_live_wrapper_shaped",
            ),
            (
                "test/unit/backends/rs/test_py2rs_smoke.py",
                "def test_runtime_scaffold_exposes_pytra_std_time_and_math",
            ),
        ),
    },
    {
        "module_id": "std/time",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/time.py",
        "manifest_postprocess_targets": (
            "rs:rs_perf_counter_runtime_wrapper",
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "java:java_std_native_owner_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_perf_counter_host_wrapper",
            "ts:ts_perf_counter_host_wrapper",
            "php:php_perf_counter_host_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/native/std/time.cpp",),
        "noncpp_native_owner_paths": (
            "src/runtime/cs/native/std/time_native.cs",
            "src/runtime/java/native/std/time_native.java",
            "src/runtime/js/native/std/time_native.js",
            "src/runtime/ts/native/std/time_native.ts",
        ),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/nim/generated/std/time.nim", "Python runtime fallback."),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/cs/test_py2cs_smoke.py",
                "def test_representative_time_import_fixture_transpiles",
            ),
            (
                "test/unit/backends/java/test_py2java_smoke.py",
                "def test_java_native_emitter_routes_perf_counter_via_runtime_helper",
            ),
            (
                "test/unit/backends/rs/test_py2rs_smoke.py",
                "def test_generated_time_and_math_runtime_hook_modules_compile_with_scaffold",
            ),
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
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/os.rs", "Python runtime fallback."),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "test/unit/backends/php/test_py2php_smoke.py",
                "def test_php_runtime_source_path_is_migrated",
            ),
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
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/os_path.rs", "Python runtime fallback."),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "test/unit/backends/js/test_py2js_smoke.py",
                "def test_stdlib_imports_use_runtime_bundle_paths",
            ),
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
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/js/generated/std/sys.js", "process.argv"),
            ("src/runtime/ts/generated/std/sys.ts", "process.argv"),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/cs/test_py2cs_smoke.py",
                "def test_representative_sys_extended_fixture_transpiles",
            ),
            (
                "test/unit/backends/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
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
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (
            ("src/runtime/rs/generated/std/glob.rs", "Python runtime fallback."),
        ),
        "representative_smoke_needles": (
            (
                "test/unit/backends/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "test/unit/backends/ts/test_py2ts_smoke.py",
                "def test_stdlib_imports_use_runtime_bundle_paths",
            ),
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
        "representative_smoke_needles": (
            (
                "test/unit/backends/go/test_py2go_smoke.py",
                "def test_go_generated_built_in_compare_lane_compiles_with_runtime_bundle",
            ),
            (
                "test/unit/backends/kotlin/test_py2kotlin_smoke.py",
                "def test_kotlin_generated_built_in_compare_lane_compiles_with_runtime_bundle",
            ),
        ),
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
        "representative_smoke_needles": (
            (
                "test/unit/backends/scala/test_py2scala_smoke.py",
                "def test_scala_generated_built_in_compare_lane_is_materialized",
            ),
            (
                "test/unit/backends/swift/test_py2swift_smoke.py",
                "def test_swift_generated_built_in_compare_lane_compiles_with_runtime_bundle",
            ),
        ),
    },
)


def iter_multilang_extern_runtime_realign_inventory() -> tuple[ExternRuntimeRealignEntry, ...]:
    return MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1

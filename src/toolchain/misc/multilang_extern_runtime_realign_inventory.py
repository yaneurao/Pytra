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
NONCPP_OWNERSHIP_MODE_ORDER: Final[tuple[str, ...]] = (
    "native_owner",
    "generated_compare_only",
)


class ExternRuntimeRealignEntry(TypedDict):
    module_id: str
    bucket: str
    source_rel: str
    manifest_postprocess_targets: tuple[str, ...]
    cpp_native_owner_paths: tuple[str, ...]
    noncpp_ownership_mode: str
    noncpp_native_owner_paths: tuple[str, ...]
    accepted_generated_compare_residual_targets: tuple[str, ...]
    emitter_hardcode_needles: tuple[tuple[str, str], ...]
    generated_drift_needles: tuple[tuple[str, str], ...]
    representative_smoke_needles: tuple[tuple[str, str], ...]


MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1: Final[tuple[ExternRuntimeRealignEntry, ...]] = (
    {
        "module_id": "std/math",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/math.py",
        "manifest_postprocess_targets": (
            "rs:rs_std_native_owner_wrapper",
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "java:java_std_native_owner_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_native_owner_wrapper",
            "ts:ts_std_native_owner_wrapper",
            "php:php_std_native_owner_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/std/math.cpp",),
        "noncpp_ownership_mode": "native_owner",
        "noncpp_native_owner_paths": (
            "src/runtime/rs/std/math_native.rs",
            "src/runtime/cs/std/math_native.cs",
            "src/runtime/java/std/math_native.java",
            "src/runtime/js/std/math_native.js",
            "src/runtime/ts/std/math_native.ts",
            "src/runtime/php/std/math_native.php",
        ),
        "accepted_generated_compare_residual_targets": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/cs/test_py2cs_smoke.py",
                "def test_representative_math_import_fixture_transpiles",
            ),
            (
                "tools/unittest/emit/go/test_py2go_smoke.py",
                "def test_go_native_emitter_routes_math_calls_via_runtime_helpers",
            ),
            (
                "tools/unittest/emit/java/test_py2java_smoke.py",
                "def test_java_generated_math_runtime_owner_is_live_wrapper_shaped",
            ),
            (
                "tools/unittest/emit/php/test_py2php_smoke.py",
                "def test_php_generated_math_runtime_owner_is_live_wrapper_shaped",
            ),
            (
                "tools/unittest/emit/rs/test_py2rs_smoke.py",
                "def test_runtime_scaffold_exposes_pytra_std_time_and_math",
            ),
        ),
    },
    {
        "module_id": "std/time",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/time.py",
        "manifest_postprocess_targets": (
            "rs:rs_std_native_owner_wrapper",
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "java:java_std_native_owner_wrapper",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_std_native_owner_wrapper",
            "ts:ts_std_native_owner_wrapper",
            "php:php_std_native_owner_wrapper",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/std/time.cpp",),
        "noncpp_ownership_mode": "native_owner",
        "noncpp_native_owner_paths": (
            "src/runtime/rs/std/time_native.rs",
            "src/runtime/cs/std/time_native.cs",
            "src/runtime/java/std/time_native.java",
            "src/runtime/js/std/time_native.js",
            "src/runtime/ts/std/time_native.ts",
            "src/runtime/php/std/time_native.php",
        ),
        "accepted_generated_compare_residual_targets": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/cs/test_py2cs_smoke.py",
                "def test_representative_time_import_fixture_transpiles",
            ),
            (
                "tools/unittest/emit/java/test_py2java_smoke.py",
                "def test_java_native_emitter_routes_perf_counter_via_runtime_helper",
            ),
            (
                "tools/unittest/emit/php/test_py2php_smoke.py",
                "def test_php_generated_time_runtime_owner_is_live_wrapper_shaped",
            ),
            (
                "tools/unittest/emit/rs/test_py2rs_smoke.py",
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
        "cpp_native_owner_paths": ("src/runtime/cpp/std/os.cpp",),
        "noncpp_ownership_mode": "generated_compare_only",
        "noncpp_native_owner_paths": (),
        "accepted_generated_compare_residual_targets": ("rs",),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "tools/unittest/emit/php/test_py2php_smoke.py",
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
        "cpp_native_owner_paths": ("src/runtime/cpp/std/os_path.cpp",),
        "noncpp_ownership_mode": "generated_compare_only",
        "noncpp_native_owner_paths": (),
        "accepted_generated_compare_residual_targets": ("rs",),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "tools/unittest/emit/js/test_py2js_smoke.py",
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
            "js:js_std_native_owner_wrapper",
            "ts:ts_std_native_owner_wrapper",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/std/sys.cpp",),
        "noncpp_ownership_mode": "native_owner",
        "noncpp_native_owner_paths": (
            "src/runtime/js/std/sys_native.js",
            "src/runtime/ts/std/sys_native.ts",
        ),
        "accepted_generated_compare_residual_targets": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/cs/test_py2cs_smoke.py",
                "def test_representative_sys_extended_fixture_transpiles",
            ),
            (
                "tools/unittest/emit/js/test_py2js_smoke.py",
                "def test_js_generated_sys_runtime_wrapper_delegates_to_native_owner",
            ),
            (
                "tools/unittest/emit/ts/test_py2ts_smoke.py",
                "def test_ts_generated_sys_runtime_wrapper_delegates_to_native_owner",
            ),
            (
                "tools/unittest/emit/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
        ),
    },
    {
        "module_id": "std/glob",
        "bucket": "stdlib",
        "source_rel": "src/pytra/std/glob.py",
        "manifest_postprocess_targets": (
            "cs:cs_std_native_owner_wrapper",
            "go:go_program_to_library",
            "kotlin:kotlin_program_to_library",
            "scala:scala_program_to_library",
            "swift:swift_program_to_library",
            "js:js_program_to_cjs_module",
            "ts:js_program_to_cjs_module",
            "php:php_program_to_library",
        ),
        "cpp_native_owner_paths": ("src/runtime/cpp/std/glob.cpp",),
        "noncpp_ownership_mode": "native_owner",
        "noncpp_native_owner_paths": ("src/runtime/cs/std/glob_native.cs",),
        "accepted_generated_compare_residual_targets": ("rs",),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/lua/test_py2lua_smoke.py",
                "def test_import_lowering_maps_os_sys_glob_runtime_via_generic_extern_metadata",
            ),
            (
                "tools/unittest/emit/ts/test_py2ts_smoke.py",
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
        "cpp_native_owner_paths": ("src/runtime/cpp/built_in/io_ops.h",),
        "noncpp_ownership_mode": "generated_compare_only",
        "noncpp_native_owner_paths": (),
        "accepted_generated_compare_residual_targets": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/go/test_py2go_smoke.py",
                "def test_go_generated_built_in_compare_lane_compiles_with_runtime_bundle",
            ),
            (
                "tools/unittest/emit/kotlin/test_py2kotlin_smoke.py",
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
        "cpp_native_owner_paths": ("src/runtime/cpp/built_in/scalar_ops.h",),
        "noncpp_ownership_mode": "generated_compare_only",
        "noncpp_native_owner_paths": (),
        "accepted_generated_compare_residual_targets": (),
        "emitter_hardcode_needles": (),
        "generated_drift_needles": (),
        "representative_smoke_needles": (
            (
                "tools/unittest/emit/scala/test_py2scala_smoke.py",
                "def test_scala_generated_built_in_compare_lane_is_materialized",
            ),
            (
                "tools/unittest/emit/swift/test_py2swift_smoke.py",
                "def test_swift_generated_built_in_compare_lane_compiles_with_runtime_bundle",
            ),
        ),
    },
)


def iter_multilang_extern_runtime_realign_inventory() -> tuple[ExternRuntimeRealignEntry, ...]:
    return MULTILANG_EXTERN_RUNTIME_REALIGN_INVENTORY_V1

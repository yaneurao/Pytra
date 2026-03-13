"""Canonical non-C++ generated runtime baseline derived from cpp/generated."""

from __future__ import annotations

from typing import Final, TypedDict


class NonCppRuntimeGeneratedCppBaselineBucketEntry(TypedDict):
    bucket: str
    modules: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineLegacyStateEntry(TypedDict):
    backend: str
    legacy_state: str
    modules: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineLegacyPolicyFileEntry(TypedDict):
    path: str
    required_needle: str


class NonCppRuntimeGeneratedCppBaselineActivePolicyDocEntry(TypedDict):
    path: str
    required_needles: tuple[str, ...]
    forbidden_needles: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineBuildProfileEntry(TypedDict):
    backend: str
    wiring_mode: str
    runtime_refs: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineSmokeEntry(TypedDict):
    backend: str
    test_path: str
    required_tests: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineRuntimeFileInventoryEntry(TypedDict):
    backend: str
    generated_files: tuple[str, ...]
    native_files: tuple[str, ...]
    compat_files: tuple[str, ...]


NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKET_ORDER_V1: Final[tuple[str, ...]] = (
    "built_in",
    "std",
    "utils",
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUILT_IN_MODULES_V1: Final[tuple[str, ...]] = (
    "contains",
    "io_ops",
    "iter_ops",
    "numeric_ops",
    "predicates",
    "scalar_ops",
    "sequence",
    "string_ops",
    "type_id",
    "zip_ops",
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_STD_MODULES_V1: Final[tuple[str, ...]] = (
    "argparse",
    "glob",
    "json",
    "math",
    "os",
    "os_path",
    "pathlib",
    "random",
    "re",
    "sys",
    "time",
    "timeit",
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_UTILS_MODULES_V1: Final[tuple[str, ...]] = (
    "assertions",
    "gif",
    "png",
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKETS_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineBucketEntry, ...]
] = (
    {
        "bucket": "built_in",
        "modules": NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUILT_IN_MODULES_V1,
    },
    {
        "bucket": "std",
        "modules": NONCPP_RUNTIME_GENERATED_CPP_BASELINE_STD_MODULES_V1,
    },
    {
        "bucket": "utils",
        "modules": NONCPP_RUNTIME_GENERATED_CPP_BASELINE_UTILS_MODULES_V1,
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MODULES_V1: Final[tuple[str, ...]] = tuple(
    f"{entry['bucket']}/{module}"
    for entry in NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKETS_V1
    for module in entry["modules"]
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_FORBIDDEN_LEGACY_STATES_V1: Final[
    tuple[str, ...]
] = (
    "blocked",
    "compare_artifact",
    "no_runtime_module",
    "native_canonical",
    "helper_artifact",
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LEGACY_STATE_BUCKETS_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineLegacyStateEntry, ...]
] = (
    {
        "backend": "cs",
        "legacy_state": "compare_artifact",
        "modules": (
            "std/argparse",
            "std/random",
            "std/re",
            "std/sys",
            "std/timeit",
        ),
    },
    {
        "backend": "rs",
        "legacy_state": "compare_artifact",
        "modules": (
            "std/argparse",
            "std/glob",
            "std/json",
            "std/math",
            "std/os",
            "std/os_path",
            "std/pathlib",
            "std/random",
            "std/re",
            "std/sys",
            "std/time",
            "std/timeit",
        ),
    },
    {
        "backend": "rs",
        "legacy_state": "native_canonical",
        "modules": ("std/math", "std/time"),
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_OVERLAP_V1: Final[
    tuple[str, ...]
] = ()

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MATERIALIZED_BACKENDS_V1: Final[
    tuple[str, ...]
] = ("cs", "go", "java", "rs", "swift", "nim", "kotlin", "scala", "js", "ts", "lua", "ruby", "php")

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LOCAL_RUNTIME_FILE_INVENTORY_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineRuntimeFileInventoryEntry, ...]
] = (
    {
        "backend": "cs",
        "generated_files": (
            "generated/built_in/contains.cs",
            "generated/built_in/io_ops.cs",
            "generated/built_in/iter_ops.cs",
            "generated/built_in/numeric_ops.cs",
            "generated/built_in/predicates.cs",
            "generated/built_in/scalar_ops.cs",
            "generated/built_in/sequence.cs",
            "generated/built_in/string_ops.cs",
            "generated/built_in/type_id.cs",
            "generated/built_in/zip_ops.cs",
            "generated/std/argparse.cs",
            "generated/std/glob.cs",
            "generated/std/json.cs",
            "generated/std/math.cs",
            "generated/std/os.cs",
            "generated/std/os_path.cs",
            "generated/std/pathlib.cs",
            "generated/std/random.cs",
            "generated/std/re.cs",
            "generated/std/sys.cs",
            "generated/std/time.cs",
            "generated/std/timeit.cs",
            "generated/utils/assertions.cs",
            "generated/utils/gif.cs",
            "generated/utils/png.cs",
        ),
        "native_files": (
            "native/built_in/py_runtime.cs",
            "native/std/time_native.cs",
        ),
        "compat_files": (),
    },
    {
        "backend": "rs",
        "generated_files": (
            "generated/built_in/contains.rs",
            "generated/built_in/io_ops.rs",
            "generated/built_in/iter_ops.rs",
            "generated/built_in/numeric_ops.rs",
            "generated/built_in/predicates.rs",
            "generated/built_in/scalar_ops.rs",
            "generated/built_in/sequence.rs",
            "generated/built_in/string_ops.rs",
            "generated/built_in/type_id.rs",
            "generated/built_in/zip_ops.rs",
            "generated/std/argparse.rs",
            "generated/std/glob.rs",
            "generated/std/json.rs",
            "generated/std/math.rs",
            "generated/std/os.rs",
            "generated/std/os_path.rs",
            "generated/std/pathlib.rs",
            "generated/std/random.rs",
            "generated/std/re.rs",
            "generated/std/sys.rs",
            "generated/std/time.rs",
            "generated/std/timeit.rs",
            "generated/utils/assertions.rs",
            "generated/utils/gif.rs",
            "generated/utils/image_runtime.rs",
            "generated/utils/png.rs",
        ),
        "native_files": ("native/built_in/py_runtime.rs",),
        "compat_files": ("pytra/README.md", "pytra/built_in/py_runtime.rs"),
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LEGACY_POLICY_FILES_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineLegacyPolicyFileEntry, ...]
] = (
    {
        "path": "src/toolchain/compiler/noncpp_runtime_layout_contract.py",
        "required_needle": "Legacy",
    },
    {
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "required_needle": "Legacy",
    },
    {
        "path": "tools/check_noncpp_runtime_layout_contract.py",
        "required_needle": "Legacy",
    },
    {
        "path": "tools/check_noncpp_runtime_layout_rollout_remaining_contract.py",
        "required_needle": "Legacy",
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_ACTIVE_POLICY_DOCS_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineActivePolicyDocEntry, ...]
] = (
    {
        "path": "docs/ja/spec/spec-runtime.md",
        "required_needles": (
            "`generated = baseline`",
            "legacy inventory",
        ),
        "forbidden_needles": (
            "rollout 済み backend（現行: `cpp`, `rs`, `cs`）",
        ),
    },
    {
        "path": "docs/en/spec/spec-runtime.md",
        "required_needles": (
            "`generated = baseline`",
            "legacy inventory",
        ),
        "forbidden_needles": (
            "backends that already completed the rollout (`cpp`, `rs`, `cs`)",
        ),
    },
    {
        "path": "docs/ja/spec/spec-tools.md",
        "required_needles": (
            "tools/check_noncpp_runtime_generated_cpp_baseline_contract.py",
            "tools/export_backend_test_matrix.py",
        ),
        "forbidden_needles": (),
    },
    {
        "path": "docs/en/spec/spec-tools.md",
        "required_needles": (
            "tools/check_noncpp_runtime_generated_cpp_baseline_contract.py",
            "tools/export_backend_test_matrix.py",
        ),
        "forbidden_needles": (),
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUILD_PROFILES_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineBuildProfileEntry, ...]
] = (
    {
        "backend": "cs",
        "wiring_mode": "repo_runtime_bundle_residual",
        "runtime_refs": (
            "src/runtime/cs/native/built_in/py_runtime.cs",
            "src/runtime/cs/generated/std/time.cs",
            "src/runtime/cs/native/std/time_native.cs",
            "src/runtime/cs/generated/std/math.cs",
            "src/runtime/cs/generated/std/json.cs",
            "src/runtime/cs/generated/std/pathlib.cs",
            "src/runtime/cs/generated/utils/png.cs",
            "src/runtime/cs/generated/utils/gif.cs",
        ),
    },
    {
        "backend": "go",
        "wiring_mode": "staged_output_runtime_bundle",
        "runtime_refs": ("out/py_runtime.go", "out/png.go", "out/gif.go"),
    },
    {
        "backend": "java",
        "wiring_mode": "staged_output_runtime_bundle",
        "runtime_refs": ("out/PyRuntime.java", "out/png.java", "out/gif.java"),
    },
    {
        "backend": "swift",
        "wiring_mode": "staged_output_runtime_bundle",
        "runtime_refs": ("out/py_runtime.swift", "out/image_runtime.swift"),
    },
    {
        "backend": "kotlin",
        "wiring_mode": "staged_output_runtime_bundle",
        "runtime_refs": ("out/py_runtime.kt", "out/image_runtime.kt"),
    },
    {
        "backend": "scala",
        "wiring_mode": "staged_output_runner_bundle",
        "runtime_refs": ("out/py_runtime.scala", "out/image_runtime.scala"),
    },
    {
        "backend": "nim",
        "wiring_mode": "standalone_compiler_only",
        "runtime_refs": (),
    },
    {
        "backend": "rs",
        "wiring_mode": "standalone_compiler_only",
        "runtime_refs": (),
    },
    {
        "backend": "js",
        "wiring_mode": "direct_script_runner",
        "runtime_refs": (),
    },
    {
        "backend": "ts",
        "wiring_mode": "direct_script_runner",
        "runtime_refs": (),
    },
    {
        "backend": "lua",
        "wiring_mode": "direct_script_runner",
        "runtime_refs": (),
    },
    {
        "backend": "ruby",
        "wiring_mode": "direct_script_runner",
        "runtime_refs": (),
    },
    {
        "backend": "php",
        "wiring_mode": "direct_script_runner",
        "runtime_refs": (),
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_SMOKE_INVENTORY_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineSmokeEntry, ...]
] = (
    {
        "backend": "go",
        "test_path": "test/unit/backends/go/test_py2go_smoke.py",
        "required_tests": (
            "test_go_runtime_source_path_is_migrated",
            "test_go_generated_built_in_compare_lane_compiles_with_runtime_bundle",
        ),
    },
    {
        "backend": "java",
        "test_path": "test/unit/backends/java/test_py2java_smoke.py",
        "required_tests": (
            "test_java_runtime_source_path_is_migrated",
            "test_java_generated_built_in_compare_lane_compiles_with_runtime_bundle",
        ),
    },
    {
        "backend": "kotlin",
        "test_path": "test/unit/backends/kotlin/test_py2kotlin_smoke.py",
        "required_tests": (
            "test_kotlin_runtime_source_path_is_migrated",
            "test_kotlin_generated_built_in_compare_lane_compiles_with_runtime_bundle",
        ),
    },
    {
        "backend": "scala",
        "test_path": "test/unit/backends/scala/test_py2scala_smoke.py",
        "required_tests": (
            "test_scala_runtime_source_path_is_migrated",
            "test_scala_generated_built_in_compare_lane_is_materialized",
        ),
    },
    {
        "backend": "swift",
        "test_path": "test/unit/backends/swift/test_py2swift_smoke.py",
        "required_tests": (
            "test_swift_runtime_source_path_is_migrated",
            "test_swift_generated_built_in_compare_lane_compiles_with_runtime_bundle",
        ),
    },
    {
        "backend": "nim",
        "test_path": "test/unit/backends/nim/test_py2nim_smoke.py",
        "required_tests": (
            "test_nim_runtime_source_path_is_migrated",
            "test_nim_generated_built_in_compare_lane_compiles_with_runtime_bundle",
        ),
    },
    {
        "backend": "js",
        "test_path": "test/unit/backends/js/test_py2js_smoke.py",
        "required_tests": (
            "test_js_repo_compat_lane_resolves_runtime_helpers",
            "test_js_generated_built_in_compare_lane_resolves_native_runtime",
        ),
    },
    {
        "backend": "ts",
        "test_path": "test/unit/backends/ts/test_py2ts_smoke.py",
        "required_tests": (
            "test_ts_repo_compat_lane_reexports_runtime_helpers",
            "test_ts_generated_built_in_compare_lane_rehomes_native_runtime_import",
        ),
    },
    {
        "backend": "lua",
        "test_path": "test/unit/backends/lua/test_py2lua_smoke.py",
        "required_tests": (
            "test_lua_runtime_source_path_is_migrated",
            "test_lua_repo_compat_lane_resolves_runtime_helpers",
        ),
    },
    {
        "backend": "ruby",
        "test_path": "test/unit/backends/rb/test_py2rb_smoke.py",
        "required_tests": (
            "test_ruby_runtime_source_path_is_migrated",
            "test_ruby_repo_compat_lane_resolves_runtime_helpers",
        ),
    },
    {
        "backend": "php",
        "test_path": "test/unit/backends/php/test_py2php_smoke.py",
        "required_tests": (
            "test_php_runtime_source_path_is_migrated",
            "test_php_repo_generated_and_compat_lanes_resolve_native_substrate",
            "test_php_generated_built_in_compare_lane_resolves_native_runtime",
            "test_php_repo_public_compat_lane_resolves_remaining_shims",
        ),
    },
)


def iter_noncpp_runtime_generated_cpp_baseline_bucket_order() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKET_ORDER_V1


def iter_noncpp_runtime_generated_cpp_baseline_buckets() -> tuple[
    NonCppRuntimeGeneratedCppBaselineBucketEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKETS_V1


def iter_noncpp_runtime_generated_cpp_baseline_modules() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MODULES_V1


def iter_noncpp_runtime_generated_cpp_baseline_forbidden_legacy_states() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_FORBIDDEN_LEGACY_STATES_V1


def iter_noncpp_runtime_generated_cpp_baseline_legacy_state_buckets() -> tuple[
    NonCppRuntimeGeneratedCppBaselineLegacyStateEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LEGACY_STATE_BUCKETS_V1


def iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_overlap() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_OVERLAP_V1


def iter_noncpp_runtime_generated_cpp_baseline_materialized_backends() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MATERIALIZED_BACKENDS_V1


def iter_noncpp_runtime_generated_cpp_baseline_local_runtime_file_inventory() -> tuple[
    NonCppRuntimeGeneratedCppBaselineRuntimeFileInventoryEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LOCAL_RUNTIME_FILE_INVENTORY_V1


def iter_noncpp_runtime_generated_cpp_baseline_legacy_policy_files() -> tuple[
    NonCppRuntimeGeneratedCppBaselineLegacyPolicyFileEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LEGACY_POLICY_FILES_V1


def iter_noncpp_runtime_generated_cpp_baseline_active_policy_docs() -> tuple[
    NonCppRuntimeGeneratedCppBaselineActivePolicyDocEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_ACTIVE_POLICY_DOCS_V1


def iter_noncpp_runtime_generated_cpp_baseline_build_profiles() -> tuple[
    NonCppRuntimeGeneratedCppBaselineBuildProfileEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUILD_PROFILES_V1


def iter_noncpp_runtime_generated_cpp_baseline_smoke_inventory() -> tuple[
    NonCppRuntimeGeneratedCppBaselineSmokeEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_SMOKE_INVENTORY_V1

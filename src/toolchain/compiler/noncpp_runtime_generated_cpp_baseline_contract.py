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
    delete_target_files: tuple[str, ...]


class NonCppRuntimeGeneratedCppBaselineHelperArtifactInventoryEntry(TypedDict):
    backend: str
    helper_artifact_modules: tuple[str, ...]


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
            "std/os",
            "std/os_path",
            "std/pathlib",
            "std/random",
            "std/re",
            "std/sys",
            "std/timeit",
        ),
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_OVERLAP_V1: Final[
    tuple[str, ...]
] = ()

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_INVENTORY_V1: Final[
    tuple[NonCppRuntimeGeneratedCppBaselineHelperArtifactInventoryEntry, ...]
] = (
    {"backend": "cs", "helper_artifact_modules": ()},
    {"backend": "go", "helper_artifact_modules": ()},
    {"backend": "java", "helper_artifact_modules": ()},
    {"backend": "rs", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "swift", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "nim", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "kotlin", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "scala", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "js", "helper_artifact_modules": ()},
    {"backend": "ts", "helper_artifact_modules": ()},
    {"backend": "lua", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "ruby", "helper_artifact_modules": ("utils/image_runtime",)},
    {"backend": "php", "helper_artifact_modules": ()},
)

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
            "native/std/glob_native.cs",
            "native/std/math_native.cs",
            "native/std/time_native.cs",
        ),
        "delete_target_files": (),
    },
    {
        "backend": "go",
        "generated_files": (
            "generated/built_in/contains.go",
            "generated/built_in/io_ops.go",
            "generated/built_in/iter_ops.go",
            "generated/built_in/numeric_ops.go",
            "generated/built_in/predicates.go",
            "generated/built_in/scalar_ops.go",
            "generated/built_in/sequence.go",
            "generated/built_in/string_ops.go",
            "generated/built_in/type_id.go",
            "generated/built_in/zip_ops.go",
            "generated/std/argparse.go",
            "generated/std/glob.go",
            "generated/std/json.go",
            "generated/std/math.go",
            "generated/std/os.go",
            "generated/std/os_path.go",
            "generated/std/pathlib.go",
            "generated/std/random.go",
            "generated/std/re.go",
            "generated/std/sys.go",
            "generated/std/time.go",
            "generated/std/timeit.go",
            "generated/utils/assertions.go",
            "generated/utils/gif.go",
            "generated/utils/png.go",
        ),
        "native_files": ("native/built_in/py_runtime.go",),
        "delete_target_files": (),
    },
    {
        "backend": "java",
        "generated_files": (
            "generated/built_in/contains.java",
            "generated/built_in/io_ops.java",
            "generated/built_in/iter_ops.java",
            "generated/built_in/numeric_ops.java",
            "generated/built_in/predicates.java",
            "generated/built_in/scalar_ops.java",
            "generated/built_in/sequence.java",
            "generated/built_in/string_ops.java",
            "generated/built_in/type_id.java",
            "generated/built_in/zip_ops.java",
            "generated/std/argparse.java",
            "generated/std/glob.java",
            "generated/std/json.java",
            "generated/std/math.java",
            "generated/std/os.java",
            "generated/std/os_path.java",
            "generated/std/pathlib.java",
            "generated/std/random.java",
            "generated/std/re.java",
            "generated/std/sys.java",
            "generated/std/time.java",
            "generated/std/timeit.java",
            "generated/utils/assertions.java",
            "generated/utils/gif.java",
            "generated/utils/png.java",
        ),
        "native_files": (
            "native/built_in/PyRuntime.java",
            "native/std/math_native.java",
            "native/std/time_native.java",
        ),
        "delete_target_files": (),
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
        "native_files": ("native/built_in/py_runtime.rs", "native/std/math_native.rs", "native/std/time_native.rs"),
        "delete_target_files": (),
    },
    {
        "backend": "swift",
        "generated_files": (
            "generated/built_in/contains.swift",
            "generated/built_in/io_ops.swift",
            "generated/built_in/iter_ops.swift",
            "generated/built_in/numeric_ops.swift",
            "generated/built_in/predicates.swift",
            "generated/built_in/scalar_ops.swift",
            "generated/built_in/sequence.swift",
            "generated/built_in/string_ops.swift",
            "generated/built_in/type_id.swift",
            "generated/built_in/zip_ops.swift",
            "generated/std/argparse.swift",
            "generated/std/glob.swift",
            "generated/std/json.swift",
            "generated/std/math.swift",
            "generated/std/os.swift",
            "generated/std/os_path.swift",
            "generated/std/pathlib.swift",
            "generated/std/random.swift",
            "generated/std/re.swift",
            "generated/std/sys.swift",
            "generated/std/time.swift",
            "generated/std/timeit.swift",
            "generated/utils/assertions.swift",
            "generated/utils/gif.swift",
            "generated/utils/image_runtime.swift",
            "generated/utils/png.swift",
        ),
        "native_files": ("native/built_in/py_runtime.swift",),
        "delete_target_files": (),
    },
    {
        "backend": "nim",
        "generated_files": (
            "generated/built_in/contains.nim",
            "generated/built_in/io_ops.nim",
            "generated/built_in/iter_ops.nim",
            "generated/built_in/numeric_ops.nim",
            "generated/built_in/predicates.nim",
            "generated/built_in/scalar_ops.nim",
            "generated/built_in/sequence.nim",
            "generated/built_in/string_ops.nim",
            "generated/built_in/type_id.nim",
            "generated/built_in/zip_ops.nim",
            "generated/std/argparse.nim",
            "generated/std/glob.nim",
            "generated/std/json.nim",
            "generated/std/math.nim",
            "generated/std/os.nim",
            "generated/std/os_path.nim",
            "generated/std/pathlib.nim",
            "generated/std/random.nim",
            "generated/std/re.nim",
            "generated/std/sys.nim",
            "generated/std/time.nim",
            "generated/std/timeit.nim",
            "generated/utils/assertions.nim",
            "generated/utils/gif.nim",
            "generated/utils/image_runtime.nim",
            "generated/utils/png.nim",
        ),
        "native_files": ("native/built_in/py_runtime.nim",),
        "delete_target_files": (),
    },
    {
        "backend": "kotlin",
        "generated_files": (
            "generated/built_in/contains.kt",
            "generated/built_in/io_ops.kt",
            "generated/built_in/iter_ops.kt",
            "generated/built_in/numeric_ops.kt",
            "generated/built_in/predicates.kt",
            "generated/built_in/scalar_ops.kt",
            "generated/built_in/sequence.kt",
            "generated/built_in/string_ops.kt",
            "generated/built_in/type_id.kt",
            "generated/built_in/zip_ops.kt",
            "generated/std/argparse.kt",
            "generated/std/glob.kt",
            "generated/std/json.kt",
            "generated/std/math.kt",
            "generated/std/os.kt",
            "generated/std/os_path.kt",
            "generated/std/pathlib.kt",
            "generated/std/random.kt",
            "generated/std/re.kt",
            "generated/std/sys.kt",
            "generated/std/time.kt",
            "generated/std/timeit.kt",
            "generated/utils/assertions.kt",
            "generated/utils/gif.kt",
            "generated/utils/image_runtime.kt",
            "generated/utils/png.kt",
        ),
        "native_files": ("native/built_in/py_runtime.kt",),
        "delete_target_files": (),
    },
    {
        "backend": "scala",
        "generated_files": (
            "generated/built_in/contains.scala",
            "generated/built_in/io_ops.scala",
            "generated/built_in/iter_ops.scala",
            "generated/built_in/numeric_ops.scala",
            "generated/built_in/predicates.scala",
            "generated/built_in/scalar_ops.scala",
            "generated/built_in/sequence.scala",
            "generated/built_in/string_ops.scala",
            "generated/built_in/type_id.scala",
            "generated/built_in/zip_ops.scala",
            "generated/std/argparse.scala",
            "generated/std/glob.scala",
            "generated/std/json.scala",
            "generated/std/math.scala",
            "generated/std/os.scala",
            "generated/std/os_path.scala",
            "generated/std/pathlib.scala",
            "generated/std/random.scala",
            "generated/std/re.scala",
            "generated/std/sys.scala",
            "generated/std/time.scala",
            "generated/std/timeit.scala",
            "generated/utils/assertions.scala",
            "generated/utils/gif.scala",
            "generated/utils/image_runtime.scala",
            "generated/utils/png.scala",
        ),
        "native_files": ("native/built_in/py_runtime.scala",),
        "delete_target_files": (),
    },
    {
        "backend": "js",
        "generated_files": (
            "generated/built_in/contains.js",
            "generated/built_in/io_ops.js",
            "generated/built_in/iter_ops.js",
            "generated/built_in/numeric_ops.js",
            "generated/built_in/predicates.js",
            "generated/built_in/scalar_ops.js",
            "generated/built_in/sequence.js",
            "generated/built_in/string_ops.js",
            "generated/built_in/type_id.js",
            "generated/built_in/zip_ops.js",
            "generated/std/argparse.js",
            "generated/std/glob.js",
            "generated/std/json.js",
            "generated/std/math.js",
            "generated/std/os.js",
            "generated/std/os_path.js",
            "generated/std/pathlib.js",
            "generated/std/random.js",
            "generated/std/re.js",
            "generated/std/sys.js",
            "generated/std/time.js",
            "generated/std/timeit.js",
            "generated/utils/assertions.js",
            "generated/utils/gif.js",
            "generated/utils/png.js",
        ),
        "native_files": (
            "native/built_in/py_runtime.js",
            "native/std/math_native.js",
            "native/std/sys_native.js",
            "native/std/time_native.js",
        ),
        "delete_target_files": (),
    },
    {
        "backend": "ts",
        "generated_files": (
            "generated/built_in/contains.ts",
            "generated/built_in/io_ops.ts",
            "generated/built_in/iter_ops.ts",
            "generated/built_in/numeric_ops.ts",
            "generated/built_in/predicates.ts",
            "generated/built_in/scalar_ops.ts",
            "generated/built_in/sequence.ts",
            "generated/built_in/string_ops.ts",
            "generated/built_in/type_id.ts",
            "generated/built_in/zip_ops.ts",
            "generated/std/argparse.ts",
            "generated/std/glob.ts",
            "generated/std/json.ts",
            "generated/std/math.ts",
            "generated/std/os.ts",
            "generated/std/os_path.ts",
            "generated/std/pathlib.ts",
            "generated/std/random.ts",
            "generated/std/re.ts",
            "generated/std/sys.ts",
            "generated/std/time.ts",
            "generated/std/timeit.ts",
            "generated/utils/assertions.ts",
            "generated/utils/gif.ts",
            "generated/utils/png.ts",
        ),
        "native_files": (
            "native/built_in/py_runtime.ts",
            "native/std/math_native.ts",
            "native/std/sys_native.ts",
            "native/std/time_native.ts",
        ),
        "delete_target_files": (),
    },
    {
        "backend": "lua",
        "generated_files": (
            "generated/built_in/contains.lua",
            "generated/built_in/io_ops.lua",
            "generated/built_in/iter_ops.lua",
            "generated/built_in/numeric_ops.lua",
            "generated/built_in/predicates.lua",
            "generated/built_in/scalar_ops.lua",
            "generated/built_in/sequence.lua",
            "generated/built_in/string_ops.lua",
            "generated/built_in/type_id.lua",
            "generated/built_in/zip_ops.lua",
            "generated/std/argparse.lua",
            "generated/std/glob.lua",
            "generated/std/json.lua",
            "generated/std/math.lua",
            "generated/std/os.lua",
            "generated/std/os_path.lua",
            "generated/std/pathlib.lua",
            "generated/std/random.lua",
            "generated/std/re.lua",
            "generated/std/sys.lua",
            "generated/std/time.lua",
            "generated/std/timeit.lua",
            "generated/utils/assertions.lua",
            "generated/utils/gif.lua",
            "generated/utils/image_runtime.lua",
            "generated/utils/png.lua",
        ),
        "native_files": ("native/built_in/py_runtime.lua",),
        "delete_target_files": (),
    },
    {
        "backend": "ruby",
        "generated_files": (
            "generated/built_in/contains.rb",
            "generated/built_in/io_ops.rb",
            "generated/built_in/iter_ops.rb",
            "generated/built_in/numeric_ops.rb",
            "generated/built_in/predicates.rb",
            "generated/built_in/scalar_ops.rb",
            "generated/built_in/sequence.rb",
            "generated/built_in/string_ops.rb",
            "generated/built_in/type_id.rb",
            "generated/built_in/zip_ops.rb",
            "generated/std/argparse.rb",
            "generated/std/glob.rb",
            "generated/std/json.rb",
            "generated/std/math.rb",
            "generated/std/os.rb",
            "generated/std/os_path.rb",
            "generated/std/pathlib.rb",
            "generated/std/random.rb",
            "generated/std/re.rb",
            "generated/std/sys.rb",
            "generated/std/time.rb",
            "generated/std/timeit.rb",
            "generated/utils/assertions.rb",
            "generated/utils/gif.rb",
            "generated/utils/image_runtime.rb",
            "generated/utils/png.rb",
        ),
        "native_files": ("native/built_in/py_runtime.rb",),
        "delete_target_files": (),
    },
    {
        "backend": "php",
        "generated_files": (
            "generated/built_in/contains.php",
            "generated/built_in/io_ops.php",
            "generated/built_in/iter_ops.php",
            "generated/built_in/numeric_ops.php",
            "generated/built_in/predicates.php",
            "generated/built_in/scalar_ops.php",
            "generated/built_in/sequence.php",
            "generated/built_in/string_ops.php",
            "generated/built_in/type_id.php",
            "generated/built_in/zip_ops.php",
            "generated/std/argparse.php",
            "generated/std/glob.php",
            "generated/std/json.php",
            "generated/std/math.php",
            "generated/std/os.php",
            "generated/std/os_path.php",
            "generated/std/pathlib.php",
            "generated/std/random.php",
            "generated/std/re.php",
            "generated/std/sys.php",
            "generated/std/time.php",
            "generated/std/timeit.php",
            "generated/utils/assertions.php",
            "generated/utils/gif.php",
            "generated/utils/png.php",
        ),
        "native_files": ("native/built_in/py_runtime.php", "native/std/math_native.php", "native/std/time_native.php"),
        "delete_target_files": (),
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
            "src/runtime/cs/native/std/math_native.cs",
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
            "test_js_cli_staged_runtime_bundle_resolves_runtime_helpers",
            "test_js_generated_built_in_compare_lane_resolves_native_runtime",
        ),
    },
    {
        "backend": "ts",
        "test_path": "test/unit/backends/ts/test_py2ts_smoke.py",
        "required_tests": (
            "test_ts_cli_staged_runtime_bundle_resolves_runtime_helpers",
            "test_ts_generated_built_in_compare_lane_rehomes_native_runtime_import",
        ),
    },
    {
        "backend": "lua",
        "test_path": "test/unit/backends/lua/test_py2lua_smoke.py",
        "required_tests": (
            "test_lua_runtime_source_path_is_migrated",
            "test_lua_cli_staged_runtime_lane_resolves_runtime_helpers",
        ),
    },
    {
        "backend": "ruby",
        "test_path": "test/unit/backends/rb/test_py2rb_smoke.py",
        "required_tests": (
            "test_ruby_runtime_source_path_is_migrated",
            "test_ruby_cli_staged_runtime_lane_resolves_runtime_helpers",
        ),
    },
    {
        "backend": "php",
        "test_path": "test/unit/backends/php/test_py2php_smoke.py",
        "required_tests": (
            "test_php_runtime_source_path_is_migrated",
            "test_php_generated_math_runtime_owner_is_live_wrapper_shaped",
            "test_php_generated_time_runtime_owner_is_live_wrapper_shaped",
            "test_php_repo_generated_lanes_resolve_native_substrate",
            "test_php_generated_built_in_compare_lane_resolves_native_runtime",
            "test_php_cli_staged_runtime_lane_resolves_remaining_shims",
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


def iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_inventory() -> tuple[
    NonCppRuntimeGeneratedCppBaselineHelperArtifactInventoryEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_INVENTORY_V1


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

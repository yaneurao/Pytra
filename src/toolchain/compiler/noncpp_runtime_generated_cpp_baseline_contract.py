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
            "std/json",
            "std/math",
            "std/pathlib",
            "std/random",
            "std/re",
            "std/sys",
            "std/timeit",
        ),
    },
    {
        "backend": "cs",
        "legacy_state": "native_canonical",
        "modules": ("std/json", "std/math", "std/pathlib"),
    },
    {
        "backend": "lua",
        "legacy_state": "blocked",
        "modules": NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MODULES_V1,
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
    {
        "backend": "ruby",
        "legacy_state": "blocked",
        "modules": NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MODULES_V1,
    },
)

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_HELPER_ARTIFACT_OVERLAP_V1: Final[
    tuple[str, ...]
] = ()

NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MATERIALIZED_BACKENDS_V1: Final[
    tuple[str, ...]
] = ("cs", "go", "java", "rs", "swift", "nim", "kotlin", "scala", "js", "ts", "php")

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


def iter_noncpp_runtime_generated_cpp_baseline_legacy_policy_files() -> tuple[
    NonCppRuntimeGeneratedCppBaselineLegacyPolicyFileEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_LEGACY_POLICY_FILES_V1


def iter_noncpp_runtime_generated_cpp_baseline_active_policy_docs() -> tuple[
    NonCppRuntimeGeneratedCppBaselineActivePolicyDocEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_ACTIVE_POLICY_DOCS_V1

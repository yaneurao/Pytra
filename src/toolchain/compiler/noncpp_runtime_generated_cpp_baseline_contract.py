"""Canonical non-C++ generated runtime baseline derived from cpp/generated."""

from __future__ import annotations

from typing import Final, TypedDict


class NonCppRuntimeGeneratedCppBaselineBucketEntry(TypedDict):
    bucket: str
    modules: tuple[str, ...]


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


def iter_noncpp_runtime_generated_cpp_baseline_bucket_order() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKET_ORDER_V1


def iter_noncpp_runtime_generated_cpp_baseline_buckets() -> tuple[
    NonCppRuntimeGeneratedCppBaselineBucketEntry, ...
]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_BUCKETS_V1


def iter_noncpp_runtime_generated_cpp_baseline_modules() -> tuple[str, ...]:
    return NONCPP_RUNTIME_GENERATED_CPP_BASELINE_MODULES_V1


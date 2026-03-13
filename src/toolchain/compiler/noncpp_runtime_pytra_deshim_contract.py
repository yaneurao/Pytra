"""Baseline contract for removing checked-in non-C++/non-C# runtime `pytra/` lanes."""

from __future__ import annotations

from typing import Final, TypedDict


class NonCppPytraDeshimBackendEntry(TypedDict):
    backend: str
    family: str
    current_dir: str
    target_policy: str
    target_roots: tuple[str, ...]
    blocker_buckets: tuple[str, ...]


class NonCppPytraDeshimBlockerEntry(TypedDict):
    backend: str
    bucket: str
    path: str
    needles: tuple[str, ...]
    rationale: str


class NonCppPytraDeshimDocPolicyEntry(TypedDict):
    path: str
    needles: tuple[str, ...]


NONCPP_PYTRA_DESHIM_BACKEND_ORDER_V1: Final[tuple[str, ...]] = (
    "rs",
    "go",
    "java",
    "kotlin",
    "scala",
    "swift",
    "nim",
    "js",
    "ts",
    "lua",
    "ruby",
    "php",
)

NONCPP_PYTRA_DESHIM_BUCKET_ORDER_V1: Final[tuple[str, ...]] = (
    "direct_load_smoke",
    "runtime_shim_writer",
    "contract_allowlist",
    "selfhost_stage",
)

NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1: Final[tuple[str, ...]] = ("generated", "native")

NONCPP_PYTRA_DESHIM_CURRENT_DIRS_V1: Final[tuple[str, ...]] = ()

NONCPP_PYTRA_DESHIM_CURRENT_FILES_V1: Final[tuple[str, ...]] = ()

NONCPP_PYTRA_DESHIM_BACKENDS_V1: Final[tuple[NonCppPytraDeshimBackendEntry, ...]] = (
    {
        "backend": "rs",
        "family": "rust_cleanup",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_rust_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "go",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "java",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "kotlin",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "scala",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "swift",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "nim",
        "family": "static",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_static_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "js",
        "family": "script",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_script_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "ts",
        "family": "script",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_script_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "lua",
        "family": "script",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_script_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "ruby",
        "family": "script",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_script_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "php",
        "family": "script",
        "current_dir": "",
        "target_policy": "delete_target_removed_after_script_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
)

NONCPP_PYTRA_DESHIM_BLOCKERS_V1: Final[tuple[NonCppPytraDeshimBlockerEntry, ...]] = ()

NONCPP_PYTRA_DESHIM_DOC_POLICY_V1: Final[tuple[NonCppPytraDeshimDocPolicyEntry, ...]] = (
    {
        "path": "docs/ja/spec/spec-folder.md",
        "needles": (
            "非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` は存在してはならず、再出現は contract fail とする。",
            "repo 正本 layout は `src/runtime/<lang>/{generated,native}/` のみを許可する。",
        ),
    },
    {
        "path": "docs/en/spec/spec-folder.md",
        "needles": (
            "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` must not exist; any re-entry is a contract failure.",
            "The canonical repo layout allows only `src/runtime/<lang>/{generated,native}/` as live runtime roots.",
        ),
    },
    {
        "path": "docs/ja/spec/spec-dev.md",
        "needles": (
            "non-C++ / non-C# backend の checked-in `src/runtime/<lang>/pytra/**` は存在してはならない。",
        ),
    },
    {
        "path": "docs/en/spec/spec-dev.md",
        "needles": (
            "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` must not exist.",
        ),
    },
        {
            "path": "docs/ja/spec/spec-java-native-backend.md",
            "needles": (
                "実行時依存は Java runtime（repo 正本は `src/runtime/java/{generated,native}/`）へ収束し",
                "`src/runtime/java/{generated,native}/` 配下の Java runtime API。",
            ),
        },
        {
            "path": "docs/en/spec/spec-java-native-backend.md",
            "needles": (
                "Runtime dependency converges to Java runtime (the canonical repo roots are `src/runtime/java/{generated,native}/`)",
                "Java runtime APIs under `src/runtime/java/{generated,native}/`;",
            ),
        },
    {
        "path": "docs/ja/spec/spec-lua-native-backend.md",
        "needles": (
            "`src/runtime/lua/{generated,native}/` 配下の Lua runtime API（checked-in repo tree に `src/runtime/lua/pytra/**` は存在しない）",
        ),
    },
    {
        "path": "docs/en/spec/spec-lua-native-backend.md",
        "needles": (
            "Lua runtime API under `src/runtime/lua/{generated,native}/` (the checked-in repo tree no longer keeps `src/runtime/lua/pytra/**`)",
        ),
    },
        {
            "path": "docs/ja/spec/spec-gsk-native-backend.md",
            "needles": (
                "Go: `src/runtime/go/{generated,native}/` + Go 標準ライブラリ。",
                "Swift: `src/runtime/swift/{generated,native}/` + Swift 標準ライブラリ。",
                "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM 標準ライブラリ。",
            ),
        },
        {
            "path": "docs/en/spec/spec-gsk-native-backend.md",
            "needles": (
                "Go: `src/runtime/go/{generated,native}/` + Go standard library.",
                "Swift: `src/runtime/swift/{generated,native}/` + Swift standard library.",
                "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM standard library.",
            ),
        },
)


def iter_noncpp_pytra_deshim_backend_order() -> tuple[str, ...]:
    return NONCPP_PYTRA_DESHIM_BACKEND_ORDER_V1


def iter_noncpp_pytra_deshim_bucket_order() -> tuple[str, ...]:
    return NONCPP_PYTRA_DESHIM_BUCKET_ORDER_V1


def iter_noncpp_pytra_deshim_current_dirs() -> tuple[str, ...]:
    return NONCPP_PYTRA_DESHIM_CURRENT_DIRS_V1


def iter_noncpp_pytra_deshim_current_files() -> tuple[str, ...]:
    return NONCPP_PYTRA_DESHIM_CURRENT_FILES_V1


def iter_noncpp_pytra_deshim_backends() -> tuple[NonCppPytraDeshimBackendEntry, ...]:
    return NONCPP_PYTRA_DESHIM_BACKENDS_V1


def iter_noncpp_pytra_deshim_blockers() -> tuple[NonCppPytraDeshimBlockerEntry, ...]:
    return NONCPP_PYTRA_DESHIM_BLOCKERS_V1


def iter_noncpp_pytra_deshim_doc_policy() -> tuple[NonCppPytraDeshimDocPolicyEntry, ...]:
    return NONCPP_PYTRA_DESHIM_DOC_POLICY_V1

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

NONCPP_PYTRA_DESHIM_CURRENT_DIRS_V1: Final[tuple[str, ...]] = (
    "src/runtime/js/pytra",
    "src/runtime/lua/pytra",
    "src/runtime/php/pytra",
    "src/runtime/ruby/pytra",
    "src/runtime/ts/pytra",
)

NONCPP_PYTRA_DESHIM_CURRENT_FILES_V1: Final[tuple[str, ...]] = (
    "src/runtime/js/pytra/README.md",
    "src/runtime/js/pytra/py_runtime.js",
    "src/runtime/js/pytra/std/json.js",
    "src/runtime/js/pytra/std/math.js",
    "src/runtime/js/pytra/std/pathlib.js",
    "src/runtime/js/pytra/std/time.js",
    "src/runtime/js/pytra/utils/gif.js",
    "src/runtime/js/pytra/utils/png.js",
    "src/runtime/lua/pytra/built_in/py_runtime.lua",
    "src/runtime/php/pytra/py_runtime.php",
    "src/runtime/php/pytra/std/time.php",
    "src/runtime/php/pytra/utils/gif.php",
    "src/runtime/php/pytra/utils/png.php",
    "src/runtime/ruby/pytra/built_in/py_runtime.rb",
    "src/runtime/ts/pytra/README.md",
    "src/runtime/ts/pytra/py_runtime.ts",
    "src/runtime/ts/pytra/std/json.ts",
    "src/runtime/ts/pytra/std/math.ts",
    "src/runtime/ts/pytra/std/pathlib.ts",
    "src/runtime/ts/pytra/std/time.ts",
    "src/runtime/ts/pytra/utils/gif.ts",
    "src/runtime/ts/pytra/utils/png.ts",
)

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
        "current_dir": "src/runtime/js/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "ts",
        "family": "script",
        "current_dir": "src/runtime/ts/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": (),
    },
    {
        "backend": "lua",
        "family": "script",
        "current_dir": "src/runtime/lua/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("direct_load_smoke", "contract_allowlist"),
    },
    {
        "backend": "ruby",
        "family": "script",
        "current_dir": "src/runtime/ruby/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("direct_load_smoke", "contract_allowlist"),
    },
    {
        "backend": "php",
        "family": "script",
        "current_dir": "src/runtime/php/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("direct_load_smoke", "runtime_shim_writer", "contract_allowlist"),
    },
)

NONCPP_PYTRA_DESHIM_BLOCKERS_V1: Final[tuple[NonCppPytraDeshimBlockerEntry, ...]] = (
    {
        "backend": "lua",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/lua/test_py2lua_smoke.py",
        "needles": ('delete_target_runtime = ROOT / "src" / "runtime" / "lua" / "pytra" / "built_in" / "py_runtime.lua"',),
        "rationale": "Lua compat smoke still directly loads the checked-in pytra runtime shim.",
    },
    {
        "backend": "ruby",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/rb/test_py2rb_smoke.py",
        "needles": ('delete_target_runtime = ROOT / "src" / "runtime" / "ruby" / "pytra" / "built_in" / "py_runtime.rb"',),
        "rationale": "Ruby compat smoke still directly loads the checked-in pytra runtime shim.",
    },
    {
        "backend": "php",
        "bucket": "runtime_shim_writer",
        "path": "tools/gen_runtime_from_manifest.py",
        "needles": ("require_once __DIR__ . '/pytra/py_runtime.php';",),
        "rationale": "PHP runtime generation still knows how to emit a repo-tree pytra shim include.",
    },
    {
        "backend": "php",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/php/test_py2php_smoke.py",
        "needles": ('delete_target_runtime_path = ROOT / "src" / "runtime" / "php" / "pytra" / "py_runtime.php"',),
        "rationale": "PHP compat smoke still directly loads the checked-in pytra runtime shim.",
    },
)

NONCPP_PYTRA_DESHIM_DOC_POLICY_V1: Final[tuple[NonCppPytraDeshimDocPolicyEntry, ...]] = (
    {
        "path": "docs/ja/spec/spec-folder.md",
        "needles": (
            "非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` は互換 lane ではなく delete target とする。",
            "repo 正本 layout は `src/runtime/<lang>/{generated,native}/` のみを許可する。",
        ),
    },
    {
        "path": "docs/en/spec/spec-folder.md",
        "needles": (
            "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` is a delete target, not a compatibility lane.",
            "The canonical repo layout allows only `src/runtime/<lang>/{generated,native}/` as live runtime roots.",
        ),
    },
    {
        "path": "docs/ja/spec/spec-dev.md",
        "needles": (
            "non-C++ / non-C# backend の checked-in `src/runtime/<lang>/pytra/**` は delete target debt とする。",
        ),
    },
    {
        "path": "docs/en/spec/spec-dev.md",
        "needles": (
            "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` is delete-target debt only.",
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
            "`src/runtime/lua/{generated,native}/` 配下の Lua runtime API（checked-in `src/runtime/lua/pytra/**` は delete target debt）",
        ),
    },
    {
        "path": "docs/en/spec/spec-lua-native-backend.md",
        "needles": (
            "Lua runtime API under `src/runtime/lua/{generated,native}/` (checked-in `src/runtime/lua/pytra/**` is delete-target debt only)",
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

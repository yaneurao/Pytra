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
    "src/runtime/go/pytra",
    "src/runtime/java/pytra",
    "src/runtime/js/pytra",
    "src/runtime/kotlin/pytra",
    "src/runtime/lua/pytra",
    "src/runtime/nim/pytra",
    "src/runtime/php/pytra",
    "src/runtime/rs/pytra",
    "src/runtime/ruby/pytra",
    "src/runtime/scala/pytra",
    "src/runtime/swift/pytra",
    "src/runtime/ts/pytra",
)

NONCPP_PYTRA_DESHIM_CURRENT_FILES_V1: Final[tuple[str, ...]] = (
    "src/runtime/go/pytra/built_in/py_runtime.go",
    "src/runtime/java/pytra/built_in/PyRuntime.java",
    "src/runtime/js/pytra/README.md",
    "src/runtime/js/pytra/py_runtime.js",
    "src/runtime/js/pytra/std/json.js",
    "src/runtime/js/pytra/std/math.js",
    "src/runtime/js/pytra/std/pathlib.js",
    "src/runtime/js/pytra/std/time.js",
    "src/runtime/js/pytra/utils/gif.js",
    "src/runtime/js/pytra/utils/png.js",
    "src/runtime/kotlin/pytra/built_in/py_runtime.kt",
    "src/runtime/lua/pytra/built_in/py_runtime.lua",
    "src/runtime/nim/pytra/built_in/py_runtime.nim",
    "src/runtime/php/pytra/py_runtime.php",
    "src/runtime/php/pytra/std/time.php",
    "src/runtime/php/pytra/utils/gif.php",
    "src/runtime/php/pytra/utils/png.php",
    "src/runtime/rs/pytra/README.md",
    "src/runtime/rs/pytra/built_in/py_runtime.rs",
    "src/runtime/rs/pytra/compiler/README.md",
    "src/runtime/rs/pytra/std/README.md",
    "src/runtime/rs/pytra/utils/README.md",
    "src/runtime/ruby/pytra/built_in/py_runtime.rb",
    "src/runtime/scala/pytra/built_in/py_runtime.scala",
    "src/runtime/swift/pytra/built_in/py_runtime.swift",
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
        "current_dir": "src/runtime/rs/pytra",
        "target_policy": "delete_target_after_contract_cleanup",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "go",
        "family": "static",
        "current_dir": "src/runtime/go/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "java",
        "family": "static",
        "current_dir": "src/runtime/java/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "kotlin",
        "family": "static",
        "current_dir": "src/runtime/kotlin/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "scala",
        "family": "static",
        "current_dir": "src/runtime/scala/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "swift",
        "family": "static",
        "current_dir": "src/runtime/swift/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "nim",
        "family": "static",
        "current_dir": "src/runtime/nim/pytra",
        "target_policy": "delete_target_after_static_bundle",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("contract_allowlist",),
    },
    {
        "backend": "js",
        "family": "script",
        "current_dir": "src/runtime/js/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("direct_load_smoke", "runtime_shim_writer", "contract_allowlist", "selfhost_stage"),
    },
    {
        "backend": "ts",
        "family": "script",
        "current_dir": "src/runtime/ts/pytra",
        "target_policy": "delete_target_after_script_output_staging",
        "target_roots": NONCPP_PYTRA_DESHIM_TARGET_ROOTS_V1,
        "blocker_buckets": ("runtime_shim_writer", "contract_allowlist"),
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
        "backend": "go",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/go/pytra/built_in/py_runtime.go"',),
        "rationale": "Go current->target rollout mapping still treats the checked-in pytra lane as a live current root.",
    },
    {
        "backend": "java",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/java/pytra/built_in/"',),
        "rationale": "Java current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "kotlin",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/kotlin/pytra/built_in/py_runtime.kt"',),
        "rationale": "Kotlin current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "scala",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/scala/pytra/built_in/py_runtime.scala"',),
        "rationale": "Scala current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "swift",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/swift/pytra/built_in/py_runtime.swift"',),
        "rationale": "Swift current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "nim",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/nim/pytra/built_in/py_runtime.nim"',),
        "rationale": "Nim current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "js",
        "bucket": "runtime_shim_writer",
        "path": "src/toolchain/compiler/js_runtime_shims.py",
        "needles": ('"pytra/py_runtime.js"', '"pytra/std/pathlib.js"'),
        "rationale": "JS runtime shim generation still writes repo-tree pytra import paths.",
    },
    {
        "backend": "js",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/js/test_py2js_smoke.py",
        "needles": (
            "./src/runtime/js/pytra/py_runtime.js",
            "./src/runtime/js/pytra/std/json.js",
        ),
        "rationale": "JS smoke still directly loads checked-in runtime files under src/runtime/js/pytra.",
    },
    {
        "backend": "js",
        "bucket": "selfhost_stage",
        "path": "tools/check_multilang_selfhost_stage1.py",
        "needles": ('"pytra/py_runtime.js"', '"pytra/std/pathlib.js"'),
        "rationale": "JS selfhost stage checks still enumerate pytra runtime staging files explicitly.",
    },
    {
        "backend": "js",
        "bucket": "selfhost_stage",
        "path": "tools/check_multilang_selfhost_multistage.py",
        "needles": ('"pytra/py_runtime.js"', '"pytra/std/pathlib.js"'),
        "rationale": "JS multistage selfhost checks still enumerate pytra runtime staging files explicitly.",
    },
    {
        "backend": "ts",
        "bucket": "contract_allowlist",
        "path": "src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py",
        "needles": ('"current_prefix": "src/runtime/ts/pytra/py_runtime.ts"',),
        "rationale": "TS current->target rollout mapping still includes the checked-in pytra lane.",
    },
    {
        "backend": "lua",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/lua/test_py2lua_smoke.py",
        "needles": ('compat_runtime = ROOT / "src" / "runtime" / "lua" / "pytra" / "built_in" / "py_runtime.lua"',),
        "rationale": "Lua compat smoke still directly loads the checked-in pytra runtime shim.",
    },
    {
        "backend": "ruby",
        "bucket": "direct_load_smoke",
        "path": "test/unit/backends/rb/test_py2rb_smoke.py",
        "needles": ('compat_runtime = ROOT / "src" / "runtime" / "ruby" / "pytra" / "built_in" / "py_runtime.rb"',),
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
        "needles": ('compat_runtime_path = ROOT / "src" / "runtime" / "php" / "pytra" / "py_runtime.php"',),
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
            "`src/runtime/rs/pytra/` を runtime ownership root として扱ってはならない。",
            "non-C++ / non-C# backend の checked-in `src/runtime/<lang>/pytra/**` は delete target debt とする。",
        ),
    },
    {
        "path": "docs/en/spec/spec-dev.md",
        "needles": (
            "`src/runtime/rs/pytra/` must not be treated as a live runtime ownership root.",
            "For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` is delete-target debt only.",
        ),
    },
    {
        "path": "docs/ja/spec/spec-java-native-backend.md",
        "needles": (
            "実行時依存は Java runtime（repo 正本は `src/runtime/java/{generated,native}/`）へ収束し",
            "`src/runtime/java/{generated,native}/` 配下の Java runtime API（checked-in `src/runtime/java/pytra/**` は delete target debt）。",
        ),
    },
    {
        "path": "docs/en/spec/spec-java-native-backend.md",
        "needles": (
            "Runtime dependency converges to Java runtime (the canonical repo roots are `src/runtime/java/{generated,native}/`)",
            "Java runtime APIs under `src/runtime/java/{generated,native}/` (checked-in `src/runtime/java/pytra/**` is delete-target debt only);",
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
            "Go: `src/runtime/go/{generated,native}/` + Go 標準ライブラリ（checked-in `src/runtime/go/pytra/**` は delete target debt）。",
            "Swift: `src/runtime/swift/{generated,native}/` + Swift 標準ライブラリ（checked-in `src/runtime/swift/pytra/**` は delete target debt）。",
            "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM 標準ライブラリ（checked-in `src/runtime/kotlin/pytra/**` は delete target debt）。",
        ),
    },
    {
        "path": "docs/en/spec/spec-gsk-native-backend.md",
        "needles": (
            "Go: `src/runtime/go/{generated,native}/` + Go standard library (checked-in `src/runtime/go/pytra/**` is delete-target debt only).",
            "Swift: `src/runtime/swift/{generated,native}/` + Swift standard library (checked-in `src/runtime/swift/pytra/**` is delete-target debt only).",
            "Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM standard library (checked-in `src/runtime/kotlin/pytra/**` is delete-target debt only).",
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

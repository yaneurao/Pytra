"""Current->target runtime layout mapping for remaining non-C++ backends."""

from __future__ import annotations

from typing import Final, TypedDict


class RemainingRuntimeLaneMappingEntry(TypedDict):
    current_prefix: str
    target_prefix: str
    ownership: str
    rationale: str


class RemainingRuntimeBackendMappingEntry(TypedDict):
    backend: str
    family: str
    runtime_hook_key: str
    current_roots: tuple[str, ...]
    target_roots: tuple[str, ...]
    lane_mappings: tuple[RemainingRuntimeLaneMappingEntry, ...]


REMAINING_NONCPP_BACKEND_ORDER_V1: Final[tuple[str, ...]] = (
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


REMAINING_NONCPP_RUNTIME_LAYOUT_V1: Final[tuple[RemainingRuntimeBackendMappingEntry, ...]] = (
    {
        "backend": "go",
        "family": "static",
        "runtime_hook_key": "go",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/go/pytra-core/built_in/",
                "target_prefix": "src/runtime/go/native/built_in/",
                "ownership": "native",
                "rationale": "Go keeps its handwritten runtime substrate in pytra-core/built_in today.",
            },
            {
                "current_prefix": "src/runtime/go/pytra-gen/utils/",
                "target_prefix": "src/runtime/go/generated/utils/",
                "ownership": "generated",
                "rationale": "Go image helpers already come from SoT generation under pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/go/pytra/py_runtime.go",
                "target_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "ownership": "compat",
                "rationale": "The public Go shim is still flat today and will be bucketed under pytra/built_in during rollout.",
            },
        ),
    },
    {
        "backend": "java",
        "family": "static",
        "runtime_hook_key": "java",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/java/pytra-core/built_in/",
                "target_prefix": "src/runtime/java/native/built_in/",
                "ownership": "native",
                "rationale": "Java handwritten runtime helpers currently live in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/java/pytra-core/std/",
                "target_prefix": "src/runtime/java/native/std/",
                "ownership": "native",
                "rationale": "Java std handwritten seams are still under pytra-core/std.",
            },
            {
                "current_prefix": "src/runtime/java/pytra-gen/std/",
                "target_prefix": "src/runtime/java/generated/std/",
                "ownership": "generated",
                "rationale": "Java already has SoT-generated std compare artifacts under pytra-gen/std.",
            },
            {
                "current_prefix": "src/runtime/java/pytra-gen/utils/",
                "target_prefix": "src/runtime/java/generated/utils/",
                "ownership": "generated",
                "rationale": "Java image helpers are already emitted from SoT into pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/java/pytra/built_in/",
                "target_prefix": "src/runtime/java/pytra/built_in/",
                "ownership": "compat",
                "rationale": "Java public shims are already bucketed under pytra/built_in and stay there as compat lane.",
            },
        ),
    },
    {
        "backend": "kotlin",
        "family": "static",
        "runtime_hook_key": "kotlin",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/kotlin/pytra-core/built_in/",
                "target_prefix": "src/runtime/kotlin/native/built_in/",
                "ownership": "native",
                "rationale": "Kotlin handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/kotlin/pytra-gen/utils/",
                "target_prefix": "src/runtime/kotlin/generated/utils/",
                "ownership": "generated",
                "rationale": "Kotlin image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/kotlin/pytra/py_runtime.kt",
                "target_prefix": "src/runtime/kotlin/pytra/built_in/py_runtime.kt",
                "ownership": "compat",
                "rationale": "Kotlin public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "scala",
        "family": "static",
        "runtime_hook_key": "scala",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/scala/pytra-core/built_in/",
                "target_prefix": "src/runtime/scala/native/built_in/",
                "ownership": "native",
                "rationale": "Scala handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/scala/pytra-gen/utils/",
                "target_prefix": "src/runtime/scala/generated/utils/",
                "ownership": "generated",
                "rationale": "Scala image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/scala/pytra/py_runtime.scala",
                "target_prefix": "src/runtime/scala/pytra/built_in/py_runtime.scala",
                "ownership": "compat",
                "rationale": "Scala public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "swift",
        "family": "static",
        "runtime_hook_key": "swift",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/swift/pytra-core/built_in/",
                "target_prefix": "src/runtime/swift/native/built_in/",
                "ownership": "native",
                "rationale": "Swift handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/swift/pytra-gen/utils/",
                "target_prefix": "src/runtime/swift/generated/utils/",
                "ownership": "generated",
                "rationale": "Swift image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/swift/pytra/py_runtime.swift",
                "target_prefix": "src/runtime/swift/pytra/built_in/py_runtime.swift",
                "ownership": "compat",
                "rationale": "Swift public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "nim",
        "family": "static",
        "runtime_hook_key": "nim",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/nim/pytra-core/built_in/",
                "target_prefix": "src/runtime/nim/native/built_in/",
                "ownership": "native",
                "rationale": "Nim handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/nim/pytra-gen/utils/",
                "target_prefix": "src/runtime/nim/generated/utils/",
                "ownership": "generated",
                "rationale": "Nim image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/nim/pytra/py_runtime.nim",
                "target_prefix": "src/runtime/nim/pytra/built_in/py_runtime.nim",
                "ownership": "compat",
                "rationale": "Nim public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "js",
        "family": "script",
        "runtime_hook_key": "js_shims",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/js/pytra-core/built_in/",
                "target_prefix": "src/runtime/js/native/built_in/",
                "ownership": "native",
                "rationale": "JS handwritten built-in runtime still lives in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/js/pytra-core/std/",
                "target_prefix": "src/runtime/js/native/std/",
                "ownership": "native",
                "rationale": "JS std handwritten runtime still lives in pytra-core/std.",
            },
            {
                "current_prefix": "src/runtime/js/pytra-gen/utils/",
                "target_prefix": "src/runtime/js/generated/utils/",
                "ownership": "generated",
                "rationale": "JS image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/py_runtime.js",
                "target_prefix": "src/runtime/js/pytra/py_runtime.js",
                "ownership": "compat",
                "rationale": "JS keeps a root-level public shim for built_in py_runtime.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/time.js",
                "target_prefix": "src/runtime/js/pytra/std/time.js",
                "ownership": "compat",
                "rationale": "Flat JS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/math.js",
                "target_prefix": "src/runtime/js/pytra/std/math.js",
                "ownership": "compat",
                "rationale": "Flat JS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/pathlib.js",
                "target_prefix": "src/runtime/js/pytra/std/pathlib.js",
                "ownership": "compat",
                "rationale": "Flat JS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/png.js",
                "target_prefix": "src/runtime/js/pytra/utils/png.js",
                "ownership": "compat",
                "rationale": "Flat JS utils shim files will be bucketed under pytra/utils during rollout.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/gif.js",
                "target_prefix": "src/runtime/js/pytra/utils/gif.js",
                "ownership": "compat",
                "rationale": "Flat JS utils shim files will be bucketed under pytra/utils during rollout.",
            },
            {
                "current_prefix": "src/runtime/js/pytra/README.md",
                "target_prefix": "src/runtime/js/pytra/README.md",
                "ownership": "compat",
                "rationale": "JS pytra README remains a compat-lane document.",
            },
        ),
    },
    {
        "backend": "ts",
        "family": "script",
        "runtime_hook_key": "js_shims",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/ts/pytra-core/built_in/",
                "target_prefix": "src/runtime/ts/native/built_in/",
                "ownership": "native",
                "rationale": "TS handwritten built-in runtime still lives in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra-core/std/",
                "target_prefix": "src/runtime/ts/native/std/",
                "ownership": "native",
                "rationale": "TS std handwritten runtime still lives in pytra-core/std.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra-gen/utils/",
                "target_prefix": "src/runtime/ts/generated/utils/",
                "ownership": "generated",
                "rationale": "TS image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/py_runtime.ts",
                "target_prefix": "src/runtime/ts/pytra/py_runtime.ts",
                "ownership": "compat",
                "rationale": "TS keeps a root-level public shim for built_in py_runtime.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/time.ts",
                "target_prefix": "src/runtime/ts/pytra/std/time.ts",
                "ownership": "compat",
                "rationale": "Flat TS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/math.ts",
                "target_prefix": "src/runtime/ts/pytra/std/math.ts",
                "ownership": "compat",
                "rationale": "Flat TS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/pathlib.ts",
                "target_prefix": "src/runtime/ts/pytra/std/pathlib.ts",
                "ownership": "compat",
                "rationale": "Flat TS std shim files will be bucketed under pytra/std during rollout.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/png_helper.ts",
                "target_prefix": "src/runtime/ts/pytra/utils/png.ts",
                "ownership": "compat",
                "rationale": "TS flat utils shim files will be bucketed under pytra/utils during rollout.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/gif_helper.ts",
                "target_prefix": "src/runtime/ts/pytra/utils/gif.ts",
                "ownership": "compat",
                "rationale": "TS flat utils shim files will be bucketed under pytra/utils during rollout.",
            },
            {
                "current_prefix": "src/runtime/ts/pytra/README.md",
                "target_prefix": "src/runtime/ts/pytra/README.md",
                "ownership": "compat",
                "rationale": "TS pytra README remains a compat-lane document.",
            },
        ),
    },
    {
        "backend": "lua",
        "family": "script",
        "runtime_hook_key": "lua",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/lua/pytra-core/built_in/",
                "target_prefix": "src/runtime/lua/native/built_in/",
                "ownership": "native",
                "rationale": "Lua handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/lua/pytra-gen/utils/",
                "target_prefix": "src/runtime/lua/generated/utils/",
                "ownership": "generated",
                "rationale": "Lua image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/lua/pytra/py_runtime.lua",
                "target_prefix": "src/runtime/lua/pytra/built_in/py_runtime.lua",
                "ownership": "compat",
                "rationale": "Lua public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "ruby",
        "family": "script",
        "runtime_hook_key": "ruby",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/ruby/pytra-core/built_in/",
                "target_prefix": "src/runtime/ruby/native/built_in/",
                "ownership": "native",
                "rationale": "Ruby handwritten runtime substrate still sits in pytra-core/built_in.",
            },
            {
                "current_prefix": "src/runtime/ruby/pytra-gen/utils/",
                "target_prefix": "src/runtime/ruby/generated/utils/",
                "ownership": "generated",
                "rationale": "Ruby image helpers are SoT-generated in pytra-gen/utils.",
            },
            {
                "current_prefix": "src/runtime/ruby/pytra/py_runtime.rb",
                "target_prefix": "src/runtime/ruby/pytra/built_in/py_runtime.rb",
                "ownership": "compat",
                "rationale": "Ruby public shim is currently flat and will be normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "php",
        "family": "script",
        "runtime_hook_key": "php",
        "current_roots": ("pytra", "pytra-core", "pytra-gen"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/php/pytra-core/py_runtime.php",
                "target_prefix": "src/runtime/php/native/built_in/py_runtime.php",
                "ownership": "native",
                "rationale": "PHP handwritten core runtime is still a flat file under pytra-core.",
            },
            {
                "current_prefix": "src/runtime/php/pytra-core/std/",
                "target_prefix": "src/runtime/php/native/std/",
                "ownership": "native",
                "rationale": "PHP handwritten std seams still live in pytra-core/std.",
            },
            {
                "current_prefix": "src/runtime/php/pytra-gen/runtime/",
                "target_prefix": "src/runtime/php/generated/utils/",
                "ownership": "generated",
                "rationale": "PHP still uses a legacy runtime bucket for SoT-generated image helpers; rollout renames it to generated/utils.",
            },
            {
                "current_prefix": "src/runtime/php/pytra/py_runtime.php",
                "target_prefix": "src/runtime/php/pytra/py_runtime.php",
                "ownership": "compat",
                "rationale": "PHP keeps a root-level public shim for require_once compatibility.",
            },
            {
                "current_prefix": "src/runtime/php/pytra/std/",
                "target_prefix": "src/runtime/php/pytra/std/",
                "ownership": "compat",
                "rationale": "PHP already exposes std shims in bucketed form and keeps that public shape.",
            },
            {
                "current_prefix": "src/runtime/php/pytra/runtime/",
                "target_prefix": "src/runtime/php/pytra/utils/",
                "ownership": "compat",
                "rationale": "PHP public image shims still live in a legacy runtime bucket and will be normalized into pytra/utils.",
            },
        ),
    },
)


def iter_remaining_noncpp_backend_order() -> tuple[str, ...]:
    return REMAINING_NONCPP_BACKEND_ORDER_V1


def iter_remaining_noncpp_runtime_layout() -> tuple[RemainingRuntimeBackendMappingEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_LAYOUT_V1

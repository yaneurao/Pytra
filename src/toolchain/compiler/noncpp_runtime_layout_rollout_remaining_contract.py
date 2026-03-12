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


class RemainingRuntimeCurrentInventoryEntry(TypedDict):
    backend: str
    pytra_core_files: tuple[str, ...]
    pytra_gen_files: tuple[str, ...]
    pytra_files: tuple[str, ...]


class RemainingRuntimeTargetInventoryEntry(TypedDict):
    backend: str
    generated_files: tuple[str, ...]
    native_files: tuple[str, ...]
    compat_files: tuple[str, ...]


class RemainingRuntimeModuleBucketEntry(TypedDict):
    backend: str
    generated_modules: tuple[str, ...]
    native_modules: tuple[str, ...]
    compat_modules: tuple[str, ...]
    blocked_modules: tuple[str, ...]


class RemainingRuntimeWaveAHookSourceEntry(TypedDict):
    backend: str
    runtime_hook_files: tuple[str, ...]


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

REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1: Final[tuple[str, ...]] = (
    "built_in/contains",
    "built_in/io_ops",
    "built_in/iter_ops",
    "built_in/numeric_ops",
    "built_in/predicates",
    "built_in/scalar_ops",
    "built_in/sequence",
    "built_in/string_ops",
    "built_in/type_id",
    "built_in/zip_ops",
)

REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1: Final[tuple[str, ...]] = (
    "std/json",
    "std/math",
    "std/pathlib",
    "std/time",
)

REMAINING_NONCPP_GENERATED_COMPARE_UTILS_MODULES_V1: Final[tuple[str, ...]] = (
    "utils/gif",
    "utils/png",
)

REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1: Final[tuple[str, ...]] = (
    REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1
    + REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1
    + REMAINING_NONCPP_GENERATED_COMPARE_UTILS_MODULES_V1
)


REMAINING_NONCPP_RUNTIME_LAYOUT_V1: Final[tuple[RemainingRuntimeBackendMappingEntry, ...]] = (
    {
        "backend": "go",
        "family": "static",
        "runtime_hook_key": "go",
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/go/native/built_in/",
                "target_prefix": "src/runtime/go/native/built_in/",
                "ownership": "native",
                "rationale": "Go handwritten runtime substrate already lives in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/go/generated/utils/",
                "target_prefix": "src/runtime/go/generated/utils/",
                "ownership": "generated",
                "rationale": "Go image helpers already live in the canonical generated/utils lane after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "target_prefix": "src/runtime/go/pytra/built_in/py_runtime.go",
                "ownership": "compat",
                "rationale": "The public Go runtime shim has already been normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "java",
        "family": "static",
        "runtime_hook_key": "java",
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/java/native/built_in/",
                "target_prefix": "src/runtime/java/native/built_in/",
                "ownership": "native",
                "rationale": "Java handwritten runtime helpers already live in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/java/native/std/",
                "target_prefix": "src/runtime/java/native/std/",
                "ownership": "native",
                "rationale": "Java handwritten std seams already live in native/std after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/java/generated/std/",
                "target_prefix": "src/runtime/java/generated/std/",
                "ownership": "generated",
                "rationale": "Java SoT-generated std compare artifacts already live in generated/std after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/java/generated/utils/",
                "target_prefix": "src/runtime/java/generated/utils/",
                "ownership": "generated",
                "rationale": "Java image helpers already live in the canonical generated/utils lane after the Wave A path cutover.",
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
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/kotlin/native/built_in/",
                "target_prefix": "src/runtime/kotlin/native/built_in/",
                "ownership": "native",
                "rationale": "Kotlin handwritten runtime substrate already lives in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/kotlin/generated/utils/",
                "target_prefix": "src/runtime/kotlin/generated/utils/",
                "ownership": "generated",
                "rationale": "Kotlin image helpers already live in generated/utils after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/kotlin/pytra/built_in/py_runtime.kt",
                "target_prefix": "src/runtime/kotlin/pytra/built_in/py_runtime.kt",
                "ownership": "compat",
                "rationale": "Kotlin public shim has already been normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "scala",
        "family": "static",
        "runtime_hook_key": "scala",
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/scala/native/built_in/",
                "target_prefix": "src/runtime/scala/native/built_in/",
                "ownership": "native",
                "rationale": "Scala handwritten runtime substrate already lives in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/scala/generated/utils/",
                "target_prefix": "src/runtime/scala/generated/utils/",
                "ownership": "generated",
                "rationale": "Scala image helpers already live in generated/utils after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/scala/pytra/built_in/py_runtime.scala",
                "target_prefix": "src/runtime/scala/pytra/built_in/py_runtime.scala",
                "ownership": "compat",
                "rationale": "Scala public shim has already been normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "swift",
        "family": "static",
        "runtime_hook_key": "swift",
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/swift/native/built_in/",
                "target_prefix": "src/runtime/swift/native/built_in/",
                "ownership": "native",
                "rationale": "Swift handwritten runtime substrate already lives in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/swift/generated/utils/",
                "target_prefix": "src/runtime/swift/generated/utils/",
                "ownership": "generated",
                "rationale": "Swift image helpers already live in generated/utils after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/swift/pytra/built_in/py_runtime.swift",
                "target_prefix": "src/runtime/swift/pytra/built_in/py_runtime.swift",
                "ownership": "compat",
                "rationale": "Swift public shim has already been normalized into pytra/built_in.",
            },
        ),
    },
    {
        "backend": "nim",
        "family": "static",
        "runtime_hook_key": "nim",
        "current_roots": ("generated", "native", "pytra"),
        "target_roots": ("generated", "native", "pytra"),
        "lane_mappings": (
            {
                "current_prefix": "src/runtime/nim/native/built_in/",
                "target_prefix": "src/runtime/nim/native/built_in/",
                "ownership": "native",
                "rationale": "Nim handwritten runtime substrate already lives in native/built_in after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/nim/generated/utils/",
                "target_prefix": "src/runtime/nim/generated/utils/",
                "ownership": "generated",
                "rationale": "Nim image helpers already live in generated/utils after the Wave A path cutover.",
            },
            {
                "current_prefix": "src/runtime/nim/pytra/built_in/py_runtime.nim",
                "target_prefix": "src/runtime/nim/pytra/built_in/py_runtime.nim",
                "ownership": "compat",
                "rationale": "Nim public shim has already been normalized into pytra/built_in.",
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


REMAINING_NONCPP_RUNTIME_CURRENT_INVENTORY_V1: Final[tuple[RemainingRuntimeCurrentInventoryEntry, ...]] = (
    {
        "backend": "go",
        "pytra_core_files": ("built_in/py_runtime.go",),
        "pytra_gen_files": ("utils/gif.go", "utils/png.go"),
        "pytra_files": ("built_in/py_runtime.go",),
    },
    {
        "backend": "java",
        "pytra_core_files": (
            "built_in/PyRuntime.java",
            "std/math_impl.java",
            "std/time_impl.java",
        ),
        "pytra_gen_files": (
            "std/json.java",
            "std/math.java",
            "std/pathlib.java",
            "std/time.java",
            "utils/gif.java",
            "utils/png.java",
        ),
        "pytra_files": ("built_in/PyRuntime.java",),
    },
    {
        "backend": "kotlin",
        "pytra_core_files": ("built_in/py_runtime.kt",),
        "pytra_gen_files": (
            "utils/gif_helper.kt",
            "utils/image_runtime.kt",
            "utils/png_helper.kt",
        ),
        "pytra_files": ("built_in/py_runtime.kt",),
    },
    {
        "backend": "scala",
        "pytra_core_files": ("built_in/py_runtime.scala",),
        "pytra_gen_files": (
            "utils/gif_helper.scala",
            "utils/image_runtime.scala",
            "utils/png_helper.scala",
        ),
        "pytra_files": ("built_in/py_runtime.scala",),
    },
    {
        "backend": "swift",
        "pytra_core_files": ("built_in/py_runtime.swift",),
        "pytra_gen_files": (
            "utils/gif_helper.swift",
            "utils/image_runtime.swift",
            "utils/png_helper.swift",
        ),
        "pytra_files": ("built_in/py_runtime.swift",),
    },
    {
        "backend": "nim",
        "pytra_core_files": ("built_in/py_runtime.nim",),
        "pytra_gen_files": (
            "utils/gif_helper.nim",
            "utils/image_runtime.nim",
            "utils/png_helper.nim",
        ),
        "pytra_files": ("built_in/py_runtime.nim",),
    },
    {
        "backend": "js",
        "pytra_core_files": (
            "built_in/py_runtime.js",
            "std/math.js",
            "std/pathlib.js",
            "std/time.js",
        ),
        "pytra_gen_files": ("utils/gif.js", "utils/png.js"),
        "pytra_files": (
            "README.md",
            "gif.js",
            "math.js",
            "pathlib.js",
            "png.js",
            "py_runtime.js",
            "time.js",
        ),
    },
    {
        "backend": "ts",
        "pytra_core_files": (
            "built_in/py_runtime.ts",
            "std/math.ts",
            "std/pathlib.ts",
            "std/time.ts",
        ),
        "pytra_gen_files": ("utils/gif.ts", "utils/png.ts"),
        "pytra_files": (
            "README.md",
            "gif_helper.ts",
            "math.ts",
            "pathlib.ts",
            "png_helper.ts",
            "py_runtime.ts",
            "time.ts",
        ),
    },
    {
        "backend": "lua",
        "pytra_core_files": ("built_in/py_runtime.lua",),
        "pytra_gen_files": (
            "utils/gif_helper.lua",
            "utils/image_runtime.lua",
            "utils/png_helper.lua",
        ),
        "pytra_files": ("py_runtime.lua",),
    },
    {
        "backend": "ruby",
        "pytra_core_files": ("built_in/py_runtime.rb",),
        "pytra_gen_files": (
            "utils/gif_helper.rb",
            "utils/image_runtime.rb",
            "utils/png_helper.rb",
        ),
        "pytra_files": ("py_runtime.rb",),
    },
    {
        "backend": "php",
        "pytra_core_files": ("py_runtime.php", "std/time.php"),
        "pytra_gen_files": ("runtime/gif.php", "runtime/png.php"),
        "pytra_files": (
            "py_runtime.php",
            "runtime/gif.php",
            "runtime/png.php",
            "std/time.php",
        ),
    },
)


REMAINING_NONCPP_RUNTIME_TARGET_INVENTORY_V1: Final[tuple[RemainingRuntimeTargetInventoryEntry, ...]] = (
    {
        "backend": "go",
        "generated_files": ("generated/utils/gif.go", "generated/utils/png.go"),
        "native_files": ("native/built_in/py_runtime.go",),
        "compat_files": ("pytra/built_in/py_runtime.go",),
    },
    {
        "backend": "java",
        "generated_files": (
            "generated/std/json.java",
            "generated/std/math.java",
            "generated/std/pathlib.java",
            "generated/std/time.java",
            "generated/utils/gif.java",
            "generated/utils/png.java",
        ),
        "native_files": (
            "native/built_in/PyRuntime.java",
            "native/std/math_impl.java",
            "native/std/time_impl.java",
        ),
        "compat_files": ("pytra/built_in/PyRuntime.java",),
    },
    {
        "backend": "kotlin",
        "generated_files": (
            "generated/utils/gif_helper.kt",
            "generated/utils/image_runtime.kt",
            "generated/utils/png_helper.kt",
        ),
        "native_files": ("native/built_in/py_runtime.kt",),
        "compat_files": ("pytra/built_in/py_runtime.kt",),
    },
    {
        "backend": "scala",
        "generated_files": (
            "generated/utils/gif_helper.scala",
            "generated/utils/image_runtime.scala",
            "generated/utils/png_helper.scala",
        ),
        "native_files": ("native/built_in/py_runtime.scala",),
        "compat_files": ("pytra/built_in/py_runtime.scala",),
    },
    {
        "backend": "swift",
        "generated_files": (
            "generated/utils/gif_helper.swift",
            "generated/utils/image_runtime.swift",
            "generated/utils/png_helper.swift",
        ),
        "native_files": ("native/built_in/py_runtime.swift",),
        "compat_files": ("pytra/built_in/py_runtime.swift",),
    },
    {
        "backend": "nim",
        "generated_files": (
            "generated/utils/gif_helper.nim",
            "generated/utils/image_runtime.nim",
            "generated/utils/png_helper.nim",
        ),
        "native_files": ("native/built_in/py_runtime.nim",),
        "compat_files": ("pytra/built_in/py_runtime.nim",),
    },
    {
        "backend": "js",
        "generated_files": ("generated/utils/gif.js", "generated/utils/png.js"),
        "native_files": (
            "native/built_in/py_runtime.js",
            "native/std/math.js",
            "native/std/pathlib.js",
            "native/std/time.js",
        ),
        "compat_files": (
            "pytra/README.md",
            "pytra/py_runtime.js",
            "pytra/std/math.js",
            "pytra/std/pathlib.js",
            "pytra/std/time.js",
            "pytra/utils/gif.js",
            "pytra/utils/png.js",
        ),
    },
    {
        "backend": "ts",
        "generated_files": ("generated/utils/gif.ts", "generated/utils/png.ts"),
        "native_files": (
            "native/built_in/py_runtime.ts",
            "native/std/math.ts",
            "native/std/pathlib.ts",
            "native/std/time.ts",
        ),
        "compat_files": (
            "pytra/README.md",
            "pytra/py_runtime.ts",
            "pytra/std/math.ts",
            "pytra/std/pathlib.ts",
            "pytra/std/time.ts",
            "pytra/utils/gif.ts",
            "pytra/utils/png.ts",
        ),
    },
    {
        "backend": "lua",
        "generated_files": (
            "generated/utils/gif_helper.lua",
            "generated/utils/image_runtime.lua",
            "generated/utils/png_helper.lua",
        ),
        "native_files": ("native/built_in/py_runtime.lua",),
        "compat_files": ("pytra/built_in/py_runtime.lua",),
    },
    {
        "backend": "ruby",
        "generated_files": (
            "generated/utils/gif_helper.rb",
            "generated/utils/image_runtime.rb",
            "generated/utils/png_helper.rb",
        ),
        "native_files": ("native/built_in/py_runtime.rb",),
        "compat_files": ("pytra/built_in/py_runtime.rb",),
    },
    {
        "backend": "php",
        "generated_files": ("generated/utils/gif.php", "generated/utils/png.php"),
        "native_files": ("native/built_in/py_runtime.php", "native/std/time.php"),
        "compat_files": (
            "pytra/py_runtime.php",
            "pytra/std/time.php",
            "pytra/utils/gif.php",
            "pytra/utils/png.php",
        ),
    },
)


REMAINING_NONCPP_RUNTIME_MODULE_BUCKETS_V1: Final[tuple[RemainingRuntimeModuleBucketEntry, ...]] = (
    {
        "backend": "go",
        "generated_modules": ("utils/gif", "utils/png"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": (
            REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1
            + REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1
        ),
    },
    {
        "backend": "java",
        "generated_modules": (
            "std/json",
            "std/math",
            "std/pathlib",
            "std/time",
            "utils/gif",
            "utils/png",
        ),
        "native_modules": ("built_in/py_runtime", "std/math", "std/time"),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1,
    },
    {
        "backend": "kotlin",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "scala",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "swift",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "nim",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "js",
        "generated_modules": ("utils/gif", "utils/png"),
        "native_modules": ("built_in/py_runtime", "std/math", "std/pathlib", "std/time"),
        "compat_modules": (
            "built_in/py_runtime",
            "std/math",
            "std/pathlib",
            "std/time",
            "utils/gif",
            "utils/png",
        ),
        "blocked_modules": (
            REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1
            + REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1
        ),
    },
    {
        "backend": "ts",
        "generated_modules": ("utils/gif", "utils/png"),
        "native_modules": ("built_in/py_runtime", "std/math", "std/pathlib", "std/time"),
        "compat_modules": (
            "built_in/py_runtime",
            "std/math",
            "std/pathlib",
            "std/time",
            "utils/gif",
            "utils/png",
        ),
        "blocked_modules": (
            REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1
            + REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1
        ),
    },
    {
        "backend": "lua",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "ruby",
        "generated_modules": ("utils/gif_helper", "utils/image_runtime", "utils/png_helper"),
        "native_modules": ("built_in/py_runtime",),
        "compat_modules": ("built_in/py_runtime",),
        "blocked_modules": REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1,
    },
    {
        "backend": "php",
        "generated_modules": ("utils/gif", "utils/png"),
        "native_modules": ("built_in/py_runtime", "std/time"),
        "compat_modules": ("built_in/py_runtime", "std/time", "utils/gif", "utils/png"),
        "blocked_modules": (
            REMAINING_NONCPP_GENERATED_COMPARE_BUILT_IN_MODULES_V1
            + REMAINING_NONCPP_GENERATED_COMPARE_STD_MODULES_V1
        ),
    },
)


REMAINING_NONCPP_RUNTIME_WAVE_A_HOOK_SOURCES_V1: Final[
    tuple[RemainingRuntimeWaveAHookSourceEntry, ...]
] = (
    {
        "backend": "go",
        "runtime_hook_files": (
            "runtime/go/native/built_in/py_runtime.go",
            "runtime/go/generated/utils/png.go",
            "runtime/go/generated/utils/gif.go",
        ),
    },
    {
        "backend": "java",
        "runtime_hook_files": (
            "runtime/java/native/built_in/PyRuntime.java",
            "runtime/java/native/std/time_impl.java",
            "runtime/java/native/std/math_impl.java",
            "runtime/java/generated/utils/png.java",
            "runtime/java/generated/utils/gif.java",
            "runtime/java/generated/std/time.java",
            "runtime/java/generated/std/json.java",
            "runtime/java/generated/std/pathlib.java",
            "runtime/java/generated/std/math.java",
        ),
    },
    {
        "backend": "kotlin",
        "runtime_hook_files": (
            "runtime/kotlin/native/built_in/py_runtime.kt",
            "runtime/kotlin/generated/utils/image_runtime.kt",
        ),
    },
    {
        "backend": "scala",
        "runtime_hook_files": (
            "runtime/scala/native/built_in/py_runtime.scala",
            "runtime/scala/generated/utils/image_runtime.scala",
        ),
    },
    {
        "backend": "swift",
        "runtime_hook_files": (
            "runtime/swift/native/built_in/py_runtime.swift",
            "runtime/swift/generated/utils/image_runtime.swift",
        ),
    },
    {
        "backend": "nim",
        "runtime_hook_files": (
            "runtime/nim/native/built_in/py_runtime.nim",
            "runtime/nim/generated/utils/image_runtime.nim",
        ),
    },
)


def iter_remaining_noncpp_backend_order() -> tuple[str, ...]:
    return REMAINING_NONCPP_BACKEND_ORDER_V1


def iter_remaining_noncpp_runtime_layout() -> tuple[RemainingRuntimeBackendMappingEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_LAYOUT_V1


def iter_remaining_noncpp_runtime_current_inventory() -> tuple[RemainingRuntimeCurrentInventoryEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_CURRENT_INVENTORY_V1


def iter_remaining_noncpp_runtime_target_inventory() -> tuple[RemainingRuntimeTargetInventoryEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_TARGET_INVENTORY_V1


def iter_remaining_noncpp_runtime_generated_compare_baseline() -> tuple[str, ...]:
    return REMAINING_NONCPP_GENERATED_COMPARE_BASELINE_V1


def iter_remaining_noncpp_runtime_module_buckets() -> tuple[RemainingRuntimeModuleBucketEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_MODULE_BUCKETS_V1


def iter_remaining_noncpp_runtime_wave_a_hook_sources() -> tuple[RemainingRuntimeWaveAHookSourceEntry, ...]:
    return REMAINING_NONCPP_RUNTIME_WAVE_A_HOOK_SOURCES_V1

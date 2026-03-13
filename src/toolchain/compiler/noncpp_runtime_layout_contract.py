"""Legacy rs/cs runtime generated/native inventory before cpp-generated baseline parity."""

from __future__ import annotations

from typing import Final, TypedDict


class CsStdLaneOwnershipEntry(TypedDict):
    module_name: str
    canonical_lane: str
    generated_std_state: str
    generated_std_rel: str
    native_rel: str
    canonical_runtime_symbol: str
    representative_fixture: str
    smoke_guard_needles: tuple[str, ...]
    rationale: str


class CsStdFirstLiveGeneratedCandidateEntry(TypedDict):
    module_name: str
    current_canonical_lane: str
    generated_std_rel: str
    native_rel: str
    representative_fixture: str
    smoke_guard_needles: tuple[str, ...]
    deferred_native_canonical_modules: tuple[str, ...]
    deferred_no_runtime_modules: tuple[str, ...]
    rationale: str


class RsStdLaneOwnershipEntry(TypedDict):
    module_name: str
    canonical_lane: str
    generated_std_state: str
    generated_std_rel: str
    native_rel: str
    canonical_runtime_symbol: str
    representative_fixture: str
    smoke_guard_needles: tuple[str, ...]
    rationale: str


NONCPP_GENERATED_BUILTIN_MODULES_V1: Final[tuple[str, ...]] = (
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

CS_NATIVE_BUILTIN_RESIDUAL_MODULES_V1: Final[tuple[str, ...]] = (
    "py_runtime",
)

RS_NATIVE_BUILTIN_RESIDUAL_MODULES_V1: Final[tuple[str, ...]] = ("py_runtime",)

CS_PYTRA_DUPLICATE_DELETE_TARGETS_V1: Final[tuple[str, ...]] = (
    "src/runtime/cs/pytra/built_in/math.cs",
    "src/runtime/cs/pytra/built_in/py_runtime.cs",
    "src/runtime/cs/pytra/built_in/time.cs",
    "src/runtime/cs/pytra/std/json.cs",
    "src/runtime/cs/pytra/std/pathlib.cs",
    "src/runtime/cs/pytra/utils/gif.cs",
    "src/runtime/cs/pytra/utils/png.cs",
)

CS_PYTRA_GENERATED_DUPLICATE_DELETE_TARGETS_V1: Final[tuple[str, ...]] = (
    "src/runtime/cs/pytra/utils/gif.cs",
    "src/runtime/cs/pytra/utils/png.cs",
)

CS_PYTRA_HANDWRITTEN_DUPLICATE_DELETE_TARGETS_V1: Final[tuple[str, ...]] = (
    "src/runtime/cs/pytra/built_in/math.cs",
    "src/runtime/cs/pytra/built_in/py_runtime.cs",
    "src/runtime/cs/pytra/built_in/time.cs",
    "src/runtime/cs/pytra/std/json.cs",
    "src/runtime/cs/pytra/std/pathlib.cs",
)

RS_PYTRA_COMPAT_ALLOWLIST_V1: Final[tuple[str, ...]] = (
    "src/runtime/rs/pytra/README.md",
    "src/runtime/rs/pytra/built_in/py_runtime.rs",
    "src/runtime/rs/pytra/compiler/README.md",
    "src/runtime/rs/pytra/std/README.md",
    "src/runtime/rs/pytra/utils/README.md",
)


CS_STD_GENERATED_STATE_ORDER: Final[tuple[str, ...]] = (
    "canonical_generated",
    "compare_artifact",
    "blocked",
    "no_runtime_module",
)

CS_STD_CANONICAL_LANE_ORDER: Final[tuple[str, ...]] = (
    "generated/std",
    "native/std",
    "native/built_in",
    "no_runtime_module",
)

RS_STD_GENERATED_STATE_ORDER: Final[tuple[str, ...]] = CS_STD_GENERATED_STATE_ORDER
RS_STD_CANONICAL_LANE_ORDER: Final[tuple[str, ...]] = CS_STD_CANONICAL_LANE_ORDER

CS_STD_LANE_OWNERSHIP_V1: Final[tuple[CsStdLaneOwnershipEntry, ...]] = (
    {
        "module_name": "time",
        "canonical_lane": "generated/std",
        "generated_std_state": "canonical_generated",
        "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
        "native_rel": "src/runtime/cs/native/std/time_native.cs",
        "canonical_runtime_symbol": "Pytra.CsModule.time",
        "representative_fixture": "test/fixtures/imports/import_time_from.py",
        "smoke_guard_needles": (
            "def test_representative_time_import_fixture_transpiles",
            "Pytra.CsModule.time.perf_counter()",
        ),
        "rationale": "generated/std/time.cs is the first live-generated C# std lane, while native/std/time_native.cs remains only as the backing seam referenced by the generated wrapper.",
    },
    {
        "module_name": "json",
        "canonical_lane": "generated/std",
        "generated_std_state": "canonical_generated",
        "generated_std_rel": "src/runtime/cs/generated/std/json.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "Pytra.CsModule.json",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
        "smoke_guard_needles": (
            "def test_representative_json_extended_fixture_transpiles",
            "Pytra.CsModule.json.loads(s)",
        ),
        "rationale": "generated/std/json.cs is now the live C# JSON owner and ships the wrapper-shaped `Pytra.CsModule.json` surface directly from generated code without a handwritten native/std owner.",
    },
    {
        "module_name": "pathlib",
        "canonical_lane": "generated/std",
        "generated_std_state": "canonical_generated",
        "generated_std_rel": "src/runtime/cs/generated/std/pathlib.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "Pytra.CsModule.py_path",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (
            "def test_representative_pathlib_extended_fixture_transpiles",
            "using Path = Pytra.CsModule.py_path;",
        ),
        "rationale": "generated/std/pathlib.cs is now the live C# pathlib owner and ships the wrapper-shaped `Pytra.CsModule.py_path` surface directly from generated code without a handwritten native/std owner.",
    },
    {
        "module_name": "math",
        "canonical_lane": "generated/std",
        "generated_std_state": "canonical_generated",
        "generated_std_rel": "src/runtime/cs/generated/std/math.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "Pytra.CsModule.math",
        "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
        "smoke_guard_needles": (
            "def test_representative_math_import_fixture_transpiles",
            "Pytra.CsModule.math.sqrt(81.0)",
        ),
        "rationale": "generated/std/math.cs is now the live C# math owner and maps the extern-marked SoT surface directly onto System.Math without a handwritten native seam.",
    },
    {
        "module_name": "random",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/random.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/random_timeit_traceback_extended.py",
        "smoke_guard_needles": (
            "def test_representative_random_timeit_traceback_fixture_transpiles",
            "long v2 = System.Convert.ToInt64(random.randint(1, 3));",
        ),
        "rationale": "generated/std/random.cs now exists for compare, but the current C# representative lane still transpiles without shipping a dedicated live random runtime module.",
    },
    {
        "module_name": "re",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/re.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
        "smoke_guard_needles": (
            "def test_representative_re_extended_fixture_transpiles",
            'string py_out = System.Convert.ToString(sub("\\\\\\\\s+", " ", "a   b\\\\tc"));',
        ),
        "rationale": "generated/std/re.cs now exists for compare, but the current C# representative lane still transpiles without shipping a dedicated live re runtime module.",
    },
    {
        "module_name": "argparse",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/argparse.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
        "smoke_guard_needles": (
            "def test_representative_argparse_extended_fixture_transpiles",
            'ArgumentParser p = ArgumentParser("x");',
        ),
        "rationale": "generated/std/argparse.cs now exists for compare, but the current C# representative lane still transpiles without shipping a dedicated live argparse runtime module.",
    },
    {
        "module_name": "sys",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/sys.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/sys_extended.py",
        "smoke_guard_needles": (
            "def test_representative_sys_extended_fixture_transpiles",
            'sys.set_argv(new System.Collections.Generic.List<string> { "a", "b" });',
        ),
        "rationale": "generated/std/sys.cs now exists for compare, but the current C# representative lane still transpiles without shipping a dedicated live sys runtime module.",
    },
    {
        "module_name": "timeit",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/timeit.cs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/random_timeit_traceback_extended.py",
        "smoke_guard_needles": (
            "def test_representative_random_timeit_traceback_fixture_transpiles",
            "using timer = Pytra.CsModule.default_timer;",
        ),
        "rationale": "generated/std/timeit.cs now exists for compare, but the current C# representative lane still transpiles without shipping a dedicated live timeit runtime module.",
    },
    {
        "module_name": "enum",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/enum_extended.py",
        "smoke_guard_needles": (
            "def test_representative_enum_extended_fixture_transpiles",
            "public class Color : Enum",
            "public class Perm : IntFlag",
        ),
        "rationale": "the current C# representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/std.",
    },
)

CS_STD_FIRST_LIVE_GENERATED_CANDIDATE_V1: Final[CsStdFirstLiveGeneratedCandidateEntry] = {
    "module_name": "time",
    "current_canonical_lane": "generated/std",
    "generated_std_rel": "src/runtime/cs/generated/std/time.cs",
    "native_rel": "src/runtime/cs/native/std/time_native.cs",
    "representative_fixture": "test/fixtures/imports/import_time_from.py",
    "smoke_guard_needles": (
        "def test_representative_time_import_fixture_transpiles",
        "Pytra.CsModule.time.perf_counter()",
    ),
    "deferred_native_canonical_modules": (),
    "deferred_no_runtime_modules": ("random", "re", "argparse", "sys", "timeit", "enum"),
    "rationale": "time/math/json/pathlib are now live-generated C# std lanes; the remaining C# std migration debt is limited to no-runtime representative modules that still transpile without dedicated runtime owners.",
}

RS_STD_LANE_OWNERSHIP_V1: Final[tuple[RsStdLaneOwnershipEntry, ...]] = (
    {
        "module_name": "time",
        "canonical_lane": "native/built_in",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/time.rs",
        "native_rel": "src/runtime/rs/native/built_in/py_runtime.rs",
        "canonical_runtime_symbol": "pub use super::super::time;",
        "representative_fixture": "test/fixtures/imports/import_time_from.py",
        "smoke_guard_needles": (
            "def test_runtime_scaffold_exposes_pytra_std_time_and_math",
        ),
        "rationale": "generated/std/time.rs exists for compare, but the live Rust runtime still comes from the native built_in scaffold re-export in py_runtime.rs.",
    },
    {
        "module_name": "math",
        "canonical_lane": "native/built_in",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/math.rs",
        "native_rel": "src/runtime/rs/native/built_in/py_runtime.rs",
        "canonical_runtime_symbol": "pub use super::super::math;",
        "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
        "smoke_guard_needles": (
            "def test_imports_emit_use_lines",
            "use crate::pytra::std::math::floor;",
        ),
        "rationale": "generated/std/math.rs exists for compare, but the live Rust runtime still comes from the native built_in scaffold re-export in py_runtime.rs.",
    },
    {
        "module_name": "pathlib",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/pathlib.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (
            "def test_representative_pathlib_extended_fixture_transpiles",
            "use crate::pytra::std::pathlib::Path;",
        ),
        "rationale": "generated/std/pathlib.rs exists for compare, but the current Rust lane is still transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "os",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/os.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (),
        "rationale": "generated/std/os.rs exists for compare, but the current Rust lane is still transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "os_path",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/os_path.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (),
        "rationale": "generated/std/os_path.rs exists for compare, but the current Rust lane is still transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "glob",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/glob.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (),
        "rationale": "generated/std/glob.rs exists for compare, but the current Rust lane is still transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "json",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/json.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
        "smoke_guard_needles": (
            "def test_representative_json_extended_fixture_transpiles",
            "use crate::pytra::std::json::dumps;",
        ),
        "rationale": "generated/std/json.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "random",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/random.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/random_timeit_traceback_extended.py",
        "smoke_guard_needles": (
            "def test_representative_random_timeit_traceback_fixture_transpiles",
            "let v2: i64 = py_any_to_i64(&pytra::std::random::randint(1, 3));",
        ),
        "rationale": "generated/std/random.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "re",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/re.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
        "smoke_guard_needles": (
            "def test_representative_re_extended_fixture_transpiles",
            "use crate::pytra::std::re::sub;",
        ),
        "rationale": "generated/std/re.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "argparse",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/argparse.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
        "smoke_guard_needles": (
            "def test_representative_argparse_extended_fixture_transpiles",
            "use crate::pytra::std::argparse::ArgumentParser;",
        ),
        "rationale": "generated/std/argparse.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "sys",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/sys.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/sys_extended.py",
        "smoke_guard_needles": (
            "def test_representative_sys_extended_fixture_transpiles",
            'pytra::std::sys::set_argv((vec![("a").to_string(), ("b").to_string()]).clone());',
        ),
        "rationale": "generated/std/sys.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "timeit",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/rs/generated/std/timeit.rs",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/random_timeit_traceback_extended.py",
        "smoke_guard_needles": (
            "def test_representative_random_timeit_traceback_fixture_transpiles",
            "use crate::pytra::std::timeit::default_timer as timer;",
        ),
        "rationale": "generated/std/timeit.rs now exists for compare, but the current Rust representative remains transpile-only and does not ship a live runtime module.",
    },
    {
        "module_name": "enum",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/enum_extended.py",
        "smoke_guard_needles": (
            "def test_representative_enum_extended_fixture_transpiles",
            "trait __pytra_trait_Color",
        ),
        "rationale": "the current Rust representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/built_in.",
    },
)


def iter_cs_std_lane_ownership() -> tuple[CsStdLaneOwnershipEntry, ...]:
    return CS_STD_LANE_OWNERSHIP_V1


def get_cs_std_first_live_generated_candidate() -> CsStdFirstLiveGeneratedCandidateEntry:
    return CS_STD_FIRST_LIVE_GENERATED_CANDIDATE_V1


def iter_rs_std_lane_ownership() -> tuple[RsStdLaneOwnershipEntry, ...]:
    return RS_STD_LANE_OWNERSHIP_V1


def iter_noncpp_generated_builtin_modules() -> tuple[str, ...]:
    return NONCPP_GENERATED_BUILTIN_MODULES_V1


def iter_cs_native_builtin_residual_modules() -> tuple[str, ...]:
    return CS_NATIVE_BUILTIN_RESIDUAL_MODULES_V1


def iter_rs_native_builtin_residual_modules() -> tuple[str, ...]:
    return RS_NATIVE_BUILTIN_RESIDUAL_MODULES_V1


def iter_cs_pytra_duplicate_delete_targets() -> tuple[str, ...]:
    return CS_PYTRA_DUPLICATE_DELETE_TARGETS_V1


def iter_cs_pytra_generated_duplicate_delete_targets() -> tuple[str, ...]:
    return CS_PYTRA_GENERATED_DUPLICATE_DELETE_TARGETS_V1


def iter_cs_pytra_handwritten_duplicate_delete_targets() -> tuple[str, ...]:
    return CS_PYTRA_HANDWRITTEN_DUPLICATE_DELETE_TARGETS_V1


def iter_rs_pytra_compat_allowlist() -> tuple[str, ...]:
    return RS_PYTRA_COMPAT_ALLOWLIST_V1

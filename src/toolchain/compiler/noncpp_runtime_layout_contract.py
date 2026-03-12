"""Contracts for non-C++ runtime generated/native lane ownership."""

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
    "math",
    "py_runtime",
    "time",
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
        "native_rel": "src/runtime/cs/native/built_in/time.cs",
        "canonical_runtime_symbol": "Pytra.CsModule.time",
        "representative_fixture": "test/fixtures/imports/import_time_from.py",
        "smoke_guard_needles": (
            "def test_representative_time_import_fixture_transpiles",
            "Pytra.CsModule.time.perf_counter()",
        ),
        "rationale": "generated/std/time.cs is the first live-generated C# std lane, while native/built_in/time.cs remains only as the backing seam referenced by the generated wrapper.",
    },
    {
        "module_name": "json",
        "canonical_lane": "native/std",
        "generated_std_state": "blocked",
        "generated_std_rel": "",
        "native_rel": "src/runtime/cs/native/std/json.cs",
        "canonical_runtime_symbol": "Pytra.CsModule.json",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
        "smoke_guard_needles": (
            "def test_representative_json_extended_fixture_transpiles",
            "Pytra.CsModule.json.loads(s)",
        ),
        "rationale": "json.py cannot yet generate the C# runtime lane because the current ABI/object contract is still handwritten.",
    },
    {
        "module_name": "pathlib",
        "canonical_lane": "native/std",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/pathlib.cs",
        "native_rel": "src/runtime/cs/native/std/pathlib.cs",
        "canonical_runtime_symbol": "Pytra.CsModule.py_path",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "smoke_guard_needles": (
            "def test_representative_pathlib_extended_fixture_transpiles",
            "using Path = Pytra.CsModule.py_path;",
        ),
        "rationale": "generated/std/pathlib.cs exists for compare, but the build profile and emitter still route the live C# runtime to native/std/pathlib.cs.",
    },
    {
        "module_name": "math",
        "canonical_lane": "native/built_in",
        "generated_std_state": "compare_artifact",
        "generated_std_rel": "src/runtime/cs/generated/std/math.cs",
        "native_rel": "src/runtime/cs/native/built_in/math.cs",
        "canonical_runtime_symbol": "Pytra.CsModule.math",
        "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
        "smoke_guard_needles": (
            "def test_representative_math_import_fixture_transpiles",
            "Pytra.CsModule.math.sqrt(81.0)",
        ),
        "rationale": "generated/std/math.cs exists for compare, but live C# builds still compile the handwritten native built_in math lane.",
    },
    {
        "module_name": "re",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
        "smoke_guard_needles": (
            "def test_representative_re_extended_fixture_transpiles",
            'string py_out = System.Convert.ToString(sub("\\\\\\\\s+", " ", "a   b\\\\tc"));',
        ),
        "rationale": "the current C# representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/std.",
    },
    {
        "module_name": "argparse",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
        "smoke_guard_needles": (
            "def test_representative_argparse_extended_fixture_transpiles",
            'ArgumentParser p = ArgumentParser("x");',
        ),
        "rationale": "the current C# representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/std.",
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
    "native_rel": "src/runtime/cs/native/built_in/time.cs",
    "representative_fixture": "test/fixtures/imports/import_time_from.py",
    "smoke_guard_needles": (
        "def test_representative_time_import_fixture_transpiles",
        "Pytra.CsModule.time.perf_counter()",
    ),
    "deferred_native_canonical_modules": ("json", "pathlib", "math"),
    "deferred_no_runtime_modules": ("re", "argparse", "enum"),
    "rationale": "time is the first live-generated C# std lane because its representative surface is a single `perf_counter()` wrapper, while `json` remains blocked and `pathlib/math` still depend on heavier native canonical seams.",
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
        "generated_std_state": "blocked",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
        "smoke_guard_needles": (
            "def test_representative_json_extended_fixture_transpiles",
            "use crate::pytra::std::json::dumps;",
        ),
        "rationale": "json.py does not yet emit an rs generated/std lane, and the current Rust representative remains transpile-only.",
    },
    {
        "module_name": "re",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
        "smoke_guard_needles": (
            "def test_representative_re_extended_fixture_transpiles",
            "use crate::pytra::std::re::sub;",
        ),
        "rationale": "the current Rust representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/built_in.",
    },
    {
        "module_name": "argparse",
        "canonical_lane": "no_runtime_module",
        "generated_std_state": "no_runtime_module",
        "generated_std_rel": "",
        "native_rel": "",
        "canonical_runtime_symbol": "",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
        "smoke_guard_needles": (
            "def test_representative_argparse_extended_fixture_transpiles",
            "use crate::pytra::std::argparse::ArgumentParser;",
        ),
        "rationale": "the current Rust representative lane is transpile-only and does not own a dedicated runtime module under generated/std or native/built_in.",
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

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

CS_STD_LANE_OWNERSHIP_V1: Final[tuple[CsStdLaneOwnershipEntry, ...]] = (
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


def iter_cs_std_lane_ownership() -> tuple[CsStdLaneOwnershipEntry, ...]:
    return CS_STD_LANE_OWNERSHIP_V1

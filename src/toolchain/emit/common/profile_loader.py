"""Language/lowering profile loader for toolchain2 emitters."""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std.json import JsonVal

_PROFILE_DOC_CACHE: dict[str, dict[str, JsonVal]] = {}

_VALID_TUPLE_UNPACK_STYLES: set[str] = {
    "subscript",
    "structured_binding",
    "pattern_match",
    "multi_return",
    "individual_temps",
}
_VALID_CLOSURE_STYLES: set[str] = {
    "native_nested",
    "closure_syntax",
}
_VALID_WITH_STYLES: set[str] = {
    "raii",
    "try_with_resources",
    "using",
    "defer",
    "try_finally",
}
_VALID_PROPERTY_STYLES: set[str] = {
    "field_access",
    "method_call",
}
_VALID_SWAP_STYLES: set[str] = {
    "std_swap",
    "multi_assign",
    "mem_swap",
    "temp_var",
}
_VALID_EXCEPTION_STYLES: set[str] = {
    "native_throw",
    "union_return",
    "panic_catch_unwind",
    "manual_exception_slot",
}


@dataclass
class LoweringProfile:
    tuple_unpack_style: str
    container_covariance: bool
    closure_style: str
    with_style: str
    property_style: str
    swap_style: str
    exception_style: str


def _default_profile_doc() -> dict[str, JsonVal]:
    lowering: dict[str, JsonVal] = {
        "tuple_unpack_style": "subscript",
        "container_covariance": False,
        "closure_style": "native_nested",
        "with_style": "try_finally",
        "property_style": "field_access",
        "swap_style": "temp_var",
        "exception_style": "native_throw",
    }
    return {
        "schema_version": 1,
        "lowering": lowering,
    }



def load_profile_with_includes(profile_path: object) -> dict[str, JsonVal]:
    _ = profile_path
    return _default_profile_doc()



def _validate_enum(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise RuntimeError("invalid lowering profile value for " + field_name + ": " + value)
    return value



def parse_lowering_profile(doc: dict[str, JsonVal]) -> LoweringProfile:
    _ = doc
    return LoweringProfile(
        tuple_unpack_style="subscript",
        container_covariance=False,
        closure_style="native_nested",
        with_style="try_finally",
        property_style="field_access",
        swap_style="temp_var",
        exception_style="native_throw",
    )



def load_lowering_profile(language: str) -> LoweringProfile:
    if language == "":
        raise RuntimeError("language must not be empty")
    return parse_lowering_profile(_default_profile_doc())



def load_profile_doc(language: str) -> dict[str, JsonVal]:
    if language == "":
        raise RuntimeError("language must not be empty")
    cached = _PROFILE_DOC_CACHE.get(language)
    if cached is not None:
        return cached
    loaded = _default_profile_doc()
    _PROFILE_DOC_CACHE[language] = loaded
    return loaded

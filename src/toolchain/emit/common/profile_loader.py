"""Language/lowering profile loader for toolchain2 emitters."""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

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


@dataclass
class LoweringProfileDocDraft:
    profile: LoweringProfile
    schema_version: int = 1

    def to_jv(self) -> dict[str, JsonVal]:
        lowering: dict[str, JsonVal] = {
            "tuple_unpack_style": self.profile.tuple_unpack_style,
            "container_covariance": self.profile.container_covariance,
            "closure_style": self.profile.closure_style,
            "with_style": self.profile.with_style,
            "property_style": self.profile.property_style,
            "swap_style": self.profile.swap_style,
            "exception_style": self.profile.exception_style,
        }
        return {
            "schema_version": self.schema_version,
            "lowering": lowering,
        }


def _default_lowering_profile() -> LoweringProfile:
    return LoweringProfile(
        "subscript",
        False,
        "native_nested",
        "try_finally",
        "field_access",
        "temp_var",
        "native_throw",
    )


def _default_profile_doc() -> dict[str, JsonVal]:
    return LoweringProfileDocDraft(_default_lowering_profile()).to_jv()


def _profile_root() -> Path:
    cwd_profile_root = Path("src").joinpath("toolchain").joinpath("emit").joinpath("profiles")
    return cwd_profile_root


def _read_profile_doc(profile_path: Path) -> dict[str, JsonVal]:
    parsed = json.loads(profile_path.read_text(encoding="utf-8")).as_obj()
    if parsed is None:
        raise RuntimeError("profile root must be an object: " + str(profile_path))
    return parsed.raw


def _clone_profile_value(value: JsonVal) -> JsonVal:
    value_obj = json.JsonValue(value).as_obj()
    if value_obj is not None:
        child: dict[str, JsonVal] = {}
        for child_key, child_value in value_obj.raw.items():
            child[child_key] = _clone_profile_value(child_value)
        return child
    value_arr = json.JsonValue(value).as_arr()
    if value_arr is not None:
        out: list[JsonVal] = []
        for item in value_arr.raw:
            out.append(_clone_profile_value(item))
        return out
    return value


def _merge_profile_values(base: JsonVal, override: JsonVal) -> JsonVal:
    base_obj = json.JsonValue(base).as_obj()
    override_obj = json.JsonValue(override).as_obj()
    if base_obj is not None and override_obj is not None:
        merged: dict[str, JsonVal] = {}
        for key, value in base_obj.raw.items():
            merged[key] = _clone_profile_value(value)
        for key, value in override_obj.raw.items():
            if key in merged:
                merged[key] = _merge_profile_values(merged[key], value)
            else:
                merged[key] = _clone_profile_value(value)
        return merged
    return _clone_profile_value(override)


def _merge_profile_docs(base: dict[str, JsonVal], override: dict[str, JsonVal]) -> dict[str, JsonVal]:
    merged: dict[str, JsonVal] = {}
    for key, value in base.items():
        merged[key] = _clone_profile_value(value)
    for key, value in override.items():
        if key in merged:
            merged[key] = _merge_profile_values(merged[key], value)
        else:
            merged[key] = _clone_profile_value(value)
    return merged



def load_profile_with_includes(profile_path: Path) -> dict[str, JsonVal]:
    return _merge_profile_docs(
        _read_profile_doc(_profile_root().joinpath("core.json")),
        _read_profile_doc(profile_path),
    )



def _validate_enum(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise RuntimeError("invalid lowering profile value for " + field_name + ": " + value)
    return value



def parse_lowering_profile(doc: dict[str, JsonVal]) -> LoweringProfile:
    lowering_raw = doc.get("lowering")
    lowering_obj = json.JsonValue(lowering_raw).as_obj()
    if lowering_obj is None:
        raise RuntimeError("lowering profile must define lowering object")
    lowering = lowering_obj.raw
    defaults = _default_lowering_profile()
    tuple_unpack_style = json.JsonValue(lowering.get("tuple_unpack_style")).as_str()
    container_covariance = json.JsonValue(lowering.get("container_covariance")).as_bool()
    closure_style = json.JsonValue(lowering.get("closure_style")).as_str()
    with_style = json.JsonValue(lowering.get("with_style")).as_str()
    property_style = json.JsonValue(lowering.get("property_style")).as_str()
    swap_style = json.JsonValue(lowering.get("swap_style")).as_str()
    exception_style = json.JsonValue(lowering.get("exception_style")).as_str()
    return LoweringProfile(
        _validate_enum(
            tuple_unpack_style if tuple_unpack_style is not None else defaults.tuple_unpack_style,
            _VALID_TUPLE_UNPACK_STYLES,
            "tuple_unpack_style",
        ),
        container_covariance if container_covariance is not None else defaults.container_covariance,
        _validate_enum(
            closure_style if closure_style is not None else defaults.closure_style,
            _VALID_CLOSURE_STYLES,
            "closure_style",
        ),
        _validate_enum(
            with_style if with_style is not None else defaults.with_style,
            _VALID_WITH_STYLES,
            "with_style",
        ),
        _validate_enum(
            property_style if property_style is not None else defaults.property_style,
            _VALID_PROPERTY_STYLES,
            "property_style",
        ),
        _validate_enum(
            swap_style if swap_style is not None else defaults.swap_style,
            _VALID_SWAP_STYLES,
            "swap_style",
        ),
        _validate_enum(
            exception_style if exception_style is not None else defaults.exception_style,
            _VALID_EXCEPTION_STYLES,
            "exception_style",
        ),
    )



def load_lowering_profile(language: str) -> LoweringProfile:
    if language == "":
        raise RuntimeError("language must not be empty")
    return parse_lowering_profile(load_profile_doc(language))



def load_profile_doc(language: str) -> dict[str, JsonVal]:
    if language == "":
        raise RuntimeError("language must not be empty")
    if language in _PROFILE_DOC_CACHE:
        return _PROFILE_DOC_CACHE[language]
    profile_path = _profile_root().joinpath(language + ".json")
    doc = load_profile_with_includes(profile_path)
    _PROFILE_DOC_CACHE[language] = doc
    return doc

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
        tuple_unpack_style="subscript",
        container_covariance=False,
        closure_style="native_nested",
        with_style="try_finally",
        property_style="field_access",
        swap_style="temp_var",
        exception_style="native_throw",
    )


def _default_profile_doc() -> dict[str, JsonVal]:
    return LoweringProfileDocDraft(profile=_default_lowering_profile()).to_jv()


def _profile_root() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles"


def _read_profile_doc(profile_path: Path) -> dict[str, JsonVal]:
    parsed = json.loads(profile_path.read_text(encoding="utf-8")).as_obj()
    if parsed is None:
        raise RuntimeError("profile root must be an object: " + str(profile_path))
    return parsed.raw


def _clone_profile_value(value: JsonVal) -> JsonVal:
    if isinstance(value, dict):
        child: dict[str, JsonVal] = {}
        for child_key, child_value in value.items():
            child[child_key] = _clone_profile_value(child_value)
        return child
    if isinstance(value, list):
        out: list[JsonVal] = []
        for item in value:
            out.append(_clone_profile_value(item))
        return out
    return value


def _merge_profile_values(base: JsonVal, override: JsonVal) -> JsonVal:
    if isinstance(base, dict) and isinstance(override, dict):
        merged: dict[str, JsonVal] = {}
        for key, value in base.items():
            merged[key] = _clone_profile_value(value)
        for key, value in override.items():
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



def load_profile_with_includes(profile_path: object) -> dict[str, JsonVal]:
    if isinstance(profile_path, Path):
        path = profile_path
    elif isinstance(profile_path, str):
        path = Path(profile_path)
    else:
        path = Path(str(profile_path))
    core_path = _profile_root() / "core.json"
    core_doc = _read_profile_doc(core_path)
    lang_doc = _read_profile_doc(path)
    return _merge_profile_docs(core_doc, lang_doc)



def _validate_enum(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise RuntimeError("invalid lowering profile value for " + field_name + ": " + value)
    return value



def parse_lowering_profile(doc: dict[str, JsonVal]) -> LoweringProfile:
    lowering_raw = doc.get("lowering")
    if not isinstance(lowering_raw, dict):
        raise RuntimeError("lowering profile must define lowering object")
    defaults = _default_lowering_profile()
    tuple_unpack_style = lowering_raw.get("tuple_unpack_style")
    container_covariance = lowering_raw.get("container_covariance")
    closure_style = lowering_raw.get("closure_style")
    with_style = lowering_raw.get("with_style")
    property_style = lowering_raw.get("property_style")
    swap_style = lowering_raw.get("swap_style")
    exception_style = lowering_raw.get("exception_style")
    return LoweringProfile(
        tuple_unpack_style=_validate_enum(
            tuple_unpack_style if isinstance(tuple_unpack_style, str) else defaults.tuple_unpack_style,
            _VALID_TUPLE_UNPACK_STYLES,
            "tuple_unpack_style",
        ),
        container_covariance=container_covariance if isinstance(container_covariance, bool) else defaults.container_covariance,
        closure_style=_validate_enum(
            closure_style if isinstance(closure_style, str) else defaults.closure_style,
            _VALID_CLOSURE_STYLES,
            "closure_style",
        ),
        with_style=_validate_enum(
            with_style if isinstance(with_style, str) else defaults.with_style,
            _VALID_WITH_STYLES,
            "with_style",
        ),
        property_style=_validate_enum(
            property_style if isinstance(property_style, str) else defaults.property_style,
            _VALID_PROPERTY_STYLES,
            "property_style",
        ),
        swap_style=_validate_enum(
            swap_style if isinstance(swap_style, str) else defaults.swap_style,
            _VALID_SWAP_STYLES,
            "swap_style",
        ),
        exception_style=_validate_enum(
            exception_style if isinstance(exception_style, str) else defaults.exception_style,
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
    cached = _PROFILE_DOC_CACHE.get(language)
    if cached is not None:
        return cached
    loaded = load_profile_with_includes(_profile_root() / (language + ".json"))
    _PROFILE_DOC_CACHE[language] = loaded
    return loaded

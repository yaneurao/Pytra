"""Language/lowering profile loader for toolchain2 emitters.

Loads canonical profiles from ``toolchain2/emit/profiles/*.json`` and
validates the lowering profile block used by EAST3 lowering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pytra.std import json
from pytra.std.json import JsonVal


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


@dataclass
class LoweringProfile:
    tuple_unpack_style: str
    container_covariance: bool
    closure_style: str
    with_style: str
    property_style: str
    swap_style: str


def _load_json_dict(path: Path) -> dict[str, JsonVal]:
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw).raw
    if not isinstance(doc, dict):
        raise RuntimeError("profile must be a JSON object: " + str(path))
    return doc


def _merge_profile_dict(base: dict[str, JsonVal], override: dict[str, JsonVal]) -> dict[str, JsonVal]:
    out: dict[str, JsonVal] = {}
    for key in base.keys():
        out[key] = base[key]
    for key in override.keys():
        base_val = out.get(key)
        override_val = override[key]
        if isinstance(base_val, dict) and isinstance(override_val, dict):
            merged_child = _merge_profile_dict(base_val, override_val)
            out[key] = merged_child
        else:
            out[key] = override_val
    return out


def _profiles_root() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles"


def load_profile_with_includes(profile_path: Path) -> dict[str, JsonVal]:
    merged = _load_json_dict(_profiles_root().joinpath("core.json"))
    profile_doc = _load_json_dict(profile_path)
    return _merge_profile_dict(merged, profile_doc)


def _require_str(doc: dict[str, JsonVal], key: str) -> str:
    value = doc.get(key)
    if isinstance(value, str) and value != "":
        return value
    raise RuntimeError("profile field must be a non-empty string: " + key)


def _require_bool(doc: dict[str, JsonVal], key: str) -> bool:
    value = doc.get(key)
    if isinstance(value, bool):
        return value
    raise RuntimeError("profile field must be a bool: " + key)


def _validate_enum(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise RuntimeError("invalid lowering profile value for " + field_name + ": " + value)
    return value


def parse_lowering_profile(doc: dict[str, JsonVal]) -> LoweringProfile:
    schema_version = doc.get("schema_version")
    if schema_version != 1:
        raise RuntimeError("unsupported profile schema_version")
    lowering = doc.get("lowering")
    if not isinstance(lowering, dict):
        raise RuntimeError("profile.lowering must be an object")
    return LoweringProfile(
        tuple_unpack_style=_validate_enum(
            _require_str(lowering, "tuple_unpack_style"),
            _VALID_TUPLE_UNPACK_STYLES,
            "tuple_unpack_style",
        ),
        container_covariance=_require_bool(lowering, "container_covariance"),
        closure_style=_validate_enum(
            _require_str(lowering, "closure_style"),
            _VALID_CLOSURE_STYLES,
            "closure_style",
        ),
        with_style=_validate_enum(
            _require_str(lowering, "with_style"),
            _VALID_WITH_STYLES,
            "with_style",
        ),
        property_style=_validate_enum(
            _require_str(lowering, "property_style"),
            _VALID_PROPERTY_STYLES,
            "property_style",
        ),
        swap_style=_validate_enum(
            _require_str(lowering, "swap_style"),
            _VALID_SWAP_STYLES,
            "swap_style",
        ),
    )


def load_lowering_profile(language: str) -> LoweringProfile:
    if language == "":
        raise RuntimeError("language must not be empty")
    profile_path = _profiles_root().joinpath(language + ".json")
    doc = load_profile_with_includes(profile_path)
    return parse_lowering_profile(doc)


def load_profile_doc(language: str) -> dict[str, JsonVal]:
    if language == "":
        raise RuntimeError("language must not be empty")
    return load_profile_with_includes(_profiles_root().joinpath(language + ".json"))

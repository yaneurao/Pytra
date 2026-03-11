from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


CONFORMANCE_FIXTURE_CLASS_ORDER: Final[tuple[str, ...]] = (
    "syntax",
    "builtin",
    "pytra_std",
)

CONFORMANCE_FIXTURE_CLASS_CATEGORY_MAP: Final[dict[str, tuple[str, ...]]] = {
    "syntax": ("syntax",),
    "builtin": ("builtin",),
    "pytra_std": ("stdlib",),
}

CONFORMANCE_FIXTURE_ALLOWED_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "syntax": (
        "test/fixtures/core/",
        "test/fixtures/control/",
        "test/fixtures/oop/",
        "test/fixtures/collections/",
    ),
    "builtin": (
        "test/fixtures/control/",
        "test/fixtures/oop/",
        "test/fixtures/signature/",
        "test/fixtures/strings/",
        "test/fixtures/typing/",
    ),
    "pytra_std": ("test/fixtures/stdlib/",),
}


class RepresentativeConformanceFixtureEntry(TypedDict):
    feature_id: str
    category: str
    fixture_class: str
    representative_fixture: str
    required_lanes: tuple[str, ...]
    representative_backends: tuple[str, ...]
    downstream_task: str


def _classify_fixture_class(category: str) -> str:
    if category == "syntax":
        return "syntax"
    if category == "builtin":
        return "builtin"
    if category == "stdlib":
        return "pytra_std"
    raise ValueError(f"unsupported conformance fixture category: {category}")


REPRESENTATIVE_CONFORMANCE_FIXTURE_INVENTORY: Final[
    tuple[RepresentativeConformanceFixtureEntry, ...]
] = tuple(
    {
        "feature_id": entry["feature_id"],
        "category": entry["category"],
        "fixture_class": _classify_fixture_class(entry["category"]),
        "representative_fixture": entry["representative_fixture"],
        "required_lanes": entry["required_lanes"],
        "representative_backends": entry["representative_backends"],
        "downstream_task": entry["downstream_task"],
    }
    for entry in feature_contract_mod.iter_representative_conformance_handoff()
)


def iter_representative_conformance_fixture_inventory() -> tuple[RepresentativeConformanceFixtureEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_FIXTURE_INVENTORY


def build_backend_conformance_seed_manifest() -> dict[str, object]:
    representative_conformance_fixtures = [
        {
            "feature_id": entry["feature_id"],
            "category": entry["category"],
            "fixture_class": entry["fixture_class"],
            "representative_fixture": entry["representative_fixture"],
            "required_lanes": list(entry["required_lanes"]),
            "representative_backends": list(entry["representative_backends"]),
            "downstream_task": entry["downstream_task"],
        }
        for entry in iter_representative_conformance_fixture_inventory()
    ]
    return {
        "inventory_version": 1,
        "fixture_class_order": list(CONFORMANCE_FIXTURE_CLASS_ORDER),
        "fixture_class_category_map": {
            fixture_class: list(categories)
            for fixture_class, categories in CONFORMANCE_FIXTURE_CLASS_CATEGORY_MAP.items()
        },
        "fixture_allowed_prefixes": {
            fixture_class: list(prefixes)
            for fixture_class, prefixes in CONFORMANCE_FIXTURE_ALLOWED_PREFIXES.items()
        },
        "representative_conformance_fixtures": representative_conformance_fixtures,
    }

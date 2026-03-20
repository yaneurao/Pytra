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

CONFORMANCE_LANE_ORDER: Final[tuple[str, ...]] = feature_contract_mod.CONFORMANCE_LANE_ORDER

CONFORMANCE_LANE_HARNESS_KIND: Final[dict[str, str]] = {
    "parse": "frontend_parse_diagnostic",
    "east": "east_document_compare",
    "east3_lowering": "east3_document_compare",
    "emit": "backend_emit_compare",
    "runtime": "runtime_parity_compare",
}

CONFORMANCE_LANE_ENTRYPOINTS: Final[dict[str, str]] = {
    "parse": "toolchain.compile.core_entrypoints.convert_source_to_east_with_backend",
    "east": "toolchain.compile.core_entrypoints.convert_source_to_east_with_backend",
    "east3_lowering": "toolchain.compile.east3.lower_east2_to_east3_document",
    "emit": "toolchain.compiler.backend_registry.emit_source_typed",
    "runtime": "tools.runtime_parity_check.main",
}

CONFORMANCE_LANE_COMPARE_UNITS: Final[dict[str, str]] = {
    "parse": "success_or_structured_error",
    "east": "normalized_east_document",
    "east3_lowering": "normalized_east3_document",
    "emit": "normalized_source_or_fail_closed_diagnostic",
    "runtime": "normalized_stdout_exitcode_artifact_digest",
}

CONFORMANCE_FIXTURE_CLASS_LANE_POLICY: Final[dict[str, dict[str, str]]] = {
    "syntax": {
        "parse": "required",
        "east": "required",
        "east3_lowering": "required",
        "emit": "required",
        "runtime": "case_runtime",
    },
    "builtin": {
        "parse": "required",
        "east": "required",
        "east3_lowering": "required",
        "emit": "required",
        "runtime": "case_runtime",
    },
    "pytra_std": {
        "parse": "required",
        "east": "required",
        "east3_lowering": "required",
        "emit": "required",
        "runtime": "module_runtime_strategy",
    },
}


class RepresentativeConformanceFixtureEntry(TypedDict):
    feature_id: str
    category: str
    fixture_class: str
    representative_fixture: str
    required_lanes: tuple[str, ...]
    representative_backends: tuple[str, ...]
    downstream_task: str


class ConformanceLaneHarnessEntry(TypedDict):
    lane: str
    harness_kind: str
    producer_entrypoint: str
    compare_unit: str


class ConformanceFixtureLanePolicyEntry(TypedDict):
    fixture_class: str
    lane_policy: dict[str, str]


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

CONFORMANCE_LANE_HARNESS: Final[tuple[ConformanceLaneHarnessEntry, ...]] = tuple(
    {
        "lane": lane,
        "harness_kind": CONFORMANCE_LANE_HARNESS_KIND[lane],
        "producer_entrypoint": CONFORMANCE_LANE_ENTRYPOINTS[lane],
        "compare_unit": CONFORMANCE_LANE_COMPARE_UNITS[lane],
    }
    for lane in CONFORMANCE_LANE_ORDER
)

CONFORMANCE_FIXTURE_LANE_POLICY: Final[tuple[ConformanceFixtureLanePolicyEntry, ...]] = tuple(
    {
        "fixture_class": fixture_class,
        "lane_policy": dict(CONFORMANCE_FIXTURE_CLASS_LANE_POLICY[fixture_class]),
    }
    for fixture_class in CONFORMANCE_FIXTURE_CLASS_ORDER
)


def iter_representative_conformance_fixture_inventory() -> tuple[RepresentativeConformanceFixtureEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_FIXTURE_INVENTORY


def iter_conformance_lane_harness() -> tuple[ConformanceLaneHarnessEntry, ...]:
    return CONFORMANCE_LANE_HARNESS


def iter_conformance_fixture_lane_policy() -> tuple[ConformanceFixtureLanePolicyEntry, ...]:
    return CONFORMANCE_FIXTURE_LANE_POLICY


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
    conformance_lane_harness = [
        {
            "lane": entry["lane"],
            "harness_kind": entry["harness_kind"],
            "producer_entrypoint": entry["producer_entrypoint"],
            "compare_unit": entry["compare_unit"],
        }
        for entry in iter_conformance_lane_harness()
    ]
    conformance_fixture_lane_policy = [
        {
            "fixture_class": entry["fixture_class"],
            "lane_policy": dict(entry["lane_policy"]),
        }
        for entry in iter_conformance_fixture_lane_policy()
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
        "lane_order": list(CONFORMANCE_LANE_ORDER),
        "lane_harness": conformance_lane_harness,
        "fixture_lane_policy": conformance_fixture_lane_policy,
        "representative_conformance_fixtures": representative_conformance_fixtures,
    }

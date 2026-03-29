from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.misc import backend_conformance_inventory as inventory_mod
from src.toolchain.misc import backend_conformance_runner_contract as runner_mod
from src.toolchain.misc import backend_conformance_runtime_parity_contract as runtime_parity_mod
from src.toolchain.misc import backend_feature_contract_inventory as feature_contract_mod


CONFORMANCE_SUMMARY_KIND: Final[str] = "feature_backend_lane_summary"

CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER: Final[tuple[str, ...]] = (
    "support_matrix",
    "docs",
    "tooling",
)

CONFORMANCE_SUMMARY_DOC_TARGETS: Final[tuple[str, ...]] = (
    "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
    "docs/en/plans/p7-backend-parity-rollout-and-matrix.md",
)

CONFORMANCE_SUMMARY_TOOLING_EXPORTS: Final[tuple[str, ...]] = (
    "tools/gen/export_backend_conformance_summary_handoff_manifest.py",
    "tools/check/check_backend_conformance_summary_handoff_contract.py",
)

CONFORMANCE_SUMMARY_SOURCE_EXPORTS: Final[dict[str, str]] = {
    "seed_manifest": "tools/gen/export_backend_conformance_seed_manifest.py",
    "runner_manifest": "tools/export_backend_conformance_runner_manifest.py",
    "runtime_parity_manifest": "tools/export_backend_conformance_runtime_parity_manifest.py",
}

CONFORMANCE_SUMMARY_SHARED_LANES: Final[tuple[str, ...]] = tuple(
    lane
    for lane in inventory_mod.CONFORMANCE_LANE_ORDER
    if lane not in runner_mod.BACKEND_SELECTABLE_RUNNER_LANES
)

CONFORMANCE_SUMMARY_BACKEND_SELECTABLE_LANES: Final[tuple[str, ...]] = (
    runner_mod.BACKEND_SELECTABLE_RUNNER_LANES
)

CONFORMANCE_SUMMARY_BACKEND_ORDER: Final[tuple[str, ...]] = (
    feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER
)

CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER: Final[tuple[str, ...]] = (
    feature_contract_mod.SUPPORT_STATE_ORDER
)


class RepresentativeConformanceSummaryHandoffEntry(TypedDict):
    feature_id: str
    category: str
    fixture_class: str
    representative_fixture: str
    summary_kind: str
    shared_lanes: tuple[str, ...]
    backend_selectable_lanes: tuple[str, ...]
    backend_order: tuple[str, ...]
    runtime_lane_policy: str
    runtime_summary_source: str
    support_state_order: tuple[str, ...]
    downstream_task: str


_FIXTURE_LANE_POLICY_BY_CLASS: Final[dict[str, dict[str, str]]] = {
    entry["fixture_class"]: dict(entry["lane_policy"])
    for entry in inventory_mod.iter_conformance_fixture_lane_policy()
}

_SUPPORT_HANDOFF_BY_ID: Final[dict[str, dict[str, object]]] = {
    entry["feature_id"]: entry
    for entry in feature_contract_mod.iter_representative_support_matrix_handoff()
}

_RUNTIME_PARITY_FEATURE_IDS: Final[set[str]] = {
    entry["feature_id"] for entry in runtime_parity_mod.iter_representative_stdlib_runtime_parity()
}


def _resolve_runtime_summary_source(feature_id: str, fixture_class: str) -> str:
    if fixture_class == "pytra_std" or feature_id in _RUNTIME_PARITY_FEATURE_IDS:
        return "runtime_parity_manifest"
    return "fixture_lane_policy"


REPRESENTATIVE_CONFORMANCE_SUMMARY_HANDOFF: Final[
    tuple[RepresentativeConformanceSummaryHandoffEntry, ...]
] = tuple(
    {
        "feature_id": entry["feature_id"],
        "category": entry["category"],
        "fixture_class": entry["fixture_class"],
        "representative_fixture": entry["representative_fixture"],
        "summary_kind": CONFORMANCE_SUMMARY_KIND,
        "shared_lanes": CONFORMANCE_SUMMARY_SHARED_LANES,
        "backend_selectable_lanes": CONFORMANCE_SUMMARY_BACKEND_SELECTABLE_LANES,
        "backend_order": tuple(_SUPPORT_HANDOFF_BY_ID[entry["feature_id"]]["backend_order"]),
        "runtime_lane_policy": _FIXTURE_LANE_POLICY_BY_CLASS[entry["fixture_class"]]["runtime"],
        "runtime_summary_source": _resolve_runtime_summary_source(
            entry["feature_id"],
            entry["fixture_class"],
        ),
        "support_state_order": tuple(_SUPPORT_HANDOFF_BY_ID[entry["feature_id"]]["support_state_order"]),
        "downstream_task": str(_SUPPORT_HANDOFF_BY_ID[entry["feature_id"]]["downstream_task"]),
    }
    for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
)


def iter_representative_conformance_summary_handoff() -> tuple[RepresentativeConformanceSummaryHandoffEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_SUMMARY_HANDOFF


def build_backend_conformance_summary_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "summary_kind": CONFORMANCE_SUMMARY_KIND,
        "publish_target_order": list(CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER),
        "docs_targets": list(CONFORMANCE_SUMMARY_DOC_TARGETS),
        "tooling_exports": list(CONFORMANCE_SUMMARY_TOOLING_EXPORTS),
        "source_exports": dict(CONFORMANCE_SUMMARY_SOURCE_EXPORTS),
        "shared_lanes": list(CONFORMANCE_SUMMARY_SHARED_LANES),
        "backend_selectable_lanes": list(CONFORMANCE_SUMMARY_BACKEND_SELECTABLE_LANES),
        "backend_order": list(CONFORMANCE_SUMMARY_BACKEND_ORDER),
        "support_state_order": list(CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER),
        "representative_summary_entries": [
            {
                "feature_id": entry["feature_id"],
                "category": entry["category"],
                "fixture_class": entry["fixture_class"],
                "representative_fixture": entry["representative_fixture"],
                "summary_kind": entry["summary_kind"],
                "shared_lanes": list(entry["shared_lanes"]),
                "backend_selectable_lanes": list(entry["backend_selectable_lanes"]),
                "backend_order": list(entry["backend_order"]),
                "runtime_lane_policy": entry["runtime_lane_policy"],
                "runtime_summary_source": entry["runtime_summary_source"],
                "support_state_order": list(entry["support_state_order"]),
                "downstream_task": entry["downstream_task"],
            }
            for entry in iter_representative_conformance_summary_handoff()
        ],
    }

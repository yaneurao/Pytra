from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


CONFORMANCE_SUMMARY_DESTINATION_ORDER: Final[tuple[str, ...]] = (
    "support_matrix",
    "docs",
    "tooling",
)

CONFORMANCE_SUMMARY_REQUIRED_MANIFESTS: Final[dict[str, str]] = {
    "feature_matrix_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
    "conformance_seed": "backend_conformance_inventory.build_backend_conformance_seed_manifest",
    "runner_seed": "backend_conformance_runner_contract.build_backend_conformance_runner_manifest",
    "stdlib_runtime_seed": "backend_conformance_runtime_parity_contract.build_backend_conformance_runtime_parity_manifest",
}

CONFORMANCE_SUMMARY_BACKEND_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER
CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_STATE_ORDER
CONFORMANCE_SUMMARY_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]


class RepresentativeConformanceSummaryHandoffEntry(TypedDict):
    destination: str
    source_manifest: str
    summary_keys: tuple[str, ...]
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_CONFORMANCE_SUMMARY_HANDOFF: Final[tuple[RepresentativeConformanceSummaryHandoffEntry, ...]] = (
    {
        "destination": "support_matrix",
        "source_manifest": "feature_contract_handoff.support_matrix_handoff",
        "summary_keys": (
            "feature_id",
            "category",
            "representative_fixture",
            "backend_order",
            "support_state_order",
        ),
        "downstream_task": CONFORMANCE_SUMMARY_DOWNSTREAM_TASK,
        "downstream_plan": CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN,
    },
    {
        "destination": "docs",
        "source_manifest": "backend_conformance_runtime_parity_manifest.stdlib_runtime_modules",
        "summary_keys": (
            "module_name",
            "case_stem",
            "compare_unit",
            "representative_backends",
        ),
        "downstream_task": CONFORMANCE_SUMMARY_DOWNSTREAM_TASK,
        "downstream_plan": CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN,
    },
    {
        "destination": "tooling",
        "source_manifest": "backend_conformance_seed_manifest.lane_harness+fixture_lane_policy+runner_manifest",
        "summary_keys": (
            "lane_order",
            "lane_harness",
            "fixture_lane_policy",
            "backend_order",
            "selectable_lanes",
        ),
        "downstream_task": CONFORMANCE_SUMMARY_DOWNSTREAM_TASK,
        "downstream_plan": CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN,
    },
)


def iter_representative_conformance_summary_handoff() -> tuple[RepresentativeConformanceSummaryHandoffEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_SUMMARY_HANDOFF


def build_backend_conformance_summary_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "destination_order": list(CONFORMANCE_SUMMARY_DESTINATION_ORDER),
        "backend_order": list(CONFORMANCE_SUMMARY_BACKEND_ORDER),
        "support_state_order": list(CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER),
        "required_manifests": dict(CONFORMANCE_SUMMARY_REQUIRED_MANIFESTS),
        "summary_handoff": [
            {
                "destination": entry["destination"],
                "source_manifest": entry["source_manifest"],
                "summary_keys": list(entry["summary_keys"]),
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_conformance_summary_handoff()
        ],
    }

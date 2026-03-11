from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_inventory as fixture_inventory_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


CONFORMANCE_HARNESS_STAGE_ORDER: Final[tuple[str, ...]] = (
    "frontend",
    "ir",
    "backend",
    "runtime",
)

BACKEND_SELECTABLE_CONFORMANCE_LANES: Final[tuple[str, ...]] = ("emit", "runtime")


class ConformanceHarnessLaneEntry(TypedDict):
    lane_id: str
    stage: str
    backend_selectable: bool
    fixture_classes: tuple[str, ...]
    artifact_kind: str
    result_contract: str


REPRESENTATIVE_CONFORMANCE_LANE_CONTRACTS: Final[tuple[ConformanceHarnessLaneEntry, ...]] = (
    {
        "lane_id": "parse",
        "stage": "frontend",
        "backend_selectable": False,
        "fixture_classes": fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
        "artifact_kind": "parse_result",
        "result_contract": "parser_success_or_frontend_diagnostic",
    },
    {
        "lane_id": "east",
        "stage": "ir",
        "backend_selectable": False,
        "fixture_classes": fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
        "artifact_kind": "east_document",
        "result_contract": "east_document_or_frontend_diagnostic",
    },
    {
        "lane_id": "east3_lowering",
        "stage": "ir",
        "backend_selectable": False,
        "fixture_classes": fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
        "artifact_kind": "east3_document",
        "result_contract": "east3_document_or_lowering_diagnostic",
    },
    {
        "lane_id": "emit",
        "stage": "backend",
        "backend_selectable": True,
        "fixture_classes": fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
        "artifact_kind": "module_artifact",
        "result_contract": "artifact_or_fail_closed_backend_diagnostic",
    },
    {
        "lane_id": "runtime",
        "stage": "runtime",
        "backend_selectable": True,
        "fixture_classes": fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER,
        "artifact_kind": "runtime_execution",
        "result_contract": "stdout_stderr_exit_or_fail_closed_backend_diagnostic",
    },
)


def iter_representative_conformance_lane_contracts() -> tuple[ConformanceHarnessLaneEntry, ...]:
    return REPRESENTATIVE_CONFORMANCE_LANE_CONTRACTS


def build_backend_conformance_harness_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "stage_order": list(CONFORMANCE_HARNESS_STAGE_ORDER),
        "lane_order": list(feature_contract_mod.CONFORMANCE_LANE_ORDER),
        "backend_selectable_lanes": list(BACKEND_SELECTABLE_CONFORMANCE_LANES),
        "representative_backends": list(feature_contract_mod.FIRST_CONFORMANCE_BACKEND_ORDER),
        "fixture_class_order": list(fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER),
        "lane_contracts": [
            {
                "lane_id": entry["lane_id"],
                "stage": entry["stage"],
                "backend_selectable": entry["backend_selectable"],
                "fixture_classes": list(entry["fixture_classes"]),
                "artifact_kind": entry["artifact_kind"],
                "result_contract": entry["result_contract"],
            }
            for entry in iter_representative_conformance_lane_contracts()
        ],
    }

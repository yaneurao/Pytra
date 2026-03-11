from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_summary_handoff as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


PARITY_MATRIX_SOURCE_MANIFESTS: Final[dict[str, str]] = {
    "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
    "conformance_summary_seed": "backend_conformance_summary_handoff.build_backend_conformance_summary_handoff_manifest",
}

PARITY_MATRIX_PUBLISH_PATHS: Final[dict[str, str]] = {
    "docs_ja": "docs/ja/language/backend-parity-matrix.md",
    "docs_en": "docs/en/language/backend-parity-matrix.md",
    "tool_manifest": "tools/export_backend_parity_matrix_manifest.py",
}

PARITY_MATRIX_SOURCE_DESTINATION: Final[str] = "support_matrix"
PARITY_MATRIX_BACKEND_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER
PARITY_MATRIX_SUPPORT_STATE_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_STATE_ORDER
PARITY_MATRIX_ROW_KEYS: Final[tuple[str, ...]] = (
    "feature_id",
    "category",
    "representative_fixture",
    "backend_order",
    "support_state_order",
)

_SUPPORT_MATRIX_SUMMARY_ENTRY: Final = next(
    entry
    for entry in conformance_summary_mod.iter_representative_conformance_summary_handoff()
    if entry["destination"] == PARITY_MATRIX_SOURCE_DESTINATION
)

PARITY_MATRIX_SUMMARY_SOURCE: Final[str] = _SUPPORT_MATRIX_SUMMARY_ENTRY["source_manifest"]
PARITY_MATRIX_SUMMARY_KEYS: Final[tuple[str, ...]] = _SUPPORT_MATRIX_SUMMARY_ENTRY["summary_keys"]
PARITY_MATRIX_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
PARITY_MATRIX_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]


class RepresentativeParityMatrixRow(TypedDict):
    feature_id: str
    category: str
    representative_fixture: str
    backend_order: tuple[str, ...]
    support_state_order: tuple[str, ...]
    summary_source: str
    summary_keys: tuple[str, ...]
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_PARITY_MATRIX_ROWS: Final[tuple[RepresentativeParityMatrixRow, ...]] = tuple(
    {
        "feature_id": entry["feature_id"],
        "category": entry["category"],
        "representative_fixture": entry["representative_fixture"],
        "backend_order": PARITY_MATRIX_BACKEND_ORDER,
        "support_state_order": PARITY_MATRIX_SUPPORT_STATE_ORDER,
        "summary_source": PARITY_MATRIX_SUMMARY_SOURCE,
        "summary_keys": PARITY_MATRIX_SUMMARY_KEYS,
        "downstream_task": PARITY_MATRIX_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_MATRIX_DOWNSTREAM_PLAN,
    }
    for entry in feature_contract_mod.iter_representative_support_matrix_handoff()
)


def iter_representative_parity_matrix_rows() -> tuple[RepresentativeParityMatrixRow, ...]:
    return REPRESENTATIVE_PARITY_MATRIX_ROWS


def build_backend_parity_matrix_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "source_manifests": dict(PARITY_MATRIX_SOURCE_MANIFESTS),
        "source_destination": PARITY_MATRIX_SOURCE_DESTINATION,
        "backend_order": list(PARITY_MATRIX_BACKEND_ORDER),
        "support_state_order": list(PARITY_MATRIX_SUPPORT_STATE_ORDER),
        "publish_paths": dict(PARITY_MATRIX_PUBLISH_PATHS),
        "summary_source": PARITY_MATRIX_SUMMARY_SOURCE,
        "summary_keys": list(PARITY_MATRIX_SUMMARY_KEYS),
        "row_keys": list(PARITY_MATRIX_ROW_KEYS),
        "matrix_rows": [
            {
                "feature_id": entry["feature_id"],
                "category": entry["category"],
                "representative_fixture": entry["representative_fixture"],
                "backend_order": list(entry["backend_order"]),
                "support_state_order": list(entry["support_state_order"]),
                "summary_source": entry["summary_source"],
                "summary_keys": list(entry["summary_keys"]),
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_parity_matrix_rows()
        ],
    }

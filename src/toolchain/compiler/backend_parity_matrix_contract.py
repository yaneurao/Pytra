from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


PARITY_MATRIX_SOURCE_MANIFESTS: Final[dict[str, str]] = {
    "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
    "conformance_summary_seed": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
}

PARITY_MATRIX_PUBLISH_PATHS: Final[dict[str, str]] = {
    "docs_ja": "docs/ja/language/backend-parity-matrix.md",
    "docs_en": "docs/en/language/backend-parity-matrix.md",
    "tool_manifest": "tools/export_backend_parity_matrix_manifest.py",
}

PARITY_MATRIX_SOURCE_DESTINATION: Final[str] = "support_matrix"
PARITY_MATRIX_BACKEND_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER
PARITY_MATRIX_SUPPORT_STATE_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_STATE_ORDER
PARITY_MATRIX_IMPLEMENTATION_PHASE: Final[str] = "cell_seed_manifest"
PARITY_MATRIX_CELL_SCHEMA_STATUS: Final[str] = "seed_populated"
PARITY_MATRIX_CELL_SCHEMA_VERSION: Final[int] = 1
PARITY_MATRIX_CELL_COLLECTION_KEY: Final[str] = "backend_cells"
PARITY_MATRIX_CELL_REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "backend",
    "support_state",
    "evidence_kind",
)
PARITY_MATRIX_CELL_OPTIONAL_KEYS: Final[tuple[str, ...]] = (
    "details",
    "evidence_ref",
    "diagnostic_kind",
)
PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER: Final[tuple[str, ...]] = (
    "build_run_smoke",
    "transpile_smoke",
    "contract_guard",
    "diagnostic_guard",
    "not_started_placeholder",
    "preview_guard",
)
PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE: Final[dict[str, tuple[str, ...]]] = {
    "supported": ("build_run_smoke", "transpile_smoke"),
    "fail_closed": ("contract_guard", "diagnostic_guard"),
    "not_started": ("not_started_placeholder",),
    "experimental": ("preview_guard", "transpile_smoke", "build_run_smoke"),
}
PARITY_MATRIX_CELL_GAP_SUMMARY: Final[dict[str, str]] = {
    "seed_state_is_conservative": "Current backend cell seeds use conservative placeholder states outside cpp until reviewed backend-by-backend evidence is filled.",
    "docs_table_is_seed_only": "The docs page now renders the seeded 2D support table, but the published cells are still placeholders outside the reviewed cpp lane.",
    "cell_details_are_sparse": "Per-cell details/evidence_ref/diagnostic_kind remain sparse until follow-up row fill bundles land.",
}
PARITY_MATRIX_ROW_KEYS: Final[tuple[str, ...]] = (
    "feature_id",
    "category",
    "representative_fixture",
    "backend_order",
    "support_state_order",
    "backend_cells",
)

_SUPPORT_MATRIX_SUMMARY_ENTRY: Final = next(
    entry
    for entry in conformance_summary_mod.iter_representative_conformance_summary_handoff()
    if entry["summary_kind"] == conformance_summary_mod.CONFORMANCE_SUMMARY_KIND
)

PARITY_MATRIX_SUMMARY_SOURCE: Final[str] = "conformance_summary_handoff.representative_summary_entries"
PARITY_MATRIX_SUMMARY_KEYS: Final[tuple[str, ...]] = (
    "feature_id",
    "category",
    "fixture_class",
    "representative_fixture",
    "summary_kind",
    "shared_lanes",
    "backend_selectable_lanes",
    "backend_order",
    "runtime_lane_policy",
    "runtime_summary_source",
    "support_state_order",
    "downstream_task",
)
PARITY_MATRIX_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
PARITY_MATRIX_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]
PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER: Final[str] = "<!-- BEGIN BACKEND PARITY MATRIX TABLE -->"
PARITY_MATRIX_DOC_TABLE_END_MARKER: Final[str] = "<!-- END BACKEND PARITY MATRIX TABLE -->"
PARITY_MATRIX_DOC_TABLE_HEADERS: Final[tuple[str, ...]] = (
    "feature_id",
    "fixture",
    *PARITY_MATRIX_BACKEND_ORDER,
)


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
    backend_cells: tuple["BackendParityMatrixCellSeed", ...]


class BackendParityMatrixCellSchema(TypedDict):
    schema_version: int
    collection_key: str
    required_keys: tuple[str, ...]
    optional_keys: tuple[str, ...]
    support_state_order: tuple[str, ...]
    evidence_kind_order: tuple[str, ...]
    allowed_evidence_kinds_by_state: dict[str, tuple[str, ...]]


class BackendParityMatrixCellSeed(TypedDict):
    backend: str
    support_state: str
    evidence_kind: str


def _seed_backend_cell(backend: str) -> BackendParityMatrixCellSeed:
    if backend == "cpp":
        return {
            "backend": backend,
            "support_state": "supported",
            "evidence_kind": "build_run_smoke",
        }
    return {
        "backend": backend,
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
    }


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
        "backend_cells": tuple(_seed_backend_cell(backend) for backend in PARITY_MATRIX_BACKEND_ORDER),
    }
    for entry in feature_contract_mod.iter_representative_support_matrix_handoff()
)

BACKEND_PARITY_MATRIX_CELL_SCHEMA: Final[BackendParityMatrixCellSchema] = {
    "schema_version": PARITY_MATRIX_CELL_SCHEMA_VERSION,
    "collection_key": PARITY_MATRIX_CELL_COLLECTION_KEY,
    "required_keys": PARITY_MATRIX_CELL_REQUIRED_KEYS,
    "optional_keys": PARITY_MATRIX_CELL_OPTIONAL_KEYS,
    "support_state_order": PARITY_MATRIX_SUPPORT_STATE_ORDER,
    "evidence_kind_order": PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER,
    "allowed_evidence_kinds_by_state": PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE,
}


def iter_representative_parity_matrix_rows() -> tuple[RepresentativeParityMatrixRow, ...]:
    return REPRESENTATIVE_PARITY_MATRIX_ROWS


def build_backend_parity_matrix_markdown_table() -> str:
    lines = [
        "| " + " | ".join(PARITY_MATRIX_DOC_TABLE_HEADERS) + " |",
        "|" + "|".join("---" for _ in PARITY_MATRIX_DOC_TABLE_HEADERS) + "|",
    ]
    for entry in iter_representative_parity_matrix_rows():
        cells_by_backend = {
            cell["backend"]: f"{cell['support_state']} / {cell['evidence_kind']}"
            for cell in entry["backend_cells"]
        }
        row_values = [
            entry["feature_id"],
            entry["representative_fixture"],
            *[cells_by_backend[backend] for backend in PARITY_MATRIX_BACKEND_ORDER],
        ]
        lines.append("| " + " | ".join(row_values) + " |")
    return "\n".join(lines)


def build_backend_parity_matrix_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "source_manifests": dict(PARITY_MATRIX_SOURCE_MANIFESTS),
        "source_destination": PARITY_MATRIX_SOURCE_DESTINATION,
        "implementation_phase": PARITY_MATRIX_IMPLEMENTATION_PHASE,
        "cell_schema_status": PARITY_MATRIX_CELL_SCHEMA_STATUS,
        "cell_schema": {
            "schema_version": BACKEND_PARITY_MATRIX_CELL_SCHEMA["schema_version"],
            "collection_key": BACKEND_PARITY_MATRIX_CELL_SCHEMA["collection_key"],
            "required_keys": list(BACKEND_PARITY_MATRIX_CELL_SCHEMA["required_keys"]),
            "optional_keys": list(BACKEND_PARITY_MATRIX_CELL_SCHEMA["optional_keys"]),
            "support_state_order": list(BACKEND_PARITY_MATRIX_CELL_SCHEMA["support_state_order"]),
            "evidence_kind_order": list(BACKEND_PARITY_MATRIX_CELL_SCHEMA["evidence_kind_order"]),
            "allowed_evidence_kinds_by_state": {
                state: list(kinds)
                for state, kinds in BACKEND_PARITY_MATRIX_CELL_SCHEMA["allowed_evidence_kinds_by_state"].items()
            },
        },
        "cell_gap_summary": dict(PARITY_MATRIX_CELL_GAP_SUMMARY),
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
                "backend_cells": [
                    {
                        "backend": cell["backend"],
                        "support_state": cell["support_state"],
                        "evidence_kind": cell["evidence_kind"],
                    }
                    for cell in entry["backend_cells"]
                ],
                "summary_source": entry["summary_source"],
                "summary_keys": list(entry["summary_keys"]),
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_parity_matrix_rows()
        ],
    }

"""Canonical residual inventory for the secondary backend parity rollout."""

from __future__ import annotations

from typing import Final, TypedDict

from toolchain.compiler import backend_parity_matrix_contract as matrix_mod


SECONDARY_ROLLOUT_TODO_ID: Final[str] = "P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01"
SECONDARY_ROLLOUT_PLAN_JA: Final[str] = "docs/ja/plans/p5-backend-parity-secondary-rollout.md"
SECONDARY_ROLLOUT_PLAN_EN: Final[str] = "docs/en/plans/p5-backend-parity-secondary-rollout.md"
SECONDARY_BACKEND_ORDER: Final[tuple[str, ...]] = ("go", "java", "kt", "scala", "swift", "nim")
SECONDARY_RESIDUAL_STATES: Final[tuple[str, ...]] = ("not_started", "fail_closed")

SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1: Final[dict[str, tuple[str, ...]]] = {
    "go": (),
    "java": (),
    "kt": (),
    "scala": (),
    "swift": (),
    "nim": (),
}


class SecondaryResidualCell(TypedDict):
    backend: str
    feature_id: str
    support_state: str
    evidence_kind: str
    representative_fixture: str


class SecondaryRolloutBundle(TypedDict):
    bundle_id: str
    backend_order: tuple[str, ...]
    feature_ids_by_backend: dict[str, tuple[str, ...]]
    target_evidence: str
    notes: str


def _feature_fixture_map() -> dict[str, str]:
    return {
        row["feature_id"]: row["representative_fixture"]
        for row in matrix_mod.iter_representative_parity_matrix_rows()
    }


def _build_expected_secondary_residual_cells() -> tuple[SecondaryResidualCell, ...]:
    feature_fixture = _feature_fixture_map()
    rows: list[SecondaryResidualCell] = []
    for backend in SECONDARY_BACKEND_ORDER:
        for feature_id in SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1[backend]:
            rows.append(
                {
                    "backend": backend,
                    "feature_id": feature_id,
                    "support_state": "not_started",
                    "evidence_kind": "not_started_placeholder",
                    "representative_fixture": feature_fixture[feature_id],
                }
            )
    return tuple(rows)


def _iter_observed_secondary_residual_cells() -> tuple[SecondaryResidualCell, ...]:
    rows: list[SecondaryResidualCell] = []
    for row in matrix_mod.iter_representative_parity_matrix_rows():
        for cell in row["backend_cells"]:
            if cell["backend"] not in SECONDARY_BACKEND_ORDER:
                continue
            if cell["support_state"] not in SECONDARY_RESIDUAL_STATES:
                continue
            rows.append(
                {
                    "backend": cell["backend"],
                    "feature_id": row["feature_id"],
                    "support_state": cell["support_state"],
                    "evidence_kind": cell["evidence_kind"],
                    "representative_fixture": row["representative_fixture"],
                }
            )
    backend_rank = {backend: index for index, backend in enumerate(SECONDARY_BACKEND_ORDER)}
    return tuple(sorted(rows, key=lambda row: (backend_rank[row["backend"]], row["feature_id"])))


SECONDARY_RESIDUAL_CELLS_V1: Final[tuple[SecondaryResidualCell, ...]] = (
    _build_expected_secondary_residual_cells()
)


SECONDARY_ROLLOUT_BUNDLES_V1: Final[tuple[SecondaryRolloutBundle, ...]] = (
    {
        "bundle_id": "go_java_kt_bundle",
        "backend_order": ("go", "java", "kt"),
        "feature_ids_by_backend": {
            "go": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["go"],
            "java": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["java"],
            "kt": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["kt"],
        },
        "target_evidence": "transpile_smoke",
        "notes": "The go/java/kt bundle is now green; keep the empty bundle as a handoff marker while scala/swift/nim becomes the active residual set.",
    },
    {
        "bundle_id": "scala_swift_nim_bundle",
        "backend_order": ("scala", "swift", "nim"),
        "feature_ids_by_backend": {
            "scala": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["scala"],
            "swift": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["swift"],
            "nim": SECONDARY_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["nim"],
        },
        "target_evidence": "transpile_smoke",
        "notes": "The scala/swift/nim bundle is green; keep the empty bundle as the final handoff marker before archival close.",
    },
)


SECONDARY_ROLLOUT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": SECONDARY_ROLLOUT_TODO_ID,
    "coverage_inventory": "src/toolchain/compiler/backend_parity_secondary_rollout_inventory.py",
    "coverage_checker": "tools/check_backend_parity_secondary_rollout_inventory.py",
    "matrix_contract": "src/toolchain/compiler/backend_parity_matrix_contract.py",
    "plan_paths": (
        SECONDARY_ROLLOUT_PLAN_JA,
        SECONDARY_ROLLOUT_PLAN_EN,
    ),
    "backend_order": SECONDARY_BACKEND_ORDER,
    "residual_states": SECONDARY_RESIDUAL_STATES,
    "completed_backends": ("go", "java", "kt", "scala", "swift", "nim"),
    "next_backend": None,
    "remaining_backends": (),
    "bundle_order": tuple(bundle["bundle_id"] for bundle in SECONDARY_ROLLOUT_BUNDLES_V1),
    "target_evidence_lane": "transpile_smoke",
}


def iter_secondary_rollout_residual_cells() -> tuple[SecondaryResidualCell, ...]:
    return SECONDARY_RESIDUAL_CELLS_V1


def iter_secondary_rollout_bundles() -> tuple[SecondaryRolloutBundle, ...]:
    return SECONDARY_ROLLOUT_BUNDLES_V1


def build_secondary_rollout_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "todo_id": SECONDARY_ROLLOUT_HANDOFF_V1["todo_id"],
        "coverage_inventory": SECONDARY_ROLLOUT_HANDOFF_V1["coverage_inventory"],
        "coverage_checker": SECONDARY_ROLLOUT_HANDOFF_V1["coverage_checker"],
        "matrix_contract": SECONDARY_ROLLOUT_HANDOFF_V1["matrix_contract"],
        "plan_paths": list(SECONDARY_ROLLOUT_HANDOFF_V1["plan_paths"]),
        "backend_order": list(SECONDARY_BACKEND_ORDER),
        "residual_states": list(SECONDARY_RESIDUAL_STATES),
        "completed_backends": list(SECONDARY_ROLLOUT_HANDOFF_V1["completed_backends"]),
        "next_backend": SECONDARY_ROLLOUT_HANDOFF_V1["next_backend"],
        "remaining_backends": list(SECONDARY_ROLLOUT_HANDOFF_V1["remaining_backends"]),
        "bundle_order": list(SECONDARY_ROLLOUT_HANDOFF_V1["bundle_order"]),
        "target_evidence_lane": SECONDARY_ROLLOUT_HANDOFF_V1["target_evidence_lane"],
        "residual_cells": list(iter_secondary_rollout_residual_cells()),
        "rollout_bundles": [
            {
                "bundle_id": bundle["bundle_id"],
                "backend_order": list(bundle["backend_order"]),
                "feature_ids_by_backend": {
                    backend: list(feature_ids)
                    for backend, feature_ids in bundle["feature_ids_by_backend"].items()
                },
                "target_evidence": bundle["target_evidence"],
                "notes": bundle["notes"],
            }
            for bundle in iter_secondary_rollout_bundles()
        ],
    }


def collect_observed_secondary_rollout_residual_cells() -> tuple[SecondaryResidualCell, ...]:
    return _iter_observed_secondary_residual_cells()

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_runner_contract as runner_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


ROLLOUT_TIER_ORDER: Final[tuple[str, ...]] = (
    "representative",
    "secondary",
    "long_tail",
)

ROLLOUT_TIER_BACKENDS: Final[dict[str, tuple[str, ...]]] = {
    "representative": runner_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS,
    "secondary": ("go", "java", "kt", "scala", "swift", "nim"),
    "long_tail": ("js", "ts", "lua", "rb", "php"),
}

ROLLOUT_BACKEND_ORDER: Final[tuple[str, ...]] = feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER
ROLLOUT_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
ROLLOUT_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]
ROLLOUT_DOC_TARGETS: Final[tuple[str, ...]] = (
    "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
    "docs/en/plans/p7-backend-parity-rollout-and-matrix.md",
)


class BackendParityRolloutTierEntry(TypedDict):
    tier: str
    backend_order: tuple[str, ...]
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_BACKEND_PARITY_ROLLOUT_TIERS: Final[tuple[BackendParityRolloutTierEntry, ...]] = tuple(
    {
        "tier": tier,
        "backend_order": ROLLOUT_TIER_BACKENDS[tier],
        "downstream_task": ROLLOUT_DOWNSTREAM_TASK,
        "downstream_plan": ROLLOUT_DOWNSTREAM_PLAN,
    }
    for tier in ROLLOUT_TIER_ORDER
)


def iter_representative_backend_parity_rollout_tiers() -> tuple[BackendParityRolloutTierEntry, ...]:
    return REPRESENTATIVE_BACKEND_PARITY_ROLLOUT_TIERS


def build_backend_parity_rollout_tier_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "tier_order": list(ROLLOUT_TIER_ORDER),
        "backend_order": list(ROLLOUT_BACKEND_ORDER),
        "doc_targets": list(ROLLOUT_DOC_TARGETS),
        "representative_tiers": [
            {
                "tier": entry["tier"],
                "backend_order": list(entry["backend_order"]),
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_backend_parity_rollout_tiers()
        ],
    }

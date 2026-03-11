from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_matrix_contract as matrix_contract_mod
from src.toolchain.compiler import backend_parity_rollout_tier_contract as rollout_tier_mod


PARITY_REVIEW_SOURCE_MANIFESTS: Final[dict[str, str]] = {
    "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
    "parity_matrix_seed": "backend_parity_matrix_contract.build_backend_parity_matrix_manifest",
    "rollout_tier_seed": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
}

PARITY_REVIEW_CHECKLIST_ORDER: Final[tuple[str, ...]] = (
    "feature_inventory",
    "matrix_state_recorded",
    "representative_tier_recorded",
    "later_tier_state_recorded",
    "unsupported_lanes_fail_closed",
    "docs_mirror",
)

PARITY_REVIEW_FAIL_CLOSED_ALLOWED_STATES: Final[tuple[str, ...]] = (
    "fail_closed",
    "not_started",
    "experimental",
)
PARITY_REVIEW_FAIL_CLOSED_PHASE_RULES: Final[dict[str, str]] = feature_contract_mod.FAIL_CLOSED_PHASE_RULES
PARITY_REVIEW_FORBIDDEN_SILENT_FALLBACK_LABELS: Final[tuple[str, ...]] = (
    feature_contract_mod.FORBIDDEN_SILENT_FALLBACK_LABELS
)
PARITY_REVIEW_DOWNSTREAM_TASK: Final[str] = matrix_contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK
PARITY_REVIEW_DOWNSTREAM_PLAN: Final[str] = matrix_contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN


class BackendParityReviewChecklistEntry(TypedDict):
    checklist_id: str
    requirement: str
    applies_to_tiers: tuple[str, ...]
    source_rule: str
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_PARITY_REVIEW_CHECKLIST: Final[tuple[BackendParityReviewChecklistEntry, ...]] = (
    {
        "checklist_id": "feature_inventory",
        "requirement": "Every merged feature records a feature_id and representative fixture, or explicitly leaves a follow-up parity task.",
        "applies_to_tiers": rollout_tier_mod.ROLLOUT_TIER_ORDER,
        "source_rule": feature_contract_mod.NEW_FEATURE_ACCEPTANCE_RULES["feature_id_required"],
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
    {
        "checklist_id": "matrix_state_recorded",
        "requirement": "The feature must have an explicit support-state row in the parity matrix before merge.",
        "applies_to_tiers": rollout_tier_mod.ROLLOUT_TIER_ORDER,
        "source_rule": feature_contract_mod.NEW_FEATURE_ACCEPTANCE_RULES["inventory_or_followup_required"],
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
    {
        "checklist_id": "representative_tier_recorded",
        "requirement": "Representative backends must record explicit support states before later tiers are treated as active rollout work.",
        "applies_to_tiers": ("representative",),
        "source_rule": "backend_parity_rollout_tier_contract.ROLLOUT_TIER_BACKENDS['representative']",
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
    {
        "checklist_id": "later_tier_state_recorded",
        "requirement": "Secondary and long-tail rollout may proceed only after the preceding tier is visible in the matrix.",
        "applies_to_tiers": ("secondary", "long_tail"),
        "source_rule": "backend_parity_rollout_tier_contract.ROLLOUT_TIER_ORDER",
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
    {
        "checklist_id": "unsupported_lanes_fail_closed",
        "requirement": "Any unsupported backend lane must stay in fail_closed/not_started/experimental and must not degrade into object/string/comment fallback output.",
        "applies_to_tiers": rollout_tier_mod.ROLLOUT_TIER_ORDER,
        "source_rule": feature_contract_mod.NEW_FEATURE_ACCEPTANCE_RULES["unsupported_lanes_fail_closed"],
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
    {
        "checklist_id": "docs_mirror",
        "requirement": "Parity review updates must land with docs/en mirror changes in the same change.",
        "applies_to_tiers": rollout_tier_mod.ROLLOUT_TIER_ORDER,
        "source_rule": feature_contract_mod.NEW_FEATURE_ACCEPTANCE_RULES["docs_mirror_required"],
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
    },
)


def iter_representative_backend_parity_review_checklist() -> tuple[BackendParityReviewChecklistEntry, ...]:
    return REPRESENTATIVE_PARITY_REVIEW_CHECKLIST


def build_backend_parity_review_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "source_manifests": dict(PARITY_REVIEW_SOURCE_MANIFESTS),
        "checklist_order": list(PARITY_REVIEW_CHECKLIST_ORDER),
        "fail_closed_allowed_states": list(PARITY_REVIEW_FAIL_CLOSED_ALLOWED_STATES),
        "fail_closed_phase_rules": dict(PARITY_REVIEW_FAIL_CLOSED_PHASE_RULES),
        "forbidden_silent_fallback_labels": list(PARITY_REVIEW_FORBIDDEN_SILENT_FALLBACK_LABELS),
        "downstream_task": PARITY_REVIEW_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_REVIEW_DOWNSTREAM_PLAN,
        "checklist": [
            {
                "checklist_id": entry["checklist_id"],
                "requirement": entry["requirement"],
                "applies_to_tiers": list(entry["applies_to_tiers"]),
                "source_rule": entry["source_rule"],
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_backend_parity_review_checklist()
        ],
    }

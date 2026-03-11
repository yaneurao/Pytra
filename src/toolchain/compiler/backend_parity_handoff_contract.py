from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_matrix_contract as matrix_contract_mod
from src.toolchain.compiler import backend_parity_review_contract as review_contract_mod
from src.toolchain.compiler import backend_parity_rollout_tier_contract as rollout_tier_mod


PARITY_HANDOFF_SOURCE_MANIFESTS: Final[dict[str, str]] = {
    "support_matrix": "backend_parity_matrix_contract.build_backend_parity_matrix_manifest",
    "conformance_summary": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
    "review_checklist": "backend_parity_review_contract.build_backend_parity_review_manifest",
    "rollout_tier": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
}

PARITY_HANDOFF_TARGET_ORDER: Final[tuple[str, ...]] = (
    "docs_matrix_page",
    "docs_index",
    "release_note",
    "tooling_manifest",
)

PARITY_HANDOFF_DOC_TARGETS: Final[tuple[str, ...]] = (
    matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_ja"],
    matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_en"],
    "docs/ja/language/index.md",
    "docs/en/language/index.md",
    "docs/ja/index.md",
    "docs/en/index.md",
)

PARITY_HANDOFF_RELEASE_NOTE_TARGETS: Final[tuple[str, ...]] = (
    "docs/ja/README.md",
    "README.md",
    "docs/ja/news/index.md",
    "docs/en/news/index.md",
)

PARITY_HANDOFF_TOOLING_TARGETS: Final[tuple[str, ...]] = (
    "tools/export_backend_parity_matrix_manifest.py",
    "tools/export_backend_conformance_summary_handoff_manifest.py",
    "tools/export_backend_parity_review_manifest.py",
)

PARITY_HANDOFF_RULES: Final[dict[str, str]] = {
    "docs_matrix_page": "Publish the canonical backend parity matrix page at docs/ja|en/language/backend-parity-matrix.md and treat tooling manifests as the source seed, not hand-edited support claims.",
    "docs_index": "Link the backend parity matrix page from docs/ja|en index.md and language/index.md so parity status is discoverable from the regular docs entrypoints.",
    "release_note": "Release notes may summarize parity movement, but they must link the canonical matrix page instead of duplicating per-backend support tables.",
    "tooling_manifest": "Tooling/export paths must publish machine-readable matrix, conformance-summary, and parity-review manifests from the same vocabulary used by the docs handoff.",
}

PARITY_HANDOFF_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
PARITY_HANDOFF_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]


class BackendParityHandoffTarget(TypedDict):
    target_group: str
    paths: tuple[str, ...]
    source_manifest: str
    rule: str
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_BACKEND_PARITY_HANDOFF_TARGETS: Final[tuple[BackendParityHandoffTarget, ...]] = (
    {
        "target_group": "docs_matrix_page",
        "paths": (
            matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_ja"],
            matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_en"],
        ),
        "source_manifest": PARITY_HANDOFF_SOURCE_MANIFESTS["support_matrix"],
        "rule": PARITY_HANDOFF_RULES["docs_matrix_page"],
        "downstream_task": PARITY_HANDOFF_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_HANDOFF_DOWNSTREAM_PLAN,
    },
    {
        "target_group": "docs_index",
        "paths": (
            "docs/ja/language/index.md",
            "docs/en/language/index.md",
            "docs/ja/index.md",
            "docs/en/index.md",
        ),
        "source_manifest": PARITY_HANDOFF_SOURCE_MANIFESTS["support_matrix"],
        "rule": PARITY_HANDOFF_RULES["docs_index"],
        "downstream_task": PARITY_HANDOFF_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_HANDOFF_DOWNSTREAM_PLAN,
    },
    {
        "target_group": "release_note",
        "paths": PARITY_HANDOFF_RELEASE_NOTE_TARGETS,
        "source_manifest": PARITY_HANDOFF_SOURCE_MANIFESTS["support_matrix"],
        "rule": PARITY_HANDOFF_RULES["release_note"],
        "downstream_task": PARITY_HANDOFF_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_HANDOFF_DOWNSTREAM_PLAN,
    },
    {
        "target_group": "tooling_manifest",
        "paths": PARITY_HANDOFF_TOOLING_TARGETS,
        "source_manifest": PARITY_HANDOFF_SOURCE_MANIFESTS["conformance_summary"],
        "rule": PARITY_HANDOFF_RULES["tooling_manifest"],
        "downstream_task": PARITY_HANDOFF_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_HANDOFF_DOWNSTREAM_PLAN,
    },
)


def iter_representative_backend_parity_handoff_targets() -> tuple[BackendParityHandoffTarget, ...]:
    return REPRESENTATIVE_BACKEND_PARITY_HANDOFF_TARGETS


def build_backend_parity_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "source_manifests": dict(PARITY_HANDOFF_SOURCE_MANIFESTS),
        "target_order": list(PARITY_HANDOFF_TARGET_ORDER),
        "doc_targets": list(PARITY_HANDOFF_DOC_TARGETS),
        "release_note_targets": list(PARITY_HANDOFF_RELEASE_NOTE_TARGETS),
        "tooling_targets": list(PARITY_HANDOFF_TOOLING_TARGETS),
        "rules": dict(PARITY_HANDOFF_RULES),
        "downstream_task": PARITY_HANDOFF_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_HANDOFF_DOWNSTREAM_PLAN,
        "handoff_targets": [
            {
                "target_group": entry["target_group"],
                "paths": list(entry["paths"]),
                "source_manifest": entry["source_manifest"],
                "rule": entry["rule"],
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_backend_parity_handoff_targets()
        ],
        "matrix_backend_order": list(matrix_contract_mod.PARITY_MATRIX_BACKEND_ORDER),
        "matrix_support_state_order": list(matrix_contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER),
        "rollout_tier_order": list(rollout_tier_mod.ROLLOUT_TIER_ORDER),
        "review_checklist_order": list(review_contract_mod.PARITY_REVIEW_CHECKLIST_ORDER),
        "conformance_publish_target_order": list(
            conformance_summary_mod.CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER
        ),
    }

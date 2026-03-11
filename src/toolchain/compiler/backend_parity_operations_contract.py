from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_handoff_contract as handoff_mod


PARITY_OPERATIONS_MAINTENANCE_ORDER: Final[tuple[str, ...]] = (
    "contract_seed",
    "docs_publish",
    "docs_entrypoints",
    "release_note_link",
    "tooling_export",
    "archive_handoff",
)

PARITY_OPERATIONS_DOC_LINK_TARGETS: Final[dict[str, str]] = {
    "docs_ja_index": "language/backend-parity-matrix.md",
    "docs_en_index": "language/backend-parity-matrix.md",
    "docs_ja_language_index": "./backend-parity-matrix.md",
    "docs_en_language_index": "./backend-parity-matrix.md",
    "docs_ja_readme": "language/backend-parity-matrix.md",
    "repo_readme": "docs/en/language/backend-parity-matrix.md",
    "docs_ja_news_index": "../language/backend-parity-matrix.md",
    "docs_en_news_index": "../language/backend-parity-matrix.md",
}

PARITY_OPERATIONS_DOC_LINK_PATHS: Final[dict[str, str]] = {
    "docs_ja_index": "docs/ja/index.md",
    "docs_en_index": "docs/en/index.md",
    "docs_ja_language_index": "docs/ja/language/index.md",
    "docs_en_language_index": "docs/en/language/index.md",
    "docs_ja_readme": "docs/ja/README.md",
    "repo_readme": "README.md",
    "docs_ja_news_index": "docs/ja/news/index.md",
    "docs_en_news_index": "docs/en/news/index.md",
}

PARITY_OPERATIONS_TOOLING_EXPORTS: Final[tuple[str, ...]] = (
    "tools/export_backend_parity_matrix_manifest.py",
    "tools/export_backend_parity_handoff_manifest.py",
)

PARITY_OPERATIONS_ARCHIVE_TARGETS: Final[tuple[str, ...]] = (
    "docs/ja/todo/archive/index.md",
    "docs/en/todo/archive/index.md",
    "docs/ja/plans/archive",
    "docs/en/plans/archive",
)

PARITY_OPERATIONS_RULES: Final[dict[str, str]] = {
    "contract_seed": "Matrix, rollout-tier, review-checklist, and handoff contracts must stay synchronized before any docs or release-note refresh is merged.",
    "docs_publish": "The canonical matrix page stays live at docs/ja|en/language/backend-parity-matrix.md and is refreshed from tooling exports, not from ad-hoc support claims.",
    "docs_entrypoints": "docs index and language index must keep a stable link to the matrix page so parity status stays discoverable.",
    "release_note_link": "README / docs README / news index may summarize parity movement, but they must link back to the canonical matrix page instead of duplicating backend tables.",
    "tooling_export": "Tooling exports remain the machine-readable source for matrix, handoff, and review vocabulary.",
    "archive_handoff": "When P7 closes, archive the plan and todo entry through the dated archive path while leaving the live matrix page and contracts in place.",
}

PARITY_OPERATIONS_DOWNSTREAM_TASK: Final[str] = feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]
PARITY_OPERATIONS_DOWNSTREAM_PLAN: Final[str] = feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]


class BackendParityOperationsTarget(TypedDict):
    target_id: str
    path: str
    required_link: str
    rule: str
    downstream_task: str
    downstream_plan: str


REPRESENTATIVE_BACKEND_PARITY_OPERATIONS_TARGETS: Final[tuple[BackendParityOperationsTarget, ...]] = tuple(
    {
        "target_id": target_id,
        "path": PARITY_OPERATIONS_DOC_LINK_PATHS[target_id],
        "required_link": required_link,
        "rule": PARITY_OPERATIONS_RULES[
            "release_note_link"
            if target_id in {"docs_ja_readme", "repo_readme", "docs_ja_news_index", "docs_en_news_index"}
            else "docs_entrypoints"
        ],
        "downstream_task": PARITY_OPERATIONS_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_OPERATIONS_DOWNSTREAM_PLAN,
    }
    for target_id, required_link in PARITY_OPERATIONS_DOC_LINK_TARGETS.items()
)


def iter_representative_backend_parity_operations_targets() -> tuple[BackendParityOperationsTarget, ...]:
    return REPRESENTATIVE_BACKEND_PARITY_OPERATIONS_TARGETS


def build_backend_parity_operations_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "maintenance_order": list(PARITY_OPERATIONS_MAINTENANCE_ORDER),
        "doc_link_targets": dict(PARITY_OPERATIONS_DOC_LINK_TARGETS),
        "doc_link_paths": dict(PARITY_OPERATIONS_DOC_LINK_PATHS),
        "tooling_exports": list(PARITY_OPERATIONS_TOOLING_EXPORTS),
        "archive_targets": list(PARITY_OPERATIONS_ARCHIVE_TARGETS),
        "rules": dict(PARITY_OPERATIONS_RULES),
        "handoff_doc_targets": list(handoff_mod.PARITY_HANDOFF_DOC_TARGETS),
        "handoff_release_note_targets": list(handoff_mod.PARITY_HANDOFF_RELEASE_NOTE_TARGETS),
        "downstream_task": PARITY_OPERATIONS_DOWNSTREAM_TASK,
        "downstream_plan": PARITY_OPERATIONS_DOWNSTREAM_PLAN,
        "operations_targets": [
            {
                "target_id": entry["target_id"],
                "path": entry["path"],
                "required_link": entry["required_link"],
                "rule": entry["rule"],
                "downstream_task": entry["downstream_task"],
                "downstream_plan": entry["downstream_plan"],
            }
            for entry in iter_representative_backend_parity_operations_targets()
        ],
    }

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_handoff_contract as contract_mod
from src.toolchain.compiler import backend_parity_matrix_contract as matrix_contract_mod
from src.toolchain.compiler import backend_parity_review_contract as review_contract_mod
from src.toolchain.compiler import backend_parity_rollout_tier_contract as rollout_tier_mod


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.PARITY_HANDOFF_SOURCE_MANIFESTS != {
        "support_matrix": "backend_parity_matrix_contract.build_backend_parity_matrix_manifest",
        "conformance_summary": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
        "review_checklist": "backend_parity_review_contract.build_backend_parity_review_manifest",
        "rollout_tier": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
    }:
        issues.append("handoff source manifests drifted")
    if contract_mod.PARITY_HANDOFF_TARGET_ORDER != (
        "docs_matrix_page",
        "docs_index",
        "release_note",
        "tooling_manifest",
    ):
        issues.append("handoff target order drifted")
    if contract_mod.PARITY_HANDOFF_DOC_TARGETS != (
        matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_ja"],
        matrix_contract_mod.PARITY_MATRIX_PUBLISH_PATHS["docs_en"],
        "docs/ja/language/index.md",
        "docs/en/language/index.md",
        "docs/ja/index.md",
        "docs/en/index.md",
    ):
        issues.append("handoff doc targets drifted")
    if contract_mod.PARITY_HANDOFF_RELEASE_NOTE_TARGETS != (
        "docs/ja/README.md",
        "README.md",
        "docs/ja/news/index.md",
        "docs/en/news/index.md",
    ):
        issues.append("handoff release-note targets drifted")
    if contract_mod.PARITY_HANDOFF_TOOLING_TARGETS != (
        "tools/export_backend_parity_matrix_manifest.py",
        "tools/export_backend_conformance_summary_handoff_manifest.py",
        "tools/export_backend_parity_review_manifest.py",
    ):
        issues.append("handoff tooling targets drifted")
    if contract_mod.PARITY_HANDOFF_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("handoff downstream task drifted")
    if contract_mod.PARITY_HANDOFF_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("handoff downstream plan drifted")
    if tuple(entry["target_group"] for entry in contract_mod.iter_representative_backend_parity_handoff_targets()) != contract_mod.PARITY_HANDOFF_TARGET_ORDER:
        issues.append("handoff target groups no longer match target order")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_handoff_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "source_manifests",
        "target_order",
        "doc_targets",
        "release_note_targets",
        "tooling_targets",
        "rules",
        "downstream_task",
        "downstream_plan",
        "handoff_targets",
        "matrix_backend_order",
        "matrix_support_state_order",
        "rollout_tier_order",
        "review_checklist_order",
        "conformance_publish_target_order",
    }:
        issues.append("handoff manifest keys drifted")
    if manifest["source_manifests"] != contract_mod.PARITY_HANDOFF_SOURCE_MANIFESTS:
        issues.append("handoff manifest source_manifests drifted")
    if manifest["target_order"] != list(contract_mod.PARITY_HANDOFF_TARGET_ORDER):
        issues.append("handoff manifest target_order drifted")
    if manifest["doc_targets"] != list(contract_mod.PARITY_HANDOFF_DOC_TARGETS):
        issues.append("handoff manifest doc_targets drifted")
    if manifest["release_note_targets"] != list(contract_mod.PARITY_HANDOFF_RELEASE_NOTE_TARGETS):
        issues.append("handoff manifest release_note_targets drifted")
    if manifest["tooling_targets"] != list(contract_mod.PARITY_HANDOFF_TOOLING_TARGETS):
        issues.append("handoff manifest tooling_targets drifted")
    if manifest["rules"] != contract_mod.PARITY_HANDOFF_RULES:
        issues.append("handoff manifest rules drifted")
    if manifest["downstream_task"] != contract_mod.PARITY_HANDOFF_DOWNSTREAM_TASK:
        issues.append("handoff manifest downstream_task drifted")
    if manifest["downstream_plan"] != contract_mod.PARITY_HANDOFF_DOWNSTREAM_PLAN:
        issues.append("handoff manifest downstream_plan drifted")
    if manifest["matrix_backend_order"] != list(matrix_contract_mod.PARITY_MATRIX_BACKEND_ORDER):
        issues.append("handoff manifest matrix_backend_order drifted")
    if manifest["matrix_support_state_order"] != list(matrix_contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER):
        issues.append("handoff manifest matrix_support_state_order drifted")
    if manifest["rollout_tier_order"] != list(rollout_tier_mod.ROLLOUT_TIER_ORDER):
        issues.append("handoff manifest rollout_tier_order drifted")
    if manifest["review_checklist_order"] != list(review_contract_mod.PARITY_REVIEW_CHECKLIST_ORDER):
        issues.append("handoff manifest review_checklist_order drifted")
    if manifest["conformance_publish_target_order"] != list(conformance_summary_mod.CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER):
        issues.append("handoff manifest conformance_publish_target_order drifted")
    if len(manifest["handoff_targets"]) != len(contract_mod.iter_representative_backend_parity_handoff_targets()):
        issues.append("handoff manifest target length drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_manifest_issues())
    if issues:
        print("[NG] backend parity handoff contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity handoff contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

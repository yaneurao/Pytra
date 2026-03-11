from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_review_contract as contract_mod
from src.toolchain.compiler import backend_parity_rollout_tier_contract as rollout_tier_mod


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.PARITY_REVIEW_SOURCE_MANIFESTS != {
        "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
        "parity_matrix_seed": "backend_parity_matrix_contract.build_backend_parity_matrix_manifest",
        "rollout_tier_seed": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
    }:
        issues.append("parity review source manifests drifted")
    if contract_mod.PARITY_REVIEW_CHECKLIST_ORDER != (
        "feature_inventory",
        "matrix_state_recorded",
        "representative_tier_recorded",
        "later_tier_state_recorded",
        "unsupported_lanes_fail_closed",
        "docs_mirror",
    ):
        issues.append("parity review checklist order drifted")
    if contract_mod.PARITY_REVIEW_FAIL_CLOSED_ALLOWED_STATES != ("fail_closed", "not_started", "experimental"):
        issues.append("fail-closed allowed states drifted")
    if contract_mod.PARITY_REVIEW_FAIL_CLOSED_PHASE_RULES != feature_contract_mod.FAIL_CLOSED_PHASE_RULES:
        issues.append("fail-closed phase rules drifted away from feature contract")
    if contract_mod.PARITY_REVIEW_FORBIDDEN_SILENT_FALLBACK_LABELS != feature_contract_mod.FORBIDDEN_SILENT_FALLBACK_LABELS:
        issues.append("forbidden silent fallback labels drifted away from feature contract")
    if contract_mod.PARITY_REVIEW_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("downstream task drifted away from support matrix handoff")
    if contract_mod.PARITY_REVIEW_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("downstream plan drifted away from support matrix handoff")
    seen_ids: set[str] = set()
    for entry in contract_mod.iter_representative_backend_parity_review_checklist():
        checklist_id = entry["checklist_id"]
        if checklist_id in seen_ids:
            issues.append(f"{checklist_id}: duplicated checklist_id")
        seen_ids.add(checklist_id)
        if not entry["requirement"]:
            issues.append(f"{checklist_id}: requirement must not be empty")
        if not entry["source_rule"]:
            issues.append(f"{checklist_id}: source_rule must not be empty")
        if not entry["applies_to_tiers"]:
            issues.append(f"{checklist_id}: applies_to_tiers must not be empty")
        for tier in entry["applies_to_tiers"]:
            if tier not in rollout_tier_mod.ROLLOUT_TIER_ORDER:
                issues.append(f"{checklist_id}: unknown rollout tier {tier}")
        if entry["downstream_task"] != contract_mod.PARITY_REVIEW_DOWNSTREAM_TASK:
            issues.append(f"{checklist_id}: downstream task drifted")
        if entry["downstream_plan"] != contract_mod.PARITY_REVIEW_DOWNSTREAM_PLAN:
            issues.append(f"{checklist_id}: downstream plan drifted")
    if tuple(entry["checklist_id"] for entry in contract_mod.iter_representative_backend_parity_review_checklist()) != contract_mod.PARITY_REVIEW_CHECKLIST_ORDER:
        issues.append("checklist ids no longer match checklist order")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_review_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "source_manifests",
        "checklist_order",
        "fail_closed_allowed_states",
        "fail_closed_phase_rules",
        "forbidden_silent_fallback_labels",
        "downstream_task",
        "downstream_plan",
        "checklist",
    }:
        issues.append("parity review manifest keys drifted")
    if manifest["source_manifests"] != contract_mod.PARITY_REVIEW_SOURCE_MANIFESTS:
        issues.append("parity review manifest source_manifests drifted")
    if manifest["checklist_order"] != list(contract_mod.PARITY_REVIEW_CHECKLIST_ORDER):
        issues.append("parity review manifest checklist_order drifted")
    if manifest["fail_closed_allowed_states"] != list(contract_mod.PARITY_REVIEW_FAIL_CLOSED_ALLOWED_STATES):
        issues.append("parity review manifest fail_closed_allowed_states drifted")
    if manifest["fail_closed_phase_rules"] != contract_mod.PARITY_REVIEW_FAIL_CLOSED_PHASE_RULES:
        issues.append("parity review manifest fail_closed_phase_rules drifted")
    if manifest["forbidden_silent_fallback_labels"] != list(contract_mod.PARITY_REVIEW_FORBIDDEN_SILENT_FALLBACK_LABELS):
        issues.append("parity review manifest forbidden_silent_fallback_labels drifted")
    if manifest["downstream_task"] != contract_mod.PARITY_REVIEW_DOWNSTREAM_TASK:
        issues.append("parity review manifest downstream_task drifted")
    if manifest["downstream_plan"] != contract_mod.PARITY_REVIEW_DOWNSTREAM_PLAN:
        issues.append("parity review manifest downstream_plan drifted")
    if len(manifest["checklist"]) != len(contract_mod.iter_representative_backend_parity_review_checklist()):
        issues.append("parity review manifest checklist length drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_manifest_issues())
    if issues:
        print("[NG] backend parity review contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity review contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

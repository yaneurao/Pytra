from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_feature_contract_inventory as inventory_mod
from src.toolchain.compiler import backend_registry_diagnostics as diag_mod


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    by_category: dict[str, int] = {category: 0 for category in inventory_mod.CATEGORY_ORDER}
    for entry in inventory_mod.iter_representative_feature_inventory():
        feature_id = entry["feature_id"]
        category = entry["category"]
        if category not in inventory_mod.CATEGORY_ORDER:
            issues.append(f"unknown category: {feature_id}: {category}")
            continue
        by_category[category] += 1
        if feature_id in seen_ids:
            issues.append(f"duplicate feature id: {feature_id}")
        else:
            seen_ids.add(feature_id)
        pattern = inventory_mod.CATEGORY_ID_PATTERNS[category]
        if pattern.fullmatch(feature_id) is None:
            issues.append(f"feature id does not match naming rule: {feature_id}")
        fixture_rel = entry["representative_fixture"]
        if not (ROOT / fixture_rel).exists():
            issues.append(f"missing representative fixture: {feature_id}: {fixture_rel}")
    for category, count in sorted(by_category.items()):
        if count == 0:
            issues.append(f"category has no representative features: {category}")
    return issues


def _collect_support_state_issues() -> list[str]:
    issues: list[str] = []
    if set(inventory_mod.SUPPORT_STATE_ORDER) != set(inventory_mod.SUPPORT_STATE_CRITERIA.keys()):
        issues.append("support-state order and criteria keys do not match")
    for state in inventory_mod.SUPPORT_STATE_ORDER:
        text = inventory_mod.SUPPORT_STATE_CRITERIA.get(state, "").strip()
        if text == "":
            issues.append(f"support-state criterion is empty: {state}")
    return issues


def _collect_fail_closed_policy_issues() -> list[str]:
    issues: list[str] = []
    if not set(inventory_mod.FAIL_CLOSED_DETAIL_CATEGORIES).issubset(diag_mod.KNOWN_BLOCK_DETAIL_CATEGORIES):
        issues.append("fail-closed detail categories are not a subset of known_block detail categories")
    if "toolchain_missing" in inventory_mod.FAIL_CLOSED_DETAIL_CATEGORIES:
        issues.append("toolchain_missing must not be classified as a fail-closed feature detail")
    if set(inventory_mod.FAIL_CLOSED_PHASE_RULES.keys()) != {"parse_and_ir", "emit_and_runtime", "preview_rollout"}:
        issues.append("fail-closed phase rules do not match the fixed phase set")
    for phase, text in sorted(inventory_mod.FAIL_CLOSED_PHASE_RULES.items()):
        if text.strip() == "":
            issues.append(f"fail-closed phase rule is empty: {phase}")
    if set(inventory_mod.FORBIDDEN_SILENT_FALLBACK_LABELS) != {
        "object_fallback",
        "string_fallback",
        "comment_stub_fallback",
        "empty_output_fallback",
    }:
        issues.append("forbidden silent fallback labels drifted from the fixed set")
    return issues


def _collect_acceptance_rule_issues() -> list[str]:
    issues: list[str] = []
    if set(inventory_mod.NEW_FEATURE_ACCEPTANCE_RULES.keys()) != {
        "feature_id_required",
        "inventory_or_followup_required",
        "cxx_only_not_complete",
        "noncpp_state_required",
        "unsupported_lanes_fail_closed",
        "docs_mirror_required",
    }:
        issues.append("new-feature acceptance rules drifted from the fixed key set")
    for key, text in sorted(inventory_mod.NEW_FEATURE_ACCEPTANCE_RULES.items()):
        if text.strip() == "":
            issues.append(f"new-feature acceptance rule is empty: {key}")
    return issues


def _collect_handoff_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_feature_contract_handoff_manifest()
    expected_manifest_keys = {
        "inventory_version",
        "representative_features",
        "conformance_handoff",
        "support_matrix_handoff",
        "support_state_order",
        "fail_closed_detail_categories",
        "handoff_task_ids",
        "handoff_plan_paths",
    }
    if set(manifest.keys()) != expected_manifest_keys:
        issues.append("handoff manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("handoff manifest inventory_version must stay at 1")
    if set(inventory_mod.HANDOFF_TASK_IDS.keys()) != {"conformance_suite", "support_matrix"}:
        issues.append("handoff task ids drifted from the fixed key set")
    if set(inventory_mod.HANDOFF_PLAN_PATHS.keys()) != set(inventory_mod.HANDOFF_TASK_IDS.keys()):
        issues.append("handoff plan paths do not match the handoff task keys")
    for handoff_key, plan_rel in sorted(inventory_mod.HANDOFF_PLAN_PATHS.items()):
        if not (ROOT / plan_rel).exists():
            issues.append(f"missing handoff plan path: {handoff_key}: {plan_rel}")
    inventory_by_id = {
        entry["feature_id"]: entry for entry in inventory_mod.iter_representative_feature_inventory()
    }
    conformance_handoff = inventory_mod.iter_representative_conformance_handoff()
    support_matrix_handoff = inventory_mod.iter_representative_support_matrix_handoff()
    if {entry["feature_id"] for entry in conformance_handoff} != set(inventory_by_id.keys()):
        issues.append("conformance handoff inventory drifted from representative feature inventory")
    if {entry["feature_id"] for entry in support_matrix_handoff} != set(inventory_by_id.keys()):
        issues.append("support-matrix handoff inventory drifted from representative feature inventory")
    if manifest["support_state_order"] != list(inventory_mod.SUPPORT_STATE_ORDER):
        issues.append("handoff manifest support_state_order drifted from the fixed taxonomy")
    if manifest["fail_closed_detail_categories"] != list(inventory_mod.FAIL_CLOSED_DETAIL_CATEGORIES):
        issues.append("handoff manifest fail_closed_detail_categories drifted from the fixed taxonomy")
    for entry in conformance_handoff:
        feature_id = entry["feature_id"]
        inventory_entry = inventory_by_id.get(feature_id)
        if inventory_entry is None:
            continue
        if entry["category"] != inventory_entry["category"]:
            issues.append(f"conformance handoff category drifted: {feature_id}")
        if entry["representative_fixture"] != inventory_entry["representative_fixture"]:
            issues.append(f"conformance handoff fixture drifted: {feature_id}")
        if entry["required_lanes"] != inventory_mod.CONFORMANCE_LANE_ORDER:
            issues.append(f"conformance handoff lanes drifted: {feature_id}")
        if entry["representative_backends"] != inventory_mod.FIRST_CONFORMANCE_BACKEND_ORDER:
            issues.append(f"conformance handoff backend order drifted: {feature_id}")
        if entry["downstream_task"] != inventory_mod.HANDOFF_TASK_IDS["conformance_suite"]:
            issues.append(f"conformance handoff task drifted: {feature_id}")
    for entry in support_matrix_handoff:
        feature_id = entry["feature_id"]
        inventory_entry = inventory_by_id.get(feature_id)
        if inventory_entry is None:
            continue
        if entry["category"] != inventory_entry["category"]:
            issues.append(f"support-matrix handoff category drifted: {feature_id}")
        if entry["representative_fixture"] != inventory_entry["representative_fixture"]:
            issues.append(f"support-matrix handoff fixture drifted: {feature_id}")
        if entry["backend_order"] != inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER:
            issues.append(f"support-matrix handoff backend order drifted: {feature_id}")
        if entry["support_state_order"] != inventory_mod.SUPPORT_STATE_ORDER:
            issues.append(f"support-matrix handoff support states drifted: {feature_id}")
        if entry["downstream_task"] != inventory_mod.HANDOFF_TASK_IDS["support_matrix"]:
            issues.append(f"support-matrix handoff task drifted: {feature_id}")
    return issues


def main() -> int:
    issues = (
        _collect_inventory_issues()
        + _collect_support_state_issues()
        + _collect_fail_closed_policy_issues()
        + _collect_acceptance_rule_issues()
        + _collect_handoff_issues()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend feature contract inventory is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

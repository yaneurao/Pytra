from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_inventory as inventory_mod
from src.toolchain.compiler import backend_conformance_runner_contract as runner_mod
from src.toolchain.compiler import backend_conformance_runtime_parity_contract as runtime_parity_mod
from src.toolchain.compiler import backend_conformance_summary_handoff_contract as contract_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_summary_inventory_issues() -> list[str]:
    issues: list[str] = []
    conformance_by_id = {
        entry["feature_id"]: entry
        for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
    }
    support_by_id = {
        entry["feature_id"]: entry
        for entry in feature_contract_mod.iter_representative_support_matrix_handoff()
    }
    runtime_feature_ids = {
        entry["feature_id"] for entry in runtime_parity_mod.iter_representative_stdlib_runtime_parity()
    }
    lane_policy_by_class = {
        entry["fixture_class"]: dict(entry["lane_policy"])
        for entry in inventory_mod.iter_conformance_fixture_lane_policy()
    }
    seen_ids: set[str] = set()
    for entry in contract_mod.iter_representative_conformance_summary_handoff():
        feature_id = entry["feature_id"]
        seen_ids.add(feature_id)
        conformance_entry = conformance_by_id.get(feature_id)
        support_entry = support_by_id.get(feature_id)
        if conformance_entry is None:
            issues.append(f"missing conformance fixture entry: {feature_id}")
            continue
        if support_entry is None:
            issues.append(f"missing support-matrix handoff entry: {feature_id}")
            continue
        if entry["category"] != conformance_entry["category"]:
            issues.append(f"summary category drifted from conformance inventory: {feature_id}")
        if entry["fixture_class"] != conformance_entry["fixture_class"]:
            issues.append(f"summary fixture class drifted from conformance inventory: {feature_id}")
        if entry["representative_fixture"] != conformance_entry["representative_fixture"]:
            issues.append(f"summary fixture drifted from conformance inventory: {feature_id}")
        if entry["summary_kind"] != contract_mod.CONFORMANCE_SUMMARY_KIND:
            issues.append(f"summary kind drifted: {feature_id}")
        if entry["shared_lanes"] != contract_mod.CONFORMANCE_SUMMARY_SHARED_LANES:
            issues.append(f"shared lane contract drifted: {feature_id}")
        if entry["backend_selectable_lanes"] != contract_mod.CONFORMANCE_SUMMARY_BACKEND_SELECTABLE_LANES:
            issues.append(f"backend-selectable lane contract drifted: {feature_id}")
        if entry["backend_order"] != support_entry["backend_order"]:
            issues.append(f"backend order drifted from support handoff: {feature_id}")
        if entry["support_state_order"] != support_entry["support_state_order"]:
            issues.append(f"support state order drifted from support handoff: {feature_id}")
        if entry["downstream_task"] != support_entry["downstream_task"]:
            issues.append(f"downstream task drifted from support handoff: {feature_id}")
        expected_runtime_policy = lane_policy_by_class[entry["fixture_class"]]["runtime"]
        if entry["runtime_lane_policy"] != expected_runtime_policy:
            issues.append(f"runtime lane policy drifted: {feature_id}")
        expected_runtime_source = (
            "runtime_parity_manifest"
            if feature_id in runtime_feature_ids or entry["fixture_class"] == "pytra_std"
            else "fixture_lane_policy"
        )
        if entry["runtime_summary_source"] != expected_runtime_source:
            issues.append(f"runtime summary source drifted: {feature_id}")
    expected_ids = set(conformance_by_id.keys())
    if seen_ids != expected_ids:
        issues.append("representative conformance summary handoff drifted from conformance inventory")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_conformance_summary_handoff_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "summary_kind",
        "publish_target_order",
        "docs_targets",
        "tooling_exports",
        "source_exports",
        "shared_lanes",
        "backend_selectable_lanes",
        "backend_order",
        "support_state_order",
        "representative_summary_entries",
    }:
        issues.append("conformance summary handoff manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("conformance summary handoff manifest inventory_version must stay at 1")
    if manifest["summary_kind"] != contract_mod.CONFORMANCE_SUMMARY_KIND:
        issues.append("conformance summary kind drifted from the fixed set")
    if manifest["publish_target_order"] != list(contract_mod.CONFORMANCE_SUMMARY_PUBLISH_TARGET_ORDER):
        issues.append("publish target order drifted from the fixed set")
    if manifest["docs_targets"] != list(contract_mod.CONFORMANCE_SUMMARY_DOC_TARGETS):
        issues.append("docs target handoff drifted from the fixed set")
    if manifest["tooling_exports"] != list(contract_mod.CONFORMANCE_SUMMARY_TOOLING_EXPORTS):
        issues.append("tooling export handoff drifted from the fixed set")
    if manifest["source_exports"] != dict(contract_mod.CONFORMANCE_SUMMARY_SOURCE_EXPORTS):
        issues.append("source export handoff drifted from the fixed set")
    if manifest["shared_lanes"] != list(contract_mod.CONFORMANCE_SUMMARY_SHARED_LANES):
        issues.append("shared lanes drifted from the fixed set")
    if manifest["backend_selectable_lanes"] != list(contract_mod.CONFORMANCE_SUMMARY_BACKEND_SELECTABLE_LANES):
        issues.append("backend-selectable lanes drifted from the fixed set")
    if manifest["backend_order"] != list(contract_mod.CONFORMANCE_SUMMARY_BACKEND_ORDER):
        issues.append("summary backend order drifted from the fixed set")
    if manifest["support_state_order"] != list(contract_mod.CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER):
        issues.append("summary support state order drifted from the fixed set")
    if {
        entry["feature_id"] for entry in manifest["representative_summary_entries"]
    } != {
        entry["feature_id"] for entry in contract_mod.iter_representative_conformance_summary_handoff()
    }:
        issues.append("summary handoff manifest entries drifted from the fixed inventory")
    return issues


def main() -> int:
    issues = _collect_summary_inventory_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance summary handoff contract is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

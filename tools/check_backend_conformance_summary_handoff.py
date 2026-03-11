from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_summary_handoff as handoff_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_handoff_issues() -> list[str]:
    issues: list[str] = []
    if handoff_mod.CONFORMANCE_SUMMARY_DESTINATION_ORDER != ("support_matrix", "docs", "tooling"):
        issues.append("conformance summary destination order drifted from the fixed set")
    if handoff_mod.CONFORMANCE_SUMMARY_BACKEND_ORDER != feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER:
        issues.append("conformance summary backend order drifted from the support-matrix handoff")
    if handoff_mod.CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER != feature_contract_mod.SUPPORT_STATE_ORDER:
        issues.append("conformance summary support-state order drifted from the support-matrix handoff")
    if handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("conformance summary downstream task drifted from the support-matrix handoff")
    if handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("conformance summary downstream plan drifted from the support-matrix handoff")
    if set(handoff_mod.CONFORMANCE_SUMMARY_REQUIRED_MANIFESTS.keys()) != {
        "feature_matrix_seed",
        "conformance_seed",
        "runner_seed",
        "stdlib_runtime_seed",
    }:
        issues.append("conformance summary required manifests drifted from the fixed set")
    destinations = tuple(entry["destination"] for entry in handoff_mod.iter_representative_conformance_summary_handoff())
    if destinations != handoff_mod.CONFORMANCE_SUMMARY_DESTINATION_ORDER:
        issues.append("conformance summary handoff destinations drifted from the fixed order")
    for entry in handoff_mod.iter_representative_conformance_summary_handoff():
        if entry["downstream_task"] != handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_TASK:
            issues.append(f"conformance summary downstream task drifted: {entry['destination']}")
        if entry["downstream_plan"] != handoff_mod.CONFORMANCE_SUMMARY_DOWNSTREAM_PLAN:
            issues.append(f"conformance summary downstream plan drifted: {entry['destination']}")
        if len(entry["summary_keys"]) == 0:
            issues.append(f"conformance summary keys are empty: {entry['destination']}")
        if entry["source_manifest"].strip() == "":
            issues.append(f"conformance summary source manifest is empty: {entry['destination']}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = handoff_mod.build_backend_conformance_summary_handoff_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "destination_order",
        "backend_order",
        "support_state_order",
        "required_manifests",
        "summary_handoff",
    }:
        issues.append("conformance summary manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("conformance summary manifest inventory_version must stay at 1")
    if manifest["destination_order"] != list(handoff_mod.CONFORMANCE_SUMMARY_DESTINATION_ORDER):
        issues.append("conformance summary manifest destination order drifted from the fixed set")
    if manifest["backend_order"] != list(handoff_mod.CONFORMANCE_SUMMARY_BACKEND_ORDER):
        issues.append("conformance summary manifest backend order drifted from the fixed set")
    if manifest["support_state_order"] != list(handoff_mod.CONFORMANCE_SUMMARY_SUPPORT_STATE_ORDER):
        issues.append("conformance summary manifest support-state order drifted from the fixed set")
    if manifest["required_manifests"] != dict(handoff_mod.CONFORMANCE_SUMMARY_REQUIRED_MANIFESTS):
        issues.append("conformance summary manifest required manifests drifted from the fixed set")
    if manifest["summary_handoff"] != [
        {
            "destination": entry["destination"],
            "source_manifest": entry["source_manifest"],
            "summary_keys": list(entry["summary_keys"]),
            "downstream_task": entry["downstream_task"],
            "downstream_plan": entry["downstream_plan"],
        }
        for entry in handoff_mod.iter_representative_conformance_summary_handoff()
    ]:
        issues.append("conformance summary manifest handoff entries drifted from the fixed set")
    return issues


def main() -> int:
    issues = _collect_handoff_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance summary handoff is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

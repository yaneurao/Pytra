from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_harness_contract as contract_mod
from src.toolchain.compiler import backend_conformance_inventory as fixture_inventory_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_lane_contract_issues() -> list[str]:
    issues: list[str] = []
    seen_lane_ids: set[str] = set()
    if tuple(entry["lane_id"] for entry in contract_mod.iter_representative_conformance_lane_contracts()) != (
        feature_contract_mod.CONFORMANCE_LANE_ORDER
    ):
        issues.append("representative lane contracts drifted from feature-contract conformance lane order")
    for entry in contract_mod.iter_representative_conformance_lane_contracts():
        lane_id = entry["lane_id"]
        if lane_id in seen_lane_ids:
            issues.append(f"duplicate lane contract: {lane_id}")
        else:
            seen_lane_ids.add(lane_id)
        if entry["stage"] not in contract_mod.CONFORMANCE_HARNESS_STAGE_ORDER:
            issues.append(f"lane stage is unknown: {lane_id}: {entry['stage']}")
        expected_backend_selectable = lane_id in contract_mod.BACKEND_SELECTABLE_CONFORMANCE_LANES
        if entry["backend_selectable"] != expected_backend_selectable:
            issues.append(f"lane backend-selectable flag drifted: {lane_id}")
        if entry["fixture_classes"] != fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER:
            issues.append(f"lane fixture-class order drifted: {lane_id}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_conformance_harness_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "stage_order",
        "lane_order",
        "backend_selectable_lanes",
        "representative_backends",
        "fixture_class_order",
        "lane_contracts",
    }:
        issues.append("conformance harness manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("conformance harness manifest inventory_version must stay at 1")
    if manifest["stage_order"] != list(contract_mod.CONFORMANCE_HARNESS_STAGE_ORDER):
        issues.append("conformance harness stage order drifted from the fixed set")
    if manifest["lane_order"] != list(feature_contract_mod.CONFORMANCE_LANE_ORDER):
        issues.append("conformance harness lane order drifted from the fixed set")
    if manifest["backend_selectable_lanes"] != list(contract_mod.BACKEND_SELECTABLE_CONFORMANCE_LANES):
        issues.append("backend-selectable conformance lanes drifted from the fixed set")
    if manifest["representative_backends"] != list(feature_contract_mod.FIRST_CONFORMANCE_BACKEND_ORDER):
        issues.append("representative conformance backends drifted from the fixed set")
    if manifest["fixture_class_order"] != list(fixture_inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER):
        issues.append("conformance harness fixture class order drifted from the fixed set")
    if {entry["lane_id"] for entry in manifest["lane_contracts"]} != set(feature_contract_mod.CONFORMANCE_LANE_ORDER):
        issues.append("conformance harness lane contracts drifted from the fixed lane set")
    return issues


def main() -> int:
    issues = _collect_lane_contract_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance harness contract is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

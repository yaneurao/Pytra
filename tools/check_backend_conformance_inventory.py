from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_inventory as inventory_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    by_fixture_class: dict[str, int] = {
        fixture_class: 0 for fixture_class in inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER
    }
    handoff_by_id = {
        entry["feature_id"]: entry for entry in feature_contract_mod.iter_representative_conformance_handoff()
    }
    for entry in inventory_mod.iter_representative_conformance_fixture_inventory():
        feature_id = entry["feature_id"]
        fixture_class = entry["fixture_class"]
        category = entry["category"]
        if fixture_class not in inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER:
            issues.append(f"unknown conformance fixture class: {feature_id}: {fixture_class}")
            continue
        by_fixture_class[fixture_class] += 1
        if feature_id in seen_ids:
            issues.append(f"duplicate conformance feature id: {feature_id}")
        else:
            seen_ids.add(feature_id)
        allowed_categories = inventory_mod.CONFORMANCE_FIXTURE_CLASS_CATEGORY_MAP[fixture_class]
        if category not in allowed_categories:
            issues.append(f"fixture class/category drifted: {feature_id}: {fixture_class} -> {category}")
        fixture_rel = entry["representative_fixture"]
        if not (ROOT / fixture_rel).exists():
            issues.append(f"missing representative conformance fixture: {feature_id}: {fixture_rel}")
        allowed_prefixes = inventory_mod.CONFORMANCE_FIXTURE_ALLOWED_PREFIXES[fixture_class]
        if not any(fixture_rel.startswith(prefix) for prefix in allowed_prefixes):
            issues.append(f"fixture path drifted from allowed prefixes: {feature_id}: {fixture_rel}")
        handoff_entry = handoff_by_id.get(feature_id)
        if handoff_entry is None:
            issues.append(f"missing feature-contract conformance handoff: {feature_id}")
            continue
        if category != handoff_entry["category"]:
            issues.append(f"conformance category drifted from handoff: {feature_id}")
        if fixture_rel != handoff_entry["representative_fixture"]:
            issues.append(f"conformance fixture drifted from handoff: {feature_id}")
        if entry["required_lanes"] != handoff_entry["required_lanes"]:
            issues.append(f"conformance lanes drifted from handoff: {feature_id}")
        if entry["representative_backends"] != handoff_entry["representative_backends"]:
            issues.append(f"conformance backends drifted from handoff: {feature_id}")
        if entry["downstream_task"] != handoff_entry["downstream_task"]:
            issues.append(f"conformance downstream task drifted from handoff: {feature_id}")
    if seen_ids != set(handoff_by_id.keys()):
        issues.append("representative conformance fixture inventory drifted from feature-contract handoff")
    for fixture_class, count in sorted(by_fixture_class.items()):
        if count == 0:
            issues.append(f"fixture class has no representative entries: {fixture_class}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_backend_conformance_seed_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "fixture_class_order",
        "fixture_class_category_map",
        "fixture_allowed_prefixes",
        "lane_order",
        "lane_harness",
        "fixture_lane_policy",
        "representative_conformance_fixtures",
    }:
        issues.append("conformance seed manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("conformance seed manifest inventory_version must stay at 1")
    if manifest["fixture_class_order"] != list(inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER):
        issues.append("fixture class order drifted from the fixed set")
    if manifest["fixture_class_category_map"] != {
        fixture_class: list(categories)
        for fixture_class, categories in inventory_mod.CONFORMANCE_FIXTURE_CLASS_CATEGORY_MAP.items()
    }:
        issues.append("fixture class/category map drifted from the fixed set")
    if manifest["fixture_allowed_prefixes"] != {
        fixture_class: list(prefixes)
        for fixture_class, prefixes in inventory_mod.CONFORMANCE_FIXTURE_ALLOWED_PREFIXES.items()
    }:
        issues.append("fixture allowed prefixes drifted from the fixed set")
    if manifest["lane_order"] != list(inventory_mod.CONFORMANCE_LANE_ORDER):
        issues.append("lane order drifted from the fixed set")
    if manifest["lane_harness"] != [
        {
            "lane": entry["lane"],
            "harness_kind": entry["harness_kind"],
            "producer_entrypoint": entry["producer_entrypoint"],
            "compare_unit": entry["compare_unit"],
        }
        for entry in inventory_mod.iter_conformance_lane_harness()
    ]:
        issues.append("lane harness drifted from the fixed set")
    if manifest["fixture_lane_policy"] != [
        {
            "fixture_class": entry["fixture_class"],
            "lane_policy": dict(entry["lane_policy"]),
        }
        for entry in inventory_mod.iter_conformance_fixture_lane_policy()
    ]:
        issues.append("fixture lane policy drifted from the fixed set")
    if {
        entry["feature_id"] for entry in manifest["representative_conformance_fixtures"]
    } != {
        entry["feature_id"] for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
    }:
        issues.append("conformance seed manifest fixtures drifted from the representative inventory")
    return issues


def _collect_lane_issues() -> list[str]:
    issues: list[str] = []
    if inventory_mod.CONFORMANCE_LANE_ORDER != feature_contract_mod.CONFORMANCE_LANE_ORDER:
        issues.append("conformance lane order drifted from the feature-contract handoff")
    harness_by_lane = {entry["lane"]: entry for entry in inventory_mod.iter_conformance_lane_harness()}
    if set(harness_by_lane.keys()) != set(inventory_mod.CONFORMANCE_LANE_ORDER):
        issues.append("lane harness drifted from the fixed lane order")
    for lane in inventory_mod.CONFORMANCE_LANE_ORDER:
        entry = harness_by_lane.get(lane)
        if entry is None:
            continue
        if entry["harness_kind"].strip() == "":
            issues.append(f"lane harness kind is empty: {lane}")
        if entry["producer_entrypoint"].strip() == "":
            issues.append(f"lane producer entrypoint is empty: {lane}")
        if entry["compare_unit"].strip() == "":
            issues.append(f"lane compare unit is empty: {lane}")
    fixture_policy_by_class = {
        entry["fixture_class"]: entry["lane_policy"] for entry in inventory_mod.iter_conformance_fixture_lane_policy()
    }
    if set(fixture_policy_by_class.keys()) != set(inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER):
        issues.append("fixture lane policy drifted from the fixed fixture classes")
    for fixture_class in inventory_mod.CONFORMANCE_FIXTURE_CLASS_ORDER:
        lane_policy = fixture_policy_by_class.get(fixture_class)
        if lane_policy is None:
            continue
        if set(lane_policy.keys()) != set(inventory_mod.CONFORMANCE_LANE_ORDER):
            issues.append(f"fixture lane policy keys drifted: {fixture_class}")
            continue
        if fixture_class == "pytra_std" and lane_policy["runtime"] != "module_runtime_strategy":
            issues.append("pytra_std runtime lane policy must stay on module_runtime_strategy until S3-01")
        if fixture_class != "pytra_std" and lane_policy["runtime"] != "case_runtime":
            issues.append(f"non-stdlib runtime lane policy drifted: {fixture_class}")
        for lane, policy in sorted(lane_policy.items()):
            if policy.strip() == "":
                issues.append(f"fixture lane policy is empty: {fixture_class}:{lane}")
    return issues


def main() -> int:
    issues = _collect_inventory_issues() + _collect_lane_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance inventory is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

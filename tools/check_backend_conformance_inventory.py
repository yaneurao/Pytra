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
    if {
        entry["feature_id"] for entry in manifest["representative_conformance_fixtures"]
    } != {
        entry["feature_id"] for entry in inventory_mod.iter_representative_conformance_fixture_inventory()
    }:
        issues.append("conformance seed manifest fixtures drifted from the representative inventory")
    return issues


def main() -> int:
    issues = _collect_inventory_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance inventory is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

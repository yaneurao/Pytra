from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_feature_contract_inventory as inventory_mod


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


def main() -> int:
    issues = _collect_inventory_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend feature contract inventory is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

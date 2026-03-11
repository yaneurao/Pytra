from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_parity_rollout_tier_contract as contract_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.ROLLOUT_TIER_ORDER != ("representative", "secondary", "long_tail"):
        issues.append("rollout tier order drifted from the fixed set")
    if contract_mod.ROLLOUT_TIER_BACKENDS["representative"] != ("cpp", "rs", "cs"):
        issues.append("representative rollout tier drifted from the fixed set")
    if set(contract_mod.ROLLOUT_TIER_BACKENDS.keys()) != set(contract_mod.ROLLOUT_TIER_ORDER):
        issues.append("rollout tier keys drifted from the fixed set")
    flattened = tuple(
        backend
        for tier in contract_mod.ROLLOUT_TIER_ORDER
        for backend in contract_mod.ROLLOUT_TIER_BACKENDS[tier]
    )
    if flattened != contract_mod.ROLLOUT_BACKEND_ORDER:
        issues.append("rollout tiers no longer cover the support-matrix backend order")
    if len(flattened) != len(set(flattened)):
        issues.append("rollout tiers must not overlap")
    if contract_mod.ROLLOUT_BACKEND_ORDER != feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER:
        issues.append("rollout backend order drifted from support matrix backend order")
    for entry in contract_mod.iter_representative_backend_parity_rollout_tiers():
        if entry["backend_order"] != contract_mod.ROLLOUT_TIER_BACKENDS[entry["tier"]]:
            issues.append(f"rollout tier backend order drifted: {entry['tier']}")
        if entry["downstream_task"] != contract_mod.ROLLOUT_DOWNSTREAM_TASK:
            issues.append(f"rollout tier downstream task drifted: {entry['tier']}")
        if entry["downstream_plan"] != contract_mod.ROLLOUT_DOWNSTREAM_PLAN:
            issues.append(f"rollout tier downstream plan drifted: {entry['tier']}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_rollout_tier_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "tier_order",
        "backend_order",
        "doc_targets",
        "representative_tiers",
    }:
        issues.append("rollout tier manifest keys drifted from the fixed set")
    if manifest["inventory_version"] != 1:
        issues.append("rollout tier manifest inventory_version must stay at 1")
    if manifest["tier_order"] != list(contract_mod.ROLLOUT_TIER_ORDER):
        issues.append("rollout tier manifest order drifted")
    if manifest["backend_order"] != list(contract_mod.ROLLOUT_BACKEND_ORDER):
        issues.append("rollout tier manifest backend order drifted")
    if manifest["doc_targets"] != list(contract_mod.ROLLOUT_DOC_TARGETS):
        issues.append("rollout tier doc targets drifted")
    if len(manifest["representative_tiers"]) != len(contract_mod.ROLLOUT_TIER_ORDER):
        issues.append("rollout tier manifest entries drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues() + _collect_manifest_issues()
    if issues:
        print("[NG] backend parity rollout tier contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity rollout tier contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

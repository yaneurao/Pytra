#!/usr/bin/env python3
"""Validate the seed matrix for bundle-based backend contract coverage."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_contract_coverage_matrix_contract as contract_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_inventory_mod


def _collect_seed_issues() -> list[str]:
    issues: list[str] = []
    rows = contract_mod.iter_backend_contract_coverage_matrix_seed_rows()
    if len(rows) != contract_mod.expected_seed_row_count():
        issues.append("coverage matrix seed row count drifted from representative feature/lane/backend product")
    bundle_ids = set(contract_mod.known_bundle_ids())
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (row["feature_id"], row["required_lane"], row["backend"])
        if key in seen:
            issues.append(f"duplicate coverage matrix seed row: {key}")
        seen.add(key)
        if row["owner_kind"] not in contract_mod.OWNER_KIND_ORDER:
            issues.append(f"unknown owner kind in coverage matrix seed: {key}: {row['owner_kind']}")
            continue
        owner = row["bundle_id_or_rule"]
        if row["owner_kind"] == "bundle" and owner not in bundle_ids:
            issues.append(f"coverage matrix seed references unknown bundle: {key}: {owner}")
        if row["owner_kind"] == "rule" and owner not in contract_mod.RUNTIME_RULE_ORDER:
            issues.append(f"coverage matrix seed references unknown rule: {key}: {owner}")
        if row["required_lane"] == "runtime" and row["owner_kind"] != "rule":
            issues.append(f"runtime lane must stay rule-owned in seed matrix: {key}")
        if row["required_lane"] != "runtime" and row["owner_kind"] != "bundle":
            issues.append(f"non-runtime lane must stay bundle-owned in seed matrix: {key}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_contract_coverage_matrix_seed_manifest()
    if manifest["manifest_version"] != 1:
        issues.append("coverage matrix seed manifest version must stay at 1")
    if tuple(manifest["owner_kind_order"]) != contract_mod.OWNER_KIND_ORDER:
        issues.append("coverage matrix owner kind order drifted")
    if tuple(manifest["support_backend_order"]) != feature_inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER:
        issues.append("coverage matrix backend order drifted")
    if tuple(manifest["required_lane_order"]) != feature_inventory_mod.CONFORMANCE_LANE_ORDER:
        issues.append("coverage matrix required lane order drifted")
    return issues


def main() -> int:
    issues = _collect_seed_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage matrix seed contract is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

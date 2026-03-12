#!/usr/bin/env python3
"""Validate the fixed secondary-backend parity rollout inventory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler import backend_parity_secondary_rollout_inventory as inventory_mod


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    observed = inventory_mod.collect_observed_secondary_rollout_residual_cells()
    expected = inventory_mod.iter_secondary_rollout_residual_cells()
    observed_pairs = {
        (
            cell["backend"],
            cell["feature_id"],
            cell["support_state"],
            cell["evidence_kind"],
            cell["representative_fixture"],
        )
        for cell in observed
    }
    expected_pairs = {
        (
            cell["backend"],
            cell["feature_id"],
            cell["support_state"],
            cell["evidence_kind"],
            cell["representative_fixture"],
        )
        for cell in expected
    }
    if observed_pairs != expected_pairs:
        issues.append("secondary rollout residual inventory drifted from the matrix seed")
    if expected:
        issues.append(f"secondary residual inventory must be empty once the scala/swift/nim bundle closes: got {len(expected)} residual cells")
    return issues


def _collect_bundle_issues() -> list[str]:
    issues: list[str] = []
    bundles = inventory_mod.iter_secondary_rollout_bundles()
    bundle_order = tuple(bundle["bundle_id"] for bundle in bundles)
    if bundle_order != inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["bundle_order"]:
        issues.append("secondary rollout bundle order drifted from the fixed handoff")
    flattened_backend_order = tuple(backend for bundle in bundles for backend in bundle["backend_order"])
    if flattened_backend_order != inventory_mod.SECONDARY_BACKEND_ORDER:
        issues.append("secondary rollout bundle backend order no longer matches the fixed secondary backend order")
    residual_pairs = {
        (cell["backend"], cell["feature_id"])
        for cell in inventory_mod.iter_secondary_rollout_residual_cells()
    }
    bundled_pairs = {
        (backend, feature_id)
        for bundle in bundles
        for backend, feature_ids in bundle["feature_ids_by_backend"].items()
        for feature_id in feature_ids
    }
    if residual_pairs != bundled_pairs:
        issues.append("secondary rollout bundles no longer cover the exact residual feature set")
    if inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["next_backend"] is not None:
        issues.append("secondary rollout next_backend must become null once the scala/swift/nim bundle closes")
    if inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["completed_backends"] != inventory_mod.SECONDARY_BACKEND_ORDER:
        issues.append("secondary rollout completed_backends must cover the full secondary backend order once the residual set is empty")
    if inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["remaining_backends"] != ():
        issues.append("secondary rollout remaining_backends must become empty once the residual set closes")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_secondary_rollout_handoff_manifest()
    if manifest.get("inventory_version") != 1:
        issues.append("secondary rollout handoff inventory_version must stay at 1")
    if tuple(manifest.get("backend_order", ())) != inventory_mod.SECONDARY_BACKEND_ORDER:
        issues.append("secondary rollout manifest backend order drifted from the fixed inventory")
    if tuple(manifest.get("plan_paths", ())) != inventory_mod.SECONDARY_ROLLOUT_HANDOFF_V1["plan_paths"]:
        issues.append("secondary rollout manifest plan paths drifted from the fixed inventory")
    return issues


def main() -> int:
    issues = _collect_inventory_issues() + _collect_bundle_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] secondary backend parity rollout inventory is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

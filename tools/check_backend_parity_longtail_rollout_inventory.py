#!/usr/bin/env python3
"""Validate the fixed long-tail backend parity rollout inventory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler import backend_parity_longtail_rollout_inventory as inventory_mod


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    observed = inventory_mod.collect_observed_longtail_rollout_residual_cells()
    expected = inventory_mod.iter_longtail_rollout_residual_cells()
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
        issues.append("long-tail rollout residual inventory drifted from the matrix seed")
    return issues


def _collect_bundle_issues() -> list[str]:
    issues: list[str] = []
    bundles = inventory_mod.iter_longtail_rollout_bundles()
    bundle_order = tuple(bundle["bundle_id"] for bundle in bundles)
    if bundle_order != inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["bundle_order"]:
        issues.append("long-tail rollout bundle order drifted from the fixed handoff")
    flattened_backend_order = tuple(backend for bundle in bundles for backend in bundle["backend_order"])
    if flattened_backend_order != inventory_mod.LONGTAIL_BACKEND_ORDER:
        issues.append("long-tail rollout bundle backend order no longer matches the fixed long-tail backend order")
    residual_pairs = {
        (cell["backend"], cell["feature_id"])
        for cell in inventory_mod.iter_longtail_rollout_residual_cells()
    }
    bundled_pairs = {
        (backend, feature_id)
        for bundle in bundles
        for backend, feature_ids in bundle["feature_ids_by_backend"].items()
        for feature_id in feature_ids
    }
    if residual_pairs != bundled_pairs:
        issues.append("long-tail rollout bundles no longer cover the exact residual feature set")
    next_bundle_id = inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_bundle"]
    if len(residual_pairs) == 0:
        if next_bundle_id is not None:
            issues.append("long-tail rollout next_bundle must become null once the lua/rb/php bundle closes")
        if inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["completed_backends"] != inventory_mod.LONGTAIL_BACKEND_ORDER:
            issues.append("long-tail rollout completed_backends must cover the full backend order once the residual set is empty")
        if inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_backend"] is not None:
            issues.append("long-tail rollout next_backend must become null once the residual set is empty")
        if inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["remaining_backends"] != ():
            issues.append("long-tail rollout remaining_backends must become empty once the residual set closes")
        for bundle in bundles:
            if any(bundle["feature_ids_by_backend"].values()):
                issues.append("long-tail rollout bundles must stay empty handoff markers once the residual set is empty")
        return issues
    bundle_by_id = {bundle["bundle_id"]: bundle for bundle in bundles}
    next_bundle = bundle_by_id.get(next_bundle_id)
    if next_bundle is None:
        issues.append("long-tail rollout next_bundle must point at one of the fixed rollout bundles")
        return issues
    next_index = bundle_order.index(next_bundle_id)
    completed_backends = tuple(
        backend
        for bundle in bundles[:next_index]
        for backend in bundle["backend_order"]
    )
    if completed_backends != inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["completed_backends"]:
        issues.append("long-tail rollout completed_backends drifted from the completed bundle prefix")
    for bundle in bundles[:next_index]:
        if any(bundle["feature_ids_by_backend"].values()):
            issues.append("long-tail rollout bundles before next_bundle must stay empty handoff markers once completed")
    if next_bundle["backend_order"][0] != inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_backend"]:
        issues.append("long-tail rollout next_backend must stay aligned with the active next_bundle")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_longtail_rollout_handoff_manifest()
    if manifest.get("inventory_version") != 1:
        issues.append("long-tail rollout handoff inventory_version must stay at 1")
    if tuple(manifest.get("backend_order", ())) != inventory_mod.LONGTAIL_BACKEND_ORDER:
        issues.append("long-tail rollout manifest backend order drifted from the fixed inventory")
    if tuple(manifest.get("plan_paths", ())) != inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["plan_paths"]:
        issues.append("long-tail rollout manifest plan paths drifted from the fixed inventory")
    if manifest.get("next_bundle") != inventory_mod.LONGTAIL_ROLLOUT_HANDOFF_V1["next_bundle"]:
        issues.append("long-tail rollout manifest next_bundle drifted from the fixed inventory")
    return issues


def main() -> int:
    issues = _collect_inventory_issues() + _collect_bundle_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] long-tail backend parity rollout inventory is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

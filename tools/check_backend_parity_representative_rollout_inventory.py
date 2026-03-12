#!/usr/bin/env python3
"""Validate the fixed representative-backend parity rollout inventory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler import backend_parity_representative_rollout_inventory as inventory_mod


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    observed = inventory_mod.collect_observed_representative_rollout_residual_cells()
    expected = inventory_mod.iter_representative_rollout_residual_cells()
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
        issues.append("representative rollout residual inventory drifted from the matrix seed")
    cpp_cells = [cell for cell in expected if cell["backend"] == "cpp"]
    if cpp_cells:
        issues.append(f"cpp representative residual inventory must stay empty: got {cpp_cells}")
    backends = {cell["backend"] for cell in expected}
    if backends != {"rs", "cs"}:
        issues.append(f"representative residual backends must stay rs/cs-only: got {sorted(backends)}")
    return issues


def _collect_bundle_issues() -> list[str]:
    issues: list[str] = []
    bundles = inventory_mod.iter_representative_rollout_bundles()
    bundle_order = tuple(bundle["bundle_id"] for bundle in bundles)
    if bundle_order != inventory_mod.REPRESENTATIVE_ROLLOUT_HANDOFF_V1["bundle_order"]:
        issues.append("representative rollout bundle order drifted from the fixed handoff")
    if bundles[0]["backend"] != "cpp" or bundles[0]["feature_ids"] != ():
        issues.append("cpp locked baseline bundle must stay first and empty")
    residual_pairs = {
        (cell["backend"], cell["feature_id"])
        for cell in inventory_mod.iter_representative_rollout_residual_cells()
    }
    bundled_pairs = {
        (bundle["backend"], feature_id)
        for bundle in bundles
        for feature_id in bundle["feature_ids"]
    }
    if residual_pairs != bundled_pairs:
        issues.append("representative rollout bundles no longer cover the exact residual feature set")
    if inventory_mod.REPRESENTATIVE_ROLLOUT_HANDOFF_V1["next_backend"] != "rs":
        issues.append("representative rollout next_backend must stay rs while builtin.iter.zip remains in the Rust residual set")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_representative_rollout_handoff_manifest()
    if manifest.get("inventory_version") != 1:
        issues.append("representative rollout handoff inventory_version must stay at 1")
    if tuple(manifest.get("backend_order", ())) != inventory_mod.REPRESENTATIVE_BACKEND_ORDER:
        issues.append("representative rollout manifest backend order drifted from the fixed inventory")
    if tuple(manifest.get("plan_paths", ())) != inventory_mod.REPRESENTATIVE_ROLLOUT_HANDOFF_V1["plan_paths"]:
        issues.append("representative rollout manifest plan paths drifted from the fixed inventory")
    return issues


def main() -> int:
    issues = _collect_inventory_issues() + _collect_bundle_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] representative backend parity rollout inventory is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

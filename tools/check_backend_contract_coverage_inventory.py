#!/usr/bin/env python3
"""Validate the seed inventory for bundle-based backend contract coverage."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler import backend_contract_coverage_inventory as inventory_mod


def _collect_bundle_issues() -> list[str]:
    issues: list[str] = []
    bundles = inventory_mod.iter_backend_contract_coverage_bundles()
    bundle_ids = tuple(bundle["bundle_id"] for bundle in bundles)
    if bundle_ids != inventory_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["bundle_order"]:
        issues.append("coverage bundle order drifted from the fixed seed inventory")
    bundle_kinds = tuple(bundle["bundle_kind"] for bundle in bundles)
    if bundle_kinds != inventory_mod.BUNDLE_KIND_ORDER:
        issues.append("coverage bundle kinds drifted from the fixed taxonomy")
    if len(set(bundle_ids)) != len(bundle_ids):
        issues.append("coverage bundle ids contain duplicates")
    if len(set(bundle_kinds)) != len(bundle_kinds):
        issues.append("coverage bundle kinds contain duplicates")
    for bundle in bundles:
        if bundle["suite_kind"] not in inventory_mod.SUITE_KIND_ORDER:
            issues.append(f"unknown suite kind in coverage bundle: {bundle['bundle_id']}: {bundle['suite_kind']}")
        if bundle["harness_kind"] not in inventory_mod.HARNESS_KIND_ORDER:
            issues.append(
                f"unknown harness kind in coverage bundle: {bundle['bundle_id']}: {bundle['harness_kind']}"
            )
        for relpath in bundle["source_paths"]:
            if not (ROOT / relpath).exists():
                issues.append(f"missing coverage bundle source path: {bundle['bundle_id']}: {relpath}")
        for evidence in bundle["evidence_refs"]:
            relpath = evidence["relpath"]
            path = ROOT / relpath
            if not path.exists():
                issues.append(f"missing coverage bundle evidence path: {bundle['bundle_id']}: {relpath}")
                continue
            if evidence["needle"] not in path.read_text(encoding="utf-8"):
                issues.append(
                    f"missing coverage bundle evidence needle: {bundle['bundle_id']}: {relpath}: {evidence['needle']}"
                )
    return issues


def _collect_coverage_only_fixture_issues() -> list[str]:
    issues: list[str] = []
    support_fixtures = set(inventory_mod.SUPPORT_MATRIX_FIXTURES)
    coverage_only = inventory_mod.iter_backend_contract_coverage_only_fixtures()
    if len({row["fixture_stem"] for row in coverage_only}) != len(coverage_only):
        issues.append("coverage-only fixture stems contain duplicates")
    for row in coverage_only:
        if row["status"] not in inventory_mod.COVERAGE_ONLY_STATUS_ORDER:
            issues.append(f"unknown coverage-only fixture status: {row['fixture_stem']}: {row['status']}")
        fixture_path = ROOT / row["fixture_rel"]
        if not fixture_path.exists():
            issues.append(f"coverage-only fixture path is missing: {row['fixture_stem']}: {row['fixture_rel']}")
        if row["fixture_rel"] in support_fixtures:
            issues.append(f"coverage-only fixture was already promoted into support inventory: {row['fixture_rel']}")
        backend_order = tuple(item["backend"] for item in row["backend_evidence"])
        if backend_order != feature_backend_order():
            issues.append(
                f"coverage-only backend order drifted: {row['fixture_stem']}: {backend_order} != {feature_backend_order()}"
            )
        for evidence in row["backend_evidence"]:
            relpath = evidence["relpath"]
            path = ROOT / relpath
            if not path.exists():
                issues.append(
                    f"coverage-only evidence path is missing: {row['fixture_stem']}: {evidence['backend']}: {relpath}"
                )
                continue
            if evidence["needle"] not in path.read_text(encoding="utf-8"):
                issues.append(
                    "coverage-only evidence needle is missing: "
                    f"{row['fixture_stem']}: {evidence['backend']}: {relpath}: {evidence['needle']}"
                )
    return issues


def feature_backend_order() -> tuple[str, ...]:
    return tuple(inventory_mod.SMOKE_TEST_PATH_BY_BACKEND.keys())


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_backend_contract_coverage_seed_manifest()
    if manifest.get("inventory_version") != 1:
        issues.append("coverage seed manifest version must stay at 1")
    if tuple(manifest.get("bundle_kind_order", ())) != inventory_mod.BUNDLE_KIND_ORDER:
        issues.append("coverage seed manifest bundle kind order drifted")
    if tuple(manifest.get("suite_kind_order", ())) != inventory_mod.SUITE_KIND_ORDER:
        issues.append("coverage seed manifest suite kind order drifted")
    if tuple(manifest.get("harness_kind_order", ())) != inventory_mod.HARNESS_KIND_ORDER:
        issues.append("coverage seed manifest harness kind order drifted")
    if tuple(manifest.get("coverage_only_status_order", ())) != inventory_mod.COVERAGE_ONLY_STATUS_ORDER:
        issues.append("coverage seed manifest coverage-only status order drifted")
    return issues


def main() -> int:
    issues = _collect_bundle_issues() + _collect_coverage_only_fixture_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] backend contract coverage seed inventory is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

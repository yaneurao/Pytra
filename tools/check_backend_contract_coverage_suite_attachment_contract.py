#!/usr/bin/env python3
"""Validate live suite family coverage-bundle attachments and exclusions."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod
from src.toolchain.compiler import (
    backend_contract_coverage_suite_attachment_contract as contract_mod,
)


def _collect_attachment_issues() -> list[str]:
    issues: list[str] = []
    suites = {entry["suite_id"]: entry for entry in inventory_mod.iter_live_suite_family_inventory()}
    bundles = {entry["bundle_id"]: entry for entry in inventory_mod.iter_backend_contract_coverage_bundles()}
    attached_pairs: set[tuple[str, str]] = set()
    for row in contract_mod.iter_suite_attachment_rows():
        suite = suites.get(row["suite_id"])
        pair = (row["suite_id"], row["bundle_kind"])
        if pair in attached_pairs:
            issues.append(f"duplicate suite attachment row: {pair}")
        attached_pairs.add(pair)
        if row["status"] != "attached":
            issues.append(f"attached suite row drifted from attached status: {pair}: {row['status']}")
        if suite is None:
            issues.append(f"unknown suite in attachment row: {pair}")
            continue
        if suite["coverage_role"] != "direct_matrix_input":
            issues.append(f"non-direct suite cannot own attachment row: {pair}")
        if row["bundle_kind"] not in suite["bundle_candidates"]:
            issues.append(f"attachment row uses non-candidate bundle kind: {pair}")
        bundle = bundles.get(row["bundle_id"])
        if bundle is None:
            issues.append(f"attachment row references unknown bundle: {pair}: {row['bundle_id']}")
            continue
        if bundle["bundle_kind"] != row["bundle_kind"]:
            issues.append(f"attachment row bundle kind drifted: {pair}: {row['bundle_id']}")
    return issues


def _collect_unmapped_issues() -> list[str]:
    issues: list[str] = []
    suites = {entry["suite_id"]: entry for entry in inventory_mod.iter_live_suite_family_inventory()}
    seen: set[tuple[str, str]] = set()
    for row in contract_mod.iter_unmapped_suite_candidate_rows():
        pair = (row["suite_id"], row["bundle_kind"])
        if pair in seen:
            issues.append(f"duplicate unmapped suite candidate row: {pair}")
        seen.add(pair)
        if row["status"] != "unmapped_candidate":
            issues.append(f"unmapped suite row drifted from unmapped_candidate status: {pair}: {row['status']}")
        if row["reason_code"] not in contract_mod.UNMAPPED_REASON_ORDER:
            issues.append(f"unknown unmapped suite reason: {pair}: {row['reason_code']}")
        suite = suites.get(row["suite_id"])
        if suite is None:
            issues.append(f"unknown suite in unmapped row: {pair}")
            continue
        if suite["coverage_role"] != "direct_matrix_input":
            issues.append(f"non-direct suite cannot own unmapped row: {pair}")
        if row["bundle_kind"] not in suite["bundle_candidates"]:
            issues.append(f"unmapped row uses non-candidate bundle kind: {pair}")
    return issues


def _collect_supporting_only_issues() -> list[str]:
    issues: list[str] = []
    suites = {entry["suite_id"]: entry for entry in inventory_mod.iter_live_suite_family_inventory()}
    seen: set[str] = set()
    for row in contract_mod.iter_supporting_only_suite_rows():
        suite_id = row["suite_id"]
        if suite_id in seen:
            issues.append(f"duplicate supporting-only suite row: {suite_id}")
        seen.add(suite_id)
        if row["status"] != "supporting_only":
            issues.append(
                f"supporting-only row drifted from supporting_only status: {suite_id}: {row['status']}"
            )
        if row["reason_code"] not in contract_mod.SUPPORTING_ONLY_REASON_ORDER:
            issues.append(f"unknown supporting-only reason: {suite_id}: {row['reason_code']}")
        suite = suites.get(suite_id)
        if suite is None:
            issues.append(f"unknown suite in supporting-only row: {suite_id}")
            continue
        if suite["coverage_role"] != "supporting_only":
            issues.append(f"direct suite cannot be marked supporting-only: {suite_id}")
    return issues


def _collect_coverage_accounting_issues() -> list[str]:
    issues: list[str] = []
    suites = tuple(inventory_mod.iter_live_suite_family_inventory())
    attached_pairs = {(row["suite_id"], row["bundle_kind"]) for row in contract_mod.iter_suite_attachment_rows()}
    unmapped_pairs = {
        (row["suite_id"], row["bundle_kind"]) for row in contract_mod.iter_unmapped_suite_candidate_rows()
    }
    supporting_only_ids = {row["suite_id"] for row in contract_mod.iter_supporting_only_suite_rows()}
    overlap = attached_pairs & unmapped_pairs
    if overlap:
        issues.append(f"suite attachment/unmapped overlap is not allowed: {sorted(overlap)!r}")
    for suite in suites:
        suite_id = suite["suite_id"]
        if suite["coverage_role"] == "supporting_only":
            if suite_id not in supporting_only_ids:
                issues.append(f"supporting-only suite missing exclusion row: {suite_id}")
            continue
        for bundle_kind in suite["bundle_candidates"]:
            pair = (suite_id, bundle_kind)
            if pair not in attached_pairs and pair not in unmapped_pairs:
                issues.append(f"direct suite candidate missing attachment accounting: {pair}")
        if suite_id in supporting_only_ids:
            issues.append(f"direct suite incorrectly listed as supporting-only: {suite_id}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_contract_coverage_suite_attachment_manifest()
    if manifest["manifest_version"] != 1:
        issues.append("suite attachment manifest version must stay at 1")
    if tuple(manifest["status_order"]) != contract_mod.ATTACHMENT_STATUS_ORDER:
        issues.append("suite attachment status order drifted")
    if tuple(manifest["unmapped_reason_order"]) != contract_mod.UNMAPPED_REASON_ORDER:
        issues.append("suite attachment unmapped reason order drifted")
    if tuple(manifest["supporting_only_reason_order"]) != contract_mod.SUPPORTING_ONLY_REASON_ORDER:
        issues.append("suite attachment supporting-only reason order drifted")
    if tuple(manifest["bundle_order"]) != inventory_mod.COVERAGE_BUNDLE_ORDER:
        issues.append("suite attachment bundle order drifted")
    if tuple(manifest["suite_family_order"]) != inventory_mod.SUITE_FAMILY_ORDER:
        issues.append("suite attachment suite family order drifted")
    return issues


def main() -> int:
    issues = (
        _collect_attachment_issues()
        + _collect_unmapped_issues()
        + _collect_supporting_only_issues()
        + _collect_coverage_accounting_issues()
        + _collect_manifest_issues()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage suite attachments are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

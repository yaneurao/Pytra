#!/usr/bin/env python3
"""Validate suite-family attachment rows for backend contract coverage."""

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


def _suite_rows_by_id() -> dict[str, inventory_mod.LiveSuiteFamilyEntry]:
    return {row["suite_id"]: row for row in inventory_mod.iter_live_suite_family_inventory()}


def _collect_attachment_issues() -> list[str]:
    issues: list[str] = []
    suite_rows = _suite_rows_by_id()
    known_bundle_ids = set(contract_mod.known_bundle_ids())
    seen_suite_ids: set[str] = set()
    for row in contract_mod.iter_backend_contract_coverage_suite_attachments():
        suite_id = row["suite_id"]
        if suite_id in seen_suite_ids:
            issues.append(f"duplicate suite attachment row: {suite_id}")
        seen_suite_ids.add(suite_id)
        if suite_id not in suite_rows:
            issues.append(f"unknown suite attachment row: {suite_id}")
            continue
        source_row = suite_rows[suite_id]
        if row["suite_kind"] != source_row["suite_kind"]:
            issues.append(
                f"suite kind drifted for attachment row: {suite_id}: {row['suite_kind']} != {source_row['suite_kind']}"
            )
        if row["coverage_role"] != source_row["coverage_role"]:
            issues.append(
                f"coverage role drifted for attachment row: {suite_id}: {row['coverage_role']} != {source_row['coverage_role']}"
            )
        if row["attachment_kind"] not in contract_mod.ATTACHMENT_KIND_ORDER:
            issues.append(f"unknown attachment kind: {suite_id}: {row['attachment_kind']}")
            continue
        if row["attachment_kind"] == "bundle_attachment":
            if row["coverage_role"] != "direct_matrix_input":
                issues.append(f"bundle attachment must stay direct_matrix_input: {suite_id}")
            if not row["bundle_ids"]:
                issues.append(f"bundle attachment row must list bundle ids: {suite_id}")
            for bundle_id in row["bundle_ids"]:
                if bundle_id not in known_bundle_ids:
                    issues.append(f"suite attachment references unknown bundle: {suite_id}: {bundle_id}")
                if bundle_id not in source_row["bundle_candidates"]:
                    issues.append(
                        f"suite attachment bundle not allowed by live suite inventory: {suite_id}: {bundle_id}"
                    )
            if row["exclusion_reason"]:
                issues.append(f"bundle attachment row must not carry exclusion reason: {suite_id}")
            continue
        if row["coverage_role"] != "supporting_only":
            issues.append(f"explicit exclusion must stay supporting_only: {suite_id}")
        if row["bundle_ids"]:
            issues.append(f"explicit exclusion must not map to bundle ids: {suite_id}")
        if row["exclusion_reason"] not in contract_mod.EXCLUSION_REASON_ORDER:
            issues.append(f"unknown exclusion reason: {suite_id}: {row['exclusion_reason']}")
    if seen_suite_ids != set(contract_mod.expected_suite_ids()):
        missing = sorted(set(contract_mod.expected_suite_ids()) - seen_suite_ids)
        extra = sorted(seen_suite_ids - set(contract_mod.expected_suite_ids()))
        if missing:
            issues.append(f"suite attachment rows are missing suite ids: {', '.join(missing)}")
        if extra:
            issues.append(f"suite attachment rows contain unexpected suite ids: {', '.join(extra)}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_contract_coverage_suite_attachment_manifest()
    if manifest["manifest_version"] != 1:
        issues.append("suite attachment manifest version must stay at 1")
    if tuple(manifest["attachment_kind_order"]) != contract_mod.ATTACHMENT_KIND_ORDER:
        issues.append("suite attachment kind order drifted")
    if tuple(manifest["exclusion_reason_order"]) != contract_mod.EXCLUSION_REASON_ORDER:
        issues.append("suite attachment exclusion-reason order drifted")
    if tuple(manifest["coverage_role_order"]) != inventory_mod.LIVE_SUITE_ROLE_ORDER:
        issues.append("suite attachment coverage-role order drifted")
    if tuple(manifest["suite_family_order"]) != inventory_mod.SUITE_FAMILY_ORDER:
        issues.append("suite attachment suite-family order drifted")
    return issues


def main() -> int:
    issues = _collect_attachment_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage suite attachments are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

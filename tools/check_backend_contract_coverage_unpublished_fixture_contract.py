#!/usr/bin/env python3
"""Validate unpublished multi-backend fixture classification for coverage rollout."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod
from src.toolchain.compiler import (
    backend_contract_coverage_unpublished_fixture_contract as contract_mod,
)


def _collect_classification_issues() -> list[str]:
    issues: list[str] = []
    unpublished_rows = inventory_mod.iter_unpublished_multi_backend_fixture_inventory()
    actual_rows = tuple(
        {
            "fixture_rel": row["fixture_rel"],
            "fixture_stem": row["fixture_stem"],
            "status": row["status"],
            "target_surface": row["target_surface"],
        }
        for row in unpublished_rows
    )
    if actual_rows != contract_mod.expected_unpublished_fixture_rows():
        issues.append("unpublished fixture classification rows drifted")
    support_fixtures = set(inventory_mod.SUPPORT_MATRIX_FIXTURES)
    coverage_only = {
        row["fixture_stem"]: row for row in inventory_mod.iter_backend_contract_coverage_only_fixtures()
    }
    for row in unpublished_rows:
        expected_target = contract_mod.UNPUBLISHED_FIXTURE_STATUS_TO_TARGET.get(row["status"])
        if expected_target != row["target_surface"]:
            issues.append(
                "unpublished fixture target surface drifted: "
                f"{row['fixture_stem']}: {row['status']} -> {row['target_surface']}"
            )
        if row["fixture_rel"] in support_fixtures:
            issues.append(f"unpublished fixture was already promoted into support inventory: {row['fixture_rel']}")
        if row["target_surface"] == "coverage_matrix_only" and row["fixture_stem"] not in coverage_only:
            issues.append(f"unpublished fixture lost coverage-only evidence row: {row['fixture_stem']}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_contract_coverage_unpublished_fixture_manifest()
    if manifest["contract_version"] != 1:
        issues.append("unpublished fixture contract version must stay at 1")
    if tuple(manifest["status_order"]) != inventory_mod.UNPUBLISHED_FIXTURE_STATUS_ORDER:
        issues.append("unpublished fixture status order drifted")
    if tuple(manifest["target_order"]) != inventory_mod.UNPUBLISHED_FIXTURE_TARGET_ORDER:
        issues.append("unpublished fixture target order drifted")
    if manifest["status_to_target"] != contract_mod.UNPUBLISHED_FIXTURE_STATUS_TO_TARGET:
        issues.append("unpublished fixture status-to-target mapping drifted")
    return issues


def _collect_doc_issues() -> list[str]:
    issues: list[str] = []
    if set(contract_mod.UNPUBLISHED_FIXTURE_DOC_TARGETS.values()) != set(
        contract_mod.UNPUBLISHED_FIXTURE_REQUIRED_DOC_NEEDLES
    ):
        issues.append("unpublished fixture doc targets drifted away from required-doc inventory")
    for rel, needles in contract_mod.UNPUBLISHED_FIXTURE_REQUIRED_DOC_NEEDLES.items():
        path = ROOT / rel
        if not path.exists():
            issues.append(f"missing unpublished fixture doc target: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing unpublished fixture doc needle: {rel}: {needle}")
    return issues


def main() -> int:
    issues = _collect_classification_issues() + _collect_manifest_issues() + _collect_doc_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage unpublished fixture contract is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

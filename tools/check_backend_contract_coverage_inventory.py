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
from toolchain.compiler import backend_feature_contract_inventory as feature_inventory_mod


def _collect_seed_issues() -> list[str]:
    issues: list[str] = []
    taxonomy = inventory_mod.iter_coverage_bundle_taxonomy()
    taxonomy_ids = tuple(entry["bundle_id"] for entry in taxonomy)
    if taxonomy_ids != inventory_mod.COVERAGE_BUNDLE_ORDER:
        issues.append("coverage bundle taxonomy order drifted from the fixed seed inventory")
    if len(set(taxonomy_ids)) != len(taxonomy_ids):
        issues.append("coverage bundle taxonomy ids contain duplicates")
    for entry in taxonomy:
        for source_root in entry["source_roots"]:
            if not (ROOT / source_root).exists():
                issues.append(f"missing coverage taxonomy source root: {entry['bundle_id']}: {source_root}")
        if len(set(entry["suite_ids"])) != len(entry["suite_ids"]):
            issues.append(f"duplicate suite ids in coverage taxonomy: {entry['bundle_id']}")
        if len(set(entry["harness_kinds"])) != len(entry["harness_kinds"]):
            issues.append(f"duplicate harness kinds in coverage taxonomy: {entry['bundle_id']}")
        for harness_kind in entry["harness_kinds"]:
            if harness_kind not in inventory_mod.TAXONOMY_HARNESS_KIND_ORDER:
                issues.append(
                    f"unknown taxonomy harness kind: {entry['bundle_id']}: {harness_kind}"
                )
    return issues


def _collect_bundle_issues() -> list[str]:
    issues: list[str] = []
    bundles = inventory_mod.iter_backend_contract_coverage_bundles()
    bundle_ids = tuple(bundle["bundle_id"] for bundle in bundles)
    if bundle_ids != inventory_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_V1["bundle_order"]:
        issues.append("coverage bundle order drifted from the fixed seed inventory")
    bundle_kinds = tuple(bundle["bundle_kind"] for bundle in bundles)
    if bundle_kinds != inventory_mod.COVERAGE_BUNDLE_ORDER:
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


def _collect_live_suite_issues() -> list[str]:
    issues: list[str] = []
    suites = inventory_mod.iter_live_suite_family_inventory()
    suite_ids = tuple(entry["suite_id"] for entry in suites)
    if suite_ids != inventory_mod.SUITE_FAMILY_ORDER:
        issues.append("live suite family order drifted from the fixed seed inventory")
    if len(set(suite_ids)) != len(suite_ids):
        issues.append("live suite ids contain duplicates")
    allowed_bundle_ids = set(inventory_mod.COVERAGE_BUNDLE_ORDER)
    for entry in suites:
        if entry["suite_kind"] not in inventory_mod.SUITE_KIND_ORDER:
            issues.append(f"unknown live suite kind: {entry['suite_id']}: {entry['suite_kind']}")
        if entry["coverage_role"] not in inventory_mod.LIVE_SUITE_ROLE_ORDER:
            issues.append(
                f"unknown live suite coverage role: {entry['suite_id']}: {entry['coverage_role']}"
            )
        for source_root in entry["source_roots"]:
            if not (ROOT / source_root).exists():
                issues.append(f"missing live suite source root: {entry['suite_id']}: {source_root}")
        for bundle_id in entry["bundle_candidates"]:
            if bundle_id not in allowed_bundle_ids:
                issues.append(
                    f"unknown live suite bundle candidate: {entry['suite_id']}: {bundle_id}"
                )
        if entry["coverage_role"] == "supporting_only" and entry["bundle_candidates"]:
            issues.append(
                f"supporting-only suite must not declare bundle candidates: {entry['suite_id']}"
            )
        if entry["coverage_role"] == "direct_matrix_input" and not entry["bundle_candidates"]:
            issues.append(
                f"direct matrix input suite must declare bundle candidates: {entry['suite_id']}"
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
        if backend_order != inventory_mod.feature_backend_order():
            issues.append(
                "coverage-only backend order drifted: "
                f"{row['fixture_stem']}: {backend_order} != {inventory_mod.feature_backend_order()}"
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


def _collect_promotion_candidate_issues() -> list[str]:
    issues: list[str] = []
    support_fixtures = set(inventory_mod.SUPPORT_MATRIX_FIXTURES)
    known_feature_ids = {
        row["feature_id"] for row in feature_inventory_mod.iter_representative_feature_inventory()
    }
    promotion_candidates = inventory_mod.iter_backend_contract_promotion_candidate_fixtures()
    if len({row["fixture_stem"] for row in promotion_candidates}) != len(promotion_candidates):
        issues.append("promotion-candidate fixture stems contain duplicates")
    for row in promotion_candidates:
        if row["status"] not in inventory_mod.PROMOTION_CANDIDATE_STATUS_ORDER:
            issues.append(
                f"unknown promotion-candidate fixture status: {row['fixture_stem']}: {row['status']}"
            )
        fixture_path = ROOT / row["fixture_rel"]
        if not fixture_path.exists():
            issues.append(
                f"promotion-candidate fixture path is missing: {row['fixture_stem']}: {row['fixture_rel']}"
            )
        if row["fixture_rel"] in support_fixtures:
            issues.append(
                f"promotion-candidate fixture was already promoted into support inventory: {row['fixture_rel']}"
            )
        if not row["proposed_feature_id"] or not row["proposed_category"] or not row["proposed_title"]:
            issues.append(
                f"promotion-candidate fixture must declare proposed support-matrix metadata: {row['fixture_stem']}"
            )
        if row["proposed_feature_id"] in known_feature_ids:
            issues.append(
                f"promotion-candidate proposed feature id already exists in support inventory: {row['proposed_feature_id']}"
            )
        backend_order = tuple(item["backend"] for item in row["backend_evidence"])
        if backend_order != inventory_mod.feature_backend_order():
            issues.append(
                "promotion-candidate backend order drifted: "
                f"{row['fixture_stem']}: {backend_order} != {inventory_mod.feature_backend_order()}"
            )
        for evidence in row["backend_evidence"]:
            relpath = evidence["relpath"]
            path = ROOT / relpath
            if not path.exists():
                issues.append(
                    f"promotion-candidate evidence path is missing: {row['fixture_stem']}: {evidence['backend']}: {relpath}"
                )
                continue
            if evidence["needle"] not in path.read_text(encoding="utf-8"):
                issues.append(
                    "promotion-candidate evidence needle is missing: "
                    f"{row['fixture_stem']}: {evidence['backend']}: {relpath}: {evidence['needle']}"
                )
    return issues


def _collect_unpublished_fixture_issues() -> list[str]:
    issues: list[str] = []
    support_fixtures = set(inventory_mod.SUPPORT_MATRIX_FIXTURES)
    unpublished = inventory_mod.iter_unpublished_multi_backend_fixture_inventory()
    if len({row["fixture_rel"] for row in unpublished}) != len(unpublished):
        issues.append("unpublished multi-backend fixture inventory contains duplicates")
    expected_backend_order = inventory_mod.feature_backend_order()
    expected_target_by_status = {
        "support_matrix_promotion_candidate": "support_matrix",
        "coverage_only_representative": "coverage_matrix_only",
    }
    for row in unpublished:
        if row["status"] not in inventory_mod.UNPUBLISHED_FIXTURE_STATUS_ORDER:
            issues.append(f"unknown unpublished fixture status: {row['fixture_rel']}: {row['status']}")
        if row["target_surface"] not in inventory_mod.UNPUBLISHED_FIXTURE_TARGET_ORDER:
            issues.append(
                f"unknown unpublished fixture target surface: {row['fixture_rel']}: {row['target_surface']}"
            )
        expected_target = expected_target_by_status.get(row["status"])
        if expected_target is not None and row["target_surface"] != expected_target:
            issues.append(
                "unpublished fixture target surface drifted from status policy: "
                f"{row['fixture_rel']}: {row['status']} -> {row['target_surface']} != {expected_target}"
            )
        fixture_path = ROOT / row["fixture_rel"]
        if not fixture_path.exists():
            issues.append(f"missing unpublished fixture path: {row['fixture_rel']}")
        if row["fixture_rel"] in support_fixtures:
            issues.append(
                f"unpublished fixture was already promoted into support inventory: {row['fixture_rel']}"
            )
        if row["status"] == "support_matrix_promotion_candidate":
            if row["target_surface"] != "support_matrix":
                issues.append(
                    f"promotion candidate must target support_matrix: {row['fixture_rel']}"
                )
            if not row["proposed_feature_id"] or not row["proposed_category"] or not row["proposed_title"]:
                issues.append(
                    f"promotion candidate must declare proposed metadata in unpublished inventory: {row['fixture_rel']}"
                )
        if row["status"] == "coverage_only_representative":
            if row["target_surface"] != "coverage_matrix_only":
                issues.append(
                    f"coverage-only representative must target coverage_matrix_only: {row['fixture_rel']}"
                )
            if row["proposed_feature_id"] or row["proposed_category"] or row["proposed_title"]:
                issues.append(
                    f"coverage-only representative must not declare proposed support-matrix metadata: {row['fixture_rel']}"
                )
        if row["observed_backends"] != expected_backend_order:
            issues.append(
                "unpublished fixture observed backend order drifted: "
                f"{row['fixture_rel']}: {row['observed_backends']} != {expected_backend_order}"
            )
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = inventory_mod.build_backend_contract_coverage_seed_manifest()
    if manifest.get("inventory_version") != 1:
        issues.append("coverage seed manifest version must stay at 1")
    if tuple(manifest.get("coverage_bundle_order", ())) != inventory_mod.COVERAGE_BUNDLE_ORDER:
        issues.append("coverage seed manifest bundle order drifted")
    if tuple(manifest.get("suite_family_order", ())) != inventory_mod.SUITE_FAMILY_ORDER:
        issues.append("coverage seed manifest suite family order drifted")
    if tuple(manifest.get("suite_kind_order", ())) != inventory_mod.SUITE_KIND_ORDER:
        issues.append("coverage seed manifest suite kind order drifted")
    if tuple(manifest.get("harness_kind_order", ())) != inventory_mod.HARNESS_KIND_ORDER:
        issues.append("coverage seed manifest harness kind order drifted")
    if (
        tuple(manifest.get("taxonomy_harness_kind_order", ()))
        != inventory_mod.TAXONOMY_HARNESS_KIND_ORDER
    ):
        issues.append("coverage seed manifest taxonomy harness kind order drifted")
    if tuple(manifest.get("coverage_only_status_order", ())) != inventory_mod.COVERAGE_ONLY_STATUS_ORDER:
        issues.append("coverage seed manifest coverage-only status order drifted")
    if (
        tuple(manifest.get("promotion_candidate_status_order", ()))
        != inventory_mod.PROMOTION_CANDIDATE_STATUS_ORDER
    ):
        issues.append("coverage seed manifest promotion-candidate status order drifted")
    if (
        tuple(manifest.get("unpublished_fixture_status_order", ()))
        != inventory_mod.UNPUBLISHED_FIXTURE_STATUS_ORDER
    ):
        issues.append("coverage seed manifest unpublished-fixture status order drifted")
    if (
        tuple(manifest.get("unpublished_fixture_target_order", ()))
        != inventory_mod.UNPUBLISHED_FIXTURE_TARGET_ORDER
    ):
        issues.append("coverage seed manifest unpublished-fixture target order drifted")
    if tuple(manifest.get("live_suite_role_order", ())) != inventory_mod.LIVE_SUITE_ROLE_ORDER:
        issues.append("coverage seed manifest live suite role order drifted")
    return issues


def main() -> int:
    issues = (
        _collect_seed_issues()
        + _collect_bundle_issues()
        + _collect_live_suite_issues()
        + _collect_coverage_only_fixture_issues()
        + _collect_promotion_candidate_issues()
        + _collect_unpublished_fixture_issues()
        + _collect_manifest_issues()
    )
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] backend contract coverage seed inventory is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

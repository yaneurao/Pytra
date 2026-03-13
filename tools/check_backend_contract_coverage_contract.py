#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_contract_coverage_contract as contract_mod
from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.BACKEND_CONTRACT_COVERAGE_MATRIX_STATUS != "published_seed_surface":
        issues.append("coverage matrix status drifted away from published_seed_surface")
    if contract_mod.BACKEND_CONTRACT_COVERAGE_REQUIREMENT_KEYS != (
        "feature_id",
        "required_lane",
        "backend",
        "bundle_id_or_rule",
    ):
        issues.append("coverage requirement keys drifted")
    if contract_mod.BACKEND_CONTRACT_COVERAGE_100_RULES != {
        "contract_not_line": "100% means contract coverage for feature x required_lane x backend, not line or branch coverage.",
        "bundle_or_rule_required": "Each cell must map to a coverage bundle or an explicit backend-specific/non-applicable rule.",
        "suite_status_not_enough": "Suite PASS/FAIL status alone does not satisfy contract coverage without bundle ownership metadata.",
    }:
        issues.append("coverage 100% rules drifted")
    if contract_mod.BACKEND_CONTRACT_COVERAGE_SUITE_ATTACHMENT_RULES != {
        "direct_matrix_input": "Direct matrix-input suite families must declare bundle attachments or explicit unmapped bundle-candidate rows.",
        "supporting_only": "Supporting-only suite families must declare explicit exclusion reasons and may not silently own coverage cells.",
    }:
        issues.append("coverage suite attachment rules drifted")
    if contract_mod.BACKEND_CONTRACT_COVERAGE_ROLE_SPLIT != {
        "support_matrix": "Canonical feature x backend support-state publication surface.",
        "coverage_matrix": "Separate bundle-based publication surface for feature x required_lane x backend contract coverage.",
        "backend_test_matrix": "Backend-owned suite-health publication surface that must stay distinct from contract coverage.",
    }:
        issues.append("coverage role split drifted")
    manifest = contract_mod.build_backend_contract_coverage_contract_manifest()
    if manifest["bundle_order"] != list(inventory_mod.COVERAGE_BUNDLE_ORDER):
        issues.append("coverage contract manifest drifted from coverage bundle order")
    if manifest["suite_attachment_rules"] != contract_mod.BACKEND_CONTRACT_COVERAGE_SUITE_ATTACHMENT_RULES:
        issues.append("coverage contract manifest drifted from suite attachment rules")
    return issues


def _collect_doc_issues() -> list[str]:
    issues: list[str] = []
    if set(contract_mod.BACKEND_CONTRACT_COVERAGE_DOC_TARGETS.values()) != set(
        contract_mod.BACKEND_CONTRACT_COVERAGE_REQUIRED_DOC_NEEDLES
    ):
        issues.append("coverage contract doc targets drifted away from required-doc inventory")
    for rel, needles in contract_mod.BACKEND_CONTRACT_COVERAGE_REQUIRED_DOC_NEEDLES.items():
        path = ROOT / rel
        if not path.exists():
            issues.append(f"missing coverage contract doc target: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing coverage contract doc needle: {rel}: {needle}")
    return issues


def main() -> int:
    issues = _collect_contract_issues() + _collect_doc_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage contract is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

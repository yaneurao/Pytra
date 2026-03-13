#!/usr/bin/env python3
"""Validate docs/export/checker handoff for backend contract coverage."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import (
    backend_contract_coverage_handoff_contract as contract_mod,
)
from tools import export_backend_contract_coverage_docs as export_mod


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_contract_coverage_handoff_manifest()
    if manifest["contract_version"] != 1:
        issues.append("coverage handoff contract version must stay at 1")
    for relpath in contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS.values():
        if not (ROOT / relpath).exists():
            issues.append(f"missing coverage handoff doc target: {relpath}")
    for relpath in contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_EXPORTS.values():
        if not (ROOT / relpath).exists():
            issues.append(f"missing coverage handoff export/checker path: {relpath}")
    for relpath in contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_SOURCES.values():
        if not (ROOT / relpath).exists():
            issues.append(f"missing coverage handoff source path: {relpath}")
    return issues


def _collect_doc_issues() -> list[str]:
    issues: list[str] = []
    if set(contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS.values()) != set(
        contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_REQUIRED_DOC_NEEDLES
    ):
        issues.append("coverage handoff doc target inventory drifted")
    for relpath, needles in contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_REQUIRED_DOC_NEEDLES.items():
        path = ROOT / relpath
        if not path.exists():
            issues.append(f"missing coverage handoff doc target: {relpath}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"missing coverage handoff doc needle: {relpath}: {needle}")
    return issues


def _collect_export_issues() -> list[str]:
    issues: list[str] = []
    for relpath in (
        contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS["coverage_matrix_ja"],
        contract_mod.BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS["coverage_matrix_en"],
    ):
        path = ROOT / relpath
        current = path.read_text(encoding="utf-8")
        expected = export_mod.render_updated_doc_text(current)
        if expected != current:
            issues.append(f"stale exported backend coverage doc: {relpath}")
    return issues


def main() -> int:
    issues = _collect_manifest_issues() + _collect_doc_issues() + _collect_export_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend contract coverage handoff contract is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

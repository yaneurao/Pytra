#!/usr/bin/env python3
"""Guard the final handoff contract for the cpp py_runtime residual thin-seam task."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_cpp_pyruntime_contract_inventory as contract_mod
from tools import check_cpp_pyruntime_header_surface as header_mod
from tools import check_cpp_pyruntime_residual_thin_seam_contract as seam_mod
from tools import check_crossruntime_pyruntime_emitter_inventory as emitter_mod

ACTIVE_TASK_ID = "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01"
ACTIVE_PLAN_PATH = "docs/ja/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md"

BUNDLE_ORDER = (
    "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S1-01",
    "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-01",
    "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-02",
    "P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S3-01",
)

REPRESENTATIVE_CHECKS = (
    "tools/check_cpp_pyruntime_header_surface.py",
    "tools/check_cpp_pyruntime_contract_inventory.py",
    "tools/check_crossruntime_pyruntime_emitter_inventory.py",
    "tools/check_cpp_pyruntime_residual_thin_seam_contract.py",
)

REPRESENTATIVE_TEST_FILES = (
    "test/unit/tooling/test_check_cpp_pyruntime_header_surface.py",
    "test/unit/tooling/test_check_cpp_pyruntime_contract_inventory.py",
    "test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py",
    "test/unit/tooling/test_check_cpp_pyruntime_residual_thin_seam_contract.py",
)


def _collect_handoff_issues() -> list[str]:
    issues: list[str] = []
    if not (ROOT / ACTIVE_PLAN_PATH).exists():
        issues.append(f"active p5 plan missing: {ACTIVE_PLAN_PATH}")
    if header_mod.FOLLOWUP_TASK_ID != ACTIVE_TASK_ID:
        issues.append("header surface follow-up task drifted")
    if header_mod.FOLLOWUP_PLAN_PATH != ACTIVE_PLAN_PATH:
        issues.append("header surface follow-up plan path drifted")
    if header_mod.BUNDLE_ORDER != BUNDLE_ORDER:
        issues.append("header surface bundle order drifted")
    if emitter_mod.FUTURE_FOLLOWUP_TASK_ID != ACTIVE_TASK_ID:
        issues.append("emitter inventory follow-up task drifted")
    if emitter_mod.FUTURE_FOLLOWUP_PLAN_PATH != ACTIVE_PLAN_PATH:
        issues.append("emitter inventory follow-up plan path drifted")
    if emitter_mod.FUTURE_HANDOFF_TARGETS["cpp_header_shrink"]["plan_path"] != ACTIVE_PLAN_PATH:
        issues.append("emitter handoff target drifted from active p5 plan")
    if header_mod._collect_handoff_issues():
        issues.append("header surface handoff issues are not empty")
    if contract_mod._collect_inventory_issues():
        issues.append("contract inventory issues are not empty")
    if seam_mod._collect_issues():
        issues.append("residual thin-seam classification issues are not empty")
    if emitter_mod._collect_future_followup_issues():
        issues.append("emitter future follow-up issues are not empty")
    for rel in REPRESENTATIVE_CHECKS + REPRESENTATIVE_TEST_FILES:
        if not (ROOT / rel).exists():
            issues.append(f"representative handoff path missing: {rel}")
    return issues


def main() -> int:
    issues = _collect_handoff_issues()
    if not issues:
        print("[OK] cpp py_runtime residual thin-seam handoff contract is classified")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

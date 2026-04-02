#!/usr/bin/env python3
"""Run local CI-equivalent checks in a fixed order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    return int(p.returncode)


def build_steps() -> list[list[str]]:
    return [
        ["python3", "tools/check/check_tools_ledger.py"],
        ["python3", "tools/check/check_mapping_json.py"],
        ["python3", "tools/check/check_legacy_cli_references.py"],
        ["python3", "tools/check/check_legacy_transpile_checkers_absent.py"],
        ["python3", "tools/check/check_todo_priority.py"],
        ["python3", "tools/check/check_jsonvalue_decode_boundaries.py"],
        ["python3", "tools/check/check_jsonvalue_typeexpr_contract.py"],
        ["python3", "tools/check/check_east_stage_boundary.py"],
        ["python3", "tools/gen/gen_runtime_symbol_index.py", "--check"],
        ["python3", "tools/check/audit_image_runtime_sot.py", "--fail-on-core-mix", "--fail-on-gen-markers"],
        ["python3", "tools/check/check_runtime_std_sot_guard.py"],
        ["python3", "tools/check/check_runtime_special_generators_absent.py"],
        ["python3", "tools/check/check_runtime2_references_absent.py"],
        ["python3", "tools/check/check_runtime_core_gen_markers.py"],
        ["python3", "tools/check/check_runtime_pytra_gen_naming.py"],
        ["python3", "tools/check/check_emitter_runtimecall_guardrails.py"],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/unittest/tooling",
            "-p",
            "test_check_runtime2_references_absent.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/unittest/tooling",
            "-p",
            "test_check_emitter_runtimecall_guardrails.py",
        ],
        ["python3", "tools/check/check_emitter_forbidden_runtime_symbols.py"],
        ["python3", "tools/check/check_runtime_legacy_shims.py"],
        ["python3", "tools/run/run_regen_on_version_bump.py", "--verify-cpp-on-diff"],
        ["python3", "tools/check/check_sample_regen_clean.py"],
        ["python3", "tools/check/check_multilang_quality_regression.py"],
        ["python3", "tools/check/check_py2x_transpile.py", "--target", "cpp"],
        ["python3", "tools/check/check_noncpp_east3_contract.py"],
        ["python3", "tools/check/check_noncpp_backend_health.py", "--family", "all", "--skip-parity"],
        ["python3", "-m", "unittest", "discover", "-s", "tools/unittest/common", "-p", "test_code_emitter.py"],
        ["python3", "-m", "unittest", "discover", "-s", "tools/unittest/emit/cpp", "-p", "test_py2cpp_features.py"],
        ["python3", "-m", "unittest", "discover", "-s", "tools/unittest/emit/cpp", "-p", "test_py2cpp_smoke.py"],
    ]


def main() -> int:
    steps = build_steps()
    for step in steps:
        rc = run(step)
        if rc != 0:
            print(f"[FAIL] {' '.join(step)}")
            return rc
    print("[OK] local CI checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run local CI-equivalent checks in a fixed order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    return int(p.returncode)


def main() -> int:
    steps: list[list[str]] = [
        ["python3", "tools/check_transpiler_version_gate.py"],
        ["python3", "tools/check_legacy_cli_references.py"],
        ["python3", "tools/check_legacy_transpile_checkers_absent.py"],
        ["python3", "tools/check_todo_priority.py"],
        ["python3", "tools/check_py2cpp_boundary.py"],
        ["python3", "tools/check_east_stage_boundary.py"],
        ["python3", "tools/check_py2cpp_helper_guard.py"],
        ["python3", "tools/check_cpp_hooks_semantic_budget.py", "--max-semantic", "0"],
        ["python3", "tools/check_runtime_cpp_layout.py"],
        ["python3", "tools/check_rs_runtime_layout.py"],
        ["python3", "tools/audit_image_runtime_sot.py", "--fail-on-core-mix", "--fail-on-gen-markers"],
        ["python3", "tools/check_runtime_std_sot_guard.py"],
        ["python3", "tools/check_runtime_special_generators_absent.py"],
        ["python3", "tools/check_runtime2_references_absent.py"],
        ["python3", "tools/check_runtime_core_gen_markers.py"],
        ["python3", "tools/check_runtime_pytra_gen_naming.py"],
        ["python3", "tools/check_java_pyruntime_boundary.py"],
        ["python3", "tools/check_java_runtimecall_api_boundary.py"],
        ["python3", "tools/check_emitter_runtimecall_guardrails.py"],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "test/unit/tooling",
            "-p",
            "test_check_runtime2_references_absent.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "test/unit/tooling",
            "-p",
            "test_check_emitter_runtimecall_guardrails.py",
        ],
        ["python3", "tools/check_emitter_forbidden_runtime_symbols.py"],
        ["python3", "tools/check_runtime_legacy_shims.py"],
        ["python3", "tools/run_regen_on_version_bump.py", "--verify-cpp-on-diff"],
        ["python3", "tools/check_sample_regen_clean.py"],
        ["python3", "tools/check_multilang_quality_regression.py"],
        ["python3", "tools/check_multilang_selfhost_suite.py"],
        ["python3", "tools/check_py2x_transpile.py", "--target", "cpp"],
        ["python3", "tools/check_noncpp_east3_contract.py"],
        ["python3", "-m", "unittest", "discover", "-s", "test/unit/common", "-p", "test_code_emitter.py"],
        ["python3", "-m", "unittest", "discover", "-s", "test/unit/backends/cpp", "-p", "test_py2cpp_features.py"],
        ["python3", "-m", "unittest", "discover", "-s", "test/unit/backends/cpp", "-p", "test_py2cpp_smoke.py"],
        ["python3", "tools/build_selfhost.py"],
        [
            "python3",
            "tools/check_selfhost_cpp_diff.py",
            "--mode",
            "allow-not-implemented",
        ],
        [
            "python3",
            "tools/check_selfhost_stage2_cpp_diff.py",
            "--mode",
            "allow-not-implemented",
        ],
    ]
    for step in steps:
        rc = run(step)
        if rc != 0:
            print(f"[FAIL] {' '.join(step)}")
            return rc
    print("[OK] local CI checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

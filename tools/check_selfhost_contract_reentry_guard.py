#!/usr/bin/env python3
"""Run representative host/selfhost contract checks under one entrypoint."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_host_contract_steps() -> list[tuple[str, list[str]]]:
    return [
        (
            "host-entrypoint-contract",
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "test/unit/common",
                "-p",
                "test_py2x_entrypoints_contract.py",
            ],
        ),
    ]


def build_selfhost_contract_steps() -> list[tuple[str, list[str]]]:
    return [
        (
            "selfhost-source-contract",
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "test/unit/selfhost",
                "-p",
                "test_prepare_selfhost_source.py",
            ],
        ),
        (
            "selfhost-build-verify-contract",
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "test/unit/selfhost",
                "-p",
                "test_selfhost_build_verify_tools.py",
            ],
        ),
        (
            "selfhost-diff-contract",
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "test/unit/selfhost",
                "-p",
                "test_check_selfhost_cpp_diff.py",
            ],
        ),
        (
            "selfhost-stage2-diff-contract",
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "test/unit/selfhost",
                "-p",
                "test_check_selfhost_stage2_cpp_diff.py",
            ],
        ),
    ]


def build_reentry_guard_steps() -> list[tuple[str, list[str]]]:
    return [*build_host_contract_steps(), *build_selfhost_contract_steps()]


def run_reentry_guard_steps(steps: list[tuple[str, list[str]]], *, dry_run: bool = False) -> int:
    for label, cmd in steps:
        print("+", " ".join(cmd))
        if dry_run:
            continue
        cp = subprocess.run(cmd, cwd=str(ROOT))
        if cp.returncode != 0:
            print(f"[FAIL] {label}")
            return int(cp.returncode)
    print("[OK] selfhost contract reentry guard passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run representative host/selfhost contract regressions together")
    parser.add_argument("--dry-run", action="store_true", help="print commands without executing them")
    args = parser.parse_args()
    return run_reentry_guard_steps(build_reentry_guard_steps(), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

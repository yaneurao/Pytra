#!/usr/bin/env python3
"""Verify artifact byte parity between Python source and Ruby transpile outputs."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample" / "py"


@dataclass
class CaseResult:
    stem: str
    ok: bool
    detail: str


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True, env=proc_env)


def _parse_output_path(stdout_text: str) -> str:
    m = re.search(r"^output:\s*(.+)$", stdout_text, flags=re.MULTILINE)
    if m is None:
        return ""
    return m.group(1).strip()


def _resolve_output_path(cwd: Path, output_text: str) -> Path:
    p = Path(output_text)
    if p.is_absolute():
        return p
    return cwd / p


def _assert_toolchain() -> tuple[bool, str]:
    if shutil.which("ruby") is None:
        return False, "missing ruby"
    if shutil.which("python3") is None:
        return False, "missing python3"
    return True, ""


def _run_one(stem: str, east3_opt_level: str) -> CaseResult:
    src_py = SAMPLE_ROOT / f"{stem}.py"
    if not src_py.exists():
        return CaseResult(stem, False, f"missing sample source: {src_py}")

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "sample").mkdir(parents=True, exist_ok=True)
        (work / "sample" / "py").symlink_to(SAMPLE_ROOT, target_is_directory=True)
        (work / "sample" / "out").mkdir(parents=True, exist_ok=True)
        (work / "test" / "transpile" / "ruby").mkdir(parents=True, exist_ok=True)

        py = _run(
            ["python3", f"sample/py/{stem}.py"],
            cwd=work,
            env={"PYTHONPATH": "src"},
        )
        if py.returncode != 0:
            detail = py.stderr.strip() or py.stdout.strip() or "python run failed"
            return CaseResult(stem, False, f"python run failed: {detail}")

        py_out_txt = _parse_output_path(py.stdout)
        if py_out_txt == "":
            return CaseResult(stem, False, "python stdout missing 'output:' line")
        py_artifact = _resolve_output_path(work, py_out_txt)
        if not py_artifact.exists() or not py_artifact.is_file():
            return CaseResult(stem, False, f"python artifact missing: {py_artifact}")
        expected_bytes = py_artifact.read_bytes()

        tr = _run(
            [
                "python3",
                "src/py2rb.py",
                f"sample/py/{stem}.py",
                "-o",
                f"test/transpile/ruby/{stem}.rb",
                "--east3-opt-level",
                east3_opt_level,
            ],
            cwd=work,
            env={"PYTHONPATH": "src"},
        )
        if tr.returncode != 0:
            detail = tr.stderr.strip() or tr.stdout.strip() or "ruby transpile failed"
            return CaseResult(stem, False, f"ruby transpile failed: {detail}")

        rb = _run(
            ["ruby", f"test/transpile/ruby/{stem}.rb"],
            cwd=work,
        )
        if rb.returncode != 0:
            detail = rb.stderr.strip() or rb.stdout.strip() or "ruby run failed"
            return CaseResult(stem, False, f"ruby run failed: {detail}")

        rb_out_txt = _parse_output_path(rb.stdout)
        if rb_out_txt == "":
            return CaseResult(stem, False, "ruby stdout missing 'output:' line")
        rb_artifact = _resolve_output_path(work, rb_out_txt)
        if not rb_artifact.exists() or not rb_artifact.is_file():
            return CaseResult(stem, False, f"ruby artifact missing: {rb_artifact}")
        actual_bytes = rb_artifact.read_bytes()

        if expected_bytes != actual_bytes:
            return CaseResult(
                stem,
                False,
                f"artifact mismatch: py={len(expected_bytes)} bytes ruby={len(actual_bytes)} bytes",
            )
        return CaseResult(stem, True, f"artifact bytes matched ({len(actual_bytes)} bytes)")


def main() -> int:
    ap = argparse.ArgumentParser(description="verify sample artifact parity: Python vs Ruby")
    ap.add_argument(
        "--samples",
        nargs="*",
        default=["01_mandelbrot", "06_julia_parameter_sweep"],
        help="sample stems under sample/py (default: 01_mandelbrot 06_julia_parameter_sweep)",
    )
    ap.add_argument(
        "--east3-opt-level",
        default="1",
        choices=("0", "1", "2"),
        help="optimizer level passed to py2rb (default: 1)",
    )
    args = ap.parse_args()

    ok_tools, tool_msg = _assert_toolchain()
    if not ok_tools:
        print(f"[ERROR] {tool_msg}")
        return 2

    failures = 0
    i = 0
    while i < len(args.samples):
        stem = args.samples[i]
        result = _run_one(stem, args.east3_opt_level)
        if result.ok:
            print(f"[OK] {stem}: {result.detail}")
        else:
            failures += 1
            print(f"[FAIL] {stem}: {result.detail}")
        i += 1

    if failures > 0:
        print(f"[FAIL] ruby artifact parity: fail={failures} total={len(args.samples)}")
        return 1
    print(f"[PASS] ruby artifact parity: total={len(args.samples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

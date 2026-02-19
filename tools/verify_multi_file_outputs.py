#!/usr/bin/env python3
"""Verify outputs for py2cpp multi-file mode."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


def run_cmd(cmd: list[str], *, cwd: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    p = subprocess.run(cmd, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def normalize_stdout(text: str) -> str:
    out: list[str] = []
    for ln in text.splitlines():
        low = ln.strip().lower()
        if low.startswith("elapsed_sec:") or low.startswith("elapsed:") or low.startswith("time_sec:"):
            continue
        out.append(ln)
    return "\n".join(out)


def verify_case(root: Path, stem: str) -> tuple[bool, str]:
    py = root / "sample" / "py" / f"{stem}.py"
    if not py.exists():
        return False, f"missing sample: {stem}"
    with tempfile.TemporaryDirectory(prefix="pytra_mf_verify_") as tmpdir:
        work = Path(tmpdir)
        out_dir = work / "out"
        exe = work / "app.out"
        rc, py_stdout = run_cmd(["python3", str(py)], cwd=root)
        if rc != 0:
            return False, f"{stem}: python run failed"
        rc, tr_out = run_cmd(
            ["python3", "src/py2cpp.py", str(py), "--multi-file", "--output-dir", str(out_dir)], cwd=root
        )
        if rc != 0:
            return False, f"{stem}: transpile failed\n{tr_out}"
        rc, bd_out = run_cmd(
            ["python3", "tools/build_multi_cpp.py", str(out_dir / "manifest.json"), "-o", str(exe)], cwd=root
        )
        if rc != 0:
            return False, f"{stem}: build failed\n{bd_out}"
        rc, cpp_stdout = run_cmd([str(exe)], cwd=root)
        if rc != 0:
            return False, f"{stem}: cpp run failed"
        if normalize_stdout(py_stdout) != normalize_stdout(cpp_stdout):
            return False, f"{stem}: stdout mismatch"
    return True, f"{stem}: ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", nargs="*", default=["01_mandelbrot"], help="sample stems to verify")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    ok = 0
    ng = 0
    for stem in args.samples:
        passed, msg = verify_case(root, stem)
        if passed:
            print("OK " + msg)
            ok += 1
        else:
            print("NG " + msg)
            ng += 1
    print(f"SUMMARY OK={ok} NG={ng}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

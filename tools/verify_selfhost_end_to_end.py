#!/usr/bin/env python3
"""Verify direct selfhost end-to-end flow against Python outputs.

Flow per case:
1) run source with CPython and capture stdout
2) transpile source via selfhost binary (direct .py input)
3) compile generated C++ with runtime sources
4) run executable and compare stdout (with optional ignored line prefixes)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELFHOST_BIN = ROOT / "selfhost" / "py2cpp.out"
BUILD_SELFHOST = ROOT / "tools" / "build_selfhost.py"


DEFAULT_CASES = [
    "test/fixtures/core/add.py",
    "test/fixtures/core/str_join_method.py",
    "test/fixtures/control/if_else.py",
    "sample/py/04_monte_carlo_pi.py",
]


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    py_path = env.get("PYTHONPATH", "")
    src_txt = str(ROOT / "src")
    if py_path == "":
        env["PYTHONPATH"] = src_txt
    elif src_txt not in py_path.split(":"):
        env["PYTHONPATH"] = src_txt + ":" + py_path
    return subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True, env=env)


def _runtime_cpp_sources() -> list[str]:
    out: list[str] = []
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "pytra").rglob("*.cpp")):
        out.append(str(p))
    return out


def _normalize_stdout(text: str, ignore_prefixes: list[str]) -> str:
    lines = text.splitlines()
    out_lines: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        skip = False
        j = 0
        while j < len(ignore_prefixes):
            pfx = ignore_prefixes[j]
            if pfx != "" and ln.startswith(pfx):
                skip = True
                break
            j += 1
        if not skip:
            out_lines.append(ln)
        i += 1
    return "\n".join(out_lines)


def _ignore_prefixes_for_case(rel: str) -> list[str]:
    if rel.endswith("sample/py/04_monte_carlo_pi.py"):
        return ["elapsed_sec:"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="verify selfhost direct e2e output parity")
    ap.add_argument("--selfhost-bin", default=str(SELFHOST_BIN), help="path to selfhost binary")
    ap.add_argument("--skip-build", action="store_true", help="skip building selfhost binary")
    ap.add_argument("--cases", nargs="*", default=DEFAULT_CASES, help="python case files")
    args = ap.parse_args()

    selfhost_bin = Path(args.selfhost_bin)
    if not args.skip_build:
        cp_build = _run(["python3", str(BUILD_SELFHOST)])
        if cp_build.returncode != 0:
            msg = cp_build.stderr.strip() or cp_build.stdout.strip()
            print("[FAIL build_selfhost]", msg.splitlines()[:1])
            return 2
    if not selfhost_bin.exists():
        print(f"[FAIL] missing selfhost binary: {selfhost_bin}")
        return 2

    runtime_cpp = _runtime_cpp_sources()
    failures = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        i = 0
        while i < len(args.cases):
            rel = args.cases[i]
            src = ROOT / rel
            if not src.exists():
                print(f"[FAIL missing] {rel}")
                failures += 1
                i += 1
                continue

            py_run = _run(["python3", str(src)])
            if py_run.returncode != 0:
                msg = py_run.stderr.strip() or py_run.stdout.strip()
                print(f"[FAIL python-run] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                i += 1
                continue

            out_cpp = td / (src.stem + ".selfhost.cpp")
            out_bin = td / (src.stem + ".selfhost.out")

            cp_transpile = _run([str(selfhost_bin), str(src), "-o", str(out_cpp)])
            if cp_transpile.returncode != 0:
                msg = cp_transpile.stderr.strip() or cp_transpile.stdout.strip()
                print(f"[FAIL selfhost-transpile] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                i += 1
                continue

            compile_cmd = [
                "g++",
                "-std=c++20",
                "-O2",
                "-Isrc",
                "-Isrc/runtime/cpp",
                str(out_cpp),
                *runtime_cpp,
                "-o",
                str(out_bin),
            ]
            cp_compile = _run(compile_cmd)
            if cp_compile.returncode != 0:
                msg = cp_compile.stderr.strip() or cp_compile.stdout.strip()
                print(f"[FAIL compile] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                i += 1
                continue

            cp_run = _run([str(out_bin)])
            if cp_run.returncode != 0:
                msg = cp_run.stderr.strip() or cp_run.stdout.strip()
                print(f"[FAIL run] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                i += 1
                continue

            ignore_prefixes = _ignore_prefixes_for_case(rel)
            py_stdout = _normalize_stdout(py_run.stdout, ignore_prefixes)
            cpp_stdout = _normalize_stdout(cp_run.stdout, ignore_prefixes)
            if py_stdout != cpp_stdout:
                print(f"[FAIL stdout] {rel}")
                print("  python:", repr(py_stdout))
                print("  selfhost:", repr(cpp_stdout))
                failures += 1
            else:
                print(f"[OK] {rel}")

            i += 1

    print(f"failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

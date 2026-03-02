#!/usr/bin/env python3
"""Benchmark for Nim transpiled output."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY2NIM = ROOT / "src" / "py2nim.py"
ELAPSED_RE = re.compile(r"elapsed(?:_sec)?:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

def _run(cmd: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT / "src")}
    )

def _extract_elapsed(stdout: str) -> float:
    for line in stdout.splitlines():
        m = ELAPSED_RE.search(line.strip())
        if m is not None:
            return float(m.group(1))
    return -1.0

def main() -> int:
    case = "01_mandelbrot"
    src_py = ROOT / "sample" / "py" / f"{case}.py"
    
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        # Nim module names cannot start with numbers
        out_nim = work / "mandelbrot.nim"
        
        print(f"[1/3] Transpiling {case}.py to Nim...")
        tr = _run(f"python3 {PY2NIM} {src_py} -o {out_nim}", work)
        if tr.returncode != 0:
            print(f"Transpilation failed:\n{tr.stderr}")
            return 1
        
        # Ensure py_runtime.nim is included
        src_text = out_nim.read_text(encoding="utf-8")
        out_nim.write_text('include "py_runtime.nim"\n' + src_text, encoding="utf-8")
        
        print(f"[2/3] Compiling {out_nim.name} with Nim...")
        # Use absolute path for nim if not in /bin/sh PATH
        nim_exe = "/Users/jasagiri/.local/share/mise/installs/nim/2.2.6/bin/nim"
        nim_cache = work / "nimcache"
        build = _run(f"{nim_exe} c -d:release --hints:off --nimcache:{nim_cache} {out_nim}", work)
        if build.returncode != 0:
            print(f"Compilation failed:\n{build.stderr}")
            return 1
        
        binary = work / "mandelbrot"
        if not binary.exists():
             binary = work / "mandelbrot.exe"
        
        print(f"[3/3] Running {case} binary...")
        run = _run(str(binary), work)
        if run.returncode != 0:
            print(f"Execution failed:\n{run.stderr}")
            return 1
        
        elapsed = _extract_elapsed(run.stdout)
        if elapsed >= 0:
            print(f"\nBenchmark Result for {case}:")
            print(f"Nim: {elapsed:.3f} s")
            
            # For comparison, show Python/PyPy values from README
            print("\nReference from README (Workload 01):")
            print("Python: 18.647 s")
            print("C++:    0.790 s")
            print("Rust:   0.781 s")
        else:
            print("Could not find elapsed_sec in output:")
            print(run.stdout)
            
    return 0

if __name__ == "__main__":
    sys.exit(main())

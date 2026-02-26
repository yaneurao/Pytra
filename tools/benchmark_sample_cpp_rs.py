#!/usr/bin/env python3
"""Benchmark sample/py cases for transpiled C++ and Rust outputs."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import statistics
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample" / "py"


ELAPSED_RE = re.compile(r"elapsed(?:_sec)?:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


@dataclass
class CaseResult:
    case: str
    cpp_median: float
    rs_median: float
    cpp_runs: list[float]
    rs_runs: list[float]

    @property
    def rs_over_cpp(self) -> float:
        if self.cpp_median == 0.0:
            return 0.0
        return self.rs_median / self.cpp_median


def _run(cmd: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        env=proc_env,
    )


def _runtime_cpp_sources_shell() -> str:
    parts: list[str] = []
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "base").glob("*.cpp")):
        parts.append(shlex.quote(p.relative_to(ROOT).as_posix()))
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "pytra").rglob("*.cpp")):
        parts.append(shlex.quote(p.relative_to(ROOT).as_posix()))
    return " ".join(parts)


def _extract_elapsed(stdout: str) -> float:
    for line in stdout.splitlines():
        m = ELAPSED_RE.search(line.strip())
        if m is not None:
            return float(m.group(1))
    raise RuntimeError("elapsed_sec not found in stdout")


def _run_repeated(binary_cmd: str, cwd: Path, warmup: int, repeat: int) -> list[float]:
    warm = 0
    while warm < warmup:
        p = _run(binary_cmd, cwd)
        if p.returncode != 0:
            raise RuntimeError("warmup failed: " + p.stderr.strip())
        _ = _extract_elapsed(p.stdout)
        warm += 1

    out: list[float] = []
    i = 0
    while i < repeat:
        p = _run(binary_cmd, cwd)
        if p.returncode != 0:
            raise RuntimeError("run failed: " + p.stderr.strip())
        out.append(_extract_elapsed(p.stdout))
        i += 1
    return out


def _collect_cases(cases: list[str]) -> list[str]:
    if len(cases) > 0:
        return cases
    out: list[str] = []
    for p in sorted(SAMPLE_ROOT.glob("*.py")):
        if p.stem == "__init__":
            continue
        out.append(p.stem)
    return out


def benchmark_case(case: str, work: Path, warmup: int, repeat: int, runtime_cpp: str) -> CaseResult:
    sample_path = SAMPLE_ROOT / f"{case}.py"
    if not sample_path.is_file():
        raise RuntimeError("missing case: " + case)
    src = sample_path.as_posix()

    tr_cpp = _run(f"python src/py2cpp.py {shlex.quote(src)} test/transpile/cpp/{case}.cpp", work)
    if tr_cpp.returncode != 0:
        raise RuntimeError("py2cpp failed: " + tr_cpp.stderr.strip())
    tr_rs = _run(f"python src/py2rs.py {shlex.quote(src)} -o test/transpile/rs/{case}.rs", work)
    if tr_rs.returncode != 0:
        raise RuntimeError("py2rs failed: " + tr_rs.stderr.strip())

    build_cpp = (
        f"g++ -std=c++20 -O2 -I src test/transpile/cpp/{case}.cpp "
        "-I src/runtime/cpp "
        f"{runtime_cpp} "
        f"-o test/transpile/obj/{case}_cpp.out"
    )
    b_cpp = _run(build_cpp, work)
    if b_cpp.returncode != 0:
        raise RuntimeError("g++ failed: " + b_cpp.stderr.strip())

    build_rs = f"rustc -O test/transpile/rs/{case}.rs -o test/transpile/obj/{case}_rs.out"
    b_rs = _run(build_rs, work)
    if b_rs.returncode != 0:
        raise RuntimeError("rustc failed: " + b_rs.stderr.strip())

    cpp_runs = _run_repeated(f"test/transpile/obj/{case}_cpp.out", work, warmup, repeat)
    rs_runs = _run_repeated(f"test/transpile/obj/{case}_rs.out", work, warmup, repeat)

    return CaseResult(
        case=case,
        cpp_median=float(statistics.median(cpp_runs)),
        rs_median=float(statistics.median(rs_runs)),
        cpp_runs=cpp_runs,
        rs_runs=rs_runs,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark transpiled C++ and Rust sample cases")
    parser.add_argument("cases", nargs="*", help="sample case stems (default: all sample/py cases)")
    parser.add_argument("--warmup", type=int, default=1, help="warmup runs per target")
    parser.add_argument("--repeat", type=int, default=5, help="measured runs per target")
    parser.add_argument("--emit-json", default="", help="optional JSON output path (repo-relative)")
    args = parser.parse_args()

    cases = _collect_cases(args.cases)
    if len(cases) == 0:
        raise RuntimeError("no cases to benchmark")

    runtime_cpp = _runtime_cpp_sources_shell()
    results: list[CaseResult] = []
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "sample").symlink_to(ROOT / "sample", target_is_directory=True)
        (work / "test" / "transpile" / "cpp").mkdir(parents=True, exist_ok=True)
        (work / "test" / "transpile" / "rs").mkdir(parents=True, exist_ok=True)
        (work / "test" / "transpile" / "obj").mkdir(parents=True, exist_ok=True)

        for case in cases:
            print(f"[RUN] {case}")
            result = benchmark_case(case, work, args.warmup, args.repeat, runtime_cpp)
            results.append(result)
            print(
                f"[OK] {case} cpp={result.cpp_median:.3f}s rs={result.rs_median:.3f}s rs/cpp={result.rs_over_cpp:.2f}x"
            )

    print("")
    print("| case | cpp_median | rs_median | rs/cpp |")
    print("|---|---:|---:|---:|")
    for row in results:
        print(f"| {row.case} | {row.cpp_median:.3f} | {row.rs_median:.3f} | {row.rs_over_cpp:.2f}x |")

    if args.emit_json != "":
        out_path = ROOT / args.emit_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "warmup": args.warmup,
            "repeat": args.repeat,
            "cases": [
                {
                    "case": r.case,
                    "cpp_median": r.cpp_median,
                    "rs_median": r.rs_median,
                    "rs_over_cpp": r.rs_over_cpp,
                    "cpp_runs": r.cpp_runs,
                    "rs_runs": r.rs_runs,
                }
                for r in results
            ],
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("")
        print("json:", out_path.relative_to(ROOT).as_posix())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

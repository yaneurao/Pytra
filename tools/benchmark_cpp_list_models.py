#!/usr/bin/env python3
"""Benchmark sample/py cases for C++ list models (value vs pyobj)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample" / "py"
ELAPSED_RE = re.compile(r"elapsed(?:_sec)?:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

sys.path.insert(0, str(ROOT / "src"))
from py2cpp import load_east  # noqa: E402
from hooks.cpp.emitter import CppEmitter  # noqa: E402


@dataclass
class ModelResult:
    elapsed_runs: list[float]
    elapsed_avg: float
    binary_size: int
    source_size: int
    source_lines: int


@dataclass
class CaseResult:
    case: str
    value: ModelResult
    pyobj: ModelResult
    changed_lines: int

    @property
    def elapsed_ratio(self) -> float:
        if self.value.elapsed_avg == 0.0:
            return 0.0
        return self.pyobj.elapsed_avg / self.value.elapsed_avg

    @property
    def binary_size_ratio(self) -> float:
        if self.value.binary_size == 0:
            return 0.0
        return float(self.pyobj.binary_size) / float(self.value.binary_size)

    @property
    def source_size_ratio(self) -> float:
        if self.value.source_size == 0:
            return 0.0
        return float(self.pyobj.source_size) / float(self.value.source_size)


def _run(cmd: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
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


def _render_cpp(case_path: Path, model: str) -> str:
    east = load_east(
        case_path,
        parser_backend="self_hosted",
        east_stage="3",
        object_dispatch_mode="native",
        east3_opt_level="1",
        east3_opt_pass="",
    )
    em = CppEmitter(east, {}, emit_main=True)
    em.cpp_list_model = model
    return em.transpile()


def _count_changed_lines(a_text: str, b_text: str) -> int:
    a_lines = a_text.splitlines()
    b_lines = b_text.splitlines()
    max_len = len(a_lines) if len(a_lines) > len(b_lines) else len(b_lines)
    changed = 0
    i = 0
    while i < max_len:
        a_line = a_lines[i] if i < len(a_lines) else ""
        b_line = b_lines[i] if i < len(b_lines) else ""
        if a_line != b_line:
            changed += 1
        i += 1
    return changed


def _collect_cases(cases: list[str]) -> list[str]:
    if len(cases) > 0:
        return cases
    out: list[str] = []
    for p in sorted(SAMPLE_ROOT.glob("*.py")):
        if p.stem == "__init__":
            continue
        out.append(p.stem)
    return out


def _build_and_measure_one(
    case: str,
    model: str,
    work: Path,
    runtime_cpp: str,
    warmup: int,
    repeat: int,
) -> tuple[ModelResult, str]:
    src_py = SAMPLE_ROOT / f"{case}.py"
    cpp_path = work / "test" / "transpile" / "cpp" / f"{case}_{model}.cpp"
    out_bin = work / "test" / "transpile" / "obj" / f"{case}_{model}.out"

    cpp_text = _render_cpp(src_py, model)
    cpp_path.write_text(cpp_text, encoding="utf-8")

    build_cpp = (
        f"g++ -std=c++20 -O2 -I src {shlex.quote(cpp_path.relative_to(work).as_posix())} "
        "-I src/runtime/cpp "
        f"{runtime_cpp} "
        f"-o {shlex.quote(out_bin.relative_to(work).as_posix())}"
    )
    b_cpp = _run(build_cpp, work)
    if b_cpp.returncode != 0:
        raise RuntimeError("g++ failed (" + model + "): " + b_cpp.stderr.strip())

    runs = _run_repeated(shlex.quote(out_bin.relative_to(work).as_posix()), work, warmup, repeat)
    result = ModelResult(
        elapsed_runs=runs,
        elapsed_avg=float(statistics.fmean(runs)),
        binary_size=int(out_bin.stat().st_size),
        source_size=len(cpp_text.encode("utf-8")),
        source_lines=len(cpp_text.splitlines()),
    )
    return result, cpp_text


def benchmark_case(case: str, work: Path, runtime_cpp: str, warmup: int, repeat: int) -> CaseResult:
    value_result, value_cpp = _build_and_measure_one(case, "value", work, runtime_cpp, warmup, repeat)
    pyobj_result, pyobj_cpp = _build_and_measure_one(case, "pyobj", work, runtime_cpp, warmup, repeat)
    changed_lines = _count_changed_lines(value_cpp, pyobj_cpp)
    return CaseResult(case=case, value=value_result, pyobj=pyobj_result, changed_lines=changed_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark C++ list models (value vs pyobj) on sample cases")
    parser.add_argument("cases", nargs="*", help="sample case stems (default: all sample/py cases)")
    parser.add_argument("--warmup", type=int, default=1, help="warmup runs per model")
    parser.add_argument("--repeat", type=int, default=2, help="measured runs per model (average over repeats)")
    parser.add_argument("--emit-json", default="", help="optional JSON output path (repo-relative)")
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="continue on per-case failures and exit 0 (failures are reported in stdout/json)",
    )
    args = parser.parse_args()

    cases = _collect_cases(args.cases)
    if len(cases) == 0:
        raise RuntimeError("no cases to benchmark")

    runtime_cpp = _runtime_cpp_sources_shell()
    results: list[CaseResult] = []
    failures: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "sample").symlink_to(ROOT / "sample", target_is_directory=True)
        (work / "test" / "transpile" / "cpp").mkdir(parents=True, exist_ok=True)
        (work / "test" / "transpile" / "obj").mkdir(parents=True, exist_ok=True)

        for case in cases:
            print(f"[RUN] {case}")
            try:
                result = benchmark_case(case, work, runtime_cpp, args.warmup, args.repeat)
                results.append(result)
                print(
                    f"[OK] {case} elapsed(pyobj/value)={result.elapsed_ratio:.2f}x "
                    f"bin(pyobj/value)={result.binary_size_ratio:.2f}x changed_lines={result.changed_lines}"
                )
            except Exception as ex:
                msg = str(ex)
                failures.append({"case": case, "error": msg})
                print(f"[FAIL] {case} {msg}")

    if len(results) > 0:
        print("")
        print(
            "| case | value_avg(sec) | pyobj_avg(sec) | pyobj/value | value(bin) | pyobj(bin) | pyobj/value(bin) | changed_lines |"
        )
        print("|---|---:|---:|---:|---:|---:|---:|---:|")
        for row in results:
            print(
                f"| {row.case} | {row.value.elapsed_avg:.3f} | {row.pyobj.elapsed_avg:.3f} | {row.elapsed_ratio:.2f}x "
                f"| {row.value.binary_size} | {row.pyobj.binary_size} | {row.binary_size_ratio:.2f}x | {row.changed_lines} |"
            )

    elapsed_ratios = [r.elapsed_ratio for r in results if r.elapsed_ratio > 0.0]
    bin_ratios = [r.binary_size_ratio for r in results if r.binary_size_ratio > 0.0]
    src_ratios = [r.source_size_ratio for r in results if r.source_size_ratio > 0.0]
    if len(elapsed_ratios) > 0 and len(bin_ratios) > 0 and len(src_ratios) > 0:
        print("")
        print(
            "summary: "
            + f"elapsed_avg(pyobj/value)={statistics.fmean(elapsed_ratios):.3f}x, "
            + f"bin_avg(pyobj/value)={statistics.fmean(bin_ratios):.3f}x, "
            + f"src_avg(pyobj/value)={statistics.fmean(src_ratios):.3f}x"
        )

    if len(failures) > 0:
        print("")
        print("failures:")
        for ent in failures:
            print(f"- {ent['case']}: {ent['error']}")

    if args.emit_json != "":
        out_path = ROOT / args.emit_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "warmup": args.warmup,
            "repeat": args.repeat,
            "success_count": len(results),
            "failure_count": len(failures),
            "cases": [
                {
                    "case": r.case,
                    "value": {
                        "elapsed_runs": r.value.elapsed_runs,
                        "elapsed_avg": r.value.elapsed_avg,
                        # Backward-compatible key (same numeric value as elapsed_avg).
                        "elapsed_median": r.value.elapsed_avg,
                        "binary_size": r.value.binary_size,
                        "source_size": r.value.source_size,
                        "source_lines": r.value.source_lines,
                    },
                    "pyobj": {
                        "elapsed_runs": r.pyobj.elapsed_runs,
                        "elapsed_avg": r.pyobj.elapsed_avg,
                        # Backward-compatible key (same numeric value as elapsed_avg).
                        "elapsed_median": r.pyobj.elapsed_avg,
                        "binary_size": r.pyobj.binary_size,
                        "source_size": r.pyobj.source_size,
                        "source_lines": r.pyobj.source_lines,
                    },
                    "elapsed_ratio": r.elapsed_ratio,
                    "binary_size_ratio": r.binary_size_ratio,
                    "source_size_ratio": r.source_size_ratio,
                    "changed_lines": r.changed_lines,
                }
                for r in results
            ],
            "failures": failures,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("")
        print("json:", out_path.relative_to(ROOT).as_posix())

    if len(failures) > 0 and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify `sample/py` outputs against C++ outputs using golden baselines.

Default behavior:
- Load baseline from `sample/golden/manifest.json`
- Transpile+compile+run C++ and compare against the baseline

Refresh behavior:
- `--refresh-golden`: run Python samples and update golden baseline entries
- `--refresh-golden-only`: update baselines without running C++ verification
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERBOSE = False
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLDEN_MANIFEST = ROOT / "sample" / "golden" / "manifest.json"
MANIFEST_SCHEMA_VERSION = 1


@dataclass
class CaseResult:
    stem: str
    ok: bool
    message: str


def run_cmd(cmd: list[str], *, env: dict[str, str] | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    return p.returncode, p.stdout


def vlog(msg: str) -> None:
    if VERBOSE:
        print(msg, flush=True)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_output_path(stdout_text: str) -> str | None:
    m = re.search(r"^output:\s*(.+)$", stdout_text, flags=re.M)
    return m.group(1).strip() if m else None


def normalize_stdout_for_compare(stdout_text: str) -> str:
    """Normalize stdout by removing unstable timing lines."""
    out_lines: list[str] = []
    for line in stdout_text.splitlines():
        low = line.strip().lower()
        if low.startswith("elapsed_sec:") or low.startswith("elapsed:") or low.startswith("time_sec:"):
            continue
        out_lines.append(line)
    return "\n".join(out_lines)


def runtime_cpp_sources() -> list[str]:
    """Return runtime/cpp implementation sources without hardcoded module names."""
    out: list[str] = []
    seen: set[str] = set()
    for p in sorted(Path("src/runtime/cpp/pytra/built_in").glob("*.cpp")):
        rel = p.as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        out.append(rel)
    for p in sorted(Path("src/runtime/cpp/pytra").rglob("*.cpp")):
        rel = p.as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        out.append(rel)
    return out


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": MANIFEST_SCHEMA_VERSION, "cases": {}}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"failed to parse golden manifest: {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise RuntimeError(f"golden manifest must be a JSON object: {path}")
    schema = obj.get("schema_version")
    if schema != MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"unsupported golden manifest schema: {schema} (expected {MANIFEST_SCHEMA_VERSION})"
        )
    cases = obj.get("cases")
    if not isinstance(cases, dict):
        raise RuntimeError(f"golden manifest 'cases' must be object: {path}")
    return obj


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(txt + "\n", encoding="utf-8")


def _source_sha256(stem: str) -> str:
    src = Path("sample/py") / f"{stem}.py"
    return _sha256_file(src)


def _collect_python_baseline(stem: str) -> tuple[bool, str, dict[str, Any] | None]:
    py = Path("sample/py") / f"{stem}.py"
    if not py.exists():
        return False, "python source missing", None

    rc, py_stdout = run_cmd(["python3", str(py)], env={**os.environ, "PYTHONPATH": "src"})
    if rc != 0:
        return False, "python run failed", None

    stdout_norm = normalize_stdout_for_compare(py_stdout)
    out_path_txt = parse_output_path(py_stdout)

    artifact_obj: dict[str, Any] | None = None
    if out_path_txt is not None:
        out_path = Path(out_path_txt)
        if not out_path.exists() or not out_path.is_file():
            return False, f"python output artifact missing: {out_path_txt}", None
        artifact_obj = {
            "suffix": out_path.suffix.lower(),
            "sha256": _sha256_file(out_path),
            "size": int(out_path.stat().st_size),
        }

    baseline = {
        "source_rel": py.as_posix(),
        "source_sha256": _source_sha256(stem),
        "stdout_normalized": stdout_norm,
        "stdout_sha256": hashlib.sha256(stdout_norm.encode("utf-8")).hexdigest(),
        "artifact": artifact_obj,
    }
    return True, "baseline updated", baseline


def _verify_cpp_against_baseline(
    stem: str,
    *,
    baseline: dict[str, Any],
    work: Path,
    compile_flags: list[str],
    ignore_stdout: bool,
) -> CaseResult:
    py = Path("sample/py") / f"{stem}.py"
    cpp = work / f"{stem}.cpp"
    exe = work / f"{stem}.out"

    baseline_src_sha = str(baseline.get("source_sha256", ""))
    current_src_sha = _source_sha256(stem)
    if baseline_src_sha != current_src_sha:
        return CaseResult(
            stem,
            False,
            "golden is stale for current source (run --refresh-golden)",
        )

    t1 = time.time()
    vlog(f"[{stem}] transpile start")
    rc, transpile_out = run_cmd(["python3", "src/py2cpp.py", str(py), "-o", str(cpp)])
    vlog(f"[{stem}] transpile done ({time.time() - t1:.2f}s)")
    if rc != 0:
        first = transpile_out.strip().splitlines()
        msg = first[0] if len(first) > 0 else "transpile failed"
        return CaseResult(stem, False, f"transpile failed: {msg}")

    t2 = time.time()
    vlog(f"[{stem}] cpp compile start")
    rc, compile_out = run_cmd(
        [
            "g++",
            "-std=c++20",
            *compile_flags,
            "-I",
            "src",
            "-I",
            "src/runtime/cpp",
            str(cpp),
            *runtime_cpp_sources(),
            "-o",
            str(exe),
        ]
    )
    vlog(f"[{stem}] cpp compile done ({time.time() - t2:.2f}s)")
    if rc != 0:
        first = compile_out.strip().splitlines()
        msg = first[0] if len(first) > 0 else "cpp compile failed"
        return CaseResult(stem, False, f"cpp compile failed: {msg}")

    t3 = time.time()
    vlog(f"[{stem}] cpp run start")
    rc, cpp_stdout = run_cmd([str(exe)])
    vlog(f"[{stem}] cpp run done ({time.time() - t3:.2f}s)")
    if rc != 0:
        first = cpp_stdout.strip().splitlines()
        msg = first[0] if len(first) > 0 else "cpp run failed"
        return CaseResult(stem, False, f"cpp run failed: {msg}")

    # stdout compare
    if not ignore_stdout:
        cpp_norm = normalize_stdout_for_compare(cpp_stdout)
        expected_norm = str(baseline.get("stdout_normalized", ""))
        if cpp_norm != expected_norm:
            return CaseResult(stem, False, "stdout mismatch vs golden")

    # artifact compare
    expected_artifact_obj = baseline.get("artifact")
    cpp_out_txt = parse_output_path(cpp_stdout)

    if expected_artifact_obj is None:
        if cpp_out_txt is None:
            return CaseResult(stem, True, "stdout=ok image=none")
        return CaseResult(stem, False, "artifact presence mismatch (golden:none, cpp:exists)")

    if not isinstance(expected_artifact_obj, dict):
        return CaseResult(stem, False, "invalid golden artifact metadata")
    if cpp_out_txt is None:
        return CaseResult(stem, False, "artifact presence mismatch (golden:exists, cpp:none)")

    cpp_artifact = Path(cpp_out_txt)
    if not cpp_artifact.exists() or not cpp_artifact.is_file():
        return CaseResult(stem, False, f"cpp output artifact missing: {cpp_out_txt}")

    expected_suffix = str(expected_artifact_obj.get("suffix", ""))
    expected_sha = str(expected_artifact_obj.get("sha256", ""))
    expected_size = int(expected_artifact_obj.get("size", -1))

    actual_suffix = cpp_artifact.suffix.lower()
    actual_sha = _sha256_file(cpp_artifact)
    actual_size = int(cpp_artifact.stat().st_size)

    if expected_suffix != actual_suffix:
        return CaseResult(stem, False, f"artifact suffix mismatch: {expected_suffix} vs {actual_suffix}")
    if expected_size != actual_size:
        return CaseResult(stem, False, f"artifact size mismatch: {expected_size} vs {actual_size}")
    if expected_sha != actual_sha:
        return CaseResult(stem, False, "artifact hash mismatch")

    return CaseResult(stem, True, "stdout=ok image=ok")


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify sample/py vs transpiled C++ outputs")
    ap.add_argument("--samples", nargs="*", default=None, help="sample stems (e.g. 01_mandelbrot)")
    ap.add_argument("--compile-flags", default="-O2", help="extra g++ compile flags (space-separated)")
    ap.add_argument("--verbose", action="store_true", help="print phase timings")
    ap.add_argument("--ignore-stdout", action="store_true", help="judge only artifact parity and ignore stdout differences")
    ap.add_argument(
        "--golden-manifest",
        default=str(DEFAULT_GOLDEN_MANIFEST),
        help="golden manifest JSON path",
    )
    ap.add_argument(
        "--refresh-golden",
        action="store_true",
        help="run Python samples and refresh golden baseline entries",
    )
    ap.add_argument(
        "--refresh-golden-only",
        action="store_true",
        help="with --refresh-golden, refresh baseline only (skip C++ transpile/compile/run)",
    )
    args = ap.parse_args()

    if args.refresh_golden_only and not args.refresh_golden:
        print("[ERROR] --refresh-golden-only requires --refresh-golden")
        return 2

    global VERBOSE
    VERBOSE = args.verbose

    if args.samples is None:
        stems = [p.stem for p in sorted(Path("sample/py").glob("*.py"))]
    else:
        stems = args.samples

    compile_flags = [x for x in args.compile_flags.split(" ") if x]

    manifest_path = Path(args.golden_manifest)
    try:
        manifest = _load_manifest(manifest_path)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 2

    cases_obj = manifest.get("cases")
    if not isinstance(cases_obj, dict):
        print("[ERROR] golden manifest 'cases' must be object")
        return 2

    work = Path(tempfile.mkdtemp(prefix="pytra_verify_sample_"))
    print(f"work={work}")

    ok = 0
    ng = 0
    updated = 0

    for stem in stems:
        baseline_obj: dict[str, Any] | None = None

        if args.refresh_golden:
            good, msg, baseline_new = _collect_python_baseline(stem)
            if not good or baseline_new is None:
                ng += 1
                print(f"NG {stem}: {msg}")
                continue
            cases_obj[stem] = baseline_new
            baseline_obj = baseline_new
            updated += 1
            if args.refresh_golden_only:
                ok += 1
                print(f"OK {stem}: golden refreshed")
                continue

        if baseline_obj is None:
            baseline_raw = cases_obj.get(stem)
            if not isinstance(baseline_raw, dict):
                ng += 1
                print(f"NG {stem}: golden baseline missing (run --refresh-golden)")
                continue
            baseline_obj = baseline_raw

        result = _verify_cpp_against_baseline(
            stem,
            baseline=baseline_obj,
            work=work,
            compile_flags=compile_flags,
            ignore_stdout=args.ignore_stdout,
        )
        if result.ok:
            ok += 1
            print(f"OK {stem}: {result.message}")
        else:
            ng += 1
            print(f"NG {stem}: {result.message}")

    if args.refresh_golden:
        _save_manifest(manifest_path, manifest)

    print(f"SUMMARY OK={ok} NG={ng} UPDATED={updated}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

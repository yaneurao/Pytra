#!/usr/bin/env python3
"""Runtime parity check across transpiler targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shlex
import shutil
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "test" / "fixtures"
SAMPLE_ROOT = ROOT / "sample" / "py"
ARTIFACT_OPTIONAL_TARGETS: set[str] = set()


@dataclass
class Target:
    name: str
    transpile_cmd: str
    run_cmd: str
    needs: tuple[str, ...]
    ignore_artifacts: bool = False


@dataclass
class CheckRecord:
    case_stem: str
    target: str
    category: str
    detail: str


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_shell(
    cmd: str,
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=proc_env,
        start_new_session=True,
    )
    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_sec)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=int(proc.returncode or 0),
            stdout=stdout_text,
            stderr=stderr_text,
        )
    except subprocess.TimeoutExpired:
        # Kill the whole process group so compiled runners spawned by the shell
        # cannot continue running in the background.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout_text, stderr_text = proc.communicate()
        timeout_note = f"[TIMEOUT] exceeded {timeout_sec}s: {cmd}"
        if stderr_text == "":
            stderr_text = timeout_note
        else:
            stderr_text = stderr_text.rstrip() + "\n" + timeout_note
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout_text,
            stderr=stderr_text,
        )


def can_run(target: Target) -> bool:
    for tool in target.needs:
        if tool.startswith("/"):
            if Path(tool).is_file():
                continue
            return False
        if shutil.which(tool) is None:
            return False
    return True


def _normalize_output_for_compare(stdout_text: str) -> str:
    lines: list[str] = []
    for line in stdout_text.splitlines():
        low = line.strip().lower()
        if low.startswith("elapsed_sec:") or low.startswith("elapsed:") or low.startswith("time_sec:"):
            continue
        lines.append(line)
    return "\n".join(lines)


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


def _safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    if path.exists() and path.is_file():
        path.unlink()


def _file_crc32(path: Path) -> int:
    crc = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 16)
            if chunk == b"":
                break
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


def _crc32_hex(v: int) -> str:
    return f"0x{(v & 0xFFFFFFFF):08x}"


def _purge_case_artifacts(work: Path, case_stem: str) -> None:
    # Always remove stale artifacts before each run so parity checks cannot pass
    # by reusing files left by a previous language execution.
    for out_dir in (work / "sample" / "out", work / "test" / "out", work / "out"):
        if not out_dir.exists() or not out_dir.is_dir():
            continue
        for p in sorted(out_dir.glob(f"{case_stem}.*")):
            if p.is_file():
                p.unlink()


def find_case_path(case_stem: str, case_root: str) -> Path | None:
    root = SAMPLE_ROOT if case_root == "sample" else FIXTURE_ROOT
    matches = sorted(root.rglob(f"{case_stem}.py"))
    if not matches:
        return None
    return matches[0]


def collect_sample_case_stems() -> list[str]:
    out: list[str] = []
    for p in sorted(SAMPLE_ROOT.glob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        out.append(stem)
    return out


def resolve_case_stems(cases: list[str], case_root: str, all_samples: bool) -> tuple[list[str], str]:
    if all_samples:
        if case_root != "sample":
            return [], "--all-samples requires --case-root sample"
        if len(cases) > 0:
            return [], "--all-samples cannot be combined with positional cases"
        return collect_sample_case_stems(), ""
    if len(cases) > 0:
        return cases, ""
    if case_root == "sample":
        return collect_sample_case_stems(), ""
    return ["math_extended", "pathlib_extended", "inheritance_virtual_dispatch_multilang"], ""


def build_targets(
    case_stem: str,
    case_path: Path,
    east3_opt_level: str,
) -> list[Target]:
    case_src = case_path.as_posix()
    opt_arg = "--east3-opt-level " + shlex.quote(str(east3_opt_level))

    def _pytra_cmd(target: str, *, build: bool, run: bool) -> str:
        out_dir = f"test/transpile/{target}/{case_stem}"
        parts: list[str] = [
            "python",
            "src/pytra_cli.py",
            shlex.quote(case_src),
            "--target",
            shlex.quote(target),
            "--output-dir",
            shlex.quote(out_dir),
            opt_arg,
        ]
        if build:
            parts.append("--build")
        if run:
            parts.append("--run")
        return " ".join(parts)

    needs_map: dict[str, tuple[str, ...]] = {
        "cpp": ("python", "make", "g++"),
        "rs": ("python", "rustc"),
        "cs": ("python", "mcs", "mono"),
        "js": ("python", "node"),
        "ruby": ("python", "ruby"),
        "lua": ("python", "lua"),
        "php": ("python", "php"),
        "ts": ("python", "node", "npx"),
        "go": ("python", "go"),
        "java": ("python", "javac", "java"),
        "swift": ("python", "swiftc"),
        "kotlin": ("python", "kotlinc", "java"),
        "scala": ("python", "scala"),
        "nim": ("python", "nim"),
    }
    order = [
        "cpp",
        "rs",
        "cs",
        "js",
        "ruby",
        "lua",
        "php",
        "ts",
        "go",
        "java",
        "swift",
        "kotlin",
        "scala",
        "nim",
    ]
    out: list[Target] = []
    for name in order:
        out.append(
            Target(
                name=name,
                transpile_cmd=_pytra_cmd(name, build=False, run=False),
                run_cmd=_pytra_cmd(name, build=True, run=True),
                needs=needs_map[name],
            )
        )
    return out


def check_case(
    case_stem: str,
    enabled_targets: set[str],
    *,
    case_root: str,
    ignore_stdout: bool,
    east3_opt_level: str,
    cmd_timeout_sec: int = 120,
    records: list[CheckRecord] | None = None,
) -> int:
    # Compatibility note:
    # parity compare always ignores unstable timing lines (elapsed_sec / elapsed / time_sec).
    # This parameter remains for backward compatibility with old callers.
    _ = ignore_stdout

    def _record(target: str, category: str, detail: str) -> None:
        if records is None:
            return
        records.append(CheckRecord(case_stem=case_stem, target=target, category=category, detail=detail))

    case_path = find_case_path(case_stem, case_root)
    if case_path is None:
        print(f"[ERROR] missing case: {case_stem}")
        _record("-", "case_missing", "missing case")
        return 1
    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir)
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "test").symlink_to(ROOT / "test", target_is_directory=True)
        if case_root == "sample":
            # Keep outputs isolated in temp dir while reusing sample sources.
            (work / "sample").mkdir(parents=True, exist_ok=True)
            (work / "sample" / "py").symlink_to(ROOT / "sample" / "py", target_is_directory=True)
            (work / "sample" / "out").mkdir(parents=True, exist_ok=True)

        _purge_case_artifacts(work, case_stem)
        run_expr = f"python {shlex.quote(case_path.as_posix())}"
        run_env = {"PYTHONPATH": "src"}
        py = run_shell(run_expr, cwd=work, env=run_env, timeout_sec=cmd_timeout_sec)

        if py.returncode != 0:
            print(f"[ERROR] python:{case_stem} failed")
            print(py.stderr.strip())
            _record("python", "python_failed", py.stderr.strip())
            return 1
        expected = _normalize_output_for_compare(py.stdout)
        expected_artifact_size: int | None = None
        expected_artifact_crc32: int | None = None
        expected_artifact_path: Path | None = None
        expected_out_txt = _parse_output_path(py.stdout)
        if expected_out_txt != "":
            expected_artifact_path = _resolve_output_path(work, expected_out_txt)
            if not expected_artifact_path.exists() or not expected_artifact_path.is_file():
                _record("python", "python_artifact_missing", str(expected_artifact_path))
                print(f"[ERROR] python:{case_stem} artifact missing: {expected_artifact_path}")
                return 1
            expected_artifact_size = int(expected_artifact_path.stat().st_size)
            expected_artifact_crc32 = _file_crc32(expected_artifact_path)

        mismatches: list[str] = []
        for target in build_targets(case_stem, case_path, east3_opt_level):
            if target.name not in enabled_targets:
                continue
            if not can_run(target):
                print(f"[SKIP] {case_stem}:{target.name} (missing toolchain)")
                _record(target.name, "toolchain_missing", "missing toolchain")
                continue

            tr = run_shell(target.transpile_cmd, cwd=work, timeout_sec=cmd_timeout_sec)
            if tr.returncode != 0:
                msg = tr.stderr.strip()
                mismatches.append(f"{case_stem}:{target.name}: transpile failed: {msg}")
                _record(target.name, "transpile_failed", msg)
                continue

            # Ensure target artifact validation is never masked by stale outputs.
            _purge_case_artifacts(work, case_stem)
            _safe_unlink(expected_artifact_path)

            rr = run_shell(target.run_cmd, cwd=work, timeout_sec=cmd_timeout_sec)
            if rr.returncode != 0:
                msg = rr.stderr.strip()
                mismatches.append(f"{case_stem}:{target.name}: run failed: {msg}")
                _record(target.name, "run_failed", msg)
                continue

            actual = _normalize_output_for_compare(rr.stdout)
            if actual != expected:
                _record(target.name, "output_mismatch", "stdout mismatch")
                mismatches.append(
                    f"{case_stem}:{target.name}: output mismatch\n"
                    f"  expected: {expected!r}\n"
                    f"  actual  : {actual!r}"
                )
                continue

            if target.ignore_artifacts or target.name in ARTIFACT_OPTIONAL_TARGETS:
                print(f"[OK] {case_stem}:{target.name}")
                _record(target.name, "ok", "")
                continue

            actual_out_txt = _parse_output_path(rr.stdout)
            if expected_artifact_size is None:
                if actual_out_txt != "":
                    actual_artifact_path = _resolve_output_path(work, actual_out_txt)
                    if actual_artifact_path.exists() and actual_artifact_path.is_file():
                        _record(target.name, "artifact_presence_mismatch", "unexpected artifact")
                        mismatches.append(
                            f"{case_stem}:{target.name}: artifact presence mismatch "
                            "(python:none target:exists)"
                        )
                        continue
                print(f"[OK] {case_stem}:{target.name}")
                _record(target.name, "ok", "")
                continue

            if actual_out_txt == "":
                _record(target.name, "artifact_presence_mismatch", "missing output line")
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact presence mismatch (python:exists target:none)"
                )
                continue

            actual_artifact_path = _resolve_output_path(work, actual_out_txt)
            if not actual_artifact_path.exists() or not actual_artifact_path.is_file():
                _record(target.name, "artifact_missing", str(actual_artifact_path))
                mismatches.append(
                    f"{case_stem}:{target.name}: output artifact missing: {actual_artifact_path}"
                )
                continue

            actual_artifact_size = int(actual_artifact_path.stat().st_size)
            if actual_artifact_size != expected_artifact_size:
                _record(target.name, "artifact_size_mismatch", "size mismatch")
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact size mismatch "
                    f"(python:{expected_artifact_size} target:{actual_artifact_size})"
                )
                continue

            actual_artifact_crc32 = _file_crc32(actual_artifact_path)
            if expected_artifact_crc32 is None:
                expected_artifact_crc32 = _file_crc32(expected_artifact_path)
            if actual_artifact_crc32 != expected_artifact_crc32:
                _record(
                    target.name,
                    "artifact_crc32_mismatch",
                    (
                        f"python:{_crc32_hex(expected_artifact_crc32)} "
                        f"target:{_crc32_hex(actual_artifact_crc32)}"
                    ),
                )
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact crc32 mismatch "
                    f"(python:{_crc32_hex(expected_artifact_crc32)} "
                    f"target:{_crc32_hex(actual_artifact_crc32)})"
                )
                continue

            artifact_info = (
                f"artifact_size={actual_artifact_size} "
                f"artifact_crc32={_crc32_hex(actual_artifact_crc32)}"
            )
            print(f"[OK] {case_stem}:{target.name} {artifact_info}")
            _record(target.name, "ok", artifact_info)

    if mismatches:
        print("\n[FAIL] mismatches")
        for m in mismatches:
            print(f"- {m}")
        return 1

    print(f"[PASS] {case_stem}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run runtime parity checks for stdlib/runtime cases")
    parser.add_argument(
        "cases",
        nargs="*",
        default=[],
        help="case stems (case names without .py).",
    )
    parser.add_argument(
        "--case-root",
        default="fixture",
        choices=("fixture", "sample"),
        help="source root to read cases from (fixture: test/fixtures, sample: sample/py)",
    )
    parser.add_argument(
        "--ignore-unstable-stdout",
        action="store_true",
        help="deprecated compatibility flag; unstable timing lines are always ignored",
    )
    parser.add_argument(
        "--targets",
        default="cpp",
        help="comma separated targets (default: cpp)",
    )
    parser.add_argument(
        "--all-samples",
        action="store_true",
        help="run all cases under sample/py (requires --case-root sample)",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="optional path to write machine-readable summary json",
    )
    parser.add_argument(
        "--east3-opt-level",
        default="1",
        choices=("0", "1", "2"),
        help="EAST3 optimizer level passed to transpilers (default: 1)",
    )
    parser.add_argument(
        "--cmd-timeout-sec",
        type=int,
        default=120,
        help="timeout seconds applied to python/transpile/run commands per case (default: 120)",
    )
    args = parser.parse_args()

    enabled_targets: set[str] = set()
    for raw in args.targets.split(","):
        name = raw.strip()
        if name != "":
            enabled_targets.add(name)
    if len(enabled_targets) == 0:
        print("[ERROR] --targets must include at least one target")
        return 1

    stems, err = resolve_case_stems(args.cases, args.case_root, args.all_samples)
    if err != "":
        print(f"[ERROR] {err}")
        return 2
    if len(stems) == 0:
        print("[ERROR] no cases resolved")
        return 2

    exit_code = 0
    pass_cases = 0
    fail_cases = 0
    records: list[CheckRecord] = []
    for stem in stems:
        code = check_case(
            stem,
            enabled_targets,
            case_root=args.case_root,
            ignore_stdout=args.ignore_unstable_stdout,
            east3_opt_level=args.east3_opt_level,
            cmd_timeout_sec=args.cmd_timeout_sec,
            records=records,
        )
        if code != 0:
            exit_code = code
            fail_cases += 1
        else:
            pass_cases += 1

    category_counts: dict[str, int] = {}
    for rec in records:
        category_counts[rec.category] = category_counts.get(rec.category, 0) + 1

    print(
        "SUMMARY "
        + f"cases={len(stems)} pass={pass_cases} fail={fail_cases} "
        + f"targets={','.join(sorted(enabled_targets))} "
        + f"east3_opt_level={args.east3_opt_level}"
    )
    if len(category_counts) > 0:
        print("SUMMARY_CATEGORIES")
        for category in sorted(category_counts.keys()):
            print(f"- {category}: {category_counts[category]}")

    if args.summary_json != "":
        summary_obj = {
            "case_root": args.case_root,
            "east3_opt_level": args.east3_opt_level,
            "targets": sorted(enabled_targets),
            "cases": stems,
            "case_total": len(stems),
            "case_pass": pass_cases,
            "case_fail": fail_cases,
            "category_counts": category_counts,
            "records": [
                {
                    "case": rec.case_stem,
                    "target": rec.target,
                    "category": rec.category,
                    "detail": rec.detail,
                }
                for rec in records
            ],
        }
        out_path = Path(args.summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

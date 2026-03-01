#!/usr/bin/env python3
"""Runtime parity check across transpiler targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
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
) -> subprocess.CompletedProcess[str]:
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


def runtime_cpp_sources_shell() -> str:
    """runtime/cpp の C++ 実装ファイルをシェル引数文字列で返す。"""
    paths: list[str] = []
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "base").glob("*.cpp")):
        paths.append(shlex.quote(p.relative_to(ROOT).as_posix()))
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "pytra").rglob("*.cpp")):
        paths.append(shlex.quote(p.relative_to(ROOT).as_posix()))
    return " ".join(paths)


def build_targets(
    case_stem: str,
    case_path: Path,
    east3_opt_level: str,
) -> list[Target]:
    case_src = case_path.as_posix()
    runtime_srcs = runtime_cpp_sources_shell()
    opt_arg = "--east3-opt-level " + shlex.quote(str(east3_opt_level))
    return [
        Target(
            name="cpp",
            transpile_cmd=f"python src/py2cpp.py {shlex.quote(case_src)} test/transpile/cpp/{case_stem}.cpp {opt_arg}",
            run_cmd=(
                f"g++ -std=c++20 -O2 -I src test/transpile/cpp/{case_stem}.cpp "
                "-I src/runtime/cpp "
                f"{runtime_srcs} "
                f"-o test/transpile/obj/{case_stem}_cpp.out && test/transpile/obj/{case_stem}_cpp.out"
            ),
            needs=("python", "g++"),
        ),
        Target(
            name="rs",
            transpile_cmd=f"python src/py2rs.py {shlex.quote(case_src)} -o test/transpile/rs/{case_stem}.rs {opt_arg}",
            run_cmd=f"rustc -O test/transpile/rs/{case_stem}.rs -o test/transpile/obj/{case_stem}_rs.out && test/transpile/obj/{case_stem}_rs.out",
            needs=("python", "rustc"),
        ),
        Target(
            name="cs",
            transpile_cmd=f"python src/py2cs.py {shlex.quote(case_src)} -o test/transpile/cs/{case_stem}.cs {opt_arg}",
            run_cmd=(
                f"mcs -warn:0 -out:test/transpile/obj/{case_stem}_cs.exe test/transpile/cs/{case_stem}.cs "
                "src/runtime/cs/pytra/built_in/py_runtime.cs "
                "src/runtime/cs/pytra/built_in/time.cs "
                "src/runtime/cs/pytra/built_in/math.cs "
                "src/runtime/cs/pytra/utils/png_helper.cs "
                "src/runtime/cs/pytra/utils/gif_helper.cs "
                "src/runtime/cs/pytra/std/pathlib.cs "
                f"&& mono test/transpile/obj/{case_stem}_cs.exe"
            ),
            needs=("python", "mcs", "mono"),
        ),
        Target(
            name="js",
            transpile_cmd=f"python src/py2js.py {shlex.quote(case_src)} -o test/transpile/js/{case_stem}.js {opt_arg}",
            run_cmd=f"node test/transpile/js/{case_stem}.js",
            needs=("python", "node"),
        ),
        Target(
            name="ruby",
            transpile_cmd=f"python src/py2rb.py {shlex.quote(case_src)} -o test/transpile/ruby/{case_stem}.rb {opt_arg}",
            run_cmd=f"ruby test/transpile/ruby/{case_stem}.rb",
            needs=("python", "ruby"),
        ),
        Target(
            name="lua",
            transpile_cmd=f"python src/py2lua.py {shlex.quote(case_src)} -o test/transpile/lua/{case_stem}.lua {opt_arg}",
            run_cmd=f"lua test/transpile/lua/{case_stem}.lua",
            needs=("python", "lua"),
        ),
        Target(
            name="ts",
            transpile_cmd=f"python src/py2ts.py {shlex.quote(case_src)} -o test/transpile/ts/{case_stem}.ts {opt_arg}",
            run_cmd=f"npx -y tsx test/transpile/ts/{case_stem}.ts",
            needs=("python", "node", "npx"),
        ),
        Target(
            name="go",
            transpile_cmd=f"python src/py2go.py {shlex.quote(case_src)} -o test/transpile/go/{case_stem}.go {opt_arg}",
            run_cmd=f"go run test/transpile/go/{case_stem}.go test/transpile/go/py_runtime.go",
            needs=("python", "go"),
        ),
        Target(
            name="java",
            transpile_cmd=f"python src/py2java.py {shlex.quote(case_src)} -o test/transpile/java/Main.java {opt_arg}",
            run_cmd="javac test/transpile/java/Main.java test/transpile/java/PyRuntime.java && java -cp test/transpile/java Main",
            needs=("python", "javac", "java"),
        ),
        Target(
            name="swift",
            transpile_cmd=(
                f"python src/py2swift.py {shlex.quote(case_src)} --output "
                f"test/transpile/swift/{case_stem}.swift {opt_arg}"
            ),
            run_cmd=(
                f"swiftc test/transpile/swift/{case_stem}.swift test/transpile/swift/py_runtime.swift "
                f"-o test/transpile/obj/{case_stem}_swift.out && test/transpile/obj/{case_stem}_swift.out"
            ),
            needs=("python", "swiftc"),
        ),
        Target(
            name="kotlin",
            transpile_cmd=(
                f"python src/py2kotlin.py {shlex.quote(case_src)} "
                f"-o test/transpile/kotlin/{case_stem}.kt {opt_arg}"
            ),
            run_cmd=(
                f"kotlinc test/transpile/kotlin/{case_stem}.kt test/transpile/kotlin/py_runtime.kt "
                f"-include-runtime -d test/transpile/obj/{case_stem}_kotlin.jar "
                f"&& java -jar test/transpile/obj/{case_stem}_kotlin.jar"
            ),
            needs=("python", "kotlinc", "java"),
            # Kotlin backend still lowers image writers to no-op, so artifact parity is not meaningful yet.
            ignore_artifacts=True,
        ),
        Target(
            name="scala",
            transpile_cmd=(
                f"python src/py2scala.py {shlex.quote(case_src)} "
                f"-o test/transpile/scala/{case_stem}.scala {opt_arg}"
            ),
            run_cmd=f"scala run test/transpile/scala/{case_stem}.scala",
            needs=("python", "scala"),
        ),
    ]


def check_case(
    case_stem: str,
    enabled_targets: set[str],
    *,
    case_root: str,
    ignore_stdout: bool,
    east3_opt_level: str,
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

        run_expr = f"python {shlex.quote(case_path.as_posix())}"
        run_env = {"PYTHONPATH": "src"}
        py = run_shell(run_expr, cwd=work, env=run_env)

        if py.returncode != 0:
            print(f"[ERROR] python:{case_stem} failed")
            print(py.stderr.strip())
            _record("python", "python_failed", py.stderr.strip())
            return 1
        expected = _normalize_output_for_compare(py.stdout)
        expected_artifact_size: int | None = None
        expected_artifact_path: Path | None = None
        expected_out_txt = _parse_output_path(py.stdout)
        if expected_out_txt != "":
            expected_artifact_path = _resolve_output_path(work, expected_out_txt)
            if not expected_artifact_path.exists() or not expected_artifact_path.is_file():
                _record("python", "python_artifact_missing", str(expected_artifact_path))
                print(f"[ERROR] python:{case_stem} artifact missing: {expected_artifact_path}")
                return 1
            expected_artifact_size = int(expected_artifact_path.stat().st_size)

        mismatches: list[str] = []
        for target in build_targets(case_stem, case_path, east3_opt_level):
            if target.name not in enabled_targets:
                continue
            if not can_run(target):
                print(f"[SKIP] {case_stem}:{target.name} (missing toolchain)")
                _record(target.name, "toolchain_missing", "missing toolchain")
                continue

            tr = run_shell(target.transpile_cmd, cwd=work)
            if tr.returncode != 0:
                msg = tr.stderr.strip()
                mismatches.append(f"{case_stem}:{target.name}: transpile failed: {msg}")
                _record(target.name, "transpile_failed", msg)
                continue

            # Ensure target artifact validation is not masked by stale python output.
            if expected_artifact_path is not None and expected_artifact_path.exists() and expected_artifact_path.is_file():
                expected_artifact_path.unlink()

            rr = run_shell(target.run_cmd, cwd=work)
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

            print(f"[OK] {case_stem}:{target.name}")
            _record(target.name, "ok", "")

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

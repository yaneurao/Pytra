#!/usr/bin/env python3
"""math/pathlib parity check across transpiler targets."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "test" / "fixtures"


@dataclass
class Target:
    name: str
    transpile_cmd: str
    run_cmd: str
    needs: tuple[str, ...]


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_shell(cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True)


def can_run(target: Target) -> bool:
    for tool in target.needs:
        if shutil.which(tool) is None:
            return False
    return True


def find_case_path(case_stem: str) -> Path | None:
    matches = sorted(FIXTURE_ROOT.rglob(f"{case_stem}.py"))
    if not matches:
        return None
    return matches[0]


def build_targets(case_stem: str, case_path: Path) -> list[Target]:
    case_src = case_path.as_posix()
    return [
        Target(
            name="cpp",
            transpile_cmd=f"python src/py2cpp.py {shlex.quote(case_src)} test/transpile/cpp/{case_stem}.cpp",
            run_cmd=(
                f"g++ -std=c++20 -O2 -I src test/transpile/cpp/{case_stem}.cpp "
                "src/runtime/cpp/pylib/png.cpp src/runtime/cpp/pylib/gif.cpp src/runtime/cpp/core/math.cpp "
                "src/runtime/cpp/core/time.cpp src/runtime/cpp/core/pathlib.cpp src/runtime/cpp/core/dataclasses.cpp "
                "src/runtime/cpp/base/io.cpp src/runtime/cpp/base/bytes_util.cpp "
                "src/runtime/cpp/base/gc.cpp "
                f"-o test/transpile/obj/{case_stem}_cpp.out && test/transpile/obj/{case_stem}_cpp.out"
            ),
            needs=("python", "g++"),
        ),
        Target(
            name="rs",
            transpile_cmd=f"python src/py2rs.py {shlex.quote(case_src)} test/transpile/rs/{case_stem}.rs",
            run_cmd=f"rustc -O test/transpile/rs/{case_stem}.rs -o test/transpile/obj/{case_stem}_rs.out && test/transpile/obj/{case_stem}_rs.out",
            needs=("python", "rustc"),
        ),
        Target(
            name="cs",
            transpile_cmd=f"python src/py2cs.py {shlex.quote(case_src)} test/transpile/cs/{case_stem}.cs",
            run_cmd=(
                f"mcs -out:test/transpile/obj/{case_stem}_cs.exe test/transpile/cs/{case_stem}.cs "
                "src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs src/cs_module/pathlib.cs "
                f"&& mono test/transpile/obj/{case_stem}_cs.exe"
            ),
            needs=("python", "mcs", "mono"),
        ),
        Target(
            name="js",
            transpile_cmd=f"python src/py2js.py {shlex.quote(case_src)} test/transpile/js/{case_stem}.js",
            run_cmd=f"node test/transpile/js/{case_stem}.js",
            needs=("python", "node"),
        ),
        Target(
            name="ts",
            transpile_cmd=f"python src/py2ts.py {shlex.quote(case_src)} test/transpile/ts/{case_stem}.ts",
            run_cmd=f"npx -y tsx test/transpile/ts/{case_stem}.ts",
            needs=("python", "node", "npx"),
        ),
        Target(
            name="go",
            transpile_cmd=f"python src/py2go.py {shlex.quote(case_src)} test/transpile/go/{case_stem}.go",
            run_cmd=f"go run test/transpile/go/{case_stem}.go",
            needs=("python", "go"),
        ),
        Target(
            name="java",
            transpile_cmd=f"python src/py2java.py {shlex.quote(case_src)} test/transpile/java/{case_stem}.java",
            run_cmd=f"javac test/transpile/java/{case_stem}.java && java -cp test/transpile/java {case_stem}",
            needs=("python", "javac", "java"),
        ),
        Target(
            name="swift",
            transpile_cmd=f"python src/py2swift.py {shlex.quote(case_src)} test/transpile/swift/{case_stem}.swift",
            run_cmd=f"swiftc test/transpile/swift/{case_stem}.swift -o test/transpile/obj/{case_stem}_swift.out && test/transpile/obj/{case_stem}_swift.out",
            needs=("python", "swiftc", "node"),
        ),
        Target(
            name="kotlin",
            transpile_cmd=f"python src/py2kotlin.py {shlex.quote(case_src)} test/transpile/kotlin/{case_stem}.kt",
            run_cmd=(
                f"kotlinc test/transpile/kotlin/{case_stem}.kt -include-runtime -d test/transpile/obj/{case_stem}_kotlin.jar "
                f"&& java -jar test/transpile/obj/{case_stem}_kotlin.jar"
            ),
            needs=("python", "kotlinc", "java", "node"),
        ),
    ]


def check_case(case_stem: str) -> int:
    case_path = find_case_path(case_stem)
    if case_path is None:
        print(f"[ERROR] missing case: {case_stem}")
        return 1
    py = run_shell(f"python {shlex.quote(case_path.as_posix())}")
    if py.returncode != 0:
        print(f"[ERROR] python:{case_stem} failed")
        print(py.stderr.strip())
        return 1
    expected = normalize(py.stdout)

    mismatches: list[str] = []
    for target in build_targets(case_stem, case_path):
        if not can_run(target):
            print(f"[SKIP] {case_stem}:{target.name} (missing toolchain)")
            continue

        tr = run_shell(target.transpile_cmd)
        if tr.returncode != 0:
            mismatches.append(f"{case_stem}:{target.name}: transpile failed: {tr.stderr.strip()}")
            continue

        rr = run_shell(target.run_cmd)
        if rr.returncode != 0:
            mismatches.append(f"{case_stem}:{target.name}: run failed: {rr.stderr.strip()}")
            continue

        actual = normalize(rr.stdout)
        if actual != expected:
            mismatches.append(
                f"{case_stem}:{target.name}: output mismatch\n"
                f"  expected: {expected!r}\n"
                f"  actual  : {actual!r}"
            )
        else:
            print(f"[OK] {case_stem}:{target.name}")

    if mismatches:
        print("\n[FAIL] mismatches")
        for m in mismatches:
            print(f"- {m}")
        return 1

    print(f"[PASS] {case_stem}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run runtime parity checks for math/pathlib cases")
    parser.add_argument(
        "cases",
        nargs="*",
        default=["math_extended", "pathlib_extended"],
        help="case stems under test/fixtures/** (without .py)",
    )
    args = parser.parse_args()

    exit_code = 0
    for stem in args.cases:
        code = check_case(stem)
        if code != 0:
            exit_code = code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

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


def build_targets(case_stem: str) -> list[Target]:
    return [
        Target(
            name="cpp",
            transpile_cmd=f"python src/py2cpp.py test/fixtures/py/{case_stem}.py test/transpile/cpp/{case_stem}.cpp",
            run_cmd=(
                f"g++ -std=c++20 -O2 -I src test/transpile/cpp/{case_stem}.cpp "
                "src/cpp_module/png.cpp src/cpp_module/gif.cpp src/cpp_module/math.cpp "
                "src/cpp_module/time.cpp src/cpp_module/pathlib.cpp src/cpp_module/dataclasses.cpp "
                "src/cpp_module/gc.cpp "
                f"-o test/transpile/obj/{case_stem}_cpp.out && test/transpile/obj/{case_stem}_cpp.out"
            ),
            needs=("python", "g++"),
        ),
        Target(
            name="rs",
            transpile_cmd=f"python src/py2rs.py test/fixtures/py/{case_stem}.py test/transpile/rs/{case_stem}.rs",
            run_cmd=f"rustc -O test/transpile/rs/{case_stem}.rs -o test/transpile/obj/{case_stem}_rs.out && test/transpile/obj/{case_stem}_rs.out",
            needs=("python", "rustc"),
        ),
        Target(
            name="cs",
            transpile_cmd=f"python src/py2cs.py test/fixtures/py/{case_stem}.py test/transpile/cs/{case_stem}.cs",
            run_cmd=(
                f"mcs -out:test/transpile/obj/{case_stem}_cs.exe test/transpile/cs/{case_stem}.cs "
                "src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs src/cs_module/pathlib.cs "
                f"&& mono test/transpile/obj/{case_stem}_cs.exe"
            ),
            needs=("python", "mcs", "mono"),
        ),
        Target(
            name="js",
            transpile_cmd=f"python src/py2js.py test/fixtures/py/{case_stem}.py test/transpile/js/{case_stem}.js",
            run_cmd=f"node test/transpile/js/{case_stem}.js",
            needs=("python", "node"),
        ),
        Target(
            name="ts",
            transpile_cmd=f"python src/py2ts.py test/fixtures/py/{case_stem}.py test/transpile/ts/{case_stem}.ts",
            run_cmd=f"npx -y tsx test/transpile/ts/{case_stem}.ts",
            needs=("python", "node", "npx"),
        ),
        Target(
            name="go",
            transpile_cmd=f"python src/py2go.py test/fixtures/py/{case_stem}.py test/transpile/go/{case_stem}.go",
            run_cmd=f"go run test/transpile/go/{case_stem}.go",
            needs=("python", "go"),
        ),
        Target(
            name="java",
            transpile_cmd=f"python src/py2java.py test/fixtures/py/{case_stem}.py test/transpile/java/{case_stem}.java",
            run_cmd=f"javac test/transpile/java/{case_stem}.java && java -cp test/transpile/java {case_stem}",
            needs=("python", "javac", "java"),
        ),
        Target(
            name="swift",
            transpile_cmd=f"python src/py2swift.py test/fixtures/py/{case_stem}.py test/transpile/swift/{case_stem}.swift",
            run_cmd=f"swiftc test/transpile/swift/{case_stem}.swift -o test/transpile/obj/{case_stem}_swift.out && test/transpile/obj/{case_stem}_swift.out",
            needs=("python", "swiftc", "node"),
        ),
        Target(
            name="kotlin",
            transpile_cmd=f"python src/py2kotlin.py test/fixtures/py/{case_stem}.py test/transpile/kotlin/{case_stem}.kt",
            run_cmd=(
                f"kotlinc test/transpile/kotlin/{case_stem}.kt -include-runtime -d test/transpile/obj/{case_stem}_kotlin.jar "
                f"&& java -jar test/transpile/obj/{case_stem}_kotlin.jar"
            ),
            needs=("python", "kotlinc", "java", "node"),
        ),
    ]


def check_case(case_stem: str) -> int:
    py = run_shell(f"python test/fixtures/py/{case_stem}.py")
    if py.returncode != 0:
        print(f"[ERROR] python:{case_stem} failed")
        print(py.stderr.strip())
        return 1
    expected = normalize(py.stdout)

    mismatches: list[str] = []
    for target in build_targets(case_stem):
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
        default=["case31_math_extended", "case32_pathlib_extended"],
        help="case stems under test/fixtures/py (without .py)",
    )
    args = parser.parse_args()

    exit_code = 0
    for stem in args.cases:
        if not (ROOT / "test" / "fixtures" / "py" / f"{stem}.py").exists():
            print(f"[ERROR] missing case: {stem}")
            exit_code = 1
            continue
        code = check_case(stem)
        if code != 0:
            exit_code = code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare py2cpp outputs between Python and selfhost executable."""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CPP = ROOT / "src" / "py2cpp.py"
DEFAULT_EXPECTED_DIFF_FILE = ROOT / "tools" / "selfhost_cpp_diff_expected.txt"
DEFAULT_CASES = [
    "test/fixtures/core/add.py",
    "test/fixtures/core/str_join_method.py",
    "test/fixtures/control/if_else.py",
    "test/fixtures/collections/comprehension_filter.py",
    "test/fixtures/typing/enum_basic.py",
    "test/fixtures/stdlib/enum_extended.py",
    "sample/py/01_mandelbrot.py",
    "sample/py/17_monte_carlo_pi.py",
]

_DECL_NONE_INIT_RE = re.compile(
    r"^(\s*)([A-Za-z_][A-Za-z0-9_:<>]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"[A-Za-z_][A-Za-z0-9_:<>]*\s*\(\s*py_to_[A-Za-z0-9_]+\(/\* none \*/\)\s*\);\s*$"
)
_FLOAT_CAST_PERF_COUNTER_RE = re.compile(
    r"py_to_float64\((pytra::std::time::perf_counter\(\)(?:\s*-\s*[A-Za-z_][A-Za-z0-9_]*)?)\)"
)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def _load_expected_diff_cases(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "" or line.startswith("#"):
            continue
        out.add(line)
    return out


def _canonicalize_cpp_line(line: str) -> str:
    """Normalize known semantically-equivalent cpp diff patterns."""
    m = _DECL_NONE_INIT_RE.match(line)
    if m is not None:
        indent = m.group(1)
        typ = m.group(2)
        name = m.group(3)
        return f"{indent}{typ} {name};"
    return _FLOAT_CAST_PERF_COUNTER_RE.sub(r"\1", line)


def _canonicalize_cpp_lines(lines: list[str]) -> list[str]:
    return [_canonicalize_cpp_line(line) for line in lines]


def _run_east3_contract_tests() -> tuple[bool, str]:
    checks = [
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "test/unit",
            "-p",
            "test_east2_to_east3_lowering.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "test/unit",
            "-p",
            "test_east3_cpp_bridge.py",
        ],
    ]
    for cmd in checks:
        cp = _run(cmd)
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip()
            first = msg.splitlines()[0] if msg else "unknown error"
            return False, first
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="compare py2cpp outputs: python vs selfhost")
    ap.add_argument("--selfhost-bin", default="selfhost/py2cpp.out")
    ap.add_argument(
        "--selfhost-driver",
        choices=["direct", "bridge"],
        default="direct",
        help="direct: call selfhost bin directly, bridge: use tools/selfhost_transpile.py",
    )
    ap.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    ap.add_argument("--show-diff", action="store_true")
    ap.add_argument(
        "--expected-diff-file",
        default=str(DEFAULT_EXPECTED_DIFF_FILE),
        help="newline-separated known mismatch cases; comments(#) and blank lines are ignored",
    )
    ap.add_argument(
        "--mode",
        choices=["strict", "allow-not-implemented"],
        default="allow-not-implemented",
        help="strict: any selfhost failure is mismatch, allow-not-implemented: [not_implemented] is skipped",
    )
    ap.add_argument(
        "--skip-east3-contract-tests",
        action="store_true",
        help="skip EAST3 schema/lowering preflight tests",
    )
    args = ap.parse_args()

    if not args.skip_east3_contract_tests:
        ok_contract, msg_contract = _run_east3_contract_tests()
        if not ok_contract:
            print(f"[FAIL east3-contract] {msg_contract}")
            return 1

    selfhost_bin = ROOT / args.selfhost_bin
    if not selfhost_bin.exists():
        print(f"missing selfhost binary: {selfhost_bin}")
        return 2
    bridge_tool = ROOT / "tools" / "selfhost_transpile.py"
    if args.selfhost_driver == "bridge" and not bridge_tool.exists():
        print(f"missing bridge tool: {bridge_tool}")
        return 2

    expected_diff_cases = _load_expected_diff_cases(Path(args.expected_diff_file))
    mismatches = 0
    known_diffs = 0
    skipped = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        for rel in args.cases:
            src = ROOT / rel
            if not src.exists():
                print(f"missing case: {rel}")
                mismatches += 1
                continue
            out_py = td / (src.stem + ".py.cpp")
            out_sh = td / (src.stem + ".sh.cpp")

            cp1 = _run(["python3", str(PY2CPP), str(src), "-o", str(out_py)])
            if cp1.returncode != 0:
                print(f"[FAIL python] {rel}: {(cp1.stderr.strip() or cp1.stdout.strip()).splitlines()[:1]}")
                mismatches += 1
                continue
            if args.selfhost_driver == "bridge":
                cp2 = _run(
                    [
                        "python3",
                        str(bridge_tool),
                        str(src),
                        "-o",
                        str(out_sh),
                        "--selfhost-bin",
                        str(selfhost_bin),
                    ]
                )
            else:
                cp2 = _run([str(selfhost_bin), str(src), "-o", str(out_sh)])
            if cp2.returncode != 0:
                msg = (cp2.stderr.strip() or cp2.stdout.strip())
                if args.mode == "allow-not-implemented" and "[not_implemented]" in msg:
                    skipped += 1
                    print(f"[SKIP selfhost-not-implemented] {rel}")
                    continue
                if args.mode == "allow-not-implemented" and args.selfhost_driver == "bridge" and "[input_invalid]" in msg:
                    skipped += 1
                    print(f"[SKIP selfhost-bridge-json-unavailable] {rel}")
                    continue
                if rel in expected_diff_cases:
                    known_diffs += 1
                    print(f"[KNOWN DIFF selfhost] {rel}: {msg.splitlines()[:1]}")
                else:
                    print(f"[FAIL selfhost] {rel}: {msg.splitlines()[:1]}")
                    mismatches += 1
                continue
            if not out_sh.exists():
                if rel in expected_diff_cases:
                    known_diffs += 1
                    print(f"[KNOWN DIFF selfhost] {rel}: output file was not generated ({out_sh})")
                else:
                    print(f"[FAIL selfhost] {rel}: output file was not generated ({out_sh})")
                    mismatches += 1
                continue

            a = out_py.read_text(encoding="utf-8").splitlines()
            b = out_sh.read_text(encoding="utf-8").splitlines()
            a_norm = _canonicalize_cpp_lines(a)
            b_norm = _canonicalize_cpp_lines(b)
            if a_norm != b_norm:
                if rel in expected_diff_cases:
                    known_diffs += 1
                    print(f"[KNOWN DIFF] {rel}")
                else:
                    mismatches += 1
                    print(f"[DIFF] {rel}")
                    if args.show_diff:
                        for ln in difflib.unified_diff(
                            a_norm,
                            b_norm,
                            fromfile=f"{rel}:python(normalized)",
                            tofile=f"{rel}:selfhost(normalized)",
                            lineterm="",
                        ):
                            print(ln)
            else:
                print(f"[OK] {rel}")

    print(f"mismatches={mismatches} known_diffs={known_diffs} skipped={skipped}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())

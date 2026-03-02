#!/usr/bin/env python3
"""Check py2php transpile success for smoke fixtures/sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2PHP = ROOT / "src" / "py2php.py"

CASES = [
    "test/fixtures/core/add.py",
    "test/fixtures/control/if_else.py",
    "test/fixtures/control/for_range.py",
    "test/fixtures/control/range_downcount_len_minus1.py",
    "test/fixtures/oop/inheritance.py",
    "test/fixtures/oop/inheritance_virtual_dispatch_multilang.py",
    "test/fixtures/oop/is_instance.py",
    "sample/py/01_mandelbrot.py",
    "sample/py/18_mini_language_interpreter.py",
]

STAGE2_REMOVED_FRAGMENT = "--east-stage 2 is no longer supported; use EAST3 (default)."


def _assert_sample18_quality(out: Path) -> tuple[bool, str]:
    text = out.read_text(encoding="utf-8")
    required_fragments = [
        '$single_char_token_tags = ["+" => 1',
        "array_key_exists($node->name, $env)",
        "public function __construct($kind, $text, $pos, $number_value)",
        "public function __construct($kind, $value, $name, $op, $left, $right, $kind_tag, $op_tag)",
        "public function __construct($kind, $name, $expr_index, $kind_tag)",
        "function __pytra_entry_main(): void {",
        "__pytra_entry_main();",
    ]
    i = 0
    while i < len(required_fragments):
        frag = required_fragments[i]
        if frag not in text:
            return False, "sample18 missing fragment: " + frag
        i += 1
    return True, ""


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2PHP), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        runtime_files = [
            out.parent / "pytra" / "py_runtime.php",
            out.parent / "pytra" / "runtime" / "png.php",
            out.parent / "pytra" / "runtime" / "gif.php",
            out.parent / "pytra" / "std" / "time.php",
        ]
        i = 0
        while i < len(runtime_files):
            if not runtime_files[i].exists():
                return False, "missing runtime file: " + str(runtime_files[i].relative_to(out.parent))
            i += 1
        if src.name == "18_mini_language_interpreter.py":
            ok, msg = _assert_sample18_quality(out)
            if not ok:
                return False, msg
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _run_one_stage2_must_fail(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2PHP), str(src), "--east-stage", "2", "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return False, "unexpected success for --east-stage 2"
    stderr = cp.stderr.strip()
    if STAGE2_REMOVED_FRAGMENT in stderr:
        return True, ""
    first = stderr.splitlines()[0] if stderr else "missing stderr message"
    return False, "unexpected stage2 error message: " + first


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2php transpile success for smoke cases")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.php"
        i = 0
        while i < len(CASES):
            rel = CASES[i]
            src = ROOT / rel
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))
            i += 1

        total += 1
        stage2_probe = ROOT / CASES[0]
        good, msg = _run_one_stage2_must_fail(stage2_probe, out)
        if good:
            ok += 1
            if args.verbose:
                print("OK", CASES[0], "[stage2 rejected]")
        else:
            fails.append((CASES[0] + " [stage2 rejected]", msg))

    print(f"checked={total} ok={ok} fail={len(fails)}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

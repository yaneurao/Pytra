#!/usr/bin/env python3
"""Check py2js transpile success for fixtures and sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2JS = ROOT / "src" / "py2js.py"

DEFAULT_EXPECTED_FAILS = {
    "test/fixtures/signature/ng_kwargs.py",
    "test/fixtures/signature/ng_object_receiver.py",
    "test/fixtures/signature/ng_posonly.py",
    "test/fixtures/signature/ng_varargs.py",
    "test/fixtures/signature/ng_untyped_param.py",
    "test/fixtures/typing/any_class_alias.py",
}


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2JS), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    compat_warning = "warning: --east-stage 2 is compatibility mode; default is 3."
    if cp.returncode == 0 and compat_warning in cp.stderr:
        return False, "unexpected stage2 compatibility warning in default run"
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


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
            "test_east3_lowering.py",
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
        cp = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip()
            first = msg.splitlines()[0] if msg else "unknown error"
            return False, first
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2js transpile success for fixtures/sample")
    ap.add_argument("--include-expected-failures", action="store_true", help="do not skip known negative fixtures")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    ap.add_argument(
        "--skip-east3-contract-tests",
        action="store_true",
        help="skip EAST3 schema/lowering preflight tests",
    )
    args = ap.parse_args()

    if not args.skip_east3_contract_tests:
        ok_contract, msg_contract = _run_east3_contract_tests()
        if not ok_contract:
            print(f"FAIL east3-contract: {msg_contract}")
            return 1

    fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
    expected_fails = set() if args.include_expected_failures else DEFAULT_EXPECTED_FAILS

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    skipped = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.js"
        for src in fixture_files + sample_files:
            rel = str(src.relative_to(ROOT))
            if rel in expected_fails:
                skipped += 1
                continue
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))

    print(f"checked={total} ok={ok} fail={len(fails)} skipped={skipped}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

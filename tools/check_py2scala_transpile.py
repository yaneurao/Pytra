#!/usr/bin/env python3
"""Check py2scala transpile success for fixtures and sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2SCALA = ROOT / "src" / "py2scala.py"

DEFAULT_EXPECTED_FAILS = {
    "test/fixtures/signature/ng_kwargs.py",
    "test/fixtures/signature/ng_object_receiver.py",
    "test/fixtures/signature/ng_posonly.py",
    "test/fixtures/signature/ng_varargs.py",
    "test/fixtures/signature/ng_untyped_param.py",
    "test/fixtures/typing/any_class_alias.py",
}

SAMPLE01_REL = "sample/py/01_mandelbrot.py"


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2SCALA), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    compat_warning = "warning: --east-stage 2 is compatibility mode; default is 3."
    if cp.returncode == 0 and compat_warning in cp.stderr:
        return False, "unexpected stage2 compatibility warning in default run"
    if cp.returncode == 0:
        runtime_path = out.parent / "py_runtime.scala"
        if not runtime_path.exists():
            return False, "missing runtime file: py_runtime.scala"
        src_text = out.read_text(encoding="utf-8")
        if "def __pytra_truthy(" in src_text or "def __pytra_int(" in src_text:
            return False, "inline scala runtime helper detected in generated source"
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _sample01_quality_error(rel: str, out: Path) -> str:
    if rel != SAMPLE01_REL:
        return ""
    text = out.read_text(encoding="utf-8")
    if "boundary:" in text or "__breakLabel_" in text or "__continueLabel_" in text:
        return "sample/01 quality regression: boundary labels reintroduced"
    if "__pytra_int(0L)" in text:
        return "sample/01 quality regression: identity int cast reintroduced"
    if "__pytra_int(height)" in text or "__pytra_int(width)" in text or "__pytra_int(max_iter)" in text:
        return "sample/01 quality regression: typed range bound cast reintroduced"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2scala transpile success for fixtures/sample")
    ap.add_argument("--include-expected-failures", action="store_true", help="do not skip known negative fixtures")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
    expected_fails = set() if args.include_expected_failures else DEFAULT_EXPECTED_FAILS

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    skipped = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.scala"
        for src in fixture_files + sample_files:
            rel = str(src.relative_to(ROOT))
            if rel in expected_fails:
                skipped += 1
                continue
            total += 1
            good, msg = _run_one(src, out)
            if good:
                quality_err = _sample01_quality_error(rel, out)
                if quality_err != "":
                    fails.append((rel, quality_err))
                    continue
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

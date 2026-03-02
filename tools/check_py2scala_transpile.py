#!/usr/bin/env python3
"""Check py2scala transpile success for fixtures and sample files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2SCALA = ROOT / "src" / "py2scala.py"


@dataclass(frozen=True)
class ExpectedFailureSpec:
    category: str
    contains: str


@dataclass(frozen=True)
class RunResult:
    ok: bool
    message: str
    raw: str
    category: str


USER_ERROR_RE = re.compile(r"__PYTRA_USER_ERROR__\|([^|]+)\|([^\r\n]+)")

DEFAULT_EXPECTED_FAILURES: dict[str, ExpectedFailureSpec] = {
    "test/fixtures/signature/ng_kwargs.py": ExpectedFailureSpec(
        category="user_syntax_error",
        contains="variadic kwargs parameter",
    ),
    "test/fixtures/signature/ng_object_receiver.py": ExpectedFailureSpec(
        category="unsupported_by_design",
        contains="object receiver attribute/method access is forbidden",
    ),
    "test/fixtures/signature/ng_posonly.py": ExpectedFailureSpec(
        category="user_syntax_error",
        contains="positional-only marker '/'",
    ),
    "test/fixtures/signature/ng_varargs.py": ExpectedFailureSpec(
        category="user_syntax_error",
        contains="variadic args parameter",
    ),
    "test/fixtures/typing/any_class_alias.py": ExpectedFailureSpec(
        category="unsupported_by_design",
        contains="object receiver attribute/method access is forbidden",
    ),
}

SAMPLE01_REL = "sample/py/01_mandelbrot.py"


def _extract_user_error_category(text: str) -> str:
    m = USER_ERROR_RE.search(text)
    if m is None:
        return ""
    return m.group(1).strip()


def _extract_failure_headline(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
    if len(lines) == 0:
        return "unknown error"
    for line in lines:
        m = USER_ERROR_RE.search(line)
        if m is not None:
            return f"{m.group(1)}: {m.group(2)}"
    for line in lines:
        if line.startswith("RuntimeError:"):
            return line
    for line in reversed(lines):
        if line.startswith("Traceback (most recent call last):"):
            continue
        if line.startswith("File "):
            continue
        if line == "^":
            continue
        return line
    return lines[0]


def _run_one(src: Path, out: Path) -> RunResult:
    cp = subprocess.run(
        ["python3", str(PY2SCALA), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    compat_warning = "warning: --east-stage 2 is compatibility mode; default is 3."
    if cp.returncode == 0 and compat_warning in cp.stderr:
        return RunResult(
            ok=False,
            message="unexpected stage2 compatibility warning in default run",
            raw=cp.stderr,
            category="",
        )
    if cp.returncode == 0:
        runtime_path = out.parent / "py_runtime.scala"
        if not runtime_path.exists():
            return RunResult(
                ok=False,
                message="missing runtime file: py_runtime.scala",
                raw="",
                category="",
            )
        src_text = out.read_text(encoding="utf-8")
        if "def __pytra_truthy(" in src_text or "def __pytra_int(" in src_text:
            return RunResult(
                ok=False,
                message="inline scala runtime helper detected in generated source",
                raw="",
                category="",
            )
        return RunResult(ok=True, message="", raw="", category="")
    raw = (cp.stderr or "").strip() or (cp.stdout or "").strip()
    return RunResult(
        ok=False,
        message=_extract_failure_headline(raw),
        raw=raw,
        category=_extract_user_error_category(raw),
    )


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


def _evaluate_expected_failure(rel: str, result: RunResult, spec: ExpectedFailureSpec) -> str:
    if result.ok:
        return f"unexpected pass (expected failure category={spec.category})"
    got = result.category if result.category != "" else "<none>"
    if got != spec.category:
        return f"unexpected error category: expected={spec.category} got={got} message={result.message}"
    if spec.contains != "" and spec.contains not in result.raw:
        return f"unexpected error detail: expected fragment='{spec.contains}' message={result.message}"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2scala transpile success for fixtures/sample")
    ap.add_argument(
        "--include-expected-failures",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()
    if args.include_expected_failures:
        print(
            "warning: --include-expected-failures is deprecated; expected failures are always checked.",
            file=sys.stderr,
        )

    fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    expected_fail_checked = 0
    expected_fail_ok = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.scala"
        for src in fixture_files + sample_files:
            rel = str(src.relative_to(ROOT))
            total += 1
            result = _run_one(src, out)
            expected = DEFAULT_EXPECTED_FAILURES.get(rel)
            if expected is not None:
                expected_fail_checked += 1
                mismatch = _evaluate_expected_failure(rel, result, expected)
                if mismatch != "":
                    fails.append((rel, mismatch))
                    continue
                expected_fail_ok += 1
                ok += 1
                if args.verbose:
                    print(f"OK_EXPECTED_FAIL {rel} [{expected.category}]")
                continue
            if result.ok:
                quality_err = _sample01_quality_error(rel, out)
                if quality_err != "":
                    fails.append((rel, quality_err))
                    continue
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, result.message))

    print(
        "checked="
        + str(total)
        + " ok="
        + str(ok)
        + " fail="
        + str(len(fails))
        + " expected_fail_checked="
        + str(expected_fail_checked)
        + " expected_fail_ok="
        + str(expected_fail_ok)
        + " skipped=0"
    )
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

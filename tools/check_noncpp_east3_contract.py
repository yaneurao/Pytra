#!/usr/bin/env python3
"""Check non-C++ transpiler EAST3 contract and unified regression route."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    ("rs", "src/py2rs.py", "test/unit/test_py2rs_smoke.py", "tools/check_py2rs_transpile.py"),
    ("cs", "src/py2cs.py", "test/unit/test_py2cs_smoke.py", "tools/check_py2cs_transpile.py"),
    ("js", "src/py2js.py", "test/unit/test_py2js_smoke.py", "tools/check_py2js_transpile.py"),
    ("ts", "src/py2ts.py", "test/unit/test_py2ts_smoke.py", "tools/check_py2ts_transpile.py"),
    ("go", "src/py2go.py", "test/unit/test_py2go_smoke.py", "tools/check_py2go_transpile.py"),
    ("java", "src/py2java.py", "test/unit/test_py2java_smoke.py", "tools/check_py2java_transpile.py"),
    ("kotlin", "src/py2kotlin.py", "test/unit/test_py2kotlin_smoke.py", "tools/check_py2kotlin_transpile.py"),
    ("swift", "src/py2swift.py", "test/unit/test_py2swift_smoke.py", "tools/check_py2swift_transpile.py"),
]

SOURCE_REQUIRED_PATTERNS = [
    "--east-stage",
    'choices=["2", "3"]',
    "--object-dispatch-mode",
    "load_east3_document",
    'east_stage = "3"',
    "--east-stage 2 is no longer supported; use EAST3 (default).",
]

SOURCE_FORBIDDEN_PATTERNS = [
    "load_east_document_compat",
    "normalize_east3_to_legacy",
    "warning: --east-stage 2 is compatibility mode; default is 3.",
]

SMOKE_REQUIRED_PATTERNS = [
    "test_load_east_defaults_to_stage3_entry_and_returns_east3_shape",
    "test_cli_rejects_stage2_compat_mode",
    "--east-stage 2 is no longer supported; use EAST3 (default).",
]

SMOKE_FORBIDDEN_PATTERNS = [
    "test_cli_warns_when_stage2_compat_mode_is_selected",
    "warning: --east-stage 2 is compatibility mode; default is 3.",
]


def _missing_patterns(path: Path, patterns: list[str]) -> list[str]:
    if not path.exists():
        return ["<missing file>"]
    text = path.read_text(encoding="utf-8")
    return [pattern for pattern in patterns if pattern not in text]


def _present_patterns(path: Path, patterns: list[str]) -> list[str]:
    if not path.exists():
        return ["<missing file>"]
    text = path.read_text(encoding="utf-8")
    return [pattern for pattern in patterns if pattern in text]


def _run(cmd: list[str]) -> tuple[bool, str]:
    print("+", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def main() -> int:
    ap = argparse.ArgumentParser(description="check non-cpp EAST3 defaults/warnings and transpile route")
    ap.add_argument(
        "--skip-transpile",
        action="store_true",
        help="only check static source/smoke contracts",
    )
    args = ap.parse_args()

    failures: list[str] = []
    for lang, src_rel, smoke_rel, _ in TARGETS:
        src_path = ROOT / src_rel
        smoke_path = ROOT / smoke_rel
        missing_src = _missing_patterns(src_path, SOURCE_REQUIRED_PATTERNS)
        if missing_src:
            failures.append(f"{lang}: {src_rel} missing {missing_src}")
        present_src = _present_patterns(src_path, SOURCE_FORBIDDEN_PATTERNS)
        if present_src:
            failures.append(f"{lang}: {src_rel} contains forbidden {present_src}")
        missing_smoke = _missing_patterns(smoke_path, SMOKE_REQUIRED_PATTERNS)
        if missing_smoke:
            failures.append(f"{lang}: {smoke_rel} missing {missing_smoke}")
        present_smoke = _present_patterns(smoke_path, SMOKE_FORBIDDEN_PATTERNS)
        if present_smoke:
            failures.append(f"{lang}: {smoke_rel} contains forbidden {present_smoke}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"[OK] static contract checks passed for {len(TARGETS)} non-cpp transpilers")

    if args.skip_transpile:
        return 0

    transpile_failures: list[str] = []
    for lang, _, _, check_rel in TARGETS:
        ok, msg = _run(["python3", check_rel])
        if not ok:
            transpile_failures.append(f"{lang}: {msg}")
    if transpile_failures:
        for failure in transpile_failures:
            print(f"FAIL {failure}")
        return 1
    print(f"[OK] transpile checks passed for {len(TARGETS)} non-cpp transpilers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

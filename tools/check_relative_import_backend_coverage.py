#!/usr/bin/env python3
"""Validate the canonical relative-import backend coverage inventory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
)


EXPECTED_BACKENDS = (
    "cpp",
    "rs",
    "cs",
    "go",
    "java",
    "js",
    "kotlin",
    "lua",
    "nim",
    "php",
    "ruby",
    "scala",
    "swift",
    "ts",
)


def validate_relative_import_backend_coverage() -> None:
    seen = {row["backend"] for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1}
    missing = sorted(set(EXPECTED_BACKENDS) - seen)
    extra = sorted(seen - set(EXPECTED_BACKENDS))
    if missing or extra:
        raise SystemExit(
            f"relative import backend coverage mismatch: missing={missing}, extra={extra}"
        )
    locked = [
        row["backend"]
        for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
        if row["contract_state"] == "build_run_locked"
    ]
    if locked != ["cpp"]:
        raise SystemExit(
            "relative import backend coverage must keep cpp as the only "
            f"build_run_locked lane: got {locked}"
        )
    for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1:
        if row["backend"] == "cpp":
            continue
        if row["contract_state"] != "not_locked":
            raise SystemExit(
                "non-cpp relative import backend coverage must remain "
                f"not_locked until verified: got {row['backend']}={row['contract_state']}"
            )


def main() -> None:
    validate_relative_import_backend_coverage()
    print("[OK] relative import backend coverage inventory passed")


if __name__ == "__main__":
    main()

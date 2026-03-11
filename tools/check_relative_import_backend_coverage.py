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
    RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_V1,
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

EXPECTED_NONCPP_ROLLOUT_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_plan": (
        "docs/ja/plans/p1-relative-import-firstwave-smoke.md",
        "docs/en/plans/p1-relative-import-firstwave-smoke.md",
    ),
    "first_wave_backends": ("rs", "cs"),
    "next_verification_lane": "second_wave_rollout_planning",
    "fail_closed_lane": "backend_specific_fail_closed",
}


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
    first_wave_smoke = [
        row["backend"]
        for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
        if row["contract_state"] == "transpile_smoke_locked"
    ]
    if first_wave_smoke != ["rs", "cs"]:
        raise SystemExit(
            "relative import backend coverage must keep rs/cs as the only "
            f"transpile_smoke_locked lanes: got {first_wave_smoke}"
        )
    for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1:
        if row["backend"] == "cpp":
            continue
        if row["backend"] in {"rs", "cs"}:
            continue
        if row["contract_state"] != "not_locked":
            raise SystemExit(
                "non-cpp relative import backend coverage must remain "
                f"not_locked until verified: got {row['backend']}={row['contract_state']}"
            )


def validate_relative_import_noncpp_rollout() -> None:
    seen = {row["backend"] for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1}
    missing = sorted(set(EXPECTED_BACKENDS) - seen)
    extra = sorted(seen - set(EXPECTED_BACKENDS))
    if missing or extra:
        raise SystemExit(
            "relative import non-cpp rollout mismatch: "
            f"missing={missing}, extra={extra}"
        )
    first_wave = [
        row["backend"]
        for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1
        if row["rollout_wave"] == "first_wave"
    ]
    if first_wave != ["rs", "cs"]:
        raise SystemExit(
            "relative import non-cpp rollout must keep rs/cs as the first wave: "
            f"got {first_wave}"
        )
    for row in RELATIVE_IMPORT_NONCPP_ROLLOUT_V1:
        backend = row["backend"]
        if backend == "cpp":
            if row["rollout_wave"] != "baseline_locked" or row["next_verification_lane"] != "already_locked":
                raise SystemExit(
                    "cpp must remain the locked baseline lane in non-cpp rollout inventory"
                )
            continue
        if row["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "non-cpp rollout rows must keep backend_specific_fail_closed until rollout is complete: "
                f"got {backend}={row['fail_closed_lane']}"
            )
        if backend in {"rs", "cs"}:
            if row["next_verification_lane"] != "transpile_smoke":
                raise SystemExit(
                    "first-wave backends must lock transpile_smoke next: "
                    f"got {backend}={row['next_verification_lane']}"
                )
            continue
        if row["next_verification_lane"] != "defer_until_first_wave_complete":
            raise SystemExit(
                "second-wave and long-tail backends must stay deferred until first wave completes: "
                f"got {backend}={row['next_verification_lane']}"
            )


def validate_relative_import_noncpp_rollout_handoff() -> None:
    if RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1 != EXPECTED_NONCPP_ROLLOUT_HANDOFF:
        raise SystemExit(
            "relative import non-cpp rollout handoff drifted from the fixed inventory"
        )
    plan_paths = RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_rollout_plan"]
    for doc_path in RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["backend_parity_docs"]:
        doc_text = (ROOT / doc_path).read_text(encoding="utf-8")
        for plan_path in plan_paths:
            plan_name = Path(plan_path).name
            if plan_name not in doc_text:
                raise SystemExit(
                    f"relative import backend parity docs must link the next rollout plan: {doc_path} missing {plan_name}"
                )
        if (
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_verification_lane"]
            not in doc_text
        ):
            raise SystemExit(
                "relative import backend parity docs must mention the next verification lane: "
                f"{doc_path}"
            )
        if RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["fail_closed_lane"] not in doc_text:
            raise SystemExit(
                "relative import backend parity docs must mention the fail-closed lane: "
                f"{doc_path}"
            )


def main() -> None:
    validate_relative_import_backend_coverage()
    validate_relative_import_noncpp_rollout()
    validate_relative_import_noncpp_rollout_handoff()
    print("[OK] relative import backend coverage inventory passed")


if __name__ == "__main__":
    main()

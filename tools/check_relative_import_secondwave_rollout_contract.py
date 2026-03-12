#!/usr/bin/env python3
"""Validate the live second-wave relative-import rollout contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compiler.relative_import_secondwave_rollout_contract import (  # noqa: E402
    RELATIVE_IMPORT_SECONDWAVE_BACKEND_BUNDLES_V1,
    RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1,
    RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1,
    RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1,
    RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1,
)


EXPECTED_SECONDWAVE_BACKENDS = [
    "go",
    "java",
    "js",
    "kotlin",
    "nim",
    "scala",
    "swift",
    "ts",
]
EXPECTED_LONGTAIL_BACKENDS = ["lua", "php", "ruby"]
EXPECTED_SCENARIOS = ["parent_module_alias", "parent_symbol_alias"]
EXPECTED_BUNDLES = [
    {
        "bundle_id": "locked_js_ts_smoke_bundle",
        "backends": ("js", "ts"),
        "verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "locked_baseline",
    },
    {
        "bundle_id": "native_path_bundle",
        "backends": ("go", "nim", "swift"),
        "verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "next_rollout",
    },
    {
        "bundle_id": "jvm_package_bundle",
        "backends": ("java", "kotlin", "scala"),
        "verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "followup_rollout",
    },
]
EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01",
    "verification_lane": "second_wave_rollout_planning",
    "fail_closed_lane": "backend_specific_fail_closed",
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-secondwave-planning.md",
        "docs/en/plans/p1-relative-import-secondwave-planning.md",
    ),
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "bundle_order": (
        "locked_js_ts_smoke_bundle",
        "native_path_bundle",
        "jvm_package_bundle",
    ),
    "next_bundle_id": "native_path_bundle",
}


def validate_relative_import_secondwave_rollout_contract() -> None:
    if RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1 != EXPECTED_SECONDWAVE_BACKENDS:
        raise SystemExit(
            "second-wave backend order drifted: "
            f"{RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1!r}"
        )
    if RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1 != EXPECTED_LONGTAIL_BACKENDS:
        raise SystemExit(
            "long-tail backend order drifted: "
            f"{RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1!r}"
        )
    if RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1 != EXPECTED_SCENARIOS:
        raise SystemExit(
            "second-wave representative scenarios drifted: "
            f"{RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1!r}"
        )
    if RELATIVE_IMPORT_SECONDWAVE_BACKEND_BUNDLES_V1 != EXPECTED_BUNDLES:
        raise SystemExit(
            "second-wave backend bundles drifted: "
            f"{RELATIVE_IMPORT_SECONDWAVE_BACKEND_BUNDLES_V1!r}"
        )
    if RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit(
            "second-wave handoff drifted: "
            f"{RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1!r}"
        )
    for rel_path in RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing active plan path: {rel_path}")
    for rel_path in RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1["backend_parity_docs"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing backend parity doc: {rel_path}")


def main() -> int:
    validate_relative_import_secondwave_rollout_contract()
    print("[OK] relative-import second-wave rollout contract is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

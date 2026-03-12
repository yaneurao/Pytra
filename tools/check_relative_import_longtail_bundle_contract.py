#!/usr/bin/env python3
"""Validate the archived long-tail relative-import fail-closed bundle contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_longtail_bundle_contract import (
    RELATIVE_IMPORT_LONGTAIL_BUNDLE_BACKENDS_V1,
    RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1,
    RELATIVE_IMPORT_LONGTAIL_BUNDLE_SCENARIOS_V1,
)


EXPECTED_SCENARIOS = {
    "parent_module_alias": {
        "entry_rel": "pkg/sub/main.py",
        "import_form": "from .. import helper as h",
        "helper_rel": "pkg/helper.py",
        "representative_expr": "h.f()",
    },
    "parent_symbol_alias": {
        "entry_rel": "pkg/sub/main.py",
        "import_form": "from ..helper import f as g",
        "helper_rel": "pkg/helper.py",
        "representative_expr": "g()",
    },
}

EXPECTED_BACKENDS = ("lua", "php", "ruby")

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01",
    "archive_plan_paths": (
        "docs/ja/plans/archive/20260312-p1-relative-import-longtail-bundle.md",
        "docs/en/plans/archive/20260312-p1-relative-import-longtail-bundle.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "bundle_id": "longtail_relative_import_rollout",
    "backends": ("lua", "php", "ruby"),
    "bundle_state": "locked_fail_closed_baseline",
    "verification_lane": "backend_native_fail_closed",
    "fail_closed_lane": "backend_specific_fail_closed",
    "current_contract_state": "fail_closed_locked",
    "current_evidence_lane": "backend_native_fail_closed",
    "locked_transpile_smoke_backends": (
        "rs",
        "cs",
        "go",
        "java",
        "js",
        "kotlin",
        "nim",
        "scala",
        "swift",
        "ts",
    ),
    "followup_bundle_id": "longtail_relative_import_support_rollout",
    "followup_backends": ("lua", "php", "ruby"),
    "followup_verification_lane": "longtail_relative_import_support_rollout",
}


def validate_relative_import_longtail_bundle_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry for entry in RELATIVE_IMPORT_LONGTAIL_BUNDLE_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import long-tail scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import long-tail scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(entry["backend"] for entry in RELATIVE_IMPORT_LONGTAIL_BUNDLE_BACKENDS_V1)
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import long-tail backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_LONGTAIL_BUNDLE_BACKENDS_V1:
        if entry["verification_lane"] != "backend_native_fail_closed":
            raise SystemExit(
                "long-tail bundle backend must stay on backend_native_fail_closed: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "long-tail bundle scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "long-tail bundle fail-closed lane drifted: "
                f"{entry['backend']}={entry['fail_closed_lane']}"
            )
    if RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit("relative import long-tail handoff drifted from the fixed inventory")
    for rel_path in RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1["archive_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing long-tail archive plan path: {rel_path}")


def main() -> None:
    validate_relative_import_longtail_bundle_contract()
    print("[OK] relative import long-tail bundle contract passed")


if __name__ == "__main__":
    main()

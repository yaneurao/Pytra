#!/usr/bin/env python3
"""Validate the archived JVM-package relative-import rollout bundle contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_jvm_package_bundle_contract import (
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1,
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1,
    relative_import_jvm_package_bundle_coverage_rows,
    relative_import_jvm_package_bundle_handoff_snapshot,
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

EXPECTED_BACKENDS = ("java", "kotlin", "scala")

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01",
    "archive_plan_paths": (
        "docs/ja/plans/archive/20260312-p1-relative-import-jvm-package-bundle.md",
        "docs/en/plans/archive/20260312-p1-relative-import-jvm-package-bundle.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "bundle_id": "jvm_package_bundle",
    "backends": ("java", "kotlin", "scala"),
    "bundle_state": "locked_representative_smoke",
    "verification_lane": "transpile_smoke_locked",
    "fail_closed_lane": "backend_specific_fail_closed",
    "followup_bundle_id": "longtail_relative_import_rollout",
    "followup_backends": ("lua", "php", "ruby"),
    "followup_verification_lane": "longtail_relative_import_rollout",
}


def validate_relative_import_jvm_package_bundle_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import JVM-package scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import JVM-package scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(
        entry["backend"] for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1
    )
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import JVM-package backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1:
        if entry["verification_lane"] != "transpile_smoke_locked":
            raise SystemExit(
                "JVM-package bundle backend must stay on transpile_smoke_locked: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "JVM-package bundle scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "JVM-package bundle fail-closed lane drifted: "
                f"{entry['backend']}={entry['fail_closed_lane']}"
            )
    if RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit("relative import JVM-package handoff drifted from the fixed inventory")
    coverage_rows = relative_import_jvm_package_bundle_coverage_rows()
    if [row["backend"] for row in coverage_rows] != list(EXPECTED_BACKENDS):
        raise SystemExit(
            "relative import JVM-package coverage rows drifted from the backend order"
        )
    for row in coverage_rows:
        if row["contract_state"] != EXPECTED_HANDOFF["verification_lane"]:
            raise SystemExit(
                "relative import JVM-package coverage rows must stay transpile_smoke_locked: "
                f"{row['backend']}={row['contract_state']}"
            )
        if row["evidence_lane"] != "package_project_transpile":
            raise SystemExit(
                "relative import JVM-package coverage rows must stay on package_project_transpile: "
                f"{row['backend']}={row['evidence_lane']}"
            )
    if relative_import_jvm_package_bundle_handoff_snapshot() != {
        "next_rollout_backends": EXPECTED_HANDOFF["followup_backends"],
        "next_verification_lane": EXPECTED_HANDOFF["followup_verification_lane"],
        "fail_closed_lane": EXPECTED_HANDOFF["fail_closed_lane"],
    }:
        raise SystemExit(
            "relative import JVM-package handoff snapshot drifted from coverage handoff"
        )
    for rel_path in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1["archive_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing JVM-package archive plan path: {rel_path}")


def main() -> None:
    validate_relative_import_jvm_package_bundle_contract()
    print("[OK] relative import JVM-package bundle contract passed")


if __name__ == "__main__":
    main()

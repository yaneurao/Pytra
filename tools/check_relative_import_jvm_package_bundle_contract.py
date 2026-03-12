#!/usr/bin/env python3
"""Validate the live JVM-package relative-import rollout bundle contract."""

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
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-jvm-package-bundle.md",
        "docs/en/plans/p1-relative-import-jvm-package-bundle.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "bundle_id": "jvm_package_bundle",
    "backends": ("java", "kotlin", "scala"),
    "verification_lane": "jvm_package_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
    "followup_bundle_id": "longtail_relative_import_rollout",
    "followup_backends": ("lua", "php", "ruby"),
    "followup_verification_lane": "defer_until_jvm_package_bundle_complete",
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
        if entry["verification_lane"] != "jvm_package_bundle_rollout":
            raise SystemExit(
                "JVM-package bundle backend must stay on jvm_package_bundle_rollout: "
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
    for rel_path in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing JVM-package active plan path: {rel_path}")


def main() -> None:
    validate_relative_import_jvm_package_bundle_contract()
    print("[OK] relative import JVM-package bundle contract passed")


if __name__ == "__main__":
    main()

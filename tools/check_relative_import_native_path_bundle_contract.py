#!/usr/bin/env python3
"""Validate the live native-path relative-import rollout bundle contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_native_path_bundle_contract import (
    RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_BACKENDS_V1,
    RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_HANDOFF_V1,
    RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_SCENARIOS_V1,
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

EXPECTED_BACKENDS = ("go", "nim", "swift")

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01",
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-native-path-bundle.md",
        "docs/en/plans/p1-relative-import-native-path-bundle.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "bundle_id": "native_path_bundle",
    "backends": ("go", "nim", "swift"),
    "verification_lane": "native_path_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
    "followup_bundle_id": "jvm_package_bundle",
    "followup_backends": ("java", "kotlin", "scala"),
    "followup_verification_lane": "remaining_second_wave_rollout_planning",
}


def validate_relative_import_native_path_bundle_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import native-path scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import native-path scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(
        entry["backend"] for entry in RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_BACKENDS_V1
    )
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import native-path backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_BACKENDS_V1:
        if entry["verification_lane"] != "native_path_bundle_rollout":
            raise SystemExit(
                "native-path bundle backend must stay on native_path_bundle_rollout: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "native-path bundle scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "native-path bundle fail-closed lane drifted: "
                f"{entry['backend']}={entry['fail_closed_lane']}"
            )
    if RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit("relative import native-path handoff drifted from the fixed inventory")
    for rel_path in RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing native-path active plan path: {rel_path}")


def main() -> None:
    validate_relative_import_native_path_bundle_contract()
    print("[OK] relative import native-path bundle contract passed")


if __name__ == "__main__":
    main()

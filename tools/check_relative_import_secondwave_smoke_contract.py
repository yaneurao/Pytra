#!/usr/bin/env python3
"""Validate the canonical second-wave relative-import transpile-smoke contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_secondwave_smoke_contract import (
    RELATIVE_IMPORT_SECOND_WAVE_BACKENDS_V1,
    RELATIVE_IMPORT_SECOND_WAVE_HANDOFF_V1,
    RELATIVE_IMPORT_SECOND_WAVE_SCENARIOS_V1,
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

EXPECTED_BACKENDS = ("js", "ts")

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_backends": ("java", "kotlin", "scala"),
    "next_verification_lane": "jvm_package_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
}


def validate_relative_import_secondwave_smoke_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry for entry in RELATIVE_IMPORT_SECOND_WAVE_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import second-wave scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import second-wave scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(entry["backend"] for entry in RELATIVE_IMPORT_SECOND_WAVE_BACKENDS_V1)
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import second-wave backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_SECOND_WAVE_BACKENDS_V1:
        if entry["verification_lane"] != "transpile_smoke":
            raise SystemExit(
                "relative import second-wave backend must stay on transpile_smoke: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "relative import second-wave scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["fail_closed_policy"] != "backend_specific_fail_closed_until_supported":
            raise SystemExit(
                "relative import second-wave fail-closed policy drifted: "
                f"{entry['backend']}={entry['fail_closed_policy']}"
            )
    if RELATIVE_IMPORT_SECOND_WAVE_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit(
            "relative import second-wave handoff drifted from the fixed inventory"
        )


def main() -> None:
    validate_relative_import_secondwave_smoke_contract()
    print("[OK] relative import second-wave smoke contract passed")


if __name__ == "__main__":
    main()

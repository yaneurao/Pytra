#!/usr/bin/env python3
"""Validate the canonical first-wave relative-import transpile-smoke contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_firstwave_smoke_contract import (
    RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1,
    RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1,
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

EXPECTED_BACKENDS = ("rs", "cs")


def validate_relative_import_firstwave_smoke_contract() -> None:
    scenario_map = {entry["scenario_id"]: entry for entry in RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1}
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import first-wave scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import first-wave scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(entry["backend"] for entry in RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1)
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import first-wave backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1:
        if entry["verification_lane"] != "transpile_smoke":
            raise SystemExit(
                "relative import first-wave backend must stay on transpile_smoke: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "relative import first-wave scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["fail_closed_policy"] != "backend_specific_fail_closed_until_supported":
            raise SystemExit(
                "relative import first-wave fail-closed policy drifted: "
                f"{entry['backend']}={entry['fail_closed_policy']}"
            )


def main() -> None:
    validate_relative_import_firstwave_smoke_contract()
    print("[OK] relative import first-wave smoke contract passed")


if __name__ == "__main__":
    main()

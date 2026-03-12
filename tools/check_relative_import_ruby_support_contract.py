#!/usr/bin/env python3
"""Validate the backend-local Ruby relative-import support contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_ruby_support_contract import (
    RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_SCENARIOS_V1,
    RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1,
    relative_import_ruby_support_parent_backend_snapshot,
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

EXPECTED_BACKEND = {
    "backend": "ruby",
    "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
    "current_contract_state": "fail_closed_locked",
    "current_evidence_lane": "backend_native_fail_closed",
    "verification_lane": "longtail_relative_import_support_rollout",
    "focused_verification_lane": "ruby_relative_import_support_rollout_smoke",
    "fail_closed_lane": "backend_specific_fail_closed",
}

EXPECTED_SMOKE = {
    "smoke_test_file": "test/unit/backends/rb/test_py2rb_smoke.py",
    "focused_tests": (
        "test_cli_relative_import_support_rollout_fail_closed_for_ruby",
        "test_cli_relative_import_support_rollout_fail_closed_for_wildcard_on_ruby",
    ),
    "expected_error_family": (
        "unsupported relative import form: relative import",
        "unsupported relative import form: wildcard import",
    ),
    "expected_backend_marker": "ruby native emitter",
}

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-03",
    "parent_todo_id": "P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01",
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-longtail-support.md",
        "docs/en/plans/p1-relative-import-longtail-support.md",
    ),
    "support_contract_inventory": "src/toolchain/compiler/relative_import_longtail_support_contract.py",
    "support_checker": "tools/check_relative_import_longtail_support_contract.py",
    "focused_contract_inventory": "src/toolchain/compiler/relative_import_ruby_support_contract.py",
    "focused_checker": "tools/check_relative_import_ruby_support_contract.py",
    "smoke_test_file": "test/unit/backends/rb/test_py2rb_smoke.py",
    "backend": "ruby",
    "verification_lane": "longtail_relative_import_support_rollout",
    "focused_verification_lane": "ruby_relative_import_support_rollout_smoke",
    "current_contract_state": "fail_closed_locked",
    "current_evidence_lane": "backend_native_fail_closed",
    "fail_closed_lane": "backend_specific_fail_closed",
}


def validate_relative_import_ruby_support_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry for entry in RELATIVE_IMPORT_RUBY_SUPPORT_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "ruby relative-import support scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "ruby relative-import support scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    if RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1 != EXPECTED_BACKEND:
        raise SystemExit("ruby relative-import support backend contract drifted")
    if RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1 != EXPECTED_SMOKE:
        raise SystemExit("ruby relative-import support smoke contract drifted")
    if RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit("ruby relative-import support handoff drifted")
    if relative_import_ruby_support_parent_backend_snapshot() != {
        "backend": "ruby",
        "scenario_ids": EXPECTED_BACKEND["scenario_ids"],
        "current_contract_state": EXPECTED_BACKEND["current_contract_state"],
        "current_evidence_lane": EXPECTED_BACKEND["current_evidence_lane"],
        "verification_lane": EXPECTED_BACKEND["verification_lane"],
        "fail_closed_lane": EXPECTED_BACKEND["fail_closed_lane"],
    }:
        raise SystemExit(
            "ruby relative-import support parent backend snapshot drifted from the generic contract"
        )
    for rel_path in RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing ruby support active plan path: {rel_path}")
    smoke_path = ROOT / RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["smoke_test_file"]
    if not smoke_path.is_file():
        raise SystemExit(f"missing ruby support smoke file: {smoke_path}")
    smoke_src = smoke_path.read_text(encoding="utf-8")
    for test_name in RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["focused_tests"]:
        if f"def {test_name}(" not in smoke_src:
            raise SystemExit(f"missing ruby support focused smoke test: {test_name}")
    for needle in (
        *RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["expected_error_family"],
        RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["expected_backend_marker"],
    ):
        if needle not in smoke_src:
            raise SystemExit(f"missing ruby support smoke diagnostic marker: {needle}")
    emitter_path = ROOT / "src/backends/ruby/emitter/ruby_native_emitter.py"
    emitter_src = emitter_path.read_text(encoding="utf-8")
    for needle in (
        *RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["expected_error_family"],
        RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["expected_backend_marker"],
    ):
        if needle not in emitter_src:
            raise SystemExit(f"missing ruby emitter diagnostic marker: {needle}")


def main() -> None:
    validate_relative_import_ruby_support_contract()
    print("[OK] ruby relative-import support contract passed")


if __name__ == "__main__":
    main()

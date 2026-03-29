"""Canonical backend-local contract for Ruby relative-import support rollout."""

from __future__ import annotations

from typing import Final

from toolchain.misc.relative_import_longtail_support_contract import (
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1,
)


RELATIVE_IMPORT_RUBY_SUPPORT_SCENARIOS_V1: Final[list[dict[str, object]]] = [
    entry for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1
]

RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1: Final[dict[str, object]] = {
    "backend": "ruby",
    "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
    "current_contract_state": "transpile_smoke_locked",
    "current_evidence_lane": "native_emitter_function_body_transpile",
    "verification_lane": "longtail_relative_import_support_rollout",
    "focused_verification_lane": "ruby_relative_import_support_rollout_smoke",
    "fail_closed_lane": "backend_specific_fail_closed",
}

RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1: Final[dict[str, object]] = {
    "smoke_test_file": "tools/unittest/emit/rb/test_py2rb_smoke.py",
    "focused_tests": (
        "test_cli_relative_import_support_rollout_scenarios_transpile_for_ruby",
        "test_cli_relative_import_support_rollout_fail_closed_for_wildcard_on_ruby",
    ),
    "expected_rewrite_markers": ("helper_f()",),
    "expected_emitter_markers": (
        "_RELATIVE_IMPORT_MODULE_ALIASES",
        "_RELATIVE_IMPORT_SYMBOL_ALIASES",
        "module_path + \"_\" + _safe_ident(name, \"fn\")",
    ),
    "expected_error_family": (
        "unsupported relative import form: wildcard import",
    ),
    "expected_backend_marker": "ruby native emitter",
}

RELATIVE_IMPORT_RUBY_SUPPORT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-03",
    "parent_todo_id": RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1["todo_id"],
    "active_plan_paths": RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1["active_plan_paths"],
    "support_contract_inventory": "src/toolchain/compiler/relative_import_longtail_support_contract.py",
    "support_checker": "tools/check_relative_import_longtail_support_contract.py",
    "focused_contract_inventory": "src/toolchain/compiler/relative_import_ruby_support_contract.py",
    "focused_checker": "tools/check_relative_import_ruby_support_contract.py",
    "smoke_test_file": RELATIVE_IMPORT_RUBY_SUPPORT_SMOKE_V1["smoke_test_file"],
    "backend": "ruby",
    "verification_lane": RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1["verification_lane"],
    "focused_verification_lane": RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1[
        "focused_verification_lane"
    ],
    "current_contract_state": RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1[
        "current_contract_state"
    ],
    "current_evidence_lane": RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1[
        "current_evidence_lane"
    ],
    "fail_closed_lane": RELATIVE_IMPORT_RUBY_SUPPORT_BACKEND_V1["fail_closed_lane"],
}


def relative_import_ruby_support_parent_backend_snapshot() -> dict[str, object]:
    entry = next(
        row for row in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1 if row["backend"] == "ruby"
    )
    return {
        "backend": entry["backend"],
        "scenario_ids": tuple(entry["scenario_ids"]),
        "current_contract_state": entry["current_contract_state"],
        "current_evidence_lane": entry["current_evidence_lane"],
        "verification_lane": entry["verification_lane"],
        "fail_closed_lane": entry["fail_closed_lane"],
    }

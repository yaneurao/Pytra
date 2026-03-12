#!/usr/bin/env python3
"""Validate the live long-tail relative-import support rollout contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolchain.compiler.relative_import_longtail_support_contract import (
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1,
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1,
    relative_import_longtail_support_archive_snapshot,
    relative_import_longtail_support_coverage_rows,
    relative_import_longtail_support_handoff_snapshot,
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
EXPECTED_FOCUSED_VERIFICATION_LANES = (
    "lua_relative_import_support_rollout_smoke",
    "php_relative_import_support_rollout_smoke",
    "ruby_relative_import_support_rollout_smoke",
)

EXPECTED_HANDOFF = {
    "todo_id": "P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01",
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-longtail-support.md",
        "docs/en/plans/p1-relative-import-longtail-support.md",
    ),
    "archived_prereq_plan_paths": (
        "docs/ja/plans/archive/20260312-p1-relative-import-longtail-bundle.md",
        "docs/en/plans/archive/20260312-p1-relative-import-longtail-bundle.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "bundle_id": "longtail_relative_import_support_rollout",
    "bundle_state": "active_rollout",
    "backends": ("lua", "php", "ruby"),
    "verification_lane": "longtail_relative_import_support_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
    "current_contract_state": "mixed_rollout_locked",
    "current_evidence_lane": "mixed_backend_evidence",
    "prereq_bundle_id": "longtail_relative_import_rollout",
    "followup_bundle_id": "none",
    "followup_backends": (),
    "followup_verification_lane": "none",
    "remaining_rollout_backends": ("php", "ruby"),
}


def validate_relative_import_longtail_support_contract() -> None:
    scenario_map = {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1
    }
    if set(scenario_map) != set(EXPECTED_SCENARIOS):
        raise SystemExit(
            "relative import long-tail support scenarios drifted: "
            f"expected={sorted(EXPECTED_SCENARIOS)}, got={sorted(scenario_map)}"
        )
    for scenario_id, expected in EXPECTED_SCENARIOS.items():
        current = scenario_map[scenario_id]
        for key, value in expected.items():
            if current[key] != value:
                raise SystemExit(
                    "relative import long-tail support scenario drifted: "
                    f"{scenario_id}.{key}={current[key]!r} != {value!r}"
                )
    backend_order = tuple(
        entry["backend"] for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1
    )
    if backend_order != EXPECTED_BACKENDS:
        raise SystemExit(
            "relative import long-tail support backends drifted: "
            f"expected={EXPECTED_BACKENDS}, got={backend_order}"
        )
    for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1:
        if tuple(entry["scenario_ids"]) != tuple(EXPECTED_SCENARIOS):
            raise SystemExit(
                "relative import long-tail support scenario coverage drifted: "
                f"{entry['backend']}={entry['scenario_ids']}"
            )
        if entry["backend"] == "lua":
            if entry["current_contract_state"] != "transpile_smoke_locked":
                raise SystemExit(
                    "lua must move to transpile_smoke_locked in the active long-tail rollout: "
                    f"{entry['current_contract_state']}"
                )
            if entry["current_evidence_lane"] != "native_emitter_function_body_transpile":
                raise SystemExit(
                    "lua must use native_emitter_function_body_transpile as current evidence: "
                    f"{entry['current_evidence_lane']}"
                )
        else:
            if entry["current_contract_state"] != "fail_closed_locked":
                raise SystemExit(
                    "php/ruby must remain fail_closed_locked during the live rollout: "
                    f"{entry['backend']}={entry['current_contract_state']}"
                )
            if entry["current_evidence_lane"] != "backend_native_fail_closed":
                raise SystemExit(
                    "php/ruby must keep backend_native_fail_closed as current evidence: "
                    f"{entry['backend']}={entry['current_evidence_lane']}"
                )
        if entry["verification_lane"] != "longtail_relative_import_support_rollout":
            raise SystemExit(
                "long-tail support backend verification lane drifted: "
                f"{entry['backend']}={entry['verification_lane']}"
            )
        if entry["focused_verification_lane"] != EXPECTED_FOCUSED_VERIFICATION_LANES[
            EXPECTED_BACKENDS.index(entry["backend"])
        ]:
            raise SystemExit(
                "long-tail support backend focused verification lane drifted: "
                f"{entry['backend']}={entry['focused_verification_lane']}"
            )
        if entry["fail_closed_lane"] != "backend_specific_fail_closed":
            raise SystemExit(
                "long-tail support fail-closed lane drifted: "
                f"{entry['backend']}={entry['fail_closed_lane']}"
            )
    if RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1 != EXPECTED_HANDOFF:
        raise SystemExit(
            "relative import long-tail support handoff drifted from the fixed inventory"
        )
    coverage_rows = relative_import_longtail_support_coverage_rows()
    if [row["backend"] for row in coverage_rows] != list(EXPECTED_BACKENDS):
        raise SystemExit(
            "relative import long-tail support coverage rows drifted from backend order"
        )
    for row in coverage_rows:
        if row["backend"] == "lua":
            if row["contract_state"] != "transpile_smoke_locked":
                raise SystemExit(
                    "lua coverage row must move to transpile_smoke_locked: "
                    f"{row['contract_state']}"
                )
            if row["evidence_lane"] != "native_emitter_function_body_transpile":
                raise SystemExit(
                    "lua coverage row must use native_emitter_function_body_transpile: "
                    f"{row['evidence_lane']}"
                )
        else:
            if row["contract_state"] != "fail_closed_locked":
                raise SystemExit(
                    "php/ruby coverage rows must stay fail_closed_locked: "
                    f"{row['backend']}={row['contract_state']}"
                )
            if row["evidence_lane"] != "backend_native_fail_closed":
                raise SystemExit(
                    "php/ruby coverage rows must stay backend_native_fail_closed: "
                    f"{row['backend']}={row['evidence_lane']}"
                )
    if relative_import_longtail_support_archive_snapshot() != {
        "prereq_bundle_id": EXPECTED_HANDOFF["prereq_bundle_id"],
        "prereq_current_contract_state": "fail_closed_locked",
        "prereq_current_evidence_lane": "backend_native_fail_closed",
        "prereq_followup_bundle_id": EXPECTED_HANDOFF["bundle_id"],
        "prereq_followup_verification_lane": EXPECTED_HANDOFF["verification_lane"],
    }:
        raise SystemExit(
            "relative import long-tail support archive snapshot drifted from the archived bundle handoff"
        )
    if relative_import_longtail_support_handoff_snapshot() != {
            "next_rollout_backends": EXPECTED_HANDOFF["remaining_rollout_backends"],
            "next_verification_lane": EXPECTED_HANDOFF["verification_lane"],
            "current_bundle_contract_state": EXPECTED_HANDOFF["current_contract_state"],
            "current_bundle_evidence_lane": EXPECTED_HANDOFF["current_evidence_lane"],
            "current_bundle_smoke_locked_backends": ("lua",),
            "current_bundle_fail_closed_locked_backends": ("php", "ruby"),
            "focused_verification_lanes": EXPECTED_FOCUSED_VERIFICATION_LANES,
    }:
        raise SystemExit(
            "relative import long-tail support handoff snapshot drifted from backend coverage"
        )
    for rel_path in RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1["active_plan_paths"]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"missing long-tail support live plan path: {rel_path}")
    for rel_path in RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1[
        "archived_prereq_plan_paths"
    ]:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(
                f"missing long-tail support archived prerequisite path: {rel_path}"
            )
    for doc_path in RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1["backend_parity_docs"]:
        doc_text = (ROOT / doc_path).read_text(encoding="utf-8")
        for lane in EXPECTED_FOCUSED_VERIFICATION_LANES:
            if lane not in doc_text:
                raise SystemExit(
                    "relative import long-tail support backend parity docs must mention the focused rollout lanes: "
                    f"{doc_path} missing {lane}"
                )


def main() -> None:
    validate_relative_import_longtail_support_contract()
    print("[OK] relative import long-tail support contract passed")


if __name__ == "__main__":
    main()

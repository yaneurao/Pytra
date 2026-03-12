"""Canonical live contract for the long-tail relative-import support rollout."""

from __future__ import annotations

from typing import Final

from toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
)
from toolchain.compiler.relative_import_longtail_bundle_contract import (
    RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1,
)


RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1: Final[list[dict[str, object]]] = [
    {
        "scenario_id": "parent_module_alias",
        "entry_rel": "pkg/sub/main.py",
        "import_form": "from .. import helper as h",
        "helper_rel": "pkg/helper.py",
        "representative_expr": "h.f()",
    },
    {
        "scenario_id": "parent_symbol_alias",
        "entry_rel": "pkg/sub/main.py",
        "import_form": "from ..helper import f as g",
        "helper_rel": "pkg/helper.py",
        "representative_expr": "g()",
    },
]


RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "lua",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "native_emitter_function_body_transpile",
        "verification_lane": "longtail_relative_import_support_rollout",
        "focused_verification_lane": "lua_relative_import_support_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "php",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "native_emitter_function_body_transpile",
        "verification_lane": "longtail_relative_import_support_rollout",
        "focused_verification_lane": "php_relative_import_support_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "ruby",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "current_contract_state": "fail_closed_locked",
        "current_evidence_lane": "backend_native_fail_closed",
        "verification_lane": "longtail_relative_import_support_rollout",
        "focused_verification_lane": "ruby_relative_import_support_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
    },
]


RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1: Final[dict[str, object]] = {
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
    "remaining_rollout_backends": ("ruby",),
}


def relative_import_longtail_support_coverage_rows() -> list[dict[str, str]]:
    return [
        row
        for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
        if row["backend"] in RELATIVE_IMPORT_LONGTAIL_SUPPORT_HANDOFF_V1["backends"]
    ]


def relative_import_longtail_support_archive_snapshot() -> dict[str, object]:
    return {
        "prereq_bundle_id": RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1["bundle_id"],
        "prereq_current_contract_state": RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1[
            "current_contract_state"
        ],
        "prereq_current_evidence_lane": RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1[
            "current_evidence_lane"
        ],
        "prereq_followup_bundle_id": RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1[
            "followup_bundle_id"
        ],
        "prereq_followup_verification_lane": RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1[
            "followup_verification_lane"
        ],
    }


def relative_import_longtail_support_handoff_snapshot() -> dict[str, object]:
    return {
        "next_rollout_backends": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["next_rollout_backends"],
        "next_verification_lane": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1[
            "next_verification_lane"
        ],
        "current_bundle_contract_state": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1[
            "current_bundle_contract_state"
        ],
        "current_bundle_evidence_lane": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1[
            "current_bundle_evidence_lane"
        ],
        "current_bundle_smoke_locked_backends": tuple(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_smoke_locked_backends"]
        ),
        "current_bundle_fail_closed_locked_backends": tuple(
            RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["current_bundle_fail_closed_locked_backends"]
        ),
        "focused_verification_lanes": tuple(
            str(entry["focused_verification_lane"])
            for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_BACKENDS_V1
        ),
    }

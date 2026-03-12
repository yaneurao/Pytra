"""Canonical archived contract for the long-tail relative-import fail-closed bundle."""

from __future__ import annotations

from typing import Final


RELATIVE_IMPORT_LONGTAIL_BUNDLE_SCENARIOS_V1: Final[list[dict[str, object]]] = [
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


RELATIVE_IMPORT_LONGTAIL_BUNDLE_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "lua",
        "verification_lane": "backend_native_fail_closed",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "php",
        "verification_lane": "backend_native_fail_closed",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "ruby",
        "verification_lane": "backend_native_fail_closed",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
]


RELATIVE_IMPORT_LONGTAIL_BUNDLE_HANDOFF_V1: Final[dict[str, object]] = {
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

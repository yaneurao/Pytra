"""Canonical archived contract for the JVM-package relative-import rollout bundle."""

from __future__ import annotations

from typing import Final

from toolchain.compiler.relative_import_backend_coverage import (
    RELATIVE_IMPORT_BACKEND_COVERAGE_V1,
    RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1,
)


RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1: Final[list[dict[str, object]]] = [
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


RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "java",
        "verification_lane": "transpile_smoke_locked",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "kotlin",
        "verification_lane": "transpile_smoke_locked",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
    {
        "backend": "scala",
        "verification_lane": "transpile_smoke_locked",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_lane": "backend_specific_fail_closed",
    },
]


RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1: Final[dict[str, object]] = {
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


def relative_import_jvm_package_bundle_coverage_rows() -> list[dict[str, str]]:
    return [
        row
        for row in RELATIVE_IMPORT_BACKEND_COVERAGE_V1
        if row["backend"] in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_HANDOFF_V1["backends"]
    ]


def relative_import_jvm_package_bundle_handoff_snapshot() -> dict[str, object]:
    return {
        "next_rollout_backends": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1[
            "next_rollout_backends"
        ],
        "next_verification_lane": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1[
            "next_verification_lane"
        ],
        "fail_closed_lane": RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1["fail_closed_lane"],
    }

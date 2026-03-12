"""Canonical live handoff contract for second-wave relative-import rollout."""

from __future__ import annotations

from typing import Final


RELATIVE_IMPORT_SECONDWAVE_BACKENDS_V1: Final[list[str]] = [
    "go",
    "java",
    "js",
    "kotlin",
    "nim",
    "scala",
    "swift",
    "ts",
]

RELATIVE_IMPORT_LONGTAIL_BACKENDS_V1: Final[list[str]] = [
    "lua",
    "php",
    "ruby",
]

RELATIVE_IMPORT_SECONDWAVE_REPRESENTATIVE_SCENARIOS_V1: Final[list[str]] = [
    "parent_module_alias",
    "parent_symbol_alias",
]

RELATIVE_IMPORT_SECONDWAVE_BACKEND_BUNDLES_V1: Final[list[dict[str, object]]] = [
    {
        "bundle_id": "locked_js_ts_smoke_bundle",
        "backends": ("js", "ts"),
        "verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "locked_baseline",
    },
    {
        "bundle_id": "native_path_bundle",
        "backends": ("go", "nim", "swift"),
        "verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "locked_representative_smoke",
    },
    {
        "bundle_id": "jvm_package_bundle",
        "backends": ("java", "kotlin", "scala"),
        "verification_lane": "jvm_package_bundle_rollout",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle_state": "active_rollout",
    },
]

RELATIVE_IMPORT_SECONDWAVE_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01",
    "verification_lane": "jvm_package_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
    "active_plan_paths": (
        "docs/ja/plans/p1-relative-import-jvm-package-bundle.md",
        "docs/en/plans/p1-relative-import-jvm-package-bundle.md",
    ),
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "bundle_order": (
        "locked_js_ts_smoke_bundle",
        "native_path_bundle",
        "jvm_package_bundle",
    ),
    "next_bundle_id": "jvm_package_bundle",
}

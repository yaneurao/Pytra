"""Canonical contract for relative wildcard import rollout on native backends."""

from __future__ import annotations

from typing import Final


RELATIVE_WILDCARD_IMPORT_NATIVE_CPP_BASELINE_V1: Final[dict[str, object]] = {
    "backend": "cpp",
    "current_contract_state": "build_run_locked",
    "current_evidence_lane": "multi_file_build_run",
    "representative_import_form": "from .helper import *",
}


RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "go",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "go_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "native_path_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "java",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "java_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "jvm_package_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "kotlin",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "kotlin_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "jvm_package_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "lua",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "lua_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "longtail_native_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "nim",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "nim_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "native_path_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "php",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "php_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "longtail_native_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "ruby",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "ruby_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "longtail_native_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "scala",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "scala_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "jvm_package_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
    {
        "backend": "swift",
        "current_contract_state": "transpile_smoke_locked",
        "current_evidence_lane": "module_graph_bundle_transpile",
        "verification_lane": "relative_wildcard_import_native_rollout",
        "focused_verification_lane": "swift_relative_wildcard_import_rollout_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "bundle": "native_path_bundle",
        "expected_error_family": ("unsupported relative import form: wildcard import",),
    },
]


RELATIVE_WILDCARD_IMPORT_NATIVE_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01",
    "active_plan_paths": (
        "docs/ja/plans/p0-relative-wildcard-import-native-rollout.md",
        "docs/en/plans/p0-relative-wildcard-import-native-rollout.md",
    ),
    "contract_inventory": (
        "src/toolchain/compiler/relative_wildcard_import_native_rollout_contract.py"
    ),
    "contract_checker": "tools/check_relative_wildcard_import_native_rollout_contract.py",
    "current_bundle_id": "longtail_native_bundle",
    "current_bundle_state": "transpile_smoke_locked",
    "bundle_order": (
        "native_path_bundle",
        "jvm_package_bundle",
        "longtail_native_bundle",
    ),
    "backends": tuple(row["backend"] for row in RELATIVE_WILDCARD_IMPORT_NATIVE_BACKENDS_V1),
    "current_contract_state": "transpile_smoke_locked",
    "current_fail_closed_lane": "backend_specific_fail_closed",
}

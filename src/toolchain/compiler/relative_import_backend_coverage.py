"""Canonical backend coverage inventory for relative-import verification."""

from __future__ import annotations

from typing import Final


RELATIVE_IMPORT_BACKEND_COVERAGE_V1: Final[list[dict[str, str]]] = [
    {
        "backend": "cpp",
        "contract_state": "build_run_locked",
        "evidence_lane": "multi_file_build_run",
        "notes": "Nested-package chain and bare-parent relative imports are locked through multi-file C++ build/run smoke.",
    },
    {
        "backend": "rs",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "single_output_transpile",
        "notes": "Representative relative-import transpile smoke is locked through the Rust backend smoke suite.",
    },
    {
        "backend": "cs",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "single_output_transpile",
        "notes": "Representative relative-import transpile smoke is locked through the C# backend smoke suite.",
    },
    {
        "backend": "go",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "native_emitter_function_body_transpile",
        "notes": "Representative relative-import smoke is locked through direct native-emitter function-body transpile checks.",
    },
    {
        "backend": "java",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "js",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "single_output_transpile",
        "notes": "Representative relative-import transpile smoke is locked through the JavaScript backend smoke suite.",
    },
    {
        "backend": "kotlin",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "lua",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "nim",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "native_emitter_function_body_transpile",
        "notes": "Representative relative-import smoke is locked through direct native-emitter function-body transpile checks.",
    },
    {
        "backend": "php",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "ruby",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "scala",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "swift",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "native_emitter_function_body_transpile",
        "notes": "Representative relative-import smoke is locked through direct native-emitter function-body transpile checks.",
    },
    {
        "backend": "ts",
        "contract_state": "transpile_smoke_locked",
        "evidence_lane": "single_output_transpile",
        "notes": "Representative relative-import transpile smoke is locked through the TypeScript backend smoke suite.",
    },
]


RELATIVE_IMPORT_NONCPP_ROLLOUT_V1: Final[list[dict[str, str]]] = [
    {
        "backend": "cpp",
        "rollout_wave": "baseline_locked",
        "next_verification_lane": "already_locked",
        "fail_closed_lane": "n/a",
        "notes": "C++ already owns the locked build/run baseline for relative imports.",
    },
    {
        "backend": "rs",
        "rollout_wave": "first_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative transpile smoke is locked; keep backend-specific fail-closed diagnostics until support is widened.",
    },
    {
        "backend": "cs",
        "rollout_wave": "first_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative transpile smoke is locked; keep backend-specific fail-closed diagnostics until support is widened.",
    },
    {
        "backend": "go",
        "rollout_wave": "second_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative native-path smoke is locked; the completed native_path_bundle now stays in the transpile_smoke_locked baseline.",
    },
    {
        "backend": "java",
        "rollout_wave": "second_wave",
        "next_verification_lane": "jvm_package_bundle_rollout",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS and native-path representative smoke are locked; the jvm_package_bundle is now the active live rollout bundle.",
    },
    {
        "backend": "js",
        "rollout_wave": "second_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative transpile smoke is locked; keep backend-specific fail-closed diagnostics until support is widened.",
    },
    {
        "backend": "kotlin",
        "rollout_wave": "second_wave",
        "next_verification_lane": "jvm_package_bundle_rollout",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS and native-path representative smoke are locked; the jvm_package_bundle is now the active live rollout bundle.",
    },
    {
        "backend": "lua",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_jvm_package_bundle_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the active JVM package bundle.",
    },
    {
        "backend": "nim",
        "rollout_wave": "second_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative native-path smoke is locked; the completed native_path_bundle now stays in the transpile_smoke_locked baseline.",
    },
    {
        "backend": "php",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_jvm_package_bundle_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the active JVM package bundle.",
    },
    {
        "backend": "ruby",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_jvm_package_bundle_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the active JVM package bundle.",
    },
    {
        "backend": "scala",
        "rollout_wave": "second_wave",
        "next_verification_lane": "jvm_package_bundle_rollout",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS and native-path representative smoke are locked; the jvm_package_bundle is now the active live rollout bundle.",
    },
    {
        "backend": "swift",
        "rollout_wave": "second_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative native-path smoke is locked; the completed native_path_bundle now stays in the transpile_smoke_locked baseline.",
    },
    {
        "backend": "ts",
        "rollout_wave": "second_wave",
        "next_verification_lane": "transpile_smoke_locked",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Representative transpile smoke is locked; keep backend-specific fail-closed diagnostics until support is widened.",
    },
]


RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_plan": (
        "docs/ja/plans/p1-relative-import-jvm-package-bundle.md",
        "docs/en/plans/p1-relative-import-jvm-package-bundle.md",
    ),
    "locked_transpile_smoke_backends": ("rs", "cs", "go", "js", "nim", "swift", "ts"),
    "next_rollout_backends": ("java", "kotlin", "scala"),
    "second_wave_bundle_order": (
        "locked_js_ts_smoke_bundle",
        "native_path_bundle",
        "jvm_package_bundle",
    ),
    "next_rollout_bundle": "jvm_package_bundle",
    "next_rollout_bundle_backends": ("java", "kotlin", "scala"),
    "followup_rollout_bundle": "longtail_relative_import_rollout",
    "followup_rollout_bundle_backends": ("lua", "php", "ruby"),
    "next_verification_lane": "jvm_package_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
}

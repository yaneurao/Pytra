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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
    },
    {
        "backend": "java",
        "rollout_wave": "second_wave",
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
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
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
    },
    {
        "backend": "lua",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_second_wave_remaining_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the remaining second-wave rollout bundle.",
    },
    {
        "backend": "nim",
        "rollout_wave": "second_wave",
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
    },
    {
        "backend": "php",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_second_wave_remaining_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the remaining second-wave rollout bundle.",
    },
    {
        "backend": "ruby",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_second_wave_remaining_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind the remaining second-wave rollout bundle.",
    },
    {
        "backend": "scala",
        "rollout_wave": "second_wave",
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
    },
    {
        "backend": "swift",
        "rollout_wave": "second_wave",
        "next_verification_lane": "remaining_second_wave_rollout_planning",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "JS/TS representative smoke is locked; remaining second-wave rollout stays under planning until the next backend bundle is chosen.",
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
    "todo_id": "P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_plan": (
        "docs/ja/plans/p1-relative-import-secondwave-planning.md",
        "docs/en/plans/p1-relative-import-secondwave-planning.md",
    ),
    "locked_transpile_smoke_backends": ("rs", "cs", "js", "ts"),
    "next_rollout_backends": ("go", "java", "kotlin", "nim", "scala", "swift"),
    "second_wave_bundle_order": (
        "locked_js_ts_smoke_bundle",
        "native_path_bundle",
        "jvm_package_bundle",
    ),
    "next_rollout_bundle": "native_path_bundle",
    "next_rollout_bundle_backends": ("go", "nim", "swift"),
    "followup_rollout_bundle": "jvm_package_bundle",
    "followup_rollout_bundle_backends": ("java", "kotlin", "scala"),
    "next_verification_lane": "remaining_second_wave_rollout_planning",
    "fail_closed_lane": "backend_specific_fail_closed",
}

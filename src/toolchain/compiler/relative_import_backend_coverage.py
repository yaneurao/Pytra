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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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
        "next_verification_lane": "transpile_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "First add representative transpile smoke; keep backend-specific fail-closed diagnostics until support is widened.",
    },
    {
        "backend": "cs",
        "rollout_wave": "first_wave",
        "next_verification_lane": "transpile_smoke",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "First add representative transpile smoke; keep backend-specific fail-closed diagnostics until support is widened.",
    },
    {
        "backend": "go",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "java",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "js",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "kotlin",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "lua",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind first-wave and second-wave stabilization.",
    },
    {
        "backend": "nim",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "php",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind first-wave and second-wave stabilization.",
    },
    {
        "backend": "ruby",
        "rollout_wave": "long_tail",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Long-tail rollout stays blocked behind first-wave and second-wave stabilization.",
    },
    {
        "backend": "scala",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "swift",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
    {
        "backend": "ts",
        "rollout_wave": "second_wave",
        "next_verification_lane": "defer_until_first_wave_complete",
        "fail_closed_lane": "backend_specific_fail_closed",
        "notes": "Do not widen support claims before first-wave backends have locked representative smoke.",
    },
]


RELATIVE_IMPORT_NONCPP_ROLLOUT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_plan": (
        "docs/ja/plans/p1-relative-import-firstwave-smoke.md",
        "docs/en/plans/p1-relative-import-firstwave-smoke.md",
    ),
    "first_wave_backends": ("rs", "cs"),
    "next_verification_lane": "second_wave_rollout_planning",
    "fail_closed_lane": "backend_specific_fail_closed",
}

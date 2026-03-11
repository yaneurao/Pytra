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
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
    },
    {
        "backend": "cs",
        "contract_state": "not_locked",
        "evidence_lane": "none",
        "notes": "No representative relative-import backend smoke is locked yet.",
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


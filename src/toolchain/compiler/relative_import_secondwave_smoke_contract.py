"""Canonical second-wave transpile-smoke contract for relative imports."""

from __future__ import annotations

from typing import Final


RELATIVE_IMPORT_SECOND_WAVE_SCENARIOS_V1: Final[list[dict[str, object]]] = [
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


RELATIVE_IMPORT_SECOND_WAVE_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "js",
        "verification_lane": "transpile_smoke",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_policy": "backend_specific_fail_closed_until_supported",
    },
    {
        "backend": "ts",
        "verification_lane": "transpile_smoke",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_policy": "backend_specific_fail_closed_until_supported",
    },
]


RELATIVE_IMPORT_SECOND_WAVE_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": "P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01",
    "coverage_inventory": "src/toolchain/compiler/relative_import_backend_coverage.py",
    "coverage_checker": "tools/check_relative_import_backend_coverage.py",
    "backend_parity_docs": (
        "docs/ja/language/backend-parity-matrix.md",
        "docs/en/language/backend-parity-matrix.md",
    ),
    "next_rollout_backends": ("java", "kotlin", "scala"),
    "next_verification_lane": "jvm_package_bundle_rollout",
    "fail_closed_lane": "backend_specific_fail_closed",
}

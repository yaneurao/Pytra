"""Canonical first-wave transpile-smoke contract for relative imports."""

from __future__ import annotations

from typing import Final


RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1: Final[list[dict[str, object]]] = [
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


RELATIVE_IMPORT_FIRST_WAVE_BACKENDS_V1: Final[list[dict[str, object]]] = [
    {
        "backend": "rs",
        "verification_lane": "transpile_smoke",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_policy": "backend_specific_fail_closed_until_supported",
    },
    {
        "backend": "cs",
        "verification_lane": "transpile_smoke",
        "scenario_ids": ("parent_module_alias", "parent_symbol_alias"),
        "fail_closed_policy": "backend_specific_fail_closed_until_supported",
    },
]

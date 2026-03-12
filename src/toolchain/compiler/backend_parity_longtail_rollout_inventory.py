"""Canonical residual inventory for the long-tail backend parity rollout."""

from __future__ import annotations

from typing import Final, TypedDict

from toolchain.compiler import backend_parity_matrix_contract as matrix_mod


LONGTAIL_ROLLOUT_TODO_ID: Final[str] = "P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01"
LONGTAIL_ROLLOUT_PLAN_JA: Final[str] = "docs/ja/plans/p6-backend-parity-longtail-rollout.md"
LONGTAIL_ROLLOUT_PLAN_EN: Final[str] = "docs/en/plans/p6-backend-parity-longtail-rollout.md"
LONGTAIL_BACKEND_ORDER: Final[tuple[str, ...]] = ("js", "ts", "lua", "rb", "php")
LONGTAIL_RESIDUAL_STATES: Final[tuple[str, ...]] = ("not_started", "fail_closed")

LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1: Final[dict[str, tuple[str, ...]]] = {
    "js": (),
    "ts": (),
    "lua": (
        "syntax.assign.tuple_destructure",
        "syntax.expr.lambda",
        "syntax.expr.list_comprehension",
        "syntax.control.try_raise",
        "builtin.iter.enumerate",
        "stdlib.json.loads_dumps",
        "stdlib.pathlib.path_ops",
        "stdlib.enum.enum_and_intflag",
        "stdlib.argparse.parse_args",
        "stdlib.math.imported_symbols",
        "stdlib.re.sub",
    ),
    "rb": (
        "syntax.assign.tuple_destructure",
        "syntax.expr.lambda",
        "syntax.expr.list_comprehension",
        "syntax.control.for_range",
        "syntax.control.try_raise",
        "builtin.iter.range",
        "builtin.iter.enumerate",
        "builtin.iter.zip",
        "stdlib.json.loads_dumps",
        "stdlib.pathlib.path_ops",
        "stdlib.enum.enum_and_intflag",
        "stdlib.argparse.parse_args",
        "stdlib.math.imported_symbols",
        "stdlib.re.sub",
    ),
    "php": (
        "syntax.assign.tuple_destructure",
        "syntax.expr.lambda",
        "syntax.expr.list_comprehension",
        "syntax.control.try_raise",
        "builtin.iter.enumerate",
        "stdlib.json.loads_dumps",
        "stdlib.pathlib.path_ops",
        "stdlib.enum.enum_and_intflag",
        "stdlib.argparse.parse_args",
        "stdlib.math.imported_symbols",
        "stdlib.re.sub",
    ),
}


class LongtailResidualCell(TypedDict):
    backend: str
    feature_id: str
    support_state: str
    evidence_kind: str
    representative_fixture: str


class LongtailRolloutBundle(TypedDict):
    bundle_id: str
    backend_order: tuple[str, ...]
    feature_ids_by_backend: dict[str, tuple[str, ...]]
    target_evidence: str
    notes: str


def _feature_fixture_map() -> dict[str, str]:
    return {
        row["feature_id"]: row["representative_fixture"]
        for row in matrix_mod.iter_representative_parity_matrix_rows()
    }


def _build_expected_longtail_residual_cells() -> tuple[LongtailResidualCell, ...]:
    feature_fixture = _feature_fixture_map()
    rows: list[LongtailResidualCell] = []
    for backend in LONGTAIL_BACKEND_ORDER:
        for feature_id in LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1[backend]:
            rows.append(
                {
                    "backend": backend,
                    "feature_id": feature_id,
                    "support_state": "not_started",
                    "evidence_kind": "not_started_placeholder",
                    "representative_fixture": feature_fixture[feature_id],
                }
            )
    return tuple(rows)


def _iter_observed_longtail_residual_cells() -> tuple[LongtailResidualCell, ...]:
    rows: list[LongtailResidualCell] = []
    for row in matrix_mod.iter_representative_parity_matrix_rows():
        for cell in row["backend_cells"]:
            if cell["backend"] not in LONGTAIL_BACKEND_ORDER:
                continue
            if cell["support_state"] not in LONGTAIL_RESIDUAL_STATES:
                continue
            rows.append(
                {
                    "backend": cell["backend"],
                    "feature_id": row["feature_id"],
                    "support_state": cell["support_state"],
                    "evidence_kind": cell["evidence_kind"],
                    "representative_fixture": row["representative_fixture"],
                }
            )
    backend_rank = {backend: index for index, backend in enumerate(LONGTAIL_BACKEND_ORDER)}
    return tuple(sorted(rows, key=lambda row: (backend_rank[row["backend"]], row["feature_id"])))


LONGTAIL_RESIDUAL_CELLS_V1: Final[tuple[LongtailResidualCell, ...]] = (
    _build_expected_longtail_residual_cells()
)


LONGTAIL_ROLLOUT_BUNDLES_V1: Final[tuple[LongtailRolloutBundle, ...]] = (
    {
        "bundle_id": "js_ts_bundle",
        "backend_order": ("js", "ts"),
        "feature_ids_by_backend": {
            "js": LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["js"],
            "ts": LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["ts"],
        },
        "target_evidence": "transpile_smoke",
        "notes": "The js/ts bundle is complete; the bundle stays as an empty handoff marker so the long-tail rollout can advance to lua/rb/php without losing bundle order.",
    },
    {
        "bundle_id": "lua_rb_php_bundle",
        "backend_order": ("lua", "rb", "php"),
        "feature_ids_by_backend": {
            "lua": LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["lua"],
            "rb": LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["rb"],
            "php": LONGTAIL_RESIDUAL_FEATURE_IDS_BY_BACKEND_V1["php"],
        },
        "target_evidence": "transpile_smoke",
        "notes": "The lua/rb/php bundle keeps the lighter syntax/stdlib gaps together; Ruby also retains for_range/range/zip while Lua/PHP do not.",
    },
)


LONGTAIL_ROLLOUT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": LONGTAIL_ROLLOUT_TODO_ID,
    "coverage_inventory": "src/toolchain/compiler/backend_parity_longtail_rollout_inventory.py",
    "coverage_checker": "tools/check_backend_parity_longtail_rollout_inventory.py",
    "matrix_contract": "src/toolchain/compiler/backend_parity_matrix_contract.py",
    "plan_paths": (
        LONGTAIL_ROLLOUT_PLAN_JA,
        LONGTAIL_ROLLOUT_PLAN_EN,
    ),
    "backend_order": LONGTAIL_BACKEND_ORDER,
    "residual_states": LONGTAIL_RESIDUAL_STATES,
    "completed_backends": ("js", "ts"),
    "next_backend": "lua",
    "remaining_backends": ("rb", "php"),
    "bundle_order": tuple(bundle["bundle_id"] for bundle in LONGTAIL_ROLLOUT_BUNDLES_V1),
    "next_bundle": "lua_rb_php_bundle",
    "target_evidence_lane": "transpile_smoke",
}


def iter_longtail_rollout_residual_cells() -> tuple[LongtailResidualCell, ...]:
    return LONGTAIL_RESIDUAL_CELLS_V1


def iter_longtail_rollout_bundles() -> tuple[LongtailRolloutBundle, ...]:
    return LONGTAIL_ROLLOUT_BUNDLES_V1


def build_longtail_rollout_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "todo_id": LONGTAIL_ROLLOUT_HANDOFF_V1["todo_id"],
        "coverage_inventory": LONGTAIL_ROLLOUT_HANDOFF_V1["coverage_inventory"],
        "coverage_checker": LONGTAIL_ROLLOUT_HANDOFF_V1["coverage_checker"],
        "matrix_contract": LONGTAIL_ROLLOUT_HANDOFF_V1["matrix_contract"],
        "plan_paths": list(LONGTAIL_ROLLOUT_HANDOFF_V1["plan_paths"]),
        "backend_order": list(LONGTAIL_BACKEND_ORDER),
        "residual_states": list(LONGTAIL_RESIDUAL_STATES),
        "completed_backends": list(LONGTAIL_ROLLOUT_HANDOFF_V1["completed_backends"]),
        "next_backend": LONGTAIL_ROLLOUT_HANDOFF_V1["next_backend"],
        "remaining_backends": list(LONGTAIL_ROLLOUT_HANDOFF_V1["remaining_backends"]),
        "bundle_order": list(LONGTAIL_ROLLOUT_HANDOFF_V1["bundle_order"]),
        "next_bundle": LONGTAIL_ROLLOUT_HANDOFF_V1["next_bundle"],
        "target_evidence_lane": LONGTAIL_ROLLOUT_HANDOFF_V1["target_evidence_lane"],
        "residual_cells": list(iter_longtail_rollout_residual_cells()),
        "rollout_bundles": [
            {
                "bundle_id": bundle["bundle_id"],
                "backend_order": list(bundle["backend_order"]),
                "feature_ids_by_backend": {
                    backend: list(feature_ids)
                    for backend, feature_ids in bundle["feature_ids_by_backend"].items()
                },
                "target_evidence": bundle["target_evidence"],
                "notes": bundle["notes"],
            }
            for bundle in iter_longtail_rollout_bundles()
        ],
    }


def collect_observed_longtail_rollout_residual_cells() -> tuple[LongtailResidualCell, ...]:
    return _iter_observed_longtail_residual_cells()

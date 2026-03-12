"""Canonical residual inventory for the representative backend parity rollout."""

from __future__ import annotations

from typing import Final, TypedDict

from toolchain.compiler import backend_parity_matrix_contract as matrix_mod


REPRESENTATIVE_ROLLOUT_TODO_ID: Final[str] = "P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01"
REPRESENTATIVE_ROLLOUT_PLAN_JA: Final[str] = (
    "docs/ja/plans/p4-backend-parity-representative-rollout.md"
)
REPRESENTATIVE_ROLLOUT_PLAN_EN: Final[str] = (
    "docs/en/plans/p4-backend-parity-representative-rollout.md"
)
REPRESENTATIVE_BACKEND_ORDER: Final[tuple[str, ...]] = ("cpp", "rs", "cs")
REPRESENTATIVE_RESIDUAL_STATES: Final[tuple[str, ...]] = ("not_started", "fail_closed")


class RepresentativeResidualCell(TypedDict):
    backend: str
    feature_id: str
    support_state: str
    evidence_kind: str
    representative_fixture: str


class RepresentativeRolloutBundle(TypedDict):
    bundle_id: str
    backend: str
    feature_ids: tuple[str, ...]
    target_evidence: str
    notes: str


def _iter_observed_representative_residual_cells() -> tuple[RepresentativeResidualCell, ...]:
    rows: list[RepresentativeResidualCell] = []
    for row in matrix_mod.iter_representative_parity_matrix_rows():
        for cell in row["backend_cells"]:
            if cell["backend"] not in REPRESENTATIVE_BACKEND_ORDER:
                continue
            if cell["support_state"] not in REPRESENTATIVE_RESIDUAL_STATES:
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
    backend_rank = {backend: index for index, backend in enumerate(REPRESENTATIVE_BACKEND_ORDER)}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                backend_rank[row["backend"]],
                row["feature_id"],
            ),
        )
    )


REPRESENTATIVE_RESIDUAL_CELLS_V1: Final[tuple[RepresentativeResidualCell, ...]] = (
    {
        "backend": "rs",
        "feature_id": "builtin.iter.zip",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/signature/ok_generator_tuple_target.py",
    },
    {
        "backend": "cs",
        "feature_id": "syntax.control.for_range",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/control/for_range.py",
    },
    {
        "backend": "cs",
        "feature_id": "syntax.control.try_raise",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/control/try_raise.py",
    },
    {
        "backend": "cs",
        "feature_id": "builtin.iter.range",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/control/for_range.py",
    },
    {
        "backend": "cs",
        "feature_id": "builtin.iter.zip",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/signature/ok_generator_tuple_target.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.json.loads_dumps",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.pathlib.path_ops",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.enum.enum_and_intflag",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/enum_extended.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.argparse.parse_args",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.math.imported_symbols",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
    },
    {
        "backend": "cs",
        "feature_id": "stdlib.re.sub",
        "support_state": "not_started",
        "evidence_kind": "not_started_placeholder",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
    },
)


REPRESENTATIVE_ROLLOUT_BUNDLES_V1: Final[tuple[RepresentativeRolloutBundle, ...]] = (
    {
        "bundle_id": "cpp_locked_baseline",
        "backend": "cpp",
        "feature_ids": (),
        "target_evidence": "build_run_smoke",
        "notes": "The representative cpp residual inventory is empty; keep the existing build/run baseline locked and move directly to rs.",
    },
    {
        "bundle_id": "rs_syntax_iter_bundle",
        "backend": "rs",
        "feature_ids": ("builtin.iter.zip",),
        "target_evidence": "transpile_smoke",
        "notes": "Rust representative syntax rows are green; keep the remaining iterator zip row isolated until direct evidence is locked.",
    },
    {
        "bundle_id": "rs_stdlib_bundle",
        "backend": "rs",
        "feature_ids": (),
        "target_evidence": "transpile_smoke",
        "notes": "The representative Rust stdlib rows are green; keep the empty bundle as a handoff marker while cs becomes the next backend.",
    },
    {
        "bundle_id": "cs_syntax_iter_bundle",
        "backend": "cs",
        "feature_ids": (
            "syntax.control.for_range",
            "syntax.control.try_raise",
            "builtin.iter.range",
            "builtin.iter.zip",
        ),
        "target_evidence": "transpile_smoke",
        "notes": "Cover the C# syntax and iterator rows together before moving to stdlib-heavy bundles.",
    },
    {
        "bundle_id": "cs_stdlib_bundle",
        "backend": "cs",
        "feature_ids": (
            "stdlib.json.loads_dumps",
            "stdlib.pathlib.path_ops",
            "stdlib.enum.enum_and_intflag",
            "stdlib.argparse.parse_args",
            "stdlib.math.imported_symbols",
            "stdlib.re.sub",
        ),
        "target_evidence": "transpile_smoke",
        "notes": "Finish the C# representative residuals with the remaining stdlib rows.",
    },
)


REPRESENTATIVE_ROLLOUT_HANDOFF_V1: Final[dict[str, object]] = {
    "todo_id": REPRESENTATIVE_ROLLOUT_TODO_ID,
    "coverage_inventory": "src/toolchain/compiler/backend_parity_representative_rollout_inventory.py",
    "coverage_checker": "tools/check_backend_parity_representative_rollout_inventory.py",
    "matrix_contract": "src/toolchain/compiler/backend_parity_matrix_contract.py",
    "plan_paths": (
        REPRESENTATIVE_ROLLOUT_PLAN_JA,
        REPRESENTATIVE_ROLLOUT_PLAN_EN,
    ),
    "backend_order": REPRESENTATIVE_BACKEND_ORDER,
    "residual_states": REPRESENTATIVE_RESIDUAL_STATES,
    "completed_backends": ("cpp",),
    "next_backend": "rs",
    "remaining_backends": ("rs", "cs"),
    "bundle_order": tuple(bundle["bundle_id"] for bundle in REPRESENTATIVE_ROLLOUT_BUNDLES_V1),
    "target_evidence_lane": "transpile_smoke",
}


def iter_representative_rollout_residual_cells() -> tuple[RepresentativeResidualCell, ...]:
    return REPRESENTATIVE_RESIDUAL_CELLS_V1


def iter_representative_rollout_bundles() -> tuple[RepresentativeRolloutBundle, ...]:
    return REPRESENTATIVE_ROLLOUT_BUNDLES_V1


def build_representative_rollout_handoff_manifest() -> dict[str, object]:
    return {
        "inventory_version": 1,
        "todo_id": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["todo_id"],
        "coverage_inventory": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["coverage_inventory"],
        "coverage_checker": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["coverage_checker"],
        "matrix_contract": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["matrix_contract"],
        "plan_paths": list(REPRESENTATIVE_ROLLOUT_HANDOFF_V1["plan_paths"]),
        "backend_order": list(REPRESENTATIVE_BACKEND_ORDER),
        "residual_states": list(REPRESENTATIVE_RESIDUAL_STATES),
        "completed_backends": list(REPRESENTATIVE_ROLLOUT_HANDOFF_V1["completed_backends"]),
        "next_backend": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["next_backend"],
        "remaining_backends": list(REPRESENTATIVE_ROLLOUT_HANDOFF_V1["remaining_backends"]),
        "bundle_order": list(REPRESENTATIVE_ROLLOUT_HANDOFF_V1["bundle_order"]),
        "target_evidence_lane": REPRESENTATIVE_ROLLOUT_HANDOFF_V1["target_evidence_lane"],
        "residual_cells": list(iter_representative_rollout_residual_cells()),
        "rollout_bundles": list(iter_representative_rollout_bundles()),
    }


def collect_observed_representative_rollout_residual_cells() -> tuple[RepresentativeResidualCell, ...]:
    return _iter_observed_representative_residual_cells()

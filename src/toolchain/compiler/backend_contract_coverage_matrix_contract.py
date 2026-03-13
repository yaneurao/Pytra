"""Seed ownership rows for bundle-based backend contract coverage."""

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_conformance_inventory as conformance_inventory_mod
from src.toolchain.compiler import backend_contract_coverage_inventory as coverage_inventory_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_inventory_mod


OWNER_KIND_ORDER: Final[tuple[str, ...]] = ("bundle", "rule")

BUNDLE_OWNER_BY_LANE: Final[dict[str, str]] = {
    "parse": "frontend_unit_contract_bundle",
    "east": "frontend_unit_contract_bundle",
    "east3_lowering": "frontend_unit_contract_bundle",
    "emit": "emit_backend_smoke_bundle",
}

RUNTIME_RULE_ORDER: Final[tuple[str, ...]] = (
    "case_runtime_followup",
    "module_runtime_strategy_followup",
)

RUNTIME_RULE_BY_CATEGORY: Final[dict[str, str]] = {
    "syntax": "case_runtime_followup",
    "builtin": "case_runtime_followup",
    "stdlib": "module_runtime_strategy_followup",
}


class CoverageMatrixOwnershipRow(TypedDict):
    feature_id: str
    category: str
    representative_fixture: str
    required_lane: str
    backend: str
    owner_kind: str
    bundle_id_or_rule: str


def _build_coverage_matrix_seed_rows() -> tuple[CoverageMatrixOwnershipRow, ...]:
    rows: list[CoverageMatrixOwnershipRow] = []
    for feature_row in conformance_inventory_mod.iter_representative_conformance_fixture_inventory():
        for required_lane in feature_row["required_lanes"]:
            if required_lane in BUNDLE_OWNER_BY_LANE:
                owner_kind = "bundle"
                bundle_id_or_rule = BUNDLE_OWNER_BY_LANE[required_lane]
            elif required_lane == "runtime":
                owner_kind = "rule"
                bundle_id_or_rule = RUNTIME_RULE_BY_CATEGORY[feature_row["category"]]
            else:
                raise ValueError(f"unsupported required lane for coverage seed: {required_lane}")
            for backend in feature_inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER:
                rows.append(
                    {
                        "feature_id": feature_row["feature_id"],
                        "category": feature_row["category"],
                        "representative_fixture": feature_row["representative_fixture"],
                        "required_lane": required_lane,
                        "backend": backend,
                        "owner_kind": owner_kind,
                        "bundle_id_or_rule": bundle_id_or_rule,
                    }
                )
    return tuple(rows)


COVERAGE_MATRIX_CELL_SEED_V1: Final[tuple[CoverageMatrixOwnershipRow, ...]] = _build_coverage_matrix_seed_rows()


def iter_backend_contract_coverage_matrix_seed_rows() -> tuple[CoverageMatrixOwnershipRow, ...]:
    return COVERAGE_MATRIX_CELL_SEED_V1


def build_backend_contract_coverage_matrix_seed_manifest() -> dict[str, object]:
    return {
        "manifest_version": 1,
        "owner_kind_order": list(OWNER_KIND_ORDER),
        "bundle_owner_by_lane": dict(BUNDLE_OWNER_BY_LANE),
        "runtime_rule_order": list(RUNTIME_RULE_ORDER),
        "runtime_rule_by_category": dict(RUNTIME_RULE_BY_CATEGORY),
        "support_backend_order": list(feature_inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER),
        "required_lane_order": list(feature_inventory_mod.CONFORMANCE_LANE_ORDER),
        "rows": list(iter_backend_contract_coverage_matrix_seed_rows()),
    }


def expected_seed_row_count() -> int:
    feature_count = len(conformance_inventory_mod.iter_representative_conformance_fixture_inventory())
    lane_count = len(feature_inventory_mod.CONFORMANCE_LANE_ORDER)
    backend_count = len(feature_inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER)
    return feature_count * lane_count * backend_count


def known_bundle_ids() -> tuple[str, ...]:
    return tuple(bundle["bundle_id"] for bundle in coverage_inventory_mod.iter_backend_contract_coverage_bundles())

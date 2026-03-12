from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_matrix_contract as contract_mod
from tools import check_backend_parity_matrix_contract as check_mod


class CheckBackendParityMatrixContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_matrix_constants_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_MATRIX_SOURCE_MANIFESTS,
            {
                "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
                "conformance_summary_seed": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
            },
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_PUBLISH_PATHS,
            {
                "docs_ja": "docs/ja/language/backend-parity-matrix.md",
                "docs_en": "docs/en/language/backend-parity-matrix.md",
                "tool_manifest": "tools/export_backend_parity_matrix_manifest.py",
            },
        )
        self.assertEqual(contract_mod.PARITY_MATRIX_SOURCE_DESTINATION, "support_matrix")
        self.assertEqual(contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE, "row_seed_scaffold")
        self.assertEqual(contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS, "not_populated")
        self.assertEqual(contract_mod.PARITY_MATRIX_CELL_SCHEMA_VERSION, 1)
        self.assertEqual(contract_mod.PARITY_MATRIX_CELL_COLLECTION_KEY, "backend_cells")
        self.assertEqual(
            contract_mod.PARITY_MATRIX_CELL_REQUIRED_KEYS,
            ("backend", "support_state", "evidence_kind"),
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_CELL_OPTIONAL_KEYS,
            ("details", "evidence_ref", "diagnostic_kind"),
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER,
            (
                "build_run_smoke",
                "transpile_smoke",
                "contract_guard",
                "diagnostic_guard",
                "not_started_placeholder",
                "preview_guard",
            ),
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE,
            {
                "supported": ("build_run_smoke", "transpile_smoke"),
                "fail_closed": ("contract_guard", "diagnostic_guard"),
                "not_started": ("not_started_placeholder",),
                "experimental": ("preview_guard", "transpile_smoke", "build_run_smoke"),
            },
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_CELL_GAP_SUMMARY,
            {
                "missing_per_backend_cells": "The current matrix exports representative row seeds only and does not yet publish per-backend cells.",
                "missing_support_state_per_cell": "Each feature × backend cell still lacks an explicit support_state entry.",
                "missing_evidence_kind_per_cell": "Each feature × backend cell still lacks an explicit evidence_kind entry.",
            },
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_ROW_KEYS,
            (
                "feature_id",
                "category",
                "representative_fixture",
                "backend_order",
                "support_state_order",
            ),
        )

    def test_summary_linkage_is_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_MATRIX_SUMMARY_SOURCE,
            "conformance_summary_handoff.representative_summary_entries",
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_SUMMARY_KEYS,
            (
                "feature_id",
                "category",
                "fixture_class",
                "representative_fixture",
                "summary_kind",
                "shared_lanes",
                "backend_selectable_lanes",
                "backend_order",
                "runtime_lane_policy",
                "runtime_summary_source",
                "support_state_order",
                "downstream_task",
            ),
        )
        self.assertEqual(contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK, "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01")
        self.assertEqual(contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN, "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md")

    def test_manifest_shape_is_fixed(self) -> None:
        self.assertEqual(
            set(contract_mod.build_backend_parity_matrix_manifest().keys()),
            {
                "inventory_version",
                "source_manifests",
                "source_destination",
                "implementation_phase",
                "cell_schema_status",
                "cell_schema",
                "cell_gap_summary",
                "backend_order",
                "support_state_order",
                "publish_paths",
                "summary_source",
                "summary_keys",
                "row_keys",
                "matrix_rows",
            },
        )
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["cell_schema"],
            {
                "schema_version": 1,
                "collection_key": "backend_cells",
                "required_keys": ["backend", "support_state", "evidence_kind"],
                "optional_keys": ["details", "evidence_ref", "diagnostic_kind"],
                "support_state_order": ["supported", "fail_closed", "not_started", "experimental"],
                "evidence_kind_order": [
                    "build_run_smoke",
                    "transpile_smoke",
                    "contract_guard",
                    "diagnostic_guard",
                    "not_started_placeholder",
                    "preview_guard",
                ],
                "allowed_evidence_kinds_by_state": {
                    "supported": ["build_run_smoke", "transpile_smoke"],
                    "fail_closed": ["contract_guard", "diagnostic_guard"],
                    "not_started": ["not_started_placeholder"],
                    "experimental": ["preview_guard", "transpile_smoke", "build_run_smoke"],
                },
            },
        )


if __name__ == "__main__":
    unittest.main()

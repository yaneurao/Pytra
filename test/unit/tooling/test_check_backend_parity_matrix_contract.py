from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_parity_matrix_contract as contract_mod
from tools import check_backend_parity_matrix_contract as check_mod


class CheckBackendParityMatrixContractTest(unittest.TestCase):
    def test_contract_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_contract_issues(), [])

    def test_manifest_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_manifest_issues(), [])

    def test_docs_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_docs_issues(), [])

    def test_matrix_constants_are_fixed(self) -> None:
        self.assertEqual(
            contract_mod.PARITY_MATRIX_SOURCE_MANIFESTS,
            {
                "feature_contract_seed": "backend_feature_contract_inventory.build_feature_contract_handoff_manifest",
                "conformance_summary_seed": "backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest",
                "rollout_tier_seed": "backend_parity_rollout_tier_contract.build_backend_parity_rollout_tier_manifest",
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
        self.assertEqual(
            contract_mod.PARITY_MATRIX_CPP_DRILLDOWN_DOCS,
            {
                "docs_ja": "docs/ja/language/cpp/spec-support.md",
                "docs_en": "docs/en/language/cpp/spec-support.md",
            },
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_BACKEND_ORDER,
            ("cpp", "rs", "cs", "js", "ts", "go", "java", "swift", "kt", "rb", "lua", "scala", "php", "nim"),
        )
        self.assertEqual(
            set(contract_mod.PARITY_MATRIX_BACKEND_ORDER),
            set(contract_mod.PARITY_MATRIX_SUPPORT_INVENTORY_BACKEND_ORDER),
        )
        self.assertEqual(contract_mod.PARITY_MATRIX_SOURCE_DESTINATION, "support_matrix")
        self.assertEqual(contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE, "cell_seed_manifest")
        self.assertEqual(contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS, "seed_populated")
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
                "seed_state_is_conservative": "Current backend cell seeds stay conservative outside the reviewed representative, secondary, and long-tail cells that already have direct transpile or build/run smoke evidence.",
                "docs_table_is_seed_only": "The docs page now renders the seeded 2D support table, but non-reviewed lanes still stay on placeholders outside the reviewed representative, secondary, and long-tail cells.",
                "cell_details_are_sparse": "Per-cell details/evidence_ref/diagnostic_kind remain sparse until follow-up row fill bundles land.",
            },
        )
        self.assertEqual(
            contract_mod.REVIEWED_REPRESENTATIVE_CELL_OVERRIDES,
            {
                "syntax.assign.tuple_destructure": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "syntax.expr.lambda": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "syntax.expr.list_comprehension": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "syntax.control.for_range": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "syntax.oop.virtual_dispatch": {
                    "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "builtin.iter.enumerate": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "builtin.iter.range": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "builtin.type.isinstance": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "builtin.bit.invert_and_mask": {
                    "go": {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "cs": {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "java": {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "kt": {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "scala": {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "swift": {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "nim": {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "js": {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "ts": {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "lua": {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "rb": {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                    "php": {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
                "stdlib.math.imported_symbols": {
                    "rs": {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                },
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
                "backend_cells",
            ),
        )
        self.assertEqual(contract_mod.PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER, "<!-- BEGIN BACKEND PARITY MATRIX TABLE -->")
        self.assertEqual(contract_mod.PARITY_MATRIX_DOC_TABLE_END_MARKER, "<!-- END BACKEND PARITY MATRIX TABLE -->")
        self.assertEqual(
            contract_mod.PARITY_MATRIX_DOC_TABLE_HEADERS,
            ("feature_id", "fixture", *contract_mod.PARITY_MATRIX_BACKEND_ORDER),
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_DOC_ROLE_SPLIT,
            {
                "canonical_matrix": "The cross-backend backend parity matrix is the canonical source for feature x backend support-state reporting.",
                "cpp_drilldown": "The py2cpp support matrix is a cpp-only drill-down that refines the cpp lane without redefining the cross-backend taxonomy.",
            },
        )
        self.assertEqual(
            contract_mod.PARITY_MATRIX_DOC_MAINTENANCE_ORDER,
            (
                "update_matrix_contract_and_docs",
                "sync_cpp_drilldown_docs",
            ),
        )
        self.assertEqual(contract_mod.PARITY_MATRIX_ROLLOUT_TIER_ORDER, ("representative", "secondary", "long_tail"))
        self.assertEqual(
            contract_mod.PARITY_MATRIX_ROLLOUT_TIERS,
            (
                {
                    "tier": "representative",
                    "backend_order": ("cpp", "rs", "cs"),
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
                {
                    "tier": "secondary",
                    "backend_order": ("go", "java", "kt", "scala", "swift", "nim"),
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
                {
                    "tier": "long_tail",
                    "backend_order": ("js", "ts", "lua", "rb", "php"),
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
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
                "cpp_drilldown_docs",
                "doc_role_split",
                "maintenance_order",
                "rollout_tier_order",
                "rollout_tiers",
                "summary_source",
                "summary_keys",
                "row_keys",
                "matrix_rows",
            },
        )
        first_row = contract_mod.build_backend_parity_matrix_manifest()["matrix_rows"][0]
        self.assertEqual(first_row["backend_cells"][0], {
            "backend": "cpp",
            "support_state": "supported",
            "evidence_kind": "build_run_smoke",
        })
        self.assertEqual(
            first_row["backend_cells"][1:3],
            [
                {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            ],
        )
        self.assertTrue(
            all(
                cell == {
                    "backend": backend,
                    "support_state": "not_started",
                    "evidence_kind": "not_started_placeholder",
                }
                for backend, cell in zip(contract_mod.PARITY_MATRIX_BACKEND_ORDER[3:], first_row["backend_cells"][3:])
            )
        )
        rows = {
            row["feature_id"]: row
            for row in contract_mod.build_backend_parity_matrix_manifest()["matrix_rows"]
        }
        cells = {
            feature_id: {cell["backend"]: cell for cell in row["backend_cells"]}
            for feature_id, row in rows.items()
        }
        self.assertEqual(
            [cells["builtin.bit.invert_and_mask"]["rs"], cells["builtin.bit.invert_and_mask"]["cs"]],
            [
                {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            ],
        )
        self.assertEqual(
            cells["syntax.control.for_range"]["rs"],
            {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["syntax.control.for_range"]["java"],
            {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["syntax.control.for_range"]["nim"],
            {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["syntax.control.for_range"]["lua"],
            {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["syntax.control.for_range"]["php"],
            {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["builtin.iter.range"]["rs"],
            {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["builtin.iter.range"]["java"],
            {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["builtin.iter.range"]["nim"],
            {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["builtin.iter.range"]["lua"],
            {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["builtin.iter.range"]["php"],
            {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["syntax.oop.virtual_dispatch"]["cs"],
            {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            [
                cells["syntax.oop.virtual_dispatch"]["go"],
                cells["syntax.oop.virtual_dispatch"]["java"],
                cells["syntax.oop.virtual_dispatch"]["kt"],
                cells["syntax.oop.virtual_dispatch"]["scala"],
                cells["syntax.oop.virtual_dispatch"]["swift"],
                cells["syntax.oop.virtual_dispatch"]["nim"],
            ],
            [
                {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "nim", "support_state": "not_started", "evidence_kind": "not_started_placeholder"},
            ],
        )
        self.assertEqual(
            [
                cells["syntax.oop.virtual_dispatch"]["js"],
                cells["syntax.oop.virtual_dispatch"]["ts"],
                cells["syntax.oop.virtual_dispatch"]["lua"],
                cells["syntax.oop.virtual_dispatch"]["rb"],
                cells["syntax.oop.virtual_dispatch"]["php"],
            ],
            [
                {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "ts", "support_state": "not_started", "evidence_kind": "not_started_placeholder"},
                {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            ],
        )
        self.assertEqual(
            [
                cells["builtin.bit.invert_and_mask"]["rs"],
                cells["builtin.bit.invert_and_mask"]["cs"],
                cells["builtin.bit.invert_and_mask"]["go"],
                cells["builtin.bit.invert_and_mask"]["java"],
                cells["builtin.bit.invert_and_mask"]["kt"],
                cells["builtin.bit.invert_and_mask"]["scala"],
                cells["builtin.bit.invert_and_mask"]["swift"],
                cells["builtin.bit.invert_and_mask"]["nim"],
                cells["builtin.bit.invert_and_mask"]["js"],
                cells["builtin.bit.invert_and_mask"]["ts"],
                cells["builtin.bit.invert_and_mask"]["lua"],
                cells["builtin.bit.invert_and_mask"]["rb"],
                cells["builtin.bit.invert_and_mask"]["php"],
            ],
            [
                {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "cs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "go", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "java", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "kt", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "scala", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "swift", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "nim", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "js", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "ts", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            ],
        )
        self.assertEqual(
            [
                cells["builtin.type.isinstance"]["rs"],
                cells["builtin.type.isinstance"]["lua"],
                cells["builtin.type.isinstance"]["rb"],
                cells["builtin.type.isinstance"]["php"],
            ],
            [
                {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "lua", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "rb", "support_state": "supported", "evidence_kind": "transpile_smoke"},
                {"backend": "php", "support_state": "supported", "evidence_kind": "transpile_smoke"},
            ],
        )
        self.assertEqual(
            cells["stdlib.math.imported_symbols"]["rs"],
            {"backend": "rs", "support_state": "supported", "evidence_kind": "transpile_smoke"},
        )
        self.assertEqual(
            cells["stdlib.math.imported_symbols"]["cs"],
            {"backend": "cs", "support_state": "not_started", "evidence_kind": "not_started_placeholder"},
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
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["cpp_drilldown_docs"],
            {
                "docs_ja": "docs/ja/language/cpp/spec-support.md",
                "docs_en": "docs/en/language/cpp/spec-support.md",
            },
        )
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["doc_role_split"],
            {
                "canonical_matrix": "The cross-backend backend parity matrix is the canonical source for feature x backend support-state reporting.",
                "cpp_drilldown": "The py2cpp support matrix is a cpp-only drill-down that refines the cpp lane without redefining the cross-backend taxonomy.",
            },
        )
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["maintenance_order"],
            [
                "update_matrix_contract_and_docs",
                "sync_cpp_drilldown_docs",
            ],
        )
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["rollout_tier_order"],
            ["representative", "secondary", "long_tail"],
        )
        self.assertEqual(
            contract_mod.build_backend_parity_matrix_manifest()["rollout_tiers"],
            [
                {
                    "tier": "representative",
                    "backend_order": ["cpp", "rs", "cs"],
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
                {
                    "tier": "secondary",
                    "backend_order": ["go", "java", "kt", "scala", "swift", "nim"],
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
                {
                    "tier": "long_tail",
                    "backend_order": ["js", "ts", "lua", "rb", "php"],
                    "downstream_task": contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK,
                    "downstream_plan": contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN,
                },
            ],
        )
        self.assertIn("<th>cpp</th>", contract_mod.build_backend_parity_matrix_html_table())
        self.assertIn(
            '<td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>',
            contract_mod.build_backend_parity_matrix_html_table(),
        )


if __name__ == "__main__":
    unittest.main()

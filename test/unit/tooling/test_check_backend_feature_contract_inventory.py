from __future__ import annotations

import unittest

from src.toolchain.compiler import backend_feature_contract_inventory as inventory_mod
from tools import check_backend_feature_contract_inventory as check_mod


class CheckBackendFeatureContractInventoryTest(unittest.TestCase):
    def test_inventory_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_inventory_issues(), [])

    def test_support_state_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_support_state_issues(), [])

    def test_fail_closed_policy_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_fail_closed_policy_issues(), [])

    def test_acceptance_rule_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_acceptance_rule_issues(), [])

    def test_handoff_issues_are_empty(self) -> None:
        self.assertEqual(check_mod._collect_handoff_issues(), [])

    def test_categories_have_stable_order(self) -> None:
        self.assertEqual(inventory_mod.CATEGORY_ORDER, ("syntax", "builtin", "stdlib"))

    def test_category_naming_rules_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CATEGORY_NAMING_RULES,
            {
                "syntax": "syntax.<area>.<feature>",
                "builtin": "builtin.<domain>.<feature>",
                "stdlib": "stdlib.<module>.<feature>",
            },
        )

    def test_support_state_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.SUPPORT_STATE_ORDER,
            ("supported", "fail_closed", "not_started", "experimental"),
        )
        self.assertEqual(
            set(inventory_mod.SUPPORT_STATE_ORDER),
            set(inventory_mod.SUPPORT_STATE_CRITERIA.keys()),
        )

    def test_fail_closed_taxonomy_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.FAIL_CLOSED_DETAIL_CATEGORIES,
            ("not_implemented", "unsupported_by_design", "preview_only", "blocked"),
        )
        self.assertEqual(
            set(inventory_mod.FAIL_CLOSED_PHASE_RULES.keys()),
            {"parse_and_ir", "emit_and_runtime", "preview_rollout"},
        )
        self.assertEqual(
            inventory_mod.FORBIDDEN_SILENT_FALLBACK_LABELS,
            (
                "object_fallback",
                "string_fallback",
                "comment_stub_fallback",
                "empty_output_fallback",
            ),
        )

    def test_new_feature_acceptance_rules_are_fixed(self) -> None:
        self.assertEqual(
            set(inventory_mod.NEW_FEATURE_ACCEPTANCE_RULES.keys()),
            {
                "feature_id_required",
                "inventory_or_followup_required",
                "cxx_only_not_complete",
                "noncpp_state_required",
                "unsupported_lanes_fail_closed",
                "docs_mirror_required",
            },
        )

    def test_handoff_targets_are_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.HANDOFF_TASK_IDS,
            {
                "conformance_suite": "P6-BACKEND-CONFORMANCE-SUITE-01",
                "support_matrix": "P7-BACKEND-PARITY-ROLLOUT-MATRIX-01",
            },
        )
        self.assertEqual(
            inventory_mod.HANDOFF_PLAN_PATHS,
            {
                "conformance_suite": "docs/ja/plans/p6-backend-conformance-suite.md",
                "support_matrix": "docs/ja/plans/p7-backend-parity-rollout-and-matrix.md",
            },
        )

    def test_conformance_handoff_contract_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.CONFORMANCE_LANE_ORDER,
            ("parse", "east", "east3_lowering", "emit", "runtime"),
        )
        self.assertEqual(inventory_mod.FIRST_CONFORMANCE_BACKEND_ORDER, ("cpp", "rs", "cs"))
        self.assertEqual(
            {entry["feature_id"] for entry in inventory_mod.iter_representative_conformance_handoff()},
            {entry["feature_id"] for entry in inventory_mod.iter_representative_feature_inventory()},
        )

    def test_support_matrix_handoff_contract_is_fixed(self) -> None:
        self.assertEqual(
            inventory_mod.SUPPORT_MATRIX_BACKEND_ORDER,
            ("cpp", "rs", "cs", "go", "java", "kt", "scala", "swift", "nim", "js", "ts", "lua", "rb", "php"),
        )
        self.assertEqual(
            {entry["feature_id"] for entry in inventory_mod.iter_representative_support_matrix_handoff()},
            {entry["feature_id"] for entry in inventory_mod.iter_representative_feature_inventory()},
        )

    def test_handoff_manifest_contract_is_fixed(self) -> None:
        self.assertEqual(
            set(inventory_mod.build_feature_contract_handoff_manifest().keys()),
            {
                "inventory_version",
                "representative_features",
                "conformance_handoff",
                "support_matrix_handoff",
                "support_state_order",
                "fail_closed_detail_categories",
                "handoff_task_ids",
                "handoff_plan_paths",
            },
        )

    def test_representative_inventory_contains_all_categories(self) -> None:
        categories = {entry["category"] for entry in inventory_mod.iter_representative_feature_inventory()}
        self.assertEqual(categories, set(inventory_mod.CATEGORY_ORDER))

    def test_representative_inventory_ids_are_stable(self) -> None:
        self.assertEqual(
            {entry["feature_id"] for entry in inventory_mod.iter_representative_feature_inventory()},
            {
                "syntax.assign.tuple_destructure",
                "syntax.expr.lambda",
                "syntax.expr.list_comprehension",
                "syntax.control.for_range",
                "syntax.control.try_raise",
                "syntax.oop.virtual_dispatch",
                "builtin.iter.range",
                "builtin.iter.enumerate",
                "builtin.iter.zip",
                "builtin.type.isinstance",
                "builtin.bit.invert_and_mask",
                "stdlib.json.loads_dumps",
                "stdlib.pathlib.path_ops",
                "stdlib.enum.enum_and_intflag",
                "stdlib.argparse.parse_args",
                "stdlib.math.imported_symbols",
                "stdlib.re.sub",
            },
        )


if __name__ == "__main__":
    unittest.main()

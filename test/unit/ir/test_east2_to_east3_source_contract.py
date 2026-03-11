"""Source-contract regressions for EAST2 -> EAST3 lowering split modules."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import EAST23_LOWERING_SOURCE_PATH
from _east_core_test_support import EAST23_CALL_METADATA_SOURCE_PATH
from _east_core_test_support import EAST23_STMT_LOWERING_SOURCE_PATH
from _east_core_test_support import EAST23_NOMINAL_ADT_META_SOURCE_PATH
from _east_core_test_support import EAST23_TYPE_ID_PREDICATE_SOURCE_PATH
from _east_core_test_support import EAST23_TYPE_SUMMARY_SOURCE_PATH


class East2ToEast3SourceContractTest(unittest.TestCase):
    def test_main_lowering_imports_type_summary_cluster(self) -> None:
        text = EAST23_LOWERING_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("from toolchain.ir.east2_to_east3_type_summary import _swap_nominal_adt_decl_summary_table", text)
        self.assertIn("from toolchain.ir.east2_to_east3_call_metadata import _decorate_call_metadata", text)
        self.assertIn("from toolchain.ir.east2_to_east3_stmt_lowering import _lower_assignment_like_stmt", text)
        self.assertIn("from toolchain.ir.east2_to_east3_stmt_lowering import _lower_for_stmt", text)
        self.assertIn("from toolchain.ir.east2_to_east3_stmt_lowering import _lower_forrange_stmt", text)
        self.assertIn("from toolchain.ir.east2_to_east3_stmt_lowering import _lower_forcore_stmt", text)
        self.assertIn("from toolchain.ir.east2_to_east3_type_id_predicate import _lower_type_id_call_expr", text)
        self.assertIn(
            "from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_match_stmt",
            text,
        )
        self.assertIn(
            "from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_projection_attr",
            text,
        )
        self.assertIn(
            "from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_variant_pattern",
            text,
        )
        self.assertIn(
            "prev_nominal_adt_decl_table = _swap_nominal_adt_decl_summary_table(",
            text,
        )
        for helper_name in (
            "_type_expr_summary_from_payload",
            "_type_expr_summary_from_node",
            "_collect_nominal_adt_decl_summary_table",
            "_collect_nominal_adt_family_variants",
            "_expr_type_summary",
            "_json_nominal_type_name",
            "_structured_type_expr_summary_from_node",
            "_representative_json_contract_metadata",
            "_make_type_predicate_expr",
            "_collect_expected_type_id_specs",
            "_lower_type_id_call_expr",
            "_infer_json_semantic_tag",
            "_build_json_decode_meta",
            "_lower_representative_json_decode_call",
            "_decorate_call_metadata",
            "_normalize_iter_mode",
            "_resolve_assign_target_type_summary",
            "_resolve_assign_target_type",
            "_build_target_plan",
            "_lower_assignment_like_stmt",
            "_lower_for_stmt",
            "_lower_forrange_stmt",
            "_lower_forcore_stmt",
            "_decorate_nominal_adt_projection_attr",
            "_decorate_nominal_adt_variant_pattern",
            "_decorate_nominal_adt_match_stmt",
        ):
            self.assertNotIn(f"def {helper_name}(", text)

    def test_call_metadata_module_owns_split_helpers(self) -> None:
        text = EAST23_CALL_METADATA_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "from toolchain.ir.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_ctor_call",
            text,
        )
        for helper_name in (
            "_infer_json_semantic_tag",
            "_build_json_decode_meta",
            "_lower_representative_json_decode_call",
            "_decorate_call_metadata",
        ):
            self.assertIn(f"def {helper_name}(", text)

    def test_stmt_lowering_module_owns_split_helpers(self) -> None:
        text = EAST23_STMT_LOWERING_SOURCE_PATH.read_text(encoding="utf-8")
        for helper_name in (
            "_normalize_iter_mode",
            "_resolve_assign_target_type_summary",
            "_resolve_assign_target_type",
            "_build_target_plan",
            "_lower_assignment_like_stmt",
            "_lower_for_stmt",
            "_lower_forrange_stmt",
            "_lower_forcore_stmt",
        ):
            self.assertIn(f"def {helper_name}(", text)

    def test_type_summary_module_owns_split_helpers(self) -> None:
        text = EAST23_TYPE_SUMMARY_SOURCE_PATH.read_text(encoding="utf-8")
        for helper_name in (
            "_swap_nominal_adt_decl_summary_table",
            "_type_expr_summary_from_payload",
            "_collect_nominal_adt_decl_summary_table",
            "_collect_nominal_adt_family_variants",
            "_expr_type_summary",
            "_json_nominal_type_name",
            "_representative_json_contract_metadata",
        ):
            self.assertIn(f"def {helper_name}(", text)

    def test_type_id_predicate_module_owns_split_helpers(self) -> None:
        text = EAST23_TYPE_ID_PREDICATE_SOURCE_PATH.read_text(encoding="utf-8")
        for helper_name in (
            "_make_type_predicate_expr",
            "_build_nominal_adt_type_test_meta",
            "_attach_nominal_adt_type_test_meta",
            "_collect_expected_type_id_specs",
            "_lower_isinstance_call_expr",
            "_lower_issubclass_call_expr",
            "_lower_type_id_call_expr",
        ):
            self.assertIn(f"def {helper_name}(", text)

    def test_nominal_adt_meta_module_owns_split_helpers(self) -> None:
        text = EAST23_NOMINAL_ADT_META_SOURCE_PATH.read_text(encoding="utf-8")
        for helper_name in (
            "_decorate_nominal_adt_ctor_call",
            "_decorate_nominal_adt_projection_attr",
            "_decorate_nominal_adt_variant_pattern",
            "_decorate_nominal_adt_match_stmt",
            "_build_nominal_adt_match_analysis",
        ):
            self.assertIn(f"def {helper_name}(", text)


if __name__ == "__main__":
    unittest.main()

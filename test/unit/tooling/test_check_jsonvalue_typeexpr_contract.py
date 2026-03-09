from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_jsonvalue_typeexpr_contract as guard_mod


class JsonValueTypeExprContractGuardTest(unittest.TestCase):
    def test_collect_passes_for_current_repo_contract(self) -> None:
        self.assertEqual(guard_mod._collect_findings(), [])

    def test_collect_detects_typeexpr_lane_metadata_regression(self) -> None:
        with patch.object(
            guard_mod,
            "_probe_typeexpr_lane",
            return_value={"lowered_kind": "Call", "json_decode_v1": {"contract_source": "resolved_type_compat"}},
        ):
            findings = guard_mod._collect_findings()
        self.assertEqual(
            [item.key for item in findings],
            ["typeexpr_lane_kind", "typeexpr_lane_contract", "typeexpr_lane_receiver_name"],
        )

    def test_collect_detects_compat_and_representative_mismatch_regressions(self) -> None:
        with patch.object(
            guard_mod,
            "_probe_resolved_type_compat_lane",
            return_value={"lowered_kind": "Call", "json_decode_v1": {"contract_source": "type_expr"}},
        ), patch.object(guard_mod, "_probe_representative_mismatch_error", return_value=""):
            findings = guard_mod._collect_findings()
        self.assertEqual(
            [item.key for item in findings],
            ["compat_lane_kind", "compat_lane_contract", "representative_mismatch_guard"],
        )

    def test_collect_detects_helper_lane_and_module_load_regressions(self) -> None:
        with patch.object(
            guard_mod,
            "_probe_json_obj_lane",
            return_value={"semantic_tag": "json.value.as_obj", "json_decode_v1": {"receiver_nominal_adt_name": "JsonValue"}},
        ), patch.object(
            guard_mod,
            "_probe_json_arr_lane",
            return_value={"semantic_tag": "json.obj.get_int", "json_decode_v1": {"receiver_nominal_adt_name": "JsonObj"}},
        ), patch.object(
            guard_mod,
            "_probe_loads_obj_lane",
            return_value={"semantic_tag": "json.loads", "json_decode_v1": {"decode_kind": "narrow", "result_type": {}}},
        ), patch.object(guard_mod, "_probe_json_obj_mismatch_error", return_value=""):
            findings = guard_mod._collect_findings()
        self.assertEqual(
            [item.key for item in findings],
            [
                "json_obj_semantic_tag",
                "json_obj_receiver",
                "json_arr_semantic_tag",
                "json_arr_receiver",
                "loads_obj_semantic_tag",
                "loads_obj_decode_kind",
                "loads_obj_result_type",
                "json_obj_mismatch_guard",
            ],
        )

    def test_main_passes_for_current_repo_contract(self) -> None:
        with patch.object(sys, "argv", ["check_jsonvalue_typeexpr_contract.py"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as buf:
            rc = guard_mod.main()
        self.assertEqual(rc, 0)
        self.assertIn("[OK] jsonvalue TypeExpr contract guard passed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

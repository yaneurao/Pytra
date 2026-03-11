from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from _east23_lowering_test_support import East23LoweringNominalAdtFixtureMixin
from _east23_lowering_test_support import _const_i
from src.toolchain.compiler.east_parts.east2_to_east3_lowering import lower_east2_to_east3
from src.toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.frontends.type_expr import parse_type_expr_text


class East2ToEast3SplitRegressionTest(East23LoweringNominalAdtFixtureMixin, unittest.TestCase):
    def test_load_east3_document_preserves_nominal_adt_match_metadata(self) -> None:
        payload = self.representative_nominal_adt_match_east2()
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "east.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east3_document(p)
        fn = out.get("body", [])[3]
        match_stmt = fn.get("body", [])[0]
        self.assertEqual(match_stmt.get("lowered_kind"), "NominalAdtMatch")
        self.assertEqual(match_stmt.get("nominal_adt_match_v1", {}).get("family_name"), "Maybe")
        first_pattern = match_stmt.get("cases", [])[0].get("pattern", {})
        self.assertEqual(first_pattern.get("lowered_kind"), "NominalAdtVariantPattern")
        self.assertEqual(first_pattern.get("nominal_adt_pattern_v1", {}).get("variant_name"), "Just")
        first_bind = first_pattern.get("subpatterns", [])[0]
        self.assertEqual(first_bind.get("lowered_kind"), "NominalAdtPatternBind")
        self.assertEqual(first_bind.get("nominal_adt_pattern_bind_v1", {}).get("field_name"), "value")

    def test_load_east3_document_lowers_type_id_predicate_via_split_helper(self) -> None:
        payload = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "isinstance"},
                        "args": [
                            {"kind": "Name", "id": "value", "resolved_type": "Child"},
                            {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "east.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east3_document(p, object_dispatch_mode="type_id")
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("kind"), "IsInstance")
        self.assertEqual(value.get("value", {}).get("id"), "value")
        self.assertEqual(value.get("value", {}).get("resolved_type"), "Child")
        self.assertEqual(value.get("expected_type_id", {}).get("id"), "Base")

    def test_lower_user_nominal_adt_constructor_attaches_ctor_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        ctor_call = fn.get("body", [])[1].get("value", {})
        self.assertEqual(ctor_call.get("kind"), "Call")
        self.assertEqual(ctor_call.get("lowered_kind"), "NominalAdtCtorCall")
        self.assertEqual(ctor_call.get("semantic_tag"), "nominal_adt.variant_ctor")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("variant_name"), "Just")
        self.assertEqual(ctor_call.get("type_expr_summary_v1", {}).get("nominal_adt_name"), "Just")

    def test_lower_user_nominal_adt_projection_attaches_projection_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        projection = fn.get("body", [])[2].get("value", {})
        self.assertEqual(projection.get("kind"), "Attribute")
        self.assertEqual(projection.get("lowered_kind"), "NominalAdtProjection")
        self.assertEqual(projection.get("semantic_tag"), "nominal_adt.variant_projection")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("variant_name"), "Just")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("field_name"), "value")

    def test_lower_user_nominal_adt_match_attaches_match_metadata(self) -> None:
        east2 = self.representative_nominal_adt_match_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        match_stmt = fn.get("body", [])[0]
        self.assertEqual(match_stmt.get("kind"), "Match")
        self.assertEqual(match_stmt.get("lowered_kind"), "NominalAdtMatch")
        self.assertEqual(match_stmt.get("semantic_tag"), "nominal_adt.match")
        self.assertEqual(match_stmt.get("nominal_adt_match_v1", {}).get("family_name"), "Maybe")
        first_pattern = match_stmt.get("cases", [])[0].get("pattern", {})
        self.assertEqual(first_pattern.get("lowered_kind"), "NominalAdtVariantPattern")
        self.assertEqual(first_pattern.get("nominal_adt_pattern_v1", {}).get("variant_name"), "Just")
        first_bind = first_pattern.get("subpatterns", [])[0]
        self.assertEqual(first_bind.get("lowered_kind"), "NominalAdtPatternBind")
        self.assertEqual(first_bind.get("nominal_adt_pattern_bind_v1", {}).get("field_name"), "value")

    def test_lower_json_decode_call_uses_split_call_metadata_helper(self) -> None:
        out = lower_east2_to_east3(
            {
                "kind": "Module",
                "meta": {"dispatch_mode": "native"},
                "body": [
                    {
                        "kind": "Expr",
                        "value": {
                            "kind": "Call",
                            "resolved_type": "JsonObj | None",
                            "type_expr": parse_type_expr_text("JsonObj | None"),
                            "func": {
                                "kind": "Attribute",
                                "attr": "as_obj",
                                "value": {
                                    "kind": "Name",
                                    "id": "payload",
                                    "resolved_type": "JsonValue",
                                    "type_expr": parse_type_expr_text("JsonValue"),
                                },
                            },
                            "args": [],
                            "keywords": [],
                        },
                    }
                ],
            }
        )
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("lowered_kind"), "JsonDecodeCall")
        self.assertEqual(value.get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(value.get("json_decode_v1", {}).get("decode_entry"), "json.value.as_obj")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonValue")

    def test_lower_stmt_cluster_keeps_assign_bridge_and_forrange_plan(self) -> None:
        out = lower_east2_to_east3(
            {
                "kind": "Module",
                "meta": {"dispatch_mode": "native"},
                "body": [
                    {
                        "kind": "AnnAssign",
                        "target": {"kind": "Name", "id": "boxed", "resolved_type": "object"},
                        "annotation": "object",
                        "decl_type": "object",
                        "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                        "declare": True,
                    },
                    {
                        "kind": "ForRange",
                        "target": {"kind": "Name", "id": "i"},
                        "target_type": "int64",
                        "start": _const_i(0),
                        "stop": _const_i(4),
                        "step": _const_i(1),
                        "body": [],
                        "orelse": [],
                    },
                ],
            }
        )
        body = out.get("body", [])
        assign_value = body[0].get("value", {})
        self.assertEqual(assign_value.get("kind"), "Box")
        self.assertEqual(assign_value.get("resolved_type"), "object")
        for_stmt = body[1]
        self.assertEqual(for_stmt.get("kind"), "ForCore")
        self.assertEqual(for_stmt.get("iter_mode"), "static_fastpath")
        self.assertEqual(for_stmt.get("iter_plan", {}).get("kind"), "StaticRangeForPlan")
        self.assertEqual(for_stmt.get("target_plan", {}).get("kind"), "NameTarget")

    def test_lower_builtin_jsonvalue_and_user_nominal_adt_share_nominal_adt_category(self) -> None:
        user_out = lower_east2_to_east3(self.representative_nominal_adt_match_east2())
        user_match = user_out.get("body", [])[3].get("body", [])[0]
        user_subject_type = user_match.get("nominal_adt_match_v1", {}).get("subject_type", {})
        self.assertEqual(user_subject_type.get("category"), "nominal_adt")
        self.assertEqual(user_subject_type.get("nominal_adt_family"), "Maybe")

        json_out = lower_east2_to_east3(
            {
                "kind": "Module",
                "meta": {"dispatch_mode": "native"},
                "body": [
                    {
                        "kind": "Expr",
                        "value": {
                            "kind": "Call",
                            "resolved_type": "JsonObj | None",
                            "type_expr": parse_type_expr_text("JsonObj | None"),
                            "func": {
                                "kind": "Attribute",
                                "attr": "as_obj",
                                "value": {
                                    "kind": "Name",
                                    "id": "payload",
                                    "resolved_type": "JsonValue",
                                    "type_expr": parse_type_expr_text("JsonValue"),
                                },
                            },
                            "args": [],
                            "keywords": [],
                        },
                    }
                ],
            }
        )
        json_value = json_out.get("body", [])[0].get("value", {})
        self.assertEqual(json_value.get("type_expr_summary_v1", {}).get("category"), "optional")
        self.assertEqual(json_value.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "json")


if __name__ == "__main__":
    unittest.main()

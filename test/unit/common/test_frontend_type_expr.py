from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.frontends.type_expr import parse_type_expr_text
from src.toolchain.frontends.type_expr import summarize_type_text
from src.toolchain.frontends.type_expr import sync_type_expr_mirrors
from src.toolchain.ir.east2 import normalize_east1_to_east2_document
from src.toolchain.link.program_validator import validate_raw_east3_doc


class FrontendTypeExprTest(unittest.TestCase):
    def test_summarize_type_text_distinguishes_type_lanes(self) -> None:
        optional_nominal = summarize_type_text("JsonValue | None")
        self.assertEqual(optional_nominal["category"], "optional")
        self.assertEqual(optional_nominal["nominal_adt_family"], "json")

        dynamic_union = summarize_type_text("int64 | Any")
        self.assertEqual(dynamic_union["category"], "dynamic_union")
        self.assertEqual(dynamic_union["union_mode"], "dynamic")

        general_union = summarize_type_text("int64 | bool")
        self.assertEqual(general_union["category"], "general_union")
        self.assertEqual(general_union["union_mode"], "general")

    def test_sync_type_expr_mirrors_fills_legacy_string_fields(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 1,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_type_exprs": {
                        "x": parse_type_expr_text("int | bool"),
                    },
                    "return_type_expr": parse_type_expr_text("JsonValue | None"),
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {
                                "kind": "Name",
                                "id": "local",
                                "type_expr": parse_type_expr_text("list[int | bool]"),
                            },
                            "annotation_type_expr": parse_type_expr_text("list[int | bool]"),
                            "decl_type_expr": parse_type_expr_text("list[int | bool]"),
                            "value": None,
                        }
                    ],
                }
            ],
        }

        out = sync_type_expr_mirrors(doc)
        self.assertIs(out, doc)
        fn = doc["body"][0]
        self.assertEqual(fn["arg_types"]["x"], "int64|bool")
        self.assertEqual(fn["return_type"], "JsonValue | None")
        ann = fn["body"][0]
        self.assertEqual(ann["target"]["resolved_type"], "list[int64|bool]")
        self.assertEqual(ann["annotation"], "list[int64|bool]")
        self.assertEqual(ann["decl_type"], "list[int64|bool]")

    def test_sync_type_expr_mirrors_rejects_mismatch(self) -> None:
        doc = {
            "kind": "Module",
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "object",
                        "type_expr": parse_type_expr_text("int | bool"),
                    },
                    "annotation": "int64|bool",
                    "annotation_type_expr": parse_type_expr_text("int | bool"),
                    "decl_type": "int64|bool",
                    "decl_type_expr": parse_type_expr_text("int | bool"),
                    "value": None,
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.target\.resolved_type mismatch"):
            sync_type_expr_mirrors(doc)

    def test_normalize_east1_to_east2_document_uses_type_expr_guard(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 1,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"x": "str"},
                    "arg_type_exprs": {"x": parse_type_expr_text("int")},
                    "return_type": "None",
                    "return_type_expr": parse_type_expr_text("None"),
                    "body": [],
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.arg_types\.x mismatch"):
            normalize_east1_to_east2_document(doc)

    def test_validate_raw_east3_doc_uses_type_expr_guard(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "str",
                        "type_expr": parse_type_expr_text("int"),
                    },
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.value\.resolved_type mismatch"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m")


if __name__ == "__main__":
    unittest.main()

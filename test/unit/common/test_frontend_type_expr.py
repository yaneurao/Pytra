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
from src.toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.compile.east2 import normalize_east1_to_east2_document
from src.toolchain.link import validate_raw_east3_doc


class FrontendTypeExprTest(unittest.TestCase):
    def test_summarize_type_text_distinguishes_type_lanes(self) -> None:
        optional_nominal = summarize_type_text("JsonValue | None")
        self.assertEqual(optional_nominal["category"], "optional")
        self.assertEqual(optional_nominal["nominal_adt_name"], "JsonValue")
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
                    "vararg_type_expr": parse_type_expr_text("Path"),
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
        self.assertEqual(fn["vararg_type"], "Path")
        self.assertEqual(fn["return_type"], "JsonValue | None")
        ann = fn["body"][0]
        self.assertEqual(ann["target"]["resolved_type"], "list[int64|bool]")
        self.assertEqual(ann["annotation"], "list[int64|bool]")
        self.assertEqual(ann["decl_type"], "list[int64|bool]")

    def test_sync_type_expr_mirrors_rejects_vararg_mismatch(self) -> None:
        doc = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "vararg_type": "object",
                    "vararg_type_expr": parse_type_expr_text("Path"),
                    "body": [],
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.vararg_type mismatch"):
            sync_type_expr_mirrors(doc)

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

    def test_validate_raw_east3_doc_rejects_non_object_body_item(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [1],
        }

        with self.assertRaisesRegex(RuntimeError, r"raw EAST3\.body\[0\] must be an object"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m")

    def test_validate_raw_east3_doc_requires_source_span_for_user_node(self) -> None:
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
                        "source_span": {
                            "lineno": 1,
                            "end_lineno": 1,
                            "col_offset": 0,
                            "end_col_offset": 1,
                        },
                    },
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.source_span is required"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m", require_source_spans=True)

    def test_validate_raw_east3_doc_rejects_invalid_source_span_shape(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "source_span": {
                        "lineno": 3,
                        "end_lineno": 2,
                        "col_offset": 4,
                        "end_col_offset": 1,
                    },
                    "value": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"source_span: .* must not encode reversed range"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m", require_source_spans=True)

    def test_validate_raw_east3_doc_rejects_nested_dispatch_mode_drift(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "source_span": {
                        "lineno": 1,
                        "end_lineno": 1,
                        "col_offset": 0,
                        "end_col_offset": 1,
                    },
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "int64",
                        "source_span": {
                            "lineno": 1,
                            "end_lineno": 1,
                            "col_offset": 0,
                            "end_col_offset": 1,
                        },
                        "meta": {"dispatch_mode": "type_id"},
                    },
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.value\.meta\.dispatch_mode mismatch"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m")

    def test_validate_raw_east3_doc_allows_synthetic_node_without_source_span(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "meta": {"generated_by": "linked_optimizer"},
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "int64",
                        "source_span": {
                            "lineno": 1,
                            "end_lineno": 1,
                            "col_offset": 0,
                            "end_col_offset": 1,
                        },
                    },
                }
            ],
        }

        out = validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m")
        self.assertEqual(out["body"][0]["meta"]["generated_by"], "linked_optimizer")

    def test_validate_raw_east3_doc_rejects_invalid_generated_by_shape(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "meta": {"generated_by": 1},
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "int64",
                        "source_span": {
                            "lineno": 1,
                            "end_lineno": 1,
                            "col_offset": 0,
                            "end_col_offset": 1,
                        },
                    },
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, r"\$\.body\[0\]\.meta\.generated_by must be non-empty string"):
            validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m")

    def test_validate_raw_east3_doc_ignores_auxiliary_meta_and_kind_keys(self) -> None:
        span = {
            "lineno": 1,
            "end_lineno": 1,
            "col_offset": 0,
            "end_col_offset": 1,
        }
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "source_span": span,
                    "meta": {
                        "lifetime_analysis": {
                            "def_use": {
                                "defs": {
                                    "meta": ["n1"],
                                }
                            }
                        }
                    },
                    "arg_index": {"kind": 0},
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "int64",
                        "source_span": span,
                    },
                }
            ],
        }

        out = validate_raw_east3_doc(doc, expected_dispatch_mode="native", module_id="m", require_source_spans=True)
        self.assertEqual(out["body"][0]["meta"]["lifetime_analysis"]["def_use"]["defs"]["meta"], ["n1"])
        self.assertEqual(out["body"][0]["arg_index"]["kind"], 0)

    def test_load_east3_document_accepts_any_dict_items_fixture(self) -> None:
        doc = load_east3_document(
            ROOT / "test" / "fixtures" / "typing" / "any_dict_items.py",
            parser_backend="self_hosted",
            target_lang="rs",
        )
        self.assertEqual(doc.get("kind"), "Module")
        self.assertGreaterEqual(len(doc.get("body", [])), 1)

    def test_load_east3_document_accepts_sample18_mini_language_interpreter(self) -> None:
        doc = load_east3_document(
            ROOT / "sample" / "py" / "18_mini_language_interpreter.py",
            parser_backend="self_hosted",
            target_lang="cpp",
        )
        self.assertEqual(doc.get("kind"), "Module")
        self.assertGreaterEqual(len(doc.get("body", [])), 1)


if __name__ == "__main__":
    unittest.main()

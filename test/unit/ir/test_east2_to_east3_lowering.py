from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from _east23_lowering_test_support import _const_i
from _east23_lowering_test_support import East23LoweringNominalAdtFixtureMixin
from src.toolchain.compiler.east_parts.east2_to_east3_lowering import lower_east2_to_east3
from src.toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.frontends.type_expr import parse_type_expr_text
from src.toolchain.ir.east3 import load_east3_document as load_east3_stage


class East2ToEast3LoweringTest(East23LoweringNominalAdtFixtureMixin, unittest.TestCase):

    def _collect_runtime_iter_plans(self, node: object) -> list[dict[str, object]]:
        plans: list[dict[str, object]] = []
        if not isinstance(node, dict):
            return plans
        if node.get("kind") == "ForCore":
            iter_plan = node.get("iter_plan")
            if isinstance(iter_plan, dict) and iter_plan.get("kind") == "RuntimeIterForPlan":
                plans.append(iter_plan)
        for key in ("body", "orelse"):
            val = node.get(key)
            if isinstance(val, list):
                for child in val:
                    plans.extend(self._collect_runtime_iter_plans(child))
        return plans

    def test_schema_root_fields_are_present_after_lowering(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [],
        }
        out = lower_east2_to_east3(east2)
        self.assertEqual(out.get("kind"), "Module")
        self.assertEqual(out.get("east_stage"), 3)
        self.assertEqual(out.get("schema_version"), 1)
        self.assertIn(out.get("meta", {}).get("dispatch_mode"), {"native", "type_id"})
        self.assertIsInstance(out.get("body"), list)

    def test_schema_forcore_iter_plan_shape_static_and_runtime(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "target_type": "unknown",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "items"},
                    "body": [],
                    "orelse": [],
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
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertIsInstance(body, list)
        runtime_for = body[0]
        runtime_plan = runtime_for.get("iter_plan", {})
        self.assertEqual(runtime_for.get("kind"), "ForCore")
        self.assertEqual(runtime_plan.get("kind"), "RuntimeIterForPlan")
        self.assertIsInstance(runtime_plan.get("iter_expr"), dict)
        self.assertEqual(runtime_plan.get("init_op"), "ObjIterInit")
        self.assertEqual(runtime_plan.get("next_op"), "ObjIterNext")
        self.assertIn(runtime_plan.get("dispatch_mode"), {"native", "type_id"})
        static_for = body[1]
        static_plan = static_for.get("iter_plan", {})
        self.assertEqual(static_for.get("kind"), "ForCore")
        self.assertEqual(static_plan.get("kind"), "StaticRangeForPlan")
        self.assertIsInstance(static_plan.get("start"), dict)
        self.assertIsInstance(static_plan.get("stop"), dict)
        self.assertIsInstance(static_plan.get("step"), dict)

    def test_schema_dispatch_mode_is_consistent_between_root_and_runtime_iter_plan(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "body": [
                        {
                            "kind": "For",
                            "target": {"kind": "Name", "id": "x"},
                            "target_type": "unknown",
                            "iter_mode": "runtime_protocol",
                            "iter": {"kind": "Name", "id": "obj"},
                            "body": [],
                            "orelse": [],
                        }
                    ],
                }
            ],
        }
        out = lower_east2_to_east3(east2, object_dispatch_mode="type_id")
        root_mode = out.get("meta", {}).get("dispatch_mode")
        self.assertEqual(root_mode, "type_id")
        plans = self._collect_runtime_iter_plans(out)
        self.assertGreaterEqual(len(plans), 1)
        for plan in plans:
            self.assertEqual(plan.get("dispatch_mode"), root_mode)

    def test_lower_for_contract_coerces_iter_mode_to_runtime_protocol(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "target_type": "int64",
                    "iter_mode": "static_fastpath",
                    "iter": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("kind"), "ForCore")
        self.assertEqual(body[0].get("iter_mode"), "runtime_protocol")
        self.assertEqual(body[0].get("iter_plan", {}).get("kind"), "RuntimeIterForPlan")

    def test_lower_call_contract_keeps_non_any_builtin_call_unchanged(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {"kind": "Name", "id": "len"},
                        "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "len",
                        "runtime_call": "py_len",
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        value = body[0].get("value", {})
        self.assertEqual(value.get("kind"), "Call")
        self.assertEqual(value.get("runtime_call"), "py_len")

    def test_lower_assign_contract_keeps_same_side_non_any_assignment(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                    "annotation": "int64",
                    "decl_type": "int64",
                    "value": {"kind": "Name", "id": "j", "resolved_type": "int64"},
                    "declare": True,
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        value = body[0].get("value", {})
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "j")

    def test_lower_for_and_forrange_to_forcore(self) -> None:
        east2 = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "target_type": "int64",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "items"},
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                },
                {
                    "kind": "ForRange",
                    "target": {"kind": "Name", "id": "i"},
                    "target_type": "int64",
                    "start": _const_i(0),
                    "stop": {"kind": "Name", "id": "n"},
                    "step": _const_i(2),
                    "body": [],
                    "orelse": [],
                },
            ],
        }

        out = lower_east2_to_east3(east2)

        self.assertEqual(east2["body"][0]["kind"], "For")
        self.assertEqual(east2["body"][1]["kind"], "ForRange")

        self.assertEqual(out.get("kind"), "Module")
        self.assertEqual(out.get("east_stage"), 3)
        self.assertEqual(out.get("schema_version"), 1)
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")

        body = out.get("body", [])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        for_runtime = body[0]
        self.assertEqual(for_runtime.get("kind"), "ForCore")
        self.assertEqual(for_runtime.get("iter_mode"), "runtime_protocol")
        runtime_plan = for_runtime.get("iter_plan", {})
        self.assertEqual(runtime_plan.get("kind"), "RuntimeIterForPlan")
        self.assertEqual(runtime_plan.get("dispatch_mode"), "type_id")
        self.assertEqual(runtime_plan.get("init_op"), "ObjIterInit")
        self.assertEqual(runtime_plan.get("next_op"), "ObjIterNext")
        self.assertEqual(runtime_plan.get("iter_expr", {}).get("kind"), "Name")
        self.assertEqual(runtime_plan.get("iter_expr", {}).get("id"), "items")
        self.assertEqual(for_runtime.get("target_plan", {}).get("kind"), "NameTarget")
        self.assertEqual(for_runtime.get("target_plan", {}).get("id"), "x")

        for_range = body[1]
        self.assertEqual(for_range.get("kind"), "ForCore")
        self.assertEqual(for_range.get("iter_mode"), "static_fastpath")
        range_plan = for_range.get("iter_plan", {})
        self.assertEqual(range_plan.get("kind"), "StaticRangeForPlan")
        self.assertEqual(range_plan.get("start", {}).get("value"), 0)
        self.assertEqual(range_plan.get("step", {}).get("value"), 2)
        self.assertEqual(range_plan.get("stop", {}).get("kind"), "Name")
        self.assertEqual(range_plan.get("stop", {}).get("id"), "n")
        self.assertEqual(for_range.get("target_plan", {}).get("kind"), "NameTarget")
        self.assertEqual(for_range.get("target_plan", {}).get("id"), "i")

    def test_lower_for_tuple_target_propagates_tuple_element_target_types(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {
                        "kind": "Tuple",
                        "elements": [
                            {"kind": "Name", "id": "line_index"},
                            {"kind": "Name", "id": "source"},
                        ],
                    },
                    "target_type": "tuple[int64, str]",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "pairs", "resolved_type": "object"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        target_plan = out.get("body", [])[0].get("target_plan", {})
        self.assertEqual(target_plan.get("kind"), "TupleTarget")
        self.assertEqual(target_plan.get("target_type"), "tuple[int64, str]")
        elems = target_plan.get("elements", [])
        self.assertEqual(elems[0].get("target_type"), "int64")
        self.assertEqual(elems[1].get("target_type"), "str")

    def test_lower_for_tuple_target_uses_iter_element_type_when_target_type_unknown(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {
                        "kind": "Tuple",
                        "elements": [
                            {"kind": "Name", "id": "line_index"},
                            {"kind": "Name", "id": "source"},
                        ],
                    },
                    "target_type": "unknown",
                    "iter_element_type": "tuple[int64, str]",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "pairs", "resolved_type": "object"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        target_plan = out.get("body", [])[0].get("target_plan", {})
        elems = target_plan.get("elements", [])
        self.assertEqual(elems[0].get("target_type"), "int64")
        self.assertEqual(elems[1].get("target_type"), "str")

    def test_lower_nested_for_statements_inside_function(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "body": [
                        {
                            "kind": "For",
                            "target": {"kind": "Name", "id": "a"},
                            "target_type": "unknown",
                            "iter_mode": "static_fastpath",
                            "iter": {"kind": "Name", "id": "xs"},
                            "body": [
                                {
                                    "kind": "ForRange",
                                    "target": {"kind": "Name", "id": "i"},
                                    "target_type": "int64",
                                    "start": _const_i(0),
                                    "stop": _const_i(10),
                                    "step": _const_i(1),
                                    "body": [],
                                    "orelse": [],
                                }
                            ],
                            "orelse": [],
                        }
                    ],
                }
            ],
        }

        out = lower_east2_to_east3(east2)
        fn_body = out.get("body", [])[0].get("body", [])
        self.assertEqual(fn_body[0].get("kind"), "ForCore")
        self.assertEqual(fn_body[0].get("iter_mode"), "runtime_protocol")
        inner_body = fn_body[0].get("body", [])
        self.assertEqual(inner_body[0].get("kind"), "ForCore")
        self.assertEqual(inner_body[0].get("iter_mode"), "static_fastpath")

    def test_invalid_dispatch_mode_falls_back_to_native(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "unknown"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "v"},
                    "target_type": "unknown",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "obj"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "native")
        body = out.get("body", [])
        runtime_plan = body[0].get("iter_plan", {})
        self.assertEqual(runtime_plan.get("dispatch_mode"), "native")

    def test_load_east3_document_helper_lowers_from_json_input(self) -> None:
        payload = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "ForRange",
                    "target": {"kind": "Name", "id": "i"},
                    "target_type": "int64",
                    "start": _const_i(0),
                    "stop": _const_i(3),
                    "step": _const_i(1),
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "east.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east3_document(p)
        self.assertEqual(out.get("east_stage"), 3)
        body = out.get("body", [])
        self.assertEqual(body[0].get("kind"), "ForCore")
        self.assertEqual(body[0].get("iter_plan", {}).get("kind"), "StaticRangeForPlan")

    def test_load_east3_document_normalizes_existing_forcore_runtime_dispatch_mode(self) -> None:
        payload = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "ForCore",
                    "iter_mode": "runtime_protocol",
                    "iter_plan": {
                        "kind": "RuntimeIterForPlan",
                        "iter_expr": {"kind": "Name", "id": "xs", "resolved_type": "object"},
                        "dispatch_mode": "native",
                        "init_op": "ObjIterInit",
                        "next_op": "ObjIterNext",
                    },
                    "target_plan": {"kind": "NameTarget", "id": "x", "target_type": "object"},
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "east3.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east3_document(p, object_dispatch_mode="type_id")
        self.assertEqual(out.get("east_stage"), 3)
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")
        body = out.get("body", [])
        runtime_plan = body[0].get("iter_plan", {})
        self.assertEqual(runtime_plan.get("kind"), "RuntimeIterForPlan")
        self.assertEqual(runtime_plan.get("dispatch_mode"), "type_id")

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

    def test_load_east3_document_validates_lowered_doc_before_optimizer(self) -> None:
        bad_east3 = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
            "body": [1],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "main.py"
            p.write_text("", encoding="utf-8")
            with patch("src.toolchain.ir.east3.lower_east2_to_east3_document", return_value=bad_east3):
                with self.assertRaisesRegex(RuntimeError, r"raw EAST3\.body\[0\] must be an object: pkg\.main"):
                    load_east3_stage(
                        p,
                        load_east_document_fn=lambda *_args, **_kwargs: {"kind": "Module", "body": []},
                    )

    def test_load_east3_document_validates_optimized_doc_before_return(self) -> None:
        valid_east3 = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
            "body": [],
        }
        bad_optimized = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
            "body": [1],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "main.py"
            p.write_text("", encoding="utf-8")
            with patch("src.toolchain.ir.east3.lower_east2_to_east3_document", return_value=valid_east3):
                with patch("src.toolchain.ir.east3.optimize_east3_document", return_value=(bad_optimized, {"trace": []})):
                    with self.assertRaisesRegex(RuntimeError, r"raw EAST3\.body\[0\] must be an object: pkg\.main"):
                        load_east3_stage(
                            p,
                            load_east_document_fn=lambda *_args, **_kwargs: {"kind": "Module", "body": []},
                        )

    def test_lower_any_boundary_builtin_calls_to_obj_ops(self) -> None:
        any_name = {"kind": "Name", "id": "x", "resolved_type": "Any"}
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "bool"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "bool",
                        "runtime_call": "py_to_bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {"kind": "Name", "id": "len"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "len",
                        "runtime_call": "py_len",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "str",
                        "func": {"kind": "Name", "id": "str"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "str",
                        "runtime_call": "py_to_string",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "iter"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "py_iter_or_raise",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "next"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "runtime_call": "py_next_or_stop",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "ObjBool")
        self.assertEqual(body[1].get("value", {}).get("kind"), "ObjLen")
        self.assertEqual(body[2].get("value", {}).get("kind"), "ObjStr")
        self.assertEqual(body[3].get("value", {}).get("kind"), "ObjIterInit")
        self.assertEqual(body[4].get("value", {}).get("kind"), "ObjIterNext")

    def test_lower_any_boundary_builtin_calls_accepts_legacy_builtin_name_fallback(self) -> None:
        any_name = {"kind": "Name", "id": "x", "resolved_type": "Any"}
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "bool"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "bool",
                        "runtime_call": "static_cast",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "iter"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "ObjBool")
        self.assertEqual(body[1].get("value", {}).get("kind"), "ObjIterInit")

    def test_lower_any_boundary_legacy_builtin_fallback_can_be_disabled(self) -> None:
        any_name = {"kind": "Name", "id": "x", "resolved_type": "Any"}
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native", "legacy_compat_bridge": False},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "bool"},
                        "args": [any_name],
                        "keywords": [],
                        "lowered_kind": "BuiltinCall",
                        "builtin_name": "bool",
                        "runtime_call": "static_cast",
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "Call")

    def test_lower_any_boundary_builtin_calls_prefers_semantic_tag(self) -> None:
        any_name = {"kind": "Name", "id": "x", "resolved_type": "Any"}
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "wrapped_bool"},
                        "args": [any_name],
                        "keywords": [],
                        "runtime_call": "static_cast",
                        "semantic_tag": "cast.bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {"kind": "Name", "id": "wrapped_len"},
                        "args": [any_name],
                        "keywords": [],
                        "semantic_tag": "core.len",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "str",
                        "func": {"kind": "Name", "id": "wrapped_str"},
                        "args": [any_name],
                        "keywords": [],
                        "semantic_tag": "cast.str",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "wrapped_iter"},
                        "args": [any_name],
                        "keywords": [],
                        "semantic_tag": "iter.init",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "wrapped_next"},
                        "args": [any_name],
                        "keywords": [],
                        "semantic_tag": "iter.next",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "ObjBool")
        self.assertEqual(body[1].get("value", {}).get("kind"), "ObjLen")
        self.assertEqual(body[2].get("value", {}).get("kind"), "ObjStr")
        self.assertEqual(body[3].get("value", {}).get("kind"), "ObjIterInit")
        self.assertEqual(body[4].get("value", {}).get("kind"), "ObjIterNext")

    def test_lower_any_boundary_does_not_reinterpret_plain_call_by_name(self) -> None:
        any_name = {"kind": "Name", "id": "x", "resolved_type": "Any"}
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "object",
                        "func": {"kind": "Name", "id": "iter"},
                        "args": [any_name],
                        "keywords": [],
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "Call")

    def test_lower_isinstance_and_issubclass_to_type_id_core_nodes(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "isinstance"},
                        "args": [
                            {"kind": "Name", "id": "x", "resolved_type": "object"},
                            {"kind": "Name", "id": "int", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "isinstance"},
                        "args": [
                            {"kind": "Name", "id": "x", "resolved_type": "object"},
                            {
                                "kind": "Tuple",
                                "resolved_type": "tuple[unknown,unknown,unknown]",
                                "elements": [
                                    {"kind": "Name", "id": "int", "resolved_type": "unknown"},
                                    {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
                                    {"kind": "Name", "id": "dict", "resolved_type": "unknown"},
                                ],
                            },
                        ],
                        "keywords": [],
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "issubclass"},
                        "args": [
                            {"kind": "Name", "id": "Child", "resolved_type": "unknown"},
                            {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        first = body[0].get("value", {})
        self.assertEqual(first.get("kind"), "IsInstance")
        self.assertEqual(first.get("expected_type_id", {}).get("kind"), "Name")
        self.assertEqual(first.get("expected_type_id", {}).get("id"), "PYTRA_TID_INT")
        second = body[1].get("value", {})
        self.assertEqual(second.get("kind"), "BoolOp")
        self.assertEqual(second.get("op"), "Or")
        second_values = second.get("values", [])
        self.assertEqual(second_values[0].get("kind"), "IsInstance")
        self.assertEqual(second_values[0].get("expected_type_id", {}).get("id"), "PYTRA_TID_INT")
        self.assertEqual(second_values[1].get("expected_type_id", {}).get("kind"), "Name")
        self.assertEqual(second_values[1].get("expected_type_id", {}).get("id"), "Base")
        self.assertEqual(second_values[2].get("expected_type_id", {}).get("id"), "PYTRA_TID_DICT")
        third = body[2].get("value", {})
        self.assertEqual(third.get("kind"), "IsSubclass")
        self.assertEqual(third.get("actual_type_id", {}).get("kind"), "Name")
        self.assertEqual(third.get("actual_type_id", {}).get("id"), "Child")
        self.assertEqual(third.get("expected_type_id", {}).get("kind"), "Name")
        self.assertEqual(third.get("expected_type_id", {}).get("id"), "Base")

    def test_lower_type_predicate_calls_accept_semantic_tag(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "wrapped_isinstance"},
                        "args": [
                            {"kind": "Name", "id": "x", "resolved_type": "object"},
                            {"kind": "Name", "id": "int", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                        "semantic_tag": "type.isinstance",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "wrapped_issubclass"},
                        "args": [
                            {"kind": "Name", "id": "Child", "resolved_type": "unknown"},
                            {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                        "semantic_tag": "type.issubclass",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "IsInstance")
        self.assertEqual(body[1].get("value", {}).get("kind"), "IsSubclass")

    def test_lower_type_predicate_calls_accept_type_predicate_call_kind(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "wrapped_type_check"},
                        "args": [
                            {"kind": "Name", "id": "x", "resolved_type": "object"},
                            {"kind": "Name", "id": "int", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                        "lowered_kind": "TypePredicateCall",
                        "builtin_name": "isinstance",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "wrapped_type_check2"},
                        "args": [
                            {"kind": "Name", "id": "Child", "resolved_type": "unknown"},
                            {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                        "lowered_kind": "TypePredicateCall",
                        "builtin_name": "issubclass",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "IsInstance")
        self.assertEqual(body[1].get("value", {}).get("kind"), "IsSubclass")

    def test_lower_type_predicate_legacy_name_fallback_can_be_disabled(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id", "legacy_compat_bridge": False},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "isinstance"},
                        "args": [
                            {"kind": "Name", "id": "x", "resolved_type": "object"},
                            {"kind": "Name", "id": "int", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "Call")

    def test_lower_runtime_type_id_and_subtype_calls_to_core_nodes(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {"kind": "Name", "id": "py_runtime_type_id"},
                        "args": [{"kind": "Name", "id": "x", "resolved_type": "object"}],
                        "keywords": [],
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "py_is_subtype"},
                        "args": [
                            {"kind": "Name", "id": "a_tid", "resolved_type": "int64"},
                            {"kind": "Name", "id": "e_tid", "resolved_type": "int64"},
                        ],
                        "keywords": [],
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "py_issubclass"},
                        "args": [
                            {"kind": "Name", "id": "a_tid", "resolved_type": "int64"},
                            {"kind": "Name", "id": "e_tid", "resolved_type": "int64"},
                        ],
                        "keywords": [],
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        self.assertEqual(body[0].get("value", {}).get("kind"), "ObjTypeId")
        self.assertEqual(body[1].get("value", {}).get("kind"), "IsSubtype")
        self.assertEqual(body[2].get("value", {}).get("kind"), "IsSubclass")

    def test_lower_assign_inserts_box_and_unbox_for_any_boundary(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {
                        "kind": "Name",
                        "id": "obj",
                        "resolved_type": "object",
                        "type_expr": parse_type_expr_text("object"),
                    },
                    "annotation": "object",
                    "annotation_type_expr": parse_type_expr_text("object"),
                    "decl_type": "object",
                    "decl_type_expr": parse_type_expr_text("object"),
                    "value": _const_i(1),
                    "declare": True,
                },
                {
                    "kind": "AnnAssign",
                    "target": {
                        "kind": "Name",
                        "id": "i",
                        "resolved_type": "JsonValue | None",
                        "type_expr": parse_type_expr_text("JsonValue | None"),
                    },
                    "annotation": "JsonValue | None",
                    "annotation_type_expr": parse_type_expr_text("JsonValue | None"),
                    "decl_type": "JsonValue | None",
                    "decl_type_expr": parse_type_expr_text("JsonValue | None"),
                    "value": {
                        "kind": "Name",
                        "id": "obj",
                        "resolved_type": "Any",
                        "type_expr": parse_type_expr_text("Any"),
                    },
                    "declare": True,
                },
                {
                    "kind": "AnnAssign",
                    "target": {
                        "kind": "Name",
                        "id": "obj2",
                        "resolved_type": "object",
                        "type_expr": parse_type_expr_text("object"),
                    },
                    "annotation": "object",
                    "annotation_type_expr": parse_type_expr_text("object"),
                    "decl_type": "object",
                    "decl_type_expr": parse_type_expr_text("object"),
                    "value": {
                        "kind": "Name",
                        "id": "payload",
                        "resolved_type": "JsonValue | None",
                        "type_expr": parse_type_expr_text("JsonValue | None"),
                    },
                    "declare": True,
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        first_value = body[0].get("value", {})
        second_value = body[1].get("value", {})
        third_value = body[2].get("value", {})
        self.assertEqual(first_value.get("kind"), "Box")
        self.assertEqual(first_value.get("resolved_type"), "object")
        self.assertEqual(first_value.get("bridge_lane_v1", {}).get("target_category"), "dynamic")
        self.assertEqual(first_value.get("bridge_lane_v1", {}).get("value_category"), "static")
        self.assertEqual(second_value.get("kind"), "Unbox")
        self.assertEqual(second_value.get("target"), "JsonValue | None")
        self.assertEqual(second_value.get("on_fail"), "raise")
        self.assertEqual(second_value.get("type_expr_summary_v1", {}).get("category"), "optional")
        self.assertEqual(second_value.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "json")
        self.assertEqual(second_value.get("bridge_lane_v1", {}).get("target", {}).get("category"), "optional")
        self.assertEqual(third_value.get("kind"), "Box")
        self.assertEqual(third_value.get("bridge_lane_v1", {}).get("value", {}).get("category"), "optional")
        self.assertEqual(third_value.get("bridge_lane_v1", {}).get("value", {}).get("nominal_adt_family"), "json")

    def test_lower_isinstance_records_narrowing_lane_for_optional_nominal_type(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "type_id"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool",
                        "func": {"kind": "Name", "id": "isinstance"},
                        "args": [
                            {
                                "kind": "Name",
                                "id": "payload",
                                "resolved_type": "JsonValue | None",
                                "type_expr": parse_type_expr_text("JsonValue | None"),
                            },
                            {"kind": "Name", "id": "JsonObj", "resolved_type": "unknown"},
                        ],
                        "keywords": [],
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("kind"), "IsInstance")
        self.assertEqual(value.get("type_expr_summary_v1", {}).get("category"), "optional")
        self.assertEqual(value.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "json")
        self.assertEqual(value.get("narrowing_lane_v1", {}).get("source_category"), "optional")

    def test_lower_user_nominal_adt_isinstance_attaches_variant_test_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        test_expr = fn.get("body", [])[0].get("test", {})
        self.assertEqual(test_expr.get("kind"), "IsInstance")
        self.assertEqual(test_expr.get("type_expr_summary_v1", {}).get("category"), "nominal_adt")
        self.assertEqual(test_expr.get("type_expr_summary_v1", {}).get("nominal_adt_name"), "Maybe")
        self.assertEqual(test_expr.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "Maybe")
        self.assertEqual(test_expr.get("narrowing_lane_v1", {}).get("source_category"), "nominal_adt")
        self.assertEqual(test_expr.get("narrowing_lane_v1", {}).get("predicate_category"), "nominal_adt")
        self.assertEqual(test_expr.get("narrowing_lane_v1", {}).get("variant_name"), "Just")
        self.assertEqual(test_expr.get("nominal_adt_test_v1", {}).get("predicate_kind"), "variant")
        self.assertEqual(test_expr.get("nominal_adt_test_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(test_expr.get("nominal_adt_test_v1", {}).get("variant_name"), "Just")

    def test_lower_user_nominal_adt_isinstance_attaches_family_test_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        east2["body"][3]["body"].insert(
            0,
            {
                "kind": "Expr",
                "value": {
                    "kind": "Call",
                    "resolved_type": "bool",
                    "func": {"kind": "Name", "id": "isinstance"},
                    "args": [
                        {
                            "kind": "Name",
                            "id": "x",
                            "resolved_type": "Maybe",
                            "type_expr": parse_type_expr_text("Maybe"),
                        },
                        {"kind": "Name", "id": "Maybe", "resolved_type": "unknown"},
                    ],
                    "keywords": [],
                },
            },
        )
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        family_check = fn.get("body", [])[0].get("value", {})
        self.assertEqual(family_check.get("kind"), "IsInstance")
        self.assertEqual(family_check.get("type_expr_summary_v1", {}).get("category"), "nominal_adt")
        self.assertEqual(family_check.get("type_expr_summary_v1", {}).get("nominal_adt_name"), "Maybe")
        self.assertEqual(family_check.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "Maybe")
        self.assertEqual(family_check.get("nominal_adt_test_v1", {}).get("predicate_kind"), "family")
        self.assertEqual(family_check.get("nominal_adt_test_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(family_check.get("narrowing_lane_v1", {}).get("source_category"), "nominal_adt")
        self.assertEqual(family_check.get("narrowing_lane_v1", {}).get("predicate_category"), "nominal_adt")
        self.assertEqual(family_check.get("narrowing_lane_v1", {}).get("predicate_kind"), "family")

    def test_lower_user_nominal_adt_constructor_attaches_ctor_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        ctor_call = fn.get("body", [])[1].get("value", {})
        self.assertEqual(ctor_call.get("kind"), "Call")
        self.assertEqual(ctor_call.get("lowered_kind"), "NominalAdtCtorCall")
        self.assertEqual(ctor_call.get("semantic_tag"), "nominal_adt.variant_ctor")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("ir_category"), "NominalAdtCtorCall")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("variant_name"), "Just")
        self.assertEqual(ctor_call.get("nominal_adt_ctor_v1", {}).get("payload_style"), "dataclass")
        self.assertEqual(ctor_call.get("type_expr_summary_v1", {}).get("category"), "nominal_adt")
        self.assertEqual(ctor_call.get("type_expr_summary_v1", {}).get("nominal_adt_name"), "Just")
        self.assertEqual(ctor_call.get("type_expr_summary_v1", {}).get("nominal_adt_family"), "Maybe")

    def test_lower_user_nominal_adt_projection_attaches_projection_metadata(self) -> None:
        east2 = self.representative_nominal_adt_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        projection = fn.get("body", [])[2].get("value", {})
        self.assertEqual(projection.get("kind"), "Attribute")
        self.assertEqual(projection.get("lowered_kind"), "NominalAdtProjection")
        self.assertEqual(projection.get("semantic_tag"), "nominal_adt.variant_projection")
        self.assertEqual(projection.get("resolved_type"), "int64")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("ir_category"), "NominalAdtProjection")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("family_name"), "Maybe")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("variant_name"), "Just")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("field_name"), "value")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("field_type"), "int64")
        self.assertEqual(projection.get("nominal_adt_projection_v1", {}).get("payload_style"), "dataclass")
        self.assertEqual(projection.get("type_expr_summary_v1", {}).get("mirror"), "int64")

    def test_lower_user_nominal_adt_match_attaches_match_metadata(self) -> None:
        east2 = self.representative_nominal_adt_match_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        match_stmt = fn.get("body", [])[0]
        self.assertEqual(match_stmt.get("kind"), "Match")
        self.assertEqual(match_stmt.get("lowered_kind"), "NominalAdtMatch")
        self.assertEqual(match_stmt.get("semantic_tag"), "nominal_adt.match")
        match_meta = match_stmt.get("nominal_adt_match_v1", {})
        self.assertEqual(match_meta.get("ir_category"), "NominalAdtMatch")
        self.assertEqual(match_meta.get("family_name"), "Maybe")
        self.assertEqual(match_meta.get("coverage_kind"), "exhaustive")
        self.assertEqual(match_meta.get("covered_variants"), ["Just", "Nothing"])
        self.assertEqual(match_meta.get("subject_type", {}).get("category"), "nominal_adt")
        self.assertEqual(match_meta.get("subject_type", {}).get("nominal_adt_name"), "Maybe")
        self.assertEqual(match_meta.get("subject_type", {}).get("nominal_adt_family"), "Maybe")

        first_case = match_stmt.get("cases", [])[0]
        first_pattern = first_case.get("pattern", {})
        self.assertEqual(first_pattern.get("kind"), "VariantPattern")
        self.assertEqual(first_pattern.get("lowered_kind"), "NominalAdtVariantPattern")
        self.assertEqual(first_pattern.get("semantic_tag"), "nominal_adt.variant_pattern")
        first_pattern_meta = first_pattern.get("nominal_adt_pattern_v1", {})
        self.assertEqual(first_pattern_meta.get("ir_category"), "NominalAdtVariantPattern")
        self.assertEqual(first_pattern_meta.get("family_name"), "Maybe")
        self.assertEqual(first_pattern_meta.get("variant_name"), "Just")
        self.assertEqual(first_pattern_meta.get("payload_style"), "dataclass")
        self.assertEqual(first_pattern_meta.get("bind_names"), ["value"])

        first_bind = first_pattern.get("subpatterns", [])[0]
        self.assertEqual(first_bind.get("kind"), "PatternBind")
        self.assertEqual(first_bind.get("lowered_kind"), "NominalAdtPatternBind")
        self.assertEqual(first_bind.get("semantic_tag"), "nominal_adt.pattern_bind")
        self.assertEqual(first_bind.get("nominal_adt_pattern_bind_v1", {}).get("field_name"), "value")
        self.assertEqual(first_bind.get("nominal_adt_pattern_bind_v1", {}).get("field_type"), "int64")
        self.assertEqual(first_bind.get("type_expr_summary_v1", {}).get("mirror"), "int64")

        second_pattern = match_stmt.get("cases", [])[1].get("pattern", {})
        self.assertEqual(second_pattern.get("lowered_kind"), "NominalAdtVariantPattern")
        self.assertEqual(second_pattern.get("nominal_adt_pattern_v1", {}).get("variant_name"), "Nothing")

    def test_lower_user_nominal_adt_match_attaches_analysis_metadata(self) -> None:
        east2 = self.representative_nominal_adt_match_east2()
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        match_stmt = fn.get("body", [])[0]
        self.assertEqual(match_stmt.get("kind"), "Match")
        analysis = match_stmt.get("meta", {}).get("match_analysis_v1", {})
        self.assertEqual(analysis.get("family_name"), "Maybe")
        self.assertEqual(analysis.get("coverage_kind"), "exhaustive")
        self.assertEqual(analysis.get("covered_variants"), ["Just", "Nothing"])
        self.assertEqual(analysis.get("uncovered_variants"), [])
        self.assertEqual(analysis.get("duplicate_case_indexes"), [])
        self.assertEqual(analysis.get("unreachable_case_indexes"), [])
        first_case = match_stmt.get("cases", [])[0]
        first_pattern = first_case.get("pattern", {})
        self.assertEqual(first_pattern.get("kind"), "VariantPattern")
        self.assertEqual(first_pattern.get("family_name"), "Maybe")
        self.assertEqual(first_pattern.get("variant_name"), "Just")
        self.assertEqual(first_pattern.get("subpatterns", [])[0].get("kind"), "PatternBind")
        self.assertEqual(first_pattern.get("subpatterns", [])[0].get("name"), "value")

    def test_lower_user_nominal_adt_match_marks_duplicate_variant_invalid(self) -> None:
        east2 = self.representative_nominal_adt_match_east2()
        match_stmt = east2["body"][3]["body"][0]
        match_stmt["cases"].insert(
            1,
            {
                "kind": "MatchCase",
                "pattern": {
                    "kind": "VariantPattern",
                    "family_name": "Maybe",
                    "variant_name": "Just",
                    "subpatterns": [{"kind": "PatternBind", "name": "other"}],
                },
                "guard": None,
                "body": [{"kind": "Return", "value": _const_i(2)}],
            },
        )
        out = lower_east2_to_east3(east2)
        fn = out.get("body", [])[3]
        analysis = fn.get("body", [])[0].get("meta", {}).get("match_analysis_v1", {})
        self.assertEqual(analysis.get("coverage_kind"), "invalid")
        self.assertEqual(analysis.get("covered_variants"), ["Just", "Nothing"])
        self.assertEqual(analysis.get("duplicate_case_indexes"), [1])
        self.assertEqual(analysis.get("unreachable_case_indexes"), [1])

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
        json_call = json_out.get("body", [])[0].get("value", {})
        receiver_type = json_call.get("json_decode_v1", {}).get("receiver_type", {})
        self.assertEqual(receiver_type.get("category"), "nominal_adt")
        self.assertEqual(receiver_type.get("nominal_adt_family"), "json")
        self.assertEqual(json_call.get("json_decode_v1", {}).get("receiver_category"), "nominal_adt")
        self.assertEqual(receiver_type.get("category"), user_subject_type.get("category"))

    def test_lower_json_value_helper_call_attaches_decode_metadata(self) -> None:
        east2 = {
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
        out = lower_east2_to_east3(east2)
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("kind"), "Call")
        self.assertEqual(value.get("lowered_kind"), "JsonDecodeCall")
        self.assertEqual(value.get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(value.get("json_decode_receiver", {}).get("id"), "payload")
        self.assertEqual(value.get("json_decode_v1", {}).get("decode_kind"), "narrow")
        self.assertEqual(value.get("json_decode_v1", {}).get("ir_category"), "JsonDecodeCall")
        self.assertEqual(value.get("json_decode_v1", {}).get("decode_entry"), "json.value.as_obj")
        self.assertEqual(value.get("json_decode_v1", {}).get("contract_source"), "type_expr")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonValue")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_category"), "nominal_adt")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_nominal_adt_family"), "json")

    def test_lower_json_value_helper_call_prefers_type_expr_over_runtime_mirror(self) -> None:
        east2 = {
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
                                "resolved_type": "unknown",
                                "type_expr": parse_type_expr_text("JsonValue"),
                            },
                        },
                        "args": [],
                        "keywords": [],
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(value.get("lowered_kind"), "JsonDecodeCall")
        self.assertEqual(value.get("json_decode_v1", {}).get("contract_source"), "type_expr")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonValue")
        self.assertEqual(value.get("json_decode_v1", {}).get("receiver_nominal_adt_family"), "json")

    def test_lower_assign_reads_structured_dynamic_union_for_boundary_bridge(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "slot", "resolved_type": "unknown"},
                    "annotation": "unknown",
                    "decl_type": "unknown",
                    "decl_type_expr": {
                        "kind": "UnionType",
                        "union_mode": "dynamic",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "DynamicType", "name": "Any"},
                        ],
                    },
                    "value": _const_i(1),
                    "declare": True,
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        stmt = out.get("body", [])[0]
        value = stmt.get("value", {})
        self.assertEqual(value.get("kind"), "Box")
        summary = value.get("type_expr_summary_v1", {})
        self.assertEqual(summary.get("category"), "dynamic_union")
        self.assertEqual(value.get("bridge_lane_v1", {}).get("target_category"), "dynamic_union")

    def test_lower_json_decode_calls_attach_nominal_metadata(self) -> None:
        json_value = {
            "kind": "Name",
            "id": "value",
            "resolved_type": "JsonValue",
            "type_expr": parse_type_expr_text("JsonValue"),
        }
        json_obj = {"kind": "Name", "id": "obj", "resolved_type": "JsonObj"}
        json_arr = {"kind": "Name", "id": "arr", "resolved_type": "JsonArr"}
        east2 = {
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
                            "value": json_value,
                            "attr": "as_obj",
                            "resolved_type": "unknown",
                        },
                        "args": [],
                        "keywords": [],
                        "semantic_tag": "json.value.as_obj",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64 | None",
                        "func": {
                            "kind": "Attribute",
                            "value": json_obj,
                            "attr": "get_int",
                            "resolved_type": "unknown",
                        },
                        "args": [{"kind": "Constant", "value": "age", "resolved_type": "str"}],
                        "keywords": [],
                        "semantic_tag": "json.obj.get_int",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "bool | None",
                        "func": {
                            "kind": "Attribute",
                            "value": json_arr,
                            "attr": "get_bool",
                            "resolved_type": "unknown",
                        },
                        "args": [{"kind": "Constant", "value": 0, "resolved_type": "int64"}],
                        "keywords": [],
                        "semantic_tag": "json.arr.get_bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "JsonObj | None",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "json", "resolved_type": "unknown"},
                            "attr": "loads_obj",
                            "resolved_type": "unknown",
                        },
                        "args": [{"kind": "Name", "id": "text", "resolved_type": "str"}],
                        "keywords": [],
                        "runtime_module_id": "pytra.std.json",
                        "runtime_symbol": "loads_obj",
                    },
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        first = body[0].get("value", {})
        second = body[1].get("value", {})
        third = body[2].get("value", {})
        fourth = body[3].get("value", {})
        self.assertEqual(first.get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(first.get("json_decode_v1", {}).get("decode_kind"), "narrow")
        self.assertEqual(first.get("json_decode_v1", {}).get("contract_source"), "type_expr")
        self.assertEqual(first.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonValue")
        self.assertEqual(first.get("json_decode_v1", {}).get("receiver_nominal_adt_family"), "json")
        self.assertEqual(first.get("type_expr_summary_v1", {}).get("category"), "optional")
        self.assertEqual(second.get("semantic_tag"), "json.obj.get_int")
        self.assertEqual(second.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonObj")
        self.assertEqual(second.get("json_decode_v1", {}).get("receiver_nominal_adt_family"), "json")
        self.assertEqual(third.get("semantic_tag"), "json.arr.get_bool")
        self.assertEqual(third.get("json_decode_v1", {}).get("receiver_nominal_adt_name"), "JsonArr")
        self.assertEqual(third.get("json_decode_v1", {}).get("receiver_nominal_adt_family"), "json")
        self.assertEqual(fourth.get("semantic_tag"), "json.loads_obj")
        self.assertEqual(fourth.get("json_decode_v1", {}).get("decode_kind"), "module_load")
        self.assertEqual(fourth.get("type_expr_summary_v1", {}).get("category"), "optional")

    def test_representative_json_decode_uses_resolved_type_compat_when_type_expr_missing(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "JsonObj | None",
                        "func": {
                            "kind": "Attribute",
                            "attr": "as_obj",
                            "value": {"kind": "Name", "id": "payload", "resolved_type": "JsonValue"},
                        },
                        "args": [],
                        "keywords": [],
                        "semantic_tag": "json.value.as_obj",
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        value = out.get("body", [])[0].get("value", {})
        self.assertEqual(value.get("lowered_kind"), "JsonDecodeCall")
        self.assertEqual(value.get("json_decode_v1", {}).get("contract_source"), "resolved_type_compat")

    def test_json_semantic_tag_contract_rejects_non_jsonvalue_receiver(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "JsonObj | None",
                        "type_expr": parse_type_expr_text("JsonObj | None"),
                        "semantic_tag": "json.value.as_obj",
                        "func": {
                            "kind": "Attribute",
                            "attr": "as_obj",
                            "value": {
                                "kind": "Name",
                                "id": "payload",
                                "resolved_type": "JsonObj",
                                "type_expr": parse_type_expr_text("JsonObj"),
                            },
                        },
                        "args": [],
                        "keywords": [],
                    },
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "json_decode_contract_violation: json.value.as_obj requires JsonValue nominal receiver TypeExpr",
        ):
            lower_east2_to_east3(east2)

    def test_dispatch_mode_override_is_applied_at_lower_entrypoint(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "target_type": "unknown",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "obj", "resolved_type": "Any"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        out = lower_east2_to_east3(east2, object_dispatch_mode="type_id")
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")
        body = out.get("body", [])
        iter_plan = body[0].get("iter_plan", {})
        self.assertEqual(iter_plan.get("dispatch_mode"), "type_id")

    def test_lower_fixed_tuple_starred_call_arg_to_positional_subscripts(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {
                            "kind": "Name",
                            "id": "mix_rgb",
                            "resolved_type": "Callable[[int64,int64,int64],int64]",
                        },
                        "args": [
                            {
                                "kind": "Starred",
                                "resolved_type": "tuple[int64,int64,int64]",
                                "value": {
                                    "kind": "Name",
                                    "id": "rgb",
                                    "resolved_type": "tuple[int64,int64,int64]",
                                },
                            }
                        ],
                        "keywords": [],
                    },
                }
            ],
        }
        out = lower_east2_to_east3(east2)
        call = out.get("body", [])[0].get("value", {})
        args = call.get("args", [])
        self.assertEqual(len(args), 3)
        for idx, arg in enumerate(args):
            self.assertEqual(arg.get("kind"), "Subscript")
            self.assertEqual(arg.get("value", {}).get("kind"), "Name")
            self.assertEqual(arg.get("value", {}).get("id"), "rgb")
            self.assertEqual(arg.get("slice", {}).get("kind"), "Constant")
            self.assertEqual(arg.get("slice", {}).get("value"), idx)
            self.assertEqual(arg.get("resolved_type"), "int64")

    def test_lower_starred_call_rejects_non_tuple_receiver(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "resolved_type": "int64",
                        "func": {
                            "kind": "Name",
                            "id": "mix_rgb",
                            "resolved_type": "Callable[[int64,int64,int64],int64]",
                        },
                        "args": [
                            {
                                "kind": "Starred",
                                "resolved_type": "list[int64]",
                                "value": {
                                    "kind": "Name",
                                    "id": "rgb",
                                    "resolved_type": "list[int64]",
                                },
                            }
                        ],
                        "keywords": [],
                    },
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "starred_call_contract_violation: call starred unpack requires fixed tuple receiver TypeExpr",
        ):
            lower_east2_to_east3(east2)

    def test_load_east3_document_helper_accepts_dispatch_override(self) -> None:
        payload = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "target_type": "unknown",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "obj", "resolved_type": "Any"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "east.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east3_document(p, object_dispatch_mode="type_id")
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")
        body = out.get("body", [])
        iter_plan = body[0].get("iter_plan", {})
        self.assertEqual(iter_plan.get("dispatch_mode"), "type_id")

    def test_noncpp_east3_contract_script_passes_static_mode(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_noncpp_east3_contract.py", "--skip-transpile"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"{cp.stdout}\n{cp.stderr}")
        self.assertIn("static contract checks passed", cp.stdout)

    def test_jsonvalue_typeexpr_contract_script_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_jsonvalue_typeexpr_contract.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"{cp.stdout}\n{cp.stderr}")
        self.assertIn("jsonvalue TypeExpr contract guard passed", cp.stdout)


if __name__ == "__main__":
    unittest.main()

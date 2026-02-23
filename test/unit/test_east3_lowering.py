from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.east_parts.east3_lowering import lower_east2_to_east3
from src.pytra.compiler.transpile_cli import load_east3_document


def _const_i(v: int) -> dict[str, object]:
    return {"kind": "Constant", "value": v, "resolved_type": "int64"}


class East3LoweringTest(unittest.TestCase):
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
                        "runtime_call": "static_cast",
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

    def test_lower_assign_inserts_box_and_unbox_for_any_boundary(self) -> None:
        east2 = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "obj", "resolved_type": "object"},
                    "annotation": "object",
                    "decl_type": "object",
                    "value": _const_i(1),
                    "declare": True,
                },
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                    "annotation": "int64",
                    "decl_type": "int64",
                    "value": {"kind": "Name", "id": "obj", "resolved_type": "Any"},
                    "declare": True,
                },
            ],
        }
        out = lower_east2_to_east3(east2)
        body = out.get("body", [])
        first_value = body[0].get("value", {})
        second_value = body[1].get("value", {})
        self.assertEqual(first_value.get("kind"), "Box")
        self.assertEqual(first_value.get("resolved_type"), "object")
        self.assertEqual(second_value.get("kind"), "Unbox")
        self.assertEqual(second_value.get("target"), "int64")
        self.assertEqual(second_value.get("on_fail"), "raise")

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


if __name__ == "__main__":
    unittest.main()

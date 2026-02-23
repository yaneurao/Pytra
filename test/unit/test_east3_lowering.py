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


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hooks.cpp.emitter.cpp_emitter import emit_cpp_from_east
from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult
from hooks.cpp.optimizer.cpp_optimizer import CppPassManager
from hooks.cpp.optimizer.cpp_optimizer import optimize_cpp_ir
from hooks.cpp.optimizer.cpp_optimizer import parse_cpp_opt_pass_overrides
from hooks.cpp.optimizer.cpp_optimizer import resolve_cpp_opt_level
from hooks.cpp.optimizer.passes.const_condition_pass import CppConstConditionPass
from hooks.cpp.optimizer.passes.dead_temp_pass import CppDeadTempPass
from hooks.cpp.optimizer.passes.noop_cast_pass import CppNoOpCastPass
from hooks.cpp.optimizer.passes.range_for_shape_pass import CppRangeForShapePass
from hooks.cpp.optimizer.passes.runtime_fastpath_pass import CppRuntimeFastPathPass
from hooks.cpp.optimizer.trace import render_cpp_opt_trace


def _module_doc() -> dict[str, object]:
    return {"kind": "Module", "meta": {}, "body": []}


class _TouchPass(CppOptimizerPass):
    name = "TouchPass"
    min_opt_level = 1

    def run(self, cpp_ir: dict[str, object], context: CppOptContext) -> CppOptResult:
        _ = context
        meta_any = cpp_ir.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        meta["touch"] = "ok"
        cpp_ir["meta"] = meta
        return CppOptResult(changed=True, change_count=1)


class CppOptimizerTest(unittest.TestCase):
    def test_resolve_cpp_opt_level(self) -> None:
        self.assertEqual(resolve_cpp_opt_level(""), 1)
        self.assertEqual(resolve_cpp_opt_level("0"), 0)
        self.assertEqual(resolve_cpp_opt_level("1"), 1)
        self.assertEqual(resolve_cpp_opt_level("2"), 2)
        self.assertEqual(resolve_cpp_opt_level(2), 2)
        with self.assertRaisesRegex(ValueError, "invalid --cpp-opt-level"):
            resolve_cpp_opt_level("3")

    def test_parse_cpp_opt_pass_overrides(self) -> None:
        enabled, disabled = parse_cpp_opt_pass_overrides("+A,-B,+C")
        self.assertEqual(enabled, {"A", "C"})
        self.assertEqual(disabled, {"B"})
        with self.assertRaisesRegex(ValueError, "invalid --cpp-opt-pass token"):
            parse_cpp_opt_pass_overrides("A")

    def test_pass_manager_runs_and_collects_trace(self) -> None:
        doc = _module_doc()
        manager = CppPassManager([_TouchPass()])
        context = CppOptContext(opt_level=1)
        report = manager.run(doc, context)
        self.assertTrue(bool(report.get("changed")))
        self.assertEqual(int(report.get("change_count", 0)), 1)
        self.assertEqual(doc.get("meta", {}).get("touch"), "ok")
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "TouchPass")
        self.assertTrue(bool(trace[0].get("enabled")))

    def test_optimize_cpp_ir_can_disable_default_pass(self) -> None:
        doc = _module_doc()
        out_doc, report = optimize_cpp_ir(
            doc,
            opt_level="1",
            opt_pass_spec="-CppNoOpPass,-CppDeadTempPass,-CppNoOpCastPass,-CppConstConditionPass,-CppRangeForShapePass,-CppRuntimeFastPathPass",
        )
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "CppNoOpPass")
        self.assertFalse(bool(trace[0].get("enabled")))
        self.assertEqual(trace[1].get("name"), "CppDeadTempPass")
        self.assertFalse(bool(trace[1].get("enabled")))
        self.assertEqual(trace[2].get("name"), "CppNoOpCastPass")
        self.assertFalse(bool(trace[2].get("enabled")))
        self.assertEqual(trace[3].get("name"), "CppConstConditionPass")
        self.assertFalse(bool(trace[3].get("enabled")))
        self.assertEqual(trace[4].get("name"), "CppRangeForShapePass")
        self.assertFalse(bool(trace[4].get("enabled")))
        self.assertEqual(trace[5].get("name"), "CppRuntimeFastPathPass")
        self.assertFalse(bool(trace[5].get("enabled")))
        trace_text = render_cpp_opt_trace(report)
        self.assertIn("CppNoOpPass enabled=false", trace_text)
        self.assertIn("CppDeadTempPass enabled=false", trace_text)
        self.assertIn("CppNoOpCastPass enabled=false", trace_text)
        self.assertIn("CppConstConditionPass enabled=false", trace_text)
        self.assertIn("CppRangeForShapePass enabled=false", trace_text)
        self.assertIn("CppRuntimeFastPathPass enabled=false", trace_text)

    def test_cpp_noop_cast_pass_removes_noop_cast_entries(self) -> None:
        doc = _module_doc()
        expr = {
            "kind": "Name",
            "id": "x",
            "resolved_type": "int64",
            "casts": [
                {"on": "self", "from": "int64", "to": "int64"},
                {"on": "self", "from": "int64", "to": "float64"},
            ],
        }
        doc["body"] = [{"kind": "Expr", "value": expr}]
        result = CppNoOpCastPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        casts = expr.get("casts")
        self.assertIsInstance(casts, list)
        self.assertEqual(len(casts), 1)
        self.assertEqual(casts[0].get("to"), "float64")

    def test_cpp_noop_cast_pass_folds_noop_static_cast_call(self) -> None:
        doc = _module_doc()
        call = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
            "resolved_type": "int64",
            "args": [
                {
                    "kind": "Name",
                    "id": "x",
                    "resolved_type": "int64",
                    "casts": [],
                }
            ],
            "keywords": [],
        }
        doc["body"] = [{"kind": "Expr", "value": call}]
        result = CppNoOpCastPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "x")

    def test_cpp_dead_temp_pass_removes_unused_pure_temp_assign(self) -> None:
        doc = _module_doc()
        dead_assign = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": "__tmp0", "resolved_type": "int64"},
            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
        }
        keep_stmt = {"kind": "Expr", "value": {"kind": "Constant", "value": 2, "resolved_type": "int64"}}
        doc["body"] = [dead_assign, keep_stmt]
        result = CppDeadTempPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        body = doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0].get("kind"), "Expr")

    def test_cpp_dead_temp_pass_keeps_temp_assign_when_used(self) -> None:
        doc = _module_doc()
        live_assign = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": "__tmp0", "resolved_type": "int64"},
            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
        }
        use_stmt = {"kind": "Expr", "value": {"kind": "Name", "id": "__tmp0", "resolved_type": "int64"}}
        doc["body"] = [live_assign, use_stmt]
        result = CppDeadTempPass().run(doc, CppOptContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        body = doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

    def test_cpp_const_condition_pass_rewrites_if_true_branch(self) -> None:
        doc = _module_doc()
        if_stmt = {
            "kind": "If",
            "test": {"kind": "Constant", "value": True, "resolved_type": "bool"},
            "body": [{"kind": "Expr", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}}],
            "orelse": [{"kind": "Expr", "value": {"kind": "Constant", "value": 2, "resolved_type": "int64"}}],
        }
        doc["body"] = [if_stmt]
        result = CppConstConditionPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        body = doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)
        value = body[0].get("value")
        self.assertEqual(value.get("value"), 1)

    def test_cpp_range_for_shape_pass_rewrites_runtime_range_forcore(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {
                    "kind": "Call",
                    "resolved_type": "object",
                    "borrow_kind": "value",
                    "casts": [],
                    "func": {"kind": "Name", "id": "range", "resolved_type": "unknown"},
                    "args": [
                        {"kind": "Constant", "resolved_type": "int64", "value": 5, "repr": "5"},
                    ],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_range",
                },
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppRangeForShapePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        self.assertEqual(for_stmt.get("iter_mode"), "static_fastpath")
        iter_plan = for_stmt.get("iter_plan")
        self.assertIsInstance(iter_plan, dict)
        self.assertEqual(iter_plan.get("kind"), "StaticRangeForPlan")
        self.assertEqual(iter_plan.get("start", {}).get("value"), 0)
        self.assertEqual(iter_plan.get("stop", {}).get("value"), 5)
        self.assertEqual(iter_plan.get("step", {}).get("value"), 1)

    def test_cpp_runtime_fastpath_pass_folds_unbox_same_type_at_o2(self) -> None:
        base_doc = _module_doc()
        base_doc["body"] = [
            {
                "kind": "Expr",
                "value": {
                    "kind": "Unbox",
                    "target": "int64",
                    "resolved_type": "int64",
                    "value": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                },
            }
        ]

        o1_doc = copy.deepcopy(base_doc)
        optimize_cpp_ir(o1_doc, opt_level="1")
        o1_value = o1_doc.get("body")[0].get("value")
        self.assertEqual(o1_value.get("kind"), "Unbox")

        o2_doc = copy.deepcopy(base_doc)
        result = CppRuntimeFastPathPass().run(o2_doc, CppOptContext(opt_level=2))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        o2_value = o2_doc.get("body")[0].get("value")
        self.assertEqual(o2_value.get("kind"), "Name")
        self.assertEqual(o2_value.get("id"), "x")

    def test_emit_cpp_from_east_runs_cpp_optimizer_hook(self) -> None:
        east_doc = _module_doc()
        optimized_doc = _module_doc()
        optimized_doc["meta"] = {"optimized": "1"}

        class _DummyEmitter:
            def __init__(self, east_ir: dict[str, object], *args: object, **kwargs: object) -> None:
                _ = args
                _ = kwargs
                self.east_ir = east_ir

            def transpile(self) -> str:
                meta_any = self.east_ir.get("meta")
                meta = meta_any if isinstance(meta_any, dict) else {}
                return "dummy-cpp:" + str(meta.get("optimized", "0"))

        with patch("hooks.cpp.emitter.cpp_emitter.optimize_cpp_ir", return_value=(optimized_doc, {"trace": []})) as opt_mock:
            with patch("hooks.cpp.emitter.cpp_emitter.CppEmitter", _DummyEmitter):
                out = emit_cpp_from_east(east_doc, {})
        self.assertEqual(opt_mock.call_count, 1)
        call_args = opt_mock.call_args
        self.assertIsNotNone(call_args)
        self.assertIs(call_args.args[0], east_doc)
        self.assertEqual(call_args.kwargs.get("opt_level"), 1)
        self.assertEqual(out, "dummy-cpp:1")


if __name__ == "__main__":
    unittest.main()

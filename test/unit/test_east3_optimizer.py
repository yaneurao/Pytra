from __future__ import annotations

import copy
import unittest

from src.pytra.compiler.east_parts.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from src.pytra.compiler.east_parts.east3_opt_passes.loop_invariant_hoist_lite_pass import LoopInvariantHoistLitePass
from src.pytra.compiler.east_parts.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from src.pytra.compiler.east_parts.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.strength_reduction_float_loop_pass import StrengthReductionFloatLoopPass
from src.pytra.compiler.east_parts.east3_opt_passes.typed_enumerate_normalization_pass import TypedEnumerateNormalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.unused_loop_var_elision_pass import UnusedLoopVarElisionPass
from src.pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from src.pytra.compiler.east_parts.east3_optimizer import PassContext
from src.pytra.compiler.east_parts.east3_optimizer import PassManager
from src.pytra.compiler.east_parts.east3_optimizer import PassResult
from src.pytra.compiler.east_parts.east3_optimizer import optimize_east3_document
from src.pytra.compiler.east_parts.east3_optimizer import parse_east3_opt_pass_overrides
from src.pytra.compiler.east_parts.east3_optimizer import render_east3_opt_trace
from src.pytra.compiler.east_parts.east3_optimizer import resolve_east3_opt_level


def _module_doc() -> dict[str, object]:
    return {"kind": "Module", "east_stage": 3, "schema_version": 1, "meta": {}, "body": []}


def _const_i(v: int) -> dict[str, object]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(v),
        "value": v,
    }


class _TouchPass(East3OptimizerPass):
    name = "TouchPass"
    min_opt_level = 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = context
        meta_any = east3_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        meta["touch"] = "ok"
        east3_doc["meta"] = meta
        return PassResult(changed=True, change_count=1)


class East3OptimizerTest(unittest.TestCase):
    def test_resolve_east3_opt_level(self) -> None:
        self.assertEqual(resolve_east3_opt_level(""), 1)
        self.assertEqual(resolve_east3_opt_level("0"), 0)
        self.assertEqual(resolve_east3_opt_level("1"), 1)
        self.assertEqual(resolve_east3_opt_level("2"), 2)
        self.assertEqual(resolve_east3_opt_level(2), 2)
        with self.assertRaisesRegex(ValueError, "invalid --east3-opt-level"):
            resolve_east3_opt_level("3")

    def test_parse_east3_opt_pass_overrides(self) -> None:
        enabled, disabled = parse_east3_opt_pass_overrides("+A,-B,+C")
        self.assertEqual(enabled, {"A", "C"})
        self.assertEqual(disabled, {"B"})
        with self.assertRaisesRegex(ValueError, "invalid --east3-opt-pass token"):
            parse_east3_opt_pass_overrides("A")

    def test_pass_manager_runs_and_collects_trace(self) -> None:
        doc = _module_doc()
        manager = PassManager([_TouchPass()])
        context = PassContext(opt_level=1)
        report = manager.run(doc, context)
        self.assertTrue(bool(report.get("changed")))
        self.assertEqual(int(report.get("change_count", 0)), 1)
        self.assertEqual(doc.get("meta", {}).get("touch"), "ok")
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "TouchPass")
        self.assertTrue(bool(trace[0].get("enabled")))

    def test_optimize_east3_document_validates_stage(self) -> None:
        doc = _module_doc()
        bad = dict(doc)
        bad["east_stage"] = 2
        with self.assertRaisesRegex(RuntimeError, "east_stage=3"):
            optimize_east3_document(bad)

    def test_optimize_east3_document_can_disable_default_pass(self) -> None:
        doc = _module_doc()
        out_doc, report = optimize_east3_document(
            doc,
            opt_level="1",
            opt_pass_spec="-NoOpCastCleanupPass,-LiteralCastFoldPass,-RangeForCanonicalizationPass,-TypedEnumerateNormalizationPass,-UnusedLoopVarElisionPass,-LoopInvariantHoistLitePass,-StrengthReductionFloatLoopPass",
        )
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        by_name = {str(item.get("name", "")): bool(item.get("enabled")) for item in trace if isinstance(item, dict)}
        self.assertFalse(by_name.get("NoOpCastCleanupPass", True))
        self.assertFalse(by_name.get("LiteralCastFoldPass", True))
        self.assertFalse(by_name.get("RangeForCanonicalizationPass", True))
        self.assertFalse(by_name.get("TypedEnumerateNormalizationPass", True))
        self.assertFalse(by_name.get("UnusedLoopVarElisionPass", True))
        self.assertFalse(by_name.get("LoopInvariantHoistLitePass", True))
        self.assertFalse(by_name.get("StrengthReductionFloatLoopPass", True))
        trace_text = render_east3_opt_trace(report)
        self.assertIn("NoOpCastCleanupPass", trace_text)
        self.assertIn("LiteralCastFoldPass", trace_text)
        self.assertIn("RangeForCanonicalizationPass", trace_text)
        self.assertIn("TypedEnumerateNormalizationPass", trace_text)
        self.assertIn("UnusedLoopVarElisionPass", trace_text)
        self.assertIn("LoopInvariantHoistLitePass", trace_text)
        self.assertIn("StrengthReductionFloatLoopPass", trace_text)

    def test_noop_cast_cleanup_pass_removes_only_proven_noops(self) -> None:
        doc = _module_doc()
        expr = {
            "kind": "Name",
            "id": "x",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [
                {"on": "self", "from": "int64", "to": "int64", "reason": "noop"},
                {"on": "self", "from": "int64", "to": "float64", "reason": "promotion"},
                {"on": "self", "from": "unknown", "to": "unknown", "reason": "unknown"},
            ],
            "repr": "x",
        }
        doc["body"] = [{"kind": "Expr", "value": expr}]
        result = NoOpCastCleanupPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        casts = expr.get("casts")
        self.assertIsInstance(casts, list)
        self.assertEqual(len(casts), 2)
        self.assertEqual(casts[0].get("to"), "float64")
        self.assertEqual(casts[1].get("to"), "unknown")

    def test_literal_cast_fold_pass_folds_constant_static_cast(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "int(42)",
            "func": {"kind": "Name", "id": "int"},
            "args": [
                {
                    "kind": "Constant",
                    "resolved_type": "int64",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": "42",
                    "value": 42,
                }
            ],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        doc["body"] = [{"kind": "Expr", "value": cast_call}]
        result = LiteralCastFoldPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        folded_value = doc.get("body")[0].get("value")
        self.assertEqual(folded_value.get("kind"), "Constant")
        self.assertEqual(folded_value.get("value"), 42)
        self.assertEqual(folded_value.get("repr"), "int(42)")

    def test_literal_cast_fold_pass_skips_non_foldable_cast(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "float(42)",
            "func": {"kind": "Name", "id": "float"},
            "args": [
                {
                    "kind": "Constant",
                    "resolved_type": "int64",
                    "borrow_kind": "value",
                    "casts": [],
                    "repr": "42",
                    "value": 42,
                }
            ],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        doc["body"] = [{"kind": "Expr", "value": cast_call}]
        result = LiteralCastFoldPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Call")

    def test_range_for_canonicalization_pass_rewrites_runtime_range_loop(self) -> None:
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
                    "args": [_const_i(5)],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_range",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = RangeForCanonicalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        self.assertEqual(for_stmt.get("iter_mode"), "static_fastpath")
        iter_plan = for_stmt.get("iter_plan")
        self.assertIsInstance(iter_plan, dict)
        self.assertEqual(iter_plan.get("kind"), "StaticRangeForPlan")
        self.assertEqual(iter_plan.get("start", {}).get("value"), 0)
        self.assertEqual(iter_plan.get("stop", {}).get("value"), 5)
        self.assertEqual(iter_plan.get("step", {}).get("value"), 1)
        self.assertEqual(iter_plan.get("range_mode"), "ascending")

    def test_range_for_canonicalization_pass_skips_zero_step(self) -> None:
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
                    "args": [_const_i(0), _const_i(5), _const_i(0)],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_range",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = RangeForCanonicalizationPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(for_stmt.get("iter_mode"), "runtime_protocol")
        self.assertEqual(for_stmt.get("iter_plan", {}).get("kind"), "RuntimeIterForPlan")

    def test_range_for_canonicalization_pass_accepts_dynamic_stop_with_const_step(self) -> None:
        doc = _module_doc()
        stop_name = {"kind": "Name", "id": "n", "resolved_type": "int64", "borrow_kind": "value", "casts": []}
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
                    "args": [stop_name],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_range",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = RangeForCanonicalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        iter_plan = for_stmt.get("iter_plan")
        self.assertIsInstance(iter_plan, dict)
        self.assertEqual(iter_plan.get("kind"), "StaticRangeForPlan")
        self.assertEqual(iter_plan.get("start", {}).get("value"), 0)
        self.assertEqual(iter_plan.get("stop", {}).get("kind"), "Name")
        self.assertEqual(iter_plan.get("stop", {}).get("id"), "n")
        self.assertEqual(iter_plan.get("step", {}).get("value"), 1)
        self.assertEqual(iter_plan.get("range_mode"), "ascending")

    def test_range_for_canonicalization_pass_skips_dynamic_stop_when_type_is_unknown(self) -> None:
        doc = _module_doc()
        stop_name = {"kind": "Name", "id": "n", "resolved_type": "unknown", "borrow_kind": "value", "casts": []}
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
                    "args": [stop_name],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_range",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = RangeForCanonicalizationPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(for_stmt.get("iter_mode"), "runtime_protocol")
        self.assertEqual(for_stmt.get("iter_plan", {}).get("kind"), "RuntimeIterForPlan")

    def test_typed_enumerate_normalization_pass_populates_metadata_from_list_arg(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {
                    "kind": "Call",
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "func": {"kind": "Name", "id": "enumerate", "resolved_type": "unknown"},
                    "args": [
                        {"kind": "Name", "id": "lines", "resolved_type": "list[str]", "borrow_kind": "value", "casts": []}
                    ],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "builtin_name": "enumerate",
                    "runtime_call": "py_enumerate",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "line_index", "target_type": "unknown"},
                    {"kind": "NameTarget", "id": "source", "target_type": "unknown"},
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = TypedEnumerateNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        iter_plan = for_stmt.get("iter_plan", {})
        iter_expr = iter_plan.get("iter_expr", {})
        self.assertEqual(iter_expr.get("resolved_type"), "list[tuple[int64, str]]")
        self.assertEqual(iter_expr.get("iter_element_type"), "tuple[int64, str]")
        self.assertEqual(iter_expr.get("iterable_trait"), "yes")
        self.assertEqual(iter_expr.get("iter_protocol"), "static_range")
        self.assertEqual(iter_plan.get("iter_item_type"), "tuple[int64, str]")
        target_plan = for_stmt.get("target_plan", {})
        self.assertEqual(target_plan.get("target_type"), "tuple[int64, str]")
        elems = target_plan.get("elements", [])
        self.assertEqual(elems[0].get("target_type"), "int64")
        self.assertEqual(elems[1].get("target_type"), "str")

    def test_typed_enumerate_normalization_pass_skips_when_list_elem_type_unknown(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {
                    "kind": "Call",
                    "resolved_type": "unknown",
                    "borrow_kind": "value",
                    "casts": [],
                    "func": {"kind": "Name", "id": "enumerate", "resolved_type": "unknown"},
                    "args": [
                        {
                            "kind": "Name",
                            "id": "lines",
                            "resolved_type": "list[unknown]",
                            "borrow_kind": "value",
                            "casts": [],
                        }
                    ],
                    "keywords": [],
                    "lowered_kind": "BuiltinCall",
                    "builtin_name": "enumerate",
                    "runtime_call": "py_enumerate",
                },
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "line_index", "target_type": "unknown"},
                    {"kind": "NameTarget", "id": "source", "target_type": "unknown"},
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = TypedEnumerateNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        iter_expr = for_stmt.get("iter_plan", {}).get("iter_expr", {})
        self.assertEqual(iter_expr.get("resolved_type"), "unknown")
        self.assertIsNone(for_stmt.get("iter_plan", {}).get("iter_item_type"))

    def test_unused_loop_var_elision_pass_renames_unused_target_to_underscore(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = UnusedLoopVarElisionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        self.assertEqual(for_stmt.get("target_plan", {}).get("id"), "_")

    def test_unused_loop_var_elision_pass_keeps_target_when_read_later(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        use_stmt = {"kind": "Expr", "value": {"kind": "Name", "id": "i", "resolved_type": "int64"}}
        doc["body"] = [for_stmt, use_stmt]
        result = UnusedLoopVarElisionPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(for_stmt.get("target_plan", {}).get("id"), "i")

    def test_loop_invariant_hoist_lite_pass_moves_first_assign_to_preheader(self) -> None:
        doc = _module_doc()
        hoist_assign = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": "tmp", "resolved_type": "int64"},
            "value": {
                "kind": "BinOp",
                "op": "Add",
                "left": {"kind": "Name", "id": "a", "resolved_type": "int64"},
                "right": _const_i(1),
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            },
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [hoist_assign, {"kind": "Expr", "value": {"kind": "Name", "id": "tmp", "resolved_type": "int64"}}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantHoistLitePass().run(doc, PassContext(opt_level=2))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        body = doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(body[0].get("kind"), "Assign")
        self.assertEqual(body[1].get("kind"), "ForCore")
        self.assertEqual(len(body[1].get("body", [])), 1)
        self.assertEqual(body[1].get("body", [])[0].get("kind"), "Expr")

    def test_loop_invariant_hoist_lite_pass_skips_potentially_empty_loop(self) -> None:
        doc = _module_doc()
        hoist_assign = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": "tmp", "resolved_type": "int64"},
            "value": {
                "kind": "BinOp",
                "op": "Add",
                "left": {"kind": "Name", "id": "a", "resolved_type": "int64"},
                "right": _const_i(1),
                "resolved_type": "int64",
                "borrow_kind": "value",
                "casts": [],
            },
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(0), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [hoist_assign, {"kind": "Expr", "value": {"kind": "Name", "id": "tmp", "resolved_type": "int64"}}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantHoistLitePass().run(doc, PassContext(opt_level=2))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(doc.get("body")[0].get("kind"), "ForCore")

    def test_strength_reduction_float_loop_pass_rewrites_div_power_of_two(self) -> None:
        doc = _module_doc()
        div_expr = {
            "kind": "BinOp",
            "op": "Div",
            "left": {"kind": "Name", "id": "x", "resolved_type": "float64"},
            "right": {
                "kind": "Constant",
                "resolved_type": "float64",
                "borrow_kind": "value",
                "casts": [],
                "repr": "2.0",
                "value": 2.0,
            },
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(4), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Assign", "target": {"kind": "Name", "id": "y", "resolved_type": "float64"}, "value": div_expr}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = StrengthReductionFloatLoopPass().run(doc, PassContext(opt_level=2))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = for_stmt.get("body", [])[0].get("value")
        self.assertEqual(value.get("op"), "Mult")
        self.assertEqual(value.get("right", {}).get("value"), 0.5)

    def test_strength_reduction_float_loop_pass_skips_non_power_of_two(self) -> None:
        doc = _module_doc()
        div_expr = {
            "kind": "BinOp",
            "op": "Div",
            "left": {"kind": "Name", "id": "x", "resolved_type": "float64"},
            "right": {
                "kind": "Constant",
                "resolved_type": "float64",
                "borrow_kind": "value",
                "casts": [],
                "repr": "3.0",
                "value": 3.0,
            },
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(4), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Assign", "target": {"kind": "Name", "id": "y", "resolved_type": "float64"}, "value": div_expr}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = StrengthReductionFloatLoopPass().run(doc, PassContext(opt_level=2))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        value = for_stmt.get("body", [])[0].get("value")
        self.assertEqual(value.get("op"), "Div")

    def test_unused_loop_var_elision_pass_skips_when_dynamic_name_access_exists(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "locals", "resolved_type": "unknown"},
                        "args": [],
                        "keywords": [],
                        "resolved_type": "object",
                    },
                }
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = UnusedLoopVarElisionPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(for_stmt.get("target_plan", {}).get("id"), "i")

    def test_loop_invariant_hoist_lite_pass_skips_when_dynamic_name_access_exists(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "tmp", "resolved_type": "int64"},
                    "value": {
                        "kind": "BinOp",
                        "op": "Add",
                        "left": {"kind": "Name", "id": "a", "resolved_type": "int64"},
                        "right": _const_i(1),
                        "resolved_type": "int64",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "locals", "resolved_type": "unknown"},
                        "args": [],
                        "keywords": [],
                        "resolved_type": "object",
                    },
                },
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantHoistLitePass().run(doc, PassContext(opt_level=2))
        self.assertFalse(result.changed)
        self.assertEqual(doc.get("body")[0].get("kind"), "ForCore")

    def test_optimize_east3_document_applies_o2_passes_only_at_o2(self) -> None:
        from pytra.compiler.east_parts.east3_optimizer import optimize_east3_document as optimize_native

        base_for = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(4), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "tmp", "resolved_type": "int64"},
                    "value": {
                        "kind": "BinOp",
                        "op": "Add",
                        "left": {"kind": "Name", "id": "a", "resolved_type": "int64"},
                        "right": _const_i(1),
                        "resolved_type": "int64",
                    },
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "y", "resolved_type": "float64"},
                    "value": {
                        "kind": "BinOp",
                        "op": "Div",
                        "left": {"kind": "Name", "id": "x", "resolved_type": "float64"},
                        "right": {
                            "kind": "Constant",
                            "resolved_type": "float64",
                            "borrow_kind": "value",
                            "casts": [],
                            "repr": "2.0",
                            "value": 2.0,
                        },
                        "resolved_type": "float64",
                        "borrow_kind": "value",
                        "casts": [],
                    },
                },
            ],
            "orelse": [],
        }
        doc_o1 = _module_doc()
        doc_o1["body"] = [copy.deepcopy(base_for)]
        _, report_o1 = optimize_native(doc_o1, opt_level=1)
        for_stmt_o1 = doc_o1.get("body")[0]
        self.assertEqual(for_stmt_o1.get("kind"), "ForCore")
        self.assertEqual(for_stmt_o1.get("body", [])[0].get("kind"), "Assign")
        self.assertEqual(for_stmt_o1.get("body", [])[1].get("value", {}).get("op"), "Div")
        trace_o1 = report_o1.get("trace", [])
        by_name_o1 = {str(item.get("name", "")): bool(item.get("enabled")) for item in trace_o1 if isinstance(item, dict)}
        self.assertFalse(by_name_o1.get("LoopInvariantHoistLitePass", True))
        self.assertFalse(by_name_o1.get("StrengthReductionFloatLoopPass", True))

        doc_o2 = _module_doc()
        doc_o2["body"] = [copy.deepcopy(base_for)]
        _, report_o2 = optimize_native(doc_o2, opt_level=2)
        body_o2 = doc_o2.get("body")
        self.assertEqual(body_o2[0].get("kind"), "Assign")
        self.assertEqual(body_o2[1].get("kind"), "ForCore")
        for_stmt_o2 = body_o2[1]
        self.assertEqual(for_stmt_o2.get("body", [])[0].get("value", {}).get("op"), "Mult")
        trace_o2 = report_o2.get("trace", [])
        by_name_o2 = {str(item.get("name", "")): bool(item.get("enabled")) for item in trace_o2 if isinstance(item, dict)}
        self.assertTrue(by_name_o2.get("LoopInvariantHoistLitePass", False))
        self.assertTrue(by_name_o2.get("StrengthReductionFloatLoopPass", False))


if __name__ == "__main__":
    unittest.main()

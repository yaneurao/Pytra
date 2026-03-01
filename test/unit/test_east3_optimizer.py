from __future__ import annotations

import copy
import unittest

from src.pytra.compiler.east_parts.east3_opt_passes.dict_str_key_normalization_pass import DictStrKeyNormalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.expression_normalization_pass import ExpressionNormalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.identity_py_to_elision_pass import IdentityPyToElisionPass
from src.pytra.compiler.east_parts.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from src.pytra.compiler.east_parts.east3_opt_passes.loop_invariant_cast_hoist_pass import LoopInvariantCastHoistPass
from src.pytra.compiler.east_parts.east3_opt_passes.loop_invariant_hoist_lite_pass import LoopInvariantHoistLitePass
from src.pytra.compiler.east_parts.east3_opt_passes.numeric_cast_chain_reduction_pass import NumericCastChainReductionPass
from src.pytra.compiler.east_parts.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from src.pytra.compiler.east_parts.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.safe_reserve_hint_pass import SafeReserveHintPass
from src.pytra.compiler.east_parts.east3_opt_passes.strength_reduction_float_loop_pass import StrengthReductionFloatLoopPass
from src.pytra.compiler.east_parts.east3_opt_passes.typed_enumerate_normalization_pass import TypedEnumerateNormalizationPass
from src.pytra.compiler.east_parts.east3_opt_passes.typed_repeat_materialization_pass import TypedRepeatMaterializationPass
from src.pytra.compiler.east_parts.east3_opt_passes.tuple_target_direct_expansion_pass import TupleTargetDirectExpansionPass
from src.pytra.compiler.east_parts.east3_opt_passes.unused_loop_var_elision_pass import UnusedLoopVarElisionPass
from src.pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from src.pytra.compiler.east_parts.east3_optimizer import PassContext
from src.pytra.compiler.east_parts.east3_optimizer import PassManager
from src.pytra.compiler.east_parts.east3_optimizer import PassResult
from src.pytra.compiler.east_parts.east3_optimizer import optimize_east3_document
from src.pytra.compiler.east_parts.east3_optimizer import parse_east3_opt_pass_overrides
from src.pytra.compiler.east_parts.east3_optimizer import render_east3_opt_trace
from src.pytra.compiler.east_parts.east3_optimizer import resolve_east3_opt_level
from src.pytra.compiler.east_parts.east3_optimizer import normalize_non_escape_policy


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


class _CapturePolicyPass(East3OptimizerPass):
    name = "CapturePolicyPass"
    min_opt_level = 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        meta_any = east3_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        meta["non_escape_policy"] = dict(context.non_escape_policy)
        east3_doc["meta"] = meta
        return PassResult(changed=False, change_count=0)


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

    def test_pass_context_non_escape_policy_defaults(self) -> None:
        context = PassContext(opt_level=1)
        policy = context.non_escape_policy
        self.assertIsInstance(policy, dict)
        self.assertTrue(bool(policy.get("unknown_call_escape")))
        self.assertTrue(bool(policy.get("unknown_attr_call_escape")))
        self.assertTrue(bool(policy.get("global_write_escape")))
        self.assertTrue(bool(policy.get("return_escape_by_default")))
        self.assertTrue(bool(policy.get("yield_escape_by_default")))

    def test_pass_context_non_escape_policy_override(self) -> None:
        context = PassContext(
            opt_level=1,
            non_escape_policy={
                "unknown_call_escape": False,
                "yield_escape_by_default": False,
                "ignored_key": True,
            },
        )
        policy = context.non_escape_policy
        self.assertFalse(bool(policy.get("unknown_call_escape")))
        self.assertFalse(bool(policy.get("yield_escape_by_default")))
        self.assertTrue(bool(policy.get("unknown_attr_call_escape")))
        self.assertTrue(bool(policy.get("global_write_escape")))

    def test_normalize_non_escape_policy_is_fail_closed(self) -> None:
        policy = normalize_non_escape_policy({"unknown_call_escape": False, "unknown_attr_call_escape": "yes"})
        self.assertFalse(bool(policy.get("unknown_call_escape")))
        self.assertTrue(bool(policy.get("unknown_attr_call_escape")))

    def test_pass_manager_exposes_non_escape_policy_to_passes(self) -> None:
        doc = _module_doc()
        manager = PassManager([_CapturePolicyPass()])
        context = PassContext(
            opt_level=1,
            non_escape_policy={"return_escape_by_default": False},
        )
        _ = manager.run(doc, context)
        meta = doc.get("meta", {})
        self.assertIsInstance(meta, dict)
        captured = meta.get("non_escape_policy")
        self.assertIsInstance(captured, dict)
        self.assertFalse(bool(captured.get("return_escape_by_default")))

    def test_optimize_east3_document_reports_non_escape_policy(self) -> None:
        doc = _module_doc()
        _, report = optimize_east3_document(
            doc,
            opt_level="1",
            non_escape_policy={"unknown_call_escape": False},
            pass_manager=PassManager([_CapturePolicyPass()]),
        )
        policy_obj = report.get("non_escape_policy")
        self.assertIsInstance(policy_obj, dict)
        self.assertFalse(bool(policy_obj.get("unknown_call_escape")))

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
            opt_pass_spec="-NoOpCastCleanupPass,-LiteralCastFoldPass,-IdentityPyToElisionPass,-NumericCastChainReductionPass,-RangeForCanonicalizationPass,-ExpressionNormalizationPass,-SafeReserveHintPass,-TypedEnumerateNormalizationPass,-TypedRepeatMaterializationPass,-DictStrKeyNormalizationPass,-TupleTargetDirectExpansionPass,-NonEscapeInterproceduralPass,-LoopInvariantCastHoistPass,-UnusedLoopVarElisionPass,-LoopInvariantHoistLitePass,-StrengthReductionFloatLoopPass",
        )
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        by_name = {str(item.get("name", "")): bool(item.get("enabled")) for item in trace if isinstance(item, dict)}
        self.assertFalse(by_name.get("NoOpCastCleanupPass", True))
        self.assertFalse(by_name.get("LiteralCastFoldPass", True))
        self.assertFalse(by_name.get("IdentityPyToElisionPass", True))
        self.assertFalse(by_name.get("NumericCastChainReductionPass", True))
        self.assertFalse(by_name.get("RangeForCanonicalizationPass", True))
        self.assertFalse(by_name.get("ExpressionNormalizationPass", True))
        self.assertFalse(by_name.get("SafeReserveHintPass", True))
        self.assertFalse(by_name.get("TypedEnumerateNormalizationPass", True))
        self.assertFalse(by_name.get("TypedRepeatMaterializationPass", True))
        self.assertFalse(by_name.get("DictStrKeyNormalizationPass", True))
        self.assertFalse(by_name.get("TupleTargetDirectExpansionPass", True))
        self.assertFalse(by_name.get("NonEscapeInterproceduralPass", True))
        self.assertFalse(by_name.get("LoopInvariantCastHoistPass", True))
        self.assertFalse(by_name.get("UnusedLoopVarElisionPass", True))
        self.assertFalse(by_name.get("LoopInvariantHoistLitePass", True))
        self.assertFalse(by_name.get("StrengthReductionFloatLoopPass", True))
        trace_text = render_east3_opt_trace(report)
        self.assertIn("NoOpCastCleanupPass", trace_text)
        self.assertIn("LiteralCastFoldPass", trace_text)
        self.assertIn("IdentityPyToElisionPass", trace_text)
        self.assertIn("NumericCastChainReductionPass", trace_text)
        self.assertIn("RangeForCanonicalizationPass", trace_text)
        self.assertIn("ExpressionNormalizationPass", trace_text)
        self.assertIn("SafeReserveHintPass", trace_text)
        self.assertIn("TypedEnumerateNormalizationPass", trace_text)
        self.assertIn("TypedRepeatMaterializationPass", trace_text)
        self.assertIn("DictStrKeyNormalizationPass", trace_text)
        self.assertIn("TupleTargetDirectExpansionPass", trace_text)
        self.assertIn("NonEscapeInterproceduralPass", trace_text)
        self.assertIn("LoopInvariantCastHoistPass", trace_text)
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

    def test_identity_py_to_elision_pass_folds_py_to_string_on_typed_str(self) -> None:
        doc = _module_doc()
        to_string_call = {
            "kind": "Call",
            "resolved_type": "str",
            "borrow_kind": "value",
            "casts": [],
            "repr": "str(s)",
            "func": {"kind": "Name", "id": "str"},
            "args": [{"kind": "Name", "id": "s", "resolved_type": "str", "borrow_kind": "value", "casts": []}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_to_string",
        }
        doc["body"] = [{"kind": "Expr", "value": to_string_call}]
        result = IdentityPyToElisionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        folded_value = doc.get("body")[0].get("value")
        self.assertEqual(folded_value.get("kind"), "Name")
        self.assertEqual(folded_value.get("id"), "s")

    def test_identity_py_to_elision_pass_skips_py_to_string_on_any_like_source(self) -> None:
        doc = _module_doc()
        to_string_call = {
            "kind": "Call",
            "resolved_type": "str",
            "borrow_kind": "value",
            "casts": [],
            "repr": "str(v)",
            "func": {"kind": "Name", "id": "str"},
            "args": [{"kind": "Name", "id": "v", "resolved_type": "object", "borrow_kind": "value", "casts": []}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_to_string",
        }
        doc["body"] = [{"kind": "Expr", "value": to_string_call}]
        result = IdentityPyToElisionPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(doc.get("body")[0].get("value", {}).get("kind"), "Call")

    def test_identity_py_to_elision_pass_folds_typed_unbox(self) -> None:
        doc = _module_doc()
        unbox_expr = {
            "kind": "Unbox",
            "target": "str",
            "resolved_type": "str",
            "borrow_kind": "value",
            "casts": [],
            "value": {"kind": "Name", "id": "s", "resolved_type": "str", "borrow_kind": "value", "casts": []},
        }
        doc["body"] = [{"kind": "Expr", "value": unbox_expr}]
        result = IdentityPyToElisionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        folded_value = doc.get("body")[0].get("value")
        self.assertEqual(folded_value.get("kind"), "Name")
        self.assertEqual(folded_value.get("id"), "s")

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

    def test_numeric_cast_chain_reduction_pass_folds_redundant_static_cast(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "int(x)",
            "func": {"kind": "Name", "id": "int"},
            "args": [{"kind": "Name", "id": "x", "resolved_type": "int64", "borrow_kind": "value", "casts": []}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        doc["body"] = [{"kind": "Expr", "value": cast_call}]
        result = NumericCastChainReductionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        folded_value = doc.get("body")[0].get("value")
        self.assertEqual(folded_value.get("kind"), "Name")
        self.assertEqual(folded_value.get("id"), "x")

    def test_numeric_cast_chain_reduction_pass_folds_redundant_unbox(self) -> None:
        doc = _module_doc()
        unbox_expr = {
            "kind": "Unbox",
            "target": "float64",
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
            "value": {"kind": "Name", "id": "v", "resolved_type": "float64", "borrow_kind": "value", "casts": []},
        }
        doc["body"] = [{"kind": "Expr", "value": unbox_expr}]
        result = NumericCastChainReductionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        folded_value = doc.get("body")[0].get("value")
        self.assertEqual(folded_value.get("kind"), "Name")
        self.assertEqual(folded_value.get("id"), "v")

    def test_numeric_cast_chain_reduction_pass_skips_any_like_source(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "int(x)",
            "func": {"kind": "Name", "id": "int"},
            "args": [{"kind": "Name", "id": "x", "resolved_type": "object", "borrow_kind": "value", "casts": []}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        doc["body"] = [{"kind": "Expr", "value": cast_call}]
        result = NumericCastChainReductionPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(doc.get("body")[0].get("value", {}).get("kind"), "Call")

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

    def test_expression_normalization_pass_tags_static_range_condition_and_binop(self) -> None:
        doc = _module_doc()
        binop = {
            "kind": "BinOp",
            "op": "Add",
            "left": {"kind": "Name", "id": "a", "resolved_type": "int64", "borrow_kind": "value", "casts": []},
            "right": {"kind": "Name", "id": "b", "resolved_type": "int64", "borrow_kind": "value", "casts": []},
            "resolved_type": "int64",
            "borrow_kind": "value",
            "casts": [],
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_range",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": _const_i(0),
                "stop": {"kind": "Name", "id": "n", "resolved_type": "int64", "borrow_kind": "value", "casts": []},
                "step": _const_i(1),
                "range_mode": "ascending",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Expr", "value": binop}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]

        result = ExpressionNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 2)
        self.assertEqual(for_stmt.get("normalized_expr_version"), "east3_expr_v1")
        exprs = for_stmt.get("normalized_exprs", {})
        self.assertIsInstance(exprs, dict)
        cond_expr = exprs.get("for_cond_expr")
        self.assertIsInstance(cond_expr, dict)
        self.assertEqual(cond_expr.get("kind"), "Compare")
        self.assertEqual(cond_expr.get("ops"), ["Lt"])
        self.assertEqual(cond_expr.get("left", {}).get("id"), "i")
        self.assertEqual(cond_expr.get("comparators", [{}])[0].get("id"), "n")
        self.assertEqual(binop.get("normalized_expr_version"), "east3_expr_v1")
        normalized_binop = binop.get("normalized_expr", {})
        self.assertIsInstance(normalized_binop, dict)
        self.assertEqual(normalized_binop.get("kind"), "BinOp")
        self.assertNotIn("normalized_expr", normalized_binop)

    def test_expression_normalization_pass_builds_dynamic_for_range_condition(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_range",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": _const_i(0),
                "stop": {"kind": "Name", "id": "limit", "resolved_type": "int64", "borrow_kind": "value", "casts": []},
                "step": {"kind": "Name", "id": "step", "resolved_type": "int64", "borrow_kind": "value", "casts": []},
                "range_mode": "dynamic",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]

        result = ExpressionNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        exprs = for_stmt.get("normalized_exprs", {})
        self.assertIsInstance(exprs, dict)
        cond_expr = exprs.get("for_cond_expr")
        self.assertIsInstance(cond_expr, dict)
        self.assertEqual(cond_expr.get("kind"), "IfExp")
        test_expr = cond_expr.get("test", {})
        self.assertEqual(test_expr.get("kind"), "Compare")
        self.assertEqual(test_expr.get("ops"), ["Gt"])

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

    def test_typed_repeat_materialization_pass_inferrs_listcomp_type_from_repeat_binop(self) -> None:
        doc = _module_doc()
        repeat_elt = {
            "kind": "BinOp",
            "op": "Mult",
            "resolved_type": "unknown",
            "left": {"kind": "List", "resolved_type": "list[int64]", "elements": [_const_i(0)]},
            "right": {"kind": "Name", "id": "w", "resolved_type": "int64"},
            "casts": [],
        }
        list_comp = {
            "kind": "ListComp",
            "resolved_type": "list[unknown]",
            "elt": repeat_elt,
            "generators": [],
            "casts": [],
        }
        doc["body"] = [{"kind": "Expr", "value": list_comp}]
        result = TypedRepeatMaterializationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 2)
        self.assertEqual(repeat_elt.get("resolved_type"), "list[int64]")
        self.assertEqual(list_comp.get("resolved_type"), "list[list[int64]]")

    def test_typed_repeat_materialization_pass_skips_when_repeat_factor_not_int(self) -> None:
        doc = _module_doc()
        repeat_elt = {
            "kind": "BinOp",
            "op": "Mult",
            "resolved_type": "unknown",
            "left": {"kind": "List", "resolved_type": "list[int64]", "elements": [_const_i(0)]},
            "right": {"kind": "Name", "id": "w", "resolved_type": "float64"},
            "casts": [],
        }
        list_comp = {
            "kind": "ListComp",
            "resolved_type": "list[unknown]",
            "elt": repeat_elt,
            "generators": [],
            "casts": [],
        }
        doc["body"] = [{"kind": "Expr", "value": list_comp}]
        result = TypedRepeatMaterializationPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(repeat_elt.get("resolved_type"), "unknown")
        self.assertEqual(list_comp.get("resolved_type"), "list[unknown]")

    def test_dict_str_key_normalization_pass_marks_subscript_key_for_str_dict(self) -> None:
        doc = _module_doc()
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "env", "resolved_type": "dict[str, int64]"},
            "slice": {"kind": "Name", "id": "k", "resolved_type": "unknown"},
            "resolved_type": "int64",
        }
        doc["body"] = [{"kind": "Expr", "value": subscript}]
        result = DictStrKeyNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        key_node = subscript.get("slice", {})
        self.assertEqual(key_node.get("resolved_type"), "str")
        self.assertTrue(bool(key_node.get("dict_key_verified", False)))

    def test_dict_str_key_normalization_pass_skips_non_str_key_dict(self) -> None:
        doc = _module_doc()
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "env", "resolved_type": "dict[int64, int64]"},
            "slice": {"kind": "Name", "id": "k", "resolved_type": "unknown"},
            "resolved_type": "int64",
        }
        doc["body"] = [{"kind": "Expr", "value": subscript}]
        result = DictStrKeyNormalizationPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        key_node = subscript.get("slice", {})
        self.assertEqual(key_node.get("resolved_type"), "unknown")
        self.assertFalse(bool(key_node.get("dict_key_verified", False)))

    def test_tuple_target_direct_expansion_pass_marks_flat_typed_tuple_target(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {
                    "kind": "Call",
                    "resolved_type": "unknown",
                    "runtime_call": "py_enumerate",
                    "iter_element_type": "tuple[int64, str]",
                    "args": [{"kind": "Name", "id": "lines", "resolved_type": "list[str]"}],
                    "lowered_kind": "BuiltinCall",
                    "builtin_name": "enumerate",
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
        result = TupleTargetDirectExpansionPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        target_plan = for_stmt.get("target_plan", {})
        self.assertTrue(bool(target_plan.get("direct_unpack", False)))
        self.assertEqual(target_plan.get("direct_unpack_names"), ["line_index", "source"])
        self.assertEqual(target_plan.get("direct_unpack_types"), ["int64", "str"])
        self.assertEqual(for_stmt.get("iter_plan", {}).get("iter_item_type"), "tuple[int64, str]")

    def test_tuple_target_direct_expansion_pass_skips_nested_tuple_target(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {"kind": "Name", "id": "pairs", "resolved_type": "list[tuple[int64, tuple[str, str]]]"},
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "idx", "target_type": "int64"},
                    {
                        "kind": "TupleTarget",
                        "elements": [
                            {"kind": "NameTarget", "id": "a", "target_type": "str"},
                            {"kind": "NameTarget", "id": "b", "target_type": "str"},
                        ],
                    },
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = TupleTargetDirectExpansionPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertFalse(bool(for_stmt.get("target_plan", {}).get("direct_unpack", False)))

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

    def test_safe_reserve_hint_pass_marks_static_loop_with_unconditional_append(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": _const_i(0),
                "stop": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                "step": _const_i(1),
                "range_mode": "ascending",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Attribute", "value": {"kind": "Name", "id": "xs"}, "attr": "append"},
                        "args": [{"kind": "Name", "id": "i", "resolved_type": "int64"}],
                        "keywords": [],
                    },
                }
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = SafeReserveHintPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        hints = for_stmt.get("reserve_hints")
        self.assertIsInstance(hints, list)
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].get("owner"), "xs")
        self.assertTrue(bool(hints[0].get("safe")))
        self.assertEqual(hints[0].get("count_expr_version"), "east3_expr_v1")
        count_expr = hints[0].get("count_expr")
        self.assertIsInstance(count_expr, dict)
        self.assertEqual(count_expr.get("kind"), "IfExp")

    def test_safe_reserve_hint_pass_skips_conditional_append(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": _const_i(0),
                "stop": _const_i(8),
                "step": _const_i(1),
                "range_mode": "ascending",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "If",
                    "test": {"kind": "Name", "id": "pred", "resolved_type": "bool"},
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Attribute", "value": {"kind": "Name", "id": "xs"}, "attr": "append"},
                                "args": [_const_i(1)],
                                "keywords": [],
                            },
                        }
                    ],
                    "orelse": [],
                }
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = SafeReserveHintPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertIsNone(for_stmt.get("reserve_hints"))

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

    def test_loop_invariant_cast_hoist_pass_hoists_static_cast_arg_without_loop_var(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "float(width - 1)",
            "func": {"kind": "Name", "id": "float"},
            "args": [
                {
                    "kind": "BinOp",
                    "op": "Sub",
                    "resolved_type": "int64",
                    "left": {"kind": "Name", "id": "width", "resolved_type": "int64"},
                    "right": _const_i(1),
                }
            ],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "denom", "resolved_type": "float64"},
                    "value": cast_call,
                }
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantCastHoistPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        body = doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(body[0].get("kind"), "AnnAssign")
        hoisted_name = body[0].get("target", {}).get("id")
        self.assertIsInstance(hoisted_name, str)
        self.assertTrue(hoisted_name.startswith("__hoisted_cast_"))
        self.assertEqual(body[1].get("kind"), "ForCore")
        loop_assign = body[1].get("body", [])[0]
        self.assertEqual(loop_assign.get("value", {}).get("kind"), "Name")
        self.assertEqual(loop_assign.get("value", {}).get("id"), hoisted_name)

    def test_loop_invariant_cast_hoist_pass_skips_when_cast_depends_on_loop_var(self) -> None:
        doc = _module_doc()
        cast_call = {
            "kind": "Call",
            "resolved_type": "float64",
            "borrow_kind": "value",
            "casts": [],
            "repr": "float(i)",
            "func": {"kind": "Name", "id": "float"},
            "args": [{"kind": "Name", "id": "i", "resolved_type": "int64"}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "y", "resolved_type": "float64"},
                    "value": cast_call,
                }
            ],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantCastHoistPass().run(doc, PassContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertEqual(doc.get("body")[0].get("kind"), "ForCore")

    def test_loop_invariant_cast_hoist_pass_hoists_binop_right_numeric_promotion(self) -> None:
        doc = _module_doc()
        div_expr = {
            "kind": "BinOp",
            "op": "Div",
            "resolved_type": "float64",
            "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
            "right": {
                "kind": "BinOp",
                "op": "Sub",
                "resolved_type": "int64",
                "left": {"kind": "Name", "id": "width", "resolved_type": "int64"},
                "right": _const_i(1),
            },
            "casts": [
                {"on": "left", "from": "int64", "to": "float64", "reason": "numeric_promotion"},
                {"on": "right", "from": "int64", "to": "float64", "reason": "numeric_promotion"},
            ],
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {"kind": "StaticRangeForPlan", "start": _const_i(0), "stop": _const_i(5), "step": _const_i(1)},
            "target_plan": {"kind": "NameTarget", "id": "x", "target_type": "int64"},
            "body": [{"kind": "Assign", "target": {"kind": "Name", "id": "ratio", "resolved_type": "float64"}, "value": div_expr}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = LoopInvariantCastHoistPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertGreaterEqual(result.change_count, 1)
        body = doc.get("body")
        self.assertEqual(body[0].get("kind"), "AnnAssign")
        tmp_name = body[0].get("target", {}).get("id")
        self.assertTrue(isinstance(tmp_name, str) and tmp_name.startswith("__hoisted_cast_"))
        loop_div = body[1].get("body", [])[0].get("value", {})
        self.assertEqual(loop_div.get("right", {}).get("kind"), "Name")
        self.assertEqual(loop_div.get("right", {}).get("id"), tmp_name)
        casts = loop_div.get("casts", [])
        self.assertEqual(len(casts), 1)
        self.assertEqual(casts[0].get("on"), "left")

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

from __future__ import annotations

import unittest

from src.pytra.compiler.east_parts.east3_opt_passes.literal_cast_fold_pass import LiteralCastFoldPass
from src.pytra.compiler.east_parts.east3_opt_passes.noop_cast_cleanup_pass import NoOpCastCleanupPass
from src.pytra.compiler.east_parts.east3_opt_passes.range_for_canonicalization_pass import RangeForCanonicalizationPass
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
            opt_pass_spec="-NoOpCastCleanupPass,-LiteralCastFoldPass,-RangeForCanonicalizationPass,-UnusedLoopVarElisionPass",
        )
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "NoOpCastCleanupPass")
        self.assertFalse(bool(trace[0].get("enabled")))
        self.assertEqual(trace[1].get("name"), "LiteralCastFoldPass")
        self.assertFalse(bool(trace[1].get("enabled")))
        self.assertEqual(trace[2].get("name"), "RangeForCanonicalizationPass")
        self.assertFalse(bool(trace[2].get("enabled")))
        self.assertEqual(trace[3].get("name"), "UnusedLoopVarElisionPass")
        self.assertFalse(bool(trace[3].get("enabled")))
        trace_text = render_east3_opt_trace(report)
        self.assertIn("NoOpCastCleanupPass", trace_text)
        self.assertIn("LiteralCastFoldPass", trace_text)
        self.assertIn("RangeForCanonicalizationPass", trace_text)
        self.assertIn("UnusedLoopVarElisionPass", trace_text)

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


if __name__ == "__main__":
    unittest.main()

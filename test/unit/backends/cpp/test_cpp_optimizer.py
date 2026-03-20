from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.emit.cpp.emitter.cpp_emitter import CppEmitter
from toolchain.emit.cpp.emitter.cpp_emitter import emit_cpp_from_east
from toolchain.emit.cpp.lower import lower_cpp_from_east3
from toolchain.emit.cpp.optimizer.context import CppOptContext
from toolchain.emit.cpp.optimizer.context import CppOptimizerPass
from toolchain.emit.cpp.optimizer.context import CppOptResult
from toolchain.emit.cpp.optimizer.cpp_optimizer import CppPassManager
from toolchain.emit.cpp.optimizer.cpp_optimizer import optimize_cpp_ir
from toolchain.emit.cpp.optimizer.cpp_optimizer import parse_cpp_opt_pass_overrides
from toolchain.emit.cpp.optimizer.cpp_optimizer import resolve_cpp_opt_level
from toolchain.emit.cpp.optimizer.cpp_ir_optimizer import optimize_cpp_ir_module
from toolchain.emit.cpp.optimizer.passes.const_condition_pass import CppConstConditionPass
from toolchain.emit.cpp.optimizer.passes.dead_temp_pass import CppDeadTempPass
from toolchain.emit.cpp.optimizer.passes.binop_normalize_pass import CppBinOpNormalizePass
from toolchain.emit.cpp.optimizer.passes.brace_omit_hint_pass import CppBraceOmitHintPass
from toolchain.emit.cpp.optimizer.passes.cast_call_normalize_pass import CppCastCallNormalizePass
from toolchain.emit.cpp.optimizer.passes.compare_normalize_pass import CppCompareNormalizePass
from toolchain.emit.cpp.optimizer.passes.forcore_direct_unpack_hint_pass import CppForcoreDirectUnpackHintPass
from toolchain.emit.cpp.optimizer.passes.for_iter_mode_hint_pass import CppForIterModeHintPass
from toolchain.emit.cpp.optimizer.passes.noop_cast_pass import CppNoOpCastPass
from toolchain.emit.cpp.optimizer.passes.range_for_shape_pass import CppRangeForShapePass
from toolchain.emit.cpp.optimizer.passes.runtime_fastpath_pass import CppRuntimeFastPathPass
from toolchain.emit.cpp.optimizer.trace import render_cpp_opt_trace


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
    def test_cpp_lower_accepts_module_and_is_pass_through(self) -> None:
        doc = _module_doc()
        out_doc, report = lower_cpp_from_east3(doc, debug_flags={"x": "1"})
        self.assertIs(out_doc, doc)
        self.assertEqual(report.get("stage"), "cpp_lower")
        self.assertEqual(report.get("mode"), "pass_through_v1_stmt_kind_hint")
        self.assertFalse(bool(report.get("changed")))

    def test_cpp_lower_adds_stmt_kind_hints(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {},
            "body": [
                {"kind": "Pass"},
                {
                    "kind": "If",
                    "test": {"kind": "Constant", "value": True, "resolved_type": "bool"},
                    "body": [{"kind": "Break"}],
                    "orelse": [],
                },
            ],
        }
        out_doc, report = lower_cpp_from_east3(doc)
        self.assertIs(out_doc, doc)
        self.assertTrue(bool(report.get("changed")))
        self.assertGreaterEqual(int(report.get("change_count", 0)), 3)
        body = out_doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(body[0].get("cpp_stmt_kind_v1"), "Pass")
        self.assertEqual(body[1].get("cpp_stmt_kind_v1"), "If")
        nested = body[1].get("body")
        self.assertIsInstance(nested, list)
        self.assertEqual(nested[0].get("cpp_stmt_kind_v1"), "Break")
        test_expr = body[1].get("test")
        self.assertIsInstance(test_expr, dict)
        self.assertEqual(test_expr.get("cpp_expr_kind_v1"), "Constant")

    def test_cpp_lower_adds_match_stmt_hint(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {},
            "body": [
                {
                    "kind": "Match",
                    "subject": {"kind": "Name", "id": "x", "resolved_type": "Maybe"},
                    "cases": [],
                }
            ],
        }
        out_doc, report = lower_cpp_from_east3(doc)
        self.assertIs(out_doc, doc)
        self.assertTrue(bool(report.get("changed")))
        body = out_doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(body[0].get("cpp_stmt_kind_v1"), "Match")

    def test_cpp_lower_does_not_annotate_non_ast_kind_maps(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {},
            "body": [
                {
                    "kind": "ClassDef",
                    "name": "Token",
                    "base": None,
                    "dataclass": True,
                    "field_types": {"kind": "str", "text": "str"},
                    "body": [],
                }
            ],
        }
        out_doc, _report = lower_cpp_from_east3(doc)
        body = out_doc.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)
        cls = body[0]
        self.assertIsInstance(cls, dict)
        field_types = cls.get("field_types")
        self.assertIsInstance(field_types, dict)
        self.assertNotIn("cpp_expr_kind_v1", field_types)

    def test_cpp_emitter_accepts_stmt_kind_hint(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter.emit_stmt({"kind": "Unknown", "cpp_stmt_kind_v1": "Pass"})
        text = "\n".join(emitter.lines)
        self.assertIn("pass", text)

    def test_cpp_emitter_accepts_expr_kind_hint(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        out = emitter.render_expr({"kind": "Unknown", "cpp_expr_kind_v1": "Name", "id": "x", "resolved_type": "int64"})
        self.assertEqual(out, "x")

    def test_cpp_lower_rejects_non_module_kind(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "kind must be Module"):
            lower_cpp_from_east3({"kind": "Expr"})

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
            opt_pass_spec="-CppNoOpPass,-CppDeadTempPass,-CppNoOpCastPass,-CppCastCallNormalizePass,-CppCompareNormalizePass,-CppBinOpNormalizePass,-CppConstConditionPass,-CppRangeForShapePass,-CppForcoreDirectUnpackHintPass,-CppForIterModeHintPass,-CppBraceOmitHintPass,-CppRuntimeFastPathPass",
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
        self.assertEqual(trace[3].get("name"), "CppCastCallNormalizePass")
        self.assertFalse(bool(trace[3].get("enabled")))
        self.assertEqual(trace[4].get("name"), "CppCompareNormalizePass")
        self.assertFalse(bool(trace[4].get("enabled")))
        self.assertEqual(trace[5].get("name"), "CppBinOpNormalizePass")
        self.assertFalse(bool(trace[5].get("enabled")))
        self.assertEqual(trace[6].get("name"), "CppConstConditionPass")
        self.assertFalse(bool(trace[6].get("enabled")))
        self.assertEqual(trace[7].get("name"), "CppRangeForShapePass")
        self.assertFalse(bool(trace[7].get("enabled")))
        self.assertEqual(trace[8].get("name"), "CppForcoreDirectUnpackHintPass")
        self.assertFalse(bool(trace[8].get("enabled")))
        self.assertEqual(trace[9].get("name"), "CppForIterModeHintPass")
        self.assertFalse(bool(trace[9].get("enabled")))
        self.assertEqual(trace[10].get("name"), "CppBraceOmitHintPass")
        self.assertFalse(bool(trace[10].get("enabled")))
        self.assertEqual(trace[11].get("name"), "CppRuntimeFastPathPass")
        self.assertFalse(bool(trace[11].get("enabled")))
        trace_text = render_cpp_opt_trace(report)
        self.assertIn("CppNoOpPass enabled=false", trace_text)
        self.assertIn("CppDeadTempPass enabled=false", trace_text)
        self.assertIn("CppNoOpCastPass enabled=false", trace_text)
        self.assertIn("CppCastCallNormalizePass enabled=false", trace_text)
        self.assertIn("CppCompareNormalizePass enabled=false", trace_text)
        self.assertIn("CppBinOpNormalizePass enabled=false", trace_text)
        self.assertIn("CppConstConditionPass enabled=false", trace_text)
        self.assertIn("CppRangeForShapePass enabled=false", trace_text)
        self.assertIn("CppForcoreDirectUnpackHintPass enabled=false", trace_text)
        self.assertIn("CppForIterModeHintPass enabled=false", trace_text)
        self.assertIn("CppBraceOmitHintPass enabled=false", trace_text)
        self.assertIn("CppRuntimeFastPathPass enabled=false", trace_text)

    def test_cpp_brace_omit_hint_pass_marks_simple_forcore(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                "range_mode": "ascending",
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Expr", "value": {"kind": "Name", "id": "i", "resolved_type": "int64"}}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppBraceOmitHintPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        self.assertTrue(bool(for_stmt.get("cpp_omit_braces_v1")))

    def test_cpp_for_iter_mode_hint_pass_is_noop_in_pyobj_mode(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "For",
            "target": {"kind": "Name", "id": "x", "resolved_type": "object"},
            "iter": {"kind": "Name", "id": "xs", "resolved_type": "object"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppForIterModeHintPass().run(doc, CppOptContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertNotIn("cpp_iter_mode_v1", for_stmt)

    def test_cpp_for_iter_mode_hint_pass_skips_typed_iter_in_pyobj_mode(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "For",
            "target": {"kind": "Name", "id": "x", "resolved_type": "int64"},
            "iter": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppForIterModeHintPass().run(doc, CppOptContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)
        self.assertNotIn("cpp_iter_mode_v1", for_stmt)

    def test_optimize_cpp_ir_module_delegates_existing_optimizer(self) -> None:
        doc = _module_doc()
        out_doc, report = optimize_cpp_ir_module(
            doc,
            opt_level="1",
            opt_pass_spec="-CppNoOpPass",
            debug_flags={"k": "v"},
        )
        self.assertIs(out_doc, doc)
        self.assertEqual(report.get("opt_level"), 1)
        self.assertIn("CppNoOpPass", report.get("disabled_passes", []))

    def test_cpp_cast_call_normalize_pass_folds_nested_py_to_int64(self) -> None:
        doc = _module_doc()
        call = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_to_int64",
            "resolved_type": "int64",
            "args": [
                {
                    "kind": "Call",
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_to_int64",
                    "resolved_type": "int64",
                    "args": [{"kind": "Name", "id": "x", "resolved_type": "object"}],
                    "keywords": [],
                }
            ],
            "keywords": [],
        }
        doc["body"] = [{"kind": "Expr", "value": call}]
        result = CppCastCallNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Call")
        self.assertEqual(value.get("runtime_call"), "py_to_int64")
        inner_args = value.get("args")
        self.assertIsInstance(inner_args, list)
        self.assertEqual(inner_args[0].get("kind"), "Name")

    def test_cpp_cast_call_normalize_pass_folds_static_cast_over_py_to_int64(self) -> None:
        doc = _module_doc()
        call = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "static_cast",
            "resolved_type": "int64",
            "args": [
                {
                    "kind": "Call",
                    "lowered_kind": "BuiltinCall",
                    "runtime_call": "py_to_int64",
                    "resolved_type": "int64",
                    "args": [{"kind": "Name", "id": "x", "resolved_type": "object"}],
                    "keywords": [],
                }
            ],
            "keywords": [],
        }
        doc["body"] = [{"kind": "Expr", "value": call}]
        result = CppCastCallNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Call")
        self.assertEqual(value.get("runtime_call"), "py_to_int64")

    def test_cpp_compare_normalize_pass_folds_eq_true_to_left(self) -> None:
        doc = _module_doc()
        compare = {
            "kind": "Compare",
            "left": {"kind": "Name", "id": "flag", "resolved_type": "bool"},
            "ops": ["Eq"],
            "comparators": [{"kind": "Constant", "value": True, "resolved_type": "bool"}],
            "resolved_type": "bool",
        }
        doc["body"] = [{"kind": "Expr", "value": compare}]
        result = CppCompareNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "flag")

    def test_cpp_compare_normalize_pass_folds_eq_false_to_not(self) -> None:
        doc = _module_doc()
        compare = {
            "kind": "Compare",
            "left": {"kind": "Name", "id": "flag", "resolved_type": "bool"},
            "ops": ["Eq"],
            "comparators": [{"kind": "Constant", "value": False, "resolved_type": "bool"}],
            "resolved_type": "bool",
        }
        doc["body"] = [{"kind": "Expr", "value": compare}]
        result = CppCompareNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "UnaryOp")
        self.assertEqual(value.get("op"), "Not")

    def test_cpp_binop_normalize_pass_folds_add_zero(self) -> None:
        doc = _module_doc()
        expr = {
            "kind": "BinOp",
            "op": "Add",
            "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
            "right": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        doc["body"] = [{"kind": "Expr", "value": expr}]
        result = CppBinOpNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "x")

    def test_cpp_binop_normalize_pass_folds_mult_one(self) -> None:
        doc = _module_doc()
        expr = {
            "kind": "BinOp",
            "op": "Mult",
            "left": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            "right": {"kind": "Name", "id": "x", "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        doc["body"] = [{"kind": "Expr", "value": expr}]
        result = CppBinOpNormalizePass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        value = doc.get("body")[0].get("value")
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "x")

    def test_cpp_forcore_direct_unpack_hint_pass_sets_hint_for_known_tuple(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {"kind": "Name", "id": "pairs", "resolved_type": "list[tuple[int64, str]]"},
                "iter_item_type": "tuple[int64, str]",
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "line_index", "target_type": "int64"},
                    {"kind": "NameTarget", "id": "source", "target_type": "str"},
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppForcoreDirectUnpackHintPass().run(doc, CppOptContext(opt_level=1))
        self.assertTrue(result.changed)
        self.assertEqual(result.change_count, 1)
        target_plan = for_stmt.get("target_plan")
        self.assertIsInstance(target_plan, dict)
        self.assertTrue(bool(target_plan.get("direct_unpack")))
        self.assertEqual(target_plan.get("direct_unpack_names"), ["line_index", "source"])
        self.assertEqual(target_plan.get("direct_unpack_types"), ["int64", "str"])

    def test_cpp_forcore_direct_unpack_hint_pass_skips_unknown_tuple(self) -> None:
        doc = _module_doc()
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {"kind": "Name", "id": "pairs", "resolved_type": "object"},
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "a", "target_type": "unknown"},
                    {"kind": "NameTarget", "id": "b", "target_type": "unknown"},
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc["body"] = [for_stmt]
        result = CppForcoreDirectUnpackHintPass().run(doc, CppOptContext(opt_level=1))
        self.assertFalse(result.changed)
        self.assertEqual(result.change_count, 0)

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

    def test_emit_cpp_from_east_runs_cpp_lower_and_optimizer_hooks(self) -> None:
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

        with patch(
            "toolchain.emit.cpp.emitter.cpp_emitter.lower_cpp_from_east3",
            return_value=(east_doc, {"mode": "pass_through_v0", "changed": False, "change_count": 0}),
        ) as lower_mock:
            with patch(
                "toolchain.emit.cpp.emitter.cpp_emitter.optimize_cpp_ir_module",
                return_value=(optimized_doc, {"trace": []}),
            ) as opt_mock:
                with patch("toolchain.emit.cpp.emitter.cpp_emitter.CppEmitter", _DummyEmitter):
                    out = emit_cpp_from_east(east_doc, {})
        self.assertEqual(lower_mock.call_count, 1)
        lower_call_args = lower_mock.call_args
        self.assertIsNotNone(lower_call_args)
        self.assertIs(lower_call_args.args[0], east_doc)
        self.assertEqual(opt_mock.call_count, 1)
        call_args = opt_mock.call_args
        self.assertIsNotNone(call_args)
        self.assertIs(call_args.args[0], east_doc)
        self.assertEqual(call_args.kwargs.get("opt_level"), 1)
        self.assertEqual(out, "dummy-cpp:1")


if __name__ == "__main__":
    unittest.main()

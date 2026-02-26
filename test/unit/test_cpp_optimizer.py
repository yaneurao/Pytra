from __future__ import annotations

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
        out_doc, report = optimize_cpp_ir(doc, opt_level="1", opt_pass_spec="-CppNoOpPass")
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "CppNoOpPass")
        self.assertFalse(bool(trace[0].get("enabled")))
        trace_text = render_cpp_opt_trace(report)
        self.assertIn("CppNoOpPass enabled=false", trace_text)

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

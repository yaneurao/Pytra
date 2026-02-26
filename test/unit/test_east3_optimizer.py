from __future__ import annotations

import unittest

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
        out_doc, report = optimize_east3_document(doc, opt_level="1", opt_pass_spec="-NoOpPass")
        self.assertIs(out_doc, doc)
        trace = report.get("trace")
        self.assertIsInstance(trace, list)
        self.assertEqual(trace[0].get("name"), "NoOpPass")
        self.assertFalse(bool(trace[0].get("enabled")))
        trace_text = render_east3_opt_trace(report)
        self.assertIn("NoOpPass", trace_text)


if __name__ == "__main__":
    unittest.main()


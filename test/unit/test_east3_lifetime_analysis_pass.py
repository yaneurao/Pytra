from __future__ import annotations

import unittest

from src.toolchain.compiler.east_parts.east3_opt_passes.lifetime_analysis_pass import LifetimeAnalysisPass
from src.toolchain.compiler.east_parts.east3_optimizer import PassContext


def _name(name: str) -> dict[str, object]:
    return {"kind": "Name", "id": name}


def _const(value: object) -> dict[str, object]:
    return {"kind": "Constant", "value": value}


def _assign(name: str, value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Assign", "target": _name(name), "value": value}


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


def _ret(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Return", "value": value}


def _if(
    test: dict[str, object],
    body: list[dict[str, object]],
    orelse: list[dict[str, object]],
) -> dict[str, object]:
    return {"kind": "If", "test": test, "body": body, "orelse": orelse}


def _call(name: str, args: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "Call", "func": _name(name), "args": args, "keywords": []}


def _tuple_target(*names: str) -> dict[str, object]:
    return {"kind": "Tuple", "elements": [_name(name) for name in names]}


def _fn(name: str, args: list[str], body: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "arg_order": args, "body": body}


class LifetimeAnalysisPassTest(unittest.TestCase):
    def test_pass_attaches_cfg_and_def_use(self) -> None:
        ret_stmt = _ret(_name("y"))
        fn = _fn(
            "f",
            ["x"],
            [
                _assign("y", _const(0)),
                _if(_name("x"), [_assign("y", _name("x"))], [_assign("y", _const(1))]),
                ret_stmt,
            ],
        )
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}

        result = LifetimeAnalysisPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        fn_meta = fn.get("meta", {})
        self.assertIsInstance(fn_meta, dict)
        analysis = fn_meta.get("lifetime_analysis")
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("schema_version"), "east3_lifetime_v1")
        self.assertEqual(analysis.get("status"), "ok")
        cfg = analysis.get("cfg")
        self.assertIsInstance(cfg, list)
        self.assertGreater(len(cfg), 0)
        defs_index = analysis.get("def_use", {}).get("defs", {})
        uses_index = analysis.get("def_use", {}).get("uses", {})
        self.assertIn("y", defs_index)
        self.assertIn("x", uses_index)
        self.assertIn("y", uses_index)
        self.assertIn("y", ret_stmt.get("meta", {}).get("lifetime_last_use_vars", []))

    def test_pass_computes_branch_liveness_and_last_use(self) -> None:
        ret_stmt = _ret(_name("acc"))
        if_stmt = _if(_name("cond"), [_assign("acc", _name("x"))], [_assign("acc", _name("y"))])
        fn = _fn(
            "f",
            ["cond", "x", "y"],
            [
                _assign("acc", _const(0)),
                if_stmt,
                ret_stmt,
            ],
        )
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}

        _ = LifetimeAnalysisPass().run(doc, PassContext(opt_level=1))
        analysis = fn.get("meta", {}).get("lifetime_analysis", {})
        vars_info = analysis.get("variables", {})
        self.assertIn("acc", vars_info)
        acc_info = vars_info.get("acc", {})
        self.assertIn("last_use_nodes", acc_info)
        self.assertGreaterEqual(len(acc_info.get("last_use_nodes", [])), 1)
        ret_meta = ret_stmt.get("meta", {})
        self.assertIn("acc", ret_meta.get("lifetime_last_use_vars", []))
        if_meta = if_stmt.get("meta", {})
        self.assertIn("cond", if_meta.get("lifetime_uses", []))
        self.assertIn("x", if_meta.get("lifetime_live_out", []))
        self.assertIn("y", if_meta.get("lifetime_live_out", []))

    def test_pass_fail_closed_on_dynamic_name_access(self) -> None:
        fn = _fn(
            "f",
            ["x"],
            [
                _expr(_call("eval", [_name("x")])),
                _ret(_name("x")),
            ],
        )
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}

        _ = LifetimeAnalysisPass().run(doc, PassContext(opt_level=1))
        analysis = fn.get("meta", {}).get("lifetime_analysis", {})
        self.assertEqual(analysis.get("status"), "fail_closed")
        self.assertEqual(analysis.get("reason"), "dynamic_name_access")
        self.assertTrue(bool(analysis.get("has_dynamic_name_access")))
        vars_info = analysis.get("variables", {})
        self.assertEqual(vars_info.get("x", {}).get("lifetime_class"), "escape_or_unknown")

    def test_pass_respects_non_escape_arg_summary(self) -> None:
        fn = _fn("f", ["a", "b"], [_expr(_name("b"))])
        fn["meta"] = {"escape_summary": {"arg_escape": [True, False]}}
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}

        _ = LifetimeAnalysisPass().run(doc, PassContext(opt_level=1))
        analysis = fn.get("meta", {}).get("lifetime_analysis", {})
        vars_info = analysis.get("variables", {})
        self.assertEqual(vars_info.get("a", {}).get("lifetime_class"), "escape_or_unknown")
        self.assertEqual(vars_info.get("b", {}).get("lifetime_class"), "local_non_escape_candidate")

    def test_pass_is_deterministic(self) -> None:
        fn = _fn("f", ["x"], [_assign("y", _name("x")), _ret(_name("y"))])
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}
        pass_obj = LifetimeAnalysisPass()

        result1 = pass_obj.run(doc, PassContext(opt_level=1))
        summary1 = fn.get("meta", {}).get("lifetime_analysis", {})
        result2 = pass_obj.run(doc, PassContext(opt_level=1))
        summary2 = fn.get("meta", {}).get("lifetime_analysis", {})

        self.assertTrue(result1.changed)
        self.assertFalse(result2.changed)
        self.assertEqual(summary1, summary2)

    def test_pass_handles_loop_and_tuple_unpack_defs(self) -> None:
        loop_stmt = {
            "kind": "For",
            "target": _tuple_target("i", "v"),
            "iter": _name("pairs"),
            "body": [_expr(_name("i")), _expr(_name("v"))],
            "orelse": [],
        }
        fn = _fn("f", ["pairs"], [loop_stmt, _ret(_const(0))])
        doc: dict[str, object] = {"kind": "Module", "east_stage": 3, "meta": {}, "body": [fn]}

        _ = LifetimeAnalysisPass().run(doc, PassContext(opt_level=1))
        analysis = fn.get("meta", {}).get("lifetime_analysis", {})
        defs_index = analysis.get("def_use", {}).get("defs", {})
        uses_index = analysis.get("def_use", {}).get("uses", {})
        self.assertIn("i", defs_index)
        self.assertIn("v", defs_index)
        self.assertIn("pairs", uses_index)
        cfg = analysis.get("cfg", [])
        self.assertTrue(any(isinstance(item, dict) and item.get("kind") == "For" for item in cfg))


if __name__ == "__main__":
    unittest.main()

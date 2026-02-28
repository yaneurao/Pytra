from __future__ import annotations

import unittest

from src.pytra.compiler.east_parts.east3_opt_passes.non_escape_interprocedural_pass import NonEscapeInterproceduralPass
from src.pytra.compiler.east_parts.east3_optimizer import PassContext


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _call_name(id_text: str, args: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "Call", "func": _name(id_text), "args": args, "keywords": []}


def _ret(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Return", "value": value}


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


def _fn(name: str, args: list[str], body: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "arg_order": args, "body": body}


class East3NonEscapeInterproceduralPassTest(unittest.TestCase):
    def test_pass_propagates_arg_escape_through_known_calls(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("sink", ["x"], [_expr(_call_name("unknown_sink", [_name("x")]))]),
                _fn("wrap", ["y"], [_expr(_call_name("sink", [_name("y")]))]),
            ],
        }
        result = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(summary["sink"]["arg_escape"][0])
        self.assertTrue(summary["wrap"]["arg_escape"][0])

    def test_pass_propagates_return_from_args(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("identity", ["x"], [_ret(_name("x"))]),
                _fn("wrap", ["y"], [_ret(_call_name("identity", [_name("y")]))]),
                _fn("wrap2", ["z"], [_ret(_call_name("wrap", [_name("z")]))]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(summary["identity"]["return_from_args"][0])
        self.assertTrue(summary["wrap"]["return_from_args"][0])
        self.assertTrue(summary["wrap2"]["return_from_args"][0])
        self.assertTrue(summary["wrap2"]["return_escape"])

    def test_unknown_call_policy_can_disable_direct_arg_escape(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("sink", ["x"], [_expr(_call_name("unknown_sink", [_name("x")]))]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(
            doc,
            PassContext(
                opt_level=1,
                non_escape_policy={"unknown_call_escape": False},
            ),
        )
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertFalse(summary["sink"]["arg_escape"][0])
        self.assertFalse(summary["sink"]["return_escape"])


if __name__ == "__main__":
    unittest.main()

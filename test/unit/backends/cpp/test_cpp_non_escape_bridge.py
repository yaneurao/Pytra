"""Bridge tests for EAST3 non-escape metadata into C++ emitter state."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.emit.cpp.cli import CppEmitter


class CppNonEscapeBridgeTest(unittest.TestCase):
    def test_emitter_seeds_module_and_function_non_escape_summary(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {
                "non_escape_summary": {
                    "f": {
                        "symbol": "f",
                        "arg_order": ["xs"],
                        "arg_escape": [False],
                        "return_escape": False,
                        "return_from_args": [False],
                        "unresolved_calls": 0,
                    }
                }
            },
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": ["xs"],
                    "arg_types": {"xs": "list[int64]"},
                    "return_type": "None",
                    "body": [{"kind": "Pass"}],
                }
            ],
        }

        em = CppEmitter(doc, {}, emit_main=False)
        _ = em.transpile()

        self.assertIn("f", em.non_escape_summary_map)
        self.assertIn("f", em.function_non_escape_summary_map)
        self.assertEqual(em.function_non_escape_summary_map["f"].get("symbol"), "f")

    def test_emitter_records_non_escape_callsite_meta(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {"non_escape_summary": {}},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "g",
                    "arg_order": ["x"],
                    "arg_types": {"x": "int64"},
                    "return_type": "None",
                    "body": [{"kind": "Pass"}],
                },
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": ["x"],
                    "arg_types": {"x": "int64"},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "g", "resolved_type": "unknown"},
                                "args": [{"kind": "Name", "id": "x", "resolved_type": "int64"}],
                                "keywords": [],
                                "resolved_type": "None",
                                "meta": {
                                    "non_escape_callsite": {
                                        "callee": "g",
                                        "resolved": True,
                                        "callee_return_escape": False,
                                        "callee_arg_escape": [False],
                                    }
                                },
                            },
                        }
                    ],
                },
            ],
        }

        em = CppEmitter(doc, {}, emit_main=False)
        _ = em.transpile()

        records = em.non_escape_callsite_records
        self.assertTrue(len(records) >= 1)
        first = records[0]
        self.assertEqual(first.get("function_symbol"), "f")
        self.assertEqual(first.get("callee"), "g")
        self.assertEqual(first.get("resolved"), True)

    def test_emitter_seeds_function_stack_list_locals_from_optimizer_hint(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {"non_escape_summary": {}},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "meta": {"cpp_value_list_locals_v1": {"version": "1", "locals": ["xs"]}},
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "xs"},
                            "annotation": "list[int64]",
                            "value": {"kind": "List", "elements": []},
                        }
                    ],
                }
            ],
        }

        em = CppEmitter(doc, {}, emit_main=False)

        _ = em.transpile()

        self.assertEqual(em.function_stack_list_locals_map.get("f"), ["xs"])

    def test_emitter_ignores_stack_list_locals_without_optimizer_hint(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {"non_escape_summary": {}},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "xs"},
                            "annotation": "list[int64]",
                            "value": {"kind": "List", "elements": []},
                        }
                    ],
                }
            ],
        }

        em = CppEmitter(doc, {}, emit_main=False)

        _ = em.transpile()

        self.assertEqual(em.function_stack_list_locals_map.get("f"), [])

    def test_emitter_fail_closes_on_malformed_stack_list_locals_hint(self) -> None:
        doc = {
            "kind": "Module",
            "meta": {"non_escape_summary": {}},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "meta": {"cpp_value_list_locals_v1": {"version": "1", "locals": "xs"}},
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "xs"},
                            "annotation": "list[int64]",
                            "value": {"kind": "List", "elements": []},
                        }
                    ],
                }
            ],
        }

        em = CppEmitter(doc, {}, emit_main=False)

        _ = em.transpile()

        self.assertEqual(em.function_stack_list_locals_map.get("f"), [])


if __name__ == "__main__":
    unittest.main()

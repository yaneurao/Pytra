from __future__ import annotations

import unittest

from src.pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import build_non_escape_call_graph
from src.pytra.compiler.east_parts.east3_opt_passes.non_escape_call_graph import strongly_connected_components


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _call_name(id_text: str) -> dict[str, object]:
    return {"kind": "Call", "func": _name(id_text), "args": [], "keywords": []}


def _call_attr(owner: str, attr: str) -> dict[str, object]:
    return {
        "kind": "Call",
        "func": {"kind": "Attribute", "value": _name(owner), "attr": attr},
        "args": [],
        "keywords": [],
    }


def _fn(name: str, body: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "body": body}


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


class East3NonEscapeCallGraphTest(unittest.TestCase):
    def test_build_call_graph_for_top_level_functions(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                _fn("a", [_expr(_call_name("b")), _expr(_call_name("print"))]),
                _fn("b", []),
            ],
        }
        graph, unresolved = build_non_escape_call_graph(doc)
        self.assertEqual(set(graph.keys()), {"a", "b"})
        self.assertEqual(graph["a"], {"b"})
        self.assertEqual(graph["b"], set())
        self.assertEqual(unresolved["a"], 1)  # print
        self.assertEqual(unresolved["b"], 0)

    def test_build_call_graph_for_class_methods(self) -> None:
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ClassDef",
                    "name": "Dog",
                    "body": [
                        _fn("speak", [_expr(_call_attr("self", "growl"))]),
                        _fn("growl", []),
                    ],
                }
            ],
        }
        graph, unresolved = build_non_escape_call_graph(doc)
        self.assertEqual(set(graph.keys()), {"Dog.speak", "Dog.growl"})
        self.assertEqual(graph["Dog.speak"], {"Dog.growl"})
        self.assertEqual(graph["Dog.growl"], set())
        self.assertEqual(unresolved["Dog.speak"], 0)

    def test_scc_detects_mutual_recursion(self) -> None:
        graph = {
            "a": {"b"},
            "b": {"a"},
            "c": {"c"},
            "d": set(),
        }
        sccs = strongly_connected_components(graph)
        got = {frozenset(comp) for comp in sccs}
        self.assertIn(frozenset({"a", "b"}), got)
        self.assertIn(frozenset({"c"}), got)
        self.assertIn(frozenset({"d"}), got)


if __name__ == "__main__":
    unittest.main()

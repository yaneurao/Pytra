from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.parse.py.parse_python import parse_python_file
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2
from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.emit.go.emitter import emit_go_module


def _load_registry() -> object:
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


def _resolve_lower_emit(source: str) -> tuple[dict[str, object], dict[str, object], str]:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "snippet.py"
        src.write_text("from pytra.std.json import JsonVal\n" + source, encoding="utf-8")
        east2 = parse_python_file(str(src))
        east2["source_path"] = "src/app/snippet.py"
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)
        go_code = emit_go_module(east3)
    return east2, east3, go_code


class Toolchain2IsinstanceNarrowingTests(unittest.TestCase):
    def test_boolop_and_narrowing_refines_following_string_method(self) -> None:
        source = """\
def f(stmt: dict[str, JsonVal]) -> str:
    name = stmt.get("name")
    if isinstance(name, str) and name.strip() != "":
        return name.strip()
    return ""
"""
        east2, _east3, go_code = _resolve_lower_emit(source)

        fn2 = next(stmt for stmt in east2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        if2 = next(stmt for stmt in fn2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "If")
        boolop2 = if2["test"]
        assert isinstance(boolop2, dict)
        rhs_compare = boolop2["values"][1]
        assert isinstance(rhs_compare, dict)
        strip_owner = rhs_compare["left"]["func"]["value"]
        assert isinstance(strip_owner, dict)
        self.assertEqual(strip_owner.get("resolved_type"), "str")

        self.assertIn("py_str_strip(name.(string))", go_code)
        self.assertNotIn("name.strip()", go_code)

    def test_fallthrough_narrowing_refines_jsonval_list_loop_target(self) -> None:
        source = """\
def f(east_doc: dict[str, JsonVal]) -> dict[str, str]:
    symbols: dict[str, str] = {}
    body_val = east_doc.get("body")
    if not isinstance(body_val, list):
        return symbols
    for stmt in body_val:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
    return symbols
"""
        east2, east3, go_code = _resolve_lower_emit(source)

        fn2 = next(stmt for stmt in east2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        for2 = next(stmt for stmt in fn2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "For")
        assign2 = next(stmt for stmt in for2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "Assign")
        owner2 = assign2["value"]["func"]["value"]
        assert isinstance(owner2, dict)
        self.assertEqual(owner2.get("resolved_type"), "dict[str,JsonVal]")

        fn3 = next(stmt for stmt in east3["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        for3 = next(stmt for stmt in fn3["body"] if isinstance(stmt, dict) and stmt.get("kind") == "ForCore")
        iter_expr = for3["iter_plan"]["iter_expr"]
        target_plan = for3["target_plan"]
        assert isinstance(iter_expr, dict)
        assert isinstance(target_plan, dict)
        self.assertEqual(iter_expr.get("resolved_type"), "list[JsonVal]")
        self.assertEqual(target_plan.get("target_type"), "JsonVal")

        self.assertIn("for _, stmt := range body_val.([]any)", go_code)
        self.assertIn("stmt.(map[string]any)[\"kind\"]", go_code)
        self.assertNotIn("stmt.get(\"kind\")", go_code)
        self.assertNotIn(".(*list)", go_code)
        self.assertNotIn(".(*dict)", go_code)

    def test_ifexp_isinstance_narrowing_refines_optional_dict_value(self) -> None:
        source = """\
def f(node: JsonVal) -> str:
    owner = node
    owner_node = owner if isinstance(owner, dict) else None
    if owner_node is None:
        return ""
    return owner_node.get("kind") if isinstance(owner_node.get("kind"), str) else ""
"""
        _east2, _east3, go_code = _resolve_lower_emit(source)

        self.assertIn("owner_node := func() map[string]any", go_code)
        self.assertIn("owner_node[\"kind\"]", go_code)
        self.assertNotIn("owner_node.get(", go_code)

    def test_container_unbox_prefers_narrowed_generic_container_type(self) -> None:
        source = """\
def f(node: JsonVal) -> None:
    if isinstance(node, dict):
        for value in node.values():
            print(value)
    elif isinstance(node, list):
        for item in node:
            print(item)
"""
        _east2, _east3, go_code = _resolve_lower_emit(source)

        self.assertNotIn(".(*dict)", go_code)
        self.assertNotIn(".(*list)", go_code)
        self.assertIn("for _, item := range node.([]any)", go_code)

    def test_or_guard_continue_narrows_dict_loop_variable_for_following_uses(self) -> None:
        source = """\
def f(class_body: list[JsonVal]) -> str:
    out = ""
    for method in class_body:
        if not isinstance(method, dict) or method.get("kind") != "FunctionDef":
            continue
        method_name = method.get("name")
        if isinstance(method_name, str):
            out = method_name
    return out
"""
        east2, east3, go_code = _resolve_lower_emit(source)

        fn2 = next(stmt for stmt in east2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        for2 = next(stmt for stmt in fn2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "For")
        method_assign = next(stmt for stmt in for2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "Assign")
        owner2 = method_assign["value"]["func"]["value"]
        assert isinstance(owner2, dict)
        self.assertEqual(owner2.get("resolved_type"), "dict[str,JsonVal]")

        fn3 = next(stmt for stmt in east3["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        for3 = next(stmt for stmt in fn3["body"] if isinstance(stmt, dict) and stmt.get("kind") == "ForCore")
        if3 = next(stmt for stmt in for3["body"] if isinstance(stmt, dict) and stmt.get("kind") == "If")
        test3 = if3["test"]
        assert isinstance(test3, dict)
        rhs3 = test3["values"][1]
        assert isinstance(rhs3, dict)
        rhs_owner = rhs3["left"]["func"]["value"]
        assert isinstance(rhs_owner, dict)
        self.assertEqual(rhs_owner.get("resolved_type"), "dict[str,JsonVal]")

        self.assertIn("method.(map[string]any)[\"kind\"]", go_code)
        self.assertIn("method.(map[string]any)[\"name\"]", go_code)
        self.assertNotIn("method.get(", go_code)

    def test_reassignment_invalidates_narrowing_for_following_uses(self) -> None:
        source = """\
def f(node: JsonVal, other: JsonVal) -> str:
    out = ""
    if isinstance(node, dict):
        out = node.get("kind") if isinstance(node.get("kind"), str) else ""
        node = other
        if isinstance(node, dict):
            out = node.get("name") if isinstance(node.get("name"), str) else out
    return out
"""
        east2, _east3, _go_code = _resolve_lower_emit(source)

        fn2 = next(stmt for stmt in east2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef")
        if2 = next(stmt for stmt in fn2["body"] if isinstance(stmt, dict) and stmt.get("kind") == "If")
        body2 = if2["body"]
        assert isinstance(body2, list)
        nested_if2 = next(stmt for stmt in body2 if isinstance(stmt, dict) and stmt.get("kind") == "If")
        test2 = nested_if2["test"]
        assert isinstance(test2, dict)
        self.assertEqual(test2.get("resolved_type"), "bool")
        self.assertEqual(test2["args"][0].get("resolved_type"), "JsonVal")

        nested_body2 = nested_if2["body"]
        assert isinstance(nested_body2, list)
        nested_assign2 = next(stmt for stmt in nested_body2 if isinstance(stmt, dict) and stmt.get("kind") == "Assign")
        owner2 = nested_assign2["value"]["body"]["func"]["value"]
        assert isinstance(owner2, dict)
        self.assertEqual(owner2.get("resolved_type"), "dict[str,JsonVal]")

        reassign2 = next(
            stmt
            for stmt in body2
            if isinstance(stmt, dict)
            and stmt.get("kind") == "Assign"
            and isinstance(stmt.get("target"), dict)
            and stmt["target"].get("id") == "node"
        )
        value2 = reassign2["value"]
        assert isinstance(value2, dict)
        self.assertEqual(value2.get("resolved_type"), "JsonVal")


if __name__ == "__main__":
    unittest.main()

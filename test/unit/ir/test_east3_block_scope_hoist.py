"""Unit tests for EAST3 block-scope variable hoist pass."""

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

from src.toolchain.compile.east2_to_east3_block_scope_hoist import (
    _collect_assigned_names_in_stmts,
    _collect_referenced_names,
    _hoist_block_scope_vars_in_stmt_list,
    hoist_block_scope_variables,
)
from src.toolchain.compile.core_entrypoints import convert_source_to_east_with_backend
from src.toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3


def _build_east3(source: str) -> dict[str, object]:
    """Convert Python source to EAST3 (with hoist pass applied)."""
    east = convert_source_to_east_with_backend(
        source,
        filename="test.py",
        parser_backend="self_hosted",
    )
    return lower_east2_to_east3(east)


def _find_function_body(east3: dict[str, object], func_name: str) -> list[dict[str, object]]:
    """Find the body of a FunctionDef by name."""
    body = east3.get("body", [])
    for stmt in body:
        if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef" and stmt.get("name") == func_name:
            return stmt.get("body", [])
        if isinstance(stmt, dict) and stmt.get("kind") == "ClassDef":
            for m in stmt.get("body", []):
                if isinstance(m, dict) and m.get("kind") == "FunctionDef" and m.get("name") == func_name:
                    return m.get("body", [])
    return []


def _collect_var_decls(stmts: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collect VarDecl nodes from a statement list (non-recursive)."""
    return [s for s in stmts if isinstance(s, dict) and s.get("kind") == "VarDecl"]


def _collect_var_decl_names(stmts: list[dict[str, object]]) -> set[str]:
    """Collect names from VarDecl nodes."""
    return {s["name"] for s in _collect_var_decls(stmts) if isinstance(s.get("name"), str)}


class TestCollectAssignedNames(unittest.TestCase):
    """Tests for _collect_assigned_names_in_stmts helper."""

    def test_simple_assign(self) -> None:
        stmts = [
            {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
        ]
        result = _collect_assigned_names_in_stmts(stmts)
        self.assertIn("x", result)
        self.assertEqual(result["x"], "int64")

    def test_nested_if_assign(self) -> None:
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "a"}, "decl_type": "str"},
                ],
                "orelse": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "b"}, "decl_type": "int64"},
                ],
            },
        ]
        result = _collect_assigned_names_in_stmts(stmts)
        self.assertIn("a", result)
        self.assertIn("b", result)


class TestCollectReferencedNames(unittest.TestCase):
    """Tests for _collect_referenced_names helper."""

    def test_name_reference(self) -> None:
        node = {"kind": "Name", "id": "x"}
        result = _collect_referenced_names(node)
        self.assertIn("x", result)

    def test_nested_reference(self) -> None:
        node = {
            "kind": "Return",
            "value": {
                "kind": "BinOp",
                "left": {"kind": "Name", "id": "a"},
                "right": {"kind": "Name", "id": "b"},
            },
        }
        result = _collect_referenced_names(node)
        self.assertIn("a", result)
        self.assertIn("b", result)


class TestHoistBlockScopeVars(unittest.TestCase):
    """Tests for the core hoist pass on raw statement lists."""

    def test_if_else_both_branches(self) -> None:
        """Variable assigned in both if/else branches and used after."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
                ],
                "orelse": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
                ],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "x"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        var_decls = _collect_var_decl_names(result)
        self.assertIn("x", var_decls)
        # VarDecl should appear before the If
        kinds = [s.get("kind") for s in result if isinstance(s, dict)]
        self.assertEqual(kinds[0], "VarDecl")
        self.assertEqual(kinds[1], "If")

    def test_if_only_no_else(self) -> None:
        """Variable assigned only in if branch, used after → should hoist."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "y"}, "decl_type": "str"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "y"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertIn("y", _collect_var_decl_names(result))

    def test_no_hoist_when_not_used_after(self) -> None:
        """Variable assigned in block but NOT used after → no hoist."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "z"}, "decl_type": "int64"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Constant", "value": 0},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertEqual(len(_collect_var_decls(result)), 0)

    def test_no_hoist_when_already_declared(self) -> None:
        """Variable already assigned before block → no hoist."""
        stmts = [
            {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "x"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertEqual(len(_collect_var_decls(result)), 0)

    def test_no_hoist_when_param(self) -> None:
        """Variable is a function parameter → no hoist."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "x"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, {"x"})
        self.assertEqual(len(_collect_var_decls(result)), 0)

    def test_for_loop_hoist(self) -> None:
        """Variable assigned in for loop body and used after."""
        stmts = [
            {
                "kind": "ForCore",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "result"}, "decl_type": "str"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "result"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertIn("result", _collect_var_decl_names(result))

    def test_while_loop_hoist(self) -> None:
        """Variable assigned in while loop body and used after."""
        stmts = [
            {
                "kind": "While",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "acc"}, "decl_type": "int64"},
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "acc"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertIn("acc", _collect_var_decl_names(result))

    def test_nested_if_in_for(self) -> None:
        """Variable assigned in nested if inside a for loop, used after for."""
        stmts = [
            {
                "kind": "ForCore",
                "body": [
                    {
                        "kind": "If",
                        "body": [
                            {"kind": "Assign", "target": {"kind": "Name", "id": "found"}, "decl_type": "bool"},
                        ],
                        "orelse": [],
                    },
                ],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "found"},
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertIn("found", _collect_var_decl_names(result))

    def test_is_reassign_flag_set(self) -> None:
        """Assign inside block gets is_reassign=True for hoisted variable."""
        body_assign = {"kind": "Assign", "target": {"kind": "Name", "id": "x"}, "decl_type": "int64"}
        stmts = [
            {
                "kind": "If",
                "body": [body_assign],
                "orelse": [],
            },
            {
                "kind": "Return",
                "value": {"kind": "Name", "id": "x"},
            },
        ]
        _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertTrue(body_assign.get("is_reassign"))

    def test_multiple_vars_hoisted(self) -> None:
        """Multiple variables from same block are all hoisted."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "a"}, "decl_type": "str"},
                    {"kind": "Assign", "target": {"kind": "Name", "id": "b"}, "decl_type": "int64"},
                ],
                "orelse": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "a"}, "decl_type": "str"},
                    {"kind": "Assign", "target": {"kind": "Name", "id": "b"}, "decl_type": "int64"},
                ],
            },
            {
                "kind": "Return",
                "value": {
                    "kind": "BinOp",
                    "left": {"kind": "Name", "id": "a"},
                    "right": {"kind": "Name", "id": "b"},
                },
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        decl_names = _collect_var_decl_names(result)
        self.assertIn("a", decl_names)
        self.assertIn("b", decl_names)


    def test_multi_branch_no_use_after(self) -> None:
        """Variable assigned in multiple if/elif/else branches, not used after block.
        Must still be hoisted because each branch is a separate block scope."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "ph"}, "decl_type": "int64"},
                ],
                "orelse": [
                    {
                        "kind": "If",
                        "body": [
                            {"kind": "Assign", "target": {"kind": "Name", "id": "ph"}, "decl_type": "int64"},
                        ],
                        "orelse": [
                            {"kind": "Assign", "target": {"kind": "Name", "id": "ph"}, "decl_type": "int64"},
                        ],
                    },
                ],
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertIn("ph", _collect_var_decl_names(result))

    def test_single_branch_no_use_after_no_hoist(self) -> None:
        """Variable assigned in only one branch, not used after → no hoist."""
        stmts = [
            {
                "kind": "If",
                "body": [
                    {"kind": "Assign", "target": {"kind": "Name", "id": "z"}, "decl_type": "int64"},
                    {"kind": "Expr", "value": {"kind": "Name", "id": "z"}},
                ],
                "orelse": [],
            },
        ]
        result = _hoist_block_scope_vars_in_stmt_list(stmts, set())
        self.assertEqual(len(_collect_var_decls(result)), 0)


class TestHoistE2E(unittest.TestCase):
    """End-to-end tests: Python source → EAST3 with hoist applied."""

    def test_if_else_hoist_e2e(self) -> None:
        """if/else branch assignment is hoisted in EAST3."""
        source = """def choose(flag: bool) -> str:
    if flag:
        x = "yes"
    else:
        x = "no"
    return x
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "choose")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("x", decl_names)

    def test_for_loop_hoist_e2e(self) -> None:
        """Variable assigned inside for loop and used after is hoisted."""
        source = """def process(items: list[int]) -> int:
    for item in items:
        result = item + 1
    return result
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "process")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("result", decl_names)

    def test_while_loop_hoist_e2e(self) -> None:
        """Variable assigned inside while loop and used after is hoisted."""
        source = """def countdown(n: int) -> int:
    while n > 0:
        last = n
        n = n - 1
    return last
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "countdown")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("last", decl_names)

    def test_nested_if_else_hoist_e2e(self) -> None:
        """Nested if/else blocks hoist correctly."""
        source = """def nested(a: bool, b: bool) -> str:
    if a:
        if b:
            x = "ab"
        else:
            x = "a"
    else:
        x = "none"
    return x
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "nested")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("x", decl_names)


    def test_if_elif_else_multi_branch_hoist_e2e(self) -> None:
        """Variable assigned in all if/elif/else branches but not used after.
        Must be hoisted because each branch is a separate block scope."""
        source = """def place(kind: int) -> int:
    if kind == 0:
        ph = 3
        for i in range(ph):
            pw = 4
    elif kind == 1:
        ph = 5
        for i in range(ph):
            pw = 6
    else:
        ph = 7
        for i in range(ph):
            pw = 8
    return 0
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "place")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("ph", decl_names)
        self.assertIn("pw", decl_names)

    def test_two_branch_if_else_multi_branch_hoist_e2e(self) -> None:
        """Variable assigned in both if and else branches, not used after."""
        source = """def pick(flag: bool) -> int:
    if flag:
        val = 10
    else:
        val = 20
    return 0
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "pick")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertIn("val", decl_names)

    def test_multi_branch_hoist_not_triggered_for_single_branch(self) -> None:
        """Variable assigned in only one branch, not used after → no hoist."""
        source = """def maybe(flag: bool) -> int:
    if flag:
        tmp = 99
    return 0
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "maybe")
        self.assertTrue(len(body) > 0, "Function body not found")
        decl_names = _collect_var_decl_names(body)
        self.assertNotIn("tmp", decl_names)


class TestHoistCppEmitter(unittest.TestCase):
    """Verify C++ emitter correctly handles VarDecl from hoist pass."""

    def test_cpp_output_contains_hoisted_decl(self) -> None:
        from src.toolchain.emit.cpp.cli import load_east, transpile_to_cpp
        source = """def choose_sep(use_default: bool) -> str:
    if use_default:
        item_sep = ","
        key_sep = ":"
    else:
        item_sep = ";"
        key_sep = "="
    return item_sep + key_sep
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_py = Path(tmpdir) / "hoist_test.py"
            src_py.write_text(source, encoding="utf-8")
            east = load_east(src_py)
            cpp = transpile_to_cpp(east)

        self.assertIn("str item_sep;", cpp)
        self.assertIn("str key_sep;", cpp)
        self.assertIn("return item_sep + key_sep;", cpp)


class TestHoistDartEmitter(unittest.TestCase):
    """Verify Dart emitter correctly handles VarDecl from hoist pass."""

    def test_dart_output_contains_hoisted_decl(self) -> None:
        from src.toolchain.emit.dart.emitter import transpile_to_dart_native
        source = """def choose(flag: bool) -> str:
    if flag:
        x = "yes"
    else:
        x = "no"
    return x
"""
        east3 = _build_east3(source)
        dart = transpile_to_dart_native(east3)

        # str is a nil-free type in Dart, so no "late" keyword
        self.assertIn("String x;", dart)
        # Assignments inside blocks should be reassignments (no type prefix)
        self.assertNotIn("String x = ", dart)


class TestHoistZigEmitter(unittest.TestCase):
    """Verify Zig emitter correctly handles VarDecl from hoist pass."""

    def test_zig_output_contains_hoisted_decl(self) -> None:
        from src.toolchain.emit.zig.emitter import transpile_to_zig_native
        source = """def choose(flag: bool) -> str:
    if flag:
        x = "yes"
    else:
        x = "no"
    return x
"""
        east3 = _build_east3(source)
        zig = transpile_to_zig_native(east3)

        # Zig should have: var x: ... = undefined;
        self.assertIn("var x:", zig)
        self.assertIn("= undefined;", zig)


class TestHoistJuliaEmitter(unittest.TestCase):
    """Verify Julia emitter correctly handles VarDecl from hoist pass."""

    def test_julia_output_contains_hoisted_decl(self) -> None:
        from src.toolchain.emit.julia.emitter import transpile_to_julia_native
        source = """def choose(flag: bool) -> str:
    if flag:
        x = "yes"
    else:
        x = "no"
    return x
"""
        east3 = _build_east3(source)
        julia = transpile_to_julia_native(east3)

        self.assertIn("x = nothing", julia)


if __name__ == "__main__":
    unittest.main()

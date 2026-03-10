"""Unit regression tests for the self_hosted EAST converter."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import _walk
from src.toolchain.compiler.east import EastBuildError
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreTest(unittest.TestCase):


    def test_core_does_not_reintroduce_perf_counter_direct_branch(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "perf_counter"', src)
        self.assertNotIn("fn_name == 'perf_counter'", src)

    def test_core_does_not_reintroduce_path_direct_branches(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "Path"', src)
        self.assertNotIn("fn_name == 'Path'", src)
        self.assertNotIn('owner_t == "Path"', src)
        self.assertNotIn("owner_t == 'Path'", src)

    def test_core_semantic_tag_mapping_is_adapter_driven(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("lookup_builtin_semantic_tag", src)
        self.assertIn("lookup_stdlib_function_semantic_tag", src)
        self.assertIn("lookup_stdlib_symbol_semantic_tag", src)
        self.assertIn("lookup_stdlib_method_semantic_tag", src)
        self.assertNotIn('payload["semantic_tag"] = "', src)


    def test_identifier_prefixed_with_import_is_not_import_stmt(self) -> None:
        src = """
def f() -> None:
    import_modules: dict[str, str] = {}
    print(import_modules)

if __name__ == "__main__":
    f()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        ann = [n for n in body if isinstance(n, dict) and n.get("kind") == "AnnAssign"]
        self.assertEqual(len(ann), 1)
        target = ann[0].get("target")
        self.assertIsInstance(target, dict)
        self.assertEqual(target.get("id"), "import_modules")


    def test_super_call_is_parsed(self) -> None:
        src = """
class Base:
    def __init__(self) -> None:
        self.x: int = 1

class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.x += 1

def main() -> None:
    c: Child = Child()
    print(c.x)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_super = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Attribute"
            and isinstance(c.get("func", {}).get("value"), dict)
            and c.get("func", {}).get("value", {}).get("kind") == "Call"
            and isinstance(c.get("func", {}).get("value", {}).get("func"), dict)
            and c.get("func", {}).get("value", {}).get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("value", {}).get("func", {}).get("id") == "super"
            for c in calls
        )
        self.assertTrue(has_super)

    def test_bare_return_is_parsed_as_return_stmt(self) -> None:
        src = """
def f(flag: bool) -> None:
    if flag:
        return
    print(1)

def main() -> None:
    f(True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        returns = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Return"]
        self.assertGreaterEqual(len(returns), 1)
        bare = [r for r in returns if r.get("value") is None]
        self.assertGreaterEqual(len(bare), 1)

    def test_arg_usage_tracks_reassigned_parameters(self) -> None:
        src = """
def f(x: int, y: int, z: int, w: int) -> int:
    x = x + 1
    for y in range(2):
        z += y
    return x + z + w
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_usage = fn.get("arg_usage", {})
        self.assertEqual(arg_usage.get("x"), "reassigned")
        self.assertEqual(arg_usage.get("y"), "reassigned")
        self.assertEqual(arg_usage.get("z"), "reassigned")
        self.assertEqual(arg_usage.get("w"), "readonly")

    def test_arg_usage_ignores_nested_scope_reassignment(self) -> None:
        src = """
def outer(a: int) -> int:
    def inner(a: int) -> int:
        a = a + 1
        return a
    return inner(a)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        outer_funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "outer"]
        self.assertEqual(len(outer_funcs), 1)
        outer = outer_funcs[0]
        outer_usage = outer.get("arg_usage", {})
        self.assertEqual(outer_usage.get("a"), "readonly")

        inner_funcs = [n for n in _walk(outer.get("body", [])) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"]
        self.assertEqual(len(inner_funcs), 1)
        inner = inner_funcs[0]
        inner_usage = inner.get("arg_usage", {})
        self.assertEqual(inner_usage.get("a"), "reassigned")

    def test_trailing_semicolon_is_rejected(self) -> None:
        src = """
def main() -> None:
    x: int = 1;
    print(x)
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("statement terminator", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

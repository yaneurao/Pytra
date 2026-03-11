"""Parser behavior regressions for expression-oriented syntax lanes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import _walk
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorExprsTest(unittest.TestCase):
    def test_dict_set_comprehension_infers_target_type(self) -> None:
        src = """
def main() -> None:
    xs: list[int] = [1, 2, 3, 4]
    ys: set[int] = {x * x for x in xs if x % 2 == 1}
    ds: dict[int, int] = {x: x * x for x in xs if x % 2 == 0}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        dict_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "DictComp"]
        set_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "SetComp"]
        self.assertEqual(len(dict_comps), 1)
        self.assertEqual(len(set_comps), 1)
        dc = dict_comps[0]
        sc = set_comps[0]
        self.assertEqual(dc.get("resolved_type"), "dict[int64,int64]")
        self.assertEqual(sc.get("resolved_type"), "set[int64]")
        self.assertEqual(dc.get("key", {}).get("resolved_type"), "int64")
        self.assertEqual(dc.get("value", {}).get("resolved_type"), "int64")
        self.assertEqual(sc.get("elt", {}).get("resolved_type"), "int64")
        d_ifs = dc.get("generators", [{}])[0].get("ifs", [])
        s_ifs = sc.get("generators", [{}])[0].get("ifs", [])
        self.assertEqual(len(d_ifs), 1)
        self.assertEqual(len(s_ifs), 1)

    def test_list_comprehension_over_range_uses_range_expr(self) -> None:
        src = """
def main() -> list[int]:
    return [x for x in range(3)]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        list_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ListComp"]
        self.assertEqual(len(list_comps), 1)
        generators = list_comps[0].get("generators", [])
        self.assertEqual(len(generators), 1)
        iter_node = generators[0].get("iter", {})
        self.assertEqual(iter_node.get("kind"), "RangeExpr")
        self.assertEqual(iter_node.get("range_mode"), "ascending")
        self.assertEqual(iter_node.get("start", {}).get("value"), 0)
        self.assertEqual(iter_node.get("stop", {}).get("value"), 3)
        self.assertEqual(iter_node.get("step", {}).get("value"), 1)

    def test_lambda_expression_builds_lambda_node(self) -> None:
        src = """
def main() -> None:
    fn = lambda x: x + 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        lambdas = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Lambda"]
        self.assertEqual(len(lambdas), 1)
        lam = lambdas[0]
        self.assertEqual([arg.get("arg") for arg in lam.get("args", [])], ["x"])
        self.assertEqual(lam.get("body", {}).get("kind"), "BinOp")

    def test_fstring_builds_joinedstr_and_formatted_value_nodes(self) -> None:
        src = """
def main(name: str) -> str:
    return f"hello {name}"
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        joined = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "JoinedStr"]
        self.assertEqual(len(joined), 1)
        values = joined[0].get("values", [])
        formatted = [v for v in values if isinstance(v, dict) and v.get("kind") == "FormattedValue"]
        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0].get("value", {}).get("kind"), "Name")
        self.assertEqual(formatted[0].get("value", {}).get("id"), "name")

    def test_except_without_as_is_supported(self) -> None:
        src = """
def f(x: str) -> bool:
    try:
        _ = int(x)
        return True
    except ValueError:
        return False

def main() -> None:
    print(f("12"))

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        try_nodes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Try"]
        self.assertEqual(len(try_nodes), 1)
        handlers = try_nodes[0].get("handlers", [])
        self.assertEqual(len(handlers), 1)
        self.assertIsNone(handlers[0].get("name"))

    def test_numeric_literal_prefixes_are_parsed(self) -> None:
        src = """
def main() -> int:
    a: int = 0xFF
    b: int = 0X10
    return a + b
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        constants = [n.get("value") for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Constant"]
        self.assertIn(255, constants)
        self.assertIn(16, constants)

    def test_bitwise_invert_is_parsed_as_unaryop(self) -> None:
        src = """
def main(x: int, y: int) -> int:
    return x & ~y
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        unary_nodes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "UnaryOp"]
        self.assertEqual(len(unary_nodes), 1)
        unary = unary_nodes[0]
        self.assertEqual(unary.get("op"), "Invert")
        self.assertEqual(unary.get("resolved_type"), "int64")
        operand = unary.get("operand", {})
        self.assertEqual(operand.get("kind"), "Name")
        self.assertEqual(operand.get("id"), "y")

    def test_starred_call_tuple_arg_is_parsed_as_starred_expr(self) -> None:
        src = """
def mix_rgb(r: int, g: int, b: int) -> int:
    return (r << 16) | (g << 8) | b

def main(rgb: tuple[int, int, int]) -> int:
    return mix_rgb(*rgb)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        self.assertGreaterEqual(len(calls), 1)
        starred_args = [
            arg
            for call in calls
            for arg in call.get("args", [])
            if isinstance(arg, dict) and arg.get("kind") == "Starred"
        ]
        self.assertEqual(len(starred_args), 1)
        starred = starred_args[0]
        self.assertEqual(starred.get("resolved_type"), "tuple[int64,int64,int64]")
        value = starred.get("value", {})
        self.assertEqual(value.get("kind"), "Name")
        self.assertEqual(value.get("id"), "rgb")

    def test_parser_accepts_bom_line_continuation_and_pow(self) -> None:
        src = """\ufefffrom pytra.std import math

def main() -> None:
    x: int = 1 + \\
        2
    y: float = math.sqrt(float(x ** 2))
    print(x, y)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        binops = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "BinOp"]
        has_pow = any(b.get("op") == "Pow" for b in binops)
        self.assertTrue(has_pow)

    def test_parser_accepts_top_level_expr_class_pass_nested_def_and_tuple_trailing_comma(self) -> None:
        src = """
class E:
    X = 0,
    pass

def outer() -> int:
    def inner(x: int) -> int:
        return x + 1
    return inner(2)

print(outer())
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "E"]
        self.assertEqual(len(classes), 1)
        tuples = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Tuple"]
        self.assertGreaterEqual(len(tuples), 1)
        nested_fns = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"
        ]
        self.assertEqual(len(nested_fns), 1)
        exprs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Expr"]
        self.assertGreaterEqual(len(exprs), 1)

    def test_yield_is_parsed_as_generator_function(self) -> None:
        src = """
def gen(n: int) -> int:
    i: int = 0
    while i < n:
        yield i
        i += 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        self.assertEqual(fn.get("return_type"), "list[int64]")
        yields = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertGreaterEqual(len(yields), 1)

    def test_single_line_for_with_yield_is_parsed(self) -> None:
        src = """
def gen() -> int:
    for _ in range(3): yield 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        for_ranges = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "ForRange"]
        self.assertEqual(len(for_ranges), 1)
        yields = [n for n in _walk(for_ranges[0].get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertEqual(len(yields), 1)

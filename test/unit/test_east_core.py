"""Unit regression tests for the self_hosted EAST converter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.east import convert_source_to_east_with_backend
from src.pytra.compiler.east import EastBuildError


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for it in node:
            yield from _walk(it)


class EastCoreTest(unittest.TestCase):
    def test_quoted_type_annotation_is_normalized(self) -> None:
        src = """
def f(p: "Path", xs: "list[int]") -> "Path":
    return p
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_types = fn.get("arg_types", {})
        self.assertEqual(arg_types.get("p"), "Path")
        self.assertEqual(arg_types.get("xs"), "list[int64]")
        self.assertEqual(fn.get("return_type"), "Path")

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

    def test_builtin_call_lowering_for_common_methods(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    s: str = "  abc  "
    t: str = s.strip()
    xs: list[int] = []
    xs.append(1)
    d: dict[str, int] = {"a": 1}
    v: int = d.get("a", 0)
    p: Path = Path("tmp")
    ok: bool = p.exists()
    print(len(xs), t, v, ok)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        runtime_calls = {str(n.get("runtime_call")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)

    def test_path_mkdir_keywords_are_kept(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out")
    p.mkdir(parents=True, exist_ok=True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        mkdir_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("runtime_call") == "std::filesystem::create_directories"
        ]
        self.assertEqual(len(mkdir_calls), 1)
        kws = mkdir_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertIn("parents", names)
        self.assertIn("exist_ok", names)

    def test_raw_range_call_is_lowered_out(self) -> None:
        src = """
def main() -> None:
    s: int = 0
    for i in range(3):
        s += i
    print(s)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_raw_range = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("id") == "range"
            for c in calls
        )
        self.assertFalse(has_raw_range)
        has_for_range = any(
            isinstance(n, dict) and n.get("kind") == "ForRange"
            for n in _walk(east)
        )
        self.assertTrue(has_for_range)

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

    def test_object_receiver_access_is_rejected(self) -> None:
        src = """
def f(x: object) -> int:
    return x.bit_length()

def main() -> None:
    print(f(1))

if __name__ == "__main__":
    main()
"""
        with self.assertRaises((EastBuildError, RuntimeError)):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

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

    def test_class_storage_hint_override_is_supported(self) -> None:
        src = """
class Box:
    __pytra_class_storage_hint__ = "value"

    def __init__(self, x: int) -> None:
        self.x = x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("class_storage_hint"), "value")
        names = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    names.append(tgt.get("id"))
        self.assertNotIn("__pytra_class_storage_hint__", names)

    def test_enum_members_are_parsed_in_class_body(self) -> None:
        src = """
from pytra.std.enum import Enum

class Color(Enum):
    RED = 1
    BLUE = 2
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Color"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("base"), "Enum")
        self.assertEqual(cls.get("class_storage_hint"), "value")
        members: list[str] = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    members.append(str(tgt.get("id", "")))
        self.assertIn("RED", members)
        self.assertIn("BLUE", members)

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

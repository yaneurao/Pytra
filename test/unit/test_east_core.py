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
    u: str = s.lstrip()
    p0: int = s.find("a")
    p1: int = s.rfind("a")
    blob: bytes = bytes()
    ba: bytearray = bytearray(blob)
    xs: list[int] = []
    xs.append(1)
    zp = zip(xs, xs)
    n: int = int("10", 16)
    o: object = xs
    b: bool = bool(o)
    it = iter(xs)
    first = next(it)
    ri = reversed(xs)
    en = enumerate(xs, 1)
    has_any: bool = any(xs)
    has_all: bool = all(xs)
    ch: str = chr(65)
    ocode: int = ord("A")
    r = range(3)
    ys: list[int] = list(xs)
    zs: set[int] = set(xs)
    d: dict[str, int] = {"a": 1}
    d2: dict[str, int] = dict(d)
    v: int = d.get("a", 0)
    p: Path = Path("tmp")
    ok: bool = p.exists()
    print(len(xs), t, u, p0, p1, len(ba), n, b, first, ri, en, zp, has_any, has_all, ch, ocode, len(ys), len(zs), len(d2), v, ok)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        runtime_calls = {str(n.get("runtime_call")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("py_lstrip", runtime_calls)
        self.assertIn("py_find", runtime_calls)
        self.assertIn("py_rfind", runtime_calls)
        self.assertIn("bytes_ctor", runtime_calls)
        self.assertIn("bytearray_ctor", runtime_calls)
        self.assertIn("py_iter_or_raise", runtime_calls)
        self.assertIn("py_next_or_stop", runtime_calls)
        self.assertIn("py_reversed", runtime_calls)
        self.assertIn("py_enumerate", runtime_calls)
        self.assertIn("zip", runtime_calls)
        self.assertIn("py_any", runtime_calls)
        self.assertIn("py_all", runtime_calls)
        self.assertIn("py_ord", runtime_calls)
        self.assertIn("py_chr", runtime_calls)
        self.assertIn("py_range", runtime_calls)
        self.assertIn("list_ctor", runtime_calls)
        self.assertIn("set_ctor", runtime_calls)
        self.assertIn("dict_ctor", runtime_calls)
        self.assertIn("py_to_bool", runtime_calls)
        self.assertIn("py_to_int64_base", runtime_calls)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)

    def test_perf_counter_resolved_type_comes_from_stdlib_signature(self) -> None:
        src = """
from pytra.std.time import perf_counter

def main() -> float:
    t0: float = perf_counter()
    return t0
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "perf_counter"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("resolved_type"), "float64")

    def test_core_does_not_reintroduce_perf_counter_direct_branch(self) -> None:
        core_path = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "core.py"
        src = core_path.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "perf_counter"', src)
        self.assertNotIn("fn_name == 'perf_counter'", src)

    def test_core_does_not_reintroduce_path_direct_branches(self) -> None:
        core_path = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "core.py"
        src = core_path.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "Path"', src)
        self.assertNotIn("fn_name == 'Path'", src)
        self.assertNotIn('owner_t == "Path"', src)
        self.assertNotIn("owner_t == 'Path'", src)

    def test_path_constructor_is_resolved_via_import_binding(self) -> None:
        src = """
from pathlib import Path as P
from pytra.std.pathlib import Path as PP

def main() -> None:
    p = P("out")
    q = PP("tmp")
    r = p / "a.txt"
    print(q, r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        path_ctor_calls = [
            n
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and n.get("runtime_call") == "Path"
        ]
        self.assertEqual(len(path_ctor_calls), 2)
        for call in path_ctor_calls:
            self.assertEqual(call.get("resolved_type"), "Path")

        path_div_binops = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "BinOp"
            and n.get("op") == "Div"
            and n.get("resolved_type") == "Path"
        ]
        self.assertEqual(len(path_div_binops), 1)

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

    def test_range_keywords_are_kept_for_builtin_call(self) -> None:
        src = """
def main() -> None:
    r = range(start=1, stop=5, step=2)
    print(r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        range_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "py_range"
        ]
        self.assertEqual(len(range_calls), 1)
        kws = range_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertEqual(names, ["start", "stop", "step"])

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

    def test_builtin_call_nodes_always_have_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], s: str, p: Path) -> None:
    _ = print(len(xs), str(1), int("10", 16), bool(xs), range(3), zip(xs, xs))
    _ = s.strip()
    _ = s.find("x")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        builtin_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        self.assertGreater(len(builtin_calls), 0)
        missing_runtime = [
            n
            for n in builtin_calls
            if not isinstance(n.get("runtime_call"), str) or str(n.get("runtime_call")) == ""
        ]
        self.assertEqual(missing_runtime, [])

    def test_builtin_method_calls_keep_runtime_owner(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], d: dict[str, int], s: str, n: int, p: Path) -> None:
    xs.append(1)
    _ = d.get("a", 0)
    _ = s.strip()
    _ = n.to_bytes(2, "little")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        target_runtime_calls = {"list.append", "dict.get", "py_strip", "py_int_to_bytes", "std::filesystem::exists"}
        targets = [c for c in calls if str(c.get("runtime_call")) in target_runtime_calls]
        self.assertEqual(len(targets), 5)
        for c in targets:
            owner = c.get("runtime_owner")
            self.assertIsInstance(owner, dict)
            self.assertNotEqual(owner.get("kind"), "")

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

    def test_for_iter_mode_and_iterable_traits_are_annotated(self) -> None:
        src = """
def f(xs: list[int], d: dict[str, int], x: object) -> None:
    for a in xs:
        pass
    for k in d:
        pass
    for v in x:
        pass
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        for_nodes = [n for n in body if isinstance(n, dict) and n.get("kind") == "For"]
        self.assertEqual(len(for_nodes), 3)

        list_for = for_nodes[0]
        self.assertEqual(list_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(list_for.get("iter_element_type"), "int64")
        self.assertEqual(list_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(list_for.get("iter", {}).get("iter_protocol"), "static_range")

        dict_for = for_nodes[1]
        self.assertEqual(dict_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(dict_for.get("iter_element_type"), "str")
        self.assertEqual(dict_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(dict_for.get("iter", {}).get("iter_protocol"), "static_range")

        obj_for = for_nodes[2]
        self.assertEqual(obj_for.get("iter_mode"), "runtime_protocol")
        self.assertEqual(obj_for.get("iter_source_type"), "object")
        self.assertEqual(obj_for.get("iter", {}).get("iterable_trait"), "unknown")
        self.assertEqual(obj_for.get("iter", {}).get("iter_protocol"), "runtime_protocol")

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

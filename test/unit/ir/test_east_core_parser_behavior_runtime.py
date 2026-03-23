"""Parser behavior regressions for runtime annotation and builtin-call lanes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import _walk
from src.toolchain.misc.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorRuntimeTest(unittest.TestCase):
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
        semantic_tags = {str(n.get("semantic_tag")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
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
        self.assertIn("core.len", semantic_tags)
        self.assertIn("core.print", semantic_tags)
        self.assertIn("container.dict.get", semantic_tags)
        self.assertIn("cast.bool", semantic_tags)
        self.assertIn("cast.int", semantic_tags)
        self.assertIn("iter.init", semantic_tags)
        self.assertIn("iter.next", semantic_tags)
        self.assertIn("logic.any", semantic_tags)
        self.assertIn("logic.all", semantic_tags)
        runtime_bindings = {
            str(n.get("runtime_call")): (str(n.get("runtime_module_id", "")), str(n.get("runtime_symbol", "")))
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and isinstance(n.get("runtime_call"), str)
        }
        self.assertEqual(runtime_bindings.get("py_enumerate"), ("pytra.built_in.iter_ops", "enumerate"))
        self.assertEqual(runtime_bindings.get("py_any"), ("pytra.built_in.predicates", "any"))
        self.assertEqual(runtime_bindings.get("py_print"), ("pytra.built_in.io_ops", "py_print"))
        self.assertEqual(runtime_bindings.get("py_to_int64_base"), ("pytra.built_in.scalar_ops", "py_to_int64_base"))
        self.assertEqual(runtime_bindings.get("py_ord"), ("pytra.built_in.scalar_ops", "py_ord"))
        self.assertEqual(runtime_bindings.get("py_chr"), ("pytra.built_in.scalar_ops", "py_chr"))
        self.assertEqual(runtime_bindings.get("dict.get"), ("pytra.core.dict", "dict.get"))
        self.assertEqual(runtime_bindings.get("std::filesystem::exists"), ("pytra.std.pathlib", "Path.exists"))

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
        self.assertEqual(calls[0].get("runtime_module_id"), "pytra.std.time")
        self.assertEqual(calls[0].get("runtime_symbol"), "perf_counter")

    def test_noncpp_runtime_call_annotations_for_import_symbol_and_module_attr(self) -> None:
        src = """
from pytra.std import json
from pytra.utils import png, gif
from pytra.utils.assertions import py_assert_stdout
import math

def main() -> None:
    obj = json.loads("{\\"ok\\": true}")
    txt = json.dumps(obj)
    pixels: bytes = bytes([0, 0, 0])
    wave = math.sin(math.pi)
    png.write_rgb_png("x.png", 1, 1, pixels)
    palette = gif.grayscale_palette()
    gif.save_gif("x.gif", 1, 1, [pixels], palette, delay_cs=1, loop=0)
    py_assert_stdout("ok", txt + str(wave))
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        resolved_runtime_calls = {
            str(n.get("resolved_runtime_call"))
            for n in calls
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("json.loads", resolved_runtime_calls)
        self.assertIn("json.dumps", resolved_runtime_calls)
        self.assertIn("write_rgb_png", resolved_runtime_calls)
        self.assertIn("save_gif", resolved_runtime_calls)
        self.assertIn("grayscale_palette", resolved_runtime_calls)
        self.assertIn("py_assert_stdout", resolved_runtime_calls)
        self.assertIn("math.sin", resolved_runtime_calls)
        math_sin_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.sin"
        ]
        self.assertEqual(len(math_sin_calls), 1)
        self.assertEqual(math_sin_calls[0].get("resolved_type"), "float64")
        self.assertEqual(math_sin_calls[0].get("runtime_module_id"), "math")
        self.assertEqual(math_sin_calls[0].get("runtime_symbol"), "sin")
        json_loads_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "json.loads"
        ]
        self.assertEqual(len(json_loads_calls), 1)
        self.assertEqual(json_loads_calls[0].get("runtime_module_id"), "pytra.std.json")
        self.assertEqual(json_loads_calls[0].get("runtime_symbol"), "loads")
        png_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "write_rgb_png"
        ]
        self.assertEqual(len(png_calls), 1)
        self.assertEqual(png_calls[0].get("runtime_module_id"), "pytra.utils.png")
        self.assertEqual(png_calls[0].get("runtime_symbol"), "write_rgb_png")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        resolved_runtime_attrs = {
            str(n.get("resolved_runtime_call"))
            for n in attrs
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("math.pi", resolved_runtime_attrs)
        math_pi_attrs = [
            n for n in attrs if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.pi"
        ]
        self.assertEqual(len(math_pi_attrs), 1)
        self.assertEqual(math_pi_attrs[0].get("runtime_module_id"), "math")
        self.assertEqual(math_pi_attrs[0].get("runtime_symbol"), "pi")

    def test_json_decode_helpers_receive_json_semantic_tags(self) -> None:
        src = """
from pytra.std import json
from pytra.std.json import JsonArr, JsonObj, JsonValue

def main(text: str, value: JsonValue, obj: JsonObj, arr: JsonArr) -> None:
    root = json.loads(text)
    obj0 = json.loads_obj(text)
    arr0 = json.loads_arr(text)
    a = value.as_obj()
    b = value.as_int()
    c = obj.get_arr("items")
    d = arr.get_bool(0)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "Call" and isinstance(n.get("repr"), str)
        ]
        by_repr = {str(n.get("repr")): n for n in calls}
        self.assertEqual(by_repr["json.loads(text)"].get("semantic_tag"), "json.loads")
        self.assertEqual(by_repr["json.loads_obj(text)"].get("semantic_tag"), "json.loads_obj")
        self.assertEqual(by_repr["json.loads_arr(text)"].get("semantic_tag"), "json.loads_arr")
        self.assertEqual(by_repr["value.as_obj()"].get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(by_repr["value.as_int()"].get("semantic_tag"), "json.value.as_int")
        self.assertEqual(by_repr['obj.get_arr("items")'].get("semantic_tag"), "json.obj.get_arr")
        self.assertEqual(by_repr["arr.get_bool(0)"].get("semantic_tag"), "json.arr.get_bool")

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
            self.assertEqual(call.get("runtime_module_id"), "pytra.std.pathlib")
            self.assertEqual(call.get("runtime_symbol"), "Path")

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

    def test_path_property_attributes_are_lowered_with_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out/a.txt")
    parent = p.parent
    name = p.name
    stem = p.stem
    print(parent, name, stem)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        path_attrs = [n for n in attrs if str(n.get("attr")) in {"parent", "name", "stem"}]
        self.assertEqual(len(path_attrs), 3)
        runtime_calls = {str(n.get("runtime_call")) for n in path_attrs}
        self.assertEqual(runtime_calls, {"path_parent", "path_name", "path_stem"})
        lowered_kinds = {str(n.get("lowered_kind")) for n in path_attrs}
        self.assertEqual(lowered_kinds, {"BuiltinAttr"})
        semantic_tags = {str(n.get("semantic_tag")) for n in path_attrs}
        self.assertEqual(
            semantic_tags,
            {"stdlib.method.parent", "stdlib.method.name", "stdlib.method.stem"},
        )

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

    def test_container_extraction_yields_dynamic_annotation(self) -> None:
        """dict.get() on dict[str,int] sets yields_dynamic=True and
        container.dict.get semantic_tag; dict[str,Any].get() does NOT
        set yields_dynamic because resolved_type is already Any."""
        src = """
from pytra.typing import Any

def concrete(d: dict[str, int]) -> int:
    return d.get("x", 0)

def dynamic(d: dict[str, Any]) -> Any:
    return d.get("x", 0)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = {
            str(n.get("name")): n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef"
        }
        # concrete dict[str,int].get() → yields_dynamic=True
        concrete_calls = [
            n
            for n in _walk(funcs["concrete"])
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("runtime_call") == "dict.get"
        ]
        self.assertEqual(len(concrete_calls), 1)
        self.assertTrue(concrete_calls[0].get("yields_dynamic"))
        self.assertEqual(concrete_calls[0].get("semantic_tag"), "container.dict.get")
        self.assertEqual(concrete_calls[0].get("resolved_type"), "int64")

        # dynamic dict[str,Any].get() → no yields_dynamic
        dynamic_calls = [
            n
            for n in _walk(funcs["dynamic"])
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("runtime_call") == "dict.get"
        ]
        self.assertEqual(len(dynamic_calls), 1)
        self.assertIsNone(dynamic_calls[0].get("yields_dynamic"))
        self.assertEqual(dynamic_calls[0].get("semantic_tag"), "container.dict.get")
        self.assertEqual(dynamic_calls[0].get("resolved_type"), "Any")

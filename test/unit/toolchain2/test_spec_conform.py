from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.common.jv import deep_copy_json
from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.parse.py.parser import parse_python_source
from toolchain2.resolve.py.builtin_registry import BuiltinRegistry, load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2
from toolchain2.resolve.py.validate_east2 import validate_east2


def _walk(node: object) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            out.extend(_walk(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk(item))
    return out


def _load_registry() -> BuiltinRegistry:
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


class Toolchain2SpecConformTests(unittest.TestCase):
    def test_parser_preserves_typing_prefix_until_resolve(self) -> None:
        source = """
import typing

def f(xs: typing.List[int], *rest: typing.Tuple[str, int]) -> "typing.List[int]":
    return xs
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        fn = next(node for node in _walk(east1) if node.get("kind") == "FunctionDef" and node.get("name") == "f")

        self.assertEqual(fn.get("arg_types", {}).get("xs"), "typing.List[int]")
        self.assertEqual(fn.get("vararg_type"), "typing.Tuple[str, int]")
        self.assertEqual(fn.get("return_type"), '"typing.List[int]"')

        east2 = deep_copy_json(east1)
        self.assertIsInstance(east2, dict)
        resolve_east1_to_east2(east2, registry=_load_registry())
        fn2 = next(node for node in _walk(east2) if node.get("kind") == "FunctionDef" and node.get("name") == "f")

        self.assertEqual(fn2.get("arg_types", {}).get("xs"), "list[int64]")
        self.assertEqual(fn2.get("vararg_type"), "tuple[str,int64]")
        self.assertEqual(fn2.get("return_type"), "list[int64]")
        self.assertEqual(
            fn2.get("vararg_type_expr"),
            {
                "kind": "GenericType",
                "base": "tuple",
                "args": [
                    {"kind": "NamedType", "name": "str"},
                    {"kind": "NamedType", "name": "int64"},
                ],
            },
        )

    def test_parser_preserves_type_alias_value_in_east1(self) -> None:
        source = """
type Scalar = int | float
"""
        east1 = parse_python_source(source, "<mem>").to_jv()

        type_alias = next(node for node in _walk(east1) if node.get("kind") == "TypeAlias")
        self.assertEqual(type_alias.get("name"), "Scalar")
        self.assertEqual(type_alias.get("value"), "int | float")

    def test_resolver_expands_type_aliases_by_east2(self) -> None:
        source = """
type Scalar = int | float

def identity(value: Scalar) -> Scalar:
    return value
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        type_alias = next(node for node in _walk(east2) if node.get("kind") == "TypeAlias")
        fn = next(node for node in _walk(east2) if node.get("kind") == "FunctionDef" and node.get("name") == "identity")
        ret_name = next(
            node for node in _walk(fn)
            if node.get("kind") == "Name" and node.get("id") == "value" and node.get("resolved_type") != "callable"
        )

        self.assertEqual(type_alias.get("value"), "int64 | float64")
        self.assertEqual(fn.get("arg_types", {}).get("value"), "int64 | float64")
        self.assertEqual(fn.get("return_type"), "int64 | float64")
        self.assertEqual(ret_name.get("resolved_type"), "int64 | float64")

    def test_pytra_typing_cast_is_kept_as_value_import_and_resolves_target_type(self) -> None:
        source = """
from pytra.typing import Any, cast
from pytra.std.pathlib import Path

def f(value: str | Path, raw: Any) -> str:
    text = cast(str, value)
    path_obj = cast(Path, value)
    return text
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        meta1 = east1.get("meta", {})
        self.assertIsInstance(meta1, dict)
        import_symbols1 = meta1.get("import_symbols", {})
        self.assertIsInstance(import_symbols1, dict)
        self.assertEqual(import_symbols1.get("cast"), {"module": "pytra.typing", "name": "cast"})
        self.assertNotIn("Any", import_symbols1)

        east2 = deep_copy_json(east1)
        self.assertIsInstance(east2, dict)
        resolve_east1_to_east2(east2, registry=_load_registry())

        cast_calls = [
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "cast"
        ]
        self.assertEqual([node.get("resolved_type") for node in cast_calls], ["str", "Path"])

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        text_assign = next(
            node for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "text"
        )
        path_assign = next(
            node for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "path_obj"
        )
        self.assertEqual(text_assign.get("decl_type"), "str")
        self.assertEqual(path_assign.get("decl_type"), "Path")

    def test_registry_driven_resolution_covers_builtins_stdlib_and_forrange(self) -> None:
        source = """
from pytra.std import json, random
from pytra.std.pathlib import Path

def f(xs: list[int], ys: list[str], text: str) -> None:
    a = sorted(xs)
    b = zip(xs, ys)
    c = json.loads(text)
    d = random.randint(1, 2)
    p = Path("x")
    for i in range(3):
        pass
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        sorted_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "sorted"
        )
        zip_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "zip"
        )
        json_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and isinstance(node["func"].get("value"), dict)
            and node["func"]["value"].get("kind") == "Name"
            and node["func"]["value"].get("id") == "json"
            and node["func"].get("attr") == "loads"
        )
        randint_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and isinstance(node["func"].get("value"), dict)
            and node["func"]["value"].get("kind") == "Name"
            and node["func"]["value"].get("id") == "random"
            and node["func"].get("attr") == "randint"
        )
        path_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "Path"
        )
        for_range = next(node for node in _walk(east2) if node.get("kind") == "ForRange")

        self.assertEqual(sorted_call.get("resolved_type"), "list[int64]")
        self.assertEqual(zip_call.get("resolved_type"), "list[tuple[int64,str]]")
        self.assertEqual(json_call.get("resolved_type"), "JsonValue")
        self.assertEqual(json_call.get("runtime_module_id"), "pytra.std.json")
        self.assertEqual(randint_call.get("resolved_type"), "int64")
        self.assertEqual(randint_call.get("runtime_module_id"), "pytra.std.random")
        self.assertEqual(path_call.get("resolved_type"), "Path")
        self.assertEqual(for_range.get("target_type"), "int64")
        self.assertEqual(for_range.get("target", {}).get("resolved_type"), "int64")

    def test_resolver_annotates_module_attr_runtime_metadata_for_extern_values(self) -> None:
        source = """
from pytra.std import math

def f() -> float:
    return math.pi
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        math_pi = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "pi"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Name"
            and node["value"].get("id") == "math"
        )

        self.assertEqual(math_pi.get("resolved_type"), "float64")
        self.assertEqual(math_pi.get("runtime_module_id"), "pytra.std.math")
        self.assertEqual(math_pi.get("runtime_symbol"), "pi")
        self.assertEqual(math_pi.get("runtime_symbol_dispatch"), "value")

    def test_resolver_propagates_extern_call_argument_type(self) -> None:
        source = """
import sys
from pytra.std import extern

stdout = extern(sys.stdout)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        stdout_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "stdout"
        )

        self.assertEqual(stdout_assign.get("decl_type"), "str")
        self.assertEqual(stdout_assign.get("value", {}).get("resolved_type"), "str")

    def test_resolver_recognizes_builtin_type_objects_in_value_position(self) -> None:
        source = """
int8 = int
float64 = float
Obj = object
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        assigns = {
            node["target"]["id"]: node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and isinstance(node["target"].get("id"), str)
        }

        self.assertEqual(assigns["int8"].get("decl_type"), "type")
        self.assertEqual(assigns["int8"].get("value", {}).get("resolved_type"), "type")
        self.assertEqual(assigns["float64"].get("decl_type"), "type")
        self.assertEqual(assigns["Obj"].get("decl_type"), "type")

    def test_registry_loads_runtime_builtins_and_tuple_target_comprehensions(self) -> None:
        registry = _load_registry()
        sum_sig = registry.lookup_function("sum")

        self.assertIsNotNone(sum_sig)
        self.assertEqual(sum_sig.return_type, "T")

        source = """
def linear(x: list[float], w: list[list[float]]) -> list[float]:
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=registry)

        linear_fn = next(
            node for node in _walk(east2)
            if node.get("kind") == "FunctionDef" and node.get("name") == "linear"
        )
        sum_call = next(
            node
            for node in _walk(linear_fn)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "sum"
        )
        wi_nodes = [
            node for node in _walk(linear_fn)
            if node.get("kind") == "Name" and node.get("id") == "wi"
        ]
        xi_nodes = [
            node for node in _walk(linear_fn)
            if node.get("kind") == "Name" and node.get("id") == "xi"
        ]

        self.assertEqual(linear_fn.get("return_type"), "list[float64]")
        self.assertEqual(sum_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(sum_call.get("resolved_type"), "float64")
        self.assertTrue(wi_nodes)
        self.assertTrue(xi_nodes)
        self.assertTrue(all(node.get("resolved_type") == "float64" for node in wi_nodes))
        self.assertTrue(all(node.get("resolved_type") == "float64" for node in xi_nodes))

    def test_resolve_requires_registry(self) -> None:
        east1 = parse_python_source("def f() -> None:\n    pass\n", "<mem>").to_jv()
        with self.assertRaisesRegex(ValueError, "registry is required"):
            resolve_east1_to_east2(east1, registry=None)

    def test_resolver_keeps_pathlib_methods_transpilable_and_resolves_with_body(self) -> None:
        source = """
from pytra.std.pathlib import Path

def f(p: Path) -> str:
    p.write_text("42")
    with open("out.bin", "wb") as fh:
        fh.write(bytes(bytearray([1, 2, 3])))
    return p.read_text()
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        write_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "write_text"
        )
        read_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "read_text"
        )
        with_node = next(node for node in _walk(east2) if node.get("kind") == "With")
        with_body_call = with_node["body"][0]["value"]

        self.assertNotEqual(write_call.get("lowered_kind"), "BuiltinCall")
        self.assertNotEqual(read_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(with_node.get("context_expr", {}).get("kind"), "Call")
        self.assertEqual(with_node.get("context_expr", {}).get("args", [])[0].get("resolved_type"), "str")
        self.assertEqual(with_body_call.get("args", [])[0].get("resolved_type"), "bytes")

    def test_boolop_value_select_preserves_operand_type(self) -> None:
        source = """
def f() -> None:
    x: str = ""
    y: str = "fallback"
    z: str = x or y
    n: int = 0
    m: int = 9
    t: int = n or m
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        boolops = [node for node in _walk(east2) if node.get("kind") == "BoolOp"]
        self.assertEqual(len(boolops), 2)
        self.assertEqual(boolops[0].get("resolved_type"), "str")
        self.assertEqual(boolops[1].get("resolved_type"), "int64")

    def test_ann_assign_does_not_rewrite_any_annotated_value_type(self) -> None:
        source = """
from pytra.typing import Any

def f() -> None:
    values: list[Any] = [1, 2]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        ann_assign = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "values"
        )

        self.assertEqual(ann_assign.get("decl_type"), "list[Any]")
        self.assertEqual(ann_assign.get("value", {}).get("resolved_type"), "list[int64]")

        east3 = lower_east2_to_east3(east2)
        ann_assign3 = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "values"
        )
        self.assertEqual(ann_assign3.get("value", {}).get("kind"), "Box")
        self.assertEqual(ann_assign3.get("value", {}).get("target"), "list[Any]")

    def test_compile_inserts_unbox_for_yields_dynamic_assignment_targets(self) -> None:
        source = """
from pytra.typing import Any

def f(root: dict[str, Any]) -> int:
    meta: dict[str, Any] = root.get("meta", {})
    total: int = 0
    for _k, v in meta.items():
        total += v
    return total
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        meta_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "meta"
        )
        total_aug = next(node for node in _walk(east3) if node.get("kind") == "AugAssign")

        self.assertEqual(meta_assign.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(meta_assign.get("value", {}).get("target"), "dict[str,Any]")
        self.assertEqual(total_aug.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(total_aug.get("value", {}).get("target"), "int64")

    def test_compile_keeps_optional_unbox_boundary_for_dict_get_without_default(self) -> None:
        source = """
def f(d: dict[str, int]) -> bool:
    g: int | None = d.get("x")
    return g is not None
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        g_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "g"
        )

        self.assertEqual(g_assign.get("decl_type"), "int64 | None")
        self.assertEqual(g_assign.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(g_assign.get("value", {}).get("target"), "int64 | None")
        self.assertTrue(g_assign.get("value", {}).get("value", {}).get("yields_dynamic"))

    def test_compile_narrows_union_names_inside_isinstance_guard(self) -> None:
        source = """
type Scalar = int | float

def add_scalars(a: Scalar, b: Scalar) -> int:
    if isinstance(a, int) and isinstance(b, int):
        return a + b
    return 0
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        guarded_return = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Return"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "BinOp"
        )
        binop = guarded_return["value"]
        left = binop.get("left", {})
        right = binop.get("right", {})

        self.assertEqual(left.get("kind"), "Unbox")
        self.assertEqual(left.get("target"), "int64")
        self.assertEqual(right.get("kind"), "Unbox")
        self.assertEqual(right.get("target"), "int64")
        self.assertEqual(binop.get("resolved_type"), "int64")

    def test_compile_boxes_imported_stdlib_alias_arguments(self) -> None:
        source = """
from pytra.std.json import dumps

def f() -> str:
    return dumps(123)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        dumps_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "dumps"
        )
        boxed_arg = dumps_call.get("args", [])[0]

        self.assertEqual(boxed_arg.get("kind"), "Box")
        self.assertEqual(boxed_arg.get("target"), "bool|int64|float64|str|list[Any]|dict[str,Any]|None")
        self.assertEqual(boxed_arg.get("value", {}).get("resolved_type"), "int64")

    def test_compile_preserves_tuple_unpack_value_type_for_static_tuple_calls(self) -> None:
        source = """
def pair() -> tuple[int, int]:
    return 1, 2

def f() -> int:
    x, y = pair()
    return x + y
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        tmp_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "__tup_1"
        )
        x_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "x"
        )

        self.assertEqual(tmp_assign.get("decl_type"), "tuple[int64,int64]")
        self.assertEqual(tmp_assign.get("value", {}).get("kind"), "Call")
        self.assertEqual(x_assign.get("decl_type"), "int64")
        self.assertEqual(x_assign.get("value", {}).get("resolved_type"), "int64")

    def test_compile_unboxes_optional_tuple_before_unpack(self) -> None:
        source = """
def f(separators: tuple[str, str] | None) -> str:
    item_sep = ","
    key_sep = ":"
    if separators is not None:
        item_sep, key_sep = separators
    return item_sep + key_sep
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        tmp_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "__tup_1"
        )
        item_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "item_sep"
            and node.get("decl_type") == "str"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Subscript"
        )
        key_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "key_sep"
            and node.get("decl_type") == "str"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Subscript"
        )

        self.assertEqual(tmp_assign.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(tmp_assign.get("value", {}).get("target"), "tuple[str,str]")
        self.assertEqual(item_assign.get("value", {}).get("resolved_type"), "str")
        self.assertEqual(key_assign.get("value", {}).get("resolved_type"), "str")

    def test_compile_casts_string_index_to_byte_target(self) -> None:
        source = """
def f(s: str, i: int) -> None:
    ch: byte = s[i]
    print(ch == 66)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        ch_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "ch"
        )
        value = ch_assign.get("value")

        self.assertEqual(ch_assign.get("decl_type"), "str")
        self.assertEqual(ch_assign.get("decl_type_expr"), {"kind": "NamedType", "name": "str"})
        self.assertIsInstance(ch_assign.get("target"), dict)
        self.assertEqual(ch_assign["target"].get("resolved_type"), "str")
        self.assertEqual(ch_assign["target"].get("type_expr"), {"kind": "NamedType", "name": "str"})
        self.assertIsInstance(value, dict)
        self.assertEqual(value.get("kind"), "Subscript")
        self.assertEqual(value.get("resolved_type"), "str")

    def test_resolver_sets_for_loop_target_types_for_strings_and_bytes(self) -> None:
        source = """
def f(b: bytes, ba: bytearray, s: str) -> None:
    for vb in b:
        print(vb)
    for vba in ba:
        print(vba)
    for ch in s:
        print(ch)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        for_nodes = [node for node in _walk(east2) if node.get("kind") == "For"]
        self.assertEqual(len(for_nodes), 3)

        bytes_for = for_nodes[0]
        bytearray_for = for_nodes[1]
        str_for = for_nodes[2]

        self.assertEqual(bytes_for.get("target_type"), "int64")
        self.assertEqual(bytes_for.get("iter_element_type"), "int64")
        self.assertEqual(bytes_for.get("target", {}).get("resolved_type"), "int64")

        self.assertEqual(bytearray_for.get("target_type"), "int64")
        self.assertEqual(bytearray_for.get("iter_element_type"), "int64")
        self.assertEqual(bytearray_for.get("target", {}).get("resolved_type"), "int64")

        self.assertEqual(str_for.get("target_type"), "str")
        self.assertEqual(str_for.get("iter_element_type"), "str")
        self.assertEqual(str_for.get("target", {}).get("resolved_type"), "str")

    def test_resolver_refines_lambda_args_from_calls_and_defaults(self) -> None:
        source = """
def f() -> tuple[int, float]:
    direct: int = (lambda x, y: x + y)(4, 5)
    matrix = lambda nout, nin, std=0.08: nout + nin * std
    return direct, matrix(1, 2)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        lambdas = [node for node in _walk(east2) if node.get("kind") == "Lambda"]
        direct_lambda = lambdas[0]
        named_lambda = lambdas[1]
        direct_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Lambda"
        )
        named_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "matrix"
        )

        self.assertEqual(direct_lambda.get("arg_types"), {"x": "int64", "y": "int64"})
        self.assertEqual(direct_lambda.get("return_type"), "int64")
        self.assertEqual(direct_call.get("resolved_type"), "int64")

        self.assertEqual(named_lambda.get("arg_types", {}).get("std"), "float64")
        self.assertEqual(named_lambda.get("return_type"), "float64")
        self.assertEqual(named_call.get("resolved_type"), "float64")

    def test_compile_expands_defaults_for_lambda_assigned_to_name(self) -> None:
        source = """
def f() -> None:
    matrix = lambda nout, nin, std=0.08: nout + nin * std
    print(matrix(1, 2))
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        validate_east2(east2)

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        matrix_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "matrix"
        )

        self.assertEqual(len(matrix_call.get("args", [])), 3)
        self.assertEqual(matrix_call.get("args", [])[2].get("resolved_type"), "float64")

    def test_resolver_substitutes_container_method_arg_hints(self) -> None:
        source = """
def f() -> None:
    keys: list[list[int]] = []
    keys.append([])
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        append_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "append"
        )
        append_arg = append_call.get("args", [])[0]

        self.assertEqual(append_arg.get("resolved_type"), "list[int64]")
        self.assertEqual(append_arg.get("call_arg_type"), "list[int64]")

    def test_resolver_loads_utils_registry_and_type_name_attribute(self) -> None:
        source = """
from pytra.utils.assertions import py_assert_eq

class Value:
    pass

def f(v: Value) -> bool:
    name = type(v).__name__
    return py_assert_eq(name, "Value", "type name")
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        type_name_attr = next(
            node for node in _walk(east2)
            if node.get("kind") == "Attribute" and node.get("attr") == "__name__"
        )
        assert_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "py_assert_eq"
        )

        self.assertEqual(type_name_attr.get("resolved_type"), "str")
        self.assertEqual(assert_call.get("resolved_type"), "bool")

    def test_compile_preserves_nested_list_comp_element_type(self) -> None:
        source = """
def f(n_layer: int) -> list[list[int]]:
    keys: list[list[int]] = [[] for _ in range(n_layer)]
    return keys
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        append_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "append"
        )
        append_arg = append_call.get("args", [])[0]

        self.assertEqual(append_arg.get("resolved_type"), "list[int64]")
        self.assertEqual(append_arg.get("call_arg_type"), "list[int64]")

    def test_validator_reports_unknown_missing_and_unnormalized_types(self) -> None:
        unknown_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<unknown>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "unknown",
                    },
                }
            ],
        }
        missing_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<missing>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Name",
                        "id": "x",
                    },
                }
            ],
        }
        range_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<range>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"x": "int"},
                    "arg_usage": {"x": "readonly"},
                    "arg_type_exprs": {"x": {"kind": "NamedType", "name": "int64"}},
                    "return_type": "float",
                    "return_type_expr": {"kind": "NamedType", "name": "float64"},
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "RangeExpr",
                                "resolved_type": "list[int64]",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            },
                        }
                    ],
                }
            ],
        }

        unknown_result = validate_east2(unknown_doc)
        missing_result = validate_east2(missing_doc)
        range_result = validate_east2(range_doc)

        self.assertTrue(any("resolved_type is unknown" in err for err in unknown_result.errors))
        self.assertTrue(any("missing resolved_type" in err for err in missing_result.errors))
        self.assertTrue(any("unnormalized type 'int'" in err for err in range_result.errors))
        self.assertTrue(any("unnormalized type 'float'" in err for err in range_result.errors))
        self.assertFalse(any("RangeExpr" in err for err in range_result.errors))


if __name__ == "__main__":
    unittest.main()

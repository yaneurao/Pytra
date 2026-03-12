"""Parser behavior regressions for decode-first and type-expression lanes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import _walk
from src.toolchain.compiler.east import EastBuildError
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorTypesTest(unittest.TestCase):
    def test_homogeneous_tuple_ellipsis_annotation_is_accepted_as_generic_tuple_typeexpr(self) -> None:
        src = """
LENGTH_TABLE: tuple[int, ...] = (10, 20, 30)

def head(xs: tuple[int, ...]) -> int:
    return xs[0]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

        ann_assign = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "AnnAssign" and n.get("target", {}).get("id") == "LENGTH_TABLE"
        )
        self.assertEqual(ann_assign.get("annotation"), "tuple[int64,...]")
        self.assertEqual(
            ann_assign.get("annotation_type_expr"),
            {
                "kind": "GenericType",
                "base": "tuple",
                "args": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "..."},
                ],
            },
        )

        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "head"
        )
        self.assertEqual(fn.get("arg_types", {}).get("xs"), "tuple[int64,...]")
        self.assertEqual(
            fn.get("arg_type_exprs", {}).get("xs"),
            {
                "kind": "GenericType",
                "base": "tuple",
                "args": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "..."},
                ],
            },
        )

    def test_sum_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> int:
    value = json.loads(text)
    return sum(value)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("sum() does not accept object/Any values", str(cm.exception))

    def test_zip_on_json_values_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(lhs_text: str, rhs_text: str) -> None:
    lhs = json.loads(lhs_text)
    rhs = json.loads(rhs_text)
    _ = zip(lhs, rhs)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("zip() does not accept object/Any values", str(cm.exception))

    def test_dict_keys_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> None:
    value = json.loads(text)
    _ = value.keys()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("keys() does not accept object/Any receivers", str(cm.exception))

    def test_quoted_type_annotation_is_normalized(self) -> None:
        src = """
def f(p: "Path", xs: "list[int]") -> "Path":
    return p
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_types = fn.get("arg_types", {})
        self.assertEqual(arg_types.get("p"), "Path")
        self.assertEqual(arg_types.get("xs"), "list[int64]")
        self.assertEqual(fn.get("return_type"), "Path")
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(arg_type_exprs.get("p"), {"kind": "NamedType", "name": "Path"})
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [{"kind": "NamedType", "name": "int64"}],
            },
        )
        self.assertEqual(fn.get("return_type_expr"), {"kind": "NamedType", "name": "Path"})

    def test_typed_varargs_signature_uses_dedicated_vararg_fields(self) -> None:
        src = """
class ControllerState:
    pressed: bool

def merge_controller_states(target: ControllerState, *states: ControllerState) -> None:
    for state in states:
        target.pressed = target.pressed or state.pressed
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "merge_controller_states"
        )
        self.assertEqual(fn.get("arg_order"), ["target"])
        self.assertEqual(fn.get("arg_types", {}).get("target"), "ControllerState")
        self.assertNotIn("states", fn.get("arg_types", {}))
        self.assertEqual(fn.get("vararg_name"), "states")
        self.assertEqual(fn.get("vararg_type"), "ControllerState")
        self.assertEqual(fn.get("vararg_type_expr"), {"kind": "NamedType", "name": "ControllerState"})

    def test_type_expr_is_emitted_for_union_optional_and_nested_generic_annotations(self) -> None:
        src = """
from pytra.std.json import JsonValue

def f(x: int | bool, ys: list[int | bool], payload: JsonValue | None) -> dict[str, int | bool]:
    local: list[int | bool] = []
    return {"a": 1}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        self.assertEqual(fn.get("arg_types", {}).get("x"), "int64|bool")
        self.assertEqual(fn.get("arg_types", {}).get("ys"), "list[int64|bool]")
        self.assertEqual(fn.get("arg_types", {}).get("payload"), "JsonValue | None")
        self.assertEqual(fn.get("return_type"), "dict[str,int64|bool]")

        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("ys"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "GenericType",
                "base": "dict",
                "args": [
                    {"kind": "NamedType", "name": "str"},
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    },
                ],
            },
        )

        ann_assign = next(
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        )
        self.assertEqual(ann_assign.get("annotation"), "list[int64|bool]")
        self.assertEqual(
            ann_assign.get("annotation_type_expr"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )

    def test_type_expr_is_built_for_union_optional_and_nominal_annotations(self) -> None:
        src = """
from pytra.std.json import JsonObj, JsonValue

def f(x: int | bool, xs: list[int | bool], payload: JsonValue | None) -> JsonObj | None:
    local: dict[str, int | bool] = {}
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonObj",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        ann_assign = next(
            n
            for n in fn.get("body", [])
            if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        )
        expected_decl = {
            "kind": "GenericType",
            "base": "dict",
            "args": [
                {"kind": "NamedType", "name": "str"},
                {
                    "kind": "UnionType",
                    "union_mode": "general",
                    "options": [
                        {"kind": "NamedType", "name": "int64"},
                        {"kind": "NamedType", "name": "bool"},
                    ],
                },
            ],
        }
        self.assertEqual(ann_assign.get("annotation_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("decl_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("target", {}).get("type_expr"), expected_decl)

    def test_future_annotations_is_not_emitted_to_east_imports(self) -> None:
        src = """
from __future__ import annotations
from pytra.std import json

def main() -> int:
    x: "int" = 1
    _ = json.dumps({"x": x})
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "ImportFrom"
        ]
        future_nodes = [n for n in import_from_nodes if n.get("module") == "__future__"]
        self.assertEqual(future_nodes, [])
        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "__future__")

    def test_typing_imports_are_annotation_only_noop(self) -> None:
        src = """
import typing
from typing import Any as A, List as L
from pytra.std import json

def main(xs: L[int]) -> A:
    _ = json.dumps({"n": len(xs)})
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(len(import_nodes), 1)
        self.assertEqual(import_nodes[0].get("kind"), "ImportFrom")
        self.assertEqual(import_nodes[0].get("module"), "pytra.std")

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        module_ids = [
            str(ent.get("module_id"))
            for ent in import_bindings
            if isinstance(ent, dict) and isinstance(ent.get("module_id"), str)
        ]
        self.assertNotIn("typing", module_ids)
        self.assertIn("pytra.std", module_ids)

    def test_typing_alias_is_resolved_without_runtime_import(self) -> None:
        src = """
from typing import List as L

def main() -> None:
    ys: L[int] = []
    print(ys)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in east.get("body", [])
            if isinstance(n, dict)
            and n.get("kind") == "FunctionDef"
            and (n.get("original_name") == "main" or n.get("name") == "main")
        )
        ann_assigns = [
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(ann_assigns[0].get("annotation"), "list[int64]")
        self.assertEqual(ann_assigns[0].get("value", {}).get("resolved_type"), "list[unknown]")

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertEqual(import_bindings, [])

    def test_relative_from_import_preserves_raw_module_text(self) -> None:
        src = """
from .helper import f

def main() -> None:
    f()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ImportFrom"
        ]
        self.assertEqual(len(import_from_nodes), 1)
        self.assertEqual(import_from_nodes[0].get("module"), ".helper")
        self.assertEqual(import_from_nodes[0].get("level"), 1)

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        self.assertEqual(len(import_bindings), 1)
        self.assertEqual(import_bindings[0].get("module_id"), ".helper")
        self.assertEqual(import_bindings[0].get("export_name"), "f")
        self.assertEqual(import_bindings[0].get("local_name"), "f")

        import_symbols = meta.get("import_symbols", {})
        self.assertIsInstance(import_symbols, dict)
        self.assertEqual(import_symbols.get("f"), {"module": ".helper", "name": "f"})

    def test_relative_from_import_without_module_preserves_dot_root(self) -> None:
        src = """
from . import f

def main() -> None:
    f()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ImportFrom"
        ]
        self.assertEqual(len(import_from_nodes), 1)
        self.assertEqual(import_from_nodes[0].get("module"), ".")
        self.assertEqual(import_from_nodes[0].get("level"), 1)

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        self.assertEqual(len(import_bindings), 1)
        self.assertEqual(import_bindings[0].get("module_id"), ".")
        self.assertEqual(import_bindings[0].get("export_name"), "f")

    def test_relative_from_import_accepts_parenthesized_symbol_list(self) -> None:
        src = """
from .controller import (
    BUTTON_A,
    BUTTON_B,
)

def main() -> int:
    return BUTTON_A | BUTTON_B
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ImportFrom"
        ]
        self.assertEqual(len(import_from_nodes), 1)
        self.assertEqual(import_from_nodes[0].get("module"), ".controller")
        self.assertEqual(import_from_nodes[0].get("level"), 1)
        aliases = import_from_nodes[0].get("names", [])
        self.assertEqual(
            [(alias.get("name"), alias.get("asname")) for alias in aliases],
            [("BUTTON_A", None), ("BUTTON_B", None)],
        )

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        self.assertEqual(
            [(entry.get("module_id"), entry.get("export_name")) for entry in import_bindings],
            [(".controller", "BUTTON_A"), (".controller", "BUTTON_B")],
        )

    def test_future_non_annotations_is_rejected(self) -> None:
        src = """
from __future__ import generator_stop
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("__future__", str(cm.exception))

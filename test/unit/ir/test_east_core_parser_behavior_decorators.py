"""Parser behavior regressions for extern/abi/template decorators."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import _walk
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorDecoratorsTest(unittest.TestCase):
    def test_template_decorator_rejects_duplicate_params(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("duplicate template parameter", str(cm.exception))

    def test_template_decorator_rejects_keyword_form(self) -> None:
        src = """
from pytra.std.template import template

@template(name="T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn(
            "template decorator accepts positional string literal parameters only",
            str(cm.exception),
        )

    def test_template_decorator_is_rejected_outside_runtime_helper_modules(self) -> None:
        src = """
from pytra.std.template import template

@template("T")
def f(xs: list[T]) -> list[T]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(
                src,
                "sample/py/template_demo.py",
                parser_backend="self_hosted",
            )
        self.assertIn("@template is supported on runtime helper modules only", str(cm.exception))

    def test_method_level_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

class Box:
    @abi(args={"xs": "value"})
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@abi is not supported on methods", str(cm.exception))

    def test_positional_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

@abi("value")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("abi decorator accepts keyword arguments only", str(cm.exception))

    def test_value_mut_is_rejected_for_return_mode(self) -> None:
        src = """
from pytra.std import abi

@abi(ret="value_mut")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("unsupported abi mode for abi ret", str(cm.exception))

    def test_value_abi_rejects_mutating_append(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"})
def py_join(parts: list[str]) -> str:
    parts.append("x")
    return ""
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("value parameter mutated", str(cm.exception))
        self.assertIn("parts", str(cm.exception))

    def test_top_level_extern_decorator_is_preserved(self) -> None:
        src = """
from pytra.std import extern

@extern
def f(x: float) -> float:
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0].get("decorators"), ["extern"])

    def test_top_level_annassign_extern_same_name_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

document: Any = extern()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 1,
            },
        )

    def test_top_level_annassign_extern_alias_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

doc: Any = extern("document")
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 0,
            },
        )

    def test_top_level_abi_decorator_sets_runtime_abi_metadata(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_legacy_value_readonly_alias_is_normalized_to_value(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value_readonly"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_top_level_extern_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import extern, abi

@extern
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[int]) -> list[int]:
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ["extern", 'abi(args={"xs": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value"},
                "ret": "value",
            },
        )

    def test_top_level_abi_decorator_accepts_value_mut_arg(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"xs": "value_mut"})
def sort_inplace(xs: list[int]) -> None:
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "sort_inplace"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(
            funcs[0].get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value_mut"},
                "ret": "default",
            },
        )

    def test_top_level_template_decorator_sets_template_metadata(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "U")
def py_zip(lhs: list[T], rhs: list[U]) -> list[tuple[T, U]]:
    return []
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_zip"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("decorators"), ['template("T", "U")'])
        self.assertEqual(
            fn.get("meta", {}).get("template_v1"),
            {
                "schema_version": 1,
                "params": ["T", "U"],
                "scope": "runtime_helper",
                "instantiation_mode": "linked_implicit",
            },
        )

    def test_top_level_template_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import abi
from pytra.std.template import template

@template("T")
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[T]) -> list[T]:
    return xs
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("meta", {}),
            {
                "template_v1": {
                    "schema_version": 1,
                    "params": ["T"],
                    "scope": "runtime_helper",
                    "instantiation_mode": "linked_implicit",
                },
                "runtime_abi_v1": {
                    "schema_version": 1,
                    "args": {"xs": "value"},
                    "ret": "value",
                },
            },
        )

    def test_method_level_template_decorator_is_rejected(self) -> None:
        src = """
from pytra.std.template import template

class Box:
    @template("T")
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@template is not supported on methods", str(cm.exception))

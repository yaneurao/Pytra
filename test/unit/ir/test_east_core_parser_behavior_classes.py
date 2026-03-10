"""Parser behavior regressions for class-like declarations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import _walk
from src.toolchain.compiler.east import convert_source_to_east_with_backend


class EastCoreParserBehaviorClassesTest(unittest.TestCase):
    def test_class_storage_hint_override_is_supported(self) -> None:
        src = """
class Box:
    __pytra_class_storage_hint__ = "value"

    def __init__(self, x: int) -> None:
        self.x = x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"
        ]
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

    def test_dataclass_scalar_fields_are_value_candidates(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    text: str
    pos: int
    number_value: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Token"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "value")

    def test_dataclass_container_field_falls_back_to_ref(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Box:
    items: list[int]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "ref")

    def test_std_dataclasses_imports_are_noop_and_decorator_resolves(self) -> None:
        src = """
import dataclasses as dc
from dataclasses import dataclass as d

@dc.dataclass(eq=False)
class A:
    x: int

@d(init=False, frozen=True)
class B:
    y: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(import_nodes, [])

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "dataclasses")

        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") in {"A", "B"}
        ]
        self.assertEqual(len(classes), 2)
        by_name = {str(c.get("name")): c for c in classes}
        self.assertTrue(bool(by_name["A"].get("dataclass")))
        self.assertTrue(bool(by_name["B"].get("dataclass")))
        opts_a = by_name["A"].get("dataclass_options", {})
        opts_b = by_name["B"].get("dataclass_options", {})
        self.assertIsInstance(opts_a, dict)
        self.assertIsInstance(opts_b, dict)
        self.assertEqual(opts_a.get("eq"), False)
        self.assertEqual(opts_b.get("init"), False)
        self.assertEqual(opts_b.get("frozen"), True)

    def test_nominal_adt_family_and_variants_are_parsed(self) -> None:
        src = """
from dataclasses import dataclass

@sealed
class Maybe:
    pass

@dataclass
class Just(Maybe):
    value: int

class Nothing(Maybe):
    pass
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") in {"Maybe", "Just", "Nothing"}
        ]
        self.assertEqual(len(classes), 3)
        by_name = {str(c.get("name")): c for c in classes}

        maybe = by_name["Maybe"]
        maybe_meta = maybe.get("meta", {}).get("nominal_adt_v1", {})
        self.assertEqual(maybe.get("decorators"), ["sealed"])
        self.assertEqual(maybe_meta.get("role"), "family")
        self.assertEqual(maybe_meta.get("family_name"), "Maybe")
        self.assertEqual(maybe_meta.get("surface_phase"), "declaration_v1")
        self.assertEqual(maybe_meta.get("closed"), 1)

        just = by_name["Just"]
        just_meta = just.get("meta", {}).get("nominal_adt_v1", {})
        self.assertTrue(bool(just.get("dataclass")))
        self.assertEqual(just.get("base"), "Maybe")
        self.assertEqual(just_meta.get("role"), "variant")
        self.assertEqual(just_meta.get("family_name"), "Maybe")
        self.assertEqual(just_meta.get("variant_name"), "Just")
        self.assertEqual(just_meta.get("payload_style"), "dataclass")

        nothing = by_name["Nothing"]
        nothing_meta = nothing.get("meta", {}).get("nominal_adt_v1", {})
        self.assertEqual(nothing.get("base"), "Maybe")
        self.assertEqual(nothing_meta.get("role"), "variant")
        self.assertEqual(nothing_meta.get("family_name"), "Maybe")
        self.assertEqual(nothing_meta.get("variant_name"), "Nothing")
        self.assertEqual(nothing_meta.get("payload_style"), "unit")

    def test_nominal_adt_payload_variant_requires_dataclass(self) -> None:
        src = """
@sealed
class Maybe:
    pass

class Bad(Maybe):
    value: int
"""
        with self.assertRaisesRegex(RuntimeError, "payload variant 'Bad' must use @dataclass"):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

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

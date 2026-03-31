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


from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.parse.py.parse_python import parse_python_file
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2


def _load_registry() -> object:
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


def _resolve_lower(source: str) -> tuple[dict[str, object], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "snippet.py"
        src.write_text(source, encoding="utf-8")
        east2 = parse_python_file(str(src))
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2, target_language="rs")
    return east2, east3


def _find_class(doc: dict[str, object], name: str) -> dict[str, object]:
    for stmt in doc.get("body", []):
        if isinstance(stmt, dict) and stmt.get("kind") == "ClassDef" and stmt.get("name") == name:
            return stmt
    raise AssertionError(f"class not found: {name}")


def _find_super_call(doc: dict[str, object]) -> dict[str, object]:
    for stmt in doc.get("body", []):
        if not isinstance(stmt, dict) or stmt.get("kind") != "ClassDef" or stmt.get("name") != "LoudDog":
            continue
        for method in stmt.get("body", []):
            if not isinstance(method, dict) or method.get("kind") not in ("FunctionDef", "ClosureDef"):
                continue
            if method.get("name") != "speak":
                continue
            ret = method.get("body", [])[0]
            if not isinstance(ret, dict):
                continue
            value = ret.get("value")
            if not isinstance(value, dict):
                continue
            right = value.get("right")
            if isinstance(right, dict) and right.get("kind") == "Call":
                return right
    raise AssertionError("super().speak() call not found")


class InheritanceRefSuperResolutionTests(unittest.TestCase):
    def test_base_classes_with_descendants_are_promoted_to_ref(self) -> None:
        source = """\
class Animal:
    def speak(self) -> str:
        return "animal"

class Dog(Animal):
    def speak(self) -> str:
        return "dog"

class LoudDog(Dog):
    def speak(self) -> str:
        return "loud-" + super().speak()
"""
        east2, east3 = _resolve_lower(source)

        self.assertEqual(_find_class(east2, "Animal").get("class_storage_hint"), "ref")
        self.assertEqual(_find_class(east2, "Dog").get("class_storage_hint"), "ref")
        self.assertEqual(_find_class(east2, "LoudDog").get("class_storage_hint"), "ref")

        self.assertEqual(_find_class(east3, "Animal").get("class_storage_hint"), "ref")
        self.assertEqual(_find_class(east3, "Dog").get("class_storage_hint"), "ref")
        self.assertEqual(_find_class(east3, "LoudDog").get("class_storage_hint"), "ref")

    def test_super_call_resolves_to_base_receiver_and_method_return_type(self) -> None:
        source = """\
class Animal:
    def speak(self) -> str:
        return "animal"

class Dog(Animal):
    def speak(self) -> str:
        return "dog"

class LoudDog(Dog):
    def speak(self) -> str:
        return "loud-" + super().speak()
"""
        east2, east3 = _resolve_lower(source)

        super_call2 = _find_super_call(east2)
        self.assertEqual(super_call2.get("resolved_type"), "str")
        func2 = super_call2.get("func")
        assert isinstance(func2, dict)
        self.assertEqual(func2.get("resolved_type"), "callable")
        owner2 = func2.get("value")
        assert isinstance(owner2, dict)
        self.assertEqual(owner2.get("resolved_type"), "Dog")
        self.assertEqual(owner2.get("special_form"), "super")
        self.assertEqual(owner2.get("super_of"), "LoudDog")

        super_call3 = _find_super_call(east3)
        self.assertEqual(super_call3.get("resolved_type"), "str")
        func3 = super_call3.get("func")
        assert isinstance(func3, dict)
        owner3 = func3.get("value")
        assert isinstance(owner3, dict)
        self.assertEqual(owner3.get("resolved_type"), "Dog")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.parse.py.parser import parse_python_source
from toolchain2.resolve.py.builtin_registry import BuiltinRegistry, load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2


def _load_registry() -> BuiltinRegistry:
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


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


def _resolve(source: str) -> dict[str, object]:
    east1 = parse_python_source(source, filename="<ifexp_optional>").to_jv()
    resolve_east1_to_east2(east1, registry=_load_registry())
    return east1


class IfExpOptionalInferenceTests(unittest.TestCase):
    def test_ifexp_infers_optional_when_else_is_none(self) -> None:
        east2 = _resolve(
            """\
def f(flag: bool, name: str) -> str | None:
    out = name if flag else None
    return out
"""
        )

        ifexp = next(node for node in _walk(east2) if node.get("kind") == "IfExp")
        self.assertEqual(ifexp.get("resolved_type"), "str | None")

    def test_ifexp_infers_optional_when_body_is_none(self) -> None:
        east2 = _resolve(
            """\
def f(flag: bool, name: str) -> str | None:
    out = None if flag else name
    return out
"""
        )

        ifexp = next(node for node in _walk(east2) if node.get("kind") == "IfExp")
        self.assertEqual(ifexp.get("resolved_type"), "str | None")

    def test_ifexp_infers_union_for_distinct_non_none_branches(self) -> None:
        east2 = _resolve(
            """\
def f(flag: bool):
    out = 1 if flag else "x"
    return out
"""
        )

        ifexp = next(node for node in _walk(east2) if node.get("kind") == "IfExp")
        self.assertEqual(ifexp.get("resolved_type"), "int64 | str")

    def test_ifexp_keeps_shared_branch_type_for_guarded_dict_access(self) -> None:
        east2 = _resolve(
            """\
def f(summary: dict[str, str]) -> str:
    out = summary["mirror"] if "mirror" in summary else ""
    return out
"""
        )

        ifexp = next(node for node in _walk(east2) if node.get("kind") == "IfExp")
        self.assertEqual(ifexp.get("resolved_type"), "str")

    def test_ifexp_unknown_branch_with_none_becomes_optional_any(self) -> None:
        east2 = _resolve(
            """\
type Node = dict[str, object]

def f(node: Node):
    out = node["kind"] if "kind" in node else None
    return out
"""
        )

        ifexp = next(node for node in _walk(east2) if node.get("kind") == "IfExp")
        self.assertEqual(ifexp.get("resolved_type"), "object | None")


if __name__ == "__main__":
    unittest.main()

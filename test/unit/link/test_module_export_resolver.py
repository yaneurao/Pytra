"""Unit tests for post-link module attribute type resolution."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.link.module_export_resolver import (
    _collect_module_exports,
    _build_import_module_map,
    resolve_module_attribute_types,
)


class _FakeModule:
    def __init__(self, module_id: str, east_doc: dict[str, object]) -> None:
        self.module_id = module_id
        self.east_doc = east_doc


class TestCollectModuleExports(unittest.TestCase):

    def test_annassign_constant(self) -> None:
        doc = {
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "pi"},
                    "annotation": "float64",
                    "decl_type": "float64",
                    "value": {"kind": "Constant", "value": 3.14159, "resolved_type": "float64"},
                },
            ],
        }
        exports = _collect_module_exports(doc)
        self.assertEqual(exports["pi"], "float64")

    def test_assign_variable(self) -> None:
        doc = {
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "sep", "resolved_type": "str"},
                    "decl_type": "str",
                },
            ],
        }
        exports = _collect_module_exports(doc)
        self.assertEqual(exports["sep"], "str")

    def test_function_def(self) -> None:
        doc = {
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "sqrt",
                    "return_type": "float64",
                    "body": [],
                },
            ],
        }
        exports = _collect_module_exports(doc)
        self.assertEqual(exports["sqrt"], "callable:float64")


class TestResolveModuleAttributeTypes(unittest.TestCase):

    def test_resolve_math_pi(self) -> None:
        math_mod = _FakeModule("pytra.std.math", {
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "pi"},
                    "decl_type": "float64",
                    "value": {"kind": "Constant", "value": 3.14, "resolved_type": "float64"},
                },
            ],
        })
        user_mod = _FakeModule("main", {
            "meta": {
                "import_bindings": [
                    {"module_id": "pytra.std.math", "local_name": "math",
                     "binding_kind": "module", "export_name": ""},
                ],
            },
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "test",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "BinOp",
                                "op": "Mult",
                                "left": {"kind": "Constant", "value": 2.0, "resolved_type": "float64"},
                                "right": {
                                    "kind": "Attribute",
                                    "value": {"kind": "Name", "id": "math"},
                                    "attr": "pi",
                                    "resolved_type": "unknown",
                                },
                            },
                        },
                    ],
                },
            ],
        })
        modules = (math_mod, user_mod)
        count = resolve_module_attribute_types(modules)
        self.assertGreater(count, 0)
        # Find the Attribute node and check resolved_type
        body = user_mod.east_doc["body"][0]["body"]
        attr_node = body[0]["value"]["right"]
        self.assertEqual(attr_node["resolved_type"], "float64")

    def test_no_resolve_for_known_type(self) -> None:
        math_mod = _FakeModule("pytra.std.math", {
            "body": [
                {"kind": "AnnAssign", "target": {"kind": "Name", "id": "pi"},
                 "decl_type": "float64"},
            ],
        })
        user_mod = _FakeModule("main", {
            "meta": {
                "import_bindings": [
                    {"module_id": "pytra.std.math", "local_name": "math",
                     "binding_kind": "module", "export_name": ""},
                ],
            },
            "body": [
                {
                    "kind": "Attribute",
                    "value": {"kind": "Name", "id": "math"},
                    "attr": "pi",
                    "resolved_type": "float64",  # already known
                },
            ],
        })
        count = resolve_module_attribute_types((math_mod, user_mod))
        self.assertEqual(count, 0)

    def test_alias_import_resolution(self) -> None:
        """from pytra.std import os_path as path → path.sep resolved."""
        os_path_mod = _FakeModule("pytra.std.os_path", {
            "body": [
                {"kind": "Assign", "target": {"kind": "Name", "id": "sep"},
                 "decl_type": "str"},
            ],
        })
        user_mod = _FakeModule("main", {
            "meta": {
                "import_bindings": [
                    {"module_id": "pytra.std", "local_name": "path",
                     "binding_kind": "symbol", "export_name": "os_path"},
                ],
            },
            "body": [
                {
                    "kind": "Attribute",
                    "value": {"kind": "Name", "id": "path"},
                    "attr": "sep",
                    "resolved_type": "unknown",
                },
            ],
        })
        count = resolve_module_attribute_types((os_path_mod, user_mod))
        self.assertGreater(count, 0)
        self.assertEqual(user_mod.east_doc["body"][0]["resolved_type"], "str")


if __name__ == "__main__":
    unittest.main()

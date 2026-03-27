from __future__ import annotations

import unittest
from unittest.mock import patch

from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.emit.common.profile_loader import LoweringProfile
from toolchain2.emit.cpp.emitter import emit_cpp_module
from toolchain2.emit.go.emitter import emit_go_module


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


class ProfileLoweringSemanticsTests(unittest.TestCase):
    def test_try_finally_profile_lowers_with_statement(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "With",
                            "context_expr": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "open", "resolved_type": "callable"},
                                "args": [{"kind": "Constant", "value": "x.txt", "resolved_type": "str"}],
                                "keywords": [],
                                "resolved_type": "File",
                            },
                            "var_name": "fobj",
                            "body": [],
                        }
                    ],
                }
            ],
        }
        profile = LoweringProfile(
            tuple_unpack_style="individual_temps",
            container_covariance=False,
            closure_style="closure_syntax",
            with_style="try_finally",
            property_style="method_call",
            swap_style="temp_var",
        )

        with patch("toolchain2.compile.lower.load_lowering_profile", return_value=profile):
            east3 = lower_east2_to_east3(east2, target_language="core")

        fn = next(node for node in _walk(east3) if node.get("kind") == "FunctionDef" and node.get("name") == "f")
        body = fn.get("body", [])
        self.assertEqual(body[0].get("kind"), "Assign")
        self.assertEqual(body[0].get("target", {}).get("id"), "fobj")
        self.assertEqual(body[1].get("kind"), "Try")
        self.assertEqual(body[1].get("finalbody", [])[0].get("value", {}).get("func", {}).get("attr"), "close")
        self.assertFalse(any(node.get("kind") == "With" for node in _walk(east3)))

    def test_field_access_profile_clears_property_getter_marker(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "read_prop",
                    "arg_types": {"obj": "Thing"},
                    "arg_order": ["obj"],
                    "arg_defaults": {},
                    "arg_index": {"obj": 0},
                    "return_type": "int64",
                    "arg_usage": {"obj": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "resolved_type": "int64",
                                "attribute_access_kind": "property_getter",
                                "value": {"kind": "Name", "id": "obj", "resolved_type": "Thing"},
                                "attr": "size",
                            },
                        }
                    ],
                }
            ],
        }
        profile = LoweringProfile(
            tuple_unpack_style="individual_temps",
            container_covariance=False,
            closure_style="closure_syntax",
            with_style="try_finally",
            property_style="field_access",
            swap_style="temp_var",
        )

        with patch("toolchain2.compile.lower.load_lowering_profile", return_value=profile):
            east3 = lower_east2_to_east3(east2, target_language="core")

        attr = next(node for node in _walk(east3) if node.get("kind") == "Attribute")
        self.assertEqual(attr.get("attribute_access_kind"), "field_access")

    def test_covariant_copy_is_lowered_and_emitted_for_list_constructor(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"params": "list[str]"},
                    "arg_order": ["params"],
                    "arg_defaults": {},
                    "arg_index": {"params": 0},
                    "return_type": "list[JsonVal]",
                    "arg_usage": {"params": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "xs", "resolved_type": "list[JsonVal]"},
                            "annotation": "list[JsonVal]",
                            "decl_type": "list[JsonVal]",
                            "declare": True,
                            "value": {
                                "kind": "Call",
                                "resolved_type": "list[JsonVal]",
                                "func": {"kind": "Name", "id": "list", "resolved_type": "type"},
                                "args": [{"kind": "Name", "id": "params", "resolved_type": "list[str]"}],
                                "keywords": [],
                            },
                        },
                        {
                            "kind": "Return",
                            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[JsonVal]"},
                        },
                    ],
                }
            ],
        }

        east3_go = lower_east2_to_east3(east2, target_language="go")
        covariant = next(node for node in _walk(east3_go) if node.get("kind") == "CovariantCopy")

        self.assertEqual(covariant.get("source_type"), "list[str]")
        self.assertEqual(covariant.get("target_type"), "list[JsonVal]")

        go_code = emit_go_module(east3_go)
        self.assertIn("make([]any, len(params))", go_code)
        self.assertIn("for ", go_code)
        self.assertIn("range params", go_code)

        east3_cpp = lower_east2_to_east3(east2, target_language="cpp")
        cpp_code = emit_cpp_module(east3_cpp)
        self.assertIn("push_back", cpp_code)
        self.assertIn("for (auto const&", cpp_code)


if __name__ == "__main__":
    unittest.main()

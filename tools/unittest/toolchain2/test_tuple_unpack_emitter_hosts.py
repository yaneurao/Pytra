from __future__ import annotations

import unittest

from toolchain.emit.dart.emitter import emit_dart_module
from toolchain.emit.zig.emitter import emit_zig_module


def _tuple_unpack_doc(kind: str) -> dict:
    return {
        "kind": "Module",
        "east_stage": 3,
        "meta": {
            "emit_context": {
                "module_id": "app",
                "root_rel_prefix": "./",
                "is_entry": False,
            }
        },
        "body": [
            {
                "kind": "FunctionDef",
                "name": "f",
                "arg_order": [],
                "return_type": "int64",
                "body": [
                    {
                        "kind": kind,
                        "declare": True,
                        "targets": [
                            {"kind": "Name", "id": "x", "resolved_type": "int64"},
                            {"kind": "Name", "id": "y", "resolved_type": "int64"},
                        ],
                        "target_types": ["int64", "int64"],
                        "value": {
                            "kind": "Tuple",
                            "resolved_type": "tuple[int64,int64]",
                            "elements": [
                                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                            ],
                        },
                    },
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "BinOp",
                            "op": "Add",
                            "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                            "right": {"kind": "Name", "id": "y", "resolved_type": "int64"},
                            "resolved_type": "int64",
                        },
                    },
                ],
            }
        ],
    }


class TupleUnpackEmitterHostTests(unittest.TestCase):
    def test_dart_emits_tuple_unpack_stmt(self) -> None:
        code = emit_dart_module(_tuple_unpack_doc("TupleUnpack"))

        self.assertIn("var __pytraTuple_", code)
        self.assertIn("var x = __pytraTuple_", code)
        self.assertIn("var y = __pytraTuple_", code)
        self.assertIn("return pytraInt((x + y));", code)

    def test_dart_emits_multi_assign_stmt(self) -> None:
        code = emit_dart_module(_tuple_unpack_doc("MultiAssign"))

        self.assertIn("var __pytraTuple_", code)
        self.assertIn("var x = __pytraTuple_", code)
        self.assertIn("var y = __pytraTuple_", code)

    def test_zig_emits_tuple_unpack_stmt(self) -> None:
        code = emit_zig_module(_tuple_unpack_doc("TupleUnpack"))

        self.assertIn("const __tmp_", code)
        self.assertIn("const x = __tmp_", code)
        self.assertIn("const y = __tmp_", code)
        self.assertIn("return (x + y);", code)

    def test_zig_emits_multi_assign_stmt(self) -> None:
        code = emit_zig_module(_tuple_unpack_doc("MultiAssign"))

        self.assertIn("const __tmp_", code)
        self.assertIn("const x = __tmp_", code)
        self.assertIn("const y = __tmp_", code)


if __name__ == "__main__":
    unittest.main()

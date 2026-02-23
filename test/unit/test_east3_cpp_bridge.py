from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2cpp import CppEmitter, load_east
from src.pytra.compiler.transpile_cli import collect_symbols_from_stmt, parse_py2cpp_argv


def _const_i(v: int) -> dict[str, object]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(v),
        "value": v,
    }


class East3CppBridgeTest(unittest.TestCase):
    def test_emit_stmt_forcore_static_range(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        stmt = {
            "kind": "ForCore",
            "iter_mode": "static_fastpath",
            "iter_plan": {
                "kind": "StaticRangeForPlan",
                "start": _const_i(0),
                "stop": _const_i(3),
                "step": _const_i(1),
            },
            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        emitter.emit_stmt(stmt)
        text = "\n".join(emitter.lines)
        self.assertIn("for (int64 i = 0; i < 3; ++i)", text)

    def test_emit_stmt_forcore_runtime_iter_plan(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": {"kind": "Name", "id": "xs", "resolved_type": "object"},
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {"kind": "NameTarget", "id": "x", "target_type": "object"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        emitter.emit_stmt(stmt)
        text = "\n".join(emitter.lines)
        self.assertIn("py_dyn_range(xs)", text)

    def test_render_expr_supports_east3_obj_boundary_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        any_name = {"kind": "Name", "id": "v", "resolved_type": "Any"}

        obj_len = {"kind": "ObjLen", "value": any_name, "resolved_type": "int64"}
        obj_bool = {"kind": "ObjBool", "value": any_name, "resolved_type": "bool"}
        obj_str = {"kind": "ObjStr", "value": any_name, "resolved_type": "str"}
        obj_iter = {"kind": "ObjIterInit", "value": any_name, "resolved_type": "object"}
        obj_next = {"kind": "ObjIterNext", "iter": any_name, "resolved_type": "object"}
        box_expr = {"kind": "Box", "value": _const_i(1), "resolved_type": "object"}
        unbox_expr = {"kind": "Unbox", "value": any_name, "target": "int64", "resolved_type": "int64"}

        self.assertEqual(emitter.render_expr(obj_len), "py_len(v)")
        self.assertEqual(emitter.render_expr(obj_bool), "py_to_bool(v)")
        self.assertEqual(emitter.render_expr(obj_str), "py_to_string(v)")
        self.assertEqual(emitter.render_expr(obj_iter), "py_iter_or_raise(v)")
        self.assertEqual(emitter.render_expr(obj_next), "py_next_or_stop(v)")
        self.assertEqual(emitter.render_expr(box_expr), "make_object(1)")
        self.assertEqual(emitter.render_expr(unbox_expr), "int64(py_to_int64(v))")

    def test_collect_symbols_from_stmt_supports_forcore_target_plan(self) -> None:
        stmt = {
            "kind": "ForCore",
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "a"},
                    {"kind": "NameTarget", "id": "b"},
                ],
            },
            "body": [],
            "orelse": [],
        }
        symbols = collect_symbols_from_stmt(stmt)
        self.assertEqual(symbols, {"a", "b"})

    def test_parse_py2cpp_argv_accepts_east_stage_and_object_dispatch_mode(self) -> None:
        parsed = parse_py2cpp_argv(
            [
                "input.py",
                "--east-stage",
                "3",
                "--object-dispatch-mode",
                "type_id",
            ]
        )
        self.assertEqual(parsed.get("__error"), "")
        self.assertEqual(parsed.get("east_stage"), "3")
        self.assertEqual(parsed.get("object_dispatch_mode_opt"), "type_id")

    def test_load_east_stage3_applies_dispatch_mode_override(self) -> None:
        payload = {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x", "resolved_type": "object"},
                    "target_type": "object",
                    "iter_mode": "runtime_protocol",
                    "iter": {"kind": "Name", "id": "xs", "resolved_type": "object"},
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "in.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east(p, east_stage="3", object_dispatch_mode="type_id")
        self.assertEqual(out.get("east_stage"), 3)
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")
        body = out.get("body", [])
        self.assertEqual(body[0].get("kind"), "ForCore")
        self.assertEqual(body[0].get("iter_plan", {}).get("dispatch_mode"), "type_id")


if __name__ == "__main__":
    unittest.main()

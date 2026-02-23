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

    def test_emit_stmt_for_runtime_protocol_typed_target_uses_unbox_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        stmt = {
            "kind": "For",
            "target": {"kind": "Name", "id": "v", "resolved_type": "int64"},
            "target_type": "int64",
            "iter_mode": "runtime_protocol",
            "iter": {"kind": "Name", "id": "xs", "resolved_type": "object"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        emitter.emit_stmt(stmt)
        text = "\n".join(emitter.lines)
        self.assertIn("for (object __itobj", text)
        self.assertIn("int64 v = int64(py_to_int64(__itobj", text)

    def test_render_expr_supports_east3_obj_boundary_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter.ref_classes = {"Base"}
        any_name = {"kind": "Name", "id": "v", "resolved_type": "Any"}

        obj_len = {"kind": "ObjLen", "value": any_name, "resolved_type": "int64"}
        obj_bool = {"kind": "ObjBool", "value": any_name, "resolved_type": "bool"}
        obj_str = {"kind": "ObjStr", "value": any_name, "resolved_type": "str"}
        obj_iter = {"kind": "ObjIterInit", "value": any_name, "resolved_type": "object"}
        obj_next = {"kind": "ObjIterNext", "iter": any_name, "resolved_type": "object"}
        obj_type_id = {"kind": "ObjTypeId", "value": any_name, "resolved_type": "int64"}
        box_expr = {"kind": "Box", "value": _const_i(1), "resolved_type": "object"}
        unbox_expr = {"kind": "Unbox", "value": any_name, "target": "int64", "resolved_type": "int64"}
        is_instance = {
            "kind": "IsInstance",
            "value": any_name,
            "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_INT", "resolved_type": "int64"},
            "resolved_type": "bool",
        }
        is_instance_class = {
            "kind": "IsInstance",
            "value": any_name,
            "expected_type_id": {"kind": "Name", "id": "Base", "resolved_type": "unknown"},
            "resolved_type": "bool",
        }
        is_subclass = {
            "kind": "IsSubclass",
            "actual_type_id": _const_i(1001),
            "expected_type_id": _const_i(1000),
            "resolved_type": "bool",
        }
        is_subtype = {
            "kind": "IsSubtype",
            "actual_type_id": _const_i(1001),
            "expected_type_id": _const_i(1000),
            "resolved_type": "bool",
        }

        self.assertEqual(emitter.render_expr(obj_len), "py_len(v)")
        self.assertEqual(emitter.render_expr(obj_bool), "py_to_bool(v)")
        self.assertEqual(emitter.render_expr(obj_str), "py_to_string(v)")
        self.assertEqual(emitter.render_expr(obj_iter), "py_iter_or_raise(v)")
        self.assertEqual(emitter.render_expr(obj_next), "py_next_or_stop(v)")
        self.assertEqual(emitter.render_expr(obj_type_id), "py_runtime_type_id(v)")
        self.assertEqual(emitter.render_expr(box_expr), "make_object(1)")
        self.assertEqual(emitter.render_expr(unbox_expr), "int64(py_to_int64(v))")
        self.assertEqual(
            emitter.render_expr(is_instance),
            "py_isinstance(v, PYTRA_TID_INT)",
        )
        self.assertEqual(
            emitter.render_expr(is_instance_class),
            "py_isinstance(v, Base::PYTRA_TYPE_ID)",
        )
        self.assertEqual(
            emitter.render_expr(is_subclass),
            "py_issubclass(1001, 1000)",
        )
        self.assertEqual(
            emitter.render_expr(is_subtype),
            "py_is_subtype(1001, 1000)",
        )

    def test_render_cond_for_any_routes_to_objbool(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        any_name = {"kind": "Name", "id": "v", "resolved_type": "Any"}
        self.assertEqual(emitter.render_cond(any_name), "py_to_bool(v)")

    def test_render_unbox_honors_ctx_for_refclass_cast(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter.ref_classes = {"Box"}
        any_name = {"kind": "Name", "id": "arg", "resolved_type": "Any"}
        unbox_ref = {
            "kind": "Unbox",
            "value": any_name,
            "target": "Box",
            "ctx": "call_arg:Box",
            "resolved_type": "Box",
        }
        self.assertEqual(
            emitter.render_expr(unbox_ref),
            'obj_to_rc_or_raise<Box>(arg, "call_arg:Box")',
        )

    def test_box_any_target_value_handles_none_and_plain_values(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        int_name = {"kind": "Name", "id": "n", "resolved_type": "int64"}
        any_name = {"kind": "Name", "id": "v", "resolved_type": "Any"}
        none_node = {"kind": "Constant", "value": None, "resolved_type": "None"}

        boxed_int = emitter._box_any_target_value("n", int_name)
        boxed_any = emitter._box_any_target_value("v", any_name)
        boxed_none = emitter._box_any_target_value("std::nullopt", none_node)

        self.assertEqual(boxed_int, "make_object(n)")
        self.assertEqual(boxed_any, "make_object(v)")
        self.assertEqual(boxed_none, "object{}")

    def test_coerce_args_for_module_function_boxes_any_target_param(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter._module_fn_arg_type_cache["pkg.mod"] = {"f": ["Any"]}
        arg_node = {"kind": "Name", "id": "n", "resolved_type": "int64"}
        out = emitter._coerce_args_for_module_function("pkg.mod", "f", ["n"], [arg_node])
        self.assertEqual(out, ["make_object(n)"])

    def test_coerce_dict_key_expr_boxes_any_key_type(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "d", "resolved_type": "dict[Any, int64]"}
        key_node = _const_i(7)
        out = emitter._coerce_dict_key_expr(owner, "7", key_node)
        self.assertEqual(out, "make_object(7)")

    def test_render_append_call_object_method_boxes_list_any_arg(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner_types = ["list[Any]"]
        arg_node = {"kind": "Name", "id": "n", "resolved_type": "int64"}
        out = emitter._render_append_call_object_method(owner_types, "xs", ["n"], [arg_node])
        self.assertEqual(out, "xs.append(make_object(n))")

    def test_render_expr_supports_list_append_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "ListAppend",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[Any]"},
            "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(node), "xs.append(make_object(n))")

    def test_builtin_runtime_list_append_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.append",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[Any]"},
                "attr": "append",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "xs.append(make_object(n))")

    def test_render_expr_supports_list_extend_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "ListExtend",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "value": {"kind": "Name", "id": "ys", "resolved_type": "list[int64]"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(node), "xs.insert(xs.end(), ys.begin(), ys.end())")

    def test_builtin_runtime_list_extend_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.extend",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "extend",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "ys", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "xs.insert(xs.end(), ys.begin(), ys.end())")

    def test_render_expr_supports_set_add_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "SetAdd",
            "owner": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
            "value": {"kind": "Name", "id": "v", "resolved_type": "int64"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(node), "s.insert(v)")

    def test_builtin_runtime_set_add_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "set.add",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
                "attr": "add",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "v", "resolved_type": "int64"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "s.insert(v)")

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

    def test_builtin_any_boundary_helper_builds_obj_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        any_arg = {"kind": "Name", "id": "x", "resolved_type": "object"}

        out_bool = emitter._build_any_boundary_expr_from_builtin_call("bool", "static_cast", [any_arg])
        out_len = emitter._build_any_boundary_expr_from_builtin_call("len", "py_len", [any_arg])
        out_str = emitter._build_any_boundary_expr_from_builtin_call("str", "py_to_string", [any_arg])
        out_iter = emitter._build_any_boundary_expr_from_builtin_call("iter", "", [any_arg])
        out_next = emitter._build_any_boundary_expr_from_builtin_call("next", "", [any_arg])

        self.assertEqual(out_bool.get("kind"), "ObjBool")
        self.assertEqual(out_len.get("kind"), "ObjLen")
        self.assertEqual(out_str.get("kind"), "ObjStr")
        self.assertEqual(out_iter.get("kind"), "ObjIterInit")
        self.assertEqual(out_next.get("kind"), "ObjIterNext")

        concrete_arg = {"kind": "Name", "id": "n", "resolved_type": "int64"}
        out_none = emitter._build_any_boundary_expr_from_builtin_call("bool", "static_cast", [concrete_arg])
        self.assertIsNone(out_none)

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

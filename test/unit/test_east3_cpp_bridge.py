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

    def test_forrange_stmt_to_forcore_builds_static_range_plan(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        stmt = {
            "kind": "ForRange",
            "target": {"kind": "Name", "id": "i", "resolved_type": "int64"},
            "target_type": "int64",
            "start": _const_i(0),
            "stop": _const_i(4),
            "step": _const_i(1),
            "range_mode": "ascending",
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        out = emitter._forrange_stmt_to_forcore(stmt)
        self.assertEqual(out.get("kind"), "ForCore")
        self.assertEqual(out.get("iter_mode"), "static_fastpath")
        iter_plan = out.get("iter_plan", {})
        self.assertEqual(iter_plan.get("kind"), "StaticRangeForPlan")
        self.assertEqual(iter_plan.get("range_mode"), "ascending")

    def test_for_stmt_to_forcore_builds_runtime_plan_for_runtime_protocol(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"dispatch_mode": "type_id"}}, {})
        stmt = {
            "kind": "For",
            "target": {"kind": "Name", "id": "x", "resolved_type": "object"},
            "target_type": "object",
            "iter_mode": "runtime_protocol",
            "iter": {"kind": "Name", "id": "xs", "resolved_type": "object"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        out = emitter._for_stmt_to_forcore(stmt)
        self.assertEqual(out.get("kind"), "ForCore")
        self.assertEqual(out.get("iter_mode"), "runtime_protocol")
        iter_plan = out.get("iter_plan", {})
        self.assertEqual(iter_plan.get("kind"), "RuntimeIterForPlan")
        self.assertEqual(iter_plan.get("dispatch_mode"), "type_id")

    def test_for_stmt_to_forcore_keeps_static_for_each_on_legacy_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        stmt = {
            "kind": "For",
            "target": {"kind": "Name", "id": "x", "resolved_type": "int64"},
            "target_type": "int64",
            "iter_mode": "static_fastpath",
            "iter": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        out = emitter._for_stmt_to_forcore(stmt)
        self.assertEqual(out, {})

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

    def test_legacy_type_id_name_call_rejected_in_east3(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"east_stage": "3"}}, {})
        call_expr = {
            "kind": "Call",
            "func": {"kind": "Name", "id": "isinstance", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "v", "resolved_type": "Any"},
                {"kind": "Name", "id": "int", "resolved_type": "unknown"},
            ],
            "keywords": [],
            "resolved_type": "bool",
        }
        with self.assertRaisesRegex(ValueError, "type_id call must be lowered to EAST3 node: isinstance"):
            emitter.render_expr(call_expr)

    def test_legacy_type_id_name_call_allowed_in_east2_compat(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"east_stage": "2"}}, {})
        call_expr = {
            "kind": "Call",
            "func": {"kind": "Name", "id": "isinstance", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "v", "resolved_type": "Any"},
                {"kind": "Name", "id": "int", "resolved_type": "unknown"},
            ],
            "keywords": [],
            "resolved_type": "bool",
        }
        self.assertEqual(emitter.render_expr(call_expr), "py_isinstance(v, PYTRA_TID_INT)")

    def test_builtin_call_without_runtime_call_rejected_in_east3(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"east_stage": "3"}}, {})
        call_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "builtin_name": "bytes",
            "runtime_call": "",
            "func": {"kind": "Name", "id": "bytes", "resolved_type": "unknown"},
            "args": [],
            "keywords": [],
            "resolved_type": "bytes",
        }
        with self.assertRaisesRegex(ValueError, "builtin call must define runtime_call in EAST3: bytes"):
            emitter.render_expr(call_expr)

    def test_builtin_call_without_runtime_call_allowed_for_stage2_selfhost_compat(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"east_stage": "2", "parser_backend": "self_hosted"}}, {})
        call_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "builtin_name": "bytes",
            "runtime_call": "",
            "func": {"kind": "Name", "id": "bytes", "resolved_type": "unknown"},
            "args": [],
            "keywords": [],
            "resolved_type": "bytes",
        }
        self.assertEqual(emitter.render_expr(call_expr), "bytes{}")

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

    def test_coerce_any_expr_to_target_via_unbox_prefers_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        any_name = {"kind": "Name", "id": "v", "resolved_type": "Any"}
        emitter._coerce_any_expr_to_target = lambda *_args, **_kwargs: "LEGACY_PATH_USED"  # type: ignore[method-assign]
        self.assertEqual(
            emitter._coerce_any_expr_to_target_via_unbox("v", any_name, "int64", "assign:x"),
            "int64(py_to_int64(v))",
        )

    def test_emit_return_stmt_prefers_unbox_ir_over_legacy_coerce(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter.current_function_return_type = "int64"
        emitter._coerce_any_expr_to_target = lambda *_args, **_kwargs: "LEGACY_PATH_USED"  # type: ignore[method-assign]
        stmt = {
            "kind": "Return",
            "value": {"kind": "Name", "id": "v", "resolved_type": "Any"},
        }
        emitter._emit_return_stmt(stmt)
        text = "\n".join(emitter.lines)
        self.assertIn("return int64(py_to_int64(v));", text)
        self.assertNotIn("LEGACY_PATH_USED", text)

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

    def test_builtin_runtime_list_append_uses_runtime_owner_when_func_value_missing(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.append",
            "runtime_owner": {"kind": "Name", "id": "xs", "resolved_type": "list[Any]"},
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "attr": "append",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "xs.append(make_object(n))")

    def test_builtin_runtime_list_append_requires_owner(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.append",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "attr": "append",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
            "keywords": [],
        }
        with self.assertRaisesRegex(ValueError, "builtin runtime owner is required: list.append"):
            emitter.render_expr(expr)

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

    def test_render_expr_supports_list_pop_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node_no_index = {
            "kind": "ListPop",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "int64",
        }
        node_with_index = {
            "kind": "ListPop",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "index": {"kind": "Name", "id": "i", "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        self.assertEqual(emitter.render_expr(node_no_index), "xs.pop()")
        self.assertEqual(emitter.render_expr(node_with_index), "xs.pop(i)")

    def test_builtin_runtime_list_pop_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.pop",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "pop",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "xs.pop()")

    def test_render_expr_supports_list_clear_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "ListClear",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(node), "xs.clear()")

    def test_builtin_runtime_list_clear_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.clear",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "clear",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "xs.clear()")

    def test_render_expr_supports_list_reverse_and_sort_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        reverse_node = {
            "kind": "ListReverse",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "None",
        }
        sort_node = {
            "kind": "ListSort",
            "owner": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(reverse_node), "::std::reverse(xs.begin(), xs.end())")
        self.assertEqual(emitter.render_expr(sort_node), "::std::sort(xs.begin(), xs.end())")

    def test_builtin_runtime_list_reverse_and_sort_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        reverse_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.reverse",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "reverse",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        sort_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list.sort",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "sort",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(reverse_expr), "::std::reverse(xs.begin(), xs.end())")
        self.assertEqual(emitter.render_expr(sort_expr), "::std::sort(xs.begin(), xs.end())")

    def test_render_expr_supports_set_erase_and_clear_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        erase_node = {
            "kind": "SetErase",
            "owner": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
            "value": {"kind": "Name", "id": "v", "resolved_type": "int64"},
            "resolved_type": "None",
        }
        clear_node = {
            "kind": "SetClear",
            "owner": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
            "resolved_type": "None",
        }
        self.assertEqual(emitter.render_expr(erase_node), "s.erase(v)")
        self.assertEqual(emitter.render_expr(clear_node), "s.clear()")

    def test_builtin_runtime_set_erase_and_clear_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        erase_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "set.remove",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
                "attr": "remove",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "v", "resolved_type": "int64"}],
            "keywords": [],
        }
        clear_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "set.clear",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "set[int64]"},
                "attr": "clear",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(erase_expr), "s.erase(v)")
        self.assertEqual(emitter.render_expr(clear_expr), "s.clear()")

    def test_render_expr_supports_dict_view_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"}
        items_node = {"kind": "DictItems", "owner": owner, "resolved_type": "dict_items[str, int64]"}
        keys_node = {"kind": "DictKeys", "owner": owner, "resolved_type": "list[str]"}
        values_node = {"kind": "DictValues", "owner": owner, "resolved_type": "list[int64]"}
        self.assertEqual(emitter.render_expr(items_node), "d")
        self.assertEqual(emitter.render_expr(keys_node), "py_dict_keys(d)")
        self.assertEqual(emitter.render_expr(values_node), "py_dict_values(d)")

    def test_builtin_runtime_dict_views_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        items_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.items",
            "resolved_type": "dict_items[str, int64]",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "items",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        keys_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.keys",
            "resolved_type": "list[str]",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "keys",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        values_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.values",
            "resolved_type": "list[int64]",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "values",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(items_expr), "d")
        self.assertEqual(emitter.render_expr(keys_expr), "py_dict_keys(d)")
        self.assertEqual(emitter.render_expr(values_expr), "py_dict_values(d)")

    def test_render_expr_supports_dict_pop_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "DictPop",
            "owner": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
            "key": {"kind": "Name", "id": "k", "resolved_type": "str"},
            "resolved_type": "int64",
        }
        self.assertEqual(emitter.render_expr(node), "d.pop(py_to_string(k))")

    def test_builtin_runtime_dict_pop_without_default_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        pop_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.pop",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "pop",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "k", "resolved_type": "str"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(pop_expr), "d.pop(py_to_string(k))")

    def test_render_expr_supports_dict_pop_default_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "DictPopDefault",
            "owner": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
            "key": {"kind": "Name", "id": "k", "resolved_type": "str"},
            "default": {"kind": "Constant", "value": 7, "resolved_type": "int64"},
            "value_type": "int64",
            "resolved_type": "int64",
        }
        self.assertEqual(
            emitter.render_expr(node),
            "(d.contains(py_to_string(k)) ? d.pop(py_to_string(k)) : 7)",
        )

    def test_builtin_runtime_dict_pop_with_default_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        pop_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.pop",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "pop",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Name", "id": "k", "resolved_type": "str"},
                {"kind": "Constant", "value": 7, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        self.assertEqual(
            emitter.render_expr(pop_expr),
            "(d.contains(py_to_string(k)) ? d.pop(py_to_string(k)) : 7)",
        )

    def test_render_expr_supports_dict_get_maybe_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "DictGetMaybe",
            "owner": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
            "key": {"kind": "Name", "id": "k", "resolved_type": "str"},
            "resolved_type": "optional[int64]",
        }
        self.assertEqual(emitter.render_expr(node), "py_dict_get_maybe(d, py_to_string(k))")

    def test_builtin_runtime_dict_get_without_default_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        get_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.get",
            "resolved_type": "optional[int64]",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "get",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "k", "resolved_type": "str"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(get_expr), "py_dict_get_maybe(d, py_to_string(k))")

    def test_render_expr_supports_dict_get_default_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        node = {
            "kind": "DictGetDefault",
            "owner": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
            "key": {"kind": "Name", "id": "k", "resolved_type": "str"},
            "default": {"kind": "Constant", "value": 7, "resolved_type": "int64"},
            "out_type": "int64",
            "default_type": "int64",
            "owner_value_type": "int64",
            "objectish_owner": False,
            "owner_optional_object_dict": False,
            "resolved_type": "int64",
        }
        self.assertEqual(emitter.render_expr(node), "d.get(py_to_string(k), 7)")

    def test_builtin_runtime_dict_get_with_default_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        get_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict.get",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "d", "resolved_type": "dict[str, int64]"},
                "attr": "get",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Name", "id": "k", "resolved_type": "str"},
                {"kind": "Constant", "value": 7, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(get_expr), "d.get(py_to_string(k), 7)")

    def test_render_expr_supports_str_strip_op_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "s", "resolved_type": "str"}
        strip_node = {"kind": "StrStripOp", "mode": "strip", "owner": owner, "resolved_type": "str"}
        strip_chars_node = {
            "kind": "StrStripOp",
            "mode": "strip",
            "owner": owner,
            "chars": {"kind": "Constant", "value": "x", "resolved_type": "str"},
            "resolved_type": "str",
        }
        lstrip_node = {"kind": "StrStripOp", "mode": "lstrip", "owner": owner, "resolved_type": "str"}
        rstrip_node = {"kind": "StrStripOp", "mode": "rstrip", "owner": owner, "resolved_type": "str"}
        self.assertEqual(emitter.render_expr(strip_node), "py_strip(s)")
        self.assertEqual(emitter.render_expr(strip_chars_node), 's.strip("x")')
        self.assertEqual(emitter.render_expr(lstrip_node), "py_lstrip(s)")
        self.assertEqual(emitter.render_expr(rstrip_node), "py_rstrip(s)")

    def test_builtin_runtime_py_strip_uses_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        strip_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_strip",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "strip",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        strip_chars_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_strip",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "strip",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": "x", "resolved_type": "str"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(strip_expr), "py_strip(s)")
        self.assertEqual(emitter.render_expr(strip_chars_expr), 's.strip("x")')

    def test_render_expr_supports_str_starts_ends_with_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "s", "resolved_type": "str"}
        needle = {"kind": "Constant", "value": "x", "resolved_type": "str"}
        starts_node = {
            "kind": "StrStartsEndsWith",
            "mode": "startswith",
            "owner": owner,
            "needle": needle,
            "resolved_type": "bool",
        }
        ends_slice_node = {
            "kind": "StrStartsEndsWith",
            "mode": "endswith",
            "owner": owner,
            "needle": needle,
            "start": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            "end": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
            "resolved_type": "bool",
        }
        self.assertEqual(emitter.render_expr(starts_node), 'py_startswith(s, "x")')
        self.assertEqual(
            emitter.render_expr(ends_slice_node),
            'py_endswith(py_slice(s, py_to_int64(1), py_to_int64(3)), "x")',
        )

    def test_builtin_runtime_py_startswith_endswith_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        starts_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_startswith",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "startswith",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": "x", "resolved_type": "str"}],
            "keywords": [],
        }
        ends_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_endswith",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "endswith",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Constant", "value": "x", "resolved_type": "str"},
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 3, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(starts_expr), 'py_startswith(s, "x")')
        self.assertEqual(
            emitter.render_expr(ends_expr),
            'py_endswith(py_slice(s, py_to_int64(1), py_to_int64(3)), "x")',
        )

    def test_render_expr_supports_str_find_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "s", "resolved_type": "str"}
        needle = {"kind": "Constant", "value": "x", "resolved_type": "str"}
        find_node = {
            "kind": "StrFindOp",
            "mode": "find",
            "owner": owner,
            "needle": needle,
            "resolved_type": "int64",
        }
        rfind_node = {
            "kind": "StrFindOp",
            "mode": "rfind",
            "owner": owner,
            "needle": needle,
            "start": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            "end": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        self.assertEqual(emitter.render_expr(find_node), 'py_find(s, "x")')
        self.assertEqual(emitter.render_expr(rfind_node), 'py_rfind(s, "x", 1, 3)')

    def test_builtin_runtime_py_find_rfind_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        find_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_find",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "find",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": "x", "resolved_type": "str"}],
            "keywords": [],
        }
        rfind_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_rfind",
            "resolved_type": "int64",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "rfind",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Constant", "value": "x", "resolved_type": "str"},
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 3, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(find_expr), 'py_find(s, "x")')
        self.assertEqual(emitter.render_expr(rfind_expr), 'py_rfind(s, "x", 1, 3)')

    def test_render_expr_supports_str_char_class_ir_node(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        isdigit_node = {
            "kind": "StrCharClassOp",
            "mode": "isdigit",
            "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
            "resolved_type": "bool",
        }
        isalpha_node = {
            "kind": "StrCharClassOp",
            "mode": "isalpha",
            "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
            "resolved_type": "bool",
        }
        self.assertEqual(emitter.render_expr(isdigit_node), "s.isdigit()")
        self.assertEqual(emitter.render_expr(isalpha_node), "s.isalpha()")

    def test_builtin_runtime_py_isdigit_isalpha_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        isdigit_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_isdigit",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "isdigit",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        isalpha_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_isalpha",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "isalpha",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(isdigit_expr), "s.isdigit()")
        self.assertEqual(emitter.render_expr(isalpha_expr), "s.isalpha()")

    def test_render_expr_supports_str_replace_and_join_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "s", "resolved_type": "str"}
        replace_node = {
            "kind": "StrReplace",
            "owner": owner,
            "old": {"kind": "Constant", "value": "a", "resolved_type": "str"},
            "new": {"kind": "Constant", "value": "b", "resolved_type": "str"},
            "resolved_type": "str",
        }
        join_node = {
            "kind": "StrJoin",
            "owner": owner,
            "items": {"kind": "Name", "id": "xs", "resolved_type": "list[str]"},
            "resolved_type": "str",
        }
        self.assertEqual(emitter.render_expr(replace_node), 'py_replace(s, "a", "b")')
        self.assertEqual(emitter.render_expr(join_node), "str(s).join(xs)")

    def test_builtin_runtime_py_replace_py_join_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        replace_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_replace",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "replace",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Constant", "value": "a", "resolved_type": "str"},
                {"kind": "Constant", "value": "b", "resolved_type": "str"},
            ],
            "keywords": [],
        }
        join_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_join",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "join",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[str]"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(replace_expr), 'py_replace(s, "a", "b")')
        self.assertEqual(emitter.render_expr(join_expr), "str(s).join(xs)")

    def test_render_expr_supports_path_runtime_op_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        owner = {"kind": "Name", "id": "p", "resolved_type": "Path"}
        mkdir_node = {
            "kind": "PathRuntimeOp",
            "op": "mkdir",
            "owner": owner,
            "parents": {"kind": "Constant", "value": True, "resolved_type": "bool"},
            "exist_ok": {"kind": "Constant", "value": False, "resolved_type": "bool"},
            "resolved_type": "None",
        }
        exists_node = {"kind": "PathRuntimeOp", "op": "exists", "owner": owner, "resolved_type": "bool"}
        write_node = {
            "kind": "PathRuntimeOp",
            "op": "write_text",
            "owner": owner,
            "value": {"kind": "Constant", "value": "42", "resolved_type": "str"},
            "resolved_type": "None",
        }
        read_node = {"kind": "PathRuntimeOp", "op": "read_text", "owner": owner, "resolved_type": "str"}
        parent_node = {"kind": "PathRuntimeOp", "op": "parent", "owner": owner, "resolved_type": "Path"}
        name_node = {"kind": "PathRuntimeOp", "op": "name", "owner": owner, "resolved_type": "str"}
        stem_node = {"kind": "PathRuntimeOp", "op": "stem", "owner": owner, "resolved_type": "str"}
        identity_node = {"kind": "PathRuntimeOp", "op": "identity", "owner": owner, "resolved_type": "Path"}

        self.assertEqual(emitter.render_expr(mkdir_node), "p.mkdir(true, false)")
        self.assertEqual(emitter.render_expr(exists_node), "p.exists()")
        self.assertEqual(emitter.render_expr(write_node), 'p.write_text("42")')
        self.assertEqual(emitter.render_expr(read_node), "p.read_text()")
        self.assertEqual(emitter.render_expr(parent_node), "p.parent()")
        self.assertEqual(emitter.render_expr(name_node), "p.name()")
        self.assertEqual(emitter.render_expr(stem_node), "p.stem()")
        self.assertEqual(emitter.render_expr(identity_node), "p")

    def test_builtin_runtime_path_special_ops_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        mkdir_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::filesystem::create_directories",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "mkdir",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Constant", "value": True, "resolved_type": "bool"},
                {"kind": "Constant", "value": False, "resolved_type": "bool"},
            ],
            "keywords": [],
        }
        mkdir_kw_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::filesystem::create_directories",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "mkdir",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [
                {"arg": "parents", "value": {"kind": "Constant", "value": True, "resolved_type": "bool"}},
                {"arg": "exist_ok", "value": {"kind": "Constant", "value": True, "resolved_type": "bool"}},
            ],
        }
        exists_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::filesystem::exists",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "exists",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        write_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_write_text",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "write_text",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": "42", "resolved_type": "str"}],
            "keywords": [],
        }
        read_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_read_text",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "read_text",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        parent_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "path_parent",
            "resolved_type": "Path",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "parent",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        name_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "path_name",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "name",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        stem_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "path_stem",
            "resolved_type": "str",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "stem",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        identity_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "identity",
            "resolved_type": "Path",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "identity",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }

        self.assertEqual(emitter.render_expr(mkdir_expr), "p.mkdir(true, false)")
        self.assertEqual(emitter.render_expr(mkdir_kw_expr), "p.mkdir(true, true)")
        self.assertEqual(emitter.render_expr(exists_expr), "p.exists()")
        self.assertEqual(emitter.render_expr(write_expr), 'p.write_text("42")')
        self.assertEqual(emitter.render_expr(read_expr), "p.read_text()")
        self.assertEqual(emitter.render_expr(parent_expr), "p.parent()")
        self.assertEqual(emitter.render_expr(name_expr), "p.name()")
        self.assertEqual(emitter.render_expr(stem_expr), "p.stem()")
        self.assertEqual(emitter.render_expr(identity_expr), "p")

    def test_builtin_runtime_path_exists_uses_runtime_owner_when_func_value_missing(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::filesystem::exists",
            "runtime_owner": {"kind": "Name", "id": "p", "resolved_type": "Path"},
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "attr": "exists",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(expr), "p.exists()")

    def test_builtin_runtime_path_exists_requires_owner(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::filesystem::exists",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "attr": "exists",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        with self.assertRaisesRegex(ValueError, "builtin runtime owner is required: std::filesystem::exists"):
            emitter.render_expr(expr)

    def test_render_expr_supports_runtime_special_op_ir_nodes(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        print_node = {
            "kind": "RuntimeSpecialOp",
            "op": "print",
            "args": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": "x", "resolved_type": "str"},
            ],
            "resolved_type": "None",
        }
        len_node = {
            "kind": "RuntimeSpecialOp",
            "op": "len",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "int64",
        }
        to_string_node = {
            "kind": "RuntimeSpecialOp",
            "op": "to_string",
            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            "resolved_type": "str",
        }
        int_base_node = {
            "kind": "RuntimeSpecialOp",
            "op": "int_base",
            "args": [
                {"kind": "Constant", "value": "10", "resolved_type": "str"},
                {"kind": "Constant", "value": 16, "resolved_type": "int64"},
            ],
            "resolved_type": "int64",
        }
        static_cast_node = {
            "kind": "RuntimeSpecialOp",
            "op": "static_cast",
            "target": "int64",
            "value": {"kind": "Constant", "value": "10", "resolved_type": "str"},
            "resolved_type": "int64",
        }
        iter_node = {
            "kind": "RuntimeSpecialOp",
            "op": "iter_or_raise",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "object"},
            "resolved_type": "object",
        }
        next_node = {
            "kind": "RuntimeSpecialOp",
            "op": "next_or_stop",
            "value": {"kind": "Name", "id": "it", "resolved_type": "object"},
            "resolved_type": "object",
        }
        reversed_node = {
            "kind": "RuntimeSpecialOp",
            "op": "reversed",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "object",
        }
        enumerate_node = {
            "kind": "RuntimeSpecialOp",
            "op": "enumerate",
            "args": [
                {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            ],
            "resolved_type": "object",
        }
        any_node = {
            "kind": "RuntimeSpecialOp",
            "op": "any",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "bool",
        }
        all_node = {
            "kind": "RuntimeSpecialOp",
            "op": "all",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "resolved_type": "bool",
        }
        ord_node = {
            "kind": "RuntimeSpecialOp",
            "op": "ord",
            "value": {"kind": "Constant", "value": "A", "resolved_type": "str"},
            "resolved_type": "int64",
        }
        chr_node = {
            "kind": "RuntimeSpecialOp",
            "op": "chr",
            "value": {"kind": "Constant", "value": 65, "resolved_type": "int64"},
            "resolved_type": "str",
        }
        range_node = {
            "kind": "RuntimeSpecialOp",
            "op": "range",
            "args": [{"kind": "Constant", "value": 3, "resolved_type": "int64"}],
            "resolved_type": "range",
        }
        range_kw_node = {
            "kind": "RuntimeSpecialOp",
            "op": "range",
            "args": [],
            "kw_names": ["start", "stop", "step"],
            "kw_values": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 5, "resolved_type": "int64"},
                {"kind": "Constant", "value": 2, "resolved_type": "int64"},
            ],
            "resolved_type": "range",
        }
        zip_node = {
            "kind": "RuntimeSpecialOp",
            "op": "zip",
            "args": [
                {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                {"kind": "Name", "id": "ys", "resolved_type": "list[int64]"},
            ],
            "resolved_type": "list[tuple[int64,int64]]",
        }
        list_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "collection_ctor",
            "ctor_name": "list",
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "resolved_type": "list[int64]",
        }
        set_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "collection_ctor",
            "ctor_name": "set",
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "resolved_type": "set[int64]",
        }
        dict_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "collection_ctor",
            "ctor_name": "dict",
            "args": [{"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"}],
            "resolved_type": "dict[str,int64]",
        }
        minmax_node = {
            "kind": "RuntimeSpecialOp",
            "op": "minmax",
            "mode": "max",
            "args": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 2, "resolved_type": "int64"},
            ],
            "resolved_type": "int64",
        }
        perf_node = {"kind": "RuntimeSpecialOp", "op": "perf_counter", "resolved_type": "float64"}
        open_node = {
            "kind": "RuntimeSpecialOp",
            "op": "open",
            "args": [
                {"kind": "Constant", "value": "a.txt", "resolved_type": "str"},
                {"kind": "Constant", "value": "rb", "resolved_type": "str"},
            ],
            "resolved_type": "unknown",
        }
        path_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "path_ctor",
            "args": [{"kind": "Constant", "value": "a.txt", "resolved_type": "str"}],
            "resolved_type": "Path",
        }
        runtime_error_node = {
            "kind": "RuntimeSpecialOp",
            "op": "runtime_error",
            "message": {"kind": "Constant", "value": "boom", "resolved_type": "str"},
            "resolved_type": "::std::runtime_error",
        }
        int_to_bytes_node = {
            "kind": "RuntimeSpecialOp",
            "op": "int_to_bytes",
            "owner": {"kind": "Name", "id": "n", "resolved_type": "int64"},
            "length": {"kind": "Constant", "value": 4, "resolved_type": "int64"},
            "byteorder": {"kind": "Constant", "value": "little", "resolved_type": "str"},
            "resolved_type": "bytes",
        }
        bytes_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "bytes_ctor",
            "resolved_type": "bytes",
        }
        bytearray_ctor_node = {
            "kind": "RuntimeSpecialOp",
            "op": "bytearray_ctor",
            "args": [{"kind": "Constant", "value": b"\x01\x02", "resolved_type": "bytes"}],
            "resolved_type": "bytearray",
        }

        self.assertEqual(emitter.render_expr(print_node), 'py_print(1, "x")')
        self.assertEqual(emitter.render_expr(len_node), "py_len(xs)")
        self.assertEqual(emitter.render_expr(to_string_node), "::std::to_string(1)")
        self.assertEqual(emitter.render_expr(int_base_node), 'py_to_int64_base("10", py_to_int64(16))')
        self.assertEqual(emitter.render_expr(static_cast_node), 'py_to_int64("10")')
        self.assertEqual(emitter.render_expr(iter_node), "py_iter_or_raise(xs)")
        self.assertEqual(emitter.render_expr(next_node), "py_next_or_stop(it)")
        self.assertEqual(emitter.render_expr(reversed_node), "py_reversed(xs)")
        self.assertEqual(emitter.render_expr(enumerate_node), "py_enumerate(xs, py_to_int64(1))")
        self.assertEqual(emitter.render_expr(any_node), "py_any(xs)")
        self.assertEqual(emitter.render_expr(all_node), "py_all(xs)")
        self.assertEqual(emitter.render_expr(ord_node), 'py_ord("A")')
        self.assertEqual(emitter.render_expr(chr_node), "py_chr(65)")
        self.assertEqual(emitter.render_expr(range_node), "py_range(0, 3, 1)")
        self.assertEqual(emitter.render_expr(range_kw_node), "py_range(1, 5, 2)")
        self.assertEqual(emitter.render_expr(zip_node), "zip(xs, ys)")
        self.assertEqual(emitter.render_expr(list_ctor_node), "xs")
        self.assertEqual(emitter.render_expr(set_ctor_node), "set<int64>(xs)")
        self.assertEqual(emitter.render_expr(dict_ctor_node), "d")
        self.assertEqual(
            emitter.render_expr(minmax_node),
            "::std::max<int64>(static_cast<int64>(1), static_cast<int64>(2))",
        )
        self.assertEqual(emitter.render_expr(perf_node), "pytra::std::time::perf_counter()")
        self.assertEqual(emitter.render_expr(open_node), 'open("a.txt", "rb")')
        self.assertEqual(emitter.render_expr(path_ctor_node), 'Path("a.txt")')
        self.assertEqual(emitter.render_expr(runtime_error_node), '::std::runtime_error("boom")')
        self.assertEqual(emitter.render_expr(int_to_bytes_node), 'py_int_to_bytes(n, 4, "little")')
        self.assertEqual(emitter.render_expr(bytes_ctor_node), "bytes{}")
        self.assertEqual(emitter.render_expr(bytearray_ctor_node), "bytearray(b'\\x01\\x02')")

    def test_builtin_runtime_misc_special_ops_use_ir_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        print_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_print",
            "resolved_type": "None",
            "func": {"kind": "Name", "id": "print", "resolved_type": "unknown"},
            "args": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": "x", "resolved_type": "str"},
            ],
            "keywords": [],
        }
        len_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_len",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "len", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        to_string_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_to_string",
            "resolved_type": "str",
            "func": {"kind": "Name", "id": "str", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}],
            "keywords": [],
        }
        int_base_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_to_int64_base",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "int", "resolved_type": "unknown"},
            "args": [
                {"kind": "Constant", "value": "10", "resolved_type": "str"},
                {"kind": "Constant", "value": 16, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        iter_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_iter_or_raise",
            "resolved_type": "object",
            "func": {"kind": "Name", "id": "iter", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "object"}],
            "keywords": [],
        }
        next_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_next_or_stop",
            "resolved_type": "object",
            "func": {"kind": "Name", "id": "next", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "it", "resolved_type": "object"}],
            "keywords": [],
        }
        reversed_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_reversed",
            "resolved_type": "object",
            "func": {"kind": "Name", "id": "reversed", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        enumerate_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_enumerate",
            "resolved_type": "object",
            "func": {"kind": "Name", "id": "enumerate", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        zip_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "zip",
            "resolved_type": "list[tuple[int64,int64]]",
            "func": {"kind": "Name", "id": "zip", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                {"kind": "Name", "id": "ys", "resolved_type": "list[int64]"},
            ],
            "keywords": [],
        }
        any_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_any",
            "resolved_type": "bool",
            "func": {"kind": "Name", "id": "any", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        all_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_all",
            "resolved_type": "bool",
            "func": {"kind": "Name", "id": "all", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        ord_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_ord",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "ord", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": "A", "resolved_type": "str"}],
            "keywords": [],
        }
        chr_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_chr",
            "resolved_type": "str",
            "func": {"kind": "Name", "id": "chr", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": 65, "resolved_type": "int64"}],
            "keywords": [],
        }
        range_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_range",
            "resolved_type": "range",
            "func": {"kind": "Name", "id": "range", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": 3, "resolved_type": "int64"}],
            "keywords": [],
        }
        range_kw_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_range",
            "resolved_type": "range",
            "func": {"kind": "Name", "id": "range", "resolved_type": "unknown"},
            "args": [],
            "keywords": [
                {"arg": "start", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}},
                {"arg": "stop", "value": {"kind": "Constant", "value": 5, "resolved_type": "int64"}},
                {"arg": "step", "value": {"kind": "Constant", "value": 2, "resolved_type": "int64"}},
            ],
        }
        list_ctor_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "list_ctor",
            "resolved_type": "list[int64]",
            "func": {"kind": "Name", "id": "list", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        set_ctor_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "set_ctor",
            "resolved_type": "set[int64]",
            "func": {"kind": "Name", "id": "set", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "list[int64]"}],
            "keywords": [],
        }
        dict_ctor_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "dict_ctor",
            "resolved_type": "dict[str,int64]",
            "func": {"kind": "Name", "id": "dict", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "d", "resolved_type": "dict[str,int64]"}],
            "keywords": [],
        }
        max_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_max",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "max", "resolved_type": "unknown"},
            "args": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 2, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        min_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_min",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "min", "resolved_type": "unknown"},
            "args": [
                {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                {"kind": "Constant", "value": 2, "resolved_type": "int64"},
            ],
            "keywords": [],
        }
        perf_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "perf_counter",
            "resolved_type": "float64",
            "func": {"kind": "Name", "id": "perf_counter", "resolved_type": "unknown"},
            "args": [],
            "keywords": [],
        }
        open_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "open",
            "resolved_type": "unknown",
            "func": {"kind": "Name", "id": "open", "resolved_type": "unknown"},
            "args": [
                {"kind": "Constant", "value": "a.txt", "resolved_type": "str"},
                {"kind": "Constant", "value": "rb", "resolved_type": "str"},
            ],
            "keywords": [],
        }
        path_ctor_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "Path",
            "resolved_type": "Path",
            "func": {"kind": "Name", "id": "Path", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": "a.txt", "resolved_type": "str"}],
            "keywords": [],
        }
        runtime_error_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "std::runtime_error",
            "resolved_type": "::std::runtime_error",
            "func": {"kind": "Name", "id": "RuntimeError", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": "boom", "resolved_type": "str"}],
            "keywords": [],
        }
        int_to_bytes_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "runtime_call": "py_int_to_bytes",
            "resolved_type": "bytes",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                "attr": "to_bytes",
                "resolved_type": "unknown",
            },
            "args": [
                {"kind": "Constant", "value": 4, "resolved_type": "int64"},
                {"kind": "Constant", "value": "little", "resolved_type": "str"},
            ],
            "keywords": [],
        }
        bytes_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "builtin_name": "bytes",
            "runtime_call": "bytes_ctor",
            "resolved_type": "bytes",
            "func": {"kind": "Name", "id": "bytes", "resolved_type": "unknown"},
            "args": [],
            "keywords": [],
        }
        bytearray_expr = {
            "kind": "Call",
            "lowered_kind": "BuiltinCall",
            "builtin_name": "bytearray",
            "runtime_call": "bytearray_ctor",
            "resolved_type": "bytearray",
            "func": {"kind": "Name", "id": "bytearray", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": b"\x01\x02", "resolved_type": "bytes"}],
            "keywords": [],
        }

        self.assertEqual(emitter.render_expr(print_expr), 'py_print(1, "x")')
        self.assertEqual(emitter.render_expr(len_expr), "py_len(xs)")
        self.assertEqual(emitter.render_expr(to_string_expr), "::std::to_string(1)")
        self.assertEqual(emitter.render_expr(int_base_expr), 'py_to_int64_base("10", py_to_int64(16))')
        self.assertEqual(emitter.render_expr(iter_expr), "py_iter_or_raise(xs)")
        self.assertEqual(emitter.render_expr(next_expr), "py_next_or_stop(it)")
        self.assertEqual(emitter.render_expr(reversed_expr), "py_reversed(xs)")
        self.assertEqual(emitter.render_expr(enumerate_expr), "py_enumerate(xs, py_to_int64(1))")
        self.assertEqual(emitter.render_expr(zip_expr), "zip(xs, ys)")
        self.assertEqual(emitter.render_expr(any_expr), "py_any(xs)")
        self.assertEqual(emitter.render_expr(all_expr), "py_all(xs)")
        self.assertEqual(emitter.render_expr(ord_expr), 'py_ord("A")')
        self.assertEqual(emitter.render_expr(chr_expr), "py_chr(65)")
        self.assertEqual(emitter.render_expr(range_expr), "py_range(0, 3, 1)")
        self.assertEqual(emitter.render_expr(range_kw_expr), "py_range(1, 5, 2)")
        self.assertEqual(emitter.render_expr(list_ctor_expr), "xs")
        self.assertEqual(emitter.render_expr(set_ctor_expr), "set<int64>(xs)")
        self.assertEqual(emitter.render_expr(dict_ctor_expr), "d")
        self.assertEqual(
            emitter.render_expr(max_expr),
            "::std::max<int64>(static_cast<int64>(1), static_cast<int64>(2))",
        )
        self.assertEqual(
            emitter.render_expr(min_expr),
            "::std::min<int64>(static_cast<int64>(1), static_cast<int64>(2))",
        )
        self.assertEqual(emitter.render_expr(perf_expr), "pytra::std::time::perf_counter()")
        self.assertEqual(emitter.render_expr(open_expr), 'open("a.txt", "rb")')
        self.assertEqual(emitter.render_expr(path_ctor_expr), 'Path("a.txt")')
        self.assertEqual(emitter.render_expr(runtime_error_expr), '::std::runtime_error("boom")')
        self.assertEqual(emitter.render_expr(int_to_bytes_expr), 'py_int_to_bytes(n, 4, "little")')
        self.assertEqual(emitter.render_expr(bytes_expr), "bytes{}")
        self.assertEqual(emitter.render_expr(bytearray_expr), "bytearray(b'\\x01\\x02')")

    def test_plain_builtin_call_requires_builtin_lowering(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        plain_print = {
            "kind": "Call",
            "resolved_type": "None",
            "func": {"kind": "Name", "id": "print", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}],
            "keywords": [],
        }
        plain_len = {
            "kind": "Call",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "len", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "object"}],
            "keywords": [],
        }
        plain_any = {
            "kind": "Call",
            "resolved_type": "bool",
            "func": {"kind": "Name", "id": "any", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "xs", "resolved_type": "object"}],
            "keywords": [],
        }
        plain_ord = {
            "kind": "Call",
            "resolved_type": "int64",
            "func": {"kind": "Name", "id": "ord", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": "A", "resolved_type": "str"}],
            "keywords": [],
        }
        plain_list = {
            "kind": "Call",
            "resolved_type": "list[int64]",
            "func": {"kind": "Name", "id": "list", "resolved_type": "unknown"},
            "args": [],
            "keywords": [],
        }
        plain_range = {
            "kind": "Call",
            "resolved_type": "range",
            "func": {"kind": "Name", "id": "range", "resolved_type": "unknown"},
            "args": [{"kind": "Constant", "value": 3, "resolved_type": "int64"}],
            "keywords": [],
        }
        plain_zip = {
            "kind": "Call",
            "resolved_type": "list[tuple[int64,int64]]",
            "func": {"kind": "Name", "id": "zip", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                {"kind": "Name", "id": "ys", "resolved_type": "list[int64]"},
            ],
            "keywords": [],
        }
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: print"):
            emitter.render_expr(plain_print)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: len"):
            emitter.render_expr(plain_len)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: any"):
            emitter.render_expr(plain_any)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: ord"):
            emitter.render_expr(plain_ord)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: list"):
            emitter.render_expr(plain_list)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: range"):
            emitter.render_expr(plain_range)
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: zip"):
            emitter.render_expr(plain_zip)

    def test_plain_builtin_method_call_requires_builtin_lowering(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        plain_append = {
            "kind": "Call",
            "resolved_type": "None",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
                "attr": "append",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}],
            "keywords": [],
        }
        plain_path_exists = {
            "kind": "Call",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "p", "resolved_type": "Path"},
                "attr": "exists",
                "resolved_type": "unknown",
            },
            "args": [],
            "keywords": [],
        }
        with self.assertRaisesRegex(
            ValueError,
            "builtin method call must be lowered_kind=BuiltinCall: list\\[int64\\].append",
        ):
            emitter.render_expr(plain_append)
        with self.assertRaisesRegex(
            ValueError,
            "builtin method call must be lowered_kind=BuiltinCall: Path.exists",
        ):
            emitter.render_expr(plain_path_exists)

    def test_plain_builtin_method_call_allows_self_hosted_parser_compat(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {"parser_backend": "self_hosted"}}, {})
        plain_endswith = {
            "kind": "Call",
            "resolved_type": "bool",
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "s", "resolved_type": "str"},
                "attr": "endswith",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Constant", "value": ".py", "resolved_type": "str"}],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(plain_endswith), 'py_endswith(s, ".py")')

    def test_plain_isinstance_call_uses_type_id_core_node_path(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        plain_isinstance = {
            "kind": "Call",
            "resolved_type": "bool",
            "func": {"kind": "Name", "id": "isinstance", "resolved_type": "unknown"},
            "args": [
                {"kind": "Name", "id": "x", "resolved_type": "object"},
                {"kind": "Name", "id": "int", "resolved_type": "unknown"},
            ],
            "keywords": [],
        }
        self.assertEqual(emitter.render_expr(plain_isinstance), "py_isinstance(x, PYTRA_TID_INT)")

    def test_call_fallback_rejects_parser_lowered_builtins(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        with self.assertRaisesRegex(ValueError, "builtin call must be lowered_kind=BuiltinCall: print"):
            emitter._render_call_fallback("print", ["1"])

    def test_call_fallback_rejects_parser_lowered_builtin_methods(self) -> None:
        emitter = CppEmitter({"kind": "Module", "body": [], "meta": {}}, {})
        emitter.declared_var_types["xs"] = "list[int64]"
        with self.assertRaisesRegex(
            ValueError,
            "builtin method call must be lowered_kind=BuiltinCall: list\\[int64\\].append",
        ):
            emitter._render_call_fallback("xs.append", ["1"])

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

        out_bool = emitter._build_any_boundary_expr_from_builtin_call("py_to_bool", [any_arg])
        out_len = emitter._build_any_boundary_expr_from_builtin_call("py_len", [any_arg])
        out_str = emitter._build_any_boundary_expr_from_builtin_call("py_to_string", [any_arg])
        out_iter = emitter._build_any_boundary_expr_from_builtin_call("py_iter_or_raise", [any_arg])
        out_next = emitter._build_any_boundary_expr_from_builtin_call("py_next_or_stop", [any_arg])

        self.assertEqual(out_bool.get("kind"), "ObjBool")
        self.assertEqual(out_len.get("kind"), "ObjLen")
        self.assertEqual(out_str.get("kind"), "ObjStr")
        self.assertIsNone(out_iter)
        self.assertIsNone(out_next)

        concrete_arg = {"kind": "Name", "id": "n", "resolved_type": "int64"}
        out_none = emitter._build_any_boundary_expr_from_builtin_call("py_to_bool", [concrete_arg])
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

    def test_load_east_rejects_stage2_for_py2cpp(self) -> None:
        payload = {"kind": "Module", "meta": {}, "body": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "in.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "supports only --east-stage 3"):
                load_east(p, east_stage="2")

    def test_load_east_stage3_normalizes_prelowered_forcore_dispatch_mode(self) -> None:
        payload = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
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
                    "body": [],
                    "orelse": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "in-stage3.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            out = load_east(p, east_stage="3", object_dispatch_mode="type_id")
        self.assertEqual(out.get("east_stage"), 3)
        self.assertEqual(out.get("meta", {}).get("dispatch_mode"), "type_id")
        body = out.get("body", [])
        self.assertEqual(body[0].get("kind"), "ForCore")
        self.assertEqual(body[0].get("iter_plan", {}).get("dispatch_mode"), "type_id")


if __name__ == "__main__":
    unittest.main()

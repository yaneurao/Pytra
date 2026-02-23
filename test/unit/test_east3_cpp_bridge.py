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

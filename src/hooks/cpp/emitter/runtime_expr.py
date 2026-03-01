from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import join_str_list


class CppRuntimeExprEmitter:
    """Runtime/path/type_id expression helpers extracted from CppEmitter."""

    def _render_expr_kind_path_runtime_op(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        owner_expr = self.render_expr(expr_d.get("owner"))
        owner_node = self.any_to_dict_or_empty(expr_d.get("owner"))
        owner_kind = self._node_kind_from_dict(owner_node)
        if owner_kind in {"BinOp", "BoolOp", "Compare", "IfExp"}:
            owner_expr = "(" + owner_expr + ")"
        op = self.any_dict_get_str(expr_d, "op", "")
        if op == "mkdir":
            parents_expr = "false"
            if self.any_dict_has(expr_d, "parents"):
                parents_expr = self.render_expr(expr_d.get("parents"))
            exist_ok_expr = "false"
            if self.any_dict_has(expr_d, "exist_ok"):
                exist_ok_expr = self.render_expr(expr_d.get("exist_ok"))
            return f"{owner_expr}.mkdir({parents_expr}, {exist_ok_expr})"
        if op == "exists":
            return f"{owner_expr}.exists()"
        if op == "write_text":
            value_expr = '""'
            if self.any_dict_has(expr_d, "value"):
                value_expr = self.render_expr(expr_d.get("value"))
            return f"{owner_expr}.write_text({value_expr})"
        if op == "read_text":
            return f"{owner_expr}.read_text()"
        if op == "parent":
            return f"{owner_expr}.parent()"
        if op == "name":
            return f"{owner_expr}.name()"
        if op == "stem":
            return f"{owner_expr}.stem()"
        if op == "identity":
            return owner_expr
        return ""

    def _render_expr_kind_runtime_special_op(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        op = self.any_dict_get_str(expr_d, "op", "")
        if op == "print":
            print_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    print_args.append(self.render_expr(arg_node))
            return f"py_print({join_str_list(', ', print_args)})"
        if op == "len":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_len({value_expr})"
        if op == "to_string":
            return self.render_to_string(expr_d.get("value"))
        if op == "int_base":
            int_base_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    int_base_args.append(self.render_expr(arg_node))
            if len(int_base_args) >= 2:
                return f"py_to_int64_base({int_base_args[0]}, py_to<int64>({int_base_args[1]}))"
            return ""
        if op == "static_cast":
            if not self.any_dict_has(expr_d, "value"):
                return ""
            target = self.any_dict_get_str(expr_d, "target", "")
            if target == "":
                target = self.any_dict_get_str(expr_d, "resolved_type", "")
            static_cast_expr = {"resolved_type": target}
            static_cast_rendered = self._render_builtin_static_cast_call(static_cast_expr, [expr_d.get("value")])
            if static_cast_rendered is not None:
                return str(static_cast_rendered)
            return ""
        if op == "iter_or_raise":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_iter_or_raise({value_expr})"
        if op == "next_or_stop":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_next_or_stop({value_expr})"
        if op == "reversed":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_reversed({value_expr})"
        if op == "enumerate":
            enumerate_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    enumerate_args.append(self.render_expr(arg_node))
            if len(enumerate_args) >= 2:
                return f"py_enumerate({enumerate_args[0]}, py_to<int64>({enumerate_args[1]}))"
            if len(enumerate_args) == 1:
                return f"py_enumerate({enumerate_args[0]})"
            return ""
        if op == "any":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_any({value_expr})"
        if op == "all":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_all({value_expr})"
        if op == "ord":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_ord({value_expr})"
        if op == "chr":
            value_expr = self.render_expr(expr_d.get("value"))
            return f"py_chr({value_expr})"
        if op == "range":
            range_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    range_args.append(self.render_expr(arg_node))
            range_kw: dict[str, str] = {}
            kw_names: list[str] = []
            if self.any_dict_has(expr_d, "kw_names"):
                kw_names = self.any_to_str_list(expr_d.get("kw_names"))
            kw_values: list[Any] = []
            if self.any_dict_has(expr_d, "kw_values"):
                kw_values = self.any_to_list(expr_d.get("kw_values"))
            i = 0
            while i < len(kw_values):
                if i < len(kw_names):
                    kw_name = kw_names[i]
                    if kw_name != "":
                        range_kw[kw_name] = self.render_expr(kw_values[i])
                i += 1
            range_rendered = self._render_range_name_call(range_args, range_kw)
            if range_rendered is not None:
                return str(range_rendered)
            return ""
        if op == "zip":
            zip_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    zip_args.append(self.render_expr(arg_node))
            if len(zip_args) >= 2:
                return f"zip({zip_args[0]}, {zip_args[1]})"
            return ""
        if op == "collection_ctor":
            ctor_name = self.any_dict_get_str(expr_d, "ctor_name", "")
            ctor_args: list[str] = []
            arg_nodes_raw: list[Any] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes_raw = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes_raw:
                    ctor_args.append(self.render_expr(arg_node))
            first_arg: Any = expr_d
            if len(arg_nodes_raw) > 0:
                first_arg = arg_nodes_raw[0]
            return self._render_collection_constructor_call(ctor_name, expr_d, ctor_args, first_arg) or ""
        if op == "minmax":
            mode = self.any_dict_get_str(expr_d, "mode", "min")
            fn_name = "max" if mode == "max" else "min"
            rendered_args: list[str] = []
            arg_nodes_for_minmax: list[Any] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes_for_minmax = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes_for_minmax:
                    rendered_args.append(self.render_expr(arg_node))
            out_t = self.any_dict_get_str(expr_d, "resolved_type", "")
            return self.render_minmax(fn_name, rendered_args, out_t, arg_nodes_for_minmax)
        if op == "perf_counter":
            return "pytra::std::time::perf_counter()"
        if op == "open":
            open_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    open_args.append(self.render_expr(arg_node))
            return f"open({join_str_list(', ', open_args)})"
        if op == "path_ctor":
            path_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    path_args.append(self.render_expr(arg_node))
            return f"Path({join_str_list(', ', path_args)})"
        if op == "runtime_error":
            if self.any_dict_has(expr_d, "message"):
                message_expr = self.render_expr(expr_d.get("message"))
                return f"::std::runtime_error({message_expr})"
            return '::std::runtime_error("error")'
        if op == "int_to_bytes":
            owner_expr = self.render_expr(expr_d.get("owner"))
            length_expr = "0"
            if self.any_dict_has(expr_d, "length"):
                length_expr = self.render_expr(expr_d.get("length"))
            byteorder_expr = '"little"'
            if self.any_dict_has(expr_d, "byteorder"):
                byteorder_expr = self.render_expr(expr_d.get("byteorder"))
            return f"py_int_to_bytes({owner_expr}, {length_expr}, {byteorder_expr})"
        if op == "bytes_ctor":
            bytes_args: list[str] = []
            arg_nodes: list[Any] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    bytes_args.append(self.render_expr(arg_node))
            if len(bytes_args) == 0:
                return "bytes{}"
            if len(bytes_args) == 1 and len(arg_nodes) == 1:
                src_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0]))
                if src_t in {"bytes", "bytearray"}:
                    return bytes_args[0]
            return f"bytes({join_str_list(', ', bytes_args)})"
        if op == "bytearray_ctor":
            bytearray_args: list[str] = []
            if self.any_dict_has(expr_d, "args"):
                arg_nodes = self.any_to_list(expr_d.get("args"))
                for arg_node in arg_nodes:
                    bytearray_args.append(self.render_expr(arg_node))
            if len(bytearray_args) == 0:
                return "bytearray{}"
            return f"bytearray({join_str_list(', ', bytearray_args)})"
        return ""

    def _render_expr_kind_is_subtype(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        actual_type_id_expr = self.render_expr(expr_d.get("actual_type_id"))
        expected_type_id_expr = self.render_expr(expr_d.get("expected_type_id"))
        if actual_type_id_expr == "" or expected_type_id_expr == "":
            return "false"
        return f"py_is_subtype({actual_type_id_expr}, {expected_type_id_expr})"

    def _render_expr_kind_is_subclass(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        actual_type_id_expr = self._render_type_id_operand_expr(expr_d.get("actual_type_id"))
        expected_type_id_expr = self._render_type_id_operand_expr(expr_d.get("expected_type_id"))
        if actual_type_id_expr == "" or expected_type_id_expr == "":
            return "false"
        return f"py_issubclass({actual_type_id_expr}, {expected_type_id_expr})"

    def _render_expr_kind_is_instance(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        value_expr = self.render_expr(expr_d.get("value"))
        expected_type_id_expr = self._render_type_id_operand_expr(expr_d.get("expected_type_id"))
        if expected_type_id_expr == "":
            return "false"
        return f"py_isinstance({value_expr}, {expected_type_id_expr})"

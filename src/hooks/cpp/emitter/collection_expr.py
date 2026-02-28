from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import join_str_list


class CppCollectionExprEmitter:
    """Collection literal/comprehension render helpers extracted from CppEmitter."""

    def _render_expr_kind_list(self, expr: Any, expr_d: dict[str, Any]) -> str:
        t = self.cpp_type(expr_d.get("resolved_type"))
        list_model = self.any_to_str(getattr(self, "cpp_list_model", "value"))
        pyobj_list_mode = list_model == "pyobj"
        elem_t = ""
        rt0 = self.get_expr_type(expr)
        rt = rt0 if isinstance(rt0, str) else ""
        rt_norm = self.normalize_type_name(rt)
        if rt_norm in {"", "unknown"}:
            rt_norm = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
        if rt_norm.startswith("list[") and rt_norm.endswith("]"):
            elem_t = rt_norm[5:-1].strip()
        pyobj_runtime_list_mode = pyobj_list_mode and (
            rt_norm in {"", "unknown", "Any", "object"} or self._is_pyobj_runtime_list_type(rt_norm)
        )
        parts: list[str] = []
        ctor_elem = ""
        ctor_mixed = False
        elements = self.any_to_list(expr_d.get("elements"))
        for e in elements:
            rv = self.render_expr(e)
            brace_pos = rv.find("{")
            if brace_pos > 0:
                cand = rv[:brace_pos].strip()
                if cand.startswith("dict<") or cand.startswith("list<") or cand.startswith("set<"):
                    first_ctor_elem = ctor_elem == ""
                    ctor_elem = cand if first_ctor_elem else ctor_elem
                    if not first_ctor_elem and ctor_elem != cand:
                        ctor_mixed = True
            if self.is_any_like_type(elem_t):
                rv = self._box_expr_for_any(rv, e)
            parts.append(rv)
        if t.startswith("list<") and ctor_elem != "" and not ctor_mixed:
            expect_t = f"list<{ctor_elem}>"
            if t != expect_t:
                t = expect_t
        sep = ", "
        items = sep.join(parts)
        if pyobj_runtime_list_mode:
            value_list_t = "list<object>"
            if ctor_elem != "" and not ctor_mixed:
                value_list_t = f"list<{ctor_elem}>"
            elif elem_t not in {"", "unknown", "None"} and not self.is_any_like_type(elem_t):
                value_list_t = f"list<{self._cpp_type_text(elem_t)}>"
            if value_list_t == "list<object>":
                boxed_parts: list[str] = []
                for i, e in enumerate(elements):
                    rv = parts[i] if i < len(parts) else ""
                    boxed_parts.append(self._box_expr_for_any(rv, e))
                items = sep.join(boxed_parts)
            return f"make_object({value_list_t}{{{items}}})"
        return f"{t}{{{items}}}"

    def _render_expr_kind_tuple(self, expr: Any, expr_d: dict[str, Any]) -> str:
        elements = self.any_to_list(expr_d.get("elements"))
        elem_types: list[str] = []
        rt0 = self.get_expr_type(expr)
        rt = rt0 if isinstance(rt0, str) else ""
        if rt.startswith("tuple[") and rt.endswith("]"):
            elem_types = self.split_generic(rt[6:-1])
        rendered_items: list[str] = []
        for i, e in enumerate(elements):
            item = self.render_expr(e)
            target_t = elem_types[i] if i < len(elem_types) else ""
            src_t0 = self.get_expr_type(e)
            src_t = src_t0 if isinstance(src_t0, str) else ""
            if target_t != "" and not self.is_any_like_type(target_t) and src_t != target_t:
                item = self.apply_cast(item, target_t)
            rendered_items.append(item)
        sep = ", "
        items = sep.join(rendered_items)
        return f"::std::make_tuple({items})"

    def _render_expr_kind_set(self, expr: Any, expr_d: dict[str, Any]) -> str:
        _ = expr
        t = self.cpp_type(expr_d.get("resolved_type"))
        elements = self.any_to_list(expr_d.get("elements"))
        rendered: list[str] = []
        for e in elements:
            rendered.append(self.render_expr(e))
        sep = ", "
        items = sep.join(rendered)
        return f"{t}{{{items}}}"

    def _render_expr_kind_dict(self, expr: Any, expr_d: dict[str, Any]) -> str:
        t = self.cpp_type(expr_d.get("resolved_type"))
        key_t = ""
        val_t = ""
        rt = self.get_expr_type(expr)
        if isinstance(rt, str) and rt.startswith("dict[") and rt.endswith("]"):
            inner = self.split_generic(rt[5:-1])
            if len(inner) == 2:
                key_t = inner[0]
                val_t = inner[1]
        entries = self._dict_stmt_list(expr_d.get("entries"))
        if len(entries) == 0:
            keys_raw = self.any_to_list(expr_d.get("keys"))
            vals_raw = self.any_to_list(expr_d.get("values"))
            n = len(keys_raw)
            if len(vals_raw) < n:
                n = len(vals_raw)
            for i in range(n):
                entries.append({"key": keys_raw[i], "value": vals_raw[i]})
        if len(entries) == 0:
            return f"{t}{{}}"
        inferred_key = ""
        inferred_val = ""
        key_mixed = False
        val_mixed = False
        for kv in entries:
            key_node: Any = kv.get("key")
            val_node: Any = kv.get("value")
            kt0 = self.get_expr_type(key_node)
            kt = kt0 if isinstance(kt0, str) else ""
            if kt not in {"", "unknown"}:
                first_inferred_key = inferred_key == ""
                inferred_key = kt if first_inferred_key else inferred_key
                if not first_inferred_key and kt != inferred_key:
                    key_mixed = True
            vt0 = self.get_expr_type(val_node)
            vt = vt0 if isinstance(vt0, str) else ""
            if vt not in {"", "unknown"}:
                first_inferred_val = inferred_val == ""
                inferred_val = vt if first_inferred_val else inferred_val
                if not first_inferred_val and vt != inferred_val:
                    val_mixed = True
        if key_t in {"", "unknown"} and inferred_key != "" and not key_mixed:
            key_t = inferred_key
        if val_t in {"", "unknown"} and inferred_val != "" and not val_mixed:
            val_t = inferred_val
        if val_mixed:
            key_pick = key_t if key_t not in {"", "unknown"} and not key_mixed else "str"
            if key_pick == "str" and inferred_key != "" and not key_mixed:
                key_pick = inferred_key
            t = f"dict<{self._cpp_type_text(key_pick)}, object>"
            val_t = "Any"
        elif t in {"auto", "dict<str, str>", "dict<str, object>"}:
            key_pick = key_t if key_t not in {"", "unknown"} and not key_mixed else "str"
            default_val_pick = "Any" if t == "dict<str, object>" else "str"
            val_pick = (
                val_t
                if val_t not in {"", "unknown"}
                else (inferred_val if inferred_val != "" else default_val_pick)
            )
            val_is_any_like = self.is_any_like_type(val_pick)
            t = (
                f"dict<{self._cpp_type_text(key_pick)}, object>"
                if val_is_any_like
                else f"dict<{self._cpp_type_text(key_pick)}, {self._cpp_type_text(val_pick)}>"
            )
            val_t = "Any" if val_is_any_like else val_t
        items: list[str] = []
        for kv in entries:
            key_node = kv.get("key")
            val_node = kv.get("value")
            k = self.render_expr(key_node)
            v = self.render_expr(val_node)
            if self.is_any_like_type(key_t):
                k = self._box_expr_for_any(k, key_node)
            if self.is_any_like_type(val_t):
                v = self._box_expr_for_any(v, val_node)
            items.append(f"{{{k}, {v}}}")
        return f"{t}{{{join_str_list(', ', items)}}}"

    def _render_expr_kind_list_comp(self, expr: Any, expr_d: dict[str, Any]) -> str:
        gens = self.any_to_list(expr_d.get("generators"))
        if len(gens) != 1:
            return "{}"
        list_model = self.any_to_str(getattr(self, "cpp_list_model", "value"))
        pyobj_list_mode = list_model == "pyobj"
        g_obj = gens[0]
        g = self.any_to_dict_or_empty(g_obj)
        g_target_raw: object = g.get("target")
        g_target = self.any_to_dict_or_empty(g_target_raw)
        tgt = self.render_expr(g_target_raw)
        it = self.render_expr(g.get("iter"))
        elt = self.render_expr(expr_d.get("elt"))
        out_t = self.cpp_type(expr_d.get("resolved_type"))
        out_east_t0 = self.get_expr_type(expr)
        out_east_t = self.normalize_type_name(out_east_t0 if isinstance(out_east_t0, str) else "")
        if out_east_t in {"", "unknown"}:
            out_east_t = self.normalize_type_name(self.any_to_str(expr_d.get("resolved_type")))
        pyobj_runtime_list_mode = pyobj_list_mode and (
            out_east_t in {"", "unknown", "Any", "object"} or self._is_pyobj_runtime_list_type(out_east_t)
        )
        elt_t0 = self.get_expr_type(expr_d.get("elt"))
        elt_t = elt_t0 if isinstance(elt_t0, str) else ""
        expected_out_t = ""
        if elt_t != "" and elt_t != "unknown":
            expected_out_t = self._cpp_type_text(f"list[{elt_t}]")
        out_is_dynamic = out_t == "list<object>" or out_t == "object" or out_t == "auto"
        if out_is_dynamic:
            if elt_t != "" and elt_t != "unknown":
                out_t = self._cpp_type_text(f"list[{elt_t}]")
        elif expected_out_t != "" and out_t != expected_out_t:
            out_t = expected_out_t
        brace_pos = elt.find("{")
        if brace_pos > 0:
            elt_ctor = elt[:brace_pos].strip()
            if elt_ctor.startswith("dict<") or elt_ctor.startswith("list<") or elt_ctor.startswith("set<"):
                out_t = f"list<{elt_ctor}>"
        emit_out_t = out_t
        lambda_ret_t = out_t
        if pyobj_runtime_list_mode:
            lambda_ret_t = "object"
            if not (emit_out_t.startswith("list<") and emit_out_t.endswith(">")):
                if elt_t not in {"", "unknown"}:
                    emit_out_t = self._cpp_type_text(f"list[{elt_t}]")
                if not (emit_out_t.startswith("list<") and emit_out_t.endswith(">")):
                    emit_out_t = "list<object>"
        lines = [f"[&]() -> {lambda_ret_t} {{", f"    {emit_out_t} __out;"]
        tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
        iter_tmp = self.next_for_iter_name()
        rg = self.any_to_dict_or_empty(g.get("iter"))
        if self._node_kind_from_dict(rg) == "RangeExpr":
            start = self.render_expr(rg.get("start"))
            stop = self.render_expr(rg.get("stop"))
            step = self.render_expr(rg.get("step"))
            mode = self.any_to_str(rg.get("range_mode"))
            mode = mode if mode != "" else "dynamic"
            cond = (
                f"({tgt} < {stop})"
                if mode == "ascending"
                else (
                    f"({tgt} > {stop})"
                    if mode == "descending"
                    else f"(({step}) > 0 ? ({tgt} < {stop}) : ({tgt} > {stop}))"
                )
            )
            lines.append(f"    for (int64 {tgt} = {start}; {cond}; {tgt} += ({step})) {{")
        else:
            if tuple_unpack:
                lines.append(f"    for (auto {iter_tmp} : {it}) {{")
                target_elements = self.any_to_list(g_target.get("elements"))
                for i, e in enumerate(target_elements):
                    e_node = self.any_to_dict_or_empty(e)
                    if self._node_kind_from_dict(e_node) == "Name":
                        nm = self.render_expr(e)
                        lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
            else:
                lines.append(f"    for (auto {tgt} : {it}) {{")
        ifs = self.any_to_list(g.get("ifs"))
        list_elt = elt
        out_elem_t = ""
        if out_east_t.startswith("list[") and out_east_t.endswith("]"):
            out_parts = self.split_generic(out_east_t[5:-1])
            if len(out_parts) == 1:
                out_elem_t = self.normalize_type_name(out_parts[0])
        if (out_elem_t == "" or self.is_any_like_type(out_elem_t)) and emit_out_t.startswith("list<") and emit_out_t.endswith(">"):
            cpp_inner = self._trim_ws(emit_out_t[5:-1])
            if cpp_inner in {
                "float32",
                "float64",
                "double",
                "int8",
                "uint8",
                "int16",
                "uint16",
                "int32",
                "uint32",
                "int64",
                "uint64",
                "bool",
                "str",
            }:
                out_elem_t = "float64" if cpp_inner == "double" else cpp_inner
        if out_elem_t != "" and not self.is_any_like_type(out_elem_t):
            list_elt_trim = self._trim_ws(list_elt)
            if self.is_boxed_object_expr(list_elt_trim):
                list_elt = self._render_unbox_target_cast(list_elt_trim, out_elem_t, "listcomp:elt")
            elif self.is_any_like_type(elt_t):
                list_elt = self._coerce_any_expr_to_target_via_unbox(
                    list_elt,
                    expr_d.get("elt"),
                    out_elem_t,
                    "listcomp:elt",
                )
        if emit_out_t == "list<object>" and not self.is_boxed_object_expr(list_elt):
            list_elt = self._box_any_target_value(list_elt, expr_d.get("elt"))
        if len(ifs) == 0:
            lines.append(f"        __out.append({list_elt});")
        else:
            cond_parts: list[str] = []
            for c in ifs:
                c_txt = self.render_expr(c)
                if c_txt in {"", "true"}:
                    c_node = self.any_to_dict_or_empty(c)
                    c_rep = self.any_dict_get_str(c_node, "repr", "")
                    if c_rep != "":
                        c_txt = c_rep
                cond_parts.append(c_txt if c_txt != "" else "true")
            cond: str = join_str_list(" && ", cond_parts)
            lines.append(f"        if ({cond}) __out.append({list_elt});")
        lines.append("    }")
        if pyobj_runtime_list_mode:
            lines.append("    return make_object(__out);")
        else:
            lines.append("    return __out;")
        lines.append("}()")
        sep = " "
        return sep.join(lines)

    def _render_expr_kind_set_comp(self, expr: Any, expr_d: dict[str, Any]) -> str:
        gens = self.any_to_list(expr_d.get("generators"))
        if len(gens) != 1:
            return "{}"
        g_obj = gens[0]
        g = self.any_to_dict_or_empty(g_obj)
        g_target_raw: object = g.get("target")
        g_target = self.any_to_dict_or_empty(g_target_raw)
        tgt = self.render_expr(g_target_raw)
        it = self.render_expr(g.get("iter"))
        elt = self.render_expr(expr_d.get("elt"))
        out_t = self.cpp_type(expr_d.get("resolved_type"))
        elt_t0 = self.get_expr_type(expr_d.get("elt"))
        elt_t = elt_t0 if isinstance(elt_t0, str) else ""
        expected_out_t = ""
        if elt_t != "" and elt_t != "unknown":
            expected_out_t = self._cpp_type_text(f"set[{elt_t}]")
        out_is_dynamic = out_t == "set<object>" or out_t == "object" or out_t == "auto"
        if out_is_dynamic:
            if elt_t != "" and elt_t != "unknown":
                out_t = self._cpp_type_text(f"set[{elt_t}]")
        elif expected_out_t != "" and out_t != expected_out_t:
            out_t = expected_out_t
        lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
        tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
        iter_tmp = self.next_for_iter_name()
        if tuple_unpack:
            lines.append(f"    for (auto {iter_tmp} : {it}) {{")
            target_elements = self.any_to_list(g_target.get("elements"))
            for i, e in enumerate(target_elements):
                e_node = self.any_to_dict_or_empty(e)
                if self._node_kind_from_dict(e_node) == "Name":
                    nm = self.render_expr(e)
                    lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
        else:
            lines.append(f"    for (auto {tgt} : {it}) {{")
        ifs = self.any_to_list(g.get("ifs"))
        set_elt = elt
        if out_t == "set<object>" and not self.is_boxed_object_expr(set_elt):
            set_elt = self._box_any_target_value(set_elt, expr_d.get("elt"))
        if len(ifs) == 0:
            lines.append(f"        __out.insert({set_elt});")
        else:
            cond_parts: list[str] = []
            for c in ifs:
                c_txt = self.render_expr(c)
                if c_txt in {"", "true"}:
                    c_node = self.any_to_dict_or_empty(c)
                    c_rep = self.any_dict_get_str(c_node, "repr", "")
                    if c_rep != "":
                        c_txt = c_rep
                cond_parts.append(c_txt if c_txt != "" else "true")
            cond: str = join_str_list(" && ", cond_parts)
            lines.append(f"        if ({cond}) __out.insert({set_elt});")
        lines.append("    }")
        lines.append("    return __out;")
        lines.append("}()")
        sep = " "
        return sep.join(lines)

    def _render_expr_kind_dict_comp(self, expr: Any, expr_d: dict[str, Any]) -> str:
        gens = self.any_to_list(expr_d.get("generators"))
        if len(gens) != 1:
            return "{}"
        g_obj = gens[0]
        g = self.any_to_dict_or_empty(g_obj)
        g_target_raw: object = g.get("target")
        g_target = self.any_to_dict_or_empty(g_target_raw)
        tgt = self.render_expr(g_target_raw)
        it = self.render_expr(g.get("iter"))
        key = self.render_expr(expr_d.get("key"))
        val = self.render_expr(expr_d.get("value"))
        out_t = self.cpp_type(expr_d.get("resolved_type"))
        key_t0 = self.get_expr_type(expr_d.get("key"))
        val_t0 = self.get_expr_type(expr_d.get("value"))
        key_t = key_t0 if isinstance(key_t0, str) else ""
        val_t = val_t0 if isinstance(val_t0, str) else ""
        expected_out_t = ""
        if key_t != "" and key_t != "unknown" and val_t != "" and val_t != "unknown":
            expected_out_t = self._cpp_type_text(f"dict[{key_t},{val_t}]")
        out_is_dynamic = out_t == "dict<str, object>" or out_t == "object" or out_t == "auto"
        if out_is_dynamic:
            if key_t != "" and key_t != "unknown" and val_t != "" and val_t != "unknown":
                out_t = self._cpp_type_text(f"dict[{key_t},{val_t}]")
        elif expected_out_t != "" and out_t != expected_out_t:
            out_t = expected_out_t
        lines = [f"[&]() -> {out_t} {{", f"    {out_t} __out;"]
        tuple_unpack = self._node_kind_from_dict(g_target) == "Tuple"
        iter_tmp = self.next_for_iter_name()
        if tuple_unpack:
            lines.append(f"    for (auto {iter_tmp} : {it}) {{")
            target_elements = self.any_to_list(g_target.get("elements"))
            for i, e in enumerate(target_elements):
                e_node = self.any_to_dict_or_empty(e)
                if self._node_kind_from_dict(e_node) == "Name":
                    nm = self.render_expr(e)
                    lines.append(f"        auto {nm} = ::std::get<{i}>({iter_tmp});")
        else:
            lines.append(f"    for (auto {tgt} : {it}) {{")
        ifs = self.any_to_list(g.get("ifs"))
        if len(ifs) == 0:
            lines.append(f"        __out[{key}] = {val};")
        else:
            cond_parts: list[str] = []
            for c in ifs:
                c_txt = self.render_expr(c)
                if c_txt in {"", "true"}:
                    c_node = self.any_to_dict_or_empty(c)
                    c_rep = self.any_dict_get_str(c_node, "repr", "")
                    if c_rep != "":
                        c_txt = c_rep
                cond_parts.append(c_txt if c_txt != "" else "true")
            cond: str = join_str_list(" && ", cond_parts)
            lines.append(f"        if ({cond}) __out[{key}] = {val};")
        lines.append("    }")
        lines.append("    return __out;")
        lines.append("}()")
        sep = " "
        return sep.join(lines)

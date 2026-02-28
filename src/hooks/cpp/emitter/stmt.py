from __future__ import annotations

from pytra.std.typing import Any
from hooks.cpp.profile import AUG_BIN, AUG_OPS, load_cpp_profile


class CppStatementEmitter:
    """Statement-level emit helpers extracted from :class:`CppEmitter`."""

    def _emit_if_stmt(self, stmt: dict[str, Any]) -> None:
        """If ノードを出力する。"""
        cond_txt, body_stmts, else_stmts = self.prepare_if_stmt_parts(
            stmt,
            cond_empty_default="false",
        )
        self._predeclare_if_join_names(body_stmts, else_stmts)
        omit_default = self._default_stmt_omit_braces("If", stmt, False)
        omit_braces = self.hook_on_stmt_omit_braces("If", stmt, omit_default)
        if omit_braces and len(body_stmts) == 1 and len(else_stmts) <= 1:
            self.emit(self.syntax_line("if_no_brace", "if ({cond})", {"cond": cond_txt}))
            self.emit_scoped_stmt_list([body_stmts[0]], set())
            if len(else_stmts) > 0:
                self.emit(self.syntax_text("else_no_brace", "else"))
                self.emit_scoped_stmt_list([else_stmts[0]], set())
            return

        self.emit_if_stmt_skeleton(
            cond_txt,
            body_stmts,
            else_stmts,
            if_open_default="if ({cond}) {",
            else_open_default="} else {",
        )

    def _emit_while_stmt(self, stmt: dict[str, Any]) -> None:
        """While ノードを出力する。"""
        cond_txt, body_stmts = self.prepare_while_stmt_parts(
            stmt,
            cond_empty_default="false",
        )
        self.emit_while_stmt_skeleton(
            cond_txt,
            body_stmts,
            while_open_default="while ({cond}) {",
        )

    def _render_lvalue_for_augassign(self, target_expr: Any) -> str:
        """AugAssign 向けに左辺を簡易レンダリングする。"""
        target_node = self.any_to_dict_or_empty(target_expr)
        if self._node_kind_from_dict(target_node) == "Name":
            return self.any_dict_get_str(target_node, "id", "_")
        return self.render_lvalue(target_expr)

    def _emit_annassign_stmt(self, stmt: dict[str, Any]) -> None:
        """AnnAssign ノードを出力する。"""
        t = self.cpp_type(stmt.get("annotation"))
        decl_hint = self.any_dict_get_str(stmt, "decl_type", "")
        decl_hint_fallback = str(stmt.get("decl_type"))
        ann_text_fallback = str(stmt.get("annotation"))
        if decl_hint == "" and decl_hint_fallback not in {"", "{}", "None"}:
            decl_hint = decl_hint_fallback
        if decl_hint != "":
            t = self._cpp_type_text(decl_hint)
        elif t == "auto":
            t = self.cpp_type(stmt.get("decl_type"))
            if t == "auto" and ann_text_fallback not in {"", "{}", "None"}:
                t = self._cpp_type_text(self.normalize_type_name(ann_text_fallback))
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self.render_expr(stmt.get("target"))
        val = self.any_to_dict_or_empty(stmt.get("value"))
        val_is_dict: bool = len(val) > 0
        rendered_val: str = ""
        if val_is_dict:
            rendered_val = self.render_expr(stmt.get("value"))
        ann_t_str = self.any_dict_get_str(stmt, "annotation", "")
        ann_fallback = ann_text_fallback if ann_text_fallback not in {"", "{}", "None"} else ""
        ann_t_str = ann_t_str if ann_t_str != "" else (decl_hint if decl_hint != "" else ann_fallback)
        if rendered_val != "" and ann_t_str != "":
            rendered_val = self._rewrite_nullopt_default_for_typed_target(rendered_val, ann_t_str)
        if ann_t_str in {"byte", "uint8"} and val_is_dict:
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rendered_val = str(byte_val)
        val_kind = self.any_dict_get_str(val, "kind", "")
        if val_is_dict and val_kind == "Dict" and ann_t_str.startswith("dict[") and ann_t_str.endswith("]"):
            inner_ann = self.split_generic(ann_t_str[5:-1])
            if len(inner_ann) == 2 and self.is_any_like_type(inner_ann[1]):
                items: list[str] = []
                for kv in self._dict_stmt_list(val.get("entries")):
                    k = self.render_expr(kv.get("key"))
                    v = self.render_expr_as_any(kv.get("value"))
                    items.append(f"{{{k}, {v}}}")
                rendered_val = f"{t}{{{', '.join(items)}}}"
        if val_is_dict and t != "auto":
            vkind = val_kind
            if vkind == "BoolOp":
                if ann_t_str != "bool":
                    rendered_val = self.render_boolop(stmt.get("value"), True)
            if vkind == "List" and len(self._dict_stmt_list(val.get("elements"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "Dict" and len(self._dict_stmt_list(val.get("entries"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "Set" and len(self._dict_stmt_list(val.get("elements"))) == 0:
                rendered_val = f"{t}{{}}"
            elif vkind == "ListComp" and isinstance(rendered_val, str):
                rendered_trim = self._trim_ws(rendered_val)
                if rendered_trim.startswith("[&]() -> list<object> {"):
                    rendered_val = rendered_val.replace("[&]() -> list<object> {", f"[&]() -> {t} {{", 1)
                    rendered_val = rendered_val.replace("list<object> __out;", f"{t} __out;", 1)
        val_t0 = self.get_expr_type(stmt.get("value"))
        val_t = val_t0 if isinstance(val_t0, str) else ""
        if rendered_val != "" and ann_t_str != "" and self._contains_text(val_t, "|"):
            union_parts = self.split_union(val_t)
            has_none = False
            non_none_norm: list[str] = []
            for p in union_parts:
                pn = self.normalize_type_name(p)
                if pn == "None":
                    has_none = True
                    continue
                if pn != "":
                    non_none_norm.append(pn)
            ann_norm = self.normalize_type_name(ann_t_str)
            if has_none and len(non_none_norm) == 1 and non_none_norm[0] == ann_norm:
                rendered_val = f"({rendered_val}).value()"
        if self._can_runtime_cast_target(ann_t_str) and self.is_any_like_type(val_t) and rendered_val != "":
            rendered_val = self._coerce_any_expr_to_target_via_unbox(
                rendered_val,
                stmt.get("value"),
                ann_t_str,
                f"annassign:{target}",
            )
        if self.is_any_like_type(ann_t_str) and val_is_dict:
            rendered_val = self._box_any_target_value(rendered_val, stmt.get("value"))
        is_plain_name_target = self._node_kind_from_dict(target_node) == "Name"
        declare_stmt = self.stmt_declare_flag(stmt, True)
        declare_name_binding = is_plain_name_target and self.should_declare_name_binding(stmt, target, True)
        already_declared = is_plain_name_target and self.is_declared_for_name_binding(target)
        if target.startswith("this->"):
            if not val_is_dict:
                self.emit(f"{target};")
            else:
                self.emit(f"{target} = {rendered_val};")
            return
        if not val_is_dict:
            if declare_name_binding:
                self.declare_in_current_scope(target)
            if declare_stmt and not already_declared:
                self.emit(f"{t} {target};")
            return
        if declare_name_binding:
            self.declare_in_current_scope(target)
            picked_decl_t = ann_t_str if ann_t_str != "" else decl_hint
            picked_decl_t = (
                picked_decl_t if picked_decl_t != "" else (val_t if val_t != "" else self.get_expr_type(target_node))
            )
            self.declared_var_types[target] = self.normalize_type_name(picked_decl_t)
        if declare_stmt and not already_declared:
            self.emit(f"{t} {target} = {rendered_val};")
        else:
            self.emit(f"{target} = {rendered_val};")

    def _emit_augassign_stmt(self, stmt: dict[str, Any]) -> None:
        """AugAssign ノードを出力する。"""
        op = "+="
        target_expr_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self._render_lvalue_for_augassign(stmt.get("target"))
        declare_name_binding = self._node_kind_from_dict(target_expr_node) == "Name" and self.should_declare_name_binding(
            stmt,
            target,
            False,
        )
        if declare_name_binding:
            decl_t_raw = stmt.get("decl_type")
            decl_t = str(decl_t_raw) if isinstance(decl_t_raw, str) else ""
            inferred_t = self.get_expr_type(stmt.get("target"))
            picked_t = decl_t if decl_t != "" else inferred_t
            t = self._cpp_type_text(picked_t)
            self.declare_in_current_scope(target)
            self.emit(f"{t} {target} = {self.render_expr(stmt.get('value'))};")
            return
        val = self.render_expr(stmt.get("value"))
        target_t = self.get_expr_type(stmt.get("target"))
        value_t = self.get_expr_type(stmt.get("value"))
        if self.is_any_like_type(value_t):
            if target_t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
                val = f"py_to<int64>({val})"
            elif target_t in {"float32", "float64"}:
                val = f"static_cast<float64>(py_to<int64>({val}))"
        op_name = str(stmt.get("op"))
        op_txt = str(AUG_OPS.get(op_name, ""))
        if op_txt != "":
            op = op_txt
        if str(AUG_BIN.get(op_name, "")) != "":
            # Prefer idiomatic ++/-- for +/-1 updates.
            if self._opt_ge(2) and op_name in {"Add", "Sub"} and val == "1":
                if op_name == "Add":
                    self.emit(f"{target}++;")
                else:
                    self.emit(f"{target}--;")
                return
            if op_name == "FloorDiv":
                if self.floor_div_mode == "python":
                    self.emit(f"{target} = py_floordiv({target}, {val});")
                else:
                    self.emit(f"{target} /= {val};")
            elif op_name == "Mod":
                if self.mod_mode == "python":
                    self.emit(f"{target} = py_mod({target}, {val});")
                else:
                    self.emit(f"{target} {op} {val};")
            else:
                self.emit(f"{target} {op} {val};")
            return
        self.emit(f"{target} {op} {val};")

    def emit_assign(self, stmt: dict[str, Any]) -> None:
        """代入文（通常代入/タプル代入）を C++ へ出力する。"""
        target = self.primary_assign_target(stmt)
        value = self.any_to_dict_or_empty(stmt.get("value"))
        if len(target) == 0 or len(value) == 0:
            self.emit("/* invalid assign */")
            return
        # `X = imported.Y` / `X = imported` の純再エクスポートは
        # C++ 側では宣言変数に落とすと未使用・型退化の温床になるため省略する。
        if self._is_reexport_assign(target, value):
            return
        if self._node_kind_from_dict(target) == "Tuple":
            lhs_elems = self.any_dict_get_list(target, "elements")
            if len(lhs_elems) == 0:
                fallback_names = self.fallback_tuple_target_names_from_stmt(target, stmt)
                if len(fallback_names) > 0:
                    recovered: list[Any] = []
                    for nm in fallback_names:
                        rec: dict[str, Any] = {
                            "kind": "Name",
                            "id": nm,
                            "resolved_type": "unknown",
                            "repr": nm,
                        }
                        rec_any: Any = rec
                        recovered.append(rec_any)
                    lhs_elems = recovered
            if self._opt_ge(2) and isinstance(value, dict) and self._node_kind_from_dict(value) == "Tuple":
                rhs_elems = self.any_dict_get_list(value, "elements")
                if (
                    len(lhs_elems) == 2
                    and len(rhs_elems) == 2
                    and self._expr_repr_eq(lhs_elems[0], rhs_elems[1])
                    and self._expr_repr_eq(lhs_elems[1], rhs_elems[0])
                ):
                    self.emit(f"::std::swap({self.render_lvalue(lhs_elems[0])}, {self.render_lvalue(lhs_elems[1])});")
                    return
            tmp = self.next_tuple_tmp_name()
            value_expr = self.render_expr(stmt.get("value"))
            tuple_elem_types: list[str] = []
            value_t = self.get_expr_type(stmt.get("value"))
            value_is_optional_tuple = False
            rhs_is_tuple = False
            if isinstance(value_t, str):
                tuple_type_text = ""
                if value_t.startswith("tuple[") and value_t.endswith("]"):
                    tuple_type_text = value_t
                elif self._contains_text(value_t, "|"):
                    for part in self.split_union(value_t):
                        if part.startswith("tuple[") and part.endswith("]"):
                            tuple_type_text = part
                            break
                if tuple_type_text != "":
                    rhs_is_tuple = True
                    tuple_elem_types = self.split_generic(tuple_type_text[6:-1])
                    if tuple_type_text != value_t:
                        value_is_optional_tuple = True
            if not rhs_is_tuple:
                value_node = self.any_to_dict_or_empty(stmt.get("value"))
                if self._node_kind_from_dict(value_node) == "Call":
                    fn_node = self.any_to_dict_or_empty(value_node.get("func"))
                    fn_name = ""
                    if self._node_kind_from_dict(fn_node) == "Name":
                        fn_name = self.any_to_str(fn_node.get("id"))
                    if fn_name != "":
                        fn_name = self.rename_if_reserved(fn_name, self.reserved_words, self.rename_prefix, self.renamed_symbols)
                        ret_t = self.function_return_types.get(fn_name, "")
                        if ret_t.startswith("tuple[") and ret_t.endswith("]"):
                            rhs_is_tuple = True
                            tuple_elem_types = self.split_generic(ret_t[6:-1])
            if value_is_optional_tuple:
                self.emit(f"auto {tmp} = *({value_expr});")
            else:
                self.emit(f"auto {tmp} = {value_expr};")
            for i, elt in enumerate(lhs_elems):
                lhs = self.render_expr(elt)
                rhs_item = f"::std::get<{i}>({tmp})" if rhs_is_tuple else f"py_at({tmp}, {i})"
                if self.is_plain_name_expr(elt):
                    elt_dict = self.any_to_dict_or_empty(elt)
                    name = self.any_dict_get_str(elt_dict, "id", "")
                    if not self.is_declared_for_name_binding(name):
                        decl_t_txt = tuple_elem_types[i] if i < len(tuple_elem_types) else self.get_expr_type(elt)
                        self.declare_in_current_scope(name)
                        self.declared_var_types[name] = decl_t_txt
                        if decl_t_txt in {"", "unknown", "Any", "object"}:
                            self.emit(f"auto {lhs} = {rhs_item};")
                            continue
                        decl_t = self._cpp_type_text(decl_t_txt)
                        self.emit(f"{decl_t} {lhs} = {rhs_item};")
                        continue
                self.emit(f"{lhs} = {rhs_item};")
            return
        target_obj: Any = target
        texpr = self.render_lvalue(target_obj)
        if self.is_plain_name_expr(target_obj) and not self.is_declared_for_name_binding(texpr):
            d0 = self.normalize_type_name(self.any_dict_get_str(stmt, "decl_type", ""))
            d1 = self.normalize_type_name(self.get_expr_type(target_obj))
            d2 = self.normalize_type_name(self.get_expr_type(stmt.get("value")))
            if d0 == "unknown":
                d0 = ""
            if d1 == "unknown":
                d1 = ""
            if d2 == "unknown":
                d2 = ""
            picked = d0 if d0 != "" else (d1 if d1 != "" else d2)
            if picked == "None":
                picked = "Any"
            if picked in {"", "unknown", "Any", "object"} and isinstance(value, dict):
                numeric_picked = self._infer_numeric_expr_type(value)
                if numeric_picked != "":
                    picked = numeric_picked
            dtype = self._cpp_type_text(picked)
            self.declare_in_current_scope(texpr)
            self.declared_var_types[texpr] = picked
            rval = self.render_expr(stmt.get("value"))
            rval = self._rewrite_nullopt_default_for_typed_target(rval, picked)
            rval_trim = self._trim_ws(rval)
            if dtype.startswith("list<") and rval_trim.startswith("[&]() -> list<object> {"):
                rval = rval.replace("[&]() -> list<object> {", f"[&]() -> {dtype} {{", 1)
                rval = rval.replace("list<object> __out;", f"{dtype} __out;", 1)
            if dtype == "uint8" and isinstance(value, dict):
                byte_val = self._byte_from_str_expr(stmt.get("value"))
                if byte_val != "":
                    rval = str(byte_val)
            if isinstance(value, dict) and self._node_kind_from_dict(value) == "BoolOp" and picked != "bool":
                rval = self.render_boolop(stmt.get("value"), True)
            rval_t0 = self.get_expr_type(stmt.get("value"))
            rval_t = rval_t0 if isinstance(rval_t0, str) else ""
            if self._can_runtime_cast_target(picked) and self.is_any_like_type(rval_t):
                rval = self._coerce_any_expr_to_target_via_unbox(
                    rval,
                    stmt.get("value"),
                    picked,
                    f"assign:{texpr}",
                )
            if self.is_any_like_type(picked):
                rval = self._box_any_target_value(rval, stmt.get("value"))
            self.emit(f"{dtype} {texpr} = {rval};")
            return
        rval = self.render_expr(stmt.get("value"))
        t_target = self.get_expr_type(target_obj)
        if t_target == "None":
            t_target = "Any"
        if self.is_plain_name_expr(target_obj) and t_target in {"", "unknown"}:
            if texpr in self.declared_var_types:
                t_target = self.declared_var_types[texpr]
        if t_target != "":
            rval = self._rewrite_nullopt_default_for_typed_target(rval, t_target)
        if t_target == "uint8" and isinstance(value, dict):
            byte_val = self._byte_from_str_expr(stmt.get("value"))
            if byte_val != "":
                rval = str(byte_val)
        if isinstance(value, dict) and self._node_kind_from_dict(value) == "BoolOp" and t_target != "bool":
            rval = self.render_boolop(stmt.get("value"), True)
        rval_t0 = self.get_expr_type(stmt.get("value"))
        rval_t = rval_t0 if isinstance(rval_t0, str) else ""
        if self._can_runtime_cast_target(t_target) and self.is_any_like_type(rval_t):
            rval = self._coerce_any_expr_to_target_via_unbox(
                rval,
                stmt.get("value"),
                t_target,
                f"assign:{texpr}",
            )
        if self.is_any_like_type(t_target):
            rval = self._box_any_target_value(rval, stmt.get("value"))
        self.emit(f"{texpr} = {rval};")

    def _emit_try_stmt(self, stmt: dict[str, Any]) -> None:
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        has_effective_finally = False
        for s in finalbody:
            if isinstance(s, dict) and self._node_kind_from_dict(s) != "Pass":
                has_effective_finally = True
                break
        if has_effective_finally:
            self.emit(self.syntax_text("scope_open", "{"))
            self.indent += 1
            gid = self.next_finally_guard_name()
            self.emit(
                self.syntax_line(
                    "scope_exit_open",
                    "auto {guard} = py_make_scope_exit([&]() {{",
                    {"guard": gid},
                )
            )
            self.indent += 1
            self.emit_stmt_list(finalbody)
            self.indent -= 1
            self.emit(self.syntax_text("scope_exit_close", "});"))
        if len(handlers) == 0:
            self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
            if has_effective_finally:
                self.indent -= 1
                self.emit_block_close()
            return
        self.emit(self.syntax_text("try_open", "try {"))
        self.indent += 1
        self.emit_stmt_list(self._dict_stmt_list(stmt.get("body")))
        self.indent -= 1
        self.emit_block_close()
        for h in handlers:
            name_raw = h.get("name")
            name = "ex"
            if isinstance(name_raw, str) and name_raw != "":
                name = name_raw
            self.emit(
                self.syntax_line(
                    "catch_open",
                    "catch (const ::std::exception& {name}) {{",
                    {"name": name},
                )
            )
            self.indent += 1
            self.emit_stmt_list(self._dict_stmt_list(h.get("body")))
            self.indent -= 1
            self.emit_block_close()
        if has_effective_finally:
            self.indent -= 1
            self.emit_block_close()

    def _emit_for_body_open(self, header: str, scope_names: set[str], omit_braces: bool) -> None:
        """for 系文のヘッダ出力 + scope 開始を共通化する。"""
        if omit_braces:
            self.emit(header)
        else:
            self.emit(
                self.syntax_line(
                    "for_open_block",
                    "{header} {{",
                    {"header": header},
                )
            )
        self.indent += 1
        self.scope_stack.append(set(scope_names))

    def _emit_for_body_stmts(self, body_stmts: list[dict[str, Any]], omit_braces: bool) -> None:
        """for 系文の本文出力（omit_braces 対応）を共通化する。"""
        if omit_braces:
            self.emit_stmt(body_stmts[0])
            return
        self.emit_stmt_list(body_stmts)

    def _emit_for_body_close(self, omit_braces: bool) -> None:
        """for 系文の scope 終了 + ブロック閉じを共通化する。"""
        self.scope_stack.pop()
        self.indent -= 1
        if not omit_braces:
            self.emit_block_close()

    def emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノードを C++ の for ループとして出力する。"""
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target_node) == 0:
            self.emit("/* invalid for-range target */")
            return
        tgt = self.render_expr(stmt.get("target"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        tgt_ty_txt = t0 if t0 != "" else t1
        tgt_ty = self._cpp_type_text(tgt_ty_txt)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_default = self._default_stmt_omit_braces("ForRange", stmt, False)
        omit_braces = self.hook_on_stmt_omit_braces("ForRange", stmt, omit_default)
        if len(body_stmts) != 1:
            omit_braces = False
        mode_default = self._default_for_range_mode(stmt, "dynamic", step)
        mode = self.hook_on_for_range_mode(stmt, mode_default)
        if mode not in {"ascending", "descending", "dynamic"}:
            mode = mode_default
        cond = (
            f"{tgt} < {stop}"
            if mode == "ascending"
            else (f"{tgt} > {stop}" if mode == "descending" else f"{step} > 0 ? {tgt} < {stop} : {tgt} > {stop}")
        )
        inc = (
            f"++{tgt}"
            if self._opt_ge(2) and step == "1"
            else (f"--{tgt}" if self._opt_ge(2) and step == "-1" else f"{tgt} += {step}")
        )
        hdr: str = self.syntax_line(
            "for_range_open",
            "for ({type} {target} = {start}; {cond}; {inc})",
            {"type": tgt_ty, "target": tgt, "start": start, "cond": cond, "inc": inc},
        )
        self.declared_var_types[tgt] = tgt_ty_txt
        scope_names: set[str] = set()
        scope_names.add(tgt)
        self._emit_for_body_open(hdr, scope_names, omit_braces)
        self._emit_for_body_stmts(body_stmts, omit_braces)
        self._emit_for_body_close(omit_braces)

    def emit_for_each(self, stmt: dict[str, Any]) -> None:
        """For ノード（反復）を C++ range-for として出力する。"""
        target = self.any_to_dict_or_empty(stmt.get("target"))
        iter_expr = self.any_to_dict_or_empty(stmt.get("iter"))
        if len(target) == 0 or len(iter_expr) == 0:
            self.emit("/* invalid for */")
            return
        if self._node_kind_from_dict(iter_expr) == "RangeExpr":
            t_raw = stmt.get("target_type")
            target_type_txt = "int64"
            if isinstance(t_raw, str) and t_raw != "":
                target_type_txt = t_raw
            self.emit_for_range(
                {
                    "target": stmt.get("target"),
                    "target_type": target_type_txt,
                    "start": iter_expr.get("start"),
                    "stop": iter_expr.get("stop"),
                    "step": iter_expr.get("step"),
                    "range_mode": self.any_dict_get_str(iter_expr, "range_mode", "dynamic"),
                    "body": self.any_dict_get_list(stmt, "body"),
                    "orelse": self.any_dict_get_list(stmt, "orelse"),
                }
            )
            return
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        omit_default = self._default_stmt_omit_braces("For", stmt, False)
        omit_braces = self.hook_on_stmt_omit_braces("For", stmt, omit_default)
        if len(body_stmts) != 1:
            omit_braces = False
        iter_mode = self._resolve_for_iter_mode(stmt, iter_expr)
        if iter_mode == "runtime_protocol":
            self._emit_for_each_runtime(stmt, target, iter_expr, body_stmts, omit_braces)
            return
        t = self.render_expr(stmt.get("target"))
        it = self.render_expr(stmt.get("iter"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        t_ty = self._cpp_type_text(t0 if t0 != "" else t1)
        target_names = self.target_bound_names(target)
        unpack_tuple = self._node_kind_from_dict(target) == "Tuple"
        iter_tmp = ""
        hdr = ""
        if unpack_tuple:
            iter_tmp = self.next_for_iter_name()
            target_names = self.scope_names_with_tmp(target_names, iter_tmp)
            hdr = self.syntax_line(
                "for_each_unpack_open",
                "for (auto {iter_tmp} : {iter})",
                {"iter_tmp": iter_tmp, "iter": it},
            )
        else:
            hdr = (
                self.syntax_line(
                    "for_each_auto_ref_open",
                    "for (auto& {target} : {iter})",
                    {"target": t, "iter": it},
                )
                if t_ty == "auto"
                else self.syntax_line(
                    "for_each_typed_open",
                    "for ({type} {target} : {iter})",
                    {"type": t_ty, "target": t, "iter": it},
                )
            )
            if t_ty != "auto":
                self.declared_var_types[t] = t0 if t0 != "" else t1

        self._emit_for_body_open(hdr, target_names, omit_braces)
        if unpack_tuple:
            self._emit_target_unpack(target, iter_tmp, iter_expr)
        self._emit_for_body_stmts(body_stmts, omit_braces)
        self._emit_for_body_close(omit_braces)

    def _emit_target_unpack(self, target: dict[str, Any], src: str, iter_expr: dict[str, Any]) -> None:
        """タプルターゲットへのアンパック代入を出力する。"""
        if not isinstance(target, dict) or len(target) == 0:
            return
        if self._node_kind_from_dict(target) != "Tuple":
            return
        elem_types: list[str] = []
        iter_node: dict[str, Any] = iter_expr
        if len(iter_node) > 0:
            iter_kind: str = self._node_kind_from_dict(iter_node)
            iter_t: str = self.any_dict_get_str(iter_node, "resolved_type", "")
            if iter_t.startswith("list[") and iter_t.endswith("]"):
                inner_txt: str = iter_t[5:-1]
                if inner_txt.startswith("tuple[") and inner_txt.endswith("]"):
                    elem_types = self.split_generic(inner_txt[6:-1])
            elif iter_t.startswith("set[") and iter_t.endswith("]"):
                inner_txt = iter_t[4:-1]
                if inner_txt.startswith("tuple[") and inner_txt.endswith("]"):
                    elem_types = self.split_generic(inner_txt[6:-1])
            elif iter_kind == "Call":
                runtime_call: str = self.any_dict_get_str(iter_node, "runtime_call", "")
                if runtime_call == "dict.items":
                    fn_node = self.any_to_dict_or_empty(iter_node.get("func"))
                    owner_obj = fn_node.get("value")
                    owner_t: str = self.get_expr_type(owner_obj)
                    if owner_t.startswith("dict[") and owner_t.endswith("]"):
                        dict_inner_parts: list[str] = self.split_generic(owner_t[5:-1])
                        if len(dict_inner_parts) == 2:
                            elem_types = [self.normalize_type_name(dict_inner_parts[0]), self.normalize_type_name(dict_inner_parts[1])]
        for i, e in enumerate(self.any_dict_get_list(target, "elements")):
            if isinstance(e, dict) and self._node_kind_from_dict(e) == "Name":
                nm = self.render_expr(e)
                elem_decl_t = self.normalize_type_name(elem_types[i]) if i < len(elem_types) else ""
                decl_t = elem_decl_t if elem_decl_t != "" else self.normalize_type_name(self.get_expr_type(e))
                decl_t = decl_t if decl_t != "" else "unknown"
                self.declared_var_types[nm] = decl_t
                if self.is_any_like_type(decl_t):
                    self.emit(f"auto {nm} = ::std::get<{i}>({src});")
                else:
                    self.emit(f"{self._cpp_type_text(decl_t)} {nm} = ::std::get<{i}>({src});")

    def _emit_target_unpack_runtime(self, target: dict[str, Any], src_obj: str, iter_expr: dict[str, Any]) -> None:
        """runtime iterable プロトコル用のタプル unpack（`py_at` ベース）。"""
        if self._node_kind_from_dict(target) != "Tuple":
            return
        elem_types: list[str] = []
        target_t = self.any_dict_get_str(target, "resolved_type", "")
        if target_t.startswith("tuple[") and target_t.endswith("]"):
            elem_types = self.split_generic(target_t[6:-1])
        if len(elem_types) == 0 and len(iter_expr) > 0:
            iter_t = self.any_dict_get_str(iter_expr, "resolved_type", "")
            if iter_t.startswith("list[") and iter_t.endswith("]"):
                inner = iter_t[5:-1]
                if inner.startswith("tuple[") and inner.endswith("]"):
                    elem_types = self.split_generic(inner[6:-1])
            elif iter_t.startswith("set[") and iter_t.endswith("]"):
                inner = iter_t[4:-1]
                if inner.startswith("tuple[") and inner.endswith("]"):
                    elem_types = self.split_generic(inner[6:-1])
        elems = self.any_to_list(target.get("elements"))
        for i, e in enumerate(elems):
            e_node = self.any_to_dict_or_empty(e)
            if self._node_kind_from_dict(e_node) != "Name":
                continue
            nm = self.render_expr(e)
            rhs = f"py_at({src_obj}, {i})"
            elem_decl_t = self.normalize_type_name(elem_types[i]) if i < len(elem_types) else ""
            decl_t = elem_decl_t if elem_decl_t != "" else self.normalize_type_name(self.get_expr_type(e))
            if self._can_runtime_cast_target(decl_t):
                rhs = self.render_expr(
                    self._build_unbox_expr_node(
                        self._build_py_at_expr_node(src_obj, i),
                        decl_t,
                        f"for_unpack:{nm}",
                    )
                )
                self.emit(f"{self._cpp_type_text(decl_t)} {nm} = {rhs};")
                self.declared_var_types[nm] = decl_t
            else:
                self.emit(f"auto {nm} = {rhs};")
                self.declared_var_types[nm] = "object"

    def _emit_for_each_runtime_target_bind(
        self,
        target: dict[str, Any],
        target_name: str,
        target_decl_type: str,
        iter_tmp: str,
    ) -> None:
        """runtime for-each で一時 object をターゲットへ束縛する。"""
        if iter_tmp == "" or self._node_kind_from_dict(target) != "Name":
            return
        rhs = iter_tmp
        if self._can_runtime_cast_target(target_decl_type):
            rhs = self.render_expr(
                self._build_unbox_expr_node(
                    self._build_name_expr_node(iter_tmp, "object"),
                    target_decl_type,
                    f"for_target:{target_name}",
                )
            )
            self.emit(f"{self._cpp_type_text(target_decl_type)} {target_name} = {rhs};")
            self.declared_var_types[target_name] = target_decl_type
            return
        self.emit(f"auto {target_name} = {rhs};")
        self.declared_var_types[target_name] = "object"

    def _emit_for_each_runtime(
        self,
        stmt: dict[str, Any],
        target: dict[str, Any],
        iter_expr: dict[str, Any],
        body_stmts: list[dict[str, Any]],
        omit_braces: bool,
    ) -> None:
        """`For` を runtime iterable プロトコル（`py_dyn_range`）で出力する。"""
        t = self.render_expr(stmt.get("target"))
        it = self.render_expr(stmt.get("iter"))
        t0 = self.any_to_str(stmt.get("target_type"))
        t1 = self.get_expr_type(stmt.get("target"))
        t_decl = self.normalize_type_name(t0 if t0 != "" else t1)
        unpack_tuple = self._node_kind_from_dict(target) == "Tuple"
        target_names = self.target_bound_names(target)
        iter_tmp = ""
        hdr = ""
        needs_tmp = unpack_tuple or self._node_kind_from_dict(target) != "Name" or not self.is_any_like_type(t_decl)
        if needs_tmp:
            iter_tmp = self.next_for_runtime_iter_name()
            target_names = self.scope_names_with_tmp(target_names, iter_tmp)
            hdr = self.syntax_line(
                "for_each_runtime_open",
                "for (object {iter_tmp} : py_dyn_range({iter}))",
                {"iter_tmp": iter_tmp, "iter": it},
            )
        else:
            hdr = self.syntax_line(
                "for_each_runtime_target_open",
                "for (object {target} : py_dyn_range({iter}))",
                {"target": t, "iter": it},
            )
            if t != "":
                self.declared_var_types[t] = "object"

        self._emit_for_body_open(hdr, target_names, omit_braces)
        if unpack_tuple:
            self._emit_target_unpack_runtime(target, iter_tmp, iter_expr)
        else:
            self._emit_for_each_runtime_target_bind(target, t, t_decl, iter_tmp)
        self._emit_for_body_stmts(body_stmts, omit_braces)
        self._emit_for_body_close(omit_braces)

    def _forcore_target_bound_names(self, target_plan: dict[str, Any]) -> set[str]:
        """ForCore `target_plan` から scope 登録すべき束縛名を抽出する。"""
        out: set[str] = set()
        plan_kind = self.any_dict_get_str(target_plan, "kind", "")
        if plan_kind == "NameTarget":
            target_id = self.any_dict_get_str(target_plan, "id", "")
            if target_id != "":
                out.add(target_id)
            return out
        if plan_kind == "TupleTarget":
            for elem_obj in self.any_to_list(target_plan.get("elements")):
                elem_plan = self.any_to_dict_or_empty(elem_obj)
                out |= self._forcore_target_bound_names(elem_plan)
        return out

    def _emit_forcore_tuple_unpack_runtime(
        self,
        target_plan: dict[str, Any],
        src_obj: str,
        inherited_elem_types: list[str] | None = None,
    ) -> None:
        """ForCore tuple target を runtime iterable でアンパックする。"""
        elem_plans = self.any_to_list(target_plan.get("elements"))
        elem_types: list[str] = inherited_elem_types if isinstance(inherited_elem_types, list) else []
        if len(elem_types) == 0:
            parent_target_type = self.normalize_type_name(self.any_dict_get_str(target_plan, "target_type", ""))
            if parent_target_type.startswith("tuple[") and parent_target_type.endswith("]"):
                elem_types = self.split_generic(parent_target_type[6:-1])
        for i, elem_plan_obj in enumerate(elem_plans):
            elem_plan = self.any_to_dict_or_empty(elem_plan_obj)
            plan_kind = self.any_dict_get_str(elem_plan, "kind", "")
            if plan_kind == "NameTarget":
                nm = self.any_dict_get_str(elem_plan, "id", "")
                if nm == "":
                    continue
                elem_t = self.normalize_type_name(self.any_dict_get_str(elem_plan, "target_type", ""))
                if elem_t in {"", "unknown"} and i < len(elem_types):
                    elem_t = self.normalize_type_name(elem_types[i])
                if elem_t == "":
                    elem_t = "unknown"
                rhs = f"py_at({src_obj}, {i})"
                if self._can_runtime_cast_target(elem_t):
                    rhs = self.render_expr(
                        self._build_unbox_expr_node(
                            self._build_py_at_expr_node(src_obj, i),
                            elem_t,
                            f"for_unpack:{nm}",
                        )
                    )
                    self.emit(f"{self._cpp_type_text(elem_t)} {nm} = {rhs};")
                    self.declared_var_types[nm] = elem_t
                else:
                    self.emit(f"auto {nm} = {rhs};")
                    self.declared_var_types[nm] = "object"
                continue
            if plan_kind == "TupleTarget":
                nested_tmp = self.next_for_runtime_iter_name()
                self.emit(f"object {nested_tmp} = py_at({src_obj}, {i});")
                nested_elem_types: list[str] = []
                if i < len(elem_types):
                    nested_type = self.normalize_type_name(elem_types[i])
                    if nested_type.startswith("tuple[") and nested_type.endswith("]"):
                        nested_elem_types = self.split_generic(nested_type[6:-1])
                self._emit_forcore_tuple_unpack_runtime(elem_plan, nested_tmp, nested_elem_types)

    def _range_mode_from_step_expr(self, step_expr: dict[str, Any]) -> str:
        """`step` 式から `range_mode`（ascending/descending/dynamic）を求める。"""
        step_value = step_expr.get("value")
        if isinstance(step_value, int):
            if step_value == 1:
                return "ascending"
            if step_value == -1:
                return "descending"
        return "dynamic"

    def _forcore_runtime_iter_item_type(
        self, iter_expr: dict[str, Any], iter_plan: dict[str, Any] | None = None
    ) -> str:
        """ForCore runtime iterable の要素型（既知時）を返す。"""
        iter_plan_norm = iter_plan if isinstance(iter_plan, dict) else {}
        iter_item_hint = self.normalize_type_name(self.any_dict_get_str(iter_plan_norm, "iter_item_type", ""))
        if iter_item_hint not in {"", "unknown"} and not self.is_any_like_type(iter_item_hint):
            return iter_item_hint
        iter_elem_hint = self.normalize_type_name(self.any_dict_get_str(iter_expr, "iter_element_type", ""))
        if iter_elem_hint not in {"", "unknown"} and not self.is_any_like_type(iter_elem_hint):
            return iter_elem_hint
        if len(iter_expr) == 0:
            return ""
        iter_t = self.normalize_type_name(self.any_dict_get_str(iter_expr, "resolved_type", ""))
        if iter_t in {"", "unknown"}:
            iter_t = self.normalize_type_name(self.get_expr_type(iter_expr))
        if iter_t.startswith("list[") and iter_t.endswith("]"):
            parts = self.split_generic(iter_t[5:-1])
            if len(parts) == 1:
                return self.normalize_type_name(parts[0])
        if iter_t.startswith("set[") and iter_t.endswith("]"):
            parts = self.split_generic(iter_t[4:-1])
            if len(parts) == 1:
                return self.normalize_type_name(parts[0])
        if self._node_kind_from_dict(iter_expr) == "Call":
            runtime_call = self.any_dict_get_str(iter_expr, "runtime_call", "")
            if runtime_call == "dict.items":
                fn_node = self.any_to_dict_or_empty(iter_expr.get("func"))
                owner_obj = fn_node.get("value")
                owner_t = self.normalize_type_name(self.get_expr_type(owner_obj))
                if owner_t.startswith("dict[") and owner_t.endswith("]"):
                    dict_inner_parts = self.split_generic(owner_t[5:-1])
                    if len(dict_inner_parts) == 2:
                        key_t = self.normalize_type_name(dict_inner_parts[0])
                        val_t = self.normalize_type_name(dict_inner_parts[1])
                        if key_t != "" and val_t != "":
                            return f"tuple[{key_t}, {val_t}]"
        return ""

    def emit_for_core(self, stmt: dict[str, Any]) -> None:
        """EAST3 `ForCore` を直接 C++ ループへ描画する。"""
        iter_plan = self.any_to_dict_or_empty(stmt.get("iter_plan"))
        plan_kind = self.any_dict_get_str(iter_plan, "kind", "")
        target_plan = self.any_to_dict_or_empty(stmt.get("target_plan"))
        body_stmts = self.any_dict_get_list(stmt, "body")
        _ = self.any_dict_get_list(stmt, "orelse")
        omit_default = self._default_stmt_omit_braces("ForCore", stmt, False)
        omit_braces = self.hook_on_stmt_omit_braces("ForCore", stmt, omit_default)
        if len(body_stmts) != 1:
            omit_braces = False

        if plan_kind == "StaticRangeForPlan":
            if self.any_dict_get_str(target_plan, "kind", "") != "NameTarget":
                self.emit("/* invalid forcore target for static range */")
                return
            target_id = self.any_dict_get_str(target_plan, "id", "")
            if target_id == "":
                self.emit("/* invalid forcore target name */")
                return
            target_type = self.normalize_type_name(self.any_dict_get_str(target_plan, "target_type", ""))
            if target_type in {"", "unknown"}:
                target_type = "int64"
            start_expr = iter_plan.get("start")
            stop_expr = iter_plan.get("stop")
            step_obj = iter_plan.get("step")
            step_expr = self.any_to_dict_or_empty(step_obj)
            if len(step_expr) == 0:
                step_expr = {"kind": "Constant", "resolved_type": "int64", "value": 1, "repr": "1"}
            start_txt = self.render_expr(start_expr)
            stop_txt = self.render_expr(stop_expr)
            step_txt = self.render_expr(step_expr)
            range_mode_txt = self.any_dict_get_str(iter_plan, "range_mode", "")
            if range_mode_txt == "":
                range_mode_txt = self._range_mode_from_step_expr(step_expr)
            cond = (
                f"{target_id} < {stop_txt}"
                if range_mode_txt == "ascending"
                else (
                    f"{target_id} > {stop_txt}"
                    if range_mode_txt == "descending"
                    else f"{step_txt} > 0 ? {target_id} < {stop_txt} : {target_id} > {stop_txt}"
                )
            )
            inc = (
                f"++{target_id}"
                if self._opt_ge(2) and step_txt == "1"
                else (f"--{target_id}" if self._opt_ge(2) and step_txt == "-1" else f"{target_id} += {step_txt}")
            )
            hdr = self.syntax_line(
                "for_range_open",
                "for ({type} {target} = {start}; {cond}; {inc})",
                {
                    "type": self._cpp_type_text(target_type),
                    "target": target_id,
                    "start": start_txt,
                    "cond": cond,
                    "inc": inc,
                },
            )
            self.declared_var_types[target_id] = target_type
            self._emit_for_body_open(hdr, {target_id}, omit_braces)
            self._emit_for_body_stmts(body_stmts, omit_braces)
            self._emit_for_body_close(omit_braces)
            return

        if plan_kind == "RuntimeIterForPlan":
            iter_expr = self.any_to_dict_or_empty(iter_plan.get("iter_expr"))
            if len(iter_expr) == 0:
                self.emit("/* invalid forcore runtime iter_plan */")
                return
            iter_txt = self.render_expr(iter_expr)
            target_kind = self.any_dict_get_str(target_plan, "kind", "")
            if target_kind == "NameTarget":
                target_id = self.any_dict_get_str(target_plan, "id", "")
                if target_id == "":
                    self.emit("/* invalid forcore target name */")
                    return
                target_type = self.normalize_type_name(self.any_dict_get_str(target_plan, "target_type", ""))
                iter_item_t = self._forcore_runtime_iter_item_type(iter_expr, iter_plan)
                typed_iter = iter_item_t not in {"", "unknown"} and not self.is_any_like_type(iter_item_t)
                if target_type in {"", "unknown"}:
                    target_type = iter_item_t if typed_iter else "object"
                if self.is_any_like_type(target_type):
                    hdr = self.syntax_line(
                        "for_each_runtime_target_open",
                        "for (object {target} : py_dyn_range({iter}))",
                        {"target": target_id, "iter": iter_txt},
                    )
                    self.declared_var_types[target_id] = "object"
                    self._emit_for_body_open(hdr, {target_id}, omit_braces)
                    self._emit_for_body_stmts(body_stmts, omit_braces)
                    self._emit_for_body_close(omit_braces)
                    return
                if typed_iter:
                    hdr = self.syntax_line(
                        "for_each_typed_open",
                        "for ({type} {target} : {iter})",
                        {"type": self._cpp_type_text(target_type), "target": target_id, "iter": iter_txt},
                    )
                    self.declared_var_types[target_id] = target_type
                    self._emit_for_body_open(hdr, {target_id}, omit_braces)
                    self._emit_for_body_stmts(body_stmts, omit_braces)
                    self._emit_for_body_close(omit_braces)
                    return
                iter_tmp = self.next_for_runtime_iter_name()
                hdr = self.syntax_line(
                    "for_each_runtime_open",
                    "for (object {iter_tmp} : py_dyn_range({iter}))",
                    {"iter_tmp": iter_tmp, "iter": iter_txt},
                )
                self._emit_for_body_open(hdr, self.scope_names_with_tmp({target_id}, iter_tmp), omit_braces)
                rhs = self.render_expr(
                    self._build_unbox_expr_node(
                        self._build_name_expr_node(iter_tmp, "object"),
                        target_type,
                        f"for_target:{target_id}",
                    )
                )
                self.emit(f"{self._cpp_type_text(target_type)} {target_id} = {rhs};")
                self.declared_var_types[target_id] = target_type
                self._emit_for_body_stmts(body_stmts, omit_braces)
                self._emit_for_body_close(omit_braces)
                return
            if target_kind == "TupleTarget":
                iter_tmp = self.next_for_runtime_iter_name()
                scope_names = self.scope_names_with_tmp(self._forcore_target_bound_names(target_plan), iter_tmp)
                iter_item_t = self._forcore_runtime_iter_item_type(iter_expr, iter_plan)
                typed_iter = iter_item_t not in {"", "unknown"} and not self.is_any_like_type(iter_item_t)
                inherited_elem_types: list[str] = []
                if typed_iter and iter_item_t.startswith("tuple[") and iter_item_t.endswith("]"):
                    inherited_elem_types = self.split_generic(iter_item_t[6:-1])
                direct_unpack = bool(target_plan.get("direct_unpack", False))
                direct_names_obj = target_plan.get("direct_unpack_names")
                direct_types_obj = target_plan.get("direct_unpack_types")
                direct_names = direct_names_obj if isinstance(direct_names_obj, list) else []
                direct_types = direct_types_obj if isinstance(direct_types_obj, list) else []
                direct_names_txt: list[str] = []
                for raw_name in direct_names:
                    if isinstance(raw_name, str) and raw_name != "":
                        direct_names_txt.append(raw_name)
                if typed_iter and direct_unpack and len(direct_names_txt) > 0:
                    bind_targets = ", ".join(direct_names_txt)
                    hdr = f"for (const auto& [{bind_targets}] : {iter_txt})"
                    self._emit_for_body_open(hdr, set(direct_names_txt), omit_braces)
                    i = 0
                    while i < len(direct_names_txt):
                        nm = direct_names_txt[i]
                        nm_t = "unknown"
                        if i < len(direct_types) and isinstance(direct_types[i], str):
                            nm_t = self.normalize_type_name(direct_types[i])
                        if nm_t != "":
                            self.declared_var_types[nm] = nm_t
                        i += 1
                    self._emit_for_body_stmts(body_stmts, omit_braces)
                    self._emit_for_body_close(omit_braces)
                    return
                if typed_iter:
                    hdr = self.syntax_line(
                        "for_each_typed_open",
                        "for (const {type}& {target} : {iter})",
                        {"type": self._cpp_type_text(iter_item_t), "target": iter_tmp, "iter": iter_txt},
                    )
                else:
                    hdr = self.syntax_line(
                        "for_each_runtime_open",
                        "for (object {iter_tmp} : py_dyn_range({iter}))",
                        {"iter_tmp": iter_tmp, "iter": iter_txt},
                    )
                self._emit_for_body_open(hdr, scope_names, omit_braces)
                self._emit_forcore_tuple_unpack_runtime(target_plan, iter_tmp, inherited_elem_types)
                self._emit_for_body_stmts(body_stmts, omit_braces)
                self._emit_for_body_close(omit_braces)
                return
            self.emit("/* invalid forcore runtime target */")
            return

        self.emit(f"/* unsupported ForCore iter_plan kind: {plan_kind} */")

    def _resolve_for_iter_mode(self, stmt: dict[str, Any], iter_expr: dict[str, Any]) -> str:
        """`For` の反復モード（static/runtime）を決定する。"""
        mode_txt = self.any_to_str(stmt.get("iter_mode"))
        if mode_txt == "static_fastpath" or mode_txt == "runtime_protocol":
            return mode_txt
        list_model = self.any_to_str(getattr(self, "cpp_list_model", "value"))
        iter_t = self.normalize_type_name(self.get_expr_type(iter_expr))
        if iter_t == "":
            iter_t = self.normalize_type_name(self.any_dict_get_str(iter_expr, "resolved_type", ""))
        if iter_t == "Any" or iter_t == "object":
            return "runtime_protocol"
        if list_model == "pyobj":
            if iter_t.startswith("list[") and iter_t.endswith("]"):
                return "runtime_protocol"
        # 明示 `iter_mode` が無い既存 EAST では selfhost 互換を優先し、unknown は static 側に倒す。
        if iter_t == "" or iter_t == "unknown":
            return "static_fastpath"
        if self._contains_text(iter_t, "|"):
            parts = self.split_union(iter_t)
            for p in parts:
                p_norm = self.normalize_type_name(p)
                if p_norm == "Any" or p_norm == "object":
                    return "runtime_protocol"
                if list_model == "pyobj" and p_norm.startswith("list[") and p_norm.endswith("]"):
                    return "runtime_protocol"
            return "static_fastpath"
        return "static_fastpath"

    def emit_function(self, stmt: dict[str, Any], in_class: bool = False) -> None:
        """関数定義ノードを C++ 関数として出力する。"""
        name = self.any_dict_get_str(stmt, "name", "fn")
        emitted_name = self.rename_if_reserved(str(name), self.reserved_words, self.rename_prefix, self.renamed_symbols)
        is_generator = self.any_dict_get_int(stmt, "is_generator", 0) != 0
        yield_value_type = self.any_to_str(stmt.get("yield_value_type"))
        ret = self.cpp_type(stmt.get("return_type"))
        if is_generator:
            elem_type_for_cpp = yield_value_type
            if elem_type_for_cpp in {"", "unknown"}:
                elem_type_for_cpp = "Any"
            elem_cpp = self._cpp_type_text(elem_type_for_cpp)
            ret = f"list<{elem_cpp}>"
        arg_types = self.any_to_dict_or_empty(stmt.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(stmt.get("arg_usage"))
        arg_defaults = self.any_to_dict_or_empty(stmt.get("arg_defaults"))
        arg_index = self.any_to_dict_or_empty(stmt.get("arg_index"))
        body_stmts = self._dict_stmt_list(stmt.get("body"))
        params: list[str] = []
        fn_scope: set[str] = set()
        arg_names: list[str] = []
        raw_order = self.any_dict_get_list(stmt, "arg_order")
        for raw_n in raw_order:
            if isinstance(raw_n, str) and raw_n != "":
                n = str(raw_n)
                if n in arg_types:
                    arg_names.append(n)
        mutated_params = self._collect_mutated_params(body_stmts, arg_names)
        for idx, n in enumerate(arg_names):
            t = self.any_to_str(arg_types.get(n))
            skip_self = in_class and idx == 0 and n == "self"
            ct = self._cpp_type_text(t)
            usage = self.any_to_str(arg_usage.get(n))
            usage = usage if usage != "" else "readonly"
            if usage != "mutable" and n in mutated_params:
                usage = "mutable"
            by_ref = ct not in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64", "float32", "float64", "bool"}
            if skip_self:
                pass
            else:
                param_txt = (
                    (f"{ct} {n}" if ct == "object" else f"{ct}& {n}")
                    if by_ref and usage == "mutable"
                    else (f"const {ct}& {n}" if by_ref else f"{ct} {n}")
                )
                if n in arg_defaults:
                    default_txt = self._render_param_default_expr(arg_defaults.get(n), t)
                    if default_txt != "":
                        default_txt = self._coerce_param_signature_default(default_txt, t)
                        param_txt += f" = {default_txt}"
                params.append(param_txt)
                fn_scope.add(n)
        if in_class and name == "__init__" and self.current_class_name is not None:
            param_sep = ", "
            params_txt = param_sep.join(params)
            if self.current_class_base_name == "CodeEmitter":
                self.emit(f"{self.current_class_name}({params_txt}) : CodeEmitter(east_doc, load_cpp_profile(), dict<str, object>{{}}) {{")
            else:
                self.emit_ctor_open(str(self.current_class_name), params_txt)
        elif in_class and name == "__del__" and self.current_class_name is not None:
            self.emit_dtor_open(str(self.current_class_name))
        else:
            param_sep = ", "
            params_txt = param_sep.join(params)
            if self.current_class_name is not None and in_class:
                func_prefix = ""
                func_suffix = ""
                if name != "__del__":
                    if self._class_has_base_method(self.current_class_name, str(name)):
                        func_suffix = " override"
                    elif str(name) in self.class_method_virtual.get(self.current_class_name, set()):
                        func_prefix = "virtual "
                self.emit(f"{func_prefix}{ret} {emitted_name}({params_txt}){func_suffix} {{")
            else:
                self.emit_function_open(ret, str(emitted_name), params_txt)
        docstring = self.any_to_str(stmt.get("docstring"))
        self.indent += 1
        self.scope_stack.append(set(fn_scope))
        prev_ret = self.current_function_return_type
        prev_is_gen = self.current_function_is_generator
        prev_yield_buf = self.current_function_yield_buffer
        prev_yield_ty = self.current_function_yield_type
        prev_decl_types = self.declared_var_types
        empty_decl_types: dict[str, str] = {}
        self.declared_var_types = empty_decl_types
        for i, an in enumerate(arg_names):
            if not (in_class and i == 0 and an == "self"):
                at = self.any_to_str(arg_types.get(an))
                if at != "":
                    self.declared_var_types[an] = self.normalize_type_name(at)
        self.current_function_return_type = self.any_to_str(stmt.get("return_type"))
        self.current_function_is_generator = is_generator
        self.current_function_yield_type = yield_value_type if yield_value_type != "" else "Any"
        self.current_function_yield_buffer = self.next_yield_values_name() if is_generator else ""
        if docstring != "":
            self.emit_block_comment(docstring)
        if is_generator:
            yield_elem_ty = self.current_function_yield_type
            if yield_elem_ty in {"", "unknown"}:
                yield_elem_ty = "Any"
            yield_elem_cpp = self._cpp_type_text(yield_elem_ty)
            self.emit(f"list<{yield_elem_cpp}> {self.current_function_yield_buffer} = list<{yield_elem_cpp}>{{}};")
        self.emit_stmt_list(body_stmts)
        if is_generator and self.current_function_yield_buffer != "":
            self.emit(f"return {self.current_function_yield_buffer};")
        self.current_function_return_type = prev_ret
        self.current_function_is_generator = prev_is_gen
        self.current_function_yield_buffer = prev_yield_buf
        self.current_function_yield_type = prev_yield_ty
        self.declared_var_types = prev_decl_types
        self.scope_stack.pop()
        self.indent -= 1
        self.emit_block_close()

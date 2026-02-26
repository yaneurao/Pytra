from __future__ import annotations

from pytra.std.typing import Any


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

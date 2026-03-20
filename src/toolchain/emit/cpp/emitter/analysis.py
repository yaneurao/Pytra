from __future__ import annotations

from pytra.typing import Any


class CppAnalysisEmitter:
    """Analysis helpers for assignment/type/mutability inference."""

    def _strip_rc_wrapper(self, t: str) -> str:
        """`rc<T>` 形式の型文字列を `T` へ正規化する。"""
        txt = self.normalize_type_name(t)
        if txt.startswith("rc<") and txt.endswith(">"):
            inner = txt[3:-1].strip()
            if inner != "":
                return self.normalize_type_name(inner)
        return txt

    def should_skip_same_type_cast(self, rendered_expr: str, target_t: str) -> bool:
        """同型かつ非 Any/object/unknown なら cast を省略できるか判定する。"""
        t_norm = self.normalize_type_name(target_t)
        if t_norm in {"", "unknown"}:
            return False
        if self.is_any_like_type(t_norm):
            return False
        inferred_src_t = self.normalize_type_name(
            self.infer_rendered_arg_type(rendered_expr, "unknown", self.declared_var_types)
        )
        if inferred_src_t in {"", "unknown"}:
            return False
        if self.is_any_like_type(inferred_src_t):
            return False
        t_cmp = self._strip_rc_wrapper(t_norm)
        src_cmp = self._strip_rc_wrapper(inferred_src_t)
        return src_cmp == t_cmp

    def _collect_assigned_name_types(self, stmts: list[dict[str, Any]]) -> dict[str, str]:
        """文リスト中の `Name` 代入候補型を収集する。"""
        out: dict[str, str] = {}
        saved_decl_types = self.declared_var_types
        local_decl_types = dict(saved_decl_types)
        self.declared_var_types = local_decl_types
        try:
            for st in stmts:
                kind = self._node_kind_from_dict(st)
                if kind == "Assign":
                    tgt = self.any_to_dict_or_empty(st.get("target"))
                    if self._node_kind_from_dict(tgt) == "Name":
                        name = self.any_to_str(tgt.get("id"))
                        if name != "":
                            inferred = self._infer_name_assign_type(st, tgt)
                            out[name] = inferred
                            if inferred not in {"", "unknown"}:
                                local_decl_types[name] = self.normalize_type_name(inferred)
                    elif self._node_kind_from_dict(tgt) == "Tuple":
                        elems = self.any_dict_get_list(tgt, "elements")
                        value_t_obj = self.get_expr_type(st.get("value"))
                        value_t = value_t_obj if isinstance(value_t_obj, str) else ""
                        tuple_t = ""
                        if value_t.startswith("tuple[") and value_t.endswith("]"):
                            tuple_t = value_t
                        elif self._contains_text(value_t, "|"):
                            for part in self.split_union(value_t):
                                if part.startswith("tuple[") and part.endswith("]"):
                                    tuple_t = part
                                    break
                        elem_types: list[str] = []
                        if tuple_t != "":
                            elem_types = self.split_generic(tuple_t[6:-1])
                        for i, elem in enumerate(elems):
                            ent = self.any_to_dict_or_empty(elem)
                            if self._node_kind_from_dict(ent) == "Name":
                                nm = self.any_to_str(ent.get("id"))
                                if nm != "":
                                    et = ""
                                    if i < len(elem_types):
                                        et = self.normalize_type_name(elem_types[i])
                                    if et == "":
                                        t_ent = self.get_expr_type(elem)
                                        if isinstance(t_ent, str):
                                            et = self.normalize_type_name(t_ent)
                                    out[nm] = et
                                    if et not in {"", "unknown"}:
                                        local_decl_types[nm] = self.normalize_type_name(et)
                elif kind == "AnnAssign":
                    tgt = self.any_to_dict_or_empty(st.get("target"))
                    if self._node_kind_from_dict(tgt) == "Name":
                        name = self.any_to_str(tgt.get("id"))
                        if name != "":
                            inferred = self._infer_name_assign_type(st, tgt)
                            out[name] = inferred
                            if inferred not in {"", "unknown"}:
                                local_decl_types[name] = self.normalize_type_name(inferred)
                elif kind == "If":
                    child_body = self._collect_assigned_name_types(self._dict_stmt_list(st.get("body")))
                    child_else = self._collect_assigned_name_types(self._dict_stmt_list(st.get("orelse")))
                    for nm, ty in child_body.items():
                        out[nm] = ty
                        if ty not in {"", "unknown"}:
                            local_decl_types[nm] = self.normalize_type_name(ty)
                    for nm, ty in child_else.items():
                        if nm in out:
                            merged = self._merge_decl_types_for_branch_join(out[nm], ty)
                            out[nm] = merged
                            if merged not in {"", "unknown"}:
                                local_decl_types[nm] = self.normalize_type_name(merged)
                        else:
                            out[nm] = ty
                            if ty not in {"", "unknown"}:
                                local_decl_types[nm] = self.normalize_type_name(ty)
                elif kind == "Try":
                    child_groups: list[list[dict[str, Any]]] = []
                    child_groups.append(self._dict_stmt_list(st.get("body")))
                    child_groups.append(self._dict_stmt_list(st.get("orelse")))
                    child_groups.append(self._dict_stmt_list(st.get("finalbody")))
                    for h in self._dict_stmt_list(st.get("handlers")):
                        child_groups.append(self._dict_stmt_list(h.get("body")))
                    for grp in child_groups:
                        child_map = self._collect_assigned_name_types(grp)
                        for nm, ty in child_map.items():
                            if nm in out:
                                merged = self._merge_decl_types_for_branch_join(out[nm], ty)
                                out[nm] = merged
                                if merged not in {"", "unknown"}:
                                    local_decl_types[nm] = self.normalize_type_name(merged)
                            else:
                                out[nm] = ty
                                if ty not in {"", "unknown"}:
                                    local_decl_types[nm] = self.normalize_type_name(ty)
                elif kind in {"While", "For", "ForRange", "ForCore"}:
                    child_groups = [self._dict_stmt_list(st.get("body")), self._dict_stmt_list(st.get("orelse"))]
                    for grp in child_groups:
                        child_map = self._collect_assigned_name_types(grp)
                        for nm, ty in child_map.items():
                            if nm in out:
                                merged = self._merge_decl_types_for_branch_join(out[nm], ty)
                                out[nm] = merged
                                if merged not in {"", "unknown"}:
                                    local_decl_types[nm] = self.normalize_type_name(merged)
                            else:
                                out[nm] = ty
                                if ty not in {"", "unknown"}:
                                    local_decl_types[nm] = self.normalize_type_name(ty)
        finally:
            self.declared_var_types = saved_decl_types
        return out

    def _collect_assigned_name_counts(self, stmts: list[dict[str, Any]]) -> dict[str, int]:
        """文リスト中で `Name` に代入される回数を再帰収集する。"""
        out: dict[str, int] = {}

        def _inc(name: str) -> None:
            if name == "":
                return
            out[name] = int(out.get(name, 0)) + 1

        def _collect_target(target_obj: Any) -> None:
            target = self.any_to_dict_or_empty(target_obj)
            kind = self._node_kind_from_dict(target)
            if kind == "Name":
                _inc(self.any_to_str(target.get("id")))
                return
            if kind == "Tuple":
                for elem in self.any_to_list(target.get("elements")):
                    _collect_target(elem)

        def _collect_target_plan(target_plan_obj: Any) -> None:
            target_plan = self.any_to_dict_or_empty(target_plan_obj)
            kind = self._node_kind_from_dict(target_plan)
            if kind == "NameTarget":
                _inc(self.any_to_str(target_plan.get("id")))
                return
            if kind == "TupleTarget":
                for elem in self.any_to_list(target_plan.get("elements")):
                    _collect_target_plan(elem)

        def _visit(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    _visit(item)
                return
            if not isinstance(node, dict):
                return
            d: dict[str, Any] = node
            kind = self._node_kind_from_dict(d)
            if kind in {"Assign", "AnnAssign", "AugAssign"}:
                _collect_target(d.get("target"))
            elif kind in {"For", "ForRange"}:
                _collect_target(d.get("target"))
            elif kind == "ForCore":
                _collect_target_plan(d.get("target_plan"))
            for value in d.values():
                _visit(value)

        _visit(stmts)
        return out

    def _mark_mutated_param_from_target(self, target_obj: Any, params: set[str], out: set[str]) -> None:
        """代入ターゲットから、破壊的変更対象の引数名を再帰的に抽出する。"""
        tgt = self.any_to_dict_or_empty(target_obj)
        tkind = self._node_kind_from_dict(tgt)
        if tkind == "Name":
            nm = self.any_to_str(tgt.get("id"))
            if nm in params:
                out.add(nm)
            return
        if tkind == "Subscript":
            base = self.any_to_dict_or_empty(tgt.get("value"))
            if self._node_kind_from_dict(base) == "Name":
                nm = self.any_to_str(base.get("id"))
                if nm in params:
                    out.add(nm)
            else:
                self._mark_mutated_param_from_target(base, params, out)
            return
        if tkind == "Attribute":
            owner = self.any_to_dict_or_empty(tgt.get("value"))
            if self._node_kind_from_dict(owner) == "Name":
                nm = self.any_to_str(owner.get("id"))
                if nm in params:
                    out.add(nm)
            return
        if tkind == "Tuple":
            elems = self.any_dict_get_list(tgt, "elements")
            for elem in elems:
                self._mark_mutated_param_from_target(elem, params, out)

    def _collect_self_method_calls(self, node: Any, out: set[str]) -> None:
        """ノード配下の `self.method(...)` 呼び出し名を再帰収集する。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) > 0:
            if self._node_kind_from_dict(node_dict) == "Call":
                fn = self.any_to_dict_or_empty(node_dict.get("func"))
                if self._node_kind_from_dict(fn) == "Attribute":
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    if self._node_kind_from_dict(owner) == "Name":
                        owner_name = self.any_to_str(owner.get("id"))
                        if owner_name == "self":
                            method_name = self.any_to_str(fn.get("attr"))
                            if method_name != "":
                                out.add(method_name)
            for value in node_dict.values():
                self._collect_self_method_calls(value, out)
            return
        node_list = self.any_to_list(node)
        if len(node_list) > 0:
            for item in node_list:
                self._collect_self_method_calls(item, out)

    def _collect_nonconst_method_names_in_class_body(self, class_body: list[dict[str, Any]]) -> set[str]:
        """class body 内で non-const 扱いすべき method 名を closure で返す。"""
        methods: dict[str, tuple[list[dict[str, Any]], list[str]]] = {}
        direct_nonconst: set[str] = set()
        call_graph: dict[str, set[str]] = {}
        for method_stmt in class_body:
            if self._node_kind_from_dict(method_stmt) != "FunctionDef":
                continue
            method_name = self.any_to_str(method_stmt.get("name"))
            if method_name in {"", "__init__", "__del__"}:
                continue
            arg_order = [name for name in self.any_to_str_list(method_stmt.get("arg_order")) if name != ""]
            if "self" not in arg_order:
                continue
            body_stmts = self._dict_stmt_list(method_stmt.get("body"))
            methods[method_name] = (body_stmts, arg_order)
            if "self" in self._collect_mutated_params(body_stmts, arg_order):
                direct_nonconst.add(method_name)
            callees: set[str] = set()
            self._collect_self_method_calls(body_stmts, callees)
            if method_name in callees:
                callees.remove(method_name)
            call_graph[method_name] = callees
        nonconst = set(direct_nonconst)
        changed = True
        while changed:
            changed = False
            for method_name, callees in call_graph.items():
                if method_name in nonconst:
                    continue
                if any(callee in nonconst for callee in callees):
                    nonconst.add(method_name)
                    changed = True
        return nonconst

    def _collect_mutated_params_from_stmt(self, stmt: dict[str, Any], params: set[str], out: set[str]) -> None:
        """1文から「破壊的に使われる引数名」を再帰的に収集する。"""
        kind = self._node_kind_from_dict(stmt)

        if kind in {"Assign", "AnnAssign", "AugAssign"}:
            self._mark_mutated_param_from_target(stmt.get("target"), params, out)
        elif kind == "Swap":
            self._mark_mutated_param_from_target(stmt.get("lhs"), params, out)
            self._mark_mutated_param_from_target(stmt.get("rhs"), params, out)
        elif kind == "Expr":
            call = self.any_to_dict_or_empty(stmt.get("value"))
            if self._node_kind_from_dict(call) == "Call":
                fn = self.any_to_dict_or_empty(call.get("func"))
                if self._node_kind_from_dict(fn) == "Attribute":
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    attr = self.any_to_str(fn.get("attr"))
                    mutating_attrs = {
                        "append",
                        "extend",
                        "insert",
                        "pop",
                        "clear",
                        "remove",
                        "discard",
                        "add",
                        "update",
                        "setdefault",
                        "sort",
                        "reverse",
                        "mkdir",
                        "write",
                        "write_text",
                        "close",
                    }
                    if attr in mutating_attrs:
                        self._mark_mutated_param_from_target(owner, params, out)
                elif self._node_kind_from_dict(fn) == "Name":
                    fn_name = self.any_to_str(fn.get("id"))
                    mutated_positions = getattr(self, "function_mutated_param_positions", {}).get(fn_name, set())
                    if isinstance(mutated_positions, set) and len(mutated_positions) > 0:
                        call_args = self.any_to_list(call.get("args"))
                        for idx, arg in enumerate(call_args):
                            if idx in mutated_positions:
                                self._mark_mutated_param_from_target(arg, params, out)

        if kind == "If":
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return
        if kind in {"While", "For", "ForCore"}:
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return
        if kind == "Try":
            for s in self._dict_stmt_list(stmt.get("body")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for h in self._dict_stmt_list(stmt.get("handlers")):
                for s in self._dict_stmt_list(h.get("body")):
                    self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("orelse")):
                self._collect_mutated_params_from_stmt(s, params, out)
            for s in self._dict_stmt_list(stmt.get("finalbody")):
                self._collect_mutated_params_from_stmt(s, params, out)
            return

    def _collect_mutated_params(self, body_stmts: list[dict[str, Any]], arg_names: list[str]) -> set[str]:
        """関数本体から `mutable` 扱いすべき引数名を推定する。"""
        params: set[str] = set()
        for arg_name in arg_names:
            params.add(arg_name)
        out: set[str] = set()
        for st in body_stmts:
            self._collect_mutated_params_from_stmt(st, params, out)
        return out

    def _node_contains_call_name(self, node: Any, fn_name: str) -> bool:
        """ノード配下に `fn_name(...)` 呼び出しが含まれるかを返す。"""
        node_dict = self.any_to_dict_or_empty(node)
        if len(node_dict) > 0:
            if self._node_kind_from_dict(node_dict) == "Call":
                fn = self.any_to_dict_or_empty(node_dict.get("func"))
                if self._node_kind_from_dict(fn) == "Name":
                    if self.any_dict_get_str(fn, "id", "") == fn_name:
                        return True
            for _k, v in node_dict.items():
                if self._node_contains_call_name(v, fn_name):
                    return True
            return False
        node_list = self.any_to_list(node)
        if len(node_list) > 0:
            for item in node_list:
                if self._node_contains_call_name(item, fn_name):
                    return True
        return False

    def _stmt_list_contains_call_name(self, body_stmts: list[dict[str, Any]], fn_name: str) -> bool:
        """文リストに `fn_name(...)` 呼び出しが含まれるかを返す。"""
        for st in body_stmts:
            if self._node_contains_call_name(st, fn_name):
                return True
        return False

"""EAST -> JavaScript transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.hooks.js_hooks import build_js_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter
from pytra.std import json
from pytra.std.pathlib import Path


def js_string_lit(text: str) -> str:
    """JavaScript の文字列リテラルへエスケープ変換する。"""
    out = "\""
    i = 0
    while i < len(text):
        ch = text[i : i + 1]
        if ch == "\\":
            out += "\\\\"
        elif ch == "\"":
            out += "\\\""
        elif ch == "\n":
            out += "\\n"
        elif ch == "\r":
            out += "\\r"
        elif ch == "\t":
            out += "\\t"
        else:
            out += ch
        i += 1
    out += "\""
    return out


def _load_profile_piece(path: Path) -> dict[str, Any]:
    """JSON プロファイル断片を読み込む。失敗時は空 dict。"""
    if not path.exists():
        return {}
    try:
        txt = path.read_text(encoding="utf-8")
        raw = json.loads(txt)
    except Exception:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}


def load_js_profile() -> dict[str, Any]:
    """JavaScript 用 profile を読み込む。"""
    profile_path = Path("src/profiles/js/profile.json")
    if not profile_path.exists():
        this_file = str(__file__)
        src_pos = this_file.rfind("/src/")
        if src_pos >= 0:
            src_root = this_file[: src_pos + 4]
            profile_path = Path(src_root + "/profiles/js/profile.json")
    profile_root = profile_path.parent
    meta = _load_profile_piece(profile_path)
    out: dict[str, Any] = {}
    includes_obj = meta.get("include")
    includes: list[str] = []
    if isinstance(includes_obj, list):
        for item in includes_obj:
            if isinstance(item, str) and item != "":
                includes.append(item)
    i = 0
    while i < len(includes):
        rel = includes[i]
        piece = _load_profile_piece(profile_root / rel)
        for key, val in piece.items():
            out[key] = val
        i += 1
    for key, val in meta.items():
        if key != "include":
            out[key] = val
    return out


def load_js_hooks(profile: dict[str, Any]) -> dict[str, Any]:
    """JavaScript 用 hook を読み込む。"""
    _ = profile
    hooks = build_js_hooks()
    if isinstance(hooks, dict):
        return hooks
    return {}


class JsEmitter(CodeEmitter):
    """EAST を JavaScript ソースへ変換するエミッタ。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        profile = load_js_profile()
        hooks = load_js_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        raw_types = self.any_to_dict_or_empty(profile.get("types"))
        nested_types = self.any_to_dict_or_empty(raw_types.get("types"))
        if len(nested_types) > 0:
            self.type_map = self.any_to_str_dict_or_empty(nested_types)
        else:
            self.type_map = self.any_to_str_dict_or_empty(raw_types)
        operators = self.any_to_dict_or_empty(profile.get("operators"))
        self.bin_ops = self.any_to_str_dict_or_empty(operators.get("binop"))
        self.cmp_ops = self.any_to_str_dict_or_empty(operators.get("cmp"))
        self.aug_ops = self.any_to_str_dict_or_empty(operators.get("aug"))
        syntax = self.any_to_dict_or_empty(profile.get("syntax"))
        identifiers = self.any_to_dict_or_empty(syntax.get("identifiers"))
        self.reserved_words: set[str] = set(self.any_to_str_list(identifiers.get("reserved_words")))
        self.rename_prefix = self.any_to_str(identifiers.get("rename_prefix"))
        if self.rename_prefix == "":
            self.rename_prefix = "py_"
        self.declared_var_types: dict[str, str] = {}
        self.current_class_name: str = ""
        self.class_names: set[str] = set()
        self.in_method_scope: bool = False
        self.browser_symbol_aliases: dict[str, str] = {}
        self.browser_module_aliases: dict[str, str] = {}

    def _safe_name(self, name: str) -> str:
        return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, {})

    def _is_browser_module(self, module_id: str) -> bool:
        """browser 外部参照モジュールかを判定する。"""
        return module_id == "browser" or module_id.startswith("browser.")

    def _module_id_to_js_path(self, module_id: str) -> str:
        """Python 形式モジュール名を JS import パスへ変換する。"""
        if module_id == "":
            return ""
        return "./" + module_id.replace(".", "/") + ".js"

    def _collect_import_statements(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """import 情報を JavaScript import 文へ変換する。"""
        out: list[str] = []
        seen: set[str] = set()
        self.browser_symbol_aliases = {}
        self.browser_module_aliases = {}

        def _add(line: str) -> None:
            if line == "" or line in seen:
                return
            seen.add(line)
            out.append(line)

        bindings = self.any_to_dict_list(meta.get("import_bindings"))
        if len(bindings) > 0:
            i = 0
            while i < len(bindings):
                ent = bindings[i]
                binding_kind = self.any_to_str(ent.get("binding_kind"))
                module_id = self.any_to_str(ent.get("module_id"))
                local_name = self.any_to_str(ent.get("local_name"))
                export_name = self.any_to_str(ent.get("export_name"))
                if module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    i += 1
                    continue
                if self._is_browser_module(module_id):
                    if binding_kind == "symbol" and local_name != "" and export_name != "" and local_name != export_name:
                        self.browser_symbol_aliases[local_name] = export_name
                    if binding_kind == "module" and local_name != "":
                        self.browser_module_aliases[local_name] = module_id
                    i += 1
                    continue
                module_path = self._module_id_to_js_path(module_id)
                if module_path == "":
                    i += 1
                    continue
                if binding_kind == "module" and local_name != "":
                    leaf = self._last_dotted_name(module_id)
                    alias = local_name if local_name != leaf else leaf
                    _add("import * as " + self._safe_name(alias) + " from " + js_string_lit(module_path) + ";")
                elif binding_kind == "symbol" and export_name != "":
                    if local_name != "" and local_name != export_name:
                        _add(
                            "import { "
                            + export_name
                            + " as "
                            + self._safe_name(local_name)
                            + " } from "
                            + js_string_lit(module_path)
                            + ";"
                        )
                    else:
                        _add("import { " + export_name + " } from " + js_string_lit(module_path) + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                        continue
                    if self._is_browser_module(module_id):
                        asname = self.any_to_str(ent.get("asname"))
                        if asname != "":
                            self.browser_module_aliases[asname] = module_id
                        continue
                    module_path = self._module_id_to_js_path(module_id)
                    if module_path == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    leaf = self._last_dotted_name(module_id)
                    alias = asname if asname != "" else leaf
                    _add("import * as " + self._safe_name(alias) + " from " + js_string_lit(module_path) + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing"}:
                    continue
                for ent in self._dict_stmt_list(stmt.get("names")):
                    name = self.any_to_str(ent.get("name"))
                    asname = self.any_to_str(ent.get("asname"))
                    if name == "":
                        continue
                    if self._is_browser_module(module_id):
                        if asname != "" and asname != name:
                            self.browser_symbol_aliases[asname] = name
                        continue
                    module_path = self._module_id_to_js_path(module_id)
                    if module_path == "":
                        continue
                    if asname != "" and asname != name:
                        _add("import { " + name + " as " + self._safe_name(asname) + " } from " + js_string_lit(module_path) + ";")
                    else:
                        _add("import { " + name + " } from " + js_string_lit(module_path) + ";")
        return out

    def transpile(self) -> str:
        """モジュール全体を JavaScript ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}
        self.in_method_scope = False

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()
        import_lines = self._collect_import_statements(body, meta)
        for line in import_lines:
            self.emit(line)
        if len(import_lines) > 0:
            self.emit("")

        self.class_names = set()
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") == "ClassDef":
                nm = self.any_to_str(stmt.get("name"))
                if nm != "":
                    self.class_names.add(nm)

        top_level_stmts: list[dict[str, Any]] = []
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                continue
            if kind == "FunctionDef":
                self.emit_leading_comments(stmt)
                self._emit_function(stmt, in_class=None)
                self.emit("")
                continue
            if kind == "ClassDef":
                self.emit_leading_comments(stmt)
                self._emit_class(stmt)
                self.emit("")
                continue
            top_level_stmts.append(stmt)

        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        if len(main_guard_body) > 0:
            self.emit("// __main__ guard")
            self.emit_stmt_list(main_guard_body)
        elif len(top_level_stmts) > 0:
            self.emit_stmt_list(top_level_stmts)
        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を JavaScript class として出力する。"""
        class_name = self._safe_name(self.any_to_str(stmt.get("name")))
        self.current_class_name = class_name
        self.emit("class " + class_name + " {")
        self.indent += 1
        members = self._dict_stmt_list(stmt.get("body"))

        emitted_ctor = False
        for member in members:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                self._emit_function(member, in_class=class_name)
                emitted_ctor = True
                break
        if not emitted_ctor:
            self.emit("constructor() {")
            self.emit("}")

        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            self.emit("")
            self._emit_function(member, in_class=class_name)

        self.indent -= 1
        self.emit("}")
        self.current_class_name = ""

    def _emit_function(self, fn: dict[str, Any], in_class: str | None) -> None:
        """FunctionDef を JavaScript 関数/メソッドとして出力する。"""
        fn_name_raw = self.any_to_str(fn.get("name"))
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        args: list[str] = []
        scope_names: set[str] = set()
        self.in_method_scope = in_class is not None

        if in_class is not None:
            method_name = "constructor" if fn_name_raw == "__init__" else self._safe_name(fn_name_raw)
            if len(arg_order) > 0 and arg_order[0] == "self":
                arg_order = arg_order[1:]
            for arg_name in arg_order:
                args.append(self._safe_name(arg_name))
                scope_names.add(arg_name)
            self.emit(method_name + "(" + ", ".join(args) + ") {")
        else:
            fn_name = self._safe_name(fn_name_raw)
            for arg_name in arg_order:
                args.append(self._safe_name(arg_name))
                scope_names.add(arg_name)
            self.emit("function " + fn_name + "(" + ", ".join(args) + ") {")

        body = self._dict_stmt_list(fn.get("body"))
        self.emit_scoped_stmt_list(body, scope_names)
        self.emit("}")
        self.in_method_scope = False

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを JavaScript へ出力する。"""
        self.emit_leading_comments(stmt)
        if self.hook_on_emit_stmt(stmt) is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        if self.hook_on_emit_stmt_kind(kind, stmt) is True:
            return

        if kind == "Pass":
            self.emit(self.syntax_text("pass_stmt", "// pass"))
            return
        if kind == "Break":
            self.emit(self.syntax_text("break_stmt", "break;"))
            return
        if kind == "Continue":
            self.emit(self.syntax_text("continue_stmt", "continue;"))
            return
        if kind == "Expr":
            expr_txt = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("expr_stmt", "{expr};", {"expr": expr_txt}))
            return
        if kind == "Return":
            if stmt.get("value") is None:
                self.emit(self.syntax_text("return_void", "return;"))
            else:
                value = self.render_expr(stmt.get("value"))
                self.emit(self.syntax_line("return_value", "return {value};", {"value": value}))
            return
        if kind == "Raise":
            exc = stmt.get("exc")
            if exc is None:
                self.emit("throw new Error(\"raise\");")
            else:
                self.emit("throw " + self.render_expr(exc) + ";")
            return
        if kind == "Try":
            self._emit_try(stmt)
            return
        if kind == "AnnAssign":
            self._emit_annassign(stmt)
            return
        if kind == "Assign":
            self._emit_assign(stmt)
            return
        if kind == "AugAssign":
            self._emit_augassign(stmt)
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
            return
        if kind == "For":
            self._emit_for(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            return
        self.emit("// unsupported stmt: " + kind)

    def _emit_try(self, stmt: dict[str, Any]) -> None:
        """Try/Except/Finally を JavaScript の try/catch/finally へ変換する。"""
        self.emit("try {")
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        handlers = self._dict_stmt_list(stmt.get("handlers"))
        finalbody = self._dict_stmt_list(stmt.get("finalbody"))
        if len(handlers) > 0:
            first = handlers[0]
            ex_name = self.any_to_str(first.get("name"))
            if ex_name == "":
                ex_name = "ex"
            ex_name_safe = self._safe_name(ex_name)
            self.emit("} catch (" + ex_name_safe + ") {")
            self.emit_scoped_stmt_list(self._dict_stmt_list(first.get("body")), set([ex_name]))
            if len(handlers) > 1:
                self.emit("    // unsupported: additional except handlers are ignored")
        if len(finalbody) > 0:
            if len(handlers) == 0:
                self.emit("} finally {")
            else:
                self.emit("} finally {")
            self.emit_scoped_stmt_list(finalbody, set())
        self.emit("}")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit(self.syntax_line("if_open", "if ({cond}) {", {"cond": cond}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        orelse = self._dict_stmt_list(stmt.get("orelse"))
        if len(orelse) == 0:
            self.emit(self.syntax_text("block_close", "}"))
            return
        self.emit(self.syntax_text("else_open", "} else {"))
        self.emit_scoped_stmt_list(orelse, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit(self.syntax_line("while_open", "while ({cond}) {", {"cond": cond}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, set())
        self.emit(self.syntax_text("block_close", "}"))

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_i")
        target = self._safe_name(target_name)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))
        cond = target + " < " + stop
        inc = target + " += " + step
        if range_mode == "descending":
            cond = target + " > " + stop
        self.emit("for (let " + target + " = " + start + "; " + cond + "; " + inc + ") {")
        body = self._dict_stmt_list(stmt.get("body"))
        scope = set()
        scope.add(target_name)
        self.emit_scoped_stmt_list(body, scope)
        self.emit("}")

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        target_text = "_it"
        scope: set[str] = set()
        if target_kind == "Tuple":
            items = self.tuple_elements(target_node)
            names: list[str] = []
            for item in items:
                d = self.any_to_dict_or_empty(item)
                if self.any_dict_get_str(d, "kind", "") == "Name":
                    nm = self.any_dict_get_str(d, "id", "_")
                    names.append(self._safe_name(nm))
                    scope.add(nm)
                else:
                    names.append("_")
            target_text = "[" + ", ".join(names) + "]"
        else:
            target_name = self.any_dict_get_str(target_node, "id", "_it")
            target_text = self._safe_name(target_name)
            scope.add(target_name)

        iter_node = stmt.get("iter")
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        if iter_type.startswith("dict[") and target_kind != "Tuple":
            iter_expr = "Object.keys(" + iter_expr + ")"
        self.emit(self.syntax_line("for_open", "for (const {target} of {iter}) {", {"target": target_text, "iter": iter_expr}))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_stmt_list(body, scope)
        self.emit("}")

    def _emit_annassign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if self.any_dict_get_str(target, "kind", "") != "Name":
            t = self.render_expr(target)
            v = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("annassign_assign", "{target} = {value};", {"target": t, "value": v}))
            return
        name_raw = self.any_dict_get_str(target, "id", "_")
        name = self._safe_name(name_raw)
        value_obj = stmt.get("value")
        declare = self.any_dict_get_bool(stmt, "declare", True)
        if declare and not self.is_declared(name_raw):
            self.declare_in_current_scope(name_raw)
            if value_obj is None:
                self.emit("let " + name + ";")
            else:
                self.emit("let " + name + " = " + self.render_expr(value_obj) + ";")
            return
        if value_obj is not None:
            self.emit(name + " = " + self.render_expr(value_obj) + ";")

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        if len(target) == 0:
            targets = self._dict_stmt_list(stmt.get("targets"))
            if len(targets) > 0:
                target = targets[0]
        value = self.render_expr(stmt.get("value"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        if target_kind == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            declare = self.any_dict_get_bool(stmt, "declare", False)
            if declare and not self.is_declared(name_raw):
                self.declare_in_current_scope(name_raw)
                self.emit("let " + name + " = " + value + ";")
            else:
                self.emit(name + " = " + value + ";")
            return
        if target_kind == "Tuple":
            names = self.tuple_elements(target)
            if len(names) == 2:
                a = self.render_expr(names[0])
                b = self.render_expr(names[1])
                tmp = self.next_tmp("__tmp")
                self.emit("const " + tmp + " = " + value + ";")
                self.emit(a + " = " + tmp + "[0];")
                self.emit(b + " = " + tmp + "[1];")
                return
        self.emit(self.render_expr(target) + " = " + value + ";")

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target = self.render_expr(stmt.get("target"))
        value = self.render_expr(stmt.get("value"))
        op = self.any_to_str(stmt.get("op"))
        mapped = self.aug_ops.get(op, "+=")
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left = self.render_expr(expr.get("left"))
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        if len(ops) == 0 or len(comps) == 0:
            return "false"
        terms: list[str] = []
        cur_left = left
        i = 0
        while i < len(ops) and i < len(comps):
            op = ops[i]
            right = self.render_expr(comps[i])
            op_txt = self.cmp_ops.get(op, "===")
            terms.append("(" + cur_left + " " + op_txt + " " + right + ")")
            cur_left = right
            i += 1
        if len(terms) == 1:
            return terms[0]
        return "(" + " && ".join(terms) + ")"

    def _render_name_call(self, fn_name_raw: str, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """組み込み関数呼び出しを JavaScript 式へ変換する。"""
        fn_name = self._safe_name(fn_name_raw)
        if fn_name_raw == "print":
            return "console.log(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "len" and len(rendered_args) == 1:
            return "(" + rendered_args[0] + ").length"
        if fn_name_raw == "str" and len(rendered_args) == 1:
            return "String(" + rendered_args[0] + ")"
        if fn_name_raw == "int" and len(rendered_args) == 1:
            return "Math.trunc(Number(" + rendered_args[0] + "))"
        if fn_name_raw == "float" and len(rendered_args) == 1:
            return "Number(" + rendered_args[0] + ")"
        if fn_name_raw == "bool" and len(rendered_args) == 1:
            return "Boolean(" + rendered_args[0] + ")"
        if fn_name_raw == "Exception":
            if len(rendered_args) >= 1:
                return "new Error(" + rendered_args[0] + ")"
            return "new Error(\"Exception\")"
        if fn_name_raw in self.class_names:
            return "new " + fn_name_raw + "(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "enumerate" and len(rendered_args) == 1:
            arg0 = rendered_args[0]
            return arg0 + ".map((__v, __i) => [__i, __v])"
        if fn_name_raw == "enumerate" and len(rendered_args) >= 2:
            arg0 = rendered_args[0]
            arg1 = rendered_args[1]
            return arg0 + ".map((__v, __i) => [__i + (" + arg1 + "), __v])"
        _ = arg_nodes
        return fn_name + "(" + ", ".join(rendered_args) + ")"

    def _render_attr_call(self, owner_node: dict[str, Any], attr_raw: str, rendered_args: list[str]) -> str:
        """属性呼び出しを JavaScript 式へ変換する。"""
        owner_expr = self.render_expr(owner_node)
        owner_type = self.get_expr_type(owner_node)

        if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
            if attr_raw == "append" and len(rendered_args) == 1:
                return owner_expr + ".push(" + rendered_args[0] + ")"
            if attr_raw == "clear" and len(rendered_args) == 0:
                return owner_expr + ".length = 0"
            if attr_raw == "pop" and len(rendered_args) == 0:
                return owner_expr + ".pop()"
            if attr_raw == "pop" and len(rendered_args) >= 1:
                return owner_expr + ".splice(" + rendered_args[0] + ", 1)[0]"

        if owner_type.startswith("dict["):
            if attr_raw == "get":
                if len(rendered_args) == 1:
                    k = rendered_args[0]
                    return "(Object.prototype.hasOwnProperty.call(" + owner_expr + ", " + k + ") ? " + owner_expr + "[" + k + "] : null)"
                if len(rendered_args) >= 2:
                    k = rendered_args[0]
                    d = rendered_args[1]
                    return "(Object.prototype.hasOwnProperty.call(" + owner_expr + ", " + k + ") ? " + owner_expr + "[" + k + "] : " + d + ")"
            if attr_raw == "items" and len(rendered_args) == 0:
                return "Object.entries(" + owner_expr + ")"
            if attr_raw == "keys" and len(rendered_args) == 0:
                return "Object.keys(" + owner_expr + ")"
            if attr_raw == "values" and len(rendered_args) == 0:
                return "Object.values(" + owner_expr + ")"

        if attr_raw == "items" and len(rendered_args) == 0:
            return "Object.entries(" + owner_expr + ")"
        if attr_raw == "keys" and len(rendered_args) == 0:
            return "Object.keys(" + owner_expr + ")"
        if attr_raw == "values" and len(rendered_args) == 0:
            return "Object.values(" + owner_expr + ")"

        attr = self._safe_name(attr_raw)
        return owner_expr + "." + attr + "(" + ", ".join(rendered_args) + ")"

    def _render_call(self, expr: dict[str, Any]) -> str:
        parts = self.unpack_prepared_call_parts(self._prepare_call_parts(expr))
        fn_node = self.any_to_dict_or_empty(parts.get("fn"))
        fn_kind = self.any_dict_get_str(fn_node, "kind", "")
        args = self.any_to_list(parts.get("args"))
        arg_nodes = self.any_to_list(parts.get("arg_nodes"))

        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(self.any_to_str(args[i]))
            i += 1

        if fn_kind == "Name":
            fn_name_raw = self.any_dict_get_str(fn_node, "id", "")
            return self._render_name_call(fn_name_raw, rendered_args, arg_nodes)
        if fn_kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            attr_raw = self.any_dict_get_str(fn_node, "attr", "")
            return self._render_attr_call(owner_node, attr_raw, rendered_args)
        fn_expr = self.render_expr(fn_node)
        return fn_expr + "(" + ", ".join(rendered_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを JavaScript へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "undefined"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            if name in self.browser_symbol_aliases:
                return self.browser_symbol_aliases[name]
            if name == "self" and self.in_method_scope:
                return "this"
            return self._safe_name(name)
        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "null", "null")
            if tag == "1":
                return non_str
            val = self.any_to_str(expr_d.get("value"))
            return js_string_lit(val)
        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner_expr = self.render_expr(owner_node)
            attr = self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))
            return owner_expr + "." + attr
        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            operand = self.render_expr(expr_d.get("operand"))
            if op == "USub":
                return "(-" + operand + ")"
            if op == "Not":
                return "(!" + operand + ")"
            return operand
        if kind == "BinOp":
            op = self.any_to_str(expr_d.get("op"))
            left_node = self.any_to_dict_or_empty(expr_d.get("left"))
            right_node = self.any_to_dict_or_empty(expr_d.get("right"))
            left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, op, is_right=False)
            right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, op, is_right=True)
            custom = self.hook_on_render_binop(expr_d, left, right)
            if custom != "":
                return custom
            if op == "FloorDiv":
                return "Math.floor((" + left + ") / (" + right + "))"
            mapped = self.bin_ops.get(op, "+")
            return "(" + left + " " + mapped + " " + right + ")"
        if kind == "Compare":
            return self._render_compare(expr_d)
        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_common(vals, op, and_token="&&", or_token="||", empty_literal="false")
        if kind == "Call":
            hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if hook != "":
                return hook
            return self._render_call(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        if kind == "List":
            elts = self.any_to_list(expr_d.get("elts"))
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            return "[" + ", ".join(rendered) + "]"
        if kind == "Tuple":
            elts = self.tuple_elements(expr_d)
            rendered = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            return "[" + ", ".join(rendered) + "]"
        if kind == "Dict":
            entries = self.any_to_list(expr_d.get("entries"))
            parts: list[str] = []
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_node = self.any_to_dict_or_empty(ent.get("key"))
                val_node = ent.get("value")
                key_kind = self.any_dict_get_str(key_node, "kind", "")
                if key_kind == "Constant":
                    key_val = self.any_to_str(key_node.get("value"))
                    parts.append(js_string_lit(key_val) + ": " + self.render_expr(val_node))
                else:
                    key_expr = self.render_expr(key_node)
                    parts.append("[" + key_expr + "]: " + self.render_expr(val_node))
                i += 1
            return "({" + ", ".join(parts) + "})"
        if kind == "Subscript":
            owner = self.render_expr(expr_d.get("value"))
            idx = self.render_expr(expr_d.get("slice"))
            return owner + "[" + idx + "]"
        if kind == "Lambda":
            args_obj = self.any_to_dict_or_empty(expr_d.get("args"))
            args = self.any_to_list(args_obj.get("args"))
            arg_names: list[str] = []
            for arg in args:
                ad = self.any_to_dict_or_empty(arg)
                arg_names.append(self._safe_name(self.any_to_str(ad.get("arg"))))
            body = self.render_expr(expr_d.get("body"))
            return "(" + ", ".join(arg_names) + ") => " + body

        hook_complex = self.hook_on_render_expr_complex(expr_d)
        if hook_complex != "":
            return hook_complex
        return self.any_to_str(expr_d.get("repr"))

    def render_cond(self, expr: Any) -> str:
        """条件式向け描画（シーケンスを真偽値へ寄せる）。"""
        node = self.any_to_dict_or_empty(expr)
        if len(node) == 0:
            return "false"
        t = self.get_expr_type(expr)
        rendered = self._strip_outer_parens(self.render_expr(expr))
        if rendered == "":
            return "false"
        if t == "bool":
            return rendered
        if t == "str":
            return "(" + rendered + ").length !== 0"
        if t.startswith("list[") or t.startswith("tuple[") or t.startswith("dict[") or t.startswith("set["):
            return "(" + rendered + ").length !== 0"
        return rendered


def transpile_to_js(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを JavaScript コードへ変換する。"""
    emitter = JsEmitter(east_doc)
    return emitter.transpile()

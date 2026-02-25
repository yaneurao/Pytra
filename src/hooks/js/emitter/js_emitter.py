"""EAST -> JavaScript transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.hooks.js_hooks import build_js_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter


def load_js_profile() -> dict[str, Any]:
    """JavaScript 用 profile を読み込む。"""
    return CodeEmitter.load_profile_with_includes(
        "src/profiles/js/profile.json",
        anchor_file=__file__,
    )


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
        self.type_map = self.load_type_map(profile)
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
        self.top_function_names: set[str] = set()

    def _safe_name(self, name: str) -> str:
        return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, {})

    def _is_browser_module(self, module_id: str) -> bool:
        """browser 外部参照モジュールかを判定する。"""
        return module_id == "browser" or module_id.startswith("browser.")

    def _module_id_to_js_path(self, module_id: str) -> str:
        """Python 形式モジュール名を JS import パスへ変換する。"""
        if module_id == "":
            return ""
        runtime_map = {
            "math": "./pytra/std/math.js",
            "time": "./pytra/std/time.js",
            "pathlib": "./pytra/std/pathlib.js",
            "pytra.std.math": "./pytra/std/math.js",
            "pytra.std.time": "./pytra/std/time.js",
            "pytra.std.pathlib": "./pytra/std/pathlib.js",
            "pytra.runtime": "./pytra/runtime.js",
            "pytra.runtime.png": "./pytra/runtime/png.js",
            "pytra.runtime.gif": "./pytra/runtime/gif.js",
            "pytra.utils": "./pytra/utils.js",
            "pytra.utils.png": "./pytra/utils/png.js",
            "pytra.utils.gif": "./pytra/utils/gif.js",
        }
        if module_id in runtime_map:
            return runtime_map[module_id]
        return "./" + module_id.replace(".", "/") + ".js"

    def _walk_node_names(self, node: Any, out: set[str]) -> None:
        """ノード配下の Name.id を収集する（Import/ImportFrom 自身は除外）。"""
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                return
            if kind == "Name":
                name = self.any_to_str(node.get("id"))
                if name != "":
                    out.add(name)
                return
            for key, value in node.items():
                if key == "comments":
                    continue
                self._walk_node_names(value, out)
            return
        if isinstance(node, list):
            for item in node:
                self._walk_node_names(item, out)

    def _collect_used_names(self, body: list[dict[str, Any]], main_guard_body: list[dict[str, Any]]) -> set[str]:
        """モジュール全体で実際に参照される識別子名を収集する。"""
        used: set[str] = set()
        for stmt in body:
            self._walk_node_names(stmt, used)
        for stmt in main_guard_body:
            self._walk_node_names(stmt, used)
        return used

    def _collect_isinstance_type_symbols(self, rhs_node: dict[str, Any], required: set[str]) -> None:
        """isinstance の第2引数から必要な runtime type 定数を抽出する。"""
        kind = self.any_dict_get_str(rhs_node, "kind", "")
        if kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            type_id_map = {
                "str": "PY_TYPE_STRING",
                "list": "PY_TYPE_ARRAY",
                "dict": "PY_TYPE_MAP",
                "set": "PY_TYPE_SET",
                "int": "PY_TYPE_NUMBER",
                "float": "PY_TYPE_NUMBER",
                "bool": "PY_TYPE_BOOL",
                "object": "PY_TYPE_OBJECT",
            }
            symbol = type_id_map.get(rhs_name, "")
            if symbol != "":
                required.add(symbol)
            return
        if kind == "Tuple":
            for elt in self.tuple_elements(rhs_node):
                self._collect_isinstance_type_symbols(self.any_to_dict_or_empty(elt), required)

    def _walk_runtime_requirements(self, node: Any, required: set[str]) -> None:
        """ノード配下から py_runtime シンボル依存を収集する。"""
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind == "ClassDef":
                required.add("PYTRA_TYPE_ID")
                required.add("PY_TYPE_OBJECT")
                required.add("pyRegisterClassType")
            elif kind == "Dict":
                required.add("PYTRA_TYPE_ID")
                required.add("PY_TYPE_MAP")
            elif kind == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Name" and self.any_dict_get_str(fn, "id", "") == "isinstance":
                    required.add("pyIsInstance")
                    args = self.any_to_list(node.get("args"))
                    if len(args) >= 2:
                        self._collect_isinstance_type_symbols(self.any_to_dict_or_empty(args[1]), required)
            for key, value in node.items():
                if key == "comments":
                    continue
                self._walk_runtime_requirements(value, required)
            return
        if isinstance(node, list):
            for item in node:
                self._walk_runtime_requirements(item, required)

    def _collect_runtime_symbols(
        self,
        body: list[dict[str, Any]],
        main_guard_body: list[dict[str, Any]],
    ) -> list[str]:
        """モジュールで必要な py_runtime シンボルを順序付きで返す。"""
        required: set[str] = set()
        for stmt in body:
            self._walk_runtime_requirements(stmt, required)
        for stmt in main_guard_body:
            self._walk_runtime_requirements(stmt, required)
        ordered = [
            "PYTRA_TYPE_ID",
            "PY_TYPE_BOOL",
            "PY_TYPE_NUMBER",
            "PY_TYPE_STRING",
            "PY_TYPE_ARRAY",
            "PY_TYPE_MAP",
            "PY_TYPE_SET",
            "PY_TYPE_OBJECT",
            "pyRegisterClassType",
            "pyIsInstance",
        ]
        out: list[str] = []
        for name in ordered:
            if name in required:
                out.append(name)
        return out

    def _collect_import_statements(
        self,
        body: list[dict[str, Any]],
        meta: dict[str, Any],
        used_names: set[str],
    ) -> list[str]:
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
                    if local_name not in used_names:
                        i += 1
                        continue
                    leaf = self._last_dotted_name(module_id)
                    alias = local_name if local_name != leaf else leaf
                    _add("import * as " + self._safe_name(alias) + " from " + self.quote_string_literal(module_path) + ";")
                elif binding_kind == "symbol" and export_name != "":
                    if local_name == "" or local_name not in used_names:
                        i += 1
                        continue
                    if local_name != "" and local_name != export_name:
                        _add(
                            "import { "
                            + export_name
                            + " as "
                            + self._safe_name(local_name)
                            + " } from "
                            + self.quote_string_literal(module_path)
                            + ";"
                        )
                    else:
                        _add("import { " + export_name + " } from " + self.quote_string_literal(module_path) + ";")
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
                    if alias not in used_names:
                        continue
                    _add("import * as " + self._safe_name(alias) + " from " + self.quote_string_literal(module_path) + ";")
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
                    alias_name = asname if asname != "" else name
                    if alias_name not in used_names:
                        continue
                    if asname != "" and asname != name:
                        _add("import { " + name + " as " + self._safe_name(asname) + " } from " + self.quote_string_literal(module_path) + ";")
                    else:
                        _add("import { " + name + " } from " + self.quote_string_literal(module_path) + ";")
        return out

    def transpile(self) -> str:
        """モジュール全体を JavaScript ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}
        self.in_method_scope = False

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()
        self.top_function_names = set()
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                if fn_name != "":
                    self.top_function_names.add(fn_name)
        used_names = self._collect_used_names(body, main_guard_body)
        runtime_symbols = self._collect_runtime_symbols(body, main_guard_body)
        runtime_import_line = ""
        if len(runtime_symbols) > 0:
            runtime_import_line = "import { " + ", ".join(runtime_symbols) + " } from " + self.quote_string_literal("./pytra/py_runtime.js") + ";"
        import_lines = self._collect_import_statements(body, meta, used_names)
        if runtime_import_line != "":
            self.emit(runtime_import_line)
        for line in import_lines:
            self.emit(line)
        if runtime_import_line != "" or len(import_lines) > 0:
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

        if len(main_guard_body) > 0:
            self.emit("// __main__ guard")
            self.emit_stmt_list(main_guard_body)
        elif len(top_level_stmts) > 0:
            self.emit_stmt_list(top_level_stmts)
        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を JavaScript class として出力する。"""
        class_name_raw = self.any_to_str(stmt.get("name"))
        class_name = self._safe_name(class_name_raw)
        base_raw = self.any_to_str(stmt.get("base"))
        self.current_class_name = class_name
        self.emit("class " + class_name + " {")
        self.indent += 1
        members = self._dict_stmt_list(stmt.get("body"))
        base_type_id = "PY_TYPE_OBJECT"
        if base_raw != "" and base_raw in self.class_names:
            base_type_id = self._safe_name(base_raw) + ".PYTRA_TYPE_ID"
        self.emit("static PYTRA_TYPE_ID = pyRegisterClassType([" + base_type_id + "]);")
        self.emit("")

        field_names: list[str] = []
        for member in members:
            if self.any_dict_get_str(member, "kind", "") == "AnnAssign":
                target = self.any_to_dict_or_empty(member.get("target"))
                if self.any_dict_get_str(target, "kind", "") == "Name":
                    nm = self.any_dict_get_str(target, "id", "")
                    if nm != "":
                        field_names.append(nm)

        emitted_ctor = False
        for member in members:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                self._emit_function(member, in_class=class_name)
                emitted_ctor = True
                break
        if not emitted_ctor:
            ctor_args: list[str] = []
            for field_name in field_names:
                ctor_args.append(self._safe_name(field_name))
            self.emit("constructor(" + ", ".join(ctor_args) + ") {")
            self.emit("this[PYTRA_TYPE_ID] = " + class_name + ".PYTRA_TYPE_ID;")
            for field_name in field_names:
                safe = self._safe_name(field_name)
                self.emit("this." + safe + " = " + safe + ";")
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
            if fn_name_raw == "__init__":
                self.emit("this[PYTRA_TYPE_ID] = " + in_class + ".PYTRA_TYPE_ID;")
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
            expr_d = self.any_to_dict_or_empty(stmt.get("value"))
            if self.any_dict_get_str(expr_d, "kind", "") == "Name":
                expr_name = self.any_dict_get_str(expr_d, "id", "")
                if expr_name == "break":
                    self.emit(self.syntax_text("break_stmt", "break;"))
                    return
                if expr_name == "continue":
                    self.emit(self.syntax_text("continue_stmt", "continue;"))
                    return
                if expr_name == "pass":
                    self.emit(self.syntax_text("pass_stmt", "// pass"))
                    return
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
        self.emit_if_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            self._dict_stmt_list(stmt.get("orelse")),
            if_open_default="if ({cond}) {",
            else_open_default="} else {",
        )

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_while_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            while_open_default="while ({cond}) {",
        )

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_i")
        target = self._safe_name(target_name)
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        start_tmp = self.next_tmp("__start")
        self.emit("const " + start_tmp + " = " + start + ";")
        range_mode = self.any_to_str(stmt.get("range_mode"))
        cond = target + " < " + stop
        inc = target + " += " + step
        if range_mode == "descending":
            cond = target + " > " + stop
        body = self._dict_stmt_list(stmt.get("body"))
        scope = set()
        scope.add(target_name)
        self.emit_scoped_block("for (let " + target + " = " + start_tmp + "; " + cond + "; " + inc + ") {", body, scope)

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
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block(
            self.syntax_line("for_open", "for (const {target} of {iter}) {", {"target": target_text, "iter": iter_expr}),
            body,
            scope,
        )

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
        if self.should_declare_name_binding(stmt, name_raw, True):
            self.declare_in_current_scope(name_raw)
            if value_obj is None:
                self.emit("let " + name + ";")
            else:
                self.emit("let " + name + " = " + self.render_expr(value_obj) + ";")
            return
        if value_obj is not None:
            self.emit(name + " = " + self.render_expr(value_obj) + ";")

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.primary_assign_target(stmt)
        value = self.render_expr(stmt.get("value"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        if target_kind == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            if self.should_declare_name_binding(stmt, name_raw, False):
                self.declare_in_current_scope(name_raw)
                self.emit("let " + name + " = " + value + ";")
            else:
                self.emit(name + " = " + value + ";")
            return
        if target_kind == "Tuple":
            items = self.tuple_elements(target)
            if len(items) == 0:
                return
            tmp_name = self.next_tmp("__tmp")
            self.emit("const " + tmp_name + " = " + value + ";")
            i = 0
            while i < len(items):
                item_node = self.any_to_dict_or_empty(items[i])
                item_expr = tmp_name + "[" + str(i) + "]"
                item_kind = self.any_dict_get_str(item_node, "kind", "")
                if item_kind == "Name":
                    raw = self.any_dict_get_str(item_node, "id", "")
                    if raw != "":
                        safe = self._safe_name(raw)
                        if not self.is_declared(raw):
                            self.declare_in_current_scope(raw)
                            self.emit("let " + safe + " = " + item_expr + ";")
                        else:
                            self.emit(safe + " = " + item_expr + ";")
                    i += 1
                    continue
                self.emit(self.render_expr(item_node) + " = " + item_expr + ";")
                i += 1
            return
        self.emit(self.render_expr(target) + " = " + value + ";")

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target, value, mapped = self.render_augassign_basic(stmt, self.aug_ops, "+=")
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        left = self.render_expr(left_node)
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        right_exprs: list[str] = []
        pair_count = len(ops)
        if len(comps) < pair_count:
            pair_count = len(comps)
        i = 0
        while i < pair_count:
            right_exprs.append(self.render_expr(comps[i]))
            i += 1
        if pair_count == 0:
            return "false"
        terms: list[str] = []
        cur_left = left
        j = 0
        while j < pair_count:
            op = ops[j]
            right = right_exprs[j]
            right_node = self.any_to_dict_or_empty(comps[j])
            right_t = self.get_expr_type(right_node)
            term = ""
            if op == "In" or op == "NotIn":
                if right_t.startswith("dict["):
                    term = "Object.prototype.hasOwnProperty.call(" + right + ", " + cur_left + ")"
                elif right_t.startswith("list[") or right_t in {"bytes", "bytearray", "str"}:
                    term = "(" + right + ").includes(" + cur_left + ")"
                else:
                    term = "(" + cur_left + " in " + right + ")"
                if op == "NotIn":
                    term = "!(" + term + ")"
            else:
                mapped = self.cmp_ops.get(op, "==")
                term = cur_left + " " + mapped + " " + right
            terms.append(term)
            cur_left = right
            j += 1
        if len(terms) == 1:
            return terms[0]
        return " && ".join(terms)

    def _render_isinstance_type_check(self, value_expr: str, type_name: str) -> str:
        """`isinstance(x, T)` の `T` を JS runtime API 判定式へ変換する。"""
        type_id_map = {
            "str": "PY_TYPE_STRING",
            "list": "PY_TYPE_ARRAY",
            "dict": "PY_TYPE_MAP",
            "set": "PY_TYPE_SET",
            "int": "PY_TYPE_NUMBER",
            "float": "PY_TYPE_NUMBER",
            "bool": "PY_TYPE_BOOL",
            "object": "PY_TYPE_OBJECT",
        }
        if type_name in type_id_map:
            return "pyIsInstance(" + value_expr + ", " + type_id_map[type_name] + ")"
        if type_name in self.class_names:
            return "pyIsInstance(" + value_expr + ", " + self._safe_name(type_name) + ".PYTRA_TYPE_ID)"
        return ""

    def _render_isinstance_call(self, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """`isinstance(...)` 呼び出しを JS runtime API へ lower する。"""
        if len(rendered_args) != 2:
            return "false"
        rhs_node = self.any_to_dict_or_empty(arg_nodes[1] if len(arg_nodes) > 1 else None)
        rhs_kind = self.any_dict_get_str(rhs_node, "kind", "")
        if rhs_kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            lowered = self._render_isinstance_type_check(rendered_args[0], rhs_name)
            if lowered != "":
                return lowered
            return "false"
        if rhs_kind == "Tuple":
            checks: list[str] = []
            for elt in self.tuple_elements(rhs_node):
                e_node = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(e_node, "kind", "") != "Name":
                    continue
                e_name = self.any_dict_get_str(e_node, "id", "")
                lowered = self._render_isinstance_type_check(rendered_args[0], e_name)
                if lowered != "":
                    checks.append(lowered)
            if len(checks) > 0:
                return " || ".join(checks)
        return "false"

    def _render_list_repeat(self, base_expr: str, count_expr: str) -> str:
        """Python の list 乗算（`[x] * n`）を JS 式へ lower する。"""
        return (
            "(() => { const __base = (" + base_expr + "); const __n = Math.max(0, Math.trunc(Number(" + count_expr + "))); "
            "let __out = []; for (let __i = 0; __i < __n; __i += 1) { for (const __v of __base) { __out.push(__v); } } return __out; })()"
        )

    def _render_range_expr(self, expr_d: dict[str, Any]) -> str:
        """RangeExpr を JavaScript 配列式へ lower する。"""
        start = self.render_expr(expr_d.get("start"))
        stop = self.render_expr(expr_d.get("stop"))
        step = self.render_expr(expr_d.get("step"))
        return (
            "(() => { const __out = []; const __start = " + start + "; const __stop = " + stop + "; const __step = " + step + "; "
            "if (__step === 0) { return __out; } "
            "if (__step > 0) { for (let __i = __start; __i < __stop; __i += __step) { __out.push(__i); } } "
            "else { for (let __i = __start; __i > __stop; __i += __step) { __out.push(__i); } } "
            "return __out; })()"
        )

    def _render_comp_target(self, target_node: dict[str, Any]) -> str:
        """comprehension target を JS `for..of` で使える形へ変換する。"""
        kind = self.any_dict_get_str(target_node, "kind", "")
        if kind == "Name":
            return self._safe_name(self.any_dict_get_str(target_node, "id", "_"))
        if kind == "Tuple":
            parts: list[str] = []
            for item in self.tuple_elements(target_node):
                item_d = self.any_to_dict_or_empty(item)
                if self.any_dict_get_str(item_d, "kind", "") == "Name":
                    parts.append(self._safe_name(self.any_dict_get_str(item_d, "id", "_")))
                else:
                    parts.append("_")
            return "[" + ", ".join(parts) + "]"
        return "_"

    def _render_list_comp_expr(self, expr_d: dict[str, Any]) -> str:
        """ListComp を JavaScript 配列構築式へ lower する。"""
        generators = self.any_to_list(expr_d.get("generators"))
        if len(generators) == 0:
            return "[]"
        elt_expr = self.render_expr(expr_d.get("elt"))
        lines: list[str] = []
        lines.append("(() => {")
        lines.append("let __out = [];")
        depth = 0
        for gen in generators:
            gen_d = self.any_to_dict_or_empty(gen)
            target_txt = self._render_comp_target(self.any_to_dict_or_empty(gen_d.get("target")))
            iter_expr = self.render_expr(gen_d.get("iter"))
            lines.append("for (const " + target_txt + " of " + iter_expr + ") {")
            depth += 1
            for cond_node in self.any_to_list(gen_d.get("ifs")):
                lines.append("if (!(" + self.render_cond(cond_node) + ")) { continue; }")
        lines.append("__out.push(" + elt_expr + ");")
        while depth > 0:
            lines.append("}")
            depth -= 1
        lines.append("return __out;")
        lines.append("})()")
        return " ".join(lines)

    def _render_name_call(self, fn_name_raw: str, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """組み込み関数呼び出しを JavaScript 式へ変換する。"""
        fn_name = self._safe_name(fn_name_raw)
        if fn_name_raw == "main" and "__pytra_main" in self.top_function_names and "main" not in self.top_function_names:
            fn_name = "__pytra_main"
        if fn_name_raw == "isinstance":
            return self._render_isinstance_call(rendered_args, arg_nodes)
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
        if fn_name_raw == "max" and len(rendered_args) >= 1:
            expr_txt = rendered_args[0]
            i = 1
            while i < len(rendered_args):
                expr_txt = "Math.max(" + expr_txt + ", " + rendered_args[i] + ")"
                i += 1
            return expr_txt
        if fn_name_raw == "min" and len(rendered_args) >= 1:
            expr_txt = rendered_args[0]
            i = 1
            while i < len(rendered_args):
                expr_txt = "Math.min(" + expr_txt + ", " + rendered_args[i] + ")"
                i += 1
            return expr_txt
        if fn_name_raw in {"Exception", "RuntimeError", "ValueError", "TypeError", "KeyError", "IndexError"}:
            if len(rendered_args) >= 1:
                return "new Error(" + rendered_args[0] + ")"
            return "new Error(" + self.quote_string_literal(fn_name_raw) + ")"
        if fn_name_raw in self.class_names:
            return "new " + fn_name_raw + "(" + ", ".join(rendered_args) + ")"
        if fn_name_raw == "enumerate" and len(rendered_args) == 1:
            arg0 = rendered_args[0]
            return arg0 + ".map((__v, __i) => [__i, __v])"
        if fn_name_raw == "enumerate" and len(rendered_args) >= 2:
            arg0 = rendered_args[0]
            arg1 = rendered_args[1]
            return arg0 + ".map((__v, __i) => [__i + (" + arg1 + "), __v])"
        if fn_name_raw == "bytearray":
            if len(rendered_args) == 0:
                return "[]"
            if len(rendered_args) == 1:
                arg0 = rendered_args[0]
                arg0_expr = "(" + arg0 + ")"
                return "(typeof " + arg0_expr + " === \"number\" ? new Array(Math.max(0, Math.trunc(Number(" + arg0_expr + ")))).fill(0) : (Array.isArray(" + arg0_expr + ") ? " + arg0_expr + ".slice() : Array.from(" + arg0_expr + ")))"
            return "[]"
        if fn_name_raw == "bytes":
            if len(rendered_args) == 0:
                return "[]"
            arg0_expr = "(" + rendered_args[0] + ")"
            return "(Array.isArray(" + arg0_expr + ") ? " + arg0_expr + ".slice() : Array.from(" + arg0_expr + "))"
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

        if owner_type == "str":
            if attr_raw == "isdigit" and len(rendered_args) == 0:
                return "((typeof " + owner_expr + " === \"string\") && (" + owner_expr + ").length > 0 && (/^[0-9]+$/.test(" + owner_expr + ")))"
            if attr_raw == "isalpha" and len(rendered_args) == 0:
                return "((typeof " + owner_expr + " === \"string\") && (" + owner_expr + ").length > 0 && (/^[A-Za-z]+$/.test(" + owner_expr + ")))"

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
        parts = self.prepare_call_context(expr)
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

        hook_specific = self.hook_on_render_expr_kind_specific(kind, expr_d)
        if hook_specific != "":
            return hook_specific
        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            if name in self.browser_symbol_aliases:
                return self.browser_symbol_aliases[name]
            if name == "main" and "__pytra_main" in self.top_function_names and "main" not in self.top_function_names:
                return "__pytra_main"
            if name == "self" and self.in_method_scope:
                return "this"
            return self._safe_name(name)
        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "null", "null")
            if tag == "1":
                return non_str
            val = self.any_to_str(expr_d.get("value"))
            return self.quote_string_literal(val)
        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner_expr = self.render_expr(owner_node)
            attr = self._safe_name(self.any_dict_get_str(expr_d, "attr", ""))
            return owner_expr + "." + attr
        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            operand_node = self.any_to_dict_or_empty(expr_d.get("operand"))
            operand = self.render_expr(operand_node)
            operand_kind = self.any_dict_get_str(operand_node, "kind", "")
            simple_operand = operand_kind in {"Name", "Constant", "Call", "Attribute", "Subscript"}
            if op == "USub":
                if simple_operand:
                    return "-" + operand
                return "-(" + operand + ")"
            if op == "Not":
                if simple_operand:
                    return "!" + operand
                return "!(" + operand + ")"
            return operand
        if kind == "BinOp":
            op = self.any_to_str(expr_d.get("op"))
            left_node = self.any_to_dict_or_empty(expr_d.get("left"))
            right_node = self.any_to_dict_or_empty(expr_d.get("right"))
            left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, op, is_right=False)
            right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, op, is_right=True)
            left_kind = self.any_dict_get_str(left_node, "kind", "")
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            custom = self.hook_on_render_binop(expr_d, left, right)
            if custom != "":
                return custom
            if op == "FloorDiv":
                return "Math.floor(" + left + " / " + right + ")"
            if op == "Mult":
                if left_kind == "List" and right_kind != "List":
                    return self._render_list_repeat(left, right)
                if right_kind == "List" and left_kind != "List":
                    return self._render_list_repeat(right, left)
            mapped = self.bin_ops.get(op, "+")
            return left + " " + mapped + " " + right
        if kind == "Compare":
            return self._render_compare(expr_d)
        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_chain_common(
                vals,
                op,
                and_token="&&",
                or_token="||",
                empty_literal="false",
                wrap_each=False,
                wrap_whole=False,
            )
        if kind == "Call":
            hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if hook != "":
                return hook
            return self._render_call(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        if kind == "RangeExpr":
            return self._render_range_expr(expr_d)
        if kind == "ListComp":
            return self._render_list_comp_expr(expr_d)
        if kind == "List":
            elts = self.any_to_list(expr_d.get("elts"))
            if len(elts) == 0:
                elts = self.any_to_list(expr_d.get("elements"))
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
            parts.append("[PYTRA_TYPE_ID]: PY_TYPE_MAP")
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_node = self.any_to_dict_or_empty(ent.get("key"))
                val_node = ent.get("value")
                key_kind = self.any_dict_get_str(key_node, "kind", "")
                if key_kind == "Constant":
                    key_val = self.any_to_str(key_node.get("value"))
                    parts.append(self.quote_string_literal(key_val) + ": " + self.render_expr(val_node))
                else:
                    key_expr = self.render_expr(key_node)
                    parts.append("[" + key_expr + "]: " + self.render_expr(val_node))
                i += 1
            return "({" + ", ".join(parts) + "})"
        if kind == "Subscript":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            owner_t = self.get_expr_type(owner_node)
            idx_node = self.any_to_dict_or_empty(expr_d.get("slice"))
            idx_kind = self.any_dict_get_str(idx_node, "kind", "")
            if idx_kind == "Slice":
                lower_node = idx_node.get("lower")
                upper_node = idx_node.get("upper")
                step_node = idx_node.get("step")
                has_lower = lower_node is not None and len(self.any_to_dict_or_empty(lower_node)) > 0
                has_upper = upper_node is not None and len(self.any_to_dict_or_empty(upper_node)) > 0
                has_step = step_node is not None and len(self.any_to_dict_or_empty(step_node)) > 0
                if has_step:
                    step_expr = self.render_expr(step_node)
                    if has_lower and has_upper:
                        return owner + ".slice(" + self.render_expr(lower_node) + ", " + self.render_expr(upper_node) + ").filter((_, i) => i % (" + step_expr + ") === 0)"
                    if has_lower:
                        return owner + ".slice(" + self.render_expr(lower_node) + ").filter((_, i) => i % (" + step_expr + ") === 0)"
                    if has_upper:
                        return owner + ".slice(0, " + self.render_expr(upper_node) + ").filter((_, i) => i % (" + step_expr + ") === 0)"
                    return owner + ".filter((_, i) => i % (" + step_expr + ") === 0)"
                if has_lower and has_upper:
                    return owner + ".slice(" + self.render_expr(lower_node) + ", " + self.render_expr(upper_node) + ")"
                if has_lower:
                    return owner + ".slice(" + self.render_expr(lower_node) + ")"
                if has_upper:
                    return owner + ".slice(0, " + self.render_expr(upper_node) + ")"
                return owner + ".slice()"
            idx = self.render_expr(idx_node)
            if self.is_indexable_sequence_type(owner_t):
                return owner + "[(((" + idx + ") < 0) ? ((" + owner + ").length + (" + idx + ")) : (" + idx + "))]"
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
        return self.render_truthy_cond_common(
            expr,
            str_non_empty_pattern="({expr}).length !== 0",
            collection_non_empty_pattern="({expr}).length !== 0",
            # JS backend は数値条件をそのまま使う既存挙動を維持する。
            number_non_zero_pattern="{expr}",
        )


def transpile_to_js(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを JavaScript コードへ変換する。"""
    emitter = JsEmitter(east_doc)
    return emitter.transpile()

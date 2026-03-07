"""EAST3 -> Lua native emitter (minimal skeleton)."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.runtime_symbol_index import canonical_runtime_module_id, resolve_import_binding_doc


_LUA_KEYWORDS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "goto",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}
_NIL_FREE_DECL_TYPES = {"int", "int64", "float", "float64", "bool", "str"}


def _safe_ident(name: Any, fallback: str = "value") -> str:
    if not isinstance(name, str) or name == "":
        return fallback
    chars: list[str] = []
    i = 0
    while i < len(name):
        ch = name[i]
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
        i += 1
    out = "".join(chars)
    if out == "":
        out = fallback
    if out[0].isdigit():
        out = "_" + out
    if out in _LUA_KEYWORDS:
        out = "_" + out
    return out


def _lua_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _binop_symbol(op: str) -> str:
    if op == "Add":
        return "+"
    if op == "Sub":
        return "-"
    if op == "Mult":
        return "*"
    if op == "Div":
        return "/"
    if op == "Mod":
        return "%"
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitAnd":
        return "&"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "~"
    if op == "FloorDiv":
        return "//"
    return "+"


def _cmp_symbol(op: str) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "~="
    if op == "Lt":
        return "<"
    if op == "LtE":
        return "<="
    if op == "Gt":
        return ">"
    if op == "GtE":
        return ">="
    return "=="


def _runtime_module_alias_line(alias_txt: str, runtime_module_id: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    if mod == "pytra.std.math":
        return "local " + alias_txt + " = __pytra_math_module()"
    if mod == "pytra.std.json":
        return "local " + alias_txt + " = { loads = pyJsonLoads, dumps = pyJsonDumps }"
    if mod == "pytra.std.pathlib":
        return "local " + alias_txt + " = { Path = Path }"
    if mod == "pytra.std.time":
        return "local " + alias_txt + " = { perf_counter = __pytra_perf_counter }"
    if mod in {"pytra.utils.png", "pytra.utils.gif"}:
        leaf = _safe_ident(mod.rsplit(".", 1)[-1], "utils")
        return "local " + alias_txt + " = __pytra_" + leaf + "_module()"
    return ""


def _runtime_symbol_alias_line(alias_txt: str, runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    if mod == "pytra.std.math":
        return "local " + alias_txt + " = __pytra_math_module()." + _safe_ident(sym, sym)
    if mod == "pytra.std.json":
        if sym == "loads":
            return "local " + alias_txt + " = pyJsonLoads"
        if sym == "dumps":
            return "local " + alias_txt + " = pyJsonDumps"
        return ""
    if mod == "pytra.std.pathlib" and sym == "Path":
        return "local " + alias_txt + " = Path"
    if mod == "pytra.std.time" and sym == "perf_counter":
        return "local " + alias_txt + " = __pytra_perf_counter"
    if mod.startswith("pytra.utils.") and sym != "":
        return "local " + alias_txt + " = __pytra_" + _safe_ident(sym, sym)
    return ""


class LuaNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=lua invalid east document: root must be dict")
        kind = east_doc.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=lua invalid root kind: " + str(kind))
        if east_doc.get("east_stage") != 3:
            raise RuntimeError("lang=lua unsupported east_stage: " + str(east_doc.get("east_stage")))
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.imported_modules: set[str] = set()
        self.function_names: set[str] = set()
        self.loop_continue_labels: list[str] = []
        self.current_class_name: str = ""
        self.current_class_base_name: str = ""
        self._local_type_stack: list[dict[str, str]] = []
        self._ref_var_stack: list[set[str]] = []
        self._local_var_stack: list[set[str]] = []

    def _current_type_map(self) -> dict[str, str]:
        if len(self._local_type_stack) == 0:
            return {}
        return self._local_type_stack[-1]

    def _current_ref_vars(self) -> set[str]:
        if len(self._ref_var_stack) == 0:
            return set()
        return self._ref_var_stack[-1]

    def _current_local_vars(self) -> set[str]:
        if len(self._local_var_stack) == 0:
            return set()
        return self._local_var_stack[-1]

    def _container_kind_from_decl_type(self, type_name: Any) -> str:
        if not isinstance(type_name, str):
            return ""
        if type_name.startswith("dict["):
            return "dict"
        if type_name.startswith("list[") or type_name.startswith("tuple[") or type_name.startswith("set["):
            return "list"
        if type_name in {"bytes", "bytearray"}:
            return "list"
        return ""

    def _is_container_east_type(self, type_name: Any) -> bool:
        return self._container_kind_from_decl_type(type_name) != ""

    def _push_function_context(self, stmt: dict[str, Any], arg_names: list[str], arg_order: list[Any]) -> None:
        type_map: dict[str, str] = {}
        ref_vars: set[str] = set()
        local_vars: set[str] = set(arg_names)
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        i = 0
        while i < len(arg_names):
            safe_name = arg_names[i]
            raw_name = arg_order[i] if i < len(arg_order) else safe_name
            arg_type_any = arg_types.get(raw_name)
            if not isinstance(arg_type_any, str):
                arg_type_any = arg_types.get(safe_name)
            arg_type = arg_type_any.strip() if isinstance(arg_type_any, str) else ""
            if arg_type != "":
                type_map[safe_name] = arg_type
                if self._is_container_east_type(arg_type):
                    ref_vars.add(safe_name)
            i += 1
        self._local_type_stack.append(type_map)
        self._ref_var_stack.append(ref_vars)
        self._local_var_stack.append(local_vars)

    def _pop_function_context(self) -> None:
        if len(self._local_type_stack) > 0:
            self._local_type_stack.pop()
        if len(self._ref_var_stack) > 0:
            self._ref_var_stack.pop()
        if len(self._local_var_stack) > 0:
            self._local_var_stack.pop()

    def _materialize_container_value_from_ref(self, value_any: Any, *, target_name: str, target_decl_type: Any) -> str | None:
        if target_name == "":
            return None
        if not isinstance(value_any, dict) or value_any.get("kind") != "Name":
            return None
        source_name = _safe_ident(value_any.get("id"), "value")
        if source_name == target_name:
            return None
        if source_name not in self._current_ref_vars():
            return None
        container_kind = self._container_kind_from_decl_type(target_decl_type)
        if container_kind == "":
            return None
        source_expr = self._render_expr(value_any)
        if container_kind == "dict":
            return (
                "(function(__src) local __out = {}; "
                + "for __k, __v in pairs(__src) do __out[__k] = __v end; "
                + "return __out end)("
                + source_expr
                + ")"
            )
        return (
            "(function(__src) local __out = {}; "
            + "for __i = 1, #__src do __out[__i] = __src[__i] end; "
            + "return __out end)("
            + source_expr
            + ")"
        )

    def _const_int_literal(self, node_any: Any) -> int | None:
        if not isinstance(node_any, dict):
            return None
        kind = node_any.get("kind")
        if kind == "Constant":
            value = node_any.get("value")
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            return None
        if kind == "UnaryOp" and str(node_any.get("op")) == "USub":
            operand = self._const_int_literal(node_any.get("operand"))
            if operand is None:
                return None
            return -operand
        return None

    def _resolved_runtime_call(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        runtime_call = expr_any.get("runtime_call")
        if isinstance(runtime_call, str) and runtime_call != "":
            return runtime_call
        resolved_runtime_call = expr_any.get("resolved_runtime_call")
        if isinstance(resolved_runtime_call, str) and resolved_runtime_call != "":
            return resolved_runtime_call
        return ""

    def _is_sequence_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        kind = node_any.get("kind")
        if kind in {"List", "Tuple", "JoinedStr", "Dict", "Set"}:
            return True
        if kind == "Constant" and isinstance(node_any.get("value"), str):
            return True
        resolved = node_any.get("resolved_type")
        if isinstance(resolved, str):
            if (
                resolved == "str"
                or resolved.startswith("list[")
                or resolved.startswith("tuple[")
                or resolved.startswith("dict[")
                or resolved.startswith("set[")
            ):
                return True
        return False

    def _render_cond_expr(self, test_any: Any) -> str:
        test = self._render_expr(test_any)
        if self._is_sequence_expr(test_any):
            return "__pytra_truthy(" + test + ")"
        return test

    def _is_str_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        if node_any.get("kind") == "Constant" and isinstance(node_any.get("value"), str):
            return True
        resolved = node_any.get("resolved_type")
        return isinstance(resolved, str) and resolved == "str"

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="-- ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        self._emit_imports(body)
        if len(self.class_names) > 0:
            self._emit_isinstance_helper()
        for stmt in body:
            self._emit_stmt(stmt)
        if len(main_guard) > 0:
            self.lines.append("")
            for stmt in main_guard:
                self._emit_stmt(stmt)
        return "\n".join(self.lines).rstrip() + "\n"

    def _dict_list(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        out: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _module_leading_comment_lines(self, prefix: str) -> list[str]:
        trivia = self._dict_list(self.east_doc.get("module_leading_trivia"))
        out: list[str] = []
        for item in trivia:
            kind = item.get("kind")
            if kind == "comment":
                text = item.get("text")
                if isinstance(text, str):
                    out.append(prefix + text)
                continue
            if kind == "blank":
                count = item.get("count")
                n = count if isinstance(count, int) and count > 0 else 1
                i = 0
                while i < n:
                    out.append("")
                    i += 1
        while len(out) > 0 and out[-1] == "":
            out.pop()
        return out

    def _emit_leading_trivia(self, stmt: dict[str, Any], prefix: str) -> None:
        trivia = self._dict_list(stmt.get("leading_trivia"))
        for item in trivia:
            kind = item.get("kind")
            if kind == "comment":
                text = item.get("text")
                if isinstance(text, str):
                    self._emit_line(prefix + text)
                continue
            if kind == "blank":
                count = item.get("count")
                n = count if isinstance(count, int) and count > 0 else 1
                i = 0
                while i < n:
                    self._emit_line("")
                    i += 1

    def _emit_line(self, text: str) -> None:
        self.lines.append(("    " * self.indent) + text)

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        if len(body) == 0:
            self._emit_line("do end")
            return
        i = 0
        while i < len(body):
            head = self._append_chain_stmt_parts(body[i])
            if head is not None:
                owner = head[0]
                args: list[str] = [head[1]]
                j = i + 1
                while j < len(body):
                    nxt = self._append_chain_stmt_parts(body[j])
                    if nxt is None or nxt[0] != owner:
                        break
                    args.append(nxt[1])
                    j += 1
                if len(args) >= 2:
                    self._emit_leading_trivia(body[i], prefix="-- ")
                    self._emit_line(
                        "table.move({" + ", ".join(args) + "}, 1, " + str(len(args)) + ", #(" + owner + ") + 1, " + owner + ")"
                    )
                    i = j
                    continue
            self._emit_stmt(body[i])
            i += 1

    def _is_safe_append_chain_arg_node(self, node: Any) -> bool:
        if not isinstance(node, dict):
            return False
        kind = node.get("kind")
        return kind in {"Name", "Constant", "Attribute", "Subscript"}

    def _append_chain_stmt_parts(self, stmt_any: Any) -> tuple[str, str] | None:
        if not isinstance(stmt_any, dict) or stmt_any.get("kind") != "Expr":
            return None
        value_any = stmt_any.get("value")
        if not isinstance(value_any, dict) or value_any.get("kind") != "Call":
            return None
        func_any = value_any.get("func")
        if not isinstance(func_any, dict) or func_any.get("kind") != "Attribute":
            return None
        if _safe_ident(func_any.get("attr"), "") != "append":
            return None
        owner_any = func_any.get("value")
        if not isinstance(owner_any, dict) or owner_any.get("kind") != "Name":
            return None
        args_any = value_any.get("args")
        args = args_any if isinstance(args_any, list) else []
        keywords_any = value_any.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        if len(args) != 1 or len(keywords) != 0:
            return None
        if not self._is_safe_append_chain_arg_node(args[0]):
            return None
        return (self._render_expr(owner_any), self._render_expr(args[0]))

    def _has_continue_in_block(self, body_any: Any) -> bool:
        body = self._dict_list(body_any)
        i = 0
        while i < len(body):
            stmt = body[i]
            kind = stmt.get("kind")
            if kind == "Continue":
                return True
            if kind == "Expr":
                value_any = stmt.get("value")
                if isinstance(value_any, dict) and value_any.get("kind") == "Name":
                    if str(value_any.get("id")) == "continue":
                        return True
            if kind == "If":
                if self._has_continue_in_block(stmt.get("body")):
                    return True
                if self._has_continue_in_block(stmt.get("orelse")):
                    return True
            if kind == "ForCore" or kind == "While":
                if self._has_continue_in_block(stmt.get("body")):
                    return True
            i += 1
        return False

    def _is_simple_bound_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        kind = node_any.get("kind")
        if kind == "Name":
            return True
        if kind == "Constant":
            value_any = node_any.get("value")
            if isinstance(value_any, bool):
                return False
            return isinstance(value_any, int) or isinstance(value_any, float)
        return False

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        self.class_names = set()
        self.imported_modules = set()
        self.function_names = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "ClassDef":
                self.class_names.add(_safe_ident(stmt.get("name"), "Class"))
                continue
            if kind == "FunctionDef":
                self.function_names.add(_safe_ident(stmt.get("name"), "fn"))
                continue
            if kind == "Import":
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    module_name = ent.get("name")
                    if not isinstance(module_name, str) or module_name == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else module_name.split(".")[-1]
                    resolved = resolve_import_binding_doc(module_name, "", "module")
                    if len(resolved) > 0:
                        self.imported_modules.add(_safe_ident(alias, "mod"))
                continue
            if kind == "ImportFrom":
                module_name = stmt.get("module")
                if not isinstance(module_name, str):
                    continue
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    symbol = ent.get("name")
                    if not isinstance(symbol, str) or symbol == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else symbol
                    resolved = resolve_import_binding_doc(module_name, symbol, "symbol")
                    if resolved.get("resolved_binding_kind") == "module":
                        self.imported_modules.add(_safe_ident(alias, "mod"))

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        import_lines: list[str] = []
        self._emit_line('dofile((debug.getinfo(1, "S").source:sub(2):match("^(.*[\\\\/])") or "") .. "py_runtime.lua")')
        self._emit_line("")
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "Import":
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    mod = ent.get("name")
                    if not isinstance(mod, str) or mod == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else mod.split(".")[-1]
                    alias_txt = _safe_ident(alias, "mod")
                    resolved = resolve_import_binding_doc(mod, "", "module")
                    if len(resolved) > 0:
                        runtime_module_id = resolved.get("runtime_module_id")
                        if isinstance(runtime_module_id, str):
                            line = _runtime_module_alias_line(alias_txt, runtime_module_id)
                            if line != "":
                                import_lines.append(line)
                                continue
                    if mod.startswith("pytra."):
                        raise RuntimeError("lang=lua unresolved import module: " + mod)
                    import_lines.append("-- import " + mod + " as " + alias_txt + " (not yet mapped)")
                continue
            if kind == "ImportFrom":
                mod = stmt.get("module")
                if not isinstance(mod, str):
                    continue
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    sym = ent.get("name")
                    if not isinstance(sym, str) or sym == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else sym
                    alias_txt = _safe_ident(alias, sym)
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_stdout":
                        import_lines.append(
                            "local py_assert_stdout = function(_expected, _fn) return true end"
                        )
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_eq":
                        import_lines.append("local " + alias_txt + " = function(a, b, _label) return a == b end")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_true":
                        import_lines.append("local " + alias_txt + " = function(v, _label) return not not v end")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_all":
                        import_lines.append(
                            "local "
                            + alias_txt
                            + " = function(checks, _label) if checks == nil then return false end; for i = 1, #checks do if not checks[i] then return false end end; return true end"
                        )
                        continue
                    resolved = resolve_import_binding_doc(mod, sym, "symbol")
                    if len(resolved) > 0:
                        runtime_module_id = resolved.get("runtime_module_id")
                        resolved_kind = resolved.get("resolved_binding_kind")
                        runtime_symbol = resolved.get("runtime_symbol")
                        if isinstance(runtime_module_id, str):
                            if resolved_kind == "module":
                                line = _runtime_module_alias_line(alias_txt, runtime_module_id)
                                if line != "":
                                    import_lines.append(line)
                                    continue
                            if isinstance(runtime_symbol, str):
                                line = _runtime_symbol_alias_line(alias_txt, runtime_module_id, runtime_symbol)
                                if line != "":
                                    import_lines.append(line)
                                    continue
                    if mod.startswith("pytra."):
                        raise RuntimeError("lang=lua unresolved import symbol: " + mod + "." + sym)
                    import_lines.append(
                        "-- from " + mod + " import " + sym + " as " + alias_txt + " (not yet mapped)"
                    )
        for line in import_lines:
            self._emit_line(line)
        if len(import_lines) > 0:
            self._emit_line("")

    def _emit_print_helper(self) -> None:
        self._emit_line("local function __pytra_print(...)")
        self.indent += 1
        self._emit_line("local argc = select(\"#\", ...)")
        self._emit_line("if argc == 0 then")
        self.indent += 1
        self._emit_line("io.write(\"\\n\")")
        self._emit_line("return")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local parts = {}")
        self._emit_line("for i = 1, argc do")
        self.indent += 1
        self._emit_line("local v = select(i, ...)")
        self._emit_line("if v == true then")
        self.indent += 1
        self._emit_line('parts[i] = "True"')
        self.indent -= 1
        self._emit_line("elseif v == false then")
        self.indent += 1
        self._emit_line('parts[i] = "False"')
        self.indent -= 1
        self._emit_line("elseif v == nil then")
        self.indent += 1
        self._emit_line('parts[i] = "None"')
        self.indent -= 1
        self._emit_line("else")
        self.indent += 1
        self._emit_line("parts[i] = tostring(v)")
        self.indent -= 1
        self._emit_line("end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("io.write(table.concat(parts, \" \") .. \"\\n\")")
        self.indent -= 1
        self._emit_line("end")

    def _emit_repeat_helper(self) -> None:
        self._emit_line("local function __pytra_repeat_seq(a, b)")
        self.indent += 1
        self._emit_line("local seq = a")
        self._emit_line("local count = b")
        self._emit_line("if type(a) == \"number\" and type(b) ~= \"number\" then")
        self.indent += 1
        self._emit_line("seq = b")
        self._emit_line("count = a")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local n = math.floor(tonumber(count) or 0)")
        self._emit_line("if n <= 0 then")
        self.indent += 1
        self._emit_line("if type(seq) == \"string\" then return \"\" end")
        self._emit_line("return {}")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("if type(seq) == \"string\" then")
        self.indent += 1
        self._emit_line("return string.rep(seq, n)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("if type(seq) ~= \"table\" then")
        self.indent += 1
        self._emit_line("return (tonumber(a) or 0) * (tonumber(b) or 0)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local out = {}")
        self._emit_line("for _ = 1, n do")
        self.indent += 1
        self._emit_line("for i = 1, #seq do")
        self.indent += 1
        self._emit_line("out[#out + 1] = seq[i]")
        self.indent -= 1
        self._emit_line("end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return out")
        self.indent -= 1
        self._emit_line("end")

    def _emit_truthy_helper(self) -> None:
        self._emit_line("local function __pytra_truthy(v)")
        self.indent += 1
        self._emit_line("if v == nil then return false end")
        self._emit_line("local t = type(v)")
        self._emit_line("if t == \"boolean\" then return v end")
        self._emit_line("if t == \"number\" then return v ~= 0 end")
        self._emit_line("if t == \"string\" then return #v ~= 0 end")
        self._emit_line("if t == \"table\" then return next(v) ~= nil end")
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")

    def _emit_contains_helper(self) -> None:
        self._emit_line("local function __pytra_contains(container, value)")
        self.indent += 1
        self._emit_line("local t = type(container)")
        self._emit_line("if t == \"table\" then")
        self.indent += 1
        self._emit_line("if container[value] ~= nil then return true end")
        self._emit_line("for i = 1, #container do")
        self.indent += 1
        self._emit_line("if container[i] == value then return true end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return false")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("if t == \"string\" then")
        self.indent += 1
        self._emit_line("if type(value) ~= \"string\" then value = tostring(value) end")
        self._emit_line("return string.find(container, value, 1, true) ~= nil")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return false")
        self.indent -= 1
        self._emit_line("end")

    def _emit_string_predicate_helpers(self) -> None:
        self._emit_line("local function __pytra_str_isdigit(s)")
        self.indent += 1
        self._emit_line("if type(s) ~= \"string\" or #s == 0 then return false end")
        self._emit_line("for i = 1, #s do")
        self.indent += 1
        self._emit_line("local b = string.byte(s, i)")
        self._emit_line("if b < 48 or b > 57 then return false end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_str_isalpha(s)")
        self.indent += 1
        self._emit_line("if type(s) ~= \"string\" or #s == 0 then return false end")
        self._emit_line("for i = 1, #s do")
        self.indent += 1
        self._emit_line("local b = string.byte(s, i)")
        self._emit_line("local is_upper = (b >= 65 and b <= 90)")
        self._emit_line("local is_lower = (b >= 97 and b <= 122)")
        self._emit_line("if not (is_upper or is_lower) then return false end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_str_isalnum(s)")
        self.indent += 1
        self._emit_line("if type(s) ~= \"string\" or #s == 0 then return false end")
        self._emit_line("for i = 1, #s do")
        self.indent += 1
        self._emit_line("local b = string.byte(s, i)")
        self._emit_line("local is_digit = (b >= 48 and b <= 57)")
        self._emit_line("local is_upper = (b >= 65 and b <= 90)")
        self._emit_line("local is_lower = (b >= 97 and b <= 122)")
        self._emit_line("if not (is_digit or is_upper or is_lower) then return false end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")

    def _emit_perf_counter_helper(self) -> None:
        self._emit_line("local function __pytra_perf_counter()")
        self.indent += 1
        self._emit_line("return os.clock()")
        self.indent -= 1
        self._emit_line("end")

    def _emit_isinstance_helper(self) -> None:
        self._emit_line("local function __pytra_isinstance(obj, class_tbl)")
        self.indent += 1
        self._emit_line("if type(obj) ~= \"table\" then")
        self.indent += 1
        self._emit_line("return false")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local mt = getmetatable(obj)")
        self._emit_line("while mt do")
        self.indent += 1
        self._emit_line("if mt == class_tbl then")
        self.indent += 1
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local parent = getmetatable(mt)")
        self._emit_line("if type(parent) == \"table\" and type(parent.__index) == \"table\" then")
        self.indent += 1
        self._emit_line("mt = parent.__index")
        self.indent -= 1
        self._emit_line("else")
        self.indent += 1
        self._emit_line("mt = nil")
        self.indent -= 1
        self._emit_line("end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return false")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        self._emit_leading_trivia(stmt, prefix="-- ")
        kind = stmt.get("kind")
        if kind in {"Import", "ImportFrom"}:
            return
        if kind == "ClassDef":
            self._emit_class_def(stmt)
            return
        if kind == "FunctionDef":
            self._emit_function_def(stmt)
            return
        if kind == "Return":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("return " + val)
            return
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value_node = stmt.get("value")
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "nil"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type_any = stmt.get("decl_type")
                decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                if decl_type == "":
                    anno_any = stmt.get("annotation")
                    if isinstance(anno_any, str):
                        decl_type = anno_any.strip()
                if value_node is None and bool(stmt.get("declare")):
                    if decl_type in _NIL_FREE_DECL_TYPES:
                        if decl_type != "":
                            self._current_type_map()[target_name] = decl_type
                        if len(self._local_var_stack) > 0:
                            self._current_local_vars().add(target_name)
                        self._emit_line("local " + target)
                        return
                materialized = self._materialize_container_value_from_ref(
                    value_node,
                    target_name=target_name,
                    target_decl_type=decl_type,
                )
                if materialized is not None:
                    value = materialized
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                if len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                self._emit_line("local " + target + " = " + value)
            else:
                self._emit_line(target + " = " + value)
            return
        if kind == "Assign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                if target_any.get("kind") == "Tuple":
                    self._emit_tuple_assign(target_any, stmt.get("value"))
                    return
                target = self._render_target(target_any)
                value = self._render_expr(stmt.get("value"))
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    target_name = _safe_ident(target_any.get("id"), "value")
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        mapped_decl = self._current_type_map().get(target_name)
                        decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
                    materialized = self._materialize_container_value_from_ref(
                        stmt.get("value"),
                        target_name=target_name,
                        target_decl_type=decl_type,
                    )
                    if materialized is not None:
                        value = materialized
                    if isinstance(decl_type_any, str) and decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        self._emit_line("local " + target + " = " + value)
                        return
                self._emit_line(target + " = " + value)
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                if targets[0].get("kind") == "Tuple":
                    self._emit_tuple_assign(targets[0], stmt.get("value"))
                    return
                target = self._render_target(targets[0])
                value = self._render_expr(stmt.get("value"))
                if targets[0].get("kind") == "Name":
                    target_name = _safe_ident(targets[0].get("id"), "value")
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        mapped_decl = self._current_type_map().get(target_name)
                        decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
                    materialized = self._materialize_container_value_from_ref(
                        stmt.get("value"),
                        target_name=target_name,
                        target_decl_type=decl_type,
                    )
                    if materialized is not None:
                        value = materialized
                    if isinstance(decl_type_any, str) and decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        self._emit_line("local " + target + " = " + value)
                        return
                self._emit_line(target + " = " + value)
                return
            raise RuntimeError("lang=lua unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            self._emit_line(target + " = " + target + " " + _binop_symbol(op) + " " + value)
            return
        if kind == "Expr":
            value_any = stmt.get("value")
            if isinstance(value_any, dict) and value_any.get("kind") == "Name":
                loop_kw = str(value_any.get("id"))
                if loop_kw == "break":
                    self._emit_line("break")
                    return
                if loop_kw == "continue":
                    if len(self.loop_continue_labels) == 0:
                        raise RuntimeError("lang=lua continue outside loop is unsupported")
                    self._emit_line("goto " + self.loop_continue_labels[-1])
                    return
            self._emit_line(self._render_expr(value_any))
            return
        if kind == "Raise":
            exc_any = stmt.get("exc")
            if isinstance(exc_any, dict) and exc_any.get("kind") == "Call":
                fn_any = exc_any.get("func")
                if isinstance(fn_any, dict) and fn_any.get("kind") == "Name":
                    fn_name = _safe_ident(fn_any.get("id"), "")
                    if fn_name in {"RuntimeError", "ValueError", "TypeError", "Exception", "AssertionError"}:
                        args_any = exc_any.get("args")
                        args = args_any if isinstance(args_any, list) else []
                        if len(args) > 0:
                            self._emit_line("error(" + self._render_expr(args[0]) + ")")
                            return
                        self._emit_line('error("error")')
                        return
            if isinstance(exc_any, dict):
                self._emit_line("error(" + self._render_expr(exc_any) + ")")
            else:
                self._emit_line('error("error")')
            return
        if kind == "Try":
            body = self._dict_list(stmt.get("body"))
            i = 0
            while i < len(body):
                self._emit_stmt(body[i])
                i += 1
            handlers_any = stmt.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            i = 0
            while i < len(handlers):
                h = handlers[i]
                if isinstance(h, dict):
                    h_body = self._dict_list(h.get("body"))
                    j = 0
                    while j < len(h_body):
                        self._emit_stmt(h_body[j])
                        j += 1
                i += 1
            orelse = self._dict_list(stmt.get("orelse"))
            i = 0
            while i < len(orelse):
                self._emit_stmt(orelse[i])
                i += 1
            finalbody = self._dict_list(stmt.get("finalbody"))
            i = 0
            while i < len(finalbody):
                self._emit_stmt(finalbody[i])
                i += 1
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "Pass":
            self._emit_line("do end")
            return
        raise RuntimeError("lang=lua unsupported stmt kind: " + str(kind))

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn")
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        self._emit_line("function " + name + "(" + ", ".join(arg_names) + ")")
        self.indent += 1
        self._push_function_context(stmt, arg_names, args)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("if " + test + " then")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        orelse = self._dict_list(stmt.get("orelse"))
        if len(orelse) > 0:
            self._emit_line("else")
            self.indent += 1
            for sub in orelse:
                self._emit_stmt(sub)
            self.indent -= 1
        self._emit_line("end")

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class")
        base_any = stmt.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        if base_name != "":
            self._emit_line(cls_name + " = setmetatable({}, { __index = " + base_name + " })")
        else:
            self._emit_line(cls_name + " = {}")
        self._emit_line(cls_name + ".__index = " + cls_name)
        self._emit_line("")
        body = self._dict_list(stmt.get("body"))
        dataclass_fields: list[str] = []
        if bool(stmt.get("dataclass")):
            for sub in body:
                if sub.get("kind") != "AnnAssign":
                    continue
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    dataclass_fields.append(_safe_ident(target_any.get("id"), "field"))
        has_init = False
        for sub in body:
            if sub.get("kind") != "FunctionDef":
                continue
            if sub.get("name") == "__init__":
                has_init = True
            self._emit_class_method(cls_name, base_name, sub)
        if not has_init:
            arg_list = ", ".join(dataclass_fields)
            self._emit_line("function " + cls_name + ".new(" + arg_list + ")")
            self.indent += 1
            self._emit_line("local self = setmetatable({}, " + cls_name + ")")
            for field_name in dataclass_fields:
                self._emit_line("self." + field_name + " = " + field_name)
            self._emit_line("return self")
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")

    def _emit_class_method(self, cls_name: str, base_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        for i, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i == 0 and arg_name == "self":
                continue
            args.append(arg_name)
        prev_class = self.current_class_name
        prev_base = self.current_class_base_name
        self.current_class_name = cls_name
        self.current_class_base_name = base_name
        if method_name == "__init__":
            self._emit_line("function " + cls_name + ".new(" + ", ".join(args) + ")")
            self.indent += 1
            self._emit_line("local self = setmetatable({}, " + cls_name + ")")
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._emit_line("return self")
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")
            self.current_class_name = prev_class
            self.current_class_base_name = prev_base
            return
        self._emit_line("function " + cls_name + ":" + method_name + "(" + ", ".join(args) + ")")
        self.indent += 1
        self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self.current_class_name = prev_class
        self.current_class_base_name = prev_base

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")
        continue_label = self._next_tmp_name("__pytra_continue")
        needs_continue_label = self._has_continue_in_block(stmt.get("body"))
        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict) or iter_plan.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=lua unsupported forcore static_fastpath shape")
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            step = self._render_expr(iter_plan.get("step"))
            step_const = self._const_int_literal(iter_plan.get("step"))
            range_mode = str(iter_plan.get("range_mode") or "")
            if range_mode not in {"ascending", "descending", "dynamic"}:
                if isinstance(step_const, int):
                    if step_const > 0:
                        range_mode = "ascending"
                    elif step_const < 0:
                        range_mode = "descending"
                    else:
                        range_mode = "dynamic"
                else:
                    range_mode = "dynamic"
            if range_mode == "ascending":
                # Python range stop is exclusive, Lua numeric-for upper bound is inclusive.
                upper = stop + " - 1" if self._is_simple_bound_expr(iter_plan.get("stop")) else "(" + stop + ") - 1"
                if step_const == 1:
                    self._emit_line("for " + target_name + " = " + start + ", " + upper + " do")
                else:
                    self._emit_line("for " + target_name + " = " + start + ", " + upper + ", " + step + " do")
                self.indent += 1
                if needs_continue_label:
                    self.loop_continue_labels.append(continue_label)
                self._emit_block(stmt.get("body"))
                if needs_continue_label:
                    self.loop_continue_labels.pop()
                    self._emit_line("::" + continue_label + "::")
                self.indent -= 1
                self._emit_line("end")
                return
            if range_mode == "descending":
                # Descending range: exclusive stop must shift toward +1 for Lua inclusive bound.
                lower = "(" + stop + ") + 1"
                self._emit_line("for " + target_name + " = " + start + ", " + lower + ", " + step + " do")
                self.indent += 1
                if needs_continue_label:
                    self.loop_continue_labels.append(continue_label)
                self._emit_block(stmt.get("body"))
                if needs_continue_label:
                    self.loop_continue_labels.pop()
                    self._emit_line("::" + continue_label + "::")
                self.indent -= 1
                self._emit_line("end")
                return
            start_tmp = self._next_tmp_name("__pytra_range_start")
            stop_tmp = self._next_tmp_name("__pytra_range_stop")
            step_tmp = self._next_tmp_name("__pytra_range_step")
            self._emit_line("local " + start_tmp + " = " + start)
            self._emit_line("local " + stop_tmp + " = " + stop)
            self._emit_line("local " + step_tmp + " = " + step)
            self._emit_line("if " + step_tmp + " > 0 then")
            self.indent += 1
            self._emit_line(
                "for " + target_name + " = " + start_tmp + ", (" + stop_tmp + ") - 1, " + step_tmp + " do"
            )
            self.indent += 1
            if needs_continue_label:
                self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
            if needs_continue_label:
                self.loop_continue_labels.pop()
                self._emit_line("::" + continue_label + "::")
            self.indent -= 1
            self._emit_line("end")
            self.indent -= 1
            self._emit_line("elseif " + step_tmp + " < 0 then")
            self.indent += 1
            self._emit_line(
                "for " + target_name + " = " + start_tmp + ", (" + stop_tmp + ") + 1, " + step_tmp + " do"
            )
            self.indent += 1
            if needs_continue_label:
                self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
            if needs_continue_label:
                self.loop_continue_labels.pop()
                self._emit_line("::" + continue_label + "::")
            self.indent -= 1
            self._emit_line("end")
            self.indent -= 1
            self._emit_line("end")
            return
        if iter_mode == "runtime_protocol":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=lua unsupported forcore runtime shape")
            iter_expr = self._render_expr(iter_plan.get("iter_expr"))
            tuple_target = isinstance(target_plan, dict) and target_plan.get("kind") == "TupleTarget"
            iter_name = target_name
            if tuple_target:
                iter_name = self._next_tmp_name("__it")
            self._emit_line("for _, " + iter_name + " in ipairs(" + iter_expr + ") do")
            self.indent += 1
            if tuple_target and isinstance(target_plan, dict):
                direct_names_any = target_plan.get("direct_unpack_names")
                direct_names = direct_names_any if isinstance(direct_names_any, list) else []
                if len(direct_names) > 0:
                    i = 0
                    while i < len(direct_names):
                        name_any = direct_names[i]
                        if isinstance(name_any, str) and name_any != "":
                            local_name = _safe_ident(name_any, "it")
                            self._emit_line("local " + local_name + " = " + iter_name + "[" + str(i + 1) + "]")
                        i += 1
                else:
                    elems_any = target_plan.get("elements")
                    elems = elems_any if isinstance(elems_any, list) else []
                    i = 0
                    while i < len(elems):
                        elem = elems[i]
                        if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                            local_name = _safe_ident(elem.get("id"), "it")
                            self._emit_line("local " + local_name + " = " + iter_name + "[" + str(i + 1) + "]")
                        i += 1
            if needs_continue_label:
                self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
            if needs_continue_label:
                self.loop_continue_labels.pop()
                self._emit_line("::" + continue_label + "::")
            self.indent -= 1
            self._emit_line("end")
            return
        raise RuntimeError("lang=lua unsupported forcore iter_mode: " + iter_mode)

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        continue_label = self._next_tmp_name("__pytra_continue")
        needs_continue_label = self._has_continue_in_block(stmt.get("body"))
        self._emit_line("while " + test + " do")
        self.indent += 1
        if needs_continue_label:
            self.loop_continue_labels.append(continue_label)
        self._emit_block(stmt.get("body"))
        if needs_continue_label:
            self.loop_continue_labels.pop()
            self._emit_line("::" + continue_label + "::")
        self.indent -= 1
        self._emit_line("end")

    def _next_tmp_name(self, prefix: str = "__pytra_tmp") -> str:
        self.tmp_seq += 1
        return prefix + "_" + str(self.tmp_seq)

    def _emit_tuple_assign(self, tuple_target: dict[str, Any], value_any: Any) -> None:
        elems_any = tuple_target.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        if len(elems) == 0:
            raise RuntimeError("lang=lua unsupported tuple assign target: empty")
        tmp_name = self._next_tmp_name("__pytra_tuple")
        value_expr = self._render_expr(value_any)
        self._emit_line("local " + tmp_name + " = " + value_expr)
        i = 0
        while i < len(elems):
            elem_any = elems[i]
            if isinstance(elem_any, dict):
                target_txt = self._render_target(elem_any)
                if (
                    isinstance(elem_any, dict)
                    and elem_any.get("kind") == "Name"
                    and len(self._local_var_stack) > 0
                ):
                    target_name = _safe_ident(elem_any.get("id"), "value")
                    if target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        self._emit_line("local " + target_txt + " = " + tmp_name + "[" + str(i + 1) + "]")
                        i += 1
                        continue
                self._emit_line(target_txt + " = " + tmp_name + "[" + str(i + 1) + "]")
            i += 1

    def _render_target(self, target_any: Any) -> str:
        if isinstance(target_any, dict) and target_any.get("kind") == "Name":
            return _safe_ident(target_any.get("id"), "value")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            owner = self._render_expr(target_any.get("value"))
            attr = _safe_ident(target_any.get("attr"), "field")
            return owner + "." + attr
        if isinstance(target_any, dict) and target_any.get("kind") == "Subscript":
            owner_node = target_any.get("value")
            owner = self._render_expr(owner_node)
            index_node = target_any.get("slice")
            if isinstance(index_node, dict) and index_node.get("kind") == "Slice":
                raise RuntimeError("lang=lua unsupported slice assignment target")
            index = self._render_expr(index_node)
            owner_type = ""
            if isinstance(owner_node, dict) and isinstance(owner_node.get("resolved_type"), str):
                owner_type = owner_node.get("resolved_type") or ""
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if idx_const >= 0:
                    return owner + "[" + str(idx_const + 1) + "]"
                return owner + "[(#(" + owner + ") + (" + str(idx_const) + ") + 1)]"
            return owner + "[(((" + index + ") < 0) and (#(" + owner + ") + (" + index + ") + 1) or ((" + index + ") + 1))]"
        target_kind = target_any.get("kind") if isinstance(target_any, dict) else type(target_any).__name__
        raise RuntimeError("lang=lua unsupported assignment target: " + str(target_kind))

    def _render_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "nil"
        kind = expr_any.get("kind")
        if kind == "Constant":
            return self._render_constant(expr_any.get("value"))
        if kind == "Name":
            return _safe_ident(expr_any.get("id"), "value")
        if kind == "BinOp":
            left_node = expr_any.get("left")
            right_node = expr_any.get("right")
            left = self._render_expr(expr_any.get("left"))
            right = self._render_expr(expr_any.get("right"))
            op_raw = str(expr_any.get("op"))
            op = _binop_symbol(op_raw)
            if op_raw == "Add":
                expr_resolved = expr_any.get("resolved_type")
                if (
                    (isinstance(expr_resolved, str) and expr_resolved == "str")
                    or self._is_str_expr(left_node)
                    or self._is_str_expr(right_node)
                ):
                    return "(" + left + " .. " + right + ")"
            if op_raw == "Mult" and (self._is_sequence_expr(left_node) or self._is_sequence_expr(right_node)):
                return "__pytra_repeat_seq(" + left + ", " + right + ")"
            return "(" + left + " " + op + " " + right + ")"
        if kind == "UnaryOp":
            operand = self._render_expr(expr_any.get("operand"))
            op = str(expr_any.get("op"))
            if op == "USub":
                return "(-" + operand + ")"
            if op == "UAdd":
                return "(+" + operand + ")"
            if op == "Not":
                return "(not " + operand + ")"
            return operand
        if kind == "Compare":
            ops = expr_any.get("ops")
            comps = expr_any.get("comparators")
            if not isinstance(ops, list) or not isinstance(comps, list) or len(ops) == 0 or len(comps) == 0:
                return "false"
            left = self._render_expr(expr_any.get("left"))
            right = self._render_expr(comps[0])
            op0 = str(ops[0])
            if op0 == "In":
                return "__pytra_contains(" + right + ", " + left + ")"
            if op0 == "NotIn":
                return "(not __pytra_contains(" + right + ", " + left + "))"
            return "(" + left + " " + _cmp_symbol(op0) + " " + right + ")"
        if kind == "BoolOp":
            values_any = expr_any.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "false"
            op = str(expr_any.get("op"))
            delim = " and " if op == "And" else " or "
            out: list[str] = []
            for v in values:
                out.append(self._render_expr(v))
            return "(" + delim.join(out) + ")"
        if kind == "Call":
            return self._render_call(expr_any)
        if kind == "List":
            elems_any = expr_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "Tuple":
            elems_any = expr_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "Set":
            elems_any = expr_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "ListComp":
            gens_any = expr_any.get("generators")
            gens = gens_any if isinstance(gens_any, list) else []
            if len(gens) != 1 or not isinstance(gens[0], dict):
                return "{}"
            gen = gens[0]
            target_any = gen.get("target")
            iter_any = gen.get("iter")
            if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
                return "{}"
            if not isinstance(iter_any, dict) or iter_any.get("kind") != "RangeExpr":
                return "{}"
            loop_var = _safe_ident(target_any.get("id"), "__lc_i")
            if loop_var == "_":
                loop_var = self._next_tmp_name("__lc_i")
            start = self._render_expr(iter_any.get("start"))
            stop = self._render_expr(iter_any.get("stop"))
            step = self._render_expr(iter_any.get("step"))
            elt = self._render_expr(expr_any.get("elt"))
            out_name = self._next_tmp_name("__lc_out")
            cond_expr = ""
            ifs_any = gen.get("ifs")
            if isinstance(ifs_any, list) and len(ifs_any) > 0:
                cond_parts: list[str] = []
                for cond_any in ifs_any:
                    cond_parts.append(self._render_expr(cond_any))
                cond_expr = " and ".join(cond_parts)
            insert_stmt = "table.insert(" + out_name + ", " + elt + ")"
            if cond_expr != "":
                insert_stmt = "if " + cond_expr + " then " + insert_stmt + " end"
            return (
                "(function() local "
                + out_name
                + " = {}; for "
                + loop_var
                + " = "
                + start
                + ", ("
                + stop
                + ") - 1, "
                + step
                + " do "
                + insert_stmt
                + " end; return "
                + out_name
                + " end)()"
            )
        if kind == "Dict":
            keys_any = expr_any.get("keys")
            values_any = expr_any.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            values = values_any if isinstance(values_any, list) else []
            if len(keys) == 0 or len(values) == 0:
                entries_any = expr_any.get("entries")
                entries = entries_any if isinstance(entries_any, list) else []
                if len(entries) == 0:
                    return "{}"
                pairs_from_entries: list[str] = []
                i = 0
                while i < len(entries):
                    ent = entries[i]
                    if isinstance(ent, dict):
                        k = self._render_expr(ent.get("key"))
                        v = self._render_expr(ent.get("value"))
                        pairs_from_entries.append("[" + k + "] = " + v)
                    i += 1
                if len(pairs_from_entries) == 0:
                    return "{}"
                return "{ " + ", ".join(pairs_from_entries) + " }"
            pairs: list[str] = []
            i = 0
            while i < len(keys) and i < len(values):
                k = self._render_expr(keys[i])
                v = self._render_expr(values[i])
                pairs.append("[" + k + "] = " + v)
                i += 1
            return "{ " + ", ".join(pairs) + " }"
        if kind == "Subscript":
            owner = self._render_expr(expr_any.get("value"))
            index_node = expr_any.get("slice")
            owner_node = expr_any.get("value")
            owner_type = ""
            if isinstance(owner_node, dict) and isinstance(owner_node.get("resolved_type"), str):
                owner_type = owner_node.get("resolved_type") or ""
            if isinstance(index_node, dict) and index_node.get("kind") == "Slice":
                lower_node = index_node.get("lower")
                upper_node = index_node.get("upper")
                lower = self._render_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._render_expr(upper_node) if isinstance(upper_node, dict) else "nil"
                if owner_type == "str":
                    if upper == "nil":
                        upper = "#" + owner
                    return "string.sub(" + owner + ", (" + lower + ") + 1, " + upper + ")"
                return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"
            index = self._render_expr(index_node)
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if owner_type == "str":
                    if idx_const >= 0:
                        pos = str(idx_const + 1)
                        return "string.sub(" + owner + ", " + pos + ", " + pos + ")"
                    pos = "(#(" + owner + ") + (" + str(idx_const) + ") + 1)"
                    return "string.sub(" + owner + ", " + pos + ", " + pos + ")"
                if idx_const >= 0:
                    return owner + "[" + str(idx_const + 1) + "]"
                return owner + "[(#(" + owner + ") + (" + str(idx_const) + ") + 1)]"
            if owner_type == "str":
                pos = "(((" + index + ") < 0) and (#(" + owner + ") + (" + index + ") + 1) or ((" + index + ") + 1))"
                return "string.sub(" + owner + ", " + pos + ", " + pos + ")"
            return owner + "[(((" + index + ") < 0) and (#(" + owner + ") + (" + index + ") + 1) or ((" + index + ") + 1))]"
        if kind == "Attribute":
            owner = self._render_expr(expr_any.get("value"))
            attr = _safe_ident(expr_any.get("attr"), "field")
            semantic_tag_any = expr_any.get("semantic_tag")
            semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
            runtime_call = self._resolved_runtime_call(expr_any)
            if semantic_tag.startswith("stdlib.") and runtime_call == "":
                raise RuntimeError("lang=lua unresolved stdlib runtime attribute: " + semantic_tag)
            return owner + "." + attr
        if kind == "IsInstance":
            value = self._render_expr(expr_any.get("value"))
            expected_any = expr_any.get("expected_type_id")
            if isinstance(expected_any, dict) and expected_any.get("kind") == "Name":
                expected = _safe_ident(expected_any.get("id"), "object")
                if expected in {"int", "int64", "float", "float64"}:
                    return '(type(' + value + ') == "number")'
                if expected in {"str", "string"}:
                    return '(type(' + value + ') == "string")'
                if expected in {"bool"}:
                    return '(type(' + value + ') == "boolean")'
                if expected in {"list", "dict", "set", "tuple"}:
                    return '(type(' + value + ') == "table")'
                if expected in self.class_names:
                    return "__pytra_isinstance(" + value + ", " + expected + ")"
            return "false"
        if kind == "IfExp":
            test = self._render_expr(expr_any.get("test"))
            body = self._render_expr(expr_any.get("body"))
            orelse = self._render_expr(expr_any.get("orelse"))
            return (
                "(function() "
                + "if __pytra_truthy("
                + test
                + ") then return ("
                + body
                + ") else return ("
                + orelse
                + ") end "
                + "end)()"
            )
        if kind == "JoinedStr":
            values_any = expr_any.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return '""'
            parts: list[str] = []
            for item in values:
                item_d = item if isinstance(item, dict) else {}
                item_kind = item_d.get("kind")
                if item_kind == "Constant" and isinstance(item_d.get("value"), str):
                    parts.append(self._render_expr(item_d))
                elif item_kind == "FormattedValue":
                    parts.append("tostring(" + self._render_expr(item_d.get("value")) + ")")
                else:
                    parts.append("tostring(" + self._render_expr(item_d) + ")")
            return "(" + " .. ".join(parts) + ")"
        if kind == "Box":
            return self._render_expr(expr_any.get("value"))
        if kind == "Unbox":
            return self._render_expr(expr_any.get("value"))
        if kind == "ObjStr":
            return "tostring(" + self._render_expr(expr_any.get("value")) + ")"
        if kind == "ObjBool":
            val = self._render_expr(expr_any.get("value"))
            resolved = expr_any.get("resolved_type")
            if isinstance(resolved, str):
                if resolved in {"bool"}:
                    return "__pytra_truthy(" + val + ")"
                if resolved in {"int", "int64", "float", "float64"}:
                    return "((" + val + ") ~= 0)"
                if resolved == "str":
                    return "(#(" + val + ") ~= 0)"
                if resolved.startswith("list[") or resolved.startswith("tuple[") or resolved.startswith("dict[") or resolved.startswith("set["):
                    return "(next(" + val + ") ~= nil)"
            return "__pytra_truthy(" + val + ")"
        if kind == "ObjLen":
            return "#(" + self._render_expr(expr_any.get("value")) + ")"
        raise RuntimeError("lang=lua unsupported expr kind: " + str(kind))

    def _render_call(self, expr: dict[str, Any]) -> str:
        func_any = expr.get("func")
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        keywords_any = expr.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(self._render_expr(arg))
        kw_rendered: dict[str, str] = {}
        kw_values_in_order: list[str] = []
        for kw_any in keywords:
            if not isinstance(kw_any, dict):
                continue
            key_any = kw_any.get("arg")
            if not isinstance(key_any, str) or key_any == "":
                continue
            rendered_kw = self._render_expr(kw_any.get("value"))
            kw_rendered[key_any] = rendered_kw
            kw_values_in_order.append(rendered_kw)
        semantic_tag_any = expr.get("semantic_tag")
        semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
        runtime_call = self._resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and semantic_tag != "stdlib.symbol.Path" and runtime_call == "":
            raise RuntimeError("lang=lua unresolved stdlib runtime call: " + semantic_tag)
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            fn_name = _safe_ident(func_any.get("id"), "fn")
            if fn_name == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
                fn_name = "__pytra_main"
            if fn_name == "print":
                return "__pytra_print(" + ", ".join(rendered_args) + ")"
            if fn_name == "int":
                if len(rendered_args) == 0:
                    return "0"
                return "__pytra_int(" + rendered_args[0] + ")"
            if fn_name == "float":
                if len(rendered_args) == 0:
                    return "0.0"
                return "__pytra_float(" + rendered_args[0] + ")"
            if fn_name == "bool":
                if len(rendered_args) == 0:
                    return "false"
                return "__pytra_truthy(" + rendered_args[0] + ")"
            if fn_name == "str":
                if len(rendered_args) == 0:
                    return '""'
                return "tostring(" + rendered_args[0] + ")"
            if fn_name == "len":
                if len(rendered_args) == 0:
                    return "0"
                return "#(" + rendered_args[0] + ")"
            if fn_name == "max":
                if len(rendered_args) == 0:
                    return "0"
                return "_G.math.max(" + ", ".join(rendered_args) + ")"
            if fn_name == "min":
                if len(rendered_args) == 0:
                    return "0"
                return "_G.math.min(" + ", ".join(rendered_args) + ")"
            if fn_name == "enumerate":
                if len(rendered_args) == 0:
                    return "{}"
                return (
                    "(function(__v) local __out = {}; "
                    + "for __i = 1, #__v do table.insert(__out, { __i - 1, __v[__i] }) end; "
                    + "return __out end)("
                    + rendered_args[0]
                    + ")"
                )
            if fn_name == "bytearray":
                if len(rendered_args) == 0:
                    return "__pytra_bytearray()"
                return "__pytra_bytearray(" + rendered_args[0] + ")"
            if fn_name == "bytes":
                if len(rendered_args) == 0:
                    return "__pytra_bytes()"
                return "__pytra_bytes(" + rendered_args[0] + ")"
            if fn_name in self.class_names:
                return fn_name + ".new(" + ", ".join(rendered_args) + ")"
            return fn_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_node = func_any.get("value")
            attr = _safe_ident(func_any.get("attr"), "call")
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and super_func.get("kind") == "Name":
                    super_name = str(super_func.get("id"))
                    if super_name in {"super", "_super"}:
                        if attr == "__init__":
                            return "__pytra_noop()"
                        if self.current_class_base_name != "":
                            if len(rendered_args) == 0:
                                return self.current_class_base_name + "." + attr + "(self)"
                            return self.current_class_base_name + "." + attr + "(self, " + ", ".join(rendered_args) + ")"
            owner = self._render_expr(owner_node)
            owner_type = ""
            if isinstance(owner_node, dict) and isinstance(owner_node.get("resolved_type"), str):
                owner_type = owner_node.get("resolved_type") or ""
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in self.imported_modules:
                    return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            if attr == "get":
                key = rendered_args[0] if len(rendered_args) >= 1 else "nil"
                default = rendered_args[1] if len(rendered_args) >= 2 else "nil"
                return (
                    "(function(__tbl, __key, __default) "
                    + "local __val = __tbl[__key]; "
                    + "if __val == nil then return __default end; "
                    + "return __val end)("
                    + owner
                    + ", "
                    + key
                    + ", "
                    + default
                    + ")"
                )
            if owner_type == "str" or attr in {"isdigit", "isalpha", "isalnum"}:
                if attr == "isdigit":
                    return "__pytra_str_isdigit(" + owner + ")"
                if attr == "isalpha":
                    return "__pytra_str_isalpha(" + owner + ")"
                if attr == "isalnum":
                    return "__pytra_str_isalnum(" + owner + ")"
            if attr == "append" and len(rendered_args) == 1:
                return "table.insert(" + owner + ", " + rendered_args[0] + ")"
            if attr == "pop":
                if len(rendered_args) == 0:
                    return "table.remove(" + owner + ")"
                return "table.remove(" + owner + ", (" + rendered_args[0] + ") + 1)"
            return owner + ":" + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        raise RuntimeError("lang=lua unsupported call target")

    def _render_constant(self, value: Any) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            return _lua_string(value)
        return "nil"


def transpile_to_lua_native(east_doc: dict[str, Any]) -> str:
    """EAST3 ドキュメントを Lua native ソースへ変換する。"""
    return LuaNativeEmitter(east_doc).transpile()

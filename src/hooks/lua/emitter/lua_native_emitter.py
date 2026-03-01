"""EAST3 -> Lua native emitter (minimal skeleton)."""

from __future__ import annotations

from pytra.std.typing import Any


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
        for stmt in body:
            self._emit_stmt(stmt)

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
                    if module_name in {"pytra.utils", "pytra.runtime"} and symbol in {"png", "gif"}:
                        self.imported_modules.add(_safe_ident(alias, "mod"))

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        import_lines: list[str] = []
        needs_perf_counter = False
        needs_png_runtime = False
        needs_math_runtime = False
        needs_path_runtime = False
        self._emit_print_helper()
        self._emit_line("")
        for stmt in body:
            kind = stmt.get("kind")
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
                    alias_txt = _safe_ident(alias, "mod")
                    if module_name == "math":
                        needs_math_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_math_module()")
                        continue
                    if module_name == "pathlib":
                        needs_path_runtime = True
                        import_lines.append("local " + alias_txt + " = { Path = __pytra_path_new }")
                        continue
                    if module_name == "time":
                        needs_perf_counter = True
                        import_lines.append("local " + alias_txt + " = { perf_counter = __pytra_perf_counter }")
                        continue
                    if module_name in {"pytra.utils.png", "pytra.runtime.png"}:
                        needs_png_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_png_module()")
                        continue
                    if module_name in {"pytra.utils.gif", "pytra.runtime.gif"}:
                        raise RuntimeError("lang=lua unresolved import module: " + module_name + " (gif runtime is not implemented)")
                    if module_name.startswith("pytra."):
                        raise RuntimeError("lang=lua unresolved import module: " + module_name)
                    import_lines.append("-- import " + module_name + " as " + alias_txt + " (not yet mapped)")
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
                    alias_txt = _safe_ident(alias, symbol)
                    if module_name in {"pytra.utils.assertions", "pytra.std.test"} and symbol == "py_assert_stdout":
                        import_lines.append("local py_assert_stdout = function(expected, fn) fn(); return true end")
                        continue
                    if module_name in {"pytra.utils.assertions", "pytra.std.test"} and symbol == "py_assert_eq":
                        import_lines.append("local " + alias_txt + " = function(a, b, _label) return a == b end")
                        continue
                    if module_name in {"pytra.utils.assertions", "pytra.std.test"} and symbol == "py_assert_true":
                        import_lines.append("local " + alias_txt + " = function(v, _label) return not not v end")
                        continue
                    if module_name in {"pytra.utils.assertions", "pytra.std.test"} and symbol == "py_assert_all":
                        import_lines.append(
                            "local "
                            + alias_txt
                            + " = function(checks, _label) if checks == nil then return false end; for i = 1, #checks do if not checks[i] then return false end end; return true end"
                        )
                        continue
                    if module_name == "time" and symbol == "perf_counter":
                        needs_perf_counter = True
                        import_lines.append("local " + alias_txt + " = __pytra_perf_counter")
                        continue
                    if module_name == "math":
                        needs_math_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_math_module()." + _safe_ident(symbol, symbol))
                        continue
                    if module_name == "pathlib" and symbol == "Path":
                        needs_path_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_path_new")
                        continue
                    if module_name in {"pytra.utils", "pytra.runtime"} and symbol == "png":
                        needs_png_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_png_module()")
                        continue
                    if module_name in {"pytra.utils.png", "pytra.runtime.png"} and symbol == "write_rgb_png":
                        needs_png_runtime = True
                        import_lines.append("local " + alias_txt + " = __pytra_write_rgb_png")
                        continue
                    if (
                        (module_name in {"pytra.utils", "pytra.runtime"} and symbol == "gif")
                        or (module_name in {"pytra.utils.gif", "pytra.runtime.gif"})
                    ):
                        raise RuntimeError(
                            "lang=lua unresolved import symbol: " + module_name + "." + symbol + " (gif runtime is not implemented)"
                        )
                    if module_name.startswith("pytra."):
                        raise RuntimeError("lang=lua unresolved import symbol: " + module_name + "." + symbol)
                    if module_name == "time":
                        raise RuntimeError("lang=lua unresolved import symbol: time." + symbol)
                    import_lines.append(
                        "-- from " + module_name + " import " + symbol + " as " + alias_txt + " (not yet mapped)"
                    )
        if needs_perf_counter:
            self._emit_perf_counter_helper()
            self._emit_line("")
        if needs_math_runtime:
            self._emit_math_runtime_helpers()
            self._emit_line("")
        if needs_path_runtime:
            self._emit_path_runtime_helpers()
            self._emit_line("")
        if needs_png_runtime:
            self._emit_png_runtime_helpers()
            self._emit_line("")
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

    def _emit_perf_counter_helper(self) -> None:
        self._emit_line("local function __pytra_perf_counter()")
        self.indent += 1
        self._emit_line("return os.clock()")
        self.indent -= 1
        self._emit_line("end")

    def _emit_math_runtime_helpers(self) -> None:
        self._emit_line("local function __pytra_math_module()")
        self.indent += 1
        self._emit_line("local m = {}")
        self._emit_line("for k, v in pairs(math) do")
        self.indent += 1
        self._emit_line("m[k] = v")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("if m.fabs == nil then m.fabs = math.abs end")
        self._emit_line("if m.log10 == nil then m.log10 = function(x) return math.log(x, 10) end end")
        self._emit_line("if m.pow == nil then m.pow = function(a, b) return (a ^ b) end end")
        self._emit_line("return m")
        self.indent -= 1
        self._emit_line("end")

    def _emit_path_runtime_helpers(self) -> None:
        self._emit_line("local function __pytra_path_basename(path)")
        self.indent += 1
        self._emit_line('local name = string.match(path, "([^/]+)$")')
        self._emit_line("if name == nil or name == \"\" then return path end")
        self._emit_line("return name")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_path_parent_text(path)")
        self.indent += 1
        self._emit_line('local parent = string.match(path, \"^(.*)/[^/]*$\")')
        self._emit_line("if parent == nil or parent == \"\" then return \".\" end")
        self._emit_line("return parent")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_path_stem(path)")
        self.indent += 1
        self._emit_line("local name = __pytra_path_basename(path)")
        self._emit_line('local stem = string.match(name, "^(.*)%.")')
        self._emit_line("if stem == nil or stem == \"\" then return name end")
        self._emit_line("return stem")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local __pytra_path_mt = {}")
        self._emit_line("__pytra_path_mt.__index = __pytra_path_mt")
        self._emit_line("")
        self._emit_line("local function __pytra_path_join(left, right)")
        self.indent += 1
        self._emit_line("if left == \"\" or left == \".\" then return right end")
        self._emit_line('if string.sub(left, -1) == "/" then return left .. right end')
        self._emit_line('return left .. "/" .. right')
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_path_new(path)")
        self.indent += 1
        self._emit_line("local text = tostring(path)")
        self._emit_line("local obj = { path = text }")
        self._emit_line("setmetatable(obj, __pytra_path_mt)")
        self._emit_line("obj.name = __pytra_path_basename(text)")
        self._emit_line("obj.stem = __pytra_path_stem(text)")
        self._emit_line("local parent_text = __pytra_path_parent_text(text)")
        self._emit_line("if parent_text ~= text then")
        self.indent += 1
        self._emit_line("obj.parent = setmetatable({ path = parent_text }, __pytra_path_mt)")
        self._emit_line("obj.parent.name = __pytra_path_basename(parent_text)")
        self._emit_line("obj.parent.stem = __pytra_path_stem(parent_text)")
        self._emit_line("obj.parent.parent = nil")
        self.indent -= 1
        self._emit_line("else")
        self.indent += 1
        self._emit_line("obj.parent = nil")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return obj")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("function __pytra_path_mt.__div(lhs, rhs)")
        self.indent += 1
        self._emit_line("local left = lhs.path")
        self._emit_line("local right = tostring(rhs)")
        self._emit_line("if type(rhs) == \"table\" and rhs.path ~= nil then")
        self.indent += 1
        self._emit_line("right = rhs.path")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return __pytra_path_new(__pytra_path_join(left, right))")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("function __pytra_path_mt:exists()")
        self.indent += 1
        self._emit_line('local f = io.open(self.path, "rb")')
        self._emit_line("if f ~= nil then")
        self.indent += 1
        self._emit_line("f:close()")
        self._emit_line("return true")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local ok = os.execute('test -e \"' .. self.path .. '\"')")
        self._emit_line("if type(ok) == \"boolean\" then return ok end")
        self._emit_line("if type(ok) == \"number\" then return ok == 0 end")
        self._emit_line("return false")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("function __pytra_path_mt:mkdir()")
        self.indent += 1
        self._emit_line("os.execute('mkdir -p \"' .. self.path .. '\"')")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("function __pytra_path_mt:write_text(text)")
        self.indent += 1
        self._emit_line('local f = assert(io.open(self.path, "wb"))')
        self._emit_line("f:write(tostring(text))")
        self._emit_line("f:close()")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("function __pytra_path_mt:read_text()")
        self.indent += 1
        self._emit_line('local f = assert(io.open(self.path, "rb"))')
        self._emit_line('local data = f:read("*a")')
        self._emit_line("f:close()")
        self._emit_line("return data")
        self.indent -= 1
        self._emit_line("end")

    def _emit_png_runtime_helpers(self) -> None:
        self._emit_line("local function __pytra_u32be(n)")
        self.indent += 1
        self._emit_line("local v = math.floor(tonumber(n) or 0) & 0xFFFFFFFF")
        self._emit_line("return string.char((v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local __pytra_crc_table = nil")
        self._emit_line("local function __pytra_init_crc_table()")
        self.indent += 1
        self._emit_line("if __pytra_crc_table ~= nil then")
        self.indent += 1
        self._emit_line("return")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local tbl = {}")
        self._emit_line("for i = 0, 255 do")
        self.indent += 1
        self._emit_line("local c = i")
        self._emit_line("for _ = 1, 8 do")
        self.indent += 1
        self._emit_line("if (c & 1) ~= 0 then")
        self.indent += 1
        self._emit_line("c = ((c >> 1) ~ 0xEDB88320) & 0xFFFFFFFF")
        self.indent -= 1
        self._emit_line("else")
        self.indent += 1
        self._emit_line("c = (c >> 1) & 0xFFFFFFFF")
        self.indent -= 1
        self._emit_line("end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("tbl[i] = c")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("__pytra_crc_table = tbl")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_png_crc32(data)")
        self.indent += 1
        self._emit_line("__pytra_init_crc_table()")
        self._emit_line("local c = 0xFFFFFFFF")
        self._emit_line("for i = 1, #data do")
        self.indent += 1
        self._emit_line("local b = string.byte(data, i)")
        self._emit_line("local idx = (c ~ b) & 0xFF")
        self._emit_line("c = ((c >> 8) ~ __pytra_crc_table[idx]) & 0xFFFFFFFF")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return (~c) & 0xFFFFFFFF")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_png_adler32(data)")
        self.indent += 1
        self._emit_line("local s1 = 1")
        self._emit_line("local s2 = 0")
        self._emit_line("for i = 1, #data do")
        self.indent += 1
        self._emit_line("s1 = (s1 + string.byte(data, i)) % 65521")
        self._emit_line("s2 = (s2 + s1) % 65521")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return ((s2 << 16) | s1) & 0xFFFFFFFF")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_png_chunk(kind, data)")
        self.indent += 1
        self._emit_line("local payload = data or \"\"")
        self._emit_line("local crc = __pytra_png_crc32(kind .. payload)")
        self._emit_line("return __pytra_u32be(#payload) .. kind .. payload .. __pytra_u32be(crc)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_zlib_store(raw)")
        self.indent += 1
        self._emit_line("local out = { string.char(0x78, 0x01) }")
        self._emit_line("local pos = 1")
        self._emit_line("while pos <= #raw do")
        self.indent += 1
        self._emit_line("local block_len = math.min(65535, #raw - pos + 1)")
        self._emit_line("local final_block = ((pos + block_len - 1) >= #raw) and 1 or 0")
        self._emit_line("local nlen = 65535 - block_len")
        self._emit_line("out[#out + 1] = string.char(final_block, block_len & 0xFF, (block_len >> 8) & 0xFF, nlen & 0xFF, (nlen >> 8) & 0xFF)")
        self._emit_line("out[#out + 1] = string.sub(raw, pos, pos + block_len - 1)")
        self._emit_line("pos = pos + block_len")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("out[#out + 1] = __pytra_u32be(__pytra_png_adler32(raw))")
        self._emit_line("return table.concat(out)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_write_rgb_png(path, width, height, pixels)")
        self.indent += 1
        self._emit_line("local out_path = tostring(path)")
        self._emit_line("local w = math.floor(tonumber(width) or 0)")
        self._emit_line("local h = math.floor(tonumber(height) or 0)")
        self._emit_line("if w <= 0 or h <= 0 then")
        self.indent += 1
        self._emit_line("error(\"write_rgb_png: width/height must be positive\")")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("if type(pixels) ~= \"table\" then")
        self.indent += 1
        self._emit_line("error(\"write_rgb_png: pixels must be table\")")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local expected = w * h * 3")
        self._emit_line("if #pixels ~= expected then")
        self.indent += 1
        self._emit_line("error(\"write_rgb_png: pixels length mismatch\")")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local scan = {}")
        self._emit_line("local idx = 1")
        self._emit_line("for _y = 1, h do")
        self.indent += 1
        self._emit_line("scan[#scan + 1] = string.char(0)")
        self._emit_line("for _x = 1, w * 3 do")
        self.indent += 1
        self._emit_line("local n = math.floor(tonumber(pixels[idx]) or 0)")
        self._emit_line("if n < 0 then n = 0 end")
        self._emit_line("if n > 255 then n = 255 end")
        self._emit_line("scan[#scan + 1] = string.char(n)")
        self._emit_line("idx = idx + 1")
        self.indent -= 1
        self._emit_line("end")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local raw = table.concat(scan)")
        self._emit_line("local ihdr = __pytra_u32be(w) .. __pytra_u32be(h) .. string.char(8, 2, 0, 0, 0)")
        self._emit_line("local idat = __pytra_zlib_store(raw)")
        self._emit_line(
            "local png_data = string.char(137, 80, 78, 71, 13, 10, 26, 10) .. __pytra_png_chunk(\"IHDR\", ihdr) .. __pytra_png_chunk(\"IDAT\", idat) .. __pytra_png_chunk(\"IEND\", \"\")"
        )
        self._emit_line("local fh = assert(io.open(out_path, \"wb\"))")
        self._emit_line("fh:write(png_data)")
        self._emit_line("fh:close()")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")
        self._emit_line("local function __pytra_png_module()")
        self.indent += 1
        self._emit_line("return {")
        self.indent += 1
        self._emit_line("write_rgb_png = function(...)")
        self.indent += 1
        self._emit_line("local argc = select(\"#\", ...)")
        self._emit_line("if argc == 5 then")
        self.indent += 1
        self._emit_line("local _, path, width, height, pixels = ...")
        self._emit_line("return __pytra_write_rgb_png(path, width, height, pixels)")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local path, width, height, pixels = ...")
        self._emit_line("return __pytra_write_rgb_png(path, width, height, pixels)")
        self.indent -= 1
        self._emit_line("end,")
        self._emit_line("write_gif = function(...)")
        self.indent += 1
        self._emit_line("error(\"lua runtime: write_gif is not implemented\")")
        self.indent -= 1
        self._emit_line("end,")
        self.indent -= 1
        self._emit_line("}")
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
            value = self._render_expr(stmt.get("value")) if isinstance(stmt.get("value"), dict) else "nil"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
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
                self._emit_line(target + " = " + value)
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                if targets[0].get("kind") == "Tuple":
                    self._emit_tuple_assign(targets[0], stmt.get("value"))
                    return
                target = self._render_target(targets[0])
                value = self._render_expr(stmt.get("value"))
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
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
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
        has_init = False
        for sub in body:
            if sub.get("kind") != "FunctionDef":
                continue
            if sub.get("name") == "__init__":
                has_init = True
            self._emit_class_method(cls_name, sub)
        if not has_init:
            self._emit_line("function " + cls_name + ".new()")
            self.indent += 1
            self._emit_line("return setmetatable({}, " + cls_name + ")")
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")

    def _emit_class_method(self, cls_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        for i, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i == 0 and arg_name == "self":
                continue
            args.append(arg_name)
        if method_name == "__init__":
            self._emit_line("function " + cls_name + ".new(" + ", ".join(args) + ")")
            self.indent += 1
            self._emit_line("local self = setmetatable({}, " + cls_name + ")")
            self._emit_block(stmt.get("body"))
            self._emit_line("return self")
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")
            return
        self._emit_line("function " + cls_name + ":" + method_name + "(" + ", ".join(args) + ")")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")
        continue_label = self._next_tmp_name("__pytra_continue")
        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict) or iter_plan.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=lua unsupported forcore static_fastpath shape")
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            step = self._render_expr(iter_plan.get("step"))
            range_mode = str(iter_plan.get("range_mode") or "")
            if range_mode not in {"ascending", "descending", "dynamic"}:
                step_const = self._const_int_literal(iter_plan.get("step"))
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
                upper = "(" + stop + ") - 1"
                self._emit_line("for " + target_name + " = " + start + ", " + upper + ", " + step + " do")
                self.indent += 1
                self.loop_continue_labels.append(continue_label)
                self._emit_block(stmt.get("body"))
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
                self.loop_continue_labels.append(continue_label)
                self._emit_block(stmt.get("body"))
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
            self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
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
            self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
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
            self._emit_line("for _, " + target_name + " in ipairs(" + iter_expr + ") do")
            self.indent += 1
            self.loop_continue_labels.append(continue_label)
            self._emit_block(stmt.get("body"))
            self.loop_continue_labels.pop()
            self._emit_line("::" + continue_label + "::")
            self.indent -= 1
            self._emit_line("end")
            return
        raise RuntimeError("lang=lua unsupported forcore iter_mode: " + iter_mode)

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
        continue_label = self._next_tmp_name("__pytra_continue")
        self._emit_line("while " + test + " do")
        self.indent += 1
        self.loop_continue_labels.append(continue_label)
        self._emit_block(stmt.get("body"))
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
            return owner + "[(" + index + ") + 1]"
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
            left = self._render_expr(expr_any.get("left"))
            right = self._render_expr(expr_any.get("right"))
            op = _binop_symbol(str(expr_any.get("op")))
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
            return "(" + left + " " + _cmp_symbol(str(ops[0])) + " " + right + ")"
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
                upper = self._render_expr(upper_node) if isinstance(upper_node, dict) else ("#" + owner)
                if owner_type == "str":
                    return "string.sub(" + owner + ", (" + lower + ") + 1, " + upper + ")"
                raise RuntimeError("lang=lua unsupported expr kind: Slice")
            index = self._render_expr(index_node)
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            return owner + "[(" + index + ") + 1]"
        if kind == "Attribute":
            owner = self._render_expr(expr_any.get("value"))
            attr = _safe_ident(expr_any.get("attr"), "field")
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
            return "((" + test + ") and (" + body + ") or (" + orelse + "))"
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
            return "((" + val + ") and true or false)"
        if kind == "ObjLen":
            return "#(" + self._render_expr(expr_any.get("value")) + ")"
        raise RuntimeError("lang=lua unsupported expr kind: " + str(kind))

    def _render_call(self, expr: dict[str, Any]) -> str:
        func_any = expr.get("func")
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(self._render_expr(arg))
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            fn_name = _safe_ident(func_any.get("id"), "fn")
            if fn_name == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
                fn_name = "__pytra_main"
            if fn_name == "print":
                return "__pytra_print(" + ", ".join(rendered_args) + ")"
            if fn_name == "int":
                if len(rendered_args) == 0:
                    return "0"
                return "(math.floor(tonumber(" + rendered_args[0] + ") or 0))"
            if fn_name == "float":
                if len(rendered_args) == 0:
                    return "0.0"
                return "(tonumber(" + rendered_args[0] + ") or 0.0)"
            if fn_name == "bool":
                if len(rendered_args) == 0:
                    return "false"
                return "((" + rendered_args[0] + ") and true or false)"
            if fn_name == "str":
                if len(rendered_args) == 0:
                    return '""'
                return "tostring(" + rendered_args[0] + ")"
            if fn_name == "len":
                if len(rendered_args) == 0:
                    return "0"
                return "#(" + rendered_args[0] + ")"
            if fn_name == "bytearray":
                if len(rendered_args) == 0:
                    return "{}"
                return (
                    "(function(__v) "
                    + "if type(__v) == \"number\" then local __n = math.max(0, math.floor(tonumber(__v) or 0)); local __out = {}; for __i = 1, __n do __out[#__out + 1] = 0 end; return __out "
                    + "elseif type(__v) == \"table\" then local __out = {}; for __i = 1, #__v do __out[#__out + 1] = __v[__i] end; return __out "
                    + "else return {} end end)("
                    + rendered_args[0]
                    + ")"
                )
            if fn_name in self.class_names:
                return fn_name + ".new(" + ", ".join(rendered_args) + ")"
            return fn_name + "(" + ", ".join(rendered_args) + ")"
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner = self._render_expr(func_any.get("value"))
            owner_node = func_any.get("value")
            attr = _safe_ident(func_any.get("attr"), "call")
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in self.imported_modules:
                    return owner + "." + attr + "(" + ", ".join(rendered_args) + ")"
            if attr == "append" and len(rendered_args) == 1:
                return "table.insert(" + owner + ", " + rendered_args[0] + ")"
            if attr == "pop":
                if len(rendered_args) == 0:
                    return "table.remove(" + owner + ")"
                return "table.remove(" + owner + ", (" + rendered_args[0] + ") + 1)"
            return owner + ":" + attr + "(" + ", ".join(rendered_args) + ")"
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

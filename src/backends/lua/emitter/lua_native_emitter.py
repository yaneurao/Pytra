"""EAST3 -> Lua native emitter (minimal skeleton)."""

from __future__ import annotations

from typing import Any

from backends.common.emitter.code_emitter import (
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)

from toolchain.frontends.runtime_symbol_index import (
    canonical_runtime_module_id,
    lookup_runtime_module_symbols,
    lookup_runtime_symbol_doc,
    resolve_import_binding_doc,
)


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
_COMPILETIME_STD_IMPORT_SYMBOLS = {"abi", "template", "extern"}


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


def _relative_import_module_path(module_id: str) -> str:
    parts = [
        _safe_ident(part, "module")
        for part in module_id.lstrip(".").split(".")
        if part != ""
    ]
    return ".".join(parts)


def _collect_relative_import_name_aliases(east_doc: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    wildcard_modules: dict[str, str] = {}
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
        sd: dict[str, Any] = stmt
        if sd.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = sd.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = sd.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        names_any = sd.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if not isinstance(ent, dict):
                j += 1
                continue
            name_any = ent.get("name")
            name = name_any if isinstance(name_any, str) else ""
            if name == "":
                j += 1
                continue
            if name == "*":
                wildcard_module = module_path if module_path != "" else _relative_import_module_path(module_id)
                if wildcard_module != "":
                    wildcard_modules[wildcard_module] = wildcard_module
                j += 1
                continue
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    if len(wildcard_modules) == 0:
        return aliases
    meta_any = east_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    import_symbols_any = meta.get("import_symbols")
    import_symbols = import_symbols_any if isinstance(import_symbols_any, dict) else {}
    wildcard_resolved: dict[str, bool] = {module_id: False for module_id in wildcard_modules}
    for local_name_any, binding_any in import_symbols.items():
        if not isinstance(local_name_any, str) or local_name_any == "":
            continue
        if not isinstance(binding_any, dict):
            continue
        binding_module_any = binding_any.get("module")
        binding_symbol_any = binding_any.get("name")
        binding_module = (
            _relative_import_module_path(binding_module_any)
            if isinstance(binding_module_any, str)
            else ""
        )
        binding_symbol = binding_symbol_any if isinstance(binding_symbol_any, str) else ""
        if binding_module not in wildcard_resolved or binding_symbol == "":
            continue
        local_rendered = _safe_ident(local_name_any, "value")
        target_name = _safe_ident(binding_symbol, "value")
        aliases[local_rendered] = (
            target_name if binding_module == "" else binding_module + "." + target_name
        )
        wildcard_resolved[binding_module] = True
    unresolved = [module_id for module_id, resolved in wildcard_resolved.items() if not resolved]
    if len(unresolved) > 0:
        raise RuntimeError(
            "lua native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


def _lua_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\t", "\\t")
    out = out.replace("\r", "\\r")
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


def _runtime_module_symbol_names(runtime_module_id: str) -> tuple[str, ...]:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    if mod == "":
        return ()
    symbols = lookup_runtime_module_symbols(mod)
    out = [name for name in symbols if isinstance(name, str) and name != ""]
    out.sort()
    return tuple(out)


def _runtime_symbol_call_adapter_kind(runtime_module_id: str, runtime_symbol: str) -> str:
    symbol_doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    adapter_kind_any = symbol_doc.get("call_adapter_kind")
    if isinstance(adapter_kind_any, str):
        as: str = adapter_kind_any
        return as.strip()
    return ""


def _runtime_symbol_semantic_tag(runtime_module_id: str, runtime_symbol: str) -> str:
    symbol_doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    semantic_tag_any = symbol_doc.get("semantic_tag")
    if isinstance(semantic_tag_any, str):
        ss: str = semantic_tag_any
        return ss.strip()
    return ""


def _is_math_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_call_adapter_kind(runtime_module_id, runtime_symbol) in {
        "math.float_args",
        "math.value_getter",
    }


def _is_perf_counter_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) == "stdlib.fn.perf_counter"


def _is_glob_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) == "stdlib.fn.glob"


def _is_os_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) in {
        "stdlib.fn.getcwd",
        "stdlib.fn.mkdir",
        "stdlib.fn.makedirs",
    }


def _is_os_path_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) in {
        "stdlib.fn.join",
        "stdlib.fn.dirname",
        "stdlib.fn.basename",
        "stdlib.fn.splitext",
        "stdlib.fn.abspath",
        "stdlib.fn.exists",
    }


def _is_sys_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) in {
        "stdlib.symbol.argv",
        "stdlib.symbol.path",
        "stdlib.symbol.stderr",
        "stdlib.symbol.stdout",
        "stdlib.fn.exit",
        "stdlib.fn.set_argv",
        "stdlib.fn.set_path",
        "stdlib.fn.write_stderr",
        "stdlib.fn.write_stdout",
    }


def _pascal_symbol_name(name: str) -> str:
    out: list[str] = []
    uppercase_next = True
    i = 0
    while i < len(name):
        ch = name[i]
        if ch == "_":
            uppercase_next = True
            i += 1
            continue
        if uppercase_next:
            out.append(ch.upper())
            uppercase_next = False
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _runtime_symbol_alias_expr(runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    if sym == "":
        return ""
    if _is_math_runtime_symbol(mod, sym):
        if sym == "pi":
            return "pyMathPi()"
        if sym == "e":
            return "pyMathE()"
        if sym == "log10":
            return "function(x) return math.log(x, 10) end"
        return "pyMath" + _pascal_symbol_name(sym)
    if _is_perf_counter_runtime_symbol(mod, sym):
        return "__pytra_perf_counter"
    if _is_glob_runtime_symbol(mod, sym):
        return "function(_pattern) return {} end"
    if _is_os_runtime_symbol(mod, sym):
        if sym == "getcwd":
            return "function() return '.' end"
        return "function(_p, _exist_ok) end"
    if _is_os_path_runtime_symbol(mod, sym):
        if sym == "join":
            return "function(a, b) return tostring(a) .. '/' .. tostring(b) end"
        if sym == "dirname":
            return "function(_p) return '' end"
        if sym == "basename":
            return "function(p) return tostring(p) end"
        if sym == "splitext":
            return "function(p) return { tostring(p), '' } end"
        if sym == "abspath":
            return "function(p) return tostring(p) end"
        if sym == "exists":
            return "function(_p) return false end"
    if _is_sys_runtime_symbol(mod, sym):
        if sym == "argv":
            return "(arg or {})"
        if sym == "path":
            return "{}"
        if sym == "stderr":
            return "{ write = function(text) io.stderr:write(text) end }"
        if sym == "stdout":
            return "{ write = function(text) io.write(text) end }"
        if sym == "exit":
            return "function(code) os.exit(tonumber(code) or 0) end"
        if sym == "set_argv" or sym == "set_path":
            return "function(_values) end"
        if sym == "write_stderr":
            return "function(text) io.stderr:write(text) end"
        if sym == "write_stdout":
            return "function(text) io.write(text) end"
    return ""


def _runtime_module_alias_via_symbol_table(alias_txt: str, runtime_module_id: str) -> str:
    symbol_names = _runtime_module_symbol_names(runtime_module_id)
    if len(symbol_names) == 0:
        return ""
    entries: list[str] = []
    for symbol_name in symbol_names:
        expr = _runtime_symbol_alias_expr(runtime_module_id, symbol_name)
        if expr == "":
            return ""
        entries.append(_safe_ident(symbol_name, symbol_name) + " = " + expr)
    return "local " + alias_txt + " = { " + ", ".join(entries) + " }"


def _runtime_module_alias_line(alias_txt: str, runtime_module_id: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    symbol_table_line = _runtime_module_alias_via_symbol_table(alias_txt, mod)
    if symbol_table_line != "":
        return symbol_table_line
    if mod in {"enum", "pytra.std.enum"}:
        return "local " + alias_txt + " = { Enum = {}, IntEnum = {}, IntFlag = {} }"
    if mod == "pytra.std.argparse":
        return "local " + alias_txt + " = { ArgumentParser = function(...) return {} end }"
    if mod == "pytra.std.re":
        return "local " + alias_txt + " = { sub = function(_pattern, _repl, text, _flags) return text end }"
    if mod == "pytra.std.json":
        return "local " + alias_txt + " = { loads = pyJsonLoads, dumps = pyJsonDumps }"
    if mod == "pytra.std.pathlib":
        return "local " + alias_txt + " = { Path = Path }"
    if mod in {"pytra.utils.png", "pytra.utils.gif"}:
        leaf = _safe_ident(mod.rsplit(".", 1)[-1], "utils")
        return "local " + alias_txt + " = __pytra_" + leaf + "_module()"
    return ""


def _runtime_symbol_alias_line(alias_txt: str, runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    alias_expr = _runtime_symbol_alias_expr(mod, sym)
    if alias_expr != "":
        return "local " + alias_txt + " = " + alias_expr
    if mod in {"enum", "pytra.std.enum"}:
        if sym in {"Enum", "IntEnum", "IntFlag"}:
            return "local " + alias_txt + " = {}"
        return ""
    if mod == "pytra.std.argparse" and sym == "ArgumentParser":
        return "local " + alias_txt + " = function(...) return {} end"
    if mod == "pytra.std.re" and sym == "sub":
        return "local " + alias_txt + " = function(_pattern, _repl, text, _flags) return text end"
    if mod == "pytra.std.json":
        if sym == "loads":
            return "local " + alias_txt + " = pyJsonLoads"
        if sym == "dumps":
            return "local " + alias_txt + " = pyJsonDumps"
        return ""
    if mod == "pytra.std.pathlib" and sym == "Path":
        return "local " + alias_txt + " = Path"
    if mod.startswith("pytra.utils.") and sym != "":
        return "local " + alias_txt + " = __pytra_" + _safe_ident(sym, sym)
    return ""


def _is_compile_time_std_import_symbol(module_id: str, symbol: str) -> bool:
    mod = canonical_runtime_module_id(module_id.strip())
    return mod == "pytra.std" and symbol in _COMPILETIME_STD_IMPORT_SYMBOLS


def _reject_unsupported_relative_import_forms(body_any: Any) -> None:
    if not isinstance(body_any, list):
        return
    i = 0
    while i < len(body_any):
        stmt = body_any[i]
        i += 1
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind != "Import" and kind != "ImportFrom":
            continue
        module_any = stmt.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if isinstance(ent, dict) and ent.get("name") == "*":
                raise RuntimeError(
                    "lua native emitter: unsupported relative import form: wildcard import"
                )
            j += 1
        if kind == "ImportFrom":
            continue
        raise RuntimeError(
            "lua native emitter: unsupported relative import form: relative import"
        )


class LuaNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=lua invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=lua invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=lua unsupported east_stage: " + str(ed.get("east_stage")))
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.imported_modules: set[str] = set()
        self.function_names: set[str] = set()
        self.relative_import_name_aliases: dict[str, str] = {}
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
        ts: str = type_name
        if ts.startswith("dict["):
            return "dict"
        if ts.startswith("list[") or ts.startswith("tuple[") or ts.startswith("set["):
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
        if not isinstance(value_any, dict):
            return None
        vd2: dict[str, Any] = value_any
        if vd2.get("kind") != "Name":
            return None
        source_name = _safe_ident(vd2.get("id"), "value")
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
        nd5: dict[str, Any] = node_any
        kind = nd5.get("kind")
        if kind == "Constant":
            value = nd5.get("value")
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            return None
        if kind == "UnaryOp" and str(nd5.get("op")) == "USub":
            operand = self._const_int_literal(nd5.get("operand"))
            if operand is None:
                return None
            return -operand
        return None

    def _resolved_runtime_call(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed2: dict[str, Any] = expr_any
        runtime_call = ed2.get("runtime_call")
        if isinstance(runtime_call, str) and runtime_call != "":
            return runtime_call
        resolved_runtime_call = ed2.get("resolved_runtime_call")
        if isinstance(resolved_runtime_call, str) and resolved_runtime_call != "":
            return resolved_runtime_call
        return ""

    def _is_sequence_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        nd4: dict[str, Any] = node_any
        kind = nd4.get("kind")
        if kind in {"List", "Tuple", "JoinedStr", "Dict", "Set"}:
            return True
        if kind == "Constant" and isinstance(nd4.get("value"), str):
            return True
        resolved = self._lookup_expr_type(node_any)
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
        nd3: dict[str, Any] = node_any
        if nd3.get("kind") == "Constant" and isinstance(nd3.get("value"), str):
            return True
        return self._lookup_expr_type(node_any) == "str"

    def _lookup_expr_type(self, node_any: Any) -> str:
        if not isinstance(node_any, dict):
            return ""
        nd2: dict[str, Any] = node_any
        resolved = nd2.get("resolved_type")
        if isinstance(resolved, str) and resolved != "":
            return resolved
        kind = nd2.get("kind")
        if kind == "Name":
            safe_name = _safe_ident(nd2.get("id"), "")
            if safe_name != "":
                mapped = self._current_type_map().get(safe_name)
                if isinstance(mapped, str) and mapped != "":
                    return mapped
        if kind == "Constant":
            value = nd2.get("value")
            if isinstance(value, bool):
                return "bool"
            if isinstance(value, int):
                return "int"
            if isinstance(value, float):
                return "float"
            if isinstance(value, str):
                return "str"
        if kind in {"List", "Tuple"}:
            return "list[Any]"
        if kind == "Dict":
            return "dict[Any,Any]"
        if kind == "Set":
            return "set[Any]"
        return ""

    def _infer_decl_type_from_expr(self, node_any: Any) -> str:
        inferred = self._lookup_expr_type(node_any)
        if inferred == "":
            return ""
        if inferred in {"bool", "int", "float", "str"}:
            return inferred
        if (
            inferred.startswith("list[")
            or inferred.startswith("tuple[")
            or inferred.startswith("dict[")
            or inferred.startswith("set[")
        ):
            return inferred
        return ""

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="-- ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        self._emit_imports(body)
        self._emit_obj_type_id_helper()
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

    def _block_has_return_stmt(self, body_any: Any) -> bool:
        body = self._dict_list(body_any)
        i = 0
        while i < len(body):
            if body[i].get("kind") == "Return":
                return True
            i += 1
        return False

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
        nd: dict[str, Any] = node
        kind = nd.get("kind")
        return kind in {"Name", "Constant", "Attribute", "Subscript"}

    def _append_chain_stmt_parts(self, stmt_any: Any) -> tuple[str, str] | None:
        if not isinstance(stmt_any, dict):
            return None
        sd: dict[str, Any] = stmt_any
        if sd.get("kind") != "Expr":
            return None
        value_any = sd.get("value")
        if not isinstance(value_any, dict):
            return None
        vd: dict[str, Any] = value_any
        if vd.get("kind") != "Call":
            return None
        func_any = vd.get("func")
        if not isinstance(func_any, dict):
            return None
        fd: dict[str, Any] = func_any
        if fd.get("kind") != "Attribute":
            return None
        if _safe_ident(fd.get("attr"), "") != "append":
            return None
        owner_any = fd.get("value")
        if not isinstance(owner_any, dict):
            return None
        od: dict[str, Any] = owner_any
        if od.get("kind") != "Name":
            return None
        args_any = vd.get("args")
        args = args_any if isinstance(args_any, list) else []
        keywords_any = vd.get("keywords")
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
        nd: dict[str, Any] = node_any
        kind = nd.get("kind")
        if kind == "Name":
            return True
        if kind == "Constant":
            value_any = nd.get("value")
            if isinstance(value_any, bool):
                return False
            return isinstance(value_any, int) or isinstance(value_any, float)
        return False

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        self.class_names = set()
        self.imported_modules = set()
        self.function_names = set()
        self.relative_import_name_aliases = _collect_relative_import_name_aliases(self.east_doc)
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
                level_any = stmt.get("level")
                level = level_any if isinstance(level_any, int) else 0
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
                    if level > 0 or module_name.startswith("."):
                        module_path = _relative_import_module_path(module_name)
                        if module_path == "":
                            self.imported_modules.add(_safe_ident(alias, "mod"))
                        continue
                    resolved = resolve_import_binding_doc(module_name, symbol, "symbol")
                    if resolved.get("resolved_binding_kind") == "module":
                        self.imported_modules.add(_safe_ident(alias, "mod"))

    def _render_name_expr(self, expr_any: dict[str, Any]) -> str:
        ident = _safe_ident(expr_any.get("id"), "value")
        if ident == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
            ident = "__pytra_main"
        return self.relative_import_name_aliases.get(ident, ident)

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
                level_any = stmt.get("level")
                level = level_any if isinstance(level_any, int) else 0
                if level > 0 or mod.startswith("."):
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
                    if _is_compile_time_std_import_symbol(mod, sym):
                        continue
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

    def _emit_obj_type_id_helper(self) -> None:
        self._emit_line("local function __pytra_obj_type_id(value)")
        self.indent += 1
        self._emit_line('if type(value) ~= "table" then')
        self.indent += 1
        self._emit_line("return nil")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line('local tagged = rawget(value, "PYTRA_TYPE_ID")')
        self._emit_line("if tagged ~= nil then")
        self.indent += 1
        self._emit_line("return tagged")
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("local mt = getmetatable(value)")
        self._emit_line('if type(mt) == "table" then')
        self.indent += 1
        self._emit_line('return rawget(mt, "PYTRA_TYPE_ID")')
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("return nil")
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
                        as: str = anno_any
                        decl_type = as.strip()
                if decl_type == "":
                    decl_type = self._infer_decl_type_from_expr(value_node)
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
                td2: dict[str, Any] = target_any
                if td2.get("kind") == "Tuple":
                    self._emit_tuple_assign(target_any, stmt.get("value"))
                    return
                target = self._render_target(target_any)
                value = self._render_expr(stmt.get("value"))
                if isinstance(target_any, dict) and td2.get("kind") == "Name":
                    target_name = _safe_ident(td2.get("id"), "value")
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        mapped_decl = self._current_type_map().get(target_name)
                        decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
                    if decl_type == "":
                        decl_type = self._infer_decl_type_from_expr(stmt.get("value"))
                    materialized = self._materialize_container_value_from_ref(
                        stmt.get("value"),
                        target_name=target_name,
                        target_decl_type=decl_type,
                    )
                    if materialized is not None:
                        value = materialized
                    if decl_type != "":
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
                    if decl_type == "":
                        decl_type = self._infer_decl_type_from_expr(stmt.get("value"))
                    materialized = self._materialize_container_value_from_ref(
                        stmt.get("value"),
                        target_name=target_name,
                        target_decl_type=decl_type,
                    )
                    if materialized is not None:
                        value = materialized
                    if decl_type != "":
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
            op_token = _binop_symbol(op)
            if op == "Add":
                target_type = self._lookup_expr_type(stmt.get("target"))
                value_type = self._lookup_expr_type(stmt.get("value"))
                if target_type == "str" or value_type == "str":
                    op_token = ".."
            self._emit_line(target + " = " + target + " " + op_token + " " + value)
            return
        if kind == "Swap":
            self._emit_swap(stmt)
            return
        if kind == "Expr":
            value_any = stmt.get("value")
            if isinstance(value_any, dict) and value_any.get("kind") == "Constant":
                if isinstance(value_any.get("value"), str):
                    return
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
            if self._block_has_return_stmt(body):
                return
            handlers_any = stmt.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            i = 0
            while i < len(handlers):
                h = handlers[i]
                if isinstance(h, dict):
                    hd: dict[str, Any] = h
                    h_body = self._dict_list(hd.get("body"))
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
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=lua unsupported forcore static_fastpath shape")
            id2: dict[str, Any] = iter_plan
            if id2.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=lua unsupported forcore static_fastpath shape")
            start = self._render_expr(id2.get("start"))
            stop = self._render_expr(id2.get("stop"))
            step = self._render_expr(id2.get("step"))
            step_const = self._const_int_literal(id2.get("step"))
            range_mode = str(id2.get("range_mode") or "")
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
                upper = stop + " - 1" if self._is_simple_bound_expr(id2.get("stop")) else "(" + stop + ") - 1"
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
            id: dict[str, Any] = iter_plan
            iter_expr = self._render_expr(id.get("iter_expr"))
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

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_target(stmt.get("left"))
        right = self._render_target(stmt.get("right"))
        tmp_name = self._next_tmp_name("__swap")
        self._emit_line("local " + tmp_name + " = " + left)
        self._emit_line(left + " = " + right)
        self._emit_line(right + " = " + tmp_name)

    def _render_target(self, target_any: Any) -> str:
        if not isinstance(target_any, dict):
            return "nil"
        tad: dict[str, Any] = target_any
        if tad.get("kind") == "Name":
            return _safe_ident(tad.get("id"), "value")
        if tad.get("kind") == "Attribute":
            owner = self._render_expr(tad.get("value"))
            attr = _safe_ident(tad.get("attr"), "field")
            return owner + "." + attr
        if tad.get("kind") == "Subscript":
            owner_node = tad.get("value")
            owner = self._render_expr(owner_node)
            index_node = tad.get("slice")
            if isinstance(index_node, dict):
                ind: dict[str, Any] = index_node
                if ind.get("kind") == "Slice":
                    raise RuntimeError("lang=lua unsupported slice assignment target")
            index = self._render_expr(index_node)
            owner_type = ""
            if isinstance(owner_node, dict):
                ond: dict[str, Any] = owner_node
                rt_any = ond.get("resolved_type")
                if isinstance(rt_any, str):
                    owner_type = rt_any
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if idx_const >= 0:
                    return owner + "[" + str(idx_const + 1) + "]"
                return owner + "[(#(" + owner + ") + (" + str(idx_const) + ") + 1)]"
            return owner + "[(((" + index + ") < 0) and (#(" + owner + ") + (" + index + ") + 1) or ((" + index + ") + 1))]"
        target_kind = tad.get("kind")
        raise RuntimeError("lang=lua unsupported assignment target: " + str(target_kind))

    def _render_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "nil"
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            return self._render_constant(ed.get("value"))
        if kind == "Name":
            return self._render_name_expr(expr_any)
        if kind == "BinOp":
            left_node = ed.get("left")
            right_node = ed.get("right")
            left = self._render_expr(ed.get("left"))
            right = self._render_expr(ed.get("right"))
            op_raw = str(ed.get("op"))
            op = _binop_symbol(op_raw)
            if op_raw == "Add":
                expr_resolved = ed.get("resolved_type")
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
            operand = self._render_expr(ed.get("operand"))
            op = str(ed.get("op"))
            if op == "USub":
                return "(-" + operand + ")"
            if op == "UAdd":
                return "(+" + operand + ")"
            if op == "Invert":
                return "(~" + operand + ")"
            if op == "Not":
                return "(not " + operand + ")"
            return operand
        if kind == "Compare":
            ops = ed.get("ops")
            comps = ed.get("comparators")
            if not isinstance(ops, list) or not isinstance(comps, list) or len(ops) == 0 or len(comps) == 0:
                return "false"
            left = self._render_expr(ed.get("left"))
            right = self._render_expr(comps[0])
            op0 = str(ops[0])
            if op0 == "In":
                return "__pytra_contains(" + right + ", " + left + ")"
            if op0 == "NotIn":
                return "(not __pytra_contains(" + right + ", " + left + "))"
            return "(" + left + " " + _cmp_symbol(op0) + " " + right + ")"
        if kind == "BoolOp":
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "false"
            op = str(ed.get("op"))
            delim = " and " if op == "And" else " or "
            out: list[str] = []
            for v in values:
                out.append(self._render_expr(v))
            return "(" + delim.join(out) + ")"
        if kind == "Call":
            return self._render_call(expr_any)
        if kind == "Lambda":
            args_any = ed.get("args")
            args = args_any if isinstance(args_any, list) else []
            if len(args) == 0 and isinstance(args_any, dict):
                nested_args_any = args_any.get("args")
                args = nested_args_any if isinstance(nested_args_any, list) else []
            names: list[str] = []
            for arg_any in args:
                if not isinstance(arg_any, dict):
                    continue
                names.append(_safe_ident(arg_any.get("arg"), "arg"))
            body = self._render_expr(ed.get("body"))
            return "function(" + ", ".join(names) + ") return " + body + " end"
        if kind == "List":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "Tuple":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "Set":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
        if kind == "ListComp":
            gens_any = ed.get("generators")
            gens = gens_any if isinstance(gens_any, list) else []
            if len(gens) != 1 or not isinstance(gens[0], dict):
                return "{}"
            gen = gens[0]
            target_any = gen.get("target")
            iter_any = gen.get("iter")
            if not isinstance(target_any, dict):
                return "{}"
            td: dict[str, Any] = target_any
            if td.get("kind") != "Name":
                return "{}"
            if not isinstance(iter_any, dict):
                return "{}"
            id: dict[str, Any] = iter_any
            if id.get("kind") != "RangeExpr":
                return "{}"
            loop_var = _safe_ident(td.get("id"), "__lc_i")
            if loop_var == "_":
                loop_var = self._next_tmp_name("__lc_i")
            start = self._render_expr(id.get("start"))
            stop = self._render_expr(id.get("stop"))
            step = self._render_expr(id.get("step"))
            elt = self._render_expr(ed.get("elt"))
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
            keys_any = ed.get("keys")
            values_any = ed.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            values = values_any if isinstance(values_any, list) else []
            if len(keys) == 0 or len(values) == 0:
                entries_any = ed.get("entries")
                entries = entries_any if isinstance(entries_any, list) else []
                if len(entries) == 0:
                    return "{}"
                pairs_from_entries: list[str] = []
                i = 0
                while i < len(entries):
                    ent = entries[i]
                    if isinstance(ent, dict):
                        ed: dict[str, Any] = ent
                        k = self._render_expr(ed.get("key"))
                        v = self._render_expr(ed.get("value"))
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
            owner = self._render_expr(ed.get("value"))
            index_node = ed.get("slice")
            owner_node = ed.get("value")
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
            owner = self._render_expr(ed.get("value"))
            attr = _safe_ident(ed.get("attr"), "field")
            semantic_tag_any = ed.get("semantic_tag")
            semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
            runtime_call = self._resolved_runtime_call(expr_any)
            if semantic_tag.startswith("stdlib.") and runtime_call == "":
                raise RuntimeError("lang=lua unresolved stdlib runtime attribute: " + semantic_tag)
            return owner + "." + attr
        if kind == "IsInstance":
            value = self._render_expr(ed.get("value"))
            expected_any = ed.get("expected_type_id")
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
        if kind == "IsSubtype" or kind == "IsSubclass":
            actual = self._render_expr(ed.get("actual_type_id"))
            expected = self._render_expr(ed.get("expected_type_id"))
            return "py_tid_is_subtype(" + actual + ", " + expected + ")"
        if kind == "IfExp":
            test = self._render_expr(ed.get("test"))
            body = self._render_expr(ed.get("body"))
            orelse = self._render_expr(ed.get("orelse"))
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
            values_any = ed.get("values")
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
            return self._render_expr(ed.get("value"))
        if kind == "Unbox":
            return self._render_expr(ed.get("value"))
        if kind == "ObjTypeId":
            return "__pytra_obj_type_id(" + self._render_expr(ed.get("value")) + ")"
        if kind == "ObjStr":
            return "tostring(" + self._render_expr(ed.get("value")) + ")"
        if kind == "ObjBool":
            val = self._render_expr(ed.get("value"))
            resolved = ed.get("resolved_type")
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
            return "#(" + self._render_expr(ed.get("value")) + ")"
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
            rendered_name = self._render_name_expr(func_any)
            return rendered_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
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
            owner_type = self._lookup_expr_type(owner_node)
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
            if owner_type == "str" or attr in {
                "isdigit",
                "isalpha",
                "isalnum",
                "isspace",
                "strip",
                "lstrip",
                "rstrip",
                "startswith",
                "endswith",
                "join",
                "find",
                "rfind",
                "replace",
                "split",
                "splitlines",
            }:
                if attr == "isdigit":
                    return "__pytra_str_isdigit(" + owner + ")"
                if attr == "isalpha":
                    return "__pytra_str_isalpha(" + owner + ")"
                if attr == "isalnum":
                    return "__pytra_str_isalnum(" + owner + ")"
                if attr == "isspace":
                    return (
                        "(("
                        + owner
                        + ' == " ") or ('
                        + owner
                        + ' == "\\t") or ('
                        + owner
                        + ' == "\\n") or ('
                        + owner
                        + ' == "\\r"))'
                    )
                if attr == "strip":
                    if len(rendered_args) == 0:
                        return "py_strip(" + owner + ")"
                    return "py_strip_chars(" + owner + ", " + rendered_args[0] + ")"
                if attr == "lstrip":
                    if len(rendered_args) == 0:
                        return "py_lstrip(" + owner + ")"
                    return "py_lstrip_chars(" + owner + ", " + rendered_args[0] + ")"
                if attr == "rstrip":
                    if len(rendered_args) == 0:
                        return "py_rstrip(" + owner + ")"
                    return "py_rstrip_chars(" + owner + ", " + rendered_args[0] + ")"
                if attr == "startswith" and len(rendered_args) >= 1:
                    return "py_startswith(" + owner + ", " + rendered_args[0] + ")"
                if attr == "endswith" and len(rendered_args) >= 1:
                    return "py_endswith(" + owner + ", " + rendered_args[0] + ")"
                if attr == "join" and len(rendered_args) >= 1:
                    return "py_join(" + owner + ", " + rendered_args[0] + ")"
                if attr == "find" and len(rendered_args) >= 1:
                    if len(rendered_args) >= 3:
                        return "py_find_window(" + owner + ", " + rendered_args[0] + ", " + rendered_args[1] + ", " + rendered_args[2] + ")"
                    return "py_find(" + owner + ", " + rendered_args[0] + ")"
                if attr == "rfind" and len(rendered_args) >= 1:
                    if len(rendered_args) >= 3:
                        return "py_rfind_window(" + owner + ", " + rendered_args[0] + ", " + rendered_args[1] + ", " + rendered_args[2] + ")"
                    return "py_rfind(" + owner + ", " + rendered_args[0] + ")"
                if attr == "replace" and len(rendered_args) >= 2:
                    return "py_replace(" + owner + ", " + rendered_args[0] + ", " + rendered_args[1] + ")"
                if attr == "split":
                    sep = rendered_args[0] if len(rendered_args) >= 1 else '" "'
                    maxsplit = rendered_args[1] if len(rendered_args) >= 2 else "-1"
                    return "py_split(" + owner + ", " + sep + ", " + maxsplit + ")"
                if attr == "splitlines":
                    return "py_splitlines(" + owner + ")"
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
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Lua backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Lua backend")
    body_any = east_doc.get("body") if isinstance(east_doc, dict) else None
    return LuaNativeEmitter(east_doc).transpile()

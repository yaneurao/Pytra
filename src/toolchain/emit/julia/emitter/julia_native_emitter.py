"""EAST3 -> Julia native emitter."""

from __future__ import annotations

from typing import Any

from toolchain.emit.common.emitter.code_emitter import (
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)

from toolchain.frontends.runtime_symbol_index import (
    canonical_runtime_module_id,
    lookup_runtime_module_symbols,
    lookup_runtime_symbol_doc,
    resolve_import_binding_doc,
)


_JULIA_KEYWORDS = {
    "abstract",
    "baremodule",
    "begin",
    "break",
    "catch",
    "const",
    "continue",
    "do",
    "else",
    "elseif",
    "end",
    "export",
    "false",
    "finally",
    "for",
    "function",
    "global",
    "if",
    "import",
    "in",
    "let",
    "local",
    "macro",
    "module",
    "mutable",
    "nothing",
    "quote",
    "return",
    "struct",
    "true",
    "try",
    "type",
    "using",
    "while",
}
# Julia Base built-in names that user-defined identifiers must not shadow.
# NOTE: Only include names that are NOT used as runtime/stdlib function names
# in Pytra, since _safe_ident cannot distinguish user definitions from runtime
# references.  Names like open/sin/cos/sqrt etc. are used by the runtime and
# must NOT be listed here.
_JULIA_RESERVED_BUILTINS = {
    "length", "size", "string", "display",
    "readline", "readlines",
    "push!", "pop!", "append!", "insert!", "deleteat!",
    "sort!", "reverse!", "filter", "reduce",
    "prod", "minimum", "maximum",
    "pairs", "haskey", "merge",
    "tryparse", "repr", "show",
    "rethrow",
    "collect",
    "sign",
    "trunc",
    "convert", "promote", "typeof", "isa",
    "deepcopy", "isequal",
    "iterate", "eltype", "first", "last", "step",
    "isempty", "isnothing", "ismissing",
    "fill", "zeros", "ones",
    "Array", "Vector", "Matrix",
}
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
    if out in _JULIA_KEYWORDS:
        out = "_" + out
    while out in _JULIA_RESERVED_BUILTINS:
        out = out + "_"
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
            continue
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
            "julia native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


def _julia_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\t", "\\t")
    out = out.replace("\r", "\\r")
    out = out.replace("\n", "\\n")
    out = out.replace("$", "\\$")
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
        return "^"  # Julia uses `xor()` but ^ is power; use xor() in render
    if op == "FloorDiv":
        return "÷"
    if op == "Pow":
        return "^"
    return "+"


def _cmp_symbol(op: str) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "!="
    if op == "Lt":
        return "<"
    if op == "LtE":
        return "<="
    if op == "Gt":
        return ">"
    if op == "GtE":
        return ">="
    return "=="


def _is_compile_time_std_import_symbol(module_id: str, symbol: str) -> bool:
    mod = canonical_runtime_module_id(module_id.strip())
    return mod == "pytra.std" and symbol in _COMPILETIME_STD_IMPORT_SYMBOLS


def _runtime_symbol_semantic_tag(runtime_module_id: str, runtime_symbol: str) -> str:
    symbol_doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    semantic_tag_any = symbol_doc.get("semantic_tag")
    if isinstance(semantic_tag_any, str):
        ss: str = semantic_tag_any
        return ss.strip()
    return ""


def _runtime_symbol_call_adapter_kind(runtime_module_id: str, runtime_symbol: str) -> str:
    symbol_doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    adapter_kind_any = symbol_doc.get("call_adapter_kind")
    if isinstance(adapter_kind_any, str):
        ak: str = adapter_kind_any
        return ak.strip()
    return ""


def _is_math_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_call_adapter_kind(runtime_module_id, runtime_symbol) in {
        "math.float_args",
        "math.value_getter",
    }


def _is_perf_counter_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol) == "stdlib.fn.perf_counter"


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


def _runtime_symbol_alias_expr(runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    if sym == "":
        return ""
    if _is_math_runtime_symbol(mod, sym):
        if sym == "pi":
            return "Base.MathConstants.pi"
        if sym == "e":
            return "Base.MathConstants.e"
        if sym == "inf":
            return "Inf"
        if sym == "nan":
            return "NaN"
        if sym == "sqrt":
            return "sqrt"
        if sym == "floor":
            return "(x -> Int(floor(x)))"
        if sym == "ceil":
            return "(x -> Int(ceil(x)))"
        if sym == "fabs" or sym == "abs":
            return "abs"
        if sym == "log":
            return "log"
        if sym == "sin":
            return "sin"
        if sym == "cos":
            return "cos"
        if sym == "tan":
            return "tan"
        if sym == "pow":
            return "((b, e) -> b^e)"
        return sym
    if _is_perf_counter_runtime_symbol(mod, sym):
        return "__pytra_perf_counter"
    if _is_sys_runtime_symbol(mod, sym):
        if sym == "argv":
            return "ARGS"
        if sym == "exit":
            return "exit"
        if sym == "write_stdout":
            return "(s -> print(s))"
        if sym == "write_stderr":
            return "(s -> print(stderr, s))"
        return sym
    return ""


def _runtime_module_alias_line(alias: str, runtime_module_id: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    if mod == "":
        return ""
    if mod in {"enum", "pytra.std.enum"}:
        return "# import " + alias + " (enum stub)"
    if mod in {"pytra.std.math", "math"}:
        return (
            alias + " = ("
            "sqrt=sqrt, sin=sin, cos=cos, tan=tan, "
            "asin=asin, acos=acos, atan=atan, atan2=atan, "
            "floor=x->Int(floor(x)), ceil=x->Int(ceil(x)), "
            "fabs=abs, abs=abs, log=log, log2=log2, log10=log10, exp=exp, "
            "pow=(b, e)->b^e, "
            "pi=Base.MathConstants.pi, e=Base.MathConstants.e, inf=Inf, nan=NaN"
            ")"
        )
    if mod == "pytra.std.argparse":
        return "# import " + alias + " (argparse stub)"
    if mod == "pytra.std.re":
        return "# import " + alias + " (re stub)"
    if mod == "pytra.std.json":
        return "# import " + alias + " (json stub)"
    if mod == "pytra.std.pathlib":
        return "# import " + alias + " (pathlib stub)"
    if mod == "pytra.std.collections":
        return "# import " + alias + " (collections stub)"
    if mod == "pytra.utils.png":
        return (
            'include(joinpath(@__DIR__, "utils", "png.jl"))\n'
            + alias + " = (write_rgb_png=write_rgb_png,)"
        )
    if mod == "pytra.utils.gif":
        return (
            'include(joinpath(@__DIR__, "utils", "gif.jl"))\n'
            + alias + " = (save_gif=save_gif, grayscale_palette=grayscale_palette)"
        )
    symbol_names = lookup_runtime_module_symbols(mod)
    if len(symbol_names) == 0:
        return ""
    return "# module alias: " + alias + " -> " + mod


def _runtime_symbol_alias_line(alias: str, runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    expr = _runtime_symbol_alias_expr(runtime_module_id, runtime_symbol)
    if expr != "":
        return alias + " = " + expr
    if mod in {"enum", "pytra.std.enum"}:
        if sym in {"Enum", "IntEnum", "IntFlag"}:
            return "# " + alias + " (enum stub)"
        return ""
    if mod == "pytra.std.argparse" and sym == "ArgumentParser":
        return "# " + alias + " (argparse stub)"
    if mod == "pytra.std.re" and sym == "sub":
        return alias + " = (_pattern, _repl, text) -> text"
    if mod == "pytra.std.json":
        if sym == "loads":
            return "# " + alias + " (json.loads stub)"
        if sym == "dumps":
            return "# " + alias + " (json.dumps stub)"
        return ""
    if mod == "pytra.std.pathlib" and sym == "Path":
        return "# " + alias + " (pathlib stub)"
    if mod == "pytra.std.collections" and sym == "deque":
        return "# " + alias + " (deque stub)"
    if mod == "pytra.utils.png" and sym != "":
        return "__PYTRA_INCLUDE_UTILS_PNG__"
    if mod == "pytra.utils.gif" and sym != "":
        return "__PYTRA_INCLUDE_UTILS_GIF__"
    if mod.startswith("pytra.utils.") and sym != "":
        return ""
    return ""


class JuliaNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=julia invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=julia invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=julia unsupported east_stage: " + str(ed.get("east_stage")))
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.imported_modules: set[str] = set()
        self.function_names: set[str] = set()
        self.relative_import_name_aliases: dict[str, str] = {}
        self.current_class_name: str = ""
        self.current_class_base_name: str = ""
        self._local_type_stack: list[dict[str, str]] = [{}]

    def _current_type_map(self) -> dict[str, str]:
        if len(self._local_type_stack) == 0:
            return {}
        return self._local_type_stack[-1]

    def _push_function_context(self, stmt: dict[str, Any], arg_names: list[str], arg_order: list[Any]) -> None:
        type_map: dict[str, str] = {}
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
            i += 1
        self._local_type_stack.append(type_map)

    def _pop_function_context(self) -> None:
        if len(self._local_type_stack) > 0:
            self._local_type_stack.pop()

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="# ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        self._emit_imports(body)
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
            return
        i = 0
        while i < len(body):
            self._emit_stmt(body[i])
            i += 1

    def _next_tmp_name(self, prefix: str = "__pytra_tmp") -> str:
        self.tmp_seq += 1
        return prefix + "_" + str(self.tmp_seq)

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

    def _const_int_literal(self, node_any: Any) -> int | None:
        if not isinstance(node_any, dict):
            return None
        nd: dict[str, Any] = node_any
        kind = nd.get("kind")
        if kind == "Constant":
            value = nd.get("value")
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            return None
        if kind == "UnaryOp" and str(nd.get("op")) == "USub":
            operand = self._const_int_literal(nd.get("operand"))
            if operand is None:
                return None
            return -operand
        return None

    def _resolved_runtime_call(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed: dict[str, Any] = expr_any
        runtime_call = ed.get("runtime_call")
        if isinstance(runtime_call, str) and runtime_call != "":
            return runtime_call
        resolved_runtime_call = ed.get("resolved_runtime_call")
        if isinstance(resolved_runtime_call, str) and resolved_runtime_call != "":
            return resolved_runtime_call
        return ""

    def _lookup_expr_type(self, node_any: Any) -> str:
        if not isinstance(node_any, dict):
            return ""
        nd: dict[str, Any] = node_any
        resolved = nd.get("resolved_type")
        if isinstance(resolved, str) and resolved != "":
            return resolved
        kind = nd.get("kind")
        if kind == "Name":
            safe_name = _safe_ident(nd.get("id"), "")
            if safe_name != "":
                mapped = self._current_type_map().get(safe_name)
                if isinstance(mapped, str) and mapped != "":
                    return mapped
        if kind == "Constant":
            value = nd.get("value")
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

    def _is_str_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        nd: dict[str, Any] = node_any
        if nd.get("kind") == "Constant" and isinstance(nd.get("value"), str):
            return True
        return self._lookup_expr_type(node_any) == "str"

    def _is_sequence_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        nd: dict[str, Any] = node_any
        kind = nd.get("kind")
        if kind in {"List", "Tuple", "JoinedStr", "Dict", "Set"}:
            return True
        if kind == "Constant" and isinstance(nd.get("value"), str):
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

    # ── scan ──

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

    # ── imports ──

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        import_lines: list[str] = []
        self._emit_line('include(joinpath(@__DIR__, "py_runtime.jl"))')
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
                    if mod == "pytra.typing" or mod == "typing":
                        continue
                    if mod.startswith("pytra.utils.") or mod.startswith("pytra.std."):
                        import_lines.append("# import " + mod + " as " + alias_txt + " (stub)")
                        continue
                    if mod.startswith("pytra."):
                        raise RuntimeError("lang=julia unresolved import module: " + mod)
                    import_lines.append("# import " + mod + " as " + alias_txt + " (not yet mapped)")
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
                            "py_assert_stdout(_expected, _fn) = true"
                        )
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_eq":
                        import_lines.append(alias_txt + "(a, b, _label=\"\") = (a == b)")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_true":
                        import_lines.append(alias_txt + "(v, _label=\"\") = !!(v)")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_all":
                        import_lines.append(
                            alias_txt + "(checks, _label=\"\") = all(checks)"
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
                    if mod.startswith("pytra.utils.") or mod.startswith("pytra.std."):
                        import_lines.append("# " + alias_txt + " = " + mod + "." + sym + " (stub)")
                        continue
                    if mod.startswith("pytra."):
                        raise RuntimeError("lang=julia unresolved import symbol: " + mod + "." + sym)
                    import_lines.append(
                        "# from " + mod + " import " + sym + " as " + alias_txt + " (not yet mapped)"
                    )
        # Deduplicate and resolve utils include markers
        seen_includes: set[str] = set()
        resolved_lines: list[str] = []
        for line in import_lines:
            if line == "__PYTRA_INCLUDE_UTILS_PNG__":
                if "utils_png" not in seen_includes:
                    seen_includes.add("utils_png")
                    resolved_lines.append('include(joinpath(@__DIR__, "utils", "png.jl"))')
                continue
            if line == "__PYTRA_INCLUDE_UTILS_GIF__":
                if "utils_gif" not in seen_includes:
                    seen_includes.add("utils_gif")
                    resolved_lines.append('include(joinpath(@__DIR__, "utils", "gif.jl"))')
                continue
            resolved_lines.append(line)
        for line in resolved_lines:
            self._emit_line(line)
        if len(resolved_lines) > 0:
            self._emit_line("")

    # ── statements ──

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        self._emit_leading_trivia(stmt, prefix="# ")
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
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "nothing"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type_any = stmt.get("decl_type")
                decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                if decl_type == "":
                    anno_any = stmt.get("annotation")
                    if isinstance(anno_any, str):
                        ann_str: str = anno_any
                        decl_type = ann_str.strip()
                if value_node is None and bool(stmt.get("declare")):
                    self._emit_line(target + " = nothing")
                    return
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                self._emit_line(target + " = " + value)
            else:
                self._emit_line(target + " = " + value)
            return
        if kind == "Assign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                td: dict[str, Any] = target_any
                if td.get("kind") == "Tuple":
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
            raise RuntimeError("lang=julia unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            if op == "Add":
                target_type = self._lookup_expr_type(stmt.get("target"))
                value_type = self._lookup_expr_type(stmt.get("value"))
                if target_type == "str" or value_type == "str":
                    self._emit_line(target + " = " + target + " * " + value)
                    return
            op_token = _binop_symbol(op)
            if op == "BitXor":
                self._emit_line(target + " = xor(" + target + ", " + value + ")")
                return
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
                    self._emit_line("continue")
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
            self._emit_line("try")
            self.indent += 1
            body = self._dict_list(stmt.get("body"))
            for sub in body:
                self._emit_stmt(sub)
            self.indent -= 1
            handlers_any = stmt.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            if len(handlers) > 0:
                self._emit_line("catch __pytra_exc")
                self.indent += 1
                for h in handlers:
                    if isinstance(h, dict):
                        h_body = self._dict_list(h.get("body"))
                        for sub in h_body:
                            self._emit_stmt(sub)
                self.indent -= 1
            finalbody = self._dict_list(stmt.get("finalbody"))
            if len(finalbody) > 0:
                self._emit_line("finally")
                self.indent += 1
                for sub in finalbody:
                    self._emit_stmt(sub)
                self.indent -= 1
            self._emit_line("end")
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
            return
        if kind == "TypeAlias":
            return
        if kind == "Yield":
            self._emit_line("# yield (not supported)")
            return
        if kind == "VarDecl":
            self._emit_var_decl(stmt)
            return
        raise RuntimeError("lang=julia unsupported stmt kind: " + str(kind))

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node)."""
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type_any = stmt.get("type")
        var_type = var_type_any.strip() if isinstance(var_type_any, str) else ""
        if var_type != "":
            self._current_type_map()[name] = var_type
        self._emit_line(name + " = nothing")

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
        self._emit_line("if " + test)
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        orelse = self._dict_list(stmt.get("orelse"))
        if len(orelse) > 0:
            if len(orelse) == 1 and orelse[0].get("kind") == "If":
                elseif_stmt = orelse[0]
                elseif_test = self._render_cond_expr(elseif_stmt.get("test"))
                self._emit_line("elseif " + elseif_test)
                self.indent += 1
                self._emit_block(elseif_stmt.get("body"))
                self.indent -= 1
                inner_orelse = self._dict_list(elseif_stmt.get("orelse"))
                if len(inner_orelse) > 0:
                    self._emit_line("else")
                    self.indent += 1
                    for sub in inner_orelse:
                        self._emit_stmt(sub)
                    self.indent -= 1
            else:
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

        # Collect fields
        body = self._dict_list(stmt.get("body"))
        fields: list[str] = []
        for sub in body:
            if sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    fields.append(_safe_ident(target_any.get("id"), "field"))
            if sub.get("kind") == "FunctionDef" and sub.get("name") == "__init__":
                init_body = self._dict_list(sub.get("body"))
                for init_stmt in init_body:
                    if init_stmt.get("kind") in {"AnnAssign", "Assign"}:
                        t_any = init_stmt.get("target")
                        if isinstance(t_any, dict) and t_any.get("kind") == "Attribute":
                            attr_val = t_any.get("value")
                            if isinstance(attr_val, dict) and attr_val.get("kind") == "Name":
                                if str(attr_val.get("id")) == "self":
                                    field_name = _safe_ident(t_any.get("attr"), "field")
                                    if field_name not in fields:
                                        fields.append(field_name)

        # Emit struct
        if base_name != "":
            self._emit_line("# inherits from " + base_name)
        self._emit_line("mutable struct " + cls_name)
        self.indent += 1
        if len(fields) > 0:
            for f in fields:
                self._emit_line(f)
        self.indent -= 1
        self._emit_line("end")
        self._emit_line("")

        # Emit constructor and methods
        has_init = False
        for sub in body:
            if sub.get("kind") != "FunctionDef":
                continue
            if sub.get("name") == "__init__":
                has_init = True
            self._emit_class_method(cls_name, base_name, sub)

        if not has_init:
            # Default constructor already generated by Julia struct
            pass

    def _emit_class_method(self, cls_name: str, base_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        for i_idx, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i_idx == 0 and arg_name == "self":
                args.append("self::" + cls_name)
                continue
            args.append(arg_name)
        prev_class = self.current_class_name
        prev_base = self.current_class_base_name
        self.current_class_name = cls_name
        self.current_class_base_name = base_name

        if method_name == "__init__":
            # Constructor: emit as a function returning new instance
            init_args = [a for a in args if not a.startswith("self")]
            self._emit_line("function " + cls_name + "(" + ", ".join(init_args) + ")")
            self.indent += 1
            self._emit_line("self = " + cls_name + "(" + ", ".join(["nothing" for _ in self._get_class_fields(stmt)]) + ")")
            self._push_function_context(stmt, [_safe_ident(a, "arg") for a in arg_order[1:]], arg_order[1:])
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._emit_line("return self")
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")
        else:
            self._emit_line("function " + method_name + "(" + ", ".join(args) + ")")
            self.indent += 1
            self._push_function_context(stmt, [_safe_ident(a.split("::")[0], "arg") for a in args], arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self.indent -= 1
            self._emit_line("end")
            self._emit_line("")
        self.current_class_name = prev_class
        self.current_class_base_name = prev_base

    def _get_class_fields(self, init_stmt: dict[str, Any]) -> list[str]:
        fields: list[str] = []
        init_body = self._dict_list(init_stmt.get("body"))
        for stmt in init_body:
            if stmt.get("kind") in {"AnnAssign", "Assign"}:
                t_any = stmt.get("target")
                if isinstance(t_any, dict) and t_any.get("kind") == "Attribute":
                    attr_val = t_any.get("value")
                    if isinstance(attr_val, dict) and attr_val.get("kind") == "Name":
                        if str(attr_val.get("id")) == "self":
                            field_name = _safe_ident(t_any.get("attr"), "field")
                            if field_name not in fields:
                                fields.append(field_name)
        return fields

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")

        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=julia unsupported forcore static_fastpath shape")
            ipd: dict[str, Any] = iter_plan
            if ipd.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=julia unsupported forcore static_fastpath shape")
            start = self._render_expr(ipd.get("start"))
            stop = self._render_expr(ipd.get("stop"))
            step = self._render_expr(ipd.get("step"))
            step_const = self._const_int_literal(ipd.get("step"))
            range_mode = str(ipd.get("range_mode") or "")
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
            # Julia range: start:step:stop (inclusive), Python range is exclusive at stop
            if range_mode == "ascending":
                upper = stop + " - 1" if self._is_simple_bound_expr(ipd.get("stop")) else "(" + stop + ") - 1"
                if step_const == 1:
                    self._emit_line("for " + target_name + " in " + start + ":" + upper)
                else:
                    self._emit_line("for " + target_name + " in " + start + ":" + step + ":" + upper)
            elif range_mode == "descending":
                lower = "(" + stop + ") + 1"
                self._emit_line("for " + target_name + " in " + start + ":" + step + ":" + lower)
            else:
                # Dynamic: use a helper
                self._emit_line("for " + target_name + " in __pytra_range(" + start + ", " + stop + ", " + step + ")")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("end")
            return

        if iter_mode == "runtime_protocol":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=julia unsupported forcore runtime shape")
            ipd2: dict[str, Any] = iter_plan
            iter_expr_node = ipd2.get("iter_expr")
            iter_expr = self._render_expr(iter_expr_node)
            # Python bytes/bytearray iteration yields int; Julia UInt8 overflows on bit ops
            iter_type = self._lookup_expr_type(iter_expr_node) if isinstance(iter_expr_node, dict) else ""
            if iter_type in {"bytes", "bytearray"}:
                iter_expr = "__pytra_iter_ints(" + iter_expr + ")"
            tuple_target = isinstance(target_plan, dict) and target_plan.get("kind") == "TupleTarget"
            iter_name = target_name
            if tuple_target:
                iter_name = self._next_tmp_name("__it")
            self._emit_line("for " + iter_name + " in " + iter_expr)
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
                            self._emit_line(local_name + " = " + iter_name + "[" + str(i + 1) + "]")
                        i += 1
                else:
                    elems_any = target_plan.get("elements")
                    elems = elems_any if isinstance(elems_any, list) else []
                    i = 0
                    while i < len(elems):
                        elem = elems[i]
                        if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                            local_name = _safe_ident(elem.get("id"), "it")
                            self._emit_line(local_name + " = " + iter_name + "[" + str(i + 1) + "]")
                        i += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("end")
            return
        raise RuntimeError("lang=julia unsupported forcore iter_mode: " + iter_mode)

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("while " + test)
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("end")

    def _emit_tuple_assign(self, tuple_target: dict[str, Any], value_any: Any) -> None:
        elems_any = tuple_target.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        if len(elems) == 0:
            raise RuntimeError("lang=julia unsupported tuple assign target: empty")
        targets: list[str] = []
        i = 0
        while i < len(elems):
            targets.append(self._render_target(elems[i]))
            i += 1
        value = self._render_expr(value_any)
        # Julia supports tuple unpacking via (a, b, ...) = expr
        self._emit_line("(" + ", ".join(targets) + ") = " + value)

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_target(stmt.get("left"))
        right = self._render_target(stmt.get("right"))
        self._emit_line("(" + left + ", " + right + ") = (" + right + ", " + left + ")")

    # ── targets ──

    def _render_target(self, target_any: Any) -> str:
        if not isinstance(target_any, dict):
            return "nothing"
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
                    raise RuntimeError("lang=julia unsupported slice assignment target")
            index = self._render_expr(index_node)
            owner_type = ""
            if isinstance(owner_node, dict):
                rt_any = owner_node.get("resolved_type")
                if isinstance(rt_any, str):
                    owner_type = rt_any
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            # Julia is 1-indexed
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if idx_const >= 0:
                    return owner + "[" + str(idx_const + 1) + "]"
                return owner + "[end + " + str(idx_const + 1) + "]"
            return owner + "[__pytra_idx(" + index + ", length(" + owner + "))]"
        target_kind = tad.get("kind")
        raise RuntimeError("lang=julia unsupported assignment target: " + str(target_kind))

    # ── expressions ──

    def _render_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "nothing"
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            return self._render_constant(ed.get("value"))
        if kind == "Name":
            return self._render_name_expr(expr_any)
        if kind == "BinOp":
            left_node = ed.get("left")
            right_node = ed.get("right")
            left = self._render_expr(left_node)
            right = self._render_expr(right_node)
            op_raw = str(ed.get("op"))
            if op_raw == "Add":
                expr_resolved = ed.get("resolved_type")
                if (
                    (isinstance(expr_resolved, str) and expr_resolved == "str")
                    or self._is_str_expr(left_node)
                    or self._is_str_expr(right_node)
                ):
                    return "(" + left + " * " + right + ")"
            if op_raw == "Mult" and (self._is_sequence_expr(left_node) or self._is_sequence_expr(right_node)):
                return "__pytra_repeat_seq(" + left + ", " + right + ")"
            if op_raw == "BitXor":
                return "xor(" + left + ", " + right + ")"
            op = _binop_symbol(op_raw)
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
                return "(!(" + operand + "))"
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
                return "!__pytra_contains(" + right + ", " + left + ")"
            if op0 == "Is":
                return "(" + left + " === " + right + ")"
            if op0 == "IsNot":
                return "(" + left + " !== " + right + ")"
            return "(" + left + " " + _cmp_symbol(op0) + " " + right + ")"
        if kind == "BoolOp":
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "false"
            op = str(ed.get("op"))
            delim = " && " if op == "And" else " || "
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
            if len(names) == 1:
                return names[0] + " -> " + body
            return "((" + ", ".join(names) + ") -> " + body + ")"
        if kind == "List":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            if len(out) == 0:
                return "Any[]"
            return "[" + ", ".join(out) + "]"
        if kind == "Tuple":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "(" + ", ".join(out) + ")"
        if kind == "Set":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "Set([" + ", ".join(out) + "])"
        if kind == "ListComp":
            gens_any = ed.get("generators")
            gens = gens_any if isinstance(gens_any, list) else []
            if len(gens) != 1 or not isinstance(gens[0], dict):
                return "Any[]"
            gen = gens[0]
            target_any = gen.get("target")
            iter_any = gen.get("iter")
            if not isinstance(target_any, dict):
                return "Any[]"
            td2: dict[str, Any] = target_any
            if not isinstance(iter_any, dict):
                return "Any[]"
            itd: dict[str, Any] = iter_any
            elt = self._render_expr(ed.get("elt"))
            if td2.get("kind") != "Name":
                return "Any[]"
            loop_var = _safe_ident(td2.get("id"), "__lc_i")
            if itd.get("kind") == "RangeExpr":
                start = self._render_expr(itd.get("start"))
                stop = self._render_expr(itd.get("stop"))
                step = self._render_expr(itd.get("step"))
                step_const = self._const_int_literal(itd.get("step"))
                if step_const == 1:
                    range_expr = start + ":(" + stop + " - 1)"
                else:
                    range_expr = start + ":" + step + ":(" + stop + " - 1)"
            else:
                range_expr = self._render_expr(iter_any)
            cond_expr = ""
            ifs_any = gen.get("ifs")
            if isinstance(ifs_any, list) and len(ifs_any) > 0:
                cond_parts: list[str] = []
                for cond_any in ifs_any:
                    cond_parts.append(self._render_expr(cond_any))
                cond_expr = " && ".join(cond_parts)
            if cond_expr != "":
                return "[" + elt + " for " + loop_var + " in " + range_expr + " if " + cond_expr + "]"
            return "[" + elt + " for " + loop_var + " in " + range_expr + "]"
        if kind == "SetComp":
            gens_any = ed.get("generators")
            gens = gens_any if isinstance(gens_any, list) else []
            if len(gens) != 1 or not isinstance(gens[0], dict):
                return "Set{Any}()"
            gen = gens[0]
            target_any = gen.get("target")
            iter_any = gen.get("iter")
            if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
                return "Set{Any}()"
            td_sc: dict[str, Any] = target_any
            if td_sc.get("kind") != "Name":
                return "Set{Any}()"
            elt = self._render_expr(ed.get("elt"))
            loop_var = _safe_ident(td_sc.get("id"), "__sc_i")
            range_expr = self._render_expr(iter_any)
            cond_expr = ""
            ifs_any = gen.get("ifs")
            if isinstance(ifs_any, list) and len(ifs_any) > 0:
                cond_parts_sc: list[str] = []
                for cond_any in ifs_any:
                    cond_parts_sc.append(self._render_expr(cond_any))
                cond_expr = " && ".join(cond_parts_sc)
            if cond_expr != "":
                return "Set([" + elt + " for " + loop_var + " in " + range_expr + " if " + cond_expr + "])"
            return "Set([" + elt + " for " + loop_var + " in " + range_expr + "])"
        if kind == "DictComp":
            gens_any = ed.get("generators")
            gens = gens_any if isinstance(gens_any, list) else []
            if len(gens) != 1 or not isinstance(gens[0], dict):
                return "Dict{Any,Any}()"
            gen = gens[0]
            target_any = gen.get("target")
            iter_any = gen.get("iter")
            if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
                return "Dict{Any,Any}()"
            td_dc: dict[str, Any] = target_any
            if td_dc.get("kind") != "Name":
                return "Dict{Any,Any}()"
            key_expr = self._render_expr(ed.get("key"))
            val_expr = self._render_expr(ed.get("value"))
            loop_var = _safe_ident(td_dc.get("id"), "__dc_i")
            range_expr = self._render_expr(iter_any)
            cond_expr = ""
            ifs_any = gen.get("ifs")
            if isinstance(ifs_any, list) and len(ifs_any) > 0:
                cond_parts_dc: list[str] = []
                for cond_any in ifs_any:
                    cond_parts_dc.append(self._render_expr(cond_any))
                cond_expr = " && ".join(cond_parts_dc)
            if cond_expr != "":
                return "Dict(" + key_expr + " => " + val_expr + " for " + loop_var + " in " + range_expr + " if " + cond_expr + ")"
            return "Dict(" + key_expr + " => " + val_expr + " for " + loop_var + " in " + range_expr + ")"
        if kind == "Dict":
            keys_any = ed.get("keys")
            values_any = ed.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            values = values_any if isinstance(values_any, list) else []
            if len(keys) == 0 or len(values) == 0:
                entries_any = ed.get("entries")
                entries = entries_any if isinstance(entries_any, list) else []
                if len(entries) == 0:
                    return "Dict{Any,Any}()"
                pairs: list[str] = []
                for ent in entries:
                    if isinstance(ent, dict):
                        k = self._render_expr(ent.get("key"))
                        v = self._render_expr(ent.get("value"))
                        pairs.append(k + " => " + v)
                if len(pairs) == 0:
                    return "Dict{Any,Any}()"
                return "Dict(" + ", ".join(pairs) + ")"
            pairs2: list[str] = []
            i = 0
            while i < len(keys) and i < len(values):
                k = self._render_expr(keys[i])
                v = self._render_expr(values[i])
                pairs2.append(k + " => " + v)
                i += 1
            return "Dict(" + ", ".join(pairs2) + ")"
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
                upper = self._render_expr(upper_node) if isinstance(upper_node, dict) else "nothing"
                if owner_type == "str":
                    if upper == "nothing":
                        return owner + "[(" + lower + " + 1):end]"
                    return owner + "[(" + lower + " + 1):" + upper + "]"
                if upper == "nothing":
                    return owner + "[(" + lower + " + 1):end]"
                return owner + "[(" + lower + " + 1):" + upper + "]"
            index = self._render_expr(index_node)
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            # Julia is 1-indexed
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if owner_type == "str":
                    if idx_const >= 0:
                        pos = str(idx_const + 1)
                        return "string(" + owner + "[" + pos + "])"
                    return "string(" + owner + "[end + " + str(idx_const + 1) + "])"
                if idx_const >= 0:
                    return owner + "[" + str(idx_const + 1) + "]"
                return owner + "[end + " + str(idx_const + 1) + "]"
            if owner_type == "str":
                return "string(" + owner + "[__pytra_idx(" + index + ", length(" + owner + "))])"
            return owner + "[__pytra_idx(" + index + ", length(" + owner + "))]"
        if kind == "Attribute":
            owner = self._render_expr(ed.get("value"))
            attr = _safe_ident(ed.get("attr"), "field")
            return owner + "." + attr
        if kind == "IsInstance":
            value = self._render_expr(ed.get("value"))
            expected_any = ed.get("expected_type_id")
            if isinstance(expected_any, dict) and expected_any.get("kind") == "Name":
                expected = _safe_ident(expected_any.get("id"), "object")
                if expected in {"int", "int64"}:
                    return "(isa(" + value + ", Integer))"
                if expected in {"float", "float64"}:
                    return "(isa(" + value + ", AbstractFloat))"
                if expected in {"str", "string"}:
                    return "(isa(" + value + ", AbstractString))"
                if expected in {"bool"}:
                    return "(isa(" + value + ", Bool))"
                if expected in {"list"}:
                    return "(isa(" + value + ", AbstractVector))"
                if expected in {"dict"}:
                    return "(isa(" + value + ", AbstractDict))"
                if expected in {"tuple"}:
                    return "(isa(" + value + ", Tuple))"
                if expected in {"set"}:
                    return "(isa(" + value + ", AbstractSet))"
                if expected in self.class_names:
                    return "(isa(" + value + ", " + expected + "))"
            return "false"
        if kind == "IsSubtype" or kind == "IsSubclass":
            actual = self._render_expr(ed.get("actual_type_id"))
            expected = self._render_expr(ed.get("expected_type_id"))
            return "(" + actual + " <: " + expected + ")"
        if kind == "IfExp":
            test = self._render_expr(ed.get("test"))
            body = self._render_expr(ed.get("body"))
            orelse = self._render_expr(ed.get("orelse"))
            return "(__pytra_truthy(" + test + ") ? (" + body + ") : (" + orelse + "))"
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
                    parts.append("string(" + self._render_expr(item_d.get("value")) + ")")
                else:
                    parts.append("string(" + self._render_expr(item_d) + ")")
            return "(" + " * ".join(parts) + ")"
        if kind == "Box":
            return self._render_expr(ed.get("value"))
        if kind == "Unbox":
            return self._render_expr(ed.get("value"))
        if kind == "ObjTypeId":
            return "typeof(" + self._render_expr(ed.get("value")) + ")"
        if kind == "ObjStr":
            return "string(" + self._render_expr(ed.get("value")) + ")"
        if kind == "ObjBool":
            val = self._render_expr(ed.get("value"))
            resolved = ed.get("resolved_type")
            if isinstance(resolved, str):
                if resolved in {"bool"}:
                    return "__pytra_truthy(" + val + ")"
                if resolved in {"int", "int64", "float", "float64"}:
                    return "((" + val + ") != 0)"
                if resolved == "str":
                    return "(length(" + val + ") != 0)"
                if resolved.startswith("list[") or resolved.startswith("tuple[") or resolved.startswith("dict[") or resolved.startswith("set["):
                    return "(!isempty(" + val + "))"
            return "__pytra_truthy(" + val + ")"
        if kind == "ObjLen":
            return "length(" + self._render_expr(ed.get("value")) + ")"
        raise RuntimeError("lang=julia unsupported expr kind: " + str(kind))

    def _render_call(self, expr: dict[str, Any]) -> str:
        func_any = expr.get("func")
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        keywords_any = expr.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(self._render_expr(arg))
        kw_values_in_order: list[str] = []
        for kw_any in keywords:
            if not isinstance(kw_any, dict):
                continue
            key_any = kw_any.get("arg")
            if not isinstance(key_any, str) or key_any == "":
                continue
            rendered_kw = self._render_expr(kw_any.get("value"))
            kw_values_in_order.append(rendered_kw)

        semantic_tag_any = expr.get("semantic_tag")
        semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
        runtime_call = self._resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and semantic_tag != "stdlib.symbol.Path" and runtime_call == "":
            raise RuntimeError("lang=julia unresolved stdlib runtime call: " + semantic_tag)

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
                return "Float64(" + rendered_args[0] + ")"
            if fn_name == "bool":
                if len(rendered_args) == 0:
                    return "false"
                return "__pytra_truthy(" + rendered_args[0] + ")"
            if fn_name == "str":
                if len(rendered_args) == 0:
                    return '""'
                return "string(" + rendered_args[0] + ")"
            if fn_name == "len":
                if len(rendered_args) == 0:
                    return "0"
                return "length(" + rendered_args[0] + ")"
            if fn_name == "max":
                if len(rendered_args) == 0:
                    return "0"
                return "max(" + ", ".join(rendered_args) + ")"
            if fn_name == "min":
                if len(rendered_args) == 0:
                    return "0"
                return "min(" + ", ".join(rendered_args) + ")"
            if fn_name == "abs":
                if len(rendered_args) == 0:
                    return "0"
                return "abs(" + rendered_args[0] + ")"
            if fn_name == "enumerate":
                if len(rendered_args) == 0:
                    return "Any[]"
                return "__pytra_enumerate(" + rendered_args[0] + ")"
            if fn_name == "sorted":
                if len(rendered_args) == 0:
                    return "Any[]"
                return "sort(" + rendered_args[0] + ")"
            if fn_name == "reversed":
                if len(rendered_args) == 0:
                    return "Any[]"
                return "reverse(" + rendered_args[0] + ")"
            if fn_name == "zip":
                return "collect(zip(" + ", ".join(rendered_args) + "))"
            if fn_name == "range":
                if len(rendered_args) == 1:
                    return "0:(" + rendered_args[0] + " - 1)"
                if len(rendered_args) == 2:
                    return rendered_args[0] + ":(" + rendered_args[1] + " - 1)"
                if len(rendered_args) == 3:
                    return rendered_args[0] + ":" + rendered_args[2] + ":(" + rendered_args[1] + " - 1)"
                return "0:-1"
            if fn_name == "bytearray":
                if len(rendered_args) == 0:
                    return "UInt8[]"
                return "__pytra_bytearray(" + rendered_args[0] + ")"
            if fn_name == "bytes":
                if len(rendered_args) == 0:
                    return "UInt8[]"
                return "__pytra_bytes(" + rendered_args[0] + ")"
            if fn_name == "isinstance":
                if len(rendered_args) >= 2:
                    return "isa(" + rendered_args[0] + ", " + rendered_args[1] + ")"
            if fn_name == "open":
                return "py_open(" + ", ".join(rendered_args) + ")"
            if fn_name in self.class_names:
                return fn_name + "(" + ", ".join(rendered_args) + ")"
            rendered_name = self._render_name_expr(func_any)
            return rendered_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"

        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_node = func_any.get("value")
            attr = _safe_ident(func_any.get("attr"), "call")
            # super() calls
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and super_func.get("kind") == "Name":
                    super_name = str(super_func.get("id"))
                    if super_name in {"super", "_super"}:
                        if attr == "__init__":
                            return "nothing"
                        if self.current_class_base_name != "":
                            return self.current_class_base_name + "_" + attr + "(" + ", ".join(["self"] + rendered_args) + ")"
            owner = self._render_expr(owner_node)
            owner_type = self._lookup_expr_type(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in self.imported_modules:
                    return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            # dict.get
            if attr == "get" and len(rendered_args) >= 1:
                key = rendered_args[0]
                default = rendered_args[1] if len(rendered_args) >= 2 else "nothing"
                return "get(" + owner + ", " + key + ", " + default + ")"
            # list methods
            if attr == "append" and len(rendered_args) == 1:
                return "push!(" + owner + ", " + rendered_args[0] + ")"
            if attr == "pop":
                if len(rendered_args) == 0:
                    return "pop!(" + owner + ")"
                return "splice!(" + owner + ", (" + rendered_args[0] + ") + 1)"
            if attr == "insert" and len(rendered_args) == 2:
                return "insert!(" + owner + ", (" + rendered_args[0] + ") + 1, " + rendered_args[1] + ")"
            if attr == "extend" and len(rendered_args) == 1:
                return "append!(" + owner + ", " + rendered_args[0] + ")"
            if attr == "clear":
                return "empty!(" + owner + ")"
            if attr == "copy":
                return "copy(" + owner + ")"
            if attr == "reverse":
                return "reverse!(" + owner + ")"
            if attr == "sort":
                return "sort!(" + owner + ")"
            if attr == "index" and len(rendered_args) >= 1:
                return "(findfirst(x -> x == " + rendered_args[0] + ", " + owner + ") - 1)"
            if attr == "count" and len(rendered_args) >= 1:
                return "count(x -> x == " + rendered_args[0] + ", " + owner + ")"
            # string methods
            if owner_type == "str" or attr in {
                "isdigit", "isalpha", "isalnum", "strip", "lstrip", "rstrip",
                "startswith", "endswith", "join", "find", "rfind", "replace",
                "split", "splitlines", "upper", "lower",
            }:
                if attr == "upper":
                    return "uppercase(" + owner + ")"
                if attr == "lower":
                    return "lowercase(" + owner + ")"
                if attr == "strip":
                    return "strip(" + owner + ")"
                if attr == "lstrip":
                    return "lstrip(" + owner + ")"
                if attr == "rstrip":
                    return "rstrip(" + owner + ")"
                if attr == "startswith" and len(rendered_args) >= 1:
                    return "startswith(" + owner + ", " + rendered_args[0] + ")"
                if attr == "endswith" and len(rendered_args) >= 1:
                    return "endswith(" + owner + ", " + rendered_args[0] + ")"
                if attr == "join" and len(rendered_args) >= 1:
                    return "join(" + rendered_args[0] + ", " + owner + ")"
                if attr == "find" and len(rendered_args) >= 1:
                    return "__pytra_str_find(" + owner + ", " + rendered_args[0] + ")"
                if attr == "rfind" and len(rendered_args) >= 1:
                    return "__pytra_str_rfind(" + owner + ", " + rendered_args[0] + ")"
                if attr == "replace" and len(rendered_args) >= 2:
                    return "replace(" + owner + ", " + rendered_args[0] + " => " + rendered_args[1] + ")"
                if attr == "split":
                    if len(rendered_args) == 0:
                        return "split(" + owner + ")"
                    return "split(" + owner + ", " + rendered_args[0] + ")"
                if attr == "splitlines":
                    return "split(" + owner + ", \"\\n\")"
                if attr == "isdigit":
                    return "__pytra_str_isdigit(" + owner + ")"
                if attr == "isalpha":
                    return "__pytra_str_isalpha(" + owner + ")"
                if attr == "isalnum":
                    return "__pytra_str_isalnum(" + owner + ")"
            # dict methods
            if attr == "keys":
                return "collect(keys(" + owner + "))"
            if attr == "values":
                return "collect(values(" + owner + "))"
            if attr == "items":
                return "collect(pairs(" + owner + "))"
            if attr == "update" and len(rendered_args) == 1:
                return "merge!(" + owner + ", " + rendered_args[0] + ")"
            # Method call with self
            if self.current_class_name != "" and isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                if str(owner_node.get("id")) == "self":
                    return attr + "(" + ", ".join([owner] + rendered_args + kw_values_in_order) + ")"
            return attr + "(" + ", ".join([owner] + rendered_args + kw_values_in_order) + ")"

        # Lambda or other callable expression
        fn_expr = self._render_expr(func_any)
        return "(" + fn_expr + ")(" + ", ".join(rendered_args + kw_values_in_order) + ")"

    def _render_name_expr(self, expr_any: dict[str, Any]) -> str:
        ident = _safe_ident(expr_any.get("id"), "value")
        if ident == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
            ident = "__pytra_main"
        return self.relative_import_name_aliases.get(ident, ident)

    def _render_constant(self, value: Any) -> str:
        if value is None:
            return "nothing"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            return _julia_string(value)
        return "nothing"


def transpile_to_julia_native(east_doc: dict[str, Any]) -> str:
    """EAST3 ドキュメントを Julia native ソースへ変換する。"""
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Julia backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Julia backend")
    return JuliaNativeEmitter(east_doc).transpile()

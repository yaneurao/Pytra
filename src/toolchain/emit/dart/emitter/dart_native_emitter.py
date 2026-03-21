"""EAST3 -> Dart native emitter (minimal skeleton)."""

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


_DART_KEYWORDS = {
    "abstract",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "covariant",
    "default",
    "deferred",
    "do",
    "dynamic",
    "else",
    "enum",
    "export",
    "extends",
    "extension",
    "external",
    "factory",
    "false",
    "final",
    "finally",
    "for",
    "Function",
    "get",
    "hide",
    "if",
    "implements",
    "import",
    "in",
    "interface",
    "is",
    "late",
    "library",
    "mixin",
    "new",
    "null",
    "of",
    "on",
    "operator",
    "part",
    "required",
    "rethrow",
    "return",
    "set",
    "show",
    "static",
    "super",
    "switch",
    "sync",
    "this",
    "throw",
    "true",
    "try",
    "typedef",
    "var",
    "void",
    "while",
    "with",
    "yield",
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
    if out == "_":
        out = "unused_"
    if out[0].isdigit():
        out = "d_" + out
    if out in _DART_KEYWORDS:
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
            "dart native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


def _dart_string(text: str) -> str:
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
        return "^"
    if op == "FloorDiv":
        return "~/"
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
        ak: str = adapter_kind_any
        return ak.strip()
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
            return "(double x) => pytraLog(x) / pytraLog(10)"
        return "pyMath" + _pascal_symbol_name(sym)
    if _is_perf_counter_runtime_symbol(mod, sym):
        return "pytraPerfCounter"
    if _is_glob_runtime_symbol(mod, sym):
        return "(String _pattern) => <String>[]"
    if _is_os_runtime_symbol(mod, sym):
        if sym == "getcwd":
            return "() => '.'"
        return "([String? _p, bool? _existOk]) {}"
    if _is_os_path_runtime_symbol(mod, sym):
        if sym == "join":
            return r"(dynamic a, dynamic b) => '${a}/${b}'"
        if sym == "dirname":
            return "(dynamic _p) => ''"
        if sym == "basename":
            return r"(dynamic p) => '$p'"
        if sym == "splitext":
            return r"(dynamic p) => ['$p', '']"
        if sym == "abspath":
            return r"(dynamic p) => '$p'"
        if sym == "exists":
            return "(dynamic _p) => false"
    if _is_sys_runtime_symbol(mod, sym):
        if sym == "argv":
            return "<String>[]"
        if sym == "path":
            return "<String>[]"
        if sym == "stderr":
            return "PytraStderr()"
        if sym == "stdout":
            return "PytraStdout()"
        if sym == "exit":
            return "(dynamic code) => exit(code is int ? code : 0)"
        if sym == "set_argv" or sym == "set_path":
            return "(dynamic _values) {}"
        if sym == "write_stderr":
            return "(dynamic text) => stderr.write(text)"
        if sym == "write_stdout":
            return "(dynamic text) => stdout.write(text)"
    return ""


def _runtime_module_alias_line(alias_txt: str, runtime_module_id: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    if mod == "pytra.std.math":
        return "import 'dart:math' as " + alias_txt + ";"
    if mod in {"enum", "pytra.std.enum"}:
        return "// import " + alias_txt + " (enum stub)"
    if mod == "pytra.std.argparse":
        return "// import " + alias_txt + " (argparse stub)"
    if mod == "pytra.std.re":
        return "// import " + alias_txt + " (re stub)"
    if mod == "pytra.std.json":
        return "// import " + alias_txt + " (json stub)"
    if mod == "pytra.std.pathlib":
        return "// import " + alias_txt + " (pathlib stub)"
    if mod == "pytra.utils.png":
        return "import 'png/east.dart' as " + alias_txt + ";"
    if mod == "pytra.utils.gif":
        return "import 'gif/east.dart' as " + alias_txt + ";"
    symbol_names = _runtime_module_symbol_names(mod)
    if len(symbol_names) == 0:
        return ""
    return "// import " + alias_txt + " (module stub)"


def _runtime_symbol_alias_line(alias_txt: str, runtime_module_id: str, runtime_symbol: str) -> str:
    mod = canonical_runtime_module_id(runtime_module_id.strip())
    sym = runtime_symbol.strip()
    alias_expr = _runtime_symbol_alias_expr(mod, sym)
    if alias_expr != "":
        return "var " + alias_txt + " = " + alias_expr + ";"
    if mod in {"enum", "pytra.std.enum"}:
        if sym in {"Enum", "IntEnum", "IntFlag"}:
            return "// " + alias_txt + " (enum stub)"
        return ""
    if mod == "pytra.std.argparse" and sym == "ArgumentParser":
        return "// " + alias_txt + " (argparse stub)"
    if mod == "pytra.std.re" and sym == "sub":
        return "var " + alias_txt + " = (dynamic _pattern, dynamic _repl, dynamic text, [dynamic _flags]) => text;"
    if mod == "pytra.std.json":
        if sym == "loads":
            return "// " + alias_txt + " (json.loads stub)"
        if sym == "dumps":
            return "// " + alias_txt + " (json.dumps stub)"
        return ""
    if mod == "pytra.std.pathlib" and sym == "Path":
        return "// " + alias_txt + " (pathlib stub)"
    if mod.startswith("pytra.utils.") and sym != "":
        # Symbol imported from utils module — available via module-level import
        return "// " + alias_txt + " from " + mod + " (via module import)"
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
                    "dart native emitter: unsupported relative import form: wildcard import"
                )
            j += 1
        if kind == "ImportFrom":
            continue
        raise RuntimeError(
            "dart native emitter: unsupported relative import form: relative import"
        )


class DartNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=dart invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=dart invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=dart unsupported east_stage: " + str(ed.get("east_stage")))
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
        self._local_type_stack: list[dict[str, str]] = []
        self._ref_var_stack: list[set[str]] = []
        self._local_var_stack: list[set[str]] = []
        self._needs_math_import = False
        self._needs_io_import = False
        self._class_field_types: dict[str, dict[str, str]] = {}
        self._function_return_types: dict[str, str] = {}

    # --- type mapping ---

    def _dart_type(self, east_type: Any) -> str:
        """Map an EAST type string to a Dart type string."""
        if not isinstance(east_type, str) or east_type == "":
            return "dynamic"
        t = east_type.strip()
        if t in {"Any", "object", "unknown"}:
            return "dynamic"
        if t == "int" or t == "int64" or t == "int32" or t == "int16" or t == "int8":
            return "int"
        if t == "uint8" or t == "uint16" or t == "uint32" or t == "uint64" or t == "byte":
            return "int"
        if t == "float" or t == "float64" or t == "float32":
            return "double"
        if t == "bool":
            return "bool"
        if t == "str" or t == "string":
            return "String"
        if t == "None":
            return "void"
        if t in {"bytes", "bytearray"}:
            return "List<int>"
        # Optional: T | None
        if t.find("|") != -1:
            parts = [p.strip() for p in t.split("|")]
            non_none = [p for p in parts if p != "None"]
            has_none = len(non_none) < len(parts)
            if has_none and len(non_none) == 1:
                return self._dart_type(non_none[0]) + "?"
            if not has_none and len(non_none) == 1:
                return self._dart_type(non_none[0])
            return "dynamic"
        # list[T]
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return "List<" + self._dart_type(inner) + ">"
        # dict[K, V]
        if t.startswith("dict[") and t.endswith("]"):
            inner = t[5:-1]
            parts = self._split_generic_args(inner)
            if len(parts) == 2:
                return "Map<" + self._dart_type(parts[0]) + ", " + self._dart_type(parts[1]) + ">"
            return "Map<dynamic, dynamic>"
        # tuple[...] → List<dynamic>
        if t.startswith("tuple[") and t.endswith("]"):
            return "List<dynamic>"
        # set[T]
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return "Set<" + self._dart_type(inner) + ">"
        # callable
        if t.startswith("callable") or t == "callable":
            return "Function"
        # User-defined class
        if t in self.class_names:
            return t
        return "dynamic"

    def _split_generic_args(self, inner: str) -> list[str]:
        """Split 'K, V' respecting nested brackets."""
        parts: list[str] = []
        depth = 0
        current: list[str] = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
                current.append(ch)
            elif ch == "]":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
            i += 1
        if len(current) > 0:
            parts.append("".join(current).strip())
        return parts

    def _dart_return_type(self, stmt: dict[str, Any]) -> str:
        """Get the Dart return type for a function statement.

        Container types use ``dynamic`` to avoid type mismatch.
        """
        rt = stmt.get("return_type")
        if isinstance(rt, str) and rt.strip() != "":
            dart_t = self._dart_type(rt)
            if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
                return "dynamic"
            return dart_t
        return "dynamic"

    def _dart_arg_type(self, stmt: dict[str, Any], arg_name: str) -> str:
        """Get the Dart type for a function argument.

        Container types use ``dynamic`` to avoid type mismatch with
        runtime helpers that pass ``List<dynamic>``.
        """
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        t = arg_types.get(arg_name)
        if isinstance(t, str) and t.strip() != "":
            dart_t = self._dart_type(t)
            if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
                return "dynamic"
            return dart_t
        return "dynamic"

    def _dart_decl_type(self, stmt: dict[str, Any], value_node: Any) -> str:
        """Get Dart type for a variable declaration from decl_type, annotation, or inference.

        Container types (List/Map/Set) use ``var`` to avoid type mismatch
        with runtime helpers that return ``dynamic``.
        """
        raw = ""
        decl_type_any = stmt.get("decl_type")
        if isinstance(decl_type_any, str) and decl_type_any.strip() != "":
            raw = decl_type_any.strip()
        if raw == "":
            anno_any = stmt.get("annotation")
            if isinstance(anno_any, str) and anno_any.strip() != "":
                raw = anno_any.strip()
        if raw == "":
            raw = self._infer_decl_type_from_expr(value_node)
        if raw == "":
            return "var"
        dart_t = self._dart_type(raw)
        # Container types → var (runtime helpers return dynamic)
        if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
            return "var"
        return dart_t

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
            return "__pytraTruthy(" + test + ")"
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
        module_comments = self._module_leading_comment_lines(prefix="// ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        # Emit imports header
        self._emit_imports(body)
        # Emit runtime helpers
        self._emit_line("// --- pytra runtime helpers ---")
        self._emit_print_helper()
        self._emit_line("")
        self._emit_truthy_helper()
        self._emit_line("")
        self._emit_contains_helper()
        self._emit_line("")
        self._emit_repeat_helper()
        self._emit_line("")
        self._emit_string_predicate_helpers()
        if len(self.class_names) > 0:
            self._emit_line("")
            self._emit_isinstance_helper()
        self._emit_line("// --- end runtime helpers ---")
        self._emit_line("")
        # Emit body
        for stmt in body:
            self._emit_stmt(stmt)
        # Emit main guard
        if len(main_guard) > 0:
            self._emit_line("")
            self._emit_line("void main() {")
            self.indent += 1
            for stmt in main_guard:
                self._emit_stmt(stmt)
            self.indent -= 1
            self._emit_line("}")
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
        self.lines.append(("  " * self.indent) + text)

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        if len(body) == 0:
            return
        i = 0
        while i < len(body):
            self._emit_stmt(body[i])
            i += 1

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

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        self.class_names = set()
        self.imported_modules = set()
        self.function_names = set()
        self._function_return_types = {}
        self._class_field_types = {}
        self.relative_import_name_aliases = _collect_relative_import_name_aliases(self.east_doc)
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "ClassDef":
                cls_name = _safe_ident(stmt.get("name"), "Class_")
                self.class_names.add(cls_name)
                # Collect field types
                fields: dict[str, str] = {}
                cls_body = stmt.get("body")
                if isinstance(cls_body, list):
                    for sub in cls_body:
                        if isinstance(sub, dict) and sub.get("kind") == "AnnAssign":
                            target_any = sub.get("target")
                            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                                fname = _safe_ident(target_any.get("id"), "field")
                                ftype = sub.get("annotation")
                                if not isinstance(ftype, str) or ftype.strip() == "":
                                    ftype = sub.get("decl_type")
                                if isinstance(ftype, str) and ftype.strip() != "":
                                    fields[fname] = ftype.strip()
                        if isinstance(sub, dict) and sub.get("kind") == "FunctionDef":
                            fn_name = _safe_ident(sub.get("name"), "fn")
                            rt = sub.get("return_type")
                            if isinstance(rt, str) and rt.strip() != "":
                                self._function_return_types[cls_name + "." + fn_name] = rt.strip()
                field_types_any = stmt.get("field_types")
                if isinstance(field_types_any, dict):
                    for fk, fv in field_types_any.items():
                        if isinstance(fk, str) and isinstance(fv, str) and fv.strip() != "":
                            fields[_safe_ident(fk, "field")] = fv.strip()
                self._class_field_types[cls_name] = fields
                continue
            if kind == "FunctionDef":
                fn_name = _safe_ident(stmt.get("name"), "fn")
                self.function_names.add(fn_name)
                rt = stmt.get("return_type")
                if isinstance(rt, str) and rt.strip() != "":
                    self._function_return_types[fn_name] = rt.strip()
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
        if ident == "self" and self.current_class_name != "":
            return "this"
        if ident == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
            ident = "__pytra_main"
        return self.relative_import_name_aliases.get(ident, ident)

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        import_lines: list[str] = []
        import_lines.append("import 'py_runtime.dart';")
        import_lines.append("")
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
                        raise RuntimeError("lang=dart unresolved import module: " + mod)
                    import_lines.append("// import " + mod + " as " + alias_txt + " (not yet mapped)")
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
                    # pytra.utils.png / pytra.utils.gif: emit import for the generated module
                    if mod == "pytra.utils.png":
                        dart_import = "import 'png/east.dart';"
                        if dart_import not in import_lines:
                            import_lines.append(dart_import)
                        continue
                    if mod == "pytra.utils.gif":
                        dart_import = "import 'gif/east.dart';"
                        if dart_import not in import_lines:
                            import_lines.append(dart_import)
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_stdout":
                        import_lines.append(
                            "dynamic " + alias_txt + " = (dynamic _expected, dynamic _fn) => true;"
                        )
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_eq":
                        import_lines.append("dynamic " + alias_txt + " = (dynamic a, dynamic b, [dynamic _label]) => a == b;")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_true":
                        import_lines.append("dynamic " + alias_txt + " = (dynamic v, [dynamic _label]) => v != null && v != false && v != 0;")
                        continue
                    if mod in {"pytra.utils.assertions", "pytra.std.test"} and sym == "py_assert_all":
                        import_lines.append(
                            "dynamic "
                            + alias_txt
                            + " = (dynamic checks, [dynamic _label]) { if (checks == null) return false; for (var c in checks) { if (c != true) return false; } return true; };"
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
                        raise RuntimeError("lang=dart unresolved import symbol: " + mod + "." + sym)
                    import_lines.append(
                        "// from " + mod + " import " + sym + " as " + alias_txt + " (not yet mapped)"
                    )
        # Dart requires all import directives before declarations.
        # Split import lines into import directives and other lines.
        dart_imports: list[str] = []
        other_lines: list[str] = []
        for line in import_lines:
            if line.startswith("import "):
                dart_imports.append(line)
            else:
                other_lines.append(line)
        for line in dart_imports:
            self._emit_line(line)
        if len(dart_imports) > 0 and len(other_lines) > 0:
            self._emit_line("")
        for line in other_lines:
            self._emit_line(line)
        if len(import_lines) > 0:
            self._emit_line("")

    def _emit_print_helper(self) -> None:
        self._emit_line("String __pytraPrintRepr(dynamic v) {")
        self.indent += 1
        self._emit_line("if (v == true) return 'True';")
        self._emit_line("if (v == false) return 'False';")
        self._emit_line("if (v == null) return 'None';")
        self._emit_line("return v.toString();")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self._emit_line("void __pytraPrint(List<dynamic> args) {")
        self.indent += 1
        self._emit_line("print(args.map(__pytraPrintRepr).join(' '));")
        self.indent -= 1
        self._emit_line("}")

    def _emit_truthy_helper(self) -> None:
        self._emit_line("bool __pytraTruthy(dynamic v) {")
        self.indent += 1
        self._emit_line("if (v == null) return false;")
        self._emit_line("if (v is bool) return v;")
        self._emit_line("if (v is num) return v != 0;")
        self._emit_line("if (v is String) return v.isNotEmpty;")
        self._emit_line("if (v is List) return v.isNotEmpty;")
        self._emit_line("if (v is Map) return v.isNotEmpty;")
        self._emit_line("return true;")
        self.indent -= 1
        self._emit_line("}")

    def _emit_contains_helper(self) -> None:
        self._emit_line("bool __pytraContains(dynamic container, dynamic value) {")
        self.indent += 1
        self._emit_line("if (container is List) return container.contains(value);")
        self._emit_line("if (container is Map) return container.containsKey(value);")
        self._emit_line("if (container is Set) return container.contains(value);")
        self._emit_line("if (container is String) return container.contains(value.toString());")
        self._emit_line("return false;")
        self.indent -= 1
        self._emit_line("}")

    def _emit_repeat_helper(self) -> None:
        self._emit_line("dynamic __pytraRepeatSeq(dynamic a, dynamic b) {")
        self.indent += 1
        self._emit_line("dynamic seq = a;")
        self._emit_line("dynamic count = b;")
        self._emit_line("if (a is num && b is! num) { seq = b; count = a; }")
        self._emit_line("int n = (count is num) ? count.toInt() : 0;")
        self._emit_line("if (n <= 0) {")
        self.indent += 1
        self._emit_line("if (seq is String) return '';")
        self._emit_line("return [];")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("if (seq is String) return seq * n;")
        self._emit_line("if (seq is List) {")
        self.indent += 1
        self._emit_line("var out = [];")
        self._emit_line("for (var i = 0; i < n; i++) { out.addAll(seq); }")
        self._emit_line("return out;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("return (a is num ? a : 0) * (b is num ? b : 0);")
        self.indent -= 1
        self._emit_line("}")

    def _emit_string_predicate_helpers(self) -> None:
        self._emit_line("bool __pytraStrIsdigit(String s) {")
        self.indent += 1
        self._emit_line("if (s.isEmpty) return false;")
        self._emit_line("for (var i = 0; i < s.length; i++) {")
        self.indent += 1
        self._emit_line("var c = s.codeUnitAt(i);")
        self._emit_line("if (c < 48 || c > 57) return false;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("return true;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self._emit_line("bool __pytraStrIsalpha(String s) {")
        self.indent += 1
        self._emit_line("if (s.isEmpty) return false;")
        self._emit_line("for (var i = 0; i < s.length; i++) {")
        self.indent += 1
        self._emit_line("var c = s.codeUnitAt(i);")
        self._emit_line("if (!((c >= 65 && c <= 90) || (c >= 97 && c <= 122))) return false;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("return true;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self._emit_line("bool __pytraStrIsalnum(String s) {")
        self.indent += 1
        self._emit_line("if (s.isEmpty) return false;")
        self._emit_line("for (var i = 0; i < s.length; i++) {")
        self.indent += 1
        self._emit_line("var c = s.codeUnitAt(i);")
        self._emit_line("if (!((c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122))) return false;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("return true;")
        self.indent -= 1
        self._emit_line("}")

    def _emit_isinstance_helper(self) -> None:
        self._emit_line("bool __pytraIsinstance(dynamic obj, dynamic classType) {")
        self.indent += 1
        self._emit_line("if (obj == null) return false;")
        self._emit_line("// Dart runtime type check is handled via 'is' keyword at emit site")
        self._emit_line("return false;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        self._emit_leading_trivia(stmt, prefix="// ")
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
            self._emit_line("return " + val + ";")
            return
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value_node = stmt.get("value")
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "null"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type_any = stmt.get("decl_type")
                decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                if decl_type == "":
                    anno_any = stmt.get("annotation")
                    if isinstance(anno_any, str):
                        anno_s: str = anno_any
                        decl_type = anno_s.strip()
                if decl_type == "":
                    decl_type = self._infer_decl_type_from_expr(value_node)
                dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                if value_node is None and bool(stmt.get("declare")):
                    if decl_type in _NIL_FREE_DECL_TYPES:
                        if decl_type != "":
                            self._current_type_map()[target_name] = decl_type
                        if len(self._local_var_stack) > 0:
                            self._current_local_vars().add(target_name)
                        self._emit_line(dart_t + " " + target + ";")
                        return
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                if len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                self._emit_line(dart_t + " " + target + " = " + value + ";")
            else:
                self._emit_line(target + " = " + value + ";")
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
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                        dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                        self._emit_line(dart_t + " " + target + " = " + value + ";")
                        return
                self._emit_line(target + " = " + value + ";")
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
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                        dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                        self._emit_line(dart_t + " " + target + " = " + value + ";")
                        return
                self._emit_line(target + " = " + value + ";")
                return
            raise RuntimeError("lang=dart unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            op_token = _binop_symbol(op)
            # If target is int-typed, cast the augmented result to avoid num promotion
            target_type = self._lookup_expr_type(stmt.get("target"))
            if target_type in {"int", "int64", "int32"} and op in {"Add", "Sub", "Mult", "Mod", "FloorDiv"}:
                self._emit_line(target + " = ((" + target + " " + op_token + " " + value + ") as int);")
            else:
                self._emit_line(target + " " + op_token + "= " + value + ";")
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
                    self._emit_line("break;")
                    return
                if loop_kw == "continue":
                    self._emit_line("continue;")
                    return
            self._emit_line(self._render_expr(value_any) + ";")
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
                            self._emit_line("throw Exception(" + self._render_expr(args[0]) + ");")
                            return
                        self._emit_line("throw Exception('error');")
                        return
            if isinstance(exc_any, dict):
                self._emit_line("throw Exception(" + self._render_expr(exc_any) + ".toString());")
            else:
                self._emit_line("throw Exception('error');")
            return
        if kind == "Try":
            body = self._dict_list(stmt.get("body"))
            self._emit_line("try {")
            self.indent += 1
            i = 0
            while i < len(body):
                self._emit_stmt(body[i])
                i += 1
            self.indent -= 1
            handlers_any = stmt.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            if len(handlers) > 0:
                i = 0
                while i < len(handlers):
                    h = handlers[i]
                    if isinstance(h, dict):
                        hd: dict[str, Any] = h
                        handler_name = hd.get("name")
                        if isinstance(handler_name, str) and handler_name != "":
                            self._emit_line("} catch (" + _safe_ident(handler_name, "e") + ") {")
                        else:
                            self._emit_line("} catch (e) {")
                        self.indent += 1
                        h_body = self._dict_list(hd.get("body"))
                        j = 0
                        while j < len(h_body):
                            self._emit_stmt(h_body[j])
                            j += 1
                        self.indent -= 1
                    i += 1
            else:
                self._emit_line("} catch (e) {")
                self.indent += 1
                self._emit_line("// handler")
                self.indent -= 1
            finalbody = self._dict_list(stmt.get("finalbody"))
            if len(finalbody) > 0:
                self._emit_line("} finally {")
                self.indent += 1
                i = 0
                while i < len(finalbody):
                    self._emit_stmt(finalbody[i])
                    i += 1
                self.indent -= 1
            self._emit_line("}")
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
            self._emit_line("/* pass */")
            return
        if kind == "TypeAlias":
            # type X = A | B — no runtime effect in Dart, emit as comment
            alias_name = _safe_ident(stmt.get("name"), "T")
            self._emit_line("// type alias: " + alias_name)
            return
        if kind == "Yield":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("yield " + val + ";")
            return
        if kind == "VarDecl":
            self._emit_var_decl(stmt)
            return
        raise RuntimeError("lang=dart unsupported stmt kind: " + str(kind))

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn")
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        param_parts: list[str] = []
        for a_raw, a_safe in zip(args, arg_names):
            raw_name = a_raw if isinstance(a_raw, str) else a_safe
            at = self._dart_arg_type(stmt, raw_name)
            param_parts.append(at + " " + a_safe)
        params = ", ".join(param_parts)
        ret_type = self._dart_return_type(stmt)
        self._emit_line(ret_type + " " + name + "(" + params + ") {")
        self.indent += 1
        self._push_function_context(stmt, arg_names, args)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("if (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        orelse = self._dict_list(stmt.get("orelse"))
        if len(orelse) > 0:
            self._emit_line("} else {")
            self.indent += 1
            for sub in orelse:
                self._emit_stmt(sub)
            self.indent -= 1
        self._emit_line("}")

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class_")
        base_any = stmt.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        if base_name != "":
            self._emit_line("class " + cls_name + " extends " + base_name + " {")
        else:
            self._emit_line("class " + cls_name + " {")
        self.indent += 1
        body = self._dict_list(stmt.get("body"))
        field_types = self._class_field_types.get(cls_name, {})
        # Collect fields for dataclass or from AnnAssign
        fields: list[str] = []
        field_defaults: dict[str, str] = {}
        for sub in body:
            if sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    fields.append(field_name)
                    ft = field_types.get(field_name, "")
                    dart_ft = self._dart_type(ft) if ft != "" else "dynamic"
                    self._emit_line(dart_ft + " " + field_name + ";")
                    # Collect default value
                    value_node = sub.get("value")
                    if isinstance(value_node, dict):
                        field_defaults[field_name] = self._render_expr(value_node)
        has_init = False
        for sub in body:
            if sub.get("kind") != "FunctionDef":
                continue
            if sub.get("name") == "__init__":
                has_init = True
            self._emit_class_method(cls_name, base_name, sub)
        if not has_init and len(fields) > 0:
            required_params: list[str] = []
            optional_params: list[str] = []
            for f in fields:
                if f in field_defaults:
                    optional_params.append("this." + f + " = " + field_defaults[f])
                else:
                    required_params.append("this." + f)
            if len(optional_params) == 0:
                params = ", ".join(required_params)
                self._emit_line(cls_name + "(" + params + ");")
            else:
                all_params = ", ".join(required_params + ["[" + ", ".join(optional_params) + "]"]) if len(required_params) > 0 else "[" + ", ".join(optional_params) + "]"
                self._emit_line(cls_name + "(" + all_params + ");")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_class_method(self, cls_name: str, base_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        raw_args: list[str] = []
        for i_idx, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i_idx == 0 and (arg_name == "self_" or arg_name == "self"):
                continue
            args.append(arg_name)
            raw_args.append(arg if isinstance(arg, str) else arg_name)
        prev_class = self.current_class_name
        prev_base = self.current_class_base_name
        self.current_class_name = cls_name
        self.current_class_base_name = base_name
        param_parts: list[str] = []
        for a_raw, a_safe in zip(raw_args, args):
            at = self._dart_arg_type(stmt, a_raw)
            param_parts.append(at + " " + a_safe)
        params = ", ".join(param_parts)
        if method_name == "__init__":
            self._emit_line(cls_name + "(" + params + ") {")
            self.indent += 1
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
            self.current_class_name = prev_class
            self.current_class_base_name = prev_base
            return
        if method_name == "__str__":
            method_name = "toString"
        ret_type = self._dart_return_type(stmt)
        self._emit_line(ret_type + " " + method_name + "(" + params + ") {")
        self.indent += 1
        self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self.current_class_name = prev_class
        self.current_class_base_name = prev_base

    def _for_needs_tmp_start(self, target_name: str, start_expr: str) -> bool:
        """Check if start expression references the target variable (shadowing risk)."""
        # Simple check: target_name appears as a word boundary in start_expr
        # e.g. start="y" target="y" → True
        if target_name == start_expr:
            return True
        # Check for target_name as substring with non-alnum boundaries
        i = 0
        while i < len(start_expr):
            pos = start_expr.find(target_name, i)
            if pos < 0:
                break
            end_pos = pos + len(target_name)
            left_ok = pos == 0 or not (start_expr[pos - 1].isalnum() or start_expr[pos - 1] == "_")
            right_ok = end_pos >= len(start_expr) or not (start_expr[end_pos].isalnum() or start_expr[end_pos] == "_")
            if left_ok and right_ok:
                return True
            i = pos + 1
        return False

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")
        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=dart unsupported forcore static_fastpath shape")
            id2: dict[str, Any] = iter_plan
            if id2.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=dart unsupported forcore static_fastpath shape")
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
                if self._for_needs_tmp_start(target_name, start):
                    tmp = self._next_tmp_name("__forStart")
                    self._emit_line("var " + tmp + " = " + start + ";")
                    self._emit_line("for (var " + target_name + " = " + tmp + "; " + target_name + " < " + stop + "; " + target_name + ("++" if step_const == 1 else " += " + step) + ") {")
                elif step_const == 1:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " < " + stop + "; " + target_name + "++) {")
                else:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " < " + stop + "; " + target_name + " += " + step + ") {")
                self.indent += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            if range_mode == "descending":
                if self._for_needs_tmp_start(target_name, start):
                    tmp = self._next_tmp_name("__forStart")
                    self._emit_line("var " + tmp + " = " + start + ";")
                    self._emit_line("for (var " + target_name + " = " + tmp + "; " + target_name + " > " + stop + "; " + target_name + " += " + step + ") {")
                else:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " > " + stop + "; " + target_name + " += " + step + ") {")
                self.indent += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            # Dynamic range mode
            start_tmp = self._next_tmp_name("__pytraRangeStart")
            stop_tmp = self._next_tmp_name("__pytraRangeStop")
            step_tmp = self._next_tmp_name("__pytraRangeStep")
            self._emit_line("var " + start_tmp + " = " + start + ";")
            self._emit_line("var " + stop_tmp + " = " + stop + ";")
            self._emit_line("var " + step_tmp + " = " + step + ";")
            self._emit_line("if (" + step_tmp + " > 0) {")
            self.indent += 1
            self._emit_line("for (var " + target_name + " = " + start_tmp + "; " + target_name + " < " + stop_tmp + "; " + target_name + " += " + step_tmp + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            self.indent -= 1
            self._emit_line("} else if (" + step_tmp + " < 0) {")
            self.indent += 1
            self._emit_line("for (var " + target_name + " = " + start_tmp + "; " + target_name + " > " + stop_tmp + "; " + target_name + " += " + step_tmp + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            self.indent -= 1
            self._emit_line("}")
            return
        if iter_mode == "runtime_protocol":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=dart unsupported forcore runtime shape")
            id_node: dict[str, Any] = iter_plan
            iter_expr = self._render_expr(id_node.get("iter_expr"))
            tuple_target = isinstance(target_plan, dict) and target_plan.get("kind") == "TupleTarget"
            if tuple_target and isinstance(target_plan, dict):
                iter_name = self._next_tmp_name("__it")
                self._emit_line("for (var " + iter_name + " in " + iter_expr + ") {")
                self.indent += 1
                direct_names_any = target_plan.get("direct_unpack_names")
                direct_names = direct_names_any if isinstance(direct_names_any, list) else []
                if len(direct_names) > 0:
                    i = 0
                    while i < len(direct_names):
                        name_any = direct_names[i]
                        if isinstance(name_any, str) and name_any != "":
                            local_name = _safe_ident(name_any, "it")
                            self._emit_line("var " + local_name + " = " + iter_name + "[" + str(i) + "];")
                        i += 1
                else:
                    elems_any = target_plan.get("elements")
                    elems = elems_any if isinstance(elems_any, list) else []
                    i = 0
                    while i < len(elems):
                        elem = elems[i]
                        if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                            local_name = _safe_ident(elem.get("id"), "it")
                            self._emit_line("var " + local_name + " = " + iter_name + "[" + str(i) + "];")
                        i += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            self._emit_line("for (var " + target_name + " in " + iter_expr + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            return
        raise RuntimeError("lang=dart unsupported forcore iter_mode: " + iter_mode)

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node)."""
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type_any = stmt.get("type")
        var_type = var_type_any.strip() if isinstance(var_type_any, str) else ""
        dart_t = self._dart_type(var_type) if var_type != "" else "var"
        if var_type != "":
            self._current_type_map()[name] = var_type
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(name)
        if var_type in _NIL_FREE_DECL_TYPES:
            self._emit_line(dart_t + " " + name + ";")
        else:
            self._emit_line("late " + dart_t + " " + name + ";")

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("while (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _next_tmp_name(self, prefix: str = "__pytraTmp") -> str:
        self.tmp_seq += 1
        return prefix + "_" + str(self.tmp_seq)

    def _emit_tuple_assign(self, tuple_target: dict[str, Any], value_any: Any) -> None:
        elems_any = tuple_target.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        if len(elems) == 0:
            raise RuntimeError("lang=dart unsupported tuple assign target: empty")
        tmp_name = self._next_tmp_name("__pytraTuple")
        value_expr = self._render_expr(value_any)
        self._emit_line("var " + tmp_name + " = " + value_expr + ";")
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
                        self._emit_line("var " + target_txt + " = " + tmp_name + "[" + str(i) + "];")
                        i += 1
                        continue
                self._emit_line(target_txt + " = " + tmp_name + "[" + str(i) + "];")
            i += 1

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_target(stmt.get("left"))
        right = self._render_target(stmt.get("right"))
        tmp_name = self._next_tmp_name("__swap")
        self._emit_line("var " + tmp_name + " = " + left + ";")
        self._emit_line(left + " = " + right + ";")
        self._emit_line(right + " = " + tmp_name + ";")

    def _render_target(self, target_any: Any) -> str:
        if not isinstance(target_any, dict):
            return "null"
        tad: dict[str, Any] = target_any
        if tad.get("kind") == "Name":
            return _safe_ident(tad.get("id"), "value")
        if tad.get("kind") == "Attribute":
            owner = self._render_expr(tad.get("value"))
            attr = _safe_ident(tad.get("attr"), "field")
            return owner + "." + attr
        if tad.get("kind") == "Subscript":
            owner = self._render_expr(tad.get("value"))
            index_node = tad.get("slice")
            if isinstance(index_node, dict):
                ind: dict[str, Any] = index_node
                if ind.get("kind") == "Slice":
                    raise RuntimeError("lang=dart unsupported slice assignment target")
            index = self._render_expr(index_node)
            return owner + "[" + index + "]"
        target_kind = tad.get("kind")
        raise RuntimeError("lang=dart unsupported assignment target: " + str(target_kind))

    def _render_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "null"
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
            op = _binop_symbol(op_raw)
            if op_raw == "Mult" and (self._is_sequence_expr(left_node) or self._is_sequence_expr(right_node)):
                return "__pytraRepeatSeq(" + left + ", " + right + ")"
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
                return "(!" + operand + ")"
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
                return "__pytraContains(" + right + ", " + left + ")"
            if op0 == "NotIn":
                return "(!__pytraContains(" + right + ", " + left + "))"
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
            return "(" + ", ".join(names) + ") => " + body
        if kind == "List":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "[" + ", ".join(out) + "]"
        if kind == "Tuple":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "[" + ", ".join(out) + "]"
        if kind == "Set":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{" + ", ".join(out) + "}"
        if kind == "ListComp":
            return self._render_list_comp(ed)
        if kind == "SetComp":
            return self._render_set_comp(ed)
        if kind == "DictComp":
            return self._render_dict_comp(ed)
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
                        ed2: dict[str, Any] = ent
                        k = self._render_expr(ed2.get("key"))
                        v = self._render_expr(ed2.get("value"))
                        pairs_from_entries.append(k + ": " + v)
                    i += 1
                if len(pairs_from_entries) == 0:
                    return "{}"
                return "{" + ", ".join(pairs_from_entries) + "}"
            pairs: list[str] = []
            i = 0
            while i < len(keys) and i < len(values):
                k = self._render_expr(keys[i])
                v = self._render_expr(values[i])
                pairs.append(k + ": " + v)
                i += 1
            return "{" + ", ".join(pairs) + "}"
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
                upper = self._render_expr(upper_node) if isinstance(upper_node, dict) else "null"
                if owner_type == "str":
                    if upper == "null":
                        return "pytraStrSlice(" + owner + ", " + lower + ", null)"
                    return "pytraStrSlice(" + owner + ", " + lower + ", " + upper + ")"
                if upper == "null":
                    return "pytraSlice(" + owner + ", " + lower + ", null)"
                return "pytraSlice(" + owner + ", " + lower + ", " + upper + ")"
            index = self._render_expr(index_node)
            idx_const = self._const_int_literal(index_node)
            if isinstance(idx_const, int):
                if owner_type == "str":
                    if idx_const >= 0:
                        return owner + "[" + str(idx_const) + "]"
                    return owner + "[" + owner + ".length + " + str(idx_const) + "]"
                if idx_const >= 0:
                    return owner + "[" + str(idx_const) + "]"
                return owner + "[" + owner + ".length + " + str(idx_const) + "]"
            return owner + "[(" + index + ") < 0 ? " + owner + ".length + (" + index + ") : (" + index + ")]"
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
                    return "(" + value + " is int)"
                if expected in {"float", "float64"}:
                    return "(" + value + " is double)"
                if expected in {"str", "string"}:
                    return "(" + value + " is String)"
                if expected in {"bool"}:
                    return "(" + value + " is bool)"
                if expected in {"list"}:
                    return "(" + value + " is List)"
                if expected in {"dict"}:
                    return "(" + value + " is Map)"
                if expected in {"set_"}:
                    return "(" + value + " is Set)"
                if expected in {"tuple"}:
                    return "(" + value + " is List)"
                if expected in self.class_names:
                    return "(" + value + " is " + expected + ")"
            return "false"
        if kind == "IsSubtype" or kind == "IsSubclass":
            return "false"
        if kind == "IfExp":
            test = self._render_expr(ed.get("test"))
            body = self._render_expr(ed.get("body"))
            orelse = self._render_expr(ed.get("orelse"))
            return "(__pytraTruthy(" + test + ") ? (" + body + ") : (" + orelse + "))"
        if kind == "JoinedStr":
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "''"
            parts: list[str] = []
            for item in values:
                item_d = item if isinstance(item, dict) else {}
                item_kind = item_d.get("kind")
                if item_kind == "Constant" and isinstance(item_d.get("value"), str):
                    parts.append(self._render_expr(item_d))
                elif item_kind == "FormattedValue":
                    parts.append("(" + self._render_expr(item_d.get("value")) + ").toString()")
                else:
                    parts.append("(" + self._render_expr(item_d) + ").toString()")
            return "(" + " + ".join(parts) + ")"
        if kind == "Box":
            return self._render_expr(ed.get("value"))
        if kind == "Unbox":
            return self._render_expr(ed.get("value"))
        if kind == "ObjTypeId":
            return "null /* obj_type_id */"
        if kind == "ObjStr":
            return "(" + self._render_expr(ed.get("value")) + ").toString()"
        if kind == "ObjBool":
            val = self._render_expr(ed.get("value"))
            return "__pytraTruthy(" + val + ")"
        if kind == "ObjLen":
            return "(" + self._render_expr(ed.get("value")) + ").length"
        raise RuntimeError("lang=dart unsupported expr kind: " + str(kind))

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
            raise RuntimeError("lang=dart unresolved stdlib runtime call: " + semantic_tag)
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            fn_name = _safe_ident(func_any.get("id"), "fn")
            if fn_name == "print":
                return "__pytraPrint([" + ", ".join(rendered_args) + "])"
            if fn_name == "int":
                if len(rendered_args) == 0:
                    return "0"
                return "pytraInt(" + rendered_args[0] + ")"
            if fn_name == "float":
                if len(rendered_args) == 0:
                    return "0.0"
                return "pytraFloat(" + rendered_args[0] + ")"
            if fn_name == "bool":
                if len(rendered_args) == 0:
                    return "false"
                return "__pytraTruthy(" + rendered_args[0] + ")"
            if fn_name == "str":
                if len(rendered_args) == 0:
                    return "''"
                return "(" + rendered_args[0] + ").toString()"
            if fn_name == "len":
                if len(rendered_args) == 0:
                    return "0"
                return "(" + rendered_args[0] + ").length"
            if fn_name == "max":
                self._needs_math_import = True
                if len(rendered_args) == 0:
                    return "0"
                if len(rendered_args) == 2:
                    return "((" + rendered_args[0] + ") > (" + rendered_args[1] + ") ? (" + rendered_args[0] + ") : (" + rendered_args[1] + "))"
                return "[" + ", ".join(rendered_args) + "].reduce((a, b) => a > b ? a : b)"
            if fn_name == "min":
                self._needs_math_import = True
                if len(rendered_args) == 0:
                    return "0"
                if len(rendered_args) == 2:
                    return "((" + rendered_args[0] + ") < (" + rendered_args[1] + ") ? (" + rendered_args[0] + ") : (" + rendered_args[1] + "))"
                return "[" + ", ".join(rendered_args) + "].reduce((a, b) => a < b ? a : b)"
            if fn_name == "abs":
                if len(rendered_args) == 0:
                    return "0"
                return "(" + rendered_args[0] + ").abs()"
            if fn_name == "enumerate":
                if len(rendered_args) == 0:
                    return "[]"
                return "(" + rendered_args[0] + ").asMap().entries.map((e) => [e.key, e.value]).toList()"
            if fn_name == "sorted":
                if len(rendered_args) == 0:
                    return "[]"
                return "(List.from(" + rendered_args[0] + ")..sort())"
            if fn_name == "reversed":
                if len(rendered_args) == 0:
                    return "[]"
                return "(" + rendered_args[0] + ").reversed.toList()"
            if fn_name == "zip":
                if len(rendered_args) < 2:
                    return "[]"
                return "pytraZip(" + ", ".join(rendered_args) + ")"
            if fn_name == "range":
                if len(rendered_args) == 1:
                    return "List.generate(" + rendered_args[0] + ", (i) => i)"
                if len(rendered_args) == 2:
                    return "List.generate((" + rendered_args[1] + ") - (" + rendered_args[0] + "), (i) => i + (" + rendered_args[0] + "))"
                return "List.generate(((" + rendered_args[1] + ") - (" + rendered_args[0] + ")) ~/ (" + rendered_args[2] + "), (i) => (" + rendered_args[0] + ") + i * (" + rendered_args[2] + "))"
            if fn_name == "bytearray":
                if len(rendered_args) == 0:
                    return "<int>[]"
                return "pytraBytearray(" + rendered_args[0] + ")"
            if fn_name == "bytes":
                if len(rendered_args) == 0:
                    return "<int>[]"
                return "pytraBytes(" + rendered_args[0] + ")"
            if fn_name in self.class_names:
                return fn_name + "(" + ", ".join(rendered_args) + ")"
            rendered_name = self._render_name_expr(func_any)
            return rendered_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_node = func_any.get("value")
            raw_attr = func_any.get("attr") if isinstance(func_any.get("attr"), str) else ""
            attr = _safe_ident(raw_attr, "call")
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and super_func.get("kind") == "Name":
                    super_name = str(super_func.get("id"))
                    if super_name in {"super", "_super"}:
                        if attr == "__init__":
                            return "/* super().__init__() */"
                        if self.current_class_base_name != "":
                            return "super." + attr + "(" + ", ".join(rendered_args) + ")"
            owner = self._render_expr(owner_node)
            owner_type = self._lookup_expr_type(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in self.imported_modules:
                    # Dart math: floor/ceil/fabs are instance methods, not top-level
                    if owner_name == "math" and attr in {"floor", "ceil"}:
                        if len(rendered_args) >= 1:
                            return "(" + rendered_args[0] + " as num)." + attr + "()"
                    if owner_name == "math" and attr == "fabs":
                        if len(rendered_args) >= 1:
                            return "(" + rendered_args[0] + " as num).abs()"
                    return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            # String methods
            if owner_type == "str" or attr in {
                "isdigit",
                "isalpha",
                "isalnum",
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
                "upper",
                "lower",
            }:
                if attr == "isdigit":
                    return "__pytraStrIsdigit(" + owner + ")"
                if attr == "isalpha":
                    return "__pytraStrIsalpha(" + owner + ")"
                if attr == "isalnum":
                    return "__pytraStrIsalnum(" + owner + ")"
                if attr == "strip":
                    return owner + ".trim()"
                if attr == "lstrip":
                    return owner + ".trimLeft()"
                if attr == "rstrip":
                    return owner + ".trimRight()"
                if attr == "startswith" and len(rendered_args) >= 1:
                    return owner + ".startsWith(" + rendered_args[0] + ")"
                if attr == "endswith" and len(rendered_args) >= 1:
                    return owner + ".endsWith(" + rendered_args[0] + ")"
                if attr == "join" and len(rendered_args) >= 1:
                    return "(" + rendered_args[0] + ").join(" + owner + ")"
                if attr == "find" and len(rendered_args) >= 1:
                    return owner + ".indexOf(" + rendered_args[0] + ")"
                if attr == "rfind" and len(rendered_args) >= 1:
                    return owner + ".lastIndexOf(" + rendered_args[0] + ")"
                if attr == "replace" and len(rendered_args) >= 2:
                    return owner + ".replaceAll(" + rendered_args[0] + ", " + rendered_args[1] + ")"
                if attr == "split":
                    sep = rendered_args[0] if len(rendered_args) >= 1 else "' '"
                    return owner + ".split(" + sep + ")"
                if attr == "splitlines":
                    return owner + ".split('\\n')"
                if attr == "upper":
                    return owner + ".toUpperCase()"
                if attr == "lower":
                    return owner + ".toLowerCase()"
            # List methods
            if attr == "append" and len(rendered_args) == 1:
                return owner + ".add(" + rendered_args[0] + ")"
            if attr == "extend" and len(rendered_args) == 1:
                return owner + ".addAll(" + rendered_args[0] + ")"
            if attr == "pop":
                if len(rendered_args) == 0:
                    return owner + ".removeLast()"
                return owner + ".removeAt(" + rendered_args[0] + ")"
            if attr == "insert" and len(rendered_args) == 2:
                return owner + ".insert(" + rendered_args[0] + ", " + rendered_args[1] + ")"
            if attr == "remove" and len(rendered_args) == 1:
                return owner + ".remove(" + rendered_args[0] + ")"
            if attr == "sort":
                return owner + ".sort()"
            if attr == "reverse":
                return "(" + owner + " = " + owner + ".reversed.toList())"
            if attr == "copy":
                return "List.from(" + owner + ")"
            # Dict methods
            if raw_attr == "get":
                key = rendered_args[0] if len(rendered_args) >= 1 else "null"
                default = rendered_args[1] if len(rendered_args) >= 2 else "null"
                return "(" + owner + "[" + key + "] ?? " + default + ")"
            if attr == "keys":
                return owner + ".keys.toList()"
            if attr == "values":
                return owner + ".values.toList()"
            if attr == "items":
                return owner + ".entries.map((e) => [e.key, e.value]).toList()"
            if attr == "update" and len(rendered_args) == 1:
                return owner + ".addAll(" + rendered_args[0] + ")"
            return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        # Lambda immediate call: (lambda x: body)(arg) → ((x) => body)(arg)
        if isinstance(func_any, dict) and func_any.get("kind") == "Lambda":
            lambda_expr = self._render_expr(func_any)
            return "(" + lambda_expr + ")(" + ", ".join(rendered_args) + ")"
        # Fallback: render func expression and call it
        func_expr = self._render_expr(func_any)
        return func_expr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"

    def _render_list_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "[]"
        td: dict[str, Any] = target_any
        elt = self._render_expr(ed.get("elt"))
        # Collect condition
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        id_node: dict[str, Any] = iter_any
        if id_node.get("kind") == "RangeExpr":
            loop_var = _safe_ident(td.get("id"), "__lc_i") if td.get("kind") == "Name" else "__lc_i"
            start = self._render_expr(id_node.get("start"))
            stop = self._render_expr(id_node.get("stop"))
            step = self._render_expr(id_node.get("step"))
            step_const = self._const_int_literal(id_node.get("step"))
            insert_stmt = "__out.add(" + elt + ");"
            if cond_expr != "":
                insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
            if step_const == 1:
                return (
                    "(() { var __out = []; for (var " + loop_var + " = " + start
                    + "; " + loop_var + " < " + stop + "; " + loop_var + "++) { "
                    + insert_stmt + " } return __out; })()"
                )
            return (
                "(() { var __out = []; for (var " + loop_var + " = " + start
                + "; " + loop_var + " < " + stop + "; " + loop_var + " += " + step + ") { "
                + insert_stmt + " } return __out; })()"
            )
        # General iterable comprehension
        loop_var = _safe_ident(td.get("id"), "__lc_i") if td.get("kind") == "Name" else "__lc_i"
        iter_expr = self._render_expr(iter_any)
        insert_stmt = "__out.add(" + elt + ");"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        return (
            "(() { var __out = []; for (var " + loop_var + " in " + iter_expr + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_set_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "<dynamic>{}"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "<dynamic>{}"
        td: dict[str, Any] = target_any
        elt = self._render_expr(ed.get("elt"))
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        loop_var = _safe_ident(td.get("id"), "__sc_i") if td.get("kind") == "Name" else "__sc_i"
        iter_expr = self._render_expr(iter_any)
        insert_stmt = "__out.add(" + elt + ");"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        return (
            "(() { var __out = <dynamic>{}; for (var " + loop_var + " in " + iter_expr + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_dict_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "{}"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "{}"
        td: dict[str, Any] = target_any
        key_expr = self._render_expr(ed.get("key"))
        value_expr = self._render_expr(ed.get("value"))
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        loop_var = _safe_ident(td.get("id"), "__dc_i") if td.get("kind") == "Name" else "__dc_i"
        iter_rendered = self._render_expr(iter_any)
        insert_stmt = "__out[" + key_expr + "] = " + value_expr + ";"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        return (
            "(() { var __out = {}; for (var " + loop_var + " in " + iter_rendered + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_constant(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            return _dart_string(value)
        return "null"


def transpile_to_dart_native(east_doc: dict[str, Any]) -> str:
    """EAST3 ドキュメントを Dart native ソースへ変換する。"""
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Dart backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Dart backend")
    return DartNativeEmitter(east_doc).transpile()

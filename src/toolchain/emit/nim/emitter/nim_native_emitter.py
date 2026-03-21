"""EAST3 -> Nim native emitter."""

from __future__ import annotations

from toolchain.emit.common.emitter.code_emitter import (
    reject_backend_general_union_type_exprs,
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)

from typing import Any

from toolchain.frontends.runtime_symbol_index import lookup_runtime_module_extern_contract

_NIM_KEYWORDS = {
    "addr", "and", "as", "asm",
    "bind", "block", "break",
    "case", "cast", "concept", "const", "continue", "converter",
    "defer", "discard", "distinct", "div", "do",
    "elif", "else", "end", "enum", "except", "export",
    "finally", "for", "from", "func",
    "if", "import", "in", "include", "interface", "is", "isnot", "iterator",
    "let", "macro", "method", "mixin", "mod", "nil", "not", "notin",
    "object", "of", "or", "out",
    "proc", "ptr", "raise", "ref", "return",
    "shl", "shr", "static",
    "template", "try", "tuple", "type",
    "using", "var", "when", "while", "yield",
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
    while out.startswith("_"):
        out = "v" + out[1:]
    if out[0].isdigit():
        out = "v" + out
    if out in _NIM_KEYWORDS:
        out = "`" + out + "`"
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
    wildcard_modules: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
        sd2: dict[str, Any] = stmt
        if sd2.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = sd2.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = sd2.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        names_any = sd2.get("names")
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
            local_rendered = _safe_ident(local_name)
            target_name = _safe_ident(name)
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
        local_rendered = _safe_ident(local_name_any)
        target_name = _safe_ident(binding_symbol)
        aliases[local_rendered] = (
            target_name if binding_module == "" else binding_module + "." + target_name
        )
        wildcard_resolved[binding_module] = True
    unresolved = [module_id for module_id, resolved in wildcard_resolved.items() if not resolved]
    if len(unresolved) > 0:
        raise RuntimeError(
            "nim native emitter: unsupported relative import form: wildcard import"
        )
    return aliases

def _nim_string(text: str) -> str:
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
    if op == "FloorDiv":
        return "div"
    if op == "Mod":
        return "mod"
    if op == "BitAnd":
        return "and"
    if op == "BitOr":
        return "or"
    if op == "BitXor":
        return "xor"
    if op == "LShift":
        return "shl"
    if op == "RShift":
        return "shr"
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


def _const_int_value(node: Any) -> int | None:
    if not isinstance(node, dict):
        return None
    nd7: dict[str, Any] = node
    kind = nd7.get("kind")
    if kind == "Constant":
        val = nd7.get("value")
        if isinstance(val, bool):
            return None
        if isinstance(val, int):
            return int(val)
        return None
    if kind == "UnaryOp" and nd7.get("op") == "USub":
        operand = nd7.get("operand")
        val = _const_int_value(operand)
        if isinstance(val, int):
            return -val
    return None


def _is_uint8_expr(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    nd6: dict[str, Any] = node
    resolved = nd6.get("resolved_type")
    if not isinstance(resolved, str):
        return False
    return resolved in {"uint8", "byte"}


def _is_int_like_expr(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    nd5: dict[str, Any] = node
    resolved = nd5.get("resolved_type")
    if isinstance(resolved, str) and resolved in {"int", "int64"}:
        return True
    kind = nd5.get("kind")
    if kind == "Constant":
        val = nd5.get("value")
        return isinstance(val, int) and not isinstance(val, bool)
    if kind == "Call":
        fn = nd5.get("func")
        if isinstance(fn, dict) and fn.get("kind") == "Name" and fn.get("id") == "int":
            return True
    return False


def _is_float_like_expr(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    nd4: dict[str, Any] = node
    resolved = nd4.get("resolved_type")
    if isinstance(resolved, str) and resolved in {"float", "float64"}:
        return True
    kind = nd4.get("kind")
    if kind == "Constant":
        val = nd4.get("value")
        return isinstance(val, float)
    if kind == "Call":
        fn = nd4.get("func")
        if isinstance(fn, dict) and fn.get("kind") == "Name" and fn.get("id") == "float":
            return True
    return False


def _is_string_like_expr(node: Any, rendered: str) -> bool:
    if isinstance(node, dict):
        nd3: dict[str, Any] = node
        resolved = nd3.get("resolved_type")
        if isinstance(resolved, str) and resolved == "str":
            return True
        if nd3.get("kind") == "Constant":
            return isinstance(nd3.get("value"), str)
    txt = rendered.strip()
    return txt.startswith("$(") or txt.startswith('"')


def _resolved_runtime_call(expr: dict[str, Any]) -> tuple[str, str]:
    runtime_call_any = expr.get("runtime_call")
    runtime_call = runtime_call_any if isinstance(runtime_call_any, str) else ""
    if runtime_call != "":
        return runtime_call, "runtime_call"
    resolved_any = expr.get("resolved_runtime_call")
    resolved = resolved_any if isinstance(resolved_any, str) else ""
    if resolved != "":
        return resolved, "resolved_runtime_call"
    return "", ""


def _runtime_symbol_name(expr: dict[str, Any]) -> str:
    runtime_symbol_any = expr.get("runtime_symbol")
    if isinstance(runtime_symbol_any, str):
        rs: str = runtime_symbol_any
        return rs.strip()
    runtime_call, _ = _resolved_runtime_call(expr)
    dot = runtime_call.find(".")
    if dot >= 0:
        return runtime_call[dot + 1 :].strip()
    return ""


def _runtime_semantic_tag(expr: dict[str, Any]) -> str:
    semantic_tag_any = expr.get("semantic_tag")
    if isinstance(semantic_tag_any, str):
        ss: str = semantic_tag_any
        return ss.strip()
    return ""


def _has_runtime_extern_module(expr: dict[str, Any]) -> bool:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        return False
    return len(lookup_runtime_module_extern_contract(runtime_module)) > 0


def _matches_math_symbol(expr: dict[str, Any], symbol: str, semantic_tag: str) -> bool:
    if _runtime_symbol_name(expr) != symbol:
        return False
    if _runtime_semantic_tag(expr) == semantic_tag:
        return True
    if _has_runtime_extern_module(expr):
        return True
    runtime_call, _ = _resolved_runtime_call(expr)
    return runtime_call.strip() == "math." + symbol


def _is_math_constant(expr: dict[str, Any]) -> bool:
    return _matches_math_symbol(expr, "pi", "stdlib.symbol.pi") or _matches_math_symbol(
        expr, "e", "stdlib.symbol.e"
    )


def _is_math_sqrt_call(expr: dict[str, Any]) -> bool:
    return _matches_math_symbol(expr, "sqrt", "stdlib.fn.sqrt")


def _arg_is_mutated_in_body(arg_name: str, body: list[Any]) -> bool:
    """Check if a function argument is mutated (appended to, assigned via subscript, etc.)."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _arg_is_mutated_in_node(arg_name, stmt):
            return True
    return False


def _arg_is_mutated_in_node(arg_name: str, node: dict[str, Any]) -> bool:
    """Recursively check if arg_name is mutated in a statement/expression tree."""
    kind = node.get("kind", "")
    # Check for method calls like arg.append(...)
    if kind == "Expr":
        value = node.get("value")
        if isinstance(value, dict) and value.get("kind") == "Call":
            func = value.get("func")
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                owner = func.get("value")
                attr = func.get("attr", "")
                if isinstance(owner, dict) and owner.get("kind") == "Name" and owner.get("id") == arg_name:
                    if attr in {"append", "extend", "insert", "pop", "remove", "clear", "sort", "reverse"}:
                        return True
    # Check for subscript assignment like arg[i] = ...
    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        target = node.get("target")
        targets = node.get("targets")
        if isinstance(targets, list):
            for t in targets:
                if isinstance(t, dict) and t.get("kind") == "Subscript":
                    val = t.get("value")
                    if isinstance(val, dict) and val.get("kind") == "Name" and val.get("id") == arg_name:
                        return True
        if isinstance(target, dict) and target.get("kind") == "Subscript":
            val = target.get("value")
            if isinstance(val, dict) and val.get("kind") == "Name" and val.get("id") == arg_name:
                return True
    # Recurse into sub-statements
    for key in ("body", "orelse", "finalbody", "handlers"):
        sub = node.get(key)
        if isinstance(sub, list):
            for s in sub:
                if isinstance(s, dict) and _arg_is_mutated_in_node(arg_name, s):
                    return True
    return False


class NimNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        reject_backend_general_union_type_exprs(east_doc, backend_name="Nim backend")
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.class_names: set[str] = set()
        self.current_class: str = ""
        self.self_replacement: str = ""
        self.imported_modules: set[str] = set()
        self.declared_vars: set[str] = set()
        self.var_types: dict[str, str] = {}
        self.function_names: set[str] = set()
        self.function_level_vars: set[str] = set()
        self.tmp_counter = 0
        self.scope_stack: list[int] = [0]
        self.next_scope_id = 1
        self.scope_declared: set[tuple[int, str]] = set()
        body_any = east_doc.get("body")
        body = body_any if isinstance(body_any, list) else []
        self.relative_import_name_aliases = _collect_relative_import_name_aliases(east_doc)

    def transpile(self) -> str:
        # Calculate relative path for sub-modules
        meta_any = self.east_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        module_id_val = meta.get("module_id", "")
        module_depth = module_id_val.count(".") if isinstance(module_id_val, str) and module_id_val != "" else 0
        runtime_prefix = "../" * module_depth
        self.lines.append(f'include "{runtime_prefix}py_runtime.nim"')
        self.lines.append("")
        self.lines.append('import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils')

        # Import linked sub-modules from import_bindings
        meta_any = self.east_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        import_bindings_any = meta.get("import_bindings")
        import_bindings = import_bindings_any if isinstance(import_bindings_any, list) else []
        imported_modules: set[str] = set()
        for binding in import_bindings:
            if not isinstance(binding, dict):
                continue
            module_id_any = binding.get("module_id")
            if not isinstance(module_id_any, str):
                continue
            module_id: str = module_id_any
            # Skip pytra standard library modules (provided by runtime)
            if module_id.startswith("pytra.std") or module_id.startswith("pytra.built_in"):
                continue
            binding_kind = binding.get("binding_kind", "")
            export_name = binding.get("export_name", "")
            local_name = binding.get("local_name", "")
            if module_id.startswith("pytra.utils"):
                # e.g. module_id=pytra.utils.gif, export_name=save_gif → gif/east
                # or module_id=pytra.utils, export_name=png → png/east
                parts = module_id.split(".")
                if len(parts) >= 3:
                    # pytra.utils.gif → gif/east
                    import_path = parts[2] + "/east"
                elif binding_kind == "symbol" and export_name != "":
                    import_path = export_name + "/east"
                else:
                    continue
            else:
                # e.g. module_id=io_ops.east → io_ops/east
                import_path = module_id.replace(".", "/")
            if import_path not in imported_modules:
                imported_modules.add(import_path)
                self.lines.append(f'import {import_path}')
            if isinstance(local_name, str) and local_name != "":
                self.imported_modules.add(local_name)
        self.lines.append("")

        body = self.east_doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if isinstance(stmt, dict) and stmt.get("kind") == "ClassDef":
                    self.class_names.add(_safe_ident(stmt.get("name")))
                if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef":
                    self.function_names.add(_safe_ident(stmt.get("name"), "fn"))

            self.declared_vars = set()
            for stmt in body:
                if isinstance(stmt, dict):
                    self._emit_stmt(stmt)

        main_guard = self.east_doc.get("main_guard_body")
        if isinstance(main_guard, list) and len(main_guard) > 0:
            self.lines.append("")
            self.lines.append("if isMainModule:")
            self.indent += 1
            # In Nim, variables assigned in if isMainModule: are global if not in a proc.
            # But let's track them to add 'var' for the first assignment.
            for stmt in main_guard:
                if isinstance(stmt, dict):
                    self._emit_stmt(stmt)
            self.indent -= 1

        return "\n".join(self.lines).rstrip() + "\n"

    def _emit_line(self, text: str) -> None:
        self.lines.append("  " * self.indent + text)

    def _enter_scope(self) -> None:
        self.scope_stack.append(self.next_scope_id)
        self.next_scope_id += 1

    def _leave_scope(self) -> None:
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _scope_key(self, name: str) -> tuple[int, str]:
        if len(self.scope_stack) == 0:
            return (0, name)
        return (self.scope_stack[-1], name)

    def _fresh_tmp(self, prefix: str) -> str:
        name = "__" + prefix + "_" + str(self.tmp_counter)
        self.tmp_counter += 1
        return name

    def _map_type(self, py_type: Any) -> str:
        if not isinstance(py_type, str):
            return "auto"
        ps: str = py_type
        t = ps.strip()
        if t in {"int", "int64"}:
            return "int"
        if t in {"float", "float64"}:
            return "float"
        if t == "str":
            return "string"
        if t == "bool":
            return "bool"
        if t == "None":
            return "void"
        if t == "bytearray":
            return "seq[uint8]"
        if t == "bytes":
            return "seq[uint8]"
        if t.startswith("list["):
            inner = self._map_type(t[5:-1])
            return f"seq[{inner}]"
        if t.startswith("dict["):
            parts = t[5:-1].split(",", 1)
            if len(parts) == 2:
                k = self._map_type(parts[0])
                v = self._map_type(parts[1])
                return f"Table[{k}, {v}]"
            return "Table[auto, auto]"
        if t.startswith("tuple["):
            parts = t[6:-1].split(",")
            mapped = [self._map_type(p.strip()) for p in parts]
            return f"({', '.join(mapped)})"
        if t in self.class_names:
            return t
        return "auto"

    def _default_value_for_type(self, nim_type: str) -> str:
        if nim_type == "int":
            return "0"
        if nim_type == "float":
            return "0.0"
        if nim_type == "bool":
            return "false"
        if nim_type == "string":
            return "\"\""
        if nim_type.startswith("seq["):
            return "@[]"
        if nim_type.startswith("Table["):
            inner = nim_type[len("Table[") : -1] if nim_type.endswith("]") else ""
            parts = [p.strip() for p in inner.split(",", 1)]
            if len(parts) == 2 and parts[0] != "" and parts[1] != "":
                if parts[0] == "auto" or parts[1] == "auto":
                    return "initTable[string, int]()"
                return f"initTable[{parts[0]}, {parts[1]}]()"
            return "initTable[string, int]()"
        if nim_type.startswith("(") and nim_type.endswith(")"):
            inner = nim_type[1:-1]
            parts = [p.strip() for p in inner.split(",") if p.strip() != ""]
            defaults: list[str] = []
            i = 0
            while i < len(parts):
                defaults.append(self._default_value_for_type(parts[i]))
                i += 1
            return "(" + ", ".join(defaults) + ")"
        if nim_type in self.class_names:
            return "nil"
        return "0"

    def _is_unknown_decl_type(self, t: Any) -> bool:
        if not isinstance(t, str):
            return True
        ts: str = t
        tt = ts.strip()
        return tt in {"", "unknown", "auto", "None"}

    def _merge_decl_type(self, prev: Any, cur: Any) -> Any:
        if isinstance(prev, str) and isinstance(cur, str):
            ps: str = prev
            cs: str = cur
            p = ps.strip()
            c = cs.strip()
            if p in {"int", "int64"} and c in {"float", "float64"}:
                return "float64"
            if p in {"float", "float64"} and c in {"int", "int64"}:
                return "float64"
        if self._is_unknown_decl_type(prev) and not self._is_unknown_decl_type(cur):
            return cur
        if not self._is_unknown_decl_type(prev):
            return prev
        return cur

    def _tuple_decl_elem_type(self, tuple_decl: Any, index: int) -> Any:
        if not isinstance(tuple_decl, str):
            return "unknown"
        ts: str = tuple_decl
        txt = ts.strip()
        if not (txt.startswith("tuple[") and txt.endswith("]")):
            return "unknown"
        inner = txt[6:-1]
        parts = [p.strip() for p in inner.split(",")]
        if index < 0 or index >= len(parts):
            return "unknown"
        return parts[index]

    def _collect_declared_locals(self, stmts: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}

        def _put(name: str, decl_type: Any) -> None:
            prev = out.get(name)
            out[name] = self._merge_decl_type(prev, decl_type)

        def _walk_stmt(stmt: Any) -> None:
            if not isinstance(stmt, dict):
                return
            sd: dict[str, Any] = stmt
            kind = sd.get("kind")
            if kind in {"Assign", "AnnAssign"} and bool(sd.get("declare")):
                target = sd.get("target")
                decl_type = sd.get("decl_type")
                if kind == "AnnAssign" and self._is_unknown_decl_type(decl_type):
                    decl_type = sd.get("annotation")
                if self._is_unknown_decl_type(decl_type):
                    value_any = sd.get("value")
                    if isinstance(value_any, dict):
                        vd2: dict[str, Any] = value_any
                        decl_type = vd2.get("resolved_type")
                if isinstance(target, dict):
                    td: dict[str, Any] = target
                    tk = td.get("kind")
                    if tk == "Name":
                        _put(_safe_ident(td.get("id"), "tmp"), decl_type)
                    elif tk == "Tuple":
                        elements_any = td.get("elements")
                        elements = elements_any if isinstance(elements_any, list) else []
                        i = 0
                        while i < len(elements):
                            elem = elements[i]
                            if isinstance(elem, dict) and elem.get("kind") == "Name":
                                _put(_safe_ident(elem.get("id"), "tmp" + str(i)), self._tuple_decl_elem_type(decl_type, i))
                            i += 1
            # recurse over nested statement lists
            for key in ("body", "orelse", "finalbody"):
                child_any = sd.get(key)
                if isinstance(child_any, list):
                    for child in child_any:
                        _walk_stmt(child)
            handlers_any = sd.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            for hd in handlers:
                if isinstance(hd, dict):
                    hd: dict[str, Any] = hd
                    hbody_any = hd.get("body")
                    hbody = hbody_any if isinstance(hbody_any, list) else []
                    for child in hbody:
                        _walk_stmt(child)

        if isinstance(stmts, list):
            for s in stmts:
                _walk_stmt(s)
        return out

    def _infer_return_type_from_body(self, stmts: Any) -> str:
        types: list[str] = []

        def _merge_type(acc: str, cur: str) -> str:
            if acc in {"", "auto", "unknown"}:
                return cur
            if cur in {"", "auto", "unknown"}:
                return acc
            if acc in {"int", "int64"} and cur in {"float", "float64"}:
                return "float"
            if acc in {"float", "float64"} and cur in {"int", "int64"}:
                return "float"
            if acc == cur:
                return acc
            return acc

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                nd2: dict[str, Any] = node
                if nd2.get("kind") == "Return":
                    value_any = nd2.get("value")
                    if isinstance(value_any, dict):
                        vd: dict[str, Any] = value_any
                        rt = self._map_type(vd.get("resolved_type"))
                        if rt == "auto":
                            vk = vd.get("kind")
                            if vk == "Constant":
                                v = vd.get("value")
                                if isinstance(v, bool):
                                    rt = "bool"
                                elif isinstance(v, int) and not isinstance(v, bool):
                                    rt = "int"
                                elif isinstance(v, float):
                                    rt = "float"
                                elif isinstance(v, str):
                                    rt = "string"
                            elif vk == "Attribute":
                                attr = vd.get("attr")
                                if isinstance(attr, str):
                                    if attr in {"kind", "name", "text", "op"}:
                                        rt = "string"
                                    elif attr in {"pos", "value", "left", "right", "expr_index", "kind_tag", "op_tag", "number_value"}:
                                        rt = "int"
                        types.append(rt)
                    else:
                        types.append("void")
                for v in nd2.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)

        _walk(stmts)
        if len(types) == 0:
            return "void"
        out = ""
        i = 0
        while i < len(types):
            t = types[i]
            if t == "void":
                i += 1
                continue
            out = _merge_type(out, t)
            i += 1
        if out == "":
            return "void"
        return out

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        kind = stmt.get("kind")
        if kind == "FunctionDef":
            self._emit_function_def(stmt)
        elif kind == "ClassDef":
            self._emit_class_def(stmt)
        elif kind == "Expr":
            self._emit_expr_stmt(stmt)
        elif kind == "Assign":
            self._emit_assign(stmt)
        elif kind == "AnnAssign":
            self._emit_ann_assign(stmt)
        elif kind == "AugAssign":
            self._emit_aug_assign(stmt)
        elif kind == "Swap":
            self._emit_swap(stmt)
        elif kind == "Return":
            val_node = stmt.get("value")
            val = self._render_expr(val_node) if val_node else ""
            self._emit_line("return " + val)
        elif kind == "If":
            self._emit_if(stmt)
        elif kind == "While":
            self._emit_while(stmt)
        elif kind == "ForCore":
            self._emit_for(stmt)
        elif kind == "Raise":
            self._emit_raise(stmt)
        elif kind == "Try":
            self._emit_try(stmt)
        elif kind == "VarDecl":
            self._emit_var_decl(stmt)
        elif kind == "Pass":
            self._emit_line("discard")
        elif kind == "Import":
            self._emit_import(stmt)
        elif kind == "ImportFrom":
            self._emit_import_from(stmt)
        else:
            raise RuntimeError("nim native emitter: unsupported stmt kind: " + str(kind))

    def _emit_import(self, stmt: dict[str, Any]) -> None:
        pass

    def _emit_import_from(self, stmt: dict[str, Any]) -> None:
        pass

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        raw_name = stmt.get("name")
        name = _safe_ident(raw_name, "fn")
        arg_order = stmt.get("arg_order", [])
        arg_types = stmt.get("arg_types", {})
        body = stmt.get("body", [])
        ret_type = self._map_type(stmt.get("returns"))
        override_ret_any = stmt.get("_nim_return_override")
        if isinstance(override_ret_any, str) and override_ret_any != "":
            ret_type = override_ret_any
        if ret_type == "auto" or ret_type == "":
            inferred_ret = self._infer_return_type_from_body(body)
            if inferred_ret != "":
                ret_type = inferred_ret

        args = []
        old_vars = self.declared_vars
        old_var_types = self.var_types
        old_scope_stack = self.scope_stack
        old_next_scope_id = self.next_scope_id
        old_scope_declared = self.scope_declared
        old_function_level_vars = self.function_level_vars
        self.declared_vars = set()
        self.var_types = {}
        self.function_level_vars = set()
        self.scope_stack = [0]
        self.next_scope_id = 1
        self.scope_declared = set()

        for a in arg_order:
            safe_a = _safe_ident(a)
            self.declared_vars.add(safe_a)
            self.function_level_vars.add(safe_a)
            if self.current_class and safe_a == "self":
                args.append(f"{safe_a}: {self.current_class}")
                self.var_types[safe_a] = self.current_class
            else:
                t = self._map_type(arg_types.get(a))
                # Check if this argument is mutated in the function body
                needs_var = False
                if t.startswith("seq[") or t.startswith("Table["):
                    needs_var = _arg_is_mutated_in_body(a, body)
                if needs_var:
                    args.append(f"{safe_a}: var {t}")
                else:
                    args.append(f"{safe_a}: {t}")
                if t != "auto":
                    self.var_types[safe_a] = t

        old_self_replacement = self.self_replacement
        if raw_name == "__init__":
             name = "new" + self.current_class
             args = args[1:]
             ret_type = self.current_class
             self.self_replacement = "result"
             self.declared_vars.add("result")
             self.function_level_vars.add("result")
             self.var_types["result"] = self.current_class

        header = f"proc {name}*({', '.join(args)})"
        if ret_type != "void" and ret_type != "":
            header += f": {ret_type}"
        elif "return " in str(body):
            header += ": auto"
        self._emit_line(header + " =")

        self.indent += 1
        if raw_name == "__init__":
             self._emit_line(f"new(result)")

        local_decls = self._collect_declared_locals(body)
        for local_name in sorted(local_decls.keys()):
            if local_name in self.declared_vars:
                continue
            mapped_t = self._map_type(local_decls.get(local_name))
            if mapped_t == "auto" or mapped_t == "":
                continue
            self._emit_line(f"var {local_name}: {mapped_t} = {self._default_value_for_type(mapped_t)}")
            self.declared_vars.add(local_name)
            self.function_level_vars.add(local_name)
            self.var_types[local_name] = mapped_t

        if not body:
            self._emit_line("discard")
        else:
            self._enter_scope()
            for s in body:
                if isinstance(s, dict):
                    self._emit_stmt(s)
            self._leave_scope()
        self.indent -= 1
        self.self_replacement = old_self_replacement
        self.declared_vars = old_vars
        self.var_types = old_var_types
        self.function_level_vars = old_function_level_vars
        self.scope_stack = old_scope_stack
        self.next_scope_id = old_next_scope_id
        self.scope_declared = old_scope_declared
        self.lines.append("")

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "Class")
        self.current_class = name

        body = stmt.get("body", [])
        field_map: dict[str, str] = {}

        def _put_field(field_name: str, field_type: str) -> None:
            prev = field_map.get(field_name, "")
            if prev == "" or prev == "auto":
                field_map[field_name] = field_type

        i = 0
        while i < len(body):
            s = body[i]
            if isinstance(s, dict) and s.get("kind") == "AnnAssign":
                target = s.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    field_name = _safe_ident(target.get("id"))
                    field_type = self._map_type(s.get("annotation"))
                    _put_field(field_name, field_type)
            i += 1

        def _collect_init_fields(node: Any) -> None:
            if not isinstance(node, dict):
                return
            nd: dict[str, Any] = node
            nk = nd.get("kind")
            if nk in {"Assign", "AnnAssign"}:
                target = nd.get("target")
                if isinstance(target, dict) and target.get("kind") == "Attribute":
                    value_any = target.get("value")
                    if isinstance(value_any, dict) and value_any.get("kind") == "Name" and value_any.get("id") == "self":
                        field_name = _safe_ident(target.get("attr"), "field")
                        decl_type = nd.get("decl_type")
                        if self._is_unknown_decl_type(decl_type):
                            decl_type = nd.get("annotation")
                        if self._is_unknown_decl_type(decl_type):
                            val_any = nd.get("value")
                            if isinstance(val_any, dict):
                                vd: dict[str, Any] = val_any
                                decl_type = vd.get("resolved_type")
                        field_type = self._map_type(decl_type)
                        if field_type == "auto" or field_type == "":
                            field_type = "int"
                        _put_field(field_name, field_type)
            for key in ("body", "orelse", "finalbody"):
                child_any = nd.get(key)
                if isinstance(child_any, list):
                    j = 0
                    while j < len(child_any):
                        _collect_init_fields(child_any[j])
                        j += 1

        i = 0
        while i < len(body):
            s = body[i]
            if isinstance(s, dict) and s.get("kind") == "FunctionDef" and s.get("name") == "__init__":
                fn_body_any = s.get("body")
                fn_body = fn_body_any if isinstance(fn_body_any, list) else []
                j = 0
                while j < len(fn_body):
                    _collect_init_fields(fn_body[j])
                    j += 1
            i += 1

        self._emit_line(f"type {name}* = ref object")
        self.indent += 1
        has_fields = False
        fields: list[tuple[str, str]] = []
        for field_name in field_map.keys():
            field_type = field_map[field_name]
            fields.append((field_name, field_type))
            if not has_fields:
                has_fields = True
            self._emit_line(f"{field_name}*: {field_type}")
        if not has_fields:
             self._emit_line("discard")
        self.indent -= 1
        self.lines.append("")

        has_init = False
        methods: list[dict[str, Any]] = []
        for s in body:
            if isinstance(s, dict) and s.get("kind") == "FunctionDef":
                methods.append(s)
                if s.get("name") == "__init__":
                    has_init = True
        if not has_init:
            ctor_args: list[str] = []
            i = 0
            while i < len(fields):
                fld_name, fld_type = fields[i]
                ctor_args.append(f"{fld_name}: {fld_type}")
                i += 1
            self._emit_line(f"proc new{name}*({', '.join(ctor_args)}): {name} =")
            self.indent += 1
            self._emit_line("new(result)")
            i = 0
            while i < len(fields):
                fld_name, _ = fields[i]
                self._emit_line(f"result.{fld_name} = {fld_name}")
                i += 1
            self.indent -= 1
            self.lines.append("")

        # Emit forward declarations for methods to avoid order dependency
        i = 0
        while i < len(methods):
            fn = methods[i]
            raw_name = fn.get("name")
            if raw_name != "__init__":
                mname = _safe_ident(raw_name, "fn")
                arg_order_any = fn.get("arg_order")
                arg_order = arg_order_any if isinstance(arg_order_any, list) else []
                arg_types_any = fn.get("arg_types")
                arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
                params: list[str] = []
                j = 0
                while j < len(arg_order):
                    arg = arg_order[j]
                    if not isinstance(arg, str):
                        j += 1
                        continue
                    safe_arg = _safe_ident(arg, "arg" + str(j))
                    if safe_arg == "self":
                        params.append(f"{safe_arg}: {name}")
                    else:
                        params.append(f"{safe_arg}: {self._map_type(arg_types.get(arg))}")
                    j += 1
                ret_type = self._map_type(fn.get("returns"))
                if ret_type == "auto" or ret_type == "":
                    ret_type = self._infer_return_type_from_body(fn.get("body"))
                if ret_type == "seq[auto]" and isinstance(raw_name, str) and raw_name.startswith("new_"):
                    linked_name = raw_name[4:]
                    linked_type = field_map.get(linked_name, "")
                    if linked_type != "":
                        ret_type = linked_type
                if isinstance(ret_type, str):
                    fn["_nim_return_override"] = ret_type
                header = f"proc {mname}*({', '.join(params)})"
                if ret_type not in {"", "void", "auto"}:
                    header += f": {ret_type}"
                self._emit_line(header)
            i += 1
        if len(methods) > 0:
            self.lines.append("")
        
        for s in methods:
            self._emit_function_def(s)
        
        self.current_class = ""

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        value_node = stmt.get("value")
        if isinstance(value_node, dict) and value_node.get("kind") == "Name":
            control_name = value_node.get("id")
            if control_name == "break":
                self._emit_line("break")
                return
            if control_name == "continue":
                self._emit_line("continue")
                return
        expr = self._render_expr(value_node)
        if isinstance(value_node, dict) and value_node.get("kind") == "Call":
            call_name = ""
            fn_any = value_node.get("func")
            if isinstance(fn_any, dict):
                fd: dict[str, Any] = fn_any
                if fd.get("kind") == "Name":
                    raw = fd.get("id")
                    call_name = raw if isinstance(raw, str) else ""
                elif fd.get("kind") == "Attribute":
                    raw = fd.get("attr")
                    call_name = raw if isinstance(raw, str) else ""
            if call_name == "skip_newlines":
                self._emit_line(expr)
                return
            if call_name == "pop":
                self._emit_line("discard " + expr)
                return
            resolved = value_node.get("resolved_type")
            if isinstance(resolved, str) and resolved not in {"", "None", "void", "unknown"}:
                self._emit_line("discard " + expr)
            else:
                self._emit_line(expr)
            return
        if expr.startswith("echo ") or expr.startswith("return ") or ".add(" in expr or "run_" in expr:
            self._emit_line(expr)
        else:
            self._emit_line("discard " + expr)

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target_node = stmt.get("target")
        if not isinstance(target_node, dict):
             targets = stmt.get("targets", [])
             if targets:
                 target_node = targets[0]

        if isinstance(target_node, dict) and target_node.get("kind") == "Tuple":
            value_expr = self._render_expr(stmt.get("value"))
            elements_any = target_node.get("elements")
            elements = elements_any if isinstance(elements_any, list) else []
            names: list[str] = []
            i = 0
            while i < len(elements):
                elem = elements[i]
                if isinstance(elem, dict) and elem.get("kind") == "Name":
                    names.append(_safe_ident(elem.get("id"), "tmp" + str(i)))
                i += 1
            if len(names) > 0:
                tuple_pat = "(" + ", ".join(names) + ")"
                undeclared = [nm for nm in names if nm not in self.declared_vars]
                if len(undeclared) > 0:
                    j = 0
                    while j < len(undeclared):
                        self.declared_vars.add(undeclared[j])
                        j += 1
                    self._emit_line(f"var {tuple_pat} = {value_expr}")
                else:
                    self._emit_line(f"{tuple_pat} = {value_expr}")
                return

        target = self._render_expr(target_node)
        value_node = stmt.get("value")
        value = self._render_expr(value_node)
        if isinstance(target_node, dict) and target_node.get("kind") == "Subscript":
            subscript_type = target_node.get("resolved_type")
            if isinstance(subscript_type, str) and subscript_type in {"uint8", "byte"}:
                value = f"uint8({value})"

        target_name = ""
        if target_node.get("kind") == "Name":
             name = _safe_ident(target_node.get("id"))
             target_name = name
             if bool(stmt.get("declare")) and self.indent > 1:
                  if name in self.function_level_vars:
                      declared_t = self.var_types.get(name, "")
                      if declared_t == "float" and _is_int_like_expr(value_node):
                          value = f"float({value})"
                      elif declared_t == "int" and _is_float_like_expr(value_node):
                          value = f"int({value})"
                      self._emit_line(f"{target} = {value}")
                      return
                  inferred_t = self._map_type(stmt.get("decl_type"))
                  if inferred_t == "auto" and isinstance(value_node, dict):
                      inferred_t = self._map_type(value_node.get("resolved_type"))
                  if inferred_t != "auto" and inferred_t != "":
                      self.var_types[name] = inferred_t
                  self.declared_vars.add(name)
                  scope_key = self._scope_key(name)
                  if scope_key in self.scope_declared:
                      self._emit_line(f"{target} = {value}")
                  else:
                      self.scope_declared.add(scope_key)
                      self._emit_line(f"var {target} = {value}")
                  return
             if name not in self.declared_vars:
                  if self._emit_list_comp_assignment(
                      target=target,
                      value_node=value_node,
                      decl_type="",
                      declare_var=True,
                  ):
                      self.declared_vars.add(name)
                      self.var_types[name] = "seq[auto]"
                      return
                  self.declared_vars.add(name)
                  if self.indent <= 1:
                      self.function_level_vars.add(name)
                  inferred_t = self._map_type(stmt.get("decl_type"))
                  if inferred_t == "auto" and isinstance(value_node, dict):
                      inferred_t = self._map_type(value_node.get("resolved_type"))
                  if inferred_t != "auto" and inferred_t != "":
                      self.var_types[name] = inferred_t
                  self._emit_line(f"var {target} = {value}")
                  return

        if target_name != "":
            declared_t = self.var_types.get(target_name, "")
            if declared_t == "float" and _is_int_like_expr(value_node):
                value = f"float({value})"
            elif declared_t == "int" and _is_float_like_expr(value_node):
                value = f"int({value})"

        if self._emit_list_comp_assignment(
            target=target,
            value_node=value_node,
            decl_type="",
            declare_var=False,
        ):
            return

        self._emit_line(f"{target} = {value}")

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node)."""
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type_any = stmt.get("type")
        var_type = var_type_any.strip() if isinstance(var_type_any, str) else ""
        nim_t = self._map_type(var_type) if var_type != "" else "auto"
        if var_type != "":
            self.var_types[name] = nim_t
        self.declared_vars.add(name)
        self.function_level_vars.add(name)
        default_val = self._default_value_for_type(nim_t)
        if nim_t != "auto":
            self._emit_line(f"var {name}: {nim_t} = {default_val}")
        else:
            self._emit_line(f"var {name} = {default_val}")

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_expr(stmt.get("left"))
        right = self._render_expr(stmt.get("right"))
        tmp = self._fresh_tmp("swap")
        self._emit_line(f"var {tmp} = {left}")
        self._emit_line(f"{left} = {right}")
        self._emit_line(f"{right} = {tmp}")

    def _emit_ann_assign(self, stmt: dict[str, Any]) -> None:
        target_node = stmt.get("target")
        target = self._render_expr(target_node)
        t = self._map_type(stmt.get("annotation"))
        value_node = stmt.get("value")
        
        if target_node.get("kind") == "Name":
             name = _safe_ident(target_node.get("id"))
             if bool(stmt.get("declare")) and self.indent > 1:
                  if name in self.function_level_vars:
                      if value_node:
                          value = self._render_expr(value_node)
                          self._emit_line(f"{target} = {value}")
                      else:
                          self._emit_line("discard")
                      return
                  self.declared_vars.add(name)
                  if t != "":
                      self.var_types[name] = t
                  scope_key = self._scope_key(name)
                  if value_node:
                      value = self._render_expr(value_node)
                      if scope_key in self.scope_declared:
                          self._emit_line(f"{target} = {value}")
                      else:
                          self.scope_declared.add(scope_key)
                          self._emit_line(f"var {target}: {t} = {value}")
                  else:
                      if scope_key in self.scope_declared:
                          self._emit_line("discard")
                      else:
                          self.scope_declared.add(scope_key)
                          self._emit_line(f"var {target}: {t}")
                  return
             if name not in self.declared_vars:
                  if self._emit_list_comp_assignment(
                      target=target,
                      value_node=value_node,
                      decl_type=t,
                      declare_var=True,
                  ):
                      self.declared_vars.add(name)
                      if t != "":
                          self.var_types[name] = t
                      return
                  self.declared_vars.add(name)
                  if self.indent <= 1:
                      self.function_level_vars.add(name)
                  if value_node:
                       value = self._render_expr(value_node)
                       self._emit_line(f"var {target}: {t} = {value}")
                  else:
                       self._emit_line(f"var {target}: {t}")
                  if t != "":
                      self.var_types[name] = t
                  return

        if self._emit_list_comp_assignment(
            target=target,
            value_node=value_node,
            decl_type=t,
            declare_var=False,
        ):
            return

        if value_node:
            value = self._render_expr(value_node)
            self._emit_line(f"{target} = {value} # {t}")
        else:
            self._emit_line(f"discard {target} # {t}")

    def _emit_aug_assign(self, stmt: dict[str, Any]) -> None:
        target = self._render_expr(stmt.get("target"))
        op = _binop_symbol(stmt.get("op", "Add"))
        value = self._render_expr(stmt.get("value"))
        # Nim doesn't support compound assignment for keyword operators
        if op in {"or", "and", "xor", "shl", "shr", "div", "mod"}:
            self._emit_line(f"{target} = {target} {op} {value}")
        else:
            self._emit_line(f"{target} {op}= {value}")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_truthy_expr(stmt.get("test"))
        self._emit_line(f"if {test}:")
        self.indent += 1
        self._enter_scope()
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self._leave_scope()
        self.indent -= 1
        orelse = stmt.get("orelse", [])
        if orelse:
            if len(orelse) == 1 and orelse[0].get("kind") == "If":
                self._emit_elif(orelse[0])
            else:
                self._emit_line("else:")
                self.indent += 1
                self._enter_scope()
                for s in orelse:
                    if isinstance(s, dict):
                        self._emit_stmt(s)
                self._leave_scope()
                self.indent -= 1

    def _emit_elif(self, stmt: dict[str, Any]) -> None:
        test = self._render_truthy_expr(stmt.get("test"))
        self._emit_line(f"elif {test}:")
        self.indent += 1
        self._enter_scope()
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self._leave_scope()
        self.indent -= 1
        orelse = stmt.get("orelse", [])
        if orelse:
            if len(orelse) == 1 and orelse[0].get("kind") == "If":
                self._emit_elif(orelse[0])
            else:
                self._emit_line("else:")
                self.indent += 1
                self._enter_scope()
                for s in orelse:
                    if isinstance(s, dict):
                        self._emit_stmt(s)
                self._leave_scope()
                self.indent -= 1

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_truthy_expr(stmt.get("test"))
        self._emit_line(f"while {test}:")
        self.indent += 1
        self._enter_scope()
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self._leave_scope()
        self.indent -= 1

    def _emit_try(self, stmt: dict[str, Any]) -> None:
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        handlers_any = stmt.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        for child in body:
            if isinstance(child, dict):
                self._emit_stmt(child)
        for handler in handlers:
            if not isinstance(handler, dict):
                continue
            body_any = handler.get("body")
            body = body_any if isinstance(body_any, list) else []
            for child in body:
                if isinstance(child, dict):
                    self._emit_stmt(child)
        for key in ("orelse", "finalbody"):
            block_any = stmt.get(key)
            block = block_any if isinstance(block_any, list) else []
            for child in block:
                if isinstance(child, dict):
                    self._emit_stmt(child)

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_plan = stmt.get("target_plan")
        iter_plan = stmt.get("iter_plan")
        target_name = "it"
        tuple_targets: list[str] = []
        if isinstance(target_plan, dict):
            td: dict[str, Any] = target_plan
            plan_kind = td.get("kind")
            if plan_kind == "NameTarget":
                target_name = _safe_ident(td.get("id"))
            elif plan_kind == "TupleTarget":
                elements_any = td.get("elements")
                elements = elements_any if isinstance(elements_any, list) else []
                i = 0
                while i < len(elements):
                    elem = elements[i]
                    if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                        tuple_targets.append(_safe_ident(elem.get("id"), "it" + str(i)))
                    i += 1

        if len(tuple_targets) > 0 and isinstance(iter_plan, dict) and iter_plan.get("kind") == "RuntimeIterForPlan":
            iter_expr_any = iter_plan.get("iter_expr")
            if (
                isinstance(iter_expr_any, dict)
                and iter_expr_any.get("kind") == "Call"
                and isinstance(iter_expr_any.get("func"), dict)
                and iter_expr_any["func"].get("kind") == "Name"
                and iter_expr_any["func"].get("id") == "enumerate"
            ):
                args_any = iter_expr_any.get("args")
                args = args_any if isinstance(args_any, list) else []
                if len(args) == 1 and len(tuple_targets) == 2:
                    iterable = self._render_expr(args[0])
                    self.declared_vars.add(tuple_targets[0])
                    self.declared_vars.add(tuple_targets[1])
                    self._emit_line(f"for {tuple_targets[0]}, {tuple_targets[1]} in pairs({iterable}):")
                    self.indent += 1
                    self._enter_scope()
                    for s in stmt.get("body", []):
                        if isinstance(s, dict):
                            self._emit_stmt(s)
                    self._leave_scope()
                    self.indent -= 1
                    return

        self.declared_vars.add(target_name)

        if isinstance(iter_plan, dict) and iter_plan.get("kind") == "StaticRangeForPlan":
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            step_node = iter_plan.get("step")
            step_expr = self._render_expr(step_node)
            step_const = _const_int_value(step_node)
            if step_const == 1:
                self._emit_line(f"for {target_name} in {start} ..< {stop}:")
            elif step_const == -1:
                self._emit_line(f"for {target_name} in countdown({start}, ({stop}) + 1):")
            elif isinstance(step_const, int) and step_const > 1:
                self._emit_line(f"for {target_name} in countup({start}, ({stop}) - 1, {step_const}):")
            elif isinstance(step_const, int) and step_const < -1:
                self._emit_line(f"for {target_name} in countdown({start}, ({stop}) + 1, {0 - step_const}):")
            else:
                self._emit_line(f"for {target_name} in py_range({start}, {stop}, {step_expr}):")
        else:
            expr = self._render_expr(iter_plan.get("iter_expr") if isinstance(iter_plan, dict) else None)
            self._emit_line(f"for {target_name} in {expr}:")
        
        self.indent += 1
        self._enter_scope()
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self._leave_scope()
        self.indent -= 1

    def _emit_raise(self, stmt: dict[str, Any]) -> None:
        exc = self._render_expr(stmt.get("exc"))
        self._emit_line(f"raise newException(Exception, {exc})")

    def _emit_list_comp_assignment(
        self,
        *,
        target: str,
        value_node: Any,
        decl_type: str,
        declare_var: bool,
    ) -> bool:
        if not isinstance(value_node, dict):
            return False
        vd: dict[str, Any] = value_node
        if vd.get("kind") != "ListComp":
            return False
        gens_any = vd.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1:
            return False
        gen = gens[0]
        if not isinstance(gen, dict):
            return False
        gd: dict[str, Any] = gen
        ifs_any = gd.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return False
        target_any = gd.get("target")
        if not isinstance(target_any, dict):
            return False
        td: dict[str, Any] = target_any
        if td.get("kind") != "Name":
            return False
        loop_var = _safe_ident(td.get("id"), "__lc_it")
        if loop_var == "_":
            loop_var = "__lc_it"
        iter_expr = self._render_expr(gd.get("iter"))
        elt_expr = self._render_expr(vd.get("elt"))
        if declare_var:
            if decl_type != "":
                self._emit_line(f"var {target}: {decl_type} = @[]")
            else:
                self._emit_line(f"var {target} = @[]")
        else:
            self._emit_line(f"{target} = @[]")
        self._emit_line(f"for {loop_var} in {iter_expr}:")
        self.indent += 1
        self._emit_line(f"{target}.add({elt_expr})")
        self.indent -= 1
        return True

    def _render_truthy_expr(self, expr_node: Any) -> str:
        if not isinstance(expr_node, dict):
            return "false"
        ed: dict[str, Any] = expr_node
        kind = ed.get("kind")
        if kind == "Compare":
            return self._render_expr(expr_node)
        if kind == "Constant":
            val = ed.get("value")
            if isinstance(val, bool):
                 return "true" if val else "false"
        
        rendered = self._render_expr(expr_node)
        return f"py_truthy({rendered})"

    def _render_expr(self, expr: Any) -> str:
        if not isinstance(expr, dict):
            return "nil"
        ed: dict[str, Any] = expr
        kind = ed.get("kind")
        if kind == "Constant":
            val = ed.get("value")
            if isinstance(val, str):
                return _nim_string(val)
            if isinstance(val, bool):
                return "true" if val else "false"
            if val is None:
                return "nil"
            return str(val)
        elif kind == "Name":
            name = ed.get("id")
            if name == "self" and self.self_replacement:
                 return self.self_replacement
            if name == "main" and "main" not in self.function_names and "v_pytra_main" in self.function_names:
                 return "v_pytra_main"
            rendered = _safe_ident(name)
            return self.relative_import_name_aliases.get(rendered, rendered)
        elif kind == "UnaryOp":
            op = ed.get("op")
            if op == "Not":
                operand = self._render_truthy_expr(ed.get("operand"))
                return f"(not {operand})"
            operand = self._render_expr(ed.get("operand"))
            if op == "Invert":
                return f"(not {operand})"
            if op == "USub":
                return f"(-{operand})"
            return operand
        elif kind == "BinOp":
            left_node = ed.get("left")
            right_node = ed.get("right")
            left = self._render_expr(left_node)
            right = self._render_expr(right_node)
            op_raw = ed.get("op")
            resolved = ed.get("resolved_type")
            
            if op_raw == "Div":
                 # Nim / is for floats. If either is int, convert to float.
                 return f"(float({left}) / float({right}))"
            
            if op_raw == "Mod":
                if isinstance(resolved, str) and resolved in {"int", "int64"}:
                    return f"py_mod(int({left}), int({right}))"
                return f"py_mod({left}, {right})"
            if op_raw == "Mult":
                if isinstance(left_node, dict) and left_node.get("kind") == "List":
                    left_elts_any = left_node.get("elements")
                    left_elts = left_elts_any if isinstance(left_elts_any, list) else []
                    if len(left_elts) == 1:
                        elt_expr = self._render_expr(left_elts[0])
                        return f"newSeqWith(int({right}), {elt_expr})"
                if isinstance(right_node, dict) and right_node.get("kind") == "List":
                    right_elts_any = right_node.get("elements")
                    right_elts = right_elts_any if isinstance(right_elts_any, list) else []
                    if len(right_elts) == 1:
                        elt_expr = self._render_expr(right_elts[0])
                        return f"newSeqWith(int({left}), {elt_expr})"
            symbol = _binop_symbol(op_raw)
            if isinstance(resolved, str) and resolved in {"float", "float64"} and op_raw in {"Add", "Sub", "Mult"}:
                return f"(float({left}) {symbol} float({right}))"
            if op_raw == "Add":
                if (isinstance(resolved, str) and resolved == "str") or _is_string_like_expr(left_node, left) or _is_string_like_expr(right_node, right):
                    return f"($({left}) & $({right}))"
            return f"({left} {symbol} {right})"
        elif kind == "BoolOp":
            op = "and" if ed.get("op") == "And" else "or"
            values = [self._render_truthy_expr(v) for v in ed.get("values", [])]
            if len(values) == 0:
                return "false"
            return "(" + (" " + op + " ").join(values) + ")"
        elif kind == "Compare":
            left_node = ed.get("left")
            left = self._render_expr(left_node)
            ops = ed.get("ops", [])
            comps = ed.get("comparators", [])
            if not ops:
                return left
            op = ops[0]
            right_node = comps[0]
            right = self._render_expr(right_node)
            if op == "In" or op == "NotIn":
                in_expr = ""
                right_t = right_node.get("resolved_type") if isinstance(right_node, dict) else ""
                if isinstance(right_t, str) and right_t.startswith("dict["):
                    in_expr = f"hasKey({right}, {left})"
                else:
                    in_expr = f"({left} in {right})"
                if op == "NotIn":
                    return f"(not {in_expr})"
                return in_expr
            if _is_uint8_expr(left_node) and not _is_uint8_expr(right_node):
                left = f"int({left})"
            if _is_uint8_expr(right_node) and not _is_uint8_expr(left_node):
                right = f"int({right})"
            symbol = _cmp_symbol(op)
            return f"({left} {symbol} {right})"
        elif kind == "Call":
            return self._render_call(expr)
        elif kind == "List":
            elts = [self._render_expr(e) for e in ed.get("elements", [])]
            return f"@[{', '.join(elts)}]"
        elif kind == "Tuple":
            elements = ed.get("elements", [])
            elts = [self._render_expr(e) for e in elements]
            return f"({', '.join(elts)})"
        elif kind == "Dict":
            entries = ed.get("entries", [])
            pairs = []
            for entry in entries:
                k = self._render_expr(entry.get("key"))
                v = self._render_expr(entry.get("value"))
                pairs.append(f"{k}: {v}")
            if len(pairs) == 0:
                mapped = self._map_type(ed.get("resolved_type"))
                if isinstance(mapped, str) and mapped.startswith("Table["):
                    return self._default_value_for_type(mapped)
                return "initTable[string, int]()"
            return f"{{ {', '.join(pairs)} }}.toTable"
        elif kind == "ListComp":
            elt = self._render_expr(ed.get("elt"))
            gens = ed.get("generators", [])
            if len(gens) == 1:
                gen = gens[0]
                target = self._render_expr(gen.get("target"))
                iter_expr = self._render_expr(gen.get("iter"))
                ifs = gen.get("ifs", [])
                if not ifs:
                    return f"(block: var res: seq[auto] = @[]; for {target} in {iter_expr}: res.add({elt}); res)"
                else:
                    cond = " and ".join([self._render_truthy_expr(i) for i in ifs])
                    return f"(block: var res: seq[auto] = @[]; for {target} in {iter_expr}: (if {cond}: res.add({elt})); res)"
            return "@[] # complex ListComp"
        elif kind == "IfExp":
            test_expr = self._render_truthy_expr(ed.get("test"))
            body_expr = self._render_expr(ed.get("body"))
            else_expr = self._render_expr(ed.get("orelse"))
            return f"(if {test_expr}: {body_expr} else: {else_expr})"
        elif kind == "RangeExpr":
            start = self._render_expr(ed.get("start"))
            stop = self._render_expr(ed.get("stop"))
            step_node = ed.get("step")
            step_expr = self._render_expr(step_node)
            step_const = _const_int_value(step_node)
            if step_const == 1:
                return f"({start} ..< {stop})"
            if step_const == -1:
                return f"countdown({start}, ({stop}) + 1)"
            return f"py_range({start}, {stop}, {step_expr})"
        elif kind == "ObjLen":
            return f"{self._render_expr(ed.get('value'))}.len"
        elif kind == "ObjStr":
            return f"$({self._render_expr(ed.get('value'))})"
        elif kind == "ObjBool":
            return self._render_truthy_expr(ed.get("value"))
        elif kind == "IsInstance":
            return "false"
        elif kind == "Subscript":
            value = self._render_expr(ed.get("value"))
            slice_node = ed.get("slice")
            if isinstance(slice_node, dict) and slice_node.get("kind") == "Slice":
                lower_node = slice_node.get("lower")
                upper_node = slice_node.get("upper")
                lower = self._render_expr(lower_node) if lower_node else "0"
                upper = self._render_expr(upper_node) if upper_node else f"({value}.len)"
                return f"{value}[{lower} ..< {upper}]"
            idx_node = slice_node if isinstance(slice_node, dict) else None
            idx = self._render_expr(slice_node)
            idx_const = _const_int_value(idx_node)
            base = f"{value}[{idx}]"
            if isinstance(idx_const, int) and idx_const < 0:
                base = f"{value}[({value}.len + {idx})]"
            resolved = ed.get("resolved_type")
            if isinstance(resolved, str) and resolved == "str":
                return f"$({base})"
            return base
        elif kind == "Attribute":
            value_node = ed.get("value")
            value = self._render_expr(value_node)
            attr = _safe_ident(ed.get("attr"))
            semantic_tag_any = ed.get("semantic_tag")
            semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
            runtime_call, runtime_source = _resolved_runtime_call(expr)
            if semantic_tag.startswith("stdlib.") and runtime_call == "":
                raise RuntimeError("nim native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
            resolved_runtime_any = ed.get("resolved_runtime_call")
            resolved_runtime = resolved_runtime_any if isinstance(resolved_runtime_any, str) else ""
            resolved_source_any = ed.get("resolved_runtime_source")
            resolved_source = resolved_source_any if isinstance(resolved_source_any, str) else ""
            if _is_math_constant(expr):
                if _runtime_symbol_name(expr) == "pi":
                    return "PI"
                if _runtime_symbol_name(expr) == "e":
                    return "E"
            # Fallback: math.pi / math.e without semantic_tag
            if isinstance(value_node, dict) and value_node.get("kind") == "Name":
                owner_name = value_node.get("id")
                if owner_name == "math":
                    if attr == "pi":
                        return "PI"
                    if attr == "e":
                        return "E"
            if resolved_source == "module_attr" and resolved_runtime != "" and "." not in resolved_runtime:
                return _safe_ident(resolved_runtime)
            if semantic_tag.startswith("stdlib.") and runtime_source == "resolved_runtime_call":
                raise RuntimeError(
                    "nim native emitter: unresolved stdlib runtime attribute mapping: "
                    + semantic_tag
                    + " ("
                    + runtime_call
                    + ")"
                )
            # Linked sub-module attribute → direct reference
            if isinstance(value_node, dict) and value_node.get("kind") == "Name":
                owner_name = value_node.get("id")
                if isinstance(owner_name, str) and owner_name in self.imported_modules:
                    return attr
            return f"{value}.{attr}"
        elif kind == "Unbox" or kind == "Box":
            return self._render_expr(ed.get("value"))
        return "0"

    def _render_call(self, expr: dict[str, Any]) -> str:
        func = expr.get("func")
        args_nodes = expr.get("args", [])
        args = [self._render_expr(a) for a in args_nodes]
        kw_any = expr.get("keywords")
        keywords = kw_any if isinstance(kw_any, list) else []
        i_kw = 0
        while i_kw < len(keywords):
            kw = keywords[i_kw]
            if isinstance(kw, dict) and "value" in kw:
                args.append(self._render_expr(kw.get("value")))
            i_kw += 1
        semantic_tag_any = expr.get("semantic_tag")
        semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
        runtime_call, runtime_source = _resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and semantic_tag != "stdlib.symbol.Path" and runtime_call == "":
            raise RuntimeError("nim native emitter: unresolved stdlib runtime call: " + semantic_tag)
        if runtime_source == "resolved_runtime_call" and _is_math_sqrt_call(expr) and len(args) == 1:
            return f"math.sqrt(float({args[0]}))"
        # Fallback: math.sqrt / math.sin / math.cos etc. via Attribute call
        if isinstance(func, dict) and func.get("kind") == "Attribute":
            func_value = func.get("value")
            func_attr = func.get("attr")
            if isinstance(func_value, dict) and func_value.get("kind") == "Name" and func_value.get("id") == "math":
                if isinstance(func_attr, str):
                    if func_attr == "sqrt" and len(args) == 1:
                        return f"math.sqrt(float({args[0]}))"
                    if func_attr in {"sin", "cos", "tan", "exp", "log", "log10", "fabs", "floor", "ceil", "atan2"}:
                        float_args = [f"float({a})" for a in args]
                        return f"math.{func_attr}({', '.join(float_args)})"
                    if func_attr == "pow" and len(args) == 2:
                        return f"math.pow(float({args[0]}), float({args[1]}))"
            # Linked sub-module method call → direct function call
            if isinstance(func_value, dict) and func_value.get("kind") == "Name":
                owner_name = func_value.get("id")
                if isinstance(owner_name, str) and owner_name in self.imported_modules:
                    if isinstance(func_attr, str):
                        return f"{func_attr}({', '.join(args)})"
        if isinstance(func, dict) and func.get("kind") == "Name":
            name = func.get("id")
            if name == "print":
                if len(args) == 0:
                    return "echo \"\""
                if len(args) == 1:
                    return f"echo py_str({args[0]})"
                joined = " & \" \" & ".join([f"py_str({a})" for a in args])
                return f"echo {joined}"
            if name == "open":
                # Convert Python file mode string to Nim FileMode
                if len(args) >= 2:
                    mode_map = {'"wb"': "fmWrite", '"w"': "fmWrite", '"rb"': "fmRead", '"r"': "fmRead", '"a"': "fmAppend", '"ab"': "fmAppend"}
                    nim_mode = mode_map.get(args[1].strip(), "fmRead")
                    return f"open({args[0]}, {nim_mode})"
                return f"open({args[0]})"
            if name == "len":
                return f"{args[0]}.len"
            if name == "int":
                if len(args_nodes) > 0:
                    arg0_node = args_nodes[0]
                    if isinstance(arg0_node, dict):
                        ad2: dict[str, Any] = arg0_node
                        arg0_t = ad2.get("resolved_type")
                        if isinstance(arg0_t, str) and arg0_t == "str":
                            return f"parseInt({args[0]})"
                return f"int({args[0]})"
            if name == "float":
                if len(args_nodes) > 0:
                    arg0_node = args_nodes[0]
                    if isinstance(arg0_node, dict):
                        ad: dict[str, Any] = arg0_node
                        arg0_t = ad.get("resolved_type")
                        if isinstance(arg0_t, str) and arg0_t == "str":
                            return f"parseFloat({args[0]})"
                return f"float({args[0]})"
            if name == "str":
                return f"$( {args[0]} )"
            if name == "range":
                if len(args) == 1:
                    return f"0 ..< {args[0]}"
                if len(args) == 2:
                    return f"{args[0]} ..< {args[1]}"
            if name == "enumerate":
                if len(args) == 1:
                    return f"pairs({args[0]})"
                return "pairs(@[])"
            if name in {"RuntimeError", "ValueError", "TypeError"}:
                if len(args) >= 1:
                    return args[0]
                return _nim_string(name)
            if name == "perf_counter":
                return "epochTime()"
            if name == "bytearray":
                 if len(args) == 0:
                     return "newSeq[uint8]()"
                 return f"newSeq[uint8](int({args[0]}))"
            if name == "bytes":
                if len(args) == 0:
                    return "@[]"
                return args[0]
            if name in self.class_names:
                 return f"new{name}({', '.join(args)})"
        
        if isinstance(func, dict) and func.get("kind") == "Attribute":
            value_node = func.get("value")
            value = self._render_expr(value_node)
            attr = func.get("attr")
            if attr == "append":
                 resolved = value_node.get("resolved_type")
                 if resolved == "bytearray":
                      return f"{value}.add(uint8({', '.join(args)}))"
                 return f"{value}.add({', '.join(args)})"
            if attr == "get":
                 if len(args) >= 2:
                      return f"getOrDefault({value}, {args[0]}, {args[1]})"
                 if len(args) == 1:
                      return f"getOrDefault({value}, {args[0]})"
            if attr == "isdigit":
                 return f"py_isdigit({value})"
            if attr == "isalpha":
                 return f"py_isalpha({value})"

        if semantic_tag.startswith("stdlib.") and runtime_source == "resolved_runtime_call":
            raise RuntimeError(
                "nim native emitter: unresolved stdlib runtime mapping: "
                + semantic_tag
                + " ("
                + runtime_call
                + ")"
            )
        func_expr = self._render_expr(func)
        return f"{func_expr}({', '.join(args)})"

def transpile_to_nim_native(east_doc: dict[str, Any]) -> str:
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Nim backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Nim backend")
    emitter = NimNativeEmitter(east_doc)
    return emitter.transpile()

"""EAST3 -> Zig native emitter (minimal skeleton)."""

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


_ZIG_KEYWORDS = {
    "addrspace", "align", "allowzero", "and", "anyframe", "anytype",
    "asm", "async", "await", "break", "callconv", "catch", "comptime",
    "const", "continue", "defer", "else", "enum", "errdefer", "error",
    "export", "extern", "false", "fn", "for", "if", "inline",
    "linksection", "noalias", "nosuspend", "null", "opaque", "or",
    "orelse", "packed", "pub", "resume", "return", "struct", "suspend",
    "switch", "test", "threadlocal", "true", "try", "undefined",
    "union", "unreachable", "var", "volatile", "while",
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
    if out in _ZIG_KEYWORDS:
        out = "@\"" + out + "\""
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
                raise RuntimeError(
                    "zig native emitter: unsupported relative import form: wildcard import"
                )
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    return aliases


def _zig_string(text: str) -> str:
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
    if op == "FloorDiv":
        return "/@"
    if op == "Mod":
        return "%"
    if op == "Pow":
        return "**"
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
    if op == "BitAnd":
        return "&"
    raise RuntimeError("lang=zig unsupported binop: " + op)


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
    if op == "Is":
        return "=="
    if op == "IsNot":
        return "!="
    raise RuntimeError("lang=zig unsupported compare op: " + op)


def _runtime_module_symbol_names(runtime_module_id: str) -> tuple[str, ...]:
    symbols = lookup_runtime_module_symbols(runtime_module_id)
    if symbols is None:
        return ()
    return tuple(s.name for s in symbols)


def _runtime_symbol_call_adapter_kind(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return ""
    return doc.call_adapter_kind


def _runtime_symbol_semantic_tag(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return ""
    return doc.semantic_tag


def _is_math_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    tag = _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol)
    return tag == "math"


def _is_perf_counter_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return runtime_symbol == "perf_counter" or runtime_symbol == "perf_counter_ns"


def _is_compile_time_std_import_symbol(module_id: str, symbol: str) -> bool:
    return symbol in _COMPILETIME_STD_IMPORT_SYMBOLS


def _pascal_symbol_name(name: str) -> str:
    parts = name.split("_")
    out_parts: list[str] = []
    for part in parts:
        if part == "":
            continue
        out_parts.append(part[0].upper() + part[1:])
    return "".join(out_parts)


def _runtime_symbol_alias_expr(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return "__pytra_" + runtime_symbol
    adapter = doc.call_adapter_kind
    if adapter == "direct":
        return "__pytra_" + runtime_symbol
    if adapter == "method":
        return "__pytra_" + runtime_symbol
    return "__pytra_" + runtime_symbol


class ZigNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=zig invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=zig invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=zig unsupported east_stage: " + str(ed.get("east_stage")))
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

    def _is_top_level_decl(self, stmt: dict[str, Any]) -> bool:
        """トップレベル宣言（関数/クラス/import/型エイリアス）かどうか判定する。"""
        kind = stmt.get("kind")
        return kind in {"FunctionDef", "ClassDef", "Import", "ImportFrom", "TypeAlias"}

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="// ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        self.lines.append("const std = @import(\"std\");")
        self.lines.append("const pytra = @import(\"py_runtime.zig\");")
        self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        # トップレベル宣言（fn, struct）を先に emit
        for stmt in body:
            if self._is_top_level_decl(stmt):
                self._emit_stmt(stmt)
        # トップレベルステートメント + main_guard_body を pub fn main() に入れる
        top_stmts: list[dict[str, Any]] = []
        for stmt in body:
            if not self._is_top_level_decl(stmt):
                top_stmts.append(stmt)
        for stmt in main_guard:
            top_stmts.append(stmt)
        if len(top_stmts) > 0:
            self.lines.append("pub fn main() void {")
            self.indent += 1
            for stmt in top_stmts:
                self._emit_stmt(stmt)
            self.indent -= 1
            self.lines.append("}")
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
        for stmt in body:
            self._emit_stmt(stmt)

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "FunctionDef":
                name = _safe_ident(stmt.get("name"), "fn")
                self.function_names.add(name)
            if kind == "ClassDef":
                name = _safe_ident(stmt.get("name"), "Class")
                self.class_names.add(name)

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
            if val == "null":
                self._emit_line("return;")
            else:
                self._emit_line("return " + val + ";")
            return
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value_node = stmt.get("value")
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "undefined"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type = self._infer_decl_type(stmt)
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                zig_ty = self._zig_type(decl_type)
                if len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                if value_node is None and bool(stmt.get("declare")):
                    self._emit_line("var " + target + ": " + zig_ty + " = undefined;")
                else:
                    self._emit_line("var " + target + ": " + zig_ty + " = " + value + ";")
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
                if td2.get("kind") == "Name":
                    target_name = _safe_ident(td2.get("id"), "value")
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        zig_ty = self._zig_type(decl_type)
                        self._emit_line("var " + target + ": " + zig_ty + " = " + value + ";")
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
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        zig_ty = self._zig_type(decl_type)
                        self._emit_line("var " + target + ": " + zig_ty + " = " + value + ";")
                        return
                self._emit_line(target + " = " + value + ";")
                return
            raise RuntimeError("lang=zig unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            aug_op = self._aug_assign_op(op)
            self._emit_line(target + " " + aug_op + " " + value + ";")
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
            expr_text = self._render_expr(value_any)
            if isinstance(value_any, dict) and value_any.get("kind") == "Call":
                self._emit_line(expr_text + ";")
            else:
                self._emit_line("_ = " + expr_text + ";")
            return
        if kind == "Raise":
            exc_any = stmt.get("exc")
            if isinstance(exc_any, dict) and exc_any.get("kind") == "Call":
                fn_any = exc_any.get("func")
                if isinstance(fn_any, dict) and fn_any.get("kind") == "Name":
                    fn_name = _safe_ident(fn_any.get("id"), "")
                    args_any = exc_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) > 0:
                        self._emit_line("@panic(" + self._render_expr(args[0]) + ");")
                        return
                    self._emit_line("@panic(\"error\");")
                    return
            if isinstance(exc_any, dict):
                self._emit_line("@panic(" + self._render_expr(exc_any) + ");")
            else:
                self._emit_line("@panic(\"error\");")
            return
        if kind == "Try":
            body = self._dict_list(stmt.get("body"))
            for sub in body:
                self._emit_stmt(sub)
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
            self._emit_line("// pass")
            return
        if kind == "Swap":
            self._emit_swap(stmt)
            return
        if kind == "TypeAlias":
            alias_name = _safe_ident(stmt.get("name"), "T")
            self._emit_line("const " + alias_name + " = PyObject;  // type alias")
            return
        if kind == "Yield":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("_ = " + val + ";  // yield (unsupported)")
            return
        if kind == "Delete":
            return
        if kind == "Assert":
            test = self._render_expr(stmt.get("test"))
            self._emit_line("std.debug.assert(" + test + ");")
            return
        if kind == "Global" or kind == "Nonlocal":
            return
        raise RuntimeError("lang=zig unsupported stmt kind: " + str(kind))

    def _resolve_arg_zig_type(self, arg_name: str, raw_name: Any, arg_types: dict[str, Any]) -> str:
        """引数の型を EAST3 の arg_types から解決して Zig 型を返す。"""
        raw_any = arg_types.get(raw_name) if isinstance(raw_name, str) else None
        if not isinstance(raw_any, str):
            raw_any = arg_types.get(arg_name)
        py_type = raw_any.strip() if isinstance(raw_any, str) else ""
        return self._zig_type(py_type)

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn_")
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        arg_strs: list[str] = []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        i = 0
        while i < len(arg_names):
            raw_name = args[i] if i < len(args) else arg_names[i]
            zig_ty = self._resolve_arg_zig_type(arg_names[i], raw_name, arg_types)
            arg_strs.append(arg_names[i] + ": " + zig_ty)
            i += 1
        ret_type_any = stmt.get("return_type")
        ret_py = ret_type_any.strip() if isinstance(ret_type_any, str) else ""
        ret_type = self._zig_type(ret_py)
        self._emit_line("fn " + name + "(" + ", ".join(arg_strs) + ") " + ret_type + " {")
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

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        target_plan = stmt.get("target_plan")
        iter_plan = stmt.get("iter_plan")
        target_name = "_"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "i")
        elif isinstance(stmt.get("target"), dict) and stmt["target"].get("kind") == "Name":
            target_name = _safe_ident(stmt["target"].get("id"), "i")
        if isinstance(iter_plan, dict) and iter_plan.get("kind") == "StaticRangeForPlan":
            self._emit_static_range_for(stmt, target_name, iter_plan)
            return
        iter_any = stmt.get("iter")
        if isinstance(iter_any, dict) and iter_any.get("kind") == "Call":
            func_any = iter_any.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Name":
                fname = str(func_any.get("id"))
                if fname == "range":
                    self._emit_range_for_from_call(stmt, target_name, iter_any)
                    return
        iter_expr = self._render_expr(iter_any)
        self._emit_line("for (" + iter_expr + ") |" + target_name + "| {")
        self.indent += 1
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(target_name)
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_static_range_for(self, stmt: dict[str, Any], target_name: str, plan: dict[str, Any]) -> None:
        start = self._render_expr(plan.get("start"))
        stop = self._render_expr(plan.get("stop"))
        step_any = plan.get("step")
        step = self._render_expr(step_any) if isinstance(step_any, dict) else "1"
        self._emit_line("var " + target_name + ": i64 = " + start + ";")
        self._emit_line("while (" + target_name + " < " + stop + ") : (" + target_name + " += " + step + ") {")
        self.indent += 1
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(target_name)
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_range_for_from_call(self, stmt: dict[str, Any], target_name: str, iter_node: dict[str, Any]) -> None:
        args_any = iter_node.get("args")
        args = args_any if isinstance(args_any, list) else []
        if len(args) == 1:
            end = self._render_expr(args[0])
            self._emit_line("var " + target_name + ": i64 = 0;")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += 1) {")
        elif len(args) == 2:
            start = self._render_expr(args[0])
            end = self._render_expr(args[1])
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += 1) {")
        elif len(args) == 3:
            start = self._render_expr(args[0])
            end = self._render_expr(args[1])
            step = self._render_expr(args[2])
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += " + step + ") {")
        else:
            self._emit_line("// unsupported range args count")
            self._emit_line("while (false) {")
        self.indent += 1
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(target_name)
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("while (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class")
        self._emit_line("const " + cls_name + " = struct {")
        self.indent += 1
        body = self._dict_list(stmt.get("body"))
        dataclass_fields: list[str] = []
        if bool(stmt.get("dataclass")):
            for sub in body:
                if sub.get("kind") != "AnnAssign":
                    continue
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    decl_type_any = sub.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    self._emit_line(field_name + ": " + zig_ty + ",")
                    dataclass_fields.append(field_name)
        for sub in body:
            if sub.get("kind") == "AnnAssign" and bool(stmt.get("dataclass")):
                continue
            if sub.get("kind") == "FunctionDef":
                self._emit_class_method(cls_name, sub)
            elif sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    decl_type_any = sub.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    self._emit_line(field_name + ": " + zig_ty + ",")
        self.indent -= 1
        self._emit_line("};")
        self._emit_line("")

    def _emit_class_method(self, cls_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        arg_strs: list[str] = []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        has_self = False
        for i, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i == 0 and arg_name == "self":
                has_self = True
                arg_strs.append("self: *" + cls_name)
                continue
            args.append(arg_name)
            zig_ty = self._resolve_arg_zig_type(arg_name, arg, arg_types)
            arg_strs.append(arg_name + ": " + zig_ty)
        prev_class = self.current_class_name
        self.current_class_name = cls_name
        ret_type_any = stmt.get("return_type")
        ret_py = ret_type_any.strip() if isinstance(ret_type_any, str) else ""
        ret_type = self._zig_type(ret_py)
        if method_name == "__init__":
            self._emit_line("pub fn init(" + ", ".join(arg_strs[1:]) + ") " + cls_name + " {")
            self.indent += 1
            self._emit_line("var self: " + cls_name + " = undefined;")
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._emit_line("return self;")
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
        else:
            self._emit_line("pub fn " + method_name + "(" + ", ".join(arg_strs) + ") " + ret_type + " {")
            self.indent += 1
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
        self.current_class_name = prev_class

    def _emit_tuple_assign(self, target_any: Any, value_any: Any) -> None:
        if not isinstance(target_any, dict):
            return
        elts_any = target_any.get("elts")
        elts = elts_any if isinstance(elts_any, list) else []
        value_expr = self._render_expr(value_any)
        tmp = "__tmp_" + str(self.tmp_seq)
        self.tmp_seq += 1
        self._emit_line("const " + tmp + " = " + value_expr + ";")
        i = 0
        while i < len(elts):
            elt = elts[i]
            if isinstance(elt, dict):
                name = self._render_target(elt)
                if len(self._local_var_stack) > 0 and isinstance(elt, dict) and elt.get("kind") == "Name":
                    elt_name = _safe_ident(elt.get("id"), "value")
                    if elt_name not in self._current_local_vars():
                        self._current_local_vars().add(elt_name)
                        self._emit_line("var " + name + " = " + tmp + "[" + str(i) + "];")
                        i += 1
                        continue
                self._emit_line(name + " = " + tmp + "[" + str(i) + "];")
            i += 1

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_target(stmt.get("left"))
        right = self._render_target(stmt.get("right"))
        tmp = "__swap_tmp_" + str(self.tmp_seq)
        self.tmp_seq += 1
        self._emit_line("const " + tmp + " = " + left + ";")
        self._emit_line(left + " = " + right + ";")
        self._emit_line(right + " = " + tmp + ";")

    def _render_target(self, node: Any) -> str:
        if not isinstance(node, dict):
            return "_"
        nd: dict[str, Any] = node
        kind = nd.get("kind")
        if kind == "Name":
            return _safe_ident(nd.get("id"), "value")
        if kind == "Attribute":
            obj = self._render_expr(nd.get("value"))
            attr = _safe_ident(nd.get("attr"), "attr")
            return obj + "." + attr
        if kind == "Subscript":
            obj = self._render_expr(nd.get("value"))
            idx = self._render_expr(nd.get("slice"))
            return obj + "[" + idx + "]"
        return "_"

    def _render_cond_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "true"
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            v = ed.get("value")
            if v is True:
                return "true"
            if v is False:
                return "false"
        if kind == "Call":
            func_any = ed.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Name":
                fname = _safe_ident(func_any.get("id"), "")
                if fname == "__pytra_truthy":
                    args_any = ed.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) > 0:
                        return "pytra.truthy(" + self._render_expr(args[0]) + ")"
        return self._render_expr(expr_any)

    def _render_expr(self, expr_any: Any) -> str:
        if expr_any is None:
            return "null"
        if not isinstance(expr_any, dict):
            return str(expr_any)
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            return self._render_constant(ed)
        if kind == "Name":
            name = _safe_ident(ed.get("id"), "value")
            if name == "True":
                return "true"
            if name == "False":
                return "false"
            if name == "None":
                return "null"
            return name
        if kind == "BinOp":
            left = self._render_expr(ed.get("left"))
            right = self._render_expr(ed.get("right"))
            op = str(ed.get("op"))
            if op == "Add":
                left_type = self._lookup_expr_type(ed.get("left"))
                right_type = self._lookup_expr_type(ed.get("right"))
                if left_type == "str" or right_type == "str":
                    return "pytra.str_concat(" + left + ", " + right + ")"
            if op == "Pow":
                return "std.math.pow(f64, " + left + ", " + right + ")"
            if op == "FloorDiv":
                return "@divFloor(" + left + ", " + right + ")"
            sym = _binop_symbol(op)
            return "(" + left + " " + sym + " " + right + ")"
        if kind == "UnaryOp":
            op = str(ed.get("op"))
            operand = self._render_expr(ed.get("operand"))
            if op == "USub":
                return "-" + operand
            if op == "UAdd":
                return "+" + operand
            if op == "Not":
                return "!" + operand
            if op == "Invert":
                return "~" + operand
            return operand
        if kind == "Compare":
            return self._render_compare(ed)
        if kind == "BoolOp":
            op = str(ed.get("op"))
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            parts: list[str] = []
            for v in values:
                parts.append(self._render_expr(v))
            joiner = " and " if op == "And" else " or "
            return "(" + joiner.join(parts) + ")"
        if kind == "Call":
            return self._render_call(ed)
        if kind == "Attribute":
            obj = self._render_expr(ed.get("value"))
            attr = _safe_ident(ed.get("attr"), "attr")
            return obj + "." + attr
        if kind == "Subscript":
            obj = self._render_expr(ed.get("value"))
            idx = self._render_expr(ed.get("slice"))
            return obj + "[" + idx + "]"
        if kind == "List":
            elts_any = ed.get("elts")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            return ".{ " + ", ".join(items) + " }"
        if kind == "Tuple":
            elts_any = ed.get("elts")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            return ".{ " + ", ".join(items) + " }"
        if kind == "Dict":
            return self._render_dict(ed)
        if kind == "JoinedStr":
            return self._render_joined_str(ed)
        if kind == "IfExp":
            test = self._render_cond_expr(ed.get("test"))
            body_expr = self._render_expr(ed.get("body"))
            orelse_expr = self._render_expr(ed.get("orelse"))
            return "if (" + test + ") " + body_expr + " else " + orelse_expr
        if kind == "FormattedValue":
            return self._render_expr(ed.get("value"))
        if kind == "Lambda":
            arg_order_any = ed.get("arg_order")
            args = arg_order_any if isinstance(arg_order_any, list) else []
            arg_names = [_safe_ident(a, "arg") for a in args]
            body_expr = self._render_expr(ed.get("body"))
            return "struct { fn call(" + ", ".join(a + ": PyObject" for a in arg_names) + ") PyObject { return " + body_expr + "; } }.call"
        if kind == "ListComp" or kind == "SetComp" or kind == "DictComp" or kind == "GeneratorExp":
            return "pytra.empty_list()  /* comprehension */";
        if kind == "Starred":
            return self._render_expr(ed.get("value"))
        if kind == "Slice":
            lower = self._render_expr(ed.get("lower")) if isinstance(ed.get("lower"), dict) else "0"
            upper = self._render_expr(ed.get("upper")) if isinstance(ed.get("upper"), dict) else "null"
            return "pytra.slice(" + lower + ", " + upper + ")"
        return "null"

    def _render_constant(self, node: dict[str, Any]) -> str:
        v = node.get("value")
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(v)
        if isinstance(v, str):
            return _zig_string(v)
        return str(v)

    def _render_compare(self, node: dict[str, Any]) -> str:
        left = self._render_expr(node.get("left"))
        ops_any = node.get("ops")
        ops = ops_any if isinstance(ops_any, list) else []
        comparators_any = node.get("comparators")
        comparators = comparators_any if isinstance(comparators_any, list) else []
        if len(ops) == 0 or len(comparators) == 0:
            return left
        parts: list[str] = []
        prev = left
        i = 0
        while i < len(ops):
            right = self._render_expr(comparators[i])
            op_str = str(ops[i])
            if op_str == "In":
                parts.append("pytra.contains(" + right + ", " + prev + ")")
            elif op_str == "NotIn":
                parts.append("!pytra.contains(" + right + ", " + prev + ")")
            else:
                sym = _cmp_symbol(op_str)
                parts.append("(" + prev + " " + sym + " " + right + ")")
            prev = right
            i += 1
        if len(parts) == 1:
            return parts[0]
        return "(" + " and ".join(parts) + ")"

    def _render_call(self, node: dict[str, Any]) -> str:
        func_any = node.get("func")
        args_any = node.get("args")
        args = args_any if isinstance(args_any, list) else []
        arg_strs = [self._render_expr(a) for a in args]
        if isinstance(func_any, dict):
            fkind = func_any.get("kind")
            if fkind == "Name":
                fname = _safe_ident(func_any.get("id"), "fn_")
                if fname == "print":
                    if len(args) == 1 and isinstance(args[0], dict) and args[0].get("kind") == "Call":
                        inner_func = args[0].get("func")
                        if isinstance(inner_func, dict) and inner_func.get("kind") == "Name":
                            inner_fname = str(inner_func.get("id"))
                            if inner_fname == "py_assert_stdout":
                                inner_args = args[0].get("args")
                                inner_args = inner_args if isinstance(inner_args, list) else []
                                if len(inner_args) >= 2:
                                    return self._render_expr(inner_args[1]) + "()"
                    if len(arg_strs) == 0:
                        return "pytra.print(\"\")"
                    if len(arg_strs) == 1:
                        return "pytra.print(" + arg_strs[0] + ")"
                    if len(arg_strs) == 2:
                        return "pytra.print2(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                    if len(arg_strs) == 3:
                        return "pytra.print3(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ")"
                    return "pytra.print(" + arg_strs[0] + ")"
                if fname == "len":
                    if len(arg_strs) > 0:
                        return arg_strs[0] + ".len"
                    return "0"
                if fname == "int":
                    if len(arg_strs) > 0:
                        return "@as(i64, " + arg_strs[0] + ")"
                    return "0"
                if fname == "float":
                    if len(arg_strs) > 0:
                        return "@as(f64, " + arg_strs[0] + ")"
                    return "0.0"
                if fname == "str":
                    if len(arg_strs) > 0:
                        return "pytra.to_str(" + arg_strs[0] + ")"
                    return "\"\""
                if fname == "abs":
                    if len(arg_strs) > 0:
                        return "std.math.absInt(" + arg_strs[0] + ")"
                    return "0"
                if fname == "min":
                    if len(arg_strs) >= 2:
                        return "@min(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "max":
                    if len(arg_strs) >= 2:
                        return "@max(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "isinstance":
                    return "pytra.isinstance_check(" + ", ".join(arg_strs) + ")"
                if fname == "py_assert_stdout":
                    if len(args) >= 2:
                        fn_expr = self._render_expr(args[1])
                        return fn_expr + "()"
                    return "{}"
                if fname in self.class_names:
                    return cls_name_init(fname, arg_strs)
                return fname + "(" + ", ".join(arg_strs) + ")"
            if fkind == "Attribute":
                obj = self._render_expr(func_any.get("value"))
                attr = _safe_ident(func_any.get("attr"), "method")
                if attr == "append":
                    if len(arg_strs) > 0:
                        return obj + ".append(" + arg_strs[0] + ")"
                if attr == "sqrt":
                    if len(arg_strs) > 0:
                        return "std.math.sqrt(@as(f64, " + arg_strs[0] + "))"
                    return "std.math.sqrt(@as(f64, " + obj + "))"
                return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
        fn_expr = self._render_expr(func_any)
        return fn_expr + "(" + ", ".join(arg_strs) + ")"

    def _render_dict(self, node: dict[str, Any]) -> str:
        keys_any = node.get("keys")
        values_any = node.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        values = values_any if isinstance(values_any, list) else []
        if len(keys) == 0:
            return "pytra.new_dict()"
        parts: list[str] = []
        i = 0
        while i < len(keys):
            k = self._render_expr(keys[i])
            v = self._render_expr(values[i]) if i < len(values) else "null"
            parts.append(".{ " + k + ", " + v + " }")
            i += 1
        return ".{ " + ", ".join(parts) + " }"

    def _render_joined_str(self, node: dict[str, Any]) -> str:
        values_any = node.get("values")
        values = values_any if isinstance(values_any, list) else []
        parts: list[str] = []
        for v in values:
            if isinstance(v, dict):
                if v.get("kind") == "Constant" and isinstance(v.get("value"), str):
                    parts.append(_zig_string(str(v.get("value"))))
                else:
                    parts.append("pytra.to_str(" + self._render_expr(v) + ")")
            else:
                parts.append(_zig_string(str(v)))
        if len(parts) == 0:
            return "\"\""
        if len(parts) == 1:
            return parts[0]
        return "pytra.str_join(&.{ " + ", ".join(parts) + " })"

    def _normalize_type(self, t: str) -> str:
        """Python 型名を内部正規表現へ変換する。"""
        s = t.strip()
        if s == "":
            return ""
        if s == "int":
            return "int64"
        if s == "float":
            return "float64"
        if s == "byte":
            return "uint8"
        if s == "any":
            return "Any"
        if s.startswith("list[") and s.endswith("]"):
            inner = self._normalize_type(s[5:-1])
            return "list[" + inner + "]"
        if s.startswith("set[") and s.endswith("]"):
            inner = self._normalize_type(s[4:-1])
            return "set[" + inner + "]"
        if s.startswith("dict[") and s.endswith("]"):
            inner = s[5:-1]
            parts = self._split_generic(inner)
            if len(parts) == 2:
                return "dict[" + self._normalize_type(parts[0]) + ", " + self._normalize_type(parts[1]) + "]"
        if s.startswith("tuple[") and s.endswith("]"):
            inner = s[6:-1]
            parts = self._split_generic(inner)
            normed: list[str] = []
            for p in parts:
                normed.append(self._normalize_type(p))
            return "tuple[" + ", ".join(normed) + "]"
        if s.find("|") != -1:
            parts = [self._normalize_type(p.strip()) for p in s.split("|")]
            return "|".join(parts)
        return s

    def _split_generic(self, inner: str) -> list[str]:
        """ジェネリック型引数をカンマで分割する（ネスト考慮）。"""
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
        tail = "".join(current).strip()
        if tail != "":
            parts.append(tail)
        return parts

    def _zig_type(self, py_type: str) -> str:
        """正規化済み Python 型名を Zig 型名へ変換する。"""
        t = self._normalize_type(py_type)
        if t == "":
            return "PyObject"
        if t in {"Any", "object", "unknown"}:
            return "PyObject"
        # --- スカラー型 ---
        if t == "bool":
            return "bool"
        if t == "int8":
            return "i8"
        if t == "uint8":
            return "u8"
        if t == "int16":
            return "i16"
        if t == "uint16":
            return "u16"
        if t == "int32":
            return "i32"
        if t == "uint32":
            return "u32"
        if t == "int64":
            return "i64"
        if t == "uint64":
            return "u64"
        if t == "float32":
            return "f32"
        if t == "float64":
            return "f64"
        if t == "str":
            return "[]const u8"
        if t == "bytes":
            return "[]const u8"
        if t == "bytearray":
            return "[]u8"
        if t == "None":
            return "void"
        # --- Union / Optional ---
        if t.find("|") != -1:
            parts = [p.strip() for p in t.split("|")]
            non_none = [p for p in parts if p != "None"]
            has_none = len(non_none) < len(parts)
            if has_none and len(non_none) == 1:
                return "?" + self._zig_type(non_none[0])
            if len(non_none) == 1:
                return self._zig_type(non_none[0])
            return "PyObject"
        # --- コンテナ型 ---
        if t.startswith("list[") and t.endswith("]"):
            elem = t[5:-1].strip()
            if elem == "uint8":
                return "[]u8"
            return "std.ArrayList(" + self._zig_type(elem) + ")"
        if t.startswith("set[") and t.endswith("]"):
            elem = t[4:-1].strip()
            return "std.AutoHashMap(" + self._zig_type(elem) + ", void)"
        if t.startswith("dict[") and t.endswith("]"):
            parts = self._split_generic(t[5:-1])
            if len(parts) == 2:
                key_t = self._zig_type(parts[0].strip())
                val_t = self._zig_type(parts[1].strip())
                return "std.AutoHashMap(" + key_t + ", " + val_t + ")"
            return "std.AutoHashMap([]const u8, PyObject)"
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self._split_generic(t[6:-1])
            if len(parts) == 2 and parts[1].strip() == "...":
                return "std.ArrayList(" + self._zig_type(parts[0].strip()) + ")"
            inner_types = [self._zig_type(p.strip()) for p in parts]
            return "struct { " + ", ".join("_" + str(i) + ": " + zt for i, zt in enumerate(inner_types)) + " }"
        # --- クラス名 ---
        if t in self.class_names:
            return t
        return "PyObject"

    def _get_expr_type(self, expr_any: Any) -> str:
        """EAST3 式ノードの resolved_type を正規化して返す。"""
        if not isinstance(expr_any, dict):
            return ""
        resolved = expr_any.get("resolved_type")
        if isinstance(resolved, str) and resolved.strip() != "":
            return self._normalize_type(resolved.strip())
        return ""

    def _infer_decl_type(self, stmt: dict[str, Any]) -> str:
        """変数宣言ノードから型を推論する（decl_type → annotation → value の resolved_type）。"""
        decl_type_any = stmt.get("decl_type")
        if isinstance(decl_type_any, str) and decl_type_any.strip() != "":
            return self._normalize_type(decl_type_any.strip())
        anno_any = stmt.get("annotation")
        if isinstance(anno_any, str) and anno_any.strip() != "":
            return self._normalize_type(anno_any.strip())
        value_any = stmt.get("value")
        if isinstance(value_any, dict):
            return self._get_expr_type(value_any)
        return ""

    def _lookup_expr_type(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed: dict[str, Any] = expr_any
        resolved = self._get_expr_type(ed)
        if resolved != "":
            return resolved
        kind = ed.get("kind")
        if kind == "Name":
            name = _safe_ident(ed.get("id"), "value")
            return self._current_type_map().get(name, "")
        if kind == "Constant":
            v = ed.get("value")
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int64"
            if isinstance(v, float):
                return "float64"
            if isinstance(v, str):
                return "str"
        return ""

    def _aug_assign_op(self, op: str) -> str:
        if op == "Add":
            return "+="
        if op == "Sub":
            return "-="
        if op == "Mult":
            return "*="
        if op == "Div":
            return "/="
        if op == "Mod":
            return "%="
        if op == "BitOr":
            return "|="
        if op == "BitXor":
            return "^="
        if op == "BitAnd":
            return "&="
        if op == "LShift":
            return "<<="
        if op == "RShift":
            return ">>="
        return "+="


def cls_name_init(cls_name: str, arg_strs: list[str]) -> str:
    return cls_name + ".init(" + ", ".join(arg_strs) + ")"


def transpile_to_zig_native(east_doc: dict[str, Any]) -> str:
    """EAST3 ドキュメントを Zig native ソースへ変換する。"""
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Zig backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Zig backend")
    return ZigNativeEmitter(east_doc).transpile()

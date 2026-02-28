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

    def transpile(self) -> str:
        self.lines.append("-- Auto-generated Pytra Lua native source from EAST3.")
        self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        for stmt in body:
            self._emit_stmt(stmt)
        if len(main_guard) > 0:
            self.lines.append("")
            self.lines.append("-- __main__ guard")
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

    def _emit_line(self, text: str) -> None:
        self.lines.append(("    " * self.indent) + text)

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        if len(body) == 0:
            self._emit_line("-- pass")
            return
        for stmt in body:
            self._emit_stmt(stmt)

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        kind = stmt.get("kind")
        if kind in {"Import", "ImportFrom"}:
            return
        if kind == "FunctionDef":
            self._emit_function_def(stmt)
            return
        if kind == "Return":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("return " + val)
            return
        if kind == "AnnAssign":
            target = self._name_from_target(stmt.get("target"))
            value = self._render_expr(stmt.get("value")) if isinstance(stmt.get("value"), dict) else "nil"
            self._emit_line("local " + target + " = " + value)
            return
        if kind == "Assign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                target = self._name_from_target(target_any)
                value = self._render_expr(stmt.get("value"))
                self._emit_line(target + " = " + value)
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                target = self._name_from_target(targets[0])
                value = self._render_expr(stmt.get("value"))
                self._emit_line(target + " = " + value)
                return
            raise RuntimeError("lang=lua unsupported assign shape")
        if kind == "AugAssign":
            target = self._name_from_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            self._emit_line(target + " = " + target + " " + _binop_symbol(op) + " " + value)
            return
        if kind == "Expr":
            self._emit_line(self._render_expr(stmt.get("value")))
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

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")
        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict) or iter_plan.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=lua unsupported forcore static_fastpath shape")
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            step = self._render_expr(iter_plan.get("step"))
            # Python range(stop) semantics: Lua for upper bound is inclusive.
            upper = "(" + stop + ") - 1"
            self._emit_line("for " + target_name + " = " + start + ", " + upper + ", " + step + " do")
            self.indent += 1
            self._emit_block(stmt.get("body"))
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
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("end")
            return
        raise RuntimeError("lang=lua unsupported forcore iter_mode: " + iter_mode)

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
        self._emit_line("while " + test + " do")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("end")

    def _name_from_target(self, target_any: Any) -> str:
        if isinstance(target_any, dict) and target_any.get("kind") == "Name":
            return _safe_ident(target_any.get("id"), "value")
        raise RuntimeError("lang=lua unsupported assignment target")

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
        if kind == "Set":
            elems_any = expr_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "{ " + ", ".join(out) + " }"
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
            index = self._render_expr(expr_any.get("slice"))
            owner_node = expr_any.get("value")
            owner_type = ""
            if isinstance(owner_node, dict) and isinstance(owner_node.get("resolved_type"), str):
                owner_type = owner_node.get("resolved_type") or ""
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            return owner + "[(" + index + ") + 1]"
        if kind == "Attribute":
            owner = self._render_expr(expr_any.get("value"))
            attr = _safe_ident(expr_any.get("attr"), "field")
            return owner + "." + attr
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
            if fn_name == "print":
                return "print(" + ", ".join(rendered_args) + ")"
            return fn_name + "(" + ", ".join(rendered_args) + ")"
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner = self._render_expr(func_any.get("value"))
            attr = _safe_ident(func_any.get("attr"), "call")
            return owner + "." + attr + "(" + ", ".join(rendered_args) + ")"
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

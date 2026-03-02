"""EAST3 -> Nim native emitter (minimal skeleton)."""

from __future__ import annotations

from pytra.std.typing import Any


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
    if out[0].isdigit():
        out = "v" + out
    if out in _NIM_KEYWORDS:
        out = "`" + out + "`"
    return out

def _nim_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\n", "\\n")
    return '"' + out + '"'

class NimNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0

    def transpile(self) -> str:
        self.lines.append('import std/os')
        # self.lines.append('include "py_runtime.nim"')
        self.lines.append("")

        body = self.east_doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if isinstance(stmt, dict):
                    self._emit_stmt(stmt)

        main_guard = self.east_doc.get("main_guard_body")
        if isinstance(main_guard, list) and len(main_guard) > 0:
            self.lines.append("")
            self.lines.append("if isMainModule:")
            self.indent += 1
            for stmt in main_guard:
                if isinstance(stmt, dict):
                    self._emit_stmt(stmt)
            self.indent -= 1

        return "\n".join(self.lines).rstrip() + "\n"

    def _emit_line(self, text: str) -> None:
        self.lines.append("  " * self.indent + text)

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        kind = stmt.get("kind")
        if kind == "FunctionDef":
            self._emit_function_def(stmt)
        elif kind == "Expr":
            self._emit_expr_stmt(stmt)
        elif kind == "Assign":
            self._emit_assign(stmt)
        elif kind == "Return":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("return " + val)
        elif kind == "If":
            self._emit_if(stmt)
        elif kind == "ForCore":
            self._emit_for(stmt)
        elif kind == "Pass":
            self._emit_line("discard")
        else:
            self._emit_line("# unsupported stmt: " + str(kind))

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn")
        arg_order = stmt.get("arg_order", [])
        args = []
        for a in arg_order:
            args.append(_safe_ident(a) + ": any")
        
        self._emit_line(f"proc {name}({', '.join(args)}) =")
        self.indent += 1
        body = stmt.get("body", [])
        if not body:
            self._emit_line("discard")
        else:
            for s in body:
                if isinstance(s, dict):
                    self._emit_stmt(s)
        self.indent -= 1
        self.lines.append("")

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        expr = self._render_expr(stmt.get("value"))
        if expr.startswith("echo "):
            self._emit_line(expr)
        else:
            self._emit_line("discard " + expr)

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target_node = stmt.get("target")
        if not isinstance(target_node, dict):
             targets = stmt.get("targets", [])
             if targets:
                 target_node = targets[0]
        
        target = self._render_expr(target_node)
        value = self._render_expr(stmt.get("value"))
        
        if self.indent == 0:
            self._emit_line(f"var {target} = {value}")
        else:
             self._emit_line(f"{target} = {value}")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
        self._emit_line(f"if {test}:")
        self.indent += 1
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self.indent -= 1
        orelse = stmt.get("orelse", [])
        if orelse:
            if len(orelse) == 1 and orelse[0].get("kind") == "If":
                self._emit_elif(orelse[0])
            else:
                self._emit_line("else:")
                self.indent += 1
                for s in orelse:
                    if isinstance(s, dict):
                        self._emit_stmt(s)
                self.indent -= 1

    def _emit_elif(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
        self._emit_line(f"elif {test}:")
        self.indent += 1
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self.indent -= 1
        orelse = stmt.get("orelse", [])
        if orelse:
            if len(orelse) == 1 and orelse[0].get("kind") == "If":
                self._emit_elif(orelse[0])
            else:
                self._emit_line("else:")
                self.indent += 1
                for s in orelse:
                    if isinstance(s, dict):
                        self._emit_stmt(s)
                self.indent -= 1

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"))
        
        iter_plan = stmt.get("iter_plan")
        if isinstance(iter_plan, dict) and iter_plan.get("kind") == "StaticRangeForPlan":
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            self._emit_line(f"for {target_name} in {start} ..< {stop}:")
        else:
             self._emit_line(f"for {target_name} in []:") # placeholder
        
        self.indent += 1
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self.indent -= 1

    def _render_expr(self, expr: Any) -> str:
        if not isinstance(expr, dict):
            return "nil"
        kind = expr.get("kind")
        if kind == "Constant":
            val = expr.get("value")
            if isinstance(val, str):
                return _nim_string(val)
            if isinstance(val, bool):
                return "true" if val else "false"
            if val is None:
                return "nil"
            return str(val)
        elif kind == "Name":
            return _safe_ident(expr.get("id"))
        elif kind == "BinOp":
            left = self._render_expr(expr.get("left"))
            right = self._render_expr(expr.get("right"))
            op = expr.get("op")
            symbol = "+"
            if op == "Add":
                # Nim uses '&' for string concatenation
                resolved = expr.get("resolved_type")
                if isinstance(resolved, str) and resolved == "str":
                    symbol = "&"
                else:
                    symbol = "+"
            elif op == "Sub": symbol = "-"
            elif op == "Mult": symbol = "*"
            elif op == "Div": symbol = "/"
            elif op == "FloorDiv": symbol = "div"
            elif op == "Mod": symbol = "mod"
            return f"({left} {symbol} {right})"
        elif kind == "Compare":
            left = self._render_expr(expr.get("left"))
            ops = expr.get("ops", [])
            comps = expr.get("comparators", [])
            if not ops: return left
            op = ops[0]
            right = self._render_expr(comps[0])
            symbol = "=="
            if op == "Eq": symbol = "=="
            elif op == "NotEq": symbol = "!="
            elif op == "Lt": symbol = "<"
            elif op == "LtE": symbol = "<="
            elif op == "Gt": symbol = ">"
            elif op == "GtE": symbol = ">="
            return f"({left} {symbol} {right})"
        elif kind == "Call":
            return self._render_call(expr)
        return f"/* unknown expr {kind} */"

    def _render_call(self, expr: dict[str, Any]) -> str:
        func = expr.get("func")
        args = [self._render_expr(a) for a in expr.get("args", [])]
        if isinstance(func, dict) and func.get("kind") == "Name":
            name = func.get("id")
            if name == "print":
                return f"echo {', '.join(args)}"
        
        func_expr = self._render_expr(func)
        return f"{func_expr}({', '.join(args)})"

def transpile_to_nim_native(east_doc: dict[str, Any]) -> str:
    emitter = NimNativeEmitter(east_doc)
    return emitter.transpile()

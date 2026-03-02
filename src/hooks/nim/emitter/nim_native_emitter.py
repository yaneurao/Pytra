"""EAST3 -> Nim native emitter."""

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

def _binop_symbol(op: str) -> str:
    if op == "Add": return "+"
    if op == "Sub": return "-"
    if op == "Mult": return "*"
    if op == "Div": return "/"
    if op == "FloorDiv": return "div"
    if op == "Mod": return "mod"
    return "+"

def _cmp_symbol(op: str) -> str:
    if op == "Eq": return "=="
    if op == "NotEq": return "!="
    if op == "Lt": return "<"
    if op == "LtE": return "<="
    if op == "Gt": return ">"
    if op == "GtE": return ">="
    return "=="

class NimNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.class_names: set[str] = set()
        self.current_class: str = ""
        self.self_replacement: str = ""

    def transpile(self) -> str:
        self.lines.append('import std/os, std/times, std/tables, std/strutils')
        self.lines.append("")

        body = self.east_doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if isinstance(stmt, dict) and stmt.get("kind") == "ClassDef":
                    self.class_names.add(_safe_ident(stmt.get("name")))

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

    def _map_type(self, py_type: Any) -> str:
        if not isinstance(py_type, str):
            return "auto"
        t = py_type.strip()
        if t in {"int", "int64"}: return "int"
        if t in {"float", "float64"}: return "float"
        if t == "str": return "string"
        if t == "bool": return "bool"
        if t == "None": return "void"
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
        if t in self.class_names:
            return t
        return "auto"

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
        elif kind == "Pass":
            self._emit_line("discard")
        elif kind in {"Import", "ImportFrom"}:
            pass
        else:
            self._emit_line("# unsupported stmt: " + str(kind))

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        raw_name = stmt.get("name")
        name = _safe_ident(raw_name, "fn")
        arg_order = stmt.get("arg_order", [])
        arg_types = stmt.get("arg_types", {})
        ret_type = self._map_type(stmt.get("returns"))
        
        args = []
        for a in arg_order:
            safe_a = _safe_ident(a)
            if self.current_class and safe_a == "self":
                args.append(f"{safe_a}: {self.current_class}")
            else:
                t = self._map_type(arg_types.get(a))
                args.append(f"{safe_a}: {t}")
        
        old_self_replacement = self.self_replacement
        if raw_name == "__init__":
             name = "new" + self.current_class
             args = args[1:]
             ret_type = self.current_class
             self.self_replacement = "result"

        header = f"proc {name}({', '.join(args)})"
        if ret_type != "void" and ret_type != "auto":
            header += f": {ret_type}"
        self._emit_line(header + " =")
        
        self.indent += 1
        if raw_name == "__init__":
             self._emit_line(f"new(result)")
        
        body = stmt.get("body", [])
        if not body:
            self._emit_line("discard")
        else:
            for s in body:
                if isinstance(s, dict):
                    self._emit_stmt(s)
        self.indent -= 1
        self.self_replacement = old_self_replacement
        self.lines.append("")

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "Class")
        self.current_class = name
        
        self._emit_line(f"type {name}* = ref object")
        self.indent += 1
        body = stmt.get("body", [])
        has_fields = False
        for s in body:
            if isinstance(s, dict) and s.get("kind") == "AnnAssign":
                target = s.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    field_name = _safe_ident(target.get("id"))
                    field_type = self._map_type(s.get("annotation"))
                    if not has_fields:
                        has_fields = True
                    self._emit_line(f"{field_name}*: {field_type}")
        if not has_fields:
             self._emit_line("discard")
        self.indent -= 1
        self.lines.append("")
        
        for s in body:
            if isinstance(s, dict) and s.get("kind") == "FunctionDef":
                self._emit_function_def(s)
        
        self.current_class = ""

    def _emit_expr_stmt(self, stmt: dict[str, Any]) -> None:
        expr = self._render_expr(stmt.get("value"))
        if expr.startswith("echo ") or expr.startswith("discard "):
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

    def _emit_ann_assign(self, stmt: dict[str, Any]) -> None:
        target = self._render_expr(stmt.get("target"))
        t = self._map_type(stmt.get("annotation"))
        value_node = stmt.get("value")
        if value_node:
            value = self._render_expr(value_node)
            if self.indent == 0:
                self._emit_line(f"var {target}: {t} = {value}")
            else:
                self._emit_line(f"{target} = {value} # {t}")
        else:
            if self.indent == 0:
                self._emit_line(f"var {target}: {t}")
            else:
                self._emit_line(f"var {target}: {t} # local decl")

    def _emit_aug_assign(self, stmt: dict[str, Any]) -> None:
        target = self._render_expr(stmt.get("target"))
        op = _binop_symbol(stmt.get("op", "Add"))
        value = self._render_expr(stmt.get("value"))
        self._emit_line(f"{target} {op}= {value}")

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

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_expr(stmt.get("test"))
        self._emit_line(f"while {test}:")
        self.indent += 1
        for s in stmt.get("body", []):
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
             expr = self._render_expr(iter_plan.get("iter_expr") if isinstance(iter_plan, dict) else None)
             self._emit_line(f"for {target_name} in {expr}:")
        
        self.indent += 1
        for s in stmt.get("body", []):
            if isinstance(s, dict):
                self._emit_stmt(s)
        self.indent -= 1

    def _emit_raise(self, stmt: dict[str, Any]) -> None:
        exc = self._render_expr(stmt.get("exc"))
        self._emit_line(f"raise newException(Exception, {exc})")

    def _render_expr(self, expr: Any) -> str:
        if not isinstance(expr, dict):
            return "nil"
        kind = expr.get("kind")
        if kind == "Constant":
            val = expr.get("value")
            if isinstance(val, str): return _nim_string(val)
            if isinstance(val, bool): return "true" if val else "false"
            if val is None: return "nil"
            return str(val)
        elif kind == "Name":
            name = expr.get("id")
            if name == "self" and self.self_replacement:
                 return self.self_replacement
            return _safe_ident(name)
        elif kind == "UnaryOp":
            op = expr.get("op")
            operand = self._render_expr(expr.get("operand"))
            if op == "Not": return f"(not {operand})"
            if op == "USub": return f"(-{operand})"
            return operand
        elif kind == "BinOp":
            left = self._render_expr(expr.get("left"))
            right = self._render_expr(expr.get("right"))
            op_raw = expr.get("op")
            symbol = _binop_symbol(op_raw)
            if op_raw == "Add":
                resolved = expr.get("resolved_type")
                if isinstance(resolved, str) and resolved == "str":
                    symbol = "&"
            return f"({left} {symbol} {right})"
        elif kind == "BoolOp":
            op = "and" if expr.get("op") == "And" else "or"
            values = [self._render_expr(v) for v in expr.get("values", [])]
            return f"({' {op} '.join(values)})"
        elif kind == "Compare":
            left = self._render_expr(expr.get("left"))
            ops = expr.get("ops", [])
            comps = expr.get("comparators", [])
            if not ops: return left
            op = ops[0]
            right = self._render_expr(comps[0])
            symbol = _cmp_symbol(op)
            return f"({left} {symbol} {right})"
        elif kind == "Call":
            return self._render_call(expr)
        elif kind == "List":
            elts = [self._render_expr(e) for e in expr.get("elements", [])]
            return f"@[{', '.join(elts)}]"
        elif kind == "Dict":
            entries = expr.get("entries", [])
            pairs = []
            for entry in entries:
                k = self._render_expr(entry.get("key"))
                v = self._render_expr(entry.get("value"))
                pairs.append(f"{k}: {v}")
            if not pairs:
                 # Fallback to old format just in case
                 keys = expr.get("keys", [])
                 values = expr.get("values", [])
                 for k_node, v_node in zip(keys, values):
                      if k_node is None: continue
                      pairs.append(f"{self._render_expr(k_node)}: {self._render_expr(v_node)}")
            return f"{{ {', '.join(pairs)} }}.toTable"
        elif kind == "Subscript":
            value = self._render_expr(expr.get("value"))
            slice_node = expr.get("slice")
            if isinstance(slice_node, dict) and slice_node.get("kind") == "Slice":
                lower = self._render_expr(slice_node.get("lower"))
                upper = self._render_expr(slice_node.get("upper"))
                return f"{value}[{lower} .. {upper}]"
            idx = self._render_expr(slice_node)
            return f"{value}[{idx}]"
        elif kind == "Attribute":
            value = self._render_expr(expr.get("value"))
            attr = _safe_ident(expr.get("attr"))
            return f"{value}.{attr}"
        return f"/* unknown expr {kind} */"

    def _render_call(self, expr: dict[str, Any]) -> str:
        func = expr.get("func")
        args = [self._render_expr(a) for a in expr.get("args", [])]
        if isinstance(func, dict) and func.get("kind") == "Name":
            name = func.get("id")
            if name == "print":
                return f"echo {', '.join(args)}"
            if name == "len":
                return f"{args[0]}.len"
            if name == "int":
                return f"int({args[0]})"
            if name == "float":
                return f"float({args[0]})"
            if name == "str":
                return f"$( {args[0]} )"
            if name in self.class_names:
                 return f"new{name}({', '.join(args)})"
        
        func_expr = self._render_expr(func)
        return f"{func_expr}({', '.join(args)})"

def transpile_to_nim_native(east_doc: dict[str, Any]) -> str:
    emitter = NimNativeEmitter(east_doc)
    return emitter.transpile()

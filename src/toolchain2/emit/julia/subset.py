"""Small toolchain2-native Julia subset renderer.

This module intentionally supports only a narrow AST subset so the Julia
backend can start migrating off the legacy emitter incrementally.
Unsupported modules must fall back to the legacy bridge.
"""

from __future__ import annotations

from pytra.std.json import JsonVal


_BINOP_TEXT = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "div",
    "Mod": "%",
}

_CMP_TEXT = {
    "Eq": "==",
    "NotEq": "!=",
    "In": "in",
    "NotIn": "notin",
    "Is": "===",
    "IsNot": "!==",
    "Lt": "<",
    "LtE": "<=",
    "Gt": ">",
    "GtE": ">=",
}

_UNARY_TEXT = {
    "USub": "-",
    "UAdd": "+",
    "Not": "!",
}

_EXCEPTION_CTOR_TEXT = {
    "Exception": "__pytra_exception",
    "ValueError": "__pytra_value_error",
    "RuntimeError": "__pytra_runtime_error",
    "TypeError": "__pytra_type_error",
}

_EXCEPTION_TYPE_TEXT = {
    "Exception": "PytraException",
    "ValueError": "PytraValueError",
    "RuntimeError": "PytraRuntimeError",
    "TypeError": "PytraTypeError",
}

_IMPORTFROM_MODULES: dict[str, set[str] | None] = {
    "pytra.utils.assertions": {"py_assert_stdout", "py_assert_eq", "py_assert_all", "py_assert_true"},
    "pytra.utils.png": None,
    "pytra.std.collections": {"deque"},
    "pytra.std.math": {"fabs", "floor", "sqrt"},
    "math": {"floor", "sqrt"},
    "time": {"perf_counter"},
}

_JULIA_RESERVED_NAMES = {
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
    "let",
    "local",
    "macro",
    "module",
    "quote",
    "return",
    "struct",
    "true",
    "try",
    "using",
    "while",
}


def _str(node: dict[str, JsonVal], key: str) -> str:
    value = node.get(key)
    if isinstance(value, str):
        return value
    return ""


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    value = node.get(key)
    if isinstance(value, list):
        return value
    return []


def _quote_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _simple_class_supported(node: dict[str, JsonVal]) -> bool:
    if _str(node, "base") != "":
        return False
    body = _list(node, "body")
    if len(body) == 0:
        return True
    if len(body) == 1 and isinstance(body[0], dict) and _str(body[0], "kind") == "Pass":
        return True
    if len(body) != 1 or not isinstance(body[0], dict) or _str(body[0], "kind") != "FunctionDef":
        return False
    init_fn = body[0]
    if _str(init_fn, "name") != "__init__":
        return False
    if [arg for arg in _list(init_fn, "arg_order") if isinstance(arg, str)] != ["self"]:
        return False
    for stmt in _list(init_fn, "body"):
        if not isinstance(stmt, dict):
            return False
        if _str(stmt, "kind") not in {"AnnAssign", "Assign"}:
            return False
        target = stmt.get("target")
        if not isinstance(target, dict) or _str(target, "kind") != "Attribute":
            return False
        owner = target.get("value")
        if not isinstance(owner, dict) or _str(owner, "kind") != "Name" or _str(owner, "id") != "self":
            return False
        if not _expr_supported(stmt.get("value")):
            return False
    return True


def _exception_class_supported(node: dict[str, JsonVal]) -> bool:
    base = _str(node, "base")
    if base not in {"Exception", "ValueError", "TypeError", "RuntimeError"}:
        return False
    body = _list(node, "body")
    init_fn: dict[str, JsonVal] | None = None
    for stmt in body:
        if not isinstance(stmt, dict):
            return False
        kind = _str(stmt, "kind")
        if kind == "AnnAssign":
            target = stmt.get("target")
            if not isinstance(target, dict) or _str(target, "kind") != "Name":
                return False
            continue
        if kind == "FunctionDef" and _str(stmt, "name") == "__init__":
            if init_fn is not None:
                return False
            init_fn = stmt
            continue
        return False
    if init_fn is None:
        return False
    args = [arg for arg in _list(init_fn, "arg_order") if isinstance(arg, str)]
    if len(args) < 2 or args[0] != "self":
        return False
    for stmt in _list(init_fn, "body"):
        if not isinstance(stmt, dict):
            return False
        kind = _str(stmt, "kind")
        if kind == "Expr":
            value = stmt.get("value")
            if not isinstance(value, dict) or _str(value, "kind") != "Call":
                return False
            func = value.get("func")
            if not isinstance(func, dict) or _str(func, "kind") != "Attribute" or _str(func, "attr") != "__init__":
                return False
            owner = func.get("value")
            if not (
                isinstance(owner, dict)
                and _str(owner, "kind") == "Call"
                and isinstance(owner.get("func"), dict)
                and _str(owner.get("func"), "kind") == "Name"
                and _str(owner.get("func"), "id") == "super"
            ):
                return False
            if not all(_expr_supported(arg) for arg in _list(value, "args")):
                return False
            continue
        if kind not in {"Assign", "AnnAssign"}:
            return False
        target = stmt.get("target")
        if not isinstance(target, dict) or _str(target, "kind") != "Attribute":
            return False
        owner = target.get("value")
        if not isinstance(owner, dict) or _str(owner, "kind") != "Name" or _str(owner, "id") != "self":
            return False
        if not _expr_supported(stmt.get("value")):
            return False
    return True


def _except_handler_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "ExceptHandler":
        return False
    type_node = node.get("type")
    if type_node is not None and (not isinstance(type_node, dict) or _str(type_node, "kind") != "Name"):
        return False
    return all(_stmt_supported(stmt) for stmt in _list(node, "body"))


def _importfrom_supported(module_name: str, names: list[JsonVal]) -> bool:
    allowed = _IMPORTFROM_MODULES.get(module_name)
    if allowed is None:
        return module_name in _IMPORTFROM_MODULES and all(isinstance(item, dict) for item in names)
    return all(isinstance(item, dict) and _str(item, "name") in allowed for item in names)


def _ident(name: str) -> str:
    if name in _JULIA_RESERVED_NAMES:
        return name + "_py"
    return name


def _import_supported(names: list[JsonVal]) -> bool:
    allowed = {"math", "pytra.std.env", "pytra.std.os", "pytra.utils.png"}
    return all(isinstance(item, dict) and _str(item, "name") in allowed for item in names)


def _expr_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind in {"Name", "Constant"}:
        return True
    if kind == "FormattedValue":
        return _expr_supported(node.get("value"))
    if kind == "JoinedStr":
        return all(_expr_supported(item) for item in _list(node, "values"))
    if kind == "ObjStr":
        return _expr_supported(node.get("value"))
    if kind == "Attribute":
        return _expr_supported(node.get("value"))
    if kind == "List":
        return all(_expr_supported(item) for item in _list(node, "elements"))
    if kind == "Tuple":
        return all(_expr_supported(item) for item in _list(node, "elements"))
    if kind == "Dict":
        return all(
            isinstance(item, dict)
            and _expr_supported(item.get("key"))
            and _expr_supported(item.get("value"))
            for item in _list(node, "entries")
        )
    if kind == "Set":
        return all(_expr_supported(item) for item in _list(node, "elements"))
    if kind == "BinOp":
        return _str(node, "op") in _BINOP_TEXT and _expr_supported(node.get("left")) and _expr_supported(node.get("right"))
    if kind == "BoolOp":
        return _str(node, "op") in {"And", "Or"} and all(_expr_supported(item) for item in _list(node, "values"))
    if kind == "Compare":
        ops = _list(node, "ops")
        comparators = _list(node, "comparators")
        return len(ops) == 1 and len(comparators) == 1 and (
            (isinstance(ops[0], str) and ops[0] in _CMP_TEXT)
            or (isinstance(ops[0], dict) and _str(ops[0], "kind") in _CMP_TEXT)
        ) and _expr_supported(node.get("left")) and _expr_supported(comparators[0])
    if kind == "UnaryOp":
        return _str(node, "op") in _UNARY_TEXT and _expr_supported(node.get("operand"))
    if kind == "IfExp":
        return _expr_supported(node.get("test")) and _expr_supported(node.get("body")) and _expr_supported(node.get("orelse"))
    if kind == "Lambda":
        args = _list(node, "args")
        return all(isinstance(arg, dict) and isinstance(arg.get("arg"), str) for arg in args) and _expr_supported(node.get("body"))
    if kind == "Call":
        func = node.get("func")
        keywords = _list(node, "keywords")
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            owner = func.get("value")
            attr = _str(func, "attr")
            if not _expr_supported(owner):
                return False
            if not all(_expr_supported(arg) for arg in _list(node, "args")):
                return False
            if not all(
                isinstance(item, dict)
                and isinstance(item.get("arg"), str)
                and _expr_supported(item.get("value"))
                for item in keywords
            ):
                return False
            return attr in {
                "add",
                "append",
                "appendleft",
                "clear",
                "discard",
                "endswith",
                "extend",
                "fabs",
                "find",
                "floor",
                "get",
                "index",
                "isalnum",
                "items",
                "join",
                "keys",
                "lower",
                "lstrip",
                "makedirs",
                "popleft",
                "pop",
                "replace",
                "remove",
                "reverse",
                "rstrip",
                "setdefault",
                "split",
                "sort",
                "sqrt",
                "values",
                "write_rgb_png",
                "startswith",
                "strip",
            }
        return (
            _expr_supported(node.get("func"))
            and all(_expr_supported(arg) for arg in _list(node, "args"))
            and all(
                isinstance(item, dict)
                and isinstance(item.get("arg"), str)
                and _expr_supported(item.get("value"))
                for item in keywords
            )
        )
    if kind in {"Box", "Unbox"}:
        return _expr_supported(node.get("value"))
    if kind == "Subscript":
        if not _expr_supported(node.get("value")):
            return False
        slice_node = node.get("slice")
        if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
            lower = slice_node.get("lower")
            upper = slice_node.get("upper")
            return (lower is None or _expr_supported(lower)) and (upper is None or _expr_supported(upper))
        return _expr_supported(slice_node)
    return False


def _stmt_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind == "Import":
        return _import_supported(_list(node, "names"))
    if kind == "ImportFrom":
        module_name = _str(node, "module")
        names = _list(node, "names")
        return _importfrom_supported(module_name, names)
    if kind in {"Return", "Expr"}:
        value = node.get("value")
        return value is None or _expr_supported(value)
    if kind == "Pass":
        return True
    if kind == "VarDecl":
        return isinstance(node.get("name"), str) and node.get("name") != ""
    if kind == "Raise":
        exc = node.get("exc")
        cause = node.get("cause")
        return (exc is None or _expr_supported(exc)) and (cause is None or _expr_supported(cause))
    if kind == "AnnAssign":
        target = node.get("target")
        return isinstance(target, dict) and _str(target, "kind") == "Name" and _expr_supported(node.get("value"))
    if kind == "Assign":
        target = node.get("target")
        if not isinstance(target, dict):
            return False
        target_kind = _str(target, "kind")
        if target_kind == "Name":
            return _expr_supported(node.get("value"))
        if target_kind == "Subscript":
            return _expr_supported(target.get("value")) and _expr_supported(target.get("slice")) and _expr_supported(node.get("value"))
        return False
    if kind == "Swap":
        left = node.get("left")
        right = node.get("right")
        return (
            isinstance(left, dict)
            and _str(left, "kind") == "Name"
            and isinstance(right, dict)
            and _str(right, "kind") == "Name"
        )
    if kind == "AugAssign":
        target = node.get("target")
        return (
            isinstance(target, dict)
            and _str(target, "kind") == "Name"
            and _str(node, "op") in _BINOP_TEXT
            and _expr_supported(node.get("value"))
        )
    if kind == "If":
        return _expr_supported(node.get("test")) and all(_stmt_supported(stmt) for stmt in _list(node, "body")) and all(
            _stmt_supported(stmt) for stmt in _list(node, "orelse")
        )
    if kind == "While":
        return _expr_supported(node.get("test")) and all(_stmt_supported(stmt) for stmt in _list(node, "body")) and all(
            _stmt_supported(stmt) for stmt in _list(node, "orelse")
        )
    if kind == "Try":
        return (
            all(_stmt_supported(stmt) for stmt in _list(node, "body"))
            and all(_except_handler_supported(handler) for handler in _list(node, "handlers"))
            and len(_list(node, "orelse")) == 0
            and all(_stmt_supported(stmt) for stmt in _list(node, "finalbody"))
        )
    if kind == "ForCore":
        target_plan = node.get("target_plan")
        iter_plan = node.get("iter_plan")
        if not isinstance(target_plan, dict) or _str(target_plan, "kind") != "NameTarget":
            return False
        if not isinstance(iter_plan, dict):
            return False
        iter_kind = _str(iter_plan, "kind")
        if iter_kind == "StaticRangeForPlan":
            return (
                _expr_supported(iter_plan.get("start"))
                and _expr_supported(iter_plan.get("stop"))
                and _expr_supported(iter_plan.get("step"))
                and all(_stmt_supported(stmt) for stmt in _list(node, "body"))
                and all(_stmt_supported(stmt) for stmt in _list(node, "orelse"))
            )
        if iter_kind == "RuntimeIterForPlan":
            return (
                _expr_supported(iter_plan.get("iter_expr"))
                and all(_stmt_supported(stmt) for stmt in _list(node, "body"))
                and all(_stmt_supported(stmt) for stmt in _list(node, "orelse"))
            )
        return False
    if kind == "FunctionDef":
        return all(_stmt_supported(stmt) for stmt in _list(node, "body"))
    if kind == "ClassDef":
        return _simple_class_supported(node) or _exception_class_supported(node)
    return False


def can_render_module_natively(east3_doc: dict[str, JsonVal]) -> bool:
    body = _list(east3_doc, "body")
    main_guard_body = _list(east3_doc, "main_guard_body")
    return all(_stmt_supported(stmt) for stmt in body) and all(_stmt_supported(stmt) for stmt in main_guard_body)


class JuliaSubsetRenderer:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.indent_level = 0
        self.tmp_counter = 0
        self.function_names: set[str] = set()
        self.class_names: set[str] = set()
        self.exception_class_names: set[str] = set()

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _emit(self, line: str) -> None:
        self.lines.append(self._indent() + line)

    def _emit_blank(self) -> None:
        self.lines.append("")

    def _next_tmp(self, prefix: str) -> str:
        self.tmp_counter += 1
        return prefix + str(self.tmp_counter)

    def _render_expr(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            raise RuntimeError("julia subset: expr must be dict")
        kind = _str(node, "kind")
        if kind == "Name":
            name = _str(node, "id")
            if name == "main" and "__pytra_main" in self.function_names:
                return "__pytra_main"
            return _ident(name)
        if kind == "Attribute":
            return self._render_expr(node.get("value")) + "." + _str(node, "attr")
        if kind == "FormattedValue":
            return "string(" + self._render_expr(node.get("value")) + ")"
        if kind == "JoinedStr":
            values = _list(node, "values")
            if len(values) == 0:
                return '""'
            parts = [self._render_expr(item) for item in values]
            expr = parts[0]
            for part in parts[1:]:
                expr = "(" + expr + " * " + part + ")"
            return expr
        if kind == "ObjStr":
            return "string(" + self._render_expr(node.get("value")) + ")"
        if kind == "Constant":
            value = node.get("value")
            if value is None:
                return "nothing"
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, str):
                return _quote_string(value)
            return str(value)
        if kind == "List":
            elems = [self._render_expr(item) for item in _list(node, "elements")]
            return "[" + ", ".join(elems) + "]"
        if kind == "Tuple":
            elems = [self._render_expr(item) for item in _list(node, "elements")]
            if len(elems) == 1:
                return "(" + elems[0] + ",)"
            return "(" + ", ".join(elems) + ")"
        if kind == "Dict":
            parts: list[str] = []
            for item in _list(node, "entries"):
                if isinstance(item, dict):
                    parts.append(self._render_expr(item.get("key")) + " => " + self._render_expr(item.get("value")))
            return "Dict(" + ", ".join(parts) + ")"
        if kind == "Set":
            elems = [self._render_expr(item) for item in _list(node, "elements")]
            return "Set([" + ", ".join(elems) + "])"
        if kind == "BinOp":
            op = _str(node, "op")
            left = self._render_expr(node.get("left"))
            right = self._render_expr(node.get("right"))
            if op == "FloorDiv":
                return "div(" + left + ", " + right + ")"
            if op == "Add":
                left_node = node.get("left")
                right_node = node.get("right")
                lhs_resolved = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
                rhs_resolved = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
                if lhs_resolved == "str" or rhs_resolved == "str":
                    return "(" + left + " * " + right + ")"
            if op == "Mult":
                left_node = node.get("left")
                right_node = node.get("right")
                lhs_resolved = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
                rhs_resolved = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
                if lhs_resolved.startswith("list[") or rhs_resolved.startswith("list["):
                    return "repeat(" + left + ", " + right + ")"
            return "(" + left + " " + _BINOP_TEXT[op] + " " + right + ")"
        if kind == "BoolOp":
            values = _list(node, "values")
            if len(values) == 0:
                return "false"
            expr = self._render_expr(values[-1])
            op = _str(node, "op")
            for value in reversed(values[:-1]):
                tmp_name = self._next_tmp("__pytra_boolop_")
                current = self._render_expr(value)
                if op == "And":
                    expr = "(begin " + tmp_name + " = " + current + "; __pytra_truthy(" + tmp_name + ") ? " + expr + " : " + tmp_name + " end)"
                else:
                    expr = "(begin " + tmp_name + " = " + current + "; __pytra_truthy(" + tmp_name + ") ? " + tmp_name + " : " + expr + " end)"
            return expr
        if kind == "Compare":
            left = self._render_expr(node.get("left"))
            comparators = _list(node, "comparators")
            ops = _list(node, "ops")
            op_raw = ops[0]
            op = op_raw if isinstance(op_raw, str) else _str(op_raw, "kind")
            right = self._render_expr(comparators[0])
            if op == "In":
                comparator_type = _str(comparators[0], "resolved_type")
                if comparator_type.startswith("dict["):
                    return "haskey(" + right + ", " + left + ")"
                return "__pytra_contains(" + right + ", " + left + ")"
            if op == "NotIn":
                comparator_type = _str(comparators[0], "resolved_type")
                if comparator_type.startswith("dict["):
                    return "(!haskey(" + right + ", " + left + "))"
                return "(!__pytra_contains(" + right + ", " + left + "))"
            return "(" + left + " " + _CMP_TEXT[op] + " " + right + ")"
        if kind == "UnaryOp":
            op = _str(node, "op")
            operand = self._render_expr(node.get("operand"))
            if op == "Not":
                return "(!__pytra_truthy(" + operand + "))"
            return "(" + _UNARY_TEXT[op] + operand + ")"
        if kind == "IfExp":
            test = self._render_expr(node.get("test"))
            body = self._render_expr(node.get("body"))
            orelse = self._render_expr(node.get("orelse"))
            return "(__pytra_truthy(" + test + ") ? " + body + " : " + orelse + ")"
        if kind == "Lambda":
            args = []
            for arg in _list(node, "args"):
                if isinstance(arg, dict):
                    name = arg.get("arg")
                    if isinstance(name, str):
                        args.append(name)
            body = self._render_expr(node.get("body"))
            return "((" + ", ".join(args) + ") -> " + body + ")"
        if kind == "Call":
            func_node = node.get("func")
            if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
                owner = self._render_expr(func_node.get("value"))
                attr = _str(func_node, "attr")
                args = [self._render_expr(arg) for arg in _list(node, "args")]
                keywords = [item for item in _list(node, "keywords") if isinstance(item, dict)]
                if attr == "append" and len(args) == 1:
                    return "push!(" + owner + ", " + args[0] + ")"
                if attr == "add" and len(args) == 1:
                    return "push!(" + owner + ", " + args[0] + ")"
                if attr == "appendleft" and len(args) == 1:
                    return "pushfirst!(" + owner + ", " + args[0] + ")"
                if attr == "clear" and len(args) == 0:
                    return "empty!(" + owner + ")"
                if attr == "discard" and len(args) == 1:
                    return "delete!(" + owner + ", " + args[0] + ")"
                if attr == "extend" and len(args) == 1:
                    return "append!(" + owner + ", " + args[0] + ")"
                if attr == "find" and len(args) == 1:
                    return "__pytra_str_find(" + owner + ", " + args[0] + ")"
                if attr == "index" and len(args) == 1:
                    return "__pytra_str_find(" + owner + ", " + args[0] + ")"
                if attr == "isalnum" and len(args) == 0:
                    return "__pytra_str_isalnum(" + owner + ")"
                if attr == "items" and len(args) == 0:
                    return "collect(pairs(" + owner + "))"
                if attr == "lower" and len(args) == 0:
                    return "lowercase(" + owner + ")"
                if attr == "lstrip" and len(args) == 0:
                    return "lstrip(" + owner + ")"
                if attr == "makedirs" and len(args) == 1 and len(keywords) == 1 and keywords[0].get("arg") == "exist_ok":
                    return owner + ".makedirs(" + args[0] + ", " + self._render_expr(keywords[0].get("value")) + ")"
                if attr == "sort" and len(args) == 0:
                    return "sort!(" + owner + ")"
                if attr == "reverse" and len(args) == 0:
                    return "reverse!(" + owner + ")"
                if attr == "popleft" and len(args) == 0:
                    return "popfirst!(" + owner + ")"
                if attr == "get" and len(args) == 2:
                    return "get(" + owner + ", " + args[0] + ", " + args[1] + ")"
                if attr == "pop" and len(args) == 1:
                    return "pop!(" + owner + ", " + args[0] + ")"
                if attr == "pop" and len(args) == 0:
                    return "pop!(" + owner + ")"
                if attr == "setdefault" and len(args) == 2:
                    return "get!(" + owner + ", " + args[0] + ", " + args[1] + ")"
                if attr == "split" and len(args) == 1:
                    return "split(" + owner + ", " + args[0] + ")"
                if attr == "join" and len(args) == 1:
                    return "join(" + args[0] + ", " + owner + ")"
                if attr == "keys" and len(args) == 0:
                    return "collect(keys(" + owner + "))"
                if attr == "strip" and len(args) == 0:
                    return "strip(" + owner + ")"
                if attr == "rstrip" and len(args) == 0:
                    return "rstrip(" + owner + ")"
                if attr == "startswith" and len(args) == 1:
                    return "startswith(" + owner + ", " + args[0] + ")"
                if attr == "endswith" and len(args) == 1:
                    return "endswith(" + owner + ", " + args[0] + ")"
                if attr == "replace" and len(args) == 2:
                    return "replace(" + owner + ", " + args[0] + " => " + args[1] + ")"
                if attr == "remove" and len(args) == 1:
                    return "delete!(" + owner + ", " + args[0] + ")"
                if attr == "values" and len(args) == 0:
                    return "collect(values(" + owner + "))"
                if attr == "write_rgb_png" and len(args) == 4 and len(keywords) == 0:
                    return owner + ".write_rgb_png(" + ", ".join(args) + ")"
            func = self._render_expr(func_node)
            args = [self._render_expr(arg) for arg in _list(node, "args")]
            if func == "print":
                return "__pytra_print(" + ", ".join(args) + ")"
            if func == "int" and len(args) == 1:
                return "__pytra_int(" + args[0] + ")"
            if func == "len" and len(args) == 1:
                return "length(" + args[0] + ")"
            if func == "range":
                if len(args) == 1:
                    return "0:(" + args[0] + " - 1)"
                if len(args) == 2:
                    return args[0] + ":(" + args[1] + " - 1)"
                if len(args) == 3:
                    step = args[2]
                    if step == "1":
                        return args[0] + ":(" + args[1] + " - 1)"
                    if step.startswith("-"):
                        return args[0] + ":" + step + ":(" + args[1] + " + 1)"
                    return (
                        args[0]
                        + ":"
                        + step
                        + ":(("
                        + step
                        + ") > 0 ? ("
                        + args[1]
                        + " - 1) : ("
                        + args[1]
                        + " + 1))"
                    )
            if func == "str" and len(args) == 1:
                return "string(" + args[0] + ")"
            if func == "set" and len(args) == 0:
                return "Set()"
            if func == "bytearray" and len(args) == 1:
                return "__pytra_bytearray(" + args[0] + ")"
            if func == "reversed" and len(args) == 1:
                return "reverse(" + args[0] + ")"
            if func in _EXCEPTION_CTOR_TEXT:
                if len(args) == 0:
                    return _EXCEPTION_CTOR_TEXT[func] + "()"
                return _EXCEPTION_CTOR_TEXT[func] + "(" + ", ".join(args) + ")"
            if func in self.exception_class_names:
                return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
            if func in self.class_names:
                return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
            return func + "(" + ", ".join(args) + ")"
        if kind in {"Box", "Unbox"}:
            return self._render_expr(node.get("value"))
        if kind == "Subscript":
            owner_node = node.get("value")
            owner = self._render_expr(owner_node)
            owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            slice_node = node.get("slice")
            if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
                lower = slice_node.get("lower")
                upper = slice_node.get("upper")
                lower_text = self._render_expr(lower) if isinstance(lower, dict) else "0"
                upper_text = self._render_expr(upper) if isinstance(upper, dict) else "nothing"
                if owner_type == "str":
                    return "__pytra_str_slice(" + owner + ", " + lower_text + ", " + upper_text + ")"
                if upper_text == "nothing":
                    return owner + "[(" + lower_text + " + 1):end]"
                return owner + "[(" + lower_text + " + 1):" + upper_text + "]"
            index = self._render_expr(slice_node)
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            if owner_type == "str":
                return "string(" + owner + "[__pytra_idx(" + index + ", length(" + owner + "))])"
            return owner + "[__pytra_idx(" + index + ", length(" + owner + "))]"
        raise RuntimeError("julia subset: unsupported expr kind: " + kind)

    def _render_for_header(self, node: dict[str, JsonVal]) -> str:
        target_plan = node.get("target_plan")
        iter_plan = node.get("iter_plan")
        if not isinstance(target_plan, dict) or not isinstance(iter_plan, dict):
            raise RuntimeError("julia subset: ForCore missing plan")
        target_name = _ident(_str(target_plan, "id"))
        iter_kind = _str(iter_plan, "kind")
        if iter_kind == "StaticRangeForPlan":
            start = self._render_expr(iter_plan.get("start"))
            stop = self._render_expr(iter_plan.get("stop"))
            step = self._render_expr(iter_plan.get("step"))
            if step == "1":
                return "for " + target_name + " in " + start + ":(" + stop + " - 1)"
            if step.startswith("-"):
                return "for " + target_name + " in " + start + ":" + step + ":(" + stop + " + 1)"
            return (
                "for "
                + target_name
                + " in "
                + start
                + ":"
                + step
                + ":(("
                + step
                + ") > 0 ? ("
                + stop
                + " - 1) : ("
                + stop
                + " + 1))"
            )
        if iter_kind == "RuntimeIterForPlan":
            return "for " + target_name + " in " + self._render_expr(iter_plan.get("iter_expr"))
        raise RuntimeError("julia subset: unsupported ForCore plan: " + iter_kind)

    def _emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            raise RuntimeError("julia subset: stmt must be dict")
        kind = _str(node, "kind")
        if kind == "Import":
            for item in _list(node, "names"):
                if not isinstance(item, dict):
                    continue
                source_name = _str(item, "name")
                bound_name = _ident(_str(item, "asname") or source_name)
                if source_name == "math":
                    self._emit('include(joinpath(@__DIR__, "std", "math_native.jl"))')
                    self._emit(
                        bound_name
                        + " = (ceil=__MathNative.ceil, cos=__MathNative.cos, e=__MathNative.e, exp=__MathNative.exp, "
                        + "fabs=__MathNative.fabs, floor=__MathNative.floor, log=__MathNative.log, log10=__MathNative.log10, "
                        + "pi=__MathNative.pi, pow=__MathNative.pow, sin=__MathNative.sin, sqrt=__MathNative.sqrt, tan=__MathNative.tan)"
                    )
                elif source_name == "pytra.std.env":
                    self._emit(bound_name + ' = (target="julia",)')
                elif source_name == "pytra.std.os":
                    self._emit('include(joinpath(@__DIR__, "std", "os_native.jl"))')
                    self._emit('include(joinpath(@__DIR__, "std", "os_path_native.jl"))')
                    self._emit(
                        bound_name
                        + " = (getcwd=__OsNative.getcwd, makedirs=__OsNative.makedirs, mkdir=__OsNative.mkdir, "
                        + "path=(join=__OsPathNative.join, splitext=__OsPathNative.splitext, "
                        + "basename=__OsPathNative.basename, dirname=__OsPathNative.dirname, exists=__OsPathNative.exists))"
                    )
                elif source_name == "pytra.utils.png":
                    self._emit('include(joinpath(@__DIR__, "utils", "png.jl"))')
                    self._emit(
                        bound_name
                        + " = (_adler32=_adler32, _chunk=_chunk, _crc32=_crc32, _png_append_list=_png_append_list, "
                        + "_png_u16le=_png_u16le, _png_u32be=_png_u32be, _zlib_deflate_store=_zlib_deflate_store, "
                        + "write_rgb_png=write_rgb_png)"
                    )
            return
        if kind == "ImportFrom":
            module_name = _str(node, "module")
            names = _list(node, "names")
            if module_name == "pytra.utils.assertions":
                for item in names:
                    if not isinstance(item, dict):
                        continue
                    name = _str(item, "name")
                    if name == "py_assert_stdout":
                        self._emit("py_assert_stdout(_expected, _fn) = true")
                    elif name == "py_assert_eq":
                        self._emit("py_assert_eq(a, b, _label=\"\") = (a == b)")
                    elif name == "py_assert_all":
                        self._emit("py_assert_all(checks, _label=\"\") = all(checks)")
                    elif name == "py_assert_true":
                        self._emit("py_assert_true(v, _label=\"\") = __pytra_truthy(v)")
                return
            if module_name == "pytra.utils.png":
                self._emit('include(joinpath(@__DIR__, "utils", "png.jl"))')
                return
            if module_name == "pytra.std.collections":
                for item in names:
                    if not isinstance(item, dict):
                        continue
                    source_name = _str(item, "name")
                    bound_name = _ident(_str(item, "asname") or source_name)
                    if source_name == "deque":
                        self._emit(bound_name + " = __pytra_deque")
                return
            if module_name == "math":
                self._emit('include(joinpath(@__DIR__, "std", "math_native.jl"))')
                for item in names:
                    if not isinstance(item, dict):
                        continue
                    source_name = _str(item, "name")
                    bound_name = _ident(_str(item, "asname") or source_name)
                    self._emit(bound_name + " = __MathNative." + source_name)
                return
            if module_name == "pytra.std.math":
                self._emit('include(joinpath(@__DIR__, "std", "math_native.jl"))')
                for item in names:
                    if not isinstance(item, dict):
                        continue
                    source_name = _str(item, "name")
                    bound_name = _ident(_str(item, "asname") or source_name)
                    self._emit(bound_name + " = __MathNative." + source_name)
                return
            if module_name == "time":
                self._emit('include(joinpath(@__DIR__, "std", "time_native.jl"))')
                for item in names:
                    if not isinstance(item, dict):
                        continue
                    source_name = _str(item, "name")
                    bound_name = _ident(_str(item, "asname") or source_name)
                    self._emit(bound_name + " = __TimeNative." + source_name)
                return
            for item in _list(node, "names"):
                if not isinstance(item, dict):
                    continue
                name = _str(item, "name")
                if name == "py_assert_stdout":
                    self._emit("py_assert_stdout(_expected, _fn) = true")
                elif name == "py_assert_eq":
                    self._emit("py_assert_eq(a, b, _label=\"\") = (a == b)")
                elif name == "py_assert_all":
                    self._emit("py_assert_all(checks, _label=\"\") = all(checks)")
                elif name == "py_assert_true":
                    self._emit("py_assert_true(v, _label=\"\") = __pytra_truthy(v)")
            return
        if kind == "Pass":
            self._emit("nothing")
            return
        if kind == "VarDecl":
            self._emit(_ident(_str(node, "name")) + " = nothing")
            return
        if kind == "Raise":
            exc = node.get("exc")
            if exc is None:
                self._emit("rethrow()")
            else:
                self._emit("throw(" + self._render_expr(exc) + ")")
            return
        if kind == "Return":
            value = node.get("value")
            if value is None:
                self._emit("return nothing")
            else:
                self._emit("return " + self._render_expr(value))
            return
        if kind == "Expr":
            value = node.get("value")
            if isinstance(value, dict) and _str(value, "kind") == "Name" and _str(value, "id") == "raise":
                self._emit("rethrow()")
            else:
                self._emit(self._render_expr(value))
            return
        if kind == "AnnAssign":
            self._emit(_ident(_str(node.get("target"), "id")) + " = " + self._render_expr(node.get("value")))
            return
        if kind == "Assign":
            target = node.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Subscript":
                owner_node = target.get("value")
                owner = self._render_expr(owner_node)
                owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                index = self._render_expr(target.get("slice"))
                value = self._render_expr(node.get("value"))
                if owner_type == "bytearray":
                    self._emit(owner + "[__pytra_idx(" + index + ", length(" + owner + "))] = " + value)
                    return
                self._emit(owner + "[" + index + "] = " + value)
                return
            self._emit(_ident(_str(target, "id")) + " = " + self._render_expr(node.get("value")))
            return
        if kind == "Swap":
            left = _ident(_str(node.get("left"), "id"))
            right = _ident(_str(node.get("right"), "id"))
            self._emit(left + ", " + right + " = " + right + ", " + left)
            return
        if kind == "AugAssign":
            target = _ident(_str(node.get("target"), "id"))
            op = _str(node, "op")
            value = self._render_expr(node.get("value"))
            self._emit(target + " = (" + target + " " + _BINOP_TEXT[op] + " " + value + ")")
            return
        if kind == "If":
            self._emit("if __pytra_truthy(" + self._render_expr(node.get("test")) + ")")
            self.indent_level += 1
            for stmt in _list(node, "body"):
                self._emit_stmt(stmt)
            self.indent_level -= 1
            orelse = _list(node, "orelse")
            if len(orelse) > 0:
                self._emit("else")
                self.indent_level += 1
                for stmt in orelse:
                    self._emit_stmt(stmt)
                self.indent_level -= 1
            self._emit("end")
            return
        if kind == "While":
            self._emit("while __pytra_truthy(" + self._render_expr(node.get("test")) + ")")
            self.indent_level += 1
            for stmt in _list(node, "body"):
                self._emit_stmt(stmt)
            self.indent_level -= 1
            self._emit("end")
            return
        if kind == "Try":
            self._emit_try(node)
            return
        if kind == "ForCore":
            self._emit(self._render_for_header(node))
            self.indent_level += 1
            for stmt in _list(node, "body"):
                self._emit_stmt(stmt)
            self.indent_level -= 1
            self._emit("end")
            return
        if kind == "FunctionDef":
            name = _ident(_str(node, "name"))
            args = [_ident(arg) for arg in _list(node, "arg_order") if isinstance(arg, str)]
            self._emit("function " + name + "(" + ", ".join(args) + ")")
            self.indent_level += 1
            for stmt in _list(node, "body"):
                self._emit_stmt(stmt)
            self.indent_level -= 1
            self._emit("end")
            return
        if kind == "ClassDef":
            if _exception_class_supported(node):
                self._emit_exception_class(node)
            else:
                self._emit_class(node)
            return
        raise RuntimeError("julia subset: unsupported stmt kind: " + kind)

    def _emit_try(self, node: dict[str, JsonVal]) -> None:
        handlers = _list(node, "handlers")
        finalbody = _list(node, "finalbody")
        self._emit("try")
        self.indent_level += 1
        for stmt in _list(node, "body"):
            self._emit_stmt(stmt)
        self.indent_level -= 1
        if len(handlers) > 0:
            err_name = "__pytra_err"
            self._emit("catch " + err_name)
            self.indent_level += 1
            for index, handler in enumerate(handlers):
                if not isinstance(handler, dict):
                    continue
                type_node = handler.get("type")
                type_name = self._render_expr(type_node) if isinstance(type_node, dict) else ""
                if type_name in _EXCEPTION_TYPE_TEXT:
                    type_name = _EXCEPTION_TYPE_TEXT[type_name]
                cond = "true" if type_name == "" else err_name + " isa " + type_name
                if index == 0:
                    self._emit("if " + cond)
                else:
                    self._emit("elseif " + cond)
                self.indent_level += 1
                bound_name = handler.get("name")
                if isinstance(bound_name, str) and bound_name != "":
                    self._emit(bound_name + " = " + err_name)
                for stmt in _list(handler, "body"):
                    self._emit_stmt(stmt)
                self.indent_level -= 1
            self._emit("else")
            self.indent_level += 1
            self._emit("rethrow()")
            self.indent_level -= 1
            self._emit("end")
            self.indent_level -= 1
        if len(finalbody) > 0:
            self._emit("finally")
            self.indent_level += 1
            for stmt in finalbody:
                self._emit_stmt(stmt)
            self.indent_level -= 1
        self._emit("end")

    def _emit_class(self, node: dict[str, JsonVal]) -> None:
        class_name = _str(node, "name")
        field_types = node.get("field_types")
        field_names = list(field_types.keys()) if isinstance(field_types, dict) else []
        self._emit("mutable struct " + class_name)
        self.indent_level += 1
        for field_name in field_names:
            self._emit(field_name)
        self.indent_level -= 1
        self._emit("end")
        self._emit_blank()
        self._emit("function __pytra_new_" + class_name + "()")
        self.indent_level += 1
        ctor_args = ", ".join("nothing" for _ in field_names)
        self._emit("self = " + class_name + "(" + ctor_args + ")")
        body = _list(node, "body")
        if len(body) == 1 and isinstance(body[0], dict) and _str(body[0], "kind") == "FunctionDef":
            for stmt in _list(body[0], "body"):
                target = stmt.get("target") if isinstance(stmt, dict) else None
                if isinstance(target, dict):
                    self._emit("self." + _str(target, "attr") + " = " + self._render_expr(stmt.get("value")))
        self._emit("return self")
        self.indent_level -= 1
        self._emit("end")

    def _emit_exception_class(self, node: dict[str, JsonVal]) -> None:
        class_name = _str(node, "name")
        base_name = _str(node, "base")
        base_map = {
            "Exception": "PytraException",
            "ValueError": "PytraValueError",
            "TypeError": "PytraTypeError",
            "RuntimeError": "PytraRuntimeError",
        }
        field_types = node.get("field_types")
        field_names = list(field_types.keys()) if isinstance(field_types, dict) else []
        self._emit("# inherits from " + base_name)
        self._emit("mutable struct " + class_name + " <: " + base_map[base_name])
        self.indent_level += 1
        self._emit("__pytra_message")
        for field_name in field_names:
            self._emit(field_name)
        self.indent_level -= 1
        self._emit("end")
        self._emit("Base.show(io::IO, e::" + class_name + ") = print(io, e.__pytra_message)")
        self._emit("Base.showerror(io::IO, e::" + class_name + ") = print(io, e.__pytra_message)")
        self._emit("__pytra_exception_message(e::" + class_name + ") = string(e.__pytra_message)")
        self._emit_blank()
        init_fn = next(
            stmt for stmt in _list(node, "body") if isinstance(stmt, dict) and _str(stmt, "kind") == "FunctionDef" and _str(stmt, "name") == "__init__"
        )
        args = [arg for arg in _list(init_fn, "arg_order") if isinstance(arg, str) and arg != "self"]
        self._emit("function __pytra_new_" + class_name + "(" + ", ".join(args) + ")")
        self.indent_level += 1
        ctor_args = ['""'] + ["nothing" for _ in field_names]
        self._emit("self = " + class_name + "(" + ", ".join(ctor_args) + ")")
        for stmt in _list(init_fn, "body"):
            if not isinstance(stmt, dict):
                continue
            if _str(stmt, "kind") == "Expr":
                value = stmt.get("value")
                if isinstance(value, dict):
                    call_args = [self._render_expr(arg) for arg in _list(value, "args")]
                    if len(call_args) == 1:
                        self._emit("self.__pytra_message = string(" + call_args[0] + ")")
                continue
            target = stmt.get("target")
            if isinstance(target, dict):
                self._emit("self." + _str(target, "attr") + " = " + self._render_expr(stmt.get("value")))
        self._emit("return self")
        self.indent_level -= 1
        self._emit("end")

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        self.lines = []
        self.indent_level = 0
        self.tmp_counter = 0
        self.function_names = {
            _str(stmt, "name")
            for stmt in _list(east3_doc, "body")
            if isinstance(stmt, dict) and _str(stmt, "kind") == "FunctionDef"
        }
        self.class_names = {
            _str(stmt, "name")
            for stmt in _list(east3_doc, "body")
            if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef"
        }
        self.exception_class_names = {
            _str(stmt, "name")
            for stmt in _list(east3_doc, "body")
            if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef" and _exception_class_supported(stmt)
        }
        self._emit('include(joinpath(@__DIR__, "built_in", "py_runtime.jl"))')
        self._emit_blank()
        for stmt in _list(east3_doc, "body"):
            self._emit_stmt(stmt)
            if _str(stmt, "kind") == "FunctionDef":
                self._emit_blank()
        main_guard_body = _list(east3_doc, "main_guard_body")
        if len(main_guard_body) > 0:
            for stmt in main_guard_body:
                self._emit_stmt(stmt)
        return "\n".join(self.lines).rstrip() + "\n"

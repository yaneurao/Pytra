"""Small toolchain2-native Julia subset renderer.

This module intentionally supports only a narrow AST subset so the Julia
backend can start migrating off the legacy emitter incrementally.
Unsupported modules must fall back to the legacy bridge.
"""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain2.emit.common.code_emitter import RuntimeMapping
from toolchain2.emit.common.code_emitter import build_import_alias_map
from toolchain2.emit.common.code_emitter import build_runtime_import_map
from toolchain2.emit.common.code_emitter import resolve_runtime_call
from toolchain2.emit.common.code_emitter import should_skip_module


_BINOP_TEXT = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "div",
    "LShift": "<<",
    "Mod": "%",
    "BitAnd": "&",
    "BitOr": "|",
    "BitXor": "xor",
    "RShift": ">>",
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
    "Invert": "~",
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


def _function_arg_order(node: dict[str, JsonVal]) -> list[str]:
    return [arg for arg in _list(node, "arg_order") if isinstance(arg, str)]


def _function_decorators(node: dict[str, JsonVal]) -> set[str]:
    return {value for value in _list(node, "decorators") if isinstance(value, str)}


def _is_init_function(node: dict[str, JsonVal]) -> bool:
    return _str(node, "kind") == "FunctionDef" and _str(node, "name") == "__init__"


def _is_static_method(node: dict[str, JsonVal]) -> bool:
    return "staticmethod" in _function_decorators(node)


def _is_property_method(node: dict[str, JsonVal]) -> bool:
    return "property" in _function_decorators(node)


def _is_init_name(name: str) -> bool:
    return name == "__init__"


def _is_enum_base_name(base_name: str) -> bool:
    return base_name in {"Enum", "IntEnum", "IntFlag"}


def _simple_class_supported(node: dict[str, JsonVal]) -> bool:
    body = _list(node, "body")
    if len(body) == 0:
        return True
    if len(body) == 1 and isinstance(body[0], dict) and _str(body[0], "kind") == "Pass":
        return True
    for stmt in body:
        if not isinstance(stmt, dict):
            return False
        if _str(stmt, "kind") != "FunctionDef":
            return False
        if not all(_stmt_supported(inner) for inner in _list(stmt, "body")):
            return False
    return True


def _exception_class_supported(node: dict[str, JsonVal]) -> bool:
    base_name = _str(node, "base")
    if base_name == "":
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
        if _is_init_function(stmt):
            if init_fn is not None:
                return False
            init_fn = stmt
            continue
        return False
    if init_fn is None:
        return False
    args = _function_arg_order(init_fn)
    if len(args) < 2:
        return False
    instance_arg = args[0]
    for stmt in _list(init_fn, "body"):
        if not isinstance(stmt, dict):
            return False
        kind = _str(stmt, "kind")
        if kind == "Expr":
            value = stmt.get("value")
            if not isinstance(value, dict) or _str(value, "kind") != "Call":
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
        if not isinstance(owner, dict) or _str(owner, "kind") != "Name" or _str(owner, "id") != instance_arg:
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
    _ = module_name
    return all(isinstance(item, dict) and _str(item, "name") != "" for item in names)


def _assign_target_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind == "Name":
        return True
    if kind == "Subscript":
        return _expr_supported(node.get("value")) and _expr_supported(node.get("slice"))
    if kind in {"Tuple", "List"}:
        elements = _list(node, "elements")
        return len(elements) > 0 and all(_assign_target_supported(item) for item in elements)
    return False


def _ident(name: str) -> str:
    if name in _JULIA_RESERVED_NAMES:
        return name + "_py"
    return name


def _import_supported(names: list[JsonVal]) -> bool:
    return all(isinstance(item, dict) and _str(item, "name") != "" for item in names)


def _comp_generator_supported(node: dict[str, JsonVal]) -> bool:
    target = node.get("target")
    if not isinstance(target, dict):
        return False
    target_kind = _str(target, "kind")
    if target_kind == "Name":
        pass
    elif target_kind in {"Tuple", "List"}:
        elements = _list(target, "elements")
        if len(elements) == 0 or not all(isinstance(item, dict) and _str(item, "kind") == "Name" for item in elements):
            return False
    else:
        return False
    return _expr_supported(node.get("iter")) and all(_expr_supported(item) for item in _list(node, "ifs"))


def _isinstance_expected_name(node: dict[str, JsonVal]) -> str:
    expected_any = node.get("expected_type_id")
    if isinstance(expected_any, dict) and _str(expected_any, "kind") == "Name":
        expected_id = expected_any.get("id")
        if isinstance(expected_id, str) and expected_id != "":
            return expected_id
    expected_name = node.get("expected_type_name")
    if isinstance(expected_name, str):
        return expected_name
    return ""


def _call_keywords_supported(keywords: list[JsonVal]) -> bool:
    return all(
        isinstance(item, dict)
        and isinstance(item.get("arg"), str)
        and _expr_supported(item.get("value"))
        for item in keywords
    )


def _attribute_call_supported(node: dict[str, JsonVal], func: dict[str, JsonVal], keywords: list[JsonVal]) -> bool:
    owner = func.get("value")
    runtime_call = _str(node, "resolved_runtime_call")
    if runtime_call == "":
        runtime_call = _str(node, "runtime_call")
    if not _expr_supported(owner):
        return False
    if not all(_expr_supported(arg) for arg in _list(node, "args")):
        return False
    if not _call_keywords_supported(keywords):
        return False
    if runtime_call != "":
        return True
    return len(keywords) == 0


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
    if kind == "ListComp":
        generators = _list(node, "generators")
        return len(generators) == 1 and isinstance(generators[0], dict) and _expr_supported(node.get("elt")) and _comp_generator_supported(generators[0])
    if kind == "SetComp":
        generators = _list(node, "generators")
        return len(generators) == 1 and isinstance(generators[0], dict) and _expr_supported(node.get("elt")) and _comp_generator_supported(generators[0])
    if kind == "DictComp":
        generators = _list(node, "generators")
        return len(generators) == 1 and isinstance(generators[0], dict) and _expr_supported(node.get("key")) and _expr_supported(node.get("value")) and _comp_generator_supported(generators[0])
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
    if kind == "IsInstance":
        return _expr_supported(node.get("value")) and _isinstance_expected_name(node) != ""
    if kind == "Lambda":
        args = _list(node, "args")
        return all(isinstance(arg, dict) and isinstance(arg.get("arg"), str) for arg in args) and _expr_supported(node.get("body"))
    if kind == "Call":
        func = node.get("func")
        keywords = _list(node, "keywords")
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            return _attribute_call_supported(node, func, keywords)
        return (
            _expr_supported(node.get("func"))
            and all(_expr_supported(arg) for arg in _list(node, "args"))
            and _call_keywords_supported(keywords)
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
        if not isinstance(target, dict):
            return False
        target_kind = _str(target, "kind")
        if target_kind == "Name":
            value = node.get("value")
            return value is None or _expr_supported(value)
        if target_kind == "Attribute":
            owner = target.get("value")
            if not isinstance(owner, dict) or _str(owner, "kind") != "Name":
                return False
            value = node.get("value")
            return value is None or _expr_supported(value)
        value = node.get("value")
        return False
    if kind == "Assign":
        target = node.get("target")
        if not isinstance(target, dict):
            return False
        target_kind = _str(target, "kind")
        if target_kind == "Name":
            return _expr_supported(node.get("value"))
        if target_kind == "Attribute":
            return _expr_supported(target.get("value")) and _expr_supported(node.get("value"))
        if target_kind == "Subscript":
            return _expr_supported(target.get("value")) and _expr_supported(target.get("slice")) and _expr_supported(node.get("value"))
        if target_kind in {"Tuple", "List"}:
            return _assign_target_supported(target) and _expr_supported(node.get("value"))
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
        if not isinstance(target, dict) or _str(node, "op") not in _BINOP_TEXT or not _expr_supported(node.get("value")):
            return False
        if _str(target, "kind") == "Name":
            return True
        if _str(target, "kind") == "Attribute":
            owner = target.get("value")
            return isinstance(owner, dict) and _str(owner, "kind") == "Name"
        return False
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
    if kind == "TypeAlias":
        return True
    if kind == "ClassDef":
        return _simple_class_supported(node) or _exception_class_supported(node)
    return False


def can_render_module_natively(east3_doc: dict[str, JsonVal]) -> bool:
    body = _list(east3_doc, "body")
    main_guard_body = _list(east3_doc, "main_guard_body")
    exception_base_names = {
        _str(stmt, "base")
        for stmt in body
        if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef" and _exception_class_supported(stmt)
    }
    for stmt in body:
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "ClassDef":
            continue
        if _str(stmt, "name") in exception_base_names and _str(stmt, "base") == "":
            return False
    return all(_stmt_supported(stmt) for stmt in body) and all(_stmt_supported(stmt) for stmt in main_guard_body)


class JuliaSubsetRenderer:
    def __init__(self, mapping: RuntimeMapping | None = None, meta: dict[str, JsonVal] | None = None) -> None:
        self.lines: list[str] = []
        self.indent_level = 0
        self.tmp_counter = 0
        self.mapping = mapping if mapping is not None else RuntimeMapping()
        self.meta = meta if isinstance(meta, dict) else {}
        self.function_names: set[str] = set()
        self.class_names: set[str] = set()
        self.exception_class_names: set[str] = set()
        self.class_base_names: dict[str, str] = {}
        self.class_subclasses: dict[str, set[str]] = {}
        self.class_direct_field_names: dict[str, list[str]] = {}
        self.class_all_field_names: dict[str, list[str]] = {}
        self.class_method_names: dict[str, set[str]] = {}
        self.class_property_names: dict[str, set[str]] = {}
        self.class_static_method_names: dict[str, set[str]] = {}
        self.current_class_name: str = ""
        self.import_alias_modules: dict[str, str] = build_import_alias_map(self.meta)
        self.runtime_imports: dict[str, str] = build_runtime_import_map(self.meta, self.mapping)
        self.emitted_native_files: set[str] = set()

    def _base_name(self, class_name: str) -> str:
        return self.class_base_names.get(class_name, "")

    def _has_subclasses(self, class_name: str) -> bool:
        return len(self.class_subclasses.get(class_name, set())) > 0

    def _uses_abstract_backing(self, class_name: str) -> bool:
        return self._base_name(class_name) != "" or self._has_subclasses(class_name)

    def _class_impl_name(self, class_name: str) -> str:
        if self._uses_abstract_backing(class_name):
            return "__pytra_cls_" + class_name
        return class_name

    def _method_impl_name(self, class_name: str, method_name: str) -> str:
        return "__pytra_method_" + class_name + "_" + method_name

    def _resolve_exception_base_type(self, base_name: str) -> str:
        base_type = self.mapping.predicate_types.get(base_name, "")
        if base_type == "" and base_name in self.exception_class_names:
            return base_name
        return base_type

    def _collect_field_names(self, class_name: str, visiting: set[str] | None = None) -> list[str]:
        if class_name in self.class_all_field_names:
            return list(self.class_all_field_names[class_name])
        if visiting is None:
            visiting = set()
        if class_name in visiting:
            return []
        visiting = set(visiting)
        visiting.add(class_name)
        out: list[str] = []
        base_name = self._base_name(class_name)
        if base_name != "":
            for field_name in self._collect_field_names(base_name, visiting):
                if field_name not in out:
                    out.append(field_name)
        for field_name in self.class_direct_field_names.get(class_name, []):
            if field_name not in out:
                out.append(field_name)
        self.class_all_field_names[class_name] = list(out)
        return out

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _emit(self, line: str) -> None:
        self.lines.append(self._indent() + line)

    def _emit_blank(self) -> None:
        self.lines.append("")

    def _emit_native_module_include(self, module_id: str) -> None:
        native_rel = self.mapping.module_native_files.get(module_id, "")
        if native_rel == "":
            return
        for native_item in native_rel.split("|"):
            native_file = native_item.strip()
            if native_file == "" or native_file in self.emitted_native_files:
                continue
            self.emitted_native_files.add(native_file)
            parts = [part for part in native_file.split("/") if part != ""]
            if len(parts) == 0:
                continue
            join_parts = ', '.join(_quote_string(part) for part in parts)
            self._emit("include(joinpath(@__DIR__, " + join_parts + "))")

    def _emit_runtime_binding(self, local_name: str, resolved_name: str) -> None:
        local_ident = _ident(local_name)
        if local_ident == resolved_name:
            return
        self._emit(local_ident + " = " + resolved_name)

    def _emit_module_namespace_binding(self, local_name: str, module_id: str) -> None:
        self._emit_native_module_include(module_id)
        expr = self.mapping.module_namespace_exprs.get(module_id, "")
        if expr == "":
            return
        self._emit(_ident(local_name) + " = " + expr)

    def _resolve_subset_runtime_call(self, runtime_call: str, adapter_kind: str, builtin_name: str) -> str:
        mapped_runtime = resolve_runtime_call(runtime_call, builtin_name, adapter_kind, self.mapping)
        if mapped_runtime == "":
            return ""
        if runtime_call not in self.mapping.calls and builtin_name not in self.mapping.calls:
            return ""
        if "." in runtime_call and runtime_call not in self.mapping.calls:
            if builtin_name in self.mapping.calls:
                return self.mapping.calls[builtin_name]
            return ""
        return mapped_runtime

    def _render_mapped_runtime_call(
        self,
        mapped: str,
        args: list[str],
        result_type: str,
        builtin_name: str = "",
        source_type: str = "",
        keywords: list[dict[str, JsonVal]] | None = None,
    ) -> str:
        kw_items = keywords if isinstance(keywords, list) else []
        if mapped == "":
            return ""
        if mapped == "__CAST__":
            return self._render_static_cast_call(builtin_name, result_type, args, source_type)
        if mapped == "__MAKEDIRS__":
            if len(args) == 1 and len(kw_items) == 1 and kw_items[0].get("arg") == "exist_ok":
                return "__pytra_makedirs(" + args[0] + ", " + self._render_expr(kw_items[0].get("value")) + ")"
            return ""
        scalar_expr = self._render_scalar_runtime_call(mapped, args)
        if scalar_expr != "":
            return scalar_expr
        collection_expr = self._render_collection_runtime_call(mapped, args)
        if collection_expr != "":
            return collection_expr
        string_expr = self._render_string_runtime_call(mapped, args)
        if string_expr != "":
            return string_expr
        range_expr = self._render_range_runtime_call(mapped, args)
        if range_expr != "":
            return range_expr
        if len(args) == 0:
            return mapped + "()"
        return mapped + "(" + ", ".join(args) + ")"

    def _render_scalar_runtime_call(self, mapped: str, args: list[str]) -> str:
        if mapped == "__INT__" and len(args) == 1:
            return "__pytra_int(" + args[0] + ")"
        if mapped == "__BYTES_CTOR__":
            if len(args) == 0:
                return "UInt8[]"
            if len(args) == 1:
                return "__pytra_bytes(" + args[0] + ")"
        if mapped == "__SET_CTOR__" and len(args) == 0:
            return "Set()"
        return ""

    def _render_collection_runtime_call(self, mapped: str, args: list[str]) -> str:
        if mapped == "__LIST_APPEND__" and len(args) == 2:
            return "push!(" + args[0] + ", " + args[1] + ")"
        if mapped == "__LIST_POP__":
            if len(args) == 1:
                return "pop!(" + args[0] + ")"
            if len(args) == 2:
                return "pop!(" + args[0] + ", " + args[1] + ")"
            return ""
        if mapped == "__LIST_EXTEND__" and len(args) == 2:
            return "append!(" + args[0] + ", " + args[1] + ")"
        if mapped == "__LIST_INDEX__" and len(args) == 2:
            return "(findfirst(==(" + args[1] + "), " + args[0] + ") - 1)"
        if mapped == "__LIST_CLEAR__" and len(args) == 1:
            return "empty!(" + args[0] + ")"
        if mapped == "__LIST_REVERSE__" and len(args) == 1:
            return "reverse!(" + args[0] + ")"
        if mapped == "__LIST_SORT__" and len(args) == 1:
            return "sort!(" + args[0] + ")"
        if mapped == "__DEQUE_APPENDLEFT__" and len(args) == 2:
            return "pushfirst!(" + args[0] + ", " + args[1] + ")"
        if mapped == "__DEQUE_POPLEFT__" and len(args) == 1:
            return "popfirst!(" + args[0] + ")"
        if mapped == "__DICT_GET__":
            if len(args) == 2:
                return "get(" + args[0] + ", " + args[1] + ", nothing)"
            if len(args) == 3:
                return "get(" + args[0] + ", " + args[1] + ", " + args[2] + ")"
            return ""
        if mapped == "__DICT_POP__":
            if len(args) == 2:
                return "pop!(" + args[0] + ", " + args[1] + ")"
            if len(args) == 3:
                return "pop!(" + args[0] + ", " + args[1] + ", " + args[2] + ")"
            return ""
        if mapped == "__DICT_ITEMS__" and len(args) == 1:
            return "collect(pairs(" + args[0] + "))"
        if mapped == "__DICT_KEYS__" and len(args) == 1:
            return "collect(keys(" + args[0] + "))"
        if mapped == "__DICT_VALUES__" and len(args) == 1:
            return "collect(values(" + args[0] + "))"
        if mapped == "__DICT_SETDEFAULT__" and len(args) == 3:
            return "get!(" + args[0] + ", " + args[1] + ", " + args[2] + ")"
        if mapped == "__SET_ADD__" and len(args) == 2:
            return "push!(" + args[0] + ", " + args[1] + ")"
        if mapped == "__SET_DISCARD__" and len(args) == 2:
            return "delete!(" + args[0] + ", " + args[1] + ")"
        if mapped == "__SET_REMOVE__" and len(args) == 2:
            return "delete!(" + args[0] + ", " + args[1] + ")"
        return ""

    def _render_string_runtime_call(self, mapped: str, args: list[str]) -> str:
        if mapped == "__STR_REPLACE__" and len(args) == 3:
            return "replace(" + args[0] + ", " + args[1] + " => " + args[2] + ")"
        if mapped == "__STR_JOIN__" and len(args) == 2:
            return "join(" + args[1] + ", " + args[0] + ")"
        if mapped == "__STR_COUNT__" and len(args) == 2:
            return "count(" + args[1] + ", " + args[0] + ")"
        if mapped == "__STR_INDEX__" and len(args) == 2:
            return "__pytra_str_find(" + args[0] + ", " + args[1] + ")"
        if mapped == "__STR_ISSPACE__" and len(args) == 1:
            return "((length(" + args[0] + ") != 0) && all(isspace, " + args[0] + "))"
        return ""

    def _render_range_runtime_call(self, mapped: str, args: list[str]) -> str:
        if mapped != "__RANGE__":
            return ""
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
        return ""

    def _render_mapped_method_call(
        self,
        node: dict[str, JsonVal],
        owner: str,
        args: list[str],
    ) -> str:
        runtime_call = _str(node, "resolved_runtime_call")
        if runtime_call == "":
            runtime_call = _str(node, "runtime_call")
        mapped = self.mapping.calls.get(runtime_call, "")
        if mapped == "":
            return ""
        owner_node = node.get("func")
        source_type = ""
        if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Attribute":
            value_node = owner_node.get("value")
            if isinstance(value_node, dict):
                source_type = _str(value_node, "resolved_type")
        return self._render_mapped_runtime_call(mapped, [owner] + args, _str(node, "resolved_type"), source_type=source_type)

    def _render_static_cast_call(self, builtin_name: str, result_type: str, args: list[str], source_type: str) -> str:
        if len(args) != 1:
            return ""
        if source_type != "" and self.mapping.is_implicit_cast(source_type, result_type):
            return args[0]
        if builtin_name == "int" or result_type in {"int", "int64"}:
            return "__pytra_int(" + args[0] + ")"
        if builtin_name == "bool" or result_type == "bool":
            return "__pytra_truthy(" + args[0] + ")"
        if builtin_name == "str" or result_type in {"str", "string"}:
            return "__pytra_str(" + args[0] + ")"
        target_type = self.mapping.types.get(result_type, "")
        if target_type != "":
            return target_type + "(" + args[0] + ")"
        return ""

    def _render_super_method_call(self, owner_type: str, attr: str, args: list[str]) -> str:
        base_name = self._base_name(owner_type)
        if base_name == "" and self.current_class_name != "":
            base_name = self._base_name(self.current_class_name)
        if base_name == "":
            return ""
        if _is_init_name(attr):
            pieces = ["__pytra_base = __pytra_new_" + base_name + "(" + ", ".join(args) + ")"]
            for field_name in self._collect_field_names(base_name):
                pieces.append("self." + field_name + " = __pytra_base." + field_name)
            pieces.append("nothing")
            return "(begin " + "; ".join(pieces) + "; end)"
        return self._method_impl_name(base_name, attr) + "(self" + (", " if len(args) > 0 else "") + ", ".join(args) + ")"

    def _render_class_dispatch_call(
        self,
        owner: str,
        owner_type: str,
        owner_name: str,
        attr: str,
        args: list[str],
        keywords: list[dict[str, JsonVal]],
    ) -> str:
        if len(keywords) != 0:
            return ""
        if attr in self.class_static_method_names.get(owner_name, set()):
            return _ident(attr) + "(" + ", ".join(args) + ")"
        if attr in self.class_method_names.get(owner_type, set()):
            call_args = [owner]
            call_args.extend(args)
            return _ident(attr) + "(" + ", ".join(call_args) + ")"
        return ""

    def _render_attribute_call(
        self,
        node: dict[str, JsonVal],
        owner_node: JsonVal,
        owner: str,
        owner_type: str,
        owner_name: str,
        attr: str,
        args: list[str],
        keywords: list[dict[str, JsonVal]],
    ) -> str:
        if (
            isinstance(owner_node, dict)
            and _str(owner_node, "kind") == "Call"
            and isinstance(owner_node.get("func"), dict)
            and _str(owner_node.get("func"), "kind") == "Name"
            and _str(owner_node.get("func"), "id") == "super"
        ):
            super_call = self._render_super_method_call(owner_type, attr, args)
            if super_call != "":
                return super_call
        mapped_method = self._render_mapped_method_call(node, owner, args)
        if mapped_method != "":
            return mapped_method
        runtime_call = _str(node, "resolved_runtime_call")
        if runtime_call == "":
            runtime_call = _str(node, "runtime_call")
        mapped_runtime = self.mapping.calls.get(runtime_call, "")
        if mapped_runtime != "":
            mapped_expr = self._render_mapped_runtime_call(
                mapped_runtime,
                args,
                _str(node, "resolved_type"),
                keywords=keywords,
            )
            if mapped_expr != "":
                return mapped_expr
        class_dispatch = self._render_class_dispatch_call(owner, owner_type, owner_name, attr, args, keywords)
        if class_dispatch != "":
            return class_dispatch
        raise RuntimeError("julia subset: attribute call requires runtime metadata: " + attr)

    def _render_name_call(
        self,
        func: str,
        args: list[str],
        runtime_call: str,
        builtin_name: str,
        result_type: str,
        use_mapped_runtime: str,
        source_type: str,
    ) -> str:
        if use_mapped_runtime != "":
            mapped_expr = self._render_mapped_runtime_call(
                use_mapped_runtime,
                args,
                result_type,
                builtin_name=builtin_name,
                source_type=source_type,
            )
            if mapped_expr != "":
                return mapped_expr
        return ""

    def _render_constructor_call(self, func: str, args: list[str]) -> str:
        if func in self.exception_class_names:
            return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
        if func in self.class_names:
            return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
        return ""

    def _render_attribute_call_maybe(self, node: dict[str, JsonVal], func_node: JsonVal) -> str:
        if not isinstance(func_node, dict) or _str(func_node, "kind") != "Attribute":
            return ""
        owner_node = func_node.get("value")
        owner = self._render_expr(owner_node)
        owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
        attr = _str(func_node, "attr")
        owner_name = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
        args = [self._render_expr(arg) for arg in _list(node, "args")]
        keywords = [item for item in _list(node, "keywords") if isinstance(item, dict)]
        return self._render_attribute_call(node, owner_node, owner, owner_type, owner_name, attr, args, keywords)

    def _resolve_call_runtime_target(self, node: dict[str, JsonVal], func_node: JsonVal) -> tuple[str, str, str]:
        runtime_call = _str(node, "resolved_runtime_call")
        if runtime_call == "":
            runtime_call = _str(node, "runtime_call")
        adapter_kind = _str(node, "runtime_call_adapter_kind")
        builtin_name = ""
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
            candidate_name = _str(func_node, "id")
            if runtime_call != "" or candidate_name in self.mapping.calls:
                builtin_name = candidate_name
        use_mapped_runtime = self._resolve_subset_runtime_call(runtime_call, adapter_kind, builtin_name)
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
            use_mapped_runtime = ""
        return runtime_call, builtin_name, use_mapped_runtime

    def _render_isinstance_expr(self, node: dict[str, JsonVal]) -> str:
        value = self._render_expr(node.get("value"))
        expected_name = _isinstance_expected_name(node)
        mapped = self.mapping.predicate_types.get(expected_name, "")
        if mapped == "":
            mapped = self.mapping.types.get(expected_name, "")
        if mapped != "":
            return "(isa(" + value + ", " + mapped + "))"
        if expected_name in self.class_names or expected_name in self.exception_class_names:
            return "(isa(" + value + ", " + expected_name + "))"
        return "false"

    def _render_subscript_expr(self, node: dict[str, JsonVal]) -> str:
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
            return "string(" + owner + "[__pytra_idx(__pytra_int(" + index + "), length(" + owner + "))])"
        return owner + "[__pytra_idx(__pytra_int(" + index + "), length(" + owner + "))]"

    def _render_literal_or_comp_expr(self, node: dict[str, JsonVal], kind: str) -> str:
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
        if kind == "ListComp":
            generator = _list(node, "generators")[0]
            assert isinstance(generator, dict)
            elt = self._render_expr(node.get("elt"))
            loop_var = self._render_comp_target(generator.get("target"))
            iter_expr = self._render_comp_iter(generator.get("iter"))
            return "[" + elt + " for " + loop_var + " in " + iter_expr + self._render_comp_if_suffix(generator) + "]"
        if kind == "SetComp":
            generator = _list(node, "generators")[0]
            assert isinstance(generator, dict)
            elt = self._render_expr(node.get("elt"))
            loop_var = self._render_comp_target(generator.get("target"))
            iter_expr = self._render_comp_iter(generator.get("iter"))
            return "Set([" + elt + " for " + loop_var + " in " + iter_expr + self._render_comp_if_suffix(generator) + "])"
        if kind == "DictComp":
            generator = _list(node, "generators")[0]
            assert isinstance(generator, dict)
            key_expr = self._render_expr(node.get("key"))
            value_expr = self._render_expr(node.get("value"))
            loop_var = self._render_comp_target(generator.get("target"))
            iter_expr = self._render_comp_iter(generator.get("iter"))
            return "Dict(" + key_expr + " => " + value_expr + " for " + loop_var + " in " + iter_expr + self._render_comp_if_suffix(generator) + ")"
        return ""

    def _render_operator_expr(self, node: dict[str, JsonVal], kind: str) -> str:
        if kind == "BinOp":
            op = _str(node, "op")
            left = self._render_expr(node.get("left"))
            right = self._render_expr(node.get("right"))
            if op == "FloorDiv":
                return "div(" + left + ", " + right + ")"
            if op == "BitXor":
                return "xor(" + left + ", " + right + ")"
            if op == "Add":
                left_node = node.get("left")
                right_node = node.get("right")
                lhs_resolved = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
                rhs_resolved = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
                if lhs_resolved == "str" or rhs_resolved == "str":
                    return "(" + left + " * " + right + ")"
                if lhs_resolved.startswith("list[") or rhs_resolved.startswith("list["):
                    return "vcat(" + left + ", " + right + ")"
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
        return ""

    def _render_simple_expr(self, node: dict[str, JsonVal], kind: str) -> str:
        if kind == "Name":
            name = _str(node, "id")
            if name == "main" and "__pytra_main" in self.function_names:
                return "__pytra_main"
            return _ident(name)
        if kind == "Attribute":
            owner_node = node.get("value")
            if (
                isinstance(owner_node, dict)
                and _str(owner_node, "kind") == "Call"
                and isinstance(owner_node.get("func"), dict)
                and _str(owner_node.get("func"), "kind") == "Name"
                and _str(owner_node.get("func"), "id") == "type"
                and _str(node, "attr") == "__name__"
            ):
                args = _list(owner_node, "args")
                if len(args) >= 1:
                    return "string(nameof(typeof(" + self._render_expr(args[0]) + ")))"
            owner = self._render_expr(owner_node)
            owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            attr = _str(node, "attr")
            if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Name":
                owner_name = _str(owner_node, "id")
                if attr in self.class_static_method_names.get(owner_name, set()):
                    return _ident(attr)
            if attr in self.class_property_names.get(owner_type, set()):
                return _ident(attr) + "(" + owner + ")"
            return owner + "." + attr
        if kind == "FormattedValue":
            format_spec = node.get("format_spec")
            if isinstance(format_spec, str) and format_spec != "":
                return "__pytra_format(" + self._render_expr(node.get("value")) + ", " + _quote_string(format_spec) + ")"
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
        return ""

    def _render_call_expr(self, node: dict[str, JsonVal]) -> str:
        func_node = node.get("func")
        attr_call = self._render_attribute_call_maybe(node, func_node)
        if attr_call != "":
            return attr_call
        func = self._render_expr(func_node)
        args = [self._render_expr(arg) for arg in _list(node, "args")]
        runtime_call, builtin_name, use_mapped_runtime = self._resolve_call_runtime_target(node, func_node)
        result_type = _str(node, "resolved_type")
        source_type = ""
        arg_nodes = _list(node, "args")
        if len(arg_nodes) >= 1 and isinstance(arg_nodes[0], dict):
            source_type = _str(arg_nodes[0], "resolved_type")
        name_call = self._render_name_call(
            func,
            args,
            runtime_call,
            builtin_name,
            result_type,
            use_mapped_runtime,
            source_type,
        )
        if name_call != "":
            return name_call
        constructor_call = self._render_constructor_call(func, args)
        if constructor_call != "":
            return constructor_call
        return func + "(" + ", ".join(args) + ")"

    def _next_tmp(self, prefix: str) -> str:
        self.tmp_counter += 1
        return prefix + str(self.tmp_counter)

    def _render_expr(self, node: JsonVal) -> str:
        if not isinstance(node, dict):
            raise RuntimeError("julia subset: expr must be dict")
        kind = _str(node, "kind")
        simple_expr = self._render_simple_expr(node, kind)
        if simple_expr != "":
            return simple_expr
        literal_or_comp = self._render_literal_or_comp_expr(node, kind)
        if literal_or_comp != "":
            return literal_or_comp
        operator_expr = self._render_operator_expr(node, kind)
        if operator_expr != "":
            return operator_expr
        if kind == "IsInstance":
            return self._render_isinstance_expr(node)
        if kind == "Call":
            return self._render_call_expr(node)
        if kind in {"Box", "Unbox"}:
            return self._render_expr(node.get("value"))
        if kind == "Subscript":
            return self._render_subscript_expr(node)
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
            iter_expr_node = iter_plan.get("iter_expr")
            iter_expr = self._render_expr(iter_expr_node)
            if isinstance(iter_expr_node, dict) and _str(iter_expr_node, "resolved_type") == "str":
                iter_expr = "(__pytra_str(__pytra_ch) for __pytra_ch in " + iter_expr + ")"
            return "for " + target_name + " in " + iter_expr
        raise RuntimeError("julia subset: unsupported ForCore plan: " + iter_kind)

    def _emit_assign_target(self, target: dict[str, JsonVal], value_expr: str) -> None:
        kind = _str(target, "kind")
        if kind == "Name":
            self._emit(_ident(_str(target, "id")) + " = " + value_expr)
            return
        if kind == "Subscript":
            owner_node = target.get("value")
            owner = self._render_expr(owner_node)
            owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
            index = self._render_expr(target.get("slice"))
            index_expr = "__pytra_int(" + index + ")"
            if owner_type == "bytearray":
                self._emit(owner + "[__pytra_idx(" + index_expr + ", length(" + owner + "))] = " + value_expr)
                return
            self._emit(owner + "[__pytra_idx(" + index_expr + ", length(" + owner + "))] = " + value_expr)
            return
        if kind in {"Tuple", "List"}:
            seq_tmp = self._next_tmp("__pytra_unpack_")
            self._emit(seq_tmp + " = " + value_expr)
            for index, item in enumerate(_list(target, "elements")):
                if not isinstance(item, dict):
                    raise RuntimeError("julia subset: unpack target must be dict")
                item_expr = seq_tmp + "[__pytra_idx(" + str(index) + ", length(" + seq_tmp + "))]"
                self._emit_assign_target(item, item_expr)
            return
        raise RuntimeError("julia subset: unsupported assign target kind: " + kind)

    def _render_comp_target(self, target: dict[str, JsonVal]) -> str:
        kind = _str(target, "kind")
        if kind == "Name":
            return _ident(_str(target, "id"))
        if kind in {"Tuple", "List"}:
            parts: list[str] = []
            for item in _list(target, "elements"):
                if isinstance(item, dict) and _str(item, "kind") == "Name":
                    parts.append(_ident(_str(item, "id")))
            if len(parts) == 0:
                raise RuntimeError("julia subset: empty comprehension target")
            return "(" + ", ".join(parts) + ")"
        raise RuntimeError("julia subset: unsupported comprehension target kind: " + kind)

    def _render_comp_iter(self, node: JsonVal) -> str:
        iter_expr = self._render_expr(node)
        if isinstance(node, dict) and _str(node, "resolved_type") == "str":
            return "(__pytra_str(__pytra_ch) for __pytra_ch in " + iter_expr + ")"
        return iter_expr

    def _render_comp_if_suffix(self, generator: dict[str, JsonVal]) -> str:
        conditions = [self._render_expr(item) for item in _list(generator, "ifs")]
        if len(conditions) == 0:
            return ""
        return " if " + " && ".join(conditions)

    def _emit_import_stmt(self, node: dict[str, JsonVal]) -> None:
        for item in _list(node, "names"):
            if not isinstance(item, dict):
                continue
            source_name = _str(item, "name")
            bound_name = _ident(_str(item, "asname") or source_name)
            if should_skip_module(source_name, self.mapping):
                self._emit_module_namespace_binding(bound_name, source_name)

    def _emit_import_from_stmt(self, node: dict[str, JsonVal]) -> None:
        module_name = _str(node, "module")
        names = _list(node, "names")
        if should_skip_module(module_name, self.mapping):
            self._emit_native_module_include(module_name)
        for item in names:
            if not isinstance(item, dict):
                continue
            source_name = _str(item, "name")
            local_name = _str(item, "asname") or source_name
            resolved_name = self.runtime_imports.get(local_name, "")
            if resolved_name != "":
                self._emit_runtime_binding(local_name, resolved_name)
                continue
            sub_mod = self.import_alias_modules.get(local_name, "")
            if sub_mod != "" and sub_mod != module_name and should_skip_module(sub_mod, self.mapping):
                self._emit_module_namespace_binding(local_name, sub_mod)

    def _emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        target = node.get("target")
        if isinstance(target, dict) and _str(target, "kind") == "Attribute":
            owner = self._render_expr(target.get("value"))
            attr = _str(target, "attr")
            self._emit(owner + "." + attr + " = " + self._render_expr(node.get("value")))
            return
        if isinstance(target, dict) and _str(target, "kind") == "Subscript":
            owner_node = target.get("value")
            owner = self._render_expr(owner_node)
            index = self._render_expr(target.get("slice"))
            index_expr = "__pytra_int(" + index + ")"
            value = self._render_expr(node.get("value"))
            self._emit(owner + "[__pytra_idx(" + index_expr + ", length(" + owner + "))] = " + value)
            return
        if isinstance(target, dict) and _str(target, "kind") in {"Tuple", "List"}:
            self._emit_assign_target(target, self._render_expr(node.get("value")))
            return
        self._emit(_ident(_str(target, "id")) + " = " + self._render_expr(node.get("value")))

    def _emit_augassign_stmt(self, node: dict[str, JsonVal]) -> None:
        target_node = node.get("target")
        op = _str(node, "op")
        value = self._render_expr(node.get("value"))
        if isinstance(target_node, dict) and _str(target_node, "kind") == "Attribute":
            owner = self._render_expr(target_node.get("value"))
            attr = _str(target_node, "attr")
            lhs = owner + "." + attr
            self._emit(lhs + " = (" + lhs + " " + _BINOP_TEXT[op] + " " + value + ")")
            return
        target = _ident(_str(target_node, "id"))
        if op == "Add" and isinstance(target_node, dict) and _str(target_node, "resolved_type") == "str":
            self._emit(target + " = (" + target + " * " + value + ")")
            return
        self._emit(target + " = (" + target + " " + _BINOP_TEXT[op] + " " + value + ")")

    def _emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        value = node.get("value")
        if isinstance(value, dict) and _str(value, "kind") == "Constant" and isinstance(value.get("value"), str):
            return
        if isinstance(value, dict) and _str(value, "kind") == "Name":
            value_id = _str(value, "id")
            if value_id == "raise":
                self._emit("rethrow()")
                return
            if value_id == "continue":
                self._emit("continue")
                return
            if value_id == "break":
                self._emit("break")
                return
        self._emit(self._render_expr(value))

    def _emit_annassign_stmt(self, node: dict[str, JsonVal]) -> None:
        target = node.get("target")
        value = node.get("value")
        if isinstance(target, dict) and _str(target, "kind") == "Attribute":
            owner = self._render_expr(target.get("value"))
            attr = _str(target, "attr")
            if value is None:
                self._emit(owner + "." + attr + " = nothing")
            else:
                self._emit(owner + "." + attr + " = " + self._render_expr(value))
            return
        target_name = _ident(_str(target, "id"))
        if value is None:
            self._emit(target_name + " = nothing")
        else:
            self._emit(target_name + " = " + self._render_expr(value))

    def _emit_if_stmt(self, node: dict[str, JsonVal]) -> None:
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

    def _emit_while_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit("while __pytra_truthy(" + self._render_expr(node.get("test")) + ")")
        self.indent_level += 1
        for stmt in _list(node, "body"):
            self._emit_stmt(stmt)
        self.indent_level -= 1
        self._emit("end")

    def _emit_for_stmt(self, node: dict[str, JsonVal]) -> None:
        self._emit(self._render_for_header(node))
        self.indent_level += 1
        for stmt in _list(node, "body"):
            self._emit_stmt(stmt)
        self.indent_level -= 1
        self._emit("end")

    def _emit_function_stmt(self, node: dict[str, JsonVal]) -> None:
        name = _ident(_str(node, "name"))
        args = [_ident(arg) for arg in _list(node, "arg_order") if isinstance(arg, str)]
        vararg_name = node.get("vararg_name")
        if isinstance(vararg_name, str) and vararg_name != "":
            args.append(_ident(vararg_name))
        self._emit("function " + name + "(" + ", ".join(args) + ")")
        self.indent_level += 1
        for stmt in _list(node, "body"):
            self._emit_stmt(stmt)
        self.indent_level -= 1
        self._emit("end")

    def _emit_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        exc = node.get("exc")
        if exc is None:
            self._emit("rethrow()")
        else:
            self._emit("throw(" + self._render_expr(exc) + ")")

    def _emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        value = node.get("value")
        if value is None:
            self._emit("return nothing")
        else:
            self._emit("return " + self._render_expr(value))

    def _emit_class_stmt(self, node: dict[str, JsonVal]) -> None:
        if _exception_class_supported(node):
            self._emit_exception_class(node)
        else:
            self._emit_class(node)

    def _emit_try_handlers(self, handlers: list[JsonVal], err_name: str) -> None:
        self._emit("catch " + err_name)
        self.indent_level += 1
        for index, handler in enumerate(handlers):
            if not isinstance(handler, dict):
                continue
            type_node = handler.get("type")
            type_name = self._render_expr(type_node) if isinstance(type_node, dict) else ""
            mapped_type_name = self.mapping.predicate_types.get(type_name, "")
            if mapped_type_name != "":
                type_name = mapped_type_name
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

    def _emit_try_finally(self, finalbody: list[JsonVal]) -> None:
        self._emit("finally")
        self.indent_level += 1
        for stmt in finalbody:
            self._emit_stmt(stmt)
        self.indent_level -= 1

    def _emit_class_ctor(self, node: dict[str, JsonVal], class_name: str, impl_name: str, field_names: list[str]) -> None:
        init_fn: dict[str, JsonVal] | None = None
        for stmt in _list(node, "body"):
            if isinstance(stmt, dict) and _is_init_function(stmt):
                init_fn = stmt
                break
        ctor_args = []
        if init_fn is not None:
            ctor_args = [_ident(arg) for arg in _function_arg_order(init_fn)[1:]]
        self._emit("function __pytra_new_" + class_name + "(" + ", ".join(ctor_args) + ")")
        self.indent_level += 1
        ctor_init_args = ", ".join("nothing" for _ in field_names)
        self._emit("self = " + impl_name + "(" + ctor_init_args + ")")
        if init_fn is not None:
            prev_class_name = self.current_class_name
            self.current_class_name = class_name
            for stmt in _list(init_fn, "body"):
                self._emit_stmt(stmt)
            self.current_class_name = prev_class_name
        self._emit("return self")
        self.indent_level -= 1
        self._emit("end")

    def _emit_class_methods(self, node: dict[str, JsonVal], class_name: str) -> None:
        for stmt in _list(node, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") != "FunctionDef" or _is_init_function(stmt):
                continue
            self._emit_blank()
            fn_name = _ident(_str(stmt, "name"))
            impl_fn_name = self._method_impl_name(class_name, fn_name)
            is_static = _is_static_method(stmt)
            arg_order = _function_arg_order(stmt)
            args = []
            for index, arg in enumerate(arg_order):
                if not is_static and index == 0:
                    args.append("self::" + class_name)
                else:
                    args.append(_ident(arg))
            if is_static:
                self._emit("function " + fn_name + "(" + ", ".join(args) + ")")
            else:
                self._emit("function " + impl_fn_name + "(" + ", ".join(args) + ")")
            self.indent_level += 1
            prev_class_name = self.current_class_name
            self.current_class_name = class_name
            for inner in _list(stmt, "body"):
                self._emit_stmt(inner)
            self.current_class_name = prev_class_name
            self.indent_level -= 1
            self._emit("end")
            if not is_static:
                self._emit("function " + fn_name + "(" + ", ".join(args) + ")")
                self.indent_level += 1
                call_args = [_ident(arg) for arg in arg_order]
                self._emit("return " + impl_fn_name + "(" + ", ".join(call_args) + ")")
                self.indent_level -= 1
                self._emit("end")

    def _emit_simple_stmt(self, node: dict[str, JsonVal], kind: str) -> bool:
        if kind == "Import":
            self._emit_import_stmt(node)
            return True
        if kind == "ImportFrom":
            self._emit_import_from_stmt(node)
            return True
        if kind == "Pass":
            self._emit("nothing")
            return True
        if kind == "VarDecl":
            self._emit(_ident(_str(node, "name")) + " = nothing")
            return True
        if kind == "Raise":
            self._emit_raise_stmt(node)
            return True
        if kind == "Return":
            self._emit_return_stmt(node)
            return True
        if kind == "Expr":
            self._emit_expr_stmt(node)
            return True
        if kind == "AnnAssign":
            self._emit_annassign_stmt(node)
            return True
        if kind == "Assign":
            self._emit_assign_stmt(node)
            return True
        if kind == "Swap":
            left = _ident(_str(node.get("left"), "id"))
            right = _ident(_str(node.get("right"), "id"))
            self._emit(left + ", " + right + " = " + right + ", " + left)
            return True
        if kind == "AugAssign":
            self._emit_augassign_stmt(node)
            return True
        if kind == "TypeAlias":
            return True
        return False

    def _emit_stmt(self, node: JsonVal) -> None:
        if not isinstance(node, dict):
            raise RuntimeError("julia subset: stmt must be dict")
        kind = _str(node, "kind")
        if self._emit_simple_stmt(node, kind):
            return
        if kind == "If":
            self._emit_if_stmt(node)
            return
        if kind == "While":
            self._emit_while_stmt(node)
            return
        if kind == "Try":
            self._emit_try(node)
            return
        if kind == "ForCore":
            self._emit_for_stmt(node)
            return
        if kind == "FunctionDef":
            self._emit_function_stmt(node)
            return
        if kind == "ClassDef":
            self._emit_class_stmt(node)
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
            self._emit_try_handlers(handlers, "__pytra_err")
        if len(finalbody) > 0:
            self._emit_try_finally(finalbody)
        self._emit("end")

    def _emit_class(self, node: dict[str, JsonVal]) -> None:
        class_name = _str(node, "name")
        base_name = _str(node, "base")
        if _is_enum_base_name(base_name):
            return
        field_names = self._collect_field_names(class_name)
        impl_name = self._class_impl_name(class_name)
        if self._uses_abstract_backing(class_name):
            if base_name != "":
                self._emit("abstract type " + class_name + " <: " + base_name + " end")
            else:
                self._emit("abstract type " + class_name + " end")
            self._emit("mutable struct " + impl_name + " <: " + class_name)
        elif base_name != "":
            self._emit("mutable struct " + class_name + " <: " + base_name)
        else:
            self._emit("mutable struct " + class_name)
        self.indent_level += 1
        for field_name in field_names:
            self._emit(field_name)
        self.indent_level -= 1
        self._emit("end")
        self._emit_blank()
        self._emit_class_ctor(node, class_name, impl_name, field_names)
        self._emit_class_methods(node, class_name)

    def _emit_exception_ctor_body(self, init_fn: dict[str, JsonVal]) -> None:
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

    def _emit_exception_class(self, node: dict[str, JsonVal]) -> None:
        class_name = _str(node, "name")
        base_name = _str(node, "base")
        base_type = self._resolve_exception_base_type(base_name)
        if base_type == "":
            raise ValueError("unsupported Julia exception base: " + base_name)
        field_types = node.get("field_types")
        field_names = list(field_types.keys()) if isinstance(field_types, dict) else []
        self._emit("# inherits from " + base_name)
        self._emit("mutable struct " + class_name + " <: " + base_type)
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
            stmt for stmt in _list(node, "body") if isinstance(stmt, dict) and _is_init_function(stmt)
        )
        init_args = _function_arg_order(init_fn)
        args = init_args[1:] if len(init_args) > 0 else []
        self._emit("function __pytra_new_" + class_name + "(" + ", ".join(args) + ")")
        self.indent_level += 1
        ctor_args = ['""'] + ["nothing" for _ in field_names]
        self._emit("self = " + class_name + "(" + ", ".join(ctor_args) + ")")
        self._emit_exception_ctor_body(init_fn)
        self._emit("return self")
        self.indent_level -= 1
        self._emit("end")

    def _collect_class_member_sets(self, node: dict[str, JsonVal]) -> tuple[set[str], set[str], set[str]]:
        methods: set[str] = set()
        properties: set[str] = set()
        static_methods: set[str] = set()
        for item in _list(node, "body"):
            if not isinstance(item, dict) or _str(item, "kind") != "FunctionDef":
                continue
            name = _str(item, "name")
            if _is_init_function(item):
                continue
            if _is_static_method(item):
                static_methods.add(name)
            elif _is_property_method(item):
                properties.add(name)
            else:
                methods.add(name)
        return methods, properties, static_methods

    def _populate_class_metadata(self, east3_doc: dict[str, JsonVal]) -> None:
        for stmt in _list(east3_doc, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") != "ClassDef":
                continue
            class_name = _str(stmt, "name")
            base_name = _str(stmt, "base")
            self.class_base_names[class_name] = base_name
            if base_name != "":
                self.class_subclasses.setdefault(base_name, set()).add(class_name)
            field_types = stmt.get("field_types")
            self.class_direct_field_names[class_name] = list(field_types.keys()) if isinstance(field_types, dict) else []
            methods, properties, static_methods = self._collect_class_member_sets(stmt)
            inherited_methods = set(methods)
            inherited_properties = set(properties)
            walk_base = base_name
            while walk_base != "":
                inherited_methods |= self.class_method_names.get(walk_base, set())
                inherited_properties |= self.class_property_names.get(walk_base, set())
                walk_base = self.class_base_names.get(walk_base, "")
            self.class_method_names[class_name] = inherited_methods
            self.class_property_names[class_name] = inherited_properties
            self.class_static_method_names[class_name] = static_methods

    def _emit_module_prelude(self) -> None:
        self._emit('include(joinpath(@__DIR__, "built_in", "py_runtime.jl"))')
        self.emitted_native_files.add("built_in/py_runtime.jl")
        self._emit_blank()

    def _emit_module_body(self, east3_doc: dict[str, JsonVal]) -> None:
        for stmt in _list(east3_doc, "body"):
            self._emit_stmt(stmt)
            if _str(stmt, "kind") == "FunctionDef":
                self._emit_blank()

    def _emit_main_guard_body(self, east3_doc: dict[str, JsonVal]) -> None:
        for stmt in _list(east3_doc, "main_guard_body"):
            self._emit_stmt(stmt)

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        self.lines = []
        self.indent_level = 0
        self.tmp_counter = 0
        meta = east3_doc.get("meta")
        self.meta = meta if isinstance(meta, dict) else {}
        self.import_alias_modules = build_import_alias_map(self.meta)
        self.runtime_imports = build_runtime_import_map(self.meta, self.mapping)
        self.emitted_native_files = set()
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
        self.class_base_names = {}
        self.class_subclasses = {}
        self.class_direct_field_names = {}
        self.class_all_field_names = {}
        self.class_method_names = {}
        self.class_property_names = {}
        self.class_static_method_names = {}
        self.current_class_name = ""
        self._populate_class_metadata(east3_doc)
        self.exception_class_names = {
            _str(stmt, "name")
            for stmt in _list(east3_doc, "body")
            if isinstance(stmt, dict) and _str(stmt, "kind") == "ClassDef" and _exception_class_supported(stmt)
        }
        self._emit_module_prelude()
        self._emit_module_body(east3_doc)
        if len(_list(east3_doc, "main_guard_body")) > 0:
            self._emit_main_guard_body(east3_doc)
        return "\n".join(self.lines).rstrip() + "\n"

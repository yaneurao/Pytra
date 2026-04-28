"""Small toolchain2-native Julia subset renderer.

This module intentionally supports only a narrow AST subset so the Julia
backend can start migrating off the legacy emitter incrementally.
Unsupported modules must fall back to the legacy bridge.
"""

from __future__ import annotations

from typing import Callable

from pytra.std.json import JsonVal

from toolchain.emit.common.code_emitter import RuntimeMapping
from toolchain.emit.common.code_emitter import build_import_alias_map
from toolchain.emit.common.code_emitter import build_runtime_import_map
from toolchain.emit.common.code_emitter import should_skip_module


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


def _json_str(value: JsonVal) -> str:
    if isinstance(value, str):
        text: str = value
        return text
    return ""


def _json_is_str(value: JsonVal) -> bool:
    return isinstance(value, str)


def _bool(node: dict[str, JsonVal], key: str) -> bool:
    value = node.get(key)
    if isinstance(value, bool):
        flag: bool = value
        return flag
    return False


def _list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    value = node.get(key)
    if isinstance(value, list):
        return value
    return []


def _quote_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _render_keyword_suffix(render_value: Callable[[JsonVal], str], keywords: list[dict[str, JsonVal]]) -> str:
    if len(keywords) == 0:
        return ""
    parts: list[str] = []
    for item in keywords:
        arg = _str(item, "arg")
        if arg == "":
            continue
        parts.append(arg + "=" + render_value(item.get("value")))
    if len(parts) == 0:
        return ""
    return "; " + ", ".join(parts)


def _function_arg_order(node: dict[str, JsonVal]) -> list[str]:
    out: list[str] = []
    for arg in _list(node, "arg_order"):
        if isinstance(arg, str):
            out.append(arg)
    return out


def _function_decorators(node: dict[str, JsonVal]) -> set[str]:
    out: set[str] = set()
    for value in _list(node, "decorators"):
        if isinstance(value, str):
            out.add(value)
    return out


def _has_decorator(node: dict[str, JsonVal], name: str) -> bool:
    for value in _list(node, "decorators"):
        if _json_str(value) == name:
            return True
    return False


def _is_init_function(node: dict[str, JsonVal]) -> bool:
    return _str(node, "kind") == "FunctionDef" and _str(node, "name") == "__init__"


def _is_static_method(node: dict[str, JsonVal]) -> bool:
    return _has_decorator(node, "staticmethod")


def _is_property_method(node: dict[str, JsonVal]) -> bool:
    return _has_decorator(node, "property")


def _find_init_function(node: dict[str, JsonVal]) -> dict[str, JsonVal] | None:
    for stmt in _list(node, "body"):
        if isinstance(stmt, dict) and _is_init_function(stmt):
            return stmt
    return None


def _ctor_arg_order(node: dict[str, JsonVal]) -> list[str]:
    init_fn = _find_init_function(node)
    if init_fn is None:
        return []
    args = _function_arg_order(init_fn)
    out: list[str] = []
    index = 1
    while index < len(args):
        out.append(args[index])
        index += 1
    return out


def _dataclass_ctor_fields(node: dict[str, JsonVal]) -> list[tuple[str, bool, JsonVal]]:
    fields: list[tuple[str, bool, JsonVal]] = []
    for stmt in _list(node, "body"):
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "AnnAssign":
            continue
        target = stmt.get("target")
        if not isinstance(target, dict) or _str(target, "kind") != "Name":
            continue
        name = _str(target, "id")
        if name == "":
            continue
        value = stmt.get("value")
        if isinstance(value, dict):
            fields.append((name, True, value))
        else:
            fields.append((name, False, JsonVal()))
    return fields


def _class_member_bucket(node: dict[str, JsonVal]) -> str:
    if _is_init_function(node):
        return "init"
    if _is_static_method(node):
        return "static"
    if _is_property_method(node):
        return "property"
    return "method"


def _method_call_args(arg_order: list[str]) -> list[str]:
    out: list[str] = []
    for arg in arg_order:
        out.append(_ident(arg))
    return out


def _set_contains_str(items: set[str], value: str) -> bool:
    for item in items:
        if item == value:
            return True
    return False


def _is_init_name(name: str) -> bool:
    return name == "__init__"


def _is_enum_base_name(base_name: str) -> bool:
    return base_name in {"Enum", "IntEnum", "IntFlag"}


def _exception_ctor_message_expr(node: dict[str, JsonVal]) -> JsonVal | None:
    if _str(node, "kind") != "Expr":
        return None
    value = node.get("value")
    if not isinstance(value, dict) or _str(value, "kind") != "Call":
        return None
    args = _list(value, "args")
    if len(args) != 1:
        return None
    return args[0]


def _declared_field_names(node: dict[str, JsonVal]) -> list[str]:
    field_types = node.get("field_types")
    if not isinstance(field_types, dict):
        return []
    out: list[str] = []
    for name in field_types.keys():
        out.append(name)
    return out


def _all_expr_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not _expr_supported(item):
            return False
    return True


def _all_stmt_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not _stmt_supported(item):
            return False
    return True


def _all_handlers_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not _except_handler_supported(item):
            return False
    return True


def _all_assign_targets_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not _assign_target_supported(item):
            return False
    return True


def _all_method_body_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not _method_body_supported(item):
            return False
    return True


def _all_named_imports_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not isinstance(item, dict) or _str(item, "name") == "":
            return False
    return True


def _all_name_nodes(items: list[JsonVal]) -> bool:
    for item in items:
        if not isinstance(item, dict) or _str(item, "kind") != "Name":
            return False
    return True


def _all_lambda_args_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not isinstance(item, dict) or _str(item, "arg") == "":
            return False
    return True


def _all_dict_entries_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not isinstance(item, dict):
            return False
        if not _expr_supported(item.get("key")) or not _expr_supported(item.get("value")):
            return False
    return True


def _all_keywords_supported(items: list[JsonVal]) -> bool:
    for item in items:
        if not isinstance(item, dict):
            return False
        if _str(item, "arg") == "":
            return False
        if not _expr_supported(item.get("value")):
            return False
    return True


def _pass_only_class_body(body: list[JsonVal]) -> bool:
    return len(body) == 1 and isinstance(body[0], dict) and _str(body[0], "kind") == "Pass"


def _method_body_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "FunctionDef":
        return False
    return _all_stmt_supported(_list(node, "body"))


def _exception_ctor_stmt_supported(stmt: dict[str, JsonVal], instance_arg: str) -> bool:
    kind = _str(stmt, "kind")
    if kind == "Expr":
        value = stmt.get("value")
        if not isinstance(value, dict) or _str(value, "kind") != "Call":
            return False
        return _all_expr_supported(_list(value, "args"))
    if kind not in {"Assign", "AnnAssign"}:
        return False
    target = stmt.get("target")
    if not isinstance(target, dict) or _str(target, "kind") != "Attribute":
        return False
    owner = target.get("value")
    if not isinstance(owner, dict) or _str(owner, "kind") != "Name" or _str(owner, "id") != instance_arg:
        return False
    return _expr_supported(stmt.get("value"))


def _simple_class_supported(node: dict[str, JsonVal]) -> bool:
    body = _list(node, "body")
    if len(body) == 0:
        return True
    if _pass_only_class_body(body):
        return True
    return _all_method_body_supported(body)


def _exception_class_supported(node: dict[str, JsonVal]) -> bool:
    base_name = _str(node, "base")
    if base_name == "":
        return False
    body = _list(node, "body")
    init_seen = False
    init_fn: dict[str, JsonVal] = {}
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
            if init_seen:
                return False
            init_seen = True
            init_fn = stmt
            continue
        return False
    if not init_seen:
        return False
    args = _function_arg_order(init_fn)
    if len(args) < 2:
        return False
    instance_arg = args[0]
    for stmt in _list(init_fn, "body"):
        if not isinstance(stmt, dict) or not _exception_ctor_stmt_supported(stmt, instance_arg):
            return False
    return True


def _except_handler_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict) or _str(node, "kind") != "ExceptHandler":
        return False
    type_node = node.get("type")
    if type_node is not None and (not isinstance(type_node, dict) or _str(type_node, "kind") != "Name"):
        return False
    return _all_stmt_supported(_list(node, "body"))


def _importfrom_supported(module_name: str, names: list[JsonVal]) -> bool:
    _ = module_name
    return _all_named_imports_supported(names)


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
        return len(elements) > 0 and _all_assign_targets_supported(elements)
    return False


def _ident(name: str) -> str:
    if name in _JULIA_RESERVED_NAMES:
        return name + "_py"
    return name


def _owner_type_runtime_prefix(owner_type: str) -> str:
    if owner_type.startswith("list["):
        return "list"
    if owner_type.startswith("dict[") or "dict[" in owner_type:
        return "dict"
    if owner_type.startswith("set["):
        return "set"
    if owner_type.startswith("tuple["):
        return "tuple"
    return owner_type


def _is_io_owner_type(owner_type: str) -> bool:
    return owner_type in {"IOBase", "TextIOWrapper", "BufferedWriter", "BufferedReader"}


def _import_supported(names: list[JsonVal]) -> bool:
    return _all_named_imports_supported(names)


def _comp_generator_supported(node: dict[str, JsonVal]) -> bool:
    target = node.get("target")
    if not isinstance(target, dict):
        return False
    target_kind = _str(target, "kind")
    if target_kind == "Name":
        pass
    elif target_kind in {"Tuple", "List"}:
        elements = _list(target, "elements")
        if len(elements) == 0 or not _all_name_nodes(elements):
            return False
    else:
        return False
    return _expr_supported(node.get("iter")) and _all_expr_supported(_list(node, "ifs"))


def _isinstance_expected_name(node: dict[str, JsonVal]) -> str:
    expected_any = node.get("expected_type_id")
    if isinstance(expected_any, dict) and _str(expected_any, "kind") == "Name":
        expected_id = _str(expected_any, "id")
        if expected_id != "":
            return expected_id
    expected_name = node.get("expected_type_name")
    if isinstance(expected_name, str):
        return expected_name
    return ""


def _isinstance_expected_names(node: dict[str, JsonVal]) -> list[str]:
    expected_any = node.get("expected_type_id")
    if isinstance(expected_any, dict) and _str(expected_any, "kind") == "Tuple":
        out: list[str] = []
        for element in _list(expected_any, "elements"):
            if not isinstance(element, dict):
                continue
            item_name = _str(element, "type_object_of")
            if item_name == "":
                item_name = _str(element, "id")
            if item_name != "":
                out.append(item_name)
        return out
    name = _isinstance_expected_name(node)
    return [name] if name != "" else []


def _call_keywords_supported(keywords: list[JsonVal]) -> bool:
    return _all_keywords_supported(keywords)


def _attribute_call_supported(node: dict[str, JsonVal], func: dict[str, JsonVal], keywords: list[JsonVal]) -> bool:
    owner = func.get("value")
    runtime_call = _str(node, "resolved_runtime_call")
    if runtime_call == "":
        runtime_call = _str(node, "runtime_call")
    owner_type = _str(owner, "resolved_type") if isinstance(owner, dict) else ""
    if runtime_call == "" and _str(func, "attr") in {"items", "keys", "values", "get"} and "dict[" in owner_type:
        runtime_call = "dict." + _str(func, "attr")
    if not _expr_supported(owner):
        return False
    if not _all_expr_supported(_list(node, "args")):
        return False
    if not _call_keywords_supported(keywords):
        return False
    return runtime_call != "" or len(keywords) == 0


def _expr_supported(node: JsonVal) -> bool:
    if not isinstance(node, dict):
        return False
    kind = _str(node, "kind")
    if kind in {"Name", "Constant"}:
        return True
    if kind == "FormattedValue":
        return _expr_supported(node.get("value"))
    if kind == "JoinedStr":
        return _all_expr_supported(_list(node, "values"))
    if kind == "ObjStr":
        return _expr_supported(node.get("value"))
    if kind == "Attribute":
        return _expr_supported(node.get("value"))
    if kind == "List":
        return _all_expr_supported(_list(node, "elements"))
    if kind == "Tuple":
        return _all_expr_supported(_list(node, "elements"))
    if kind == "Dict":
        return _all_dict_entries_supported(_list(node, "entries"))
    if kind == "Set":
        return _all_expr_supported(_list(node, "elements"))
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
        return _str(node, "op") in {"And", "Or"} and _all_expr_supported(_list(node, "values"))
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
        return _all_lambda_args_supported(args) and _expr_supported(node.get("body"))
    if kind == "Call":
        func = node.get("func")
        keywords = _list(node, "keywords")
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            return _attribute_call_supported(node, func, keywords)
        return (
            _expr_supported(node.get("func"))
            and _all_expr_supported(_list(node, "args"))
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
        return _expr_supported(node.get("test")) and _all_stmt_supported(_list(node, "body")) and _all_stmt_supported(_list(node, "orelse"))
    if kind == "While":
        return _expr_supported(node.get("test")) and _all_stmt_supported(_list(node, "body")) and _all_stmt_supported(_list(node, "orelse"))
    if kind == "Try":
        return (
            _all_stmt_supported(_list(node, "body"))
            and _all_handlers_supported(_list(node, "handlers"))
            and len(_list(node, "orelse")) == 0
            and _all_stmt_supported(_list(node, "finalbody"))
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
                and _all_stmt_supported(_list(node, "body"))
                and _all_stmt_supported(_list(node, "orelse"))
            )
        if iter_kind == "RuntimeIterForPlan":
            return (
                _expr_supported(iter_plan.get("iter_expr"))
                and _all_stmt_supported(_list(node, "body"))
                and _all_stmt_supported(_list(node, "orelse"))
            )
        return False
    if kind == "FunctionDef":
        return _all_stmt_supported(_list(node, "body"))
    if kind == "TypeAlias":
        return True
    if kind == "ClassDef":
        return _simple_class_supported(node) or _exception_class_supported(node)
    return False


def can_render_module_natively(east3_doc: dict[str, JsonVal]) -> bool:
    body = _list(east3_doc, "body")
    main_guard_body = _list(east3_doc, "main_guard_body")
    exception_base_names: set[str] = set()
    for item in body:
        if isinstance(item, dict) and _str(item, "kind") == "ClassDef" and _exception_class_supported(item):
            exception_base_names.add(_str(item, "base"))
    for stmt in body:
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "ClassDef":
            continue
        if _str(stmt, "name") in exception_base_names and _str(stmt, "base") == "":
            return False
    return _all_stmt_supported(body) and _all_stmt_supported(main_guard_body)


class JuliaSubsetRenderer:
    lines: list[str]
    indent_level: int
    tmp_counter: int
    mapping: RuntimeMapping
    meta: dict[str, JsonVal]
    function_names: set[str]
    class_names: set[str]
    exception_class_names: set[str]
    class_base_names: dict[str, str]
    class_subclasses: dict[str, set[str]]
    class_direct_field_names: dict[str, list[str]]
    class_all_field_names: dict[str, list[str]]
    class_method_names: dict[str, set[str]]
    class_property_names: dict[str, set[str]]
    class_static_method_names: dict[str, set[str]]
    current_class_name: str
    local_names_stack: list[set[str]]
    import_alias_modules: dict[str, str]
    runtime_imports: dict[str, str]
    emitted_native_files: set[str]

    def __init__(self, mapping: RuntimeMapping | None = None, meta: dict[str, JsonVal] | None = None) -> None:
        self.lines: list[str] = []
        self.indent_level = 0
        self.tmp_counter = 0
        self.mapping = RuntimeMapping()
        if mapping is not None:
            self.mapping = mapping
        empty_meta: dict[str, JsonVal] = {}
        self.meta = empty_meta
        if meta is not None:
            self.meta = meta
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
        self.local_names_stack: list[set[str]] = []
        self.import_alias_modules: dict[str, str] = build_import_alias_map(self.meta)
        self.runtime_imports: dict[str, str] = build_runtime_import_map(self.meta, self.mapping)
        self.emitted_native_files: set[str] = set()

    def _base_name(self, class_name: str) -> str:
        return self.class_base_names.get(class_name, "")

    def _has_subclasses(self, class_name: str) -> bool:
        empty: set[str] = set()
        return len(self.class_subclasses.get(class_name, empty)) > 0

    def _uses_abstract_backing(self, class_name: str) -> bool:
        return self._base_name(class_name) != "" or self._has_subclasses(class_name)

    def _class_impl_name(self, class_name: str) -> str:
        if self._uses_abstract_backing(class_name):
            return "__pytra_cls_" + class_name
        return class_name

    def _method_impl_name(self, class_name: str, method_name: str) -> str:
        return "__pytra_method_" + class_name + "_" + method_name

    def _method_signature_args(self, class_name: str, stmt: dict[str, JsonVal]) -> tuple[bool, list[str], list[str]]:
        is_static = _is_static_method(stmt)
        arg_order = _function_arg_order(stmt)
        args: list[str] = []
        for index, arg in enumerate(arg_order):
            if not is_static and index == 0:
                args.append("self::" + class_name)
            else:
                args.append(_ident(arg))
        return is_static, arg_order, args

    def _resolve_exception_base_type(self, base_name: str) -> str:
        base_type = ""
        if base_name in self.mapping.predicate_types:
            base_type = self.mapping.predicate_types[base_name]
        if base_type == "" and _set_contains_str(self.exception_class_names, base_name):
            return base_name
        return base_type

    def _collect_field_names(self, class_name: str, visiting: set[str] | None = None) -> list[str]:
        if class_name in self.class_all_field_names:
            return list(self.class_all_field_names[class_name])
        if visiting is None:
            visiting = set()
        if class_name in visiting:
            return []
        next_visiting: set[str] = set()
        for name in visiting:
            next_visiting.add(name)
        next_visiting.add(class_name)
        out: list[str] = []
        base_name = self._base_name(class_name)
        if base_name != "":
            for field_name in self._collect_field_names(base_name, next_visiting):
                if field_name not in out:
                    out.append(field_name)
        for field_name in self.class_direct_field_names.get(class_name, []):
            if field_name not in out:
                out.append(field_name)
        self.class_all_field_names[class_name] = list(out)
        return out

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _current_local_names(self) -> set[str]:
        if len(self.local_names_stack) == 0:
            empty: set[str] = set()
            return empty
        return self.local_names_stack[-1]

    def _add_current_local_name(self, name: str) -> None:
        if len(self.local_names_stack) == 0:
            return
        self.local_names_stack[-1].add(name)

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
            parts: list[str] = []
            for part in native_file.split("/"):
                if part != "":
                    parts.append(part)
            if len(parts) == 0:
                continue
            quoted_parts: list[str] = []
            for part in parts:
                quoted_parts.append(_quote_string(part))
            join_parts = ', '.join(quoted_parts)
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
        mapped_runtime = ""
        if runtime_call in self.mapping.calls:
            mapped_runtime = self.mapping.calls[runtime_call]
        elif adapter_kind == "builtin" and runtime_call != "" and "." not in runtime_call:
            if self.mapping.builtin_prefix != "" and runtime_call.startswith(self.mapping.builtin_prefix):
                mapped_runtime = runtime_call
            else:
                mapped_runtime = self.mapping.builtin_prefix + runtime_call
        elif adapter_kind == "extern" and runtime_call != "" and "." not in runtime_call:
            mapped_runtime = runtime_call
        elif builtin_name != "" and builtin_name in self.mapping.calls:
            mapped_runtime = self.mapping.calls[builtin_name]
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
        keywords: list[dict[str, JsonVal]] = [],
    ) -> str:
        kw_suffix_parts: list[str] = []
        for item in keywords:
            arg = _str(item, "arg")
            if arg != "":
                kw_suffix_parts.append(arg + "=" + self._render_expr(item.get("value")))
        kw_suffix = ""
        if len(kw_suffix_parts) > 0:
            kw_suffix = "; " + ", ".join(kw_suffix_parts)
        if mapped == "":
            return ""
        if mapped == "__CAST__":
            return self._render_static_cast_call(builtin_name, result_type, args, source_type)
        if mapped == "__MAKEDIRS__":
            if len(args) == 1 and len(keywords) == 1 and _str(keywords[0], "arg") == "exist_ok":
                return "__OsNative.makedirs(" + args[0] + ", " + self._render_expr(keywords[0].get("value")) + ")"
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
        rendered_args = ", ".join(args)
        if len(args) == 0:
            return mapped + "(" + kw_suffix + ")"
        return mapped + "(" + rendered_args + kw_suffix + ")"

    def _render_scalar_runtime_call(self, mapped: str, args: list[str]) -> str:
        if mapped == "__INT__" and len(args) == 1:
            return "__pytra_int(" + args[0] + ")"
        if mapped == "__PY_IO_ENTER__" and len(args) == 1:
            return "__py_io_enter(" + args[0] + ")"
        if mapped == "__PY_IO_EXIT__" and len(args) == 4:
            return "__py_io_exit(" + ", ".join(args) + ")"
        if mapped == "__PYFILE_READ__":
            if len(args) == 1:
                return "read(" + args[0] + ", String)"
            if len(args) == 2:
                return "read(" + args[0] + ", " + args[1] + ")"
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
        if mapped == "__SET_UPDATE__" and len(args) == 2:
            return "union!(" + args[0] + ", " + args[1] + ")"
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
            return "__pytra_str_index(" + args[0] + ", " + args[1] + ")"
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
        if runtime_call == "":
            func_node = node.get("func")
            if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
                owner_node = func_node.get("value")
                attr = _str(func_node, "attr")
                owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
                runtime_prefix = _owner_type_runtime_prefix(owner_type)
                if runtime_prefix != "":
                    runtime_call = runtime_prefix + "." + attr
        mapped = self.mapping.calls.get(runtime_call, "")
        if mapped == "":
            return ""
        owner_node = node.get("func")
        source_type = ""
        keywords: list[dict[str, JsonVal]] = []
        for item in _list(node, "keywords"):
            if isinstance(item, dict):
                keywords.append(item)
        if isinstance(owner_node, dict) and _str(owner_node, "kind") == "Attribute":
            value_node = owner_node.get("value")
            if isinstance(value_node, dict):
                source_type = _str(value_node, "resolved_type")
        call_args: list[str] = []
        call_args.append(owner)
        for arg in args:
            call_args.append(arg)
        return self._render_mapped_runtime_call(
            mapped,
            call_args,
            _str(node, "resolved_type"),
            source_type=source_type,
            keywords=keywords,
        )

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
        target_type = ""
        if result_type in self.mapping.types:
            target_type = self.mapping.types[result_type]
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
            pieces: list[str] = []
            pieces.append("__pytra_base = __pytra_new_" + base_name + "(" + ", ".join(args) + ")")
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
        empty_set: set[str] = set()
        if _set_contains_str(self.class_static_method_names.get(owner_name, empty_set), attr):
            return _ident(attr) + "(" + ", ".join(args) + ")"
        if _set_contains_str(self.class_method_names.get(owner_type, empty_set), attr):
            call_args: list[str] = []
            call_args.append(owner)
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
        if _is_io_owner_type(owner_type):
            if attr == "__enter__" and len(args) == 0:
                return "__py_io_enter(" + owner + ")"
            if attr == "__exit__" and len(args) == 3:
                return "__py_io_exit(" + ", ".join([owner] + args) + ")"
            if attr == "read":
                if len(args) == 0:
                    return "read(" + owner + ", String)"
                if len(args) == 1:
                    return "read(" + owner + ", " + args[0] + ")"
            if attr == "write" and len(args) >= 1:
                return "write(" + ", ".join([owner] + args) + ")"
            if attr == "close" and len(args) == 0:
                return "close(" + owner + ")"
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
        if isinstance(owner_node, dict):
            owner_module_id = _str(owner_node, "runtime_module_id")
            runtime_symbol = _str(node, "runtime_symbol")
            if owner_module_id != "" and runtime_symbol != "":
                module_key = owner_module_id + "." + runtime_symbol
                mapped_runtime = self.mapping.calls.get(module_key, "")
                if mapped_runtime != "":
                    mapped_expr = self._render_mapped_runtime_call(
                        mapped_runtime,
                        args,
                        _str(node, "resolved_type"),
                        keywords=keywords,
                    )
                    if mapped_expr != "":
                        return mapped_expr
            if _str(owner_node, "resolved_type") == "module" or owner_module_id != "":
                rendered_args = ", ".join(args)
                if len(keywords) == 0:
                    return owner + "." + attr + "(" + rendered_args + ")"
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
        if _set_contains_str(self.exception_class_names, func):
            return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
        if _set_contains_str(self.class_names, func):
            return "__pytra_new_" + func + "(" + ", ".join(args) + ")"
        if func == "bytearray":
            if len(args) == 0:
                return "__pytra_bytearray()"
            if len(args) == 1:
                return "__pytra_bytearray(" + args[0] + ")"
        if func == "bytes":
            if len(args) == 0:
                return "__pytra_bytes()"
            if len(args) == 1:
                return "__pytra_bytes(" + args[0] + ")"
        return ""

    def _render_attribute_call_maybe(self, node: dict[str, JsonVal], func_node: JsonVal) -> str:
        if not isinstance(func_node, dict) or _str(func_node, "kind") != "Attribute":
            return ""
        owner_node = func_node.get("value")
        owner = self._render_expr(owner_node)
        owner_type = _str(owner_node, "resolved_type") if isinstance(owner_node, dict) else ""
        attr = _str(func_node, "attr")
        owner_name = _str(owner_node, "id") if isinstance(owner_node, dict) else ""
        args: list[str] = []
        for arg in _list(node, "args"):
            args.append(self._render_expr(arg))
        keywords: list[dict[str, JsonVal]] = []
        for item in _list(node, "keywords"):
            if isinstance(item, dict):
                keywords.append(item)
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
        checks: list[str] = []
        for expected_name in _isinstance_expected_names(node):
            mapped = ""
            if expected_name in self.mapping.predicate_types:
                mapped = self.mapping.predicate_types[expected_name]
            if mapped == "":
                if expected_name in self.mapping.types:
                    mapped = self.mapping.types[expected_name]
            if mapped != "":
                checks.append("(isa(" + value + ", " + mapped + "))")
            elif _set_contains_str(self.class_names, expected_name) or _set_contains_str(self.exception_class_names, expected_name):
                checks.append("(isa(" + value + ", " + expected_name + "))")
        if len(checks) > 0:
            return "(" + " || ".join(checks) + ")"
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
        has_dict_lane = owner_type.startswith("dict[")
        if not has_dict_lane:
            for part in owner_type.split("|"):
                if part.strip().startswith("dict["):
                    has_dict_lane = True
        if has_dict_lane:
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
            if _json_is_str(value):
                return _quote_string(_json_str(value))
            return str(value)
        if kind == "List":
            elems: list[str] = []
            for item in _list(node, "elements"):
                elems.append(self._render_expr(item))
            return "[" + ", ".join(elems) + "]"
        if kind == "Tuple":
            elems: list[str] = []
            for item in _list(node, "elements"):
                elems.append(self._render_expr(item))
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
            elems: list[str] = []
            for item in _list(node, "elements"):
                elems.append(self._render_expr(item))
            return "Set([" + ", ".join(elems) + "])"
        if kind == "ListComp":
            generator = _list(node, "generators")[0]
            if not isinstance(generator, dict):
                raise RuntimeError("julia subset: comprehension generator must be dict")
            elt = self._render_expr(node.get("elt"))
            loop_var = self._render_comp_target(generator.get("target"))
            iter_expr = self._render_comp_iter(generator.get("iter"))
            return "[" + elt + " for " + loop_var + " in " + iter_expr + self._render_comp_if_suffix(generator) + "]"
        if kind == "SetComp":
            generator = _list(node, "generators")[0]
            if not isinstance(generator, dict):
                raise RuntimeError("julia subset: comprehension generator must be dict")
            elt = self._render_expr(node.get("elt"))
            loop_var = self._render_comp_target(generator.get("target"))
            iter_expr = self._render_comp_iter(generator.get("iter"))
            return "Set([" + elt + " for " + loop_var + " in " + iter_expr + self._render_comp_if_suffix(generator) + "])"
        if kind == "DictComp":
            generator = _list(node, "generators")[0]
            if not isinstance(generator, dict):
                raise RuntimeError("julia subset: comprehension generator must be dict")
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
            args: list[str] = []
            for arg in _list(node, "args"):
                if isinstance(arg, dict):
                    name = _str(arg, "arg")
                    if name != "":
                        args.append(name)
            body = self._render_expr(node.get("body"))
            return "((" + ", ".join(args) + ") -> " + body + ")"
        return ""

    def _render_simple_expr(self, node: dict[str, JsonVal], kind: str) -> str:
        if kind == "Name":
            name = _str(node, "id")
            if name == "main" and _set_contains_str(self.function_names, "__pytra_main"):
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
                empty_static_methods: set[str] = set()
                if _set_contains_str(self.class_static_method_names.get(owner_name, empty_static_methods), attr):
                    return _ident(attr)
            empty_properties: set[str] = set()
            if _set_contains_str(self.class_property_names.get(owner_type, empty_properties), attr):
                return _ident(attr) + "(" + owner + ")"
            return owner + "." + attr
        if kind == "FormattedValue":
            format_spec = _str(node, "format_spec")
            if format_spec != "":
                return "__pytra_format(" + self._render_expr(node.get("value")) + ", " + _quote_string(format_spec) + ")"
            return "string(" + self._render_expr(node.get("value")) + ")"
        if kind == "JoinedStr":
            values = _list(node, "values")
            if len(values) == 0:
                return '""'
            parts: list[str] = []
            for item in values:
                parts.append(self._render_expr(item))
            expr = parts[0]
            index = 1
            while index < len(parts):
                part = parts[index]
                expr = "(" + expr + " * " + part + ")"
                index += 1
            return expr
        if kind == "ObjStr":
            return "string(" + self._render_expr(node.get("value")) + ")"
        return ""

    def _render_call_expr(self, node: dict[str, JsonVal]) -> str:
        func_node = node.get("func")
        attr_call = self._render_attribute_call_maybe(node, func_node)
        if attr_call != "":
            return attr_call
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Name" and _str(func_node, "id") == "isinstance":
            args0 = _list(node, "args")
            if len(args0) >= 2:
                return self._render_isinstance_expr({
                    "kind": "IsInstance",
                    "value": args0[0],
                    "expected_type_id": args0[1],
                })
        func = self._render_expr(func_node)
        args: list[str] = []
        for arg in _list(node, "args"):
            args.append(self._render_expr(arg))
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
        conditions: list[str] = []
        for item in _list(generator, "ifs"):
            conditions.append(self._render_expr(item))
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
        target_name = _ident(_str(target, "id"))
        self._add_current_local_name(target_name)
        self._emit(target_name + " = " + self._render_expr(node.get("value")))

    def _emit_multi_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        value_expr = self._render_expr(node.get("value"))
        tmp_name = self._next_tmp("__pytra_multi_")
        self._emit(tmp_name + " = " + value_expr)
        for index, target in enumerate(_list(node, "targets")):
            if not isinstance(target, dict):
                continue
            item_expr = tmp_name + "[__pytra_idx(" + str(index) + ", length(" + tmp_name + "))]"
            self._emit_assign_target(target, item_expr)

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
        self._add_current_local_name(target_name)
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
        args: list[str] = []
        for arg in _list(node, "arg_order"):
            arg_name = _json_str(arg)
            if arg_name != "":
                args.append(_ident(arg_name))
        vararg_name = _str(node, "vararg_name")
        if vararg_name != "":
            args.append(_ident(vararg_name) + "...")
        self._emit("function " + name + "(" + ", ".join(args) + ")")
        self.indent_level += 1
        self.local_names_stack.append(set(args))
        try:
            for stmt in _list(node, "body"):
                self._emit_stmt(stmt)
        finally:
            self.local_names_stack.pop()
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
            mapped_type_name = ""
            if type_name in self.mapping.predicate_types:
                mapped_type_name = self.mapping.predicate_types[type_name]
            if mapped_type_name != "":
                type_name = mapped_type_name
            if type_name == "PytraIndexError":
                cond = "(" + err_name + " isa PytraIndexError || " + err_name + " isa BoundsError)"
            else:
                cond = "true" if type_name == "" else err_name + " isa " + type_name
            if index == 0:
                self._emit("if " + cond)
            else:
                self._emit("elseif " + cond)
            self.indent_level += 1
            bound_name = _str(handler, "name")
            if bound_name != "":
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

    def _emit_stmt_block(self, body: list[JsonVal]) -> None:
        for stmt in body:
            self._emit_stmt(stmt)

    def _emit_class_scoped_block(self, class_name: str, body: list[JsonVal]) -> None:
        prev_class_name = self.current_class_name
        self.current_class_name = class_name
        try:
            self._emit_stmt_block(body)
        finally:
            self.current_class_name = prev_class_name

    def _emit_new_ctor_header(self, class_name: str, args: list[str]) -> None:
        self._emit("function __pytra_new_" + class_name + "(" + ", ".join(args) + ")")
        self.indent_level += 1

    def _emit_ctor_return_self(self) -> None:
        self._emit("return self")
        self.indent_level -= 1
        self._emit("end")

    def _emit_mutable_struct(self, struct_name: str, base_type: str, field_names: list[str]) -> None:
        header = "mutable struct " + struct_name
        if base_type != "":
            header += " <: " + base_type
        self._emit(header)
        self.indent_level += 1
        for field_name in field_names:
            self._emit(field_name)
        self.indent_level -= 1
        self._emit("end")

    def _emit_function_header(self, fn_name: str, args: list[str]) -> None:
        self._emit("function " + fn_name + "(" + ", ".join(args) + ")")
        self.indent_level += 1

    def _emit_function_end(self) -> None:
        self.indent_level -= 1
        self._emit("end")

    def _emit_method_impl(self, class_name: str, impl_fn_name: str, args: list[str], body: list[JsonVal]) -> None:
        self._emit_function_header(impl_fn_name, args)
        self._emit_class_scoped_block(class_name, body)
        self._emit_function_end()

    def _emit_method_wrapper(self, fn_name: str, impl_fn_name: str, args: list[str], arg_order: list[str]) -> None:
        self._emit_function_header(fn_name, args)
        call_args = _method_call_args(arg_order)
        self._emit("return " + impl_fn_name + "(" + ", ".join(call_args) + ")")
        self._emit_function_end()

    def _emit_class_ctor(self, node: dict[str, JsonVal], class_name: str, impl_name: str, field_names: list[str]) -> None:
        init_fn = _find_init_function(node)
        if init_fn is None and _bool(node, "dataclass"):
            dataclass_fields = _dataclass_ctor_fields(node)
            ctor_args: list[str] = []
            for field_name, has_default, default_value in dataclass_fields:
                if has_default:
                    ctor_args.append(_ident(field_name) + "=" + self._render_expr(default_value))
                else:
                    ctor_args.append(_ident(field_name))
            self._emit_new_ctor_header(class_name, ctor_args)
            ctor_init_parts: list[str] = []
            for _field_name in field_names:
                ctor_init_parts.append("nothing")
            ctor_init_args = ", ".join(ctor_init_parts)
            self._emit("self = " + impl_name + "(" + ctor_init_args + ")")
            for field_name, _has_default, _default_value in dataclass_fields:
                self._emit("self." + field_name + " = " + _ident(field_name))
            self._emit_ctor_return_self()
            return
        ctor_args: list[str] = []
        for arg in _ctor_arg_order(node):
            ctor_args.append(_ident(arg))
        self._emit_new_ctor_header(class_name, ctor_args)
        ctor_init_parts: list[str] = []
        for _field_name in field_names:
            ctor_init_parts.append("nothing")
        ctor_init_args = ", ".join(ctor_init_parts)
        self._emit("self = " + impl_name + "(" + ctor_init_args + ")")
        if init_fn is not None:
            self._emit_class_scoped_block(class_name, _list(init_fn, "body"))
        self._emit_ctor_return_self()

    def _emit_class_methods(self, node: dict[str, JsonVal], class_name: str) -> None:
        for stmt in _list(node, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") != "FunctionDef" or _is_init_function(stmt):
                continue
            self._emit_blank()
            fn_name = _ident(_str(stmt, "name"))
            impl_fn_name = self._method_impl_name(class_name, fn_name)
            is_static, arg_order, args = self._method_signature_args(class_name, stmt)
            if is_static:
                self._emit_function_header(fn_name, args)
                self._emit_class_scoped_block(class_name, _list(stmt, "body"))
                self._emit_function_end()
            else:
                self._emit_method_impl(class_name, impl_fn_name, args, _list(stmt, "body"))
                self._emit_method_wrapper(fn_name, impl_fn_name, args, arg_order)

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
            self._add_current_local_name(_str(node, "name"))
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
        if kind in {"MultiAssign", "TupleUnpack"}:
            self._emit_multi_assign_stmt(node)
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
        if kind == "With":
            self._emit_with(node)
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

    def _emit_with(self, node: dict[str, JsonVal]) -> None:
        body = _list(node, "body")
        empty_body: list[JsonVal] = []
        empty_handlers: list[JsonVal] = []
        hoisted = self._collect_try_hoisted_names_from_parts(body, empty_body, empty_handlers)
        current_locals = self._current_local_names()
        for name in hoisted:
            if name in current_locals:
                continue
            current_locals.add(name)
            self._emit(_ident(name) + " = nothing")

        ctx_name = self._next_tmp("__with_ctx_")
        var_name = _str(node, "var_name")
        if var_name == "":
            var_name = self._next_tmp("__with_value_")
        current_locals.add(var_name)
        context_expr = node.get("context_expr")
        self._emit(ctx_name + " = " + self._render_expr(context_expr))
        no_keywords: list[dict[str, JsonVal]] = []
        enter_args: list[str] = []
        enter_args.append(ctx_name)
        enter_runtime = _str(node, "with_enter_runtime_call")
        enter_mapped = self._resolve_subset_runtime_call(enter_runtime, "", "")
        enter_expr = ""
        if enter_mapped != "":
            enter_expr = self._render_mapped_runtime_call(enter_mapped, enter_args, _str(node, "with_enter_type"), keywords=no_keywords)
        if enter_expr == "":
            enter_expr = ctx_name + ".__enter__()"
        self._emit(var_name + " = " + enter_expr)
        self._emit("try")
        self.indent_level += 1
        for stmt in body:
            self._emit_stmt(stmt)
        self.indent_level -= 1
        self._emit("finally")
        self.indent_level += 1
        exit_args: list[str] = []
        exit_args.append(ctx_name)
        exit_args.append("nothing")
        exit_args.append("nothing")
        exit_args.append("nothing")
        exit_runtime = _str(node, "with_exit_runtime_call")
        exit_mapped = self._resolve_subset_runtime_call(exit_runtime, "", "")
        exit_expr = ""
        if exit_mapped != "":
            exit_expr = self._render_mapped_runtime_call(exit_mapped, exit_args, "None", keywords=no_keywords)
        if exit_expr == "":
            exit_expr = ctx_name + ".__exit__(nothing, nothing, nothing)"
        self._emit(exit_expr)
        self.indent_level -= 1
        self._emit("end")

    def _emit_try(self, node: dict[str, JsonVal]) -> None:
        handlers = _list(node, "handlers")
        finalbody = _list(node, "finalbody")
        hoisted = self._collect_try_hoisted_names(node)
        current_locals = self._current_local_names()
        for name in hoisted:
            if name in current_locals:
                continue
            current_locals.add(name)
            self._emit(_ident(name) + " = nothing")
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

    def _collect_try_hoisted_names(self, node: dict[str, JsonVal]) -> list[str]:
        return self._collect_try_hoisted_names_from_parts(_list(node, "body"), _list(node, "finalbody"), _list(node, "handlers"))

    def _collect_try_hoisted_names_from_parts(
        self,
        body: list[JsonVal],
        finalbody: list[JsonVal],
        handlers: list[JsonVal],
    ) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()

        def add_name(name: str) -> None:
            if name == "" or name in seen:
                return
            seen.add(name)
            out.append(name)

        def walk(stmts: list[JsonVal]) -> None:
            for stmt in stmts:
                if not isinstance(stmt, dict):
                    continue
                kind = _str(stmt, "kind")
                if kind == "AnnAssign":
                    target = stmt.get("target")
                    if isinstance(target, dict) and _str(target, "kind") == "Name":
                        add_name(_str(target, "id"))
                elif kind == "Assign":
                    target = stmt.get("target")
                    if not isinstance(target, dict):
                        targets = _list(stmt, "targets")
                        if len(targets) > 0 and isinstance(targets[0], dict):
                            target = targets[0]
                    if isinstance(target, dict) and _str(target, "kind") == "Name":
                        add_name(_str(target, "id"))
                elif kind in {"If", "While", "Try", "ForCore"}:
                    walk(_list(stmt, "body"))
                    walk(_list(stmt, "orelse"))
                    walk(_list(stmt, "finalbody"))
                    for handler in _list(stmt, "handlers"):
                        if isinstance(handler, dict):
                            walk(_list(handler, "body"))

        walk(body)
        walk(finalbody)
        for handler in handlers:
            if isinstance(handler, dict):
                walk(_list(handler, "body"))
        return out

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
            self._emit_mutable_struct(impl_name, class_name, field_names)
        elif base_name != "":
            self._emit_mutable_struct(class_name, base_name, field_names)
        else:
            self._emit_mutable_struct(class_name, "", field_names)
        self._emit_blank()
        self._emit_class_ctor(node, class_name, impl_name, field_names)
        self._emit_class_methods(node, class_name)

    def _emit_exception_ctor_body(self, init_fn: dict[str, JsonVal]) -> None:
        for stmt in _list(init_fn, "body"):
            if not isinstance(stmt, dict):
                continue
            message_expr = _exception_ctor_message_expr(stmt)
            if message_expr is not None:
                self._emit("self.__pytra_message = string(" + self._render_expr(message_expr) + ")")
                continue
            self._emit_exception_ctor_assign(stmt)

    def _emit_exception_ctor_assign(self, stmt: dict[str, JsonVal]) -> None:
        target = stmt.get("target")
        if isinstance(target, dict):
            self._emit("self." + _str(target, "attr") + " = " + self._render_expr(stmt.get("value")))

    def _emit_exception_display_methods(self, class_name: str) -> None:
        self._emit("Base.show(io::IO, e::" + class_name + ") = print(io, e.__pytra_message)")
        self._emit("Base.showerror(io::IO, e::" + class_name + ") = print(io, e.__pytra_message)")
        self._emit("__pytra_exception_message(e::" + class_name + ") = string(e.__pytra_message)")

    def _emit_exception_struct(self, class_name: str, base_type: str, field_names: list[str]) -> None:
        all_fields: list[str] = []
        all_fields.append("__pytra_message")
        for name in field_names:
            all_fields.append(name)
        self._emit_mutable_struct(class_name, base_type, all_fields)

    def _emit_exception_class(self, node: dict[str, JsonVal]) -> None:
        class_name = _str(node, "name")
        base_name = _str(node, "base")
        base_type = self._resolve_exception_base_type(base_name)
        if base_type == "":
            raise ValueError("unsupported Julia exception base: " + base_name)
        field_names = _declared_field_names(node)
        self._emit("# inherits from " + base_name)
        self._emit_exception_struct(class_name, base_type, field_names)
        self._emit_exception_display_methods(class_name)
        self._emit_blank()
        init_fn = _find_init_function(node)
        if init_fn is None:
            raise ValueError("julia subset: exception class missing __init__: " + class_name)
        args = _ctor_arg_order(node)
        self._emit_new_ctor_header(class_name, args)
        ctor_args: list[str] = []
        ctor_args.append('""')
        for _field_name in field_names:
            ctor_args.append("nothing")
        self._emit("self = " + class_name + "(" + ", ".join(ctor_args) + ")")
        self._emit_exception_ctor_body(init_fn)
        self._emit_ctor_return_self()

    def _collect_class_member_sets(self, node: dict[str, JsonVal]) -> tuple[set[str], set[str], set[str]]:
        methods: set[str] = set()
        properties: set[str] = set()
        static_methods: set[str] = set()
        for item in _list(node, "body"):
            if not isinstance(item, dict) or _str(item, "kind") != "FunctionDef":
                continue
            name = _str(item, "name")
            bucket = _class_member_bucket(item)
            if bucket == "init":
                continue
            if bucket == "static":
                static_methods.add(name)
            elif bucket == "property":
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
                if base_name not in self.class_subclasses:
                    empty_children: set[str] = set()
                    self.class_subclasses[base_name] = empty_children
                self.class_subclasses[base_name].add(class_name)
            self.class_direct_field_names[class_name] = _declared_field_names(stmt)
            methods, properties, static_methods = self._collect_class_member_sets(stmt)
            inherited_methods: set[str] = set()
            for method_name in methods:
                inherited_methods.add(method_name)
            inherited_properties: set[str] = set()
            for property_name in properties:
                inherited_properties.add(property_name)
            walk_base = base_name
            while walk_base != "":
                empty_methods: set[str] = set()
                for method_name in self.class_method_names.get(walk_base, empty_methods):
                    inherited_methods.add(method_name)
                empty_properties: set[str] = set()
                for property_name in self.class_property_names.get(walk_base, empty_properties):
                    inherited_properties.add(property_name)
                walk_base = self.class_base_names.get(walk_base, "")
            self.class_method_names[class_name] = inherited_methods
            self.class_property_names[class_name] = inherited_properties
            self.class_static_method_names[class_name] = static_methods

    def _collect_top_level_names(self, east3_doc: dict[str, JsonVal], kind: str, pred: Callable[[dict[str, JsonVal]], bool] | None = None) -> set[str]:
        names: set[str] = set()
        for stmt in _list(east3_doc, "body"):
            if not isinstance(stmt, dict) or _str(stmt, "kind") != kind:
                continue
            if pred is not None and not pred(stmt):
                continue
            name = _str(stmt, "name")
            if name != "":
                names.add(name)
        return names

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
        empty_meta: dict[str, JsonVal] = {}
        self.meta = empty_meta
        if isinstance(meta, dict):
            self.meta = meta
        self.import_alias_modules = build_import_alias_map(self.meta)
        self.runtime_imports = build_runtime_import_map(self.meta, self.mapping)
        self.emitted_native_files = set()
        self.function_names = self._collect_top_level_names(east3_doc, "FunctionDef")
        self.class_names = self._collect_top_level_names(east3_doc, "ClassDef")
        empty_base_names: dict[str, str] = {}
        self.class_base_names = empty_base_names
        empty_subclasses: dict[str, set[str]] = {}
        self.class_subclasses = empty_subclasses
        empty_direct_field_names: dict[str, list[str]] = {}
        self.class_direct_field_names = empty_direct_field_names
        empty_all_field_names: dict[str, list[str]] = {}
        self.class_all_field_names = empty_all_field_names
        empty_method_names: dict[str, set[str]] = {}
        self.class_method_names = empty_method_names
        empty_property_names: dict[str, set[str]] = {}
        self.class_property_names = empty_property_names
        empty_static_method_names: dict[str, set[str]] = {}
        self.class_static_method_names = empty_static_method_names
        self.current_class_name = ""
        self._populate_class_metadata(east3_doc)
        self.exception_class_names = self._collect_top_level_names(east3_doc, "ClassDef", _exception_class_supported)
        self._emit_module_prelude()
        self._emit_module_body(east3_doc)
        if len(_list(east3_doc, "main_guard_body")) > 0:
            self._emit_main_guard_body(east3_doc)
        return "\n".join(self.lines).rstrip() + "\n"

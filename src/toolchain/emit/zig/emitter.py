"""toolchain2 EAST3 -> Zig native emitter."""

from __future__ import annotations

import json
from typing import Any
from pathlib import Path

from pytra.std import json as pytra_json
from pytra.std.json import JsonVal
from toolchain.emit.common.code_emitter import RuntimeMapping
from toolchain.emit.common.code_emitter import build_import_alias_map
from toolchain.emit.common.code_emitter import load_runtime_mapping
from toolchain.emit.common.common_renderer import CommonRenderer


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
# Zig std built-in type/namespace names that user-defined identifiers should
# not shadow.  Names used by the Pytra runtime (print, math, etc.) are
# excluded since _safe_ident cannot distinguish user vs runtime references.
_ZIG_RESERVED_BUILTINS = {
    'std',
    'i8', 'i16', 'i32', 'i64', 'i128',
    'u8', 'u16', 'u32', 'u64', 'u128',
    'f16', 'f32', 'f64', 'f128',
    'usize', 'isize', 'bool',
    'void', 'anyerror',
    'allocator', 'ArrayList', 'HashMap',
    'mem', 'fmt', 'debug', 'heap', 'io', 'os', 'fs',
    'testing', 'log',
}
_NIL_FREE_DECL_TYPES = {"int", "int64", "float", "float64", "bool", "str"}
_COMPILETIME_STD_IMPORT_SYMBOLS = {"abi", "template", "extern"}
_ZIG_ACTIVE_EXCEPTION_SLOTS = ("__pytra_exc_type", "__pytra_exc_msg", "__pytra_exc_line")
_ZIG_CAUGHT_EXCEPTION_SLOTS = ("__pytra_caught_type", "__pytra_caught_msg", "__pytra_caught_line")
_ZIG_BOUND_EXCEPTION_RECORD = "__PytraError"
_RUNTIME_SYMBOL_INDEX_PATH = Path("tools").joinpath("runtime_symbol_index.json")
_RUNTIME_SYMBOL_INDEX_CACHE: dict[str, JsonVal] = {}
_RUNTIME_SYMBOL_INDEX_LOADED: bool = False


def _load_runtime_symbol_index() -> dict[str, JsonVal]:
    global _RUNTIME_SYMBOL_INDEX_CACHE
    global _RUNTIME_SYMBOL_INDEX_LOADED
    if _RUNTIME_SYMBOL_INDEX_LOADED:
        return _RUNTIME_SYMBOL_INDEX_CACHE
    _RUNTIME_SYMBOL_INDEX_LOADED = True
    if not _RUNTIME_SYMBOL_INDEX_PATH.exists():
        _RUNTIME_SYMBOL_INDEX_CACHE = {}
        return _RUNTIME_SYMBOL_INDEX_CACHE
    try:
        raw_obj = json.loads_obj(_RUNTIME_SYMBOL_INDEX_PATH.read_text())
        if raw_obj is not None:
            _RUNTIME_SYMBOL_INDEX_CACHE = raw_obj.raw
    except Exception:
        _RUNTIME_SYMBOL_INDEX_CACHE = {}
    return _RUNTIME_SYMBOL_INDEX_CACHE


def _runtime_module_doc(module_id: str) -> dict[str, JsonVal]:
    modules = _load_runtime_symbol_index().get("modules")
    if not isinstance(modules, dict):
        return {}
    doc = modules.get(module_id)
    return doc if isinstance(doc, dict) else {}


def _runtime_module_exists(module_id: str) -> bool:
    return len(_runtime_module_doc(module_id)) > 0


def _find_runtime_modules_by_leaf(module_id: str) -> list[str]:
    mod = module_id.strip()
    if mod == "":
        return []
    modules = _load_runtime_symbol_index().get("modules")
    if not isinstance(modules, dict):
        return []
    matches: list[str] = []
    for candidate_any in modules.keys():
        if not isinstance(candidate_any, str):
            continue
        candidate = candidate_any.strip()
        if candidate == "":
            continue
        parts = candidate.split(".")
        if len(parts) > 0 and parts[-1] == mod:
            matches.append(candidate)
    return matches


def canonical_runtime_module_id(module_id: str) -> str:
    mod = module_id.strip()
    if mod == "":
        return ""
    if _runtime_module_exists(mod):
        return mod
    if "." not in mod:
        matches = _find_runtime_modules_by_leaf(mod)
        if len(matches) == 1:
            return matches[0]
    return mod


def lookup_runtime_module_symbols(module_id: str) -> dict[str, JsonVal]:
    symbols = _runtime_module_doc(module_id).get("symbols")
    return symbols if isinstance(symbols, dict) else {}


def lookup_runtime_symbol_doc(module_id: str, symbol_name: str) -> dict[str, JsonVal]:
    mod = canonical_runtime_module_id(module_id.strip())
    if mod == "":
        return {}
    symbol = lookup_runtime_module_symbols(mod).get(symbol_name.strip())
    return symbol if isinstance(symbol, dict) else {}


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
    if out == "_":
        out = "_unused"
    if out in _ZIG_KEYWORDS:
        out = "@\"" + out + "\""
    while out in _ZIG_RESERVED_BUILTINS:
        out = out + "_"
    return out


def _starts_with_upper(text: str) -> bool:
    if len(text) == 0:
        return False
    first = text[0:1]
    return first >= "A" and first <= "Z"


def _relative_import_module_path(module_id: str) -> str:
    rel = module_id
    while rel.startswith("."):
        rel = rel[1:]
    parts = [
        _safe_ident(part, "module")
        for part in rel.split(".")
        if part != ""
    ]
    return ".".join(parts)


def _collect_relative_import_name_aliases(east_doc: dict[str, JsonVal]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
            continue
        sd: dict[str, JsonVal] = stmt
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
            local_name = name
            if isinstance(asname_any, str):
                asname_value: str = asname_any
                if asname_value != "":
                    local_name = asname_value
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    return aliases


def reject_backend_homogeneous_tuple_ellipsis_type_exprs(doc: object, *, backend_name: str) -> None:
    return None


def reject_backend_typed_vararg_signatures(doc: object, *, backend_name: str) -> None:
    return None


def _scan_reassigned_names(node: Any, param_names: set[str], out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _scan_reassigned_names(item, param_names, out)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind", "")
    if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
        target = node.get("target")
        if isinstance(target, dict):
            if target.get("kind") == "Name":
                name = target.get("id", "")
                if name in param_names:
                    out.add(name)
            elif target.get("kind") == "Tuple":
                elements = target.get("elements")
                if isinstance(elements, list):
                    for elem in elements:
                        if isinstance(elem, dict) and elem.get("kind") == "Name":
                            name = elem.get("id", "")
                            if name in param_names:
                                out.add(name)
    if kind == "ForCore":
        target_plan = node.get("target_plan")
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            name = target_plan.get("id", "")
            if name in param_names:
                out.add(name)
    body = node.get("body")
    if isinstance(body, list):
        _scan_reassigned_names(body, param_names, out)
    orelse = node.get("orelse")
    if isinstance(orelse, list):
        _scan_reassigned_names(orelse, param_names, out)


def _collect_reassigned_params(func_def: dict[str, Any]) -> set[str]:
    arg_order = func_def.get("arg_order")
    if not isinstance(arg_order, list) or len(arg_order) == 0:
        empty_params: set[str] = set()
        return empty_params
    param_names: set[str] = set()
    for arg in arg_order:
        if isinstance(arg, str):
            arg_name: str = arg
            if arg_name != "":
                param_names.add(arg_name)
    if len(param_names) == 0:
        empty_params = set()
        return empty_params
    reassigned: set[str] = set()
    _scan_reassigned_names(func_def.get("body"), param_names, reassigned)
    return reassigned


def _mutable_param_name(name: str) -> str:
    return name + "_"


def _zig_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\t", "\\t")
    out = out.replace("\r", "\\r")
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _binop_precedence(op: str) -> int:
    """Zig 演算子優先順位（高い値 = 高い優先度）。"""
    if op in {"Mult", "Div", "FloorDiv", "Mod"}:
        return 6
    if op in {"Add", "Sub"}:
        return 5
    if op in {"LShift", "RShift"}:
        return 4
    if op == "BitAnd":
        return 3
    if op == "BitXor":
        return 2
    if op == "BitOr":
        return 1
    if op == "Pow":
        return 7
    return 0


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


def _runtime_module_symbol_names(runtime_module_id: str) -> list[str]:
    symbols = lookup_runtime_module_symbols(runtime_module_id)
    names: list[str] = []
    for name in symbols.keys():
        if isinstance(name, str):
            names.append(name)
    return names


def _runtime_symbol_call_adapter_kind(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    adapter_kind = doc.get("call_adapter_kind")
    return adapter_kind if isinstance(adapter_kind, str) else ""


def _runtime_symbol_semantic_tag(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    semantic_tag = doc.get("semantic_tag")
    return semantic_tag if isinstance(semantic_tag, str) else ""


def _is_math_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    tag = _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol)
    return tag == 'math'


def _is_perf_counter_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return runtime_symbol == 'perf_counter' or runtime_symbol == 'perf_counter_ns'


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
    return "__pytra_" + runtime_symbol


class ZigNativeEmitter:
    def __init__(self, east_doc: dict[str, JsonVal], is_submodule: bool = False) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=zig invalid east document: root must be dict")
        ed: dict[str, JsonVal] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=zig invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=zig unsupported east_stage: " + str(ed.get("east_stage")))
        self.east_doc: dict[str, JsonVal] = east_doc
        self.is_submodule = is_submodule
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.imported_modules: set[str] = set()
        self.function_names: set[str] = set()
        self.relative_import_name_aliases: dict[str, str] = {}
        self.current_class_name: str = ""
        self.current_class_base_name: str = ""
        self._dataclass_names: set[str] = set()
        self._dataclass_fields: dict[str, list[str]] = {}
        self._classes_with_init: set[str] = set()
        self._classes_with_del: set[str] = set()
        self._classes_with_mut_method: set[str] = set()
        self._class_base: dict[str, str] = {}
        self._class_methods: dict[str, set[str]] = {}
        self._class_properties: dict[str, set[str]] = {}
        self._known_imported_nominals: set[str] = set()
        self._import_alias_map: dict[str, str] = {}
        self._type_aliases: dict[str, str] = {}
        self._class_init_defaults: dict[str, list[Any]] = {}
        self._class_init_default_types: dict[str, list[str]] = {}
        self._class_method_defaults: dict[str, dict[str, list[Any]]] = {}
        self._class_method_default_types: dict[str, dict[str, list[str]]] = {}
        self._class_method_arg_order: dict[str, dict[str, list[str]]] = {}
        self._class_field_types: dict[str, dict[str, str]] = {}
        self._static_fields: dict[str, list[list[str]]] = {}  # cls -> [[field, type, default]]
        self._vtable_root: dict[str, str] = {}  # cls -> vtable root class
        self._vtable_methods: dict[str, list[str]] = {}  # root cls -> [method names]
        self._class_return_types: dict[str, dict[str, str]] = {}  # cls -> {method: return_type}
        self._module_function_types: dict[str, str] = {}
        self._module_function_param_zig_types: dict[str, list[str]] = {}
        self._module_function_vararg_index: dict[str, int] = {}
        self._local_type_stack: list[dict[str, str]] = []
        self._storage_type_stack: list[dict[str, str]] = []
        self._ref_var_stack: list[set[str]] = []
        self._local_var_stack: list[set[str]] = []
        self._decl_line_stack: list[dict[str, int]] = []
        self._reassigned_name_stack: list[set[str]] = []
        self._mutated_var_stack: list[set[str]] = []
        self._hoisted_var_names: set[str] = set()
        # タプル型の名前付き typedef: normalized_type → zig_name
        self._tuple_typedefs: dict[str, str] = {}
        self._tuple_typedef_seq: int = 0
        # Class context for parameter shadowing detection
        self._current_class_name: str = ""
        self._current_class_methods: list[dict[str, Any]] = []
        # Parameter rename stack: original_name → zig_name (for shadowing avoidance)
        self._param_rename_stack: list[dict[str, str]] = []
        # Lambda capture rewrite stack: captured name → rendered expr (e.g. self.base)
        self._lambda_capture_stack: list[dict[str, str]] = []
        self._lambda_local_stack: list[set[str]] = []
        self._exception_var_stack: list[set[str]] = []
        self._pending_exception_var_push: bool = False
        self._return_type_stack: list[str] = []
        self._function_depth: int = 0
        self._try_depth: int = 0
        self._try_label_stack: list[str] = []
        mapping_path = Path("src").joinpath("runtime").joinpath("zig").joinpath("mapping.json")
        self._runtime_mapping: RuntimeMapping = load_runtime_mapping(mapping_path)
        self._catch_all_exception_types: set[str] = set()
        for name in self._runtime_mapping.types.keys():
            mapped = self._runtime_mapping.types.get(name, "")
            if mapped == "pytra.PyObject":
                self._catch_all_exception_types.add(name)
        self._top_level_runtime_inits: list[tuple[str, str]] = []
        self._uses_pytra_std_sys: bool = False
        self._extern_native_emitted: bool = False

    def _make_stmt_renderer(self) -> _ZigStmtCommonRenderer:
        renderer_owner = self._renderer_owner_value()
        renderer = _new_zig_stmt_common_renderer(renderer_owner)
        renderer.state.lines = self.lines
        renderer.state.indent_level = self.indent
        renderer.state.tmp_counter = self.tmp_seq
        renderer._tmp_counter = self.tmp_seq
        return renderer

    def _renderer_owner_value(self) -> "ZigNativeEmitter":
        return self

    def _sync_from_stmt_renderer(self, renderer: _ZigStmtCommonRenderer) -> None:
        self.indent = renderer.state.indent_level
        self.tmp_seq = renderer.state.tmp_counter

    def _begin_exception_binding(self, safe_name: str, value_expr: str) -> None:
        self._emit_line("const " + safe_name + " = " + value_expr + ";")
        self._exception_var_stack.append({safe_name})
        self._pending_exception_var_push = True

    def _end_pending_exception_binding(self) -> None:
        if self._pending_exception_var_push:
            self._exception_var_stack.pop()
            self._pending_exception_var_push = False

    def _union_storage_zig(self) -> str:
        return "*pytra.UnionVal"

    def _is_union_storage_zig(self, zig_ty: str) -> bool:
        check_ty = zig_ty
        if check_ty.startswith("?"):
            check_ty = check_ty[1:]
        return check_ty == "*pytra.UnionVal" or check_ty == "*pytra.JsonVal"

    def _type_expr_mirror(self, node: Any) -> str:
        if not isinstance(node, dict):
            return ""
        summary = node.get("type_expr_summary_v1")
        if isinstance(summary, dict):
            mirror = summary.get("mirror")
            if isinstance(mirror, str) and mirror.strip() not in {"", "unknown"}:
                return mirror.strip()
        resolved = node.get("resolved_type")
        if isinstance(resolved, str) and resolved.strip() not in {"", "unknown"}:
            return resolved.strip()
        return ""

    def _type_alias_value_mirror(self, stmt: dict[str, Any]) -> str:
        mirror = self._type_expr_mirror(stmt)
        alias_name = _safe_ident(stmt.get("name"), "T")
        if mirror != "" and mirror != alias_name:
            return mirror
        value_any = stmt.get("value")
        if isinstance(value_any, dict):
            mirror = self._type_expr_mirror(value_any)
            if mirror != "":
                return mirror
        target = stmt.get("target")
        if isinstance(target, str) and target.strip() not in {"", "unknown", alias_name}:
            return target.strip()
        return ""

    def _zig_tuple_type(self, normalized_tuple_type: str) -> str:
        """タプル型を名前付き型として返す。初出時に typedef を登録する。"""
        if normalized_tuple_type in self._tuple_typedefs:
            return self._tuple_typedefs[normalized_tuple_type]
        parts = self._split_generic(normalized_tuple_type[6:-1])
        inner_types = [self._zig_type(p.strip()) for p in parts]
        name = "Tuple" + str(self._tuple_typedef_seq)
        self._tuple_typedef_seq += 1
        self._tuple_typedefs[normalized_tuple_type] = name
        return name

    def _emit_tuple_typedefs(self) -> None:
        """登録されたタプル typedef をモジュール先頭に出力する。"""
        for norm_type, name in self._tuple_typedefs.items():
            parts = self._split_generic(norm_type[6:-1])
            inner_types: list[str] = []
            for p in parts:
                inner_types.append(self._zig_type(p.strip()))
            field_parts: list[str] = []
            index = 0
            while index < len(inner_types):
                field_parts.append("_" + str(index) + ": " + inner_types[index])
                index += 1
            fields = ", ".join(field_parts)
            self._emit_line("const " + name + " = struct { " + fields + " };")

    def _current_type_map(self) -> dict[str, str]:
        if len(self._local_type_stack) == 0:
            return {}
        return self._local_type_stack[-1]

    def _current_storage_type_map(self) -> dict[str, str]:
        if len(self._storage_type_stack) == 0:
            return {}
        return self._storage_type_stack[-1]

    def _current_ref_vars(self) -> set[str]:
        if len(self._ref_var_stack) == 0:
            empty: set[str] = set()
            return empty
        return self._ref_var_stack[-1]

    def _current_local_vars(self) -> set[str]:
        if len(self._local_var_stack) == 0:
            empty: set[str] = set()
            return empty
        return self._local_var_stack[-1]

    def _current_mutated_vars(self) -> set[str]:
        if len(self._mutated_var_stack) == 0:
            empty: set[str] = set()
            return empty
        return self._mutated_var_stack[-1]

    def _current_lambda_locals(self) -> set[str]:
        if len(self._lambda_local_stack) == 0:
            empty: set[str] = set()
            return empty
        return self._lambda_local_stack[-1]

    def _add_current_local_var(self, name: str) -> None:
        values = self._current_local_vars()
        values.add(name)

    def _add_current_lambda_local(self, name: str) -> None:
        values = self._current_lambda_locals()
        values.add(name)

    def _storage_type_setdefault(self, name: str, decl_type: str) -> None:
        mapping = self._current_storage_type_map()
        if name not in mapping:
            mapping[name] = decl_type

    def _current_exception_vars(self) -> set[str]:
        if len(self._exception_var_stack) == 0:
            empty: set[str] = set()
            return empty
        return self._exception_var_stack[-1]

    def _scan_mutated_vars(self, body_any: Any) -> set[str]:
        """関数本体をスキャンし、再代入・AugAssign される変数名を集める。"""
        mutated: set[str] = set()
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "AugAssign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    mutated.add(_safe_ident(target.get("id"), ""))
            elif kind == "Assign":
                # Subscript 代入: dict[key] = val / list[idx] = val → owner は mutated
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Subscript":
                    sub_val = target.get("value")
                    if isinstance(sub_val, dict) and sub_val.get("kind") == "Name":
                        mutated.add(_safe_ident(sub_val.get("id"), ""))
            elif kind == "Expr":
                value = stmt.get("value")
                if isinstance(value, dict) and value.get("kind") == "Call":
                    func = value.get("func")
                    if isinstance(func, dict) and func.get("kind") == "Attribute":
                        owner = func.get("value")
                        if isinstance(owner, dict) and owner.get("kind") == "Name":
                            attr = _safe_ident(func.get("attr"), "")
                            if attr in {'clear', 'pop', 'setdefault', 'append', 'extend'}:
                                mutated.add(_safe_ident(owner.get("id"), ""))
            elif kind == "If":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
                mutated.update(self._scan_mutated_vars(stmt.get("orelse")))
            elif kind == "ForCore":
                tp = stmt.get("target_plan")
                if isinstance(tp, dict) and tp.get("kind") == "NameTarget":
                    mutated.add(_safe_ident(tp.get("id"), ""))
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "ForRange":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    mutated.add(_safe_ident(target.get("id"), ""))
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "While":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "Swap":
                left = stmt.get("left")
                right = stmt.get("right")
                if isinstance(left, dict) and left.get("kind") == "Name":
                    mutated.add(_safe_ident(left.get("id"), ""))
                if isinstance(right, dict) and right.get("kind") == "Name":
                    mutated.add(_safe_ident(right.get("id"), ""))
            elif kind == "Try":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
                handlers = stmt.get("handlers")
                if isinstance(handlers, list):
                    for h in handlers:
                        if isinstance(h, dict):
                            mutated.update(self._scan_mutated_vars(h.get("body")))
                mutated.update(self._scan_mutated_vars(stmt.get("finalbody")))
        # AnnAssign で宣言された変数名を集め、Assign で再代入されるものを mutated に追加
        # トップレベルで宣言された変数を集め、ネスト内での再代入を検出
        declared: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"AnnAssign", "Assign"}:
                target_any = stmt.get("target")
                target_node: dict[str, JsonVal] = {}
                has_target = False
                if isinstance(target_any, dict):
                    target_node = target_any
                    has_target = True
                else:
                    targets = stmt.get("targets")
                    if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                        first_target = targets[0]
                        if isinstance(first_target, dict):
                            target_node = first_target
                            has_target = True
                if has_target and target_node.get("kind") == "Name":
                    declared.add(_safe_ident(target_node.get("id"), ""))
        # 同一スコープ内の Assign 重複（2回目は再代入）+ ネスト内の再代入を検出
        assign_seen: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"Assign", "AnnAssign"}:
                target_any = stmt.get("target")
                target_node: dict[str, JsonVal] = {}
                has_target = False
                if isinstance(target_any, dict):
                    target_node = target_any
                    has_target = True
                else:
                    targets = stmt.get("targets")
                    if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                        first_target = targets[0]
                        if isinstance(first_target, dict):
                            target_node = first_target
                            has_target = True
                if has_target and target_node.get("kind") == "Name":
                    n = _safe_ident(target_node.get("id"), "")
                    if n in assign_seen:
                        mutated.add(n)
                    assign_seen.add(n)
            elif kind == "ForCore":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "ForRange":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "While":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "If":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("orelse"), declared, mutated)
            elif kind == "Try":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                handlers = stmt.get("handlers")
                if isinstance(handlers, list):
                    for h in handlers:
                        if isinstance(h, dict):
                            self._scan_reassign_to_declared(h.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("finalbody"), declared, mutated)
        return mutated

    def _collect_assigned_name_counts(self, node: Any) -> dict[str, int]:
        counts: dict[str, int] = {}

        def add(name: str) -> None:
            counts[name] = counts.get(name, 0) + 1

        if not isinstance(node, list):
            return counts
        for cur in node:
            if not isinstance(cur, dict):
                continue
            kind = str(cur.get("kind") or "")
            if kind in {"Assign", "AnnAssign", "AugAssign"}:
                target = cur.get("target")
                if not isinstance(target, dict):
                    targets = cur.get("targets")
                    if isinstance(targets, list):
                        for item in targets:
                            if isinstance(item, dict) and item.get("kind") == "Name":
                                add(_safe_ident(item.get("id"), ""))
                    target = None
                if isinstance(target, dict) and target.get("kind") == "Name":
                    add(_safe_ident(target.get("id"), ""))
            if kind == "With":
                var_name_any = cur.get("var_name")
                if isinstance(var_name_any, str):
                    var_name: str = var_name_any
                    if var_name != "":
                        add(_safe_ident(var_name, "ctx"))
        return counts

    def _scan_reassign_to_declared(self, body_any: Any, declared: set[str], mutated: set[str]) -> None:
        """declared に含まれる変数名への Assign/AugAssign をネスト含めて検出する。"""
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"Assign", "AnnAssign"}:
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    n = _safe_ident(target.get("id"), "")
                    if n in declared:
                        mutated.add(n)
                targets = stmt.get("targets")
                if isinstance(targets, list):
                    for t in targets:
                        if isinstance(t, dict) and t.get("kind") == "Name":
                            n = _safe_ident(t.get("id"), "")
                            if n in declared:
                                mutated.add(n)
            elif kind == "AugAssign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    n = _safe_ident(target.get("id"), "")
                    if n in declared:
                        mutated.add(n)
            elif kind == "If":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("orelse"), declared, mutated)
            elif kind == "ForCore":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "ForRange":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "While":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "Try":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                handlers = stmt.get("handlers")
                if isinstance(handlers, list):
                    for h in handlers:
                        if isinstance(h, dict):
                            self._scan_reassign_to_declared(h.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("finalbody"), declared, mutated)

    def _is_var_mutated(self, name: str) -> bool:
        return name in self._current_mutated_vars()

    def _needs_var_for_type(self, decl_type: str) -> bool:
        """型が mutable メソッドを持つクラスなら var が必要（ポインタ型では不要）。"""
        t = self._normalize_type(decl_type)
        if t.startswith("list[") or t.startswith("set[") or t in {"bytes", "bytearray"}:
            return False
        # dict 型は put で mutation するが、read-only 使用もある
        # _is_var_mutated で Subscript 代入を検出する方が正確
        # ポインタ型（*ClassName）なら const でもフィールド変更可能
        if t in self.class_names:
            return False
        return t in self._classes_with_mut_method

    def _body_uses_name(self, body_any: Any, name: str) -> bool:
        """body 内で指定した名前が Name ノードの id として参照されているか判定する。"""
        if not isinstance(body_any, list):
            return False
        return self._node_uses_name(body_any, name)

    def _body_uses_name_runtime(self, body_any: Any, name: str) -> bool:
        """body 内で実行時コードに残る名前参照だけを判定する。"""
        if not isinstance(body_any, list):
            return False
        return self._node_uses_name_runtime(body_any, name)

    def _node_uses_name(self, node: Any, name: str) -> bool:
        """AST ノードツリー内で Name.id == name の参照を検索する。"""
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            if nd.get("kind") == "Name" and nd.get("id") == name:
                return True
            for key, val in nd.items():
                # Skip non-structural fields
                if key in {"repr", "source_span", "resolved_type", "semantic_tag",
                           "runtime_call", "resolved_runtime_call", "runtime_module_id",
                           "runtime_symbol", "escape_summary", "type_expr_summary_v1"}:
                    continue
                if self._node_uses_name(val, name):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._node_uses_name(item, name):
                    return True
        return False

    def _node_uses_name_runtime(self, node: Any, name: str) -> bool:
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            if nd.get("kind") == "Name" and nd.get("id") == name:
                return True
            for key, val in nd.items():
                if key in {"repr", "source_span", "resolved_type", "semantic_tag",
                           "runtime_call", "resolved_runtime_call", "runtime_module_id",
                           "runtime_symbol", "escape_summary", "type_expr_summary_v1"}:
                    continue
                if nd.get("kind") == "Raise" and key == "cause":
                    continue
                if self._node_uses_name_runtime(val, name):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._node_uses_name_runtime(item, name):
                    return True
        return False

    def _strip_dead_branches(self, body_any: Any) -> list[dict[str, Any]]:
        """body から明らかな dead branch (if false) だけを除去したリストを返す。"""
        if not isinstance(body_any, list):
            return []
        result: list[dict[str, Any]] = []
        for stmt in body_any:
            if not isinstance(stmt, dict):
                continue
            if stmt.get("kind") == "If":
                test = stmt.get("test")
                if isinstance(test, dict):
                    test_kind = test.get("kind")
                    test_value = test.get("value")
                    is_false_const = False
                    if test_kind == "Constant" and isinstance(test_value, bool):
                        is_false_const = not test_value
                    if is_false_const:
                        # Dead branch: skip body, include only orelse
                        orelse = stmt.get("orelse")
                        if isinstance(orelse, list):
                            result.extend(self._strip_dead_branches(orelse))
                        continue
            result.append(stmt)
        return result

    def _body_mutates_self(self, body_any: Any) -> bool:
        """body 内で self のフィールドに代入があるか判定する。"""
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"Assign", "AnnAssign", "AugAssign"}:
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Attribute":
                    val = target.get("value")
                    if isinstance(val, dict) and val.get("kind") == "Name" and val.get("id") == "self":
                        return True
        return False

    def _node_uses_super_call(self, node: Any) -> bool:
        if isinstance(node, dict):
            if node.get("kind") == "Call":
                func = node.get("func")
                if isinstance(func, dict) and func.get("kind") == "Name" and func.get("id") == "super":
                    return True
            for key, val in node.items():
                if key in {"repr", "source_span", "resolved_type", "semantic_tag",
                           "runtime_call", "resolved_runtime_call", "runtime_module_id",
                           "runtime_symbol", "escape_summary", "type_expr_summary_v1"}:
                    continue
                if self._node_uses_super_call(val):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._node_uses_super_call(item):
                    return True
        return False

    def _push_function_context(self, stmt: dict[str, Any], arg_names: list[str], arg_order: list[Any]) -> None:
        empty_hoisted: set[str] = set()
        self._hoisted_var_names = empty_hoisted
        type_map: dict[str, str] = {}
        storage_type_map: dict[str, str] = {}
        ref_vars: set[str] = set()
        local_vars: set[str] = set(arg_names)
        arg_types_any = stmt.get("arg_types")
        arg_types: dict[str, Any] = {}
        if isinstance(arg_types_any, dict):
            arg_types = self._json_dict_to_any(arg_types_any)
        i = 0
        while i < len(arg_names):
            safe_name = arg_names[i]
            raw_name = safe_name
            if i < len(arg_order):
                raw_name = self._any_str(arg_order[i], safe_name)
            arg_type = self._dict_get_str(arg_types, raw_name, "")
            if arg_type == "":
                arg_type = self._dict_get_str(arg_types, safe_name, "")
            arg_type = arg_type.strip()
            if arg_type != "":
                type_map[safe_name] = arg_type
                storage_type_map[safe_name] = arg_type
            i += 1
        self._local_type_stack.append(type_map)
        self._storage_type_stack.append(storage_type_map)
        self._ref_var_stack.append(ref_vars)
        self._local_var_stack.append(local_vars)
        empty_decl_lines: dict[str, int] = {}
        self._decl_line_stack.append(empty_decl_lines)
        reassigned: set[str] = set()
        body_for_counts = stmt.get("body")
        if isinstance(body_for_counts, (dict, list)):
            for name, count in self._collect_assigned_name_counts(body_for_counts).items():
                if count > 1:
                    reassigned.add(name)
        self._reassigned_name_stack.append(reassigned)
        self._mutated_var_stack.append(self._scan_mutated_vars(stmt.get("body")))
        empty_lambda_locals: set[str] = set()
        self._lambda_local_stack.append(empty_lambda_locals)
        ret_any = stmt.get("return_type")
        ret_type = self._any_str(ret_any, "").strip()
        self._return_type_stack.append(self._zig_type(ret_type) if ret_type != "" else "void")

    def _collect_branch_assigned_names(self, node: Any, nested: bool = False) -> set[str]:
        names: set[str] = set()
        if isinstance(node, list):
            for item in node:
                names.update(self._collect_branch_assigned_names(item, nested))
            return names
        if not isinstance(node, dict):
            return names
        kind = str(node.get("kind") or "")
        if kind == "Assign":
            target = node.get("target")
            if not isinstance(target, dict):
                targets = node.get("targets")
                if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                    target = targets[0]
            if nested and isinstance(target, dict) and target.get("kind") == "Name":
                value = node.get("value")
                skip_tuple_temp = False
                if isinstance(value, dict) and value.get("kind") == "Subscript":
                    owner = value.get("value")
                    if isinstance(owner, dict):
                        owner_id = owner.get("id")
                        if isinstance(owner_id, str) and owner_id.startswith("__tte_"):
                            skip_tuple_temp = True
                if not skip_tuple_temp:
                    names.add(_safe_ident(target.get("id"), "value"))
            return names
        if kind == "AnnAssign":
            target = node.get("target")
            if nested and isinstance(target, dict) and target.get("kind") == "Name":
                names.add(_safe_ident(target.get("id"), "value"))
            return names
        child_nested = nested or kind in {"If", "Try", "ExceptHandler", "With", "While", "ForCore", "ForRange"}
        for key, value in node.items():
            if key in {"repr", "source_span", "resolved_type", "semantic_tag",
                       "runtime_call", "resolved_runtime_call", "runtime_module_id",
                       "runtime_symbol", "escape_summary", "type_expr_summary_v1"}:
                continue
            names.update(self._collect_branch_assigned_names(value, child_nested))
        return names

    def _collect_existing_vardecl_names(self, node: Any) -> set[str]:
        names: set[str] = set()
        if isinstance(node, list):
            for item in node:
                names.update(self._collect_existing_vardecl_names(item))
            return names
        if not isinstance(node, dict):
            return names
        if str(node.get("kind") or "") == "VarDecl":
            names.add(_safe_ident(node.get("name"), "var_"))
        for value in node.values():
            names.update(self._collect_existing_vardecl_names(value))
        return names

    def _collect_top_level_assigned_names(self, body_any: Any) -> set[str]:
        names: set[str] = set()
        body = body_any if isinstance(body_any, list) else []
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            kind = str(stmt.get("kind") or "")
            if kind == "Assign":
                target = stmt.get("target")
                if not isinstance(target, dict):
                    targets = stmt.get("targets")
                    if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                        target = targets[0]
                if isinstance(target, dict) and target.get("kind") == "Name":
                    names.add(_safe_ident(target.get("id"), "value"))
            if kind == "AnnAssign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    names.add(_safe_ident(target.get("id"), "value"))
        return names

    def _expr_is_float_like(self, node: Any) -> bool:
        if not isinstance(node, dict):
            return False
        node_type = self._lookup_expr_type(node) or self._get_expr_type(node)
        if node_type in {"float", "float32", "float64"}:
            return True
        kind = str(node.get("kind") or "")
        if kind == "Constant":
            value = node.get("value")
            return isinstance(value, float)
        if kind == "BinOp":
            if str(node.get("op") or "") == "Div":
                return True
            return self._expr_is_float_like(node.get("left")) or self._expr_is_float_like(node.get("right"))
        if kind == "UnaryOp":
            return self._expr_is_float_like(node.get("operand"))
        if kind in {"Call", "Attribute", "IfExp"}:
            expr_keys = ["func", "value", "test", "body", "orelse"]
            for key in expr_keys:
                if self._expr_is_float_like(node.get(key)):
                    return True
            args = node.get("args")
            if isinstance(args, list):
                for arg in args:
                    if self._expr_is_float_like(arg):
                        return True
        return False

    def _pop_function_context(self) -> None:
        if len(self._local_type_stack) > 0:
            self._local_type_stack.pop()
        if len(self._storage_type_stack) > 0:
            self._storage_type_stack.pop()
        if len(self._ref_var_stack) > 0:
            self._ref_var_stack.pop()
        if len(self._local_var_stack) > 0:
            self._local_var_stack.pop()
        if len(self._decl_line_stack) > 0:
            self._decl_line_stack.pop()
        if len(self._reassigned_name_stack) > 0:
            self._reassigned_name_stack.pop()
        if len(self._mutated_var_stack) > 0:
            self._mutated_var_stack.pop()
        if len(self._lambda_local_stack) > 0:
            self._lambda_local_stack.pop()
        if len(self._return_type_stack) > 0:
            self._return_type_stack.pop()

    def _exception_return_stmt(self) -> str:
        if len(self._return_type_stack) == 0:
            return "return;"
        ret_type = self._return_type_stack[-1]
        if ret_type == "void":
            return "return;"
        if ret_type.startswith("?"):
            return "return null;"
        if ret_type == "bool":
            return "return false;"
        if ret_type in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "usize", "isize", "f64", "f32"}:
            return "return 0;"
        if ret_type == "[]const u8":
            return "return \"\";"
        return "return undefined;"

    def _record_decl_line(self, name: str) -> None:
        self.tmp_seq = self.tmp_seq
        if len(self._decl_line_stack) == 0:
            return
        self._decl_line_stack[-1][name] = len(self.lines) - 1

    def _mark_decl_mutable(self, name: str) -> None:
        candidates: list[int] = []
        if len(self._decl_line_stack) > 0:
            line_idx = self._decl_line_stack[-1].get(name)
            if isinstance(line_idx, int):
                candidates.append(line_idx)
        i = len(self.lines) - 1
        while i >= 0:
            candidates.append(i)
            i -= 1
        seen: set[int] = set()
        for line_idx in candidates:
            if line_idx in seen or line_idx < 0 or line_idx >= len(self.lines):
                continue
            seen.add(line_idx)
            line = self.lines[line_idx]
            stripped = line.lstrip()
            if stripped.startswith("const " + name):
                indent = line[: len(line) - len(stripped)]
                self.lines[line_idx] = indent + "var " + stripped[len("const "):]
                return

    def _is_name_reassigned(self, name: str) -> bool:
        return len(self._reassigned_name_stack) > 0 and name in self._reassigned_name_stack[-1]

    def _is_top_level_decl(self, stmt: dict[str, Any]) -> bool:
        """トップレベル宣言（関数/クラス/import/型エイリアス）かどうか判定する。"""
        kind = stmt.get("kind")
        return kind in {"FunctionDef", "ClassDef", "Import", "ImportFrom", "TypeAlias"}

    def _is_top_level_var(self, stmt: dict[str, Any]) -> bool:
        """トップレベル変数宣言（Assign/AnnAssign で Name ターゲット）かどうか判定する。"""
        kind = stmt.get("kind")
        if kind == "AnnAssign":
            target = stmt.get("target")
            return isinstance(target, dict) and target.get("kind") == "Name"
        if kind == "Assign":
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                return True
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0:
                first_target = targets[0]
                if isinstance(first_target, dict) and first_target.get("kind") == "Name":
                    return True
        return False

    def _emit_top_level_var(self, stmt: dict[str, Any]) -> None:
        """トップレベル変数をモジュールスコープの var として emit する。"""
        kind = stmt.get("kind")
        target_name = ""
        if kind == "AnnAssign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                target_name = _safe_ident(target_any.get("id"), "value")
        elif kind == "Assign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                target_name = _safe_ident(target_any.get("id"), "value")
        if target_name == "":
            return
        value_node = stmt.get("value")
        if _starts_with_upper(target_name):
            if isinstance(value_node, dict) and value_node.get("kind") in {"Name", "Subscript"}:
                return
        # extern() 変数 → __native 委譲（spec-emitter-guide §4）
        if isinstance(value_node, dict):
            if value_node.get("kind") == "Call":
                vfunc = value_node.get("func")
                if isinstance(vfunc, dict) and vfunc.get("id") in {"extern", "@\"extern\""}:
                    self._ensure_native_import()
                    decl_type = self._infer_decl_type(stmt)
                    zig_ty = self._zig_type(decl_type)
                    self._emit_line("pub const " + target_name + ": " + zig_ty + " = __native." + target_name + ";")
                    return
            elif value_node.get("kind") == "Unbox":
                unboxed = value_node.get("value")
                if isinstance(unboxed, dict) and unboxed.get("kind") == "Call":
                    vfunc = unboxed.get("func")
                    if isinstance(vfunc, dict) and vfunc.get("id") in {"extern", "@\"extern\""}:
                        self._ensure_native_import()
                        decl_type = self._infer_decl_type(stmt)
                        zig_ty = self._zig_type(decl_type)
                        self._emit_line("pub const " + target_name + ": " + zig_ty + " = __native." + target_name + ";")
                        return
        decl_type = self._infer_decl_type(stmt)
        zig_ty = self._zig_type(decl_type)
        value = self._render_expr(value_node) if isinstance(value_node, dict) else "undefined"
        prefix = "pub var " if self.is_submodule else "var "
        if self.is_submodule and self._top_level_value_needs_runtime_init(value):
            self._top_level_runtime_inits.append((target_name, value))
            self._emit_line(prefix + target_name + ": " + zig_ty + " = undefined;")
            return
        self._emit_line(prefix + target_name + ": " + zig_ty + " = " + value + ";")

    def transpile(self) -> str:
        renderer = self._make_stmt_renderer()
        module_comments = self._module_leading_comment_lines(prefix="// ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        self.lines.append("const std = @import(\"std\");")
        rt_path = self._root_rel_prefix() + "built_in/py_runtime.zig"
        self.lines.append("const pytra = @import(\"" + rt_path + "\");")
        self.lines.extend(renderer.exception_support_decl_lines())
        self.lines.extend(renderer.exception_slot_decl_lines())
        body = self._dict_list(self._json_to_any(self.east_doc.get("body")))
        main_guard = self._dict_list(self._json_to_any(self.east_doc.get("main_guard_body")))
        self._scan_module_symbols(body)
        # import 文から @import を生成
        self._emit_imports(body)
        self.lines.append("")
        # 静的フィールドをモジュールスコープに emit
        for cls_name, sfields in self._static_fields.items():
            for sfield in sfields:
                field_name = sfield[0]
                field_type = sfield[1]
                default_val = sfield[2]
                zig_ty = self._zig_type(field_type)
                self._emit_line("var Module_" + cls_name + "_" + field_name + ": " + zig_ty + " = " + default_val + ";")
        # トップレベル変数をモジュールスコープに emit
        for stmt in body:
            if self._is_top_level_var(stmt):
                self._emit_top_level_var(stmt)
        # トップレベル宣言（fn, struct）を emit
        for stmt in body:
            if self._is_top_level_decl(stmt):
                self._emit_stmt(stmt)
        self._emit_top_level_runtime_init_func()
        # vtable を emit
        self._emit_vtables()
        # §8: 残りのステートメント + main_guard_body (is_entry のみ) を pub fn main() に入れる
        ectx_main = self._get_emit_context()
        is_entry = False
        if isinstance(ectx_main, dict):
            is_entry_any: Any = ectx_main.get("is_entry")
            if isinstance(is_entry_any, bool):
                is_entry = is_entry_any
        top_stmts: list[dict[str, Any]] = []
        for stmt in body:
            if not self._is_top_level_decl(stmt) and not self._is_top_level_var(stmt):
                top_stmts.append(stmt)
        if is_entry:
            for stmt in main_guard:
                top_stmts.append(stmt)
        if len(top_stmts) > 0 or is_entry:
            self._mutated_var_stack.append(self._scan_mutated_vars(top_stmts))
            empty_local_vars: set[str] = set()
            empty_type_map: dict[str, str] = {}
            empty_ref_vars: set[str] = set()
            empty_lambda_locals: set[str] = set()
            self._local_var_stack.append(empty_local_vars)
            self._local_type_stack.append(empty_type_map)
            self._ref_var_stack.append(empty_ref_vars)
            self._lambda_local_stack.append(empty_lambda_locals)
            self._return_type_stack.append("void")
            self.lines.append("pub fn main() void {")
            self.indent += 1
            self._emit_line("__pytra_init_module();")
            self._emit_line("if (__pytra_exc_type != null) return;")
            if self._uses_pytra_std_sys:
                self._emit_line("const __pytra_process_args = std.process.argsAlloc(std.heap.page_allocator) catch unreachable;")
                self._emit_line("defer std.process.argsFree(std.heap.page_allocator, __pytra_process_args);")
                self._emit_line("const __pytra_argv_obj = pytra.make_list([]const u8);")
                self._emit_line("for (__pytra_process_args) |__pytra_arg| {")
                self.indent += 1
                self._emit_line("pytra.list_append(__pytra_argv_obj, []const u8, __pytra_arg);")
                self.indent -= 1
                self._emit_line("}")
                self._emit_line("pytra_std_sys.set_argv(__pytra_argv_obj);")
            for stmt in top_stmts:
                self._emit_stmt(stmt)
            self.indent -= 1
            self.lines.append("}")
            self._pop_function_context()
        self._fixup_unused_obj_vars()
        self._fixup_block_member_access()
        self._fixup_undeclared_simple_assignments()
        self._fixup_final_zig_strictness()
        self._fixup_known_type_artifacts()
        # タプル typedef をモジュール先頭（import 直後）に挿入
        if len(self._tuple_typedefs) > 0:
            insert_idx = 0
            # @import 行の直後を探す
            for li in range(len(self.lines)):
                line = self.lines[li].strip()
                if line.startswith("const ") and "@import" in line:
                    insert_idx = li + 1
            typedef_lines: list[str] = []
            for norm_type, name in self._tuple_typedefs.items():
                parts = self._split_generic(norm_type[6:-1])
                inner_types: list[str] = []
                for p in parts:
                    inner_types.append(self._zig_type(p.strip()))
                field_parts: list[str] = []
                i = 0
                while i < len(inner_types):
                    field_parts.append("_" + str(i) + ": " + inner_types[i])
                    i += 1
                fields = ", ".join(field_parts)
                typedef_lines.append("const " + name + " = struct { " + fields + " };")
            rebuilt_lines: list[str] = []
            li = 0
            while li < len(self.lines):
                if li == insert_idx:
                    for tl in typedef_lines:
                        rebuilt_lines.append(tl)
                rebuilt_lines.append(self.lines[li])
                li += 1
            if insert_idx >= len(self.lines):
                for tl in typedef_lines:
                    rebuilt_lines.append(tl)
            self.lines = rebuilt_lines
        return "\n".join(self.lines).rstrip() + "\n"

    def _top_level_value_needs_runtime_init(self, value: str) -> bool:
        return (
            "pytra.list_from(" in value
            or "pytra.make_str_dict(" in value
            or "pytra.make_str_dict_from(" in value
            or "__call_blk_" in value
            or ".joinpath(" in value
        )

    def _emit_top_level_runtime_init_func(self) -> None:
        self._emit_line("pub fn __pytra_init_module() void {")
        self.indent += 1
        for name, value in self._top_level_runtime_inits:
            if value == "":
                self._emit_line("if (@hasDecl(" + name.split(".", 1)[0] + ", \"__pytra_init_module\")) " + name + ";")
                self._emit_line("if (__pytra_exc_type != null) return;")
                continue
            self._emit_line(name + " = " + value + ";")
            self._emit_line("if (__pytra_exc_type != null) return;")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _fixup_unused_obj_vars(self) -> None:
        """Selfhost-safe cleanup for a few simple generated artifacts."""
        cleaned: list[str] = []
        for line in self.lines:
            stripped = line.strip()
            if stripped == "_ = _unused;":
                continue
            if line.strip() == "":
                cleaned.append(line)
                continue
            cleaned.append(line)
        self.lines = cleaned

    def _fixup_block_member_access(self) -> None:
        """後処理: Zig の labeled block expression への member access を括弧で保護する。"""
        fixed: list[str] = []
        for raw_line in self.lines:
            line = raw_line
            if "__idx_blk_" in line and ": {" in line and ("}._" in line or "}.__" in line):
                line = line.replace("; }._", "; })._")
                line = line.replace("; }.__", "; }).__")
            if "var base_type" in line:
                line = line.replace("var base_type", "const base_type")
            fixed.append(line)
        self.lines = fixed

    def _fixup_undeclared_simple_assignments(self) -> None:
        """後処理: 同一関数内で宣言漏れした単純代入を var 宣言に戻す。"""
        return

    def _fixup_final_zig_strictness(self) -> None:
        """後処理: Zig の unused capture / never-mutated var を最後に整える。"""
        return

    def _fixup_known_type_artifacts(self) -> None:
        return

    def _wrap_union_return_lines(self, lines: list[str], owner_cls: str = "") -> list[str]:
        return lines

    def _json_to_any(self, value: JsonVal) -> Any:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            return value
        arr_value = pytra_json.JsonValue(value).as_arr()
        if arr_value is not None:
            out_list: list[Any] = []
            for item in arr_value.raw:
                out_list.append(self._json_to_any(item))
            return out_list
        obj_value = pytra_json.JsonValue(value).as_obj()
        if obj_value is not None:
            out_dict: dict[str, Any] = {}
            for key, item in obj_value.raw.items():
                out_dict[key] = self._json_to_any(item)
            return out_dict
        return None

    def _json_dict_to_any(self, value: dict[str, JsonVal]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, item in value.items():
            out[key] = self._json_to_any(item)
        return out

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
        trivia = self._dict_list(self._json_to_any(self.east_doc.get("module_leading_trivia")))
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
                n = 1
                if isinstance(count, int) and count > 0:
                    n = count
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
                n = 1
                if isinstance(count, int) and count > 0:
                    n = count
                i = 0
                while i < n:
                    self._emit_line("")
                    i += 1

    def _emit_line(self, text: str) -> None:
        self.lines.append(("    " * self.indent) + text)

    def _stmt_guarantees_local_exit(self, stmt: dict[str, Any]) -> bool:
        kind = stmt.get("kind")
        if kind in {"Return", "Raise", "Try", "Break", "Continue"}:
            return True
        if kind == "Expr":
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "Name":
                loop_kw = str(value.get("id"))
                if loop_kw in {"break", "continue"}:
                    return True
        return False

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        renderer = self._make_stmt_renderer()
        exc_check = renderer.render_active_exception_check()
        for stmt in body:
            self._emit_stmt(stmt)
            if self._function_depth > 0 and self._try_depth == 0:
                if not self._stmt_guarantees_local_exit(stmt):
                    self._emit_line("if (" + exc_check + ") " + self._exception_return_stmt())

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "TypeAlias":
                alias_name = _safe_ident(stmt.get("name"), "T")
                alias_mirror = self._type_alias_value_mirror(stmt)
                if alias_mirror != "":
                    self._type_aliases[alias_name] = alias_mirror
            if kind == "FunctionDef":
                name = _safe_ident(stmt.get("name"), "fn")
                if name == "main":
                    name = "__pytra_main"
                self.function_names.add(name)
            if kind == "ClassDef":
                name = _safe_ident(stmt.get("name"), "Class")
                self.class_names.add(name)
                base_any = stmt.get("base")
                if isinstance(base_any, str) and base_any.strip() != "":
                    self._class_base[name] = _safe_ident(base_any.strip(), "")
                methods: set[str] = set()
                properties: set[str] = set()
                method_defaults: dict[str, list[Any]] = {}
                method_default_types: dict[str, list[str]] = {}
                method_arg_order: dict[str, list[str]] = {}
                cls_body = self._dict_list(stmt.get("body"))
                for sub in cls_body:
                    if sub.get("kind") in {"FunctionDef", "ClosureDef"}:
                        m_name = sub.get("name")
                        if isinstance(m_name, str):
                            arg_order_any = sub.get("arg_order")
                            arg_order: list[str] = []
                            if isinstance(arg_order_any, list):
                                for a in arg_order_any:
                                    arg_order.append(str(a))
                            method_arg_order[m_name] = arg_order
                            defaults_any = sub.get("arg_defaults")
                            arg_types_any = sub.get("arg_types")
                            arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
                            if isinstance(defaults_any, dict):
                                defaults_list: list[Any] = []
                                default_types: list[str] = []
                                for arg_name in arg_order[1:]:
                                    defaults_list.append(defaults_any.get(arg_name))
                                    arg_type_any = arg_types.get(arg_name)
                                    arg_type = ""
                                    if isinstance(arg_type_any, str):
                                        arg_type = arg_type_any.strip()
                                    default_types.append(arg_type)
                                method_defaults[m_name] = defaults_list
                                method_default_types[m_name] = default_types
                        if isinstance(m_name, str) and m_name != "__init__":
                            methods.add(m_name)
                            decorators = sub.get("decorators")
                            if isinstance(decorators, list) and "property" in decorators:
                                properties.add(m_name)
                self._class_methods[name] = methods
                self._class_properties[name] = properties
                self._class_method_defaults[name] = method_defaults
                self._class_method_default_types[name] = method_default_types
                self._class_method_arg_order[name] = method_arg_order
                if "__init__" in method_defaults:
                    self._class_init_defaults[name] = method_defaults["__init__"]
                    self._class_init_default_types[name] = method_default_types.get("__init__", [])
                if bool(stmt.get("dataclass")):
                    self._dataclass_names.add(name)
                    fields: list[str] = []
                    for sub in cls_body:
                        if sub.get("kind") == "AnnAssign":
                            target_any = sub.get("target")
                            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                                fields.append(_safe_ident(target_any.get("id"), "field"))
                    self._dataclass_fields[name] = fields
                # 静的フィールドの検出: AnnAssign で初期値付き + メソッド内で ClassName.field としてアクセス
                static_fields: list[list[str]] = []
                for sub in cls_body:
                    if sub.get("kind") in {"AnnAssign", "Assign"}:
                        target_any = sub.get("target")
                        if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                            field_name = _safe_ident(target_any.get("id"), "field")
                            value_node = sub.get("value")
                            if isinstance(value_node, dict):
                                decl_type = self._infer_decl_type(sub)
                                if decl_type == "":
                                    decl_type = self._get_expr_type(value_node)
                                default_val = self._render_expr(value_node)
                                static_fields.append([field_name, decl_type, default_val])
                if len(static_fields) > 0:
                    self._static_fields[name] = static_fields
                for sub in cls_body:
                    if sub.get("kind") in {"FunctionDef", "ClosureDef"}:
                        if sub.get("name") == "__init__":
                            self._classes_with_init.add(name)
                        elif sub.get("name") == "__del__":
                            self._classes_with_del.add(name)
                        elif self._body_mutates_self(sub.get("body")):
                            self._classes_with_mut_method.add(name)
                # メソッドの戻り値型を記録
                cls_ret_types: dict[str, str] = {}
                for sub in cls_body:
                    if sub.get("kind") in {"FunctionDef", "ClosureDef"}:
                        m_name = sub.get("name")
                        ret = sub.get("return_type")
                        if isinstance(m_name, str) and isinstance(ret, str):
                            cls_ret_types[m_name] = ret.strip()
                self._class_return_types[name] = cls_ret_types
        # __del__ があるクラスも vtable 対象にする（rc + drop が必要）
        for cls_name in self._classes_with_del:
            if cls_name not in self._vtable_root:
                self._vtable_root[cls_name] = cls_name
                if cls_name not in self._vtable_methods:
                    empty_methods: list[str] = []
                    self._vtable_methods[cls_name] = empty_methods
        # vtable 検出: 継承階層でメソッドが override されている場合
        for cls_name in self.class_names:
            base = self._class_base.get(cls_name, "")
            if base == "":
                continue
            empty_method_set: set[str] = set()
            own = self._class_methods.get(cls_name, empty_method_set)
            # 基底を辿って root を見つける
            root = base
            while self._class_base.get(root, "") != "":
                root = self._class_base[root]
            # root のメソッドと override を収集
            if root not in self._vtable_methods:
                all_methods: list[str] = []
                seen_m: set[str] = set()
                # root から全子孫のメソッドを収集
                for cn in self.class_names:
                    r = cn
                    while self._class_base.get(r, "") != "":
                        r = self._class_base[r]
                    if r != root:
                        continue
                    empty_cn_methods: set[str] = set()
                    for m in self._class_methods.get(cn, empty_cn_methods):
                        if m not in seen_m:
                            all_methods.append(m)
                            seen_m.add(m)
                self._vtable_methods[root] = all_methods
            self._vtable_root[cls_name] = root
            self._vtable_root[root] = root

    def _has_vtable(self, cls_name: str) -> bool:
        return cls_name in self._vtable_root

    def _get_vtable_root(self, cls_name: str) -> str:
        return self._vtable_root.get(cls_name, cls_name)

    def _emit_vtables(self) -> None:
        """vtable struct, wrapper 関数, vtable インスタンスを emit する。"""
        emitted_roots: set[str] = set()
        for root, methods in self._vtable_methods.items():
            if root in emitted_roots:
                continue
            emitted_roots.add(root)
            # VTable struct
            vt_name = root + "VT"
            self._emit_line("const " + vt_name + " = struct {")
            self.indent += 1
            for m in methods:
                ret_type = self._find_method_return_type(root, m)
                zig_ret = self._zig_type(ret_type)
                self._emit_line(m + ": *const fn (*anyopaque) " + zig_ret + ",")
            self.indent -= 1
            self._emit_line("};")
            self._emit_line("")
            # 階層内の全クラスの wrapper + vtable instance
            for cls_name in self.class_names:
                cls_root = self._vtable_root.get(cls_name, "")
                if cls_root != root:
                    continue
                # wrapper 関数と vtable instance
                for m in methods:
                    impl_cls = self._find_method_impl(cls_name, m)
                    ret_type = self._class_return_types.get(impl_cls, {}).get(m, "")
                    if ret_type == "":
                        ret_type = self._find_method_return_type(root, m)
                    zig_ret = self._zig_type(ret_type)
                    wrapper_name = cls_name + "_" + m + "_wrap"
                    self._emit_line("fn " + wrapper_name + "(p: *anyopaque) " + zig_ret + " {")
                    self.indent += 1
                    self._emit_line("const self_obj: *" + cls_name + " = @ptrCast(@alignCast(p));")
                    self._emit_line("return self_obj." + m + "();")
                    self.indent -= 1
                    self._emit_line("}")
                # drop wrapper for __del__
                if cls_name in self._classes_with_del:
                    drop_name = cls_name + "_drop_wrap"
                    self._emit_line("fn " + drop_name + "(p: *anyopaque) void {")
                    self.indent += 1
                    self._emit_line("const self: *" + cls_name + " = @ptrCast(@alignCast(p));")
                    self._emit_line(cls_name + ".__del__(self);")
                    self.indent -= 1
                    self._emit_line("}")
                # vtable instance
                vt_inst = cls_name + "_vt"
                field_inits: list[str] = []
                for m in methods:
                    field_inits.append("." + m + " = " + cls_name + "_" + m + "_wrap")
                self._emit_line("const " + vt_inst + " = " + vt_name + "{ " + ", ".join(field_inits) + " };")
                self._emit_line("")

    def _find_method_return_type(self, root: str, method: str) -> str:
        """vtable root から全子孫を辿り、method の戻り値型を見つける。"""
        for cls_name in self.class_names:
            r = self._vtable_root.get(cls_name, "")
            if r != root:
                continue
            empty_returns: dict[str, str] = {}
            ret = self._str_dict_get(self._class_return_types.get(cls_name, empty_returns), method, "")
            if ret != "":
                return ret
        return ""

    def _find_method_impl(self, cls_name: str, method: str) -> str:
        """cls_name から基底を辿り、method を実装しているクラスを返す。"""
        current = cls_name
        while current != "":
            empty_methods: set[str] = set()
            has_method = False
            for method_name in self._class_methods.get(current, empty_methods):
                if method_name == method:
                    has_method = True
            if has_method:
                return current
            current = self._class_base.get(current, "")
        return cls_name

    def _str_dict_get(self, mapping: dict[str, str], key: str, default_value: str) -> str:
        for item_key, item_value in mapping.items():
            if item_key == key:
                return item_value
        return default_value

    def _dict_get_str(self, mapping: dict[str, Any], key: str, default_value: str) -> str:
        value_any = mapping.get(key)
        if isinstance(value_any, str):
            return value_any
        return default_value

    def _any_str(self, value: Any, default_value: str) -> str:
        if isinstance(value, str):
            return value
        return default_value

    def _json_dict_get_str(self, obj: dict[str, JsonVal], key: str, default_value: str) -> str:
        if key not in obj:
            return default_value
        value = obj[key]
        if isinstance(value, str):
            return value
        return default_value

    def _get_emit_context(self) -> dict[str, Any]:
        meta_value = pytra_json.JsonValue(self.east_doc.get("meta")).as_obj()
        if meta_value is not None:
            ectx_value = meta_value.get_obj("emit_context")
            if ectx_value is not None:
                converted = self._json_to_any(ectx_value.raw)
                if isinstance(converted, dict):
                    return converted
        return {}

    def _current_module_id(self) -> str:
        ectx = self._get_emit_context()
        return self._dict_get_str(ectx, "module_id", "")

    def _root_rel_prefix(self) -> str:
        ectx = self._get_emit_context()
        rr = self._dict_get_str(ectx, "root_rel_prefix", "./")
        if rr == "./":
            return ""
        return rr

    def _module_id_to_import_path(self, module_id: str) -> str:
        """module_id から Zig import パスを機械的に生成（spec-emitter-guide §3）。"""
        native_file = self._runtime_mapping.module_native_files.get(module_id, "")
        if native_file != "":
            return self._root_rel_prefix() + native_file
        rel = module_id
        while rel.startswith("."):
            rel = rel[1:]
        return self._root_rel_prefix() + rel.replace(".", "_") + ".zig"

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        """import_bindings から Zig の @import を生成（§3: linker 解決済み情報を使用）。"""
        emitted: set[str] = set()
        meta_any_json: JsonVal = self.east_doc.get("meta")
        meta_json: dict[str, JsonVal] = {}
        meta_obj = pytra_json.JsonValue(meta_any_json).as_obj()
        if meta_obj is not None:
            meta_json = meta_obj.raw
        self._import_alias_map = build_import_alias_map(meta_json)
        _DECORATORS: set[str] = {"abi", "extern", "template"}
        import_bindings_json: list[JsonVal] = []
        if meta_obj is not None:
            import_bindings_arr = meta_obj.get_arr("import_bindings")
            if import_bindings_arr is not None:
                import_bindings_json = import_bindings_arr.raw
        known_nominals_by_module: dict[str, set[str]] = {
            'pytra.std.json': {'JsonObj', 'JsonArr', 'JsonValue'},
            'pytra.std.pathlib': {'Path'},
            'pytra.std.argparse': {'ArgumentParser', 'Namespace'},
        }
        known_properties_by_nominal: dict[str, set[str]] = {
            'Path': {'parent', 'name', 'stem', 'suffix'},
        }
        for binding_json in import_bindings_json:
            binding_obj = pytra_json.JsonValue(binding_json).as_obj()
            if binding_obj is None:
                continue
            binding_raw: dict[str, JsonVal] = binding_obj.raw
            module_id = self._json_dict_get_str(binding_raw, "module_id", "")
            if module_id == "":
                continue
            runtime_module_id = self._json_dict_get_str(binding_raw, "runtime_module_id", "")
            export_name = self._json_dict_get_str(binding_raw, "export_name", "")
            local_name = self._json_dict_get_str(binding_raw, "local_name", "")
            # Skip pytra.built_in (provided by py_runtime.zig)
            if module_id.startswith("pytra.built_in"):
                continue
            if module_id.startswith("pytra.core.") or runtime_module_id.startswith("pytra.core."):
                continue
            if module_id == "pytra.std.json" and export_name == "JsonVal":
                if "JsonVal" not in emitted:
                    self._emit_line("const JsonVal = pytra.JsonVal;")
                    emitted.add("JsonVal")
                continue
            if module_id in {"pytra.types", "pytra.typing", "typing", "typing.cast"} or module_id.startswith("pytra.types.") or module_id.startswith("pytra.typing."):
                if not (module_id == "typing" and export_name != "cast"):
                    continue
            if module_id == "typing" and export_name == "cast":
                continue
            if "typing" in module_id and (export_name == "cast" or local_name == "cast"):
                continue
            binding_kind = self._json_dict_get_str(binding_raw, "resolved_binding_kind", "")
            if binding_kind == "":
                binding_kind = self._json_dict_get_str(binding_raw, "binding_kind", "")
            nominal_module_id = runtime_module_id if runtime_module_id != "" else module_id
            empty_nominals: set[str] = set()
            for nominal in known_nominals_by_module.get(nominal_module_id, empty_nominals):
                self._import_alias_map[nominal] = nominal
                self._known_imported_nominals.add(nominal)
                empty_properties: set[str] = set()
                prop_values: set[str] = set()
                for prop in known_properties_by_nominal.get(nominal, empty_properties):
                    prop_values.add(prop)
                self._class_properties[nominal] = prop_values
            if export_name in _DECORATORS:
                continue
            candidate_module: str = runtime_module_id if runtime_module_id != "" else module_id
            imported_module: str = candidate_module
            if candidate_module == 'math':
                import_path = self._root_rel_prefix() + "std/math_native.zig"
                safe_mod = "math_native"
            elif candidate_module == 'time':
                import_path = self._root_rel_prefix() + "std/time_native.zig"
                safe_mod = "time_native"
            else:
                if not candidate_module.startswith("pytra.") and not candidate_module.startswith(".") and not candidate_module.startswith("toolchain."):
                    canonical = canonical_runtime_module_id(candidate_module)
                    if isinstance(canonical, str) and canonical != "" and canonical != candidate_module:
                        imported_module = canonical
                        candidate_module = canonical
                if not candidate_module.startswith("pytra.") and not candidate_module.startswith(".") and not candidate_module.startswith("toolchain."):
                    continue
                import_path = self._module_id_to_import_path(imported_module)
                safe_mod = _safe_ident(imported_module.replace(".", "_"), "mod")
            if safe_mod not in emitted:
                self._emit_line("const " + safe_mod + " = @import(\"" + import_path + "\");")
                emitted.add(safe_mod)
                self._top_level_runtime_inits.append((safe_mod + ".__pytra_init_module()", ""))
                if imported_module == "pytra.std.sys" and safe_mod == "pytra_std_sys":
                    self._uses_pytra_std_sys = True
            if binding_kind == "module" and local_name != "":
                safe_local = _safe_ident(local_name, "mod")
                if safe_local != safe_mod and safe_local not in emitted:
                    self._emit_line("const " + safe_local + " = " + safe_mod + ";")
                    emitted.add(safe_local)
                empty_nominals_for_module: set[str] = set()
                for nominal in known_nominals_by_module.get(nominal_module_id, empty_nominals_for_module):
                    if nominal not in emitted:
                        self._emit_line("const " + nominal + " = " + safe_local + "." + nominal + ";")
                        emitted.add(nominal)
            # Symbol binding: add const alias (e.g. const Path = pathlib.Path;)
            if binding_kind == "symbol" and local_name != "":
                safe_local = _safe_ident(local_name, "fn")
                if safe_local != safe_mod and safe_local not in emitted:
                    self._emit_line("const " + safe_local + " = " + safe_mod + "." + _safe_ident(export_name, "fn") + ";")
                    emitted.add(safe_local)

    def _emit_raise_stmt(self, stmt: dict[str, Any]) -> None:
        renderer = self._make_stmt_renderer()
        try_label = self._try_label_stack[-1] if self._try_depth > 0 and len(self._try_label_stack) > 0 else ""
        return_stmt = self._exception_return_stmt()
        exc_any = stmt.get("exc")
        if exc_any is None:
            renderer.state.indent_level = self.indent
            renderer.emit_bare_raise_restore()
            renderer.state.indent_level = self.indent
            renderer.emit_raise_propagation(try_label, return_stmt)
            self._sync_from_stmt_renderer(renderer)
            return
        if isinstance(exc_any, dict):
            exc_node: dict[str, Any] = exc_any
            if exc_node.get("kind") == "Call":
                fn_any = exc_node.get("func")
                if isinstance(fn_any, dict) and fn_any.get("kind") == "Name":
                    fn_name = _safe_ident(fn_any.get("id"), "")
                    args_any = exc_node.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    exc_line_expr = "0"
                    exc_msg_expr = "\"error\""
                    if len(args) > 0:
                        if len(args) >= 2:
                            exc_line_expr = self._render_expr(args[0])
                            exc_msg_expr = "pytra.to_str(" + self._render_expr(args[1]) + ")"
                        else:
                            exc_msg_expr = "pytra.to_str(" + self._render_expr(args[0]) + ")"
                    renderer.state.indent_level = self.indent
                    renderer.emit_raise_exception_state(_zig_string(fn_name), exc_msg_expr, exc_line_expr)
                    renderer.state.indent_level = self.indent
                    renderer.emit_raise_propagation(try_label, return_stmt)
                    self._sync_from_stmt_renderer(renderer)
                    return
            renderer.state.indent_level = self.indent
            renderer.emit_raise_exception_state("\"Exception\"", "pytra.to_str(" + self._render_expr(exc_node) + ")", "0")
        else:
            renderer.state.indent_level = self.indent
            renderer.emit_raise_exception_state("\"Exception\"", "\"error\"", "0")
        renderer.state.indent_level = self.indent
        renderer.emit_raise_propagation(try_label, return_stmt)
        self._sync_from_stmt_renderer(renderer)

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
        if kind == "ClosureDef":
            self._emit_closure_def(stmt)
            return
        if kind == "Return":
            val = self._render_expr(stmt.get("value"))
            if val == "null":
                ret_type = self._return_type_stack[-1] if len(self._return_type_stack) > 0 else "void"
                if ret_type.startswith("?"):
                    self._emit_line("return null;")
                elif self._is_union_storage_zig(ret_type):
                    self._emit_line("return pytra.union_new_none();")
                else:
                    self._emit_line("return;")
            else:
                ret_type = self._return_type_stack[-1] if len(self._return_type_stack) > 0 else ""
                orig_val = val
                value_node = stmt.get("value")
                value_type = self._lookup_expr_type(value_node) if isinstance(value_node, dict) else ""
                stripped_value = self._strip_optional_type(value_type) if value_type != "" else ""
                if isinstance(value_node, dict) and value_node.get("kind") == "Name":
                    name_type = self._current_type_map().get(_safe_ident(value_node.get("id"), "value"), "")
                    stripped_name = self._strip_optional_type(name_type)
                    if stripped_name != "" and self._zig_type(stripped_name) == ret_type:
                        val = val + ".?"
                if stripped_value != "" and self._zig_type(stripped_value) == ret_type:
                    val = val + ".?"
                val = self._coerce_value_to_zig_type(ret_type, value_node, val)
                if self._is_union_storage_zig(ret_type) and val == orig_val and isinstance(value_node, dict):
                    value_zig = self._zig_type(value_type) if value_type != "" else self._infer_value_zig_type(value_node)
                    if value_zig != "" and not self._is_union_storage_zig(value_zig):
                        val = "pytra.union_wrap(" + val + ")"
                self._emit_line("return " + val + ";")
            return
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value_node = stmt.get("value")
            annotation_type_expr = stmt.get("annotation_type_expr")
            # extern() 変数 → __native 委譲（spec-emitter-guide §4）
            # Unbox ラッパーを透過
            if isinstance(value_node, dict):
                if value_node.get("kind") == "Call":
                    vfunc = value_node.get("func")
                    if isinstance(vfunc, dict) and (vfunc.get("id") == "extern" or vfunc.get("id") == "@\"extern\""):
                        self._ensure_native_import()
                        decl_type = self._infer_decl_type(stmt)
                        zig_ty = self._zig_type(decl_type)
                        self._emit_line("pub const " + target + ": " + zig_ty + " = __native." + target + ";")
                        return
                elif value_node.get("kind") == "Unbox":
                    unboxed = value_node.get("value")
                    if isinstance(unboxed, dict) and unboxed.get("kind") == "Call":
                        vfunc = unboxed.get("func")
                        if isinstance(vfunc, dict) and (vfunc.get("id") == "extern" or vfunc.get("id") == "@\"extern\""):
                            self._ensure_native_import()
                            decl_type = self._infer_decl_type(stmt)
                            zig_ty = self._zig_type(decl_type)
                            self._emit_line("pub const " + target + ": " + zig_ty + " = __native." + target + ";")
                            return
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "undefined"
            raw_core_value_node = self._unwrap_box_unbox(value_node)
            core_value_node: Any = raw_core_value_node
            if isinstance(raw_core_value_node, dict):
                core_value_node = self._json_dict_to_any(raw_core_value_node)
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type = self._infer_decl_type(stmt)
                decl_type = self._refine_unknown_decl_type(decl_type, value_node)
                decl_type = self._runtime_decl_type(decl_type, value_node)
                if isinstance(core_value_node, dict) and core_value_node.get("kind") == "Dict" and decl_type.startswith("dict["):
                    value = self._render_dict_with_decl_type(core_value_node, decl_type)
                if isinstance(core_value_node, dict) and core_value_node.get("kind") == "List" and decl_type.startswith("list["):
                    value = self._render_list_with_decl_type(core_value_node, decl_type)
                typed_empty = self._render_typed_empty_container(core_value_node, decl_type)
                if typed_empty != "":
                    value = typed_empty
                if decl_type != "":
                    self._current_type_map()[target_name] = self._merge_decl_type(
                        self._current_type_map().get(target_name, ""),
                        decl_type,
                        stmt.get("decl_type_expr") if stmt.get("decl_type_expr") is not None else annotation_type_expr,
                    )
                    self._storage_type_setdefault(target_name, decl_type)
                is_lambda_value = isinstance(value_node, dict) and value_node.get("kind") == "Lambda"
                is_callable_decl = self._is_callable_type(decl_type)
                if is_lambda_value and len(self._lambda_local_stack) > 0:
                    self._add_current_lambda_local(target_name)
                zig_ty = self._zig_type(decl_type)
                if isinstance(core_value_node, dict) and core_value_node.get("kind") == "Dict" and zig_ty == "std.StringHashMap(" + self._union_storage_zig() + ")":
                    value = self._render_union_dict_literal(core_value_node)
                optional_dict_get = self._render_optional_dict_get(core_value_node, decl_type)
                if optional_dict_get != "":
                    value = optional_dict_get
                # PyObject fallback の場合、値の resolved_type で型を補正
                if zig_ty == "pytra.PyObject" and isinstance(value_node, dict):
                    val_zig = self._preferred_value_zig_type(decl_type, value_node)
                    if val_zig != "pytra.PyObject":
                        zig_ty = val_zig
                if self._is_union_storage_zig(zig_ty) and isinstance(value_node, dict) and value_node.get("kind") == "Unbox" and isinstance(core_value_node, dict):
                    value = self._render_expr(core_value_node)
                # VarDecl で既に宣言済みなら再代入
                already_declared = len(self._local_var_stack) > 0 and target_name in self._current_local_vars()
                if already_declared:
                    if value_node is not None:
                        self._emit_line(target + " = " + value + ";")
                    return
                if len(self._local_var_stack) > 0:
                    self._add_current_local_var(target_name)
                decl_kw = "var" if (self._is_var_mutated(target_name) or self._is_name_reassigned(target_name) or self._needs_var_for_type(decl_type) or zig_ty == "pytra.Obj") else "const"
                if value_node is None and bool(stmt.get("declare")):
                    self._emit_line("var " + target + ": " + zig_ty + " = undefined;")
                else:
                    if is_lambda_value or is_callable_decl:
                        self._emit_line(decl_kw + " " + target + " = " + value + ";")
                        self._record_decl_line(target_name)
                        return
                    # 空 dict リテラル: decl_type の値型で初期化
                    if isinstance(value_node, dict) and value_node.get("kind") == "Dict":
                        entries = value_node.get("entries")
                        if (entries is None or (isinstance(entries, list) and len(entries) == 0)):
                            if decl_type.startswith("dict[") and decl_type.endswith("]"):
                                parts = self._split_generic(decl_type[5:-1])
                                if len(parts) == 2:
                                    val_zig = self._zig_type(parts[1].strip())
                                    value = "pytra.make_str_dict(" + val_zig + ")"
                    # 型キャスト挿入: i64 変数に f64 値、f64 変数に i64 値
                    val_type = self._get_expr_type(value_node) if isinstance(value_node, dict) else ""
                    _INT_T = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                    _FLOAT_T = {"float64", "float32", "float"}
                    norm_decl = self._normalize_type(decl_type)
                    if norm_decl in _INT_T and (val_type in _FLOAT_T or self._expr_is_float_like(value_node)) and "@intFromFloat(" not in value:
                        value = "@as(i64, @intFromFloat(" + value + "))"
                    elif norm_decl in _FLOAT_T and val_type in _INT_T and not self._expr_is_float_like(value_node):
                        value = "@as(f64, @floatFromInt(" + value + "))"
                    value = self._coerce_value_to_zig_type(zig_ty, value_node, value)
                    self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                    self._record_decl_line(target_name)
                    norm_type = self._normalize_type(decl_type)
                    if norm_type in self.class_names and self._has_vtable(norm_type) and not (self._is_subclass_of(norm_type, "IntEnum") or self._is_subclass_of(norm_type, "IntFlag")):
                        self._emit_line("defer " + target + ".release();")

            else:
                self._emit_line(target + " = " + value + ";")
            return
        if kind == "Assign":
            assign_value = stmt.get("value")
            assign_value_node: Any = assign_value
            if isinstance(assign_value, dict):
                assign_value_node = self._json_dict_to_any(assign_value)
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                td2: dict[str, Any] = target_any
                if td2.get("kind") == "Name":
                    alias_name = _safe_ident(td2.get("id"), "")
                    if _starts_with_upper(alias_name):
                        value_any = stmt.get("value")
                        if isinstance(value_any, dict) and value_any.get("kind") in {"Name", "Subscript"}:
                            return
                if td2.get("kind") == "Tuple":
                    self._emit_tuple_assign(target_any, assign_value_node)
                    return
                # Subscript 代入: list[idx] = val → list_set
                if td2.get("kind") == "Subscript":
                    sub_val = td2.get("value")
                    sub_val_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
                    if sub_val_type.startswith("list[") or sub_val_type in {"bytearray", "bytes"}:
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(td2.get("slice"))
                        val_expr = self._render_expr(assign_value_node)
                        elem = "i64"
                        if sub_val_type.startswith("list[") and sub_val_type.endswith("]"):
                            elem = self._zig_type(sub_val_type[5:-1].strip())
                        elif sub_val_type in {"bytearray", "bytes"}:
                            elem = "u8"
                        if elem in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            val_expr = "@intCast(" + val_expr + ")"
                        self._emit_line("pytra.list_set(" + obj_expr + ", " + elem + ", " + idx_expr + ", " + val_expr + ");")
                        return
                    # dict[key] = val → .put(key, val)
                    if sub_val_type.startswith("dict["):
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(td2.get("slice"))
                        parts: list[str] = []
                        if sub_val_type.endswith("]"):
                            parts = self._split_generic(sub_val_type[5:-1])
                        if len(parts) == 2 and self._normalize_type(parts[0].strip()) != "str":
                            idx_expr = "pytra.to_str(" + idx_expr + ")"
                        val_expr = self._render_expr(assign_value_node)
                        val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(sub_val_type)
                        if self._is_union_storage_zig(val_zig):
                            val_expr = "pytra.union_wrap(" + val_expr + ")"
                        self._emit_line(obj_expr + ".put(" + idx_expr + ", " + val_expr + ") catch {};")
                        return
                target = self._render_target(target_any)
                value = self._render_expr(assign_value_node)
                if td2.get("kind") == "Name":
                    target_name = _safe_ident(td2.get("id"), "value")
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(assign_value_node)
                    decl_type = self._refine_unknown_decl_type(decl_type, assign_value_node)
                    decl_type = self._runtime_decl_type(decl_type, assign_value_node)
                    if isinstance(assign_value_node, dict) and assign_value_node.get("kind") == "Dict" and decl_type.startswith("dict["):
                        value = self._render_dict_with_decl_type(assign_value_node, decl_type)
                    typed_empty = self._render_typed_empty_container(assign_value_node, decl_type)
                    if typed_empty != "":
                        value = typed_empty
                    if decl_type != "":
                        self._current_type_map()[target_name] = self._merge_decl_type(
                            self._current_type_map().get(target_name, ""),
                            decl_type,
                            stmt.get("decl_type_expr"),
                        )
                        self._storage_type_setdefault(target_name, decl_type)
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._add_current_local_var(target_name)
                        is_lambda_value = isinstance(assign_value_node, dict) and assign_value_node.get("kind") == "Lambda"
                        is_callable_decl = self._is_callable_type(decl_type)
                        if is_lambda_value and len(self._lambda_local_stack) > 0:
                            self._add_current_lambda_local(target_name)
                        zig_ty = self._zig_type(decl_type)
                        optional_dict_get = self._render_optional_dict_get(assign_value_node, decl_type)
                        if optional_dict_get != "":
                            value = optional_dict_get
                        # PyObject fallback → 値の型推論で型を補正
                        if zig_ty == "pytra.PyObject" and isinstance(assign_value_node, dict):
                            val_zig = self._preferred_value_zig_type(decl_type, assign_value_node)
                            if val_zig != "pytra.PyObject":
                                zig_ty = val_zig
                                decl_type = self._lookup_expr_type(assign_value_node)
                                self._current_type_map()[target_name] = self._merge_decl_type(
                                    self._current_type_map().get(target_name, ""),
                                    decl_type,
                                    stmt.get("decl_type_expr"),
                                )
                        decl_kw = "var" if (self._is_var_mutated(target_name) or self._is_name_reassigned(target_name) or self._needs_var_for_type(decl_type) or zig_ty == "pytra.Obj") else "const"
                        if is_lambda_value or is_callable_decl:
                            self._emit_line(decl_kw + " " + target + " = " + value + ";")
                            self._record_decl_line(target_name)
                            return
                        if self._is_union_storage_zig(zig_ty) and isinstance(assign_value_node, dict) and assign_value_node.get("kind") == "Unbox":
                            core_value = self._unwrap_box_unbox(assign_value_node)
                            if isinstance(core_value, dict):
                                value = self._render_expr(core_value)
                        value = self._coerce_value_to_zig_type(zig_ty, assign_value_node, value)
                        self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                        self._record_decl_line(target_name)
                        norm_type = self._normalize_type(decl_type)
                        if norm_type in self.class_names and self._has_vtable(norm_type) and not (self._is_subclass_of(norm_type, "IntEnum") or self._is_subclass_of(norm_type, "IntFlag")):
                            self._emit_line("defer " + target + ".release();")
                        return
                # 既存変数への再代入 — pytra.Obj なら release + retain
                if td2.get("kind") == "Name":
                    self._mark_decl_mutable(target_name)
                    old_type = self._current_type_map().get(target_name, "")
                    if self._normalize_type(old_type) in self.class_names and self._has_vtable(self._normalize_type(old_type)):
                        self._emit_line(target + ".release();")
                        self._emit_line(target + " = " + value + ".retain();")
                        return
                # 型キャスト: 変数型と値型の不一致を補正
                if td2.get("kind") == "Name":
                    var_type = self._current_type_map().get(target_name, "")
                    val_type = self._get_expr_type(assign_value_node)
                    norm_var = self._normalize_type(var_type)
                    _INT_T = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                    _FLOAT_T = {"float64", "float32", "float"}
                    if norm_var in _INT_T and (val_type in _FLOAT_T or self._expr_is_float_like(assign_value_node)) and "@intFromFloat(" not in value:
                        value = "@as(i64, @intFromFloat(" + value + "))"
                    elif norm_var in _FLOAT_T and val_type in _INT_T and not self._expr_is_float_like(assign_value_node):
                        value = "@as(f64, @floatFromInt(" + value + "))"
                    value = self._coerce_value_to_zig_type(self._zig_type(var_type), assign_value_node, value)
                elif td2.get("kind") == "Attribute":
                    owner_node = td2.get("value")
                    field_type = ""
                    if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                        owner_name = _safe_ident(owner_node.get("id"), "")
                        if owner_name == "self" and self._current_class_name != "":
                            owner_type = self._current_class_name
                        else:
                            owner_type = self._normalize_type(self._current_type_map().get(owner_name, ""))
                            if owner_type.startswith("*"):
                                owner_type = owner_type[1:]
                        field_name = _safe_ident(td2.get("attr"), "")
                        field_type = self._class_field_types.get(owner_type, {}).get(field_name, "")
                    if field_type != "":
                        value = self._coerce_value_to_zig_type(self._zig_type(field_type), assign_value_node, value)
                self._emit_line(target + " = " + value + ";")
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                first_target: dict[str, Any] = self._json_dict_to_any(targets[0])
                if first_target.get("kind") == "Tuple":
                    self._emit_tuple_assign(first_target, assign_value_node)
                    return
                target = self._render_target(first_target)
                value = self._render_expr(assign_value_node)
                if first_target.get("kind") == "Name":
                    target_name = _safe_ident(first_target.get("id"), "value")
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(assign_value_node)
                    decl_type = self._refine_unknown_decl_type(decl_type, assign_value_node)
                    decl_type = self._runtime_decl_type(decl_type, assign_value_node)
                    if isinstance(assign_value_node, dict) and assign_value_node.get("kind") == "Dict" and decl_type.startswith("dict["):
                        value = self._render_dict_with_decl_type(assign_value_node, decl_type)
                    if decl_type != "":
                        self._current_type_map()[target_name] = self._merge_decl_type(
                            self._current_type_map().get(target_name, ""),
                            decl_type,
                            stmt.get("decl_type_expr"),
                        )
                        self._storage_type_setdefault(target_name, decl_type)
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._add_current_local_var(target_name)
                        is_lambda_value = isinstance(assign_value_node, dict) and assign_value_node.get("kind") == "Lambda"
                        is_callable_decl = self._is_callable_type(decl_type)
                        if is_lambda_value and len(self._lambda_local_stack) > 0:
                            self._add_current_lambda_local(target_name)
                        zig_ty = self._zig_type(decl_type)
                        optional_dict_get = self._render_optional_dict_get(assign_value_node, decl_type)
                        if optional_dict_get != "":
                            value = optional_dict_get
                        # PyObject fallback → 値の型推論で型を補正
                        if zig_ty == "pytra.PyObject" and isinstance(assign_value_node, dict):
                            val_zig = self._infer_value_zig_type(assign_value_node)
                            if val_zig != "pytra.PyObject":
                                zig_ty = val_zig
                                decl_type = self._lookup_expr_type(assign_value_node)
                                self._current_type_map()[target_name] = self._merge_decl_type(
                                    self._current_type_map().get(target_name, ""),
                                    decl_type,
                                    stmt.get("decl_type_expr"),
                                )
                        decl_kw = "var" if (self._is_var_mutated(target_name) or self._is_name_reassigned(target_name) or self._needs_var_for_type(decl_type) or zig_ty == "pytra.Obj") else "const"
                        if is_lambda_value or is_callable_decl:
                            self._emit_line(decl_kw + " " + target + " = " + value + ";")
                            self._record_decl_line(target_name)
                            return
                        value = self._coerce_value_to_zig_type(zig_ty, assign_value_node, value)
                        self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                        self._record_decl_line(target_name)
                        return
                    self._mark_decl_mutable(target_name)
                    value = self._coerce_value_to_zig_type(self._zig_type(self._current_type_map().get(target_name, "")), assign_value_node, value)
                self._emit_line(target + " = " + value + ";")
                return
            raise RuntimeError("lang=zig unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            target_type = self._lookup_expr_type(stmt.get("target")) if isinstance(stmt.get("target"), dict) else ""
            if op == "Add" and target_type == "str":
                self._emit_line(target + " = pytra.str_concat(" + target + ", " + value + ");")
                return
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
            if expr_text == "":
                return
            if isinstance(value_any, dict) and value_any.get("kind") == "Call":
                if " = " in expr_text and not expr_text.lstrip().startswith("__call_blk_"):
                    self._emit_line(expr_text + ";")
                else:
                    self._emit_line("_ = " + expr_text + ";")
            else:
                self._emit_line("_ = " + expr_text + ";")
            return
        if kind == "Raise":
            self._emit_raise_stmt(stmt)
            return
        if kind == "Try":
            try_renderer = self._make_stmt_renderer()
            try_renderer.emit_try_stmt(stmt)
            self._sync_from_stmt_renderer(try_renderer)
            return
        if kind == "With":
            with_renderer = self._make_stmt_renderer()
            items = stmt.get("items")
            if isinstance(items, list) and len(items) > 0:
                context_expr = stmt.get("context_expr")
                body = self._dict_list(stmt.get("body"))
                enter_type = str(stmt.get("with_enter_type", ""))
                var_name_any = stmt.get("var_name")
                var_name = _safe_ident(var_name_any, "ctx") if isinstance(var_name_any, str) and var_name_any != "" else ""
                ctx_name = with_renderer.next_with_context_name()
                with_blk = with_renderer.next_with_block_name()
                ctx_type = self._lookup_expr_type(context_expr) if isinstance(context_expr, dict) else ""
                ctx_expr = self._render_expr(context_expr)
                self._emit_line("const " + ctx_name + " = " + ctx_expr + ";")
                if var_name != "":
                    self._current_type_map()[var_name] = enter_type
                    already_declared = len(self._local_var_stack) > 0 and var_name in self._current_local_vars()
                    if enter_type == "TextIOWrapper":
                        if already_declared:
                            with_renderer.state.indent_level = self.indent
                            with_renderer.emit_with_context_bind(var_name, ctx_name, enter_type, False)
                        else:
                            zig_enter_type = self._zig_type(enter_type) if enter_type != "" else "pytra.PyObject"
                            self._emit_line("var " + var_name + ": " + zig_enter_type + " = " + ctx_name + ";")
                    else:
                        zig_enter_type = self._zig_type(enter_type) if enter_type != "" else "pytra.PyObject"
                        if already_declared:
                            self._emit_line(var_name + " = " + ctx_name + ".__enter__();")
                        else:
                            self._emit_line("var " + var_name + ": " + zig_enter_type + " = " + ctx_name + ".__enter__();")
                    if not already_declared and len(self._local_var_stack) > 0:
                        self._add_current_local_var(var_name)
                elif enter_type != "TextIOWrapper":
                    with_renderer.state.indent_level = self.indent
                    with_renderer.emit_with_fallback_enter(ctx_name, enter_type)
                self._emit_line(with_renderer.render_try_body_open(with_blk))
                self.indent += 1
                self._try_depth += 1
                self._try_label_stack.append(with_blk)
                for sub in body:
                    self._emit_stmt(sub)
                    post_stmt = with_renderer.render_try_body_post_stmt_stmt(sub, with_blk)
                    if post_stmt != "":
                        self._emit_line(post_stmt)
                self._try_label_stack.pop()
                self._try_depth -= 1
                self.indent -= 1
                self._emit_line(with_renderer.render_try_body_close(with_blk))
                if enter_type == "TextIOWrapper":
                    with_renderer.state.indent_level = self.indent
                    with_renderer.emit_with_close_fallback(ctx_name, enter_type)
                else:
                    with_renderer.state.indent_level = self.indent
                    with_renderer.emit_with_fallback_exit(ctx_name, enter_type)
            else:
                self._emit_line("// unsupported with shape")
            self._sync_from_stmt_renderer(with_renderer)
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
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
        if kind == "VarDecl":
            self._emit_var_decl(stmt)
            return
        raise RuntimeError("lang=zig unsupported stmt kind: " + str(kind))

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node).

        If the variable is captured by a nested for loop (ForCore target_plan),
        skip the VarDecl to avoid shadow errors in Zig.
        """
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type = self._dict_get_str(stmt, "type", "").strip()
        if var_type != "":
            self._current_type_map()[name] = var_type
        if len(self._local_var_stack) > 0:
            self._add_current_local_var(name)
        self._hoisted_var_names.add(name)
        # object/unknown 型は具体型を推論 (PyObject は i64 alias なので float 代入に不適)
        if var_type in {"object", "unknown", "Any", ""}:
            scope_body = stmt.get("scope_body")
            if isinstance(scope_body, list):
                inferred = self._infer_hoisted_var_type_from_scope(name, self._dict_list(scope_body))
            else:
                inferred = self._infer_hoisted_var_type_from_body(name)
            if inferred != "":
                var_type = inferred
                self._current_type_map()[name] = var_type
        zig_ty = self._zig_type(var_type) if var_type != "" else "pytra.PyObject"
        self._emit_line("var " + name + ": " + zig_ty + " = undefined;")

    def _infer_hoisted_var_type_from_scope(self, name: str, scope_body: list[dict[str, Any]]) -> str:
        return self._find_first_assign_type(scope_body, name)

    def _infer_hoisted_var_type_from_body(self, name: str) -> str:
        """VarDecl の型が object/unknown の場合、EAST 全体の Assign から具体型を推論。"""
        body = self._dict_list(self._json_to_any(self.east_doc.get("body")))
        main_guard = self._dict_list(self._json_to_any(self.east_doc.get("main_guard_body")))
        result = self._find_first_assign_type(body, name)
        if result == "":
            result = self._find_first_assign_type(main_guard, name)
        return result

    def _find_first_assign_type(self, nodes: list[dict[str, Any]], name: str) -> str:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kind = self._dict_get_str(node, "kind", "")
            if kind == "Assign" or kind == "AnnAssign":
                target = node.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    if _safe_ident(target.get("id"), "") == name:
                        decl_type = self._infer_decl_type(node)
                        if decl_type != "" and decl_type != "unknown":
                            return decl_type
                        val = node.get("value")
                        if isinstance(val, dict):
                            t = self._lookup_expr_type(val)
                            if t != "" and t != "unknown":
                                return t
            # Recurse into blocks
            block_keys: list[str] = ["body", "orelse", "finalbody"]
            for key in block_keys:
                sub = node.get(key)
                if isinstance(sub, list):
                    result = self._find_first_assign_type(self._dict_list(sub), name)
                    if result != "":
                        return result
        return ""

    def _is_for_capture_var(self, name: str) -> bool:
        """Check if name is used as a for-loop capture variable in current function body."""
        # Walk the current function's body to find ForCore with matching target
        if len(self._local_var_stack) == 0:
            return False
        # Search east_doc body recursively for ForCore target matching name
        body = self._json_to_any(self.east_doc.get("body"))
        return self._find_for_capture(body, name)

    def _find_for_capture(self, nodes: Any, name: str) -> bool:
        if not isinstance(nodes, list):
            return False
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kind = node.get("kind", "")
            if kind == "ForCore":
                tp = node.get("target_plan")
                if isinstance(tp, dict) and tp.get("kind") == "NameTarget":
                    if _safe_ident(tp.get("id"), "") == name:
                        return True
                if self._find_for_capture(self._dict_list(node.get("body")), name):
                    return True
            elif kind == "ForRange":
                target = node.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    if _safe_ident(target.get("id"), "") == name:
                        return True
                if self._find_for_capture(self._dict_list(node.get("body")), name):
                    return True
            elif kind == "FunctionDef":
                if self._find_for_capture(self._dict_list(node.get("body")), name):
                    return True
            elif kind == "While":
                if self._find_for_capture(self._dict_list(node.get("body")), name):
                    return True
            elif kind == "If":
                if self._find_for_capture(self._dict_list(node.get("body")), name):
                    return True
                if self._find_for_capture(self._dict_list(node.get("orelse")), name):
                    return True
        return False

    def _resolve_arg_zig_type(self, arg_name: str, raw_name: Any, arg_types: dict[str, Any]) -> str:
        """引数の型を EAST3 の arg_types から解決して Zig 型を返す。"""
        raw_key = raw_name if isinstance(raw_name, str) else ""
        py_type = self._dict_get_str(arg_types, raw_key, "")
        if py_type == "":
            py_type = self._dict_get_str(arg_types, arg_name, "")
        py_type = py_type.strip()
        if py_type.find("|") != -1:
            parts = [self._normalize_type(p.strip()) for p in py_type.split("|")]
            non_none = [part for part in parts if part != "None"]
            if len(non_none) == 1 and len(non_none) != len(parts):
                if self._is_callable_type(non_none[0]):
                    return self._zig_callable_type(non_none[0], optional=True)
                return "?" + self._zig_type(non_none[0])
        if py_type.find("|") != -1:
            parts = [self._normalize_type(p.strip()) for p in py_type.split("|")]
            for part in parts:
                if part in self.class_names or part in self._import_alias_map:
                    return "anytype"
        return self._zig_type(py_type)

    def _ensure_native_import(self) -> None:
        """__native import を1度だけ出力する（@extern 関数/変数の委譲用）。"""
        if not self._extern_native_emitted:
            ectx = self._get_emit_context()
            module_id = self._dict_get_str(ectx, "module_id", "")
            clean_id = module_id.replace(".east", "")
            parts = clean_id.split(".")
            leaf = parts[-1] if len(parts) > 0 else "unknown"
            native_path = leaf + "_native.zig"
            self._emit_line("const __native = @import(\"" + native_path + "\");")
            self._extern_native_emitted = True

    def _emit_extern_delegation(self, stmt: dict[str, Any], name: str) -> None:
        """@extern 関数の native 委譲コードを生成（spec-emitter-guide §4/§5.1）。"""
        self._ensure_native_import()
        # 引数リスト
        arg_order_any = stmt.get("arg_order")
        args: list[Any] = []
        if isinstance(arg_order_any, list):
            for item in arg_order_any:
                args.append(item)
        arg_types_any = stmt.get("arg_types")
        arg_types: dict[str, Any] = {}
        if isinstance(arg_types_any, dict):
            arg_types = self._json_dict_to_any(arg_types_any)
        arg_strs: list[str] = []
        call_args: list[str] = []
        for a in args:
            safe_name = _safe_ident(a, "arg")
            arg_key = a if isinstance(a, str) else ""
            py_t = self._dict_get_str(arg_types, arg_key, "").strip()
            zig_ty = self._zig_type(py_t)
            arg_strs.append(safe_name + ": " + zig_ty)
            call_args.append(safe_name)
        ret_py = self._dict_get_str(stmt, "return_type", "").strip()
        ret_zig = self._zig_type(ret_py) if ret_py != "" else "void"
        if ret_zig == "pytra.PyObject":
            ret_zig = "f64"  # extern 関数の戻り値は通常スカラー
        sig = "pub fn " + name + "(" + ", ".join(arg_strs) + ") " + ret_zig
        if ret_zig == "void":
            self._emit_line(sig + " { __native." + name + "(" + ", ".join(call_args) + "); }")
        else:
            self._emit_line(sig + " { return __native." + name + "(" + ", ".join(call_args) + "); }")

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn_")
        if name == "main":
            name = "__pytra_main"
        self._module_function_types[name] = self._closure_callable_type(stmt)
        param_zig_types_empty: list[str] = []
        self._module_function_param_zig_types[name] = param_zig_types_empty
        # @extern decorator → native 委譲コードを生成（spec-emitter-guide §4）
        decorators = stmt.get("decorators")
        if isinstance(decorators, list) and "extern" in decorators:
            self._emit_extern_delegation(stmt, name)
            return
        arg_order_any = stmt.get("arg_order")
        args: list[Any] = []
        if isinstance(arg_order_any, list):
            for item in arg_order_any:
                args.append(item)
        vararg_name_raw = stmt.get("vararg_name")
        vararg_name = vararg_name_raw if isinstance(vararg_name_raw, str) and vararg_name_raw != "" else ""
        if isinstance(vararg_name_raw, str) and vararg_name_raw != "":
            args.append(vararg_name_raw)
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        arg_strs: list[str] = []
        # Zig parameters are immutable; detect reassigned params and rename.
        reassigned_params = _collect_reassigned_params(stmt)
        mutable_copies: list[tuple[str, str, str]] = []
        arg_types_any = stmt.get("arg_types")
        arg_types: dict[str, Any] = {}
        if isinstance(arg_types_any, dict):
            arg_types = self._json_dict_to_any(arg_types_any)
        arg_usage = stmt.get("arg_usage")
        if isinstance(arg_usage, dict):
            arg_usage = self._json_dict_to_any(arg_usage)
        else:
            arg_usage = {}
        module_id = self._current_module_id()
        # Collect sibling method names for shadowing detection (§ Zig param shadow)
        sibling_method_names: set[str] = set()
        if self._current_class_name != "":
            for sib in self._current_class_methods:
                sib_name = self._dict_get_str(sib, "name", "") if isinstance(sib, dict) else ""
                if sib_name != "":
                    sibling_method_names.add(sib_name)
        fn_live_body = self._strip_dead_branches(stmt.get("body"))
        i = 0
        while i < len(arg_names):
            raw_name_any = args[i] if i < len(args) else arg_names[i]
            raw_name = self._any_str(raw_name_any, "")
            zig_ty = self._resolve_arg_zig_type(arg_names[i], raw_name, arg_types)
            if vararg_name != "" and raw_name == vararg_name:
                elem_ty = "pytra.PyObject"
                if len(self._module_function_param_zig_types[name]) > 0:
                    elem_ty = self._module_function_param_zig_types[name][-1]
                zig_ty = "[]const " + elem_ty
                self._module_function_vararg_index[name] = i
            if module_id == "pytra.utils.assertions" and name == "py_assert_eq" and i < 2:
                zig_ty = "anytype"
            if module_id == "pytra.utils.assertions" and name == "py_assert_stdout" and i == 1:
                zig_ty = "anytype"
            self._module_function_param_zig_types[name].append(zig_ty)
            param_name = arg_names[i]
            if raw_name == "_":
                param_name = "_"
                arg_names[i] = "_"
                arg_strs.append(param_name + ": " + zig_ty)
                i += 1
                continue
            # Check unused: EAST3 arg_usage or body scan (excluding dead branches)
            if raw_name != "":
                is_unused = not self._body_uses_name(fn_live_body, raw_name)
            else:
                is_unused = not self._body_uses_name(fn_live_body, param_name)
            if is_unused:
                param_name = "_"
            # Rename param if it shadows a sibling method name
            elif raw_name in sibling_method_names and raw_name != name:
                param_name = param_name + "_param"
                arg_names[i] = param_name
            # Reassigned params or mutable container params: rename and copy to var
            py_t = self._dict_get_str(arg_types, raw_name, "")
            if py_t == "":
                py_t = self._dict_get_str(arg_types, arg_names[i], "")
            py_t = py_t.strip()
            norm_t = self._normalize_type(py_t)
            needs_mut = False
            if norm_t.startswith("list[") or norm_t in {"bytearray", "bytes"}:
                # body 内で .append/.extend 等が呼ばれるか or subscript 代入があるか
                mutated_in_body = self._scan_mutated_vars(stmt.get("body"))
                if arg_names[i] in mutated_in_body:
                    needs_mut = True
            is_reassigned = raw_name in reassigned_params or param_name in reassigned_params
            if is_reassigned or needs_mut:
                param_alias = _mutable_param_name(arg_names[i])
                decl_kw = "var" if is_reassigned else "const"
                mutable_copies.append((arg_names[i], param_alias, decl_kw))
                arg_strs.append(param_alias + ": " + zig_ty)
            else:
                arg_strs.append(param_name + ": " + zig_ty)
            i += 1
        ret_py = self._dict_get_str(stmt, "return_type", "").strip()
        ret_type = self._zig_type(ret_py)
        fn_kw = "pub fn" if self.is_submodule else "fn"
        self._emit_line(fn_kw + " " + name + "(" + ", ".join(arg_strs) + ") " + ret_type + " {")
        self.indent += 1
        self._function_depth += 1
        body_start = len(self.lines)
        # Copy renamed params to mutable local vars
        for orig_name, param_alias, decl_kw in mutable_copies:
            self._emit_line(decl_kw + " " + orig_name + " = " + param_alias + ";")
            if decl_kw == "var":
                self._emit_line("_ = &" + orig_name + ";")
        empty_rename: dict[str, str] = {}
        self._param_rename_stack.append(empty_rename)
        self._push_function_context(stmt, arg_names, args)
        existing_vardecls = self._collect_existing_vardecl_names(stmt.get("body"))
        top_level_assigned = self._collect_top_level_assigned_names(stmt.get("body"))
        for hoisted_name in sorted(self._collect_branch_assigned_names(stmt.get("body"))):
            if hoisted_name not in existing_vardecls and hoisted_name not in top_level_assigned and hoisted_name not in self._current_local_vars():
                self._emit_var_decl({"kind": "VarDecl", "name": hoisted_name, "scope_body": stmt.get("body")})
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self._param_rename_stack.pop()
        self._function_depth -= 1
        self.indent -= 1
        if self._is_union_storage_zig(ret_type):
            prefix_lines: list[str] = []
            line_index = 0
            while line_index < body_start:
                prefix_lines.append(self.lines[line_index])
                line_index += 1
            body_lines: list[str] = []
            while line_index < len(self.lines):
                body_lines.append(self.lines[line_index])
                line_index += 1
            self.lines = prefix_lines + self._wrap_union_return_lines(body_lines)
        self._emit_line("}")
        self._emit_line("")

    def _closure_callable_type(self, stmt: dict[str, Any]) -> str:
        arg_order_any = stmt.get("arg_order")
        args: list[Any] = []
        if isinstance(arg_order_any, list):
            for item in arg_order_any:
                args.append(item)
        arg_types_any = stmt.get("arg_types")
        arg_types: dict[str, Any] = {}
        if isinstance(arg_types_any, dict):
            arg_types = self._json_dict_to_any(arg_types_any)
        ret_type = self._dict_get_str(stmt, "return_type", "None").strip()
        if ret_type == "":
            ret_type = "None"
        sig_args: list[str] = []
        for raw_name in args:
            raw_key = raw_name if isinstance(raw_name, str) else ""
            raw_type = self._dict_get_str(arg_types, raw_key, "Any").strip()
            sig_args.append(raw_type if raw_type != "" else "Any")
        return "callable[[" + ", ".join(sig_args) + "], " + ret_type + "]"

    def _emit_closure_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "closure")
        self._current_type_map()[name] = self._closure_callable_type(stmt)
        if len(self._local_var_stack) > 0:
            self._add_current_local_var(name)
        decl_kw = "var" if self._is_var_mutated(name) else "const"
        captures_any = stmt.get("captures")
        captures = captures_any if isinstance(captures_any, list) else []
        capture_fields: list[tuple[str, str, str]] = []
        capture_rewrites: dict[str, str] = {}
        init_parts: list[str] = []
        for cap in captures:
            if not isinstance(cap, dict):
                continue
            cap_name = _safe_ident(cap.get("name"), "cap")
            cap_type = str(cap.get("type") or "Any")
            cap_mode = str(cap.get("mode") or "readonly")
            field_type = self._zig_type(cap_type)
            init_expr = cap_name
            rewrite_expr = "self." + cap_name
            if cap_mode == "mutable":
                field_type = "*" + field_type
                init_expr = "&" + cap_name
                rewrite_expr = "self." + cap_name + ".*"
            capture_fields.append((cap_name, field_type, init_expr))
            capture_rewrites[cap_name] = rewrite_expr
            init_parts.append("." + cap_name + " = " + init_expr)
        if bool(stmt.get("is_recursive")):
            capture_rewrites[name] = "self"
        self._emit_line(decl_kw + " " + name + " = struct {")
        self.indent += 1
        for field_name, field_type, _ in capture_fields:
            self._emit_line(field_name + ": " + field_type + ",")
        arg_order_any = stmt.get("arg_order")
        args: list[Any] = []
        if isinstance(arg_order_any, list):
            for item in arg_order_any:
                args.append(item)
        arg_names = [_safe_ident(a, "arg") for a in args]
        arg_types_any = stmt.get("arg_types")
        arg_types: dict[str, Any] = {}
        if isinstance(arg_types_any, dict):
            arg_types = self._json_dict_to_any(arg_types_any)
        uses_self = len(capture_fields) > 0 or bool(stmt.get("is_recursive"))
        arg_strs = ["self: @This()" if uses_self else "_: @This()"]
        i = 0
        while i < len(arg_names):
            raw_name = args[i] if i < len(args) else arg_names[i]
            zig_ty = self._resolve_arg_zig_type(arg_names[i], raw_name, arg_types)
            arg_strs.append(arg_names[i] + ": " + zig_ty)
            i += 1
        ret_py = self._dict_get_str(stmt, "return_type", "").strip()
        ret_type = self._zig_type(ret_py)
        self._emit_line("pub fn call(" + ", ".join(arg_strs) + ") " + ret_type + " {")
        self.indent += 1
        self._function_depth += 1
        empty_rename: dict[str, str] = {}
        self._param_rename_stack.append(empty_rename)
        self._lambda_capture_stack.append(capture_rewrites)
        self._push_function_context(stmt, arg_names, args)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self._lambda_capture_stack.pop()
        self._param_rename_stack.pop()
        self._function_depth -= 1
        self.indent -= 1
        self._emit_line("}")
        self.indent -= 1
        if len(init_parts) > 0:
            self._emit_line("}{ " + ", ".join(init_parts) + " };")
        else:
            self._emit_line("}{};")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test_node = stmt.get("test")
        # Skip dead branches only for explicit constant false.
        if isinstance(test_node, dict):
            test_dict = self._json_dict_to_any(test_node)
            test_value = test_dict.get("value")
            if test_dict.get("kind") == "Constant" and isinstance(test_value, bool) and not test_value:
                orelse = self._dict_list(stmt.get("orelse"))
                for sub in orelse:
                    self._emit_stmt(sub)
                return
        test = self._render_cond_expr(test_node)
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
        target_plan_raw = stmt.get("target_plan")
        target_plan: dict[str, Any] = {}
        if isinstance(target_plan_raw, dict):
            target_plan = self._json_dict_to_any(target_plan_raw)
        iter_plan_raw = stmt.get("iter_plan")
        iter_plan: dict[str, Any] = {}
        if isinstance(iter_plan_raw, dict):
            iter_plan = self._json_dict_to_any(iter_plan_raw)
        target_name = "_"
        tuple_unpack_names: list[str] = []
        if target_plan.get("kind") == "TupleTarget":
            # タプル展開: for (item, item2) in iterable → capture as struct then unpack
            elements = target_plan.get("elements")
            if isinstance(elements, list):
                for elt in elements:
                    if isinstance(elt, dict) and elt.get("kind") == "NameTarget":
                        tuple_unpack_names.append(_safe_ident(elt.get("id"), "v"))
            target_name = self._make_stmt_renderer().next_for_tuple_name()
        elif target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "i")
            direct_unpack_names = target_plan.get("direct_unpack_names")
            if isinstance(direct_unpack_names, list):
                for raw_name in direct_unpack_names:
                    if isinstance(raw_name, str):
                        tuple_unpack_names.append(_safe_ident(raw_name, "v"))
        else:
            target_legacy = stmt.get("target")
            if isinstance(target_legacy, dict):
                target_legacy_dict = self._json_dict_to_any(target_legacy)
                if target_legacy_dict.get("kind") == "Name":
                    target_name = _safe_ident(target_legacy_dict.get("id"), "i")
        body_nodes = self._strip_for_synthetic_unpack(stmt.get("body"), target_name, tuple_unpack_names)
        if iter_plan.get("kind") == "StaticRangeForPlan":
            self._emit_static_range_for(stmt, target_name, iter_plan)
            return
        if iter_plan.get("kind") == "RuntimeIterForPlan":
            iter_expr_node_raw = iter_plan.get("iter_expr")
            iter_expr_node: dict[str, Any] = {}
            if isinstance(iter_expr_node_raw, dict):
                iter_expr_node = self._json_dict_to_any(iter_expr_node_raw)
            if len(iter_expr_node) > 0:
                func_node_raw = iter_expr_node.get("func")
                func_node: dict[str, Any] = {}
                if isinstance(func_node_raw, dict):
                    func_node = self._json_dict_to_any(func_node_raw)
                if (
                    iter_expr_node.get("kind") == "Call"
                    and func_node.get("kind") == "Attribute"
                    and func_node.get("attr") == "items"
                ):
                    owner_node = func_node.get("value")
                    owner_type = self._lookup_expr_type(owner_node)
                    if (owner_type.startswith("dict[") or "dict[" in owner_type) and len(tuple_unpack_names) == 2:
                        owner_expr = self._render_expr(owner_node)
                        owner_source = owner_node
                        if isinstance(owner_node, dict):
                            owner_node_dict = self._json_dict_to_any(owner_node)
                            if owner_node_dict.get("kind") == "Unbox":
                                owner_source = owner_node_dict.get("value")
                        owner_source_type = self._lookup_expr_type(owner_source) if isinstance(owner_source, dict) else ""
                        owner_is_union = self._is_union_storage_zig(self._zig_type(owner_source_type)) or self._is_union_storage_zig(self._zig_type(owner_type))
                        iter_name, entry_name = self._make_stmt_renderer().next_dict_items_iter_names()
                        key_name = tuple_unpack_names[0]
                        value_name = tuple_unpack_names[1]
                        key_used = self._body_uses_name(self._strip_dead_branches(body_nodes), key_name)
                        value_used = self._body_uses_name(self._strip_dead_branches(body_nodes), value_name)
                        val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(owner_type)
                        if owner_is_union:
                            val_zig = self._union_storage_zig()
                            owner_expr = "pytra.union_as_dict(" + owner_expr + ")"
                        if ": {" in owner_expr:
                            owner_expr = "(" + owner_expr + ")"
                        self._emit_line("var " + iter_name + " = " + owner_expr + ".iterator();")
                        self._emit_line("while (" + iter_name + ".next()) |" + entry_name + "| {")
                        self.indent += 1
                        if key_used:
                            self._emit_line("const " + key_name + ": []const u8 = " + entry_name + ".key_ptr.*;")
                            self._current_type_map()[key_name] = "str"
                        if value_used:
                            self._emit_line("const " + value_name + ": " + val_zig + " = " + entry_name + ".value_ptr.*;")
                            self._current_type_map()[value_name] = "object" if owner_is_union else owner_type
                        self._emit_block(body_nodes)
                        self.indent -= 1
                        self._emit_line("}")
                        return
                iter_expr = self._render_expr(iter_expr_node)
                iter_type = self._lookup_expr_type(iter_expr_node)
                iter_elem_type = ""
                iter_elem_resolved_type = ""
                if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
                    target_type_any = target_plan.get("target_type")
                    if isinstance(target_type_any, str):
                        iter_elem_type = self._normalize_type(target_type_any)
                if iter_type.startswith("list[") or iter_type in {"bytearray", "bytes"}:
                    elem = "i64"
                    if iter_type.startswith("list[") and iter_type.endswith("]"):
                        iter_elem_resolved_type = iter_type[5:-1].strip()
                        elem = self._zig_type(iter_elem_resolved_type)
                    elif iter_type == "list" and iter_elem_type != "":
                        iter_elem_resolved_type = iter_elem_type
                        elem = self._zig_type(iter_elem_type)
                    elif iter_type in {"bytearray", "bytes"}:
                        iter_elem_resolved_type = "uint8"
                        elem = "u8"
                    iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
                elif iter_type.startswith("set["):
                    elem = self._zig_type(iter_type[4:-1].strip()) if iter_type.endswith("]") else "i64"
                    iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
                elif iter_type.startswith("dict["):
                    val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(iter_type)
                    iter_expr = "pytra.list_items(pytra.dict_keys(" + val_zig + ", " + iter_expr + "), []const u8)"
                elif iter_type == "str":
                    iter_expr = "pytra.list_items(pytra.str_chars(" + iter_expr + "), []const u8)"
                elif self._is_union_storage_zig(self._zig_type(iter_type)):
                    elem = self._zig_type(iter_elem_type) if iter_elem_type != "" else "i64"
                    iter_expr = "pytra.list_items(pytra.union_as_list(" + iter_expr + "), " + elem + ")"
                capture_name = target_name
                reassign_after_capture = False
                # If loop variable is unused in body, use _ to avoid Zig error
                target_unused = isinstance(target_plan, dict) and bool(target_plan.get("unused"))
                if len(tuple_unpack_names) == 0 and target_name != "_unused" and (target_unused or not self._body_uses_name(self._strip_dead_branches(body_nodes), target_name)):
                    capture_name = "_"
                elif target_name in self._hoisted_var_names:
                    capture_name = "_cap_" + target_name
                    reassign_after_capture = True
                self._emit_line("for (" + iter_expr + ") |" + capture_name + "| {")
                self.indent += 1
                if reassign_after_capture:
                    self._emit_line(target_name + " = " + capture_name + ";")
                elif len(self._local_var_stack) > 0:
                    self._add_current_local_var(target_name)
                if capture_name != "_" and iter_elem_resolved_type != "":
                    self._current_type_map()[target_name] = iter_elem_resolved_type
                self._emit_tuple_unpack_in_for(tuple_unpack_names, capture_name, body_nodes)
                self._emit_block(body_nodes)
                self.indent -= 1
                self._emit_line("}")
                return
        iter_any_raw = stmt.get("iter")
        iter_any: Any = iter_any_raw
        if isinstance(iter_any_raw, dict):
            iter_any = self._json_dict_to_any(iter_any_raw)
        if isinstance(iter_any, dict) and iter_any.get("kind") == "Call":
            func_any_raw = iter_any.get("func")
            func_any: dict[str, Any] = {}
            if isinstance(func_any_raw, dict):
                func_any = self._json_dict_to_any(func_any_raw)
            if func_any.get("kind") == "Name":
                fname = str(func_any.get("id"))
                if fname == "range":
                    self._emit_range_for_from_call(stmt, target_name, iter_any)
                    return
        iter_expr = self._render_expr(iter_any)
        iter_type = self._lookup_expr_type(iter_any) if isinstance(iter_any, dict) else ""
        iter_elem_resolved_type = ""
        if iter_type.startswith("list[") or iter_type in {"bytearray", "bytes"}:
            elem = "i64"
            if iter_type.startswith("list[") and iter_type.endswith("]"):
                iter_elem_resolved_type = iter_type[5:-1].strip()
                elem = self._zig_type(iter_elem_resolved_type)
            elif iter_type in {"bytearray", "bytes"}:
                iter_elem_resolved_type = "uint8"
                elem = "u8"
            iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
        elif iter_type.startswith("set["):
            elem = self._zig_type(iter_type[4:-1].strip()) if iter_type.endswith("]") else "i64"
            iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
        elif iter_type.startswith("dict["):
            val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(iter_type)
            iter_expr = "pytra.list_items(pytra.dict_keys(" + val_zig + ", " + iter_expr + "), []const u8)"
        elif iter_type == "str":
            iter_expr = "pytra.list_items(pytra.str_chars(" + iter_expr + "), []const u8)"
        elif self._is_union_storage_zig(self._zig_type(iter_type)):
            iter_expr = "pytra.list_items(pytra.union_as_list(" + iter_expr + "), i64)"
        capture_name = target_name
        reassign_after_capture = False
        target_unused = isinstance(target_plan, dict) and bool(target_plan.get("unused"))
        if target_unused:
            capture_name = "_"
        elif len(self._local_var_stack) > 0 and target_name in self._current_local_vars():
            capture_name = "_cap_" + target_name
            reassign_after_capture = True
        self._emit_line("for (" + iter_expr + ") |" + capture_name + "| {")
        self.indent += 1
        if reassign_after_capture:
            self._emit_line(target_name + " = " + capture_name + ";")
        elif len(self._local_var_stack) > 0:
            self._add_current_local_var(target_name)
        if capture_name != "_" and iter_elem_resolved_type != "":
            self._current_type_map()[target_name] = iter_elem_resolved_type
        self._emit_tuple_unpack_in_for(tuple_unpack_names, capture_name, body_nodes)
        self._emit_block(body_nodes)
        self.indent -= 1
        self._emit_line("}")

    def _emit_tuple_unpack_in_for(self, names: list[str], capture: str, body_any: Any = None) -> None:
        """for ループキャプチャ変数からタプルフィールドを展開する。"""
        if len(names) == 0:
            return
        live_body = self._strip_dead_branches(body_any)
        i = 0
        while i < len(names):
            n = names[i]
            if len(live_body) > 0 and not self._body_uses_name(live_body, n):
                i += 1
                continue
            decl_kw = "var" if self._is_var_mutated(n) else "const"
            self._emit_line(decl_kw + " " + n + " = " + capture + "._" + str(i) + ";")
            if len(self._local_var_stack) > 0:
                self._add_current_local_var(n)
            i += 1

    def _strip_for_synthetic_unpack(self, body_any: Any, capture_name: str, unpack_names: list[str]) -> list[dict[str, Any]]:
        body = self._dict_list(body_any)
        if len(body) > 0:
            first = body[0]
            if (
                isinstance(first, dict)
                and first.get("kind") == "Assign"
                and bool(first.get("unused"))
            ):
                target = first.get("target")
                value = first.get("value")
                if (
                    isinstance(target, dict)
                    and target.get("kind") == "Name"
                    and target.get("id") == "_"
                    and isinstance(value, dict)
                    and value.get("kind") == "Name"
                    and _safe_ident(value.get("id"), "i") == capture_name
                ):
                    body = body[1:]
        if len(unpack_names) == 0 or len(body) < len(unpack_names):
            return body
        i = 0
        while i < len(unpack_names):
            stmt = body[i]
            if stmt.get("kind") != "Assign":
                return body
            target = stmt.get("target")
            value = stmt.get("value")
            if not isinstance(target, dict) or target.get("kind") != "Name" or _safe_ident(target.get("id"), "v") != unpack_names[i]:
                return body
            if not isinstance(value, dict) or value.get("kind") != "Subscript":
                return body
            owner = value.get("value")
            idx = value.get("slice")
            if not isinstance(owner, dict) or owner.get("kind") != "Name" or _safe_ident(owner.get("id"), "i") != capture_name:
                return body
            if not isinstance(idx, dict) or idx.get("kind") != "Constant" or idx.get("value") != i:
                return body
            i += 1
        return body[len(unpack_names):]

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノード（ListComp lowering 由来）を while ループに展開する。"""
        target_node = stmt.get("target")
        target_name = "_unused"
        if isinstance(target_node, dict) and target_node.get("kind") == "Name":
            target_name = _safe_ident(target_node.get("id"), "i")
        start = self._render_expr(stmt.get("start"))
        stop = self._render_expr(stmt.get("stop"))
        step_node = stmt.get("step")
        step = self._render_expr(step_node) if isinstance(step_node, dict) else "1"
        already_exists = target_name in self._hoisted_var_names or (len(self._local_var_stack) > 0 and target_name in self._current_local_vars())
        if already_exists:
            self._emit_line(target_name + " = " + start + ";")
        else:
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            if len(self._local_var_stack) > 0:
                self._add_current_local_var(target_name)
        self._emit_line("while (((" + step + ") > 0 and " + target_name + " < " + stop + ") or ((" + step + ") < 0 and " + target_name + " > " + stop + ")) : (" + target_name + " += " + step + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_static_range_for(self, stmt: dict[str, Any], target_name: str, plan: dict[str, Any]) -> None:
        start = self._render_expr(plan.get("start"))
        stop = self._render_expr(plan.get("stop"))
        step_any = plan.get("step")
        step = self._render_expr(step_any) if isinstance(step_any, dict) else "1"
        already_exists = target_name in self._hoisted_var_names or (len(self._local_var_stack) > 0 and target_name in self._current_local_vars())
        if already_exists:
            # Reuse existing variable (avoid shadow)
            self._emit_line(target_name + " = " + start + ";")
        else:
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            if len(self._local_var_stack) > 0:
                self._add_current_local_var(target_name)
        self._emit_line("while (((" + step + ") > 0 and " + target_name + " < " + stop + ") or ((" + step + ") < 0 and " + target_name + " > " + stop + ")) : (" + target_name + " += " + step + ") {")
        self.indent += 1
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
            self._emit_line("while (((" + step + ") > 0 and " + target_name + " < " + end + ") or ((" + step + ") < 0 and " + target_name + " > " + end + ")) : (" + target_name + " += " + step + ") {")
        else:
            self._emit_line("// unsupported range args count")
            self._emit_line("while (false) {")
        self.indent += 1
        if len(self._local_var_stack) > 0:
            self._add_current_local_var(target_name)
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

    def _scan_init_fields(self, body: list[dict[str, Any]], arg_types: dict[str, Any]) -> list[tuple[str, str]]:
        """__init__ body から self.field = ... のフィールドを抽出する。"""
        fields: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind not in {"Assign", "AnnAssign"}:
                continue
            target = stmt.get("target")
            if not isinstance(target, dict) or target.get("kind") != "Attribute":
                continue
            val = target.get("value")
            if not isinstance(val, dict) or val.get("kind") != "Name" or val.get("id") != "self":
                continue
            field_name = _safe_ident(target.get("attr"), "field")
            if field_name in seen:
                continue
            seen.add(field_name)
            decl_type = ""
            if kind == "AnnAssign":
                decl_type = self._infer_decl_type(stmt)
            if decl_type == "":
                value_node = stmt.get("value")
                if isinstance(value_node, dict):
                    if value_node.get("kind") == "Name":
                        src_name = str(value_node.get("id"))
                        src_type = arg_types.get(src_name)
                        if isinstance(src_type, str) and src_type.strip() != "":
                            decl_type = src_type.strip()
                    if decl_type == "":
                        decl_type = self._get_expr_type(value_node)
            fields.append((field_name, decl_type))
        return fields

    def _get_base_methods(self, cls_name: str) -> list[tuple[str, str]]:
        """基底クラスのメソッド名と基底クラス名のペアを再帰的に収集する。"""
        base = self._class_base.get(cls_name, "")
        if base == "":
            return []
        result: list[tuple[str, str]] = []
        empty_methods: set[str] = set()
        base_methods = self._class_methods.get(base, empty_methods)
        for m in base_methods:
            result.append((m, base))
        result.extend(self._get_base_methods(base))
        return result

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class")
        base_name = self._class_base.get(cls_name, "")
        has_local_base = base_name in self.class_names
        # Track class context for param shadowing detection
        old_class_name = self._current_class_name
        old_class_methods = self._current_class_methods
        self._current_class_name = cls_name
        body_all = self._dict_list(stmt.get("body"))
        self._current_class_methods = [s for s in body_all if isinstance(s, dict) and s.get("kind") in {"FunctionDef", "ClosureDef"}]
        struct_kw = "pub const" if self.is_submodule else "const"
        self._emit_line(struct_kw + " " + cls_name + " = struct {")
        self.indent += 1
        # composition: 基底クラスフィールド
        if has_local_base:
            self._emit_line("_base: " + base_name + " = " + base_name + "{},")
        body = self._dict_list(stmt.get("body"))
        class_field_types = self._class_field_types.setdefault(cls_name, {})
        # __init__ body から struct フィールドを抽出
        emitted_fields: set[str] = set()
        dataclass_fields: list[str] = []
        if bool(stmt.get("dataclass")):
            for sub in body:
                if sub.get("kind") != "AnnAssign":
                    continue
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    decl_type_any = sub.get("decl_type")
                    decl_type = self._any_str(decl_type_any, "").strip()
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    value_node = sub.get("value")
                    if isinstance(value_node, dict):
                        default_val = self._render_expr(value_node)
                        if value_node.get("kind") == "Call":
                            func_any = value_node.get("func")
                            if isinstance(func_any, dict) and func_any.get("kind") == "Name" and _safe_ident(func_any.get("id"), "") == "field":
                                default_val = self._zig_zero_value(zig_ty)
                        default_val = self._coerce_value_to_zig_type(zig_ty, value_node, default_val)
                        self._emit_line(field_name + ": " + zig_ty + " = " + default_val + ",")
                    else:
                        self._emit_line(field_name + ": " + zig_ty + ",")
                    class_field_types[field_name] = decl_type
                    dataclass_fields.append(field_name)
                    emitted_fields.add(field_name)
        for sub in body:
            if sub.get("kind") in {"FunctionDef", "ClosureDef"} and sub.get("name") == "__init__":
                init_body = self._dict_list(sub.get("body"))
                init_arg_types = sub.get("arg_types")
                if isinstance(init_arg_types, dict):
                    init_arg_types = self._json_dict_to_any(init_arg_types)
                else:
                    init_arg_types = {}
                init_fields = self._scan_init_fields(init_body, init_arg_types)
                for field_name, field_type in init_fields:
                    if field_name not in emitted_fields:
                        zig_ty = self._zig_type(field_type)
                        self._emit_line(field_name + ": " + zig_ty + " = undefined,")
                        class_field_types[field_name] = field_type
                        emitted_fields.add(field_name)
                break
        for sub in body:
            if sub.get("kind") == "AnnAssign" and bool(stmt.get("dataclass")):
                continue
            if sub.get("kind") in {"FunctionDef", "ClosureDef"}:
                self._emit_class_method(cls_name, sub)
            elif sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    # 静的フィールドはモジュールスコープに emit 済み → struct から除外
                    static_field_names: set[str] = set()
                    for sf in self._static_fields.get(cls_name, []):
                        if len(sf) > 0:
                            static_field_names.add(sf[0])
                    if field_name in static_field_names:
                        continue
                    decl_type_any = sub.get("decl_type")
                    decl_type = self._any_str(decl_type_any, "").strip()
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    if field_name not in emitted_fields:
                        value_node = sub.get("value")
                        if isinstance(value_node, dict):
                            default_val = self._render_expr(value_node)
                            default_val = self._coerce_value_to_zig_type(zig_ty, value_node, default_val)
                            self._emit_line(field_name + ": " + zig_ty + " = " + default_val + ",")
                        else:
                            self._emit_line(field_name + ": " + zig_ty + " = undefined,")
                        class_field_types[field_name] = decl_type
                        emitted_fields.add(field_name)
        # 基底クラスの未 override メソッドの委譲関数を生成
        if has_local_base:
            empty_own_methods: set[str] = set()
            own_methods = self._class_methods.get(cls_name, empty_own_methods)
            base_method_pairs = self._get_base_methods(cls_name)
            for method_name, origin_cls in base_method_pairs:
                if method_name not in own_methods:
                    ret_type = self._class_return_types.get(origin_cls, {}).get(method_name, "")
                    zig_ret = self._zig_type(ret_type)
                    self._emit_line("pub fn " + method_name + "(self: *const " + cls_name + ") " + zig_ret + " {")
                    self.indent += 1
                    self._emit_line("return self._base." + method_name + "();")
                    self.indent -= 1
                    self._emit_line("}")
                    self._emit_line("")
        self.indent -= 1
        self._emit_line("};")
        self._emit_line("")
        self._current_class_name = old_class_name
        self._current_class_methods = old_class_methods

    def _emit_class_method(self, cls_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        arg_strs: list[str] = []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        has_self = False
        self_used = self._body_uses_name(stmt.get("body"), "self")
        if not self_used and self._node_uses_super_call(stmt.get("body")):
            self_used = True
        # EAST3 の mutates_self フラグを優先（call graph 伝播済み）
        ms_flag = stmt.get("mutates_self")
        if isinstance(ms_flag, bool):
            self_mutated = ms_flag
        else:
            self_mutated = self._body_mutates_self(stmt.get("body"))
            if not self_mutated:
                self_mutated = cls_name in self._classes_with_mut_method
        sibling_names: set[str] = set()
        for sib in self._current_class_methods:
            sn = sib.get("name", "") if isinstance(sib, dict) else ""
            if sn != "":
                sibling_names.add(sn)
        live_body = self._strip_dead_branches(stmt.get("body"))
        param_renames: dict[str, str] = {}  # original → renamed
        for i, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i == 0 and arg_name == "self":
                has_self = True
                if not self_used:
                    arg_strs.append("_: *const " + cls_name)
                elif self_mutated:
                    arg_strs.append("self: *" + cls_name)
                else:
                    arg_strs.append("self: *const " + cls_name)
                continue
            # Unused param (not referenced in live branches) → _
            if not self._body_uses_name(live_body, arg_name):
                args.append("_")
                zig_ty = self._resolve_arg_zig_type(arg_name, arg, arg_types)
                arg_strs.append("_: " + zig_ty)
                continue
            # Param name shadows sibling method → rename + track mapping
            if arg_name in sibling_names and arg_name != method_name:
                new_name = arg_name + "_arg"
                param_renames[arg_name] = new_name
                arg_name = new_name
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
            saved_lines = self.lines
            self.lines = []
            self.indent += 1
            self._function_depth += 1
            self._emit_line("var self: " + cls_name + " = undefined;")
            self._param_rename_stack.append(param_renames)
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            if len(self._return_type_stack) > 0:
                self._return_type_stack[-1] = cls_name
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._param_rename_stack.pop()
            body_text = "\n".join(self.lines)
            for p in args:
                if p == "_" or p == "self":
                    continue
                if p not in body_text:
                    self._emit_line("_ = " + p + ";")
            self._emit_line("return self;")
            self._function_depth -= 1
            self.indent -= 1
            init_body_lines = self.lines
            self.lines = saved_lines
            for line in init_body_lines:
                self.lines.append(line)
            self._emit_line("}")
            self._emit_line("")
        else:
            # Emit method body to a temporary buffer, then post-check for unused params
            saved_lines = self.lines
            self.lines = []
            self.indent += 1
            self._function_depth += 1
            self._param_rename_stack.append(param_renames)
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._param_rename_stack.pop()
            self._function_depth -= 1
            self.indent -= 1
            method_body_lines = self.lines
            if self._is_union_storage_zig(ret_type):
                method_body_lines = self._wrap_union_return_lines(method_body_lines, cls_name)
            self.lines = saved_lines
            # Determine which non-self params are actually used in generated code
            body_text = "\n".join(method_body_lines)
            actual_unused: list[str] = []
            for p in args:
                if p == "_" or p == "self":
                    continue
                # Check if param name (or its renamed form) appears in the generated body
                check_name = p
                if check_name not in body_text:
                    actual_unused.append(p)
            # Rebuild arg_strs with _ for truly unused params
            final_arg_strs: list[str] = []
            for astr in arg_strs:
                replaced = False
                for unused_p in actual_unused:
                    if astr.startswith(unused_p + ":"):
                        final_arg_strs.append("_: " + astr.split(": ", 1)[1])
                        replaced = True
                        break
                if not replaced:
                    final_arg_strs.append(astr)
            self._emit_line("pub fn " + method_name + "(" + ", ".join(final_arg_strs) + ") " + ret_type + " {")
            self.lines.extend(method_body_lines)
            self._emit_line("}")
            self._emit_line("")
        self.current_class_name = prev_class

    def _emit_tuple_assign(self, target_any: Any, value_any: Any) -> None:
        if not isinstance(target_any, dict):
            return
        # elements (EAST3) or elts (legacy)
        elts_any = target_any.get("elements")
        if not isinstance(elts_any, list):
            elts_any = target_any.get("elts")
        elts = elts_any if isinstance(elts_any, list) else []
        value_expr = self._render_expr(value_any)
        value_type = self._lookup_expr_type(value_any) if isinstance(value_any, dict) else ""
        value_zig = self._zig_type(value_type) if value_type != "" else ""
        tuple_type = ""
        if isinstance(value_any, dict):
            resolved_tuple = self._get_expr_type(value_any)
            inner_tuple = self._strip_optional_type(resolved_tuple)
            if resolved_tuple.startswith("tuple["):
                tuple_type = resolved_tuple
            elif inner_tuple.startswith("tuple["):
                tuple_type = inner_tuple
        if value_zig.startswith("?") or (value_type != "" and self._strip_optional_type(value_type) != value_type):
            value_expr = value_expr + ".?"
        tmp = self._make_stmt_renderer().next_tuple_assign_temp_name()
        self._emit_line("const " + tmp + " = " + value_expr + ";")
        i = 0
        while i < len(elts):
            elt = elts[i]
            if isinstance(elt, dict):
                field_access = tmp + "._" + str(i)
                elt_kind = elt.get("kind")
                # Subscript target → list_set
                if elt_kind == "Subscript":
                    sub_val = elt.get("value")
                    sub_val_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
                    if sub_val_type.startswith("list[") or sub_val_type in {"bytearray", "bytes"}:
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(elt.get("slice"))
                        elem = "i64"
                        if sub_val_type.startswith("list[") and sub_val_type.endswith("]"):
                            elem = self._zig_type(sub_val_type[5:-1].strip())
                        elif sub_val_type in {"bytearray", "bytes"}:
                            elem = "u8"
                        val_cast = "@intCast(" + field_access + ")" if elem in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"} else field_access
                        self._emit_line("pytra.list_set(" + obj_expr + ", " + elem + ", " + idx_expr + ", " + val_cast + ");")
                        i += 1
                        continue
                name = self._render_target(elt)
                # EAST3 unused: true on tuple element → use _ discard
                is_unused_elt = bool(elt.get("unused", False))
                elt_id_raw = elt.get("id", "") if elt_kind == "Name" else ""
                if is_unused_elt or (isinstance(elt_id_raw, str) and elt_id_raw == "_"):
                    self._emit_line("_ = " + field_access + ";")
                    i += 1
                    continue
                if len(self._local_var_stack) > 0 and elt_kind == "Name":
                    elt_name = _safe_ident(elt.get("id"), "value")
                    if elt_name not in self._current_local_vars():
                        self._add_current_local_var(elt_name)
                        decl_kw = "var" if self._is_var_mutated(elt_name) else "const"
                        self._emit_line(decl_kw + " " + name + " = " + field_access + ";")
                        i += 1
                        continue
                self._emit_line(name + " = " + field_access + ";")
            i += 1

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        lhs_node = stmt.get("lhs") if stmt.get("lhs") is not None else stmt.get("left")
        rhs_node = stmt.get("rhs") if stmt.get("rhs") is not None else stmt.get("right")
        # list Subscript の swap: list_get + list_set
        lhs_is_list_sub = self._is_list_subscript(lhs_node)
        rhs_is_list_sub = self._is_list_subscript(rhs_node)
        if lhs_is_list_sub and rhs_is_list_sub:
            tmp = self._make_stmt_renderer().next_swap_temp_name()
            lobj, lidx, lelem = self._list_subscript_parts(lhs_node)
            robj, ridx, relem = self._list_subscript_parts(rhs_node)
            self._emit_line("const " + tmp + " = pytra.list_get(" + lobj + ", " + lelem + ", " + lidx + ");")
            self._emit_line("pytra.list_set(" + lobj + ", " + lelem + ", " + lidx + ", pytra.list_get(" + robj + ", " + relem + ", " + ridx + "));")
            self._emit_line("pytra.list_set(" + robj + ", " + relem + ", " + ridx + ", " + tmp + ");")
            return
        left = self._render_target(lhs_node)
        right = self._render_target(rhs_node)
        tmp = self._make_stmt_renderer().next_swap_temp_name()
        self._emit_line("const " + tmp + " = " + left + ";")
        self._emit_line(left + " = " + right + ";")
        self._emit_line(right + " = " + tmp + ";")

    def _is_list_subscript(self, node: Any) -> bool:
        if not isinstance(node, dict) or node.get("kind") != "Subscript":
            return False
        sub_val = node.get("value")
        sub_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
        return sub_type.startswith("list[") or sub_type in {"bytearray", "bytes"}

    def _list_subscript_parts(self, node: dict[str, Any]) -> tuple[str, str, str]:
        sub_val = node.get("value")
        sub_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
        obj_expr = self._render_expr(sub_val)
        idx_expr = self._render_expr(node.get("slice"))
        elem = "i64"
        if sub_type.startswith("list[") and sub_type.endswith("]"):
            elem = self._zig_type(sub_type[5:-1].strip())
        elif sub_type in {"bytearray", "bytes"}:
            elem = "u8"
        return obj_expr, idx_expr, elem

    def _render_target(self, node: Any) -> str:
        if not isinstance(node, dict):
            return "_"
        nd: dict[str, Any] = node
        kind = nd.get("kind")
        if kind == "Name":
            return _safe_ident(nd.get("id"), "value")
        if kind == "Attribute":
            val_node = nd.get("value")
            attr = _safe_ident(nd.get("attr"), "attr")
            if isinstance(val_node, dict) and val_node.get("kind") == "Name":
                owner = _safe_ident(val_node.get("id"), "")
                if owner in self._static_fields:
                    for sf in self._static_fields[owner]:
                        sf_name = sf[0] if len(sf) > 0 else ""
                        if sf_name == attr:
                            return "Module_" + owner + "_" + attr
            obj = self._render_expr(val_node)
            if (
                isinstance(val_node, dict)
                and val_node.get("kind") == "Name"
                and _safe_ident(val_node.get("id"), "") == "self"
                and self.current_class_name != ""
            ):
                base_name = self._class_base.get(self.current_class_name, "")
                if base_name in self.class_names and attr not in self._class_methods.get(self.current_class_name, set()):
                    return obj + "._base." + attr
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
        rendered = self._render_expr(expr_any)
        # i64 の条件式は != 0 で bool に変換
        expr_type = self._lookup_expr_type(expr_any) if isinstance(expr_any, dict) else ""
        if expr_type in {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
            return "(" + rendered + " != 0)"
        # list/Obj の条件式は list_len > 0 に変換（Python の truthiness）
        if expr_type.startswith("list[") or expr_type in {"bytearray", "bytes"}:
            elem = "i64"
            if expr_type.startswith("list[") and expr_type.endswith("]"):
                elem = self._zig_type(expr_type[5:-1].strip())
            elif expr_type in {"bytearray", "bytes"}:
                elem = "u8"
            return "(pytra.list_len(" + rendered + ", " + elem + ") > 0)"
        if expr_type.startswith("dict["):
            return "(" + rendered + ".count() > 0)"
        if expr_type == "str":
            return "(" + rendered + ".len > 0)"
        return rendered

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
            i_lc = len(self._lambda_capture_stack) - 1
            while i_lc >= 0:
                rewritten = self._lambda_capture_stack[i_lc].get(name)
                if rewritten is not None:
                    return rewritten
                i_lc -= 1
            # Apply param rename mapping (for Zig shadowing avoidance)
            i_pr = len(self._param_rename_stack) - 1
            while i_pr >= 0:
                renamed = self._param_rename_stack[i_pr].get(name)
                if renamed is not None:
                    return renamed
                i_pr -= 1
            node_resolved_type = self._normalize_type(self._get_expr_type(ed))
            resolved_type = self._lookup_expr_type(ed)
            if (
                node_resolved_type not in {"", "unknown", "Any", "object"}
                and node_resolved_type.find("|") == -1
            ):
                resolved_type = node_resolved_type
            storage_type = self._current_storage_type_map().get(name, "")
            if storage_type == "":
                storage_type = self._current_type_map().get(name, "")
            if self._is_union_storage_zig(self._zig_type(storage_type)) and resolved_type not in {"", "unknown", "Any", "object"}:
                if resolved_type == "str":
                    return "pytra.union_as_str(" + name + ")"
                if resolved_type in {"int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
                    return "pytra.union_to_int(" + name + ")"
                if resolved_type in {"float", "float64", "float32"}:
                    return "pytra.union_to_float(" + name + ")"
                if resolved_type == "bool":
                    return "pytra.union_to_bool(" + name + ")"
            return name
        if kind == "BinOp":
            left = self._render_expr(ed.get("left"))
            right = self._render_expr(ed.get("right"))
            op = str(ed.get("op"))
            # BinOp の子は常に括弧で囲む（浮動小数点の演算順序を Python と完全一致させる）
            left_type = self._lookup_expr_type(ed.get("left"))
            right_type = self._lookup_expr_type(ed.get("right"))
            # Fallback: check resolved_type if _lookup_expr_type returns empty
            if left_type == "":
                left_type = self._get_expr_type(ed.get("left"))
            if right_type == "":
                right_type = self._get_expr_type(ed.get("right"))
            # int/float 混合演算: int 側を @floatFromInt でラップ
            _INT_TYPES = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
            _FLOAT_TYPES = {"float64", "float32", "float"}
            left_float_like = self._expr_is_float_like(ed.get("left"))
            right_float_like = self._expr_is_float_like(ed.get("right"))
            if op not in {"LShift", "RShift", "BitOr", "BitXor", "BitAnd", "FloorDiv"}:
                if left_type in _INT_TYPES and (right_type in _FLOAT_TYPES or right_float_like):
                    if not left_float_like:
                        left = "@as(f64, @floatFromInt(" + left + "))"
                elif (left_type in _FLOAT_TYPES or left_float_like) and right_type in _INT_TYPES:
                    if not right_float_like:
                        right = "@as(f64, @floatFromInt(" + right + "))"
            if op == "Add":
                if left_type == "str" or right_type == "str":
                    return "pytra.str_concat(" + left + ", " + right + ")"
                list_type = ""
                result_type = self._get_expr_type(ed)
                if left_type.startswith("list[") and right_type.startswith("list["):
                    list_type = left_type
                elif result_type.startswith("list["):
                    list_type = result_type
                if list_type.startswith("list[") and list_type.endswith("]"):
                    elem_type = self._zig_type(list_type[5:-1].strip())
                    renderer = self._make_stmt_renderer()
                    blk, out_name, item_name = renderer.next_list_concat_names()
                    return renderer.render_simple_block_expr(
                        blk,
                        "const "
                        + out_name
                        + " = pytra.make_list("
                        + elem_type
                        + "); for (pytra.list_items("
                        + left
                        + ", "
                        + elem_type
                        + ")) |"
                        + item_name
                        + "| { pytra.list_append("
                        + out_name
                        + ", "
                        + elem_type
                        + ", "
                        + item_name
                        + "); } for (pytra.list_items("
                        + right
                        + ", "
                        + elem_type
                        + ")) |"
                        + item_name
                        + "| { pytra.list_append("
                        + out_name
                        + ", "
                        + elem_type
                        + ", "
                        + item_name
                        + "); }",
                        out_name,
                    )
            # list * int → list replication (ブロック式)
            if op == "Mult":
                if left_type == "str" and right_type in _INT_TYPES:
                    return "pytra.str_repeat(" + left + ", @as(i64, @intCast(" + right + ")))"
                if right_type == "str" and left_type in _INT_TYPES:
                    return "pytra.str_repeat(" + right + ", @as(i64, @intCast(" + left + ")))"
                if left_type.startswith("list[") or left_type in {"bytearray", "bytes"}:
                    elem_type = "i64"
                    if left_type.startswith("list[") and left_type.endswith("]"):
                        elem_type = self._zig_type(left_type[5:-1].strip())
                    elif left_type in {"bytearray", "bytes"}:
                        elem_type = "u8"
                    renderer = self._make_stmt_renderer()
                    blk, src_name, item_name = renderer.next_list_repeat_names()
                    return renderer.render_simple_block_expr(
                        blk,
                        "const "
                        + src_name
                        + " = "
                        + left
                        + "; const __rl = pytra.make_list("
                        + elem_type
                        + "); var __ri: i64 = 0; while (__ri < "
                        + right
                        + ") : (__ri += 1) { for (pytra.list_items("
                        + src_name
                        + ", "
                        + elem_type
                        + ")) |"
                        + item_name
                        + "| { pytra.list_append(__rl, "
                        + elem_type
                        + ", "
                        + item_name
                        + "); } }",
                        "__rl",
                    )
            if op == "Pow":
                return "std.math.pow(f64, " + left + ", " + right + ")"
            if op == "FloorDiv":
                return "@divFloor(" + left + ", " + right + ")"
            if op == "Div":
                left_type = self._lookup_expr_type(ed.get("left"))
                right_type = self._lookup_expr_type(ed.get("right"))
                if left_type in {"Path", "PyPath", "pytra.std.pathlib.Path"} and right_type == "str":
                    return left + ".__truediv__(" + right + ")"
                if left_type in {"float64", "float32", "float"} or right_type in {"float64", "float32", "float"}:
                    return "(" + left + " / " + right + ")"
                return "(@as(f64, @floatFromInt(" + left + ")) / @as(f64, @floatFromInt(" + right + ")))"
            if op == "Mod":
                return "@mod(" + left + ", " + right + ")"
            if op in {"LShift", "RShift"}:
                sym = _binop_symbol(op)
                # LHS を常に i64 に昇格（EAST3 の型と Zig の実際の型が異なる場合の安全策）
                left = "@as(i64, " + left + ")"
                return "(" + left + " " + sym + " @intCast(" + right + "))"
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
            if len(values) == 2:
                left_node = values[0]
                right_node = values[1]
                resolved_type = self._lookup_expr_type(ed)
                if resolved_type != "bool":
                    left_expr = self._render_expr(left_node)
                    right_expr = self._render_expr(right_node)
                    left_cond = self._render_cond_expr(left_node)
                    if op == "And":
                        return "if (" + left_cond + ") " + right_expr + " else " + left_expr
                    if op == "Or":
                        return "if (" + left_cond + ") " + left_expr + " else " + right_expr
            parts: list[str] = []
            for v in values:
                parts.append(self._render_expr(v))
            joiner = " and " if op == "And" else " or "
            return "(" + joiner.join(parts) + ")"
        if kind == "Unbox":
            value_node = ed.get("value")
            target_type = self._normalize_type(ed.get("target"))
            source_type = self._lookup_expr_type(value_node) if isinstance(value_node, dict) else ""
            value_expr = self._render_expr(value_node)
            source_zig = self._zig_type(source_type) if source_type != "" else ""
            if source_type != "" and self._strip_optional_type(source_type) == target_type:
                return value_expr + ".?"
            if self._is_union_storage_zig(self._zig_type(source_type)):
                if target_type == "dict" or target_type.startswith("dict["):
                    if target_type.startswith("dict["):
                        parts = self._split_generic(target_type[5:-1])
                        if len(parts) == 2:
                            return "pytra.as_dict_typed(" + self._zig_type(parts[1].strip()) + ", " + value_expr + ")"
                    return "pytra.as_dict_any(" + value_expr + ")"
                if target_type == "list" or target_type.startswith("list["):
                    return "pytra.as_list_any(" + value_expr + ")"
                if target_type == "str":
                    return "pytra.union_as_str(" + value_expr + ")"
                if target_type in {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
                    return "pytra.union_to_int(" + value_expr + ")"
                if target_type in {"float64", "float32"}:
                    return "pytra.union_to_float(" + value_expr + ")"
                if target_type == "bool":
                    return "pytra.union_to_bool(" + value_expr + ")"
            if self._is_callable_type(target_type) and isinstance(value_node, dict) and value_node.get("kind") == "Name":
                name = _safe_ident(value_node.get("id"), "")
                storage_type = self._current_storage_type_map().get(name, "")
                if self._is_optional_callable_type(storage_type) or (isinstance(storage_type, str) and storage_type.startswith("?")):
                    return value_expr + ".?"
            if target_type == "str" and source_zig == "anytype":
                return "pytra._jv_as_str_any(" + value_expr + ").?"
            if target_type in {"float64", "float32"} and source_zig == "anytype":
                return "pytra._jv_as_float_any(" + value_expr + ").?"
            return value_expr
        if kind == "Box":
            return self._render_expr(ed.get("value"))
        if kind == "ObjStr":
            inner = self._render_expr(ed.get("value"))
            return "pytra.to_str(" + inner + ")"
        if kind == "ObjLen":
            value_node = ed.get("value")
            inner = self._render_expr(value_node)
            if isinstance(value_node, dict) and value_node.get("kind") in {"Call", "Compare", "BoolOp", "BinOp", "IfExp", "Subscript", "Attribute"}:
                inner = "(" + inner + ")"
            inner_type = self._lookup_expr_type(value_node)
            elem = "i64"
            if inner_type.startswith("list[") and inner_type.endswith("]"):
                elem = self._zig_type(inner_type[5:-1].strip())
            elif inner_type in {"bytearray", "bytes"}:
                elem = "u8"
            # ObjLen は Python の len() なので、Obj コンテナ前提で list_len を使う
            zig_inner_type = self._zig_type(inner_type) if inner_type != "" else ""
            if inner_type.startswith("list[") or inner_type in {"bytearray", "bytes"} or zig_inner_type == "pytra.Obj" or inner_type in {"", "unknown"}:
                return "pytra.list_len(" + inner + ", " + elem + ")"
            return "@as(i64, @intCast(" + inner + ".len))"
        if kind == "Call":
            return self._render_call(ed)
        if kind == "Attribute":
            val_node = ed.get("value")
            attr = _safe_ident(ed.get("attr"), "attr")
            if attr == "__name__" and isinstance(val_node, dict) and val_node.get("kind") == "Call":
                type_func = val_node.get("func")
                type_args_any = val_node.get("args")
                type_args = type_args_any if isinstance(type_args_any, list) else []
                if (
                    isinstance(type_func, dict)
                    and type_func.get("kind") == "Name"
                    and _safe_ident(type_func.get("id"), "") == "type"
                    and len(type_args) == 1
                ):
                    arg_type = self._lookup_expr_type(type_args[0]) or self._get_expr_type(type_args[0])
                    return _zig_string(self._normalize_type(arg_type) or "unknown")
            if isinstance(val_node, dict) and val_node.get("kind") == "Name":
                owner = _safe_ident(val_node.get("id"), "")
                if owner in self._static_fields:
                    for sf in self._static_fields[owner]:
                        sf_name = sf[0] if len(sf) > 0 else ""
                        if sf_name == attr:
                            return "Module_" + owner + "_" + attr
            obj = self._render_expr(val_node)
            if isinstance(val_node, dict) and val_node.get("kind") in {"Subscript", "Call", "Compare", "BoolOp", "BinOp", "IfExp", "IsInstance"}:
                obj = "(" + obj + ")"
            elif ": {" in obj:
                obj = "(" + obj + ")"
            val_type = self._lookup_expr_type(val_node) if isinstance(val_node, dict) else ""
            norm_val_type = self._normalize_type(val_type)
            is_self_receiver = (
                isinstance(val_node, dict)
                and val_node.get("kind") == "Name"
                and _safe_ident(val_node.get("id"), "") == "self"
                and self.current_class_name == norm_val_type
            )
            if norm_val_type in self.class_names and self._zig_type(norm_val_type) == "pytra.Obj" and not is_self_receiver:
                return obj + ".as(" + norm_val_type + ")." + attr
            if (norm_val_type in self.class_names or norm_val_type in self._known_imported_nominals) and attr in self._class_properties.get(norm_val_type, set()):
                return obj + "." + attr + "()"
            if (
                isinstance(val_node, dict)
                and val_node.get("kind") == "Name"
                and _safe_ident(val_node.get("id"), "") == "self"
                and self.current_class_name != ""
            ):
                base_name = self._class_base.get(self.current_class_name, "")
                if base_name in self.class_names and attr not in self._class_methods.get(self.current_class_name, set()) and attr not in self._class_properties.get(self.current_class_name, set()):
                    return obj + "._base." + attr
            # Obj-managed list の .len → pytra.list_len
            if attr == "len":
                zig_val_type = self._zig_type(val_type) if val_type != "" else ""
                # Obj 型（list/dict/unknown のコンテナ）なら list_len を使う
                is_obj_container = val_type.startswith("list[") or val_type in {"bytearray", "bytes"} or zig_val_type == "pytra.Obj"
                if is_obj_container:
                    elem = "i64"
                    if val_type.startswith("list[") and val_type.endswith("]"):
                        elem = self._zig_type(val_type[5:-1].strip())
                    elif val_type in {"bytearray", "bytes"}:
                        elem = "u8"
                    return "pytra.list_len(" + obj + ", " + elem + ")"
            return obj + "." + attr
        if kind == "Subscript":
            value_node = ed.get("value")
            obj = self._render_expr(value_node)
            slice_node = ed.get("slice")
            obj_type = self._lookup_expr_type(value_node)
            # 文字列スライス: str[start:end]
            if isinstance(slice_node, dict) and slice_node.get("kind") == "Slice":
                lower = self._render_expr(slice_node.get("lower")) if slice_node.get("lower") is not None else "0"
                upper_node = slice_node.get("upper")
                if upper_node is not None:
                    upper = self._render_expr(upper_node)
                else:
                    upper = "@as(i64, @intCast(" + obj + ".len))"
                if obj_type == "str":
                    return "pytra.str_slice(" + obj + ", " + lower + ", " + upper + ")"
                if obj_type.startswith("list[") and obj_type.endswith("]"):
                    elem_type = self._zig_type(obj_type[5:-1].strip())
                    if upper_node is None:
                        upper = "pytra.list_len(" + obj + ", " + elem_type + ")"
                    return "pytra.list_slice(" + obj + ", " + elem_type + ", " + lower + ", " + upper + ")"
                if obj_type in {"bytearray", "bytes", "", "unknown"} or self._zig_type(obj_type) == "pytra.Obj":
                    if upper_node is None:
                        upper = "pytra.list_len(" + obj + ", u8)"
                    return "pytra.list_slice(" + obj + ", u8, " + lower + ", " + upper + ")"
                return obj + "[" + lower + ".." + upper + "]"
            idx = self._render_expr(slice_node)
            if obj_type.startswith("dict["):
                # dict get with default
                val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(obj_type)
                parts = self._split_generic(obj_type[5:-1])
                key_expr = idx
                if len(parts) == 2:
                    if self._normalize_type(parts[0].strip()) != "str":
                        key_expr = "pytra.to_str(" + idx + ")"
                default_expr = "pytra.union_new_none()" if self._is_union_storage_zig(val_zig) else self._zig_zero_value(val_zig)
                return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + key_expr + ", " + default_expr + ")"
            if self._is_union_storage_zig(self._zig_type(obj_type)):
                result_type = self._lookup_expr_type(ed)
                result_zig = self._zig_type(result_type) if result_type != "" else "i64"
                if isinstance(slice_node, dict) and slice_node.get("kind") == "Constant" and isinstance(slice_node.get("value"), str):
                    key_expr = idx
                    if result_zig in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}:
                        return "@as(" + result_zig + ", @intCast(pytra.union_to_int(pytra.dict_get_default(*pytra.UnionVal, pytra.union_as_dict(" + obj + "), " + key_expr + ", pytra.union_new_none()))))"
                    if result_zig == "[]const u8":
                        return "pytra.union_as_str(pytra.dict_get_default(*pytra.UnionVal, pytra.union_as_dict(" + obj + "), " + key_expr + ", pytra.union_new_none()))"
                    return "pytra.dict_get_default(*pytra.UnionVal, pytra.union_as_dict(" + obj + "), " + key_expr + ", pytra.union_new_none())"
                if result_zig in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}:
                    return "@as(" + result_zig + ", @intCast(pytra.list_get(pytra.union_as_list(" + obj + "), i64, " + idx + ")))"
                return "pytra.list_get(pytra.union_as_list(" + obj + "), " + result_zig + ", " + idx + ")"
            if obj_type.startswith("list[") or obj_type in {"bytearray", "bytes"}:
                elem_type = "i64"
                if obj_type.startswith("list[") and obj_type.endswith("]"):
                    elem_type = self._zig_type(obj_type[5:-1].strip())
                elif obj_type in {"bytearray", "bytes"}:
                    elem_type = "u8"
                return self._render_bounds_checked_index(
                    obj,
                    idx,
                    "pytra.list_len(" + obj + ", " + elem_type + ")",
                    "pytra.list_get(" + obj + ", " + elem_type + ", " + idx + ")",
                    elem_type,
                )
            if obj_type.startswith("tuple["):
                idx_node = slice_node if isinstance(slice_node, dict) else None
                idx_val: Any = None
                if isinstance(idx_node, dict) and idx_node.get("kind") == "Constant":
                    idx_val = idx_node.get("value")
                if isinstance(idx_val, int) and not isinstance(idx_val, bool):
                    if ": {" in obj:
                        obj = "(" + obj + ")"
                    return obj + "._" + str(idx_val)
            if isinstance(value_node, dict) and value_node.get("kind") == "Attribute":
                owner_node = value_node.get("value")
                idx_node2 = slice_node if isinstance(slice_node, dict) else None
                idx_val2: Any = None
                if isinstance(idx_node2, dict) and idx_node2.get("kind") == "Constant":
                    idx_val2 = idx_node2.get("value")
                if (
                    isinstance(owner_node, dict)
                    and owner_node.get("kind") == "Name"
                    and owner_node.get("resolved_type") == "type"
                    and isinstance(idx_val2, int)
                    and not isinstance(idx_val2, bool)
                ):
                    return obj + "._" + str(idx_val2)
            # 文字列インデックス: str[i]
            if obj_type == "str":
                result_type = self._lookup_expr_type(ed)
                if result_type in {"byte", "uint8", "u8"}:
                    return self._render_bounds_checked_index(
                        obj,
                        idx,
                        obj + ".len",
                        obj + "[@intCast(" + idx + ")]",
                        "u8",
                    )
                return self._render_bounds_checked_index(
                    obj,
                    idx,
                    obj + ".len",
                    "pytra.str_index(" + obj + ", " + idx + ")",
                    "[]const u8",
                )
            return obj + "[@intCast(" + idx + ")]"
        if kind == "List":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            resolved = self._get_expr_type(ed)
            if resolved.startswith("list["):
                inner = resolved[5:-1].strip() if resolved.endswith("]") else ""
                zig_elem = self._zig_type(inner) if inner != "" else "i64"
                if self._is_union_storage_zig(zig_elem):
                    items = ["pytra.union_wrap(" + item + ")" for item in items]
                # タプル型要素の list はブロック式で make_list + append に展開
                if inner.startswith("tuple["):
                    if len(items) == 0:
                        return "pytra.make_list(" + zig_elem + ")"
                    blk_label, list_name = self._make_stmt_renderer().next_tuple_list_literal_names()
                    parts: list[str] = []
                    parts.append("const " + list_name + " = pytra.make_list(" + zig_elem + ");")
                    for item in items:
                        parts.append(" pytra.list_append(" + list_name + ", " + zig_elem + ", " + item + ");")
                    return self._make_stmt_renderer().render_simple_block_expr(blk_label, "".join(parts), list_name)
                return "pytra.list_from(" + zig_elem + ", &[_]" + zig_elem + "{ " + ", ".join(items) + " })"
            if len(items) == 0:
                return "pytra.list_from(i64, &[_]i64{})"
            return "&.{ " + ", ".join(items) + " }"
        if kind == "Tuple":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            # 名前付きフィールドの struct リテラルを生成 (._0, ._1, ...)
            field_inits: list[str] = []
            j = 0
            while j < len(items):
                field_inits.append("._" + str(j) + " = " + items[j])
                j += 1
            return ".{ " + ", ".join(field_inits) + " }"
        if kind == "Set":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            resolved = self._get_expr_type(ed)
            inner = ""
            if resolved.startswith("set[") and resolved.endswith("]"):
                inner = resolved[4:-1].strip()
            zig_elem = self._zig_type(inner) if inner != "" else "i64"
            return "pytra.list_from(" + zig_elem + ", &[_]" + zig_elem + "{ " + ", ".join(items) + " })"
        if kind == "Dict":
            return self._render_dict(ed)
        if kind == "JoinedStr":
            return self._render_joined_str(ed)
        if kind == "IfExp":
            test = self._render_cond_expr(ed.get("test"))
            body_node = ed.get("body")
            orelse_node = ed.get("orelse")
            body_expr = self._render_expr(body_node)
            orelse_expr = self._render_expr(orelse_node)
            if ": {" in body_expr:
                body_expr = "(" + body_expr + ")"
            if ": {" in orelse_expr:
                orelse_expr = "(" + orelse_expr + ")"
            # comptime_int リテラルを @as(i64, ...) にキャスト
            if isinstance(body_node, dict) and body_node.get("kind") == "Constant" and isinstance(body_node.get("value"), int):
                body_expr = "@as(i64, " + body_expr + ")"
            if isinstance(orelse_node, dict) and orelse_node.get("kind") == "Constant" and isinstance(orelse_node.get("value"), int):
                orelse_expr = "@as(i64, " + orelse_expr + ")"
            return "if (" + test + ") " + body_expr + " else " + orelse_expr
        if kind == "FormattedValue":
            value_expr = self._render_expr(ed.get("value"))
            spec = ""
            spec_node = ed.get("format_spec")
            if isinstance(spec_node, str):
                spec = spec_node
            if isinstance(spec_node, dict):
                if spec_node.get("kind") == "Constant" and isinstance(spec_node.get("value"), str):
                    spec = str(spec_node.get("value"))
                elif spec_node.get("kind") == "JoinedStr":
                    values_any = spec_node.get("values")
                    values = values_any if isinstance(values_any, list) else []
                    if len(values) == 1 and isinstance(values[0], dict) and values[0].get("kind") == "Constant" and isinstance(values[0].get("value"), str):
                        spec = str(values[0].get("value"))
            if spec.endswith("d") and spec[:-1].isdigit():
                width = str(int(spec[:-1], 10))
                if spec[:-1].startswith("0") and len(spec[:-1]) > 1:
                    return "pytra.format_int_zero_width(" + value_expr + ", " + width + ")"
                return "pytra.format_int_width(" + value_expr + ", " + width + ")"
            if spec == "+d":
                return "pytra.format_int_sign(" + value_expr + ")"
            if spec.endswith("x") and spec[:-1].isdigit():
                return "pytra.format_int_hex_width(" + value_expr + ", " + str(int(spec[:-1], 10)) + ", false)"
            if spec.endswith("X") and spec[:-1].isdigit():
                return "pytra.format_int_hex_width(" + value_expr + ", " + str(int(spec[:-1], 10)) + ", true)"
            if spec == ",d":
                return "pytra.format_int_grouped(" + value_expr + ")"
            if spec.startswith(".") and spec.endswith("%") and spec[1:-1].isdigit():
                return "pytra.format_percent_precision(" + value_expr + ", " + spec[1:-1] + ")"
            if spec.endswith("s") and spec.startswith("<") and spec[1:-1].isdigit():
                return "pytra.format_str_left_width(" + value_expr + ", " + spec[1:-1] + ")"
            if spec.endswith("f") and "." in spec and spec[:-1].replace(".", "", 1).isdigit():
                width_text, precision_text = spec[:-1].split(".", 1)
                if width_text and precision_text and width_text.isdigit() and precision_text.isdigit():
                    return "pytra.format_float_width_precision(" + value_expr + ", " + width_text + ", " + precision_text + ")"
            if spec.startswith(".") and spec.endswith("f") and spec[1:-1].isdigit():
                return "pytra.format_float_precision(" + value_expr + ", " + spec[1:-1] + ")"
            return value_expr
        if kind == "Lambda":
            arg_order_any = ed.get("arg_order")
            args = arg_order_any if isinstance(arg_order_any, list) else []
            arg_names = [_safe_ident(a, "arg") for a in args]
            arg_types_any = ed.get("arg_types")
            arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
            capture_names = self._collect_lambda_captures(ed.get("body"), arg_names)
            capture_fields: list[str] = []
            capture_inits: list[str] = []
            lambda_type_map: dict[str, str] = {}
            for arg_name in arg_names:
                raw_type_any = arg_types.get(arg_name)
                arg_type = raw_type_any.strip() if isinstance(raw_type_any, str) else ""
                if arg_type != "":
                    lambda_type_map[arg_name] = arg_type
            capture_rewrites: dict[str, str] = {}
            for capture_name in capture_names:
                capture_type = self._current_type_map().get(capture_name, "")
                if capture_type != "":
                    lambda_type_map[capture_name] = capture_type
                capture_fields.append(capture_name + ": " + self._zig_type(capture_type))
                capture_inits.append("." + capture_name + " = " + capture_name)
                capture_rewrites[capture_name] = "self." + capture_name
            arg_parts: list[str] = []
            for i, arg_name in enumerate(arg_names):
                raw_name = args[i] if i < len(args) else arg_name
                raw_type_any = arg_types.get(raw_name)
                if not isinstance(raw_type_any, str):
                    raw_type_any = arg_types.get(arg_name)
                arg_type = raw_type_any.strip() if isinstance(raw_type_any, str) else ""
                arg_parts.append(arg_name + ": " + self._zig_type(arg_type))
            ret_type = self._zig_type(str(ed.get("return_type", "")))
            self._local_type_stack.append(lambda_type_map)
            self._lambda_capture_stack.append(capture_rewrites)
            body_expr = self._render_expr(ed.get("body"))
            self._lambda_capture_stack.pop()
            self._local_type_stack.pop()
            self_param = "self: @This()"
            if len(capture_names) == 0:
                self_param = "_: @This()"
            method_args = [self_param]
            method_args.extend(arg_parts)
            field_decl = ""
            if len(capture_fields) > 0:
                field_decl = ", ".join(capture_fields) + ", "
            init_expr = "{}"
            if len(capture_inits) > 0:
                init_expr = "{ " + ", ".join(capture_inits) + " }"
            return "struct { " + field_decl + "pub fn call(" + ", ".join(method_args) + ") " + ret_type + " { return " + body_expr + "; } }" + init_expr
        if kind == "ListComp":
            return self._render_list_comp(ed)
        if kind == "SetComp":
            return self._render_set_comp(ed)
        if kind == "DictComp":
            return self._render_dict_comp(ed)
        if kind == "GeneratorExp":
            return "pytra.empty_list()"
        if kind == "Starred":
            return self._render_expr(ed.get("value"))
        if kind == "Slice":
            lower = self._render_expr(ed.get("lower")) if isinstance(ed.get("lower"), dict) else "0"
            upper = self._render_expr(ed.get("upper")) if isinstance(ed.get("upper"), dict) else "null"
            return "pytra.slice(" + lower + ", " + upper + ")"
        if kind == "IsInstance":
            return self._render_isinstance(ed)
        return "null"

    def _render_isinstance(self, node: dict[str, Any]) -> str:
        """IsInstance ノードをレンダリングする。"""
        value_node = node.get("value")
        type_node = node.get("expected_type_id")
        target_type = ""
        if isinstance(type_node, dict):
            if type_node.get("kind") == "Tuple":
                checks: list[str] = []
                elements_any = type_node.get("elements")
                elements = elements_any if isinstance(elements_any, list) else []
                for elem in elements:
                    if not isinstance(elem, dict):
                        continue
                    elem_target = ""
                    if elem.get("kind") == "Name":
                        elem_target = str(elem.get("id", ""))
                    elif elem.get("kind") == "Attribute":
                        elem_target = str(elem.get("attr", ""))
                    if elem_target != "":
                        checks.append(self._render_isinstance({
                            "kind": "IsInstance",
                            "value": value_node,
                            "expected_type_name": elem_target,
                        }))
                return "(" + " or ".join(checks) + ")" if len(checks) > 0 else "false"
            raw_type_id = type_node.get("id")
            target_type = self._normalize_type(str(raw_type_id)) if isinstance(raw_type_id, str) else ""
        expected_name = node.get("expected_type_name")
        if target_type == "" and isinstance(expected_name, str):
            target_type = self._normalize_type(expected_name)
        if not isinstance(value_node, dict) or target_type == "":
            return "false"
        obj_type = self._get_expr_type(value_node)
        value_expr = self._render_expr(value_node)
        if obj_type in {"", "unknown", "Any", "object"} or self._zig_type(obj_type) == "pytra.Obj":
            obj_type = _safe_ident(value_node.get("id"), "")
            obj_type = self._current_type_map().get(obj_type, "")
        norm_obj_type = self._normalize_type(obj_type)
        obj_zig_type = self._zig_type(norm_obj_type) if norm_obj_type != "" else ""
        builtin_targets = {
            "dict", "list", "tuple", "set", "str", "bool",
            "int", "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64",
            "float", "float32", "float64", "None",
        }
        if target_type in self.class_names:
            runtime_checks: list[str] = []
            for cls_name in sorted(self.class_names):
                if not self._is_subclass_of(cls_name, target_type):
                    continue
                if self._has_vtable(cls_name):
                    runtime_checks.append("(@TypeOf(" + value_expr + ") == pytra.Obj and " + value_expr + ".vtable == @as(*const anyopaque, @ptrCast(&" + cls_name + "_vt)))")
                else:
                    runtime_checks.append("(@TypeOf(" + value_expr + ") == *" + cls_name + ")")
            if len(runtime_checks) > 0 and (norm_obj_type.find("|") != -1 or norm_obj_type in {"", "unknown", "Any", "object"}):
                return "(" + " or ".join(runtime_checks) + ")"
        if target_type in builtin_targets and (
            norm_obj_type.find("|") != -1
            or norm_obj_type in {"", "unknown", "Any", "object", "JsonVal"}
            or self._is_union_storage_zig(obj_zig_type)
        ):
            return "pytra.isinstance_check(" + value_expr + ", " + _zig_string(target_type) + ")"
        if obj_type == "" or target_type == "":
            return "false"
        if self._is_subclass_of(obj_type, target_type):
            return "true"
        if target_type in builtin_targets:
            return "pytra.isinstance_check(" + value_expr + ", " + _zig_string(target_type) + ")"
        return "false"

    def _is_subclass_of(self, cls: str, base: str) -> bool:
        """cls が base と同一か、base の子孫かを判定する。"""
        current = cls
        while current != "":
            if current == base:
                return True
            current = self._class_base.get(current, "")
        return False

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
        prev_node = node.get("left")
        i = 0
        while i < len(ops):
            right = self._render_expr(comparators[i])
            op_str = str(ops[i])
            if op_str == "In":
                range_expr = self._render_range_contains(prev, comparators[i], negate=False)
                if range_expr != "":
                    parts.append(range_expr)
                    prev = right
                    prev_node = comparators[i]
                    i += 1
                    continue
                right_type = self._lookup_expr_type(comparators[i]) if isinstance(comparators[i], dict) else ""
                needle_expr = prev
                if right_type.startswith("dict[") and right_type.endswith("]"):
                    dparts = self._split_generic(right_type[5:-1])
                    if len(dparts) == 2 and self._normalize_type(dparts[0].strip()) != "str":
                        needle_expr = "pytra.to_str(" + prev + ")"
                else:
                    needle_expr = self._coerce_membership_needle(needle_expr, prev_node, right_type)
                parts.append("pytra.contains(" + right + ", " + needle_expr + ")")
            elif op_str == "NotIn":
                range_expr = self._render_range_contains(prev, comparators[i], negate=True)
                if range_expr != "":
                    parts.append(range_expr)
                    prev = right
                    prev_node = comparators[i]
                    i += 1
                    continue
                right_type = self._lookup_expr_type(comparators[i]) if isinstance(comparators[i], dict) else ""
                needle_expr = prev
                if right_type.startswith("dict[") and right_type.endswith("]"):
                    dparts = self._split_generic(right_type[5:-1])
                    if len(dparts) == 2 and self._normalize_type(dparts[0].strip()) != "str":
                        needle_expr = "pytra.to_str(" + prev + ")"
                else:
                    needle_expr = self._coerce_membership_needle(needle_expr, prev_node, right_type)
                parts.append("!pytra.contains(" + right + ", " + needle_expr + ")")
            else:
                # 文字列比較は std.mem.eql を使う
                effective_prev_node = prev_node
                if isinstance(effective_prev_node, dict) and effective_prev_node.get("kind") == "Unbox" and isinstance(effective_prev_node.get("value"), dict):
                    effective_prev_node = effective_prev_node.get("value")
                effective_cmp_node = comparators[i]
                if isinstance(effective_cmp_node, dict) and effective_cmp_node.get("kind") == "Unbox" and isinstance(effective_cmp_node.get("value"), dict):
                    effective_cmp_node = effective_cmp_node.get("value")
                left_type = self._lookup_expr_type(effective_prev_node) if isinstance(effective_prev_node, dict) else ""
                right_type = self._lookup_expr_type(effective_cmp_node) if isinstance(effective_cmp_node, dict) else ""
                if (right == "null" or prev == "null") and op_str in ("Is", "IsNot", "Eq", "NotEq"):
                    obj_type = left_type if right == "null" else right_type
                    obj_expr = prev if right == "null" else right
                    if isinstance(effective_prev_node, dict) and effective_prev_node.get("kind") == "Name":
                        safe_prev_name = _safe_ident(effective_prev_node.get("id"), "")
                        storage_prev_type = self._current_storage_type_map().get(safe_prev_name, "")
                        if isinstance(storage_prev_type, str) and storage_prev_type != "":
                            obj_type = storage_prev_type
                        else:
                            raw_prev_type = self._get_expr_type(effective_prev_node)
                            if isinstance(raw_prev_type, str) and raw_prev_type != "":
                                obj_type = raw_prev_type
                            else:
                                actual_prev_type = self._current_type_map().get(safe_prev_name, "")
                                if isinstance(actual_prev_type, str) and actual_prev_type != "":
                                    obj_type = actual_prev_type
                    if self._is_optional_callable_type(obj_type) or self._is_callable_type(obj_type):
                        if self._is_callable_type(obj_type) and not self._is_optional_callable_type(obj_type):
                            bool_text = "false" if op_str in {"Is", "Eq"} else "true"
                            parts.append(
                                self._make_stmt_renderer().render_simple_block_expr(
                                    "blk",
                                    "_ = " + obj_expr + ";",
                                    bool_text,
                                )
                            )
                        else:
                            parts.append((obj_expr + " == null") if op_str in {"Is", "Eq"} else (obj_expr + " != null"))
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if self._is_union_storage_zig(self._zig_type(obj_type)) or self._normalize_type(obj_type) in {"Any", "object", "unknown"}:
                        is_none_call = "pytra.is_none_any(" + obj_expr + ")"
                        parts.append(is_none_call if op_str in {"Is", "Eq"} else "!" + is_none_call)
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if obj_type in self.class_names:
                        bool_text = "false" if op_str in {"Is", "Eq"} else "true"
                        parts.append(bool_text)
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if obj_type in self._known_imported_nominals:
                        bool_text = "false" if op_str in {"Is", "Eq"} else "true"
                        parts.append(bool_text)
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if self._is_callable_type(obj_type) and not self._is_optional_callable_type(obj_type):
                        bool_text = "false" if op_str in {"Is", "Eq"} else "true"
                        parts.append(
                            self._make_stmt_renderer().render_simple_block_expr(
                                "blk",
                                "_ = " + (prev if right == "null" else right) + ";",
                                bool_text,
                            )
                        )
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                is_str_cmp = (left_type == "str" or right_type == "str")
                if op_str in ("Eq", "NotEq"):
                    left_zig_type = self._zig_type(left_type) if left_type != "" else ""
                    right_zig_type = self._zig_type(right_type) if right_type != "" else ""
                    if left_type == "str" and right_type not in {"", "str"} and not self._is_union_storage_zig(right_zig_type):
                        parts.append("false" if op_str == "Eq" else "true")
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if right_type == "str" and left_type not in {"", "str"} and not self._is_union_storage_zig(left_zig_type):
                        parts.append("false" if op_str == "Eq" else "true")
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if self._is_union_storage_zig(left_zig_type) and right_type == "str":
                        eql_call = "(pytra.isinstance_check(" + prev + ", \"str\") and std.mem.eql(u8, pytra.union_as_str(" + prev + "), " + right + "))"
                        parts.append(eql_call if op_str == "Eq" else "!" + eql_call)
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                    if self._is_union_storage_zig(right_zig_type) and left_type == "str":
                        eql_call = "(pytra.isinstance_check(" + right + ", \"str\") and std.mem.eql(u8, " + prev + ", pytra.union_as_str(" + right + ")))"
                        parts.append(eql_call if op_str == "Eq" else "!" + eql_call)
                        prev = right
                        prev_node = comparators[i]
                        i += 1
                        continue
                if is_str_cmp and op_str in ("Eq", "NotEq"):
                    char_cmp = ""
                    if left_type in {"byte", "uint8", "u8"} and right.startswith("\"") and right.endswith("\"") and len(right) == 3:
                        char_cmp = prev + " == '" + right[1] + "'"
                    elif right_type in {"byte", "uint8", "u8"} and prev.startswith("\"") and prev.endswith("\"") and len(prev) == 3:
                        char_cmp = right + " == '" + prev[1] + "'"
                    eql_call = char_cmp if char_cmp != "" else "std.mem.eql(u8, " + prev + ", " + right + ")"
                    if op_str == "Eq":
                        parts.append(eql_call)
                    else:
                        parts.append("!" + eql_call)
                elif is_str_cmp and op_str in ("Lt", "LtE", "Gt", "GtE"):
                    order_expr = "std.mem.order(u8, " + prev + ", " + right + ")"
                    if op_str == "Lt":
                        parts.append(order_expr + " == .lt")
                    elif op_str == "LtE":
                        parts.append(order_expr + " != .gt")
                    elif op_str == "Gt":
                        parts.append(order_expr + " == .gt")
                    else:
                        parts.append(order_expr + " != .lt")
                else:
                    sym = _cmp_symbol(op_str)
                    parts.append(prev + " " + sym + " " + right)
            prev = right
            prev_node = comparators[i]
            i += 1
        if len(parts) == 1:
            return parts[0]
        return "(" + " and ".join(parts) + ")"

    def _coerce_membership_needle(self, needle_expr: str, needle_node: Any, container_type: str) -> str:
        if not isinstance(needle_node, dict) or needle_node.get("kind") != "Tuple":
            return needle_expr
        norm = self._normalize_type(container_type)
        elem_type = ""
        if norm.startswith("list[") and norm.endswith("]"):
            elem_type = norm[5:-1].strip()
        elif norm.startswith("set[") and norm.endswith("]"):
            elem_type = norm[4:-1].strip()
        if not elem_type.startswith("tuple["):
            return needle_expr
        return "@as(" + self._zig_type(elem_type) + ", " + needle_expr + ")"

    def _render_range_contains(self, needle_expr: str, comparator: Any, *, negate: bool) -> str:
        if not isinstance(comparator, dict) or comparator.get("kind") != "Call":
            return ""
        func = comparator.get("func")
        if not isinstance(func, dict) or func.get("kind") != "Name" or _safe_ident(func.get("id"), "") != "range":
            return ""
        args_any = comparator.get("args")
        args = args_any if isinstance(args_any, list) else []
        if len(args) == 0 or len(args) > 3:
            return ""
        start = "0"
        end = self._render_expr(args[0])
        step = "1"
        if len(args) >= 2:
            start = self._render_expr(args[0])
            end = self._render_expr(args[1])
        if len(args) == 3:
            step = self._render_expr(args[2])
        if step == "1":
            expr = "((" + needle_expr + " >= " + start + ") and (" + needle_expr + " < " + end + "))"
        else:
            expr = "((" + step + " > 0 and " + needle_expr + " >= " + start + " and " + needle_expr + " < " + end + " and @mod(" + needle_expr + " - " + start + ", " + step + ") == 0) or (" + step + " < 0 and " + needle_expr + " <= " + start + " and " + needle_expr + " > " + end + " and @mod(" + start + " - " + needle_expr + ", -(" + step + ")) == 0))"
        return "!" + expr if negate else expr

    def _render_call(self, node: dict[str, Any]) -> str:
        func_any = node.get("func")
        args_any = node.get("args")
        args = args_any if isinstance(args_any, list) else []
        arg_strs = [self._render_expr(a) for a in args]
        i = 0
        while i < len(args):
            arg_node = args[i]
            if isinstance(arg_node, dict) and arg_node.get("kind") == "Name":
                arg_name = _safe_ident(arg_node.get("id"), "")
                if arg_name in self._current_exception_vars():
                    arg_strs[i] = arg_name + ".msg"
            if isinstance(arg_node, dict) and arg_node.get("kind") == "Call":
                inner_func = arg_node.get("func")
                inner_args_any = arg_node.get("args")
                inner_args = inner_args_any if isinstance(inner_args_any, list) else []
                if (
                    isinstance(inner_func, dict)
                    and inner_func.get("kind") == "Name"
                    and inner_func.get("id") == "str"
                    and len(inner_args) == 1
                    and isinstance(inner_args[0], dict)
                    and inner_args[0].get("kind") == "Name"
                ):
                    arg_name = _safe_ident(inner_args[0].get("id"), "")
                    if arg_name in self._current_exception_vars():
                        arg_strs[i] = arg_name + ".msg"
            arg_text = arg_strs[i]
            for exc_name in self._current_exception_vars():
                if arg_text == "pytra.to_str(" + exc_name + ")":
                    arg_strs[i] = exc_name + ".msg"
            i += 1
        if isinstance(func_any, dict):
            fkind = func_any.get("kind")
            if fkind == "Attribute":
                attr_name = _safe_ident(func_any.get("attr"), "")
                owner_node = func_any.get("value")
                owner_name = ""
                if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                    owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in {"json", "pytra_std_json"} and attr_name == "JsonValue":
                    arg0 = arg_strs[0] if len(arg_strs) > 0 else "null"
                    return "pytra.make_object(JsonValue, JsonValue.init(" + arg0 + "))"
            if fkind == "Name":
                fname = _safe_ident(func_any.get("id"), "fn_")
                rendered_name = self._render_expr(func_any)
                # Python main → EAST __pytra_main リネーム対応
                if fname == "main" and "__pytra_main" in self.function_names:
                    fname = "__pytra_main"
                    rendered_name = fname
                if fname == "field":
                    return "undefined"
                if fname == "print":
                    if len(arg_strs) == 0:
                        return "pytra.print(\"\")"
                    if len(args) == 1 and isinstance(args[0], dict):
                        arg_t = self._lookup_expr_type(args[0])
                        if arg_t.startswith("list[") and arg_t.endswith("]"):
                            elem_t = self._zig_type(arg_t[5:-1].strip())
                            return "pytra.print_list(" + elem_t + ", " + arg_strs[0] + ")"
                    if len(args) == 1 and isinstance(args[0], dict) and args[0].get("kind") == "Name":
                        arg_name = _safe_ident(args[0].get("id"), "")
                        if arg_name in self._current_exception_vars():
                            return "pytra.print(" + arg_name + ".msg)"
                    if len(arg_strs) == 1:
                        return "pytra.print(" + arg_strs[0] + ")"
                    if len(arg_strs) == 2:
                        return "pytra.print2(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                    if len(arg_strs) == 3:
                        return "pytra.print3(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ")"
                    if len(arg_strs) == 4:
                        return "pytra.print4(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ", " + arg_strs[3] + ")"
                    return "pytra.print(" + arg_strs[0] + ")"
                if fname == "len":
                    if len(args) > 0:
                        len_arg = arg_strs[0]
                        if isinstance(args[0], dict) and args[0].get("kind") in {"Call", "Compare", "BoolOp", "BinOp", "IfExp", "Subscript", "Attribute"}:
                            len_arg = "(" + len_arg + ")"
                        arg_t = self._get_expr_type(args[0])
                        if hasattr(self, "_import_alias_map") and arg_t in self._import_alias_map:
                            return len_arg + ".__len__()"
                        if arg_t.startswith("dict["):
                            return "@as(i64, @intCast(" + len_arg + ".count()))"
                        if arg_t.startswith("list[") or arg_t.startswith("set[") or arg_t in {"bytearray", "bytes"}:
                            elem = "i64"
                            if (arg_t.startswith("list[") or arg_t.startswith("set[")) and arg_t.endswith("]"):
                                inner_t = arg_t[5:-1].strip() if arg_t.startswith("list[") else arg_t[4:-1].strip()
                                elem = self._zig_type(inner_t)
                            elif arg_t in {"bytearray", "bytes"}:
                                elem = "u8"
                            return "pytra.list_len(" + len_arg + ", " + elem + ")"
                    if len(arg_strs) > 0:
                        len_arg = arg_strs[0]
                        if len(args) > 0 and isinstance(args[0], dict) and args[0].get("kind") in {"Call", "Compare", "BoolOp", "BinOp", "IfExp", "Subscript", "Attribute"}:
                            len_arg = "(" + len_arg + ")"
                        return "@as(i64, @intCast(" + len_arg + ".len))"
                    return "0"
                if fname == "int":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "":
                            arg_t = self._get_expr_type(args[0]) if len(args) > 0 else ""
                        arg_float_like = self._expr_is_float_like(args[0]) if len(args) > 0 and isinstance(args[0], dict) else False
                        norm_arg_t = self._normalize_type(arg_t)
                        if arg_t == "str":
                            return "pytra.str_to_int(" + arg_strs[0] + ")"
                        if norm_arg_t != "" and (self._is_subclass_of(norm_arg_t, "IntEnum") or self._is_subclass_of(norm_arg_t, "IntFlag")):
                            return "@as(i64, " + arg_strs[0] + ")"
                        if arg_t in {"float64", "float32", "float"} or arg_float_like:
                            return "@as(i64, @intFromFloat(" + arg_strs[0] + "))"
                        if arg_t in {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
                            return "@as(i64, @intCast(" + arg_strs[0] + "))"
                        if self._is_union_storage_zig(self._zig_type(arg_t)):
                            return "pytra.union_to_int(" + arg_strs[0] + ")"
                        # 型不明: @intFromFloat で安全に変換（int にも @as(f64,...) 経由で対応）
                        return "@as(i64, @intFromFloat(@as(f64, " + arg_strs[0] + ")))"
                    return "0"
                if fname == "float":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "":
                            arg_t = self._get_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "str":
                            return "pytra.str_to_float(" + arg_strs[0] + ")"
                        if arg_t == "bool":
                            return "if (" + arg_strs[0] + ") 1.0 else 0.0"
                        if self._is_union_storage_zig(self._zig_type(arg_t)):
                            return "pytra.union_to_float(" + arg_strs[0] + ")"
                        return "@as(f64, " + arg_strs[0] + ")"
                    return "0.0"
                if fname == "str":
                    if len(arg_strs) > 0:
                        if len(args) > 0 and isinstance(args[0], dict):
                            raw_arg = self._unwrap_box_unbox(args[0])
                            if isinstance(raw_arg, dict) and raw_arg.get("kind") == "List":
                                elts_any = raw_arg.get("elts")
                                if not isinstance(elts_any, list):
                                    elts_any = raw_arg.get("elements")
                                if isinstance(elts_any, list) and len(elts_any) == 0:
                                    return "\"[]\""
                            if isinstance(raw_arg, dict) and raw_arg.get("kind") == "Dict":
                                entries_any = raw_arg.get("entries")
                                if isinstance(entries_any, list) and len(entries_any) == 0:
                                    return "\"{}\""
                        if len(args) > 0 and isinstance(args[0], dict) and args[0].get("kind") == "Name":
                            arg_name = _safe_ident(args[0].get("id"), "")
                            if arg_name in self._current_exception_vars():
                                return arg_name + ".msg"
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t.startswith("list[list[") and arg_t.endswith("]]"):
                            inner_raw = arg_t[10:-2].strip()
                            return "pytra.list_repr_nested(" + self._zig_type(inner_raw) + ", " + arg_strs[0] + ")"
                        if arg_t.startswith("list[") and arg_t.endswith("]"):
                            return "pytra.list_repr(" + self._zig_type(arg_t[5:-1].strip()) + ", " + arg_strs[0] + ")"
                        if arg_t.startswith("dict[") and arg_t.endswith("]"):
                            parts = self._split_generic(arg_t[5:-1])
                            if len(parts) == 2 and self._normalize_type(parts[0].strip()) == "str":
                                return "pytra.dict_repr(" + self._zig_type(parts[1].strip()) + ", " + arg_strs[0] + ")"
                        if arg_t.startswith("tuple[") and arg_t.endswith("]"):
                            return "pytra.tuple_repr(" + arg_strs[0] + ")"
                        return "pytra.to_str(" + arg_strs[0] + ")"
                    return "\"\""
                if fname in {"repr", "py_repr"}:
                    if len(arg_strs) > 0:
                        return "pytra.to_str(" + arg_strs[0] + ")"
                    return "\"\""
                if fname == "dict":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.make_str_dict(*pytra.UnionVal)"
                if fname == "RuntimeError":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "\"RuntimeError\""
                if fname in {"bool", "bool_"}:
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if self._is_union_storage_zig(self._zig_type(arg_t)):
                            return "pytra.union_to_bool(" + arg_strs[0] + ")"
                        return "pytra.truthy(" + arg_strs[0] + ")"
                    return "false"
                if fname == "abs":
                    if len(arg_strs) > 0:
                        return "std.math.absInt(" + arg_strs[0] + ")"
                    return "0"
                if fname == "bytearray":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t.startswith("list["):
                            return "pytra.list_to_bytes(" + arg_strs[0] + ")"
                        if arg_t in {"bytearray", "bytes"}:
                            return "pytra.bytes_copy(" + arg_strs[0] + ")"
                        return "pytra.bytearray(" + arg_strs[0] + ")"
                    return "pytra.bytearray(0)"
                if fname == "bytes":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t.startswith("list["):
                            return "pytra.list_to_bytes(" + arg_strs[0] + ")"
                        if arg_t in {"bytearray", "bytes"}:
                            return "pytra.bytes_copy(" + arg_strs[0] + ")"
                        return arg_strs[0]
                    return "pytra.bytearray(0)"
                # perf_counter は @extern 委譲経由 (time モジュール) で提供
                # import されていれば perf_counter() としてアクセス可能
                if fname == "cast":
                    # cast(T, value) is a Python type narrowing hint.
                    if len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
                        type_name = ""
                        type_arg = args[0]
                        if type_arg.get("kind") == "Name":
                            type_name = self._normalize_type(_safe_ident(type_arg.get("id"), ""))
                        value_type = self._lookup_expr_type(args[1])
                        stripped_value = self._strip_optional_type(value_type) if value_type != "" else ""
                        value_type = self._lookup_expr_type(args[1])
                        value_zig = self._zig_type(value_type) if value_type != "" else ""
                        if type_name != "" and stripped_value != "" and self._normalize_type(type_name) == stripped_value:
                            return arg_strs[1] + ".?"
                        if type_name == "str" and (value_zig == "anytype" or self._is_union_storage_zig(value_zig)):
                            return "pytra._jv_as_str_any(" + arg_strs[1] + ").?"
                        if type_name in {"float", "float64", "float32"} and (value_zig == "anytype" or self._is_union_storage_zig(value_zig)):
                            return "pytra._jv_as_float_any(" + arg_strs[1] + ").?"
                        if type_name in {"int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"} and self._is_union_storage_zig(value_zig):
                            return "pytra.union_to_int(" + arg_strs[1] + ")"
                    if len(arg_strs) >= 2:
                        return arg_strs[1]
                    return arg_strs[0] if len(arg_strs) == 1 else "null"
                if fname == "@\"extern\"" or fname == "extern":
                    # @extern(value) → value を直接返す
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "0"
                if fname == "open":
                    result_type = self._lookup_expr_type(node) or self._get_expr_type(node)
                    mode_expr = arg_strs[1] if len(arg_strs) > 1 else "\"r\""
                    if len(arg_strs) > 0:
                        expr = "pytra.file_open(" + arg_strs[0] + ", " + mode_expr + ")"
                        if self._is_union_storage_zig(self._zig_type(result_type)):
                            return "pytra.union_wrap(" + expr + ")"
                        return expr
                    expr = "pytra.file_open(\"\", \"r\")"
                    if self._is_union_storage_zig(self._zig_type(result_type)):
                        return "pytra.union_wrap(" + expr + ")"
                    return expr
                if fname == "range":
                    return "pytra.empty_list()"
                if fname == "enumerate":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "sorted":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "list[int]" or arg_t == "list[int64]":
                            return "pytra.list_sorted_i64(" + arg_strs[0] + ")"
                        if arg_t == "list[str]":
                            return "pytra.list_sorted_str(" + arg_strs[0] + ")"
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "reversed":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "set":
                    return "pytra.empty_list()"
                if fname == "ord" and len(arg_strs) > 0:
                    return "pytra.ord(" + arg_strs[0] + ")"
                if fname == "chr" and len(arg_strs) > 0:
                    return "pytra.chr(" + arg_strs[0] + ")"
                if fname == "list":
                    if len(arg_strs) == 0:
                        return "pytra.empty_list()"
                    if len(args) > 0:
                        arg_t = self._lookup_expr_type(args[0])
                        arg_zig = self._zig_type(arg_t) if arg_t != "" else ""
                        if arg_zig.startswith("?") and arg_zig[1:] == "pytra.Obj":
                            return arg_strs[0] + ".?"
                        if arg_t.startswith("list[") or arg_t in {"bytearray", "bytes"} or self._zig_type(arg_t) == "pytra.Obj":
                            return arg_strs[0]
                        if arg_t == "str":
                            return "pytra.str_chars(" + arg_strs[0] + ")"
                    return arg_strs[0]
                if fname == "sum":
                    if len(arg_strs) > 0 and len(args) > 0:
                        arg_t = self._lookup_expr_type(args[0])
                        elem_t = "i64"
                        acc_zero = "0"
                        if arg_t.startswith("list[") and arg_t.endswith("]"):
                            elem_t = self._zig_type(arg_t[5:-1].strip())
                            if elem_t in {"f64", "f32"}:
                                acc_zero = "0.0"
                        blk, acc_name, item_name = self._make_stmt_renderer().next_sum_names()
                        return self._make_stmt_renderer().render_simple_block_expr(
                            blk,
                            "var "
                            + acc_name
                            + ": "
                            + elem_t
                            + " = "
                            + acc_zero
                            + "; for (pytra.list_items("
                            + arg_strs[0]
                            + ", "
                            + elem_t
                            + ")) |"
                            + item_name
                            + "| { "
                            + acc_name
                            + " += "
                            + item_name
                            + "; }",
                            acc_name,
                        )
                    return "0"
                if fname == "zip":
                    if len(arg_strs) == 2 and len(args) == 2:
                        left_t = self._lookup_expr_type(args[0])
                        right_t = self._lookup_expr_type(args[1])
                        left_elem = "i64"
                        right_elem = "i64"
                        left_items = arg_strs[0]
                        right_items = arg_strs[1]
                        if left_t.startswith("list[") and left_t.endswith("]"):
                            left_elem = self._zig_type(left_t[5:-1].strip())
                            left_items = "pytra.list_items(" + arg_strs[0] + ", " + left_elem + ")"
                        elif left_t == "str":
                            left_elem = "[]const u8"
                            left_items = "pytra.list_items(pytra.str_chars(" + arg_strs[0] + "), []const u8)"
                        if right_t.startswith("list[") and right_t.endswith("]"):
                            right_elem = self._zig_type(right_t[5:-1].strip())
                            right_items = "pytra.list_items(" + arg_strs[1] + ", " + right_elem + ")"
                        elif right_t == "str":
                            right_elem = "[]const u8"
                            right_items = "pytra.list_items(pytra.str_chars(" + arg_strs[1] + "), []const u8)"
                        tuple_type = "Tuple0"
                        call_t = self._get_expr_type(node)
                        if call_t.startswith("list[tuple[") and call_t.endswith("]]"):
                            tuple_type = self._zig_type(call_t[5:-1].strip())
                        blk, left_name, right_name, out_name, idx_name = self._make_stmt_renderer().next_zip_names()
                        return self._make_stmt_renderer().render_simple_block_expr(
                            blk,
                            "const "
                            + left_name
                            + " = "
                            + left_items
                            + "; const "
                            + right_name
                            + " = "
                            + right_items
                            + "; const "
                            + out_name
                            + " = pytra.make_list("
                            + tuple_type
                            + "); var "
                            + idx_name
                            + ": usize = 0; while ("
                            + idx_name
                            + " < @min("
                            + left_name
                            + ".len, "
                            + right_name
                            + ".len)) : ("
                            + idx_name
                            + " += 1) { pytra.list_append("
                            + out_name
                            + ", "
                            + tuple_type
                            + ", .{ ._0 = "
                            + left_name
                            + "["
                            + idx_name
                            + "], ._1 = "
                            + right_name
                            + "["
                            + idx_name
                            + "] }); }",
                            out_name,
                        )
                if fname == "min":
                    if len(arg_strs) >= 2:
                        return "@min(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "max":
                    if len(arg_strs) >= 2:
                        return "@max(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "isinstance":
                    if len(args) >= 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
                        type_node = args[1]
                        if type_node.get("kind") == "Tuple":
                            checks: list[str] = []
                            elements_any = type_node.get("elements")
                            elements = elements_any if isinstance(elements_any, list) else []
                            for elem in elements:
                                if not isinstance(elem, dict):
                                    continue
                                elem_target = ""
                                if elem.get("kind") == "Name":
                                    elem_target = str(elem.get("id", ""))
                                elif elem.get("kind") == "Attribute":
                                    elem_target = str(elem.get("attr", ""))
                                if elem_target != "":
                                    checks.append(self._render_isinstance({
                                        "kind": "IsInstance",
                                        "value": args[0],
                                        "expected_type_name": elem_target,
                                    }))
                            return "(" + " or ".join(checks) + ")" if len(checks) > 0 else "false"
                        target = ""
                        if type_node.get("kind") == "Name":
                            target = str(type_node.get("id", ""))
                        elif type_node.get("kind") == "Attribute":
                            target = str(type_node.get("attr", ""))
                        if target != "":
                            return self._render_isinstance({
                                "kind": "IsInstance",
                                "value": args[0],
                                "expected_type_name": target,
                            })
                    return "pytra.isinstance_check(" + ", ".join(arg_strs) + ")"
                if fname == "py_assert_stdout":
                    return "true"
                # Local class or imported class constructor (resolved_type matches func name)
                call_resolved = str(node.get("resolved_type", ""))
                is_local_class = fname in self.class_names
                is_imported_class = (
                    not is_local_class
                    and hasattr(self, "_import_alias_map")
                    and fname in self._import_alias_map
                    and (call_resolved == fname or (isinstance(func_any, dict) and func_any.get("resolved_type") == "type"))
                )
                if is_imported_class:
                    init_order = self._class_method_arg_order.get(fname, {}).get("__init__", [])
                    if len(init_order) > 1:
                        arg_strs = self._fill_args_with_keywords(
                            node,
                            arg_strs,
                            init_order[1:],
                            self._class_init_defaults.get(fname, []),
                            self._class_init_default_types.get(fname, []),
                        )
                    # Imported class: use Type.init(args)
                    return "pytra.make_object(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "))"
                if is_local_class:
                    if fname in self._classes_with_init:
                        init_order = self._class_method_arg_order.get(fname, {}).get("__init__", [])
                        arg_strs = self._fill_args_with_keywords(
                            node,
                            arg_strs,
                            init_order[1:] if len(init_order) > 1 else [],
                            self._class_init_defaults.get(fname, []),
                            self._class_init_default_types.get(fname, []),
                        )
                    if self._has_vtable(fname):
                        vt_inst = "&" + fname + "_vt"
                        drop_arg = fname + "_drop_wrap" if fname in self._classes_with_del else "null"
                        make_fn = "pytra.make_obj_drop"
                        if fname in self._classes_with_init:
                            return make_fn + "(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "), @ptrCast(" + vt_inst + "), " + drop_arg + ")"
                        return make_fn + "(" + fname + ", " + fname + "{}, @ptrCast(" + vt_inst + "), " + drop_arg + ")"
                    if fname in self._dataclass_names:
                        fields = self._dataclass_fields.get(fname, [])
                        field_inits: list[str] = []
                        j = 0
                        while j < len(fields) and j < len(arg_strs):
                            field_inits.append("." + fields[j] + " = " + arg_strs[j])
                            j += 1
                        return "pytra.make_object(" + fname + ", " + fname + "{ " + ", ".join(field_inits) + " })"
                    if fname in self._classes_with_init:
                        return "pytra.make_object(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "))"
                    return "pytra.make_object(" + fname + ", " + fname + "{})"
                func_type = self._lookup_expr_type(func_any)
                call_arg_strs = self._coerce_call_args_for_signature(arg_strs, args, func_type, func_any)
                if self._is_callable_type(func_type) or self._is_optional_callable_type(func_type):
                    return self._render_callable_invoke(rendered_name, call_arg_strs, func_type)
                return rendered_name + "(" + ", ".join(call_arg_strs) + ")"
            if fkind == "Attribute":
                obj_node_for_attr = func_any.get("value")
                attr = _safe_ident(func_any.get("attr"), "method")
                runtime_symbol = node.get("runtime_symbol")
                # super().method() → BaseClass.method(undefined)
                if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") == "Call":
                    super_func = obj_node_for_attr.get("func")
                    if isinstance(super_func, dict) and super_func.get("kind") == "Name" and super_func.get("id") == "super":
                        base = self._class_base.get(self.current_class_name, "")
                        if base != "":
                            if attr == "__init__" and base not in self.class_names:
                                return ""
                            if attr == "__init__":
                                return "self._base = " + base + ".init(" + ", ".join(arg_strs) + ")"
                            return "self._base." + attr + "(" + ", ".join(arg_strs) + ")"
                obj = self._render_expr(obj_node_for_attr)
                if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") in {"Subscript", "Call", "Compare", "BoolOp", "BinOp", "IfExp", "IsInstance"}:
                    obj = "(" + obj + ")"
                elif ": {" in obj:
                    obj = "(" + obj + ")"
                if runtime_symbol == "ArgumentParser.add_argument":
                    filled = ["\"\"", "\"\"", "\"\"", "\"\"", "\"\"", "\"\"", "pytra.empty_list()", "pytra.union_new_none()"]
                    i = 0
                    while i < len(arg_strs) and i < 4:
                        filled[i] = arg_strs[i]
                        i += 1
                    keywords_any = node.get("keywords")
                    keywords = keywords_any if isinstance(keywords_any, list) else []
                    for kw in keywords:
                        if not isinstance(kw, dict):
                            continue
                        kw_arg = kw.get("arg")
                        kw_val = kw.get("value")
                        if not isinstance(kw_arg, str) or not isinstance(kw_val, dict):
                            continue
                        rendered_kw = self._render_expr(kw_val)
                        if kw_arg == "help":
                            filled[4] = rendered_kw
                        elif kw_arg == "action":
                            filled[5] = rendered_kw
                        elif kw_arg == "choices":
                            filled[6] = rendered_kw
                        elif kw_arg == "default":
                            filled[7] = "pytra.union_wrap(" + rendered_kw + ")"
                    return obj + ".add_argument(" + ", ".join(filled) + ")"
                obj_type = self._lookup_expr_type(obj_node_for_attr)
                if obj_type in self._class_method_defaults and attr in self._class_method_defaults[obj_type]:
                    defaults = self._class_method_defaults[obj_type].get(attr, [])
                    default_types = self._class_method_default_types.get(obj_type, {}).get(attr, [])
                    filled_args = list(arg_strs)
                    i = len(filled_args)
                    while i < len(defaults):
                        default_node = defaults[i]
                        expected_type = default_types[i] if i < len(default_types) else ""
                        default_expr = self._render_default_arg_value(default_node, expected_type)
                        if default_expr == "":
                            i += 1
                            continue
                        filled_args.append(default_expr)
                        i += 1
                    arg_strs = filled_args
                # math.* → サブモジュール内は math_native.*、メインモジュールはそのまま
                if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") == "Name" and str(obj_node_for_attr.get("id")) == 'math':
                    if attr in {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "log2", "log10", "sqrt", "fabs", "floor", "ceil", "round", "fmod", "hypot", "atan2", "pow", "log_"}:
                        zig_attr = attr if attr != "log_" else "log"
                        # math 関数は f64 引数を期待 — int 引数を自動変換
                        _INT_TYPES_M = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                        coerced_args: list[str] = []
                        j = 0
                        while j < len(args):
                            a_type = self._lookup_expr_type(args[j]) if j < len(args) else ""
                            if a_type == "":
                                a_type = self._get_expr_type(args[j]) if isinstance(args[j], dict) else ""
                            raw_expr_type = self._get_expr_type(args[j]) if j < len(args) and isinstance(args[j], dict) else ""
                            if attr == "sqrt" and j < len(args) and (
                                raw_expr_type in _INT_TYPES_M
                                or (not self._expr_is_float_like(args[j]) if isinstance(args[j], dict) else False)
                                or (arg_strs[j].startswith("@as(f64, ") and "@floatFromInt(" not in arg_strs[j])
                            ):
                                raw_arg = arg_strs[j]
                                if raw_arg.startswith("@as(f64, ") and raw_arg.endswith(")"):
                                    raw_arg = raw_arg[len("@as(f64, "):-1]
                                coerced_args.append("@as(f64, @floatFromInt(" + raw_arg + "))")
                            elif a_type in _INT_TYPES_M:
                                coerced_args.append("@as(f64, @floatFromInt(" + arg_strs[j] + "))")
                            else:
                                coerced_args.append(arg_strs[j])
                            j += 1
                        if self.is_submodule:
                            return "math_native." + zig_attr + "(" + ", ".join(coerced_args) + ")"
                        return obj + "." + zig_attr + "(" + ", ".join(coerced_args) + ")"
                if attr == 'isdigit':
                    return "pytra.char_isdigit(" + obj + ")"
                if attr == 'isalpha':
                    return "pytra.char_isalpha(" + obj + ")"
                if attr == "isspace":
                    return "pytra.str_isspace(" + obj + ")"
                if attr == "splitext" and len(arg_strs) > 0:
                    renderer = self._make_stmt_renderer()
                    blk, tmp = renderer.next_splitext_names()
                    return renderer.render_simple_block_expr(
                        blk,
                        "const " + tmp + " = " + obj + ".splitext(" + arg_strs[0] + ");",
                        ".{ ._0 = " + tmp + "._0, ._1 = " + tmp + "._1 }",
                    )
                if attr == "makedirs" and len(arg_strs) > 0:
                    filled_args = list(arg_strs)
                    exist_ok_arg = ""
                    keywords_any = node.get("keywords")
                    keywords = keywords_any if isinstance(keywords_any, list) else []
                    for kw in keywords:
                        if not isinstance(kw, dict):
                            continue
                        if kw.get("arg") == "exist_ok" and isinstance(kw.get("value"), dict):
                            exist_ok_arg = self._render_expr(kw.get("value"))
                    if len(filled_args) == 1:
                        filled_args.append(exist_ok_arg if exist_ok_arg != "" else "false")
                    return obj + ".makedirs(" + ", ".join(filled_args) + ")"
                if attr == "upper":
                    return "pytra.str_upper(" + obj + ")"
                if attr == "lower":
                    return "pytra.str_lower(" + obj + ")"
                if attr == 'strip':
                    if len(arg_strs) > 0:
                        return "pytra.str_strip_chars(" + obj + ", " + arg_strs[0] + ")"
                    return "pytra.str_strip(" + obj + ")"
                if attr == 'lstrip':
                    if len(arg_strs) > 0:
                        return "pytra.str_lstrip_chars(" + obj + ", " + arg_strs[0] + ")"
                    return "pytra.str_lstrip(" + obj + ")"
                if attr == 'rstrip':
                    if len(arg_strs) > 0:
                        return "pytra.str_rstrip_chars(" + obj + ", " + arg_strs[0] + ")"
                    return "pytra.str_rstrip(" + obj + ")"
                if attr == 'startswith' and len(arg_strs) > 0:
                    return "pytra.str_startswith(" + obj + ", " + arg_strs[0] + ")"
                if attr == 'endswith' and len(arg_strs) > 0:
                    return "pytra.str_endswith(" + obj + ", " + arg_strs[0] + ")"
                if attr == "find" and len(arg_strs) > 0:
                    return "pytra.str_find(" + obj + ", " + arg_strs[0] + ")"
                if attr == "count" and len(arg_strs) > 0:
                    return "pytra.str_count(" + obj + ", " + arg_strs[0] + ")"
                if attr == "index" and len(arg_strs) > 0:
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type == "str":
                        renderer = self._make_stmt_renderer()
                        blk, val_name = renderer.next_str_index_names()
                        return renderer.render_guarded_block_expr(
                            blk,
                            "const "
                            + val_name
                            + ": i64 = pytra.str_index_of("
                            + obj
                            + ", "
                            + arg_strs[0]
                            + ");",
                            val_name + " < 0",
                            "\"ValueError\"",
                            "\"substring not found\"",
                            "0",
                            "@as(i64, 0)",
                            val_name,
                        )
                    if obj_type.startswith("list[") and obj_type.endswith("]"):
                        elem_type = self._zig_type(obj_type[5:-1].strip())
                        return "pytra.list_index(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                call_name = ""
                resolved_runtime_call = node.get("resolved_runtime_call")
                runtime_call = node.get("runtime_call")
                if isinstance(resolved_runtime_call, str) and resolved_runtime_call != "":
                    call_name = resolved_runtime_call
                elif isinstance(runtime_call, str):
                    call_name = runtime_call
                if call_name in {
                    "TextIOWrapper.__enter__",
                }:
                    return "pytra.file_enter(" + obj + ")"
                if call_name in {
                    "IOBase.__exit__",
                }:
                    coerced_args = [
                        "pytra.union_new_none()" if isinstance(arg, dict) and arg.get("kind") == "Constant" and arg.get("value") is None else arg_strs[i]
                        for i, arg in enumerate(args)
                    ]
                    return "pytra.file_exit(" + obj + ", " + ", ".join(coerced_args) + ")"
                if call_name == "str.rfind" and len(arg_strs) > 0:
                    return "pytra.str_rfind(" + obj + ", " + arg_strs[0] + ")"
                if attr == "replace" and len(arg_strs) >= 2:
                    return "pytra.str_replace(" + obj + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                if attr == 'isalnum':
                    return "pytra.str_isalnum(" + obj + ")"
                if attr == 'split':
                    if len(arg_strs) > 0:
                        return "pytra.str_split(" + obj + ", " + arg_strs[0] + ")"
                    return "pytra.str_split(" + obj + ", \" \")"
                if attr == "get":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(obj_type)
                        key_expr = arg_strs[0] if len(arg_strs) > 0 else "\"\""
                        if len(parts) == 2:
                            if self._normalize_type(parts[0].strip()) != "str" and len(arg_strs) > 0:
                                key_expr = "pytra.to_str(" + arg_strs[0] + ")"
                        if len(arg_strs) >= 2:
                            default_expr = arg_strs[1]
                            if self._is_union_storage_zig(val_zig):
                                default_expr = "pytra.union_wrap(" + default_expr + ")"
                            return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + key_expr + ", " + default_expr + ")"
                        if len(arg_strs) == 1:
                            default_expr = "pytra.union_new_none()" if self._is_union_storage_zig(val_zig) else self._zig_zero_value(val_zig)
                            return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + key_expr + ", " + default_expr + ")"
                if attr == 'clear':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        return "@constCast(&" + obj + ").clearRetainingCapacity()"
                    if obj_type.startswith("list["):
                        elem_type = self._zig_type(obj_type[5:-1].strip()) if obj_type.endswith("]") else "i64"
                        return "pytra.list_clear(" + obj + ", " + elem_type + ")"
                    if obj_type.startswith("set["):
                        elem_type = self._zig_type(obj_type[4:-1].strip()) if obj_type.endswith("]") else "i64"
                        return "pytra.list_clear(" + obj + ", " + elem_type + ")"
                if attr == "keys":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig = "i64"
                        if len(parts) == 2:
                            val_zig = self._zig_type(parts[1].strip())
                        return "pytra.dict_keys(" + val_zig + ", " + obj + ")"
                if attr == "values":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig = "i64"
                        if len(parts) == 2:
                            val_zig = self._zig_type(parts[1].strip())
                        return "pytra.dict_values(" + val_zig + ", " + obj + ")"
                if attr == 'append':
                    if len(arg_strs) > 0:
                        obj_type = self._lookup_expr_type(obj_node_for_attr)
                        elem_type = "i64"
                        if obj_type.startswith("list[") and obj_type.endswith("]"):
                            inner_raw = obj_type[5:-1].strip()
                            elem_type = self._zig_type(inner_raw)
                            # list[unknown] → 要素型は pytra.Obj (ネスト list 等)
                            if elem_type == "pytra.PyObject" and inner_raw in {"unknown", "Any", "object"}:
                                elem_type = "pytra.Obj"
                        elif obj_type in {"bytearray", "bytes"}:
                            elem_type = "u8"
                        else:
                            return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
                        if elem_type in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            return "pytra.list_append(" + obj + ", " + elem_type + ", @intCast(" + arg_strs[0] + "))"
                        if self._is_union_storage_zig(elem_type):
                            return "pytra.list_append(" + obj + ", " + elem_type + ", pytra.union_wrap(" + arg_strs[0] + "))"
                        arg_type = self._lookup_expr_type(args[0]) if len(args) > 0 and isinstance(args[0], dict) else ""
                        if elem_type.startswith("std.StringHashMap(") and self._is_union_storage_zig(self._zig_type(arg_type)):
                            value_type = elem_type[len("std.StringHashMap("):-1]
                            return "pytra.list_append(" + obj + ", " + elem_type + ", pytra.as_dict_typed(" + value_type + ", " + arg_strs[0] + "))"
                        return "pytra.list_append(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == "add":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("set[") and len(arg_strs) > 0:
                        elem_type = self._zig_type(obj_type[4:-1].strip()) if obj_type.endswith("]") else "i64"
                        if elem_type in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            return "pytra.set_add(" + obj + ", " + elem_type + ", @intCast(" + arg_strs[0] + "))"
                        return "pytra.set_add(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == "update":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("set[") and len(arg_strs) > 0:
                        elem_type = self._zig_type(obj_type[4:-1].strip()) if obj_type.endswith("]") else "i64"
                        return "pytra.set_update(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == 'discard':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("set[") and len(arg_strs) > 0:
                        elem_type = self._zig_type(obj_type[4:-1].strip()) if obj_type.endswith("]") else "i64"
                        if elem_type in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            return "pytra.set_discard(" + obj + ", " + elem_type + ", @intCast(" + arg_strs[0] + "))"
                        return "pytra.set_discard(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == 'remove':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("set[") and len(arg_strs) > 0:
                        elem_type = self._zig_type(obj_type[4:-1].strip()) if obj_type.endswith("]") else "i64"
                        if elem_type in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            return "pytra.set_remove(" + obj + ", " + elem_type + ", @intCast(" + arg_strs[0] + "))"
                        return "pytra.set_remove(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == 'sort':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type == "list[int]" or obj_type == "list[int64]":
                        return "pytra.list_sort_i64(" + obj + ")"
                if attr == 'reverse':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("list["):
                        elem_type = self._zig_type(obj_type[5:-1].strip()) if obj_type.endswith("]") else "i64"
                        return "pytra.list_reverse(" + obj + ", " + elem_type + ")"
                if attr == "clear":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("list[") and obj_type.endswith("]"):
                        return "pytra.list_clear(" + obj + ", " + self._zig_type(obj_type[5:-1].strip()) + ")"
                    if obj_type in {"bytearray", "bytes"}:
                        return "pytra.list_clear(" + obj + ", u8)"
                if attr == 'join':
                    # Only str.join → str_join_sep; module.join passes through
                    owner_type = self._lookup_expr_type(obj_node_for_attr) if isinstance(obj_node_for_attr, dict) else ""
                    if owner_type == "str":
                        if len(arg_strs) > 0:
                            arg_type = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                            if arg_type.startswith("list["):
                                return "pytra.str_join_sep(" + obj + ", pytra.list_items(" + arg_strs[0] + ", []const u8))"
                            return "pytra.str_join_sep(" + obj + ", " + arg_strs[0] + ")"
                        return "pytra.str_join_sep(" + obj + ", &.{})"
                if attr == 'pop':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    elem_type = "i64"
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig = "i64"
                        key_expr = arg_strs[0] if len(arg_strs) > 0 else "\"\""
                        if len(parts) == 2:
                            val_zig = self._zig_type(parts[1].strip())
                            if self._normalize_type(parts[0].strip()) != "str" and len(arg_strs) > 0:
                                key_expr = "pytra.to_str(" + arg_strs[0] + ")"
                        default_expr = "0"
                        if len(arg_strs) > 1:
                            default_expr = arg_strs[1]
                        return "pytra.dict_pop(" + val_zig + ", @constCast(&" + obj + "), " + key_expr + ", " + default_expr + ")"
                    if obj_type.startswith("list[") and obj_type.endswith("]"):
                        elem_type = self._zig_type(obj_type[5:-1].strip())
                    elif obj_type in {"bytearray", "bytes"}:
                        elem_type = "u8"
                    else:
                        return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
                    return "pytra.list_pop(" + obj + ", " + elem_type + ")"
                if attr == 'setdefault':
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig = "i64"
                        key_expr = arg_strs[0] if len(arg_strs) > 0 else "\"\""
                        default_expr = arg_strs[1] if len(arg_strs) > 1 else "0"
                        if len(parts) == 2:
                            val_zig = self._zig_type(parts[1].strip())
                            if self._normalize_type(parts[0].strip()) != "str" and len(arg_strs) > 0:
                                key_expr = "pytra.to_str(" + arg_strs[0] + ")"
                        return "pytra.dict_setdefault(" + val_zig + ", @constCast(&" + obj + "), " + key_expr + ", " + default_expr + ")"
                if attr == 'extend':
                    if len(arg_strs) > 0:
                        obj_type = self._lookup_expr_type(obj_node_for_attr)
                        elem_type = "i64"
                        if obj_type.startswith("list[") and obj_type.endswith("]"):
                            elem_type = self._zig_type(obj_type[5:-1].strip())
                        elif obj_type in {"bytearray", "bytes"}:
                            elem_type = "u8"
                        else:
                            return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
                        return "pytra.list_extend(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == "write":
                    if len(arg_strs) > 0:
                        return "pytra.file_write(" + obj + ", " + arg_strs[0] + ")"
                if attr == "read":
                    return "pytra.file_read(" + obj + ")"
                if attr == "__exit__":
                    coerced_args = [
                        "pytra.union_new_none()" if isinstance(arg, dict) and arg.get("kind") == "Constant" and arg.get("value") is None else arg_strs[i]
                        for i, arg in enumerate(args)
                    ]
                    return obj + ".__exit__(" + ", ".join(coerced_args) + ")"
                if attr == "close":
                    return "pytra.file_close(" + obj + ")"
                if attr == "sqrt":
                    if len(arg_strs) > 0:
                        return "std.math.sqrt(@as(f64, " + arg_strs[0] + "))"
                    return "std.math.sqrt(@as(f64, " + obj + "))"
                # vtable ディスパッチ: obj の型がクラスかつ vtable あり
                # ただしメソッド内の self.method() は直接呼び出し
                obj_node = func_any.get("value")
                is_self_call = isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and obj_node.get("id") == "self"
                obj_type = self._lookup_expr_type(obj_node)
                if obj_type in self.class_names and self._has_vtable(obj_type) and not is_self_call:
                    root = self._get_vtable_root(obj_type)
                    vt_name = root + "VT"
                    return obj + ".vt(" + vt_name + ")." + attr + "(" + obj + ".data)"
                return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
        fn_expr = self._render_expr(func_any)
        fn_type = self._lookup_expr_type(func_any) if isinstance(func_any, dict) else ""
        call_arg_strs = self._coerce_call_args_for_signature(arg_strs, args, fn_type, func_any)
        if (isinstance(func_any, dict) and func_any.get("kind") == "Lambda") or self._is_callable_type(fn_type) or self._is_optional_callable_type(fn_type):
            return self._render_callable_invoke(fn_expr, call_arg_strs, fn_type)
        return fn_expr + "(" + ", ".join(call_arg_strs) + ")"

    def _render_callable_invoke(self, fn_expr: str, arg_strs: list[str], fn_type: str = "") -> str:
        name_renderer = self._make_stmt_renderer()
        blk_label, fn_local = name_renderer.next_callable_invoke_names()
        self._sync_from_stmt_renderer(name_renderer)
        call_args = ", ".join(arg_strs)
        if call_args == "":
            direct_call = fn_expr + "()"
            method_call = fn_expr + ".call()"
        else:
            direct_call = fn_expr + "(" + call_args + ")"
            method_call = fn_expr + ".call(" + call_args + ")"
        local_init = fn_expr
        if self._is_optional_callable_type(fn_type):
            local_init = fn_expr + " orelse unreachable"
        block_renderer = self._make_stmt_renderer()
        rendered = block_renderer.render_simple_block_expr(
            blk_label,
            "const " + fn_local + " = " + local_init + ";",
            "switch (@typeInfo(@TypeOf(" + fn_local + "))) { "
            + ".@\"struct\", .@\"union\", .@\"enum\", .@\"opaque\" => if (@hasDecl(@TypeOf(" + fn_local + "), \"call\")) "
            + method_call.replace(fn_expr, fn_local, 1)
            + " else "
            + direct_call.replace(fn_expr, fn_local, 1)
            + ", else => "
            + direct_call.replace(fn_expr, fn_local, 1)
            + ", }",
        )
        self._sync_from_stmt_renderer(block_renderer)
        return rendered

    def _coerce_call_args_for_signature(self, arg_strs: list[str], args: list[Any], fn_type: str, func_any: Any = None) -> list[str]:
        param_zig_types: list[str] = []
        func_name = ""
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            func_name = _safe_ident(func_any.get("id"), "fn_")
            param_zig_types = self._module_function_param_zig_types.get(func_name, [])
        if len(param_zig_types) == 0:
            sig = self._callable_signature_parts(fn_type)
            if sig is None or len(arg_strs) == 0:
                return arg_strs
            param_types, _ret_type = sig
            param_zig_types = [self._zig_type(p.strip()) for p in param_types]
        if len(arg_strs) == 0:
            return arg_strs
        out = list(arg_strs)
        vararg_index = self._module_function_vararg_index.get(func_name, -1)
        if vararg_index >= 0 and len(param_zig_types) > vararg_index and len(out) >= vararg_index:
            elem_zig = param_zig_types[vararg_index]
            if elem_zig.startswith("[]const "):
                elem_zig = elem_zig[len("[]const "):]
            out = out[:vararg_index] + ["&[_]" + elem_zig + "{ " + ", ".join(out[vararg_index:]) + " }"]
        i = 0
        while i < len(out) and i < len(param_zig_types) and i < len(args):
            expected_zig = param_zig_types[i]
            arg_type = self._lookup_expr_type(args[i]) if isinstance(args[i], dict) else ""
            arg_zig = self._zig_type(arg_type) if arg_type != "" else ""
            if self._is_union_storage_zig(expected_zig) and not self._is_union_storage_zig(arg_zig):
                out[i] = "pytra.union_wrap(" + out[i] + ")"
            i += 1
        return out

    def _render_default_arg_value(self, value: Any, expected_type: str = "") -> str:
        expected_zig = self._zig_type(expected_type) if expected_type != "" else ""
        if isinstance(value, dict):
            rendered = self._render_expr(value)
            if self._is_union_storage_zig(expected_zig):
                value_type = self._lookup_expr_type(value)
                value_zig = self._zig_type(value_type) if value_type != "" else ""
                if not self._is_union_storage_zig(value_zig):
                    return "pytra.union_wrap(" + rendered + ")"
            return rendered
        if value is None:
            if self._is_union_storage_zig(expected_zig):
                return "pytra.union_new_none()"
            if expected_zig.startswith("?"):
                return "null"
            return ""
        if isinstance(value, str):
            return value
        return ""

    def _coerce_value_to_zig_type(self, target_zig: str, value_node: Any, rendered: str) -> str:
        if target_zig == "" or not isinstance(value_node, dict):
            return rendered
        if target_zig == "bool":
            rendered = rendered.replace("@as(i64, false)", "false").replace("@as(i64, true)", "true")
        if target_zig.startswith("?") and value_node.get("kind") == "Constant" and value_node.get("value") is None:
            return "null"
        value_type = self._lookup_expr_type(value_node)
        if value_type == "":
            value_type = self._get_expr_type(value_node)
        value_zig = self._zig_type(value_type) if value_type != "" else ""
        if target_zig.startswith("?"):
            inner_target = target_zig[1:]
            if inner_target == "[]const u8" and value_zig == "anytype":
                return "pytra._jv_as_str_any(" + rendered + ")"
            if inner_target == "f64" and value_zig == "anytype":
                return "pytra._jv_as_float_any(" + rendered + ")"
        if value_zig.startswith("?") and value_zig[1:] == target_zig:
            if self._is_union_storage_zig(target_zig):
                return "(" + rendered + " orelse pytra.union_new_none())"
            return rendered + ".?"
        if value_type != "":
            stripped_value = self._strip_optional_type(value_type)
            if stripped_value != value_type and self._zig_type(stripped_value) == target_zig:
                if self._is_union_storage_zig(target_zig):
                    return "(" + rendered + " orelse pytra.union_new_none())"
                return rendered + ".?"
        if self._is_union_storage_zig(target_zig) and value_zig != "" and not self._is_union_storage_zig(value_zig):
            return "pytra.union_wrap(" + rendered + ")"
        if self._is_union_storage_zig(target_zig) and value_node.get("kind") == "Name":
            return "pytra.union_wrap(" + rendered + ")"
        if self._is_union_storage_zig(target_zig) and value_zig == "" and value_node.get("kind") in {"Call", "Dict", "List", "Constant", "Name"}:
            return "pytra.union_wrap(" + rendered + ")"
        return rendered

    def _fill_args_with_keywords(
        self,
        call_node: dict[str, Any],
        positional_args: list[str],
        param_order: list[str],
        defaults: list[Any],
        default_types: list[str],
    ) -> list[str]:
        if len(param_order) == 0:
            return positional_args
        filled = list(positional_args[: len(param_order)])
        while len(filled) < len(param_order):
            filled.append("")
        keywords_any = call_node.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        positions = {param_order[i]: i for i in range(len(param_order))}
        for kw in keywords:
            if not isinstance(kw, dict):
                continue
            kw_arg = kw.get("arg")
            kw_val = kw.get("value")
            if not isinstance(kw_arg, str) or not isinstance(kw_val, dict):
                continue
            idx = positions.get(kw_arg)
            if idx is None:
                continue
            filled[idx] = self._render_expr(kw_val)
        i = 0
        while i < len(filled):
            if filled[i] == "":
                default_node = defaults[i] if i < len(defaults) else None
                expected_type = default_types[i] if i < len(default_types) else ""
                default_expr = self._render_default_arg_value(default_node, expected_type)
                if default_expr != "":
                    filled[i] = default_expr
            i += 1
        while len(filled) > 0 and filled[-1] == "":
            filled.pop()
        return filled

    def _render_dict(self, node: dict[str, Any]) -> str:
        entries_any = node.get("entries")
        entries: list[dict[str, Any]] = []
        if isinstance(entries_any, list):
            for e in entries_any:
                if isinstance(e, dict):
                    entries.append(e)
        if len(entries) == 0:
            # 空 dict
            resolved = self._get_expr_type(node)
            if resolved.startswith("dict["):
                parts = self._split_generic(resolved[5:-1] if resolved.endswith("]") else "")
                if len(parts) == 2:
                    val_t = self._zig_type(parts[1].strip())
                    return "pytra.make_str_dict(" + val_t + ")"
            return "pytra.make_str_dict(i64)"
        val_parts: list[str] = []
        key_parts: list[str] = []
        for entry in entries:
            key_expr = self._render_expr(entry.get("key"))
            key_parts.append(key_expr)
            val_parts.append(self._render_expr(entry.get("value")))
        resolved = self._get_expr_type(node)
        val_zig = "i64"
        key_is_str = True
        if resolved.startswith("dict[") and resolved.endswith("]"):
            dparts = self._split_generic(resolved[5:-1])
            if len(dparts) == 2:
                val_zig = self._zig_type(dparts[1].strip())
                key_is_str = self._normalize_type(dparts[0].strip()) == "str"
        if self._is_union_storage_zig(val_zig):
            val_parts = ["pytra.union_wrap(" + vp + ")" for vp in val_parts]
        if not key_is_str:
            key_parts = ["pytra.to_str(" + kp + ")" for kp in key_parts]
        return "pytra.make_str_dict_from(" + val_zig + ", " + "&[_][]const u8{ " + ", ".join(key_parts) + " }, " + "&[_]" + val_zig + "{ " + ", ".join(val_parts) + " })"

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

    def _render_set_comp(self, node: dict[str, Any]) -> str:
        gens_any = node.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "pytra.empty_list()"
        gen = gens[0]
        target = gen.get("target")
        iter_node = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target, dict) or target.get("kind") not in {"Name", "Tuple"} or not isinstance(iter_node, dict):
            return "pytra.empty_list()"
        target_name = _safe_ident(target.get("id"), "item") if target.get("kind") == "Name" else self._make_stmt_renderer().next_tuple_target_name("__set_tuple")
        iter_expr, elem_type, unpack_lines, name_types = self._comp_iter_parts(iter_node, target_name, target)
        result_type = self._get_expr_type(node)
        if result_type.startswith("set[") and result_type.endswith("]"):
            elem_type = self._zig_type(result_type[4:-1].strip())
        loop_cond = "true"
        type_map = dict(self._current_type_map())
        if target.get("kind") == "Name":
            type_map[target_name] = result_type[4:-1].strip() if result_type.startswith("set[") and result_type.endswith("]") else self._lookup_expr_type(target)
        else:
            type_map.update(name_types)
        self._local_type_stack.append(type_map)
        if len(ifs) > 0:
            loop_cond = " and ".join(self._render_cond_expr(cond) for cond in ifs if isinstance(cond, dict))
        elt_expr = self._render_expr(node.get("elt"))
        self._local_type_stack.pop()
        blk, out_name = self._make_stmt_renderer().next_set_comp_names()
        parts: list[str] = []
        parts.append("const " + out_name + " = pytra.make_list(" + elem_type + ");")
        parts.append(" for (" + iter_expr + ") |" + target_name + "| {")
        for line in unpack_lines:
            parts.append("  " + line)
        if loop_cond != "true":
            parts.append("  if (" + loop_cond + ") {")
        parts.append("   if (!pytra.contains(" + out_name + ", " + elt_expr + ")) { pytra.list_append(" + out_name + ", " + elem_type + ", " + elt_expr + "); }")
        if loop_cond != "true":
            parts.append("  }")
        parts.append(" }")
        return self._make_stmt_renderer().render_simple_block_expr(blk, "".join(parts), out_name)

    def _render_list_comp(self, node: dict[str, Any]) -> str:
        gens_any = node.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "pytra.empty_list()"
        gen = gens[0]
        target = gen.get("target")
        iter_node = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target, dict) or target.get("kind") not in {"Name", "Tuple"} or not isinstance(iter_node, dict):
            return "pytra.empty_list()"
        target_name = _safe_ident(target.get("id"), "item") if target.get("kind") == "Name" else self._make_stmt_renderer().next_tuple_target_name("__list_tuple")
        iter_expr, iter_elem_type, unpack_lines, name_types = self._comp_iter_parts(iter_node, target_name, target)
        result_type = self._get_expr_type(node)
        result_elem_type = "i64"
        declared_elem_type = ""
        if result_type.startswith("list[") and result_type.endswith("]"):
            declared_elem_type = result_type[5:-1].strip()
            result_elem_type = self._zig_type(declared_elem_type)
        type_map = dict(self._current_type_map())
        if target.get("kind") == "Name":
            target_type = self._lookup_expr_type(target)
            iter_source_type = self._lookup_expr_type(iter_node)
            if (
                target_type in {"", "unknown", "object", "Any"}
                and iter_source_type.startswith("list[")
                and iter_source_type.endswith("]")
            ):
                target_type = iter_source_type[5:-1].strip()
            type_map[target_name] = target_type or declared_elem_type
        else:
            type_map.update(name_types)
        self._local_type_stack.append(type_map)
        loop_cond = "true"
        if len(ifs) > 0:
            loop_cond = " and ".join(self._render_cond_expr(cond) for cond in ifs if isinstance(cond, dict))
        elt_expr = self._render_expr(node.get("elt"))
        self._local_type_stack.pop()
        blk, out_name = self._make_stmt_renderer().next_list_comp_names()
        parts: list[str] = []
        parts.append("const " + out_name + " = pytra.make_list(" + result_elem_type + ");")
        parts.append(" for (" + iter_expr + ") |" + target_name + "| {")
        for line in unpack_lines:
            parts.append("  " + line)
        if loop_cond != "true":
            parts.append("  if (" + loop_cond + ") {")
        parts.append("   pytra.list_append(" + out_name + ", " + result_elem_type + ", " + elt_expr + ");")
        if loop_cond != "true":
            parts.append("  }")
        parts.append(" }")
        return self._make_stmt_renderer().render_simple_block_expr(blk, "".join(parts), out_name)

    def _comp_iter_parts(self, iter_node: dict[str, Any], capture_name: str, target: dict[str, Any]) -> tuple[str, str, list[str], dict[str, str]]:
        iter_expr = self._render_expr(iter_node)
        iter_type = self._lookup_expr_type(iter_node)
        iter_elem_type = "i64"
        if iter_type.startswith("list[") and iter_type.endswith("]"):
            iter_elem_type = self._zig_type(iter_type[5:-1].strip())
            iter_expr = "pytra.list_items(" + iter_expr + ", " + iter_elem_type + ")"
        elif iter_type == "str":
            iter_elem_type = "[]const u8"
            iter_expr = "pytra.list_items(pytra.str_chars(" + iter_expr + "), []const u8)"
        unpack_lines: list[str] = []
        name_types: dict[str, str] = {}
        if target.get("kind") == "Tuple":
            elements = target.get("elements")
            tuple_parts = self._split_generic(iter_type[11:-1]) if iter_type.startswith("list[tuple[") and iter_type.endswith("]]") else []
            if isinstance(elements, list):
                i = 0
                while i < len(elements):
                    elt = elements[i]
                    if isinstance(elt, dict) and elt.get("kind") == "Name":
                        elt_name = _safe_ident(elt.get("id"), "item")
                        unpack_lines.append("const " + elt_name + " = " + capture_name + "._" + str(i) + ";")
                        if i < len(tuple_parts):
                            name_types[elt_name] = tuple_parts[i].strip()
                    i += 1
        return iter_expr, iter_elem_type, unpack_lines, name_types

    def _render_dict_comp(self, node: dict[str, Any]) -> str:
        gens_any = node.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "pytra.make_str_dict(i64)"
        gen = gens[0]
        target = gen.get("target")
        iter_node = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target, dict) or target.get("kind") != "Name" or not isinstance(iter_node, dict):
            return "pytra.make_str_dict(i64)"
        target_name = _safe_ident(target.get("id"), "item")
        iter_expr = self._render_expr(iter_node)
        iter_type = self._lookup_expr_type(iter_node)
        iter_elem_type = "i64"
        if iter_type.startswith("list[") and iter_type.endswith("]"):
            iter_elem_type = self._zig_type(iter_type[5:-1].strip())
        resolved = self._get_expr_type(node)
        val_zig = "i64"
        key_is_str = True
        declared_key_type = "str"
        if resolved.startswith("dict[") and resolved.endswith("]"):
            dparts = self._split_generic(resolved[5:-1])
            if len(dparts) == 2:
                declared_key_type = self._normalize_type(dparts[0].strip())
                key_is_str = declared_key_type == "str"
                val_zig = self._zig_type(dparts[1].strip())
        type_map = dict(self._current_type_map())
        type_map[target_name] = declared_key_type if declared_key_type != "str" else self._lookup_expr_type(target)
        self._local_type_stack.append(type_map)
        loop_cond = "true"
        if len(ifs) > 0:
            loop_cond = " and ".join(self._render_cond_expr(cond) for cond in ifs if isinstance(cond, dict))
        key_expr = self._render_expr(node.get("key"))
        val_expr = self._render_expr(node.get("value"))
        self._local_type_stack.pop()
        if not key_is_str:
            key_expr = "pytra.to_str(" + key_expr + ")"
        blk = self._make_stmt_renderer().next_dict_comp_name()
        parts: list[str] = []
        parts.append("var __dc = pytra.make_str_dict(" + val_zig + ");")
        parts.append(" for (pytra.list_items(" + iter_expr + ", " + iter_elem_type + ")) |" + target_name + "| {")
        if loop_cond != "true":
            parts.append("  if (" + loop_cond + ") {")
        parts.append("   __dc.put(" + key_expr + ", " + val_expr + ") catch {};")
        if loop_cond != "true":
            parts.append("  }")
        parts.append(" }")
        return self._make_stmt_renderer().render_simple_block_expr(blk, "".join(parts), "__dc")

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
        if s == "callable":
            return "callable"
        alias_target = self._type_aliases.get(s, "")
        if alias_target != "" and alias_target != s:
            return self._normalize_type(alias_target)
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
        union_parts = self._split_top_level_union(s)
        if len(union_parts) > 1:
            parts = [self._normalize_type(p.strip()) for p in union_parts]
            return "|".join(parts)
        return s

    def _strip_optional_type(self, t: str) -> str:
        norm = self._normalize_type(t)
        parts = self._split_top_level_union(norm)
        if len(parts) <= 1:
            return ""
        parts = [p.strip() for p in parts]
        non_none = [p for p in parts if p != "None"]
        has_none = len(non_none) < len(parts)
        if has_none and len(non_none) == 1:
            return non_none[0]
        return ""

    def _callable_signature_parts(self, t: str) -> tuple[list[str], str] | None:
        norm = self._normalize_type(t)
        if norm.startswith("callable[") or norm.startswith("Callable["):
            inner = norm[norm.find("[") + 1 : -1].strip()
        else:
            return None
        if not inner.startswith("["):
            return None
        depth = 0
        split_idx = -1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    split_idx = i
                    break
            i += 1
        if split_idx < 0:
            return None
        args_blob = inner[1:split_idx].strip()
        ret_blob = inner[split_idx + 1 :].strip()
        if ret_blob.startswith(","):
            ret_blob = ret_blob[1:].strip()
        args = self._split_generic(args_blob) if args_blob != "" else []
        return (args, ret_blob if ret_blob != "" else "None")

    def _zig_callable_type(self, t: str, *, optional: bool = False) -> str:
        sig = self._callable_signature_parts(t)
        if sig is None:
            return "anytype" if not optional else "?*const anyopaque"
        arg_types, ret_type = sig
        zig_args = [self._zig_type(arg_type.strip()) for arg_type in arg_types]
        zig_ret = self._zig_type(ret_type)
        fn_type = "*const fn (" + ", ".join(zig_args) + ") " + zig_ret
        return "?" + fn_type if optional else fn_type

    def _is_optional_callable_type(self, typ: str) -> bool:
        inner = self._strip_optional_type(typ)
        return inner != "" and self._is_callable_type(inner)

    def _type_expr_is_optional_callable(self, type_expr: Any) -> bool:
        if not isinstance(type_expr, dict):
            return False
        if type_expr.get("kind") != "OptionalType":
            return False
        inner = type_expr.get("inner")
        if not isinstance(inner, dict):
            return False
        if inner.get("kind") == "NamedType":
            return inner.get("name") in {"callable", "Callable"}
        return inner.get("kind") == "GenericType" and inner.get("base") in {"callable", "Callable"}

    def _merge_decl_type(self, existing_type: str, new_type: str, type_expr: Any = None) -> str:
        if self._is_optional_callable_type(existing_type):
            if self._is_callable_type(new_type) or self._type_expr_is_optional_callable(type_expr):
                return existing_type
        return new_type

    def _render_optional_dict_get(self, call_node: Any, decl_type: str) -> str:
        node = call_node
        while isinstance(node, dict) and node.get("kind") in {"Unbox", "Box"}:
            node = node.get("value")
        if not isinstance(node, dict) or node.get("kind") != "Call":
            return ""
        if self._strip_optional_type(decl_type) == "":
            return ""
        func = node.get("func")
        if not isinstance(func, dict) or func.get("kind") != "Attribute" or func.get("attr") != "get":
            return ""
        args = node.get("args")
        if not isinstance(args, list) or len(args) != 1:
            return ""
        owner = func.get("value")
        owner_type = self._lookup_expr_type(owner)
        if not owner_type.startswith("dict[") or not owner_type.endswith("]"):
            return ""
        parts = self._split_generic(owner_type[5:-1])
        if len(parts) != 2:
            return ""
        key_expr = self._render_expr(args[0])
        if self._normalize_type(parts[0].strip()) != "str":
            key_expr = "pytra.to_str(" + key_expr + ")"
        return (
            "pytra.dict_get_optional("
            + self._zig_type(parts[1].strip())
            + ", "
            + self._render_expr(owner)
            + ", "
            + key_expr
            + ")"
        )

    def _infer_value_zig_type(self, value_node: Any) -> str:
        node = value_node
        while isinstance(node, dict) and node.get("kind") in {"Unbox", "Box"}:
            node = node.get("value")
        if not isinstance(node, dict):
            return "pytra.PyObject"
        resolved = self._lookup_expr_type(node)
        zig_ty = self._zig_type(resolved) if resolved != "" else "pytra.PyObject"
        if zig_ty != "pytra.PyObject":
            return zig_ty
        kind = node.get("kind")
        if kind == "Call":
            func = node.get("func")
            if isinstance(func, dict) and func.get("kind") == "Name":
                fname = _safe_ident(func.get("id"), "")
                current = self._current_type_map().get(fname, "")
                sig = self._callable_signature_parts(current)
                if sig is not None:
                    return self._zig_type(self._normalize_type(sig[1]))
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                owner = func.get("value")
                owner_type = self._lookup_expr_type(owner)
                if owner_type.startswith("dict["):
                    val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(owner_type)
                    return val_zig
        if kind == "Subscript":
            owner_type = self._lookup_expr_type(node.get("value"))
            if owner_type.startswith("dict["):
                val_zig, _key_is_str, _stringify_values = self._dict_storage_spec(owner_type)
                return val_zig
        return "pytra.PyObject"

    def _preferred_value_zig_type(self, decl_type: str, value_node: Any) -> str:
        inferred = self._infer_value_zig_type(value_node)
        if inferred == "pytra.PyObject":
            return "pytra.PyObject"
        norm_decl = self._normalize_type(decl_type)
        if norm_decl == "" or "|" in norm_decl or norm_decl in {"Any", "object", "unknown"}:
            return inferred
        return inferred if self._zig_type(norm_decl) == "pytra.PyObject" else "pytra.PyObject"

    def _render_typed_empty_container(self, value_node: Any, decl_type: str) -> str:
        if not isinstance(value_node, dict):
            return ""
        norm_decl = self._normalize_type(decl_type)
        elem_type = ""
        if norm_decl.startswith("list[") and norm_decl.endswith("]"):
            elem_type = self._zig_type(norm_decl[5:-1].strip())
        elif norm_decl.startswith("set[") and norm_decl.endswith("]"):
            elem_type = self._zig_type(norm_decl[4:-1].strip())
        if elem_type == "":
            return ""
        kind = value_node.get("kind")
        if kind == "List":
            elements = value_node.get("elements")
            if not isinstance(elements, list) or len(elements) == 0:
                return "pytra.make_list(" + elem_type + ")"
        if kind == "Call":
            func = value_node.get("func")
            args = value_node.get("args")
            if isinstance(func, dict) and func.get("kind") == "Name" and isinstance(args, list) and len(args) == 0:
                if func.get("id") in {"list", "set"}:
                    return "pytra.make_list(" + elem_type + ")"
        return ""

    def _refine_unknown_decl_type(self, decl_type: str, value_node: Any) -> str:
        norm_decl = self._normalize_type(decl_type)
        inferred = self._lookup_expr_type(value_node)
        inferred_zig = self._zig_type(inferred) if inferred != "" else ""
        stripped_decl = self._strip_optional_type(norm_decl)
        if norm_decl in {"", "unknown"}:
            if inferred != "" and "unknown" not in inferred:
                return inferred
            return norm_decl
        if stripped_decl in {"Any", "object"} and inferred != "":
            return inferred
        if self._is_union_storage_zig(self._zig_type(norm_decl)) and inferred != "" and not self._is_union_storage_zig(inferred_zig):
            return inferred
        if "unknown" not in norm_decl:
            return norm_decl
        if inferred != "" and "unknown" not in inferred:
            return inferred
        node = value_node
        while isinstance(node, dict) and node.get("kind") in {"Box", "Unbox"}:
            node = node.get("value")
        inferred = self._lookup_expr_type(node)
        if inferred != "" and "unknown" not in inferred:
            return inferred
        return norm_decl

    def _runtime_decl_type(self, decl_type: str, value_node: Any) -> str:
        norm_decl = self._normalize_type(decl_type)
        value_type = self._normalize_type(self._lookup_expr_type(value_node))
        numeric_types = {
            "byte", "int8", "uint8", "int16", "uint16", "int32", "uint32",
            "int64", "uint64", "int", "float32", "float64", "float",
        }
        if norm_decl in numeric_types and value_type == "str":
            return value_type
        return norm_decl

    def _zig_zero_value(self, zig_type: str) -> str:
        if zig_type.startswith("?"):
            return "null"
        if zig_type == "bool":
            return "false"
        if zig_type in {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "usize", "isize", "f64", "f32"}:
            return "0"
        if zig_type == "[]const u8":
            return "\"\""
        if zig_type == "pytra.Obj":
            return "pytra.empty_list()"
        return "undefined"

    def _render_bounds_checked_index(self, obj: str, idx: str, len_expr: str, value_expr: str, result_zig_type: str) -> str:
        renderer = self._make_stmt_renderer()
        blk, len_name, real_name = renderer.next_bounds_checked_index_names()
        zero = self._zig_zero_value(result_zig_type)
        rendered = renderer.render_guarded_block_expr(
            blk,
            "const "
            + len_name
            + ": i64 = @intCast("
            + len_expr
            + "); const "
            + real_name
            + ": i64 = if ("
            + idx
            + " < 0) "
            + idx
            + " + "
            + len_name
            + " else "
            + idx
            + ";",
            real_name + " < 0 or " + real_name + " >= " + len_name,
            "\"IndexError\"",
            "\"index out of range\"",
            "0",
            zero,
            value_expr,
        )
        self._sync_from_stmt_renderer(renderer)
        return rendered

    def _dict_storage_spec(self, dict_type: str) -> tuple[str, bool, bool]:
        val_zig = "i64"
        key_is_str = True
        stringify_values = False
        norm = self._normalize_type(dict_type)
        if norm.startswith("dict[") and norm.endswith("]"):
            dparts = self._split_generic(norm[5:-1])
            if len(dparts) == 2:
                key_is_str = self._normalize_type(dparts[0].strip()) == "str"
                value_type = dparts[1].strip()
                union_parts = self._split_top_level_union(value_type)
                non_none = [p.strip() for p in union_parts if p.strip() != "None"]
                has_none = len(non_none) < len(union_parts)
                if self._normalize_type(value_type) in {"Any", "object"}:
                    val_zig = self._union_storage_zig()
                elif len(union_parts) > 1 and not (has_none and len(non_none) == 1):
                    val_zig = self._union_storage_zig()
                else:
                    val_zig = self._zig_type(value_type)
        return (val_zig, key_is_str, stringify_values)

    def _render_dict_with_decl_type(self, node: dict[str, Any], decl_type: str) -> str:
        entries_any = node.get("entries")
        entries: list[dict[str, Any]] = []
        if isinstance(entries_any, list):
            for e in entries_any:
                if isinstance(e, dict):
                    entries.append(e)
        val_zig, key_is_str, stringify_values = self._dict_storage_spec(decl_type)
        if len(entries) == 0:
            return "pytra.make_str_dict(" + val_zig + ")"
        key_parts: list[str] = []
        val_parts: list[str] = []
        for entry in entries:
            key_expr = self._render_expr(entry.get("key"))
            if not key_is_str:
                key_expr = "pytra.to_str(" + key_expr + ")"
            key_parts.append(key_expr)
            value_expr = self._render_expr(entry.get("value"))
            if stringify_values:
                value_expr = "pytra.to_str(" + value_expr + ")"
            elif self._is_union_storage_zig(val_zig):
                value_expr = "pytra.union_wrap(" + value_expr + ")"
            val_parts.append(value_expr)
        return "pytra.make_str_dict_from(" + val_zig + ", " + "&[_][]const u8{ " + ", ".join(key_parts) + " }, " + "&[_]" + val_zig + "{ " + ", ".join(val_parts) + " })"

    def _render_union_dict_literal(self, node: dict[str, Any]) -> str:
        entries_any = node.get("entries")
        entries: list[dict[str, Any]] = []
        if isinstance(entries_any, list):
            for e in entries_any:
                if isinstance(e, dict):
                    entries.append(e)
        if len(entries) == 0:
            return "pytra.make_str_dict(" + self._union_storage_zig() + ")"
        key_parts: list[str] = []
        val_parts: list[str] = []
        for entry in entries:
            key_parts.append(self._render_expr(entry.get("key")))
            val_parts.append("pytra.union_wrap(" + self._render_expr(entry.get("value")) + ")")
        return "pytra.make_str_dict_from(" + self._union_storage_zig() + ", " + "&[_][]const u8{ " + ", ".join(key_parts) + " }, " + "&[_]" + self._union_storage_zig() + "{ " + ", ".join(val_parts) + " })"

    def _render_list_with_decl_type(self, node: dict[str, Any], decl_type: str) -> str:
        inner = decl_type[5:-1].strip() if decl_type.startswith("list[") and decl_type.endswith("]") else ""
        zig_elem = self._zig_type(inner) if inner != "" else "i64"
        elts_any = node.get("elts")
        if not isinstance(elts_any, list):
            elts_any = node.get("elements")
        elts = elts_any if isinstance(elts_any, list) else []
        items = [self._render_expr(e) for e in elts]
        if self._is_union_storage_zig(zig_elem):
            items = ["pytra.union_wrap(" + item + ")" for item in items]
        return "pytra.list_from(" + zig_elem + ", &[_]" + zig_elem + "{ " + ", ".join(items) + " })"

    def _unwrap_box_unbox(self, node: Any) -> Any:
        cur = node
        while isinstance(cur, dict) and cur.get("kind") in {"Box", "Unbox"}:
            cur = cur.get("value")
        return cur

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

    def _split_top_level_union(self, text: str) -> list[str]:
        parts: list[str] = []
        depth = 0
        current: list[str] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "[":
                depth += 1
                current.append(ch)
            elif ch == "]":
                depth -= 1
                current.append(ch)
            elif ch == "|" and depth == 0:
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
            return "pytra.PyObject"
        if t in {"Any", "object"}:
            return self._union_storage_zig()
        if t == "unknown":
            return "pytra.Obj"
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
        if t == "JsonVal":
            return self._union_storage_zig()
        if t == "bytes" or t == "bytearray":
            return "pytra.Obj"
        if t == "None":
            return "void"
        if self._is_callable_type(t):
            return self._zig_callable_type(t)
        # --- Union / Optional ---
        union_parts = self._split_top_level_union(t)
        if len(union_parts) > 1:
            parts = [p.strip() for p in union_parts]
            non_none = [p for p in parts if p != "None"]
            has_none = len(non_none) < len(parts)
            if has_none and len(non_none) == 1:
                if self._is_callable_type(non_none[0]):
                    return self._zig_callable_type(non_none[0], optional=True)
                return "?" + self._zig_type(non_none[0])
            if len(non_none) == 1:
                return self._zig_type(non_none[0])
            return self._union_storage_zig()
        # --- コンテナ型 ---
        if t.startswith("list[") and t.endswith("]"):
            return "pytra.Obj"
        if t.startswith("set[") and t.endswith("]"):
            return "pytra.Obj"
        if t.startswith("dict[") and t.endswith("]"):
            val_t, key_is_str, _stringify_values = self._dict_storage_spec(t)
            if key_is_str:
                return "std.StringHashMap(" + val_t + ")"
            return "std.StringHashMap(pytra.PyObject)"
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self._split_generic(t[6:-1])
            if len(parts) == 2 and parts[1].strip() == "...":
                return "pytra.Obj"
            return self._zig_tuple_type(t)
        # --- クラス名 ---
        if t in self.class_names:
            if self._is_subclass_of(t, "IntEnum") or self._is_subclass_of(t, "IntFlag"):
                return "i64"
            if self._has_vtable(t):
                return "pytra.Obj"
            return "*" + t
        # Imported class: known via import_alias_map → *ClassName
        if hasattr(self, "_import_alias_map") and t in self._import_alias_map:
            return "*" + t
        if t in self._known_imported_nominals:
            return "*" + t
        if t.replace("_", "").isalnum():
            return self._union_storage_zig()
        return "pytra.PyObject"

    def _get_expr_type(self, expr_any: Any) -> str:
        """EAST3 式ノードの resolved_type を正規化して返す。"""
        if not isinstance(expr_any, dict):
            return ""
        resolved = expr_any.get("resolved_type")
        if isinstance(resolved, str) and resolved.strip() != "" and resolved.strip() != "unknown":
            return self._normalize_type(resolved.strip())
        return ""

    def _infer_decl_type(self, stmt: dict[str, Any]) -> str:
        """変数宣言ノードから型を推論する（decl_type → annotation → value の resolved_type）。"""
        decl_type_any = stmt.get("decl_type")
        if isinstance(decl_type_any, str) and decl_type_any.strip() not in {"", "unknown"}:
            return self._normalize_type(decl_type_any.strip())
        anno_any = stmt.get("annotation")
        if isinstance(anno_any, str) and anno_any.strip() not in {"", "unknown"}:
            return self._normalize_type(anno_any.strip())
        value_any = stmt.get("value")
        if isinstance(value_any, dict):
            inferred = self._lookup_expr_type(value_any)
            if inferred != "" and inferred != "unknown":
                return inferred
            return self._get_expr_type(value_any)
        return ""

    def _lookup_expr_type(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Name":
            name = _safe_ident(ed.get("id"), "value")
            current = self._current_type_map().get(name, "")
            module_fn = self._module_function_types.get(name, "")
            resolved = self._get_expr_type(ed)
            if self._is_optional_callable_type(current):
                return current
            if current != "" and "unknown" not in current:
                return current
            if module_fn != "":
                return module_fn
            if current != "" and resolved in {"", "unknown"}:
                return current
            if resolved != "":
                return resolved
            return current
        resolved = self._get_expr_type(ed)
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
        if kind == "Tuple":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            if len(elts) > 0:
                parts: list[str] = []
                for elt in elts:
                    elt_t = self._lookup_expr_type(elt)
                    parts.append(elt_t if elt_t != "" else "object")
                return "tuple[" + ", ".join(parts) + "]"
        # math.* 呼び出しは float64 を返す
        if kind == "Call":
            func = ed.get("func")
            if isinstance(func, dict) and func.get("kind") == "Name":
                fname = _safe_ident(func.get("id"), "")
                current = self._current_type_map().get(fname, "")
                sig = self._callable_signature_parts(current)
                if sig is not None:
                    return self._normalize_type(sig[1])
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                obj_node = func.get("value")
                if isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and str(obj_node.get("id")) == 'json':
                    attr = str(func.get("attr"))
                    if attr == "loads":
                        return "JsonValue"
                    if attr == "loads_arr":
                        return "JsonArr|None"
                    if attr == "loads_obj":
                        return "JsonObj|None"
                    if attr in {"dumps", "dumps_jv"}:
                        return "str"
                obj_type = self._lookup_expr_type(obj_node) if isinstance(obj_node, dict) else ""
                attr = str(func.get("attr"))
                if obj_type in self._class_return_types:
                    method_ret = self._class_return_types.get(obj_type, {}).get(attr, "")
                    if method_ret != "":
                        return self._normalize_type(method_ret)
                if isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and str(obj_node.get("id")) == 'math':
                    attr = str(func.get("attr"))
                    if attr in {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "log2", "log10", "sqrt", "fabs", "floor", "ceil", "round", "fmod", "hypot", "atan2", "pow"}:
                        return "float64"
        if kind == "Subscript":
            owner_type = self._lookup_expr_type(ed.get("value"))
            if owner_type.startswith("tuple[") and owner_type.endswith("]"):
                parts = self._split_generic(owner_type[6:-1])
                idx_node = ed.get("slice")
                if isinstance(idx_node, dict) and idx_node.get("kind") == "Constant" and isinstance(idx_node.get("value"), int):
                    idx = int(idx_node.get("value"))
                    if 0 <= idx < len(parts):
                        return self._normalize_type(parts[idx].strip())
            if owner_type.startswith("list[") and owner_type.endswith("]"):
                return self._normalize_type(owner_type[5:-1].strip())
            if owner_type.startswith("dict[") and owner_type.endswith("]"):
                parts = self._split_generic(owner_type[5:-1])
                if len(parts) == 2:
                    return self._normalize_type(parts[1].strip())
        # BinOp の型推論: float が含まれれば float64
        if kind == "BinOp":
            lt = self._lookup_expr_type(ed.get("left"))
            rt = self._lookup_expr_type(ed.get("right"))
            _FT = {"float64", "float32", "float"}
            _IT = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
            if lt in _FT or rt in _FT:
                return "float64"
            if lt in _IT and rt in _IT:
                return "int64"
        if resolved != "" and "unknown" not in resolved:
            return resolved
        return ""

    def _is_callable_type(self, typ: str) -> bool:
        t = self._normalize_type(typ)
        if t.find("|") != -1:
            return False
        return t in {"callable", "Callable"} or t.startswith("callable[") or t.startswith("Callable[")

    def _collect_lambda_captures(self, body_any: Any, arg_names: list[str]) -> list[str]:
        captures: list[str] = []
        current_types = self._current_type_map()
        for name in current_types:
            if name in arg_names:
                continue
            if self._node_uses_name(body_any, name):
                captures.append(name)
        return captures

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


class _ZigStmtCommonRenderer(CommonRenderer):
    def __init__(self, owner: "ZigNativeEmitter") -> None:
        self.owner = owner
        super().__init__("zig")

    def render_name(self, node: dict[str, Any]) -> str:
        return self.owner._render_expr(node)

    def render_constant(self, node: dict[str, Any]) -> str:
        if node.get("value") is None:
            return "pytra.union_new_none()"
        return self.owner._render_expr(node)

    def render_expr(self, node: Any) -> str:
        return self.owner._render_expr(node)

    def render_condition_expr(self, node: Any) -> str:
        return self.owner._render_expr(node)

    def _next_tmp(self, prefix: str) -> str:
        self.owner.tmp_seq += 1
        self._tmp_counter = self.owner.tmp_seq
        self.state.tmp_counter = self.owner.tmp_seq
        return prefix + "_" + str(self.owner.tmp_seq)

    def render_attribute(self, node: dict[str, Any]) -> str:
        return self.owner._render_expr(node)

    def render_call(self, node: dict[str, Any]) -> str:
        return self.owner._render_expr(node)

    def render_assign_stmt(self, node: dict[str, Any]) -> str:
        raise RuntimeError("zig common renderer assign string hook is not used directly")

    def render_raise_value(self, node: dict[str, Any]) -> str:
        raise RuntimeError("zig common renderer raise value hook is not used directly")

    def render_except_open(self, handler: dict[str, Any]) -> str:
        raise RuntimeError("zig common renderer except hook is not used directly")

    def emit_assign_stmt(self, node: dict[str, Any]) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_expr_stmt(self, node: dict[str, Any]) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_stmt_extension(self, node: dict[str, Any]) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_bare_raise_stmt(self, node: dict[str, Any]) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_raise_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_raise_call_stmt(
        self,
        node: dict[str, Any],
        call_node: dict[str, Any],
        func_name: str,
        args: list[Any],
    ) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_raise_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_raise_value_stmt(self, node: dict[str, Any], value: Any) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_raise_stmt(node)
        self.state.indent_level = self.owner.indent

    def emit_try_stmt(self, node: dict[str, Any]) -> None:
        body = self.owner._dict_list(node.get("body"))
        handlers_any = node.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        orelse = self.owner._dict_list(node.get("orelse"))
        finalbody = self.owner._dict_list(node.get("finalbody"))
        try_blk = self.next_try_block_name()
        self.emit_backend_line(self.render_try_body_open(try_blk))
        self.state.indent_level += 1
        self.owner._try_depth += 1
        self.owner._try_label_stack.append(try_blk)
        for sub in body:
            self.emit_stmt(sub)
            self.emit_try_body_post_stmt(sub, try_blk)
        self.owner._try_label_stack.pop()
        self.owner._try_depth -= 1
        self.state.indent_level -= 1
        self.emit_backend_line(self.render_try_body_close(try_blk))
        if len(handlers) > 0:
            handled = self.next_exception_dispatch_state_name()
            self.emit_exception_dispatch_handlers(self.active_exception_type_slot_name(), handled, handlers)
        if len(orelse) > 0:
            self.emit_backend_line(self.render_try_orelse_open())
            self.state.indent_level += 1
            self.emit_body(orelse)
            self.state.indent_level -= 1
            self.emit_backend_line(self.render_try_orelse_close())
        if len(finalbody) > 0:
            self.emit_body(finalbody)

    def emit_exception_handler(self, handler: dict[str, Any]) -> None:
        self.state.indent_level = self.owner.indent
        super().emit_exception_handler(handler)
        self.owner.indent = self.state.indent_level

    def emit_backend_line(self, text: str) -> None:
        self.owner.indent = self.state.indent_level
        self.owner._emit_line(text)
        self.state.indent_level = self.owner.indent

    def active_exception_slot_names(self) -> tuple[str, str, str]:
        self._require_exception_style("manual_exception_slot")
        return _ZIG_ACTIVE_EXCEPTION_SLOTS

    def caught_exception_slot_names(self) -> tuple[str, str, str]:
        self._require_exception_style("manual_exception_slot")
        return _ZIG_CAUGHT_EXCEPTION_SLOTS

    def bound_exception_record_type_name(self) -> str:
        self._require_exception_style("manual_exception_slot")
        return _ZIG_BOUND_EXCEPTION_RECORD

    def is_catch_all_exception_handler(self, handler: dict[str, Any]) -> bool:
        type_name = _safe_ident(self.exception_handler_type_name(handler), "")
        return type_name in self.owner._catch_all_exception_types

    def iter_exception_match_type_names(self, handler: dict[str, Any]) -> list[str]:
        type_name = _safe_ident(self.exception_handler_type_name(handler), "")
        if type_name == "":
            return []
        out: list[str] = [type_name]
        current = self.owner._class_base.get(type_name, "")
        while current != "":
            out.append(current)
            current = self.owner._class_base.get(current, "")
        return out

    def render_exception_match_condition(
        self,
        handler: dict[str, Any],
        caught_type_expr: str,
    ) -> str:
        if self.is_catch_all_exception_handler(handler):
            return "true"
        type_name = _safe_ident(self.exception_handler_type_name(handler), "")
        if type_name == "":
            return "true"
        return " or ".join(
            "std.mem.eql(u8, " + caught_type_expr + ".?, " + _zig_string(current) + ")"
            for current in self.iter_exception_match_type_names(handler)
        )

    def render_exception_dispatch_condition(self, caught_type_expr: str) -> str:
        return caught_type_expr + " != null"

    def render_exception_dispatch_state_init_stmt(self, handled_name: str) -> str:
        return "var " + handled_name + " = false;"

    def render_exception_handler_guard_condition(
        self,
        handler: dict[str, Any],
        handled_name: str,
        caught_type_expr: str,
    ) -> str:
        cond = self.render_exception_match_condition(handler, caught_type_expr)
        return "!" + handled_name + " and (" + cond + ")"

    def render_exception_handler_mark_handled_stmt(self, handled_name: str) -> str:
        return handled_name + " = true;"

    def render_try_body_post_stmt_stmt(self, stmt: dict[str, Any], try_label: str) -> str:
        self._require_exception_style("manual_exception_slot")
        if stmt.get("kind") in {"Return", "Raise", "Break", "Continue"}:
            return ""
        return "if (" + self.render_active_exception_check() + ") " + self.render_try_break(try_label)

    def render_labeled_block_open(self, block_label: str) -> str:
        return block_label + ": {"

    def render_labeled_block_close(self, block_label: str) -> str:
        del block_label
        return "}"

    def render_break_to_label(self, block_label: str) -> str:
        return "break :" + block_label + ";"

    def render_break_to_label_value(self, block_label: str, value_expr: str) -> str:
        return "break :" + block_label + " " + value_expr + ";"

    def render_raise_propagation_stmt(self, try_label: str, return_stmt: str) -> str:
        if try_label != "":
            return self.render_try_break(try_label)
        return return_stmt

    def emit_exception_handler_binding_prelude(self, handler: dict[str, Any]) -> None:
        current_indent = self.owner.indent
        hname = self.exception_handler_name(handler)
        if isinstance(hname, str) and hname != "":
            safe_hname = _safe_ident(hname, "err")
            handler_body = self.exception_handler_body(handler)
            if self.owner._body_uses_name_runtime(handler_body, safe_hname):
                _, caught_msg, caught_line = self.caught_exception_slot_names()
                self.owner._begin_exception_binding(
                    safe_hname,
                    self.render_bound_exception_value(caught_msg, caught_line),
                )
        self.owner.indent = current_indent

    def emit_exception_handler_binding_teardown(self, handler: dict[str, Any]) -> None:
        del handler
        self.owner._end_pending_exception_binding()

    def render_with_fallback_enter_stmt(self, target_name: str, target_type: str) -> str:
        del target_type
        return "_ = " + target_name + ".__enter__();"

    def render_with_fallback_exit_stmt(self, target_name: str, target_type: str) -> str:
        del target_type
        return (
            "_ = "
            + target_name
            + ".__exit__(pytra.union_new_none(), pytra.union_new_none(), pytra.union_new_none());"
        )

    def render_with_close_fallback_stmt(self, target_name: str, target_type: str) -> str:
        del target_type
        return "pytra.file_close(" + target_name + ");"

    def render_with_context_bind_stmt(
        self,
        target_name: str,
        source_name: str,
        source_type: str,
        declare: bool,
    ) -> str:
        del source_type
        prefix = "var " if declare else ""
        return prefix + target_name + " = " + source_name + ";"

    def build_with_enter_assign(
        self,
        node: dict[str, Any],
        enter_name: str,
        enter_type: str,
        value: Any,
        bind_ref: bool = False,
    ) -> dict[str, Any]:
        assign_node: dict[str, Any] = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": enter_name, "resolved_type": enter_type},
            "value": value,
            "declare": not (len(self.owner._local_var_stack) > 0 and enter_name in self.owner._current_local_vars()),
            "decl_type": enter_type,
        }
        if bind_ref:
            assign_node["bind_ref"] = True
        return assign_node

    def emit_with_enter_prelude(
        self,
        node: dict[str, Any],
        enter_name: str,
        enter_type: str,
    ) -> None:
        if enter_name == "" or len(self.owner._local_var_stack) == 0:
            return
        if enter_name in self.owner._current_local_vars():
            return
        self.owner.indent = self.state.indent_level
        if enter_type != "":
            self.owner._current_type_map()[enter_name] = enter_type
        self.owner._add_current_local_var(enter_name)
        self.owner._emit_line("var " + enter_name + ": " + self.owner._zig_type(enter_type) + " = undefined;")
        self.state.indent_level = self.owner.indent


def _new_zig_stmt_common_renderer(owner: ZigNativeEmitter) -> _ZigStmtCommonRenderer:
    return _ZigStmtCommonRenderer(owner)



def cls_name_init(cls_name: str, arg_strs: list[str]) -> str:
    return cls_name + ".init(" + ", ".join(arg_strs) + ")"


def transpile_to_zig_native(east_doc: dict[str, JsonVal], is_submodule: bool = False) -> str:
    """EAST3 ドキュメントを Zig native ソースへ変換する。"""
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Zig backend")
    return ZigNativeEmitter(east_doc, is_submodule=is_submodule).transpile()


def emit_zig_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a single EAST3 module to Zig source."""
    meta = east3_doc.get("meta")
    emit_ctx = meta.get("emit_context") if isinstance(meta, dict) else None
    is_entry = False
    if isinstance(emit_ctx, dict):
        is_entry = bool(emit_ctx.get("is_entry"))
    return transpile_to_zig_native(east3_doc, is_submodule=not is_entry)


__all__ = ["emit_zig_module", "transpile_to_zig_native"]

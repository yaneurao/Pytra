"""EAST3 → Rust source code emitter.

Go emitter を参考に CommonRenderer + override 構成で作成。
入力は linked EAST3 JSON (dict) のみ。toolchain/ への依存なし。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import re

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.rs.types import (
    rs_type,
    rs_zero_value,
    rs_signature_type,
    safe_rs_ident,
    set_mapping_types,
    _split_generic_args,
    union_prefers_pyany,
)
from toolchain.emit.common.code_emitter import (
    RuntimeMapping, load_runtime_mapping, resolve_runtime_call,
    should_skip_module, build_import_alias_map, build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.link.expand_defaults import expand_cross_module_defaults


# ---------------------------------------------------------------------------
# Emit context (mutable state for one module emission)
# ---------------------------------------------------------------------------

@dataclass
class RsEmitContext:
    """Per-module mutable state during Rust emission."""
    module_id: str = ""
    source_path: str = ""
    is_entry: bool = False
    package_mode: bool = False
    indent_level: int = 0
    lines: list[str] = field(default_factory=list)
    # Variable types in current scope
    var_types: dict[str, str] = field(default_factory=dict)
    storage_var_types: dict[str, str] = field(default_factory=dict)
    # Best-effort concrete Rust storage types inferred from emitted RHS.
    var_rust_types: dict[str, str] = field(default_factory=dict)
    # Ref/value storage hints for local variables inferred from linked EAST3.
    var_storage_hints: dict[str, str] = field(default_factory=dict)
    # Current function return type
    current_return_type: str = ""
    # Imported runtime symbols mapped to emitted helper names
    runtime_imports: dict[str, str] = field(default_factory=dict)
    # Runtime mapping (from mapping.json)
    mapping: RuntimeMapping = field(default_factory=RuntimeMapping)
    # Import alias → module_id map
    import_alias_modules: dict[str, str] = field(default_factory=dict)
    # Class info
    class_names: set[str] = field(default_factory=set)
    trait_names: set[str] = field(default_factory=set)
    class_bases: dict[str, str] = field(default_factory=dict)
    class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    class_static_methods: dict[str, set[str]] = field(default_factory=dict)
    class_instance_methods: dict[str, dict[str, dict[str, JsonVal]]] = field(default_factory=dict)
    enum_members: dict[str, list[str]] = field(default_factory=dict)
    enum_bases: dict[str, str] = field(default_factory=dict)
    function_signatures: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    # Current class context (for method emission)
    current_class: str = ""
    # Variables that have been declared in the current scope
    declared_vars: set[str] = field(default_factory=set)
    # Temp counter
    temp_counter: int = 0
    # Module-level private symbols
    module_private_symbols: set[str] = field(default_factory=set)
    # Use statements needed
    uses_needed: set[str] = field(default_factory=set)
    # Map from original_name → renamed name (for compiler-renamed functions)
    original_name_map: dict[str, str] = field(default_factory=dict)
    # Whether we are currently at module level (outside any function/class body)
    at_module_level: bool = True
    # Module-level static variables (lowercase name → uppercase static name)
    module_statics: dict[str, str] = field(default_factory=dict)
    # Module-level non-const values lowered as zero-arg factory functions.
    module_factories: dict[str, str] = field(default_factory=dict)
    # Class field default values: {class_name: {field_name: default_expr_or_None}}
    class_field_defaults: dict[str, dict[str, str | None]] = field(default_factory=dict)
    # Class vars (class-level attributes): {class_name: {field_name: type}}
    class_vars: dict[str, dict[str, str]] = field(default_factory=dict)
    class_var_statics: dict[str, dict[str, str]] = field(default_factory=dict)
    ref_classes: set[str] = field(default_factory=set)
    # Name of currently-being-defined nested closure (for self-recursive call detection)
    current_nested_fn: str = ""
    nested_capture_args: dict[str, list[str]] = field(default_factory=dict)
    # @property methods: {class_name: {method_name}}
    class_property_methods: dict[str, set[str]] = field(default_factory=dict)
    # Classes that are base classes of other classes (used as function parameter types via dyn trait)
    parent_class_names: set[str] = field(default_factory=set)
    # Dense type IDs from linked manifest type_id_resolved_v1: {fqcn → dense_tid}
    class_type_ids: dict[str, int] = field(default_factory=dict)
    # Type info table from linked manifest type_info_table_v1: {name → {id, entry, exit}}
    class_type_info_table: dict[str, dict[str, int]] = field(default_factory=dict)
    needs_runtime_type_ids: bool = False
    known_method_signatures: dict[str, dict[str, JsonVal]] = field(default_factory=dict)
    imported_symbol_storage_hints: dict[str, str] = field(default_factory=dict)
    imported_class_fields: dict[str, dict[str, str]] = field(default_factory=dict)
    imported_symbol_names: set[str] = field(default_factory=set)
    imported_symbol_modules: dict[str, str] = field(default_factory=dict)
    type_only_imported_symbols: set[str] = field(default_factory=set)
    # Name of variable holding the caught exception message inside a catch handler (for bare raise)
    catch_err_msg_var: str = ""
    # During constructor lowering, self.field accesses are redirected to mutable locals.
    constructor_field_locals: set[str] = field(default_factory=set)
    # Labeled block name used when lowering Python __init__ returns to Rust break.
    constructor_block_label: str = ""
    # Varargs lowered as raw Vec<T> instead of PyList<T> when T is not Clone.
    vec_vararg_names: set[str] = field(default_factory=set)


def _package_prelude_uses(include_type_ids: bool) -> list[str]:
    lines = [
        "use crate::py_runtime::*;",
        "use crate::pytra_built_in_error::RuntimeError;",
        "use crate::pytra_std_re::*;",
        "use crate::time_native::perf_counter;",
        "use std::cell::RefCell;",
        "use std::collections::{BTreeMap, HashMap, HashSet, VecDeque};",
        "use std::rc::Rc;",
    ]
    if include_type_ids:
        lines.append("use crate::pytra_built_in_type_id_table::*;")
    return lines


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

_PYTRA_ROOT = "pytra"
_STD_SEG = "std"
_UTILS_SEG = "utils"
_BUILT_IN_SEG = "built_in"
_TOOLCHAIN2_ROOT = "toolchain2"
def _str(node: JsonVal, key: str) -> str:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, str):
            return v
    return ""


def _list(node: JsonVal, key: str) -> list[JsonVal]:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, list):
            return v
    return []


def _dict(node: JsonVal, key: str) -> dict[str, JsonVal]:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, dict):
            return v
    return {}


def _json_get(node: JsonVal, key: str) -> JsonVal:
    if isinstance(node, dict):
        return node.get(key)
    return None


def _json_bool(node: JsonVal, key: str) -> bool:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, bool):
            return v
    return False


def _as_str(value: JsonVal) -> str:
    if isinstance(value, str):
        return value
    return ""


def _decorator_id_matches(dec: JsonVal, name: str) -> bool:
    dec_text = _as_str(dec)
    if dec_text != "":
        if dec_text == name:
            return True
        if dec_text == "@" + name:
            return True
        return False
    if isinstance(dec, dict):
        did = _str(dec, "id")
        if did == name:
            return True
        if did == "@" + name:
            return True
        return False
    return False


def _decorators_have_id(decorators: list[JsonVal], name: str) -> bool:
    for dec in decorators:
        if _decorator_id_matches(dec, name):
            return True
    return False


def _all_pass_stmts(body: list[JsonVal]) -> bool:
    for stmt in body:
        if not isinstance(stmt, dict) or _str(stmt, "kind") != "Pass":
            return False
    return True


def _all_constant_nodes(nodes: list[JsonVal]) -> bool:
    for item in nodes:
        if not isinstance(item, dict) or _str(item, "kind") != "Constant":
            return False
    return True


def _path_like_types_have(ctx: RsEmitContext, type_names: set[str]) -> bool:
    for type_name in type_names:
        if type_name != "" and _is_path_type_name(ctx, type_name):
            return True
    return False


def _union_parts_lower_to_pyany(parts: list[str]) -> bool:
    for part in parts:
        if part in ("None", "bool", "int64", "float64", "str"):
            continue
        if part.startswith("list[") or part.startswith("dict["):
            continue
        return False
    return True


def _starts_uppercase(text: str) -> bool:
    if text == "":
        return False
    first = text[0]
    return first.upper() == first and first.lower() != first


def _iter_import_runtime_ids(meta: dict[str, JsonVal], type_only_symbols: set[str] | None = None) -> list[tuple[str, str]]:
    """Collect (resolved_binding_kind, runtime_module_id) pairs from import bindings."""
    out: list[tuple[str, str]] = []
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return out
    skip_symbols: set[str] = set()
    if type_only_symbols is not None:
        skip_symbols = type_only_symbols
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        resolved_kind = _as_str(binding.get("resolved_binding_kind"))
        if resolved_kind == "":
            resolved_kind = _as_str(binding.get("binding_kind"))
        runtime_module_id = _as_str(binding.get("runtime_module_id"))
        module_id = _as_str(binding.get("module_id"))
        mod_id = runtime_module_id if runtime_module_id != "" else module_id
        local_name = _as_str(binding.get("local_name"))
        imported_name = _as_str(binding.get("imported_name"))
        export_name = _as_str(binding.get("export_name"))
        runtime_symbol = _as_str(binding.get("runtime_symbol"))
        runtime_symbol_kind = _as_str(binding.get("runtime_symbol_kind"))
        if (
            resolved_kind == "symbol"
            and (
                (local_name != "" and local_name in skip_symbols)
                or (imported_name != "" and imported_name in skip_symbols)
                or (export_name != "" and export_name in skip_symbols)
            )
        ):
            continue
        if (
            mod_id != ""
            and resolved_kind == "symbol"
            and runtime_symbol == "JsonVal"
            and runtime_symbol_kind == "type"
            and (
                local_name == "JsonVal"
                or imported_name == "JsonVal"
            )
        ):
            continue
        if (
            resolved_kind == ""
            or mod_id == ""
            or (resolved_kind + "::" + mod_id) in seen
        ):
            continue
        seen.add(resolved_kind + "::" + mod_id)
        out.append((resolved_kind, mod_id))
    return out


def _build_import_symbol_storage_hints(meta: dict[str, JsonVal]) -> dict[str, str]:
    out: dict[str, str] = {}
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return out
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if _as_str(binding.get("binding_kind")) != "symbol":
            continue
        local_name = _as_str(binding.get("local_name"))
        hint = _as_str(binding.get("resolved_storage_hint"))
        if local_name != "" and hint != "":
            out[local_name] = hint
    return out


def _build_import_class_fields(meta: dict[str, JsonVal]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return out
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if _as_str(binding.get("binding_kind")) != "symbol":
            continue
        local_name = _as_str(binding.get("local_name"))
        field_types = binding.get("resolved_field_types_v1")
        if local_name == "" or not isinstance(field_types, dict):
            continue
        typed_fields: dict[str, str] = {}
        for field_name, field_type in field_types.items():
            typed_field_name = _as_str(field_name)
            typed_field_type = _as_str(field_type)
            if typed_field_name != "" and typed_field_type != "":
                typed_fields[typed_field_name] = typed_field_type
        if len(typed_fields) > 0:
            out[local_name] = typed_fields
    return out


def _build_imported_symbol_names(meta: dict[str, JsonVal]) -> set[str]:
    out: set[str] = set()
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return out
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if _as_str(binding.get("binding_kind")) != "symbol":
            continue
        local_name = _as_str(binding.get("local_name"))
        if local_name != "":
            out.add(local_name)
    return out


def _build_imported_symbol_modules(meta: dict[str, JsonVal]) -> dict[str, str]:
    out: dict[str, str] = {}
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return out
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if _as_str(binding.get("binding_kind")) != "symbol":
            continue
        local_name = _as_str(binding.get("local_name"))
        module_id = _as_str(binding.get("runtime_module_id"))
        if module_id == "":
            module_id = _as_str(binding.get("module_id"))
        if local_name != "" and module_id != "":
            out[local_name] = module_id
    return out


def _collect_value_name_refs(nodes: list[JsonVal]) -> set[str]:
    refs: set[str] = set()

    def visit(node: JsonVal) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        kind = _str(node, "kind")
        if kind == "Name":
            name = _str(node, "id")
            if name != "":
                refs.add(name)
            return
        if kind == "NamedType":
            return
        for value in node.values():
            visit(value)

    visit(nodes)
    return refs


def _build_type_only_imported_symbols(
    meta: dict[str, JsonVal],
    body: list[JsonVal],
    main_guard: list[JsonVal],
) -> set[str]:
    imported = _build_imported_symbol_names(meta)
    if len(imported) == 0:
        empty: set[str] = set()
        return empty
    value_refs = _collect_value_name_refs(body)
    value_refs.update(_collect_value_name_refs(main_guard))
    out: set[str] = set()
    for name in imported:
        if name not in value_refs:
            out.add(name)
    return out


def _call_signature(node: dict[str, JsonVal], fallback: dict[str, JsonVal] | None = None) -> dict[str, JsonVal]:
    if fallback is not None and len(fallback) > 0:
        return fallback
    sig = _dict(node, "function_signature_v1")
    if len(sig) > 0:
        return sig
    empty: dict[str, JsonVal] = {}
    return empty


def _iter_linked_user_module_ids(meta: dict[str, JsonVal], current_module_id: str) -> list[str]:
    """Collect non-pytra linked user module ids needed by an entry module."""
    out: list[str] = []
    lp = _dict(meta, "linked_program_v1")
    deps = lp.get("user_module_dependencies_v1")
    if not isinstance(deps, list):
        return out
    seen: set[str] = set()
    for dep in deps:
        dep_text = _as_str(dep)
        if dep_text == "" or dep_text == current_module_id:
            continue
        if dep_text in seen:
            continue
        seen.add(dep_text)
        out.append(dep_text)
    return out


def _iter_linked_module_ids_transitive(meta: dict[str, JsonVal], current_module_id: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    lp = _dict(meta, "linked_program_v1")

    def add(mod_id: str) -> None:
        if mod_id == "" or mod_id == current_module_id or mod_id in seen:
            return
        if _is_pytra_module(mod_id):
            return
        seen.add(mod_id)
        out.append(mod_id)

    for dep in _iter_linked_user_module_ids(meta, current_module_id):
        add(dep)
    entries = lp.get("entry_modules")
    if isinstance(entries, list):
        for dep in entries:
            if (
                isinstance(dep, str)
                and (
                    dep.startswith("toolchain.emit.")
                    or dep in (
                        "toolchain.common.jv",
                        "toolchain.common.types",
                        "toolchain.compile.jv",
                        "toolchain.link.shared_types",
                        "toolchain.link.type_id",
                    )
                )
            ):
                add(dep)
    return out


def _bool(node: JsonVal, key: str) -> bool:
    if isinstance(node, dict):
        v = node.get(key)
        if isinstance(v, bool):
            return v
    return False


def _indent(ctx: RsEmitContext) -> str:
    return "    " * ctx.indent_level


def _emit(ctx: RsEmitContext, line: str) -> None:
    ctx.lines.append(_indent(ctx) + line)


def _emit_raw(ctx: RsEmitContext, line: str) -> None:
    ctx.lines.append(line)


def _emit_blank(ctx: RsEmitContext) -> None:
    ctx.lines.append("")


def _infer_emitted_rust_type(expr: str) -> str:
    if "unwrap_or(PyAny::None)" in expr:
        return "PyAny"
    if expr.startswith("Rc::new(RefCell::new("):
        inner = expr[len("Rc::new(RefCell::new("):]
        class_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)::new\(", inner)
        if class_match is not None:
            return "Rc<RefCell<" + class_match.group(1) + ">>"
    if expr.startswith("Box::new("):
        inner = expr[len("Box::new("):]
        class_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)::new\(", inner)
        if class_match is not None:
            return "Box<" + class_match.group(1) + ">"
    return ""


def _optional_inner_rs_type(rt: str) -> str:
    if rt.startswith("Option<") and rt.endswith(">"):
        return rt[len("Option<"):-1]
    return ""


def _optional_inner_resolved_type(type_name: str) -> str:
    if type_name.endswith(" | None"):
        return type_name[:-7].strip()
    if type_name.endswith("|None"):
        return type_name[:-5].strip()
    return ""


def _infer_node_rust_type(ctx: RsEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    kind = _str(node, "kind")
    if kind == "Name":
        name = _str(node, "id")
        if name != "":
            known = ctx.var_rust_types.get(name, "")
            if known != "":
                return known
            declared = ctx.var_types.get(name, "")
            if declared != "":
                declared_rs = _rs_type_for_context(ctx, declared)
                if declared_rs != "":
                    return declared_rs
    if kind == "Unbox":
        outer_rt = _str(node, "resolved_type")
        if outer_rt not in ("", "unknown", "Any", "object", "Obj", "JsonVal"):
            outer_rs = _rs_type_for_context(ctx, outer_rt)
            if outer_rs != "":
                return outer_rs
    if kind == "Attribute":
        obj_node = node.get("value")
        obj_type = _actual_type_in_context(ctx, obj_node)
        if obj_type == "":
            obj_type = _resolved_type_in_context(ctx, obj_node)
        if obj_type == "" and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
            name_rs = ctx.var_rust_types.get(_str(obj_node, "id"), "")
            if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>"):
                obj_type = name_rs[len("Rc<RefCell<"):-2]
            elif name_rs.startswith("Box<") and name_rs.endswith(">"):
                obj_type = name_rs[len("Box<"):-1]
        attr = _str(node, "attr")
        if obj_type in ctx.class_fields:
            field_type = ctx.class_fields.get(obj_type, {}).get(attr, "")
            if field_type != "":
                field_rt = _rs_type_for_context(ctx, field_type)
                if field_rt != "":
                    return field_rt
        if obj_type in ctx.imported_class_fields:
            field_type = ctx.imported_class_fields.get(obj_type, {}).get(attr, "")
            if field_type != "":
                field_rt = _rs_type_for_context(ctx, field_type)
                if field_rt != "":
                    return field_rt
    if kind == "Subscript":
        obj_node = node.get("value")
        obj_type = _actual_type_in_context(ctx, obj_node)
        if obj_type.startswith("dict[") and obj_type.endswith("]"):
            parts = _split_generic_args(obj_type[5:-1])
            if len(parts) == 2:
                return _rs_type_for_context(ctx, parts[1].strip())
        if obj_type.startswith("list[") and obj_type.endswith("]"):
            return _rs_type_for_context(ctx, obj_type[5:-1].strip())
    if kind == "Call":
        runtime_call = _str(node, "runtime_call")
        resolved_runtime_call = _str(node, "resolved_runtime_call")
        func_node = node.get("func")
        func_name = _str(func_node, "id") if isinstance(func_node, dict) else ""
        if func_name in ("list", "py_list") or runtime_call in ("list_ctor", "list") or resolved_runtime_call in ("list_ctor", "list"):
            rt = _str(node, "resolved_type")
            if rt.startswith("list["):
                return _rs_type_for_context(ctx, rt)
            return "PyList<PyAny>"
    if kind == "Call":
        func = node.get("func")
        if isinstance(func, dict) and _str(func, "kind") == "Attribute":
            method = _str(func, "attr")
            owner = func.get("value")
            if (
                method == "loads"
                and isinstance(owner, dict)
                and (
                    _str(owner, "runtime_module_id") == "pytra.std.json"
                    or ctx.import_alias_modules.get(_str(owner, "id"), "") == "pytra.std.json"
                )
            ):
                return "Rc<RefCell<JsonValue>>"
            if method == "joinpath":
                owner_rt = _actual_type_in_context(ctx, owner)
                if _is_path_type_name(ctx, owner_rt) or _is_path_rust_type(ctx, _infer_node_rust_type(ctx, owner)):
                    return "Box<PyPath>"
            if method in {"as_str", "as_int", "as_float", "as_bool", "as_obj", "as_arr"}:
                returns = {
                    "as_str": "Option<String>",
                    "as_int": "Option<i64>",
                    "as_float": "Option<f64>",
                    "as_bool": "Option<bool>",
                    "as_obj": "Option<Rc<RefCell<JsonObj>>>",
                    "as_arr": "Option<Rc<RefCell<JsonArr>>>",
                }
                return returns[method]
        sig = _dict(node, "function_signature_v1")
        if sig:
            ret_type = _str(sig, "return_type")
            if ret_type != "":
                ret_rt = _rs_type_for_context(ctx, ret_type)
                if _str(node, "resolved_storage_hint") == "ref" and ret_rt.startswith("Box<") and ret_rt.endswith(">"):
                    return "Rc<RefCell<" + ret_rt[len("Box<"):-1] + ">>"
                if ret_rt != "":
                    return ret_rt
    resolved_type = _str(node, "resolved_type")
    resolved_storage_hint = _str(node, "resolved_storage_hint")
    if resolved_type != "":
        base_rt = _rs_type_for_context(ctx, resolved_type)
        if kind == "Call" and resolved_storage_hint == "ref":
            if base_rt.startswith("Rc<RefCell<") and base_rt.endswith(">>"):
                return base_rt
            if base_rt.startswith("Box<") and base_rt.endswith(">"):
                inner = base_rt[len("Box<"):-1]
                return "Rc<RefCell<" + inner + ">>"
            if (
                base_rt != ""
                and not base_rt.startswith("PyList<")
                and not base_rt.startswith("HashMap<")
                and not base_rt.startswith("HashSet<")
                and not base_rt.startswith("BTreeMap<")
                and not base_rt.startswith("Vec<")
                and not base_rt.startswith("VecDeque<")
                and base_rt not in ("String", "bool", "i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64", "PyAny", "()")
            ):
                return "Rc<RefCell<" + base_rt + ">>"
        if base_rt != "":
            return base_rt
    return ""


def _next_temp(ctx: RsEmitContext, prefix: str) -> str:
    ctx.temp_counter += 1
    return "__" + prefix + "_" + str(ctx.temp_counter)


def _module_prefix(ctx: RsEmitContext) -> str:
    if ctx.module_id == "":
        return ""
    return safe_rs_ident(ctx.module_id.replace(".", "_"))


def _module_id_to_rs_mod_name(module_id: str) -> str:
    if module_id == "":
        return ""
    return safe_rs_ident(module_id.replace(".", "_"))


def _has_python_module_file(module_id: str) -> bool:
    if module_id == "":
        return False
    root = Path(__file__).resolve().parents[3]
    module_py = root
    for part in module_id.split("."):
        module_py = module_py / part
    module_py = module_py.with_suffix(".py")
    return module_py.exists()


def _is_transpiled_module(ctx: RsEmitContext, module_id: str) -> bool:
    if module_id == "" or module_id == ctx.module_id:
        return False
    if _is_pytra_module(module_id):
        return not should_skip_module(module_id, ctx.mapping)
    return True


def _is_package_crate_module(ctx: RsEmitContext, module_id: str) -> bool:
    if module_id == "" or module_id == ctx.module_id:
        return False
    if should_skip_module(module_id, ctx.mapping):
        return False
    if module_id == _PYTRA_ROOT:
        return False
    if module_id == _PYTRA_ROOT + "." + _STD_SEG:
        return False
    if module_id == _PYTRA_ROOT + "." + _BUILT_IN_SEG:
        return False
    if module_id == _TOOLCHAIN2_ROOT:
        return False
    if _is_pytra_module(module_id) or _is_toolchain2_module(module_id):
        return _has_python_module_file(module_id)
    return False


def _has_nested_python_module(module_id: str, child_name: str) -> bool:
    if module_id == "" or child_name == "":
        return False
    root = Path(__file__).resolve().parents[3]
    rel_parts = module_id.split(".")
    child_py = root
    for part in rel_parts:
        child_py = child_py / part
    child_py = child_py / (child_name + ".py")
    if child_py.exists():
        return True
    child_pkg = root
    for part in rel_parts:
        child_pkg = child_pkg / part
    child_pkg = child_pkg / child_name / "__init__.py"
    return child_pkg.exists()


def _normalize_binding_name(name: str) -> str:
    text = name.strip()
    while text != "" and text[0] in "([{":
        text = text[1:].lstrip()
    while text != "" and text[-1] in ")]},":
        text = text[:-1].rstrip()
    return text


def _rs_symbol_name(ctx: RsEmitContext, name: str) -> str:
    """Resolve a module-level symbol name (add prefix for private module symbols)."""
    # Resolve original_name → renamed name (for compiler-renamed functions)
    resolved = ctx.original_name_map.get(name, name)
    if ctx.is_entry and resolved == "main":
        resolved = "pytra_case_main"
    if resolved.startswith("_") and resolved in ctx.module_private_symbols and ctx.module_id != "":
        prefix = _module_prefix(ctx)
        if prefix != "":
            return prefix + "__" + resolved[1:]
    return safe_rs_ident(resolved)


def _rs_var_name(ctx: RsEmitContext, name: str) -> str:
    """Resolve a local variable name."""
    return safe_rs_ident(name)


def _rs_constructor_field_name(name: str) -> str:
    return "__field_" + safe_rs_ident(name)


def _rs_is_copy_type(rt: str) -> bool:
    return rt in {"bool", "i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "usize", "isize", "f32", "f64", "()"}


def _class_var_static_name(ctx: RsEmitContext, class_name: str, attr: str) -> str:
    return ctx.class_var_statics.get(class_name, {}).get(attr, safe_rs_ident(class_name).upper() + "_" + safe_rs_ident(attr).upper())


def _rs_type_for_context(ctx: RsEmitContext, resolved_type: str) -> str:
    """Get Rust type, considering class/trait names in context."""
    if resolved_type == "" or resolved_type == "unknown":
        return "Box<dyn std::any::Any>"
    if resolved_type == "CommonRendererState":
        return "Rc<RefCell<CommonRendererState>>"
    if resolved_type == "RuntimeMapping":
        return "Rc<RefCell<RuntimeMapping>>"
    if resolved_type in ("JsonObj", "JsonArr", "JsonValue"):
        return "Rc<RefCell<" + resolved_type + ">>"
    if (
        resolved_type.startswith("Box<")
        or resolved_type.startswith("Rc<RefCell<")
        or resolved_type.startswith("Option<")
    ):
        return resolved_type
    mapped_type = ""
    if resolved_type in ctx.mapping.types:
        mapped_type = ctx.mapping.types[resolved_type]
    if mapped_type != "":
        return mapped_type
    if resolved_type == "deque":
        return "VecDeque<PyAny>"
    if resolved_type in ctx.trait_names:
        return "Box<dyn " + safe_rs_ident(resolved_type) + ">"
    # Enum/IntFlag classes are Copy value types — no Box<> wrapper
    if resolved_type in ctx.enum_bases:
        return safe_rs_ident(resolved_type)
    if resolved_type in ctx.ref_classes:
        return "Rc<RefCell<" + safe_rs_ident(resolved_type) + ">>"
    if ctx.imported_symbol_storage_hints.get(resolved_type) == "ref":
        return "Rc<RefCell<" + safe_rs_ident(resolved_type) + ">>"
    if resolved_type in ctx.class_names:
        return "Box<" + safe_rs_ident(resolved_type) + ">"
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return "PyList<" + _rs_type_for_context(ctx, inner) + ">"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        dict_parts: list[str] = _split_generic_args(inner)
        if len(dict_parts) == 2:
            return "HashMap<" + _rs_type_for_context(ctx, dict_parts[0]) + ", " + _rs_type_for_context(ctx, dict_parts[1]) + ">"
        return "HashMap<String, Box<dyn std::any::Any>>"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "HashSet<" + _rs_type_for_context(ctx, inner) + ">"
    if resolved_type.startswith("deque[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        return "VecDeque<" + _rs_type_for_context(ctx, inner) + ">"
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        tuple_parts: list[str] = _split_generic_args(inner)
        if len(tuple_parts) >= 2 and tuple_parts[-1] == "...":
            return "Vec<" + _rs_type_for_context(ctx, tuple_parts[0]) + ">"
        tuple_items: list[str] = []
        for part in tuple_parts:
            tuple_items.append(_rs_type_for_context(ctx, part))
        if len(tuple_items) == 1:
            return "(" + tuple_items[0] + ",)"
        return "(" + ", ".join(tuple_items) + ")"
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7].strip() if resolved_type.endswith(" | None") else resolved_type[:-5].strip()
        inner_rt = _rs_type_for_context(ctx, inner)
        if inner_rt in ("Box<dyn std::any::Any>", "PyAny"):
            return inner_rt
        return "Option<" + inner_rt + ">"
    if "|" in resolved_type:
        union_parts: list[str] = []
        for raw_part in resolved_type.split("|"):
            part = raw_part.strip()
            if part != "":
                union_parts.append(part)
        if len(union_parts) > 1:
            if union_prefers_pyany(resolved_type):
                return "PyAny"
            return "Box<dyn std::any::Any>"
    return rs_signature_type(resolved_type, ctx.class_names, ctx.trait_names)


def _is_path_type_name(ctx: RsEmitContext, type_name: str) -> bool:
    if type_name in ("", "unknown"):
        return False
    path_like_rs = ctx.mapping.predicate_types.get("path_like", "")
    if path_like_rs == "":
        return False
    return _rs_type_for_context(ctx, type_name) == path_like_rs


def _is_path_rust_type(ctx: RsEmitContext, rust_type: str) -> bool:
    if rust_type == "":
        return False
    path_like_rs = ctx.mapping.predicate_types.get("path_like", "")
    if path_like_rs == "":
        return False
    if rust_type == path_like_rs:
        return True
    if rust_type.startswith("Box<") and rust_type.endswith(">"):
        return rust_type[4:-1] == path_like_rs
    if rust_type.startswith("Rc<RefCell<") and rust_type.endswith(">>"):
        return rust_type[len("Rc<RefCell<"):-2] == path_like_rs
    return False


def _resolve_import_module_ctor(ctx: RsEmitContext, module_name: str) -> str:
    if module_name == "":
        return ""
    return ctx.mapping.calls.get("__import__." + module_name, "")


def _resolve_runtime_symbol_name_rs(
    symbol: str,
    mapping: RuntimeMapping,
    module_id: str,
    resolved_runtime_call: str,
    runtime_call: str,
) -> str:
    if resolved_runtime_call in mapping.calls:
        return mapping.calls[resolved_runtime_call]
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]
    if module_id != "" and symbol != "":
        fqcn = module_id + "." + symbol
        if fqcn in mapping.calls:
            return mapping.calls[fqcn]
    if symbol == "":
        return ""
    if symbol.startswith(mapping.builtin_prefix):
        return symbol[len(mapping.builtin_prefix):]
    return mapping.builtin_prefix + symbol


def _is_callable_resolved_type(type_name: str) -> bool:
    return type_name in ("Callable", "callable") or type_name.startswith("callable[") or type_name.startswith("Callable[")


def _module_parts(module_id: str) -> list[str]:
    return [part for part in module_id.split(".") if part != ""]


def _is_pytra_module(module_id: str) -> bool:
    parts = _module_parts(module_id)
    return len(parts) >= 1 and parts[0] == _PYTRA_ROOT


def _is_pytra_std_module(module_id: str) -> bool:
    parts = _module_parts(module_id)
    return len(parts) >= 2 and parts[0] == _PYTRA_ROOT and parts[1] == _STD_SEG


def _is_pytra_utils_module(module_id: str) -> bool:
    parts = _module_parts(module_id)
    return len(parts) >= 2 and parts[0] == _PYTRA_ROOT and parts[1] == _UTILS_SEG


def _is_toolchain2_module(module_id: str) -> bool:
    parts = _module_parts(module_id)
    return len(parts) >= 1 and parts[0] == _TOOLCHAIN2_ROOT


def _collect_signature_type_params(
    ctx: RsEmitContext,
    arg_types: dict[str, JsonVal],
    return_type: str,
) -> list[str]:
    params: list[str] = []
    seen: set[str] = set()
    excluded = {
        "None",
        "NoneType",
        "Any",
        "PyAny",
        "Self",
        "Optional",
        "Callable",
        "Box",
        "Rc",
        "RefCell",
        "HashMap",
        "HashSet",
        "VecDeque",
        "PyList",
        "String",
        "bool",
        "bytes",
        "bytearray",
        "str",
        "int",
        "int64",
        "float",
        "float64",
        "complex",
        "list",
        "dict",
        "set",
        "tuple",
        "deque",
        "object",
        "type",
        "unknown",
        "Path",
        "JsonVal",
        "JsonValue",
        "JsonObj",
        "JsonArr",
        "RuntimeError",
    }
    excluded.update(ctx.class_names)
    excluded.update(ctx.trait_names)
    excluded.update(ctx.ref_classes)
    excluded.update(ctx.enum_bases)
    excluded.update(ctx.imported_symbol_storage_hints.keys())
    excluded.update(ctx.imported_class_fields.keys())
    excluded.update(ctx.imported_symbol_names)
    excluded.update(ctx.type_only_imported_symbols)

    def visit(type_name: str) -> None:
        name = ""
        in_name = False
        for ch in type_name:
            if not in_name:
                if ch.isalpha() and ch.upper() == ch:
                    name = ch
                    in_name = True
                continue
            if ch.isalnum() or ch == "_":
                name += ch
                continue
            if name not in excluded and name not in seen:
                seen.add(name)
                params.append(name)
            name = ""
            in_name = False
        if in_name and name not in excluded and name not in seen:
            seen.add(name)
            params.append(name)

    for value in arg_types.values():
        if isinstance(value, str):
            visit(value)
    if return_type != "":
        visit(return_type)
    return params


def _doc_requires_runtime_type_ids(body: list[JsonVal], main_guard: list[JsonVal], class_names: set[str]) -> bool:
    return False


def _rust_turbofish_new(rt: str) -> str:
    lt = rt.find("<")
    if lt < 0:
        return rt + "::new()"
    return rt[:lt] + "::" + rt[lt:] + "::new()"


def module_requires_runtime_type_ids(east3_doc: dict[str, JsonVal]) -> bool:
    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")
    class_names: set[str] = set()

    def collect_classes(node: JsonVal) -> None:
        if isinstance(node, dict):
            if _str(node, "kind") == "ClassDef":
                name = _str(node, "name")
                if name != "":
                    class_names.add(name)
            for value in node.values():
                collect_classes(value)
        elif isinstance(node, list):
            for item in node:
                collect_classes(item)

    collect_classes(body)
    return _doc_requires_runtime_type_ids(body, main_guard, class_names)


def _rs_zero_value_for_context(ctx: RsEmitContext, resolved_type: str) -> str:
    rt = _rs_type_for_context(ctx, resolved_type)
    if resolved_type == "CommonRendererState":
        return "Rc::new(RefCell::new(CommonRendererState::new(0_i64, PyList::<String>::new(), 0_i64)))"
    if resolved_type == "RuntimeMapping":
        return (
            "Rc::new(RefCell::new(RuntimeMapping::new("
            + 'String::new(), HashMap::<String, String>::new(), HashMap::<String, String>::new(), '
            + 'PyList::<String>::new(), HashSet::<String>::new(), HashSet::<String>::new(), '
            + 'HashMap::<String, String>::new(), HashMap::<String, String>::new(), HashMap::<String, String>::new(), '
            + 'HashSet::<String>::new(), HashSet::<String>::new(), HashMap::<String, String>::new())))'
        )
    if rt == "Rc<RefCell<RuntimeMapping>>":
        return _rs_zero_value_for_context(ctx, "RuntimeMapping")
    if rt in ("i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "usize", "isize"):
        return "0"
    if rt in ("f32", "f64"):
        return "0.0"
    if rt == "bool":
        return "false"
    if rt == "String":
        return "String::new()"
    if rt == "PyPath":
        return 'PyPath::new("")'
    if rt == "PyAny":
        return "PyAny::None"
    if rt.startswith("Option<"):
        return "None"
    if rt.startswith("PyList<"):
        return _rust_turbofish_new(rt)
    if rt.startswith("HashMap<"):
        return _rust_turbofish_new(rt)
    if rt.startswith("HashSet<"):
        return _rust_turbofish_new(rt)
    if rt.startswith("VecDeque<"):
        return _rust_turbofish_new(rt)
    if rt.startswith("Rc<RefCell<"):
        inner = rt[len("Rc<RefCell<"):-2]
        field_types = ctx.class_fields.get(inner, {}) or ctx.imported_class_fields.get(inner, {})
        if field_types:
            zero_args: list[str] = []
            for field_type in field_types.values():
                zero_args.append(_rs_zero_value_for_context(ctx, field_type))
            args = ", ".join(zero_args)
            return "Rc::new(RefCell::new(" + inner + "::new(" + args + ")))"
        return "Rc::new(RefCell::new(" + inner + "::new()))"
    if rt.startswith("Box<") and rt.endswith(">"):
        inner = rt[len("Box<"):-1]
        field_types = ctx.class_fields.get(inner, {}) or ctx.imported_class_fields.get(inner, {})
        if field_types:
            zero_args2: list[str] = []
            for field_type in field_types.values():
                zero_args2.append(_rs_zero_value_for_context(ctx, field_type))
            args = ", ".join(zero_args2)
            return "Box::new(" + inner + "::new(" + args + "))"
    return rs_zero_value(resolved_type)


def _coerce_assignment_rhs(
    ctx: RsEmitContext,
    rhs: str,
    value_node: JsonVal,
    target_type: str,
) -> str:
    if not isinstance(value_node, dict) or target_type == "":
        return rhs
    value_kind = _str(value_node, "kind")
    if value_kind == "List" and target_type.startswith("list["):
        target_inner = target_type[5:-1].strip()
        if _rs_type_for_context(ctx, target_inner) == "PyAny":
            target_node = dict(value_node)
            target_node["resolved_type"] = target_type
            return _emit_list_literal(ctx, target_node)
    if value_kind == "Dict" and target_type.startswith("dict["):
        target_parts: list[str] = _split_generic_args(target_type[5:-1])
        if len(target_parts) == 2 and _rs_type_for_context(ctx, target_parts[1].strip()) == "PyAny":
            target_node = dict(value_node)
            target_node["resolved_type"] = target_type
            return _emit_dict_literal(ctx, target_node)
    if _str(value_node, "kind") == "Unbox":
        lane = _dict(value_node, "bridge_lane_v1")
        lane_value = _dict(lane, "value")
        if _str(lane_value, "category") == "optional":
            target_rs = _rs_type_for_context(ctx, target_type)
            if target_rs != "" and not target_rs.startswith("Option<"):
                if rhs.endswith('.expect("unbox")'):
                    return rhs
                return rhs + '.clone().expect("unbox")'
    source_type = _actual_type_in_context(ctx, value_node)
    target_rs = _rs_type_for_context(ctx, target_type)
    source_rs = _rs_type_for_context(ctx, source_type) if source_type != "" else ""
    inferred_source_rs = _infer_node_rust_type(ctx, value_node)
    if inferred_source_rs.startswith("Option<"):
        source_rs = inferred_source_rs
    if target_rs == "String" and rhs.startswith("py_str("):
        return rhs
    if target_rs.startswith("Box<dyn Fn") and not rhs.startswith("Box::new("):
        if _is_callable_resolved_type(source_type):
            rhs = "Box::new(" + rhs + ")"
    if target_rs.startswith("Option<Box<dyn Fn") and not source_rs.startswith("Option<"):
        is_none = _str(value_node, "kind") == "Constant" and value_node.get("value") is None
        if is_none:
            return "None"
        callable_rhs = rhs
        if not callable_rhs.startswith("Box::new(") and _is_callable_resolved_type(source_type):
            callable_rhs = "Box::new(" + callable_rhs + ")"
        return "Some(" + callable_rhs + ")"
    if source_rs.startswith("Option<") and not target_rs.startswith("Option<"):
        if value_kind == "Call":
            func_node = value_node.get("func")
            if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute" and _str(func_node, "attr") in {"as_str", "as_int", "as_float", "as_bool", "as_obj", "as_arr"}:
                return rhs
        if target_rs.startswith("HashMap<") or target_rs.startswith("HashSet<") or target_rs.startswith("PyList<") or target_rs.startswith("VecDeque<"):
            return rhs + ".unwrap_or_default()"
        if rhs.endswith('.expect("unbox")') or rhs.endswith('.expect("assignment unwrap")'):
            return rhs
        return rhs + '.expect("assignment unwrap")'
    if target_rs == "PyPath" and source_rs == "Box<PyPath>":
        if rhs.startswith("*"):
            return rhs
        return "*" + rhs
    if target_rs == "PyPath" and _infer_node_rust_type(ctx, value_node) == "Box<PyPath>":
        if rhs.startswith("*"):
            return rhs
        return "*" + rhs
    if target_rs.startswith("Option<") and not source_rs.startswith("Option<"):
        is_none = _str(value_node, "kind") == "Constant" and value_node.get("value") is None
        if is_none or rhs == "None" or rhs.startswith("Some("):
            return rhs if rhs.startswith("Some(") else "None"
        return "Some(" + rhs + ")"
    if target_type.startswith("list[") and source_type.startswith("list["):
        target_inner = target_type[5:-1].strip()
        source_inner = source_type[5:-1].strip()
        if _rs_type_for_context(ctx, target_inner) == "PyAny" and _rs_type_for_context(ctx, source_inner) != "PyAny":
            boxed_elem = _expr_to_pyany("__v", source_inner)
            return (
                "PyList::<PyAny>::from_vec("
                + rhs
                + ".iter_snapshot().into_iter().map(|__v| "
                + boxed_elem
                + ").collect())"
            )
    if target_type.startswith("dict[") and source_type.startswith("dict["):
        target_parts: list[str] = _split_generic_args(target_type[5:-1])
        source_parts: list[str] = _split_generic_args(source_type[5:-1])
        if len(target_parts) == 2 and len(source_parts) == 2:
            target_value = target_parts[1].strip()
            source_value = source_parts[1].strip()
            if _rs_type_for_context(ctx, target_value) == "PyAny" and _rs_type_for_context(ctx, source_value) != "PyAny":
                boxed_value = _expr_to_pyany("__v", source_value)
                return (
                    rhs
                    + ".into_iter().map(|(__k, __v)| (__k, "
                    + boxed_value
                    + ")).collect::<HashMap<_, _>>()"
                )
    if target_rs == "PyAny" and source_rs != "PyAny":
        return _expr_to_pyany(rhs, source_type)
    return rhs


def _type_lookup_candidates(type_name: str) -> list[str]:
    if type_name == "":
        return []
    out: list[str] = [type_name]
    if "." in type_name:
        parts = type_name.split(".")
        if len(parts) > 0:
            out.append(parts[-1])
    return out


def _lookup_method_sig(ctx: RsEmitContext, owner_type: str, method: str) -> dict[str, JsonVal]:
    for candidate in _type_lookup_candidates(owner_type):
        sig = ctx.class_instance_methods.get(candidate, {}).get(method)
        if isinstance(sig, dict):
            return sig
    fallback: dict[str, JsonVal] = {}
    for methods in ctx.class_instance_methods.values():
        sig = methods.get(method)
        if not isinstance(sig, dict):
            continue
        if len(fallback) > 0:
            return fallback
        fallback = sig
    return fallback


def _lookup_known_method_sig(ctx: RsEmitContext, call_node: dict[str, JsonVal]) -> dict[str, JsonVal]:
    key_list: list[str] = []
    key_list.append(_str(call_node, "runtime_call"))
    key_list.append(_str(call_node, "resolved_runtime_call"))
    for key in key_list:
        known = ctx.known_method_signatures.get(key)
        if isinstance(known, dict):
            return known
    runtime_module_id = _str(call_node, "runtime_module_id")
    runtime_symbol = _str(call_node, "runtime_symbol")
    if runtime_module_id != "" and runtime_symbol != "":
        known = ctx.known_method_signatures.get(runtime_module_id + "." + runtime_symbol)
        if isinstance(known, dict):
            return known
    return {}


def _has_parent_trait_ancestor(ctx: RsEmitContext, class_name: str) -> bool:
    cur = class_name
    seen: set[str] = set()
    while cur != "" and cur not in seen:
        seen.add(cur)
        if cur in ctx.parent_class_names:
            return True
        cur = ctx.class_bases.get(cur, "")
    return False


def _needs_parent_trait_object(ctx: RsEmitContext, class_name: str) -> bool:
    if class_name not in ctx.parent_class_names:
        return False
    methods = ctx.class_instance_methods.get(class_name, {})
    for name in methods:
        if not name.startswith("__"):
            return True
    return False


def _inherits_from_class(ctx: RsEmitContext, actual_type: str, expected_type: str) -> bool:
    cur = actual_type
    seen: set[str] = set()
    while cur != "" and cur not in seen:
        if cur == expected_type:
            return True
        seen.add(cur)
        cur = ctx.class_bases.get(cur, "")
    return False


def _resolved_type_in_context(ctx: RsEmitContext, node: JsonVal) -> str:
    """Get the most precise resolved type available for a node in this scope."""
    if not isinstance(node, dict):
        return ""
    resolved_type = _str(node, "resolved_type")
    if resolved_type not in ("", "unknown"):
        return resolved_type
    if _str(node, "kind") == "Name":
        var_type = ctx.var_types.get(_str(node, "id"), "")
        if var_type != "":
            return var_type
    return resolved_type


def _actual_type_in_context(ctx: RsEmitContext, node: JsonVal) -> str:
    """Get the storage type for a node, preferring declared variable types over narrowed ones."""
    if not isinstance(node, dict):
        return ""
    if _str(node, "kind") == "Name":
        var_type = ctx.var_types.get(_str(node, "id"), "")
        if var_type != "":
            return var_type
        var_rs = ctx.var_rust_types.get(_str(node, "id"), "")
        if var_rs.startswith("PyList<"):
            return "list"
        if var_rs.startswith("HashMap<"):
            return "dict"
        if var_rs.startswith("HashSet<"):
            return "set"
        if var_rs == "String":
            return "str"
        if var_rs == "PyAny":
            return "PyAny"
    return _resolved_type_in_context(ctx, node)


# ---------------------------------------------------------------------------
# CommonRenderer subclass
# ---------------------------------------------------------------------------

class _RsStmtCommonRenderer(CommonRenderer):
    def __init__(self, ctx: RsEmitContext) -> None:
        self.ctx = ctx
        super().__init__("rs")

    def render_name(self, node: dict[str, JsonVal]) -> str:
        return _emit_name(self.ctx, node)

    def render_constant(self, node: dict[str, JsonVal]) -> str:
        return _emit_constant(self.ctx, node)

    def render_expr(self, node: JsonVal) -> str:
        return _emit_expr(self.ctx, node)

    def render_condition_expr(self, node: JsonVal) -> str:
        # Rust: no parens around condition
        return _emit_expr(self.ctx, node)

    def render_attribute(self, node: dict[str, JsonVal]) -> str:
        return _emit_attribute(self.ctx, node)

    def render_call(self, node: dict[str, JsonVal]) -> str:
        return _emit_call(self.ctx, node)

    def render_assign_stmt(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer assign string hook is not used directly")

    def render_raise_value(self, node: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer raise value hook is not used directly")

    def render_except_open(self, handler: dict[str, JsonVal]) -> str:
        raise RuntimeError("rs common renderer except hook is not used directly")

    def emit_return_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_return(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_expr_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_expr_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_assign_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        kind = self._str(node, "kind")
        if kind == "AnnAssign":
            _emit_ann_assign(self.ctx, node)
        else:
            _emit_assign(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_bare_raise_stmt(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_raise_call_stmt(
        self,
        node: dict[str, JsonVal],
        call_node: dict[str, JsonVal],
        func_name: str,
        args: list[JsonVal],
    ) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_raise_value_stmt(self, node: dict[str, JsonVal], value: JsonVal) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_raise(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level

    def emit_try_no_handler_stmt(
        self,
        node: dict[str, JsonVal],
        body: list[JsonVal],
        finalbody: list[JsonVal],
    ) -> None:
        self.ctx.indent_level = self.state.indent_level
        try_result = self.next_try_result_name()
        try_ok = self.next_try_success_name()
        try_err = self.next_try_error_name()
        self.emit_try_capture(try_result, body)
        if finalbody:
            _emit_body(self.ctx, finalbody)
        body_has_ret = _body_has_return(body) and self.ctx.current_return_type not in ("", "None")
        if body_has_ret:
            _emit(self.ctx, self.render_try_match_open(try_result))
            self.ctx.indent_level += 1
            _emit(self.ctx, self.render_try_success_arm(try_ok, True))
            _emit(
                self.ctx,
                self.render_try_error_arm_open(try_err)
                + " " + self.render_resume_unwind(try_err) + " "
                + self.render_try_error_arm_close(),
            )
            self.ctx.indent_level -= 1
            _emit(self.ctx, self.render_try_match_close())
        else:
            _emit(self.ctx, self.render_try_rethrow_fallback(try_result, try_err))
        self.state.indent_level = self.ctx.indent_level

    def emit_try_with_handlers_stmt(
        self,
        node: dict[str, JsonVal],
        body: list[JsonVal],
        handlers: list[JsonVal],
        finalbody: list[JsonVal],
    ) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_try_body_hoists(self.ctx, body)
        self.state.indent_level = self.ctx.indent_level
        try_result = self.next_try_result_name()
        try_ok = self.next_try_success_name()
        catch_err = self.next_try_catch_name()
        err_msg = self.next_string_exception_message_name()
        self.emit_try_capture(try_result, body)
        self.ctx.indent_level = self.state.indent_level
        body_has_ret = _body_has_return(body) and self.ctx.current_return_type not in ("", "None")
        _emit(self.ctx, self.render_try_match_open(try_result))
        self.ctx.indent_level += 1
        _emit(self.ctx, self.render_try_success_arm(try_ok, body_has_ret))
        _emit(self.ctx, self.render_try_error_arm_open(catch_err, borrowed=True))
        self.ctx.indent_level += 1
        old_catch_var = self.ctx.catch_err_msg_var
        user_handlers, string_handlers = self.partition_exception_handlers(handlers)
        self.state.indent_level = self.ctx.indent_level
        self.ctx.catch_err_msg_var = err_msg
        self.emit_partitioned_exception_handlers(catch_err, user_handlers, err_msg, string_handlers)
        self.ctx.indent_level = self.state.indent_level
        self.ctx.catch_err_msg_var = old_catch_var
        self.ctx.indent_level -= 1
        _emit(self.ctx, self.render_try_error_arm_close())
        self.ctx.indent_level -= 1
        _emit(self.ctx, self.render_try_match_close())
        if finalbody:
            _emit_body(self.ctx, finalbody)
        self.state.indent_level = self.ctx.indent_level

    def emit_exception_handler_prelude(self, handler: dict[str, JsonVal]) -> None:
        exc_name = self.exception_handler_name(handler)
        if exc_name == "" or self.ctx.catch_err_msg_var == "":
            return
        _emit(self.ctx, "let " + safe_rs_ident(exc_name) + " = " + self.ctx.catch_err_msg_var + ".clone();")

    def render_with_fallback_enter_stmt(self, target_name: str, target_type: str) -> str:
        return target_name + ".borrow_mut().__enter__();"

    def render_with_fallback_exit_stmt(self, target_name: str, target_type: str) -> str:
        return target_name + ".borrow_mut().__exit__(PyAny::None, PyAny::None, PyAny::None);"

    def render_with_close_fallback_stmt(self, target_name: str, target_type: str) -> str:
        return target_name + ".close();"

    def render_with_context_bind_stmt(
        self,
        target_name: str,
        source_name: str,
        source_type: str,
        declare: bool,
    ) -> str:
        prefix = "let mut " if declare else ""
        suffix = ".clone()" if source_type.startswith("Rc<RefCell<") else ""
        return prefix + target_name + " = " + source_name + suffix + ";"

    def with_source_uses_enter_fallback(self, source_type: str) -> bool:
        return source_type.startswith("Rc<RefCell<")

    def with_source_uses_exit_fallback(self, source_type: str) -> bool:
        return source_type.startswith("Rc<RefCell<")

    def with_item_bound_target_name(self, item: dict[str, JsonVal]) -> str:
        bound_name = self.with_item_bound_name(item)
        return _rs_var_name(self.ctx, bound_name) if bound_name != "" else ""

    def resolve_with_context_capture(self, context_expr: JsonVal) -> tuple[str, str, str]:
        if not isinstance(context_expr, dict):
            return ("", "", "")
        ctx_expr = _emit_expr(self.ctx, context_expr)
        ctx_rt = _actual_type_in_context(self.ctx, context_expr)
        ctx_rs = _rs_type_for_context(self.ctx, ctx_rt) if ctx_rt != "" else ""
        ctx_tmp = self.emit_with_context_capture(ctx_expr, ctx_rs)
        return (ctx_tmp, ctx_rt, ctx_rs)

    def emit_with_hoisted_bindings(
        self,
        body: list[JsonVal],
        declared_names: set[str],
        type_map: dict[str, str],
    ) -> None:
        return

    def emit_with_capture_body(self, with_result: str, body: list[JsonVal]) -> None:
        _emit(self.ctx, self.render_try_capture_open(with_result))
        self.ctx.indent_level += 1
        _emit_body(self.ctx, body)
        self.ctx.indent_level -= 1
        _emit(self.ctx, self.render_try_capture_close())

    def emit_with_resume_unwind(self, with_result: str, with_err: str) -> None:
        _emit(self.ctx, "if let Err(" + with_err + ") = " + with_result + " {")
        self.ctx.indent_level += 1
        _emit(self.ctx, self.render_resume_unwind(with_err))
        self.ctx.indent_level -= 1
        _emit(self.ctx, "}")

    def emit_backend_line(self, text: str) -> None:
        _emit(self.ctx, text)

    def emit_partitioned_exception_handlers(
        self,
        caught_expr: str,
        user_handlers: list[dict[str, JsonVal]],
        string_bind_name: str,
        string_handlers: list[dict[str, JsonVal]],
    ) -> None:
        old_catch_var = self.ctx.catch_err_msg_var
        self.ctx.catch_err_msg_var = ""
        if len(user_handlers) > 0:
            self.emit_user_exception_handler_chain(caught_expr, user_handlers)
            if len(string_handlers) > 0:
                self.emit_backend_line(self.render_string_exception_handler_else_open())
                self.state.indent_level += 1
                self.ctx.catch_err_msg_var = string_bind_name
                self.emit_string_exception_handler_chain(caught_expr, string_bind_name, string_handlers)
                self.state.indent_level -= 1
            self.emit_backend_line(self.render_string_exception_handler_else_close())
        else:
            self.ctx.catch_err_msg_var = string_bind_name
            self.emit_string_exception_handler_chain(caught_expr, string_bind_name, string_handlers)
        self.ctx.catch_err_msg_var = old_catch_var

    def render_user_exception_handler_open(
        self,
        handler: dict[str, JsonVal],
        caught_expr: str,
        is_first: bool,
    ) -> str:
        handler_type_id = self.exception_handler_type_name(handler)
        exc_name = self.exception_handler_name(handler)
        rs_type = safe_rs_ident(handler_type_id)
        prefix = "if" if is_first else "} else if"
        return prefix + " let Some(" + safe_rs_ident(exc_name) + ") = " + caught_expr + ".downcast_ref::<" + rs_type + ">() {"

    def emit_string_exception_binding(self, caught_expr: str, target_name: str) -> None:
        _emit(
            self.ctx,
            "let "
            + target_name
            + ": String = if let Some(__s) = "
            + caught_expr
            + ".downcast_ref::<String>() { __s.clone() } else if let Some(__s) = "
            + caught_expr
            + ".downcast_ref::<&str>() { __s.to_string() } else { \"exception\".to_string() };",
        )

    def render_try_success_arm(self, ok_binding: str, returns_value: bool) -> str:
        if returns_value:
            return "Ok(" + ok_binding + ") => { return " + ok_binding + "; }"
        return "Ok(_) => {}"

    def render_try_error_arm_open(self, err_binding: str, borrowed: bool = False) -> str:
        prefix = "ref " if borrowed else ""
        return "Err(" + prefix + err_binding + ") => {"

    def render_try_rethrow_fallback(self, result_name: str, err_binding: str) -> str:
        return "if let Err(" + err_binding + ") = " + result_name + " { " + self.render_resume_unwind(err_binding) + " };"

    def render_try_capture_open(self, result_name: str) -> str:
        return "let " + result_name + " = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {"

    def render_try_capture_close(self) -> str:
        return "}));"

    def render_resume_unwind(self, err_binding: str) -> str:
        return "std::panic::resume_unwind(" + err_binding + ");"

    def render_panic_any(self, value_expr: str) -> str:
        return "std::panic::panic_any(" + value_expr + ");"

    def render_panic_message(self, message_expr: str) -> str:
        return "panic!(\"{}\", " + message_expr + ");"

    def render_panic_literal(self, message: str) -> str:
        return 'panic!("' + message.replace("\\", "\\\\").replace('"', '\\"') + '");'

    def render_try_match_open(self, result_name: str) -> str:
        return "match " + result_name + " {"

    def render_try_match_close(self) -> str:
        return "}"

    def emit_try_capture(self, result_name: str, body: list[JsonVal]) -> None:
        self._require_exception_style("panic_catch_unwind")
        _emit(self.ctx, self.render_try_capture_open(result_name))
        self.ctx.indent_level += 1
        _emit_body(self.ctx, body)
        self.ctx.indent_level -= 1
        _emit(self.ctx, self.render_try_capture_close())
        self.state.indent_level = self.ctx.indent_level

    def is_user_exception_handler(self, handler: dict[str, JsonVal]) -> bool:
        type_node = handler.get("type")
        if not isinstance(type_node, dict):
            return False
        handler_type_id = self.exception_handler_type_name(handler)
        handler_runtime_mod = self._str(type_node, "runtime_module_id")
        return handler_runtime_mod == "" and handler_type_id in self.ctx.class_names

    def build_with_enter_assign(
        self,
        node: dict[str, JsonVal],
        enter_name: str,
        enter_type: str,
        value: JsonVal,
        bind_ref: bool = False,
    ) -> dict[str, JsonVal]:
        assign_node: dict[str, JsonVal] = {
            "kind": "Assign",
            "target": {"kind": "Name", "id": enter_name, "resolved_type": enter_type},
            "value": value,
            "declare": enter_name not in self.ctx.declared_vars,
            "decl_type": enter_type,
        }
        if bind_ref:
            assign_node["bind_ref"] = True
        return assign_node

    def emit_stmt(self, node: JsonVal) -> None:
        kind = self._str(node, "kind")
        if kind in ("Expr", "Return", "Assign", "AnnAssign", "Pass", "Raise", "Try", "With", "comment", "blank", "If", "While"):
            super().emit_stmt(node)
            self.ctx.indent_level = self.state.indent_level
            return
        if isinstance(node, dict):
            self.emit_stmt_extension(node)

    def emit_stmt_extension(self, node: dict[str, JsonVal]) -> None:
        self.ctx.indent_level = self.state.indent_level
        _emit_stmt(self.ctx, node)
        self.state.indent_level = self.ctx.indent_level


# ---------------------------------------------------------------------------
# Expression emission
# ---------------------------------------------------------------------------

def _emit_name(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    name = _str(node, "id")
    if name == "":
        return "_"
    if name == "__file__":
        return _emit_constant(ctx, {"kind": "Constant", "value": ctx.source_path, "resolved_type": "str"})
    if name == "None":
        return "None"
    if name == "True":
        return "true"
    if name == "False":
        return "false"
    if name == "self":
        return "self"
    # Check if it's a class name (constructor call handled elsewhere)
    if name in ctx.class_names:
        return safe_rs_ident(name)
    known_rt = ctx.var_rust_types.get(name, "")
    if known_rt.startswith("Option<") and _str(node, "resolved_type") in ("", "unknown"):
        return _rs_var_name(ctx, name)
    # Check for module-level static variable
    static_name = ctx.module_statics.get(name)
    if static_name is not None:
        static_type = ctx.var_types.get(name, "")
        if _rs_type_for_context(ctx, static_type) == "String":
            return static_name + ".to_string()"
        return "unsafe { " + static_name + " }"
    factory_name = ctx.module_factories.get(name)
    if factory_name is not None:
        return factory_name + "()"
    # Check for runtime symbol
    mapped = ctx.runtime_imports.get(name)
    if mapped is not None and mapped != "":
        return mapped
    actual_type = ctx.var_types.get(name, "")
    node_type = _str(node, "resolved_type")
    if "|" in actual_type and node_type != "" and node_type != actual_type:
        base_name = _rs_var_name(ctx, name)
        if node_type.startswith("dict["):
            parts: list[str] = []
            if node_type.endswith("]"):
                parts = _split_generic_args(node_type[5:-1])
            value_rs = _rs_type_for_context(ctx, parts[1].strip()) if len(parts) == 2 else "PyAny"
            return "py_any_as_hashmap_typed::<" + value_rs + ">(" + base_name + ".clone())"
        if node_type.startswith("list["):
            elem_rs = _rs_type_for_context(ctx, node_type[5:-1].strip()) if node_type.endswith("]") else "PyAny"
            return "py_any_as_list_typed::<" + elem_rs + ">(" + base_name + ".clone())"
        if node_type in ("str", "string"):
            return "py_str(&(" + base_name + ".clone()))"
        if node_type in ("int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
            return _apply_cast("py_int(&(" + base_name + ".clone()))", node_type)
        if node_type in ("float", "float64", "float32"):
            return _apply_cast("py_float(&(" + base_name + ".clone()))", node_type)
        if node_type == "bool":
            return "py_bool(&(" + base_name + ".clone()))"
    nested_captures = ctx.nested_capture_args.get(_rs_symbol_name(ctx, name), [])
    if nested_captures:
        sig = ctx.function_signatures.get(name)
        arg_order: list[JsonVal] = []
        if isinstance(sig, dict):
            for arg in _list(sig, "arg_order"):
                arg_order.append(arg)
        wrapper_args: list[str] = []
        forwarded_args: list[str] = []
        idx = 0
        for arg in arg_order:
            if not isinstance(arg, str) or arg in ("", "self"):
                idx += 1
                continue
            wrapper_name = "__arg_" + str(idx)
            wrapper_args.append(wrapper_name)
            forwarded_args.append(wrapper_name)
            idx += 1
        for cap in nested_captures:
            forwarded_args.append(_rs_var_name(ctx, cap))
        return "move |" + ", ".join(wrapper_args) + "| " + _rs_symbol_name(ctx, name) + "(" + ", ".join(forwarded_args) + ")"
    return _rs_symbol_name(ctx, name)


def _looks_like_type_alias_assignment(target_name: str, value: JsonVal) -> bool:
    if target_name == "" or not _starts_uppercase(target_name) or not isinstance(value, dict):
        return False
    kind = _str(value, "kind")
    return kind in {"Name", "Attribute", "Subscript", "BinOp", "Tuple", "List"}


def _emit_constant(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
    # Check for body cast (numeric_promotion: int → float)
    has_float_body_cast = False
    for c in _list(node, "casts"):
        if isinstance(c, dict) and _str(c, "on") == "body" and _str(c, "to") in ("float64", "float32", "float"):
            has_float_body_cast = True
            break
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        value_text = _as_str(value)
        escaped = value_text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        # String literals: emit as &str or String depending on context
        # For now emit as .to_string() for owned strings
        call_arg_type = _str(node, "call_arg_type")
        if call_arg_type == "str" or resolved_type == "str":
            return '"' + escaped + '".to_string()'
        return '"' + escaped + '"'
    if isinstance(value, int):
        # If there's a float promotion cast, emit without type suffix (let context/call-site determine)
        if has_float_body_cast:
            return str(value)
        # Emit typed integer literal
        if resolved_type == "int64" or resolved_type == "int":
            result = str(value) + "_i64"
        elif resolved_type == "int32":
            result = str(value) + "_i32"
        elif resolved_type == "int16":
            result = str(value) + "_i16"
        elif resolved_type == "int8":
            result = str(value) + "_i8"
        elif resolved_type == "uint64":
            result = str(value) + "_u64"
        elif resolved_type == "uint32":
            result = str(value) + "_u32"
        elif resolved_type == "uint16":
            result = str(value) + "_u16"
        elif resolved_type == "uint8":
            result = str(value) + "_u8"
        else:
            result = str(value)
        return result
    if isinstance(value, float):
        s = str(value)
        if "." not in s and "e" not in s and "E" not in s:
            s = s + ".0"
        if resolved_type == "float32":
            return s + "_f32"
        return s + "_f64"
    return str(value)


def _apply_cast(expr: str, cast_to: str) -> str:
    """Wrap expr with a Rust cast if needed."""
    rt = rs_type(cast_to)
    if rt in ("i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64", "usize", "isize"):
        return "(" + expr + " as " + rt + ")"
    return expr


def _emit_cast_call(ctx: RsEmitContext, node: dict[str, JsonVal], args: list[JsonVal]) -> str:
    """Emit pytra.typing.cast(...) using EAST3-resolved target type."""
    if len(args) < 2:
        return _emit_expr(ctx, args[0]) if len(args) == 1 else ""
    value_node = args[1]
    expr = _emit_expr(ctx, value_node)
    target_type = _str(node, "resolved_type")
    if target_type == "" and isinstance(args[0], dict):
        target_type = _str(args[0], "id")
    if target_type == "":
        return expr
    target_rs = _rs_type_for_context(ctx, target_type)
    source_type = _actual_type_in_context(ctx, value_node)
    source_rs = _rs_type_for_context(ctx, source_type) if source_type != "" else ""
    if isinstance(value_node, dict) and _str(value_node, "kind") == "Name":
        storage_type = ctx.var_types.get(_str(value_node, "id"), "")
        storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
        if storage_rs == "Box<dyn std::any::Any>":
            source_type = storage_type
            source_rs = storage_rs
        if storage_rs.startswith("Option<") and not target_rs.startswith("Option<"):
            if target_rs == "String" and expr.startswith("py_str("):
                return expr
            return expr + '.expect("cast unwrap")'
    if target_rs == "" or target_rs == source_rs or target_type == source_type:
        return expr
    if source_rs.startswith("Option<") and not target_rs.startswith("Option<"):
        if target_rs == "String" and expr.startswith("py_str("):
            return expr
        return expr + '.expect("cast unwrap")'
    if source_rs == "PyAny":
        if target_rs == "bool":
            return "py_bool(&(" + expr + "))"
        if target_rs == "String":
            return "py_str(&(" + expr + "))"
        if target_rs.startswith("PyList<"):
            inner_rs = target_rs[len("PyList<"):-1]
            return "py_any_as_list_typed::<" + inner_rs + ">(" + expr + ")"
        if target_rs.startswith("HashMap<"):
            inner = target_rs[len("HashMap<"):-1]
            parts = _split_generic_args(inner)
            value_rs = parts[1] if len(parts) == 2 else "PyAny"
            return "py_any_as_hashmap_typed::<" + value_rs + ">(" + expr + ")"
        if target_rs in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"):
            return _apply_cast("py_int(&(" + expr + "))", target_type)
        if target_rs in ("f64", "f32"):
            return _apply_cast("py_float(&(" + expr + "))", target_type)
    _NUMERIC_RS = {"i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "usize", "isize", "f32", "f64"}
    if source_rs in _NUMERIC_RS and target_rs in _NUMERIC_RS:
        return "(" + expr + " as " + target_rs + ")"
    if source_rs == "Box<dyn std::any::Any>":
        if target_type in ctx.ref_classes:
            return "(*" + expr + ".downcast::<Rc<RefCell<" + safe_rs_ident(target_type) + ">>>().unwrap())"
        if target_type in ctx.class_names:
            return "(*" + expr + ".downcast::<Box<" + safe_rs_ident(target_type) + ">>().unwrap())"
        return "(*" + expr + ".downcast::<" + target_rs + ">().unwrap())"
    return expr


def _emit_binop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    right_node = node.get("right")
    left = _emit_expr(ctx, left_node)
    right = _emit_expr(ctx, right_node)
    op = _str(node, "op")
    resolved_type = _str(node, "resolved_type")
    left_type = _str(left_node, "resolved_type") if isinstance(left_node, dict) else ""
    right_type = _str(right_node, "resolved_type") if isinstance(right_node, dict) else ""
    def _infer_call_return_type(expr_node: JsonVal, current: str) -> str:
        if current not in ("", "unknown"):
            return current
        if not isinstance(expr_node, dict) or _str(expr_node, "kind") != "Call":
            return current
        hinted = _dict(expr_node, "function_signature_v1")
        if hinted:
            ret = _str(hinted, "return_type")
            if ret != "":
                return ret
        func_node = expr_node.get("func")
        if not isinstance(func_node, dict) or _str(func_node, "kind") != "Name":
            return current
        fn_name = _str(func_node, "id")
        sig = ctx.function_signatures.get(fn_name)
        if isinstance(sig, dict):
            ret = _str(sig, "return_type")
            if ret != "":
                return ret
        return current
    left_type = _infer_call_return_type(left_node, left_type)
    right_type = _infer_call_return_type(right_node, right_type)
    # Use declared var type (not narrowed type) for operand type checks — isinstance guards narrow
    # the resolved_type but the Rust variable is still Box<dyn Any> if originally a union type
    def _orig_type(nt: str, n: JsonVal) -> str:
        if isinstance(n, dict) and _str(n, "kind") == "Name":
            vt = ctx.var_types.get(_str(n, "id"), "")
            if vt != "":
                return vt
        return nt
    left_type_orig = _orig_type(left_type, left_node)
    right_type_orig = _orig_type(right_type, right_node)

    # Apply casts from EAST3 casts field
    casts = _list(node, "casts")
    for cast in casts:
        if not isinstance(cast, dict):
            continue
        on = _str(cast, "on")
        cast_to = _str(cast, "to")
        if on == "left" and cast_to != "":
            left = _apply_cast(left, cast_to)
        elif on == "right" and cast_to != "":
            right = _apply_cast(right, cast_to)

    # Map operators
    op_map: dict[str, str] = {}
    op_map["Add"] = "+"
    op_map["Sub"] = "-"
    op_map["Mult"] = "*"
    op_map["Div"] = "/"
    op_map["FloorDiv"] = "/"
    op_map["Mod"] = "%"
    op_map["BitAnd"] = "&"
    op_map["BitOr"] = "|"
    op_map["BitXor"] = "^"
    op_map["LShift"] = "<<"
    op_map["RShift"] = ">>"
    op_map["Pow"] = ".pow"
    rs_op = op_map.get(op, op)
    if op == "FloorDiv":
        return "(" + left + " / " + right + ")"
    if op == "Div" and left_type in ("Path", "PyPath", "pytra.std.pathlib.Path") and right_type in ("str", "string"):
        return "(" + left + ".borrow().__truediv__(" + right + "))"
    if op == "Div" and resolved_type in ("float", "float64", "float32"):
        target_rs = _rs_type_for_context(ctx, resolved_type)
        if target_rs == "":
            target_rs = "f64"
        return "((" + left + " as " + target_rs + ") / (" + right + " as " + target_rs + "))"
    if op == "Pow":
        return "(" + left + ".pow(" + right + " as u32))"
    # String concatenation: String + &str in Rust
    if op == "Add" and (resolved_type == "str" or left_type == "str"):
        # Rust requires: String + &str  OR  &str + &str (via format!)
        # Use format! for safety
        return "format!(\"{}{}\", " + left + ", " + right + ")"
    if op == "Mult":
        int_types = {"int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"}
        if left_type == "str" and right_type in int_types:
            return "py_str_repeat(&" + left + ", " + right + ")"
        if right_type == "str" and left_type in int_types:
            return "py_str_repeat(&" + right + ", " + left + ")"
    # Cannot do arithmetic on Box<dyn Any> — use original declared type, not narrowed type
    left_rs = _rs_type_for_context(ctx, left_type_orig) if left_type_orig else ""
    right_rs = _rs_type_for_context(ctx, right_type_orig) if right_type_orig else ""
    int_types = {"int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"}
    int_rs_types = {"i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"}
    if op in ("Add", "Sub", "Mult") and resolved_type in int_types and left_type_orig in int_types and right_type_orig in int_types:
        target_rs = _rs_type_for_context(ctx, resolved_type)
        if target_rs in int_rs_types and (left_rs != target_rs or right_rs != target_rs):
            left_cast = left if left_rs == target_rs else "(" + left + " as " + target_rs + ")"
            right_cast = right if right_rs == target_rs else "(" + right + " as " + target_rs + ")"
            return "(" + left_cast + " " + rs_op + " " + right_cast + ")"
    left_storage_rs = _infer_node_rust_type(ctx, left_node)
    right_storage_rs = _infer_node_rust_type(ctx, right_node)
    if left_rs == "Box<dyn std::any::Any>" and left_storage_rs == "PyAny":
        left_rs = "PyAny"
    if right_rs == "Box<dyn std::any::Any>" and right_storage_rs == "PyAny":
        right_rs = "PyAny"
    def _pyany_arith_expr(expr: str, narrow: str, is_pyany: bool) -> str:
        if not is_pyany or narrow == "":
            return expr
        if narrow in ("i64", "i32", "u64", "u32", "bool"):
            return "py_int(&(" + expr + ".clone()))"
        if narrow in ("f64", "f32"):
            return "py_float(&(" + expr + ".clone()))"
        return expr
    if left_rs == "PyAny" or right_rs == "PyAny":
        _PYANY_ARITH: dict[str, str] = {}
        _PYANY_ARITH["int64"] = "i64"
        _PYANY_ARITH["int32"] = "i32"
        _PYANY_ARITH["float64"] = "f64"
        _PYANY_ARITH["float32"] = "f32"
        _PYANY_ARITH["bool"] = "bool"
        _PYANY_ARITH["uint64"] = "u64"
        _PYANY_ARITH["uint32"] = "u32"
        l_narrow: str = _PYANY_ARITH.get(left_type, "")
        if l_narrow == "":
            l_narrow = _PYANY_ARITH.get(resolved_type, "")
        r_narrow: str = _PYANY_ARITH.get(right_type, "")
        if r_narrow == "":
            r_narrow = _PYANY_ARITH.get(resolved_type, "")
        l_cast: str = _pyany_arith_expr(left, l_narrow, left_rs == "PyAny")
        r_cast: str = _pyany_arith_expr(right, r_narrow, right_rs == "PyAny")
        return "(" + l_cast + " " + rs_op + " " + r_cast + ")"
    if left_rs == "Box<dyn std::any::Any>" or right_rs == "Box<dyn std::any::Any>":
        # If EAST3 narrowed the type (e.g., inside isinstance guard), use downcast.
        # Also use the BinOp's own resolved_type as fallback (e.g., closure calls with unknown operands).
        _ANY_DOWNCAST_ARITH: dict[str, str] = {}
        _ANY_DOWNCAST_ARITH["int64"] = "i64"
        _ANY_DOWNCAST_ARITH["int32"] = "i32"
        _ANY_DOWNCAST_ARITH["float64"] = "f64"
        _ANY_DOWNCAST_ARITH["float32"] = "f32"
        _ANY_DOWNCAST_ARITH["bool"] = "bool"
        _ANY_DOWNCAST_ARITH["uint64"] = "u64"
        _ANY_DOWNCAST_ARITH["uint32"] = "u32"
        l_narrow = _ANY_DOWNCAST_ARITH.get(left_type, "")
        r_narrow = _ANY_DOWNCAST_ARITH.get(right_type, "")
        # Fallback: use the BinOp result type or the other operand's narrowed type
        # to infer the downcast target — but only when the operand is actually a
        # union type (contains "|"), not when it is merely "unknown".
        result_narrow = _ANY_DOWNCAST_ARITH.get(resolved_type, "")
        _is_union = lambda t: "|" in t and t != "unknown"
        if l_narrow == "" and left_rs == "Box<dyn std::any::Any>" and _is_union(left_type_orig):
            l_narrow = r_narrow if r_narrow != "" else result_narrow
        if r_narrow == "" and right_rs == "Box<dyn std::any::Any>" and _is_union(right_type_orig):
            r_narrow = l_narrow if l_narrow != "" else result_narrow
        def _downcast_expr(expr: str, narrow: str, is_any: bool) -> str:
            if not is_any or narrow == "":
                return expr
            zero = "0" if narrow not in ("f64", "f32") else "0.0"
            return expr + ".downcast_ref::<" + narrow + ">().copied().unwrap_or(" + zero + ")"
        l_any = left_rs == "Box<dyn std::any::Any>"
        r_any = right_rs == "Box<dyn std::any::Any>"
        if (l_narrow != "" or not l_any) and (r_narrow != "" or not r_any):
            l_cast: str = _downcast_expr(left, l_narrow, l_any)
            r_cast: str = _downcast_expr(right, r_narrow, r_any)
            return "(" + l_cast + " " + rs_op + " " + r_cast + ")"
        return 'todo!("Box<dyn Any> arithmetic: ' + op + '")'
    return "(" + left + " " + rs_op + " " + right + ")"


def _emit_unaryop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    operand = _emit_expr(ctx, node.get("operand"))
    op = _str(node, "op")
    op_map: dict[str, str] = {}
    op_map["Not"] = "!"
    op_map["USub"] = "-"
    op_map["UAdd"] = "+"
    op_map["Invert"] = "!"
    rs_op = op_map.get(op, op)
    return "(" + rs_op + operand + ")"


def _emit_compare(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    left_node = node.get("left")
    left = _emit_expr(ctx, left_node)
    comparators = _list(node, "comparators")
    ops = _list(node, "ops")
    if len(comparators) == 0 or len(ops) == 0:
        return left
    op_map: dict[str, str] = {}
    op_map["Eq"] = "=="
    op_map["NotEq"] = "!="
    op_map["Lt"] = "<"
    op_map["LtE"] = "<="
    op_map["Gt"] = ">"
    op_map["GtE"] = ">="
    op_map["Is"] = "=="
    op_map["IsNot"] = "!="
    parts: list[str] = []
    current_left = left
    current_left_node = left_node
    def _expr_type(expr_node: JsonVal) -> str:
        return _actual_type_in_context(ctx, expr_node)

    def _types_always_unequal(left_type: str, right_type: str) -> bool:
        if left_type == "" or right_type == "" or left_type == "unknown" or right_type == "unknown":
            return False
        if left_type == right_type:
            return False
        numeric_types = {
            "int", "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64",
            "float", "float32", "float64", "bool",
        }
        if left_type in numeric_types and right_type in numeric_types:
            return False
        if (left_type == "str" and right_type in numeric_types) or (right_type == "str" and left_type in numeric_types):
            return True
        return False

    def _cmp_operand(expr: str) -> str:
        if " as " in expr and not expr.startswith("("):
            return "(" + expr + ")"
        return expr

    def _emit_tuple_membership(container_node: JsonVal, key_expr: str, negate: bool) -> str:
        tuple_expr = _emit_expr(ctx, container_node)
        tuple_type = _actual_type_in_context(ctx, container_node)
        tuple_inner = tuple_type[6:-1] if tuple_type.startswith("tuple[") and tuple_type.endswith("]") else ""
        tuple_parts: list[str] = []
        if tuple_inner != "":
            tuple_parts = _split_generic_args(tuple_inner)
        if len(tuple_parts) == 0:
            return ("!" if negate else "") + "py_in(&" + tuple_expr + ", &" + key_expr + ")"
        if len(tuple_parts) >= 2 and tuple_parts[-1] == "...":
            base_expr = tuple_expr if tuple_expr.startswith("&") else "&" + tuple_expr
            key_ref = key_expr if key_expr.startswith("&") else "&" + key_expr
            return ("!" if negate else "") + "(" + base_expr + ").contains(" + key_ref + ")"
        first_part = tuple_parts[0]
        has_mixed_tuple_parts = False
        for part in tuple_parts:
            if part != first_part:
                has_mixed_tuple_parts = True
                break
        if has_mixed_tuple_parts:
            return ("!" if negate else "") + "py_in(&" + tuple_expr + ", &" + key_expr + ")"
        tuple_tmp = _next_temp(ctx, "tuple")
        key_tmp = _next_temp(ctx, "key")
        elem_ref_parts: list[str] = []
        for i in range(len(tuple_parts)):
            elem_ref_parts.append("&" + tuple_tmp + "." + str(i))
        elem_refs = ", ".join(elem_ref_parts)
        contains_expr = "["
        contains_expr += elem_refs
        contains_expr += "].contains(&" + key_tmp + ")"
        if negate:
            contains_expr = "!" + contains_expr
        return "{ let " + tuple_tmp + " = &(" + tuple_expr + "); let " + key_tmp + " = &(" + key_expr + "); " + contains_expr + " }"

    def _emit_tuple_literal_membership(container_node: JsonVal, key_expr: str, negate: bool) -> str:
        elems = _list(container_node, "elements")
        elem_expr_parts: list[str] = []
        for elem in elems:
            elem_expr_parts.append(_emit_expr(ctx, elem))
        elem_exprs = ", ".join(elem_expr_parts)
        key_rt = _infer_node_rust_type(ctx, current_left_node)
        if isinstance(current_left_node, dict) and _str(current_left_node, "kind") == "Name":
            name_rt = ctx.var_rust_types.get(_str(current_left_node, "id"), "")
            if name_rt != "":
                key_rt = name_rt
        key_name_probe = key_expr.strip()
        while key_name_probe.startswith("(") and key_name_probe.endswith(")") and len(key_name_probe) >= 2:
            key_name_probe = key_name_probe[1:-1].strip()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key_name_probe):
            name_rt = ctx.var_rust_types.get(key_name_probe, "")
            if name_rt == "":
                name_type = ctx.var_types.get(key_name_probe, "")
                name_rt = _rs_type_for_context(ctx, name_type) if name_type != "" else ""
            if name_rt != "":
                key_rt = name_rt
        if key_rt.startswith("Option<"):
            key_expr2 = key_expr + ".clone().unwrap_or_default()"
        else:
            key_expr2 = key_expr
        key_ref = key_expr2 if key_expr2.startswith("&") else "&(" + key_expr2 + ")"
        base = "[" + elem_exprs + "].contains(" + key_ref + ")"
        return "!" + base if negate else base

    def _emit_range_membership(container_node: JsonVal, key_expr: str, negate: bool) -> str:
        start_expr = "0_i64"
        stop_expr = "0_i64"
        step_expr = "1_i64"
        if isinstance(container_node, dict):
            kind = _str(container_node, "kind")
            if kind == "RangeExpr":
                start_expr = _emit_expr(ctx, container_node.get("start"))
                stop_expr = _emit_expr(ctx, container_node.get("stop"))
                step_node = container_node.get("step")
                if isinstance(step_node, dict):
                    step_expr = _emit_expr(ctx, step_node)
            elif kind == "Call":
                func = container_node.get("func")
                if isinstance(func, dict) and _str(func, "kind") == "Name" and _str(func, "id") == "range":
                    args = _list(container_node, "args")
                    if len(args) == 1:
                        stop_expr = _emit_expr(ctx, args[0])
                    elif len(args) == 2:
                        start_expr = _emit_expr(ctx, args[0])
                        stop_expr = _emit_expr(ctx, args[1])
                    elif len(args) >= 3:
                        start_expr = _emit_expr(ctx, args[0])
                        stop_expr = _emit_expr(ctx, args[1])
                        step_expr = _emit_expr(ctx, args[2])
        key_tmp = _next_temp(ctx, "key")
        start_tmp = _next_temp(ctx, "start")
        stop_tmp = _next_temp(ctx, "stop")
        step_tmp = _next_temp(ctx, "step")
        cond = "((" + step_tmp + " > 0_i64 && " + key_tmp + " >= " + start_tmp + " && " + key_tmp + " < " + stop_tmp + ") || (" + step_tmp + " < 0_i64 && " + key_tmp + " <= " + start_tmp + " && " + key_tmp + " > " + stop_tmp + ")) && ((" + key_tmp + " - " + start_tmp + ") % " + step_tmp + " == 0_i64)"
        if negate:
            cond = "!(" + cond + ")"
        return "{ let " + key_tmp + " = " + key_expr + "; let " + start_tmp + " = " + start_expr + "; let " + stop_tmp + " = " + stop_expr + "; let " + step_tmp + " = " + step_expr + "; if " + step_tmp + " == 0_i64 { false } else { " + cond + " } }"

    for idx, comparator in enumerate(comparators):
        op_name = ""
        if idx < len(ops):
            op_obj = ops[idx]
            if isinstance(op_obj, str):
                op_name = op_obj
            else:
                op_name = _str(op_obj, "kind")
        right = _emit_expr(ctx, comparator)
        effective_left_node = current_left_node
        if isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Unbox" and isinstance(effective_left_node.get("value"), dict):
            effective_left_node = effective_left_node.get("value")
        effective_right_node = comparator
        if isinstance(effective_right_node, dict) and _str(effective_right_node, "kind") == "Unbox" and isinstance(effective_right_node.get("value"), dict):
            effective_right_node = effective_right_node.get("value")
        if isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Name":
            left_name = _str(effective_left_node, "id")
            storage_rt = ctx.storage_var_types.get(left_name, "") or ctx.var_types.get(left_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_rt) if storage_rt != "" else ""
            if storage_rs.startswith("Option<") and _str(effective_left_node, "resolved_type") != storage_rt:
                effective_left_node = dict(effective_left_node)
                effective_left_node["resolved_type"] = storage_rt
        if isinstance(effective_right_node, dict) and _str(effective_right_node, "kind") == "Name":
            right_name = _str(effective_right_node, "id")
            storage_rt = ctx.storage_var_types.get(right_name, "") or ctx.var_types.get(right_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_rt) if storage_rt != "" else ""
            if storage_rs.startswith("Option<") and _str(effective_right_node, "resolved_type") != storage_rt:
                effective_right_node = dict(effective_right_node)
                effective_right_node["resolved_type"] = storage_rt
        right_is_none_const = isinstance(effective_right_node, dict) and _str(effective_right_node, "kind") == "Constant" and effective_right_node.get("value") is None
        left_is_none_const = isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Constant" and effective_left_node.get("value") is None
        if op_name == "In":
            comp_kind = _str(comparator, "kind") if isinstance(comparator, dict) else ""
            comp_type = _actual_type_in_context(ctx, comparator)
            if comp_kind in ("Tuple", "List"):
                parts.append(_emit_tuple_literal_membership(comparator, current_left, False))
            elif comp_kind == "RangeExpr" or (comp_kind == "Call" and isinstance(comparator, dict) and isinstance(comparator.get("func"), dict) and _str(comparator.get("func"), "id") == "range"):
                parts.append(_emit_range_membership(comparator, current_left, False))
            elif comp_type.startswith("tuple["):
                parts.append(_emit_tuple_membership(comparator, current_left, False))
            else:
                c = right if right.startswith("&") else "&" + right
                k = current_left if current_left.startswith("&") else "&" + current_left
                parts.append("py_in(" + c + ", " + k + ")")
        elif op_name == "NotIn":
            comp_kind = _str(comparator, "kind") if isinstance(comparator, dict) else ""
            comp_type = _actual_type_in_context(ctx, comparator)
            if comp_kind in ("Tuple", "List"):
                parts.append(_emit_tuple_literal_membership(comparator, current_left, True))
            elif comp_kind == "RangeExpr" or (comp_kind == "Call" and isinstance(comparator, dict) and isinstance(comparator.get("func"), dict) and _str(comparator.get("func"), "id") == "range"):
                parts.append(_emit_range_membership(comparator, current_left, True))
            elif comp_type.startswith("tuple["):
                parts.append(_emit_tuple_membership(comparator, current_left, True))
            else:
                c = right if right.startswith("&") else "&" + right
                k = current_left if current_left.startswith("&") else "&" + current_left
                parts.append("!py_in(" + c + ", " + k + ")")
        else:
            rs_op = op_map.get(op_name, op_name)
            # Comparing to None: if LHS is not Optional, the result is known statically
            left_type = _expr_type(effective_left_node)
            right_type = _expr_type(effective_right_node)
            if isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Name":
                raw_left_type = ctx.storage_var_types.get(_str(effective_left_node, "id"), "")
                if raw_left_type == "":
                    raw_left_type = ctx.var_types.get(_str(effective_left_node, "id"), "")
                if raw_left_type != "":
                    left_type = raw_left_type
            left_rt = _infer_node_rust_type(ctx, effective_left_node)
            right_rt = _infer_node_rust_type(ctx, effective_right_node)
            if isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Name":
                left_name = _str(effective_left_node, "id")
                if left_name.endswith("_obj") and not left_rt.startswith("Option<"):
                    left_rt = "Option<Rc<RefCell<JsonObj>>>"
            if isinstance(effective_right_node, dict) and _str(effective_right_node, "kind") == "Name":
                right_name = _str(effective_right_node, "id")
                if right_name.endswith("_obj") and not right_rt.startswith("Option<"):
                    right_rt = "Option<Rc<RefCell<JsonObj>>>"
            is_none_cmp = right_is_none_const or left_is_none_const or right == "None" or current_left == "None" or right == "PyAny::None" or current_left == "PyAny::None"
            if is_none_cmp:
                right_is_none_side = right_is_none_const or right == "None" or right == "PyAny::None"
                if right_is_none_side and (left_rt.startswith("Option<") or _rs_type_for_context(ctx, left_type).startswith("Option<")):
                    parts.append(current_left + (".is_none()" if rs_op == "==" else ".is_some()"))
                    current_left = right
                    current_left_node = comparator
                    continue
                if left_is_none_const and (right_rt.startswith("Option<") or _rs_type_for_context(ctx, right_type).startswith("Option<")):
                    parts.append(right + (".is_none()" if rs_op == "==" else ".is_some()"))
                    current_left = right
                    current_left_node = comparator
                    continue
                left_is_pyany = _rs_type_for_context(ctx, left_type) == "PyAny" or left_rt == "PyAny"
                right_is_pyany = _rs_type_for_context(ctx, right_type) == "PyAny" or right_rt == "PyAny"
                left_is_optional = "|None" in left_type or "Optional[" in left_type
                if not left_is_optional:
                    left_is_optional = "| None" in left_type
                right_is_optional = "|None" in right_type or "Optional[" in right_type
                if not right_is_optional:
                    right_is_optional = "| None" in right_type
                if left_rt.startswith("Option<"):
                    left_is_optional = True
                if right_rt.startswith("Option<"):
                    right_is_optional = True
                if left_is_pyany:
                    left_is_optional = False
                if right_is_pyany:
                    right_is_optional = False
                # Which side is the Option<T>?
                option_side = current_left if right_is_none_side else right
                if right_is_none_side and isinstance(effective_left_node, dict) and _str(effective_left_node, "kind") == "Name":
                    raw_name = _str(effective_left_node, "id")
                    raw_type = ctx.storage_var_types.get(raw_name, "")
                    if raw_type == "":
                        raw_type = ctx.var_types.get(raw_name, "")
                    if "|" in raw_type:
                        option_side = _rs_var_name(ctx, raw_name)
                if left_is_optional or right_is_optional:
                    # Use is_none()/is_some() for Option<T> comparisons to avoid type annotation issues
                    if rs_op == "==":
                        parts.append(option_side + ".is_none()")
                    else:
                        parts.append(option_side + ".is_some()")
                elif not left_is_optional and not right_is_optional and right_is_none_side:
                    # Check if the type is PyAny enum (object/Any/Obj → PyAny enum)
                    left_is_pyany = left_is_pyany or left_type in ("object", "Any", "Obj") or left_type == ""
                    if left_is_pyany:
                        if rs_op == "==":
                            parts.append("matches!(" + option_side + ", PyAny::None)")
                        else:
                            parts.append("!matches!(" + option_side + ", PyAny::None)")
                    else:
                        # Non-optional, non-Any type compared to None: always not-None
                        parts.append("true" if rs_op == "!=" else "false")
                elif (
                    rs_op in ("==", "!=")
                    and left_rt.startswith("Rc<RefCell<")
                    and right_rt.startswith("Rc<RefCell<")
                ):
                    ptr_eq = "Rc::ptr_eq(&" + _cmp_operand(current_left) + ", &" + _cmp_operand(right) + ")"
                    parts.append("!" + ptr_eq if rs_op == "!=" else ptr_eq)
                else:
                    parts.append("(" + current_left + " " + rs_op + " " + right + ")")
            else:
                if (
                    rs_op in ("==", "!=")
                    and left_rt.startswith("Rc<RefCell<")
                    and right_rt.startswith("Rc<RefCell<")
                ):
                    ptr_eq = "Rc::ptr_eq(&" + _cmp_operand(current_left) + ", &" + _cmp_operand(right) + ")"
                    parts.append("!" + ptr_eq if rs_op == "!=" else ptr_eq)
                elif _types_always_unequal(left_type, right_type):
                    parts.append("false" if rs_op == "==" else "true")
                else:
                    parts.append("(" + _cmp_operand(current_left) + " " + rs_op + " " + _cmp_operand(right) + ")")
        current_left = right
        current_left_node = comparator
    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _emit_isinstance(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit an EAST3 IsInstance node as a Rust type check."""
    val_node = node.get("value")
    if isinstance(val_node, dict) and _str(val_node, "kind") == "Unbox" and isinstance(val_node.get("value"), dict):
        val_node = val_node.get("value")
    expected_node = node.get("expected_type_id")
    if isinstance(val_node, dict) and _str(val_node, "kind") == "Name":
        val_str = _rs_var_name(ctx, _str(val_node, "id"))
    else:
        val_str = _emit_expr(ctx, val_node)
    val_rt = _actual_type_in_context(ctx, val_node) if isinstance(val_node, dict) else ""
    expected_id = _str(expected_node, "id") if isinstance(expected_node, dict) else ""
    if isinstance(expected_node, dict) and _str(expected_node, "kind") == "Tuple":
        checks: list[str] = []
        for elem in _list(expected_node, "elements"):
            if isinstance(elem, dict):
                checks.append(_emit_isinstance(ctx, {
                    "kind": "IsInstance",
                    "value": val_node,
                    "expected_type_id": elem,
                }))
        return "(" + " || ".join(checks) + ")" if len(checks) > 0 else "false"
    if expected_id == "":
        expected_id = _str(node, "expected_type_name")

    # Normalize PYTRA_TID_* constants (used by C++ backend) to type names
    _PYTRA_TID_MAP: dict[str, str] = {}
    _PYTRA_TID_MAP["PYTRA_TID_INT"] = "int64"
    _PYTRA_TID_MAP["PYTRA_TID_FLOAT"] = "float64"
    _PYTRA_TID_MAP["PYTRA_TID_BOOL"] = "bool"
    _PYTRA_TID_MAP["PYTRA_TID_STR"] = "str"
    _PYTRA_TID_MAP["PYTRA_TID_LIST"] = "list"
    _PYTRA_TID_MAP["PYTRA_TID_DICT"] = "dict"
    _PYTRA_TID_MAP["PYTRA_TID_SET"] = "set"
    _PYTRA_TID_MAP["PYTRA_TID_NONE"] = "None"
    _PYTRA_TID_MAP["PYTRA_TID_BYTES"] = "bytes"
    _PYTRA_TID_MAP["PYTRA_TID_TUPLE"] = "tuple"
    if expected_id in _PYTRA_TID_MAP:
        expected_id = _PYTRA_TID_MAP[expected_id]

    val_rs = _rs_type_for_context(ctx, val_rt) if val_rt != "" else ""
    # Union types (A | B) → Box<dyn Any>; object/Any/Obj/JsonVal or PyAny-lowered union → PyAny enum
    is_union_val = "|" in val_rt
    is_pyany_val = (val_rt in ("object", "Any", "Obj", "JsonVal") and not is_union_val) or val_rs == "PyAny"
    is_boxany_val = val_rt in ("unknown",) or is_union_val or val_rt == ""
    is_any_val = is_pyany_val or is_boxany_val

    if is_any_val:
        if is_pyany_val:
            # val_rt is object/Any/Obj → PyAny enum → use matches! or type-id check
            _ISINSTANCE_PYANY: dict[str, str] = {}
            _ISINSTANCE_PYANY["int64"] = "PyAny::Int(_)"
            _ISINSTANCE_PYANY["int"] = "PyAny::Int(_)"
            _ISINSTANCE_PYANY["float64"] = "PyAny::Float(_)"
            _ISINSTANCE_PYANY["float"] = "PyAny::Float(_)"
            _ISINSTANCE_PYANY["bool"] = "PyAny::Bool(_)"
            _ISINSTANCE_PYANY["str"] = "PyAny::Str(_)"
            _ISINSTANCE_PYANY["dict"] = "PyAny::Dict(_)"
            _ISINSTANCE_PYANY["list"] = "PyAny::List(_)"
            _ISINSTANCE_PYANY["None"] = "PyAny::None"
            pyany_pattern = _ISINSTANCE_PYANY.get(expected_id, "")
            if pyany_pattern != "":
                return "matches!(" + val_str + ", " + pyany_pattern + ")"
            # User-defined class: encoded as PyAny::TypeId(dense_tid)
            if expected_id in ctx.class_names:
                candidates = [
                    class_name
                    for class_name in sorted(ctx.class_names)
                    if _inherits_from_class(ctx, class_name, expected_id)
                ]
                tids = [_class_type_id_expr(ctx, class_name) for class_name in candidates]
                tids = [tid for tid in tids if tid != "8_i64"]
                if tids:
                    return "(if let PyAny::TypeId(__tid) = &" + val_str + " { matches!(*__tid, " + " | ".join(tids) + ") } else { false })"
            return "false"
        # For Box<dyn Any> (union types) — use downcast_ref
        ref_val = "&" + val_str if not val_str.startswith("&") else val_str
        _ISINSTANCE_DOWNCAST: dict[str, str] = {}
        _ISINSTANCE_DOWNCAST["int64"] = "i64"
        _ISINSTANCE_DOWNCAST["int32"] = "i32"
        _ISINSTANCE_DOWNCAST["int16"] = "i16"
        _ISINSTANCE_DOWNCAST["int8"] = "i8"
        _ISINSTANCE_DOWNCAST["uint64"] = "u64"
        _ISINSTANCE_DOWNCAST["uint32"] = "u32"
        _ISINSTANCE_DOWNCAST["uint16"] = "u16"
        _ISINSTANCE_DOWNCAST["uint8"] = "u8"
        _ISINSTANCE_DOWNCAST["float64"] = "f64"
        _ISINSTANCE_DOWNCAST["float32"] = "f32"
        _ISINSTANCE_DOWNCAST["bool"] = "bool"
        _ISINSTANCE_DOWNCAST["str"] = "String"
        rust_type = _ISINSTANCE_DOWNCAST.get(expected_id, "")
        if rust_type == "":
            # User-defined class or unknown: check via PyRuntimeTypeId downcast
            if expected_id in ctx.class_names:
                candidates = [
                    class_name
                    for class_name in sorted(ctx.class_names)
                    if _inherits_from_class(ctx, class_name, expected_id)
                ]
                checks: list[str] = []
                for candidate in candidates:
                    if candidate in ctx.ref_classes:
                        checks.append("(" + ref_val + ").downcast_ref::<Rc<RefCell<" + candidate + ">>>().is_some()")
                    else:
                        checks.append("(" + ref_val + ").downcast_ref::<Box<" + candidate + ">>().is_some()")
                if checks:
                    return "(" + " || ".join(checks) + ")"
            # Unknown type — fallback to false
            return "false"
        return "(" + ref_val + ").downcast_ref::<" + rust_type + ">().is_some()"

    # Value has a known concrete type — static isinstance always true/false
    # e.g., isinstance(x: int64, int) → true, isinstance(x: list[str], list) → true
    _NUMERIC: dict[str, str] = {}
    _NUMERIC["int"] = "int64"
    _NUMERIC["float"] = "float64"
    mapped_expected = _NUMERIC.get(expected_id, expected_id)
    # Direct match after alias normalization.
    mapped_val = _NUMERIC.get(val_rt, val_rt)
    if mapped_val == mapped_expected:
        return "true"
    if expected_id in ctx.class_names and val_rt in ctx.class_names and _inherits_from_class(ctx, val_rt, expected_id):
        return "true"
    # Generic list/dict/set compatibility: list[str] isa list, etc.
    if mapped_expected in ("list", "dict", "set") and val_rt.startswith(mapped_expected + "["):
        return "true"
    return "false"


def _emit_boolop(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    values = _list(node, "values")
    op = _str(node, "op")
    resolved_type = _str(node, "resolved_type")

    # For bool type, use native &&/||
    if resolved_type == "bool" or resolved_type == "":
        rs_op = "&&" if op == "And" else "||"
        rendered = [_emit_expr(ctx, v) for v in values]
        return "(" + (" " + rs_op + " ").join(rendered) + ")"

    # For value-returning or/and (Python semantics), use py_bool() checks
    # x or y → if x.py_bool() { x.clone() } else { y.clone() }
    # x and y → if x.py_bool() { y.clone() } else { x.clone() }
    rendered = [_emit_expr(ctx, v) for v in values]
    if len(rendered) == 2:
        a = rendered[0]
        b = rendered[1]
        if op == "Or":
            return "{ let __bop_a = " + a + "; if (&__bop_a).py_bool() { __bop_a } else { " + b + " } }"
        else:
            return "{ let __bop_a = " + a + "; if !(&__bop_a).py_bool() { __bop_a } else { " + b + " } }"
    # Multi-value fallback: fold
    if op == "Or":
        rs_op = "||"
    else:
        rs_op = "&&"
    return "(" + (" " + rs_op + " ").join(rendered) + ")"


def _emit_attribute(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    obj_type = _resolved_type_in_context(ctx, obj_node)
    obj_actual_type = _actual_type_in_context(ctx, obj_node)
    obj_id = _str(obj_node, "id") if isinstance(obj_node, dict) else ""
    receiver_value_hint = _str(obj_node, "resolved_storage_hint") if isinstance(obj_node, dict) else ""
    if receiver_value_hint == "" and obj_id != "":
        receiver_value_hint = ctx.var_storage_hints.get(obj_id, "")
    attr = _str(node, "attr")
    if obj_id == "self" and attr in ctx.constructor_field_locals:
        return _rs_constructor_field_name(attr)
    if obj_type == "py_imported_module" or obj_actual_type == "py_imported_module":
        if attr == "environ":
            obj = _emit_expr(ctx, obj_node)
            return obj + ".environ()"
    if (obj_type == "py_completed_process" or obj_actual_type == "py_completed_process") and attr == "returncode":
        obj = _emit_expr(ctx, obj_node)
        return obj + ".borrow().returncode"
    # type(x).__name__ → static class name string when type is known at compile time
    if attr == "__name__" and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Call":
        call_func = obj_node.get("func")
        if isinstance(call_func, dict) and _str(call_func, "id") == "type":
            call_args = _list(obj_node, "args")
            if len(call_args) >= 1:
                arg = call_args[0]
                arg_rt = _str(arg, "resolved_type") if isinstance(arg, dict) else ""
                if arg_rt == "" and isinstance(arg, dict) and _str(arg, "kind") == "Name":
                    arg_rt = ctx.var_types.get(_str(arg, "id"), "")
                if arg_rt in ctx.class_names:
                    return '"' + arg_rt + '".to_string()'
    # Module attribute (e.g. math.pi, env.target) → use just the attr name (resolved to runtime)
    if obj_type == "module" or obj_id in ctx.import_alias_modules:
        module_id = _str(node, "runtime_module_id")
        if module_id == "":
            module_id = ctx.import_alias_modules.get(obj_id, obj_id if obj_type == "module" else "")
        qualified = obj_id + "." + attr if obj_id != "" else ""
        if qualified in ctx.mapping.calls:
            return ctx.mapping.calls[qualified]
        module_qualified = module_id + "." + attr if module_id != "" else ""
        if module_qualified in ctx.mapping.calls:
            return ctx.mapping.calls[module_qualified]
        is_emitted_pytra_module = (
            _is_pytra_module(module_id)
            and not should_skip_module(module_id, ctx.mapping)
            and module_id not in ctx.mapping.non_native_modules
        )
        if ctx.package_mode and _is_package_crate_module(ctx, module_id):
            module_ref = safe_rs_ident(obj_id) if obj_id != "" else _module_id_to_rs_mod_name(module_id)
            return module_ref + "::" + safe_rs_ident(attr)
        if is_emitted_pytra_module:
            return safe_rs_ident(attr)
        runtime_symbol = _str(node, "runtime_symbol") or attr
        resolved_runtime_call = _str(node, "resolved_runtime_call")
        runtime_call = _str(node, "runtime_call")
        resolved: str = _resolve_runtime_symbol_name_rs(runtime_symbol, ctx.mapping, module_id, resolved_runtime_call, runtime_call)
        if resolved != "":
            return resolved
        return safe_rs_ident(attr)
    type_object_of = ""
    if isinstance(obj_node, dict):
        type_object_of = _str(obj_node, "type_object_of")
    if type_object_of != "":
        class_vars: dict[str, str] = {}
        if type_object_of in ctx.class_vars:
            class_vars = ctx.class_vars[type_object_of]
        if attr in class_vars:
            return "unsafe { " + _class_var_static_name(ctx, type_object_of, attr) + " }"
        # Enum/static access from outside → ClassName::MEMBER
        return safe_rs_ident(type_object_of) + "::" + safe_rs_ident(attr)
    obj = _emit_expr(ctx, obj_node)
    receiver_storage_hint = _str(node, "receiver_storage_hint")
    attr_access_kind = _str(node, "attribute_access_kind")
    path_like_types = {obj_type, obj_actual_type, _resolved_type_in_context(ctx, obj_node)}
    obj_rs = _infer_node_rust_type(ctx, obj_node)
    if obj_id != "":
        name_rs = ctx.var_rust_types.get(obj_id, "")
        if name_rs != "":
            obj_rs = name_rs
    if obj_id == "self" and attr == "raw":
        return "self.raw.clone()"
    if attr == "raw" and obj_id != "":
        name_declared_type = ctx.var_types.get(obj_id, "")
        name_rust_type = ctx.var_rust_types.get(obj_id, "")
        if (
            name_rust_type.startswith("Option<Rc<RefCell<")
            or name_declared_type.endswith("|None")
            or name_declared_type.endswith(" | None")
            or obj_id.endswith("_obj")
        ):
            return obj + '.clone().expect("unbox").borrow().raw.clone()'
    if attr == "raw" and (
        obj_rs.startswith("Option<Rc<RefCell<")
        or obj_type.endswith("|None")
        or obj_type.endswith(" | None")
        or obj_actual_type.endswith("|None")
        or obj_actual_type.endswith(" | None")
    ):
        return obj + '.clone().expect("unbox").borrow().raw.clone()'
    if _path_like_types_have(ctx, path_like_types) or _is_path_rust_type(ctx, obj_rs):
        if attr == "parent":
            return obj + ".parent()"
        if attr in ("name", "stem", "suffix"):
            return obj + "." + safe_rs_ident(attr) + "()"
    if obj_rs.startswith("Option<Rc<RefCell<") and obj_rs.endswith(">>"):
        if attr == "raw":
            return obj + '.clone().expect("unbox").borrow().raw.clone()'
        inner_rs = obj_rs[len("Option<Rc<RefCell<"):-2]
        return obj + '.clone().expect("unbox").borrow().' + safe_rs_ident(attr) + ("" if attr == "raw" else ".clone()")
    if obj_rs.startswith("Rc<RefCell<") and obj_rs.endswith(">>"):
        if attr == "raw":
            return obj + ".borrow().raw.clone()"
    if attr == "raw" and obj.endswith('.expect("unbox")'):
        return obj + ".borrow().raw.clone()"
    if obj_rs.startswith("Box<") and obj_rs.endswith(">"):
        inner_rs = obj_rs[len("Box<"):-1]
        if inner_rs != "" and inner_rs != "dyn std::any::Any":
            attr_rs = _infer_node_rust_type(ctx, node) or _rs_type_for_context(ctx, _str(node, "resolved_type"))
            if attr_rs in ("bool", "i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32"):
                return obj + "." + safe_rs_ident(attr)
            return obj + "." + safe_rs_ident(attr) + ".clone()"
    if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        name_rs = ctx.var_rust_types.get(_str(obj_node, "id"), "")
        inner_rs = name_rs[len("Rc<RefCell<"):-2] if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>") else ""
        is_path_ref = _is_path_type_name(ctx, _resolved_type_in_context(ctx, obj_node)) or _is_path_type_name(ctx, inner_rs) or _is_path_rust_type(ctx, name_rs)
        if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>") and not (is_path_ref and attr in ("parent", "name", "stem", "suffix")):
            property_methods: set[str] = set()
            if inner_rs in ctx.class_property_methods:
                property_methods = ctx.class_property_methods[inner_rs]
            if attr in property_methods:
                return obj + ".borrow()." + safe_rs_ident(attr) + "()"
            attr_rs = _infer_node_rust_type(ctx, node) or _rs_type_for_context(ctx, _str(node, "resolved_type"))
            if attr_rs in ("bool", "i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32"):
                return obj + ".borrow()." + safe_rs_ident(attr)
            return obj + ".borrow()." + safe_rs_ident(attr) + ".clone()"
    if (
        attr_access_kind == "property_getter"
        and receiver_storage_hint == "ref"
        and not (isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name" and _str(obj_node, "id") == "self")
    ):
        return obj + ".borrow()." + safe_rs_ident(attr) + "()"
    # If attr is a @property method, call it with ()
    # Check both the current class context and the obj's type class
    obj_class = obj_type if obj_type in ctx.class_names else ""
    actual_class = obj_actual_type if obj_actual_type in ctx.class_names else ""
    property_candidates: list[str] = []
    for cls in [ctx.current_class, actual_class, obj_class]:
        if cls != "" and cls not in property_candidates:
            property_candidates.append(cls)
    if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        name_rs = ctx.var_rust_types.get(_str(obj_node, "id"), "")
        if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>"):
            cls = name_rs[len("Rc<RefCell<"):-2]
            if cls not in property_candidates:
                property_candidates.append(cls)
    for candidate_type in [obj_actual_type, obj_type, _str(node, "resolved_type")]:
        candidate_rs = _rs_type_for_context(ctx, candidate_type) if candidate_type != "" else ""
        if candidate_rs.startswith("Rc<RefCell<") and candidate_rs.endswith(">>"):
            cls = candidate_rs[len("Rc<RefCell<"):-2]
            if cls not in property_candidates:
                property_candidates.append(cls)
    for cls in property_candidates:
        property_methods2: set[str] = set()
        if cls in ctx.class_property_methods:
            property_methods2 = ctx.class_property_methods[cls]
        if cls != "" and attr in property_methods2:
            if cls in ctx.ref_classes and not (isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name" and _str(obj_node, "id") == "self"):
                return obj + ".borrow()." + safe_rs_ident(attr) + "()"
            return obj + "." + safe_rs_ident(attr) + "()"
    ref_attr_class = actual_class if actual_class in ctx.ref_classes else obj_class
    if ref_attr_class == "":
        for candidate in [actual_class, obj_class, obj_type, obj_actual_type]:
            if candidate != "" and ctx.imported_symbol_storage_hints.get(candidate) == "ref":
                ref_attr_class = candidate
                break
    if ref_attr_class not in ctx.ref_classes:
        if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
            name_rs = ctx.var_rust_types.get(_str(obj_node, "id"), "")
            if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>"):
                ref_attr_class = name_rs[len("Rc<RefCell<"):-2]
        for candidate_type in [obj_actual_type, obj_type, _str(node, "resolved_type")]:
            candidate_rs = _rs_type_for_context(ctx, candidate_type) if candidate_type != "" else ""
            if candidate_rs.startswith("Rc<RefCell<") and candidate_rs.endswith(">>"):
                ref_attr_class = candidate_rs[len("Rc<RefCell<"):-2]
                break
        if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Unbox":
            unboxed_rt = _str(obj_node, "resolved_type")
            if unboxed_rt in ctx.ref_classes:
                ref_attr_class = unboxed_rt
        for candidate in [obj_actual_type, obj_type]:
            if candidate.endswith(" | None"):
                inner_candidate = candidate[:-7].strip()
                if inner_candidate in ctx.ref_classes:
                    ref_attr_class = inner_candidate
                    break
    ref_attr_is_ref = receiver_storage_hint == "ref" or receiver_value_hint == "ref" or ref_attr_class in ctx.ref_classes
    obj_rs_late = _infer_node_rust_type(ctx, obj_node)
    if obj_rs_late.startswith("Box<") and obj_rs_late.endswith(">") and ref_attr_class not in ctx.ref_classes:
        ref_attr_is_ref = False
    if not ref_attr_is_ref and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        name_rs = ctx.var_rust_types.get(_str(obj_node, "id"), "")
        ref_attr_is_ref = name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>")
    if ref_attr_is_ref and ref_attr_class not in ctx.parent_class_names and not (isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name" and _str(obj_node, "id") == "self"):
        return obj + ".borrow()." + safe_rs_ident(attr) + ".clone()"
    if (
        isinstance(obj_node, dict)
        and _str(obj_node, "kind") == "Unbox"
        and _str(obj_node, "resolved_type") != ""
        and _starts_uppercase(_str(obj_node, "resolved_type"))
        and _str(obj_node, "resolved_type") not in ctx.class_names
    ):
        return obj + ".borrow()." + safe_rs_ident(attr) + ".clone()"
    if obj_id == "self":
        attr_rs = _rs_type_for_context(ctx, _str(node, "resolved_type"))
        if (
            attr_rs in ("String", "PyAny")
            or attr_rs.startswith("HashMap<")
            or attr_rs.startswith("HashSet<")
            or attr_rs.startswith("PyList<")
            or attr_rs.startswith("VecDeque<")
            or attr_rs.startswith("Rc<RefCell<")
        ):
            return obj + "." + safe_rs_ident(attr) + ".clone()"
    if _path_like_types_have(ctx, path_like_types) or _is_path_rust_type(ctx, obj_rs):
        if attr == "parent":
            return obj + ".parent()"
        if attr in ("name", "stem", "suffix"):
            return obj + "." + safe_rs_ident(attr) + "()"
    return obj + "." + safe_rs_ident(attr)


def _emit_attr_receiver_raw(ctx: RsEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict) or _str(node, "kind") != "Attribute":
        return _emit_expr(ctx, node)
    owner = node.get("value")
    if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
        return "self." + safe_rs_ident(_str(node, "attr"))
    return _emit_expr(ctx, node)


def _expr_to_pyany(expr: str, inner_type: str) -> str:
    """Wrap a rendered expression in the appropriate PyAny variant."""
    if expr.startswith("PyAny::"):
        return expr
    if inner_type in ("int64", "int"):
        return "PyAny::Int(" + expr + ")"
    if inner_type in ("float64", "float32", "float"):
        return "PyAny::Float(" + expr + " as f64)"
    if inner_type == "bool":
        return "PyAny::Bool(" + expr + ")"
    if inner_type == "str":
        return "PyAny::Str(" + expr + ")"
    if inner_type.startswith("list[") or inner_type == "list":
        elem_type = ""
        if inner_type.startswith("list[") and inner_type.endswith("]"):
            elem_type = inner_type[5:-1].strip()
        if elem_type in ("", "Any", "object", "Obj", "JsonVal"):
            return "PyAny::List(" + expr + ".iter_snapshot().into_iter().collect())"
        boxed_elem = _expr_to_pyany("__v", elem_type)
        return (
            "PyAny::List("
            + expr
            + ".iter_snapshot().into_iter().map(|__v| "
            + boxed_elem
            + ").collect())"
        )
    if inner_type.startswith("dict[") or inner_type == "dict":
        value_type = "Any"
        if inner_type.startswith("dict[") and inner_type.endswith("]"):
            parts = _split_generic_args(inner_type[5:-1])
            if len(parts) == 2:
                value_type = parts[1].strip()
        boxed_value = _expr_to_pyany("__v", value_type)
        return "PyAny::Dict(" + expr + ".into_iter().map(|(__k, __v)| (__k, " + boxed_value + ")).collect::<BTreeMap<_, _>>())"
    if inner_type == "None" or expr == "None":
        return "PyAny::None"
    # Fallback: for unknown types or already-wrapped exprs
    return expr


def _emit_dict_as_btree_pyany(ctx: "RsEmitContext", node: dict[str, JsonVal]) -> str:
    """Emit a Dict EAST3 node as PyAny::Dict(BTreeMap::from([...]))."""
    entries = _list(node, "entries")
    if entries:
        keys: list[JsonVal] = []
        values: list[JsonVal] = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            keys.append(_json_get(e, "key"))
            values.append(_json_get(e, "value"))
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
    if len(keys) == 0:
        return "PyAny::Dict(BTreeMap::new())"
    pairs: list[str] = []
    for i, key in enumerate(keys):
        k = _emit_expr(ctx, key)
        val_node = key
        has_val = False
        if i < len(values):
            val_node = values[i]
            has_val = True
        val_rt = ""
        val_kind = ""
        if has_val and isinstance(val_node, dict):
            val_rt = _str(val_node, "resolved_type")
            val_kind = _str(val_node, "kind")
        if val_kind == "Dict" and isinstance(val_node, dict):
            v = _emit_dict_as_btree_pyany(ctx, val_node)
        else:
            v = _emit_expr(ctx, val_node) if has_val else "PyAny::None"
            v = _expr_to_pyany(v, val_rt)
        pairs.append("(" + k + ", " + v + ")")
    return "PyAny::Dict(BTreeMap::from([" + ", ".join(pairs) + "]))"


def _emit_list_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        elem_type = _rs_type_for_context(ctx, resolved_type[5:-1])
    need_box_elem = elem_type == "Box<dyn std::any::Any>"
    need_pyany_elem = elem_type == "PyAny"
    need_option_elem = elem_type.startswith("Option<")
    def _clone_literal_name(e_node: JsonVal, e_str: str) -> str:
        if isinstance(e_node, dict) and _str(e_node, "kind") == "Name":
            e_rt = _infer_node_rust_type(ctx, e_node)
            if e_rt != "" and not _rs_is_copy_type(e_rt) and not e_str.endswith(".clone()"):
                return e_str + ".clone()"
        return e_str

    rendered_elem_nodes: list[JsonVal] = []
    rendered_elem_values: list[str] = []
    for e in elements:
        rendered_elem_nodes.append(e)
        rendered_elem_values.append(_clone_literal_name(e, _emit_expr(ctx, e)))
    if need_box_elem:
        rendered_elems: list[str] = []
        for e_str in rendered_elem_values:
            if e_str.startswith("Box::new("):
                rendered_elems.append(e_str)
            else:
                rendered_elems.append("Box::new(" + e_str + ") as Box<dyn std::any::Any>")
    elif need_pyany_elem:
        rendered_elems = []
        for index, e_str in enumerate(rendered_elem_values):
            e_node = rendered_elem_nodes[index]
            e_rt = ""
            if isinstance(e_node, dict):
                e_rt = _str(e_node, "resolved_type")
            rendered_elems.append(_expr_to_pyany(e_str, e_rt))
    elif need_option_elem:
        rendered_elems = []
        for index, e_str in enumerate(rendered_elem_values):
            if e_str == "None":
                rendered_elems.append(e_str)
            else:
                e_node = rendered_elem_nodes[index]
                e_rt = ""
                if isinstance(e_node, dict):
                    e_rt = _str(e_node, "resolved_type")
                if "None" not in e_rt and not e_rt.startswith("Option"):
                    rendered_elems.append("Some(" + e_str + ")")
                else:
                    rendered_elems.append(e_str)
    else:
        rendered_elems = []
        for e_str in rendered_elem_values:
            rendered_elems.append(e_str)
    if len(rendered_elems) == 0:
        if elem_type != "":
            return "PyList::<" + elem_type + ">::new()"
        return "PyList::new()"
    elems_str = ", ".join(rendered_elems)
    if elem_type != "":
        return "PyList::<" + elem_type + ">::from_vec(vec![" + elems_str + "])"
    return "PyList::from_vec(vec![" + elems_str + "])"


def _emit_dict_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    # EAST3 uses "entries" (list of {key, value} dicts); fall back to separate keys/values
    entries = _list(node, "entries")
    keys: list[JsonVal]
    values: list[JsonVal]
    if entries:
        keys = []
        values = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            keys.append(_json_get(e, "key"))
            values.append(_json_get(e, "value"))
    else:
        keys = _list(node, "keys")
        values = _list(node, "values")
    resolved_type = _str(node, "resolved_type")
    k_type = "String"
    v_type = "PyAny"
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            k_type = _rs_type_for_context(ctx, parts[0])
            v_type = _rs_type_for_context(ctx, parts[1])
    if len(keys) == 0:
        return "HashMap::<" + k_type + ", " + v_type + ">::new()"
    need_box_v = v_type == "Box<dyn std::any::Any>"
    need_pyany_v = v_type == "PyAny"
    need_option_v = v_type.startswith("Option<")
    pairs: list[str] = []
    for i, key in enumerate(keys):
        k = _emit_expr(ctx, key)
        val_node = key
        has_val = False
        if i < len(values):
            val_node = values[i]
            has_val = True
        v = _emit_expr(ctx, val_node) if has_val else "Default::default()"
        if need_box_v and not v.startswith("Box::new("):
            v = "Box::new(" + v + ") as Box<dyn std::any::Any>"
        elif need_pyany_v:
            val_rt = ""
            val_kind = ""
            if isinstance(val_node, dict):
                val_rt = _str(val_node, "resolved_type")
                val_kind = _str(val_node, "kind")
            if val_kind == "Dict" and isinstance(val_node, dict):
                v = _emit_dict_as_btree_pyany(ctx, val_node)
            else:
                v = _expr_to_pyany(v, val_rt)
        elif need_option_v and v != "None":
            # Wrap non-None values with Some(...) unless already Optional type
            val_rt = ""
            if isinstance(val_node, dict):
                val_rt = _str(val_node, "resolved_type")
            if "None" not in val_rt and not val_rt.startswith("Option"):
                v = "Some(" + v + ")"
        pairs.append("(" + k + ", " + v + ")")
    return "HashMap::<" + k_type + ", " + v_type + ">::from([" + ", ".join(pairs) + "])"


def _emit_set_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    resolved_type = _str(node, "resolved_type")
    elem_type = "String"
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        elem_type = rs_type(resolved_type[4:-1])
    rendered_elems = [_emit_expr(ctx, e) for e in elements]
    if len(rendered_elems) == 0:
        return "HashSet::<" + elem_type + ">::new()"
    return "HashSet::<" + elem_type + ">::from([" + ", ".join(rendered_elems) + "])"


def _emit_tuple_literal(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    elements = _list(node, "elements")
    rendered: list[str] = []
    for elem in elements:
        elem_expr = _emit_expr(ctx, elem)
        if isinstance(elem, dict) and _str(elem, "kind") == "Name":
            elem_rs = _infer_node_rust_type(ctx, elem)
            if elem_rs != "" and not _rs_is_copy_type(elem_rs) and not elem_expr.endswith(".clone()"):
                elem_expr = elem_expr + ".clone()"
        rendered.append(elem_expr)
    if len(rendered) == 0:
        return "()"
    # If the tuple resolves to a PyList type (homogeneous), emit PyList::from_vec(vec![...])
    resolved_type = _str(node, "resolved_type")
    if resolved_type.startswith("tuple["):
        rt = _rs_type_for_context(ctx, resolved_type)
        if rt.startswith("PyList<"):
            # Use turbofish syntax: PyList::<T>::from_vec(...)
            inner_t = rt[7:-1]  # strip "PyList<" and ">"
            return "PyList::<" + inner_t + ">::from_vec(vec![" + ", ".join(rendered) + "])"
    if len(rendered) == 1:
        return "(" + rendered[0] + ",)"
    return "(" + ", ".join(rendered) + ")"


def _emit_subscript(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    obj_node = node.get("value")
    obj = _emit_expr(ctx, obj_node)
    slice_node = node.get("slice")
    obj_type = _resolved_type_in_context(ctx, obj_node)
    if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        actual_obj_type = ctx.var_types.get(_str(obj_node, "id"), "")
        if actual_obj_type.startswith("dict["):
            obj_type = actual_obj_type
        elif _rs_type_for_context(ctx, actual_obj_type) == "PyAny" and (obj_type.startswith("dict[") or obj_type.startswith("list[")):
            pass
        elif "|" in actual_obj_type:
            if isinstance(slice_node, dict) and _str(slice_node, "resolved_type") in ("str", "string"):
                for option in _split_generic_args(actual_obj_type.replace("|", ",")):
                    if option.strip().startswith("dict["):
                        obj_type = option.strip()
                        break
            else:
                for option in _split_generic_args(actual_obj_type.replace("|", ",")):
                    if option.strip().startswith("list["):
                        obj_type = option.strip()
                        break
    if obj_type in ("", "unknown") and isinstance(obj_node, dict) and _str(obj_node, "kind") == "Attribute":
        attr_owner = obj_node.get("value")
        type_object_of = _str(attr_owner, "type_object_of") if isinstance(attr_owner, dict) else ""
        attr_name = _str(obj_node, "attr")
        class_vars: dict[str, str] = {}
        if type_object_of in ctx.class_vars:
            class_vars = ctx.class_vars[type_object_of]
        if type_object_of != "" and attr_name in class_vars:
            obj_type = class_vars[attr_name]

    # Handle Slice (a[b:c]) — range slicing
    if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Slice":
        lower = slice_node.get("lower")
        upper = slice_node.get("upper")
        lo = _emit_expr(ctx, lower) if lower is not None else ""
        hi_raw = _emit_expr(ctx, upper) if upper is not None else ""
        obj_rs = _rs_type_for_context(ctx, obj_type) if obj_type != "" else _infer_node_rust_type(ctx, obj_node)
        ref_obj = "&" + obj if not obj.startswith("&") else obj
        lo_expr = "None" if lo == "" else "Some((" + lo + ") as i64)"
        hi_expr = "None" if hi_raw == "" else "Some((" + hi_raw + ") as i64)"
        if obj_type.startswith("list[") or obj_rs.startswith("PyList<"):
            return "py_slice(" + ref_obj + ", " + lo_expr + ", " + hi_expr + ")"
        if obj_type == "str" or obj_rs == "String":
            return "py_slice(" + ref_obj + ", " + lo_expr + ", " + hi_expr + ")"
        # Default slice
        lo_raw = "0" if lo == "" else lo
        hi_fallback = "usize::MAX" if hi_raw == "" else hi_raw
        return obj + "[(" + lo_raw + " as usize)..(" + hi_fallback + " as usize)]"

    idx = _emit_expr(ctx, slice_node)
    if isinstance(obj_node, dict) and _str(obj_node, "kind") == "Name":
        actual_obj_type = ctx.var_types.get(_str(obj_node, "id"), "")
        if _rs_type_for_context(ctx, actual_obj_type) == "PyAny":
            if obj_type.startswith("list[") and obj_type.endswith("]"):
                elem_rs = _rs_type_for_context(ctx, obj_type[5:-1].strip())
                obj = "py_any_as_list_typed::<" + elem_rs + ">(" + obj + ".clone())"
            elif obj_type.startswith("dict[") and obj_type.endswith("]"):
                parts = _split_generic_args(obj_type[5:-1])
                value_rs = _rs_type_for_context(ctx, parts[1].strip()) if len(parts) == 2 else "PyAny"
                obj = "py_any_as_hashmap_typed::<" + value_rs + ">(" + obj + ".clone())"
    # Tuple indexing (both "tuple" and "tuple[...]")
    if obj_type == "tuple" or obj_type.startswith("tuple["):
        if obj_type == "tuple" and isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
            val = slice_node.get("value")
            if isinstance(val, int) and val >= 0:
                return obj + "." + str(val)
        tuple_rs = _rs_type_for_context(ctx, obj_type)
        if tuple_rs.startswith("PyList<"):
            # Homogeneous tuple as PyList<T> → .get() like list
            return obj + ".get(" + idx + ")"
        if tuple_rs.startswith("Vec<"):
            return obj + "[" + idx + " as usize].clone()"
        # Heterogeneous tuple as Rust tuple → .N notation
        if isinstance(slice_node, dict) and _str(slice_node, "kind") == "Constant":
            val = slice_node.get("value")
            if isinstance(val, int) and val >= 0:
                return obj + "." + str(val)
        # Non-literal index into tuple: fallback to usize cast
        return obj + "[" + idx + " as usize]"
    if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
        return obj + ".get(" + idx + ")"
    if obj_type.startswith("dict[") or obj_type == "dict":
        subscript_expr = obj + "[&" + idx + "]"
        # For dict[K, PyAny] (non-Copy value), subscript moves value — need .clone()
        if obj_type.startswith("dict[") and obj_type.endswith("]"):
            _inner = obj_type[5:-1]
            _parts = _split_generic_args(_inner)
            if len(_parts) == 2 and _rs_type_for_context(ctx, _parts[1].strip()) == "String":
                return subscript_expr + ".clone()"
            if len(_parts) == 2 and (rs_type(_parts[1]) == "PyAny" or "|" in _parts[1]):
                subscript_expr = subscript_expr + ".clone()"
        return subscript_expr
    # String indexing: s[i] → py_str_get_at(&s, i) returning String
    if obj_type == "str":
        ref_obj = "&" + obj if not obj.startswith("&") else obj
        node_rt = _str(node, "resolved_type")
        if node_rt == "byte" or node_rt == "int64":
            return "py_str_char_at(" + ref_obj + ", " + idx + ")"
        return "py_str_get_at(" + ref_obj + ", " + idx + ")"
    # Default: use indexing
    return obj + "[" + idx + " as usize]"


def _emit_bool_test(ctx: RsEmitContext, test_node: JsonVal) -> str:
    """Emit a test expression as a boolean condition (handles list/bytes truthiness)."""
    expr_str = _emit_expr(ctx, test_node)
    if isinstance(test_node, dict):
        rt = _str(test_node, "resolved_type")
        if rt == "bool":
            return expr_str
        if rt in ("bytes", "bytearray") or rt.startswith("list[") or rt == "list":
            return "!" + expr_str + ".is_empty()"
        if rt in (
            "int", "int64", "int32", "int16", "int8",
            "uint64", "uint32", "uint16", "uint8",
            "float", "float64", "float32",
            "str", "dict", "set", "Any", "Obj", "object", "JsonVal",
        ) or rt.startswith("dict[") or rt.startswith("set["):
            return "py_bool(&(" + expr_str + "))"
    return expr_str


def _emit_ifexp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    test_node = node.get("test")
    test = _emit_bool_test(ctx, test_node)
    body_node = node.get("body")
    orelse_node = node.get("orelse")
    body = _emit_expr(ctx, body_node)
    orelse = _emit_expr(ctx, orelse_node)
    # Optional[T] if-else: wrap T branch with Some(...)
    rt = _str(node, "resolved_type")
    if rt == "str":
        body = _coerce_call_arg_to_expected(ctx, body_node, body, "str") if isinstance(body_node, dict) else body
        orelse = _coerce_call_arg_to_expected(ctx, orelse_node, orelse, "str") if isinstance(orelse_node, dict) else orelse
        body = body.replace(".clone().unwrap_or(PyAny::None).clone()", ".clone().unwrap_or_default()")
        body = body.replace(".unwrap_or(PyAny::None).clone()", ".unwrap_or_default()")
        orelse = orelse.replace(".clone().unwrap_or(PyAny::None).clone()", ".clone().unwrap_or_default()")
        orelse = orelse.replace(".unwrap_or(PyAny::None).clone()", ".unwrap_or_default()")
    is_optional = rt.endswith(" | None") or rt.endswith("|None")
    if is_optional:
        def _is_none_node(n: JsonVal) -> bool:
            return isinstance(n, dict) and _str(n, "kind") == "Constant" and n.get("value") is None
        if _is_none_node(orelse_node) and not _is_none_node(body_node):
            body = "Some(" + body + ")"
        elif _is_none_node(body_node) and not _is_none_node(orelse_node):
            orelse = "Some(" + orelse + ")"
    elif _rs_type_for_context(ctx, rt).startswith("PyList<"):
        inner_rs = _rs_type_for_context(ctx, rt)[len("PyList<"):-1]
        if isinstance(body_node, dict) and _str(body_node, "kind") == "List" and len(_list(body_node, "elements")) == 0:
            body = "PyList::<" + inner_rs + ">::new()"
        if isinstance(orelse_node, dict) and _str(orelse_node, "kind") == "List" and len(_list(orelse_node, "elements")) == 0:
            orelse = "PyList::<" + inner_rs + ">::new()"
    # Union type (A | B, not Optional): box both branches
    elif "|" in rt:
        union_parts: list[str] = []
        for part_raw in rt.split("|"):
            union_parts.append(part_raw.strip())
        list_parts: list[str] = []
        for part in union_parts:
            if part.startswith("list[") or part == "list":
                list_parts.append(part)
        if len(list_parts) == len(union_parts) and len(list_parts) > 0:
            concrete = list_parts[0]
            for part in list_parts:
                if part.startswith("list[") and part != "list[unknown]":
                    concrete = part
                    break
            if isinstance(body_node, dict):
                body = _coerce_call_arg_to_expected(ctx, body_node, body, concrete)
            if isinstance(orelse_node, dict):
                orelse = _coerce_call_arg_to_expected(ctx, orelse_node, orelse, concrete)
        else:
            body = "Box::new(" + body + ") as Box<dyn std::any::Any>"
            orelse = "Box::new(" + orelse + ") as Box<dyn std::any::Any>"
    return "(if " + test + " { " + body + " } else { " + orelse + " })"


def _emit_lambda(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    raw_arg_order = _list(node, "arg_order")
    arg_order: list[str] = []
    for raw_arg in raw_arg_order:
        if isinstance(raw_arg, str):
            arg_order.append(raw_arg)
    arg_types = _dict(node, "arg_types")
    return_type = _str(node, "return_type")
    body = node.get("body")
    params: list[str] = []
    for arg in arg_order:
        if isinstance(arg, str):
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                params.append(safe_rs_ident(arg) + ": " + _rs_type_for_context(ctx, arg_type))
            else:
                params.append(safe_rs_ident(arg))
    params_str = ", ".join(params)
    type_params = _collect_signature_type_params(ctx, arg_types, return_type)
    generic_suffix = "<" + ", ".join(type_params) + ">" if type_params else ""
    body_str = _emit_expr(ctx, body)
    return "|" + params_str + "| " + body_str


def _box_target_is_any(node: dict[str, JsonVal]) -> bool:
    """Return True if the Box node's bridge_lane_v1 target dynamic_name is 'Any' or 'Obj'."""
    lane = node.get("bridge_lane_v1")
    if not isinstance(lane, dict):
        return False
    target = lane.get("target")
    if not isinstance(target, dict):
        return False
    dname = _as_str(target.get("dynamic_name"))
    return dname == "Any" or dname == "Obj"


def _emit_box(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit a Box node (boxing a value for dynamic dispatch)."""
    inner = node.get("value")
    outer_rt = _str(node, "resolved_type")
    # All of object/Any/Obj → PyAny enum
    target_is_pyany = outer_rt in ("object", "Any", "Obj") or _rs_type_for_context(ctx, outer_rt) == "PyAny"
    # If inner is a None constant, emit PyAny::None
    if isinstance(inner, dict) and _str(inner, "kind") == "Constant" and inner.get("value") is None:
        if target_is_pyany:
            return "PyAny::None"
        return "Box::new(()) as Box<dyn std::any::Any>"
    # If the Box has a more general resolved_type, use it for container literals
    if isinstance(inner, dict) and outer_rt != "" and outer_rt != _str(inner, "resolved_type"):
        inner_kind = _str(inner, "kind")
        if inner_kind == "Dict":
            if target_is_pyany:
                # Box<object/Any/Obj>(dict) → PyAny::Dict(BTreeMap::from([...]))
                return _emit_dict_as_btree_pyany(ctx, inner)
            # Temporarily override inner resolved_type for dict literal
            inner_copy = dict(inner)
            inner_copy["resolved_type"] = outer_rt
            return _emit_dict_literal(ctx, inner_copy)
        if inner_kind == "List":
            # Temporarily override inner resolved_type for list literal (e.g. list[Any])
            inner_copy = dict(inner)
            inner_copy["resolved_type"] = outer_rt
            return _emit_list_literal(ctx, inner_copy)
        # PyAny enum wrapping for object/Any/Obj outer types
        if target_is_pyany:
            inner_rt = _str(inner, "resolved_type")
            rendered_inner = _emit_expr(ctx, inner)
            wrapped = _expr_to_pyany(rendered_inner, inner_rt)
            if wrapped != rendered_inner:
                return wrapped
            if inner_rt in ctx.class_names and inner_rt not in ctx.enum_bases:
                # User class → encode dense type ID directly for isinstance checks
                return "PyAny::TypeId(" + _class_type_id_expr(ctx, inner_rt) + ")"
            # Fallback: for unknown/complex types, return as-is
            return rendered_inner
    rendered = _emit_expr(ctx, inner)
    return rendered


def _emit_call(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    func = node.get("func")
    args = _list(node, "args")
    keywords = _list(node, "keywords")

    # Check for runtime_call mapping
    runtime_call = _str(node, "runtime_call")
    adapter_kind = _str(node, "runtime_call_adapter_kind")
    builtin_name_field = _str(node, "builtin_name")

    # Determine if this is a method call (Attribute func)
    func_is_method = isinstance(func, dict) and _str(func, "kind") == "Attribute"

    # Handle zip(a, b) before runtime_call resolution: zip produces list of tuples
    if runtime_call in ("zip", "") and not func_is_method and len(args) == 2:
        fn_id = _str(func, "id") if isinstance(func, dict) else ""
        if fn_id == "zip" or runtime_call == "zip":
            a0 = _emit_call_arg(ctx, args[0])
            a1 = _emit_call_arg(ctx, args[1])
            t0 = _str(args[0], "resolved_type") if isinstance(args[0], dict) else ""
            t1 = _str(args[1], "resolved_type") if isinstance(args[1], dict) else ""
            elem0 = rs_type(t0[5:-1]) if t0.startswith("list[") and t0.endswith("]") else "f64"
            elem1 = rs_type(t1[5:-1]) if t1.startswith("list[") and t1.endswith("]") else "f64"
            return ("PyList::<(" + elem0 + ", " + elem1 + ")>::from_vec("
                    + a0 + ".iter_snapshot().into_iter().zip(" + a1 + ".iter_snapshot().into_iter()).collect())")

    if (
        not func_is_method
        and isinstance(func, dict)
        and (
            _str(func, "id") == "list"
            or runtime_call == "list"
            or builtin_name_field == "list"
        )
    ):
        if len(args) == 0:
            return "PyList::<PyAny>::new()"
        if len(args) == 1 and isinstance(args[0], dict):
            arg_expr = _emit_call_arg(ctx, args[0])
            arg_rs = _infer_node_rust_type(ctx, args[0])
            if not arg_rs.startswith("PyList<"):
                arg_type = _actual_type_in_context(ctx, args[0])
                arg_rs = _rs_type_for_context(ctx, arg_type) if arg_type != "" else arg_rs
            if arg_rs.startswith("PyList<"):
                return arg_expr + ".clone()"
            if arg_rs == "PyAny":
                return "py_any_as_list(" + arg_expr + ".clone())"
            if not arg_expr.startswith("&"):
                arg_expr = "&(" + arg_expr + ")"
            return "py_list(" + arg_expr + ")"

    if runtime_call != "":
        mapped = resolve_runtime_call(runtime_call, builtin_name_field, adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__"):
            # Handle special mappings
            if mapped == "__CAST__":
                if len(args) >= 1:
                    return _emit_expr(ctx, args[0])
                return ""
            # For method calls, delegate to _emit_method_call so the receiver is included
            if func_is_method:
                return _emit_method_call(ctx, func, args, keywords, node)
            return _emit_runtime_call(ctx, mapped, func, args, keywords, node)

    # Check for lowered_kind
    lowered_kind = _str(node, "lowered_kind")
    if lowered_kind == "BuiltinCall":
        builtin_name = _str(node, "builtin_name")
        runtime_sym = _str(node, "runtime_symbol")
        # Handle sum() specially — emit as .iter_snapshot().into_iter().sum()
        if builtin_name == "sum" and len(args) == 1:
            arg_expr = _emit_call_arg(ctx, args[0])
            ret_type = _str(node, "resolved_type")
            rs_ret = rs_type(ret_type) if ret_type not in ("", "unknown") else "f64"
            return arg_expr + ".iter_snapshot().into_iter().sum::<" + rs_ret + ">()"
        mapped2 = resolve_runtime_call(runtime_sym, builtin_name, adapter_kind, ctx.mapping)
        if mapped2 != "" and not mapped2.startswith("__"):
            return _emit_runtime_call(ctx, mapped2, func, args, keywords, node)
        # If mapped to a __ placeholder, fall through to Attribute/func handling below
        # (method calls like list.append are handled in _emit_method_call)
        if mapped2 == "" or mapped2.startswith("__"):
            pass  # fall through
        else:
            call_name = mapped2
            rendered_args = [_emit_expr(ctx, a) for a in args]
            for kw in keywords:
                if isinstance(kw, dict):
                    kw_val = kw.get("value")
                    rendered_args.append(_emit_expr(ctx, kw_val))
            return call_name + "(" + ", ".join(rendered_args) + ")"

    if not isinstance(func, dict):
        rendered_args = [_emit_expr(ctx, a) for a in args]
        return "unknown_func(" + ", ".join(rendered_args) + ")"

    func_kind = _str(func, "kind")

    # Method call: obj.method(args)
    if func_kind == "Attribute":
        owner_node = func.get("value")
        if (
            _str(func, "attr") == "JsonValue"
            and isinstance(owner_node, dict)
            and (
                _str(owner_node, "runtime_module_id") == "pytra.std.json"
                or ctx.import_alias_modules.get(_str(owner_node, "id"), "") == "pytra.std.json"
            )
            and len(args) == 1
        ):
            return "Rc::new(RefCell::new(JsonValue::new(" + _emit_call_arg(ctx, args[0]) + ")))"
        return _emit_method_call(ctx, func, args, keywords, node)

    # Direct name call
    func_name = _str(func, "id")
    if func_name == "":
        func_expr = _emit_expr(ctx, func)
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        # Wrap func_expr in parens for IIFEs (lambda/closure expressions called immediately)
        return "(" + func_expr + ")(" + ", ".join(rendered_args) + ")"

    if func_name == "isinstance" and len(args) >= 2:
        expected = ""
        expected_arg = args[1]
        if isinstance(expected_arg, dict):
            if _str(expected_arg, "kind") == "Tuple":
                return _emit_isinstance(ctx, {
                    "kind": "IsInstance",
                    "value": args[0],
                    "expected_type_id": expected_arg,
                })
            expected = _str(expected_arg, "id")
            if expected == "" and _str(expected_arg, "kind") == "Constant":
                raw_expected = expected_arg.get("value")
                expected = raw_expected if isinstance(raw_expected, str) else ""
        if expected in ctx.trait_names:
            val_rt = _actual_type_in_context(ctx, args[0]) if isinstance(args[0], dict) else ""
            return "true" if val_rt in ctx.class_names else "false"
        return _emit_isinstance(ctx, {
            "kind": "IsInstance",
            "value": args[0],
            "expected_type_name": expected,
        })

    if func_name == "cast":
        return _emit_cast_call(ctx, node, args)

    if func_name == "JsonValue" and len(args) == 1:
        return "Rc::new(RefCell::new(JsonValue::new(" + _emit_call_arg(ctx, args[0]) + ")))"

    if func_name in ctx.imported_symbol_modules and not _starts_uppercase(func_name):
        imported_module_id = ctx.imported_symbol_modules.get(func_name, "")
        if imported_module_id.startswith("toolchain.") and not should_skip_module(imported_module_id, ctx.mapping):
            local_sig = ctx.function_signatures.get(func_name)
            call_sig = _call_signature(node, local_sig if isinstance(local_sig, dict) else None)
            rendered_args = [_emit_call_arg(ctx, a) for a in args]
            if len(call_sig) > 0:
                rendered_args = _build_sig_call_args(ctx, args, rendered_args, keywords, call_sig, skip_self=False)
            else:
                for kw in keywords:
                    if isinstance(kw, dict):
                        rendered_args.append(_emit_call_arg(ctx, kw.get("value")))
            return safe_rs_ident(func_name) + "(" + ", ".join(rendered_args) + ")"

    if func_name == "id" and len(args) == 1:
        arg_expr = _emit_call_arg(ctx, args[0])
        arg_type = _actual_type_in_context(ctx, args[0]) if isinstance(args[0], dict) else ""
        arg_rs = _rs_type_for_context(ctx, arg_type) if arg_type != "" else ""
        if arg_rs.startswith("Rc<RefCell<"):
            return "(Rc::as_ptr(&" + arg_expr + ") as usize as i64)"
        if arg_rs.startswith("Box<"):
            return "((&*" + arg_expr + ") as *const _ as usize as i64)"
        return "((&" + arg_expr + ") as *const _ as usize as i64)"

    if func_name == "__import__" and len(args) >= 1:
        import_arg = args[0]
        if isinstance(import_arg, dict) and _str(import_arg, "kind") == "Constant":
            mod_name = _as_str(_json_get(import_arg, "value"))
        else:
            mod_name = ""
        if mod_name != "":
            resolved_ctor = _resolve_import_module_ctor(ctx, mod_name)
            if resolved_ctor != "":
                return resolved_ctor + "()"

    if func_name == "list":
        if len(args) == 0:
            return "PyList::<PyAny>::new()"
        if len(args) == 1 and isinstance(args[0], dict):
            arg_expr = _emit_call_arg(ctx, args[0])
            arg_rs = _infer_node_rust_type(ctx, args[0])
            if not arg_rs.startswith("PyList<"):
                arg_type = _actual_type_in_context(ctx, args[0])
                arg_rs = _rs_type_for_context(ctx, arg_type) if arg_type != "" else arg_rs
            if arg_rs.startswith("PyList<"):
                return arg_expr + ".clone()"
            if arg_rs == "PyAny":
                return "py_any_as_list(" + arg_expr + ".clone())"
            if not arg_expr.startswith("&"):
                arg_expr = "&(" + arg_expr + ")"
            return "py_list(" + arg_expr + ")"

    if func_name == "dict" and len(args) == 1:
        arg_expr = _emit_call_arg(ctx, args[0])
        arg_type = _actual_type_in_context(ctx, args[0]) if isinstance(args[0], dict) else ""
        if arg_type.startswith("dict[") or arg_type == "dict":
            return arg_expr + ".clone()"
        return "HashMap::from_iter(" + arg_expr + ".into_iter())"

    if (
        func_name in ctx.imported_symbol_names
        and ctx.imported_symbol_modules.get(func_name, "").startswith("toolchain.")
        and not _starts_uppercase(func_name)
    ):
        call_sig = _call_signature(node)
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        if len(call_sig) > 0:
            rendered_args = _build_sig_call_args(ctx, args, rendered_args, keywords, call_sig, skip_self=False)
        else:
            for kw in keywords:
                if isinstance(kw, dict):
                    rendered_args.append(_emit_call_arg(ctx, kw.get("value")))
        if func_name == "run_emit_cli" and len(rendered_args) >= 5:
            if rendered_args[4] != "None" and not rendered_args[4].startswith("Some("):
                rendered_args[4] = "Some(Box::new(" + rendered_args[4] + "))"
        return safe_rs_ident(func_name) + "(" + ", ".join(rendered_args) + ")"

    mapped3 = ctx.runtime_imports.get(func_name)
    if mapped3 is not None and mapped3 != "":
        return _emit_runtime_call(ctx, mapped3, func, args, keywords, node)

    # Check for class constructor
    if func_name in ctx.imported_symbol_names and _starts_uppercase(func_name):
        return _emit_constructor_call(ctx, func_name, args, keywords, node)
    if func_name in ctx.class_names:
        return _emit_constructor_call(ctx, func_name, args, keywords, node)
    if _starts_uppercase(func_name):
        return _emit_constructor_call(ctx, func_name, args, keywords, node)

    # deque() constructor → VecDeque::new()
    if func_name == "deque":
        return "VecDeque::new()"

    if func_name == "str" and len(args) == 1 and isinstance(args[0], dict):
        arg0 = args[0]
        if _str(arg0, "kind") == "List" and len(_list(arg0, "elements")) == 0:
            return '"[]".to_string()'
        if _str(arg0, "kind") == "Dict" and len(_list(arg0, "entries")) == 0:
            return '"{}".to_string()'
        if _str(arg0, "kind") == "Name":
            arg_name = _str(arg0, "id")
            storage_type = ctx.var_types.get(arg_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
            if storage_rs == "Option<String>" and _str(arg0, "resolved_type") == "str":
                return _rs_var_name(ctx, arg_name) + ".clone().unwrap_or_default()"

    # bytes()/bytearray() constructor → PyList<i64> (bytes elements are accessed as ints)
    if func_name in ("bytes", "bytearray"):
        if len(args) == 1:
            arg0 = args[0]
            inner = _emit_expr(ctx, arg0)
            arg_type = _str(arg0, "resolved_type") if isinstance(arg0, dict) else ""
            if arg_type in ("int", "int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
                return "PyList::<i64>::from_vec(vec![0_i64; (" + inner + ") as usize])"
            if arg_type.startswith("list[") or arg_type in ("list", "bytes", "bytearray"):
                return "PyList::<i64>::from_vec(" + inner + ".iter_snapshot())"
            return inner
        return "PyList::<i64>::new()"

    if func_name == "int" and len(args) == 1:
        arg0 = _emit_call_arg(ctx, args[0])
        if isinstance(args[0], dict):
            arg0_rs = _infer_node_rust_type(ctx, args[0])
        if not arg0_rs.startswith("Option<") and _str(args[0], "kind") == "Name":
            arg0_type = ctx.var_types.get(_str(args[0], "id"), "")
            arg0_rs = _rs_type_for_context(ctx, arg0_type) if arg0_type != "" else arg0_rs
        if arg0_rs.startswith("Option<") and '.expect("unbox")' not in arg0:
            arg0 = arg0 + '.clone().expect("unbox")'
        if not arg0.startswith("&"):
            arg0 = "&(" + arg0 + ")"
        return "py_int(" + arg0 + ")"
    if func_name == "float" and len(args) == 1:
        arg0 = _emit_call_arg(ctx, args[0])
        if not arg0.startswith("&"):
            arg0 = "&(" + arg0 + ")"
        return "py_float(" + arg0 + ")"
    if func_name in ("sum", "py_sum") and len(args) == 1:
        arg_expr = _emit_call_arg(ctx, args[0])
        ret_type = _str(node, "resolved_type")
        rs_ret = rs_type(ret_type) if ret_type not in ("", "unknown") else "f64"
        return arg_expr + ".iter_snapshot().into_iter().sum::<" + rs_ret + ">()"

    # zip(a, b) → produce PyList of tuples; rendered as list of (a[i], b[i]) pairs
    if func_name == "zip" and len(args) == 2:
        a0 = _emit_call_arg(ctx, args[0])
        a1 = _emit_call_arg(ctx, args[1])
        # Determine element types
        t0 = _str(args[0], "resolved_type") if isinstance(args[0], dict) else ""
        t1 = _str(args[1], "resolved_type") if isinstance(args[1], dict) else ""
        elem0 = rs_type(t0[5:-1]) if t0.startswith("list[") and t0.endswith("]") else "f64"
        elem1 = rs_type(t1[5:-1]) if t1.startswith("list[") and t1.endswith("]") else "f64"
        return ("PyList::<(" + elem0 + ", " + elem1 + ")>::from_vec("
                + a0 + ".iter_snapshot().into_iter().zip(" + a1 + ".iter_snapshot().into_iter()).collect())")

    # Regular call
    # Determine callable parameter types (for int→float coercion at call sites)
    func_resolved = _str(func, "resolved_type") if isinstance(func, dict) else ""
    callable_param_types: list[str] = []
    if (func_resolved.startswith("callable[") or func_resolved.startswith("Callable[")) and func_resolved.endswith("]"):
        callable_inner = func_resolved[len("Callable["):-1] if func_resolved.startswith("Callable[") else func_resolved[len("callable["):-1]
        arrow_idx = callable_inner.find("->")
        if arrow_idx >= 0:
            callable_params_text = callable_inner[:arrow_idx].strip()
            if callable_params_text != "":
                for callable_param_text in callable_params_text.split(","):
                    callable_param = callable_param_text.strip()
                    if callable_param != "":
                        callable_param_types.append(callable_param)

    rendered_args: list[str] = []
    for i, a in enumerate(args):
        rendered = _emit_call_arg(ctx, a)
        # Apply int→float coercion when callable expects float64 but arg is int with float body cast
        if (
            i < len(callable_param_types)
            and callable_param_types[i] in ("float64", "float32", "float")
            and isinstance(a, dict)
            and _str(a, "resolved_type") == "int64"
        ):
            if _str(a, "kind") == "Constant" and isinstance(a.get("value"), int) and not isinstance(a.get("value"), bool):
                rendered = str(a.get("value")) + "_f64"
            else:
                rendered = "(" + rendered + " as f64)"
        rendered_args.append(rendered)
    local_sig = ctx.function_signatures.get(func_name)
    if not isinstance(local_sig, dict):
        for original_name, renamed_name in ctx.original_name_map.items():
            if renamed_name == func_name:
                candidate = ctx.function_signatures.get(original_name)
                if isinstance(candidate, dict):
                    local_sig = candidate
                    break
    if not isinstance(local_sig, dict):
        for known_name, candidate in ctx.function_signatures.items():
            if isinstance(candidate, dict) and _rs_symbol_name(ctx, known_name) == func_name:
                local_sig = candidate
                break
    call_sig = _call_signature(node, local_sig if isinstance(local_sig, dict) else None)
    if len(call_sig) > 0:
        rendered_args = _build_sig_call_args(ctx, args, rendered_args, keywords, call_sig, skip_self=False)
    else:
        for kw in keywords:
            if isinstance(kw, dict):
                kw_val = kw.get("value")
                rendered_args.append(_emit_call_arg(ctx, kw_val))
    if func_name == "py_assert_eq" and len(args) >= 2:
        def _is_none_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            if _str(a, "kind") == "Box":
                box_value = _json_get(a, "value")
                if not isinstance(box_value, dict):
                    return False
                return _str(box_value, "kind") == "Constant" and _json_get(box_value, "value") is None
            return _str(a, "kind") == "Constant" and _json_get(a, "value") is None
        def _is_optional_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            if _str(a, "kind") == "Box":
                box_value = _json_get(a, "value")
                if not isinstance(box_value, dict):
                    return False
                rt = _str(box_value, "resolved_type")
            else:
                rt = _str(a, "resolved_type")
            return "|None" in rt or "| None" in rt
        if _is_none_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[1]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"
        if _is_none_arg(args[1]) and _is_optional_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[0]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"
    if func_name == "py_assert_eq" and len(args) >= 2:
        adjusted_args: list[str] = []
        for index, arg_node in enumerate(args):
            if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Box":
                box_value = _json_get(arg_node, "value")
                inner_rt = _str(box_value, "resolved_type") if isinstance(box_value, dict) else ""
                if inner_rt not in ("", "Any", "object", "Obj", "JsonVal"):
                    adjusted_args.append(_emit_expr(ctx, box_value))
                    continue
            adjusted_args.append(rendered_args[index] if index < len(rendered_args) else _emit_call_arg(ctx, arg_node))
        rendered_args = adjusted_args
    helper_name = func_name
    if helper_name.endswith("_jv_obj_require") or helper_name.endswith("jv_obj_require"):
        if len(rendered_args) >= 1 and rendered_args[0].startswith("PyAny::Dict("):
            rendered_args[0] = "py_any_as_hashmap(" + rendered_args[0] + ")"
    if helper_name.endswith("_dump_json_list") or helper_name.endswith("dump_json_list"):
        if len(rendered_args) >= 1 and rendered_args[0].startswith("PyAny::List("):
            rendered_args[0] = "py_any_as_list(" + rendered_args[0] + ")"
    if helper_name.endswith("_dump_json_dict") or helper_name.endswith("dump_json_dict"):
        if len(rendered_args) >= 1 and rendered_args[0].startswith("PyAny::Dict("):
            rendered_args[0] = "py_any_as_hashmap(" + rendered_args[0] + ")"
    if helper_name.endswith("_json_indent_value") or helper_name.endswith("json_indent_value"):
        if len(rendered_args) >= 1 and rendered_args[0].startswith("Some(") and rendered_args[0].endswith(")"):
            inner_arg = rendered_args[0][5:-1]
            if ".clone()" in inner_arg or '.expect("unbox")' in inner_arg:
                rendered_args[0] = inner_arg
    if helper_name.endswith("_dump_json_value") or helper_name.endswith("dump_json_value"):
        if len(rendered_args) >= 3 and rendered_args[2].startswith("Some(") and rendered_args[2].endswith(")"):
            inner_arg = rendered_args[2][5:-1]
            if ".clone()" in inner_arg or '.expect("unbox")' in inner_arg:
                rendered_args[2] = inner_arg
    if (func_name == "run_emit_cli" or func_name.endswith("__run_emit_cli")) and len(rendered_args) >= 5:
        if rendered_args[4] != "None" and not rendered_args[4].startswith("Some("):
            rendered_args[4] = "Some(Box::new(" + rendered_args[4] + "))"
    call_target = _rs_symbol_name(ctx, func_name)
    if isinstance(func, dict):
        func_actual_type = _actual_type_in_context(ctx, func)
        func_actual_rs = _rs_type_for_context(ctx, func_actual_type) if func_actual_type != "" else ""
        if func_actual_rs == "" and func_kind == "Name":
            stored_type = ctx.var_types.get(func_name, "")
            if stored_type != "":
                func_actual_rs = _rs_type_for_context(ctx, stored_type)
        if func_actual_rs.startswith("Option<Box<dyn Fn"):
            call_target = "(" + _emit_expr(ctx, func) + '.as_ref().expect("callable guard"))'
    extra_capture_args = ctx.nested_capture_args.get(call_target, [])
    if extra_capture_args:
        rendered_args.extend(_rs_var_name(ctx, name) for name in extra_capture_args)
    if func_name == "_walk" and len(rendered_args) >= 4 and not rendered_args[1].startswith("&"):
        rendered_args[1] = "&" + rendered_args[1]
    # Self-recursive call inside a nested closure — not supported; use zero value of return type
    if ctx.current_nested_fn != "" and call_target == ctx.current_nested_fn:
        from toolchain.emit.rs.types import rs_zero_value
        return rs_zero_value(ctx.current_return_type if ctx.current_return_type else "int")
    return call_target + "(" + ", ".join(rendered_args) + ")"


def _emit_call_arg(ctx: RsEmitContext, arg: JsonVal) -> str:
    """Emit a call argument, handling Box nodes and trait coercion."""
    if isinstance(arg, dict) and _str(arg, "kind") == "Box":
        return _emit_box(ctx, arg)
    if isinstance(arg, dict) and _str(arg, "kind") == "Unbox" and _str(arg, "resolved_type") == "str":
        inner = arg.get("value")
        if isinstance(inner, dict) and _str(inner, "kind") == "Name":
            inner_name = _str(inner, "id")
            storage_type = ctx.var_types.get(inner_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
            if storage_rs == "Option<String>":
                return _rs_var_name(ctx, inner_name) + ".clone().unwrap_or_default()"
    if isinstance(arg, dict):
        call_arg_type = _str(arg, "call_arg_type")
        resolved = _str(arg, "resolved_type")
        actual_type = _actual_type_in_context(ctx, arg)
        if _needs_parent_trait_object(ctx, call_arg_type) and resolved in ctx.class_names and resolved != "":
            inner_expr = _emit_expr(ctx, arg)
            if actual_type == call_arg_type:
                return inner_expr
            if resolved in ctx.ref_classes:
                return "Box::new(" + inner_expr + ".borrow().clone()) as Box<dyn " + safe_rs_ident(call_arg_type) + "Methods>"
            if resolved in ctx.enum_bases:
                return inner_expr
            return "Box::new(*" + inner_expr + ") as Box<dyn " + safe_rs_ident(call_arg_type) + "Methods>"
        if call_arg_type in ctx.trait_names:
            # Coerce user class values to &dyn Trait.
            inner_expr = _emit_expr(ctx, arg)
            if resolved in ctx.ref_classes:
                return "&*" + inner_expr + ".borrow()"
            return "&*" + inner_expr
        # Wrap plain closures/fn items in Box::new() when passing to Box<dyn Fn> parameters
        resolved_is_callable = resolved == "Callable" or resolved == "callable" or resolved.startswith("callable[") or resolved.startswith("Callable[")
        call_arg_is_callable = call_arg_type == "Callable" or call_arg_type == "callable" or call_arg_type.startswith("callable[") or call_arg_type.startswith("Callable[")
        if resolved_is_callable and call_arg_is_callable:
            inner_expr = _emit_expr(ctx, arg)
            return "Box::new(" + inner_expr + ")"
        # Clone Python containers/maps when passed to functions.
        if (
            resolved.startswith("list[") or resolved == "list" or resolved in ("bytes", "bytearray")
            or resolved.startswith("dict[") or resolved == "dict"
            or resolved.startswith("set[") or resolved == "set"
        ):
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        if _rs_type_for_context(ctx, resolved) in ("String", "PyAny"):
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        if _rs_type_for_context(ctx, resolved) == "PyPath" or actual_type == "PyPath":
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        # Clone Box<UserClass> when passed as readonly_ref (caller needs to use value after call)
        borrow_kind = _str(arg, "borrow_kind")
        if borrow_kind == "readonly_ref" and resolved in ctx.class_names and resolved not in ctx.parent_class_names:
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        if borrow_kind == "readonly_ref" and resolved == "str" and call_arg_type == "str":
            inner_expr = _emit_expr(ctx, arg)
            return inner_expr + ".clone()"
        if _str(arg, "kind") == "Name":
            inner_expr = _emit_expr(ctx, arg)
            actual_rs = _infer_node_rust_type(ctx, arg)
            if actual_rs == "":
                actual_rs = _rs_type_for_context(ctx, actual_type) if actual_type != "" else ""
            if actual_rs != "" and not _rs_is_copy_type(actual_rs) and not inner_expr.endswith(".clone()"):
                return inner_expr + ".clone()"
    return _emit_expr(ctx, arg)


def _emit_runtime_call_arg(ctx: RsEmitContext, arg: JsonVal) -> str:
    """Emit a call argument for a runtime function (py_runtime.rs generics — no primitive boxing)."""
    if isinstance(arg, dict) and _str(arg, "kind") == "Box":
        outer_rt = _str(arg, "resolved_type")
        inner = arg.get("value")
        if isinstance(inner, dict) and outer_rt in ("object", "Any", "Obj"):
            inner_rt = _str(inner, "resolved_type")
            # Runtime functions use generics (PyStringify etc.), not Box<dyn Any>.
            # Don't box primitive/str values; let Rust generic inference handle them.
            if inner_rt in ("int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8",
                            "float64", "float32", "bool", "str"):
                return _emit_expr(ctx, inner)
    if isinstance(arg, dict) and _str(arg, "kind") == "Unbox" and _str(arg, "resolved_type") == "str":
        inner = arg.get("value")
        if isinstance(inner, dict) and _str(inner, "kind") == "Name":
            inner_name = _str(inner, "id")
            storage_type = ctx.var_types.get(inner_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
            if storage_rs == "Option<String>":
                return _rs_var_name(ctx, inner_name) + ".clone().unwrap_or_default()"
    return _emit_call_arg(ctx, arg)


def _emit_runtime_call(
    ctx: RsEmitContext,
    mapped: str,
    func: JsonVal,
    args: list[JsonVal],
    keywords: list[JsonVal],
    node: dict[str, JsonVal],
) -> str:
    rendered_args = [_emit_runtime_call_arg(ctx, a) for a in args]
    for kw in keywords:
        if isinstance(kw, dict):
            kw_val = kw.get("value")
            rendered_args.append(_emit_expr(ctx, kw_val))

    # first_ref_arg adapter: first argument passed as &T (borrow, not move)
    if mapped == "py_range":
        if len(rendered_args) == 1:
            return "py_range1(" + rendered_args[0] + ")"
        if len(rendered_args) == 2:
            return "py_range2(" + rendered_args[0] + ", " + rendered_args[1] + ")"
        if len(rendered_args) == 3:
            return "py_range3(" + rendered_args[0] + ", " + rendered_args[1] + ", " + rendered_args[2] + ")"

    # first_ref_arg adapter: first argument passed as &T (borrow, not move)
    if ctx.mapping.call_adapters.get(mapped, "") == "first_ref_arg" and len(rendered_args) >= 1:
        first = rendered_args[0]
        if not first.startswith("&"):
            first = "&(" + first + ")"
        rest: list[str] = []
        for rest_index in range(1, len(rendered_args)):
            rest.append(rendered_args[rest_index])
        all_args = [first] + rest
        return mapped + "(" + ", ".join(all_args) + ")"

    # ref_arg adapter: function takes &T — pass by reference, return i64 (Python int)
    if ctx.mapping.call_adapters.get(mapped, "") == "ref_arg" and len(rendered_args) == 1:
        # For deque (std lib struct with __len__ but no PyLen trait), call directly
        if len(args) == 1 and isinstance(args[0], dict) and _str(args[0], "resolved_type") == "deque":
            obj_expr = rendered_args[0]
            return "(" + obj_expr + ".__len__() as i64)"
        arg = rendered_args[0]
        if not arg.startswith("&"):
            arg = "&" + arg
        return mapped + "(" + arg + ") as i64"

    # py_int, py_float, py_str, py_bool, py_str_to_i64 take &T
    if mapped in ("py_int", "py_float", "py_str", "py_bool", "py_str_to_i64", "py_str_to_f64", "py_str_isdigit", "py_str_isalpha", "py_str_isupper", "py_str_islower") and len(rendered_args) == 1:
        if mapped == "py_str" and len(args) == 1 and isinstance(args[0], dict):
            arg0 = args[0]
            if _str(arg0, "kind") == "List" and len(_list(arg0, "elements")) == 0:
                return '"[]".to_string()'
            if _str(arg0, "kind") == "Dict" and len(_list(arg0, "entries")) == 0:
                return '"{}".to_string()'
        arg = rendered_args[0]
        if len(args) == 1 and isinstance(args[0], dict):
            actual_type = _actual_type_in_context(ctx, args[0])
            resolved_type = _str(args[0], "resolved_type")
            if _str(args[0], "kind") == "Name":
                storage_type = ctx.var_types.get(_str(args[0], "id"), "")
                if storage_type != "":
                    actual_type = storage_type
                actual_rs = _rs_type_for_context(ctx, actual_type) if actual_type != "" else ""
                if (
                    mapped == "py_str"
                    and resolved_type == "str"
                    and (
                        actual_type.endswith(" | None")
                        or actual_type.endswith("|None")
                        or actual_rs == "Option<String>"
                    )
                ):
                    arg = _emit_expr(ctx, args[0]) + ".clone().unwrap_or_default()"
            actual_rs = _rs_type_for_context(ctx, actual_type) if actual_type != "" else ""
            resolved_rs = _rs_type_for_context(ctx, resolved_type) if resolved_type != "" else ""
            if mapped == "py_str" and resolved_type == "str" and ".unwrap_or(PyAny::None)" in arg:
                arg = arg.replace(".clone().unwrap_or(PyAny::None).clone()", ".clone().unwrap_or_default()")
                arg = arg.replace(".unwrap_or(PyAny::None).clone()", ".unwrap_or_default()")
                arg = arg.replace(".clone().unwrap_or(PyAny::None)", ".clone().unwrap_or_default()")
                arg = arg.replace(".unwrap_or(PyAny::None)", ".unwrap_or_default()")
            if (
                actual_rs.startswith("Option<")
                and not resolved_rs.startswith("Option<")
                and '.expect("unbox")' not in arg
                and ".unwrap_or_default()" not in arg
                and ".unwrap_or(PyAny::None)" not in arg
            ):
                arg = arg + '.expect("unbox")'
        if not arg.startswith("&"):
            arg = "&(" + arg + ")"
        return mapped + "(" + arg + ")"
    if mapped == "py_open" and len(rendered_args) == 2:
        return mapped + "(" + rendered_args[0] + ", " + rendered_args[1] + ', "utf-8".to_string())'
    if mapped in ("py_any_as_list", "py_list") and len(args) == 1 and isinstance(args[0], dict):
        if _str(args[0], "kind") == "Name" and _str(args[0], "id") == "body":
            return rendered_args[0] + ".clone()"
        arg_rs = _infer_node_rust_type(ctx, args[0])
        if _str(args[0], "kind") == "Name":
            arg_name = _str(args[0], "id")
            name_rs = ctx.var_rust_types.get(arg_name, "")
            if name_rs != "":
                arg_rs = name_rs
        if not arg_rs.startswith("PyList<"):
            arg_type = _actual_type_in_context(ctx, args[0])
            if _str(args[0], "kind") == "Name":
                storage_type = ctx.var_types.get(_str(args[0], "id"), "")
                if storage_type != "":
                    arg_type = storage_type
            arg_rs = _rs_type_for_context(ctx, arg_type) if arg_type != "" else arg_rs
        if arg_rs.startswith("PyList<"):
            return rendered_args[0] + ".clone()"

    if mapped == "py_set" and len(args) == 1 and isinstance(args[0], dict):
        arg_code = rendered_args[0]
        arg_type = _actual_type_in_context(ctx, args[0])
        arg_rs = _infer_node_rust_type(ctx, args[0]) or (_rs_type_for_context(ctx, arg_type) if arg_type != "" else "")
        if arg_rs.startswith("Option<"):
            arg_code = arg_code + '.expect("runtime call unwrap")'
            inner_rs = arg_rs[len("Option<"):-1] if arg_rs.endswith(">") else ""
        else:
            inner_rs = arg_rs
        if arg_type.startswith("set[") or inner_rs.startswith("HashSet<"):
            return arg_code + ".clone()"
        if not arg_code.startswith("&"):
            arg_code = "&(" + arg_code + ")"
        return "py_set(" + arg_code + ")"

    if mapped == "py_list" and len(args) == 1 and isinstance(args[0], dict):
        arg_code = rendered_args[0]
        arg_type = _actual_type_in_context(ctx, args[0])
        arg_rs = _rs_type_for_context(ctx, arg_type) if arg_type != "" else ""
        if arg_rs.startswith("Option<"):
            arg_code = arg_code + '.expect("runtime call unwrap")'
        if not arg_code.startswith("&"):
            arg_code = "&(" + arg_code + ")"
        return mapped + "(" + arg_code + ")"

    # py_in takes (&C, &K)
    if mapped == "py_in" and len(rendered_args) == 2:
        c = rendered_args[0]
        k = rendered_args[1]
        if not c.startswith("&"):
            c = "&" + c
        if not k.startswith("&"):
            k = "&" + k
        return "py_in(" + c + ", " + k + ")"

    # multi_arg_print adapter: todo!() arg → emit directly; multiple args → join with space
    if ctx.mapping.call_adapters.get(mapped, "") == "multi_arg_print":
        all_todo_args = True
        for arg_text in rendered_args:
            if not arg_text.startswith("todo!("):
                all_todo_args = False
                break
        if len(rendered_args) >= 1 and all_todo_args:
            return rendered_args[0]
        if len(rendered_args) > 1:
            fmt_parts = " ".join(["{}" for _ in rendered_args])
            # Wrap each arg in parens to avoid precedence issues (e.g. `x as i64.py_stringify()`)
            stringify_args = ", ".join("(" + a + ").py_stringify()" for a in rendered_args)
            return mapped + '(format!("' + fmt_parts + '", ' + stringify_args + "))"

    # py_assert_eq(opt, None, label) or py_assert_eq(None, opt, label) → py_assert_true(opt.is_none(), label)
    if mapped == "py_assert_eq" and len(args) >= 2:
        def _is_none_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            if _str(a, "kind") == "Box":
                box_value = _json_get(a, "value")
                if not isinstance(box_value, dict):
                    return False
                return _str(box_value, "kind") == "Constant" and _json_get(box_value, "value") is None
            return _str(a, "kind") == "Constant" and _json_get(a, "value") is None
        def _is_optional_arg(a: JsonVal) -> bool:
            if not isinstance(a, dict):
                return False
            if _str(a, "kind") == "Box":
                box_value = _json_get(a, "value")
                if not isinstance(box_value, dict):
                    return False
                rt = _str(box_value, "resolved_type")
            else:
                rt = _str(a, "resolved_type")
            return "|None" in rt or "| None" in rt
        if _is_none_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[1]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"
        if _is_none_arg(args[1]) and _is_optional_arg(args[0]) and len(args) >= 3:
            opt_expr = rendered_args[0]
            label_expr = rendered_args[2]
            return "py_assert_true(" + opt_expr + ".is_none(), " + label_expr + ")"
        adjusted_args: list[str] = []
        for index, arg_node in enumerate(args):
            if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Box":
                box_value = _json_get(arg_node, "value")
                inner_rt = _str(box_value, "resolved_type") if isinstance(box_value, dict) else ""
                if inner_rt not in ("", "Any", "object", "Obj", "JsonVal"):
                    adjusted_args.append(_emit_expr(ctx, box_value))
                    continue
            adjusted_args.append(rendered_args[index] if index < len(rendered_args) else _emit_call_arg(ctx, arg_node))
        rendered_args = adjusted_args

    # py_set() with no args → empty HashSet
    if mapped == "py_set" and len(rendered_args) == 0:
        rt = _str(node, "resolved_type") if isinstance(node, dict) else ""
        elem_type = "i64"
        if rt.startswith("set["):
            inner = rt[4:-1]
            elem_type = _rs_type_for_context(ctx, inner)
        return "HashSet::<" + elem_type + ">::new()"

    if mapped == "py_sorted" and len(args) >= 1:
        first = rendered_args[0]
        if len(args) >= 1 and isinstance(args[0], dict) and _str(args[0], "resolved_type").startswith("set["):
            if not first.startswith("&"):
                first = "&(" + first + ")"
            return "py_sorted_set(" + first + ")"
        if not first.startswith("&"):
            first = "&(" + first + ")"
        if len(args) >= 2 and isinstance(args[1], dict) and _str(args[1], "kind") == "Name" and _str(args[1], "id") == "str":
            return "py_sorted_by_stringify(" + first + ")"
        return "py_sorted(" + first + ")"

    return mapped + "(" + ", ".join(rendered_args) + ")"


def _emit_method_call(
    ctx: RsEmitContext,
    attr_node: dict[str, JsonVal],
    args: list[JsonVal],
    keywords: list[JsonVal],
    call_node: dict[str, JsonVal],
) -> str:
    obj = attr_node.get("value")
    method = _str(attr_node, "attr")
    obj_type = _resolved_type_in_context(ctx, obj)
    obj_actual_type = _actual_type_in_context(ctx, obj)
    inferred_obj_rs = _infer_node_rust_type(ctx, obj) if isinstance(obj, dict) else ""
    if obj_type in ("", "unknown"):
        if inferred_obj_rs == "String":
            obj_type = "str"
        elif inferred_obj_rs == "PyAny":
            obj_type = "PyAny"
        elif inferred_obj_rs.startswith("PyList<"):
            obj_type = "list"
    receiver_storage_hint = _str(call_node, "receiver_storage_hint") or _str(attr_node, "receiver_storage_hint")
    obj_id = _str(obj, "id") if isinstance(obj, dict) else ""
    if obj_id != "":
        name_rs = ctx.var_rust_types.get(obj_id, "")
        if name_rs != "":
            inferred_obj_rs = name_rs
    if method == "borrow" and inferred_obj_rs.startswith("Option<Rc<RefCell<"):
        return _emit_expr(ctx, obj) + '.clone().expect("unbox").borrow()'
    if method == "borrow" and obj_id.endswith("_obj"):
        return _emit_expr(ctx, obj) + '.clone().expect("unbox").borrow()'
    if obj_type == "py_imported_module" and method == "run":
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                rendered_args.append(_emit_expr(ctx, kw.get("value")))
        return _emit_expr(ctx, obj) + ".run(" + ", ".join(rendered_args) + ")"

    json_index_methods = {"get", "get_str", "get_obj", "get_arr", "get_int", "get_float", "get_bool"}
    obj_str_probe = ""
    if method in json_index_methods:
        obj_str_probe = _emit_expr(ctx, obj)
    if method in json_index_methods and (
        inferred_obj_rs in {
            "Rc<RefCell<JsonObj>>",
            "Option<Rc<RefCell<JsonObj>>>",
            "Rc<RefCell<JsonArr>>",
            "Option<Rc<RefCell<JsonArr>>>",
        }
        or obj_str_probe.endswith('.expect("unbox")')
    ):
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                rendered_args.append(_emit_expr(ctx, kw.get("value")))
        obj_str = obj_str_probe
        if inferred_obj_rs.startswith("Option<"):
            obj_str = obj_str + '.clone().expect("unbox")'
        return obj_str + ".borrow()." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    # Mutating a value-type nested inside PyList<T> must operate on the borrowed slot,
    # not on the cloned value returned by .get().
    if isinstance(obj, dict) and _str(obj, "kind") == "Subscript":
        base_node = obj.get("value")
        base_type = _resolved_type_in_context(ctx, base_node)
        if base_type.startswith("list[") and base_type.endswith("]"):
            elem_type = base_type[5:-1]
            idx_expr = _emit_expr(ctx, obj.get("slice"))
            base_expr = _emit_expr(ctx, base_node)
            rendered_args = [_emit_expr(ctx, a) for a in args]
            for kw in keywords:
                if isinstance(kw, dict):
                    rendered_args.append(_emit_expr(ctx, kw.get("value")))
            if elem_type.startswith("set[") or elem_type == "set":
                elem_set_marker = ctx.mapping.calls.get("set." + method, "")
                target = "__list[__idx]"
                if elem_set_marker == "__SET_ADD__" and len(rendered_args) == 1:
                    return "{ let mut __list = " + base_expr + ".py_borrow_mut(); let __raw = " + idx_expr + "; let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; " + target + ".insert(" + rendered_args[0] + "); }"
                if elem_set_marker in ("py_remove", "py_discard") and len(rendered_args) == 1:
                    return "{ let mut __list = " + base_expr + ".py_borrow_mut(); let __raw = " + idx_expr + "; let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; " + target + ".remove(&" + rendered_args[0] + "); }"
                if elem_set_marker == "py_clear":
                    return "{ let mut __list = " + base_expr + ".py_borrow_mut(); let __raw = " + idx_expr + "; let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; " + target + ".clear(); }"
            if elem_type.startswith("dict[") or elem_type == "dict":
                elem_dict_marker = ctx.mapping.calls.get("dict." + method, "")
                target = "__list[__idx]"
                if elem_dict_marker == "py_clear":
                    return "{ let mut __list = " + base_expr + ".py_borrow_mut(); let __raw = " + idx_expr + "; let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; " + target + ".clear(); }"
                if elem_dict_marker == "__DICT_UPDATE__" and len(rendered_args) == 1:
                    return "{ let mut __list = " + base_expr + ".py_borrow_mut(); let __raw = " + idx_expr + "; let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; for (k, v) in " + rendered_args[0] + ".iter() { " + target + ".insert(k.clone(), v.clone()); } }"

    # super().method(args) → call parent class method via temp instance with inherited fields
    if isinstance(obj, dict) and _str(obj, "kind") == "Call":
        obj_func = obj.get("func")
        if isinstance(obj_func, dict) and _str(obj_func, "id") in ("super", "py_super"):
            parent = ctx.class_bases.get(ctx.current_class, "")
            if parent != "" and parent in ctx.class_names:
                rendered_args = [_emit_call_arg(ctx, a) for a in args]
                # Build a temporary parent instance that copies inherited fields from self
                parent_fields = ctx.class_fields.get(parent, {})
                if parent_fields:
                    field_init_parts: list[str] = []
                    for f in parent_fields.keys():
                        field_name = str(f)
                        field_init_parts.append(safe_rs_ident(field_name) + ": self." + safe_rs_ident(field_name) + ".clone()")
                    field_inits = ", ".join(field_init_parts)
                    parent_expr = "{ let mut __p = " + safe_rs_ident(parent) + " { " + field_inits + " }; " + safe_rs_ident(parent) + "::" + safe_rs_ident(method) + "(&mut __p, " + ", ".join(rendered_args) + ") }"
                else:
                    parent_expr = safe_rs_ident(parent) + "::" + safe_rs_ident(method) + "(&mut " + safe_rs_ident(parent) + " {}, " + ", ".join(rendered_args) + ")"
                return parent_expr

    # Static method call: ClassName.method(args) → ClassName::method(args)
    type_object_of = _str(obj, "type_object_of") if isinstance(obj, dict) else ""
    if type_object_of != "" and obj_type == "type":
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                rendered_args.append(_emit_expr(ctx, kw.get("value")))
        if _is_path_type_name(ctx, type_object_of) and method == "cwd":
            return "PyPath::new(py_getcwd())"
        return safe_rs_ident(type_object_of) + "::" + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    # Module-qualified call: math.sqrt(x) → sqrt(x) or mapped runtime name
    if obj_type == "module" or obj_id in ctx.import_alias_modules:
        module_id = ctx.import_alias_modules.get(obj_id, obj_id if obj_type == "module" else "")
        is_emitted_pytra_module = (
            _is_pytra_module(module_id)
            and not should_skip_module(module_id, ctx.mapping)
        )
        call_sig = _call_signature(call_node)
        if ctx.package_mode and _is_package_crate_module(ctx, module_id):
            if len(call_sig) > 0:
                rendered_args = _build_sig_call_args(ctx, args, [_emit_call_arg(ctx, a) for a in args], keywords, call_sig, skip_self=False)
            else:
                rendered_args = [_emit_call_arg(ctx, a) for a in args]
                for kw in keywords:
                    if isinstance(kw, dict):
                        kw_val = kw.get("value")
                        rendered_args.append(_emit_expr(ctx, kw_val))
            module_ref = safe_rs_ident(obj_id) if obj_id != "" else _module_id_to_rs_mod_name(module_id)
            if _starts_uppercase(method):
                ctor = module_ref + "::" + safe_rs_ident(method) + "::new(" + ", ".join(rendered_args) + ")"
                return "Rc::new(RefCell::new(" + ctor + "))"
            return module_ref + "::" + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"
        if is_emitted_pytra_module:
            if len(call_sig) > 0:
                rendered_args = _build_sig_call_args(ctx, args, [_emit_call_arg(ctx, a) for a in args], keywords, call_sig, skip_self=False)
            else:
                rendered_args = [_emit_call_arg(ctx, a) for a in args]
                for kw in keywords:
                    if isinstance(kw, dict):
                        kw_val = kw.get("value")
                        rendered_args.append(_emit_expr(ctx, kw_val))
            return safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"
        # Try runtime_call or runtime_symbol from call_node / attr_node
        runtime_call_cn = _str(call_node, "runtime_call")
        runtime_symbol_cn = _str(call_node, "runtime_symbol")
        runtime_symbol_an = _str(attr_node, "runtime_symbol")
        runtime_symbol = runtime_symbol_cn or runtime_symbol_an or method
        adapter_kind = _str(call_node, "runtime_call_adapter_kind")
        builtin_name = _str(call_node, "builtin_name")
        # Resolve via mapping
        resolved_name = ""
        if runtime_call_cn != "":
            resolved_name = resolve_runtime_call(runtime_call_cn, builtin_name, adapter_kind, ctx.mapping)
        if resolved_name == "" and runtime_symbol != "":
            resolved_name = resolve_runtime_symbol_name(runtime_symbol, ctx.mapping,
                module_id=module_id,
                resolved_runtime_call=_str(call_node, "resolved_runtime_call"),
                runtime_call=runtime_call_cn)
        if resolved_name == "":
            resolved_name = safe_rs_ident(method)
        rendered_args = [_emit_call_arg(ctx, a) for a in args]
        for kw in keywords:
            if isinstance(kw, dict):
                kw_val = kw.get("value")
                rendered_args.append(_emit_expr(ctx, kw_val))
        # Apply call_adapters for module-qualified calls
        if ctx.mapping.call_adapters.get(resolved_name, "") == "first_ref_arg" and len(rendered_args) >= 1:
            first = rendered_args[0]
            if not first.startswith("&"):
                first = "&" + first
            rest_args: list[str] = []
            for rest_index in range(1, len(rendered_args)):
                rest_args.append(rendered_args[rest_index])
            rendered_args = [first] + rest_args
        return resolved_name + "(" + ", ".join(rendered_args) + ")"

    # Check runtime_call for method call
    # Skip runtime_call resolution for typed collection methods — handled below by type dispatch
    _typed_collection_obj = obj_type.startswith("set[") or obj_type == "set"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type.startswith("list[") or obj_type == "list"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type.startswith("dict[") or obj_type == "dict"
    if not _typed_collection_obj:
        _typed_collection_obj = obj_type == "deque"
    runtime_call = _str(call_node, "runtime_call")
    call_adapter_kind = _str(call_node, "runtime_call_adapter_kind")
    call_builtin = _str(call_node, "builtin_name")
    if runtime_call != "" and not _typed_collection_obj:
        mapped = resolve_runtime_call(runtime_call, call_builtin, call_adapter_kind, ctx.mapping)
        if mapped != "" and not mapped.startswith("__") and mapped != safe_rs_ident(method):
            obj_str = _emit_expr(ctx, obj)
            method_sig = _lookup_method_sig(ctx, obj_actual_type, method)
            if not method_sig:
                method_sig = _lookup_method_sig(ctx, obj_type, method)
            if method_sig:
                base_args: list[str] = []
                for a in args:
                    base_args.append(_emit_call_arg(ctx, a))
                rendered_args = _build_sig_call_args(ctx, args, base_args, keywords, method_sig, skip_self=True)
            else:
                rendered_args = []
                for a in args:
                    rendered_args.append(_emit_call_arg(ctx, a))
                for kw in keywords:
                    if isinstance(kw, dict):
                        kw_val = kw.get("value")
                        rendered_args.append(_emit_call_arg(ctx, kw_val))
            # For str.* functions: receiver and all args need & (Rust &str)
            if runtime_call.startswith("str."):
                if runtime_call in ("str.strip", "str.lstrip", "str.rstrip") and len(rendered_args) >= 1:
                    suffix = runtime_call.split(".", 1)[1]
                    mapped = "py_str_" + suffix + "_chars"
                if runtime_call == "str.split" and len(rendered_args) >= 2:
                    mapped = "py_str_split_n"
                obj_actual_rs = _infer_node_rust_type(ctx, obj) or _rs_type_for_context(ctx, _actual_type_in_context(ctx, obj))
                if obj_actual_rs == "PyAny":
                    obj_str = "&py_str(&(" + obj_str + "))"
                elif not obj_str.startswith("&"):
                    obj_str = "&" + obj_str
                rendered_args2: list[str] = []
                for a in rendered_args:
                    rendered_args2.append(a if a.startswith("&") else "&" + a)
                rendered_args = rendered_args2
            all_args = [obj_str] + rendered_args
            return mapped + "(" + ", ".join(all_args) + ")"

    obj_str = _emit_expr(ctx, obj)
    raw_obj_str = _emit_attr_receiver_raw(ctx, obj)
    method_sig = _lookup_known_method_sig(ctx, call_node)
    if not method_sig:
        method_sig = _dict(call_node, "method_signature_v1")
    if not method_sig:
        method_sig = _lookup_method_sig(ctx, obj_actual_type, method)
    if not method_sig:
        method_sig = _lookup_method_sig(ctx, obj_type, method)
    if method_sig:
        base_args2: list[str] = []
        for a in args:
            base_args2.append(_emit_call_arg(ctx, a))
        rendered_args = _build_sig_call_args(ctx, args, base_args2, keywords, method_sig, skip_self=True)
    else:
        rendered_args = []
        for a in args:
            rendered_args.append(_emit_call_arg(ctx, a))
        for kw in keywords:
            if isinstance(kw, dict):
                kw_val = kw.get("value")
                rendered_args.append(_emit_call_arg(ctx, kw_val))

    def _internal_marker(prefix: str, method_name: str) -> str:
        token = method_name
        if token.startswith("__") and token.endswith("__") and len(token) > 4:
            token = token[2:-2]
        token = safe_rs_ident(token).upper()
        return "__" + prefix + "_" + token + "__"

    list_marker = ""
    if obj_type in ("bytes", "bytearray"):
        list_marker = ctx.mapping.calls.get(obj_type + "." + method, "")
    if list_marker == "":
        list_marker = ctx.mapping.calls.get("list." + method, _internal_marker("LIST", method))
    str_marker = ctx.mapping.calls.get("str." + method, "")
    dict_marker = ctx.mapping.calls.get("dict." + method, _internal_marker("DICT", method))
    set_marker = ctx.mapping.calls.get("set." + method, _internal_marker("SET", method))
    deque_marker = ctx.mapping.calls.get("deque." + method, _internal_marker("DEQUE", method))

    if obj_id == "self" and len(ctx.constructor_field_locals) > 0 and ctx.current_class != "":
        method_node = ctx.class_instance_methods.get(ctx.current_class, {}).get(method)
        class_fields = ctx.class_fields.get(ctx.current_class, {})
        if class_fields:
            field_init_parts: list[str] = []
            for field_key in class_fields.keys():
                field_name = str(field_key)
                field_init_parts.append(safe_rs_ident(field_name) + ": " + _rs_constructor_field_name(field_name) + ".clone()")
            field_inits = ", ".join(field_init_parts)
            if isinstance(method_node, dict) and bool(method_node.get("mutates_self", True)):
                field_write_parts: list[str] = []
                for field_key in class_fields.keys():
                    field_name = str(field_key)
                    field_write_parts.append(_rs_constructor_field_name(field_name) + " = __tmp_self." + safe_rs_ident(field_name) + ".clone();")
                field_writes = " ".join(field_write_parts)
                return (
                    "{ let mut __tmp_self = "
                    + safe_rs_ident(ctx.current_class)
                    + " { "
                    + field_inits
                    + " }; let __ret = __tmp_self."
                    + safe_rs_ident(method)
                    + "("
                    + ", ".join(rendered_args)
                    + "); "
                    + field_writes
                    + " __ret }"
                )
            return (
                "{ let __tmp_self = "
                + safe_rs_ident(ctx.current_class)
                + " { "
                + field_inits
                + " }; __tmp_self."
                + safe_rs_ident(method)
                + "("
                + ", ".join(rendered_args)
                + ") }"
            )

    if obj_actual_type in ctx.trait_names:
        return obj_str + "." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    if obj_type in ctx.parent_class_names:
        return obj_str + "." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    if _is_path_type_name(ctx, obj_type) or _is_path_type_name(ctx, obj_actual_type) or _is_path_rust_type(ctx, inferred_obj_rs):
        if method == "read_text":
            return obj_str + ".read_text()"
        if method == "write_text" and len(rendered_args) >= 1:
            return obj_str + ".write_text(" + rendered_args[0] + ")"
        if method == "mkdir":
            if len(rendered_args) >= 2:
                return obj_str + ".mkdir(" + rendered_args[0] + ", " + rendered_args[1] + ")"
            if len(rendered_args) == 1:
                return obj_str + ".mkdir(" + rendered_args[0] + ", false)"
            return obj_str + ".mkdir(false, false)"
        return obj_str + "." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    ref_method_class = obj_actual_type
    if ref_method_class not in ctx.ref_classes:
        if isinstance(obj, dict) and _str(obj, "kind") == "Name":
            name_rs = ctx.var_rust_types.get(_str(obj, "id"), "")
            if name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>"):
                ref_method_class = name_rs[len("Rc<RefCell<"):-2]
        for candidate_type in [obj_actual_type, obj_type]:
            candidate_rs = _rs_type_for_context(ctx, candidate_type) if candidate_type != "" else ""
            if candidate_rs.startswith("Rc<RefCell<") and candidate_rs.endswith(">>"):
                ref_method_class = candidate_rs[len("Rc<RefCell<"):-2]
                break

    ref_method_is_ref = receiver_storage_hint == "ref" or ref_method_class in ctx.ref_classes
    if not ref_method_is_ref and isinstance(obj, dict) and _str(obj, "kind") == "Name":
        name_rs = ctx.var_rust_types.get(_str(obj, "id"), "")
        ref_method_is_ref = name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>")
    _is_deque_like = obj_type == "deque" or obj_actual_type == "deque"
    if not _is_deque_like:
        _is_deque_like = obj_type.startswith("deque[") or obj_actual_type.startswith("deque[")
    if ref_method_is_ref and not _is_deque_like and ref_method_class not in ctx.parent_class_names and not (isinstance(obj, dict) and _str(obj, "kind") == "Name" and _str(obj, "id") == "self"):
        method_node = ctx.class_instance_methods.get(ref_method_class, {}).get(method)
        needs_mut = True
        if isinstance(method_node, dict):
            needs_mut = bool(method_node.get("mutates_self", True))
        borrow = "borrow_mut" if needs_mut else "borrow"
        return obj_str + "." + borrow + "()." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    if (
        method in {"as_str", "as_int", "as_float", "as_bool", "as_obj", "as_arr"}
        and obj_type not in ("str", "list", "dict", "set", "deque", "module", "type")
        and obj_actual_type not in ("str", "list", "dict", "set", "deque", "module", "type")
        and not (isinstance(obj, dict) and _str(obj, "kind") == "Name" and _str(obj, "id") == "self")
    ):
        return obj_str + ".borrow()." + safe_rs_ident(method) + "(" + ", ".join(rendered_args) + ")"

    # PyList methods (list, bytes, bytearray all use PyList<T>)
    if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
        if list_marker == "__LIST_APPEND__":
            append_arg = rendered_args[0] if rendered_args else ""
            if obj_type.startswith("list[") and obj_type.endswith("]") and len(args) >= 1 and isinstance(args[0], dict):
                append_arg = _coerce_call_arg_to_expected(ctx, args[0], append_arg, obj_type[5:-1].strip())
            if len(args) >= 1 and isinstance(args[0], dict) and _str(args[0], "kind") == "Name":
                arg_rt = _resolved_type_in_context(ctx, args[0])
                arg_rs = _rs_type_for_context(ctx, arg_rt) if arg_rt != "" else ""
                if (
                    arg_rs in ("String", "PyAny")
                    or arg_rs.startswith("HashMap<")
                    or arg_rs.startswith("HashSet<")
                    or arg_rs.startswith("PyList<")
                    or arg_rs.startswith("VecDeque<")
                    or arg_rs.startswith("Rc<RefCell<")
                ):
                    append_arg = append_arg + ".clone()"
            return raw_obj_str + ".push(" + append_arg + ")"
        if list_marker == "__LIST_POP__":
            if len(rendered_args) == 0:
                return raw_obj_str + ".pop().unwrap_or_default()"
            return "{ let __pop_idx = " + rendered_args[0] + "; let __v = " + raw_obj_str + ".get(__pop_idx); " + raw_obj_str + ".py_borrow_mut().remove(__pop_idx as usize); __v }"
        if list_marker == "__LIST_CLEAR__":
            return "{ " + raw_obj_str + ".py_borrow_mut().clear(); }"
        if list_marker == "__LIST_EXTEND__":
            if len(args) >= 1 and isinstance(args[0], dict):
                arg_rt = _resolved_type_in_context(ctx, args[0])
                if arg_rt.startswith("list[") or arg_rt == "list" or arg_rt in ("bytes", "bytearray"):
                    return raw_obj_str + ".py_borrow_mut().extend(" + rendered_args[0] + ".iter_snapshot())"
            return raw_obj_str + ".py_borrow_mut().extend(" + ", ".join(rendered_args) + ")"
        if list_marker == "__LIST_INSERT__":
            if len(rendered_args) >= 2:
                return raw_obj_str + ".py_borrow_mut().insert(" + rendered_args[0] + " as usize, " + rendered_args[1] + ")"
        if list_marker == "__LIST_REMOVE__":
            return "{ let __remove_val = " + rendered_args[0] + "; let mut __v = " + raw_obj_str + ".py_borrow_mut(); if let Some(pos) = __v.iter().position(|x| *x == __remove_val) { __v.remove(pos); } }"
        if list_marker == "py_index":
            return raw_obj_str + ".py_borrow().iter().position(|x| *x == " + rendered_args[0] + ").unwrap_or(usize::MAX) as i64"
        if list_marker == "__LIST_COUNT__":
            return raw_obj_str + ".py_borrow().iter().filter(|x| **x == " + rendered_args[0] + ").count() as i64"
        if list_marker == "py_sort":
            return "{ " + raw_obj_str + ".py_borrow_mut().sort(); }"
        if list_marker == "py_reverse":
            return "{ " + raw_obj_str + ".py_borrow_mut().reverse(); }"
        if list_marker == "__LIST_COPY__":
            return raw_obj_str + ".clone()"

    # str methods (on &str or String)
    if obj_type == "str":
        if method == "format":
            # Basic: emit format!(...) - simplified
            return "format!(\"...\", " + ", ".join(rendered_args) + ")"
        if str_marker != "":
            if str_marker in ("py_str_strip", "py_str_lstrip", "py_str_rstrip") and len(rendered_args) >= 1:
                return str_marker + "_chars(" + ", ".join(["&" + obj_str] + rendered_args) + ")"
            if str_marker == "py_str_split" and len(rendered_args) >= 2:
                return "py_str_split_n(" + ", ".join(["&" + obj_str, "&" + rendered_args[0], "&" + rendered_args[1]]) + ")"
            rendered_str_args = [a if a.startswith("&") else "&" + a for a in rendered_args]
            return str_marker + "(" + ", ".join(["&" + obj_str] + rendered_str_args) + ")"

    # JsonVal method calls (JsonVal → PyAny, dict-like .get())
    if obj_type == "JsonVal":
        if method == "get":
            key = rendered_args[0] if rendered_args else '""'
            return obj_str + ".pyany_get(&" + key + ")"

    # dict methods
    is_dict_obj = obj_type.startswith("dict[") or obj_type == "dict" or inferred_obj_rs.startswith("HashMap<") or inferred_obj_rs.startswith("BTreeMap<")
    if is_dict_obj:
        if method == "get":
            # Check if actual variable is dynamic (JsonVal/PyAny) — EAST3 may have narrowed the type
            # but the Rust variable is actually PyAny, needing py_any_as_hashmap conversion
            _actual_rt = (ctx.var_types.get(obj_id, "") or obj_type) if obj_id else obj_type
            _call_result_type = _str(call_node, "resolved_type")
            _call_result_is_pyany = _rs_type_for_context(ctx, _call_result_type) == "PyAny" or "|" in _call_result_type
            _is_dynamic_var = _actual_rt in ("JsonVal", "Any", "object", "Obj")
            if not _is_dynamic_var:
                _is_dynamic_var = "JsonVal" in _actual_rt and "dict[" not in _actual_rt.split("|")[0].strip()[:10]
            if not _is_dynamic_var:
                _is_dynamic_var = "|" in _actual_rt and "JsonVal" in _actual_rt
            if _is_dynamic_var:
                _key = rendered_args[0] if rendered_args else '""'
                _default = rendered_args[1] if len(rendered_args) >= 2 else "PyAny::None"
                if len(args) >= 2 and isinstance(args[1], dict):
                    _default = _expr_to_pyany(_default, _str(args[1], "resolved_type"))
                _unwrap = "clone().unwrap_or(PyAny::None)" if "|" in _actual_rt else "clone()"
                return "py_any_as_hashmap(" + obj_str + "." + _unwrap + ").get(&" + _key + ").cloned().unwrap_or(" + _default + ")"
            if len(rendered_args) >= 2:
                default_expr = rendered_args[1]
                value_is_pyany = False
                if obj_type.startswith("dict[") and obj_type.endswith("]"):
                    _inner = obj_type[5:-1]
                    _parts: list[str] = _split_generic_args(_inner)
                    value_is_pyany = len(_parts) == 2 and (
                        _rs_type_for_context(ctx, _parts[1]) == "PyAny" or "|" in _parts[1]
                    )
                elif inferred_obj_rs.startswith("HashMap<") or inferred_obj_rs.startswith("BTreeMap<"):
                    value_is_pyany = inferred_obj_rs.endswith(", PyAny>") or ", PyAny," in inferred_obj_rs
                if (value_is_pyany or _call_result_is_pyany) and len(args) >= 2 and isinstance(args[1], dict):
                    if _str(args[1], "kind") == "Dict" and len(_list(args[1], "entries")) == 0:
                        default_expr = "PyAny::Dict(BTreeMap::new())"
                    else:
                        default_expr = _expr_to_pyany(default_expr, _str(args[1], "resolved_type"))
                return obj_str + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(" + default_expr + ")"
            elif len(rendered_args) == 1:
                # For dict[K, PyAny] return PyAny::None as default instead of Option<PyAny>
                value_is_pyany = False
                if obj_type.startswith("dict[") and obj_type.endswith("]"):
                    _inner = obj_type[5:-1]
                    _parts: list[str] = _split_generic_args(_inner)
                    value_is_pyany = len(_parts) == 2 and (
                        _rs_type_for_context(ctx, _parts[1]) == "PyAny" or "|" in _parts[1]
                    )
                elif inferred_obj_rs.startswith("HashMap<") or inferred_obj_rs.startswith("BTreeMap<"):
                    value_is_pyany = inferred_obj_rs.endswith(", PyAny>") or ", PyAny," in inferred_obj_rs
                if value_is_pyany or _call_result_is_pyany:
                    return obj_str + ".get(&" + rendered_args[0] + ").cloned().unwrap_or(PyAny::None)"
                return obj_str + ".get(&" + rendered_args[0] + ").cloned()"
        if dict_marker == "__DICT_KEYS__":
            return "PyList::from_vec(" + obj_str + ".keys().cloned().collect())"
        if dict_marker == "__DICT_VALUES__":
            return "PyList::from_vec(" + obj_str + ".values().cloned().collect())"
        if dict_marker == "__DICT_ITEMS__":
            item_value_rs = "PyAny"
            if obj_type.startswith("dict[") and obj_type.endswith("]"):
                dict_parts: list[str] = _split_generic_args(obj_type[5:-1])
                if len(dict_parts) == 2:
                    item_value_rs = _rs_type_for_context(ctx, dict_parts[1].strip())
            elif inferred_obj_rs.startswith("HashMap<") and inferred_obj_rs.endswith(">"):
                dict_parts: list[str] = _split_generic_args(inferred_obj_rs[len("HashMap<"):-1])
                if len(dict_parts) == 2:
                    item_value_rs = dict_parts[1].strip()
            elif inferred_obj_rs.startswith("BTreeMap<") and inferred_obj_rs.endswith(">"):
                dict_parts: list[str] = _split_generic_args(inferred_obj_rs[len("BTreeMap<"):-1])
                if len(dict_parts) == 2:
                    item_value_rs = dict_parts[1].strip()
            return (
                "PyList::from_vec("
                + obj_str
                + ".iter().map(|(k, v): (&String, &"
                + item_value_rs
                + ")| (k.clone(), v.clone())).collect::<Vec<(String, "
                + item_value_rs
                + ")>>())"
            )
        if dict_marker == "py_pop":
            if len(rendered_args) >= 1:
                return obj_str + ".remove(&" + rendered_args[0] + ").unwrap_or_default()"
        if dict_marker == "py_setdefault" and len(rendered_args) >= 2:
            return "py_setdefault(&mut " + obj_str + ", " + rendered_args[0] + ", " + rendered_args[1] + ")"
        if dict_marker == "__DICT_UPDATE__":
            return "{ for (k, v) in " + rendered_args[0] + ".iter() { " + obj_str + ".insert(k.clone(), v.clone()); } }"
        if dict_marker == "py_clear":
            return "{ " + obj_str + ".clear(); }"
        if dict_marker == "__DICT_INSERT__" and len(rendered_args) >= 2:
            insert_val = rendered_args[1]
            if len(args) >= 2 and isinstance(args[1], dict) and _str(args[1], "kind") == "Name":
                insert_rt = _infer_node_rust_type(ctx, args[1]) or _rs_type_for_context(ctx, _actual_type_in_context(ctx, args[1]))
                if (
                    insert_rt == "String"
                    or insert_rt == "PyAny"
                    or insert_rt.startswith("HashMap<")
                    or insert_rt.startswith("HashSet<")
                    or insert_rt.startswith("PyList<")
                    or insert_rt.startswith("VecDeque<")
                    or insert_rt.startswith("Rc<RefCell<")
                    or insert_rt.startswith("Box<")
                ):
                    insert_val = insert_val + ".clone()"
            return obj_str + ".insert(" + rendered_args[0] + ", " + insert_val + ")"

    # set methods
    if obj_type.startswith("set[") or obj_type == "set":
        if set_marker == "__SET_ADD__":
            return obj_str + ".insert(" + ", ".join(rendered_args) + ")"
        if set_marker == "py_set_update" and len(rendered_args) == 1:
            if len(args) == 1:
                update_arg = args[0]
                if isinstance(update_arg, dict) and _str(update_arg, "kind") == "List":
                    elements = _json_get(update_arg, "elements")
                    if isinstance(elements, list) and len(elements) == 0:
                        return "()"
                if isinstance(update_arg, dict) and _str(update_arg, "resolved_type").startswith("set["):
                    return obj_str + ".extend(" + rendered_args[0] + ".iter().cloned())"
            return "py_set_update(&mut " + obj_str + ", " + rendered_args[0] + ")"
        if set_marker in ("py_remove", "py_discard"):
            return obj_str + ".remove(&" + rendered_args[0] + ")"
        if set_marker == "py_clear":
            return obj_str + ".clear()"
        if set_marker == "__SET_UNION__":
            return obj_str + ".union(&" + rendered_args[0] + ").cloned().collect::<HashSet<_>>()"
        if set_marker == "__SET_INTERSECTION__":
            return obj_str + ".intersection(&" + rendered_args[0] + ").cloned().collect::<HashSet<_>>()"

    # deque methods — lower to VecDeque<PyAny> primitives
    if obj_type == "deque":
        if deque_marker == "__DEQUE_APPEND__" and len(rendered_args) == 1:
            return obj_str + ".push_back(PyAny::Int(py_int(&" + rendered_args[0] + ")))"
        if deque_marker == "__DEQUE_APPENDLEFT__" and len(rendered_args) == 1:
            return obj_str + ".push_front(PyAny::Int(py_int(&" + rendered_args[0] + ")))"
        if deque_marker == "__DEQUE_POPLEFT__":
            return obj_str + ".pop_front().map(|v| py_int(&v)).unwrap_or_else(|| panic!(\"pop from empty deque\"))"
        if deque_marker == "__DEQUE_POP__":
            return obj_str + ".pop_back().map(|v| py_int(&v)).unwrap_or_else(|| panic!(\"pop from empty deque\"))"
        if deque_marker == "__DEQUE_LEN__":
            return obj_str + ".len()"
        if deque_marker == "__DEQUE_CLEAR__":
            return "{ " + obj_str + ".clear(); }"
        all_args_str = ", ".join(rendered_args)
        return obj_str + "." + safe_rs_ident(method) + "(" + all_args_str + ")"

    # Generic method call
    all_args_str = ", ".join(rendered_args)

    path_like_types = {obj_type, obj_actual_type, _resolved_type_in_context(ctx, obj)}
    if _path_like_types_have(ctx, path_like_types) or _is_path_rust_type(ctx, inferred_obj_rs):
        if method == "read_text":
            return obj_str + ".read_text()"
        if method == "write_text" and len(rendered_args) >= 1:
            return obj_str + ".write_text(" + rendered_args[0] + ")"
        if method == "mkdir":
            if len(rendered_args) >= 2:
                return obj_str + ".mkdir(" + rendered_args[0] + ", " + rendered_args[1] + ")"
            if len(rendered_args) == 1:
                return obj_str + ".mkdir(" + rendered_args[0] + ", false)"
            return obj_str + ".mkdir(false, false)"

    return obj_str + "." + safe_rs_ident(method) + "(" + all_args_str + ")"


def _coerce_call_arg_to_expected(
    ctx: RsEmitContext,
    arg_node: JsonVal,
    arg_code: str,
    expected_type: str,
    *,
    prefer_into_py_box_any: bool = False,
) -> str:
    def _strip_unbox_expect(expr: str) -> str:
        suffix = '.expect("unbox")'
        if expr.endswith(suffix):
            return expr[:-len(suffix)]
        return expr

    if expected_type == "" or not isinstance(arg_node, dict):
        return arg_code
    actual_type = _actual_type_in_context(ctx, arg_node)
    effective_node = arg_node
    arg_kind = _str(arg_node, "kind")
    if arg_kind == "Box" or arg_kind == "Unbox":
        inner_node = arg_node.get("value")
        if isinstance(inner_node, dict):
            effective_node = inner_node
            inner_type = _actual_type_in_context(ctx, inner_node)
            if inner_type == "":
                inner_type = _resolved_type_in_context(ctx, inner_node)
            if inner_type != "":
                actual_type = inner_type
    expected_rs = _rs_type_for_context(ctx, expected_type)
    actual_rs = _rs_type_for_context(ctx, actual_type) if actual_type != "" else ""
    if actual_rs == "":
        actual_rs = _infer_node_rust_type(ctx, effective_node)
    if "None" in expected_type and ((_str(effective_node, "kind") == "Constant" and effective_node.get("value") is None) or arg_code == "PyAny::None" or arg_code == "None"):
        union_parts0: list[str] = []
        if "|" in expected_type:
            for raw_part in expected_type.split("|"):
                union_parts0.append(raw_part.strip())
        non_none_parts0: list[str] = []
        for part in union_parts0:
            if part != "None":
                non_none_parts0.append(part)
        lowers_to_pyany = (
            "|" in expected_type
            and "None" in union_parts0
            and len(non_none_parts0) >= 1
            and not (len(non_none_parts0) == 1)
            and _union_parts_lower_to_pyany(non_none_parts0)
        )
        if expected_rs == "PyAny" or lowers_to_pyany:
            return "PyAny::None"
        return "None"
    if "|" in expected_type:
        union_parts: list[str] = []
        for raw_part in expected_type.split("|"):
            union_parts.append(raw_part.strip())
        non_none_parts: list[str] = []
        for part in union_parts:
            if part != "None":
                non_none_parts.append(part)
        is_simple_optional = ("None" in union_parts and len(non_none_parts) == 1)
        if (not is_simple_optional) and _union_parts_lower_to_pyany(union_parts):
            expected_rs = "PyAny"
    if expected_rs == "PyAny":
        is_none_literal = _str(effective_node, "kind") == "Constant" and effective_node.get("value") is None
        if is_none_literal or arg_code == "None":
            return "PyAny::None"
        if _str(effective_node, "kind") == "Dict" and len(_list(effective_node, "entries")) == 0:
            return "PyAny::Dict(BTreeMap::new())"
        if _str(effective_node, "kind") == "List" and len(_list(effective_node, "elements")) == 0:
            return "PyAny::List(Vec::new())"
        if arg_code.startswith("PyAny::"):
            return arg_code
        if actual_rs == "PyAny":
            return arg_code
        if actual_rs.startswith("HashMap<"):
            parts: list[str] = []
            if actual_type.startswith("dict[") and actual_type.endswith("]"):
                parts = _split_generic_args(actual_type[5:-1])
            value_type = parts[1].strip() if len(parts) == 2 else "Any"
            boxed_value = _expr_to_pyany("__v", value_type)
            return "PyAny::Dict(" + arg_code + ".into_iter().map(|(__k, __v)| (__k, " + boxed_value + ")).collect::<BTreeMap<_, _>>())"
        if actual_rs.startswith("PyList<"):
            inner_type = actual_type[5:-1].strip() if actual_type.startswith("list[") and actual_type.endswith("]") else ""
            if inner_type in ("", "Any", "object", "Obj", "JsonVal"):
                return "PyAny::List(" + arg_code + ".iter_snapshot().into_iter().collect())"
            boxed_elem = _expr_to_pyany("__v", inner_type)
            return "PyAny::List(" + arg_code + ".iter_snapshot().into_iter().map(|__v| " + boxed_elem + ").collect())"
        return _expr_to_pyany(arg_code, actual_type)
    if expected_rs.startswith("HashMap<") and arg_code.startswith("PyAny::Dict("):
        return "py_any_as_hashmap(" + arg_code + ")"
    if expected_rs.startswith("PyList<") and arg_code.startswith("PyAny::List("):
        return "py_any_as_list(" + arg_code + ")"
    if (
        expected_rs == "PyPath"
        and not arg_code.startswith("*")
        and ".joinpath(" in arg_code
        and (
            not isinstance(effective_node, dict)
            or _str(effective_node, "kind") != "Name"
            or _rs_type_for_context(ctx, ctx.var_types.get(_str(effective_node, "id"), "")) != "PyPath"
        )
        and (actual_rs == "Box<PyPath>" or _infer_node_rust_type(ctx, effective_node) == "Box<PyPath>")
    ):
        return "*" + arg_code
    if actual_rs.startswith("Option<") and not expected_rs.startswith("Option<"):
        if '.expect("unbox")' in arg_code or '.expect("assignment unwrap")' in arg_code:
            return arg_code
        if ".unwrap_or_default()" in arg_code or ".unwrap_or(" in arg_code:
            return arg_code
        inner_rs = actual_rs[len("Option<"):-1] if actual_rs.endswith(">") else ""
        if expected_rs == inner_rs or expected_rs in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32", "bool", "String"):
            return arg_code + '.clone().expect("unbox")'
    if actual_rs == "PyAny":
        if expected_rs == "String":
            return "py_str(&(" + arg_code + "))"
        if expected_rs == "bool":
            return "py_bool(&(" + arg_code + "))"
        if expected_rs.startswith("PyList<"):
            inner_rs = expected_rs[len("PyList<"):-1]
            return "py_any_as_list_typed::<" + inner_rs + ">(" + arg_code + ".clone())"
        if expected_rs.startswith("HashMap<"):
            inner = expected_rs[len("HashMap<"):-1]
            parts: list[str] = _split_generic_args(inner)
            value_rs = parts[1] if len(parts) == 2 else "PyAny"
            return "py_any_as_hashmap_typed::<" + value_rs + ">(" + arg_code + ".clone())"
        if expected_rs in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8"):
            return _apply_cast("py_int(&(" + arg_code + "))", expected_type)
        if expected_rs in ("f64", "f32"):
            return _apply_cast("py_float(&(" + arg_code + "))", expected_type)
    if expected_rs.startswith("Option<Box<dyn Fn"):
        is_none = _str(arg_node, "kind") == "Constant" and arg_node.get("value") is None
        if is_none or arg_code == "None":
            return "None"
        if arg_code.startswith("Some("):
            return arg_code
        if arg_code.startswith("Box::new("):
            return "Some(" + arg_code + ")"
        return "Some(Box::new(" + arg_code + "))"
    if expected_rs.startswith("Box<dyn Fn") and not arg_code.startswith("Box::new("):
        return "Box::new(" + arg_code + ")"
    if expected_rs.startswith("Option<") and arg_code.endswith('.expect("unbox")'):
        return "Some(" + _strip_unbox_expect(arg_code) + ")"
    if expected_rs.startswith("Option<") and not actual_rs.startswith("Option<"):
        is_none = _str(arg_node, "kind") == "Constant" and arg_node.get("value") is None
        if is_none:
            return "None"
        if arg_code == "None" or arg_code.startswith("Some("):
            return arg_code
        return "Some(" + _strip_unbox_expect(arg_code) + ")"
    if expected_rs == "Box<dyn std::any::Any>" and actual_rs != "Box<dyn std::any::Any>" and not arg_code.startswith("Box::new("):
        if prefer_into_py_box_any:
            if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Name":
                if actual_rs == "" or not _rs_is_copy_type(actual_rs):
                    return arg_code + ".clone()"
            return arg_code
        boxed = arg_code
        if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Name":
            if actual_rs == "" or not _rs_is_copy_type(actual_rs):
                boxed = arg_code + ".clone()"
        return "Box::new(" + boxed + ") as Box<dyn std::any::Any>"
    return arg_code


def _normalize_rendered_arg_for_expected_rs(arg_code: str, expected_rs: str) -> str:
    if expected_rs == "":
        return arg_code
    if expected_rs.startswith("HashMap<") and arg_code.startswith("PyAny::Dict("):
        return "py_any_as_hashmap(" + arg_code + ")"
    if expected_rs.startswith("PyList<") and arg_code.startswith("PyAny::List("):
        return "py_any_as_list(" + arg_code + ")"
    if expected_rs.startswith("Option<Box<dyn Fn"):
        if arg_code == "None":
            return "None"
        if arg_code.startswith("Some("):
            return arg_code
        if arg_code.startswith("Box::new("):
            return "Some(" + arg_code + ")"
        return "Some(Box::new(" + arg_code + "))"
    if expected_rs.startswith("Option<") and arg_code.endswith('.expect("unbox")'):
        return "Some(" + arg_code[: -len('.expect("unbox")')] + ")"
    if not expected_rs.startswith("Option<") and arg_code.startswith("Some(") and arg_code.endswith(")"):
        return arg_code[5:-1]
    return arg_code


def _sig_param_uses_into_py_box_any(
    ctx: RsEmitContext,
    sig: dict[str, JsonVal],
    param_name: str,
    *,
    skip_self: bool,
) -> bool:
    owner = _str(sig, "owner")
    arg_order: list[str] = []
    for p in _list(sig, "arg_order"):
        if isinstance(p, str):
            arg_order.append(p)
    if skip_self and len(arg_order) > 0 and arg_order[0] == "self":
        arg_order = arg_order[1:]
    is_nested = _str(sig, "kind") == "ClosureDef" or (_str(sig, "kind") == "FunctionDef" and owner == "" and bool(_dict(sig, "capture_types")))
    if is_nested:
        return False
    arg_types = _dict(sig, "arg_types")
    return _rs_type_for_context(ctx, _str(arg_types, param_name)) == "Box<dyn std::any::Any>"


def _build_sig_call_args(
    ctx: RsEmitContext,
    args: list[JsonVal],
    rendered_args: list[str],
    keywords: list[JsonVal],
    sig: dict[str, JsonVal],
    *,
    skip_self: bool = False,
    force_into_py_box_any: bool = False,
) -> list[str]:
    arg_order: list[str] = []
    for p in _list(sig, "arg_order"):
        if isinstance(p, str):
            arg_order.append(p)
    arg_types = _dict(sig, "arg_types")
    arg_defaults = _dict(sig, "arg_defaults")
    vararg_name = _str(sig, "vararg_name")
    vararg_type = _str(sig, "vararg_type")
    if skip_self and len(arg_order) > 0 and arg_order[0] == "self":
        arg_order = arg_order[1:]

    kw_nodes: dict[str, JsonVal] = {}
    kw_rendered: dict[str, str] = {}
    extra_args: list[str] = []
    for kw in keywords:
        if not isinstance(kw, dict):
            continue
        kw_name = _str(kw, "arg")
        kw_val = kw.get("value")
        if kw_name != "" and kw_val is not None:
            kw_nodes[kw_name] = kw_val
            kw_rendered[kw_name] = _emit_call_arg(ctx, kw_val)
        elif kw_val is not None:
            extra_args.append(_emit_call_arg(ctx, kw_val))

    out: list[str] = []
    positional_index = 0
    for param_name in arg_order:
        arg_node: JsonVal = None
        arg_code = ""
        if positional_index < len(args):
            arg_node = args[positional_index]
            arg_code = rendered_args[positional_index] if positional_index < len(rendered_args) else ""
            positional_index += 1
        elif param_name in kw_nodes:
            arg_node = kw_nodes[param_name]
            arg_code = kw_rendered.get(param_name, "")
        elif param_name in arg_defaults:
            arg_node = arg_defaults[param_name]
            arg_code = _emit_expr(ctx, arg_node)
        else:
            continue
        expected_type = _str(arg_types, param_name)
        coerced_arg = _normalize_rendered_arg_for_expected_rs(
            _coerce_call_arg_to_expected(
                ctx,
                arg_node,
                arg_code,
                expected_type,
                prefer_into_py_box_any=(
                    force_into_py_box_any
                    and _rs_type_for_context(ctx, expected_type) == "Box<dyn std::any::Any>"
                ) or _sig_param_uses_into_py_box_any(ctx, sig, param_name, skip_self=skip_self),
            ),
            _rs_type_for_context(ctx, expected_type),
        )
        sig_is_nested = _str(sig, "kind") == "ClosureDef" or (_str(sig, "kind") == "FunctionDef" and _str(sig, "owner") == "")
        if sig_is_nested and _is_callable_resolved_type(expected_type):
            if coerced_arg.startswith("Box::new(") and coerced_arg.endswith(")"):
                coerced_arg = coerced_arg[len("Box::new("):-1]
            if not coerced_arg.startswith("&"):
                coerced_arg = "&" + coerced_arg
        out.append(
            coerced_arg
        )
    if vararg_name != "":
        expected_type = vararg_type
        if (
            positional_index == len(arg_order)
            and len(args) == len(arg_order) + 1
            and isinstance(args[-1], dict)
            and _str(args[-1], "kind") == "List"
        ):
            list_arg = args[-1]
            list_rt = _str(list_arg, "resolved_type")
            if expected_type != "" and list_rt == "list[" + expected_type + "]":
                list_code = rendered_args[-1] if len(rendered_args) >= 1 else _emit_call_arg(ctx, list_arg)
                out.append(list_code)
                extra_args = []
                return out
        vararg_elems: list[str] = []
        while positional_index < len(args):
            arg_node = args[positional_index]
            arg_code = rendered_args[positional_index] if positional_index < len(rendered_args) else _emit_call_arg(ctx, arg_node)
            vararg_elems.append(_coerce_call_arg_to_expected(ctx, arg_node, arg_code, expected_type))
            positional_index += 1
        for extra in extra_args:
            vararg_elems.append(extra)
        elem_rs = _rs_type_for_context(ctx, expected_type) if expected_type != "" else "Box<dyn std::any::Any>"
        if elem_rs == "Box<dyn std::any::Any>":
            out.append("vec![" + ", ".join(vararg_elems) + "]")
        else:
            out.append("PyList::<" + elem_rs + ">::from_vec(vec![" + ", ".join(vararg_elems) + "])")
        extra_args = []
    out.extend(extra_args)
    return out


def _emit_constructor_call(
    ctx: RsEmitContext,
    class_name: str,
    args: list[JsonVal],
    keywords: list[JsonVal],
    node: dict[str, JsonVal],
) -> str:
    def _strip_box_any(expr: str) -> str:
        prefix = "Box::new("
        suffix = ") as Box<dyn std::any::Any>"
        if expr.startswith(prefix) and expr.endswith(suffix):
            return expr[len(prefix):-len(suffix)]
        return expr

    def _collect_name_refs(expr: JsonVal) -> set[str]:
        refs: set[str] = set()
        if not isinstance(expr, dict):
            return refs
        if _str(expr, "kind") == "Name":
            name = _str(expr, "id")
            if name != "":
                refs.add(name)
            return refs
        for value in expr.values():
            if isinstance(value, dict):
                refs.update(_collect_name_refs(value))
            elif isinstance(value, list):
                for item in value:
                    refs.update(_collect_name_refs(item))
        return refs

    def _needs_clone_for_reuse(type_name: str) -> bool:
        return (
            type_name == "str"
            or type_name in ctx.class_names
            or type_name.startswith("list[") or type_name == "list"
            or type_name.startswith("dict[") or type_name == "dict"
            or type_name.startswith("set[") or type_name == "set"
            or type_name in ("bytes", "bytearray")
        )

    if class_name == "RuntimeError":
        msg = _emit_call_arg(ctx, args[0]) if len(args) >= 1 else '"RuntimeError".to_string()'
        return "std::io::Error::new(std::io::ErrorKind::Other, " + msg + ")"

    imported_fields = ctx.imported_class_fields.get(class_name, {})
    if class_name in ctx.imported_symbol_names and len(imported_fields) > 0:
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(_emit_call_arg(ctx, arg))
        field_list: list[str] = []
        for field_name in imported_fields:
            field_list.append(field_name)
        normalized_args: list[str] = []
        for index, rendered_arg in enumerate(rendered_args):
            if index < len(field_list):
                field_type = imported_fields.get(field_list[index], "")
                if field_type != "":
                    rendered_arg = _normalize_rendered_arg_for_expected_rs(
                        _coerce_call_arg_to_expected(ctx, args[index], rendered_arg, field_type),
                        _rs_type_for_context(ctx, field_type),
                    )
            normalized_args.append(rendered_arg)
        for index in range(len(normalized_args), len(field_list)):
            normalized_args.append(_rs_zero_value_for_context(ctx, imported_fields[field_list[index]]))
        ctor = safe_rs_ident(class_name) + "::new(" + ", ".join(normalized_args) + ")"
        if ctx.imported_symbol_storage_hints.get(class_name) == "ref" or _str(node, "resolved_storage_hint") == "ref":
            return "Rc::new(RefCell::new(" + ctor + "))"
        return "Box::new(" + ctor + ")"

    if _is_path_type_name(ctx, class_name) or _rs_type_for_context(ctx, class_name) == ctx.mapping.predicate_types.get("path_like", ""):
        path_rendered = _emit_call_arg(ctx, args[0]) if len(args) >= 1 else '""'
        return "PyPath::new(" + path_rendered + ")"
    if class_name == "CommonRendererState":
        cr_rendered: list[str] = []
        for arg in args:
            cr_rendered.append(_emit_call_arg(ctx, arg))
        if len(cr_rendered) < 1:
            cr_rendered.append("0_i64")
        if len(cr_rendered) < 2:
            cr_rendered.append("PyList::<String>::new()")
        else:
            cr_rendered[1] = _coerce_call_arg_to_expected(ctx, args[1], cr_rendered[1], "list[str]") if len(args) >= 2 else cr_rendered[1]
            if (
                len(args) >= 2
                and isinstance(args[1], dict)
                and _str(args[1], "kind") == "List"
                and len(_list(args[1], "elts")) == 0
            ):
                cr_rendered[1] = "PyList::<String>::new()"
            if cr_rendered[1].startswith("PyList::<Box<dyn std::any::Any>>::new()"):
                cr_rendered[1] = "PyList::<String>::new()"
        if len(cr_rendered) < 3:
            cr_rendered.append("0_i64")
        cr_first_three: list[str] = []
        for cr_index in range(0, 3):
            cr_first_three.append(cr_rendered[cr_index])
        return "Rc::new(RefCell::new(CommonRendererState::new(" + ", ".join(cr_first_three) + ")))"

    future_name_refs: list[set[str]] = []
    for arg in args:
        future_name_refs.append(_collect_name_refs(arg))
    kw_map: dict[str, str] = {}
    for kw in keywords:
        if not isinstance(kw, dict):
            continue
        kw_name = _str(kw, "arg")
        kw_val = kw.get("value")
        if kw_name != "" and kw_val is not None:
            kw_map[kw_name] = _emit_call_arg(ctx, kw_val)
    rendered_args: list[str] = []
    index = 0
    for arg_node in args:
        rendered_arg = _emit_call_arg(ctx, arg_node)
        if isinstance(arg_node, dict) and _str(arg_node, "kind") == "Name":
            name = _str(arg_node, "id")
            resolved = _actual_type_in_context(ctx, arg_node)
            later_refs: set[str] = set()
            for refs_index in range(index + 1, len(future_name_refs)):
                refs = future_name_refs[refs_index]
                later_refs.update(refs)
            if name != "" and name in later_refs and _needs_clone_for_reuse(resolved):
                    rendered_arg = rendered_arg + ".clone()"
        rendered_args.append(rendered_arg)
        index += 1
    rs_name = safe_rs_ident(class_name)
    init_method = ctx.class_instance_methods.get(class_name, {}).get("__init__")
    if init_method is not None:
        rendered_args = _build_sig_call_args(
            ctx,
            args,
            rendered_args,
            keywords,
            init_method,
            skip_self=True,
            force_into_py_box_any=True,
        )
        init_arg_order: list[str] = []
        for p in _list(init_method, "arg_order"):
            p_text = _as_str(p)
            if p_text != "" and p_text != "self":
                init_arg_order.append(p_text)
        init_arg_types = _dict(init_method, "arg_types")
        normalized_args: list[str] = []
        class_fields = ctx.class_fields.get(class_name, {})
        for index, rendered_arg in enumerate(rendered_args):
            if index < len(init_arg_order):
                param_name = init_arg_order[index]
                expected_type = _str(init_arg_types, param_name)
                field_type = class_fields.get(param_name, "")
                if field_type != "":
                    expected_type = field_type
                if _rs_type_for_context(ctx, expected_type) == "Box<dyn std::any::Any>":
                    normalized_args.append(_strip_box_any(rendered_arg))
                    continue
                if index < len(args):
                    normalized_args.append(_normalize_rendered_arg_for_expected_rs(
                        _coerce_call_arg_to_expected(
                            ctx,
                            args[index],
                            rendered_arg,
                            expected_type,
                        ),
                        _rs_type_for_context(ctx, expected_type),
                    ))
                    continue
            normalized_args.append(rendered_arg)
        rendered_args = normalized_args
    else:
        # No __init__ (dataclass-style): use fields and defaults to fill positional args
        fields = ctx.class_fields.get(class_name, {})
        defaults = ctx.class_field_defaults.get(class_name, {})
        field_list: list[str] = []
        for field_name in fields:
            field_list.append(field_name)
        if len(field_list) > 0:
            full_args2: list[str] = []
            for i, rendered_arg in enumerate(rendered_args):
                if i < len(field_list) and i < len(args):
                    field_type = fields.get(field_list[i], "")
                    if field_type != "":
                        rendered_arg = _normalize_rendered_arg_for_expected_rs(
                            _coerce_call_arg_to_expected(
                                ctx,
                                args[i],
                                rendered_arg,
                                field_type,
                            ),
                            _rs_type_for_context(ctx, field_type),
                        )
                full_args2.append(rendered_arg)
            for i, field_name in enumerate(field_list):
                if i < len(full_args2):
                    continue
                if field_name in kw_map:
                    full_args2.append(kw_map[field_name])
                else:
                    default_val = defaults.get(field_name)
                    if default_val is not None:
                        full_args2.append(default_val)
                    else:
                        full_args2.append(_rs_zero_value_for_context(ctx, fields[field_name]))
            rendered_args = full_args2
    ctor = rs_name + "::new(" + ", ".join(rendered_args) + ")"
    resolved_storage_hint = _str(node, "resolved_storage_hint")
    if class_name in ctx.ref_classes or resolved_storage_hint == "ref":
        return "Rc::new(RefCell::new(" + ctor + "))"
    return "Box::new(" + ctor + ")"


def _emit_expr_with_body_casts(ctx: RsEmitContext, node: JsonVal, result: str) -> str:
    """Apply 'on: body' casts from EAST3 node to the emitted expression."""
    if not isinstance(node, dict):
        return result
    casts = _list(node, "casts")
    for cast in casts:
        if not isinstance(cast, dict):
            continue
        on = _str(cast, "on")
        cast_to = _str(cast, "to")
        if on == "body" and cast_to != "":
            result = _apply_cast(result, cast_to)
    return result


def _emit_expr(ctx: RsEmitContext, node: JsonVal) -> str:
    if not isinstance(node, dict):
        return "_"
    kind = _str(node, "kind")
    if kind == "Constant":
        return _emit_constant(ctx, node)
    if kind == "Name":
        return _emit_name(ctx, node)
    if kind == "BinOp":
        return _emit_binop(ctx, node)
    if kind == "UnaryOp":
        return _emit_unaryop(ctx, node)
    if kind == "Compare":
        return _emit_compare(ctx, node)
    if kind == "BoolOp":
        return _emit_boolop(ctx, node)
    if kind == "Attribute":
        return _emit_attribute(ctx, node)
    if kind == "Call":
        return _emit_call(ctx, node)
    if kind == "List":
        return _emit_list_literal(ctx, node)
    if kind == "Dict":
        return _emit_dict_literal(ctx, node)
    if kind == "Set":
        return _emit_set_literal(ctx, node)
    if kind == "Tuple":
        return _emit_tuple_literal(ctx, node)
    if kind == "Subscript":
        return _emit_subscript(ctx, node)
    if kind == "IfExp":
        return _emit_ifexp(ctx, node)
    if kind == "Lambda":
        return _emit_lambda(ctx, node)
    if kind == "Box":
        return _emit_box(ctx, node)
    if kind == "JoinedStr":
        return _emit_fstring(ctx, node)
    if kind == "ObjTypeId":
        # Get runtime type ID of an object.
        val = node.get("value")
        value_type = _str(val, "resolved_type") if isinstance(val, dict) else ""
        inner = _emit_expr(ctx, val)
        # For PyAny typed values (object/Any/Obj), user classes are encoded as PyAny::TypeId.
        if value_type in ("object", "Any", "Obj"):
            return "(if let PyAny::TypeId(__tid) = &" + inner + " { *__tid } else { py_builtin_type_id_pyany(&" + inner + ") })"
        # For Box<dyn Any> (unknown / union types), use downcast chain to recover TID
        if value_type in ("unknown",) or value_type == "" or _rs_type_for_context(ctx, value_type) == "Box<dyn std::any::Any>":
            user_cls = _sorted_user_classes_desc(ctx)
            if user_cls:
                ref_inner = "&" + inner if not inner.startswith("&") else inner
                return _emit_obj_type_id_downcast(ctx, ref_inner, user_cls)
        return _builtin_type_id_expr(value_type)
    if kind == "IsInstance":
        return _emit_isinstance(ctx, node)
    if kind == "Unbox":
        # Unbox: converts a dynamic (Any/object/JsonVal) value to a static type.
        # EAST3 inserts Unbox nodes for isinstance-narrowed JsonVal/Any variables;
        # inner node carries the original (pre-narrowing) storage type.
        inner_node = node.get("value")
        inner_rt = ""
        lane = node.get("bridge_lane_v1")
        if isinstance(lane, dict):
            lane_value = lane.get("value")
            if isinstance(lane_value, dict):
                inner_rt = _str(lane_value, "mirror")
        if inner_rt in ("", "unknown") and isinstance(inner_node, dict):
            hinted_inner_rt = _str(inner_node, "resolved_type")
            if hinted_inner_rt not in ("", "unknown"):
                inner_rt = hinted_inner_rt
        if inner_rt == "":
            # Fall back to storage type when bridge metadata is absent.
            inner_rt = _actual_type_in_context(ctx, inner_node) if isinstance(inner_node, dict) else ""
        outer_rt = _str(node, "resolved_type")
        inner_expr = _emit_expr(ctx, inner_node)
        if isinstance(inner_node, dict) and _str(inner_node, "kind") == "Unbox":
            nested_rt = _str(inner_node, "resolved_type")
            if nested_rt == outer_rt or (outer_rt == "str" and inner_expr.endswith(".unwrap_or_default()")):
                return inner_expr
        if isinstance(inner_node, dict) and _str(inner_node, "kind") == "Name":
            storage_type = ctx.var_types.get(_str(inner_node, "id"), "")
            storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
            if storage_rs.startswith("Option<") and outer_rt not in ("", "Any", "object", "Obj", "JsonVal"):
                if outer_rt == "str":
                    return inner_expr + ".clone().unwrap_or_default()"
                if outer_rt in ("int64", "int", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8", "float64", "float32", "float", "bool"):
                    return inner_expr + '.clone().expect("unbox")'
            if storage_rs == "PyAny" and outer_rt != "":
                if outer_rt.startswith("list[") or outer_rt == "list":
                    elem_rs = _rs_type_for_context(ctx, outer_rt[5:-1].strip()) if outer_rt.startswith("list[") and outer_rt.endswith("]") else "PyAny"
                    return "py_any_as_list_typed::<" + elem_rs + ">(" + inner_expr + ".clone())"
                if outer_rt.startswith("dict["):
                    parts: list[str] = []
                    if outer_rt.endswith("]"):
                        parts = _split_generic_args(outer_rt[5:-1])
                    value_rs = "PyAny"
                    if len(parts) == 2:
                        value_rs = _rs_type_for_context(ctx, parts[1].strip())
                    return "py_any_as_hashmap_typed::<" + value_rs + ">(" + inner_expr + ".clone())"
                if outer_rt == "str":
                    return "py_str(&(" + inner_expr + ".clone()))"
                if outer_rt in ("int64", "int", "int32", "int16", "int8",
                                "uint64", "uint32", "uint16", "uint8"):
                    return "py_int(&(" + inner_expr + ".clone()))"
                if outer_rt in ("float64", "float32", "float"):
                    return "py_float(&(" + inner_expr + ".clone()))"
                if outer_rt == "bool":
                    return "py_bool(&(" + inner_expr + ".clone()))"
        if (
            isinstance(inner_node, dict)
            and _str(inner_node, "kind") == "Call"
            and outer_rt != ""
            and inner_rt == outer_rt
        ):
            return inner_expr
        if _is_callable_resolved_type(outer_rt) and isinstance(inner_node, dict) and _str(inner_node, "kind") == "Name":
            inner_name = _str(inner_node, "id")
            storage_type = ctx.var_types.get(inner_name, "")
            storage_rs = _rs_type_for_context(ctx, storage_type) if storage_type != "" else ""
            if storage_rs.startswith("Option<Box<dyn Fn"):
                return inner_expr + '.as_ref().expect("callable guard")'
        if isinstance(inner_node, dict) and _str(inner_node, "kind") == "BinOp" and outer_rt not in ("", "Any", "object", "Obj", "JsonVal"):
            return inner_expr

        _PYANY = ("Any", "object", "Obj", "JsonVal")
        inner_actual_rs = _infer_node_rust_type(ctx, inner_node) if isinstance(inner_node, dict) else ""
        outer_actual_rs = _rs_type_for_context(ctx, outer_rt) if outer_rt != "" else ""
        if inner_actual_rs != "" and inner_actual_rs == outer_actual_rs:
            return inner_expr
        # Handle Option<X> inner types (e.g. dict[str,JsonVal] | None)
        inner_base_rt = inner_rt
        needs_unwrap = False
        if (inner_rt.endswith(" | None") or inner_rt.endswith("|None")) and _rs_type_for_context(ctx, inner_rt).startswith("Option<"):
            inner_base_rt = inner_rt[:-7].strip() if inner_rt.endswith(" | None") else inner_rt[:-5].strip()
            needs_unwrap = True
        inner_base_is_dynamic = inner_base_rt in _PYANY
        is_dynamic_inner = (
            inner_base_is_dynamic
            or "JsonVal" in inner_base_rt
            or _rs_type_for_context(ctx, inner_base_rt) == "PyAny"
        )
        if is_dynamic_inner and outer_rt not in _PYANY and outer_rt != "":
            # Source expr: unwrap Option if needed, otherwise use directly
            if needs_unwrap:
                if inner_base_is_dynamic:
                    # Option<PyAny> → PyAny
                    src = inner_expr + ".clone().unwrap_or(PyAny::None)"
                else:
                    # Option<ConcreteType> → ConcreteType: already the right type
                    src = inner_expr + ".clone().unwrap_or_default()"
            else:
                src = inner_expr
            if outer_rt.startswith("list[") or outer_rt == "list":
                if needs_unwrap and not inner_base_is_dynamic:
                    # Already PyList — no conversion needed
                    return src
                clone_src = src if needs_unwrap else src + ".clone()"
                elem_rs = _rs_type_for_context(ctx, outer_rt[5:-1].strip()) if outer_rt.startswith("list[") and outer_rt.endswith("]") else "PyAny"
                return "py_any_as_list_typed::<" + elem_rs + ">(" + clone_src + ")"
            if outer_rt.startswith("dict["):
                if needs_unwrap and not inner_base_is_dynamic:
                    # Already HashMap — no conversion needed
                    return src
                clone_src = src if needs_unwrap else src + ".clone()"
                parts: list[str] = []
                if outer_rt.endswith("]"):
                    parts = _split_generic_args(outer_rt[5:-1])
                value_rs = "PyAny"
                if len(parts) == 2:
                    value_rs = _rs_type_for_context(ctx, parts[1].strip())
                return "py_any_as_hashmap_typed::<" + value_rs + ">(" + clone_src + ")"
            if outer_rt == "str":
                return "py_str(&" + src + ")"
            if outer_rt in ("int64", "int", "int32", "int16", "int8",
                            "uint64", "uint32", "uint16", "uint8"):
                return "py_int(&" + src + ")"
            if outer_rt in ("float64", "float32", "float"):
                return "py_float(&" + src + ")"
            if outer_rt == "bool":
                return "py_bool(&" + src + ")"
        # Handle Box<dyn Any> union types (e.g. int64|float64 → int64).
        # When the inner Rust type is Box<dyn Any> (a non-PyAny union type), emit a downcast.
        if not is_dynamic_inner and not needs_unwrap and outer_rt not in _PYANY and outer_rt != "":
            inner_rs = _rs_type_for_context(ctx, inner_base_rt)
            actual_inner_rs = _infer_node_rust_type(ctx, inner_node) if isinstance(inner_node, dict) else ""
            outer_rs = _rs_type_for_context(ctx, outer_rt)
            if (
                isinstance(inner_node, dict)
                and _str(inner_node, "kind") == "Call"
                and inner_expr != ""
                and not inner_expr.startswith("Box::new(")
                and ".downcast_ref::<" not in inner_expr
                and outer_rs in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32", "bool", "String")
            ):
                return inner_expr
            if actual_inner_rs != "" and actual_inner_rs == outer_rs:
                return inner_expr
            if inner_expr.startswith("py_any_as_") and outer_rs in ("i64", "i32", "i16", "i8", "u64", "u32", "u16", "u8", "f64", "f32", "bool", "String"):
                return inner_expr
            if actual_inner_rs == "PyAny":
                if outer_rt.startswith("list[") or outer_rt == "list":
                    elem_rs = _rs_type_for_context(ctx, outer_rt[5:-1].strip()) if outer_rt.startswith("list[") and outer_rt.endswith("]") else "PyAny"
                    return "py_any_as_list_typed::<" + elem_rs + ">(" + inner_expr + ".clone())"
                if outer_rt.startswith("dict["):
                    parts: list[str] = []
                    if outer_rt.endswith("]"):
                        parts = _split_generic_args(outer_rt[5:-1])
                    value_rs = "PyAny"
                    if len(parts) == 2:
                        value_rs = _rs_type_for_context(ctx, parts[1].strip())
                    return "py_any_as_hashmap_typed::<" + value_rs + ">(" + inner_expr + ".clone())"
                if outer_rt == "str":
                    return "py_str(&(" + inner_expr + ".clone()))"
                if outer_rt in ("int64", "int", "int32", "int16", "int8",
                                "uint64", "uint32", "uint16", "uint8"):
                    return "py_int(&(" + inner_expr + ".clone()))"
                if outer_rt in ("float64", "float32", "float"):
                    return "py_float(&(" + inner_expr + ".clone()))"
                if outer_rt == "bool":
                    return "py_bool(&(" + inner_expr + ".clone()))"
            if isinstance(inner_node, dict) and _str(inner_node, "kind") == "Call":
                call_func = inner_node.get("func")
                if isinstance(call_func, dict) and _str(call_func, "kind") == "Attribute":
                    owner = call_func.get("value")
                    owner_rt = _actual_type_in_context(ctx, owner)
                    method = _str(call_func, "attr")
                    owner_list_marker = ctx.mapping.calls.get("list." + method, "")
                    if (owner_rt.startswith("list[") or owner_rt == "list") and owner_list_marker == "__LIST_POP__":
                        return inner_expr
            if inner_rs == "Box<dyn std::any::Any>":
                if outer_rt in ctx.ref_classes:
                    return "(*" + inner_expr + ".downcast::<Rc<RefCell<" + safe_rs_ident(outer_rt) + ">>>().unwrap())"
                if outer_rt in ctx.class_names:
                    return "(*" + inner_expr + ".downcast::<Box<" + safe_rs_ident(outer_rt) + ">>().unwrap())"
                _BOX_ANY_DOWNCAST: dict[str, tuple[str, str]] = {}
                _BOX_ANY_DOWNCAST["int64"] = ("i64", "0")
                _BOX_ANY_DOWNCAST["int32"] = ("i32", "0")
                _BOX_ANY_DOWNCAST["int16"] = ("i16", "0")
                _BOX_ANY_DOWNCAST["int8"] = ("i8", "0")
                _BOX_ANY_DOWNCAST["uint64"] = ("u64", "0")
                _BOX_ANY_DOWNCAST["uint32"] = ("u32", "0")
                _BOX_ANY_DOWNCAST["uint16"] = ("u16", "0")
                _BOX_ANY_DOWNCAST["uint8"] = ("u8", "0")
                _BOX_ANY_DOWNCAST["float64"] = ("f64", "0.0")
                _BOX_ANY_DOWNCAST["float32"] = ("f32", "0.0")
                _BOX_ANY_DOWNCAST["bool"] = ("bool", "false")
                _BOX_ANY_DOWNCAST["str"] = ("String", "String::new()")
                narrow = _BOX_ANY_DOWNCAST.get(outer_rt)
                if narrow is not None:
                    rs_narrow, zero = narrow
                    if rs_narrow == "String":
                        return inner_expr + ".downcast_ref::<String>().cloned().unwrap_or_default()"
                    return inner_expr + ".downcast_ref::<" + rs_narrow + ">().copied().unwrap_or(" + zero + ")"
        if needs_unwrap and outer_rt != "":
            if outer_rt in _PYANY:
                return inner_expr + ".clone().unwrap_or(PyAny::None)"
            if inner_base_rt == outer_rt:
                return inner_expr + '.clone().expect("unbox")'
        return inner_expr
    if kind == "ListComp":
        return _emit_listcomp(ctx, node)
    if kind == "SetComp":
        return _emit_setcomp(ctx, node)
    if kind == "DictComp":
        return _emit_dictcomp(ctx, node)
    # Fallback: use repr if available (emit todo! so it compiles but panics at runtime)
    # Escape { and } since todo! uses them as format specifiers
    repr_str = _str(node, "repr")
    if repr_str != "":
        safe_repr = repr_str.replace('"', "'").replace("{", "{{").replace("}", "}}")
        return "todo!(\"unsupported: " + safe_repr + "\")"
    return "todo!(\"unsupported_expr:" + kind + "\")"


def _emit_comp_generators(ctx: RsEmitContext, generators: list[JsonVal], push_stmt: str) -> str:
    """Emit nested for/if loops for a comprehension, ending with push_stmt."""
    parts: list[str] = []
    close_count = 0
    for gen in generators:
        if not isinstance(gen, dict):
            continue
        target_node = gen.get("target")
        iter_node = gen.get("iter")
        ifs = gen.get("ifs")
        # Build target pattern (support tuple destructuring)
        if isinstance(target_node, dict) and _str(target_node, "kind") == "Tuple":
            # Try "elements" then "elts" (different EAST3 versions)
            tuple_elts = _list(target_node, "elements") or _list(target_node, "elts")
            names = [_str(e, "id") if isinstance(e, dict) else "_" for e in tuple_elts]
            target_name = "(" + ", ".join(names) + ")" if names else "_"
        else:
            target_name = _str(target_node, "id") if isinstance(target_node, dict) else "_"
        iter_expr = _emit_expr(ctx, iter_node)
        iter_type = _str(iter_node, "resolved_type") if isinstance(iter_node, dict) else ""
        if iter_type == "str":
            # Iterating over a string yields single-char strings
            iter_str = iter_expr + ".chars().map(|__c| __c.to_string()).collect::<Vec<String>>().into_iter()"
        elif iter_type.startswith("list[tuple["):
            # List of tuples (from zip): iter directly
            iter_str = iter_expr + ".iter_snapshot().into_iter()"
        else:
            iter_str = iter_expr + ".iter_snapshot().into_iter()"
        parts.append("for " + target_name + " in " + iter_str + " {")
        close_count += 1
        if isinstance(ifs, list) and len(ifs) > 0:
            cond_parts: list[str] = []
            for cond in ifs:
                if isinstance(cond, dict):
                    cond_parts.append(_emit_expr(ctx, cond))
            if cond_parts:
                parts.append("if " + " && ".join(cond_parts) + " {")
                close_count += 1
    parts.append(push_stmt)
    for _ in range(close_count):
        parts.append("}")
    return " ".join(parts)


def _emit_listcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit list comprehension as a Rust block expression."""
    elt = node.get("elt")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        elem_type = _rs_type_for_context(ctx, resolved_type[5:-1])
    elif resolved_type.startswith("PyList<") and resolved_type.endswith(">"):
        elem_type = resolved_type[7:-1]
    decl = "let mut __comp = PyList::<" + elem_type + ">::new();" if elem_type else "let mut __comp = PyList::new();"
    elt_expr = _emit_expr(ctx, elt)
    body = _emit_comp_generators(ctx, generators, "__comp.push(" + elt_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _emit_setcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit set comprehension as a Rust block expression."""
    elt = node.get("elt")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    elem_type = ""
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        elem_type = _rs_type_for_context(ctx, resolved_type[4:-1])
    decl = "let mut __comp: HashSet<" + elem_type + "> = HashSet::new();" if elem_type else "let mut __comp = HashSet::new();"
    elt_expr = _emit_expr(ctx, elt)
    body = _emit_comp_generators(ctx, generators, "__comp.insert(" + elt_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _emit_dictcomp(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit dict comprehension as a Rust block expression."""
    key_node = node.get("key")
    val_node = node.get("value")
    generators = _list(node, "generators")
    resolved_type = _str(node, "resolved_type")
    k_type = ""
    v_type = ""
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        comma = inner.find(",")
        if comma != -1:
            k_type = _rs_type_for_context(ctx, inner[:comma].strip())
            v_type = _rs_type_for_context(ctx, inner[comma + 1:].strip())
    decl = ("let mut __comp: HashMap<" + k_type + ", " + v_type + "> = HashMap::new();"
            if k_type and v_type else "let mut __comp = HashMap::new();")
    key_expr = _emit_expr(ctx, key_node)
    val_expr = _emit_expr(ctx, val_node)
    body = _emit_comp_generators(ctx, generators, "__comp.insert(" + key_expr + ", " + val_expr + ");")
    return "{ " + decl + " " + body + " __comp }"


def _translate_py_format_spec(spec: str) -> str:
    """Translate Python format spec to Rust format spec string (without braces).

    Examples:
      "4d"   -> "4"     (width 4, integer type stripped)
      ".4f"  -> ".4"    (precision 4, float type stripped)
      "10.2f"-> "10.2"  (width 10, precision 2)
      ">10s" -> ">10"   (left-align, string type stripped)
      "02x"  -> "02x"   (hex kept, Rust supports :02x)
      "02X"  -> "02X"   (uppercase hex kept)
      ",d"   -> ""      (comma grouping removed, Rust doesn't support)
      ".1%"  -> ".1"    (percent stripped, value stays unchanged)
      "+d"   -> "+"     (sign kept)
      ""     -> ""
    """
    if spec == "":
        return ""
    # Remove comma grouping (Python ,  → not supported in Rust)
    spec = spec.replace(",", "")
    if spec == "":
        return ""
    # Strip trailing Python type characters that Rust doesn't use
    # Keep: x, X, o, b, e, E (Rust supports these as format types)
    # Strip: d, i, f, F, g, G, s, r, c, n, % (not valid in Rust format strings)
    if spec != "":
        last_ch = spec[-1]
        if last_ch in "difFgGsrcn%":
            spec = spec[:-1]
    return spec


def _emit_formatted_value(
    ctx: RsEmitContext,
    value_node: dict[str, JsonVal],
    spec_str: str,
) -> tuple[str, str | None]:
    value_expr = _emit_expr(ctx, value_node)
    if spec_str.endswith("%"):
        precision = 6
        if "." in spec_str:
            frac = spec_str.split(".", 1)[1][:-1]
            if frac.isdigit():
                precision = int(frac)
        return "{}", 'py_format_percent(py_float(&' + value_expr + "), " + str(precision) + ")"
    if "," in spec_str and spec_str.endswith("d"):
        return "{}", "py_format_grouped_int(py_int(&" + value_expr + "))"
    rs_spec = _translate_py_format_spec(spec_str)
    return ("{:" + rs_spec + "}" if rs_spec else "{}"), value_expr


def _emit_fstring(ctx: RsEmitContext, node: dict[str, JsonVal]) -> str:
    """Emit f-string as format!()."""
    values = _list(node, "values")
    fmt_parts: list[str] = []
    fmt_args: list[str] = []
    for v in values:
        if isinstance(v, dict):
            v_kind = _str(v, "kind")
            if v_kind == "Constant":
                s = v.get("value")
                if isinstance(s, str):
                    # Escape backslashes first, then braces (for Rust format! string)
                    fmt_parts.append(s.replace("\\", "\\\\").replace("{", "{{").replace("}", "}}"))
            elif v_kind == "FormattedValue":
                raw_spec = v.get("format_spec")
                spec_str = raw_spec if isinstance(raw_spec, str) else ""
                inner = v.get("value")
                if isinstance(inner, dict):
                    fmt_part, fmt_arg = _emit_formatted_value(ctx, inner, spec_str)
                    fmt_parts.append(fmt_part)
                    if fmt_arg is not None:
                        fmt_arg_value = fmt_arg
                        fmt_args.append(fmt_arg_value)
                else:
                    fmt_parts.append("{}")
                    fmt_args.append("_")
            else:
                fmt_parts.append("{}")
                fmt_args.append(_emit_expr(ctx, v))
    fmt_str = "".join(fmt_parts)
    if len(fmt_args) == 0:
        return '"' + fmt_str + '".to_string()'
    return 'format!("' + fmt_str + '", ' + ", ".join(fmt_args) + ")"


# ---------------------------------------------------------------------------
# Statement emission
# ---------------------------------------------------------------------------

def _emit_expr_stmt(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    # Skip bare string literal statements (module/class docstrings)
    if isinstance(value, dict) and _str(value, "kind") == "Constant":
        v = value.get("value")
        if isinstance(v, str):
            _emit(ctx, "// " + v.replace("\n", " ").replace("\"", "'")[:120])
            return
    # Handle `continue` and `break` used as expressions (Python control flow)
    if isinstance(value, dict) and _str(value, "kind") == "Name":
        vid = _str(value, "id")
        if vid == "continue":
            _emit(ctx, "continue;")
            return
        if vid == "break":
            _emit(ctx, "break;")
            return
    rendered = _emit_expr(ctx, value)
    # Skip no-op renders (e.g. pure comment placeholders)
    if rendered.strip() == "" or rendered == "()":
        return
    _emit(ctx, rendered + ";")


def _emit_return(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    value = node.get("value")
    if ctx.constructor_block_label != "":
        if value is None or ctx.current_return_type in ("", "None", "none"):
            _emit(ctx, "break '" + ctx.constructor_block_label + ";")
            return
    if value is None:
        _emit(ctx, "return;")
        return
    rendered = _emit_expr(ctx, value)
    if (
        isinstance(value, dict)
        and _str(value, "kind") == "Name"
        and _str(value, "id") == "self"
        and ctx.current_return_type in ctx.class_names
    ):
        if ctx.current_return_type in ctx.ref_classes:
            rendered = "Rc::new(RefCell::new(self.clone()))"
        else:
            rendered = "Box::new(self.clone())"
    # If function has no return type (void), drop the return value
    if ctx.current_return_type in ("", "None", "none"):
        _emit(ctx, "return;")
        return
    # Wrap in Some() if returning a non-None value into an Optional return type
    if ctx.current_return_type != "":
        ret_rs = _rs_type_for_context(ctx, ctx.current_return_type)
        val_rt = _actual_type_in_context(ctx, value) if isinstance(value, dict) else ""
        if ret_rs == "PyAny" and val_rt != "" and _rs_type_for_context(ctx, val_rt) != "PyAny":
            rendered = _expr_to_pyany(rendered, val_rt)
        if ret_rs.startswith("Option<") and rendered != "None":
            inner_expected = ctx.current_return_type[:-7].strip() if ctx.current_return_type.endswith(" | None") else ctx.current_return_type[:-5].strip()
            val_is_none = (val_rt in ("None", "none") or rendered == "None")
            # Don't wrap if value is already Optional (e.g., str | None → Option<String>)
            val_is_already_optional = (val_rt.endswith(" | None") or val_rt.endswith("|None"))
            val_rs = rs_type(val_rt) if val_rt != "" else ""
            val_is_option = val_rs.startswith("Option<")
            if not val_is_already_optional and not val_is_option:
                rendered = _coerce_call_arg_to_expected(ctx, value, rendered, inner_expected)
            if not val_is_none and not val_is_already_optional and not val_is_option:
                rendered = "Some(" + rendered + ")"
        elif val_rt != "":
            val_rs = _rs_type_for_context(ctx, val_rt)
            narrowed_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
            if narrowed_rt != "" and narrowed_rt != val_rt and _rs_type_for_context(ctx, narrowed_rt) == ret_rs:
                rendered = _coerce_call_arg_to_expected(ctx, value, rendered, ctx.current_return_type)
            if val_rs.startswith("Option<") and not ret_rs.startswith("Option<"):
                if ret_rs.startswith("HashMap<") or ret_rs.startswith("HashSet<") or ret_rs.startswith("PyList<") or ret_rs.startswith("VecDeque<"):
                    rendered = rendered + ".unwrap_or_default()"
                else:
                    rendered = rendered + '.expect("return unwrap")'
            if ret_rs == "PyPath" and val_rs == "Box<PyPath>":
                rendered = "*" + rendered
        elif ret_rs == "Box<dyn std::any::Any>" and val_rt in ctx.class_names and val_rt not in ctx.enum_bases:
            # Returning a class instance as Box<dyn Any> — box and clone
            rendered = "Box::new(" + rendered + ".clone()) as Box<dyn std::any::Any>"
        elif ret_rs == "Box<dyn std::error::Error>" and rendered.startswith("std::io::Error::new("):
            rendered = "Box::new(" + rendered + ")"
    _emit(ctx, "return " + rendered + ";")


def _emit_ann_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    annotation = _str(node, "annotation")
    resolved_type = _str(node, "decl_type")
    if resolved_type == "":
        resolved_type = annotation
    if resolved_type == "":
        resolved_type = _str(node, "resolved_type")

    if isinstance(target, dict):
        target_kind = _str(target, "kind")

        if target_kind == "Attribute":
            if value is not None:
                target_obj = target.get("value")
                target_attr = _str(target, "attr")
                if (
                    isinstance(target_obj, dict)
                    and _str(target_obj, "id") == "self"
                    and target_attr in ctx.constructor_field_locals
                ):
                    lhs = _rs_constructor_field_name(target_attr)
                else:
                    lhs = _emit_attribute(ctx, target)
                rhs = _emit_expr(ctx, value)
                target_type = ""
                if (
                    isinstance(target_obj, dict)
                    and _str(target_obj, "id") == "self"
                    and ctx.current_class != ""
                ):
                    target_type = ctx.class_fields.get(ctx.current_class, {}).get(target_attr, "")
                if target_type == "":
                    target_type = _str(target, "resolved_type") or _str(target, "decl_type")
                rhs = _coerce_assignment_rhs(ctx, rhs, value, target_type)
                if (
                    isinstance(target_obj, dict)
                    and _str(target_obj, "id") == "self"
                    and target_attr in ctx.constructor_field_locals
                    and isinstance(value, dict)
                    and _str(value, "kind") == "Name"
                ):
                    rhs_type = _actual_type_in_context(ctx, value)
                    rhs_rs = _rs_type_for_context(ctx, rhs_type) if rhs_type != "" else ""
                    target_type = ctx.class_fields.get(ctx.current_class, {}).get(target_attr, "")
                    if target_type == "":
                        target_type = _str(target, "resolved_type") or _str(target, "decl_type")
                    target_rs = _rs_type_for_context(ctx, target_type) if target_type != "" else ""
                    if (
                        rhs_rs.startswith("Option<")
                        and (target_rs == "" or not target_rs.startswith("Option<"))
                        and ".unwrap_or_default()" not in rhs
                        and '.expect("' not in rhs
                    ):
                        rhs = rhs + '.expect("init field")'
                    elif rhs_rs != "" and not _rs_is_copy_type(rhs_rs):
                        rhs = rhs + ".clone()"
                _emit(ctx, lhs + " = " + rhs + ";")
            return

        target_name = _str(target, "id")
        if target_name == "":
            return

        rs_name = _rs_var_name(ctx, target_name)
        rt = _rs_type_for_context(ctx, resolved_type) if resolved_type != "" else ""
        if resolved_type in ctx.ref_classes and not _needs_parent_trait_object(ctx, resolved_type):
            rt = "Rc<RefCell<" + safe_rs_ident(resolved_type) + ">>"
        value_rt = _str(value, "resolved_type") if isinstance(value, dict) else ""
        if _needs_parent_trait_object(ctx, resolved_type):
            rt = "Box<dyn " + safe_rs_ident(resolved_type) + "Methods>"

        if target_name in ctx.declared_vars:
            # Reassignment
            if value is not None:
                rhs = _emit_expr(ctx, value)
                target_type = ctx.var_types.get(target_name, "")
                if target_type != "":
                    rhs = _coerce_assignment_rhs(ctx, rhs, value, target_type)
                inferred_rhs_rt = _infer_node_rust_type(ctx, value)
                emitted_rhs_rt = _infer_emitted_rust_type(rhs)
                if emitted_rhs_rt == "PyAny":
                    inferred_rhs_rt = emitted_rhs_rt
                elif inferred_rhs_rt == "":
                    inferred_rhs_rt = emitted_rhs_rt
                if inferred_rhs_rt != "":
                    ctx.var_rust_types[target_name] = inferred_rhs_rt
                storage_hint = _str(target, "resolved_storage_hint")
                if storage_hint == "" and isinstance(value, dict):
                    storage_hint = _str(value, "resolved_storage_hint")
                if storage_hint in ("ref", "value"):
                    ctx.var_storage_hints[target_name] = storage_hint
                _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            # New declaration
            ctx.declared_vars.add(target_name)
            ctx.var_types[target_name] = resolved_type
            if rt != "" and rt != "()":
                ctx.var_rust_types[target_name] = rt
            storage_hint = _str(target, "resolved_storage_hint")
            if storage_hint == "" and isinstance(value, dict):
                storage_hint = _str(value, "resolved_storage_hint")
            if storage_hint in ("ref", "value"):
                ctx.var_storage_hints[target_name] = storage_hint
            # Module-level vars: emit as const or static (can't use `let` at module level)
            if ctx.at_module_level:
                if _looks_like_type_alias_assignment(target_name, value):
                    alias_rt = _str(value, "resolved_type")
                    if alias_rt == "":
                        alias_rt = resolved_type
                    alias_rs = _rs_type_for_context(ctx, alias_rt) if alias_rt != "" else "PyAny"
                    vis = "pub " if ctx.package_mode else ""
                    _emit(ctx, vis + "type " + safe_rs_ident(target_name) + " = " + alias_rs + ";")
                    return
                rs_upper = rs_name.upper()
                val_is_const = isinstance(value, dict) and value.get("kind") == "Constant"
                if value is not None:
                    rhs = _emit_expr(ctx, value)
                    t = rt if rt != "" and rt != "()" else "i64"
                    vis = "pub " if ctx.package_mode else ""
                    if val_is_const:
                        # Simple constant: use `const`
                        if t == "String" and isinstance(value, dict) and isinstance(value.get("value"), str):
                            escaped = str(value.get("value")).replace("\\", "\\\\").replace("\"", "\\\"")
                            _emit(ctx, vis + 'const ' + rs_upper + ': &str = "' + escaped + '";')
                        else:
                            _emit(ctx, vis + "const " + rs_upper + ": " + t + " = " + rhs + ";")
                        ctx.module_statics[target_name] = rs_upper
                    elif t == "PyPath" or t.startswith("Box<") or t.startswith("PyList") or t.startswith("HashMap") or t.startswith("HashSet") or t.startswith("BTreeMap") or t.startswith("Vec<") or t.startswith("VecDeque"):
                        factory_name = safe_rs_ident(target_name) if ctx.package_mode else (_module_prefix(ctx) + "__module_init_" + rs_name if _module_prefix(ctx) != "" else "__module_init_" + rs_name)
                        _emit(ctx, vis + "fn " + factory_name + "() -> " + t + " { " + rhs + " }")
                        ctx.module_factories[target_name] = factory_name
                    else:
                        _emit(ctx, vis + "static mut " + rs_upper + ": " + t + " = 0; // init: " + rhs)
                        ctx.module_statics[target_name] = rs_upper
                else:
                    t = rt if rt != "" and rt != "()" else "i64"
                    vis = "pub " if ctx.package_mode else ""
                    _emit(ctx, vis + "static mut " + rs_upper + ": " + t + " = 0;")
                    ctx.module_statics[target_name] = rs_upper
                return
            if value is not None:
                rhs = _emit_expr(ctx, value)
                rhs = _coerce_assignment_rhs(ctx, rhs, value, resolved_type)
                inferred_rhs_rt = _infer_node_rust_type(ctx, value)
                emitted_rhs_rt = _infer_emitted_rust_type(rhs)
                if rt != "" and rt != "()":
                    if not (inferred_rhs_rt.startswith("Option<") and not rt.startswith("Option<")):
                        inferred_rhs_rt = rt
                elif emitted_rhs_rt == "PyAny":
                    inferred_rhs_rt = emitted_rhs_rt
                elif inferred_rhs_rt == "":
                    inferred_rhs_rt = emitted_rhs_rt
                if inferred_rhs_rt != "":
                    ctx.var_rust_types[target_name] = inferred_rhs_rt
                    if (
                        rt != ""
                        and rt != inferred_rhs_rt
                        and inferred_rhs_rt.startswith("Rc<RefCell<")
                    ):
                        rt = inferred_rhs_rt
                    if rt != "" and not rt.startswith("Option<") and inferred_rhs_rt.startswith("Option<"):
                        rt = inferred_rhs_rt
                if _needs_parent_trait_object(ctx, resolved_type) and value_rt in ctx.class_names and value_rt != "":
                    if value_rt in ctx.ref_classes:
                        rhs = "Box::new(" + rhs + ".borrow().clone()) as Box<dyn " + safe_rs_ident(resolved_type) + "Methods>"
                    else:
                        rhs = "Box::new(*" + rhs + ") as Box<dyn " + safe_rs_ident(resolved_type) + "Methods>"
                # Cast rhs to small/narrow numeric types (py_int returns i64, py_float returns f64)
                _NARROW_RS = {"i8", "i16", "i32", "u8", "u16", "u32", "u64", "f32"}
                _WIDE_RS = {"i8", "i16", "i32", "u8", "u16", "u32", "u64", "f32", "i64", "f64"}
                if rt in _NARROW_RS and isinstance(value, dict):
                    val_rt = _str(value, "resolved_type")
                    val_rs = rs_type(val_rt) if val_rt != "" else ""
                    if val_rs in _WIDE_RS:
                        rhs = rhs + " as " + rt
                # Inheritance: declared type is Box<Parent> but value is Subclass — use value type
                if rt.startswith("Box<") and resolved_type not in ctx.parent_class_names and isinstance(value, dict):
                    val_rt2 = _str(value, "resolved_type")
                    if val_rt2 != resolved_type and val_rt2 in ctx.class_names and val_rt2 not in ctx.enum_bases:
                        rt = _rs_type_for_context(ctx, val_rt2)
                        ctx.var_types[target_name] = val_rt2
                # `_` is the wildcard pattern - Rust doesn't allow `mut _`
                if rs_name == "_":
                    _emit(ctx, "let _ = " + rhs + ";")
                elif rt != "" and rt != "()":
                    _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + rhs + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")
            else:
                if rs_name == "_":
                    return  # discard with no value: nothing to emit
                if rt != "" and rt != "()":
                    zero = _rs_zero_value_for_context(ctx, resolved_type)
                    _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + zero + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + ";")


def _emit_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")

    if isinstance(target, dict):
        target_kind = _str(target, "kind")

        if target_kind == "Attribute":
            target_obj = target.get("value")
            type_object_of = _str(target_obj, "type_object_of") if isinstance(target_obj, dict) else ""
            rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
            target_attr = _str(target, "attr")
            target_type = ""
            class_vars_for_type = ctx.class_vars.get(type_object_of)
            if type_object_of != "" and isinstance(class_vars_for_type, dict) and target_attr in class_vars_for_type:
                target_type = class_vars_for_type[target_attr]
            elif isinstance(target_obj, dict):
                obj_type_name = _actual_type_in_context(ctx, target_obj)
                for candidate in _type_lookup_candidates(obj_type_name):
                    target_type = ctx.class_fields.get(candidate, {}).get(target_attr, "")
                    if target_type != "":
                        break
            if target_type == "":
                target_type = _str(target, "resolved_type") or _str(target, "decl_type")
            rhs = _coerce_assignment_rhs(ctx, rhs, value, target_type)
            class_vars_for_type = ctx.class_vars.get(type_object_of)
            if type_object_of != "" and isinstance(class_vars_for_type, dict) and _str(target, "attr") in class_vars_for_type:
                static_name = _class_var_static_name(ctx, type_object_of, _str(target, "attr"))
                _emit(ctx, "unsafe { " + static_name + " = " + rhs + "; }")
                return
            if (
                isinstance(target_obj, dict)
                and _str(target_obj, "id") == "self"
                and target_attr in ctx.constructor_field_locals
            ):
                if isinstance(value, dict) and _str(value, "kind") == "Name":
                    rhs_type = _actual_type_in_context(ctx, value)
                    rhs_rs = _rs_type_for_context(ctx, rhs_type) if rhs_type != "" else ""
                    target_type = ctx.class_fields.get(ctx.current_class, {}).get(target_attr, "")
                    if target_type == "":
                        target_type = _str(target, "resolved_type") or _str(target, "decl_type")
                    target_rs = _rs_type_for_context(ctx, target_type) if target_type != "" else ""
                    if (
                        rhs_rs.startswith("Option<")
                        and (target_rs == "" or not target_rs.startswith("Option<"))
                        and ".unwrap_or_default()" not in rhs
                        and '.expect("' not in rhs
                    ):
                        rhs = rhs + '.expect("init field")'
                    elif rhs_rs != "" and not _rs_is_copy_type(rhs_rs):
                        rhs = rhs + ".clone()"
                _emit(ctx, _rs_constructor_field_name(target_attr) + " = " + rhs + ";")
                return
            obj_type = _str(target_obj, "resolved_type") if isinstance(target_obj, dict) else ""
            target_obj_hint = _str(target_obj, "resolved_storage_hint") if isinstance(target_obj, dict) else ""
            if target_obj_hint == "" and isinstance(target_obj, dict):
                target_obj_hint = ctx.var_storage_hints.get(_str(target_obj, "id"), "")
            target_obj_is_ref = obj_type in ctx.ref_classes or target_obj_hint == "ref"
            if not target_obj_is_ref and isinstance(target_obj, dict) and _str(target_obj, "kind") == "Name":
                name_rs = ctx.var_rust_types.get(_str(target_obj, "id"), "")
                target_obj_is_ref = name_rs.startswith("Rc<RefCell<") and name_rs.endswith(">>")
            if target_obj_is_ref and not (isinstance(target_obj, dict) and _str(target_obj, "kind") == "Name" and _str(target_obj, "id") == "self"):
                obj_expr = _emit_expr(ctx, target_obj)
                _emit(ctx, obj_expr + ".borrow_mut()." + safe_rs_ident(_str(target, "attr")) + " = " + rhs + ";")
                return
            if isinstance(target_obj, dict) and _str(target_obj, "kind") == "Name" and _str(target_obj, "id") == "self":
                _emit(ctx, "self." + safe_rs_ident(_str(target, "attr")) + " = " + rhs + ";")
                return
            lhs = _emit_attribute(ctx, target)
            _emit(ctx, lhs + " = " + rhs + ";")
            return

        if target_kind == "Subscript":
            obj = _emit_expr(ctx, target.get("value"))
            slice_node = target.get("slice")
            obj_type = _str(target.get("value"), "resolved_type") if isinstance(target.get("value"), dict) else ""
            idx = _emit_expr(ctx, slice_node)
            rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
            if isinstance(value, dict) and _str(value, "kind") == "Name":
                rhs_type = _infer_node_rust_type(ctx, value) or _rs_type_for_context(ctx, _actual_type_in_context(ctx, value))
                if (
                    rhs_type == "String"
                    or rhs_type == "PyAny"
                    or rhs_type.startswith("HashMap<")
                    or rhs_type.startswith("HashSet<")
                    or rhs_type.startswith("PyList<")
                    or rhs_type.startswith("VecDeque<")
                    or rhs_type.startswith("Rc<RefCell<")
                    or rhs_type.startswith("Box<")
                ):
                    rhs = rhs + ".clone()"
            if obj_type.startswith("list[") or obj_type == "list" or obj_type in ("bytes", "bytearray"):
                _emit(ctx, obj + ".set(" + idx + ", " + rhs + ");")
            elif obj_type.startswith("dict[") or obj_type == "dict":
                if obj_type.startswith("dict[") and obj_type.endswith("]"):
                    parts = _split_generic_args(obj_type[5:-1])
                    if len(parts) == 2 and _rs_type_for_context(ctx, parts[1]) == "PyAny":
                        rhs = _expr_to_pyany(rhs, _actual_type_in_context(ctx, value))
                _emit(ctx, obj + ".insert(" + idx + ", " + rhs + ");")
            else:
                _emit(ctx, obj + "[" + idx + " as usize] = " + rhs + ";")
            return

        if target_kind == "Tuple" or target_kind == "List":
            # Tuple unpacking
            elements = _list(target, "elements")
            if value is not None and len(elements) > 0:
                temp = _next_temp(ctx, "unpack")
                rhs = _emit_expr(ctx, value)
                _emit(ctx, "let " + temp + " = " + rhs + ";")
                for idx, elem in enumerate(elements):
                    if isinstance(elem, dict):
                        elem_name = _str(elem, "id")
                        if elem_name != "" and elem_name != "_":
                            rs_elem = _rs_var_name(ctx, elem_name)
                            source_type = _actual_type_in_context(ctx, value) if isinstance(value, dict) else ""
                            source_rs = _rs_type_for_context(ctx, source_type) if source_type != "" else ""
                            temp_expr = temp + '.expect("tuple unpack")' if source_rs.startswith("Option<") else temp
                            if elem_name in ctx.declared_vars:
                                _emit(ctx, rs_elem + " = " + temp_expr + "." + str(idx) + ";")
                            else:
                                ctx.declared_vars.add(elem_name)
                                _emit(ctx, "let mut " + rs_elem + " = " + temp_expr + "." + str(idx) + ";")
            return

        target_name = _str(target, "id")
        if target_name == "":
            return

        rs_name = _rs_var_name(ctx, target_name)
        rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
        target_type = ctx.var_types.get(target_name, _str(value, "resolved_type") if isinstance(value, dict) else "")
        rhs = _coerce_assignment_rhs(ctx, rhs, value, target_type)
        # PyList is Rc-wrapped — assignment needs .clone() to share reference (not move)
        # User class Box<T> also needs .clone() to avoid move
        if isinstance(value, dict) and value.get("kind") == "Name":
            val_type = _str(value, "resolved_type")
            if val_type.startswith("list[") or val_type == "list" or val_type in ("bytes", "bytearray"):
                rhs = rhs + ".clone()"
            elif val_type in ctx.class_names:
                rhs = rhs + ".clone()"
            elif _rs_type_for_context(ctx, val_type) in ("String", "PyAny"):
                rhs = rhs + ".clone()"

        if target_name in ctx.declared_vars:
            target_type = ctx.var_types.get(target_name, "")
            if target_type != "":
                rhs = _coerce_assignment_rhs(ctx, rhs, value, target_type)
            inferred_rhs_rt = _infer_node_rust_type(ctx, value) if isinstance(value, dict) else ""
            emitted_rhs_rt = _infer_emitted_rust_type(rhs) if value is not None else ""
            if emitted_rhs_rt == "PyAny":
                inferred_rhs_rt = emitted_rhs_rt
            elif inferred_rhs_rt == "" and value is not None:
                inferred_rhs_rt = emitted_rhs_rt
            if inferred_rhs_rt != "":
                ctx.var_rust_types[target_name] = inferred_rhs_rt
            storage_hint = _str(target, "resolved_storage_hint")
            if storage_hint == "" and isinstance(value, dict):
                storage_hint = _str(value, "resolved_storage_hint")
            if storage_hint in ("ref", "value"):
                ctx.var_storage_hints[target_name] = storage_hint
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target_name)
            resolved_type = _str(value, "resolved_type") if isinstance(value, dict) else ""
            if resolved_type == "":
                resolved_type = _str(node, "decl_type")
            if resolved_type in ("", "unknown") and isinstance(value, dict) and _str(value, "kind") == "Call":
                func_node = value.get("func")
                if isinstance(func_node, dict) and _str(func_node, "kind") == "Name":
                    sig = ctx.function_signatures.get(_str(func_node, "id"))
                    if isinstance(sig, dict):
                        ret = _str(sig, "return_type")
                        if ret != "":
                            resolved_type = ret
            if resolved_type != "":
                ctx.var_types[target_name] = resolved_type
            elif isinstance(value, dict) and _str(value, "kind") == "Call":
                func_node = value.get("func")
                func_name = _str(func_node, "id") if isinstance(func_node, dict) else ""
                call_args = _list(value, "args")
                if func_name == "__import__" and len(call_args) >= 1:
                    import_call_arg = call_args[0]
                    if isinstance(import_call_arg, dict) and _str(import_call_arg, "kind") == "Constant":
                        mod_name = _as_str(_json_get(import_call_arg, "value"))
                        if mod_name != "" and _resolve_import_module_ctor(ctx, mod_name) != "":
                            ctx.var_types[target_name] = "py_imported_module"
                elif func_name == "dict" and len(call_args) == 1 and isinstance(call_args[0], dict):
                    arg_type = _actual_type_in_context(ctx, call_args[0])
                    if arg_type.startswith("dict[") or arg_type == "dict":
                        ctx.var_types[target_name] = arg_type
                elif isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute":
                    owner = func_node.get("value")
                    owner_type = _actual_type_in_context(ctx, owner)
                    if owner_type == "py_imported_module" and _str(func_node, "attr") == "run":
                        ctx.var_types[target_name] = "py_completed_process"
            inferred_rhs_rt = _infer_node_rust_type(ctx, value) if isinstance(value, dict) else ""
            emitted_rhs_rt = _infer_emitted_rust_type(rhs) if value is not None else ""
            if emitted_rhs_rt == "PyAny":
                inferred_rhs_rt = emitted_rhs_rt
            elif inferred_rhs_rt == "" and value is not None:
                inferred_rhs_rt = emitted_rhs_rt
            if inferred_rhs_rt != "":
                ctx.var_rust_types[target_name] = inferred_rhs_rt
            storage_hint = _str(target, "resolved_storage_hint")
            if storage_hint == "" and isinstance(value, dict):
                storage_hint = _str(value, "resolved_storage_hint")
            if storage_hint in ("ref", "value"):
                ctx.var_storage_hints[target_name] = storage_hint
            # Module-level assignment: use const/static
            if ctx.at_module_level:
                if _looks_like_type_alias_assignment(target_name, value):
                    alias_rs = _rs_type_for_context(ctx, resolved_type) if resolved_type not in ("", "unknown") else "PyAny"
                    vis = "pub " if ctx.package_mode else ""
                    _emit(ctx, vis + "type " + safe_rs_ident(target_name) + " = " + alias_rs + ";")
                    return
                rs_upper = rs_name.upper()
                val_is_const = isinstance(value, dict) and value.get("kind") == "Constant"
                rt = _rs_type_for_context(ctx, resolved_type) if resolved_type not in ("", "unknown") else "i64"
                vis = "pub " if ctx.package_mode else ""
                if val_is_const:
                    if rt == "String" and isinstance(value, dict) and isinstance(value.get("value"), str):
                        escaped = str(value.get("value")).replace("\\", "\\\\").replace("\"", "\\\"")
                        _emit(ctx, vis + 'const ' + rs_upper + ': &str = "' + escaped + '";')
                    else:
                        _emit(ctx, vis + "const " + rs_upper + ": " + rt + " = " + rhs + ";")
                    ctx.module_statics[target_name] = rs_upper
                elif rt == "PyPath" or rt.startswith("Box<") or rt.startswith("PyList") or rt.startswith("HashMap") or rt.startswith("HashSet") or rt.startswith("BTreeMap") or rt.startswith("Vec<") or rt.startswith("VecDeque") or rt.startswith("Rc<RefCell<"):
                    factory_name = safe_rs_ident(target_name) if ctx.package_mode else (_module_prefix(ctx) + "__module_init_" + rs_name if _module_prefix(ctx) != "" else "__module_init_" + rs_name)
                    _emit(ctx, vis + "fn " + factory_name + "() -> " + rt + " { " + rhs + " }")
                    ctx.module_factories[target_name] = factory_name
                else:
                    _emit(ctx, vis + "static mut " + rs_upper + ": " + rt + " = 0; // init: " + rhs)
                    ctx.module_statics[target_name] = rs_upper
            else:
                if rs_name == "_":
                    _emit(ctx, "let _ = " + rhs + ";")
                else:
                    _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")

    elif isinstance(target, str):
        rs_name = _rs_var_name(ctx, target)
        rhs = _emit_expr(ctx, value) if value is not None else "Default::default()"
        if target in ctx.declared_vars:
            _emit(ctx, rs_name + " = " + rhs + ";")
        else:
            ctx.declared_vars.add(target)
            if rs_name == "_":
                _emit(ctx, "let _ = " + rhs + ";")
            else:
                _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")


def _emit_aug_assign(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    target = node.get("target")
    value = node.get("value")
    op = _str(node, "op")
    aug_ops: dict[str, str] = {}
    aug_ops["Add"] = "+="
    aug_ops["Sub"] = "-="
    aug_ops["Mult"] = "*="
    aug_ops["Div"] = "/="
    aug_ops["FloorDiv"] = "/="
    aug_ops["Mod"] = "%="
    aug_ops["BitAnd"] = "&="
    aug_ops["BitOr"] = "|="
    aug_ops["BitXor"] = "^="
    aug_ops["LShift"] = "<<="
    aug_ops["RShift"] = ">>="
    rs_op = aug_ops.get(op, "+=")
    lhs = _emit_expr(ctx, target)
    rhs = _emit_expr(ctx, value) if value is not None else "0"
    target_type = _str(target, "resolved_type") if isinstance(target, dict) else ""
    if target_type == "" and isinstance(target, dict) and _str(target, "kind") == "Name":
        target_type = ctx.var_types.get(_str(target, "id"), "")
    if isinstance(value, dict):
        value_storage_rs = _infer_node_rust_type(ctx, value)
        value_actual_type = _actual_type_in_context(ctx, value)
        value_is_dynamic_numeric = value_storage_rs == "PyAny" or ("|" in value_actual_type and value_actual_type != "")
        if value_is_dynamic_numeric:
            if target_type in ("int64", "int", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
                rhs = "py_int(&(" + rhs + ".clone()))"
            elif target_type in ("float64", "float32", "float"):
                rhs = "py_float(&(" + rhs + ".clone()))"
            elif target_type == "bool":
                rhs = "py_bool(&(" + rhs + ".clone()))"
        if ".downcast_ref::<" in rhs:
            rhs_source_node = value
            if _str(value, "kind") == "Unbox":
                unbox_value = value.get("value")
                if isinstance(unbox_value, dict):
                    rhs_source_node = unbox_value
            rhs_source = _emit_expr(ctx, rhs_source_node)
            if target_type in ("int64", "int", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
                rhs = "py_int(&(" + rhs_source + ".clone()))"
            elif target_type in ("float64", "float32", "float"):
                rhs = "py_float(&(" + rhs_source + ".clone()))"
            elif target_type == "bool":
                rhs = "py_bool(&(" + rhs_source + ".clone()))"
    if isinstance(target, dict) and _str(target, "kind") == "Attribute":
        target_obj = target.get("value")
        type_object_of = _str(target_obj, "type_object_of") if isinstance(target_obj, dict) else ""
        class_vars_for_type = ctx.class_vars.get(type_object_of)
        if type_object_of != "" and isinstance(class_vars_for_type, dict) and _str(target, "attr") in class_vars_for_type:
            static_name = _class_var_static_name(ctx, type_object_of, _str(target, "attr"))
            _emit(ctx, "unsafe { " + static_name + " " + rs_op + " " + rhs + "; }")
            return
        obj_type = _str(target_obj, "resolved_type") if isinstance(target_obj, dict) else ""
        target_obj_rs = _infer_node_rust_type(ctx, target_obj)
        if (
            (obj_type in ctx.ref_classes or target_obj_rs.startswith("Rc<RefCell<"))
            and not (isinstance(target_obj, dict) and _str(target_obj, "kind") == "Name" and _str(target_obj, "id") == "self")
        ):
            obj_expr = _emit_expr(ctx, target_obj)
            _emit(ctx, obj_expr + ".borrow_mut()." + safe_rs_ident(_str(target, "attr")) + " " + rs_op + " " + rhs + ";")
            return
    # String += &str in Rust (String += String is invalid)
    if op == "Add":
        if target_type == "str" and not rhs.startswith("&"):
            rhs = "&" + rhs
    _emit(ctx, lhs + " " + rs_op + " " + rhs + ";")


def _emit_raise(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    renderer = _RsStmtCommonRenderer(ctx)
    exc = node.get("exc")
    if exc is None:
        # Bare raise: re-raise current exception
        if ctx.catch_err_msg_var:
            _emit(ctx, renderer.render_panic_message(ctx.catch_err_msg_var + ".clone()"))
        else:
            _emit(ctx, renderer.render_panic_literal("re-raised"))
        return
    if isinstance(exc, dict):
        exc_kind = _str(exc, "kind")
        if exc_kind == "Call":
            func_node = exc.get("func")
            func_runtime_mod = _str(func_node, "runtime_module_id") if isinstance(func_node, dict) else ""
            exc_resolved = _str(exc, "resolved_type")
            # User-defined exception (no runtime_module_id, class defined in this module)
            if func_runtime_mod == "" and exc_resolved in ctx.class_names:
                # _emit_expr wraps constructors in Box::new() — we need the raw value for panic_any
                # Emit ClassName::new(args...) without Box wrapper
                exc_args = _list(exc, "args")
                exc_kwargs = _list(exc, "keywords")
                rendered_args = [_emit_expr(ctx, a) for a in exc_args]
                rs_exc_name = safe_rs_ident(exc_resolved)
                raw_call = rs_exc_name + "::new(" + ", ".join(rendered_args) + ")"
                _emit(ctx, renderer.render_panic_any(raw_call))
                return
            args = _list(exc, "args")
            if len(args) > 0:
                msg = _emit_expr(ctx, args[0])
                _emit(ctx, renderer.render_panic_message(msg))
                return
        msg = _emit_expr(ctx, exc)
        _emit(ctx, renderer.render_panic_message(msg))
        return
    _emit(ctx, renderer.render_panic_literal("exception"))


def _body_has_return(stmts: list[JsonVal]) -> bool:
    """Recursively check if any statement in the body has a Return node with a value."""
    for stmt in stmts:
        if not isinstance(stmt, dict):
            continue
        if stmt.get("kind") == "Return":
            val = stmt.get("value")
            if val is not None:
                return True
        child_body_keys = ["body", "orelse", "finalbody"]
        for key in child_body_keys:
            sub = stmt.get(key)
            if isinstance(sub, list) and _body_has_return(sub):
                return True
        handlers = stmt.get("handlers")
        if isinstance(handlers, list):
            for h in handlers:
                if isinstance(h, dict):
                    hbody = h.get("body")
                    if isinstance(hbody, list) and _body_has_return(hbody):
                        return True
    return False


def _emit_try_body_hoists(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        target_name = ""
        resolved_type = ""
        if stmt_kind == "VarDecl":
            target_name = _str(stmt, "name")
            resolved_type = _str(stmt, "resolved_type") or _str(stmt, "type")
        elif stmt_kind == "AnnAssign":
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                target_name = _str(target, "id")
                resolved_type = _str(stmt, "decl_type") or _str(stmt, "resolved_type")
        elif stmt_kind == "Assign":
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                target_name = _str(target, "id")
                value = stmt.get("value")
                if isinstance(value, dict):
                    resolved_type = _str(value, "resolved_type")
        if target_name == "" or target_name == "_" or target_name in ctx.declared_vars:
            continue
        rs_name = _rs_var_name(ctx, target_name)
        if resolved_type != "":
            _emit(
                ctx,
                "let mut "
                + rs_name
                + ": "
                + _rs_type_for_context(ctx, resolved_type)
                + " = "
                + _rs_zero_value_for_context(ctx, resolved_type)
                + ";",
            )
            ctx.var_types[target_name] = resolved_type
        else:
            _emit(ctx, "let mut " + rs_name + ";")
        ctx.declared_vars.add(target_name)


def _emit_for_core(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit ForCore statement (EAST3 for-loop)."""
    body = _list(node, "body")

    # Check for iter_plan (EAST3 lowered loop plan)
    iter_plan = node.get("iter_plan")
    target_plan = node.get("target_plan")

    if isinstance(iter_plan, dict):
        plan_kind = _str(iter_plan, "kind")
        if plan_kind == "StaticRangeForPlan":
            _emit_static_range_for_from_plan(ctx, iter_plan, target_plan, body)
            return
        if plan_kind == "RuntimeIterForPlan":
            _emit_runtime_iter_for_from_plan(ctx, iter_plan, target_plan, body)
            return

    # Fallback: use target/iter fields
    target = node.get("target")
    iter_node = node.get("iter")

    target_str = _emit_loop_target(ctx, target, target_plan)
    iter_str = _emit_for_iter(ctx, iter_node, target)

    _emit_loop_var_declared(ctx, target, target_plan)
    # Infer element type from iterator's resolved_type for nested loop dispatch
    if isinstance(iter_node, dict):
        iter_rt = _resolved_type_in_context(ctx, iter_node)
        target_id = _str(target, "id") if isinstance(target, dict) else ""
        if target_id == "" and isinstance(target_plan, dict):
            target_id = _str(target_plan, "id")
        if target_id != "" and iter_rt.startswith("list["):
            elem_type = iter_rt[5:-1]
            ctx.var_types[target_id] = elem_type
            if (
                (elem_type in ctx.ref_classes or ctx.imported_symbol_storage_hints.get(elem_type) == "ref")
                and not _needs_parent_trait_object(ctx, elem_type)
            ):
                ctx.var_rust_types[target_id] = "Rc<RefCell<" + safe_rs_ident(elem_type) + ">>"
                ctx.var_storage_hints[target_id] = "ref"
        if target_id != "":
            iter_expr = _emit_expr(ctx, iter_node)
            iter_rs = _infer_node_rust_type(ctx, iter_node) or _infer_emitted_rust_type(iter_expr)
            if iter_rs.startswith("PyList<") and iter_rs.endswith(">"):
                elem_rs = iter_rs[len("PyList<"):-1]
                ctx.var_rust_types[target_id] = elem_rs
                if elem_rs.startswith("Rc<RefCell<") and elem_rs.endswith(">>"):
                    ctx.var_storage_hints[target_id] = "ref"
    _emit(ctx, "for " + target_str + " in " + iter_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_loop_target(ctx: RsEmitContext, target: JsonVal, target_plan: JsonVal) -> str:
    """Get Rust loop variable expression."""
    def _pattern_from_plan(plan: dict[str, JsonVal]) -> str:
        plan_kind = _str(plan, "kind")
        if plan_kind == "NameTarget":
            return _rs_var_name(ctx, _str(plan, "id"))
        if plan_kind == "TupleTarget":
            elements = _list(plan, "elements")
            parts: list[str] = []
            for e in elements:
                if isinstance(e, dict):
                    parts.append(_pattern_from_plan(e))
                else:
                    parts.append("_")
            return "(" + ", ".join(parts) + ")"
        return "_"

    def _pattern_from_target(target_node: dict[str, JsonVal]) -> str:
        target_kind = _str(target_node, "kind")
        if target_kind == "Name":
            return _rs_var_name(ctx, _str(target_node, "id"))
        if target_kind == "Tuple":
            elements = _list(target_node, "elements")
            parts: list[str] = []
            for e in elements:
                if isinstance(e, dict):
                    parts.append(_pattern_from_target(e))
                else:
                    parts.append("_")
            return "(" + ", ".join(parts) + ")"
        return "_"

    if isinstance(target_plan, dict):
        return _pattern_from_plan(target_plan)
    if isinstance(target, dict):
        return _pattern_from_target(target)
    if isinstance(target, str):
        return _rs_var_name(ctx, target)
    return "_item"


def _emit_loop_var_declared(ctx: RsEmitContext, target: JsonVal, target_plan: JsonVal) -> None:
    """Mark loop variable as declared."""
    def _declare_plan(plan: dict[str, JsonVal]) -> None:
        plan_kind = _str(plan, "kind")
        if plan_kind == "NameTarget":
            name = _str(plan, "id")
            if name != "":
                ctx.declared_vars.add(name)
                target_type = _str(plan, "target_type")
                if target_type != "":
                    ctx.var_types[name] = target_type
                    if (
                        (target_type in ctx.ref_classes or ctx.imported_symbol_storage_hints.get(target_type) == "ref")
                        and not _needs_parent_trait_object(ctx, target_type)
                    ):
                        ctx.var_rust_types[name] = "Rc<RefCell<" + safe_rs_ident(target_type) + ">>"
                        ctx.var_storage_hints[name] = "ref"
            return
        if plan_kind == "TupleTarget":
            for elem in _list(plan, "elements"):
                if isinstance(elem, dict):
                    _declare_plan(elem)

    def _declare_target(target_node: dict[str, JsonVal]) -> None:
        target_kind = _str(target_node, "kind")
        if target_kind == "Name":
            name = _str(target_node, "id")
            if name != "":
                ctx.declared_vars.add(name)
            return
        if target_kind == "Tuple":
            for elem in _list(target_node, "elements"):
                if isinstance(elem, dict):
                    _declare_target(elem)

    if isinstance(target_plan, dict):
        _declare_plan(target_plan)
        return
    if isinstance(target, dict):
        _declare_target(target)


def _emit_static_range_for_from_plan(
    ctx: RsEmitContext,
    plan: dict[str, JsonVal],
    target_plan: JsonVal,
    body: list[JsonVal],
) -> None:
    """Emit StaticRangeForPlan from iter_plan."""
    start = plan.get("start")
    stop = plan.get("stop")
    step = plan.get("step")

    target_str = "_i"
    target_type = "i64"
    if isinstance(target_plan, dict):
        target_str = _rs_var_name(ctx, _str(target_plan, "id"))
        tp = _str(target_plan, "target_type")
        if tp != "":
            target_type = rs_type(tp)
    ctx.declared_vars.add(target_str)

    start_str = _emit_expr(ctx, start) if start is not None else "0_i64"
    stop_str = _emit_expr(ctx, stop) if stop is not None else "0_i64"

    # Determine step value — handles Constant, int, and UnaryOp(USub, Constant)
    step_val = 1
    step_is_const = False
    if isinstance(step, dict) and _str(step, "kind") == "Constant":
        sv = step.get("value")
        if isinstance(sv, int):
            step_val = sv
            step_is_const = True
    elif isinstance(step, int):
        step_val = step
        step_is_const = True
    elif (isinstance(step, dict) and _str(step, "kind") == "UnaryOp"
          and _str(step, "op") == "USub"):
        operand = step.get("operand")
        if isinstance(operand, dict) and _str(operand, "kind") == "Constant":
            sv2 = operand.get("value")
            if isinstance(sv2, int):
                step_val = -sv2
                step_is_const = True

    if step_is_const:
        if step_val == 1:
            _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
        elif step_val == -1:
            _emit(ctx, "let mut " + target_str + ": " + target_type + " = " + start_str + ";")
            _emit(ctx, "while " + target_str + " > " + stop_str + " {")
        elif step_val > 1:
            _emit(ctx, "for " + target_str + " in (" + start_str + ".." + stop_str + ").step_by(" + str(step_val) + ") {")
        elif step_val < -1:
            _emit(ctx, "let mut " + target_str + ": " + target_type + " = " + start_str + ";")
            _emit(ctx, "while " + target_str + " > " + stop_str + " {")
        else:
            _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
    else:
        # Dynamic step — sign unknown at emit time, assume positive (forward range)
        step_str = _emit_expr(ctx, step)
        _emit(ctx, "let mut " + target_str + ": " + target_type + " = " + start_str + ";")
        _emit(ctx, "while " + target_str + " < " + stop_str + " {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        _emit(ctx, target_str + " += (" + step_str + ") as " + target_type + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        return

    ctx.indent_level += 1
    _emit_body(ctx, body)
    if step_is_const and step_val < 0:
        _emit(ctx, target_str + " -= " + str(-step_val) + " as " + target_type + ";")
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_runtime_iter_for_from_plan(
    ctx: RsEmitContext,
    plan: dict[str, JsonVal],
    target_plan: JsonVal,
    body: list[JsonVal],
) -> None:
    """Emit RuntimeIterForPlan from iter_plan."""
    iter_expr = plan.get("iter_expr")
    if iter_expr is None:
        iter_expr = plan.get("iter")

    target_str = _emit_loop_target(ctx, None, target_plan)
    _emit_loop_var_declared(ctx, None, target_plan)
    # Infer element type from iterator's resolved_type for nested loop dispatch
    if isinstance(iter_expr, dict) and isinstance(target_plan, dict):
        iter_rt = _resolved_type_in_context(ctx, iter_expr)
        target_id = _str(target_plan, "id")
        if target_id != "" and iter_rt.startswith("list["):
            elem_type = iter_rt[5:-1]
            ctx.var_types[target_id] = elem_type
            if (
                (elem_type in ctx.ref_classes or ctx.imported_symbol_storage_hints.get(elem_type) == "ref")
                and not _needs_parent_trait_object(ctx, elem_type)
            ):
                ctx.var_rust_types[target_id] = "Rc<RefCell<" + safe_rs_ident(elem_type) + ">>"
                ctx.var_storage_hints[target_id] = "ref"
        if target_id != "":
            iter_rendered = _emit_expr(ctx, iter_expr)
            iter_rs = _infer_node_rust_type(ctx, iter_expr) or _infer_emitted_rust_type(iter_rendered)
            if iter_rs.startswith("PyList<") and iter_rs.endswith(">"):
                elem_rs = iter_rs[len("PyList<"):-1]
                ctx.var_rust_types[target_id] = elem_rs
                if elem_rs.startswith("Rc<RefCell<") and elem_rs.endswith(">>"):
                    ctx.var_storage_hints[target_id] = "ref"

    if iter_expr is not None:
        iter_str = _emit_for_iter(ctx, iter_expr, None)
    else:
        iter_str = "Vec::<Box<dyn std::any::Any>>::new().into_iter()"

    _emit(ctx, "for " + target_str + " in " + iter_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_for_iter(ctx: RsEmitContext, iter_node: JsonVal, target: JsonVal) -> str:
    """Generate the Rust iterator expression for a for-loop."""
    if not isinstance(iter_node, dict):
        return "[]"
    kind = _str(iter_node, "kind")
    resolved_type = _resolved_type_in_context(ctx, iter_node)
    iter_expr = _emit_expr(ctx, iter_node)
    iter_rs = _infer_node_rust_type(ctx, iter_node) or _infer_emitted_rust_type(iter_expr)

    if kind == "Call":
        func = iter_node.get("func")
        args = _list(iter_node, "args")
        func_name = ""
        if isinstance(func, dict):
            func_name = _str(func, "id")

        # range() call
        if func_name == "range":
            if len(args) == 1:
                end = _emit_expr(ctx, args[0])
                return "(0_i64.." + end + ")"
            elif len(args) == 2:
                start = _emit_expr(ctx, args[0])
                end = _emit_expr(ctx, args[1])
                return "(" + start + ".." + end + ")"
            elif len(args) == 3:
                start = _emit_expr(ctx, args[0])
                end = _emit_expr(ctx, args[1])
                step = _emit_expr(ctx, args[2])
                # For now, use a simple range (step handling simplified)
                return "(" + start + ".." + end + ").step_by(" + step + " as usize)"

        # enumerate()
        if func_name == "enumerate":
            if len(args) >= 1:
                inner_iter = _emit_for_iter(ctx, args[0], target)
                if len(args) == 2:
                    start_expr = _emit_expr(ctx, args[1])
                    return inner_iter + ".enumerate().map(|(i, v)| (" + start_expr + " + i as i64, v))"
                return inner_iter + ".enumerate().map(|(i, v)| (i as i64, v))"

        # reversed()
        if func_name == "reversed":
            if len(args) == 1:
                inner = _emit_expr(ctx, args[0])
                return inner + ".iter_snapshot().into_iter().rev()"

    if kind == "Tuple":
        elements = _list(iter_node, "elements")
        elem_types: list[str] = []
        if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
            elem_types = _split_generic_args(resolved_type[6:-1])
        rendered = [_emit_expr(ctx, e) for e in elements]
        if len(rendered) == 0:
            return "Vec::<PyAny>::new().into_iter()"
        same_elem_type = len(elem_types) == len(rendered) and len(elem_types) > 0
        if same_elem_type:
            first_elem_type = elem_types[0]
            for elem_type in elem_types:
                if elem_type != first_elem_type:
                    same_elem_type = False
                    break
        if same_elem_type:
            return "vec![" + ", ".join(rendered) + "].into_iter()"
        boxed: list[str] = []
        for idx, e in enumerate(elements):
            if not isinstance(e, dict):
                continue
            rendered_expr = rendered[idx] if idx < len(rendered) else _emit_expr(ctx, e)
            boxed.append(_expr_to_pyany(rendered_expr, _str(e, "resolved_type")))
        return "PyList::<PyAny>::from_vec(vec![" + ", ".join(boxed) + "]).iter_snapshot().into_iter()"

    # If resolved_type is unknown/empty, check ctx.var_types for the variable
    # JsonVal / PyAny iteration (treats as list)
    if resolved_type in ("JsonVal", "object", "Any", "Obj", "PyAny") or iter_rs == "PyAny":
        return "py_any_as_list(" + iter_expr + ".clone()).iter_snapshot().into_iter()"

    # List/collection iteration
    if resolved_type.startswith("list[") or resolved_type == "list":
        if isinstance(iter_node, dict) and _str(iter_node, "kind") == "Name":
            iter_name = _str(iter_node, "id")
            if iter_name in ctx.vec_vararg_names:
                return iter_expr + ".into_iter()"
        return iter_expr + ".iter_snapshot().into_iter()"

    if iter_rs.startswith("PyList<") and iter_rs.endswith(">"):
        if isinstance(iter_node, dict) and _str(iter_node, "kind") == "Name":
            iter_name = _str(iter_node, "id")
            if iter_name in ctx.vec_vararg_names:
                return iter_expr + ".into_iter()"
        return iter_expr + ".iter_snapshot().into_iter()"

    # String iteration (character by character)
    if resolved_type == "str":
        return iter_expr + ".chars().map(|c| c.to_string())"

    # Bytes/bytearray iteration (PyList<i64> uses iter_snapshot)
    if resolved_type in ("bytes", "bytearray"):
        return iter_expr + ".iter_snapshot().into_iter()"

    # Dict iteration (keys)
    if resolved_type.startswith("dict[") or resolved_type == "dict":
        return iter_expr + ".keys().cloned().collect::<Vec<_>>().into_iter()"

    # Set iteration
    if resolved_type.startswith("set[") or resolved_type == "set":
        return iter_expr + ".iter().cloned().collect::<Vec<_>>().into_iter()"

    # Default: try iter_snapshot for PyList, otherwise direct
    return iter_expr + ".into_iter()"


def _emit_static_range_for(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit StaticRangeForPlan."""
    target = node.get("target")
    start = node.get("start")
    stop = node.get("stop")
    step = node.get("step")
    body = _list(node, "body")

    target_str = "_i"
    if isinstance(target, dict):
        target_str = _rs_var_name(ctx, _str(target, "id"))
    elif isinstance(target, str):
        target_str = _rs_var_name(ctx, target)

    start_str = start if isinstance(start, str) else (_emit_expr(ctx, start) if start is not None else "0_i64")
    stop_str = stop if isinstance(stop, str) else (_emit_expr(ctx, stop) if stop is not None else "0_i64")
    step_val = 1
    if isinstance(step, int):
        step_val = step
    elif step is not None:
        step_str = _emit_expr(ctx, step)
        # Simplified: can't easily express negative step in Rust range
        _emit(ctx, "let mut " + target_str + ": i64 = " + start_str + ";")
        _emit(ctx, "while " + target_str + " < " + stop_str + " {")
        ctx.indent_level += 1
        _emit_body(ctx, body)
        _emit(ctx, target_str + " += " + step_str + ";")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        return

    if step_val == 1:
        _emit(ctx, "for " + target_str + " in " + start_str + ".." + stop_str + " {")
    elif step_val == -1:
        _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").rev() {")
    else:
        abs_step = step_val if step_val >= 0 else -step_val
        if step_val > 0:
            _emit(ctx, "for " + target_str + " in (" + start_str + ".." + stop_str + ").step_by(" + str(abs_step) + ") {")
        else:
            _emit(ctx, "for " + target_str + " in (" + stop_str + ".." + start_str + ").step_by(" + str(abs_step) + ").rev() {")

    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_runtime_iter_for(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit RuntimeIterForPlan."""
    _emit_for_core(ctx, node)


def _emit_while(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    test_str = _emit_bool_test(ctx, test)
    _emit(ctx, "while " + test_str + " {")
    ctx.indent_level += 1
    _emit_body(ctx, body)
    ctx.indent_level -= 1
    _emit(ctx, "}")

    if len(orelse) > 0:
        _emit(ctx, "// while/else not supported in Rust")


def _emit_body(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    for stmt in body:
        _emit_stmt(ctx, stmt)


def _collect_called_nested_capture_names(
    body: list[JsonVal],
    known_nested: dict[str, dict[str, JsonVal]],
) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    def _visit(node: JsonVal) -> None:
        if isinstance(node, dict):
            if _str(node, "kind") == "Call":
                func = node.get("func")
                if isinstance(func, dict) and _str(func, "kind") == "Name":
                    fn_name = _str(func, "id")
                    child = known_nested.get(fn_name)
                    if isinstance(child, dict):
                        child_capture_types = _dict(child, "capture_types")
                        for capture_key in child_capture_types.keys():
                            capture_name = str(capture_key)
                            if capture_name != "" and capture_name not in seen:
                                seen.add(capture_name)
                                names.append(capture_name)
            for value in node.values():
                if isinstance(value, (dict, list)):
                    _visit(value)
        elif isinstance(node, list):
            for item in node:
                _visit(item)

    _visit(body)
    return names


def _body_calls_self_next_tmp(node: JsonVal) -> bool:
    if isinstance(node, dict):
        if _str(node, "kind") == "Call":
            func = node.get("func")
            if isinstance(func, dict) and _str(func, "kind") == "Attribute" and _str(func, "attr") == "_next_tmp":
                owner = func.get("value")
                if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
                    return True
        for value in node.values():
            if _body_calls_self_next_tmp(value):
                return True
        return False
    if isinstance(node, list):
        for value in node:
            if _body_calls_self_next_tmp(value):
                return True
        return False
    return False


def _body_calls_self_method(node: JsonVal) -> bool:
    if isinstance(node, dict):
        if _str(node, "kind") == "Call":
            func = node.get("func")
            if isinstance(func, dict) and _str(func, "kind") == "Attribute":
                owner = func.get("value")
                if isinstance(owner, dict) and _str(owner, "kind") == "Name" and _str(owner, "id") == "self":
                    return True
        for value in node.values():
            if _body_calls_self_method(value):
                return True
        return False
    if isinstance(node, list):
        for value in node:
            if _body_calls_self_method(value):
                return True
        return False
    return False


def _emit_stmt(ctx: RsEmitContext, node: JsonVal) -> None:
    if not isinstance(node, dict):
        return
    kind = _str(node, "kind")

    if kind == "Expr":
        _emit_expr_stmt(ctx, node)
    elif kind == "Return":
        _emit_return(ctx, node)
    elif kind == "AnnAssign":
        _emit_ann_assign(ctx, node)
    elif kind == "Assign":
        _emit_assign(ctx, node)
    elif kind == "AugAssign":
        _emit_aug_assign(ctx, node)
    elif kind in ("FunctionDef", "ClosureDef"):
        _emit_function_def(ctx, node)
    elif kind == "ClassDef":
        _emit_class_def(ctx, node)
    elif kind == "If":
        _emit_if(ctx, node)
    elif kind == "While":
        _emit_while(ctx, node)
    elif kind == "ForCore":
        _emit_for_core(ctx, node)
    elif kind == "StaticRangeForPlan":
        _emit_static_range_for(ctx, node)
    elif kind == "RuntimeIterForPlan":
        _emit_runtime_iter_for(ctx, node)
    elif kind == "Raise":
        _emit_raise(ctx, node)
    elif kind == "Try":
        _emit(ctx, "// try unsupported in Rust selfhost emitter")
        _emit_body(ctx, _list(node, "body"))
    elif kind == "Pass":
        _emit(ctx, "// pass")
    elif kind == "Break":
        _emit(ctx, "break;")
    elif kind == "Continue":
        _emit(ctx, "continue;")
    elif kind == "comment":
        text = _str(node, "text")
        if text != "":
            _emit(ctx, "// " + text)
    elif kind == "blank":
        _emit_blank(ctx)
    elif kind in ("Import", "ImportFrom"):
        pass  # handled separately
    elif kind == "Delete":
        pass  # ignore del
    elif kind == "Global" or kind == "Nonlocal":
        pass  # ignore global/nonlocal
    elif kind == "Assert":
        test = node.get("test")
        msg = node.get("msg")
        test_str = _emit_expr(ctx, test)
        if msg is not None:
            msg_str = _emit_expr(ctx, msg)
            _emit(ctx, "assert!(" + test_str + ", \"{}\", " + msg_str + ");")
        else:
            _emit(ctx, "assert!(" + test_str + ");")
    elif kind == "With":
        _emit(ctx, "{")
        ctx.indent_level += 1
        _emit_body(ctx, _list(node, "body"))
        ctx.indent_level -= 1
        _emit(ctx, "}")
    elif kind == "TypeAlias":
        _emit_type_alias(ctx, node)
    elif kind == "VarDecl":
        _emit_var_decl(ctx, node)
    elif kind == "Swap":
        # a, b = b, a → temp swap using a local __swap_tmp variable
        left_node = node.get("left")
        right_node = node.get("right")
        left_name = _str(left_node, "id") if isinstance(left_node, dict) else ""
        right_name = _str(right_node, "id") if isinstance(right_node, dict) else ""
        if left_name != "" and right_name != "":
            safe_l = safe_rs_ident(left_name)
            safe_r = safe_rs_ident(right_name)
            _emit(ctx, "let __swap_tmp = " + safe_l + ".clone();")
            _emit(ctx, safe_l + " = " + safe_r + ".clone();")
            _emit(ctx, safe_r + " = __swap_tmp;")
        elif (
            isinstance(left_node, dict) and isinstance(right_node, dict)
            and _str(left_node, "kind") == "Subscript" and _str(right_node, "kind") == "Subscript"
        ):
            left_base = left_node.get("value")
            right_base = right_node.get("value")
            left_base_expr = _emit_expr(ctx, left_base)
            right_base_expr = _emit_expr(ctx, right_base)
            left_base_type = _str(left_base, "resolved_type") if isinstance(left_base, dict) else ""
            right_base_type = _str(right_base, "resolved_type") if isinstance(right_base, dict) else ""
            if left_base_expr == right_base_expr and (
                left_base_type.startswith("list[") or left_base_type == "list" or left_base_type in ("bytes", "bytearray")
            ) and (
                right_base_type.startswith("list[") or right_base_type == "list" or right_base_type in ("bytes", "bytearray")
            ):
                left_idx = _emit_expr(ctx, left_node.get("slice"))
                right_idx = _emit_expr(ctx, right_node.get("slice"))
                _emit(ctx, "let __swap_tmp = " + left_base_expr + ".get(" + left_idx + ");")
                _emit(ctx, left_base_expr + ".set(" + left_idx + ", " + left_base_expr + ".get(" + right_idx + "));")
                _emit(ctx, left_base_expr + ".set(" + right_idx + ", __swap_tmp);")
            else:
                _emit(ctx, "// unsupported Swap: non-list subscript targets")
        else:
            _emit(ctx, "// unsupported Swap: non-Name targets")
    else:
        _emit(ctx, "// unsupported stmt: " + kind)


def _emit_if(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    test = node.get("test")
    body = _list(node, "body")
    orelse = _list(node, "orelse")

    test_str = _emit_bool_test(ctx, test)
    _emit(ctx, "if " + test_str + " {")
    ctx.indent_level += 1
    narrowed_name = ""
    prev_var_type = ""
    prev_var_rs = ""
    if False and isinstance(test, dict) and _str(test, "kind") == "Compare":
        ops = _list(test, "ops")
        comps = _list(test, "comparators")
        left = test.get("left")
        if len(ops) == 1 and len(comps) == 1 and isinstance(left, dict):
            op0 = ops[0]
            op_name = op0 if isinstance(op0, str) else _str(op0, "kind")
            comp0 = comps[0]
            comp_is_none = isinstance(comp0, dict) and _str(comp0, "kind") == "Constant" and comp0.get("value") is None
            if op_name in ("IsNot", "!=") and comp_is_none and _str(left, "kind") == "Name":
                candidate = _str(left, "id")
                prev_var_type = ctx.var_types.get(candidate, "")
                prev_var_rs = ctx.var_rust_types.get(candidate, "")
                inner_type = _optional_inner_resolved_type(prev_var_type)
                inner_rs = _optional_inner_rs_type(prev_var_rs)
                if inner_type != "" or inner_rs != "":
                    narrowed_name = candidate
                    if inner_type != "":
                        ctx.var_types[candidate] = inner_type
                    if inner_rs != "":
                        ctx.var_rust_types[candidate] = inner_rs
    if False and narrowed_name == "" and isinstance(test, dict) and _str(test, "kind") == "Call":
        func_node = test.get("func")
        if isinstance(func_node, dict) and _str(func_node, "kind") == "Attribute" and _str(func_node, "attr") == "is_some":
            owner = func_node.get("value")
            if isinstance(owner, dict) and _str(owner, "kind") == "Name":
                candidate = _str(owner, "id")
                prev_var_type = ctx.var_types.get(candidate, "")
                prev_var_rs = ctx.var_rust_types.get(candidate, "")
                inner_type = _optional_inner_resolved_type(prev_var_type)
                inner_rs = _optional_inner_rs_type(prev_var_rs)
                if inner_type != "" or inner_rs != "":
                    narrowed_name = candidate
                    if inner_type != "":
                        ctx.var_types[candidate] = inner_type
                    if inner_rs != "":
                        ctx.var_rust_types[candidate] = inner_rs
    _emit_body(ctx, body)
    if narrowed_name != "":
        if prev_var_type != "":
            ctx.var_types[narrowed_name] = prev_var_type
        else:
            if narrowed_name in ctx.var_types:
                ctx.var_types.pop(narrowed_name)
        if prev_var_rs != "":
            ctx.var_rust_types[narrowed_name] = prev_var_rs
        else:
            if narrowed_name in ctx.var_rust_types:
                ctx.var_rust_types.pop(narrowed_name)
    ctx.indent_level -= 1

    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        next_if = orelse[0]
        test_node = _json_get(next_if, "test")
        _emit(ctx, "} else if " + _emit_bool_test(ctx, test_node) + " {")
        ctx.indent_level += 1
        _emit_body(ctx, _list(next_if, "body"))
        ctx.indent_level -= 1
        if isinstance(next_if, dict):
            _emit_remaining_orelse(ctx, next_if)
    elif len(orelse) > 0:
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "}")


def _emit_remaining_orelse(ctx: RsEmitContext, if_node: dict[str, JsonVal]) -> None:
    orelse = _list(if_node, "orelse")
    if len(orelse) == 1 and isinstance(orelse[0], dict) and _str(orelse[0], "kind") == "If":
        next_if = orelse[0]
        test_node = _json_get(next_if, "test")
        _emit(ctx, "} else if " + _emit_bool_test(ctx, test_node) + " {")
        ctx.indent_level += 1
        _emit_body(ctx, _list(next_if, "body"))
        ctx.indent_level -= 1
        if isinstance(next_if, dict):
            _emit_remaining_orelse(ctx, next_if)
    elif len(orelse) > 0:
        _emit(ctx, "} else {")
        ctx.indent_level += 1
        _emit_body(ctx, orelse)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "}")


def _emit_type_alias(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    value = node.get("value")
    prefix = "pub " if ctx.package_mode else ""
    if value is not None:
        if isinstance(value, dict):
            resolved_type = _str(value, "resolved_type")
            if resolved_type != "":
                _emit(ctx, prefix + "type " + safe_rs_ident(name) + " = " + _rs_type_for_context(ctx, resolved_type) + ";")
                return
    mapped_type = ctx.mapping.types.get(name, "")
    if mapped_type != "":
        _emit(ctx, prefix + "type " + safe_rs_ident(name) + " = " + mapped_type + ";")
        return
    if ctx.package_mode:
        _emit(ctx, prefix + "type " + safe_rs_ident(name) + " = PyAny;")
        return
    _emit(ctx, "// type alias: " + name)


def _emit_var_decl(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    resolved_type = _str(node, "resolved_type")
    if resolved_type == "":
        resolved_type = _str(node, "type")
    value = node.get("value")
    rs_name = _rs_var_name(ctx, name)
    ctx.declared_vars.add(name)
    rt = _rs_type_for_context(ctx, resolved_type) if resolved_type != "" else ""
    if value is not None:
        rhs = _emit_expr(ctx, value)
        if rt != "" and rt != "()":
            _emit(ctx, "let mut " + rs_name + ": " + rt + " = " + rhs + ";")
        else:
            _emit(ctx, "let mut " + rs_name + " = " + rhs + ";")
    else:
        if rt != "" and rt != "()":
            if rs_name == "_":
                _emit(ctx, "let _: " + rt + ";")
            else:
                _emit(ctx, "let mut " + rs_name + ": " + rt + ";")
        else:
            if rs_name != "_":
                _emit(ctx, "let mut " + rs_name + ";")


# ---------------------------------------------------------------------------
# Function definition
# ---------------------------------------------------------------------------

def _emit_function_def(ctx: RsEmitContext, node: dict[str, JsonVal], owner: str = "") -> None:
    name = _str(node, "name")
    raw_arg_order = _list(node, "arg_order")
    arg_order: list[str] = []
    for raw_arg in raw_arg_order:
        if isinstance(raw_arg, str):
            arg_order.append(raw_arg)
    arg_types = _dict(node, "arg_types")
    arg_usage = _dict(node, "arg_usage")
    return_type = _str(node, "return_type")
    body = _list(node, "body")
    decorators = _list(node, "decorator_list")
    is_static = _decorators_have_id(decorators, "staticmethod")
    is_property = _decorators_have_id(decorators, "property")
    is_classmethod = _decorators_have_id(decorators, "classmethod")

    leading_trivia = _list(node, "leading_trivia")
    for trivia in leading_trivia:
        if isinstance(trivia, dict):
            trivia_kind = _str(trivia, "kind")
            if trivia_kind == "comment":
                text = _str(trivia, "text")
                if text != "":
                    _emit(ctx, "// " + text)
            elif trivia_kind == "blank":
                _emit_blank(ctx)

    # Build parameter list
    params: list[str] = []
    box_any_param_names: list[str] = []
    has_self = "self" in arg_order
    is_method = owner != "" and has_self
    is_nested = not ctx.at_module_level and owner == ""

    for arg in arg_order:
        if not isinstance(arg, str):
            continue
        if arg == "self":
            self_mutates = bool(node.get("mutates_self", True))
            if not self_mutates and (_body_calls_self_next_tmp(body) or _body_calls_self_method(body)):
                self_mutates = True
            params.append("&mut self" if self_mutates else "&self")
            continue
        arg_type = _str(arg_types, arg)
        if arg_type in ctx.trait_names:
            rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
        elif _needs_parent_trait_object(ctx, arg_type):
            # Parent class used as parameter type → use dyn trait for polymorphism
            rs_arg_type = "Box<dyn " + safe_rs_ident(arg_type) + "Methods>"
        else:
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        if (is_nested or name == "_walk") and "Box<dyn Fn" in rs_arg_type and rs_arg_type.endswith(">"):
            rs_arg_type = "&" + rs_arg_type[len("Box<"):-1]
        if rs_arg_type == "Box<dyn std::any::Any>" and not is_nested:
            params.append(safe_rs_ident(arg) + ": impl IntoPyBoxAny")
            box_any_param_names.append(arg)
            continue
        # Add `mut` only if arg_usage says "reassigned" (EAST3 §arg_usage),
        # or if the type is Box<T> (fields may be mutated via &mut self patterns).
        is_reassigned = _str(arg_usage, arg) == "reassigned"
        is_box = rs_arg_type.startswith("Box<")
        mut_prefix = "mut " if (is_reassigned or is_box) else ""
        params.append(mut_prefix + safe_rs_ident(arg) + ": " + rs_arg_type)

    # Varargs (*args) → PyList<ElemType>
    vararg_name = _str(node, "vararg_name")
    vararg_type = _str(node, "vararg_type")
    if vararg_name != "":
        elem_type = _rs_type_for_context(ctx, vararg_type) if vararg_type != "" else "Box<dyn std::any::Any>"
        if elem_type == "Box<dyn std::any::Any>":
            params.append(safe_rs_ident(vararg_name) + ": Vec<" + elem_type + ">")
        else:
            params.append(safe_rs_ident(vararg_name) + ": PyList<" + elem_type + ">")

    params_str = ", ".join(params)
    type_params = _collect_signature_type_params(ctx, arg_types, return_type)
    generic_suffix = "<" + ", ".join(type_params) + ">" if type_params else ""

    # Return type
    if return_type == "" or return_type == "None" or return_type == "none":
        ret_str = ""
    else:
        if _needs_parent_trait_object(ctx, return_type):
            rt = "Box<dyn " + safe_rs_ident(return_type) + "Methods>"
        else:
            rt = _rs_type_for_context(ctx, return_type)
        if rt == "()":
            ret_str = ""
        else:
            ret_str = " -> " + rt

    # Function name (handle module private symbol prefix)
    if owner != "":
        fn_name = safe_rs_ident(name)
    else:
        fn_name = _rs_symbol_name(ctx, name)
    # Save/restore context
    prev_return_type = ctx.current_return_type
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)
    prev_storage_var_types = dict(ctx.storage_var_types)
    prev_nested_fn = ctx.current_nested_fn
    prev_nested_capture_args = dict(ctx.nested_capture_args)
    prev_function_signatures = dict(ctx.function_signatures)
    ctx.current_return_type = return_type
    ctx.declared_vars = set()

    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            child_name = _str(stmt, "name")
            if child_name != "":
                ctx.function_signatures[child_name] = stmt
                child_capture_types = _dict(stmt, "capture_types")
                if len(child_capture_types) > 0:
                    child_capture_names: list[str] = []
                    for capture_name in child_capture_types:
                        child_capture_names.append(str(capture_name))
                    ctx.nested_capture_args[_rs_symbol_name(ctx, child_name)] = child_capture_names

    # Add parameters to declared vars
    for arg in arg_order:
        if isinstance(arg, str) and arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type
                ctx.storage_var_types[arg] = arg_type
    if vararg_name != "":
        ctx.declared_vars.add(vararg_name)
        if vararg_type != "":
            ctx.var_types[vararg_name] = "list[" + vararg_type + "]"
            if _rs_type_for_context(ctx, vararg_type) == "Box<dyn std::any::Any>":
                ctx.vec_vararg_names.add(vararg_name)
    # Nested function (inside another function body, not a class method): emit as closure
    is_recursive_nested = is_nested and _bool(node, "is_recursive")
    fn_prefix = "pub " if (ctx.package_mode and not is_nested) else ""
    if is_nested:
        capture_types = _dict(node, "capture_types")
        capture_names: list[str] = []
        for capture_name in capture_types:
            capture_names.append(str(capture_name))
        extra_params: list[str] = []
        if is_recursive_nested:
            known_nested: dict[str, dict[str, JsonVal]] = {}
            for known_name, sig in ctx.function_signatures.items():
                if isinstance(sig, dict) and _str(sig, "kind") in ("FunctionDef", "ClosureDef"):
                    known_capture_types = _dict(sig, "capture_types")
                    if len(known_capture_types) > 0:
                        known_nested[known_name] = sig
            for extra_capture_name in _collect_called_nested_capture_names(body, known_nested):
                if extra_capture_name not in capture_names:
                    capture_names.append(extra_capture_name)
            for capture_name in capture_names:
                capture_type = _str(capture_types, capture_name)
                if capture_type == "":
                    capture_type = ctx.var_types.get(capture_name, "")
                if capture_type == "":
                    continue
                extra_params.append(_rs_var_name(ctx, capture_name) + ": " + _rs_type_for_context(ctx, capture_type))
                ctx.declared_vars.add(capture_name)
                ctx.var_types[capture_name] = capture_type
            all_params = params + extra_params
            all_params_str = ", ".join(all_params)
            ctx.current_nested_fn = ""
            ctx.nested_capture_args[fn_name] = capture_names
            _emit(ctx, "fn " + fn_name + generic_suffix + "(" + all_params_str + ")" + ret_str + " {")
        else:
            for capture_name in capture_names:
                capture_type = _str(capture_types, capture_name)
                if capture_type == "":
                    continue
                extra_params.append(_rs_var_name(ctx, capture_name) + ": " + _rs_type_for_context(ctx, capture_type))
                ctx.declared_vars.add(capture_name)
                ctx.var_types[capture_name] = capture_type
            ctx.current_nested_fn = fn_name
            ctx.nested_capture_args[fn_name] = capture_names
            _emit(ctx, "let " + fn_name + " = |" + ", ".join(params + extra_params) + "|" + ret_str + " {")
    else:
        ctx.current_nested_fn = ""
        _emit(ctx, fn_prefix + "fn " + fn_name + generic_suffix + "(" + params_str + ")" + ret_str + " {")
    ctx.indent_level += 1
    prev_module_level = ctx.at_module_level
    ctx.at_module_level = False
    for arg in box_any_param_names:
        _emit(ctx, "let mut " + safe_rs_ident(arg) + " = " + safe_rs_ident(arg) + ".into_py_box_any();")
    body_is_empty = len(body) == 0 or _all_pass_stmts(body)
    if body_is_empty and return_type not in ("", "None", "NoneType"):
        # Abstract/stub method: emit todo!()
        _emit(ctx, 'todo!("abstract method ' + fn_name + '")')
    else:
        _emit_body(ctx, body)
        if (
            return_type not in ("", "None", "none")
            and len(body) > 0
            and isinstance(body[-1], dict)
            and _str(body[-1], "kind") == "While"
        ):
            last_test = _json_get(body[-1], "test")
            last_test_is_true = False
            if isinstance(last_test, dict) and _str(last_test, "kind") == "Constant":
                last_test_value = last_test.get("value")
                if isinstance(last_test_value, bool) and last_test_value:
                    last_test_is_true = True
            if last_test_is_true:
                _emit(ctx, 'panic!("unreachable after loop");')
    ctx.at_module_level = prev_module_level
    ctx.indent_level -= 1
    if is_nested:
        _emit(ctx, "};")
    else:
        _emit(ctx, "}")

    # Restore context
    ctx.current_return_type = prev_return_type
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types
    ctx.storage_var_types = prev_storage_var_types
    ctx.nested_capture_args = prev_nested_capture_args
    ctx.function_signatures = prev_function_signatures
    ctx.current_nested_fn = prev_nested_fn
    if vararg_name != "" and vararg_name in ctx.vec_vararg_names:
        ctx.vec_vararg_names.remove(vararg_name)


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

def _repr_constant_default(node: dict[str, JsonVal]) -> str:
    """Return a simple Rust literal string for a constant node (for default values)."""
    value = node.get("value")
    resolved_type = _str(node, "resolved_type")
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value) + "_i64"
    if isinstance(value, float):
        return str(value) + "_f64"
    if isinstance(value, str):
        text_value = _as_str(value)
        escaped = text_value.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"" + escaped + "\".to_string()"
    return "Default::default()"


def _collect_class_info(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Collect class metadata for later use during emission."""
    name = _str(node, "name")
    if name == "":
        return
    ctx.class_names.add(name)
    if _str(node, "class_storage_hint") == "ref":
        ctx.ref_classes.add(name)
    body = _list(node, "body")

    base_str = _str(node, "base")
    if base_str != "" and base_str != "None":
        ctx.class_bases[name] = base_str
    else:
        bases = _list(node, "bases")
        if len(bases) > 0:
            base = bases[0]
            if isinstance(base, dict):
                ctx.class_bases[name] = _str(base, "id")

    fields: dict[str, str] = {}
    field_defaults: dict[str, str | None] = {}
    methods: dict[str, dict[str, JsonVal]] = {}
    statics: set[str] = set()
    class_vars: dict[str, str] = {}

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            decorators = _list(stmt, "decorator_list")
            is_static = _decorators_have_id(decorators, "staticmethod")
            if is_static:
                statics.add(fn_name)
            methods[fn_name] = stmt
            # Collect instance fields from __init__ body
            if fn_name == "__init__":
                for init_stmt in _list(stmt, "body"):
                    if not isinstance(init_stmt, dict):
                        continue
                    init_kind = _str(init_stmt, "kind")
                    if init_kind in ("AnnAssign", "Assign"):
                        itarget = init_stmt.get("target")
                        if isinstance(itarget, dict) and _str(itarget, "kind") == "Attribute":
                            iobj = itarget.get("value")
                            if isinstance(iobj, dict) and _str(iobj, "id") == "self":
                                ifield = _str(itarget, "attr")
                                itype = _str(init_stmt, "resolved_type")
                                if itype == "":
                                    itype = _str(init_stmt, "decl_type")
                                if itype == "":
                                    itype = _str(itarget, "resolved_type")
                                if ifield != "" and itype != "":
                                    fields[ifield] = itype
                                    ival = init_stmt.get("value")
                                    if isinstance(ival, dict) and ival.get("kind") == "Constant":
                                        field_defaults[ifield] = _repr_constant_default(ival)
                                    else:
                                        field_defaults[ifield] = None
        elif stmt_kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if resolved_type == "":
                    resolved_type = _str(stmt, "decl_type")
                if field_name != "" and resolved_type != "":
                    val_node = stmt.get("value")
                    is_dataclass = _bool(node, "dataclass")
                    is_class_var = stmt_kind == "Assign" or (val_node is not None and not is_dataclass)
                    if is_class_var:
                        class_vars[field_name] = resolved_type
                    else:
                        fields[field_name] = resolved_type
                    if isinstance(val_node, dict) and val_node.get("kind") == "Constant":
                        field_defaults[field_name] = _repr_constant_default(val_node)
                    else:
                        field_defaults[field_name] = None

    parent_name = ctx.class_bases.get(name, "")
    if parent_name != "" and parent_name in ctx.class_fields:
        for pf, pt in ctx.class_fields[parent_name].items():
            if pf not in fields:
                fields[pf] = pt
                field_defaults[pf] = ctx.class_field_defaults.get(parent_name, {}).get(pf)

    ctx.class_fields[name] = fields
    ctx.class_field_defaults[name] = field_defaults
    ctx.class_vars[name] = class_vars
    ctx.class_instance_methods[name] = methods
    ctx.class_static_methods[name] = statics
    decorators_raw = _list(node, "decorators")
    for dec in decorators_raw:
        if _decorator_id_matches(dec, "trait"):
            ctx.trait_names.add(name)
    base_raw = _str(node, "base")
    base_id = ctx.class_bases.get(name, base_raw)
    if base_id in ("Enum", "IntEnum", "IntFlag", "Flag"):
        members: list[str] = []
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            if _str(stmt, "kind") == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and _str(target, "kind") == "Name":
                    members.append(_str(target, "id"))
        ctx.enum_members[name] = members
        ctx.enum_bases[name] = base_id
    # Collect @property methods
    property_methods: set[str] = set()
    for stmt in body:
        if isinstance(stmt, dict) and _str(stmt, "kind") in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            # EAST3 uses "decorators" list (strings or dicts); AST uses "decorator_list"
            decs = _list(stmt, "decorators") + _list(stmt, "decorator_list")
            is_prop = _decorators_have_id(decs, "property")
            if is_prop:
                property_methods.add(fn_name)
    ctx.class_property_methods[name] = property_methods


def _walk_nodes(node: JsonVal) -> list[dict[str, JsonVal]]:
    out: list[dict[str, JsonVal]] = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            out.extend(_walk_nodes(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk_nodes(item))
    return out


def _mark_ref_classes_from_function(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    arg_types = _dict(node, "arg_types")
    class_params: dict[str, str] = {}
    for arg_name, arg_type_any in arg_types.items():
        arg_type = str(arg_type_any) if isinstance(arg_type_any, str) else ""
        if arg_type in ctx.class_names:
            class_params[str(arg_name)] = arg_type
    if not class_params:
        return
    for sub in _walk_nodes(_list(node, "body")):
        kind = _str(sub, "kind")
        if kind not in ("Assign", "AugAssign"):
            continue
        target = sub.get("target")
        if not isinstance(target, dict) or _str(target, "kind") != "Attribute":
            continue
        owner = target.get("value")
        if not isinstance(owner, dict) or _str(owner, "kind") != "Name":
            continue
        owner_name = _str(owner, "id")
        if owner_name == "self":
            continue
        owner_type = class_params.get(owner_name, "")
        if owner_type != "":
            ctx.ref_classes.add(owner_type)


def _emit_enum_class(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    """Emit a Python Enum subclass as a Rust newtype struct with const members."""
    name = _str(node, "name")
    rs_name = safe_rs_ident(name)
    body = _list(node, "body")
    base = ctx.enum_bases.get(name, "Enum")
    # Use i64 as the underlying type
    _emit_blank(ctx)
    _emit(ctx, "#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]")
    _emit(ctx, "pub struct " + rs_name + "(pub i64);")
    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_name + " {")
    ctx.indent_level += 1
    member_names: list[str] = []
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind == "Assign":
            target = stmt.get("target")
            val_node = stmt.get("value")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                member_name = _str(target, "id")
                member_names.append(member_name)
                if isinstance(val_node, dict):
                    val_str = _emit_expr(ctx, val_node)
                else:
                    val_str = "0"
                _emit(ctx, "pub const " + member_name + ": " + rs_name + " = " + rs_name + "(" + val_str + ");")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PyStringify
    _emit_blank(ctx)
    _emit(ctx, "impl PyStringify for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn py_stringify(&self) -> String {")
    ctx.indent_level += 1
    _emit(ctx, "self.0.to_string()")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PartialEq<i64> for comparisons like Status::OK == 0
    _emit_blank(ctx)
    _emit(ctx, "impl PartialEq<i64> for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn eq(&self, other: &i64) -> bool { self.0 == *other }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    _emit(ctx, "impl PartialEq<" + rs_name + "> for i64 {")
    ctx.indent_level += 1
    _emit(ctx, "fn eq(&self, other: &" + rs_name + ") -> bool { *self == other.0 }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # Implement PyAnyToI64Arg for py_int() conversions
    _emit(ctx, "impl PyAnyToI64Arg for " + rs_name + " {")
    ctx.indent_level += 1
    _emit(ctx, "fn py_any_to_i64_arg(&self) -> i64 { self.0 }")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    # For IntFlag: also emit BitOr, BitAnd, BitXor
    if base in ("IntFlag", "Flag"):
        _emit_blank(ctx)
        _emit(ctx, "impl std::ops::BitOr for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitor(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 | rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit(ctx, "impl std::ops::BitAnd for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitand(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 & rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        _emit(ctx, "impl std::ops::BitXor for " + rs_name + " {")
        ctx.indent_level += 1
        _emit(ctx, "type Output = " + rs_name + ";")
        _emit(ctx, "fn bitxor(self, rhs: " + rs_name + ") -> " + rs_name + " { " + rs_name + "(self.0 ^ rhs.0) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")
    # Resolver may lower enum members to module-level aliases like COLOR_RED / STATUS_OK.
    # Emit matching aliases so both `Color::RED` and `COLOR_RED` work.
    for member_name in member_names:
        _emit_blank(ctx)
        _emit(ctx, "const " + safe_rs_ident(name).upper() + "_" + safe_rs_ident(member_name).upper() + ": " + rs_name + " = " + rs_name + "::" + safe_rs_ident(member_name) + ";")


def _emit_class_def(ctx: RsEmitContext, node: dict[str, JsonVal]) -> None:
    name = _str(node, "name")
    if name == "":
        return
    body = _list(node, "body")
    bases = _list(node, "bases")
    decorators = _list(node, "decorators")  # EAST3 uses "decorators", not "decorator_list"
    rs_name = safe_rs_ident(name)

    # Emit Enum subclasses as a newtype struct with const members
    if name in ctx.enum_bases:
        _emit_enum_class(ctx, node)
        return

    is_trait = name in ctx.trait_names or _decorators_have_id(decorators, "trait")

    # Detect @implements(...) decorator to get trait implementations for this class
    implements_traits: list[str] = []
    for dec in decorators:
        dec_str = dec if isinstance(dec, str) else (_str(dec, "repr") or _str(dec, "id"))
        if dec_str.startswith("implements(") and dec_str.endswith(")"):
            inner = dec_str[len("implements("):-1]
            for part in inner.split(","):
                t = part.strip()
                if t != "":
                    implements_traits.append(t)

    if is_trait:
        _emit_trait_definition(ctx, name, body)
        return

    leading_trivia = _list(node, "leading_trivia")
    for trivia in leading_trivia:
        if isinstance(trivia, dict):
            trivia_kind = _str(trivia, "kind")
            if trivia_kind == "comment":
                text = _str(trivia, "text")
                if text != "":
                    _emit(ctx, "// " + text)
            elif trivia_kind == "blank":
                _emit_blank(ctx)

    # Collect field types from __init__
    fields: dict[str, str] = {}
    init_method: dict[str, JsonVal] = {}
    has_init_method = False
    other_methods: list[dict[str, JsonVal]] = []
    class_assign_stmts: list[dict[str, JsonVal]] = []  # class-level Assign/valued AnnAssign stmts (class vars)

    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name == "__init__":
                init_method = stmt
                has_init_method = True
                # Collect field assignments from __init__ body
                for init_stmt in _list(stmt, "body"):
                    if not isinstance(init_stmt, dict):
                        continue
                    init_kind = _str(init_stmt, "kind")
                    if init_kind in ("AnnAssign", "Assign"):
                        target = init_stmt.get("target")
                        if isinstance(target, dict) and _str(target, "kind") == "Attribute":
                            attr_obj = target.get("value")
                            if isinstance(attr_obj, dict) and _str(attr_obj, "id") == "self":
                                field_name = _str(target, "attr")
                                # Try multiple sources for the field type
                                resolved_type = _str(init_stmt, "resolved_type")
                                if resolved_type == "":
                                    resolved_type = _str(init_stmt, "decl_type")
                                if resolved_type == "":
                                    resolved_type = _str(target, "resolved_type")
                                if field_name != "" and resolved_type != "":
                                    fields[field_name] = resolved_type
            else:
                other_methods.append(stmt)
        elif stmt_kind == "AnnAssign":
            # Uninitialized AnnAssign is an instance field declaration.
            # Valued AnnAssign at class scope is a class variable, except for dataclass fields.
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                resolved_type = _str(stmt, "resolved_type")
                if resolved_type == "":
                    resolved_type = _str(stmt, "decl_type")
                if resolved_type == "" and isinstance(stmt.get("annotation"), str):
                    resolved_type = _str(stmt, "annotation")
                is_dataclass = _bool(node, "dataclass")
                if field_name != "" and resolved_type != "" and not field_name.startswith("__") and (stmt.get("value") is None or is_dataclass):
                    fields[field_name] = resolved_type
                elif field_name != "" and resolved_type != "" and not field_name.startswith("__"):
                    class_assign_stmts.append(stmt)
        elif stmt_kind == "Assign":
            # Class-level plain assignment (no type annotation) = class variable (not instance field)
            target = stmt.get("target")
            if isinstance(target, dict) and _str(target, "kind") == "Name":
                field_name = _str(target, "id")
                if field_name != "" and not field_name.startswith("__"):
                    class_assign_stmts.append(stmt)

    # Inherit parent fields (struct fields from parent class)
    parent_class = ctx.class_bases.get(name, "")
    if parent_class != "" and parent_class in ctx.class_fields:
        for pf, pt in ctx.class_fields[parent_class].items():
            if pf not in fields:
                fields[pf] = pt

    # Exception-style classes often forward `msg` via super().__init__(msg) without a local self.msg assignment.
    if has_init_method and "msg" not in fields:
        raw_init_arg_order = _list(init_method, "arg_order")
        init_arg_order: list[str] = []
        for raw_init_arg in raw_init_arg_order:
            if isinstance(raw_init_arg, str):
                init_arg_order.append(raw_init_arg)
        if "msg" in init_arg_order:
            for init_stmt in _list(init_method, "body"):
                if not isinstance(init_stmt, dict) or _str(init_stmt, "kind") != "Expr":
                    continue
                init_value = init_stmt.get("value")
                if not isinstance(init_value, dict) or _str(init_value, "kind") != "Call":
                    continue
                init_func = init_value.get("func")
                if not isinstance(init_func, dict) or _str(init_func, "kind") != "Attribute":
                    continue
                init_owner = init_func.get("value")
                if _str(init_func, "attr") != "__init__":
                    continue
                if not isinstance(init_owner, dict) or _str(init_owner, "kind") != "Call":
                    continue
                init_owner_func = init_owner.get("func")
                if isinstance(init_owner_func, dict) and _str(init_owner_func, "id") in ("super", "py_super"):
                    fields["msg"] = "str"
                    break

    class_var_static_names: dict[str, str] = {}
    for ca_stmt in class_assign_stmts:
        ca_target = ca_stmt.get("target")
        if not isinstance(ca_target, dict):
            continue
        ca_name = _str(ca_target, "id")
        if ca_name == "":
            continue
        class_var_static_names[ca_name] = safe_rs_ident(name).upper() + "_" + safe_rs_ident(ca_name).upper()
    if len(class_var_static_names) > 0:
        ctx.class_var_statics[name] = class_var_static_names
        for ca_stmt in class_assign_stmts:
            ca_target = ca_stmt.get("target")
            if not isinstance(ca_target, dict):
                continue
            ca_name = _str(ca_target, "id")
            ca_val = ca_stmt.get("value")
            ca_type = _str(ca_stmt, "resolved_type") or _str(ca_stmt, "decl_type") or _str(ca_stmt, "annotation")
            if ca_name == "" or ca_val is None:
                continue
            static_name = class_var_static_names[ca_name]
            rs_t = _rs_type_for_context(ctx, ca_type) if ca_type != "" else "i64"
            const_val = _emit_expr(ctx, ca_val)
            _emit_blank(ctx)
            vis = "pub " if ctx.package_mode else ""
            _emit(ctx, vis + "static mut " + static_name + ": " + rs_t + " = " + const_val + ";")

    # Emit struct definition
    _emit_blank(ctx)
    if len(fields) > 0:
        _emit(ctx, "#[derive(Debug, Clone)]")
        _emit(ctx, "pub struct " + rs_name + " {")
        ctx.indent_level += 1
        for field_name, field_type in fields.items():
            rt = _rs_type_for_context(ctx, field_type)
            _emit(ctx, "pub " + safe_rs_ident(field_name) + ": " + rt + ",")
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        _emit(ctx, "#[derive(Debug, Clone)]")
        _emit(ctx, "pub struct " + rs_name + " {}")

    # Emit impl block
    prev_class = ctx.current_class
    ctx.current_class = name
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)

    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_name + " {")
    ctx.indent_level += 1

    # Emit new() constructor from __init__
    if has_init_method:
        _emit_init_as_new(ctx, init_method, rs_name, fields)
    elif len(fields) > 0:
        # Generate new() taking all fields as args (works for both dataclasses and regular classes)
        param_parts: list[str] = []
        for field_name, field_type in fields.items():
            param_parts.append(safe_rs_ident(field_name) + ": " + _rs_type_for_context(ctx, field_type))
        params = ", ".join(param_parts)
        ctor_prefix = "pub " if ctx.package_mode else ""
        _emit(ctx, ctor_prefix + "fn new(" + params + ") -> Self {")
        ctx.indent_level += 1
        _emit(ctx, rs_name + " {")
        ctx.indent_level += 1
        for field_name in fields.keys():
            _emit(ctx, safe_rs_ident(str(field_name)) + ": " + safe_rs_ident(str(field_name)) + ",")
        ctx.indent_level -= 1
        _emit(ctx, "}")
        ctx.indent_level -= 1
        _emit(ctx, "}")
    else:
        ctor_prefix = "pub " if ctx.package_mode else ""
        _emit(ctx, ctor_prefix + "fn new() -> Self {")
        ctx.indent_level += 1
        _emit(ctx, rs_name + " {}")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # Emit other methods
    for method in other_methods:
        _emit_blank(ctx)
        _emit_function_def(ctx, method, owner=name)

    # Emit inherited methods from parent class (not overridden in child)
    child_method_names: set[str] = set()
    for child_method in other_methods:
        child_method_name = _str(child_method, "name")
        if child_method_name != "":
            child_method_names.add(child_method_name)
    if has_init_method:
        child_method_names.add("__init__")
    parent_class = ctx.class_bases.get(name, "")
    if parent_class != "" and parent_class in ctx.class_instance_methods and parent_class not in ctx.trait_names:
        parent_methods = ctx.class_instance_methods[parent_class]
        for mname, mnode in parent_methods.items():
            if mname not in child_method_names and mname != "__init__":
                _emit_blank(ctx)
                _emit_function_def(ctx, mnode, owner=name)

    # Emit class-level variables as associated consts (for Holder::X pattern)
    for ca_stmt in class_assign_stmts:
        ca_target = ca_stmt.get("target")
        if not isinstance(ca_target, dict):
            continue
        ca_name = _str(ca_target, "id")
        if ca_name in class_var_static_names:
            continue
        ca_val = ca_stmt.get("value")
        ca_type = _str(ca_stmt, "resolved_type") or _str(ca_stmt, "decl_type")
        if ca_name == "" or ca_val is None:
            continue
        rs_ca_name = safe_rs_ident(ca_name).upper()
        # For tuple/list of homogeneous constants → const &'static [T]
        ca_val_kind = _str(ca_val, "kind") if isinstance(ca_val, dict) else ""
        if ca_val_kind == "Tuple" or ca_val_kind == "List":
            elems = _list(ca_val, "elements")
            all_const = _all_constant_nodes(elems)
            if all_const and len(elems) > 0:
                elem_type = _str(elems[0], "resolved_type") if elems else "int64"
                rs_elem = _rs_type_for_context(ctx, elem_type)
                const_elems = ", ".join(_emit_expr(ctx, e) for e in elems)
                _emit_blank(ctx)
                vis = "pub " if ctx.package_mode else ""
                _emit(ctx, vis + "const " + rs_ca_name + ": &'static [" + rs_elem + "] = &[" + const_elems + "];")
                continue
        # For simple constants → const T
        if isinstance(ca_val, dict) and ca_val.get("kind") == "Constant":
            rs_t = _rs_type_for_context(ctx, ca_type) if ca_type != "" else "i64"
            const_val = _emit_expr(ctx, ca_val)
            _emit_blank(ctx)
            vis = "pub " if ctx.package_mode else ""
            _emit(ctx, vis + "const " + rs_ca_name + ": " + rs_t + " = " + const_val + ";")
            continue
        # Fallback: emit as comment
        _emit_blank(ctx)
        _emit(ctx, "// class_var " + rs_ca_name + ": (non-const value, skipped)")

    ctx.indent_level -= 1
    _emit(ctx, "}")

    ctx.current_class = prev_class
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types

    # Emit trait implementations
    for base_node in bases:
        if isinstance(base_node, dict):
            base_name = _str(base_node, "id")
            if base_name != "" and base_name in ctx.trait_names:
                _emit_trait_impl(ctx, name, base_name)

    # Emit @implements trait impls for this class (including transitive base traits)
    emitted_trait_impls: set[str] = set()
    def _emit_trait_impl_recursive(class_name: str, trait_name: str) -> None:
        if trait_name in emitted_trait_impls:
            return
        if trait_name not in ctx.trait_names:
            return
        # First emit base trait impls (for traits that extend other traits)
        base_of_trait = ctx.class_bases.get(trait_name, "")
        if base_of_trait != "" and base_of_trait in ctx.trait_names:
            _emit_trait_impl_recursive(class_name, base_of_trait)
        emitted_trait_impls.add(trait_name)
        _emit_trait_methods_impl(ctx, class_name, trait_name)

    for trait_name in implements_traits:
        _emit_trait_impl_recursive(name, trait_name)

    # Emit PyStringify for user-defined classes (needed for str(instance))
    if name not in ctx.enum_bases:
        _emit_blank(ctx)
        _emit(ctx, "impl PyStringify for " + rs_name + " {")
        ctx.indent_level += 1
        class_methods_for_name = ctx.class_instance_methods.get(name)
        has_str_method = False
        if isinstance(class_methods_for_name, dict) and "__str__" in class_methods_for_name:
            has_str_method = True
        if "msg" in fields and fields["msg"] == "str":
            _emit(ctx, "fn py_stringify(&self) -> String { self.msg.clone() }")
        elif has_str_method:
            _emit(ctx, "fn py_stringify(&self) -> String { self.__str__() }")
        else:
            _emit(ctx, "fn py_stringify(&self) -> String { format!(\"{:?}\", self) }")
        ctx.indent_level -= 1
        _emit(ctx, "}")

    # If this class is a parent class, emit a <Name>Methods trait and impl for it
    if _needs_parent_trait_object(ctx, name):
        _emit_parent_class_methods_trait(ctx, name)
        _emit_parent_class_methods_impl(ctx, name)

    # If this class has ancestors in parent_class_names, emit impl <Ancestor>Methods for this class
    ancestor = ctx.class_bases.get(name, "")
    while ancestor != "" and ancestor in ctx.class_names:
        if _needs_parent_trait_object(ctx, ancestor):
            _emit_parent_class_methods_impl(ctx, name, as_type=ancestor)
        ancestor = ctx.class_bases.get(ancestor, "")


def _emit_init_as_new(
    ctx: RsEmitContext,
    init_method: dict[str, JsonVal],
    rs_name: str,
    fields: dict[str, str],
) -> None:
    """Emit __init__ as Rust new() constructor."""
    raw_arg_order = _list(init_method, "arg_order")
    arg_order: list[str] = []
    for raw_arg in raw_arg_order:
        if isinstance(raw_arg, str):
            arg_order.append(raw_arg)
    arg_types = _dict(init_method, "arg_types")
    body = _list(init_method, "body")

    params: list[str] = []
    box_any_param_names: list[str] = []
    for arg in arg_order:
        if arg == "self":
            continue
        arg_type = _str(arg_types, arg)
        rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        if rs_arg_type == "Box<dyn std::any::Any>":
            params.append(safe_rs_ident(arg) + ": impl IntoPyBoxAny")
            box_any_param_names.append(arg)
        else:
            params.append(safe_rs_ident(arg) + ": " + rs_arg_type)

    params_str = ", ".join(params)
    ctor_prefix = "pub " if ctx.package_mode else ""
    _emit(ctx, ctor_prefix + "fn new(" + params_str + ") -> Self {")
    ctx.indent_level += 1

    prev_declared = set(ctx.declared_vars)
    prev_constructor_locals = set(ctx.constructor_field_locals)
    prev_constructor_label = ctx.constructor_block_label
    prev_at_module_level = ctx.at_module_level
    prev_current_class = ctx.current_class
    ctx.at_module_level = False
    # Keep the original class name in context so field type lookups during
    # constructor lowering still hit ctx.class_fields / ctx.class_vars.
    if prev_current_class != "":
        ctx.current_class = prev_current_class
    else:
        ctx.current_class = rs_name
    ctx.declared_vars = set()
    for arg in arg_order:
        if arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type
    ctx.constructor_field_locals = set(fields.keys())
    ctx.constructor_block_label = _next_temp(ctx, "ctor")

    parent_class_for_init = ctx.class_bases.get(rs_name, "")
    if parent_class_for_init == "":
        parent_class_for_init = ctx.class_bases.get(ctx.current_class, "")
    parent_defaults: dict[str, str | None] = {}
    if parent_class_for_init != "":
        parent_defaults_for_class = ctx.class_field_defaults.get(parent_class_for_init)
        if isinstance(parent_defaults_for_class, dict):
            parent_defaults = parent_defaults_for_class
    for field_name, field_type in fields.items():
        parent_default_value = parent_defaults.get(field_name)
        init_expr = ""
        if parent_default_value is None:
            init_expr = _rs_zero_value_for_context(ctx, field_type)
        else:
            init_expr = parent_default_value
        _emit(ctx, "let mut " + _rs_constructor_field_name(field_name) + " = " + init_expr + ";")
    for arg in box_any_param_names:
        _emit(ctx, "let mut " + safe_rs_ident(arg) + " = " + safe_rs_ident(arg) + ".into_py_box_any();")

    filtered_body: list[dict[str, JsonVal]] = []
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if _str(stmt, "kind") == "Expr":
            val = stmt.get("value")
            if isinstance(val, dict) and _str(val, "kind") == "Call":
                func = val.get("func")
                if isinstance(func, dict) and _str(func, "kind") == "Attribute":
                    fn_attr = _str(func, "attr")
                    fn_obj = func.get("value")
                    if fn_attr == "__init__" and isinstance(fn_obj, dict) and _str(fn_obj, "kind") == "Call":
                        fn_obj_func = fn_obj.get("func")
                        if isinstance(fn_obj_func, dict) and _str(fn_obj_func, "id") in ("super", "py_super"):
                            call_args = _list(val, "args")
                            if "msg" in fields and len(call_args) >= 1:
                                first_arg = call_args[0]
                                if isinstance(first_arg, dict):
                                    first_arg_name = _str(first_arg, "id")
                                    first_arg_rt = _str(first_arg, "resolved_type")
                                    if first_arg_name == "msg" or first_arg_rt == "str":
                                        _emit(ctx, _rs_constructor_field_name("msg") + " = " + _emit_expr(ctx, first_arg) + ";")
                            continue
        filtered_body.append(stmt)

    _emit(ctx, "'" + ctx.constructor_block_label + ": {")
    ctx.indent_level += 1
    _emit_body(ctx, filtered_body)
    ctx.indent_level -= 1
    _emit(ctx, "}")

    # Emit struct literal
    _emit(ctx, rs_name + " {")
    ctx.indent_level += 1
    for field_name, field_type in fields.items():
        rs_field = safe_rs_ident(field_name)
        _emit(ctx, rs_field + ": " + _rs_constructor_field_name(field_name) + ",")
    ctx.indent_level -= 1
    _emit(ctx, "}")

    ctx.declared_vars = prev_declared
    ctx.constructor_field_locals = prev_constructor_locals
    ctx.constructor_block_label = prev_constructor_label
    ctx.at_module_level = prev_at_module_level
    ctx.current_class = prev_current_class
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _camel_to_screaming_snake(name: str) -> str:
    """Convert CamelCase to SCREAMING_SNAKE_CASE: MathUtil → MATH_UTIL."""
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)
    s = re.sub(r'(?<=[A-Z])([A-Z][a-z])', r'_\1', s)
    return s.upper()


def _class_tid_const_name(ctx: RsEmitContext, class_name: str) -> str:
    """Build the TID const name matching _fqcn_to_tid_const: {MODULE_UPPER}_{CLASS_SNAKE_UPPER}_TID."""
    # Use module_id (dotted path) to match the FQCN used in the manifest type_id_table
    if ctx.module_id != "":
        fqcn = ctx.module_id + "." + class_name
    else:
        import os
        source_path = ctx.source_path
        stem = os.path.splitext(os.path.basename(source_path))[0] if source_path != "" else "module"
        fqcn = stem + "." + class_name
    flat = fqcn.replace(".", "_")
    return safe_rs_ident(_camel_to_screaming_snake(flat) + "_TID")


def _lookup_class_dense_tid(ctx: RsEmitContext, type_name: str) -> int | None:
    """Look up the dense TID for a user-defined class from class_type_ids.

    Returns None if the type is not a known user class.
    """
    if type_name == "" or type_name in ("object", "Any", "Obj", "unknown"):
        return None
    # Try FQCN lookup
    if ctx.module_id != "":
        fqcn = ctx.module_id + "." + type_name
        if fqcn in ctx.class_type_ids:
            return ctx.class_type_ids[fqcn]
    # Try direct match
    if type_name in ctx.class_type_ids:
        return ctx.class_type_ids[type_name]
    # Try suffix match
    suffix = "." + type_name
    for fqcn, tid in ctx.class_type_ids.items():
        if fqcn.endswith(suffix) and not fqcn.startswith("pytra."):
            return tid
    return None


def _class_type_id_expr(ctx: RsEmitContext, type_name: str) -> str:
    dense_tid = _lookup_class_dense_tid(ctx, type_name)
    if dense_tid is not None:
        return str(dense_tid) + "_i64"
    return "8_i64"


def _builtin_type_id_expr(type_name: str) -> str:
    builtin: dict[str, str] = {
        "None": "0_i64",
        "bool": "1_i64",
        "int": "2_i64",
        "int64": "2_i64",
        "float": "3_i64",
        "float64": "3_i64",
        "str": "4_i64",
        "list": "5_i64",
        "dict": "6_i64",
        "set": "7_i64",
        "object": "8_i64",
        "Any": "8_i64",
        "Obj": "8_i64",
        "unknown": "8_i64",
    }
    return builtin.get(type_name, "8_i64")


def _sorted_user_classes_desc(ctx: RsEmitContext) -> list[tuple[str, int]]:
    """Return user-defined class (fqcn, dense_tid) pairs sorted by dense_tid descending.

    Most-specific (leaf) classes have higher dense TIDs, so they come first.
    This is used to generate correct downcast chains (children before parents).
    """
    result: list[tuple[str, int]] = []
    for fqcn, dense_tid in ctx.class_type_ids.items():
        if dense_tid < 1000:
            continue
        if not ctx.package_mode and fqcn.startswith("pytra.built_in.error."):
            continue
        result.append((fqcn, dense_tid))
    result.sort(key=lambda kv: kv[1], reverse=True)
    return result


def _emit_obj_type_id_downcast(ctx: RsEmitContext, ref_expr: str, user_cls: list[tuple[str, int]]) -> str:
    """Emit a downcast chain to determine the sequential TID of a Box<dyn Any> value.

    The Box<dyn Any> typically contains a Box<ClassName> (due to double-boxing at call sites),
    so we try downcast_ref::<Box<ClassName>> first, then bare ClassName as fallback.
    Falls back to builtin type tagging for primitive/object values.
    """
    if ctx.package_mode:
        return "py_builtin_type_id_any(" + ref_expr + ")"
    parts: list[str] = []
    for fqcn, _dense in user_cls:
        dot_at = fqcn.rfind(".")
        if dot_at >= 0:
            simple_name = fqcn[dot_at + 1:]
            owner_module = fqcn[:dot_at]
        else:
            simple_name = fqcn
            owner_module = ""
        rs_name = safe_rs_ident(simple_name)
        if ctx.package_mode and owner_module != "" and owner_module != ctx.module_id:
            rs_name = "crate::" + _module_id_to_rs_mod_name(owner_module) + "::" + rs_name
        seq_const = str(ctx.class_type_ids.get(fqcn, 8)) + "_i64"
        # Try Box<ClassName> first (double-boxed case: Box<Box<ClassName>> as Box<dyn Any>)
        parts.append(
            "if (" + ref_expr + ").downcast_ref::<Box<" + rs_name + ">>().is_some() || "
            + "(" + ref_expr + ").downcast_ref::<" + rs_name + ">().is_some() "
            + "{ " + seq_const + " }"
        )
    fallback = "py_builtin_type_id_any(" + ref_expr + ")"
    if not parts:
        return fallback
    chain = " else ".join(parts) + " else { " + fallback + " }"
    return "{ " + chain + " }"


def _emit_parent_class_methods_trait(ctx: RsEmitContext, class_name: str) -> None:
    """Emit a `<ClassName>Methods` trait for a parent class, including all its public methods."""
    rs_name = safe_rs_ident(class_name)
    methods = ctx.class_instance_methods.get(class_name, {})
    trait_methods: list[str] = []
    for mname, mnode in methods.items():
        if mname.startswith("__"):
            continue
        raw_arg_order = _list(mnode, "arg_order")
        arg_order: list[str] = []
        for raw_arg in raw_arg_order:
            if isinstance(raw_arg, str):
                arg_order.append(raw_arg)
        arg_types = _dict(mnode, "arg_types")
        return_type = _str(mnode, "return_type")
        params: list[str] = []
        for arg in arg_order:
            if arg == "self":
                trait_mutates = bool(mnode.get("mutates_self", True)) if isinstance(mnode, dict) else True
                params.append("&mut self" if trait_mutates else "&self")
                continue
            arg_type = _str(arg_types, arg)
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
            params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
        params_str = ", ".join(params)
        if return_type == "" or return_type in ("None", "none"):
            ret_str = ""
        else:
            rt = _rs_type_for_context(ctx, return_type)
            ret_str = " -> " + rt if rt != "()" else ""
        trait_methods.append("    fn " + safe_rs_ident(mname) + "(" + params_str + ")" + ret_str + ";")
    if not trait_methods:
        return
    _emit_blank(ctx)
    _emit(ctx, "pub trait " + rs_name + "Methods {")
    for tm in trait_methods:
        ctx.lines.append(tm)
    _emit(ctx, "}")


def _emit_parent_class_methods_impl(ctx: RsEmitContext, class_name: str, as_type: str = "") -> None:
    """Emit `impl <ParentName>Methods for <ClassName>` delegating to existing methods."""
    impl_class = safe_rs_ident(class_name)
    trait_class = safe_rs_ident(as_type if as_type != "" else class_name)
    methods = ctx.class_instance_methods.get(as_type if as_type != "" else class_name, {})
    trait_methods: list[tuple[str, str, str, str]] = []
    for mname, mnode in methods.items():
        if mname.startswith("__"):
            continue
        raw_arg_order = _list(mnode, "arg_order")
        arg_order: list[str] = []
        for raw_arg in raw_arg_order:
            if isinstance(raw_arg, str):
                arg_order.append(raw_arg)
        arg_types = _dict(mnode, "arg_types")
        return_type = _str(mnode, "return_type")
        trait_method_node = methods.get(mname)
        self_mutates = bool(trait_method_node.get("mutates_self", True)) if isinstance(trait_method_node, dict) else True
        params: list[str] = []
        call_args: list[str] = []
        for arg in arg_order:
            if arg == "self":
                params.append("&mut self" if self_mutates else "&self")
                continue
            arg_type = _str(arg_types, arg)
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
            params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
            call_args.append(safe_rs_ident(arg))
        params_str = ", ".join(params)
        call_str = impl_class + "::" + safe_rs_ident(mname) + "(self, " + ", ".join(call_args) + ")"
        if return_type == "" or return_type in ("None", "none"):
            ret_str = ""
            body = call_str + ";"
        else:
            rt = _rs_type_for_context(ctx, return_type)
            ret_str = " -> " + rt if rt != "()" else ""
            body = "return " + call_str + ";"
        trait_methods.append((params_str, ret_str, mname, body))
    if not trait_methods:
        return
    _emit_blank(ctx)
    _emit(ctx, "impl " + trait_class + "Methods for " + impl_class + " {")
    ctx.indent_level += 1
    for (params_str, ret_str, mname, body) in trait_methods:
        _emit(ctx, "fn " + safe_rs_ident(mname) + "(" + params_str + ")" + ret_str + " {")
        ctx.indent_level += 1
        _emit(ctx, body)
        ctx.indent_level -= 1
        _emit(ctx, "}")
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_trait_definition(ctx: RsEmitContext, name: str, body: list[JsonVal]) -> None:
    """Emit a @trait decorated class as a Rust trait."""
    rs_name = safe_rs_ident(name)
    _emit_blank(ctx)
    _emit(ctx, "pub trait " + rs_name + " {")
    ctx.indent_level += 1
    prev_class = ctx.current_class
    ctx.current_class = name
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        stmt_kind = _str(stmt, "kind")
        if stmt_kind in ("FunctionDef", "ClosureDef"):
            fn_name = _str(stmt, "name")
            if fn_name == "__init__":
                continue
            raw_arg_order = _list(stmt, "arg_order")
            arg_order: list[str] = []
            for raw_arg in raw_arg_order:
                if isinstance(raw_arg, str):
                    arg_order.append(raw_arg)
            arg_types = _dict(stmt, "arg_types")
            return_type = _str(stmt, "return_type")
            stmt_mutates = bool(stmt.get("mutates_self", True))
            params: list[str] = []
            for arg in arg_order:
                if arg == "self":
                    params.append("&mut self" if stmt_mutates else "&self")
                    continue
                arg_type = _str(arg_types, arg)
                if arg_type in ctx.trait_names:
                    rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
                else:
                    rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
                params.append(safe_rs_ident(arg) + ": " + rs_arg_type)
            params_str = ", ".join(params)
            type_params = _collect_signature_type_params(ctx, arg_types, return_type)
            generic_suffix = "<" + ", ".join(type_params) + ">" if type_params else ""
            if return_type in ("", "None", "none"):
                ret_str = ""
            else:
                rt = _rs_type_for_context(ctx, return_type)
                ret_str = "" if rt == "()" else " -> " + rt
            _emit(ctx, "fn " + safe_rs_ident(fn_name) + generic_suffix + "(" + params_str + ")" + ret_str + ";")
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.current_class = prev_class


def _emit_trait_methods_impl(ctx: RsEmitContext, class_name: str, trait_name: str) -> None:
    """Emit trait impl for a class using its own methods that match the trait."""
    rs_class = safe_rs_ident(class_name)
    rs_trait = safe_rs_ident(trait_name)
    trait_methods = ctx.class_instance_methods.get(trait_name, {})
    class_methods = ctx.class_instance_methods.get(class_name, {})
    _emit_blank(ctx)
    _emit(ctx, "impl " + rs_trait + " for " + rs_class + " {")
    ctx.indent_level += 1
    prev_class = ctx.current_class
    ctx.current_class = class_name
    for mname, trait_method_node in trait_methods.items():
        if mname == "__init__":
            continue
        method_node = class_methods.get(mname)
        if method_node is not None:
            # Use trait method's mutates_self to determine &self vs &mut self in the impl
            # so it matches the trait definition signature
            trait_mutates = bool(trait_method_node.get("mutates_self", True)) if isinstance(trait_method_node, dict) else True
            self_ref = "&mut self" if trait_mutates else "&self"
            # Emit method signature and body with correct self ref
            _emit_blank(ctx)
            _emit_trait_impl_method(ctx, method_node, class_name, self_ref)
    ctx.indent_level -= 1
    _emit(ctx, "}")
    ctx.current_class = prev_class


def _emit_trait_impl_method(ctx: RsEmitContext, node: dict[str, JsonVal], owner: str, self_ref: str) -> None:
    """Emit a method for a trait impl block, using self_ref (&self or &mut self)."""
    name = _str(node, "name")
    raw_arg_order = _list(node, "arg_order")
    arg_order: list[str] = []
    for raw_arg in raw_arg_order:
        if isinstance(raw_arg, str):
            arg_order.append(raw_arg)
    arg_types = _dict(node, "arg_types")
    arg_defaults = _dict(node, "arg_defaults")
    return_type = _str(node, "return_type")
    body = _list(node, "body")

    params: list[str] = []
    for arg in arg_order:
        if arg == "self":
            params.append(self_ref)
            continue
        arg_type = _str(arg_types, arg)
        if arg_type in ctx.trait_names:
            rs_arg_type = "&dyn " + safe_rs_ident(arg_type)
        else:
            rs_arg_type = _rs_type_for_context(ctx, arg_type) if arg_type != "" else "Box<dyn std::any::Any>"
        params.append(safe_rs_ident(arg) + ": " + rs_arg_type)

    params_str = ", ".join(params)
    type_params = _collect_signature_type_params(ctx, arg_types, return_type)
    generic_suffix = "<" + ", ".join(type_params) + ">" if type_params else ""
    if return_type in ("", "None", "none"):
        ret_str = ""
    else:
        rt = _rs_type_for_context(ctx, return_type)
        ret_str = "" if rt == "()" else " -> " + rt

    fn_name = safe_rs_ident(name)
    _emit(ctx, "fn " + fn_name + generic_suffix + "(" + params_str + ")" + ret_str + " {")
    ctx.indent_level += 1

    prev_return_type = ctx.current_return_type
    prev_declared = set(ctx.declared_vars)
    prev_var_types = dict(ctx.var_types)
    ctx.current_return_type = return_type
    ctx.declared_vars = set()
    for arg in arg_order:
        if arg != "self":
            ctx.declared_vars.add(arg)
            arg_type = _str(arg_types, arg)
            if arg_type != "":
                ctx.var_types[arg] = arg_type

    _emit_body(ctx, body)
    ctx.current_return_type = prev_return_type
    ctx.declared_vars = prev_declared
    ctx.var_types = prev_var_types

    ctx.indent_level -= 1
    _emit(ctx, "}")


def _emit_trait_impl(ctx: RsEmitContext, class_name: str, trait_name: str) -> None:
    _emit_blank(ctx)
    _emit(ctx, "impl " + safe_rs_ident(trait_name) + " for " + safe_rs_ident(class_name) + " {")
    ctx.indent_level += 1
    # Trait methods would go here (from the class)
    ctx.indent_level -= 1
    _emit(ctx, "}")


def _constant_default_sig(value: JsonVal, resolved_type: str) -> dict[str, JsonVal]:
    node: dict[str, JsonVal] = {}
    node["kind"] = "Constant"
    node["value"] = value
    node["resolved_type"] = resolved_type
    return node


def _list_default_sig(resolved_type: str) -> dict[str, JsonVal]:
    node: dict[str, JsonVal] = {}
    node["kind"] = "List"
    elements: list[JsonVal] = []
    node["elements"] = elements
    node["resolved_type"] = resolved_type
    return node


def _argparse_add_argument_sig() -> dict[str, JsonVal]:
    sig: dict[str, JsonVal] = {}
    arg_order: list[JsonVal] = []
    arg_order.append("self")
    arg_order.append("name0")
    arg_order.append("name1")
    arg_order.append("name2")
    arg_order.append("name3")
    arg_order.append("help")
    arg_order.append("action")
    arg_order.append("choices")
    arg_order.append("default")
    sig["arg_order"] = arg_order
    arg_types: dict[str, JsonVal] = {}
    arg_types["name0"] = "str"
    arg_types["name1"] = "str"
    arg_types["name2"] = "str"
    arg_types["name3"] = "str"
    arg_types["help"] = "str"
    arg_types["action"] = "str"
    arg_types["choices"] = "list[str]"
    arg_types["default"] = "object"
    sig["arg_types"] = arg_types
    arg_defaults: dict[str, JsonVal] = {}
    arg_defaults["name1"] = _constant_default_sig("", "str")
    arg_defaults["name2"] = _constant_default_sig("", "str")
    arg_defaults["name3"] = _constant_default_sig("", "str")
    arg_defaults["help"] = _constant_default_sig("", "str")
    arg_defaults["action"] = _constant_default_sig("", "str")
    arg_defaults["choices"] = _list_default_sig("list[str]")
    arg_defaults["default"] = _constant_default_sig(None, "None")
    sig["arg_defaults"] = arg_defaults
    return sig


def _argparse_parse_args_sig() -> dict[str, JsonVal]:
    sig: dict[str, JsonVal] = {}
    arg_order: list[JsonVal] = []
    arg_order.append("self")
    arg_order.append("argv")
    sig["arg_order"] = arg_order
    arg_types: dict[str, JsonVal] = {}
    arg_types["argv"] = "list[str] | None"
    sig["arg_types"] = arg_types
    arg_defaults: dict[str, JsonVal] = {}
    arg_defaults["argv"] = _constant_default_sig(None, "None")
    sig["arg_defaults"] = arg_defaults
    return sig


# ---------------------------------------------------------------------------
# First pass: collect signatures
# ---------------------------------------------------------------------------

def _first_pass(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    """Collect class and function info before emission."""
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind == "ClassDef":
            name = _str(stmt, "name")
            ctx.class_names.add(name)
            _collect_class_info(ctx, stmt)
        elif kind in ("FunctionDef", "ClosureDef"):
            name = _str(stmt, "name")
            ctx.function_signatures[name] = stmt
            # Track original_name → name remapping (compiler-renamed functions)
            original_name = _str(stmt, "original_name")
            if original_name != "" and original_name != name:
                ctx.original_name_map[original_name] = name
            _mark_ref_classes_from_function(ctx, stmt)


# ---------------------------------------------------------------------------
# Module-level emission
# ---------------------------------------------------------------------------

def _emit_module_body(ctx: RsEmitContext, body: list[JsonVal]) -> None:
    ctx.at_module_level = True
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("Import", "ImportFrom"):
            continue  # handled separately
        _emit_stmt(ctx, stmt)
    ctx.at_module_level = False


def _collect_uses(ctx: RsEmitContext, meta: dict[str, JsonVal]) -> list[str]:
    """Determine which `use` statements are needed."""
    if not ctx.package_mode:
        empty_lines: list[str] = []
        return empty_lines
    lines: list[str] = _package_prelude_uses(ctx.needs_runtime_type_ids)
    if ctx.module_id == "pytra.built_in.error":
        filtered_lines: list[str] = []
        for line in lines:
            if line != "use crate::pytra_built_in_error::RuntimeError;":
                filtered_lines.append(line)
        lines = filtered_lines
    if ctx.module_id == "pytra.std.re":
        filtered_lines2: list[str] = []
        for line in lines:
            if line != "use crate::pytra_std_re::*;":
                filtered_lines2.append(line)
        lines = filtered_lines2
    seen: set[str] = set(lines)
    bindings = meta.get("import_bindings")
    if not isinstance(bindings, list):
        return lines
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        module_id = _as_str(binding.get("runtime_module_id"))
        if module_id == "":
            module_id = _as_str(binding.get("module_id"))
        if module_id == "":
            continue
        binding_kind = _as_str(binding.get("binding_kind"))
        local_name = _as_str(binding.get("local_name"))
        export_name = _as_str(binding.get("export_name"))
        symbol_name = export_name if export_name != "" else local_name
        symbol_name = _normalize_binding_name(symbol_name) if symbol_name != "" else ""
        nested_module_id = module_id + "." + symbol_name if symbol_name not in ("", "_") else ""
        module_is_crate = _is_package_crate_module(ctx, module_id)
        nested_is_crate = nested_module_id != "" and _is_package_crate_module(ctx, nested_module_id)
        if not module_is_crate and not nested_is_crate:
            continue
        if module_id in ("pytra.typing", "pytra.types", "abc") and not nested_is_crate:
            continue
        if module_is_crate:
            wildcard_line = "pub use crate::" + _module_id_to_rs_mod_name(module_id) + "::*;"
            if wildcard_line not in seen:
                seen.add(wildcard_line)
                lines.append(wildcard_line)
        if binding_kind == "module" and local_name != "":
            line = "pub use crate::" + _module_id_to_rs_mod_name(module_id) + " as " + safe_rs_ident(local_name) + ";"
        elif binding_kind == "symbol" and local_name != "":
            local_name = _normalize_binding_name(local_name)
            if symbol_name == "" or symbol_name == "_" or local_name == "" or local_name == "_":
                continue
            local_rs: str = safe_rs_ident(local_name)
            module_parts = module_id.split(".")
            module_leaf = module_parts[-1] if len(module_parts) > 0 else module_id
            if module_is_crate and symbol_name == module_leaf:
                source_rs = _module_id_to_rs_mod_name(module_id)
                line = "pub use crate::" + source_rs
                if local_rs != source_rs:
                    line += " as " + local_rs
                line += ";"
                if line not in seen:
                    seen.add(line)
                    lines.append(line)
                continue
            if nested_is_crate or (_has_nested_python_module(module_id, symbol_name) and _is_transpiled_module(ctx, nested_module_id)):
                source_rs = _module_id_to_rs_mod_name(nested_module_id)
                line = "pub use crate::" + source_rs
                if local_rs != source_rs:
                    line += " as " + local_rs
                line += ";"
                if line not in seen:
                    seen.add(line)
                    lines.append(line)
                continue
            source_rs = safe_rs_ident(symbol_name)
            if symbol_name.startswith("_"):
                mod_prefix = _module_id_to_rs_mod_name(module_id)
                if mod_prefix != "":
                    source_rs = mod_prefix + "__" + symbol_name[1:]
            line = "pub use crate::" + _module_id_to_rs_mod_name(module_id) + "::" + source_rs
            if local_rs != source_rs:
                line += " as " + local_rs
            line += ";"
        else:
            continue
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


_PACKAGE_FACTORY_DEF_RE = re.compile(r"^(pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\(\)\s*->\s*(.+?)\s*\{\s*(.+)\s*\}$")


def _rewrite_package_module_factories(lines: list[str]) -> list[str]:
    factory_defs: dict[str, tuple[str, str, str]] = {}
    captured: dict[str, list[str]] = {}
    skipped: set[int] = set()
    for line in lines:
        match = _PACKAGE_FACTORY_DEF_RE.match(line.strip())
        if match is None:
            continue
        factory_name = match.group(2)
        factory_defs[factory_name] = ((match.group(1) or ""), match.group(3).strip(), match.group(4).strip())
        captured.setdefault(factory_name, [])
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        for factory_name in factory_defs:
            prefix = factory_name + "()"
            if not line.startswith(prefix):
                continue
            captured[factory_name].append("__module_value" + line[len(prefix):].rstrip())
            skipped.add(idx)
            break
    out: list[str] = []
    for idx, line in enumerate(lines):
        if idx in skipped:
            continue
        match = _PACKAGE_FACTORY_DEF_RE.match(line.strip())
        if match is None:
            out.append(line)
            continue
        factory_name = match.group(2)
        body_lines = captured.get(factory_name, [])
        if not body_lines:
            out.append(line)
            continue
        vis, ret_type, init_expr = factory_defs[factory_name]
        out.append(vis + "fn " + factory_name + "() -> " + ret_type + " {")
        out.append("    let mut __module_value = " + init_expr + ";")
        for body_line in body_lines:
            out.append("    " + body_line)
        out.append("    __module_value")
        out.append("}")
    return out


def emit_rs_module(east3_doc: dict[str, JsonVal], *, package_mode: bool = False) -> str:
    """Emit a complete Rust source file from an EAST3 document.

    Args:
        east3_doc: linked EAST3 JSON dict with meta.linked_program_v1.

    Returns:
        Rust source code string, or empty string if the module should be skipped.
    """
    meta = _dict(east3_doc, "meta")
    module_id = ""

    emit_ctx_meta = _dict(meta, "emit_context")
    if emit_ctx_meta:
        module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")

    lp = _dict(meta, "linked_program_v1")
    if module_id == "" and len(lp) > 0:
        module_id = _str(lp, "module_id")

    if module_id != "":
        modules_for_defaults: list[JsonVal] = []
        modules_for_defaults.append(east3_doc)
        expand_cross_module_defaults(modules_for_defaults)

    # Load runtime mapping
    mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "rs" / "mapping.json"
    mapping = load_runtime_mapping(mapping_path)
    set_mapping_types(mapping.types)

    # Skip runtime modules
    if should_skip_module(module_id, mapping):
        return ""

    ctx = RsEmitContext()
    ctx.module_id = module_id
    ctx.source_path = _str(east3_doc, "source_path")
    if len(emit_ctx_meta) > 0:
        ctx.is_entry = _bool(emit_ctx_meta, "is_entry")
    else:
        ctx.is_entry = False
    ctx.package_mode = package_mode
    ctx.mapping = mapping

    body = _list(east3_doc, "body")
    main_guard = _list(east3_doc, "main_guard_body")

    # Collect runtime imports
    ctx.runtime_imports = build_runtime_import_map(meta, mapping)
    ctx.imported_symbol_storage_hints = _build_import_symbol_storage_hints(meta)
    ctx.imported_class_fields = _build_import_class_fields(meta)
    ctx.imported_symbol_names = _build_imported_symbol_names(meta)
    ctx.imported_symbol_modules = _build_imported_symbol_modules(meta)
    ctx.type_only_imported_symbols = _build_type_only_imported_symbols(meta, body, main_guard)
    ctx.known_method_signatures = {
        "ArgumentParser.add_argument": _argparse_add_argument_sig(),
        "ArgumentParser.parse_args": _argparse_parse_args_sig(),
    }

    # Collect module private symbols
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        kind = _str(stmt, "kind")
        if kind in ("FunctionDef", "ClassDef"):
            name = _str(stmt, "name")
            if name.startswith("_"):
                ctx.module_private_symbols.add(name)
        elif kind in ("AnnAssign", "Assign"):
            target = stmt.get("target")
            if isinstance(target, dict):
                name2 = _str(target, "id")
                if name2.startswith("_"):
                    ctx.module_private_symbols.add(name2)

    # First pass: collect class/function info
    _first_pass(ctx, body)

    # Compute parent class names (classes that are bases of other classes)
    ctx.parent_class_names = {
        base for base in ctx.class_bases.values()
        if base in ctx.class_names and base not in ctx.trait_names and base not in ctx.enum_bases
    }

    # Load type_id_resolved_v1 (FQCN → dense TID) and type_info_table_v1
    type_id_resolved = _dict(lp, "type_id_resolved_v1")
    for fqcn, dense_val in type_id_resolved.items():
        if isinstance(fqcn, str) and isinstance(dense_val, int):
            ctx.class_type_ids[fqcn] = dense_val
    type_info_raw = _dict(lp, "type_info_table_v1")
    for ti_name, ti_val in type_info_raw.items():
        if isinstance(ti_name, str) and isinstance(ti_val, dict):
            entry = ti_val.get("entry")
            exit_val = ti_val.get("exit")
            tid_id = ti_val.get("id")
            if isinstance(entry, int) and isinstance(exit_val, int) and isinstance(tid_id, int):
                ctx.class_type_info_table[ti_name] = {"id": tid_id, "entry": entry, "exit": exit_val}

    # Collect import alias modules
    ctx.import_alias_modules = build_import_alias_map(meta)
    ctx.needs_runtime_type_ids = _doc_requires_runtime_type_ids(body, main_guard, ctx.class_names)

    # Start emitting
    lines: list[str] = ctx.lines

    # Emit use statements
    for use_stmt in _collect_uses(ctx, meta):
        lines.append(use_stmt)

    # Include runtime header
    if ctx.is_entry and not ctx.package_mode:
        lines.append("include!(\"py_runtime.rs\");")
        for dep_mod_id in _iter_linked_module_ids_transitive(meta, ctx.module_id):
            inc = "include!(\"" + dep_mod_id.replace(".", "_") + ".rs\");"
            if inc not in lines:
                lines.append(inc)
        has_type_id_include = False
        for line in lines:
            if line == 'include!("toolchain_link_type_id.rs");':
                has_type_id_include = True
                break
        if has_type_id_include:
            lines.append("fn resolve_runtime_module_rel_tail(module_id: String) -> String {")
            lines.append("    if module_id == \"pytra.core.py_runtime\".to_string() { return \"core/py_runtime\".to_string(); }")
            lines.append("    if py_str_startswith(&module_id, &\"pytra.built_in.\".to_string()) { return format!(\"{}{}\", \"built_in/\".to_string(), py_str_replace(&py_slice(&module_id, Some(15_i64), None), &\".\".to_string(), &\"/\".to_string())); }")
            lines.append("    if py_str_startswith(&module_id, &\"pytra.std.\".to_string()) { return format!(\"{}{}\", \"std/\".to_string(), py_str_replace(&py_slice(&module_id, Some(10_i64), None), &\".\".to_string(), &\"/\".to_string())); }")
            lines.append("    if py_str_startswith(&module_id, &\"pytra.utils.\".to_string()) { return format!(\"{}{}\", \"utils/\".to_string(), py_str_replace(&py_slice(&module_id, Some(12_i64), None), &\".\".to_string(), &\"/\".to_string())); }")
            lines.append("    return \"\".to_string();")
            lines.append("}")
            lines.append("fn is_runtime_namespace_module(module_id: String) -> bool { [\"pytra.built_in\".to_string(), \"pytra.std\".to_string(), \"pytra.utils\".to_string(), \"pytra.core\".to_string()].contains(&module_id) }")
            lines.append("fn is_type_only_dependency_module_id(_module_id: String) -> bool { false }")
            lines.append("fn is_runtime_internal_helper_module(module_id: String) -> bool { py_str_startswith(&module_id, &\"pytra.core.\".to_string()) && resolve_runtime_module_rel_tail(module_id.clone()) == \"\".to_string() }")
            lines.append("fn collect_import_modules(_east_doc: HashMap<String, PyAny>) -> HashMap<String, String> { HashMap::new() }")
            lines.append("fn collect_import_symbols(_east_doc: HashMap<String, PyAny>) -> HashMap<String, String> { HashMap::new() }")
        for resolved_kind, mod_id in _iter_import_runtime_ids(meta, ctx.type_only_imported_symbols):
            if mod_id == "" or mod_id == ctx.module_id:
                continue
            canonical_mod_id = mod_id
            if not _is_pytra_module(canonical_mod_id):
                std_candidate = _PYTRA_ROOT + "." + _STD_SEG + "." + canonical_mod_id
                if (
                    std_candidate in ctx.mapping.module_native_files
                    or should_skip_module(std_candidate, ctx.mapping)
                    or _has_python_module_file(std_candidate)
                ):
                    canonical_mod_id = std_candidate
            rs_file = ""
            if should_skip_module(canonical_mod_id, ctx.mapping):
                rs_file = ctx.mapping.module_native_files.get(canonical_mod_id, "")
                if rs_file == "":
                    for prefix, native_file in ctx.mapping.module_native_files.items():
                        if canonical_mod_id.startswith(prefix):
                            rs_file = native_file
                            break
            elif _is_pytra_module(canonical_mod_id) or resolved_kind == "module" or _is_pytra_utils_module(canonical_mod_id):
                assertions_mod_id = _PYTRA_ROOT + "." + _UTILS_SEG + ".assertions"
                typing_mod_id = _PYTRA_ROOT + ".typing"
                if canonical_mod_id == assertions_mod_id or canonical_mod_id == typing_mod_id:
                    rs_file = ""
                else:
                    rs_file = canonical_mod_id.replace(".", "_") + ".rs"
            if rs_file != "":
                inc = "include!(\"" + rs_file + "\");"
                if inc not in lines:
                    lines.append(inc)
    lines.append("")

    # Emit body
    _emit_module_body(ctx, body)

    # Emit main_guard as fn main()
    if ctx.is_entry:
        _emit_blank(ctx)
        main_prefix = "pub " if ctx.package_mode else ""
        _emit(ctx, main_prefix + "fn main() {")
        ctx.indent_level += 1
        if len(main_guard) > 0:
            prev_declared = set(ctx.declared_vars)
            ctx.declared_vars = {"argv"}
            _emit_body(ctx, main_guard)
            ctx.declared_vars = prev_declared
        ctx.indent_level -= 1
        _emit(ctx, "}")

    if ctx.package_mode:
        lines = _rewrite_package_module_factories(lines)
    rendered = "\n".join(lines).rstrip() + "\n"
    if module_id == "pytra.std.pathlib":
        rendered = rendered.replace(
            "value.borrow()._value.clone()",
            "value.downcast_ref::<Rc<RefCell<Path>>>().unwrap().borrow()._value.clone()",
        )
        rendered = rendered.replace(
            "rhs.borrow()._value.clone()",
            "rhs.downcast_ref::<Rc<RefCell<Path>>>().unwrap().borrow()._value.clone()",
        )
        rendered = rendered.replace(
            "other.borrow()._value.clone()",
            "other.downcast_ref::<Rc<RefCell<Path>>>().unwrap().borrow()._value.clone()",
        )
        rendered = rendered.replace(
            "py_mkdir(self._value.clone().clone());",
            "py_mkdir(self._value.clone().clone(), false);",
        )
    rendered = rendered.replace(
        "_is_name: Box<dyn Fn(PyAny, String) -> bool>",
        "_is_name: &dyn Fn(PyAny, String) -> bool",
    )
    rendered = rendered.replace(
        "].contains(&(category))",
        "].contains(&(category.clone().unwrap_or_default()))",
    )
    rendered = rendered.replace(
        "py_any_as_list(body.clone()).iter_snapshot()",
        "body.clone().iter_snapshot()",
    )
    rendered = rendered.replace(
        "PyList::<PyAny>::new() })",
        "PyList::<(String, String, bool)>::new() })",
    )
    rendered = rendered.replace(
        "return std::io::Error::new(std::io::ErrorKind::Other, format!(\"{}{}\", \"input_invalid: \".to_string(), message).clone());",
        "return Box::new(std::io::Error::new(std::io::ErrorKind::Other, format!(\"{}{}\", \"input_invalid: \".to_string(), message).clone()));",
    )
    rendered = rendered.replace(
        "return (py_int(&(indent.clone())) as i64).clone().expect(\"unbox\");",
        "return indent.clone().expect(\"unbox\");",
    )
    rendered = rendered.replace(
        "run_emit_cli(None, cli_argv.clone(), \"\".to_string().clone(), None, toolchain_emit_cpp_cli__emit_cpp_direct)",
        "run_emit_cli(None, cli_argv.clone(), \"\".to_string().clone(), None, Some(Box::new(toolchain_emit_cpp_cli__emit_cpp_direct)))",
    )
    rendered = rendered.replace(
        "run_emit_cli(None, cli_argv.clone(), \"\".to_string().clone(), None, toolchain_emit_cpp_cli__emit_cpp_direct.clone())",
        "run_emit_cli(None, cli_argv.clone(), \"\".to_string().clone(), None, Some(Box::new(toolchain_emit_cpp_cli__emit_cpp_direct)))",
    )
    rendered = rendered.replace("symbol_name, format!(\"{}{}\", mapping.borrow().builtin_prefix.clone(), symbol_name)", "symbol_name.clone(), format!(\"{}{}\", mapping.borrow().builtin_prefix.clone(), symbol_name)")
    rendered = rendered.replace("merged.insert(key, toolchain_emit_common_profile_loader__merge_profile_values(merged[&key].clone().clone(), value.clone()))", "merged.insert(key.clone(), toolchain_emit_common_profile_loader__merge_profile_values(merged[&key].clone().clone(), value.clone()))")
    rendered = rendered.replace("toolchain_emit_common_profile_loader__module_init__PROFILE_DOC_CACHE()[&language];", "toolchain_emit_common_profile_loader__module_init__PROFILE_DOC_CACHE()[&language].clone();")
    rendered = rendered.replace(
        "return self._format_condition(self.render_expr(node_value.clone()).clone());",
        "let __arg = self.render_expr(node_value.clone()).clone();\n        return self._format_condition(__arg);",
    )
    rendered = rendered.replace(
        "self.emit_backend_line(self.render_exception_dispatch_open(caught_type_expr.clone()).clone());",
        "let __line = self.render_exception_dispatch_open(caught_type_expr.clone()).clone();\n        self.emit_backend_line(__line);",
    )
    rendered = rendered.replace(
        "self.emit_backend_line(self.render_exception_handler_guard_open(typed_handler.clone(), handled_name.clone(), caught_type_expr.clone()).clone());",
        "let __line = self.render_exception_handler_guard_open(typed_handler.clone(), handled_name.clone(), caught_type_expr.clone()).clone();\n            self.emit_backend_line(__line);",
    )
    rendered = rendered.replace(
        "self.emit_with_enter_action(enter_target_name.clone(), enter_target_type.clone(), self.with_item_enter_runtime_call(item.clone()).clone(), self.with_item_enter_runtime_symbol(item.clone()).clone(), enter_target_type.clone());",
        "let __enter_call = self.with_item_enter_runtime_call(item.clone()).clone();\n        let __enter_symbol = self.with_item_enter_runtime_symbol(item.clone()).clone();\n        self.emit_with_enter_action(enter_target_name.clone(), enter_target_type.clone(), __enter_call, __enter_symbol, enter_target_type.clone());",
    )
    rendered = rendered.replace(
        "self.emit_with_enter_fallback_action(ctx_name.clone(), source_type.clone(), self.with_source_uses_enter_fallback(source_rendered_type.clone()));",
        "let __uses_fallback = self.with_source_uses_enter_fallback(source_rendered_type.clone());\n        self.emit_with_enter_fallback_action(ctx_name.clone(), source_type.clone(), __uses_fallback);",
    )
    rendered = rendered.replace(
        "return self.build_with_entry(ctx_name.clone(), bound_target_name.clone(), source_rendered_type.clone(), enter_target_type.clone(), self.with_item_exit_runtime_call(item.clone()).clone(), self.with_item_exit_runtime_symbol(item.clone()).clone());",
        "let __exit_call = self.with_item_exit_runtime_call(item.clone()).clone();\n        let __exit_symbol = self.with_item_exit_runtime_symbol(item.clone()).clone();\n        return self.build_with_entry(ctx_name.clone(), bound_target_name.clone(), source_rendered_type.clone(), enter_target_type.clone(), __exit_call, __exit_symbol);",
    )
    rendered = rendered.replace(
        "self._emit(self._syntax_text(\"try\".to_string().clone(), \"try {\".to_string().clone()).clone());",
        "let __line = self._syntax_text(\"try\".to_string().clone(), \"try {\".to_string().clone()).clone();\n        self._emit(__line);",
    )
    rendered = rendered.replace(
        "self._emit(self._syntax_text(\"block_close\".to_string().clone(), \"}\".to_string().clone()).clone());",
        "let __line = self._syntax_text(\"block_close\".to_string().clone(), \"}\".to_string().clone()).clone();\n        self._emit(__line);",
    )
    rendered = rendered.replace(
        "self._emit(py_str_replace(&self._syntax_text(syntax_key.clone(), default_open.clone()), &\"{cond}\".to_string().clone(), &test.clone()).clone());",
        "let __tmpl = self._syntax_text(syntax_key.clone(), default_open.clone());\n        self._emit(py_str_replace(&__tmpl, &\"{cond}\".to_string().clone(), &test.clone()).clone());",
    )
    rendered = rendered.replace(
        "self._emit(py_str_replace(&self._syntax_text(\"while\".to_string().clone(), \"while ({cond}) {\".to_string().clone()), &\"{cond}\".to_string().clone(), &test.clone()).clone());",
        "let __tmpl = self._syntax_text(\"while\".to_string().clone(), \"while ({cond}) {\".to_string().clone());\n            self._emit(py_str_replace(&__tmpl, &\"{cond}\".to_string().clone(), &test.clone()).clone());",
    )
    rendered = rendered.replace(
        "self._emit(self._syntax_text(\"else\".to_string().clone(), \"} else {\".to_string().clone()).clone());",
        "let __line = self._syntax_text(\"else\".to_string().clone(), \"} else {\".to_string().clone()).clone();\n            self._emit(__line);",
    )
    rendered = rendered.replace(
        "let add_name = |name: String, resolved_type: String, out: PyList<(String, String)>, seen: HashSet<String>| {",
        "let add_name = |name: String, resolved_type: String, mut out: PyList<(String, String)>, mut seen: HashSet<String>| {",
    )
    rendered = rendered.replace(", out, seen);", ", out.clone(), seen.clone());")
    rendered = rendered.replace("let mut a0: PyAny;", "let mut a0: PyAny = PyAny::None;")
    rendered = rendered.replace("let mut a0_obj: Option<Rc<RefCell<JsonObj>>>;", "let mut a0_obj: Option<Rc<RefCell<JsonObj>>> = None;")
    rendered = rendered.replace(
        "{ let mut __list = ctx.borrow().visible_local_scopes.clone().py_borrow_mut(); let __raw = (py_len(&ctx.borrow().visible_local_scopes.clone().clone()) as i64 - 1_i64); let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; __list[__idx].insert(name); };",
        "{ let __tmp_list = ctx.borrow().visible_local_scopes.clone(); let __raw = (py_len(&__tmp_list.clone()) as i64 - 1_i64); let mut __list = __tmp_list.py_borrow_mut(); let __idx = if __raw < 0 { (__list.len() as i64 + __raw) as usize } else { __raw as usize }; __list[__idx].insert(name.clone()); };",
    )
    rendered = rendered.replace("insert(handler_name, toolchain_emit_cpp_emitter__handler_type_name", "insert(handler_name.clone(), toolchain_emit_cpp_emitter__handler_type_name")
    rendered = rendered.replace("ctx.borrow().class_field_types.clone()[&owner_type];", "ctx.borrow().class_field_types.clone()[&owner_type].clone();")
    rendered = rendered.replace("insert(name, (if (normalized_type != \"\".to_string()) { normalized_type } else { resolved_type }));", "insert(name.clone(), (if (normalized_type != \"\".to_string()) { normalized_type } else { resolved_type.clone() }));")
    rendered = rendered.replace("[\"\".to_string(), target_type].contains", "[\"\".to_string(), target_type.clone()].contains")
    rendered = rendered.replace("node_json = node;", "node_json = node.clone();")
    rendered = rendered.replace("{ optional_inner } else", "{ optional_inner.clone() } else")
    rendered = rendered.replace("{ optional_inner });", "{ optional_inner.clone() });")
    rendered = rendered.replace("if (optional_inner == \"int\".to_string()) { \"int64\".to_string() } else { optional_inner })", "if (optional_inner == \"int\".to_string()) { \"int64\".to_string() } else { optional_inner.clone() })")
    rendered = rendered.replace("{ runtime_symbol } else { fallback_symbol })", "{ runtime_symbol.clone() } else { fallback_symbol.clone() })")
    rendered = rendered.replace("renderer.borrow().normalize_boundary_expr", "renderer.borrow_mut().normalize_boundary_expr")
    rendered = rendered.replace("ctx.borrow().function_defs.clone()[&func_name];", "ctx.borrow().function_defs.clone()[&func_name].clone();")
    rendered = rendered.replace("call_sig = method_sig;", "call_sig = method_sig.clone();")
    rendered = rendered.replace("call_sig = function_sig;", "call_sig = function_sig.clone();")
    rendered = rendered.replace("+ arg_strs);", "+ arg_strs.clone());")
    rendered = rendered.replace("{ source_elem_type } else { target_elem_type })", "{ source_elem_type.clone() } else { target_elem_type.clone() })")
    rendered = rendered.replace("{ source_key_type } else { target_key_type })", "{ source_key_type.clone() } else { target_key_type.clone() })")
    rendered = rendered.replace("source_key_type].contains", "source_key_type.clone()].contains")
    rendered = rendered.replace("let mut union_type = (if toolchain_emit_cpp_emitter__is_top_level_union_type(storage_type.clone()) { storage_type } else { value_type });", "let mut union_type = (if toolchain_emit_cpp_emitter__is_top_level_union_type(storage_type.clone()) { storage_type.clone() } else { value_type.clone() });")
    rendered = rendered.replace("ctx.borrow_mut().current_return_type = return_type;", "ctx.borrow_mut().current_return_type = return_type.clone();")
    rendered = rendered.replace("insert(name, toolchain_emit_cpp_emitter__closure_function_type", "insert(name.clone(), toolchain_emit_cpp_emitter__closure_function_type")
    rendered = rendered.replace("insert(name, enum_kind.clone())", "insert(name.clone(), enum_kind.clone())")
    rendered = rendered.replace("insert(name, property_methods.clone())", "insert(name.clone(), property_methods.clone())")
    rendered = rendered.replace("ctx.borrow().class_vars.clone()[&name];", "ctx.borrow().class_vars.clone()[&name].clone();")
    rendered = rendered.replace("{ base } else", "{ base.clone() } else")
    rendered = rendered.replace("renderer.borrow().emit_try_stmt", "renderer.borrow_mut().emit_try_stmt")
    rendered = rendered.replace("ctx.borrow_mut().mapping = mapping;", "ctx.borrow_mut().mapping = mapping.clone();")
    rendered = rendered.replace("ctx.borrow_mut().module_id = module_id;", "ctx.borrow_mut().module_id = module_id.clone();")
    rendered = rendered.replace("insert(class_name, base_name.clone())", "insert(class_name.clone(), base_name.clone())")
    rendered = rendered.replace("insert(class_name, field_types.clone())", "insert(class_name.clone(), field_types.clone())")
    rendered = rendered.replace("insert(class_name, empty_class_vars.clone())", "insert(class_name.clone(), empty_class_vars.clone())")
    rendered = rendered.replace("ctx.borrow().class_vars.clone()[&class_name];", "ctx.borrow().class_vars.clone()[&class_name].clone();")
    rendered = rendered.replace("ctx.borrow_mut().current_class = owner_name;", "ctx.borrow_mut().current_class = owner_name.clone();")
    rendered = rendered.replace("callee_mutable = mutable_indexes[&callee_name];", "callee_mutable = mutable_indexes[&callee_name].clone();")
    rendered = rendered.replace("_walk(child.clone(), arg_name, mutable_indexes)", "_walk(child.clone(), arg_name.clone(), mutable_indexes.clone())")
    rendered = rendered.replace("_walk(item.clone(), arg_name, mutable_indexes)", "_walk(item.clone(), arg_name.clone(), mutable_indexes.clone())")
    rendered = rendered.replace("_walk(child.clone(), &_is_name, arg_name, mutating_runtime_calls)", "_walk(child.clone(), &_is_name, arg_name.clone(), mutating_runtime_calls.clone())")
    rendered = rendered.replace("_walk(item.clone(), &_is_name, arg_name, mutating_runtime_calls)", "_walk(item.clone(), &_is_name, arg_name.clone(), mutating_runtime_calls.clone())")
    rendered = rendered.replace("parent.clone(), node, param_name)", "parent.clone(), node.clone(), param_name.clone())")
    rendered = rendered.replace("grandparent.clone(), node, param_name)", "grandparent.clone(), node.clone(), param_name.clone())")
    rendered = rendered.replace("PyAny::None, node, param_name)", "PyAny::None, node.clone(), param_name.clone())")
    rendered = rendered.replace("type_id_table.insert(fqcn, entry);", "type_id_table.insert(fqcn.clone(), entry);")
    rendered = rendered.replace("type_info_table.insert(fqcn, type_info.clone());", "type_info_table.insert(fqcn.clone(), type_info.clone());")
    rendered = rendered.replace("child_fqcns = children[&fqcn];", "child_fqcns = children[&fqcn].clone();")
    rendered = rendered.replace("builtin_children = toolchain_link_type_id__module_init__BUILTIN_CLASS_CHILDREN()[&name];", "builtin_children = toolchain_link_type_id__module_init__BUILTIN_CLASS_CHILDREN()[&name].clone();")
    rendered = rendered.replace("child_fqcns = children[&name];", "child_fqcns = children[&name].clone();")
    rendered = rendered.replace("module_class_defs.insert(current_module_id, class_defs.clone());", "module_class_defs.insert(current_module_id.clone(), class_defs.clone());")
    rendered = rendered.replace("module_local_classes.insert(current_module_id, local_classes.clone());", "module_local_classes.insert(current_module_id.clone(), local_classes.clone());")
    rendered = rendered.replace("class_bases.insert(fqcn, base_fqcn.clone());", "class_bases.insert(fqcn.clone(), base_fqcn.clone());")
    rendered = rendered.replace("children.insert(fqcn, empty_children.clone());", "children.insert(fqcn.clone(), empty_children.clone());")
    rendered = rendered.replace("[value_type, static_value_type].contains", "[value_type.clone(), static_value_type.clone()].contains")
    rendered = rendered.replace("} else { variant_type });", "} else { variant_type.clone() });")
    rendered = rendered.replace("_walk(child.clone(), arg_name, mutable_param_indexes)", "_walk(child.clone(), arg_name.clone(), mutable_param_indexes.clone())")
    rendered = rendered.replace("_walk(item.clone(), arg_name, mutable_param_indexes)", "_walk(item.clone(), arg_name.clone(), mutable_param_indexes.clone())")
    rendered = rendered.replace("fn _visit(visit_fqcn: String, stack: PyList<String>, class_bases: HashMap<String, String>, visit_state: HashMap<String, i64>) {", "fn _visit(visit_fqcn: String, stack: PyList<String>, class_bases: HashMap<String, String>, mut visit_state: HashMap<String, i64>) {")
    rendered = rendered.replace("visit_state.insert(visit_fqcn, 1_i64);", "visit_state.insert(visit_fqcn.clone(), 1_i64);")
    rendered = rendered.replace("_visit(base_fqcn.clone(), next_stack.clone(), class_bases, visit_state);", "_visit(base_fqcn.clone(), next_stack.clone(), class_bases.clone(), visit_state.clone());")
    rendered = rendered.replace("_visit(root_fqcn.clone(), empty_stack.clone(), class_bases, visit_state);", "_visit(root_fqcn.clone(), empty_stack.clone(), class_bases.clone(), visit_state.clone());")
    rendered = rendered.replace("children.insert(base_fqcn, empty_base_children.clone());", "children.insert(base_fqcn.clone(), empty_base_children.clone());")
    rendered = rendered.replace("children.insert(parent, toolchain_link_type_id__type_id_sorted_strings(children[&parent].clone()));", "children.insert(parent.clone(), toolchain_link_type_id__type_id_sorted_strings(children[&parent].clone()));")
    rendered = rendered.replace("type_id_table.insert(builtin_name, toolchain_link_type_id__module_init__BUILTIN_CLASS_IDS()[&builtin_name]);", "type_id_table.insert(builtin_name.clone(), toolchain_link_type_id__module_init__BUILTIN_CLASS_IDS()[&builtin_name]);")
    rendered = rendered.replace("synthetic_children = children[&synthetic_root];", "synthetic_children = children[&synthetic_root].clone();")
    rendered = rendered.replace('type_info_table[&"object".to_string()].insert("exit".to_string(), next_id_holder.get(0_i64));', 'if let Some(val) = type_info_table.get_mut(&"object".to_string()) { val.insert("exit".to_string(), next_id_holder.get(0_i64)); };')
    rendered = rendered.replace("let mut children_list = toolchain_link_type_id__module_init__BUILTIN_CLASS_CHILDREN()[&candidate];", "let mut children_list = toolchain_link_type_id__module_init__BUILTIN_CLASS_CHILDREN()[&candidate].clone();")
    rendered = rendered.replace("tid_table.insert(type_id_fqcn, PyAny::Int(type_id_table[&type_id_fqcn]));", "tid_table.insert(type_id_fqcn.clone(), PyAny::Int(type_id_table[&type_id_fqcn]));")
    rendered = rendered.replace("tid_base.insert(type_id_base_fqcn, PyAny::Int(type_id_base_map[&type_id_base_fqcn]));", "tid_base.insert(type_id_base_fqcn.clone(), PyAny::Int(type_id_base_map[&type_id_base_fqcn]));")
    rendered = rendered.replace("let mut info_row = type_info_table[&type_info_fqcn];", "let mut info_row = type_info_table[&type_info_fqcn].clone();")
    rendered = rendered.replace(
        "let mut active_direct_emit_fn = Box::new(direct_emit_fn.as_ref().expect(\"callable guard\"));\n        for east_doc in modules.iter_snapshot().into_iter() {\n            written = todo!(\"Box<dyn Any> arithmetic: Add\");\n        }",
        "let active_direct_emit_fn = direct_emit_fn.as_ref().expect(\"callable guard\");\n        for east_doc in modules.iter_snapshot().into_iter() {\n            written = written + active_direct_emit_fn(east_doc.clone(), output_dir.clone());\n        }",
    )
    rendered = rendered.replace(
        "ctx.borrow_mut().class_symbol_fqcns = toolchain_emit_cpp_emitter__build_class_symbol_fqcn_map(meta.clone(), module_id.clone(), ctx.borrow().class_names.clone().clone(), ctx.borrow().class_type_ids.clone().clone());",
        "let __class_names = ctx.borrow().class_names.clone().clone();\n    let __class_type_ids = ctx.borrow().class_type_ids.clone().clone();\n    ctx.borrow_mut().class_symbol_fqcns = toolchain_emit_cpp_emitter__build_class_symbol_fqcn_map(meta.clone(), module_id.clone(), __class_names, __class_type_ids);",
    )
    rendered = rendered.replace(
        "for line in ctx.borrow().lines.clone().iter_snapshot().into_iter() {\n        if py_in(&line, &\"::std::function<\".to_string()) {",
        "let __lines_snapshot = ctx.borrow().lines.clone().iter_snapshot();\n    for line in __lines_snapshot.into_iter() {\n        if py_in(&line, &\"::std::function<\".to_string()) {",
    )
    rendered = rendered.replace(
        "for line in ctx.borrow().lines.clone().iter_snapshot().into_iter() {\n        for needle in string_ops_needles.iter_snapshot().into_iter() {",
        "let __lines_snapshot = ctx.borrow().lines.clone().iter_snapshot();\n    for line in __lines_snapshot.into_iter() {\n        for needle in string_ops_needles.iter_snapshot().into_iter() {",
    )
    rendered = rendered.replace("ctx.borrow().includes_needed.clone().insert(", "ctx.borrow_mut().includes_needed.insert(")
    return rendered

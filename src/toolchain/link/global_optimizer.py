"""Linked-program global optimizer/materializer."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from toolchain.compile.east3_opt_passes.cpp_list_value_local_hint_pass import CppListValueLocalHintPass
from toolchain.compile.east3_opt_passes.non_escape_call_graph import collect_non_escape_import_maps
from toolchain.compile.east3_opt_passes.non_escape_call_graph import collect_non_escape_symbols
from toolchain.compile.east3_opt_passes.non_escape_interprocedural_pass import NonEscapeInterproceduralPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import parse_east3_opt_pass_overrides
from toolchain.compile.east3_optimizer import resolve_east3_opt_level
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_abi import validate_runtime_abi_target_support
from toolchain.frontends.runtime_template import validate_template_module
from toolchain.link.program_call_graph import build_linked_program_call_graph
from toolchain.link.program_model import LINK_OUTPUT_SCHEMA
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule
from toolchain.link.program_validator import validate_link_output_doc
from toolchain.link.program_validator import validate_raw_east3_doc
from toolchain.link.module_export_resolver import resolve_module_attribute_types
from toolchain.link.runtime_template_specializer import materialize_runtime_template_specializations


_LINKED_META_KEY = "linked_program_v1"
_CPP_VALUE_LIST_LOCAL_HINT_KEY = "cpp_value_list_locals_v1"
_BUILTIN_TYPE_IDS: dict[str, int] = {
    "None": 0,
    "bool": 1,
    "int": 2,
    "float": 3,
    "str": 4,
    "list": 5,
    "dict": 6,
    "set": 7,
    "object": 8,
}
_ROOT_BASE_NAMES: set[str] = set(_BUILTIN_TYPE_IDS) | {
    "Enum",
    "IntEnum",
    "IntFlag",
    "BaseException",
    "Exception",
    "RuntimeError",
    "ValueError",
    "TypeError",
    "IndexError",
    "KeyError",
    "TypedDict",
}
_USER_TYPE_ID_BASE = 1000


@dataclass(frozen=True)
class LinkedProgramOptimizationResult:
    linked_program: LinkedProgram
    link_output_doc: dict[str, object]


@dataclass(frozen=True)
class _GlobalPassConfig:
    opt_level: int
    enabled: set[str]
    disabled: set[str]


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        text = s.strip()
        if text != "":
            return text
    return ""


def _ensure_meta(node: dict[str, Any]) -> dict[str, Any]:
    meta_any = node.get("meta")
    if isinstance(meta_any, dict):
        return meta_any
    meta: dict[str, Any] = {}
    node["meta"] = meta
    return meta


def _resolve_global_pass_config(program: LinkedProgram) -> _GlobalPassConfig:
    options = program.options if isinstance(program.options, dict) else {}
    raw_opt_level = options.get("east3_opt_level", 1)
    raw_pass_spec = options.get("east3_opt_pass", "")
    try:
        opt_level = resolve_east3_opt_level(raw_opt_level)
    except Exception as exc:
        raise RuntimeError("invalid linked program east3_opt_level: " + str(raw_opt_level)) from exc
    pass_spec = raw_pass_spec if isinstance(raw_pass_spec, str) else ""
    try:
        enabled, disabled = parse_east3_opt_pass_overrides(pass_spec)
    except Exception as exc:
        raise RuntimeError("invalid linked program east3_opt_pass: " + pass_spec) from exc
    return _GlobalPassConfig(opt_level=opt_level, enabled=enabled, disabled=disabled)


def _is_global_pass_enabled(config: _GlobalPassConfig, pass_name: str, *, min_opt_level: int = 1) -> bool:
    if pass_name in config.disabled:
        return False
    if pass_name in config.enabled:
        return True
    return config.opt_level >= min_opt_level


def _clone_module_doc(module: LinkedProgramModule) -> dict[str, Any]:
    doc_any = deepcopy(module.east_doc)
    doc = doc_any if isinstance(doc_any, dict) else {}
    meta = _ensure_meta(doc)
    meta["module_id"] = module.module_id
    meta.pop(_LINKED_META_KEY, None)
    meta.pop("non_escape_import_closure", None)
    doc["meta"] = meta
    doc["source_path"] = ""
    return doc


def _build_non_escape_closure_docs(program: LinkedProgram) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for module in program.modules:
        out[module.module_id] = _clone_module_doc(module)
    return out


def _run_program_non_escape(program: LinkedProgram) -> tuple[tuple[LinkedProgramModule, ...], dict[str, object]]:
    closure_docs = _build_non_escape_closure_docs(program)
    pass_obj = NonEscapeInterproceduralPass()
    context = PassContext(opt_level=1, target_lang=program.target)
    linked_modules: list[LinkedProgramModule] = []
    global_summary: dict[str, object] = {}

    for module in program.modules:
        root_doc_any = deepcopy(closure_docs[module.module_id])
        root_doc = root_doc_any if isinstance(root_doc_any, dict) else {}
        root_meta = _ensure_meta(root_doc)
        # closure payload は pass 内で read-only のため参照渡し（O(N²) deepcopy 回避）
        closure_payload: dict[str, dict[str, Any]] = {}
        for other_module_id, other_doc in closure_docs.items():
            if other_module_id == module.module_id:
                continue
            closure_payload[other_module_id] = other_doc
        root_meta["non_escape_import_closure"] = closure_payload
        root_doc["meta"] = root_meta
        _ = pass_obj.run(root_doc, context)

        linked_meta = _ensure_meta(root_doc)
        linked_meta.pop("non_escape_import_closure", None)
        module_summary_any = linked_meta.get("non_escape_summary")
        module_summary = module_summary_any if isinstance(module_summary_any, dict) else {}
        for symbol in sorted(module_summary.keys()):
            global_summary[symbol] = module_summary[symbol]

        linked_modules.append(
            LinkedProgramModule(
                module_id=module.module_id,
                source_path=module.source_path,
                is_entry=module.is_entry,
                east_doc=root_doc,
                artifact_path=module.artifact_path,
                module_kind=module.module_kind,
                helper_id=module.helper_id,
                owner_module_id=module.owner_module_id,
                generated_by=module.generated_by,
            )
        )

    return tuple(linked_modules), global_summary


def _extract_cpp_container_hints(module_doc: dict[str, Any]) -> dict[str, object]:
    _module_id, symbols, _local_map = collect_non_escape_symbols(module_doc)
    out: dict[str, object] = {}
    for symbol, fn_node in sorted(symbols.items()):
        meta_any = fn_node.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        hint_any = meta.get(_CPP_VALUE_LIST_LOCAL_HINT_KEY)
        hint = hint_any if isinstance(hint_any, dict) else {}
        locals_any = hint.get("locals")
        locals_list = locals_any if isinstance(locals_any, list) else []
        locals_out: list[str] = []
        for item in locals_list:
            name = _safe_name(item)
            if name != "":
                locals_out.append(name)
        if len(locals_out) == 0:
            continue
        out[symbol] = {"version": "1", "locals": sorted(locals_out)}
    return out


def _materialize_container_hints(
    linked_modules: tuple[LinkedProgramModule, ...],
    *,
    target: str,
) -> tuple[tuple[LinkedProgramModule, ...], dict[str, object]]:
    if target != "cpp":
        return linked_modules, {}

    hint_pass = CppListValueLocalHintPass()
    context = PassContext(opt_level=1, target_lang=target)
    updated_modules: list[LinkedProgramModule] = []
    global_hints: dict[str, object] = {}
    cpp_locals: dict[str, object] = {}

    for module in linked_modules:
        doc_any = deepcopy(module.east_doc)
        doc = doc_any if isinstance(doc_any, dict) else {}
        _ = hint_pass.run(doc, context)
        module_hints = _extract_cpp_container_hints(doc)
        for symbol, payload in sorted(module_hints.items()):
            cpp_locals[symbol] = payload
        updated_modules.append(
            LinkedProgramModule(
                module_id=module.module_id,
                source_path=module.source_path,
                is_entry=module.is_entry,
                east_doc=doc,
                artifact_path=module.artifact_path,
                module_kind=module.module_kind,
                helper_id=module.helper_id,
                owner_module_id=module.owner_module_id,
                generated_by=module.generated_by,
            )
        )

    global_hints["cpp_value_list_locals_v1"] = cpp_locals
    return tuple(updated_modules), global_hints


def _collect_runtime_module_ids_from_node(node: object, out: set[str]) -> None:
    """Recursively collect runtime_module_id values from EAST nodes."""
    if isinstance(node, dict):
        nd: dict[str, Any] = node
        mid = nd.get("runtime_module_id")
        if isinstance(mid, str) and mid != "":
            out.add(mid)
        for value in nd.values():
            _collect_runtime_module_ids_from_node(value, out)
    elif isinstance(node, list):
        nl: list[object] = node
        for item in nl:
            _collect_runtime_module_ids_from_node(item, out)


def _build_resolved_dependencies(module: LinkedProgramModule) -> list[str]:
    """Build sorted list of dependency module IDs for a single module.

    Collects both explicit imports (import_bindings / Import / ImportFrom)
    and implicit runtime dependencies (runtime_module_id on EAST nodes).
    """
    deps: set[str] = set()
    doc = module.east_doc if isinstance(module.east_doc, dict) else {}
    meta = doc.get("meta")
    meta_dict = meta if isinstance(meta, dict) else {}

    # 1. Explicit imports from import_bindings.
    bindings = meta_dict.get("import_bindings")
    if isinstance(bindings, list):
        for item in bindings:
            if isinstance(item, dict):
                mod_id = item.get("module_id")
                if isinstance(mod_id, str) and mod_id != "":
                    deps.add(mod_id)
    else:
        # Fallback: scan body for Import / ImportFrom nodes.
        body = doc.get("body")
        if isinstance(body, list):
            for stmt in body:
                if not isinstance(stmt, dict):
                    continue
                kind = stmt.get("kind")
                if kind == "Import":
                    names = stmt.get("names")
                    if isinstance(names, list):
                        for ent in names:
                            if isinstance(ent, dict):
                                name = ent.get("name")
                                if isinstance(name, str) and name != "":
                                    deps.add(name)
                elif kind == "ImportFrom":
                    mod = stmt.get("module")
                    if isinstance(mod, str) and mod != "":
                        deps.add(mod)

    # 2. Implicit runtime dependencies from EAST node annotations.
    body = doc.get("body")
    if isinstance(body, list):
        _collect_runtime_module_ids_from_node(body, deps)
    main_guard = doc.get("main_guard_body")
    if isinstance(main_guard, list):
        _collect_runtime_module_ids_from_node(main_guard, deps)

    return sorted(deps)


def _build_all_resolved_dependencies(program: LinkedProgram) -> dict[str, list[str]]:
    """Build resolved_dependencies_v1 for all modules in the program."""
    out: dict[str, list[str]] = {}
    for module in program.modules:
        out[module.module_id] = _build_resolved_dependencies(module)
    return out


def _iter_module_class_defs(module_doc: dict[str, Any]) -> list[dict[str, Any]]:
    body_any = module_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    out: list[dict[str, Any]] = []
    for item in body:
        if isinstance(item, dict) and item.get("kind") == "ClassDef":
            out.append(item)
    return out


def _resolve_class_base_fqcn(
    base_name: str,
    *,
    module_id: str,
    local_classes: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
) -> str:
    name = _safe_name(base_name)
    if name == "":
        return "object"
    if name in _ROOT_BASE_NAMES:
        return name
    if name in local_classes:
        return local_classes[name]
    imported_symbol = _safe_name(import_symbols.get(name))
    if imported_symbol != "" and "::" in imported_symbol:
        dep_module_id, export_name = imported_symbol.split("::", 1)
        export_name = _safe_name(export_name)
        if dep_module_id != "" and export_name != "":
            return dep_module_id + "." + export_name
    if "." in name:
        owner_name, attr_name = name.split(".", 1)
        imported_module = _safe_name(import_modules.get(owner_name))
        if imported_module != "" and _safe_name(attr_name) != "":
            return imported_module + "." + _safe_name(attr_name)
    fqcn_candidate = module_id + "." + name
    if fqcn_candidate in local_classes.values():
        return fqcn_candidate
    raise RuntimeError("unknown base type: " + module_id + "." + name)


def _build_type_id_table(program: LinkedProgram) -> tuple[dict[str, int], dict[str, int]]:
    """Build type_id table and base_type_id map via DFS.

    Returns (type_id_table, type_id_base_map):
      - type_id_table: FQCN -> linker-assigned type_id
      - type_id_base_map: FQCN -> base type_id (resolved to int)
    """
    class_bases: dict[str, str] = {}
    children: dict[str, list[str]] = {}

    for module in sorted(program.modules, key=lambda item: item.module_id):
        module_doc = module.east_doc
        import_modules, import_symbols = collect_non_escape_import_maps(module_doc)
        local_classes: dict[str, str] = {}
        class_defs = _iter_module_class_defs(module_doc)
        for class_def in class_defs:
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            local_classes[class_name] = fqcn
        for class_def in class_defs:
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            base_fqcn = _resolve_class_base_fqcn(
                _safe_name(class_def.get("base")),
                module_id=module.module_id,
                local_classes=local_classes,
                import_modules=import_modules,
                import_symbols=import_symbols,
            )
            class_bases[fqcn] = base_fqcn
            children.setdefault(fqcn, [])

    for fqcn, base_fqcn in sorted(class_bases.items()):
        if base_fqcn in class_bases:
            children.setdefault(base_fqcn, [])
            children[base_fqcn].append(fqcn)

    for parent, items in list(children.items()):
        children[parent] = sorted(items)

    roots: list[str] = []
    for fqcn, base_fqcn in sorted(class_bases.items()):
        if base_fqcn not in class_bases:
            roots.append(fqcn)

    next_type_id_holder: list[int] = [_USER_TYPE_ID_BASE]
    type_id_table: dict[str, int] = {}
    # TypeInfo interval table: fqcn -> {id, entry, exit}
    type_info_table: dict[str, dict[str, int]] = {}

    def _assign(fqcn: str) -> None:
        entry = next_type_id_holder[0]
        type_id_table[fqcn] = entry
        next_type_id_holder[0] = next_type_id_holder[0] + 1
        for child_fqcn in children.get(fqcn, []):
            _assign(child_fqcn)
        exit_val = next_type_id_holder[0]
        type_info_table[fqcn] = {"id": entry, "entry": entry, "exit": exit_val}

    for fqcn in sorted(roots):
        _assign(fqcn)

    # Build base type_id map: for each user class, resolve its base to a numeric type_id.
    type_id_base_map: dict[str, int] = {}
    for fqcn, base_fqcn in class_bases.items():
        if base_fqcn in type_id_table:
            type_id_base_map[fqcn] = type_id_table[base_fqcn]
        else:
            # Base is a built-in or non-user type; resolve to built-in type_id.
            base_short = base_fqcn.rsplit(".", 1)[-1] if "." in base_fqcn else base_fqcn
            type_id_base_map[fqcn] = _BUILTIN_TYPE_IDS.get(base_short, _BUILTIN_TYPE_IDS["object"])

    return type_id_table, type_id_base_map, type_info_table


def _apply_union_param_ref_promotion(modules: tuple[LinkedProgramModule, ...]) -> None:
    """Promote classes to ref (gc_managed) if they appear in union type parameters.

    A class passed as a union type argument gets boxed into object, which is escape.
    Such classes must be gc_managed (RcObject-based) to be storable in object.
    """
    # Collect all class names that appear in union type parameters.
    classes_in_unions: set[str] = set()
    for module in modules:
        doc = module.east_doc if isinstance(module.east_doc, dict) else {}
        body = doc.get("body")
        if not isinstance(body, list):
            continue
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            kind = stmt.get("kind")
            # Check function-level arg_types
            if kind == "FunctionDef":
                _collect_union_class_names(stmt, classes_in_unions)
            # Check class methods
            elif kind == "ClassDef":
                class_body = stmt.get("body")
                if isinstance(class_body, list):
                    for method in class_body:
                        if isinstance(method, dict) and method.get("kind") == "FunctionDef":
                            _collect_union_class_names(method, classes_in_unions)

    if len(classes_in_unions) == 0:
        return

    # Update class_storage_hint for matched classes.
    for module in modules:
        doc = module.east_doc if isinstance(module.east_doc, dict) else {}
        body = doc.get("body")
        if not isinstance(body, list):
            continue
        for stmt in body:
            if not isinstance(stmt, dict) or stmt.get("kind") != "ClassDef":
                continue
            class_name = _safe_name(stmt.get("name"))
            if class_name in classes_in_unions:
                stmt["class_storage_hint"] = "ref"


def _collect_union_class_names(fn_node: dict[str, object], out: set[str]) -> None:
    """Collect class names that appear in union type parameters of a function."""
    arg_types = fn_node.get("arg_types")
    if not isinstance(arg_types, dict):
        return
    for param_type in arg_types.values():
        if not isinstance(param_type, str) or "|" not in param_type:
            continue
        parts = param_type.split("|")
        for part in parts:
            stripped = part.strip()
            if stripped == "" or stripped in ("str", "int", "int64", "float", "float64", "bool", "None",
                                              "uint8", "int8", "int16", "uint16", "int32", "uint32", "uint64", "float32",
                                              "list", "dict", "set", "object", "any", "unknown"):
                continue
            # Likely a class name
            out.add(stripped)


def _collect_global_vararg_table(modules: tuple[LinkedProgramModule, ...]) -> dict[str, dict[str, Any]]:
    """Build a table of desugared vararg functions across all modules.

    Key = "module_id::fn_name" for top-level functions,
          "module_id::ClassName.method_name" for class methods,
          AND the short method/function name for Attribute-based call matching.
    Value = {"n_fixed": int, "elem_type": str, "list_type": str}.
    """
    out: dict[str, Any] = {}

    def _scan_funcdef(fn: dict[str, Any], *, module_id: str, owner_class: str = "") -> None:
        info_any = fn.get("vararg_desugared_v1")
        if not isinstance(info_any, dict):
            return
        info: dict[str, Any] = info_any
        fn_name_any = fn.get("name")
        fn_name = fn_name_any if isinstance(fn_name_any, str) else ""
        if fn_name.strip() == "":
            return
        entry: dict[str, Any] = {
            "n_fixed": info.get("n_fixed", 0),
            "elem_type": info.get("elem_type", ""),
            "list_type": info.get("list_type", "list[unknown]"),
        }
        qualified = module_id + "::" + fn_name
        if owner_class != "":
            qualified = module_id + "::" + owner_class + "." + fn_name
        out[qualified] = entry
        # Also register by short name for attr-based matching
        if owner_class != "":
            short_key = owner_class + "." + fn_name
        else:
            short_key = fn_name
        if short_key not in out:
            out[short_key] = entry

    for module in modules:
        doc = module.east_doc if isinstance(module.east_doc, dict) else {}
        body_any = doc.get("body")
        if not isinstance(body_any, list):
            continue
        for stmt in body_any:
            if not isinstance(stmt, dict):
                continue
            kind = stmt.get("kind")
            if kind == "FunctionDef":
                _scan_funcdef(stmt, module_id=module.module_id)
            elif kind == "ClassDef":
                class_name_any = stmt.get("name")
                class_name = class_name_any if isinstance(class_name_any, str) else ""
                class_body_any = stmt.get("body")
                if isinstance(class_body_any, list):
                    for method in class_body_any:
                        if isinstance(method, dict) and method.get("kind") == "FunctionDef":
                            _scan_funcdef(method, module_id=module.module_id, owner_class=class_name)

    return out


def _make_global_vararg_list_node(elements: list[Any], list_type: str) -> dict[str, Any]:
    return {
        "kind": "List",
        "resolved_type": list_type,
        "borrow_kind": "value",
        "casts": [],
        "elements": elements,
    }


def _pack_global_vararg_callsite(call: dict[str, Any], vararg_table: dict[str, Any]) -> None:
    """Pack trailing args of a Call node if it targets a desugared vararg function."""
    func_any = call.get("func")
    if not isinstance(func_any, dict):
        return
    func: dict[str, Any] = func_any

    # Determine the lookup key
    lookup_key = ""
    func_kind = func.get("kind")
    if func_kind == "Name":
        id_any = func.get("id")
        lookup_key = id_any if isinstance(id_any, str) else ""
    elif func_kind == "Attribute":
        attr_any = func.get("attr")
        attr = attr_any if isinstance(attr_any, str) else ""
        # Try qualified: resolve via meta non_escape_callsite
        meta_any = call.get("meta")
        if isinstance(meta_any, dict):
            nec_any = meta_any.get("non_escape_callsite")
            if isinstance(nec_any, dict):
                callee_any = nec_any.get("callee")
                callee = callee_any if isinstance(callee_any, str) else ""
                if callee != "" and callee in vararg_table:
                    lookup_key = callee
        if lookup_key == "" and attr != "":
            # Fallback: try ClassName.method_name or just method_name
            owner_type_any = func.get("value")
            if isinstance(owner_type_any, dict):
                owner_type = owner_type_any.get("resolved_type")
                if isinstance(owner_type, str) and owner_type.strip() != "":
                    candidate = owner_type.strip() + "." + attr
                    if candidate in vararg_table:
                        lookup_key = candidate
            if lookup_key == "":
                lookup_key = attr

    if lookup_key == "" or lookup_key not in vararg_table:
        return

    info: dict[str, Any] = vararg_table[lookup_key]
    n_fixed: int = info.get("n_fixed", 0)
    list_type: str = info.get("list_type", "list[unknown]")
    args_any = call.get("args")
    args: list[Any] = args_any if isinstance(args_any, list) else []
    if len(args) < n_fixed:
        return
    if len(args) == n_fixed:
        # Pass empty list for zero varargs
        packed = _make_global_vararg_list_node([], list_type)
        call["args"] = args + [packed]
        return
    # Check if trailing args are already packed (first element is a List with correct type)
    if len(args) == n_fixed + 1:
        last_any = args[n_fixed]
        last_d: dict[str, object] = last_any if isinstance(last_any, dict) else {}
        if isinstance(last_any, dict) and last_d.get("kind") == "List":
            return  # Already packed by per-module pass
    fixed_args = args[:n_fixed]
    vararg_args = args[n_fixed:]
    packed = _make_global_vararg_list_node(vararg_args, list_type)
    call["args"] = fixed_args + [packed]


def _walk_vararg_callsite_packing(node: Any, vararg_table: dict[str, Any]) -> None:
    """Recursively walk the AST and pack vararg call sites in-place."""
    if isinstance(node, dict):
        nd: dict[str, Any] = node
        if nd.get("kind") == "Call":
            _pack_global_vararg_callsite(nd, vararg_table)
        for value in nd.values():
            _walk_vararg_callsite_packing(value, vararg_table)
    elif isinstance(node, list):
        for item in node:
            _walk_vararg_callsite_packing(item, vararg_table)


def _apply_vararg_callsite_packing_global(
    linked_modules: tuple[LinkedProgramModule, ...],
) -> tuple[LinkedProgramModule, ...]:
    """Pack cross-module vararg call sites using desugaring markers from all modules."""
    vararg_table = _collect_global_vararg_table(linked_modules)
    if not vararg_table:
        return linked_modules
    updated: list[LinkedProgramModule] = []
    for module in linked_modules:
        doc_any = deepcopy(module.east_doc)
        doc = doc_any if isinstance(doc_any, dict) else {}
        _walk_vararg_callsite_packing(doc, vararg_table)
        updated.append(
            LinkedProgramModule(
                module_id=module.module_id,
                source_path=module.source_path,
                is_entry=module.is_entry,
                east_doc=doc,
                artifact_path=module.artifact_path,
                module_kind=module.module_kind,
                helper_id=module.helper_id,
                owner_module_id=module.owner_module_id,
                generated_by=module.generated_by,
            )
        )
    return tuple(updated)


def _program_id(program: LinkedProgram) -> str:
    module_ids = [module.module_id for module in sorted(program.modules, key=lambda item: item.module_id)]
    return program.target + ":" + program.dispatch_mode + ":" + ",".join(module_ids)


def _linked_output_path(module_id: str) -> str:
    return "linked/" + module_id.replace(".", "/") + ".east3.json"


def _input_label(module: LinkedProgramModule) -> str:
    if module.artifact_path is not None:
        return str(module.artifact_path)
    if module.source_path != "":
        return module.source_path
    return module.module_id


def optimize_linked_program(program: LinkedProgram) -> LinkedProgramOptimizationResult:
    for module in program.modules:
        doc = module.east_doc if isinstance(module.east_doc, dict) else {}
        validate_raw_east3_doc(
            doc,
            expected_dispatch_mode=program.dispatch_mode,
            module_id=module.module_id,
            require_source_spans=False,
        )
        validate_template_module(doc)
    linked_input_program = program
    template_summary: dict[str, object] = {}
    linked_input_program, template_summary = materialize_runtime_template_specializations(program)
    for module in linked_input_program.modules:
        doc = module.east_doc if isinstance(module.east_doc, dict) else {}
        validate_raw_east3_doc(
            doc,
            expected_dispatch_mode=program.dispatch_mode,
            module_id=module.module_id,
            require_source_spans=False,
        )
        validate_runtime_abi_module(doc)
        validate_template_module(doc)
        validate_runtime_abi_target_support(doc, target=program.target)
    call_graph = build_linked_program_call_graph(linked_input_program)
    pass_config = _resolve_global_pass_config(linked_input_program)
    linked_modules: tuple[LinkedProgramModule, ...] = tuple(linked_input_program.modules)
    non_escape_summary: dict[str, object] = {}
    if _is_global_pass_enabled(pass_config, "NonEscapeInterproceduralPass"):
        linked_modules, non_escape_summary = _run_program_non_escape(linked_input_program)
    container_hints: dict[str, object] = {}
    if _is_global_pass_enabled(pass_config, "CppListValueLocalHintPass"):
        linked_modules, container_hints = _materialize_container_hints(linked_modules, target=program.target)
    # Cross-module vararg call site packing: pack trailing positional args of calls to
    # desugared vararg functions (marked with vararg_desugared_v1) into List nodes.
    linked_modules = _apply_vararg_callsite_packing_global(linked_modules)
    # Classes that appear in union type parameters must be ref (gc_managed)
    # because they get boxed into object. Update class_storage_hint accordingly.
    _apply_union_param_ref_promotion(linked_modules)
    # Resolve module attribute types (e.g. math.pi → float64) from export tables.
    resolve_module_attribute_types(linked_modules)

    type_id_table, type_id_base_map, type_info_table = _build_type_id_table(linked_input_program)
    resolved_deps_by_module = _build_all_resolved_dependencies(linked_input_program)
    program_id = _program_id(linked_input_program)

    module_entries: list[dict[str, object]] = []
    final_modules: list[LinkedProgramModule] = []
    for module in sorted(linked_modules, key=lambda item: item.module_id):
        doc_any = deepcopy(module.east_doc)
        doc = doc_any if isinstance(doc_any, dict) else {}
        meta = _ensure_meta(doc)
        module_hints: dict[str, object] = {}
        cpp_hints_any = container_hints.get("cpp_value_list_locals_v1")
        cpp_hints = cpp_hints_any if isinstance(cpp_hints_any, dict) else {}
        if len(cpp_hints) > 0:
            local_slice: dict[str, object] = {}
            prefix = module.module_id + "::"
            for symbol, payload in sorted(cpp_hints.items()):
                if symbol.startswith(prefix):
                    local_slice[symbol] = payload
            module_hints["cpp_value_list_locals_v1"] = local_slice
        meta[_LINKED_META_KEY] = {
            "program_id": program_id,
            "module_id": module.module_id,
            "entry_modules": list(program.entry_modules),
            "type_id_resolved_v1": dict(type_id_table),
            "type_id_base_map_v1": dict(type_id_base_map),
            "type_info_table_v1": dict(type_info_table),
            "resolved_dependencies_v1": resolved_deps_by_module.get(module.module_id, []),
            "non_escape_summary": dict(non_escape_summary),
            "container_ownership_hints_v1": module_hints,
        }
        doc["meta"] = meta
        final_modules.append(
            LinkedProgramModule(
                module_id=module.module_id,
                source_path=module.source_path,
                is_entry=module.is_entry,
                east_doc=doc,
                artifact_path=module.artifact_path,
                module_kind=module.module_kind,
                helper_id=module.helper_id,
                owner_module_id=module.owner_module_id,
                generated_by=module.generated_by,
            )
        )
        me: dict[str, object] = {
            "module_id": module.module_id,
            "input": _input_label(module),
            "output": _linked_output_path(module.module_id),
            "source_path": module.source_path,
            "is_entry": module.is_entry,
            "module_kind": module.module_kind,
        }
        if module.module_kind == "helper":
            me["helper_id"] = module.helper_id
            me["owner_module_id"] = module.owner_module_id
            me["generated_by"] = module.generated_by
        module_entries.append(me)

    call_graph_dict: dict[str, object] = {}
    for caller, callees in call_graph.graph.items():
        call_graph_dict[caller] = list(callees)
    sccs_list: list[object] = []
    for component in call_graph.sccs:
        sccs_list.append(list(component))
    global_section: dict[str, object] = {
        "type_id_table": dict(type_id_table),
        "type_id_base_map": dict(type_id_base_map),
        "call_graph": call_graph_dict,
        "sccs": sccs_list,
        "non_escape_summary": dict(non_escape_summary),
        "container_ownership_hints_v1": dict(container_hints),
    }
    for ts_key, ts_val in template_summary.items():
        global_section[ts_key] = ts_val
    link_output_doc: dict[str, object] = {
        "schema": LINK_OUTPUT_SCHEMA,
        "target": program.target,
        "dispatch_mode": program.dispatch_mode,
        "entry_modules": list(program.entry_modules),
        "modules": module_entries,
        "global": global_section,
        "diagnostics": {"warnings": [], "errors": []},
    }
    _ = validate_link_output_doc(link_output_doc)

    return LinkedProgramOptimizationResult(
        linked_program=LinkedProgram(
            schema=linked_input_program.schema,
            manifest_path=linked_input_program.manifest_path,
            target=linked_input_program.target,
            dispatch_mode=linked_input_program.dispatch_mode,
            entry_modules=linked_input_program.entry_modules,
            modules=tuple(final_modules),
            options=dict(linked_input_program.options),
        ),
        link_output_doc=link_output_doc,
    )

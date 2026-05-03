"""type_id table builder for linked programs.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/link/global_optimizer.py _build_type_id_table (import はしない)。

割り当て規則 (spec-linker.md §6):
- built-in: 固定値 (NONE=0, OBJECT=8 等)
- user class: USER_BASE (1000) 以上を DFS で割り当て
- 決定性: 同一入力では常に同一 type_id
- 順序: 継承トポロジカル順 → 同順位は FQCN 辞書順
"""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain.compile.jv import jv_str, jv_is_dict, jv_is_list, jv_dict, jv_list

from toolchain.link.import_maps import collect_import_modules
from toolchain.link.import_maps import collect_import_symbols
from toolchain.link.shared_types import LinkedModule


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
    "BaseException": 9,
    "Exception": 10,
    "RuntimeError": 11,
    "ValueError": 12,
    "TypeError": 13,
    "IndexError": 14,
    "KeyError": 15,
}

_BUILTIN_CLASS_IDS: dict[str, int] = {
    "object": 8,
    "BaseException": 9,
    "Exception": 10,
    "RuntimeError": 11,
    "ValueError": 12,
    "TypeError": 13,
    "IndexError": 14,
    "KeyError": 15,
    "None": 0,
    "bool": 1,
    "int": 2,
    "float": 3,
    "str": 4,
    "list": 5,
    "dict": 6,
    "set": 7,
}

_BUILTIN_CLASS_CHILDREN: dict[str, list[str]] = {
    "object": ["BaseException"],
    "BaseException": ["Exception"],
    "Exception": ["IndexError", "KeyError", "RuntimeError", "TypeError", "ValueError"],
    "RuntimeError": [],
    "ValueError": [],
    "TypeError": [],
    "IndexError": [],
    "KeyError": [],
}

_ROOT_BASE_NAMES: set[str] = {
    "None",
    "bool",
    "int",
    "float",
    "str",
    "list",
    "dict",
    "set",
    "object",
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
    "ABC",
    "Protocol",
}

_USER_TYPE_ID_BASE = 1000


def _builtin_class_names_in_id_order() -> list[str]:
    out: list[str] = []
    pending_id = 0
    while pending_id <= 15:
        for builtin_name in _BUILTIN_CLASS_IDS:
            if _BUILTIN_CLASS_IDS[builtin_name] == pending_id:
                out.append(builtin_name)
                break
        pending_id += 1
    return out


def _type_id_sorted_strings(values: list[str]) -> list[str]:
    out: list[str] = []
    used: set[str] = set()
    while len(out) < len(values):
        found = False
        min_value = ""
        for value in values:
            if value in used:
                continue
            if not found or value < min_value:
                min_value = value
                found = True
        if not found:
            break
        used.add(min_value)
        out.append(min_value)
    return out


def _tail_name(name: str) -> str:
    if "." not in name:
        return name
    parts = name.split(".")
    if len(parts) == 0:
        return name
    return parts[len(parts) - 1]


def _assign_type_rows(
    fqcn: str,
    children: dict[str, list[str]],
    next_id_holder: list[int],
    type_id_table: dict[str, int],
    type_info_table: dict[str, dict[str, int]],
) -> None:
    entry = next_id_holder[0]
    type_id_table[fqcn] = entry
    next_id_holder[0] = next_id_holder[0] + 1
    child_fqcns: list[str] = []
    if fqcn in children:
        child_fqcns = children[fqcn]
    for child_fqcn in child_fqcns:
        _assign_type_rows(child_fqcn, children, next_id_holder, type_id_table, type_info_table)
    exit_val = next_id_holder[0]
    type_info: dict[str, int] = {}
    type_info["id"] = entry
    type_info["entry"] = entry
    type_info["exit"] = exit_val
    type_info_table[fqcn] = type_info


def _walk_builtin_type_tree(
    name: str,
    children: dict[str, list[str]],
    next_id_holder: list[int],
    type_id_table: dict[str, int],
    type_info_table: dict[str, dict[str, int]],
) -> None:
    builtin_children: list[str] = []
    if name in _BUILTIN_CLASS_CHILDREN:
        builtin_children = _BUILTIN_CLASS_CHILDREN[name]
    for builtin_child in builtin_children:
        _walk_builtin_type_tree(builtin_child, children, next_id_holder, type_id_table, type_info_table)
    child_fqcns: list[str] = []
    if name in children:
        child_fqcns = children[name]
    for child_fqcn in child_fqcns:
        _assign_type_rows(child_fqcn, children, next_id_holder, type_id_table, type_info_table)
    exit_val = next_id_holder[0]
    next_builtin_id = _BUILTIN_CLASS_IDS[name] + 1
    if len(builtin_children) == 0 and len(child_fqcns) == 0:
        exit_val = next_builtin_id
    elif exit_val < next_builtin_id:
        exit_val = next_builtin_id
    builtin_type_info: dict[str, int] = {}
    builtin_type_info["id"] = _BUILTIN_CLASS_IDS[name]
    builtin_type_info["entry"] = _BUILTIN_CLASS_IDS[name]
    builtin_type_info["exit"] = exit_val
    type_info_table[name] = builtin_type_info


def builtin_exception_type_names() -> set[str]:
    out: set[str] = set()
    pending: list[str] = ["BaseException"]
    seen: set[str] = set()
    while len(pending) > 0:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        out.add(name)
        builtin_children: list[str] = []
        if name in _BUILTIN_CLASS_CHILDREN:
            builtin_children = _BUILTIN_CLASS_CHILDREN[name]
        for child in builtin_children:
            pending.append(child)
    return out


def is_builtin_exception_type_name(type_name: str) -> bool:
    return type_name in builtin_exception_type_names()


def _safe_name(val: JsonVal) -> str:
    text = ("" + jv_str(val)).strip()
    if text != "":
        return text
    return ""


def _iter_class_defs(east_doc: JsonVal) -> list[dict[str, JsonVal]]:
    """Extract top-level ClassDef nodes from module body."""
    out: list[dict[str, JsonVal]] = []
    if not jv_is_dict(east_doc):
        return out
    east_doc_dict: dict[str, JsonVal] = jv_dict(east_doc)
    body_val = east_doc_dict.get("body")
    if not jv_is_list(body_val):
        return out
    for item in jv_list(body_val):
        if jv_is_dict(item):
            item_dict: dict[str, JsonVal] = jv_dict(item)
            if _safe_name(item_dict.get("kind")) == "ClassDef":
                out.append(item_dict)
    return out


def _type_id_decorators(class_def: dict[str, JsonVal]) -> list[str]:
    raw = class_def.get("decorators")
    out: list[str] = []
    if jv_is_list(raw):
        for item in jv_list(raw):
            text = _safe_name(item)
            if text != "":
                out.append(text)
    return out


def _type_id_is_trait_class(class_def: dict[str, JsonVal]) -> bool:
    meta = class_def.get("meta")
    if jv_is_dict(meta):
        meta_dict: dict[str, JsonVal] = jv_dict(meta)
        if jv_is_dict(meta_dict.get("trait_v1")):
            return True
    for decorator in _type_id_decorators(class_def):
        if decorator == "trait":
            return True
    return False


def _type_id_input_invalid(message: str) -> RuntimeError:
    return RuntimeError("input_invalid: " + message)


def _iter_class_base_names(class_def: dict[str, JsonVal]) -> list[str]:
    """Extract declared base names from a ClassDef.

    EAST1 historically used ``base`` while spec-east uses ``bases``.
    The linker accepts both forms, but multiple inheritance is rejected.
    """
    bases: list[str] = []
    bases_raw = class_def.get("bases")
    if jv_is_list(bases_raw):
        for item in jv_list(bases_raw):
            name = _safe_name(item)
            if name != "":
                bases.append(name)
    if len(bases) == 0:
        base_name = _safe_name(class_def.get("base"))
        if base_name != "":
            bases.append(base_name)
    return bases


def _resolve_declared_class_base_fqcn(
    base_name: str,
    *,
    fqcn: str,
    module_id: str,
    all_classes: set[str],
    local_classes: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
) -> str:
    """Resolve a declared base class name to a fully-qualified class name (FQCN)."""
    name = base_name.strip()
    if name == "":
        return "object"
    if name in _ROOT_BASE_NAMES:
        return name
    if name in all_classes:
        return name
    if name in local_classes:
        local_fqcn = local_classes[name]
        if local_fqcn != "":
            return local_fqcn
    # Check import symbols (binding_kind=symbol: "module_id::export_name")
    imported_symbol = import_symbols.get(name, "").strip()
    if imported_symbol != "" and "::" in imported_symbol:
        sep = imported_symbol.find("::")
        dep_module_id = imported_symbol[:sep].strip()
        export_name = imported_symbol[sep + 2:].strip()
        if dep_module_id != "" and export_name != "":
            imported_fqcn = dep_module_id + "." + export_name
            if imported_fqcn in all_classes:
                return imported_fqcn
            return "object"
    # Check dotted name (e.g. module.ClassName)
    if "." in name:
        first_dot = name.find(".")
        last_dot = -1
        i = len(name) - 1
        while i >= 0:
            if name[i] == ".":
                last_dot = i
                break
            i -= 1
        owner_name = name[:first_dot]
        attr_name = name[last_dot + 1:]
        imported_module = import_modules.get(owner_name, "").strip()
        if imported_module != "" and attr_name.strip() != "":
            imported_fqcn = imported_module + "." + attr_name.strip()
            if imported_fqcn in all_classes:
                return imported_fqcn
            return "object"
    # Fallback: assume local
    fqcn_candidate = module_id + "." + name
    if fqcn_candidate in all_classes:
        return fqcn_candidate
    return "object"


def build_type_id_table(
    modules: list[LinkedModule],
) -> tuple[dict[str, JsonVal], dict[str, JsonVal], dict[str, JsonVal]]:
    """Build type_id table, base_map, and info_table via DFS.

    Returns:
        (type_id_table, type_id_base_map, type_info_table)
        - type_id_table: {FQCN: int}
        - type_id_base_map: {FQCN: int}
        - type_info_table: {FQCN: {id, entry, exit}}
    """
    class_bases: dict[str, str] = {}
    children: dict[str, list[str]] = {}
    all_classes: set[str] = set()
    module_local_classes: dict[str, dict[str, str]] = {}
    module_class_defs: dict[str, list[dict[str, JsonVal]]] = {}

    for module in modules:
        current_module_id = module.module_id + ""

        # First pass: collect local class names → FQCN
        local_classes: dict[str, str] = {}
        class_defs = _iter_class_defs(module.east_doc)
        module_class_defs[current_module_id] = class_defs
        for class_def in class_defs:
            if _type_id_is_trait_class(class_def):
                continue
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = current_module_id + "." + class_name
            if fqcn in all_classes:
                empty_a: dict[str, JsonVal] = {}
                empty_b: dict[str, JsonVal] = {}
                empty_c: dict[str, JsonVal] = {}
                return empty_a, empty_b, empty_c
            local_classes[class_name] = fqcn
            all_classes.add(fqcn)
        module_local_classes[current_module_id] = local_classes

    for module in modules:
        current_module_id = module.module_id + ""
        class_defs = module_class_defs.get(current_module_id, [])
        local_classes = module_local_classes.get(current_module_id, {})
        import_modules: dict[str, str] = collect_import_modules(module.east_doc)
        import_symbols: dict[str, str] = collect_import_symbols(module.east_doc)

        for class_def in class_defs:
            if _type_id_is_trait_class(class_def):
                continue
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = current_module_id + "." + class_name
            base_names = _iter_class_base_names(class_def)
            if len(base_names) > 1:
                empty_a: dict[str, JsonVal] = {}
                empty_b: dict[str, JsonVal] = {}
                empty_c: dict[str, JsonVal] = {}
                return empty_a, empty_b, empty_c
            base_fqcn = "object"
            if len(base_names) == 1:
                base_fqcn = _resolve_declared_class_base_fqcn(
                    base_names[0],
                    fqcn=fqcn,
                    module_id=current_module_id,
                    all_classes=all_classes,
                    local_classes=local_classes,
                    import_modules=import_modules,
                    import_symbols=import_symbols,
                )
            class_bases[fqcn] = base_fqcn
            if fqcn not in children:
                empty_children: list[str] = []
                children[fqcn] = empty_children

    visit_state: dict[str, int] = {}

    def _visit(visit_fqcn: str, stack: list[str]) -> None:
        state = visit_state.get(visit_fqcn, 0)
        if state == 2:
            return
        if state == 1:
            cycle_start = 0
            i = 0
            while i < len(stack):
                if stack[i] == visit_fqcn:
                    cycle_start = i
                    break
                i += 1
            cycle: list[str] = []
            cycle_idx = cycle_start
            while cycle_idx < len(stack):
                cycle.append(stack[cycle_idx])
                cycle_idx += 1
            cycle.append(visit_fqcn)
            visit_state[visit_fqcn] = 2
            return

        visit_state[visit_fqcn] = 1
        base_fqcn = class_bases.get(visit_fqcn, "")
        if base_fqcn in class_bases:
            next_stack: list[str] = []
            for stack_item in stack:
                next_stack.append(stack_item)
            next_stack.append(visit_fqcn)
            _visit(base_fqcn, next_stack)
        visit_state[visit_fqcn] = 2

    class_base_names: list[str] = []
    for class_base_fqcn in class_bases:
        class_base_names.append(class_base_fqcn)
    for root_fqcn in _type_id_sorted_strings(class_base_names):
        empty_stack: list[str] = []
        _visit(root_fqcn, empty_stack)

    # Build children map
    sorted_class_names = _type_id_sorted_strings(class_base_names)
    for sorted_fqcn in sorted_class_names:
        base_fqcn = class_bases[sorted_fqcn]
        if base_fqcn not in children:
            empty_base_children: list[str] = []
            children[base_fqcn] = empty_base_children
        children[base_fqcn].append(sorted_fqcn)

    # Sort children for determinism
    child_parents: list[str] = []
    for parent in children:
        child_parents.append(parent)
    for parent in _type_id_sorted_strings(child_parents):
        children[parent] = _type_id_sorted_strings(children[parent])

    # DFS assignment
    next_id_holder: list[int] = [_USER_TYPE_ID_BASE]
    type_id_table: dict[str, int] = {}
    type_info_table: dict[str, dict[str, int]] = {}

    for builtin_name in _builtin_class_names_in_id_order():
        type_id_table[builtin_name] = _BUILTIN_CLASS_IDS[builtin_name]

    _walk_builtin_type_tree("object", children, next_id_holder, type_id_table, type_info_table)

    # Add type_info_table entries for any _BUILTIN_CLASS_IDS entries not processed by
    # _walk_builtin (e.g. None, bool, int, float, str, list, dict, set — standalone leaf types).
    # type_id_table entries were already added above; only type_info is missing.
    for builtin_name in _builtin_class_names_in_id_order():
        if builtin_name not in type_info_table:
            raw_tid = _BUILTIN_CLASS_IDS[builtin_name]
            standalone_type_info: dict[str, int] = {}
            standalone_type_info["id"] = raw_tid
            standalone_type_info["entry"] = raw_tid
            standalone_type_info["exit"] = raw_tid + 1
            type_info_table[builtin_name] = standalone_type_info

    synthetic_roots: list[str] = []
    for synthetic_root in _ROOT_BASE_NAMES:
        synthetic_roots.append(synthetic_root)
    for synthetic_root in _type_id_sorted_strings(synthetic_roots):
        if synthetic_root in _BUILTIN_CLASS_IDS:
            continue
        synthetic_children: list[str] = []
        if synthetic_root in children:
            synthetic_children = children[synthetic_root]
        for child_fqcn in synthetic_children:
            if child_fqcn not in type_info_table:
                _assign_type_rows(child_fqcn, children, next_id_holder, type_id_table, type_info_table)

    for sorted_fqcn in sorted_class_names:
        base_fqcn = class_bases[sorted_fqcn]
        if base_fqcn == "object" and sorted_fqcn not in type_info_table:
            _assign_type_rows(sorted_fqcn, children, next_id_holder, type_id_table, type_info_table)

    if "object" in type_info_table:
        type_info_table["object"]["exit"] = next_id_holder[0]

    if len(type_id_table) != len(class_bases) + len(_BUILTIN_CLASS_IDS):
        empty_a: dict[str, JsonVal] = {}
        empty_b: dict[str, JsonVal] = {}
        empty_c: dict[str, JsonVal] = {}
        return empty_a, empty_b, empty_c

    # Build base type_id map
    type_id_base_map: dict[str, int] = {}
    for builtin_name in _builtin_class_names_in_id_order():
        builtin_id = _BUILTIN_CLASS_IDS[builtin_name]
        builtin_base = ""
        for candidate in _BUILTIN_CLASS_CHILDREN:
            children_list = _BUILTIN_CLASS_CHILDREN[candidate]
            if builtin_name in children_list:
                builtin_base = candidate
                break
        if builtin_base != "":
            type_id_base_map[builtin_name] = _BUILTIN_CLASS_IDS[builtin_base]
        else:
            type_id_base_map[builtin_name] = builtin_id

    for base_map_fqcn in class_bases:
        base_fqcn = class_bases[base_map_fqcn]
        if base_fqcn in type_id_table:
            type_id_base_map[base_map_fqcn] = type_id_table[base_fqcn]
        else:
            base_short = _tail_name(base_fqcn)
            type_id_base_map[base_map_fqcn] = _BUILTIN_TYPE_IDS.get(base_short, _BUILTIN_TYPE_IDS["object"])

    # Convert to JsonVal-compatible dicts
    tid_table: dict[str, JsonVal] = {}
    type_id_names: list[str] = []
    for type_id_fqcn in type_id_table:
        type_id_names.append(type_id_fqcn)
    for type_id_fqcn in _type_id_sorted_strings(type_id_names):
        tid_table[type_id_fqcn] = type_id_table[type_id_fqcn]

    tid_base: dict[str, JsonVal] = {}
    type_id_base_names: list[str] = []
    for type_id_base_fqcn in type_id_base_map:
        type_id_base_names.append(type_id_base_fqcn)
    for type_id_base_fqcn in _type_id_sorted_strings(type_id_base_names):
        tid_base[type_id_base_fqcn] = type_id_base_map[type_id_base_fqcn]

    tid_info: dict[str, JsonVal] = {}
    type_info_names: list[str] = []
    for type_info_fqcn in type_info_table:
        type_info_names.append(type_info_fqcn)
    for type_info_fqcn in _type_id_sorted_strings(type_info_names):
        info_row = type_info_table[type_info_fqcn]
        info: dict[str, JsonVal] = {}
        info["id"] = info_row["id"]
        info["entry"] = info_row["entry"]
        info["exit"] = info_row["exit"]
        tid_info[type_info_fqcn] = info

    return tid_table, tid_base, tid_info

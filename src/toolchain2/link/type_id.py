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

from typing import TYPE_CHECKING

from pytra.std.json import JsonVal

if TYPE_CHECKING:
    from toolchain2.link.linker import LinkedModule

from toolchain2.link.import_maps import collect_import_maps


_BUILTIN_TYPE_IDS: dict[str, int] = {}
_BUILTIN_TYPE_IDS["None"] = 0
_BUILTIN_TYPE_IDS["bool"] = 1
_BUILTIN_TYPE_IDS["int"] = 2
_BUILTIN_TYPE_IDS["float"] = 3
_BUILTIN_TYPE_IDS["str"] = 4
_BUILTIN_TYPE_IDS["list"] = 5
_BUILTIN_TYPE_IDS["dict"] = 6
_BUILTIN_TYPE_IDS["set"] = 7
_BUILTIN_TYPE_IDS["object"] = 8
_BUILTIN_TYPE_IDS["BaseException"] = 9
_BUILTIN_TYPE_IDS["Exception"] = 10
_BUILTIN_TYPE_IDS["RuntimeError"] = 11
_BUILTIN_TYPE_IDS["ValueError"] = 12
_BUILTIN_TYPE_IDS["TypeError"] = 13
_BUILTIN_TYPE_IDS["IndexError"] = 14
_BUILTIN_TYPE_IDS["KeyError"] = 15

_BUILTIN_CLASS_IDS: dict[str, int] = {}
_BUILTIN_CLASS_IDS["object"] = _BUILTIN_TYPE_IDS["object"]
_BUILTIN_CLASS_IDS["BaseException"] = _BUILTIN_TYPE_IDS["BaseException"]
_BUILTIN_CLASS_IDS["Exception"] = _BUILTIN_TYPE_IDS["Exception"]
_BUILTIN_CLASS_IDS["RuntimeError"] = _BUILTIN_TYPE_IDS["RuntimeError"]
_BUILTIN_CLASS_IDS["ValueError"] = _BUILTIN_TYPE_IDS["ValueError"]
_BUILTIN_CLASS_IDS["TypeError"] = _BUILTIN_TYPE_IDS["TypeError"]
_BUILTIN_CLASS_IDS["IndexError"] = _BUILTIN_TYPE_IDS["IndexError"]
_BUILTIN_CLASS_IDS["KeyError"] = _BUILTIN_TYPE_IDS["KeyError"]
_BUILTIN_CLASS_IDS["None"] = _BUILTIN_TYPE_IDS["None"]
_BUILTIN_CLASS_IDS["bool"] = _BUILTIN_TYPE_IDS["bool"]
_BUILTIN_CLASS_IDS["int"] = _BUILTIN_TYPE_IDS["int"]
_BUILTIN_CLASS_IDS["float"] = _BUILTIN_TYPE_IDS["float"]
_BUILTIN_CLASS_IDS["str"] = _BUILTIN_TYPE_IDS["str"]
_BUILTIN_CLASS_IDS["list"] = _BUILTIN_TYPE_IDS["list"]
_BUILTIN_CLASS_IDS["dict"] = _BUILTIN_TYPE_IDS["dict"]
_BUILTIN_CLASS_IDS["set"] = _BUILTIN_TYPE_IDS["set"]

_BUILTIN_CLASS_CHILDREN: dict[str, list[str]] = {}
_BUILTIN_CLASS_CHILDREN["object"] = ["BaseException"]
_BUILTIN_CLASS_CHILDREN["BaseException"] = ["Exception"]
_BUILTIN_CLASS_CHILDREN["Exception"] = ["IndexError", "KeyError", "RuntimeError", "TypeError", "ValueError"]
_BUILTIN_CLASS_CHILDREN["RuntimeError"] = []
_BUILTIN_CLASS_CHILDREN["ValueError"] = []
_BUILTIN_CLASS_CHILDREN["TypeError"] = []
_BUILTIN_CLASS_CHILDREN["IndexError"] = []
_BUILTIN_CLASS_CHILDREN["KeyError"] = []

_ROOT_BASE_NAMES: set[str] = set(_BUILTIN_TYPE_IDS.keys())
_ROOT_BASE_NAMES.add("Enum")
_ROOT_BASE_NAMES.add("IntEnum")
_ROOT_BASE_NAMES.add("IntFlag")
_ROOT_BASE_NAMES.add("BaseException")
_ROOT_BASE_NAMES.add("Exception")
_ROOT_BASE_NAMES.add("RuntimeError")
_ROOT_BASE_NAMES.add("ValueError")
_ROOT_BASE_NAMES.add("TypeError")
_ROOT_BASE_NAMES.add("IndexError")
_ROOT_BASE_NAMES.add("KeyError")
_ROOT_BASE_NAMES.add("TypedDict")
_ROOT_BASE_NAMES.add("ABC")
_ROOT_BASE_NAMES.add("Protocol")

_USER_TYPE_ID_BASE = 1000


def _safe_name(val: JsonVal) -> str:
    if isinstance(val, str):
        text = val.strip()
        if text != "":
            return text
    return ""


def _iter_class_defs(east_doc: dict[str, JsonVal]) -> list[dict[str, JsonVal]]:
    """Extract top-level ClassDef nodes from module body."""
    body_val = east_doc.get("body")
    body = body_val if isinstance(body_val, list) else []
    out: list[dict[str, JsonVal]] = []
    for item in body:
        if isinstance(item, dict) and item.get("kind") == "ClassDef":
            out.append(item)
    return out


def _decorators(class_def: dict[str, JsonVal]) -> list[str]:
    raw = class_def.get("decorators")
    out: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip() != "":
                out.append(item.strip())
    return out


def _is_trait_class(class_def: dict[str, JsonVal]) -> bool:
    meta = class_def.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("trait_v1"), dict):
        return True
    return "trait" in _decorators(class_def)


def _input_invalid(message: str) -> RuntimeError:
    return RuntimeError("input_invalid: " + message)


def _iter_class_base_names(class_def: dict[str, JsonVal]) -> list[str]:
    """Extract declared base names from a ClassDef.

    EAST1 historically used ``base`` while spec-east uses ``bases``.
    The linker accepts both forms, but multiple inheritance is rejected.
    """
    bases: list[str] = []
    bases_raw = class_def.get("bases")
    if isinstance(bases_raw, list):
        for item in bases_raw:
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
        return local_classes[name]
    # Check import symbols (binding_kind=symbol: "module_id::export_name")
    imported_symbol = import_symbols.get(name, "").strip()
    if imported_symbol != "" and "::" in imported_symbol:
        dep_module_id, export_name = imported_symbol.split("::", 1)
        export_name = export_name.strip()
        if dep_module_id.strip() != "" and export_name != "":
            return dep_module_id.strip() + "." + export_name
    # Check dotted name (e.g. module.ClassName)
    if "." in name:
        owner_name, attr_name = name.rsplit(".", 1)
        imported_module = import_modules.get(owner_name, "").strip()
        if imported_module != "" and attr_name.strip() != "":
            return imported_module + "." + attr_name.strip()
    # Fallback: assume local
    fqcn_candidate = module_id + "." + name
    if fqcn_candidate in all_classes:
        return fqcn_candidate
    raise _input_invalid("undefined base class: " + fqcn + " -> " + name)


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
    module_import_maps: dict[str, tuple[dict[str, str], dict[str, str]]] = {}
    module_class_defs: dict[str, list[dict[str, JsonVal]]] = {}

    for module in sorted(modules, key=lambda m: m.module_id):
        doc = module.east_doc
        if not isinstance(doc, dict):
            continue

        import_modules, import_symbols = collect_import_maps(doc)
        module_import_maps[module.module_id] = (import_modules, import_symbols)

        # First pass: collect local class names → FQCN
        local_classes: dict[str, str] = {}
        class_defs = _iter_class_defs(doc)
        module_class_defs[module.module_id] = class_defs
        for class_def in class_defs:
            if _is_trait_class(class_def):
                continue
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            if fqcn in all_classes:
                raise _input_invalid("duplicate class definition: " + fqcn)
            local_classes[class_name] = fqcn
            all_classes.add(fqcn)
        module_local_classes[module.module_id] = local_classes

    for module in sorted(modules, key=lambda m: m.module_id):
        class_defs = module_class_defs.get(module.module_id, [])
        local_classes = module_local_classes.get(module.module_id, {})
        import_modules, import_symbols = module_import_maps.get(module.module_id, ({}, {}))

        for class_def in class_defs:
            if _is_trait_class(class_def):
                continue
            class_name = _safe_name(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            base_names = _iter_class_base_names(class_def)
            if len(base_names) > 1:
                raise _input_invalid(
                    "multiple inheritance is not supported: "
                    + fqcn
                    + " -> "
                    + ", ".join(base_names)
                )
            base_fqcn = "object"
            if len(base_names) == 1:
                base_fqcn = _resolve_declared_class_base_fqcn(
                    base_names[0],
                    fqcn=fqcn,
                    module_id=module.module_id,
                    all_classes=all_classes,
                    local_classes=local_classes,
                    import_modules=import_modules,
                    import_symbols=import_symbols,
                )
            class_bases[fqcn] = base_fqcn
            if fqcn not in children:
                children[fqcn] = []

    visit_state: dict[str, int] = {}

    def _visit(fqcn: str, stack: list[str]) -> None:
        state = visit_state.get(fqcn, 0)
        if state == 2:
            return
        if state == 1:
            cycle_start = 0
            i = 0
            while i < len(stack):
                if stack[i] == fqcn:
                    cycle_start = i
                    break
                i += 1
            cycle = stack[cycle_start:] + [fqcn]
            raise _input_invalid("inheritance cycle: " + " -> ".join(cycle))

        visit_state[fqcn] = 1
        base_fqcn = class_bases.get(fqcn, "")
        if base_fqcn in class_bases:
            _visit(base_fqcn, stack + [fqcn])
        visit_state[fqcn] = 2

    for fqcn in sorted(class_bases.keys()):
        _visit(fqcn, [])

    # Build children map
    for fqcn, base_fqcn in sorted(class_bases.items()):
        if base_fqcn not in children:
            children[base_fqcn] = []
        children[base_fqcn].append(fqcn)

    # Sort children for determinism
    for parent in list(children.keys()):
        children[parent] = sorted(children[parent])

    # DFS assignment
    next_id_holder: list[int] = [_USER_TYPE_ID_BASE]
    type_id_table: dict[str, int] = {}
    type_info_table: dict[str, dict[str, int]] = {}

    def _assign(fqcn: str) -> None:
        entry = next_id_holder[0]
        type_id_table[fqcn] = entry
        next_id_holder[0] = next_id_holder[0] + 1
        for child_fqcn in children.get(fqcn, []):
            _assign(child_fqcn)
        exit_val = next_id_holder[0]
        type_info_table[fqcn] = {"id": entry, "entry": entry, "exit": exit_val}

    for builtin_name, builtin_id in sorted(_BUILTIN_CLASS_IDS.items(), key=lambda item: item[1]):
        type_id_table[builtin_name] = builtin_id

    def _walk_builtin(name: str) -> None:
        for builtin_child in _BUILTIN_CLASS_CHILDREN.get(name, []):
            _walk_builtin(builtin_child)
        for child_fqcn in children.get(name, []):
            _assign(child_fqcn)
        exit_val = next_id_holder[0]
        next_builtin_id = _BUILTIN_CLASS_IDS[name] + 1
        if len(_BUILTIN_CLASS_CHILDREN.get(name, [])) == 0 and len(children.get(name, [])) == 0:
            exit_val = next_builtin_id
        elif exit_val < next_builtin_id:
            exit_val = next_builtin_id
        type_info_table[name] = {"id": _BUILTIN_CLASS_IDS[name], "entry": _BUILTIN_CLASS_IDS[name], "exit": exit_val}

    _walk_builtin("object")

    # Add type_info_table entries for any _BUILTIN_CLASS_IDS entries not processed by
    # _walk_builtin (e.g. None, bool, int, float, str, list, dict, set — standalone leaf types).
    # type_id_table entries were already added above; only type_info is missing.
    for builtin_name in sorted(_BUILTIN_CLASS_IDS.keys()):
        if builtin_name not in type_info_table:
            raw_tid = _BUILTIN_CLASS_IDS[builtin_name]
            type_info_table[builtin_name] = {"id": raw_tid, "entry": raw_tid, "exit": raw_tid + 1}

    for synthetic_root in sorted(_ROOT_BASE_NAMES):
        if synthetic_root in _BUILTIN_CLASS_IDS:
            continue
        for child_fqcn in children.get(synthetic_root, []):
            if child_fqcn not in type_info_table:
                _assign(child_fqcn)

    for fqcn, base_fqcn in sorted(class_bases.items()):
        if base_fqcn == "object" and fqcn not in type_info_table:
            _assign(fqcn)

    object_info = type_info_table.get("object")
    if isinstance(object_info, dict):
        object_info["exit"] = next_id_holder[0]

    if len(type_id_table) != len(class_bases) + len(_BUILTIN_CLASS_IDS):
        raise _input_invalid(
            "failed to assign type_id to all classes: "
            + str(len(type_id_table))
            + "/"
            + str(len(class_bases) + len(_BUILTIN_CLASS_IDS))
        )

    # Build base type_id map
    type_id_base_map: dict[str, int] = {}
    for builtin_name, builtin_id in sorted(_BUILTIN_CLASS_IDS.items(), key=lambda item: item[1]):
        builtin_base = ""
        for candidate, children_list in _BUILTIN_CLASS_CHILDREN.items():
            if builtin_name in children_list:
                builtin_base = candidate
                break
        if builtin_base != "":
            type_id_base_map[builtin_name] = _BUILTIN_CLASS_IDS[builtin_base]
        else:
            type_id_base_map[builtin_name] = builtin_id

    for fqcn, base_fqcn in class_bases.items():
        if base_fqcn in type_id_table:
            type_id_base_map[fqcn] = type_id_table[base_fqcn]
        else:
            base_short = base_fqcn.rsplit(".", 1)[-1] if "." in base_fqcn else base_fqcn
            type_id_base_map[fqcn] = _BUILTIN_TYPE_IDS.get(base_short, _BUILTIN_TYPE_IDS["object"])

    # Convert to JsonVal-compatible dicts
    tid_table: dict[str, JsonVal] = {}
    for k, v in sorted(type_id_table.items()):
        tid_table[k] = v

    tid_base: dict[str, JsonVal] = {}
    for k, v in sorted(type_id_base_map.items()):
        tid_base[k] = v

    tid_info: dict[str, JsonVal] = {}
    for k, v in sorted(type_info_table.items()):
        info: dict[str, JsonVal] = {"id": v["id"], "entry": v["entry"], "exit": v["exit"]}
        tid_info[k] = info

    return tid_table, tid_base, tid_info

"""Trait relationship helpers for linked programs.

Trait は runtime metadata を持たず、link 時に nominal 関係だけを解決する。
"""

from __future__ import annotations

from pytra.std.json import JsonVal

from toolchain.compile.jv import jv_str, jv_is_dict, jv_is_list, jv_dict, jv_list

from toolchain.link.import_maps import collect_import_maps
from toolchain.link.shared_types import LinkedModule


def _safe_str(val: JsonVal) -> str:
    text = ("" + jv_str(val)).strip()
    if text != "":
        return text
    return ""


def _iter_class_defs(east_doc: dict[str, JsonVal]) -> list[dict[str, JsonVal]]:
    body_val = east_doc.get("body")
    out: list[dict[str, JsonVal]] = []
    if not jv_is_list(body_val):
        return out
    for item in jv_list(body_val):
        if jv_is_dict(item):
            item_dict: dict[str, JsonVal] = jv_dict(item)
            if _safe_str(item_dict.get("kind")) == "ClassDef":
                out.append(item_dict)
    return out


def _decorators(class_def: dict[str, JsonVal]) -> list[str]:
    out: list[str] = []
    raw = class_def.get("decorators")
    if jv_is_list(raw):
        for item in jv_list(raw):
            text = _safe_str(item)
            if text != "":
                out.append(text)
    return out


def _is_trait(class_def: dict[str, JsonVal]) -> bool:
    meta = class_def.get("meta")
    if jv_is_dict(meta):
        meta_dict: dict[str, JsonVal] = jv_dict(meta)
        if jv_is_dict(meta_dict.get("trait_v1")):
            return True
    for decorator in _decorators(class_def):
        if decorator == "trait":
            return True
    return False


def _parse_implements(decorator: str) -> list[str]:
    if not decorator.startswith("implements(") or not decorator.endswith(")"):
        return []
    inner = decorator[len("implements("):-1]
    out: list[str] = []
    for part in inner.split(","):
        name = part.strip()
        if name != "":
            out.append(name)
    return out


def _trait_extends_names(class_def: dict[str, JsonVal]) -> list[str]:
    meta = class_def.get("meta")
    if jv_is_dict(meta):
        meta_dict: dict[str, JsonVal] = jv_dict(meta)
        trait_meta = meta_dict.get("trait_v1")
        if jv_is_dict(trait_meta):
            trait_meta_dict: dict[str, JsonVal] = jv_dict(trait_meta)
            extends = trait_meta_dict.get("extends_traits")
            out: list[str] = []
            if jv_is_list(extends):
                for item in jv_list(extends):
                    name = _safe_str(item)
                    if name != "":
                        out.append(name)
            if len(out) > 0:
                return out
    bases = class_def.get("bases")
    out2: list[str] = []
    if jv_is_list(bases):
        for item2 in jv_list(bases):
            name2 = _safe_str(item2)
            if name2 != "":
                out2.append(name2)
    base = _safe_str(class_def.get("base"))
    if base != "" and len(out2) == 0:
        out2.append(base)
    return out2


def _implemented_trait_names(class_def: dict[str, JsonVal]) -> list[str]:
    meta = class_def.get("meta")
    if jv_is_dict(meta):
        meta_dict: dict[str, JsonVal] = jv_dict(meta)
        impl_meta = meta_dict.get("implements_v1")
        if jv_is_dict(impl_meta):
            impl_meta_dict: dict[str, JsonVal] = jv_dict(impl_meta)
            traits = impl_meta_dict.get("traits")
            out: list[str] = []
            if jv_is_list(traits):
                for item in jv_list(traits):
                    name = _safe_str(item)
                    if name != "":
                        out.append(name)
            if len(out) > 0:
                return out
    out2: list[str] = []
    for decorator in _decorators(class_def):
        out2.extend(_parse_implements(decorator))
    return out2


def _input_invalid(message: str) -> RuntimeError:
    return RuntimeError("input_invalid: " + message)


def _resolve_trait_name(
    trait_name: str,
    *,
    module_id: str,
    all_traits: set[str],
    local_traits: dict[str, str],
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
) -> str:
    name = trait_name.strip()
    if name == "":
        return ""
    if name in all_traits:
        return name
    if name in local_traits:
        return local_traits[name]
    imported_symbol = import_symbols.get(name, "").strip()
    if imported_symbol != "" and "::" in imported_symbol:
        sep = imported_symbol.find("::")
        dep_module_id = imported_symbol[:sep].strip()
        export_name = imported_symbol[sep + 2:].strip()
        if dep_module_id != "" and export_name != "":
            candidate = dep_module_id + "." + export_name
            if candidate in all_traits:
                return candidate
    if "." in name:
        last_dot = -1
        i = len(name) - 1
        while i >= 0:
            if name[i] == ".":
                last_dot = i
                break
            i -= 1
        owner_name = name[:last_dot]
        attr_name = name[last_dot + 1:]
        imported_module = import_modules.get(owner_name, "").strip()
        if imported_module != "":
            candidate2 = imported_module + "." + attr_name.strip()
            if candidate2 in all_traits:
                return candidate2
    candidate3 = module_id + "." + name
    if candidate3 in all_traits:
        return candidate3
    raise _input_invalid("undefined trait: " + module_id + " -> " + name)


def build_trait_implementation_map(modules: list[LinkedModule]) -> tuple[set[str], dict[str, set[str]]]:
    all_traits: set[str] = set()
    local_traits_by_module: dict[str, dict[str, str]] = {}
    import_modules_by_module: dict[str, dict[str, str]] = {}
    import_symbols_by_module: dict[str, dict[str, str]] = {}
    class_defs_by_module: dict[str, list[dict[str, JsonVal]]] = {}

    for module in modules:
        doc = module.east_doc
        import_modules_for_module, import_symbols_for_module = collect_import_maps(doc)
        import_modules_by_module[module.module_id] = import_modules_for_module
        import_symbols_by_module[module.module_id] = import_symbols_for_module
        class_defs = _iter_class_defs(doc)
        class_defs_by_module[module.module_id] = class_defs
        local_traits: dict[str, str] = {}
        for class_def in class_defs:
            if not _is_trait(class_def):
                continue
            class_name = _safe_str(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            local_traits[class_name] = fqcn
            all_traits.add(fqcn)
        local_traits_by_module[module.module_id] = local_traits

    trait_bases: dict[str, list[str]] = {}
    for module in modules:
        import_modules = import_modules_by_module.get(module.module_id, {})
        import_symbols = import_symbols_by_module.get(module.module_id, {})
        local_traits = local_traits_by_module.get(module.module_id, {})
        class_defs = class_defs_by_module.get(module.module_id, [])
        for class_def in class_defs:
            if not _is_trait(class_def):
                continue
            class_name = _safe_str(class_def.get("name"))
            if class_name == "":
                continue
            fqcn = module.module_id + "." + class_name
            bases: list[str] = []
            for base_name in _trait_extends_names(class_def):
                bases.append(
                    _resolve_trait_name(
                        base_name,
                        module_id=module.module_id,
                        all_traits=all_traits,
                        local_traits=local_traits,
                        import_modules=import_modules,
                        import_symbols=import_symbols,
                    )
                )
            trait_bases[fqcn] = bases

    memo: dict[str, set[str]] = {}

    def _trait_closure(fqcn: str, stack: list[str]) -> set[str]:
        if fqcn in memo:
            return memo[fqcn]
        if fqcn in stack:
            raise _input_invalid("trait inheritance cycle: " + " -> ".join(stack + [fqcn]))
        out: set[str] = {fqcn}
        for base_fqcn in trait_bases.get(fqcn, []):
            base_closure = _trait_closure(base_fqcn, stack + [fqcn])
            for inherited_fqcn in base_closure:
                out.add(inherited_fqcn)
        memo[fqcn] = out
        return out

    impls_by_type: dict[str, set[str]] = {}
    empty_stack: list[str] = []
    for trait_fqcn in sorted(all_traits):
        impls_by_type[trait_fqcn] = set(_trait_closure(trait_fqcn, empty_stack))

    for module in modules:
        import_modules2 = import_modules_by_module.get(module.module_id, {})
        import_symbols2 = import_symbols_by_module.get(module.module_id, {})
        local_traits2 = local_traits_by_module.get(module.module_id, {})
        class_defs2 = class_defs_by_module.get(module.module_id, [])
        for class_def2 in class_defs2:
            if _is_trait(class_def2):
                continue
            class_name2 = _safe_str(class_def2.get("name"))
            if class_name2 == "":
                continue
            fqcn2 = module.module_id + "." + class_name2
            trait_set: set[str] = set()
            for impl_name in _implemented_trait_names(class_def2):
                trait_fqcn = _resolve_trait_name(
                    impl_name,
                    module_id=module.module_id,
                    all_traits=all_traits,
                    local_traits=local_traits2,
                    import_modules=import_modules2,
                    import_symbols=import_symbols2,
                )
                impl_closure = _trait_closure(trait_fqcn, empty_stack)
                for inherited_impl in impl_closure:
                    trait_set.add(inherited_impl)
            if len(trait_set) > 0:
                impls_by_type[fqcn2] = trait_set

    return all_traits, impls_by_type

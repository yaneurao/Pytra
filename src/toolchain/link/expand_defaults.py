"""Cross-module default argument expansion for linked programs.

Link 段で全 module の FunctionDef から arg_defaults を収集し、
Call ノードの引数が不足している場合にデフォルト値を補完する。

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.typing import cast

from toolchain.common.jv import deep_copy_json
from toolchain.link.import_maps import collect_import_modules, collect_import_symbols
from toolchain.resolve.py.type_norm import make_type_expr, normalize_type
from toolchain.compile.jv import jv_str, jv_is_dict, jv_is_list, jv_dict, jv_list, nd_get_str, nd_get_dict, nd_get_list


def _module_id_from_doc(doc: dict[str, JsonVal]) -> str:
    """Extract module_id from linked metadata or raw EAST meta."""
    meta: dict[str, JsonVal] = nd_get_dict(doc, "meta")
    if len(meta) == 0:
        return ""
    lp: dict[str, JsonVal] = nd_get_dict(meta, "linked_program_v1")
    module_id: str = nd_get_str(lp, "module_id")
    if module_id != "":
        return module_id
    return "" + nd_get_str(meta, "module_id")


def _collect_all_fn_sigs(modules: list[dict[str, JsonVal]]) -> dict[str, dict[str, JsonVal]]:
    """Collect function signatures from all modules."""
    sigs: dict[str, dict[str, JsonVal]] = {}
    for doc in modules:
        module_id = _module_id_from_doc(doc)
        if module_id == "":
            continue
        for stmt in nd_get_list(doc, "body"):
            if jv_is_dict(stmt):
                _collect_sig(jv_dict(stmt), sigs, module_id, "")
    return sigs


def _collect_sig(
    node: dict[str, JsonVal],
    sigs: dict[str, dict[str, JsonVal]],
    module_id: str,
    class_name: str,
) -> None:
    kind: str = nd_get_str(node, "kind")
    if kind == "FunctionDef":
        name: str = nd_get_str(node, "name")
        if name == "" or module_id == "":
            return
        ao: list[JsonVal] = nd_get_list(node, "arg_order")
        if len(ao) == 0:
            return
        ad: dict[str, JsonVal] = nd_get_dict(node, "arg_defaults")
        at: dict[str, JsonVal] = nd_get_dict(node, "arg_types")
        sig: dict[str, JsonVal] = {
            "arg_order": ao,
            "arg_defaults": ad,
            "arg_types": at,
        }
        full = name
        if class_name != "":
            full = class_name + "." + name
        sigs[module_id + "::" + full] = sig

        for stmt in nd_get_list(node, "body"):
            if jv_is_dict(stmt):
                _collect_sig(jv_dict(stmt), sigs, module_id, "")
        return

    if kind == "ClassDef":
        class_name2: str = nd_get_str(node, "name")
        if class_name2 == "":
            return
        for stmt in nd_get_list(node, "body"):
            if jv_is_dict(stmt):
                _collect_sig(jv_dict(stmt), sigs, module_id, class_name2)


def _expand_defaults_collection_hint(type_name: str) -> str:
    t = type_name.strip()
    if t.endswith(" | None"):
        t = t[:-7].strip()
    elif t.endswith("|None"):
        t = t[:-6].strip()
    if t.startswith("list[") or t.startswith("dict[") or t.startswith("set["):
        return t
    return ""


def _apply_collection_default_hint(default_node: JsonVal, param_type: str) -> None:
    if not jv_is_dict(default_node):
        return
    default_map: dict[str, JsonVal] = jv_dict(default_node)
    empty_aliases: dict[str, str] = {}
    empty_seen: set[str] = set()
    hinted = _expand_defaults_collection_hint(normalize_type(param_type, empty_aliases, empty_seen))
    if hinted == "":
        return
    kind: str = nd_get_str(default_map, "kind")
    current_type: str = nd_get_str(default_map, "resolved_type")
    if kind == "List" and hinted.startswith("list[") and current_type in ("", "unknown", "list[unknown]"):
        default_map["resolved_type"] = hinted
        return
    if kind == "Dict" and hinted.startswith("dict[") and current_type in ("", "unknown", "dict[unknown,unknown]"):
        default_map["resolved_type"] = hinted
        return
    if kind == "Set" and hinted.startswith("set[") and current_type in ("", "unknown", "set[unknown]"):
        default_map["resolved_type"] = hinted
        return


def _resolve_call_sig_key(
    node: dict[str, JsonVal],
    *,
    current_module_id: str,
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
) -> str:
    """Resolve a Call node to a qualified signature key."""
    func: dict[str, JsonVal] = nd_get_dict(node, "func")
    if len(func) == 0:
        return ""

    fk: str = nd_get_str(func, "kind")
    if fk == "Name":
        fn_id: str = nd_get_str(func, "id")
        if fn_id != "":
            imported = import_symbols.get(fn_id, "")
            if imported != "":
                return imported
            if current_module_id != "":
                return current_module_id + "::" + fn_id
        return ""

    if fk == "Attribute":
        attr: str = nd_get_str(func, "attr")
        owner: dict[str, JsonVal] = nd_get_dict(func, "value")
        if attr == "" or len(owner) == 0:
            return ""
        if nd_get_str(owner, "kind") != "Name":
            return ""
        owner_id: str = nd_get_str(owner, "id")
        if owner_id == "":
            return ""
        module_id = import_modules.get(owner_id, "")
        if module_id != "":
            return module_id + "::" + attr

        imported = import_symbols.get(owner_id, "")
        if imported != "":
            owner_rt: str = nd_get_str(owner, "resolved_type")
            if owner_rt == "module":
                runtime_module_id: str = nd_get_str(owner, "runtime_module_id")
                if runtime_module_id != "":
                    return runtime_module_id + "::" + attr
                if "::" in imported:
                    sep = imported.find("::")
                    mod = imported[0:sep]
                    export_name = imported[sep + 2:]
                    if mod != "" and export_name != "":
                        return mod + "." + export_name + "::" + attr

        owner_rt2: str = nd_get_str(owner, "resolved_type")
        if owner_rt2 != "":
            for _symbol_name, imported2 in import_symbols.items():
                if "::" not in imported2:
                    continue
                sep2: int = imported2.find("::")
                mod2: str = imported2[0:sep2]
                export_name2: str = imported2[sep2 + 2:]
                if export_name2 == owner_rt2:
                    if mod2.startswith("pytra."):
                        return mod2 + "::" + export_name2 + "." + attr
                    if mod2 != "":
                        return "pytra.std." + mod2 + "::" + export_name2 + "." + attr
                    return mod2 + "::" + export_name2 + "." + attr
            if current_module_id != "":
                return current_module_id + "::" + owner_rt2 + "." + attr

    return ""


def _expand_walk(
    node: JsonVal,
    sigs: dict[str, dict[str, JsonVal]],
    *,
    current_module_id: str,
    import_modules: dict[str, str],
    import_symbols: dict[str, str],
) -> None:
    """Recursively walk the AST and expand default arguments in Call nodes."""
    if jv_is_list(node):
        for item in jv_list(node):
            _expand_walk(
                item,
                sigs,
                current_module_id=current_module_id,
                import_modules=import_modules,
                import_symbols=import_symbols,
            )
        return
    if not jv_is_dict(node):
        return

    node_map: dict[str, JsonVal] = jv_dict(node)
    if nd_get_str(node_map, "kind") == "Call":
        sig_key = _resolve_call_sig_key(
            node_map,
            current_module_id=current_module_id,
            import_modules=import_modules,
            import_symbols=import_symbols,
        )
        if sig_key != "" and sig_key in sigs:
            sig = sigs[sig_key]
            ao: list[JsonVal] = nd_get_list(sig, "arg_order")
            empty_node: dict[str, JsonVal] = {}
            ad: dict[str, JsonVal] = empty_node
            if "arg_defaults" in sig and jv_is_dict(sig["arg_defaults"]):
                ad = jv_dict(sig["arg_defaults"])
            empty_types: dict[str, JsonVal] = {}
            at: dict[str, JsonVal] = empty_types
            if "arg_types" in sig and jv_is_dict(sig["arg_types"]):
                at = jv_dict(sig["arg_types"])
            empty_args: list[JsonVal] = []
            args: list[JsonVal] = empty_args
            if "args" in node_map and jv_is_list(node_map["args"]):
                args = jv_list(node_map["args"])
            if len(ao) != 0:
                expected: list[str] = []
                for p in ao:
                    p_text: str = jv_str(p)
                    name: str = p_text.strip()
                    if name != "" and name != "self":
                        expected.append(name)
                n_expected: int = len(expected)

                kw_map: dict[str, JsonVal] = {}
                empty_kws: list[JsonVal] = []
                kws: list[JsonVal] = empty_kws
                if "keywords" in node_map and jv_is_list(node_map["keywords"]):
                    kws = jv_list(node_map["keywords"])
                for kw in kws:
                    if not jv_is_dict(kw):
                        continue
                    kw_node: dict[str, JsonVal] = jv_dict(kw)
                    ka: str = nd_get_str(kw_node, "arg")
                    if ka != "":
                        if "value" in kw_node:
                            kw_map[ka] = kw_node["value"]

                if len(args) < n_expected:
                    i: int = len(args)
                    while i < n_expected:
                        param_name = expected[i]
                        if param_name in kw_map:
                            kv2 = kw_map[param_name]
                            if jv_is_dict(kv2) or jv_is_list(kv2):
                                args.append(deep_copy_json(kv2))
                            else:
                                args.append(kv2)
                        elif param_name in ad:
                            default_val = ad[param_name]
                            if jv_is_dict(default_val) or jv_is_list(default_val):
                                copied = deep_copy_json(default_val)
                                if jv_is_dict(copied):
                                    param_type: str = nd_get_str(at, param_name)
                                    if param_type != "":
                                        _apply_collection_default_hint(copied, param_type)
                                args.append(copied)
                            else:
                                args.append(default_val)
                        i += 1
                node_map["args"] = args
                if len(kw_map) > 0:
                    empty_keywords: list[JsonVal] = []
                    node_map["keywords"] = empty_keywords

    for _key, value in node_map.items():
        if jv_is_dict(value) or jv_is_list(value):
            _expand_walk(
                value,
                sigs,
                current_module_id=current_module_id,
                import_modules=import_modules,
                import_symbols=import_symbols,
            )


def expand_cross_module_defaults(
    modules_with_ids: list[JsonVal],
) -> None:
    """Expand default arguments in Call nodes across all linked modules."""
    sigs: dict[str, dict[str, JsonVal]] = {}
    normalized: list[tuple[str, dict[str, JsonVal]]] = []
    for entry in modules_with_ids:
        if not jv_is_dict(entry):
            continue
        doc: dict[str, JsonVal] = jv_dict(entry)
        module_id = _module_id_from_doc(doc)
        normalized.append((module_id, doc))
        if module_id == "":
            continue
        for stmt in nd_get_list(doc, "body"):
            if jv_is_dict(stmt):
                _collect_sig(jv_dict(stmt), sigs, module_id, "")

    if len(sigs) == 0:
        return

    for module_id, doc in normalized:
        import_modules: dict[str, str] = collect_import_modules(doc)
        import_symbols: dict[str, str] = collect_import_symbols(doc)
        _expand_walk(
            doc,
            sigs,
            current_module_id=module_id,
            import_modules=import_modules,
            import_symbols=import_symbols,
        )

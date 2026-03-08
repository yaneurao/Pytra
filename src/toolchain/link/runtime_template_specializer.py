"""Linked-program specialization for runtime-helper `@template` v1."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from toolchain.ir.east3_opt_passes.non_escape_call_graph import collect_non_escape_import_maps
from toolchain.ir.east3_opt_passes.non_escape_call_graph import collect_non_escape_symbols
from toolchain.ir.east3_opt_passes.non_escape_call_graph import resolve_non_escape_call_target
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule


_TEMPLATE_META_KEY = "template_v1"
_SPECIALIZATION_META_KEY = "template_specialization_v1"


def _safe_name(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text != "":
            return text
    return ""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _kind(node: Any) -> str:
    return str(node.get("kind", "")) if isinstance(node, dict) else ""


def _func_local_name(symbol: str) -> str:
    if "::" not in symbol:
        return symbol
    return symbol.split("::", 1)[1]


def _module_for_symbol(symbol: str) -> str:
    if "::" not in symbol:
        return ""
    return symbol.split("::", 1)[0]


def _encode_type_name(text: str) -> str:
    out_chars: list[str] = []
    prev_us = False
    for ch in text:
        if ch.isalnum():
            out_chars.append(ch)
            prev_us = False
            continue
        if not prev_us:
            out_chars.append("_")
        prev_us = True
    encoded = "".join(out_chars).strip("_")
    return encoded if encoded != "" else "type"


def _parse_type_expr(text: str) -> Any:
    src = text.strip()
    if src == "":
        return ""

    def _skip(i: int) -> int:
        while i < len(src) and src[i].isspace():
            i += 1
        return i

    def _parse(i: int) -> tuple[Any, int]:
        i = _skip(i)
        start = i
        while i < len(src) and (src[i].isalnum() or src[i] in {"_", "."}):
            i += 1
        if start == i:
            raise ValueError("type identifier expected")
        head = src[start:i]
        i = _skip(i)
        if i >= len(src) or src[i] != "[":
            return head, i
        i += 1
        args: list[Any] = []
        while True:
            arg, i = _parse(i)
            args.append(arg)
            i = _skip(i)
            if i < len(src) and src[i] == ",":
                i += 1
                continue
            if i < len(src) and src[i] == "]":
                i += 1
                break
            raise ValueError("unterminated type argument list")
        return (head, tuple(args)), i

    expr, pos = _parse(0)
    pos = _skip(pos)
    if pos != len(src):
        raise ValueError("trailing type tokens")
    return expr


def _type_expr_to_string(expr: Any) -> str:
    if isinstance(expr, str):
        return expr
    if isinstance(expr, tuple) and len(expr) == 2 and isinstance(expr[0], str):
        name = expr[0]
        args = expr[1] if isinstance(expr[1], tuple) else tuple()
        return name + "[" + ",".join(_type_expr_to_string(arg) for arg in args) + "]"
    return str(expr)


def _unify_type_expr(
    formal_expr: Any,
    actual_expr: Any,
    *,
    template_params: set[str],
    bindings: dict[str, str],
) -> bool:
    if isinstance(formal_expr, str):
        if formal_expr in template_params:
            actual_text = _type_expr_to_string(actual_expr)
            prev = bindings.get(formal_expr)
            if prev is None:
                bindings[formal_expr] = actual_text
                return True
            return prev == actual_text
        return isinstance(actual_expr, str) and formal_expr == actual_expr
    if not (isinstance(formal_expr, tuple) and len(formal_expr) == 2):
        return False
    if not (isinstance(actual_expr, tuple) and len(actual_expr) == 2):
        return False
    if formal_expr[0] != actual_expr[0]:
        return False
    formal_args = formal_expr[1] if isinstance(formal_expr[1], tuple) else tuple()
    actual_args = actual_expr[1] if isinstance(actual_expr[1], tuple) else tuple()
    if len(formal_args) != len(actual_args):
        return False
    idx = 0
    while idx < len(formal_args):
        if not _unify_type_expr(
            formal_args[idx],
            actual_args[idx],
            template_params=template_params,
            bindings=bindings,
        ):
            return False
        idx += 1
    return True


def _substitute_type_expr(expr: Any, bindings: dict[str, str]) -> Any:
    if isinstance(expr, str):
        replacement = bindings.get(expr)
        if replacement is None:
            return expr
        return _parse_type_expr(replacement)
    if isinstance(expr, tuple) and len(expr) == 2:
        name = expr[0]
        args = expr[1] if isinstance(expr[1], tuple) else tuple()
        return (name, tuple(_substitute_type_expr(arg, bindings) for arg in args))
    return expr


def _substitute_type_text(text: str, bindings: dict[str, str]) -> str:
    raw = _safe_name(text)
    if raw == "":
        return text
    try:
        expr = _parse_type_expr(raw)
    except Exception:
        return bindings.get(raw, raw)
    return _type_expr_to_string(_substitute_type_expr(expr, bindings))


def _substitute_types_in_node(node: Any, bindings: dict[str, str]) -> None:
    if isinstance(node, list):
        for item in node:
            _substitute_types_in_node(item, bindings)
        return
    if not isinstance(node, dict):
        return
    for key, value in list(node.items()):
        if key == "arg_types" and isinstance(value, dict):
            out_arg_types: dict[str, Any] = {}
            for arg_name, arg_type_any in value.items():
                if isinstance(arg_type_any, str):
                    out_arg_types[arg_name] = _substitute_type_text(arg_type_any, bindings)
                else:
                    out_arg_types[arg_name] = arg_type_any
            node[key] = out_arg_types
            continue
        if key in {"annotation", "return_type", "resolved_type", "yield_value_type"} and isinstance(value, str):
            node[key] = _substitute_type_text(value, bindings)
            continue
        _substitute_types_in_node(value, bindings)


@dataclass(frozen=True)
class _TemplateDef:
    qualified_symbol: str
    module_id: str
    local_name: str
    fn_node: dict[str, Any]
    params: tuple[str, ...]
    arg_order: tuple[str, ...]
    arg_types: dict[str, str]
    return_type: str


@dataclass(frozen=True)
class _Specialization:
    template_symbol: str
    module_id: str
    export_name: str
    local_name: str
    type_args: tuple[str, ...]
    bindings: dict[str, str]
    fn_node: dict[str, Any]


class _TemplateMaterializer:
    def __init__(self, program: LinkedProgram) -> None:
        self.program = program
        self.module_docs: dict[str, dict[str, Any]] = {}
        self.module_import_modules: dict[str, dict[str, str]] = {}
        self.module_import_symbols: dict[str, dict[str, str]] = {}
        self.module_local_symbol_maps: dict[str, dict[str, str]] = {}
        self.module_template_body_names: dict[str, set[str]] = {}
        self.template_defs: dict[str, _TemplateDef] = {}
        self.known_symbols: set[str] = set()
        self.specializations: dict[tuple[str, tuple[str, ...]], _Specialization] = {}
        self.specialized_nodes_by_symbol: dict[str, list[dict[str, Any]]] = {}
        self.import_symbol_rewrites: dict[str, dict[tuple[str, str, str], set[str]]] = {}

        for module in program.modules:
            doc_any = deepcopy(module.east_doc)
            doc = doc_any if isinstance(doc_any, dict) else {}
            self.module_docs[module.module_id] = doc
            _module_id, symbols, local_symbol_map = collect_non_escape_symbols(doc)
            import_modules, import_symbols = collect_non_escape_import_maps(doc)
            self.module_import_modules[module.module_id] = dict(import_modules)
            self.module_import_symbols[module.module_id] = dict(import_symbols)
            self.module_local_symbol_maps[module.module_id] = dict(local_symbol_map)
            self.known_symbols.update(symbols.keys())
            template_names: set[str] = set()
            for qualified_symbol, fn_node in sorted(symbols.items()):
                meta = _as_dict(fn_node.get("meta"))
                template_meta = _as_dict(meta.get(_TEMPLATE_META_KEY))
                if len(template_meta) == 0:
                    continue
                params = tuple(_safe_name(item) for item in _as_list(template_meta.get("params")))
                params = tuple(item for item in params if item != "")
                if len(params) == 0:
                    continue
                local_name = _func_local_name(qualified_symbol)
                self.template_defs[qualified_symbol] = _TemplateDef(
                    qualified_symbol=qualified_symbol,
                    module_id=module.module_id,
                    local_name=local_name,
                    fn_node=fn_node,
                    params=params,
                    arg_order=tuple(_safe_name(name) for name in _as_list(fn_node.get("arg_order")) if _safe_name(name) != ""),
                    arg_types={
                        _safe_name(name): _safe_name(type_text)
                        for name, type_text in _as_dict(fn_node.get("arg_types")).items()
                        if _safe_name(name) != "" and _safe_name(type_text) != ""
                    },
                    return_type=_safe_name(fn_node.get("return_type")),
                )
                template_names.add(local_name)
            self.module_template_body_names[module.module_id] = template_names
            self.import_symbol_rewrites[module.module_id] = {}

    def materialize(self) -> tuple[LinkedProgram, dict[str, object]]:
        if len(self.template_defs) == 0:
            return self.program, {}
        for module in sorted(self.program.modules, key=lambda item: item.module_id):
            doc = self.module_docs[module.module_id]
            self._rewrite_module_functions(doc, module.module_id)
        final_modules: list[LinkedProgramModule] = []
        specialization_summary: dict[str, list[dict[str, object]]] = {}
        for module in sorted(self.program.modules, key=lambda item: item.module_id):
            doc = self.module_docs[module.module_id]
            self._finalize_import_symbol_rewrites(doc, module.module_id)
            self._replace_template_defs_with_specializations(doc, module.module_id, specialization_summary)
            final_modules.append(
                LinkedProgramModule(
                    module_id=module.module_id,
                    source_path=module.source_path,
                    is_entry=module.is_entry,
                    east_doc=doc,
                    artifact_path=module.artifact_path,
                )
            )
        linked_program = LinkedProgram(
            schema=self.program.schema,
            manifest_path=self.program.manifest_path,
            target=self.program.target,
            dispatch_mode=self.program.dispatch_mode,
            entry_modules=self.program.entry_modules,
            modules=tuple(final_modules),
            options=dict(self.program.options),
        )
        summary: dict[str, object] = {}
        if len(specialization_summary) > 0:
            ordered: dict[str, object] = {}
            for symbol in sorted(specialization_summary.keys()):
                ordered[symbol] = specialization_summary[symbol]
            summary["runtime_template_specializations_v1"] = ordered
        return linked_program, summary

    def _rewrite_module_functions(self, module_doc: dict[str, Any], module_id: str) -> None:
        body = _as_list(module_doc.get("body"))
        for item in body:
            if _kind(item) != "FunctionDef":
                continue
            name = _safe_name(item.get("name"))
            if name in self.module_template_body_names.get(module_id, set()):
                continue
            self._rewrite_calls_in_function(item, module_id=module_id, owner_class="")
        for item in body:
            if _kind(item) != "ClassDef":
                continue
            class_name = _safe_name(item.get("name"))
            for child in _as_list(item.get("body")):
                if _kind(child) != "FunctionDef":
                    continue
                self._rewrite_calls_in_function(child, module_id=module_id, owner_class=class_name)

    def _rewrite_calls_in_function(self, fn_node: dict[str, Any], *, module_id: str, owner_class: str) -> None:
        def _visit(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    _visit(item)
                return
            if not isinstance(node, dict):
                return
            for value in node.values():
                _visit(value)
            if _kind(node) != "Call":
                return
            self._rewrite_call_node(node, module_id=module_id, owner_class=owner_class)

        _visit(_as_list(fn_node.get("body")))

    def _rewrite_call_node(self, call_node: dict[str, Any], *, module_id: str, owner_class: str) -> None:
        target, resolved = resolve_non_escape_call_target(
            call_node,
            owner_class=owner_class,
            local_symbol_map=self.module_local_symbol_maps.get(module_id, {}),
            import_modules=self.module_import_modules.get(module_id, {}),
            import_symbols=self.module_import_symbols.get(module_id, {}),
            known_symbols=self.known_symbols,
        )
        if not resolved:
            return
        template_def = self.template_defs.get(target)
        if template_def is None:
            return
        bindings = self._infer_specialization_bindings(template_def, call_node)
        type_args = tuple(bindings[param] for param in template_def.params)
        specialization = self._ensure_specialization(template_def, bindings=bindings, type_args=type_args)
        self._rewrite_call_target(
            call_node,
            caller_module_id=module_id,
            template_symbol=target,
            specialization=specialization,
        )
        if template_def.return_type != "":
            call_node["resolved_type"] = _substitute_type_text(template_def.return_type, bindings)

    def _infer_specialization_bindings(self, template_def: _TemplateDef, call_node: dict[str, Any]) -> dict[str, str]:
        actuals: dict[str, str] = {}
        args = _as_list(call_node.get("args"))
        if len(args) > len(template_def.arg_order):
            raise RuntimeError(
                "template_specialization_violation: too many positional args for "
                + template_def.qualified_symbol
            )
        idx = 0
        while idx < len(args):
            param_name = template_def.arg_order[idx]
            actual_type = _safe_name(_as_dict(args[idx]).get("resolved_type"))
            if actual_type == "":
                actual_type = "unknown"
            actuals[param_name] = actual_type
            idx += 1
        for keyword_any in _as_list(call_node.get("keywords")):
            keyword = _as_dict(keyword_any)
            arg_name = _safe_name(keyword.get("arg"))
            if arg_name == "":
                raise RuntimeError(
                    "template_specialization_violation: keyword args require named parameters: "
                    + template_def.qualified_symbol
                )
            if arg_name in actuals:
                raise RuntimeError(
                    "template_specialization_violation: duplicate argument for "
                    + template_def.qualified_symbol
                    + ": "
                    + arg_name
                )
            actual_type = _safe_name(_as_dict(keyword.get("value")).get("resolved_type"))
            if actual_type == "":
                actual_type = "unknown"
            actuals[arg_name] = actual_type

        bindings: dict[str, str] = {}
        param_set = set(template_def.params)
        for param_name, formal_type in sorted(template_def.arg_types.items()):
            if param_name not in actuals:
                continue
            actual_type = actuals[param_name]
            try:
                formal_expr = _parse_type_expr(formal_type)
                actual_expr = _parse_type_expr(actual_type)
            except Exception as exc:
                raise RuntimeError(
                    "template_specialization_violation: failed to parse specialization types for "
                    + template_def.qualified_symbol
                    + ": "
                    + formal_type
                    + " vs "
                    + actual_type
                ) from exc
            if not _unify_type_expr(
                formal_expr,
                actual_expr,
                template_params=param_set,
                bindings=bindings,
            ):
                raise RuntimeError(
                    "template_specialization_violation: could not bind template params for "
                    + template_def.qualified_symbol
                    + ": "
                    + formal_type
                    + " vs "
                    + actual_type
                )
        for param_name in template_def.params:
            if _safe_name(bindings.get(param_name)) == "":
                raise RuntimeError(
                    "template_specialization_violation: missing concrete type for "
                    + template_def.qualified_symbol
                    + ": "
                    + param_name
                )
        return bindings

    def _ensure_specialization(
        self,
        template_def: _TemplateDef,
        *,
        bindings: dict[str, str],
        type_args: tuple[str, ...],
    ) -> _Specialization:
        key = (template_def.qualified_symbol, type_args)
        existing = self.specializations.get(key)
        if existing is not None:
            return existing
        export_name = template_def.local_name + "__pytra_tmpl__" + "__".join(_encode_type_name(arg) for arg in type_args)
        clone_any = deepcopy(template_def.fn_node)
        clone = clone_any if isinstance(clone_any, dict) else {}
        clone["name"] = export_name
        decorators = [item for item in _as_list(clone.get("decorators")) if isinstance(item, str)]
        decorators = [item for item in decorators if "@template" not in item and not item.startswith("template(") and item != "template"]
        if len(decorators) > 0:
            clone["decorators"] = decorators
        elif "decorators" in clone:
            clone.pop("decorators", None)
        meta = _as_dict(clone.get("meta"))
        if _TEMPLATE_META_KEY in meta:
            meta.pop(_TEMPLATE_META_KEY, None)
        meta[_SPECIALIZATION_META_KEY] = {
            "schema_version": 1,
            "origin_symbol": template_def.qualified_symbol,
            "type_args": list(type_args),
        }
        clone["meta"] = meta
        _substitute_types_in_node(clone, bindings)
        specialization = _Specialization(
            template_symbol=template_def.qualified_symbol,
            module_id=template_def.module_id,
            export_name=export_name,
            local_name=export_name,
            type_args=type_args,
            bindings=dict(bindings),
            fn_node=clone,
        )
        self.specializations[key] = specialization
        self.specialized_nodes_by_symbol.setdefault(template_def.qualified_symbol, []).append(clone)
        self.known_symbols.add(template_def.module_id + "::" + export_name)
        self._rewrite_calls_in_function(clone, module_id=template_def.module_id, owner_class="")
        return specialization

    def _rewrite_call_target(
        self,
        call_node: dict[str, Any],
        *,
        caller_module_id: str,
        template_symbol: str,
        specialization: _Specialization,
    ) -> None:
        func = _as_dict(call_node.get("func"))
        kind = _kind(func)
        template_module_id = _module_for_symbol(template_symbol)
        template_local_name = _func_local_name(template_symbol)
        if kind == "Name":
            local_name = _safe_name(func.get("id"))
            import_target = self.module_import_symbols.get(caller_module_id, {}).get(local_name, "")
            if import_target == template_symbol:
                rewrites = self.import_symbol_rewrites.setdefault(caller_module_id, {})
                key = (template_module_id, template_local_name, local_name)
                rewrites.setdefault(key, set()).add(specialization.export_name)
                func["id"] = specialization.local_name
                func["repr"] = specialization.local_name
                return
            func["id"] = specialization.local_name
            func["repr"] = specialization.local_name
            return
        if kind == "Attribute":
            owner = _as_dict(func.get("value"))
            owner_name = _safe_name(owner.get("id"))
            if owner_name != "":
                func["attr"] = specialization.export_name
                if owner_name != "":
                    func["repr"] = owner_name + "." + specialization.export_name

    def _finalize_import_symbol_rewrites(self, module_doc: dict[str, Any], module_id: str) -> None:
        rewrites = self.import_symbol_rewrites.get(module_id, {})
        if len(rewrites) == 0:
            return
        meta = _as_dict(module_doc.get("meta"))
        old_bindings = [dict(_as_dict(item)) for item in _as_list(meta.get("import_bindings"))]
        new_bindings: list[dict[str, Any]] = []
        for binding in old_bindings:
            if _safe_name(binding.get("binding_kind")) != "symbol":
                new_bindings.append(binding)
                continue
            key = (
                _safe_name(binding.get("module_id")),
                _safe_name(binding.get("export_name")),
                _safe_name(binding.get("local_name")),
            )
            replacements = rewrites.get(key)
            if not replacements:
                new_bindings.append(binding)
                continue
            for export_name in sorted(replacements):
                new_bindings.append(
                    {
                        "module_id": key[0],
                        "export_name": export_name,
                        "local_name": export_name,
                        "binding_kind": "symbol",
                    }
                )
        import_modules: dict[str, str] = {}
        import_symbols: dict[str, dict[str, str]] = {}
        qualified_refs: list[dict[str, str]] = []
        for binding in new_bindings:
            binding_kind = _safe_name(binding.get("binding_kind"))
            module_name = _safe_name(binding.get("module_id"))
            local_name = _safe_name(binding.get("local_name"))
            export_name = _safe_name(binding.get("export_name"))
            if binding_kind == "module" and module_name != "" and local_name != "":
                import_modules[local_name] = module_name
            if binding_kind == "symbol" and module_name != "" and local_name != "" and export_name != "":
                import_symbols[local_name] = {"module": module_name, "name": export_name}
                qualified_refs.append(
                    {"module_id": module_name, "symbol": export_name, "local_name": local_name}
                )
        import_resolution = _as_dict(meta.get("import_resolution"))
        import_resolution["schema_version"] = 1
        import_resolution["bindings"] = new_bindings
        import_resolution["qualified_refs"] = qualified_refs
        meta["import_bindings"] = new_bindings
        meta["import_symbols"] = import_symbols
        meta["import_modules"] = import_modules
        meta["qualified_symbol_refs"] = qualified_refs
        meta["import_resolution"] = import_resolution
        module_doc["meta"] = meta

        body = _as_list(module_doc.get("body"))
        updated_body: list[dict[str, Any]] = []
        by_module: dict[str, list[tuple[tuple[str, str, str], set[str]]]] = {}
        for key, exports in rewrites.items():
            by_module.setdefault(key[0], []).append((key, exports))
        for stmt_any in body:
            stmt = _as_dict(stmt_any)
            if _kind(stmt) != "ImportFrom":
                updated_body.append(stmt)
                continue
            imported_module = _safe_name(stmt.get("module"))
            module_rules = by_module.get(imported_module, [])
            if len(module_rules) == 0:
                updated_body.append(stmt)
                continue
            names = _as_list(stmt.get("names"))
            kept_names: list[dict[str, Any]] = []
            added_for_key: set[tuple[str, str, str]] = set()
            for name_any in names:
                name_obj = _as_dict(name_any)
                import_name = _safe_name(name_obj.get("name"))
                asname_any = name_obj.get("asname")
                asname = _safe_name(asname_any) if asname_any is not None else ""
                local_name = asname if asname != "" else import_name
                matched_key: tuple[str, str, str] | None = None
                matched_exports: set[str] | None = None
                for key, exports in module_rules:
                    _module_id, export_name, old_local = key
                    if export_name == import_name and old_local == local_name:
                        matched_key = key
                        matched_exports = exports
                        break
                if matched_key is None or matched_exports is None:
                    kept_names.append(name_obj)
                    continue
                added_for_key.add(matched_key)
                for export_name in sorted(matched_exports):
                    kept_names.append({"name": export_name, "asname": None})
            for key, exports in module_rules:
                if key in added_for_key:
                    continue
                for export_name in sorted(exports):
                    kept_names.append({"name": export_name, "asname": None})
            if len(kept_names) == 0:
                continue
            stmt["names"] = kept_names
            updated_body.append(stmt)
        module_doc["body"] = updated_body

    def _replace_template_defs_with_specializations(
        self,
        module_doc: dict[str, Any],
        module_id: str,
        specialization_summary: dict[str, list[dict[str, object]]],
    ) -> None:
        body = _as_list(module_doc.get("body"))
        new_body: list[dict[str, Any]] = []
        for item in body:
            if _kind(item) != "FunctionDef":
                new_body.append(item)
                continue
            local_name = _safe_name(item.get("name"))
            qualified_symbol = module_id + "::" + local_name
            template_def = self.template_defs.get(qualified_symbol)
            if template_def is None:
                new_body.append(item)
                continue
            specialized_nodes = self.specialized_nodes_by_symbol.get(qualified_symbol, [])
            for specialized in sorted(specialized_nodes, key=lambda node: _safe_name(node.get("name"))):
                new_body.append(deepcopy(specialized))
            if len(specialized_nodes) > 0:
                entries = specialization_summary.setdefault(qualified_symbol, [])
                for specialized in sorted(specialized_nodes, key=lambda node: _safe_name(node.get("name"))):
                    meta = _as_dict(specialized.get("meta"))
                    payload = _as_dict(meta.get(_SPECIALIZATION_META_KEY))
                    entries.append(
                        {
                            "export_name": _safe_name(specialized.get("name")),
                            "type_args": list(_as_list(payload.get("type_args"))),
                        }
                    )
        module_doc["body"] = new_body


def materialize_runtime_template_specializations(
    program: LinkedProgram,
) -> tuple[LinkedProgram, dict[str, object]]:
    materializer = _TemplateMaterializer(program)
    return materializer.materialize()


__all__ = [
    "materialize_runtime_template_specializations",
]

"""east1 → east2 resolver: 型解決 + 正規化 (Python 固有 → 言語非依存).

責務:
  - 型注釈の正規化 (int→int64, float→float64 等)
  - 全式の resolved_type 確定
  - borrow_kind の判定
  - cast 挿入 (数値昇格等)
  - built-in → py_* ノード変換
  - semantic_tag / runtime_module_id / runtime_symbol 付与
  - range() → ForRange 変換
  - arg_usage / arg_type_exprs / return_type_expr 生成
  - schema_version / dispatch_mode 付与

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytra.std import json
from pytra.std import os_path as path
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from toolchain.common.jv import deep_copy_json

from toolchain.resolve.py.type_norm import (
    normalize_type,
    make_type_expr,
    is_numeric,
    is_int_type,
    is_float_type,
    extract_base_type,
    extract_type_args,
)
from toolchain.resolve.py.builtin_registry import (
    BuiltinRegistry,
    load_builtin_registry,
    FuncSig,
    ClassSig,
    ExternV2,
    VarSig,
)
from toolchain.resolve.py.normalize_order import normalize_field_order

_BUILTIN_TYPE_OBJECT_NAMES: set[str] = {
    "int",
    "float",
    "bool",
    "str",
    "object",
    "bytes",
    "bytearray",
    "list",
    "dict",
    "set",
    "tuple",
}

_BUILTIN_EXCEPTION_TYPE_NAMES: set[str] = {
    "PytraError",
    "BaseException",
    "Exception",
    "RuntimeError",
    "ValueError",
    "TypeError",
    "KeyError",
    "IndexError",
    "NameError",
    "FileNotFoundError",
    "PermissionError",
    "NotImplementedError",
    "OverflowError",
}

_BUILTIN_EXCEPTION_MODULE_ID = "pytra.built_in.error"


def _jv_obj(value: JsonVal) -> dict[str, JsonVal]:
    obj = json.JsonValue(value).as_obj()
    if obj is None:
        empty: dict[str, JsonVal] = {}
        return empty
    return obj.raw


def _jv_str(value: JsonVal) -> str:
    raw = json.JsonValue(value).as_str()
    if raw is None:
        return ""
    return "" + raw


def _jv_arr(value: JsonVal) -> list[JsonVal]:
    arr = json.JsonValue(value).as_arr()
    if arr is None:
        empty: list[JsonVal] = []
        return empty
    return arr.raw


def _dict_get_obj(obj: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    if key not in obj:
        empty: dict[str, JsonVal] = {}
        return empty
    return _jv_obj(obj[key])


def _dict_get_str(obj: dict[str, JsonVal], key: str) -> str:
    if key not in obj:
        return ""
    return _jv_str(obj[key])


def _dict_get_arr(obj: dict[str, JsonVal], key: str) -> list[JsonVal]:
    if key not in obj:
        empty: list[JsonVal] = []
        return empty
    return _jv_arr(obj[key])


def _json_str_list(values: list[str]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for value in values:
        out.append(value)
    return out


def _json_obj_list(values: list[dict[str, JsonVal]]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for value in values:
        out.append(value)
    return out


def _json_str_dict(values: dict[str, str]) -> dict[str, JsonVal]:
    out: dict[str, JsonVal] = {}
    for key, value in values.items():
        out[key] = value
    return out


def _path_parent(base: Path) -> Path:
    parent_text: str = path.dirname(str(base))
    if parent_text == "":
        parent_text = "."
    return Path(parent_text)


def _repo_root_from_cwd() -> Path:
    cur = Path(".").resolve()
    while True:
        if cur.joinpath("src").joinpath("pytra-cli.py").exists():
            return cur
        parent = _path_parent(cur)
        if str(parent) == str(cur):
            return Path(".").resolve()
        cur = parent


@dataclass
class ResolveResult:
    """resolve の結果。"""
    east2_doc: dict[str, JsonVal]
    source_path: str


@dataclass
class Scope:
    """Variable type environment."""
    vars: dict[str, str] = field(default_factory=dict)
    lambda_vars: dict[str, dict[str, JsonVal]] = field(default_factory=dict)

    def lookup(self, name: str) -> str:
        v: str = self.vars.get(name, "")
        if v != "":
            return v
        return "unknown"

    def define(self, name: str, typ: str) -> None:
        self.vars[name] = typ

    def bind_lambda(self, name: str, expr: dict[str, JsonVal]) -> None:
        self.lambda_vars[name] = expr

    def clear_lambda(self, name: str) -> None:
        if name in self.lambda_vars:
            self.lambda_vars.pop(name)

    def lookup_lambda(self, name: str) -> dict[str, JsonVal] | None:
        expr = self.lambda_vars.get(name)
        if expr is not None:
            return expr
        return None

    def child(self) -> Scope:
        child_scope = Scope()
        for name, typ in self.vars.items():
            child_scope.vars[name] = typ
        for name, expr in self.lambda_vars.items():
            child_scope.lambda_vars[name] = expr
        return child_scope


@dataclass
class ResolveContext:
    """Resolution state for a single module."""
    registry: BuiltinRegistry
    scope: Scope
    # Import info
    import_symbols: dict[str, dict[str, str]] = field(default_factory=dict)  # local→{module, name}
    import_modules: dict[str, str] = field(default_factory=dict)  # local→module_id
    # Functions defined in this module
    module_functions: dict[str, FuncSig] = field(default_factory=dict)
    # Classes defined in this module
    module_classes: dict[str, ClassSig] = field(default_factory=dict)
    # Module-local type aliases (PEP 695 style), expanded during resolve
    type_aliases: dict[str, str] = field(default_factory=dict)
    # Tracked implicit builtin modules
    used_builtin_modules: set[str] = field(default_factory=set)
    # Current function parameters (for borrow_kind: readonly_ref)
    current_params: set[str] = field(default_factory=set)
    # Whether we're inside a class body
    in_class: bool = False
    # Current class name while resolving methods
    current_class: str = ""
    # Current function/method name while resolving body
    current_function: str = ""
    # Source file path
    source_file: str = ""
    def load_runtime_index(self) -> dict[str, JsonVal]:
        try:
            idx_path: Path = _repo_root_from_cwd().joinpath("tools").joinpath("runtime_symbol_index.json")
            if idx_path.exists():
                text: str = idx_path.read_text(encoding="utf-8")
                raw: JsonVal = json.loads(text).raw
                return _jv_obj(raw)
        except Exception:
            pass
        empty: dict[str, JsonVal] = {}
        return empty

    def lookup_runtime_module_group(self, module_id: str) -> str:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods: dict[str, JsonVal] = _dict_get_obj(idx, "modules")
        mod: dict[str, JsonVal] = _dict_get_obj(mods, module_id)
        return _dict_get_str(mod, "runtime_group")

    def lookup_runtime_symbol_doc(self, module_id: str, symbol: str) -> dict[str, JsonVal]:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods: dict[str, JsonVal] = _dict_get_obj(idx, "modules")
        mod: dict[str, JsonVal] = _dict_get_obj(mods, module_id)
        syms: dict[str, JsonVal] = _dict_get_obj(mod, "symbols")
        sym: dict[str, JsonVal] = _dict_get_obj(syms, symbol)
        return sym

    def lookup_adapter_kind(self, module_id: str, symbol: str) -> str:
        doc: dict[str, JsonVal] = self.lookup_runtime_symbol_doc(module_id, symbol)
        return _dict_get_str(doc, "call_adapter_kind")

    def runtime_module_exists(self, module_id: str) -> bool:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods: dict[str, JsonVal] = _dict_get_obj(idx, "modules")
        return module_id in mods

    def canonical_module_id(self, module_id: str) -> str:
        mod: str = module_id.strip()
        if mod.startswith("pytra.") or mod.startswith("toolchain."):
            return mod
        if "." not in mod and mod != "":
            candidate: str = "pytra.std." + mod
            if self.runtime_module_exists(candidate):
                return candidate
        return mod

    # Renamed symbols mapping (original_name → name)
    renamed_symbols: dict[str, str] = field(default_factory=dict)

    def lookup_function(self, name: str) -> FuncSig | None:
        """Look up function: module-local first (with rename), then builtins."""
        local: FuncSig | None = self.module_functions.get(name)
        if local is not None:
            return local
        # Check renamed symbols
        renamed: str = self.renamed_symbols.get(name, "")
        if renamed != "":
            local2: FuncSig | None = self.module_functions.get(renamed)
            if local2 is not None:
                return local2
        return self.registry.lookup_function(name)

    def lookup_local_function(self, name: str) -> FuncSig | None:
        """Look up only module-local functions, excluding registry builtins."""
        local: FuncSig | None = self.module_functions.get(name)
        if local is not None:
            return local
        renamed: str = self.renamed_symbols.get(name, "")
        if renamed != "":
            return self.module_functions.get(renamed)
        return None

    def lookup_class(self, name: str) -> ClassSig | None:
        """Look up class: module-local first, then builtins."""
        local: ClassSig | None = self.module_classes.get(name)
        if local is not None:
            return local
        return self.registry.classes.get(name)

    def lookup_local_class(self, name: str) -> ClassSig | None:
        """Look up only module-local classes, excluding registry classes."""
        return self.module_classes.get(name)


def _ctx_normalize_type(raw: str, ctx: ResolveContext) -> str:
    return "" + normalize_type(raw, ctx.type_aliases)


def _ctx_make_type_expr(type_str: str, ctx: ResolveContext) -> dict[str, JsonVal]:
    return make_type_expr(_ctx_normalize_type(type_str, ctx))


def _is_unknown_like_type(type_str: str) -> bool:
    return type_str == "" or type_str == "unknown"


def _make_callable_type(param_types: list[str], return_type: str) -> str:
    params: list[str] = []
    for param in param_types:
        p: str = param.strip()
        params.append(p if p != "" else "unknown")
    ret: str = return_type.strip()
    if ret == "":
        ret = "unknown"
    if len(params) == 0 and ret == "unknown":
        return "callable[unknown]"
    return "callable[[" + ",".join(params) + "]," + ret + "]"


def _parse_callable_signature(type_str: str, ctx: ResolveContext) -> tuple[list[str], str]:
    t: str = _ctx_normalize_type(type_str, ctx)
    if not t.startswith("callable[") or not t.endswith("]"):
        empty_params: list[str] = []
        return empty_params, "unknown"
    inner: str = t[len("callable["):-1].strip()
    if inner == "":
        empty_params2: list[str] = []
        return empty_params2, "unknown"
    if inner.startswith("["):
        depth: int = 0
        close_idx: int = -1
        i: int = 0
        while i < len(inner):
            ch: str = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
            i += 1
        if close_idx >= 0 and close_idx + 1 < len(inner) and inner[close_idx + 1] == ",":
            params_text: str = inner[1:close_idx].strip()
            return_text: str = inner[close_idx + 2:].strip()
            params: list[str] = []
            if params_text != "":
                params = extract_type_args("tuple[" + params_text + "]")
            normalized_params: list[str] = []
            for param in params:
                normalized_params.append("" + normalize_type(param, ctx.type_aliases))
            return normalized_params, _ctx_normalize_type(return_text, ctx)
    arrow_idx: int = inner.find("->")
    if arrow_idx >= 0:
        params_text2: str = inner[:arrow_idx].strip()
        return_text2: str = inner[arrow_idx + 2:].strip()
        params2: list[str] = []
        if params_text2 != "":
            for part in params_text2.split(","):
                part_text: str = part.strip()
                if part_text != "":
                    params2.append("" + normalize_type(part_text, ctx.type_aliases))
        return params2, _ctx_normalize_type(return_text2, ctx)
    empty_params3: list[str] = []
    return empty_params3, _ctx_normalize_type(inner, ctx)


def _lookup_any_class(name: str, ctx: ResolveContext) -> ClassSig | None:
    local: ClassSig | None = ctx.module_classes.get(name)
    if local is not None:
        return local
    builtin_cls: ClassSig | None = ctx.registry.classes.get(name)
    if builtin_cls is not None:
        return builtin_cls
    for mod in ctx.registry.stdlib_modules.values():
        std_cls: ClassSig | None = mod.classes.get(name)
        if std_cls is not None:
            return std_cls
    return None


def _iter_class_hierarchy(name: str, ctx: ResolveContext) -> list[str]:
    out: list[str] = []
    pending: list[str] = []
    pending.append("" + extract_base_type(name))
    seen: set[str] = set()
    while len(pending) > 0:
        cur: str = "" + extract_base_type(pending.pop(0))
        if cur == "" or cur in seen:
            continue
        seen.add(cur)
        cls_sig: ClassSig | None = _lookup_any_class(cur, ctx)
        if cls_sig is None:
            continue
        out.append(cur)
        for base in cls_sig.bases:
            if base != "":
                pending.append(base)
    return out


def _resolve_owner_base_type(value: dict[str, JsonVal], receiver_type: str, ctx: ResolveContext) -> str:
    owner_base: str = "" + extract_base_type(receiver_type)
    if owner_base != "type":
        return owner_base
    type_object_of: str = _dict_get_str(value, "type_object_of")
    if type_object_of != "":
        return "" + extract_base_type(type_object_of)
    if _dict_get_str(value, "kind") == "Name":
        name: str = _dict_get_str(value, "id")
        if name != "":
            imp: dict[str, str] = ctx.import_symbols.get(name, {})
            module_id = imp.get("module", "")
            export_name = imp.get("name", "")
            if module_id != "" and export_name != "" and ctx.registry.lookup_stdlib_class(module_id, export_name) is not None:
                return export_name
            if ctx.lookup_class(name) is not None:
                return name
    return ""


def _resolve_alias_direct_deps(type_text: str, alias_names: set[str]) -> list[str]:
    deps: list[str] = []
    token = ""
    for ch in type_text:
        if ch.isalnum() or ch == "_" or ch == ".":
            token += ch
            continue
        if token != "":
            if token in alias_names and token not in deps:
                deps.append(token)
            token = ""
    if token != "" and token in alias_names and token not in deps:
        deps.append(token)
    return deps


def _resolve_validate_type_alias_cycles(type_aliases: dict[str, str]) -> None:
    alias_names: set[str] = set()
    for alias_name in type_aliases.keys():
        if alias_name != "":
            alias_names.add(alias_name)
    deps_map: dict[str, list[str]] = {}
    for alias_name in alias_names:
        alias_value: str = type_aliases.get(alias_name, "")
        deps_map[alias_name] = _resolve_alias_direct_deps(alias_value, alias_names)

    visiting: set[str] = set()
    visited: set[str] = set()

    def _walk(alias_name: str, stack: list[str]) -> None:
        if alias_name in visiting:
            cycle_start = 0
            while cycle_start < len(stack) and stack[cycle_start] != alias_name:
                cycle_start += 1
            cycle: list[str] = []
            cycle_index = cycle_start
            while cycle_index < len(stack):
                cycle.append(stack[cycle_index])
                cycle_index += 1
            cycle.append(alias_name)
            uniq: list[str] = []
            for item in cycle:
                if item not in uniq:
                    uniq.append(item)
            if len(uniq) >= 2:
                raise ValueError("mutually recursive type aliases are not supported: " + " -> ".join(cycle))
            return
        if alias_name in visited:
            return
        visiting.add(alias_name)
        next_stack = list(stack)
        next_stack.append(alias_name)
        for dep in deps_map.get(alias_name, []):
            _walk(dep, next_stack)
        visiting.remove(alias_name)
        visited.add(alias_name)

    for alias_name in alias_names:
        empty_stack: list[str] = []
        _walk(alias_name, empty_stack)


def _lookup_method_sig(owner_base: str, attr: str, ctx: ResolveContext) -> tuple[ClassSig | None, FuncSig | None]:
    for class_name in _iter_class_hierarchy(owner_base, ctx):
        cls_sig: ClassSig | None = _lookup_any_class(class_name, ctx)
        if cls_sig is None:
            continue
        msig: FuncSig | None = cls_sig.methods.get(attr)
        if msig is not None:
            return cls_sig, msig
    return None, None


def _attach_stdlib_method_runtime_metadata(
    expr: dict[str, JsonVal],
    cls_sig: ClassSig,
    method_sig: FuncSig,
    owner_base: str,
    attr: str,
    ctx: ResolveContext,
) -> None:
    module_id: str = ""
    for registry_module_id, registry_module in ctx.registry.stdlib_modules.items():
        for candidate_cls in registry_module.classes.values():
            if candidate_cls.name == cls_sig.name:
                module_id = registry_module_id
                break
        if module_id != "":
            break
    if module_id == "":
        return
    method_extern_info: ExternV2 | None = method_sig.extern_v2
    runtime_call_name: str = owner_base + "." + attr
    runtime_symbol_name: str = runtime_call_name
    runtime_module_id: str = module_id
    if method_extern_info is not None:
        if method_extern_info.symbol != "":
            runtime_call_name = method_extern_info.symbol
            runtime_symbol_name = method_extern_info.symbol
        if method_extern_info.module != "":
            runtime_module_id = method_extern_info.module
    expr["resolved_runtime_call"] = runtime_call_name
    expr["resolved_runtime_source"] = "stdlib_method"
    expr["runtime_call"] = runtime_call_name
    expr["runtime_module_id"] = runtime_module_id
    expr["runtime_symbol"] = runtime_symbol_name
    runtime_idx: dict[str, JsonVal] = ctx.load_runtime_index()
    runtime_mods: dict[str, JsonVal] = _dict_get_obj(runtime_idx, "modules")
    runtime_mod: dict[str, JsonVal] = _dict_get_obj(runtime_mods, runtime_module_id)
    runtime_symbols: dict[str, JsonVal] = _dict_get_obj(runtime_mod, "symbols")
    adapter_doc: dict[str, JsonVal] = _dict_get_obj(runtime_symbols, runtime_symbol_name)
    adapter: str = _dict_get_str(adapter_doc, "call_adapter_kind")
    if adapter != "":
        expr["runtime_call_adapter_kind"] = adapter
    if method_extern_info is not None and method_extern_info.tag != "":
        expr["semantic_tag"] = method_extern_info.tag
    elif attr != "":
        expr["semantic_tag"] = "stdlib.method." + attr


def _has_inherited_field(class_name: str, field_name: str, ctx: ResolveContext) -> bool:
    cls_sig: ClassSig | None = ctx.module_classes.get(class_name)
    if cls_sig is None:
        return False
    pending: list[str] = list(cls_sig.bases)
    seen: set[str] = {class_name}
    while len(pending) > 0:
        cur: str = "" + extract_base_type(pending.pop(0))
        if cur == "" or cur in seen:
            continue
        seen.add(cur)
        base_sig: ClassSig | None = _lookup_any_class(cur, ctx)
        if base_sig is None:
            continue
        if field_name in base_sig.fields:
            return True
        for base in base_sig.bases:
            if base != "":
                pending.append(base)
    return False


def _class_decorators(node: dict[str, JsonVal]) -> list[str]:
    decorators: list[str] = []
    for item in _dict_get_arr(node, "decorators"):
        item_text: str = _jv_str(item)
        if item_text != "":
            decorators.append(item_text)
    return decorators


def _parse_implements_decorator(decorator: str) -> list[str]:
    if not decorator.startswith("implements(") or not decorator.endswith(")"):
        empty_traits: list[str] = []
        return empty_traits
    inner = decorator[len("implements("):-1]
    out: list[str] = []
    for part in inner.split(","):
        trait_name = part.strip()
        if trait_name != "":
            out.append(trait_name)
    return out


def _trait_method_signature_tuple(sig: FuncSig) -> tuple[list[str], str]:
    params: list[str] = []
    idx = 0
    while idx < len(sig.arg_names):
        arg_name = sig.arg_names[idx]
        if arg_name != "self":
            params.append(sig.arg_types.get(arg_name, "unknown"))
        idx += 1
    return params, sig.return_type


def _build_trait_method_meta(trait_name: str, method_name: str) -> dict[str, JsonVal]:
    return {
        "schema_version": 1,
        "trait_name": trait_name,
        "method_name": method_name,
    }


def _collect_trait_methods(trait_name: str, ctx: ResolveContext) -> dict[str, list[FuncSig]]:
    out: dict[str, list[FuncSig]] = {}
    pending: list[str] = [trait_name]
    seen: set[str] = set()
    while len(pending) > 0:
        current = extract_base_type(pending.pop(0))
        if current == "" or current in seen:
            continue
        seen.add(current)
        trait_sig = _lookup_any_class(current, ctx)
        if trait_sig is None or not trait_sig.is_trait:
            continue
        for method_name, method_sig in trait_sig.methods.items():
            rows = out.get(method_name)
            if rows is None:
                rows = []
                out[method_name] = rows
            rows.append(method_sig)
        for base_name in trait_sig.bases:
            if base_name != "":
                pending.append(base_name)
    return out


def _resolve_trait_contracts(stmt: dict[str, JsonVal], class_name: str, ctx: ResolveContext) -> None:
    cls_sig = ctx.module_classes.get(class_name)
    if cls_sig is None:
        return
    decorators = _class_decorators(stmt)
    is_trait = cls_sig.is_trait or ("trait" in decorators)
    implements_traits: list[str] = []
    for decorator in decorators:
        parsed_traits = _parse_implements_decorator(decorator)
        for trait_name in parsed_traits:
            implements_traits.append(trait_name)

    meta: dict[str, JsonVal] = _dict_get_obj(stmt, "meta")
    stmt["meta"] = meta

    if is_trait:
        if len(cls_sig.fields) > 0:
            raise RuntimeError("semantic_conflict: trait may not declare fields: " + class_name)
        extends_traits: list[str] = []
        for base_name in cls_sig.bases:
            trait_base = extract_base_type(base_name)
            if trait_base == "":
                continue
            base_sig = _lookup_any_class(trait_base, ctx)
            if base_sig is None or not base_sig.is_trait:
                raise RuntimeError("semantic_conflict: trait may only extend traits: " + class_name + " -> " + trait_base)
            extends_traits.append(trait_base)
        methods_meta: list[JsonVal] = []
        body = _dict_get_arr(stmt, "body")
        if len(body) > 0:
            for item_val in body:
                item = _jv_obj(item_val)
                if len(item) == 0:
                    continue
                item_kind = _dict_get_str(item, "kind")
                if item_kind == "FunctionDef":
                    method_name = _dict_get_str(item, "name")
                    if method_name == "":
                        continue
                    method_body = _dict_get_arr(item, "body")
                    if len(method_body) > 0:
                        raise RuntimeError("unsupported_syntax: trait method body must be ellipsis-only: " + class_name + "." + method_name)
                    method_sig = cls_sig.methods.get(method_name)
                    if method_sig is None:
                        continue
                    params, ret = _trait_method_signature_tuple(method_sig)
                    method_meta: dict[str, JsonVal] = {}
                    method_meta["name"] = method_name
                    method_meta["args"] = _json_str_list(list(method_sig.arg_names))
                    method_meta["param_types"] = _json_str_list(params)
                    method_meta["return_type"] = ret
                    methods_meta.append(method_meta)
                elif item_kind in ("Expr", "Pass"):
                    continue
                else:
                    raise RuntimeError("unsupported_syntax: trait body only allows method signatures: " + class_name)
        trait_meta: dict[str, JsonVal] = {}
        trait_meta["schema_version"] = 1
        trait_meta["methods"] = methods_meta
        trait_meta["extends_traits"] = _json_str_list(extends_traits)
        meta["trait_v1"] = trait_meta
        return

    if len(implements_traits) == 0:
        return

    method_impl_map: dict[str, list[dict[str, JsonVal]]] = {}
    idx_trait = 0
    while idx_trait < len(implements_traits):
        trait_name = "" + extract_base_type(implements_traits[idx_trait])
        idx_trait += 1
        if trait_name == "":
            continue
        trait_sig = _lookup_any_class(trait_name, ctx)
        if trait_sig is None or not trait_sig.is_trait:
            raise RuntimeError("semantic_conflict: implements target must be a trait: " + class_name + " -> " + trait_name)
        trait_methods = _collect_trait_methods(trait_name, ctx)
        for method_name, trait_rows in trait_methods.items():
            impl_sig = cls_sig.methods.get(method_name)
            if impl_sig is None:
                raise RuntimeError("semantic_conflict: missing trait method implementation: " + class_name + "." + method_name + " for " + trait_name)
            impl_sig_tuple = _trait_method_signature_tuple(impl_sig)
            matched = False
            for trait_method_sig in trait_rows:
                if impl_sig_tuple == _trait_method_signature_tuple(trait_method_sig):
                    matched = True
                    break
            if not matched:
                raise RuntimeError("semantic_conflict: trait signature mismatch: " + class_name + "." + method_name + " for " + trait_name)
            rows = method_impl_map.get(method_name)
            if rows is None:
                rows = []
                method_impl_map[method_name] = rows
            rows.append(_build_trait_method_meta(trait_name, method_name))

    body2 = _dict_get_arr(stmt, "body")
    if len(body2) > 0:
        for item2_val in body2:
            item2 = _jv_obj(item2_val)
            if len(item2) == 0 or _dict_get_str(item2, "kind") != "FunctionDef":
                continue
            method_name2 = _dict_get_str(item2, "name")
            impl_rows = method_impl_map.get(method_name2)
            if impl_rows is None or len(impl_rows) == 0:
                continue
            item_meta: dict[str, JsonVal] = _dict_get_obj(item2, "meta")
            item2["meta"] = item_meta
            if len(impl_rows) == 1:
                item_meta["trait_impl_v1"] = impl_rows[0]
            else:
                item_meta["trait_impl_v1"] = _json_obj_list(impl_rows)

    implements_meta: dict[str, JsonVal] = {}
    implements_meta["schema_version"] = 1
    implements_meta["traits"] = _json_str_list(implements_traits)
    meta["implements_v1"] = implements_meta


def _default_collection_hint(param_type: str) -> str:
    t: str = param_type.strip()
    if t.endswith(" | None"):
        t = t[:-7].strip()
    elif t.endswith("|None"):
        t = t[:-6].strip()
    if t.startswith("list[") or t.startswith("dict[") or t.startswith("set["):
        return t
    return ""


def _tuple_assign_element_types(
    tuple_target: dict[str, JsonVal],
    value_type: str,
    ctx: ResolveContext,
) -> list[str]:
    candidate_types: list[str] = []
    norm_value_type = _ctx_normalize_type(value_type, ctx)
    if norm_value_type != "":
        candidate_types.append(norm_value_type)
        if norm_value_type.endswith(" | None"):
            candidate_types.append(norm_value_type[:-7].strip())
        elif norm_value_type.endswith("|None"):
            candidate_types.append(norm_value_type[:-6].strip())

    target_type = _dict_get_str(tuple_target, "resolved_type")
    if target_type != "":
        candidate_types.append(_ctx_normalize_type(target_type, ctx))

    for candidate in candidate_types:
        if candidate.startswith("tuple[") and candidate.endswith("]"):
            return extract_type_args(candidate)

    elems = _dict_get_arr(tuple_target, "elements")
    if len(elems) == 0:
        empty: list[str] = []
        return empty
    elem_types: list[str] = []
    any_known = False
    for elem_val in elems:
        elem = _jv_obj(elem_val)
        elem_type = "unknown"
        if _dict_get_str(elem, "kind") == "Name":
            elem_name = _dict_get_str(elem, "id")
            if elem_name != "":
                existing = ctx.scope.lookup(elem_name)
                if existing != "unknown":
                    elem_type = existing
        if elem_type == "unknown":
            elem_resolved = _dict_get_str(elem, "resolved_type")
            if elem_resolved != "":
                elem_type = elem_resolved
        if elem_type != "unknown":
            any_known = True
        elem_types.append(elem_type)
    if any_known:
        return elem_types
    empty2: list[str] = []
    return empty2

def _apply_default_annotation_type(default_node: dict[str, JsonVal], param_type: str, ctx: ResolveContext) -> None:
    hinted_type: str = _default_collection_hint(_ctx_normalize_type(param_type, ctx))
    if hinted_type == "":
        return
    kind: str = _dict_get_str(default_node, "kind")
    current: str = _dict_get_str(default_node, "resolved_type")
    if kind == "List" and hinted_type.startswith("list[") and current in ("", "unknown", "list[unknown]"):
        default_node["resolved_type"] = hinted_type
        return
    if kind == "Dict" and hinted_type.startswith("dict[") and current in ("", "unknown", "dict[unknown,unknown]"):
        default_node["resolved_type"] = hinted_type
        return
    if kind == "Set" and hinted_type.startswith("set[") and current in ("", "unknown", "set[unknown]"):
        default_node["resolved_type"] = hinted_type


def _apply_collection_type_hint(node: dict[str, JsonVal], target_type: str, ctx: ResolveContext) -> None:
    hinted_type: str = _default_collection_hint(_ctx_normalize_type(target_type, ctx))
    if hinted_type == "":
        return
    kind: str = _dict_get_str(node, "kind")
    current: str = _dict_get_str(node, "resolved_type")
    if kind == "Call":
        call_rc = _dict_get_str(node, "runtime_call")
        if call_rc == "list_ctor" and hinted_type.startswith("list[") and current in ("", "unknown", "list[unknown]"):
            node["resolved_type"] = hinted_type
            return
        if call_rc == "set_ctor" and hinted_type.startswith("set[") and current in ("", "unknown", "set[unknown]"):
            node["resolved_type"] = hinted_type
            return
    if kind == "List" and hinted_type.startswith("list[") and current in ("", "unknown", "list[unknown]"):
        node["resolved_type"] = hinted_type
        return
    if kind == "Dict" and hinted_type.startswith("dict[") and current in ("", "unknown", "dict[unknown,unknown]"):
        node["resolved_type"] = hinted_type
        return
    if kind == "Set" and hinted_type.startswith("set[") and current in ("", "unknown", "set[unknown]"):
        node["resolved_type"] = hinted_type




def _drop_first_str(values: list[str]) -> list[str]:
    out: list[str] = []
    idx = 1
    while idx < len(values):
        out.append(values[idx])
        idx += 1
    return out

def _apply_call_arg_hints(
    expr: dict[str, JsonVal],
    arg_names: list[str],
    arg_types: dict[str, str],
    ctx: ResolveContext,
) -> None:
    generic_param_names: set[str] = {"T", "K", "V", "KT", "VT", "R", "P"}
    args = _dict_get_arr(expr, "args")
    idx = 0
    while idx < len(args):
        arg = _jv_obj(args[idx])
        if len(arg) == 0:
            idx += 1
            continue
        if idx >= len(arg_names):
            idx += 1
            continue
        param_name: str = arg_names[idx]
        hinted_type: str = arg_types.get(param_name, "")
        if hinted_type != "":
            _apply_collection_type_hint(arg, hinted_type, ctx)
            hinted_type_norm = _ctx_normalize_type(hinted_type, ctx)
            if hinted_type_norm not in ("", "unknown") and hinted_type_norm not in generic_param_names:
                arg["call_arg_type"] = hinted_type_norm
        idx += 1
    keywords = _dict_get_arr(expr, "keywords")
    for kw_val in keywords:
        kw = _jv_obj(kw_val)
        if len(kw) == 0:
            continue
        kw_name = _dict_get_str(kw, "arg")
        kw_value = _dict_get_obj(kw, "value")
        if kw_name == "" or len(kw_value) == 0:
            continue
        hinted_type2: str = arg_types.get(kw_name, "")
        if hinted_type2 != "":
            _apply_collection_type_hint(kw_value, hinted_type2, ctx)
            hinted_type2_norm = _ctx_normalize_type(hinted_type2, ctx)
            if hinted_type2_norm not in ("", "unknown") and hinted_type2_norm not in generic_param_names:
                kw_value["call_arg_type"] = hinted_type2_norm

def _lambda_arg_names(expr: dict[str, JsonVal]) -> list[str]:
    arg_order: list[str] = []
    arg_order_raw = _dict_get_arr(expr, "arg_order")
    for item in arg_order_raw:
        item_text = _jv_str(item)
        if item_text != "":
            arg_order.append(item_text)
    if len(arg_order) > 0:
        return arg_order
    args_list = _dict_get_arr(expr, "args")
    for arg_val in args_list:
        arg = _jv_obj(arg_val)
        name = _dict_get_str(arg, "arg")
        if name != "":
            arg_order.append(name)
    return arg_order

def _lambda_arg_types(expr: dict[str, JsonVal], ctx: ResolveContext, arg_order: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    arg_types_raw = _dict_get_obj(expr, "arg_types")
    for name, value in arg_types_raw.items():
        value_text = _jv_str(value)
        if value_text != "":
            result[name] = _ctx_normalize_type(value_text, ctx)
    args_list = _dict_get_arr(expr, "args")
    for arg_val in args_list:
        arg = _jv_obj(arg_val)
        if len(arg) == 0:
            continue
        name2 = _dict_get_str(arg, "arg")
        if name2 == "":
            continue
        resolved_type = _dict_get_str(arg, "resolved_type")
        if resolved_type != "" and not _is_unknown_like_type(resolved_type):
            result[name2] = _ctx_normalize_type(resolved_type, ctx)
    for name3 in arg_order:
        if name3 not in result:
            result[name3] = "unknown"
    return result

def _resolve_lambda_defaults(
    expr: dict[str, JsonVal],
    ctx: ResolveContext,
    arg_types: dict[str, str],
) -> None:
    args_list = _dict_get_arr(expr, "args")
    if len(args_list) == 0:
        return
    for arg_val in args_list:
        arg = _jv_obj(arg_val)
        if len(arg) == 0:
            continue
        arg_name = _dict_get_str(arg, "arg")
        default_node = _dict_get_obj(arg, "default")
        if arg_name == "" or len(default_node) == 0:
            continue
        default_type = _resolve_expr(default_node, ctx)
        current = arg_types.get(arg_name, "")
        if _is_unknown_like_type(current) and not _is_unknown_like_type(default_type):
            arg_types[arg_name] = default_type

def _merge_refined_type(current: str, hinted: str) -> str:
    if _is_unknown_like_type(hinted):
        return current
    if _is_unknown_like_type(current):
        return hinted
    if current == hinted:
        return current
    if is_numeric(current) and is_numeric(hinted):
        return _binop_result_type(current, hinted, "Add")
    return current


def _merge_literal_type(current: str, new_type: str) -> str:
    if _is_unknown_like_type(current):
        return new_type
    if _is_unknown_like_type(new_type):
        return current
    if current == new_type:
        return current
    if current == "None":
        if new_type.endswith(" | None") or new_type.endswith("|None"):
            return new_type
        return new_type + " | None"
    if new_type == "None":
        if current.endswith(" | None") or current.endswith("|None"):
            return current
        return current + " | None"
    current_base = extract_base_type(current)
    new_base = extract_base_type(new_type)
    if current_base == new_base and current_base != "":
        current_has_args = "[" in current and current.endswith("]")
        new_has_args = "[" in new_type and new_type.endswith("]")
        if not current_has_args and new_has_args:
            return new_type
        if current_has_args and not new_has_args:
            return current
        if current.startswith("set[") and new_type.startswith("set["):
            current_inner = current[4:-1]
            new_inner = new_type[4:-1]
            return "set[" + _merge_literal_type(current_inner, new_inner) + "]"
        if current.startswith("list[") and new_type.startswith("list["):
            current_inner2 = current[5:-1]
            new_inner2 = new_type[5:-1]
            return "list[" + _merge_literal_type(current_inner2, new_inner2) + "]"
        if current.startswith("dict[") and new_type.startswith("dict["):
            current_args = extract_type_args(current)
            new_args = extract_type_args(new_type)
            if len(current_args) == 2 and len(new_args) == 2:
                merged_key = _merge_literal_type(current_args[0], new_args[0])
                merged_val = _merge_literal_type(current_args[1], new_args[1])
                return "dict[" + merged_key + "," + merged_val + "]"
    return current


def _split_union_type_parts(type_str: str) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    for ch in type_str:
        if ch == "[":
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
        if ch == "|" and depth == 0:
            part = "".join(cur).strip()
            if part != "":
                parts.append(part)
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _merge_ifexp_result_type(body_type: str, orelse_type: str) -> str:
    if _is_unknown_like_type(body_type) and orelse_type == "None":
        return "Any | None"
    if _is_unknown_like_type(orelse_type) and body_type == "None":
        return "Any | None"
    if _is_unknown_like_type(body_type):
        return orelse_type
    if _is_unknown_like_type(orelse_type):
        return body_type
    if body_type == orelse_type:
        return body_type

    merged_literal = _merge_literal_type(body_type, orelse_type)
    body_base = extract_base_type(body_type)
    orelse_base = extract_base_type(orelse_type)
    body_has_args = "[" in body_type and body_type.endswith("]")
    orelse_has_args = "[" in orelse_type and orelse_type.endswith("]")
    if body_base == orelse_base and body_base != "":
        if body_has_args != orelse_has_args:
            return merged_literal
        if merged_literal != body_type and merged_literal != orelse_type:
            return merged_literal

    merged_parts: list[str] = []
    seen: set[str] = set()
    pending_none = False
    for part in _split_union_type_parts(body_type) + _split_union_type_parts(orelse_type):
        if part == "None":
            pending_none = True
            continue
        if part not in seen:
            seen.add(part)
            merged_parts.append(part)
    if pending_none:
        merged_parts.append("None")
    if len(merged_parts) == 0:
        return "unknown"
    if len(merged_parts) == 1:
        return merged_parts[0]
    return " | ".join(merged_parts)




def _is_dynamic_supertype(type_str: str) -> bool:
    return type_str == "JsonVal" or type_str == "Any" or type_str == "Obj" or type_str == "object"


def _resolve_safe_str(value: JsonVal) -> str:
    return _jv_str(value).strip()


_RESOLVE_TYPE_GUARD_DEFAULTS: dict[str, str] = {
    "bool": "bool",
    "int": "int64",
    "float": "float64",
    "str": "str",
    "list": "list[JsonVal]",
    "dict": "dict[str,JsonVal]",
    "set": "set[JsonVal]",
    "tuple": "tuple[JsonVal]",
    "None": "None",
    "PYTRA_TID_NONE": "None",
    "PYTRA_TID_BOOL": "bool",
    "PYTRA_TID_INT": "int64",
    "PYTRA_TID_FLOAT": "float64",
    "PYTRA_TID_STR": "str",
    "PYTRA_TID_LIST": "list[JsonVal]",
    "PYTRA_TID_DICT": "dict[str,JsonVal]",
    "PYTRA_TID_SET": "set[JsonVal]",
    "PYTRA_TID_TUPLE": "tuple[JsonVal]",
}


def _resolve_split_union_members(type_name: str) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    for ch in type_name:
        if ch == "[":
            depth += 1
            cur.append(ch)
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur.append(ch)
        elif ch == "|" and depth == 0:
            part = "".join(cur).strip()
            if part != "":
                parts.append(part)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _resolve_type_matches_guard(type_name: str, guard_type: str) -> bool:
    norm = normalize_type(type_name)
    guard = normalize_type(guard_type)
    if norm == "" or norm == "unknown" or guard == "" or guard == "unknown":
        return False
    if guard == "None":
        return norm == "None"
    if guard == "bool":
        return norm == "bool"
    if guard in ("int", "int64"):
        return is_int_type(norm) or norm == "int"
    if guard in ("float", "float64"):
        return norm in ("float", "float32", "float64")
    if guard == "str":
        return norm == "str"
    if guard == "list":
        return norm == "list" or norm.startswith("list[")
    if guard == "dict":
        return norm == "dict" or norm.startswith("dict[")
    if guard == "set":
        return norm == "set" or norm.startswith("set[")
    if guard == "tuple":
        return norm == "tuple" or norm.startswith("tuple[")
    return norm == guard


def _resolve_matching_guard_members(source_type: str, expected_name: str) -> list[str]:
    src = "" + normalize_type(source_type)
    expected = "" + normalize_type(expected_name)
    if src in ("", "unknown") or expected in ("", "unknown"):
        empty: list[str] = []
        return empty
    guard_type = _RESOLVE_TYPE_GUARD_DEFAULTS.get(expected, expected)
    members = _resolve_split_union_members(src)
    if len(members) == 0:
        members.append(src)
    matches: list[str] = []
    for member in members:
        norm_member = "" + normalize_type(member)
        if _resolve_type_matches_guard(norm_member, guard_type):
            matches.append(norm_member)
    return matches


def _resolve_select_guard_target_type(source_type: str, expected_name: str) -> str:
    src = "" + normalize_type(source_type)
    expected = "" + normalize_type(expected_name)
    if expected == "" or expected == "unknown":
        return ""
    matches = _resolve_matching_guard_members(src, expected)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return " | ".join(matches)
    guard_type = _RESOLVE_TYPE_GUARD_DEFAULTS.get(expected, expected)
    if src in ("", "unknown") or _is_dynamic_supertype(src):
        return "" + normalize_type(guard_type)
    if _resolve_type_matches_guard(src, guard_type):
        return "" + src
    return ""


def _resolve_isinstance_guard_info(expr: JsonVal) -> tuple[JsonVal, str]:
    nd = _jv_obj(expr)
    if len(nd) == 0:
        return None, ""
    kind = _dict_get_str(nd, "kind")
    if kind == "IsInstance":
        value: JsonVal = None
        if "value" in nd:
            value = nd["value"]
        return value, _dict_get_str(nd, "expected_type_name").strip()
    if kind == "Call" and _dict_get_str(nd, "predicate_kind") == "isinstance":
        args = _dict_get_arr(nd, "args")
        if len(args) >= 2:
            expected = _jv_obj(args[1])
            expected_name = ""
            if len(expected) > 0:
                expected_name = _dict_get_str(expected, "id")
                if expected_name == "":
                    expected_name = _dict_get_str(expected, "repr")
            return args[0], expected_name
    return None, ""


def _resolve_guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    nd = _jv_obj(expr)
    if len(nd) == 0:
        empty: dict[str, str] = {}
        return empty
    kind = _dict_get_str(nd, "kind")
    guarded, expected_name = _resolve_isinstance_guard_info(expr)
    guarded_obj = _jv_obj(guarded)
    if len(guarded_obj) > 0 and _dict_get_str(guarded_obj, "kind") == "Name":
        name = _dict_get_str(guarded_obj, "id")
        if name != "":
            target = _resolve_select_guard_target_type(_dict_get_str(guarded_obj, "resolved_type"), expected_name)
            if target != "" and target != "unknown":
                one: dict[str, str] = {}
                one[name] = target
                return one
    if kind == "Compare":
        left = _dict_get_obj(nd, "left")
        comparators = _dict_get_arr(nd, "comparators")
        ops = _dict_get_arr(nd, "ops")
        if len(left) > 0 and _dict_get_str(left, "kind") == "Name" and len(comparators) == 1 and len(ops) == 1:
            comp0 = _jv_obj(comparators[0])
            comp_is_none = False
            if len(comp0) > 0 and _dict_get_str(comp0, "kind") == "Constant" and "value" in comp0 and comp0["value"] is None:
                comp_is_none = True
            if comp_is_none:
                name2 = _dict_get_str(left, "id")
                src_type = _dict_get_str(left, "resolved_type")
                if name2 == "" or src_type == "":
                    empty2: dict[str, str] = {}
                    return empty2
                members: list[str] = []
                for member in _resolve_split_union_members(src_type):
                    norm = "" + normalize_type(member)
                    if norm != "None":
                        members.append(member)
                op = _jv_str(ops[0])
                if op == "IsNot":
                    if len(members) == 0:
                        empty3: dict[str, str] = {}
                        return empty3
                    narrowed = ""
                    if len(members) == 1:
                        narrowed = "" + normalize_type(members[0])
                    else:
                        normalized_members: list[str] = []
                        for member2 in members:
                            normalized_members.append("" + normalize_type(member2))
                        narrowed = " | ".join(normalized_members)
                    one2: dict[str, str] = {}
                    one2[name2] = narrowed
                    return one2
        empty4: dict[str, str] = {}
        return empty4
    if kind == "UnaryOp" and _dict_get_str(nd, "op") == "Not":
        if "operand" in nd:
            return _resolve_invert_guard_narrowing_from_expr(nd["operand"])
        empty5: dict[str, str] = {}
        return empty5
    if kind == "BoolOp" and _dict_get_str(nd, "op") == "And":
        merged: dict[str, str] = {}
        values = _dict_get_arr(nd, "values")
        for value in values:
            child = _resolve_guard_narrowing_from_expr(value)
            for name3, target_type in child.items():
                cur = merged.get(name3, "")
                if cur == "" or cur == target_type:
                    merged[name3] = target_type
                else:
                    if name3 in merged:
                        merged.pop(name3)
        return merged
    empty6: dict[str, str] = {}
    return empty6


def _resolve_invert_guard_narrowing_from_expr(expr: JsonVal) -> dict[str, str]:
    nd = _jv_obj(expr)
    if len(nd) == 0:
        empty: dict[str, str] = {}
        return empty
    kind = _dict_get_str(nd, "kind")
    guarded, expected_name = _resolve_isinstance_guard_info(expr)
    guarded_obj = _jv_obj(guarded)
    if len(guarded_obj) > 0 and _dict_get_str(guarded_obj, "kind") == "Name":
        name0 = _dict_get_str(guarded_obj, "id")
        src_type0 = _dict_get_str(guarded_obj, "resolved_type")
        if name0 != "" and src_type0 != "":
            src_norm = "" + normalize_type(src_type0)
            members0 = _resolve_split_union_members(src_norm)
            if len(members0) == 0:
                members0.append(src_norm)
            matches0 = _resolve_matching_guard_members(src_norm, expected_name)
            remaining0: list[str] = []
            for member0 in members0:
                norm_member0 = "" + normalize_type(member0)
                if norm_member0 not in matches0:
                    remaining0.append(norm_member0)
            if len(remaining0) == 1:
                one0: dict[str, str] = {}
                one0[name0] = remaining0[0]
                return one0
            if len(remaining0) > 1:
                many0: dict[str, str] = {}
                many0[name0] = " | ".join(remaining0)
                return many0
            empty0: dict[str, str] = {}
            return empty0
    if kind == "UnaryOp" and _dict_get_str(nd, "op") == "Not":
        if "operand" in nd:
            return _resolve_guard_narrowing_from_expr(nd["operand"])
        empty1: dict[str, str] = {}
        return empty1
    if kind == "Compare":
        left = _dict_get_obj(nd, "left")
        comparators = _dict_get_arr(nd, "comparators")
        ops = _dict_get_arr(nd, "ops")
        if len(left) > 0 and _dict_get_str(left, "kind") == "Name" and len(comparators) == 1 and len(ops) == 1:
            comp0 = _jv_obj(comparators[0])
            comp_is_none = False
            if len(comp0) > 0 and _dict_get_str(comp0, "kind") == "Constant" and "value" in comp0 and comp0["value"] is None:
                comp_is_none = True
            if comp_is_none:
                name = _dict_get_str(left, "id")
                src_type = _dict_get_str(left, "resolved_type")
                if name == "" or src_type == "":
                    empty2: dict[str, str] = {}
                    return empty2
                members: list[str] = []
                for member in _resolve_split_union_members(src_type):
                    norm = "" + normalize_type(member)
                    if norm != "None":
                        members.append(member)
                if len(members) == 0:
                    empty3: dict[str, str] = {}
                    return empty3
                narrowed = members[0] if len(members) == 1 else " | ".join(members)
                if _jv_str(ops[0]) == "Is":
                    one: dict[str, str] = {}
                    one[name] = "" + normalize_type(narrowed)
                    return one
        empty4: dict[str, str] = {}
        return empty4
    if kind == "BoolOp" and _dict_get_str(nd, "op") == "Or":
        merged2: dict[str, str] = {}
        values2 = _dict_get_arr(nd, "values")
        for value2 in values2:
            child2 = _resolve_invert_guard_narrowing_from_expr(value2)
            for name2, target_type2 in child2.items():
                cur2 = merged2.get(name2, "")
                if cur2 == "" or cur2 == target_type2:
                    merged2[name2] = target_type2
                else:
                    if name2 in merged2:
                        merged2.pop(name2)
        return merged2
    empty5: dict[str, str] = {}
    return empty5

def _resolver_stmt_guarantees_exit(stmt: JsonVal) -> bool:
    nd = _jv_obj(stmt)
    if len(nd) == 0:
        return False
    kind = _dict_get_str(nd, "kind")
    if kind in ("Return", "Raise"):
        return True
    if kind == "Expr":
        value = _dict_get_obj(nd, "value")
        if len(value) > 0 and _dict_get_str(value, "kind") == "Name":
            name = _dict_get_str(value, "id")
            if name in ("continue", "break"):
                return True
    if kind == "If":
        body_ok = False
        orelse_ok = False
        if "body" in nd:
            body_ok = _resolver_block_guarantees_exit(nd["body"])
        if "orelse" in nd:
            orelse_ok = _resolver_block_guarantees_exit(nd["orelse"])
        return body_ok and orelse_ok
    return False


def _resolver_block_guarantees_exit(stmts: JsonVal) -> bool:
    stmt_list = _jv_arr(stmts)
    if len(stmt_list) == 0:
        return False
    return _resolver_stmt_guarantees_exit(stmt_list[-1])

def _resolve_stmt_list_with_narrowing(stmts: JsonVal, ctx: ResolveContext, narrowed: dict[str, str]) -> None:
    stmt_list = _jv_arr(stmts)
    if len(stmt_list) == 0:
        return
    saved: dict[str, tuple[bool, str]] = {}
    for name, typ in narrowed.items():
        if name == "" or typ == "" or typ == "unknown":
            continue
        saved[name] = (name in ctx.scope.vars, ctx.scope.vars.get(name, ""))
        ctx.scope.vars[name] = typ
    try:
        for stmt_val in stmt_list:
            stmt = _jv_obj(stmt_val)
            if len(stmt) > 0:
                _resolve_stmt(stmt, ctx)
                invalidated: set[str] = set()
                one_stmt: list[JsonVal] = []
                one_stmt.append(stmt)
                _collect_reassigned(one_stmt, invalidated)
                for name in invalidated:
                    if name not in saved:
                        continue
                    had_local, value = saved[name]
                    if had_local:
                        ctx.scope.vars[name] = value
                    else:
                        if name in ctx.scope.vars:
                            ctx.scope.vars[name] = "unknown"
                    saved.pop(name)
    finally:
        for name, entry in saved.items():
            had_local, value = entry
            if had_local:
                ctx.scope.vars[name] = value
            else:
                if name in ctx.scope.vars:
                    ctx.scope.vars[name] = "unknown"

def _same_expr_shape(left: JsonVal, right: JsonVal) -> bool:
    left_obj = _jv_obj(left)
    right_obj = _jv_obj(right)
    if len(left_obj) == 0 or len(right_obj) == 0:
        return False
    left_kind = _dict_get_str(left_obj, "kind")
    right_kind = _dict_get_str(right_obj, "kind")
    if left_kind != right_kind:
        return False
    if left_kind == "Name":
        left_id = _dict_get_str(left_obj, "id")
        right_id = _dict_get_str(right_obj, "id")
        return left_id != "" and left_id == right_id
    left_repr = _dict_get_str(left_obj, "repr")
    right_repr = _dict_get_str(right_obj, "repr")
    return left_repr != "" and left_repr == right_repr


def _narrow_ifexp_branch_type(
    test: JsonVal,
    body: JsonVal,
    orelse: JsonVal,
    body_type: str,
    orelse_type: str,
) -> tuple[str, str, str]:
    test_obj = _jv_obj(test)
    if len(test_obj) == 0:
        return body_type, body_type, orelse_type
    guarded, expected_name = _resolve_isinstance_guard_info(test)
    guarded_obj = _jv_obj(guarded)
    if len(guarded_obj) == 0:
        return body_type, body_type, orelse_type
    narrowed_target = _resolve_select_guard_target_type(body_type, expected_name)
    if narrowed_target == "":
        narrowed_target = _resolve_select_guard_target_type(orelse_type, expected_name)
    if _same_expr_shape(guarded, body) and (_is_dynamic_supertype(body_type) or _is_unknown_like_type(body_type)) and not _is_unknown_like_type(orelse_type):
        narrowed_body_type = narrowed_target if narrowed_target != "" else body_type
        if orelse_type == "None":
            return narrowed_body_type + " | None", narrowed_body_type, orelse_type
        return narrowed_body_type, narrowed_body_type, narrowed_body_type
    if _same_expr_shape(guarded, orelse) and (_is_dynamic_supertype(orelse_type) or _is_unknown_like_type(orelse_type)) and not _is_unknown_like_type(body_type):
        narrowed_orelse_type = narrowed_target if narrowed_target != "" else orelse_type
        if body_type == "None":
            return narrowed_orelse_type + " | None", body_type, narrowed_orelse_type
        return body_type, body_type, body_type
    return body_type, body_type, orelse_type


def _bind_comp_target(scope: Scope, target: dict[str, JsonVal], elem_type: str) -> None:
    target_kind = _dict_get_str(target, "kind")
    if target_kind == "Name":
        var_name = _dict_get_str(target, "id")
        if var_name != "":
            scope.define(var_name, elem_type)
            target["resolved_type"] = elem_type
        return
    if target_kind != "Tuple":
        return
    target["resolved_type"] = elem_type
    if not elem_type.startswith("tuple[") or not elem_type.endswith("]"):
        return
    item_types = extract_type_args(elem_type)
    elements = _dict_get_arr(target, "elements")
    idx = 0
    while idx < len(elements):
        elem = _jv_obj(elements[idx])
        if len(elem) > 0 and _dict_get_str(elem, "kind") == "Name":
            item_name = _dict_get_str(elem, "id")
            if item_name != "":
                item_type = item_types[idx] if idx < len(item_types) else "unknown"
                scope.define(item_name, item_type)
                elem["resolved_type"] = item_type
        idx += 1


def _write_lambda_arg_nodes(expr: dict[str, JsonVal], arg_types: dict[str, str]) -> None:
    args_list = _dict_get_arr(expr, "args")
    for arg_val in args_list:
        arg = _jv_obj(arg_val)
        if len(arg) == 0:
            continue
        arg_name = _dict_get_str(arg, "arg")
        if arg_name != "":
            arg["resolved_type"] = arg_types.get(arg_name, "unknown")

def _resolve_lambda_body(
    expr: dict[str, JsonVal],
    ctx: ResolveContext,
    arg_types: dict[str, str],
) -> str:
    lam_scope: Scope = ctx.scope.child()
    for name, typ in arg_types.items():
        lam_scope.define(name, typ)
    old_scope: Scope = ctx.scope
    ctx.scope = lam_scope
    body_type: str = "unknown"
    if "body" in expr:
        body_val = expr["body"]
        body_obj = _jv_obj(body_val)
        if len(body_obj) > 0:
            body_type = _resolve_expr(body_obj, ctx)
        else:
            body_list = _jv_arr(body_val)
            for stmt_val in body_list:
                stmt = _jv_obj(stmt_val)
                if len(stmt) > 0:
                    _resolve_stmt(stmt, ctx)
    ctx.scope = old_scope
    return body_type

def _refine_lambda_from_call(
    expr: dict[str, JsonVal],
    ctx: ResolveContext,
    call_arg_types: list[str],
) -> str:
    arg_order: list[str] = _lambda_arg_names(expr)
    arg_types: dict[str, str] = _lambda_arg_types(expr, ctx, arg_order)
    _resolve_lambda_defaults(expr, ctx, arg_types)
    index = 0
    while index < len(call_arg_types):
        if index >= len(arg_order):
            break
        actual_type = call_arg_types[index]
        arg_name = arg_order[index]
        arg_types[arg_name] = _merge_refined_type(arg_types.get(arg_name, "unknown"), actual_type)
        index += 1

    ret_raw = _dict_get_str(expr, "return_type")
    ret: str = _ctx_normalize_type(ret_raw, ctx) if ret_raw != "" else "unknown"
    _write_lambda_arg_nodes(expr, arg_types)
    body_type: str = _resolve_lambda_body(expr, ctx, arg_types)

    inferred: dict[str, str] = _infer_lambda_arg_types(expr, arg_order)
    rerun: bool = False
    for arg_name2 in arg_order:
        inferred_type = inferred.get(arg_name2, "")
        merged = _merge_refined_type(arg_types.get(arg_name2, "unknown"), inferred_type)
        if merged != arg_types.get(arg_name2, "unknown"):
            arg_types[arg_name2] = merged
            rerun = True
    if rerun:
        _write_lambda_arg_nodes(expr, arg_types)
        body_type = _resolve_lambda_body(expr, ctx, arg_types)

    if _is_unknown_like_type(ret) and not _is_unknown_like_type(body_type):
        ret = body_type

    expr["arg_order"] = _json_str_list(arg_order)
    expr["arg_types"] = _json_str_dict(arg_types)
    expr["return_type"] = ret
    arg_type_strs: list[str] = [arg_types.get(name, "unknown") for name in arg_order]
    callable_type: str = _make_callable_type(arg_type_strs, ret)
    expr["resolved_type"] = callable_type
    return callable_type


def _lambda_assign_expected_type(node: JsonVal, expected: str, arg_names: set[str], inferred: dict[str, str]) -> None:
    nd = _jv_obj(node)
    if len(nd) == 0 or _is_unknown_like_type(expected):
        return
    kind: str = _dict_get_str(nd, "kind")
    if kind == "Name":
        name = _dict_get_str(nd, "id")
        current = _dict_get_str(nd, "resolved_type")
        if name in arg_names and (current == "" or _is_unknown_like_type(current)) and name not in inferred:
            inferred[name] = expected
        return
    if kind == "BinOp":
        if "left" in nd:
            _lambda_assign_expected_type(nd["left"], expected, arg_names, inferred)
        if "right" in nd:
            _lambda_assign_expected_type(nd["right"], expected, arg_names, inferred)
        return
    if kind == "UnaryOp":
        if "operand" in nd:
            _lambda_assign_expected_type(nd["operand"], expected, arg_names, inferred)
        return
    if kind == "IfExp":
        if "body" in nd:
            _lambda_assign_expected_type(nd["body"], expected, arg_names, inferred)
        if "orelse" in nd:
            _lambda_assign_expected_type(nd["orelse"], expected, arg_names, inferred)

def _infer_lambda_arg_types(expr: dict[str, JsonVal], arg_order: list[str]) -> dict[str, str]:
    inferred: dict[str, str] = {}
    arg_names: set[str] = set(arg_order)

    def visit(node: JsonVal) -> None:
        node_list = _jv_arr(node)
        if len(node_list) > 0:
            for item in node_list:
                visit(item)
            return
        nd = _jv_obj(node)
        if len(nd) == 0:
            return
        kind: str = _dict_get_str(nd, "kind")
        if kind == "BinOp":
            left: JsonVal = None
            right: JsonVal = None
            if "left" in nd:
                left = nd["left"]
            if "right" in nd:
                right = nd["right"]
            left_obj = _jv_obj(left)
            right_obj = _jv_obj(right)
            lt = _dict_get_str(left_obj, "resolved_type") if len(left_obj) > 0 else "unknown"
            rt = _dict_get_str(right_obj, "resolved_type") if len(right_obj) > 0 else "unknown"
            result = _dict_get_str(nd, "resolved_type")
            if not _is_unknown_like_type(rt):
                _lambda_assign_expected_type(left, rt, arg_names, inferred)
            if not _is_unknown_like_type(lt):
                _lambda_assign_expected_type(right, lt, arg_names, inferred)
            if not _is_unknown_like_type(result):
                _lambda_assign_expected_type(left, result, arg_names, inferred)
                _lambda_assign_expected_type(right, result, arg_names, inferred)
        elif kind == "Compare":
            left_node: JsonVal = None
            if "left" in nd:
                left_node = nd["left"]
            comparators = _dict_get_arr(nd, "comparators")
            prev: JsonVal = left_node
            for comp in comparators:
                prev_obj = _jv_obj(prev)
                comp_obj = _jv_obj(comp)
                prev_t = _dict_get_str(prev_obj, "resolved_type") if len(prev_obj) > 0 else "unknown"
                comp_t = _dict_get_str(comp_obj, "resolved_type") if len(comp_obj) > 0 else "unknown"
                if not _is_unknown_like_type(comp_t):
                    _lambda_assign_expected_type(prev, comp_t, arg_names, inferred)
                if not _is_unknown_like_type(prev_t):
                    _lambda_assign_expected_type(comp, prev_t, arg_names, inferred)
                prev = comp
        for value in nd.values():
            visit(value)

    if "body" in expr:
        visit(expr["body"])
    return inferred

def _collect_callable_param_uses(node: JsonVal, params: set[str], out: dict[str, list[str]], invalid: set[str]) -> None:
    node_list = _jv_arr(node)
    if len(node_list) > 0:
        for item in node_list:
            _collect_callable_param_uses(item, params, out, invalid)
        return
    nd = _jv_obj(node)
    if len(nd) == 0:
        return
    if _dict_get_str(nd, "kind") == "Call":
        func = _dict_get_obj(nd, "func")
        if len(func) > 0 and _dict_get_str(func, "kind") == "Name":
            fn_name = _dict_get_str(func, "id")
            if fn_name != "" and fn_name in params and fn_name not in invalid:
                actual = _collect_call_arg_types(nd)
                if fn_name in out and out[fn_name] != actual:
                    invalid.add(fn_name)
                    out.pop(fn_name)
                else:
                    out[fn_name] = actual
    for value in nd.values():
        _collect_callable_param_uses(value, params, out, invalid)

def _callable_type_uses_signature(type_str: str) -> bool:
    return type_str in ("callable", "Callable") or type_str.startswith("callable[") or type_str.startswith("Callable[")


def _effective_resolved_type_for_callable(node: JsonVal) -> str:
    nd = _jv_obj(node)
    if len(nd) == 0:
        return ""
    resolved = _dict_get_str(nd, "resolved_type")
    if resolved != "":
        return resolved
    if _dict_get_str(nd, "kind") == "Unbox" and "value" in nd:
        return _effective_resolved_type_for_callable(nd["value"])
    return ""


def _infer_callable_return_from_parent(
    call_node: dict[str, JsonVal],
    parent: JsonVal,
    grandparent: JsonVal,
    func_node: dict[str, JsonVal],
) -> str:
    parent_obj = _jv_obj(parent)
    if len(parent_obj) == 0:
        return ""
    parent_kind = _dict_get_str(parent_obj, "kind")
    if parent_kind == "Return":
        return _dict_get_str(func_node, "return_type")
    if parent_kind == "Unbox":
        resolved = _effective_resolved_type_for_callable(parent)
        if resolved != "":
            return resolved
    if parent_kind == "Call":
        runtime_call = _dict_get_str(parent_obj, "runtime_call")
        if runtime_call == "list.append" and "runtime_owner" in parent_obj:
            owner_type = _effective_resolved_type_for_callable(parent_obj["runtime_owner"])
            if owner_type.startswith("list[") and owner_type.endswith("]"):
                return owner_type[5:-1]
        func = _dict_get_obj(parent_obj, "func")
        call_func = _dict_get_obj(call_node, "func")
        func_kind = _dict_get_str(func, "kind")
        func_id = _dict_get_str(func, "id")
        call_func_id = _dict_get_str(call_func, "id")
        if func_kind == "Name" and func_id != "" and func_id == call_func_id:
            grandparent_obj = _jv_obj(grandparent)
            grandparent_kind = _dict_get_str(grandparent_obj, "kind")
            if grandparent_kind == "Return":
                return _dict_get_str(func_node, "return_type")
            if grandparent_kind == "Unbox":
                resolved2 = _effective_resolved_type_for_callable(grandparent)
                if resolved2 != "":
                    return resolved2
    if parent_kind in ("Assign", "AnnAssign"):
        declared = _dict_get_str(parent_obj, "decl_type")
        if declared != "":
            return declared
    return ""

def _callable_type_needs_refinement(type_str: str, ctx: ResolveContext) -> bool:
    if not _callable_type_uses_signature(type_str):
        return False
    if type_str in ("callable", "Callable"):
        return True
    params, ret = _parse_callable_signature(type_str, ctx)
    if _is_unknown_like_type(ret):
        return True
    for param in params:
        if _is_unknown_like_type(param):
            return True
    return False


def _infer_callable_param_signature(
    func_node: dict[str, JsonVal],
    param_name: str,
    ctx: ResolveContext,
) -> str:
    arg_types = _dict_get_obj(func_node, "arg_types")
    declared = _dict_get_str(arg_types, param_name)
    if not _callable_type_needs_refinement(declared, ctx):
        return ""

    inferred_args: list[str] = []
    inferred_ret = ""
    if declared not in ("callable", "Callable", ""):
        declared_params, declared_ret = _parse_callable_signature(declared, ctx)
        declared_params_known = len(declared_params) > 0
        for p in declared_params:
            if _is_unknown_like_type(p):
                declared_params_known = False
        if declared_params_known:
            inferred_args = declared_params
        if declared_ret != "" and not _is_unknown_like_type(declared_ret):
            inferred_ret = declared_ret

    invalid = False

    def _set_args(arg_types2: list[str]) -> None:
        nonlocal inferred_args, invalid
        if len(arg_types2) == 0:
            return
        for t in arg_types2:
            if _is_unknown_like_type(t) or _callable_type_uses_signature(t):
                return
        if len(inferred_args) == 0:
            inferred_args = []
            for arg_type in arg_types2:
                inferred_args.append(arg_type)
            return
        if inferred_args != arg_types2:
            invalid = True

    def _set_ret(ret_type: str) -> None:
        nonlocal inferred_ret, invalid
        if ret_type == "" or _is_unknown_like_type(ret_type) or _callable_type_uses_signature(ret_type):
            return
        if inferred_ret == "":
            inferred_ret = ret_type
            return
        if inferred_ret != ret_type:
            invalid = True

    def _visit(cur: JsonVal, parent: JsonVal = None, grandparent: JsonVal = None) -> None:
        nonlocal invalid
        if invalid:
            return
        cur_obj = _jv_obj(cur)
        if len(cur_obj) > 0:
            cur_kind = _dict_get_str(cur_obj, "kind")
            if cur_kind == "Call":
                func = _dict_get_obj(cur_obj, "func")
                func_kind = _dict_get_str(func, "kind")
                func_id = _dict_get_str(func, "id")
                if func_kind == "Name" and func_id == param_name:
                    _set_args(_collect_call_arg_types(cur_obj))
                    _set_ret(_infer_callable_return_from_parent(cur_obj, parent, grandparent, func_node))
            for child in cur_obj.values():
                _visit(child, cur, parent)
            return
        cur_list = _jv_arr(cur)
        for child in cur_list:
            _visit(child, parent, grandparent)

    if "body" in func_node:
        _visit(func_node["body"], None, None)
    if invalid or len(inferred_args) == 0 or inferred_ret == "":
        return ""
    return _make_callable_type(inferred_args, inferred_ret)


def _refresh_callable_param_calls(node: JsonVal, refined: dict[str, str], ctx: ResolveContext) -> None:
    node_list = _jv_arr(node)
    if len(node_list) > 0:
        for item in node_list:
            _refresh_callable_param_calls(item, refined, ctx)
        return
    nd = _jv_obj(node)
    if len(nd) == 0:
        return
    if _dict_get_str(nd, "kind") == "Call":
        func = _dict_get_obj(nd, "func")
        if len(func) > 0 and _dict_get_str(func, "kind") == "Name":
            fn_name = _dict_get_str(func, "id")
            if fn_name != "" and fn_name in refined:
                callable_type = refined[fn_name]
                _, ret = _parse_callable_signature(callable_type, ctx)
                func["resolved_type"] = callable_type
                nd["resolved_type"] = ret if not _is_unknown_like_type(ret) else "unknown"
    for value in nd.values():
        _refresh_callable_param_calls(value, refined, ctx)

def _refine_callable_params_from_calls(module_doc: dict[str, JsonVal], ctx: ResolveContext) -> None:
    functions: dict[str, dict[str, JsonVal]] = {}
    body_list: list[JsonVal] = _dict_get_arr(module_doc, "body")
    for stmt_val in body_list:
        stmt = _jv_obj(stmt_val)
        if len(stmt) > 0 and _dict_get_str(stmt, "kind") == "FunctionDef":
            name = _dict_get_str(stmt, "name")
            if name != "":
                functions[name] = stmt

    def _local_function_callable_type(name: str) -> str:
        fn_def = functions.get(name)
        if fn_def is None:
            renamed = ctx.renamed_symbols.get(name, "")
            if renamed != "":
                fn_def = functions.get(renamed)
        if fn_def is None:
            return ""
        arg_order_list: list[str] = []
        for arg_name_obj in _dict_get_arr(fn_def, "arg_order"):
            arg_name_text = _jv_str(arg_name_obj)
            if arg_name_text != "":
                arg_order_list.append(arg_name_text)
        arg_types_obj = _dict_get_obj(fn_def, "arg_types")
        ret_obj = _dict_get_str(fn_def, "return_type")
        if len(arg_order_list) == 0 or len(arg_types_obj) == 0 or ret_obj == "":
            return ""
        params: list[str] = []
        for arg_name in arg_order_list:
            if arg_name == "self":
                continue
            arg_type = _dict_get_str(arg_types_obj, arg_name)
            if arg_type == "":
                return ""
            params.append(arg_type)
        return _make_callable_type(params, ret_obj)

    observed: dict[str, dict[str, str]] = {}
    invalid: set[tuple[str, str]] = set()

    def _record(fn_name: str, param_name: str, callable_type: str) -> None:
        key = (fn_name, param_name)
        if key in invalid:
            return
        cur = observed.setdefault(fn_name, {})
        prev = cur.get(param_name, "")
        if prev == "" or prev == callable_type:
            cur[param_name] = callable_type
            return
        invalid.add(key)
        if param_name in cur:
            cur.pop(param_name)

    def _visit(node: JsonVal) -> None:
        node_list = _jv_arr(node)
        if len(node_list) > 0:
            for item in node_list:
                _visit(item)
            return
        nd = _jv_obj(node)
        if len(nd) == 0:
            return
        if _dict_get_str(nd, "kind") == "Call":
            func = _dict_get_obj(nd, "func")
            fn_name = _dict_get_str(func, "id") if len(func) > 0 else ""
            fn_def = functions.get(fn_name) if fn_name != "" else None
            if fn_def is not None:
                arg_order_list: list[str] = []
                for param_obj in _dict_get_arr(fn_def, "arg_order"):
                    param_text = _jv_str(param_obj)
                    if param_text != "":
                        arg_order_list.append(param_text)
                arg_types_obj = _dict_get_obj(fn_def, "arg_types")
                args_obj = _dict_get_arr(nd, "args")
                if len(arg_order_list) > 0 and len(arg_types_obj) > 0:
                    positional_index = 0
                    for param in arg_order_list:
                        if param == "self":
                            continue
                        declared = _dict_get_str(arg_types_obj, param)
                        if not _callable_type_needs_refinement(declared, ctx):
                            positional_index += 1
                            continue
                        if positional_index >= len(args_obj):
                            positional_index += 1
                            continue
                        actual_arg = args_obj[positional_index]
                        actual = _effective_resolved_type_for_callable(actual_arg)
                        actual_obj = _jv_obj(actual_arg)
                        if actual in ("callable", "Callable") and len(actual_obj) > 0 and _dict_get_str(actual_obj, "kind") == "Name":
                            actual_name = _dict_get_str(actual_obj, "id")
                            if actual_name != "":
                                precise_actual = _local_function_callable_type(actual_name)
                                if precise_actual != "":
                                    actual = "" + precise_actual
                        if _callable_type_uses_signature(actual) and not _callable_type_needs_refinement(actual, ctx):
                            _record(fn_name, param, actual)
                        positional_index += 1
        for value in nd.values():
            _visit(value)

    if "body" in module_doc:
        _visit(module_doc["body"])
    if "main_guard_body" in module_doc:
        _visit(module_doc["main_guard_body"])

    for fn_name, param_map in observed.items():
        fn_def = functions.get(fn_name)
        if fn_def is None:
            continue
        arg_types_obj = _dict_get_obj(fn_def, "arg_types")
        if len(arg_types_obj) == 0:
            continue
        refined: dict[str, str] = {}
        for param_name, callable_type in param_map.items():
            if (fn_name, param_name) in invalid:
                continue
            declared_prev = _dict_get_str(arg_types_obj, param_name)
            final_type = callable_type
            if declared_prev != "" and _type_text_contains_none(declared_prev):
                if not _type_text_contains_none(final_type):
                    final_type = final_type + " | None"
            arg_types_obj[param_name] = final_type
            refined[param_name] = final_type
            arg_types_raw = _dict_get_obj(fn_def, "arg_types_raw")
            if len(arg_types_raw) > 0:
                arg_types_raw[param_name] = final_type
            arg_type_exprs = _dict_get_obj(fn_def, "arg_type_exprs")
            if len(arg_type_exprs) > 0:
                arg_type_exprs[param_name] = make_type_expr(final_type)
        if len(refined) > 0 and "body" in fn_def:
            _refresh_callable_param_calls(fn_def["body"], refined, ctx)

def _type_text_contains_none(type_str: str) -> bool:
    t: str = type_str.strip()
    if t == "" or t == "None":
        return t == "None"
    # Rough top-level `| None` check; good enough for preserving the
    # optionality that a refined callable dropped.
    parts = t.split(" | ")
    for part in parts:
        if part.strip() == "None":
            return True
    return False


# ---------------------------------------------------------------------------
# Expression type resolution
# ---------------------------------------------------------------------------

def _resolve_expr(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve the type of an expression node, mutating it in place.
    Returns the resolved_type string."""
    kind: str = _dict_get_str(expr, "kind")

    if kind == "Constant":
        return _resolve_constant(expr, ctx)
    if kind == "Name":
        return _resolve_name(expr, ctx)
    if kind == "BinOp":
        return _resolve_binop(expr, ctx)
    if kind == "UnaryOp":
        return _resolve_unaryop(expr, ctx)
    if kind == "Compare":
        return _resolve_compare(expr, ctx)
    if kind == "BoolOp":
        return _resolve_boolop(expr, ctx)
    if kind == "Call":
        return _resolve_call(expr, ctx)
    if kind == "Attribute":
        return _resolve_attribute(expr, ctx)
    if kind == "Subscript":
        return _resolve_subscript(expr, ctx)
    if kind == "List":
        return _resolve_list(expr, ctx)
    if kind == "Dict":
        return _resolve_dict(expr, ctx)
    if kind == "Set":
        return _resolve_set(expr, ctx)
    if kind == "Tuple":
        return _resolve_tuple(expr, ctx)
    if kind == "IfExp":
        return _resolve_ifexp(expr, ctx)
    if kind == "ListComp":
        return _resolve_listcomp(expr, ctx)
    if kind == "SetComp":
        return _resolve_setcomp(expr, ctx)
    if kind == "DictComp":
        return _resolve_dictcomp(expr, ctx)
    if kind == "Lambda":
        return _resolve_lambda(expr, ctx)
    if kind == "Starred":
        return _resolve_starred(expr, ctx)
    if kind == "Slice":
        return _resolve_slice(expr, ctx)
    if kind == "JoinedStr":
        expr["resolved_type"] = "str"
        values = _dict_get_arr(expr, "values")
        for v_val in values:
            v = _jv_obj(v_val)
            if len(v) == 0:
                continue
            vk: str = _dict_get_str(v, "kind")
            if vk == "FormattedValue":
                inner = _dict_get_obj(v, "value")
                if len(inner) > 0:
                    _resolve_expr(inner, ctx)
                v["resolved_type"] = "str"
            elif vk == "Constant":
                _resolve_expr(v, ctx)
            else:
                _resolve_expr(v, ctx)
        return "str"
    if kind == "FormattedValue":
        inner2 = _dict_get_obj(expr, "value")
        if len(inner2) > 0:
            _resolve_expr(inner2, ctx)
        expr["resolved_type"] = "str"
        return "str"

    # Fallback: resolve children recursively
    rt = _dict_get_str(expr, "resolved_type")
    if rt == "":
        expr["resolved_type"] = "unknown"
    for val in expr.values():
        child = _jv_obj(val)
        if len(child) > 0 and "kind" in child:
            _resolve_expr(child, ctx)
        else:
            child_items = _jv_arr(val)
            for item_val in child_items:
                item = _jv_obj(item_val)
                if len(item) > 0 and "kind" in item:
                    _resolve_expr(item, ctx)
    rt2 = _dict_get_str(expr, "resolved_type")
    return rt2 if rt2 != "" else "unknown"


def _resolve_constant(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    val: JsonVal = None
    if "value" in expr:
        val = expr["value"]
    if val is None:
        t: str = "None"
    else:
        value = json.JsonValue(val)
        if value.as_bool() is not None:
            t = "bool"
        elif value.as_int() is not None:
            t = "int64"
        elif value.as_float() is not None:
            t = "float64"
        elif value.as_str() is not None:
            t = "str"
        else:
            t = "unknown"
    expr["resolved_type"] = t
    return t

def _resolve_name(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    name: str = _dict_get_str(expr, "id")
    if name in ctx.import_modules:
        expr["resolved_type"] = "module"
        expr["runtime_module_id"] = ctx.import_modules.get(name, "")
        return "module"
    imp: dict[str, str] = ctx.import_symbols.get(name, {})
    if len(imp) > 0:
        module_id: str = imp.get("module", "")
        export_name: str = imp.get("name", "")
        if export_name == "":
            export_name = name
        if ctx.registry.lookup_stdlib_class(module_id, export_name) is not None:
            expr["resolved_type"] = "type"
            expr["type_object_of"] = export_name
            return "type"
        if ctx.registry.lookup_stdlib_function(module_id, export_name) is not None:
            expr["resolved_type"] = "callable"
            return "callable"
    t: str = ctx.scope.lookup(name)
    if ctx.lookup_class(name) is not None:
        expr["resolved_type"] = "type"
        expr["type_object_of"] = name
        return "type"
    if t == "unknown" and name in _BUILTIN_EXCEPTION_TYPE_NAMES:
        expr["resolved_type"] = "type"
        expr["type_object_of"] = name
        expr["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
        return "type"
    if t == "unknown" and name in _BUILTIN_TYPE_OBJECT_NAMES:
        expr["resolved_type"] = "type"
        expr["type_object_of"] = name
        return "type"
    if t == "unknown":
        fn_sig: FuncSig | None = ctx.lookup_function(name)
        if fn_sig is not None:
            expr["resolved_type"] = "Callable"
            return "Callable"
    expr["resolved_type"] = t
    if t != "unknown":
        expr["borrow_kind"] = "readonly_ref"
    return t

def _numeric_cast_entry(on: str, from_type: str, to_type: str) -> dict[str, JsonVal]:
    entry: dict[str, JsonVal] = {}
    entry["on"] = on
    entry["from"] = from_type
    entry["to"] = to_type
    entry["reason"] = "numeric_promotion"
    return entry


def _resolve_binop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    left = _dict_get_obj(expr, "left")
    right = _dict_get_obj(expr, "right")
    lt: str = "unknown"
    rt: str = "unknown"
    if len(left) > 0:
        lt = _resolve_expr(left, ctx)
    if len(right) > 0:
        rt = _resolve_expr(right, ctx)

    op: str = _dict_get_str(expr, "op")

    result: str = _binop_result_type(lt, rt, op)
    expr["resolved_type"] = result

    casts = _dict_get_arr(expr, "casts")
    if len(casts) > 0:
        if is_int_type(lt) and is_float_type(rt):
            casts.append(_numeric_cast_entry("left", lt, rt))
        elif is_float_type(lt) and is_int_type(rt):
            casts.append(_numeric_cast_entry("right", rt, lt))
        elif op == "Div" and is_int_type(lt) and is_int_type(rt):
            casts.append(_numeric_cast_entry("left", lt, "float64"))
            casts.append(_numeric_cast_entry("right", rt, "float64"))
        elif is_int_type(lt) and is_int_type(rt) and lt != rt:
            promoted: str = _promote_int_types(lt, rt)
            if lt != promoted:
                casts.append(_numeric_cast_entry("left", lt, promoted))
            if rt != promoted:
                casts.append(_numeric_cast_entry("right", rt, promoted))

    return result


# Integer type rank for usual arithmetic conversion (C++ rules).
# Higher rank = larger type. Unsigned outranks signed of same size.
_INT_RANK: dict[str, int] = {
    "int8": 1, "uint8": 2,
    "int16": 3, "uint16": 4,
    "int32": 5, "uint32": 6,
    "int64": 7, "uint64": 8,
}


def _promote_int_types(a: str, b: str) -> str:
    """Return the promoted type for mixed integer arithmetic (usual arithmetic conversion)."""
    ra: int = _INT_RANK.get(a, 7)  # default to int64
    rb: int = _INT_RANK.get(b, 7)
    if ra >= rb:
        return a
    return b


def _binop_result_type(lt: str, rt: str, op: str) -> str:
    """Determine result type of a binary operation."""
    # String operations
    if lt == "str" and rt == "str":
        if op == "Add":
            return "str"
        if op == "Mod":
            return "str"
    if lt == "str" and is_int_type(rt) and op == "Mult":
        return "str"
    if is_int_type(lt) and rt == "str" and op == "Mult":
        return "str"

    # Path operations
    if lt == "Path" or rt == "Path":
        if op == "Div":
            return "Path"

    # Division always produces float
    if op == "Div":
        if is_numeric(lt) and is_numeric(rt):
            return "float64"

    # Floor division and modulo with ints produce int
    if op == "FloorDiv" or op == "Mod":
        if is_int_type(lt) and is_int_type(rt):
            return lt
        if is_float_type(lt) or is_float_type(rt):
            return "float64"

    # Numeric promotion
    if is_float_type(lt) or is_float_type(rt):
        return "float64"
    if is_int_type(lt) and is_int_type(rt):
        if lt == rt:
            return lt  # Same int type
        # Usual arithmetic conversion: promote smaller to larger
        return _promote_int_types(lt, rt)

    # Bitwise operations on ints
    if op == "BitAnd" or op == "BitOr" or op == "BitXor" or op == "LShift" or op == "RShift":
        if is_int_type(lt):
            return lt

    # Boolean operations
    if lt == "bool" and rt == "bool":
        return "bool"

    # Fallback
    if lt != "unknown":
        return lt
    if rt != "unknown":
        return rt
    return "unknown"


def _resolve_unaryop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    operand = _dict_get_obj(expr, "operand")
    ot: str = "unknown"
    if len(operand) > 0:
        ot = _resolve_expr(operand, ctx)
    op: str = _dict_get_str(expr, "op")
    if op == "Not":
        expr["resolved_type"] = "bool"
        return "bool"
    if op == "USub" or op == "UAdd":
        expr["resolved_type"] = ot
        return ot
    if op == "Invert":
        expr["resolved_type"] = ot
        return ot
    expr["resolved_type"] = ot
    return ot


def _resolve_compare(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    left = _dict_get_obj(expr, "left")
    if len(left) > 0:
        _resolve_expr(left, ctx)
    saw_membership = False
    ops = _dict_get_arr(expr, "ops")
    for op_val in ops:
        op = _jv_str(op_val)
        if op == "In" or op == "NotIn":
            saw_membership = True
            break
    comps = _dict_get_arr(expr, "comparators")
    for comp_val in comps:
        comp = _jv_obj(comp_val)
        if len(comp) > 0:
            _resolve_expr(comp, ctx)
    if saw_membership:
        ctx.used_builtin_modules.add("pytra.built_in.contains")
    expr["resolved_type"] = "bool"
    return "bool"


def _resolve_boolop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    values = _dict_get_arr(expr, "values")
    op = _dict_get_str(expr, "op")
    result_type: str = "unknown"
    saved: dict[str, tuple[bool, str]] = {}
    if len(values) > 0:
        try:
            for value in values:
                v = _jv_obj(value)
                if len(v) == 0:
                    continue
                vt = _resolve_expr(v, ctx)
                if result_type == "unknown":
                    result_type = vt
                elif vt != "unknown" and vt != result_type:
                    if is_numeric(result_type) and is_numeric(vt):
                        if is_float_type(result_type) or is_float_type(vt):
                            result_type = "float64"
                        elif is_int_type(result_type) and is_int_type(vt):
                            result_type = _promote_int_types(result_type, vt)
                    else:
                        result_type = "Any"
                narrowed: dict[str, str] = {}
                if op == "And":
                    narrowed = _resolve_guard_narrowing_from_expr(value)
                elif op == "Or":
                    narrowed = _resolve_invert_guard_narrowing_from_expr(value)
                for name, typ in narrowed.items():
                    if name == "" or typ == "" or typ == "unknown":
                        continue
                    if name not in saved:
                        saved[name] = (name in ctx.scope.vars, ctx.scope.vars.get(name, ""))
                    ctx.scope.vars[name] = typ
        finally:
            for name, entry in saved.items():
                had_local, saved_value = entry
                if had_local:
                    ctx.scope.vars[name] = saved_value
                else:
                    if name in ctx.scope.vars:
                        ctx.scope.vars[name] = "unknown"
    expr["resolved_type"] = result_type
    return result_type


def _resolve_call(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    func = _dict_get_obj(expr, "func")
    if len(func) == 0:
        expr["resolved_type"] = "unknown"
        return "unknown"

    func_kind: str = _dict_get_str(func, "kind")

    # Method call: obj.method(...)
    if func_kind == "Attribute":
        return _resolve_method_call(expr, func, ctx)

    # Inline lambda call: (lambda ...)(...)
    if func_kind == "Lambda":
        _resolve_call_args(expr, ctx)
        callable_type = _refine_lambda_from_call(func, ctx, _collect_call_arg_types(expr))
        _, callable_ret = _parse_callable_signature(callable_type, ctx)
        resolved = callable_ret if not _is_unknown_like_type(callable_ret) else "unknown"
        expr["resolved_type"] = resolved
        return resolved

    # Simple function call: f(...)
    if func_kind == "Name":
        return _resolve_simple_call(expr, func, ctx)

    # Fallback
    _resolve_expr(func, ctx)
    _resolve_call_args(expr, ctx)
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_call_args(expr: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve types of call arguments."""
    args = _dict_get_arr(expr, "args")
    for arg_val in args:
        arg = _jv_obj(arg_val)
        if len(arg) > 0:
            _resolve_expr(arg, ctx)
    keywords = _dict_get_arr(expr, "keywords")
    for kw_val in keywords:
        kw = _jv_obj(kw_val)
        if len(kw) == 0:
            continue
        val = _dict_get_obj(kw, "value")
        if len(val) > 0:
            _resolve_expr(val, ctx)


_SIG_TYPE_PARAMS: set[str] = {"T", "U", "K", "V"}


def _collect_call_arg_types(expr: dict[str, JsonVal]) -> list[str]:
    """Collect already-resolved positional argument types from a Call node."""
    result: list[str] = []
    args = _dict_get_arr(expr, "args")
    for arg_val in args:
        arg = _jv_obj(arg_val)
        if len(arg) > 0:
            rt = _dict_get_str(arg, "resolved_type")
            result.append(rt if rt != "" else "unknown")
    return result


def _bind_type_pattern(pattern: str, actual: str, bindings: dict[str, str]) -> None:
    """Bind simple generic placeholders (T/U/K/V) from signature pattern to actual type."""
    pat: str = "" + normalize_type(pattern)
    act: str = "" + normalize_type(actual)
    if pat == "" or pat == "unknown" or act == "" or act == "unknown":
        return
    if pat in _SIG_TYPE_PARAMS:
        existing: str = bindings.get(pat, "")
        if existing == "" or existing == act:
            bindings[pat] = act
        return
    if pat == act:
        return
    if " | " in pat and " | " in act:
        pat_parts: list[str] = pat.split(" | ")
        act_parts: list[str] = act.split(" | ")
        if len(pat_parts) == len(act_parts):
            for i in range(len(pat_parts)):
                _bind_type_pattern(pat_parts[i], act_parts[i], bindings)
        return
    pat_bracket: int = pat.find("[")
    act_bracket: int = act.find("[")
    if pat_bracket > 0 and act_bracket > 0 and pat.endswith("]") and act.endswith("]"):
        pat_base: str = pat[:pat_bracket]
        act_base: str = act[:act_bracket]
        if pat_base != act_base:
            return
        pat_args: list[str] = list(extract_type_args(pat))
        act_args: list[str] = list(extract_type_args(act))
        if len(pat_args) != len(act_args):
            return
        for i in range(len(pat_args)):
            _bind_type_pattern(pat_args[i], act_args[i], bindings)


def _substitute_type_bindings(type_str: str, bindings: dict[str, str]) -> str:
    """Apply generic placeholder bindings to a normalized signature type."""
    t: str = "" + normalize_type(type_str)
    if t in _SIG_TYPE_PARAMS:
        bound: str = bindings.get(t, "")
        if bound != "":
            return bound
        return t
    if " | " in t:
        parts: list[str] = t.split(" | ")
        return " | ".join([_substitute_type_bindings(part, bindings) for part in parts])
    bracket: int = t.find("[")
    if bracket > 0 and t.endswith("]"):
        base: str = t[:bracket]
        args: list[str] = list(extract_type_args(t))
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(_substitute_type_bindings(arg, bindings))
        if len(rendered_args) == 1:
            return base + "[" + rendered_args[0] + "]"
        return base + "[" + ",".join(rendered_args) + "]"
    return t


def _infer_signature_return_type(sig: FuncSig, arg_types: list[str]) -> str:
    """Infer a return type from a normalized function signature and actual arg types."""
    bindings: dict[str, str] = {}
    for i in range(min(len(sig.arg_names), len(arg_types))):
        arg_name: str = sig.arg_names[i]
        pattern: str = ""
        if arg_name in sig.arg_types:
            pattern = sig.arg_types[arg_name]
        if pattern != "":
            _bind_type_pattern(pattern, arg_types[i], bindings)
    if sig.vararg_type != "":
        for actual in arg_types[len(sig.arg_names):]:
            _bind_type_pattern(sig.vararg_type, actual, bindings)
    return "" + normalize_type(_substitute_type_bindings(sig.return_type, bindings))


def _infer_cast_target_type(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    args = _dict_get_arr(expr, "args")
    if len(args) == 0:
        return "unknown"
    target = _jv_obj(args[0])
    if len(target) == 0:
        return "unknown"
    target_kind = _dict_get_str(target, "kind")
    if target_kind == "Name":
        type_name = _dict_get_str(target, "id")
        if type_name != "":
            return _ctx_normalize_type(type_name, ctx)
    if target_kind == "Attribute":
        owner = _dict_get_obj(target, "value")
        owner_id = _dict_get_str(owner, "id")
        attr = _dict_get_str(target, "attr")
        if owner_id != "" and attr != "":
            return _ctx_normalize_type(owner_id + "." + attr, ctx)
    target_repr = _dict_get_str(target, "repr")
    if target_repr != "":
        return _ctx_normalize_type(target_repr, ctx)
    return "unknown"


def _resolve_simple_call(expr: dict[str, JsonVal], func: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a simple Name-based function call."""
    name: str = _dict_get_str(func, "id")

    # Resolve arguments first
    _resolve_call_args(expr, ctx)

    if name == "super":
        current_cls_name: str = ctx.current_class
        if current_cls_name != "":
            current_cls: ClassSig | None = ctx.lookup_local_class(current_cls_name)
            if current_cls is not None and len(current_cls.bases) > 0:
                base_name = _ctx_normalize_type("" + current_cls.bases[0], ctx)
                if base_name != "":
                    expr["resolved_type"] = base_name
                    func["resolved_type"] = "callable"
                    expr["special_form"] = "super"
                    expr["super_of"] = current_cls_name
                    return base_name
        expr["resolved_type"] = "unknown"
        func["resolved_type"] = "callable"
        return "unknown"

    # Imported symbol?
    imp: dict[str, str] = ctx.import_symbols.get(name, {})
    if len(imp) > 0:
        return _resolve_imported_call(expr, func, name, imp, ctx)

    # Module-local function?
    local_func: FuncSig | None = ctx.lookup_local_function(name)
    if local_func is not None:
        _apply_call_arg_hints(expr, local_func.arg_names, local_func.arg_types, ctx)
        t: str = local_func.return_type
        expr["resolved_type"] = t
        func["resolved_type"] = "callable"
        return t

    # Class constructor?
    local_class: ClassSig | None = ctx.lookup_local_class(name)
    if local_class is not None:
        init_sig: FuncSig | None = local_class.methods.get("__init__")
        if init_sig is not None:
            _apply_call_arg_hints(expr, _drop_first_str(init_sig.arg_names), init_sig.arg_types, ctx)
        expr["resolved_type"] = name
        func["resolved_type"] = "type"
        return name

    # Built-in exception constructors come from pytra.built_in.error and should
    # be treated as normal class constructors when the registry provides them.
    builtin_exc_class: ClassSig | None = ctx.registry.lookup_stdlib_class(_BUILTIN_EXCEPTION_MODULE_ID, name)
    if builtin_exc_class is not None and name in _BUILTIN_EXCEPTION_TYPE_NAMES:
        init_sig2: FuncSig | None = builtin_exc_class.methods.get("__init__")
        if init_sig2 is not None:
            _apply_call_arg_hints(expr, _drop_first_str(init_sig2.arg_names), init_sig2.arg_types, ctx)
        expr["resolved_type"] = name
        func["resolved_type"] = "type"
        func["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
        expr["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
        return name

    # Fallback compatibility: unresolved built-in exception constructor still
    # points at the pure-Python runtime module, never std::exception aliases.
    if name in _BUILTIN_EXCEPTION_TYPE_NAMES:
        expr["resolved_type"] = name
        func["resolved_type"] = "type"
        func["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
        expr["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
        return name

    bound_lambda = ctx.scope.lookup_lambda(name)
    if bound_lambda is not None:
        _resolve_call_args(expr, ctx)
        callable_type2 = _refine_lambda_from_call(bound_lambda, ctx, _collect_call_arg_types(expr))
        ctx.scope.define(name, callable_type2)
        func["resolved_type"] = callable_type2
        _, callable_ret2 = _parse_callable_signature(callable_type2, ctx)
        expr["resolved_type"] = callable_ret2 if not _is_unknown_like_type(callable_ret2) else "unknown"
        return str(expr.get("resolved_type", "unknown"))

    scoped_type: str = ctx.scope.lookup(name)
    if scoped_type.startswith("callable"):
        _, callable_ret = _parse_callable_signature(scoped_type, ctx)
        expr["resolved_type"] = callable_ret if not _is_unknown_like_type(callable_ret) else "unknown"
        func["resolved_type"] = scoped_type
        return str(expr.get("resolved_type", "unknown"))

    # Built-in function (registry or known constructors)
    if name == "open" or ctx.registry.is_builtin(name):
        return _resolve_builtin_call(expr, func, name, ctx)
    # bytearray/bytes are built-in constructors not always in registry
    if name == "bytearray":
        expr["resolved_type"] = "bytearray"
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["semantic_tag"] = "core.bytearray_ctor"
        return "bytearray"
    if name == "bytes":
        expr["resolved_type"] = "bytes"
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["semantic_tag"] = "core.bytes_ctor"
        return "bytes"
    if name == "dict":
        arg_types = _collect_call_arg_types(expr)
        ret = "dict[unknown, unknown]"
        if len(arg_types) >= 1:
            src_type: str = _ctx_normalize_type(arg_types[0], ctx)
            if src_type.startswith("dict[") and src_type.endswith("]"):
                ret = src_type
        expr["resolved_type"] = ret
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["semantic_tag"] = "core.dict_ctor"
        return ret
    if name == "list":
        arg_types = _collect_call_arg_types(expr)
        ret = "list[unknown]"
        if len(arg_types) >= 1:
            src_type: str = _ctx_normalize_type(arg_types[0], ctx)
            if src_type.startswith("list["):
                ret = src_type
            elif src_type.startswith("tuple["):
                items: list[str] = extract_type_args(src_type)
                if len(items) > 0:
                    ret = "list[" + items[0] + "]"
            elif src_type == "str":
                ret = "list[str]"
        expr["resolved_type"] = ret
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["runtime_call"] = "list_ctor"
        expr["runtime_module_id"] = "pytra.core.list"
        expr["runtime_symbol"] = "list"
        expr["runtime_call_adapter_kind"] = "builtin"
        expr["semantic_tag"] = "core.list_ctor"
        return ret
    if name == "set":
        arg_types = _collect_call_arg_types(expr)
        ret = "set[unknown]"
        if len(arg_types) >= 1:
            src_type2: str = _ctx_normalize_type(arg_types[0], ctx)
            if src_type2.startswith("list[") and src_type2.endswith("]"):
                ret = "set[" + src_type2[5:-1] + "]"
            elif src_type2.startswith("set[") and src_type2.endswith("]"):
                ret = src_type2
            elif src_type2 == "str":
                ret = "set[str]"
        expr["resolved_type"] = ret
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["runtime_call"] = "set_ctor"
        expr["runtime_module_id"] = "pytra.core.set"
        expr["runtime_symbol"] = "set"
        expr["runtime_call_adapter_kind"] = "builtin"
        expr["semantic_tag"] = "core.set_ctor"
        return ret
    if name == "tuple":
        arg_types = _collect_call_arg_types(expr)
        ret = "tuple[unknown]"
        if len(arg_types) >= 1:
            src_type3: str = _ctx_normalize_type(arg_types[0], ctx)
            if src_type3.startswith("tuple[") and src_type3.endswith("]"):
                ret = src_type3
            elif src_type3.startswith("list[") and src_type3.endswith("]"):
                ret = "tuple[" + src_type3[5:-1] + "]"
            elif src_type3.startswith("set[") and src_type3.endswith("]"):
                ret = "tuple[" + src_type3[4:-1] + "]"
            elif src_type3 == "str":
                ret = "tuple[str]"
        expr["resolved_type"] = ret
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["runtime_call"] = "tuple_ctor"
        expr["runtime_module_id"] = "pytra.core.tuple"
        expr["runtime_symbol"] = "tuple"
        expr["runtime_call_adapter_kind"] = "builtin"
        expr["semantic_tag"] = "core.tuple_ctor"
        return ret

    # Unknown
    func["resolved_type"] = "unknown"
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_builtin_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    name: str,
    ctx: ResolveContext,
) -> str:
    """Resolve a built-in function call (print, len, int, etc.)."""
    if name == "bytearray":
        _resolve_call_args(expr, ctx)
        expr["resolved_type"] = "bytearray"
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["semantic_tag"] = "core.bytearray_ctor"
        return "bytearray"
    if name == "bytes":
        _resolve_call_args(expr, ctx)
        expr["resolved_type"] = "bytes"
        func["resolved_type"] = "type"
        expr["lowered_kind"] = "BuiltinCall"
        expr["semantic_tag"] = "core.bytes_ctor"
        return "bytes"
    if name == "open":
        _resolve_call_args(expr, ctx)
        resolved_open_type = "IOBase"
        args = _dict_get_arr(expr, "args")
        if len(args) >= 2:
            mode_node = _jv_obj(args[1])
            if len(mode_node) > 0 and _dict_get_str(mode_node, "kind") == "Constant":
                mode_value = ""
                if "value" in mode_node:
                    mode_value = _jv_str(mode_node["value"])
                if mode_value == "rb":
                    resolved_open_type = "BufferedReader"
                elif mode_value == "wb" or mode_value == "ab":
                    resolved_open_type = "BufferedWriter"
                elif mode_value == "r" or mode_value == "w" or mode_value == "a":
                    resolved_open_type = "TextIOWrapper"
        expr["resolved_type"] = resolved_open_type
        func["resolved_type"] = "callable"
        expr["lowered_kind"] = "BuiltinCall"
        expr["runtime_call"] = "open"
        expr["runtime_module_id"] = "pytra.core.py_runtime"
        expr["runtime_symbol"] = "open"
        expr["runtime_call_adapter_kind"] = "builtin"
        expr["semantic_tag"] = "core.open"
        ctx.used_builtin_modules.add("pytra.core.py_runtime")
        return resolved_open_type

    sig: FuncSig | None = ctx.registry.lookup_function(name)
    ret: str = "unknown"
    if sig is not None:
        _apply_call_arg_hints(expr, sig.arg_names, sig.arg_types, ctx)
        arg_types = _collect_call_arg_types(expr)
        ret = _infer_signature_return_type(sig, arg_types)
        if name == "sorted" and len(arg_types) >= 1:
            src_type = _ctx_normalize_type(arg_types[0], ctx)
            if src_type.startswith("list[") and src_type.endswith("]"):
                ret = src_type
            elif src_type.startswith("set[") and src_type.endswith("]"):
                ret = "list[" + src_type[4:-1] + "]"
            elif src_type.startswith("tuple[") and src_type.endswith("]"):
                parts = list(extract_type_args(src_type))
                if len(parts) > 0:
                    ret = "list[" + parts[0] + "]"
            elif src_type.startswith("dict[") and src_type.endswith("]"):
                parts2 = list(extract_type_args(src_type))
                if len(parts2) >= 1:
                    ret = "list[" + parts2[0] + "]"
            elif src_type == "str":
                ret = "list[str]"
        elif name == "tuple" and len(arg_types) >= 1:
            src_type2 = _ctx_normalize_type(arg_types[0], ctx)
            if src_type2.startswith("tuple[") and src_type2.endswith("]"):
                ret = src_type2
            elif src_type2.startswith("list[") and src_type2.endswith("]"):
                ret = "tuple[" + src_type2[5:-1] + "]"
            elif src_type2.startswith("set[") and src_type2.endswith("]"):
                ret = "tuple[" + src_type2[4:-1] + "]"
            elif src_type2 == "str":
                ret = "tuple[str]"

    expr["resolved_type"] = ret
    func["resolved_type"] = "callable"

    # Add runtime metadata from extern_v2
    extern_info: ExternV2 | None = sig.extern_v2 if sig is not None else None

    # isinstance/issubclass use TypePredicateCall lowered_kind
    if name == "isinstance":
        expr["lowered_kind"] = "TypePredicateCall"
        expr["predicate_kind"] = "isinstance"
        if extern_info is not None:
            expr["semantic_tag"] = extern_info.tag
        return ret
    if name == "issubclass":
        expr["lowered_kind"] = "TypePredicateCall"
        expr["predicate_kind"] = "issubclass"
        if extern_info is not None:
            expr["semantic_tag"] = extern_info.tag
        return ret

    expr["lowered_kind"] = "BuiltinCall"

    # Specialize int(str)/float(str)/str(non-str) for emitter clarity
    specialized_rc: str = ""
    arg_types: list[str] = _collect_call_arg_types(expr)
    if name == "int" and len(arg_types) > 0 and arg_types[0] == "str":
        specialized_rc = "py_int_from_str"
    elif name == "float" and len(arg_types) > 0 and arg_types[0] == "str":
        specialized_rc = "py_float_from_str"
    elif name == "str" and len(arg_types) > 0 and arg_types[0] != "str":
        specialized_rc = "py_to_string"
    elif name in ("int", "float", "bool") and len(arg_types) > 0 and arg_types[0] not in ("str", "unknown"):
        specialized_rc = "static_cast"

    if extern_info is not None:
        # runtime_call: prefer specialization, else extern_info.symbol
        rc: str = specialized_rc if specialized_rc != "" else extern_info.symbol
        expr["runtime_call"] = rc
        expr["runtime_module_id"] = extern_info.module
        expr["runtime_symbol"] = extern_info.symbol
        # Adapter kind from runtime index
        adapter: str = ctx.lookup_adapter_kind(extern_info.module, extern_info.symbol)
        if adapter == "":
            adapter = "builtin"
        expr["runtime_call_adapter_kind"] = adapter
        if extern_info.tag != "":
            expr["semantic_tag"] = extern_info.tag
        if name == "float" and len(arg_types) == 0:
            expr["semantic_tag"] = "core.float_ctor"
        # Track implicit builtin module
        ctx.used_builtin_modules.add(extern_info.module)
    elif specialized_rc != "":
        expr["runtime_call"] = specialized_rc
    else:
        # Fallback for unrecognized builtins (no extern entry, no specialization).
        # Use the Python function name as runtime_call; emitters apply builtin_prefix.
        expr["runtime_call"] = name
        expr["runtime_call_adapter_kind"] = "builtin"

    return ret


def _resolve_imported_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    local_name: str,
    imp: dict[str, str],
    ctx: ResolveContext,
) -> str:
    """Resolve a call to an imported symbol."""
    module_id: str = imp.get("module", "")
    export_name: str = imp.get("name", "")
    if export_name == "":
        export_name = local_name

    arg_types: list[str] = _collect_call_arg_types(expr)

    if module_id in ("typing", "pytra.typing") and export_name == "cast":
        ret = _infer_cast_target_type(expr, ctx)
        expr["resolved_type"] = ret
        func["resolved_type"] = "callable"
        args_raw = _dict_get_arr(expr, "args")
        if ret != "unknown":
            if len(args_raw) >= 1:
                type_arg = _jv_obj(args_raw[0])
                if len(type_arg) > 0:
                    type_arg["resolved_type"] = ret
                    type_arg["type_expr"] = _ctx_make_type_expr(ret, ctx)
            if len(args_raw) >= 2:
                value_arg = _jv_obj(args_raw[1])
                if len(value_arg) > 0:
                    value_arg["call_arg_type"] = ret
        return ret
    if module_id == "pytra.std" and export_name == "extern":
        ret = arg_types[0] if len(arg_types) > 0 else "unknown"
        expr["resolved_type"] = ret
        func["resolved_type"] = "callable"
        return ret

    # Determine return type from stdlib registry if available
    ret: str = "unknown"
    stdlib_func: FuncSig | None = ctx.registry.lookup_stdlib_function(module_id, export_name)
    stdlib_class: ClassSig | None = ctx.registry.lookup_stdlib_class(module_id, export_name)
    if stdlib_func is not None:
        _apply_call_arg_hints(expr, stdlib_func.arg_names, stdlib_func.arg_types, ctx)
        ret = _infer_signature_return_type(stdlib_func, _collect_call_arg_types(expr))
        func["resolved_type"] = "callable"
    elif stdlib_class is not None:
        init_sig: FuncSig | None = stdlib_class.methods.get("__init__")
        if init_sig is not None:
            _apply_call_arg_hints(expr, _drop_first_str(init_sig.arg_names), init_sig.arg_types, ctx)
        ret = stdlib_class.name
        func["resolved_type"] = "type"
    else:
        func["resolved_type"] = "callable"

    runtime_module: str = ctx.canonical_module_id(module_id)

    # Annotate with runtime call info if symbol exists in runtime index
    sym_doc: dict[str, JsonVal] = ctx.lookup_runtime_symbol_doc(runtime_module, export_name)
    has_runtime_entry: bool = len(sym_doc) > 0

    if has_runtime_entry:
        # Use import_symbol annotation
        short_mod: str = module_id
        if short_mod.startswith("pytra.std."):
            short_mod = short_mod[len("pytra.std."):]
        elif short_mod.startswith("pytra."):
            short_mod = ""
        if short_mod != "" and "." not in short_mod:
            qualified_call: str = short_mod + "." + export_name
        else:
            qualified_call = export_name
        expr["resolved_runtime_call"] = qualified_call
        expr["resolved_runtime_source"] = "import_symbol"
        expr["runtime_module_id"] = runtime_module
        expr["runtime_symbol"] = export_name
        grp: str = ctx.lookup_runtime_module_group(runtime_module)
        adapter: str = ctx.lookup_adapter_kind(runtime_module, export_name)
        if adapter == "":
            if grp == "built_in":
                adapter = "builtin"
            else:
                adapter = "extern_delegate"
        expr["runtime_call_adapter_kind"] = adapter

    expr["resolved_type"] = ret
    return ret


def _resolve_method_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    ctx: ResolveContext,
) -> str:
    """Resolve a method call (obj.method(...))."""
    value = _dict_get_obj(func, "value")
    attr: str = _dict_get_str(func, "attr")

    # Resolve receiver
    receiver_type: str = "unknown"
    if len(value) > 0:
        receiver_type = _resolve_expr(value, ctx)

    # Resolve arguments
    _resolve_call_args(expr, ctx)

    # Module attribute call (math.sqrt, os.path.join, etc.)
    if len(value) > 0:
        mod_id = _resolve_module_expr_id(value, ctx)
        if mod_id != "":
            value["resolved_type"] = "module"
            receiver_name: str = _module_expr_display_name(value, mod_id)
            return _resolve_module_attr_call(expr, func, receiver_name, mod_id, attr, ctx)

    # Container method call (list.append, str.split, etc.)
    owner_base: str = _resolve_owner_base_type(value, receiver_type, ctx)
    method_sig: FuncSig | None = ctx.registry.lookup_method(owner_base, attr)
    if method_sig is not None:
        hinted_arg_types = method_sig.arg_types
        container_cls: ClassSig | None = ctx.registry.classes.get(owner_base)
        if container_cls is not None:
            hinted_arg_types = _substitute_arg_types(method_sig.arg_types, receiver_type, container_cls)
        _apply_call_arg_hints(expr, _drop_first_str(method_sig.arg_names), hinted_arg_types, ctx)
        return _resolve_container_method_call(expr, func, receiver_type, owner_base, attr, method_sig, ctx)

    cls, msig = _lookup_method_sig(owner_base, attr, ctx)
    if cls is not None and msig is not None and "property" not in msig.decorators:
        hinted_arg_types = _substitute_arg_types(msig.arg_types, receiver_type, cls)
        _apply_call_arg_hints(expr, _drop_first_str(msig.arg_names), hinted_arg_types, ctx)
        ret: str = _ctx_normalize_type(_substitute_type_params(msig.return_type, receiver_type, cls), ctx)
        expr["resolved_type"] = ret
        func["resolved_type"] = "callable"
        _attach_stdlib_method_runtime_metadata(expr, cls, msig, owner_base, attr, ctx)
        if "staticmethod" in msig.decorators:
            expr["call_dispatch_kind"] = "static_method"
        return ret

    # Fallback
    func["resolved_type"] = "unknown"
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_module_attr_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    receiver_name: str,
    module_id: str,
    attr: str,
    ctx: ResolveContext,
) -> str:
    """Resolve a module.attr() call (e.g., math.sqrt(x))."""
    canonical: str = ctx.canonical_module_id(module_id)
    stdlib_func: FuncSig | None = ctx.registry.lookup_stdlib_function(canonical, attr)
    stdlib_class: ClassSig | None = ctx.registry.lookup_stdlib_class(canonical, attr)
    extern_info: ExternV2 | None = None
    if stdlib_func is not None:
        extern_info = stdlib_func.extern_v2
    elif stdlib_class is not None:
        extern_info = stdlib_class.extern_v2

    # Determine return type
    ret: str = "unknown"
    if stdlib_func is not None:
        _apply_call_arg_hints(expr, stdlib_func.arg_names, stdlib_func.arg_types, ctx)
        ret = _infer_signature_return_type(stdlib_func, _collect_call_arg_types(expr))
        func["resolved_type"] = "callable"
    elif stdlib_class is not None:
        init_sig: FuncSig | None = stdlib_class.methods.get("__init__")
        if init_sig is not None:
            _apply_call_arg_hints(expr, _drop_first_str(init_sig.arg_names), init_sig.arg_types, ctx)
        ret = stdlib_class.name
        func["resolved_type"] = "type"
    else:
        func["resolved_type"] = "callable"

    expr["resolved_type"] = ret

    # Runtime metadata from extern_v2
    if extern_info is not None:
        expr["resolved_runtime_call"] = receiver_name + "." + attr
        expr["resolved_runtime_source"] = "module_attr"
        runtime_module_id = extern_info.module if extern_info.module != "" else canonical
        runtime_symbol = extern_info.symbol if extern_info.symbol != "" else attr
        expr["runtime_module_id"] = runtime_module_id
        expr["runtime_symbol"] = runtime_symbol
        # Adapter kind from runtime index
        adapter: str = ctx.lookup_adapter_kind(runtime_module_id, runtime_symbol)
        if adapter != "":
            expr["runtime_call_adapter_kind"] = adapter
        if extern_info.tag != "":
            expr["semantic_tag"] = extern_info.tag
    else:
        # Fallback for unresolved stdlib calls
        expr["resolved_runtime_call"] = receiver_name + "." + attr
        expr["resolved_runtime_source"] = "module_attr"
        expr["runtime_module_id"] = canonical
        expr["runtime_symbol"] = attr
        adapter2: str = ctx.lookup_adapter_kind(canonical, attr)
        if adapter2 != "":
            expr["runtime_call_adapter_kind"] = adapter2
        expr["semantic_tag"] = "stdlib.method." + attr

    return ret


def _normalize_method_runtime_call(owner_base: str, method: str, raw: str) -> str:
    """Pass through runtime_call as-is. Emitters resolve via mapping.json."""
    return raw


def _resolve_container_method_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    receiver_type: str,
    owner_base: str,
    method: str,
    method_sig: FuncSig,
    ctx: ResolveContext,
) -> str:
    """Resolve a container method call (list.append, str.split, etc.)."""
    # Substitute type parameters
    cls: ClassSig | None = ctx.registry.classes.get(owner_base)
    ret: str = method_sig.return_type
    if cls is not None:
        ret = _substitute_type_params(ret, receiver_type, cls)
    ret = _ctx_normalize_type(ret, ctx)

    args_raw = expr.get("args")
    if (
        owner_base == "dict"
        and method == "get"
        and ret in ("object", "Obj", "Any")
        and isinstance(args_raw, list)
        and len(args_raw) >= 2
        and isinstance(args_raw[1], dict)
    ):
        default_rt = _ctx_normalize_type(str(args_raw[1].get("resolved_type", "")), ctx)
        if default_rt not in ("", "unknown", "object", "Obj", "Any"):
            ret = default_rt
            args_raw[1]["call_arg_type"] = ret

    expr["resolved_type"] = ret
    func["resolved_type"] = "callable"

    # Runtime owner: the receiver expression
    value = func.get("value")
    if isinstance(value, dict) and method_sig.self_is_mutable:
        value["borrow_kind"] = "mutable_ref"
    if isinstance(value, dict):
        owner_copy: JsonVal = deep_copy_json(value)
        expr["runtime_owner"] = owner_copy
    if method_sig.self_is_mutable:
        meta_val = expr.get("meta")
        meta: dict[str, JsonVal] = meta_val if isinstance(meta_val, dict) else {}
        expr["meta"] = meta
        meta["mutates_receiver"] = True

    # Runtime metadata from extern_v2 (正本)
    method_extern_info: ExternV2 | None = method_sig.extern_v2
    if method_extern_info is not None and method_extern_info.module != "":
        mod = method_extern_info.module
        runtime_call_name = method_extern_info.symbol
    else:
        # Fallback: owner_base.method pattern
        mod = _default_container_module(owner_base)
        runtime_call_name = owner_base + "." + method
    sym: str = runtime_call_name  # e.g., "list.append" or "str.join"
    # Normalize runtime_call: str.strip → py_strip, str.join → py_join etc.
    normalized_rc: str = _normalize_method_runtime_call(owner_base, method, runtime_call_name)
    expr["lowered_kind"] = "BuiltinCall"
    expr["runtime_call"] = normalized_rc
    if mod != "":
        expr["runtime_module_id"] = mod
    expr["runtime_symbol"] = sym
    adapter: str = "builtin"
    expr["runtime_call_adapter_kind"] = adapter
    # semantic_tag from extern_v2 or fallback
    if method_extern_info is not None and method_extern_info.tag != "":
        expr["semantic_tag"] = method_extern_info.tag
    else:
        expr["semantic_tag"] = "stdlib.method." + method

    # yields_dynamic for methods that can return None/dynamic values
    if (owner_base == "dict" and method == "get") or \
       (owner_base == "dict" and method == "pop") or \
       (owner_base == "dict" and method == "setdefault") or \
       (owner_base == "list" and method == "pop"):
        expr["yields_dynamic"] = True

    return ret


def _default_container_module(owner_base: str) -> str:
    """Fallback runtime module for container types (when no extern_v2)."""
    if owner_base == "list":
        return "pytra.core.list"
    if owner_base == "dict":
        return "pytra.core.dict"
    if owner_base == "set":
        return "pytra.core.set"
    if owner_base == "str":
        return "pytra.core.str"
    if owner_base == "tuple":
        return "pytra.core.tuple"
    if owner_base == "deque":
        return "pytra.std.collections"
    return ""


def _substitute_type_params(ret_type: str, concrete_type: str, cls: ClassSig) -> str:
    """Substitute generic type parameters (T, K, V) with concrete types."""
    if len(cls.template_params) == 0:
        return ret_type

    type_args: list[str] = extract_type_args(concrete_type)
    if len(type_args) == 0:
        return ret_type

    result: str = ret_type
    for i in range(min(len(cls.template_params), len(type_args))):
        param: str = cls.template_params[i]
        arg: str = type_args[i]
        result = result.replace(param, arg)

    return result


def _substitute_arg_types(arg_types: dict[str, str], concrete_type: str, cls: ClassSig) -> dict[str, str]:
    substituted: dict[str, str] = {}
    for arg_name, arg_type in arg_types.items():
        if isinstance(arg_name, str) and isinstance(arg_type, str):
            substituted[arg_name] = _substitute_type_params(arg_type, concrete_type, cls)
    return substituted


def _resolve_attribute(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    attr_val = expr.get("attr")
    attr: str = str(attr_val) if isinstance(attr_val, str) else ""

    receiver_type: str = "unknown"
    if isinstance(value, dict):
        receiver_type = _resolve_expr(value, ctx)

    if attr == "__name__" and isinstance(value, dict) and value.get("kind") == "Call":
        func_node = value.get("func")
        if isinstance(func_node, dict) and func_node.get("kind") == "Name" and func_node.get("id") == "type":
            expr["resolved_type"] = "str"
            return "str"

    # Module-level attribute access (e.g., math.pi, os.path)
    if isinstance(value, dict):
        mod_id: str = _resolve_module_expr_id(value, ctx)
        if mod_id != "":
            canonical: str = ctx.canonical_module_id(mod_id)
            value["resolved_type"] = "module"
            promoted_module: str = _resolve_module_member_module(canonical, attr, ctx)
            if promoted_module != "":
                expr["resolved_type"] = "module"
                expr["runtime_module_id"] = promoted_module
                return "module"
            t: str = _infer_module_attr_type(canonical, attr, ctx)
            if t == "unknown":
                if ctx.registry.lookup_stdlib_class(canonical, attr) is not None:
                    t = "type"
                elif ctx.registry.lookup_stdlib_function(canonical, attr) is not None:
                    t = "callable"
            expr["resolved_type"] = t
            sym_doc: dict[str, JsonVal] = ctx.lookup_runtime_symbol_doc(canonical, attr)
            if len(sym_doc) > 0:
                expr["runtime_module_id"] = canonical
                expr["runtime_symbol"] = attr
                dispatch = sym_doc.get("dispatch")
                if isinstance(dispatch, str) and dispatch != "":
                    expr["runtime_symbol_dispatch"] = dispatch
                adapter = ctx.lookup_adapter_kind(canonical, attr)
                if adapter != "":
                    expr["runtime_call_adapter_kind"] = adapter
                semantic_tag = sym_doc.get("semantic_tag")
                if isinstance(semantic_tag, str) and semantic_tag != "":
                    expr["semantic_tag"] = semantic_tag
            return t

    owner_base: str = _resolve_owner_base_type(value, receiver_type, ctx) if isinstance(value, dict) else ""
    for class_name in _iter_class_hierarchy(owner_base, ctx):
        cls_sig: ClassSig | None = _lookup_any_class(class_name, ctx)
        if cls_sig is None:
            continue
        if attr in cls_sig.fields:
            field_type: str = _ctx_normalize_type(_substitute_type_params(cls_sig.fields[attr], receiver_type, cls_sig), ctx)
            expr["resolved_type"] = field_type
            return field_type
        property_sig: FuncSig | None = cls_sig.methods.get(attr)
        if property_sig is not None and "property" in property_sig.decorators:
            prop_type: str = _ctx_normalize_type(_substitute_type_params(property_sig.return_type, receiver_type, cls_sig), ctx)
            expr["resolved_type"] = prop_type
            expr["attribute_access_kind"] = "property_getter"
            return prop_type

    expr["resolved_type"] = "unknown"
    return "unknown"


def _infer_module_attr_type(canonical: str, attr: str, ctx: ResolveContext) -> str:
    """Infer type of a module-level attribute (e.g., math.pi)."""
    # Look up in stdlib registry
    var_sig: VarSig | None = ctx.registry.lookup_stdlib_variable(canonical, attr)
    if var_sig is not None:
        return var_sig.var_type
    return "unknown"


def _resolve_module_member_module(module_id: str, attr: str, ctx: ResolveContext) -> str:
    """Resolve nested module references like os.path -> pytra.std.os_path."""
    if module_id == "" or attr == "":
        return ""
    candidates: list[str] = [module_id + "." + attr, module_id + "_" + attr]
    seen: set[str] = set()
    for candidate in candidates:
        normalized: str = ctx.canonical_module_id(candidate)
        if normalized == "" or normalized in seen:
            continue
        seen.add(normalized)
        if ctx.runtime_module_exists(normalized) or normalized in ctx.registry.stdlib_modules:
            return normalized
    return ""


def _resolve_module_expr_id(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve an expression that denotes a module object to its module_id."""
    runtime_module_id = expr.get("runtime_module_id")
    resolved_type = expr.get("resolved_type")
    if isinstance(runtime_module_id, str) and runtime_module_id != "" and resolved_type == "module":
        return ctx.canonical_module_id(runtime_module_id)

    kind = expr.get("kind")
    if kind == "Name":
        name = expr.get("id")
        if isinstance(name, str):
            mod_id: str = ctx.import_modules.get(name, "")
            if mod_id != "":
                canonical = ctx.canonical_module_id(mod_id)
                expr["resolved_type"] = "module"
                expr["runtime_module_id"] = canonical
                return canonical
        return ""

    if kind == "Attribute":
        value = expr.get("value")
        attr = expr.get("attr")
        if isinstance(value, dict) and isinstance(attr, str):
            parent_mod = _resolve_module_expr_id(value, ctx)
            if parent_mod != "":
                promoted = _resolve_module_member_module(parent_mod, attr, ctx)
                if promoted != "":
                    expr["resolved_type"] = "module"
                    expr["runtime_module_id"] = promoted
                    return promoted
        return ""

    return ""


def _module_expr_display_name(expr: dict[str, JsonVal], module_id: str) -> str:
    """Best-effort label for diagnostics/runtime-call strings of module expressions."""
    kind = expr.get("kind")
    if kind == "Name":
        name = expr.get("id")
        if isinstance(name, str) and name != "":
            return name
    if kind == "Attribute":
        attr = expr.get("attr")
        if isinstance(attr, str) and attr != "":
            return attr
    tail = module_id.rsplit(".", 1)[-1]
    return tail if tail != "" else module_id


def _resolve_subscript(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    slice_node = expr.get("slice")

    vt: str = "unknown"
    if isinstance(value, dict):
        vt = _resolve_expr(value, ctx)
    if vt.endswith(" | None"):
        vt_inner: str = vt[:-7].strip()
        if vt_inner.startswith(("list[", "dict[", "tuple[")) or vt_inner in ("str", "bytes", "bytearray"):
            vt = vt_inner
    elif vt.endswith("|None"):
        vt_inner2: str = vt[:-6].strip()
        if vt_inner2.startswith(("list[", "dict[", "tuple[")) or vt_inner2 in ("str", "bytes", "bytearray"):
            vt = vt_inner2
    is_slice: bool = False
    if isinstance(slice_node, dict):
        _resolve_expr(slice_node, ctx)
        if slice_node.get("kind") == "Slice":
            is_slice = True

    # Slice subscript: list[T][a:b] → list[T], str[a:b] → str
    if is_slice and isinstance(slice_node, dict):
        expr["resolved_type"] = vt
        expr["lowered_kind"] = "SliceExpr"
        # Promote Slice fields to Subscript (golden convention)
        # Only include non-null values
        for sk in ("lower", "upper", "step"):
            sv = slice_node.get(sk)
            if sv is not None:
                expr[sk] = sv
        return vt

    # list[T][i] → T
    if vt.startswith("list[") and vt.endswith("]"):
        elem: str = vt[5:-1]
        expr["resolved_type"] = elem
        return elem

    # dict[K,V][k] → V
    if vt.startswith("dict[") and vt.endswith("]"):
        inner: str = vt[5:-1]
        args: list[str] = extract_type_args(vt)
        if len(args) >= 2:
            expr["resolved_type"] = args[1]
            return args[1]

    # str[i] → str
    if vt == "str":
        expr["resolved_type"] = "str"
        return "str"

    # bytes[i] → uint8, bytearray[i] → uint8
    if vt in ("bytes", "bytearray"):
        expr["resolved_type"] = "uint8"
        return "uint8"

    # tuple[...][i] → depends on index
    if vt.startswith("tuple[") and vt.endswith("]"):
        args2: list[str] = extract_type_args(vt)
        # If constant index, return that element type
        if isinstance(slice_node, dict) and slice_node.get("kind") == "Constant":
            idx = slice_node.get("value")
            if isinstance(idx, int) and 0 <= idx < len(args2):
                expr["resolved_type"] = args2[idx]
                return args2[idx]
        if len(args2) > 0:
            expr["resolved_type"] = args2[0]
            return args2[0]

    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_list(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    elem_type: str = "unknown"
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                elem_type = _merge_literal_type(elem_type, t)
    if elem_type != "unknown":
        result: str = "list[" + elem_type + "]"
    else:
        result = "list[unknown]"
    if isinstance(elems, list):
        target_base = extract_base_type(elem_type)
        for e2 in elems:
            if not isinstance(e2, dict):
                continue
            current = str(e2.get("resolved_type", ""))
            current_base = extract_base_type(current)
            if (
                current in ("", "unknown", "list[unknown]", "set[unknown]", "dict[unknown,unknown]")
                or (target_base != "" and current_base == target_base and ("[" not in current or "unknown" in current))
            ):
                e2["resolved_type"] = elem_type
    expr["resolved_type"] = result
    return result


def _resolve_dict(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    kt: str = "unknown"
    vt: str = "unknown"
    # EAST1 uses "entries" format: [{key: ..., value: ...}, ...]
    entries = expr.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                key_node = entry.get("key")
                val_node = entry.get("value")
                if isinstance(key_node, dict):
                    t: str = _resolve_expr(key_node, ctx)
                    kt = _merge_literal_type(kt, t)
                if isinstance(val_node, dict):
                    t2: str = _resolve_expr(val_node, ctx)
                    vt = _merge_literal_type(vt, t2)
    else:
        # Fallback: separate keys/values arrays
        keys = expr.get("keys")
        values = expr.get("values")
        if isinstance(keys, list):
            for k in keys:
                if isinstance(k, dict):
                    t3: str = _resolve_expr(k, ctx)
                    kt = _merge_literal_type(kt, t3)
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict):
                    t4: str = _resolve_expr(v, ctx)
                    vt = _merge_literal_type(vt, t4)
    result: str = "dict[" + kt + "," + vt + "]"
    expr["resolved_type"] = result
    return result


def _node_dict_or_empty(value: JsonVal) -> dict[str, JsonVal]:
    if isinstance(value, dict):
        return value
    return {}


def _resolve_set(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    elem_type: str = "unknown"
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                elem_type = _merge_literal_type(elem_type, t)
    result: str = "set[" + elem_type + "]"
    expr["resolved_type"] = result
    return result


def _resolve_tuple(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    types: list[str] = []
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                types.append(t)
    if len(types) > 0:
        result: str = "tuple[" + ", ".join(types) + "]"
    else:
        result = "tuple[]"
    expr["resolved_type"] = result
    return result


def _resolve_ifexp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    test = expr.get("test")
    body = expr.get("body")
    orelse = expr.get("orelse")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    bt: str = "unknown"
    ot: str = "unknown"
    if isinstance(body, dict):
        bt = _resolve_expr(body, ctx)
    if isinstance(orelse, dict):
        ot = _resolve_expr(orelse, ctx)
    merged, narrowed_body, narrowed_orelse = _narrow_ifexp_branch_type(test, body, orelse, bt, ot)
    if isinstance(body, dict) and not _is_unknown_like_type(narrowed_body):
        body["resolved_type"] = narrowed_body
    if isinstance(orelse, dict) and not _is_unknown_like_type(narrowed_orelse):
        orelse["resolved_type"] = narrowed_orelse
    merged_resolved = _merge_ifexp_result_type(narrowed_body, narrowed_orelse)
    if not _is_unknown_like_type(merged_resolved):
        merged = merged_resolved
    expr["resolved_type"] = merged
    return merged


def _resolve_listcomp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    generators = expr.get("generators")
    comp_scope: Scope = ctx.scope.child()
    old_scope: Scope = ctx.scope

    if isinstance(generators, list):
        for gen in generators:
            if isinstance(gen, dict):
                iter_expr = gen.get("iter")
                if isinstance(iter_expr, dict):
                    # Convert range() to RangeExpr in comprehension context
                    if _is_range_call(iter_expr):
                        _convert_call_to_range_expr(iter_expr, ctx)
                        it = iter_expr.get("resolved_type")
                        it = str(it) if isinstance(it, str) else "list[int64]"
                    else:
                        it = _resolve_expr(iter_expr, ctx)
                    # Extract element type from iterable
                    elem: str = "unknown"
                    if it.startswith("list[") and it.endswith("]"):
                        elem = it[5:-1]
                    elif it.startswith("set[") and it.endswith("]"):
                        elem = it[4:-1]
                    elif it == "str":
                        elem = "str"
                    elif it in ("bytes", "bytearray", "list[uint8]"):
                        elem = "int64"
                    elif it == "list[int64]" or it.startswith("RangeExpr"):
                        elem = "int64"
                    target = gen.get("target")
                    if isinstance(target, dict):
                        _bind_comp_target(comp_scope, target, elem)
                # Resolve filter conditions
                ifs = gen.get("ifs")
                if isinstance(ifs, list):
                    ctx.scope = comp_scope
                    for cond in ifs:
                        if isinstance(cond, dict):
                            _resolve_expr(cond, ctx)
                    ctx.scope = old_scope

    # Resolve elt in comprehension scope
    ctx.scope = comp_scope
    elt = expr.get("elt")
    elt_type: str = "unknown"
    if isinstance(elt, dict):
        elt_type = _resolve_expr(elt, ctx)
    ctx.scope = old_scope

    result: str = "list[" + elt_type + "]"
    expr["resolved_type"] = result
    return result


def _resolve_setcomp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a set comprehension {elt for ...}."""
    generators = expr.get("generators")
    comp_scope: Scope = ctx.scope.child()
    old_scope: Scope = ctx.scope
    if isinstance(generators, list):
        for gen in generators:
            if isinstance(gen, dict):
                iter_expr = gen.get("iter")
                if isinstance(iter_expr, dict):
                    if _is_range_call(iter_expr):
                        _convert_call_to_range_expr(iter_expr, ctx)
                        it = "list[int64]"
                    else:
                        it = _resolve_expr(iter_expr, ctx)
                    elem: str = "unknown"
                    if it.startswith("list[") and it.endswith("]"):
                        elem = it[5:-1]
                    elif it == "str":
                        elem = "str"
                    elif it in ("bytes", "bytearray", "list[uint8]"):
                        elem = "int64"
                    target = gen.get("target")
                    if isinstance(target, dict):
                        _bind_comp_target(comp_scope, target, elem)
                ifs = gen.get("ifs")
                if isinstance(ifs, list):
                    ctx.scope = comp_scope
                    for cond in ifs:
                        if isinstance(cond, dict):
                            _resolve_expr(cond, ctx)
                    ctx.scope = old_scope
    ctx.scope = comp_scope
    elt = expr.get("elt")
    elt_type: str = "unknown"
    if isinstance(elt, dict):
        elt_type = _resolve_expr(elt, ctx)
    ctx.scope = old_scope
    result: str = "set[" + elt_type + "]"
    expr["resolved_type"] = result
    return result


def _resolve_dictcomp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a dict comprehension {k: v for ...}."""
    generators = expr.get("generators")
    comp_scope: Scope = ctx.scope.child()
    old_scope: Scope = ctx.scope
    if isinstance(generators, list):
        for gen in generators:
            if isinstance(gen, dict):
                iter_expr = gen.get("iter")
                if isinstance(iter_expr, dict):
                    if _is_range_call(iter_expr):
                        _convert_call_to_range_expr(iter_expr, ctx)
                        it = "list[int64]"
                    else:
                        it = _resolve_expr(iter_expr, ctx)
                    elem: str = "unknown"
                    if it.startswith("list[") and it.endswith("]"):
                        elem = it[5:-1]
                    elif it == "str":
                        elem = "str"
                    elif it in ("bytes", "bytearray", "list[uint8]"):
                        elem = "int64"
                    target = gen.get("target")
                    if isinstance(target, dict):
                        _bind_comp_target(comp_scope, target, elem)
                ifs = gen.get("ifs")
                if isinstance(ifs, list):
                    ctx.scope = comp_scope
                    for cond in ifs:
                        if isinstance(cond, dict):
                            _resolve_expr(cond, ctx)
                    ctx.scope = old_scope
    ctx.scope = comp_scope
    key_node = expr.get("key")
    val_node = expr.get("value")
    kt: str = "unknown"
    vt: str = "unknown"
    if isinstance(key_node, dict):
        kt = _resolve_expr(key_node, ctx)
    if isinstance(val_node, dict):
        vt = _resolve_expr(val_node, ctx)
    ctx.scope = old_scope
    result: str = "dict[" + kt + "," + vt + "]"
    expr["resolved_type"] = result
    return result


def _resolve_lambda(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a Lambda expression."""
    return _refine_lambda_from_call(expr, ctx, [])


def _resolve_slice(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a Slice node (lower:upper:step)."""
    for key in ("lower", "upper", "step"):
        child = expr.get(key)
        if isinstance(child, dict) and "kind" in child:
            _resolve_expr(child, ctx)
    # Slice itself doesn't have a resolved_type in the same sense
    return "slice"


def _resolve_starred(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    if isinstance(value, dict):
        vt: str = _resolve_expr(value, ctx)
        expr["resolved_type"] = vt
        return vt
    expr["resolved_type"] = "unknown"
    return "unknown"


# ---------------------------------------------------------------------------
# Statement resolution
# ---------------------------------------------------------------------------

def _resolve_stmt(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve types within a statement."""
    kind_val = stmt.get("kind")
    kind: str = str(kind_val) if isinstance(kind_val, str) else ""

    if kind == "FunctionDef":
        _resolve_function_def(stmt, ctx)
    elif kind == "ClassDef":
        _resolve_class_def(stmt, ctx)
    elif kind == "TypeAlias":
        value_raw = stmt.get("value")
        if isinstance(value_raw, str):
            stmt["value"] = _ctx_normalize_type(value_raw, ctx)
    elif kind == "Assign":
        _resolve_assign(stmt, ctx)
    elif kind == "AnnAssign":
        _resolve_ann_assign(stmt, ctx)
    elif kind == "AugAssign":
        _resolve_aug_assign(stmt, ctx)
    elif kind == "Return":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "Expr":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "If":
        _resolve_if(stmt, ctx)
    elif kind == "While":
        _resolve_while(stmt, ctx)
    elif kind == "For":
        _resolve_for(stmt, ctx)
    elif kind == "ForRange":
        _resolve_for_range(stmt, ctx)
    elif kind == "Try":
        _resolve_try(stmt, ctx)
    elif kind == "With":
        _resolve_with(stmt, ctx)
    elif kind == "Yield":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "Import":
        pass  # Metadata already records imported module aliases.
    elif kind == "ImportFrom":
        pass  # Already processed during pre-scan
    elif kind == "Raise":
        exc = stmt.get("exc")
        if isinstance(exc, dict):
            _resolve_expr(exc, ctx)
        # Exception type name in handler
        exc_type = stmt.get("type")
        if isinstance(exc_type, dict) and exc_type.get("kind") == "Name":
            exc_name = exc_type.get("id")
            if isinstance(exc_name, str):
                exc_type["resolved_type"] = exc_name
    elif kind == "Swap":
        # Swap: resolve left/right but keep borrow_kind as "value"
        left = stmt.get("left")
        right = stmt.get("right")
        if isinstance(left, dict):
            _resolve_expr(left, ctx)
            left["borrow_kind"] = "value"
        if isinstance(right, dict):
            _resolve_expr(right, ctx)
            right["borrow_kind"] = "value"
    elif kind == "Break" or kind == "Continue" or kind == "Pass":
        pass
    elif kind == "Delete":
        targets = stmt.get("targets")
        if isinstance(targets, list):
            for t in targets:
                if isinstance(t, dict):
                    _resolve_expr(t, ctx)
    else:
        # Generic: resolve all child expressions
        _resolve_children(stmt, ctx)


def _resolve_children(node: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Recursively resolve any child expression nodes."""
    for key in node:
        val = node[key]
        if isinstance(val, dict) and "kind" in val:
            kind_val = val.get("kind")
            if isinstance(kind_val, str):
                # Check if it's an expression or statement
                if kind_val in {"FunctionDef", "ClassDef", "Assign", "AnnAssign", "AugAssign",
                                "Return", "Expr", "If", "While", "For", "ForRange", "Try", "With",
                                "Import",
                                "Break", "Continue", "Pass", "Yield", "ImportFrom", "Raise", "Delete"}:
                    _resolve_stmt(val, ctx)
                else:
                    _resolve_expr(val, ctx)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "kind" in item:
                    kind_val2 = item.get("kind")
                    if isinstance(kind_val2, str):
                        if kind_val2 in {"FunctionDef", "ClassDef", "Assign", "AnnAssign",
                                          "AugAssign", "Return", "Expr", "If", "While", "For",
                                          "ForRange", "Try", "With", "Import", "Break", "Continue", "Pass",
                                          "Yield", "ImportFrom", "Raise", "Delete"}:
                            _resolve_stmt(item, ctx)
                        else:
                            _resolve_expr(item, ctx)


def _resolve_function_def(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a FunctionDef: normalize types, compute arg_usage, etc."""
    # Normalize arg_types
    arg_types_raw = stmt.get("arg_types")
    arg_types: dict[str, str] = {}
    if isinstance(arg_types_raw, dict):
        for k, v in arg_types_raw.items():
            if isinstance(v, str):
                norm: str = _ctx_normalize_type(v, ctx)
                arg_types[k] = norm
                arg_types_raw[k] = norm

    # Normalize return_type
    ret_raw = stmt.get("return_type")
    ret: str = "unknown"
    if isinstance(ret_raw, str):
        ret = _ctx_normalize_type(ret_raw, ctx)
        stmt["return_type"] = ret

    # Normalize vararg_type
    vararg_type_raw = stmt.get("vararg_type")
    if isinstance(vararg_type_raw, str):
        vararg_type: str = _ctx_normalize_type(vararg_type_raw, ctx)
        stmt["vararg_type"] = vararg_type
        stmt["vararg_type_expr"] = make_type_expr(vararg_type)

    # Build arg_type_exprs / return_type_expr
    # Class methods get null (type info comes from class definition)
    ate_key_exists: bool = "arg_type_exprs" in stmt
    ate_is_null: bool = ate_key_exists and stmt.get("arg_type_exprs") is None
    if ate_is_null or ctx.in_class:
        pass  # Don't add the field — golden omits it for class methods
    else:
        arg_type_exprs: dict[str, JsonVal] = {}
        for k, t in arg_types.items():
            arg_type_exprs[k] = make_type_expr(t)
        stmt["arg_type_exprs"] = arg_type_exprs

    rte_key_exists: bool = "return_type_expr" in stmt
    rte_is_null: bool = rte_key_exists and stmt.get("return_type_expr") is None
    if rte_is_null or ctx.in_class:
        pass  # Don't add the field — golden omits it for class methods
    else:
        stmt["return_type_expr"] = make_type_expr(ret)

    # Resolve default values
    defaults_raw = stmt.get("arg_defaults")
    if isinstance(defaults_raw, dict):
        for dk, dv in defaults_raw.items():
            if isinstance(dv, dict) and "kind" in dv:
                _resolve_expr(dv, ctx)
                param_type = arg_types.get(dk, "")
                if param_type != "":
                    _apply_default_annotation_type(dv, param_type, ctx)

    # Compute arg_usage
    arg_order_raw = stmt.get("arg_order")
    arg_order: list[str] = []
    if isinstance(arg_order_raw, list):
        for a in arg_order_raw:
            if isinstance(a, str):
                arg_order.append(a)

    arg_usage: dict[str, str] = _compute_arg_usage(arg_order, stmt)
    stmt["arg_usage"] = arg_usage

    # Create function scope
    fn_scope: Scope = ctx.scope.child()
    for name, typ in arg_types.items():
        fn_scope.define(name, typ)

    # Normalize yield_value_type
    yvt_raw = stmt.get("yield_value_type")
    if isinstance(yvt_raw, str) and yvt_raw != "unknown":
        stmt["yield_value_type"] = _ctx_normalize_type(yvt_raw, ctx)

    # Resolve body in function scope
    old_scope: Scope = ctx.scope
    old_params: set[str] = ctx.current_params
    old_current_function: str = ctx.current_function
    ctx.scope = fn_scope
    ctx.current_params = set(arg_order)
    ctx.current_function = str(stmt.get("name")) if isinstance(stmt.get("name"), str) else ""
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    ctx.scope = old_scope
    ctx.current_params = old_params
    ctx.current_function = old_current_function

    refined_callable_params: dict[str, str] = {}
    for arg_name, arg_type in arg_types.items():
        if not _callable_type_needs_refinement(arg_type, ctx):
            continue
        callable_sig = _infer_callable_param_signature(stmt, arg_name, ctx)
        if callable_sig == "":
            continue
        final_sig = callable_sig
        # Preserve `| None` from the original declaration so a refined
        # callable type does not silently strip the parameter's
        # optionality — otherwise a defaulted `None` argument becomes
        # ill-typed at every call site.
        if _type_text_contains_none(arg_type) and not _type_text_contains_none(final_sig):
            final_sig = final_sig + " | None"
        arg_types[arg_name] = final_sig
        refined_callable_params[arg_name] = final_sig
        if isinstance(arg_types_raw, dict):
            arg_types_raw[arg_name] = final_sig
    if len(refined_callable_params) > 0:
        arg_type_exprs = stmt.get("arg_type_exprs")
        if isinstance(arg_type_exprs, dict):
            for arg_name2, callable_sig2 in refined_callable_params.items():
                arg_type_exprs[arg_name2] = make_type_expr(callable_sig2)
        _refresh_callable_param_calls(body, refined_callable_params, ctx)


def _compute_arg_usage(arg_order: list[str], func: dict[str, JsonVal]) -> dict[str, str]:
    """Compute arg_usage: readonly or reassigned for each parameter."""
    usage: dict[str, str] = {}
    for name in arg_order:
        usage[name] = "readonly"

    # Collect reassigned names in function body
    body = func.get("body")
    if isinstance(body, list):
        reassigned: set[str] = set()
        _collect_reassigned(body, reassigned)
        for name in arg_order:
            if name in reassigned:
                usage[name] = "reassigned"

    return usage


def _collect_reassigned(stmts: list[JsonVal], out: set[str]) -> None:
    """Collect variable names that are reassigned in statements."""
    mutating_methods: set[str] = {
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "update",
        "add",
        "discard",
        "setdefault",
        "sort",
        "reverse",
    }
    for s in stmts:
        if not isinstance(s, dict):
            continue
        kind = s.get("kind")
        if kind == "Assign":
            targets = s.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict) and t.get("kind") == "Name":
                        name = t.get("id")
                        if isinstance(name, str):
                            out.add(name)
            else:
                target = s.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    name2 = target.get("id")
                    if isinstance(name2, str):
                        out.add(name2)
                _collect_mutated_base_name(target, out)
        elif kind == "AugAssign":
            target3 = s.get("target")
            if isinstance(target3, dict) and target3.get("kind") == "Name":
                name3 = target3.get("id")
                if isinstance(name3, str):
                    out.add(name3)
            _collect_mutated_base_name(target3, out)
        elif kind == "AnnAssign":
            target4 = s.get("target")
            if isinstance(target4, dict) and target4.get("kind") == "Name":
                name4 = target4.get("id")
                if isinstance(name4, str):
                    out.add(name4)
            _collect_mutated_base_name(target4, out)
        elif kind == "Expr":
            value = s.get("value")
            if isinstance(value, dict) and value.get("kind") == "Call":
                func = value.get("func")
                if isinstance(func, dict) and func.get("kind") == "Attribute":
                    method = func.get("attr")
                    owner = func.get("value")
                    if isinstance(method, str) and method in mutating_methods:
                        _collect_mutated_base_name(owner, out)

        # Recurse into blocks
        for block_key in ["body", "orelse", "finalbody", "handlers"]:
            block = s.get(block_key)
            if isinstance(block, list):
                _collect_reassigned(block, out)


def _collect_mutated_base_name(target: JsonVal, out: set[str]) -> None:
    if not isinstance(target, dict):
        return
    kind = target.get("kind")
    if kind == "Name":
        name0 = target.get("id")
        if isinstance(name0, str):
            out.add(name0)
    elif kind == "Subscript":
        value = target.get("value")
        if isinstance(value, dict) and value.get("kind") == "Name":
            name = value.get("id")
            if isinstance(name, str):
                out.add(name)
    elif kind == "Attribute":
        value2 = target.get("value")
        if isinstance(value2, dict) and value2.get("kind") == "Name":
            name2 = value2.get("id")
            if isinstance(name2, str):
                out.add(name2)


def _resolve_class_def(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a ClassDef."""
    name_val = stmt.get("name")
    class_name: str = str(name_val) if isinstance(name_val, str) else ""
    decorators = _class_decorators(stmt)
    if len(decorators) > 0:
        stmt["decorators"] = decorators

    # Add class_storage_hint if not present
    if "class_storage_hint" not in stmt:
        is_extern_class: bool = "extern" in decorators
        ft_check: JsonVal = stmt.get("field_types")
        has_fields: bool = bool(ft_check) if isinstance(ft_check, dict) else False
        if is_extern_class and not has_fields:
            # @extern class with no fields → opaque (raw pointer, no RC)
            stmt["class_storage_hint"] = "opaque"
            meta_obj = stmt.get("meta")
            meta_dict: dict[str, JsonVal] = {}
            if isinstance(meta_obj, dict):
                for meta_key, meta_value in meta_obj.items():
                    if isinstance(meta_key, str):
                        meta_dict[meta_key] = meta_value
            meta_dict["opaque_v1"] = {"schema_version": 1}
            stmt["meta"] = meta_dict
        else:
            base_val = stmt.get("base")
            has_base: bool = base_val is not None and isinstance(base_val, str) and base_val != ""
            is_dataclass: bool = stmt.get("dataclass") is True
            # Check for __init__ method
            has_init: bool = False
            cls_body = stmt.get("body")
            if isinstance(cls_body, list):
                for item in cls_body:
                    if isinstance(item, dict) and item.get("kind") == "FunctionDef" and item.get("name") == "__init__":
                        has_init = True
                        break
            # Enum/IntEnum/IntFlag bases are value types
            base_str: str = str(base_val) if isinstance(base_val, str) else ""
            is_enum_base: bool = base_str in ("Enum", "IntEnum", "IntFlag")
            # base (non-enum), __init__, or @dataclass → "ref", otherwise "value"
            if (has_base and not is_enum_base) or has_init or is_dataclass:
                stmt["class_storage_hint"] = "ref"
            else:
                stmt["class_storage_hint"] = "value"

    # Normalize and refresh field_types from the prescanned class signature.
    ft_raw_any = stmt.get("field_types")
    ft_raw: dict[str, JsonVal] = ft_raw_any if isinstance(ft_raw_any, dict) else {}
    if not isinstance(ft_raw_any, dict):
        stmt["field_types"] = ft_raw
    else:
        for fk, fv in ft_raw.items():
            if isinstance(fv, str):
                ft_raw[fk] = _ctx_normalize_type(fv, ctx)

    cls_sig_existing: ClassSig | None = ctx.module_classes.get(class_name)
    if cls_sig_existing is not None:
        for fname, ftype in cls_sig_existing.fields.items():
            ft_raw[fname] = _ctx_normalize_type(ftype, ctx)

    # Collect fields from body
    cls_scope: Scope = ctx.scope.child()
    cls_scope.define("self", class_name)

    # Define class fields in scope
    cls_sig: ClassSig | None = ctx.module_classes.get(class_name)
    if cls_sig is not None:
        for fname, ftype in cls_sig.fields.items():
            cls_scope.define(fname, ftype)

    old_scope: Scope = ctx.scope
    old_in_class: bool = ctx.in_class
    old_current_class: str = ctx.current_class
    ctx.scope = cls_scope
    ctx.in_class = True
    ctx.current_class = class_name

    # First pass: define class-level variables in scope
    body = stmt.get("body")
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict):
                ik: str = str(item.get("kind", ""))
                if ik == "AnnAssign":
                    ann = item.get("annotation")
                    if isinstance(ann, str):
                        tgt = item.get("target")
                        if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                            vn = tgt.get("id")
                            if isinstance(vn, str):
                                cls_scope.define(vn, _ctx_normalize_type(ann, ctx))
                elif ik == "Assign":
                    tgt2 = item.get("target")
                    if isinstance(tgt2, dict) and tgt2.get("kind") == "Name":
                        vn2 = tgt2.get("id")
                        if isinstance(vn2, str):
                            # Will be resolved in second pass
                            pass

    # Second pass: resolve all statements
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict):
                _resolve_stmt(item, ctx)
    _rewrite_trait_helper_call_signatures(stmt, ctx)
    ctx.scope = old_scope
    ctx.in_class = old_in_class
    ctx.current_class = old_current_class

    if cls_sig_existing is not None and isinstance(body, list):
        for item in body:
            if not isinstance(item, dict):
                continue
            ik: str = str(item.get("kind", ""))
            if ik == "AnnAssign":
                target = item.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    field_name = target.get("id")
                    field_type = item.get("decl_type")
                    if isinstance(field_name, str) and isinstance(field_type, str) and field_type != "" and field_type != "unknown":
                        cls_sig_existing.fields[field_name] = _ctx_normalize_type(field_type, ctx)
                        ft_raw[field_name] = cls_sig_existing.fields[field_name]
            elif ik == "FunctionDef" and item.get("name") == "__init__":
                init_body = item.get("body")
                if not isinstance(init_body, list):
                    continue
                for init_stmt in init_body:
                    if not isinstance(init_stmt, dict):
                        continue
                    target2 = init_stmt.get("target")
                    if not isinstance(target2, dict) or target2.get("kind") != "Attribute":
                        continue
                    owner = target2.get("value")
                    if not isinstance(owner, dict) or owner.get("kind") != "Name" or owner.get("id") != "self":
                        continue
                    field_name2 = target2.get("attr")
                    field_type2 = target2.get("resolved_type")
                    if isinstance(field_name2, str) and isinstance(field_type2, str) and field_type2 != "" and field_type2 != "unknown":
                        if _has_inherited_field(class_name, field_name2, ctx):
                            continue
                        cls_sig_existing.fields[field_name2] = _ctx_normalize_type(field_type2, ctx)
                        ft_raw[field_name2] = cls_sig_existing.fields[field_name2]

    _resolve_trait_contracts(stmt, class_name, ctx)


def _rewrite_trait_helper_call_signatures(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Normalize local trait helper __call__ signatures away from object."""
    class_name = str(stmt.get("name", "")) if isinstance(stmt.get("name"), str) else ""
    if class_name == "":
        return
    body = stmt.get("body")
    if not isinstance(body, list):
        return
    cls_sig = ctx.module_classes.get(class_name)
    for item in body:
        if not isinstance(item, dict) or item.get("kind") != "FunctionDef" or item.get("name") != "__call__":
            continue
        if _rewrite_identity_decorator_call(item, cls_sig):
            continue
        _rewrite_implements_factory_call(item, cls_sig)


def _rewrite_identity_decorator_call(func: dict[str, JsonVal], cls_sig: ClassSig | None) -> bool:
    arg_types = func.get("arg_types")
    arg_order = func.get("arg_order")
    body = func.get("body")
    if not isinstance(arg_types, dict) or not isinstance(arg_order, list) or not isinstance(body, list):
        return False
    if len(arg_order) != 2:
        return False
    param_name = arg_order[1]
    if not isinstance(param_name, str):
        return False
    if str(arg_types.get(param_name, "")) != "object":
        return False
    if str(func.get("return_type", "")) != "object":
        return False
    if len(body) != 1:
        return False
    ret_stmt = body[0]
    if not isinstance(ret_stmt, dict) or ret_stmt.get("kind") != "Return":
        return False
    ret_value = ret_stmt.get("value")
    if not isinstance(ret_value, dict) or ret_value.get("kind") != "Name" or ret_value.get("id") != param_name:
        return False
    arg_types[param_name] = "T"
    func["return_type"] = "T"
    ret_value["resolved_type"] = "T"
    if cls_sig is not None:
        if len(cls_sig.template_params) == 0:
            cls_sig.template_params = ["T"]
        method_sig = cls_sig.methods.get("__call__")
        if method_sig is not None:
            method_sig.arg_types[param_name] = "T"
            method_sig.return_type = "T"
    return True


def _rewrite_implements_factory_call(func: dict[str, JsonVal], cls_sig: ClassSig | None) -> bool:
    if str(func.get("return_type", "")) != "object":
        return False
    body = func.get("body")
    if not isinstance(body, list) or len(body) != 1:
        return False
    ret_stmt = body[0]
    if not isinstance(ret_stmt, dict) or ret_stmt.get("kind") != "Return":
        return False
    ret_value = ret_stmt.get("value")
    if not isinstance(ret_value, dict) or ret_value.get("kind") != "Call":
        return False
    callee = ret_value.get("func")
    if not isinstance(callee, dict) or callee.get("kind") != "Name":
        return False
    callee_name = str(callee.get("id", "")) if isinstance(callee.get("id"), str) else ""
    if callee_name == "":
        return False
    func["return_type"] = callee_name
    ret_value["resolved_type"] = callee_name
    if cls_sig is not None:
        method_sig = cls_sig.methods.get("__call__")
        if method_sig is not None:
            method_sig.return_type = callee_name
    return True


def _resolve_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an Assign statement."""
    value = stmt.get("value")
    vt: str = "unknown"
    if isinstance(value, dict):
        vt = _resolve_expr(value, ctx)

    # Resolve target(s) and add decl_type
    # If variable already exists in scope → readonly_ref + resolved type
    # If new variable → value + "unknown"
    targets = stmt.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict):
                if t.get("kind") == "Name":
                    name_val = t.get("id")
                    if isinstance(name_val, str):
                        existing: str = ctx.scope.lookup(name_val)
                        if isinstance(value, dict) and existing != "unknown":
                            _apply_collection_type_hint(value, existing, ctx)
                            vt = str(value.get("resolved_type", vt))
                        if existing != "unknown":
                            # Re-assignment: keep resolved type
                            t["resolved_type"] = existing
                            t["borrow_kind"] = "readonly_ref"
                        else:
                            t["resolved_type"] = "unknown"
                        ctx.scope.define(name_val, vt)
                        if isinstance(value, dict) and value.get("kind") == "Lambda":
                            ctx.scope.bind_lambda(name_val, value)
                        else:
                            ctx.scope.clear_lambda(name_val)
                elif t.get("kind") == "Tuple":
                    _resolve_expr(t, ctx)
                    # Define tuple element variables
                    elems = t.get("elements")
                    if isinstance(elems, list):
                        tup_types: list[str] = _tuple_assign_element_types(t, vt, ctx)
                        for idx_t, elem in enumerate(elems):
                            if isinstance(elem, dict) and elem.get("kind") == "Name":
                                elem_name = elem.get("id")
                                if isinstance(elem_name, str):
                                    et: str = tup_types[idx_t] if idx_t < len(tup_types) else "unknown"
                                    elem["resolved_type"] = et
                                    ctx.scope.define(elem_name, et)
                else:
                    tt = _resolve_expr(t, ctx)
                    if isinstance(value, dict) and tt != "unknown":
                        _apply_collection_type_hint(value, tt, ctx)
                        vt = str(value.get("resolved_type", vt))
    else:
        target = stmt.get("target")
        if isinstance(target, dict):
            if target.get("kind") == "Name":
                name_val2 = target.get("id")
                if isinstance(name_val2, str):
                    existing2: str = ctx.scope.lookup(name_val2)
                    if isinstance(value, dict) and existing2 != "unknown":
                        _apply_collection_type_hint(value, existing2, ctx)
                        vt = str(value.get("resolved_type", vt))
                    if existing2 != "unknown":
                        target["resolved_type"] = existing2
                        target["borrow_kind"] = "readonly_ref"
                    else:
                        target["resolved_type"] = "unknown"
                    ctx.scope.define(name_val2, vt)
                    if isinstance(value, dict) and value.get("kind") == "Lambda":
                        ctx.scope.bind_lambda(name_val2, value)
                    else:
                        ctx.scope.clear_lambda(name_val2)
            elif target.get("kind") == "Tuple":
                _resolve_expr(target, ctx)
                elems2 = target.get("elements")
                if isinstance(elems2, list):
                    tup_types2: list[str] = _tuple_assign_element_types(target, vt, ctx)
                    for idx_t2, elem2 in enumerate(elems2):
                        if isinstance(elem2, dict) and elem2.get("kind") == "Name":
                            elem_name2 = elem2.get("id")
                            if isinstance(elem_name2, str):
                                et2: str = tup_types2[idx_t2] if idx_t2 < len(tup_types2) else "unknown"
                                elem2["resolved_type"] = et2
                                ctx.scope.define(elem_name2, et2)
            else:
                target_type = _resolve_expr(target, ctx)
                if isinstance(value, dict) and target_type != "unknown":
                    _apply_collection_type_hint(value, target_type, ctx)
                    vt = str(value.get("resolved_type", vt))

    # Add decl_type for declarations (declare=true)
    declare_val = stmt.get("declare")
    if declare_val is True:
        if vt != "unknown":
            stmt["decl_type"] = vt
        if isinstance(value, dict):
            stmt["declare_init"] = True


def _resolve_ann_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an AnnAssign (annotated assignment)."""
    # Normalize annotation
    ann_raw = stmt.get("annotation")
    ann_type: str = "unknown"
    if isinstance(ann_raw, str):
        ann_type = _ctx_normalize_type(ann_raw, ctx)
        stmt["annotation"] = ann_type

    # Add annotation_type_expr and decl_type_expr
    stmt["annotation_type_expr"] = make_type_expr(ann_type)
    stmt["decl_type"] = ann_type
    stmt["decl_type_expr"] = make_type_expr(ann_type)

    # Resolve value
    value = stmt.get("value")
    if isinstance(value, dict):
        _resolve_expr(value, ctx)
        if ann_type != "":
            _apply_collection_type_hint(value, ann_type, ctx)

    # Resolve target
    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        name_val = target.get("id")
        if isinstance(name_val, str):
            ctx.scope.define(name_val, ann_type)
            target["resolved_type"] = ann_type
            target["type_expr"] = make_type_expr(ann_type)
            if isinstance(value, dict) and value.get("kind") == "Lambda":
                ctx.scope.bind_lambda(name_val, value)
            else:
                ctx.scope.clear_lambda(name_val)
    elif isinstance(target, dict) and target.get("kind") == "Attribute":
        # self.field = ... — resolve the receiver (self) and add type_expr
        _resolve_expr(target, ctx)
        if ann_type != "unknown":
            target["type_expr"] = make_type_expr(ann_type)


def _resolve_aug_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an AugAssign (augmented assignment like +=)."""
    target = stmt.get("target")
    value = stmt.get("value")

    tt: str = "unknown"
    if isinstance(target, dict):
        tt = _resolve_expr(target, ctx)
        # AugAssign target keeps its resolved_type (it reads the current value)
    if isinstance(value, dict):
        _resolve_expr(value, ctx)

    # Set decl_type for Name targets, null for Attribute targets (self.x)
    tgt_kind: str = ""
    if isinstance(target, dict):
        tk_v = target.get("kind")
        tgt_kind = str(tk_v) if isinstance(tk_v, str) else ""
    if tgt_kind == "Attribute":
        # self.x: decl_type = null
        stmt["decl_type"] = None
    elif tt != "unknown":
        stmt["decl_type"] = tt


def _resolve_if(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    test = stmt.get("test")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    body_narrow = _resolve_guard_narrowing_from_expr(test)
    orelse_narrow = _resolve_invert_guard_narrowing_from_expr(test)
    body = stmt.get("body")
    _resolve_stmt_list_with_narrowing(body, ctx, body_narrow)
    orelse = stmt.get("orelse")
    _resolve_stmt_list_with_narrowing(orelse, ctx, orelse_narrow)
    body_exits = _resolver_block_guarantees_exit(body)
    orelse_exits = _resolver_block_guarantees_exit(orelse)
    if body_exits and not orelse_exits:
        for name, typ in orelse_narrow.items():
            ctx.scope.define(name, typ)
    elif orelse_exits and not body_exits:
        for name, typ in body_narrow.items():
            ctx.scope.define(name, typ)


def _resolve_while(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    test = stmt.get("test")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    body = stmt.get("body")
    _resolve_stmt_list_with_narrowing(body, ctx, _resolve_guard_narrowing_from_expr(test))
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_for(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a For statement — may convert to ForRange."""
    iter_expr = stmt.get("iter")
    target = stmt.get("target")

    # Check for range() conversion
    if isinstance(iter_expr, dict) and _is_range_call(iter_expr):
        _convert_for_to_forrange(stmt, iter_expr, ctx)
        return

    # Regular for loop
    it: str = "unknown"
    if isinstance(iter_expr, dict):
        it = _resolve_expr(iter_expr, ctx)

    # Determine target type from iterable
    elem_type: str = "unknown"
    if it.startswith("list[") and it.endswith("]"):
        elem_type = it[5:-1]
    elif it.startswith("set[") and it.endswith("]"):
        elem_type = it[4:-1]
    elif it == "str":
        elem_type = "str"
    elif it in ("bytes", "bytearray", "list[uint8]"):
        elem_type = "int64"
    elif it.startswith("tuple[") and it.endswith("]"):
        tup_elems: list[str] = extract_type_args(it)
        if len(tup_elems) > 0:
            first: str = tup_elems[0]
            all_same: bool = True
            for te in tup_elems:
                if te != first:
                    all_same = False
                    break
            if all_same:
                elem_type = first
    elif it.startswith("dict[") and it.endswith("]"):
        # Iterating over dict gives keys
        targs: list[str] = extract_type_args(it)
        if len(targs) >= 1:
            elem_type = targs[0]

    # Add iteration metadata
    stmt["target_type"] = elem_type
    iter_mode: str = "static_fastpath"
    if it == "unknown":
        iter_mode = "dynamic"
    stmt["iter_mode"] = iter_mode
    stmt["iter_source_type"] = it
    stmt["iter_element_type"] = elem_type

    # Add iterable traits to iter expression
    if isinstance(iter_expr, dict):
        iter_expr["iterable_trait"] = "yes"
        iter_expr["iter_protocol"] = "static_range"
        iter_expr["iter_element_type"] = elem_type

    # Define loop variable
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, elem_type)
            target["resolved_type"] = elem_type
    elif isinstance(target, dict) and target.get("kind") == "Tuple":
        # Tuple unpacking: for i, ch in enumerate(s)
        # elem_type should be like "tuple[int64, str]"
        tup_args: list[str] = extract_type_args(elem_type) if elem_type.startswith("tuple[") else []
        target["resolved_type"] = elem_type
        elems = target.get("elements")
        if isinstance(elems, list):
            for i_el, el in enumerate(elems):
                if isinstance(el, dict) and el.get("kind") == "Name":
                    el_name = el.get("id")
                    if isinstance(el_name, str):
                        el_type: str = tup_args[i_el] if i_el < len(tup_args) else "unknown"
                        ctx.scope.define(el_name, el_type)
                        el["resolved_type"] = el_type
    elif isinstance(target, dict):
        _resolve_expr(target, ctx)

    # Resolve body
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _convert_call_to_range_expr(expr: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Convert a range() Call to a RangeExpr node (in-place)."""
    args = expr.get("args")
    if not isinstance(args, list):
        return

    for a in args:
        if isinstance(a, dict):
            _resolve_expr(a, ctx)

    range_func = expr.get("func")
    source_span: dict[str, JsonVal] = _node_dict_or_empty(expr.get("source_span"))
    if isinstance(range_func, dict):
        source_span = _node_dict_or_empty(range_func.get("source_span"))

    if len(args) == 1:
        start: dict[str, JsonVal] = {
            "kind": "Constant", "source_span": source_span,
            "resolved_type": "int64", "casts": [], "borrow_kind": "value",
            "repr": "0", "value": 0,
        }
        stop = _node_dict_or_empty(args[0])
        step: dict[str, JsonVal] = {
            "kind": "Constant", "source_span": source_span,
            "resolved_type": "int64", "casts": [], "borrow_kind": "value",
            "repr": "1", "value": 1,
        }
    elif len(args) == 2:
        start = _node_dict_or_empty(args[0])
        stop = _node_dict_or_empty(args[1])
        step = {
            "kind": "Constant", "source_span": source_span,
            "resolved_type": "int64", "casts": [], "borrow_kind": "value",
            "repr": "1", "value": 1,
        }
    elif len(args) >= 3:
        start = _node_dict_or_empty(args[0])
        stop = _node_dict_or_empty(args[1])
        step = _node_dict_or_empty(args[2])
    else:
        return

    # Determine range_mode
    range_mode: str = "ascending"
    if isinstance(step, dict) and step.get("kind") == "Constant":
        sv = step.get("value")
        if isinstance(sv, int):
            if sv < 0:
                range_mode = "descending"
            elif sv != 1:
                range_mode = "dynamic"
    elif isinstance(step, dict) and step.get("kind") != "Constant":
        range_mode = "dynamic"

    # Replace the Call node in-place with RangeExpr
    orig_span: dict[str, JsonVal] = _node_dict_or_empty(expr.get("source_span"))
    orig_repr = expr.get("repr", "")
    expr.clear()
    expr["kind"] = "RangeExpr"
    expr["source_span"] = orig_span
    expr["resolved_type"] = "list[int64]"
    expr["casts"] = []
    expr["borrow_kind"] = "value"
    expr["repr"] = orig_repr
    expr["start"] = start
    expr["stop"] = stop
    expr["step"] = step
    expr["range_mode"] = range_mode


def _is_range_call(expr: dict[str, JsonVal]) -> bool:
    """Check if expr is a call to range()."""
    if expr.get("kind") != "Call":
        return False
    func = expr.get("func")
    if not isinstance(func, dict):
        return False
    return func.get("kind") == "Name" and func.get("id") == "range"


def _convert_for_to_forrange(
    stmt: dict[str, JsonVal],
    iter_call: dict[str, JsonVal],
    ctx: ResolveContext,
) -> None:
    """Convert for..in range() to ForRange node."""
    args = iter_call.get("args")
    if not isinstance(args, list):
        return

    # Resolve range arguments
    for a in args:
        if isinstance(a, dict):
            _resolve_expr(a, ctx)

    # Use the range() function name span for synthesized constants
    range_func = iter_call.get("func")
    source_span: dict[str, JsonVal] = _node_dict_or_empty(iter_call.get("source_span"))
    if isinstance(range_func, dict):
        source_span = _node_dict_or_empty(range_func.get("source_span"))

    if len(args) == 1:
        start_node: dict[str, JsonVal] = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "0",
            "value": 0,
        }
        stop_node = _node_dict_or_empty(args[0])
        step_node: dict[str, JsonVal] = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "1",
            "value": 1,
        }
    elif len(args) == 2:
        start_node = _node_dict_or_empty(args[0])
        stop_node = _node_dict_or_empty(args[1])
        step_node = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "1",
            "value": 1,
        }
    elif len(args) >= 3:
        start_node = _node_dict_or_empty(args[0])
        stop_node = _node_dict_or_empty(args[1])
        step_node = _node_dict_or_empty(args[2])
    else:
        return

    # Determine range_mode
    range_mode: str = "ascending"
    if isinstance(step_node, dict) and step_node.get("kind") == "Constant":
        sv = step_node.get("value")
        if isinstance(sv, int):
            if sv < 0:
                range_mode = "descending"
            elif sv == 1:
                range_mode = "ascending"
            else:
                range_mode = "dynamic"
    elif isinstance(step_node, dict) and step_node.get("kind") != "Constant":
        range_mode = "dynamic"

    # Convert the For node to ForRange
    stmt["kind"] = "ForRange"
    stmt["target_type"] = "int64"
    stmt["start"] = start_node
    stmt["stop"] = stop_node
    stmt["step"] = step_node
    stmt["range_mode"] = range_mode

    # Remove iter (no longer needed)
    if "iter" in stmt:
        stmt.pop("iter")

    # Define loop variable
    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, "int64")
            target["resolved_type"] = "int64"

    # Resolve body
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_for_range(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an already-converted ForRange."""
    start = stmt.get("start")
    stop = stmt.get("stop")
    step = stmt.get("step")
    if isinstance(start, dict):
        _resolve_expr(start, ctx)
    if isinstance(stop, dict):
        _resolve_expr(stop, ctx)
    if isinstance(step, dict):
        _resolve_expr(step, ctx)

    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, "int64")
            target["resolved_type"] = "int64"

    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_try(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    handlers = stmt.get("handlers")
    if isinstance(handlers, list):
        for h in handlers:
            if isinstance(h, dict):
                exc_type = h.get("type")
                if isinstance(exc_type, dict) and exc_type.get("kind") == "Name":
                    exc_name = exc_type.get("id")
                    if isinstance(exc_name, str) and exc_name in _BUILTIN_EXCEPTION_TYPE_NAMES:
                        exc_type["resolved_type"] = exc_name
                        exc_type["runtime_module_id"] = _BUILTIN_EXCEPTION_MODULE_ID
                    else:
                        exc_type["resolved_type"] = "unknown"
                handler_body = h.get("body")
                if isinstance(handler_body, list):
                    for s in handler_body:
                        if isinstance(s, dict):
                            _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    finalbody = stmt.get("finalbody")
    if isinstance(finalbody, list):
        for s in finalbody:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_with(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    context_expr = stmt.get("context_expr")
    context_type: str = "unknown"
    if isinstance(context_expr, dict):
        context_type = _resolve_expr(context_expr, ctx)
    owner_base = extract_base_type(context_type)
    enter_type = context_type
    enter_cls, enter_sig = _lookup_method_sig(owner_base, "__enter__", ctx)
    if enter_cls is not None and enter_sig is not None:
        enter_type = _ctx_normalize_type(_substitute_type_params(enter_sig.return_type, context_type, enter_cls), ctx)
        stmt["with_enter_type"] = enter_type
        if enter_sig.extern_v2 is not None:
            if enter_sig.extern_v2.symbol != "":
                stmt["with_enter_runtime_call"] = enter_sig.extern_v2.symbol
                stmt["with_enter_runtime_symbol"] = enter_sig.extern_v2.symbol
            if enter_sig.extern_v2.module != "":
                stmt["with_enter_runtime_module_id"] = enter_sig.extern_v2.module
            if enter_sig.extern_v2.tag != "":
                stmt["with_enter_semantic_tag"] = enter_sig.extern_v2.tag
    exit_cls, exit_sig = _lookup_method_sig(owner_base, "__exit__", ctx)
    if exit_cls is not None and exit_sig is not None and exit_sig.extern_v2 is not None:
        if exit_sig.extern_v2.symbol != "":
            stmt["with_exit_runtime_call"] = exit_sig.extern_v2.symbol
            stmt["with_exit_runtime_symbol"] = exit_sig.extern_v2.symbol
        if exit_sig.extern_v2.module != "":
            stmt["with_exit_runtime_module_id"] = exit_sig.extern_v2.module
        if exit_sig.extern_v2.tag != "":
            stmt["with_exit_semantic_tag"] = exit_sig.extern_v2.tag

    saved_scope: Scope = ctx.scope
    body_scope: Scope = saved_scope.child()
    var_name_val = stmt.get("var_name")
    if isinstance(var_name_val, str) and var_name_val != "":
        body_scope.define(var_name_val, enter_type)
    ctx.scope = body_scope

    items = stmt.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_context_expr = item.get("context_expr")
                if isinstance(item_context_expr, dict):
                    _resolve_expr(item_context_expr, ctx)
    body = stmt.get("body")
    try:
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _resolve_stmt(s, ctx)
    finally:
        ctx.scope = saved_scope


# ---------------------------------------------------------------------------
# Import resolution helpers
# ---------------------------------------------------------------------------

def _build_import_resolution_meta(
    ctx: ResolveContext,
    east1_meta: dict[str, JsonVal],
) -> None:
    """Enhance import_resolution bindings with runtime info."""
    ir = east1_meta.get("import_resolution")
    if not isinstance(ir, dict):
        # Build from import_bindings
        bindings_raw = east1_meta.get("import_bindings")
        if isinstance(bindings_raw, list):
            ir_dict: dict[str, JsonVal] = {}
            ir_dict["schema_version"] = 1
            ir_dict["bindings"] = bindings_raw
            empty_qrefs: list[JsonVal] = []
            ir_dict["qualified_refs"] = empty_qrefs
            ir = ir_dict
            east1_meta["import_resolution"] = ir
        else:
            return

    ir["schema_version"] = 1

    bindings = ir.get("bindings")
    if isinstance(bindings, list):
        enhanced: list[JsonVal] = []
        for b in bindings:
            if isinstance(b, dict):
                enhanced.append(_enhance_binding(b, ctx))
        ir["bindings"] = enhanced

    # Add qualified_refs from import_symbols
    qrefs_raw = east1_meta.get("qualified_symbol_refs")
    if isinstance(qrefs_raw, list):
        ir["qualified_refs"] = qrefs_raw

    # Add implicit builtin bindings
    existing_modules: set[str] = set()
    if isinstance(bindings, list):
        for b in bindings:
            if isinstance(b, dict):
                mid = b.get("module_id")
                if isinstance(mid, str):
                    existing_modules.add(mid)

    # Check for additional builtin modules from import_bindings
    ib_raw = east1_meta.get("import_bindings")
    if isinstance(ib_raw, list):
        for ib in ib_raw:
            if isinstance(ib, dict):
                mid2 = ib.get("module_id")
                if isinstance(mid2, str):
                    existing_modules.add(mid2)

    for mod in sorted(ctx.used_builtin_modules):
        if mod not in existing_modules:
            imp_binding: dict[str, JsonVal] = {
                "module_id": mod,
                "export_name": "",
                "local_name": mod,
                "binding_kind": "implicit_builtin",
                "source_file": ctx.source_file,
                "source_line": 0,
                "source_module_id": mod,
                "source_binding_kind": "implicit_builtin",
                "runtime_module_id": mod,
                "runtime_group": ctx.lookup_runtime_module_group(mod),
            }
            final_bindings = ir.get("bindings")
            if isinstance(final_bindings, list):
                final_bindings.append(imp_binding)

    final_bindings = ir.get("bindings")
    if isinstance(final_bindings, list):
        compat_bindings: list[JsonVal] = []
        for binding in final_bindings:
            if isinstance(binding, dict):
                compat_bindings.append(dict(binding))
        east1_meta["import_bindings"] = compat_bindings


def _enhance_binding(binding: dict[str, JsonVal], ctx: ResolveContext) -> dict[str, JsonVal]:
    """Enhance a single import binding with runtime resolution info."""
    module_id_val = binding.get("module_id")
    module_id: str = str(module_id_val) if isinstance(module_id_val, str) else ""
    export_name_val = binding.get("export_name")
    export_name: str = str(export_name_val) if isinstance(export_name_val, str) else ""
    binding_kind_val = binding.get("binding_kind")
    binding_kind: str = str(binding_kind_val) if isinstance(binding_kind_val, str) else ""
    local_name_val = binding.get("local_name")
    local_name: str = str(local_name_val) if isinstance(local_name_val, str) else ""

    canonical: str = ctx.canonical_module_id(module_id)
    runtime_group: str = ctx.lookup_runtime_module_group(canonical)
    if canonical == module_id and module_id != "" and "." not in module_id:
        fallback_canonical = "pytra.std." + module_id
        fallback_group = ctx.lookup_runtime_module_group(fallback_canonical)
        if binding_kind == "module":
            if fallback_group != "":
                canonical = fallback_canonical
                runtime_group = fallback_group
        elif export_name != "":
            fallback_sym_doc = ctx.lookup_runtime_symbol_doc(fallback_canonical, export_name)
            if len(fallback_sym_doc) > 0:
                canonical = fallback_canonical
                runtime_group = fallback_group

    binding["source_module_id"] = module_id
    binding["source_export_name"] = export_name
    binding["source_binding_kind"] = binding_kind
    binding["runtime_module_id"] = canonical
    binding["runtime_group"] = runtime_group

    if binding_kind == "module":
        binding["resolved_binding_kind"] = "module"
        binding["host_only"] = True
        return binding

    promoted_module: str = ctx.import_modules.get(local_name, "")
    if promoted_module != "" and promoted_module != canonical:
        binding["runtime_module_id"] = promoted_module
        binding["runtime_group"] = ctx.lookup_runtime_module_group(promoted_module)
        binding["resolved_binding_kind"] = "module"
        binding["host_only"] = True
        return binding

    if binding_kind == "implicit_builtin":
        return binding

    # Symbol binding: look up in runtime index
    sym_doc: dict[str, JsonVal] = ctx.lookup_runtime_symbol_doc(canonical, export_name)
    if len(sym_doc) > 0:
        binding["resolved_binding_kind"] = "symbol"
        binding["runtime_symbol"] = export_name
        kind_v = sym_doc.get("kind")
        if isinstance(kind_v, str) and kind_v != "":
            binding["runtime_symbol_kind"] = kind_v
        dispatch_v = sym_doc.get("dispatch")
        if isinstance(dispatch_v, str) and dispatch_v != "":
            binding["runtime_symbol_dispatch"] = dispatch_v
        stag_v = sym_doc.get("semantic_tag")
        if isinstance(stag_v, str) and stag_v != "":
            binding["runtime_semantic_tag"] = stag_v
        adapter_v = sym_doc.get("call_adapter_kind")
        if isinstance(adapter_v, str) and adapter_v != "":
            binding["runtime_call_adapter_kind"] = adapter_v

    return binding


# ---------------------------------------------------------------------------
# Pre-scan: collect module-level signatures before resolution
# ---------------------------------------------------------------------------

def _resolve_import_symbol_module_alias(
    module_id: str,
    export_name: str,
    ctx: ResolveContext,
) -> str:
    """Resolve `from X import y` when `y` should be treated as a module alias."""
    if export_name == "":
        return ""
    candidates: list[str] = []
    canonical_source: str = ctx.canonical_module_id(module_id)
    if canonical_source != "":
        candidates.append(canonical_source + "." + export_name)
    if module_id != "":
        candidates.append(module_id + "." + export_name)
    if export_name.startswith("pytra.std.") or export_name.startswith("pytra."):
        candidates.append(export_name)
    seen: set[str] = set()
    for candidate in candidates:
        normalized: str = ctx.canonical_module_id(candidate)
        if normalized == "" or normalized in seen:
            continue
        seen.add(normalized)
        if ctx.runtime_module_exists(normalized) or normalized in ctx.registry.stdlib_modules:
            return normalized
    return ""

def _prescan_module(doc: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Pre-scan module body to collect function/class signatures and imports."""
    # Collect renamed symbols
    rs_raw = doc.get("renamed_symbols")
    if isinstance(rs_raw, dict):
        for k, v in rs_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                ctx.renamed_symbols[k] = v

    meta = doc.get("meta")
    if isinstance(meta, dict):
        # Collect import info
        im_raw = meta.get("import_modules")
        if isinstance(im_raw, dict):
            for k, v in im_raw.items():
                if isinstance(v, str):
                    ctx.import_modules[k] = v
        is_raw = meta.get("import_symbols")
        if isinstance(is_raw, dict):
            for k, v in is_raw.items():
                if isinstance(v, dict):
                    mod = v.get("module")
                    nm = v.get("name")
                    module_id: str = str(mod) if isinstance(mod, str) else ""
                    export_name: str = str(nm) if isinstance(nm, str) else k
                    promoted_module: str = _resolve_import_symbol_module_alias(module_id, export_name, ctx)
                    if promoted_module != "":
                        ctx.import_modules[k] = promoted_module
                        continue
                    symbol_info: dict[str, str] = {}
                    symbol_info["module"] = module_id
                    symbol_info["name"] = export_name
                    ctx.import_symbols[k] = symbol_info

    # Collect module-local type aliases before signature extraction.
    body = doc.get("body")
    if isinstance(body, list):
        for item in body:
            if not isinstance(item, dict) or item.get("kind") != "TypeAlias":
                continue
            alias_name = item.get("name")
            alias_value = item.get("value")
            if not isinstance(alias_value, str):
                alias_value = item.get("type_expr")
            alias_name_str: str = alias_name if isinstance(alias_name, str) else ""
            alias_value_str: str = alias_value if isinstance(alias_value, str) else ""
            if alias_name_str != "" and alias_value_str != "":
                ctx.type_aliases[alias_name_str] = alias_value_str
        _resolve_validate_type_alias_cycles(ctx.type_aliases)
        alias_names: list[str] = []
        for alias_name in ctx.type_aliases.keys():
            if isinstance(alias_name, str):
                alias_names.append(alias_name)
        for alias_name in alias_names:
            alias_value = ctx.type_aliases.get(alias_name, "")
            if isinstance(alias_value, str):
                ctx.type_aliases[alias_name] = normalize_type(alias_value, ctx.type_aliases, {alias_name})

    # Collect function and class signatures
    if isinstance(body, list):
        for item in body:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                sig: FuncSig = _extract_func_sig_for_prescan(item, ctx)
                ctx.module_functions[sig.name] = sig
            elif kind == "ClassDef":
                csig: ClassSig = _extract_class_sig_for_prescan(item, ctx)
                ctx.module_classes[csig.name] = csig
                # Register class as a scope type
                ctx.scope.define(csig.name, csig.name)

    # Also scan main_guard_body
    mgb = doc.get("main_guard_body")
    if isinstance(mgb, list):
        for item in mgb:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                sig2: FuncSig = _extract_func_sig_for_prescan(item, ctx)
                ctx.module_functions[sig2.name] = sig2


def _extract_func_sig_for_prescan(node: dict[str, JsonVal], ctx: ResolveContext) -> FuncSig:
    """Extract a function signature during prescan (before full resolution)."""
    name_val = node.get("name")
    name: str = str(name_val) if isinstance(name_val, str) else ""
    arg_types_raw = node.get("arg_types")
    arg_types: dict[str, str] = {}
    if isinstance(arg_types_raw, dict):
        for k, v in arg_types_raw.items():
            if isinstance(v, str):
                arg_types[k] = _ctx_normalize_type(v, ctx)
    arg_order_raw = node.get("arg_order")
    arg_names: list[str] = []
    if isinstance(arg_order_raw, list):
        for a in arg_order_raw:
            if isinstance(a, str):
                arg_names.append(a)
    ret_raw = node.get("return_type")
    ret: str = _ctx_normalize_type(str(ret_raw), ctx) if isinstance(ret_raw, str) else "unknown"
    vararg_name_val = node.get("vararg_name")
    vararg_name: str = str(vararg_name_val) if isinstance(vararg_name_val, str) else ""
    vararg_type_raw = node.get("vararg_type")
    vararg_type: str = _ctx_normalize_type(str(vararg_type_raw), ctx) if isinstance(vararg_type_raw, str) else ""
    decorators_raw = node.get("decorators")
    decorators: list[str] = []
    if isinstance(decorators_raw, list):
        for item in decorators_raw:
            if isinstance(item, str):
                decorators.append(item)
    return FuncSig(
        name=name,
        arg_names=arg_names,
        arg_types=arg_types,
        return_type=ret,
        decorators=decorators,
        vararg_name=vararg_name,
        vararg_type=vararg_type,
    )


def _extract_class_sig_for_prescan(node: dict[str, JsonVal], ctx: ResolveContext) -> ClassSig:
    """Extract a class signature during prescan."""
    name_val = node.get("name")
    name: str = str(name_val) if isinstance(name_val, str) else ""
    base_raw = node.get("base")
    bases_raw = node.get("bases")
    bases: list[str] = []
    if isinstance(base_raw, str) and base_raw != "":
        bases.append(base_raw)
    if isinstance(bases_raw, list):
        for b in bases_raw:
            if isinstance(b, str) and b not in bases:
                bases.append(b)
    methods: dict[str, FuncSig] = {}
    fields: dict[str, str] = {}
    decorators: list[str] = _class_decorators(node)
    implements_traits: list[str] = []
    for decorator in decorators:
        parsed_traits = _parse_implements_decorator(decorator)
        for trait_name in parsed_traits:
            implements_traits.append(trait_name)
    is_enum_class: bool = False
    for base in bases:
        if base == "Enum" or base == "IntEnum" or base == "IntFlag":
            is_enum_class = True
            break
    body_raw = node.get("body")
    if isinstance(body_raw, list):
        for item in body_raw:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                msig: FuncSig = _extract_func_sig_for_prescan(item, ctx)
                msig.is_method = True
                msig.owner_class = name
                methods[msig.name] = msig
            elif kind == "AnnAssign":
                target = item.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    fld_name = target.get("id")
                    ann = item.get("annotation")
                    if isinstance(fld_name, str) and isinstance(ann, str):
                        fields[fld_name] = _ctx_normalize_type(ann, ctx)
            elif kind == "Assign" and is_enum_class:
                target2 = item.get("target")
                if isinstance(target2, dict) and target2.get("kind") == "Name":
                    fld_name2 = target2.get("id")
                    if isinstance(fld_name2, str) and fld_name2 != "":
                        fields[fld_name2] = name
    # Also extract from field_types (top-level ClassDef field from parse)
    ft_raw = node.get("field_types")
    if isinstance(ft_raw, dict):
        for fk, fv in ft_raw.items():
            if isinstance(fk, str) and isinstance(fv, str) and fk not in fields:
                fields[fk] = _ctx_normalize_type(fv, ctx)
    return ClassSig(
        name=name,
        bases=bases,
        methods=methods,
        fields=fields,
        decorators=decorators,
        is_trait=("trait" in decorators),
        implements_traits=implements_traits,
    )


def _promote_inherited_class_storage_hints(doc: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Promote base classes with descendants to ref storage transitively."""
    body = doc.get("body")
    if not isinstance(body, list):
        return
    class_nodes: dict[str, dict[str, JsonVal]] = {}
    for item in body:
        if isinstance(item, dict) and item.get("kind") == "ClassDef":
            name = item.get("name")
            if isinstance(name, str) and name != "":
                class_nodes[name] = item
    if len(class_nodes) == 0:
        return
    promoted: set[str] = set()
    pending: list[str] = []
    for class_name, cls_sig in ctx.module_classes.items():
        if class_name not in class_nodes:
            continue
        for base in cls_sig.bases:
            base_name = extract_base_type(base)
            if base_name in class_nodes and base_name not in promoted:
                promoted.add(base_name)
                pending.append(base_name)
    while len(pending) > 0:
        current = pending.pop(0)
        current_sig = ctx.module_classes.get(current)
        if current_sig is None:
            continue
        for base in current_sig.bases:
            base_name2 = extract_base_type(base)
            if base_name2 in class_nodes and base_name2 not in promoted:
                promoted.add(base_name2)
                pending.append(base_name2)
    for class_name2 in promoted:
        class_nodes[class_name2]["class_storage_hint"] = "ref"


# ---------------------------------------------------------------------------
# Main resolve entry point
# ---------------------------------------------------------------------------

def resolve_east1_to_east2(
    east1_doc: dict[str, JsonVal],
    registry: BuiltinRegistry | None = None,
) -> dict[str, JsonVal]:
    """Resolve a single EAST1 document to EAST2.

    Mutates east1_doc in place and returns it.
    """
    if registry is None:
        raise ValueError("registry is required for resolve_east1_to_east2()")

    source_path_val = east1_doc.get("source_path")
    source_file: str = str(source_path_val) if isinstance(source_path_val, str) else ""

    ctx: ResolveContext = ResolveContext(
        registry=registry,
        scope=Scope(),
        source_file=source_file,
    )

    # Pre-scan: collect module-level info
    _prescan_module(east1_doc, ctx)

    # Resolve body
    body = east1_doc.get("body")
    if isinstance(body, list):
        for stmt in body:
            if isinstance(stmt, dict):
                _resolve_stmt(stmt, ctx)

    # Resolve main_guard_body
    mgb = east1_doc.get("main_guard_body")
    if isinstance(mgb, list):
        for stmt in mgb:
            if isinstance(stmt, dict):
                _resolve_stmt(stmt, ctx)

    _refine_callable_params_from_calls(east1_doc, ctx)
    _promote_inherited_class_storage_hints(east1_doc, ctx)

    # Post-processing: metadata
    east1_doc["east_stage"] = 2
    east1_doc["schema_version"] = 1

    meta = east1_doc.get("meta")
    if isinstance(meta, dict):
        if "parser_backend" not in meta:
            meta["parser_backend"] = "self_hosted"
        if "dispatch_mode" not in meta:
            meta["dispatch_mode"] = "native"
        # Enhance import resolution
        _build_import_resolution_meta(ctx, meta)

    # Normalize field ordering to match golden files
    normalized: JsonVal = normalize_field_order(east1_doc)
    if isinstance(normalized, dict):
        east1_doc.clear()
        for key, value in normalized.items():
            east1_doc[key] = value

    return east1_doc


def resolve_file(
    input_path: Path,
    registry: BuiltinRegistry | None = None,
) -> ResolveResult:
    """Load and resolve an EAST1 file."""
    text: str = input_path.read_text(encoding="utf-8")
    raw: JsonVal = json.loads(text).raw
    if not isinstance(raw, dict):
        raise ValueError("east1 document must be a JSON object: " + str(input_path))
    east2_doc: dict[str, JsonVal] = raw
    resolve_east1_to_east2(east2_doc, registry=registry)
    source_path_val = east2_doc.get("source_path")
    sp: str = str(source_path_val) if source_path_val is not None else ""
    return ResolveResult(east2_doc=east2_doc, source_path=sp)


def east2_output_path_from_east1(east1_path: Path) -> Path:
    """Derive east2 output path from east1 path.

    a.py.east1 → a.east2 (.py removed)
    """
    name: str = east1_path.name
    if name.endswith(".py.east1"):
        base: str = name[: len(name) - len(".py.east1")]
        return east1_path.parent / (base + ".east2")
    if name.endswith(".east1"):
        base2: str = name[: len(name) - len(".east1")]
        return east1_path.parent / (base2 + ".east2")
    return east1_path.parent / (name + ".east2")

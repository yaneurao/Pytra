"""CodeEmitter 基底クラス + runtime mapping 解決。

全 emitter が共有するロジック:
- runtime_call → ターゲット関数名の解決 (mapping.json)
- runtime_call_adapter_kind 判定 (builtin/extern_delegate)
- import alias 構築
- runtime import 名の解決
- module skip 判定

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.typing import cast


# ---------------------------------------------------------------------------
# Runtime mapping: runtime_call → target language function name
# ---------------------------------------------------------------------------

@dataclass
class RuntimeMapping:
    """Language-specific runtime_call → function name mapping.

    Loaded from mapping.json. Example:
    {
      "builtin_prefix": "__pytra_",
      "calls": {
        "py_print": "__pytra_print",
        "py_len": "__pytra_len",
        "static_cast": "{target_type}({args})",
        "str.strip": "__pytra_strip"
      },
      "types": {
        "int64": "int64_t",
        "str": "std::string",
        "Exception": "std::runtime_error"
      },
      "skip_modules": ["pytra.built_in.", "pytra.std.", "pytra.utils.", "pytra.core."]
    }
    """
    builtin_prefix: str = "__pytra_"
    calls: dict[str, str] = field(default_factory=dict)
    types: dict[str, str] = field(default_factory=dict)
    skip_module_prefixes: list[str] = field(default_factory=list)
    skip_module_exact: set[str] = field(default_factory=set)
    implicit_promotions: set[str] = field(default_factory=set)
    module_native_files: dict[str, str] = field(default_factory=dict)
    module_namespace_exprs: dict[str, str] = field(default_factory=dict)
    call_adapters: dict[str, str] = field(default_factory=dict)
    non_native_modules: set[str] = field(default_factory=set)
    exception_types: set[str] = field(default_factory=set)
    predicate_types: dict[str, str] = field(default_factory=dict)

    def is_implicit_cast(self, from_type: str, to_type: str) -> bool:
        return (from_type + "->" + to_type) in self.implicit_promotions


def load_runtime_mapping(mapping_path: Path) -> RuntimeMapping:
    """Load a mapping.json file into a RuntimeMapping."""
    if not mapping_path.exists():
        return RuntimeMapping()
    text = mapping_path.read_text()
    raw_obj = json.loads_obj(text)
    if raw_obj is None:
        return RuntimeMapping()

    prefix_str = "__pytra_"
    calls: dict[str, str] = {}
    types: dict[str, str] = {}
    skip: list[str] = []
    skip_exact: set[str] = set()
    implicit_promotions: set[str] = set()
    module_native_files: dict[str, str] = {}
    module_namespace_exprs: dict[str, str] = {}
    call_adapters: dict[str, str] = {}
    non_native_modules: set[str] = set()
    exception_types: set[str] = set()
    predicate_types: dict[str, str] = {}

    prefix = raw_obj.get_str("builtin_prefix")
    if prefix is not None:
        prefix_str = prefix

    calls_obj = raw_obj.get_obj("calls")
    if calls_obj is not None:
        for key, value in calls_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                calls[key] = value_str

    types_obj = raw_obj.get_obj("types")
    if types_obj is not None:
        for key, value in types_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                types[key] = value_str

    skip_arr = raw_obj.get_arr("skip_modules")
    if skip_arr is not None:
        for item in skip_arr.raw:
            item_str = json.JsonValue(item).as_str()
            if item_str is not None:
                skip.append(item_str)

    skip_exact_arr = raw_obj.get_arr("skip_modules_exact")
    if skip_exact_arr is not None:
        for item in skip_exact_arr.raw:
            item_str = json.JsonValue(item).as_str()
            if item_str is not None:
                skip_exact.add(item_str)

    implicit_promotions_arr = raw_obj.get_arr("implicit_promotions")
    if implicit_promotions_arr is not None:
        for item in implicit_promotions_arr.raw:
            item_arr = json.JsonValue(item).as_arr()
            if item_arr is None:
                continue
            from_type = item_arr.get_str(0)
            to_type = item_arr.get_str(1)
            if from_type is not None and to_type is not None:
                implicit_promotions.add(from_type + "->" + to_type)

    module_native_files_obj = raw_obj.get_obj("module_native_files")
    if module_native_files_obj is not None:
        for key, value in module_native_files_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                module_native_files[key] = value_str

    module_namespace_exprs_obj = raw_obj.get_obj("module_namespace_exprs")
    if module_namespace_exprs_obj is not None:
        for key, value in module_namespace_exprs_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                module_namespace_exprs[key] = value_str

    call_adapters_obj = raw_obj.get_obj("call_adapters")
    if call_adapters_obj is not None:
        for key, value in call_adapters_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                call_adapters[key] = value_str

    non_native_modules_arr = raw_obj.get_arr("non_native_modules")
    if non_native_modules_arr is not None:
        for item in non_native_modules_arr.raw:
            item_str = json.JsonValue(item).as_str()
            if item_str is not None:
                non_native_modules.add(item_str)

    exception_types_arr = raw_obj.get_arr("exception_types")
    if exception_types_arr is not None:
        for item in exception_types_arr.raw:
            item_str = json.JsonValue(item).as_str()
            if item_str is not None:
                exception_types.add(item_str)

    predicate_types_obj = raw_obj.get_obj("predicate_types")
    if predicate_types_obj is not None:
        for key, value in predicate_types_obj.raw.items():
            value_str = json.JsonValue(value).as_str()
            if value_str is not None:
                predicate_types[key] = value_str

    return RuntimeMapping(
        builtin_prefix=prefix_str,
        calls=calls,
        types=types,
        skip_module_prefixes=skip,
        skip_module_exact=skip_exact,
        implicit_promotions=implicit_promotions,
        module_native_files=module_native_files,
        module_namespace_exprs=module_namespace_exprs,
        call_adapters=call_adapters,
        non_native_modules=non_native_modules,
        exception_types=exception_types,
        predicate_types=predicate_types,
    )


# ---------------------------------------------------------------------------
# Import alias map
# ---------------------------------------------------------------------------

def build_import_alias_map(meta: dict[str, JsonVal]) -> dict[str, str]:
    """Build a map from local alias → module_id from import metadata.

    e.g., {"math": "pytra.std.math", "path": "pytra.std.os_path"}
    """
    alias_map: dict[str, str] = {}

    ir = meta.get("import_resolution")
    ir_obj = json.JsonValue(ir).as_obj()
    if ir_obj is not None:
        bindings_arr = ir_obj.get_arr("bindings")
        if bindings_arr is not None:
            for binding in bindings_arr.raw:
                binding_obj = json.JsonValue(binding).as_obj()
                if binding_obj is None:
                    continue
                local_raw = binding_obj.get_str("local_name")
                if local_raw is None:
                    continue
                local: str = local_raw
                if local == "":
                    continue
                resolved_kind_raw = binding_obj.get_str("resolved_binding_kind")
                if resolved_kind_raw is None:
                    continue
                resolved_kind: str = resolved_kind_raw
                if resolved_kind != "module":
                    continue
                runtime_module_id_raw = binding_obj.get_str("runtime_module_id")
                if runtime_module_id_raw is None:
                    continue
                runtime_module_id: str = runtime_module_id_raw
                if runtime_module_id != "":
                    alias_map[local] = runtime_module_id

    # From import_modules: {alias: module_id}
    im = meta.get("import_modules")
    im_obj = json.JsonValue(im).as_obj()
    if im_obj is not None:
        for alias, mod_id in im_obj.raw.items():
            mod_id_str = json.JsonValue(mod_id).as_str()
            if mod_id_str is not None:
                alias_map[alias] = mod_id_str

    # From import_symbols: {alias: {module: str, name: str}}
    isyms = meta.get("import_symbols")
    isyms_obj = json.JsonValue(isyms).as_obj()
    if isyms_obj is not None:
        for alias, info in isyms_obj.raw.items():
            info_obj = json.JsonValue(info).as_obj()
            if info_obj is None:
                continue
            mod_raw = info_obj.get_str("module")
            if mod_raw is None:
                continue
            mod: str = mod_raw
            if mod != "" and alias not in alias_map:
                alias_map[alias] = mod

    return alias_map


def resolve_runtime_symbol_name(
    symbol: str,
    mapping: RuntimeMapping,
    *,
    module_id: str = "",
    resolved_runtime_call: str = "",
    runtime_call: str = "",
) -> str:
    """Resolve a runtime symbol/value name using mapping.json first.

    Used for skipped runtime module symbols where the emitter should render the
    native helper/value name instead of re-emitting a module reference.
    """
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


def should_skip_module(module_id: str, mapping: RuntimeMapping) -> bool:
    """Check if a module should be skipped (provided by native runtime)."""
    if module_id in mapping.skip_module_exact:
        return True
    if module_id == "pytra.built_in.error" or module_id == "pytra.built_in.type_id_table":
        return False
    for prefix in mapping.skip_module_prefixes:
        if module_id.startswith(prefix):
            return True
    return False


def build_runtime_import_map(
    meta: dict[str, JsonVal],
    mapping: RuntimeMapping,
) -> dict[str, str]:
    """Build local import name -> native/runtime symbol name for runtime bindings."""
    runtime_imports: dict[str, str] = {}
    bindings = meta.get("import_bindings")
    bindings_arr = json.JsonValue(bindings).as_arr()
    if bindings_arr is None:
        return runtime_imports

    for binding in bindings_arr.raw:
        binding_obj = json.JsonValue(binding).as_obj()
        if binding_obj is None:
            continue
        binding_kind_raw = binding_obj.get_str("binding_kind")
        if binding_kind_raw is None:
            continue
        binding_kind: str = binding_kind_raw
        if binding_kind != "symbol":
            continue
        local_name_raw = binding_obj.get_str("local_name")
        if local_name_raw is None:
            continue
        local_name: str = local_name_raw
        if local_name == "":
            continue
        # Skip module-resolved bindings (e.g. "from pytra.std import glob" where glob is a
        # namespace, not a callable symbol). These are handled via import_alias_modules.
        resolved_binding_kind_raw = binding_obj.get_str("resolved_binding_kind")
        if resolved_binding_kind_raw is not None:
            resolved_binding_kind: str = resolved_binding_kind_raw
            if resolved_binding_kind == "module":
                continue

        module_id_raw = binding_obj.get_str("runtime_module_id")
        if module_id_raw is None:
            module_id_raw = binding_obj.get_str("module_id")
        elif module_id_raw == "":
            module_id_raw = binding_obj.get_str("module_id")
        if module_id_raw is None:
            continue
        module_id: str = module_id_raw
        if module_id == "":
            continue

        export_name = binding_obj.get_str("export_name")
        export_symbol = local_name
        if export_name is not None and export_name != "":
            export_symbol = export_name
        full_module_id = module_id + "." + export_symbol
        is_runtime_namespace = module_id.startswith("pytra.")
        if not is_runtime_namespace:
            symbol_key = module_id + "." + export_symbol
            if symbol_key in mapping.calls:
                runtime_imports[local_name] = mapping.calls[symbol_key]
                continue
            if "." not in module_id:
                std_symbol_key = "pytra.std." + module_id + "." + export_symbol
                if std_symbol_key in mapping.calls:
                    runtime_imports[local_name] = mapping.calls[std_symbol_key]
                    continue
        else:
            full_symbol_key = module_id + "." + export_symbol
            if full_symbol_key in mapping.calls:
                runtime_imports[local_name] = mapping.calls[full_symbol_key]
                continue
            if export_symbol in mapping.calls:
                runtime_imports[local_name] = mapping.calls[export_symbol]
                continue
        if (
            not is_runtime_namespace
            and not should_skip_module(module_id, mapping)
            and not should_skip_module(full_module_id, mapping)
        ):
            continue

        runtime_symbol = binding_obj.get_str("runtime_symbol")
        symbol_name = export_symbol
        if runtime_symbol is not None and runtime_symbol != "":
            symbol_name = runtime_symbol
        is_native_runtime = (
            is_runtime_namespace
            and (
                should_skip_module(module_id, mapping)
                or should_skip_module(full_module_id, mapping)
            )
        )
        if is_runtime_namespace and not should_skip_module(module_id, mapping):
            # pytra.* helper module emitted by the backend: prefer its transpiled symbols.
            continue
        if is_runtime_namespace and not is_native_runtime:
            # pytra.* module that has its own compiled output file (not provided by py_runtime).
            # Skip from runtime_imports so _emit_import_stmt generates a proper module import.
            continue
        if is_native_runtime:
            if module_id in mapping.non_native_modules:
                # Module has its own compiled output file (not provided by py_runtime).
                # Skip from runtime_imports so _emit_import_stmt emits a proper module import.
                continue
            if symbol_name in mapping.calls:
                # Use explicit mapping.calls entry (highest priority)
                mapped = mapping.calls[symbol_name]
                resolved_symbol = mapped if mapped != "" else symbol_name
            else:
                resolved_symbol = resolve_runtime_symbol_name(symbol_name, mapping, module_id=module_id)
                if (
                    resolved_symbol == symbol_name
                    and module_id != ""
                    and "." not in module_id
                ):
                    std_module_id = "pytra.std." + module_id
                    std_resolved = resolve_runtime_symbol_name(symbol_name, mapping, module_id=std_module_id)
                    if std_resolved not in ("", symbol_name, mapping.builtin_prefix + symbol_name):
                        resolved_symbol = std_resolved
                if (
                    resolved_symbol == mapping.builtin_prefix + symbol_name
                    and symbol_name not in mapping.calls
                    and (module_id + "." + symbol_name) not in mapping.calls
                    and not symbol_name.startswith(mapping.builtin_prefix)
                ):
                    keep_prefixed = False
                    if module_id != "" and "." not in module_id:
                        std_key = "pytra.std." + module_id + "." + symbol_name
                        keep_prefixed = std_key in mapping.calls
                    if not keep_prefixed:
                        resolved_symbol = symbol_name
                if resolved_symbol == "":
                    # Same name in py_runtime/native file (e.g. deque, Path, etc.)
                    resolved_symbol = symbol_name
        else:
            resolved_symbol = symbol_name
            if should_skip_module(module_id, mapping) or should_skip_module(full_module_id, mapping):
                resolved_symbol = resolve_runtime_symbol_name(symbol_name, mapping, module_id=module_id)
                if (
                    resolved_symbol == mapping.builtin_prefix + symbol_name
                    and module_id != ""
                    and "." not in module_id
                ):
                    std_key = "pytra.std." + module_id + "." + symbol_name
                    if std_key in mapping.calls:
                        mapped_std = mapping.calls[std_key]
                        if mapped_std != "":
                            resolved_symbol = mapped_std
                    else:
                        resolved_symbol = symbol_name
        runtime_imports[local_name] = resolved_symbol

    return runtime_imports


# ---------------------------------------------------------------------------
# Runtime call resolution
# ---------------------------------------------------------------------------

def resolve_runtime_call(
    runtime_call: str,
    builtin_name: str,  # used only as legacy fallback when runtime_call == ""
    adapter_kind: str,
    mapping: RuntimeMapping,
) -> str:
    """Resolve a runtime_call to a target language function name."""
    # 1. Exact match
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]

    # 2. Builtin → prefix (no-dot runtime_call only)
    if adapter_kind == "builtin":
        if runtime_call != "" and "." not in runtime_call:
            # Avoid double-prefix: if runtime_call already starts with builtin_prefix, return as-is
            if mapping.builtin_prefix != "" and runtime_call.startswith(mapping.builtin_prefix):
                return runtime_call
            return mapping.builtin_prefix + runtime_call
        return ""

    # 3. Extern delegate → bare name (no prefix)
    if adapter_kind == "extern_delegate":
        return runtime_call

    # 4. Legacy fallback: runtime_call is absent but builtin_name is set (pre-S4 nodes).
    #    Used transitionally until all EAST3 nodes carry runtime_call (P0-BN-REMOVE-S4).
    if runtime_call == "" and builtin_name != "" and "." not in builtin_name:
        if builtin_name in mapping.calls:
            return mapping.calls[builtin_name]
        return mapping.builtin_prefix + builtin_name

    # 5. General fallback
    if runtime_call != "":
        if "." in runtime_call:
            return ""
        if mapping.builtin_prefix != "" and runtime_call.startswith(mapping.builtin_prefix):
            return runtime_call
        return mapping.builtin_prefix + runtime_call
    return ""


def resolve_type(east3_type: str, mapping: RuntimeMapping) -> str:
    """Resolve an EAST3 type name to a target language type string using mapping.json `types` table.

    Returns the mapped type string, or "" if the type is not found in the mapping.
    Callers should fall back to language-specific type logic when "" is returned.
    """
    return mapping.types.get(east3_type, "")

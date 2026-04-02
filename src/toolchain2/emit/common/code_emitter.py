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
    call_adapters: dict[str, str] = field(default_factory=dict)
    non_native_modules: set[str] = field(default_factory=set)
    exception_types: set[str] = field(default_factory=set)

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
    call_adapters: dict[str, str] = {}
    non_native_modules: set[str] = set()
    exception_types: set[str] = set()

    prefix = raw_obj.get_str("builtin_prefix")
    if prefix is not None:
        prefix_str = prefix

    calls_obj = raw_obj.get_obj("calls")
    if calls_obj is not None:
        for key, value in calls_obj.raw.items():
            if isinstance(key, str) and isinstance(value, str):
                calls[key] = value

    types_obj = raw_obj.get_obj("types")
    if types_obj is not None:
        for key, value in types_obj.raw.items():
            if isinstance(key, str) and isinstance(value, str):
                types[key] = value

    skip_arr = raw_obj.get_arr("skip_modules")
    if skip_arr is not None:
        for item in skip_arr.raw:
            if isinstance(item, str):
                skip.append(item)

    skip_exact_arr = raw_obj.get_arr("skip_modules_exact")
    if skip_exact_arr is not None:
        for item in skip_exact_arr.raw:
            if isinstance(item, str):
                skip_exact.add(item)

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
            if isinstance(key, str) and isinstance(value, str):
                module_native_files[key] = value

    call_adapters_obj = raw_obj.get_obj("call_adapters")
    if call_adapters_obj is not None:
        for key, value in call_adapters_obj.raw.items():
            if isinstance(key, str) and isinstance(value, str):
                call_adapters[key] = value

    non_native_modules_arr = raw_obj.get_arr("non_native_modules")
    if non_native_modules_arr is not None:
        for item in non_native_modules_arr.raw:
            if isinstance(item, str):
                non_native_modules.add(item)

    exception_types_arr = raw_obj.get_arr("exception_types")
    if exception_types_arr is not None:
        for item in exception_types_arr.raw:
            if isinstance(item, str):
                exception_types.add(item)

    return RuntimeMapping(
        builtin_prefix=prefix_str,
        calls=calls,
        types=types,
        skip_module_prefixes=skip,
        skip_module_exact=skip_exact,
        implicit_promotions=implicit_promotions,
        module_native_files=module_native_files,
        call_adapters=call_adapters,
        non_native_modules=non_native_modules,
        exception_types=exception_types,
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
    if isinstance(ir, dict):
        bindings = ir.get("bindings")
        if isinstance(bindings, list):
            for binding in bindings:
                if not isinstance(binding, dict):
                    continue
                local = binding.get("local_name")
                resolved_kind = binding.get("resolved_binding_kind")
                runtime_module_id = binding.get("runtime_module_id")
                if (
                    isinstance(local, str) and local != ""
                    and isinstance(resolved_kind, str) and resolved_kind == "module"
                    and isinstance(runtime_module_id, str) and runtime_module_id != ""
                ):
                    alias_map[local] = runtime_module_id

    # From import_modules: {alias: module_id}
    im = meta.get("import_modules")
    if isinstance(im, dict):
        for alias in im:
            mod_id = im[alias]
            if isinstance(alias, str) and isinstance(mod_id, str):
                alias_map[alias] = mod_id

    # From import_symbols: {alias: {module: str, name: str}}
    isyms = meta.get("import_symbols")
    if isinstance(isyms, dict):
        for alias in isyms:
            info = isyms[alias]
            if isinstance(alias, str) and isinstance(info, dict):
                mod = info.get("module")
                name = info.get("name")
                if isinstance(mod, str) and mod != "" and alias not in alias_map:
                    nested_mod = ""
                    if isinstance(name, str) and name != "":
                        root = Path(__file__).resolve().parents[3]
                        nested_py = root
                        for part in (mod + "." + name).split("."):
                            nested_py = nested_py / part
                        nested_py = nested_py.with_suffix(".py")
                        if nested_py.exists():
                            nested_mod = mod + "." + name
                    alias_map[alias] = nested_mod if nested_mod != "" else mod

    return alias_map


def resolve_runtime_symbol_name(
    symbol: str,
    mapping: RuntimeMapping,
    *,
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
    if symbol in mapping.calls:
        return mapping.calls[symbol]
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
    if not isinstance(bindings, list):
        return runtime_imports

    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        binding_kind = binding.get("binding_kind")
        local_name = binding.get("local_name")
        if not isinstance(binding_kind, str) or binding_kind != "symbol":
            continue
        if not isinstance(local_name, str) or local_name == "":
            continue
        # Skip module-resolved bindings (e.g. "from pytra.std import glob" where glob is a
        # namespace, not a callable symbol). These are handled via import_alias_modules.
        resolved_binding_kind = binding.get("resolved_binding_kind")
        if isinstance(resolved_binding_kind, str) and resolved_binding_kind == "module":
            continue

        module_id = binding.get("runtime_module_id")
        if not isinstance(module_id, str) or module_id == "":
            module_id = binding.get("module_id")
        if not isinstance(module_id, str) or module_id == "":
            continue

        export_name = binding.get("export_name")
        export_symbol = local_name
        if isinstance(export_name, str) and export_name != "":
            export_symbol = export_name
        full_module_id = module_id + "." + export_symbol
        is_runtime_namespace = module_id.startswith("pytra.")
        if not is_runtime_namespace:
            symbol_key = module_id + "." + export_symbol
            if symbol_key in mapping.calls:
                runtime_imports[local_name] = mapping.calls[symbol_key]
                continue
        if (
            not is_runtime_namespace
            and not should_skip_module(module_id, mapping)
            and not should_skip_module(full_module_id, mapping)
        ):
            continue

        runtime_symbol = binding.get("runtime_symbol")
        symbol_name = export_symbol
        if isinstance(runtime_symbol, str) and runtime_symbol != "":
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
                resolved_symbol = mapped if isinstance(mapped, str) and mapped != "" else symbol_name
            elif symbol_name.startswith(mapping.builtin_prefix):
                # Has prefix → resolve (may strip prefix)
                resolved_symbol = resolve_runtime_symbol_name(symbol_name, mapping)
            else:
                # Same name in py_runtime (e.g. deque, Path, etc.)
                resolved_symbol = symbol_name
        else:
            resolved_symbol = symbol_name
        runtime_imports[local_name] = resolved_symbol

    return runtime_imports


# ---------------------------------------------------------------------------
# Runtime call resolution
# ---------------------------------------------------------------------------

def resolve_runtime_call(
    runtime_call: str,
    builtin_name: str,
    adapter_kind: str,
    mapping: RuntimeMapping,
) -> str:
    """Resolve a runtime_call to a target language function name."""
    # 1. Exact match
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]

    # 2. builtin_name match
    if builtin_name != "" and builtin_name in mapping.calls:
        return mapping.calls[builtin_name]

    # 3. Builtin → prefix
    if adapter_kind == "builtin":
        if builtin_name != "":
            return mapping.builtin_prefix + builtin_name
        if runtime_call != "" and "." not in runtime_call:
            return mapping.builtin_prefix + runtime_call
        return ""

    # 4. Extern delegate → bare name (no prefix)
    if adapter_kind == "extern_delegate":
        return builtin_name if builtin_name != "" else runtime_call

    # 5. Fallback
    if runtime_call != "":
        if "." in runtime_call:
            return ""
        return mapping.builtin_prefix + runtime_call
    if builtin_name != "":
        return mapping.builtin_prefix + builtin_name
    return ""


def resolve_type(east3_type: str, mapping: RuntimeMapping) -> str:
    """Resolve an EAST3 type name to a target language type string using mapping.json `types` table.

    Returns the mapped type string, or "" if the type is not found in the mapping.
    Callers should fall back to language-specific type logic when "" is returned.
    """
    return mapping.types.get(east3_type, "")

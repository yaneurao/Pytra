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
      "skip_modules": ["pytra.built_in.", "pytra.std.", "pytra.utils.", "pytra.core."]
    }
    """
    builtin_prefix: str = "__pytra_"
    calls: dict[str, str] = field(default_factory=dict)
    skip_module_prefixes: list[str] = field(default_factory=list)
    skip_module_exact: set[str] = field(default_factory=set)
    implicit_promotions: set[str] = field(default_factory=set)

    def is_implicit_cast(self, from_type: str, to_type: str) -> bool:
        return (from_type + "->" + to_type) in self.implicit_promotions


def load_runtime_mapping(mapping_path: Path) -> RuntimeMapping:
    """Load a mapping.json file into a RuntimeMapping."""
    if not mapping_path.exists():
        return RuntimeMapping()
    text = mapping_path.read_text(encoding="utf-8")
    raw_obj = json.loads_obj(text)
    if raw_obj is None:
        return RuntimeMapping()
    raw = raw_obj.raw

    prefix_str = "__pytra_"
    if "builtin_prefix" in raw:
        prefix = raw["builtin_prefix"]
        if isinstance(prefix, str):
            prefix_str = str(prefix)

    calls_raw: JsonVal = None
    if "calls" in raw:
        calls_raw = raw["calls"]
    calls: dict[str, str] = {}
    if isinstance(calls_raw, dict):
        for key, v in calls_raw.items():
            if isinstance(v, str):
                calls[key] = v

    skip_raw: JsonVal = None
    if "skip_modules" in raw:
        skip_raw = raw["skip_modules"]
    skip: list[str] = []
    if isinstance(skip_raw, list):
        for item in skip_raw:
            if isinstance(item, str):
                skip_item = str(item)
                skip.append(skip_item)

    skip_exact_raw: JsonVal = None
    if "skip_modules_exact" in raw:
        skip_exact_raw = raw["skip_modules_exact"]
    skip_exact: set[str] = set()
    if isinstance(skip_exact_raw, list):
        for item in skip_exact_raw:
            if isinstance(item, str):
                skip_exact.add(str(item))

    implicit_promotions_raw: JsonVal = None
    if "implicit_promotions" in raw:
        implicit_promotions_raw = raw["implicit_promotions"]
    implicit_promotions: set[str] = set()
    if isinstance(implicit_promotions_raw, list):
        for item in implicit_promotions_raw:
            if isinstance(item, list):
                item_list = cast(list[JsonVal], item)
                if len(item_list) == 2:
                    from_type = item_list[0]
                    to_type = item_list[1]
                    if isinstance(from_type, str) and isinstance(to_type, str):
                        implicit_promotions.add(from_type + "->" + to_type)

    return RuntimeMapping(
        builtin_prefix=prefix_str,
        calls=calls,
        skip_module_prefixes=skip,
        skip_module_exact=skip_exact,
        implicit_promotions=implicit_promotions,
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
        for alias, mod_id in im.items():
            if isinstance(alias, str) and isinstance(mod_id, str):
                alias_map[alias] = mod_id

    # From import_symbols: {alias: {module: str, name: str}}
    isyms = meta.get("import_symbols")
    if isinstance(isyms, dict):
        for alias, info in isyms.items():
            if isinstance(alias, str) and isinstance(info, dict):
                mod = info.get("module")
                if isinstance(mod, str) and mod != "" and alias not in alias_map:
                    alias_map[alias] = mod

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
        if is_native_runtime:
            if symbol_name in mapping.calls:
                # Use explicit mapping.calls entry (highest priority)
                mapped = mapping.calls[symbol_name]
                resolved_symbol = mapped if isinstance(mapped, str) and mapped != "" else symbol_name
            elif not symbol_name.startswith(mapping.builtin_prefix):
                # No prefix → use as-is
                resolved_symbol = symbol_name
            else:
                # Has prefix → resolve (may strip prefix)
                resolved_symbol = resolve_runtime_symbol_name(symbol_name, mapping)
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


def should_skip_module(module_id: str, mapping: RuntimeMapping) -> bool:
    """Check if a module should be skipped (provided by native runtime)."""
    if module_id == "pytra.built_in.error" or module_id == "pytra.built_in.type_id_table":
        return False
    if module_id in mapping.skip_module_exact:
        return True
    for prefix in mapping.skip_module_prefixes:
        if module_id.startswith(prefix):
            return True
    return False

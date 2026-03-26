"""CodeEmitter 基底クラス + runtime mapping 解決。

全 emitter が共有するロジック:
- runtime_call → ターゲット関数名の解決 (mapping.json)
- runtime_call_adapter_kind 判定 (builtin/extern_delegate)
- import alias 構築
- module skip 判定

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path


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


def load_runtime_mapping(mapping_path: Path) -> RuntimeMapping:
    """Load a mapping.json file into a RuntimeMapping."""
    if not mapping_path.exists():
        return RuntimeMapping()
    text = mapping_path.read_text(encoding="utf-8")
    raw = json.loads(text).raw
    if not isinstance(raw, dict):
        return RuntimeMapping()

    prefix = raw.get("builtin_prefix")
    prefix_str = prefix if isinstance(prefix, str) else "__pytra_"

    calls_raw = raw.get("calls")
    calls: dict[str, str] = {}
    if isinstance(calls_raw, dict):
        for k, v in calls_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                calls[k] = v

    skip_raw = raw.get("skip_modules")
    skip: list[str] = []
    if isinstance(skip_raw, list):
        for item in skip_raw:
            if isinstance(item, str):
                skip.append(item)

    return RuntimeMapping(
        builtin_prefix=prefix_str,
        calls=calls,
        skip_module_prefixes=skip,
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
                if isinstance(mod, str) and mod != "":
                    alias_map[alias] = mod

    return alias_map


# ---------------------------------------------------------------------------
# Runtime call resolution
# ---------------------------------------------------------------------------

def resolve_runtime_call(
    runtime_call: str,
    builtin_name: str,
    adapter_kind: str,
    mapping: RuntimeMapping,
) -> str:
    """Resolve a runtime_call to a target language function name.

    Priority:
    1. Exact match in mapping.calls
    2. builtin_name match in mapping.calls
    3. adapter_kind == "builtin" → prefix + builtin_name
    4. adapter_kind == "extern_delegate" → bare function name
    5. Fallback: prefix + runtime_call
    """
    # 1. Exact match
    if runtime_call in mapping.calls:
        return mapping.calls[runtime_call]

    # 2. builtin_name match
    if builtin_name != "" and builtin_name in mapping.calls:
        return mapping.calls[builtin_name]

    # 3. Builtin → prefix
    if adapter_kind == "builtin":
        return mapping.builtin_prefix + builtin_name if builtin_name != "" else mapping.builtin_prefix + runtime_call

    # 4. Extern delegate → bare name (no prefix)
    if adapter_kind == "extern_delegate":
        return builtin_name if builtin_name != "" else runtime_call

    # 5. Fallback
    if runtime_call != "":
        return mapping.builtin_prefix + runtime_call
    if builtin_name != "":
        return mapping.builtin_prefix + builtin_name
    return ""


def should_skip_module(module_id: str, mapping: RuntimeMapping) -> bool:
    """Check if a module should be skipped (provided by native runtime)."""
    for prefix in mapping.skip_module_prefixes:
        if module_id.startswith(prefix):
            return True
    return False

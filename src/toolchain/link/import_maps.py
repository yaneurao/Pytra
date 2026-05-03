"""Import map extraction from EAST3 meta.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
ロジック参照元: toolchain/compile/east3_opt_passes/non_escape_call_graph.py (import はしない)。
"""

from __future__ import annotations

from pytra.std.json import JsonVal
from toolchain.compile.jv import jv_str, jv_is_dict, jv_dict, nd_get_dict, nd_get_str


def collect_import_modules(east_doc: dict[str, JsonVal]) -> dict[str, str]:
    """Extract meta.import_modules from EAST3 meta."""
    import_modules: dict[str, str] = {}
    meta: dict[str, JsonVal] = nd_get_dict(east_doc, "meta")
    if len(meta) == 0:
        return import_modules
    im_map: dict[str, JsonVal] = nd_get_dict(meta, "import_modules")
    if len(im_map) == 0:
        return import_modules
    for alias, mod_val in im_map.items():
        mod_id: str = jv_str(mod_val)
        if alias != "" and mod_id != "":
            import_modules[alias] = "" + mod_id
    return import_modules


def collect_import_symbols(east_doc: dict[str, JsonVal]) -> dict[str, str]:
    """Extract meta.import_symbols from EAST3 meta."""
    import_symbols: dict[str, str] = {}
    meta: dict[str, JsonVal] = nd_get_dict(east_doc, "meta")
    if len(meta) == 0:
        return import_symbols
    is_map: dict[str, JsonVal] = nd_get_dict(meta, "import_symbols")
    if len(is_map) == 0:
        return import_symbols
    for alias, info_val in is_map.items():
        if not jv_is_dict(info_val):
            continue
        info: dict[str, JsonVal] = jv_dict(info_val)
        mod: str = nd_get_str(info, "module")
        name: str = nd_get_str(info, "name")
        if alias != "" and mod != "" and name != "":
            import_symbols[alias] = mod + "::" + name
    return import_symbols


def collect_import_maps(
    east_doc: dict[str, JsonVal],
) -> tuple[dict[str, str], dict[str, str]]:
    """Extract import_modules and import_symbols from EAST3 meta."""
    return collect_import_modules(east_doc), collect_import_symbols(east_doc)

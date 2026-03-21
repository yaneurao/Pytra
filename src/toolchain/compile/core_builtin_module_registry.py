"""Built-in function → runtime module mapping for implicit import binding generation.

Maps semantic tags and runtime_call names used in EAST1 nodes to the
``pytra.built_in.*`` module that provides their implementation.  The EAST1
parser uses this table to inject implicit ``import_bindings`` so the linker
can include the required ``.east`` modules in the link-output manifest.
"""

from __future__ import annotations

from typing import Any

# semantic_tag prefix → built-in module ID
_SEMANTIC_TAG_MODULE: dict[str, str] = {
    "core.print": "pytra.built_in.io_ops",
    "core.len": "pytra.built_in.sequence",
    "iter.range": "pytra.built_in.sequence",
    "iter.zip": "pytra.built_in.zip_ops",
    "iter.init": "pytra.built_in.iter_ops",
    "iter.next": "pytra.built_in.iter_ops",
    "iter.reversed": "pytra.built_in.iter_ops",
    "iter.enumerate": "pytra.built_in.iter_ops",
    "cast.str": "pytra.built_in.scalar_ops",
    "cast.int": "pytra.built_in.scalar_ops",
    "cast.float": "pytra.built_in.scalar_ops",
    "cast.bool": "pytra.built_in.scalar_ops",
    "cast.ord": "pytra.built_in.scalar_ops",
    "cast.chr": "pytra.built_in.scalar_ops",
    "math.min": "pytra.built_in.numeric_ops",
    "math.max": "pytra.built_in.numeric_ops",
    "logic.any": "pytra.built_in.predicates",
    "logic.all": "pytra.built_in.predicates",
    "io.open": "pytra.built_in.io_ops",
}

# runtime_call name → built-in module ID
_RUNTIME_CALL_MODULE: dict[str, str] = {
    "py_print": "pytra.built_in.io_ops",
    "py_len": "pytra.built_in.sequence",
    "py_range": "pytra.built_in.sequence",
    "py_repeat": "pytra.built_in.sequence",
    "py_to_string": "pytra.built_in.scalar_ops",
    "py_to_bool": "pytra.built_in.scalar_ops",
    "py_to_int64_base": "pytra.built_in.scalar_ops",
    "py_ord": "pytra.built_in.scalar_ops",
    "py_chr": "pytra.built_in.scalar_ops",
    "py_enumerate": "pytra.built_in.iter_ops",
    "py_reversed_object": "pytra.built_in.iter_ops",
    "py_enumerate_object": "pytra.built_in.iter_ops",
    "py_iter_or_raise": "pytra.built_in.iter_ops",
    "py_next_or_stop": "pytra.built_in.iter_ops",
    "py_any": "pytra.built_in.predicates",
    "py_all": "pytra.built_in.predicates",
    "py_contains": "pytra.built_in.contains",
    "py_contains_dict_object": "pytra.built_in.contains",
    "py_contains_list_object": "pytra.built_in.contains",
    "py_sum": "pytra.built_in.numeric_ops",
    "py_min": "pytra.built_in.numeric_ops",
    "py_max": "pytra.built_in.numeric_ops",
    "py_zip": "pytra.built_in.zip_ops",
    "py_str_split": "pytra.built_in.string_ops",
    "py_str_join": "pytra.built_in.string_ops",
    "py_str_strip": "pytra.built_in.string_ops",
    "py_str_lstrip": "pytra.built_in.string_ops",
    "py_str_rstrip": "pytra.built_in.string_ops",
    "py_str_replace": "pytra.built_in.string_ops",
    "py_str_startswith": "pytra.built_in.string_ops",
    "py_str_endswith": "pytra.built_in.string_ops",
    "py_str_find": "pytra.built_in.string_ops",
    "py_str_rfind": "pytra.built_in.string_ops",
    "py_str_count": "pytra.built_in.string_ops",
    "py_str_upper": "pytra.built_in.string_ops",
    "py_str_lower": "pytra.built_in.string_ops",
    "py_str_isdigit": "pytra.built_in.string_ops",
    "py_str_isalpha": "pytra.built_in.string_ops",
    "py_str_isalnum": "pytra.built_in.string_ops",
    "py_format_value": "pytra.built_in.format_value",
}


def resolve_builtin_module(semantic_tag: str, runtime_call: str) -> str:
    """Return the built-in module ID for a semantic tag or runtime call, or ''."""
    if semantic_tag != "":
        mod = _SEMANTIC_TAG_MODULE.get(semantic_tag, "")
        if mod != "":
            return mod
    if runtime_call != "":
        mod = _RUNTIME_CALL_MODULE.get(runtime_call, "")
        if mod != "":
            return mod
    return ""


def collect_implicit_builtin_modules(body: list[Any]) -> set[str]:
    """Walk EAST body and return set of built-in module IDs used."""
    modules: set[str] = set()
    _walk_collect(body, modules)
    return modules


def _walk_collect(node: Any, modules: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_collect(item, modules)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node
    semantic_tag = nd.get("semantic_tag")
    runtime_call = nd.get("runtime_call")
    stag = semantic_tag if isinstance(semantic_tag, str) else ""
    rcall = runtime_call if isinstance(runtime_call, str) else ""
    if stag != "" or rcall != "":
        mod = resolve_builtin_module(stag, rcall)
        if mod != "":
            modules.add(mod)
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _walk_collect(value, modules)

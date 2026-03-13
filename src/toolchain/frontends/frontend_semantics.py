"""Frontend semantic-tag helpers for Python-origin EAST2 payloads."""

from __future__ import annotations


_BUILTIN_SEMANTIC_TAGS: dict[str, str] = {
    "print": "core.print",
    "len": "core.len",
    "range": "iter.range",
    "zip": "iter.zip",
    "iter": "iter.init",
    "next": "iter.next",
    "reversed": "iter.reversed",
    "enumerate": "iter.enumerate",
    "str": "cast.str",
    "int": "cast.int",
    "float": "cast.float",
    "bool": "cast.bool",
    "ord": "cast.ord",
    "chr": "cast.chr",
    "min": "math.min",
    "max": "math.max",
    "any": "logic.any",
    "all": "logic.all",
    "bytes": "ctor.bytes",
    "bytearray": "ctor.bytearray",
    "list": "ctor.list",
    "set": "ctor.set",
    "dict": "ctor.dict",
    "open": "io.open",
    "Exception": "error.raise_ctor",
    "RuntimeError": "error.raise_ctor",
    "NotImplementedError": "error.raise_ctor",
    "isinstance": "type.isinstance",
    "issubclass": "type.issubclass",
}

_RUNTIME_BINDING_SEMANTIC_TAGS: dict[tuple[str, str], str] = {
    ("pytra.std.json", "loads"): "json.loads",
    ("pytra.std.json", "loads_obj"): "json.loads_obj",
    ("pytra.std.json", "loads_arr"): "json.loads_arr",
}

_OWNER_METHOD_SEMANTIC_TAGS: dict[tuple[str, str], str] = {
    ("JsonValue", "as_obj"): "json.value.as_obj",
    ("JsonValue", "as_arr"): "json.value.as_arr",
    ("JsonValue", "as_str"): "json.value.as_str",
    ("JsonValue", "as_int"): "json.value.as_int",
    ("JsonValue", "as_float"): "json.value.as_float",
    ("JsonValue", "as_bool"): "json.value.as_bool",
    ("JsonObj", "get"): "json.obj.get",
    ("JsonObj", "get_obj"): "json.obj.get_obj",
    ("JsonObj", "get_arr"): "json.obj.get_arr",
    ("JsonObj", "get_str"): "json.obj.get_str",
    ("JsonObj", "get_int"): "json.obj.get_int",
    ("JsonObj", "get_float"): "json.obj.get_float",
    ("JsonObj", "get_bool"): "json.obj.get_bool",
    ("JsonArr", "get"): "json.arr.get",
    ("JsonArr", "get_obj"): "json.arr.get_obj",
    ("JsonArr", "get_arr"): "json.arr.get_arr",
    ("JsonArr", "get_str"): "json.arr.get_str",
    ("JsonArr", "get_int"): "json.arr.get_int",
    ("JsonArr", "get_float"): "json.arr.get_float",
    ("JsonArr", "get_bool"): "json.arr.get_bool",
}


def lookup_builtin_semantic_tag(name: str) -> str:
    return _BUILTIN_SEMANTIC_TAGS.get(name, "")


def lookup_stdlib_function_semantic_tag(name: str) -> str:
    if name == "":
        return ""
    return "stdlib.fn." + name


def lookup_stdlib_symbol_semantic_tag(name: str) -> str:
    if name == "":
        return ""
    return "stdlib.symbol." + name


def lookup_stdlib_method_semantic_tag(name: str) -> str:
    if name == "":
        return ""
    return "stdlib.method." + name


def lookup_runtime_binding_semantic_tag(module_id: str, symbol: str) -> str:
    mod = module_id.strip()
    sym = symbol.strip()
    if mod == "" or sym == "":
        return ""
    return _RUNTIME_BINDING_SEMANTIC_TAGS.get((mod, sym), "")


def lookup_owner_method_semantic_tag(owner_type: str, name: str) -> str:
    owner = owner_type.strip()
    method = name.strip()
    if owner == "" or method == "":
        return ""
    return _OWNER_METHOD_SEMANTIC_TAGS.get((owner, method), "")

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
    "isinstance": "type.isinstance",
    "issubclass": "type.issubclass",
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

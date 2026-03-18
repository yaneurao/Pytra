"""Read stdlib signatures from `pytra/std` as compiler source-of-truth."""

from __future__ import annotations

from pytra.std import re
from pytra.std.pathlib import Path
from toolchain.frontends.type_expr import normalize_type_text


_DEF_PATTERN = r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$"
_CLASS_PATTERN = r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$"

_FUNC_RETURNS_CACHE: dict[str, str] | None = None
_METHOD_RETURNS_CACHE: dict[str, dict[str, str]] | None = None

_FUNCTION_RUNTIME_CALLS: dict[str, str] = {
    "perf_counter": "perf_counter",
}

_FUNCTION_RUNTIME_BINDINGS: dict[str, tuple[str, str]] = {
    "perf_counter": ("pytra.std.time", "perf_counter"),
}

_IMPORTED_SYMBOL_RETURNS: dict[tuple[str, str], str] = {
    ("pathlib", "Path"): "Path",
    ("pytra.std.pathlib", "Path"): "Path",
}

_IMPORTED_SYMBOL_RUNTIME_BINDINGS: dict[tuple[str, str], tuple[str, str]] = {
    ("pathlib", "Path"): ("pytra.std.pathlib", "Path"),
    ("pytra.std.pathlib", "Path"): ("pytra.std.pathlib", "Path"),
}

_IMPORTED_SYMBOL_RUNTIME_CALLS: dict[tuple[str, str], str] = {
    ("pathlib", "Path"): "Path",
    ("pytra.std.pathlib", "Path"): "Path",
}

_NONCPP_IMPORTED_SYMBOL_RUNTIME_CALLS: dict[tuple[str, str], str] = {
    ("pytra.std.json", "loads"): "json.loads",
    ("pytra.std.json", "loads_obj"): "json.loads_obj",
    ("pytra.std.json", "loads_arr"): "json.loads_arr",
    ("pytra.std.json", "dumps"): "json.dumps",
    ("json", "loads"): "json.loads",
    ("json", "loads_obj"): "json.loads_obj",
    ("json", "loads_arr"): "json.loads_arr",
    ("json", "dumps"): "json.dumps",
    ("pytra.utils.png", "write_rgb_png"): "write_rgb_png",
    ("pytra.utils.gif", "save_gif"): "save_gif",
    ("pytra.utils.gif", "grayscale_palette"): "grayscale_palette",
    ("pytra.utils.assertions", "py_assert_stdout"): "py_assert_stdout",
    ("pytra.utils.assertions", "py_assert_eq"): "py_assert_eq",
    ("pytra.utils.assertions", "py_assert_true"): "py_assert_true",
    ("pytra.utils.assertions", "py_assert_all"): "py_assert_all",
    ("math", "sqrt"): "math.sqrt",
    ("math", "sin"): "math.sin",
    ("math", "cos"): "math.cos",
    ("math", "tan"): "math.tan",
    ("math", "exp"): "math.exp",
    ("math", "log"): "math.log",
    ("math", "log10"): "math.log10",
    ("math", "fabs"): "math.fabs",
    ("math", "floor"): "math.floor",
    ("math", "ceil"): "math.ceil",
    ("math", "pow"): "math.pow",
    ("pytra.std.math", "sqrt"): "math.sqrt",
    ("pytra.std.math", "sin"): "math.sin",
    ("pytra.std.math", "cos"): "math.cos",
    ("pytra.std.math", "tan"): "math.tan",
    ("pytra.std.math", "exp"): "math.exp",
    ("pytra.std.math", "log"): "math.log",
    ("pytra.std.math", "log10"): "math.log10",
    ("pytra.std.math", "fabs"): "math.fabs",
    ("pytra.std.math", "floor"): "math.floor",
    ("pytra.std.math", "ceil"): "math.ceil",
    ("pytra.std.math", "pow"): "math.pow",
}

_NONCPP_MODULE_ATTR_RUNTIME_CALLS: dict[tuple[str, str], str] = {
    ("json", "loads"): "json.loads",
    ("json", "loads_obj"): "json.loads_obj",
    ("json", "loads_arr"): "json.loads_arr",
    ("json", "dumps"): "json.dumps",
    ("pytra.std.json", "loads"): "json.loads",
    ("pytra.std.json", "loads_obj"): "json.loads_obj",
    ("pytra.std.json", "loads_arr"): "json.loads_arr",
    ("pytra.std.json", "dumps"): "json.dumps",
    ("pytra.utils.png", "write_rgb_png"): "write_rgb_png",
    ("pytra.utils.gif", "save_gif"): "save_gif",
    ("pytra.utils.gif", "grayscale_palette"): "grayscale_palette",
    ("math", "pi"): "math.pi",
    ("math", "e"): "math.e",
    ("math", "sqrt"): "math.sqrt",
    ("math", "sin"): "math.sin",
    ("math", "cos"): "math.cos",
    ("math", "tan"): "math.tan",
    ("math", "exp"): "math.exp",
    ("math", "log"): "math.log",
    ("math", "log10"): "math.log10",
    ("math", "fabs"): "math.fabs",
    ("math", "floor"): "math.floor",
    ("math", "ceil"): "math.ceil",
    ("math", "pow"): "math.pow",
    ("pytra.std.math", "pi"): "math.pi",
    ("pytra.std.math", "e"): "math.e",
    ("pytra.std.math", "sqrt"): "math.sqrt",
    ("pytra.std.math", "sin"): "math.sin",
    ("pytra.std.math", "cos"): "math.cos",
    ("pytra.std.math", "tan"): "math.tan",
    ("pytra.std.math", "exp"): "math.exp",
    ("pytra.std.math", "log"): "math.log",
    ("pytra.std.math", "log10"): "math.log10",
    ("pytra.std.math", "fabs"): "math.fabs",
    ("pytra.std.math", "floor"): "math.floor",
    ("pytra.std.math", "ceil"): "math.ceil",
    ("pytra.std.math", "pow"): "math.pow",
}

_OWNER_METHOD_RUNTIME_CALLS: dict[str, dict[str, str]] = {
    "str": {
        "strip": "py_strip",
        "lstrip": "py_lstrip",
        "rstrip": "py_rstrip",
        "startswith": "py_startswith",
        "endswith": "py_endswith",
        "find": "py_find",
        "rfind": "py_rfind",
        "replace": "py_replace",
        "join": "py_join",
        "isdigit": "py_isdigit",
        "isalpha": "py_isalpha",
    },
    "Path": {
        "mkdir": "std::filesystem::create_directories",
        "exists": "std::filesystem::exists",
        "write_text": "py_write_text",
        "read_text": "py_read_text",
        "parent": "path_parent",
        "name": "path_name",
        "stem": "path_stem",
    },
    "int": {
        "to_bytes": "py_int_to_bytes",
    },
    "list": {
        "append": "list.append",
        "extend": "list.extend",
        "pop": "list.pop",
        "clear": "list.clear",
        "reverse": "list.reverse",
        "sort": "list.sort",
    },
    "set": {
        "add": "set.add",
        "discard": "set.discard",
        "remove": "set.remove",
        "clear": "set.clear",
    },
    "dict": {
        "get": "dict.get",
        "pop": "dict.pop",
        "items": "dict.items",
        "keys": "dict.keys",
        "values": "dict.values",
        "clear": "dict.clear",
    },
    "unknown": {
        "append": "list.append",
        "extend": "list.extend",
        "pop": "list.pop",
        "get": "dict.get",
        "items": "dict.items",
        "keys": "dict.keys",
        "values": "dict.values",
        "isdigit": "py_isdigit",
        "isalpha": "py_isalpha",
    },
}

_OWNER_METHOD_RUNTIME_BINDINGS: dict[str, dict[str, tuple[str, str]]] = {
    "str": {
        "strip": ("pytra.built_in.string_ops", "str.strip"),
        "lstrip": ("pytra.built_in.string_ops", "str.lstrip"),
        "rstrip": ("pytra.built_in.string_ops", "str.rstrip"),
        "startswith": ("pytra.built_in.string_ops", "str.startswith"),
        "endswith": ("pytra.built_in.string_ops", "str.endswith"),
        "find": ("pytra.built_in.string_ops", "str.find"),
        "rfind": ("pytra.built_in.string_ops", "str.rfind"),
        "replace": ("pytra.built_in.string_ops", "str.replace"),
        "join": ("pytra.built_in.string_ops", "str.join"),
        "isdigit": ("pytra.built_in.string_ops", "str.isdigit"),
        "isalpha": ("pytra.built_in.string_ops", "str.isalpha"),
    },
    "Path": {
        "mkdir": ("pytra.std.pathlib", "Path.mkdir"),
        "exists": ("pytra.std.pathlib", "Path.exists"),
        "write_text": ("pytra.std.pathlib", "Path.write_text"),
        "read_text": ("pytra.std.pathlib", "Path.read_text"),
        "parent": ("pytra.std.pathlib", "Path.parent"),
        "name": ("pytra.std.pathlib", "Path.name"),
        "stem": ("pytra.std.pathlib", "Path.stem"),
    },
    "int": {
        "to_bytes": ("pytra.core.py_runtime", "int.to_bytes"),
    },
    "list": {
        "append": ("pytra.core.list", "list.append"),
        "extend": ("pytra.core.list", "list.extend"),
        "pop": ("pytra.core.list", "list.pop"),
        "clear": ("pytra.core.list", "list.clear"),
        "reverse": ("pytra.core.list", "list.reverse"),
        "sort": ("pytra.core.list", "list.sort"),
    },
    "set": {
        "add": ("pytra.core.set", "set.add"),
        "discard": ("pytra.core.set", "set.discard"),
        "remove": ("pytra.core.set", "set.remove"),
        "clear": ("pytra.core.set", "set.clear"),
    },
    "dict": {
        "get": ("pytra.core.dict", "dict.get"),
        "pop": ("pytra.core.dict", "dict.pop"),
        "items": ("pytra.core.dict", "dict.items"),
        "keys": ("pytra.core.dict", "dict.keys"),
        "values": ("pytra.core.dict", "dict.values"),
        "clear": ("pytra.core.dict", "dict.clear"),
    },
    "unknown": {
        "append": ("pytra.core.list", "list.append"),
        "extend": ("pytra.core.list", "list.extend"),
        "pop": ("pytra.core.list", "list.pop"),
        "get": ("pytra.core.dict", "dict.get"),
        "items": ("pytra.core.dict", "dict.items"),
        "keys": ("pytra.core.dict", "dict.keys"),
        "values": ("pytra.core.dict", "dict.values"),
        "isdigit": ("pytra.built_in.string_ops", "str.isdigit"),
        "isalpha": ("pytra.built_in.string_ops", "str.isalpha"),
    },
}

_OWNER_ATTRIBUTE_TYPES: dict[str, dict[str, str]] = {
    "Path": {
        "name": "str",
        "stem": "str",
        "parent": "Path",
    },
}


def _std_root() -> Path:
    return Path(__file__).resolve().parents[2] / "pytra" / "std"


def _strip_quotes(text: str) -> str:
    t = text.strip()
    if len(t) >= 2 and ((t[0] == "'" and t[-1] == "'") or (t[0] == '"' and t[-1] == '"')):
        return t[1:-1].strip()
    return t


def _split_top_level(text: str, sep: str) -> list[str]:
    out: list[str] = []
    buf = ""
    depth = 0
    i = 0
    n = len(text)
    sep_len = len(sep)
    while i < n:
        ch = text[i]
        if ch == "[":
            depth += 1
            buf += ch
            i += 1
            continue
        if ch == "]":
            depth -= 1
            buf += ch
            i += 1
            continue
        if depth == 0 and text.startswith(sep, i):
            item = buf.strip()
            if item != "":
                out.append(item)
            buf = ""
            i += sep_len
            continue
        buf += ch
        i += 1
    tail = buf.strip()
    if tail != "":
        out.append(tail)
    return out


def _normalize_return_type(raw_type: str) -> str:
    t = _strip_quotes(raw_type.strip())
    if t == "":
        return ""
    return normalize_type_text(t)


def _load_signature_cache() -> None:
    global _FUNC_RETURNS_CACHE, _METHOD_RETURNS_CACHE
    if _FUNC_RETURNS_CACHE is not None and _METHOD_RETURNS_CACHE is not None:
        return

    fn_returns: dict[str, str] = {}
    method_returns: dict[str, dict[str, str]] = {}
    std_root = _std_root()
    py_files = [p for p in std_root.glob("*.py")]
    py_files = sorted(py_files, key=lambda p: str(p))

    for src_path in py_files:
        name = src_path.name
        if name == "__init__.py":
            continue
        if name.endswith("_impl.py"):
            continue
        text = src_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        current_class = ""
        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue

            if not line.startswith(" ") and not line.startswith("\t"):
                current_class = ""
                cls_m = re.match(_CLASS_PATTERN, stripped)
                cls_name = re.strip_group(cls_m, 1)
                if cls_name != "":
                    current_class = cls_name
                    if cls_name not in method_returns:
                        method_returns[cls_name] = {}
                    continue

                fn_m = re.match(_DEF_PATTERN, stripped)
                fn_name = re.strip_group(fn_m, 1)
                if fn_name != "":
                    ret = _normalize_return_type(re.strip_group(fn_m, 3))
                    if ret != "":
                        fn_returns[fn_name] = ret
                continue

            if current_class == "":
                continue
            if not line.startswith("    "):
                continue
            if stripped.startswith("def "):
                method_m = re.match(_DEF_PATTERN, stripped)
                method_name = re.strip_group(method_m, 1)
                if method_name == "":
                    continue
                ret = _normalize_return_type(re.strip_group(method_m, 3))
                if ret == "":
                    continue
                method_returns[current_class][method_name] = ret

    _FUNC_RETURNS_CACHE = fn_returns
    _METHOD_RETURNS_CACHE = method_returns


def lookup_stdlib_function_return_type(function_name: str) -> str:
    _load_signature_cache()
    if _FUNC_RETURNS_CACHE is None:
        return ""
    return _FUNC_RETURNS_CACHE.get(function_name, "")


def lookup_stdlib_method_return_type(owner_type: str, method_name: str) -> str:
    _load_signature_cache()
    if _METHOD_RETURNS_CACHE is None:
        return ""
    methods = _METHOD_RETURNS_CACHE.get(owner_type, {})
    if not isinstance(methods, dict):
        return ""
    return methods.get(method_name, "")


def lookup_stdlib_method_runtime_call(owner_type: str, method_name: str) -> str:
    owner = _normalize_runtime_owner_type(owner_type)
    method = method_name.strip()
    owner_map = _OWNER_METHOD_RUNTIME_CALLS.get(owner, {})
    if not isinstance(owner_map, dict):
        return ""
    return owner_map.get(method, "")


def lookup_stdlib_function_runtime_call(function_name: str) -> str:
    fn = function_name.strip()
    if fn == "":
        return ""
    return _FUNCTION_RUNTIME_CALLS.get(fn, "")


def _normalize_runtime_owner_type(owner_type: str) -> str:
    owner = owner_type.strip()
    if owner.startswith("list["):
        owner = "list"
    elif owner.startswith("set["):
        owner = "set"
    elif owner.startswith("dict["):
        owner = "dict"
    elif owner in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
        owner = "int"
    if owner == "":
        owner = "unknown"
    return owner


def lookup_stdlib_function_runtime_binding(function_name: str) -> tuple[str, str]:
    fn = function_name.strip()
    if fn == "":
        return ("", "")
    return _FUNCTION_RUNTIME_BINDINGS.get(fn, ("", ""))


def lookup_stdlib_attribute_type(owner_type: str, attr_name: str) -> str:
    owner = owner_type.strip()
    attr = attr_name.strip()
    owner_map = _OWNER_ATTRIBUTE_TYPES.get(owner, {})
    if not isinstance(owner_map, dict):
        return ""
    return owner_map.get(attr, "")


def _resolve_imported_symbol(
    local_name: str,
    import_symbols: dict[str, dict[str, str]] | None,
) -> tuple[str, str]:
    if import_symbols is None:
        return ("", "")
    local = local_name.strip()
    if local == "":
        return ("", "")
    binding_obj = import_symbols.get(local)
    if not isinstance(binding_obj, dict):
        return ("", "")
    module = str(binding_obj.get("module", "")).strip()
    symbol = str(binding_obj.get("name", "")).strip()
    return (module, symbol)


def lookup_stdlib_imported_symbol_return_type(
    local_name: str,
    import_symbols: dict[str, dict[str, str]] | None,
) -> str:
    module, symbol = _resolve_imported_symbol(local_name, import_symbols)
    if module == "" or symbol == "":
        return ""
    return _IMPORTED_SYMBOL_RETURNS.get((module, symbol), "")


def lookup_stdlib_imported_symbol_runtime_call(
    local_name: str,
    import_symbols: dict[str, dict[str, str]] | None,
) -> str:
    module, symbol = _resolve_imported_symbol(local_name, import_symbols)
    if module == "" or symbol == "":
        return ""
    return _IMPORTED_SYMBOL_RUNTIME_CALLS.get((module, symbol), "")


def lookup_stdlib_imported_symbol_runtime_binding(
    local_name: str,
    import_symbols: dict[str, dict[str, str]] | None,
) -> tuple[str, str]:
    module, symbol = _resolve_imported_symbol(local_name, import_symbols)
    if module == "" or symbol == "":
        return ("", "")
    return _IMPORTED_SYMBOL_RUNTIME_BINDINGS.get((module, symbol), ("", ""))


def lookup_stdlib_method_runtime_binding(owner_type: str, method_name: str) -> tuple[str, str]:
    owner = _normalize_runtime_owner_type(owner_type)
    method = method_name.strip()
    owner_map = _OWNER_METHOD_RUNTIME_BINDINGS.get(owner, {})
    if not isinstance(owner_map, dict):
        return ("", "")
    return owner_map.get(method, ("", ""))


def lookup_noncpp_imported_symbol_runtime_call(
    local_name: str,
    import_symbols: dict[str, dict[str, str]] | None,
) -> str:
    module, symbol = _resolve_imported_symbol(local_name, import_symbols)
    if module == "" or symbol == "":
        return ""
    return _NONCPP_IMPORTED_SYMBOL_RUNTIME_CALLS.get((module, symbol), "")


def lookup_noncpp_module_attr_runtime_call(module_name: str, attr_name: str) -> str:
    module = module_name.strip()
    attr = attr_name.strip()
    if module == "" or attr == "":
        return ""
    return _NONCPP_MODULE_ATTR_RUNTIME_CALLS.get((module, attr), "")


def list_noncpp_assertion_runtime_calls() -> list[str]:
    out: set[str] = set()
    for runtime_call in _NONCPP_IMPORTED_SYMBOL_RUNTIME_CALLS.values():
        call = runtime_call.strip()
        if call.startswith("py_assert_"):
            out.add(call)
    return sorted(out)


def is_stdlib_path_type(type_name: str) -> bool:
    return type_name.strip() == "Path"


__all__ = [
    "is_stdlib_path_type",
    "list_noncpp_assertion_runtime_calls",
    "lookup_stdlib_attribute_type",
    "lookup_stdlib_function_return_type",
    "lookup_stdlib_function_runtime_call",
    "lookup_stdlib_function_runtime_binding",
    "lookup_stdlib_imported_symbol_return_type",
    "lookup_stdlib_imported_symbol_runtime_call",
    "lookup_stdlib_imported_symbol_runtime_binding",
    "lookup_noncpp_imported_symbol_runtime_call",
    "lookup_noncpp_module_attr_runtime_call",
    "lookup_stdlib_method_runtime_binding",
    "lookup_stdlib_method_runtime_call",
    "lookup_stdlib_method_return_type",
]

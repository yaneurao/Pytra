"""TypeScript type mapping from EAST3 resolved types.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations


# EAST3 resolved_type → TypeScript type
_TYPE_MAP: dict[str, str] = {
    "int": "number",
    "byte": "number",
    "int8": "number",
    "int16": "number",
    "int32": "number",
    "int64": "number",
    "uint8": "number",
    "uint16": "number",
    "uint32": "number",
    "uint64": "number",
    "float": "number",
    "float32": "number",
    "float64": "number",
    "bool": "boolean",
    "str": "string",
    "None": "void",
    "none": "void",
    "bytes": "number[]",
    "bytearray": "number[]",
    "list": "any[]",
    "dict": "Map<any, any>",
    "set": "Set<any>",
    "tuple": "any[]",
    "object": "any",
    "Obj": "any",
    "Any": "any",
    "JsonVal": "any",
    "Node": "Map<string, any>",
    "Callable": "(...args: any[]) => any",
    "callable": "(...args: any[]) => any",
    "Exception": "Error",
    "BaseException": "Error",
    "RuntimeError": "Error",
    "ValueError": "Error",
    "TypeError": "Error",
    "IndexError": "Error",
    "KeyError": "Error",
    "Path": "PyPath",
}

_TS_KEYWORDS: set[str] = {
    "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "enum", "export", "extends",
    "false", "finally", "for", "function", "if", "import", "in",
    "instanceof", "new", "null", "return", "super", "switch", "this",
    "throw", "true", "try", "typeof", "var", "void", "while", "with",
    "implements", "interface", "let", "package", "private", "protected",
    "public", "static", "yield", "abstract", "any", "as", "async",
    "await", "boolean", "constructor", "declare", "from", "get", "is",
    "keyof", "module", "namespace", "never", "number", "object", "of",
    "override", "readonly", "require", "set", "string", "symbol", "type",
    "undefined", "unique", "unknown",
}

TS_BUILTIN_RUNTIME_SYMBOLS: tuple[str, ...] = (
    "PY_TYPE_NONE", "PY_TYPE_BOOL", "PY_TYPE_NUMBER", "PY_TYPE_STRING",
    "PY_TYPE_ARRAY", "PY_TYPE_MAP", "PY_TYPE_SET", "PY_TYPE_OBJECT",
    "PYTRA_TRUTHY", "PYTRA_TRY_LEN", "PYTRA_STR",
    "pyRegisterType", "pyRegisterClassType", "pyIsSubtype", "pyIsInstance",
    "pyTypeId", "pyTruthy", "pyTryLen", "pyStr", "pyToString",
    "pyPrint", "pyLen", "pyBool", "pyRange", "pyFloorDiv", "pyMod",
    "pyIn", "pySlice", "pyOrd", "pyChr", "pyBytearray", "pyBytes",
    "pyStrJoin", "pyStrStrip", "pyStrLstrip", "pyStrRstrip",
    "pyStrStartswith", "pyStrEndswith", "pyStrReplace",
    "pyStrFind", "pyStrRfind", "pyStrSplit",
    "pyStrUpper", "pyStrLower", "pyStrCount", "pyStrIndex",
    "pyStrIsdigit", "pyStrIsalpha", "pyStrIsalnum", "pyStrIsspace",
    "pyEnumerate", "pyReversed", "pySorted",
    "pyAssertStdout", "pyAssertTrue", "pyAssertEq", "pyAssertAll",
    "pyFloatStr", "pyFmt",
    "pysum", "pyzip", "type_",
    "pyfabs", "pytan", "pylog", "pyexp", "pylog10", "pylog2",
    "pysqrt", "pysin", "pycos", "pyceil", "pyfloor", "pypow",
    "pyround", "pytrunc", "pyatan2", "pyasin", "pyacos", "pyatan",
    "pyhypot", "py_math_pi", "py_math_e", "py_math_inf", "py_math_nan",
    "pyisfinite", "pyisinf", "pyisnan",
    "dumps", "loads",
    "pydumps", "pyloads", "pyloads_arr", "pyloads_obj",
    "JsonValue", "JsonArr", "JsonObj",
    "Path", "PyPath", "py_math_tau",
    "pyjoin", "pysplitext", "pybasename", "pydirname", "pyexists", "pyisfile", "pyisdir",
    "pymakedirs",
    "ArgumentParser",
    "pywrite_rgb_png",
    "pyopen", "PyFile",
    "perf_counter",
    "sys", "pyset_argv", "pyset_path",
    "sub", "match", "search", "findall", "split",
    "pyglob",
    "pyupdate", "pypop", "pysetdefault", "pyextend", "pysort", "pyreverse", "pyclear",
    "pydel",
    "pyinsert", "pybool", "pyrepr",
    "pyTuple", "pyTupleToString",
    "dict", "list", "set_", "field", "___",
    "__file__",
    "bool", "str", "int", "float",
)

TS_BUILTIN_EXCEPTION_NAMES: frozenset[str] = frozenset((
    "Exception", "BaseException", "RuntimeError", "ValueError",
    "TypeError", "IndexError", "KeyError", "StopIteration",
    "AttributeError", "NameError", "NotImplementedError",
    "OverflowError", "ZeroDivisionError", "AssertionError",
    "OSError", "IOError", "FileNotFoundError", "PermissionError",
))

TS_BUILTIN_EXCEPTION_MAP: dict[str, str] = {
    "Exception": "Error",
    "BaseException": "Error",
    "RuntimeError": "Error",
    "ValueError": "Error",
    "TypeError": "TypeError",
    "KeyError": "Error",
    "IndexError": "RangeError",
    "AttributeError": "Error",
    "NotImplementedError": "Error",
    "StopIteration": "Error",
    "OverflowError": "RangeError",
    "ZeroDivisionError": "Error",
    "OSError": "Error",
    "IOError": "Error",
    "NameError": "Error",
    "ImportError": "Error",
    "AssertionError": "Error",
    "SystemExit": "Error",
    "RecursionError": "RangeError",
    "FileNotFoundError": "Error",
    "PermissionError": "Error",
    "UnicodeDecodeError": "Error",
    "UnicodeEncodeError": "Error",
}


def _safe_ts_ident(name: str) -> str:
    """Make a string safe as a TypeScript identifier."""
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        return "_unnamed"
    if out[0].isdigit():
        out = "_" + out
    if out in _TS_KEYWORDS:
        out = out + "_"
    return out


def _split_generic_args(s: str) -> list[str]:
    """Split comma-separated generic type args respecting angle brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "<" or ch == "[":
            depth += 1
            current.append(ch)
        elif ch == ">" or ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _parse_callable_signature(resolved_type: str) -> tuple[list[str], str]:
    """Parse a callable[...] or Callable[...] resolved type into (params, return_type)."""
    if not (
        (resolved_type.startswith("callable[") or resolved_type.startswith("Callable["))
        and resolved_type.endswith("]")
    ):
        return ([], "unknown")
    prefix_len = len("Callable[") if resolved_type.startswith("Callable[") else len("callable[")
    inner = resolved_type[prefix_len:-1].strip()
    if inner == "":
        return ([], "unknown")
    if inner.startswith("["):
        depth = 0
        close_idx = -1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
            i += 1
        if close_idx >= 0 and close_idx + 1 < len(inner) and inner[close_idx + 1] == ",":
            params_text = inner[1:close_idx].strip()
            ret_text = inner[close_idx + 2:].strip()
            params: list[str] = []
            if params_text != "":
                params = _split_generic_args(params_text)
            return (params, ret_text if ret_text != "" else "unknown")
    arrow_idx = inner.find("->")
    if arrow_idx >= 0:
        params_text2 = inner[:arrow_idx].strip()
        ret_text2 = inner[arrow_idx + 2:].strip()
        params2: list[str] = []
        if params_text2 != "":
            for part in params_text2.split(","):
                item = part.strip()
                if item != "":
                    params2.append(item)
        return (params2, ret_text2 if ret_text2 != "" else "unknown")
    return ([], inner)


def _needs_array_group(type_expr: str) -> bool:
    return ("|" in type_expr) or ("=>" in type_expr) or ("&" in type_expr)


def _needs_union_group(type_expr: str) -> bool:
    return "=>" in type_expr


def ts_array_type(elem_type: str) -> str:
    elem = elem_type.strip()
    if _needs_array_group(elem):
        return "(" + elem + ")[]"
    return elem + "[]"


def ts_type(resolved_type: str, *, for_return: bool = False) -> str:
    """Convert an EAST3 resolved_type to a TypeScript type string.

    Args:
        resolved_type: EAST3 resolved type string.
        for_return: If True, map None → void instead of null.
    """
    if resolved_type == "" or resolved_type == "unknown":
        return "any"

    # Callable types
    if (resolved_type.startswith("callable[") or resolved_type.startswith("Callable[")) and resolved_type.endswith("]"):
        params, ret = _parse_callable_signature(resolved_type)
        param_parts: list[str] = []
        for idx, param in enumerate(params):
            param_parts.append("arg" + str(idx) + ": " + ts_type(param))
        ret_ts = ts_type(ret, for_return=True)
        return "(" + ", ".join(param_parts) + ") => " + ret_ts

    # multi_return → tuple
    if resolved_type.startswith("multi_return[") and resolved_type.endswith("]"):
        inner = resolved_type[len("multi_return["):-1]
        parts = _split_generic_args(inner)
        return "[" + ", ".join(ts_type(p) for p in parts) + "]"

    # Direct mapping
    if resolved_type in _TYPE_MAP:
        mapped = _TYPE_MAP[resolved_type]
        if resolved_type == "None" and not for_return:
            return "null"
        return mapped

    # list[T] → T[]
    if resolved_type.startswith("list[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        return ts_array_type(ts_type(inner))

    # dict[K, V] → Map<K, V>
    if resolved_type.startswith("dict[") and resolved_type.endswith("]"):
        inner = resolved_type[5:-1]
        parts = _split_generic_args(inner)
        if len(parts) == 2:
            return "Map<" + ts_type(parts[0]) + ", " + ts_type(parts[1]) + ">"
        return "Map<any, any>"

    # set[T] → Set<T>
    if resolved_type.startswith("set[") and resolved_type.endswith("]"):
        inner = resolved_type[4:-1]
        return "Set<" + ts_type(inner) + ">"

    # tuple[A, B, ...] → [A, B, ...]
    if resolved_type.startswith("tuple[") and resolved_type.endswith("]"):
        inner = resolved_type[6:-1]
        parts = _split_generic_args(inner)
        return "[" + ", ".join(ts_type(p) for p in parts) + "]"

    # Optional: T | None → T | null
    if resolved_type.endswith(" | None") or resolved_type.endswith("|None"):
        inner = resolved_type[:-7] if resolved_type.endswith(" | None") else resolved_type[:-5]
        inner_ts = ts_type(inner)
        if _needs_union_group(inner_ts):
            inner_ts = "(" + inner_ts + ")"
        return inner_ts + " | null"

    # Union type (A | B, A|B) → A | B
    if "|" in resolved_type:
        parts = [part.strip() for part in resolved_type.split("|") if part.strip() != ""]
        if len(parts) > 1:
            rendered_parts: list[str] = []
            for part in parts:
                rendered = ts_type(part)
                if _needs_union_group(rendered):
                    rendered = "(" + rendered + ")"
                rendered_parts.append(rendered)
            return " | ".join(rendered_parts)

    # User class → ClassName
    return _safe_ts_ident(resolved_type)


def ts_zero_value(resolved_type: str) -> str:
    """Return a TypeScript zero/default value for a type."""
    tt = ts_type(resolved_type)
    if tt == "number":
        return "0"
    if tt == "boolean":
        return "false"
    if tt == "string":
        return '""'
    if tt == "void":
        return ""
    return "null"

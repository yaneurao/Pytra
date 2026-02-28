"""Read stdlib signatures from `pytra/std` as compiler source-of-truth."""

from __future__ import annotations

from pytra.std import re
from pytra.std.pathlib import Path


_DEF_PATTERN = r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*(?:->\s*(.+)\s*)?:\s*$"
_CLASS_PATTERN = r"^class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([A-Za-z_][A-Za-z0-9_]*)\))?\s*:\s*$"

_FUNC_RETURNS_CACHE: dict[str, str] | None = None
_METHOD_RETURNS_CACHE: dict[str, dict[str, str]] | None = None


def _std_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "std"


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
    primitive = {
        "int": "int64",
        "float": "float64",
        "bool": "bool",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
        "None": "None",
        "Any": "Any",
        "object": "object",
        "Path": "Path",
    }
    if t in primitive:
        return primitive[t]
    if t.startswith("list[") and t.endswith("]"):
        inner = _normalize_return_type(t[5:-1])
        if inner == "":
            inner = "unknown"
        return f"list[{inner}]"
    if t.startswith("set[") and t.endswith("]"):
        inner = _normalize_return_type(t[4:-1])
        if inner == "":
            inner = "unknown"
        return f"set[{inner}]"
    if t.startswith("dict[") and t.endswith("]"):
        inner_parts = _split_top_level(t[5:-1], ",")
        if len(inner_parts) == 2:
            key_t = _normalize_return_type(inner_parts[0])
            val_t = _normalize_return_type(inner_parts[1])
            if key_t == "":
                key_t = "unknown"
            if val_t == "":
                val_t = "unknown"
            return f"dict[{key_t},{val_t}]"
    if t.startswith("tuple[") and t.endswith("]"):
        tuple_parts = _split_top_level(t[6:-1], ",")
        normalized: list[str] = []
        for p in tuple_parts:
            n = _normalize_return_type(p)
            normalized.append(n if n != "" else "unknown")
        if len(normalized) > 0:
            return "tuple[" + ",".join(normalized) + "]"
    union_parts = _split_top_level(t, "|")
    if len(union_parts) > 1:
        normalized_union: list[str] = []
        for p in union_parts:
            n = _normalize_return_type(p)
            normalized_union.append(n if n != "" else "unknown")
        return "|".join(normalized_union)
    return t


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


__all__ = [
    "lookup_stdlib_function_return_type",
    "lookup_stdlib_method_return_type",
]

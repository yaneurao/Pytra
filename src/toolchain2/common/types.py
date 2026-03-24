"""Type name normalization and classification (selfhost-safe).

§5.1: Any/object 禁止 — JsonVal のみ使用。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


def normalize_type_name(value: JsonVal) -> str:
    """Normalize a type name string, returning 'unknown' for missing/empty."""
    if isinstance(value, str):
        t = value.strip()
        if t != "":
            return t
    return "unknown"


def is_any_like_type(value: JsonVal) -> bool:
    """Check if a type name is polymorphic/unknown (Any, object, etc.)."""
    t = normalize_type_name(value)
    if t == "Any" or t == "any" or t == "object" or t == "unknown" or t == "":
        return True
    if "|" in t:
        parts = t.split("|")
        for p in parts:
            ps = p.strip()
            if ps == "Any" or ps == "any" or ps == "object":
                return True
    return False


def split_generic_types(text: str) -> list[str]:
    """Split comma-separated generic type parameters respecting nesting.

    Handles both [] and <> as nesting delimiters.
    Example: "int64, dict[str, int64]" → ["int64", "dict[str, int64]"]
    """
    out: list[str] = []
    part = ""
    depth = 0
    for ch in text:
        if ch == "<" or ch == "[":
            depth += 1
            part += ch
            continue
        if ch == ">" or ch == "]":
            if depth > 0:
                depth -= 1
            part += ch
            continue
        if ch == "," and depth == 0:
            out.append(part.strip())
            part = ""
            continue
        part += ch
    last = part.strip()
    if last != "":
        out.append(last)
    return out

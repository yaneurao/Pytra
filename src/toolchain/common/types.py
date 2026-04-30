"""Type name normalization and classification (selfhost-safe).

§5.1: Any/object 禁止 — JsonVal のみ使用。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


_KNOWN_TYPE_ALIASES: dict[str, str] = {
    "Node": "dict[str,JsonVal]",
}

_KNOWN_UNION_ALIASES: dict[str, str] = {
    "JsonVal": "None | bool | int64 | float64 | str | list[JsonVal] | dict[str,JsonVal]",
}


def _common_normalize_type_name(value: JsonVal) -> str:
    if value is None:
        return "unknown"
    t = str(value).strip()
    if t != "":
        return t
    return "unknown"


def is_any_like_type(value: JsonVal) -> bool:
    t = _common_normalize_type_name(value)
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


def normalize_known_type_alias(type_name: JsonVal) -> str:
    normalized = _common_normalize_type_name(type_name)
    return _KNOWN_TYPE_ALIASES.get(normalized, normalized)


def split_top_level_union_types(text: str) -> list[str]:
    normalized = _common_normalize_type_name(text)
    if normalized == "unknown":
        return []
    out: list[str] = []
    part = ""
    depth = 0
    for ch in normalized:
        if ch in "[<(":
            depth += 1
            part += ch
            continue
        if ch in "]>)":
            if depth > 0:
                depth -= 1
            part += ch
            continue
        if ch == "|" and depth == 0:
            item = part.strip()
            if item != "":
                out.append(item)
            part = ""
            continue
        part += ch
    tail = part.strip()
    if tail != "":
        out.append(tail)
    return out


def expand_known_union_alias(type_name: JsonVal) -> str:
    normalized = normalize_known_type_alias(type_name)
    return _KNOWN_UNION_ALIASES.get(normalized, normalized)


def select_union_member_type(union_type: str, member_type: str) -> str:
    normalized_member = normalize_known_type_alias(member_type)
    if normalized_member in ("", "unknown"):
        return ""
    expanded_union = expand_known_union_alias(union_type)
    lanes = split_top_level_union_types(expanded_union)
    if len(lanes) == 0:
        return normalized_member if normalize_known_type_alias(expanded_union) == normalized_member else ""
    for lane in lanes:
        if normalize_known_type_alias(lane) == normalized_member:
            return normalized_member
    return ""

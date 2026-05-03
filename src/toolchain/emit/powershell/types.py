"""PowerShell type mapping utilities for EAST3 resolved types.

PowerShell is dynamically typed — all type annotations are comments only.
This module provides identifier safety and type-hint utilities.
"""

from __future__ import annotations


_PS_KEYWORDS: set[str] = {
    "begin", "break", "catch", "class", "continue", "data", "do", "dynamicparam",
    "else", "elseif", "end", "enum", "exit", "filter", "finally", "for",
    "foreach", "from", "function", "if", "in", "param", "process", "return",
    "switch", "throw", "trap", "try", "until", "using", "while",
}

_PS_AUTOMATIC_VARS: set[str] = {
    "true", "false", "null", "args", "input", "PSScriptRoot", "PSCommandPath",
    "Error", "Host", "HOME", "PID", "PROFILE",
}


def _contains_automatic_var(name: str) -> bool:
    name_lower = name.lower()
    for var_name in _PS_AUTOMATIC_VARS:
        if name_lower == var_name.lower():
            return True
    return False


def safe_ps1_ident(name: str, fallback: str) -> str:
    """Make a string safe as a PowerShell identifier (without $ sigil)."""
    if name == "":
        return fallback
    chars: list[str] = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars)
    if out == "":
        return fallback
    if out[0].isdigit():
        out = "_" + out
    out_lower = out.lower()
    if out_lower in _PS_KEYWORDS or _contains_automatic_var(out_lower):
        out = out + "_"
    return out


def ps1_string_literal(text: str) -> str:
    """Escape a string value for use in a PowerShell double-quoted string."""
    out = text.replace("`", "``")
    out = out.replace('"', '`"')
    out = out.replace("$", "`$")
    out = out.replace("\n", "`n")
    out = out.replace("\r", "`r")
    out = out.replace("\t", "`t")
    out = out.replace("\0", "`0")
    return '"' + out + '"'

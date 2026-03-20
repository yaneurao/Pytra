#!/usr/bin/env python3
"""Self-hosted EAST decorator semantics helpers."""

from __future__ import annotations


def _sh_parse_decorator_head_and_args(text: str) -> tuple[str, str]:
    """`decorator` / `decorator(...)` を (head, args_txt_or_empty) に分解する。"""
    raw = text.strip()
    if raw == "":
        return "", ""
    depth = 0
    in_str: str | None = None
    esc = False
    lp = -1
    for i, ch in enumerate(raw):
        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue
        if ch in {"'", '"'}:
            in_str = ch
            continue
        if ch in {"(", "[", "{"}:
            if ch == "(" and depth == 0:
                lp = i
                break
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
    if lp < 0:
        return raw, ""
    if not raw.endswith(")"):
        return raw, ""
    depth = 0
    in_str = None
    esc = False
    rp = -1
    i = lp
    while i < len(raw):
        ch = raw[i]
        if in_str is not None:
            if esc:
                esc = False
                i += 1
                continue
            if ch == "\\":
                esc = True
                i += 1
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {"'", '"'}:
            in_str = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth -= 1
            if depth == 0:
                rp = i
                break
            i += 1
            continue
        i += 1
    if rp < 0 or rp != len(raw) - 1:
        return raw, ""
    head = raw[:lp].strip()
    if head == "":
        return raw, ""
    return head, raw[lp + 1 : rp].strip()


def _sh_is_dataclass_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が dataclass 系（標準 dataclasses 由来）か判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "dataclass":
        return True
    if head.endswith(".dataclass"):
        owner = head[:-len(".dataclass")]
        if owner == "dataclasses":
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name == "dataclasses"
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name == "dataclasses" and sym_name == "dataclass"


def _sh_is_sealed_decorator(
    decorator_text: str,
) -> bool:
    """decorator 文字列が Stage A nominal ADT の `@sealed` か判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    return head == "sealed"


def _sh_is_abi_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が `pytra.std.abi` を指すか判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "abi":
        return True
    if head.endswith(".abi"):
        owner = head[:-len(".abi")]
        if owner == "pytra.std":
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name == "pytra.std"
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name == "pytra.std" and sym_name == "abi"


def _sh_is_template_decorator(
    decorator_text: str,
    *,
    import_module_bindings: dict[str, str],
    import_symbol_bindings: dict[str, dict[str, str]],
) -> bool:
    """decorator 文字列が `pytra.std.template.template` 系を指すか判定する。"""
    head, _args_txt = _sh_parse_decorator_head_and_args(decorator_text)
    if head == "":
        return False
    if head == "template":
        return True
    if head.endswith(".template"):
        owner = head[:-len(".template")]
        if owner in {"pytra.std", "pytra.std.template"}:
            return True
        mod_name = import_module_bindings.get(owner, "")
        return mod_name in {"pytra.std", "pytra.std.template"}
    ent = import_symbol_bindings.get(head)
    if not isinstance(ent, dict):
        return False
    mod_name = str(ent.get("module", ""))
    sym_name = str(ent.get("name", ""))
    return mod_name in {"pytra.std", "pytra.std.template"} and sym_name == "template"

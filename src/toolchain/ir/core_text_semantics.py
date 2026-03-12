#!/usr/bin/env python3
"""Self-hosted EAST text/import helper semantics."""

from __future__ import annotations

from typing import Any


def _sh_is_identifier(text: str) -> bool:
    """ASCII 識別子（先頭英字/`_`）かを返す。"""
    if text == "":
        return False
    c0 = text[0:1]
    is_head = ("A" <= c0 <= "Z") or ("a" <= c0 <= "z") or c0 == "_"
    if not is_head:
        return False
    for ch in text[1:]:
        is_body = ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "_"
        if not is_body:
            return False
    return True


def _sh_strip_utf8_bom(source: str) -> str:
    """UTF-8 BOM を先頭から除去する。"""
    if source.startswith("\ufeff"):
        return source[1:]
    return source


def _sh_is_dotted_identifier(text: str) -> bool:
    """`a.b.c` 形式の識別子列かを返す。"""
    if text.strip() == "":
        return False
    parts = text.split(".")
    if len(parts) == 0:
        return False
    for seg in parts:
        if not _sh_is_identifier(seg):
            return False
    return True


def _sh_split_top_keyword(text: str, kw: str) -> int:
    """トップレベルでキーワード出現位置を探す（未検出なら -1）。"""
    depth = 0
    in_str: str | None = None
    esc = False
    for i, ch in enumerate(text):
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
            depth += 1
            continue
        if ch in {")", "]", "}"}:
            depth -= 1
            continue
        if depth == 0 and text[i:].startswith(kw):
            prev_ok = i == 0 or text[i - 1].isspace()
            next_ok = (i + len(kw) >= len(text)) or text[i + len(kw)].isspace()
            if prev_ok and next_ok:
                return i
    return -1


def _sh_split_top_level_as(text: str) -> tuple[str, str] | None:
    """トップレベルの `lhs as rhs` を分割する。"""
    pos = _sh_split_top_keyword(text, "as")
    if pos < 0:
        return None
    lhs = text[:pos].strip()
    rhs = text[pos + 2 :].strip()
    if lhs == "" or rhs == "":
        return None
    return lhs, rhs


def _sh_parse_import_alias(text: str, *, allow_dotted_name: bool) -> tuple[str, str] | None:
    """`name` / `name as alias` を手書きパースして (name, alias_or_empty) を返す。"""
    raw = text.strip()
    if raw == "":
        return None
    name_txt = raw
    alias_txt = ""
    as_split = _sh_split_top_level_as(raw)
    if as_split is not None:
        name_txt, alias_txt = as_split
        name_txt = name_txt.strip()
        alias_txt = alias_txt.strip()
    if name_txt == "":
        return None
    if allow_dotted_name:
        if not _sh_is_dotted_identifier(name_txt):
            return None
    else:
        if not _sh_is_identifier(name_txt):
            return None
    if alias_txt != "" and not _sh_is_identifier(alias_txt):
        return None
    return name_txt, alias_txt


def _sh_normalize_import_from_names_text(text: str) -> str:
    """`from module import (...)` の optional paren wrapper を剥がす。"""
    raw = text.strip()
    if len(raw) < 2 or raw[0] != "(" or raw[-1] != ")":
        return raw
    depth = 0
    in_str: str | None = None
    esc = False
    close_idx = -1
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
        if ch == "(":
            depth += 1
            continue
        if ch == ")":
            depth -= 1
            if depth < 0:
                return raw
            if depth == 0:
                close_idx = i
                break
    if depth != 0 or close_idx != len(raw) - 1:
        return raw
    return raw[1:-1].strip()


def _sh_parse_import_from_clause(text: str) -> tuple[str, str, int] | None:
    """`from module import names` を手書きパースして raw module text と level を返す。"""
    raw = text.strip()
    if not raw.startswith("from "):
        return None
    marker = " import "
    pos = raw.find(marker)
    if pos < 0:
        return None
    module_txt = raw[len("from ") : pos].strip()
    names_txt = _sh_normalize_import_from_names_text(raw[pos + len(marker) :])
    if module_txt == "" or names_txt == "":
        return None
    level = 0
    while level < len(module_txt) and module_txt[level] == ".":
        level += 1
    if level == 0:
        if not _sh_is_dotted_identifier(module_txt):
            return None
    else:
        base_txt = module_txt[level:]
        if base_txt != "" and not _sh_is_dotted_identifier(base_txt):
            return None
    return module_txt, names_txt, level


def _sh_parse_dataclass_decorator_options(
    args_txt: str,
    *,
    line_no: int,
    line_text: str,
    split_top_commas: Any,
    split_top_level_assign: Any,
    is_identifier: Any,
    make_east_build_error: Any,
    make_span: Any,
) -> dict[str, bool]:
    """`@dataclass(...)` の keyword bool オプションを抽出する。"""
    out: dict[str, bool] = {}
    if args_txt.strip() == "":
        return out
    parts = split_top_commas(args_txt)
    for part_raw in parts:
        part = part_raw.strip()
        if part == "":
            continue
        kv = split_top_level_assign(part)
        if kv is None:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"unsupported dataclass decorator argument: {part}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use keyword bool args only: dataclass(init=..., repr=..., eq=...).",
            )
        key, val = kv
        k = key.strip()
        v = val.strip()
        if not is_identifier(k):
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"invalid dataclass option name: {k}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use ASCII identifier option names such as init or repr.",
            )
        if v == "True":
            out[k] = True
        elif v == "False":
            out[k] = False
        else:
            raise make_east_build_error(
                kind="unsupported_syntax",
                message=f"dataclass option {k} must be True/False: {v}",
                source_span=make_span(line_no, 0, len(line_text)),
                hint="Use explicit bool literals only.",
            )
    return out

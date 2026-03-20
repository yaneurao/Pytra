#!/usr/bin/env python3
"""Shared EAST core helpers for type annotation text and alias normalization."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.type_expr import parse_type_expr_text
from toolchain.frontends.type_expr import type_expr_to_string
from toolchain.compile.core_text_semantics import _sh_is_identifier


def _sh_default_type_aliases() -> dict[str, str]:
    """型解決用の初期別名テーブルを作成する。"""
    return {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Optional": "Optional",
        "Any": "Any",
        "None": "None",
        "str": "str",
        "int": "int64",
        "float": "float64",
        "bool": "bool",
    }


def _sh_is_type_expr_text(txt: str) -> bool:
    """型注釈として妥当そうな文字列かを軽量判定する。"""
    raw: str = txt.strip()
    if raw == "":
        return False
    for ch in raw:
        if ch.isspace():
            continue
        if ch.isalnum() or ch in {"[", "]", ",", "|", ":", ".", "_"}:
            continue
        return False
    return True


def _sh_typing_alias_to_type_name(sym: str) -> str:
    """`from typing` で import される代表的シンボルを EAST 型名へ正規化する。"""
    key = sym.strip()
    if key.startswith("typing."):
        key = key[len("typing.") :].strip()
    mapping = {
        "List": "list",
        "Dict": "dict",
        "Tuple": "tuple",
        "Set": "set",
        "Optional": "Optional",
        "Any": "Any",
        "None": "None",
        "bool": "bool",
        "float": "float64",
        "int": "int64",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
    }
    return mapping.get(key, "")


def _sh_ann_to_type(ann: str, *, type_aliases: dict[str, str]) -> str:
    """型注釈文字列を EAST 正規型へ変換する。"""
    return type_expr_to_string(parse_type_expr_text(ann, type_aliases=type_aliases))


def _sh_ann_to_type_expr(
    ann: str,
    *,
    type_aliases: dict[str, str],
) -> dict[str, Any]:
    return parse_type_expr_text(ann, type_aliases=type_aliases)


def _sh_type_expr_to_type_name(expr: dict[str, Any]) -> str:
    return type_expr_to_string(expr)


def _sh_register_type_alias(type_aliases: dict[str, str], alias_name: str, rhs_txt: str) -> None:
    """型っぽい代入式からトップレベルの型エイリアス定義を登録する。"""
    name = alias_name.strip()
    rhs = rhs_txt.strip()
    if not _sh_is_identifier(name):
        return
    if rhs == "":
        return
    if not _sh_is_type_expr_text(rhs):
        return
    normalized = _sh_typing_alias_to_type_name(rhs)
    ann_type = _sh_ann_to_type(rhs, type_aliases=type_aliases)
    if normalized != "":
        type_aliases[name] = normalized
    elif ann_type == "Any":
        type_aliases[name] = ann_type
    elif ann_type != "unknown" and ann_type != rhs:
        type_aliases[name] = ann_type


def _sh_split_args_with_offsets(arg_text: str) -> list[tuple[str, int]]:
    """引数文字列をトップレベルのカンマで分割し、相対オフセットも返す。"""
    out: list[tuple[str, int]] = []
    depth = 0
    in_str: str | None = None
    esc = False
    start = 0
    for i, ch in enumerate(arg_text):
        if in_str is not None:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
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
        if ch == "," and depth == 0:
            part = arg_text[start:i]
            out.append((part.strip(), start + (len(part) - len(part.lstrip()))))
            start = i + 1
    tail = arg_text[start:]
    if tail.strip() != "":
        out.append((tail.strip(), start + (len(tail) - len(tail.lstrip()))))
    return out

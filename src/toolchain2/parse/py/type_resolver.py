"""型注釈の正規化: Python 型名 → EAST 内部型名。

例: int → int64, float → float64, List[int] → list[int64]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from toolchain2.parse.py.nodes import NamedType, GenericType, TypeExpr


# デフォルト型エイリアス
_DEFAULT_TYPE_ALIASES: dict[str, str] = {
    "int": "int64",
    "float": "float64",
    "bool": "bool",
    "str": "str",
    "bytes": "bytes",
    "None": "None",
    "NoneType": "None",
    "object": "object",
}


def default_type_aliases() -> dict[str, str]:
    return dict(_DEFAULT_TYPE_ALIASES)


def resolve_type_annotation(
    ann: str,
    type_aliases: dict[str, str],
) -> str:
    """型注釈文字列を EAST 内部型名に正規化する。"""
    ann = ann.strip()
    if ann == "":
        return ""

    # Generic 型: list[T], dict[K,V], tuple[T,...], set[T], Optional[T]
    bracket_pos = ann.find("[")
    if bracket_pos > 0 and ann.endswith("]"):
        base = ann[:bracket_pos].strip()
        inner = ann[bracket_pos + 1 : -1].strip()

        # base の正規化
        base_resolved = _resolve_base_type(base, type_aliases)

        # inner の分割と再帰解決
        args = _split_type_args(inner)
        resolved_args = [resolve_type_annotation(a, type_aliases) for a in args]

        return base_resolved + "[" + ", ".join(resolved_args) + "]"

    # 単純型
    return _resolve_simple_type(ann, type_aliases)


def _resolve_simple_type(name: str, type_aliases: dict[str, str]) -> str:
    """単純型名を解決する。"""
    name = name.strip()
    if name in type_aliases:
        return type_aliases[name]
    # typing モジュールの型
    if name == "List":
        return "list"
    if name == "Dict":
        return "dict"
    if name == "Tuple":
        return "tuple"
    if name == "Set":
        return "set"
    if name == "Optional":
        return "Optional"
    return name


def _resolve_base_type(base: str, type_aliases: dict[str, str]) -> str:
    """Generic 型のベース部分を正規化する。"""
    base = base.strip()
    if base == "List":
        return "list"
    if base == "Dict":
        return "dict"
    if base == "Tuple":
        return "tuple"
    if base == "Set":
        return "set"
    if base == "Optional":
        return "Optional"
    if base in type_aliases:
        return type_aliases[base]
    return base


def _split_type_args(inner: str) -> list[str]:
    """型引数をカンマで分割する（ネストしたブラケットを考慮）。"""
    args: list[str] = []
    depth = 0
    current = ""
    for ch in inner:
        if ch == "[":
            depth += 1
            current += ch
        elif ch == "]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip() != "":
        args.append(current.strip())
    return args


def annotation_to_type_expr(
    ann: str,
    type_aliases: dict[str, str],
) -> TypeExpr:
    """型注釈文字列を TypeExpr ノードに変換する。"""
    resolved = resolve_type_annotation(ann, type_aliases)
    return _parse_type_expr(resolved)


def _parse_type_expr(text: str) -> TypeExpr:
    """正規化済み型文字列を TypeExpr に変換する。"""
    text = text.strip()
    bracket_pos = text.find("[")
    if bracket_pos > 0 and text.endswith("]"):
        base = text[:bracket_pos].strip()
        inner = text[bracket_pos + 1 : -1].strip()
        args = _split_type_args(inner)
        return GenericType(
            base=base,
            args=[_parse_type_expr(a) for a in args],
        )
    return NamedType(name=text)

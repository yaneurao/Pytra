"""EAST -> Go transpiler.

暫定的には C# エミッタ出力を受け継いで「シグネチャ要約コメント」状態を
解除し、AST 本文出力として扱える形に寄せている。
"""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_go_profile() -> dict[str, Any]:
    """Go backend 用 profile を返す。"""
    return load_cs_profile()


def transpile_to_go(east_doc: dict[str, Any]) -> str:
    """EAST を Go ソースへ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    return lowered

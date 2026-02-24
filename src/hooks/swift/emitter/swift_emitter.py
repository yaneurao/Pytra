"""EAST -> Swift transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_swift_profile() -> dict[str, Any]:
    """Swift backend で利用する profile を返す。"""
    return load_cs_profile()


def transpile_to_swift(east_doc: dict[str, Any]) -> str:
    """EAST を Swift ソースへ変換する."""
    # NOTE: 真の Swift emitter 実装へ移行するまで C# 本文を暫定利用。
    return transpile_to_csharp(east_doc)

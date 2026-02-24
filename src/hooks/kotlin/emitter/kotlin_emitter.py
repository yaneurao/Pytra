"""EAST -> Kotlin transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_kotlin_profile() -> dict[str, Any]:
    """Kotlin backend で利用する profile を返す。"""
    return load_cs_profile()


def transpile_to_kotlin(east_doc: dict[str, Any]) -> str:
    """EAST を Kotlin ソースへ変換する."""
    # NOTE: 真の Kotlin emitter 実装までは暫定的に C# 本文を流用する。
    return transpile_to_csharp(east_doc)

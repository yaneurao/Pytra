"""EAST -> Kotlin transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_kotlin_profile() -> dict[str, Any]:
    """Kotlin backend で利用する profile を返す。"""
    return load_cs_profile()


def transpile_to_kotlin(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Kotlin ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    out = "// このファイルは EAST ベース Kotlin プレビュー出力です。\n"
    out += "// TODO: 専用 KotlinEmitter 実装へ段階移行する。\n"
    out += "fun main() {\n"
    out += "    /*\n"
    if lowered != "":
        lines = lowered.splitlines()
        i = 0
        while i < len(lines):
            out += "    " + lines[i] + "\n"
            i += 1
    out += "    */\n"
    out += "}\n"
    return out


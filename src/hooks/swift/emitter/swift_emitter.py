"""EAST -> Swift transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_swift_profile() -> dict[str, Any]:
    """Swift backend で利用する profile を返す。"""
    return load_cs_profile()


def transpile_to_swift(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Swift ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    out = "// このファイルは EAST ベース Swift プレビュー出力です。\n"
    out += "// TODO: 専用 SwiftEmitter 実装へ段階移行する。\n"
    out += "import Foundation\n\n"
    out += "func main() {\n"
    out += "    /*\n"
    if lowered != "":
        lines = lowered.splitlines()
        i = 0
        while i < len(lines):
            out += "    " + lines[i] + "\n"
            i += 1
    out += "    */\n"
    out += "}\n\n"
    out += "main()\n"
    return out


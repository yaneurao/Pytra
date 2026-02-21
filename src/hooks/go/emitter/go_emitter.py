"""EAST -> Go transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_go_profile() -> dict[str, Any]:
    """Go backend で利用する profile を返す。"""
    return load_cs_profile()


def _wrap_go_preview_body(body: str) -> str:
    """C# ベースの中間出力を Go ソースへ埋め込む。"""
    out = "// このファイルは EAST ベース Go プレビュー出力です。\n"
    out += "// TODO: 専用 GoEmitter 実装へ段階移行する。\n"
    out += "package main\n\n"
    out += "func main() {\n"
    out += "    /*\n"
    if body != "":
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            out += "    " + lines[i] + "\n"
            i += 1
    out += "    */\n"
    out += "}\n"
    return out


def transpile_to_go(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Go ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    return _wrap_go_preview_body(lowered)

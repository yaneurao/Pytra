"""EAST -> Java transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_java_profile() -> dict[str, Any]:
    """Java backend で利用する profile を返す。"""
    return load_cs_profile()


def _wrap_java_preview_body(body: str) -> str:
    """C# ベースの中間出力を Java ソースへ埋め込む。"""
    out = "// このファイルは EAST ベース Java プレビュー出力です。\n"
    out += "// TODO: 専用 JavaEmitter 実装へ段階移行する。\n"
    out += "public final class Main {\n"
    out += "    public static void main(String[] args) {\n"
    out += "        /*\n"
    if body != "":
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            out += "        " + lines[i] + "\n"
            i += 1
    out += "        */\n"
    out += "    }\n"
    out += "}\n"
    return out


def transpile_to_java(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Java ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    return _wrap_java_preview_body(lowered)


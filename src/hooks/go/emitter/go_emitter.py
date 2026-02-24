"""EAST -> Go transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_go_profile() -> dict[str, Any]:
    """Go backend で利用する profile を返す。"""
    return load_cs_profile()


def _extract_preview_signature_lines(body: str) -> list[str]:
    """C# 中間出力から preview 用の軽量シグネチャ行を抽出する。"""
    out: list[str] = []
    prev_blank = False
    if body == "":
        return out
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if s == "":
            if len(out) > 0 and not prev_blank:
                out.append("")
                prev_blank = True
            continue
        prev_blank = False
        if s.startswith("using "):
            continue
        if s.startswith("//"):
            out.append(s)
            continue
        if s.startswith("public static class ") or s.startswith("public class "):
            out.append(s)
            continue
        if s.startswith("public static ") or s.startswith("public "):
            out.append(s)
            continue
    return out


def _wrap_go_preview_body(body: str) -> str:
    """C# ベースの中間出力を Go ソースへ埋め込む。"""
    preview_lines = _extract_preview_signature_lines(body)
    out = "// このファイルは EAST ベース Go プレビュー出力です。\n"
    out += "// TODO: 専用 GoEmitter 実装へ段階移行する。\n"
    out += "package main\n\n"
    out += "func main() {\n"
    out += "    // C# ベース中間出力のシグネチャ要約:\n"
    if len(preview_lines) == 0:
        out += "    // (no symbols)\n"
    else:
        i = 0
        while i < len(preview_lines):
            line = preview_lines[i]
            if line == "":
                out += "    //\n"
            else:
                out += "    // " + line + "\n"
            i += 1
    out += "}\n"
    return out


def transpile_to_go(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Go ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    return _wrap_go_preview_body(lowered)

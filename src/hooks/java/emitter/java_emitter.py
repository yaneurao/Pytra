"""EAST -> Java transpiler (preview backend)."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp


def load_java_profile() -> dict[str, Any]:
    """Java backend で利用する profile を返す。"""
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


def _wrap_java_preview_body(body: str) -> str:
    """C# ベースの中間出力を Java ソースへ埋め込む。"""
    preview_lines = _extract_preview_signature_lines(body)
    out = "// このファイルは EAST ベース Java プレビュー出力です。\n"
    out += "// TODO: 専用 JavaEmitter 実装へ段階移行する。\n"
    out += "public final class Main {\n"
    out += "    public static void main(String[] args) {\n"
    out += "        // C# ベース中間出力のシグネチャ要約:\n"
    if len(preview_lines) == 0:
        out += "        // (no symbols)\n"
    else:
        i = 0
        while i < len(preview_lines):
            line = preview_lines[i]
            if line == "":
                out += "        //\n"
            else:
                out += "        // " + line + "\n"
            i += 1
    out += "    }\n"
    out += "}\n"
    return out


def transpile_to_java(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Java ソース（プレビュー形式）へ変換する。"""
    lowered = transpile_to_csharp(east_doc)
    return _wrap_java_preview_body(lowered)
